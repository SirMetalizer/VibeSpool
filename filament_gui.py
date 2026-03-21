import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
import json
import os
import shutil
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

# --- KONFIGURATION & UPDATE CHECKER ---
APP_VERSION = "1.7"
GITHUB_REPO = "SirMetalizer/VibeSpool" 

# --- SICHERER SPEICHERORT FÜR EXE & MAC APP ---
USER_HOME = os.path.expanduser("~")
BASE_DIR = os.path.join(USER_HOME, "VibeSpool_Daten") 

possible_docs = [
    os.path.join(USER_HOME, "OneDrive", "Documents"),
    os.path.join(USER_HOME, "OneDrive", "Dokumente"),
    os.path.join(USER_HOME, "Documents"),
    os.path.join(USER_HOME, "Dokumente")
]

for path in possible_docs:
    if os.path.exists(path):
        BASE_DIR = os.path.join(path, "VibeSpool")
        break
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# --- PRÜFEN, OB EIN EIGENER SPEICHERORT EINGESTELLT WURDE ---
_temp_set = {}
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f: _temp_set = json.load(f)
    except: pass

CUSTOM_DB_PATH = _temp_set.get("custom_db_path", "")
if CUSTOM_DB_PATH and os.path.exists(CUSTOM_DB_PATH):
    DATA_FILE = os.path.join(CUSTOM_DB_PATH, "inventory.json")
    SPOOLS_FILE = os.path.join(CUSTOM_DB_PATH, "spools.json")
else:
    DATA_FILE = os.path.join(BASE_DIR, "inventory.json")
    SPOOLS_FILE = os.path.join(BASE_DIR, "spools.json")

# --- DEFAULTS ---
DEFAULT_SETTINGS = {
    "shelves": "REGAL|4|8", 
    "logistics_order": False,
    "label_row": "Fach",
    "label_col": "Slot",
    "num_ams": 1,
    "custom_locs": "Filamenttrockner",
    # --- WICHTIG: Fensterhöhe drastisch erhöht (980) ---
    "geometry": "1500x980", 
    "theme": "dark",
    "use_affiliate": True
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
COLOR_MAP = {
    "rot": "#FF0000", "red": "#FF0000", "maroon": "#800000", 
    "blau": "#0000FF", "blue": "#0000FF", "navy": "#000080", "light blue": "#ADD8E6",
    "grün": "#008000", "green": "#008000", "dark green": "#006400", "olive": "#808000", "mint": "#98FF98", "jade": "#00A86B",
    "gelb": "#FFD700", "yellow": "#FFD700", 
    "orange": "#FFA500", "terracotta": "#E2725B", 
    "lila": "#800080", "purple": "#800080", "plum": "#8E4585", "pflaume": "#8E4585", "lavendel": "#E6E6FA", "lavender": "#E6E6FA",
    "pink": "#FFC0CB", "rosa": "#FFC0CB", "rose": "#FF007F", "magenta": "#FF00FF", 
    "schwarz": "#000000", "black": "#000000", 
    "weiß": "#F0F0F0", "white": "#F0F0F0", 
    "grau": "#808080", "grey": "#808080", "gray": "#808080", "ash": "#B2BEB5", 
    "silber": "#C0C0C0", "silver": "#C0C0C0", 
    "braun": "#A52A2A", "brown": "#A52A2A", "beige": "#F5F5DC", "wood": "#D2B48C", "holz": "#D2B48C",
    "gold": "#DAA520", "bronze": "#CD7F32", "kupfer": "#B87333", "copper": "#B87333", 
    "cyan": "#00FFFF", "türkis": "#40E0D0", "turquoise": "#40E0D0", 
    "rainbow": "RAINBOW", "regenbogen": "RAINBOW",
    "transparent": "#E8F4F8", "translucent": "#E8F4F8", "clear": "#E8F4F8",
    "marmor": "#E0E0E0", "marble": "#E0E0E0", "glow": "#CCFF00"
}

# --- HELPER ---
def load_json(filename, default):
    if not os.path.exists(filename): return default
    try:
        with open(filename, "r", encoding="utf-8") as f: 
            data = json.load(f)
            if isinstance(default, dict) and isinstance(data, dict):
                merged = default.copy(); merged.update(data); return merged
            return data
    except: return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    except Exception as e: print(e)

def get_colors_from_text(text):
    hex_matches = re.findall(r'(#[0-9a-fA-F]{6})', text)
    if hex_matches: return hex_matches 
    text_lower = text.lower().strip()
    if any(x in text_lower for x in ["regenbogen", "rainbow", "bunt"]):
        return ["#FF0000", "#FFA500", "#FFFF00", "#008000", "#0000FF", "#4B0082", "#EE82EE"]
    keys = sorted(COLOR_MAP.keys(), key=len, reverse=True)
    temp_text, matches = text_lower, {}
    for key in keys:
        if key in temp_text:
            idx = temp_text.find(key)
            matches[idx] = COLOR_MAP[key]
            temp_text = temp_text.replace(key, " " * len(key), 1)
    return [matches[i] for i in sorted(matches.keys())]

def create_color_icon(hex_list, size=(24, 24), outline_color="#CCCCCC"):
    if not hex_list:
        img = Image.new("RGB", size, "#D2B48C") 
        return ImageTk.PhotoImage(img)
    img = Image.new("RGB", size, "#FFFFFF")
    draw = ImageDraw.Draw(img); width, height = size; step = width / len(hex_list)
    for i, color in enumerate(hex_list):
        x0 = i * step; x1 = (i + 1) * step
        if not color.startswith("#"): color = "#333" 
        draw.rectangle([x0, 0, x1, height], fill=color)
    draw.rectangle([0, 0, width-1, height-1], outline=outline_color, width=1)
    return ImageTk.PhotoImage(img)

def center_window(window, parent):
    window.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (window.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (window.winfo_height() // 2)
    window.geometry(f"+{x}+{y}")

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")

# --- FENSTER KLASSEN ---
class SpoolManager(tk.Toplevel):
    def __init__(self, parent, on_close_callback):
        super().__init__(parent)
        self.on_close_callback = on_close_callback; self.title("Spulen Datenbank")
        self.geometry("600x700"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        
        self.spools = load_json(SPOOLS_FILE, [])
        ttk.Label(self, text="Verfügbare Leerspulen", font=("Segoe UI", 10, "bold")).pack(pady=10)
        frm_list = ttk.Frame(self); frm_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.tree = ttk.Treeview(frm_list, columns=("id", "name", "weight"), show="headings")
        self.tree.heading("id", text="ID"); self.tree.heading("name", text="Bezeichnung"); self.tree.heading("weight", text="Leergewicht (g)")
        self.tree.column("id", width=50, anchor="center"); self.tree.column("name", width=250); self.tree.column("weight", width=100, anchor="center")
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set); self.tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
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
        self.refresh_list()
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
            self.spools.append({"id": new_id, "name": name, "weight": weight}); save_json(SPOOLS_FILE, self.spools); self.refresh_list()
        except: pass
    def update_spool(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            weight = int(float(self.ent_weight.get().strip().replace(',', '.')))
            for s in self.spools:
                if s['id'] == int(sel[0]): s['name'] = self.ent_name.get().strip(); s['weight'] = weight
            save_json(SPOOLS_FILE, self.spools); self.refresh_list()
        except: pass
    def delete_spool(self):
        sel = self.tree.selection()
        if not sel: return
        self.spools = [s for s in self.spools if s['id'] != int(sel[0])]; save_json(SPOOLS_FILE, self.spools); self.refresh_list()
    def destroy(self): self.on_close_callback(); super().destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_settings, on_save):
        super().__init__(parent)
        self.on_save = on_save; self.current_settings = current_settings; self.title("Einstellungen & Lagerorte")
        # --- WICHTIG: Fensterhöhe drastisch erhöht (820) ---
        self.geometry("500x820"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        
        ttk.Label(self, text="Multi-Regal Layout & Lagerorte", font=("Segoe UI", 12, "bold")).pack(pady=10)
        frm = ttk.Frame(self); frm.pack(padx=20, pady=5, fill="both", expand=True)
        ttk.Label(frm, text="Regale (Name|Zeilen|Spalten):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_shelves = ttk.Entry(frm, width=30); self.ent_shelves.insert(0, current_settings.get("shelves", "REGAL|4|8")); self.ent_shelves.grid(row=0, column=1, pady=5, sticky="w")
        ttk.Label(frm, text="Kommagetrennt für mehrere!\nBeispiel: REGAL|4|8, REGAL NEU|6|12").grid(row=1, column=1, sticky="w", pady=(0, 5))
        self.var_logistics = tk.BooleanVar(value=current_settings.get("logistics_order", False)); ttk.Checkbutton(frm, text="Logistik-Standard (Zählung von unten nach oben)", variable=self.var_logistics).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        ttk.Label(frm, text="Benennung Zeile:").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_lbl_row = ttk.Entry(frm, width=15); self.ent_lbl_row.insert(0, current_settings.get("label_row", "Fach")); self.ent_lbl_row.grid(row=3, column=1, sticky="w")
        ttk.Label(frm, text="Benennung Spalte:").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_lbl_col = ttk.Entry(frm, width=15); self.ent_lbl_col.insert(0, current_settings.get("label_col", "Slot")); self.ent_lbl_col.grid(row=4, column=1, sticky="w")
        ttk.Label(frm, text="Anzahl AMS Geräte:").grid(row=5, column=0, sticky="w", pady=(20,5))
        self.ent_ams = ttk.Entry(frm, width=10); self.ent_ams.insert(0, str(current_settings.get("num_ams", 1))); self.ent_ams.grid(row=5, column=1, sticky="w", pady=(20,5))
        ttk.Label(frm, text="Weitere Orte (Kommagetrennt):").grid(row=6, column=0, sticky="w", pady=5)
        self.ent_custom = ttk.Entry(frm); self.ent_custom.insert(0, current_settings.get("custom_locs", "Filamenttrockner")); self.ent_custom.grid(row=6, column=1, sticky="ew", pady=5)
        ttk.Label(frm, text="Beispiel: Samla Box, Filamenttrockner, Keller").grid(row=7, column=1, sticky="w", pady=(0, 10))
        ttk.Label(frm, text="Datenbank-Ordner:").grid(row=8, column=0, sticky="nw", pady=5); path_frm = ttk.Frame(frm); path_frm.grid(row=8, column=1, sticky="ew", pady=5)
        show_path = current_settings.get("custom_db_path", "") or "Standard (Dokumente)"; self.lbl_path = ttk.Label(path_frm, text=show_path, font=("Segoe UI", 8, "italic"), wraplength=350); self.lbl_path.pack(fill="x", pady=(0, 5))
        btn_path_frm = ttk.Frame(path_frm); btn_path_frm.pack(fill="x")
        def choose_path():
            d = filedialog.askdirectory(title="Neuen Speicherort für Datenbank wählen")
            if d: self.current_settings["custom_db_path"] = d; self.lbl_path.config(text=d); messagebox.showinfo("Wichtig", "Der neue Pfad wird beim Speichern übernommen.\nBitte starte VibeSpool danach einmal neu!", parent=self)
        def reset_path(): self.current_settings["custom_db_path"] = ""; self.lbl_path.config(text="Standard (Dokumente)"); messagebox.showinfo("Wichtig", "Pfad wurde zurückgesetzt.\nBitte starte VibeSpool nach dem Speichern neu!", parent=self)
        ttk.Button(btn_path_frm, text="Ordner ändern", command=choose_path).pack(side="left", padx=(0, 5)); ttk.Button(btn_path_frm, text="Standard verwenden", command=reset_path).pack(side="left")
        ttk.Separator(frm, orient="horizontal").grid(row=9, column=0, columnspan=2, sticky="ew", pady=15)
        self.var_affiliate = tk.BooleanVar(value=current_settings.get("use_affiliate", True)); ttk.Checkbutton(frm, text="Entwickler mit Affiliate-Links unterstützen", variable=self.var_affiliate).grid(row=10, column=0, columnspan=2, sticky="w"); ttk.Label(frm, text="(Fügt in der Einkaufsliste automatisch einen Partner-Code\nbei Bambu Lab Links hinzu. Kostet dich keinen Cent!)", font=("Segoe UI", 8)).grid(row=11, column=0, columnspan=2, sticky="w", padx=20)
        
        # --- UPDATE-CHECK & GITHUB BEREICH ---
        ttk.Separator(frm, orient="horizontal").grid(row=12, column=0, columnspan=2, sticky="ew", pady=15)
        btn_action_frm = ttk.Frame(frm); btn_action_frm.grid(row=13, column=0, columnspan=2, pady=5)
        def open_github(): webbrowser.open("https://github.com/SirMetalizer/VibeSpool/releases/latest")
        def manual_update_check():
            try:
                url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"; req = urllib.request.Request(url, headers={'User-Agent': 'VibeSpool-App'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8')); latest_tag = data.get("tag_name", "").lstrip("vV"); current_ver = APP_VERSION.lstrip("vV")
                    def parse_ver(v): return [int(x) for x in v.replace('-', '.').split('.') if x.isdigit()]
                    if parse_ver(latest_tag) > parse_ver(current_ver):
                        if messagebox.askyesno("Update verfügbar!", f"Version {latest_tag} ist online!\nDu hast aktuell v{current_ver}.\n\nMöchtest du die Download-Seite jetzt öffnen?", parent=self): open_github()
                    else: messagebox.showinfo("Aktuell", f"Du bist auf dem neuesten Stand!\nInstallierte Version: v{current_ver}", parent=self)
            except Exception as e: messagebox.showerror("Fehler", f"Keine Verbindung zu GitHub möglich:\n{e}", parent=self)
        ttk.Button(btn_action_frm, text="🔄 Nach Updates suchen", command=manual_update_check).pack(side="left", padx=5); ttk.Button(btn_action_frm, text="🌐 GitHub besuchen", command=open_github).pack(side="left", padx=5)
        ttk.Button(self, text="Speichern", command=self.save).pack(pady=20, fill="x", padx=20)
    def save(self):
        try:
            self.current_settings.update({"shelves": self.ent_shelves.get().strip(), "logistics_order": self.var_logistics.get(), "label_row": self.ent_lbl_row.get().strip() or "Fach", "label_col": self.ent_lbl_col.get().strip() or "Slot", "num_ams": int(self.ent_ams.get()), "custom_locs": self.ent_custom.get().strip(), "use_affiliate": self.var_affiliate.get()})
            self.on_save(self.current_settings); self.destroy()
        except: messagebox.showerror("Fehler", "Bitte bei AMS nur Zahlen eingeben.")

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
        
        # --- Leinwand mit VERT und HORIZ Scrollbalken ---
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
                # --- WICHTIG:anchor="w" statt fill="x" damit es kompakt bleibt ---
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
        self.parsed_shelves = []
        matches = re.findall(r'([^,|]+)\|\s*(\d+)\s*\|\s*(\d+)', self.settings.get("shelves", "REGAL|4|8"))
        for name, r_s, c_s in matches: self.parsed_shelves.append({"name": name.strip(), "rows": int(r_s), "cols": int(c_s)})
    def calculate_net_weight(self, gross, spool_id):
        try:
            g = float(str(gross).replace(',', '.')); s = next((s for s in self.spools if s['id'] == spool_id), None)
            return max(0, int(g - (s['weight'] if s else 0)))
        except: return 0
    def draw_slot(self, parent, label, item, is_ams, w=90, h=80):
        bg_colors, fg_col, txt, tooltip = ["#D2B48C"] if not is_ams else ["#666666"], "#555" if not is_ams else "#CCC", f"{label}\nLEER", "Leer"
        if item:
            cols = get_colors_from_text(item['color']); bg_colors = cols or ["#FFFFFF"]
            if bg_colors[0].startswith("#"):
                r, g, b = int(bg_colors[0][1:3], 16), int(bg_colors[0][3:5], 16), int(bg_colors[0][5:7], 16); fg_col = "white" if (r*0.299 + g*0.587 + b*0.114) < 128 else "black"
            else: fg_col = "black"
            sub = item.get('subtype', ''); net = self.calculate_net_weight(item.get('weight_gross','0'), item.get('spool_id',-1))
            # Text-Formatierung verbessert um Overlap zu vermeiden
            txt = f"{label}\n{item['brand'][:10]}\n{sub[:10]}\n{net}g"
            tooltip = f"ID: {item['id']}\n{item['brand']} - {item['color']}\n{item['material']} | Rest: {net}g"
        img = create_color_icon(bg_colors, (w, h), "black"); self.image_cache.append(img)
        lbl = tk.Label(parent, image=img, text=txt, compound="center", fg=fg_col, font=("Segoe UI", 8, "bold"), borderwidth=0)
        # padding verkleinert
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
        self.tree.column("mat", width=50); self.tree.column("price", width=60); self.tree.column("status", width=100); scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview); self.tree.configure(yscroll=scroll.set); self.tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y"); self.tree.bind("<Double-1>", lambda e: self.open_shop_link())
        self.populate(); btn_frm = ttk.Frame(self); btn_frm.pack(pady=10); ttk.Button(btn_frm, text="🔗 Im Shop öffnen", command=self.open_shop_link, style="Accent.TButton").pack(side="left", padx=10); ttk.Button(btn_frm, text="Als CSV exportieren (Excel)", command=self.export_csv).pack(side="left", padx=10); ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="left", padx=10)
    def populate(self):
        for i in self.inventory:
            if i.get('reorder') or i.get('type') == 'VERBRAUCHT':
                # Preis-Formatierung verbessert
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
        self.app = app_instance
        self.inventory = inventory
        self.title("📊 Finanz-Dashboard & Statistik")
        self.geometry("600x550")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)

        # --- Die unsichtbare Mathematik ---
        total_value = 0.0
        total_weight = 0
        total_spools = 0
        mat_stats = {} # Sammelt Daten pro Material

        for item in self.inventory:
            if item.get('type') == 'VERBRAUCHT': 
                continue # Verbrauchte Spulen zählen wir nicht mit
                
            total_spools += 1

            # Gewicht berechnen
            gross_str = str(item.get('weight_gross', '0')).replace(',', '.')
            net = self.app.calculate_net_weight(gross_str, item.get('spool_id', -1))
            total_weight += net

            # Wert berechnen
            val = 0.0
            price_str = str(item.get('price', '')).replace(',', '.')
            cap_str = str(item.get('capacity', '1000'))
            try:
                price = float(price_str)
                cap = float(cap_str)
                if cap > 0:
                    val = (net / cap) * price
            except: 
                pass
            total_value += val

            # Material-Statistik aufbauen
            mat = item.get('material', 'Unbekannt')
            if not mat: mat = 'Unbekannt'
            if mat not in mat_stats:
                mat_stats[mat] = {'count': 0, 'weight': 0, 'value': 0.0}
            mat_stats[mat]['count'] += 1
            mat_stats[mat]['weight'] += net
            mat_stats[mat]['value'] += val

        # --- UI Aufbau ---
        ttk.Label(self, text="💰 Bestands-Statistik & Finanzen", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

        kpi_frame = tk.Frame(self, bg=parent.cget('bg'))
        kpi_frame.pack(fill="x", padx=20, pady=10)

        # Große Zahlen (KPIs)
        val_str = f"{total_value:.2f} €"
        weight_str = f"{(total_weight/1000):.2f} kg"

        ttk.Label(kpi_frame, text=f"Gesamtwert:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=val_str, font=("Segoe UI", 14, "bold"), foreground="#28a745").grid(row=0, column=1, sticky="w", padx=15, pady=2)
        
        ttk.Label(kpi_frame, text=f"Lagermenge:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=weight_str, font=("Segoe UI", 12, "bold")).grid(row=1, column=1, sticky="w", padx=15, pady=2)
        
        ttk.Label(kpi_frame, text=f"Aktive Spulen:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=str(total_spools), font=("Segoe UI", 12, "bold")).grid(row=2, column=1, sticky="w", padx=15, pady=2)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # Tabelle für die Materialien
        ttk.Label(self, text="Aufschlüsselung nach Material:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(5, 5))

        cols = ("mat", "count", "weight", "value")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        tree.heading("mat", text="Material")
        tree.heading("count", text="Spulen")
        tree.heading("weight", text="Gewicht (kg)")
        tree.heading("value", text="Wert (€)")

        tree.column("mat", width=120)
        tree.column("count", width=60, anchor="center")
        tree.column("weight", width=100, anchor="center")
        tree.column("value", width=100, anchor="center")

        tree.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Tabelle füllen (sortiert nach höchstem Wert)
        for mat, stats in sorted(mat_stats.items(), key=lambda x: x[1]['value'], reverse=True):
            tree.insert("", "end", values=(
                mat,
                stats['count'],
                f"{(stats['weight']/1000):.2f}",
                f"{stats['value']:.2f} €"
            ))

        btn_frm = ttk.Frame(self)
        btn_frm.pack(pady=10)
        ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack()


class BackupDialog(tk.Toplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent); self.app = app_instance; self.title("Backup & Restore"); self.geometry("400x200"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        ttk.Label(self, text="Datenbank Backup", font=("Segoe UI", 12, "bold")).pack(pady=15); ttk.Button(self, text="📥 Backup exportieren", command=self.export_data).pack(fill="x", padx=40, pady=10); ttk.Button(self, text="📤 Backup importieren", command=self.import_data).pack(fill="x", padx=40, pady=10)
    def export_data(self):
        fp = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP", "*.zip")], initialfile="VibeSpool_Backup.zip")
        if not fp: return
        try:
            with zipfile.ZipFile(fp, 'w') as z:
                for f, n in [(DATA_FILE, "inventory.json"), (SETTINGS_FILE, "settings.json"), (SPOOLS_FILE, "spools.json")]:
                    if os.path.exists(f): z.write(f, n)
            messagebox.showinfo("Erfolg", "Backup erstellt!", parent=self); self.destroy()
        except Exception as e: messagebox.showerror("Fehler", str(e), parent=self)
    def import_data(self):
        fp = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
        if not fp: return
        if messagebox.askyesno("Warnung", "Daten werden überschrieben!", parent=self):
            try:
                with zipfile.ZipFile(fp, 'r') as z: z.extractall(BASE_DIR)
                self.app.refresh_all_data(); messagebox.showinfo("Erfolg", "Backup geladen!", parent=self.app.root); self.destroy()
            except Exception as e: messagebox.showerror("Fehler", str(e), parent=self)

class FilamentApp:
    def __init__(self, root):
        self.root = root; self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS); self.spools = load_json(SPOOLS_FILE, []) 
        # --- WICHTIG: Fensterhöhe drastisch erhöht (980) ---
        self.root.geometry(self.settings.get("geometry", "1500x980"))
        self.root.title(f"VibeSpool v{APP_VERSION}"); self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.icon_cache, self.inventory = [], load_json(DATA_FILE, [])
        self.style = ttk.Style(); self.style.theme_use("clam"); self.apply_theme(); self.style.configure("Treeview", rowheight=26)
        
        # --- TKINTER VARIABLEN FÜR SYNC & MATHEMATIK ---
        self.var_price = tk.StringVar(value="") # Geteilt zwischen Tab Basis (unsichtbar) und Kaufmännisch (sichtbar)
        self.var_capacity = tk.StringVar(value="1000")
        self.var_gross = tk.StringVar(value="")
        # Tracker für Änderungen
        for v in [self.var_price, self.var_capacity, self.var_gross]: v.trace_add("write", lambda n, i, m: self.update_net_weight_display())

        # --- TOP BAR ---
        top_bar = ttk.Frame(root, padding=10); top_bar.pack(fill="x", side="top"); ttk.Label(top_bar, text="Suche:").pack(side="left"); self.search_var = tk.StringVar(); self.search_var.trace_add("write", lambda n, i, m: self.refresh_table()); ttk.Entry(top_bar, textvariable=self.search_var, width=15).pack(side="left", padx=5)
        self.filter_mat_var, self.filter_color_var, self.filter_loc_var = tk.StringVar(value="Alle Materialien"), tk.StringVar(value="Alle Farben"), tk.StringVar(value="Alle Orte")
        self.combo_filter_mat = ttk.Combobox(top_bar, textvariable=self.filter_mat_var, state="readonly", width=15); self.combo_filter_mat.pack(side="left", padx=5); self.combo_filter_mat.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.combo_filter_color = ttk.Combobox(top_bar, textvariable=self.filter_color_var, state="readonly", width=15); self.combo_filter_color.pack(side="left", padx=5); self.combo_filter_color.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.combo_filter_loc = ttk.Combobox(top_bar, textvariable=self.filter_loc_var, state="readonly", width=15); self.combo_filter_loc.pack(side="left", padx=5); self.combo_filter_loc.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        ttk.Button(top_bar, text="🔄 Reset", command=self.reset_filters).pack(side="left", padx=5); ttk.Label(top_bar, text=" Quick-ID:").pack(side="left", padx=(10,0)); self.entry_scan = ttk.Entry(top_bar, width=8); self.entry_scan.pack(side="left", padx=5); self.entry_scan.bind("<Return>", self.on_quick_scan)
        ttk.Button(top_bar, text="⚙ Settings", command=self.open_settings).pack(side="right", padx=5); ttk.Button(top_bar, text="💾 Backup", command=lambda: BackupDialog(self.root, self)).pack(side="right", padx=5); ttk.Button(top_bar, text="🛒 Einkaufsliste", command=lambda: ShoppingListDialog(self.root, self.inventory, self)).pack(side="right", padx=5); ttk.Button(top_bar, text="☕ Spenden", command=self.open_paypal).pack(side="right", padx=5); self.btn_theme = ttk.Button(top_bar, text="...", command=self.toggle_theme); self.btn_theme.pack(side="right", padx=5); self.update_theme_button_text()
        
        # --- MAIN AREA ---
        main_frame = ttk.Frame(root, padding=10); main_frame.pack(fill="both", expand=True)
        sidebar = ttk.Frame(main_frame, width=350); sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.notebook = ttk.Notebook(sidebar); self.notebook.pack(fill="both", expand=True)
        tab_basis, tab_erp = ttk.Frame(self.notebook, padding=10), ttk.Frame(self.notebook, padding=10); self.notebook.add(tab_basis, text="Basis & Lager"); self.notebook.add(tab_erp, text="Kaufmännisch")

        # --- TAB 1: BASIS & LAGER (KOMPLETT UI FIX FÜR LIGHTMODE) ---
        # Wir nutzen keine engen Grid-Reihen mehr, sondern saubere Frame-Pakete (side="top")
        
        # Sektion ID
        frm_id = ttk.Frame(tab_basis); frm_id.pack(fill="x", pady=2); ttk.Label(frm_id, text="ID:").pack(side="left"); self.entry_id = ttk.Entry(frm_id, width=10, font=FONT_BOLD); self.entry_id.pack(side="left", padx=5)
        
        # Sektion Stammdaten
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
        
        # Sektion Spule & Gewicht
        ttk.Label(tab_basis, text="Spule / Leergewicht:").pack(anchor="w", pady=(5,0)); self.combo_spool = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN); self.combo_spool.pack(fill="x", pady=2)
        # NEU: self.combo_spool nutzt keine shared Variable, daher Tracker manuell
        self.combo_spool.bind("<<ComboboxSelected>>", lambda e: self.update_net_weight_display())
        
        ttk.Label(tab_basis, text="Original-Inhalt (Netto g):").pack(anchor="w", pady=(10,0)); self.entry_capacity = ttk.Entry(tab_basis, font=FONT_MAIN, textvariable=self.var_capacity); self.entry_capacity.pack(fill="x", pady=2)
        
        # --- PRE Prep: Unsichtbares Preis-Feld auf Tab 1, synchronisiert mit Kaufmännisch ---
        self.entry_price_tab1 = ttk.Entry(tab_basis, textvariable=self.var_price) # Unsichtbar
        
        ttk.Label(tab_basis, text="Gewicht auf Waage (Brutto g):").pack(anchor="w", pady=(10,0)); self.entry_gross = ttk.Entry(tab_basis, font=FONT_MAIN, textvariable=self.var_gross); self.entry_gross.pack(fill="x", pady=2)
        
        # Berechnetes Restgewicht
        self.lbl_net_weight = ttk.Label(tab_basis, text="Netto (Rest): 0 g | Wert: -", font=("Segoe UI", 10, "bold"), foreground=COLOR_ACCENT); self.lbl_net_weight.pack(anchor="w", pady=(10,5))
        
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=15)
        
        # Sektion Druckparameter
        ttk.Label(tab_basis, text="Flow Ratio:").pack(anchor="w"); self.entry_flow = ttk.Entry(tab_basis, width=10); self.entry_flow.pack(anchor="w", pady=2)
        ttk.Label(tab_basis, text="Pressure Adv:").pack(anchor="w", pady=(5,0)); self.entry_pa = ttk.Entry(tab_basis); self.entry_pa.pack(fill="x", pady=2)
        
        ttk.Separator(tab_basis, orient="horizontal").pack(fill="x", pady=15)
        
        # Sektion Lager & Status
        ttk.Label(tab_basis, text="Lagerort:").pack(anchor="w"); self.combo_type = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN); self.combo_type.pack(fill="x", pady=2); self.combo_type.bind("<<ComboboxSelected>>", self.update_slot_dropdown)
        ttk.Label(tab_basis, text="Slot / Nr.:").pack(anchor="w", pady=(5,0)); self.combo_loc_id = ttk.Combobox(tab_basis, font=FONT_MAIN); self.combo_loc_id.pack(fill="x", pady=2)
        
        self.var_reorder = tk.BooleanVar(); ttk.Checkbutton(tab_basis, text="Auf Einkaufsliste setzen!", variable=self.var_reorder).pack(anchor="w", pady=10)

        # --- TAB 2: ERP (KAUFMÄNNISCH) - RESTORE PRICE FIELD ---
        ttk.Label(tab_erp, text="Lieferant / Shop:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_supplier = ttk.Entry(tab_erp); self.entry_supplier.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="SKU / Art-Nr.:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_sku = ttk.Entry(tab_erp); self.entry_sku.grid(row=1, column=1, sticky="ew", pady=2)
        
        # --- RESTORE: Preis-Feld auf Kaufmännisch Tab ---
        ttk.Label(tab_erp, text="Preis (€):").grid(row=2, column=0, sticky="w", pady=5)
        # Nutzt self.var_price, synchronisiert es mit Tab 1
        self.entry_price = ttk.Entry(tab_erp, textvariable=self.var_price)
        self.entry_price.grid(row=2, column=1, sticky="ew", pady=2)
        
        ttk.Label(tab_erp, text="Link:").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_link = ttk.Entry(tab_erp); self.entry_link.grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Separator(tab_erp, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(tab_erp, text="Nozzle Temp (°C):").grid(row=5, column=0, sticky="w", pady=5); self.entry_temp_n = ttk.Entry(tab_erp); self.entry_temp_n.grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Bed Temp (°C):").grid(row=6, column=0, sticky="w", pady=5); self.entry_temp_b = ttk.Entry(tab_erp); self.entry_temp_b.grid(row=6, column=1, sticky="ew", pady=2)
        tab_erp.columnconfigure(1, weight=1)

        # AKTIONEN UNTEN
        btn_frame = ttk.Frame(sidebar)
        btn_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        # --- DIE VERLORENEN SÖHNE SIND ZURÜCK! ---
        ttk.Button(btn_frame, text="Neu Hinzufügen", command=self.add_filament, style="Accent.TButton").pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Änderungen Speichern", command=self.update_filament).pack(fill="x", pady=3)
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=8)
        
        ttk.Button(btn_frame, text="📦 Regal & AMS Ansicht", command=lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools)).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="📷 QR Code generieren", command=self.show_qr_code).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🧵 Leerspulen verwalten", command=lambda: SpoolManager(self.root, self.update_spool_dropdown)).pack(fill="x", pady=2)
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=8)
        
        ttk.Button(btn_frame, text="Felder leeren", command=self.clear_inputs).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="🔄 Quick-Swap", command=self.quick_swap_dialog).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Löschen", command=self.delete_filament, style="Delete.TButton").pack(fill="x", pady=3)
        
        ttk.Button(btn_frame, text="📊 Finanz-Dashboard", command=lambda: StatisticsDialog(self.root, self.inventory, self)).pack(fill="x", pady=8)        # -- TABELLE --
        table_frame = ttk.Frame(main_frame); table_frame.pack(side="right", fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"), show="tree headings")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview); self.tree.configure(yscroll=scrollbar.set); scrollbar.pack(side="right", fill="y"); self.tree.pack(fill="both", expand=True)
        self.tree.column("#0", width=40, anchor="center", stretch=False)
        for col, text in zip(("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status"), ["ID", "Marke", "Material", "Farbe", "Finish", "Rest(g)", "Flow", "Ort", "Status"]): self.tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(c, False))
        self.tree.column("id", width=40, anchor="center"); self.tree.column("brand", width=120); self.tree.column("material", width=60, anchor="center"); self.tree.column("weight", width=60, anchor="center"); self.tree.column("flow", width=50, anchor="center"); self.tree.column("status", width=90, anchor="center"); self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.update_locations_dropdown(); self.update_spool_dropdown(); self.update_filter_dropdowns(); self.clear_inputs(); self.refresh_table()
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def update_color_preview(self, event=None):
        cols = get_colors_from_text(self.combo_color.get())
        img = create_color_icon(cols, (30, 20), "#888888")
        self.lbl_color_preview.config(image=img); self.lbl_color_preview.image = img

    def open_paypal(self):
        if messagebox.askyesno("☕ Kaffee spendieren", "In das Tool ist eine Menge Zeit geflossen. Wenn es dir gefällt, freue ich mich über einen virtuellen Kaffee!\n\nMöchtest du zur PayPal-Seite weitergeleitet werden?"): webbrowser.open("https://paypal.me/florianfranck")

    def check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"; req = urllib.request.Request(url, headers={'User-Agent': 'VibeSpool-App'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8')); latest_tag = data.get("tag_name", ""); download_url = data.get("html_url", "")
                def p_v(v): return [int(x) for x in v.lstrip("vV").replace('-', '.').split('.') if x.isdigit()]
                if download_url and p_v(latest_tag) > p_v(APP_VERSION): self.root.after(0, lambda: self.show_update_prompt(latest_tag, download_url))
        except: pass

    def show_update_prompt(self, latest, url):
        upd = tk.Toplevel(self.root)
        upd.title("VibeSpool Update")
        upd.geometry("400x150")
        
        # --- DER FIX: Das Fenster erbt die Hintergrundfarbe vom Hauptprogramm ---
        upd.configure(bg=self.root.cget('bg')) 
        # -----------------------------------------------------------------------
        
        upd.attributes('-topmost', True)
        center_window(upd, self.root)

        ttk.Label(upd, text=f"Version {latest} ist verfügbar!", font=("Segoe UI", 12, "bold")).pack(pady=15)

        btn_frm = ttk.Frame(upd)
        btn_frm.pack(pady=10)
        
        def open_url_and_close():
            import webbrowser
            webbrowser.open(url)
            upd.destroy()
            
        ttk.Button(btn_frm, text="Laden", command=open_url_and_close).pack(side="left", padx=5)
        ttk.Button(btn_frm, text="Später", command=upd.destroy).pack(side="left", padx=5)

    def on_closing(self): self.settings["geometry"] = self.root.geometry(); save_json(SETTINGS_FILE, self.settings); self.root.destroy()
    
    def apply_theme(self):
        theme = self.settings.get("theme", "dark")
        c = THEMES[theme]
        self.root.configure(bg=c["bg"])
        s = self.style
        
        s.configure(".", background=c["bg"], foreground=c["fg"], font=FONT_MAIN)
        s.configure("TLabel", background=c["bg"], foreground=c["fg"])
        
        # --- NEU: Der Checkbutton-Fix (Löst das graue Kästchen-Problem) ---
        s.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
        s.map("TCheckbutton", background=[("active", c["bg"])], foreground=[("active", c["fg"])])
        # ------------------------------------------------------------------
        
        s.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        s.configure("TLabelframe.Label", background=c["bg"], foreground=c["lbl_frame"])
        s.configure("Treeview", background=c["tree_bg"], fieldbackground=c["tree_bg"], foreground=c["tree_fg"])
        s.configure("Treeview.Heading", background=c["head_bg"], foreground=c["head_fg"])
        s.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["entry_fg"])
        s.configure("TButton", background=c["bg"], foreground=c["fg"])
        s.map("Treeview", background=[("selected", COLOR_ACCENT)])
        
        # --- DYNAMISCHER FIX FÜR TABS, DROPDOWNS & BUTTON HOVER ---
        if theme == "dark":
            nb_bg, tab_bg, tab_fg, cb_bg, cb_fg = "#2b2b2b", "#3c3f41", "white", "#3c3f41", "white"
            btn_hover_bg = "#505050" 
        else:
            nb_bg, tab_bg, tab_fg, cb_bg, cb_fg = "#f0f0f0", "#e1e1e1", "black", "#ffffff", "black"
            btn_hover_bg = "#d0d0d0" 

        s.map("TButton", background=[("active", btn_hover_bg)], foreground=[("active", c["fg"])])

        s.configure("TNotebook", background=nb_bg, borderwidth=0)
        s.configure("TNotebook.Tab", background=tab_bg, foreground=tab_fg, padding=[10, 2], borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "white")])
        
        s.configure("TCombobox", fieldbackground=cb_bg, background=nb_bg, foreground=cb_fg)
        s.map("TCombobox", fieldbackground=[("readonly", cb_bg)], selectbackground=[("readonly", COLOR_ACCENT)], selectforeground=[("readonly", "white")])
        
        self.root.option_add('*TCombobox*Listbox.background', cb_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', cb_fg)
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        
        s.map("Accent.TButton", background=[("active", "#222222")])
        s.configure("Accent.TButton", foreground="white", background=COLOR_ACCENT, borderwidth=0)
        s.configure("Delete.TButton", foreground="white", background=COLOR_DELETE, borderwidth=0)
        # --- DYNAMISCHER FIX FÜR TABS & DROPDOWNS ---
        if theme == "dark":
            nb_bg, tab_bg, tab_fg, cb_bg, cb_fg = "#2b2b2b", "#3c3f41", "white", "#3c3f41", "white"
        else:
            nb_bg, tab_bg, tab_fg, cb_bg, cb_fg = "#f0f0f0", "#e1e1e1", "black", "#ffffff", "black"

        s.configure("TNotebook", background=nb_bg, borderwidth=0)
        s.configure("TNotebook.Tab", background=tab_bg, foreground=tab_fg, padding=[10, 2], borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "white")])
        
        s.configure("TCombobox", fieldbackground=cb_bg, background=nb_bg, foreground=cb_fg)
        s.map("TCombobox", fieldbackground=[("readonly", cb_bg)], selectbackground=[("readonly", COLOR_ACCENT)], selectforeground=[("readonly", "white")])
        
        self.root.option_add('*TCombobox*Listbox.background', cb_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', cb_fg)
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        
        s.map("Accent.TButton", background=[("active", "#222222")])
        s.configure("Accent.TButton", foreground="white", background=COLOR_ACCENT, borderwidth=0)
        s.configure("Delete.TButton", foreground="white", background=COLOR_DELETE, borderwidth=0)

    def toggle_theme(self): self.settings["theme"] = "dark" if self.settings.get("theme") == "light" else "light"; save_json(SETTINGS_FILE, self.settings); self.apply_theme(); self.update_theme_button_text()
    def update_theme_button_text(self): self.btn_theme.config(text="☀️" if self.settings.get("theme") == "dark" else "🌙")
    def get_dynamic_locations(self):
        matches = re.findall(r'([^,|]+)\|\s*\d+\s*\|\s*\d+', self.settings.get("shelves", "REGAL|4|8"))
        locs = [m.strip() for m in matches]
        for i in range(1, self.settings.get("num_ams", 1) + 1): locs.append(f"AMS {i}")
        for c in self.settings.get("custom_locs", "").split(","):
            if c.strip(): locs.append(c.strip())
        locs.extend(["LAGER", "VERBRAUCHT"]); return locs
    def update_locations_dropdown(self): self.combo_type['values'] = self.get_dynamic_locations()
    def update_spool_dropdown(self):
        self.spools = load_json(SPOOLS_FILE, []); values = ["-"] + [f"{s['id']} - {s['name']}" for s in self.spools]; curr = self.combo_spool.get(); self.combo_spool['values'] = values
        if curr not in values: self.combo_spool.current(0)
    def get_selected_spool_id(self):
        try: return -1 if self.combo_spool.get() == "-" else int(self.combo_spool.get().split(" - ")[0])
        except: return -1
    def calculate_net_weight(self, gross_str, spool_id):
        try:
            g = float(str(gross_str).replace(',', '.'))
            s = next((s for s in self.spools if s['id'] == spool_id), None)
            return max(0, int(g - (s['weight'] if s else 0)))
        except: 
            return 0
    def update_net_weight_display(self, event=None):
        try:
            # --- WICHTIG: Nutzt jetzt self.var_* shared Variables für Mathematik ---
            gross_str = self.var_gross.get().strip().replace(',', '.')
            if not gross_str: self.lbl_net_weight.config(text="Netto: 0 g | Wert: -"); return
            gross = float(gross_str)
            sid = self.get_selected_spool_id(); spool = next((s for s in self.spools if s['id'] == sid), None)
            net = max(0, gross - (spool['weight'] if spool else 0))
            
            # --- Prio 5: Restwert-Berechnung live ---
            price_str = self.var_price.get().strip().replace(',', '.')
            cap_str = self.var_capacity.get().strip(); val_str = ""
            if price_str and cap_str:
                try:
                    price, cap = float(price_str), float(cap_str)
                    if cap > 0: val_str = f" | Wert: {(net / cap) * price:.2f} €"
                except: pass
            self.lbl_net_weight.config(text=f"Netto: {int(net)} g{val_str}")
        except: self.lbl_net_weight.config(text="Netto: 0 g | Wert: -")
    def open_settings(self):
        def on_save(s): self.settings = s; save_json(SETTINGS_FILE, s); self.update_locations_dropdown(); self.update_slot_dropdown(); self.update_filter_dropdowns()
        SettingsDialog(self.root, self.settings, on_save)
    def update_slot_dropdown(self, event=None):
        loc = self.combo_type.get()
        if loc.startswith("AMS"): self.combo_loc_id['values'] = ["1", "2", "3", "4"]
        else:
            matches = re.findall(r'([^,|]+)\|\s*(\d+)\s*\|\s*(\d+)', self.settings.get("shelves", "REGAL|4|8"))
            for name, r_s, c_s in matches:
                if name.strip() == loc: r, c, logistics = int(r_s), int(c_s), self.settings.get("logistics_order"); self.combo_loc_id['values'] = [f"{self.settings.get('label_row')} {rw} - {self.settings.get('label_col')} {cl}" for rw in (range(r, 0, -1) if logistics else range(1, r + 1)) for cl in range(1, c + 1)]; return
            self.combo_loc_id['values'] = ["-"]
    def treeview_sort_column(self, col, reverse):
        def sort_key(i):
            v = i.get(col, ""); return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(v))]
        self.inventory.sort(key=sort_key, reverse=reverse); self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse)); self.refresh_table()
    def update_filter_dropdowns(self):
        mats = sorted(list(set(i.get("material", "") for i in self.inventory if i.get("material")))); cols = sorted(list(set(i.get("color", "") for i in self.inventory if i.get("color")))); locs = self.get_dynamic_locations()
        if hasattr(self, 'combo_filter_mat'): self.combo_filter_mat['values'] = ["Alle Materialien"] + mats; self.combo_filter_color['values'] = ["Alle Farben"] + cols; self.combo_filter_loc['values'] = ["Alle Orte"] + locs
    def reset_filters(self): self.filter_mat_var.set("Alle Materialien"); self.filter_color_var.set("Alle Farben"); self.filter_loc_var.set("Alle Orte"); self.search_var.set(""); self.refresh_table()
    def get_filtered_inventory(self):
        s = self.search_var.get().lower(); result = []
        for i in self.inventory:
            if self.filter_mat_var.get() != "Alle Materialien" and i.get("material") != self.filter_mat_var.get(): continue
            if self.filter_color_var.get() != "Alle Farben" and i.get("color") != self.filter_color_var.get(): continue
            t, f_l = i.get("type", ""), self.filter_loc_var.get()
            if f_l != "Alle Orte":
                if f_l.startswith("AMS") and t.startswith("AMS"):
                    if f_l != t and f_l != "AMS": continue
                elif t != f_l: continue
            # Löst das Crash-Problem in der Live-Übersicht beim Tippen
            try:
                if s and s not in f"{i.get('id','')} {i.get('brand','')} {i.get('color','')} {i.get('material','')}".lower(): continue
            except: pass
            result.append(i)
        return result
    
    def refresh_table(self, *args):
        self.icon_cache = []
        for row in self.tree.get_children(): 
            self.tree.delete(row)
            
        for i in self.get_filtered_inventory():
            loc_str = f"{i['type']} {i.get('loc_id', '')}".strip()
            stat = " | ".join(filter(None, ["VERBRAUCHT" if i['type'] == "VERBRAUCHT" else "", "KAUFEN" if i.get('reorder') else ""]))
            icon = create_color_icon(get_colors_from_text(i['color']))
            self.icon_cache.append(icon)
            
            gross = str(i.get('weight_gross', '0')).replace(',', '.')
            net = self.calculate_net_weight(gross, i.get('spool_id', -1))
            tags = ["alert"] if i.get('reorder') else ["grayed"] if i['type'] == "VERBRAUCHT" else []
            flw = i.get('flow', 'Auto' if 'bambu' in i['brand'].lower() else '-')
            
            self.tree.insert("", "end", iid=str(i['id']), image=icon, values=(i['id'], i['brand'], i.get('material', '-'), i['color'], i.get('subtype', 'Standard'), f"{net}g", flw, loc_str, stat), tags=tags)
            
        self.tree.tag_configure("alert", background="#ffe6e6", foreground="#d9534f")
        self.tree.tag_configure("grayed", foreground="#999999")

    def get_input_data(self):
        try:
            loc_id = self.combo_loc_id.get().strip()
            loc_type = self.combo_type.get()
            if loc_type == "REGAL" and "," not in loc_id and loc_id.isdigit(): 
                loc_id = f"{loc_id}, 1"
                
            return {
                "id": int(self.entry_id.get().strip()) if self.entry_id.get().strip() else None, 
                "brand": self.entry_brand.get().strip(), 
                "material": self.combo_material.get().strip(), 
                "color": self.combo_color.get().strip(), 
                "subtype": self.combo_subtype.get().strip(), 
                "type": loc_type, 
                "loc_id": loc_id, 
                "flow": self.entry_flow.get().strip(), 
                "pa": self.entry_pa.get().strip(), 
                "spool_id": self.get_selected_spool_id(), 
                "weight_gross": float(self.var_gross.get().strip().replace(',', '.') or 0), 
                "capacity": int(self.var_capacity.get().strip() or 1000), 
                "is_empty": loc_type == "VERBRAUCHT", 
                "reorder": self.var_reorder.get(), 
                "supplier": self.entry_supplier.get().strip(), 
                "sku": self.entry_sku.get().strip(), 
                "price": self.var_price.get().strip(), 
                "link": self.entry_link.get().strip(), 
                "temp_n": self.entry_temp_n.get().strip(), 
                "temp_b": self.entry_temp_b.get().strip()
            }
        except: 
            messagebox.showwarning("Fehler", "Zahlenformat ungültig.")
            return None

    def add_filament(self):
        d = self.get_input_data()
        d['id'] = d['id'] or (max([int(i['id']) for i in self.inventory], default=0) + 1)
        self.inventory.append(d)
        self.save_data()
        self.refresh_table()
        self.clear_inputs()

        d = self.get_input_data(); d['id'] = d['id'] or (max([int(i['id']) for i in self.inventory], default=0) + 1); self.inventory.append(d); self.save_data(); self.refresh_table(); self.clear_inputs()
    def update_filament(self):
        sel = self.tree.selection()
        if not sel: return
        
        d = self.get_input_data()
        idx = next(i for i, item in enumerate(self.inventory) if item['id'] == int(sel[0]))
        d['id'] = d['id'] or int(sel[0])
        self.inventory[idx] = d
        self.save_data()
        self.refresh_table()
        self.tree.selection_set(str(d['id']))

    def delete_filament(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Löschen", "Wirklich löschen?"): return
        
        self.inventory = [i for i in self.inventory if i['id'] != int(sel[0])]
        self.save_data()
        self.refresh_table()
        self.clear_inputs()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        i = next((x for x in self.inventory if x['id'] == int(sel[0])), None)
        if not i: return
        
        self.clear_inputs(deselect=False)
        self.entry_id.insert(0, str(i['id']))
        self.entry_brand.insert(0, i['brand'])
        self.combo_material.set(i.get('material', 'PLA'))
        self.combo_color.set(i['color'])
        self.combo_subtype.set(i.get('subtype', 'Standard'))
        self.update_color_preview()
        self.combo_type.set(i['type'])
        self.update_slot_dropdown()
        self.combo_loc_id.set(i.get('loc_id', ''))
        self.entry_flow.insert(0, i.get('flow', ''))
        self.entry_pa.insert(0, i.get('pa', ''))
        self.var_reorder.set(i.get('reorder', False))
        
        for val in self.combo_spool['values']:
            if val.startswith(f"{i.get('spool_id', -1)} -"): 
                self.combo_spool.set(val)
                break
                
        self.var_capacity.set(str(i.get('capacity', 1000)))
        gross = str(i.get('weight_gross', '0')).replace(',', '.')
        float_g = float(gross) if gross else 0
        self.var_gross.set(str(float_g).rstrip('0').rstrip('.') if float_g > 0 else "")
        self.var_price.set(str(i.get('price', '')))
        self.update_net_weight_display()
        
        self.entry_supplier.insert(0, i.get('supplier', ''))
        self.entry_sku.insert(0, i.get('sku', ''))
        self.entry_link.insert(0, i.get('link', ''))
        self.entry_temp_n.insert(0, i.get('temp_n', ''))
        self.entry_temp_b.insert(0, i.get('temp_b', ''))

    def clear_inputs(self, deselect=True):
        for e in [self.entry_id, self.entry_brand, self.entry_flow, self.entry_pa, self.entry_supplier, self.entry_sku, self.entry_link, self.entry_temp_n, self.entry_temp_b]: 
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
        win = tk.Toplevel(self.root)
        win.title("🔄 Quick-Swap")
        win.geometry("480x220")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        center_window(win, self.root)
        
        ttk.Label(win, text="Spule ins AMS tauschen:", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        ttk.Label(win, text=f"{s_a['brand']} {s_a['color']}", font=("Segoe UI", 10)).pack(pady=5)
        
        num = self.settings.get("num_ams", 1)
        self.ams_options_map = {}
        for a in range(1, num + 1):
            am_n = f"AMS {a}"
            for s in range(1, 5):
                s_b = next((i for i in self.inventory if i.get('type') == am_n and str(i.get('loc_id')) == str(s)), None)
                slot_str = str(s)
                d_t = f"{am_n} | Slot {s}  -->  " + (f"{s_b.get('brand', '')} {s_b.get('color', '')}" if s_b else "(LEER)")
                self.ams_options_map[d_t] = (am_n, slot_str)
                
        combo = ttk.Combobox(win, values=list(self.ams_options_map.keys()), state="readonly", font=FONT_MAIN, width=45)
        combo.pack(pady=10)
        combo.current(0)
        
        def do_swap():
            t_am, t_sl = self.ams_options_map[combo.get()]
            o_t, o_l = s_a.get('type', 'LAGER'), s_a.get('loc_id', '-')
            s_b = next((i for i in self.inventory if i.get('type') == t_am and str(i.get('loc_id')) == t_sl), None)
            
            s_a['type'], s_a['loc_id'] = t_am, t_sl
            if s_b: 
                s_b['type'], s_b['loc_id'] = o_t, o_l
                
            self.save_data()
            self.refresh_table()
            self.tree.selection_set(str(s_a['id']))
            self.on_select(None)
            win.destroy()
            
            msg = f"{s_a['brand']} ist im {t_am} (Slot {t_sl})." + (f"\n\nDie alte Spule ({s_b['brand']}) wurde in {o_t} {o_l} gelegt!" if s_b else "")
            messagebox.showinfo("Quick-Swap Erfolgreich", msg, parent=self.root)
            
        ttk.Button(win, text="🔄 Tauschen", command=do_swap, style="Accent.TButton").pack(pady=15)

    def on_quick_scan(self, event=None):
        scan = self.entry_scan.get().strip()
        match = re.search(r'(?:ID:\s*|FIL_)?(\d+)', scan, re.IGNORECASE)
        if match and self.tree.exists(match.group(1)): 
            self.tree.selection_set(match.group(1))
            self.tree.see(match.group(1))
            self.on_select(None)
            self.entry_scan.delete(0, tk.END)
        else: 
            messagebox.showerror("Fehler", "Keine gültige ID im System gefunden.")

    def show_qr_code(self):
        sel = self.tree.selection()
        if not sel: 
            return messagebox.showwarning("Info", "Bitte Filament auswählen.")
            
        i = next(x for x in self.inventory if x['id'] == int(sel[0]))
        qr_w = tk.Toplevel(self.root)
        qr_w.title("QR Code")
        qr_w.geometry("300x350")
        qr_w.configure(bg=self.root.cget('bg'))
        center_window(qr_w, self.root)
        
        sub = f" ({i.get('subtype')})" if i.get('subtype') and i.get('subtype') != "Standard" else ""
        qr_c = f"ID: {i['id']} | {i['brand']} | {i.get('material', '-')} | {i['color']}{sub}"
        
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_c)
        qr.make(fit=True)
        img = ImageTk.PhotoImage(qr.make_image(fill_color="black", back_color="white"))
        
        lbl = tk.Label(qr_w, image=img, bg=self.root.cget('bg'))
        lbl.image = img
        lbl.pack(pady=10)
        ttk.Label(qr_w, text=f"ID: {i['id']}\n{i['brand']} {i['color']}", font=FONT_BOLD).pack()

    def save_data(self): 
        save_json(DATA_FILE, self.inventory)
        self.update_filter_dropdowns()

    def refresh_all_data(self): 
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.spools = load_json(SPOOLS_FILE, [])
        self.inventory = load_json(DATA_FILE, [])
        self.apply_theme()
        self.update_locations_dropdown()
        self.refresh_table()

if __name__ == "__main__":
    try: windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk()
    app = FilamentApp(root)
    root.mainloop()