# core/shelf_visualizer.py

import tkinter as tk
from tkinter import ttk
from core.utils import center_window, get_colors_from_text, create_color_icon
from core.logic import parse_shelves_string, calculate_net_weight
from core.constants import COLOR_ACCENT

class ShelfVisualizer(tk.Toplevel):
    def __init__(self, parent, inventory, settings, spools, app_instance=None):
        super().__init__(parent)
        self.inventory = inventory
        self.settings = settings
        self.spools = spools
        self.app = app_instance
        self.title("Regal & AMS Übersicht")
        self.geometry("1200x850")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        
        # --- Drag & Drop Variablen ---
        self.drag_source = None
        self.drag_window = None

        # Toolbar for pinning and zoom options
        self.toolbar = ttk.Frame(self, padding=(10, 5))
        self.toolbar.pack(side="top", fill="x")
        
        self.var_ams_fixed = tk.BooleanVar(value=self.settings.get("ams_fixed_top", False))
        chk_fixed = ttk.Checkbutton(self.toolbar, text="🤖 AMS oben fixieren", variable=self.var_ams_fixed, command=self.toggle_ams_fixed)
        chk_fixed.pack(side="left")
        
        ttk.Label(self.toolbar, text="🔍 Symbolgröße:").pack(side="left", padx=(15, 5))
        zoom_val = self.settings.get("shelf_zoom", "Mittel")
        if zoom_val not in ["Klein", "Mittel", "Groß"]:
            zoom_val = "Mittel"
        self.combo_zoom = ttk.Combobox(self.toolbar, values=["Klein", "Mittel", "Groß"], state="readonly", width=8)
        self.combo_zoom.set(zoom_val)
        self.combo_zoom.pack(side="left")
        self.combo_zoom.bind("<<ComboboxSelected>>", self.on_zoom_change)
        
        self.fixed_ams_container = ttk.LabelFrame(self, text="📌 Angeheftete AMS-Einheiten", padding=(10, 5))
        
        self.canvas_container = ttk.Frame(self)
        self.canvas_container.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_container, bg=parent.cget('bg'), highlightthickness=0)
        v_scroll = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(self.canvas_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.frame = ttk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        
        self.redraw()

        def _on_mousewheel(event):
            try:
                if self.canvas.winfo_exists():
                    self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except: pass
        self.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.frame.bind("<MouseWheel>", _on_mousewheel)
        self.toolbar.bind("<MouseWheel>", _on_mousewheel)
        self.fixed_ams_container.bind("<MouseWheel>", _on_mousewheel)

    def toggle_ams_fixed(self):
        self.settings["ams_fixed_top"] = self.var_ams_fixed.get()
        if self.app:
            self.app.data_manager.save_settings(self.settings)
        self.redraw()

    def on_zoom_change(self, event=None):
        self.settings["shelf_zoom"] = self.combo_zoom.get()
        if self.app:
            self.app.data_manager.save_settings(self.settings)
        self.redraw()

    def redraw(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        for widget in self.fixed_ams_container.winfo_children():
            widget.destroy()
            
        self.image_cache = []
        self.widget_data = {} 
        
        zoom = self.settings.get("shelf_zoom", "Mittel")
        if zoom == "Klein":
            m = 0.75
            self.current_font = ("Segoe UI", 7, "bold")
        elif zoom == "Groß":
            m = 1.3
            self.current_font = ("Segoe UI", 10, "bold")
        else:
            m = 1.0
            self.current_font = ("Segoe UI", 8, "bold")
        
        self.parsed_shelves = parse_shelves_string(self.settings.get("shelves", "REGAL|4|8"))
        
        self.shelf_data = {}
        self.ams_data = {}
        self.other_data = {"LAGER": []}
        
        for item in self.inventory:
            try:
                t = str(item.get('type', ''))
                loc = str(item.get('loc_id', ''))
                if t in [s['name'] for s in self.parsed_shelves]: self.shelf_data[f"{t}_{loc}"] = item
                elif t.startswith("AMS"): self.ams_data[f"{t}_{loc}"] = item
                elif t and t != "VERBRAUCHT":
                    if t not in self.other_data: self.other_data[t] = []
                    self.other_data[t].append(item)
            except: pass
            
        # Pinned AMS at the top
        if self.var_ams_fixed.get() and self.settings.get("num_ams", 1) > 0:
            self.fixed_ams_container.pack(side="top", fill="x", padx=10, pady=(2, 6), before=self.canvas_container)
            ams_wrapper = ttk.Frame(self.fixed_ams_container)
            ams_wrapper.pack(fill="x")
            for a in range(1, self.settings.get("num_ams", 1) + 1):
                ams_name = f"AMS {a}"
                ams_unit_frm = ttk.Frame(ams_wrapper)
                ams_unit_frm.pack(side="left", padx=8, anchor="n")
                
                ttk.Label(ams_unit_frm, text=ams_name, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(2, 1))
                ams_frame = tk.Frame(ams_unit_frm, bg="#444444", padx=4, pady=4)
                ams_frame.pack(anchor="w")
                for i in range(1, 5): 
                    cont = tk.Frame(ams_frame, bg="#444444")
                    cont.pack(side="left", fill="y", padx=3)
                    ttk.Label(cont, text=f"Slot {i}", foreground="white", background="#444444", font=("Segoe UI", 7)).pack(pady=(0, 1))
                    self.draw_slot(cont, str(i), self.ams_data.get(f"{ams_name}_{i}"), True, int(75 * m), int(55 * m), ams_name, str(i))
        else:
            self.fixed_ams_container.pack_forget()
            
        pad = ttk.Frame(self.frame, padding=20)
        pad.pack(fill="both", expand=True)
        
        lbl_r = self.settings.get("label_row", "Fach")
        lbl_c = self.settings.get("label_col", "Slot")
        logistics = self.settings.get("logistics_order", False)
        all_shelf_names = self.settings.get("shelf_names_v2", {})
        
        for shelf in self.parsed_shelves:
            ttk.Label(pad, text=f"📦 {shelf['name']}", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 10))
            shelf_names = all_shelf_names.get(shelf['name'], {})
            for r in (range(shelf['rows'], 0, -1) if logistics else range(1, shelf['rows'] + 1)):
                row_label = shelf_names.get(str(r), f"{lbl_r} {r}")
                ttk.Label(pad, text=row_label, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
                row_frame = tk.Frame(pad, bg="#8B4513", padx=5, pady=2)
                row_frame.pack(anchor="w", pady=2)
                is_double = self.settings.get("double_depth", False)
                for c in range(1, shelf['cols'] + 1):
                    col_label = shelf_names.get(f"col_{c}", f"{lbl_c} {c}")
                    short_label = col_label.replace(f"{lbl_c} ", "") if col_label.startswith(f"{lbl_c} ") else col_label
                    
                    if is_double:
                        slot_container = tk.Frame(row_frame, bg="#8B4513")
                        slot_container.pack(side="left", padx=2)
                        
                        frm_h = tk.Frame(slot_container, bg="#8B4513")
                        frm_h.pack(side="top", pady=(0, 1))
                        frm_v = tk.Frame(slot_container, bg="#8B4513")
                        frm_v.pack(side="top", pady=(1, 0))
                        
                        slot_name_h = f"{row_label} - {col_label} (H)"
                        self.draw_slot(frm_h, f"{short_label} (H)", self.shelf_data.get(f"{shelf['name']}_{slot_name_h}"), False, int(65 * m), int(35 * m), shelf['name'], slot_name_h)
                        
                        slot_name_v = f"{row_label} - {col_label} (V)"
                        self.draw_slot(frm_v, f"{short_label} (V)", self.shelf_data.get(f"{shelf['name']}_{slot_name_v}"), False, int(65 * m), int(35 * m), shelf['name'], slot_name_v)
                    else:
                        slot_name = f"{row_label} - {col_label}"
                        self.draw_slot(row_frame, short_label, self.shelf_data.get(f"{shelf['name']}_{slot_name}"), False, int(70 * m), int(70 * m), shelf['name'], slot_name)
                    
        if not self.var_ams_fixed.get():
            ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20)
            for a in range(1, self.settings.get("num_ams", 1) + 1):
                ams_name = f"AMS {a}"
                ttk.Label(pad, text=ams_name, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 5))
                ams_frame = tk.Frame(pad, bg="#444444", padx=10, pady=10)
                ams_frame.pack(anchor="w")
                for i in range(1, 5): 
                    cont = tk.Frame(ams_frame, bg="#444444")
                    cont.pack(side="left", fill="y", padx=10)
                    ttk.Label(cont, text=f"Slot {i}", foreground="white", background="#444444").pack(pady=(0, 5))
                    self.draw_slot(cont, str(i), self.ams_data.get(f"{ams_name}_{i}"), True, int(120 * m), int(100 * m), ams_name, str(i))
                
        if self.other_data:
            ttk.Separator(pad, orient="horizontal").pack(fill="x", pady=20)
            ttk.Label(pad, text="📦 Weitere Lagerorte (Drag & Drop ins Regal & Lager möglich!)", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 5))
            for loc_name, items in self.other_data.items():
                if not items and loc_name != "LAGER": 
                    continue
                    
                ttk.Label(pad, text=loc_name, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
                loc_frame = tk.Frame(pad, bg="#333333", padx=5, pady=5)
                loc_frame.pack(anchor="w", pady=2)
                col_count, row_frame = 0, tk.Frame(loc_frame, bg="#333333")
                row_frame.pack(anchor="w")
                
                for item in items:
                    if col_count >= 10: 
                        col_count = 0
                        row_frame = tk.Frame(loc_frame, bg="#333333")
                        row_frame.pack(anchor="w", pady=(5,0))
                        
                    item_loc_id = item.get("loc_id", "") or "-"
                    self.draw_slot(row_frame, item_loc_id, item, False, int(80 * m), int(70 * m), loc_name, item_loc_id)
                    col_count += 1
                    
                if col_count >= 10:
                    row_frame = tk.Frame(loc_frame, bg="#333333")
                    row_frame.pack(anchor="w", pady=(5,0))
                
                self.draw_slot(row_frame, "➕\nAblegen", None, False, int(80 * m), int(70 * m), loc_name, "-")

    def draw_slot(self, parent, label, item, is_ams, w=90, h=80, loc_type=None, loc_id=None):
        bg_colors, fg_col, txt, tooltip = ["#D2B48C"] if not is_ams else ["#666666"], "#555" if not is_ams else "#CCC", f"{label}\nLEER", "Leer"
        if item:
            cols = get_colors_from_text(item.get('color', ''))
            bg_colors = cols or ["#FFFFFF"]
            if bg_colors[0].startswith("#"):
                r, g, b = int(bg_colors[0][1:3], 16), int(bg_colors[0][3:5], 16), int(bg_colors[0][5:7], 16)
                fg_col = "white" if (r*0.299 + g*0.587 + b*0.114) < 128 else "black"
            else: fg_col = "black"
            sub = item.get('subtype', '')
            mat = item.get('material', '')
            net = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), self.spools, item.get('empty_weight'))
            abk = {"Standard": "Std.", "High Speed": "HS", "Dual Color": "Dual", "Tri Color": "Tri", "Glow in Dark": "Glow", "Transparent": "Transp.", "Translucent": "Transl.", "Glitzer/Sparkle": "Glitz."}
            sub_short = abk.get(sub, sub[:7])
            mat_short = mat[:5] 
            txt = f"{label}\n{item['brand'][:10]}\n{mat_short} {sub_short}\n{net}g"
            tooltip = f"ID: {item['id']}\n{item['brand']} - {item.get('color', '')}\n{item.get('material', '')} | Rest: {net}g"
            
        img = create_color_icon(bg_colors, (w, h), "black")
        self.image_cache.append(img)
        font_style = getattr(self, 'current_font', ("Segoe UI", 8, "bold"))
        lbl = tk.Label(parent, image=img, text=txt, compound="center", fg=fg_col, font=font_style, borderwidth=1, relief="flat")
        lbl.pack(side="left", padx=2, fill="y")
        
        if loc_type and loc_id:
            self.widget_data[id(lbl)] = {
                "loc_type": loc_type,
                "loc_id": loc_id,
                "item": item,
                "img": img
            }
            lbl.config(cursor="hand2")
            
            lbl.bind("<ButtonPress-1>", self.on_drag_start)
            lbl.bind("<B1-Motion>", self.on_drag_motion)
            lbl.bind("<ButtonRelease-1>", self.on_drag_release)
            
        lbl.bind("<Enter>", lambda e: self.show_tip(e, tooltip), add="+")
        lbl.bind("<Leave>", self.hide_tip, add="+")

    def check_auto_scroll(self):
        if not getattr(self, 'drag_source', None):
            return
        try:
            mx = self.winfo_pointerx() - self.canvas.winfo_rootx()
            my = self.winfo_pointery() - self.canvas.winfo_rooty()
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            
            margin = 50
            if my < margin:
                self.canvas.yview_scroll(-1, "units")
            elif my > ch - margin:
                self.canvas.yview_scroll(1, "units")
                
            if mx < margin:
                self.canvas.xview_scroll(-1, "units")
            elif mx > cw - margin:
                self.canvas.xview_scroll(1, "units")
        except Exception:
            pass
        self.after(50, self.check_auto_scroll)

    def on_drag_start(self, event):
        widget = event.widget
        data = self.widget_data.get(id(widget))
        if not data or not data["item"]: return
        
        self.drag_source = widget
        
        self.drag_window = tk.Toplevel(self)
        self.drag_window.wm_overrideredirect(True)
        self.drag_window.attributes('-alpha', 0.8)
        tk.Label(self.drag_window, image=data["img"], borderwidth=2, relief="solid", bg=COLOR_ACCENT).pack()
        self.drag_window.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")
        
        self.check_auto_scroll()

    def on_drag_motion(self, event):
        drag_win = getattr(self, 'drag_window', None)
        if drag_win:
            drag_win.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

    def on_drag_release(self, event):
        drag_win = getattr(self, 'drag_window', None)
        if drag_win:
            drag_win.destroy()
            self.drag_window = None
            
        if not getattr(self, 'drag_source', None): return
        
        target_widget = self.winfo_containing(event.x_root, event.y_root)
        if target_widget and id(target_widget) in self.widget_data:
            
            source_data = self.widget_data[id(self.drag_source)]
            target_data = self.widget_data[id(target_widget)]
            
            s_type = source_data["loc_type"]
            s_id = source_data["loc_id"]
            
            t_type = target_data["loc_type"]
            t_id = target_data["loc_id"]
            
            if s_type == t_type and s_id == t_id:
                self.drag_source = None
                return
                
            source_item = source_data["item"]
            target_item = target_data["item"]
            
            source_item['type'] = t_type
            source_item['loc_id'] = t_id
            if target_item:
                target_item['type'] = s_type
                target_item['loc_id'] = s_id
                
            app_inst = getattr(self, 'app', None)
            if app_inst:
                app_inst.data_manager.save_inventory(app_inst.inventory)
                app_inst.refresh_table()
                
            self.redraw()
            
        self.drag_source = None

    def show_tip(self, event, text): 
        if getattr(self, 'drag_window', None): return
        self.tip = tk.Toplevel(self)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
        tk.Label(self.tip, text=text, bg="#FFFFE0", relief="solid", borderwidth=1, padx=5, pady=2).pack()
        
    def hide_tip(self, event):
        if hasattr(self, 'tip'): self.tip.destroy()
