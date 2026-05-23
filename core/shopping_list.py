# core/shopping_list.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import webbrowser
from core.utils import center_window

class ShoppingListDialog(tk.Toplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.inventory = inventory
        self.title("Einkaufsliste / Dashboard")
        self.geometry("800x600")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        
        ttk.Label(self, text="🛒 Nachzubestellende & Verbrauchte Filamente", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        # Buttons zuerst unten anheften
        btn_frm = ttk.Frame(self)
        btn_frm.pack(fill="x", side="bottom", pady=15, padx=20)
        
        ttk.Button(btn_frm, text="🔗 Im Shop öffnen", command=self.open_shop_link, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frm, text="Als CSV exportieren", command=self.export_csv).pack(side="left", padx=5)
        ttk.Button(btn_frm, text="Schließen", command=self.destroy).pack(side="right", padx=5)

        frm_list = ttk.Frame(self)
        frm_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.tree = ttk.Treeview(frm_list, columns=("brand", "color", "mat", "supplier", "sku", "price", "status"), show="headings")
        self.tree.heading("brand", text="Marke")
        self.tree.heading("color", text="Farbe")
        self.tree.heading("mat", text="Mat.")
        self.tree.heading("supplier", text="Lieferant")
        self.tree.heading("sku", text="SKU")
        self.tree.heading("price", text="Preis")
        self.tree.heading("status", text="Status")
        self.tree.column("mat", width=50)
        self.tree.column("price", width=60)
        self.tree.column("status", width=100)
        
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
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
        sel = self.tree.selection()
        if not sel: return messagebox.showinfo("Info", "Bitte ein Filament auswählen.", parent=self)
        item = next((x for x in self.inventory if x['id'] == str(sel[0])), None)
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
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Einkaufsliste exportieren")
        if not filepath: return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f, delimiter=';').writerow(["Marke", "Farbe", "Material", "Lieferant", "SKU", "Preis", "Status", "Link"])
                for i in self.inventory:
                    if i.get('reorder') or i.get('type') == 'VERBRAUCHT': 
                        csv.writer(f, delimiter=';').writerow([i.get('brand',''), i.get('color',''), i.get('material',''), i.get('supplier',''), i.get('sku',''), i.get('price',''), "MUSS KAUFEN" if i.get('reorder') else "Leer", i.get('link','')])
            messagebox.showinfo("Exportiert", "Liste erfolgreich gespeichert!", parent=self)
        except Exception as e: messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}", parent=self)
