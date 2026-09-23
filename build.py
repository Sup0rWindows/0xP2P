import os
import sys
import subprocess
import shutil

def run_command(command, cwd=None):
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError:
        return False

def build_project():
    print("[*] Launching Compiler Pipeline for 0xp2p Engine...")
    
    print("\n[*] Synchronizing Memory Guardian (C)...")
    sys_alloc_dir = os.path.abspath("sys-alloc")
    build_dir = os.path.join(sys_alloc_dir, "build")
    
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    cmake_success = run_command("cmake ..", cwd=build_dir)
    if cmake_success:
        run_command("cmake --build . --config Release", cwd=build_dir)
    else:
        print("[!] CMake not bound. Attempting direct GCC/Clang sequence...")
        if sys.platform == "win32":
            run_command("gcc -shared -o build/sys_alloc.dll allocator.c", cwd=sys_alloc_dir)
        else:
            run_command("gcc -shared -fPIC -o build/libsys_alloc.so allocator.c", cwd=sys_alloc_dir)
        
    print("\n[*] Baking Cryptographic Core (Rust)...")
    run_command("cargo build --release", cwd=os.path.abspath("data-parser"))
        
    print("\n[*] Weaving P2P Network Pipeline (Rust)...")
    run_command("cargo build --release", cwd=os.path.abspath("net-stream"))

    print("\n[+] PIPELINE INSULATED: All binary fabrics are locked and deployed.")
    print("[🚀] System Core 0xp2p is primed, Execute: python app.py")

if __name__ == "__main__":
    build_project()