import pytest
import os
import json
from core.utils import get_colors_from_text, load_json, save_json

def test_get_colors_from_text_hex():
    assert get_colors_from_text("#FF0000") == ["#FF0000"]
    assert get_colors_from_text("Red #FF0000") == ["#FF0000"]

def test_get_colors_from_text_names():
    assert get_colors_from_text("Rot") == ["#FF0000"]
    assert get_colors_from_text("Blue") == ["#0000FF"]
    assert get_colors_from_text("Red and Blue") == ["#FF0000", "#0000FF"]

def test_get_colors_from_text_rainbow():
    rainbow = ["#FF0000", "#FFA500", "#FFFF00", "#008000", "#0000FF", "#4B0082", "#EE82EE"]
    assert get_colors_from_text("Regenbogen") == rainbow
    assert get_colors_from_text("Rainbow") == rainbow

def test_load_json_exists(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "test.json"
    data = {"key": "value"}
    p.write_text(json.dumps(data))
    
    loaded = load_json(str(p), {})
    assert loaded == data

def test_load_json_not_exists():
    assert load_json("non_existent.json", {"default": "val"}) == {"default": "val"}

def test_save_json(tmp_path):
    p = tmp_path / "save_test.json"
    data = {"hello": "world"}
    save_json(str(p), data)
    
    assert p.exists()
    assert json.loads(p.read_text()) == data

def test_shelf_regex_compatibility():
    import re
    # The regex used in filament_gui.py
    regex = r'([^,|]+)\|\s*(\d+)\s*\|\s*(\d+)'
    
    # Test typical output from the new planner
    test_str = "Hauptregal|5|10"
    matches = re.findall(regex, test_str)
    assert len(matches) == 1
    assert matches[0] == ("Hauptregal", "5", "10")
    
    # Test multiple shelves
    multi_str = "Regal A|4|8, Regal B|2|2"
    matches = re.findall(regex, multi_str)
    assert len(matches) == 2
    assert matches[1][0].strip() == "Regal B"
