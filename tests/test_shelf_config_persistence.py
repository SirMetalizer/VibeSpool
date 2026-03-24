import pytest
import os
import json
from core.data_manager import DataManager
from core.logic import parse_shelves_string, serialize_shelves

def test_shelf_configuration_toggle(tmp_path):
    # 1. Setup DataManager in a temporary directory
    settings_file = tmp_path / "settings.json"
    
    # We create a subclass to override only the file path for the test
    class TestDataManager(DataManager):
        def __init__(self, s_file):
            self.settings_file = str(s_file)
            self.base_dir = str(os.path.dirname(s_file))
            # Other files don't matter for this test
            self.data_file = os.path.join(self.base_dir, "inventory.json")
            self.spools_file = os.path.join(self.base_dir, "spools.json")

    dm = TestDataManager(settings_file)
    
    # Initial settings (similar to app defaults)
    current_settings = {"shelves": "REGAL|4|8", "theme": "dark"}
    dm.save_settings(current_settings)
    
    # --- STEP 1: Change from 4|8 to 3|12 ---
    print("\n[TEST] Changing config to 3|12...")
    new_shelves_list = [{"name": "REGAL", "rows": 3, "cols": 12}]
    current_settings["shelves"] = serialize_shelves(new_shelves_list)
    dm.save_settings(current_settings)
    
    # Verify on Disk
    with open(settings_file, "r") as f:
        disk_data = json.load(f)
    assert disk_data["shelves"] == "REGAL|3|12"
    print("[OK] Config 3|12 saved correctly.")

    # --- STEP 2: Change back to 4|8 ---
    print("[TEST] Changing config back to 4|8...")
    revert_shelves_list = [{"name": "REGAL", "rows": 4, "cols": 8}]
    current_settings["shelves"] = serialize_shelves(revert_shelves_list)
    dm.save_settings(current_settings)
    
    # Verify on Disk again
    with open(settings_file, "r") as f:
        disk_data_reverted = json.load(f)
    assert disk_data_reverted["shelves"] == "REGAL|4|8"
    print("[OK] Config 4|8 restored correctly.")

    # --- STEP 3: Multi-Shelf Test ---
    print("[TEST] Testing multiple shelves...")
    multi_shelves = [
        {"name": "Regal A", "rows": 5, "cols": 10},
        {"name": "Regal B", "rows": 2, "cols": 2}
    ]
    current_settings["shelves"] = serialize_shelves(multi_shelves)
    dm.save_settings(current_settings)
    
    with open(settings_file, "r") as f:
        disk_data_multi = json.load(f)
    assert disk_data_multi["shelves"] == "Regal A|5|10, Regal B|2|2"
    print("[OK] Multi-Shelf config saved correctly.")
