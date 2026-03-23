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
