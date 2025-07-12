#!/usr/bin/env python3
"""
Test script for symbol validation

This script tests the validate_symbols.py script with various scenarios.
"""

import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from validate_symbols import SymbolValidator


def create_test_schema():
    """Create a test JSON schema."""
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "system": {"type": "string"},
            "svg": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"}
                },
                "required": ["content"]
            }
        },
        "required": ["name", "system", "svg"]
    }


def create_test_symbol(valid=True):
    """Create a test symbol JSON."""
    if valid:
        return {
            "name": "Test HVAC Unit",
            "system": "mechanical",
            "svg": {
                "content": "<g id=\"test_hvac\">...</g>"
            }
        }
    else:
        return {
            "name": "Test HVAC Unit",
            # Missing required fields
        }


def test_valid_symbol():
    """Test validation of a valid symbol."""
    print("Testing valid symbol...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        schema_path = Path(temp_dir) / "schema.json"
        symbols_path = Path(temp_dir) / "symbols"
        symbols_path.mkdir()
        
        # Write schema
        with open(schema_path, 'w') as f:
            json.dump(create_test_schema(), f)
        
        # Write valid symbol
        symbol_path = symbols_path / "test_symbol.json"
        with open(symbol_path, 'w') as f:
            json.dump(create_test_symbol(valid=True), f)
        
        # Test validation
        validator = SymbolValidator(
            schema_path=str(schema_path),
            symbols_path=str(symbols_path),
            verbose=True
        )
        
        result = validator.validate_all_files()
        assert result, "Valid symbol should pass validation"
        print("✓ Valid symbol test passed")


def test_invalid_symbol():
    """Test validation of an invalid symbol."""
    print("Testing invalid symbol...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        schema_path = Path(temp_dir) / "schema.json"
        symbols_path = Path(temp_dir) / "symbols"
        symbols_path.mkdir()
        
        # Write schema
        with open(schema_path, 'w') as f:
            json.dump(create_test_schema(), f)
        
        # Write invalid symbol
        symbol_path = symbols_path / "test_symbol.json"
        with open(symbol_path, 'w') as f:
            json.dump(create_test_symbol(valid=False), f)
        
        # Test validation
        validator = SymbolValidator(
            schema_path=str(schema_path),
            symbols_path=str(symbols_path),
            verbose=True
        )
        
        result = validator.validate_all_files()
        assert not result, "Invalid symbol should fail validation"
        print("✓ Invalid symbol test passed")


def test_missing_schema():
    """Test behavior with missing schema file."""
    print("Testing missing schema...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        symbols_path = Path(temp_dir) / "symbols"
        symbols_path.mkdir()
        
        # Test with non-existent schema
        validator = SymbolValidator(
            schema_path="/non/existent/schema.json",
            symbols_path=str(symbols_path),
            verbose=True
        )
        
        result = validator.validate_all_files()
        assert not result, "Missing schema should fail validation"
        print("✓ Missing schema test passed")


def test_empty_symbols_directory():
    """Test behavior with empty symbols directory."""
    print("Testing empty symbols directory...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        schema_path = Path(temp_dir) / "schema.json"
        symbols_path = Path(temp_dir) / "symbols"
        symbols_path.mkdir()
        
        # Write schema
        with open(schema_path, 'w') as f:
            json.dump(create_test_schema(), f)
        
        # Test with empty directory
        validator = SymbolValidator(
            schema_path=str(schema_path),
            symbols_path=str(symbols_path),
            verbose=True
        )
        
        result = validator.validate_all_files()
        assert not result, "Empty directory should fail validation"
        print("✓ Empty directory test passed")


def test_cli_script():
    """Test the CLI script functionality."""
    print("Testing CLI script...")
    
    script_path = Path(__file__).parent / "validate_symbols.py"
    
    # Test help
    result = subprocess.run([
        sys.executable, str(script_path), "--help"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, "Help should work"
    assert "usage:" in result.stdout, "Help should show usage"
    print("✓ CLI help test passed")


def run_all_tests():
    """Run all tests."""
    print("🧪 Running symbol validation tests...")
    print("=" * 50)
    
    try:
        test_valid_symbol()
        test_invalid_symbol()
        test_missing_schema()
        test_empty_symbols_directory()
        test_cli_script()
        
        print("=" * 50)
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 