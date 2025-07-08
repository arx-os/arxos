import pytest
import tempfile
import json
import os
from pathlib import Path
from services.schema_validation import SymbolSchemaValidator

@pytest.fixture(scope="module")
def validator():
    return SymbolSchemaValidator()

def valid_symbol():
    return {
        "id": "test_symbol_1",
        "name": "Test Symbol",
        "system": "electrical",
        "svg": {"content": "<svg></svg>"},
        "properties": {"voltage": "220V"},
        "connections": [
            {"id": "c1", "type": "input", "x": 0, "y": 0}
        ]
    }

def test_valid_symbol(validator):
    symbol = valid_symbol()
    valid, errors = validator.validate_symbol(symbol)
    assert valid
    assert errors == []

def test_invalid_id_pattern(validator):
    symbol = valid_symbol()
    symbol["id"] = "Invalid-ID!"
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("id" in e and "pattern" in e for e in errors)

def test_missing_required_field(validator):
    symbol = valid_symbol()
    del symbol["svg"]
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("svg" in e and "required property" in e for e in errors)

def test_invalid_system_enum(validator):
    symbol = valid_symbol()
    symbol["system"] = "not_a_system"
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("system" in e and "is not one of" in e for e in errors)

def test_svg_content_required(validator):
    symbol = valid_symbol()
    symbol["svg"] = {}
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("svg.content" in e and "required property" in e for e in errors)

def test_svg_content_empty(validator):
    symbol = valid_symbol()
    symbol["svg"]["content"] = ""
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("svg.content" in e and "minLength" in e for e in errors)

def test_properties_object(validator):
    symbol = valid_symbol()
    symbol["properties"] = "not_an_object"
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("properties" in e and "is not of type 'object'" in e for e in errors)

def test_connections_array(validator):
    symbol = valid_symbol()
    symbol["connections"] = [
        {"id": "c1", "type": "input", "x": 0, "y": 0},
        {"id": "c2", "type": "output", "x": 1, "y": 1}
    ]
    valid, errors = validator.validate_symbol(symbol)
    assert valid
    # Now test missing required field in connection
    symbol["connections"][0].pop("x")
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("connections.0.x" in e and "required property" in e for e in errors)

def test_connections_unique(validator):
    symbol = valid_symbol()
    symbol["connections"] = [
        {"id": "c1", "type": "input", "x": 0, "y": 0},
        {"id": "c1", "type": "output", "x": 1, "y": 1}
    ]
    valid, errors = validator.validate_symbol(symbol)
    # Should be valid as uniqueness is not enforced on id, but on array items
    assert valid

def test_additional_properties_not_allowed(validator):
    symbol = valid_symbol()
    symbol["extra_field"] = 123
    valid, errors = validator.validate_symbol(symbol)
    assert not valid
    assert any("additional properties" in e for e in errors)

def test_validate_symbols_batch(validator):
    symbols = [valid_symbol(), valid_symbol()]
    symbols[1]["id"] = "Invalid-ID!"
    results = validator.validate_symbols(symbols)
    assert results[0]["valid"]
    assert not results[1]["valid"]
    assert any("id" in e for e in results[1]["errors"])

def test_validate_symbol_from_file(validator):
    symbol = valid_symbol()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(symbol, f)
        fname = f.name
    try:
        valid, errors = validator.validate_symbol(fname)
        assert valid
    finally:
        os.remove(fname)

def test_validate_symbols_from_file(validator):
    symbols = [valid_symbol(), valid_symbol()]
    symbols[1]["id"] = "Invalid-ID!"
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(symbols, f)
        fname = f.name
    try:
        results = validator.validate_symbols(fname)
        assert results[0]["valid"]
        assert not results[1]["valid"]
    finally:
        os.remove(fname) 