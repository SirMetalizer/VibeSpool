import pytest
import tkinter as tk
from unittest.mock import MagicMock
from core.statistics import StatisticsDialog

@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass

@pytest.fixture
def mock_app():
    app = MagicMock()
    app.spools = []
    app.settings = {
        "kwh_price": 0.30,
        "printer_watts": 150,
        "wear_per_hour": 0.20,
        "profit_margin": 10
    }
    app.inventory = [
        {
            "id": 1,
            "brand": "Bambu",
            "material": "PLA",
            "color": "Rot (#FF0000)",
            "price": 20.0,
            "capacity": 1000.0,
            "type": "Regal",
            "weight_gross": 1200,
            "empty_weight": 200,
            "history": [
                {"date": "2026-06-10 12:00:00", "action": "Druck 1", "change": "-50.0g", "cost": "1.00 €", "sell_price": "1.10 €"},
                {"date": "2026-06-09 10:00:00", "action": "Druck 2", "change": "-100.0g", "cost": "2.00 €", "sell_price": "2.20 €"}
            ]
        },
        {
            "id": 2,
            "brand": "Prusa",
            "material": "PETG",
            "color": "Blau",
            "price": 30.0,
            "capacity": 1000.0,
            "type": "Regal",
            "weight_gross": 1000,
            "empty_weight": 200,
            "history": [
                {"date": "2026-06-10 15:00:00", "action": "Druck 3", "change": "-40.0g", "cost": "1.20 €", "sell_price": "1.32 €"}
            ]
        },
        {
            "id": 3,
            "brand": "Bambu",
            "material": "PLA",
            "color": "Rot (#FF0000)",
            "price": 20.0,
            "capacity": 1000.0,
            "type": "VERBRAUCHT",
            "weight_gross": 200,
            "empty_weight": 200,
            "history": []
        }
    ]
    app.data_manager = MagicMock()
    return app

def test_statistics_dialog_filtering(tk_root, mock_app):
    dialog = StatisticsDialog(tk_root, mock_app.inventory, mock_app)

    # By default, filters should be "Alle"
    assert dialog.filter_brand.get() == "Alle"
    assert dialog.filter_material.get() == "Alle"
    assert dialog.filter_color.get() == "Alle"

    # Total active spools in initial state (excludes ID 3 because type is VERBRAUCHT)
    # Spool 1 net = 1200 - 200 = 1000g
    # Spool 2 net = 1000 - 200 = 800g
    # Total active spools = 2
    # Check tree/table entries or variables
    # We can inspect dialog's internal calculation of total_spools
    # Let's mock a method to inspect variables or run build_ui
    
    # Filter by Brand = Bambu
    dialog.filter_brand.set("Bambu")
    dialog.build_ui()
    
    # Now only Spool 1 is active matching "Bambu" (Spool 3 is VERBRAUCHT)
    # Let's inspect the calculated total_spools by asserting values from the UI labels or from tree widgets.
    # Total costs label text should be costs of Druck 1 + Druck 2 = 1.00 + 2.00 = 3.00 €
    txt_total = dialog.lbl_total.cget("text")
    assert "3.00" in txt_total

    # Filter by Brand = Prusa
    dialog.filter_brand.set("Prusa")
    dialog.build_ui()
    txt_total = dialog.lbl_total.cget("text")
    assert "1.20" in txt_total

    # Reset filters
    dialog.filter_brand.set("Alle")
    dialog.build_ui()
    txt_total = dialog.lbl_total.cget("text")
    assert "4.20" in txt_total # 1.00 + 2.00 + 1.20

    dialog.destroy()
