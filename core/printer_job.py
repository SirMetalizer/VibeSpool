import tkinter as tk
from tkinter import ttk
from core.utils import center_window
from core.constants import FONT_BOLD

class PrinterJobDialog(tk.Toplevel):
    def __init__(self, parent, jobs, on_select_job):
        super().__init__(parent)
        self.configure(bg=parent.cget('bg'))
        self.on_select_job = on_select_job
        self.title("Drucker-Historie")
        self.geometry("600x450")
        center_window(self, parent)
        self.transient(parent)
        self.grab_set()
        ttk.Label(self, text="Wähle einen Druckauftrag aus:", font=FONT_BOLD).pack(pady=10)
        
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree = ttk.Treeview(frm, columns=("file", "status", "used"), show="headings")
        self.tree.heading("file", text="Datei")
        self.tree.heading("status", text="Status")
        self.tree.heading("used", text="Verbrauch (g)")
        self.tree.column("file", width=300)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("used", width=100, anchor="center")
        
        scroll = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        for i, j in enumerate(jobs):
            used = f"{j.get('filament_used', 0):.1f}g"
            self.tree.insert("", "end", iid=str(i), values=(j.get('filename', 'Unbekannt'), j.get('status', '-'), used))
        
        def confirm():
            sel = self.tree.selection()
            if not sel: 
                return
            job = jobs[int(sel[0])]
            self.on_select_job(job.get('filament_used', 0))
            self.destroy()
            
        ttk.Button(self, text="Diesen Verbrauch abziehen", command=confirm, style="Accent.TButton").pack(pady=15, fill="x", padx=20)
