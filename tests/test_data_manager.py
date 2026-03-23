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
