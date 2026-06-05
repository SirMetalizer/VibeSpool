import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
import os
import sys
import socket
import re

# --- MODULE IMPORT ---
from core.data_manager import DataManager
from core.utils import center_window
from core.spool_presets import SPOOL_PRESETS
from core.logic import calculate_net_weight, check_for_updates, parse_shelves_string, serialize_shelves
from core.label_creator import LabelCreatorDialog
from core.print_queue import PrintQueueDialog

# --- KONFIGURATION ---
APP_VERSION = "2.1.0-Beta (UI Overhaul)"
GITHUB_REPO = "SirMetalizer/VibeSpool" 

# --- DEFAULTS ---
DEFAULT_SETTINGS = {
    "shelves": "REGAL|4|8", 
    "logistics_order": False,
    "label_row": "Fach",
    "label_col": "Slot",
    "num_ams": 1,
    "custom_locs": "Filamenttrockner",
    "theme": "dark",
    "materials": ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF", "PVA", "Sonstiges"],
    "subtypes": ["Standard", "Matte", "Silk", "High Speed", "Dual Color", "Tri Color", "Glow in Dark", "Transparent", "Translucent", "Marmor", "Holz", "Glitzer/Sparkle"],
    "colors": ["Black", "White", "Grey", "Silver", "Ash Gray", "Red", "Maroon Red", "Blue", "Light Blue", "Navy", "Green", "Dark Green", "Mint", "Olive", "Yellow", "Orange", "Terracotta", "Purple", "Plum", "Lavender", "Pink", "Magenta", "Brown", "Beige", "Turquoise", "Cyan", "Gold", "Copper", "Bronze", "Rainbow", "Marble", "Wood"],
    "brands": ["Bambu", "eSun", "Geeetech", "Sunlu", "Polymaker", "Prusa", "Eryone"],
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

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, on_save, start_tab="📦 Lager", app_instance=None):
        super().__init__(master=parent)
        self.data_manager = data_manager
        self.on_save = on_save
        self.app = app_instance
        _, self.settings, _ = self.data_manager.load_all(DEFAULT_SETTINGS)
        
        self.title("⚙️ VibeSpool Einstellungen")
        self.geometry("1050x700") # Etwas breiter für die neue Optik
        self.transient(parent)
        self.grab_set()
        center_window(self, parent)

        # --- HAUPT-LAYOUT (Ersatz für PanedWindow) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Linke Seite: Das Tab-Menü
        self.notebook_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.notebook_frame.pack(side="left", fill="both", expand=True)

        footer_frm = ctk.CTkFrame(self.notebook_frame, fg_color="transparent")
        footer_frm.pack(side="bottom", fill="x", pady=10, padx=10)
        ctk.CTkButton(footer_frm, text="Abbrechen", fg_color="transparent", border_width=1, command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(footer_frm, text="💾 Änderungen Speichern", font=ctk.CTkFont(weight="bold"), command=self.do_save).pack(side="right", padx=5)

        # Das CTkTabview (Ersatz für ttk.Notebook)
        self.nb = ctk.CTkTabview(self.notebook_frame, command=lambda: self.toggle_side_panel(force_close=True))
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Rechte Seite: Das Side-Panel (Initial versteckt)
        self.side_panel = ctk.CTkFrame(self.main_container, width=350, corner_radius=0, fg_color="#1e1e1e", border_width=1, border_color="#333333")
        self.side_panel.pack_propagate(False)
        self.side_panel_open = False
        self.current_side_title = ""
        
        # ==========================================
        # TAB 1: LAGER
        # ==========================================
        tab_lager = self.nb.add("📦 Lager")
        
        ctk.CTkLabel(tab_lager, text="Regal-Konfiguration", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        self.var_shelves = tk.StringVar(value=self.settings.get("shelves", "REGAL|4|8"))
        
        self.shelf_list = tk.Listbox(tab_lager, height=6, font=("Segoe UI", 10), bg="#2b2b2b", fg="#e0e0e0", selectbackground="#1f538d", borderwidth=1, relief="solid")
        self.shelf_list.pack(fill="x", padx=10, pady=5)
        # HINWEIS: self.refresh_settings_shelf_list() muss in den folgenden Blöcken noch von dir geliefert werden!
        if hasattr(self, 'refresh_settings_shelf_list'): self.refresh_settings_shelf_list() 
        
        def on_shelf_list_select(event):
            if self.side_panel_open:
                title = self.current_side_title
                self.current_side_title = "" 
                if title == "Regal-Konfigurator": self.toggle_side_panel(title, self.build_shelf_planner_ui)
                elif title == "Fächer individuell benennen": self.toggle_side_panel(title, self.build_shelf_names_ui)
                    
        self.shelf_list.bind("<<ListboxSelect>>", on_shelf_list_select)

        btn_frm_lager = ctk.CTkFrame(tab_lager, fg_color="transparent")
        btn_frm_lager.pack(fill="x", padx=10, pady=5)
        
        def delete_selected_shelf():
            sel = self.shelf_list.curselection()
            if not sel:
                messagebox.showinfo("Info", "Bitte wähle erst ein Regal aus der Liste aus!", parent=self)
                return
            if messagebox.askyesno("Löschen", "Soll dieses Regal wirklich gelöscht werden?", parent=self):
                from core.logic import parse_shelves_string, serialize_shelves
                current_shelves = parse_shelves_string(self.var_shelves.get())
                del current_shelves[sel[0]]
                self.var_shelves.set(serialize_shelves(current_shelves))
                if hasattr(self, 'refresh_settings_shelf_list'): self.refresh_settings_shelf_list()

        ctk.CTkButton(btn_frm_lager, text="🗑️ Löschen", fg_color="#8b0000", hover_color="#5c0000", command=delete_selected_shelf).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frm_lager, text="➕ Neu / Ändern", command=lambda: self.toggle_side_panel("Regal-Konfigurator", self.build_shelf_planner_ui)).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkButton(btn_frm_lager, text="🏷️ Fächer benennen", command=lambda: self.toggle_side_panel("Fächer individuell benennen", self.build_shelf_names_ui)).pack(side="left", fill="x", expand=True, padx=(2, 0))

        f_names = ctk.CTkFrame(tab_lager, fg_color="transparent")
        f_names.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(f_names, text="Reihen-Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_row = ctk.CTkEntry(f_names, width=150)
        self.ent_row.insert(0, self.settings.get("label_row", "Fach"))
        self.ent_row.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        ctk.CTkLabel(f_names, text="Spalten-Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_col = ctk.CTkEntry(f_names, width=150)
        self.ent_col.insert(0, self.settings.get("label_col", "Slot"))
        self.ent_col.grid(row=1, column=1, sticky="w", pady=5, padx=10)

        ctk.CTkLabel(tab_lager, text="Zusatz-Orte (kommagetrennt, z.B. Trockenbox, Verliehen):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(15, 5))
        self.ent_custom = ctk.CTkEntry(tab_lager)
        self.ent_custom.insert(0, self.settings.get("custom_locs", "Filamenttrockner"))
        self.ent_custom.pack(fill="x", padx=10, pady=2)
        
        self.var_logistics = tk.BooleanVar(value=self.settings.get("logistics_order", False))
        self.var_double = tk.BooleanVar(value=self.settings.get("double_depth", False))
        ctk.CTkCheckBox(tab_lager, text="Logistik-Modus (unten = Reihe 1)", variable=self.var_logistics).pack(anchor="w", padx=10, pady=(15, 5))
        ctk.CTkCheckBox(tab_lager, text="Doppeltiefe Regale (2 Rollen pro Slot)", variable=self.var_double).pack(anchor="w", padx=10, pady=5)

        # ==========================================
        # TAB 2: DRUCKER
        # ==========================================
        tab_prn = self.nb.add("🤖 Drucker")
        
        ctk.CTkLabel(tab_prn, text="Klipper / Moonraker", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        self.var_moonraker = tk.BooleanVar(value=self.settings.get("use_moonraker", False))
        ctk.CTkCheckBox(tab_prn, text="Moonraker-Sync im Hauptfenster anzeigen", variable=self.var_moonraker).pack(anchor="w", padx=10, pady=10)
        self.ent_prn_url = ctk.CTkEntry(tab_prn, placeholder_text="Drucker URL / IP")
        self.ent_prn_url.insert(0, self.settings.get("printer_url", ""))
        self.ent_prn_url.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(tab_prn, text="Bambu Lab AMS (via MQTT)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(25,0))
        ctk.CTkLabel(tab_prn, text="Anzahl AMS Einheiten:").pack(anchor="w", padx=10, pady=(10,0))
        self.ent_ams = ctk.CTkEntry(tab_prn, width=100)
        self.ent_ams.insert(0, str(self.settings.get("num_ams", 1)))
        self.ent_ams.pack(anchor="w", padx=10, pady=2)
        
        self.var_bambu = tk.BooleanVar(value=self.settings.get("use_bambu", False))
        ctk.CTkCheckBox(tab_prn, text="Bambu AMS Live-Sync aktivieren", variable=self.var_bambu).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.ent_bambu_ip = ctk.CTkEntry(tab_prn, placeholder_text="Drucker IP-Adresse")
        self.ent_bambu_ip.insert(0, self.settings.get("bambu_ip", ""))
        self.ent_bambu_ip.pack(fill="x", padx=10, pady=5)
        self.ent_bambu_acc = ctk.CTkEntry(tab_prn, placeholder_text="Access Code (LAN)")
        self.ent_bambu_acc.insert(0, self.settings.get("bambu_access", ""))
        self.ent_bambu_acc.pack(fill="x", padx=10, pady=5)
        self.ent_bambu_ser = ctk.CTkEntry(tab_prn, placeholder_text="Seriennummer")
        self.ent_bambu_ser.insert(0, self.settings.get("bambu_serial", ""))
        self.ent_bambu_ser.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(tab_prn, text="Bambu Lab Cloud API", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(25,0))
        self.var_cloud = tk.BooleanVar(value=self.settings.get("use_bambu_cloud", True))
        ctk.CTkCheckBox(tab_prn, text="Cloud-Historie & Smart-Match aktivieren", variable=self.var_cloud).pack(anchor="w", padx=10, pady=10)

        # ==========================================
        # TAB 3: DRUCKKOSTEN
        # ==========================================
        tab_fin = self.nb.add("💰 Druckkosten")
        ctk.CTkLabel(tab_fin, text="Druckkosten & Gewerbe-Kalkulation", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(5, 10))
        ctk.CTkLabel(tab_fin, text="VibeSpool nutzt diese Werte, um bei jedem Druck die exakten Gesamtkosten (Material + Strom + Verschleiß) zu berechnen.", text_color="gray", wraplength=450, justify="left").pack(anchor="w", padx=10, pady=(0, 15))

        frm_calc = ctk.CTkFrame(tab_fin, fg_color="transparent")
        frm_calc.pack(fill="x", padx=10)

        ctk.CTkLabel(frm_calc, text="Strompreis pro kWh (€):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_kwh = ctk.CTkEntry(frm_calc, width=150)
        self.ent_kwh.insert(0, str(self.settings.get("kwh_price", "0.30")))
        self.ent_kwh.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(frm_calc, text="Drucker-Stromverbrauch (Watt):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_watts = ctk.CTkEntry(frm_calc, width=150)
        self.ent_watts.insert(0, str(self.settings.get("printer_watts", "150")))
        self.ent_watts.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(frm_calc, text="Richtwerte: Bambu A1 Mini ~80W | A1 ~100W | P1S/X1C ~250W", text_color="gray", font=ctk.CTkFont(size=11)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 20))

        ctk.CTkLabel(frm_calc, text="Maschinenverschleiß pro Stunde (€):").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_wear = ctk.CTkEntry(frm_calc, width=150)
        self.ent_wear.insert(0, str(self.settings.get("wear_per_hour", "0.20")))
        self.ent_wear.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(frm_calc, text="Gewinnmarge / Aufschlag (%):").grid(row=5, column=0, sticky="w", pady=5)
        self.ent_margin = ctk.CTkEntry(frm_calc, width=150)
        self.ent_margin.insert(0, str(self.settings.get("profit_margin", "0")))
        self.ent_margin.grid(row=5, column=1, sticky="w", padx=10, pady=5)

        # ==========================================
        # TAB 4: SYSTEM
        # ==========================================
        tab_sys = self.nb.add("⚙ System")
        self.var_affiliate = tk.BooleanVar(value=self.settings.get("use_affiliate", True))
        self.var_rfid = tk.BooleanVar(value=self.settings.get("rfid_mode", False))
        ctk.CTkCheckBox(tab_sys, text="Entwickler unterstützen (Affiliate)", variable=self.var_affiliate).pack(anchor="w", padx=10, pady=(5,5))
        ctk.CTkCheckBox(tab_sys, text="RFID-Reader Modus aktiv", variable=self.var_rfid).pack(anchor="w", padx=10, pady=5)
        
        import os
        default_path = getattr(self.data_manager, 'base_dir', os.getcwd())
        custom_path = self.settings.get("custom_db_path", "")
        path_show = custom_path if custom_path else f"{default_path} (Standard)"
        
        self.lbl_path = ctk.CTkLabel(tab_sys, text=f"Daten-Pfad:\n{path_show}", font=ctk.CTkFont(slant="italic"), text_color="#1f6aa5", wraplength=450, justify="left")
        self.lbl_path.pack(fill="x", padx=10, pady=(20, 5))
        
        p_btn_frm = ctk.CTkFrame(tab_sys, fg_color="transparent")
        p_btn_frm.pack(fill="x", padx=10, pady=5)
        
        def change_path():
            d = filedialog.askdirectory(title="Datenbank-Ordner wählen")
            if d: 
                self.settings["custom_db_path"] = d
                self.lbl_path.configure(text=f"Daten-Pfad:\n{d}")
                
        def set_standard():
            self.settings["custom_db_path"] = ""
            self.lbl_path.configure(text=f"Daten-Pfad:\n{default_path} (Standard)")
            
        ctk.CTkButton(p_btn_frm, text="Ordner ändern", command=change_path).pack(side="left", padx=(0, 5))
        ctk.CTkButton(p_btn_frm, text="Standard", fg_color="transparent", border_width=1, command=set_standard).pack(side="left")

        ctk.CTkLabel(tab_sys, text="🏡 Smart Home / Home Assistant", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(30, 5))
        self.var_mqtt = tk.BooleanVar(value=self.settings.get("mqtt_enable", False))
        
        frm_mqtt = ctk.CTkFrame(tab_sys, fg_color="transparent")
        def toggle_mqtt():
            if self.var_mqtt.get(): frm_mqtt.pack(fill="x", padx=10, pady=5)
            else: frm_mqtt.pack_forget()
            
        ctk.CTkCheckBox(tab_sys, text="MQTT Broadcasting aktivieren", variable=self.var_mqtt, command=toggle_mqtt).pack(anchor="w", padx=10, pady=5)
        
        ctk.CTkLabel(frm_mqtt, text="Broker IP / Host:").grid(row=0, column=0, sticky="w", pady=2)
        self.ent_mqtt_host = ctk.CTkEntry(frm_mqtt, width=200); self.ent_mqtt_host.insert(0, self.settings.get("mqtt_host", "")); self.ent_mqtt_host.grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkLabel(frm_mqtt, text="Port:").grid(row=1, column=0, sticky="w", pady=2)
        self.ent_mqtt_port = ctk.CTkEntry(frm_mqtt, width=80); self.ent_mqtt_port.insert(0, self.settings.get("mqtt_port", "1883")); self.ent_mqtt_port.grid(row=1, column=1, sticky="w", padx=10)
        ctk.CTkLabel(frm_mqtt, text="Benutzer:").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_mqtt_user = ctk.CTkEntry(frm_mqtt, width=200); self.ent_mqtt_user.insert(0, self.settings.get("mqtt_user", "")); self.ent_mqtt_user.grid(row=2, column=1, sticky="w", padx=10)
        ctk.CTkLabel(frm_mqtt, text="Passwort:").grid(row=3, column=0, sticky="w", pady=2)
        self.ent_mqtt_pass = ctk.CTkEntry(frm_mqtt, width=200, show="*"); self.ent_mqtt_pass.insert(0, self.settings.get("mqtt_pass", "")); self.ent_mqtt_pass.grid(row=3, column=1, sticky="w", padx=10)
        if self.var_mqtt.get(): frm_mqtt.pack(fill="x", padx=10, pady=5)

        # ==========================================
        # TAB 5: LISTEN
        # ==========================================
        tab_lists = self.nb.add("📋 Listen")
        ctk.CTkLabel(tab_lists, text="Eigene Dropdown-Listen verwalten", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 10))
        list_container = ctk.CTkFrame(tab_lists, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=5)

        self.list_vars = {}
        def create_list_manager(parent, title, key, default_list):
            frm = ctk.CTkFrame(parent, corner_radius=8)
            frm.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(frm, text=title, font=ctk.CTkFont(weight="bold")).pack(pady=5)
            
            lb = tk.Listbox(frm, height=12, font=("Segoe UI", 10), selectmode=tk.SINGLE, cursor="hand2", bg="#2b2b2b", fg="#e0e0e0", selectbackground="#1f538d", borderwidth=0, highlightthickness=0)
            lb.pack(fill="both", expand=True, padx=10, pady=5)
            
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
            
            current_data = self.settings.get(key, default_list)
            self.list_vars[key] = current_data.copy()
            for item in self.list_vars[key]: lb.insert(tk.END, item)
            
            input_frm = ctk.CTkFrame(frm, fg_color="transparent")
            input_frm.pack(fill="x", padx=10, pady=5)
            ent_new = ctk.CTkEntry(input_frm)
            ent_new.pack(side="left", fill="x", expand=True)
            
            if key == "colors":
                def pick_list_color():
                    color_code = colorchooser.askcolor(title="Farbe für Liste wählen", parent=self)[1]
                    if color_code:
                        current_text = re.sub(r'\s*\(?#[0-9a-fA-F]{6}\)?', '', ent_new.get().strip()).strip()
                        ent_new.delete(0, tk.END)
                        ent_new.insert(0, f"{current_text} ({color_code.upper()})" if current_text else color_code.upper())
                ctk.CTkButton(input_frm, text="🎨", width=30, command=pick_list_color).pack(side="left", padx=(5, 0))
            
            btn_frm = ctk.CTkFrame(frm, fg_color="transparent")
            btn_frm.pack(fill="x", padx=10, pady=(0, 10))
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
                    
            ctk.CTkButton(btn_frm, text="➕", width=30, command=add_item).pack(side="left", expand=True, fill="x", padx=(0, 2))
            ctk.CTkButton(btn_frm, text="❌", width=30, fg_color="#8b0000", hover_color="#5c0000", command=del_item).pack(side="left", expand=True, fill="x", padx=(2, 0))

        create_list_manager(list_container, "Materialien", "materials", DEFAULT_SETTINGS["materials"])
        create_list_manager(list_container, "Farben", "colors", DEFAULT_SETTINGS["colors"])
        create_list_manager(list_container, "Effekt / Typ", "subtypes", DEFAULT_SETTINGS["subtypes"])
        create_list_manager(list_container, "Hersteller", "brands", DEFAULT_SETTINGS["brands"])
        
        try: self.nb.set(start_tab)
        except: pass
    
    def toggle_side_panel(self, title=None, build_func=None, force_close=False):
        # Wenn wir schon offen sind und den GLEICHEN Titel klicken -> Schließen
        if force_close or (self.side_panel_open and self.current_side_title == title):
            self.side_panel.pack_forget()
            self.side_panel_open = False
            self.current_side_title = ""
            return

        # Ansonsten: Panel leeren und neu aufbauen
        for widget in self.side_panel.winfo_children():
            widget.destroy()

        self.side_panel.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.side_panel_open = True
        self.current_side_title = title

        # Header
        header = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        header.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(header, text=title or "", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="❌", width=30, fg_color="transparent", hover_color="#8b0000", command=lambda: self.toggle_side_panel(force_close=True)).pack(side="right")
        
        # Separator (CTk Workaround)
        ctk.CTkFrame(self.side_panel, height=2, fg_color="#333333").pack(fill="x", padx=10, pady=(0, 10))

        content = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10)
        
        if build_func:
            build_func(content)

    def build_shelf_planner_ui(self, parent):
        sel = self.shelf_list.curselection()
        from core.logic import parse_shelves_string, serialize_shelves
        current_shelves = parse_shelves_string(self.var_shelves.get())
        edit_idx = sel[0] if sel else None
        
        existing_data = current_shelves[edit_idx] if edit_idx is not None else {"name": "NEU", "rows": 4, "cols": 8}

        ctk.CTkLabel(parent, text="Regal hinzufügen oder bearbeiten:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(parent, text="Name:").pack(anchor="w")
        ent_name = ctk.CTkEntry(parent)
        ent_name.insert(0, existing_data["name"])
        ent_name.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(parent, text="Reihen (Y):").pack(anchor="w")
        ent_rows = ctk.CTkEntry(parent)
        ent_rows.insert(0, str(existing_data["rows"]))
        ent_rows.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(parent, text="Spalten (X):").pack(anchor="w")
        ent_cols = ctk.CTkEntry(parent)
        ent_cols.insert(0, str(existing_data["cols"]))
        ent_cols.pack(fill="x", pady=(0, 15))

        def save_shelf():
            try: r_val = int(ent_rows.get())
            except: r_val = 4
            try: c_val = int(ent_cols.get())
            except: c_val = 8
            
            new_shelf = {"name": ent_name.get().strip() or "Regal", "rows": r_val, "cols": c_val}
            
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
                
            self.refresh_settings_shelf_list()
            self.toggle_side_panel(force_close=True)

        ctk.CTkButton(parent, text="💾 Speichern / Übernehmen", font=ctk.CTkFont(weight="bold"), command=save_shelf).pack(fill="x")

    def build_shelf_names_ui(self, parent):
        sel = self.shelf_list.curselection()
        if not sel:
            ctk.CTkLabel(parent, text="⚠️ Bitte wähle erst links ein Regal aus!", text_color="#e74c3c", wraplength=250).pack(pady=20)
            return
            
        from core.logic import parse_shelves_string
        current_shelves = parse_shelves_string(self.var_shelves.get())
        target_shelf = current_shelves[sel[0]]
        target_name = target_shelf["name"]
        
        ctk.CTkLabel(parent, text=f"Fächer & Slots für '{target_name}':", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        sf = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        sf.pack(fill="both", expand=True, pady=10)
        
        all_custom_names = self.settings.get("shelf_names_v2", {})
        my_names = all_custom_names.get(target_name, {})
        
        app = getattr(self, 'app', None)
        
        ui_lbl_r = self.ent_row.get().strip() or "Fach"
        ui_lbl_c = self.ent_col.get().strip() or "Slot"
        
        db_lbl_r = app.settings.get('label_row', 'Fach') if app else "Fach"
        db_lbl_c = app.settings.get('label_col', 'Slot') if app else "Slot"

        # --- Reihen (Rows) ---
        ctk.CTkLabel(sf, text=f"--- {ui_lbl_r} (Reihen) ---", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 5))
        entries_r = {}
        for r in range(1, int(target_shelf["rows"]) + 1):
            row_frm = ctk.CTkFrame(sf, fg_color="transparent")
            row_frm.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frm, text=f"{ui_lbl_r} {r}:", width=80, anchor="w").pack(side="left")
            ent = ctk.CTkEntry(row_frm)
            ent.insert(0, my_names.get(str(r), f"{ui_lbl_r} {r}"))
            ent.pack(side="left", fill="x", expand=True)
            entries_r[str(r)] = ent

        # --- Spalten (Cols) ---
        ctk.CTkLabel(sf, text=f"--- {ui_lbl_c} (Spalten) ---", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        entries_c = {}
        for c in range(1, int(target_shelf["cols"]) + 1):
            row_frm = ctk.CTkFrame(sf, fg_color="transparent")
            row_frm.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frm, text=f"{ui_lbl_c} {c}:", width=80, anchor="w").pack(side="left")
            ent = ctk.CTkEntry(row_frm)
            ent.insert(0, my_names.get(f"col_{c}", f"{ui_lbl_c} {c}"))
            ent.pack(side="left", fill="x", expand=True)
            entries_c[str(c)] = ent

        def save():
            new_map = {}
            for k, v in entries_r.items(): new_map[str(k)] = v.get().strip()
            for k, v in entries_c.items(): new_map[f"col_{k}"] = v.get().strip()
            
            changes_made = 0
            
            if app is not None:
                for r in range(1, int(target_shelf["rows"]) + 1):
                    for c in range(1, int(target_shelf["cols"]) + 1):
                        old_r_val = my_names.get(str(r), f"{db_lbl_r} {r}")
                        new_r_val = new_map.get(str(r), f"{ui_lbl_r} {r}")
                        old_c_val = my_names.get(f"col_{c}", f"{db_lbl_c} {c}")
                        new_c_val = new_map.get(f"col_{c}", f"{ui_lbl_c} {c}")
                        
                        if old_r_val != new_r_val or old_c_val != new_c_val:
                            search_str = f"{old_r_val} - {old_c_val}"
                            replace_str = f"{new_r_val} - {new_c_val}"
                            
                            for item in app.inventory:
                                if item.get("type") == target_name:
                                    loc = str(item.get("loc_id", ""))
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
                
            messagebox.showinfo("Erfolg", f"Raster-Namen für '{target_name}' gespeichert!\n\n{changes_made} Spulen wurden automatisch umgebucht.", parent=self)
            self.toggle_side_panel(force_close=True)

        ctk.CTkButton(parent, text="💾 Namen übernehmen", font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x", pady=(10,0))

    def refresh_settings_shelf_list(self):
        self.shelf_list.delete(0, tk.END)
        from core.logic import parse_shelves_string
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
                
                # --- MIGRATION 0: Doppeltiefe Umschaltung ---
                old_double = self.settings.get("double_depth", False)
                new_double = self.var_double.get()
                
                if old_double != new_double:
                    for item in app_inst.inventory:
                        t = str(item.get("type", ""))
                        loc = str(item.get("loc_id", ""))
                        if t and t not in ["LAGER", "VERBRAUCHT"] and not t.startswith("AMS") and loc and loc != "-":
                            if new_double:
                                if not loc.endswith("(V)") and not loc.endswith("(H)"):
                                    item["loc_id"] = f"{loc} (V)"
                                    inventory_changed = True
                            else:
                                if loc.endswith(" (V)") or loc.endswith(" (H)"):
                                    item["loc_id"] = loc[:-4]
                                    inventory_changed = True
                
                # --- MIGRATION 1: Gelöschte Regale retten ---
                old_shelves_str = self.settings.get("shelves", "REGAL|4|8")
                from core.logic import parse_shelves_string
                old_shelf_names = [s['name'] for s in parse_shelves_string(old_shelves_str)]
                new_shelf_names = [s['name'] for s in parse_shelves_string(self.var_shelves.get())]
                
                deleted_shelves = [name for name in old_shelf_names if name not in new_shelf_names]
                moved_to_lager = 0
                
                if deleted_shelves:
                    for item in app_inst.inventory:
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

                if inventory_changed:
                    app_inst.data_manager.save_inventory(app_inst.inventory)

            
            # --- Finanzen auslesen ---
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
                "wear_per_hour": wear_val,    
                "profit_margin": margin_val,  
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
            
            # --- LIVE-UPDATE DER OBERFLÄCHE ---
            if app_inst:
                app_inst.refresh_table() 
                
                # Wenn das Cloud Feature aktiviert/deaktiviert wurde -> Button umschalten
                if hasattr(app_inst, 'btn_cloud'):
                    if self.settings.get("use_bambu_cloud", True):
                        app_inst.btn_cloud.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
                    else:
                        app_inst.btn_cloud.grid_forget()
                
            self.destroy()
            
        except ValueError: 
            messagebox.showerror("Fehler", "AMS Anzahl muss eine Zahl sein.", parent=self)
        except Exception as e:
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{e}", parent=self)



class FilamentApp:
    def __init__(self, root):
        self.root = root
        
        # --- MODERNES CTK SETUP ---
        ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
        
        self.root.title(f"VibeSpool {APP_VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- DATEN MANAGER ---
        self.data_manager = DataManager(DEFAULT_SETTINGS)
        inventory_data, settings_data, spools_data = self.data_manager.load_all(DEFAULT_SETTINGS)
        self.inventory = inventory_data if isinstance(inventory_data, list) else []
        self.settings = settings_data if isinstance(settings_data, dict) else {}
        self.spools = spools_data if isinstance(spools_data, list) else []

        # --- HAUPT-LAYOUT (Grid-System) ---
        # Das Grid-System ist in CustomTkinter viel mächtiger als .pack()
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.build_sidebar()
        self.build_main_area()

        # --- HINTERGRUND-DIENSTE STARTEN ---
        # 1. Den Handy-Webserver starten
        try:
            from core.mobile_server import start_mobile_server
            start_mobile_server(self)
        except Exception as e:
            print(f"Fehler beim Starten des Handy-Servers: {e}")

        # 2. Den lokalen Bambu-Monitor starten (MQTT)
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

    def build_sidebar(self):
        """Baut die linke, moderne Navigationsleiste."""
        self.sidebar_frame = ctk.CTkFrame(self.root, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Schiebt den unteren Bereich nach unten

        # Logo / Titel
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="VibeSpool", font=ctk.CTkFont(size=22, weight="bold"), text_color="#1f6aa5")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Helper-Funktion für moderne Buttons
        def create_nav_btn(row, text, icon=""):
            btn = ctk.CTkButton(self.sidebar_frame, text=f"{icon}  {text}", height=40, anchor="w", 
                                fg_color="transparent", text_color=("gray10", "gray90"), 
                                hover_color=("gray70", "gray30"), font=ctk.CTkFont(size=14))
            btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
            return btn

        self.btn_regal = create_nav_btn(1, "Regal", "📦")
        self.btn_regal.configure(command=self.open_regal_panel)
        
        self.btn_spools = create_nav_btn(2, "Spulen", "🧵")
        self.btn_spools.configure(command=lambda: SpoolManager(self)) # FIX: Jetzt klickbar!
        
        self.btn_labels = create_nav_btn(3, "Label", "🏷️")
        self.btn_labels.configure(command=lambda: LabelCreatorDialog(self.root, self.inventory))
        
        self.btn_finance = create_nav_btn(4, "Finanzen", "📊")
        self.btn_finance.configure(command=self.open_finance_panel)
        
        self.btn_ams = create_nav_btn(5, "AMS Sync", "🤖") # NEU: AMS Button wieder da!
        self.btn_ams.configure(command=self.run_ams_sync)
        if not self.settings.get("use_bambu", False):
            self.btn_ams.grid_forget() # Verstecken, wenn Bambu in den Optionen aus ist
            
        self.btn_cloud = create_nav_btn(6, "Cloud", "☁️")
        self.btn_cloud.configure(command=self.open_cloud_panel)
        
        self.btn_queue = create_nav_btn(7, "Aufträge", "📝")
        self.btn_queue.configure(command=lambda: PrintQueueDialog(self.root, self))
        self.btn_finance.configure(command=self.open_finance_panel)
        self.btn_cloud = create_nav_btn(5, "Cloud", "☁️")
        self.btn_cloud.configure(command=self.open_cloud_panel)
        self.btn_queue = create_nav_btn(6, "Aufträge", "📝")
        # Für die Einkaufsliste:
        btn_shop = create_nav_btn(6, "Einkauf", "🛒")
        btn_shop.configure(command=lambda: ShoppingListDialog(self.root, self.inventory, self))

        # Für die Finanzen (die wir ja als Statistik-Popup haben):
        btn_stats = create_nav_btn(4, "Statistik", "📊")
        btn_stats.configure(command=lambda: StatisticsDialog(self.root, self.inventory, self))

        # Einstellungen ganz unten
        self.btn_options = ctk.CTkButton(self.sidebar_frame, text="⚙️ Optionen", height=40, fg_color="#1f538d", command=self.open_options_panel)
        self.btn_options.grid(row=9, column=0, padx=10, pady=(10, 20), sticky="ew")

    def build_main_area(self):
        """Baut den großen rechten Bereich mit der voll ausgestatteten Top-Bar."""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- TOP BAR ---
        self.top_bar = ctk.CTkFrame(self.main_frame, height=60, corner_radius=10)
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        # --- LINKE SEITE (Filter & Suche) ---
        self.entry_search = ctk.CTkEntry(self.top_bar, placeholder_text="🔍 Suchen...", width=140, height=35)
        self.entry_search.pack(side="left", padx=10, pady=10)
        self.entry_search.bind("<KeyRelease>", self.apply_filters)

        self.combo_mat = ctk.CTkComboBox(self.top_bar, values=["Alle Materialien"], width=130, height=35, command=self.apply_filters)
        self.combo_mat.pack(side="left", padx=5)

        self.combo_color = ctk.CTkComboBox(self.top_bar, values=["Alle Farben"], width=130, height=35, command=self.apply_filters)
        self.combo_color.pack(side="left", padx=5)

        self.combo_loc = ctk.CTkComboBox(self.top_bar, values=["Alle Orte", "LAGER", "VERBRAUCHT"], width=130, height=35, command=self.apply_filters)
        self.combo_loc.pack(side="left", padx=5)
        
        self.combo_brand = ctk.CTkComboBox(self.top_bar, values=["Alle Hersteller"], width=130, height=35, command=self.apply_filters)
        self.combo_brand.pack(side="left", padx=5)

        self.btn_reset = ctk.CTkButton(self.top_bar, text="🔄 Reset", width=70, height=35, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), command=self.reset_filters)
        self.btn_reset.pack(side="left", padx=10)

        # --- RECHTE SEITE (Tools & Knöpfe) ---
        self.btn_add = ctk.CTkButton(self.top_bar, text="➕ Neu Anlegen", height=35, font=ctk.CTkFont(weight="bold"), command=self.open_spool_panel)
        self.btn_add.pack(side="right", padx=15)

        self.btn_spenden = ctk.CTkButton(self.top_bar, text="☕ Spenden", width=80, height=35, fg_color="#e67e22", hover_color="#f39c12", text_color="black", font=ctk.CTkFont(weight="bold"), command=self.open_paypal)
        self.btn_spenden.pack(side="right", padx=5)

        self.btn_handy = ctk.CTkButton(self.top_bar, text="📱 Handy", width=80, height=35, fg_color="#1f538d", command=self.open_mobile_companion)
        self.btn_handy.pack(side="right", padx=5)

        self.btn_cam = ctk.CTkButton(self.top_bar, text="📷", width=40, height=35, fg_color="#333333", hover_color="#555555", command=self.scan_qr_webcam)
        self.btn_cam.pack(side="right", padx=5)

        self.entry_scan = ctk.CTkEntry(self.top_bar, placeholder_text="Quick-ID...", width=90, height=35)
        self.entry_scan.pack(side="right", padx=5)
        self.entry_scan.bind("<Return>", self.on_quick_scan)

        # --- CONTENT AREA (Tabelle) ---
        self.table_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.table_frame.grid(row=1, column=0, sticky="nsew")
        self.table_frame.pack_propagate(False)

        self.style_modern_treeview()

        columns = ("id", "brand", "material", "color", "weight", "location", "status")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", style="Modern.Treeview")
        
        for col, text in zip(columns, ["ID", "Marke", "Material", "Farbe", "Rest(g)", "Ort", "Status"]):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=100, anchor="center" if col != "brand" else "w")

        scrollbar = ctk.CTkScrollbar(self.table_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Die Events!
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=5, pady=10)

        self.update_filter_dropdowns()
        self.refresh_table()

    def style_modern_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        bg_color, fg_color, sel_color, head_bg = "#2b2b2b", "#e0e0e0", "#1f538d", "#1e1e1e"

        style.configure("Modern.Treeview", background=bg_color, foreground=fg_color, rowheight=35, fieldbackground=bg_color, borderwidth=0, font=("Segoe UI", 10))
        style.map('Modern.Treeview', background=[('selected', sel_color)])
        style.configure("Modern.Treeview.Heading", background=head_bg, foreground=fg_color, relief="flat", font=("Segoe UI", 11, "bold"), padding=5)
        style.map("Modern.Treeview.Heading", background=[('active', '#333333')])

    def update_filter_dropdowns(self):
        mats = sorted(list(set(i.get("material", "") for i in self.inventory if i.get("material"))))
        brands = sorted(list(set(i.get("brand", "") for i in self.inventory if i.get("brand"))))
        cols = sorted(list(set(str(i.get("color", "")).split("(")[0].strip() for i in self.inventory if i.get("color"))))
        
        locs = []
        from core.logic import parse_shelves_string
        for s in parse_shelves_string(self.settings.get("shelves", "REGAL|4|8")): locs.append(s['name'])
        for i in range(1, self.settings.get("num_ams", 1) + 1): locs.append(f"AMS {i}")
        locs.extend(["LAGER", "VERBRAUCHT"])
        
        self.combo_mat.configure(values=["Alle Materialien"] + mats)
        self.combo_color.configure(values=["Alle Farben"] + cols)
        self.combo_loc.configure(values=["Alle Orte"] + locs)
        self.combo_brand.configure(values=["Alle Hersteller"] + brands)  # <--- FIX: Hier hat vorhin die schließende Klammer gefehlt!

    def apply_filters(self, event=None):
        search_str = self.entry_search.get().lower()
        filter_mat = self.combo_mat.get()
        filter_col = self.combo_color.get()
        filter_loc = self.combo_loc.get()
        filter_brand = self.combo_brand.get()
        
        filtered_data = []
        for spool in self.inventory:
            if filter_mat != "Alle Materialien" and spool.get("material") != filter_mat: continue
            if filter_brand != "Alle Hersteller" and spool.get("brand") != filter_brand: continue
                
            color_clean = str(spool.get("color", "")).split("(")[0].strip()
            if filter_col != "Alle Farben" and color_clean != filter_col: continue
                
            t = spool.get("type", "LAGER")
            if filter_loc != "Alle Orte":
                if filter_loc == "LAGER" and t != "LAGER" and not t.startswith("REGAL"): continue
                elif filter_loc == "VERBRAUCHT" and t != "VERBRAUCHT": continue
                elif filter_loc not in ["LAGER", "VERBRAUCHT"] and not t.startswith(filter_loc): continue
                    
            if search_str:
                search_target = f"{spool.get('id','')} {spool.get('brand','')} {spool.get('color','')} {spool.get('material','')} {spool.get('sku','')} {spool.get('barcode','')}".lower()
                if search_str not in search_target: continue
                    
            filtered_data.append(spool)
            
        self.refresh_table(filtered_data)

    def reset_filters(self):
        self.entry_search.delete(0, 'end')
        self.combo_mat.set("Alle Materialien")
        self.combo_color.set("Alle Farben")
        self.combo_loc.set("Alle Orte")
        self.combo_brand.set("Alle Hersteller")
        self.refresh_table()

    def refresh_table(self, data=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        from core.logic import calculate_net_weight
        display_data = data if data is not None else self.inventory
        
        # Sortieren, damit AMS immer oben ist!
        display_data = sorted(display_data, key=lambda x: (0 if str(x.get('type')).startswith('AMS') else 1, int(x.get('id', 0))))
        
        for spool in display_data:
            net_weight = calculate_net_weight(spool.get('weight_gross', '0'), spool.get('spool_id', -1), self.spools, spool.get('empty_weight'))
            loc_type = spool.get('type', 'LAGER')
            loc_id = spool.get('loc_id', '')
            if loc_type.startswith("AMS"): loc_str = f"{loc_type} Slot {loc_id}"
            elif loc_type == "REGAL": loc_str = f"Fach {loc_id}"
            else: loc_str = loc_type
            color_clean = str(spool.get("color", "")).split("(")[0].strip()
            
            # Farb-Tags für die Tabelle
            tags = ()
            if loc_type == "VERBRAUCHT": tags = ("grayed",)
            elif spool.get("reorder"): tags = ("alert",)
                
            self.tree.insert("", "end", iid=str(spool.get("id")), values=(
                spool.get("id", ""), spool.get("brand", ""), spool.get("material", ""),
                color_clean, f"{net_weight}g", loc_str, spool.get("status", "-")
            ), tags=tags)
            
        self.tree.tag_configure("grayed", foreground="#999999")
        self.tree.tag_configure("alert", background="#4a1515", foreground="#ff6b6b")

    def on_tree_double_click(self, event):
        """Wird aufgerufen, wenn man in der Tabelle doppelt auf eine Spule klickt."""
        sel = self.tree.selection()
        if not sel: return
        spool_id = sel[0]
        self.open_spool_panel(spool_id)

    def log_consumption(self, used_g):
        """Trägt den Verbrauch in die globale history.json ein (für das Dashboard-Chart)."""
        import datetime, json, os
        data_dir = getattr(self.data_manager, 'base_dir', '')
        history_file = os.path.join(data_dir, "history.json") if data_dir else "history.json"
        hist_data = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f: hist_data = json.load(f)
            except: pass
        
        date_str = datetime.date.today().isoformat()
        current_total = hist_data.get(date_str, 0.0)
        hist_data[date_str] = round(current_total + float(used_g), 1)
        
        try:
            with open(history_file, "w") as f: json.dump(hist_data, f, indent=4)
        except: pass

    def broadcast_mqtt(self):
        """Puffert den MQTT-Status für Home Assistant."""
        if not self.settings.get("mqtt_enable", False): return
        import json, os
        
        data_dir = getattr(self.data_manager, 'base_dir', '')
        buffer_file = os.path.join(data_dir, "mqtt_buffer.json") if data_dir else "mqtt_buffer.json"
        
        total_weight = 0
        from core.logic import calculate_net_weight
        for item in self.inventory:
            if item.get('type') == 'VERBRAUCHT': continue
            total_weight += calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools, item.get('empty_weight'))
            
        payload = {
            "total_spools": len([i for i in self.inventory if i.get('type') != 'VERBRAUCHT']),
            "total_weight_kg": round(total_weight / 1000, 2)
        }
        
        try:
            with open(buffer_file, "w") as f: json.dump(payload, f)
        except: pass

    def run_ams_sync(self):
        ip = self.settings.get("bambu_ip", "")
        code = self.settings.get("bambu_access", "")
        serial = self.settings.get("bambu_serial", "")

        if not ip or not code or not serial:
            return messagebox.showerror("Fehler", "Bambu Zugangsdaten fehlen! Bitte erst in den Optionen eintragen.", parent=self.root)

        # Lade-Fenster blockiert die GUI, damit der User nicht wild rumklickt
        self.sync_win = ctk.CTkToplevel(self.root)
        self.sync_win.title("AMS Sync")
        self.sync_win.geometry("350x150")
        self.sync_win.attributes('-topmost', True)
        self.sync_win.grab_set()
        
        from core.utils import center_window
        center_window(self.sync_win, self.root)
        
        ctk.CTkLabel(self.sync_win, text="Verbinde mit Bambu Drucker...\nLese AMS Daten aus.\n\nBitte warten (ca. 5-10 Sekunden).", font=ctk.CTkFont(weight="bold"), justify="center").pack(expand=True)

        try:
            from core.bambu_sync import BambuScanner # type: ignore
        except ImportError:
            self.sync_win.destroy()
            return messagebox.showerror("Fehler", "Das Modul 'paho-mqtt' fehlt. Bitte über pip installieren.", parent=self.root)

        # Threading: Der Scanner läuft im Hintergrund, die GUI friert NICHT ein!
        import threading
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
            return messagebox.showerror("Fehler", "Keine Antwort vom Drucker. Ist er an und im LAN?", parent=self.root)

        # Das neue, interaktive Sync Control Center
        win = ctk.CTkToplevel(self.root)
        win.title("🤖 AMS Live-Sync Manager")
        win.geometry("1050x550")
        win.attributes('-topmost', True)
        win.grab_set()
        
        from core.utils import center_window
        center_window(win, self.root)
        
        ctk.CTkLabel(win, text="Bambu AMS mit VibeSpool abgleichen", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 5))
        
        # Container für die Slots
        frm = ctk.CTkScrollableFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Kopfzeile
        header_frm = ctk.CTkFrame(frm, fg_color="transparent")
        header_frm.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header_frm, text="AMS Slot (Bambu Info)", font=ctk.CTkFont(weight="bold"), width=250, anchor="w").pack(side="left")
        ctk.CTkLabel(header_frm, text="Welche Spule wurde eingelegt?", font=ctk.CTkFont(weight="bold"), width=380, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_frm, text="Alte Spule zurücklegen nach:", font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left")
            
        ctk.CTkFrame(frm, height=2, fg_color="#333333").pack(fill="x", pady=(0, 10))

        # Dropdown-Werte vorbereiten
        all_locs = []
        from core.logic import parse_shelves_string
        parsed_shelves = parse_shelves_string(self.settings.get("shelves", "REGAL|4|8"))
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
                    if self.settings.get("double_depth", False):
                        all_locs.append(f"{name} {row_name} - {col_name} (H)")
                        all_locs.append(f"{name} {row_name} - {col_name} (V)")
                    else:
                        all_locs.append(f"{name} {row_name} - {col_name}")
        
        if self.settings.get("custom_locs", ""):
            custom = [x.strip() for x in self.settings.get("custom_locs", "").split(",") if x.strip()]
            all_locs += custom
            
        filament_values = ["- Leer / Ignorieren -"]
        active_filaments = [i for i in self.inventory if i.get('type') != 'VERBRAUCHT']
        active_filaments.sort(key=lambda x: int(x.get('id', 0)))
        
        for i in active_filaments:
            name = f"{i.get('brand', '')} {i.get('material', '')} {i.get('color', '')}".strip()
            loc_str = f"{i.get('type', '')} {i.get('loc_id', '')}".strip()
            loc_display = f"[{loc_str}]" if loc_str else "[Ort unbekannt]"
            filament_values.append(f"{i['id']} - {name} {loc_display}")

        loc_values = ["- Nicht verschieben -"] + all_locs
        self.sync_vars = []

        for idx, r in enumerate(result):
            raw_slot = int(r.get('slot', 0))
            ams_num = r.get('ams', (raw_slot // 4)) + 1
            slot_num = (raw_slot % 4) + 1
            ams_name = f"AMS {ams_num}"
            
            row_frm = ctk.CTkFrame(frm, fg_color="transparent")
            row_frm.pack(fill="x", pady=5)
            
            # 1. Spalte: Was sagt Bambu?
            info_frame = ctk.CTkFrame(row_frm, width=250, fg_color="transparent")
            info_frame.pack(side="left", fill="y")
            info_frame.pack_propagate(False)
            
            ctk.CTkLabel(info_frame, text=f"{ams_name} Slot {slot_num}: ", font=ctk.CTkFont(weight="bold")).pack(side="left")
            
            if r['empty']:
                ctk.CTkLabel(info_frame, text="LEER", text_color="gray").pack(side="left")
            else:
                hex_col = f"#{r['color_hex'][:6]}" if len(r['color_hex']) >= 6 else "#FFFFFF"
                color_box = ctk.CTkFrame(info_frame, width=20, height=20, fg_color=hex_col, corner_radius=4, border_width=1, border_color="#555555")
                color_box.pack(side="left", padx=(5, 5))
                ctk.CTkLabel(info_frame, text=r['material'] or "Unbekannt").pack(side="left")

            # 2. Spalte: Welche Spule aus VibeSpool ist das?
            frm_col1 = ctk.CTkFrame(row_frm, width=380, fg_color="transparent")
            frm_col1.pack(side="left", fill="y", padx=10)
            frm_col1.pack_propagate(False)
            
            cb_new = ctk.CTkComboBox(frm_col1, values=filament_values, width=240)
            cb_new.pack(side="left", padx=(0, 5))
            
            current_fil = next((i for i in active_filaments if i.get('type') == ams_name and str(i.get('loc_id')) == str(slot_num)), None)
            if current_fil:
                name = f"{current_fil.get('brand', '')} {current_fil.get('material', '')} {current_fil.get('color', '')}".strip()
                loc_str = f"{current_fil.get('type', '')} {current_fil.get('loc_id', '')}".strip()
                loc_display = f"[{loc_str}]" if loc_str else "[Ort unbekannt]"
                val_to_select = f"{current_fil['id']} - {name} {loc_display}"
                if val_to_select in filament_values: cb_new.set(val_to_select)
                else: cb_new.set("- Leer / Ignorieren -")
            else:
                cb_new.set("- Leer / Ignorieren -")

            if not r['empty']:
                def make_import_cmd(current_r, current_cb):
                    return lambda: self.auto_import_from_ams(current_r, current_cb)
                ctk.CTkButton(frm_col1, text="➕ Neu", width=80, command=make_import_cmd(r, cb_new)).pack(side="left")

            # 3. Spalte: Wohin mit dem alten Zeug?
            cb_old = ctk.CTkComboBox(row_frm, values=loc_values, width=200)
            cb_old.set("- Nicht verschieben -")
            cb_old.pack(side="left", padx=10)

            self.sync_vars.append({"ams_name": ams_name, "slot_num": slot_num, "bambu_data": r, "cb_new": cb_new, "cb_old": cb_old})

        # Footer Buttons
        btn_frm = ctk.CTkFrame(win, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", pady=20, padx=20)
        ctk.CTkButton(btn_frm, text="Abbrechen", fg_color="transparent", border_width=1, command=win.destroy).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frm, text="💾 Sync in Datenbank speichern", font=ctk.CTkFont(weight="bold"), command=lambda: self.apply_ams_sync(win)).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def auto_import_from_ams(self, r, target_cb):
        new_id = max([int(i.get('id', 0)) for i in self.inventory], default=0) + 1
        mat = r.get('material', 'PLA') or 'PLA'
        hex_color = f"#{r.get('color_hex', 'FFFFFF')[:6]}".upper()
        if hex_color == "#": hex_color = "#FFFFFF"
        
        from core.colors import get_color_name_from_hex
        matched_name = get_color_name_from_hex(hex_color)
        final_color_db = f"{matched_name} ({hex_color})" if matched_name else hex_color
        display_color_name = matched_name if matched_name else hex_color
        brand = "Bambu" 
        
        new_item = {
            "id": new_id, "rfid": "", "brand": brand, "material": mat, 
            "color": final_color_db, "subtype": "Standard", "type": "LAGER", "loc_id": "-", 
            "flow": "", "pa": "", "spool_id": -1, "weight_gross": 1000, "capacity": 1000,
            "is_empty": False, "reorder": False, "supplier": "", "sku": "", "price": "", 
            "link": "", "temp_n": "", "temp_b": ""
        }
        
        self.inventory.append(new_item)
        self.data_manager.save_inventory(self.inventory)
        self.refresh_table()
        
        display_text = f"{new_id} - {brand} {mat} {display_color_name} [LAGER -]"
        
        for sv in getattr(self, 'sync_vars', []):
            cb = sv.get('cb_new')
            if cb:
                vals = list(cb.cget("values"))
                vals.append(display_text)
                cb.configure(values=vals)
                
        target_cb.set(display_text)
    
    def apply_ams_sync(self, win):
        moved_new = []
        moved_old = []
        incoming_ids = []
        
        for sv in self.sync_vars:
            new_selection = sv['cb_new'].get()
            if new_selection != "- Leer / Ignorieren -":
                try: incoming_ids.append(str(new_selection.split(" - ")[0]))
                except: pass

        collisions = []
        for sv in self.sync_vars:
            old_destination = sv['cb_old'].get()
            if old_destination != "- Nicht verschieben -":
                parts = old_destination.split(" ", 1)
                dest_type = parts[0] if len(parts) == 2 else old_destination
                dest_loc = parts[1] if len(parts) == 2 else ""
                
                existing = next((i for i in self.inventory if i.get('type') == dest_type and i.get('loc_id') == dest_loc and i.get('type') != 'VERBRAUCHT'), None)
                if existing and str(existing.get('id')) not in incoming_ids:
                    collisions.append(f"• {old_destination} (ist belegt durch: #{existing['id']} {existing.get('brand','')} {existing.get('color','')})")
                    
        if collisions:
            msg = "Achtung! Du versuchst alte Spulen auf Plätze zu legen, die bereits belegt sind:\n\n" + "\n".join(collisions) + "\n\nMöchtest du trotzdem speichern und riskieren, dass zwei Spulen am selben Platz liegen?"
            if not messagebox.askyesno("⚠️ Lagerplatz bereits belegt", msg, parent=win):
                return 

        for sv in self.sync_vars:
            ams_name = sv['ams_name'] 
            slot_num_str = str(sv['slot_num']) 
            new_selection = sv['cb_new'].get() 
            old_destination = sv['cb_old'].get() 
            
            old_filament = next((i for i in self.inventory if i.get('type') == ams_name and str(i.get('loc_id')) == slot_num_str), None)
            
            new_id = -1
            if new_selection != "- Leer / Ignorieren -":
                try: new_id = int(new_selection.split(" - ")[0])
                except: pass

            if old_filament and new_id == old_filament.get('id'):
                continue
            
            if old_filament and old_destination != "- Nicht verschieben -":
                parts = old_destination.split(" ", 1)
                if len(parts) == 2:
                    old_filament['type'] = parts[0]
                    old_filament['loc_id'] = parts[1]
                else:
                    old_filament['type'] = old_destination
                    old_filament['loc_id'] = ""
                moved_old.append(f"#{old_filament['id']} nach {old_destination}")
            
            if new_id != -1:
                new_filament = next((i for i in self.inventory if i.get('id') == new_id), None)
                if new_filament:
                    new_filament['type'] = ams_name
                    new_filament['loc_id'] = slot_num_str
                    moved_new.append(f"#{new_filament['id']} in {ams_name} Slot {slot_num_str}")

        total_changes = len(moved_new) + len(moved_old)
        if total_changes > 0:
            try:
                self.data_manager.save_inventory(self.inventory)
            except Exception as e:
                messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{e}", parent=win)
                return

            self.refresh_table()
            self.root.update_idletasks()
            self.broadcast_mqtt()
            
            msg = f"Sync erfolgreich durchgeführt ({total_changes} Umbuchungen).\n\n"
            if moved_new: msg += "✅ In AMS eingelegt:\n" + "\n".join(moved_new) + "\n\n"
            if moved_old: msg += "📦 Ins Regal zurückgelegt:\n" + "\n".join(moved_old)
            self.show_custom_toast("🤖 AMS Sync", msg)
        else:
            self.show_custom_toast("🤖 AMS Sync", "Keine Änderungen vorgenommen.")
            
        win.destroy()
    
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
                
                # --- Historie für Auto-Sync eintragen! ---
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
                
                # Wenn das Spulen-Panel gerade offen ist, aktualisieren!
                try:
                    sel = self.tree.selection()
                    if sel and str(sel[0]) == str(item['id']):
                        self.on_tree_double_click(None)
                except: pass
                
                if not silent:
                    msg = f"Es wurden {weight_g:.1f}g von Spule #{item['id']} abgezogen.\n({item.get('brand')} {item.get('color')})"
                    self.show_custom_toast("🎨 Druck beendet!", msg)

            except Exception as e:
                print(f"Fehler beim Abziehen: {e}")

    def _show_multicolor_dialog(self, tray_ids, total_weight_g):
        """Öffnet einen Dialog, wenn mehrere AMS-Slots benutzt wurden."""
        win = ctk.CTkToplevel(self.root)
        win.title("🎨 Multi-Color Druck beendet")
        win.geometry("550x450")
        win.attributes('-topmost', True)
        win.grab_set()
        
        from core.utils import center_window
        center_window(win, self.root)
        
        ctk.CTkLabel(win, text="Multi-Color Druck abgeschlossen!", font=ctk.CTkFont(size=18, weight="bold"), text_color="#0078d7").pack(pady=(20, 5))
        ctk.CTkLabel(win, text=f"Gesamtverbrauch (laut Drucker): {total_weight_g:.1f} g\nWelche Spule hat wie viel verbraucht?", justify="center").pack(pady=5)
        
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=10)
        
        entries = []
        
        # Für jeden benutzten Slot ein Feld generieren
        for t_id in tray_ids:
            ams_id = (t_id // 4) + 1
            slot = (t_id % 4) + 1
            ams_name = f"AMS {ams_id}"
            
            # Schauen wir, welche Spule in VibeSpool auf diesem Platz liegt
            item = next((i for i in self.inventory if i.get('type') == ams_name and str(i.get('loc_id')) == str(slot)), None)
            
            row = ctk.CTkFrame(frm, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            if item:
                lbl_text = f"{ams_name} Slot {slot}: {item.get('brand')} {item.get('color')}"
            else:
                lbl_text = f"{ams_name} Slot {slot}: Unbekannte Spule"
                
            ctk.CTkLabel(row, text=lbl_text, width=250, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            
            # Eingabefeld für die Grammzahl
            ent = ctk.CTkEntry(row, width=80, justify="right")
            ent.pack(side="right")
            ctk.CTkLabel(row, text=" g ").pack(side="right", padx=5)
            
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
                from tkinter import messagebox
                messagebox.showinfo("Erfolg", f"Es wurden insgesamt {total_entered:.1f}g auf die Spulen aufgeteilt und abgezogen!", parent=self.root)
            win.destroy()
            
        ctk.CTkFrame(win, height=2, fg_color="#333333").pack(fill="x", pady=10, padx=20)
        btn_frm_mc = ctk.CTkFrame(win, fg_color="transparent")
        btn_frm_mc.pack(fill="x", side="bottom", pady=(0, 20), padx=20)
        ctk.CTkButton(btn_frm_mc, text="💾 Gewichte abziehen & Speichern", font=ctk.CTkFont(weight="bold"), height=40, command=apply_split).pack(fill="x")
    
    def show_custom_toast(self, title, message):
        """Erstellt eine elegante, dunkle Benachrichtigung unten rechts im Bildschirm."""
        toast = ctk.CTkToplevel(self.root)
        toast.overrideredirect(True) # Keine Windows-Rahmen
        toast.attributes('-topmost', True) # Immer im Vordergrund
        toast.configure(fg_color="#1f538d") # Akzentfarbe als Rahmen
        
        # Innerer Frame für den Dark-Look
        inner = ctk.CTkFrame(toast, corner_radius=0, fg_color="#2b2b2b", border_width=2, border_color="#1f538d")
        inner.pack(fill="both", expand=True)
        
        lbl_title = ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#0078d7")
        lbl_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        lbl_msg = ctk.CTkLabel(inner, text=message, font=ctk.CTkFont(size=12), justify="left")
        lbl_msg.pack(padx=20, pady=(0, 15), anchor="w")
        
        toast.update_idletasks()
        w, h = toast.winfo_width(), toast.winfo_height()
        sw, sh = toast.winfo_screenwidth(), toast.winfo_screenheight()
        
        # Position: Rechts unten
        x, y = sw - w - 20, sh - h - 60
        toast.geometry(f"{w}x{h}+{x}+{y}")
        
        # Zerstört sich nach 5 Sekunden von selbst
        self.root.after(5000, toast.destroy)

    def quick_swap_dialog(self):
        sel = self.tree.selection()
        if not sel: 
            return messagebox.showinfo("Info", "Bitte zuerst eine Spule auswählen!", parent=self.root)
            
        s_a = next((i for i in self.inventory if str(i.get('id')) == str(sel[0])), None)
        if not s_a: return

        win = ctk.CTkToplevel(self.root)
        win.title("🔄 Quick-Swap")
        win.geometry("500x260")
        win.attributes('-topmost', True)
        win.grab_set()
        from core.utils import center_window
        center_window(win, self.root)
        
        ctk.CTkLabel(win, text="Spule ins AMS tauschen:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(win, text=f"Ausgewählt: {s_a.get('brand', '')} {s_a.get('color', '')}", font=ctk.CTkFont(size=14)).pack(pady=5)
        
        ams_map = {}
        for a in range(1, self.settings.get("num_ams", 1) + 1):
            am_n = f"AMS {a}"
            for s in range(1, 5):
                s_b = next((i for i in self.inventory if i.get('type') == am_n and str(i.get('loc_id')) == str(s)), None)
                label_text = f"{s_b.get('brand', '')} {s_b.get('color', '')}" if s_b else "(LEER)"
                d_t = f"{am_n} | Slot {s}  -->  {label_text}"
                ams_map[d_t] = (am_n, str(s))
                
        combo = ctk.CTkComboBox(win, values=list(ams_map.keys()), state="readonly", width=400)
        combo.pack(pady=15)
        combo.set(list(ams_map.keys())[0])
        
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
                msg_extra = f"\nDie alte Spule ({s_b.get('brand', '')}) wurde in {o_t} {o_l} gelegt!"
                
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.tree.selection_set(str(s_a.get('id', '')))
            
            win.destroy()
            self.show_custom_toast("🔄 Quick-Swap", f"{s_a.get('brand', '')} ist jetzt im {t_am} (Slot {t_sl}).{msg_extra}")
            
        ctk.CTkButton(win, text="🔄 Tauschen", font=ctk.CTkFont(weight="bold"), height=35, command=do_swap).pack(pady=15)

    def show_spool_history(self, event=None, spool_id=None):
        """Öffnet das Logbuch (Historie) für eine ausgewählte Spule."""
        if not spool_id:
            sel = self.tree.selection()
            if not sel: return
            spool_id = sel[0]

        item = next((i for i in self.inventory if str(i.get('id')) == str(spool_id)), None)
        if not item: return

        import re
        color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', '')).strip()

        win = ctk.CTkToplevel(self.root)
        win.title(f"📜 Logbuch: #{item.get('id')} - {item.get('brand')} {color_clean}")
        win.geometry("650x450")
        win.attributes('-topmost', True)
        win.grab_set()
        from core.utils import center_window
        center_window(win, self.root)

        ctk.CTkLabel(win, text=f"📜 Historie für Spule #{item.get('id')}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(win, text=f"{item.get('brand')} {color_clean} | {item.get('material')}", text_color="gray").pack(pady=(0, 15))

        history = item.get("history", [])

        if not history:
            ctk.CTkLabel(win, text="Bisher keine Einträge vorhanden.\n\nVerbräuche durch Cloud-Sync oder die Waage\nwerden hier automatisch protokolliert.", text_color="gray").pack(expand=True)
            ctk.CTkButton(win, text="Schließen", fg_color="transparent", border_width=1, command=win.destroy).pack(pady=15)
            return

        frm_list = ctk.CTkFrame(win, fg_color="transparent")
        frm_list.pack(fill="both", expand=True, padx=20, pady=5)
        
        columns = ("date", "action", "change", "cost")
        h_tree = ttk.Treeview(frm_list, columns=columns, show="headings", height=10)
        h_tree.heading("date", text="Datum & Zeit")
        h_tree.heading("action", text="Aktion / Druck")
        h_tree.heading("change", text="Verbrauch")
        h_tree.heading("cost", text="Kosten")

        h_tree.column("date", width=130)
        h_tree.column("action", width=250)
        h_tree.column("change", width=80, anchor="e")
        h_tree.column("cost", width=80, anchor="e")

        for entry in reversed(history):
            h_tree.insert("", "end", values=(entry.get("date", ""), entry.get("action", ""), entry.get("change", ""), entry.get("cost", "-")))

        scroll = ctk.CTkScrollbar(frm_list, command=h_tree.yview)
        h_tree.configure(yscrollcommand=scroll.set)
        h_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y", padx=(5,0))

        ctk.CTkButton(win, text="Schließen", fg_color="transparent", border_width=1, command=win.destroy).pack(pady=15)

    def show_context_menu(self, event):
        """Erzeugt das Rechtsklick-Menü in der neuen Darkmode-Optik."""
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            # Wir stylen das Standard-Tkinter-Menü dunkel, passend zum Rest!
            menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="#e0e0e0", activebackground="#1f538d", font=("Segoe UI", 10))
            
            menu.add_command(label="🔄 In AMS 1 laden...", command=lambda: self.quick_move_ams(row_id, "AMS 1"))
            menu.add_command(label="🔄 In AMS 2 laden...", command=lambda: self.quick_move_ams(row_id, "AMS 2"))
            menu.add_separator()
            menu.add_command(label="📋 Spule klonen", command=lambda: self.clone_spool(row_id))
            menu.add_command(label="🗑️ Als LEER markieren", command=lambda: self.mark_empty(row_id))
            
            menu.post(event.x_root, event.y_root)

    def quick_move_ams(self, spool_id, ams_name):
        item = next((i for i in self.inventory if str(i['id']) == str(spool_id)), None)
        if item:
            slot = simpledialog.askinteger("Slot wählen", f"Welcher Slot in {ams_name}? (1-4)", minvalue=1, maxvalue=4, parent=self.root)
            if slot:
                item['type'] = ams_name
                item['loc_id'] = str(slot)
                self.data_manager.save_inventory(self.inventory)
                self.apply_filters()

    def clone_spool(self, spool_id):
        item = next((i for i in self.inventory if str(i['id']) == str(spool_id)), None)
        if item:
            import copy, time
            new_item = copy.deepcopy(item)
            new_item['id'] = str(int(time.time()))
            self.inventory.append(new_item)
            self.data_manager.save_inventory(self.inventory)
            self.apply_filters()

    def mark_empty(self, spool_id):
        item = next((i for i in self.inventory if str(i['id']) == str(spool_id)), None)
        if item:
            item['type'] = "VERBRAUCHT"
            item['loc_id'] = ""
            item['weight_gross'] = item.get('empty_weight', '250')
            self.data_manager.save_inventory(self.inventory)
            self.apply_filters()

    def close_tool(self):
        """Schließt das aktuelle Werkzeug (Regal, Cloud, Finanzen) und bringt die Tabelle zurück."""
        if hasattr(self, 'tool_panel') and self.tool_panel.winfo_exists():
            self.tool_panel.destroy()
        # WICHTIG: Die Tabelle IMMER zurückholen!
        if hasattr(self, 'table_frame') and self.table_frame.winfo_exists():
            self.table_frame.grid(row=1, column=0, sticky="nsew")

    def close_editor(self):
        """Schließt nur das rechte Bearbeitungs-Formular."""
        if hasattr(self, 'editor_panel') and self.editor_panel.winfo_exists():
            self.editor_panel.destroy()

    def open_spool_panel(self, spool_id=None, prefill_type=None, prefill_loc=None):
        """Öffnet das Editor-Panel GANZ RECHTS (Spalte 2) im vollen VibeSpool-Funktionsumfang."""
        self.close_editor()
            
        self.editor_panel = ctk.CTkFrame(self.main_frame, width=380, corner_radius=10, fg_color="#2b2b2b", border_width=1, border_color="#333333")
        self.editor_panel.grid(row=1, column=2, sticky="nsew", padx=(10, 0))
        self.editor_panel.grid_rowconfigure(1, weight=1) # Lässt den Inhalt wachsen
        
        item = None
        if spool_id:
            item = next((i for i in self.inventory if str(i['id']) == str(spool_id)), None)
            
        title_text = "✨ Neue Spule" if not item else "📝 Spule bearbeiten"
        
        header = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=15, padx=20)
        ctk.CTkLabel(header, text=title_text, font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="❌", width=30, fg_color="transparent", hover_color="#8b0000", command=self.close_editor).pack(side="right")
        
        # --- TABVIEW FÜR ÜBERSICHTLICHKEIT ---
        tabs = ctk.CTkTabview(self.editor_panel)
        tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tab_basis = tabs.add("Basis & Lager")
        tab_details = tabs.add("Details & ERP")
        
        self.form_vars = {}
        
        # ==========================================
        # TAB 1: BASIS & LAGER
        # ==========================================
        content = ctk.CTkScrollableFrame(tab_basis, fg_color="transparent")
        content.pack(fill="both", expand=True)

        # ID & RFID
        row_id = ctk.CTkFrame(content, fg_color="transparent")
        row_id.pack(fill="x", pady=(5, 5))
        ctk.CTkLabel(row_id, text="ID:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ent_id = ctk.CTkEntry(row_id, width=60)
        ent_id.insert(0, str(item.get("id", "")) if item else "")
        ent_id.pack(side="left", padx=5)
        self.form_vars["id"] = ent_id
        
        ctk.CTkLabel(row_id, text="RFID:").pack(side="left", padx=(10, 0))
        ent_rfid = ctk.CTkEntry(row_id, width=120)
        ent_rfid.insert(0, str(item.get("rfid", "")) if item else "")
        ent_rfid.pack(side="left", padx=5)
        self.form_vars["rfid"] = ent_rfid

        # Marke
        ctk.CTkLabel(content, text="Marke:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        ent_brand = ctk.CTkComboBox(content, values=sorted(self.settings.get("brands", []), key=str.lower))
        ent_brand.set(str(item.get("brand", "")) if item else "")
        ent_brand.pack(fill="x")
        self.form_vars["brand"] = ent_brand

        # Material & Typ
        row_mat = ctk.CTkFrame(content, fg_color="transparent")
        row_mat.pack(fill="x", pady=(10, 5))
        
        frm_m = ctk.CTkFrame(row_mat, fg_color="transparent")
        frm_m.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(frm_m, text="Material:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ent_mat = ctk.CTkComboBox(frm_m, values=self.settings.get("materials", []))
        ent_mat.set(str(item.get("material", "PLA")) if item else "PLA")
        ent_mat.pack(fill="x")
        self.form_vars["material"] = ent_mat
        
        frm_t = ctk.CTkFrame(row_mat, fg_color="transparent")
        frm_t.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(frm_t, text="Effekt/Typ:").pack(anchor="w")
        ent_sub = ctk.CTkComboBox(frm_t, values=self.settings.get("subtypes", []))
        ent_sub.set(str(item.get("subtype", "Standard")) if item else "Standard")
        ent_sub.pack(fill="x")
        self.form_vars["subtype"] = ent_sub

        # Farbe mit Smart-Picker
        ctk.CTkLabel(content, text="Farbe (Hex-Code / Mix mit '/' trennen):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        row_col = ctk.CTkFrame(content, fg_color="transparent")
        row_col.pack(fill="x")
        
        ent_col = ctk.CTkComboBox(row_col, values=self.settings.get("colors", []))
        ent_col.set(str(item.get("color", "")) if item else "")
        ent_col.pack(side="left", fill="x", expand=True)
        self.form_vars["color"] = ent_col
        
        def pick_smart_color():
            color_code = colorchooser.askcolor(title="Farbe wählen", parent=self.root)[1]
            if not color_code: return
            color_code = color_code.upper()
            
            from core.colors import get_color_name_from_hex
            matched_name = get_color_name_from_hex(color_code)
            
            new_entry = f"{matched_name} ({color_code})" if matched_name else color_code
            current_text = ent_col.get().strip()
            ent_col.set(new_entry if not current_text else f"{current_text} / {new_entry}")
            
        ctk.CTkButton(row_col, text="🎨", width=40, command=pick_smart_color).pack(side="left", padx=(5, 0))

        # Waage & Gewicht
        ctk.CTkFrame(content, height=2, fg_color="#333333").pack(fill="x", pady=15)
        
        row_spool = ctk.CTkFrame(content, fg_color="transparent")
        row_spool.pack(fill="x")
        ctk.CTkLabel(row_spool, text="Leerspule:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        var_refill = ctk.BooleanVar(value=item.get("is_refill", False) if item else False)
        ctk.CTkCheckBox(row_spool, text="🔄 Refill", variable=var_refill, width=60).pack(side="right")
        self.form_vars["is_refill"] = var_refill
        
        sorted_spools = sorted(self.spools, key=lambda s: s['name'].lower())
        spool_vals = ["-"] + [f"{s['id']} - {s['name']}" for s in sorted_spools]
        ent_spool = ctk.CTkComboBox(content, values=spool_vals)
        ent_spool.pack(fill="x", pady=(5, 5))
        self.form_vars["spool_id_combo"] = ent_spool
        
        if item:
            for v in spool_vals:
                if v.startswith(f"{item.get('spool_id', -1)} -"): ent_spool.set(v); break
        else: ent_spool.set("-")

        row_weights = ctk.CTkFrame(content, fg_color="transparent")
        row_weights.pack(fill="x", pady=5)
        
        frm_net = ctk.CTkFrame(row_weights, fg_color="transparent")
        frm_net.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(frm_net, text="Kapazität (Netto g):").pack(anchor="w")
        ent_cap = ctk.CTkEntry(frm_net)
        ent_cap.insert(0, str(item.get("capacity", "1000")) if item else "1000")
        ent_cap.pack(fill="x")
        self.form_vars["capacity"] = ent_cap
        
        frm_empty = ctk.CTkFrame(row_weights, fg_color="transparent")
        frm_empty.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(frm_empty, text="Leergewicht (g):").pack(anchor="w")
        ent_empty = ctk.CTkEntry(frm_empty)
        if item and item.get("empty_weight") is not None: ent_empty.insert(0, str(item["empty_weight"]))
        ent_empty.pack(fill="x")
        self.form_vars["empty_weight"] = ent_empty

        ctk.CTkLabel(content, text="Gewicht auf Waage (Brutto g):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        row_gross = ctk.CTkFrame(content, fg_color="transparent")
        row_gross.pack(fill="x")
        
        def set_full():
            try:
                c = float(ent_cap.get().replace(",", "."))
                sp_id = -1 if ent_spool.get() == "-" else int(ent_spool.get().split(" - ")[0])
                sp = next((s for s in self.spools if s['id'] == sp_id), None)
                sp_w = sp['weight'] if sp else 0
                ent_gross.delete(0, ctk.END)
                ent_gross.insert(0, f"{c + sp_w:g}")
            except: pass
            
        def calc_empty():
            try:
                c = float(ent_cap.get().replace(",", "."))
                g = float(ent_gross.get().replace(",", "."))
                if g > c:
                    ent_spool.set("-")
                    ent_empty.delete(0, ctk.END)
                    ent_empty.insert(0, f"{(g - c):g}")
            except: pass

        ent_gross = ctk.CTkEntry(row_gross)
        ent_gross.insert(0, str(item.get("weight_gross", "")) if item else "")
        ent_gross.pack(side="left", fill="x", expand=True)
        self.form_vars["weight_gross"] = ent_gross
        
        ctk.CTkButton(row_gross, text="⚖️ Voll", width=60, fg_color="#1f538d", command=set_full).pack(side="left", padx=(5, 0))
        ctk.CTkButton(row_gross, text="🧮 Leer", width=60, fg_color="#333333", hover_color="#444444", command=calc_empty).pack(side="left", padx=(5, 0))

        # Lagerort
        ctk.CTkFrame(content, height=2, fg_color="#333333").pack(fill="x", pady=15)
        
        row_loc = ctk.CTkFrame(content, fg_color="transparent")
        row_loc.pack(fill="x")
        
        frm_type = ctk.CTkFrame(row_loc, fg_color="transparent")
        frm_type.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(frm_type, text="Lagerort:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        # Dynamische Orte holen
        locs = [s['name'] for s in parse_shelves_string(self.settings.get("shelves", "REGAL|4|8"))]
        for i in range(1, self.settings.get("num_ams", 1) + 1): locs.append(f"AMS {i}")
        for c in self.settings.get("custom_locs", "").split(","):
            if c.strip(): locs.append(c.strip())
        locs.extend(["LAGER", "VERBRAUCHT"])
        
        ent_type = ctk.CTkComboBox(frm_type, values=locs)
        ent_type.set(prefill_type if prefill_type else str(item.get("type", "LAGER")) if item else "LAGER")
        ent_type.pack(fill="x")
        self.form_vars["type"] = ent_type
        
        frm_slot = ctk.CTkFrame(row_loc, fg_color="transparent")
        frm_slot.pack(side="left", fill="x", expand=True)
        lbl_slot = ctk.CTkLabel(frm_slot, text="Slot / Detail:")
        lbl_slot.pack(anchor="w")
        
        ent_loc_id = ctk.CTkComboBox(frm_slot, values=["-"])
        ent_loc_id.set(prefill_loc if prefill_loc else str(item.get("loc_id", "")) if item else "")
        ent_loc_id.pack(fill="x")
        self.form_vars["loc_id"] = ent_loc_id
        
        # ==========================================
        # TAB 2: DETAILS & ERP
        # ==========================================
        content_erp = ctk.CTkScrollableFrame(tab_details, fg_color="transparent")
        content_erp.pack(fill="both", expand=True)

        def add_field(parent, label_text, widget, key, default_val=""):
            ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
            widget.pack(fill="x")
            if isinstance(widget, ctk.CTkEntry):
                widget.insert(0, str(item.get(key, default_val)) if item else default_val)
            self.form_vars[key] = widget

        add_field(content_erp, "Barcode (Scannen):", ctk.CTkEntry(content_erp), "barcode")
        add_field(content_erp, "Lieferant / Shop:", ctk.CTkEntry(content_erp), "supplier")
        add_field(content_erp, "SKU / Art.-Nr.:", ctk.CTkEntry(content_erp), "sku")
        add_field(content_erp, "Preis (€):", ctk.CTkEntry(content_erp), "price")
        add_field(content_erp, "Link zum Shop:", ctk.CTkEntry(content_erp), "link")
        
        row_temps = ctk.CTkFrame(content_erp, fg_color="transparent")
        row_temps.pack(fill="x", pady=10)
        
        frm_tn = ctk.CTkFrame(row_temps, fg_color="transparent")
        frm_tn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        add_field(frm_tn, "Nozzle (°C):", ctk.CTkEntry(frm_tn), "temp_n")
        
        frm_tb = ctk.CTkFrame(row_temps, fg_color="transparent")
        frm_tb.pack(side="left", fill="x", expand=True)
        add_field(frm_tb, "Bed (°C):", ctk.CTkEntry(frm_tb), "temp_b")

        ctk.CTkFrame(content_erp, height=2, fg_color="#333333").pack(fill="x", pady=15)

        # Flow & PA (mit Flow-Rechner Anbindung)
        row_klipper = ctk.CTkFrame(content_erp, fg_color="transparent")
        row_klipper.pack(fill="x")
        
        frm_flow = ctk.CTkFrame(row_klipper, fg_color="transparent")
        frm_flow.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(frm_flow, text="Flow-Ratio:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        frm_f_in = ctk.CTkFrame(frm_flow, fg_color="transparent")
        frm_f_in.pack(fill="x")
        ent_flow = ctk.CTkEntry(frm_f_in)
        ent_flow.insert(0, str(item.get("flow", "")) if item else "")
        ent_flow.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(frm_f_in, text="🧪", width=30, command=lambda: FlowCalculatorDialog(self.root, ent_flow)).pack(side="right", padx=(5,0))
        self.form_vars["flow"] = ent_flow
        
        frm_pa = ctk.CTkFrame(row_klipper, fg_color="transparent")
        frm_pa.pack(side="left", fill="x", expand=True)
        add_field(frm_pa, "Pressure Adv:", ctk.CTkEntry(frm_pa), "pa")
        
        add_field(content_erp, "Notiz:", ctk.CTkEntry(content_erp), "note")
        
        var_reorder = ctk.BooleanVar(value=item.get("reorder", False) if item else False)
        ctk.CTkCheckBox(content_erp, text="🛒 Auf Einkaufsliste setzen", variable=var_reorder).pack(anchor="w", pady=(20, 10))
        self.form_vars["reorder"] = var_reorder

        # ==========================================
        # FUSSZEILE (SPEICHERN & LÖSCHEN)
        # ==========================================
        btn_frame = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=15, padx=20)
        
        if item:
            ctk.CTkButton(btn_frame, text="🗑️", width=40, height=40, fg_color="#8b0000", hover_color="#5c0000", command=lambda: self.delete_spool(spool_id)).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="💾 Speichern", height=40, font=ctk.CTkFont(weight="bold"), command=lambda: self.save_spool(spool_id)).pack(side="left", fill="x", expand=True)

    def check_location_collision(self, loc_type, loc_id, ignore_id=None):
        if loc_type in ["LAGER", "VERBRAUCHT", ""]: return None
        if loc_id in ["-", ""]: return None
        
        for i in self.inventory:
            if str(i.get('id')) == str(ignore_id): continue
            if i.get('type') == "VERBRAUCHT": continue
            if i.get('type') == loc_type and str(i.get('loc_id')) == str(loc_id):
                return i 
        return None

    def learn_dropdown_values(self, d):
        changed = False
        def add_if_new(key, val, default_list):
            if not val or val == "-" or val.startswith("Alle "): return False
            current_list = self.settings.get(key, default_list)
            if not any(x.lower() == val.lower() for x in current_list):
                current_list.append(val)
                self.settings[key] = current_list
                return True
            return False

        if add_if_new("brands", d.get('brand', ''), []): changed = True
        if add_if_new("materials", d.get('material', ''), MATERIALS): changed = True
        if add_if_new("subtypes", d.get('subtype', ''), SUBTYPES): changed = True
        
        for color_part in str(d.get('color', '')).split('/'):
            if add_if_new("colors", color_part.strip(), COMMON_COLORS): changed = True

        if changed:
            self.data_manager.save_settings(self.settings)

    def save_spool(self, spool_id=None):
        import time
        from datetime import datetime
        
        # 1. Daten sicher auslesen
        try:
            sp_id_raw = self.form_vars["spool_id_combo"].get()
            spool_ref_id = -1 if sp_id_raw == "-" else int(sp_id_raw.split(" - ")[0])
            
            gross_val = float(self.form_vars["weight_gross"].get().replace(',', '.') or 0)
            if self.form_vars["type"].get() == "VERBRAUCHT": gross_val = 0.0
            
            empty_val = None
            if spool_ref_id == -1:
                try: empty_val = float(self.form_vars["empty_weight"].get().replace(',', '.'))
                except: pass
        except ValueError:
            messagebox.showwarning("Fehler", "Bitte Zahlenwerte (Gewicht) prüfen!", parent=self.root)
            return

        d = {
            "id": self.form_vars["id"].get().strip(),
            "rfid": self.form_vars["rfid"].get().strip(),
            "brand": self.form_vars["brand"].get().strip(),
            "material": self.form_vars["material"].get().strip(),
            "color": self.form_vars["color"].get().strip(),
            "subtype": self.form_vars["subtype"].get().strip(),
            "type": self.form_vars["type"].get(),
            "loc_id": self.form_vars["loc_id"].get().strip(),
            "flow": self.form_vars["flow"].get().strip(),
            "pa": self.form_vars["pa"].get().strip(),
            "spool_id": spool_ref_id,
            "empty_weight": empty_val,
            "weight_gross": gross_val,
            "capacity": float(self.form_vars["capacity"].get().replace(',', '.') or 1000),
            "is_refill": self.form_vars["is_refill"].get(),
            "is_empty": self.form_vars["type"].get() == "VERBRAUCHT",
            "reorder": self.form_vars["reorder"].get(),
            "supplier": self.form_vars["supplier"].get().strip(),
            "sku": self.form_vars["sku"].get().strip(),
            "price": self.form_vars["price"].get().strip(),
            "link": self.form_vars["link"].get().strip(),
            "temp_n": self.form_vars["temp_n"].get().strip(),
            "temp_b": self.form_vars["temp_b"].get().strip(),
            "note": self.form_vars["note"].get().strip(),
            "barcode": self.form_vars["barcode"].get().strip()
        }
        
        # 2. Ist das eine NEUE oder BESTEHENDE Spule?
        is_new = False
        if spool_id:
            spool = next((i for i in self.inventory if str(i['id']) == str(spool_id)), None)
            d["history"] = spool.get("history", []) if spool else []
            d["added"] = spool.get("added", datetime.now().strftime("%Y-%m-%d")) if spool else datetime.now().strftime("%Y-%m-%d")
        else:
            is_new = True
            d["history"] = []
            d["added"] = datetime.now().strftime("%Y-%m-%d")
            
            if not d["id"]:
                max_num = 0
                for item in self.inventory:
                    if str(item['id']).isdigit():
                        max_num = max(max_num, int(item['id']))
                d["id"] = str(max_num + 1)

        # 3. ID-Kollisionscheck
        if is_new or str(d['id']) != str(spool_id):
            if any(str(i['id']) == str(d['id']) for i in self.inventory if str(i['id']) != str(spool_id)):
                messagebox.showerror("Fehler", f"Die ID {d['id']} existiert bereits!", parent=self.root)
                return

        # 4. Lager-Kollisionscheck
        col = self.check_location_collision(d['type'], d['loc_id'], ignore_id=spool_id)
        if col:
            msg = f"Der Platz {d['type']} {d['loc_id']} ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}\n\nTrotzdem speichern?"
            if not messagebox.askyesno("⚠️ Platz belegt", msg, parent=self.root): return

        # 5. Waagen-Abzug (Retrofit!)
        if not is_new and spool:
            old_gross = float(spool.get('weight_gross', 0.0))
            if gross_val < old_gross:
                diff = round(old_gross - gross_val, 1)
                if diff >= 1.0:
                    if messagebox.askyesno("⚖️ Waage: Verbrauch erkannt!", f"Das Gewicht ist um {diff}g leichter als vorher.\nIn die Statistik (Logbuch) eintragen?", parent=self.root):
                        self.log_consumption(diff)
                        d["history"].append({
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "action": "Waagen-Korrektur",
                            "change": f"-{diff}g",
                            "cost": "-",
                            "sell_price": "-"
                        })

        # 6. Abspeichern
        if is_new:
            self.inventory.append(d)
        else:
            idx = next(i for i, item in enumerate(self.inventory) if str(item['id']) == str(spool_id))
            self.inventory[idx] = d

        self.learn_dropdown_values(d)
        self.data_manager.save_inventory(self.inventory)
        self.broadcast_mqtt()
        
        self.refresh_table()
        self.close_editor()
        
        # Zeile markieren
        try:
            self.tree.selection_set(str(d['id']))
            self.tree.see(str(d['id']))
        except: pass
        
        # Falls das Regal im Hintergrund offen ist, aktualisieren
        if hasattr(self, 'tool_panel') and self.tool_panel.winfo_exists() and self.tool_panel.grid_info().get('column') == 0:
            self.open_regal_panel()

    def delete_spool(self, spool_id):
        if messagebox.askyesno("Löschen", "Möchtest du diese Spule wirklich löschen?", parent=self.root):
            self.inventory = [i for i in self.inventory if str(i['id']) != str(spool_id)]
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.close_editor()
            if hasattr(self, 'tool_panel') and self.tool_panel.winfo_exists() and self.tool_panel.grid_info().get('column') == 0:
                self.open_regal_panel()

    def open_regal_panel(self):
        """Öffnet den Regal-Visualisierer in Spalte 0 (BUNT, Drag&Drop, LAGER!)."""
        self.close_tool()
        
        if hasattr(self, 'table_frame') and self.table_frame.winfo_exists():
            self.table_frame.grid_remove()

        self.tool_panel = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="#2b2b2b")
        self.tool_panel.grid(row=1, column=0, sticky="nsew")

        header = ctk.CTkFrame(self.tool_panel, fg_color="transparent")
        header.pack(fill="x", pady=15, padx=20)
        ctk.CTkLabel(header, text="📦 Regal & AMS Dashboard", font=ctk.CTkFont(size=20, weight="bold"), text_color="#0078d7").pack(side="left")
        ctk.CTkButton(header, text="❌ Schließen", width=100, fg_color="transparent", hover_color="#8b0000", border_width=1, command=self.close_tool).pack(side="right")

        content = ctk.CTkScrollableFrame(self.tool_panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # WICHTIG: Cache, sonst löscht Python die Gradienten-Bilder sofort wieder!
        self.shelf_image_cache = []
        self.shelf_drop_zones = {}

        # --- HILFSFUNKTION FÜR LABEL-ERSTELLUNG (Wie im Original!) ---
        from core.utils import get_colors_from_text, create_color_icon
        from core.logic import calculate_net_weight

        def create_slot_label(parent_frm, label_text, spool_data, loc_type, loc_id, width=80, height=75):
            is_ams = loc_type.startswith("AMS")
            bg_colors = ["#D2B48C"] if not is_ams else ["#666666"]
            fg_col = "#555" if not is_ams else "#CCC"
            txt = f"{label_text}\nLEER"
            
            if spool_data:
                cols = get_colors_from_text(spool_data.get('color', ''))
                bg_colors = cols or ["#FFFFFF"]
                if bg_colors[0].startswith("#"):
                    r, g, b = int(bg_colors[0][1:3], 16), int(bg_colors[0][3:5], 16), int(bg_colors[0][5:7], 16)
                    fg_col = "white" if (r*0.299 + g*0.587 + b*0.114) < 128 else "black"
                else: fg_col = "black"
                
                sub = spool_data.get('subtype', '')
                mat = spool_data.get('material', '')
                net = calculate_net_weight(spool_data.get('weight_gross', '0'), spool_data.get('spool_id', -1), self.spools, spool_data.get('empty_weight'))
                
                # Originale Abkürzungen, damit der Text ins Feld passt!
                abk = {"Standard": "Std.", "High Speed": "HS", "Dual Color": "Dual", "Tri Color": "Tri", "Glow in Dark": "Glow", "Transparent": "Transp.", "Translucent": "Transl.", "Glitzer/Sparkle": "Glitz."}
                sub_short = abk.get(sub, sub[:7])
                mat_short = mat[:5] 
                
                txt = f"{label_text}\n{spool_data.get('brand', '')[:10]}\n{mat_short} {sub_short}\n{net}g"
                
            img = create_color_icon(bg_colors, (width, height), "black")
            self.shelf_image_cache.append(img)
            
            # WICHTIG: Wir nutzen natives tk.Label, damit die Gradients sichtbar bleiben und D&D funktioniert
            lbl = tk.Label(parent_frm, image=img, text=txt, compound="center", fg=fg_col, bg="#2b2b2b", font=("Segoe UI", 8, "bold"), borderwidth=1, relief="flat", cursor="hand2")
            
            self.shelf_drop_zones[str(lbl)] = {"type": loc_type, "loc_id": str(loc_id), "spool": spool_data}
            
            # Das Hybrid-Binding für Drag UND Klick
            lbl.bind("<ButtonPress-1>", lambda e, s=spool_data, t=loc_type, l=loc_id: self.on_shelf_drag_start(e, s, t, l))
            lbl.bind("<B1-Motion>", self.on_shelf_drag_motion)
            lbl.bind("<ButtonRelease-1>", self.on_shelf_drag_release)
            
            return lbl

        # --- 1. AMS EINHEITEN ---
        ctk.CTkLabel(content, text="🤖 Aktive AMS Einheiten", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", pady=(10, 5))
        ams_container = ctk.CTkFrame(content, fg_color="transparent")
        ams_container.pack(fill="x")
        
        for ams_idx in range(1, self.settings.get("num_ams", 1) + 1):
            ams_name = f"AMS {ams_idx}"
            ams_frame = ctk.CTkFrame(ams_container, corner_radius=8, fg_color="#1e1e1e")
            ams_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(ams_frame, text=ams_name, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20, pady=15)
            
            slots_frame = ctk.CTkFrame(ams_frame, fg_color="transparent")
            slots_frame.pack(side="right", padx=10, pady=5)
            
            for slot in range(1, 5):
                spool = next((s for s in self.inventory if s.get('type') == ams_name and str(s.get('loc_id')) == str(slot)), None)
                create_slot_label(slots_frame, str(slot), spool, ams_name, str(slot), 100, 80).pack(side="left", padx=5)

        # --- 2. REGALE ---
        ctk.CTkLabel(content, text="🗄️ Deine Lager-Regale", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", pady=(30, 5))
        
        from core.logic import parse_shelves_string
        shelves_str = self.settings.get("shelves", "REGAL|4|8")
        shelves_data = parse_shelves_string(shelves_str)
        lbl_r = self.settings.get("label_row", "Fach")
        lbl_c = self.settings.get("label_col", "Slot")
        logistics = self.settings.get("logistics_order", False)
        all_shelf_names = self.settings.get("shelf_names_v2", {})
        is_double = self.settings.get("double_depth", False)
        
        for shelf in shelves_data:
            shelf_name = shelf["name"]
            rows, cols = shelf["rows"], shelf["cols"]
            shelf_names = all_shelf_names.get(shelf_name, {})
            
            shelf_frame = ctk.CTkFrame(content, corner_radius=8, fg_color="#1e1e1e")
            shelf_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(shelf_frame, text=f"📦 {shelf_name}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15,5), padx=15, anchor="w")
            
            grid_frame = ctk.CTkFrame(shelf_frame, fg_color="transparent")
            grid_frame.pack(pady=10, padx=15, anchor="w")
            
            row_iter = range(rows, 0, -1) if logistics else range(1, rows + 1)
            for visual_r, r in enumerate(row_iter):
                row_label = shelf_names.get(str(r), f"{lbl_r} {r}")
                ctk.CTkLabel(grid_frame, text=row_label, font=ctk.CTkFont(weight="bold", size=12), width=80, anchor="e").grid(row=visual_r, column=0, padx=(0, 15), pady=5)
                
                for c in range(1, cols + 1):
                    col_label = shelf_names.get(f"col_{c}", f"{lbl_c} {c}")
                    short_label = col_label.replace(f"{lbl_c} ", "") if col_label.startswith(f"{lbl_c} ") else col_label
                    
                    slot_cell = ctk.CTkFrame(grid_frame, fg_color="transparent")
                    slot_cell.grid(row=visual_r, column=c, padx=4, pady=4)
                    
                    if is_double:
                        slot_name_h = f"{row_label} - {col_label} (H)"
                        spool_h = next((s for s in self.inventory if s.get('type') == shelf_name and str(s.get('loc_id')) == slot_name_h), None)
                        create_slot_label(slot_cell, f"{short_label}(H)", spool_h, shelf_name, slot_name_h, 75, 40).pack(side="top", pady=(0, 2))
                        
                        slot_name_v = f"{row_label} - {col_label} (V)"
                        spool_v = next((s for s in self.inventory if s.get('type') == shelf_name and str(s.get('loc_id')) == slot_name_v), None)
                        create_slot_label(slot_cell, f"{short_label}(V)", spool_v, shelf_name, slot_name_v, 75, 40).pack(side="top")
                    else:
                        slot_name = f"{row_label} - {col_label}"
                        spool = next((s for s in self.inventory if s.get('type') == shelf_name and str(s.get('loc_id')) == slot_name), None)
                        create_slot_label(slot_cell, short_label, spool, shelf_name, slot_name, 75, 75).pack()

        # --- 3. LAGER & WEITERE ORTE ---
        ctk.CTkLabel(content, text="📦 Weitere Lagerorte (Drag & Drop möglich!)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", pady=(30, 5))
        
        other_items = {}
        shelf_names_list = [s['name'] for s in shelves_data]
        for sp in self.inventory:
            t = str(sp.get('type', 'LAGER'))
            if t != "VERBRAUCHT" and not t.startswith("AMS") and t not in shelf_names_list:
                if t not in other_items: other_items[t] = []
                other_items[t].append(sp)
                
        if "LAGER" not in other_items: other_items["LAGER"] = []

        for loc_name, items in other_items.items():
            if not items and loc_name != "LAGER": continue
            
            ctk.CTkLabel(content, text=loc_name, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 2))
            loc_frame = ctk.CTkFrame(content, corner_radius=8, fg_color="#1e1e1e")
            loc_frame.pack(fill="x", pady=2, anchor="w")
            
            grid_frame = ctk.CTkFrame(loc_frame, fg_color="transparent")
            grid_frame.pack(padx=10, pady=10, anchor="w")
            
            col_count, row_count = 0, 0
            for item in items:
                if col_count >= 10:
                    col_count = 0
                    row_count += 1
                    
                loc_id = item.get("loc_id", "") or "-"
                create_slot_label(grid_frame, "1", item, loc_name, loc_id, 80, 75).grid(row=row_count, column=col_count, padx=4, pady=4)
                col_count += 1
                
            # Drop-Ziel für diesen Ort ("Magnet")
            if col_count >= 10:
                col_count = 0
                row_count += 1
            create_slot_label(grid_frame, "➕\nAblegen", None, loc_name, "-", 80, 75).grid(row=row_count, column=col_count, padx=4, pady=4)

    def open_options_panel(self):
        """Öffnet das moderne Optionen-Menü mit Tabs."""
        options_win = ctk.CTkToplevel(self.root)
        options_win.title("⚙️ Einstellungen")
        options_win.geometry("500x450")
        
        # Zentrieren & Fokus erzwingen (Modal)
        options_win.attributes("-topmost", True)
        options_win.grab_set() 

        # --- TAB-MENÜ ---
        tabview = ctk.CTkTabview(options_win)
        tabview.pack(fill="both", expand=True, padx=20, pady=10)

        tabview.add("💰 Kalkulation")
        tabview.add("📦 Lager & System")

        # --- HILFSFUNKTION FÜR LINIEN ---
        def add_setting_row(parent, label_text, key, default_val):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=8, padx=10)
            ctk.CTkLabel(row, text=label_text, width=200, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            entry = ctk.CTkEntry(row, width=120)
            entry.pack(side="right")
            entry.insert(0, str(self.settings.get(key, default_val)))
            return entry

        # --- TAB 1: KALKULATION ---
        tab_calc = tabview.tab("💰 Kalkulation")
        ctk.CTkLabel(tab_calc, text="Diese Werte nutzt VibeSpool für das Finanz-Dashboard:", text_color="gray").pack(pady=(5, 15))
        
        self.ent_kwh = add_setting_row(tab_calc, "Strompreis (€/kWh):", "kwh_price", "0.30")
        self.ent_watts = add_setting_row(tab_calc, "Drucker Verbrauch (Watt):", "printer_watts", "150")
        self.ent_wear = add_setting_row(tab_calc, "Maschinenverschleiß (€/h):", "wear_per_hour", "0.20")
        self.ent_margin = add_setting_row(tab_calc, "Gewinnmarge (%):", "profit_margin", "0")

        # --- TAB 2: LAGER & SYSTEM ---
        tab_sys = tabview.tab("📦 Lager & System")
        path = getattr(self.data_manager, 'base_dir', 'Unbekannt')
        ctk.CTkLabel(tab_sys, text=f"📂 Daten-Pfad:\n{path}", justify="left", text_color="#1f6aa5").pack(anchor="w", padx=10, pady=(5, 15))
        
        # 1. Der Button für den Leerspulen-Manager
        ctk.CTkButton(tab_sys, text="📦 Leerspulen & Vorlagen verwalten", fg_color="#1f538d", command=lambda: SpoolManager(self)).pack(fill="x", padx=10, pady=(0, 15))

        # 2. Die Regal-Planung (Textfeld + Tool-Button)
        row_regal = ctk.CTkFrame(tab_sys, fg_color="transparent")
        row_regal.pack(fill="x", pady=8, padx=10)
        ctk.CTkLabel(row_regal, text="Regal-Layout:", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.ent_shelves = ctk.CTkEntry(row_regal, width=150)
        self.ent_shelves.pack(side="left", padx=(0, 5))
        self.ent_shelves.insert(0, str(self.settings.get("shelves", "REGAL|4|8")))
        
        def open_shelf_planner():
            def on_confirm(new_string):
                self.ent_shelves.delete(0, ctk.END)
                self.ent_shelves.insert(0, new_string)
            ShelfPlannerDialog(self, self.ent_shelves.get(), on_confirm)

        ctk.CTkButton(row_regal, text="🛠️ Planer", width=80, command=open_shelf_planner).pack(side="left")

        # --- SPEICHERN LOGIK ---
        def save_settings():
            self.settings["kwh_price"] = self.ent_kwh.get().replace(',', '.')
            self.settings["printer_watts"] = self.ent_watts.get()
            self.settings["wear_per_hour"] = self.ent_wear.get().replace(',', '.')
            self.settings["profit_margin"] = self.ent_margin.get()
            self.settings["shelves"] = self.ent_shelves.get()
            
            self.data_manager.save_settings(self.settings)
            options_win.destroy()
            
            # WICHTIG: Tabelle neu laden (falls sich Regal-Namen ändern)
            self.refresh_table()
            
        btn_save = ctk.CTkButton(options_win, text="💾 Einstellungen speichern", height=40, font=ctk.CTkFont(weight="bold"), command=save_settings)
        btn_save.pack(side="bottom", fill="x", padx=20, pady=(0, 20))
    
    def open_finance_panel(self):
        """Öffnet das moderne Finanz- und Kalkulations-Dashboard."""
        self.close_tool() # Nutzt die neue sichere Methode

        self.tool_panel = ctk.CTkFrame(self.main_frame, width=450, corner_radius=10, fg_color="#2b2b2b")
        self.tool_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0)) # SPALTE 1 !

        # --- HEADER ---
        header = ctk.CTkFrame(self.tool_panel, fg_color="transparent")
        header.pack(fill="x", pady=15, padx=20)
        ctk.CTkLabel(header, text="📊 Finanz-Dashboard", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="❌", width=30, fg_color="transparent", hover_color="#8b0000", command=self.close_tool).pack(side="right")
        
        # ... ab hier geht der restliche Code von open_finance_panel normal weiter ...

        content = ctk.CTkScrollableFrame(self.tool_panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=5)

        # --- 1. KPIs (Lagerwert & Gesamtgewicht) ---
        total_value = 0.0
        total_weight = 0.0
        from core.logic import calculate_net_weight
        
        for sp in self.inventory:
            if sp.get('type') == 'VERBRAUCHT': continue
            net = calculate_net_weight(sp.get('weight_gross', '0'), sp.get('spool_id', -1), self.spools, sp.get('empty_weight'))
            total_weight += net
            try:
                price = float(str(sp.get("price", "0")).replace(',', '.'))
                cap = float(str(sp.get("capacity", "1000")).replace(',', '.'))
                if cap > 0: total_value += (price / cap) * net
            except: pass

        kpi_frame = ctk.CTkFrame(content, fg_color="#1f538d", corner_radius=8)
        kpi_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(kpi_frame, text=f"Lagerwert: {total_value:.2f} €", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(pady=(15, 2))
        ctk.CTkLabel(kpi_frame, text=f"Aktuell {total_weight / 1000:.2f} kg Filament verfügbar", text_color="#d0d0d0").pack(pady=(0, 15))

        # --- 2. QUICK-COST RECHNER ---
        calc_frame = ctk.CTkFrame(content, corner_radius=8)
        calc_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(calc_frame, text="🧮 Quick-Cost Rechner", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        def add_calc_row(parent, label_text, default_val):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=label_text).pack(side="left")
            entry = ctk.CTkEntry(row, width=80, justify="right")
            entry.pack(side="right")
            entry.insert(0, default_val)
            return entry

        ent_calc_w = add_calc_row(calc_frame, "Gewicht (g):", "100")
        ent_calc_t = add_calc_row(calc_frame, "Druckzeit (h):", "2.5")
        ent_calc_p = add_calc_row(calc_frame, "Materialpreis (€/kg):", "25.00")

        lbl_result = ctk.CTkLabel(calc_frame, text="Kosten: 0.00 €", font=ctk.CTkFont(weight="bold", size=14), text_color="#2ecc71")
        lbl_result.pack(pady=15)

        def calculate_quick_costs(event=None):
            try:
                w = float(ent_calc_w.get().replace(',', '.'))
                t = float(ent_calc_t.get().replace(',', '.'))
                p = float(ent_calc_p.get().replace(',', '.'))

                kwh = float(self.settings.get("kwh_price", 0.30))
                watts = float(self.settings.get("printer_watts", 150))
                wear = float(self.settings.get("wear_per_hour", 0.20))
                margin = float(self.settings.get("profit_margin", 0))

                mat_cost = w * (p / 1000.0)
                energy_cost = t * (watts / 1000.0) * kwh
                wear_cost = t * wear

                total = mat_cost + energy_cost + wear_cost
                total_with_margin = total * (1 + (margin / 100.0))

                lbl_result.configure(text=f"Selbstkosten: {total:.2f} €\nVK-Preis (inkl. Marge): {total_with_margin:.2f} €")
            except:
                lbl_result.configure(text="Bitte gültige Zahlen eingeben!")

        # Live-Berechnung bei jedem Tastendruck!
        ent_calc_w.bind("<KeyRelease>", calculate_quick_costs)
        ent_calc_t.bind("<KeyRelease>", calculate_quick_costs)
        ent_calc_p.bind("<KeyRelease>", calculate_quick_costs)
        calculate_quick_costs() # Direkt einmal beim Öffnen ausrechnen

        # --- 3. DURCHSCHNITTSPREISE PRO MATERIAL ---
        avg_frame = ctk.CTkFrame(content, corner_radius=8)
        avg_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(avg_frame, text="📈 Durchschnittspreise (pro kg)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        prices_by_mat = {}
        for sp in self.inventory:
            if sp.get('type') == 'VERBRAUCHT': continue
            mat = sp.get("material", "Unbekannt")
            try:
                p = float(str(sp.get("price", "0")).replace(',', '.'))
                c = float(str(sp.get("capacity", "1000")).replace(',', '.'))
                if c > 0 and p > 0:
                    price_per_kg = p / (c / 1000.0)
                    if mat not in prices_by_mat: prices_by_mat[mat] = []
                    prices_by_mat[mat].append(price_per_kg)
            except: pass

        if not prices_by_mat:
            ctk.CTkLabel(avg_frame, text="Keine Preisdaten vorhanden", text_color="gray").pack(pady=10)
        else:
            for mat, prices in prices_by_mat.items():
                avg = sum(prices) / len(prices)
                row = ctk.CTkFrame(avg_frame, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(row, text=mat).pack(side="left")
                ctk.CTkLabel(row, text=f"~ {avg:.2f} €", text_color="#f39c12", font=ctk.CTkFont(weight="bold")).pack(side="right")
            
            # Ein bisschen Abstand nach unten
            ctk.CTkFrame(avg_frame, height=10, fg_color="transparent").pack()


    def open_cloud_panel(self):
        """Öffnet das moderne Cloud-Panel."""
        self.close_tool()

        # Etwas breiter (500) für eine bessere Darstellung!
        self.tool_panel = ctk.CTkFrame(self.main_frame, width=500, corner_radius=10, fg_color="#2b2b2b")
        self.tool_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0)) # SPALTE 1 !

        header = ctk.CTkFrame(self.tool_panel, fg_color="transparent")
        header.pack(fill="x", pady=15, padx=20)
        ctk.CTkLabel(header, text="☁️ Bambu Cloud", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="❌", width=30, fg_color="transparent", hover_color="#8b0000", command=self.close_tool).pack(side="right")

        self.cloud_content = ctk.CTkScrollableFrame(self.tool_panel, fg_color="transparent")
        self.cloud_content.pack(fill="both", expand=True, padx=10, pady=5)

        token = self.settings.get("bambu_token", "")
        if not token:
            self.show_cloud_login()
        else:
            self.load_cloud_jobs(token)

    def show_cloud_login(self):
        for widget in self.cloud_content.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self.cloud_content, text="Sicherer Login via Browser", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 10))
        ctk.CTkLabel(self.cloud_content, text="VibeSpool nutzt den offiziellen OAuth2-Login\nvon MakerWorld für maximale Sicherheit.", text_color="gray").pack(pady=(0, 20))

        def do_login():
            from core.bambu_cloud import BambuCloudAPI
            import threading
            api = BambuCloudAPI()
            
            def on_success(success, token_or_msg):
                if success:
                    self.settings["bambu_token"] = token_or_msg
                    self.data_manager.save_settings(self.settings)
                    self.root.after(0, lambda: self.load_cloud_jobs(token_or_msg))
                else:
                    from tkinter import messagebox
                    self.root.after(0, lambda: messagebox.showerror("Login Fehler", str(token_or_msg)))
                    
            threading.Thread(target=lambda: api.login_via_browser(on_success), daemon=True).start()

        ctk.CTkButton(self.cloud_content, text="🌐 Jetzt Anmelden", height=40, font=ctk.CTkFont(weight="bold"), command=do_login).pack()

    def load_cloud_jobs(self, token):
        for widget in self.cloud_content.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.cloud_content, text="Lade letzte Druckaufträge...", text_color="gray").pack(pady=30)

        def fetch():
            from core.bambu_cloud import BambuCloudAPI
            import threading
            api = BambuCloudAPI()
            api.set_auth_token(token)
            success, jobs = api.fetch_print_history(limit=15)
            self.root.after(0, lambda: self.render_cloud_jobs(success, jobs))
        
        import threading
        threading.Thread(target=fetch, daemon=True).start()

    def render_cloud_jobs(self, success, jobs):
        for widget in self.cloud_content.winfo_children(): widget.destroy()
        
        if not success:
            ctk.CTkLabel(self.cloud_content, text="Sitzung abgelaufen oder Netzwerkfehler.", text_color="#e74c3c").pack(pady=10)
            ctk.CTkButton(self.cloud_content, text="Neu Anmelden", command=self.show_cloud_login).pack()
            return

        if not jobs:
            ctk.CTkLabel(self.cloud_content, text="Keine Druckaufträge gefunden.").pack(pady=20)
            return

        deducted_jobs = self.settings.get("deducted_cloud_jobs", [])

        for job in jobs:
            job_id = str(job.get("id", ""))
            is_done = job_id in deducted_jobs
            
            # Moderne Kachel-Optik für jeden Druck
            card = ctk.CTkFrame(self.cloud_content, corner_radius=8, fg_color="#1e1e1e" if not is_done else "#1a2a1a")
            card.pack(fill="x", pady=5, padx=5)
            
            title = job.get("name", "Unbekannt")
            weight = job.get("weight", 0.0)
            date = job.get("date", "")
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(weight="bold"), anchor="w", wraplength=400).pack(fill="x", padx=10, pady=(10,2))
            ctk.CTkLabel(card, text=f"{date}  •  Verbrauch: {weight}g", text_color="gray", anchor="w").pack(fill="x", padx=10, pady=(0,10))
            
            if not is_done:
                btn = ctk.CTkButton(card, text="➖ Abziehen", width=120, height=28, fg_color="#1f538d", command=lambda j=job: self.open_smart_deduction(j))
                btn.pack(side="right", padx=10, pady=(0, 10))
            else:
                ctk.CTkLabel(card, text="✅ Berechnet", text_color="#2ecc71", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=10, pady=(0, 10))

    def open_smart_deduction(self, job):
        """Das Smart-Match Menü (Die Zeitmaschine) im Darkmode."""
        for widget in self.cloud_content.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self.cloud_content, text="🧠 Smart-Match", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ecc71").pack(pady=(10,5))
        ctk.CTkLabel(self.cloud_content, text=f"{job.get('name', 'Unbekannt')}\n\nVerbrauch: {job.get('weight', 0)}g", justify="center").pack(pady=(0, 20))
        
        from datetime import datetime
        import os, json
        
        best_spool_id = None
        job_date_str = job.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # --- DIE ZEITMASCHINE ---
        snap_file = os.path.join(getattr(self.data_manager, 'base_dir', ''), "ams_snapshots.json")
        if os.path.exists(snap_file):
            try:
                with open(snap_file, "r") as f: snaps = json.load(f)
                try: job_dt = datetime.strptime(job_date_str, "%Y-%m-%d %H:%M:%S")
                except: job_dt = datetime.now()
                
                closest_key, min_diff = None, None
                for snap_time_str in snaps.keys():
                    try:
                        snap_dt = datetime.strptime(snap_time_str, "%Y-%m-%d %H:%M:%S")
                        diff = abs((job_dt - snap_dt).total_seconds())
                        if min_diff is None or diff < min_diff:
                            min_diff = diff; closest_key = snap_time_str
                    except: pass
                    
                if closest_key:
                    snapshot_data = snaps[closest_key]
                    if snapshot_data:
                        best_spool_id = list(snapshot_data.values())[0] 
            except: pass

        # Dropdown füllen
        spool_list = []
        best_match_str = ""
        for s in self.inventory:
            if s.get('type') == 'VERBRAUCHT': continue
            display_str = f"[{s['id']}] {s.get('brand')} {s.get('color').split('(')[0].strip()}"
            spool_list.append(display_str)
            if best_spool_id and str(s['id']) == str(best_spool_id):
                best_match_str = display_str
                
        if not spool_list: spool_list = ["Keine Spulen verfügbar"]
        
        ctk.CTkLabel(self.cloud_content, text="Welche Spule wurde verwendet?", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)
        combo_spool = ctk.CTkComboBox(self.cloud_content, values=spool_list, width=350)
        combo_spool.pack(pady=5, padx=10, fill="x")
        
        if best_match_str: 
            combo_spool.set(best_match_str)
            ctk.CTkLabel(self.cloud_content, text="✨ Zeitmaschine hat diese Spule gefunden!", text_color="#f39c12", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10)
        elif spool_list: 
            combo_spool.set(spool_list[0])

        def confirm_deduction():
            sel = combo_spool.get()
            if not sel.startswith("["): return
            spool_id = sel.split("]")[0][1:]
            
            spool = next((i for i in self.inventory if str(i['id']) == spool_id), None)
            if spool:
                weight_to_deduct = float(job.get('weight', 0))
                old_gross = float(spool.get('weight_gross', 0.0))
                spool['weight_gross'] = max(0.0, old_gross - weight_to_deduct)
                
                if "history" not in spool: spool["history"] = []
                spool["history"].append({
                    "date": job_date_str,
                    "action": f"Cloud: {job.get('name', '')[:20]}...",
                    "change": f"-{weight_to_deduct}g",
                    "cost": "Abgerechnet" 
                })
                
                self.data_manager.save_inventory(self.inventory)
                self.refresh_table()
                
                # Job als erledigt markieren
                deducted = self.settings.get("deducted_cloud_jobs", [])
                deducted.append(str(job.get("id")))
                self.settings["deducted_cloud_jobs"] = deducted
                self.data_manager.save_settings(self.settings)
                
                self.load_cloud_jobs(self.settings.get("bambu_token", ""))

        ctk.CTkButton(self.cloud_content, text="✅ Jetzt Abziehen", height=40, font=ctk.CTkFont(weight="bold"), command=confirm_deduction).pack(pady=30, fill="x", padx=10)
        ctk.CTkButton(self.cloud_content, text="🔙 Zurück", fg_color="transparent", border_width=1, command=lambda: self.load_cloud_jobs(self.settings.get("bambu_token", ""))).pack(fill="x", padx=10)
    
    def open_paypal(self):
        import webbrowser
        webbrowser.open("https://paypal.me/florianfranck")

    def on_quick_scan(self, event=None):
        scan = self.entry_scan.get().strip()
        if not scan: return
        found_id = None

        if self.settings.get("rfid_mode", False):
            item = next((i for i in self.inventory if i.get('rfid') == scan), None)
            if item: found_id = str(item['id'])
        else:
            # Prio 1: Suche nach Hersteller-Barcode
            item = next((i for i in self.inventory if str(i.get('barcode', '')).lower() == scan.lower() and scan != ""), None)
            if item:
                found_id = str(item['id'])
            else:
                # Prio 2: Suche nach VibeSpool ID
                match = re.search(r'(?:ID|1D|lD|VibeSpool)[\s:=_\-\.]*([a-zA-Z0-9-]+)', scan, re.IGNORECASE)
                extracted_id = match.group(1) if match else scan
                item = next((i for i in self.inventory if str(i.get('id')).lower() == str(extracted_id).lower()), None)
                if item: found_id = str(item['id'])

        if found_id and self.tree.exists(found_id):
            self.tree.selection_set(found_id)
            self.tree.see(found_id)
            self.on_tree_double_click(None) # Öffnet direkt das Bearbeiten-Panel!
            self.entry_scan.delete(0, tk.END)
        else:
            messagebox.showerror("Fehler", f"Keine Spule mit {'RFID' if self.settings.get('rfid_mode') else 'ID / Barcode'} '{scan}' gefunden.", parent=self.root)
            self.entry_scan.delete(0, tk.END)

    def scan_qr_webcam(self):
        try:
            import cv2 # type: ignore
            from pyzbar import pyzbar # type: ignore
        except Exception as e:
            messagebox.showerror("Fehler", f"Scanner-Module konnten nicht geladen werden.\nDetails: {e}", parent=self.root)
            return
            
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened(): 
            messagebox.showerror("Fehler", "Kamera (Index 0) konnte nicht geöffnet werden.\nHast du eine Webcam angeschlossen?", parent=self.root)
            return
            
        win_name = "VibeSpool QR-Scanner (ESC zum Schließen)"
        found_id = None
        ret, frame = cap.read()
        
        if not ret or frame is None:
            messagebox.showerror("Kamera Fehler", "Die Kamera liefert kein Bild!\nBitte prüfe Windows Datenschutzeinstellungen.", parent=self.root)
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
                messagebox.showerror("DLL Fehler", f"Absturz beim Dekodieren.\n{e}", parent=self.root)
                break
                
            cv2.imshow(win_name, frame)
            if found_id or cv2.waitKey(1) & 0xFF == 27: break
                
        cap.release()
        cv2.destroyAllWindows()
        
        if found_id: 
            self.entry_scan.delete(0, tk.END)
            self.entry_scan.insert(0, found_id)
            self.on_quick_scan()

    def open_mobile_companion(self):
        from core.mobile_server import get_local_ip
        local_ip = get_local_ip()
        url = f"http://{local_ip}:8289"
        
        win = ctk.CTkToplevel(self.root)
        win.title("📱 Handy Scanner")
        win.geometry("450x550")
        win.attributes('-topmost', True)
        center_window(win, self.root)
        
        ctk.CTkLabel(win, text="Scanne diesen Code mit deinem Handy:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        from PIL import Image, ImageTk
        import qrcode
        from qrcode.image.pil import PilImage
        
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr_wrapper = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
        img = qr_wrapper.get_image().convert('RGB')
        
        photo = ImageTk.PhotoImage(img)
        lbl_img = tk.Label(win, image=photo, borderwidth=2, relief="solid")
        lbl_img.image = photo # type: ignore
        lbl_img.pack(pady=10)
        
        ctk.CTkLabel(win, text="Oder gib diese URL in deinen Handy-Browser ein:", text_color="gray").pack(pady=(20, 5))
        ent = ctk.CTkEntry(win, font=ctk.CTkFont(size=14, weight="bold"), justify="center")
        ent.insert(0, url)
        ent.configure(state="readonly")
        ent.pack(fill="x", padx=40, pady=5)
        
        ctk.CTkLabel(win, text="⚠️ Hinweis: PC und Handy müssen im selben WLAN sein!", text_color="#0078d7").pack(pady=10)

    def process_mobile_scan(self, code):
        self.entry_scan.delete(0, tk.END)
        self.entry_scan.insert(0, code)
        self.on_quick_scan()
        
    def process_unknown_scan(self, code):
        if hasattr(self, 'editor_panel') and self.editor_panel.winfo_exists():
            if "barcode" in self.form_vars:
                self.form_vars["barcode"].delete(0, ctk.END)
                self.form_vars["barcode"].insert(0, code)
                self.show_custom_toast("📱 Scanner", f"Barcode {code} eingetragen!")

    def process_mobile_action(self, spool_id, action, val):
        # FIX: Wir vergleichen beide als String, damit "42" == 42 funktioniert!
        item = next((i for i in self.inventory if str(i.get('id')) == str(spool_id)), None)
        if not item: return

        changes_made = False
        if action == "usage":
            try:
                used = float(str(val).replace(',', '.'))
                curr = float(str(item.get('weight_gross', '0')).replace(',', '.'))
                if used > 0 and curr > 0:
                    item['weight_gross'] = max(0, curr - used)
                    changes_made = True
                    
                    # LOGBUCH & STATISTIK EINTRAG
                    import datetime
                    if "history" not in item: item["history"] = []
                    item["history"].append({
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "action": "Handy-Abzug",
                        "change": f"-{used}g",
                        "cost": "-",
                        "sell_price": "-"
                    })
                    self.log_consumption(used)
                    
                    # UI-Update über den Main-Thread
                    self.root.after(0, lambda: self.show_custom_toast("📱 Handy-Sync", f"Es wurden {used}g von {item.get('brand', '')} abgezogen!"))
            except: pass
            
        elif action == "move":
            if "|" in val:
                target_type, target_loc = val.split("|", 1)
                item['type'] = target_type
                item['loc_id'] = target_loc
                changes_made = True
                self.root.after(0, lambda: self.show_custom_toast("📱 Handy-Sync", f"{item.get('brand', '')} wurde nach {target_type} verschoben!"))

        if changes_made:
            self.data_manager.save_inventory(self.inventory)
            # WICHTIG: UI-Updates MÜSSEN aus dem Hintergrund-Thread über .after() aufgerufen werden!
            self.root.after(0, self.refresh_table)
            self.root.after(0, self.broadcast_mqtt)

    def process_mobile_swap(self, spool_id_str, target_type, target_loc, col_item):
        s_a = next((i for i in self.inventory if str(i['id']) == str(spool_id_str)), None)
        if not s_a: return

        o_t, o_l = s_a.get('type', 'LAGER'), s_a.get('loc_id', '-')
        s_a['type'] = target_type
        s_a['loc_id'] = target_loc
        if col_item:
            col_item['type'] = o_t
            col_item['loc_id'] = o_l

        self.data_manager.save_inventory(self.inventory)
        self.root.after(0, self.refresh_table)
        self.root.after(0, lambda: self.show_custom_toast("🔄 Mobile Quick-Swap", f"{s_a.get('brand','')} ist im {target_type} Slot {target_loc}.\nDie alte Spule liegt jetzt in {o_t} {o_l}."))
    
    def on_shelf_drag_start(self, event, spool, loc_type, loc_id):
        self.drag_source_id = str(event.widget)
        self.drag_data = spool
        self.drag_start_loc = {"type": loc_type, "loc_id": loc_id}
        
        # Pylance-Safe: Wir speichern das Fenster in der Klasse
        self.drag_window = tk.Toplevel(self.root)
        self.drag_window.wm_overrideredirect(True)
        self.drag_window.attributes('-alpha', 0.8)
        
        if spool:
            from core.utils import get_colors_from_text
            cols = get_colors_from_text(spool.get('color', ''))
            bg_col = cols[0] if cols and cols[0].startswith('#') else "#1f538d"
            lbl_txt = f" {spool.get('brand', '')[:10]}\n{spool.get('color', '').split('(')[0][:10]} "
        else:
            bg_col = "#333333"
            lbl_txt = " LEER "

        lbl = tk.Label(self.drag_window, text=lbl_txt, bg=bg_col, fg="white" if bg_col != "#FFFFFF" else "black", font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=2)
        lbl.pack()
        self.drag_window.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

    def on_shelf_drag_motion(self, event):
        drag_win = getattr(self, 'drag_window', None)
        if drag_win is not None:
            drag_win.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

    def on_shelf_drag_release(self, event):
        drag_win = getattr(self, 'drag_window', None)
        if drag_win is not None:
            drag_win.destroy()
            self.drag_window = None
            
        target_widget = self.root.winfo_containing(event.x_root, event.y_root)
        
        # Pylance-Safe: Wir holen uns die Daten und speichern sie fest in lokalen Variablen!
        drag_src_id = getattr(self, 'drag_source_id', "")
        source_spool = getattr(self, 'drag_data', None)
        
        # --- KLICK ERKENNUNG (Maus wurde am selben Ort losgelassen) ---
        if target_widget and str(target_widget) == drag_src_id:
            if source_spool is not None:
                self.open_spool_panel(source_spool['id'])
            else:
                loc_info = getattr(self, 'drag_start_loc', {})
                if loc_info and loc_info.get("loc_id") != "-":
                    self.open_spool_panel(prefill_type=loc_info.get("type"), prefill_loc=loc_info.get("loc_id"))
            
            self.drag_data = None
            self.drag_source_id = None
            return

        # --- DRAG & DROP SWAP (Maus wurde über einem ANDEREN Fach losgelassen) ---
        # Wenn source_spool None ist, brechen wir sofort ab -> Pylance ist beruhigt!
        if source_spool is None: 
            self.drag_source_id = None
            return
            
        shelf_zones = getattr(self, 'shelf_drop_zones', {})
        if target_widget and str(target_widget) in shelf_zones:
            target_info = shelf_zones[str(target_widget)]
            t_type = target_info["type"]
            t_loc = target_info["loc_id"]
            t_spool = target_info["spool"] 
            
            s_type = source_spool.get("type", "LAGER")
            s_loc = source_spool.get("loc_id", "-")
            
            if s_type == t_type and s_loc == t_loc:
                self.drag_data = None
                self.drag_source_id = None
                return
                
            # Swap ausführen (Pylance weiß jetzt zu 100%, dass source_spool ein Dictionary ist)
            source_spool["type"] = t_type
            source_spool["loc_id"] = t_loc
            if t_spool is not None:
                t_spool["type"] = s_type
                t_spool["loc_id"] = s_loc
                
            self.data_manager.save_inventory(self.inventory)
            self.refresh_table()
            self.open_regal_panel() # Lädt das Regal sofort neu!
            
        self.drag_data = None
        self.drag_source_id = None
    
    def on_closing(self):
            """Wird aufgerufen, wenn das Fenster über das rote X geschlossen wird."""
            self.root.destroy()
            sys.exit(0)


# =================================================================
# --- SHOPPING LIST / EINKAUFSLISTE ---
# =================================================================
class ShoppingListDialog(ctk.CTkToplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(master=app_instance.root)
        self.app = app_instance
        self.inventory = inventory
        self.title("🛒 Einkaufsliste / Dashboard")
        self.geometry("900x650")
        self.attributes("-topmost", True)
        self.grab_set()
        
        from core.utils import center_window
        center_window(self, app_instance.root)
        
        ctk.CTkLabel(self, text="🛒 Nachzubestellende & Verbrauchte Filamente", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        # Buttons unten anheften
        btn_frm = ctk.CTkFrame(self, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", pady=20, padx=20)
        
        ctk.CTkButton(btn_frm, text="🔗 Im Shop öffnen", font=ctk.CTkFont(weight="bold"), command=self.open_shop_link).pack(side="left", padx=5)
        ctk.CTkButton(btn_frm, text="Als CSV exportieren", fg_color="#1f538d", command=self.export_csv).pack(side="left", padx=5)
        ctk.CTkButton(btn_frm, text="Schließen", fg_color="transparent", border_width=1, command=self.destroy).pack(side="right", padx=5)

        frm_list = ctk.CTkFrame(self, fg_color="transparent")
        frm_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.tree = ttk.Treeview(frm_list, columns=("brand", "color", "mat", "supplier", "sku", "price", "status"), show="headings")
        self.tree.heading("brand", text="Marke"); self.tree.heading("color", text="Farbe"); self.tree.heading("mat", text="Mat."); self.tree.heading("supplier", text="Lieferant"); self.tree.heading("sku", text="SKU"); self.tree.heading("price", text="Preis"); self.tree.heading("status", text="Status")
        self.tree.column("mat", width=60); self.tree.column("price", width=80); self.tree.column("status", width=120)
        
        scroll = ctk.CTkScrollbar(frm_list, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y", padx=(5,0))
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
        import webbrowser
        sel = self.tree.selection()
        if not sel: return messagebox.showinfo("Info", "Bitte ein Filament auswählen.", parent=self)
        item = next((x for x in self.inventory if str(x['id']) == str(sel[0])), None)
        if not item or not item.get('link'): return messagebox.showinfo("Info", "Für dieses Filament ist leider kein Link hinterlegt.", parent=self)
        
        url = item['link'].strip()
        url = url if url.startswith("http") else "https://" + url
        
        # --- AFFILIATE INJEKTION ---
        if self.app.settings.get("use_affiliate", True):
            url_lower = url.lower()
            if "bambulab.com" in url_lower and "modelid=" not in url_lower: 
                url += ("&" if "?" in url else "?") + "modelId=1889832"
            elif ("amazon." in url_lower or "amzn.to" in url_lower) and "tag=" not in url_lower:
                url += ("&" if "?" in url else "?") + "tag=metmeyoumetwe-21"
                
        webbrowser.open(url)

    def export_csv(self):
        import csv
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Einkaufsliste exportieren")
        if not filepath: return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f, delimiter=';').writerow(["Marke", "Farbe", "Material", "Lieferant", "SKU", "Preis", "Status", "Link"])
                for i in self.inventory:
                    if i.get('reorder') or i.get('type') == 'VERBRAUCHT': csv.writer(f, delimiter=';').writerow([i.get('brand',''), i.get('color',''), i.get('material',''), i.get('supplier',''), i.get('sku',''), i.get('price',''), "MUSS KAUFEN" if i.get('reorder') else "Leer", i.get('link','')])
            messagebox.showinfo("Exportiert", "Liste erfolgreich gespeichert!", parent=self)
        except Exception as e: messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}", parent=self)


# =================================================================
# --- STATISTICS / ANALYTICS DASHBOARD ---
# =================================================================
class StatisticsDialog(ctk.CTkToplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(master=app_instance.root)
        self.app = app_instance
        self.inventory = inventory
        self.title("📊 Analytics & Finanz-Dashboard")
        self.geometry("1300x850") 
        self.attributes("-topmost", True)
        self.grab_set()
        
        from core.utils import center_window
        center_window(self, app_instance.root)
        self.build_ui()

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Master Layout (für das Side-Panel)
        self.master_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.master_frame.pack(fill="both", expand=True)
        
        self.side_panel = ctk.CTkFrame(self.master_frame, width=350, corner_radius=0, fg_color="#1e1e1e", border_width=1, border_color="#333333")
        self.side_panel.pack_propagate(False)
        
        self.main_content = ctk.CTkFrame(self.master_frame, fg_color="transparent")
        self.main_content.pack(side="left", fill="both", expand=True)

        # 1. DATEN BERECHNEN
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

        # 2. OBERER BEREICH
        ctk.CTkLabel(self.main_content, text="💰 Bestands-Statistik & Finanzen", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(15, 5))
        main_frm = ctk.CTkFrame(self.main_content, fg_color="transparent")
        main_frm.pack(fill="x", padx=20, pady=5)
        
        left_panel = ctk.CTkFrame(main_frm, fg_color="transparent")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right_panel = ctk.CTkFrame(main_frm, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # 3. LINKE SEITE (KPIs)
        kpi_frame = ctk.CTkFrame(left_panel, corner_radius=10, fg_color="#1f538d")
        kpi_frame.pack(fill="x", pady=(0, 10))
        
        kpi_grid = ctk.CTkFrame(kpi_frame, fg_color="transparent")
        kpi_grid.pack(padx=20, pady=15, fill="x")
        
        ctk.CTkLabel(kpi_grid, text="Gesamtwert:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(kpi_grid, text=f"{total_value:.2f} €", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ecc71").grid(row=0, column=1, sticky="w", padx=20, pady=2)
        ctk.CTkLabel(kpi_grid, text="Lagermenge:", font=ctk.CTkFont(size=14)).grid(row=1, column=0, sticky="w", pady=2)
        ctk.CTkLabel(kpi_grid, text=f"{(total_weight/1000):.2f} kg", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=1, sticky="w", padx=20, pady=2)
        ctk.CTkLabel(kpi_grid, text="Aktive Spulen:", font=ctk.CTkFont(size=14)).grid(row=2, column=0, sticky="w", pady=2)
        ctk.CTkLabel(kpi_grid, text=str(total_spools), font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=1, sticky="w", padx=20, pady=2)

        ctk.CTkLabel(left_panel, text="Aufschlüsselung nach Material:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        tree_mat = ttk.Treeview(left_panel, columns=("mat", "count", "weight", "value", "avg"), show="headings", height=6)
        for col, head, w in zip(("mat", "count", "weight", "value", "avg"), ("Material", "Stk", "Gewicht", "Wert", "Ø Preis/kg"), (100, 40, 80, 80, 80)): 
            tree_mat.heading(col, text=head)
            tree_mat.column(col, width=w, anchor="center" if col != "mat" else "w")
        tree_mat.pack(fill="both", expand=True)
        
        for mat, stats in sorted(mat_stats.items(), key=lambda x: x[1]['value'], reverse=True): 
            kg = stats['weight'] / 1000
            avg_price = (stats['value'] / kg) if kg > 0 else 0
            tree_mat.insert("", "end", values=(mat, stats['count'], f"{kg:.2f} kg", f"{stats['value']:.2f} €", f"{avg_price:.2f} €"))

        # 4. RECHTE SEITE (Schickes Verbrauchs-Chart auf Canvas)
        ctk.CTkLabel(right_panel, text="Verbrauch der letzten 7 Tage:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
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
        
        c_width, c_height = 450, 280
        # Darkmode Canvas
        canvas = tk.Canvas(right_panel, width=c_width, height=c_height, bg="#1e1e1e", highlightthickness=1, highlightbackground="#333333")
        canvas.pack(fill="both", expand=True, pady=0)
        
        for i in range(4):
            y_line = 40 + i * ((c_height - 80) / 3)
            val_line = max_val - (i * (max_val / 3))
            canvas.create_line(40, y_line, c_width - 20, y_line, fill="#444444", dash=(4, 4))
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
            
            color = "#0078d7" if val > 0 else "#333333"
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            
            if val > 0:
                canvas.create_text(x0 + bar_width/2, y0 - 12, text=f"{int(val)}g", fill="#e0e0e0", font=("Segoe UI", 9, "bold"))
                
            day_obj = datetime.datetime.strptime(last_7_days[i], "%Y-%m-%d")
            day_name = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][day_obj.weekday()]
            font_w = ("Segoe UI", 10, "bold") if i == 6 else ("Segoe UI", 9)
            col_w = "#0078d7" if i == 6 else "gray"
            canvas.create_text(x0 + bar_width/2, c_height - 20, text=day_name, fill=col_w, font=font_w)

        total_7d = sum(values)
        ctk.CTkLabel(right_panel, text=f"Gesamtverbrauch (7 Tage): {total_7d:.1f} g", text_color="gray", font=ctk.CTkFont(slant="italic")).pack(anchor="e", pady=2)

        # 5. FOOTER BUTTONS
        btn_frm = ctk.CTkFrame(self.main_content, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", pady=20, padx=20)
        
        ctk.CTkButton(btn_frm, text="Schließen", fg_color="transparent", border_width=1, command=self.destroy).pack(side="right", padx=5)
        self.lbl_total = ctk.CTkLabel(btn_frm, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0078d7")
        self.lbl_total.pack(side="left")

        # 6. UNTERER BEREICH (Tabelle)
        ctk.CTkFrame(self.main_content, height=2, fg_color="#333333").pack(fill="x", padx=20, pady=10) # Separator
        
        hist_lbl_frm = ctk.CTkFrame(self.main_content, fg_color="transparent")
        hist_lbl_frm.pack(fill="x", padx=20, pady=(0, 5))
        ctk.CTkLabel(hist_lbl_frm, text="📜 Globale Druck-Historie", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkLabel(hist_lbl_frm, text="Alle protokollierten Verbräuche (Doppelklick zum Bearbeiten/Löschen)", text_color="gray").pack(side="left", padx=15)

        history_frm = ctk.CTkFrame(self.main_content, fg_color="transparent")
        history_frm.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        self.history_map = {}
        all_prints = []
        for item in self.inventory:
            hist = item.get("history", [])
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', '')).strip()
            spool_name = f"[{item.get('id', '?')}] {item.get('brand', '')} {color_clean}"
            
            for idx, h in enumerate(hist):
                all_prints.append({
                    "spool_id": item['id'], "hist_idx": idx, "date": h.get("date", ""),
                    "action": h.get("action", ""), "spool": spool_name, "change": h.get("change", ""),
                    "cost": h.get("cost", "-"), "sell": h.get("sell_price", "-")
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

        self.tree_hist.column("date", width=130); self.tree_hist.column("action", width=310); self.tree_hist.column("spool", width=240)
        self.tree_hist.column("change", width=80, anchor="e"); self.tree_hist.column("cost", width=80, anchor="e"); self.tree_hist.column("sell", width=80, anchor="e")
        
        scroll_hist = ctk.CTkScrollbar(history_frm, command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=scroll_hist.set)
        self.tree_hist.pack(side="left", fill="both", expand=True)
        scroll_hist.pack(side="right", fill="y", padx=(5,0))
        self.tree_hist.bind("<Double-1>", self.on_edit_entry)

        total_costs = 0.0
        for p in all_prints:
            iid = self.tree_hist.insert("", "end", values=(p["date"], p["action"], p["spool"], p["change"], p["cost"], p["sell"]))
            self.history_map[iid] = {"spool_id": p["spool_id"], "hist_idx": p["hist_idx"]}
            try:
                c_str = p["cost"].replace(" €", "").replace(",", ".")
                total_costs += float(c_str)
            except: pass

        self.lbl_total.configure(text=f"Gesamtkosten aller Einträge: {total_costs:.2f} €")

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
        
        # --- Side-Panel aktivieren ---
        for widget in self.side_panel.winfo_children(): widget.destroy()
        self.side_panel.pack(side="right", fill="y", before=self.main_content)
        
        header = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        header.pack(fill="x", pady=15, padx=15)
        ctk.CTkLabel(header, text="✏️ Eintrag bearbeiten", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="❌", width=30, fg_color="transparent", hover_color="#8b0000", command=self.side_panel.pack_forget).pack(side="right")
        
        frm = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=15)
        
        ctk.CTkLabel(frm, text="Aktion / Druckname:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,2))
        ent_action = ctk.CTkEntry(frm)
        ent_action.insert(0, entry.get("action", ""))
        ent_action.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frm, text="Verbrauch (inkl. Vorzeichen):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0,2))
        ent_change = ctk.CTkEntry(frm)
        ent_change.insert(0, entry.get("change", "").replace("g", "")) 
        ent_change.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frm, text="Kosten:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0,2))
        frm_cost = ctk.CTkFrame(frm, fg_color="transparent")
        frm_cost.pack(fill="x", pady=(0, 15))
        
        ent_cost = ctk.CTkEntry(frm_cost)
        ent_cost.insert(0, entry.get("cost", "-"))
        
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

        ctk.CTkButton(frm_cost, text="🧮 Mat.", width=60, command=calc_cost).pack(side="left", padx=(0, 10))
        ent_cost.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(frm, text="VK-Preis:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0,2))
        frm_sell = ctk.CTkFrame(frm, fg_color="transparent")
        frm_sell.pack(fill="x", pady=(0, 15))
        
        ent_sell = ctk.CTkEntry(frm_sell)
        ent_sell.insert(0, entry.get("sell_price", "-"))
        
        def calc_vk():
            try:
                cost_str = ent_cost.get().replace('€', '').replace(',', '.').strip()
                cost_val = float(cost_str) if cost_str and cost_str != '-' else 0.0
                margin = int(self.app.settings.get("profit_margin", 0))
                vk_val = cost_val * (1 + (margin / 100.0))
                ent_sell.delete(0, tk.END)
                ent_sell.insert(0, f"{vk_val:.2f} €")
                if margin == 0: messagebox.showinfo("Info", "Gewinnmarge ist 0%. VK = Kosten.", parent=self)
            except ValueError:
                messagebox.showerror("Fehler", "Bitte Kosten eintragen!", parent=self)
                
        ctk.CTkButton(frm_sell, text="🧮 Marge", width=60, command=calc_vk).pack(side="left", padx=(0, 10))
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
                
            if delta != 0.0:
                current_day_total = hist_data.get(date_str, 0.0)
                new_day_total = max(0.0, current_day_total - delta)
                hist_data[date_str] = round(new_day_total, 1)
                try:
                    with open(history_file, "w") as f: json.dump(hist_data, f, indent=4)
                except: pass
            
            self.app.data_manager.save_inventory(self.inventory)
            self.app.refresh_table()
            self.build_ui()

        def delete():
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

        btn_frm_action = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        btn_frm_action.pack(fill="x", pady=20, padx=15, side="bottom")
        ctk.CTkButton(btn_frm_action, text="🗑️", fg_color="#8b0000", hover_color="#5c0000", width=50, command=delete).pack(side="left", padx=5)
        ctk.CTkButton(btn_frm_action, text="💾 Speichern", font=ctk.CTkFont(weight="bold"), command=save).pack(side="right", fill="x", expand=True, padx=5)

# =================================================================
# --- LEERSPULEN MANAGER (SPOOL MANAGER) ---
# =================================================================
class SpoolManager(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(master=app.root)
        self.app = app
        self.title("📦 Leerspulen Datenbank")
        self.geometry("650x750")
        self.attributes("-topmost", True)
        self.grab_set()

        # Titel
        ctk.CTkLabel(self, text="Verfügbare Leerspulen & Gewichte", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 10))

        # --- TREEVIEW (Tabelle) ---
        frm_list = ctk.CTkFrame(self, fg_color="transparent")
        frm_list.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(frm_list, columns=("id", "name", "weight"), show="headings", style="Modern.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Bezeichnung")
        self.tree.heading("weight", text="Leergewicht (g)")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=300)
        self.tree.column("weight", width=120, anchor="center")

        scroll = ctk.CTkScrollbar(frm_list, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y", padx=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # --- EINGABEBEREICH ---
        frm_input = ctk.CTkFrame(self, corner_radius=10)
        frm_input.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(frm_input, text="Name:").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.ent_name = ctk.CTkEntry(frm_input, width=300)
        self.ent_name.grid(row=0, column=1, padx=15, pady=10, sticky="ew")

        ctk.CTkLabel(frm_input, text="Gewicht (g):").grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.ent_weight = ctk.CTkEntry(frm_input, width=300)
        self.ent_weight.grid(row=1, column=1, padx=15, pady=10, sticky="ew")

        frm_input.columnconfigure(1, weight=1)

        # --- BUTTONS ---
        frm_btns = ctk.CTkFrame(frm_input, fg_color="transparent")
        frm_btns.grid(row=2, column=0, columnspan=2, pady=15)

        ctk.CTkButton(frm_btns, text="➕ Neu anlegen", width=100, command=self.add_spool).pack(side="left", padx=5)
        ctk.CTkButton(frm_btns, text="💾 Speichern", width=100, command=self.update_spool).pack(side="left", padx=5)
        ctk.CTkButton(frm_btns, text="🗑️ Löschen", width=100, fg_color="#8b0000", hover_color="#5c0000", command=self.delete_spool).pack(side="left", padx=5)
        ctk.CTkButton(frm_btns, text="📋 Vorlagen", width=100, fg_color="#1f538d", command=self.import_preset).pack(side="left", padx=5)

        self.refresh_list()

    def import_preset(self):
        """Öffnet das Sub-Fenster für Vorlagen. 100% Original-Logik!"""
        win = ctk.CTkToplevel(self)
        win.title("📋 Spulen-Vorlagen")
        win.geometry("500x600")
        win.attributes("-topmost", True)
        win.grab_set()

        from core.spool_presets import SPOOL_PRESETS
        
        ctk.CTkLabel(win, text="Wähle eine Standardspule:", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=(15, 10))

        self.ent_search = ctk.CTkEntry(win, placeholder_text="🔍 Suche...")
        self.ent_search.pack(fill="x", padx=20, pady=(0, 10))

        # tk.Listbox ist hier wegen der Such-Geschwindigkeit besser, wird aber passend zum Darkmode gestylt!
        lb = tk.Listbox(win, font=("Segoe UI", 11), bg="#1e1e1e", fg="#e0e0e0", selectbackground="#1f538d", borderwidth=0, highlightthickness=0)
        lb.pack(fill="both", expand=True, padx=20, pady=5)

        self.filtered_presets = SPOOL_PRESETS.copy()

        def filter_list(*args):
            search_term = self.ent_search.get().lower()
            lb.delete(0, tk.END)
            self.filtered_presets = []
            for p in SPOOL_PRESETS:
                display_text = f"{p['name']} ({p['weight']}g)"
                if search_term in display_text.lower():
                    self.filtered_presets.append(p)
                    lb.insert(tk.END, display_text)

        self.ent_search.bind("<KeyRelease>", filter_list)
        filter_list()

        def do_import():
            sel = lb.curselection()
            if not sel: return
            p = self.filtered_presets[sel[0]] 
            self.ent_name.delete(0, ctk.END)
            self.ent_name.insert(0, p['name'])
            self.ent_weight.delete(0, ctk.END)
            self.ent_weight.insert(0, str(p['weight']))
            win.destroy()

        ctk.CTkButton(win, text="✅ Übernehmen", height=40, font=ctk.CTkFont(weight="bold"), command=do_import).pack(pady=20, fill="x", padx=20)

    def refresh_list(self):
        for item in self.tree.get_children(): 
            self.tree.delete(item)
        sorted_spools = sorted(self.app.spools, key=lambda s: s['name'].lower())
        for s in sorted_spools: 
            self.tree.insert("", "end", iid=str(s['id']), values=(s['id'], s['name'], s['weight']))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        spool_id = int(sel[0])
        spool = next((s for s in self.app.spools if s['id'] == spool_id), None)
        if spool:
            self.ent_name.delete(0, ctk.END)
            self.ent_name.insert(0, spool['name'])
            self.ent_weight.delete(0, ctk.END)
            self.ent_weight.insert(0, str(spool['weight']))

    def add_spool(self):
        name = self.ent_name.get().strip()
        weight_str = self.ent_weight.get().strip().replace(',', '.')
        if not name or not weight_str: return
        try:
            weight = int(float(weight_str))
            new_id = max([s['id'] for s in self.app.spools], default=0) + 1
            self.app.spools.append({"id": new_id, "name": name, "weight": weight})
            self.app.data_manager.save_spools(self.app.spools)
            self.refresh_list()
        except: pass

    def update_spool(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            weight = int(float(self.ent_weight.get().strip().replace(',', '.')))
            for s in self.app.spools:
                if s['id'] == int(sel[0]): 
                    s['name'] = self.ent_name.get().strip()
                    s['weight'] = weight
            self.app.data_manager.save_spools(self.app.spools)
            self.refresh_list()
        except: pass

    def delete_spool(self):
        sel = self.tree.selection()
        if not sel: return
        self.app.spools = [s for s in self.app.spools if s['id'] != int(sel[0])]
        self.app.data_manager.save_spools(self.app.spools)
        self.refresh_list()


# =================================================================
# --- REGAL PLANER (SHELF PLANNER) ---
# =================================================================
class ShelfPlannerDialog(ctk.CTkToplevel):
    def __init__(self, app, initial_value, on_confirm):
        super().__init__(master=app.root)
        self.app = app
        self.on_confirm = on_confirm
        self.title("🗄️ Regal-Planer")
        self.geometry("600x500")
        self.attributes("-topmost", True)
        self.grab_set()
        
        from core.logic import parse_shelves_string
        self.shelves = parse_shelves_string(initial_value) or [{"name": "REGAL", "rows": 4, "cols": 8}]
        self.current_idx = 0
        self._lock = False
        
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- LINKE SEITE (Liste & Buttons) ---
        left = ctk.CTkFrame(main, width=200, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(0, 20))
        
        ctk.CTkLabel(left, text="Regal-Liste:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.listbox = tk.Listbox(left, font=("Segoe UI", 11), bg="#1e1e1e", fg="#e0e0e0", selectbackground="#1f538d", borderwidth=0, highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        btn_frm = ctk.CTkFrame(left, fg_color="transparent")
        btn_frm.pack(fill="x", pady=5)
        ctk.CTkButton(btn_frm, text="➕ Neu", width=80, command=self.add_new).pack(side="left", expand=True, padx=(0,2))
        ctk.CTkButton(btn_frm, text="❌ Lösch", width=80, fg_color="#8b0000", hover_color="#5c0000", command=self.delete_current).pack(side="left", expand=True, padx=(2,0))
        
        # --- RECHTE SEITE (Einstellungen) ---
        right = ctk.CTkFrame(main, corner_radius=10)
        right.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(right, text="Konfiguration", font=ctk.CTkFont(weight="bold", size=16)).pack(anchor="w", pady=(15, 15), padx=20)
        
        ctk.CTkLabel(right, text="Regal Name:").pack(anchor="w", padx=20)
        self.ent_name = ctk.CTkEntry(right)
        self.ent_name.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(right, text="Anzahl Reihen (Höhe):").pack(anchor="w", padx=20)
        self.ent_rows = ctk.CTkEntry(right)
        self.ent_rows.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(right, text="Anzahl Spalten (Breite):").pack(anchor="w", padx=20)
        self.ent_cols = ctk.CTkEntry(right)
        self.ent_cols.pack(fill="x", padx=20, pady=(0, 15))
        
        # Initiale Daten laden
        self._lock = True
        self.refresh_listbox()
        if self.shelves:
            self.listbox.selection_set(0)
            self.current_idx = 0
            s = self.shelves[0]
            self.ent_name.insert(0, s['name'])
            self.ent_rows.insert(0, str(s['rows']))
            self.ent_cols.insert(0, str(s['cols']))
        self._lock = False
        
        # --- SPEICHERN ---
        ctk.CTkButton(self, text="💾 Konfiguration Speichern", height=40, font=ctk.CTkFont(weight="bold"), command=self.final).pack(pady=20, fill="x", padx=40)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for s in self.shelves: 
            self.listbox.insert(tk.END, f"📦 {s['name']} ({s['rows']}x{s['cols']})")

    def save_current(self):
        if self.current_idx < len(self.shelves):
            try:
                name = self.ent_name.get().strip().replace(",", "").replace("|", "") or "REGAL"
                rows = max(1, int(self.ent_rows.get()))
                cols = max(1, int(self.ent_cols.get()))
                self.shelves[self.current_idx] = {"name": name, "rows": rows, "cols": cols}
            except: pass

    def load_to_entries(self, s):
        self.ent_name.delete(0, ctk.END); self.ent_name.insert(0, s['name'])
        self.ent_rows.delete(0, ctk.END); self.ent_rows.insert(0, str(s['rows']))
        self.ent_cols.delete(0, ctk.END); self.ent_cols.insert(0, str(s['cols']))

    def on_select(self, e):
        if self._lock: return
        sel = self.listbox.curselection()
        if not sel: return
        self.save_current() 
        self._lock = True
        self.current_idx = sel[0]
        self.refresh_listbox()
        self.listbox.selection_set(self.current_idx)
        self.load_to_entries(self.shelves[self.current_idx])
        self.listbox.see(self.current_idx)
        self._lock = False

    def add_new(self): 
        self.save_current() 
        self.shelves.append({"name": f"REGAL {len(self.shelves)+1}", "rows": 4, "cols": 8})
        self._lock = True
        self.refresh_listbox()
        self.current_idx = len(self.shelves) - 1
        self.listbox.selection_set(self.current_idx)
        self.listbox.see(self.current_idx)
        self.load_to_entries(self.shelves[self.current_idx])
        self._lock = False

    def delete_current(self):
        if len(self.shelves) > 1: 
            del self.shelves[self.current_idx]
            self._lock = True
            self.current_idx = max(0, self.current_idx - 1)
            self.refresh_listbox()
            self.listbox.selection_set(self.current_idx)
            self.load_to_entries(self.shelves[self.current_idx])
            self._lock = False

    def final(self): 
        from core.logic import serialize_shelves
        self.save_current()
        res = serialize_shelves(self.shelves)
        self.on_confirm(res)
        self.destroy()  

# =================================================================
# --- FLOW KALIBRIERUNGS-RECHNER ---
# =================================================================
class FlowCalculatorDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_flow_entry=None):
        super().__init__(master=parent)
        self.current_flow_entry = current_flow_entry
        self.title("🧪 Flow-Rechner (Kalibrierung)")
        self.geometry("450x600")
        self.attributes("-topmost", True)
        self.grab_set()
        
        from core.utils import center_window
        center_window(self, parent)
        
        ctk.CTkLabel(self, text="Flow Kalibrierung", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(self, text="Gib hier deine Wandstärken-Messungen ein (eine pro Zeile):", text_color="gray").pack(padx=20, anchor="w", pady=(0, 10))
        
        # Modernes CTkTextbox statt altem tk.Text
        self.txt_measurements = ctk.CTkTextbox(self, height=150, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_measurements.pack(padx=20, pady=5, fill="x")
        self.txt_measurements.bind("<KeyRelease>", lambda e: self.calculate())

        frm_params = ctk.CTkFrame(self, fg_color="transparent")
        frm_params.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frm_params, text="Ziel-Wandstärke (mm):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.var_target = tk.StringVar(value="0.45")
        self.ent_target = ctk.CTkEntry(frm_params, textvariable=self.var_target, width=150)
        self.ent_target.grid(row=0, column=1, sticky="e", pady=5, padx=(20, 0))
        self.var_target.trace_add("write", lambda n, i, m: self.calculate())

        ctk.CTkLabel(frm_params, text="Bisheriger Flow:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=5)
        initial_flow = "0.98"
        if current_flow_entry and current_flow_entry.get(): initial_flow = current_flow_entry.get().replace(',', '.')
        
        self.var_old_flow = tk.StringVar(value=initial_flow)
        self.ent_old_flow = ctk.CTkEntry(frm_params, textvariable=self.var_old_flow, width=150)
        self.ent_old_flow.grid(row=1, column=1, sticky="e", pady=5, padx=(20, 0))
        self.var_old_flow.trace_add("write", lambda n, i, m: self.calculate())

        frm_params.columnconfigure(1, weight=1)
        
        ctk.CTkFrame(self, height=2, fg_color="#333333").pack(fill="x", padx=20, pady=15) # Separator
        
        self.lbl_result = ctk.CTkLabel(self, text="Mess-Durchschnitt: -", font=ctk.CTkFont(size=14))
        self.lbl_result.pack(pady=2)
        self.lbl_new_flow = ctk.CTkLabel(self, text="NEUER FLOW: -", font=ctk.CTkFont(size=20, weight="bold"), text_color="#0078d7")
        self.lbl_new_flow.pack(pady=10)
        
        btn_frm = ctk.CTkFrame(self, fg_color="transparent")
        btn_frm.pack(pady=20, fill="x", padx=20, side="bottom")
        
        ctk.CTkButton(btn_frm, text="Wert übernehmen", font=ctk.CTkFont(weight="bold"), command=self.apply_value).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frm, text="Schließen", fg_color="transparent", border_width=1, command=self.destroy).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def calculate(self):
        try:
            lines = self.txt_measurements.get("1.0", tk.END).strip().split('\n')
            vals = [float(l.replace(',', '.').strip()) for l in lines if l.strip()]
            if not vals: return
            
            avg = sum(vals) / len(vals)
            target = float(self.var_target.get().replace(',', '.'))
            old_flow = float(self.var_old_flow.get().replace(',', '.'))
            
            new_flow = (target / avg) * old_flow
            
            self.lbl_result.configure(text=f"Mess-Durchschnitt: {avg:.4f} mm ({len(vals)} Werte)")
            self.lbl_new_flow.configure(text=f"NEUER FLOW: {new_flow:.4f}")
            self.calculated_value = f"{new_flow:.3f}".replace('.', ',')
        except:
            self.lbl_result.configure(text="Mess-Durchschnitt: Fehler")
            self.lbl_new_flow.configure(text="NEUER FLOW: -")

    def apply_value(self):
        if hasattr(self, 'calculated_value') and self.current_flow_entry:
            self.current_flow_entry.delete(0, tk.END)
            self.current_flow_entry.insert(0, self.calculated_value)
            self.destroy()


# =================================================================
# --- BACKUP MANAGER ---
# =================================================================
class BackupDialog(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, app_instance):
        super().__init__(master=parent)
        self.data_manager = data_manager
        self.app = app_instance
        self.title("💾 Backup & Restore")
        self.geometry("400x250")
        self.attributes("-topmost", True)
        self.grab_set()
        
        from core.utils import center_window
        center_window(self, parent)
        
        ctk.CTkLabel(self, text="Datenbank Backup", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))
        
        ctk.CTkButton(self, text="📥 Backup exportieren", height=40, command=self.export_data).pack(fill="x", padx=40, pady=10)
        ctk.CTkButton(self, text="📤 Backup importieren", height=40, fg_color="#1f538d", command=self.import_data).pack(fill="x", padx=40, pady=10)
    
    def export_data(self):
        import zipfile
        fp = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP", "*.zip")], initialfile="VibeSpool_Backup.zip")
        if not fp: return
        try:
            base_d = getattr(self.data_manager, 'base_dir', '')
            hist_f = os.path.join(base_d, "history.json") if base_d else "history.json"
            mqtt_f = os.path.join(base_d, "mqtt_buffer.json") if base_d else "mqtt_buffer.json"
            ams_f = os.path.join(base_d, "ams_snapshots.json") if base_d else "ams_snapshots.json" 
            
            with zipfile.ZipFile(fp, 'w') as z:
                for f, n in [
                    (self.data_manager.data_file, "inventory.json"), 
                    (self.data_manager.settings_file, "settings.json"), 
                    (self.data_manager.spools_file, "spools.json"),
                    (getattr(self.data_manager, 'jobs_file', 'print_jobs.json'), "print_jobs.json"), 
                    (hist_f, "history.json"),
                    (mqtt_f, "mqtt_buffer.json"),
                    (ams_f, "ams_snapshots.json") 
                ]:
                    if os.path.exists(f): z.write(f, n)
            messagebox.showinfo("Erfolg", "Backup erstellt!", parent=self)
            self.destroy()
        except Exception as e: 
            messagebox.showerror("Fehler", str(e), parent=self)
    
    def import_data(self):
        import zipfile
        fp = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
        if not fp: return
        if messagebox.askyesno("Warnung", "Alle aktuellen Daten werden überschrieben!\nSoll das Backup wirklich geladen werden?", parent=self):
            try:
                with zipfile.ZipFile(fp, 'r') as z: z.extractall(self.data_manager.base_dir)
                
                # Wenn wir die App neu laden, tun wir das über die App Instanz
                if hasattr(self.app, 'refresh_all_data'):
                    self.app.refresh_all_data()
                elif hasattr(self.app, 'refresh_table'):
                    # Fallback für die neue Struktur
                    self.app.inventory, self.app.settings, self.app.spools = self.app.data_manager.load_all(DEFAULT_SETTINGS)
                    self.app.refresh_table()
                    
                messagebox.showinfo("Erfolg", "Backup erfolgreich geladen!", parent=self.app.root)
                self.destroy()
            except Exception as e: messagebox.showerror("Fehler", str(e), parent=self)


# =================================================================
# --- PRINTER JOB DIALOG (Historie auswählen) ---
# =================================================================
class PrinterJobDialog(ctk.CTkToplevel):
    def __init__(self, parent, jobs, on_select_job):
        super().__init__(master=parent)
        self.on_select_job = on_select_job
        self.title("Drucker-Historie")
        self.geometry("650x500")
        self.attributes("-topmost", True)
        self.grab_set()
        
        from core.utils import center_window
        center_window(self, parent)
        
        ctk.CTkLabel(self, text="Wähle einen Druckauftrag aus:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.tree = ttk.Treeview(frm, columns=("file", "status", "used"), show="headings")
        self.tree.heading("file", text="Datei")
        self.tree.heading("status", text="Status")
        self.tree.heading("used", text="Verbrauch (g)")
        self.tree.column("file", width=350)
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("used", width=120, anchor="center")
        
        scroll = ctk.CTkScrollbar(frm, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y", padx=(5,0))
        
        for i, j in enumerate(jobs):
            used = f"{j.get('filament_used', 0):.1f}g"
            self.tree.insert("", "end", iid=str(i), values=(j.get('filename', 'Unbekannt'), j.get('status', '-'), used))
        
        def confirm():
            sel = self.tree.selection()
            if not sel: return
            job = jobs[int(sel[0])]
            self.on_select_job(job.get('filament_used', 0))
            self.destroy()
            
        btn_frm = ctk.CTkFrame(self, fg_color="transparent")
        btn_frm.pack(fill="x", pady=20, padx=20, side="bottom")
        
        ctk.CTkButton(btn_frm, text="Diesen Verbrauch abziehen", height=40, font=ctk.CTkFont(weight="bold"), command=confirm).pack(fill="x")


# =================================================================
# --- SYSTEM TRAY ICON ---
# =================================================================
def create_tray_icon():
    from PIL import Image, ImageDraw
    # Zeichnet einen simplen blauen Kreis als Platzhalter-Icon für die Taskleiste
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(0, 120, 215))
    return image


# =================================================================
# --- MANUELLER DRUCK PROTOKOLLIEREN ---
# =================================================================
class ManualPrintDialog(ctk.CTkToplevel):
    def __init__(self, parent, spool_item, settings, callback):
        super().__init__(master=parent)
        self.spool = spool_item
        self.settings = settings
        self.callback = callback
        
        self.title("✍️ Manuellen Druck protokollieren")
        self.geometry("450x550")
        self.attributes('-topmost', True)
        self.grab_set()
        
        from core.utils import center_window
        center_window(self, parent)

        ctk.CTkLabel(self, text="Druck-Details eingeben", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=20, padx=20)

        lbl_frame = ctk.CTkFrame(self, fg_color="transparent")
        lbl_frame.pack(fill="both", expand=True, padx=30)

        ctk.CTkLabel(lbl_frame, text="Name des Drucks (z.B. Benchy):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        self.ent_name = ctk.CTkEntry(lbl_frame, height=35)
        self.ent_name.insert(0, "Manueller Druck")
        self.ent_name.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(lbl_frame, text="Verbrauch in Gramm (g):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.ent_weight = ctk.CTkEntry(lbl_frame, height=35)
        self.ent_weight.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(lbl_frame, text="Druckdauer in Stunden (h) - Optional:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.ent_time = ctk.CTkEntry(lbl_frame, height=35)
        self.ent_time.insert(0, "0")
        self.ent_time.pack(fill="x", pady=(0, 20))

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
                price_str = str(self.spool.get('price', '0')).replace(',', '.').replace('€', '').strip()
                price = float(price_str) if price_str else 0.0
                
                cap_str = str(self.spool.get('capacity', '1000')).strip()
                cap = float(cap_str) if cap_str else 1000.0
                
                mat_cost = weight * (price / cap) if cap > 0 else 0.0
                
                # Stromkosten
                kwh_price = float(self.settings.get("kwh_price", 0.30))
                watts = int(self.settings.get("printer_watts", 150))
                elec_cost = hours * (watts / 1000.0) * kwh_price
                
                # Maschinenverschleiß
                wear_price = float(self.settings.get("wear_per_hour", 0.20))
                wear_cost = hours * wear_price
                
                # ECHTE Gesamtkosten
                total_cost = mat_cost + elec_cost + wear_cost
                
                # Optionale Gewinnmarge
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
                
                # Wir geben Gewicht, Name, Kosten UND Verkaufspreis zurück
                self.callback(weight, name, f"{total_cost:.2f} €", f"{sell_price:.2f} €")
                self.destroy()
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Fehler", "Bitte gültige Zahlen für Gewicht und Zeit eingeben!", parent=self)

        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="transparent", border_width=1, command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="💾 Druck speichern", font=ctk.CTkFont(weight="bold"), command=on_confirm).pack(side="right", expand=True, fill="x", padx=(5, 0))


if __name__ == "__main__":
    # Verhindert den Mehrfach-Start
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(('127.0.0.1', 47200))
    except socket.error:
        sys.exit()

    # WICHTIG: Das Fenster wird jetzt als CTk() Objekt geladen, nicht als Tk()
    root = ctk.CTk()
    app = FilamentApp(root)
    root.mainloop()