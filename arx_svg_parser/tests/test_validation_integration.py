"""
Test Validation Integration

This module tests the integration of comprehensive schema validation
across all symbol management services including SymbolManager, JSONSymbolLibrary,
and API endpoints.

Author: Arxos Development Team
Date: 2024
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from services.symbol_manager import SymbolManager
from services.json_symbol_library import JSONSymbolLibrary
from services.symbol_schema_validator import SymbolSchemaValidator
from routers.symbol_management import router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestValidationIntegration:
    """Test validation integration across all services."""
    
    @pytest.fixture
    def temp_library_path(self):
        """Create a temporary library path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create basic library structure
            symbols_dir = Path(temp_dir) / "symbols"
            symbols_dir.mkdir(parents=True, exist_ok=True)
            
            # Create system directories
            (symbols_dir / "mechanical").mkdir(exist_ok=True)
            (symbols_dir / "electrical").mkdir(exist_ok=True)
            
            # Create index.json
            index_data = {
                "symbols": [],
                "by_system": {
                    "mechanical": [],
                    "electrical": []
                },
                "total_count": 0
            }
            
            with open(Path(temp_dir) / "index.json", 'w') as f:
                json.dump(index_data, f)
            
            yield temp_dir
    
    @pytest.fixture
    def valid_symbol_data(self):
        """Valid symbol data for testing."""
        return {
            "id": "test_symbol_001",
            "name": "Test Symbol",
            "system": "mechanical",
            "svg": {
                "content": "<svg><circle cx='50' cy='50' r='25'/></svg>",
                "width": 100,
                "height": 100
            },
            "description": "A test symbol",
            "category": "test",
            "properties": {"test_prop": "value"},
            "connections": [],
            "tags": ["test", "symbol"],
            "metadata": {"created_by": "test"}
        }
    
    @pytest.fixture
    def invalid_symbol_data(self):
        """Invalid symbol data for testing."""
        return {
            "id": "test_symbol_002",
            "name": "",  # Invalid: empty name
            "system": "invalid_system",  # Invalid: not in enum
            "svg": {
                "content": "",  # Invalid: empty content
                "width": "invalid"  # Invalid: should be number
            }
        }
    
    def test_symbol_manager_validation_integration(self, temp_library_path, valid_symbol_data):
        """Test that SymbolManager uses comprehensive validation."""
        manager = SymbolManager(temp_library_path)
        
        # Test valid symbol creation
        created_symbol = manager.create_symbol(valid_symbol_data)
        assert created_symbol["id"] == valid_symbol_data["id"]
        assert created_symbol["name"] == valid_symbol_data["name"]
        
        # Test invalid symbol creation
        with pytest.raises(ValueError, match="Invalid symbol data provided"):
            manager.create_symbol(invalid_symbol_data)
    
    def test_symbol_manager_bulk_validation(self, temp_library_path, valid_symbol_data, invalid_symbol_data):
        """Test bulk operations with validation."""
        manager = SymbolManager(temp_library_path)
        
        # Test bulk create with mixed valid/invalid symbols
        symbols_to_create = [valid_symbol_data, invalid_symbol_data]
        created_symbols = manager.bulk_create_symbols(symbols_to_create)
        
        # Should only create the valid symbol
        assert len(created_symbols) == 1
        assert created_symbols[0]["id"] == valid_symbol_data["id"]
    
    def test_symbol_manager_validation_with_details(self, temp_library_path, valid_symbol_data, invalid_symbol_data):
        """Test detailed validation methods."""
        manager = SymbolManager(temp_library_path)
        
        # Test single symbol validation
        result = manager.validate_symbol_with_details(valid_symbol_data)
        assert result["is_valid"] is True
        assert result["errors"] == []
        
        result = manager.validate_symbol_with_details(invalid_symbol_data)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        
        # Test batch validation
        batch_result = manager.validate_batch_with_details([valid_symbol_data, invalid_symbol_data])
        assert batch_result["total_symbols"] == 2
        assert batch_result["valid_symbols"] == 1
        assert batch_result["invalid_symbols"] == 1
        assert len(batch_result["validation_details"]) == 2
    
    def test_json_symbol_library_validation_integration(self, temp_library_path, valid_symbol_data):
        """Test that JSONSymbolLibrary uses comprehensive validation."""
        library = JSONSymbolLibrary(temp_library_path)
        
        # Test validation method
        assert library.validate_symbol(valid_symbol_data) is True
        
        # Test with invalid data
        invalid_data = valid_symbol_data.copy()
        invalid_data["name"] = ""  # Invalid
        assert library.validate_symbol(invalid_data) is False
    
    def test_json_symbol_library_file_loading_validation(self, temp_library_path, valid_symbol_data):
        """Test that file loading includes validation."""
        library = JSONSymbolLibrary(temp_library_path)
        
        # Create a valid symbol file
        symbol_file = Path(temp_library_path) / "symbols" / "mechanical" / "test_symbol.json"
        with open(symbol_file, 'w') as f:
            json.dump(valid_symbol_data, f)
        
        # Test loading with validation
        loaded_symbols = library.load_all_symbols()
        assert len(loaded_symbols) == 1
        assert "test_symbol_001" in loaded_symbols
        
        # Create an invalid symbol file
        invalid_data = valid_symbol_data.copy()
        invalid_data["name"] = ""  # Invalid
        invalid_file = Path(temp_library_path) / "symbols" / "mechanical" / "invalid_symbol.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Test loading with validation (should skip invalid)
        loaded_symbols = library.load_all_symbols()
        assert len(loaded_symbols) == 1  # Only valid symbol loaded
        assert "test_symbol_001" in loaded_symbols
    
    def test_api_validation_integration(self, temp_library_path, valid_symbol_data):
        """Test API endpoint validation integration."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock authentication
        with patch('routers.symbol_management.get_current_user') as mock_user:
            mock_user.return_value = Mock(
                username="test_user",
                role="admin",
                permissions=["CREATE_SYMBOL", "READ_SYMBOL"]
            )
            
            # Test create symbol endpoint with validation
            response = client.post(
                "/api/v1/symbols",
                json=valid_symbol_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 201
            
            # Test with invalid data
            invalid_data = valid_symbol_data.copy()
            invalid_data["name"] = ""  # Invalid
            
            response = client.post(
                "/api/v1/symbols",
                json=invalid_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 422  # Validation error
    
    def test_api_validation_endpoints(self, temp_library_path, valid_symbol_data, invalid_symbol_data):
        """Test dedicated validation API endpoints."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock authentication
        with patch('routers.symbol_management.get_current_user') as mock_user:
            mock_user.return_value = Mock(
                username="test_user",
                role="admin",
                permissions=["READ_SYMBOL"]
            )
            
            # Test basic validation endpoint
            response = client.post(
                "/api/v1/symbols/validate",
                json=[valid_symbol_data, invalid_symbol_data],
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["summary"]["total_symbols"] == 2
            assert data["summary"]["valid_symbols"] == 1
            assert data["summary"]["invalid_symbols"] == 1
            
            # Test detailed validation endpoint
            response = client.post(
                "/api/v1/symbols/validate/detailed",
                json=[valid_symbol_data, invalid_symbol_data],
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "validation_summary" in data
            assert "schema_info" in data
            assert "validation_timestamp" in data
    
    def test_api_file_validation_endpoint(self, temp_library_path, valid_symbol_data):
        """Test file validation API endpoint."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock authentication
        with patch('routers.symbol_management.get_current_user') as mock_user:
            mock_user.return_value = Mock(
                username="test_user",
                role="admin",
                permissions=["READ_SYMBOL"]
            )
            
            # Create test file
            test_file_content = json.dumps([valid_symbol_data])
            
            # Test file validation
            response = client.post(
                "/api/v1/symbols/validate/file",
                files={"file": ("test_symbols.json", test_file_content, "application/json")},
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["file_info"]["filename"] == "test_symbols.json"
            assert data["validation_results"]["is_valid"] is True
            assert data["validation_results"]["total_symbols"] == 1
    
    def test_validation_error_handling(self, temp_library_path):
        """Test comprehensive error handling in validation."""
        manager = SymbolManager(temp_library_path)
        
        # Test with malformed data
        malformed_data = {
            "id": "test",
            "name": "Test",
            "system": "mechanical",
            "svg": "not_a_dict"  # Invalid: should be dict
        }
        
        result = manager.validate_symbol_with_details(malformed_data)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        
        # Test with missing required fields
        incomplete_data = {
            "id": "test",
            "name": "Test"
            # Missing system and svg
        }
        
        result = manager.validate_symbol_with_details(incomplete_data)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validation_performance(self, temp_library_path, valid_symbol_data):
        """Test validation performance with large batches."""
        manager = SymbolManager(temp_library_path)
        
        # Create large batch of valid symbols
        large_batch = []
        for i in range(100):
            symbol = valid_symbol_data.copy()
            symbol["id"] = f"test_symbol_{i:03d}"
            symbol["name"] = f"Test Symbol {i}"
            large_batch.append(symbol)
        
        # Test batch validation performance
        import time
        start_time = time.time()
        result = manager.validate_batch_with_details(large_batch)
        end_time = time.time()
        
        assert result["total_symbols"] == 100
        assert result["valid_symbols"] == 100
        assert result["invalid_symbols"] == 0
        
        # Should complete within reasonable time (less than 5 seconds)
        assert (end_time - start_time) < 5.0
    
    def test_validation_schema_info(self, temp_library_path):
        """Test schema information retrieval."""
        validator = SymbolSchemaValidator()
        
        schema_info = validator.get_schema_info()
        assert "schema_version" in schema_info
        assert "required_fields" in schema_info
        assert "optional_fields" in schema_info
        assert "validation_rules" in schema_info
        
        # Test that required fields are present
        required_fields = schema_info["required_fields"]
        assert "name" in required_fields
        assert "system" in required_fields
        assert "svg" in required_fields
    
    def test_validation_cross_service_consistency(self, temp_library_path, valid_symbol_data):
        """Test that validation is consistent across all services."""
        manager = SymbolManager(temp_library_path)
        library = JSONSymbolLibrary(temp_library_path)
        validator = SymbolSchemaValidator()
        
        # Test that all services return same validation result
        manager_result = manager.validate_symbol_with_details(valid_symbol_data)
        library_result = library.validate_symbol(valid_symbol_data)
        validator_result = validator.validate_symbol(valid_symbol_data)
        
        assert manager_result["is_valid"] == library_result
        assert manager_result["is_valid"] == validator_result[0]
        
        # Test with invalid data
        invalid_data = valid_symbol_data.copy()
        invalid_data["name"] = ""
        
        manager_result = manager.validate_symbol_with_details(invalid_data)
        library_result = library.validate_symbol(invalid_data)
        validator_result = validator.validate_symbol(invalid_data)
        
        assert manager_result["is_valid"] == library_result
        assert manager_result["is_valid"] == validator_result[0]


class TestValidationErrorHandling:
    """Test comprehensive error handling in validation integration."""
    
    def test_validation_exception_handling(self):
        """Test that validation exceptions are properly handled."""
        validator = SymbolSchemaValidator()
        
        # Test with None data
        result = validator.validate_symbol(None)
        assert result[0] is False
        assert len(result[1]) > 0
        
        # Test with non-dict data
        result = validator.validate_symbol("not_a_dict")
        assert result[0] is False
        assert len(result[1]) > 0
    
    def test_validation_error_formatting(self):
        """Test that validation errors are properly formatted."""
        validator = SymbolSchemaValidator()
        
        # Test with invalid data that produces multiple errors
        invalid_data = {
            "id": "test",
            "name": "",  # Invalid: empty
            "system": "invalid_system",  # Invalid: not in enum
            "svg": {
                "content": "",  # Invalid: empty
                "width": "not_a_number"  # Invalid: should be number
            }
        }
        
        is_valid, errors = validator.validate_symbol(invalid_data)
        assert is_valid is False
        assert len(errors) > 0
        
        # Check error format
        for error in errors:
            assert "field_path" in error
            assert "message" in error
            assert isinstance(error["field_path"], str)
            assert isinstance(error["message"], str)
    
    def test_validation_in_schema_validator_service(self):
        """Test validation methods in the schema validator service."""
        validator = SymbolSchemaValidator()
        
        # Test validate_symbols method
        symbols = [
            {"id": "test1", "name": "Test 1", "system": "mechanical", "svg": {"content": "<svg></svg>"}},
            {"id": "test2", "name": "", "system": "invalid", "svg": {"content": ""}}  # Invalid
        ]
        
        results = validator.validate_symbols(symbols)
        assert len(results) == 2
        assert results[0]["valid"] is True
        assert results[1]["valid"] is False
        
        # Test validate_file method
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(symbols, f)
            file_path = f.name
        
        try:
            is_valid, errors = validator.validate_file(file_path)
            assert is_valid is False  # Should be invalid due to second symbol
            assert len(errors) > 0
        finally:
            os.unlink(file_path)
    
    def test_validation_report_generation(self):
        """Test validation report generation."""
        validator = SymbolSchemaValidator()
        
        symbols = [
            {"id": "test1", "name": "Test 1", "system": "mechanical", "svg": {"content": "<svg></svg>"}},
            {"id": "test2", "name": "", "system": "invalid", "svg": {"content": ""}}  # Invalid
        ]
        
        report = validator.generate_validation_report(symbols)
        assert "summary" in report
        assert "details" in report
        assert report["summary"]["total_symbols"] == 2
        assert report["summary"]["valid_symbols"] == 1
        assert report["summary"]["invalid_symbols"] == 1
        assert len(report["details"]) == 2


if __name__ == "__main__":
    pytest.main([__file__]) 