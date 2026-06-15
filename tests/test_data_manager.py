import pytest
import os
from unittest.mock import MagicMock, patch
from core.data_manager import DataManager

@pytest.fixture
def mock_settings():
    return {"custom_db_path": "", "shelves": "REGAL|4|8"}

def test_data_manager_init(mock_settings):
    with patch("os.path.expanduser", return_value="/home/user"):
        with patch("os.path.exists", return_value=True):
            dm = DataManager(mock_settings)
            # Should have set up paths based on home/documents
            assert "VibeSpool" in dm.base_dir

def test_get_filtered_inventory_search():
    dm = DataManager({})
    inventory = [
        {"id": 1, "brand": "Bambu", "color": "Red", "material": "PLA"},
        {"id": 2, "brand": "Prusa", "color": "Blue", "material": "PETG"},
    ]
    
    # Search for Bambu
    results = dm.get_filtered_inventory(inventory, "Bambu", {})
    assert len(results) == 1
    assert results[0]["brand"] == "Bambu"

    # Search for Red
    results = dm.get_filtered_inventory(inventory, "Red", {})
    assert len(results) == 1
    assert results[0]["color"] == "Red"

def test_get_filtered_inventory_filters():
    dm = DataManager({})
    inventory = [
        {"id": 1, "brand": "Bambu", "color": "Red", "material": "PLA", "type": "Regal"},
        {"id": 2, "brand": "Prusa", "color": "Blue", "material": "PETG", "type": "Regal"},
        {"id": 3, "brand": "Generic", "color": "Red", "material": "ABS", "type": "Trockner"},
    ]
    
    # Filter by material PLA
    results = dm.get_filtered_inventory(inventory, "", {"material": "PLA"})
    assert len(results) == 1
    assert results[0]["material"] == "PLA"

    # Filter by color Red
    results = dm.get_filtered_inventory(inventory, "", {"color": "Red"})
    assert len(results) == 2

    # Filter by location
    results = dm.get_filtered_inventory(inventory, "", {"location": "Trockner"})
    assert len(results) == 1
    assert results[0]["type"] == "Trockner"

def test_get_filtered_inventory_ams_logic():
    dm = DataManager({})
    inventory = [
        {"id": 1, "type": "AMS 1"},
        {"id": 2, "type": "AMS 2"},
        {"id": 3, "type": "Regal"},
    ]
    
    # Filter by "AMS" (should show all AMS)
    results = dm.get_filtered_inventory(inventory, "", {"location": "AMS"})
    assert len(results) == 2
    
    # Filter by specific AMS
    results = dm.get_filtered_inventory(inventory, "", {"location": "AMS 1"})
    assert len(results) == 1
    assert results[0]["type"] == "AMS 1"

def test_data_manager_printer_migration():
    dm = DataManager({})
    
    old_settings = {
        "bambu_ip": "192.168.1.100",
        "bambu_access": "123456",
        "bambu_serial": "00M123",
        "use_bambu": True,
        "num_ams": 2,
        "custom_locs": "Filamenttrockner, P1S 2 Extern"
    }
    
    with patch("core.data_manager.load_json") as mock_load:
        mock_load.side_effect = [old_settings.copy(), [], []]
        dm.save_settings = MagicMock()
        
        inventory, settings, spools = dm.load_all(old_settings)
        
        assert "printers" in settings
        assert len(settings["printers"]) == 1
        
        printer = settings["printers"][0]
        assert printer["name"] == "Drucker 1"
        assert printer["ip"] == "192.168.1.100"
        assert printer["access_code"] == "123456"
        assert printer["serial"] == "00M123"
        assert printer["ams_ids"] == [1, 2]
        assert printer["external_loc"] == "P1S 2 Extern"
        assert printer["use_mqtt"] is True

def test_data_manager_printer_costs():
    dm = DataManager({})
    settings = {
        "printers": [
            {
                "id": "abc",
                "name": "P1S 1",
                "type": "bambu",
                "ip": "192.168.1.10",
                "access_code": "code",
                "serial": "SN123",
                "ams_ids": [1],
                "external_loc": "P1S 1 Extern",
                "use_mqtt": True,
                "printer_watts": 250,
                "wear_per_hour": 0.45
            }
        ]
    }
    
    with patch("core.data_manager.load_json") as mock_load:
        mock_load.side_effect = [settings.copy(), [], []]
        inventory, loaded_settings, spools = dm.load_all(settings)
        
        assert len(loaded_settings["printers"]) == 1
        printer = loaded_settings["printers"][0]
        assert printer["printer_watts"] == 250
        assert printer["wear_per_hour"] == 0.45
