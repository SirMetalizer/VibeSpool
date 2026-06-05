import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import zipfile
from core.utils import center_window

class BackupDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, app_instance):
        super().__init__(parent)
        self.data_manager = data_manager
        self.app = app_instance
        self.title("Backup & Restore")
        self.geometry("400x200")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        
        ttk.Label(self, text="Datenbank Backup", font=("Segoe UI", 12, "bold")).pack(pady=15)
        ttk.Button(self, text="📥 Backup exportieren", command=self.export_data).pack(fill="x", padx=40, pady=10)
        ttk.Button(self, text="📤 Backup importieren", command=self.import_data).pack(fill="x", padx=40, pady=10)
    
    def export_data(self):
        fp = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP", "*.zip")], initialfile="VibeSpool_Backup.zip")
        if not fp: 
            return
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
                    (self.data_manager.jobs_file, "print_jobs.json"),
                    (hist_f, "history.json"),
                    (mqtt_f, "mqtt_buffer.json"),
                    (ams_f, "ams_snapshots.json")
                ]:
                    if os.path.exists(f): 
                        z.write(f, n)
            messagebox.showinfo("Erfolg", "Backup erstellt!", parent=self)
            self.destroy()
        except Exception as e: 
            messagebox.showerror("Fehler", str(e), parent=self)
    
    def import_data(self):
        fp = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
        if not fp: 
            return
        if messagebox.askyesno("Warnung", "Daten werden überschrieben!", parent=self):
            try:
                with zipfile.ZipFile(fp, 'r') as z: 
                    z.extractall(self.data_manager.base_dir)
                self.app.refresh_all_data()
                messagebox.showinfo("Erfolg", "Backup geladen!", parent=self.app.root)
                self.destroy()
            except Exception as e: 
                messagebox.showerror("Fehler", str(e), parent=self)
