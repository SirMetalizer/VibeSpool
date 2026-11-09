import pytest
import json
from unittest.mock import patch, MagicMock
from core.printer_sync import fetch_last_print_usage, fetch_recent_jobs

def test_fetch_recent_jobs_success():
    mock_response_data = {
        "result": {
            "jobs": [
                {"filename": "Benchy.gcode", "filament_used": 15.2, "status": "completed"},
                {"filename": "Cube.gcode", "filament_used": 5.0, "status": "completed"}
            ]
        }
    }
    with patch("urllib.request.urlopen") as mock_url_open:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_url_open.return_value = mock_response
        
        jobs = fetch_recent_jobs("http://192.168.1.10")
        assert len(jobs) == 2
        assert jobs[0]["filename"] == "Benchy.gcode"
        assert jobs[1]["filament_used"] == 5.0

def test_fetch_last_print_usage_success():
    # Mock data that Moonraker would return
    mock_response_data = {
        "result": {
            "jobs": [
                {
                    "filament_used": 42.5,
                    "status": "completed"
                }
            ]
        }
    }
    
    # We mock urllib.request.urlopen
    with patch("urllib.request.urlopen") as mock_url_open:
        mock_response = MagicMock()
        mock_response.read.return_value = bytes(str(mock_response_data).replace("'", '"'), "utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_url_open.return_value = mock_response
        
        usage = fetch_last_print_usage("http://192.168.1.10")
        assert usage == 42.5

def test_fetch_last_print_usage_empty():
    mock_response_data = {"result": {"jobs": []}}
    with patch("urllib.request.urlopen") as mock_url_open:
        mock_response = MagicMock()
        mock_response.read.return_value = bytes(str(mock_response_data).replace("'", '"'), "utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_url_open.return_value = mock_response
        
        usage = fetch_last_print_usage("http://192.168.1.10")
        assert usage is None


def test_cloud_dryer_external_spool_resolution():
    from filament_gui import FilamentApp

    dummy = MagicMock(spec=FilamentApp)
    dummy.settings = {
        "custom_locs": "Filamenttrockner",
        "printers": [
            {
                "id": "p1",
                "name": "P1S mit AMS",
                "serial": "01S00A111",
                "ams_ids": [1],
                "external_loc": ""
            },
            {
                "id": "p2",
                "name": "A1 mit Trockner",
                "serial": "03000B222",
                "ams_ids": [],
                "external_loc": "Filamenttrockner"
            }
        ],
        "cloud_device_map": {}
    }
    dummy.inventory = [
        {"id": 1, "brand": "Bambu", "material": "PLA", "color": "Weiß", "type": "AMS 1", "loc_id": "1", "weight_gross": 800},
        {"id": 2, "brand": "eSUN", "material": "PETG", "color": "Schwarz", "type": "Filamenttrockner", "loc_id": "-", "weight_gross": 650}
    ]
    dummy.data_manager = MagicMock()
    dummy.data_manager.base_dir = ""

    # 1. Job vom 2. Drucker (mit Seriennummer, ohne AMS) -> muss auf Filamenttrockner zeigen, auch wenn Cloud ams=0 meldet!
    job_p2 = {"id": "100", "name": "Halter", "weight": 25.0, "deviceId": "03000B222", "mapping": [{"ams": 0, "weight": 25.0}]}
    printer, ams_ids, ext_loc, force_ext, src_key, label = FilamentApp._resolve_cloud_job_source(dummy, job_p2)
    assert printer["id"] == "p2"
    assert force_ext is True
    assert ext_loc == "Filamenttrockner"

    best_spool, matched_loc = FilamentApp._find_best_external_spool(dummy, ext_loc, mapping_entry={"ams": 0, "filamentType": "PETG"})
    assert best_spool is not None
    assert best_spool["id"] == 2
    assert matched_loc == "Filamenttrockner"

    # 2. Job von einem 2. Drucker, dessen Seriennummer noch gar nicht eingetragen wurde (während P1S AMS 1 besitzt)
    job_unknown_p2 = {"id": "101", "name": "Clip", "weight": 10.0, "deviceId": "03999Z999", "mapping": [{"ams": 0, "weight": 10.0}]}
    printer2, ams_ids2, ext_loc2, force_ext2, src_key2, label2 = FilamentApp._resolve_cloud_job_source(dummy, job_unknown_p2)
    assert force_ext2 is True
    assert ext_loc2 == "Filamenttrockner"

