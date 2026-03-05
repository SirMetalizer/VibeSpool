import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
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
import qrcode 

# --- KONFIGURATION & UPDATE CHECKER ---
APP_VERSION = "1.4.3"
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

DATA_FILE = os.path.join(BASE_DIR, "inventory.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
SPOOLS_FILE = os.path.join(BASE_DIR, "spools.json")

if os.path.exists("inventory.json") and not os.path.exists(DATA_FILE):
    try:
        shutil.copy("inventory.json", DATA_FILE)
        if os.path.exists("settings.json"): shutil.copy("settings.json", SETTINGS_FILE)
        if os.path.exists("spools.json"): shutil.copy("spools.json", SPOOLS_FILE)
    except: pass

# --- DEFAULTS ---
DEFAULT_SETTINGS = {
    "shelves": "REGAL|4|8", 
    "logistics_order": False,
    "label_row": "Fach",
    "label_col": "Slot",
    "num_ams": 1,
    "custom_locs": "Filamenttrockner",
    "geometry": "1500x850",
    "theme": "dark",
    "use_affiliate": True  # <--- NEU: Affiliate
}

MATERIALS = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF", "PVA", "Sonstiges"]
SUBTYPES = ["Standard", "Matte", "Silk", "High Speed", "Dual Color", "Tri Color", "Glow in Dark", "Marmor", "Holz", "Glitzer/Sparkle", "Transparent"]
COMMON_COLORS = ["Black", "White", "Red", "Blue", "Green", "Yellow", "Orange", "Grey", "Transparent", "Black/Red", "Rainbow"]

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
    "rot": "#FF0000", "red": "#FF0000", "blau": "#0000FF", "blue": "#0000FF", "grün": "#008000", "green": "#008000", 
    "gelb": "#FFD700", "yellow": "#FFD700", "orange": "#FFA500", "lila": "#800080", "purple": "#800080", "pink": "#FFC0CB", 
    "schwarz": "#000000", "black": "#000000", "weiß": "#F0F0F0", "white": "#F0F0F0", "grau": "#808080", "grey": "#808080", 
    "silber": "#C0C0C0", "braun": "#A52A2A", "brown": "#A52A2A", "gold": "#DAA520", "cyan": "#00FFFF", "rainbow": "RAINBOW"
}

# --- HELPER ---
def load_json(filename, default):
    if not os.path.exists(filename): return default
    try:
        with open(filename, "r", encoding="utf-8") as f: 
            data = json.load(f)
            if isinstance(default, dict) and isinstance(data, dict):
                merged = default.copy()
                merged.update(data)
                return merged
            return data
    except: return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    except Exception as e: print(e)

def get_colors_from_text(text):
    text_lower = text.lower().strip()
    if any(x in text_lower for x in ["regenbogen", "rainbow", "bunt"]):
        return ["#FF0000", "#FFA500", "#FFFF00", "#008000", "#0000FF", "#4B0082", "#EE82EE"]
    keys = sorted(COLOR_MAP.keys(), key=len, reverse=True)
    temp_text = text_lower
    matches = {}
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
    draw = ImageDraw.Draw(img)
    width, height = size
    step = width / len(hex_list)
    for i, color in enumerate(hex_list):
        x0 = i * step
        x1 = (i + 1) * step
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
        self.on_close_callback = on_close_callback
        self.title("Spulen Datenbank")
        self.geometry("600x700")
        self.configure(bg=parent.cget('bg')) 
        center_window(self, parent)
        
        self.spools = load_json(SPOOLS_FILE, [])
        ttk.Label(self, text="Verfügbare Leerspulen", font=("Segoe UI", 10, "bold")).pack(pady=10)
        frm_list = ttk.Frame(self)
        frm_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.tree = ttk.Treeview(frm_list, columns=("id", "name", "weight"), show="headings")
        self.tree.heading("id", text="ID"); self.tree.heading("name", text="Bezeichnung"); self.tree.heading("weight", text="Leergewicht (g)")
        self.tree.column("id", width=50, anchor="center"); self.tree.column("name", width=250); self.tree.column("weight", width=100, anchor="center")
        
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
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
        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for s in self.spools: self.tree.insert("", "end", iid=str(s['id']), values=(s['id'], s['name'], s['weight']))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        spool_id = int(sel[0])
        spool = next((s for s in self.spools if s['id'] == spool_id), None)
        if spool:
            self.ent_name.delete(0, tk.END); self.ent_name.insert(0, spool['name'])
            self.ent_weight.delete(0, tk.END); self.ent_weight.insert(0, str(spool['weight']))

    def add_spool(self):
        name = self.ent_name.get().strip()
        weight_str = self.ent_weight.get().strip().replace(',', '.')
        if not name or not weight_str: return
        try:
            weight = int(float(weight_str))
            new_id = max([s['id'] for s in self.spools], default=0) + 1
            self.spools.append({"id": new_id, "name": name, "weight": weight})
            save_json(SPOOLS_FILE, self.spools); self.refresh_list()
        except: pass

    def update_spool(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            weight = int(float(self.ent_weight.get().strip().replace(',', '.')))
            for s in self.spools:
                if s['id'] == int(sel[0]):
                    s['name'] = self.ent_name.get().strip(); s['weight'] = weight
            save_json(SPOOLS_FILE, self.spools); self.refresh_list()
        except: pass

    def delete_spool(self):
        sel = self.tree.selection()
        if not sel: return
        self.spools = [s for s in self.spools if s['id'] != int(sel[0])]
        save_json(SPOOLS_FILE, self.spools); self.refresh_list()

    def destroy(self):
        self.on_close_callback()
        super().destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_settings, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.current_settings = current_settings # <--- WICHTIG: Alte Settings im Gedächtnis behalten!
        self.title("Einstellungen & Lagerorte")
        self.geometry("500x600")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        
        ttk.Label(self, text="Multi-Regal Layout & Lagerorte", font=("Segoe UI", 12, "bold")).pack(pady=10)
        frm = ttk.Frame(self)
        frm.pack(padx=20, pady=5, fill="both", expand=True)
        
        ttk.Label(frm, text="Regale (Name|Zeilen|Spalten):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_shelves = ttk.Entry(frm, width=30)
        self.ent_shelves.insert(0, current_settings.get("shelves", "REGAL|4|8"))
        self.ent_shelves.grid(row=0, column=1, pady=5, sticky="w")
        ttk.Label(frm, text="Kommagetrennt für mehrere!").grid(row=1, column=1, sticky="w")
        
        self.var_logistics = tk.BooleanVar(value=current_settings.get("logistics_order", False))
        ttk.Checkbutton(frm, text="Logistik-Standard (Zählung von unten nach oben)", variable=self.var_logistics).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)

        ttk.Label(frm, text="Benennung Zeile:").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_lbl_row = ttk.Entry(frm, width=15); self.ent_lbl_row.insert(0, current_settings.get("label_row", "Fach"))
        self.ent_lbl_row.grid(row=3, column=1, sticky="w")
        
        ttk.Label(frm, text="Benennung Spalte:").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_lbl_col = ttk.Entry(frm, width=15); self.ent_lbl_col.insert(0, current_settings.get("label_col", "Slot"))
        self.ent_lbl_col.grid(row=4, column=1, sticky="w")

        ttk.Label(frm, text="Anzahl AMS Geräte:").grid(row=5, column=0, sticky="w", pady=(20,5))
        self.ent_ams = ttk.Entry(frm, width=10); self.ent_ams.insert(0, str(current_settings.get("num_ams", 1)))
        self.ent_ams.grid(row=5, column=1, sticky="w", pady=(20,5))
            
        ttk.Label(frm, text="Weitere Orte (Kommagetrennt):").grid(row=6, column=0, sticky="w", pady=5)
        self.ent_custom = ttk.Entry(frm)
        self.ent_custom.insert(0, current_settings.get("custom_locs", "Filamenttrockner"))
        self.ent_custom.grid(row=6, column=1, sticky="ew", pady=5)
        
        ttk.Separator(frm, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=15)
        self.var_affiliate = tk.BooleanVar(value=current_settings.get("use_affiliate", True))
        ttk.Checkbutton(frm, text="Entwickler mit Affiliate-Links unterstützen", variable=self.var_affiliate).grid(row=8, column=0, columnspan=2, sticky="w")
        ttk.Label(frm, text="(Fügt in der Einkaufsliste automatisch einen Partner-Code\nbei Bambu Lab Links hinzu. Kostet dich keinen Cent!)", font=("Segoe UI", 8)).grid(row=9, column=0, columnspan=2, sticky="w", padx=20)
            
        ttk.Button(self, text="Speichern", command=self.save).pack(pady=20, fill="x", padx=20)

    def save(self):
        try:
            # --- WICHTIG: Hier aktualisieren wir die alten Settings, statt sie zu überschreiben ---
            self.current_settings["shelves"] = self.ent_shelves.get().strip()
            self.current_settings["logistics_order"] = self.var_logistics.get()
            self.current_settings["label_row"] = self.ent_lbl_row.get().strip() or "Fach"
            self.current_settings["label_col"] = self.ent_lbl_col.get().strip() or "Slot"
            self.current_settings["num_ams"] = int(self.ent_ams.get())
            self.current_settings["custom_locs"] = self.ent_custom.get().strip()
            self.current_settings["use_affiliate"] = self.var_affiliate.get()
            
            self.on_save(self.current_settings)
            self.destroy()
        except: messagebox.showerror("Fehler", "Bitte bei AMS nur Zahlen eingeben.")

class ShelfVisualizer(tk.Toplevel):
    def __init__(self, parent, inventory, settings, spools):
        super().__init__(parent)
        self.inventory = inventory
        self.settings = settings
        self.spools = spools
        self.title("Regal & AMS Übersicht")
        self.geometry("1200x850")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        self.image_cache = []
        
        self.parse_shelves()
        
        self.shelf_data = {}
        self.ams_data = {}
        for item in self.inventory:
            try:
                t = str(item.get('type', ''))
                loc = str(item.get('loc_id', ''))
                if t in [s['name'] for s in self.parsed_shelves]:
                    self.shelf_data[f"{t}_{loc}"] = item
                elif t.startswith("AMS"): self.ams_data[f"{t}_{loc}"] = item
            except: pass

        canvas = tk.Canvas(self, bg=parent.cget('bg'), highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        pad = ttk.Frame(frame, padding=20)
        pad.pack(fill="both", expand=True)
        
        lbl_r = self.settings.get("label_row", "Fach")
        lbl_c = self.settings.get("label_col", "Slot")
        logistics = self.settings.get("logistics_order", False)
        
        for shelf in self.parsed_shelves:
            ttk.Label(pad, text=f"📦 {shelf['name']}", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 10))
            row_range = range(shelf['rows'], 0, -1) if logistics else range(1, shelf['rows'] + 1)
            
            for r in row_range:
                ttk.Label(pad, text=f"{lbl_r} {r}", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
                row_frame = tk.Frame(pad, bg="#8B4513", padx=5, pady=5)
                row_frame.pack(fill="x", pady=2)
                for c in range(1, shelf['cols'] + 1):
                    slot_name = f"{lbl_r} {r} - {lbl_c} {c}"
                    item = self.shelf_data.get(f"{shelf['name']}_{slot_name}")
                    self.draw_slot(row_frame, str(c), item, False)

        num_ams = self.settings.get("num_ams", 1)
        ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20)
        
        for a in range(1, num_ams + 1):
            ams_name = f"AMS {a}"
            ttk.Label(pad, text=ams_name, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 5))
            ams_frame = tk.Frame(pad, bg="#444444", padx=10, pady=10)
            ams_frame.pack(fill="x")
            for i in range(1, 5): 
                item = self.ams_data.get(f"{ams_name}_{i}")
                cont = tk.Frame(ams_frame, bg="#444444")
                cont.pack(side="left", fill="y", expand=True, padx=10)
                ttk.Label(cont, text=f"Slot {i}", foreground="white", background="#444444").pack(pady=(0, 5))
                self.draw_slot(cont, str(i), item, True, 120, 100)

    def parse_shelves(self):
        self.parsed_shelves = []
        raw = self.settings.get("shelves", "REGAL|4|8")
        for s in raw.split(","):
            parts = s.split("|")
            if len(parts) >= 3:
                try: self.parsed_shelves.append({"name": parts[0].strip(), "rows": int(parts[1]), "cols": int(parts[2])})
                except: pass

    def get_net_weight(self, item):
        try:
            gross = float(str(item.get('weight_gross', '0')).replace(',', '.'))
            if gross <= 0: return 0 
            sid = int(item.get('spool_id', -1))
            spool = next((s for s in self.spools if s['id'] == sid), None)
            return max(0, int(gross - (spool['weight'] if spool else 0)))
        except: return 0

    def draw_slot(self, parent, label, item, is_ams, w=90, h=80):
        bg_colors = ["#D2B48C"] if not is_ams else ["#666666"]
        fg_col = "#555" if not is_ams else "#CCC"
        txt = f"{label}\nLEER"
        tooltip = "Leer"
        
        if item:
            cols = get_colors_from_text(item['color'])
            if cols:
                bg_colors = cols
                c1 = cols[0]
                if c1.startswith("#"):
                    r, g, b = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
                    fg_col = "white" if (r*0.299 + g*0.587 + b*0.114) < 128 else "black"
            else:
                bg_colors, fg_col = ["#FFFFFF"], "black"
            
            sub = item.get('subtype', '')
            net = self.get_net_weight(item)
            txt = f"{label}\n{item['brand'][:8]}\n{sub[:8]}\n{net}g"
            tooltip = f"ID: {item['id']}\n{item['brand']} - {item['color']}\n{item['material']}\nRest: {net}g"

        img = create_color_icon(bg_colors, (w, h), "black")
        self.image_cache.append(img)
        lbl = tk.Label(parent, image=img, text=txt, compound="center", fg=fg_col, font=("Segoe UI", 8, "bold"), borderwidth=0)
        lbl.pack(side="left", padx=5, fill="y", expand=True)
        lbl.bind("<Enter>", lambda e: self.show_tip(e, tooltip))
        lbl.bind("<Leave>", self.hide_tip)

    def show_tip(self, event, text):
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
        center_window(self, parent)

        ttk.Label(self, text="🛒 Nachzubestellende & Verbrauchte Filamente", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        frm_list = ttk.Frame(self)
        frm_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        cols = ("brand", "color", "mat", "supplier", "sku", "price", "status")
        self.tree = ttk.Treeview(frm_list, columns=cols, show="headings")
        self.tree.heading("brand", text="Marke"); self.tree.heading("color", text="Farbe")
        self.tree.heading("mat", text="Mat."); self.tree.heading("supplier", text="Lieferant")
        self.tree.heading("sku", text="SKU"); self.tree.heading("price", text="Preis")
        self.tree.heading("status", text="Status")
        
        self.tree.column("mat", width=50); self.tree.column("price", width=60); self.tree.column("status", width=100)

        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        # Doppelklick öffnet den Link direkt
        self.tree.bind("<Double-1>", lambda e: self.open_shop_link())
        
        self.populate()
        
        btn_frm = ttk.Frame(self)
        btn_frm.pack(pady=10)
        ttk.Button(btn_frm, text="🔗 Im Shop öffnen", command=self.open_shop_link, style="Accent.TButton").pack(side="left", padx=10)
        ttk.Button(btn_frm, text="Als CSV exportieren (Excel)", command=self.export_csv).pack(side="left", padx=10)
        ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="left", padx=10)

    def populate(self):
        for i in self.inventory:
            if i.get('reorder') or i.get('type') == 'VERBRAUCHT':
                stat = "MUSS KAUFEN" if i.get('reorder') else "Leer"
                # Wir geben der Reihe die echte ID mit, um später den Link aus der Datenbank zu holen
                self.tree.insert("", "end", iid=str(i['id']), values=(i.get('brand',''), i.get('color',''), i.get('material',''), 
                                                    i.get('supplier',''), i.get('sku',''), i.get('price',''), stat))

    def open_shop_link(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showinfo("Info", "Bitte ein Filament auswählen.", parent=self)
        
        fil_id = int(sel[0])
        item = next((x for x in self.inventory if x['id'] == fil_id), None)
        
        if not item or not item.get('link'):
            return messagebox.showinfo("Info", "Für dieses Filament ist leider kein Link hinterlegt.", parent=self)
            
        url = item['link'].strip()
        if not url.startswith("http"):
            url = "https://" + url
            
        # --- AFFILIATE LOGIK ---
        if self.app.settings.get("use_affiliate", True):
            if "bambulab.com" in url.lower() and "modelId=" not in url:
                if "?" in url:
                    url += "&modelId=1889832"
                else:
                    url += "?modelId=1889832"
                    
        webbrowser.open(url)

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Einkaufsliste exportieren")
        if not filepath: return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Marke", "Farbe", "Material", "Lieferant", "SKU", "Preis", "Status", "Link"])
                for i in self.inventory:
                    if i.get('reorder') or i.get('type') == 'VERBRAUCHT':
                        writer.writerow([i.get('brand',''), i.get('color',''), i.get('material',''), i.get('supplier',''), 
                                         i.get('sku',''), i.get('price',''), "MUSS KAUFEN" if i.get('reorder') else "Leer", i.get('link','')])
            messagebox.showinfo("Exportiert", "Liste erfolgreich gespeichert!", parent=self)
        except Exception as e: messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}", parent=self)

class BackupDialog(tk.Toplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.title("Backup & Restore")
        self.geometry("400x200")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        ttk.Label(self, text="Datenbank Backup", font=("Segoe UI", 12, "bold")).pack(pady=15)
        ttk.Button(self, text="📥 Backup exportieren", command=self.export_data).pack(fill="x", padx=40, pady=10)
        ttk.Button(self, text="📤 Backup importieren", command=self.import_data).pack(fill="x", padx=40, pady=10)
        
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
                self.app.inventory = load_json(DATA_FILE, []); self.app.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
                self.app.spools = load_json(SPOOLS_FILE, [])
                self.app.apply_theme(); self.app.update_locations_dropdown(); self.app.refresh_table()
                messagebox.showinfo("Erfolg", "Backup geladen!", parent=self.app.root); self.destroy()
            except Exception as e: messagebox.showerror("Fehler", str(e), parent=self)

# --- MAIN APP ---
class FilamentApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"VibeSpool v{APP_VERSION}")
        self.icon_cache = []
        
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.spools = load_json(SPOOLS_FILE, []) 
        self.root.geometry(self.settings.get("geometry", "1500x850"))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.apply_theme()

        self.inventory = load_json(DATA_FILE, [])
        self.verify_data_integrity() 

        # --- TOP BAR ---
        top_bar = ttk.Frame(root, padding=10)
        top_bar.pack(fill="x", side="top")
        ttk.Label(top_bar, text="Suche:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda name, index, mode: self.refresh_table())
        ttk.Entry(top_bar, textvariable=self.search_var, width=15).pack(side="left", padx=5)
        
        ttk.Label(top_bar, text=" Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value="ALL")
        for mode in ["ALL", "REGAL", "AMS", "LAGER", "VERBRAUCHT"]:
            ttk.Radiobutton(top_bar, text=mode if mode != "ALL" else "Alle", variable=self.filter_var, value=mode, command=self.refresh_table).pack(side="left", padx=2)
            
        ttk.Label(top_bar, text=" Quick-ID:").pack(side="left", padx=(10,0))
        self.entry_scan = ttk.Entry(top_bar, width=8)
        self.entry_scan.pack(side="left", padx=5)
        self.entry_scan.bind("<Return>", self.on_quick_scan)
        
        ttk.Button(top_bar, text="⚙ Settings", command=self.open_settings).pack(side="right", padx=5)
        ttk.Button(top_bar, text="💾 Backup", command=lambda: BackupDialog(self.root, self)).pack(side="right", padx=5)
        ttk.Button(top_bar, text="🛒 Einkaufsliste", command=lambda: ShoppingListDialog(self.root, self.inventory, self)).pack(side="right", padx=5)        
        
        # SPENDEN
        ttk.Button(top_bar, text="☕ Spenden", command=self.open_paypal).pack(side="right", padx=5)
        
        self.btn_theme = ttk.Button(top_bar, text="...", command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)
        self.update_theme_button_text()

        # --- MAIN AREA ---
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # -- SIDEBAR NOTEBOOK --
        sidebar = ttk.Frame(main_frame, width=350)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        
        self.notebook = ttk.Notebook(sidebar)
        self.notebook.pack(fill="both", expand=True)
        
        # Tabs reduziert: Alles Wichtige wieder auf dem ersten Reiter!
        tab_basis = ttk.Frame(self.notebook, padding=10)
        tab_erp = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_basis, text="Basis & Lager")
        self.notebook.add(tab_erp, text="Kaufmännisch")

        # TAB 1: BASIS & LAGER
        ttk.Label(tab_basis, text="ID:").grid(row=0, column=0, sticky="w")
        self.entry_id = ttk.Entry(tab_basis, width=10, font=FONT_BOLD); self.entry_id.grid(row=0, column=1, sticky="w", pady=2)
        ttk.Label(tab_basis, text="Marke:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_brand = ttk.Entry(tab_basis, font=FONT_MAIN); self.entry_brand.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(tab_basis, text="Material:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_material = ttk.Combobox(tab_basis, values=MATERIALS, font=FONT_MAIN); self.combo_material.grid(row=2, column=1, sticky="ew", pady=2)
        
        ttk.Label(tab_basis, text="Farbe:").grid(row=3, column=0, sticky="w", pady=5)
        color_container = ttk.Frame(tab_basis)
        color_container.grid(row=3, column=1, sticky="ew", pady=2)
        self.combo_color = ttk.Combobox(color_container, values=COMMON_COLORS, font=FONT_MAIN)
        self.combo_color.pack(side="left", fill="x", expand=True)
        self.combo_color.bind("<KeyRelease>", self.update_color_preview); self.combo_color.bind("<<ComboboxSelected>>", self.update_color_preview)
        
        self.lbl_color_preview = tk.Label(color_container, borderwidth=0)
        self.lbl_color_preview.pack(side="right", padx=(5,0))
        self.update_color_preview()

        ttk.Label(tab_basis, text="Finish:").grid(row=4, column=0, sticky="w", pady=5)
        self.combo_subtype = ttk.Combobox(tab_basis, values=SUBTYPES, font=FONT_MAIN); self.combo_subtype.grid(row=4, column=1, sticky="ew", pady=2)
        
        ttk.Separator(tab_basis, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(tab_basis, text="Spule:").grid(row=6, column=0, sticky="w", pady=5)
        self.combo_spool = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN)
        self.combo_spool.grid(row=6, column=1, sticky="ew", pady=2); self.combo_spool.bind("<<ComboboxSelected>>", self.update_net_weight_display)
        
        ttk.Label(tab_basis, text="Brutto Gew.:").grid(row=7, column=0, sticky="w", pady=5)
        self.entry_gross = ttk.Entry(tab_basis, font=FONT_MAIN); self.entry_gross.grid(row=7, column=1, sticky="ew", pady=2)
        self.entry_gross.bind("<KeyRelease>", self.update_net_weight_display)
        
        self.lbl_net_weight = ttk.Label(tab_basis, text="Netto: 0 g", font=("Segoe UI", 9, "bold"), foreground=COLOR_ACCENT)
        self.lbl_net_weight.grid(row=8, column=1, sticky="w", pady=(0, 5))

        ttk.Separator(tab_basis, orient="horizontal").grid(row=9, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(tab_basis, text="Flow Ratio:").grid(row=10, column=0, sticky="w", pady=5)
        self.entry_flow = ttk.Entry(tab_basis, width=10); self.entry_flow.grid(row=10, column=1, sticky="w", pady=2)
        ttk.Label(tab_basis, text="Pressure Adv:").grid(row=11, column=0, sticky="w", pady=5)
        self.entry_pa = ttk.Entry(tab_basis); self.entry_pa.grid(row=11, column=1, sticky="ew", pady=2)

        ttk.Separator(tab_basis, orient="horizontal").grid(row=12, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(tab_basis, text="Lagerort:").grid(row=13, column=0, sticky="w", pady=5)
        self.combo_type = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN)
        self.combo_type.grid(row=13, column=1, sticky="ew", pady=2); self.combo_type.bind("<<ComboboxSelected>>", self.update_slot_dropdown)
        ttk.Label(tab_basis, text="Slot / Nr.:").grid(row=14, column=0, sticky="w", pady=5)
        self.combo_loc_id = ttk.Combobox(tab_basis, font=FONT_MAIN); self.combo_loc_id.grid(row=14, column=1, sticky="ew", pady=2)
        
        self.var_reorder = tk.BooleanVar()
        ttk.Checkbutton(tab_basis, text="Auf Einkaufsliste setzen!", variable=self.var_reorder).grid(row=15, column=0, columnspan=2, sticky="w", pady=10)

        # TAB 2: ERP (Kaufmännisch)
        ttk.Label(tab_erp, text="Lieferant / Shop:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_supplier = ttk.Entry(tab_erp); self.entry_supplier.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="SKU / Art-Nr.:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_sku = ttk.Entry(tab_erp); self.entry_sku.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Preis (€):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_price = ttk.Entry(tab_erp); self.entry_price.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Link:").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_link = ttk.Entry(tab_erp); self.entry_link.grid(row=3, column=1, sticky="ew", pady=2)
        
        ttk.Separator(tab_erp, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(tab_erp, text="Nozzle Temp (°C):").grid(row=5, column=0, sticky="w", pady=5)
        self.entry_temp_n = ttk.Entry(tab_erp); self.entry_temp_n.grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Bed Temp (°C):").grid(row=6, column=0, sticky="w", pady=5)
        self.entry_temp_b = ttk.Entry(tab_erp); self.entry_temp_b.grid(row=6, column=1, sticky="ew", pady=2)

        # AKTIONEN UNTEN
        btn_frame = ttk.Frame(sidebar)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="📦 Regal & AMS Ansicht", command=lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools)).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="📷 QR Code generieren", command=self.show_qr_code).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🧵 Leerspulen verwalten", command=lambda: SpoolManager(self.root, self.update_spool_dropdown)).pack(fill="x", pady=2)
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(btn_frame, text="Neu Hinzufügen", command=self.add_filament, style="Accent.TButton").pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Änderungen Speichern", command=self.update_filament).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Felder leeren", command=self.clear_inputs).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Löschen", command=self.delete_filament, style="Delete.TButton").pack(fill="x", pady=8)

        # -- TABELLE --
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side="right", fill="both", expand=True)
        columns = ("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="tree headings")
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y"); self.tree.pack(fill="both", expand=True)

        self.tree.column("#0", width=40, anchor="center", stretch=False)
        for col, text in zip(columns, ["ID", "Marke", "Material", "Farbe", "Finish", "Rest(g)", "Flow", "Ort", "Status"]):
            self.tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(c, False))
        
        self.tree.column("id", width=40, anchor="center"); self.tree.column("brand", width=120)
        self.tree.column("material", width=60, anchor="center"); self.tree.column("weight", width=60, anchor="center")
        self.tree.column("flow", width=50, anchor="center"); self.tree.column("status", width=90, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        self.update_locations_dropdown(); self.update_spool_dropdown() 
        self.clear_inputs(); self.refresh_table()
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def update_color_preview(self, event=None):
        text = self.combo_color.get()
        colors = get_colors_from_text(text)
        self.current_color_icon = create_color_icon(colors, (30, 20), "#888888")
        self.lbl_color_preview.config(image=self.current_color_icon)
        self.lbl_color_preview.image = self.current_color_icon

    def open_paypal(self):
        msg = (
            "In das Tool ist eine Menge Zeit und Entwicklung geflossen. "
            "Ich möchte es weiterhin kostenlos anbieten. Wenn dir das Tool "
            "gefällt, freue ich mich über einen virtuellen Kaffee von dir!\n\n"
            "Möchtest du zur PayPal-Seite weitergeleitet werden?"
        )
        if messagebox.askyesno("☕ Kaffee spendieren", msg):
            webbrowser.open("https://paypal.me/florianfranck")

    def check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'VibeSpool-App'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                latest = data.get("tag_name", "").replace("v", "")
                
                # DER DOWNGRADE-FIX: Echter Versionsnummern-Vergleich
                if latest:
                    l_parts = [int(x) for x in latest.split(".") if x.isdigit()]
                    c_parts = [int(x) for x in APP_VERSION.split(".") if x.isdigit()]
                    if l_parts > c_parts:
                        self.root.after(2000, lambda: self.show_update_prompt(latest, data.get("html_url")))
        except: pass 

    def show_update_prompt(self, latest, url):
        if messagebox.askyesno("Update", f"Neue Version ({latest}) verfügbar!\nZur Download-Seite?"): webbrowser.open(url)

    def on_closing(self):
        self.settings["geometry"] = self.root.geometry(); save_json(SETTINGS_FILE, self.settings); self.root.destroy()

    def apply_theme(self):
        theme = self.settings.get("theme", "dark")
        c = THEMES[theme]
        self.root.configure(bg=c["bg"])
        self.style.configure(".", background=c["bg"], foreground=c["fg"], font=FONT_MAIN)
        self.style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        self.style.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        self.style.configure("TLabelframe.Label", background=c["bg"], foreground=c["lbl_frame"])
        self.style.configure("Treeview", background=c["tree_bg"], fieldbackground=c["tree_bg"], foreground=c["tree_fg"])
        self.style.configure("Treeview.Heading", background=c["head_bg"], foreground=c["head_fg"])
        self.style.configure("TCombobox", fieldbackground=c["entry_bg"], foreground=c["entry_fg"], background=c["bg"])
        self.style.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["entry_fg"])
        self.style.configure("TButton", background=c["bg"], foreground=c["fg"])
        self.style.map("Treeview", background=[("selected", COLOR_ACCENT)])
        self.style.configure("Accent.TButton", foreground="white", background=COLOR_ACCENT, borderwidth=0)
        self.style.configure("Delete.TButton", foreground="white", background=COLOR_DELETE, borderwidth=0)

    def toggle_theme(self):
        self.settings["theme"] = "dark" if self.settings.get("theme") == "light" else "light"
        save_json(SETTINGS_FILE, self.settings); self.apply_theme(); self.update_theme_button_text()

    def update_theme_button_text(self):
        self.btn_theme.config(text="☀️" if self.settings.get("theme") == "dark" else "🌙")

    def get_dynamic_locations(self):
        raw = self.settings.get("shelves", "REGAL|4|8")
        locs = [s.split("|")[0].strip() for s in raw.split(",") if "|" in s]
        for i in range(1, self.settings.get("num_ams", 1) + 1): locs.append(f"AMS {i}")
        for c in self.settings.get("custom_locs", "").split(","):
            if c.strip(): locs.append(c.strip())
        locs.extend(["LAGER", "VERBRAUCHT"])
        return locs

    def update_locations_dropdown(self): self.combo_type['values'] = self.get_dynamic_locations()

    def update_spool_dropdown(self):
        values = ["-"] + [f"{s['id']} - {s['name']}" for s in self.spools]
        curr = self.combo_spool.get()
        self.combo_spool['values'] = values
        if curr not in values: self.combo_spool.current(0)

    def get_selected_spool_id(self):
        val = self.combo_spool.get()
        try: return -1 if val == "-" else int(val.split(" - ")[0])
        except: return -1

    def calculate_net_weight(self, item):
        try:
            gross = float(str(item.get('weight_gross', '0')).replace(',', '.'))
            sid = int(item.get('spool_id', -1))
            spool = next((s for s in self.spools if s['id'] == sid), None)
            return max(0, int(gross - (spool['weight'] if spool else 0)))
        except: return 0

    def update_net_weight_display(self, event=None):
        try:
            gross = float(self.entry_gross.get().strip().replace(',', '.'))
            sid = self.get_selected_spool_id()
            spool = next((s for s in self.spools if s['id'] == sid), None)
            net = gross - (spool['weight'] if spool else 0)
            self.lbl_net_weight.config(text=f"Netto: {max(0, int(net))} g")
        except: self.lbl_net_weight.config(text="Netto: 0 g")

    def open_settings(self):
        def on_save(new_settings):
            self.settings = new_settings; save_json(SETTINGS_FILE, self.settings)
            self.update_locations_dropdown(); self.update_slot_dropdown()
        SettingsDialog(self.root, self.settings, on_save)

    def update_slot_dropdown(self, event=None):
        loc = self.combo_type.get()
        if loc.startswith("AMS"): self.combo_loc_id['values'] = ["1", "2", "3", "4"]
        else:
            raw = self.settings.get("shelves", "REGAL|4|8")
            for s in raw.split(","):
                parts = s.split("|")
                if len(parts) >= 3 and parts[0].strip() == loc:
                    lbl_r, lbl_c = self.settings.get("label_row", "Fach"), self.settings.get("label_col", "Slot")
                    rows, cols = int(parts[1]), int(parts[2])
                    row_range = range(rows, 0, -1) if self.settings.get("logistics_order") else range(1, rows + 1)
                    self.combo_loc_id['values'] = [f"{lbl_r} {r} - {lbl_c} {c}" for r in row_range for c in range(1, cols + 1)]
                    return
            self.combo_loc_id['values'] = ["-"]

    def treeview_sort_column(self, col, reverse):
        def sort_key(item):
            val = item.get(col, "")
            if col == "location": return f"{item['type']}_{str(item['loc_id']).zfill(3)}"
            if col == "weight": return self.calculate_net_weight(item)
            if col == "id": return int(val)
            return str(val).lower()
        self.inventory.sort(key=sort_key, reverse=reverse)
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))
        self.refresh_table()

    def verify_data_integrity(self):
        max_id, changed = 0, False
        for item in self.inventory:
            if 'id' in item:
                try: max_id = max(max_id, int(item['id']))
                except: pass
            if item.get('type') == 'AMS': item['type'] = 'AMS 1'; changed = True
        for item in self.inventory:
            if 'id' not in item or str(item['id']).strip() == "":
                max_id += 1; item['id'] = max_id; changed = True
        if changed: self.save_data()

    def get_filtered_inventory(self):
        search, mode = self.search_var.get().lower(), self.filter_var.get()
        return [i for i in self.inventory if 
                (mode == "ALL" or (mode == "AMS" and str(i["type"]).startswith("AMS")) or i["type"] == mode) and 
                (not search or search in f"{i['id']} {i['brand']} {i['color']} {i['material']}".lower()) and
                (mode in ["VERBRAUCHT", "ALL"] or i["type"] != "VERBRAUCHT")]

    def refresh_table(self, *args):
        self.icon_cache = []
        for row in self.tree.get_children(): self.tree.delete(row)
        for i in self.get_filtered_inventory():
            loc_str = f"{i['type']} {i.get('loc_id', '')}".strip()
            status = " | ".join(filter(None, ["VERBRAUCHT" if i['type'] == "VERBRAUCHT" else "", "KAUFEN" if i.get('reorder') else ""]))
            icon = create_color_icon(get_colors_from_text(i['color']))
            self.icon_cache.append(icon)
            tags = ["alert"] if i.get('reorder') else ["grayed"] if i['type'] == "VERBRAUCHT" else []
            self.tree.insert("", "end", iid=str(i['id']), image=icon, values=(
                i['id'], i['brand'], i.get('material', '-'), i['color'], i.get('subtype', 'Standard'), 
                f"{self.calculate_net_weight(i)}g", i.get('flow', 'Auto' if 'bambu' in i['brand'].lower() else '-'), loc_str, status), tags=tags)
        self.tree.tag_configure("alert", background="#ffe6e6", foreground="#d9534f")
        self.tree.tag_configure("grayed", foreground="#999999")

    def get_input_data(self):
        try:
            return {
                "id": int(self.entry_id.get().strip()) if self.entry_id.get().strip() else None,
                "brand": self.entry_brand.get().strip(), "material": self.combo_material.get().strip(),
                "color": self.combo_color.get().strip(), "subtype": self.combo_subtype.get().strip(),
                "type": self.combo_type.get(), "loc_id": self.combo_loc_id.get().strip(),
                "flow": self.entry_flow.get().strip(), "pa": self.entry_pa.get().strip(),
                "spool_id": self.get_selected_spool_id(), "weight_gross": float(self.entry_gross.get().strip().replace(',', '.') or 0),
                "is_empty": self.combo_type.get() == "VERBRAUCHT", "reorder": self.var_reorder.get(),
                "supplier": self.entry_supplier.get().strip(), "sku": self.entry_sku.get().strip(),
                "price": self.entry_price.get().strip(), "link": self.entry_link.get().strip(),
                "temp_n": self.entry_temp_n.get().strip(), "temp_b": self.entry_temp_b.get().strip()
            }
        except: messagebox.showwarning("Fehler", "Zahlenformat ungültig."); return None

    def add_filament(self):
        d = self.get_input_data()
        if not d or not d['brand'] or not d['color']: return messagebox.showwarning("Fehler", "Marke und Farbe fehlen.")
        d['id'] = d['id'] or (max([int(i['id']) for i in self.inventory], default=0) + 1)
        if any(i['id'] == d['id'] for i in self.inventory): return messagebox.showerror("Fehler", "ID existiert bereits.")
        self.inventory.append(d); self.save_data(); self.refresh_table(); self.clear_inputs()

    def update_filament(self):
        sel = self.tree.selection()
        if not sel: return
        d = self.get_input_data()
        if not d: return
        idx = next(i for i, item in enumerate(self.inventory) if item['id'] == int(sel[0]))
        d['id'] = d['id'] or int(sel[0])
        self.inventory[idx] = d; self.save_data(); self.refresh_table(); self.tree.selection_set(str(d['id']))

    def delete_filament(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Löschen", "Wirklich löschen?"): return
        self.inventory = [i for i in self.inventory if i['id'] != int(sel[0])]
        self.save_data(); self.refresh_table(); self.clear_inputs()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        i = next((x for x in self.inventory if x['id'] == int(sel[0])), None)
        if not i: return
        self.clear_inputs(deselect=False)
        self.entry_id.insert(0, str(i['id'])); self.entry_brand.insert(0, i['brand'])
        self.combo_material.set(i.get('material', 'PLA')); self.combo_color.set(i['color'])
        self.combo_subtype.set(i.get('subtype', 'Standard')); self.update_color_preview()
        
        if i['type'] not in self.combo_type['values']: self.combo_type['values'] = list(self.combo_type['values']) + [i['type']]
        self.combo_type.set(i['type']); self.update_slot_dropdown(); self.combo_loc_id.set(i.get('loc_id', ''))
        
        self.entry_flow.insert(0, i.get('flow', '')); self.entry_pa.insert(0, i.get('pa', ''))
        self.var_reorder.set(i.get('reorder', False))
        
        for val in self.combo_spool['values']:
            if val.startswith(f"{i.get('spool_id', -1)} -"): self.combo_spool.set(val); break
        gross_val = str(i.get('weight_gross', '0')).replace(',', '.').strip()
        try:
            if gross_val and float(gross_val) > 0: 
                self.entry_gross.insert(0, str(float(gross_val)).rstrip('0').rstrip('.'))
        except ValueError:
            pass
            
        self.update_net_weight_display()
        
        self.entry_supplier.insert(0, i.get('supplier', '')); self.entry_sku.insert(0, i.get('sku', ''))
        self.entry_price.insert(0, i.get('price', '')); self.entry_link.insert(0, i.get('link', ''))
        self.entry_temp_n.insert(0, i.get('temp_n', '')); self.entry_temp_b.insert(0, i.get('temp_b', ''))

    def clear_inputs(self, deselect=True):
        for e in [self.entry_id, self.entry_brand, self.entry_flow, self.entry_pa, self.entry_gross, 
                  self.entry_supplier, self.entry_sku, self.entry_price, self.entry_link, self.entry_temp_n, self.entry_temp_b]:
            e.delete(0, tk.END)
        self.combo_color.set(""); self.combo_loc_id.set("")
        self.combo_material.current(0); self.combo_subtype.current(0); self.combo_type.current(0); self.combo_spool.current(0)
        self.update_net_weight_display(); self.update_slot_dropdown(); self.var_reorder.set(False); self.update_color_preview()
        
        if deselect:
            self.tree.selection_remove(self.tree.selection())

    def on_quick_scan(self, event=None):
        scan_text = self.entry_scan.get().strip()
        if not scan_text: return
        match = re.search(r'(?:ID:\s*|FIL_)?(\d+)', scan_text, re.IGNORECASE)
        if match and self.tree.exists(match.group(1)):
            self.tree.selection_set(match.group(1)); self.tree.see(match.group(1)); self.on_select(None)
            self.entry_scan.delete(0, tk.END)
        else: messagebox.showerror("Fehler", "Keine gültige ID im System gefunden.")

    def show_qr_code(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Info", "Bitte Filament auswählen.")
        i = next(x for x in self.inventory if x['id'] == int(sel[0]))
        qr_win = tk.Toplevel(self.root)
        qr_win.title("QR Code"); qr_win.geometry("300x350"); qr_win.configure(bg=self.root.cget('bg'))
        center_window(qr_win, self.root)
        
        sub = f" ({i.get('subtype')})" if i.get('subtype') and i.get('subtype') != "Standard" else ""
        qr_content = f"ID: {i['id']} | {i['brand']} | {i.get('material', '-')} | {i['color']}{sub}"
        
        qr = qrcode.QRCode(box_size=10, border=4); qr.add_data(qr_content); qr.make(fit=True)
        img = ImageTk.PhotoImage(qr.make_image(fill_color="black", back_color="white"))
        lbl = tk.Label(qr_win, image=img, bg=self.root.cget('bg')); lbl.image = img; lbl.pack(pady=10)
        ttk.Label(qr_win, text=f"ID: {i['id']}\n{i['brand']} {i['color']}", font=FONT_BOLD).pack()

    def save_data(self): save_json(DATA_FILE, self.inventory)

if __name__ == "__main__":
    try: windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk()
    app = FilamentApp(root)
    root.mainloop()