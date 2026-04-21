import json
import os
import re
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

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

import re

def get_colors_from_text(text):
    if not text:
        return ["#FFFFFF"]

    # 🌍 STUFE 1: Echte, kräftige Farben (Werden immer zuerst priorisiert!)
    color_map = {
        # Schwarz, Grau & Silber
        "black": "#000000", "schwarz": "#000000", "grey": "#808080", "gray": "#808080", 
        "grau": "#808080", "silver": "#C0C0C0", "silber": "#C0C0C0", "anthrazit": "#333333",
        "dark": "#222222", "dunkel": "#222222", "ash": "#B2BEB5", "asche": "#B2BEB5",
        "graphit": "#41424C", "graphite": "#41424C", "slate": "#708090", "schiefer": "#708090",
        
        # Weiß, Natur & Beige
        "white": "#FFFFFF", "weiß": "#FFFFFF", "weiss": "#FFFFFF", "natural": "#F5F5DC", 
        "natur": "#F5F5DC", "beige": "#F5F5DC", "ivory": "#FFFFF0", "elfenbein": "#FFFFF0",
        "cream": "#FFFDD0", "creme": "#FFFDD0", "bone": "#E3DAC9", "knochen": "#E3DAC9",
        "sand": "#C2B280", "pearl": "#EAE0C8", "perle": "#EAE0C8",
        
        # Rot, Rosa & Pink
        "red": "#FF0000", "rot": "#FF0000", "pink": "#FFC0CB", "rosa": "#FFC0CB", "rose": "#FFC0CB",
        "magenta": "#FF00FF", "maroon": "#800000", "weinrot": "#800000", "bordeaux": "#800000",
        "crimson": "#DC143C", "karmesin": "#DC143C", "ruby": "#E0115F", "rubin": "#E0115F",
        "salmon": "#FA8072", "lachs": "#FA8072", "coral": "#FF7F50", "koralle": "#FF7F50",
        "peach": "#FFE5B4", "pfirsich": "#FFE5B4", "plum": "#8E4585", "pflaume": "#8E4585",
        
        # Gelb, Orange & Braun
        "yellow": "#FFFF00", "gelb": "#FFFF00", "orange": "#FFA500", "gold": "#FFD700",
        "terracotta": "#E2725B", "terrakotta": "#E2725B", "mustard": "#FFDB58", "senf": "#FFDB58",
        "lemon": "#FFF700", "zitrone": "#FFF700", "brown": "#A52A2A", "braun": "#A52A2A", 
        "copper": "#B87333", "kupfer": "#B87333", "bronze": "#CD7F32", "chocolate": "#7B3F00", 
        "schoko": "#7B3F00", "wood": "#8B5A2B", "holz": "#8B5A2B", "caramel": "#FFD59A", 
        "karamell": "#FFD59A", "amber": "#FFBF00", "bernstein": "#FFBF00", "rust": "#B7410E", 
        "rost": "#B7410E",
        
        # Blau & Türkis
        "blue": "#0000FF", "blau": "#0000FF", "navy": "#000080", "marine": "#000080",
        "cyan": "#00FFFF", "turquoise": "#40E0D0", "türkis": "#40E0D0", "tuerkis": "#40E0D0", 
        "teal": "#008080", "sky": "#87CEEB", "himmel": "#87CEEB", "azure": "#007FFF", 
        "azur": "#007FFF", "sapphire": "#0F52BA", "saphir": "#0F52BA", "cobalt": "#0047AB", 
        "kobalt": "#0047AB",
        
        # Grün
        "green": "#008000", "grün": "#008000", "gruen": "#008000", "mint": "#98FF98", 
        "minze": "#98FF98", "olive": "#808000", "oliv": "#808000", "lime": "#00FF00", 
        "limette": "#00FF00", "forest": "#228B22", "wald": "#228B22", "jade": "#00A86B", 
        "emerald": "#50C878", "smaragd": "#50C878", "neon": "#39FF14",
        
        # Lila
        "purple": "#800080", "lila": "#800080", "violet": "#EE82EE", "violett": "#EE82EE",
        "lavender": "#E6E6FA", "lavendel": "#E6E6FA", "lilac": "#C8A2C8", "flieder": "#C8A2C8",
        "amethyst": "#9966CC", "aubergine": "#3D0C02",
        
        # Spezial (Kräftige Farbschemas)
        "rainbow": "#FF0000", "regenbogen": "#FF0000"
    }
    
    # 🌫️ STUFE 2: Fallback-Farben (z.B. "Clear", "Translucent"). 
    # Werden NUR benutzt, wenn im Text KEINE echte Farbe gefunden wurde.
    # So gewinnt bei "Translucent Türkis" das Türkis und nicht das Grau!
    fallback_map = {
        "clear": "#E0E0E0", "klar": "#E0E0E0", "transparent": "#E0E0E0", "translucent": "#E0E0E0", 
        "glow": "#CCFFCC", "leucht": "#CCFFCC", "glass": "#E0E0E0", "glas": "#E0E0E0",
        "milky": "#F8F8FF", "milchig": "#F8F8FF", "frost": "#E0E0E0", "eis": "#E0E0E0",
        "marble": "#EAEAEA", "marmor": "#EAEAEA", "silk": "#F5F5F5", "seide": "#F5F5F5"
    }

    result_colors = []
    
    # Text am Schrägstrich trennen (für Dual-/Tri-Color)
    for part in text.split('/'):
        part = part.strip()
        if not part:
            continue
        
        # Check 1: Hat dieser Teil einen Hex-Code in sich?
        hex_match = re.search(r'#[0-9a-fA-F]{6}', part)
        if hex_match:
            result_colors.append(hex_match.group(0).upper())
            continue
            
        part_lower = part.lower()
        found = False
        
        # Check 2: Suche in den ECHTEN Farben zuerst! (sortiert nach Länge, damit "weinrot" vor "rot" greift)
        for name in sorted(color_map.keys(), key=len, reverse=True):
            if name in part_lower:
                result_colors.append(color_map[name])
                found = True
                break
                
        # Check 3: Wenn keine echte Farbe da ist, checken wir die Modifikatoren (Translucent, Clear...)
        if not found:
            for name in sorted(fallback_map.keys(), key=len, reverse=True):
                if name in part_lower:
                    result_colors.append(fallback_map[name])
                    found = True
                    break
        
        # Check 4: Ultimativer Fallback: Grau (Wenn absolut nichts passt)
        if not found:
            result_colors.append("#CCCCCC") 
            
    return result_colors if result_colors else ["#FFFFFF"]

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

# --- NEUE UI-KOMPONENTEN FÜR KLAPPMENÜS (ACCORDIONS) ---
class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # --- NEU: Kugelsicheres Ermitteln der Hintergrundfarbe ---
        try:
            bg_color = container.cget('bg')
        except tk.TclError:
            # Falls es ein modernes ttk-Widget ist, nimm die Farbe vom Hauptfenster
            bg_color = container.winfo_toplevel().cget('bg')
            
        # Canvas für das Scroll-Verhalten
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=bg_color)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        # Passt die Breite des inneren Frames dynamisch ans Fenster an
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            # Prüfen, ob das Element überhaupt noch existiert, bevor wir scrollen!
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass

class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, title="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.show = tk.BooleanVar(value=False)
        
        self.frm_header = ttk.Frame(self)
        self.frm_header.pack(fill="x", pady=(5,0))
        
        # Der Toggle-Button
        self.btn_toggle = ttk.Checkbutton(
            self.frm_header, text=f"▶  {title}", 
            command=self.toggle, variable=self.show, style="Toolbutton"
        )
        self.btn_toggle.pack(fill="x", expand=True, ipady=5)
        
        # Container für den Inhalt
        self.content = ttk.Frame(self, padding=15)
        
    def toggle(self):
        if self.show.get():
            self.btn_toggle.config(text=self.btn_toggle.cget("text").replace("▶", "▼"))
            self.content.pack(fill="both", expand=True)
        else:
            self.btn_toggle.config(text=self.btn_toggle.cget("text").replace("▼", "▶"))
            self.content.pack_forget()
