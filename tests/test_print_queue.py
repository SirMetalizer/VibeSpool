import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from core.print_queue import PrintQueueDialog, JobDeductionDialog

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
    app.settings = {
        "kwh_price": 0.30,
        "printer_watts": 150,
        "wear_per_hour": 0.20,
        "profit_margin": 10
    }
    app.inventory = [
        {"id": 1, "brand": "Bambu", "color": "Red (#FF0000)", "price": 20.00, "capacity": 1000.0, "type": "Regal", "weight_gross": 1200},
        {"id": 2, "brand": "Prusa", "color": "Blue", "price": 30.00, "capacity": 1000.0, "type": "Regal", "weight_gross": 1000}
    ]
    app.data_manager = MagicMock()
    app.data_manager.load_jobs.return_value = []
    return app

def test_recalculate_price(tk_root, mock_app):
    dialog = PrintQueueDialog(tk_root, mock_app)
    
    # Pre-fill print time
    dialog.ent_print_time.delete(0, tk.END)
    dialog.ent_print_time.insert(0, "2.0")
    
    # Add spool rows
    dialog.add_spool_row(1, 150.0) # Spool 1: 150g (Price/kg = 20) -> Mat = 3.00
    # Strom = 2.0 * (150 / 1000.0) * 0.30 = 0.09
    # Wear = 2.0 * 0.20 = 0.40
    # Total cost = 3.00 + 0.09 + 0.40 = 3.49
    # VK with +10% = 3.49 * 1.1 = 3.839 -> 3.84
    
    dialog.recalculate_price()
    
    # Verify price label
    txt = dialog.lbl_calc_price.cget("text")
    assert "3.49" in txt
    assert "3.84" in txt
    
    dialog.destroy()

def test_job_deduction_dialog(tk_root, mock_app):
    queue_dialog = MagicMock()
    queue_dialog.app = mock_app
    queue_dialog.jobs = []
    
    job = {
        "id": "12345",
        "title": "Test Job",
        "print_time": 2.0,
        "spool_weights": {"1": 150.0},
        "status": "Geplant"
    }
    
    matched_spools = [mock_app.inventory[0]]
    
    dialog = JobDeductionDialog(tk_root, queue_dialog, job, matched_spools)
    
    # Verify fields are prefilled
    time_val = dialog.ent_time.get()
    assert time_val == "2.0"
    
    spool_val = dialog.spool_entries[1].get()
    assert spool_val == "150"
    
    # Run process_deduction
    dialog.process_deduction()
    
    # Check that inventory was updated (weight_gross reduced by 150g)
    # Spool 1 old weight_gross = 1200. 1200 - 150 = 1050
    assert mock_app.inventory[0]['weight_gross'] == 1050
    assert job['status'] == "Erledigt ✅"
    
    dialog.destroy()
