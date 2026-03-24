import pytest
from core.logic import parse_shelves_string, serialize_shelves

def test_parse_shelves_string_basic():
    input_str = "REGAL|4|8"
    expected = [{"name": "REGAL", "rows": 4, "cols": 8}]
    assert parse_shelves_string(input_str) == expected

def test_parse_shelves_string_multiple():
    input_str = "Regal A|5|10, Regal B|2|2"
    expected = [
        {"name": "Regal A", "rows": 5, "cols": 10},
        {"name": "Regal B", "rows": 2, "cols": 2}
    ]
    assert parse_shelves_string(input_str) == expected

def test_parse_shelves_string_invalid():
    input_str = "Invalid, REGAL|abc|8, |4|8"
    # Regal|abc|8 is invalid, |4|8 results in name "REGAL"
    expected = [{"name": "REGAL", "rows": 4, "cols": 8}]
    assert parse_shelves_string(input_str) == expected

def test_serialize_shelves():
    input_list = [
        {"name": "Regal A", "rows": 5, "cols": 10},
        {"name": "Regal B", "rows": 2, "cols": 2}
    ]
    expected = "Regal A|5|10, Regal B|2|2"
    assert serialize_shelves(input_list) == expected

def test_roundtrip():
    original = "Shelf 1|10|20, Shelf 2|5|5"
    parsed = parse_shelves_string(original)
    serialized = serialize_shelves(parsed)
    assert serialized == original
