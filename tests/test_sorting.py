import pytest
import re
from unittest.mock import MagicMock
from filament_gui import FilamentApp

def test_ams_sorting_fixed_regardless_of_sort_column():
    app = MagicMock(spec=FilamentApp)
    app.settings = {}
    
    # Spools in inventory:
    # AMS 1 Slot 1: Brand "Generic" (ID 20)
    # AMS 1 Slot 2: Brand "Bambu" (ID 10)
    # Shelf Slot 1: Brand "Z-Brand" (ID 30)
    # Shelf Slot 2: Brand "A-Brand" (ID 40)
    app.inventory = [
        {"id": 10, "type": "AMS 1", "loc_id": "2", "brand": "Bambu", "color": "Red"},
        {"id": 20, "type": "AMS 1", "loc_id": "1", "brand": "Generic", "color": "Green"},
        {"id": 30, "type": "Regal", "loc_id": "1-1", "brand": "Z-Brand", "color": "Blue"},
        {"id": 40, "type": "Regal", "loc_id": "1-2", "brand": "A-Brand", "color": "Yellow"},
    ]
    app.spools = []
    
    # Case A: Sort by brand (A-Z), reverse = False
    app.current_sort_col = "brand"
    app.current_sort_reverse = False
    
    FilamentApp._sort_inventory(app)
    
    # AMS VIP spools must still be sorted strictly by physical slot ascending:
    # 1. AMS 1 1 (ID 20)
    # 2. AMS 1 2 (ID 10)
    assert app.inventory[0]["id"] == 20
    assert app.inventory[1]["id"] == 10
    
    # Rest of the list (Regal) should be sorted by brand A-Z:
    # 3. Regal (A-Brand, ID 40)
    # 4. Regal (Z-Brand, ID 30)
    assert app.inventory[2]["id"] == 40
    assert app.inventory[3]["id"] == 30
    
    # Reset inventory for next case
    app.inventory = [
        {"id": 10, "type": "AMS 1", "loc_id": "2", "brand": "Bambu", "color": "Red"},
        {"id": 20, "type": "AMS 1", "loc_id": "1", "brand": "Generic", "color": "Green"},
        {"id": 30, "type": "Regal", "loc_id": "1-1", "brand": "Z-Brand", "color": "Blue"},
        {"id": 40, "type": "Regal", "loc_id": "1-2", "brand": "A-Brand", "color": "Yellow"},
    ]
    
    # Case B: Sort by brand reverse (Z-A), reverse = True
    app.current_sort_col = "brand"
    app.current_sort_reverse = True
    
    FilamentApp._sort_inventory(app)
    
    # AMS VIP spools must STILL be sorted strictly by physical slot ascending:
    # 1. AMS 1 1 (ID 20)
    # 2. AMS 1 2 (ID 10)
    assert app.inventory[0]["id"] == 20
    assert app.inventory[1]["id"] == 10
    
    # Rest of the list (Regal) should be sorted by brand Z-A:
    # 3. Regal (Z-Brand, ID 30)
    # 4. Regal (A-Brand, ID 40)
    assert app.inventory[2]["id"] == 30
    assert app.inventory[3]["id"] == 40

def test_shelf_visualizer_zoom(monkeypatch):
    from filament_gui import ShelfVisualizer
    import tkinter as tk
    from unittest.mock import patch
    
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tkinter/Tcl is not fully initialized or available in this environment")
    
    app = MagicMock()
    app.settings = {"shelf_zoom": "Mittel"}
    app.inventory = []
    app.spools = []
    
    with patch.object(ShelfVisualizer, 'redraw') as mock_redraw:
        vis = ShelfVisualizer(root, [], app.settings, [], app)
        
        # Test default value loaded
        assert vis.combo_zoom.get() == "Mittel"
        
        # Change selection and call on_zoom_change
        vis.combo_zoom.set("Klein")
        vis.on_zoom_change()
        
        # Settings should have updated
        assert app.settings["shelf_zoom"] == "Klein"
        # Redraw should have been triggered
        mock_redraw.assert_called()
        
        vis.destroy()
    root.destroy()
