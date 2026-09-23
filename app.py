from ui_render.view import VolatileAppWindow
from service import KernelOrchestrator
import sys

def init_operational_sequence(selected_mode):
    orchestrator = KernelOrchestrator()
    
    secure_block = orchestrator.enforce_ram_lock(size=2 * 1024 * 1024)
    
    try:
        orchestrator.launch_background_core(selected_mode)
    finally:
        if secure_block:
            orchestrator.release_ram_lock(secure_block)

if __name__ == "__main__":
    app = VolatileAppWindow(role_callback=init_operational_sequence)
    app.start_render_loop()
