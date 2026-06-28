import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
from qrcode.image.pil import PilImage
from core.utils import center_window, get_colors_from_text

def create_label_image(item, width_mm, height_mm, colors_settings=None):
    width_px = int(width_mm * 10)
    height_px = int(height_mm * 10)
    
    img = Image.new('RGB', (width_px, height_px), color='white')
    draw = ImageDraw.Draw(img)
    
    is_horizontal = (width_px >= height_px)
    
    if is_horizontal:
        qr_size = int(height_px * 0.9)
        margin = int(height_px * 0.05)
        scale = height_px / 400.0
    else:
        qr_size = int(width_px * 0.9)
        margin = int(width_px * 0.05)
        y_offset = qr_size + 2 * margin
        remaining_h = height_px - y_offset
        scale = min(width_px / 400.0, remaining_h / 250.0)
        if scale <= 0:
            scale = 0.1
            
    font_title_size = max(8, int(45 * scale))
    font_sub_size = max(6, int(35 * scale))
    font_small_size = max(5, int(25 * scale))
    
    try:
        font_title = ImageFont.truetype("arialbd.ttf", font_title_size)
        font_sub = ImageFont.truetype("arial.ttf", font_sub_size)
        font_small = ImageFont.truetype("arial.ttf", font_small_size)
    except:
        font_title = font_sub = font_small = ImageFont.load_default()
        
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(f"ID:{item['id']}") 
    qr.make(fit=True)
    qr_wrapper = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
    qr_img = qr_wrapper.get_image().convert('RGB')
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    img.paste(qr_img, (margin, margin))
    
    brand = item.get('brand', 'Unbekannt')
    mat = item.get('material', 'PLA')
    color = item.get('color', 'Unbekannt')
    sub = item.get('subtype', 'Standard')
    temp_n = item.get('temp_n', '-')
    temp_b = item.get('temp_b', '-')
    
    id_str = str(item['id'])
    id_text = f"VibeSpool ID: {id_str}" if len(id_str) <= 3 else f"ID: {id_str}"
    
    cols = get_colors_from_text(color, colors_settings)
    hex_col = cols[0] if cols else "#FFFFFF"
    
    if is_horizontal:
        x_text = qr_size + 2 * margin
        draw.text((x_text, int(30 * scale)), f"{brand} {mat}", fill="black", font=font_title)
        draw.text((x_text, int(100 * scale)), f"{color}", fill="#333333", font=font_sub)
        draw.text((x_text, int(150 * scale)), f"{sub}", fill="#666666", font=font_sub)
        draw.text((x_text, int(240 * scale)), f"Nozzle: {temp_n} °C", fill="black", font=font_small)
        draw.text((x_text, int(280 * scale)), f"Bed: {temp_b} °C", fill="black", font=font_small)
        
        use_font = font_title if len(id_text) < 14 else font_sub
        draw.text((x_text, int(330 * scale)), id_text, fill="black", font=use_font)
        draw.rectangle([x_text, int(385 * scale), width_px - margin, int(400 * scale)], fill=hex_col, outline="black")
    else:
        y_text = qr_size + 2 * margin
        draw.text((margin, y_text + int(10 * scale)), f"{brand} {mat}", fill="black", font=font_title)
        draw.text((margin, y_text + int(45 * scale)), f"{color}", fill="#333333", font=font_sub)
        draw.text((margin, y_text + int(80 * scale)), f"{sub}", fill="#666666", font=font_sub)
        draw.text((margin, y_text + int(120 * scale)), f"Nozzle: {temp_n} °C", fill="black", font=font_small)
        draw.text((margin, y_text + int(150 * scale)), f"Bed: {temp_b} °C", fill="black", font=font_small)
        
        use_font = font_title if len(id_text) < 14 else font_sub
        draw.text((margin, y_text + int(185 * scale)), id_text, fill="black", font=use_font)
        draw.rectangle([margin, height_px - int(15 * scale), width_px - margin, height_px - int(5 * scale)], fill=hex_col, outline="black")
        
    return img


class LabelCreatorDialog(tk.Toplevel):
    def __init__(self, parent, inventory, app_instance=None):
        super().__init__(parent)
        self.app = app_instance
        self.inventory = [i for i in inventory if i.get('type') != 'VERBRAUCHT']
        self.title("🏷️ Label Creator")
        self.configure(bg=parent.cget('bg'))
        
        geom = None
        if self.app and hasattr(self.app, "settings"):
            geom = self.app.settings.get("label_creator_geometry")
            
        if geom:
            self.geometry(geom)
        else:
            self.geometry("850x550")
            center_window(self, parent)
            
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        frm_left = ttk.Frame(self, padding=10)
        frm_left.pack(side="left", fill="y")
        
        ttk.Label(frm_left, text="Spule auswählen:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.listbox = tk.Listbox(frm_left, width=40, font=("Segoe UI", 10))
        self.listbox.pack(fill="both", expand=True)
        
        for i in self.inventory:
            self.listbox.insert(tk.END, f"[{i['id']}] {i.get('brand','')} {i.get('material','')} {i.get('color','')}")
            
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Label size settings at bottom of left panel
        frm_settings = ttk.LabelFrame(frm_left, text="Label-Größe (mm)", padding=10)
        frm_settings.pack(fill="x", pady=(10, 0), side="bottom")
        
        frm_size_inputs = ttk.Frame(frm_settings)
        frm_size_inputs.pack(fill="x")
        
        ttk.Label(frm_size_inputs, text="B:").grid(row=0, column=0, sticky="w")
        self.var_width = tk.IntVar(value=self.app.settings.get("label_width_mm", 80) if (self.app and hasattr(self.app, "settings")) else 80)
        sp_width = ttk.Spinbox(frm_size_inputs, from_=10, to=200, textvariable=self.var_width, width=6)
        sp_width.grid(row=0, column=1, padx=(5, 10))
        ttk.Label(frm_size_inputs, text="mm").grid(row=0, column=2, sticky="w")
        
        ttk.Label(frm_size_inputs, text="H:").grid(row=0, column=3, sticky="w", padx=(10, 0))
        self.var_height = tk.IntVar(value=self.app.settings.get("label_height_mm", 40) if (self.app and hasattr(self.app, "settings")) else 40)
        sp_height = ttk.Spinbox(frm_size_inputs, from_=10, to=200, textvariable=self.var_height, width=6)
        sp_height.grid(row=0, column=4, padx=(5, 10))
        ttk.Label(frm_size_inputs, text="mm").grid(row=0, column=5, sticky="w")
        
        self.var_width.trace_add("write", lambda n, i, m: self.on_size_change())
        self.var_height.trace_add("write", lambda n, i, m: self.on_size_change())

        frm_right = ttk.Frame(self, padding=10)
        frm_right.pack(side="right", fill="both", expand=True)
        
        ttk.Label(frm_right, text="Druck-Vorschau:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.lbl_preview = tk.Label(frm_right, bg="gray", relief="solid", borderwidth=1)
        self.lbl_preview.pack(pady=10, expand=True)
        
        btn_frm = ttk.Frame(frm_right)
        btn_frm.pack(fill="x", side="bottom", pady=10)
        
        ttk.Button(btn_frm, text="💾 PNG Speichern", command=self.save_label).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frm, text="👁️ System-Vorschau", command=self.preview_label).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frm, text="📑 ALLE als PDF exportieren", command=self.trigger_pdf_export, style="Accent.TButton").pack(side="right")
        
        self.current_img = None
        self.current_item = None
        
    def on_size_change(self):
        try:
            w = max(10, self.var_width.get())
            h = max(10, self.var_height.get())
            if self.app and hasattr(self.app, "settings"):
                self.app.settings["label_width_mm"] = w
                self.app.settings["label_height_mm"] = h
                self.app.data_manager.save_settings(self.app.settings)
            
            if self.current_item:
                self.generate_label(self.current_item)
        except Exception:
            pass

    def on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        self.current_item = self.inventory[sel[0]]
        self.generate_label(self.current_item)
        
    def generate_label(self, item):
        try:
            width_mm = self.var_width.get()
            height_mm = self.var_height.get()
            colors_settings = self.app.settings.get('colors') if self.app else None
            
            img = create_label_image(item, width_mm, height_mm, colors_settings)
            self.current_img = img
            
            # Aspect-ratio aware preview resize
            width_px, height_px = img.size
            max_w, max_h = 500, 250
            ratio_img = width_px / height_px
            ratio_box = max_w / max_h
            if ratio_img > ratio_box:
                new_w = max_w
                new_h = int(max_w / ratio_img)
            else:
                new_h = max_h
                new_w = int(max_h * ratio_img)
                
            preview = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(preview)
            self.lbl_preview.config(image=self.photo)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Label konnte nicht generiert werden:\n{e}")

    def save_label(self):
        if not self.current_img or not self.current_item: return
        file_name = f"Label_{self.current_item['id']}_{self.current_item.get('brand', '')}_{self.current_item.get('material', '')}.png"
        fp = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Bild", "*.png")], initialfile=file_name)
        if fp:
            self.current_img.save(fp)
            messagebox.showinfo("Gespeichert", f"Das Etikett wurde erfolgreich gespeichert!\nDu kannst es nun ausdrucken.")

    def preview_label(self):
        if not self.current_img or not self.current_item:
            messagebox.showinfo("Vorschau", "Bitte wähle zuerst eine Spule aus der Liste aus!")
            return
        try:
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            fp = os.path.join(temp_dir, f"VibeSpool_Preview_{self.current_item['id']}.png")
            self.current_img.save(fp)
            os.startfile(fp)
        except Exception as e:
            messagebox.showerror("Fehler", f"Vorschau konnte nicht geöffnet werden:\n{e}")
            
    def trigger_pdf_export(self):
        PdfExportDialog(self, self.inventory, getattr(self.app, 'spools', []) if self.app else [])

    def on_close(self):
        try:
            if self.app and hasattr(self.app, "settings"):
                self.app.settings["label_creator_geometry"] = self.geometry()
                self.app.data_manager.save_settings(self.app.settings)
        except Exception:
            pass
        self.destroy()


class PdfExportDialog(tk.Toplevel):
    def __init__(self, parent, inventory, spools):
        super().__init__(parent)
        self.parent = parent
        self.inventory = inventory
        self.spools = spools
        self.title("📑 PDF Smart Export")
        self.geometry("450x300")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        self.transient(parent)
        self.grab_set()
        
        self.width_mm = parent.app.settings.get("label_width_mm", 80) if (parent and parent.app) else 80
        self.height_mm = parent.app.settings.get("label_height_mm", 40) if (parent and parent.app) else 40

        # Prefill cols & rows dynamically based on size
        default_cols = max(1, int(190 / self.width_mm))
        default_rows = max(1, int(277 / self.height_mm))

        ttk.Label(self, text="Wie möchtest du die Etiketten drucken?", font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))

        self.var_format = tk.StringVar(value="A4")
        
        frm_opts = ttk.Frame(self, padding=10)
        frm_opts.pack(fill="x")
        
        ttk.Radiobutton(frm_opts, text="📄 DIN A4 Bogen (Mehrere pro Seite / Gitter)", variable=self.var_format, value="A4", command=self.toggle_opts).pack(anchor="w", pady=5)
        
        self.frm_grid = ttk.Frame(frm_opts)
        self.frm_grid.pack(fill="x", padx=20)
        ttk.Label(self.frm_grid, text="Spalten:").grid(row=0, column=0, sticky="w")
        self.var_cols = tk.IntVar(value=default_cols)
        ttk.Spinbox(self.frm_grid, from_=1, to=10, textvariable=self.var_cols, width=5).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.frm_grid, text="Reihen:").grid(row=1, column=0, sticky="w")
        self.var_rows = tk.IntVar(value=default_rows)
        ttk.Spinbox(self.frm_grid, from_=1, to=20, textvariable=self.var_rows, width=5).grid(row=1, column=1, padx=5, pady=2)

        ttk.Radiobutton(frm_opts, text="🏷️ Rollen-Etikettendrucker (1 Label = 1 Seite)", variable=self.var_format, value="ROLL", command=self.toggle_opts).pack(anchor="w", pady=(15, 5))

        ttk.Button(self, text="🚀 PDF Generieren", command=self.generate, style="Accent.TButton").pack(pady=15, fill="x", padx=40)

    def toggle_opts(self):
        if self.var_format.get() == "A4":
            self.frm_grid.pack(fill="x", padx=20)
        else:
            self.frm_grid.pack_forget()

    def generate(self):
        fp = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Labels speichern", initialfile="VibeSpool_Labels.pdf")
        if not fp: return

        try:
            pdf_pages = []
            colors_settings = self.parent.app.settings.get('colors') if self.parent and self.parent.app else None
            
            def draw_single_label(item):
                return create_label_image(item, self.width_mm, self.height_mm, colors_settings)

            if self.var_format.get() == "ROLL":
                for item in self.inventory:
                    pdf_pages.append(draw_single_label(item))
            else:
                a4_w, a4_h = 2480, 3508 # DIN A4 at 300 DPI
                cols, rows = max(1, self.var_cols.get()), max(1, self.var_rows.get())
                
                # Scaled size on A4 canvas at 300 DPI (1 mm = 11.811 pixels)
                label_w = int(self.width_mm * 11.811)
                label_h = int(self.height_mm * 11.811)
                
                margin_x = (a4_w - (cols * label_w)) // (cols + 1)
                margin_y = (a4_h - (rows * label_h)) // (rows + 1)
                
                current_page = Image.new('RGB', (a4_w, a4_h), 'white')
                x_idx, y_idx = 0, 0
                
                for item in self.inventory:
                    lbl_img = draw_single_label(item)
                    lbl_img_resized = lbl_img.resize((label_w, label_h), Image.Resampling.LANCZOS)
                    pos_x = margin_x + (x_idx * (label_w + margin_x))
                    pos_y = margin_y + (y_idx * (label_h + margin_y))
                    current_page.paste(lbl_img_resized, (pos_x, pos_y))
                    
                    x_idx += 1
                    if x_idx >= cols:
                        x_idx = 0
                        y_idx += 1
                        
                    if y_idx >= rows:
                        pdf_pages.append(current_page)
                        current_page = Image.new('RGB', (a4_w, a4_h), 'white')
                        x_idx, y_idx = 0, 0
                
                if x_idx > 0 or y_idx > 0:
                    pdf_pages.append(current_page)

            if pdf_pages:
                # ROLL mode saves pages at 254.0 DPI (10 pixels = 1 mm) to match label sizing perfectly.
                # A4 mode saves at 300.0 DPI.
                res_dpi = 254.0 if self.var_format.get() == "ROLL" else 300.0
                pdf_pages[0].save(fp, "PDF", resolution=res_dpi, save_all=True, append_images=pdf_pages[1:])
                messagebox.showinfo("Exportiert", f"Erfolg!\n{len(self.inventory)} Etiketten wurden auf {len(pdf_pages)} Seite(n) verteilt.", parent=self)
                self.destroy()

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Generieren:\n{e}", parent=self)