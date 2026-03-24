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
