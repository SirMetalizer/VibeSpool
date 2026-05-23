import os
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime
from core.utils import center_window
import re

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
        ttk.Label(self, text=f"Auftrag: {self.job.get('title', 'Unbekannt')}", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)
        
        ttk.Label(frm, text="⏱️ Gesamte Druckzeit (in Stunden, z.B. 2.5):").pack(anchor="w")
        self.ent_time = ttk.Entry(frm)
        self.ent_time.insert(0, self.job.get('est_time', '1.0') or '1.0')
        self.ent_time.pack(fill="x", pady=(0, 15))
        
        ttk.Label(frm, text="⚖️ Verbrauch pro Spule (in Gramm):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        est_weight_str = self.job.get('est_weight', '0')
        try:
            est_weight_val = float(est_weight_str.replace(',', '.')) if est_weight_str else 0.0
        except:
            est_weight_val = 0.0
            
        weight_per_spool = 0.0
        if len(self.matched_spools) > 0 and est_weight_val > 0:
            weight_per_spool = round(est_weight_val / len(self.matched_spools), 1)

        self.spool_entries = {}
        for sp in self.matched_spools:
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=2)
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', sp.get('color', '')).strip()
            lbl_text = f"[{sp['id']}] {sp.get('brand','')} {color_clean}:"
            ttk.Label(row, text=lbl_text, width=35).pack(side="left")
            
            ent = ttk.Entry(row, width=10)
            ent.insert(0, f"{weight_per_spool:g}" if weight_per_spool > 0 else "0")
            ent.pack(side="right")
            ttk.Label(row, text="g").pack(side="right", padx=5)
            self.spool_entries[sp['id']] = ent

        # --- FOOTER ---
        btn_frm = ttk.Frame(self, padding=10)
        btn_frm.pack(fill="x", side="bottom")
        
        ttk.Button(btn_frm, text="Abbrechen", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frm, text="💾 Speichern & Abziehen", style="Accent.TButton", command=self.process_deduction).pack(side="right", padx=5)

    def process_deduction(self):
        try:
            duration = float(self.ent_time.get().replace(",", "."))
            
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
            kwh_price = float(self.app.settings.get("kwh_price", 0.30))
            watts = int(self.app.settings.get("printer_watts", 150))
            wear_price = float(self.app.settings.get("wear_per_hour", 0.20))
            margin_percent = int(self.app.settings.get("profit_margin", 0))
            
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
            self.app.data_manager.save_jobs(self.queue_dialog.jobs)
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
        self.geometry("1150x700")  # Slightly wider for the side-by-side layout
        self.configure(bg=parent.cget('bg'))
        
        self.transient(parent)
        self.grab_set()
        center_window(self, parent)

        self.selected_job_id = None
        self.jobs = self.app.data_manager.load_jobs()
        
        db_dir = self.app.data_manager.base_dir
        custom_path = self.app.settings.get("custom_db_path", "")
        if custom_path and os.path.exists(custom_path):
            db_dir = custom_path
            
        self.images_dir = os.path.join(db_dir, "job_images")
        if not os.path.exists(self.images_dir):
            try: os.makedirs(self.images_dir)
            except: pass
        self.temp_image_path = None
        
        self.build_ui()

    def build_ui(self):
        btn_frm_footer = ttk.Frame(self, padding=10)
        btn_frm_footer.pack(fill="x", side="bottom")
        ttk.Button(btn_frm_footer, text="Schließen", command=self.destroy).pack(side="right")
        
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
        columns = ("date", "title", "price", "status")
        self.tree = ttk.Treeview(tab_active, columns=columns, show="headings")
        self.tree.heading("date", text="Datum")
        self.tree.heading("title", text="Auftrag / Kunde")
        self.tree.heading("price", text="Preis")
        self.tree.heading("status", text="Status")
        self.tree.column("date", width=90)
        self.tree.column("title", width=180)
        self.tree.column("price", width=70, anchor="e")
        self.tree.column("status", width=90)
        
        scroll = ttk.Scrollbar(tab_active, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_job_select)

        # Treeview für Archiv
        self.tree_archive = ttk.Treeview(tab_archive, columns=columns, show="headings")
        self.tree_archive.heading("date", text="Datum")
        self.tree_archive.heading("title", text="Auftrag / Kunde")
        self.tree_archive.heading("price", text="Preis")
        self.tree_archive.heading("status", text="Status")
        self.tree_archive.column("date", width=90)
        self.tree_archive.column("title", width=180)
        self.tree_archive.column("price", width=70, anchor="e")
        self.tree_archive.column("status", width=90)
        
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
        
        # Split into Form & Image side-by-side
        frm_form_and_image = ttk.Frame(frm_right)
        frm_form_and_image.pack(fill="both", expand=True)
        
        frm_form = ttk.Frame(frm_form_and_image)
        frm_form.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        frm_img_panel = ttk.Frame(frm_form_and_image, width=220)
        frm_img_panel.pack(side="right", fill="y", padx=(10, 0))
        frm_img_panel.pack_propagate(False)
        
        # Build form inputs inside frm_form
        ttk.Label(frm_form, text="Kunde / Titel:").pack(anchor="w")
        self.ent_title = ttk.Entry(frm_form)
        self.ent_title.pack(fill="x", pady=(0, 10))
        
        ttk.Label(frm_form, text="Modell-Link:").pack(anchor="w")
        frm_link = ttk.Frame(frm_form)
        frm_link.pack(fill="x", pady=(0, 10))
        self.ent_link = ttk.Entry(frm_link)
        self.ent_link.pack(side="left", fill="x", expand=True)
        ttk.Button(frm_link, text="🌐", width=3, command=self.open_url).pack(side="left", padx=(5, 0))
        
        ttk.Label(frm_form, text="Spulen (IDs oder Freitext):").pack(anchor="w")
        frm_spool_input = ttk.Frame(frm_form)
        frm_spool_input.pack(fill="x", pady=(0, 10))
        self.ent_spools = ttk.Entry(frm_spool_input)
        self.ent_spools.pack(side="left", fill="x", expand=True)
        
        spool_list = ["+ Spule hinzufügen..."]
        for i in self.app.inventory:
            if i.get('type') != 'VERBRAUCHT':
                color_clean = str(i.get('color', '')).split('(')[0].strip()
                spool_list.append(f"[{i['id']}] {i.get('brand','')} {color_clean}")
        
        self.combo_add = ttk.Combobox(frm_spool_input, values=spool_list, state="readonly", width=22)
        self.combo_add.current(0)
        self.combo_add.pack(side="left", padx=(5, 0))
        self.combo_add.bind("<<ComboboxSelected>>", self.on_quick_add_spool)
        
        # Row 4: Weight and Time
        frm_weight_time = ttk.Frame(frm_form)
        frm_weight_time.pack(fill="x", pady=(0, 10))
        
        # Left column: Weight
        frm_w = ttk.Frame(frm_weight_time)
        frm_w.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(frm_w, text="Gewicht (g):").pack(anchor="w")
        self.ent_est_weight = ttk.Entry(frm_w)
        self.ent_est_weight.pack(fill="x", pady=2)
        
        # Right column: Time
        frm_t = ttk.Frame(frm_weight_time)
        frm_t.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ttk.Label(frm_t, text="Druckzeit (Std):").pack(anchor="w")
        self.ent_est_time = ttk.Entry(frm_t)
        self.ent_est_time.pack(fill="x", pady=2)
        
        # Row 5: Estimated Price / Calculator
        ttk.Label(frm_form, text="Kalkulierter Preis (€):").pack(anchor="w")
        frm_price_calc = ttk.Frame(frm_form)
        frm_price_calc.pack(fill="x", pady=(0, 10))
        
        self.ent_est_price = ttk.Entry(frm_price_calc)
        self.ent_est_price.pack(side="left", fill="x", expand=True)
        
        btn_calc = ttk.Button(frm_price_calc, text="🧮 Rechner", width=12, command=self.calculate_estimated_price)
        btn_calc.pack(side="left", padx=(5, 0))
        
        ttk.Label(frm_form, text="Notizen (Planung / Details):").pack(anchor="w")
        self.txt_notes = tk.Text(frm_form, height=4, font=("Segoe UI", 10))
        self.txt_notes.pack(fill="both", expand=True, pady=(0, 15))
        
        # Build image panel inside frm_img_panel
        ttk.Label(frm_img_panel, text="Modell-Bild:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.lbl_img_preview = tk.Label(frm_img_panel, text="Kein Bild\nhinterlegt", relief="solid", borderwidth=1, bg="#222" if "dark" in str(self.cget('bg')) else "#eee")
        self.lbl_img_preview.pack(fill="both", expand=True, pady=(0, 10))
        
        self.btn_select_img = ttk.Button(frm_img_panel, text="📷 Bild hochladen", command=self.select_image)
        self.btn_select_img.pack(fill="x", pady=2)
        
        self.btn_delete_img = ttk.Button(frm_img_panel, text="🗑️ Bild löschen", command=self.delete_image)
        self.btn_delete_img.pack(fill="x", pady=2)
        
        # --- ACTION BUTTONS ---
        frm_actions = ttk.Frame(frm_right)
        frm_actions.pack(fill="x", pady=5)
        
        self.btn_save = ttk.Button(frm_actions, text="➕ Auftrag speichern", style="Accent.TButton", command=self.save_job)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(frm_actions, text="🧹 Neu", command=self.reset_form).pack(side="left", padx=5)
        self.btn_delete = ttk.Button(frm_actions, text="🗑️", style="Delete.TButton", command=self.delete_job, width=3)
        self.btn_delete.pack(side="left")
        
        # --- ERLEDIGT BEREICH ---
        frm_finish = ttk.Frame(frm_right)
        frm_finish.pack(fill="x", pady=10)
        
        self.btn_finish = ttk.Button(frm_finish, text="✅ Erledigt & Abziehen", command=self.finish_job)
        self.btn_finish.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_finish_no = ttk.Button(frm_finish, text="✅ Ohne Abzug erledigen", command=self.finish_job_no_deduct)
        self.btn_finish_no.pack(side="left", fill="x", expand=True)
        
        self.btn_delete.state(['disabled'])
        self.btn_finish.state(['disabled'])
        self.btn_finish_no.state(['disabled'])

        self.refresh_list()

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
                img = Image.open(img_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                self.lbl_img_preview.config(image=photo, text="")
                self.lbl_img_preview.image = photo  # Keep reference
                return
            except Exception as e:
                print(f"Fehler beim Laden des Bildes: {e}")
        
        bg_col = "#222" if "dark" in str(self.cget('bg')) else "#eee"
        self.lbl_img_preview.config(image="", text="Kein Bild\nhinterlegt", bg=bg_col)
        self.lbl_img_preview.image = None

    def on_quick_add_spool(self, event):
        sel = self.combo_add.get()
        if sel.startswith("["):
            spid = sel.split("]")[0].replace("[", "")
            current = self.ent_spools.get().strip()
            new_val = f"{current}, {spid}" if current else spid
            self.ent_spools.delete(0, tk.END)
            self.ent_spools.insert(0, new_val)
        self.combo_add.current(0)

    def calculate_estimated_price(self):
        try:
            w_str = self.ent_est_weight.get().replace(",", ".").strip()
            t_str = self.ent_est_time.get().replace(",", ".").strip()
            
            weight = float(w_str) if w_str else 0.0
            time = float(t_str) if t_str else 0.0
            
            spools_str = self.ent_spools.get().strip()
            spool_price = 25.00
            spool_capacity = 1000.0
            
            match = re.search(r'\d+', spools_str)
            if match:
                sp_id = match.group(0)
                spool = next((i for i in self.app.inventory if str(i['id']) == sp_id), None)
                if spool:
                    try:
                        spool_price = float(str(spool.get('price', '25.00')).replace(',', '.'))
                        spool_capacity = float(str(spool.get('capacity', '1000')))
                    except:
                        pass
            
            kwh_price = float(self.app.settings.get("kwh_price", 0.30))
            watts = int(self.app.settings.get("printer_watts", 150))
            wear_price = float(self.app.settings.get("wear_per_hour", 0.20))
            margin_percent = int(self.app.settings.get("profit_margin", 0))
            
            material_cost = weight * (spool_price / spool_capacity) if spool_capacity > 0 else 0.0
            electricity_cost = time * (watts / 1000.0) * kwh_price
            wear_cost = time * wear_price
            
            total_cost = material_cost + electricity_cost + wear_cost
            vk_price = total_cost * (1 + (margin_percent / 100.0))
            
            self.ent_est_price.delete(0, tk.END)
            self.ent_est_price.insert(0, f"{vk_price:.2f} €")
        except Exception as e:
            messagebox.showerror("Fehler", f"Kalkulation fehlgeschlagen: {e}", parent=self)

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
            self.ent_link.delete(0, tk.END); self.ent_link.insert(0, job.get('link', ''))
            self.ent_spools.delete(0, tk.END); self.ent_spools.insert(0, job.get('spools', ''))
            self.txt_notes.delete("1.0", tk.END); self.txt_notes.insert("1.0", job.get('notes', ''))
            
            # Populate weight, time, price
            self.ent_est_weight.delete(0, tk.END)
            self.ent_est_weight.insert(0, job.get('est_weight', ''))
            self.ent_est_time.delete(0, tk.END)
            self.ent_est_time.insert(0, job.get('est_time', ''))
            self.ent_est_price.delete(0, tk.END)
            self.ent_est_price.insert(0, job.get('est_price', ''))
            
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
        self.btn_finish.state(['disabled'])
        self.btn_finish_no.state(['disabled'])
        self.ent_title.delete(0, tk.END)
        self.ent_link.delete(0, tk.END)
        self.ent_spools.delete(0, tk.END)
        self.txt_notes.delete("1.0", tk.END)
        self.ent_est_weight.delete(0, tk.END)
        self.ent_est_time.delete(0, tk.END)
        self.ent_est_price.delete(0, tk.END)
        self.load_and_display_image(None)
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
        if self.tree_archive.selection():
            self.tree_archive.selection_remove(self.tree_archive.selection())

    def save_job(self):
        title = self.ent_title.get().strip()
        if not title:
            messagebox.showwarning("Fehler", "Titel fehlt!", parent=self)
            return

        job_id = self.selected_job_id
        if not job_id:
            job_id = str(datetime.now().timestamp())

        # Handle image save/delete
        img_name_to_save = None
        if self.temp_image_path == "":  # Image deleted
            if self.selected_job_id:
                job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
                if job and job.get('image_name'):
                    try: os.remove(os.path.join(self.images_dir, job['image_name']))
                    except: pass
            img_name_to_save = ""
        elif self.temp_image_path:  # New image selected
            try:
                from PIL import Image
                img = Image.open(self.temp_image_path)
                img.thumbnail((600, 600))
                dest_filename = f"{job_id}.png"
                img.save(os.path.join(self.images_dir, dest_filename), "PNG")
                img_name_to_save = dest_filename
            except Exception as e:
                print(f"Fehler beim Speichern des Bildes: {e}")

        if self.selected_job_id:
            job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
            if job:
                job.update({
                    "title": title,
                    "link": self.ent_link.get().strip(),
                    "spools": self.ent_spools.get().strip(),
                    "notes": self.txt_notes.get("1.0", tk.END).strip(),
                    "est_weight": self.ent_est_weight.get().strip(),
                    "est_time": self.ent_est_time.get().strip(),
                    "est_price": self.ent_est_price.get().strip()
                })
                if img_name_to_save is not None:
                    job["image_name"] = img_name_to_save
        else:
            new_job = {
                "id": job_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "title": title,
                "link": self.ent_link.get().strip(),
                "spools": self.ent_spools.get().strip(),
                "notes": self.txt_notes.get("1.0", tk.END).strip(),
                "status": "Geplant",
                "est_weight": self.ent_est_weight.get().strip(),
                "est_time": self.ent_est_time.get().strip(),
                "est_price": self.ent_est_price.get().strip()
            }
            if img_name_to_save:
                new_job["image_name"] = img_name_to_save
            self.jobs.append(new_job)

        self.app.data_manager.save_jobs(self.jobs)
        self.refresh_list()
        self.reset_form()

    def finish_job(self):
        if not self.selected_job_id: return
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
                self.app.data_manager.save_jobs(self.jobs)
                self.refresh_list()
                self.reset_form()
            return
            
        JobDeductionDialog(self, self, job, matched_spools)

    def finish_job_no_deduct(self):
        if not self.selected_job_id: return
        job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
        if not job: return
        
        if messagebox.askyesno("Auftrag abschließen", "Soll der Auftrag als 'Erledigt' markiert werden, OHNE Filament abzuziehen?", parent=self):
            job['status'] = "Erledigt ✅"
            self.app.data_manager.save_jobs(self.jobs)
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
            self.app.data_manager.save_jobs(self.jobs)
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
            price = job.get('est_price', '-')
            if "Erledigt" in status:
                self.tree_archive.insert("", "end", iid=job['id'], values=(job.get('date', ''), job.get('title', ''), price, job.get('status', '')))
            else:
                self.tree.insert("", "end", iid=job['id'], values=(job.get('date', ''), job.get('title', ''), price, job.get('status', '')))