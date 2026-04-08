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
from core.spool_presets import SPOOL_PRESETS
from core.colors import get_color_name_from_hex

def fetch_last_print_usage(url, key): 
    return None
def fetch_recent_jobs(url, key): 
    return []

# --- MOBILE COMPANION (WEBSERVER) ---
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except: return '127.0.0.1'

MOBILE_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>VibeSpool Scanner</title>
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
    <style>
        body { background-color: #2b2b2b; color: white; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { font-size: 24px; margin-bottom: 20px; color: #0078d7; }
        .btn-scan { display: inline-block; background-color: #0078d7; color: white; font-size: 20px; font-weight: bold; padding: 15px 30px; border-radius: 12px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .btn-scan:active { background-color: #005a9e; }
        input[type="file"] { display: none; }
        #status { margin-top: 20px; padding: 15px; border-radius: 8px; background: #3c3f41; font-weight: bold; }
        .success { background: #28a745 !important; } .error { background: #d9534f !important; }
        
        /* Das neue Dashboard */
        #dashboard { display: none; margin-top: 20px; background: #3c3f41; padding: 15px; border-radius: 10px; text-align: left;}
        #dash-title { color: #0078d7; font-size: 18px; margin-top: 0; margin-bottom: 5px; font-weight: bold;}
        #dash-net { font-size: 14px; color: #bbb; margin-bottom: 15px; }
        .control-group { margin-bottom: 15px; display: flex; gap: 10px; }
        .control-group input, .control-group select { flex-grow: 1; padding: 12px; font-size: 16px; border-radius: 5px; border: 1px solid #555; background: #2b2b2b; color: white; }
        .btn-action { padding: 12px 15px; font-size: 16px; font-weight: bold; border: none; border-radius: 5px; color: white; cursor: pointer; }
        .btn-red { background: #d9534f; } .btn-green { background: #28a745; }
        #btn-reset { width: 100%; padding: 15px; background: #555; color: white; font-size: 18px; font-weight: bold; border: none; border-radius: 8px; margin-top: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <h1 id="main-title">📱 VibeSpool Scanner</h1>
    
    <label class="btn-scan" id="scan-trigger">
        📷 Etikett scannen
        <input type="file" id="qr-input-file" accept="image/*" capture="environment">
    </label>
    
    <div id="status">Tippe auf den Button und mach ein Foto!</div>

    <div id="dashboard">
        <h3 id="dash-title">Spule</h3>
        <div id="dash-net">Rest: 0g</div>
        <input type="hidden" id="current-id">

        <div class="control-group">
            <input type="number" id="val-usage" placeholder="Verbrauch (z.B. 140)">
            <button class="btn-action btn-red" onclick="sendAction('usage')">Abziehen</button>
        </div>

        <div class="control-group">
            <select id="val-loc"></select>
            <button class="btn-action btn-green" onclick="sendAction('move')">Umbuchen</button>
        </div>

        <button id="btn-reset" onclick="resetUI()">Fertig / Nächste Spule</button>
    </div>

    <script>
        const fileInput = document.getElementById('qr-input-file');
        const statusDiv = document.getElementById("status");

        function resetUI() {
            document.getElementById('dashboard').style.display = 'none';
            document.getElementById('scan-trigger').style.display = 'inline-block';
            document.getElementById('main-title').style.display = 'block';
            statusDiv.innerText = "Bereit. Mach ein neues Foto!";
            statusDiv.className = "";
        }

        function sendAction(actionType) {
            let id = document.getElementById('current-id').value;
            let val = "";
            
            if (actionType === 'usage') {
                val = document.getElementById('val-usage').value;
                if (!val) return alert("Bitte Gewicht eingeben!");
            } else if (actionType === 'move') {
                val = document.getElementById('val-loc').value;
                if (!val) return;
            }

            fetch(`/action?id=${id}&action=${actionType}&val=${encodeURIComponent(val)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        alert("✅ Erfolgreich gespeichert!");
                        if (actionType === 'usage') document.getElementById('val-usage').value = '';
                    } else {
                        // Zeigt die Warnung an, falls der Platz belegt ist!
                        alert("⚠️ Aktion abgelehnt:\\n" + data.msg);
                    }
                });
        }

        fileInput.addEventListener('change', e => {
            if (e.target.files.length == 0) return;
            const file = e.target.files[0];
            statusDiv.innerText = "Analysiere..."; statusDiv.className = "";

            const reader = new FileReader();
            reader.onload = function(event) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    let w = img.width, h = img.height;
                    if (w > h && w > 800) { h *= 800/w; w = 800; } 
                    else if (h > 800) { w *= 800/h; h = 800; }
                    canvas.width = w; canvas.height = h;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, w, h);
                    const imageData = ctx.getImageData(0, 0, w, h);

                    const code = jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: "dontInvert" });

                    if (code) {
                        statusDiv.innerText = "Gefunden! Lade Daten...";
                        statusDiv.className = "success";
                        
                        // NEU: Daten vom PC abrufen und Dashboard aufbauen!
                        fetch('/scan?code=' + encodeURIComponent(code.data))
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'ok') {
                                    document.getElementById('scan-trigger').style.display = 'none';
                                    document.getElementById('main-title').style.display = 'none';
                                    statusDiv.style.display = 'none';
                                    
                                    document.getElementById('dashboard').style.display = 'block';
                                    document.getElementById('dash-title').innerText = data.name;
                                    document.getElementById('dash-net').innerText = "Aktueller Rest: " + data.net + " g";
                                    document.getElementById('current-id').value = data.id;
                                    
                                    let select = document.getElementById('val-loc');
                                    select.innerHTML = '<option value="">-- Neuen Ort wählen --</option>';
                                    data.locs.forEach(l => {
                                        select.innerHTML += `<option value="${l.val}">${l.label}</option>`;
                                    });
                                } else {
                                    statusDiv.innerText = "Fehler: " + data.msg;
                                    statusDiv.className = "error";
                                }
                            });
                    } else {
                        statusDiv.innerText = "Kein QR-Code erkannt. Bitte nochmal versuchen!";
                        statusDiv.className = "error";
                    }
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
            fileInput.value = '';
        });
    </script>
</body>
</html>
"""

class MobileScannerHandler(http.server.SimpleHTTPRequestHandler):
    # Unterdrückt die nervigen Konsolen-Logs im Hintergrund
    def log_message(self, format, *args):
        pass 

    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            import json
            parsed_path = urlparse(self.path)
            
            # 1. Ignoriere automatische Browser-Anfragen nach Icons sofort!
            if parsed_path.path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
                return
            
            if parsed_path.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(MOBILE_HTML.encode('utf-8'))
                
            elif parsed_path.path == '/scan':
                query = parse_qs(parsed_path.query)
                code = query.get('code', [''])[0]
                app_inst = getattr(self.server, 'app_instance', None)
                
                response_data = {"status": "error", "msg": "Spule nicht in der Datenbank."}
                
                if code and app_inst:
                    import re
                    match = re.search(r'(?:ID:\s*|FIL_)?(\d+)', code, re.IGNORECASE)
                    spool_id = int(match.group(1)) if match else None
                    
                    if spool_id:
                        item = next((i for i in app_inst.inventory if i.get('id') == spool_id), None)
                        if item:
                            app_inst.root.after(0, lambda: app_inst.process_mobile_scan(code))
                            
                            locs = [
                                {"label": "📦 Ins LAGER", "val": "LAGER|-"}, 
                                {"label": "🚮 Als LEER markieren", "val": "VERBRAUCHT|-"}
                            ]
                            
                            from core.logic import parse_shelves_string, calculate_net_weight
                            parsed_shelves = parse_shelves_string(app_inst.settings.get("shelves", "REGAL|4|8"))
                            lbl_r = app_inst.settings.get("label_row", "Fach")
                            lbl_c = app_inst.settings.get("label_col", "Slot")
                            all_names = app_inst.settings.get("shelf_names_v2", {})
                            is_double = app_inst.settings.get("double_depth", False)
                            
                            for sh in parsed_shelves:
                                name = sh['name']
                                s_names = all_names.get(name, {})
                                for r in range(1, sh['rows'] + 1):
                                    row_n = s_names.get(str(r), f"{lbl_r} {r}")
                                    for c in range(1, sh['cols'] + 1):
                                        if is_double:
                                            locs.append({"label": f"{name} {row_n} - {lbl_c} {c} (V)", "val": f"{name}|{row_n} - {lbl_c} {c} (V)"})
                                            locs.append({"label": f"{name} {row_n} - {lbl_c} {c} (H)", "val": f"{name}|{row_n} - {lbl_c} {c} (H)"})
                                        else:
                                            locs.append({"label": f"{name} {row_n} - {lbl_c} {c}", "val": f"{name}|{row_n} - {lbl_c} {c}"})
                                            
                            for a in range(1, app_inst.settings.get("num_ams", 1) + 1):
                                for s in range(1, 5):
                                    locs.append({"label": f"AMS {a} Slot {s}", "val": f"AMS {a}|{s}"})
                                    
                            net_w = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), app_inst.spools)
                            
                            response_data = {
                                "status": "ok",
                                "id": spool_id,
                                "name": f"{item.get('brand','')} {item.get('material','')} {item.get('color','')}",
                                "net": int(net_w),
                                "locs": locs
                            }

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            elif parsed_path.path == '/action':
                query = parse_qs(parsed_path.query)
                spool_id = query.get('id', [''])[0]
                action = query.get('action', [''])[0]
                val = query.get('val', [''])[0]
                
                app_inst = getattr(self.server, 'app_instance', None)
                response_data = {"status": "error", "msg": "Unbekannter Fehler"}
                
                if app_inst and spool_id and action:
                    spool_id_int = int(spool_id)
                    if action == "move" and "|" in val:
                        target_type, target_loc = val.split("|", 1)
                        col = app_inst.check_location_collision(target_type, target_loc, ignore_id=spool_id_int)
                        
                        if col:
                            response_data = {
                                "status": "error", 
                                "msg": f"Der Platz ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}"
                            }
                        else:
                            app_inst.root.after(0, lambda: app_inst.process_mobile_action(spool_id_int, action, val))
                            response_data = {"status": "ok"}
                    else:
                        app_inst.root.after(0, lambda: app_inst.process_mobile_action(spool_id_int, action, val))
                        response_data = {"status": "ok"}
                        
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
        except Exception as e:
            # --- DIE LEBENSRETTUNG ---
            # Statt sang- und klanglos abzustürzen, fangen wir JEDEN Fehler ab!
            print(f"Webserver Fehler abgefangen: {e}")
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"VibeSpool Server Fehler: {e}".encode('utf-8'))
            except:
                pass

def start_mobile_server(app_inst):
    port = 8289  # Neuer, freier Port!
    handler = MobileScannerHandler
    try:
        import http.server
        # Erlaubt den sofortigen Neustart des Servers ohne Blockade
        http.server.ThreadingHTTPServer.allow_reuse_address = True
        
        # Ein Threading-Server stürzt nicht ab, wenn das Handy etwas Falsches funkt
        httpd = http.server.ThreadingHTTPServer(("", port), handler)
        setattr(httpd, 'app_instance', app_inst) 
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    except Exception as e:
        print(f"Webserver konnte nicht starten: {e}")


# --- KONFIGURATION ---
APP_VERSION = "1.9.8"
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
                if s['id'] == int(sel[0]): 
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
        self.title("VibeSpool Einstellungen"); self.geometry("950x500"); self.configure(bg=parent.cget('bg')); center_window(self, parent)
        self.transient(parent); self.grab_set()
        
        # FOOTER
        btn_frm = ttk.Frame(self, padding=10); btn_frm.pack(fill="x", side="bottom")
        ttk.Button(btn_frm, text="Abbrechen", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frm, text="Änderungen Speichern", style="Accent.TButton", command=self.do_save).pack(side="right", padx=5)

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
            
        btn_frm_lager = ttk.Frame(tab_lager)
        btn_frm_lager.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_frm_lager, text="🔧 Regal-Konfigurator", command=run_planner).pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        if getattr(self, 'app', None):
            def open_shelf_editor():
                if self.app: 
                    # NEU: Wir prüfen, WELCHES Regal in der Liste markiert ist!
                    sel = self.shelf_list.curselection()
                    if not sel:
                        messagebox.showinfo("Info", "Bitte wähle zuerst ein Regal aus der Liste darüber aus!", parent=self)
                        return
                    
                    selected_str = self.shelf_list.get(sel[0])
                    # Extrahiert den Namen (z.B. "📦 REGAL (4x8)" -> "REGAL")
                    shelf_name = selected_str.replace("📦 ", "").split(" (")[0]
                    
                    current_lbl_row = self.ent_row.get().strip() or "Fach"
                    self.app.edit_shelf_names(self, self.var_shelves.get(), current_lbl_row, shelf_name)
                    
            ttk.Button(btn_frm_lager, text="🏷️ Fächer benennen", command=open_shelf_editor).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # --- NEU: Zusatz-Orte sind jetzt hier, wo sie hingehören! ---
        ttk.Separator(tab_lager, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(tab_lager, text="Zusatz-Orte (kommagetrennt, z.B. Trockenbox, Verliehen):", font=FONT_BOLD).pack(anchor="w", pady=(0, 5))
        self.ent_custom = ttk.Entry(tab_lager)
        self.ent_custom.insert(0, self.settings.get("custom_locs", "Filamenttrockner"))
        self.ent_custom.pack(fill="x", pady=2)
        self.var_double = tk.BooleanVar(value=self.settings.get("double_depth", False))
        ttk.Checkbutton(tab_lager, text="Doppeltiefe Regale (2 Rollen pro Slot)", variable=self.var_double).pack(anchor="w", pady=(10, 5))
        
        ttk.Separator(tab_lager, orient="horizontal").pack(fill="x", pady=10)
        self.var_logistics = tk.BooleanVar(value=self.settings.get("logistics_order", False))
        ttk.Checkbutton(tab_lager, text="Logistik-Modus (unten = Reihe 1)", variable=self.var_logistics).pack(anchor="w", pady=5)
        
        f_names = ttk.Frame(tab_lager); f_names.pack(fill="x", pady=5)
        ttk.Label(f_names, text="Reihen-Name:").grid(row=0, column=0, sticky="w")
        self.ent_row = ttk.Entry(f_names, width=15); self.ent_row.insert(0, self.settings.get("label_row", "Fach")); self.ent_row.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        ttk.Label(f_names, text="Spalten-Name:").grid(row=1, column=0, sticky="w")
        self.ent_col = ttk.Entry(f_names, width=15); self.ent_col.insert(0, self.settings.get("label_col", "Slot")); self.ent_col.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        
        ttk.Checkbutton(tab_lager, text="Doppeltiefe Regale (2 Rollen pro Slot)", variable=self.var_double).pack(anchor="w", pady=(10, 0))

        # TAB 3: DRUCKER
        tab_prn = ttk.Frame(self.nb, padding=15); self.nb.add(tab_prn, text="🤖 Drucker")
        
        # Moonraker Bereich
        ttk.Label(tab_prn, text="Klipper / Moonraker", font=FONT_BOLD).pack(anchor="w")
        self.var_moonraker = tk.BooleanVar(value=self.settings.get("use_moonraker", False))
        ttk.Checkbutton(tab_prn, text="Moonraker-Sync im Hauptfenster anzeigen", variable=self.var_moonraker).pack(anchor="w", pady=(5, 5))
        self.ent_prn_url = ttk.Entry(tab_prn); self.ent_prn_url.insert(0, self.settings.get("printer_url", "")); self.ent_prn_url.pack(fill="x", pady=2)
        
        ttk.Separator(tab_prn, orient="horizontal").pack(fill="x", pady=15)
        
        # NEU: Bambu Lab Bereich
        ttk.Separator(tab_prn, orient="horizontal").pack(fill="x", pady=15)
        
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

        # TAB 4: SYSTEM
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

        # Helper-Funktion baut uns 3 Listen-Manager (mit Spezial-Feature für Farben)
        self.list_vars = {}
        def create_list_manager(parent, title, key, default_list):
            frm = ttk.LabelFrame(parent, text=title, padding=5)
            frm.pack(side="left", fill="both", expand=True, padx=2)
            
            lb = tk.Listbox(frm, height=12, font=("Segoe UI", 9))
            lb.pack(fill="both", expand=True, pady=2)
            
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
                                    
                    # Auch im neuen V2-Benennungssystem die Namen patchen!
                    all_shelf_names = self.settings.get("shelf_names_v2", {})
                    for shelf_key, names_dict in all_shelf_names.items():
                        for k, v in names_dict.items():
                            if v.startswith(old_label_row + " "):
                                all_shelf_names[shelf_key][k] = v.replace(old_label_row + " ", new_label_row + " ", 1)
                    self.settings["shelf_names_v2"] = all_shelf_names

                # Nur speichern, wenn auch wirklich Spulen angefasst wurden
                if inventory_changed:
                    app_inst.data_manager.save_inventory(app_inst.inventory)

            # --- Normales Speichern der Einstellungen ---
            self.settings.update({
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
            
            # Tabelle sofort neu zeichnen
            if app_inst:
                app_inst.refresh_table() 
                
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
                    if is_double:
                        # Haupt-Container für die Spalte
                        slot_container = tk.Frame(row_frame, bg="#8B4513")
                        slot_container.pack(side="left", padx=2)
                        
                        # Zwei kleine "Stockwerke" erzwingen die Übereinander-Darstellung
                        frm_h = tk.Frame(slot_container, bg="#8B4513")
                        frm_h.pack(side="top", pady=(0, 1))
                        frm_v = tk.Frame(slot_container, bg="#8B4513")
                        frm_v.pack(side="top", pady=(1, 0))
                        
                        # Hinten (H) - Oben
                        slot_name_h = f"{row_label} - {lbl_c} {c} (H)"
                        self.draw_slot(frm_h, f"{c}H", self.shelf_data.get(f"{shelf['name']}_{slot_name_h}"), False, 65, 35, shelf['name'], slot_name_h)
                        
                        # Vorne (V) - Unten
                        slot_name_v = f"{row_label} - {lbl_c} {c} (V)"
                        self.draw_slot(frm_v, f"{c}V", self.shelf_data.get(f"{shelf['name']}_{slot_name_v}"), False, 65, 35, shelf['name'], slot_name_v)
                    else:
                        slot_name = f"{row_label} - {lbl_c} {c}"
                        self.draw_slot(row_frame, str(c), self.shelf_data.get(f"{shelf['name']}_{slot_name}"), False, 70, 70, shelf['name'], slot_name)
                    
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
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools)
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
        btn_frm = ttk.Frame(self)
        btn_frm.pack(fill="x", pady=10, padx=20)
        
        # Der neue Button ruft unsere Diagramm-Funktion in der Haupt-App auf
        ttk.Button(btn_frm, text="📈 Verbrauchs-Verlauf (7 Tage)", command=self.app.show_statistics_dialog, style="Accent.TButton").pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="left", expand=True, fill="x", padx=(5, 0))

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
class LabelCreatorDialog(tk.Toplevel):
    def __init__(self, parent, inventory):
        super().__init__(parent)
        self.inventory = [i for i in inventory if i.get('type') != 'VERBRAUCHT']
        self.title("🏷️ Label Creator")
        self.geometry("850x500")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)

        frm_left = ttk.Frame(self, padding=10)
        frm_left.pack(side="left", fill="y")
        
        ttk.Label(frm_left, text="Spule auswählen:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.listbox = tk.Listbox(frm_left, width=40, font=("Segoe UI", 10))
        self.listbox.pack(fill="both", expand=True)
        
        for i in self.inventory:
            self.listbox.insert(tk.END, f"[{i['id']}] {i.get('brand','')} {i.get('material','')} {i.get('color','')}")
            
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        frm_right = ttk.Frame(self, padding=10)
        frm_right.pack(side="right", fill="both", expand=True)
        
        ttk.Label(frm_right, text="Druck-Vorschau:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.lbl_preview = tk.Label(frm_right, bg="gray", relief="solid", borderwidth=1)
        self.lbl_preview.pack(pady=10, expand=True)
        
        btn_frm = ttk.Frame(frm_right)
        btn_frm.pack(fill="x", side="bottom", pady=10)
        
        ttk.Button(btn_frm, text="💾 Aktuelles Label als PNG", command=self.save_label).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frm, text="📑 ALLE als PDF exportieren", command=self.trigger_pdf_export, style="Accent.TButton").pack(side="right")
        
        self.current_img = None
        self.current_item = None
        
    def on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        self.current_item = self.inventory[sel[0]]
        self.generate_label(self.current_item)
        
    def generate_label(self, item):
        try:
            from PIL import ImageFont
            try:
                # Versucht Standard Windows-Fonts zu laden
                font_title = ImageFont.truetype("arialbd.ttf", 45)
                font_sub = ImageFont.truetype("arial.ttf", 35)
                font_small = ImageFont.truetype("arial.ttf", 25)
            except:
                # Fallback
                font_title = font_sub = font_small = ImageFont.load_default()
                
            # Wir erstellen ein hochauflösendes Label (2:1 Format, perfekt für Rollen-Etiketten)
            img = Image.new('RGB', (800, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # 1. QR Code generieren & einfügen
            from qrcode.image.pil import PilImage
            
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(f"ID:{item['id']}") 
            qr.make(fit=True)
            
            # FIX: Wir zwingen die Bibliothek, ein echtes PIL-Bild zu generieren
            qr_wrapper = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
            
            # get_image() holt das reine PIL-Objekt heraus, convert('RGB') macht es kompatibel
            qr_img = qr_wrapper.get_image().convert('RGB')
            qr_img = qr_img.resize((360, 360)) 
            img.paste(qr_img, (20, 20))
            
            # 2. Texte auf die rechte Seite schreiben
            brand = item.get('brand', 'Unbekannt')
            mat = item.get('material', 'PLA')
            color = item.get('color', 'Unbekannt')
            sub = item.get('subtype', 'Standard')
            temp_n = item.get('temp_n', '-')
            temp_b = item.get('temp_b', '-')
            
            draw.text((400, 30), f"{brand} {mat}", fill="black", font=font_title)
            draw.text((400, 100), f"{color}", fill="#333333", font=font_sub)
            draw.text((400, 150), f"{sub}", fill="#666666", font=font_sub)
            
            draw.text((400, 240), f"Nozzle: {temp_n} °C", fill="black", font=font_small)
            draw.text((400, 280), f"Bed: {temp_b} °C", fill="black", font=font_small)
            draw.text((400, 330), f"VibeSpool ID: {item['id']}", fill="black", font=font_title)
            
            # 3. Farb-Balken zur schnellen Erkennung
            cols = get_colors_from_text(color)
            hex_col = cols[0] if cols else "#FFFFFF"
            draw.rectangle([400, 370, 760, 390], fill=hex_col, outline="black")
            
            self.current_img = img
            
            # 4. Preview für die Anzeige verkleinern
            preview = img.resize((500, 250))
            self.photo = ImageTk.PhotoImage(preview)
            self.lbl_preview.config(image=self.photo)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Label konnte nicht generiert werden:\n{e}")

    def save_label(self):
        if not self.current_img or not self.current_item: return
        file_name = f"Label_{self.current_item['id']}_{self.current_item.get('brand', '')}_{self.current_item.get('material', '')}.png"
        fp = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Bild", "*.png")], initialfile=file_name)
        if fp:
            self.current_img.save(fp)
            messagebox.showinfo("Gespeichert", f"Das Etikett wurde erfolgreich gespeichert!\nDu kannst es nun ausdrucken.")
    def trigger_pdf_export(self):
        # Ruft den neuen Smart Export Dialog auf
        PdfExportDialog(self, self.inventory, getattr(self, 'spools', []))


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
        self.menu_opts.add_command(label="⚙ System-Optionen & Smart Home", command=lambda: self.open_settings(2))
        self.menu_opts.add_command(label="📋 Listen-Verwaltung", command=lambda: self.open_settings(3))
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="🔄 Update-Check", command=self.manual_update_check)
        self.btn_opts["menu"] = self.menu_opts
        self.btn_opts.pack(side="right", padx=5)
        
        ttk.Button(top_bar, text="💾 Backup", command=lambda: BackupDialog(self.root, self.data_manager, self)).pack(side="right", padx=5); ttk.Button(top_bar, text="🛒 Einkaufsliste", command=lambda: ShoppingListDialog(self.root, self.inventory, self)).pack(side="right", padx=5); 
        ttk.Button(top_bar, text="📥 CSV Import", command=self.import_csv).pack(side="right", padx=5)
        ttk.Button(top_bar, text="☕ Spenden", command=self.open_paypal).pack(side="right", padx=5); self.btn_theme = ttk.Button(top_bar, text="...", command=self.toggle_theme); self.btn_theme.pack(side="right", padx=5); self.update_theme_button_text()
        
        # --- SIDEBAR BUTTONS ---
        self.nav_btns = []
        def add_nav_btn(text, cmd, icon_txt=None):
            btn = tk.Button(self.nav_sidebar, text=f"{icon_txt}\n{text}" if icon_txt else text, command=cmd, 
                           font=("Segoe UI", 8), bd=0, pady=15, cursor="hand2")
            btn.pack(fill="x")
            self.nav_btns.append(btn)
            btn.bind("<Enter>", lambda e: self.on_nav_btn_hover(btn, True))
            btn.bind("<Leave>", lambda e: self.on_nav_btn_hover(btn, False))

        add_nav_btn("Regal", lambda: ShelfVisualizer(self.root, self.inventory, self.settings, self.spools, self), "📦")
        add_nav_btn("Spulen", lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown), "🧵")
        add_nav_btn("Label", lambda: LabelCreatorDialog(self.root, self.inventory), "🏷️")
        add_nav_btn("Finanzen", lambda: StatisticsDialog(self.root, self.inventory, self), "📊")
        add_nav_btn("Swap", self.quick_swap_dialog, "🔄")
        add_nav_btn("Flow", lambda: FlowCalculatorDialog(self.root, self.entry_flow), "🧪")
        if self.settings.get("use_bambu", False):
            add_nav_btn("AMS", self.run_ams_sync, "🤖")
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

        self.combo_spool = ttk.Combobox(tab_basis, state="readonly", font=FONT_MAIN)
        self.combo_spool.pack(fill="x", pady=2)
        
        # NEU: Smarter Event-Handler für die Spule
        self.last_selected_spool_id = -1
        self.combo_spool.bind("<<ComboboxSelected>>", self.on_spool_changed)
        
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
        
        ttk.Button(frm_slicer_btns, text="➖ Abziehen", command=self.deduct_slicer).pack(side="left", expand=True, fill="x", padx=(0, 2))
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
        ttk.Label(tab_erp, text="Link:").grid(row=3, column=0, sticky="w", pady=5); self.entry_link = ttk.Entry(tab_erp); self.entry_link.grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Separator(tab_erp, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(tab_erp, text="Nozzle Temp (°C):").grid(row=5, column=0, sticky="w", pady=5); self.entry_temp_n = ttk.Entry(tab_erp); self.entry_temp_n.grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab_erp, text="Bed Temp (°C):").grid(row=6, column=0, sticky="w", pady=5); self.entry_temp_b = ttk.Entry(tab_erp); self.entry_temp_b.grid(row=6, column=1, sticky="ew", pady=2)
        tab_erp.columnconfigure(1, weight=1)
       
        btn_frame = ttk.Frame(sidebar)
        btn_frame.pack(fill="x", pady=(15, 0))
        
        # --- 1. Hauptaktionen: Hinzufügen & Speichern (Nebeneinander) ---
        main_action_frame = ttk.Frame(btn_frame)
        main_action_frame.pack(fill="x", pady=3)
        ttk.Button(main_action_frame, text="Neu Hinzufügen", command=self.add_filament, style="Accent.TButton").pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(main_action_frame, text="Änderungen Speichern", command=self.update_filament).pack(side="left", fill="x", expand=True, padx=(2, 0))
        
        # --- 2. Quick-Swap (Prominent platziert) ---
        ttk.Button(btn_frame, text="🔄 Quick-Swap", command=self.quick_swap_dialog).pack(fill="x", pady=3)
        
        # --- 3. Workflow-Booster (Klonen & Ins Lager) ---
        aktion_frame = ttk.Frame(btn_frame)
        aktion_frame.pack(fill="x", pady=3)
        ttk.Button(aktion_frame, text="🐑 Klonen", command=self.clone_filament).pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(aktion_frame, text="📦 Ins Lager", command=self.send_to_storage).pack(side="left", fill="x", expand=True, padx=(2, 0))
        
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

        table_frame = ttk.Frame(main_frame); table_frame.pack(side="right", fill="both", expand=True)
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
        self.apply_theme()
        
        start_mobile_server(self)
        self.broadcast_mqtt()

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

    def show_update_prompt(self, latest, url):
        upd = tk.Toplevel(self.root); upd.title("VibeSpool Update"); upd.geometry("400x150"); upd.configure(bg=self.root.cget('bg')); upd.attributes('-topmost', True); center_window(upd, self.root)
        ttk.Label(upd, text=f"Version {latest} ist verfügbar!", font=("Segoe UI", 12, "bold")).pack(pady=15)
        btn_frm = ttk.Frame(upd); btn_frm.pack(pady=10)
        ttk.Button(btn_frm, text="Laden", command=lambda: [webbrowser.open(url), upd.destroy()]).pack(side="left", padx=5); ttk.Button(btn_frm, text="Später", command=upd.destroy).pack(side="left", padx=5)

    def on_closing(self): 
        try:
            self.settings["geometry"] = self.root.geometry()
            self.data_manager.save_settings(self.settings)
        except Exception: 
            pass
        self.root.quit()
        self.root.destroy()
        import sys
        sys.exit(0)
    
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
        try:
            used = float(self.entry_slicer.get().strip().replace(',', '.'))
            curr = float(self.var_gross.get().strip().replace(',', '.') or 0)
            if used > 0 and curr > 0:
                new_gross = max(0, curr - used)
                self.var_gross.set(f"{new_gross:g}")
                self.entry_slicer.delete(0, tk.END) # Leert das Eingabefeld nach Erfolg
                self.log_consumption(used)
        except ValueError:
            pass # Ignoriert Klicks, wenn Buchstaben drinstehen
    
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
            net = calculate_net_weight(gross_str, self.get_selected_spool_id(), self.spools); price_str = self.var_price.get().strip().replace(',', '.'); cap_str, val_str = self.var_capacity.get().strip(), ""
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
                            if is_double:
                                slots.append(f"{row_name} - {lbl_c} {cl} (H)")
                                slots.append(f"{row_name} - {lbl_c} {cl} (V)")
                            else:
                                slots.append(f"{row_name} - {lbl_c} {cl}")
                    new_values = slots
                    break

        # 1. Die neue Liste im Hintergrund zuweisen
        self.combo_loc_id['values'] = new_values
        
        # 2. FIX: Steht noch Blödsinn vom alten Lagerort im Feld? Dann automatisch korrigieren!
        current_val = self.combo_loc_id.get()
        if current_val not in new_values:
            self.combo_loc_id.set(new_values[0])

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
                    w = calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools)
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
        for i in self.data_manager.get_filtered_inventory(self.inventory, self.search_var.get(), filters):
            # NEU: Manueller Hersteller-Filter
            if self.filter_brand_var.get() != "Alle Hersteller" and i.get('brand') != self.filter_brand_var.get():
                continue
            loc_s = f"{i['type']} {i.get('loc_id', '')}".strip()
            stat = " | ".join(filter(None, ["VERBRAUCHT" if i['type'] == "VERBRAUCHT" else "", "KAUFEN" if i.get('reorder') else ""]))
            
            icon = create_color_icon(get_colors_from_text(i['color']))
            self.icon_cache.append(icon)
            
            net = calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools)
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
    def get_input_data(self):
        try:
            cap = int(self.var_capacity.get().strip() or 1000)
            spool_id = self.get_selected_spool_id()
            
            gross_str = self.var_gross.get().strip().replace(',', '.')
            
            # FIX: Wir prüfen NUR noch, ob das Feld wirklich komplett leer ist.
            # Eine eingetippte '0' ist ab sofort eine absolut gültige Eingabe!
            if not gross_str:
                sp = next((s for s in self.spools if s['id'] == spool_id), None)
                gross_val = float(cap + (sp['weight'] if sp else 0))
                self.var_gross.set(f"{gross_val:g}") # Update im UI sichtbar machen
            else:
                gross_val = float(gross_str)
                # Optionaler Schutz: Falls jemand versehentlich "-5" tippt, machen wir 0 daraus
                if gross_val < 0:
                    gross_val = 0.0

            return {"id": int(self.entry_id.get().strip()) if self.entry_id.get().strip() else None, "rfid": self.entry_rfid.get().strip(), "brand": self.entry_brand.get().strip(), "material": self.combo_material.get().strip(), "color": self.combo_color.get().strip(), "subtype": self.combo_subtype.get().strip(), "type": self.combo_type.get(), "loc_id": self.combo_loc_id.get().strip(), "flow": self.entry_flow.get().strip(), "pa": self.entry_pa.get().strip(), "spool_id": spool_id, "weight_gross": gross_val, "capacity": cap, "is_refill": self.var_is_refill.get(), "is_empty": self.combo_type.get() == "VERBRAUCHT", "reorder": self.var_reorder.get(), "supplier": self.entry_supplier.get().strip(), "sku": self.entry_sku.get().strip(), "price": self.var_price.get().strip(), "link": self.entry_link.get().strip(), "temp_n": self.entry_temp_n.get().strip(), "temp_b": self.entry_temp_b.get().strip()}
        except Exception as e: 
            messagebox.showwarning(
                "Eingabe-Fehler", 
                f"Bitte prüfe deine Eingaben!\nHast du vielleicht Text in ein Zahlenfeld getippt?\n\nFehler-Details:\n{e}"
            )
            return None

    def check_location_collision(self, loc_type, loc_id, ignore_id=None):
        # Unendliche Lagerorte ignorieren wir (da passen beliebig viele Spulen rein)
        if loc_type in ["LAGER", "VERBRAUCHT", ""]: return None
        # Wenn kein genauer Slot gewählt wurde ("-"), gibt es auch keine Kollision
        if loc_id in ["-", ""]: return None
        
        for i in self.inventory:
            # Die eigene Spule beim Bearbeiten ignorieren (sonst blockiert sie sich selbst)
            if i.get('id') == ignore_id: continue
            if i.get('type') == "VERBRAUCHT": continue
            
            # Treffer! Genau dieser Ort + Slot ist schon belegt.
            if i.get('type') == loc_type and str(i.get('loc_id')) == str(loc_id):
                return i # Wir geben die störende Spule zurück
        return None

    def add_filament(self):
        d = self.get_input_data()
        if not d: return
        
        if d['id'] is not None:
            if any(i['id'] == d['id'] for i in self.inventory):
                messagebox.showerror("Halt Stop!", f"Die ID {d['id']} existiert bereits in deinem Lager!\nBitte wähle eine andere ID oder lass das Feld leer.")
                return
        else:
            d['id'] = max([int(i['id']) for i in self.inventory], default=0) + 1
            
        # NEU: Kollisionsprüfung
        col = self.check_location_collision(d['type'], d['loc_id'])
        if col:
            msg = f"Der Platz {d['type']} {d['loc_id']} ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}\n\nTrotzdem dort speichern (führt zu doppelter Belegung)?"
            if not messagebox.askyesno("⚠️ Platz belegt", msg):
                return
                
        self.inventory.append(d)
        self.data_manager.save_inventory(self.inventory); self.broadcast_mqtt()
        self.refresh_table()
        self.clear_inputs()

    def update_filament(self):
        sel = self.tree.selection()
        if not sel: return
        d = self.get_input_data()
        if not d: return
        
        old_id = int(sel[0])
        new_id = d['id'] or old_id
        
        if new_id != old_id:
            if any(i['id'] == new_id for i in self.inventory):
                messagebox.showerror("Halt Stop!", f"Du kannst diese Spule nicht auf ID {new_id} ändern, da diese ID bereits einer anderen Spule gehört!")
                return
                
        # NEU: Kollisionsprüfung (mit ignore_id, damit sie sich nicht selbst blockiert!)
        col = self.check_location_collision(d['type'], d['loc_id'], ignore_id=old_id)
        if col:
            msg = f"Der Ziel-Platz {d['type']} {d['loc_id']} ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}\n\nTrotzdem dorthin verschieben?"
            if not messagebox.askyesno("⚠️ Platz belegt", msg):
                return
                
        d['id'] = new_id

        idx = next(i for i, item in enumerate(self.inventory) if item['id'] == old_id)
        self.inventory[idx] = d
        self.data_manager.save_inventory(self.inventory)
        self.refresh_table()
        self.tree.selection_set(str(d['id']))
    def delete_filament(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Löschen", "Wirklich löschen?"): return
        self.inventory = [i for i in self.inventory if i['id'] != int(sel[0])]; self.data_manager.save_inventory(self.inventory); self.refresh_table(); self.clear_inputs()
    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        i = next((x for x in self.inventory if x['id'] == int(sel[0])), None)
        if not i: return
        self.last_selected_spool_id = i.get('spool_id', -1)
        self.clear_inputs(deselect=False);
        self.entry_id.config(state="normal") 
        self.entry_id.insert(0, str(i['id']));
        self.entry_rfid.insert(0, i.get('rfid', '')); 
        self.entry_brand.insert(0, i['brand']); self.combo_material.set(i.get('material', 'PLA')); self.combo_color.set(i['color']); self.combo_subtype.set(i.get('subtype', 'Standard')); self.update_color_preview(); self.combo_type.set(i['type']); self.update_slot_dropdown(); self.combo_loc_id.set(i.get('loc_id', '')); self.entry_flow.insert(0, i.get('flow', '')); self.entry_pa.insert(0, i.get('pa', '')); self.var_reorder.set(i.get('reorder', False))
        for val in self.combo_spool['values']:
            if val.startswith(f"{i.get('spool_id', -1)} -"): self.combo_spool.set(val); break
        self.var_capacity.set(str(i.get('capacity', 1000))); gross = str(i.get('weight_gross', '0')).replace(',', '.'); float_g = float(gross) if gross else 0; self.var_gross.set(str(float_g).rstrip('0').rstrip('.') if float_g > 0 else ""); self.var_price.set(str(i.get('price', ''))); self.update_net_weight_display(); self.entry_supplier.insert(0, i.get('supplier', '')); self.entry_sku.insert(0, i.get('sku', '')); self.entry_link.insert(0, i.get('link', '')); self.entry_temp_n.insert(0, i.get('temp_n', '')); self.entry_temp_b.insert(0, i.get('temp_b', ''))
        self.var_is_refill.set(i.get('is_refill', False))
    
    def clear_inputs(self, deselect=True):
        self.last_selected_spool_id = -1
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
        
        # Holt exakt das Regal, das wir bearbeiten wollen
        target_shelf = next((s for s in parsed_shelves if s['name'] == target_shelf_name), None)
        if not target_shelf: return
        shelf_count = target_shelf['rows']
        
        win_height = max(250, 120 + (shelf_count * 32))
        win.geometry(f"350x{win_height}")
        
        # NEU: Ein verschachteltes Dictionary (V2), um Regale zu trennen!
        all_shelf_names = self.settings.get("shelf_names_v2", {})
        old_names = all_shelf_names.get(target_shelf_name, {})
        
        lbl_r = current_lbl_r if current_lbl_r else self.settings.get('label_row', 'Fach')
        
        entries = {}
        frame_list = ttk.Frame(win)
        frame_list.pack(fill="both", expand=True, padx=20, pady=5)
        
        for i in range(1, shelf_count + 1):
            frm = ttk.Frame(frame_list)
            frm.pack(fill="x", pady=3)
            ttk.Label(frm, text=f"{lbl_r} {i}:", width=12).pack(side="left")
            ent = ttk.Entry(frm)
            ent.pack(side="right", fill="x", expand=True)
            ent.insert(0, old_names.get(str(i), f"{lbl_r} {i}"))
            entries[str(i)] = ent

        def save_names():
            new_names = {k: v.get().strip() for k, v in entries.items()}
            
            changes_made = 0
            for i in range(1, shelf_count + 1):
                old_val = old_names.get(str(i), f"{lbl_r} {i}")
                new_val = new_names.get(str(i), f"{lbl_r} {i}")
                
                if old_val != new_val: 
                    lbl_c = self.settings.get('label_col', 'Slot')
                    search_str = f"{old_val} - {lbl_c} "
                    replace_str = f"{new_val} - {lbl_c} "
                    
                    for item in self.inventory:
                        # KUGELSICHER: Nur ändern, wenn die Spule auch in DIESEM Regal liegt!
                        if item.get("type") == target_shelf_name and item.get("loc_id", "").startswith(search_str):
                            item["loc_id"] = item["loc_id"].replace(search_str, replace_str, 1)
                            changes_made += 1
            
            all_shelf_names[target_shelf_name] = new_names
            self.settings["shelf_names_v2"] = all_shelf_names
            self.data_manager.save_settings(self.settings)
            
            if changes_made > 0:
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                
            self.update_slot_dropdown()
            messagebox.showinfo("Gespeichert", f"Namen für {target_shelf_name} aktualisiert!\n{changes_made} Spulen wurden automatisch angepasst.", parent=win)
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

    def refresh_all_data(self): 
        self.inventory, self.settings, self.spools = self.data_manager.load_all(DEFAULT_SETTINGS) # type: ignore
        self.apply_theme(); self.update_locations_dropdown(); self.refresh_table()

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
        
        for sh in parsed_shelves:
            name = sh['name']
            rows = sh['rows']
            cols = sh['cols']
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    # FIX: Exaktes VibeSpool Format! (z.B. "REGAL Fach 1 - Slot 1")
                    all_locs.append(f"{name} {lbl_row} {r} - {lbl_col} {c}")
        
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
            current_fil = next((i for i in active_filaments if i.get('type') == "ams_name" and str(i.get('loc_id')) == str(slot_num)), None)
            
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
        
        # Der Speichern-Button
        ttk.Button(win, text="💾 Sync in Datenbank speichern", command=lambda: self.apply_ams_sync(win), style="Accent.TButton").pack(pady=15)

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
                if existing:
                    collisions.append(f"• {old_destination} (ist belegt durch: #{existing['id']} {existing.get('brand','')} {existing.get('color','')})")
                    
        # Wenn wir Kollisionen gefunden haben, schlagen wir Alarm!
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
    
    def show_statistics_dialog(self):
        import datetime
        import json
        import os
        
        stat_win = tk.Toplevel(self.root)
        stat_win.title("📊 Verbrauchs-Statistik (Letzte 7 Tage)")
        stat_win.geometry("500x350")
        stat_win.configure(bg=self.root.cget('bg'))
        
        # Daten laden
        data_dir = self.settings.get("data_path", "")
        history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
        history = {}
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
                
        # Die letzten 7 Tage generieren
        today = datetime.date.today()
        last_7_days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        
        # Werte extrahieren
        values = [history.get(day, 0.0) for day in last_7_days]
        max_val = max(values) if max(values) > 0 else 100 # Skalierungsschutz
        
        # Canvas (Leinwand) erstellen
        c_width, c_height = 460, 250
        canvas = tk.Canvas(stat_win, width=c_width, height=c_height, bg="#2b2b2b", highlightthickness=0)
        canvas.pack(pady=20)
        
        bar_width = 40
        spacing = 20
        start_x = 30
        
        # Balken zeichnen
        for i, val in enumerate(values):
            x0 = start_x + i * (bar_width + spacing)
            x1 = x0 + bar_width
            # Höhe relativ zum Maximalwert berechnen
            bar_height = (val / max_val) * (c_height - 50) 
            y0 = c_height - 30 - bar_height
            y1 = c_height - 30
            
            # Balken
            color = "#00a8ff" if val > 0 else "#444444"
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            
            # Gramm-Text oben drüber
            if val > 0:
                canvas.create_text(x0 + bar_width/2, y0 - 10, text=f"{int(val)}g", fill="white", font=("Arial", 9))
                
            # Wochentag unten drunter (z.B. "Mo", "Di")
            day_obj = datetime.datetime.strptime(last_7_days[i], "%Y-%m-%d")
            day_name = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][day_obj.weekday()]
            canvas.create_text(x0 + bar_width/2, c_height - 10, text=day_name, fill="gray", font=("Arial", 10))
    
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
        self.menu_row.add_command(label="🔄 Quick-Swap (ins AMS)", command=self.quick_swap_dialog)
        self.menu_row.add_command(label="🐑 Spule klonen", command=self.clone_filament)
        self.menu_row.add_separator()
        self.menu_row.add_command(label="📦 Ins Lager verschieben", command=self.send_to_storage)
        self.menu_row.add_command(label="🚮 Als LEER markieren", command=self.quick_mark_empty)
        self.menu_row.add_command(label="🛒 Auf Einkaufsliste setzen/entfernen", command=self.quick_toggle_reorder)
        self.menu_row.add_separator()
        self.menu_row.add_command(label="📝 Etikett-Vorschau öffnen", command=self.quick_open_label)
        self.menu_row.add_command(label="❌ Spule löschen", command=self.delete_filament)

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
                self.on_select(None) # Lade die Daten ins Formular links
                self.menu_row.tk_popup(event.x_root, event.y_root)

    # --- HILFSFUNKTIONEN FÜR DAS RECHTSKLICK-MENÜ ---
    def quick_mark_empty(self):
        sel = self.tree.selection()
        if not sel: return
        item = next((i for i in self.inventory if i['id'] == int(sel[0])), None)
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
        item = next((i for i in self.inventory if i['id'] == int(sel[0])), None)
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

    def log_consumption(self, amount_g):
        import datetime
        import json
        import os
        
        # NEU: Wir blocken nur noch echte Nullen, erlauben aber Minuswerte!
        if amount_g == 0: return 
        
        data_dir = self.settings.get("data_path", "")
        history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
        
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except: pass
            
        today = datetime.date.today().isoformat()
        
        # Heutigen Verbrauch berechnen (Wenn amount_g negativ ist, wird abgezogen!)
        new_val = history.get(today, 0.0) + float(amount_g)
        
        # NEU: Verhindert, dass der Tagesverbrauch unter 0g fällt 
        # (z.B. wenn man gestern gedruckt hat, aber heute erst die Korrektur einträgt)
        history[today] = max(0.0, new_val)
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=4)

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
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools)
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
        data_dir = self.settings.get("data_path", "")
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
    
class PdfExportDialog(tk.Toplevel):
    def __init__(self, parent, inventory, spools):
        super().__init__(parent)
        self.inventory = inventory
        self.spools = spools
        self.title("📑 PDF Smart Export")
        self.geometry("450x300")
        self.configure(bg=parent.cget('bg'))
        from core.utils import center_window
        center_window(self, parent)
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text="Wie möchtest du die Etiketten drucken?", font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))

        self.var_format = tk.StringVar(value="A4")
        
        frm_opts = ttk.Frame(self, padding=10)
        frm_opts.pack(fill="x")
        
        ttk.Radiobutton(frm_opts, text="📄 DIN A4 Bogen (Mehrere pro Seite / Gitter)", variable=self.var_format, value="A4", command=self.toggle_opts).pack(anchor="w", pady=5)
        
        self.frm_grid = ttk.Frame(frm_opts)
        self.frm_grid.pack(fill="x", padx=20)
        ttk.Label(self.frm_grid, text="Spalten:").grid(row=0, column=0, sticky="w")
        self.var_cols = tk.IntVar(value=2)
        ttk.Spinbox(self.frm_grid, from_=1, to=5, textvariable=self.var_cols, width=5).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.frm_grid, text="Reihen:").grid(row=1, column=0, sticky="w")
        self.var_rows = tk.IntVar(value=4)
        ttk.Spinbox(self.frm_grid, from_=1, to=15, textvariable=self.var_rows, width=5).grid(row=1, column=1, padx=5, pady=2)

        ttk.Radiobutton(frm_opts, text="🏷️ Rollen-Etikettendrucker (1 Label = 1 Seite)", variable=self.var_format, value="ROLL", command=self.toggle_opts).pack(anchor="w", pady=(15, 5))

        ttk.Button(self, text="🚀 PDF Generieren", command=self.generate, style="Accent.TButton").pack(pady=15, fill="x", padx=40)

    def toggle_opts(self):
        if self.var_format.get() == "A4":
            self.frm_grid.pack(fill="x", padx=20)
        else:
            self.frm_grid.pack_forget()

    def generate(self):
        fp = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Labels speichern", initialfile="VibeSpool_Labels.pdf")
        if not fp: return

        try:
            from PIL import Image, ImageDraw, ImageFont
            import qrcode
            from qrcode.image.pil import PilImage

            try:
                font_title = ImageFont.truetype("arialbd.ttf", 45)
                font_sub = ImageFont.truetype("arial.ttf", 35)
                font_small = ImageFont.truetype("arial.ttf", 25)
            except:
                font_title = font_sub = font_small = ImageFont.load_default()

            pdf_pages = []
            
            # Helper zum Zeichnen eines einzelnen Labels
            def draw_single_label(item):
                from core.utils import get_colors_from_text
                img = Image.new('RGB', (800, 400), color='white')
                draw = ImageDraw.Draw(img)
                
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(f"ID:{item['id']}") 
                qr.make(fit=True)
                qr_img = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white").get_image().convert('RGB').resize((360, 360)) 
                img.paste(qr_img, (20, 20))
                
                draw.text((400, 30), f"{item.get('brand', '')} {item.get('material', '')}", fill="black", font=font_title)
                draw.text((400, 100), f"{item.get('color', '')}", fill="#333333", font=font_sub)
                draw.text((400, 150), f"{item.get('subtype', 'Standard')}", fill="#666666", font=font_sub)
                draw.text((400, 240), f"Nozzle: {item.get('temp_n', '-')} °C", fill="black", font=font_small)
                draw.text((400, 280), f"Bed: {item.get('temp_b', '-')} °C", fill="black", font=font_small)
                draw.text((400, 330), f"VibeSpool ID: {item['id']}", fill="black", font=font_title)
                
                cols = get_colors_from_text(item.get('color', ''))
                hex_col = cols[0] if cols else "#FFFFFF"
                draw.rectangle([400, 370, 760, 390], fill=hex_col, outline="black")
                return img

            # --- LOGIK FÜR ROLLEN-DRUCKER ---
            if self.var_format.get() == "ROLL":
                for item in self.inventory:
                    pdf_pages.append(draw_single_label(item))

            # --- LOGIK FÜR DIN A4 BÖGEN ---
            else:
                a4_w, a4_h = 2480, 3508 # DIN A4 bei 300 DPI
                cols, rows = max(1, self.var_cols.get()), max(1, self.var_rows.get())
                
                # Wir berechnen die Ränder und Abstände automatisch!
                label_w, label_h = 800, 400
                margin_x = (a4_w - (cols * label_w)) // (cols + 1)
                margin_y = (a4_h - (rows * label_h)) // (rows + 1)
                
                current_page = Image.new('RGB', (a4_w, a4_h), 'white')
                x_idx, y_idx = 0, 0
                
                for item in self.inventory:
                    lbl_img = draw_single_label(item)
                    
                    pos_x = margin_x + (x_idx * (label_w + margin_x))
                    pos_y = margin_y + (y_idx * (label_h + margin_y))
                    
                    current_page.paste(lbl_img, (pos_x, pos_y))
                    
                    x_idx += 1
                    if x_idx >= cols:
                        x_idx = 0
                        y_idx += 1
                        
                    # Wenn die Seite voll ist, speichern wir sie ab und nehmen ein neues A4 Blatt!
                    if y_idx >= rows:
                        pdf_pages.append(current_page)
                        current_page = Image.new('RGB', (a4_w, a4_h), 'white')
                        x_idx, y_idx = 0, 0
                
                # Die letzte (evtl. unfertige) Seite noch anhängen
                if x_idx > 0 or y_idx > 0:
                    pdf_pages.append(current_page)

            if pdf_pages:
                pdf_pages[0].save(fp, "PDF", resolution=300.0 if self.var_format.get() == "A4" else 100.0, save_all=True, append_images=pdf_pages[1:])
                messagebox.showinfo("Exportiert", f"Erfolg!\n{len(self.inventory)} Etiketten wurden auf {len(pdf_pages)} Seite(n) verteilt.", parent=self)
                self.destroy()

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Generieren:\n{e}", parent=self)

if __name__ == "__main__":
    try: windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk(); app = FilamentApp(root); root.mainloop()
