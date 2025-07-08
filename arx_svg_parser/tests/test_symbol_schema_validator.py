"""
Unit tests for Symbol Schema Validator Service.

This module tests the comprehensive validation functionality including:
- Individual symbol validation
- File validation
- Library validation
- Error reporting and formatting
- Batch validation
- Report generation

Author: Arxos Development Team
Date: 2024
"""

import pytest
import json
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.symbol_schema_validator import SymbolSchemaValidator

class TestSymbolSchemaValidator:
    """Test cases for SymbolSchemaValidator class."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a mock schema for testing
        self.mock_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "name", "system", "svg"],
            "properties": {
                "id": {
                    "type": "string",
                    "pattern": "^[a-z0-9_]+$"
                },
                "name": {
                    "type": "string"
                },
                "system": {
                    "type": "string",
                    "enum": ["electrical", "mechanical", "plumbing"]
                },
                "svg": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string",
                            "minLength": 1
                        }
                    }
                }
            }
        }
        
        # Create mock schema file
        self.schema_file = os.path.join(self.temp_dir, "test_schema.json")
        with open(self.schema_file, 'w') as f:
            json.dump(self.mock_schema, f)
        
        # Initialize validator with mock schema
        self.validator = SymbolSchemaValidator(self.schema_file)
    
    def teardown_method(self):
        """Cleanup test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_default_schema(self):
        """Test initialization with default schema path."""
        # This test requires the actual schema file to exist
        try:
            validator = SymbolSchemaValidator()
            assert validator.schema is not None
            assert validator.validator is not None
        except FileNotFoundError:
            # Skip if schema file doesn't exist
            pytest.skip("Default schema file not found")
    
    def test_init_with_custom_schema(self):
        """Test initialization with custom schema path."""
        validator = SymbolSchemaValidator(self.schema_file)
        assert validator.schema == self.mock_schema
        assert validator.validator is not None
    
    def test_init_schema_file_not_found(self):
        """Test initialization with non-existent schema file."""
        with pytest.raises(FileNotFoundError):
            SymbolSchemaValidator("nonexistent_schema.json")
    
    def test_init_invalid_json_schema(self):
        """Test initialization with invalid JSON schema."""
        invalid_schema_file = os.path.join(self.temp_dir, "invalid_schema.json")
        with open(invalid_schema_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            SymbolSchemaValidator(invalid_schema_file)
    
    def test_validate_symbol_valid(self):
        """Test validation of a valid symbol."""
        valid_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical",
            "svg": {"content": "<svg></svg>"}
        }
        
        is_valid, errors = self.validator.validate_symbol(valid_symbol)
        assert is_valid
        assert errors == []
    
    def test_validate_symbol_invalid_id_pattern(self):
        """Test validation with invalid ID pattern."""
        invalid_symbol = {
            "id": "Invalid-ID!",
            "name": "Test Symbol",
            "system": "electrical",
            "svg": {"content": "<svg></svg>"}
        }
        
        is_valid, errors = self.validator.validate_symbol(invalid_symbol)
        assert not is_valid
        assert len(errors) > 0
        assert any("id" in error["field_path"] for error in errors)
    
    def test_validate_symbol_missing_required_field(self):
        """Test validation with missing required field."""
        invalid_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical"
            # Missing 'svg' field
        }
        
        is_valid, errors = self.validator.validate_symbol(invalid_symbol)
        assert not is_valid
        assert len(errors) > 0
        assert any("svg" in error["field_path"] for error in errors)
    
    def test_validate_symbol_invalid_system_enum(self):
        """Test validation with invalid system enum."""
        invalid_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "invalid_system",
            "svg": {"content": "<svg></svg>"}
        }
        
        is_valid, errors = self.validator.validate_symbol(invalid_symbol)
        assert not is_valid
        assert len(errors) > 0
        assert any("system" in error["field_path"] for error in errors)
    
    def test_validate_symbol_empty_svg_content(self):
        """Test validation with empty SVG content."""
        invalid_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical",
            "svg": {"content": ""}
        }
        
        is_valid, errors = self.validator.validate_symbol(invalid_symbol)
        assert not is_valid
        assert len(errors) > 0
        assert any("svg.content" in error["field_path"] for error in errors)
    
    def test_validate_symbol_file_single_valid(self):
        """Test validation of a file containing a single valid symbol."""
        valid_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical",
            "svg": {"content": "<svg></svg>"}
        }
        
        symbol_file = os.path.join(self.temp_dir, "valid_symbol.json")
        with open(symbol_file, 'w') as f:
            json.dump(valid_symbol, f)
        
        result = self.validator.validate_symbol_file(symbol_file)
        assert result["valid"]
        assert result["statistics"]["total_symbols"] == 1
        assert result["statistics"]["valid_symbols"] == 1
        assert result["statistics"]["invalid_symbols"] == 0
    
    def test_validate_symbol_file_multiple_symbols(self):
        """Test validation of a file containing multiple symbols."""
        symbols = [
            {
                "id": "symbol1",
                "name": "Symbol 1",
                "system": "electrical",
                "svg": {"content": "<svg></svg>"}
            },
            {
                "id": "symbol2",
                "name": "Symbol 2",
                "system": "mechanical",
                "svg": {"content": "<svg></svg>"}
            }
        ]
        
        symbols_file = os.path.join(self.temp_dir, "symbols.json")
        with open(symbols_file, 'w') as f:
            json.dump(symbols, f)
        
        result = self.validator.validate_symbol_file(symbols_file)
        assert result["valid"]
        assert result["statistics"]["total_symbols"] == 2
        assert result["statistics"]["valid_symbols"] == 2
        assert result["statistics"]["invalid_symbols"] == 0
    
    def test_validate_symbol_file_mixed_validity(self):
        """Test validation of a file with mixed valid/invalid symbols."""
        symbols = [
            {
                "id": "valid_symbol",
                "name": "Valid Symbol",
                "system": "electrical",
                "svg": {"content": "<svg></svg>"}
            },
            {
                "id": "Invalid-ID!",
                "name": "Invalid Symbol",
                "system": "electrical",
                "svg": {"content": "<svg></svg>"}
            }
        ]
        
        symbols_file = os.path.join(self.temp_dir, "mixed_symbols.json")
        with open(symbols_file, 'w') as f:
            json.dump(symbols, f)
        
        result = self.validator.validate_symbol_file(symbols_file)
        assert not result["valid"]
        assert result["statistics"]["total_symbols"] == 2
        assert result["statistics"]["valid_symbols"] == 1
        assert result["statistics"]["invalid_symbols"] == 1
    
    def test_validate_symbol_file_not_found(self):
        """Test validation of non-existent file."""
        result = self.validator.validate_symbol_file("nonexistent.json")
        assert not result["valid"]
        assert "File not found" in result["errors"][0]["message"]
    
    def test_validate_symbol_file_invalid_json(self):
        """Test validation of file with invalid JSON."""
        invalid_json_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json }")
        
        result = self.validator.validate_symbol_file(invalid_json_file)
        assert not result["valid"]
        assert "Invalid JSON" in result["errors"][0]["message"]
    
    def test_validate_symbol_file_wrong_data_type(self):
        """Test validation of file with wrong data type."""
        wrong_type_file = os.path.join(self.temp_dir, "wrong_type.json")
        with open(wrong_type_file, 'w') as f:
            json.dump("not an object or array", f)
        
        result = self.validator.validate_symbol_file(wrong_type_file)
        assert not result["valid"]
        assert "must contain a symbol object or array" in result["errors"][0]["message"]
    
    def test_validate_library(self):
        """Test validation of an entire library."""
        # Create test library structure
        library_dir = os.path.join(self.temp_dir, "test_library")
        os.makedirs(library_dir)
        
        # Create valid symbol file
        valid_symbol = {
            "id": "valid_symbol",
            "name": "Valid Symbol",
            "system": "electrical",
            "svg": {"content": "<svg></svg>"}
        }
        valid_file = os.path.join(library_dir, "valid.json")
        with open(valid_file, 'w') as f:
            json.dump(valid_symbol, f)
        
        # Create invalid symbol file
        invalid_symbol = {
            "id": "Invalid-ID!",
            "name": "Invalid Symbol",
            "system": "electrical",
            "svg": {"content": "<svg></svg>"}
        }
        invalid_file = os.path.join(library_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            json.dump(invalid_symbol, f)
        
        # Create non-JSON file (should be ignored)
        non_json_file = os.path.join(library_dir, "readme.txt")
        with open(non_json_file, 'w') as f:
            f.write("This is not JSON")
        
        result = self.validator.validate_library(library_dir)
        assert not result["valid"]  # Should be invalid due to invalid symbol
        assert result["statistics"]["total_files"] == 2  # Only JSON files
        assert result["statistics"]["total_symbols"] == 2
        assert result["statistics"]["valid_symbols"] == 1
        assert result["statistics"]["invalid_symbols"] == 1
        assert result["statistics"]["valid_files"] == 1
        assert result["statistics"]["invalid_files"] == 1
    
    def test_validate_library_not_found(self):
        """Test validation of non-existent library."""
        result = self.validator.validate_library("nonexistent_library")
        assert not result["valid"]
        assert "Library path not found" in result["errors"][0]["message"]
    
    def test_validate_symbols_batch(self):
        """Test batch validation of symbols."""
        symbols = [
            {
                "id": "symbol1",
                "name": "Symbol 1",
                "system": "electrical",
                "svg": {"content": "<svg></svg>"}
            },
            {
                "id": "Invalid-ID!",
                "name": "Invalid Symbol",
                "system": "electrical",
                "svg": {"content": "<svg></svg>"}
            }
        ]
        
        result = self.validator.validate_symbols_batch(symbols)
        assert not result["valid"]
        assert result["statistics"]["total_symbols"] == 2
        assert result["statistics"]["valid_symbols"] == 1
        assert result["statistics"]["invalid_symbols"] == 1
        assert len(result["results"]) == 2
    
    def test_get_validation_summary(self):
        """Test generation of validation summary."""
        validation_result = {
            "valid": False,
            "statistics": {
                "total_symbols": 5,
                "valid_symbols": 3,
                "invalid_symbols": 2
            }
        }
        
        summary = self.validator.get_validation_summary(validation_result)
        assert "Validation Summary" in summary
        assert "Total Symbols: 5" in summary
        assert "Valid Symbols: 3" in summary
        assert "Invalid Symbols: 2" in summary
        assert "❌ Invalid" in summary
    
    def test_get_validation_summary_library(self):
        """Test generation of library validation summary."""
        validation_result = {
            "valid": True,
            "statistics": {
                "total_files": 10,
                "valid_files": 10,
                "invalid_files": 0,
                "total_symbols": 50,
                "valid_symbols": 50,
                "invalid_symbols": 0
            }
        }
        
        summary = self.validator.get_validation_summary(validation_result)
        assert "Library Validation Summary" in summary
        assert "Total Files: 10" in summary
        assert "Valid Files: 10" in summary
        assert "✅ Valid" in summary
    
    def test_export_validation_report(self):
        """Test export of validation report."""
        validation_result = {
            "valid": False,
            "statistics": {
                "total_symbols": 2,
                "valid_symbols": 1,
                "invalid_symbols": 1
            },
            "results": [
                {
                    "index": 0,
                    "symbol_id": "valid_symbol",
                    "valid": True,
                    "errors": []
                },
                {
                    "index": 1,
                    "symbol_id": "invalid_symbol",
                    "valid": False,
                    "errors": [{"message": "Invalid ID pattern"}]
                }
            ]
        }
        
        report_file = os.path.join(self.temp_dir, "validation_report.json")
        self.validator.export_validation_report(validation_result, report_file)
        
        assert os.path.exists(report_file)
        
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        assert "validation_report" in report
        assert "results" in report
        assert report["results"]["valid"] == False
    
    def test_get_schema_info(self):
        """Test retrieval of schema information."""
        schema_info = self.validator.get_schema_info()
        
        assert "schema_path" in schema_info
        assert "schema_version" in schema_info
        assert "title" in schema_info
        assert "required_fields" in schema_info
        assert "properties" in schema_info
        assert "id" in schema_info["required_fields"]
        assert "name" in schema_info["required_fields"]
        assert "system" in schema_info["required_fields"]
        assert "svg" in schema_info["required_fields"]
    
    def test_format_validation_error(self):
        """Test formatting of validation errors."""
        # Create a mock ValidationError
        mock_error = Mock()
        mock_error.path = ["id"]
        mock_error.message = "Does not match pattern '^[a-z0-9_]+$'"
        mock_error.schema_path = ["properties", "id", "pattern"]
        mock_error.validator = "pattern"
        mock_error.validator_value = "^[a-z0-9_]+$"
        
        formatted_error = self.validator._format_validation_error(mock_error)
        
        assert formatted_error["field_path"] == "id"
        assert formatted_error["error_type"] == "invalid_pattern"
        assert "pattern" in formatted_error["message"]
        assert formatted_error["validator"] == "pattern"
        assert formatted_error["validator_value"] == "^[a-z0-9_]+$"
    
    def test_validate_symbol_exception_handling(self):
        """Test handling of exceptions during validation."""
        # Mock the validator to raise an exception
        with patch.object(self.validator, 'validator') as mock_validator:
            mock_validator.iter_errors.side_effect = Exception("Test exception")
            
            is_valid, errors = self.validator.validate_symbol({})
            
            assert not is_valid
            assert len(errors) == 1
            assert errors[0]["error_type"] == "validation_exception"
            assert "Test exception" in errors[0]["message"]

if __name__ == "__main__":
    pytest.main([__file__]) 