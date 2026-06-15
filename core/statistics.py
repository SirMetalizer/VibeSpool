# core/statistics.py

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import os
import re
from core.utils import center_window
from core.logic import calculate_net_weight
from core.constants import COLOR_ACCENT, COLOR_DELETE

class StatisticsDialog(tk.Toplevel):
    def __init__(self, parent, inventory, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.inventory = inventory
        self.title("📊 Analytics & Finanz-Dashboard")
        self.configure(bg=parent.cget('bg'))
        
        geom = self.app.settings.get("statistics_dialog_geometry")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("1250x850") 
            center_window(self, parent)
            
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize filter variables
        self.filter_brand = tk.StringVar(value="Alle")
        self.filter_material = tk.StringVar(value="Alle")
        self.filter_color = tk.StringVar(value="Alle")
        
        self.build_ui()

    def sort_column(self, tree, col, reverse):
        l = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            def parse_val(val):
                val_clean = val.replace(" kg", "").replace(" €", "").replace(" Stk", "").replace(" g", "").replace(",", ".").strip()
                return float(val_clean)
            l.sort(key=lambda t: parse_val(t[0]), reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tree.move(k, "", index)

        tree.heading(col, command=lambda: self.sort_column(tree, col, not reverse))

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.master_frame = ttk.Frame(self)
        self.master_frame.pack(fill="both", expand=True)
        
        self.side_panel = ttk.Frame(self.master_frame, width=350, relief="solid", borderwidth=1)
        self.side_panel.pack_propagate(False)
        
        self.main_content = ttk.Frame(self.master_frame)
        self.main_content.pack(side="left", fill="both", expand=True)

        # --- 2. OBERER BEREICH (Dashboard) ---
        ttk.Label(self.main_content, text="💰 Bestands-Statistik & Finanzen", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))
        
        # --- 2b. FILTER BAR ---
        # Unique options from self.inventory
        brands = sorted(list(set(item.get('brand', 'Unbekannt') or 'Unbekannt' for item in self.inventory)))
        materials = sorted(list(set(item.get('material', 'Unbekannt') or 'Unbekannt' for item in self.inventory)))
        colors = sorted(list(set(re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', 'Unbekannt') or 'Unbekannt').strip() for item in self.inventory)))
        
        brand_options = ["Alle"] + [b for b in brands if b]
        material_options = ["Alle"] + [m for m in materials if m]
        color_options = ["Alle"] + [c for c in colors if c]
        
        if self.filter_brand.get() not in brand_options:
            self.filter_brand.set("Alle")
        if self.filter_material.get() not in material_options:
            self.filter_material.set("Alle")
        if self.filter_color.get() not in color_options:
            self.filter_color.set("Alle")
            
        filter_frame = ttk.LabelFrame(self.main_content, text=" 🔍 Filter ", padding=10)
        filter_frame.pack(fill="x", padx=20, pady=5)
        
        # Grid layout inside filter_frame
        filter_frame.columnconfigure(0, weight=1)
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(2, weight=1)
        filter_frame.columnconfigure(3, weight=0)

        # Brand Filter
        frm_b = ttk.Frame(filter_frame)
        frm_b.grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Label(frm_b, text="Hersteller:").pack(anchor="w")
        cb_brand = ttk.Combobox(frm_b, textvariable=self.filter_brand, values=brand_options, state="readonly")
        cb_brand.pack(fill="x", pady=(2, 0))
        cb_brand.bind("<<ComboboxSelected>>", lambda e: self.build_ui())

        # Material Filter
        frm_m = ttk.Frame(filter_frame)
        frm_m.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Label(frm_m, text="Material:").pack(anchor="w")
        cb_material = ttk.Combobox(frm_m, textvariable=self.filter_material, values=material_options, state="readonly")
        cb_material.pack(fill="x", pady=(2, 0))
        cb_material.bind("<<ComboboxSelected>>", lambda e: self.build_ui())

        # Color Filter
        frm_c = ttk.Frame(filter_frame)
        frm_c.grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Label(frm_c, text="Farbe:").pack(anchor="w")
        cb_color = ttk.Combobox(frm_c, textvariable=self.filter_color, values=color_options, state="readonly")
        cb_color.pack(fill="x", pady=(2, 0))
        cb_color.bind("<<ComboboxSelected>>", lambda e: self.build_ui())

        # Reset Button
        def reset_filters():
            self.filter_brand.set("Alle")
            self.filter_material.set("Alle")
            self.filter_color.set("Alle")
            self.build_ui()

        btn_reset = ttk.Button(filter_frame, text="Reset", command=reset_filters)
        btn_reset.grid(row=0, column=3, padx=5, pady=(15, 0), sticky="e")

        # --- 1. DATEN BERECHNEN (KPIs) ---
        f_brand = self.filter_brand.get()
        f_material = self.filter_material.get()
        f_color = self.filter_color.get()
        
        # Filter the spools
        filtered_spools = []
        for item in self.inventory:
            brand = item.get('brand', 'Unbekannt') or 'Unbekannt'
            mat = item.get('material', 'Unbekannt') or 'Unbekannt'
            color = item.get('color', 'Unbekannt') or 'Unbekannt'
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', color).strip()

            if f_brand != "Alle" and brand != f_brand: continue
            if f_material != "Alle" and mat != f_material: continue
            if f_color != "Alle" and color_clean != f_color: continue
            
            filtered_spools.append(item)

        total_value, total_weight, total_spools = 0.0, 0.0, 0
        mat_stats = {}
        brand_stats = {}
        color_stats = {}
        detailed_stats = {}

        for item in filtered_spools:
            if item.get('type') == 'VERBRAUCHT': continue
            total_spools += 1
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.app.spools, item.get('empty_weight'))
            total_weight += net
            val = 0.0
            try:
                price, cap = float(str(item.get('price', '0')).replace(',', '.')), float(str(item.get('capacity', '1000')))
                if cap > 0: val = (net / cap) * price
            except: pass
            total_value += val
            
            # Material
            mat = item.get('material', 'Unbekannt') or 'Unbekannt'
            if mat not in mat_stats: mat_stats[mat] = {'count': 0, 'weight': 0.0, 'value': 0.0}
            mat_stats[mat]['count'] += 1
            mat_stats[mat]['weight'] += net
            mat_stats[mat]['value'] += val

            # Hersteller
            brand = item.get('brand', 'Unbekannt') or 'Unbekannt'
            if brand not in brand_stats: brand_stats[brand] = {'count': 0, 'weight': 0.0, 'value': 0.0}
            brand_stats[brand]['count'] += 1
            brand_stats[brand]['weight'] += net
            brand_stats[brand]['value'] += val

            # Farbe
            color = item.get('color', 'Unbekannt') or 'Unbekannt'
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', color).strip()
            if color_clean not in color_stats: color_stats[color_clean] = {'count': 0, 'weight': 0.0, 'value': 0.0}
            color_stats[color_clean]['count'] += 1
            color_stats[color_clean]['weight'] += net
            color_stats[color_clean]['value'] += val

            # Detailliert
            det_key = (brand, mat, color_clean)
            if det_key not in detailed_stats: detailed_stats[det_key] = {'count': 0, 'weight': 0.0, 'value': 0.0}
            detailed_stats[det_key]['count'] += 1
            detailed_stats[det_key]['weight'] += net
            detailed_stats[det_key]['value'] += val

        main_frm = ttk.Frame(self.main_content)
        main_frm.pack(fill="x", padx=20, pady=5)
        
        left_panel = ttk.Frame(main_frm)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_panel = ttk.Frame(main_frm)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # --- 3. LINKE SEITE (KPIs & Tabelle) ---
        kpi_frame = tk.Frame(left_panel, bg="#1e1e1e" if "dark" in str(self.cget('bg')) else "#ffffff", padx=15, pady=10, highlightthickness=1, highlightbackground=COLOR_ACCENT)
        kpi_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(kpi_frame, text="Gesamtwert:", font=("Segoe UI", 12), background=kpi_frame.cget("bg")).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=f"{total_value:.2f} €", font=("Segoe UI", 16, "bold"), foreground="#28a745", background=kpi_frame.cget("bg")).grid(row=0, column=1, sticky="w", padx=15, pady=2)
        
        ttk.Label(kpi_frame, text="Lagermenge:", font=("Segoe UI", 12), background=kpi_frame.cget("bg")).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=f"{(total_weight/1000):.2f} kg", font=("Segoe UI", 14, "bold"), background=kpi_frame.cget("bg")).grid(row=1, column=1, sticky="w", padx=15, pady=2)
        
        ttk.Label(kpi_frame, text="Aktive Spulen:", font=("Segoe UI", 12), background=kpi_frame.cget("bg")).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(kpi_frame, text=str(total_spools), font=("Segoe UI", 14, "bold"), background=kpi_frame.cget("bg")).grid(row=2, column=1, sticky="w", padx=15, pady=2)

        # Tabbed breakdowns
        breakdown_notebook = ttk.Notebook(left_panel)
        breakdown_notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Tab 1: Material
        tab_mat = ttk.Frame(breakdown_notebook)
        breakdown_notebook.add(tab_mat, text="Material")
        
        tree_mat = ttk.Treeview(tab_mat, columns=("mat", "count", "weight", "value", "avg"), show="headings", height=6)
        for col, head, w in zip(("mat", "count", "weight", "value", "avg"), ("Material", "Stk", "Gewicht", "Wert", "Ø Preis/kg"), (100, 50, 75, 75, 75)): 
            tree_mat.heading(col, text=head, command=lambda c=col: self.sort_column(tree_mat, c, False))
            tree_mat.column(col, width=w, anchor="center" if col != "mat" else "w")
        tree_mat.pack(fill="both", expand=True)
        
        for mat, stats in sorted(mat_stats.items(), key=lambda x: x[1]['value'], reverse=True): 
            kg = stats['weight'] / 1000
            avg_price = (stats['value'] / kg) if kg > 0 else 0
            tree_mat.insert("", "end", values=(mat, f"{stats['count']} Stk", f"{kg:.2f} kg", f"{stats['value']:.2f} €", f"{avg_price:.2f} €"))

        # Tab 2: Hersteller
        tab_brand = ttk.Frame(breakdown_notebook)
        breakdown_notebook.add(tab_brand, text="Hersteller")
        
        tree_brand = ttk.Treeview(tab_brand, columns=("brand", "count", "weight", "value", "avg"), show="headings", height=6)
        for col, head, w in zip(("brand", "count", "weight", "value", "avg"), ("Hersteller", "Stk", "Gewicht", "Wert", "Ø Preis/kg"), (100, 50, 75, 75, 75)): 
            tree_brand.heading(col, text=head, command=lambda c=col: self.sort_column(tree_brand, c, False))
            tree_brand.column(col, width=w, anchor="center" if col != "brand" else "w")
        tree_brand.pack(fill="both", expand=True)
        
        for brand, stats in sorted(brand_stats.items(), key=lambda x: x[1]['value'], reverse=True): 
            kg = stats['weight'] / 1000
            avg_price = (stats['value'] / kg) if kg > 0 else 0
            tree_brand.insert("", "end", values=(brand, f"{stats['count']} Stk", f"{kg:.2f} kg", f"{stats['value']:.2f} €", f"{avg_price:.2f} €"))

        # Tab 3: Farbe
        tab_color = ttk.Frame(breakdown_notebook)
        breakdown_notebook.add(tab_color, text="Farbe")
        
        tree_color = ttk.Treeview(tab_color, columns=("color", "count", "weight", "value", "avg"), show="headings", height=6)
        for col, head, w in zip(("color", "count", "weight", "value", "avg"), ("Farbe", "Stk", "Gewicht", "Wert", "Ø Preis/kg"), (100, 50, 75, 75, 75)): 
            tree_color.heading(col, text=head, command=lambda c=col: self.sort_column(tree_color, c, False))
            tree_color.column(col, width=w, anchor="center" if col != "color" else "w")
        tree_color.pack(fill="both", expand=True)
        
        for color, stats in sorted(color_stats.items(), key=lambda x: x[1]['value'], reverse=True): 
            kg = stats['weight'] / 1000
            avg_price = (stats['value'] / kg) if kg > 0 else 0
            tree_color.insert("", "end", values=(color, f"{stats['count']} Stk", f"{kg:.2f} kg", f"{stats['value']:.2f} €", f"{avg_price:.2f} €"))

        # Tab 4: Detailliert
        tab_detailed = ttk.Frame(breakdown_notebook)
        breakdown_notebook.add(tab_detailed, text="Detailliert")
        
        tree_detailed = ttk.Treeview(tab_detailed, columns=("brand", "material", "color", "count", "weight", "value"), show="headings", height=6)
        for col, head, w in zip(("brand", "material", "color", "count", "weight", "value"), ("Hersteller", "Material", "Farbe", "Stk", "Gewicht", "Wert"), (100, 80, 80, 40, 60, 60)): 
            tree_detailed.heading(col, text=head, command=lambda c=col: self.sort_column(tree_detailed, c, False))
            tree_detailed.column(col, width=w, anchor="center" if col in ("count", "weight", "value") else "w")
        tree_detailed.pack(fill="both", expand=True)
        
        for (brand, mat, color), stats in sorted(detailed_stats.items(), key=lambda x: (x[0][0].lower(), x[0][1].lower(), x[0][2].lower())):
            kg = stats['weight'] / 1000
            tree_detailed.insert("", "end", values=(brand, mat, color, f"{stats['count']} Stk", f"{kg:.2f} kg", f"{stats['value']:.2f} €"))

        # --- 4. RECHTE SEITE (Verbrauchs-Chart) ---
        ttk.Label(right_panel, text="Verbrauch der letzten 7 Tage:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        today = datetime.date.today()
        last_7_days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        
        filtered_history = {day: 0.0 for day in last_7_days}
        for item in filtered_spools:
            for h in item.get("history", []):
                h_date = h.get("date", "")
                if not h_date: continue
                day_str = h_date.split(" ")[0]
                if day_str in filtered_history:
                    change_str = h.get("change", "0").replace("g", "").replace(" ", "").replace(",", ".").strip()
                    try:
                        change_val = float(change_str)
                        if change_val < 0:
                            filtered_history[day_str] += abs(change_val)
                    except ValueError:
                        pass
        
        values = [filtered_history[day] for day in last_7_days]
        max_val = max(values) if max(values) > 0 else 100 
        
        c_width, c_height = 420, 260
        canvas_bg = "#1e1e1e" if "dark" in str(self.cget('bg')) else "#f9f9f9"
        canvas = tk.Canvas(right_panel, width=c_width, height=c_height, bg=canvas_bg, highlightthickness=1, highlightbackground="#333")
        canvas.pack(fill="both", expand=True, pady=0)
        
        text_col = "white" if "dark" in str(self.cget('bg')) else "black"
        for i in range(4):
            y_line = 40 + i * ((c_height - 80) / 3)
            val_line = max_val - (i * (max_val / 3))
            canvas.create_line(40, y_line, c_width - 20, y_line, fill="#444", dash=(4, 4))
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
            
            color = COLOR_ACCENT if val > 0 else ("#333333" if "dark" in str(self.cget('bg')) else "#dddddd")
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            
            if val > 0:
                canvas.create_text(x0 + bar_width/2, y0 - 12, text=f"{int(val)}g", fill=text_col, font=("Segoe UI", 9, "bold"))
                
            day_obj = datetime.datetime.strptime(last_7_days[i], "%Y-%m-%d")
            day_name = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][day_obj.weekday()]
            font_w = ("Segoe UI", 10, "bold") if i == 6 else ("Segoe UI", 9)
            col_w = COLOR_ACCENT if i == 6 else "gray"
            canvas.create_text(x0 + bar_width/2, c_height - 20, text=day_name, fill=col_w, font=font_w)

        total_7d = sum(values)
        ttk.Label(right_panel, text=f"Gesamtverbrauch (7 Tage): {total_7d:.1f} g", font=("Segoe UI", 10, "italic"), foreground="gray").pack(anchor="e", pady=2)

        # --- 5. FOOTER BUTTONS ---
        btn_frm = ttk.Frame(self.main_content)
        btn_frm.pack(fill="x", side="bottom", pady=10, padx=20)
        
        ttk.Button(btn_frm, text="Schließen", command=self.on_close, style="Accent.TButton").pack(side="right", padx=5)
        self.lbl_total = ttk.Label(btn_frm, text="", font=("Segoe UI", 12, "bold"), foreground=COLOR_ACCENT)
        self.lbl_total.pack(side="left")

        # --- 6. UNTERER BEREICH (Tabelle) ---
        ttk.Separator(self.main_content, orient="horizontal").pack(fill="x", padx=20, pady=10)
        
        hist_lbl_frm = ttk.Frame(self.main_content)
        hist_lbl_frm.pack(fill="x", padx=20, pady=(0, 5))
        ttk.Label(hist_lbl_frm, text="📜 Globale Druck-Historie", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(hist_lbl_frm, text="Alle protokollierten Verbräuche (Doppelklick zum Bearbeiten/Löschen)", foreground="gray").pack(side="left", padx=10)

        history_frm = ttk.Frame(self.main_content)
        history_frm.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        self.history_map = {}
        all_prints = []
        for item in filtered_spools:
            hist = item.get("history", [])
            color_clean = re.sub(r'\s*\(\s*#[0-9a-fA-F]{6}\s*\)', '', item.get('color', '')).strip()
            spool_name = f"[{item.get('id', '?')}] {item.get('brand', '')} {color_clean}"
            
            for idx, h in enumerate(hist):
                all_prints.append({
                    "spool_id": item['id'],
                    "hist_idx": idx,
                    "date": h.get("date", ""),
                    "action": h.get("action", ""),
                    "spool": spool_name,
                    "change": h.get("change", ""),
                    "cost": h.get("cost", "-"),
                    "sell": h.get("sell_price", "-")
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

        self.tree_hist.column("date", width=130)
        self.tree_hist.column("action", width=310)
        self.tree_hist.column("spool", width=240)
        self.tree_hist.column("change", width=80, anchor="e")
        self.tree_hist.column("cost", width=80, anchor="e")
        self.tree_hist.column("sell", width=80, anchor="e")
        
        scroll_hist = ttk.Scrollbar(history_frm, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=scroll_hist.set)
        
        self.tree_hist.pack(side="left", fill="both", expand=True)
        scroll_hist.pack(side="right", fill="y")
        
        self.tree_hist.bind("<Double-1>", self.on_edit_entry)

        total_costs = 0.0
        for p in all_prints:
            iid = self.tree_hist.insert("", "end", values=(p["date"], p["action"], p["spool"], p["change"], p["cost"], p["sell"]))
            self.history_map[iid] = {"spool_id": p["spool_id"], "hist_idx": p["hist_idx"]}
            try:
                c_str = p["cost"].replace(" €", "").replace(",", ".")
                total_costs += float(c_str)
            except:
                pass

        self.lbl_total.config(text=f"Gesamtkosten aller Einträge: {total_costs:.2f} €")
    
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
        
        for widget in self.side_panel.winfo_children():
            widget.destroy()
            
        self.side_panel.pack(side="right", fill="y", before=self.main_content)
        
        header = ttk.Frame(self.side_panel)
        header.pack(fill="x", pady=10, padx=10)
        ttk.Label(header, text="✏️ Eintrag bearbeiten", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(header, text="❌", width=3, command=self.side_panel.pack_forget).pack(side="right")
        ttk.Separator(self.side_panel, orient="horizontal").pack(fill="x")
        
        frm = ttk.Frame(self.side_panel, padding=10)
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

        btn_calc_cost = ttk.Button(frm_cost, text="🧮 Mat.", width=8, command=calc_cost)
        btn_calc_cost.pack(side="left", padx=(0, 5))
        
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
                margin = int(self.app.settings.get("profit_margin", 0))
                vk_val = cost_val * (1 + (margin / 100.0))
                ent_sell.delete(0, tk.END)
                ent_sell.insert(0, f"{vk_val:.2f} €")
                if margin == 0:
                    messagebox.showinfo("Info", "Gewinnmarge ist 0%. VK = Kosten.", parent=self)
            except ValueError:
                messagebox.showerror("Fehler", "Bitte Kosten eintragen!", parent=self)
                
        btn_calc_vk = ttk.Button(frm_sell, text="🧮 Marge", width=8, command=calc_vk)
        btn_calc_vk.pack(side="left", padx=(0, 5))
        
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

        btn_frm_action = ttk.Frame(self.side_panel)
        btn_frm_action.pack(fill="x", pady=10, padx=10, side="bottom")
        ttk.Button(btn_frm_action, text="🗑️", command=delete, style="Delete.TButton", width=3).pack(side="left", padx=5)
        ttk.Button(btn_frm_action, text="💾 Speichern", command=save, style="Accent.TButton").pack(side="right", padx=5)

    def on_close(self):
        try:
            self.app.settings["statistics_dialog_geometry"] = self.geometry()
            self.app.data_manager.save_settings(self.app.settings)
        except:
            pass
        self.destroy()
