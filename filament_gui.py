import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import shutil
import zipfile
import webbrowser 
import urllib.request 
import threading      
from ctypes import windll
from PIL import Image, ImageTk, ImageDraw
import qrcode 

# --- KONFIGURATION & UPDATE CHECKER ---
APP_VERSION = "1.3"
GITHUB_REPO = "SirMetalizer/VibeSpool"

# --- SICHERER SPEICHERORT FÜR EXE & MAC APP ---
USER_HOME = os.path.expanduser("~")
BASE_DIR = os.path.join(USER_HOME, "VibeSpool_Daten") # Absoluter Fallback

# Wir suchen den "echten" Dokumente-Ordner (beachtet OneDrive und deutsche Windows-Versionen)
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

# Migration: Falls alte Dateien noch im selben Ordner liegen, kopiere sie in den neuen Ordner
if os.path.exists("inventory.json") and not os.path.exists(DATA_FILE):
    try:
        shutil.copy("inventory.json", DATA_FILE)
        if os.path.exists("settings.json"): shutil.copy("settings.json", SETTINGS_FILE)
        if os.path.exists("spools.json"): shutil.copy("spools.json", SPOOLS_FILE)
    except: pass

# --- DEFAULTS ---
DEFAULT_SETTINGS = {
    "shelf_rows": 4,      
    "shelf_cols": 8,      
    "num_ams": 1,
    "custom_locs": "Filamenttrockner, Samla Box",
    "geometry": "1500x850",
    "theme": "light"
}

MATERIALS = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF", "PVA", "Sonstiges"]
SUBTYPES = ["Standard", "Matte", "Silk", "High Speed", "Dual Color", "Tri Color", "Glow in Dark", "Marmor", "Holz", "Glitzer/Sparkle", "Transparent"]

# --- THEMES ---
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
    "rot": "#FF0000", "red": "#FF0000", "dunkelrot": "#8B0000", "blau": "#0000FF", "blue": "#0000FF", "hellblau": "#ADD8E6", 
    "dunkelblau": "#00008B", "navy": "#000080", "indigo": "#4B0082", "grün": "#008000", "green": "#008000", "hellgrün": "#90EE90", 
    "dunkelgrün": "#006400", "army": "#4B5320", "oliv": "#808000", "forest": "#228B22", "gelb": "#FFD700", "yellow": "#FFD700",
    "orange": "#FFA500", "lila": "#800080", "purple": "#800080", "violett": "#EE82EE", "lavendel": "#E6E6FA", "pink": "#FFC0CB", 
    "magenta": "#FF00FF", "rose": "#FF007F", "rosa": "#FFC0CB", "schwarz": "#000000", "black": "#000000", "weiß": "#F0F0F0", 
    "white": "#F0F0F0", "ivory": "#FFFFF0", "grau": "#808080", "grey": "#808080", "silber": "#C0C0C0", "silver": "#C0C0C0", 
    "ash": "#B2BEB5", "braun": "#A52A2A", "brown": "#A52A2A", "cocoa": "#D2691E", "bronze": "#CD7F32", "gold": "#DAA520", 
    "kupfer": "#B87333", "cyan": "#00FFFF", "türkis": "#40E0D0", "teal": "#008080", "beige": "#F5F5DC", "khaki": "#F0E68C",
    "rainbow": "RAINBOW", "bunt": "RAINBOW", "regenbogen": "RAINBOW"
}

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
    except Exception as e:
        print(f"Fehler beim Speichern von {filename}: {e}")

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

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
ROW_HEIGHT = 30             

class SpoolManager(tk.Toplevel):
    def __init__(self, parent, on_close_callback):
        super().__init__(parent)
        self.on_close_callback = on_close_callback
        self.title("Spulen Datenbank")
        self.geometry("600x700")
        self.minsize(500, 600)
        self.configure(bg=parent.cget('bg')) 
        
        self.spools = load_json(SPOOLS_FILE, [])
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
        try:
            spool_id = int(sel[0])
            spool = next((s for s in self.spools if s['id'] == spool_id), None)
            if spool:
                self.ent_name.delete(0, tk.END)
                self.ent_name.insert(0, spool['name'])
                self.ent_weight.delete(0, tk.END)
                self.ent_weight.insert(0, str(spool['weight']))
        except: pass

    def add_spool(self):
        name = self.ent_name.get().strip()
        weight_str = self.ent_weight.get().strip().replace(',', '.')
        if not name or not weight_str: return
        try:
            weight = int(float(weight_str))
            new_id = 1
            if self.spools: new_id = max(s['id'] for s in self.spools) + 1
            self.spools.append({"id": new_id, "name": name, "weight": weight})
            save_json(SPOOLS_FILE, self.spools)
            self.refresh_list()
            self.ent_name.delete(0, tk.END)
            self.ent_weight.delete(0, tk.END)
        except ValueError: messagebox.showerror("Fehler", "Gewicht muss Zahl sein.")

    def update_spool(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            weight = int(float(self.ent_weight.get().strip().replace(',', '.')))
            spool_id = int(sel[0])
            for s in self.spools:
                if s['id'] == spool_id:
                    s['name'] = self.ent_name.get().strip()
                    s['weight'] = weight
            save_json(SPOOLS_FILE, self.spools)
            self.refresh_list()
        except: pass

    def delete_spool(self):
        sel = self.tree.selection()
        if not sel: return
        spool_id = int(sel[0])
        self.spools = [s for s in self.spools if s['id'] != spool_id]
        save_json(SPOOLS_FILE, self.spools)
        self.refresh_list()
        self.ent_name.delete(0, tk.END)
        self.ent_weight.delete(0, tk.END)

    def destroy(self):
        self.on_close_callback()
        super().destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_settings, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Einstellungen & Lagerorte")
        self.geometry("450x400")
        self.configure(bg=parent.cget('bg'))
        ttk.Label(self, text="Regal Layout & Lagerorte", font=("Segoe UI", 10, "bold")).pack(pady=15)
        frm = ttk.Frame(self)
        frm.pack(padx=20, pady=10, fill="x")
        
        self.entries = {}
        labels = [("Fächer (Zeilen):", "shelf_rows"), ("Slots pro Fach:", "shelf_cols"), ("Anzahl AMS Geräte:", "num_ams")]
        
        for i, (txt, key) in enumerate(labels):
            ttk.Label(frm, text=txt).grid(row=i, column=0, sticky="w", pady=5)
            e = ttk.Entry(frm, width=10)
            e.insert(0, str(current_settings.get(key, 1 if key=="num_ams" else 4)))
            e.grid(row=i, column=1, pady=5, sticky="w")
            self.entries[key] = e
            
        ttk.Label(frm, text="Weitere Orte (Kommagetrennt):").grid(row=4, column=0, sticky="w", pady=(15,5))
        self.ent_custom = ttk.Entry(frm)
        self.ent_custom.insert(0, current_settings.get("custom_locs", "Filamenttrockner, Samla Box"))
        self.ent_custom.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)
            
        ttk.Button(self, text="Speichern", command=self.save).pack(pady=20, fill="x", padx=20)

    def save(self):
        try:
            new_s = {k: int(v.get()) for k, v in self.entries.items()}
            new_s["custom_locs"] = self.ent_custom.get().strip()
            self.on_save(new_s)
            self.destroy()
        except: messagebox.showerror("Fehler", "Bitte bei den ersten 3 Feldern nur ganze Zahlen eingeben.")

class ShelfVisualizer(tk.Toplevel):
    def __init__(self, parent, inventory, settings, spools):
        super().__init__(parent)
        self.inventory = inventory
        self.settings = settings
        self.spools = spools
        self.title("Regal & AMS Übersicht")
        self.geometry("1100x850")
        
        bg_col = parent.cget('bg')
        self.configure(bg=bg_col)
        self.image_cache = []
        
        self.shelf_data = {}
        self.ams_data = {}
        for item in self.inventory:
            try:
                loc = str(item.get('loc_id', ''))
                if item['type'] == "REGAL": self.shelf_data[loc] = item
                elif str(item['type']).startswith("AMS"): self.ams_data[f"{item['type']}_{loc}"] = item
            except: pass

        canvas = tk.Canvas(self, bg=bg_col, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        pad = ttk.Frame(frame, padding=20)
        pad.pack(fill="both", expand=True)
        
        rows = self.settings.get("shelf_rows", 4)
        cols = self.settings.get("shelf_cols", 8)
        
        ttk.Label(pad, text="Regal Lager", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        for r in range(1, rows + 1):
            lbl = ttk.Label(pad, text=f"Fach {r}", font=("Segoe UI", 10, "bold"))
            lbl.pack(anchor="w", pady=(5, 2))
            row_frame = tk.Frame(pad, bg="#8B4513", padx=5, pady=5)
            row_frame.pack(fill="x", pady=2)
            
            for c in range(1, cols + 1):
                slot_name = f"Fach {r} - Slot {c}"
                item = self.shelf_data.get(slot_name)
                self.draw_slot(row_frame, str(((r-1)*cols)+c), item, False)

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

    def get_net_weight(self, item):
        try:
            gross_str = str(item.get('weight_gross', '0')).replace(',', '.')
            gross = float(gross_str)
            if gross <= 0: return 0 
            
            sid = int(item.get('spool_id', -1))
            spool = next((s for s in self.spools if s['id'] == sid), None)
            tare = spool['weight'] if spool else 0
            return max(0, int(gross - tare))
        except: return 0

    def draw_slot(self, parent, label, item, is_ams, w=90, h=80):
        bg_colors = ["#D2B48C"]
        fg_col = "#555"
        if is_ams:
            bg_colors = ["#666666"]
            fg_col = "#CCC"
            
        txt = f"{label}\nLEER"
        tooltip = "Leer"
        
        if item:
            cols = get_colors_from_text(item['color'])
            if cols:
                bg_colors = cols
                c1 = cols[0]
                if c1.startswith("#"):
                    r = int(c1[1:3], 16); g = int(c1[3:5], 16); b = int(c1[5:7], 16)
                    if (r*0.299 + g*0.587 + b*0.114) < 128: fg_col = "white"
                    else: fg_col = "black"
            else:
                bg_colors = ["#FFFFFF"]
                fg_col = "black"
            
            sub = item.get('subtype', '')
            net = self.get_net_weight(item)
            w_str = f"{net}g"
            
            txt = f"{label}\n{item['brand'][:8]}\n{sub[:8]}\n{w_str}"
            tooltip = f"ID: {item['id']}\n{item['brand']} - {item['color']}\n{item['material']}\n{sub}\nRest: {w_str}"

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

class FlowCalculator(tk.Toplevel):
    def __init__(self, parent, current_flow, on_apply):
        super().__init__(parent)
        self.on_apply = on_apply
        self.title("Flow Kalibrierung")
        self.geometry("400x550")
        self.configure(bg=parent.cget('bg'))
        ttk.Label(self, text="Flow Berechnen", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        frm = ttk.LabelFrame(self, text="Werte")
        frm.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Label(frm, text="Aktueller Flow:").grid(row=0, column=0, pady=5)
        self.e_flow = ttk.Entry(frm); self.e_flow.insert(0, str(current_flow)); self.e_flow.grid(row=0, column=1)
        
        ttk.Label(frm, text="Zielwert:").grid(row=1, column=0, pady=5)
        self.e_target = ttk.Entry(frm); self.e_target.insert(0, "0.45"); self.e_target.grid(row=1, column=1)
        
        ttk.Label(frm, text="Messungen:").grid(row=2, column=0, columnspan=2, pady=10)
        self.entries = []
        for i in range(9):
            e = ttk.Entry(frm, width=8)
            e.grid(row=3+(i//3), column=i%3, padx=2, pady=2)
            self.entries.append(e)
            
        ttk.Button(self, text="Übernehmen", command=self.calc).pack(pady=10)

    def calc(self):
        try:
            vals = []
            for e in self.entries:
                s = e.get().replace(",", ".").strip()
                if s: vals.append(float(s))
            if not vals: return
            avg = sum(vals)/len(vals)
            target = float(self.e_target.get().replace(",", "."))
            old = float(self.e_flow.get().replace(",", "."))
            new_flow = round(old * (target / avg), 4)
            self.on_apply(new_flow)
            self.destroy()
        except: messagebox.showerror("Fehler", "Ungültige Eingabe")

class BackupDialog(tk.Toplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.title("Backup & Wiederherstellung")
        self.geometry("400x200")
        self.configure(bg=parent.cget('bg'))
        
        ttk.Label(self, text="Datenbank Backup & Restore", font=("Segoe UI", 12, "bold")).pack(pady=15)
        
        ttk.Button(self, text="📥 Backup erstellen (Exportieren)", command=self.export_data).pack(fill="x", padx=40, pady=10)
        ttk.Button(self, text="📤 Backup laden (Importieren)", command=self.import_data).pack(fill="x", padx=40, pady=10)
        
    def export_data(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".zip", 
            filetypes=[("ZIP Archive", "*.zip")], 
            initialfile="VibeSpool_Backup.zip",
            title="Backup speichern unter..."
        )
        if not filepath: return
        
        try:
            with zipfile.ZipFile(filepath, 'w') as zipf:
                if os.path.exists(DATA_FILE): zipf.write(DATA_FILE, "inventory.json")
                if os.path.exists(SETTINGS_FILE): zipf.write(SETTINGS_FILE, "settings.json")
                if os.path.exists(SPOOLS_FILE): zipf.write(SPOOLS_FILE, "spools.json")
            messagebox.showinfo("Erfolg", "Backup erfolgreich erstellt!", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Backup fehlgeschlagen:\n{e}", parent=self)

    def import_data(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("ZIP Archive", "*.zip")],
            title="Backup-Datei auswählen..."
        )
        if not filepath: return
        
        if messagebox.askyesno("Warnung", "ACHTUNG: Alle aktuellen Daten werden überschrieben!\n\nWillst du das Backup wirklich laden?", parent=self):
            try:
                with zipfile.ZipFile(filepath, 'r') as zipf:
                    zipf.extractall(BASE_DIR)
                
                # Daten neu in den Arbeitsspeicher laden
                self.app.inventory = load_json(DATA_FILE, [])
                self.app.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
                self.app.spools = load_json(SPOOLS_FILE, [])
                self.app.verify_data_integrity()
                self.app.apply_theme()
                self.app.update_locations_dropdown()
                self.app.update_spool_dropdown()
                self.app.clear_inputs()
                self.app.refresh_table()
                
                messagebox.showinfo("Erfolg", "Backup erfolgreich geladen! Deine Daten sind wieder da.", parent=self.app.root)
                self.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Import fehlgeschlagen:\n{e}", parent=self)

# --- MAIN APP ---
class FilamentApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"VibeSpool v{APP_VERSION}")
        self.icon_cache = []
        
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.spools = load_json(SPOOLS_FILE, []) 
        
        geom = self.settings.get("geometry", "1500x850")
        self.root.geometry(geom)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.apply_theme()

        self.inventory = load_json(DATA_FILE, [])
        self.verify_data_integrity() 

        # --- UI TOP BAR ---
        top_bar = ttk.Frame(root, padding=10)
        top_bar.pack(fill="x", side="top")
        ttk.Label(top_bar, text="Suche:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.refresh_table())
        ttk.Entry(top_bar, textvariable=self.search_var, width=20).pack(side="left", padx=5)
        ttk.Label(top_bar, text="   Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value="ALL")
        
        filter_modes = ["ALL", "REGAL"] + [f"AMS {i}" for i in range(1, self.settings.get("num_ams", 1)+1)] + ["LAGER", "VERBRAUCHT"]
        for mode in filter_modes:
            ttk.Radiobutton(top_bar, text=mode if mode != "ALL" else "Alle", variable=self.filter_var, value=mode, command=self.refresh_table).pack(side="left", padx=3)
            
        ttk.Label(top_bar, text="     Quick-ID:").pack(side="left", padx=(10,0))
        self.entry_scan = ttk.Entry(top_bar, width=8)
        self.entry_scan.pack(side="left", padx=5)
        self.entry_scan.bind("<Return>", self.on_quick_scan)
        ttk.Button(top_bar, text="Go", width=4, command=self.on_quick_scan).pack(side="left")
        
        # --- RECHTE BUTTONS ---
        ttk.Button(top_bar, text="⚙ Einstellungen", command=self.open_settings).pack(side="right", padx=5)
        # NEU: BACKUP BUTTON
        ttk.Button(top_bar, text="💾 Backup", command=self.open_backup).pack(side="right", padx=5)
        ttk.Button(top_bar, text="ℹ️ Infos", command=self.show_info).pack(side="right", padx=5)
        ttk.Button(top_bar, text="☕ Spenden", command=self.open_paypal).pack(side="right", padx=5)
        
        self.btn_theme = ttk.Button(top_bar, text="...", command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)
        self.update_theme_button_text()

        # --- MAIN AREA ---
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill="both", expand=True)

        # -- SIDEBAR --
        input_frame = ttk.LabelFrame(main_frame, text=" Filament Details ", padding=15)
        input_frame.pack(side="left", fill="y", padx=(0, 20))

        ttk.Label(input_frame, text="ID:").grid(row=0, column=0, sticky="w")
        self.entry_id = ttk.Entry(input_frame, width=10, font=FONT_BOLD)
        self.entry_id.grid(row=0, column=1, sticky="w", pady=2)
        
        ttk.Label(input_frame, text="Marke:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_brand = ttk.Entry(input_frame, font=FONT_MAIN)
        self.entry_brand.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(input_frame, text="Material:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_material = ttk.Combobox(input_frame, values=MATERIALS, state="readonly", font=FONT_MAIN)
        self.combo_material.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(input_frame, text="Farbe:").grid(row=3, column=0, sticky="w", pady=5)
        color_container = ttk.Frame(input_frame)
        color_container.grid(row=3, column=1, sticky="ew", pady=2)
        self.entry_color = ttk.Entry(color_container, font=FONT_MAIN)
        self.entry_color.pack(side="left", fill="x", expand=True)
        self.entry_color.bind("<KeyRelease>", self.update_color_preview)
        self.lbl_color_preview = tk.Label(color_container, width=4, bg="#FFFFFF", relief="solid", borderwidth=1)
        self.lbl_color_preview.pack(side="right", padx=(5,0))
        ttk.Label(input_frame, text="Finish:").grid(row=4, column=0, sticky="w", pady=5)
        self.combo_subtype = ttk.Combobox(input_frame, values=SUBTYPES, font=FONT_MAIN) 
        self.combo_subtype.grid(row=4, column=1, sticky="ew", pady=2)

        ttk.Separator(input_frame, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(input_frame, text="Spule:").grid(row=6, column=0, sticky="w", pady=5)
        self.combo_spool = ttk.Combobox(input_frame, state="readonly", font=FONT_MAIN)
        self.combo_spool.grid(row=6, column=1, sticky="ew", pady=2)
        self.combo_spool.bind("<<ComboboxSelected>>", self.update_net_weight_display)
        
        ttk.Button(input_frame, text="🧵 Spulen verwalten", command=self.open_spool_manager).grid(row=7, column=1, sticky="e", pady=2)

        ttk.Label(input_frame, text="Brutto Gew. (g):").grid(row=8, column=0, sticky="w", pady=5)
        self.entry_gross = ttk.Entry(input_frame, font=FONT_MAIN)
        self.entry_gross.grid(row=8, column=1, sticky="ew", pady=2)
        self.entry_gross.bind("<KeyRelease>", self.update_net_weight_display)

        self.lbl_net_weight = ttk.Label(input_frame, text="Netto: 0 g", font=("Segoe UI", 9, "bold"), foreground=COLOR_ACCENT)
        self.lbl_net_weight.grid(row=9, column=1, sticky="w")

        ttk.Separator(input_frame, orient="horizontal").grid(row=10, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(input_frame, text="Flow Ratio:").grid(row=11, column=0, sticky="w", pady=5)
        flow_frame = ttk.Frame(input_frame)
        flow_frame.grid(row=11, column=1, sticky="ew", pady=2)
        self.entry_flow = ttk.Entry(flow_frame, width=8)
        self.entry_flow.pack(side="left")
        ttk.Button(flow_frame, text="🛠", width=3, command=self.open_flow_calculator).pack(side="left", padx=5)
        
        ttk.Label(input_frame, text="Pressure Adv:").grid(row=12, column=0, sticky="w", pady=5)
        self.entry_pa = ttk.Entry(input_frame)
        self.entry_pa.grid(row=12, column=1, sticky="ew", pady=2)

        ttk.Separator(input_frame, orient="horizontal").grid(row=13, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(input_frame, text="Lagerort:").grid(row=14, column=0, sticky="w", pady=5)
        self.combo_type = ttk.Combobox(input_frame, state="readonly", font=FONT_MAIN)
        self.combo_type.grid(row=14, column=1, sticky="ew", pady=2)
        self.combo_type.bind("<<ComboboxSelected>>", self.update_slot_dropdown)
        
        ttk.Label(input_frame, text="Slot / Nr.:").grid(row=15, column=0, sticky="w", pady=5)
        self.combo_loc_id = ttk.Combobox(input_frame, font=FONT_MAIN)
        self.combo_loc_id.grid(row=15, column=1, sticky="ew", pady=2)

        self.var_reorder = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Nachbestellen!", variable=self.var_reorder).grid(row=16, column=1, sticky="w", pady=(10,5))

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=17, column=0, columnspan=2, pady=(15, 0), sticky="ew")
        ttk.Button(btn_frame, text="📦 Regal & AMS Ansicht", command=self.open_shelf_visualizer).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="QR Code", command=self.show_qr_code).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Als Ersatz ins Lager kopieren", command=self.duplicate_as_spare).pack(fill="x", pady=2)
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="Hinzufügen", command=self.add_filament, style="Accent.TButton").pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Speichern", command=self.update_filament).pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Felder leeren", command=self.clear_inputs).pack(fill="x", pady=4)
        ttk.Frame(btn_frame, height=5).pack() 
        ttk.Button(btn_frame, text="Löschen", command=self.delete_filament, style="Delete.TButton").pack(fill="x", pady=4)

        # -- TABELLE --
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side="right", fill="both", expand=True)
        columns = ("id", "brand", "material", "color", "subtype", "weight", "flow", "location", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="tree headings", selectmode="browse")
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.column("#0", width=40, anchor="center", stretch=False)
        self.tree.heading("#0", text="") 
        self.tree.heading("id", text="ID", anchor="center", command=lambda: self.treeview_sort_column("id", False))
        self.tree.heading("brand", text="Marke", anchor="center", command=lambda: self.treeview_sort_column("brand", False))
        self.tree.heading("material", text="Material", anchor="center", command=lambda: self.treeview_sort_column("material", False))
        self.tree.heading("color", text="Farbe", anchor="center", command=lambda: self.treeview_sort_column("color", False))
        self.tree.heading("subtype", text="Finish", anchor="center", command=lambda: self.treeview_sort_column("subtype", False))
        self.tree.heading("weight", text="Rest (g)", anchor="center", command=lambda: self.treeview_sort_column("weight", False)) 
        self.tree.heading("flow", text="Flow", anchor="center", command=lambda: self.treeview_sort_column("flow", False))
        self.tree.heading("location", text="Ort", anchor="center", command=lambda: self.treeview_sort_column("location", False))
        self.tree.heading("status", text="Status", anchor="center", command=lambda: self.treeview_sort_column("status", False))

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("brand", width=120, anchor="center")
        self.tree.column("material", width=80, anchor="center")
        self.tree.column("color", width=140, anchor="center")
        self.tree.column("subtype", width=100, anchor="center")
        self.tree.column("weight", width=80, anchor="center")
        self.tree.column("flow", width=60, anchor="center")
        self.tree.column("location", width=120, anchor="center")
        self.tree.column("status", width=120, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        self.update_locations_dropdown()
        self.update_spool_dropdown() 
        self.clear_inputs()
        self.refresh_table()

        # Update-Checker im Hintergrund starten
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    # --- AUTO UPDATE CHECKER ---
    def check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'VibeSpool-App'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").replace("v", "")
                
                if latest_version and latest_version != APP_VERSION:
                    self.root.after(2000, lambda: self.show_update_prompt(latest_version, data.get("html_url")))
        except Exception:
            pass 

    def show_update_prompt(self, latest_version, url):
        msg = f"Eine neue Version von VibeSpool ({latest_version}) ist verfügbar!\nDeine Version: {APP_VERSION}\n\nMöchtest du zur Download-Seite gehen?"
        if messagebox.askyesno("Update verfügbar!", msg):
            webbrowser.open(url)

    # --- LOGIK FÜR FENSTER & THEMES ---
    
    def on_closing(self):
        self.settings["geometry"] = self.root.geometry()
        save_json(SETTINGS_FILE, self.settings)
        self.root.destroy()

    def apply_theme(self):
        theme = self.settings.get("theme", "light")
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
        self.style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"])
        self.style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
        
        self.style.map("TEntry", fieldbackground=[("active", c["entry_bg"])])
        self.style.map("TCombobox", fieldbackground=[("active", c["entry_bg"])])
        self.style.map("Treeview", background=[("selected", COLOR_ACCENT)])
        
        self.style.configure("Accent.TButton", foreground="white", background=COLOR_ACCENT, borderwidth=0)
        self.style.map("Accent.TButton", background=[("active", "#005a9e")])
        self.style.configure("Delete.TButton", foreground="white", background=COLOR_DELETE, borderwidth=0)
        self.style.map("Delete.TButton", background=[("active", "#c9302c")])

    def toggle_theme(self):
        current = self.settings.get("theme", "light")
        new_theme = "dark" if current == "light" else "light"
        self.settings["theme"] = new_theme
        save_json(SETTINGS_FILE, self.settings)
        self.apply_theme()
        self.update_theme_button_text()

    def update_theme_button_text(self):
        theme = self.settings.get("theme", "light")
        self.btn_theme.config(text="☀️ Light Mode" if theme == "dark" else "🌙 Dark Mode")

    def open_paypal(self):
        msg = (
            "In das Tool ist eine Menge Zeit und Entwicklung geflossen. "
            "Ich möchte es weiterhin kostenlos anbieten. Wenn dir das Tool "
            "gefällt, freue ich mich über einen virtuellen Kaffee von dir!\n\n"
            "Möchtest du zur PayPal-Seite weitergeleitet werden?"
        )
        if messagebox.askyesno("☕ Kaffee spendieren", msg):
            webbrowser.open("https://paypal.me/florianfranck")
            
    def get_dynamic_locations(self):
        locs = ["REGAL"]
        for i in range(1, self.settings.get("num_ams", 1) + 1):
            locs.append(f"AMS {i}")
        
        cust = self.settings.get("custom_locs", "")
        for c in cust.split(","):
            if c.strip(): locs.append(c.strip())
            
        locs.extend(["LAGER", "VERBRAUCHT"])
        return locs

    def update_locations_dropdown(self):
        self.combo_type['values'] = self.get_dynamic_locations()

    def show_info(self):
        info_text = (
            f"VibeSpool v{APP_VERSION}\n\n"
            "Ein lokales Tool zur Verwaltung deiner Filament-Rollen "
            "inklusive Gewichts-Tracking und Regal-Visualisierung.\n\n"
            "Erstellt von Florian Franck via Vibecoding"
        )
        messagebox.showinfo("Über das Programm", info_text)

    def open_backup(self):
        BackupDialog(self.root, self)

    def open_spool_manager(self):
        def on_close():
            self.spools = load_json(SPOOLS_FILE, [])
            self.update_spool_dropdown()
        SpoolManager(self.root, on_close)

    def update_spool_dropdown(self):
        values = ["-"] + [f"{s['id']} - {s['name']}" for s in self.spools]
        current = self.combo_spool.get()
        self.combo_spool['values'] = values
        if current not in values: self.combo_spool.current(0)

    def get_selected_spool_id(self):
        val = self.combo_spool.get()
        if val == "-": return -1
        try:
            return int(val.split(" - ")[0])
        except: return -1

    def calculate_net_weight_for_item(self, item):
        try:
            gross_val = item.get('weight_gross', 0)
            if gross_val == "" or gross_val == "None": return 0 
            gross = float(gross_val)
            
            spool_id = int(item.get('spool_id', -1))
            tare = 0
            if spool_id != -1:
                spool = next((s for s in self.spools if s['id'] == spool_id), None)
                if spool: tare = spool['weight']
            
            net = gross - tare
            return max(0, int(net)) 
        except: return 0

    def update_net_weight_display(self, event=None):
        try:
            gross_str = self.entry_gross.get().strip().replace(',', '.')
            if not gross_str:
                self.lbl_net_weight.config(text="Netto: 0 g")
                return
                
            gross = float(gross_str)
            spool_id = self.get_selected_spool_id()
            tare = 0
            if spool_id != -1:
                spool_data = next((s for s in self.spools if s['id'] == spool_id), None)
                if spool_data: tare = spool_data['weight']
            
            net = gross - tare
            self.lbl_net_weight.config(text=f"Netto: {max(0, int(net))} g")
        except ValueError:
            self.lbl_net_weight.config(text="Netto: 0 g")

    def duplicate_as_spare(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Info", "Bitte erst ein Filament auswählen.")
            return
        fil_id = int(selected[0])
        item = next((i for i in self.inventory if i['id'] == fil_id), None)
        if item:
            new_item = item.copy()
            new_id = 1
            if self.inventory: new_id = max(int(i['id']) for i in self.inventory) + 1
            new_item['id'] = new_id
            new_item['type'] = "LAGER"
            new_item['loc_id'] = "-"
            new_item['is_empty'] = False
            new_item['reorder'] = False
            self.inventory.append(new_item)
            self.save_data()
            self.refresh_table()
            self.tree.see(str(new_id))
            self.tree.selection_set(str(new_id))
            self.on_select(None)
            messagebox.showinfo("Erfolg", f"Filament wurde als ID {new_id} ins Lager kopiert.")

    def open_settings(self):
        def on_settings_saved(new_settings):
            self.settings = new_settings
            save_json(SETTINGS_FILE, self.settings)
            self.update_locations_dropdown()
            self.update_slot_dropdown()
            messagebox.showinfo("Gespeichert", "Einstellungen übernommen.")
        SettingsDialog(self.root, self.settings, on_settings_saved)

    def update_slot_dropdown(self, event=None):
        loc_type = self.combo_type.get()
        if str(loc_type).startswith("AMS"):
            self.combo_loc_id['values'] = ["1", "2", "3", "4"] 
        elif loc_type == "REGAL":
            rows = self.settings.get("shelf_rows", 4)
            cols = self.settings.get("shelf_cols", 8)
            vals = []
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    vals.append(f"Fach {r} - Slot {c}")
            self.combo_loc_id['values'] = vals
        else:
            self.combo_loc_id['values'] = ["-"]

    def treeview_sort_column(self, col, reverse):
        def sort_key(item):
            val = item.get(col, "")
            if col == "location": return f"{item['type']}_{str(item['loc_id']).zfill(3)}"
            if col == "weight": return self.calculate_net_weight_for_item(item)
            if col == "id": return int(val)
            return str(val).lower()
        self.inventory.sort(key=sort_key, reverse=reverse)
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))
        self.refresh_table()

    def open_shelf_visualizer(self):
        ShelfVisualizer(self.root, self.inventory, self.settings, self.spools)

    def verify_data_integrity(self):
        max_id = 0
        changed = False
        cols = self.settings.get('shelf_cols', 8)
        
        for item in self.inventory:
            if 'id' in item:
                try: 
                    iid = int(item['id'])
                    if iid > max_id: max_id = iid
                except: pass
                
            if item.get('type') == 'AMS':
                item['type'] = 'AMS 1'
                changed = True
                
            if item.get('type') == 'REGAL':
                loc = str(item.get('loc_id', ''))
                if loc.isdigit():
                    loc_int = int(loc)
                    r = ((loc_int - 1) // cols) + 1
                    c = ((loc_int - 1) % cols) + 1
                    item['loc_id'] = f"Fach {r} - Slot {c}"
                    changed = True
                    
        for item in self.inventory:
            if 'id' not in item or str(item['id']).strip() == "":
                max_id += 1
                item['id'] = max_id
                changed = True
                
        if changed:
            self.save_data()

    def open_flow_calculator(self):
        curr_val = self.entry_flow.get().strip()
        if not curr_val: curr_val = "0.98" 
        def apply_new_flow(val):
            self.entry_flow.delete(0, tk.END)
            self.entry_flow.insert(0, str(val))
        FlowCalculator(self.root, curr_val, apply_new_flow)

    def update_color_preview(self, event=None):
        text = self.entry_color.get()
        colors = get_colors_from_text(text)
        self.lbl_color_preview.config(bg=colors[0] if colors else "#FFFFFF")

    def get_filtered_inventory(self):
        search = self.search_var.get().lower()
        mode = self.filter_var.get()
        filtered = []
        for item in self.inventory:
            if mode != "ALL":
                if mode == "AMS":
                    if not str(item["type"]).startswith("AMS"): continue
                elif item["type"] != mode: 
                    continue
            
            if mode != "VERBRAUCHT" and mode != "ALL" and item["type"] == "VERBRAUCHT": continue
            
            match_text = f"{item['id']} {item['brand']} {item['color']} {item['material']} {item.get('subtype', '')}".lower()
            if search and search not in match_text: continue
            filtered.append(item)
        return filtered

    def refresh_table(self, *args):
        self.icon_cache = []
        for row in self.tree.get_children(): self.tree.delete(row)
        display_list = self.get_filtered_inventory()
        for item in display_list:
            loc_str = f"{item['type']}"
            if item['loc_id'] and item['loc_id'] != "-": loc_str += f" {item['loc_id']}"
            status_parts = []
            if item['type'] == "VERBRAUCHT": status_parts.append("VERBRAUCHT")
            if item['reorder']: status_parts.append("KAUFEN")
            status_str = " | ".join(status_parts)
            color_text = item['color']
            icon = create_color_icon(get_colors_from_text(color_text))
            self.icon_cache.append(icon)
            tags_for_row = []
            if item['reorder']: tags_for_row.append("alert")
            if item['type'] == "VERBRAUCHT": tags_for_row.append("grayed")
            flow = item.get('flow', '-')
            if not flow and "bambu" in item['brand'].lower(): flow = "Auto"
            sub = item.get('subtype', 'Standard')
            
            net_weight = self.calculate_net_weight_for_item(item)
            item['weight_net'] = net_weight 
            weight_str = f"{net_weight} g"

            self.tree.insert("", "end", iid=str(item['id']), text="", image=icon,
                             values=(item['id'], item['brand'], item.get('material', '-'), 
                                     color_text, sub, weight_str, flow, loc_str, status_str), 
                             tags=tags_for_row)
        self.tree.tag_configure("alert", background="#ffe6e6", foreground="#d9534f")
        self.tree.tag_configure("grayed", foreground="#999999")

    def get_input_data(self):
        id_str = self.entry_id.get().strip()
        fil_id = None
        if id_str:
            try: fil_id = int(id_str)
            except: 
                messagebox.showwarning("Fehler", "Die ID muss eine Zahl sein.")
                return None

        brand = self.entry_brand.get().strip()
        material = self.combo_material.get().strip()
        color = self.entry_color.get().strip()
        subtype = self.combo_subtype.get().strip()
        l_type = self.combo_type.get()
        l_id = self.combo_loc_id.get().strip() 
        flow = self.entry_flow.get().strip()
        pa = self.entry_pa.get().strip()
        
        spool_id = self.get_selected_spool_id()
        gross_str = self.entry_gross.get().strip().replace(',', '.')
        try:
            gross = float(gross_str) if gross_str else 0.0
        except ValueError:
            gross = 0.0
        
        if not brand or not color:
            messagebox.showwarning("Fehler", "Bitte Marke und Farbe ausfüllen.")
            return None

        return {
            "id": fil_id,
            "brand": brand,
            "material": material,
            "color": color,
            "subtype": subtype,
            "type": l_type,
            "loc_id": l_id,
            "flow": flow,
            "pa": pa,
            "spool_id": spool_id,
            "weight_gross": gross,
            "is_empty": (l_type == "VERBRAUCHT"),
            "reorder": self.var_reorder.get()
        }

    def add_filament(self):
        data = self.get_input_data()
        if not data: return
        
        if data['id'] is not None:
            if any(i['id'] == data['id'] for i in self.inventory):
                messagebox.showerror("Fehler", f"Die ID {data['id']} existiert bereits!")
                return
        else:
            new_id = 1
            if self.inventory: new_id = max(int(i['id']) for i in self.inventory) + 1
            data['id'] = new_id

        self.inventory.append(data)
        self.save_data()
        self.refresh_table()
        self.clear_inputs()

    def update_filament(self):
        selected = self.tree.selection()
        if not selected: return
        old_id = int(selected[0])
        idx = next((i for i, item in enumerate(self.inventory) if item['id'] == old_id), None)
        if idx is not None:
            data = self.get_input_data()
            if not data: return
            
            new_id = data['id']
            if new_id is None:
                new_id = old_id 
                
            if new_id != old_id and any(i['id'] == new_id for i in self.inventory):
                messagebox.showerror("Fehler", f"Die ID {new_id} existiert bereits!")
                return
                
            data['id'] = new_id
            self.inventory[idx] = data
            self.save_data()
            self.refresh_table()
            self.tree.selection_set(str(new_id))

    def delete_filament(self):
        selected = self.tree.selection()
        if not selected: return
        if not messagebox.askyesno("Löschen", "Wirklich löschen?"): return
        fil_id = int(selected[0])
        self.inventory = [i for i in self.inventory if i['id'] != fil_id]
        self.save_data()
        self.refresh_table()
        self.clear_inputs()

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        fil_id = int(selected[0])
        item = next((i for i in self.inventory if i['id'] == fil_id), None)
        if not item: return

        self.entry_id.delete(0, tk.END)
        self.entry_id.insert(0, str(item['id']))
        self.entry_brand.delete(0, tk.END)
        self.entry_brand.insert(0, item['brand'])
        self.combo_material.set(item.get('material', 'PLA'))
        self.entry_color.delete(0, tk.END)
        self.entry_color.insert(0, item['color'])
        self.update_color_preview()
        self.combo_subtype.set(item.get('subtype', 'Standard'))
        
        loc_val = item['type']
        if loc_val not in self.combo_type['values']:
            vals = list(self.combo_type['values'])
            vals.append(loc_val)
            self.combo_type['values'] = vals
        self.combo_type.set(loc_val)
        
        self.update_slot_dropdown() 
        self.combo_loc_id.set(item.get('loc_id', ''))
        self.entry_flow.delete(0, tk.END)
        self.entry_flow.insert(0, str(item.get('flow', '')))
        self.entry_pa.delete(0, tk.END)
        self.entry_pa.insert(0, str(item.get('pa', '')))
        self.var_reorder.set(item.get('reorder', False))
        
        spool_id = item.get('spool_id', -1)
        found_val = "-"
        for val in self.combo_spool['values']:
            if val.startswith(f"{spool_id} -"):
                found_val = val
                break
        self.combo_spool.set(found_val)
        
        gross_val = item.get('weight_gross', 0)
        self.entry_gross.delete(0, tk.END)
        if float(gross_val) > 0:
            if float(gross_val).is_integer():
                self.entry_gross.insert(0, str(int(gross_val)))
            else:
                self.entry_gross.insert(0, str(gross_val))
                
        self.update_net_weight_display()

    def clear_inputs(self):
        self.entry_id.delete(0, tk.END)
        self.entry_brand.delete(0, tk.END)
        self.entry_color.delete(0, tk.END)
        self.combo_loc_id.set("")
        self.entry_flow.delete(0, tk.END) 
        self.entry_pa.delete(0, tk.END)
        self.combo_material.current(0)
        self.combo_subtype.current(0) 
        self.combo_type.current(0)
        self.combo_spool.current(0)
        self.entry_gross.delete(0, tk.END)
        self.update_net_weight_display()
        self.update_slot_dropdown()
        self.var_reorder.set(False)
        self.lbl_color_preview.config(bg="#FFFFFF") 
        self.tree.selection_remove(self.tree.selection())

    def on_quick_scan(self, event=None):
        scan_text = self.entry_scan.get().strip()
        if not scan_text: return
        try:
            clean_id = scan_text.upper().replace("FIL_", "")
            target_id = int(clean_id)
            if self.tree.exists(str(target_id)):
                self.tree.selection_set(str(target_id))
                self.tree.see(str(target_id))
                self.on_select(None)
                self.entry_scan.delete(0, tk.END)
            else: messagebox.showerror("Nicht gefunden", f"ID {target_id} existiert nicht.")
        except ValueError: messagebox.showerror("Fehler", "Ungültige ID.")

    def show_qr_code(self):
        selected = self.tree.selection()
        if not selected: 
            messagebox.showwarning("Info", "Bitte erst ein Filament auswählen.")
            return
        fil_id = int(selected[0])
        item = next((i for i in self.inventory if i['id'] == fil_id), None)
        qr_win = tk.Toplevel(self.root)
        qr_win.title(f"QR Code: {item['brand']}")
        qr_win.geometry("300x350")
        qr_win.configure(bg=self.root.cget('bg')) 
        qr_content = f"{fil_id}" 
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        tk_img = ImageTk.PhotoImage(img_qr)
        lbl = tk.Label(qr_win, image=tk_img, bg=self.root.cget('bg'))
        lbl.image = tk_img 
        lbl.pack(pady=10)
        ttk.Label(qr_win, text=f"ID: {fil_id}\n{item['brand']} {item['color']}", font=FONT_BOLD).pack()

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(self.inventory, f, indent=4)
        except Exception as e:
            messagebox.showerror("Speicherfehler", f"Konnte inventory.json nicht speichern.\n{e}")

if __name__ == "__main__":
    try: windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk()
    app = FilamentApp(root)
    root.mainloop()