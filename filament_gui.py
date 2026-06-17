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

# --- EXTRACTED DIALOGS IMPORT ---
from core.spool_manager import SpoolManager
from core.shelf_planner import ShelfPlannerDialog
from core.settings_dialog import SettingsDialog
from core.shelf_visualizer import ShelfVisualizer
from core.shopping_list import ShoppingListDialog
from core.statistics import StatisticsDialog
from core.flow_calculator import FlowCalculatorDialog
from core.backup import BackupDialog
from core.printer_job import PrinterJobDialog
from core.manual_print import ManualPrintDialog

# --- STYLE & CONFIG CONSTANTS ---
from core.constants import (
    APP_VERSION, GITHUB_REPO, DEFAULT_SETTINGS, MATERIALS, SUBTYPES, 
    COMMON_COLORS, THEMES, COLOR_ACCENT, COLOR_DELETE, COLOR_SUCCESS, FONT_MAIN, FONT_BOLD
)

def fetch_last_print_usage(url, key): 
    return None
def fetch_recent_jobs(url, key): 
    return []

def create_tray_icon():
    # Zeichnet einen simplen blauen Kreis als Platzhalter-Icon für die Taskleiste
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(0, 120, 215))
    return image


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
        self.shelf_visualizer = None
        
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
        self.var_ams_fixed_main = tk.BooleanVar(value=self.settings.get("ams_fixed_top", False))
        self.menu_opts.add_checkbutton(label="🤖 AMS oben fixieren", variable=self.var_ams_fixed_main, command=self.toggle_ams_fixed_main)
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="📥 CSV Inventar Importieren", command=self.import_csv)
        self.menu_opts.add_command(label="💾 Datenbank Backup / Restore", command=lambda: BackupDialog(self.root, self.data_manager, self))
        self.menu_opts.add_separator()
        self.menu_opts.add_command(label="🔄 Update-Check", command=self.manual_update_check)
        self.btn_opts["menu"] = self.menu_opts
        self.btn_opts.pack(side="right", padx=5)
        
        ttk.Button(top_bar, text="🛒 Einkaufsliste", command=lambda: ShoppingListDialog(self.root, self.inventory, self)).pack(side="right", padx=5)
        ttk.Button(top_bar, text="📄 PDF Export", command=self.export_pdf).pack(side="right", padx=5)
        
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

        add_nav_btn("Regal", self.open_shelf_visualizer, "📦")
        add_nav_btn("Spulen", lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown, self), "🧵")
        
        # FIX: Ein Leerzeichen vor dem Emoji schiebt es optisch genau in die Mitte!
        add_nav_btn("Label", lambda: LabelCreatorDialog(self.root, self.inventory, self), "   🏷️")

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
        add_nav_btn("Flow", lambda: FlowCalculatorDialog(self.root, self.entry_flow, self), "🧪")
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
        
        clean_colors = []
        for c in self.settings.get("colors", COMMON_COLORS):
            clean_name = re.sub(r'\s*\(?#[0-9a-fA-F]{6}\)?', '', c).strip()
            if clean_name and clean_name not in clean_colors:
                clean_colors.append(clean_name)
        self.combo_color = ttk.Combobox(frm_col, values=clean_colors, font=FONT_MAIN)
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
                        new_parts.append(matched_name)
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

            new_entry = matched_name if matched_name else color_code

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
        ttk.Button(btn_frame, text="📦 Regal & AMS Ansicht", command=self.open_shelf_visualizer).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🧵 Leerspulen verwalten", command=lambda: SpoolManager(self.root, self.data_manager, self.update_spool_dropdown, self)).pack(fill="x", pady=2)
        
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

        # --- NEU: Bambu Auto-Sync Monitore starten ---
        self.bambu_monitors = []
        printers = self.settings.get("printers", [])
        for p in printers:
            if p.get("type") == "bambu" and p.get("use_mqtt", False):
                try:
                    from core.bambu_sync import BambuBackgroundMonitor
                    ip = p.get("ip", "")
                    code = p.get("access_code", "")
                    serial = p.get("serial", "")
                    p_id = p.get("id")
                    
                    if ip and code and serial:
                        monitor = BambuBackgroundMonitor(
                            p_id, ip, code, serial, 
                            on_finish_callback=self.on_bambu_print_finish
                        )
                        monitor.start()
                        self.bambu_monitors.append(monitor)
                        print(f"🤖 Monitor für '{p.get('name')}' erfolgreich gestartet.")
                except Exception as e:
                    print(f"Bambu Monitor für '{p.get('name')}' konnte nicht gestartet werden: {e}")

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
        ttk.Label(parent, text="Spulen & Verbrauch (g):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        spools_frame = ttk.Frame(parent)
        spools_frame.pack(fill="x", pady=(0, 10))
        
        rows = []
        
        # Prepare spool dropdown values
        spool_list = ["[ Manueller Eintrag ]"]
        for i in self.inventory:
            if i.get('type') != 'VERBRAUCHT':
                color_clean = str(i.get('color', '')).split('(')[0].strip()
                spool_list.append(f"[{i['id']}] {i.get('brand','')} {color_clean}")

        def add_row(price="25.00", weight="100"):
            row_container = ttk.Frame(spools_frame)
            row_container.pack(fill="x", pady=5)
            
            # Line 1: Search Entry
            search_frm = ttk.Frame(row_container)
            search_frm.pack(fill="x", pady=(0, 2))
            
            ttk.Label(search_frm, text="🔍", font=("Segoe UI", 9)).pack(side="left", padx=(0, 2))
            ent_search = ttk.Entry(search_frm, font=("Segoe UI", 9))
            ent_search.pack(side="left", fill="x", expand=True)
            
            # Line 2: Combobox
            combo_spool = ttk.Combobox(row_container, values=spool_list, state="readonly", font=("Segoe UI", 9))
            combo_spool.current(0)
            combo_spool.pack(fill="x", pady=(0, 2))
            
            # Line 3: Fields and delete button
            fields_frm = ttk.Frame(row_container)
            fields_frm.pack(fill="x")
            
            ent_p = ttk.Entry(fields_frm, width=8)
            ent_p.insert(0, price)
            ent_p.pack(side="left")
            ttk.Label(fields_frm, text="€/kg").pack(side="left", padx=(2, 8))
            
            ent_w = ttk.Entry(fields_frm, width=6)
            ent_w.insert(0, weight)
            ent_w.pack(side="left")
            ttk.Label(fields_frm, text="g").pack(side="left", padx=2)
            
            btn_del = ttk.Button(fields_frm, text="❌", width=3, command=lambda: remove_row(row_container))
            btn_del.pack(side="right")
            
            def on_spool_select(event):
                val = combo_spool.get()
                if val == "[ Manueller Eintrag ]":
                    pass
                else:
                    if val.startswith("[") and "]" in val:
                        sp_id = val.split("]")[0][1:]
                        sp = next((i for i in self.inventory if str(i.get('id')) == str(sp_id)), None)
                        if sp:
                            try:
                                sp_price = float(str(sp.get('price', '0')).replace(',', '.'))
                                sp_cap = float(str(sp.get('capacity', '1000')))
                                if sp_cap > 0:
                                    price_per_kg = (sp_price / sp_cap) * 1000.0
                                    ent_p.delete(0, tk.END)
                                    ent_p.insert(0, f"{price_per_kg:.2f}")
                                    calc()  # Recalculate live
                            except: pass
                            
            def filter_spools(event):
                q = ent_search.get().lower().strip()
                if not q:
                    combo_spool['values'] = spool_list
                else:
                    filtered = [spool_list[0]] + [s for s in spool_list[1:] if q in s.lower()]
                    combo_spool['values'] = filtered
                    if len(filtered) > 1:
                        combo_spool.current(1)
                        on_spool_select(None)
                    else:
                        combo_spool.current(0)
                            
            combo_spool.bind("<<ComboboxSelected>>", on_spool_select)
            ent_search.bind("<KeyRelease>", filter_spools)
            
            rows.append((row_container, ent_p, ent_w, btn_del))
            if len(rows) == 1:
                btn_del.state(['disabled'])
            else:
                for r in rows:
                    r[3].state(['!disabled'])
                    
        def remove_row(row_container):
            for i, r in enumerate(rows):
                if r[0] == row_container:
                    r[0].destroy()
                    rows.pop(i)
                    break
            if len(rows) == 1:
                rows[0][3].state(['disabled'])
            calc()  # Recalculate live
                
        # Initial row
        add_row()
        
        btn_add = ttk.Button(parent, text="➕ Spule hinzufügen", command=lambda: add_row())
        btn_add.pack(fill="x", pady=(0, 15))
        
        ttk.Label(parent, text="Drucker:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        printers_list = self.settings.get("printers", [])
        printer_values = ["- Globaler Standard -"] + [p.get("name", "Drucker") for p in printers_list]
        combo_printer = ttk.Combobox(parent, values=printer_values, state="readonly", font=("Segoe UI", 9))
        combo_printer.current(0)
        combo_printer.pack(fill="x", pady=(0, 15))
        
        ttk.Label(parent, text="Druckzeit (Stunden):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ent_time = ttk.Entry(parent)
        ent_time.insert(0, "5")
        ent_time.pack(fill="x", pady=(0, 15))
        
        lbl_res = ttk.Label(parent, text="", font=("Segoe UI", 11, "bold"), foreground="#0078d7", justify="center")
        lbl_res.pack(pady=20)
        
        def calc():
            try:
                t = float(ent_time.get().replace(",", "."))
                
                mat = 0.0
                total_w = 0.0
                for row_container, ent_p, ent_w, _ in rows:
                    p = float(ent_p.get().replace(",", "."))
                    w = float(ent_w.get().replace(",", "."))
                    mat += w * (p / 1000.0)
                    total_w += w
                    
                selected_printer_idx = combo_printer.current()
                selected_printer = None
                if selected_printer_idx > 0 and selected_printer_idx - 1 < len(printers_list):
                    selected_printer = printers_list[selected_printer_idx - 1]
                    
                kwh = float(self.settings.get("kwh_price", 0.30))
                
                watt = 150
                if selected_printer and selected_printer.get("printer_watts") not in (None, ""):
                    try: watt = int(selected_printer.get("printer_watts"))
                    except: pass
                else:
                    watt = int(self.settings.get("printer_watts", 150))
                    
                wear_val = 0.20
                if selected_printer and selected_printer.get("wear_per_hour") not in (None, ""):
                    try: wear_val = float(selected_printer.get("wear_per_hour"))
                    except: pass
                else:
                    wear_val = float(self.settings.get("wear_per_hour", 0.20))
                    
                elec = t * (watt / 1000.0) * kwh
                wear = t * wear_val
                total = mat + elec + wear
                margin = int(self.settings.get("profit_margin", 0))
                sell = total * (1 + (margin/100.0))
                
                res = f"Gesamt-Gewicht: {total_w:.1f} g\n"
                res += f"Material: {mat:.2f} € | Strom: {elec:.2f} €\nVerschleiß: {wear:.2f} €\n"
                res += f"--------------------------\nKOSTEN: {total:.2f} €\n"
                if margin > 0: res += f"VK (+{margin}%): {sell:.2f} €"
                lbl_res.config(text=res)
            except:
                lbl_res.config(text="⚠️ Bitte Zahlen eingeben!")
                
        combo_printer.bind("<<ComboboxSelected>>", lambda e: calc())
        ttk.Button(parent, text="Berechnen", command=calc, style="Accent.TButton").pack(fill="x", pady=10)

    def toggle_ams_fixed_main(self):
        self.settings["ams_fixed_top"] = self.var_ams_fixed_main.get()
        self.data_manager.save_settings(self.settings)
        if hasattr(self, 'shelf_visualizer') and self.shelf_visualizer and self.shelf_visualizer.winfo_exists():
            self.shelf_visualizer.var_ams_fixed.set(self.var_ams_fixed_main.get())
            self.shelf_visualizer.redraw()

    def open_shelf_visualizer(self):
        if hasattr(self, 'shelf_visualizer') and self.shelf_visualizer and self.shelf_visualizer.winfo_exists():
            self.shelf_visualizer.focus_set()
        else:
            self.shelf_visualizer = ShelfVisualizer(self.root, self.inventory, self.settings, self.spools, self)

    def update_color_preview(self, event=None):
        cols = get_colors_from_text(self.combo_color.get(), self.settings.get("colors", COMMON_COLORS))
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
            try:
                self.settings["geometry"] = self.root.winfo_geometry()
                self.data_manager.save_settings(self.settings)
            except:
                pass
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
        
        # Hintergrund-Monitore stoppen
        if hasattr(self, 'bambu_monitors') and self.bambu_monitors:
            for monitor in self.bambu_monitors:
                try: monitor.stop()
                except: pass
            
        # Einstellungen speichern und App zerstören
        try:
            self.settings["geometry"] = self.root.winfo_geometry()
            self.data_manager.save_settings(self.settings)
        except: pass
        
        self.root.after(0, self.root.destroy)
    
    def apply_theme(self):
        theme = self.settings.get("theme", "dark")
        c = THEMES[theme]
        self.root.configure(bg=c["bg"])
        s = self.style
        
        # --- NATIVE WINDOWS TITELLEISTE (DARK MODE) ---
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1 if theme == "dark" else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

        # Option Database definitions for standard components
        self.root.option_add('*Listbox.background', c["entry_bg"])
        self.root.option_add('*Listbox.foreground', c["fg"])
        self.root.option_add('*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*Listbox.selectForeground', "white")
        self.root.option_add('*Listbox.font', FONT_MAIN)
        self.root.option_add('*TCombobox*Listbox.background', c["entry_bg"])
        self.root.option_add('*TCombobox*Listbox.foreground', c["fg"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', "white")
        self.root.option_add('*TCombobox*Listbox.font', FONT_MAIN)
        self.root.option_add('*Text.background', c["entry_bg"])
        self.root.option_add('*Text.foreground', c["fg"])
        self.root.option_add('*Text.insertBackground', c["fg"])
        self.root.option_add('*Text.font', FONT_MAIN)

        s.configure(".", background=c["bg"], foreground=c["fg"], font=FONT_MAIN)
        s.configure("TLabel", background=c["bg"], foreground=c["fg"])
        s.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
        s.map("TCheckbutton", background=[("active", c["bg"])], foreground=[("active", c["fg"])])
        s.configure("TLabelframe", background=c["bg"], foreground=c["fg"], bordercolor="#E5E5EA" if theme == "light" else "#2C2C2E", borderwidth=1)
        s.configure("TLabelframe.Label", background=c["bg"], foreground=c["lbl_frame"], font=FONT_BOLD)
        
        # Treeview styling (clean, borderless, contrasting headings)
        s.configure("Treeview", background=c["tree_bg"], fieldbackground=c["tree_bg"], foreground=c["tree_fg"], borderwidth=0)
        s.configure("Treeview.Heading", background=c["head_bg"], foreground=c["head_fg"], font=FONT_BOLD, borderwidth=1, bordercolor=c["bg"])
        s.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "white")])
        s.map("Treeview.Heading", background=[("active", "#D1D1D6" if theme == "light" else "#48484A")], foreground=[("active", c["head_fg"])])
        
        # Apple secondary button styles
        button_bg = "#E5E5EA" if theme == "light" else "#2C2C2E"
        button_fg = "#000000" if theme == "light" else "#FFFFFF"
        button_active_bg = "#D1D1D6" if theme == "light" else "#3A3A3C"
        s.configure("TButton", background=button_bg, foreground=button_fg, borderwidth=1, bordercolor=button_bg, relief="flat", padding=[8, 4])
        s.map("TButton", background=[("active", button_active_bg), ("disabled", button_bg)], foreground=[("active", button_fg), ("disabled", "#8E8E93")])
        
        # Accent button style
        s.configure("Accent.TButton", background=COLOR_ACCENT, foreground="white", borderwidth=1, bordercolor=COLOR_ACCENT, relief="flat", padding=[8, 4])
        s.map("Accent.TButton", background=[("active", "#0062CC" if theme == "light" else "#3395FF"), ("disabled", "#D1D1D6" if theme == "light" else "#3A3A3C")], foreground=[("active", "white"), ("disabled", "#8E8E93")])
        
        # Delete button style
        s.configure("Delete.TButton", background=COLOR_DELETE, foreground="white", borderwidth=1, bordercolor=COLOR_DELETE, relief="flat", padding=[8, 4])
        s.map("Delete.TButton", background=[("active", "#D32F2F" if theme == "light" else "#FF453A"), ("disabled", "#D1D1D6" if theme == "light" else "#3A3A3C")], foreground=[("active", "white"), ("disabled", "#8E8E93")])
        
        # Entry styling (rounded/flat with focus glow)
        entry_border = "#C7C7CC" if theme == "light" else "#48484A"
        s.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["entry_fg"], borderwidth=1, bordercolor=entry_border, lightcolor=c["entry_bg"], darkcolor=c["entry_bg"], padding=5)
        s.map("TEntry", bordercolor=[("focus", COLOR_ACCENT), ("active", COLOR_ACCENT)], lightcolor=[("focus", COLOR_ACCENT), ("active", COLOR_ACCENT)], darkcolor=[("focus", COLOR_ACCENT), ("active", COLOR_ACCENT)])
        
        # Combobox styling
        cb_border = "#C7C7CC" if theme == "light" else "#48484A"
        s.configure("TCombobox", fieldbackground=c["entry_bg"], foreground=c["entry_fg"], background=button_bg, borderwidth=1, bordercolor=cb_border, lightcolor=c["entry_bg"], darkcolor=c["entry_bg"], arrowcolor=c["fg"], padding=5)
        s.map("TCombobox", fieldbackground=[("readonly", c["entry_bg"])], bordercolor=[("focus", COLOR_ACCENT), ("active", COLOR_ACCENT)], lightcolor=[("focus", COLOR_ACCENT), ("active", COLOR_ACCENT)], darkcolor=[("focus", COLOR_ACCENT), ("active", COLOR_ACCENT)])
        
        # Notebook styling
        tab_bg = "#E5E5EA" if theme == "light" else "#2C2C2E"
        tab_fg = c["fg"]
        s.configure("TNotebook", background=c["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=tab_bg, foreground=tab_fg, padding=[14, 6], borderwidth=0, lightcolor=c["bg"], darkcolor=c["bg"])
        s.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT), ("active", button_active_bg)], foreground=[("selected", "white"), ("active", c["fg"])])
        
        # Scrollbar styling
        s.configure("TScrollbar", troughcolor=c["bg"], background="#C7C7CC" if theme == "light" else "#48484A", bordercolor=c["bg"], arrowcolor=c["fg"])
        s.map("TScrollbar", background=[("active", COLOR_ACCENT)])
        
        # --- NAV SIDEBAR THEME ---
        nav_bg = "#2C2C2E" if theme == "dark" else "#E5E5EA"
        nav_fg = "#FFFFFF" if theme == "dark" else "#000000"
        self.nav_sidebar.config(bg=nav_bg)
        self.nav_sep.config(bg="#48484A" if theme == "dark" else "#C7C7CC")
        for btn in self.nav_btns:
            btn.config(bg=nav_bg, fg=nav_fg, activebackground="#3A3A3C" if theme == "dark" else "#D1D1D6", activeforeground=nav_fg)
            
        # --- FORM CANVAS & CONTAINER ---
        self.form_container.config(bg=c["bg"])
        self.form_canvas.config(bg=c["bg"])
        self.scrollable_form_frame.config(bg=c["bg"])
        
        # --- DYNAMIC TREEVIEW TAGS ---
        if hasattr(self, 'tree') and self.tree.winfo_exists():
            if theme == "dark":
                self.tree.tag_configure("alert", background="#3D1E1E", foreground="#FF453A")
                self.tree.tag_configure("grayed", foreground="#7C7C80")
            else:
                self.tree.tag_configure("alert", background="#FFE5E5", foreground="#D9534F")
                self.tree.tag_configure("grayed", foreground="#8E8E93")

        # Update active child windows dynamically (e.g. ShelfVisualizer)
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.winfo_exists():
                try:
                    child.configure(bg=c["bg"])
                    if hasattr(child, 'canvas') and child.canvas.winfo_exists():
                        child.canvas.configure(bg=c["bg"])
                    if hasattr(child, 'redraw'):
                        child.redraw()
                except Exception:
                    pass

    def on_nav_btn_hover(self, btn, is_enter):
        theme = self.settings.get("theme", "dark")
        if is_enter:
            btn.config(bg="#3A3A3C" if theme == "dark" else "#D1D1D6")
        else:
            btn.config(bg="#2C2C2E" if theme == "dark" else "#E5E5EA")

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
            clean_colors = []
            for c in s.get("colors", COMMON_COLORS):
                clean_name = re.sub(r'\s*\(?#[0-9a-fA-F]{6}\)?', '', c).strip()
                if clean_name and clean_name not in clean_colors:
                    clean_colors.append(clean_name)
            self.combo_color['values'] = clean_colors
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
            
            # 2. Wir sortieren beide Listen unabhängig voneinander.
            # Die AMS-Spulen bleiben IMMER in ihrer physischen Slot-Reihenfolge (aufsteigend) fixiert!
            def ams_sort_key(i):
                val = f"{str(i.get('type', ''))} {str(i.get('loc_id', ''))}"
                return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', val)]
            
            ams_list.sort(key=ams_sort_key)
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
            
        # --- NEU: Live-Update für ein offenes Regal-Fenster ---
        vis = getattr(self, 'shelf_visualizer', None)
        if vis is not None and vis.winfo_exists():
            try: vis.redraw()
            except: pass
    
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
            clean_colors = []
            for c in self.settings.get("colors", COMMON_COLORS):
                clean_name = re.sub(r'\s*\(?#[0-9a-fA-F]{6}\)?', '', c).strip()
                if clean_name and clean_name not in clean_colors:
                    clean_colors.append(clean_name)
            self.combo_color['values'] = clean_colors
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
        win.geometry("480x240")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        center_window(win, self.root)
        
        ttk.Label(win, text="Spule an neuen Ort verschieben/tauschen:", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        ttk.Label(win, text=f"{s_a.get('brand', '')} {s_a.get('color', '')}", font=("Segoe UI", 10)).pack(pady=5)
        
        ams_map = {}
        # 1. AMS-Slots
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

        # 2. Externe Spule / Custom Locations
        custom_str = self.settings.get("custom_locs", "")
        if custom_str:
            custom_list = [x.strip() for x in custom_str.split(",") if x.strip()]
            for loc in custom_list:
                spools_at_loc = [i for i in self.inventory if i.get('type') == loc]
                if spools_at_loc:
                    names = ", ".join(f"{i.get('brand', '')} {i.get('color', '')}" for i in spools_at_loc[:2])
                    if len(spools_at_loc) > 2:
                        names += " ..."
                    label_text = f"Belegt: {names}"
                else:
                    label_text = "(LEER)"
                d_t = f"{loc}  -->  {label_text}"
                ams_map[d_t] = (loc, "-")

        # 3. Das globale LAGER
        spools_at_lager = [i for i in self.inventory if i.get('type') == "LAGER"]
        d_t = f"LAGER (Hauptlager)  -->  ({len(spools_at_lager)} Spulen vor Ort)"
        ams_map[d_t] = ("LAGER", "-")
                
        combo = ttk.Combobox(win, values=list(ams_map.keys()), state="readonly", font=FONT_MAIN, width=45)
        combo.pack(pady=10)
        combo.current(0)
        
        def do_swap():
            t_am, t_sl = ams_map[combo.get()]
            o_t, o_l = s_a.get('type', 'LAGER'), s_a.get('loc_id', '-')
            
            s_b = None
            if t_sl != "-":
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
            
            loc_disp = f"{t_am} (Slot {t_sl})" if t_sl != "-" else t_am
            messagebox.showinfo("Quick-Swap Erfolgreich", f"{s_a.get('brand', '')} ist in {loc_disp}.{msg_extra}", parent=self.root)
            
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

    
    def on_bambu_print_finish(self, printer_id, tray_ids, weight_g):
        """Wird vom Hintergrund-Thread aufgerufen, wenn der Druck fertig ist."""
        # Suche den Drucker in den Einstellungen
        printers = self.settings.get("printers", [])
        printer = next((p for p in printers if p.get("id") == printer_id), None)
        if not printer: return
        
        if not tray_ids: return
        
        # Springe in den Haupt-Thread
        self.root.after(0, lambda: self._process_bambu_finish_ui(printer, tray_ids, weight_g))

    def _process_bambu_finish_ui(self, printer, tray_ids, weight_g):
        ams_ids = printer.get("ams_ids", [])
        
        if len(tray_ids) == 1 and weight_g > 0:
            raw_slot = tray_ids[0]
            
            if raw_slot == 255:
                # Druck von externer Spule!
                ext_loc = printer.get("external_loc", "")
                if ext_loc:
                    matching_items = [i for i in self.inventory if i.get("type") == ext_loc and i.get("type") != "VERBRAUCHT"]
                    if len(matching_items) == 1:
                        # Eindeutige Zuweisung möglich! -> Automatisch abziehen
                        self._apply_automatic_deduction_item(matching_items[0], weight_g)
                        return
                
                # Wenn nicht eindeutig, fragen wir den User per Dialog
                self._show_multicolor_dialog_v2(printer, tray_ids, weight_g)
            else:
                # Druck aus dem AMS
                local_ams_idx = raw_slot // 4
                if local_ams_idx < len(ams_ids):
                    global_ams_id = ams_ids[local_ams_idx]
                    slot = (raw_slot % 4) + 1
                    self._apply_automatic_deduction(f"AMS {global_ams_id}", str(slot), weight_g)
                else:
                    # Fallback falls Zuordnung fehlt
                    self._show_multicolor_dialog_v2(printer, tray_ids, weight_g)
        else:
            self._show_multicolor_dialog_v2(printer, tray_ids, weight_g)

    def _apply_automatic_deduction_item(self, item, weight_g, silent=False):
        """Führt den Abzug direkt von einem bestimmten Spulen-Item aus."""
        if item:
            try:
                old_gross = float(str(item.get('weight_gross', '0')).replace(',', '.'))
                new_gross = max(0, old_gross - weight_g)
                item['weight_gross'] = new_gross
                
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
                
                self.log_consumption(weight_g)
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                self.broadcast_mqtt()
                
                sel = self.tree.selection()
                if sel and str(sel[0]) == str(item['id']):
                    self.on_select(None)
                
                if not silent:
                    msg = f"Es wurden {weight_g:.1f}g von Spule #{item['id']} abgezogen.\n({item.get('brand')} {item.get('color')})"
                    self.show_custom_toast("🎨 Druck beendet!", msg)
            except Exception as e:
                print(f"Fehler bei automatischer Zuweisung: {e}")

    def _show_multicolor_dialog_v2(self, printer, tray_ids, total_weight_g):
        """Öffnet einen Dialog, wenn mehrere AMS-Slots benutzt wurden oder eine manuelle Zuweisung nötig ist."""
        win = tk.Toplevel(self.root)
        win.title("🎨 Filament-Zuweisung nach Druck")
        win.geometry("550x450")
        win.configure(bg=self.root.cget('bg'))
        win.attributes('-topmost', True)
        from core.utils import center_window
        center_window(win, self.root)
        
        ttk.Label(win, text=f"Druck beendet auf '{printer.get('name')}'", font=("Segoe UI", 14, "bold"), foreground="#0078d7").pack(pady=(15, 5))
        ttk.Label(win, text=f"Gesamtverbrauch (laut Slicer): {total_weight_g:.1f} g\nWelches Filament hat wie viel verbraucht?", justify="center").pack(pady=5)
        
        frm = ttk.Frame(win, padding=15)
        frm.pack(fill="both", expand=True)
        
        entries = []
        ams_ids = printer.get("ams_ids", [])
        
        for t_id in tray_ids:
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=5)
            
            item = None
            if t_id == 255:
                # Externe Spule
                ext_loc = printer.get("external_loc", "")
                lbl_text = f"Externer Halter:"
                if ext_loc:
                    item = next((i for i in self.inventory if i.get('type') == ext_loc and i.get('type') != 'VERBRAUCHT'), None)
                    if item:
                        lbl_text = f"Extern ({ext_loc}): {item.get('brand')} {item.get('color')}"
                    else:
                        lbl_text = f"Extern ({ext_loc}): Keine Spule dort"
            else:
                local_ams_idx = t_id // 4
                if local_ams_idx < len(ams_ids):
                    global_ams_id = ams_ids[local_ams_idx]
                    slot = (t_id % 4) + 1
                    ams_name = f"AMS {global_ams_id}"
                    item = next((i for i in self.inventory if i.get('type') == ams_name and str(i.get('loc_id')) == str(slot)), None)
                    if item:
                        lbl_text = f"{ams_name} Slot {slot}: {item.get('brand')} {item.get('color')}"
                    else:
                        lbl_text = f"{ams_name} Slot {slot}: Keine Spule dort"
                else:
                    lbl_text = f"AMS Slot {t_id + 1}: Unbekanntes AMS"
                    
            ttk.Label(row, text=lbl_text, width=35, anchor="w").pack(side="left")
            
            ent = ttk.Entry(row, width=10, justify="right")
            ent.pack(side="right")
            ttk.Label(row, text=" g").pack(side="right")
            
            if len(tray_ids) == 1:
                ent.insert(0, f"{total_weight_g:.1f}")
                
            entries.append({"item": item, "entry": ent})
            
        def apply_split():
            total_entered = 0
            for e in entries:
                val = e["entry"].get().strip().replace(',', '.')
                if val:
                    try:
                        weight = float(val)
                        if weight > 0 and e["item"]:
                            total_entered += weight
                            self._apply_automatic_deduction_item(e["item"], weight, silent=True)
                    except Exception as ex: 
                        print(f"Fehler bei Aufteilung: {ex}")
                    
            if total_entered > 0:
                messagebox.showinfo("Erfolg", f"Es wurden insgesamt {total_entered:.1f}g auf die Spulen aufgeteilt und abgezogen!", parent=self.root)
            win.destroy()
            
        ttk.Separator(win, orient="horizontal").pack(fill="x", pady=10)
        ttk.Button(win, text="💾 Gewichte abziehen & Speichern", command=apply_split, style="Accent.TButton").pack(pady=10)

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
        bambu_printers = [p for p in self.settings.get("printers", []) if p.get("type") == "bambu"]
        if not bambu_printers:
            # Fallback falls jemand noch die alten globalen Einstellungen hat aber keine Druckerliste
            ip = self.settings.get("bambu_ip", "")
            code = self.settings.get("bambu_access", "")
            serial = self.settings.get("bambu_serial", "")
            if ip and code and serial:
                bambu_printers = [{
                    "name": "Bambu Lab Drucker",
                    "ip": ip,
                    "access_code": code,
                    "serial": serial,
                    "ams_ids": list(range(1, self.settings.get("num_ams", 1) + 1))
                }]
            else:
                return messagebox.showerror("Fehler", "Kein Bambu Lab Drucker konfiguriert! Bitte erst in den Optionen eintragen.", parent=self.root)

        if len(bambu_printers) == 1:
            self.perform_ams_sync_for_printer(bambu_printers[0])
        else:
            win = tk.Toplevel(self.root)
            win.title("Drucker auswählen")
            win.geometry("380x165")
            win.configure(bg=self.root.cget('bg'))
            win.attributes('-topmost', True)
            center_window(win, self.root)
            
            ttk.Label(win, text="Wähle den Drucker für den AMS-Abruf:", font=FONT_BOLD).pack(pady=(15, 10))
            
            printer_names = [p.get("name", "Unbekannt") for p in bambu_printers]
            combo = ttk.Combobox(win, values=printer_names, state="readonly", font=FONT_MAIN, width=30)
            combo.pack(pady=10)
            combo.current(0)
            
            def on_confirm():
                idx = combo.current()
                win.destroy()
                self.perform_ams_sync_for_printer(bambu_printers[idx])
                
            ttk.Button(win, text="Abrufen", style="Accent.TButton", command=on_confirm).pack(pady=10)

    def perform_ams_sync_for_printer(self, printer):
        ip = printer.get("ip", "")
        code = printer.get("access_code", "")
        serial = printer.get("serial", "")

        if not ip or not code or not serial:
            return messagebox.showerror("Fehler", f"Bambu Zugangsdaten für '{printer.get('name')}' unvollständig! Bitte in den Optionen ergänzen.", parent=self.root)

        self.sync_win = tk.Toplevel(self.root)
        self.sync_win.title("AMS Sync")
        self.sync_win.geometry("350x120")
        self.sync_win.configure(bg=self.root.cget('bg'))
        center_window(self.sync_win, self.root)
        ttk.Label(self.sync_win, text=f"Verbinde mit {printer.get('name')}...\nLese AMS Daten aus.\n\nBitte warten (ca. 5-10 Sekunden).", font=FONT_BOLD, justify="center").pack(expand=True)
        self.sync_win.grab_set()

        try:
            from core.bambu_sync import BambuScanner # type: ignore
        except ImportError:
            self.sync_win.destroy()
            return messagebox.showerror("Fehler", "Das Modul 'paho-mqtt' fehlt. Bitte über pip installieren.", parent=self.root)

        def worker():
            scanner = BambuScanner(ip, code, serial)
            result = scanner.fetch_ams_inventory(timeout=10)
            self.root.after(0, lambda: self._process_ams_result(result, printer))

        threading.Thread(target=worker, daemon=True).start()

    def _process_ams_result(self, result, printer=None):
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
            ams_idx = int(r.get('ams', (raw_slot // 4)))
            ams_ids = printer.get("ams_ids", []) if printer else []
            if ams_idx < len(ams_ids):
                ams_num = ams_ids[ams_idx]
            else:
                ams_num = ams_idx + 1
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
    
    def get_filtered_items_for_export(self):
        filters = {
            "material": self.filter_mat_var.get(),
            "color": self.filter_color_var.get(),
            "location": self.filter_loc_var.get()
        }
        search_term = self.search_var.get().lower().strip()
        search_words = search_term.split() if search_term else []
        
        filtered_items = []
        for i in self.data_manager.get_filtered_inventory(self.inventory, "", filters):
            if self.filter_brand_var.get() != "Alle Hersteller" and i.get('brand') != self.filter_brand_var.get():
                continue
                
            if search_words:
                all_values = " ".join(str(v) for v in i.values() if v is not None).lower()
                if not all(word in all_values for word in search_words):
                    continue
            filtered_items.append(i)
        return filtered_items

    def export_pdf(self):
        items = self.get_filtered_items_for_export()
        if not items:
            messagebox.showwarning("PDF Export", "Keine Filamente zum Exportieren vorhanden (Filter aktiv?)", parent=self.root)
            return

        fp = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF-Dokument", "*.pdf")],
            initialfile="VibeSpool_Bestand.pdf",
            title="Filament-Bestand als PDF speichern"
        )
        if not fp:
            return

        try:
            from PIL import Image, ImageDraw, ImageFont
            
            try:
                font_title = ImageFont.truetype("arialbd.ttf", 60)
                font_subtitle = ImageFont.truetype("arial.ttf", 36)
                font_header = ImageFont.truetype("arialbd.ttf", 40)
                font_body = ImageFont.truetype("arial.ttf", 34)
                font_body_bold = ImageFont.truetype("arialbd.ttf", 34)
                font_footer = ImageFont.truetype("arial.ttf", 28)
            except:
                font_title = font_subtitle = font_header = font_body = font_body_bold = font_footer = ImageFont.load_default()

            pages = []
            
            def draw_color_swatch(draw_obj, x, y, colors):
                swatch_w, swatch_h = 60, 40
                rect = [x, y, x + swatch_w, y + swatch_h]
                if not colors:
                    draw_obj.rectangle(rect, fill="white", outline="gray", width=2)
                    return
                
                num_cols = len(colors)
                col_w = swatch_w / num_cols
                for idx, col in enumerate(colors):
                    cx1 = x + idx * col_w
                    cx2 = x + (idx + 1) * col_w
                    draw_obj.rectangle([cx1, y, cx2, y + swatch_h], fill=col)
                draw_obj.rectangle(rect, fill=None, outline="black", width=2)

            def start_new_page(is_first):
                pg = Image.new('RGB', (2480, 3508), 'white')
                d = ImageDraw.Draw(pg)
                
                if is_first:
                    d.text((100, 100), "VibeSpool Filament-Bestand", fill="#111111", font=font_title)
                    
                    total_spools = len(items)
                    total_net_weight_kg = sum(calculate_net_weight(i.get('weight_gross', '0'), i.get('spool_id', -1), self.spools, i.get('empty_weight')) for i in items) / 1000.0
                    stats_text = f"Spulen: {total_spools}   |   Bestand: {total_net_weight_kg:.2f} kg"
                    d.text((2380, 120), stats_text, fill="#555555", font=font_subtitle, anchor="rt")
                    
                    d.rectangle([100, 190, 2380, 196], fill="#0078d7")
                    
                    filter_text = f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    active_filters = []
                    if self.filter_mat_var.get() != "Alle Materialien": active_filters.append(self.filter_mat_var.get())
                    if self.filter_color_var.get() != "Alle Farben": active_filters.append(self.filter_color_var.get())
                    if self.filter_loc_var.get() != "Alle Orte": active_filters.append(self.filter_loc_var.get())
                    if self.filter_brand_var.get() != "Alle Hersteller": active_filters.append(self.filter_brand_var.get())
                    if self.search_var.get().strip(): active_filters.append(f"Suche: '{self.search_var.get().strip()}'")
                    
                    if active_filters:
                        filter_text += f"   |   Filter: {', '.join(active_filters)}"
                    d.text((100, 220), filter_text, fill="#777777", font=font_subtitle)
                    
                    header_y = 300
                else:
                    d.text((100, 80), "VibeSpool Filament-Bestand", fill="#333333", font=font_subtitle)
                    d.text((2380, 80), f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}", fill="#777777", font=font_subtitle, anchor="rt")
                    d.line([100, 140, 2380, 140], fill="#e0e0e0", width=2)
                    header_y = 160
                    
                d.rectangle([100, header_y, 2380, header_y + 80], fill="#0078d7")
                
                th_y = header_y + 20
                d.text((175, th_y), "ID", fill="white", font=font_header, anchor="mt")
                d.text((270, th_y), "Hersteller", fill="white", font=font_header, anchor="lt")
                d.text((770, th_y), "Material", fill="white", font=font_header, anchor="lt")
                d.text((1070, th_y), "Farbe", fill="white", font=font_header, anchor="lt")
                d.text((1670, th_y), "Spulentyp", fill="white", font=font_header, anchor="lt")
                d.text((2360, th_y), "Gewicht (Netto)", fill="white", font=font_header, anchor="rt")
                
                return pg, d, header_y + 80

            pg, d, page_y = start_new_page(is_first=True)
            
            for idx, item in enumerate(items):
                if page_y + 80 > 3300:
                    pages.append(pg)
                    pg, d, page_y = start_new_page(is_first=False)
                
                if idx % 2 == 1:
                    d.rectangle([100, page_y, 2380, page_y + 80], fill="#f8fafc")
                    
                d.line([100, page_y + 80, 2380, page_y + 80], fill="#e2e8f0", width=1)
                
                d.text((175, page_y + 20), str(item['id']), fill="#334155", font=font_body_bold, anchor="mt")
                d.text((270, page_y + 20), item.get('brand', '-'), fill="#1e293b", font=font_body, anchor="lt")
                
                mat = item.get('material', '-')
                subtype = item.get('subtype', 'Standard')
                mat_display = f"{mat} ({subtype})" if subtype and subtype != "Standard" else mat
                d.text((770, page_y + 20), mat_display, fill="#1e293b", font=font_body, anchor="lt")
                
                display_color = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', '')).strip()
                cols = get_colors_from_text(item.get('color', ''), self.settings.get('colors') if hasattr(self, 'settings') else None)
                draw_color_swatch(d, 1070, page_y + 20, cols)
                d.text((1150, page_y + 20), display_color, fill="#1e293b", font=font_body, anchor="lt")
                
                sp_id = item.get('spool_id', -1)
                empty_weight = item.get('empty_weight')
                sp_preset = next((s for s in self.spools if s['id'] == sp_id), None)
                if sp_preset:
                    spool_name = f"{sp_preset.get('name', 'Standard')} ({sp_preset.get('weight', 0)}g)"
                elif empty_weight is not None:
                    spool_name = f"Custom ({empty_weight}g)"
                else:
                    spool_name = "-"
                d.text((1670, page_y + 20), spool_name, fill="#475569", font=font_body, anchor="lt")
                
                net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools, item.get('empty_weight'))
                capacity = float(item.get('capacity', 1000))
                pct = int(round((net / capacity) * 100)) if capacity > 0 else 0
                weight_text = f"{net}g ({pct}%)"
                d.text((2360, page_y + 20), weight_text, fill="#1e293b", font=font_body_bold, anchor="rt")
                
                page_y += 80
                
            pages.append(pg)
            
            total_pages = len(pages)
            for p_idx, page in enumerate(pages):
                p_draw = ImageDraw.Draw(page)
                footer_text = f"Seite {p_idx + 1} von {total_pages}   |   Erstellt mit VibeSpool"
                p_draw.text((1240, 3400), footer_text, fill="#94a3b8", font=font_footer, anchor="mt")
                
            pages[0].save(fp, "PDF", resolution=300.0, save_all=True, append_images=pages[1:])
            
            if messagebox.askyesno("Export erfolgreich", f"Die PDF-Datei wurde erfolgreich gespeichert unter:\n{fp}\n\nMöchtest du die Datei jetzt öffnen?", parent=self.root):
                try:
                    os.startfile(fp)
                except Exception as ex:
                    messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden:\n{ex}", parent=self.root)
                    
        except Exception as e:
            messagebox.showerror("Fehler beim PDF-Export", f"Es gab ein Problem beim Generieren der PDF-Datei:\n{e}", parent=self.root)

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

        master_frm = ttk.Frame(win)
        master_frm.pack(fill="both", expand=True)

        side_panel = ttk.Frame(master_frm, width=350, relief="solid", borderwidth=1)
        side_panel.pack_propagate(False)

        main_content = ttk.Frame(master_frm)
        main_content.pack(side="left", fill="both", expand=True)

        ttk.Label(main_content, text=f"📜 Historie für Spule #{item.get('id')}", font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))
        ttk.Label(main_content, text=f"{item.get('brand')} {color_clean} | {item.get('material')}", foreground="gray").pack(pady=(0, 10))

        history = item.get("history", [])

        # Wenn die Spule noch brandneu ist und keine Einträge hat
        if not history:
            ttk.Label(main_content, text="Bisher keine Einträge vorhanden.\n\nVerbräuche durch Cloud-Sync oder die Waage\nwerden hier automatisch protokolliert.", justify="center", foreground="gray").pack(expand=True)
            ttk.Button(main_content, text="Schließen", command=win.destroy).pack(pady=15)
            return

        # Tabelle für die Historie (NEU: 5 Spalten)
        columns = ("date", "action", "change", "cost", "sell")
        h_tree = ttk.Treeview(main_content, columns=columns, show="headings", height=10)
        h_tree.heading("date", text="Datum & Zeit")
        h_tree.heading("action", text="Aktion / Druck")
        h_tree.heading("change", text="Verbrauch")
        h_tree.heading("cost", text="Kosten")
        h_tree.heading("sell", text="VK-Preis")

        h_tree.column("date", width=110)
        h_tree.column("action", width=180)
        h_tree.column("change", width=70, anchor="e")
        h_tree.column("cost", width=70, anchor="e")
        h_tree.column("sell", width=70, anchor="e")

        def populate_tree():
            h_tree.delete(*h_tree.get_children())
            for idx, entry in enumerate(item.get("history", [])):
                h_tree.insert("", 0, iid=str(idx), values=(
                    entry.get("date", ""),
                    entry.get("action", ""),
                    entry.get("change", ""),
                    entry.get("cost", "-"),
                    entry.get("sell_price", "-")
                ))

        populate_tree()
        h_tree.pack(fill="both", expand=True, padx=15, pady=5)
        
        btn_close_frm = ttk.Frame(main_content, padding=5)
        btn_close_frm.pack(fill="x", side="bottom")
        ttk.Button(btn_close_frm, text="Schließen", command=win.destroy).pack(side="right", padx=10, pady=5)

        def on_double_click(event):
            sel = h_tree.selection()
            if not sel: return
            hist_idx = int(sel[0])
            self.open_history_edit_panel(win, side_panel, main_content, item, hist_idx, populate_tree)

        h_tree.bind("<Double-1>", on_double_click)

    def open_history_edit_panel(self, win, side_panel, main_content, spool, hist_idx, refresh_callback):
        for w in side_panel.winfo_children():
            w.destroy()

        side_panel.pack(side="right", fill="y", before=main_content)
        win.geometry("900x400")

        history = spool.get("history", [])
        if hist_idx >= len(history): return
        entry = history[hist_idx]

        header = ttk.Frame(side_panel)
        header.pack(fill="x", pady=10, padx=10)
        ttk.Label(header, text="✏️ Eintrag bearbeiten", font=("Segoe UI", 11, "bold")).pack(side="left")
        
        def close_panel():
            side_panel.pack_forget()
            win.geometry("550x400")

        ttk.Button(header, text="❌", width=3, command=close_panel).pack(side="right")
        ttk.Separator(side_panel, orient="horizontal").pack(fill="x")

        frm = ttk.Frame(side_panel, padding=10)
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

        ttk.Button(frm_cost, text="🧮 Mat.", width=8, command=calc_cost).pack(side="left", padx=(0, 5))
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
                margin = int(self.settings.get("profit_margin", 0))
                vk_val = cost_val * (1 + (margin / 100.0))
                ent_sell.delete(0, tk.END)
                ent_sell.insert(0, f"{vk_val:.2f} €")
                if margin == 0:
                    messagebox.showinfo("Info", "Gewinnmarge ist 0%. VK = Kosten.", parent=win)
            except ValueError:
                messagebox.showerror("Fehler", "Bitte Kosten eintragen!", parent=win)

        ttk.Button(frm_sell, text="🧮 Marge", width=8, command=calc_vk).pack(side="left", padx=(0, 5))
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
            
            date_str = entry.get("date", "").split(" ")[0]
            if not date_str: date_str = datetime.today().strftime("%Y-%m-%d")
                        
            data_dir = getattr(self.data_manager, 'base_dir', '')
            history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
            hist_data = {}
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r") as f: hist_data = json.load(f)
                except: pass
                
            if delta != 0.0:
                current_day_total = hist_data.get(date_str, 0.0)
                new_day_total = max(0.0, current_day_total - delta)
                hist_data[date_str] = round(new_day_total, 1)
            
                try:
                    with open(history_file, "w") as f: json.dump(hist_data, f, indent=4)
                except: pass
            
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            refresh_callback()
            close_panel()

        def delete():
            if messagebox.askyesno("Löschen", "Wirklich löschen?", parent=win):
                old_val_str = entry.get("change", "0").replace("g", "").replace(" ", "").replace(",", ".")
                try: old_val = float(old_val_str)
                except: old_val = 0.0
                
                curr_gross = float(spool.get('weight_gross', 0))
                spool['weight_gross'] = round(max(0.0, curr_gross - old_val), 1)
                
                date_str = entry.get("date", "").split(" ")[0]
                if not date_str: date_str = datetime.today().strftime("%Y-%m-%d")
                
                data_dir = getattr(self.data_manager, 'base_dir', '')
                history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
                hist_data = {}
                if os.path.exists(history_file):
                    try:
                        with open(history_file, "r") as f: hist_data = json.load(f)
                    except: pass
                
                if old_val != 0.0:
                    current_day_total = hist_data.get(date_str, 0.0)
                    new_day_total = max(0.0, current_day_total + old_val)
                    hist_data[date_str] = round(new_day_total, 1)
                    
                    try:
                        with open(history_file, "w") as f: json.dump(hist_data, f, indent=4)
                    except: pass

                del spool["history"][hist_idx]
                
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                refresh_callback()
                close_panel()

        btn_frm_action = ttk.Frame(side_panel)
        btn_frm_action.pack(fill="x", pady=10, padx=10, side="bottom")
        ttk.Button(btn_frm_action, text="🗑️", command=delete, style="Delete.TButton", width=3).pack(side="left", padx=5)
        ttk.Button(btn_frm_action, text="💾 Speichern", command=save, style="Accent.TButton").pack(side="right", padx=5)
    
    
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
        
        from datetime import datetime
        job_date_str = job.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        job_day = job_date_str.split(" ")[0] 
        
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

        model = job.get('name', 'Unbekannt')
        total_weight = job.get('weight', 0.0)
        mappings = job.get('mapping', [])

        ttk.Label(content_frm, text=f"{model}", font=("Segoe UI", 11, "bold"), wraplength=400, justify="center").pack(pady=(5, 5))
        
        # Drucker anhand deviceId ermitteln
        job_dev_id = job.get("deviceId", "")
        printers = self.settings.get("printers", [])
        printer = next((p for p in printers if p.get("serial") == job_dev_id), None)
        ams_ids = printer.get("ams_ids", []) if printer else []
        ext_loc = printer.get("external_loc", "") if printer else ""

        try: duration = float(job.get('duration_h', 0.0) or 0.0)
        except: duration = 0.0
        
        kwh_price = float(self.settings.get("kwh_price", 0.30))
        
        # Drucker-spezifische Werte mit globalem Fallback
        watts = 150
        if printer and printer.get("printer_watts") not in (None, ""):
            try: watts = int(printer.get("printer_watts"))
            except: pass
        else:
            watts = int(self.settings.get("printer_watts", 150))
            
        wear_price = 0.20
        if printer and printer.get("wear_per_hour") not in (None, ""):
            try: wear_price = float(printer.get("wear_per_hour"))
            except: pass
        else:
            wear_price = float(self.settings.get("wear_per_hour", 0.20))
            
        strom_kosten = duration * (watts / 1000.0) * kwh_price
        
        info_str = f"Verbrauch: {total_weight}g"
        if duration > 0: info_str += f"\nZeit: {duration:.1f}h | Strom: {strom_kosten:.2f} €"
        ttk.Label(content_frm, text=info_str, font=("Segoe UI", 9), foreground="#0078D7", justify="center").pack(pady=5)

        from core.logic import calculate_net_weight
        spool_list = []
        for s in self.inventory:
            if s.get('type') == 'VERBRAUCHT': continue
            net = calculate_net_weight(s.get('weight_gross', '0'), s.get('spool_id', -1), self.spools, s.get('empty_weight'))
            import re
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
            
            if raw_ams >= 0 and raw_ams != 255:
                local_ams_idx = raw_ams // 4
                if printer and local_ams_idx < len(ams_ids):
                    global_ams_id = ams_ids[local_ams_idx]
                else:
                    global_ams_id = local_ams_idx + 1
                slot_num = (raw_ams % 4) + 1
                ams_name = f"AMS {global_ams_id}"
                lbl_text = f"{ams_name} Slot {slot_num}:"
                
                # --- NEU: DIE ZEITMASCHINE (SMART AMS MEMORY) ---
                import os, json
                snap_file = os.path.join(getattr(self.data_manager, 'base_dir', ''), "ams_snapshots.json")
                if os.path.exists(snap_file):
                    try:
                        with open(snap_file, "r") as f:
                            snaps = json.load(f)
                            
                        try: job_dt = datetime.strptime(job_date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            try: job_dt = datetime.strptime(job_date_str, "%Y-%m-%d %H:%M")
                            except: job_dt = datetime.now()
                            
                        closest_key = None
                        min_diff = None
                        
                        # Wir suchen exakt das Beweisfoto, das am nächsten am Druck-Datum dran ist!
                        for snap_time_str, snap_data in snaps.items():
                            try:
                                snap_dt = datetime.strptime(snap_time_str, "%Y-%m-%d %H:%M:%S")
                                diff = abs((job_dt - snap_dt).total_seconds())
                                if min_diff is None or diff < min_diff:
                                    min_diff = diff
                                    closest_key = snap_time_str
                            except: pass
                            
                        if closest_key:
                            target_key = f"{ams_name}_{slot_num}"
                            spool_id = snaps[closest_key].get(target_key)
                            if spool_id:
                                best_match = next((s for s in self.inventory if str(s.get('id')) == spool_id), None)
                    except: pass
                
                # Fallback: Wenn es keinen Snapshot gibt (oder er gelöscht wurde), nehmen wir das, was JETZT im AMS ist
                if not best_match:
                    best_match = next((s for s in self.inventory if s.get('type') == ams_name and str(s.get('loc_id')) == str(slot_num)), None)
                # --- ENDE ZEITMASCHINE ---
            else:
                lbl_text = f"Extern ({ext_loc}):" if ext_loc else "Extern/Spule:"
                if ext_loc:
                    best_match = next((s for s in self.inventory if s.get('type') == ext_loc and s.get('type') != 'VERBRAUCHT'), None)

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
                        
                        echte_kosten = mat_cost + (strom_kosten * anteil) + ((duration * wear_price) * anteil)
                        margin_percent = int(self.settings.get("profit_margin", 0))
                        vk_preis = echte_kosten * (1 + (margin_percent / 100.0))

                        if "history" not in item: item["history"] = []
                        item["history"].append({
                            "date": job_date_str,
                            "action": f"Cloud: {model}",
                            "change": f"-{w_val}g",
                            "cost": f"{echte_kosten:.2f} €",
                            "sell_price": f"{vk_preis:.2f} €" if margin_percent > 0 else "-"
                        })
                        total_deducted += w_val

            if total_deducted > 0:
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
                
                if hasattr(self, "show_custom_toast"):
                    self.show_custom_toast("💰 Filament verrechnet", f"Verbrauch: {total_deducted:.1f}g\nGesamtkosten: {mat_cost + (strom_kosten * anteil) + ((duration * wear_price) * anteil):.2f} €")
            else:
                from tkinter import messagebox
                messagebox.showerror("Fehler", "Es wurden keine gültigen Gewichte eingetragen.", parent=parent_win)

        ttk.Button(content_frm, text="✅ Jetzt Abziehen", style="Accent.TButton", command=confirm).pack(side="bottom", pady=15)


    def _build_cloud_deduction_ui(self, content, job, parent_win, tree_widget, refresh_tree=None):

        model = job['name']
        total_weight = job['weight']
        mappings = job.get('mapping', [])
        job_id = str(job.get('id', ''))

        # Drucker anhand deviceId ermitteln
        job_dev_id = job.get("deviceId", "")
        printers = self.settings.get("printers", [])
        printer = next((p for p in printers if p.get("serial") == job_dev_id), None)
        ams_ids = printer.get("ams_ids", []) if printer else []
        ext_loc = printer.get("external_loc", "") if printer else ""

        ttk.Label(content, text=f"Druck: {model}", font=("Segoe UI", 12, "bold"), wraplength=350, justify="center").pack(pady=(10, 5))
        
        # --- NEU: Stromkosten berechnen ---
        duration = job.get('duration_h', 0.0)
        kwh_price = float(self.settings.get("kwh_price", 0.30))
        
        # Drucker-spezifische Werte mit globalem Fallback
        watts = 150
        if printer and printer.get("printer_watts") not in (None, ""):
            try: watts = int(printer.get("printer_watts"))
            except: pass
        else:
            watts = int(self.settings.get("printer_watts", 150))
            
        wear_price = 0.20
        if printer and printer.get("wear_per_hour") not in (None, ""):
            try: wear_price = float(printer.get("wear_per_hour"))
            except: pass
        else:
            wear_price = float(self.settings.get("wear_per_hour", 0.20))
            
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
            
            if raw_ams >= 0 and raw_ams != 255:
                local_ams_idx = raw_ams // 4
                if printer and local_ams_idx < len(ams_ids):
                    global_ams_id = ams_ids[local_ams_idx]
                else:
                    global_ams_id = local_ams_idx + 1
                slot_num = (raw_ams % 4) + 1
                ams_name = f"AMS {global_ams_id}"
                lbl_text = f"{ams_name} Slot {slot_num}:"
                
                # Wir suchen direkt, was aktuell in VibeSpool auf diesem Slot liegt!
                best_match = next((s for s in self.inventory if s.get('type') == ams_name and str(s.get('loc_id')) == str(slot_num)), None)
            else:
                lbl_text = f"Extern ({ext_loc}):" if ext_loc else "Extern/Spule:"
                if ext_loc:
                    best_match = next((s for s in self.inventory if s.get('type') == ext_loc and s.get('type') != 'VERBRAUCHT'), None)

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
                gesamt_kosten = mat_cost + (strom_kosten * anteil) + ((duration * wear_price) * anteil)
                self.show_custom_toast("💰 Filament verrechnet", f"Verbrauch: {total_deducted:.1f}g\nGesamtkosten (Material + Strom + Verschleiß): {gesamt_kosten:.2f} €")
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
