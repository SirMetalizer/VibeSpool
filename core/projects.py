import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import re
from datetime import datetime
from PIL import Image, ImageTk
from core.utils import center_window, ScrollableFrame
from core.print_queue import PrintQueueDialog, safe_float, decimal_to_hm, safe_int

class ProjectsDialog(tk.Toplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.app.projects_dialog = self
        self.title("📂 Projektverlauf & Druckverwaltung")
        self.configure(bg=parent.cget('bg'))
        
        geom = self.app.settings.get("projects_dialog_geometry")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("1200x800")
            center_window(self, parent)
            
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        
        self.selected_node_id = None
        self.drag_source_job_id = None
        self.projects = self.app.data_manager.load_projects()
        self.jobs = self.app.data_manager.load_jobs()
        
        # Load directory for job images
        db_dir = os.path.dirname(os.path.abspath(self.app.data_manager.filename if hasattr(self.app.data_manager, "filename") else "inventory.json"))
        self.images_dir = os.path.join(db_dir, "job_images")
        
        self.build_ui()

    def build_ui(self):
        # Footer buttons
        btn_frm_footer = ttk.Frame(self, padding=10)
        btn_frm_footer.pack(fill="x", side="bottom")
        ttk.Button(btn_frm_footer, text="Schließen", command=self.on_close).pack(side="right")
        
        # Main layout: Left Treeview, Right detail panel
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # LEFT PANEL (Treeview and toolbar)
        frm_left = ttk.Frame(main_paned)
        main_paned.add(frm_left, weight=1)
        
        # Toolbar above Treeview
        toolbar = ttk.Frame(frm_left, padding=(0, 0, 0, 5))
        toolbar.pack(fill="x")
        
        ttk.Button(toolbar, text="📁+ Neuer Ordner", command=self.create_folder).pack(side="left", padx=2)
        ttk.Button(toolbar, text="✏️ Umbenennen", command=self.rename_folder).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🗑️ Löschen", command=self.delete_folder, style="Delete.TButton").pack(side="left", padx=2)
        
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
        
        ttk.Button(toolbar, text="📋 Neuen Job planen", command=self.plan_new_job_here).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔗 Job zuweisen", command=self.assign_existing_job).pack(side="left", padx=2)
        
        # Treeview
        tree_frm = ttk.Frame(frm_left)
        tree_frm.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(tree_frm, show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frm, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_node_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start, add="+")
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_drop, add="+")
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Button-2>", self.show_context_menu)
        
        # RIGHT PANEL (Detail area)
        self.frm_right = ttk.Frame(main_paned, padding=(15, 0, 0, 0))
        main_paned.add(self.frm_right, weight=1)
        
        self.refresh_tree()
        self.show_default_welcome()

    def refresh_tree(self):
        # Save selection status to restore if possible
        selected = self.tree.selection()
        sel_id = selected[0] if selected else None
        
        self.tree.delete(*self.tree.get_children())
        
        self.projects = self.app.data_manager.load_projects()
        self.jobs = self.app.data_manager.load_jobs()
        
        # Map folders
        folders = [p for p in self.projects if p.get("type", "folder") == "folder"]
        folders_dict = {f["id"]: f for f in folders}
        
        # Add root project node
        root_node = self.tree.insert("", "end", iid="root", text="📁 Projekte / Ordner", open=True)
        
        # Function to add subfolders recursively
        def add_subfolders(parent_id, parent_node):
            # Find subfolders of this parent
            sub_folders = [f for f in folders if f.get("parent_id") == parent_id]
            sub_folders.sort(key=lambda x: x.get("name", "").lower())
            
            for sf in sub_folders:
                sf_id = sf["id"]
                node = self.tree.insert(parent_node, "end", iid=sf_id, text=f"📁 {sf['name']}", open=True)
                
                # Add print jobs inside this folder
                folder_jobs = [j for j in self.jobs if j.get("project_id") == sf_id]
                folder_jobs.sort(key=lambda x: x.get("date", ""), reverse=True)
                
                for job in folder_jobs:
                    job_status = job.get("status", "Geplant")
                    status_emoji = "✅" if "Erledigt" in job_status else "⏳"
                    job_title = job.get("title", "Unbenannt")
                    self.tree.insert(node, "end", iid=f"job_{job['id']}", text=f"{status_emoji} {job_title}")
                
                # Recurse
                add_subfolders(sf_id, node)
                
        # Fill root level folders (parent_id is None or empty)
        root_folders = [f for f in folders if not f.get("parent_id")]
        root_folders.sort(key=lambda x: x.get("name", "").lower())
        
        for rf in root_folders:
            rf_id = rf["id"]
            node = self.tree.insert(root_node, "end", iid=rf_id, text=f"📁 {rf['name']}", open=True)
            
            # Add print jobs inside this root folder
            folder_jobs = [j for j in self.jobs if j.get("project_id") == rf_id]
            folder_jobs.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            for job in folder_jobs:
                job_status = job.get("status", "Geplant")
                status_emoji = "✅" if "Erledigt" in job_status else "⏳"
                job_title = job.get("title", "Unbenannt")
                self.tree.insert(node, "end", iid=f"job_{job['id']}", text=f"{status_emoji} {job_title}")
                
            add_subfolders(rf_id, node)
            
        # Add unassigned jobs node
        unassigned_node = self.tree.insert("", "end", iid="unassigned", text="⏳ Unzugeordnete Druckaufträge", open=True)
        unassigned_jobs = [j for j in self.jobs if not j.get("project_id")]
        unassigned_jobs.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        for job in unassigned_jobs:
            job_status = job.get("status", "Geplant")
            status_emoji = "✅" if "Erledigt" in job_status else "⏳"
            job_title = job.get("title", "Unbenannt")
            self.tree.insert(unassigned_node, "end", iid=f"job_{job['id']}", text=f"{status_emoji} {job_title}")
            
        if sel_id and self.tree.exists(sel_id):
            self.tree.selection_set(sel_id)

    def show_default_welcome(self):
        for widget in self.frm_right.winfo_children():
            widget.destroy()
            
        lbl_welcome = ttk.Label(self.frm_right, text="📂 Projektverwaltung", font=("Segoe UI", 16, "bold"))
        lbl_welcome.pack(anchor="w", pady=(0, 15))
        
        lbl_desc = ttk.Label(self.frm_right, text="Wähle links ein Projekt, einen Unterordner oder einen Druckauftrag aus.\n\nHier kannst du deine 3D-Drucke nach Projekten und Kategorien gliedern und den globalen Druckfortschritt inkl. Materialverbrauch und Kosten analysieren.", justify="left", wraplength=450)
        lbl_desc.pack(anchor="w", pady=10)

    def on_node_select(self, event):
        if getattr(self, 'is_dragging', False):
            return
        sel = self.tree.selection()
        if not sel:
            self.selected_node_id = None
            return
            
        node_id = sel[0]
        self.selected_node_id = node_id
        
        if node_id == "root" or node_id == "unassigned":
            self.show_default_welcome()
        elif node_id.startswith("job_"):
            job_id = node_id[4:]
            self.show_job_details(job_id)
        else:
            self.show_folder_details(node_id)

    def show_folder_details(self, folder_id):
        for widget in self.frm_right.winfo_children():
            widget.destroy()
            
        folder = next((f for f in self.projects if f["id"] == folder_id), None)
        if not folder: return
        
        # Find path
        folders_dict = {f["id"]: f for f in self.projects if f.get("type", "folder") == "folder"}
        
        def get_full_path(fid):
            path = []
            curr = fid
            while curr:
                f = folders_dict.get(curr)
                if f:
                    path.insert(0, f["name"])
                    curr = f.get("parent_id")
                else:
                    break
            return " > ".join(path)
            
        full_path = get_full_path(folder_id)
        
        ttk.Label(self.frm_right, text=f"📁 Ordner: {folder['name']}", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 2))
        ttk.Label(self.frm_right, text=full_path, font=("Segoe UI", 9, "italic"), foreground="gray").pack(anchor="w", pady=(0, 15))
        
        # Calculate stats for this folder (recursive)
        def get_all_descendant_folder_ids(fid):
            descendants = [fid]
            for f in self.projects:
                if f.get("type", "folder") == "folder" and f.get("parent_id") == fid:
                    descendants.extend(get_all_descendant_folder_ids(f["id"]))
            return descendants
            
        all_child_folder_ids = get_all_descendant_folder_ids(folder_id)
        
        # Get all jobs belonging to this folder or subfolders
        folder_jobs = [j for j in self.jobs if j.get("project_id") in all_child_folder_ids]
        
        total_jobs_count = len(folder_jobs)
        completed_jobs = [j for j in folder_jobs if "Erledigt" in j.get("status", "")]
        completed_count = len(completed_jobs)
        planned_count = total_jobs_count - completed_count
        
        total_weight = 0.0
        total_cost = 0.0
        total_sell = 0.0
        total_time = 0.0
        
        for job in folder_jobs:
            total_time += safe_float(job.get("print_time"), 0.0)
            total_weight += safe_float(job.get("est_weight"), 0.0)
            
            # Parse prices
            price_str = job.get("est_price", "0.00")
            nums = re.findall(r'[\d.,]+', price_str)
            cost_val = 0.0
            sell_val = 0.0
            if len(nums) >= 1:
                cost_val = float(nums[0].replace(",", "."))
            if len(nums) >= 2:
                sell_val = float(nums[1].replace(",", "."))
            else:
                sell_val = cost_val
            total_cost += cost_val
            total_sell += sell_val
            
        # Stats KPI Frame
        kpi_frm = tk.Frame(self.frm_right, bg="#1e1e1e" if "dark" in str(self.cget('bg')) else "#ffffff", padx=15, pady=10, highlightthickness=1, highlightbackground="#0078d7")
        kpi_frm.pack(fill="x", pady=(0, 15))
        
        kpi_frm.columnconfigure(0, weight=1)
        kpi_frm.columnconfigure(1, weight=1)
        kpi_frm.columnconfigure(2, weight=1)
        
        # Col 0: Count
        frm_cnt = ttk.Frame(kpi_frm)
        frm_cnt.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frm_cnt, text="Druckaufträge:", font=("Segoe UI", 9), background=kpi_frm.cget("bg")).pack(anchor="w")
        ttk.Label(frm_cnt, text=f"{total_jobs_count} gesamt", font=("Segoe UI", 12, "bold"), background=kpi_frm.cget("bg")).pack(anchor="w")
        ttk.Label(frm_cnt, text=f"({completed_count} erledigt, {planned_count} geplant)", font=("Segoe UI", 8), foreground="gray", background=kpi_frm.cget("bg")).pack(anchor="w")
        
        # Col 1: Weight & Time
        frm_weight = ttk.Frame(kpi_frm)
        frm_weight.grid(row=0, column=1, sticky="nsew")
        ttk.Label(frm_weight, text="Verbrauch / Zeit:", font=("Segoe UI", 9), background=kpi_frm.cget("bg")).pack(anchor="w")
        ttk.Label(frm_weight, text=f"{(total_weight/1000.0):.2f} kg", font=("Segoe UI", 12, "bold"), background=kpi_frm.cget("bg")).pack(anchor="w")
        h, m = decimal_to_hm(total_time)
        ttk.Label(frm_weight, text=f"{h} Std {m} Min Druckzeit", font=("Segoe UI", 8), foreground="gray", background=kpi_frm.cget("bg")).pack(anchor="w")
        
        # Col 2: Financials
        frm_finance = ttk.Frame(kpi_frm)
        frm_finance.grid(row=0, column=2, sticky="nsew")
        ttk.Label(frm_finance, text="Kosten & VK-Wert:", font=("Segoe UI", 9), background=kpi_frm.cget("bg")).pack(anchor="w")
        ttk.Label(frm_finance, text=f"{total_cost:.2f} € Kosten", font=("Segoe UI", 12, "bold"), foreground="#28a745", background=kpi_frm.cget("bg")).pack(anchor="w")
        margin = safe_int(self.app.settings.get("profit_margin"), 0)
        margin_text = f"VK-Wert: {total_sell:.2f} €" if margin > 0 else "Kein Aufschlag"
        ttk.Label(frm_finance, text=margin_text, font=("Segoe UI", 8), foreground="gray", background=kpi_frm.cget("bg")).pack(anchor="w")

        # Table showing jobs in this folder (direct jobs only)
        direct_jobs = [j for j in self.jobs if j.get("project_id") == folder_id]
        direct_jobs.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        ttk.Label(self.frm_right, text="Direkt zugeordnete Aufträge:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(5, 5))
        
        if not direct_jobs:
            ttk.Label(self.frm_right, text="Keine direkten Druckaufträge in diesem Ordner.", font=("Segoe UI", 10, "italic"), foreground="gray").pack(anchor="w", pady=10)
        else:
            tbl_frm = ttk.Frame(self.frm_right)
            tbl_frm.pack(fill="both", expand=True, pady=5)
            
            columns = ("date", "title", "weight", "price", "status")
            tbl = ttk.Treeview(tbl_frm, columns=columns, show="headings", height=8)
            tbl.heading("date", text="Datum")
            tbl.heading("title", text="Titel / Kunde")
            tbl.heading("weight", text="Gewicht")
            tbl.heading("price", text="Preis")
            tbl.heading("status", text="Status")
            
            tbl.column("date", width=80, anchor="center")
            tbl.column("title", width=150)
            tbl.column("weight", width=80, anchor="center")
            tbl.column("price", width=80, anchor="e")
            tbl.column("status", width=90, anchor="center")
            
            tbl.pack(side="left", fill="both", expand=True)
            
            scroll = ttk.Scrollbar(tbl_frm, orient="vertical", command=tbl.yview)
            scroll.pack(side="right", fill="y")
            tbl.configure(yscrollcommand=scroll.set)
            
            for j in direct_jobs:
                tbl.insert("", "end", values=(
                    j.get("date", ""),
                    j.get("title", ""),
                    f"{j.get('est_weight', '0')} g",
                    j.get("est_price", "-"),
                    j.get("status", "")
                ), iid=j["id"])
                
            # Double click a row to open job details
            def on_table_double_click(event):
                sel_row = tbl.selection()
                if sel_row:
                    self.open_job_in_planner(sel_row[0])
                    
            tbl.bind("<Double-1>", on_table_double_click)

    def show_job_details(self, job_id):
        for widget in self.frm_right.winfo_children():
            widget.destroy()
            
        job = next((j for j in self.jobs if j["id"] == job_id), None)
        if not job: return
        
        # Split layout into details left and image preview right
        frm_details_container = ttk.Frame(self.frm_right)
        frm_details_container.pack(fill="both", expand=True)
        
        frm_details = ttk.Frame(frm_details_container)
        frm_details.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        frm_image = ttk.Frame(frm_details_container, width=220)
        frm_image.pack(side="right", fill="y", padx=(10, 0))
        frm_image.pack_propagate(False)
        
        # Load and display image
        ttk.Label(frm_image, text="Modell-Bild:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        lbl_img = tk.Label(frm_image, text="Kein Bild\nhinterlegt", relief="solid", borderwidth=1, bg="#222" if "dark" in str(self.cget('bg')) else "#eee")
        lbl_img.pack(fill="both", expand=True, pady=(0, 10))
        
        img_name = job.get('image_name', '')
        if img_name and os.path.exists(os.path.join(self.images_dir, img_name)):
            try:
                img = Image.open(os.path.join(self.images_dir, img_name))
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                lbl_img.config(image=photo, text="")
                lbl_img.image = photo
            except Exception as e:
                print(f"Error loading image: {e}")
                
        # Texts
        job_status = job.get("status", "Geplant")
        status_emoji = "✅" if "Erledigt" in job_status else "⏳"
        
        ttk.Label(frm_details, text=f"{status_emoji} {job.get('title', 'Unbenannt')}", font=("Segoe UI", 16, "bold"), wraplength=350).pack(anchor="w", pady=(0, 10))
        
        # Form grid
        grid = ttk.Frame(frm_details)
        grid.pack(fill="x", pady=5)
        
        def add_info_row(r, label, value):
            ttk.Label(grid, text=label, font=("Segoe UI", 10, "bold")).grid(row=r, column=0, sticky="w", pady=3, padx=(0, 10))
            ttk.Label(grid, text=value, font=("Segoe UI", 10)).grid(row=r, column=1, sticky="w", pady=3)
            
        add_info_row(0, "Datum:", job.get("date", ""))
        add_info_row(1, "Status:", job.get("status", ""))
        
        printer_id = job.get("printer_id", "")
        printer_name = "- Globaler Standard -"
        if printer_id:
            printers = self.app.settings.get("printers", [])
            printer = next((p for p in printers if p.get("id") == printer_id), None)
            if printer:
                printer_name = printer.get("name", "Drucker")
        add_info_row(2, "Drucker:", printer_name)
        
        # Retrieve spool details
        spool_weights = job.get("spool_weights", {})
        spool_str_list = []
        for sp_id, weight in spool_weights.items():
            sp = next((i for i in self.app.inventory if str(i['id']) == str(sp_id)), None)
            if sp:
                spool_str_list.append(f"[{sp['id']}] {sp.get('brand','')} {sp.get('color','').split('(')[0].strip()} ({weight}g)")
            else:
                spool_str_list.append(f"Spule {sp_id} ({weight}g)")
                
        if not spool_str_list:
            spool_str_list = ["Keine Spulen zugewiesen"]
            
        add_info_row(3, "Material:", "\n".join(spool_str_list))
        add_info_row(4, "Gewicht:", f"{job.get('est_weight', '0')} g")
        
        time_val = safe_float(job.get("print_time"), 0.0)
        h, m = decimal_to_hm(time_val)
        add_info_row(5, "Druckzeit:", f"{h} Std {m} Min")
        add_info_row(6, "Kosten/Preis:", job.get("est_price", "-"))
        
        link = job.get("link", "").strip()
        if link:
            lbl_link = ttk.Label(grid, text="Link:", font=("Segoe UI", 10, "bold"))
            lbl_link.grid(row=7, column=0, sticky="w", pady=3, padx=(0, 10))
            
            btn_link = tk.Label(grid, text=link, font=("Segoe UI", 10), fg="#0078d7", cursor="hand2")
            btn_link.grid(row=7, column=1, sticky="w", pady=3)
            btn_link.bind("<Button-1>", lambda e: self.open_link(link))
            
        notes = job.get("notes", "").strip()
        if notes:
            ttk.Label(frm_details, text="Notizen:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
            lbl_notes = ttk.Label(frm_details, text=notes, font=("Segoe UI", 10, "italic"), justify="left", wraplength=350)
            lbl_notes.pack(anchor="w", pady=2)
            
        # Action Buttons for the job
        frm_actions = ttk.Frame(self.frm_right)
        frm_actions.pack(fill="x", side="bottom", pady=10)
        
        ttk.Button(frm_actions, text="✏️ Im Planer öffnen", style="Accent.TButton", command=lambda: self.open_job_in_planner(job_id)).pack(side="left", padx=5)
        ttk.Button(frm_actions, text="💔 Aus Projekt entfernen", command=lambda: self.remove_job_from_project(job_id)).pack(side="left", padx=5)

    def open_link(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def create_folder(self):
        parent_id = None
        sel = self.tree.selection()
        if sel:
            sel_id = sel[0]
            if sel_id != "root" and sel_id != "unassigned" and not sel_id.startswith("job_"):
                parent_id = sel_id
                
        name = simpledialog.askstring("Neuer Ordner", "Gib einen Namen für den Ordner ein:")
        if not name: return
        name = name.strip()
        if not name: return
        
        import uuid
        new_folder = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "parent_id": parent_id,
            "type": "folder"
        }
        
        self.projects.append(new_folder)
        self.app.data_manager.save_projects(self.projects)
        self.refresh_tree()
        
        # Select the newly created folder
        self.tree.selection_set(new_folder["id"])

    def rename_folder(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "root" or sel[0] == "unassigned" or sel[0].startswith("job_"):
            messagebox.showinfo("Info", "Bitte wähle zuerst einen Ordner aus der Liste aus!")
            return
            
        folder_id = sel[0]
        folder = next((f for f in self.projects if f["id"] == folder_id), None)
        if not folder: return
        
        new_name = simpledialog.askstring("Ordner umbenennen", f"Neuer Name für '{folder['name']}':", initialvalue=folder["name"])
        if not new_name: return
        new_name = new_name.strip()
        if not new_name or new_name == folder["name"]: return
        
        folder["name"] = new_name
        self.app.data_manager.save_projects(self.projects)
        self.refresh_tree()

    def delete_folder(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "root" or sel[0] == "unassigned" or sel[0].startswith("job_"):
            messagebox.showinfo("Info", "Bitte wähle zuerst einen Ordner aus der Liste aus!")
            return
            
        folder_id = sel[0]
        folder = next((f for f in self.projects if f["id"] == folder_id), None)
        if not folder: return
        
        msg = f"Soll der Ordner '{folder['name']}' gelöscht werden?\n\nAlle Druckaufträge darin werden unzugeordnet (NICHT gelöscht)."
        if not messagebox.askyesno("Ordner löschen", msg, parent=self):
            return
            
        # Recursive delete of subfolders & unassignment of print jobs
        def unassign_and_delete(fid):
            # Unassign print jobs in this folder
            for job in self.jobs:
                if job.get("project_id") == fid:
                    job["project_id"] = ""
                    
            # Recursively find and process child folders
            child_folders = [f for f in self.projects if f.get("type", "folder") == "folder" and f.get("parent_id") == fid]
            for cf in child_folders:
                unassign_and_delete(cf["id"])
                
            # Remove this folder
            self.projects = [f for f in self.projects if f["id"] != fid]

        unassign_and_delete(folder_id)
        
        self.app.data_manager.save_projects(self.projects)
        self.app.data_manager.save_jobs(self.jobs)
        self.refresh_tree()
        self.show_default_welcome()

    def plan_new_job_here(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "root" or sel[0] == "unassigned" or sel[0].startswith("job_"):
            messagebox.showinfo("Info", "Bitte wähle zuerst einen Ordner aus der Liste aus!")
            return
            
        folder_id = sel[0]
        # Open planner dialog
        planner = PrintQueueDialog(self, self.app)
        
        # Find folder path
        folders_dict = {f["id"]: f for f in self.projects if f.get("type", "folder") == "folder"}
        
        def get_folder_path(fid):
            path_parts = []
            curr_id = fid
            visited = set()
            while curr_id and curr_id not in visited:
                visited.add(curr_id)
                f = folders_dict.get(curr_id)
                if f:
                    path_parts.insert(0, f["name"])
                    curr_id = f.get("parent_id")
                else:
                    break
            return " / ".join(path_parts)
            
        path = get_folder_path(folder_id)
        if path in planner.project_path_to_id:
            planner.combo_project.set(path)
            
        # Bind close event to refresh self
        def on_planner_close():
            self.refresh_tree()
            self.on_node_select(None)
            planner.destroy()
            
        planner.protocol("WM_DELETE_WINDOW", on_planner_close)

    def assign_existing_job(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "root" or sel[0] == "unassigned" or sel[0].startswith("job_"):
            messagebox.showinfo("Info", "Bitte wähle zuerst einen Ordner aus der Liste aus!")
            return
            
        folder_id = sel[0]
        
        # Get list of unassigned jobs
        unassigned_jobs = [j for j in self.jobs if not j.get("project_id")]
        if not unassigned_jobs:
            messagebox.showinfo("Zuweisen", "Es gibt keine unzugeordneten Druckaufträge im System.")
            return
            
        # Simple selection dialog
        dlg = tk.Toplevel(self)
        dlg.title("Job zuweisen")
        dlg.geometry("400x350")
        center_window(dlg, self)
        dlg.transient(self)
        dlg.grab_set()
        
        ttk.Label(dlg, text="Druckauftrag auswählen:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        listbox = tk.Listbox(dlg, font=("Segoe UI", 10))
        listbox.pack(fill="both", expand=True, padx=15, pady=5)
        
        for j in unassigned_jobs:
            listbox.insert(tk.END, f"[{j['date']}] {j.get('title','Unbenannt')} ({j.get('est_weight','0')}g)")
            
        def do_assign():
            sel_idx = listbox.curselection()
            if not sel_idx:
                messagebox.showwarning("Fehler", "Bitte wähle einen Job aus!", parent=dlg)
                return
            job = unassigned_jobs[sel_idx[0]]
            job["project_id"] = folder_id
            
            # Save
            self.app.data_manager.save_jobs(self.jobs)
            self.refresh_tree()
            self.show_folder_details(folder_id)
            dlg.destroy()
            
        btn_frm = ttk.Frame(dlg, padding=10)
        btn_frm.pack(fill="x")
        ttk.Button(btn_frm, text="Abbrechen", command=dlg.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frm, text="🔗 Zuweisen", command=do_assign, style="Accent.TButton").pack(side="right")

    def remove_job_from_project(self, job_id):
        job = next((j for j in self.jobs if j["id"] == job_id), None)
        if job:
            job["project_id"] = ""
            self.app.data_manager.save_jobs(self.jobs)
            self.refresh_tree()
            self.show_default_welcome()
            messagebox.showinfo("Erfolg", "Druckauftrag wurde aus dem Projekt entfernt.")

    def open_job_in_planner(self, job_id):
        # Open planner dialog and select this job
        planner = PrintQueueDialog(self, self.app)
        
        # Search item in tree or trigger select
        found_iid = None
        for iid in planner.tree.get_children():
            if iid == job_id:
                found_iid = iid
                break
        if not found_iid:
            for iid in planner.tree_archive.get_children():
                if iid == job_id:
                    found_iid = iid
                    # Switch tab to archive
                    planner.queue_notebook.select(1)
                    break
                    
        if found_iid:
            if planner.queue_notebook.index(planner.queue_notebook.select()) == 0:
                planner.tree.selection_set(found_iid)
                planner.on_job_select(tk.Event()) # Simulate event
            else:
                planner.tree_archive.selection_set(found_iid)
                planner.on_job_select(tk.Event()) # Simulate event
                
        # Bind close event to refresh self
        def on_planner_close():
            self.refresh_tree()
            # Select the node again to refresh info panel
            self.tree.selection_set(f"job_{job_id}")
            self.on_node_select(None)
            planner.destroy()
            
        planner.protocol("WM_DELETE_WINDOW", on_planner_close)

    def on_tree_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        node_id = sel[0]
        if node_id.startswith("job_"):
            job_id = node_id[4:]
            self.open_job_in_planner(job_id)

    def on_drag_start(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and iid.startswith("job_"):
            self.drag_source_job_id = iid[4:]
            self.is_dragging = True
            self.tree.config(cursor="fleur")
        else:
            self.drag_source_job_id = None
            self.is_dragging = False

    def on_drag_motion(self, event):
        if not getattr(self, 'is_dragging', False) or not self.drag_source_job_id:
            return
        target_iid = self.tree.identify_row(event.y)
        if target_iid:
            self.tree.selection_set(target_iid)

    def on_drag_drop(self, event):
        if not getattr(self, 'is_dragging', False):
            return
            
        self.is_dragging = False
        self.tree.config(cursor="")
        
        job_id = self.drag_source_job_id
        self.drag_source_job_id = None
        
        target_iid = self.tree.identify_row(event.y)
        if not target_iid:
            self.tree.selection_set(f"job_{job_id}")
            self.on_node_select(None)
            return
            
        project_id = ""
        if target_iid == "unassigned":
            project_id = ""
        elif target_iid == "root":
            project_id = ""
        elif target_iid.startswith("job_"):
            parent_id = self.tree.parent(target_iid)
            if parent_id and parent_id not in ("root", "unassigned"):
                project_id = parent_id
            else:
                project_id = ""
        else:
            project_id = target_iid
            
        job = next((j for j in self.jobs if j["id"] == job_id), None)
        if job:
            if job.get("project_id") != project_id:
                job["project_id"] = project_id
                self.app.data_manager.save_jobs(self.jobs)
            self.refresh_tree()
            self.tree.selection_set(f"job_{job_id}")
            self.on_node_select(None)

    def show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
            
        self.tree.selection_set(iid)
        self.on_node_select(None)
        
        menu = tk.Menu(self, tearoff=0)
        
        if iid.startswith("job_"):
            job_id = iid[4:]
            menu.add_command(label="✏️ Im Planer öffnen", command=lambda: self.open_job_in_planner(job_id))
            
            # Submenu: Move to project
            move_menu = tk.Menu(menu, tearoff=0)
            move_menu.add_command(label="⏳ Unzugeordnete Druckaufträge", command=lambda: self.move_job_to_folder(job_id, ""))
            move_menu.add_separator()
            
            folders = [f for f in self.projects if f.get("type", "folder") == "folder"]
            folders_dict = {f["id"]: f for f in folders}
            
            def get_folder_path(folder_id):
                path_parts = []
                curr_id = folder_id
                visited = set()
                while curr_id and curr_id not in visited:
                    visited.add(curr_id)
                    f = folders_dict.get(curr_id)
                    if f:
                        path_parts.insert(0, f["name"])
                        curr_id = f.get("parent_id")
                    else:
                        break
                return " / ".join(path_parts)
                
            path_folders = []
            for f in folders:
                path = get_folder_path(f["id"])
                path_folders.append((path, f["id"]))
            path_folders.sort(key=lambda x: x[0].lower())
            
            for path, fid in path_folders:
                move_menu.add_command(label=f"📁 {path}", command=lambda f_id=fid: self.move_job_to_folder(job_id, f_id))
                
            menu.add_cascade(label="📂 Verschieben nach...", menu=move_menu)
            menu.add_separator()
            menu.add_command(label="💔 Aus Projekt entfernen", command=lambda: self.remove_job_from_project(job_id))
            
        elif iid != "root" and iid != "unassigned":
            menu.add_command(label="📁+ Neuer Unterordner", command=self.create_folder)
            menu.add_command(label="✏️ Ordner umbenennen", command=self.rename_folder)
            menu.add_command(label="🗑️ Ordner löschen", command=self.delete_folder)
        else:
            if iid == "root":
                menu.add_command(label="📁+ Neuer Ordner", command=self.create_folder)
            else:
                return
                
        menu.post(event.x_root, event.y_root)

    def move_job_to_folder(self, job_id, folder_id):
        job = next((j for j in self.jobs if j["id"] == job_id), None)
        if job:
            job["project_id"] = folder_id
            self.app.data_manager.save_jobs(self.jobs)
            self.refresh_tree()
            self.tree.selection_set(f"job_{job_id}")
            self.on_node_select(None)

    def on_close(self):
        try:
            self.app.settings["projects_dialog_geometry"] = self.geometry()
            self.app.data_manager.save_settings(self.app.settings)
        except:
            pass
        self.destroy()
