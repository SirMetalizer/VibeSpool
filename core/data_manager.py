import os
import json
from core.utils import load_json, save_json

class DataManager:
    def __init__(self, default_settings):
        # 1. Prefer local directory if settings.json already exists there
        local_dir = os.getcwd()
        if os.path.exists(os.path.join(local_dir, "settings.json")) or os.path.exists(os.path.join(local_dir, "inventory.json")):
            self.base_dir = local_dir
        else:
            # 2. Otherwise use Documents folder
            user_home = os.path.expanduser("~")
            self.base_dir = os.path.join(user_home, "VibeSpool_Daten")
            
            possible_docs = [
                os.path.join(user_home, "OneDrive", "Documents"),
                os.path.join(user_home, "OneDrive", "Dokumente"),
                os.path.join(user_home, "Documents"),
                os.path.join(user_home, "Dokumente")
            ]

            for path in possible_docs:
                if os.path.exists(path):
                    self.base_dir = os.path.join(path, "VibeSpool")
                    break
            
            if not os.path.exists(self.base_dir):
                try: os.makedirs(self.base_dir)
                except: pass

        self.settings_file = os.path.join(self.base_dir, "settings.json")
        
        # Load settings to check for custom db path
        _temp_set = load_json(self.settings_file, default_settings)
        custom_db_path = _temp_set.get("custom_db_path", "")
        
        if custom_db_path and os.path.exists(custom_db_path):
            self.data_file = os.path.join(custom_db_path, "inventory.json")
            self.spools_file = os.path.join(custom_db_path, "spools.json")
            self.jobs_file = os.path.join(custom_db_path, "print_jobs.json") # NEU
        else:
            self.data_file = os.path.join(self.base_dir, "inventory.json")
            self.spools_file = os.path.join(self.base_dir, "spools.json")
            self.jobs_file = os.path.join(self.base_dir, "print_jobs.json") # NEU

    def load_all(self, default_settings):
        settings = load_json(self.settings_file, default_settings)
        spools = load_json(self.spools_file, [])
        inventory = load_json(self.data_file, [])
        return inventory, settings, spools

    def save_inventory(self, inventory):
        save_json(self.data_file, inventory)

    def save_settings(self, settings):
        save_json(self.settings_file, settings)

    def save_spools(self, spools):
        save_json(self.spools_file, spools)

    def get_filtered_inventory(self, inventory, search_str, filters):
        s = search_str.lower()
        filter_mat = filters.get("material", "Alle Materialien")
        filter_color = filters.get("color", "Alle Farben")
        filter_loc = filters.get("location", "Alle Orte")
        
        result = []
        for i in inventory:
            if filter_mat != "Alle Materialien" and i.get("material") != filter_mat:
                continue
            if filter_color != "Alle Farben" and i.get("color") != filter_color:
                continue
            
            t = i.get("type", "")
            if filter_loc != "Alle Orte":
                if filter_loc.startswith("AMS") and t.startswith("AMS"):
                    if filter_loc != t and filter_loc != "AMS":
                        continue
                elif t != filter_loc:
                    continue
            
            try:
                id_val = str(i.get('id', ''))
                brand = i.get('brand', '')
                color = i.get('color', '')
                material = i.get('material', '')
                if s and s not in f"{id_val} {brand} {color} {material}".lower():
                    continue
            except:
                pass
            
            result.append(i)
        return result
    
    def load_jobs(self):
        return load_json(self.jobs_file, [])

    def save_jobs(self, jobs):
        from core.utils import save_json
        save_json(self.jobs_file, jobs)
