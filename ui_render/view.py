import tkinter as tk
from tkinter import ttk
import asyncio, os

class AppWindow:
    def __init__(self, callback):
        self.cb = callback
        self.win = tk.Tk()
        self.win.title("Core Frame Buffer")
        self.win.geometry("450x300")
        self.win.resizable(False, False)
        
        self.win.configure(bg="#121212")
        st = ttk.Style()
        st.theme_use("clam")
        st.configure(".", background="#121212", foreground="#FFFFFF", fieldbackground="#1E1E1E")
        st.configure("TButton", font=("Courier", 10, "bold"), background="#1E1E1E", foreground="#FFFFFF", borderwidth=1)
        st.map("TButton", background=[("active", "#2D2D2D")])

        fr = ttk.Frame(self.win, padding=20)
        fr.pack(fill=tk.BOTH, expand=True)

        ttk.Label(fr, text="SELECT OPERATIONAL MODE:", font=("Courier", 12, "bold")).pack(pady=20)
        
        ttk.Button(fr, text="[ TRANSMITTER ]", command=lambda: self._click("SENDER")).pack(fill=tk.X, pady=10)
        ttk.Button(fr, text="[ RECEIVER ]", command=lambda: self._click("RECEIVER")).pack(fill=tk.X, pady=10)

        self.win.protocol("WM_DELETE_WINDOW", self._exit)

    def _click(self, mode):
        self.cb(mode)
        self.win.destroy()

    def _exit(self):
        self.win.destroy()
        os._exit(0)

    async def async_render_loop(self):
        try:
            while True:
                self.win.update()
                await asyncio.sleep(0.02)
        except tk.TclError:
            pass
