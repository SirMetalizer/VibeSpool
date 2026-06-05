# core/shelf_planner.py

import tkinter as tk
from tkinter import ttk
from core.utils import center_window
from core.logic import parse_shelves_string, serialize_shelves
from core.constants import FONT_BOLD, FONT_MAIN, COLOR_ACCENT

class ShelfPlannerDialog(tk.Toplevel):
    def __init__(self, parent, initial_value, on_confirm):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.title("Regal-Planer")
        self.geometry("500x450")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        self.transient(parent)
        self.grab_set()
        
        self.shelves = parse_shelves_string(initial_value) or [{"name": "REGAL", "rows": 4, "cols": 8}]
        self.current_idx, self._lock = 0, False
        self.var_name, self.var_rows, self.var_cols = tk.StringVar(), tk.IntVar(), tk.IntVar()
        
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=20, pady=10)
        left = ttk.Frame(main, width=200)
        left.pack(side="left", fill="y", padx=(0, 20))
        ttk.Label(left, text="Regal-Liste:", font=FONT_BOLD).pack(anchor="w")
        self.listbox = tk.Listbox(left, height=10, font=FONT_MAIN, bg=parent.cget('bg'), fg="white" if "dark" in str(parent.cget('bg')) else "black", selectbackground=COLOR_ACCENT)
        self.listbox.pack(fill="both", expand=True, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        btn_frm = ttk.Frame(left)
        btn_frm.pack(fill="x")
        ttk.Button(btn_frm, text="➕ Neu", command=self.add_new, width=8).pack(side="left")
        ttk.Button(btn_frm, text="❌ Lösch", command=self.delete_current, width=8).pack(side="left", padx=2)
        
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)
        inf = ttk.LabelFrame(right, text="Konfiguration", padding=15)
        inf.pack(fill="x")
        ttk.Label(inf, text="Regal Name:").pack(anchor="w")
        ttk.Entry(inf, textvariable=self.var_name).pack(fill="x", pady=5)
        ttk.Label(inf, text="Anzahl Reihen:").pack(anchor="w")
        ttk.Spinbox(inf, from_=1, to=50, textvariable=self.var_rows).pack(fill="x", pady=5)
        ttk.Label(inf, text="Anzahl Spalten:").pack(anchor="w")
        ttk.Spinbox(inf, from_=1, to=50, textvariable=self.var_cols).pack(fill="x", pady=5)
        
        # --- SICHERES LADEN ---
        self._lock = True
        self.refresh_listbox()
        if self.shelves:
            self.listbox.selection_set(0)
            self.current_idx = 0
            s = self.shelves[0]
            self.var_name.set(s['name'])
            self.var_rows.set(s['rows'])
            self.var_cols.set(s['cols'])
        self._lock = False
        
        ttk.Button(self, text="Konfiguration Speichern", command=self.final, style="Accent.TButton").pack(pady=20, fill="x", padx=40)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for s in self.shelves: 
            self.listbox.insert(tk.END, f"📦 {s['name']} ({s['rows']}x{s['cols']})")

    def save_current(self):
        try:
            name = self.var_name.get().strip().replace(",", "").replace("|", "") or "REGAL"
            rows = max(1, int(self.var_rows.get()))
            cols = max(1, int(self.var_cols.get()))
            self.shelves[self.current_idx] = {"name": name, "rows": rows, "cols": cols}
        except: pass

    def on_select(self, e):
        if self._lock: return
        sel = self.listbox.curselection()
        if not sel: return
        self.save_current() 
        self._lock = True
        self.current_idx = sel[0]
        self.refresh_listbox()
        self.listbox.selection_set(self.current_idx)
        s = self.shelves[self.current_idx]
        self.var_name.set(s['name'])
        self.var_rows.set(s['rows'])
        self.var_cols.set(s['cols'])
        self.listbox.see(self.current_idx)
        self._lock = False

    def add_new(self): 
        self.save_current() 
        self.shelves.append({"name": f"REGAL {len(self.shelves)+1}", "rows": 4, "cols": 8})
        self._lock = True
        self.refresh_listbox()
        self.current_idx = len(self.shelves) - 1
        self.listbox.selection_set(self.current_idx)
        self.listbox.see(self.current_idx)
        s = self.shelves[self.current_idx]
        self.var_name.set(s['name'])
        self.var_rows.set(s['rows'])
        self.var_cols.set(s['cols'])
        self._lock = False

    def delete_current(self):
        if len(self.shelves) > 1: 
            del self.shelves[self.current_idx]
            self._lock = True
            self.refresh_listbox()
            self.current_idx = max(0, self.current_idx - 1)
            self.listbox.selection_set(self.current_idx)
            s = self.shelves[self.current_idx]
            self.var_name.set(s['name'])
            self.var_rows.set(s['rows'])
            self.var_cols.set(s['cols'])
            self._lock = False

    def final(self): 
        self.save_current()
        res = serialize_shelves(self.shelves)
        self.on_confirm(res)
        self.destroy()
