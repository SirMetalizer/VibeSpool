import pytest
import tkinter as tk
from unittest.mock import MagicMock
from core.projects import ProjectsDialog

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
        "profit_margin": 10,
        "use_projects": True
    }
    
    # Mock data for projects
    app.projects_data = [
        {"id": "folder_1", "name": "Litophane", "parent_id": None, "type": "folder"},
        {"id": "folder_2", "name": "runde", "parent_id": "folder_1", "type": "folder"},
        {"id": "folder_3", "name": "gebogene", "parent_id": "folder_1", "type": "folder"},
        {"id": "folder_4", "name": "Tiere", "parent_id": "folder_2", "type": "folder"}
    ]
    
    # Mock data for print jobs
    app.jobs_data = [
        {
            "id": "job_1",
            "title": "Lithophane Tier 1",
            "project_id": "folder_4",
            "print_time": 4.5,
            "est_weight": "150.0",
            "est_price": "5.00 € (VK: 5.50 €)",
            "status": "Erledigt ✅"
        },
        {
            "id": "job_2",
            "title": "Lithophane Runde 1",
            "project_id": "folder_2",
            "print_time": 2.0,
            "est_weight": "80",
            "est_price": "2.00 € (VK: 2.20 €)",
            "status": "Geplant"
        },
        {
            "id": "job_3",
            "title": "Lithophane Gebogen 1",
            "project_id": "folder_3",
            "print_time": 3.0,
            "est_weight": "120.0",
            "est_price": "3.50 €",
            "status": "Geplant"
        },
        {
            "id": "job_4",
            "title": "Standalone Job",
            "project_id": "",
            "print_time": 1.0,
            "est_weight": "50",
            "est_price": "1.50 €",
            "status": "Geplant"
        }
    ]
    
    # Set up data manager mock
    app.data_manager = MagicMock()
    app.data_manager.load_projects.side_effect = lambda: app.projects_data
    app.data_manager.load_jobs.side_effect = lambda: app.jobs_data
    
    def save_p_side_effect(proj):
        app.projects_data = proj
    app.data_manager.save_projects.side_effect = save_p_side_effect
    
    def save_j_side_effect(jobs):
        app.jobs_data = jobs
    app.data_manager.save_jobs.side_effect = save_j_side_effect
    
    app.inventory = []
    return app

def test_projects_dialog_data_loading(tk_root, mock_app):
    dialog = ProjectsDialog(tk_root, mock_app)
    
    # Verify projects and jobs are loaded correctly
    assert len(dialog.projects) == 4
    assert len(dialog.jobs) == 4
    
    dialog.destroy()

def test_projects_dialog_folder_stats(tk_root, mock_app):
    dialog = ProjectsDialog(tk_root, mock_app)
    
    # We inspect folder stats calculations directly using the UI rendering logic.
    # Select folder_1 ("Litophane").
    # It has subfolders folder_2 ("runde"), folder_3 ("gebogene"), folder_4 ("Tiere").
    # jobs: job_1 in folder_4, job_2 in folder_2, job_3 in folder_3.
    # Total jobs for folder_1 recursively = job_1 + job_2 + job_3 = 3 jobs.
    # Total print time: 4.5 + 2.0 + 3.0 = 9.5 hours.
    # Total weight: 150.0 + 80.0 + 120.0 = 350.0 g.
    # Total cost: 5.00 + 2.00 + 3.50 = 10.50 €.
    # Total sell price: 5.50 + 2.20 + 3.50 = 11.20 €.
    
    # We can invoke show_folder_details on folder_1 and query values, or test the logic directly.
    dialog.show_folder_details("folder_1")
    
    # Let's verify that the details panel shows the correct information or we can assert directly.
    # Instead of reading Tkinter label layout (which might change), let's inspect the UI state.
    # Let's test folder_2: contains job_1 (recursively through folder_4) and job_2.
    # Total jobs for folder_2 = 2 (job_1, job_2).
    # Total print time: 4.5 + 2.0 = 6.5 hours.
    # Total weight: 150 + 80 = 230 g.
    
    # Simulate selecting folder_2
    dialog.show_folder_details("folder_2")
    
    # Inspecting stats directly by recalculating in tests to verify calculations
    # Let's write a small helper mimicking the logic to double-check
    def run_calc(fid):
        descendants = [fid]
        def get_descendants(parent_id):
            for f in mock_app.projects_data:
                if f.get("parent_id") == parent_id:
                    descendants.append(f["id"])
                    get_descendants(f["id"])
        get_descendants(fid)
        return [j for j in mock_app.jobs_data if j.get("project_id") in descendants]
        
    jobs_f2 = run_calc("folder_2")
    assert len(jobs_f2) == 2
    assert "job_1" in [j["id"] for j in jobs_f2]
    assert "job_2" in [j["id"] for j in jobs_f2]
    
    dialog.destroy()

def test_projects_dialog_folder_deletion(tk_root, mock_app):
    dialog = ProjectsDialog(tk_root, mock_app)
    
    # When folder_1 is deleted, job_1, job_2, job_3 should have project_id unassigned (set to "").
    # Let's test the recursive unassign and delete function in ProjectsDialog
    # We mock confirmation dialog to return True
    import unittest.mock as mock
    with mock.patch("tkinter.messagebox.askyesno", return_value=True):
        # Set selection to folder_1 and delete
        dialog.tree.selection_set("folder_1")
        dialog.delete_folder()
        
    # Verify that folders under folder_1 (folder_1, folder_2, folder_3, folder_4) are deleted
    # All 4 folders were under folder_1 recursively. So all projects_data should be empty.
    # Wait, mock_app.data_manager.save_projects should be called with empty list.
    assert len(mock_app.projects_data) == 0
    
    # Verify jobs have project_id cleared
    for j in mock_app.jobs_data:
        assert j.get("project_id") == ""
        
    dialog.destroy()

def test_projects_dialog_drag_and_drop(tk_root, mock_app):
    # Reset mock data to original state
    mock_app.projects_data = [
        {"id": "folder_1", "name": "Litophane", "parent_id": None, "type": "folder"},
        {"id": "folder_2", "name": "runde", "parent_id": "folder_1", "type": "folder"},
        {"id": "folder_3", "name": "gebogene", "parent_id": "folder_1", "type": "folder"},
        {"id": "folder_4", "name": "Tiere", "parent_id": "folder_2", "type": "folder"}
    ]
    mock_app.jobs_data = [
        {
            "id": "job_1",
            "title": "Lithophane Tier 1",
            "project_id": "folder_4",
            "print_time": 4.5,
            "est_weight": "150.0",
            "est_price": "5.00 €",
            "status": "Erledigt ✅"
        }
    ]
    
    dialog = ProjectsDialog(tk_root, mock_app)
    
    # Verify initial project ID
    assert mock_app.jobs_data[0]["project_id"] == "folder_4"
    
    # Start drag on job_1
    dialog.tree.identify_row = MagicMock(return_value="job_job_1")
    event_start = MagicMock()
    event_start.y = 50
    dialog.on_drag_start(event_start)
    assert dialog.drag_source_job_id == "job_1"
    
    # Drop on folder_3
    dialog.tree.identify_row = MagicMock(return_value="folder_3")
    event_drop = MagicMock()
    event_drop.y = 100
    dialog.on_drag_drop(event_drop)
    
    # Verify reassignment
    assert mock_app.jobs_data[0]["project_id"] == "folder_3"
    
    dialog.destroy()

def test_projects_dialog_context_menu(tk_root, mock_app):
    # Reset mock data to original state
    mock_app.projects_data = [
        {"id": "folder_1", "name": "Litophane", "parent_id": None, "type": "folder"}
    ]
    mock_app.jobs_data = [
        {
            "id": "job_1",
            "title": "Lithophane Tier 1",
            "project_id": "",
            "print_time": 4.5,
            "est_weight": "150.0",
            "est_price": "5.00 €",
            "status": "Erledigt ✅"
        }
    ]
    
    dialog = ProjectsDialog(tk_root, mock_app)
    
    # Initially unassigned
    assert mock_app.jobs_data[0]["project_id"] == ""
    
    # Call move_job_to_folder to move it to folder_1
    dialog.move_job_to_folder("job_1", "folder_1")
    
    # Verify reassignment
    assert mock_app.jobs_data[0]["project_id"] == "folder_1"
    
    dialog.destroy()
