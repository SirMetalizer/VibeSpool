import pytest
from core.logic import calculate_net_weight, parse_ver

def test_calculate_net_weight_basic():
    spools = [{"id": 1, "weight": 200}]
    # Gross 1000 - Spool 200 = 800
    assert calculate_net_weight(1000, 1, spools) == 800

def test_calculate_net_weight_float_string():
    spools = [{"id": 1, "weight": 200}]
    # Gross "1000,5" -> 1000.5 - 200 = 800.5 -> int 800
    assert calculate_net_weight("1000,5", 1, spools) == 800

def test_calculate_net_weight_no_spool():
    spools = []
    # If no spool is found, it subtracts 0, so 1000 - 0 = 1000
    assert calculate_net_weight(1000, 1, spools) == 1000

def test_calculate_net_weight_negative():
    spools = [{"id": 1, "weight": 250}]
    # Gross 200 - Spool 250 = -50 -> max(0, -50) = 0
    assert calculate_net_weight(200, 1, spools) == 0

def test_calculate_net_weight_invalid_input():
    spools = [{"id": 1, "weight": 200}]
    assert calculate_net_weight("abc", 1, spools) == 0

def test_parse_ver():
    assert parse_ver("1.8") == [1, 8]
    assert parse_ver("v1.8.1") == [1, 8, 1]
    assert parse_ver("2.0-beta") == [2, 0]
    assert parse_ver("") == []

def test_version_comparison():
    assert parse_ver("1.10") > parse_ver("1.9")
    assert parse_ver("v2.0") > parse_ver("1.8.5")
    assert parse_ver("1.8.1") > parse_ver("1.8")
