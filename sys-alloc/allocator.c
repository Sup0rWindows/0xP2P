#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#if defined(_WIN32)
    #include <windows.h>
#else
    #include <sys/mman.h>
    #include <unistd.h>
#endif

typedef struct {
    void* ptr;
    size_t size;
} MemBlock;

static size_t get_page_size(void) {
#if defined(_WIN32)
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return (size_t)si.dwPageSize;
#else
    return (size_t)sysconf(_SC_PAGESIZE);
#endif
}

MemBlock* sys_allocate_secure_block(size_t size) {
    if (size == 0) return NULL;

    size_t page = get_page_size();
    size_t aligned = ((size + page - 1) / page) * page;

    MemBlock* block = (MemBlock*)malloc(sizeof(MemBlock));
    if (!block) return NULL;

    block->size = aligned;

#if defined(_WIN32)
    block->ptr = VirtualAlloc(NULL, aligned, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!block->ptr) {
        free(block);
        return NULL;
    }
    if (!VirtualLock(block->ptr, aligned)) {
        VirtualFree(block->ptr, 0, MEM_RELEASE);
        free(block);
        return NULL;
    }
#else
    block->ptr = mmap(NULL, aligned, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (block->ptr == MAP_FAILED) {
        free(block);
        return NULL;
    }
    if (mlock(block->ptr, aligned) != 0) {
        munmap(block->ptr, aligned);
        free(block);
        return NULL;
    }
#if defined(__linux__) && defined(MADV_DONTDUMP)
    madvise(block->ptr, aligned, MADV_DONTDUMP);
#endif
#endif

    return block;
}

int sys_restrict_memory_access(MemBlock* block, int read_only) {
    if (!block || !block->ptr) return -1;

#if defined(_WIN32)
    DWORD old;
    DWORD flag = read_only ? PAGE_READONLY : PAGE_READWRITE;
    return VirtualProtect(block->ptr, block->size, flag, &old) ? 0 : -1;
#else
    int flag = read_only ? PROT_READ : (PROT_READ | PROT_WRITE);
    return mprotect(block->ptr, block->size, flag);
#endif
}

int sys_purge_and_free_block(MemBlock* block) {
    if (!block) return 0;

    if (block->ptr) {
        sys_restrict_memory_access(block, 0);

        volatile uint8_t* p = (volatile uint8_t*)block->ptr;
        size_t s = block->size;
        while (s--) *p++ = 0;

#if defined(_WIN32)
        VirtualUnlock(block->ptr, block->size);
        VirtualFree(block->ptr, 0, MEM_RELEASE);
#else
        munlock(block->ptr, block->size);
        munmap(block->ptr, block->size);
#endif
    }

    free(block);
    return 0;
}

void* sys_get_buffer_pointer(MemBlock* block) {
    if (!block) return NULL;
    return block->ptr;
}
