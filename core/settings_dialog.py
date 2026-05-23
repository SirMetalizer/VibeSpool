# core/settings_dialog.py

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import os
import re
from core.utils import center_window, ScrollableFrame
from core.logic import parse_shelves_string, serialize_shelves
from core.constants import (
    DEFAULT_SETTINGS, MATERIALS, SUBTYPES, COMMON_COLORS, THEMES,
    COLOR_ACCENT, COLOR_DELETE, FONT_MAIN, FONT_BOLD
)

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, on_save, start_tab=0, app_instance=None):
        super().__init__(parent)
        self.configure(bg=parent.cget('bg'))
        self.data_manager = data_manager
        self.on_save = on_save
        self.app = app_instance
        _, self.settings, _ = self.data_manager.load_all(DEFAULT_SETTINGS)
        self.title("VibeSpool Einstellungen") 
        self.geometry("950x650") 
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

        # Rechte Seite: Das Side-Panel (Initial versteckt)
        self.side_panel = ttk.Frame(self.main_paned, width=350, relief="solid", borderwidth=1)
        self.side_panel.pack_propagate(False)
        self.side_panel_open = False
        self.current_side_title = ""
        
        # TAB 1: LAGER
        tab_lager = ttk.Frame(self.nb, padding=15)
        self.nb.add(tab_lager, text="📦 Lager")
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

        f_names = ttk.Frame(tab_lager)
        f_names.pack(fill="x", pady=5)
        ttk.Label(f_names, text="Reihen-Name:").grid(row=0, column=0, sticky="w")
        self.ent_row = ttk.Entry(f_names, width=15)
        self.ent_row.insert(0, self.settings.get("label_row", "Fach"))
        self.ent_row.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        ttk.Label(f_names, text="Spalten-Name:").grid(row=1, column=0, sticky="w")
        self.ent_col = ttk.Entry(f_names, width=15)
        self.ent_col.insert(0, self.settings.get("label_col", "Slot"))
        self.ent_col.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        
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
        tab_prn = ttk.Frame(self.nb, padding=15)
        self.nb.add(tab_prn, text="🤖 Drucker")
        
        # Moonraker Bereich
        ttk.Label(tab_prn, text="Klipper / Moonraker", font=FONT_BOLD).pack(anchor="w")
        self.var_moonraker = tk.BooleanVar(value=self.settings.get("use_moonraker", False))
        ttk.Checkbutton(tab_prn, text="Moonraker-Sync im Hauptfenster anzeigen", variable=self.var_moonraker).pack(anchor="w", pady=(5, 5))
        self.ent_prn_url = ttk.Entry(tab_prn)
        self.ent_prn_url.insert(0, self.settings.get("printer_url", ""))
        self.ent_prn_url.pack(fill="x", pady=2)
        
        ttk.Separator(tab_prn, orient="horizontal").pack(fill="x", pady=15)
        
        # NEU: AMS Anzahl im Drucker-Tab
        ttk.Label(tab_prn, text="Anzahl AMS Einheiten:", font=FONT_BOLD).pack(anchor="w")
        self.ent_ams = ttk.Entry(tab_prn, width=10)
        self.ent_ams.insert(0, str(self.settings.get("num_ams", 1)))
        self.ent_ams.pack(anchor="w", pady=(2, 10))
        
        # NEU: Bambu Lab Bereich
        ttk.Label(tab_prn, text="Bambu Lab AMS (via MQTT)", font=FONT_BOLD).pack(anchor="w")
        self.var_bambu = tk.BooleanVar(value=self.settings.get("use_bambu", False))
        ttk.Checkbutton(tab_prn, text="Bambu AMS Live-Sync aktivieren", variable=self.var_bambu).pack(anchor="w", pady=(5, 5))
        
        ttk.Label(tab_prn, text="Drucker IP-Adresse:").pack(anchor="w", pady=(5,0))
        self.ent_bambu_ip = ttk.Entry(tab_prn)
        self.ent_bambu_ip.insert(0, self.settings.get("bambu_ip", ""))
        self.ent_bambu_ip.pack(fill="x", pady=2)
        ttk.Label(tab_prn, text="Access Code (LAN):").pack(anchor="w", pady=(5,0))
        self.ent_bambu_acc = ttk.Entry(tab_prn)
        self.ent_bambu_acc.insert(0, self.settings.get("bambu_access", ""))
        self.ent_bambu_acc.pack(fill="x", pady=2)
        ttk.Label(tab_prn, text="Seriennummer:").pack(anchor="w", pady=(5,0))
        self.ent_bambu_ser = ttk.Entry(tab_prn)
        self.ent_bambu_ser.insert(0, self.settings.get("bambu_serial", ""))
        self.ent_bambu_ser.pack(fill="x", pady=2)
        
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
        tab_sys = ttk.Frame(self.nb, padding=15)
        self.nb.add(tab_sys, text="⚙ System")
        self.var_affiliate = tk.BooleanVar(value=self.settings.get("use_affiliate", True))
        ttk.Checkbutton(tab_sys, text="Entwickler unterstützen (Affiliate)", variable=self.var_affiliate).pack(anchor="w", pady=2)
        self.var_rfid = tk.BooleanVar(value=self.settings.get("rfid_mode", False))
        ttk.Checkbutton(tab_sys, text="RFID-Reader Modus aktiv", variable=self.var_rfid).pack(anchor="w", pady=2)
        
        ttk.Separator(tab_sys, orient="horizontal").pack(fill="x", pady=10)
        
        # --- NEU: Echten Standard-Pfad ermitteln und anzeigen ---
        default_path = getattr(self.data_manager, 'base_dir', os.getcwd())
        custom_path = self.settings.get("custom_db_path", "")
        
        path_show = custom_path if custom_path else f"{default_path} (Standard)"
        
        self.lbl_path = ttk.Label(tab_sys, text=f"Daten-Pfad:\n{path_show}", font=("Segoe UI", 8, "italic"), wraplength=450)
        self.lbl_path.pack(fill="x", pady=5)
        
        p_btn_frm = ttk.Frame(tab_sys)
        p_btn_frm.pack(fill="x", pady=5)
        
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
        self.ent_mqtt_host = ttk.Entry(frm_mqtt, width=25)
        self.ent_mqtt_host.insert(0, self.settings.get("mqtt_host", ""))
        self.ent_mqtt_host.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(frm_mqtt, text="Port:").grid(row=1, column=0, sticky="w", pady=2)
        self.ent_mqtt_port = ttk.Entry(frm_mqtt, width=10)
        self.ent_mqtt_port.insert(0, self.settings.get("mqtt_port", "1883"))
        self.ent_mqtt_port.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(frm_mqtt, text="Benutzer:").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_mqtt_user = ttk.Entry(frm_mqtt, width=25)
        self.ent_mqtt_user.insert(0, self.settings.get("mqtt_user", ""))
        self.ent_mqtt_user.grid(row=2, column=1, sticky="w", padx=5)
        
        ttk.Label(frm_mqtt, text="Passwort:").grid(row=3, column=0, sticky="w", pady=2)
        self.ent_mqtt_pass = ttk.Entry(frm_mqtt, width=25, show="*")
        self.ent_mqtt_pass.insert(0, self.settings.get("mqtt_pass", ""))
        self.ent_mqtt_pass.grid(row=3, column=1, sticky="w", padx=5)
        
        # Initialer Zustand der Checkbox
        if self.var_mqtt.get(): 
            frm_mqtt.pack(fill="x", pady=5)

        # TAB 5: LISTEN (Materialien & Farben)
        tab_lists = ttk.Frame(self.nb, padding=15)
        self.nb.add(tab_lists, text="📋 Listen")
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
            
            # Aktuelle Daten laden
            current_data = self.settings.get(key, default_list)
            self.list_vars[key] = current_data.copy()
            for item in self.list_vars[key]: 
                lb.insert(tk.END, item)
            
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
                if hasattr(app, 'update_slot_dropdown'):
                    app.update_slot_dropdown()
                
            messagebox.showinfo("Erfolg", f"Raster-Namen für '{target_name}' gespeichert!\n\n{changes_made} Spulen wurden automatisch umgebucht.", parent=self)
            self.toggle_side_panel(force_close=True)

        ttk.Button(parent, text="💾 Namen übernehmen & Speichern", style="Accent.TButton", command=save).pack(fill="x")

    def refresh_settings_shelf_list(self):
        self.shelf_list.delete(0, tk.END)
        for s in parse_shelves_string(self.var_shelves.get()): 
            self.shelf_list.insert(tk.END, f"📦 {s['name']} ({s['rows']}x{s['cols']})")

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

            # --- NEU: Finanzen auslesen ---
            try: kwh_val = float(self.ent_kwh.get().replace(',', '.'))
            except: kwh_val = 0.30
            try: watts_val = int(self.ent_watts.get())
            except: watts_val = 150
            try: wear_val = float(self.ent_wear.get().replace(',', '.'))
            except: wear_val = 0.0
            try: margin_val = int(self.ent_margin.get())
            except: margin_val = 0

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
            
            if app_inst:
                app_inst.refresh_table() 
                if hasattr(app_inst, 'update_slot_dropdown'):
                    app_inst.update_slot_dropdown()
                if hasattr(app_inst, 'shelf_visualizer') and app_inst.shelf_visualizer:
                    app_inst.shelf_visualizer.redraw()
                if self.settings.get("use_bambu_cloud", True):
                    app_inst.btn_cloud.pack(fill="x")
                else:
                    app_inst.btn_cloud.pack_forget()
                
            self.destroy()
            
        except ValueError: 
            messagebox.showerror("Fehler", "AMS Anzahl muss eine Zahl sein.", parent=self)
        except Exception as e:
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{e}", parent=self)
