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
        self.ent_time.insert(0, "1.0")
        self.ent_time.pack(fill="x", pady=(0, 15))
        
        ttk.Label(frm, text="⚖️ Verbrauch pro Spule (in Gramm):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.spool_entries = {}
        for sp in self.matched_spools:
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=2)
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', sp.get('color', '')).strip()
            lbl_text = f"[{sp['id']}] {sp.get('brand','')} {color_clean}:"
            ttk.Label(row, text=lbl_text, width=35).pack(side="left")
            
            ent = ttk.Entry(row, width=10)
            ent.insert(0, "0")
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
        self.geometry("1050x700")
        self.configure(bg=parent.cget('bg'))
        
        self.transient(parent)
        self.grab_set()
        center_window(self, parent)

        self.selected_job_id = None
        self.jobs = self.app.data_manager.load_jobs()
        
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
        ttk.Label(frm_left, text="📋 Warteschlange", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        columns = ("date", "title", "status")
        self.tree = ttk.Treeview(frm_left, columns=columns, show="headings")
        self.tree.heading("date", text="Datum")
        self.tree.heading("title", text="Auftrag / Kunde")
        self.tree.heading("status", text="Status")
        self.tree.column("date", width=90)
        self.tree.column("title", width=200)
        self.tree.column("status", width=90)
        
        scroll = ttk.Scrollbar(frm_left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_job_select)

        # RECHTE SEITE
        frm_right = ttk.Frame(main_paned, padding=(15, 0, 0, 0))
        main_paned.add(frm_right, weight=1)
        
        self.lbl_mode = ttk.Label(frm_right, text="✨ Neuen Auftrag anlegen", font=("Segoe UI", 12, "bold"))
        self.lbl_mode.pack(anchor="w", pady=(0, 15))
        
        ttk.Label(frm_right, text="Kunde / Titel:").pack(anchor="w")
        self.ent_title = ttk.Entry(frm_right)
        self.ent_title.pack(fill="x", pady=(0, 10))
        
        ttk.Label(frm_right, text="Modell-Link:").pack(anchor="w")
        frm_link = ttk.Frame(frm_right)
        frm_link.pack(fill="x", pady=(0, 10))
        self.ent_link = ttk.Entry(frm_link)
        self.ent_link.pack(side="left", fill="x", expand=True)
        ttk.Button(frm_link, text="🌐", width=3, command=self.open_url).pack(side="left", padx=(5, 0))
        
        ttk.Label(frm_right, text="Spulen (IDs oder Freitext):").pack(anchor="w")
        frm_spool_input = ttk.Frame(frm_right)
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
        
        ttk.Label(frm_right, text="Notizen (Planung / Details):").pack(anchor="w")
        self.txt_notes = tk.Text(frm_right, height=6, font=("Segoe UI", 10))
        self.txt_notes.pack(fill="x", pady=(0, 15))
        
        # --- ACTION BUTTONS ---
        frm_actions = ttk.Frame(frm_right)
        frm_actions.pack(fill="x", pady=5)
        
        self.btn_save = ttk.Button(frm_actions, text="➕ Auftrag speichern", style="Accent.TButton", command=self.save_job)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(frm_actions, text="🧹 Neu", command=self.reset_form).pack(side="left", padx=5)
        self.btn_delete = ttk.Button(frm_actions, text="🗑️", style="Delete.TButton", command=self.delete_job, width=3)
        self.btn_delete.pack(side="left")
        
        # NEU: Der Erledigt Button!
        self.btn_finish = ttk.Button(frm_right, text="✅ Erledigt & Spulen abziehen", command=self.finish_job)
        self.btn_finish.pack(fill="x", pady=10)
        
        self.btn_delete.state(['disabled'])
        self.btn_finish.state(['disabled'])

        self.refresh_list()

    def on_quick_add_spool(self, event):
        sel = self.combo_add.get()
        if sel.startswith("["):
            spid = sel.split("]")[0].replace("[", "")
            current = self.ent_spools.get().strip()
            new_val = f"{current}, {spid}" if current else spid
            self.ent_spools.delete(0, tk.END)
            self.ent_spools.insert(0, new_val)
        self.combo_add.current(0)

    def on_job_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        self.selected_job_id = sel[0]
        job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
        
        if job:
            self.lbl_mode.config(text="📝 Auftrag bearbeiten")
            self.btn_save.config(text="💾 Änderungen speichern")
            self.btn_delete.state(['!disabled'])
            
            # Wenn der Job schon erledigt ist, Abziehen-Button deaktivieren
            if "Erledigt" in job.get('status', ''):
                self.btn_finish.state(['disabled'])
            else:
                self.btn_finish.state(['!disabled'])
            
            self.ent_title.delete(0, tk.END); self.ent_title.insert(0, job.get('title', ''))
            self.ent_link.delete(0, tk.END); self.ent_link.insert(0, job.get('link', ''))
            self.ent_spools.delete(0, tk.END); self.ent_spools.insert(0, job.get('spools', ''))
            self.txt_notes.delete("1.0", tk.END); self.txt_notes.insert("1.0", job.get('notes', ''))

    def reset_form(self):
        self.selected_job_id = None
        self.lbl_mode.config(text="✨ Neuen Auftrag anlegen")
        self.btn_save.config(text="➕ Auftrag speichern")
        self.btn_delete.state(['disabled'])
        self.btn_finish.state(['disabled'])
        self.ent_title.delete(0, tk.END)
        self.ent_link.delete(0, tk.END)
        self.ent_spools.delete(0, tk.END)
        self.txt_notes.delete("1.0", tk.END)
        self.tree.selection_remove(self.tree.selection())

    def save_job(self):
        title = self.ent_title.get().strip()
        if not title:
            messagebox.showwarning("Fehler", "Titel fehlt!", parent=self)
            return

        if self.selected_job_id:
            job = next((j for j in self.jobs if j['id'] == self.selected_job_id), None)
            if job:
                job.update({
                    "title": title,
                    "link": self.ent_link.get().strip(),
                    "spools": self.ent_spools.get().strip(),
                    "notes": self.txt_notes.get("1.0", tk.END).strip()
                })
        else:
            new_job = {
                "id": str(datetime.now().timestamp()),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "title": title,
                "link": self.ent_link.get().strip(),
                "spools": self.ent_spools.get().strip(),
                "notes": self.txt_notes.get("1.0", tk.END).strip(),
                "status": "Geplant"
            }
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
        
        # IDs extrahieren
        if spools_str:
            parts = [p.strip() for p in spools_str.split(',') if p.strip()]
            for p in parts:
                # Prüfen ob der Part eine gültige ID in unserem Inventory ist
                sp = next((i for i in self.app.inventory if str(i['id']) == p), None)
                if sp:
                    matched_spools.append(sp)
                    
        if not matched_spools:
            # Keine verknüpften Spulen gefunden
            if messagebox.askyesno("Auftrag abschließen", "In diesem Auftrag sind keine bekannten Spulen-IDs hinterlegt.\nSoll der Auftrag einfach als 'Erledigt' markiert werden?", parent=self):
                job['status'] = "Erledigt ✅"
                self.app.data_manager.save_jobs(self.jobs)
                self.refresh_list()
                self.reset_form()
            return
            
        # Dialog für den Abzug öffnen
        JobDeductionDialog(self, self, job, matched_spools)

    def delete_job(self):
        if not self.selected_job_id: return
        if messagebox.askyesno("Löschen", "Soll dieser Auftrag gelöscht werden?", parent=self):
            self.jobs = [j for j in self.jobs if j['id'] != self.selected_job_id]
            self.app.data_manager.save_jobs(self.jobs)
            self.refresh_list()
            self.reset_form()

    def open_url(self):
        url = self.ent_link.get().strip()
        if url.startswith("http"): webbrowser.open(url)

    def refresh_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for job in sorted(self.jobs, key=lambda x: x.get('date', ''), reverse=True):
            self.tree.insert("", "end", iid=job['id'], values=(job.get('date', ''), job.get('title', ''), job.get('status', '')))