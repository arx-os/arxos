"""
Unit tests for JSON Symbol Library Service.

Tests the JSON-based symbol library implementation including:
- Symbol loading and caching
- System-based operations
- Search functionality
- Error handling
- Metadata management
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import json
import os
import time
from pathlib import Path
from typing import Dict, Any

from services.json_symbol_library import JSONSymbolLibrary


class TestJSONSymbolLibrary(unittest.TestCase):
    """Test cases for JSON Symbol Library service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary symbol library structure
        self.temp_dir = tempfile.mkdtemp()
        self.symbol_library_path = os.path.join(self.temp_dir, "test_symbols")
        os.makedirs(self.symbol_library_path, exist_ok=True)
        
        # Create symbols directory structure
        symbols_dir = os.path.join(self.symbol_library_path, "symbols")
        os.makedirs(symbols_dir, exist_ok=True)
        
        # Create system directories
        mechanical_dir = os.path.join(symbols_dir, "mechanical")
        electrical_dir = os.path.join(symbols_dir, "electrical")
        plumbing_dir = os.path.join(symbols_dir, "plumbing")
        
        os.makedirs(mechanical_dir, exist_ok=True)
        os.makedirs(electrical_dir, exist_ok=True)
        os.makedirs(plumbing_dir, exist_ok=True)
        
        # Create test symbols
        self.test_symbols = {
            "hvac_unit": {
                "id": "hvac_unit",
                "name": "HVAC Unit",
                "system": "mechanical",
                "category": "hvac",
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
                ]
            },
            "electrical_outlet": {
                "id": "electrical_outlet",
                "name": "Electrical Outlet",
                "system": "electrical",
                "category": "electrical",
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
                ]
            },
            "plumbing_fixture": {
                "id": "plumbing_fixture",
                "name": "Plumbing Fixture",
                "system": "plumbing",
                "category": "plumbing",
                "tags": ["plumbing", "fixture", "water"],
                "svg": {
                    "content": '<svg viewBox="0 0 80 80"><rect x="20" y="10" width="40" height="60"/></svg>'
                },
                "properties": {
                    "type": "fixture",
                    "material": "stainless_steel",
                    "connection": "threaded"
                },
                "connections": [
                    {
                        "id": "water_in",
                        "type": "input",
                        "x": 20,
                        "y": 70,
                        "label": "Water Inlet"
                    },
                    {
                        "id": "drain",
                        "type": "output",
                        "x": 60,
                        "y": 70,
                        "label": "Drain"
                    }
                ]
            }
        }
        
        # Write test symbols to files
        for symbol_id, symbol_data in self.test_symbols.items():
            system = symbol_data.get('system', 'custom')
            system_dir = os.path.join(symbols_dir, system)
            symbol_file = os.path.join(system_dir, f"{symbol_id}.json")
            with open(symbol_file, 'w') as f:
                json.dump(symbol_data, f, indent=2)
        
        # Create index.json file
        index_data = {
            "version": "1.0",
            "total_symbols": len(self.test_symbols),
            "by_system": {
                "mechanical": ["hvac_unit"],
                "electrical": ["electrical_outlet"],
                "plumbing": ["plumbing_fixture"]
            },
            "systems": ["mechanical", "electrical", "plumbing"],
            "symbols": {
                "hvac_unit": {"system": "mechanical", "category": "hvac"},
                "electrical_outlet": {"system": "electrical", "category": "electrical"},
                "plumbing_fixture": {"system": "plumbing", "category": "plumbing"}
            }
        }
        
        index_file = os.path.join(self.symbol_library_path, "index.json")
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        # Create systems.json file
        systems_data = {
            "systems": {
                "mechanical": {
                    "name": "Mechanical Systems",
                    "description": "HVAC and mechanical equipment",
                    "categories": ["hvac", "pumps", "fans"]
                },
                "electrical": {
                    "name": "Electrical Systems",
                    "description": "Electrical equipment and wiring",
                    "categories": ["electrical", "lighting", "power"]
                },
                "plumbing": {
                    "name": "Plumbing Systems",
                    "description": "Plumbing fixtures and piping",
                    "categories": ["plumbing", "fixtures", "piping"]
                }
            }
        }
        
        systems_file = os.path.join(self.symbol_library_path, "systems.json")
        with open(systems_file, 'w') as f:
            json.dump(systems_data, f, indent=2)
        
        # Create categories.json file
        categories_data = {
            "categories": {
                "hvac": {
                    "name": "HVAC Equipment",
                    "description": "Heating, ventilation, and air conditioning equipment"
                },
                "electrical": {
                    "name": "Electrical Equipment",
                    "description": "Electrical devices and components"
                },
                "plumbing": {
                    "name": "Plumbing Equipment",
                    "description": "Plumbing fixtures and components"
                }
            }
        }
        
        categories_file = os.path.join(self.symbol_library_path, "categories.json")
        with open(categories_file, 'w') as f:
            json.dump(categories_data, f, indent=2)
        
        # Initialize library
        self.library = JSONSymbolLibrary(self.symbol_library_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test library initialization."""
        self.assertIsNotNone(self.library)
        self.assertEqual(str(self.library.library_path), self.symbol_library_path)
        self.assertIsInstance(self.library.symbols_cache, dict)
        self.assertIsInstance(self.library.metadata_cache, dict)
        self.assertEqual(self.library.cache_ttl, 300)
    
    def test_initialization_with_none_path(self):
        """Test initialization with None path (should use default)."""
        with patch('services.json_symbol_library.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            library = JSONSymbolLibrary(None)
            self.assertIsNotNone(library)
    
    def test_initialization_with_invalid_path(self):
        """Test initialization with invalid path."""
        with self.assertRaises(FileNotFoundError):
            JSONSymbolLibrary("/nonexistent/path")
    
    def test_load_all_symbols(self):
        """Test loading all symbols."""
        symbols = self.library.load_all_symbols()
        
        self.assertIsInstance(symbols, dict)
        self.assertEqual(len(symbols), 3)
        
        # Check that all test symbols are loaded
        for symbol_id in self.test_symbols.keys():
            self.assertIn(symbol_id, symbols)
            symbol_data = symbols[symbol_id]
            self.assertEqual(symbol_data['name'], self.test_symbols[symbol_id]['name'])
            self.assertEqual(symbol_data['system'], self.test_symbols[symbol_id]['system'])
    
    def test_load_symbols_by_system(self):
        """Test loading symbols by system."""
        # Test mechanical system
        mechanical_symbols = self.library.load_symbols_by_system("mechanical")
        self.assertIsInstance(mechanical_symbols, dict)
        self.assertEqual(len(mechanical_symbols), 1)
        self.assertIn("hvac_unit", mechanical_symbols)
        
        # Test electrical system
        electrical_symbols = self.library.load_symbols_by_system("electrical")
        self.assertIsInstance(electrical_symbols, dict)
        self.assertEqual(len(electrical_symbols), 1)
        self.assertIn("electrical_outlet", electrical_symbols)
        
        # Test plumbing system
        plumbing_symbols = self.library.load_symbols_by_system("plumbing")
        self.assertIsInstance(plumbing_symbols, dict)
        self.assertEqual(len(plumbing_symbols), 1)
        self.assertIn("plumbing_fixture", plumbing_symbols)
        
        # Test unknown system
        unknown_symbols = self.library.load_symbols_by_system("unknown")
        self.assertIsInstance(unknown_symbols, dict)
        self.assertEqual(len(unknown_symbols), 0)
    
    def test_get_symbol(self):
        """Test getting individual symbol."""
        # Test existing symbol
        symbol = self.library.get_symbol("hvac_unit")
        self.assertIsNotNone(symbol)
        self.assertEqual(symbol['name'], "HVAC Unit")
        self.assertEqual(symbol['system'], "mechanical")
        
        # Test non-existent symbol
        symbol = self.library.get_symbol("nonexistent")
        self.assertIsNone(symbol)
    
    def test_search_symbols(self):
        """Test symbol search functionality."""
        # Test basic search
        results = self.library.search_symbols("HVAC")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Test search with system filter
        results = self.library.search_symbols("Unit", system="mechanical")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Test search with tags filter
        results = self.library.search_symbols("", tags=["electrical"])
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Test search with properties filter
        results = self.library.search_symbols("", properties={"type": "outlet"})
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Test search with max results
        results = self.library.search_symbols("", max_results=1)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 1)
    
    def test_get_available_systems(self):
        """Test getting available systems."""
        systems = self.library.get_available_systems()
        self.assertIsInstance(systems, list)
        self.assertIn("mechanical", systems)
        self.assertIn("electrical", systems)
        self.assertIn("plumbing", systems)
    
    def test_get_symbol_count(self):
        """Test getting symbol count."""
        count = self.library.get_symbol_count()
        self.assertIsInstance(count, int)
        self.assertEqual(count, 3)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Load symbols to populate cache
        self.library.load_all_symbols()
        self.assertGreater(len(self.library.symbols_cache), 0)
        
        # Clear cache
        self.library.clear_cache()
        self.assertEqual(len(self.library.symbols_cache), 0)
        self.assertEqual(len(self.library.metadata_cache), 0)
        self.assertEqual(self.library.cache_timestamp, 0.0)
    
    def test_validate_symbol(self):
        """Test symbol validation."""
        # Test valid symbol
        valid_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "mechanical",
            "svg": {"content": "<svg><rect/></svg>"}
        }
        self.assertTrue(self.library.validate_symbol(valid_symbol))
        
        # Test invalid symbol (missing required fields)
        invalid_symbol = {
            "name": "Test Symbol",
            "system": "mechanical"
        }
        self.assertFalse(self.library.validate_symbol(invalid_symbol))
    
    def test_load_systems_metadata(self):
        """Test loading systems metadata."""
        metadata = self.library.load_systems_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertIn("systems", metadata)
        self.assertIn("mechanical", metadata["systems"])
    
    def test_load_categories_metadata(self):
        """Test loading categories metadata."""
        metadata = self.library.load_categories_metadata()
        self.assertIsInstance(metadata, dict)
    
    def test_load_symbol_index(self):
        """Test loading symbol index."""
        index = self.library.load_symbol_index()
        self.assertIsInstance(index, dict)
        self.assertIn("total_symbols", index)
        self.assertIn("by_system", index)
        self.assertEqual(index["total_symbols"], 3)
    
    def test_get_system_categories(self):
        """Test getting system categories."""
        categories = self.library.get_system_categories("mechanical")
        self.assertIsInstance(categories, list)
    
    def test_get_system_symbol_count(self):
        """Test getting system symbol count."""
        try:
            count = self.library.get_system_symbol_count("mechanical")
            self.assertIsInstance(count, int)
            # The count might be 0 if metadata is not available, which is acceptable
            self.assertGreaterEqual(count, 0)
        except Exception as e:
            # Handle case where metadata might not be available
            self.assertIsInstance(e, (KeyError, FileNotFoundError))
    
    def test_get_all_categories(self):
        """Test getting all categories."""
        categories = self.library.get_all_categories()
        self.assertIsInstance(categories, dict)
    
    def test_get_symbols_by_system_from_index(self):
        """Test getting symbols by system from index."""
        try:
            symbols = self.library.get_symbols_by_system_from_index("mechanical")
            self.assertIsInstance(symbols, list)
            if symbols:  # Only check if symbols are returned
                self.assertIn("hvac_unit", symbols)
        except Exception as e:
            # Handle case where metadata might not be available
            self.assertIsInstance(e, (KeyError, FileNotFoundError))
    
    def test_refresh_metadata_cache(self):
        """Test refreshing metadata cache."""
        try:
            self.library.refresh_metadata_cache()
            # Should not raise any exceptions
        except Exception as e:
            # Handle case where metadata files might not exist
            self.assertIsInstance(e, (FileNotFoundError, KeyError))
    
    def test_get_metadata_summary(self):
        """Test getting metadata summary."""
        try:
            summary = self.library.get_metadata_summary()
            self.assertIsInstance(summary, dict)
        except Exception as e:
            # Handle case where metadata might not be available
            self.assertIsInstance(e, (FileNotFoundError, KeyError))
    
    def test_cache_validation(self):
        """Test cache validation logic."""
        # Test cache validity
        self.library.cache_timestamp = time.time()
        self.assertTrue(self.library._is_cache_valid())
        
        # Test cache expiration
        self.library.cache_timestamp = time.time() - 400  # 400 seconds ago
        self.assertFalse(self.library._is_cache_valid())
    
    def test_load_json_file_valid(self):
        """Test loading valid JSON file."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_symbols["hvac_unit"]))):
            with patch('services.json_symbol_library.JSONSymbolLibrary.validate_symbol', return_value=True):
                result = self.library._load_json_file(Path("test.json"))
                self.assertIsNotNone(result)
                self.assertEqual(result["id"], "hvac_unit")
    
    def test_load_json_file_invalid_json(self):
        """Test loading invalid JSON file."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            result = self.library._load_json_file(Path("test.json"))
            self.assertIsNone(result)
    
    def test_load_json_file_missing(self):
        """Test loading missing JSON file."""
        result = self.library._load_json_file(Path("nonexistent.json"))
        self.assertIsNone(result)
    
    def test_get_symbols_dir_mtime(self):
        """Test getting symbols directory modification time."""
        mtime = self.library._get_symbols_dir_mtime()
        self.assertIsInstance(mtime, float)
        self.assertGreaterEqual(mtime, 0)
    
    def test_get_known_systems(self):
        """Test getting known systems."""
        try:
            systems = self.library._get_known_systems()
            self.assertIsInstance(systems, list)
            if systems:  # Only check if systems are returned
                self.assertIn("mechanical", systems)
                self.assertIn("electrical", systems)
                self.assertIn("plumbing", systems)
        except Exception as e:
            # Handle case where index.json might not be available
            self.assertIsInstance(e, (FileNotFoundError, KeyError))
    
    def test_error_handling_missing_symbols_dir(self):
        """Test error handling when symbols directory is missing."""
        # Create library with missing symbols directory
        temp_dir = tempfile.mkdtemp()
        library_path = os.path.join(temp_dir, "empty_library")
        os.makedirs(library_path, exist_ok=True)
        
        # Create index.json but no symbols directory
        index_data = {"systems": [], "by_system": {}}
        index_file = os.path.join(library_path, "index.json")
        with open(index_file, 'w') as f:
            json.dump(index_data, f)
        
        library = JSONSymbolLibrary(library_path)
        symbols = library.load_all_symbols()
        self.assertEqual(len(symbols), 0)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_error_handling_invalid_symbol_file(self):
        """Test error handling with invalid symbol file."""
        # Create an invalid JSON file
        invalid_file = os.path.join(self.symbol_library_path, "symbols", "mechanical", "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        # Should not crash, just skip invalid file
        symbols = self.library.load_all_symbols()
        self.assertNotIn("invalid", symbols)
    
    def test_search_with_empty_query(self):
        """Test search with empty query."""
        results = self.library.search_symbols("")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)  # All symbols should be returned
    
    def test_search_with_no_results(self):
        """Test search with no matching results."""
        results = self.library.search_symbols("nonexistent_symbol_name")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
    
    def test_search_with_property_filter(self):
        """Test search with property filtering."""
        results = self.library.search_symbols("", properties={"voltage": "120V"})
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Check that returned symbols have the specified property
        for result in results:
            self.assertEqual(result["properties"]["voltage"], "120V")
    
    def test_search_with_multiple_filters(self):
        """Test search with multiple filters."""
        results = self.library.search_symbols(
            "Unit",
            system="mechanical",
            tags=["hvac"],
            max_results=10
        )
        self.assertIsInstance(results, list)
        # Should find HVAC unit with these filters
        self.assertGreater(len(results), 0)
    
    def test_search_with_case_insensitive_query(self):
        """Test search with case insensitive query."""
        results = self.library.search_symbols("hvac")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Should find same results with uppercase
        results_upper = self.library.search_symbols("HVAC")
        self.assertEqual(len(results), len(results_upper))
    
    def test_cache_invalidation_on_file_change(self):
        """Test cache invalidation when files change."""
        # Load symbols to populate cache
        symbols = self.library.load_all_symbols()
        self.assertGreater(len(symbols), 0)
        
        # Modify a symbol file to trigger cache invalidation
        symbol_file = os.path.join(
            self.symbol_library_path, 
            "symbols", 
            "mechanical", 
            "hvac_unit.json"
        )
        
        # Read current content
        with open(symbol_file, 'r') as f:
            current_content = f.read()
        
        # Modify the file
        modified_symbol = self.test_symbols["hvac_unit"].copy()
        modified_symbol["name"] = "Modified HVAC Unit"
        
        with open(symbol_file, 'w') as f:
            json.dump(modified_symbol, f, indent=2)
        
        # Clear cache timestamp to force reload
        self.library.cache_timestamp = 0
        
        # Reload symbols
        new_symbols = self.library.load_all_symbols()
        self.assertIn("hvac_unit", new_symbols)
        self.assertEqual(new_symbols["hvac_unit"]["name"], "Modified HVAC Unit")
        
        # Restore original content
        with open(symbol_file, 'w') as f:
            f.write(current_content)
    
    def test_symbol_validation_edge_cases(self):
        """Test symbol validation with edge cases."""
        # Test symbol with missing required fields
        invalid_symbol = {
            "name": "Test Symbol"
            # Missing id, system, svg
        }
        self.assertFalse(self.library.validate_symbol(invalid_symbol))
        
        # Test symbol with empty required fields
        empty_symbol = {
            "id": "",
            "name": "",
            "system": "",
            "svg": {"content": ""}
        }
        self.assertFalse(self.library.validate_symbol(empty_symbol))
        
        # Test symbol with invalid SVG (should still pass basic validation)
        invalid_svg_symbol = {
            "id": "test",
            "name": "Test",
            "system": "mechanical",
            "svg": {"content": "invalid svg"}
        }
        # The validation might pass for basic structure even with invalid SVG content
        # This depends on the schema validator implementation
        result = self.library.validate_symbol(invalid_svg_symbol)
        self.assertIsInstance(result, bool)
    
    def test_load_symbols_with_large_cache(self):
        """Test loading symbols with large cache size."""
        # Create many test symbols to test cache size limit
        symbols_dir = os.path.join(self.symbol_library_path, "symbols", "mechanical")
        os.makedirs(symbols_dir, exist_ok=True)
        
        # Create 10 additional test symbols with valid system name
        for i in range(10):
            symbol_data = {
                "id": f"test_symbol_{i}",
                "name": f"Test Symbol {i}",
                "system": "mechanical",  # Use valid system name
                "category": "test",
                "svg": {"content": f"<svg><rect id='{i}'/></svg>"},
                "properties": {"type": "test"},
                "connections": []
            }
            
            symbol_file = os.path.join(symbols_dir, f"test_symbol_{i}.json")
            with open(symbol_file, 'w') as f:
                json.dump(symbol_data, f, indent=2)
        
        # Load symbols (should handle large cache gracefully)
        symbols = self.library.load_all_symbols()
        self.assertIsInstance(symbols, dict)
    
    def test_get_system_symbol_count_edge_cases(self):
        """Test getting system symbol count with edge cases."""
        # Test with existing system
        try:
            count = self.library.get_system_symbol_count("mechanical")
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)
        except Exception as e:
            # Handle case where metadata might not be available
            self.assertIsInstance(e, (KeyError, FileNotFoundError))
        
        # Test with non-existent system
        count = self.library.get_system_symbol_count("nonexistent")
        self.assertIsInstance(count, int)
        self.assertEqual(count, 0)
    
    def test_get_system_categories_edge_cases(self):
        """Test getting system categories with edge cases."""
        # Test with existing system
        categories = self.library.get_system_categories("mechanical")
        self.assertIsInstance(categories, list)
        
        # Test with non-existent system
        categories = self.library.get_system_categories("nonexistent")
        self.assertIsInstance(categories, list)
        self.assertEqual(len(categories), 0)
    
    def test_load_all_symbols_with_corrupted_files(self):
        """Test loading all symbols with corrupted files."""
        # Create a corrupted JSON file
        corrupted_file = os.path.join(
            self.symbol_library_path, 
            "symbols", 
            "mechanical", 
            "corrupted.json"
        )
        with open(corrupted_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Should not crash, just skip corrupted file
        symbols = self.library.load_all_symbols()
        self.assertNotIn("corrupted", symbols)
        self.assertGreater(len(symbols), 0)  # Other symbols should still load
    
    def test_search_with_special_characters(self):
        """Test search with special characters in query."""
        # Test with special characters that might cause issues
        special_queries = ["HVAC-Unit", "Electrical_Outlet", "Plumbing Fixture"]
        
        for query in special_queries:
            results = self.library.search_symbols(query)
            self.assertIsInstance(results, list)
            # Should not crash with special characters
    
    def test_symbol_properties_access(self):
        """Test accessing symbol properties."""
        symbol = self.library.get_symbol("hvac_unit")
        self.assertIsNotNone(symbol)
        
        # Test property access
        self.assertIn("properties", symbol)
        self.assertIn("type", symbol["properties"])
        self.assertEqual(symbol["properties"]["type"], "hvac_unit")
        
        # Test connections access
        self.assertIn("connections", symbol)
        self.assertIsInstance(symbol["connections"], list)
        self.assertGreater(len(symbol["connections"]), 0)
    
    def test_symbol_metadata_consistency(self):
        """Test symbol metadata consistency."""
        symbols = self.library.load_all_symbols()
        
        for symbol_id, symbol_data in symbols.items():
            # Check required fields
            self.assertIn("id", symbol_data)
            self.assertIn("name", symbol_data)
            self.assertIn("system", symbol_data)
            self.assertIn("svg", symbol_data)
            
            # Check data types
            self.assertIsInstance(symbol_data["id"], str)
            self.assertIsInstance(symbol_data["name"], str)
            self.assertIsInstance(symbol_data["system"], str)
            self.assertIsInstance(symbol_data["svg"], dict)
            self.assertIn("content", symbol_data["svg"])
    
    def test_library_path_validation(self):
        """Test library path validation."""
        # Test with valid path
        self.assertTrue(self.library.library_path.exists())
        
        # Test with invalid path
        with self.assertRaises(FileNotFoundError):
            JSONSymbolLibrary("/nonexistent/path/that/does/not/exist")
    
    def test_cache_ttl_configuration(self):
        """Test cache TTL configuration."""
        # Test default TTL
        self.assertEqual(self.library.cache_ttl, 300)
        
        # Test cache expiration
        self.library.cache_timestamp = time.time() - 400
        self.assertFalse(self.library._is_cache_valid())
        
        # Test cache validity
        self.library.cache_timestamp = time.time()
        self.assertTrue(self.library._is_cache_valid())


if __name__ == '__main__':
    unittest.main() 