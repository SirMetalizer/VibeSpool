import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
import os
import json
import zipfile
import webbrowser 
import urllib.request
import http.server
import socketserver
import socket 
import threading
import pystray      
import re            
import csv
from core.bambu_cloud import BambuCloudAPI
from ctypes import windll
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime, timedelta
import qrcode 

# --- MODULE IMPORT ---
from core.utils import load_json, save_json, get_colors_from_text, create_color_icon, center_window
from core.logic import calculate_net_weight, check_for_updates, parse_shelves_string, serialize_shelves
from core.data_manager import DataManager
from core.spool_presets import SPOOL_PRESETS
from core.colors import get_color_name_from_hex
from core.mobile_server import start_mobile_server, get_local_ip
from core.label_creator import LabelCreatorDialog
from core.print_queue import PrintQueueDialog

# --- KONFIGURATION ---
APP_VERSION = "2.0.2"
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
    "use_moonraker": False,
    "printer_url": "",
    "printer_api_key": "",
    "use_bambu": False,
    "bambu_ip": "",
    "bambu_access": "",
    "bambu_serial": "",
    "mqtt_enable": False,
    "mqtt_host": "",
    "mqtt_port": "1883",
    "mqtt_user": "",
    "mqtt_pass": "",
    "materials": ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF", "PVA", "Sonstiges"],
    "subtypes": ["Standard", "Matte", "Silk", "High Speed", "Dual Color", "Tri Color", "Glow in Dark", "Transparent", "Translucent", "Marmor", "Holz", "Glitzer/Sparkle"],
    "colors": ["Black", "White", "Grey", "Silver", "Ash Gray", "Red", "Maroon Red", "Blue", "Light Blue", "Navy", "Green", "Dark Green", "Mint", "Olive", "Yellow", "Orange", "Terracotta", "Purple", "Plum", "Lavender", "Pink", "Magenta", "Brown", "Beige", "Turquoise", "Cyan", "Gold", "Copper", "Bronze", "Rainbow", "Marble", "Wood"],
    "brands": ["Bambu", "eSun", "Geeetech", "Sunlu", "Polymaker", "Prusa", "Eryone"],
    "visible_columns": ["id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"]
}

MATERIALS = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF", "PVA", "Sonstiges"]
SUBTYPES = ["Standard", "Matte", "Silk", "High Speed", "Dual Color", "Tri Color", "Glow in Dark", "Transparent", "Translucent", "Marmor", "Holz", "Glitzer/Sparkle"]
COMMON_COLORS = [
    "Black", "White", "Grey", "Silver", "Ash Gray", 
    "Red", "Maroon Red", "Blue", "Light Blue", "Navy", 
    "Green", "Dark Green", "Mint", "Olive",
    "Yellow", "Orange", "Terracotta", 
    "Purple", "Plum", "Lavender", "Pink", "Magenta", 
    "Brown", "Beige", "Turquoise", "Cyan",
    "Gold", "Copper", "Bronze", 
    "Rainbow", "Marble", "Wood"
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

def fetch_last_print_usage(url, key): 
    return None
def fetch_recent_jobs(url, key): 
    return []
# --- FENSTER KLASSEN ---
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
    def __init__(self, parent, data_manager, on_save, start_tab=0, app_instance=None):
        super().__init__(parent)
        self.data_manager = data_manager; self.on_save = on_save; self.app = app_instance
        _, self.settings, _ = self.data_manager.load_all(DEFAULT_SETTINGS)
        self.title("VibeSpool Einstellungen"); 
        self.geometry("950x650"); 
        self.transient(parent)
        self.grab_set()
        center_window(self, parent)

        # --- NEU: PanedWindow für die Einstellungen ---
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)

        # Linke Seite: Das Notebook (Tabs)
        self.notebook_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.notebook_frame, weight=1)

        footer_frm = ttk.Frame(self.notebook_frame)
        footer_frm.pack(side="bottom", fill="x", pady=(0, 10), padx=10)
        ttk.Button(footer_frm, text="Abbrechen", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(footer_frm, text="💾 Änderungen Speichern", command=self.do_save, style="Accent.TButton").pack(side="right", padx=5)

        self.nb = ttk.Notebook(self.notebook_frame)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.toggle_side_panel(force_close=True))
        
        # NEU: Wenn der Tab gewechselt wird -> Side-Panel gnadenlos schließen!
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.toggle_side_panel(force_close=True))

        # Rechte Seite: Das Side-Panel (Initial versteckt)
        self.side_panel = ttk.Frame(self.main_paned, width=350, relief="solid", borderwidth=1)
        self.side_panel.pack_propagate(False)
        self.side_panel_open = False
        self.current_side_title = ""
        
        # TAB 1: LAGER
        tab_lager = ttk.Frame(self.nb, padding=15); self.nb.add(tab_lager, text="📦 Lager")
        ttk.Label(tab_lager, text="Regal-Konfiguration", font=FONT_BOLD).pack(anchor="w")
        self.var_shelves = tk.StringVar(value=self.settings.get("shelves", "REGAL|4|8"))
        self.shelf_list = tk.Listbox(tab_lager, height=6, font=("Segoe UI", 9))
        self.shelf_list.pack(fill="x", pady=10)
        self.refresh_settings_shelf_list()
        # NEU: Wenn ein neues Regal angeklickt wird und das Panel rechts offen ist -> Live aktualisieren!
        def on_shelf_list_select(event):
            if self.side_panel_open:
                title = self.current_side_title
                # Kleiner Trick: Wir leeren den Titel kurz, damit toggle_side_panel denkt, es sei ein neuer Aufruf
                self.current_side_title = "" 
                if title == "Regal-Konfigurator":
                    self.toggle_side_panel(title, self.build_shelf_planner_ui)
                elif title == "Fächer individuell benennen":
                    self.toggle_side_panel(title, self.build_shelf_names_ui)
                    
        self.shelf_list.bind("<<ListboxSelect>>", on_shelf_list_select)
        

        btn_frm_lager = ttk.Frame(tab_lager)
        btn_frm_lager.pack(fill="x", pady=(5, 0))
        
        # Löschen Button (Direkt an der Liste)
        def delete_selected_shelf():
            sel = self.shelf_list.curselection()
            if not sel:
                messagebox.showinfo("Info", "Bitte wähle erst ein Regal aus der Liste aus!", parent=self)
                return
            if messagebox.askyesno("Löschen", "Soll dieses Regal wirklich gelöscht werden?", parent=self):
                current_shelves = parse_shelves_string(self.var_shelves.get())
                del current_shelves[sel[0]]
                self.var_shelves.set(serialize_shelves(current_shelves))
                self.refresh_settings_shelf_list()

        ttk.Button(btn_frm_lager, text="🗑️ Löschen", command=delete_selected_shelf).pack(side="left", padx=(0, 5))
        
        ttk.Button(btn_frm_lager, text="➕ Neu / Ändern", 
                   command=lambda: self.toggle_side_panel("Regal-Konfigurator", self.build_shelf_planner_ui)).pack(side="left", fill="x", expand=True, padx=2)
        
        ttk.Button(btn_frm_lager, text="🏷️ Fächer benennen", 
                   command=lambda: self.toggle_side_panel("Fächer individuell benennen", self.build_shelf_names_ui)).pack(side="left", fill="x", expand=True, padx=(2, 0))

        f_names = ttk.Frame(tab_lager); f_names.pack(fill="x", pady=5)
        ttk.Label(f_names, text="Reihen-Name:").grid(row=0, column=0, sticky="w")
        self.ent_row = ttk.Entry(f_names, width=15); self.ent_row.insert(0, self.settings.get("label_row", "Fach")); self.ent_row.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        ttk.Label(f_names, text="Spalten-Name:").grid(row=1, column=0, sticky="w")
        self.ent_col = ttk.Entry(f_names, width=15); self.ent_col.insert(0, self.settings.get("label_col", "Slot")); self.ent_col.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        # --- NEU: Zusatz-Orte sind jetzt hier, wo sie hingehören! ---
        ttk.Separator(tab_lager, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(tab_lager, text="Zusatz-Orte (kommagetrennt, z.B. Trockenbox, Verliehen):", font=FONT_BOLD).pack(anchor="w", pady=(0, 5))
        self.ent_custom = ttk.Entry(tab_lager)
        self.ent_custom.insert(0, self.settings.get("custom_locs", "Filamenttrockner"))
        self.ent_custom.pack(fill="x", pady=2)
        self.var_double = tk.BooleanVar(value=self.settings.get("double_depth", False))
        
        ttk.Separator(tab_lager, orient="horizontal").pack(fill="x", pady=10)
        self.var_logistics = tk.BooleanVar(value=self.settings.get("logistics_order", False))
        ttk.Checkbutton(tab_lager, text="Logistik-Modus (unten = Reihe 1)", variable=self.var_logistics).pack(anchor="w", pady=5)
        ttk.Checkbutton(tab_lager, text="Doppeltiefe Regale (2 Rollen pro Slot)", variable=self.var_double).pack(anchor="w", pady=(10, 5))
        

        # TAB 3: DRUCKER
        tab_prn = ttk.Frame(self.nb, padding=15); self.nb.add(tab_prn, text="🤖 Drucker")
        
        # Moonraker Bereich
        ttk.Label(tab_prn, text="Klipper / Moonraker", font=FONT_BOLD).pack(anchor="w")
        self.var_moonraker = tk.BooleanVar(value=self.settings.get("use_moonraker", False))
        ttk.Checkbutton(tab_prn, text="Moonraker-Sync im Hauptfenster anzeigen", variable=self.var_moonraker).pack(anchor="w", pady=(5, 5))
        self.ent_prn_url = ttk.Entry(tab_prn); self.ent_prn_url.insert(0, self.settings.get("printer_url", "")); self.ent_prn_url.pack(fill="x", pady=2)
        
        ttk.Separator(tab_prn, orient="horizontal").pack(fill="x", pady=15)
        
        # NEU: Bambu Lab Bereich       
        # NEU: AMS Anzahl im Drucker-Tab
        ttk.Label(tab_prn, text="Anzahl AMS Einheiten:", font=FONT_BOLD).pack(anchor="w")
        self.ent_ams = ttk.Entry(tab_prn, width=10); self.ent_ams.insert(0, str(self.settings.get("num_ams", 1))); self.ent_ams.pack(anchor="w", pady=(2, 10))
        
        # NEU: Bambu Lab Bereich
        ttk.Label(tab_prn, text="Bambu Lab AMS (via MQTT)", font=FONT_BOLD).pack(anchor="w")
        self.var_bambu = tk.BooleanVar(value=self.settings.get("use_bambu", False))
        ttk.Checkbutton(tab_prn, text="Bambu AMS Live-Sync aktivieren", variable=self.var_bambu).pack(anchor="w", pady=(5, 5))
        
        ttk.Label(tab_prn, text="Drucker IP-Adresse:").pack(anchor="w", pady=(5,0))
        self.ent_bambu_ip = ttk.Entry(tab_prn); self.ent_bambu_ip.insert(0, self.settings.get("bambu_ip", "")); self.ent_bambu_ip.pack(fill="x", pady=2)
        ttk.Label(tab_prn, text="Access Code (LAN):").pack(anchor="w", pady=(5,0))
        self.ent_bambu_acc = ttk.Entry(tab_prn); self.ent_bambu_acc.insert(0, self.settings.get("bambu_access", "")); self.ent_bambu_acc.pack(fill="x", pady=2)
        ttk.Label(tab_prn, text="Seriennummer:").pack(anchor="w", pady=(5,0))
        self.ent_bambu_ser = ttk.Entry(tab_prn); self.ent_bambu_ser.insert(0, self.settings.get("bambu_serial", "")); self.ent_bambu_ser.pack(fill="x", pady=2)
        # --- NEU: Bambu Cloud API Block ---
        ttk.Separator(tab_prn, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(tab_prn, text="Bambu Lab Cloud API", font=FONT_BOLD).pack(anchor="w")
        
        self.var_cloud = tk.BooleanVar(value=self.settings.get("use_bambu_cloud", True))
        ttk.Checkbutton(tab_prn, text="Cloud-Historie & Smart-Match aktivieren", variable=self.var_cloud).pack(anchor="w", pady=(5, 5))

        # --- NEU: TAB (DRUCKKOSTEN-RECHNER) ---
        tab_fin = ttk.Frame(self.nb, padding=15)
        self.nb.add(tab_fin, text="💰 Druckkosten-Rechner")

        ttk.Label(tab_fin, text="Druckkosten & Gewerbe-Kalkulation", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(tab_fin, text="VibeSpool nutzt diese Werte, um bei jedem Druck die exakten Gesamtkosten (Material + Strom + Verschleiß) zu berechnen.", foreground="gray", wraplength=450).pack(anchor="w", pady=(0, 15))

        frm_calc = ttk.Frame(tab_fin, padding=10)
        frm_calc.pack(fill="x")

        ttk.Label(frm_calc, text="Strompreis pro kWh (€):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_kwh = ttk.Entry(frm_calc, width=15)
        self.ent_kwh.insert(0, str(self.settings.get("kwh_price", "0.30")))
        self.ent_kwh.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(frm_calc, text="Drucker-Stromverbrauch (Watt):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_watts = ttk.Entry(frm_calc, width=15)
        self.ent_watts.insert(0, str(self.settings.get("printer_watts", "150")))
        self.ent_watts.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(frm_calc, text="Richtwerte: Bambu A1 Mini ~80W | A1 ~100W | P1S/X1C ~250W", font=("Segoe UI", 8), foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ttk.Separator(frm_calc, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        # --- NEU: Maschinenverschleiß & Marge ---
        ttk.Label(frm_calc, text="Maschinenverschleiß pro Stunde (€):").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_wear = ttk.Entry(frm_calc, width=15)
        self.ent_wear.insert(0, str(self.settings.get("wear_per_hour", "0.20")))
        self.ent_wear.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(frm_calc, text="Gewinnmarge / Aufschlag (%):").grid(row=5, column=0, sticky="w", pady=5)
        self.ent_margin = ttk.Entry(frm_calc, width=15)
        self.ent_margin.insert(0, str(self.settings.get("profit_margin", "0")))
        self.ent_margin.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # TAB 5: SYSTEM
        tab_sys = ttk.Frame(self.nb, padding=15); self.nb.add(tab_sys, text="⚙ System")
        self.var_affiliate = tk.BooleanVar(value=self.settings.get("use_affiliate", True))
        ttk.Checkbutton(tab_sys, text="Entwickler unterstützen (Affiliate)", variable=self.var_affiliate).pack(anchor="w", pady=2)
        self.var_rfid = tk.BooleanVar(value=self.settings.get("rfid_mode", False))
        ttk.Checkbutton(tab_sys, text="RFID-Reader Modus aktiv", variable=self.var_rfid).pack(anchor="w", pady=2)
        
        ttk.Separator(tab_sys, orient="horizontal").pack(fill="x", pady=10)
        
        # --- NEU: Echten Standard-Pfad ermitteln und anzeigen ---
        import os
        # Wir holen uns den Pfad direkt aus dem DataManager (Fallback: Aktuelles Verzeichnis)
        default_path = getattr(self.data_manager, 'base_dir', os.getcwd())
        custom_path = self.settings.get("custom_db_path", "")
        
        path_show = custom_path if custom_path else f"{default_path} (Standard)"
        
        self.lbl_path = ttk.Label(tab_sys, text=f"Daten-Pfad:\n{path_show}", font=("Segoe UI", 8, "italic"), wraplength=450)
        self.lbl_path.pack(fill="x", pady=5)
        
        p_btn_frm = ttk.Frame(tab_sys); p_btn_frm.pack(fill="x", pady=5)
        
        def change_path():
            d = filedialog.askdirectory(title="Datenbank-Ordner wählen")
            if d: 
                self.settings["custom_db_path"] = d
                self.lbl_path.config(text=f"Daten-Pfad:\n{d}")
                
        def set_standard():
            self.settings["custom_db_path"] = ""
            self.lbl_path.config(text=f"Daten-Pfad:\n{default_path} (Standard)")
            
        ttk.Button(p_btn_frm, text="Ordner ändern", command=change_path).pack(side="left", padx=2)
        ttk.Button(p_btn_frm, text="Standard", command=set_standard).pack(side="left")

        ttk.Separator(tab_sys, orient="horizontal").pack(fill="x", pady=10)
        
        # --- NEU: HOME ASSISTANT / MQTT ---
        ttk.Label(tab_sys, text="🏡 Smart Home / Home Assistant", font=FONT_BOLD).pack(anchor="w")
        self.var_mqtt = tk.BooleanVar(value=self.settings.get("mqtt_enable", False))
        
        frm_mqtt = ttk.Frame(tab_sys, padding=10)
        
        def toggle_mqtt():
            if self.var_mqtt.get(): frm_mqtt.pack(fill="x", pady=5)
            else: frm_mqtt.pack_forget()
            
        ttk.Checkbutton(tab_sys, text="MQTT Broadcasting aktivieren", variable=self.var_mqtt, command=toggle_mqtt).pack(anchor="w", pady=2)
        
        ttk.Label(frm_mqtt, text="Broker IP / Host:").grid(row=0, column=0, sticky="w", pady=2)
        self.ent_mqtt_host = ttk.Entry(frm_mqtt, width=25); self.ent_mqtt_host.insert(0, self.settings.get("mqtt_host", "")); self.ent_mqtt_host.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(frm_mqtt, text="Port:").grid(row=1, column=0, sticky="w", pady=2)
        self.ent_mqtt_port = ttk.Entry(frm_mqtt, width=10); self.ent_mqtt_port.insert(0, self.settings.get("mqtt_port", "1883")); self.ent_mqtt_port.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(frm_mqtt, text="Benutzer:").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_mqtt_user = ttk.Entry(frm_mqtt, width=25); self.ent_mqtt_user.insert(0, self.settings.get("mqtt_user", "")); self.ent_mqtt_user.grid(row=2, column=1, sticky="w", padx=5)
        
        ttk.Label(frm_mqtt, text="Passwort:").grid(row=3, column=0, sticky="w", pady=2)
        self.ent_mqtt_pass = ttk.Entry(frm_mqtt, width=25, show="*"); self.ent_mqtt_pass.insert(0, self.settings.get("mqtt_pass", "")); self.ent_mqtt_pass.grid(row=3, column=1, sticky="w", padx=5)
        
        # Initialer Zustand der Checkbox
        if self.var_mqtt.get(): frm_mqtt.pack(fill="x", pady=5)

        # TAB 5: LISTEN (Materialien & Farben)
        tab_lists = ttk.Frame(self.nb, padding=15); self.nb.add(tab_lists, text="📋 Listen")
        ttk.Label(tab_lists, text="Eigene Dropdown-Listen verwalten", font=FONT_BOLD).pack(anchor="w", pady=(0, 10))
        
        list_container = ttk.Frame(tab_lists)
        list_container.pack(fill="both", expand=True)

        # Helper-Funktion baut uns Listen-Manager (mit Spezial-Feature für Farben)
        self.list_vars = {}
        def create_list_manager(parent, title, key, default_list):
            frm = ttk.LabelFrame(parent, text=title, padding=5)
            frm.pack(side="left", fill="both", expand=True, padx=2)
            
            lb = tk.Listbox(frm, height=12, font=("Segoe UI", 9), selectmode=tk.SINGLE, cursor="hand2")
            lb.pack(fill="both", expand=True, pady=2)
            
            # --- NEU: Pylance-Safe Drag & Drop Logik ---
            drag_state = {"idx": None}

            def on_b1_press(event):
                lb.selection_clear(0, tk.END)
                idx = lb.nearest(event.y)
                lb.selection_set(idx)
                drag_state["idx"] = idx

            def on_b1_motion(event):
                start_idx = drag_state["idx"]
                if start_idx is None: return
                
                new_idx = lb.nearest(event.y)
                if new_idx != start_idx:
                    item_text = lb.get(start_idx)
                    lb.delete(start_idx)
                    lb.insert(new_idx, item_text)
                    lb.selection_clear(0, tk.END)
                    lb.selection_set(new_idx)
                    drag_state["idx"] = new_idx

            def on_b1_release(event):
                drag_state["idx"] = None
                self.list_vars[key] = list(lb.get(0, tk.END))

            lb.bind("<ButtonPress-1>", on_b1_press)
            lb.bind("<B1-Motion>", on_b1_motion)
            lb.bind("<ButtonRelease-1>", on_b1_release)
            # -----------------------------------
            
            # Aktuelle Daten laden
            current_data = self.settings.get(key, default_list)
            self.list_vars[key] = current_data.copy()
            for item in self.list_vars[key]: lb.insert(tk.END, item)
            
            # Eingabebereich aufteilen
            input_frm = ttk.Frame(frm)
            input_frm.pack(fill="x", pady=2)
            
            ent_new = ttk.Entry(input_frm)
            ent_new.pack(side="left", fill="x", expand=True)
            
            # NEU: Color-Picker NUR für die Farben-Liste einblenden!
            if key == "colors":
                def pick_list_color():
                    color_code = colorchooser.askcolor(title="Farbe für Liste wählen", parent=self)[1]
                    if color_code:
                        # Alten Hex-Code (falls vorhanden) rausfiltern und neuen sauber anhängen
                        current_text = re.sub(r'\s*\(?#[0-9a-fA-F]{6}\)?', '', ent_new.get().strip()).strip()
                        ent_new.delete(0, tk.END)
                        ent_new.insert(0, f"{current_text} ({color_code.upper()})" if current_text else color_code.upper())
                        
                ttk.Button(input_frm, text="🎨", width=3, command=pick_list_color).pack(side="left", padx=(2, 0))
            
            btn_frm = ttk.Frame(frm)
            btn_frm.pack(fill="x")
            
            def add_item():
                val = ent_new.get().strip()
                if val and val not in self.list_vars[key]:
                    self.list_vars[key].append(val)
                    lb.insert(tk.END, val)
                    ent_new.delete(0, tk.END)
            
            def del_item():
                sel = lb.curselection()
                if sel:
                    idx = sel[0]
                    del self.list_vars[key][idx]
                    lb.delete(idx)
                    
            # Buttons etwas breiter und beschriftet, damit man sie besser trifft
            ttk.Button(btn_frm, text="➕ Hinzufügen", command=add_item).pack(side="left", expand=True, fill="x", padx=(0, 1))
            ttk.Button(btn_frm, text="❌ Löschen", command=del_item).pack(side="left", expand=True, fill="x", padx=(1, 0))

        create_list_manager(list_container, "Materialien", "materials", DEFAULT_SETTINGS["materials"])
        create_list_manager(list_container, "Farben", "colors", DEFAULT_SETTINGS["colors"])
        create_list_manager(list_container, "Effekt / Typ", "subtypes", DEFAULT_SETTINGS["subtypes"])
        create_list_manager(list_container, "Hersteller", "brands", DEFAULT_SETTINGS["brands"])
        self.nb.select(start_tab)

    def toggle_side_panel(self, title=None, build_func=None, force_close=False):
        # Wenn wir schon offen sind und den GLEICHEN Titel klicken -> Schließen
        if force_close or (self.side_panel_open and self.current_side_title == title):
            try: self.main_paned.forget(self.side_panel)
            except: pass
            self.side_panel_open = False
            self.current_side_title = ""
            return

        # Ansonsten: Panel leeren und neu aufbauen
        for widget in self.side_panel.winfo_children():
            widget.destroy()

        # Sicherstellen, dass es im PanedWindow ist (verhindert den "already added" Crash)
        try:
            self.main_paned.add(self.side_panel, weight=0)
        except tk.TclError:
            pass
        self.side_panel_open = True
        self.current_side_title = title

        # Header
        header = ttk.Frame(self.side_panel)
        header.pack(fill="x", pady=10, padx=10)
        ttk.Label(header, text=title or "", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(header, text="❌", width=3, command=lambda: self.toggle_side_panel(force_close=True)).pack(side="right")
        ttk.Separator(self.side_panel, orient="horizontal").pack(fill="x")

        content = ttk.Frame(self.side_panel, padding=10)
        content.pack(fill="both", expand=True)
        
        if build_func:
            build_func(content)

    def build_shelf_planner_ui(self, parent):
        sel = self.shelf_list.curselection()
        current_shelves = parse_shelves_string(self.var_shelves.get())
        edit_idx = sel[0] if sel else None
        
        existing_data = current_shelves[edit_idx] if edit_idx is not None else {"name": "NEU", "rows": 4, "cols": 8}

        ttk.Label(parent, text="Regal hinzufügen oder bearbeiten:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        
        ttk.Label(parent, text="Name:").pack(anchor="w")
        ent_name = ttk.Entry(parent)
        ent_name.insert(0, existing_data["name"])
        ent_name.pack(fill="x", pady=(0, 10))

        ttk.Label(parent, text="Reihen (Y):").pack(anchor="w")
        ent_rows = ttk.Spinbox(parent, from_=1, to=50)
        ent_rows.set(existing_data["rows"])
        ent_rows.pack(fill="x", pady=(0, 10))

        ttk.Label(parent, text="Spalten (X):").pack(anchor="w")
        ent_cols = ttk.Spinbox(parent, from_=1, to=50)
        ent_cols.set(existing_data["cols"])
        ent_cols.pack(fill="x", pady=(0, 15))

        def save_shelf():
            new_shelf = {"name": ent_name.get().strip() or "Regal", "rows": int(ent_rows.get()), "cols": int(ent_cols.get())}
            
            if edit_idx is not None:
                current_shelves[edit_idx] = new_shelf
            else:
                current_shelves.append(new_shelf)
                
            new_val = serialize_shelves(current_shelves)
            self.var_shelves.set(new_val)
            self.settings["shelves"] = new_val
            
            # WICHTIG: App Settings live injizieren!
            app = getattr(self, 'app', None)
            if app is not None:
                app.settings["shelves"] = new_val
                app.update_locations_dropdown()
                app.update_slot_dropdown()
                
            self.refresh_settings_shelf_list()
            messagebox.showinfo("Erfolg", "Regal gespeichert!", parent=self)
            self.toggle_side_panel(force_close=True)

        ttk.Button(parent, text="💾 Speichern / Übernehmen", style="Accent.TButton", command=save_shelf).pack(fill="x")

    def build_shelf_names_ui(self, parent):
        sel = self.shelf_list.curselection()
        if not sel:
            ttk.Label(parent, text="⚠️ Bitte wähle erst links ein Regal aus!", foreground="red", wraplength=250).pack(pady=20)
            return
            
        current_shelves = parse_shelves_string(self.var_shelves.get())
        target_shelf = current_shelves[sel[0]]
        target_name = target_shelf["name"]
        
        ttk.Label(parent, text=f"Fächer & Slots für '{target_name}':", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        from core.utils import ScrollableFrame
        sf = ScrollableFrame(parent)
        sf.pack(fill="both", expand=True, pady=10)
        
        all_custom_names = self.settings.get("shelf_names_v2", {})
        my_names = all_custom_names.get(target_name, {})
        
        app = getattr(self, 'app', None)
        
        ui_lbl_r = self.ent_row.get().strip() or "Fach"
        ui_lbl_c = self.ent_col.get().strip() or "Slot"
        
        db_lbl_r = app.settings.get('label_row', 'Fach') if app else "Fach"
        db_lbl_c = app.settings.get('label_col', 'Slot') if app else "Slot"

        # --- Reihen (Rows) ---
        ttk.Label(sf.inner, text=f"--- {ui_lbl_r} (Reihen) ---", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 5))
        entries_r = {}
        for r in range(1, int(target_shelf["rows"]) + 1):
            row_frm = ttk.Frame(sf.inner)
            row_frm.pack(fill="x", pady=2)
            ttk.Label(row_frm, text=f"{ui_lbl_r} {r}:", width=10).pack(side="left")
            ent = ttk.Entry(row_frm)
            ent.insert(0, my_names.get(str(r), f"{ui_lbl_r} {r}"))
            ent.pack(side="left", fill="x", expand=True)
            entries_r[str(r)] = ent

        # --- Spalten (Cols) ---
        ttk.Label(sf.inner, text=f"--- {ui_lbl_c} (Spalten) ---", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        entries_c = {}
        for c in range(1, int(target_shelf["cols"]) + 1):
            row_frm = ttk.Frame(sf.inner)
            row_frm.pack(fill="x", pady=2)
            ttk.Label(row_frm, text=f"{ui_lbl_c} {c}:", width=10).pack(side="left")
            ent = ttk.Entry(row_frm)
            # Spalten speichern wir unter 'col_1', 'col_2' ab, um sie von Reihen zu trennen!
            ent.insert(0, my_names.get(f"col_{c}", f"{ui_lbl_c} {c}"))
            ent.pack(side="left", fill="x", expand=True)
            entries_c[str(c)] = ent

        def save():
            new_map = {}
            for k, v in entries_r.items(): new_map[str(k)] = v.get().strip()
            for k, v in entries_c.items(): new_map[f"col_{k}"] = v.get().strip()
            
            changes_made = 0
            
            if app is not None:
                # Da sich Reihe UND Spalte geändert haben können, prüfen wir alle Kreuzungen
                for r in range(1, int(target_shelf["rows"]) + 1):
                    for c in range(1, int(target_shelf["cols"]) + 1):
                        old_r_val = my_names.get(str(r), f"{db_lbl_r} {r}")
                        new_r_val = new_map.get(str(r), f"{ui_lbl_r} {r}")
                        
                        old_c_val = my_names.get(f"col_{c}", f"{db_lbl_c} {c}")
                        new_c_val = new_map.get(f"col_{c}", f"{ui_lbl_c} {c}")
                        
                        # Prüfen, ob sich bei dieser Slot-Kombination etwas geändert hat
                        if old_r_val != new_r_val or old_c_val != new_c_val:
                            search_str = f"{old_r_val} - {old_c_val}"
                            replace_str = f"{new_r_val} - {new_c_val}"
                            
                            for item in app.inventory:
                                if item.get("type") == target_name:
                                    loc = str(item.get("loc_id", ""))
                                    # Berücksichtigt auch "(V)" oder "(H)" bei Doppeltiefe
                                    if loc == search_str or loc.startswith(f"{search_str} "):
                                        item["loc_id"] = loc.replace(search_str, replace_str, 1)
                                        changes_made += 1

            all_custom_names[target_name] = new_map
            self.settings["shelf_names_v2"] = all_custom_names
            self.data_manager.save_settings(self.settings)
            
            if app is not None:
                app.settings["shelf_names_v2"] = all_custom_names
                if changes_made > 0:
                    app.data_manager.save_inventory(app.inventory)
                    app.refresh_table()
                if hasattr(app, 'update_slot_dropdown'):
                    app.update_slot_dropdown()
                
            messagebox.showinfo("Erfolg", f"Raster-Namen für '{target_name}' gespeichert!\n\n{changes_made} Spulen wurden automatisch umgebucht.", parent=self)
            self.toggle_side_panel(force_close=True)

        ttk.Button(parent, text="💾 Namen übernehmen & Speichern", style="Accent.TButton", command=save).pack(fill="x")

    def refresh_settings_shelf_list(self):
        self.shelf_list.delete(0, tk.END)
        for s in parse_shelves_string(self.var_shelves.get()): self.shelf_list.insert(tk.END, f"📦 {s['name']} ({s['rows']}x{s['cols']})")

    def do_save(self):
        
        try:
            old_label_row = self.settings.get("label_row", "Fach")
            old_label_col = self.settings.get("label_col", "Slot")
            
            new_label_row = self.ent_row.get().strip() or "Fach"
            new_label_col = self.ent_col.get().strip() or "Slot"
            
            app_inst = getattr(self, 'app', None)
            
            if app_inst:
                inventory_changed = False
                
                # --- MIGRATION 0: Doppeltiefe Umschaltung (Vorne/Hinten anpassen) ---
                old_double = self.settings.get("double_depth", False)
                new_double = self.var_double.get()
                
                if old_double != new_double:
                    for item in app_inst.inventory:
                        t = str(item.get("type", ""))
                        loc = str(item.get("loc_id", ""))
                        # Nur Regal-Einträge anpassen (kein AMS, kein Lager)
                        if t and t not in ["LAGER", "VERBRAUCHT"] and not t.startswith("AMS") and loc and loc != "-":
                            if new_double: # Von Einzel auf Doppel
                                if not loc.endswith("(V)") and not loc.endswith("(H)"):
                                    item["loc_id"] = f"{loc} (V)"
                                    inventory_changed = True
                            else: # Von Doppel zurück auf Einzel
                                if loc.endswith(" (V)") or loc.endswith(" (H)"):
                                    item["loc_id"] = loc[:-4] # Schneidet " (V)" ab
                                    inventory_changed = True
                
                # --- MIGRATION 1: Gelöschte Regale retten ---
                old_shelves_str = self.settings.get("shelves", "REGAL|4|8")
                from core.logic import parse_shelves_string
                old_shelf_names = [s['name'] for s in parse_shelves_string(old_shelves_str)]
                new_shelf_names = [s['name'] for s in parse_shelves_string(self.var_shelves.get())]
                
                # Welche Regale gab es vorher, aber jetzt nicht mehr?
                deleted_shelves = [name for name in old_shelf_names if name not in new_shelf_names]
                moved_to_lager = 0
                
                if deleted_shelves:
                    for item in app_inst.inventory:
                        # Wenn die Spule in einem der gelöschten Regale lag -> Ab ins LAGER!
                        if item.get("type") in deleted_shelves:
                            item["type"] = "LAGER"
                            item["loc_id"] = "-"
                            moved_to_lager += 1
                            inventory_changed = True
                            
                    if moved_to_lager > 0:
                        messagebox.showinfo("Regal abgebaut", f"Info: Es wurden {moved_to_lager} Spulen aus den gelöschten Regalen sicher ins 'LAGER' verschoben.", parent=self)

                # --- MIGRATION 2: Wording (Fach/Slot) anpassen ---
                if new_label_row != old_label_row or new_label_col != old_label_col:
                    for item in app_inst.inventory:
                        loc = item.get("loc_id", "")
                        if loc and " - " in loc:
                            parts = loc.split(" - ")
                            if len(parts) == 2:
                                r_part, c_part = parts[0], parts[1]
                                
                                if c_part.startswith(old_label_col + " "):
                                    c_part = c_part.replace(old_label_col + " ", new_label_col + " ", 1)
                                    
                                if r_part.startswith(old_label_row + " "):
                                    r_part = r_part.replace(old_label_row + " ", new_label_row + " ", 1)
                                    
                                new_loc = f"{r_part} - {c_part}"
                                if new_loc != loc:
                                    item["loc_id"] = new_loc
                                    inventory_changed = True
                                    
                    # Auch im neuen V2-Benennungssystem die Namen patchen
                    all_shelf_names = self.settings.get("shelf_names_v2", {})
                    for shelf_key, names_dict in all_shelf_names.items():
                        for k, v in names_dict.items():
                            if str(k).startswith("col_"):
                                if v.startswith(old_label_col + " "):
                                    all_shelf_names[shelf_key][k] = v.replace(old_label_col + " ", new_label_col + " ", 1)
                            else:
                                if v.startswith(old_label_row + " "):
                                    all_shelf_names[shelf_key][k] = v.replace(old_label_row + " ", new_label_row + " ", 1)
                    self.settings["shelf_names_v2"] = all_shelf_names

                # Nur speichern, wenn auch wirklich Spulen angefasst wurden
                if inventory_changed:
                    app_inst.data_manager.save_inventory(app_inst.inventory)

            
            # --- NEU: Finanzen auslesen ---
            try: kwh_val = float(self.ent_kwh.get().replace(',', '.'))
            except: kwh_val = 0.30
            try: watts_val = int(self.ent_watts.get())
            except: watts_val = 150
            try: wear_val = float(self.ent_wear.get().replace(',', '.'))
            except: wear_val = 0.0
            try: margin_val = int(self.ent_margin.get())
            except: margin_val = 0

            # --- Normales Speichern der Einstellungen ---
            self.settings.update({
                "kwh_price": kwh_val,         
                "printer_watts": watts_val,   
                "wear_per_hour": wear_val,    # NEU
                "profit_margin": margin_val,  # NEU
                "double_depth": self.var_double.get(),
                "shelves": self.var_shelves.get(),
                "logistics_order": self.var_logistics.get(),
                "label_row": new_label_row,
                "label_col": new_label_col,
                "num_ams": int(self.ent_ams.get()),
                "custom_locs": self.ent_custom.get().strip(),
                "use_affiliate": self.var_affiliate.get(),
                "rfid_mode": self.var_rfid.get(),
                "use_moonraker": self.var_moonraker.get(),
                "printer_url": self.ent_prn_url.get().strip(),
                "printer_api_key": self.settings.get("printer_api_key", ""), 
                "use_bambu": self.var_bambu.get(),
                "use_bambu_cloud": self.var_cloud.get(),
                "bambu_ip": self.ent_bambu_ip.get().strip(),
                "bambu_access": self.ent_bambu_acc.get().strip(),
                "bambu_serial": self.ent_bambu_ser.get().strip(),
                "mqtt_enable": self.var_mqtt.get(),
                "mqtt_host": self.ent_mqtt_host.get().strip(),
                "mqtt_port": self.ent_mqtt_port.get().strip(),
                "mqtt_user": self.ent_mqtt_user.get().strip(),
                "mqtt_pass": self.ent_mqtt_pass.get().strip(),
                "materials": self.list_vars["materials"],
                "colors": self.list_vars["colors"],
                "subtypes": self.list_vars["subtypes"],
                "brands": self.list_vars["brands"]
            })
            
            self.on_save(self.settings)
            
            # --- NEU: LIVE-UPDATE DER OBERFLÄCHE ---
            if app_inst:
                app_inst.refresh_table() 
                
                # Dropdowns live updaten (damit neue Namen / Tiefe sofort wählbar sind)
                if hasattr(app_inst, 'update_slot_dropdown'):
                    app_inst.update_slot_dropdown()
                
                # Lageransicht sofort neu zeichnen, falls sie offen ist
                if hasattr(app_inst, 'shelf_visualizer') and app_inst.shelf_visualizer:
                    app_inst.shelf_visualizer.redraw()
                
                # NEU: Cloud Button live zeigen/verstecken
                if self.settings.get("use_bambu_cloud", True):
                    app_inst.btn_cloud.pack(fill="x")
                else:
                    app_inst.btn_cloud.pack_forget()
                
            self.destroy()
            
        except ValueError: 
            messagebox.showerror("Fehler", "AMS Anzahl muss eine Zahl sein.", parent=self)
        except Exception as e:
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{e}", parent=self)

class ShelfVisualizer(tk.Toplevel):
    # NEU: app_instance wird übergeben, damit wir live speichern können!
    def __init__(self, parent, inventory, settings, spools, app_instance=None):
        super().__init__(parent)
        self.inventory = inventory
        self.settings = settings
        self.spools = spools
        self.app = app_instance
        self.title("Regal & AMS Übersicht")
        self.geometry("1200x850")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        
        # --- Drag & Drop Variablen ---
        self.drag_source = None
        self.drag_window = None

        self.canvas = tk.Canvas(self, bg=parent.cget('bg'), highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.frame = ttk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        
        # NEU: Ausgelagerte Zeichen-Funktion, damit wir nach einem Drop einfach neu laden können
        self.redraw()

        def _on_mousewheel(event):
                # Scrollt sanft hoch und runter
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.frame.bind("<MouseWheel>", _on_mousewheel)

    def redraw(self):
        # Alles alte löschen
        for widget in self.frame.winfo_children():
            widget.destroy()
            
        self.image_cache = []
        # NEU: Ein sauberes Lexikon, in dem wir die Daten zu jedem Widget speichern
        self.widget_data = {} 
        
        from core.logic import parse_shelves_string
        self.parsed_shelves = parse_shelves_string(self.settings.get("shelves", "REGAL|4|8"))
        
        self.shelf_data = {}
        self.ams_data = {}
        # FIX: Das LAGER muss immer existieren, damit wir immer eine Drop-Zone haben!
        self.other_data = {"LAGER": []}
        
        for item in self.inventory:
            try:
                t = str(item.get('type', ''))
                loc = str(item.get('loc_id', ''))
                if t in [s['name'] for s in self.parsed_shelves]: self.shelf_data[f"{t}_{loc}"] = item
                elif t.startswith("AMS"): self.ams_data[f"{t}_{loc}"] = item
                elif t and t != "VERBRAUCHT":
                    if t not in self.other_data: self.other_data[t] = []
                    self.other_data[t].append(item)
            except: pass
            
        pad = ttk.Frame(self.frame, padding=20)
        pad.pack(fill="both", expand=True)
        
        lbl_r = self.settings.get("label_row", "Fach")
        lbl_c = self.settings.get("label_col", "Slot")
        logistics = self.settings.get("logistics_order", False)
        all_shelf_names = self.settings.get("shelf_names_v2", {})
        
        for shelf in self.parsed_shelves:
            ttk.Label(pad, text=f"📦 {shelf['name']}", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 10))
            shelf_names = all_shelf_names.get(shelf['name'], {})
            for r in (range(shelf['rows'], 0, -1) if logistics else range(1, shelf['rows'] + 1)):
                row_label = shelf_names.get(str(r), f"{lbl_r} {r}")
                ttk.Label(pad, text=row_label, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
                row_frame = tk.Frame(pad, bg="#8B4513", padx=5, pady=2)
                row_frame.pack(anchor="w", pady=2)
                is_double = self.settings.get("double_depth", False)
                for c in range(1, shelf['cols'] + 1):
                    # NEU: Spalten-Name auslesen
                    col_label = shelf_names.get(f"col_{c}", f"{lbl_c} {c}")
                    
                    # Für das kleine Icon schneiden wir "Slot " vorne ab, damit es Platz hat
                    short_label = col_label.replace(f"{lbl_c} ", "") if col_label.startswith(f"{lbl_c} ") else col_label
                    
                    if is_double:
                        slot_container = tk.Frame(row_frame, bg="#8B4513")
                        slot_container.pack(side="left", padx=2)
                        
                        frm_h = tk.Frame(slot_container, bg="#8B4513")
                        frm_h.pack(side="top", pady=(0, 1))
                        frm_v = tk.Frame(slot_container, bg="#8B4513")
                        frm_v.pack(side="top", pady=(1, 0))
                        
                        slot_name_h = f"{row_label} - {col_label} (H)"
                        self.draw_slot(frm_h, f"{short_label} (H)", self.shelf_data.get(f"{shelf['name']}_{slot_name_h}"), False, 65, 35, shelf['name'], slot_name_h)
                        
                        slot_name_v = f"{row_label} - {col_label} (V)"
                        self.draw_slot(frm_v, f"{short_label} (V)", self.shelf_data.get(f"{shelf['name']}_{slot_name_v}"), False, 65, 35, shelf['name'], slot_name_v)
                    else:
                        slot_name = f"{row_label} - {col_label}"
                        self.draw_slot(row_frame, short_label, self.shelf_data.get(f"{shelf['name']}_{slot_name}"), False, 70, 70, shelf['name'], slot_name)
                    
        ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20)
        for a in range(1, self.settings.get("num_ams", 1) + 1):
            ams_name = f"AMS {a}"
            ttk.Label(pad, text=ams_name, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 5))
            ams_frame = tk.Frame(pad, bg="#444444", padx=10, pady=10)
            ams_frame.pack(anchor="w")
            for i in range(1, 5): 
                cont = tk.Frame(ams_frame, bg="#444444")
                cont.pack(side="left", fill="y", padx=10)
                ttk.Label(cont, text=f"Slot {i}", foreground="white", background="#444444").pack(pady=(0, 5))
                self.draw_slot(cont, str(i), self.ams_data.get(f"{ams_name}_{i}"), True, 120, 100, ams_name, str(i))
                
        if self.other_data:
            ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20)
            ttk.Label(pad, text="📦 Weitere Lagerorte (Drag & Drop ins Regal & Lager möglich!)", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 5))
            for loc_name, items in self.other_data.items():
                
                # Leere Orte ausblenden, AUSSER es ist das Haupt-LAGER
                if not items and loc_name != "LAGER": 
                    continue
                    
                ttk.Label(pad, text=loc_name, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
                loc_frame = tk.Frame(pad, bg="#333333", padx=5, pady=5)
                loc_frame.pack(anchor="w", pady=2)
                col_count, row_frame = 0, tk.Frame(loc_frame, bg="#333333")
                row_frame.pack(anchor="w")
                
                # 1. Alle existierenden Spulen zeichnen
                for item in items:
                    if col_count >= 10: 
                        col_count = 0
                        row_frame = tk.Frame(loc_frame, bg="#333333")
                        row_frame.pack(anchor="w", pady=(5,0))
                        
                    item_loc_id = item.get("loc_id", "") or "-"
                    self.draw_slot(row_frame, item_loc_id, item, False, 80, 70, loc_name, item_loc_id)
                    col_count += 1
                    
                # --- NEU: Der Ablage-Magnet! ---
                # Wir prüfen, ob die Reihe schon voll ist, dann machen wir einen Umbruch
                if col_count >= 10:
                    row_frame = tk.Frame(loc_frame, bg="#333333")
                    row_frame.pack(anchor="w", pady=(5,0))
                
                # Wir zeichnen ein leeres Feld, das als Drop-Ziel für diesen Ort dient
                self.draw_slot(row_frame, "➕\nAblegen", None, False, 80, 70, loc_name, "-")

    def draw_slot(self, parent, label, item, is_ams, w=90, h=80, loc_type=None, loc_id=None):
        bg_colors, fg_col, txt, tooltip = ["#D2B48C"] if not is_ams else ["#666666"], "#555" if not is_ams else "#CCC", f"{label}\nLEER", "Leer"
        if item:
            cols = get_colors_from_text(item.get('color', ''))
            bg_colors = cols or ["#FFFFFF"]
            if bg_colors[0].startswith("#"):
                r, g, b = int(bg_colors[0][1:3], 16), int(bg_colors[0][3:5], 16), int(bg_colors[0][5:7], 16)
                fg_col = "white" if (r*0.299 + g*0.587 + b*0.114) < 128 else "black"
            else: fg_col = "black"
            sub = item.get('subtype', '')
            mat = item.get('material', '')
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools, item.get('empty_weight'))
            abk = {"Standard": "Std.", "High Speed": "HS", "Dual Color": "Dual", "Tri Color": "Tri", "Glow in Dark": "Glow", "Transparent": "Transp.", "Translucent": "Transl.", "Glitzer/Sparkle": "Glitz."}
            sub_short = abk.get(sub, sub[:7])
            mat_short = mat[:5] 
            txt = f"{label}\n{item['brand'][:10]}\n{mat_short} {sub_short}\n{net}g"
            tooltip = f"ID: {item['id']}\n{item['brand']} - {item.get('color', '')}\n{item.get('material', '')} | Rest: {net}g"
            
        img = create_color_icon(bg_colors, (w, h), "black")
        self.image_cache.append(img)
        lbl = tk.Label(parent, image=img, text=txt, compound="center", fg=fg_col, font=("Segoe UI", 8, "bold"), borderwidth=1, relief="flat")
        lbl.pack(side="left", padx=2, fill="y")
        
        # --- DRAG & DROP BINDINGS (Pylance-Safe) ---
        if loc_type and loc_id:
            # Wir speichern die Daten im Dictionary, der Schlüssel ist die ID des Widgets
            self.widget_data[id(lbl)] = {
                "loc_type": loc_type,
                "loc_id": loc_id,
                "item": item,
                "img": img
            }
            lbl.config(cursor="hand2")
            
            lbl.bind("<ButtonPress-1>", self.on_drag_start)
            lbl.bind("<B1-Motion>", self.on_drag_motion)
            lbl.bind("<ButtonRelease-1>", self.on_drag_release)
            
        lbl.bind("<Enter>", lambda e: self.show_tip(e, tooltip), add="+")
        lbl.bind("<Leave>", self.hide_tip, add="+")

    def on_drag_start(self, event):
        widget = event.widget
        data = self.widget_data.get(id(widget))
        if not data or not data["item"]: return
        
        self.drag_source = widget
        
        self.drag_window = tk.Toplevel(self)
        self.drag_window.wm_overrideredirect(True)
        self.drag_window.attributes('-alpha', 0.8)
        tk.Label(self.drag_window, image=data["img"], borderwidth=2, relief="solid", bg=COLOR_ACCENT).pack()
        self.drag_window.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

    def on_drag_motion(self, event):
        # Wir speichern das Fenster in einer lokalen Variable, damit Pylance es versteht
        drag_win = getattr(self, 'drag_window', None)
        if drag_win:
            drag_win.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

    def on_drag_release(self, event):
        # Auch hier: Lokale Variable für Pylance
        drag_win = getattr(self, 'drag_window', None)
        if drag_win:
            drag_win.destroy()
            self.drag_window = None
            
        if not getattr(self, 'drag_source', None): return
        
        target_widget = self.winfo_containing(event.x_root, event.y_root)
        if target_widget and id(target_widget) in self.widget_data:
            
            source_data = self.widget_data[id(self.drag_source)]
            target_data = self.widget_data[id(target_widget)]
            
            s_type = source_data["loc_type"]
            s_id = source_data["loc_id"]
            
            t_type = target_data["loc_type"]
            t_id = target_data["loc_id"]
            
            if s_type == t_type and s_id == t_id:
                self.drag_source = None
                return
                
            source_item = source_data["item"]
            target_item = target_data["item"]
            
            source_item['type'] = t_type
            source_item['loc_id'] = t_id
            if target_item:
                target_item['type'] = s_type
                target_item['loc_id'] = s_id
                
            app_inst = getattr(self, 'app', None)
            if app_inst:
                app_inst.data_manager.save_inventory(app_inst.inventory)
                app_inst.refresh_table()
                
            self.redraw()
            
        self.drag_source = None

    def show_tip(self, event, text): 
        if getattr(self, 'drag_window', None): return # Versteckt Tooltips beim Draggen
        self.tip = tk.Toplevel(self)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
        tk.Label(self.tip, text=text, bg="#FFFFE0", relief="solid", borderwidth=1, padx=5, pady=2).pack()
        
    def hide_tip(self, event):
        if hasattr(self, 'tip'): self.tip.destroy()

class ShoppingListDialog(tk.Toplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.inventory = inventory
        self.title("Einkaufsliste / Dashboard")
        self.geometry("800x600")
        self.configure(bg=parent.cget('bg'))
        from core.utils import center_window
        center_window(self, parent)
        
        ttk.Label(self, text="🛒 Nachzubestellende & Verbrauchte Filamente", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        # FIX: Buttons zuerst unten anheften!
        btn_frm = ttk.Frame(self)
        btn_frm.pack(fill="x", side="bottom", pady=15, padx=20)
        
        ttk.Button(btn_frm, text="🔗 Im Shop öffnen", command=self.open_shop_link, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frm, text="Als CSV exportieren", command=self.export_csv).pack(side="left", padx=5)
        ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="right", padx=5)

        frm_list = ttk.Frame(self)
        frm_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.tree = ttk.Treeview(frm_list, columns=("brand", "color", "mat", "supplier", "sku", "price", "status"), show="headings")
        self.tree.heading("brand", text="Marke"); self.tree.heading("color", text="Farbe"); self.tree.heading("mat", text="Mat."); self.tree.heading("supplier", text="Lieferant"); self.tree.heading("sku", text="SKU"); self.tree.heading("price", text="Preis"); self.tree.heading("status", text="Status")
        self.tree.column("mat", width=50); self.tree.column("price", width=60); self.tree.column("status", width=100)
        
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self.open_shop_link())
        
        self.populate()
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
        item = next((x for x in self.inventory if x['id'] == str(sel[0])), None)
        if not item or not item.get('link'): return messagebox.showinfo("Info", "Für dieses Filament ist leider kein Link hinterlegt.", parent=self)
        
        url = item['link'].strip()
        url = url if url.startswith("http") else "https://" + url
        
        # --- AFFILIATE INJEKTION ---
        if self.app.settings.get("use_affiliate", True):
            url_lower = url.lower()
            
            # Bambu Lab MakerWorld
            if "bambulab.com" in url_lower and "modelid=" not in url_lower: 
                url += ("&" if "?" in url else "?") + "modelId=1889832"
                
            # Amazon (Alle Domains & Kurzlinks)
            elif ("amazon." in url_lower or "amzn.to" in url_lower) and "tag=" not in url_lower:
                url += ("&" if "?" in url else "?") + "tag=metmeyoumetwe-21"
                
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
        self.app = app_instance
        self.inventory = inventory
        self.title("📊 Analytics & Finanz-Dashboard")
        self.geometry("1250x850") 
        self.configure(bg=parent.cget('bg'))
        from core.utils import center_window
        center_window(self, parent)
        
        self.build_ui()

    def build_ui(self):
        # Alle alten Elemente löschen, falls das UI neu geladen wird
        for widget in self.winfo_children():
            widget.destroy()

        # --- NEU: Master Layout ---
        self.master_frame = ttk.Frame(self)
        self.master_frame.pack(fill="both", expand=True)
        
        self.side_panel = ttk.Frame(self.master_frame, width=350, relief="solid", borderwidth=1)
        self.side_panel.pack_propagate(False)
        
        self.main_content = ttk.Frame(self.master_frame)
        self.main_content.pack(side="left", fill="both", expand=True)

        # --- 1. DATEN BERECHNEN (KPIs) ---
        total_value, total_weight, total_spools, mat_stats = 0.0, 0, 0, {}
        for item in self.inventory:
            if item.get('type') == 'VERBRAUCHT': continue
            total_spools += 1
            from core.logic import calculate_net_weight
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.app.spools, item.get('empty_weight'))
            total_weight += net
            val = 0.0
            try:
                price, cap = float(str(item.get('price', '0')).replace(',', '.')), float(str(item.get('capacity', '1000')))
                if cap > 0: val = (net / cap) * price
            except: pass
            total_value += val
            mat = item.get('material', 'Unbekannt') or 'Unbekannt'
            if mat not in mat_stats: mat_stats[mat] = {'count': 0, 'weight': 0, 'value': 0.0}
            mat_stats[mat]['count'] += 1
            mat_stats[mat]['weight'] += net
            mat_stats[mat]['value'] += val

        # --- 2. OBERER BEREICH (Dashboard) ---
        ttk.Label(self.main_content, text="💰 Bestands-Statistik & Finanzen", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))
        
        main_frm = ttk.Frame(self.main_content)
        main_frm.pack(fill="x", padx=20, pady=5)
        
        left_panel = ttk.Frame(main_frm)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_panel = ttk.Frame(main_frm)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # --- 3. LINKE SEITE (KPIs & Tabelle) ---
        kpi_frame = tk.Frame(left_panel, bg="#1e1e1e" if "dark" in str(self.cget('bg')) else "#ffffff", padx=15, pady=10, highlightthickness=1, highlightbackground="#0078d7")
        kpi_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(kpi_frame, text="Gesamtwert:", font=("Segoe UI", 12), background=kpi_frame.cget("bg")).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=f"{total_value:.2f} €", font=("Segoe UI", 16, "bold"), foreground="#28a745", background=kpi_frame.cget("bg")).grid(row=0, column=1, sticky="w", padx=15, pady=2)
        
        ttk.Label(kpi_frame, text="Lagermenge:", font=("Segoe UI", 12), background=kpi_frame.cget("bg")).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=f"{(total_weight/1000):.2f} kg", font=("Segoe UI", 14, "bold"), background=kpi_frame.cget("bg")).grid(row=1, column=1, sticky="w", padx=15, pady=2)
        
        ttk.Label(kpi_frame, text="Aktive Spulen:", font=("Segoe UI", 12), background=kpi_frame.cget("bg")).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=str(total_spools), font=("Segoe UI", 14, "bold"), background=kpi_frame.cget("bg")).grid(row=2, column=1, sticky="w", padx=15, pady=2)

        ttk.Label(left_panel, text="Aufschlüsselung nach Material:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        tree_mat = ttk.Treeview(left_panel, columns=("mat", "count", "weight", "value", "avg"), show="headings", height=6)
        for col, head, w in zip(("mat", "count", "weight", "value", "avg"), ("Material", "Stk", "Gewicht", "Wert", "Ø Preis/kg"), (100, 40, 80, 80, 80)): 
            tree_mat.heading(col, text=head)
            tree_mat.column(col, width=w, anchor="center" if col != "mat" else "w")
        tree_mat.pack(fill="both", expand=True)
        
        for mat, stats in sorted(mat_stats.items(), key=lambda x: x[1]['value'], reverse=True): 
            kg = stats['weight'] / 1000
            avg_price = (stats['value'] / kg) if kg > 0 else 0
            tree_mat.insert("", "end", values=(mat, stats['count'], f"{kg:.2f} kg", f"{stats['value']:.2f} €", f"{avg_price:.2f} €"))

        # --- 4. RECHTE SEITE (Schickes Verbrauchs-Chart) ---
        ttk.Label(right_panel, text="Verbrauch der letzten 7 Tage:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        import datetime, json, os, re
        data_dir = getattr(self.app.data_manager, 'base_dir', '')
        history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f: history = json.load(f)
            except: pass
                
        today = datetime.date.today()
        last_7_days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        values = [history.get(day, 0.0) for day in last_7_days]
        max_val = max(values) if max(values) > 0 else 100 
        
        c_width, c_height = 420, 260
        canvas_bg = "#1e1e1e" if "dark" in str(self.cget('bg')) else "#f9f9f9"
        canvas = tk.Canvas(right_panel, width=c_width, height=c_height, bg=canvas_bg, highlightthickness=1, highlightbackground="#333")
        canvas.pack(fill="both", expand=True, pady=0)
        
        text_col = "white" if "dark" in str(self.cget('bg')) else "black"
        for i in range(4):
            y_line = 40 + i * ((c_height - 80) / 3)
            val_line = max_val - (i * (max_val / 3))
            canvas.create_line(40, y_line, c_width - 20, y_line, fill="#444", dash=(4, 4))
            canvas.create_text(20, y_line, text=f"{int(val_line)}g", fill="gray", font=("Segoe UI", 8))
        
        bar_width = 35
        spacing = (c_width - 80 - (7 * bar_width)) / 6
        start_x = 50
        
        for i, val in enumerate(values):
            x0 = start_x + i * (bar_width + spacing)
            x1 = x0 + bar_width
            bar_height = (val / max_val) * (c_height - 80) 
            y0 = c_height - 40 - bar_height
            y1 = c_height - 40
            
            color = "#0078d7" if val > 0 else ("#333333" if "dark" in str(self.cget('bg')) else "#dddddd")
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            
            if val > 0:
                canvas.create_text(x0 + bar_width/2, y0 - 12, text=f"{int(val)}g", fill=text_col, font=("Segoe UI", 9, "bold"))
                
            day_obj = datetime.datetime.strptime(last_7_days[i], "%Y-%m-%d")
            day_name = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][day_obj.weekday()]
            font_w = ("Segoe UI", 10, "bold") if i == 6 else ("Segoe UI", 9)
            col_w = "#0078d7" if i == 6 else "gray"
            canvas.create_text(x0 + bar_width/2, c_height - 20, text=day_name, fill=col_w, font=font_w)

        total_7d = sum(values)
        ttk.Label(right_panel, text=f"Gesamtverbrauch (7 Tage): {total_7d:.1f} g", font=("Segoe UI", 10, "italic"), foreground="gray").pack(anchor="e", pady=2)

        # --- 5. FOOTER BUTTONS (Zuerst packen & nach unten anheften!) ---
        btn_frm = ttk.Frame(self.main_content)
        btn_frm.pack(fill="x", side="bottom", pady=10, padx=20)
        
        ttk.Button(btn_frm, text="Schließen", command=self.destroy, style="Accent.TButton").pack(side="right", padx=5)
        self.lbl_total = ttk.Label(btn_frm, text="", font=("Segoe UI", 12, "bold"), foreground="#0078d7")
        self.lbl_total.pack(side="left")

        # --- 6. UNTERER BEREICH (Tabelle) ---
        ttk.Separator(self.main_content, orient="horizontal").pack(fill="x", padx=20, pady=10)
        
        hist_lbl_frm = ttk.Frame(self.main_content)
        hist_lbl_frm.pack(fill="x", padx=20, pady=(0, 5))
        ttk.Label(hist_lbl_frm, text="📜 Globale Druck-Historie", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(hist_lbl_frm, text="Alle protokollierten Verbräuche (Doppelklick zum Bearbeiten/Löschen)", foreground="gray").pack(side="left", padx=10)

        history_frm = ttk.Frame(self.main_content)
        history_frm.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        self.history_map = {}
        all_prints = []
        for item in self.inventory:
            hist = item.get("history", [])
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', '')).strip()
            spool_name = f"[{item.get('id', '?')}] {item.get('brand', '')} {color_clean}"
            
            for idx, h in enumerate(hist):
                all_prints.append({
                    "spool_id": item['id'],
                    "hist_idx": idx,
                    "date": h.get("date", ""),
                    "action": h.get("action", ""),
                    "spool": spool_name,
                    "change": h.get("change", ""),
                    "cost": h.get("cost", "-"),
                    "sell": h.get("sell_price", "-")
                })
        
        all_prints.sort(key=lambda x: x["date"], reverse=True)

        columns = ("date", "action", "spool", "change", "cost", "sell")
        self.tree_hist = ttk.Treeview(history_frm, columns=columns, show="headings", height=10)
        self.tree_hist.heading("date", text="Datum & Zeit")
        self.tree_hist.heading("action", text="Druck / Aktion")
        self.tree_hist.heading("spool", text="Verwendete Spule")
        self.tree_hist.heading("change", text="Verbrauch")
        self.tree_hist.heading("cost", text="Kosten")
        self.tree_hist.heading("sell", text="VK-Preis")

        self.tree_hist.column("date", width=130)
        self.tree_hist.column("action", width=310)
        self.tree_hist.column("spool", width=240)
        self.tree_hist.column("change", width=80, anchor="e")
        self.tree_hist.column("cost", width=80, anchor="e")
        self.tree_hist.column("sell", width=80, anchor="e")
        
        scroll_hist = ttk.Scrollbar(history_frm, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=scroll_hist.set)
        
        self.tree_hist.pack(side="left", fill="both", expand=True)
        scroll_hist.pack(side="right", fill="y")
        
        self.tree_hist.bind("<Double-1>", self.on_edit_entry)

        total_costs = 0.0
        for p in all_prints:
            iid = self.tree_hist.insert("", "end", values=(p["date"], p["action"], p["spool"], p["change"], p["cost"], p["sell"]))
            self.history_map[iid] = {"spool_id": p["spool_id"], "hist_idx": p["hist_idx"]}
            try:
                c_str = p["cost"].replace(" €", "").replace(",", ".")
                total_costs += float(c_str)
            except:
                pass

        self.lbl_total.config(text=f"Gesamtkosten aller Einträge: {total_costs:.2f} €")


    
    def on_edit_entry(self, event):
        sel = self.tree_hist.selection()
        if not sel: return
        
        data = self.history_map.get(sel[0])
        if not data: return
        
        spool_id = data["spool_id"]
        hist_idx = data["hist_idx"]
        
        spool = next((s for s in self.inventory if s['id'] == spool_id), None)
        if not spool or "history" not in spool or hist_idx >= len(spool["history"]): return
        
        entry = spool["history"][hist_idx]
        
        # --- NEU: Side-Panel aktivieren ---
        for widget in self.side_panel.winfo_children():
            widget.destroy()
            
        self.side_panel.pack(side="right", fill="y", before=self.main_content)
        
        header = ttk.Frame(self.side_panel)
        header.pack(fill="x", pady=10, padx=10)
        ttk.Label(header, text="✏️ Eintrag bearbeiten", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(header, text="❌", width=3, command=self.side_panel.pack_forget).pack(side="right")
        ttk.Separator(self.side_panel, orient="horizontal").pack(fill="x")
        
        frm = ttk.Frame(self.side_panel, padding=10)
        frm.pack(fill="both", expand=True)
        
        ttk.Label(frm, text="Aktion / Druckname:").pack(anchor="w")
        ent_action = ttk.Entry(frm)
        ent_action.insert(0, entry.get("action", ""))
        ent_action.pack(fill="x", pady=(0, 10))
        
        ttk.Label(frm, text="Verbrauch (inkl. Vorzeichen):").pack(anchor="w")
        ent_change = ttk.Entry(frm)
        ent_change.insert(0, entry.get("change", "").replace("g", "")) 
        ent_change.pack(fill="x", pady=(0, 10))
        
        ttk.Label(frm, text="Kosten:").pack(anchor="w")
        frm_cost = ttk.Frame(frm)
        frm_cost.pack(fill="x", pady=(0, 10))
        
        def calc_cost():
            try:
                w_str = ent_change.get().replace('g', '').replace(',', '.').strip()
                w_val = abs(float(w_str)) if w_str else 0.0
                p = float(str(spool.get('price', '0')).replace(',', '.')) or 0.0
                c = float(str(spool.get('capacity', '1000'))) or 1000.0
                m_cost = w_val * (p / c) if c > 0 else 0.0
                ent_cost.delete(0, tk.END)
                ent_cost.insert(0, f"{m_cost:.2f} €")
            except: pass

        btn_calc_cost = ttk.Button(frm_cost, text="🧮 Mat.", width=8, command=calc_cost)
        btn_calc_cost.pack(side="left", padx=(0, 5))
        
        ent_cost = ttk.Entry(frm_cost)
        ent_cost.insert(0, entry.get("cost", "-"))
        ent_cost.pack(side="left", fill="x", expand=True)
        
        ttk.Label(frm, text="VK-Preis:").pack(anchor="w")
        frm_sell = ttk.Frame(frm)
        frm_sell.pack(fill="x", pady=(0, 10))
        
        def calc_vk():
            try:
                cost_str = ent_cost.get().replace('€', '').replace(',', '.').strip()
                cost_val = float(cost_str) if cost_str and cost_str != '-' else 0.0
                margin = int(self.app.settings.get("profit_margin", 0))
                vk_val = cost_val * (1 + (margin / 100.0))
                ent_sell.delete(0, tk.END)
                ent_sell.insert(0, f"{vk_val:.2f} €")
                if margin == 0:
                    from tkinter import messagebox
                    messagebox.showinfo("Info", "Gewinnmarge ist 0%. VK = Kosten.", parent=self)
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Fehler", "Bitte Kosten eintragen!", parent=self)
                
        btn_calc_vk = ttk.Button(frm_sell, text="🧮 Marge", width=8, command=calc_vk)
        btn_calc_vk.pack(side="left", padx=(0, 5))
        
        ent_sell = ttk.Entry(frm_sell)
        ent_sell.insert(0, entry.get("sell_price", "-"))
        ent_sell.pack(side="left", fill="x", expand=True)
        
        def save():
            new_val_str = ent_change.get().replace("g", "").replace(" ", "").replace(",", ".")
            try: new_val = -abs(float(new_val_str)) if float(new_val_str) != 0 else 0.0
            except: new_val = 0.0
                
            old_val_str = entry.get("change", "0").replace("g", "").replace(" ", "").replace(",", ".")
            try: old_val = float(old_val_str)
            except: old_val = 0.0
            
            delta = new_val - old_val
            if delta != 0.0:
                curr_gross = float(spool.get('weight_gross', 0))
                spool['weight_gross'] = round(max(0.0, curr_gross + delta), 1)
                
            entry["action"] = ent_action.get().strip()
            entry["change"] = f"{new_val:g}g"
            entry["cost"] = ent_cost.get().strip()
            entry["sell_price"] = ent_sell.get().strip()
            
            import datetime, json, os
            date_str = entry.get("date", "").split(" ")[0]
            if not date_str: date_str = datetime.date.today().isoformat()
                        
            data_dir = getattr(self.app.data_manager, 'base_dir', '')
            history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
            hist_data = {}
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r") as f: hist_data = json.load(f)
                except: pass
                
            # FIX: Nur die exakte Differenz zum bestehenden Tages-Total verrechnen!
            if delta != 0.0:
                current_day_total = hist_data.get(date_str, 0.0)
                # Da delta negativ ist, wenn der Verbrauch höher wird, ziehen wir es ab!
                new_day_total = max(0.0, current_day_total - delta)
                hist_data[date_str] = round(new_day_total, 1)
            
                try:
                    with open(history_file, "w") as f: json.dump(hist_data, f, indent=4)
                except: pass
            
            self.app.data_manager.save_inventory(self.inventory)
            self.app.refresh_table()
            self.build_ui()

        def delete():
            from tkinter import messagebox
            if messagebox.askyesno("Löschen", "Wirklich löschen?", parent=self):
                old_val_str = entry.get("change", "0").replace("g", "").replace(" ", "").replace(",", ".")
                try: old_val = float(old_val_str)
                except: old_val = 0.0
                
                curr_gross = float(spool.get('weight_gross', 0))
                spool['weight_gross'] = round(max(0.0, curr_gross - old_val), 1)
                
                import datetime, json, os
                date_str = entry.get("date", "").split(" ")[0]
                if not date_str: date_str = datetime.date.today().isoformat()
                
                data_dir = getattr(self.app.data_manager, 'base_dir', '')
                history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
                hist_data = {}
                if os.path.exists(history_file):
                    try:
                        with open(history_file, "r") as f: hist_data = json.load(f)
                    except: pass
                
                # FIX: Das gelöschte Filament aus dem Balkendiagramm abziehen
                if old_val != 0.0:
                    current_day_total = hist_data.get(date_str, 0.0)
                    new_day_total = max(0.0, current_day_total + old_val)
                    hist_data[date_str] = round(new_day_total, 1)
                    
                    try:
                        with open(history_file, "w") as f: json.dump(hist_data, f, indent=4)
                    except: pass

                del spool["history"][hist_idx]
                
                self.app.data_manager.save_inventory(self.inventory)
                self.app.refresh_table()
                self.build_ui()

        btn_frm_action = ttk.Frame(self.side_panel)
        btn_frm_action.pack(fill="x", pady=10, padx=10, side="bottom")
        ttk.Button(btn_frm_action, text="🗑️", command=delete, style="Delete.TButton", width=3).pack(side="left", padx=5)
        ttk.Button(btn_frm_action, text="💾 Speichern", command=save, style="Accent.TButton").pack(side="right", padx=5)

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
            base_d = getattr(self.data_manager, 'base_dir', '')
            hist_f = os.path.join(base_d, "history.json") if base_d else "history.json"
            mqtt_f = os.path.join(base_d, "mqtt_buffer.json") if base_d else "mqtt_buffer.json"
            
            with zipfile.ZipFile(fp, 'w') as z:
                for f, n in [
                    (self.data_manager.data_file, "inventory.json"), 
                    (self.data_manager.settings_file, "settings.json"), 
                    (self.data_manager.spools_file, "spools.json"),
                    (hist_f, "history.json"),
                    (mqtt_f, "mqtt_buffer.json")
                ]:
                    if os.path.exists(f): z.write(f, n)
            messagebox.showinfo("Erfolg", "Backup erstellt!", parent=self)
            self.destroy()
        except Exception as e: 
            messagebox.showerror("Fehler", str(e), parent=self)
    
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

def create_tray_icon():
    # Zeichnet einen simplen blauen Kreis als Platzhalter-Icon
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(0, 120, 215))
    return image

class ManualPrintDialog(tk.Toplevel):
    def __init__(self, parent, spool_item, settings, callback):
        super().__init__(parent)
        self.spool = spool_item
        self.settings = settings
        self.callback = callback
        
        self.title("✍️ Manuellen Druck protokollieren")
        # FIX 1: Fenster etwas größer machen für Windows Skalierung (>100%)
        self.geometry("450x550")
        self.configure(bg=parent.cget('bg'))
        self.attributes('-topmost', True)
        from core.utils import center_window
        center_window(self, parent)

        ttk.Label(self, text="Druck-Details eingeben", font=("Segoe UI", 14, "bold")).pack(pady=15)

        # FIX 2: Button Frame ZUERST packen und hart unten anheften (side="bottom"), 
        # damit es niemals aus dem Fenster geschoben wird!
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(fill="x", side="bottom")

        # Eingabefelder (Packen wir NACH den Buttons)
        lbl_frame = ttk.Frame(self, padding=20)
        lbl_frame.pack(fill="both", expand=True)

        ttk.Label(lbl_frame, text="Name des Drucks (z.B. Benchy):").pack(anchor="w")
        self.ent_name = ttk.Entry(lbl_frame)
        self.ent_name.insert(0, "Manueller Druck")
        self.ent_name.pack(fill="x", pady=(0, 15))

        ttk.Label(lbl_frame, text="Verbrauch in Gramm (g):").pack(anchor="w")
        self.ent_weight = ttk.Entry(lbl_frame)
        self.ent_weight.pack(fill="x", pady=(0, 15))

        ttk.Label(lbl_frame, text="Druckdauer in Stunden (h) - Optional:").pack(anchor="w")
        self.ent_time = ttk.Entry(lbl_frame)
        self.ent_time.insert(0, "0")
        self.ent_time.pack(fill="x", pady=(0, 15))

        def on_confirm():
            try:
                name = self.ent_name.get()
                
                # Werte sicher auslesen und leere Felder abfangen
                w_str = self.ent_weight.get().replace(",", ".").strip()
                t_str = self.ent_time.get().replace(",", ".").strip()
                if not w_str: w_str = "0"
                if not t_str: t_str = "0"
                
                weight = float(w_str)
                hours = float(t_str)
                
                # --- KOSTEN-RECHNUNG ---
                # Materialkosten (Kugelsicher gegen leere Preise oder "€" Zeichen!)
                price_str = str(self.spool.get('price', '0')).replace(',', '.').replace('€', '').strip()
                price = float(price_str) if price_str else 0.0
                
                cap_str = str(self.spool.get('capacity', '1000')).strip()
                cap = float(cap_str) if cap_str else 1000.0
                
                mat_cost = weight * (price / cap) if cap > 0 else 0.0
                
                # Stromkosten
                kwh_price = float(self.settings.get("kwh_price", 0.30))
                watts = int(self.settings.get("printer_watts", 150))
                elec_cost = hours * (watts / 1000.0) * kwh_price
                
                # NEU: Maschinenverschleiß
                wear_price = float(self.settings.get("wear_per_hour", 0.20))
                wear_cost = hours * wear_price
                
                # ECHTE Gesamtkosten
                total_cost = mat_cost + elec_cost + wear_cost
                
                # NEU: Optionale Gewinnmarge (Wird im Dialog angezeigt, aber die reinen Kosten gehen ins Logbuch!)
                margin_percent = int(self.settings.get("profit_margin", 0))
                sell_price = total_cost * (1 + (margin_percent / 100.0))
                
                # Wenn Marge aktiv ist, zeigen wir dem User an, was er verlangen sollte!
                if margin_percent > 0:
                    from tkinter import messagebox
                    msg = f"Kalkulation für '{name}':\n\n"
                    msg += f"Material: {mat_cost:.2f} €\n"
                    msg += f"Strom: {elec_cost:.2f} €\n"
                    msg += f"Verschleiß: {wear_cost:.2f} €\n"
                    msg += f"------------------------\n"
                    msg += f"Echte Kosten: {total_cost:.2f} €\n\n"
                    msg += f"Empfohlener Verkaufspreis (+{margin_percent}%): {sell_price:.2f} €"
                    messagebox.showinfo("💰 Kalkulation", msg, parent=self)
                
                # Wir geben jetzt Gewicht, Name, Kosten UND Verkaufspreis zurück
                self.callback(weight, name, f"{total_cost:.2f} €", f"{sell_price:.2f} €")
                self.destroy()
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Fehler", "Bitte gültige Zahlen für Gewicht und Zeit eingeben!", parent=self)

        ttk.Button(btn_frame, text="Druck speichern", command=on_confirm, style="Accent.TButton").pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(side="left")


class FilamentApp:
    def __init__(self, root):
        self.root = root; 
        self.data_manager = DataManager(DEFAULT_SETTINGS)
        # Explicitly hint types to help Pylance
        self.inventory: list[dict] = []
        self.settings: dict = {}
        self.spools: list[dict] = []
        # Pylance Definitionen für Hintergrund-Tasks
        self.tray_icon = None
        self.active_popups = set()
        self.stats_dialog = None  # Pylance-Fix: Platzhalter für das Finanz-Dashboard
        
        # Suppress type checking for this assignment since load_all returns (list, dict, list)
        inventory_data, settings_data, spools_data = self.data_manager.load_all(DEFAULT_SETTINGS)
        self.inventory = inventory_data if isinstance(inventory_data, list) else []
        self.settings = settings_data if isinstance(settings_data, dict) else {}
        self.spools = spools_data if isinstance(spools_data, list) else []

        # --- NEU: Gespeicherte Sortierung laden ---
        self.current_sort_col = self.settings.get("sort_col", "id")
        self.current_sort_reverse = self.settings.get("sort_reverse", False)
        self.last_selected_type = "LAGER"
        
        
        self.root.geometry(str(self.settings.get("geometry", "1500x980")))
        self.root.title(f"VibeSpool {APP_VERSION}"); self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.icon_cache = []
        self.mqtt_retry_active = False # Pylance-Anmeldung für den Offline-Buffer

        # --- APP ICON LADEN ---
        try:
            import os, sys
            # Wenn als .exe ausgeführt, liegt das Bild im temporären _MEIPASS Ordner
            # getattr() verhindert den Pylance-Fehler "not a known attribute"
            if hasattr(sys, '_MEIPASS'):
                base_path = getattr(sys, '_MEIPASS')
            else:
                base_path = os.path.abspath(".")
                
            icon_path = os.path.join(base_path, "core", "vibespool-icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

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
        self.filter_brand_var = tk.StringVar(value="Alle Hersteller")
        self.combo_filter_brand = ttk.Combobox(top_bar, textvariable=self.filter_brand_var, state="readonly", width=15); self.combo_filter_brand.pack(side="left", padx=5); self.combo_filter_brand.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        ttk.Button(top_bar, text="🔄 Reset", command=self.reset_filters).pack(side="left", padx=5); ttk.Label(top_bar, text=" Quick-ID:").pack(side="left", padx=(10,0)); self.entry_scan = ttk.Entry(top_bar, width=8); self.entry_scan.pack(side="left", padx=5); self.entry_scan.bind("<Return>", self.on_quick_scan)
        ttk.Button(top_bar, text="📷", width=3, command=self.scan_qr_webcam).pack(side="left")
        ttk.Button(top_bar, text="📱 Handy", command=self.open_mobile_companion).pack(side="left", padx=5)
        self.btn_opts = ttk.Menubutton(top_bar, text="⚙ Optionen")
        self.menu_opts = tk.Menu(self.btn_opts, tearoff=0)
        self.menu_opts.add_command(label="⚙ Alle Einstellungen öffnen", command=self.open_settings)
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="📦 Lager-Layout planen", command=lambda: self.open_settings(0))
        self.menu_opts.add_command(label="🤖 Drucker & AMS", command=lambda: self.open_settings(1))
        self.menu_opts.add_command(label="💰 Druckkosten-Rechner", command=lambda: self.open_settings(2))
        self.menu_opts.add_command(label="⚙ System-Optionen & Smart Home", command=lambda: self.open_settings(3))
        self.menu_opts.add_command(label="📋 Listen-Verwaltung", command=lambda: self.open_settings(4))
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="📥 CSV Inventar Importieren", command=self.import_csv)
        self.menu_opts.add_command(label="💾 Datenbank Backup / Restore", command=lambda: BackupDialog(self.root, self.data_manager, self))
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="🔄 Update-Check", command=self.manual_update_check)
        self.btn_opts["menu"] = self.menu_opts
        self.btn_opts.pack(side="right", padx=5)
        
        ttk.Button(top_bar, text="🛒 Einkaufsliste", command=lambda: ShoppingListDialog(self.root, self.inventory, self)).pack(side="right", padx=5)
        
        # --- NEU: Spenden-Button mit echtem goldenem Verlauf! ---
        def make_gradient(w, h, c1, c2):
            img = Image.new("RGB", (w, h))
            draw = ImageDraw.Draw(img)
            r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
            r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
            for x in range(w):
                r = int(r1 + (r2 - r1) * x / w)
                g = int(g1 + (g2 - g1) * x / w)
                b = int(b1 + (b2 - b1) * x / w)
                draw.line([(x, 0), (x, h)], fill=(r,g,b))
            return ImageTk.PhotoImage(img)
            
        self.donate_img = make_gradient(110, 28, "#FFD700", "#FF8C00") # Gold zu Dunkelorange
        self.btn_donate = tk.Button(top_bar, text="☕ Spenden", image=self.donate_img, compound="center", 
                                    command=self.open_paypal, font=("Segoe UI", 9, "bold"), fg="#333333", 
                                    bg="#FFD700", activebackground="#FF8C00", borderwidth=0, cursor="hand2")
        self.btn_donate.pack(side="right", padx=5)

        self.btn_theme = ttk.Button(top_bar, text="...", command=self.toggle_theme); self.btn_theme.pack(side="right", padx=5); self.update_theme_button_text()

        # --- SIDEBAR BUTTONS ---
        self.nav_btns = []
        def add_nav_btn(text, cmd, icon_txt=None):
            # NEU: justify="center" erzwingt die mittige Ausrichtung
            btn = tk.Button(self.nav_sidebar, text=f"{icon_txt}\n{text}" if icon_txt else text, command=cmd, 
                           font=("Segoe UI", 8), bd=0, pady=15, cursor="hand2", justify="center")
            btn.pack(fill="x")
            self.nav_btns.append(btn)
            btn.bind("<Enter>", lambda e: self.on_nav_btn_hover(btn, True))
            btn.bind("<Leave>", lambda e: self.on_nav_btn_hover(btn, False))
            return btn

        add_nav_btn("Regal", lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools, self), "📦")
        add_nav_btn("Spulen", lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown), "🧵")
        
        # FIX: Ein Leerzeichen vor dem Emoji schiebt es optisch genau in die Mitte!
        add_nav_btn("Label", lambda: LabelCreatorDialog(self.root, self.inventory), "   🏷️")

        # --- NEU: Dashboard-Referenz speichern für Live-Updates (Pylance-sicher!) ---
        def open_statistics():
            dlg = self.stats_dialog # Lokale Kopie für Pylance
            if dlg is not None and dlg.winfo_exists():
                dlg.focus_set()
                dlg.build_ui() # Wenn schon offen: Einfach live neu zeichnen!
            else:
                self.stats_dialog = StatisticsDialog(self.root, self.inventory, self)

        add_nav_btn("Finanzen", lambda: StatisticsDialog(self.root, self.inventory, self), "📊")
        add_nav_btn("Swap", self.quick_swap_dialog, "🔄")
        add_nav_btn("Flow", lambda: FlowCalculatorDialog(self.root, self.entry_flow), "🧪")
        add_nav_btn("Kalkulator", lambda: self.toggle_side_panel("🧮 Quick-Cost Rechner", self.build_quick_cost_calculator), "🧮") # <-- NEU!
        if self.settings.get("use_bambu", False):
            add_nav_btn("AMS", self.run_ams_sync, "🤖")
        # --- NEU: Cloud Sync im linken Menü ---
        self.btn_cloud = add_nav_btn("Cloud", self.open_bambu_cloud_sync, "☁️")
        if not self.settings.get("use_bambu_cloud", True):
            self.btn_cloud.pack_forget()
        add_nav_btn("Aufträge", lambda: PrintQueueDialog(self.root, self), "📝")
            
        self.nav_sep = tk.Label(self.nav_sidebar, height=1)
        self.nav_sep.pack(fill="x", pady=10)
        add_nav_btn("Neu", self.clear_inputs, "➕")
        add_nav_btn("Hilfe", self.show_howto, "❓") # NEU: Hilfe/Wiki Button
        
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
        
        # Canvas konfigurieren, damit es mit dem Frame (in der Höhe) mitwächst
        sidebar.bind(
            "<Configure>",
            lambda e: self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))
        )
        
        # NEU: Das Fenster ohne feste Breite erstellen und die ID speichern
        canvas_window = self.form_canvas.create_window((0, 0), window=sidebar, anchor="nw")
        
        # NEU: Das innere Formular IMMER exakt an die verbleibende Canvas-Breite anpassen!
        self.form_canvas.bind(
            "<Configure>", 
            lambda e: self.form_canvas.itemconfig(canvas_window, width=e.width)
        )
        
        self.form_canvas.configure(yscrollcommand=self.form_scrollbar.set)

        # Scrollbar und Canvas platzieren
        self.form_scrollbar.pack(side="right", fill="y")
        self.form_canvas.pack(side="left", fill="both", expand=True)

        self.notebook = ttk.Notebook(sidebar)
        self.notebook.pack(fill="both", expand=True)
        tab_basis = ttk.Frame(self.notebook, padding=10)
        tab_erp = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_basis, text="Basis & Lager")
        self.notebook.add(tab_erp, text="Kaufmännisch")

        # --- ID & RFID ---
        frm_id = ttk.Frame(tab_basis)
        frm_id.pack(fill="x", pady=2)
        ttk.Label(frm_id, text="ID:").pack(side="left")
        self.entry_id = ttk.Entry(frm_id, width=10, font=FONT_BOLD)
        self.entry_id.pack(side="left", padx=5)
        ttk.Label(frm_id, text="RFID:").pack(side="left", padx=(10, 0))
        self.entry_rfid = ttk.Entry(frm_id, width=15)
        self.entry_rfid.pack(side="left", padx=5)

        # --- Marke ---
        ttk.Label(tab_basis, text="Marke:").pack(anchor="w", pady=(10,0))
        self.entry_brand = ttk.Combobox(tab_basis, values=sorted(self.settings.get("brands", []), key=str.lower), font=FONT_MAIN)
        self.entry_brand.pack(fill="x", pady=2)
        self.entry_brand.bind("<<ComboboxSelected>>", self.auto_match_spool)
        self.entry_brand.bind("<FocusOut>", self.auto_match_spool)

        # --- NEU: Material & Effekt in EINER Zeile ---
        mat_eff_frame = ttk.Frame(tab_basis)
        mat_eff_frame.pack(fill="x", pady=(10, 0))

        # Linke Spalte: Material
        mat_frame = ttk.Frame(mat_eff_frame)
        mat_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(mat_frame, text="Material:").pack(anchor="w")
        self.combo_material = ttk.Combobox(mat_frame, values=self.settings.get("materials", MATERIALS), font=FONT_MAIN)
        self.combo_material.pack(fill="x", pady=2)

        # Rechte Spalte: Effekt / Typ
        eff_frame = ttk.Frame(mat_eff_frame)
        eff_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(eff_frame, text="Effekt / Typ:").pack(anchor="w")
        self.combo_subtype = ttk.Combobox(eff_frame, values=self.settings.get("subtypes", SUBTYPES), font=FONT_MAIN)
        self.combo_subtype.pack(fill="x", pady=2)

        # --- Farbe (mit smartem Multi-Color Picker) ---
        ttk.Label(tab_basis, text="Farbe (Für Mehrfarbig mit '/' trennen):").pack(anchor="w", pady=(10,0))
        frm_col = ttk.Frame(tab_basis)
        frm_col.pack(fill="x", pady=2)
        
        self.combo_color = ttk.Combobox(frm_col, values=self.settings.get("colors", COMMON_COLORS), font=FONT_MAIN)
        self.combo_color.pack(side="left", fill="x", expand=True)
        self.combo_color.bind("<KeyRelease>", self.update_color_preview)
        self.combo_color.bind("<<ComboboxSelected>>", self.update_color_preview)

        # --- NEU: Auto-Übersetzer für manuelle Eingaben per Tastatur ---
        def format_manual_color_entry(event=None):
            current_text = self.combo_color.get().strip()
            if not current_text: return

            parts = [p.strip() for p in current_text.split('/')]
            new_parts = []

            for part in parts:
                # Suchen wir nach einem Hex-Code in diesem Abschnitt
                hex_match = re.search(r'#[0-9a-fA-F]{6}', part)
                if hex_match:
                    hex_code = hex_match.group(0).upper()
                    matched_name = ""
                    
                    # Prio 1: Suche in der Liste des Users
                    for preset in self.settings.get("colors", COMMON_COLORS):
                        if hex_code in preset:
                            matched_name = preset.split('(')[0].strip()
                            break
                            
                    # Prio 2: Suche in unserer großen core/colors.py Datenbank
                    if not matched_name:
                        matched_name = get_color_name_from_hex(hex_code)

                    if matched_name:
                        new_parts.append(f"{matched_name} ({hex_code})")
                    else:
                        # Wenn wir gar keinen Namen kennen, behalten wir exakt das, was der User getippt hat
                        new_parts.append(part)
                else:
                    # Kein Hex-Code drin -> Einfach unverändert lassen
                    new_parts.append(part)

            # Neu zusammenbauen
            new_text = " / ".join(new_parts)
            
            # Nur aktualisieren, wenn sich wirklich was geändert hat
            if new_text != current_text:
                self.combo_color.set(new_text)
                self.update_color_preview()

        # Bindings: Die Auto-Korrektur feuert, wenn man das Feld verlässt (FocusOut) oder Enter drückt
        self.combo_color.bind("<FocusOut>", format_manual_color_entry)
        self.combo_color.bind("<Return>", format_manual_color_entry)

        def pick_smart_color():
            # Öffnet den Windows-Farbdialog
            color_code = colorchooser.askcolor(title="Farbe wählen", parent=self.root)[1]
            if not color_code: return
            
            color_code = color_code.upper()
            current_text = self.combo_color.get().strip()
            
            matched_name = ""
            for preset in self.settings.get("colors", COMMON_COLORS):
                if color_code in preset:
                    matched_name = preset.split('(')[0].strip()
                    break
                    
            if not matched_name:
                matched_name = get_color_name_from_hex(color_code)

            new_entry = f"{matched_name} ({color_code})" if matched_name else color_code

            if not current_text:
                self.combo_color.set(new_entry)
            else:
                self.combo_color.set(f"{current_text} / {new_entry}")
                
            self.update_color_preview()
                
        # Ein einziger, smarter Button!
        ttk.Button(frm_col, text="🎨", width=4, command=pick_smart_color).pack(side="left", padx=(5, 2))
        
        self.lbl_color_preview = tk.Label(frm_col, borderwidth=0)
        self.lbl_color_preview.pack(side="left")
        self.update_color_preview()

        # --- Trennlinie & Spule ---
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=5)
        
        frm_spool_header = ttk.Frame(tab_basis)
        frm_spool_header.pack(fill="x", pady=(5,0))
        ttk.Label(frm_spool_header, text="Spule / Leergewicht:").pack(side="left")
        
        self.var_is_refill = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm_spool_header, text="🔄 Refill", variable=self.var_is_refill).pack(side="right")

        frm_spool = ttk.Frame(tab_basis)
        frm_spool.pack(fill="x", pady=2)
        
        self.combo_spool = ttk.Combobox(frm_spool, state="readonly", font=FONT_MAIN)
        self.combo_spool.pack(side="left", fill="x", expand=True)
        
        self.var_custom_empty = tk.StringVar(value="")
        self.entry_custom_empty = ttk.Entry(frm_spool, textvariable=self.var_custom_empty, width=6, font=FONT_BOLD)
        self.entry_custom_empty.pack(side="left", padx=(5, 2))
        ttk.Label(frm_spool, text="g").pack(side="left")
        
        def calc_custom_empty():
            try:
                cap = float(self.var_capacity.get().replace(",", "."))
                gross = float(self.var_gross.get().replace(",", "."))
                if gross > cap:
                    self.combo_spool.current(0)
                    self.var_custom_empty.set(f"{(gross - cap):g}")
                    self.update_net_weight_display()
                else:
                    messagebox.showinfo("Info", "Brutto muss größer als Netto-Inhalt sein!", parent=self.root)
            except: pass

        btn_auto_empty = ttk.Button(frm_spool, text="🧮", width=3, command=calc_custom_empty)
        btn_auto_empty.pack(side="left", padx=(5, 0))
        btn_auto_empty.bind("<Enter>", lambda e: self.show_tip(e, "Leergewicht (Brutto minus Netto) für einmalige Spulen berechnen"))
        btn_auto_empty.bind("<Leave>", self.hide_tip)
        
        self.last_selected_spool_id = -1
        self.combo_spool.bind("<<ComboboxSelected>>", self.on_spool_changed)
        self.var_custom_empty.trace_add("write", lambda n, i, m: self.update_net_weight_display())
        
        ttk.Label(tab_basis, text="Original-Inhalt (Netto g):").pack(anchor="w", pady=(10,0))
        self.entry_capacity = ttk.Entry(tab_basis, font=FONT_MAIN, textvariable=self.var_capacity)
        self.entry_capacity.pack(fill="x", pady=2)
        
        ttk.Label(tab_basis, text="Gewicht auf Waage (Brutto g):").pack(anchor="w", pady=(10,0))
        frm_gross = ttk.Frame(tab_basis)
        frm_gross.pack(fill="x", pady=2)
        
        btn_full = ttk.Button(frm_gross, text="⚖️ Voll", width=6, command=self.set_gross_to_full)
        btn_full.pack(side="left", padx=(0, 5))
        btn_full.bind("<Enter>", lambda e: self.show_tip(e, "Brutto automatisch auf 100% (Kapazität + Spule) setzen"))
        btn_full.bind("<Leave>", self.hide_tip)
        
        self.entry_gross = ttk.Entry(frm_gross, font=FONT_MAIN, textvariable=self.var_gross)
        self.entry_gross.pack(side="left", fill="x", expand=True)
        # --- Slicer-Verbrauch Bereich ---
        frm_slicer = ttk.Frame(tab_basis)
        frm_slicer.pack(fill="x", pady=(10, 10))
        
        # Zeile 1: Label
        ttk.Label(frm_slicer, text="Slicer-Verbrauch (g):").pack(anchor="w", pady=(0, 2))
        
        # Zeile 2: Eingabefeld (Volle Breite, passend zu den anderen)
        self.entry_slicer = ttk.Entry(frm_slicer, font=FONT_MAIN)
        self.entry_slicer.pack(fill="x", pady=2)
        
        # Zeile 3: Buttons (Nebeneinander, strecken sich gleichmäßig)
        frm_slicer_btns = ttk.Frame(frm_slicer)
        frm_slicer_btns.pack(fill="x", pady=(2, 0))
        
        ttk.Button(frm_slicer_btns, text="➕ Druck protokollieren", command=self.deduct_slicer).pack(side="left", expand=True, fill="x", padx=(0, 2))
        ttk.Button(frm_slicer_btns, text="➕ Korrektur", command=self.add_slicer).pack(side="left", expand=True, fill="x", padx=(2, 0))
        
        # NEU: Der Sync-Button wird NUR gebaut, wenn er in den Settings aktiv ist!
        if self.settings.get("use_moonraker", False):
            btn_sync = ttk.Button(frm_gross, text="🤖 Sync", width=8, command=self.subtract_printer_usage)
            btn_sync.pack(side="left", padx=(5,0))
            btn_sync.bind("<Enter>", lambda e: self.show_tip(e, "Letzten Druckverbrauch von Moonraker abrufen"))
            btn_sync.bind("<Leave>", self.hide_tip)
        
        self.lbl_net_weight = ttk.Label(tab_basis, text="Netto (Rest): 0 g | Wert: -", font=("Segoe UI", 10, "bold"), foreground=COLOR_ACCENT); self.lbl_net_weight.pack(anchor="w", pady=(10,5))
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=5)

        # --- NEU: Flow Ratio & Pressure Adv in EINER Zeile ---
        flow_pa_frame = ttk.Frame(tab_basis)
        flow_pa_frame.pack(fill="x", pady=(5, 0))

        # Linke Spalte: Flow Ratio
        flow_frame = ttk.Frame(flow_pa_frame)
        flow_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(flow_frame, text="Flow Ratio:").pack(anchor="w")
        self.entry_flow = ttk.Entry(flow_frame) 
        self.entry_flow.pack(fill="x", pady=2)

        # Rechte Spalte: Pressure Adv
        pa_frame = ttk.Frame(flow_pa_frame)
        pa_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(pa_frame, text="Pressure Adv:").pack(anchor="w")
        self.entry_pa = ttk.Entry(pa_frame)
        self.entry_pa.pack(fill="x", pady=2)

        # --- Trennlinie & Lagerort ---
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=5)
        
        ttk.Label(tab_basis, text="Lagerort:").pack(anchor="w")
        self.combo_type = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN)
        self.combo_type.pack(fill="x", pady=2)
        self.combo_type.bind("<<ComboboxSelected>>", self.update_slot_dropdown)
        
        ttk.Label(tab_basis, text="Slot / Nr.:").pack(anchor="w", pady=(5,0))
        
        self.combo_loc_id = ttk.Combobox(tab_basis, font=FONT_MAIN); self.combo_loc_id.pack(fill="x", pady=2)
        self.var_reorder = tk.BooleanVar(); ttk.Checkbutton(tab_basis, text="Auf Einkaufsliste setzen!", variable=self.var_reorder).pack(anchor="w", pady=10)

        ttk.Label(tab_erp, text="Lieferant / Shop:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_supplier = ttk.Entry(tab_erp); self.entry_supplier.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="SKU / Art-Nr.:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_sku = ttk.Entry(tab_erp); self.entry_sku.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Preis (€):").grid(row=2, column=0, sticky="w", pady=5); self.entry_price = ttk.Entry(tab_erp, textvariable=self.var_price); self.entry_price.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Link:").grid(row=3, column=0, sticky="w", pady=5)
        
        # Frame für Link-Eingabe + Button nebeneinander
        frm_link_action = ttk.Frame(tab_erp)
        frm_link_action.grid(row=3, column=1, sticky="ew", pady=2)
        
        self.entry_link = ttk.Entry(frm_link_action)
        self.entry_link.pack(side="left", fill="x", expand=True)
        
        # Der neue "Direkt-Öffnen" Button
        btn_go = ttk.Button(frm_link_action, text="🔗", width=3, command=self.quick_open_shop)
        btn_go.pack(side="left", padx=(5, 0))
        btn_go.bind("<Enter>", lambda e: self.show_tip(e, "Link im Browser öffnen (inkl. Affiliate)"))
        btn_go.bind("<Leave>", self.hide_tip)
        ttk.Separator(tab_erp, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(tab_erp, text="Nozzle Temp (°C):").grid(row=5, column=0, sticky="w", pady=5); self.entry_temp_n = ttk.Entry(tab_erp); self.entry_temp_n.grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Bed Temp (°C):").grid(row=6, column=0, sticky="w", pady=5); self.entry_temp_b = ttk.Entry(tab_erp); self.entry_temp_b.grid(row=6, column=1, sticky="ew", pady=2)
        # --- NEU: Notiz / Kommentar ---
        ttk.Label(tab_erp, text="Notiz / Kommentar:").grid(row=7, column=0, sticky="w", pady=5)
        self.entry_note = ttk.Entry(tab_erp)
        self.entry_note.grid(row=7, column=1, sticky="ew", pady=2)
        # --- NEU: Eigener Hersteller Barcode ---
        ttk.Label(tab_erp, text="Hersteller Barcode:").grid(row=8, column=0, sticky="w", pady=5)
        self.entry_barcode = ttk.Entry(tab_erp)
        self.entry_barcode.grid(row=8, column=1, sticky="ew", pady=2)
        tab_erp.columnconfigure(1, weight=1)
       
        btn_frame = ttk.Frame(sidebar)
        btn_frame.pack(fill="x", pady=(15, 0))
        
        # --- EINHEITLICHES BUTTON-GRID (3 Zeilen x 2 Spalten) ---
        action_grid = ttk.Frame(btn_frame)
        action_grid.pack(fill="x", pady=3)
        
        # Spalten und Zeilen exakt gleich groß zwingen (uniform)
        action_grid.columnconfigure(0, weight=1, uniform="btn_col")
        action_grid.columnconfigure(1, weight=1, uniform="btn_col")
        action_grid.rowconfigure(0, weight=1, uniform="btn_row")
        action_grid.rowconfigure(1, weight=1, uniform="btn_row")
        action_grid.rowconfigure(2, weight=1, uniform="btn_row")
        
        # Zeile 1: Hauptaktionen
        ttk.Button(action_grid, text="Neu Hinzufügen", command=self.add_filament, style="Accent.TButton").grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=2)
        ttk.Button(action_grid, text="Änderungen Speichern", command=self.update_filament).grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=2)
        
        # Zeile 2: Tools
        ttk.Button(action_grid, text="🔄 Quick-Swap", command=self.quick_swap_dialog).grid(row=1, column=0, sticky="nsew", padx=(0, 2), pady=2)
        ttk.Button(action_grid, text="📜 Logbuch", command=self.show_spool_history).grid(row=1, column=1, sticky="nsew", padx=(2, 0), pady=2)
        
        # Zeile 3: Workflow
        ttk.Button(action_grid, text="🐑 Klonen", command=self.clone_filament).grid(row=2, column=0, sticky="nsew", padx=(0, 2), pady=2)
        ttk.Button(action_grid, text="📦 Ins Lager", command=self.send_to_storage).grid(row=2, column=1, sticky="nsew", padx=(2, 0), pady=2)
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=4)
        
        # --- 4. Ansichten & Verwaltung ---
        ttk.Button(btn_frame, text="📦 Regal & AMS Ansicht", command=lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools, self)).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🧵 Leerspulen verwalten", command=lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown)).pack(fill="x", pady=2)
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=4)
        
        # --- 5. Drucker & System ---
        if self.settings.get("use_bambu", False):
            ttk.Button(btn_frame, text="🤖 Bambu AMS Live-Sync", command=self.run_ams_sync, style="Accent.TButton").pack(fill="x", pady=2)
        
        ttk.Button(btn_frame, text="Felder leeren", command=self.clear_inputs).pack(fill="x", pady=3)
        
        # --- 6. Löschen (Ganz unten, farblich abgesetzt) ---
        ttk.Button(btn_frame, text="Löschen", command=self.delete_filament, style="Delete.TButton").pack(fill="x", pady=(10, 3))

        def _on_canvas_mousewheel(e):
            # Normales Scrollen für das Canvas
            self.form_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            
        # 1. Bindung an das Canvas selbst
        # (Manchmal nötig, um globale Bindungen zu überschreiben)
        self.form_canvas.bind("<MouseWheel>", _on_canvas_mousewheel)
        self.scrollable_form_frame.bind("<MouseWheel>", _on_canvas_mousewheel)
        
        # 2. Rekursive Bindung an ALLE Kinder-Widgets im Formular-Panel
        # (Entries, Comboboxes etc. dürfen das Event nicht blockieren!)
        def _bind_recursively(widget, binding, command):
            try:
                # add="+" ist wichtig, um bestehende Bindungen (z.B. Combobox-Listen) nicht zu killen
                widget.bind(binding, command, add="+")
            except Exception: 
                pass # Falls ein Widget das nicht unterstützt
            for child in widget.winfo_children():
                _bind_recursively(child, binding, command)
                
        # Bindung auf das Haupt-Panel anwenden
        _bind_recursively(self.scrollable_form_frame, "<MouseWheel>", _on_canvas_mousewheel)
        _bind_recursively(tab_basis, "<MouseWheel>", _on_canvas_mousewheel)
        _bind_recursively(tab_erp, "<MouseWheel>", _on_canvas_mousewheel)

        # --- NEU: Flexibles PanedWindow für Tabelle und Side-Panel ---
        self.main_paned = ttk.PanedWindow(main_frame, orient="horizontal")
        self.main_paned.pack(side="left", fill="both", expand=True)
        
        table_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(table_frame, weight=1) # Die Tabelle darf sich ausdehnen
        
        # --- NEU: DAS SIDE-PANEL ---
        self.side_panel = ttk.Frame(self.main_paned, width=380, relief="solid", borderwidth=1)
        self.side_panel.pack_propagate(False) 
        self.side_panel_open = False
        self.current_panel_title = ""
        
        self.tree = ttk.Treeview(table_frame, columns=("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"), show="tree headings")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview); self.tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y"); self.tree.pack(fill="both", expand=True)
        self.tree.column("#0", width=40, anchor="center", stretch=False)
        for col, text in zip(("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"), ["ID", "Marke", "Material", "Farbe", "Effekt / Typ", "Rest(g)", "Flow", "Ort", "Status"]): self.tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(c, False))
        self.tree.column("id", width=40, anchor="center"); self.tree.column("brand", width=120); self.tree.column("material", width=60, anchor="center"); self.tree.column("weight", width=60, anchor="center"); self.tree.column("flow", width=50, anchor="center"); self.tree.column("status", width=90, anchor="center"); self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.update_locations_dropdown(); self.update_spool_dropdown(); self.update_filter_dropdowns(); self.clear_inputs(); self.refresh_table()
        
        # Initialisiert die neuen Rechtsklick-Menüs
        self.setup_context_menus()
        # Bindet den Rechtsklick (Button-3 unter Windows, Button-2/Control-Klick unter macOS)
        self.tree.bind("<Button-3>", self.on_tree_right_click)
        
        def _on_mousewheel(e):
            self.tree.yview_scroll(int(-1*(e.delta/120)), "units")
        self.tree.bind("<MouseWheel>", _on_mousewheel)

        def run_update_check():
            res = check_for_updates(GITHUB_REPO, APP_VERSION)
            if res:
                latest, url = res
                self.root.after(0, lambda: self.show_update_prompt(latest, url))
        threading.Thread(target=run_update_check, daemon=True).start()

        # --- NEU: Bambu Auto-Sync Monitor starten ---
        if self.settings.get("use_bambu", False):
            try:
                from core.bambu_sync import BambuBackgroundMonitor
                ip = self.settings.get("bambu_ip", "")
                code = self.settings.get("bambu_access", "")
                serial = self.settings.get("bambu_serial", "")
                
                if ip and code and serial:
                    self.bambu_monitor = BambuBackgroundMonitor(
                        ip, code, serial, 
                        on_finish_callback=self.on_bambu_print_finish
                    )
                    self.bambu_monitor.start()
            except Exception as e:
                print(f"Bambu Monitor konnte nicht gestartet werden: {e}")

        self.apply_theme()
        
        start_mobile_server(self)
        self.broadcast_mqtt()

    def toggle_side_panel(self, title=None, build_func=None, force_close=False):
        # 1. Wenn explizit geschlossen wird (X-Button) ODER derselbe Tab geklickt wird -> Schließen!
        if force_close or (self.side_panel_open and self.current_panel_title == title):
            self.main_paned.forget(self.side_panel) # Aus dem PanedWindow entfernen
            self.side_panel_open = False
            return

        # 2. Panel öffnen und GANZ RECHTS anheften (verschiebbar!)
        self.main_paned.add(self.side_panel, weight=0)
        self.side_panel_open = True
        
        # Pylance Fix: Fallback auf leeren String, falls title 'None' ist
        self.current_panel_title = title or "" 
        
        # Altes Zeug im Panel löschen
        for widget in self.side_panel.winfo_children():
            widget.destroy()
            
        # Header mit Schließen-Button
        header = ttk.Frame(self.side_panel)
        header.pack(fill="x", pady=10, padx=10)
        ttk.Label(header, text=self.current_panel_title, font=("Segoe UI", 12, "bold")).pack(side="left")
        
        # FIX: Der Schließen-Button zwingt das Panel jetzt zum Schließen!
        ttk.Button(header, text="❌", width=3, command=lambda: self.toggle_side_panel(force_close=True)).pack(side="right")
        ttk.Separator(self.side_panel, orient="horizontal").pack(fill="x")
        
        # Content Bereich
        content = ttk.Frame(self.side_panel, padding=10)
        content.pack(fill="both", expand=True)
        
        if build_func:
            build_func(content)

    def build_quick_cost_calculator(self, parent):
        fields = [
            ("Materialpreis (€/kg):", "price", "25.00"),
            ("Verbrauch (Gramm):", "weight", "100"),
            ("Druckzeit (Stunden):", "time", "5")
        ]
        entries = {}
        for label, key, default in fields:
            ttk.Label(parent, text=label).pack(anchor="w")
            ent = ttk.Entry(parent)
            ent.insert(0, default)
            ent.pack(fill="x", pady=(0, 10))
            entries[key] = ent

        lbl_res = ttk.Label(parent, text="", font=("Segoe UI", 11, "bold"), foreground="#0078d7", justify="center")
        lbl_res.pack(pady=20)

        def calc():
            try:
                p = float(entries["price"].get().replace(",", "."))
                w = float(entries["weight"].get().replace(",", "."))
                t = float(entries["time"].get().replace(",", "."))
                mat = w * (p / 1000.0)
                kwh = float(self.settings.get("kwh_price", 0.30))
                watt = int(self.settings.get("printer_watts", 150))
                elec = t * (watt / 1000.0) * kwh
                wear = t * float(self.settings.get("wear_per_hour", 0.20))
                total = mat + elec + wear
                margin = int(self.settings.get("profit_margin", 0))
                sell = total * (1 + (margin/100.0))
                
                res = f"Material: {mat:.2f} € | Strom: {elec:.2f} €\nVerschleiß: {wear:.2f} €\n"
                res += f"--------------------------\nKOSTEN: {total:.2f} €\n"
                if margin > 0: res += f"VK (+{margin}%): {sell:.2f} €"
                lbl_res.config(text=res)
            except:
                lbl_res.config(text="⚠️ Bitte Zahlen eingeben!")

        ttk.Button(parent, text="Berechnen", command=calc, style="Accent.TButton").pack(fill="x", pady=10)

    def update_color_preview(self, event=None):
        cols = get_colors_from_text(self.combo_color.get())
        img = create_color_icon(cols, (30, 20), "#888888")
        self.lbl_color_preview.config(image=img); setattr(self.lbl_color_preview, 'image', img) # type: ignore

    def auto_match_spool(self, event=None):
        # Wenn es ein Refill ist, schalten wir die Automatik ab!
        if getattr(self, 'var_is_refill', None) and self.var_is_refill.get(): 
            return
            
        brand = self.entry_brand.get().strip().lower()
        if not brand: return
        
        # Suche nach einer Spule, die ähnlich heißt wie die Marke
        for val in self.combo_spool['values']:
            if val == "-": continue
            spool_name = val.split(" - ", 1)[1].lower()
            
            # Treffer! (z.B. "Bambu" steckt in "Bambu Lab Reusable Spool")
            if brand in spool_name or spool_name in brand:
                if self.combo_spool.get() != val:
                    self.combo_spool.set(val)
                    self.on_spool_changed() # Netto sofort neu berechnen!
                break

    def show_tip(self, event, text):
        self.tip = tk.Toplevel(self.root); self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
        tk.Label(self.tip, text=text, bg="#FFFFE0", relief="solid", borderwidth=1, padx=5, pady=2).pack()

    def hide_tip(self, event=None):
        if hasattr(self, 'tip') and self.tip: self.tip.destroy()

    def open_paypal(self):
        webbrowser.open("https://paypal.me/florianfranck")

    def show_howto(self):
        """Öffnet das vollständige VibeSpool Handbuch mit detaillierten Kapiteln."""
        win = tk.Toplevel(self.root)
        win.title("📘 VibeSpool Handbuch & Hilfe")
        win.geometry("950x750")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        from core.utils import center_window
        center_window(win, self.root)

        header = ttk.Frame(win, padding=15)
        header.pack(fill="x")
        ttk.Label(header, text="VibeSpool Handbuch", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Label(header, text=f"Version {APP_VERSION}", foreground="gray").pack(side="right", pady=5)
        
        tabs = ttk.Notebook(win)
        tabs.pack(fill="both", expand=True, padx=10, pady=5)

        def create_tab(title, content):
            frame = ttk.Frame(tabs)
            tabs.add(frame, text=title)
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side="right", fill="y")
            
            text_box = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, font=("Segoe UI", 10), 
                              padx=15, pady=15, bg=self.root.cget('bg'), bd=0)
            text_box.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=text_box.yview)
            
            text_box.tag_configure("h1", font=("Segoe UI", 12, "bold"), foreground="#0078D7", spacing1=15, spacing3=5)
            text_box.tag_configure("bold", font=("Segoe UI", 10, "bold"))
            text_box.tag_configure("bullet", lmargin1=20, lmargin2=35, spacing1=3)
            
            for line in content.split('\n'):
                if line.startswith('## '):
                    text_box.insert("end", line[3:] + "\n", "h1")
                elif line.startswith('• '):
                    if ":" in line:
                        parts = line.split(":", 1)
                        text_box.insert("end", "• " + parts[0].strip(":").replace("• ","") + ":", "bold")
                        text_box.insert("end", parts[1] + "\n", "bullet")
                    else:
                        text_box.insert("end", line + "\n", "bullet")
                else:
                    text_box.insert("end", line + "\n")
            
            text_box.config(state="disabled")

        # --- Inhalte definieren ---
        
        tab1_content = """## Grundlagen & Spulen anlegen
• Spulen hinzufügen: Klicke links auf 'Neu', fülle die Felder aus und klicke auf 'Neu Hinzufügen'. Wenn du das ID-Feld leer lässt, vergibt VibeSpool automatisch die nächste freie Nummer.
• Farb-Automatik: Du kannst Hex-Codes (z.B. #FF0000) eintippen. VibeSpool übersetzt diese beim Speichern automatisch in den passenden Namen und zeigt dir ein Farb-Icon. Bei Multi-Color-Filamenten trenne die Farben einfach mit einem Schrägstrich (Rot / Blau).
• Listen anpassen: Fehlt dir ein Hersteller oder ein Material im Dropdown-Menü? Klicke oben rechts auf 'Optionen' -> 'Listen-Verwaltung' und füge deine eigenen Einträge hinzu. VibeSpool lernt aber auch automatisch mit, wenn du einfach ein neues Wort in das Feld eintippst!
• Spule klonen: Du hast 5 gleiche Spulen gekauft? Wähle eine aus, klicke auf 'Klonen' und VibeSpool erstellt ein exaktes Duplikat mit einer neuen ID.

## Tabellen & Ansicht
• Spalten konfigurieren: Mach einen Rechtsklick auf den Tabellenkopf (wo 'Marke', 'Material' etc. steht). Dort kannst du Spalten ein- und ausblenden.
• Sortieren: Klicke auf eine Spaltenüberschrift, um danach zu sortieren. AMS-Spulen werden dabei immer priorisiert ganz oben angezeigt!
• Rechtsklick-Menü: Ein Rechtsklick auf eine Spule in der Tabelle öffnet ein Schnellmenü für die wichtigsten Aktionen (Löschen, Logbuch, Quick-Swap, Shop-Link)."""

        tab2_content = """## Lager & Regale
• Regalplaner: Gehe in die Optionen -> 'Lager-Layout planen'. Dort legst du fest, wie viele Regale du hast und wie viele Spalten/Reihen sie besitzen.
• Fächer benennen: Ebenfalls in den Optionen kannst du Regalfächern eigene Namen geben (z.B. 'Kiste A' statt 'Fach 1').
• Doppeltiefe Regale: Aktivierst du diese Option, bekommt jeder Slot einen vorderen (V) und einen hinteren (H) Platz. Perfekt für tiefe Schränke!
• Zusatz-Orte: Trag in den Optionen Orte wie 'Trockenbox' ein. Diese erscheinen dann endlos als normaler Lagerort im Dropdown.

## AMS & Drucker-Verwaltung
• Quick-Swap (Tauschen): Du willst drucken? Klicke auf 'Swap'. Wähle den AMS-Slot aus. VibeSpool tauscht die Spule aus dem Regal magisch mit der Spule im AMS. Du weißt immer, wo die alte Spule gelandet ist!
• Bambu AMS Live-Sync: Wenn du in den Optionen deine Bambu-IP und den Access-Code hinterlegst, kannst du links auf 'AMS' klicken. VibeSpool liest dein echtes Bambu-AMS aus und fragt dich, welche VibeSpool-Rollen du gerade eingelegt hast. Kollisionen werden dabei verhindert!
• Ins Lager: Der Button 'Ins Lager' wirft eine Spule sofort aus dem AMS/Drucker und packt sie auf den großen, endlosen Haufen 'LAGER'."""

        tab3_content = """## Die Schlaue Waage (Netto-Gewicht)
• Ziel: Präzise wissen, wie viel Filament noch auf der Rolle ist, ohne selbst rechnen zu müssen.
• Leerspulen anlegen: Klicke links auf 'Spulen' (Das Faden-Symbol). Lege dort an, wie viel eine leere Plastik-/Papprolle der jeweiligen Hersteller wiegt (z.B. Bambu Lab Leer = 250g).
• So funktioniert's: Wähle im Hauptfenster aus dem Dropdown die Leerspule deines Herstellers. Stell die Spule auf deine Küchenwaage. Trage das ermittelte Gewicht bei 'Gewicht auf Waage (Brutto)' ein. VibeSpool zieht das Leergewicht ab und zeigt dir sofort das exakte 'Netto (Rest)' an!
• Voll-Button: Klickst du auf 'Voll', rechnet VibeSpool: Leerspule + Original-Kapazität (z.B. 1000g) und trägt das perfekte Bruttogewicht für eine brandneue Spule ein.

## Verbrauch protokollieren
• Manueller Druck: Trage einen Wert in das kleine Feld 'Slicer-Verbrauch' ein und klicke auf '➕ Druck protokollieren'. Es öffnet sich ein Dialog, in dem du Name und Druckzeit eingibst. VibeSpool berechnet die exakten Kosten.
• Korrektur: Du hast Ausschuss produziert oder Filament weggeschnitten? Trag die Grammzahl ein und klicke auf '➕ Korrektur'. Dies zieht das Gewicht ab, ohne eine Finanz-Kalkulation auszulösen."""

        tab4_content = """## Finanz-Dashboard & Kosten (Das Cost Center)
• Echte Gewerbe-Kalkulation: Gehe in die Optionen zum 'Druckkosten-Rechner'. Trag deinen Strompreis, Drucker-Watt, Maschinenverschleiß (pro Stunde) und deine gewünschte Gewinnmarge ein. 
• Das Dashboard: Klicke links auf 'Finanzen'. Hier siehst du deinen Lagerwert, ein 7-Tage-Verbrauchsdiagramm und unten die 'Globale Druck-Historie'.
• Globale Historie: Dies ist dein Kassenbuch! Es zeigt alle Drucke über alle Spulen hinweg an, inklusive der ausgerechneten Kosten und deines Verkaufspreises.
• Quick-Cost Kalkulator: Klicke links im Menü auf das Taschenrechner-Symbol (🧮). Damit kannst du schnell ein Preisangebot für einen Kunden berechnen, ohne dass du dafür eine echte Spule aus dem Lager belasten musst.

## Logbuch & Retro-Fit (Nachträgliche Korrektur)
• Spulen-Logbuch: Jede Spule führt ihr eigenes Logbuch. Klicke auf 'Logbuch', um zu sehen, wann was gedruckt wurde.
• Einträge bearbeiten (Auto-Heal): Du hast dich vertippt? Doppelklicke im Finanz-Dashboard unten in der Historie auf einen Eintrag. Ändere die Grammzahl. VibeSpool korrigiert magisch das Gewicht der Spule UND repariert dein 7-Tage-Balkendiagramm automatisch (Auto-Heal)!
• Retro-Fit Kalkulator: Bei sehr alten Drucken fehlen vielleicht Kosten. Doppelklicke den Eintrag und klicke auf die Buttons '🧮 Mat.' und '🧮 Marge'. VibeSpool rechnet die Materialkosten und den VK-Preis für die Vergangenheit auf die Sekunde genau nach!"""

        tab5_content = """## Bambu Cloud & Smart-Match
• Einrichtung: Trage in den Optionen ('Drucker') deine Bambu Lab E-Mail und dein Passwort ein.
• Cloud-Sync: Klicke links auf 'Cloud'. VibeSpool holt sich deine letzten erfolgreichen Drucke direkt von den Bambu Servern.
• Smart-Match Abzug: Klicke in der Liste doppelt auf einen Druck oder auf 'Abziehen'. VibeSpool erkennt durch 'Smart-Match', auf welchem AMS-Slot die Farbe lag und wählt die passende VibeSpool-Rolle automatisch aus! Bestätigen, fertig.
• Multi-Color Drucke: Hat dein Druck 4 Farben benutzt? VibeSpool erkennt das und teilt die abgebuchten Gramm exakt auf die 4 beteiligten Spulen auf! Auch Strom und Verschleiß werden prozentual perfekt berechnet.
• Filter & Ignorieren: Drucke, die du manuell abgezogen hast oder nicht tracken willst, kannst du 'Ignorieren'. Setze oben den Haken bei 'Erledigte ausblenden', um eine cleane ToDo-Liste zu haben."""

        tab6_content = """## Handy-Scanner & QR-Codes
• Der lokale Server: VibeSpool hat einen unsichtbaren Webserver eingebaut. Klicke oben auf '📱 Handy'. Scanne den dortigen QR-Code mit deinem Smartphone.
• Mobile Bedienung: Du hast VibeSpool nun als Web-App auf dem Handy. Du kannst im WLAN durch den Raum laufen, QR-Codes auf Spulen scannen und direkt am Handy Gewichte abziehen oder Spulen umbuchen. Das Programm am PC reagiert live auf deine Handy-Eingaben!
• Etiketten & PDF Druck: Klicke links auf 'Label'. Wähle eine Spule. Du kannst das fertige Etikett als Bild speichern, oder auf 'ALLE als PDF exportieren' klicken. Der PDF-Modus druckt hunderte Etiketten perfekt ausgerichtet auf DIN A4 Bögen oder schickt sie an deinen Endlos-Labeldrucker!

## Hersteller-Barcodes anlernen
• Das Prinzip: Viele Spulen haben vom Hersteller bereits Barcodes auf der Packung. Warum eigene drucken?
• So geht's: Lege eine neue Spule am PC an (oder bearbeite eine). Nimm dein Handy (Mobile Scanner) und gehe auf den Tab 'Neu anlegen'. Scanne den Original-Barcode der Schachtel. VibeSpool schießt diesen Code live in das Feld am PC. 
• Der Vorteil: Wenn du diese leere Spule in Zukunft scannst, erkennt VibeSpool sie sofort wieder!"""

        tab7_content = """## System, Backup & Smart Home
• Backup & Restore: Klicke oben rechts auf '💾 Backup'. VibeSpool packt deine gesamte Datenbank, alle Einstellungen und das Logbuch in eine einzige, sichere ZIP-Datei. Genau dort kannst du sie bei einem PC-Wechsel auch wieder importieren.
• CSV Import: Du wechselst von Excel zu VibeSpool? Klicke auf 'CSV Import'. VibeSpool ist extrem schlau und sucht in deiner Excel-Tabelle selbstständig nach Spalten, die nach Marke, Farbe oder Material klingen.
• Smart Home (MQTT / Home Assistant): Aktiviere MQTT in den Optionen. VibeSpool funkt bei jeder Änderung (oder spätestens wenn es online ist via Offline-Buffer) live an dein Smart Home: Wie viele Spulen hast du? Welche sind fast leer? Was steckt gerade im AMS?
• Hintergrund-Modus: Wenn du auf das 'X' zum Schließen klickst, fragt dich VibeSpool, ob es sich in die Windows-Taskleiste minimieren soll. Von dort kann es blitzschnell wieder aufgerufen werden!"""

        # --- Tabs erstellen ---
        create_tab("🏠 1. Grundlagen", tab1_content)
        create_tab("📦 2. Lager & AMS", tab2_content)
        create_tab("⚖️ 3. Verbrauch & Waage", tab3_content)
        create_tab("💶 4. Finanzen & Cost Center", tab4_content)
        create_tab("☁️ 5. Cloud & Smart-Match", tab5_content)
        create_tab("📱 6. Scanner & Etiketten", tab6_content)
        create_tab("⚙️ 7. System & Backup", tab7_content)

        ttk.Button(win, text="Alles klar, ich bin bereit!", command=win.destroy, style="Accent.TButton").pack(pady=15)
    
    def show_update_prompt(self, latest, url):
        upd = tk.Toplevel(self.root); upd.title("VibeSpool Update"); upd.geometry("400x150"); upd.configure(bg=self.root.cget('bg')); upd.attributes('-topmost', True); center_window(upd, self.root)
        ttk.Label(upd, text=f"Version {latest} ist verfügbar!", font=("Segoe UI", 12, "bold")).pack(pady=15)
        btn_frm = ttk.Frame(upd); btn_frm.pack(pady=10)
        ttk.Button(btn_frm, text="Laden", command=lambda: [webbrowser.open(url), upd.destroy()]).pack(side="left", padx=5); ttk.Button(btn_frm, text="Später", command=upd.destroy).pack(side="left", padx=5)

    def on_closing(self):
        """Fragt den Nutzer, ob das Programm ins Tray minimiert oder beendet werden soll."""
        dialog = tk.Toplevel(self.root)
        dialog.title("VibeSpool beenden?")
        dialog.geometry("450x180")
        dialog.attributes('-topmost', True)
        dialog.resizable(False, False)
        dialog.configure(bg=self.root.cget('bg'))
        from core.utils import center_window
        center_window(dialog, self.root)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

        ttk.Label(dialog, text="Was möchtest du tun?", font=("Segoe UI", 12, "bold")).pack(pady=(20, 10))
        ttk.Label(dialog, text="Soll VibeSpool im Hintergrund weiterlaufen?", font=("Segoe UI", 10)).pack(pady=(0, 15))

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=20)

        def do_minimize():
            dialog.destroy()
            self.root.withdraw() # Versteckt das Hauptfenster
            
            # NEU: Das Tray-Icon tatsächlich erstellen und im Hintergrund starten!
            import pystray
            from pystray import MenuItem as item
            import threading
            
            menu = (item('Öffnen', self.show_window), item('Beenden', self.quit_app))
            self.tray_icon = pystray.Icon("VibeSpool", create_tray_icon(), "VibeSpool", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

        def do_exit():
            dialog.destroy()
            self.root.destroy() # Beendet VibeSpool komplett
            import sys; sys.exit(0)

        # Buttons
        ttk.Button(btn_frame, text="⏬ In die Taskleiste", command=do_minimize, style="Accent.TButton").pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_frame, text="❌ Komplett beenden", command=do_exit).pack(side="right", expand=True, fill="x", padx=5)

    def show_window(self, icon, item):
        # Wird aufgerufen, wenn man im Tray auf "Öffnen" klickt
        if self.tray_icon: self.tray_icon.stop()
        self.root.after(0, self.root.deiconify) # Fenster wieder einblenden

    def show_custom_toast(self, title, message):
        """Erstellt eine elegante, dunkle Benachrichtigung unten rechts im Bildschirm."""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True) # Keine Windows-Rahmen
        toast.attributes('-topmost', True) # Immer im Vordergrund
        toast.configure(bg="#2b2b2b", highlightbackground="#0078d7", highlightthickness=2)
        
        # Titel
        lbl_title = tk.Label(toast, text=title, font=("Segoe UI", 12, "bold"), fg="#0078d7", bg="#2b2b2b")
        lbl_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        # Nachricht
        lbl_msg = tk.Label(toast, text=message, font=("Segoe UI", 10), fg="white", bg="#2b2b2b")
        lbl_msg.pack(padx=20, pady=(0, 15), anchor="w")
        
        # Größe und Position berechnen
        toast.update_idletasks()
        w = toast.winfo_width()
        h = toast.winfo_height()
        sw = toast.winfo_screenwidth()
        sh = toast.winfo_screenheight()
        
        # Position: Rechts unten (knapp über der Windows-Taskleiste)
        x = sw - w - 20
        y = sh - h - 60
        toast.geometry(f"{w}x{h}+{x}+{y}")
        
        # Der Toast zerstört sich nach 6 Sekunden von selbst
        self.root.after(6000, toast.destroy)

    def quit_app(self, icon, item):
        # Das ECHTE Beenden der App
        if self.tray_icon: self.tray_icon.stop()
        
        # Hintergrund-Monitor stoppen
        if hasattr(self, 'bambu_monitor'):
            try: self.bambu_monitor.stop()
            except: pass
            
        # Einstellungen speichern und App zerstören
        try:
            self.data_manager.save_settings(self.settings)
        except: pass
        
        self.root.after(0, self.root.destroy)
    
    def apply_theme(self):
        theme = self.settings.get("theme", "dark"); c = THEMES[theme]; self.root.configure(bg=c["bg"]); s = self.style
        # --- NATIVE WINDOWS TITELLEISTE (DARK MODE) ---
        try:
            import ctypes
            # Holt die interne Windows-Fenster-ID (HWND) von Tkinter
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1 if theme == "dark" else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass # Wenn es ein Mac oder altes Windows ist, passiert einfach nichts
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
        s.configure("TScrollbar", troughcolor=c["bg"], background=c["head_bg"], bordercolor=c["bg"], arrowcolor=c["fg"])
        s.map("TScrollbar", background=[("active", COLOR_ACCENT)])
        
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
        
        # NEU: Spulen alphabetisch (case-insensitive) sortieren!
        sorted_spools = sorted(self.spools, key=lambda s: s['name'].lower())
        
        # Format "ID - Name" beibehalten, aber aus der sortierten Liste generieren
        values = ["-"] + [f"{s['id']} - {s['name']}" for s in sorted_spools]
        
        curr = self.combo_spool.get()
        self.combo_spool['values'] = values
        
        if curr not in values: 
            self.combo_spool.current(0)
    def get_selected_spool_id(self):
        try: return -1 if self.combo_spool.get() == "-" else int(self.combo_spool.get().split(" - ")[0])
        except: return -1
    def on_spool_changed(self, event=None):
        new_spool_id = self.get_selected_spool_id()
        if new_spool_id != -1: self.var_custom_empty.set("")
        old_spool_id = getattr(self, 'last_selected_spool_id', -1)
        
        # Gesetz der Massenerhaltung: Brutto anpassen, Netto bleibt gleich!
        if new_spool_id != old_spool_id:
            old_spool = next((s for s in self.spools if s['id'] == old_spool_id), None)
            new_spool = next((s for s in self.spools if s['id'] == new_spool_id), None)
            old_w = old_spool['weight'] if old_spool else 0
            new_w = new_spool['weight'] if new_spool else 0
            
            try:
                gross_str = self.var_gross.get().strip().replace(',', '.')
                if gross_str:
                    new_gross = float(gross_str) - old_w + new_w
                    self.var_gross.set(f"{new_gross:g}")
            except: pass
            self.last_selected_spool_id = new_spool_id
            
        self.update_net_weight_display()

    def set_gross_to_full(self):
        try:
            cap = float(self.var_capacity.get().strip() or 1000)
            spool_id = self.get_selected_spool_id()
            spool = next((s for s in self.spools if s['id'] == spool_id), None)
            sp_w = spool['weight'] if spool else 0
            self.var_gross.set(f"{cap + sp_w:g}")
        except: pass
    
    def deduct_slicer(self):
        """Ersetzt das einfache Abziehen durch den smarten Manuellen Druck-Dialog."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warnung", "Bitte wähle zuerst eine Spule aus der Tabelle aus!")
            return
            
        item_id = sel[0]
        spool_data = next((s for s in self.inventory if str(s['id']) == str(item_id)), None)
        
        if not spool_data: return

        # FIX: Hier steht jetzt das 'sell_str' mit in der Klammer!
        def process_deduction(weight, print_name, cost_str, sell_str):
            # Gewicht abziehen
            old_gross = float(spool_data.get('weight_gross', 0))
            new_gross = max(0, old_gross - weight)
            spool_data['weight_gross'] = round(new_gross, 1)
            
            # Logbuch-Eintrag erstellen
            if "history" not in spool_data: spool_data["history"] = []
            spool_data["history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": f"Manuell: {print_name}",
                "change": f"-{weight}g",
                "cost": cost_str,
                "sell_price": sell_str # Hier wird er jetzt fehlerfrei gespeichert!
            })
            
            # Globales Logbuch aktualisieren
            self.log_consumption(weight)
            
            # UI aktualisieren
            self.var_gross.set(f"{new_gross:g}")
            self.update_net_weight_display()
            self.entry_slicer.delete(0, tk.END)
            
            # Speichern & Tabelle aktualisieren
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.show_custom_toast("💰 Druck gespeichert", f"{weight}g abgezogen.\nGesamtkosten: {cost_str}")

        # Den neuen Dialog öffnen
        dialog = ManualPrintDialog(self.root, spool_data, self.settings, process_deduction)
        
        # UX Bonus: Wert aus dem kleinen Feld übernehmen
        pre_filled = self.entry_slicer.get().strip()
        if pre_filled:
            dialog.ent_weight.insert(0, pre_filled)
    
    def add_slicer(self):
        try:
            added = float(self.entry_slicer.get().strip().replace(',', '.'))
            curr = float(self.var_gross.get().strip().replace(',', '.') or 0)
            if added > 0:
                new_gross = curr + added
                self.var_gross.set(f"{new_gross:g}")
                self.entry_slicer.delete(0, tk.END)
                # DAS WICHTIGSTE: Wir übergeben den Wert als MINUS an den Logger!
                self.log_consumption(-added) 
        except ValueError:
            pass # Ignoriert Klicks, wenn Buchstaben drinstehen
    
    def update_net_weight_display(self, event=None):
        try:
            gross_str = self.var_gross.get().strip().replace(',', '.')
            if not gross_str: self.lbl_net_weight.config(text="Netto: 0 g | Wert: -"); return
            
            spool_id = self.get_selected_spool_id()
            custom_empty = self.var_custom_empty.get().strip() if spool_id == -1 else None
            
            net = calculate_net_weight(gross_str, spool_id, self.spools, custom_empty)
            
            price_str = self.var_price.get().strip().replace(',', '.'); cap_str, val_str = self.var_capacity.get().strip(), ""
            if price_str and cap_str:
                try:
                    p, c = float(price_str), float(cap_str)
                    if c > 0: val_str = f" | Wert: {(net / c) * p:.2f} €"
                except: pass
            self.lbl_net_weight.config(text=f"Netto: {int(net)} g{val_str}")
        except: self.lbl_net_weight.config(text="Netto: 0 g | Wert: -")

    def open_settings(self, start_tab=0):
        def on_save(s): 
            self.settings = s
            self.data_manager.save_settings(s)
            self.combo_material['values'] = s.get("materials", MATERIALS)
            self.combo_color['values'] = s.get("colors", COMMON_COLORS)
            self.combo_subtype['values'] = s.get("subtypes", SUBTYPES)
            self.entry_brand['values'] = sorted(s.get("brands", []), key=str.lower)
            self.update_locations_dropdown()
            self.update_slot_dropdown()
            self.update_filter_dropdowns()
        SettingsDialog(self.root, self.data_manager, on_save, start_tab, self)
    def manual_update_check(self):
        latest, url = check_for_updates(GITHUB_REPO, APP_VERSION) or (None, None)
        if latest: self.show_update_prompt(latest, url)
        else: messagebox.showinfo("Aktuell", f"Du nutzt bereits die aktuellste Version (v{APP_VERSION}).")
    
    def update_slot_dropdown(self, event=None):
        loc = self.combo_type.get()
        self.last_selected_type = loc
        new_values = ["-"] # Standard-Wert für endlose Orte wie LAGER oder VERBRAUCHT
        
        if loc.startswith("AMS"): 
            new_values = ["1", "2", "3", "4"]
        else:
            # NEU: Lese die Namen für das exakt gewählte Regal aus!
            shelf_names_all = self.settings.get("shelf_names_v2", {})
            shelf_names = shelf_names_all.get(loc, {})
            
            lbl_r = self.settings.get('label_row', 'Fach')
            lbl_c = self.settings.get('label_col', 'Slot')
            for s in parse_shelves_string(self.settings.get("shelves", "REGAL|4|8")):
                if s['name'] == loc: 
                    r, c, log = s['rows'], s['cols'], self.settings.get("logistics_order")
                    slots = []
                    is_double = self.settings.get("double_depth", False)
                    for rw in (range(r, 0, -1) if log else range(1, r + 1)):
                        row_name = shelf_names.get(str(rw), f"{lbl_r} {rw}")
                        for cl in range(1, c + 1):
                            col_name = shelf_names.get(f"col_{cl}", f"{lbl_c} {cl}")
                            if is_double:
                                slots.append(f"{row_name} - {col_name} (H)")
                                slots.append(f"{row_name} - {col_name} (V)")
                            else:
                                slots.append(f"{row_name} - {col_name}")
                    new_values = slots
                    break

        # 1. Die neue Liste im Hintergrund zuweisen
        self.combo_loc_id['values'] = new_values
        
        # 2. Steht noch Blödsinn vom alten Lagerort im Feld? Dann automatisch korrigieren!
        current_val = self.combo_loc_id.get()
        if current_val not in new_values:
            self.combo_loc_id.set(new_values[0])
            
        # --- NEU: Dynamisches Wording für das Label ---
        # Sucht das Widget, das vor der Combobox gepackt wurde (das Label)
        for child in self.combo_loc_id.master.winfo_children():
            if isinstance(child, ttk.Label) and ("Slot" in child.cget("text") or "Detail" in child.cget("text")):
                if loc in ["LAGER", "VERBRAUCHT"] or loc in self.settings.get("custom_locs", ""):
                    child.config(text="Detail / Info:")
                else:
                    child.config(text=f"{self.settings.get('label_col', 'Slot')} / Nr.:")
    
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
                self.log_consumption(usage_g)
                messagebox.showinfo("Erfolg", f"Gewicht aktualisiert! Neues Brutto: {new_gross:.1f}g\n\nVergiss nicht, die Änderungen zu speichern!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnungsfehler: {e}")

    def _sort_inventory(self):
        col = getattr(self, 'current_sort_col', 'id')
        reverse = getattr(self, 'current_sort_reverse', False)
        
        def get_sort_value(i):
            if col == "location":
                t = str(i.get('type', '')).upper()
                # AMS lassen wir hier weg, das bekommt unten eine Sonderbehandlung!
                if t == "LAGER": prefix = "2"
                elif t == "VERBRAUCHT": prefix = "3"
                else: prefix = "1"
                return f"{prefix}_{t} {i.get('loc_id', '')}".strip()
            elif col == "weight":
                # Gewicht mit Nullen auffüllen, damit z.B. 50g nicht vor 400g steht
                try:
                    w = calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools, i.get('empty_weight'))
                    return f"{float(w):08.2f}"
                except:
                    return "00000000.00"
            elif col == "status":
                return "VERBRAUCHT" if i.get('type') == "VERBRAUCHT" else "KAUFEN" if i.get('reorder') else ""
            return str(i.get(col, ""))

        try:
            # 1. Wir spalten das Inventar! AMS-Spulen kommen in eine VIP-Liste.
            ams_list = [i for i in self.inventory if str(i.get('type', '')).upper().startswith("AMS")]
            rest_list = [i for i in self.inventory if not str(i.get('type', '')).upper().startswith("AMS")]
            
            def sort_key(i):
                return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', get_sort_value(i))]
            
            # 2. Wir sortieren beide Listen unabhängig voneinander
            ams_list.sort(key=sort_key, reverse=reverse)
            rest_list.sort(key=sort_key, reverse=reverse)
            
            # 3. Wir leeren die originale Liste und kleben sie neu zusammen: IMMER AMS ZUERST!
            # WICHTIG: Wir nutzen clear() und extend(), damit die Verbindung der Fenster nicht abreißt!
            self.inventory.clear()
            self.inventory.extend(ams_list + rest_list)
        except Exception:
            pass

    def treeview_sort_column(self, col, reverse):
        # Merkt sich für immer, welche Spalte du geklickt hast!
        self.current_sort_col = col
        self.current_sort_reverse = reverse
        
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))
        self.refresh_table()

    def update_filter_dropdowns(self):
        # Holt alle einzigartigen Materialien und Farben aus dem Inventar
        mats = sorted(list(set(i.get("material", "") for i in self.inventory if i.get("material"))))
        brands = sorted(list(set(i.get("brand", "") for i in self.inventory if i.get("brand"))))
        cols = sorted(list(set(i.get("color", "") for i in self.inventory if i.get("color"))))
        locs = self.get_dynamic_locations()
        
        # Füllt die Dropdowns in der oberen Suchleiste
        self.combo_filter_mat['values'] = ["Alle Materialien"] + mats
        self.combo_filter_color['values'] = ["Alle Farben"] + cols
        self.combo_filter_loc['values'] = ["Alle Orte"] + locs
        self.combo_filter_brand['values'] = ["Alle Hersteller"] + brands

    def reset_filters(self): 
        # Setzt alle Filter zurück auf Standard und leert die Suche
        self.filter_mat_var.set("Alle Materialien")
        self.filter_color_var.set("Alle Farben")
        self.filter_loc_var.set("Alle Orte")
        self.filter_brand_var.set("Alle Hersteller")
        self.search_var.set("")
        self.refresh_table()

    def refresh_table(self, *args):
        self.icon_cache = []
        for row in self.tree.get_children(): 
            self.tree.delete(row)
            
        # --- NEU: Sortiert die Liste vor JEDEM Zeichnen automatisch neu! ---
        self._sort_inventory()
        
        filters = {"material": self.filter_mat_var.get(), "color": self.filter_color_var.get(), "location": self.filter_loc_var.get()}
        
        # Suchbegriff in kleine Buchstaben umwandeln und in einzelne Wörter zerlegen
        search_term = self.search_var.get().lower().strip()
        search_words = search_term.split() if search_term else []
        
        # Wir übergeben "" an den DataManager, da wir die Textsuche jetzt viel mächtiger hier selbst machen!
        for i in self.data_manager.get_filtered_inventory(self.inventory, "", filters):
            # Manueller Hersteller-Filter
            if self.filter_brand_var.get() != "Alle Hersteller" and i.get('brand') != self.filter_brand_var.get():
                continue
                
            # --- DIE NEUE OMNI-SUCHE ---
            if search_words:
                # Wirft ALLE Werte (ID, Farbe, SKU, Link, Notiz etc.) in einen riesigen String
                all_values = " ".join(str(v) for v in i.values() if v is not None).lower()
                
                # Prüft, ob JEDES eingegebene Wort irgendwo in diesem Spulen-Datensatz vorkommt
                if not all(word in all_values for word in search_words):
                    continue

            loc_s = f"{i['type']} {i.get('loc_id', '')}".strip()
            stat = " | ".join(filter(None, ["VERBRAUCHT" if i['type'] == "VERBRAUCHT" else "", "KAUFEN" if i.get('reorder') else ""]))
            
            icon = create_color_icon(get_colors_from_text(i['color']))
            self.icon_cache.append(icon)
            
            net = calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools, i.get('empty_weight'))
            flow_val = i.get('flow', 'Auto' if 'bambu' in i['brand'].lower() else '-')
            
            # --- NEU: Optik-Filter für die Farbanzeige in der Liste ---
            # Schneidet alles ab, was wie ein Hex-Code in Klammern aussieht
            display_color = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', i.get('color', '')).strip()
            
            self.tree.insert("", "end", iid=str(i['id']), image=icon, values=(
                i['id'], i['brand'], i.get('material', '-'), display_color, i.get('subtype', 'Standard'), 
                f"{net}g", flow_val, loc_s, stat
            ), tags=(["alert"] if i.get('reorder') else ["grayed"] if i['type'] == "VERBRAUCHT" else []))
            
        self.tree.tag_configure("alert", background="#ffe6e6", foreground="#d9534f")
        self.tree.tag_configure("grayed", foreground="#999999")

        # --- NEU: Live-Update für ein offenes Finanz-Dashboard (Pylance-sicher!) ---
        dlg = getattr(self, 'stats_dialog', None)
        if dlg is not None and dlg.winfo_exists():
            dlg.build_ui()

        if hasattr(self, 'stats_dialog') and self.stats_dialog and self.stats_dialog.winfo_exists():
            self.stats_dialog.build_ui()
    
    def get_input_data(self):
        try:
            cap = int(self.var_capacity.get().strip() or 1000)
            spool_id = self.get_selected_spool_id()
            
            gross_str = self.var_gross.get().strip().replace(',', '.')
            
            if self.combo_type.get() == "VERBRAUCHT":
                gross_val = 0.0
                self.var_gross.set("0")
            elif not gross_str:
                sp = next((s for s in self.spools if s['id'] == spool_id), None)
                gross_val = float(cap + (sp['weight'] if sp else 0))
                self.var_gross.set(f"{gross_val:g}")
            else:
                gross_val = float(gross_str)
                if gross_val < 0:
                    gross_val = 0.0

            custom_empty = None
            if spool_id == -1:
                try: custom_empty = float(self.var_custom_empty.get().replace(',', '.'))
                except: pass
                
            return {"id": self.entry_id.get().strip() if self.entry_id.get().strip() else None, "rfid": self.entry_rfid.get().strip(), "brand": self.entry_brand.get().strip(), "material": self.combo_material.get().strip(), "color": self.combo_color.get().strip(), "subtype": self.combo_subtype.get().strip(), "type": self.combo_type.get(), "loc_id": self.combo_loc_id.get().strip(), "flow": self.entry_flow.get().strip(), "pa": self.entry_pa.get().strip(), "spool_id": spool_id, "empty_weight": custom_empty, "weight_gross": gross_val, "capacity": cap, "is_refill": self.var_is_refill.get(), "is_empty": self.combo_type.get() == "VERBRAUCHT", "reorder": self.var_reorder.get(), "supplier": self.entry_supplier.get().strip(), "sku": self.entry_sku.get().strip(), "price": self.var_price.get().strip(), "link": self.entry_link.get().strip(), "temp_n": self.entry_temp_n.get().strip(), "temp_b": self.entry_temp_b.get().strip(), "note": self.entry_note.get().strip(), "barcode": self.entry_barcode.get().strip()}
            
        except Exception as e: 
            messagebox.showwarning("Eingabe-Fehler", f"Bitte prüfe deine Eingaben!\nHast du vielleicht Text in ein Zahlenfeld getippt?\n\nFehler-Details:\n{e}")
            return None

    def check_location_collision(self, loc_type, loc_id, ignore_id=None):
        # Unendliche Lagerorte ignorieren wir (da passen beliebig viele Spulen rein)
        if loc_type in ["LAGER", "VERBRAUCHT", ""]: return None
        # Wenn kein genauer Slot gewählt wurde ("-"), gibt es auch keine Kollision
        if loc_id in ["-", ""]: return None
        
        for i in self.inventory:
            # Die eigene Spule beim Bearbeiten ignorieren (sonst blockiert sie sich selbst)
            if str(i.get('id')) == str(ignore_id): continue
            if i.get('type') == "VERBRAUCHT": continue
            
            # Treffer! Genau dieser Ort + Slot ist schon belegt.
            if i.get('type') == loc_type and str(i.get('loc_id')) == str(loc_id):
                return i # Wir geben die störende Spule zurück
        return None

    def learn_dropdown_values(self, d):
        changed = False
        
        def add_if_new(key, val, default_list):
            if not val or val == "-" or val.startswith("Alle "): return False
            current_list = self.settings.get(key, default_list)
            # Prüft, ob der Eintrag schon existiert (Groß-/Kleinschreibung ignorieren)
            if not any(x.lower() == val.lower() for x in current_list):
                current_list.append(val)
                self.settings[key] = current_list
                return True
            return False

        # 1. Prüfen, ob es neue Werte gibt
        if add_if_new("brands", d.get('brand', ''), []): changed = True
        if add_if_new("materials", d.get('material', ''), MATERIALS): changed = True
        if add_if_new("subtypes", d.get('subtype', ''), SUBTYPES): changed = True
        
        # 2. Bei Farben extrahieren wir auch Kombinationen (z.B. "Rot / Blau")
        for color_part in str(d.get('color', '')).split('/'):
            if add_if_new("colors", color_part.strip(), COMMON_COLORS): changed = True

        # 3. Wenn er was gelernt hat -> Einstellungen speichern & Dropdowns aktualisieren
        if changed:
            self.data_manager.save_settings(self.settings)
            self.combo_material['values'] = self.settings.get("materials", MATERIALS)
            self.combo_color['values'] = self.settings.get("colors", COMMON_COLORS)
            self.combo_subtype['values'] = self.settings.get("subtypes", SUBTYPES)
            self.entry_brand['values'] = sorted(self.settings.get("brands", []), key=str.lower)
            self.update_filter_dropdowns()

    def add_filament(self):
        d = self.get_input_data()
        if not d: return
        
        if d['id'] is not None:
            # Wir vergleichen jetzt als TEXT (str)
            if any(str(i['id']) == str(d['id']) for i in self.inventory):
                messagebox.showerror("Halt Stop!", f"Die ID {d['id']} existiert bereits in deinem Lager!\nBitte wähle eine andere ID oder lass das Feld leer.")
                return
        else:
            # NEU: Wir suchen die höchste ZAHL unter allen IDs, ignorieren aber Text-IDs (wie PLA-01)
            max_num = 0
            for item in self.inventory:
                if str(item['id']).isdigit():
                    max_num = max(max_num, int(item['id']))
            d['id'] = str(max_num + 1)
            
        # NEU: Kollisionsprüfung
        col = self.check_location_collision(d['type'], d['loc_id'])
        if col:
            msg = f"Der Platz {d['type']} {d['loc_id']} ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}\n\nTrotzdem dort speichern (führt zu doppelter Belegung)?"
            if not messagebox.askyesno("⚠️ Platz belegt", msg):
                return
                
        # Zwingend als String (Text) speichern
        d['id'] = str(d['id'])
        self.inventory.append(d)
        self.learn_dropdown_values(d)
        self.data_manager.save_inventory(self.inventory); self.broadcast_mqtt()
        self.refresh_table()
        self.clear_inputs()

    def update_filament(self):
        sel = self.tree.selection()
        if not sel: return
        d = self.get_input_data()
        if not d: return
        
        # NEU: Wir lesen die alte ID als Text aus!
        old_id = str(sel[0])
        new_id = str(d['id']) if d['id'] else old_id
        
        if new_id != old_id:
            if any(str(i['id']) == new_id for i in self.inventory):
                messagebox.showerror("Halt Stop!", f"Du kannst diese Spule nicht auf ID {new_id} ändern, da diese ID bereits einer anderen Spule gehört!")
                return
                
        col = self.check_location_collision(d['type'], d['loc_id'], ignore_id=old_id)
        if col:
            msg = f"Der Ziel-Platz {d['type']} {d['loc_id']} ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}\n\nTrotzdem dorthin verschieben?"
            if not messagebox.askyesno("⚠️ Platz belegt", msg):
                return
                
        d['id'] = str(new_id)

        # NEU: Auch hier als Text vergleichen
        idx = next(i for i, item in enumerate(self.inventory) if str(item['id']) == old_id)
        
        # --- FIX 2: Die Schlaue Waage ---
        old_gross = float(self.inventory[idx].get('weight_gross', 0.0))
        new_gross = float(d['weight_gross'])
        
        if new_gross < old_gross:
            diff = round(old_gross - new_gross, 1)
            # Wir fragen nur nach, wenn mehr als 1g fehlt (ignoriert kleine Waagen-Toleranzen)
            if diff >= 1.0:
                if messagebox.askyesno("⚖️ Waage: Verbrauch erkannt!", f"Das Gewicht auf der Waage ist um {diff}g leichter als vorher.\n\nMöchtest du diese {diff}g als verbrauchtes Filament in die Statistik (Logbuch) eintragen?"):
                    self.log_consumption(diff)
        # -------------------------------

        self.inventory[idx] = d
        self.learn_dropdown_values(d)
        self.data_manager.save_inventory(self.inventory)
        self.refresh_table()
        self.tree.selection_set(str(d['id']))

    def delete_filament(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Löschen", "Wirklich löschen?"): return
        # NEU: Text-Vergleich beim Löschen
        self.inventory = [i for i in self.inventory if str(i['id']) != str(sel[0])]
        self.data_manager.save_inventory(self.inventory); self.refresh_table(); self.clear_inputs()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        i = next((x for x in self.inventory if str(x['id']) == str(sel[0])), None)
        if not i: return
        self.last_selected_spool_id = i.get('spool_id', -1)
        self.clear_inputs(deselect=False);
        self.entry_id.config(state="normal") 
        self.entry_id.insert(0, str(i['id']));
        self.entry_rfid.insert(0, i.get('rfid', '')); 
        self.entry_brand.insert(0, i['brand']); 
        self.combo_material.set(i.get('material', 'PLA')); 
        self.combo_color.set(i['color']); 
        self.combo_subtype.set(i.get('subtype', 'Standard')); 
        self.update_color_preview(); 
        self.combo_type.set(i['type']); 
        self.update_slot_dropdown(); 
        self.combo_loc_id.set(i.get('loc_id', '')); 
        self.entry_flow.insert(0, i.get('flow', '')); 
        self.entry_pa.insert(0, i.get('pa', '')); 
        self.var_reorder.set(i.get('reorder', False))
        for val in self.combo_spool['values']:
            if val.startswith(f"{i.get('spool_id', -1)} -"): self.combo_spool.set(val); break
            
        if i.get('empty_weight') is not None:
            self.var_custom_empty.set(f"{i['empty_weight']:g}")
        else:
            self.var_custom_empty.set("")
        for val in self.combo_spool['values']:
            if val.startswith(f"{i.get('spool_id', -1)} -"): self.combo_spool.set(val); break
        self.var_capacity.set(str(i.get('capacity', 1000))); gross = str(i.get('weight_gross', '0')).replace(',', '.'); float_g = float(gross) if gross else 0; self.var_gross.set(str(float_g).rstrip('0').rstrip('.') if float_g > 0 else "0"); self.var_price.set(str(i.get('price', ''))); self.update_net_weight_display(); 
        self.entry_supplier.insert(0, i.get('supplier', '')); self.entry_sku.insert(0, i.get('sku', '')); self.entry_link.insert(0, i.get('link', '')); self.entry_temp_n.insert(0, i.get('temp_n', '')); self.entry_temp_b.insert(0, i.get('temp_b', '')); self.entry_note.insert(0, i.get('note', '')); self.entry_barcode.insert(0, i.get('barcode', ''));
        self.var_is_refill.set(i.get('is_refill', False))
        self.last_selected_type = self.combo_type.get()
    
    def clear_inputs(self, deselect=True):
        self.last_selected_spool_id = -1
        self.var_custom_empty.set("")
        for e in [self.entry_id, self.entry_rfid, self.entry_brand, self.entry_flow, self.entry_pa, self.entry_supplier, self.entry_sku, self.entry_link, self.entry_temp_n, self.entry_temp_b, self.entry_note, self.entry_barcode]: 
            e.delete(0, tk.END)
        self.var_capacity.set("1000")
        self.var_gross.set("")
        self.var_price.set("")
        self.combo_color.set("")
        self.combo_loc_id.set("")
        self.combo_material.current(0)
        self.combo_subtype.current(0)
        self.combo_type.set("LAGER")
        self.combo_spool.current(0)
        self.update_net_weight_display()
        self.update_slot_dropdown()
        self.var_reorder.set(False)
        self.var_is_refill.set(False)
        self.update_color_preview()
        if deselect: 
            self.tree.selection_remove(self.tree.selection())

    def clone_filament(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showinfo("Info", "Bitte wähle zuerst eine Spule aus, die du klonen möchtest.")
        
        # 1. Wir leeren das ID-Feld und das RFID-Feld (damit es eine neue Spule wird)
        self.entry_id.delete(0, tk.END)
        self.entry_rfid.delete(0, tk.END)
        
        # 2. Wir nutzen die normale Hinzufügen-Funktion
        self.add_filament()
        messagebox.showinfo("Erfolg", "Spule erfolgreich geklont!")

    def edit_shelf_names(self, parent_win=None, current_shelves=None, current_lbl_r=None, target_shelf_name=None):
        if not target_shelf_name: return
        
        target_win = parent_win if parent_win else self.root
        win = tk.Toplevel(target_win)
        win.title(f"🏷️ Fächer benennen: {target_shelf_name}")
        win.transient(target_win)
        win.grab_set()
        
        ttk.Label(win, text=f"Eigene Namen für '{target_shelf_name}':", font=FONT_BOLD).pack(pady=10)

        shelves_str = current_shelves if current_shelves else self.settings.get("shelves", "REGAL|4|8")
        from core.logic import parse_shelves_string
        parsed_shelves = parse_shelves_string(shelves_str)
        
        target_shelf = next((s for s in parsed_shelves if s['name'] == target_shelf_name), None)
        if not target_shelf: return
        shelf_count = target_shelf['rows']
        
        win_height = max(250, 120 + (shelf_count * 32))
        win.geometry(f"350x{win_height}")
        
        all_shelf_names = self.settings.get("shelf_names_v2", {})
        old_names = all_shelf_names.get(target_shelf_name, {})
        
        # WICHTIG: Wir trennen, was in der Datenbank steht und was die UI anzeigt
        db_lbl_r = self.settings.get('label_row', 'Fach')
        ui_lbl_r = current_lbl_r if current_lbl_r else db_lbl_r
        
        entries = {}
        frame_list = ttk.Frame(win)
        frame_list.pack(fill="both", expand=True, padx=20, pady=5)
        
        for i in range(1, shelf_count + 1):
            frm = ttk.Frame(frame_list)
            frm.pack(fill="x", pady=3)
            ttk.Label(frm, text=f"{ui_lbl_r} {i}:", width=12).pack(side="left")
            ent = ttk.Entry(frm)
            ent.pack(side="right", fill="x", expand=True)
            ent.insert(0, old_names.get(str(i), f"{ui_lbl_r} {i}"))
            entries[str(i)] = ent

        def save_names():
            new_names = {str(k): v.get().strip() for k, v in entries.items()}
            changes_made = 0
            
            for i in range(1, shelf_count + 1):
                # Wir prüfen beide möglichen alten Namen (Datenbank vs. Fallback)
                old_val = old_names.get(str(i), f"{db_lbl_r} {i}")
                new_val = new_names.get(str(i), f"{ui_lbl_r} {i}")
                
                if old_val != new_val: 
                    # Wir suchen ab sofort nur noch nach dem Reihen-Namen (Kugelsicher!)
                    search_str1 = f"{old_val} - "
                    search_str2 = f"{db_lbl_r} {i} - "
                    replace_str = f"{new_val} - "
                    
                    for item in self.inventory:
                        if item.get("type") == target_shelf_name:
                            loc_id = str(item.get("loc_id", ""))
                            # Prüft auf den gespeicherten ODER den Standard-Namen
                            if loc_id.startswith(search_str1):
                                item["loc_id"] = loc_id.replace(search_str1, replace_str, 1)
                                changes_made += 1
                            elif loc_id.startswith(search_str2):
                                item["loc_id"] = loc_id.replace(search_str2, replace_str, 1)
                                changes_made += 1
            
            all_shelf_names[target_shelf_name] = new_names
            self.settings["shelf_names_v2"] = all_shelf_names
            
            # ANTI-ÜBERSCHREIB-FIX: Wir injizieren die neuen Namen sofort in das Einstellungs-Fenster im Hintergrund!
            if parent_win and hasattr(parent_win, 'settings'):
                parent_win.settings["shelf_names_v2"] = all_shelf_names
                
            self.data_manager.save_settings(self.settings)
            
            # IMMER speichern und aktualisieren, um Tabellen-Hänger zu vermeiden
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.update_slot_dropdown()
            
            messagebox.showinfo("Gespeichert", f"Namen für {target_shelf_name} aktualisiert!\n{changes_made} Spulen wurden automatisch umgebucht.", parent=win)
            win.destroy()

        ttk.Button(win, text="💾 Speichern & Aktualisieren", command=save_names, style="Accent.TButton").pack(pady=15)


    def send_to_storage(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showinfo("Info", "Bitte wähle zuerst eine Spule aus.")
        
        # 1. Wir setzen die Felder hart auf "LAGER" und leeren den genauen Slot
        self.combo_type.set("LAGER")
        self.combo_loc_id.set("-")
        
        # 2. Wir speichern die Änderung sofort ab
        self.update_filament()

    def quick_swap_dialog(self):
        sel = self.tree.selection()
        if not sel: 
            return messagebox.showinfo("Info", "Bitte zuerst eine Spule auswählen!", parent=self.root)
            
        s_a = next((i for i in self.inventory if str(i.get('id')) == str(sel[0])), None)
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
            # 1. Prio: Suche nach Hersteller-Barcode (Groß-/Kleinschreibung ignorieren)
            item = next((i for i in self.inventory if str(i.get('barcode', '')).lower() == scan.lower() and scan != ""), None)
            if item:
                found_id = str(item['id'])
            else:
                # 2. Prio: Suche nach VibeSpool ID (Jetzt auch Alphanumerisch!)
                match = re.search(r'(?:ID|1D|lD|VibeSpool)[\s:=_\-\.]*([a-zA-Z0-9-]+)', scan, re.IGNORECASE)
                extracted_id = match.group(1) if match else scan
                
                # Prüfen ob diese ID existiert (beide Seiten .lower()!)
                item = next((i for i in self.inventory if str(i.get('id')).lower() == str(extracted_id).lower()), None)
                if item:
                    found_id = str(item['id'])

        if found_id and self.tree.exists(found_id):
            self.tree.selection_set(found_id)
            self.tree.see(found_id)
            self.on_select(None)
            self.entry_scan.delete(0, tk.END)
        else:
            messagebox.showerror("Fehler", f"Keine Spule mit {'RFID' if self.settings.get('rfid_mode') else 'ID / Barcode'} '{scan}' gefunden.")
            self.entry_scan.delete(0, tk.END)
    

    def scan_qr_webcam(self):
        try:
            import cv2 # type: ignore
            from pyzbar import pyzbar # type: ignore
        except Exception as e:
            messagebox.showerror("Fehler", f"Scanner-Module konnten nicht geladen werden.\nDetails: {e}")
            return
            
        # NEU: Nutze DirectShow (CAP_DSHOW) für Windows - das startet Kameras oft viel zuverlässiger!
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not cap.isOpened(): 
            messagebox.showerror("Fehler", "Kamera (Index 0) konnte nicht geöffnet werden.\nHast du eine Webcam angeschlossen?")
            return
            
        win_name = "VibeSpool QR-Scanner (ESC zum Schließen)"
        found_id = None
        
        # NEU: Test-Bild abrufen, um zu prüfen ob Windows die Kamera blockiert
        ret, frame = cap.read()
        if not ret or frame is None:
            messagebox.showerror("Kamera Fehler", "Die Kamera liefert kein Bild!\n\nBitte prüfe in Windows:\nEinstellungen -> Datenschutz & Sicherheit -> Kamera -> 'Desktop-Apps den Zugriff erlauben' muss EINGESCHALTET sein!")
            cap.release()
            return

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            try:
                for barcode in pyzbar.decode(frame):
                    barcode_data = barcode.data.decode("utf-8")
                    match = re.search(r'(?:ID:\s*|FIL_)?(\d+)', barcode_data, re.IGNORECASE)
                    if match: 
                        found_id = match.group(1)
                        break
            except Exception as e:
                messagebox.showerror("DLL Fehler", f"Absturz beim Dekodieren. Fehlen DLLs?\n{e}")
                break
                
            cv2.imshow(win_name, frame)
            
            if found_id or cv2.waitKey(1) & 0xFF == 27: 
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        if found_id: 
            self.entry_scan.delete(0, tk.END)
            self.entry_scan.insert(0, found_id)
            self.on_quick_scan()

    def open_mobile_companion(self):
        local_ip = get_local_ip()
        url = f"http://{local_ip}:8289"
        
        win = tk.Toplevel(self.root)
        win.title("📱 Handy Scanner verbinden")
        win.geometry("450x550")
        win.configure(bg=self.root.cget('bg'))
        center_window(win, self.root)
        
        ttk.Label(win, text="Scanne diesen Code mit deinem Handy:", font=("Segoe UI", 12, "bold")).pack(pady=20)
        
        from PIL import Image, ImageTk
        import qrcode
        from qrcode.image.pil import PilImage
        
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        
        # Pylance-Safe: Wir zwingen die Bibliothek zu einem PIL-Image
        qr_wrapper = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
        img = qr_wrapper.get_image().convert('RGB')
        
        photo = ImageTk.PhotoImage(img)
        lbl_img = tk.Label(win, image=photo, borderwidth=2, relief="solid")
        lbl_img.image = photo # type: ignore
        lbl_img.pack(pady=10)
        
        ttk.Label(win, text="Oder gib diese URL in deinen Handy-Browser ein:", font=("Segoe UI", 10)).pack(pady=(20, 5))
        ent = ttk.Entry(win, font=("Segoe UI", 12, "bold"), justify="center")
        ent.insert(0, url)
        ent.config(state="readonly")
        ent.pack(fill="x", padx=40, pady=5)
        
        ttk.Label(win, text="⚠️ Hinweis: PC und Handy müssen im selben WLAN sein!", foreground="#0078d7").pack(pady=10)

    def process_mobile_scan(self, code):
        # Das Handy schickt uns den Text, VibeSpool fügt ihn oben ein und drückt quasi "Enter"
        self.entry_scan.delete(0, tk.END)
        self.entry_scan.insert(0, code)
        self.on_quick_scan()
    
    def process_unknown_scan(self, code):
        # 1. Trägt den Barcode in das entsprechende Feld ein
        self.entry_barcode.delete(0, tk.END)
        self.entry_barcode.insert(0, code)
        
        # 2. Wechselt elegant auf den "Kaufmännisch" Tab, damit du sofort siehst, dass es geklappt hat!
        try:
            self.notebook.select(1)
        except: pass

    def process_mobile_action(self, spool_id, action, val):
        item = next((i for i in self.inventory if i.get('id') == spool_id), None)
        if not item: return

        changes_made = False

        if action == "usage":
            try:
                used = float(val.replace(',', '.'))
                curr = float(str(item.get('weight_gross', '0')).replace(',', '.'))
                if used > 0 and curr > 0:
                    item['weight_gross'] = max(0, curr - used)
                    changes_made = True
            except: pass

        elif action == "move":
            # Das Handy schickt das Format "TYP|SLOT" (z.B. "REGAL|Fach 1 - Slot 2")
            if "|" in val:
                target_type, target_loc = val.split("|", 1)
                
                # Wir schieben die Spule knallhart um
                item['type'] = target_type
                item['loc_id'] = target_loc
                changes_made = True

        if changes_made:
            # Änderungen speichern und Tabelle aktualisieren
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()

            # Wenn die Spule auf dem PC gerade markiert/geöffnet ist, updaten wir das Formular live!
            sel = self.tree.selection()
            if sel and int(sel[0]) == spool_id:
                self.on_select(None)
    
    def process_mobile_swap(self, spool_id_str, target_type, target_loc, col_item):
        """Führt einen Quick-Swap vom Handy aus durch."""
        s_a = next((i for i in self.inventory if str(i['id']) == spool_id_str), None)
        if not s_a: return

        o_t, o_l = s_a.get('type', 'LAGER'), s_a.get('loc_id', '-')

        # Tausche die Spulen
        s_a['type'] = target_type
        s_a['loc_id'] = target_loc
        col_item['type'] = o_t
        col_item['loc_id'] = o_l

        self.data_manager.save_inventory(self.inventory)
        self.refresh_table()

        # Zeige PC-Benachrichtigung an!
        self.show_custom_toast("🔄 Mobile Quick-Swap", f"{s_a.get('brand','')} ist im {target_type} Slot {target_loc}.\nDie alte Spule liegt jetzt in {o_t} {o_l}.")

    def refresh_all_data(self): 
        self.inventory, self.settings, self.spools = self.data_manager.load_all(DEFAULT_SETTINGS) # type: ignore
        self.apply_theme(); self.update_locations_dropdown(); self.refresh_table()

    
    def on_bambu_print_finish(self, tray_ids, weight_g):
        """Wird vom Hintergrund-Thread aufgerufen, wenn der Druck fertig ist."""
        # Wir brechen nur noch ab, wenn gar kein AMS-Slot erkannt wurde (z.B. externe Spule)
        if not tray_ids: return
        
        # Wir springen in den Haupt-Thread von Tkinter für das UI-Update
        if len(tray_ids) == 1 and weight_g > 0:
            # SZENARIO A: Single-Color UND der Drucker kennt das Gewicht -> Vollautomatisch!
            ams_id = (tray_ids[0] // 4) + 1
            slot = (tray_ids[0] % 4) + 1
            self.root.after(0, lambda: self._apply_automatic_deduction(f"AMS {ams_id}", str(slot), weight_g))
        else:
            # SZENARIO B: Entweder Multi-Color ODER der Drucker weiß das Gewicht nicht (0g)
            # In beiden Fällen fragen wir den User einfach per Dialog!
            self.root.after(0, lambda: self._show_multicolor_dialog(tray_ids, weight_g))

    def _apply_automatic_deduction(self, ams_name, slot_in_ams, weight_g, silent=False):
        """Führt die tatsächliche Gewichtsänderung in der Datenbank aus."""
        item = next((i for i in self.inventory if i.get('type') == ams_name and str(i.get('loc_id')) == str(slot_in_ams)), None)
        
        if item:
            try:
                old_gross = float(str(item.get('weight_gross', '0')).replace(',', '.'))
                new_gross = max(0, old_gross - weight_g)
                item['weight_gross'] = new_gross
                
                # --- NEU: Historie für Auto-Sync eintragen! ---
                if "history" not in item: item["history"] = []
                
                mat_cost = 0.0
                try:
                    sp_price = float(str(item.get('price', '0')).replace(',', '.')) or 0.0
                    sp_cap = float(str(item.get('capacity', '1000'))) or 1000.0
                    if sp_cap > 0: mat_cost = weight_g * (sp_price / sp_cap)
                except: pass
                
                from datetime import datetime
                item["history"].append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "Bambu Live-Sync",
                    "change": f"-{weight_g:.1f}g",
                    "cost": f"{mat_cost:.2f} €",
                    "sell_price": "-"
                })
                
                self.data_manager.save_inventory(self.inventory)
                self.log_consumption(weight_g) # Live Sync ist immer "heute"
                self.refresh_table()
                self.broadcast_mqtt()
                
                sel = self.tree.selection()
                if sel and str(sel[0]) == str(item['id']):
                    self.on_select(None)
                
                if not silent:
                    msg = f"Es wurden {weight_g:.1f}g von Spule #{item['id']} abgezogen.\n({item.get('brand')} {item.get('color')})"
                    self.show_custom_toast("🎨 Druck beendet!", msg)

            except Exception as e:
                print(f"Fehler beim Abziehen: {e}")

    def _show_multicolor_dialog(self, tray_ids, total_weight_g):
        """Öffnet einen Dialog, wenn mehrere AMS-Slots benutzt wurden."""
        win = tk.Toplevel(self.root)
        win.title("🎨 Multi-Color Druck beendet")
        win.geometry("500x400")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        from core.utils import center_window
        center_window(win, self.root)
        
        ttk.Label(win, text="Multi-Color Druck abgeschlossen!", font=("Segoe UI", 14, "bold"), foreground="#0078d7").pack(pady=(15, 5))
        ttk.Label(win, text=f"Gesamtverbrauch (laut Slicer): {total_weight_g:.1f} g\nWelche Spule hat wie viel verbraucht?", justify="center").pack(pady=5)
        
        frm = ttk.Frame(win, padding=15)
        frm.pack(fill="both", expand=True)
        
        entries = []
        
        # Für jeden benutzten Slot ein Feld generieren
        for t_id in tray_ids:
            ams_id = (t_id // 4) + 1
            slot = (t_id % 4) + 1
            ams_name = f"AMS {ams_id}"
            
            # Schauen wir, welche Spule in VibeSpool auf diesem Platz liegt
            item = next((i for i in self.inventory if i.get('type') == ams_name and str(i.get('loc_id')) == str(slot)), None)
            
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=5)
            
            if item:
                lbl_text = f"{ams_name} Slot {slot}: {item.get('brand')} {item.get('color')}"
            else:
                lbl_text = f"{ams_name} Slot {slot}: Unbekannte Spule"
                
            ttk.Label(row, text=lbl_text, width=30).pack(side="left")
            
            # Eingabefeld für die Grammzahl
            ent = ttk.Entry(row, width=10, justify="right")
            ent.pack(side="right")
            ttk.Label(row, text=" g").pack(side="right")
            
            entries.append({"ams_name": ams_name, "slot": str(slot), "entry": ent, "item": item})
            
        def apply_split():
            total_entered = 0
            for e in entries:
                val = e["entry"].get().strip().replace(',', '.')
                if val:
                    try:
                        weight = float(val)
                        if weight > 0:
                            total_entered += weight
                            self._apply_automatic_deduction(e["ams_name"], e["slot"], weight, silent=True)
                    except: pass
                    
            if total_entered > 0:
                messagebox.showinfo("Erfolg", f"Es wurden insgesamt {total_entered:.1f}g auf die Spulen aufgeteilt und abgezogen!", parent=self.root)
            win.destroy()
            
        ttk.Separator(win, orient="horizontal").pack(fill="x", pady=10)
        btn_frm_mc = ttk.Frame(win, padding=10)
        btn_frm_mc.pack(fill="x", side="bottom")
        ttk.Button(win, text="💾 Gewichte abziehen & Speichern", command=apply_split, style="Accent.TButton").pack(pady=10)

    def run_ams_sync(self):
        ip = self.settings.get("bambu_ip", "")
        code = self.settings.get("bambu_access", "")
        serial = self.settings.get("bambu_serial", "")

        if not ip or not code or not serial:
            return messagebox.showerror("Fehler", "Bambu Zugangsdaten fehlen! Bitte erst in den Optionen eintragen.")

        # Lade-Fenster blockiert die GUI, damit der User nicht wild rumklickt
        self.sync_win = tk.Toplevel(self.root)
        self.sync_win.title("AMS Sync")
        self.sync_win.geometry("350x120")
        self.sync_win.configure(bg=self.root.cget('bg'))
        center_window(self.sync_win, self.root)
        ttk.Label(self.sync_win, text="Verbinde mit Bambu Drucker...\nLese AMS Daten aus.\n\nBitte warten (ca. 5-10 Sekunden).", font=FONT_BOLD, justify="center").pack(expand=True)
        self.sync_win.grab_set()

        # Import hier, damit das Programm nicht abstürzt, falls Paho-MQTT fehlt
        try:
            from core.bambu_sync import BambuScanner # type: ignore
        except ImportError:
            self.sync_win.destroy()
            return messagebox.showerror("Fehler", "Das Modul 'paho-mqtt' fehlt. Bitte über pip installieren.")

        # Threading: Der Scanner läuft im Hintergrund, die GUI friert NICHT ein!
        def worker():
            scanner = BambuScanner(ip, code, serial)
            result = scanner.fetch_ams_inventory(timeout=10)
            # Zurück in den Haupt-Thread für das UI-Update
            self.root.after(0, lambda: self._process_ams_result(result))

        threading.Thread(target=worker, daemon=True).start()

    def _process_ams_result(self, result):
        if hasattr(self, 'sync_win') and self.sync_win.winfo_exists():
            self.sync_win.destroy()

        if not result:
            return messagebox.showerror("Fehler", "Keine Antwort vom Drucker. Ist er an und im LAN?")

        # Das neue, interaktive Sync Control Center
        win = tk.Toplevel(self.root)
        win.title("🤖 AMS Live-Sync Manager")
        win.geometry("900x400")
        win.configure(bg=self.root.cget('bg'))
        
        # Native Tkinter-Zentrierung (Pylance-freundlich!)
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        x, y = (win.winfo_screenwidth() // 2) - (w // 2), (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"+{x}+{y}")
        
        ttk.Label(win, text="Bambu AMS mit VibeSpool abgleichen", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Container für die Slots
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True, padx=15)
        
        # Kopfzeile
        headers = ["AMS Slot (Bambu Info)", "Welche Spule wurde eingelegt?", "Alte Spule zurücklegen nach:"]
        for col, h in enumerate(headers):
            ttk.Label(frm, text=h, font=FONT_BOLD).grid(row=0, column=col, padx=5, pady=5, sticky="w")
            
        ttk.Separator(frm, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # Dropdown-Werte vorbereiten (Exakt wie in VibeSpool formatiert!)
        all_locs = []
        parsed_shelves = parse_shelves_string(self.settings.get("shelves", "REGAL|4|8")) # type: ignore
        lbl_row = self.settings.get("label_row", "Fach")
        lbl_col = self.settings.get("label_col", "Slot")
        
        shelf_names_all = self.settings.get("shelf_names_v2", {})

        for sh in parsed_shelves:
            name = sh['name']
            rows = sh['rows']
            cols = sh['cols']
            shelf_names = shelf_names_all.get(name, {})
            for r in range(1, rows + 1):
                row_name = shelf_names.get(str(r), f"{lbl_row} {r}")
                for c in range(1, cols + 1):
                    col_name = shelf_names.get(f"col_{c}", f"{lbl_col} {c}")
                    # Hier ist jetzt die Doppeltiefe auch im Sync aktiv!
                    if self.settings.get("double_depth", False):
                        all_locs.append(f"{name} {row_name} - {col_name} (H)")
                        all_locs.append(f"{name} {row_name} - {col_name} (V)")
                    else:
                        all_locs.append(f"{name} {row_name} - {col_name}")
        
        if self.settings.get("custom_locs", ""):
            custom = [x.strip() for x in self.settings.get("custom_locs", "").split(",") if x.strip()]
            all_locs += custom
            
        # Dropdown-Werte für Filament vorbereiten (Sortiert nach ID & mit intelligentem Lagerort!)
        filament_values = ["- Leer / Ignorieren -"]
        
        # 1. Wir filtern leere Spulen raus und sortieren den Rest sauber nach ID (numerisch)
        active_filaments = [i for i in self.inventory if i.get('type') != 'VERBRAUCHT']
        active_filaments.sort(key=lambda x: int(x.get('id', 0)))
        
        # 2. Wir bauen die formatierte Liste für das Dropdown auf
        for i in active_filaments:
            name = f"{i.get('brand', '')} {i.get('material', '')} {i.get('color', '')}".strip()
            loc_str = f"{i.get('type', '')} {i.get('loc_id', '')}".strip()
            loc_display = f"[{loc_str}]" if loc_str else "[Ort unbekannt]"
            
            filament_values.append(f"{i['id']} - {name} {loc_display}")

        loc_values = ["- Nicht verschieben -"] + all_locs

        # Wir speichern die Auswahl des Users ab
        self.sync_vars = []

        # Für jeden Slot eine Zeile aufbauen
        for idx, r in enumerate(result):
            row_idx = idx + 2
            
            # NEU: Wir berechnen dynamisch das AMS und den Slot (0-3 = AMS 1, 4-7 = AMS 2)
            raw_slot = int(r.get('slot', 0))
            ams_num = r.get('ams', (raw_slot // 4)) + 1
            slot_num = (raw_slot % 4) + 1
            ams_name = f"AMS {ams_num}"
            
            # 1. Spalte: Was sagt Bambu?
            info_frame = tk.Frame(frm, bg=self.root.cget('bg'))
            info_frame.grid(row=row_idx, column=0, sticky="w", pady=10)
            tk.Label(info_frame, text=f"{ams_name} Slot {slot_num}: ", font=FONT_BOLD, bg=self.root.cget('bg'), fg="white" if "dark" in str(self.root.cget('bg')) else "black").pack(side="left")
            
            if r['empty']:
                tk.Label(info_frame, text="LEER", fg="#999999", bg=self.root.cget('bg')).pack(side="left")
            else:
                hex_col = f"#{r['color_hex'][:6]}" if len(r['color_hex']) >= 6 else "#FFFFFF"
                tk.Label(info_frame, text="   ", bg=hex_col, relief="solid", borderwidth=1).pack(side="left", padx=(0, 5))
                tk.Label(info_frame, text=r['material'] or "Unbekannt", bg=self.root.cget('bg'), fg="white" if "dark" in str(self.root.cget('bg')) else "black").pack(side="left")

            # 2. Spalte: Welche Spule aus VibeSpool ist das?
            # NEU: Wir packen Combobox und Button nebeneinander in ein Frame
            frm_col1 = ttk.Frame(frm)
            frm_col1.grid(row=row_idx, column=1, padx=10, pady=10, sticky="w")
            
            var_new_spool = tk.StringVar()
            cb_new = ttk.Combobox(frm_col1, textvariable=var_new_spool, values=filament_values, state="readonly", width=35)
            cb_new.pack(side="left", padx=(0, 5))
            
            # --- SMART PRE-SELECTION (Auto-Mapping & Position Memory) ---
            current_fil = next((i for i in active_filaments if i.get('type') == ams_name and str(i.get('loc_id')) == str(slot_num)), None)
            
            if current_fil:
                name = f"{current_fil.get('brand', '')} {current_fil.get('material', '')} {current_fil.get('color', '')}".strip()
                loc_str = f"{current_fil.get('type', '')} {current_fil.get('loc_id', '')}".strip()
                loc_display = f"[{loc_str}]" if loc_str else "[Ort unbekannt]"
                val_to_select = f"{current_fil['id']} - {name} {loc_display}"
                
                if val_to_select in filament_values:
                    cb_new.set(val_to_select)
                else:
                    cb_new.set("- Leer / Ignorieren -")
            else:
                cb_new.set("- Leer / Ignorieren -")

            # --- NEU: Auto-Import Button (Nur anzeigen, wenn wirklich eine Spule im Slot ist) ---
            if not r['empty']:
                # Helper-Funktion, um die aktuellen Variablen in den Button zu "brennen"
                def make_import_cmd(current_r, current_cb):
                    return lambda: self.auto_import_from_ams(current_r, current_cb)
                
                ttk.Button(frm_col1, text="➕ Neu anlegen", command=make_import_cmd(r, cb_new)).pack(side="left")

            # 3. Spalte: Wohin mit dem alten Zeug?
            var_old_loc = tk.StringVar()
            cb_old = ttk.Combobox(frm, textvariable=var_old_loc, values=loc_values, state="readonly", width=25)
            cb_old.set("- Nicht verschieben -")
            cb_old.grid(row=row_idx, column=2, padx=10, pady=10)

            # WICHTIG: Wir speichern das 'cb_new' Widget ab, damit wir es später aktualisieren können!
            self.sync_vars.append({"ams_name": ams_name, "slot_num": slot_num, "bambu_data": r, "var_new": var_new_spool, "var_old": var_old_loc, "cb_widget": cb_new})

        ttk.Separator(frm, orient="horizontal").grid(row=6, column=0, columnspan=3, sticky="ew", pady=15)
        
        # FIX: Container für Button hart nach unten!
        btn_frm = ttk.Frame(win, padding=10)
        btn_frm.pack(fill="x", side="bottom")
        ttk.Button(btn_frm, text="💾 Sync in Datenbank speichern", command=lambda: self.apply_ams_sync(win), style="Accent.TButton").pack(side="right")

    def auto_import_from_ams(self, r, target_cb):
        # 1. Neue ID generieren
        new_id = max([int(i.get('id', 0)) for i in self.inventory], default=0) + 1
        
        # 2. Daten vom Drucker sauber auslesen
        mat = r.get('material', 'PLA') or 'PLA'
        
        # Bambu liefert den Hex oft als RGBA. Wir brauchen nur die ersten 6 Zeichen.
        hex_color = f"#{r.get('color_hex', 'FFFFFF')[:6]}".upper()
        if hex_color == "#": hex_color = "#FFFFFF"
        
        # --- NEU: Der automatische Farb-Übersetzer! ---
        from core.colors import get_color_name_from_hex
        matched_name = get_color_name_from_hex(hex_color)
        
        # In die Datenbank schreiben wir Name + Code (für das Icon)
        final_color_db = f"{matched_name} ({hex_color})" if matched_name else hex_color
        
        # In der Dropdown-Liste zeigen wir DIR aber nur den sauberen Namen!
        display_color_name = matched_name if matched_name else hex_color
        
        brand = "Bambu" 
        
        # 3. Das neue Spulen-Paket schnüren
        new_item = {
            "id": new_id, "rfid": "", "brand": brand, "material": mat, 
            "color": final_color_db,  # <--- Hier die übersetzte Farbe eintragen!
            "subtype": "Standard", "type": "LAGER", "loc_id": "-", 
            "flow": "", "pa": "", "spool_id": -1, "weight_gross": 1000, "capacity": 1000,
            "is_empty": False, "reorder": False, "supplier": "", "sku": "", "price": "", 
            "link": "", "temp_n": "", "temp_b": ""
        }
        
        # 4. In die Datenbank feuern
        self.inventory.append(new_item)
        self.data_manager.save_inventory(self.inventory)
        self.refresh_table()
        
        # 5. Den Dropdowns das neue Filament beibringen (Ohne hässlichen Hex-Code!)
        display_text = f"{new_id} - {brand} {mat} {display_color_name} [LAGER -]"
        
        for sv in getattr(self, 'sync_vars', []):
            cb = sv.get('cb_widget')
            if cb:
                vals = list(cb['values'])
                vals.append(display_text)
                cb['values'] = vals
                
        # 6. Direkt im aktuellen Slot auswählen!
        target_cb.set(display_text)
    
    def apply_ams_sync(self, win):
        moved_new = []
        moved_old = []
        
        # --- FIX: Wir sammeln zuerst alle Spulen-IDs, die gerade ins AMS wandern ---
        incoming_ids = []
        for sv in self.sync_vars:
            new_selection = sv['var_new'].get()
            if new_selection != "- Leer / Ignorieren -":
                try:
                    incoming_ids.append(str(new_selection.split(" - ")[0]))
                except: pass

        # --- PRE-CHECK: Kollisionsprüfung für das Regal ---
        collisions = []
        for sv in self.sync_vars:
            old_destination = sv['var_old'].get()
            if old_destination != "- Nicht verschieben -":
                parts = old_destination.split(" ", 1)
                dest_type = parts[0] if len(parts) == 2 else old_destination
                dest_loc = parts[1] if len(parts) == 2 else ""
                
                # Prüft, ob auf diesem Regal-Platz schon eine andere, aktive Spule liegt
                existing = next((i for i in self.inventory if i.get('type') == dest_type and i.get('loc_id') == dest_loc and i.get('type') != 'VERBRAUCHT'), None)
                
                # FIX: Wenn die blockierende Spule auf der 'incoming_ids' Liste steht, 
                # räumt sie den Platz in dieser Sekunde für uns! -> Keine Kollision! (Quick-Swap erlaubt)
                if existing and str(existing.get('id')) not in incoming_ids:
                    collisions.append(f"• {old_destination} (ist belegt durch: #{existing['id']} {existing.get('brand','')} {existing.get('color','')})")
                    
        # Wenn wir (echte) Kollisionen gefunden haben, schlagen wir Alarm!
        if collisions:
            msg = "Achtung! Du versuchst alte Spulen auf Plätze zu legen, die bereits belegt sind:\n\n" + "\n".join(collisions) + "\n\nMöchtest du trotzdem speichern und riskieren, dass zwei Spulen am selben Platz liegen?"
            if not messagebox.askyesno("⚠️ Lagerplatz bereits belegt", msg):
                return # Bricht den gesamten Sync-Vorgang ab, der User muss korrigieren!

        # --- NORMALE SPEICHERLOGIK ---
        for sv in self.sync_vars:
            ams_name = sv['ams_name'] # NEU: Dynamischer AMS-Name
            slot_num_str = str(sv['slot_num']) # z.B. "3"
            new_selection = sv['var_new'].get() 
            old_destination = sv['var_old'].get() 
            
            # FIX 1: VibeSpool nennt das Regal intern "type" und das Fach "loc_id"!
            old_filament = next((i for i in self.inventory if i.get('type') == ams_name and str(i.get('loc_id')) == slot_num_str), None)
            
            new_id = -1
            if new_selection != "- Leer / Ignorieren -":
                try:
                    new_id = int(new_selection.split(" - ")[0])
                except: pass

            if old_filament and new_id == old_filament.get('id'):
                continue
            
            # FIX 2: Alte Spule korrekt aufteilen (z.B. "REGAL Fach 1 - Slot 1" -> type="REGAL", loc_id="Fach 1 - Slot 1")
            if old_filament and old_destination != "- Nicht verschieben -":
                parts = old_destination.split(" ", 1)
                if len(parts) == 2:
                    old_filament['type'] = parts[0]
                    old_filament['loc_id'] = parts[1]
                else:
                    old_filament['type'] = old_destination
                    old_filament['loc_id'] = ""
                moved_old.append(f"#{old_filament['id']} nach {old_destination}")
            
            # FIX 3: Neue Spule korrekt in AMS eintragen
            if new_id != -1:
                new_filament = next((i for i in self.inventory if i.get('id') == new_id), None)
                if new_filament:
                    new_filament['type'] = ams_name
                    new_filament['loc_id'] = slot_num_str
                    moved_new.append(f"#{new_filament['id']} in {ams_name} Slot {slot_num_str}")

        total_changes = len(moved_new) + len(moved_old)
        if total_changes > 0:
            try:
                if hasattr(self.data_manager, 'save_inventory'):
                    self.data_manager.save_inventory(self.inventory)
                elif hasattr(self.data_manager, 'save_all'):
                    self.data_manager.save_all(self.inventory, self.settings, self.spools) # type: ignore
                else:
                    from core.utils import save_json # type: ignore
                    import os
                    db_path = os.path.join(getattr(self.data_manager, 'data_dir', ''), "inventory.json")
                    save_json(db_path, self.inventory)
            except Exception as e:
                messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{e}")
                return

            self.update_locations_dropdown()
            self.refresh_table()
            self.root.update_idletasks()
            
            msg = f"Sync erfolgreich durchgeführt ({total_changes} Umbuchungen).\n\n"
            if moved_new:
                msg += "✅ In AMS eingelegt:\n" + "\n".join(moved_new) + "\n\n"
            if moved_old:
                msg += "📦 Ins Regal zurückgelegt:\n" + "\n".join(moved_old)
            messagebox.showinfo("Bambu AMS Sync", msg)
        else:
            messagebox.showinfo("Info", "Keine Änderungen ausgewählt.")
            
        win.destroy()
    
    def import_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")], title="CSV Inventar importieren")
        if not filepath: return

        try:
            import csv
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                # Versuche das Trennzeichen automatisch zu erkennen (Komma oder Semikolon)
                sample = f.read(1024)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=';,')
                except:
                    dialect = csv.excel # Fallback, falls die Datei zu klein ist
                
                reader = csv.DictReader(f, dialect=dialect)
                
                if not reader.fieldnames:
                    return messagebox.showerror("Fehler", "Die CSV-Datei scheint leer zu sein oder hat keine Kopfzeile.")

                imported_count = 0
                for row in reader:
                    # Macht alle Spaltennamen klein und entfernt Leerzeichen, um Tippfehler zu verzeihen
                    row_lower = {k.lower().strip(): v for k, v in row.items() if k}

                    # --- SMARTES MAPPING ---
                    brand = row_lower.get('marke', row_lower.get('brand', row_lower.get('hersteller', 'Unbekannt')))
                    mat = row_lower.get('material', 'PLA')
                    color = row_lower.get('farbe', row_lower.get('color', 'Unbekannt'))
                    subtype = row_lower.get('effekt', row_lower.get('finish', row_lower.get('typ', 'Standard')))
                    gross = row_lower.get('brutto', row_lower.get('gewicht', 1000))

                    # Wenn Marke und Farbe unbekannt sind, ist es wahrscheinlich eine leere Excel-Zeile -> Überspringen
                    if brand == 'Unbekannt' and color == 'Unbekannt': 
                        continue 

                    # Neue ID generieren
                    new_id = max([int(i.get('id', 0)) for i in self.inventory], default=0) + 1

                    # Brutto-Gewicht säubern (Kommas in Punkte umwandeln für Python)
                    try:
                        gross_clean = float(str(gross).replace(',', '.'))
                    except:
                        gross_clean = 0.0

                    new_item = {
                        "id": new_id,
                        "rfid": "",
                        "brand": brand.strip(),
                        "material": mat.strip(),
                        "color": color.strip(),
                        "subtype": subtype.strip(),
                        "type": "LAGER", # Importierte Spulen landen erstmal immer im großen LAGER
                        "loc_id": "-",
                        "flow": "",
                        "pa": "",
                        "spool_id": -1, # -1 bedeutet "Unbekannte Leerspule"
                        "weight_gross": gross_clean,
                        "capacity": 1000,
                        "is_empty": False,
                        "reorder": False,
                        "supplier": row_lower.get('lieferant', row_lower.get('shop', '')).strip(),
                        "sku": row_lower.get('sku', row_lower.get('art-nr', '')).strip(),
                        "price": row_lower.get('preis', row_lower.get('price', '')).strip(),
                        "link": "",
                        "temp_n": "",
                        "temp_b": ""
                    }
                    self.inventory.append(new_item)
                    imported_count += 1

            if imported_count > 0:
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                messagebox.showinfo("Import Erfolgreich", f"Perfekt! Es wurden {imported_count} neue Spulen aus der CSV in dein Lager importiert!")
            else:
                messagebox.showwarning("Import fehlgeschlagen", "Es konnten keine passenden Daten gefunden werden.\nBitte stelle sicher, dass deine CSV Spaltennamen wie 'Marke', 'Material' und 'Farbe' in der ersten Zeile hat.")

        except Exception as e:
            messagebox.showerror("Fehler beim Import", f"Die Datei konnte nicht gelesen werden. Ist sie evtl. noch in Excel geöffnet?\n\nDetails: {e}")
    
    def setup_context_menus(self):
        # --- 1. DAS HEADER-MENÜ (Spalten-Konfigurator) ---
        self.menu_header = tk.Menu(self.root, tearoff=0)
        
        self.col_vars = {}
        all_cols = {"id": "ID", "brand": "Marke", "material": "Material", "color": "Farbe", 
                    "subtype": "Effekt / Typ", "weight": "Rest(g)", "flow": "Flow", 
                    "location": "Ort", "status": "Status"}
                    
        visible_now = self.settings.get("visible_columns", list(all_cols.keys()))
        
        def toggle_column():
            # Welche Spalten haben einen Haken?
            new_visible = [col for col, var in self.col_vars.items() if var.get()]
            if not new_visible: # Mindestens eine Spalte muss an bleiben!
                new_visible = ["id"]
                self.col_vars["id"].set(True)
                
            self.tree.configure(displaycolumns=new_visible)
            self.settings["visible_columns"] = new_visible
            self.data_manager.save_settings(self.settings)

        for col_id, col_name in all_cols.items():
            var = tk.BooleanVar(value=(col_id in visible_now))
            self.col_vars[col_id] = var
            self.menu_header.add_checkbutton(label=col_name, variable=var, command=toggle_column)
            
        self.menu_header.add_separator()
        self.menu_header.add_command(label="🔄 Standard-Ansicht", command=lambda: [v.set(True) for v in self.col_vars.values()] or toggle_column())

        # Wende die gespeicherten Spalten direkt beim Start an!
        self.tree.configure(displaycolumns=visible_now)

        # --- 2. DAS ZEILEN-MENÜ (Quick-Actions) ---
        self.menu_row = tk.Menu(self.root, tearoff=0)
        
        self.menu_row.add_command(label="🛒 Im Shop öffnen", command=self.quick_open_shop)
        self.menu_row.add_separator()
        
        self.menu_row.add_command(label="🔄 Quick-Swap (ins AMS)", command=self.quick_swap_dialog)
        self.menu_row.add_command(label="🐑 Spule klonen", command=self.clone_filament)
        self.menu_row.add_separator()
        self.menu_row.add_command(label="📦 Ins Lager verschieben", command=self.send_to_storage)
        self.menu_row.add_command(label="🚮 Als LEER markieren", command=self.quick_mark_empty)
        self.menu_row.add_command(label="🛒 Auf Einkaufsliste setzen/entfernen", command=self.quick_toggle_reorder)
        self.menu_row.add_separator()
        self.menu_row.add_command(label="📝 Etikett-Vorschau öffnen", command=self.quick_open_label)
        self.menu_row.add_command(label="❌ Spule löschen", command=self.delete_filament)

    def show_spool_history(self, event=None, spool_id=None):
        """Öffnet das Logbuch (Historie) für eine ausgewählte Spule."""
        if not spool_id:
            sel = self.tree.selection()
            if not sel: return
            spool_id = sel[0]

        # Spule in der Datenbank finden
        item = next((i for i in self.inventory if str(i.get('id')) == str(spool_id)), None)
        if not item: return

        # Farbe bereinigen für den Titel
        color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', '')).strip()

        # Fenster aufbauen
        win = tk.Toplevel(self.root)
        win.title(f"📜 Logbuch: #{item.get('id')} - {item.get('brand')} {color_clean}")
        win.geometry("550x400")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        from core.utils import center_window
        center_window(win, self.root)

        ttk.Label(win, text=f"📜 Historie für Spule #{item.get('id')}", font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))
        ttk.Label(win, text=f"{item.get('brand')} {color_clean} | {item.get('material')}", foreground="gray").pack(pady=(0, 10))

        history = item.get("history", [])

        # Wenn die Spule noch brandneu ist und keine Einträge hat
        if not history:
            ttk.Label(win, text="Bisher keine Einträge vorhanden.\n\nVerbräuche durch Cloud-Sync oder die Waage\nwerden hier automatisch protokolliert.", justify="center", foreground="gray").pack(expand=True)
            ttk.Button(win, text="Schließen", command=win.destroy).pack(pady=15)
            return

        # Tabelle für die Historie (NEU: 4 Spalten)
        columns = ("date", "action", "change", "cost")
        h_tree = ttk.Treeview(win, columns=columns, show="headings", height=10)
        h_tree.heading("date", text="Datum & Zeit")
        h_tree.heading("action", text="Aktion / Druck")
        h_tree.heading("change", text="Verbrauch")
        h_tree.heading("cost", text="Kosten (Material)")

        h_tree.column("date", width=120)
        h_tree.column("action", width=220)
        h_tree.column("change", width=80, anchor="e")
        h_tree.column("cost", width=100, anchor="e")

        # Wir drehen die Liste um (reversed), damit der neuste Eintrag ganz OBEN steht!
        for entry in reversed(history):
            h_tree.insert("", "end", values=(entry.get("date", ""), entry.get("action", ""), entry.get("change", ""), entry.get("cost", "-")))

        h_tree.pack(fill="both", expand=True, padx=15, pady=5)
        ttk.Button(win, text="Schließen", command=win.destroy).pack(pady=15)
    
    
    def on_tree_right_click(self, event):
        # Wo genau wurde geklickt?
        region = self.tree.identify("region", event.x, event.y)
        
        if region == "heading":
            # Klick auf den Tabellenkopf!
            self.menu_header.tk_popup(event.x_root, event.y_root)
            
        elif region == "cell" or region == "tree":
            # Klick auf eine Zeile! Wir markieren die Zeile automatisch.
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self.tree.selection_set(row_id)
                self.on_select(None)
                
                # --- FIX 1: Menü JEDES MAL neu aufbauen, damit es nie verschwindet! ---
                menu_row = tk.Menu(self.root, tearoff=0)
                menu_row.add_command(label="🛒 Im Shop öffnen", command=self.quick_open_shop)
                # --- NEU: Logbuch Button ---
                menu_row.add_command(label="📜 Spulen-Logbuch öffnen", command=self.show_spool_history)
                menu_row.add_separator()
                menu_row.add_command(label="🔄 Quick-Swap (ins AMS)", command=self.quick_swap_dialog)
                menu_row.add_command(label="🐑 Spule klonen", command=self.clone_filament)
                menu_row.add_separator()
                menu_row.add_command(label="📦 Ins Lager verschieben", command=self.send_to_storage)
                menu_row.add_command(label="🚮 Als LEER markieren", command=self.quick_mark_empty)
                menu_row.add_command(label="🛒 Auf Einkaufsliste setzen/entfernen", command=self.quick_toggle_reorder)
                menu_row.add_separator()
                menu_row.add_command(label="📝 Etikett-Vorschau öffnen", command=self.quick_open_label)
                menu_row.add_command(label="❌ Spule löschen", command=self.delete_filament)
                
                menu_row.tk_popup(event.x_root, event.y_root)

    # --- HILFSFUNKTIONEN FÜR DAS RECHTSKLICK-MENÜ ---
    def quick_mark_empty(self):
        sel = self.tree.selection()
        if not sel: return
        item = next((i for i in self.inventory if str(i.get('id')) == str(sel[0])), None)
        if item:
            # NEU: Verbrauch loggen, bevor er gelöscht wird!
            self.log_consumption(item.get('weight_gross', 0.0))
            
            item['type'] = "VERBRAUCHT"
            item['loc_id'] = "-"
            item['weight_gross'] = 0.0
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.clear_inputs()

    def quick_toggle_reorder(self):
        sel = self.tree.selection()
        if not sel: return
        item = next((i for i in self.inventory if str(i.get('id')) == str(sel[0])), None)
        if item:
            item['reorder'] = not item.get('reorder', False)
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.on_select(None) # Checkbox links aktualisieren

    def quick_open_label(self):
        # Öffnet den LabelCreator und wählt direkt diese Spule aus!
        sel = self.tree.selection()
        if not sel: return
        lbl_dialog = LabelCreatorDialog(self.root, self.inventory)
        
        # Simuliere einen Klick in der Liste des Label Creators
        for idx, listbox_item in enumerate(lbl_dialog.listbox.get(0, tk.END)):
            if listbox_item.startswith(f"[{sel[0]}]"):
                lbl_dialog.listbox.selection_set(idx)
                lbl_dialog.on_select(None)
                break

    def quick_open_shop(self):
        # 1. Wir schauen zuerst, ob im Eingabefeld ein Link steht (beim Bearbeiten)
        # Falls nicht, nehmen wir den Link der markierten Spule aus der Liste
        url = self.entry_link.get().strip()
        
        if not url:
            sel = self.tree.selection()
            if not sel: return
            item = next((i for i in self.inventory if str(i.get('id')) == str(sel[0])), None)
            if item and item.get('link'):
                url = item['link'].strip()

        if not url:
            messagebox.showinfo("Info", "Für dieses Filament ist leider kein Link hinterlegt.", parent=self.root)
            return
            
        # URL validieren
        url = url if url.startswith("http") else "https://" + url
        
        # --- AFFILIATE LOGIK (v1.9.9) ---
        if self.settings.get("use_affiliate", True):
            url_lower = url.lower()
            # Bambu Lab
            if "bambulab.com" in url_lower and "modelid=" not in url_lower: 
                url += ("&" if "?" in url else "?") + "modelId=1889832"
            # Amazon (Alle Domains & amzn.to Kurzlinks)
            elif ("amazon." in url_lower or "amzn.to" in url_lower) and "tag=" not in url_lower:
                url += ("&" if "?" in url else "?") + "tag=metmeyoumetwe-21"
                
        webbrowser.open(url)

    def log_consumption(self, amount_g, specific_date=None):
        import datetime
        import json
        import os
        
        if amount_g == 0: return 
        
        data_dir = getattr(self.data_manager, 'base_dir', '')
        history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
        
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except: pass
            
        # FIX: Wenn ein Datum übergeben wird, nimm das! Sonst nimm "Heute".
        today = specific_date if specific_date else datetime.date.today().isoformat()
        
        new_val = history.get(today, 0.0) + float(amount_g)
        history[today] = max(0.0, new_val)
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=4)

    def open_bambu_cloud_sync(self):
        """Versucht erst den direkten Token-Login, sonst Login-Maske."""
        saved_access_token = self.settings.get("bambu_cloud_access_token")
        
        if saved_access_token:
            def auto_login_thread():
                from core.bambu_cloud import BambuCloudAPI
                cloud = BambuCloudAPI()
                # Wir überspringen den Login komplett und setzen direkt den Schlüssel!
                cloud.set_auth_token(saved_access_token)
                
                # Testen, ob wir mit dem Token direkt an die Historie kommen
                h_success, h_data = cloud.fetch_print_history(limit=15)
                if h_success:
                    self.root.after(0, lambda: self._process_cloud_history(h_data, None))
                else:
                    # Nur wenn der 90-Tage-Schlüssel wirklich abgelaufen ist -> Login zeigen
                    self.root.after(0, self._show_cloud_login_dialog)

            threading.Thread(target=auto_login_thread, daemon=True).start()
        else:
            self._show_cloud_login_dialog()

    def _show_cloud_login_dialog(self):
        """Öffnet den Login-Dialog für die Bambu Cloud mit Passwort-Speicher-Option."""
        dialog = tk.Toplevel(self.root)
        dialog.title("☁️ Bambu Cloud Login")
        dialog.geometry("450x550")
        dialog.configure(bg=self.root.cget('bg'))
        center_window(dialog, self.root)
        
        ttk.Label(dialog, text="Bambu Cloud Login", font=("Segoe UI", 16, "bold"), foreground="#0078d7").pack(pady=(15, 5))
        
        frm = ttk.Frame(dialog, padding=20)
        frm.pack(fill="both", expand=True)
        
        ttk.Label(frm, text="Bambu E-Mail:").pack(anchor="w")
        ent_email = ttk.Entry(frm, width=40)
        ent_email.pack(fill="x", pady=(0, 10))
        ent_email.insert(0, self.settings.get("bambu_cloud_email", ""))
        
        ttk.Label(frm, text="Passwort:").pack(anchor="w")
        ent_pass = ttk.Entry(frm, width=40, show="*")
        ent_pass.pack(fill="x", pady=(0, 5))
        # Passwort laden falls gespeichert
        ent_pass.insert(0, self.settings.get("bambu_cloud_password", "")) 
        
        # NEU: Checkbox für Passwort speichern
        self.var_save_pass = tk.BooleanVar(value=True if self.settings.get("bambu_cloud_password") else False)
        chk_save = ttk.Checkbutton(frm, text="Passwort lokal speichern", variable=self.var_save_pass)
        chk_save.pack(anchor="w", pady=(0, 15))
        
        lbl_status = ttk.Label(frm, text="", foreground="#bbb", wraplength=350)
        lbl_status.pack(pady=5)

        def perform_sync():
            email = ent_email.get().strip()
            password = ent_pass.get().strip()
            
            if not email or not password:
                lbl_status.config(text="Bitte Daten eingeben!", foreground="red")
                return
            
            # Daten merken
            self.settings["bambu_cloud_email"] = email
            self.settings["bambu_cloud_password"] = password if self.var_save_pass.get() else ""
            self.data_manager.save_settings(self.settings)
            
            lbl_status.config(text="Verbindung wird aufgebaut...", foreground="#0078d7")
            
            def cloud_thread(auth_code=None):
                cloud = BambuCloudAPI()
                success, tokens = cloud.login(email, password, auth_code)
                
                if success and isinstance(tokens, dict):
                    # WICHTIG: Wir speichern den 90-Tage Access-Token!
                    self.settings["bambu_cloud_access_token"] = tokens.get("access", "")
                    self.data_manager.save_settings(self.settings)
                    
                    self.root.after(0, lambda: lbl_status.config(text="Lade Historie...", foreground="#0078d7"))
                    h_success, h_data = cloud.fetch_print_history(limit=15)
                    if h_success:
                        self.root.after(0, lambda: self._process_cloud_history(h_data, dialog))
                else:
                    msg_str = str(tokens).lower()
                    if tokens == "2FA_REQUIRED" or "code" in msg_str:
                        self.root.after(0, ask_for_2fa)
                    else:
                        self.root.after(0, lambda: lbl_status.config(text=f"Fehler: {tokens}", foreground="red"))

            def ask_for_2fa():
                code = simpledialog.askstring("🔒 Bambu 2FA", "Code aus der E-Mail eingeben:", parent=dialog)
                if code:
                    lbl_status.config(text="Prüfe Code...", foreground="#0078d7")
                    threading.Thread(target=lambda: cloud_thread(code), daemon=True).start()

            threading.Thread(target=lambda: cloud_thread(None), daemon=True).start()

        ttk.Button(frm, text="🔄 Login mit E-Mail & Passwort", command=perform_sync, style="Accent.TButton").pack(fill="x", pady=10)

        # --- NEU: DER BROWSER-LOGIN BEREICH ---
        ttk.Separator(frm, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(frm, text="Alternative: Sicherer Browser-Login", font=("Segoe UI", 9, "bold")).pack(pady=(0,5))
        
        def start_browser_login():
            lbl_status.config(text="🌐 Bitte im Browser anmelden...", foreground="#0078d7")
            
            def on_complete(success, message):
                if success:
                    # Token in Settings speichern
                    self.settings["bambu_cloud_access_token"] = message
                    self.data_manager.save_settings(self.settings)
                    lbl_status.config(text="✅ Login erfolgreich! Lade Daten...", foreground="green")
                    
                    # Historie direkt laden
                    cloud = BambuCloudAPI()
                    cloud.set_auth_token(message)
                    h_success, h_data = cloud.fetch_print_history(limit=15)
                    if h_success:
                        self.root.after(0, lambda: self._process_cloud_history(h_data, dialog))
                else:
                    lbl_status.config(text=f"❌ Fehler: {message}", foreground="red")

            cloud_api = BambuCloudAPI()
            cloud_api.login_via_browser(on_complete)

        ttk.Button(frm, text="🌐 Anmelden via MakerWorld / Bambu Lab", command=start_browser_login).pack(fill="x", pady=5)

    def _ask_for_smart_deduction(self, job, parent_win, tree_widget, refresh_tree=None):
        job_id = str(job.get('id', ''))
        
        # --- FIX 1: Original-Datum des Drucks aus der Cloud holen! ---
        from datetime import datetime
        job_date_str = job.get('date', datetime.now().strftime("%Y-%m-%d %H:%M"))
        job_day = job_date_str.split(" ")[0] # Zieht nur das Datum (YYYY-MM-DD) für das Chart heraus
        
        side_panel = getattr(parent_win, 'side_panel', None)
        main_content = getattr(parent_win, 'main_content', None)
        if not side_panel or not main_content: return
        
        for widget in side_panel.winfo_children():
            widget.destroy()
            
        side_panel.pack(side="right", fill="y", before=main_content)
        
        header = ttk.Frame(side_panel)
        header.pack(fill="x", pady=10, padx=10)
        ttk.Label(header, text="🧠 Smart-Match", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(header, text="❌", width=3, command=side_panel.pack_forget).pack(side="right")
        ttk.Separator(side_panel, orient="horizontal").pack(fill="x")

        content_frm = ttk.Frame(side_panel, padding=15)
        content_frm.pack(fill="both", expand=True)

        model = job['name']
        total_weight = job['weight']
        mappings = job.get('mapping', [])

        ttk.Label(content_frm, text=f"{model}", font=("Segoe UI", 11, "bold"), wraplength=400, justify="center").pack(pady=(5, 5))
        
        # Sicherstellen, dass Dauer eine Float-Zahl ist
        try: duration = float(job.get('duration_h', 0.0) or 0.0)
        except: duration = 0.0
        
        kwh_price = float(self.settings.get("kwh_price", 0.30))
        watts = int(self.settings.get("printer_watts", 150))
        strom_kosten = duration * (watts / 1000.0) * kwh_price
        
        info_str = f"Verbrauch: {total_weight}g"
        if duration > 0: info_str += f"\nZeit: {duration:.1f}h | Strom: {strom_kosten:.2f} €"
        ttk.Label(content_frm, text=info_str, font=("Segoe UI", 9), foreground="#0078D7", justify="center").pack(pady=5)

        from core.logic import calculate_net_weight
        spool_list = []
        for s in self.inventory:
            if s.get('type') == 'VERBRAUCHT': continue
            net = calculate_net_weight(s.get('weight_gross', '0'), s.get('spool_id', -1), self.spools, s.get('empty_weight'))
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', s.get('color', '')).strip()
            spool_list.append(f"[{s['id']}] {s.get('brand')} {color_clean} ({net}g übrig)")

        if not mappings:
            mappings = [{"ams": -1, "weight": total_weight}]
            
        valid_mappings = [m for m in mappings if m.get('weight', 0) > 0]
        if not valid_mappings:
            valid_mappings = [{"ams": -1, "weight": total_weight}]

        entries = []
        for m in valid_mappings:
            row = ttk.Frame(content_frm)
            row.pack(fill="x", pady=5)
            
            raw_ams = m.get('ams', -1)
            weight = round(m.get('weight', 0.0), 1)
            best_match = None
            lbl_text = "Unbekannt:"
            
            if raw_ams >= 0:
                ams_num = (raw_ams // 4) + 1
                slot_num = (raw_ams % 4) + 1
                ams_name = f"AMS {ams_num}"
                lbl_text = f"{ams_name} Slot {slot_num}:"
                best_match = next((s for s in self.inventory if s.get('type') == ams_name and str(s.get('loc_id')) == str(slot_num)), None)

            ttk.Label(row, text=lbl_text, width=12, font=("Segoe UI", 9, "bold")).pack(side="left")
            
            combo = ttk.Combobox(row, values=spool_list, width=28, font=("Segoe UI", 9))
            combo.pack(side="left", padx=5)
            
            if best_match:
                net_match = calculate_net_weight(best_match.get('weight_gross', '0'), best_match.get('spool_id', -1), self.spools, best_match.get('empty_weight'))
                color_match = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', best_match.get('color', '')).strip()
                match_str = f"[{best_match['id']}] {best_match.get('brand')} {color_match} ({net_match}g übrig)"
                if match_str in spool_list: combo.set(match_str)
            elif spool_list: combo.current(0)
                
            ent_w = ttk.Entry(row, width=6, justify="right", font=("Segoe UI", 9, "bold"))
            ent_w.pack(side="left")
            ent_w.insert(0, str(weight))
            ttk.Label(row, text="g").pack(side="left")
            
            entries.append({"combo": combo, "weight_entry": ent_w})

        def confirm():
            total_deducted = 0
            for e in entries:
                sel = e["combo"].get()
                try: w_val = float(e["weight_entry"].get().replace(',', '.'))
                except ValueError: continue
                
                if w_val <= 0: continue
                
                if sel and sel.startswith("["):
                    spool_id = sel.split("]")[0][1:]
                    item = next((i for i in self.inventory if str(i['id']) == spool_id), None)
                    if item:
                        old_gross = float(item.get('weight_gross', 0.0))
                        item['weight_gross'] = round(max(0.0, old_gross - w_val), 1)

                        mat_cost = 0.0
                        try:
                            sp_price = float(str(item.get('price', '0')).replace(',', '.')) or 0.0
                            sp_cap = float(str(item.get('capacity', '1000'))) or 1000.0
                            if sp_cap > 0: mat_cost = w_val * (sp_price / sp_cap)
                        except: pass

                        anteil = w_val / total_weight if total_weight > 0 else 1.0
                        wear_price = float(self.settings.get("wear_per_hour", 0.20))
                        
                        echte_kosten = mat_cost + (strom_kosten * anteil) + ((duration * wear_price) * anteil)
                        margin_percent = int(self.settings.get("profit_margin", 0))
                        vk_preis = echte_kosten * (1 + (margin_percent / 100.0))

                        if "history" not in item: item["history"] = []
                        item["history"].append({
                            "date": job_date_str, # <--- FIX 2: Original Datum des Drucks schreiben!
                            "action": f"Cloud: {model}",
                            "change": f"-{w_val}g",
                            "cost": f"{echte_kosten:.2f} €",
                            "sell_price": f"{vk_preis:.2f} €" if margin_percent > 0 else "-"
                        })
                        total_deducted += w_val

            if total_deducted > 0:
                # FIX 3: Den Tages-Verbrauch an das richtige Datum im Balkendiagramm schicken!
                self.log_consumption(total_deducted, specific_date=job_day)
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                
                deducted = self.settings.get("deducted_cloud_jobs", [])
                if job_id not in deducted:
                    deducted.append(job_id)
                    self.settings["deducted_cloud_jobs"] = deducted
                    self.data_manager.save_settings(self.settings)
                
                if refresh_tree:
                    try: refresh_tree() 
                    except Exception: pass
                
                side_panel.pack_forget()
                anteil = total_deducted / total_weight if total_weight > 0 else 1.0
                self.show_custom_toast("💰 Filament verrechnet", f"Verbrauch: {total_deducted:.1f}g\nGesamtkosten: {mat_cost + (strom_kosten * anteil):.2f} €")
            else:
                messagebox.showerror("Fehler", "Es wurden keine gültigen Gewichte eingetragen.", parent=parent_win)

        ttk.Button(content_frm, text="✅ Jetzt Abziehen", style="Accent.TButton", command=confirm).pack(side="bottom", pady=15)

    def _build_cloud_deduction_ui(self, content, job, parent_win, tree_widget, refresh_tree=None):

        model = job['name']
        total_weight = job['weight']
        mappings = job.get('mapping', [])
        job_id = str(job.get('id', ''))

        ttk.Label(content, text=f"Druck: {model}", font=("Segoe UI", 12, "bold"), wraplength=350, justify="center").pack(pady=(10, 5))
        
        # --- NEU: Stromkosten berechnen ---
        duration = job.get('duration_h', 0.0)
        kwh_price = float(self.settings.get("kwh_price", 0.30))
        watts = int(self.settings.get("printer_watts", 150))
        strom_kosten = duration * (watts / 1000.0) * kwh_price
        
        info_str = f"Verbrauch: {total_weight}g"
        if duration > 0: info_str += f"  |  Zeit: {duration:.1f}h  |  Strom: {strom_kosten:.2f} €"
        ttk.Label(content, text=info_str, font=("Segoe UI", 10), foreground="#0078D7", justify="center", wraplength=350).pack(pady=5)

        frm = ttk.LabelFrame(content, text="Verwendete Spulen zuweisen", padding=10)
        frm.pack(fill="both", expand=True, pady=10)

        # 1. Spulen-Liste formatieren
        from core.logic import calculate_net_weight
        spool_list = []
        for s in self.inventory:
            if s.get('type') == 'VERBRAUCHT': continue
            net = calculate_net_weight(s.get('weight_gross', '0'), s.get('spool_id', -1), self.spools, s.get('empty_weight'))
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', s.get('color', '')).strip()
            spool_list.append(f"[{s['id']}] {s.get('brand')} {color_clean} ({net}g)")

        # 2. Multi-Color Fallback (Falls API keine Daten liefert)
        if not mappings:
            mappings = [{"ams": -1, "weight": total_weight}]
            
        valid_mappings = [m for m in mappings if m.get('weight', 0) > 0]
        if not valid_mappings:
            valid_mappings = [{"ams": -1, "weight": total_weight}]

        entries = []
        
        # 3. Für JEDE vom Drucker gemeldete Farbe eine Zeile generieren!
        for m in valid_mappings:
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=5)
            
            raw_ams = m.get('ams', -1)
            weight = round(m.get('weight', 0.0), 1)
            
            best_match = None
            lbl_text = "Unbekannt:"
            
            if raw_ams >= 0:
                # Bambu API: 0-3 = AMS 1, 4-7 = AMS 2 usw.
                ams_num = (raw_ams // 4) + 1
                slot_num = (raw_ams % 4) + 1
                ams_name = f"AMS {ams_num}"
                lbl_text = f"{ams_name} Slot {slot_num}:"
                
                # Wir suchen direkt, was aktuell in VibeSpool auf diesem Slot liegt!
                best_match = next((s for s in self.inventory if s.get('type') == ams_name and str(s.get('loc_id')) == str(slot_num)), None)

            ttk.Label(row, text=lbl_text, width=12, font=("Segoe UI", 9, "bold")).pack(side="left")
            
            combo = ttk.Combobox(row, values=spool_list, width=22, font=("Segoe UI", 9))
            combo.pack(side="left", padx=5, fill="x", expand=True)
            
            # Die vorgeschlagene Spule automatisch eintragen
            if best_match:
                net_match = calculate_net_weight(best_match.get('weight_gross', '0'), best_match.get('spool_id', -1), self.spools, best_match.get('empty_weight'))
                color_match = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', best_match.get('color', '')).strip()
                match_str = f"[{best_match['id']}] {best_match.get('brand')} {color_match} ({net_match}g)"
                
                for sp_item in spool_list:
                    if sp_item.startswith(f"[{best_match['id']}]"):
                        combo.set(sp_item)
                        break
            elif spool_list:
                combo.current(0)
                
            ent_w = ttk.Entry(row, width=6, justify="right", font=("Segoe UI", 9, "bold"))
            ent_w.pack(side="left")
            ent_w.insert(0, str(weight))
            ttk.Label(row, text=" g").pack(side="left")
            
            entries.append({"combo": combo, "weight_entry": ent_w})

        def confirm():
            total_deducted = 0
            mat_cost = 0.0
            for e in entries:
                sel = e["combo"].get()
                try:
                    w_val = float(e["weight_entry"].get().replace(',', '.'))
                except ValueError: continue
                
                if w_val <= 0: continue
                
                if sel and sel.startswith("["):
                    spool_id = sel.split("]")[0][1:]
                    item = next((i for i in self.inventory if str(i['id']) == spool_id), None)
                    if item:
                        old_gross = float(item.get('weight_gross', 0.0))
                        new_gross = max(0.0, old_gross - w_val)
                        item['weight_gross'] = round(new_gross, 1)

                        # --- Kosten exakt berechnen! ---
                        spool_mat_cost = 0.0
                        try:
                            spool_price = float(str(item.get('price', '0')).replace(',', '.')) or 0.0
                            spool_capacity = float(str(item.get('capacity', '1000'))) or 1000.0
                            if spool_capacity > 0: spool_mat_cost = w_val * (spool_price / spool_capacity)
                        except: pass
                        
                        mat_cost += spool_mat_cost

                        # Strom, Verschleiß & Marge anteilig berechnen (wichtig bei Multi-Color!)
                        anteil = w_val / total_weight if total_weight > 0 else 1.0
                        strom_anteil = strom_kosten * anteil
                        
                        wear_price = float(self.settings.get("wear_per_hour", 0.20))
                        wear_anteil = (duration * wear_price) * anteil
                        
                        echte_kosten = spool_mat_cost + strom_anteil + wear_anteil
                        
                        margin_percent = int(self.settings.get("profit_margin", 0))
                        vk_preis = echte_kosten * (1 + (margin_percent / 100.0))

                        if "history" not in item: item["history"] = []
                        item["history"].append({
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "action": f"Cloud: {model}",
                            "change": f"-{w_val}g",
                            "cost": f"{echte_kosten:.2f} €",
                            "sell_price": f"{vk_preis:.2f} €" if margin_percent > 0 else "-" # VK-Preis speichern!
                        })
                        total_deducted += w_val

            if total_deducted > 0:
                # --- FIX: Den Cloud-Verbrauch auch an das Balkendiagramm senden! ---
                self.log_consumption(total_deducted)
                
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                
                # Den Druck in der "Erledigt"-Liste speichern
                deducted = self.settings.get("deducted_cloud_jobs", [])
                if job_id not in deducted:
                    deducted.append(job_id)
                    self.settings["deducted_cloud_jobs"] = deducted
                    self.data_manager.save_settings(self.settings)
                
                # NEU: Wir rufen die übergebene Refresh-Funktion der Hauptliste auf!
                if refresh_tree:
                    try: 
                        refresh_tree() 
                    except Exception: 
                        pass
                
                self.toggle_side_panel(force_close=True)
                
                anteil = total_deducted / total_weight if total_weight > 0 else 1.0
                gesamt_kosten = mat_cost + (strom_kosten * anteil)
                self.show_custom_toast("💰 Filament verrechnet", f"Verbrauch: {total_deducted:.1f}g\nGesamtkosten (Material + Strom): {gesamt_kosten:.2f} €")
            else:
                from tkinter import messagebox
                messagebox.showerror("Fehler", "Es wurden keine gültigen Gewichte eingetragen.", parent=self.root)

        ttk.Button(content, text="✅ Jetzt Abziehen", style="Accent.TButton", command=confirm).pack(pady=(10, 15), fill="x")
    
    def _process_cloud_history(self, history_data, dialog):
        """Zeigt die Cloud-Historie mit Status-Tracking und Filter-Option an."""
        if dialog: dialog.destroy()
            
        win = tk.Toplevel(self.root)
        win.title("📋 Cloud Historie - Zuweisen oder Ignorieren")
        win.geometry("1100x650") # Breiter für das Side-Panel
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        from core.utils import center_window
        center_window(win, self.root)
        
        # --- NEU: Master Layout für internes Side-Panel (Pylance-Safe!) ---
        master_frame = ttk.Frame(win)
        master_frame.pack(fill="both", expand=True)
        setattr(win, 'master_frame', master_frame)
        
        side_panel = ttk.Frame(master_frame, width=450, relief="solid", borderwidth=1)
        side_panel.pack_propagate(False)
        setattr(win, 'side_panel', side_panel)
        
        main_content = ttk.Frame(master_frame)
        main_content.pack(side="left", fill="both", expand=True)
        setattr(win, 'main_content', main_content)
        
        # --- Kopfzeile mit Titel und Filter ---
        header = ttk.Frame(main_content)
        header.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(header, text="Letzte erfolgreiche Druckaufträge aus der Cloud:", font=("Segoe UI", 12, "bold")).pack(side="left")
        
        self.var_hide_completed = tk.BooleanVar(value=self.settings.get("hide_completed_cloud_jobs", False))
        
        def toggle_filter():
            self.settings["hide_completed_cloud_jobs"] = self.var_hide_completed.get()
            self.data_manager.save_settings(self.settings)
            refresh_tree()

        chk_hide = ttk.Checkbutton(header, text="Erledigte/Ignorierte ausblenden", variable=self.var_hide_completed, command=toggle_filter)
        chk_hide.pack(side="right", padx=10)
        
        # --- Die Tabelle ---
        columns = ("status", "name", "weight", "date")
        tree = ttk.Treeview(main_content, columns=columns, show="headings", height=15)
        tree.heading("status", text="Status")
        tree.heading("name", text="Modell")
        tree.heading("weight", text="Verbrauch")
        tree.heading("date", text="Datum/Zeit")
        
        tree.column("status", width=120, anchor="center")
        tree.column("name", width=380)
        tree.column("weight", width=80, anchor="e")
        tree.column("date", width=140)
        
        tree.tag_configure("done", foreground="#28a745")
        tree.tag_configure("ignored", foreground="#6c757d")
        
        self.current_cloud_jobs = {str(job.get('id', '')): job for job in history_data if 'id' in job}

        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            
            deducted = self.settings.get("deducted_cloud_jobs", [])
            ignored = self.settings.get("ignored_cloud_jobs", [])
            hide = self.var_hide_completed.get()
            
            for job in history_data:
                job_id = str(job.get('id', ''))
                if not job_id: continue
                
                is_done = job_id in deducted
                is_ignored = job_id in ignored
                
                if hide and (is_done or is_ignored): continue
                
                if is_done:
                    stat, tags = "✅ Abgezogen", ("done",)
                elif is_ignored:
                    stat, tags = "🚫 Ignoriert", ("ignored",)
                else:
                    stat, tags = "Offen", ()
                
                tree.insert("", "end", iid=job_id, values=(stat, job['name'], f"{job['weight']:.1f} g", job['date']), tags=tags)

        btn_frame = ttk.Frame(main_content)
        btn_frame.pack(fill="x", side="bottom", padx=10, pady=15)

        def on_deduct_click(event=None):
            sel = tree.selection()
            if not sel: return
            job_id = sel[0]
            job = self.current_cloud_jobs[job_id]
            self._ask_for_smart_deduction(job, win, tree, refresh_tree)

        def on_ignore_toggle():
            sel = tree.selection()
            if not sel: return
            job_id = sel[0]
            ignored = self.settings.get("ignored_cloud_jobs", [])
            if job_id in ignored: ignored.remove(job_id)
            else:
                ignored.append(job_id)
                deducted = self.settings.get("deducted_cloud_jobs", [])
                if job_id in deducted: deducted.remove(job_id)
            self.settings["ignored_cloud_jobs"] = ignored
            self.data_manager.save_settings(self.settings)
            refresh_tree() 

        tree.bind("<Double-1>", on_deduct_click)
        ttk.Button(btn_frame, text="✅ Abziehen", style="Accent.TButton", command=on_deduct_click).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🚫 Ignorieren", command=on_ignore_toggle).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Schließen", command=win.destroy).pack(side="right", padx=5)
        
        tree.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        refresh_tree()

    def broadcast_mqtt(self):
        # 1. Ist MQTT überhaupt aktiviert?
        if not self.settings.get("mqtt_enable", False):
            return
            
        host = self.settings.get("mqtt_host", "")
        if not host: return
        
        # 2. Daten für Home Assistant sammeln und verpacken
        from core.logic import calculate_net_weight
        import json
        import threading
        import os
        
        total_spools = 0
        total_net_weight = 0
        low_spools = []
        ams_data = {}
        
        for item in self.inventory:
            if item.get('type') == 'VERBRAUCHT': continue
            total_spools += 1
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools, item.get('empty_weight'))
            total_net_weight += net
            
            # Alarm für fast leere Spulen (< 100g)
            if net > 0 and net < 100:
                low_spools.append({
                    "id": item['id'], 
                    "name": f"{item.get('brand', '')} {item.get('color', '')}", 
                    "net": int(net),
                    "loc": f"{item.get('type', '')} {item.get('loc_id', '')}"
                })
            
            # AMS Belegung auslesen
            loc_type = str(item.get('type', ''))
            if loc_type.startswith("AMS"):
                slot = str(item.get('loc_id', ''))
                # Formatiert z.B. "AMS 1" -> "AMS_1_Slot_3"
                ams_key = f"{loc_type.replace(' ', '_')}_Slot_{slot}"
                ams_data[ams_key] = {
                    "id": item['id'],
                    "name": f"{item.get('brand', '')} {item.get('color', '')}",
                    "material": item.get('material', ''),
                    "net": int(net)
                }

        payload = {
            "total_spools": total_spools,
            "total_weight_g": int(total_net_weight),
            "low_spools": low_spools,
            "low_spools_count": len(low_spools),
            "ams": ams_data
        }
        
        # --- NEU: OFFLINE BUFFER LOGIK ---
        data_dir = getattr(self.data_manager, 'base_dir', '')
        buffer_file = os.path.join(data_dir, "mqtt_buffer.json") if data_dir else "mqtt_buffer.json"
        
        # Wir speichern IMMER den aktuellsten Stand in den Puffer
        try:
            with open(buffer_file, "w") as f:
                json.dump(payload, f)
        except: pass

        # Wenn der Retry-Thread schon läuft, müssen wir keinen neuen starten.
        # Er schnappt sich beim nächsten Durchlauf automatisch die aktualisierte Datei!
        if getattr(self, 'mqtt_retry_active', False):
            return

        # 3. Den Funker-Thread starten (damit die UI nicht hängt)
        def send_task():
            self.mqtt_retry_active = True
            import paho.mqtt.publish as publish
            import time
            
            port = int(self.settings.get("mqtt_port", "1883"))
            user = self.settings.get("mqtt_user", "")
            password = self.settings.get("mqtt_pass", "")
            
            auth = None
            if user or password:
                auth = {'username': user, 'password': password}
                
            # Die Endlos-Schleife für den Puffer
            while True:
                if not os.path.exists(buffer_file):
                    break # Nichts mehr zu tun!
                    
                try:
                    # Lade immer den FRISCHESTEN Stand aus der Datei
                    with open(buffer_file, "r") as f:
                        current_payload = json.load(f)
                        
                    publish.single(
                        topic="vibespool/state",
                        payload=json.dumps(current_payload),
                        hostname=host,
                        port=port, 
                        auth=auth, # type: ignore
                        retain=True, # WICHTIG: Home Assistant merkt sich den Wert!
                        client_id="VibeSpool_App"
                    )
                    
                    # Erfolgreich gesendet! Puffer löschen und Schleife beenden
                    os.remove(buffer_file)
                    break
                    
                except Exception as e:
                    print(f"MQTT Broker nicht erreichbar. Neuer Versuch in 30 Sekunden... ({e})")
                    time.sleep(30) # Warte 30 Sekunden im Hintergrund
                    
            self.mqtt_retry_active = False
                
        threading.Thread(target=send_task, daemon=True).start() 
if __name__ == "__main__":
    import socket
    import sys
    from tkinter import messagebox
    
    # Verhindert den Mehrfach-Start (Single Instance Lock)
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(('127.0.0.1', 47200))
    except socket.error:
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showinfo("VibeSpool läuft bereits", "VibeSpool ist bereits im Hintergrund geöffnet!\n\nBitte schaue in deiner Taskleiste (unten rechts neben der Uhr) nach dem blauen VibeSpool-Icon.")
        sys.exit()

    try: windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    
    root = tk.Tk()
    app = FilamentApp(root)
    root.mainloop()
