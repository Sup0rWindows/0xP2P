import sys, asyncio
from service import MemService
from ui_render.app_window import AppWindow
from sync_service.sync import VolatileSyncService

BLOCK_SIZE = 2097152 

async def start_pipeline(mode):
    print(f"[*] Initializing pipeline in {mode} mode...")
    
    mem = MemService()
    
    sync_service = VolatileSyncService()
    
    asyncio.create_task(sync_service._server_init())
    asyncio.create_task(sync_service._pump())

    def rust_worker(ptr, sz):
        print(f"[+] Memory pointer {hex(ptr)} routed to low-level modules.")
        
    try:
        ui = AppWindow(callback=lambda m: None)
        
        await asyncio.gather(
            ui.async_render_loop(),
            asyncio.to_thread(mem.process, rust_worker, BLOCK_SIZE)
        )
    except KeyboardInterrupt:
        print("\n[-] Terminating components safely...")
    finally:
        sync_service.terminate()

def main():
    if len(sys.argv) < 2:
        print("[!] Execution error. Usage: python app.py [SENDER/RECEIVER]")
        sys.exit(1)
        
    operational_mode = sys.argv[1].upper()
    if operational_mode not in ["SENDER", "RECEIVER"]:
        print("[!] Invalid mode. Choose SENDER or RECEIVER.")
        sys.exit(1)

    asyncio.run(start_pipeline(operational_mode))

if __name__ == "__main__":
    main()
