# core/constants.py

APP_VERSION = "2.2.0"
GITHUB_REPO = "SirMetalizer/VibeSpool"

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
    "printers": [],
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

# Premium Apple Look styling values
COLOR_ACCENT = "#007AFF"  # Apple Blue
COLOR_DELETE = "#FF3B30"  # Apple Red
COLOR_SUCCESS = "#34C759" # Apple Green

THEMES = {
    "light": {
        "bg": "#F2F2F7",          # Apple light gray system background
        "fg": "#000000",          # Black text
        "entry_bg": "#FFFFFF",    # Pure white card/input background
        "entry_fg": "#000000",    # Black input text
        "tree_bg": "#FFFFFF",     # Pure white treeview background
        "tree_fg": "#000000",     # Black treeview text
        "head_bg": "#E5E5EA",     # System Gray 6 header background
        "head_fg": "#1C1C1E",     # Secondary header text
        "lbl_frame": "#3C3C43"    # Muted title frame text
    },
    "dark": {
        "bg": "#1C1C1E",          # Apple dark gray system background
        "fg": "#FFFFFF",          # White text
        "entry_bg": "#2C2C2E",    # Apple system gray 4 background
        "entry_fg": "#FFFFFF",    # White input text
        "tree_bg": "#2C2C2E",     # Apple system gray 4 background
        "tree_fg": "#FFFFFF",     # White treeview text
        "head_bg": "#3A3A3C",     # System Gray 3 header background
        "head_fg": "#FFFFFF",     # White header text
        "lbl_frame": "#AEAEB2"    # Muted title frame text
    }
}

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
