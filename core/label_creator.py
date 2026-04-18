import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
from qrcode.image.pil import PilImage
from core.utils import center_window, get_colors_from_text

class LabelCreatorDialog(tk.Toplevel):
    def __init__(self, parent, inventory):
        super().__init__(parent)
        self.inventory = [i for i in inventory if i.get('type') != 'VERBRAUCHT']
        self.title("🏷️ Label Creator")
        self.geometry("850x500")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)

        frm_left = ttk.Frame(self, padding=10)
        frm_left.pack(side="left", fill="y")
        
        ttk.Label(frm_left, text="Spule auswählen:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.listbox = tk.Listbox(frm_left, width=40, font=("Segoe UI", 10))
        self.listbox.pack(fill="both", expand=True)
        
        for i in self.inventory:
            self.listbox.insert(tk.END, f"[{i['id']}] {i.get('brand','')} {i.get('material','')} {i.get('color','')}")
            
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        frm_right = ttk.Frame(self, padding=10)
        frm_right.pack(side="right", fill="both", expand=True)
        
        ttk.Label(frm_right, text="Druck-Vorschau:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.lbl_preview = tk.Label(frm_right, bg="gray", relief="solid", borderwidth=1)
        self.lbl_preview.pack(pady=10, expand=True)
        
        btn_frm = ttk.Frame(frm_right)
        btn_frm.pack(fill="x", side="bottom", pady=10)
        
        ttk.Button(btn_frm, text="💾 Aktuelles Label als PNG", command=self.save_label).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frm, text="📑 ALLE als PDF exportieren", command=self.trigger_pdf_export, style="Accent.TButton").pack(side="right")
        
        self.current_img = None
        self.current_item = None
        
    def on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        self.current_item = self.inventory[sel[0]]
        self.generate_label(self.current_item)
        
    def generate_label(self, item):
        try:
            try:
                # Versucht Standard Windows-Fonts zu laden
                font_title = ImageFont.truetype("arialbd.ttf", 45)
                font_sub = ImageFont.truetype("arial.ttf", 35)
                font_small = ImageFont.truetype("arial.ttf", 25)
            except:
                # Fallback
                font_title = font_sub = font_small = ImageFont.load_default()
                
            # Wir erstellen ein hochauflösendes Label (2:1 Format, perfekt für Rollen-Etiketten)
            img = Image.new('RGB', (800, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # 1. QR Code generieren & einfügen
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(f"ID:{item['id']}") 
            qr.make(fit=True)
            
            # FIX: Wir zwingen die Bibliothek, ein echtes PIL-Bild zu generieren
            qr_wrapper = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
            
            # get_image() holt das reine PIL-Objekt heraus, convert('RGB') macht es kompatibel
            qr_img = qr_wrapper.get_image().convert('RGB')
            qr_img = qr_img.resize((360, 360)) 
            img.paste(qr_img, (20, 20))
            
            # 2. Texte auf die rechte Seite schreiben
            brand = item.get('brand', 'Unbekannt')
            mat = item.get('material', 'PLA')
            color = item.get('color', 'Unbekannt')
            sub = item.get('subtype', 'Standard')
            temp_n = item.get('temp_n', '-')
            temp_b = item.get('temp_b', '-')
            
            draw.text((400, 30), f"{brand} {mat}", fill="black", font=font_title)
            draw.text((400, 100), f"{color}", fill="#333333", font=font_sub)
            draw.text((400, 150), f"{sub}", fill="#666666", font=font_sub)
            
            draw.text((400, 240), f"Nozzle: {temp_n} °C", fill="black", font=font_small)
            draw.text((400, 280), f"Bed: {temp_b} °C", fill="black", font=font_small)
            
            # --- NEU: Dynamische Text-Breite für die ID ---
            id_str = str(item['id'])
            # Bei langen IDs das "VibeSpool" weglassen, um Platz zu sparen
            id_text = f"VibeSpool ID: {id_str}" if len(id_str) <= 3 else f"ID: {id_str}"
            # Wenn die ID extrem lang ist, Schriftart verkleinern, damit sie nicht über den Rand ragt
            use_font = font_title if len(id_text) < 14 else font_sub
            
            draw.text((400, 330), id_text, fill="black", font=use_font)
            
            # 3. Farb-Balken zur schnellen Erkennung
            cols = get_colors_from_text(color)
            hex_col = cols[0] if cols else "#FFFFFF"
            draw.rectangle([400, 385, 760, 405], fill=hex_col, outline="black")
            
            self.current_img = img
            
            # 4. Preview für die Anzeige verkleinern
            preview = img.resize((500, 250))
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
            
    def trigger_pdf_export(self):
        # Ruft den neuen Smart Export Dialog auf
        PdfExportDialog(self, self.inventory, getattr(self, 'spools', []))

class PdfExportDialog(tk.Toplevel):
    def __init__(self, parent, inventory, spools):
        super().__init__(parent)
        self.inventory = inventory
        self.spools = spools
        self.title("📑 PDF Smart Export")
        self.geometry("450x300")
        self.configure(bg=parent.cget('bg'))
        center_window(self, parent)
        self.transient(parent)
        self.grab_set()
        self.last_selected_type = "Lager"

        ttk.Label(self, text="Wie möchtest du die Etiketten drucken?", font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))

        self.var_format = tk.StringVar(value="A4")
        
        frm_opts = ttk.Frame(self, padding=10)
        frm_opts.pack(fill="x")
        
        ttk.Radiobutton(frm_opts, text="📄 DIN A4 Bogen (Mehrere pro Seite / Gitter)", variable=self.var_format, value="A4", command=self.toggle_opts).pack(anchor="w", pady=5)
        
        self.frm_grid = ttk.Frame(frm_opts)
        self.frm_grid.pack(fill="x", padx=20)
        ttk.Label(self.frm_grid, text="Spalten:").grid(row=0, column=0, sticky="w")
        self.var_cols = tk.IntVar(value=2)
        ttk.Spinbox(self.frm_grid, from_=1, to=5, textvariable=self.var_cols, width=5).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.frm_grid, text="Reihen:").grid(row=1, column=0, sticky="w")
        self.var_rows = tk.IntVar(value=4)
        ttk.Spinbox(self.frm_grid, from_=1, to=15, textvariable=self.var_rows, width=5).grid(row=1, column=1, padx=5, pady=2)

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
            try:
                font_title = ImageFont.truetype("arialbd.ttf", 45)
                font_sub = ImageFont.truetype("arial.ttf", 35)
                font_small = ImageFont.truetype("arial.ttf", 25)
            except:
                font_title = font_sub = font_small = ImageFont.load_default()

            pdf_pages = []
            
            def draw_single_label(item):
                img = Image.new('RGB', (800, 400), color='white')
                draw = ImageDraw.Draw(img)
                
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(f"ID:{item['id']}") 
                qr.make(fit=True)
                qr_img = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white").get_image().convert('RGB').resize((360, 360)) 
                img.paste(qr_img, (20, 20))
                
                draw.text((400, 30), f"{item.get('brand', '')} {item.get('material', '')}", fill="black", font=font_title)
                draw.text((400, 100), f"{item.get('color', '')}", fill="#333333", font=font_sub)
                draw.text((400, 150), f"{item.get('subtype', 'Standard')}", fill="#666666", font=font_sub)
                draw.text((400, 240), f"Nozzle: {item.get('temp_n', '-')} °C", fill="black", font=font_small)
                draw.text((400, 280), f"Bed: {item.get('temp_b', '-')} °C", fill="black", font=font_small)
                
                id_str = str(item['id'])
                id_text = f"VibeSpool ID: {id_str}" if len(id_str) <= 3 else f"ID: {id_str}"
                use_font = font_title if len(id_text) < 14 else font_sub
                draw.text((400, 330), id_text, fill="black", font=use_font)
                
                cols = get_colors_from_text(item.get('color', ''))
                hex_col = cols[0] if cols else "#FFFFFF"
                draw.rectangle([400, 385, 760, 405], fill=hex_col, outline="black")
                return img

            if self.var_format.get() == "ROLL":
                for item in self.inventory:
                    pdf_pages.append(draw_single_label(item))
            else:
                a4_w, a4_h = 2480, 3508 # DIN A4 bei 300 DPI
                cols, rows = max(1, self.var_cols.get()), max(1, self.var_rows.get())
                label_w, label_h = 800, 400
                margin_x = (a4_w - (cols * label_w)) // (cols + 1)
                margin_y = (a4_h - (rows * label_h)) // (rows + 1)
                
                current_page = Image.new('RGB', (a4_w, a4_h), 'white')
                x_idx, y_idx = 0, 0
                
                for item in self.inventory:
                    lbl_img = draw_single_label(item)
                    pos_x = margin_x + (x_idx * (label_w + margin_x))
                    pos_y = margin_y + (y_idx * (label_h + margin_y))
                    current_page.paste(lbl_img, (pos_x, pos_y))
                    
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
                pdf_pages[0].save(fp, "PDF", resolution=300.0 if self.var_format.get() == "A4" else 100.0, save_all=True, append_images=pdf_pages[1:])
                messagebox.showinfo("Exportiert", f"Erfolg!\n{len(self.inventory)} Etiketten wurden auf {len(pdf_pages)} Seite(n) verteilt.", parent=self)
                self.destroy()

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Generieren:\n{e}", parent=self)