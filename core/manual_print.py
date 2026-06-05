import tkinter as tk
from tkinter import ttk, messagebox
from core.utils import center_window

class ManualPrintDialog(tk.Toplevel):
    def __init__(self, parent, spool_item, settings, callback):
        super().__init__(parent)
        self.spool = spool_item
        self.settings = settings
        self.callback = callback
        
        self.title("✍️ Manuellen Druck protokollieren")
        self.geometry("450x550")
        self.configure(bg=parent.cget('bg'))
        self.attributes('-topmost', True)
        center_window(self, parent)

        ttk.Label(self, text="Druck-Details eingeben", font=("Segoe UI", 14, "bold")).pack(pady=15)

        # Button Frame ZUERST packen und hart unten anheften (side="bottom"), 
        # damit es niemals aus dem Fenster geschoben wird!
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(fill="x", side="bottom")

        # Eingabefelder (Packen wir NACH den Buttons)
        lbl_frame = ttk.Frame(self, padding=20)
        lbl_frame.pack(fill="both", expand=True)

        ttk.Label(lbl_frame, text="Name des Drucks (z.B. Benchy):").pack(anchor="w")
        self.ent_name = ttk.Entry(lbl_frame)
        self.ent_name.insert(0, "Manueller Druck")
        self.ent_name.pack(fill="x", pady=(0, 15))

        ttk.Label(lbl_frame, text="Verbrauch in Gramm (g):").pack(anchor="w")
        self.ent_weight = ttk.Entry(lbl_frame)
        self.ent_weight.pack(fill="x", pady=(0, 15))

        ttk.Label(lbl_frame, text="Druckdauer in Stunden (h) - Optional:").pack(anchor="w")
        self.ent_time = ttk.Entry(lbl_frame)
        self.ent_time.insert(0, "0")
        self.ent_time.pack(fill="x", pady=(0, 15))

        def on_confirm():
            try:
                name = self.ent_name.get()
                
                # Werte sicher auslesen und leere Felder abfangen
                w_str = self.ent_weight.get().replace(",", ".").strip()
                t_str = self.ent_time.get().replace(",", ".").strip()
                if not w_str: 
                    w_str = "0"
                if not t_str: 
                    t_str = "0"
                
                weight = float(w_str)
                hours = float(t_str)
                
                # --- KOSTEN-RECHNUNG ---
                # Materialkosten (Kugelsicher gegen leere Preise oder "€" Zeichen!)
                price_str = str(self.spool.get('price', '0')).replace(',', '.').replace('€', '').strip()
                price = float(price_str) if price_str else 0.0
                
                cap_str = str(self.spool.get('capacity', '1000')).strip()
                cap = float(cap_str) if cap_str else 1000.0
                
                mat_cost = weight * (price / cap) if cap > 0 else 0.0
                
                # Stromkosten
                kwh_price = float(self.settings.get("kwh_price", 0.30))
                watts = int(self.settings.get("printer_watts", 150))
                elec_cost = hours * (watts / 1000.0) * kwh_price
                
                # NEU: Maschinenverschleiß
                wear_price = float(self.settings.get("wear_per_hour", 0.20))
                wear_cost = hours * wear_price
                
                # ECHTE Gesamtkosten
                total_cost = mat_cost + elec_cost + wear_cost
                
                # NEU: Optionale Gewinnmarge (Wird im Dialog angezeigt, aber die reinen Kosten gehen ins Logbuch!)
                margin_percent = int(self.settings.get("profit_margin", 0))
                sell_price = total_cost * (1 + (margin_percent / 100.0))
                
                # Wenn Marge aktiv ist, zeigen wir dem User an, was er verlangen sollte!
                if margin_percent > 0:
                    msg = f"Kalkulation für '{name}':\n\n"
                    msg += f"Material: {mat_cost:.2f} €\n"
                    msg += f"Strom: {elec_cost:.2f} €\n"
                    msg += f"Verschleiß: {wear_cost:.2f} €\n"
                    msg += f"------------------------\n"
                    msg += f"Echte Kosten: {total_cost:.2f} €\n\n"
                    msg += f"Empfohlener Verkaufspreis (+{margin_percent}%): {sell_price:.2f} €"
                    messagebox.showinfo("💰 Kalkulation", msg, parent=self)
                
                # Wir geben jetzt Gewicht, Name, Kosten UND Verkaufspreis zurück
                self.callback(weight, name, f"{total_cost:.2f} €", f"{sell_price:.2f} €")
                self.destroy()
            except ValueError:
                messagebox.showerror("Fehler", "Bitte gültige Zahlen für Gewicht und Zeit eingeben!", parent=self)

        ttk.Button(btn_frame, text="Druck speichern", command=on_confirm, style="Accent.TButton").pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(side="left")
