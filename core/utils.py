import json
import os
import re
import tkinter as tk
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
