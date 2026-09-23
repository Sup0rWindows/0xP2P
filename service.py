import ctypes
import os
import sys

class KernelOrchestrator:
    def __init__(self):
        self.lib_alloc = None
        self.current_block = None
        self._load_memory_guardian()

    def _load_memory_guardian(self):
        try:
            if sys.platform == "win32":
                lib_path = os.path.abspath("sys-alloc/build/sys_alloc.dll")
            else:
                lib_path = os.path.abspath("sys-alloc/build/libsys_alloc.so")
            
            if os.path.exists(lib_path):
                self.lib_alloc = ctypes.CDLL(lib_path)
                self._setup_ctypes_signatures() 
        except Exception:
            pass

    def _setup_ctypes_signatures(self):
        self.lib_alloc.sys_allocate_secure_block.restype = ctypes.c_void_p
        self.lib_alloc.sys_allocate_secure_block.argtypes = [ctypes.c_size_t]
        
        self.lib_alloc.sys_restrict_memory_access.restype = ctypes.c_int
        self.lib_alloc.sys_restrict_memory_access.argtypes = [ctypes.c_void_p, ctypes.c_int]
        
        self.lib_alloc.sys_get_buffer_pointer.restype = ctypes.c_void_p
        self.lib_alloc.sys_get_buffer_pointer.argtypes = [ctypes.c_void_p]
        
        self.lib_alloc.sys_purge_and_free_block.restype = ctypes.c_int
        self.lib_alloc.sys_purge_and_free_block.argtypes = [ctypes.c_void_p]

    def enforce_ram_lock(self, size=2 * 1024 * 1024):
        if self.lib_alloc:
            self.current_block = self.lib_alloc.sys_allocate_secure_block(size)
            return self.current_block
        return None

    def secure_write_to_buffer(self, data_bytes):
        if not self.lib_alloc or not self.current_block:
            return False
            
        self.lib_alloc.sys_restrict_memory_access(self.current_block, 0)
        
        buffer_ptr = self.lib_alloc.sys_get_buffer_pointer(self.current_block)
        
        ctypes.memmove(buffer_ptr, data_bytes, len(data_bytes))
        
        self.lib_alloc.sys_restrict_memory_access(self.current_block, 1)
        return True

    def secure_read_from_buffer(self, size):
        if not self.lib_alloc or not self.current_block:
            return b""
            
        buffer_ptr = self.lib_alloc.sys_get_buffer_pointer(self.current_block)
        return ctypes.string_at(buffer_ptr, size)

    def release_and_shred_ram(self):
        if self.lib_alloc and self.current_block:
            self.lib_alloc.sys_purge_and_free_block(self.current_block)
            self.current_block = None