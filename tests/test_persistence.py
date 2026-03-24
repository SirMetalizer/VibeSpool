import pytest
import os
import json
from core.data_manager import DataManager
from core.logic import parse_shelves_string, serialize_shelves

def test_full_settings_persistence_logic(tmp_path):
    # 1. Setup DataManager with a temporary directory
    settings_file = tmp_path / "settings.json"
    default_settings = {"shelves": "OLD|1|1", "theme": "dark"}
    
    # Mock DataManager to use our tmp file
    class MockDataManager(DataManager):
        def __init__(self, path):
            self.settings_file = str(path)
            self.base_dir = str(os.path.dirname(path))
            self.data_file = os.path.join(self.base_dir, "inventory.json")
            self.spools_file = os.path.join(self.base_dir, "spools.json")

    dm = MockDataManager(settings_file)
    
    # 2. Simulate UI changes (What the Shelf Planner does)
    new_shelves_list = [
        {"name": "Regal A", "rows": 5, "cols": 10},
        {"name": "Regal B", "rows": 2, "cols": 4}
    ]
    serialized_str = serialize_shelves(new_shelves_list)
    assert serialized_str == "Regal A|5|10, Regal B|2|4"
    
    # 3. Simulate SettingsDialog gathering all data
    current_settings = default_settings.copy()
    current_settings.update({
        "shelves": serialized_str,
        "logistics_order": True
    })
    
    # 4. Simulate FilamentApp saving via DataManager
    dm.save_settings(current_settings)
    
    # 5. Verify Disk Content
    assert settings_file.exists()
    with open(settings_file, "r") as f:
        saved_data = json.load(f)
    
    assert saved_data["shelves"] == "Regal A|5|10, Regal B|2|4"
    assert saved_data["logistics_order"] is True
    assert saved_data["theme"] == "dark" # Should be preserved
