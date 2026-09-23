import tkinter as tk
from tkinter import ttk
import sys
import os 

class VolatileAppWindow:
    def __init__(self, role_callback):
        self.role_callback = role_callback
        self.root = tk.Tk()
        self.root.title("System Frame Buffer")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        self._apply_stealth_theme()
        self._build_secure_layout()

    def _apply_stealth_theme(self):
        self.root.configure(bg="#121212")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", background="#121212", foreground="#FFFFFF", fieldbackground="#1E1E1E")
        
        self.style.configure("TButton", 
                             font=("Courier", 10, "bold"), 
                             background="#1E1E1E", 
                             foreground="#FFFFFF", 
                             borderwidth=1, 
                             focuscolor="none") 
                             
        self.style.map("TButton", background=[("active", "#2D2D2D")])

    def _build_secure_layout(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        lbl = ttk.Label(main_frame, text="SELECT OPERATIONAL MODE:", font=("Courier", 12, "bold"))
        lbl.pack(pady=20)

        btn_sender = ttk.Button(main_frame, text="[ TRANSMITTER ]", command=lambda: self._select_mode("SENDER"))
        btn_sender.pack(fill=tk.X, pady=10)

        btn_receiver = ttk.Button(main_frame, text="[ RECEIVER ]", command=lambda: self._select_mode("RECEIVER"))
        btn_receiver.pack(fill=tk.X, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self._secure_exit)

    def _select_mode(self, mode):
        self.role_callback(mode)
        self.root.destroy()

    def _secure_exit(self):
        self.root.destroy()
        os._exit(0) 

    def start_render_loop(self):
        self.root.mainloop()