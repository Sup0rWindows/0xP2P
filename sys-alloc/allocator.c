#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32) || defined(_WIN64)
    #include <windows.h>
#elif defined(__linux__) || defined(__APPLE__)
    #include <sys/mman.h>
    #include <unistd.h>
#endif

#define VNP_SUCCESS 0
#define VNP_ERROR_ALLOC 1
#define VNP_ERROR_LOCK 2
#define VNP_ERROR_PROTECT 3
#define VNP_ERROR_FREE 4

typedef struct {
    void* raw_address;
    size_t aligned_size;
    size_t requested_size;
} VolatileBufferMemory;

static size_t get_system_page_size(void) {
#if defined(_WIN32) || defined(_WIN64)
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return (size_t)si.dwPageSize;
#elif defined(__linux__) || defined(__APPLE__)
    return (size_t)sysconf(_SC_PAGESIZE);
#else
    return 4096;
#endif
}

VolatileBufferMemory* sys_allocate_secure_block(size_t size) {
    if (size == 0) return NULL;

    size_t page_size = get_system_page_size();
    size_t aligned_size = ((size + page_size - 1) / page_size) * page_size;

    VolatileBufferMemory* meta = (VolatileBufferMemory*)malloc(sizeof(VolatileBufferMemory));
    if (!meta) return NULL;

    meta->requested_size = size;
    meta->aligned_size = aligned_size;

#if defined(_WIN32) || defined(_WIN64)
    meta->raw_address = VirtualAlloc(NULL, aligned_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!meta->raw_address) {
        free(meta);
        return NULL;
    }

    if (!VirtualLock(meta->raw_address, aligned_size)) {
        VirtualFree(meta->raw_address, 0, MEM_RELEASE);
        free(meta);
        return NULL;
    }
#elif defined(__linux__) || defined(__APPLE__)
    meta->raw_address = mmap(NULL, aligned_size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (meta->raw_address == MAP_FAILED) {
        free(meta);
        return NULL;
    }

    if (mlock(meta->raw_address, aligned_size) != 0) {
        munmap(meta->raw_address, aligned_size);
        free(meta);
        return NULL;
    }

##if defined(__linux__) && defined(MADV_DONTDUMP)
    madvise(meta->raw_address, aligned_size, MADV_DONTDUMP);
##endif
#endif

    return meta;
}

int sys_restrict_memory_access(VolatileBufferMemory* meta, int read_only) {
    if (!meta || !meta->raw_address) return VNP_ERROR_PROTECT;

#if defined(_WIN32) || defined(_WIN64)
    DWORD old_protect;
    DWORD protect_flag = read_only ? PAGE_READONLY : PAGE_READWRITE;
    if (!VirtualProtect(meta->raw_address, meta->aligned_size, protect_flag, &old_protect)) {
        return VNP_ERROR_PROTECT;
    }
#elif defined(__linux__) || defined(__APPLE__)
    int protect_flag = read_only ? PROT_READ : (PROT_READ | PROT_WRITE);
    if (mprotect(meta->raw_address, meta->aligned_size, protect_flag) != 0) {
        return VNP_ERROR_PROTECT;
    }
#endif

    return VNP_SUCCESS;
}

int sys_purge_and_free_block(VolatileBufferMemory* meta) {
    if (!meta) return VNP_SUCCESS;

    if (meta->raw_address) {
        sys_restrict_memory_access(meta, 0);

        volatile uint8_t* p = (volatile uint8_t*)meta->raw_address;
        size_t size = meta->aligned_size;
        while (size--) {
            *p++ = 0;
        }

#if defined(_WIN32) || defined(_WIN64)
        VirtualUnlock(meta->raw_address, meta->aligned_size);
        VirtualFree(meta->raw_address, 0, MEM_RELEASE);
#elif defined(__linux__) || defined(__APPLE__)
        munlock(meta->raw_address, meta->aligned_size);
        munmap(meta->raw_address, meta->aligned_size);
#endif
    }

    free(meta);
    return VNP_SUCCESS;
}

void* sys_get_buffer_pointer(VolatileBufferMemory* meta) {
    if (!meta) return NULL;
    return meta->raw_address;
}
