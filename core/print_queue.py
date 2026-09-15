import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
from datetime import datetime
from core.utils import center_window, ScrollableFrame
import re

def decimal_to_hm(decimal_hours):
    try:
        val = float(decimal_hours)
    except:
        val = 0.0
    h = int(val)
    m = int(round((val - h) * 60))
    if m >= 60:
        h += 1
        m -= 60
    return h, m

def hm_to_decimal(h_str, m_str):
    try:
        h = int(h_str) if str(h_str).strip() else 0
    except:
        h = 0
    try:
        m = int(m_str) if str(m_str).strip() else 0
    except:
        m = 0
    return h + (m / 60.0)

def safe_float(value, default=0.0):
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", ".").strip())
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        return int(float(str(value).replace(",", ".").strip()))
    except (ValueError, TypeError):
        return default

class JobImageViewerDialog(tk.Toplevel):
    def __init__(self, parent, img_path, title="Modell-Bild"):
        super().__init__(parent)
        self.title(f"🔍 Bildvorschau: {title}")
        self.configure(bg=parent.cget('bg'))
        self.transient(parent)
        self.grab_set()
        
        ttk.Label(self, text=title, font=("Segoe UI", 12, "bold")).pack(pady=(12, 4))
        
        self.photo = None
        try:
            from PIL import Image, ImageTk
            img = Image.open(img_path)
            orig_w, orig_h = img.size
            max_w, max_h = 750, 550
            ratio = min(max_w / orig_w, max_h / orig_h, 1.0)
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            
            resample_filter = getattr(Image, "Resampling", Image).LANCZOS
            img_resized = img.resize((new_w, new_h), resample_filter)
            self.photo = ImageTk.PhotoImage(img_resized)
            
            lbl_img = tk.Label(self, image=self.photo, bg=parent.cget('bg'), relief="solid", borderwidth=1)
            lbl_img.pack(padx=20, pady=8)
            
            lbl_dim = ttk.Label(self, text=f"Auflösung: {orig_w} × {orig_h} px", font=("Segoe UI", 9), foreground="gray")
            lbl_dim.pack(pady=(0, 8))
        except Exception as e:
            tk.Label(self, text=f"Fehler beim Laden des Bildes:\n{e}", fg="red").pack(padx=20, pady=20)
            
        btn_frm = ttk.Frame(self, padding=10)
        btn_frm.pack(fill="x", side="bottom")
        
        def open_system():
            try:
                os.startfile(img_path)
            except Exception:
                webbrowser.open(img_path)
                
        ttk.Button(btn_frm, text="🖼️ In Windows-Fotoanzeige öffnen", command=open_system).pack(side="left", padx=5)
        ttk.Button(btn_frm, text="Schließen", command=self.destroy, style="Accent.TButton").pack(side="right", padx=5)
        
        center_window(self, parent)

class JobDeductionDialog(tk.Toplevel):
    def __init__(self, parent, queue_dialog, job, matched_spools):
        super().__init__(parent)
        self.queue_dialog = queue_dialog
        self.app = queue_dialog.app
        self.job = job
        self.matched_spools = matched_spools
        
        self.title("✅ Auftrag abschließen & Abziehen")
        self.geometry("600x550")
        self.configure(bg=parent.cget('bg'))
        self.transient(parent)
        self.grab_set()
        center_window(self, parent)
        
        self.build_ui()
 
    def build_ui(self):
        qty = safe_int(self.job.get('quantity', 1), 1)
        if qty < 1: qty = 1
        qty_txt = f" ({qty} Stk.)" if qty > 1 else ""
        ttk.Label(self, text=f"Auftrag: {self.job.get('title', 'Unbekannt')}{qty_txt}", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        # Pack footer (buttons) first at the bottom so they are always visible
        btn_frm = ttk.Frame(self, padding=10)
        btn_frm.pack(fill="x", side="bottom")
        
        ttk.Button(btn_frm, text="Abbrechen", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frm, text="💾 Speichern & Abziehen", style="Accent.TButton", command=self.process_deduction).pack(side="right", padx=5)

        # Pack scrollable content frame to fill the remaining space in the middle
        sf = ScrollableFrame(self)
        sf.pack(fill="both", expand=True, padx=20, pady=5)
        
        frm = ttk.Frame(sf.inner)
        frm.pack(fill="both", expand=True)
        
        time_label_text = "⏱️ Gesamte Druckzeit (Gesamt):" if qty > 1 else "⏱️ Gesamte Druckzeit:"
        ttk.Label(frm, text=time_label_text).pack(anchor="w")
        time_frm = ttk.Frame(frm)
        time_frm.pack(fill="x", pady=(0, 15))
        
        self.ent_hours = ttk.Entry(time_frm, width=8)
        self.ent_hours.pack(side="left")
        ttk.Label(time_frm, text="Std").pack(side="left", padx=(2, 10))
        
        self.ent_mins = ttk.Entry(time_frm, width=8)
        self.ent_mins.pack(side="left")
        ttk.Label(time_frm, text="Min").pack(side="left", padx=2)
        
        planned_time = safe_float(self.job.get('print_time'), 1.0) * qty
        h, m = decimal_to_hm(planned_time)
        self.ent_hours.insert(0, str(h))
        self.ent_mins.insert(0, str(m))
        
        weight_header = f"⚖️ Gesamtverbrauch pro Spule ({qty} Stk., in Gramm):" if qty > 1 else "⚖️ Verbrauch pro Spule (in Gramm):"
        ttk.Label(frm, text=weight_header, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        est_weight_str = self.job.get('est_weight', '0')
        try:
            est_weight_val = float(est_weight_str.replace(',', '.')) if est_weight_str else 0.0
        except:
            est_weight_val = 0.0
            
        weight_per_spool = 0.0
        if len(self.matched_spools) > 0 and est_weight_val > 0:
            weight_per_spool = round(est_weight_val / len(self.matched_spools), 1)

        self.spool_entries = {}
        planned_weights = self.job.get('spool_weights', {})
        for sp in self.matched_spools:
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=2)
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', sp.get('color', '')).strip()
            lbl_text = f"[{sp['id']}] {sp.get('brand','')} {color_clean}:"
            ttk.Label(row, text=lbl_text, width=35).pack(side="left")
            
            ent = ttk.Entry(row, width=10)
            # Pre-fill with planned spool weight multiplied by quantity
            sp_id_str = str(sp['id'])
            planned_w_val = None
            if planned_weights:
                planned_w_val = planned_weights.get(sp_id_str)
                if planned_w_val is None:
                    try:
                        planned_w_val = planned_weights.get(int(sp_id_str))
                    except (ValueError, TypeError):
                        pass
            if planned_w_val is None:
                planned_w = str(weight_per_spool) if weight_per_spool > 0 else '0'
            else:
                total_spool_w = round(safe_float(planned_w_val) * qty, 1)
                planned_w = str(total_spool_w)
            if planned_w.endswith(".0"):
                planned_w = planned_w[:-2]
            ent.insert(0, planned_w)
            ent.pack(side="right")
            ttk.Label(row, text="g").pack(side="right", padx=5)
            self.spool_entries[sp['id']] = ent

    def process_deduction(self):
        try:
            duration = hm_to_decimal(self.ent_hours.get(), self.ent_mins.get())
            
            weights = {}
            total_weight = 0.0
            for sp_id, ent in self.spool_entries.items():
                w = float(ent.get().replace(",", "."))
                weights[sp_id] = w
                total_weight += w
                
            if total_weight <= 0:
                messagebox.showwarning("Fehler", "Der Gesamtverbrauch muss größer als 0 sein!", parent=self)
                return
                
            # Kosten-Parameter aus Settings holen
            kwh_price = safe_float(self.app.settings.get("kwh_price"), 0.30)
            
            # Drucker-spezifische Werte holen
            printer_id = self.job.get("printer_id", "")
            printers = self.app.settings.get("printers", [])
            printer = next((p for p in printers if p.get("id") == printer_id), None)
            
            watts = 150
            if printer and printer.get("printer_watts") not in (None, ""):
                watts = safe_int(printer.get("printer_watts"), 150)
            else:
                watts = safe_int(self.app.settings.get("printer_watts"), 150)
                
            wear_price = 0.20
            if printer and printer.get("wear_per_hour") not in (None, ""):
                wear_price = safe_float(printer.get("wear_per_hour"), 0.20)
            else:
                wear_price = safe_float(self.app.settings.get("wear_per_hour"), 0.20)
                
            margin_percent = safe_int(self.app.settings.get("profit_margin"), 0)
            
            strom_gesamt = duration * (watts / 1000.0) * kwh_price
            wear_gesamt = duration * wear_price
            
            # Für jede Spule einzeln berechnen und abziehen
            for sp in self.matched_spools:
                w_val = weights[sp['id']]
                if w_val <= 0: continue
                
                # Materialkosten
                mat_cost = 0.0
                try:
                    price = float(str(sp.get('price', '0')).replace(',', '.'))
                    cap = float(str(sp.get('capacity', '1000')))
                    if cap > 0: mat_cost = w_val * (price / cap)
                except: pass
                
                anteil = w_val / total_weight
                echte_kosten = mat_cost + (strom_gesamt * anteil) + (wear_gesamt * anteil)
                vk_preis = echte_kosten * (1 + (margin_percent / 100.0))
                
                # Brutto reduzieren
                old_gross = float(sp.get('weight_gross', 0))
                sp['weight_gross'] = max(0, old_gross - w_val)
                
                # Logbuch
                if "history" not in sp: sp["history"] = []
                sp["history"].append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": f"Auftrag: {self.job.get('title', '')}",
                    "change": f"-{w_val}g",
                    "cost": f"{echte_kosten:.2f} €",
                    "sell_price": f"{vk_preis:.2f} €" if margin_percent > 0 else "-"
                })
                
                # Globales Logbuch (falls vorhanden)
                if hasattr(self.app, 'log_consumption'):
                    self.app.log_consumption(w_val)
                    
            # Speichern
            self.app.data_manager.save_inventory(self.app.inventory)
            if hasattr(self.app, 'refresh_table'): self.app.refresh_table()
            
            # Job als Erledigt markieren
            self.job['status'] = "Erledigt ✅"
            self.queue_dialog.save_jobs_and_sync()
            self.queue_dialog.refresh_list()
            self.queue_dialog.reset_form()
            
            messagebox.showinfo("Erfolg", f"Auftrag abgeschlossen!\n{total_weight}g wurden auf {len(self.matched_spools)} Spule(n) aufgeteilt und abgebucht.", parent=self.queue_dialog)
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gib gültige Zahlen ein!", parent=self)


class PrintQueueDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("📝 Auftrags-Planer (Print Queue)")
        self.configure(bg=parent.cget('bg'))
        
        self.transient(parent)
        self.grab_set()
        
        geom = self.app.settings.get("print_queue_geometry")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("1150x700")
            center_window(self, parent)
            
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.selected_job_id = None
        self.jobs = self.app.data_manager.load_jobs()
        self.projects = self.app.data_manager.load_projects()
        self.project_path_to_id = {}
        self.selected_spool_entries = {}  # maps spool_id -> (entry_widget, row_frame)
        
        if hasattr(self.app, 'data_manager') and hasattr(self.app.data_manager, 'get_images_dir'):
            self.images_dir = self.app.data_manager.get_images_dir()
        else:
            db_dir = os.path.dirname(os.path.abspath(self.app.data_manager.jobs_file if hasattr(self.app.data_manager, "jobs_file") else "print_jobs.json"))
            self.images_dir = os.path.join(db_dir, "job_images")
            os.makedirs(self.images_dir, exist_ok=True)
        self.temp_image_path = None
        
        self.build_ui()

    def build_ui(self):
        btn_frm_footer = ttk.Frame(self, padding=10)
        btn_frm_footer.pack(fill="x", side="bottom")
        ttk.Button(btn_frm_footer, text="Schließen", command=self.on_close).pack(side="right")
        
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # LINKE SEITE
        frm_left = ttk.Frame(main_paned)
        main_paned.add(frm_left, weight=1)
        
        self.queue_notebook = ttk.Notebook(frm_left)
        self.queue_notebook.pack(fill="both", expand=True)
        
        tab_active = ttk.Frame(self.queue_notebook)
        tab_archive = ttk.Frame(self.queue_notebook)
        self.queue_notebook.add(tab_active, text="⏳ Warteschlange")
        self.queue_notebook.add(tab_archive, text="📦 Archiv")
        
        # Treeview für Warteschlange
        columns = ("date", "title", "qty", "printer", "cost", "sell_price", "actual_price", "status")
        self.tree = ttk.Treeview(tab_active, columns=columns, show="headings")
        self.tree.heading("date", text="Datum")
        self.tree.heading("title", text="Auftrag / Kunde")
        self.tree.heading("qty", text="Stk.")
        self.tree.heading("printer", text="Drucker")
        self.tree.heading("cost", text="Kosten (EK)")
        self.tree.heading("sell_price", text="Kalk. VK")
        self.tree.heading("actual_price", text="Erlös (Ist)")
        self.tree.heading("status", text="Status")
        self.tree.column("date", width=80, anchor="center")
        self.tree.column("title", width=140)
        self.tree.column("qty", width=45, anchor="center")
        self.tree.column("printer", width=95)
        self.tree.column("cost", width=75, anchor="e")
        self.tree.column("sell_price", width=75, anchor="e")
        self.tree.column("actual_price", width=75, anchor="e")
        self.tree.column("status", width=85, anchor="center")
        
        scroll = ttk.Scrollbar(tab_active, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_job_select)

        # Treeview für Archiv
        self.tree_archive = ttk.Treeview(tab_archive, columns=columns, show="headings")
        self.tree_archive.heading("date", text="Datum")
        self.tree_archive.heading("title", text="Auftrag / Kunde")
        self.tree_archive.heading("qty", text="Stk.")
        self.tree_archive.heading("printer", text="Drucker")
        self.tree_archive.heading("cost", text="Kosten (EK)")
        self.tree_archive.heading("sell_price", text="Kalk. VK")
        self.tree_archive.heading("actual_price", text="Erlös (Ist)")
        self.tree_archive.heading("status", text="Status")
        self.tree_archive.column("date", width=80, anchor="center")
        self.tree_archive.column("title", width=140)
        self.tree_archive.column("qty", width=45, anchor="center")
        self.tree_archive.column("printer", width=95)
        self.tree_archive.column("cost", width=75, anchor="e")
        self.tree_archive.column("sell_price", width=75, anchor="e")
        self.tree_archive.column("actual_price", width=75, anchor="e")
        self.tree_archive.column("status", width=85, anchor="center")
        
        scroll_arch = ttk.Scrollbar(tab_archive, orient="vertical", command=self.tree_archive.yview)
        self.tree_archive.configure(yscrollcommand=scroll_arch.set)
        self.tree_archive.pack(side="left", fill="both", expand=True)
        scroll_arch.pack(side="right", fill="y")
        self.tree_archive.bind("<<TreeviewSelect>>", self.on_job_select)

        # RECHTE SEITE
        frm_right = ttk.Frame(main_paned, padding=(15, 0, 0, 0))
        main_paned.add(frm_right, weight=1)
        
        self.lbl_mode = ttk.Label(frm_right, text="✨ Neuen Auftrag anlegen", font=("Segoe UI", 12, "bold"))
        self.lbl_mode.pack(anchor="w", pady=(0, 15))
        
        # --- ERLEDIGT BEREICH (Am unteren Rand fest angedockt) ---
        frm_finish = ttk.Frame(frm_right)
        frm_finish.pack(fill="x", side="bottom", pady=(5, 10))
        
        self.btn_finish = ttk.Button(frm_finish, text="✅ Erledigt & Abziehen", command=self.finish_job)
        self.btn_finish.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_finish_no = ttk.Button(frm_finish, text="✅ Ohne Abzug erledigen", command=self.finish_job_no_deduct)
        self.btn_finish_no.pack(side="left", fill="x", expand=True)
        
        # --- ACTION BUTTONS (Direkt über dem Erledigt-Bereich angedockt) ---
        frm_actions = ttk.Frame(frm_right)
        frm_actions.pack(fill="x", side="bottom", pady=5)
        
        self.btn_save = ttk.Button(frm_actions, text="➕ Auftrag speichern", style="Accent.TButton", command=self.save_job)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(frm_actions, text="🧹 Neu", command=self.reset_form).pack(side="left", padx=5)
        self.btn_delete = ttk.Button(frm_actions, text="🗑️", style="Delete.TButton", command=self.delete_job, width=3)
        self.btn_delete.pack(side="left")

        # --- SCROLLBAR BEREICH (Füllt den verbleibenden Platz in der Mitte) ---
        sf = ScrollableFrame(frm_right)
        sf.pack(fill="both", expand=True)
        
        # Split into Form & Image side-by-side inside the scrollable container
        frm_form_and_image = ttk.Frame(sf.inner)
        frm_form_and_image.pack(fill="both", expand=True)
        
        frm_form = ttk.Frame(frm_form_and_image)
        frm_form.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        frm_img_panel = ttk.Frame(frm_form_and_image, width=240)
        frm_img_panel.pack(side="right", fill="y", padx=(10, 0))
        frm_img_panel.pack_propagate(False)
        
        ttk.Label(frm_img_panel, text="Modell-Bild:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.lbl_img_preview = tk.Label(frm_img_panel, text="Kein Bild\nhinterlegt", relief="solid", borderwidth=1, bg="#222" if "dark" in str(self.cget('bg')) else "#eee")
        self.lbl_img_preview.pack(fill="both", expand=True, pady=(0, 3))
        self.lbl_img_preview.bind("<Button-1>", self.on_preview_click)
        
        self.lbl_zoom_hint = ttk.Label(frm_img_panel, text="", font=("Segoe UI", 8), foreground="gray")
        self.lbl_zoom_hint.pack(anchor="center", pady=(0, 5))
        
        self.btn_select_img = ttk.Button(frm_img_panel, text="📷 Bild hochladen", command=self.select_image)
        self.btn_select_img.pack(fill="x", pady=2)
        
        self.btn_delete_img = ttk.Button(frm_img_panel, text="🗑️ Bild löschen", command=self.delete_image)
        self.btn_delete_img.pack(fill="x", pady=2)
        
        # Build form inputs inside frm_form
        ttk.Label(frm_form, text="Titel / Bezeichnung:").pack(anchor="w")
        self.ent_title = ttk.Entry(frm_form)
        self.ent_title.pack(fill="x", pady=(0, 6))
        
        ttk.Label(frm_form, text="Kunde / Kontakt:").pack(anchor="w")
        self.ent_customer = ttk.Entry(frm_form)
        self.ent_customer.pack(fill="x", pady=(0, 6))
        
        row_qty_printer = ttk.Frame(frm_form)
        row_qty_printer.pack(fill="x", pady=(0, 6))
        
        frm_qty = ttk.Frame(row_qty_printer)
        frm_qty.pack(side="left", padx=(0, 10))
        ttk.Label(frm_qty, text="Stückzahl:").pack(anchor="w")
        self.ent_quantity = ttk.Entry(frm_qty, width=8)
        self.ent_quantity.insert(0, "1")
        self.ent_quantity.pack(anchor="w")
        self.ent_quantity.bind("<KeyRelease>", self.recalculate_price)
        
        frm_prn = ttk.Frame(row_qty_printer)
        frm_prn.pack(side="left", fill="x", expand=True)
        ttk.Label(frm_prn, text="Drucker:").pack(anchor="w")
        self.printers_list = self.app.settings.get("printers", [])
        printer_values = ["- Globaler Standard -"] + [p.get("name", "Drucker") for p in self.printers_list]
        self.combo_printer = ttk.Combobox(frm_prn, values=printer_values, state="readonly")
        self.combo_printer.current(0)
        self.combo_printer.pack(fill="x")
        self.combo_printer.bind("<<ComboboxSelected>>", self.recalculate_price)
        
        ttk.Label(frm_form, text="Projekt / Ordner:").pack(anchor="w")
        self.combo_project = ttk.Combobox(frm_form, state="readonly")
        self.combo_project.pack(fill="x", pady=(0, 6))
        self.update_project_combobox_values()
        
        ttk.Label(frm_form, text="Modell-Link:").pack(anchor="w")
        frm_link = ttk.Frame(frm_form)
        frm_link.pack(fill="x", pady=(0, 6))
        self.ent_link = ttk.Entry(frm_link)
        self.ent_link.pack(side="left", fill="x", expand=True)
        ttk.Button(frm_link, text="🌐", width=3, command=self.open_url).pack(side="left", padx=(5, 0))
        
        # 3MF-Datei auslesen Button
        self.btn_import_3mf = ttk.Button(frm_form, text="📄 3MF-Datei auslesen", command=self.import_3mf_file)
        self.btn_import_3mf.pack(fill="x", pady=(0, 6))
        
        ttk.Label(frm_form, text="Druckparameter / Spezifikationen:").pack(anchor="w")
        self.ent_specs = ttk.Entry(frm_form)
        self.ent_specs.pack(fill="x", pady=(0, 6))
        
        # Druckzeit (pro Stück)
        time_header_frm = ttk.Frame(sf.inner)
        time_header_frm.pack(fill="x", pady=(0, 2))
        ttk.Label(time_header_frm, text="Druckzeit (pro Stück):").pack(side="left")
        self.lbl_total_time = ttk.Label(time_header_frm, text="", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.lbl_total_time.pack(side="left", padx=(10, 0))
        
        time_frm = ttk.Frame(sf.inner)
        time_frm.pack(fill="x", pady=(0, 8))
        
        self.ent_print_hours = ttk.Entry(time_frm, width=8)
        self.ent_print_hours.insert(0, "1")
        self.ent_print_hours.pack(side="left")
        ttk.Label(time_frm, text="Std").pack(side="left", padx=(2, 10))
        
        self.ent_print_mins = ttk.Entry(time_frm, width=8)
        self.ent_print_mins.insert(0, "0")
        self.ent_print_mins.pack(side="left")
        ttk.Label(time_frm, text="Min").pack(side="left", padx=2)
        
        self.ent_print_hours.bind("<KeyRelease>", self.recalculate_price)
        self.ent_print_mins.bind("<KeyRelease>", self.recalculate_price)
        
        # Sonstige Ausgaben inside scrollable container
        ttk.Label(sf.inner, text="Sonstige Ausgaben (z.B. Modellkauf):").pack(anchor="w")
        expenses_frm = ttk.Frame(sf.inner)
        expenses_frm.pack(fill="x", pady=(0, 8))
        self.ent_other_expenses = ttk.Entry(expenses_frm, width=12)
        self.ent_other_expenses.insert(0, "0.00")
        self.ent_other_expenses.pack(side="left")
        ttk.Label(expenses_frm, text="€").pack(side="left", padx=5)
        self.ent_other_expenses.bind("<KeyRelease>", self.recalculate_price)
 
        # Verwendete Spulen & Gewichte inside scrollable container
        spools_header_frm = ttk.Frame(sf.inner)
        spools_header_frm.pack(fill="x", pady=(0, 2))
        ttk.Label(spools_header_frm, text="Ausgewählte Spulen & Grammzahl (pro Stück):").pack(side="left")
        self.lbl_total_weight = ttk.Label(spools_header_frm, text="", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.lbl_total_weight.pack(side="left", padx=(10, 0))
        
        self.spools_list_frame = ttk.Frame(sf.inner)
        self.spools_list_frame.pack(fill="x", pady=(0, 8))
        
        frm_spool_input = ttk.Frame(sf.inner)
        frm_spool_input.pack(fill="x", pady=(0, 8))
        
        self.spool_list = ["+ Spule hinzufügen..."]
        for i in self.app.inventory:
            if i.get('type') != 'VERBRAUCHT':
                color_clean = str(i.get('color', '')).split('(')[0].strip()
                self.spool_list.append(f"[{i['id']}] {i.get('brand','')} {color_clean}")
        
        # Subframe for search entry (with search icon)
        search_subfrm = ttk.Frame(frm_spool_input)
        search_subfrm.pack(fill="x", pady=(0, 2))
        
        ttk.Label(search_subfrm, text="🔍").pack(side="left", padx=(0, 5))
        self.ent_search_spool = ttk.Entry(search_subfrm)
        self.ent_search_spool.pack(side="left", fill="x", expand=True)
        
        self.combo_add = ttk.Combobox(frm_spool_input, values=self.spool_list, state="readonly")
        self.combo_add.current(0)
        self.combo_add.pack(fill="x")
        self.combo_add.bind("<<ComboboxSelected>>", self.on_quick_add_spool)
        
        def filter_add_spools(event):
            q = self.ent_search_spool.get().lower().strip()
            if not q:
                self.combo_add['values'] = self.spool_list
                self.combo_add.current(0)
            else:
                filtered = [self.spool_list[0]] + [s for s in self.spool_list[1:] if q in s.lower()]
                self.combo_add['values'] = filtered
                if len(filtered) > 1:
                    self.combo_add.current(1)
                else:
                    self.combo_add.current(0)
                    
        def on_search_enter(event):
            if self.combo_add.current() > 0:
                self.on_quick_add_spool(None)
                
        self.ent_search_spool.bind("<KeyRelease>", filter_add_spools)
        self.ent_search_spool.bind("<Return>", on_search_enter)
        
        # Errechneter Preis & Aufschlüsselung inside scrollable container
        self.lbl_calc_price = ttk.Label(sf.inner, text="Errechneter Preis: 0.00 €", font=("Segoe UI", 11, "bold"), foreground="#0078d7")
        self.lbl_calc_price.pack(anchor="w", pady=(0, 2))
        
        self.lbl_calc_breakdown = ttk.Label(sf.inner, text="", font=("Segoe UI", 9), foreground="gray")
        self.lbl_calc_breakdown.pack(anchor="w", pady=(0, 6))

        # Tatsächlicher Verkaufspreis (Erlös)
        frm_actual = ttk.Frame(sf.inner)
        frm_actual.pack(fill="x", pady=(0, 8))
        ttk.Label(frm_actual, text="Tatsächlicher Verkaufspreis (Ist):", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.ent_actual_sell_price = ttk.Entry(frm_actual, width=10)
        self.ent_actual_sell_price.pack(side="left", padx=(6, 2))
        ttk.Label(frm_actual, text="€").pack(side="left")
        self.lbl_actual_profit = ttk.Label(frm_actual, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_actual_profit.pack(side="left", padx=(12, 0))
        self.ent_actual_sell_price.bind("<KeyRelease>", self.recalculate_price)
        
        ttk.Label(sf.inner, text="Notizen (Planung / Details):").pack(anchor="w")
        self.txt_notes = tk.Text(sf.inner, height=5, font=("Segoe UI", 10))
        self.txt_notes.pack(fill="x", pady=(0, 15))
        
        self.btn_delete.state(['disabled'])
        self.btn_finish.state(['!disabled'])
        self.btn_finish_no.state(['!disabled'])

        self.refresh_list()

    def add_spool_row(self, spool_id, weight=100.0):
        spool_id_str = str(spool_id)
        if spool_id_str in self.selected_spool_entries:
            return
            
        if hasattr(self, 'imported_weight') and self.imported_weight > 0 and weight == 100.0:
            weight = self.imported_weight
            self.imported_weight = 0.0
            
        sp = next((i for i in self.app.inventory if str(i['id']) == spool_id_str), None)
        
        row_frm = ttk.Frame(self.spools_list_frame)
        row_frm.pack(fill="x", pady=2)
        
        if sp:
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', sp.get('color', '')).strip()
            lbl_text = f"[{sp['id']}] {sp.get('brand','')} {color_clean}:"
        else:
            lbl_text = f"[{spool_id_str}] Custom Spule:"
            
        ttk.Label(row_frm, text=lbl_text, width=30, anchor="w").pack(side="left")
        
        ent = ttk.Entry(row_frm, width=8)
        w_str = str(weight)
        if w_str.endswith(".0"):
            w_str = w_str[:-2]
        ent.insert(0, w_str)
        ent.pack(side="left", padx=5)
        ttk.Label(row_frm, text="g").pack(side="left", padx=(0, 10))
        
        btn_del = ttk.Button(row_frm, text="❌", width=3, command=lambda: self.remove_spool_row(spool_id_str))
        btn_del.pack(side="right")
        
        lbl_price = ttk.Label(row_frm, text="0.00 €", font=("Segoe UI", 9, "bold"), foreground="#28a745")
        lbl_price.pack(side="right", padx=(0, 10))
        
        ent.bind("<KeyRelease>", self.recalculate_price)
        
        self.selected_spool_entries[spool_id_str] = (ent, row_frm, lbl_price)
        self.recalculate_price()

    def remove_spool_row(self, spool_id_str):
        if spool_id_str in self.selected_spool_entries:
            ent, row_frm, lbl_price = self.selected_spool_entries[spool_id_str]
            row_frm.destroy()
            del self.selected_spool_entries[spool_id_str]
            self.recalculate_price()

    def recalculate_price(self, event=None):
        try:
            h_val = float(self.ent_print_hours.get().replace(",", ".")) if self.ent_print_hours.get() else 0.0
        except ValueError:
            h_val = 0.0
        try:
            m_val = float(self.ent_print_mins.get().replace(",", ".")) if self.ent_print_mins.get() else 0.0
        except ValueError:
            m_val = 0.0
        duration_single = h_val + (m_val / 60.0)
        
        qty = safe_int(self.ent_quantity.get(), 1)
        if qty < 1: qty = 1
        
        duration_total = duration_single * qty
        if qty > 1 and duration_single > 0:
            tot_h, tot_m = decimal_to_hm(duration_total)
            self.lbl_total_time.config(text=f"(Gesamt: {tot_h} Std {tot_m} Min)")
        else:
            self.lbl_total_time.config(text="")
            
        kwh_price = safe_float(self.app.settings.get("kwh_price"), 0.30)
        
        # Drucker-spezifische Werte holen
        selected_printer_idx = self.combo_printer.current()
        selected_printer = None
        if selected_printer_idx > 0 and selected_printer_idx - 1 < len(self.printers_list):
            selected_printer = self.printers_list[selected_printer_idx - 1]
            
        watts = 150
        if selected_printer and selected_printer.get("printer_watts") not in (None, ""):
            watts = safe_int(selected_printer.get("printer_watts"), 150)
        else:
            watts = safe_int(self.app.settings.get("printer_watts"), 150)
            
        wear_price = 0.20
        if selected_printer and selected_printer.get("wear_per_hour") not in (None, ""):
            wear_price = safe_float(selected_printer.get("wear_per_hour"), 0.20)
        else:
            wear_price = safe_float(self.app.settings.get("wear_per_hour"), 0.20)
            
        margin_percent = safe_int(self.app.settings.get("profit_margin"), 0)
        
        strom_single = duration_single * (watts / 1000.0) * kwh_price
        wear_single = duration_single * wear_price
        
        total_weight_single = 0.0
        weights = {}
        for sp_id, (ent, _, _) in self.selected_spool_entries.items():
            try:
                w_val = float(ent.get().replace(",", "."))
            except ValueError:
                w_val = 0.0
            weights[sp_id] = w_val
            total_weight_single += w_val
            
        if qty > 1 and total_weight_single > 0:
            self.lbl_total_weight.config(text=f"(Gesamt: {(total_weight_single * qty):.1f} g)")
        else:
            self.lbl_total_weight.config(text="")
            
        total_cost_single = 0.0
        total_mat_cost_single = 0.0
        for sp_id, w_val in weights.items():
            ent, _, lbl_price = self.selected_spool_entries[sp_id]
            if w_val <= 0:
                lbl_price.config(text="0.00 €")
                continue
            sp = next((i for i in self.app.inventory if str(i['id']) == sp_id), None)
            if not sp:
                lbl_price.config(text="0.00 €")
                continue
            
            mat_cost = 0.0
            try:
                price = float(str(sp.get('price', '0')).replace(',', '.'))
                cap = float(str(sp.get('capacity', '1000')))
                if cap > 0: mat_cost = w_val * (price / cap)
            except: pass
            
            total_mat_cost_single += mat_cost
            share = w_val / total_weight_single if total_weight_single > 0 else 0.0
            spool_share_cost = mat_cost + (strom_single * share) + (wear_single * share)
            total_cost_single += spool_share_cost
            
            lbl_price.config(text=f"{mat_cost:.2f} €")
            
        try:
            other_exp = float(self.ent_other_expenses.get().replace(",", ".")) if self.ent_other_expenses.get() else 0.0
        except ValueError:
            other_exp = 0.0

        print_sell_price_single = total_cost_single * (1 + (margin_percent / 100.0))
        
        # Batch totals
        total_cost = (total_cost_single * qty) + other_exp
        sell_price = (print_sell_price_single * qty) + other_exp
        
        if qty > 1:
            if margin_percent > 0:
                res_text = f"Einzeln: {total_cost_single:.2f} € (VK: {print_sell_price_single:.2f} €)  |  GESAMT ({qty} Stk): {total_cost:.2f} € (VK: {sell_price:.2f} €)"
            else:
                res_text = f"Einzeln: {total_cost_single:.2f} €  |  GESAMT ({qty} Stk): {total_cost:.2f} €"
        else:
            if margin_percent > 0:
                res_text = f"Errechneter Preis: {total_cost:.2f} € (VK: {sell_price:.2f} €)"
            else:
                res_text = f"Errechneter Preis: {total_cost:.2f} €"
        self.lbl_calc_price.config(text=res_text)
        
        breakdown_text = f"Material: {(total_mat_cost_single * qty):.2f} € | Strom: {(strom_single * qty):.2f} € | Verschleiß: {(wear_single * qty):.2f} €"
        if other_exp > 0:
            breakdown_text += f" | Sonstiges: {other_exp:.2f} €"
        self.lbl_calc_breakdown.config(text=breakdown_text)
        
        # Actual sell price calculation
        try:
            actual_price_val = float(self.ent_actual_sell_price.get().replace(",", ".")) if self.ent_actual_sell_price.get() else 0.0
        except ValueError:
            actual_price_val = 0.0
            
        if actual_price_val > 0:
            profit = actual_price_val - total_cost
            if profit >= 0:
                self.lbl_actual_profit.config(text=f"Echter Gewinn: +{profit:.2f} €", foreground="#28a745")
            else:
                self.lbl_actual_profit.config(text=f"Verlust: {profit:.2f} €", foreground="#d9534f")
        else:
            self.lbl_actual_profit.config(text="")

    def on_quick_add_spool(self, event):
        sel = self.combo_add.get()
        if sel.startswith("["):
            spid = sel.split("]")[0].replace("[", "")
            self.add_spool_row(spid, 100.0)
            
        # Clean search input if it exists
        if hasattr(self, 'ent_search_spool') and self.ent_search_spool.winfo_exists():
            self.ent_search_spool.delete(0, tk.END)
            if hasattr(self, 'spool_list'):
                self.combo_add['values'] = self.spool_list
                
        self.combo_add.current(0)

    def select_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Bilddateien", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if path:
            self.temp_image_path = path
            self.load_and_display_image(path)

    def delete_image(self):
        self.temp_image_path = ""  # Mark image for deletion
        self.load_and_display_image(None)

    def load_and_display_image(self, img_path):
        if img_path and os.path.exists(img_path):
            try:
                from PIL import Image, ImageTk
                with Image.open(img_path) as im:
                    img = im.copy()
                resample_filter = getattr(Image, "Resampling", Image).LANCZOS
                img.thumbnail((220, 220), resample_filter)
                photo = ImageTk.PhotoImage(img)
                self.lbl_img_preview.config(image=photo, text="", cursor="hand2")
                self.lbl_img_preview.image = photo  # Keep reference
                self.lbl_zoom_hint.config(text="🔍 Klick für Vollbild")
                return
            except Exception as e:
                print(f"Fehler beim Laden des Bildes: {e}")
        
        bg_col = "#222" if "dark" in str(self.cget('bg')) else "#eee"
        self.lbl_img_preview.config(image="", text="Kein Bild\nhinterlegt", bg=bg_col, cursor="")
        self.lbl_img_preview.image = None
        self.lbl_zoom_hint.config(text="")

    def on_preview_click(self, event=None):
        img_path = None
        if self.temp_image_path and os.path.exists(self.temp_image_path):
            img_path = self.temp_image_path
        elif self.selected_job_id:
            job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
            if job and job.get('image_name'):
                p = os.path.join(self.images_dir, job['image_name'])
                if os.path.exists(p):
                    img_path = p
        if img_path:
            title = self.ent_title.get().strip() or "Modell-Bild"
            JobImageViewerDialog(self, img_path, title)

    def import_3mf_file(self):
        path = filedialog.askopenfilename(filetypes=[("3MF Projektdatei", "*.3mf")])
        if not path:
            return
            
        import zipfile
        import xml.etree.ElementTree as ET
        
        total_time_s = 0.0
        total_weight_g = 0.0
        
        try:
            with zipfile.ZipFile(path, 'r') as z:
                config_name = None
                for name in z.namelist():
                    if name.endswith("slice_info.config"):
                        config_name = name
                        break
                
                if config_name:
                    with z.open(config_name) as f:
                        content = f.read()
                        root = ET.fromstring(content)
                        for meta in root.iter('metadata'):
                            key = meta.get('key')
                            val = meta.get('value')
                            if key == 'prediction':
                                try: total_time_s += float(val)
                                except: pass
                            elif key in ('used_g', 'weight'):
                                try: total_weight_g += float(val)
                                except: pass
                                
                        for fil in root.iter('filament'):
                            used_g = fil.get('used_g')
                            if used_g:
                                try: total_weight_g += float(used_g)
                                except: pass
                else:
                    messagebox.showwarning("Fehler", "Keine 'slice_info.config' in der 3MF-Datei gefunden.\nWurde das Modell in Bambu Studio / OrcaSlicer gesliced?", parent=self)
                    return
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Lesen der 3MF-Datei:\n{e}", parent=self)
            return
            
        if total_time_s > 0 or total_weight_g > 0:
            h, m = decimal_to_hm(total_time_s / 3600.0)
            self.ent_print_hours.delete(0, tk.END)
            self.ent_print_hours.insert(0, str(h))
            self.ent_print_mins.delete(0, tk.END)
            self.ent_print_mins.insert(0, str(m))
            
            spool_count = len(self.selected_spool_entries)
            if spool_count > 0:
                share_w = round(total_weight_g / spool_count, 1)
                for sp_id, (ent, _, _) in self.selected_spool_entries.items():
                    ent.delete(0, tk.END)
                    ent.insert(0, str(share_w))
                self.recalculate_price()
                messagebox.showinfo("3MF Import", f"Daten erfolgreich importiert:\n- Druckzeit: {h} Std {m} Min\n- Filament-Gewicht: {total_weight_g:.1f}g (aufgeteilt auf {spool_count} Spule(n))", parent=self)
            else:
                self.imported_weight = total_weight_g
                messagebox.showinfo("3MF Import", f"Daten erfolgreich importiert:\n- Druckzeit: {h} Std {m} Min\n- Filament-Gewicht: {total_weight_g:.1f}g\n\nFüge nun eine Spule hinzu, um das Gewicht automatisch einzutragen.", parent=self)
        else:
            messagebox.showwarning(
                "Fehler",
                "Es konnten keine Druckzeit- oder Filamentdaten in der 3MF-Datei gefunden werden.\n\n"
                "Hinweis: Bitte stelle sicher, dass das Modell vor dem Speichern der 3MF-Projektdatei in Bambu Studio / OrcaSlicer gesliced wurde (so dass G-Code generiert wurde). Unsliced Projektdateien enthalten noch keine Druckdaten.",
                parent=self
            )

    def on_job_select(self, event):
        trigger_tree = event.widget
        other_tree = self.tree_archive if trigger_tree == self.tree else self.tree
        
        sel = trigger_tree.selection()
        if not sel: return
        
        if other_tree.selection():
            other_tree.selection_remove(other_tree.selection())
        
        self.selected_job_id = sel[0]
        job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
        
        if job:
            self.lbl_mode.config(text="📝 Auftrag bearbeiten")
            self.btn_save.config(text="💾 Änderungen speichern")
            self.btn_delete.state(['!disabled'])
            
            if "Erledigt" in job.get('status', ''):
                self.btn_finish.state(['disabled'])
                self.btn_finish_no.state(['disabled'])
            else:
                self.btn_finish.state(['!disabled'])
                self.btn_finish_no.state(['!disabled'])
            
            self.ent_title.delete(0, tk.END); self.ent_title.insert(0, job.get('title', ''))
            self.ent_customer.delete(0, tk.END); self.ent_customer.insert(0, job.get('customer', ''))
            self.ent_quantity.delete(0, tk.END); self.ent_quantity.insert(0, str(job.get('quantity', 1)))
            self.ent_specs.delete(0, tk.END); self.ent_specs.insert(0, job.get('specs', ''))
            self.ent_link.delete(0, tk.END); self.ent_link.insert(0, job.get('link', ''))
            
            actual_p = safe_float(job.get('actual_sell_price', 0.0))
            self.ent_actual_sell_price.delete(0, tk.END)
            if actual_p > 0:
                self.ent_actual_sell_price.insert(0, f"{actual_p:.2f}")
            
            p_id = job.get("printer_id", "")
            found_idx = 0
            for idx, p in enumerate(self.printers_list):
                if p.get("id") == p_id:
                    found_idx = idx + 1
                    break
            self.combo_printer.current(found_idx)
            
            # Print time prefill
            print_time_val = float(job.get('print_time', 1.0))
            h, m = decimal_to_hm(print_time_val)
            self.ent_print_hours.delete(0, tk.END)
            self.ent_print_hours.insert(0, str(h))
            self.ent_print_mins.delete(0, tk.END)
            self.ent_print_mins.insert(0, str(m))
            
            # Clear current spool rows
            for _, (_, row_frm, _) in self.selected_spool_entries.items():
                row_frm.destroy()
            self.selected_spool_entries.clear()
            
            # Load spool weights
            spool_weights = job.get('spool_weights', {})
            spools_str = job.get('spools', '').strip()
            
            if spool_weights:
                for sp_id, w in spool_weights.items():
                    self.add_spool_row(sp_id, w)
            elif spools_str:
                parts = [p.strip() for p in spools_str.split(',') if p.strip()]
                for p in parts:
                    self.add_spool_row(p, 0.0)
                    
            # Load other expenses
            other_exp = job.get('other_expenses', 0.0)
            self.ent_other_expenses.delete(0, tk.END)
            self.ent_other_expenses.insert(0, f"{other_exp:.2f}")

            self.txt_notes.delete("1.0", tk.END); self.txt_notes.insert("1.0", job.get('notes', ''))
            self.recalculate_price()
            
            # Load project ID
            proj_id = job.get("project_id", "")
            found = False
            if proj_id:
                for path, fid in self.project_path_to_id.items():
                    if fid == proj_id:
                        self.combo_project.set(path)
                        found = True
                        break
            if not found:
                self.combo_project.current(0)
                
            self.temp_image_path = None
            img_name = job.get('image_name', '')
            if img_name:
                self.load_and_display_image(os.path.join(self.images_dir, img_name))
            else:
                self.load_and_display_image(None)

    def reset_form(self):
        self.selected_job_id = None
        self.temp_image_path = None
        self.lbl_mode.config(text="✨ Neuen Auftrag anlegen")
        self.btn_save.config(text="➕ Auftrag speichern")
        self.btn_delete.state(['disabled'])
        self.btn_finish.state(['!disabled'])
        self.btn_finish_no.state(['!disabled'])
        self.ent_title.delete(0, tk.END)
        self.ent_customer.delete(0, tk.END)
        self.ent_quantity.delete(0, tk.END); self.ent_quantity.insert(0, "1")
        self.ent_specs.delete(0, tk.END)
        self.ent_actual_sell_price.delete(0, tk.END)
        self.ent_link.delete(0, tk.END)
        self.combo_printer.current(0)
        self.combo_project.current(0)
        
        self.ent_print_hours.delete(0, tk.END)
        self.ent_print_hours.insert(0, "1")
        self.ent_print_mins.delete(0, tk.END)
        self.ent_print_mins.insert(0, "0")
        
        self.ent_other_expenses.delete(0, tk.END)
        self.ent_other_expenses.insert(0, "0.00")
        
        for _, (_, row_frm, _) in self.selected_spool_entries.items():
            row_frm.destroy()
        self.selected_spool_entries.clear()
        
        self.txt_notes.delete("1.0", tk.END)
        self.load_and_display_image(None)
        self.lbl_actual_profit.config(text="")
        self.lbl_total_time.config(text="")
        self.lbl_total_weight.config(text="")
        self.tree.selection_remove(self.tree.selection())
        self.recalculate_price()

    def update_project_combobox_values(self):
        self.projects = self.app.data_manager.load_projects()
        folders_dict = {f["id"]: f for f in self.projects if f.get("type", "folder") == "folder"}
        
        def get_folder_path(folder_id):
            path_parts = []
            curr_id = folder_id
            visited = set()
            while curr_id and curr_id not in visited:
                visited.add(curr_id)
                f = folders_dict.get(curr_id)
                if f:
                    path_parts.insert(0, f["name"])
                    curr_id = f.get("parent_id")
                else:
                    break
            return " / ".join(path_parts)
            
        self.project_path_to_id = {}
        combobox_values = ["- Kein Projekt -"]
        
        for folder_id in folders_dict:
            path = get_folder_path(folder_id)
            if path:
                self.project_path_to_id[path] = folder_id
                combobox_values.append(path)
                
        # Sort values alphabetically (except the first option)
        combobox_values[1:] = sorted(combobox_values[1:])
        self.combo_project["values"] = combobox_values
        self.combo_project.current(0)

    def save_jobs_and_sync(self):
        self.app.data_manager.save_jobs(self.jobs)
        if hasattr(self.app, 'projects_dialog') and self.app.projects_dialog and self.app.projects_dialog.winfo_exists():
            self.app.projects_dialog.refresh_tree()

    def save_job(self, clear_after=True):
        title = self.ent_title.get().strip()
        if not title:
            messagebox.showwarning("Fehler", "Titel fehlt!", parent=self)
            return False

        customer = self.ent_customer.get().strip()
        specs = self.ent_specs.get().strip()
        qty = safe_int(self.ent_quantity.get(), 1)
        if qty < 1: qty = 1

        job_id = self.selected_job_id
        if not job_id:
            job_id = str(datetime.now().timestamp())

        # Handle image save/delete
        img_name_to_save = None
        if self.temp_image_path == "":  # Image explicitly deleted
            if self.selected_job_id:
                job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
                if job and job.get('image_name'):
                    try: os.remove(os.path.join(self.images_dir, job['image_name']))
                    except: pass
            img_name_to_save = ""
            self.temp_image_path = None
        elif self.temp_image_path and os.path.exists(self.temp_image_path):  # New image selected
            try:
                from PIL import Image
                with Image.open(self.temp_image_path) as im:
                    img = im.copy()
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "transparency" in img.info else "RGB")
                img.thumbnail((600, 600))
                
                safe_id = re.sub(r'[^\w\-_]', '_', str(job_id))
                timestamp_suffix = int(datetime.now().timestamp())
                dest_filename = f"{safe_id}_{timestamp_suffix}.png"
                
                os.makedirs(self.images_dir, exist_ok=True)
                dest_full_path = os.path.join(self.images_dir, dest_filename)
                img.save(dest_full_path, "PNG")
                img_name_to_save = dest_filename
                
                # Delete previously stored image file if different
                if self.selected_job_id:
                    existing_job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
                    if existing_job and existing_job.get('image_name') and existing_job['image_name'] != dest_filename:
                        try: os.remove(os.path.join(self.images_dir, existing_job['image_name']))
                        except: pass
                        
                self.temp_image_path = None
            except Exception as e:
                print(f"Fehler beim Speichern des Bildes: {e}")
                messagebox.showerror("Bild-Fehler", f"Das Modell-Bild konnte nicht gespeichert werden:\n{e}", parent=self)

        spool_weights = {}
        spools_list = []
        for sp_id, (ent, _, _) in self.selected_spool_entries.items():
            try:
                w = float(ent.get().replace(",", "."))
            except ValueError:
                w = 0.0
            spool_weights[str(sp_id)] = w
            spools_list.append(str(sp_id))
        spools_str = ", ".join(spools_list)
        
        try:
            h_val = float(self.ent_print_hours.get().replace(",", ".")) if self.ent_print_hours.get() else 0.0
        except ValueError:
            h_val = 0.0
        try:
            m_val = float(self.ent_print_mins.get().replace(",", ".")) if self.ent_print_mins.get() else 0.0
        except ValueError:
            m_val = 0.0
        duration_single = h_val + (m_val / 60.0)
        duration_total = duration_single * qty
        
        est_weight_single = sum(spool_weights.values())
        est_weight_total = est_weight_single * qty
        
        kwh_price = safe_float(self.app.settings.get("kwh_price"), 0.30)
        
        selected_printer_idx = self.combo_printer.current()
        printer_id = ""
        selected_printer = None
        if selected_printer_idx > 0 and selected_printer_idx - 1 < len(self.printers_list):
            selected_printer = self.printers_list[selected_printer_idx - 1]
            printer_id = selected_printer.get("id", "")
            
        watts = 150
        if selected_printer and selected_printer.get("printer_watts") not in (None, ""):
            watts = safe_int(selected_printer.get("printer_watts"), 150)
        else:
            watts = safe_int(self.app.settings.get("printer_watts"), 150)
            
        wear_price = 0.20
        if selected_printer and selected_printer.get("wear_per_hour") not in (None, ""):
            wear_price = safe_float(selected_printer.get("wear_per_hour"), 0.20)
        else:
            wear_price = safe_float(self.app.settings.get("wear_per_hour"), 0.20)
            
        margin_percent = safe_int(self.app.settings.get("profit_margin"), 0)
        
        strom_single = duration_single * (watts / 1000.0) * kwh_price
        wear_single = duration_single * wear_price
        
        total_cost_single = 0.0
        total_mat_cost_single = 0.0
        for sp_id, w_val in spool_weights.items():
            if w_val <= 0: continue
            sp = next((i for i in self.app.inventory if str(i['id']) == sp_id), None)
            if not sp: continue
            
            mat_cost = 0.0
            try:
                price = float(str(sp.get('price', '0')).replace(',', '.'))
                cap = float(str(sp.get('capacity', '1000')))
                if cap > 0: mat_cost = w_val * (price / cap)
            except: pass
            
            total_mat_cost_single += mat_cost
            share = w_val / est_weight_single if est_weight_single > 0 else 0.0
            spool_share_cost = mat_cost + (strom_single * share) + (wear_single * share)
            total_cost_single += spool_share_cost
            
        try:
            other_expenses = float(self.ent_other_expenses.get().replace(",", ".")) if self.ent_other_expenses.get() else 0.0
        except ValueError:
            other_expenses = 0.0

        print_sell_price_single = total_cost_single * (1 + (margin_percent / 100.0))
        total_cost = (total_cost_single * qty) + other_expenses
        sell_price = (print_sell_price_single * qty) + other_expenses
        
        try:
            actual_sell_price = float(self.ent_actual_sell_price.get().replace(",", ".")) if self.ent_actual_sell_price.get() else 0.0
        except ValueError:
            actual_sell_price = 0.0
        
        if qty > 1:
            if margin_percent > 0:
                est_price_str = f"Einzeln: {total_cost_single:.2f} € (VK: {print_sell_price_single:.2f} €) | GESAMT ({qty} Stk): {total_cost:.2f} € (VK: {sell_price:.2f} €)"
            else:
                est_price_str = f"Einzeln: {total_cost_single:.2f} € | GESAMT ({qty} Stk): {total_cost:.2f} €"
        else:
            if margin_percent > 0:
                est_price_str = f"{total_cost:.2f} € (VK: {sell_price:.2f} €)"
            else:
                est_price_str = f"{sell_price:.2f} €"
 
        # Get selected project_id
        selected_path = self.combo_project.get()
        proj_id = self.project_path_to_id.get(selected_path, "")

        job_data = {
            "title": title,
            "customer": customer,
            "quantity": qty,
            "specs": specs,
            "link": self.ent_link.get().strip(),
            "printer_id": printer_id,
            "project_id": proj_id,
            "spools": spools_str,
            "spool_weights": spool_weights,
            "print_time": duration_single,
            "notes": self.txt_notes.get("1.0", tk.END).strip(),
            "est_weight": f"{est_weight_total:.1f}".replace(".0", ""),
            "est_time": f"{duration_total:.1f}".replace(".0", ""),
            "est_price": est_price_str,
            "material_cost": total_mat_cost_single * qty,
            "electricity_cost": strom_single * qty,
            "wear_cost": wear_single * qty,
            "other_expenses": other_expenses,
            "cost_single": total_cost_single,
            "sell_single": print_sell_price_single,
            "total_cost": total_cost,
            "sell_price": sell_price,
            "actual_sell_price": actual_sell_price
        }

        if self.selected_job_id:
            job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
            if job:
                job.update(job_data)
                if img_name_to_save is not None:
                    job["image_name"] = img_name_to_save
        else:
            new_job = {
                "id": job_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "status": "Geplant"
            }
            new_job.update(job_data)
            if img_name_to_save:
                new_job["image_name"] = img_name_to_save
            self.jobs.append(new_job)

        self.save_jobs_and_sync()
        self.refresh_list()
        if clear_after:
            self.reset_form()
        else:
            self.selected_job_id = job_id
            self.lbl_mode.config(text="📝 Auftrag bearbeiten")
            self.btn_save.config(text="💾 Änderungen speichern")
            self.btn_delete.state(['!disabled'])
            self.btn_finish.state(['!disabled'])
            self.btn_finish_no.state(['!disabled'])
        return True

    def finish_job(self):
        if not self.selected_job_id:
            if not self.save_job(clear_after=False):
                return
        job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
        if not job: return
        
        spools_str = job.get('spools', '').strip()
        matched_spools = []
        
        if spools_str:
            parts = [p.strip() for p in spools_str.split(',') if p.strip()]
            for p in parts:
                sp = next((i for i in self.app.inventory if str(i['id']) == p), None)
                if sp:
                    matched_spools.append(sp)
                    
        if not matched_spools:
            if messagebox.askyesno("Auftrag abschließen", "In diesem Auftrag sind keine bekannten Spulen-IDs hinterlegt.\nSoll der Auftrag einfach als 'Erledigt' markiert werden?", parent=self):
                job['status'] = "Erledigt ✅"
                self.save_jobs_and_sync()
                self.refresh_list()
                self.reset_form()
            return
            
        JobDeductionDialog(self, self, job, matched_spools)

    def finish_job_no_deduct(self):
        if not self.selected_job_id:
            if not self.save_job(clear_after=False):
                return
        job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
        if not job: return
        
        if messagebox.askyesno("Auftrag abschließen", "Soll der Auftrag als 'Erledigt' markiert werden, OHNE Filament abzuziehen?", parent=self):
            job['status'] = "Erledigt ✅"
            self.save_jobs_and_sync()
            self.refresh_list()
            self.reset_form()

    def delete_job(self):
        if not self.selected_job_id: return
        if messagebox.askyesno("Löschen", "Soll dieser Auftrag gelöscht werden?", parent=self):
            job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
            if job and job.get('image_name'):
                try: os.remove(os.path.join(self.images_dir, job['image_name']))
                except: pass
            self.jobs = [j for j in self.jobs if j['id'] != self.selected_job_id]
            self.save_jobs_and_sync()
            self.refresh_list()
            self.reset_form()

    def open_url(self):
        url = self.ent_link.get().strip()
        if url.startswith("http"): webbrowser.open(url)

    def refresh_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for item in self.tree_archive.get_children(): self.tree_archive.delete(item)
        
        sorted_jobs = sorted(self.jobs, key=lambda x: x.get('date', ''), reverse=True)
        for job in sorted_jobs:
            status = job.get('status', '')
            qty = safe_int(job.get('quantity', 1), 1)
            
            # Costs & Sell price
            cost = safe_float(job.get('total_cost', 0.0))
            sell = safe_float(job.get('sell_price', 0.0))
            
            # Fallback parsing for legacy jobs without explicit total_cost
            if cost == 0.0 and sell == 0.0:
                price_str = job.get('est_price', '')
                nums = re.findall(r'[\d.,]+', price_str)
                if len(nums) >= 1:
                    cost = safe_float(nums[0])
                if len(nums) >= 2:
                    sell = safe_float(nums[1])
                else:
                    sell = cost
                    
            cost_str = f"{cost:.2f} €" if cost > 0 else "-"
            sell_str = f"{sell:.2f} €" if sell > 0 else "-"
            
            actual_val = safe_float(job.get('actual_sell_price', 0.0))
            actual_str = f"{actual_val:.2f} €" if actual_val > 0 else "-"
            
            printer_id = job.get('printer_id', '')
            printers = self.app.settings.get("printers", [])
            printer = next((p for p in printers if p.get("id") == printer_id), None)
            printer_name = printer.get("name", "- Global -") if printer else "- Global -"
            
            title_display = job.get('title', '')
            customer = job.get('customer', '').strip()
            if customer:
                title_display = f"{title_display} ({customer})"
            
            row_vals = (
                job.get('date', ''),
                title_display,
                str(qty),
                printer_name,
                cost_str,
                sell_str,
                actual_str,
                job.get('status', '')
            )
            
            if "Erledigt" in status:
                self.tree_archive.insert("", "end", iid=job['id'], values=row_vals)
            else:
                self.tree.insert("", "end", iid=job['id'], values=row_vals)

    def on_close(self):
        try:
            self.app.settings["print_queue_geometry"] = self.geometry()
            self.app.data_manager.save_settings(self.app.settings)
        except:
            pass
        self.destroy()