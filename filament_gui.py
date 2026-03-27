import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
import os
import json
import zipfile
import webbrowser 
import urllib.request 
import threading      
import re            
import csv
from ctypes import windll
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime, timedelta
import qrcode 

# --- MODULE IMPORT ---
from core.utils import load_json, save_json, get_colors_from_text, create_color_icon, center_window
from core.logic import calculate_net_weight, check_for_updates, parse_shelves_string, serialize_shelves
from core.data_manager import DataManager

def fetch_last_print_usage(url, key): 
    return None
def fetch_recent_jobs(url, key): 
    return []

SPOOL_PRESETS = [
    {"name": "Bambu Reusable Spool", "weight": 250},
    {"name": "eSUN Cardboard", "weight": 140},
    {"name": "Sunlu Plastic", "weight": 150},
    {"name": "Prusament", "weight": 200}
]

# --- KONFIGURATION ---
APP_VERSION = "1.8.1"
GITHUB_REPO = "SirMetalizer/VibeSpool" 

# --- DEFAULTS ---
DEFAULT_SETTINGS = {
    "shelves": "REGAL|4|8", 
    "logistics_order": False,
    "label_row": "Fach",
    "label_col": "Slot",
    "num_ams": 1,
    "custom_locs": "Filamenttrockner",
    "geometry": "1500x980", 
    "theme": "dark",
    "use_affiliate": True,
    "rfid_mode": False,
    "printer_url": "",
    "printer_api_key": ""
}

MATERIALS = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF", "PVA", "Sonstiges"]
SUBTYPES = ["Standard", "Matte", "Silk", "High Speed", "Dual Color", "Tri Color", "Glow in Dark", "Marmor", "Holz", "Glitzer/Sparkle", "Transparent"]
COMMON_COLORS = [
    "Black", "White", "Grey", "Silver", "Ash Gray", 
    "Red", "Maroon Red", "Blue", "Light Blue", "Navy", 
    "Green", "Dark Green", "Mint", "Olive",
    "Yellow", "Orange", "Terracotta", 
    "Purple", "Plum", "Lavender", "Pink", "Magenta", 
    "Brown", "Beige", "Turquoise", "Cyan",
    "Gold", "Copper", "Bronze", 
    "Transparent", "Translucent", 
    "Glow in Dark", "Rainbow", "Marble", "Wood"
]

THEMES = {
    "light": {
        "bg": "#f0f0f0", "fg": "#333333", "entry_bg": "#ffffff", "entry_fg": "#000000",
        "tree_bg": "#ffffff", "tree_fg": "#000000", "head_bg": "#e1e1e1", "head_fg": "#333333", "lbl_frame": "#333333"
    },
    "dark": {
        "bg": "#2b2b2b", "fg": "#e0e0e0", "entry_bg": "#3c3f41", "entry_fg": "#e0e0e0",
        "tree_bg": "#3c3f41", "tree_fg": "#e0e0e0", "head_bg": "#4b4d4f", "head_fg": "#e0e0e0", "lbl_frame": "#e0e0e0"
    }
}

COLOR_ACCENT = "#0078d7"    
COLOR_DELETE = "#d9534f" 

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")

# --- FENSTER KLASSEN ---
class SpoolManager(tk.Toplevel):
    def __init__(self, parent, data_manager, on_close_callback):
        super().__init__(parent)
        self.data_manager = data_manager
        self.on_close_callback = on_close_callback; self.title("Spulen Datenbank")
        self.geometry("600x700"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        
        _, _, self.spools = self.data_manager.load_all(DEFAULT_SETTINGS)
        ttk.Label(self, text="Verfügbare Leerspulen", font=("Segoe UI", 10, "bold")).pack(pady=10)
        frm_list = ttk.Frame(self); frm_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.tree = ttk.Treeview(frm_list, columns=("id", "name", "weight"), show="headings")
        self.tree.heading("id", text="ID"); self.tree.heading("name", text="Bezeichnung"); self.tree.heading("weight", text="Leergewicht (g)")
        self.tree.column("id", width=50, anchor="center"); self.tree.column("name", width=250); self.tree.column("weight", width=100, anchor="center")
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set); self.tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        frm_input = ttk.LabelFrame(self, text="Bearbeiten / Neu"); frm_input.pack(fill="x", padx=10, pady=10, side="bottom")
        ttk.Label(frm_input, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ent_name = ttk.Entry(frm_input); self.ent_name.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(frm_input, text="Gewicht (g):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ent_weight = ttk.Entry(frm_input); self.ent_weight.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        frm_input.columnconfigure(1, weight=1); frm_btns = ttk.Frame(frm_input); frm_btns.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(frm_btns, text="Neu anlegen", command=self.add_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="Speichern", command=self.update_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="Löschen", command=self.delete_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="📋 Vorlagen", command=self.import_preset).pack(side="left", padx=5)
        self.refresh_list()
    def import_preset(self):
        win = tk.Toplevel(self); win.title("Spulen-Vorlagen"); win.geometry("400x500"); center_window(win, self)
        ttk.Label(win, text="Wähle eine Standardspule:", font=FONT_BOLD).pack(pady=10)
        lb = tk.Listbox(win, font=FONT_MAIN); lb.pack(fill="both", expand=True, padx=10, pady=5)
        for p in SPOOL_PRESETS: lb.insert(tk.END, f"{p['name']} ({p['weight']}g)")
        def do_import():
            sel = lb.curselection()
            if not sel: return
            p = SPOOL_PRESETS[sel[0]]
            self.ent_name.delete(0, tk.END); self.ent_name.insert(0, p['name'])
            self.ent_weight.delete(0, tk.END); self.ent_weight.insert(0, str(p['weight']))
            win.destroy()
        ttk.Button(win, text="Übernehmen", command=do_import, style="Accent.TButton").pack(pady=10, fill="x", padx=20)
    def refresh_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for s in self.spools: self.tree.insert("", "end", iid=str(s['id']), values=(s['id'], s['name'], s['weight']))
        self.on_close_callback()
    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        spool_id = int(sel[0]); spool = next((s for s in self.spools if s['id'] == spool_id), None)
        if spool:
            self.ent_name.delete(0, tk.END); self.ent_name.insert(0, spool['name']); self.ent_weight.delete(0, tk.END); self.ent_weight.insert(0, str(spool['weight']))
    def add_spool(self):
        name = self.ent_name.get().strip(); weight_str = self.ent_weight.get().strip().replace(',', '.')
        if not name or not weight_str: return
        try:
            weight = int(float(weight_str)); new_id = max([s['id'] for s in self.spools], default=0) + 1
            self.spools.append({"id": new_id, "name": name, "weight": weight}); self.data_manager.save_spools(self.spools); self.refresh_list()
        except: pass
    def update_spool(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            weight = int(float(self.ent_weight.get().strip().replace(',', '.')))
            for s in self.spools:
                if s['id'] == int(sel[0]): s['name'] = self.ent_name.get().strip(); s['weight'] = weight
            self.data_manager.save_spools(self.spools); self.refresh_list()
        except: pass
    def delete_spool(self):
        sel = self.tree.selection()
        if not sel: return
        self.spools = [s for s in self.spools if s['id'] != int(sel[0])]; self.data_manager.save_spools(self.spools); self.refresh_list()
    def destroy(self): self.on_close_callback(); super().destroy()

class ShelfPlannerDialog(tk.Toplevel):
    def __init__(self, parent, initial_value, on_confirm):
        super().__init__(parent); self.on_confirm = on_confirm; self.title("Regal-Planer"); self.geometry("500x450"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        self.transient(parent); self.grab_set()
        
        from core.logic import parse_shelves_string, serialize_shelves
        self.shelves = parse_shelves_string(initial_value) or [{"name": "REGAL", "rows": 4, "cols": 8}]
        self.current_idx, self._lock = 0, False
        self.var_name, self.var_rows, self.var_cols = tk.StringVar(), tk.IntVar(), tk.IntVar()
        
        main = ttk.Frame(self); main.pack(fill="both", expand=True, padx=20, pady=10)
        left = ttk.Frame(main, width=200); left.pack(side="left", fill="y", padx=(0, 20))
        ttk.Label(left, text="Regal-Liste:", font=FONT_BOLD).pack(anchor="w")
        self.listbox = tk.Listbox(left, height=10, font=FONT_MAIN, bg=parent.cget('bg'), fg="white" if "dark" in str(parent.cget('bg')) else "black", selectbackground=COLOR_ACCENT)
        self.listbox.pack(fill="both", expand=True, pady=5); self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        btn_frm = ttk.Frame(left); btn_frm.pack(fill="x")
        ttk.Button(btn_frm, text="➕ Neu", command=self.add_new, width=8).pack(side="left")
        ttk.Button(btn_frm, text="❌ Lösch", command=self.delete_current, width=8).pack(side="left", padx=2)
        
        right = ttk.Frame(main); right.pack(side="left", fill="both", expand=True)
        inf = ttk.LabelFrame(right, text="Konfiguration", padding=15); inf.pack(fill="x")
        ttk.Label(inf, text="Regal Name:").pack(anchor="w"); ttk.Entry(inf, textvariable=self.var_name).pack(fill="x", pady=5)
        ttk.Label(inf, text="Anzahl Reihen:").pack(anchor="w"); ttk.Spinbox(inf, from_=1, to=50, textvariable=self.var_rows).pack(fill="x", pady=5)
        ttk.Label(inf, text="Anzahl Spalten:").pack(anchor="w"); ttk.Spinbox(inf, from_=1, to=50, textvariable=self.var_cols).pack(fill="x", pady=5)
        
        # --- SICHERES LADEN ---
        self._lock = True
        self.refresh_listbox()
        if self.shelves:
            self.listbox.selection_set(0); self.current_idx = 0
            s = self.shelves[0]
            self.var_name.set(s['name']); self.var_rows.set(s['rows']); self.var_cols.set(s['cols'])
        self._lock = False
        
        ttk.Button(self, text="Konfiguration Speichern", command=self.final, style="Accent.TButton").pack(pady=20, fill="x", padx=40)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for s in self.shelves: self.listbox.insert(tk.END, f"📦 {s['name']} ({s['rows']}x{s['cols']})")

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
        self.refresh_listbox(); self.listbox.selection_set(self.current_idx)
        s = self.shelves[self.current_idx]
        self.var_name.set(s['name']); self.var_rows.set(s['rows']); self.var_cols.set(s['cols'])
        self.listbox.see(self.current_idx)
        self._lock = False

    def add_new(self): 
        self.save_current() 
        self.shelves.append({"name": f"REGAL {len(self.shelves)+1}", "rows": 4, "cols": 8})
        self._lock = True
        self.refresh_listbox(); self.current_idx = len(self.shelves) - 1
        self.listbox.selection_set(self.current_idx); self.listbox.see(self.current_idx)
        s = self.shelves[self.current_idx]
        self.var_name.set(s['name']); self.var_rows.set(s['rows']); self.var_cols.set(s['cols'])
        self._lock = False

    def delete_current(self):
        if len(self.shelves) > 1: 
            del self.shelves[self.current_idx]
            self._lock = True
            self.refresh_listbox(); self.current_idx = max(0, self.current_idx - 1)
            self.listbox.selection_set(self.current_idx)
            s = self.shelves[self.current_idx]
            self.var_name.set(s['name']); self.var_rows.set(s['rows']); self.var_cols.set(s['cols'])
            self._lock = False

    def final(self): 
        from core.logic import serialize_shelves
        self.save_current(); res = serialize_shelves(self.shelves); self.on_confirm(res); self.destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, on_save, start_tab=0):
        super().__init__(parent)
        self.data_manager = data_manager; self.on_save = on_save
        _, self.settings, _ = self.data_manager.load_all(DEFAULT_SETTINGS)
        self.title("VibeSpool Einstellungen"); self.geometry("550x500"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        self.transient(parent); self.grab_set()
        
        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        
        # TAB 1: LAGER
        tab_lager = ttk.Frame(self.nb, padding=15); self.nb.add(tab_lager, text="📦 Lager")
        ttk.Label(tab_lager, text="Regal-Konfiguration", font=FONT_BOLD).pack(anchor="w")
        self.var_shelves = tk.StringVar(value=self.settings.get("shelves", "REGAL|4|8"))
        self.shelf_list = tk.Listbox(tab_lager, height=6, font=("Segoe UI", 9))
        self.shelf_list.pack(fill="x", pady=10)
        self.refresh_settings_shelf_list()
        
        def run_planner():
            def on_plan_done(val): self.var_shelves.set(val); self.refresh_settings_shelf_list()
            ShelfPlannerDialog(self, self.var_shelves.get(), on_plan_done)
        ttk.Button(tab_lager, text="🔧 Regal-Konfigurator öffnen", command=run_planner).pack(fill="x")

        # TAB 2: HARDWARE
        tab_hw = ttk.Frame(self.nb, padding=15); self.nb.add(tab_hw, text="🔌 Hardware")
        self.var_logistics = tk.BooleanVar(value=self.settings.get("logistics_order", False))
        ttk.Checkbutton(tab_hw, text="Logistik-Modus (unten = Reihe 1)", variable=self.var_logistics).pack(anchor="w", pady=5)
        
        f_names = ttk.Frame(tab_hw); f_names.pack(fill="x", pady=5)
        ttk.Label(f_names, text="Reihen-Name:").grid(row=0, column=0, sticky="w")
        self.ent_row = ttk.Entry(f_names, width=15); self.ent_row.insert(0, self.settings.get("label_row", "Fach")); self.ent_row.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        ttk.Label(f_names, text="Spalten-Name:").grid(row=1, column=0, sticky="w")
        self.ent_col = ttk.Entry(f_names, width=15); self.ent_col.insert(0, self.settings.get("label_col", "Slot")); self.ent_col.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        
        ttk.Label(tab_hw, text="Anzahl AMS Einheiten:").pack(anchor="w", pady=(10,0))
        self.ent_ams = ttk.Entry(tab_hw, width=10); self.ent_ams.insert(0, str(self.settings.get("num_ams", 1))); self.ent_ams.pack(anchor="w", pady=2)
        ttk.Label(tab_hw, text="Zusatz-Orte (kommagetrennt):").pack(anchor="w", pady=(10,0))
        self.ent_custom = ttk.Entry(tab_hw); self.ent_custom.insert(0, self.settings.get("custom_locs", "")); self.ent_custom.pack(fill="x", pady=2)

        # TAB 3: DRUCKER
        tab_prn = ttk.Frame(self.nb, padding=15); self.nb.add(tab_prn, text="🤖 Drucker")
        ttk.Label(tab_prn, text="Klipper / Moonraker Sync", font=FONT_BOLD).pack(anchor="w")
        ttk.Label(tab_prn, text="Drucker-URL:").pack(anchor="w", pady=(10,0))
        self.ent_prn_url = ttk.Entry(tab_prn); self.ent_prn_url.insert(0, self.settings.get("printer_url", "")); self.ent_prn_url.pack(fill="x", pady=2)
        ttk.Label(tab_prn, text="API Key (optional):").pack(anchor="w", pady=(10,0))
        self.ent_prn_key = ttk.Entry(tab_prn); self.ent_prn_key.insert(0, self.settings.get("printer_api_key", "")); self.ent_prn_key.pack(fill="x", pady=2)

        # TAB 4: SYSTEM
        tab_sys = ttk.Frame(self.nb, padding=15); self.nb.add(tab_sys, text="⚙ System")
        self.var_affiliate = tk.BooleanVar(value=self.settings.get("use_affiliate", True))
        ttk.Checkbutton(tab_sys, text="Entwickler unterstützen (Affiliate)", variable=self.var_affiliate).pack(anchor="w", pady=2)
        self.var_rfid = tk.BooleanVar(value=self.settings.get("rfid_mode", False))
        ttk.Checkbutton(tab_sys, text="RFID-Reader Modus aktiv", variable=self.var_rfid).pack(anchor="w", pady=2)
        
        ttk.Separator(tab_sys, orient="horizontal").pack(fill="x", pady=10)
        path_show = self.settings.get("custom_db_path", "") or "Standard-Ordner"
        self.lbl_path = ttk.Label(tab_sys, text=f"Daten-Pfad:\n{path_show}", font=("Segoe UI", 8, "italic"), wraplength=450)
        self.lbl_path.pack(fill="x", pady=5)
        
        p_btn_frm = ttk.Frame(tab_sys); p_btn_frm.pack(fill="x", pady=5)
        def change_path():
            d = filedialog.askdirectory(title="Datenbank-Ordner wählen")
            if d: self.settings["custom_db_path"] = d; self.lbl_path.config(text=f"Daten-Pfad:\n{d}")
        ttk.Button(p_btn_frm, text="Ordner ändern", command=change_path).pack(side="left", padx=2)
        ttk.Button(p_btn_frm, text="Standard", command=lambda: [self.settings.update({"custom_db_path":""}), self.lbl_path.config(text="Daten-Pfad:\nStandard-Ordner")]).pack(side="left")

        # FOOTER
        btn_frm = ttk.Frame(self, padding=10); btn_frm.pack(fill="x", side="bottom")
        ttk.Button(btn_frm, text="Abbrechen", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frm, text="Änderungen Speichern", style="Accent.TButton", command=self.do_save).pack(side="right", padx=5)
        
        self.nb.select(start_tab)

    def refresh_settings_shelf_list(self):
        self.shelf_list.delete(0, tk.END)
        for s in parse_shelves_string(self.var_shelves.get()): self.shelf_list.insert(tk.END, f"📦 {s['name']} ({s['rows']}x{s['cols']})")

    def do_save(self):
        try:
            self.settings.update({
                "shelves": self.var_shelves.get(),
                "logistics_order": self.var_logistics.get(),
                "label_row": self.ent_row.get().strip() or "Fach",
                "label_col": self.ent_col.get().strip() or "Slot",
                "num_ams": int(self.ent_ams.get()),
                "custom_locs": self.ent_custom.get().strip(),
                "use_affiliate": self.var_affiliate.get(),
                "rfid_mode": self.var_rfid.get(),
                "printer_url": self.ent_prn_url.get().strip(),
                "printer_api_key": self.ent_prn_key.get().strip()
            })
            self.on_save(self.settings); self.destroy()
        except: messagebox.showerror("Fehler", "AMS Anzahl muss eine Zahl sein.")

class ShelfVisualizer(tk.Toplevel):
    def __init__(self, parent, inventory, settings, spools):
        super().__init__(parent); self.inventory = inventory; self.settings = settings; self.spools = spools; self.title("Regal & AMS Übersicht")
        self.geometry("1200x850"); self.configure(bg=parent.cget('bg')); center_window(self, parent); self.image_cache = []
        
        self.parse_shelves(); self.shelf_data = {}; self.ams_data = {}; self.other_data = {}
        for item in self.inventory:
            try:
                t = str(item.get('type', '')); loc = str(item.get('loc_id', ''))
                if t in [s['name'] for s in self.parsed_shelves]: self.shelf_data[f"{t}_{loc}"] = item
                elif t.startswith("AMS"): self.ams_data[f"{t}_{loc}"] = item
                elif t and t != "VERBRAUCHT":
                    if t not in self.other_data: self.other_data[t] = []
                    self.other_data[t].append(item)
            except: pass
        
        canvas = tk.Canvas(self, bg=parent.cget('bg'), highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview); h_scroll = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set); h_scroll.pack(side="bottom", fill="x"); v_scroll.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        frame = ttk.Frame(canvas); frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=frame, anchor="nw")
        pad = ttk.Frame(frame, padding=20); pad.pack(fill="both", expand=True)
        lbl_r = self.settings.get("label_row", "Fach"); lbl_c = self.settings.get("label_col", "Slot"); logistics = self.settings.get("logistics_order", False)
        
        for shelf in self.parsed_shelves:
            ttk.Label(pad, text=f"📦 {shelf['name']}", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 10))
            for r in (range(shelf['rows'], 0, -1) if logistics else range(1, shelf['rows'] + 1)):
                ttk.Label(pad, text=f"{lbl_r} {r}", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
                row_frame = tk.Frame(pad, bg="#8B4513", padx=5, pady=2)
                row_frame.pack(anchor="w", pady=2)
                for c in range(1, shelf['cols'] + 1):
                    slot_name = f"{lbl_r} {r} - {lbl_c} {c}"; self.draw_slot(row_frame, str(c), self.shelf_data.get(f"{shelf['name']}_{slot_name}"), False, w=70, h=70)
        
        ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20)
        for a in range(1, self.settings.get("num_ams", 1) + 1):
            ams_name = f"AMS {a}"; ttk.Label(pad, text=ams_name, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 5))
            ams_frame = tk.Frame(pad, bg="#444444", padx=10, pady=10); ams_frame.pack(anchor="w")
            for i in range(1, 5): 
                cont = tk.Frame(ams_frame, bg="#444444"); cont.pack(side="left", fill="y", padx=10); ttk.Label(cont, text=f"Slot {i}", foreground="white", background="#444444").pack(pady=(0, 5)); self.draw_slot(cont, str(i), self.ams_data.get(f"{ams_name}_{i}"), True, 120, 100)
        
        if self.other_data:
            ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20); ttk.Label(pad, text="📦 Weitere Lagerorte & Kisten", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 5))
            for loc_name, items in self.other_data.items():
                ttk.Label(pad, text=loc_name, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
                loc_frame = tk.Frame(pad, bg="#333333", padx=5, pady=5); loc_frame.pack(anchor="w", pady=2); col_count, row_frame = 0, tk.Frame(loc_frame, bg="#333333"); row_frame.pack(anchor="w")
                for item in items:
                    if col_count >= 10: col_count = 0; row_frame = tk.Frame(loc_frame, bg="#333333"); row_frame.pack(anchor="w", pady=(5,0))
                    self.draw_slot(row_frame, item.get("loc_id", "") or "-", item, False, 80, 70); col_count += 1
    def parse_shelves(self):
        self.parsed_shelves = parse_shelves_string(self.settings.get("shelves", "REGAL|4|8"))
    def draw_slot(self, parent, label, item, is_ams, w=90, h=80):
        bg_colors, fg_col, txt, tooltip = ["#D2B48C"] if not is_ams else ["#666666"], "#555" if not is_ams else "#CCC", f"{label}\nLEER", "Leer"
        if item:
            cols = get_colors_from_text(item['color']); bg_colors = cols or ["#FFFFFF"]
            if bg_colors[0].startswith("#"):
                r, g, b = int(bg_colors[0][1:3], 16), int(bg_colors[0][3:5], 16), int(bg_colors[0][5:7], 16); fg_col = "white" if (r*0.299 + g*0.587 + b*0.114) < 128 else "black"
            else: fg_col = "black"
            sub = item.get('subtype', ''); net = calculate_net_weight(item.get('weight_gross','0'), item.get('spool_id',-1), self.spools)
            txt = f"{label}\n{item['brand'][:10]}\n{sub[:10]}\n{net}g"
            tooltip = f"ID: {item['id']}\n{item['brand']} - {item['color']}\n{item['material']} | Rest: {net}g"
        img = create_color_icon(bg_colors, (w, h), "black"); self.image_cache.append(img)
        lbl = tk.Label(parent, image=img, text=txt, compound="center", fg=fg_col, font=("Segoe UI", 8, "bold"), borderwidth=0)
        lbl.pack(side="left", padx=2, fill="y"); lbl.bind("<Enter>", lambda e: self.show_tip(e, tooltip)); lbl.bind("<Leave>", self.hide_tip)
    def show_tip(self, event, text): self.tip = tk.Toplevel(self); self.tip.wm_overrideredirect(True); self.tip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}"); tk.Label(self.tip, text=text, bg="#FFFFE0", relief="solid", borderwidth=1, padx=5, pady=2).pack()
    def hide_tip(self, event):
        if hasattr(self, 'tip'): self.tip.destroy()

class ShoppingListDialog(tk.Toplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(parent); self.app = app_instance; self.inventory = inventory; self.title("Einkaufsliste / Dashboard"); self.geometry("800x600"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        ttk.Label(self, text="🛒 Nachzubestellende & Verbrauchte Filamente", font=("Segoe UI", 14, "bold")).pack(pady=15)
        frm_list = ttk.Frame(self); frm_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.tree = ttk.Treeview(frm_list, columns=("brand", "color", "mat", "supplier", "sku", "price", "status"), show="headings"); self.tree.heading("brand", text="Marke"); self.tree.heading("color", text="Farbe"); self.tree.heading("mat", text="Mat."); self.tree.heading("supplier", text="Lieferant"); self.tree.heading("sku", text="SKU"); self.tree.heading("price", text="Preis"); self.tree.heading("status", text="Status")
        self.tree.column("mat", width=50); self.tree.column("price", width=60); self.tree.column("status", width=100); scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=scroll.set); self.tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y"); self.tree.bind("<Double-1>", lambda e: self.open_shop_link())
        self.populate(); btn_frm = ttk.Frame(self); btn_frm.pack(pady=10); ttk.Button(btn_frm, text="🔗 Im Shop öffnen", command=self.open_shop_link, style="Accent.TButton").pack(side="left", padx=10); ttk.Button(btn_frm, text="Als CSV exportieren (Excel)", command=self.export_csv).pack(side="left", padx=10); ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="left", padx=10)
    def populate(self):
        for i in self.inventory:
            if i.get('reorder') or i.get('type') == 'VERBRAUCHT':
                pr = ""
                if i.get('price'):
                    try: pr = f"{float(str(i['price']).replace(',','.')):.2f} €"
                    except: pr = str(i['price'])
                self.tree.insert("", "end", iid=str(i['id']), values=(i.get('brand',''), i.get('color',''), i.get('material',''), i.get('supplier',''), i.get('sku',''), pr, "MUSS KAUFEN" if i.get('reorder') else "Leer"))
    def open_shop_link(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showinfo("Info", "Bitte ein Filament auswählen.", parent=self)
        item = next((x for x in self.inventory if x['id'] == int(sel[0])), None)
        if not item or not item.get('link'): return messagebox.showinfo("Info", "Für dieses Filament ist leider kein Link hinterlegt.", parent=self)
        url = item['link'].strip(); url = url if url.startswith("http") else "https://" + url
        if self.app.settings.get("use_affiliate", True) and "bambulab.com" in url.lower() and "modelId=" not in url: url += ("&" if "?" in url else "?") + "modelId=1889832"
        webbrowser.open(url)
    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Einkaufsliste exportieren")
        if not filepath: return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f, delimiter=';').writerow(["Marke", "Farbe", "Material", "Lieferant", "SKU", "Preis", "Status", "Link"])
                for i in self.inventory:
                    if i.get('reorder') or i.get('type') == 'VERBRAUCHT': csv.writer(f, delimiter=';').writerow([i.get('brand',''), i.get('color',''), i.get('material',''), i.get('supplier',''), i.get('sku',''), i.get('price',''), "MUSS KAUFEN" if i.get('reorder') else "Leer", i.get('link','')])
            messagebox.showinfo("Exportiert", "Liste erfolgreich gespeichert!", parent=self)
        except Exception as e: messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}", parent=self)

class StatisticsDialog(tk.Toplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(parent)
        self.app = app_instance; self.inventory = inventory; self.title("📊 Finanz-Dashboard & Statistik")
        self.geometry("600x550"); self.configure(bg=parent.cget('bg')); center_window(self, parent)

        total_value, total_weight, total_spools, mat_stats = 0.0, 0, 0, {}
        for item in self.inventory:
            if item.get('type') == 'VERBRAUCHT': continue
            total_spools += 1
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.app.spools)
            total_weight += net
            val = 0.0
            try:
                price, cap = float(str(item.get('price', '0')).replace(',', '.')), float(str(item.get('capacity', '1000')))
                if cap > 0: val = (net / cap) * price
            except: pass
            total_value += val
            mat = item.get('material', 'Unbekannt') or 'Unbekannt'
            if mat not in mat_stats: mat_stats[mat] = {'count': 0, 'weight': 0, 'value': 0.0}
            mat_stats[mat]['count'] += 1; mat_stats[mat]['weight'] += net; mat_stats[mat]['value'] += val

        ttk.Label(self, text="💰 Bestands-Statistik & Finanzen", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))
        kpi_frame = tk.Frame(self, bg=parent.cget('bg')); kpi_frame.pack(fill="x", padx=20, pady=10)
        ttk.Label(kpi_frame, text="Gesamtwert:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=f"{total_value:.2f} €", font=("Segoe UI", 14, "bold"), foreground="#28a745").grid(row=0, column=1, sticky="w", padx=15, pady=2)
        ttk.Label(kpi_frame, text="Lagermenge:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=f"{(total_weight/1000):.2f} kg", font=("Segoe UI", 12, "bold")).grid(row=1, column=1, sticky="w", padx=15, pady=2)
        ttk.Label(kpi_frame, text="Aktive Spulen:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=str(total_spools), font=("Segoe UI", 12, "bold")).grid(row=2, column=1, sticky="w", padx=15, pady=2)
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)
        ttk.Label(self, text="Aufschlüsselung nach Material:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(5, 5))
        tree = ttk.Treeview(self, columns=("mat", "count", "weight", "value"), show="headings", height=8)
        for col, head, w in zip(("mat", "count", "weight", "value"), ("Material", "Spulen", "Gewicht (kg)", "Wert (€)"), (120, 60, 100, 100)): tree.heading(col, text=head); tree.column(col, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        for mat, stats in sorted(mat_stats.items(), key=lambda x: x[1]['value'], reverse=True): tree.insert("", "end", values=(mat, stats['count'], f"{(stats['weight']/1000):.2f}", f"{stats['value']:.2f} €"))
        ttk.Button(self, text="Schließen", command=self.destroy).pack(pady=10)

class FlowCalculatorDialog(tk.Toplevel):
    def __init__(self, parent, current_flow_entry=None):
        super().__init__(parent); self.title("🧪 Flow-Rechner (Kalibrierung)"); self.geometry("450x550"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        self.current_flow_entry = current_flow_entry
        
        ttk.Label(self, text="Flow Kalibrierung", font=("Segoe UI", 14, "bold")).pack(pady=10)
        ttk.Label(self, text="Gib hier deine Wandstärken-Messungen ein (eine pro Zeile):", font=("Segoe UI", 9)).pack(padx=20, anchor="w")
        
        self.txt_measurements = tk.Text(self, height=8, width=30, font=("Consolas", 10))
        self.txt_measurements.pack(padx=20, pady=5, fill="x")
        self.txt_measurements.bind("<KeyRelease>", lambda e: self.calculate())

        frm_params = ttk.Frame(self, padding=10); frm_params.pack(fill="x", padx=10)
        
        ttk.Label(frm_params, text="Ziel-Wandstärke (mm):").grid(row=0, column=0, sticky="w", pady=2)
        self.var_target = tk.StringVar(value="0.45")
        self.ent_target = ttk.Entry(frm_params, textvariable=self.var_target); self.ent_target.grid(row=0, column=1, sticky="ew", pady=2)
        self.var_target.trace_add("write", lambda n, i, m: self.calculate())

        ttk.Label(frm_params, text="Bisheriger Flow:").grid(row=1, column=0, sticky="w", pady=2)
        initial_flow = "0.98"
        if current_flow_entry and current_flow_entry.get(): initial_flow = current_flow_entry.get().replace(',', '.')
        self.var_old_flow = tk.StringVar(value=initial_flow)
        self.ent_old_flow = ttk.Entry(frm_params, textvariable=self.var_old_flow); self.ent_old_flow.grid(row=1, column=1, sticky="ew", pady=2)
        self.var_old_flow.trace_add("write", lambda n, i, m: self.calculate())

        frm_params.columnconfigure(1, weight=1)
        
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=15)
        
        self.lbl_result = ttk.Label(self, text="Mess-Durchschnitt: -", font=("Segoe UI", 10))
        self.lbl_result.pack(pady=2)
        self.lbl_new_flow = ttk.Label(self, text="NEUER FLOW: -", font=("Segoe UI", 12, "bold"), foreground=COLOR_ACCENT)
        self.lbl_new_flow.pack(pady=10)
        
        btn_frm = ttk.Frame(self); btn_frm.pack(pady=10, fill="x", padx=20)
        ttk.Button(btn_frm, text="Wert übernehmen", style="Accent.TButton", command=self.apply_value).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="left", expand=True, fill="x", padx=5)

    def calculate(self):
        try:
            lines = self.txt_measurements.get("1.0", tk.END).strip().split('\n')
            vals = [float(l.replace(',', '.').strip()) for l in lines if l.strip()]
            if not vals: return
            
            avg = sum(vals) / len(vals)
            target = float(self.var_target.get().replace(',', '.'))
            old_flow = float(self.var_old_flow.get().replace(',', '.'))
            
            # Formel: (Target / Average) * Old Flow
            new_flow = (target / avg) * old_flow
            
            self.lbl_result.config(text=f"Mess-Durchschnitt: {avg:.4f} mm ({len(vals)} Werte)")
            self.lbl_new_flow.config(text=f"NEUER FLOW: {new_flow:.4f}")
            self.calculated_value = f"{new_flow:.3f}".replace('.', ',')
        except:
            self.lbl_result.config(text="Mess-Durchschnitt: Fehler"); self.lbl_new_flow.config(text="NEUER FLOW: -")

    def apply_value(self):
        if hasattr(self, 'calculated_value') and self.current_flow_entry:
            self.current_flow_entry.delete(0, tk.END)
            self.current_flow_entry.insert(0, self.calculated_value)
            self.destroy()

class BackupDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, app_instance):
        super().__init__(parent); self.data_manager = data_manager; self.app = app_instance; self.title("Backup & Restore"); self.geometry("400x200"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        ttk.Label(self, text="Datenbank Backup", font=("Segoe UI", 12, "bold")).pack(pady=15); ttk.Button(self, text="📥 Backup exportieren", command=self.export_data).pack(fill="x", padx=40, pady=10); ttk.Button(self, text="📤 Backup importieren", command=self.import_data).pack(fill="x", padx=40, pady=10)
    def export_data(self):
        fp = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP", "*.zip")], initialfile="VibeSpool_Backup.zip")
        if not fp: return
        try:
            with zipfile.ZipFile(fp, 'w') as z:
                for f, n in [(self.data_manager.data_file, "inventory.json"), (self.data_manager.settings_file, "settings.json"), (self.data_manager.spools_file, "spools.json")]:
                    if os.path.exists(f): z.write(f, n)
            messagebox.showinfo("Erfolg", "Backup erstellt!", parent=self); self.destroy()
        except Exception as e: messagebox.showerror("Fehler", str(e), parent=self)
    def import_data(self):
        fp = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
        if not fp: return
        if messagebox.askyesno("Warnung", "Daten werden überschrieben!", parent=self):
            try:
                with zipfile.ZipFile(fp, 'r') as z: z.extractall(self.data_manager.base_dir)
                self.app.refresh_all_data(); messagebox.showinfo("Erfolg", "Backup geladen!", parent=self.app.root); self.destroy()
            except Exception as e: messagebox.showerror("Fehler", str(e), parent=self)

class PrinterJobDialog(tk.Toplevel):
    def __init__(self, parent, jobs, on_select_job):
        super().__init__(parent); self.on_select_job = on_select_job; self.title("Drucker-Historie"); self.geometry("600x450"); center_window(self, parent)
        self.transient(parent); self.grab_set()
        ttk.Label(self, text="Wähle einen Druckauftrag aus:", font=FONT_BOLD).pack(pady=10)
        
        frm = ttk.Frame(self); frm.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree = ttk.Treeview(frm, columns=("file", "status", "used"), show="headings")
        self.tree.heading("file", text="Datei"); self.tree.heading("status", text="Status"); self.tree.heading("used", text="Verbrauch (g)")
        self.tree.column("file", width=300); self.tree.column("status", width=100, anchor="center"); self.tree.column("used", width=100, anchor="center")
        
        scroll = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=scroll.set); self.tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        
        for i, j in enumerate(jobs):
            used = f"{j.get('filament_used', 0):.1f}g"
            self.tree.insert("", "end", iid=str(i), values=(j.get('filename', 'Unbekannt'), j.get('status', '-'), used))
        
        def confirm():
            sel = self.tree.selection()
            if not sel: return
            job = jobs[int(sel[0])]
            self.on_select_job(job.get('filament_used', 0)); self.destroy()
            
        ttk.Button(self, text="Diesen Verbrauch abziehen", command=confirm, style="Accent.TButton").pack(pady=15, fill="x", padx=20)

class FilamentApp:
    def __init__(self, root):
        self.root = root; 
        self.data_manager = DataManager(DEFAULT_SETTINGS)
        # Explicitly hint types to help Pylance
        self.inventory: list[dict] = []
        self.settings: dict = {}
        self.spools: list[dict] = []
        
        # Suppress type checking for this assignment since load_all returns (list, dict, list)
        inventory_data, settings_data, spools_data = self.data_manager.load_all(DEFAULT_SETTINGS)
        self.inventory = inventory_data if isinstance(inventory_data, list) else []
        self.settings = settings_data if isinstance(settings_data, dict) else {}
        self.spools = spools_data if isinstance(spools_data, list) else []
        
        # Already assigned above with type safety checks
        
        self.root.geometry(str(self.settings.get("geometry", "1500x980")))
        self.root.title(f"VibeSpool {APP_VERSION}"); self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.icon_cache = []

        # --- PRE-INIT UI ATTRIBUTES ---
        self.nav_btns: list[tk.Button] = []
        self.nav_sidebar = tk.Frame(root, width=80) 
        self.nav_sidebar.pack(side="left", fill="y")
        self.nav_sidebar.pack_propagate(False)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=26)

        self.var_price, self.var_capacity, self.var_gross = tk.StringVar(value=""), tk.StringVar(value="1000"), tk.StringVar(value="")        
        for v in [self.var_price, self.var_capacity, self.var_gross]: v.trace_add("write", lambda n, i, m: self.update_net_weight_display())

        # --- MAIN LAYOUT ---
        top_bar = ttk.Frame(root, padding=10); top_bar.pack(fill="x", side="top"); ttk.Label(top_bar, text="Suche:").pack(side="left"); self.search_var = tk.StringVar(); self.search_var.trace_add("write", lambda n, i, m: self.refresh_table()); ttk.Entry(top_bar, textvariable=self.search_var, width=15).pack(side="left", padx=5)
        self.filter_mat_var, self.filter_color_var, self.filter_loc_var = tk.StringVar(value="Alle Materialien"), tk.StringVar(value="Alle Farben"), tk.StringVar(value="Alle Orte")
        self.combo_filter_mat = ttk.Combobox(top_bar, textvariable=self.filter_mat_var, state="readonly", width=15); self.combo_filter_mat.pack(side="left", padx=5); self.combo_filter_mat.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.combo_filter_color = ttk.Combobox(top_bar, textvariable=self.filter_color_var, state="readonly", width=15); self.combo_filter_color.pack(side="left", padx=5); self.combo_filter_color.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.combo_filter_loc = ttk.Combobox(top_bar, textvariable=self.filter_loc_var, state="readonly", width=15); self.combo_filter_loc.pack(side="left", padx=5); self.combo_filter_loc.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        ttk.Button(top_bar, text="🔄 Reset", command=self.reset_filters).pack(side="left", padx=5); ttk.Label(top_bar, text=" Quick-ID:").pack(side="left", padx=(10,0)); self.entry_scan = ttk.Entry(top_bar, width=8); self.entry_scan.pack(side="left", padx=5); self.entry_scan.bind("<Return>", self.on_quick_scan)
        ttk.Button(top_bar, text="📷", width=3, command=self.scan_qr_webcam).pack(side="left")
        self.btn_opts = ttk.Menubutton(top_bar, text="⚙ Optionen")
        self.menu_opts = tk.Menu(self.btn_opts, tearoff=0)
        self.menu_opts.add_command(label="⚙ Alle Einstellungen öffnen", command=self.open_settings)
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="📦 Lager-Layout planen", command=lambda: self.open_settings(0))
        self.menu_opts.add_command(label="🔌 Hardware & AMS", command=lambda: self.open_settings(1))
        self.menu_opts.add_command(label="🤖 Drucker-Anbindung", command=lambda: self.open_settings(2))
        self.menu_opts.add_command(label="⚙ System-Optionen", command=lambda: self.open_settings(3))
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="🔄 Update-Check", command=self.manual_update_check)
        self.btn_opts["menu"] = self.menu_opts
        self.btn_opts.pack(side="right", padx=5)
        
        ttk.Button(top_bar, text="💾 Backup", command=lambda: BackupDialog(self.root, self.data_manager, self)).pack(side="right", padx=5); ttk.Button(top_bar, text="🛒 Einkaufsliste", command=lambda: ShoppingListDialog(self.root, self.inventory, self)).pack(side="right", padx=5); ttk.Button(top_bar, text="☕ Spenden", command=self.open_paypal).pack(side="right", padx=5); self.btn_theme = ttk.Button(top_bar, text="...", command=self.toggle_theme); self.btn_theme.pack(side="right", padx=5); self.update_theme_button_text()
        
        # --- SIDEBAR BUTTONS ---
        self.nav_btns = []
        def add_nav_btn(text, cmd, icon_txt=None):
            btn = tk.Button(self.nav_sidebar, text=f"{icon_txt}\n{text}" if icon_txt else text, command=cmd, 
                           font=("Segoe UI", 8), bd=0, pady=15, cursor="hand2")
            btn.pack(fill="x")
            self.nav_btns.append(btn)
            btn.bind("<Enter>", lambda e: self.on_nav_btn_hover(btn, True))
            btn.bind("<Leave>", lambda e: self.on_nav_btn_hover(btn, False))

        add_nav_btn("Regal", lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools), "📦")
        add_nav_btn("Spulen", lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown), "🧵")
        add_nav_btn("Finanzen", lambda: StatisticsDialog(self.root, self.inventory, self), "📊")
        add_nav_btn("Swap", self.quick_swap_dialog, "🔄")
        add_nav_btn("Flow", lambda: FlowCalculatorDialog(self.root, self.entry_flow), "🧪")
        self.nav_sep = tk.Label(self.nav_sidebar, height=1)
        self.nav_sep.pack(fill="x", pady=10)
        add_nav_btn("Neu", self.clear_inputs, "➕")
        
        # (NACH der Nav-Sidebar-Definition)
        main_frame = ttk.Frame(root, padding=10); main_frame.pack(fill="both", expand=True)
        
        # --- NEU: Ein Container für die Haupt-Formularleiste + Scrollbar ---
        self.form_container = tk.Frame(main_frame, width=360) # Etwas breiter für die Scrollbar
        self.form_container.pack(side="left", fill="y", padx=(0, 10))
        self.form_container.pack_propagate(False)

        # Das Canvas macht das Scrollen möglich
        self.form_canvas = tk.Canvas(self.form_container, highlightthickness=0, width=350)
        self.form_scrollbar = ttk.Scrollbar(self.form_container, orient="vertical", command=self.form_canvas.yview)
        
        # Das eigentliche Frame, in das die Tabs und Buttons kommen
        # Wir müssen tk.Frame nutzen, um die Hintergrundfarbe im apply_theme setzen zu können.
        sidebar = tk.Frame(self.form_canvas, width=350)
        # Referenz für apply_theme speichern!
        self.scrollable_form_frame = sidebar
        
        # Canvas konfigurieren, damit es mit dem Frame mitwächst
        sidebar.bind(
            "<Configure>",
            lambda e: self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))
        )
        self.form_canvas.create_window((0, 0), window=sidebar, anchor="nw", width=350)
        self.form_canvas.configure(yscrollcommand=self.form_scrollbar.set)

        # Scrollbar und Canvas platzieren
        self.form_scrollbar.pack(side="right", fill="y")
        self.form_canvas.pack(side="left", fill="both", expand=True)

        self.notebook = ttk.Notebook(sidebar); self.notebook.pack(fill="both", expand=True)
        tab_basis, tab_erp = ttk.Frame(self.notebook, padding=10), ttk.Frame(self.notebook, padding=10); self.notebook.add(tab_basis, text="Basis & Lager"); self.notebook.add(tab_erp, text="Kaufmännisch")

        frm_id = ttk.Frame(tab_basis); frm_id.pack(fill="x", pady=2); ttk.Label(frm_id, text="ID:").pack(side="left"); self.entry_id = ttk.Entry(frm_id, width=10, font=FONT_BOLD); self.entry_id.pack(side="left", padx=5)
        ttk.Label(frm_id, text="RFID:").pack(side="left", padx=(10, 0)); self.entry_rfid = ttk.Entry(frm_id, width=15); self.entry_rfid.pack(side="left", padx=5)
        ttk.Label(tab_basis, text="Marke:").pack(anchor="w", pady=(10,0)); self.entry_brand = ttk.Entry(tab_basis, font=FONT_MAIN); self.entry_brand.pack(fill="x", pady=2)
        ttk.Label(tab_basis, text="Material:").pack(anchor="w", pady=(10,0)); self.combo_material = ttk.Combobox(tab_basis, values=MATERIALS, font=FONT_MAIN); self.combo_material.pack(fill="x", pady=2)
        ttk.Label(tab_basis, text="Farbe:").pack(anchor="w", pady=(10,0)); frm_col = ttk.Frame(tab_basis); frm_col.pack(fill="x", pady=2); self.combo_color = ttk.Combobox(frm_col, values=COMMON_COLORS, font=FONT_MAIN); self.combo_color.pack(side="left", fill="x", expand=True); self.combo_color.bind("<KeyRelease>", self.update_color_preview); self.combo_color.bind("<<ComboboxSelected>>", self.update_color_preview)
        def pick_color():
            color_code = colorchooser.askcolor(title="Eigene Farbe wählen", parent=self.root)[1]
            if color_code:
                current_text = re.sub(r'\s*\(?#[0-9a-fA-F]{6}\)?', '', self.combo_color.get().strip()).strip()
                self.combo_color.set(f"{current_text} ({color_code.upper()})" if current_text else color_code.upper()); self.update_color_preview()
        ttk.Button(frm_col, text="🎨", width=3, command=pick_color).pack(side="left", padx=5); self.lbl_color_preview = tk.Label(frm_col, borderwidth=0); self.lbl_color_preview.pack(side="left"); self.update_color_preview()
        ttk.Label(tab_basis, text="Finish:").pack(anchor="w", pady=(10,0)); self.combo_subtype = ttk.Combobox(tab_basis, values=SUBTYPES, font=FONT_MAIN); self.combo_subtype.pack(fill="x", pady=2)
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(tab_basis, text="Spule / Leergewicht:").pack(anchor="w", pady=(5,0)); self.combo_spool = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN); self.combo_spool.pack(fill="x", pady=2); self.combo_spool.bind("<<ComboboxSelected>>", lambda e: self.update_net_weight_display())
        ttk.Label(tab_basis, text="Original-Inhalt (Netto g):").pack(anchor="w", pady=(10,0)); self.entry_capacity = ttk.Entry(tab_basis, font=FONT_MAIN, textvariable=self.var_capacity); self.entry_capacity.pack(fill="x", pady=2)
        ttk.Label(tab_basis, text="Gewicht auf Waage (Brutto g):").pack(anchor="w", pady=(10,0))
        frm_gross = ttk.Frame(tab_basis); frm_gross.pack(fill="x", pady=2)
        self.entry_gross = ttk.Entry(frm_gross, font=FONT_MAIN, textvariable=self.var_gross)
        self.entry_gross.pack(side="left", fill="x", expand=True)
        btn_sync = ttk.Button(frm_gross, text="🤖 Sync", width=8, command=self.subtract_printer_usage)
        btn_sync.pack(side="left", padx=(5,0))
        btn_sync.bind("<Enter>", lambda e: self.show_tip(e, "Letzten Druckverbrauch von Moonraker abrufen"))
        btn_sync.bind("<Leave>", self.hide_tip)
        
        self.lbl_net_weight = ttk.Label(tab_basis, text="Netto (Rest): 0 g | Wert: -", font=("Segoe UI", 10, "bold"), foreground=COLOR_ACCENT); self.lbl_net_weight.pack(anchor="w", pady=(10,5))
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(tab_basis, text="Flow Ratio:").pack(anchor="w"); self.entry_flow = ttk.Entry(tab_basis, width=10); self.entry_flow.pack(anchor="w", pady=2)
        ttk.Label(tab_basis, text="Pressure Adv:").pack(anchor="w", pady=(5,0)); self.entry_pa = ttk.Entry(tab_basis); self.entry_pa.pack(fill="x", pady=2)
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(tab_basis, text="Lagerort:").pack(anchor="w"); self.combo_type = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN); self.combo_type.pack(fill="x", pady=2); self.combo_type.bind("<<ComboboxSelected>>", self.update_slot_dropdown)
        ttk.Label(tab_basis, text="Slot / Nr.:").pack(anchor="w", pady=(5,0)); self.combo_loc_id = ttk.Combobox(tab_basis, font=FONT_MAIN); self.combo_loc_id.pack(fill="x", pady=2)
        self.var_reorder = tk.BooleanVar(); ttk.Checkbutton(tab_basis, text="Auf Einkaufsliste setzen!", variable=self.var_reorder).pack(anchor="w", pady=10)

        ttk.Label(tab_erp, text="Lieferant / Shop:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_supplier = ttk.Entry(tab_erp); self.entry_supplier.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="SKU / Art-Nr.:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_sku = ttk.Entry(tab_erp); self.entry_sku.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Preis (€):").grid(row=2, column=0, sticky="w", pady=5); self.entry_price = ttk.Entry(tab_erp, textvariable=self.var_price); self.entry_price.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Link:").grid(row=3, column=0, sticky="w", pady=5); self.entry_link = ttk.Entry(tab_erp); self.entry_link.grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Separator(tab_erp, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(tab_erp, text="Nozzle Temp (°C):").grid(row=5, column=0, sticky="w", pady=5); self.entry_temp_n = ttk.Entry(tab_erp); self.entry_temp_n.grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Bed Temp (°C):").grid(row=6, column=0, sticky="w", pady=5); self.entry_temp_b = ttk.Entry(tab_erp); self.entry_temp_b.grid(row=6, column=1, sticky="ew", pady=2)
        tab_erp.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(sidebar)
        btn_frame.pack(fill="x", pady=(15, 0))
        ttk.Button(btn_frame, text="Neu Hinzufügen", command=self.add_filament, style="Accent.TButton").pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Änderungen Speichern", command=self.update_filament).pack(fill="x", pady=3)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(btn_frame, text="📦 Regal & AMS Ansicht", command=lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools)).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🧵 Leerspulen verwalten", command=lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown)).pack(fill="x", pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(btn_frame, text="Felder leeren", command=self.clear_inputs).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="🔄 Quick-Swap", command=self.quick_swap_dialog).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Löschen", command=self.delete_filament, style="Delete.TButton").pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="📊 Finanz-Dashboard", command=lambda: StatisticsDialog(self.root, self.inventory, self)).pack(fill="x", pady=8)

        table_frame = ttk.Frame(main_frame); table_frame.pack(side="right", fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"), show="tree headings")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview); self.tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y"); self.tree.pack(fill="both", expand=True)
        self.tree.column("#0", width=40, anchor="center", stretch=False)
        for col, text in zip(("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"), ["ID", "Marke", "Material", "Farbe", "Finish", "Rest(g)", "Flow", "Ort", "Status"]): self.tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(c, False))
        self.tree.column("id", width=40, anchor="center"); self.tree.column("brand", width=120); self.tree.column("material", width=60, anchor="center"); self.tree.column("weight", width=60, anchor="center"); self.tree.column("flow", width=50, anchor="center"); self.tree.column("status", width=90, anchor="center"); self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.update_locations_dropdown(); self.update_spool_dropdown(); self.update_filter_dropdowns(); self.clear_inputs(); self.refresh_table()
        def run_update_check():
            res = check_for_updates(GITHUB_REPO, APP_VERSION)
            if res:
                latest, url = res
                self.root.after(0, lambda: self.show_update_prompt(latest, url))
        threading.Thread(target=run_update_check, daemon=True).start()
        self.apply_theme()

    def update_color_preview(self, event=None):
        cols = get_colors_from_text(self.combo_color.get())
        img = create_color_icon(cols, (30, 20), "#888888")
        self.lbl_color_preview.config(image=img); setattr(self.lbl_color_preview, 'image', img) # type: ignore

    def show_tip(self, event, text):
        self.tip = tk.Toplevel(self.root); self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
        tk.Label(self.tip, text=text, bg="#FFFFE0", relief="solid", borderwidth=1, padx=5, pady=2).pack()

    def hide_tip(self, event=None):
        if hasattr(self, 'tip') and self.tip: self.tip.destroy()

    def open_paypal(self):
        if messagebox.askyesno("☕ Kaffee spendieren", "Möchtest du zur PayPal-Seite weitergeleitet werden?"): webbrowser.open("https://paypal.me/florianfranck")

    def show_update_prompt(self, latest, url):
        upd = tk.Toplevel(self.root); upd.title("VibeSpool Update"); upd.geometry("400x150"); upd.configure(bg=self.root.cget('bg')); upd.attributes('-topmost', True); center_window(upd, self.root)
        ttk.Label(upd, text=f"Version {latest} ist verfügbar!", font=("Segoe UI", 12, "bold")).pack(pady=15)
        btn_frm = ttk.Frame(upd); btn_frm.pack(pady=10)
        ttk.Button(btn_frm, text="Laden", command=lambda: [webbrowser.open(url), upd.destroy()]).pack(side="left", padx=5); ttk.Button(btn_frm, text="Später", command=upd.destroy).pack(side="left", padx=5)

    def on_closing(self): self.settings["geometry"] = self.root.geometry(); self.data_manager.save_settings(self.settings); self.root.destroy()
    
    def apply_theme(self):
        theme = self.settings.get("theme", "dark"); c = THEMES[theme]; self.root.configure(bg=c["bg"]); s = self.style
        s.configure(".", background=c["bg"], foreground=c["fg"], font=FONT_MAIN)
        s.configure("TLabel", background=c["bg"], foreground=c["fg"])
        s.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
        s.map("TCheckbutton", background=[("active", c["bg"])], foreground=[("active", c["fg"])])
        s.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        s.configure("TLabelframe.Label", background=c["bg"], foreground=c["lbl_frame"])
        s.configure("Treeview", background=c["tree_bg"], fieldbackground=c["tree_bg"], foreground=c["tree_fg"])
        s.configure("Treeview.Heading", background=c["head_bg"], foreground=c["head_fg"])
        s.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["entry_fg"])
        s.configure("TButton", background=c["bg"], foreground=c["fg"])
        s.map("Treeview", background=[("selected", COLOR_ACCENT)])
        btn_h = "#505050" if theme == "dark" else "#d0d0d0"
        s.map("TButton", background=[("active", btn_h)], foreground=[("active", c["fg"])])
        nb_bg, tab_bg, tab_fg, cb_bg, cb_fg = (("#2b2b2b", "#3c3f41", "white", "#3c3f41", "white") if theme == "dark" else ("#f0f0f0", "#e1e1e1", "black", "#ffffff", "black"))
        s.configure("TNotebook", background=nb_bg, borderwidth=0)
        s.configure("TNotebook.Tab", background=tab_bg, foreground=tab_fg, padding=[10, 2], borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "white")])
        s.configure("TCombobox", fieldbackground=cb_bg, background=nb_bg, foreground=cb_fg)
        s.map("TCombobox", fieldbackground=[("readonly", cb_bg)], selectbackground=[("readonly", COLOR_ACCENT)], selectforeground=[("readonly", "white")])
        self.root.option_add('*TCombobox*Listbox.background', cb_bg); self.root.option_add('*TCombobox*Listbox.foreground', cb_fg)
        s.configure("Accent.TButton", foreground="white", background=COLOR_ACCENT, borderwidth=0); s.configure("Delete.TButton", foreground="white", background=COLOR_DELETE, borderwidth=0)
        
        # --- NAV SIDEBAR THEME ---
        nav_bg = "#1e1e1e" if theme == "dark" else "#d0d0d0"
        nav_fg = "white" if theme == "dark" else "black"
        
        # Nur noch die nav_sidebar färben
        self.nav_sidebar.config(bg=nav_bg)
        
        self.nav_sep.config(bg="#333333" if theme == "dark" else "#bbbbbb")
        for btn in self.nav_btns:
            btn.config(bg=nav_bg, fg=nav_fg, activebackground="#3c3f41" if theme == "dark" else "#e1e1e1", activeforeground=nav_fg)
            
        # --- THEME FÜR DAS FORMULAR-CANVAS & CONTAINER (Bleibt erhalten!) ---
        c = THEMES[theme]
        self.form_container.config(bg=c["bg"])
        self.form_canvas.config(bg=c["bg"])
        self.scrollable_form_frame.config(bg=c["bg"])


    def on_nav_btn_hover(self, btn, is_enter):
        theme = self.settings.get("theme", "dark")
        if is_enter:
            btn.config(bg="#3c3f41" if theme == "dark" else "#e1e1e1")
        else:
            btn.config(bg="#1e1e1e" if theme == "dark" else "#d0d0d0")

    def toggle_theme(self): self.settings["theme"] = "dark" if self.settings.get("theme") == "light" else "light"; self.data_manager.save_settings(self.settings); self.apply_theme(); self.update_theme_button_text()
    def update_theme_button_text(self): self.btn_theme.config(text="☀️" if self.settings.get("theme") == "dark" else "🌙")
    def get_dynamic_locations(self):
        locs = [s['name'] for s in parse_shelves_string(self.settings.get("shelves", "REGAL|4|8"))]
        for i in range(1, self.settings.get("num_ams", 1) + 1): locs.append(f"AMS {i}")
        for c in self.settings.get("custom_locs", "").split(","):
            if c.strip(): locs.append(c.strip())
        locs.extend(["LAGER", "VERBRAUCHT"]); return locs
    def update_locations_dropdown(self): self.combo_type['values'] = self.get_dynamic_locations()
    def update_spool_dropdown(self):
        _, _, self.spools = self.data_manager.load_all(DEFAULT_SETTINGS) # type: ignore
        values = ["-"] + [f"{s['id']} - {s['name']}" for s in self.spools]; curr = self.combo_spool.get(); self.combo_spool['values'] = values
        if curr not in values: self.combo_spool.current(0)
    def get_selected_spool_id(self):
        try: return -1 if self.combo_spool.get() == "-" else int(self.combo_spool.get().split(" - ")[0])
        except: return -1
    def update_net_weight_display(self, event=None):
        try:
            gross_str = self.var_gross.get().strip().replace(',', '.')
            if not gross_str: self.lbl_net_weight.config(text="Netto: 0 g | Wert: -"); return
            net = calculate_net_weight(gross_str, self.get_selected_spool_id(), self.spools); price_str = self.var_price.get().strip().replace(',', '.'); cap_str, val_str = self.var_capacity.get().strip(), ""
            if price_str and cap_str:
                try:
                    p, c = float(price_str), float(cap_str)
                    if c > 0: val_str = f" | Wert: {(net / c) * p:.2f} €"
                except: pass
            self.lbl_net_weight.config(text=f"Netto: {int(net)} g{val_str}")
        except: self.lbl_net_weight.config(text="Netto: 0 g | Wert: -")
    def open_settings(self, start_tab=0):
        def on_save(s): self.settings = s; self.data_manager.save_settings(s); self.update_locations_dropdown(); self.update_slot_dropdown(); self.update_filter_dropdowns()
        SettingsDialog(self.root, self.data_manager, on_save, start_tab)
    def manual_update_check(self):
        latest, url = check_for_updates(GITHUB_REPO, APP_VERSION) or (None, None)
        if latest: self.show_update_prompt(latest, url)
        else: messagebox.showinfo("Aktuell", f"Du nutzt bereits die aktuellste Version (v{APP_VERSION}).")
    def update_slot_dropdown(self, event=None):
        loc = self.combo_type.get()
        if loc.startswith("AMS"): self.combo_loc_id['values'] = ["1", "2", "3", "4"]
        else:
            for s in parse_shelves_string(self.settings.get("shelves", "REGAL|4|8")):
                if s['name'] == loc: r, c, log = s['rows'], s['cols'], self.settings.get("logistics_order"); self.combo_loc_id['values'] = [f"{self.settings.get('label_row')} {rw} - {self.settings.get('label_col')} {cl}" for rw in (range(r, 0, -1) if log else range(1, r + 1)) for cl in range(1, c + 1)]; return
            self.combo_loc_id['values'] = ["-"]
    def subtract_printer_usage(self):
        url = self.settings.get("printer_url")
        if not url:
            messagebox.showwarning("Drucker-Sync", "Bitte zuerst die Drucker-URL in den Einstellungen hinterlegen.")
            return
        
        usage_g = fetch_last_print_usage(url, self.settings.get("printer_api_key"))
        if usage_g is None:
            messagebox.showerror("Drucker-Sync", "Fehler beim Abrufen der Druckerdaten. Ist Moonraker erreichbar?")
            return
        
        try:
            curr_gross = float(self.var_gross.get().strip().replace(',', '.') or 0)
            if curr_gross <= 0:
                messagebox.showinfo("Drucker-Sync", f"Drucker meldet {usage_g:.1f}g Verbrauch. Aber aktuelles Brutto-Gewicht ist 0. Bitte zuerst Brutto-Gewicht eingeben.")
                return
            
            if messagebox.askyesno("Drucker-Sync", f"Der letzte Druck hat {usage_g:.1f}g verbraucht.\nSoll dieser Wert vom Brutto-Gewicht ({curr_gross:.1f}g) abgezogen werden?"):
                new_gross = max(0, curr_gross - usage_g)
                self.var_gross.set(f"{new_gross:.1f}")
                messagebox.showinfo("Erfolg", f"Gewicht aktualisiert! Neues Brutto: {new_gross:.1f}g\n\nVergiss nicht, die Änderungen zu speichern!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnungsfehler: {e}")

    def treeview_sort_column(self, col, reverse):
        def get_sort_value(i):
            if col == "location":
                return f"{i.get('type', '')} {i.get('loc_id', '')}".strip()
            elif col == "weight":
                return str(calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools))
            elif col == "status":
                return "VERBRAUCHT" if i.get('type') == "VERBRAUCHT" else "KAUFEN" if i.get('reorder') else ""
            return str(i.get(col, ""))

        self.inventory.sort(key=lambda i: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', get_sort_value(i))], reverse=reverse)
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))
        self.refresh_table()
    def update_filter_dropdowns(self):
        mats = sorted(list(set(i.get("material", "") for i in self.inventory if i.get("material")))); cols = sorted(list(set(i.get("color", "") for i in self.inventory if i.get("color")))); locs = self.get_dynamic_locations()
        self.combo_filter_mat['values'] = ["Alle Materialien"] + mats; self.combo_filter_color['values'] = ["Alle Farben"] + cols; self.combo_filter_loc['values'] = ["Alle Orte"] + locs
    def reset_filters(self): self.filter_mat_var.set("Alle Materialien"); self.filter_color_var.set("Alle Farben"); self.filter_loc_var.set("Alle Orte"); self.search_var.set(""); self.refresh_table()
    def refresh_table(self, *args):
        self.icon_cache = []
        for row in self.tree.get_children(): self.tree.delete(row)
        filters = {"material": self.filter_mat_var.get(), "color": self.filter_color_var.get(), "location": self.filter_loc_var.get()}
        for i in self.data_manager.get_filtered_inventory(self.inventory, self.search_var.get(), filters):
            loc_s, stat = f"{i['type']} {i.get('loc_id', '')}".strip(), " | ".join(filter(None, ["VERBRAUCHT" if i['type'] == "VERBRAUCHT" else "", "KAUFEN" if i.get('reorder') else ""]))
            icon = create_color_icon(get_colors_from_text(i['color'])); self.icon_cache.append(icon); net = calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools)
            self.tree.insert("", "end", iid=str(i['id']), image=icon, values=(i['id'], i['brand'], i.get('material', '-'), i['color'], i.get('subtype', 'Standard'), f"{net}g", i.get('flow', 'Auto' if 'bambu' in i['brand'].lower() else '-'), loc_s, stat), tags=(["alert"] if i.get('reorder') else ["grayed"] if i['type'] == "VERBRAUCHT" else []))
        self.tree.tag_configure("alert", background="#ffe6e6", foreground="#d9534f"); self.tree.tag_configure("grayed", foreground="#999999")
    def get_input_data(self):
        try:
            return {"id": int(self.entry_id.get().strip()) if self.entry_id.get().strip() else None, "rfid": self.entry_rfid.get().strip(), "brand": self.entry_brand.get().strip(), "material": self.combo_material.get().strip(), "color": self.combo_color.get().strip(), "subtype": self.combo_subtype.get().strip(), "type": self.combo_type.get(), "loc_id": self.combo_loc_id.get().strip(), "flow": self.entry_flow.get().strip(), "pa": self.entry_pa.get().strip(), "spool_id": self.get_selected_spool_id(), "weight_gross": float(self.var_gross.get().strip().replace(',', '.') or 0), "capacity": int(self.var_capacity.get().strip() or 1000), "is_empty": self.combo_type.get() == "VERBRAUCHT", "reorder": self.var_reorder.get(), "supplier": self.entry_supplier.get().strip(), "sku": self.entry_sku.get().strip(), "price": self.var_price.get().strip(), "link": self.entry_link.get().strip(), "temp_n": self.entry_temp_n.get().strip(), "temp_b": self.entry_temp_b.get().strip()}
        except: messagebox.showwarning("Fehler", "Zahlenformat ungültig."); return None
    def add_filament(self):
        d = self.get_input_data()
        if not d: return
        d['id'] = d['id'] or (max([int(i['id']) for i in self.inventory], default=0) + 1); self.inventory.append(d); self.data_manager.save_inventory(self.inventory); self.refresh_table(); self.clear_inputs()
    def update_filament(self):
        sel = self.tree.selection()
        if not sel: return
        d = self.get_input_data()
        if not d: return
        idx = next(i for i, item in enumerate(self.inventory) if item['id'] == int(sel[0])); d['id'] = d['id'] or int(sel[0]); self.inventory[idx] = d; self.data_manager.save_inventory(self.inventory); self.refresh_table(); self.tree.selection_set(str(d['id']))
    def delete_filament(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Löschen", "Wirklich löschen?"): return
        self.inventory = [i for i in self.inventory if i['id'] != int(sel[0])]; self.data_manager.save_inventory(self.inventory); self.refresh_table(); self.clear_inputs()
    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        i = next((x for x in self.inventory if x['id'] == int(sel[0])), None)
        if not i: return
        self.clear_inputs(deselect=False); self.entry_id.insert(0, str(i['id'])); self.entry_rfid.insert(0, i.get('rfid', '')); self.entry_brand.insert(0, i['brand']); self.combo_material.set(i.get('material', 'PLA')); self.combo_color.set(i['color']); self.combo_subtype.set(i.get('subtype', 'Standard')); self.update_color_preview(); self.combo_type.set(i['type']); self.update_slot_dropdown(); self.combo_loc_id.set(i.get('loc_id', '')); self.entry_flow.insert(0, i.get('flow', '')); self.entry_pa.insert(0, i.get('pa', '')); self.var_reorder.set(i.get('reorder', False))
        for val in self.combo_spool['values']:
            if val.startswith(f"{i.get('spool_id', -1)} -"): self.combo_spool.set(val); break
        self.var_capacity.set(str(i.get('capacity', 1000))); gross = str(i.get('weight_gross', '0')).replace(',', '.'); float_g = float(gross) if gross else 0; self.var_gross.set(str(float_g).rstrip('0').rstrip('.') if float_g > 0 else ""); self.var_price.set(str(i.get('price', ''))); self.update_net_weight_display(); self.entry_supplier.insert(0, i.get('supplier', '')); self.entry_sku.insert(0, i.get('sku', '')); self.entry_link.insert(0, i.get('link', '')); self.entry_temp_n.insert(0, i.get('temp_n', '')); self.entry_temp_b.insert(0, i.get('temp_b', ''))
    
    def clear_inputs(self, deselect=True):
        for e in [self.entry_id, self.entry_rfid, self.entry_brand, self.entry_flow, self.entry_pa, self.entry_supplier, self.entry_sku, self.entry_link, self.entry_temp_n, self.entry_temp_b]: 
            e.delete(0, tk.END)
        self.var_capacity.set("1000")
        self.var_gross.set("")
        self.var_price.set("")
        self.combo_color.set("")
        self.combo_loc_id.set("")
        self.combo_material.current(0)
        self.combo_subtype.current(0)
        self.combo_type.current(0)
        self.combo_spool.current(0)
        self.update_net_weight_display()
        self.update_slot_dropdown()
        self.var_reorder.set(False)
        self.update_color_preview()
        if deselect: 
            self.tree.selection_remove(self.tree.selection())

    def quick_swap_dialog(self):
        sel = self.tree.selection()
        if not sel: 
            return messagebox.showinfo("Info", "Bitte zuerst eine Spule auswählen!", parent=self.root)
            
        s_a = next((i for i in self.inventory if i['id'] == int(sel[0])), None)
        if not s_a: return

        win = tk.Toplevel(self.root)
        win.title("🔄 Quick-Swap")
        win.geometry("480x220")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        center_window(win, self.root)
        
        ttk.Label(win, text="Spule ins AMS tauschen:", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        ttk.Label(win, text=f"{s_a.get('brand', '')} {s_a.get('color', '')}", font=("Segoe UI", 10)).pack(pady=5)
        
        ams_map = {}
        for a in range(1, self.settings.get("num_ams", 1) + 1):
            am_n = f"AMS {a}"
            for s in range(1, 5):
                s_b = next((i for i in self.inventory if i.get('type') == am_n and str(i.get('loc_id')) == str(s)), None)
                if s_b:
                    label_text = f"{s_b.get('brand', '')} {s_b.get('color', '')}"
                else:
                    label_text = "(LEER)"
                    
                d_t = f"{am_n} | Slot {s}  -->  {label_text}"
                ams_map[d_t] = (am_n, str(s))
                
        combo = ttk.Combobox(win, values=list(ams_map.keys()), state="readonly", font=FONT_MAIN, width=45)
        combo.pack(pady=10)
        combo.current(0)
        
        def do_swap():
            t_am, t_sl = ams_map[combo.get()]
            o_t, o_l = s_a.get('type', 'LAGER'), s_a.get('loc_id', '-')
            s_b = next((i for i in self.inventory if i.get('type') == t_am and str(i.get('loc_id')) == t_sl), None)
            
            s_a['type'] = t_am
            s_a['loc_id'] = t_sl
            
            msg_extra = ""
            if s_b: 
                s_b['type'] = o_t
                s_b['loc_id'] = o_l
                msg_extra = f"\n\nDie alte Spule ({s_b.get('brand', '')}) wurde in {o_t} {o_l} gelegt!"
                
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.tree.selection_set(str(s_a.get('id', '')))
            self.on_select(None)
            win.destroy()
            
            messagebox.showinfo("Quick-Swap Erfolgreich", f"{s_a.get('brand', '')} ist im {t_am} (Slot {t_sl}).{msg_extra}", parent=self.root)
            
        ttk.Button(win, text="🔄 Tauschen", command=do_swap, style="Accent.TButton").pack(pady=15)

    def on_quick_scan(self, event=None):
        scan = self.entry_scan.get().strip()
        if not scan: return
        found_id = None
        if self.settings.get("rfid_mode", False):
            item = next((i for i in self.inventory if i.get('rfid') == scan), None)
            if item: found_id = str(item['id'])
        else:
            match = re.search(r'(?:ID:\s*|FIL_)?(\d+)', scan, re.IGNORECASE)
            if match: found_id = match.group(1)
        
        if found_id and self.tree.exists(found_id):
            self.tree.selection_set(found_id); self.tree.see(found_id); self.on_select(None); self.entry_scan.delete(0, tk.END)
        else:
            messagebox.showerror("Fehler", f"Keine Spule mit {'RFID' if self.settings.get('rfid_mode') else 'ID'} '{scan}' gefunden.")
            self.entry_scan.delete(0, tk.END)
    def scan_qr_webcam(self):
        try:
            import cv2 # type: ignore
            from pyzbar import pyzbar # type: ignore
        except ImportError:
            messagebox.showerror("Fehler", "Für den QR-Scan werden 'opencv-python' und 'pyzbar' benötigt.\nBitte installiere diese via pip:\npip install opencv-python pyzbar")
            return
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): messagebox.showerror("Fehler", "Kamera konnte nicht geöffnet werden."); return
        win_name = "VibeSpool QR-Scanner (ESC zum Schließen)"; found_id = None
        while True:
            ret, frame = cap.read()
            if not ret: break
            for barcode in pyzbar.decode(frame):
                barcode_data = barcode.data.decode("utf-8"); match = re.search(r'(?:ID:\s*|FIL_)?(\d+)', barcode_data, re.IGNORECASE)
                if match: found_id = match.group(1); break
            cv2.imshow(win_name, frame)
            if found_id or cv2.waitKey(1) & 0xFF == 27: break
        cap.release(); cv2.destroyAllWindows()
        if found_id: self.entry_scan.delete(0, tk.END); self.entry_scan.insert(0, found_id); self.on_quick_scan()

    def refresh_all_data(self): 
        self.inventory, self.settings, self.spools = self.data_manager.load_all(DEFAULT_SETTINGS) # type: ignore
        self.apply_theme(); self.update_locations_dropdown(); self.refresh_table()

if __name__ == "__main__":
    try: windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk(); app = FilamentApp(root); root.mainloop()
