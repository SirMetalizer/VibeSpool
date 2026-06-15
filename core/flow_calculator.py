import tkinter as tk
from tkinter import ttk
from core.utils import center_window
from core.constants import COLOR_ACCENT

class FlowCalculatorDialog(tk.Toplevel):
    def __init__(self, parent, current_flow_entry=None, app_instance=None):
        super().__init__(parent)
        self.app = app_instance
        self.title("🧪 Flow-Rechner (Kalibrierung)")
        self.configure(bg=parent.cget('bg'))
        self.current_flow_entry = current_flow_entry
        
        geom = None
        if self.app and hasattr(self.app, "settings"):
            geom = self.app.settings.get("flow_calculator_geometry")
            
        if geom:
            self.geometry(geom)
        else:
            self.geometry("450x550")
            center_window(self, parent)
            
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        ttk.Label(self, text="Flow Kalibrierung", font=("Segoe UI", 14, "bold")).pack(pady=10)
        ttk.Label(self, text="Gib hier deine Wandstärken-Messungen ein (eine pro Zeile):", font=("Segoe UI", 9)).pack(padx=20, anchor="w")
        
        self.txt_measurements = tk.Text(self, height=8, width=30, font=("Consolas", 10))
        self.txt_measurements.pack(padx=20, pady=5, fill="x")
        self.txt_measurements.bind("<KeyRelease>", lambda e: self.calculate())

        frm_params = ttk.Frame(self, padding=10)
        frm_params.pack(fill="x", padx=10)
        
        ttk.Label(frm_params, text="Ziel-Wandstärke (mm):").grid(row=0, column=0, sticky="w", pady=2)
        self.var_target = tk.StringVar(value="0.45")
        self.ent_target = ttk.Entry(frm_params, textvariable=self.var_target)
        self.ent_target.grid(row=0, column=1, sticky="ew", pady=2)
        self.var_target.trace_add("write", lambda n, i, m: self.calculate())

        ttk.Label(frm_params, text="Bisheriger Flow:").grid(row=1, column=0, sticky="w", pady=2)
        initial_flow = "0.98"
        if current_flow_entry and current_flow_entry.get(): 
            initial_flow = current_flow_entry.get().replace(',', '.')
        self.var_old_flow = tk.StringVar(value=initial_flow)
        self.ent_old_flow = ttk.Entry(frm_params, textvariable=self.var_old_flow)
        self.ent_old_flow.grid(row=1, column=1, sticky="ew", pady=2)
        self.var_old_flow.trace_add("write", lambda n, i, m: self.calculate())

        frm_params.columnconfigure(1, weight=1)
        
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=15)
        
        self.lbl_result = ttk.Label(self, text="Mess-Durchschnitt: -", font=("Segoe UI", 10))
        self.lbl_result.pack(pady=2)
        self.lbl_new_flow = ttk.Label(self, text="NEUER FLOW: -", font=("Segoe UI", 12, "bold"), foreground=COLOR_ACCENT)
        self.lbl_new_flow.pack(pady=10)
        
        btn_frm = ttk.Frame(self)
        btn_frm.pack(pady=10, fill="x", padx=20)
        ttk.Button(btn_frm, text="Wert übernehmen", style="Accent.TButton", command=self.apply_value).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_frm, text="Schließen", command=self.on_close).pack(side="left", expand=True, fill="x", padx=5)

    def calculate(self):
        try:
            lines = self.txt_measurements.get("1.0", tk.END).strip().split('\n')
            vals = [float(l.replace(',', '.').strip()) for l in lines if l.strip()]
            if not vals: 
                return
            
            avg = sum(vals) / len(vals)
            target = float(self.var_target.get().replace(',', '.'))
            old_flow = float(self.var_old_flow.get().replace(',', '.'))
            
            # Formel: (Target / Average) * Old Flow
            new_flow = (target / avg) * old_flow
            
            self.lbl_result.config(text=f"Mess-Durchschnitt: {avg:.4f} mm ({len(vals)} Werte)")
            self.lbl_new_flow.config(text=f"NEUER FLOW: {new_flow:.4f}")
            self.calculated_value = f"{new_flow:.3f}".replace('.', ',')
        except:
            self.lbl_result.config(text="Mess-Durchschnitt: Fehler")
            self.lbl_new_flow.config(text="NEUER FLOW: -")

    def apply_value(self):
        if hasattr(self, 'calculated_value') and self.current_flow_entry:
            self.current_flow_entry.delete(0, tk.END)
            self.current_flow_entry.insert(0, self.calculated_value)
            self.destroy()

    def on_close(self):
        try:
            if self.app and hasattr(self.app, "settings"):
                self.app.settings["flow_calculator_geometry"] = self.geometry()
                self.app.data_manager.save_settings(self.app.settings)
        except Exception:
            pass
        self.destroy()
