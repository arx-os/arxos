"""
Test suite for Arxos Pipeline Integration

Tests the integration between Go orchestration layer and Python bridge service.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the svgx_engine to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "svgx_engine"))

from svgx_engine.services.pipeline_integration import PipelineIntegrationService
from svgx_engine.services.symbol_manager import SymbolManager
from svgx_engine.services.behavior_engine import BehaviorEngine
from svgx_engine.services.validation_engine import ValidationEngine
from svgx_engine.utils.errors import PipelineError, ValidationError


class TestPipelineIntegration(unittest.TestCase):
    """Test cases for pipeline integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = PipelineIntegrationService()
        
        # Create test directories
        self.schemas_dir = Path(self.temp_dir) / "schemas"
        self.schemas_dir.mkdir()
        
        self.symbols_dir = Path(self.temp_dir) / "tools/symbols"
        self.symbols_dir.mkdir()
        
        self.behavior_dir = Path(self.temp_dir) / "svgx_engine" / "behavior"
        self.behavior_dir.mkdir(parents=True)
        
        # Patch the services to use test directories
        with patch.object(self.service.symbol_manager, 'symbol_library_path', self.symbols_dir):
            with patch.object(self.service.behavior_engine, 'behavior_path', self.behavior_dir):
                pass
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validate_schema_success(self):
        """Test successful schema validation."""
        # Create a test schema
        system = "test_system"
        schema_dir = self.schemas_dir / system
        schema_dir.mkdir()
        
        schema_file = schema_dir / "schema.json"
        schema_data = {
            "system": system,
            "objects": {
                "default": {
                    "properties": {},
                    "relationships": {},
                    "behavior_profile": "default"
                }
            }
        }
        
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f)
        
        # Test validation
        params = {"system": system}
        result = self.service.validate_schema(params)
        
        self.assertTrue(result["success"])
        self.assertIn("message", result)
        self.assertEqual(result["object_count"], 1)
    
    def test_validate_schema_missing_file(self):
        """Test schema validation with missing file."""
        params = {"system": "nonexistent_system"}
        result = self.service.validate_schema(params)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Schema file not found", result["error"])
    
    def test_validate_schema_invalid_json(self):
        """Test schema validation with invalid JSON."""
        system = "test_system"
        schema_dir = self.schemas_dir / system
        schema_dir.mkdir()
        
        schema_file = schema_dir / "schema.json"
        with open(schema_file, 'w') as f:
            f.write("invalid json content")
        
        params = {"system": system}
        result = self.service.validate_schema(params)
        
        self.assertFalse(result["success"])
        self.assertIn("Invalid JSON", result["error"])
    
    def test_validate_symbol_success(self):
        """Test successful symbol validation."""
        # Mock the symbol manager
        with patch.object(self.service.symbol_manager, 'validate_symbol') as mock_validate:
            mock_validate.return_value = {"valid": True, "details": "test"}
            
            params = {"symbol": "test_symbol"}
            result = self.service.validate_symbol(params)
            
            self.assertTrue(result["success"])
            self.assertIn("message", result)
            mock_validate.assert_called_once_with("test_symbol")
    
    def test_validate_symbol_failure(self):
        """Test symbol validation failure."""
        # Mock the symbol manager to raise an exception
        with patch.object(self.service.symbol_manager, 'validate_symbol') as mock_validate:
            mock_validate.side_effect = ValidationError("Symbol validation failed")
            
            params = {"symbol": "test_symbol"}
            result = self.service.validate_symbol(params)
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_validate_behavior_success(self):
        """Test successful behavior validation."""
        # Mock the behavior engine
        with patch.object(self.service.behavior_engine, 'validate_system_behavior') as mock_validate:
            mock_validate.return_value = {"valid": True, "details": "test"}
            
            params = {"system": "test_system"}
            result = self.service.validate_behavior(params)
            
            self.assertTrue(result["success"])
            self.assertIn("message", result)
            mock_validate.assert_called_once_with("test_system")
    
    def test_validate_behavior_failure(self):
        """Test behavior validation failure."""
        # Mock the behavior engine to raise an exception
        with patch.object(self.service.behavior_engine, 'validate_system_behavior') as mock_validate:
            mock_validate.side_effect = ValidationError("Behavior validation failed")
            
            params = {"system": "test_system"}
            result = self.service.validate_behavior(params)
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_add_symbols_success(self):
        """Test successful symbol creation."""
        # Mock the symbol manager
        with patch.object(self.service.symbol_manager, 'create_symbol') as mock_create:
            mock_create.return_value = Path("test_symbol.svgx")
            
            params = {"system": "test_system", "symbols": ["test_symbol"]}
            result = self.service.add_symbols(params)
            
            self.assertTrue(result["success"])
            self.assertEqual(len(result["created_symbols"]), 1)
            self.assertEqual(len(result["errors"]), 0)
    
    def test_add_symbols_failure(self):
        """Test symbol creation failure."""
        # Mock the symbol manager to raise an exception
        with patch.object(self.service.symbol_manager, 'create_symbol') as mock_create:
            mock_create.side_effect = Exception("Symbol creation failed")
            
            params = {"system": "test_system", "symbols": ["test_symbol"]}
            result = self.service.add_symbols(params)
            
            self.assertFalse(result["success"])
            self.assertEqual(len(result["created_symbols"]), 0)
            self.assertEqual(len(result["errors"]), 1)
    
    def test_implement_behavior_success(self):
        """Test successful behavior implementation."""
        # Mock the behavior engine
        with patch.object(self.service.behavior_engine, 'create_system_behavior') as mock_create:
            mock_create.return_value = Path("test_behavior.py")
            
            params = {"system": "test_system"}
            result = self.service.implement_behavior(params)
            
            self.assertTrue(result["success"])
            self.assertIn("message", result)
            mock_create.assert_called_once_with("test_system")
    
    def test_implement_behavior_failure(self):
        """Test behavior implementation failure."""
        # Mock the behavior engine to raise an exception
        with patch.object(self.service.behavior_engine, 'create_system_behavior') as mock_create:
            mock_create.side_effect = Exception("Behavior creation failed")
            
            params = {"system": "test_system"}
            result = self.service.implement_behavior(params)
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_run_compliance_check_success(self):
        """Test successful compliance check."""
        # Mock the validation engine
        with patch.object(self.service.validation_engine, 'run_compliance_check') as mock_compliance:
            mock_compliance.return_value = {
                "compliance_status": "compliant",
                "checks_passed": 5,
                "checks_failed": 0
            }
            
            params = {"system": "test_system"}
            result = self.service.run_compliance_check(params)
            
            self.assertTrue(result["success"])
            self.assertIn("message", result)
            mock_compliance.assert_called_once_with("test_system")
    
    def test_run_compliance_check_failure(self):
        """Test compliance check failure."""
        # Mock the validation engine to raise an exception
        with patch.object(self.service.validation_engine, 'run_compliance_check') as mock_compliance:
            mock_compliance.side_effect = Exception("Compliance check failed")
            
            params = {"system": "test_system"}
            result = self.service.run_compliance_check(params)
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_unknown_operation(self):
        """Test handling of unknown operations."""
        params = {"system": "test_system"}
        result = self.service.handle_operation("unknown_operation", params)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Unknown operation", result["error"])
    
    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        # Test missing system parameter
        params = {}
        result = self.service.validate_schema(params)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("System parameter is required", result["error"])
    
    def test_error_handling(self):
        """Test general error handling."""
        # Test with an operation that raises an unexpected exception
        with patch.object(self.service, 'validate_schema') as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")
            
            params = {"system": "test_system"}
            result = self.service.handle_operation("validate-schema", params)
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Unexpected error")


class TestSymbolManager(unittest.TestCase):
    """Test cases for symbol manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.symbol_manager = SymbolManager(str(Path(self.temp_dir) / "symbols"))
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_create_symbol(self):
        """Test symbol creation."""
        system = "test_system"
        symbol_name = "test_symbol"
        
        # Mock the symbol manager methods
        with patch.object(self.symbol_manager, '_create_basic_svgx') as mock_svgx:
            with patch.object(self.symbol_manager, '_create_basic_metadata') as mock_metadata:
                with patch.object(self.symbol_manager, '_update_symbol_index') as mock_index:
                    mock_svgx.return_value = "<svg>test</svg>"
                    mock_metadata.return_value = {"id": "test"}
                    
                    # Create the symbol
                    symbol_path = self.symbol_manager.create_symbol(system, symbol_name)
                    
                    self.assertIsInstance(symbol_path, Path)
                    mock_svgx.assert_called_once_with(system, symbol_name)
                    mock_metadata.assert_called_once_with(system, symbol_name)
                    mock_index.assert_called_once()


class TestBehaviorEngine(unittest.TestCase):
    """Test cases for behavior engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.behavior_engine = BehaviorEngine(str(Path(self.temp_dir) / "behavior"))
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_create_system_behavior(self):
        """Test behavior profile creation."""
        system = "test_system"
        
        # Mock the behavior creation method
        with patch.object(self.behavior_engine, '_create_basic_behavior') as mock_create:
            mock_create.return_value = "test behavior content"
            
            # Create the behavior profile
            behavior_path = self.behavior_engine.create_system_behavior(system)
            
            self.assertIsInstance(behavior_path, Path)
            mock_create.assert_called_once_with(system)


if __name__ == "__main__":
    unittest.main() 