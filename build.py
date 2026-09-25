import os, sys, subprocess, shutil

def run(cmd, cwd):
    r = subprocess.run(cmd, check=False, cwd=cwd)
    return r.returncode == 0

def build():
    print("[*] Starting build pipeline...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(base_dir, "sys-alloc", "build")
    
    if os.path.exists(build_dir): shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    sys_alloc_dir = os.path.join(base_dir, "sys-alloc")
    ext = "dll" if sys.platform == "win32" else "so"
    c_out = os.path.join(build_dir, f"libsys_alloc.{ext}")
    
    print("[*] Compiling C memory allocator...")
    c_cmd = ["gcc", "-shared", "-o", c_out, "sys_alloc.c"] if sys.platform == "win32" else ["gcc", "-shared", "-fPIC", "-o", c_out, "sys_alloc.c"]
    
    if not run(c_cmd, cwd=sys_alloc_dir):
        print("[!] GCC failed. Trying clang...")
        c_cmd[0] = "clang"
        if not run(c_cmd, cwd=sys_alloc_dir):
            raise RuntimeError("Failed to compile C components. Ensure gcc or clang is installed.")

    print("[*] Compiling Rust crypto core...")
    rust_crypto_dir = os.path.join(base_dir, "data-parser")
    if not run(["cargo", "build", "--release"], cwd=rust_crypto_dir):
        raise RuntimeError("Rust crypto core build failed.")
        
    rust_crypto_src = os.path.join(rust_crypto_dir, "target", "release", f"libdata_parser.{ext}")
    if os.path.exists(rust_crypto_src):
        shutil.copy(rust_crypto_src, os.path.join(build_dir, f"libnet_parser_engine.{ext}"))

    print("[*] Compiling Rust P2P network stream...")
    rust_net_dir = os.path.join(base_dir, "net-stream")
    if not run(["cargo", "build", "--release"], cwd=rust_net_dir):
        raise RuntimeError("Rust P2P network build failed.")
        
    rust_net_src = os.path.join(rust_net_dir, "target", "release", f"libnet_stream.{ext}")
    if os.path.exists(rust_net_src):
        shutil.copy(rust_net_src, os.path.join(build_dir, f"libnet_stream_engine.{ext}"))

    print("\n[+] Build successful. All compiled binaries are placed in sys-alloc/build/")
    print("[->] To start the engine run: python app.py")

if __name__ == "__main__":
    build()
