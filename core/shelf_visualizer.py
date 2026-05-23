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

        self.canvas = tk.Canvas(self, bg=parent.cget('bg'), highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.frame = ttk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        
        self.redraw()

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.frame.bind("<MouseWheel>", _on_mousewheel)

    def redraw(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
            
        self.image_cache = []
        self.widget_data = {} 
        
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
                        self.draw_slot(frm_h, f"{short_label} (H)", self.shelf_data.get(f"{shelf['name']}_{slot_name_h}"), False, 65, 35, shelf['name'], slot_name_h)
                        
                        slot_name_v = f"{row_label} - {col_label} (V)"
                        self.draw_slot(frm_v, f"{short_label} (V)", self.shelf_data.get(f"{shelf['name']}_{slot_name_v}"), False, 65, 35, shelf['name'], slot_name_v)
                    else:
                        slot_name = f"{row_label} - {col_label}"
                        self.draw_slot(row_frame, short_label, self.shelf_data.get(f"{shelf['name']}_{slot_name}"), False, 70, 70, shelf['name'], slot_name)
                    
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
                self.draw_slot(cont, str(i), self.ams_data.get(f"{ams_name}_{i}"), True, 120, 100, ams_name, str(i))
                
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
                    self.draw_slot(row_frame, item_loc_id, item, False, 80, 70, loc_name, item_loc_id)
                    col_count += 1
                    
                if col_count >= 10:
                    row_frame = tk.Frame(loc_frame, bg="#333333")
                    row_frame.pack(anchor="w", pady=(5,0))
                
                self.draw_slot(row_frame, "➕\nAblegen", None, False, 80, 70, loc_name, "-")

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
        lbl = tk.Label(parent, image=img, text=txt, compound="center", fg=fg_col, font=("Segoe UI", 8, "bold"), borderwidth=1, relief="flat")
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
