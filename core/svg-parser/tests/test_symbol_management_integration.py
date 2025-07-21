"""
Integration tests for Symbol Management System.

Tests the complete integration between:
- SymbolManager CRUD operations
- JSONSymbolLibrary symbol loading
- API endpoints and authentication
- CLI tool functionality
- Bulk import/export operations
- Validation integration
- Error handling and edge cases

Author: Arxos Development Team
Date: 2024
"""

import unittest
import tempfile
import json
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, Any, List
import csv
# Remove all YAML imports and logic
# Only allow JSON for symbol management tests
# Update docstrings and comments to reference JSON only

# Add the parent directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import with error handling for missing modules
try:
    from core.svg_parser.services.symbol_manager import SymbolManager
    from core.svg_parser.services.json_symbol_library import JSONSymbolLibrary
    from core.svg_parser.services.symbol_schema_validator import SymbolSchemaValidator
    _services_available = True
except ImportError as e:
    print(f"Warning: Services not available: {e}")
    _services_available = False

try:
    from core.svg_parser.cmd.symbol_manager_cli import SymbolManagerCLI
    _cli_available = True
except ImportError as e:
    print(f"Warning: CLI not available: {e}")
    _cli_available = False

try:
    from core.svg_parser.routers.symbol_management import router, symbol_manager, schema_validator
    _api_available = True
except ImportError as e:
    print(f"Warning: API not available: {e}")
    _api_available = False

try:
    from core.svg_parser.utils.auth import create_user, login_user, UserRole, Permission
    _auth_available = True
except ImportError as e:
    print(f"Warning: Auth not available: {e}")
    _auth_available = False


class TestSymbolManagementIntegration(unittest.TestCase):
    """Integration tests for the complete symbol management system."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not _services_available:
            self.skipTest("Services not available")
        
        # Create temporary test environment
        self.test_dir = tempfile.mkdtemp()
        self.test_library_path = Path(self.test_dir) / "test-symbol-library"
        self.test_library_path.mkdir()
        
        # Create test symbol library structure
        self._create_test_library_structure()
        
        # Initialize components
        self.symbol_manager = SymbolManager(str(self.test_library_path))
        self.symbol_library = JSONSymbolLibrary(str(self.test_library_path))
        self.schema_validator = SymbolSchemaValidator()
        
        if _cli_available:
            self.cli = SymbolManagerCLI(str(self.test_library_path))
        else:
            self.cli = None
        
        # Sample test symbols
        self.test_symbols = {
            "hvac_unit": {
                "id": "hvac_unit",
                "name": "HVAC Unit",
                "system": "mechanical",
                "category": "hvac",
                "description": "Heating, ventilation, and air conditioning unit",
                "tags": ["hvac", "air_handler", "mechanical"],
                "svg": {
                    "content": '<svg viewBox="0 0 100 100"><rect x="10" y="10" width="80" height="80"/></svg>'
                },
                "properties": {
                    "type": "hvac_unit",
                    "capacity": "5000 BTU",
                    "efficiency": "high"
                },
                "connections": [
                    {
                        "id": "inlet",
                        "type": "input",
                        "x": 10,
                        "y": 50,
                        "label": "Air Inlet"
                    },
                    {
                        "id": "outlet",
                        "type": "output",
                        "x": 90,
                        "y": 50,
                        "label": "Air Outlet"
                    }
                ],
                "metadata": {"created_by": "test"},
                "version": "1.0"
            },
            "electrical_outlet": {
                "id": "electrical_outlet",
                "name": "Electrical Outlet",
                "system": "electrical",
                "category": "electrical",
                "description": "Standard electrical outlet",
                "tags": ["electrical", "outlet", "power"],
                "svg": {
                    "content": '<svg viewBox="0 0 50 50"><circle cx="25" cy="25" r="20"/></svg>'
                },
                "properties": {
                    "type": "outlet",
                    "voltage": "120V",
                    "amperage": "15A"
                },
                "connections": [
                    {
                        "id": "power",
                        "type": "input",
                        "x": 25,
                        "y": 5,
                        "label": "Power Input"
                    }
                ],
                "metadata": {"created_by": "test"},
                "version": "1.0"
            }
        }
        
        # Create test users for API testing
        self.test_users = {
            "admin": {
                "username": "admin",
                "email": "admin@test.com",
                "password": "admin123",
                "role": "ADMIN" if _auth_available else None
            },
            "user": {
                "username": "user",
                "email": "user@test.com",
                "password": "user123",
                "role": "USER" if _auth_available else None
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_library_structure(self):
        """Create test symbol library structure."""
        # Create symbols directory
        symbols_dir = self.test_library_path / "symbols"
        symbols_dir.mkdir(exist_ok=True)
        
        # Create system directories
        for system in ["mechanical", "electrical", "plumbing"]:
            system_dir = symbols_dir / system
            system_dir.mkdir(exist_ok=True)
        
        # Create index.json
        index_data = {
            "version": "1.0",
            "total_symbols": 0,
            "by_system": {
                "mechanical": [],
                "electrical": [],
                "plumbing": []
            },
            "systems": ["mechanical", "electrical", "plumbing"]
        }
        
        index_file = self.test_library_path / "index.json"
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
    
    # Task 5.2.2: Test complete CRUD operations
    def test_crud_operations_integration(self):
        """Test complete CRUD operations integration."""
        # Test Create
        symbol_data = self.test_symbols["hvac_unit"].copy()
        # Keep the ID for validation, but let manager generate a new one if needed
        symbol_data["id"] = "test_hvac_unit"
        
        created_symbol = self.symbol_manager.create_symbol(symbol_data)
        self.assertIsNotNone(created_symbol)
        self.assertIn("id", created_symbol)
        self.assertEqual(created_symbol["name"], "HVAC Unit")
        
        symbol_id = created_symbol["id"]
        
        # Test Read
        retrieved_symbol = self.symbol_manager.get_symbol(symbol_id)
        self.assertIsNotNone(retrieved_symbol)
        self.assertEqual(retrieved_symbol["name"], "HVAC Unit")
        
        # Test Update
        updates = {
            "name": "Updated HVAC Unit",
            "description": "Updated description"
        }
        
        updated_symbol = self.symbol_manager.update_symbol(symbol_id, updates)
        self.assertIsNotNone(updated_symbol)
        self.assertEqual(updated_symbol["name"], "Updated HVAC Unit")
        self.assertIn("updated_at", updated_symbol)
        
        # Test Delete
        deleted = self.symbol_manager.delete_symbol(symbol_id)
        self.assertTrue(deleted)
        
        # Verify deletion
        retrieved_symbol = self.symbol_manager.get_symbol(symbol_id)
        self.assertIsNone(retrieved_symbol)
    
    def test_bulk_crud_operations(self):
        """Test bulk CRUD operations."""
        # Test Bulk Create
        symbols_data = [
            self.test_symbols["hvac_unit"].copy(),
            self.test_symbols["electrical_outlet"].copy()
        ]
        
        # Ensure symbols have valid IDs for validation
        symbols_data[0]["id"] = "bulk_test_hvac"
        symbols_data[1]["id"] = "bulk_test_electrical"
        
        created_symbols = self.symbol_manager.bulk_create_symbols(symbols_data)
        self.assertEqual(len(created_symbols), 2)
        
        # Test Bulk Update
        symbol_ids = [symbol["id"] for symbol in created_symbols]
        updates = [
            {"id": symbol_ids[0], "name": "Updated HVAC Unit"},
            {"id": symbol_ids[1], "name": "Updated Electrical Outlet"}
        ]
        
        updated_symbols = self.symbol_manager.bulk_update_symbols(updates)
        self.assertEqual(len(updated_symbols), 2)
        
        # Test Bulk Delete
        deleted_results = self.symbol_manager.bulk_delete_symbols(symbol_ids)
        self.assertEqual(len(deleted_results), 2)
        self.assertTrue(all(deleted_results.values()))
    
    # Task 5.2.3: Test bulk import/export functionality
    def test_bulk_import_export_integration(self):
        """Test bulk import/export functionality."""
        # Create test symbols for export
        symbols_data = [
            self.test_symbols["hvac_unit"].copy(),
            self.test_symbols["electrical_outlet"].copy()
        ]
        
        # Ensure symbols have valid IDs
        symbols_data[0]["id"] = "export_test_hvac"
        symbols_data[1]["id"] = "export_test_electrical"
        
        # Create symbols
        created_symbols = self.symbol_manager.bulk_create_symbols(symbols_data)
        self.assertEqual(len(created_symbols), 2)
        
        # Test JSON Export
        export_data = {
            "symbols": created_symbols,
            "export_info": {
                "format": "json",
                "exported_at": "2024-01-01T00:00:00Z",
                "total_symbols": len(created_symbols)
            }
        }
        
        # Test JSON Import
        import_symbols = export_data["symbols"]
        for symbol in import_symbols:
            # Generate new IDs for re-import
            symbol["id"] = f"import_{symbol['id']}"
        
        # Clear existing symbols
        symbol_ids = [symbol["id"] for symbol in created_symbols]
        self.symbol_manager.bulk_delete_symbols(symbol_ids)
        
        # Re-import
        recreated_symbols = self.symbol_manager.bulk_create_symbols(import_symbols)
        self.assertEqual(len(recreated_symbols), 2)
    
    def test_csv_import_export(self):
        """Test CSV import/export functionality."""
        # Create test data for CSV
        csv_data = [
            {
                "id": "test_symbol_1",
                "name": "Test Symbol 1",
                "system": "mechanical",
                "category": "test",
                "description": "Test description 1",
                "svg_content": "<svg><rect/></svg>"
            },
            {
                "id": "test_symbol_2",
                "name": "Test Symbol 2",
                "system": "electrical",
                "category": "test",
                "description": "Test description 2",
                "svg_content": "<svg><circle/></svg>"
            }
        ]
        
        # Test CSV Export
        csv_output = io.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=csv_data[0].keys())
        writer.writeheader()
        writer.writerows(csv_data)
        
        csv_content = csv_output.getvalue()
        self.assertIn("test_symbol_1", csv_content)
        self.assertIn("Test Symbol 1", csv_content)
        
        # Test CSV Import
        csv_input = io.StringIO(csv_content)
        reader = csv.DictReader(csv_input)
        imported_data = list(reader)
        
        self.assertEqual(len(imported_data), 2)
        self.assertEqual(imported_data[0]["name"], "Test Symbol 1")
    
    # Task 5.2.4: Test API endpoint integration
    @unittest.skipUnless(_api_available, "API not available")
    def test_api_endpoint_integration(self):
        """Test API endpoint integration."""
        # Mock FastAPI app and client
        try:
            from fastapi.testclient import TestClient
            from fastapi import FastAPI
            
            app = FastAPI()
            app.include_router(router)
            
            client = TestClient(app)
            
            # Test health check endpoint
            response = client.get("/api/v1/health")
            self.assertEqual(response.status_code, 200)
            
        except ImportError:
            self.skipTest("FastAPI TestClient not available")
    
    # Task 5.2.5: Test CLI tool integration
    @unittest.skipUnless(_cli_available, "CLI not available")
    def test_cli_integration(self):
        """Test CLI tool integration."""
        # Test CLI initialization
        self.assertIsNotNone(self.cli)
        self.assertIsNotNone(self.cli.symbol_manager)
        
        # Test CLI create command
        symbol_data = self.test_symbols["hvac_unit"].copy()
        symbol_data["id"] = "cli_test_symbol"
        
        # Mock CLI arguments
        args = MagicMock()
        args.file = None
        args.id = "cli_test_symbol"
        args.name = "CLI Test Symbol"
        args.system = "mechanical"
        args.description = "Test symbol created via CLI"
        args.category = "test"
        args.tags = "test,cli,mechanical"
        args.svg_content = "<svg><rect/></svg>"
        args.properties = '{"type": "test"}'
        args.output = None
        
        # Test create command
        result = self.cli.create_symbol(args)
        self.assertEqual(result, 0)  # Success
        
        # Verify symbol was created
        created_symbol = self.symbol_manager.get_symbol("cli_test_symbol")
        self.assertIsNotNone(created_symbol)
        self.assertEqual(created_symbol["name"], "CLI Test Symbol")
    
    @unittest.skipUnless(_cli_available, "CLI not available")
    def test_cli_list_command(self):
        """Test CLI list command."""
        # Create test symbols first
        symbol_data = self.test_symbols["hvac_unit"].copy()
        symbol_data["id"] = "cli_list_test"
        
        created_symbol = self.symbol_manager.create_symbol(symbol_data)
        self.assertIsNotNone(created_symbol)
        
        # Test list command
        args = MagicMock()
        args.system = None
        args.query = None
        args.limit = 10
        args.output = None
        
        # Mock print function to capture output
        with patch('builtins.print') as mock_print:
            result = self.cli.list_symbols(args)
            self.assertEqual(result, 0)  # Success
            
            # Verify output was printed
            mock_print.assert_called()
    
    # Task 5.2.6: Test validation integration
    def test_validation_integration(self):
        """Test validation integration across components."""
        # Test valid symbol validation
        valid_symbol = self.test_symbols["hvac_unit"].copy()
        
        # Test with schema validator
        is_valid, errors = self.schema_validator.validate_symbol(valid_symbol)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test with symbol manager validation
        validation_result = self.symbol_manager.validate_symbol_with_details(valid_symbol)
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(len(validation_result["errors"]), 0)
        
        # Test invalid symbol validation
        invalid_symbol = {
            "name": "Invalid Symbol",
            # Missing required fields: id, system, svg
        }
        
        # Test with schema validator
        is_valid, errors = self.schema_validator.validate_symbol(invalid_symbol)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Test with symbol manager validation
        validation_result = self.symbol_manager.validate_symbol_with_details(invalid_symbol)
        self.assertFalse(validation_result["is_valid"])
        self.assertGreater(len(validation_result["errors"]), 0)
    
    def test_bulk_validation_integration(self):
        """Test bulk validation integration."""
        # Create test symbols for validation
        symbols_data = [
            self.test_symbols["hvac_unit"].copy(),
            self.test_symbols["electrical_outlet"].copy()
        ]
        
        # Test bulk validation with schema validator
        validation_results = self.schema_validator.validate_symbols(symbols_data)
        self.assertEqual(len(validation_results), 2)
        
        # All symbols should be valid
        for result in validation_results:
            self.assertTrue(result["valid"])
        
        # Test with invalid symbols
        invalid_symbols = [
            {"name": "Invalid 1"},  # Missing required fields
            {"name": "Invalid 2", "system": "invalid_system"}  # Invalid system
        ]
        
        validation_results = self.schema_validator.validate_symbols(invalid_symbols)
        self.assertEqual(len(validation_results), 2)
        
        # All symbols should be invalid
        for result in validation_results:
            self.assertFalse(result["valid"])
    
    def test_error_handling_integration(self):
        """Test error handling integration across components."""
        # Test file not found errors
        with self.assertRaises(FileNotFoundError):
            JSONSymbolLibrary("/nonexistent/path")
        
        # Test invalid symbol creation
        invalid_symbol = {
            "name": "Invalid Symbol",
            # Missing required fields
        }
        
        with self.assertRaises(ValueError):
            self.symbol_manager.create_symbol(invalid_symbol)
        
        # Test duplicate symbol creation
        symbol_data = self.test_symbols["hvac_unit"].copy()
        symbol_data["id"] = "duplicate_test"
        
        # Create first symbol
        created_symbol = self.symbol_manager.create_symbol(symbol_data)
        symbol_id = created_symbol["id"]
        
        # Try to create duplicate
        duplicate_symbol = symbol_data.copy()
        duplicate_symbol["id"] = symbol_id
        
        with self.assertRaises(FileExistsError):
            self.symbol_manager.create_symbol(duplicate_symbol)
        
        # Test updating non-existent symbol
        result = self.symbol_manager.update_symbol("non_existent", {"name": "Updated"})
        self.assertIsNone(result)
        
        # Test deleting non-existent symbol
        result = self.symbol_manager.delete_symbol("non_existent")
        self.assertFalse(result)
        
        # Clean up
        self.symbol_manager.delete_symbol(symbol_id)
    
    def test_performance_integration(self):
        """Test performance integration with large datasets."""
        # Create multiple symbols for performance testing
        symbols_data = []
        for i in range(10):
            symbol_data = self.test_symbols["hvac_unit"].copy()
            symbol_data["name"] = f"Performance Test Symbol {i}"
            symbol_data["id"] = f"perf_test_{i}"
            symbols_data.append(symbol_data)
        
        # Test bulk creation performance
        start_time = __import__('time').time()
        created_symbols = self.symbol_manager.bulk_create_symbols(symbols_data)
        end_time = __import__('time').time()
        
        self.assertEqual(len(created_symbols), 10)
        self.assertLess(end_time - start_time, 5.0)  # Should complete within 5 seconds
        
        # Test search performance
        start_time = __import__('time').time()
        search_results = self.symbol_library.search_symbols("Performance")
        end_time = __import__('time').time()
        
        self.assertGreater(len(search_results), 0)
        self.assertLess(end_time - start_time, 2.0)  # Should complete within 2 seconds
        
        # Clean up
        symbol_ids = [symbol["id"] for symbol in created_symbols]
        self.symbol_manager.bulk_delete_symbols(symbol_ids)
    
    def test_cache_integration(self):
        """Test cache integration across components."""
        # Create test symbol
        symbol_data = self.test_symbols["hvac_unit"].copy()
        symbol_data["id"] = "cache_test_symbol"
        
        created_symbol = self.symbol_manager.create_symbol(symbol_data)
        symbol_id = created_symbol["id"]
        
        # Test cache invalidation
        # First load should populate cache
        symbols_before = self.symbol_library.load_all_symbols()
        self.assertIn(symbol_id, symbols_before)
        
        # Update symbol
        updates = {"name": "Cache Test Updated"}
        self.symbol_manager.update_symbol(symbol_id, updates)
        
        # Second load should reflect changes (cache should be invalidated)
        symbols_after = self.symbol_library.load_all_symbols()
        self.assertIn(symbol_id, symbols_after)
        self.assertEqual(symbols_after[symbol_id]["name"], "Cache Test Updated")
        
        # Test cache clearing
        self.symbol_library.clear_cache()
        self.assertEqual(len(self.symbol_library.symbols_cache), 0)
        
        # Reload should work
        symbols_reloaded = self.symbol_library.load_all_symbols()
        self.assertIn(symbol_id, symbols_reloaded)
        
        # Clean up
        self.symbol_manager.delete_symbol(symbol_id)
    
    def test_system_integration_end_to_end(self):
        """Test complete end-to-end system integration."""
        # 1. Create symbols via SymbolManager
        symbols_data = [
            self.test_symbols["hvac_unit"].copy(),
            self.test_symbols["electrical_outlet"].copy()
        ]
        
        # Ensure symbols have valid IDs
        symbols_data[0]["id"] = "e2e_test_hvac"
        symbols_data[1]["id"] = "e2e_test_electrical"
        
        created_symbols = self.symbol_manager.bulk_create_symbols(symbols_data)
        self.assertEqual(len(created_symbols), 2)
        
        # 2. Verify symbols are accessible via JSONSymbolLibrary
        all_symbols = self.symbol_library.load_all_symbols()
        for symbol in created_symbols:
            self.assertIn(symbol["id"], all_symbols)
        
        # 3. Test search functionality
        search_results = self.symbol_library.search_symbols("HVAC")
        self.assertGreater(len(search_results), 0)
        
        # 4. Test system-based loading
        mechanical_symbols = self.symbol_library.load_symbols_by_system("mechanical")
        electrical_symbols = self.symbol_library.load_symbols_by_system("electrical")
        
        self.assertGreater(len(mechanical_symbols), 0)
        self.assertGreater(len(electrical_symbols), 0)
        
        # 5. Test validation integration
        for symbol in created_symbols:
            is_valid, errors = self.schema_validator.validate_symbol(symbol)
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
        
        # 6. Test bulk operations
        symbol_ids = [symbol["id"] for symbol in created_symbols]
        updates = [
            {"id": symbol_ids[0], "name": "Updated HVAC Unit"},
            {"id": symbol_ids[1], "name": "Updated Electrical Outlet"}
        ]
        
        updated_symbols = self.symbol_manager.bulk_update_symbols(updates)
        self.assertEqual(len(updated_symbols), 2)
        
        # 7. Test deletion
        deleted_results = self.symbol_manager.bulk_delete_symbols(symbol_ids)
        self.assertEqual(len(deleted_results), 2)
        self.assertTrue(all(deleted_results.values()))
        
        # 8. Verify symbols are removed
        remaining_symbols = self.symbol_library.load_all_symbols()
        for symbol_id in symbol_ids:
            self.assertNotIn(symbol_id, remaining_symbols)


if __name__ == '__main__':
    unittest.main() 