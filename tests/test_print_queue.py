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
    dialog.ent_print_hours.delete(0, tk.END)
    dialog.ent_print_hours.insert(0, "2")
    dialog.ent_print_mins.delete(0, tk.END)
    dialog.ent_print_mins.insert(0, "0")
    
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
    hours_val = dialog.ent_hours.get()
    mins_val = dialog.ent_mins.get()
    assert hours_val == "2"
    assert mins_val == "0"
    
    spool_val = dialog.spool_entries[1].get()
    assert spool_val == "150"
    
    # Run process_deduction
    dialog.process_deduction()
    
    # Check that inventory was updated (weight_gross reduced by 150g)
    # Spool 1 old weight_gross = 1200. 1200 - 150 = 1050
    assert mock_app.inventory[0]['weight_gross'] == 1050
    assert job['status'] == "Erledigt ✅"
    
    dialog.destroy()

def test_deleted_printer_fallback(tk_root, mock_app):
    # Set a printer ID that does not exist in the printer list
    job = {
        "id": "abcde",
        "title": "Deleted Printer Job",
        "print_time": 2.0,
        "spools": "1",
        "spool_weights": {"1": 150.0},
        "printer_id": "non_existent_id", # Deleted printer
        "status": "Geplant"
    }
    
    mock_app.data_manager.load_jobs.return_value = [job]
    dialog = PrintQueueDialog(tk_root, mock_app)
    
    # Select the job (simulates on_job_select)
    dialog.tree.selection_set("abcde")
    event = MagicMock()
    event.widget = dialog.tree
    dialog.on_job_select(event)
    
    # Check that combobox falls back to 0 (Globaler Standard)
    assert dialog.combo_printer.current() == 0
    
    # Verify price is computed using global standard values
    # watts=150, kwh=0.30, wear=0.20
    # Strom = 2.0 * (150 / 1000.0) * 0.30 = 0.09
    # Wear = 2.0 * 0.20 = 0.40
    # Spool 1: 150g (Price/kg = 20) -> Mat = 3.00
    # Total cost = 3.00 + 0.09 + 0.40 = 3.49
    # VK with +10% = 3.49 * 1.1 = 3.839 -> 3.84
    txt = dialog.lbl_calc_price.cget("text")
    assert "3.49" in txt
    assert "3.84" in txt
    
    dialog.destroy()
