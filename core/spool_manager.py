# core/spool_manager.py

import tkinter as tk
from tkinter import ttk, messagebox
from core.utils import center_window
from core.spool_presets import SPOOL_PRESETS
from core.constants import DEFAULT_SETTINGS, FONT_BOLD, FONT_MAIN, COLOR_ACCENT

class SpoolManager(tk.Toplevel):
    def __init__(self, parent, data_manager, on_close_callback):
        super().__init__(parent)
        self.data_manager = data_manager
        self.on_close_callback = on_close_callback
        self.title("Spulen Datenbank")
        self.geometry("600x700")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        
        _, _, self.spools = self.data_manager.load_all(DEFAULT_SETTINGS)
        ttk.Label(self, text="Verfügbare Leerspulen", font=("Segoe UI", 10, "bold")).pack(pady=10)
        frm_list = ttk.Frame(self)
        frm_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.tree = ttk.Treeview(frm_list, columns=("id", "name", "weight"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Bezeichnung")
        self.tree.heading("weight", text="Leergewicht (g)")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=250)
        self.tree.column("weight", width=100, anchor="center")
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        frm_input = ttk.LabelFrame(self, text="Bearbeiten / Neu")
        frm_input.pack(fill="x", padx=10, pady=10, side="bottom")
        ttk.Label(frm_input, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ent_name = ttk.Entry(frm_input)
        self.ent_name.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(frm_input, text="Gewicht (g):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ent_weight = ttk.Entry(frm_input)
        self.ent_weight.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        frm_input.columnconfigure(1, weight=1)
        
        frm_btns = ttk.Frame(frm_input)
        frm_btns.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(frm_btns, text="Neu anlegen", command=self.add_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="Speichern", command=self.update_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="Löschen", command=self.delete_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="📋 Vorlagen", command=self.import_preset).pack(side="left", padx=5)
        
        self.refresh_list()
    
    def import_preset(self):
        win = tk.Toplevel(self)
        win.title("Spulen-Vorlagen")
        win.geometry("450x550")
        win.configure(bg=self.cget('bg'))
        center_window(win, self)

        ttk.Label(win, text="Wähle eine Standardspule:", font=FONT_BOLD).pack(pady=(10, 5))

        frm_search = ttk.Frame(win)
        frm_search.pack(fill="x", padx=10, pady=(0, 5))
        ttk.Label(frm_search, text="🔍 Suche:").pack(side="left")
        var_search = tk.StringVar()
        ent_search = ttk.Entry(frm_search, textvariable=var_search)
        ent_search.pack(side="left", fill="x", expand=True, padx=(5, 0))

        lb = tk.Listbox(win, font=FONT_MAIN)
        lb.pack(fill="both", expand=True, padx=10, pady=5)

        self.filtered_presets = SPOOL_PRESETS.copy()

        def filter_list(*args):
            search_term = var_search.get().lower()
            lb.delete(0, tk.END)
            self.filtered_presets = []
            for p in SPOOL_PRESETS:
                display_text = f"{p['name']} ({p['weight']}g)"
                if search_term in display_text.lower():
                    self.filtered_presets.append(p)
                    lb.insert(tk.END, display_text)

        var_search.trace_add("write", filter_list)
        filter_list()

        def do_import():
            sel = lb.curselection()
            if not sel: return
            p = self.filtered_presets[sel[0]] 
            self.ent_name.delete(0, tk.END)
            self.ent_name.insert(0, p['name'])
            self.ent_weight.delete(0, tk.END)
            self.ent_weight.insert(0, str(p['weight']))
            win.destroy()

        ttk.Button(win, text="Übernehmen", command=do_import, style="Accent.TButton").pack(pady=10, fill="x", padx=20)
        ent_search.focus_set()

    def refresh_list(self):
        for item in self.tree.get_children(): 
            self.tree.delete(item)
        
        # Sortiert die Spulen alphabetisch (case-insensitive) vor der Ausgabe
        sorted_spools = sorted(self.spools, key=lambda s: s['name'].lower())
        for s in sorted_spools: 
            self.tree.insert("", "end", iid=str(s['id']), values=(s['id'], s['name'], s['weight']))
            
        self.on_close_callback()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        spool_id = int(sel[0])
        spool = next((s for s in self.spools if s['id'] == spool_id), None)
        if spool:
            self.ent_name.delete(0, tk.END)
            self.ent_name.insert(0, spool['name'])
            self.ent_weight.delete(0, tk.END)
            self.ent_weight.insert(0, str(spool['weight']))

    def add_spool(self):
        name = self.ent_name.get().strip()
        weight_str = self.ent_weight.get().strip().replace(',', '.')
        if not name or not weight_str: return
        try:
            weight = int(float(weight_str))
            new_id = max([s['id'] for s in self.spools], default=0) + 1
            self.spools.append({"id": new_id, "name": name, "weight": weight})
            self.data_manager.save_spools(self.spools)
            self.refresh_list()
        except: pass

    def update_spool(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            weight = int(float(self.ent_weight.get().strip().replace(',', '.')))
            for s in self.spools:
                if s['id'] == str(sel[0]): 
                    s['name'] = self.ent_name.get().strip()
                    s['weight'] = weight
            self.data_manager.save_spools(self.spools)
            self.refresh_list()
        except: pass

    def delete_spool(self):
        sel = self.tree.selection()
        if not sel: return
        self.spools = [s for s in self.spools if s['id'] != int(sel[0])]
        self.data_manager.save_spools(self.spools)
        self.refresh_list()

    def destroy(self): 
        self.on_close_callback()
        super().destroy()
