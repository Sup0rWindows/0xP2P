import ctypes, os, sys
from threading import Lock

class MemService:
    def __init__(self, path=""):
        self.lock = Lock()
        self.PAGE_SIZE = 4096
        
        if not path:
            ext = "dll" if sys.platform == "win32" else "so"
            path = os.path.join(os.path.dirname(__file__), "sys-alloc/build/libsys_alloc." + ext)
            
        self.ffi = ctypes.CDLL(path)
        
        self.ffi.sys_allocate_secure_block.restype = ctypes.c_void_p
        self.ffi.sys_allocate_secure_block.argtypes = [ctypes.c_size_t]
        self.ffi.sys_restrict_memory_access.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.ffi.sys_purge_and_free_block.argtypes = [ctypes.c_void_p]

    def process(self, rust_fn, sz):
        if sz % self.PAGE_SIZE != 0:
            sz = ((sz // self.PAGE_SIZE) + 1) * self.PAGE_SIZE

        with self.lock:
            ptr = self.ffi.sys_allocate_secure_block(sz)
            if not ptr: raise MemoryError("OS failed to alloc secure memory")

            try:
                self.ffi.sys_restrict_memory_access(ptr, 0)
                rust_fn(ptr, sz)
            finally:
                self.ffi.sys_restrict_memory_access(ptr, 1)
                self.ffi.sys_purge_and_free_block(ptr)
