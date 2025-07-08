"""
Unit tests for Symbol Manager CLI.

This module tests the CLI functionality including:
- Command argument parsing
- Symbol creation, update, delete operations
- File operations (load/save)
- Error handling
- Output formatting

Author: Arxos Development Team
Date: 2024
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.symbol_manager_cli import SymbolManagerCLI

class TestSymbolManagerCLI:
    """Test cases for SymbolManagerCLI class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.cli = SymbolManagerCLI()
        
        # Mock symbol manager
        self.mock_symbol_manager = Mock()
        self.cli.symbol_manager = self.mock_symbol_manager
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test CLI initialization."""
        assert self.cli.symbol_manager is not None
        assert self.cli.symbol_library is not None
        assert self.cli.logger is not None
    
    def test_print_methods(self):
        """Test print utility methods."""
        # Test success message
        with patch('builtins.print') as mock_print:
            self.cli.print_success("Test success")
            mock_print.assert_called_with("✅ Test success")
        
        # Test error message
        with patch('builtins.print') as mock_print:
            self.cli.print_error("Test error")
            mock_print.assert_called_with("❌ Test error")
        
        # Test info message
        with patch('builtins.print') as mock_print:
            self.cli.print_info("Test info")
            mock_print.assert_called_with("ℹ️  Test info")
        
        # Test warning message
        with patch('builtins.print') as mock_print:
            self.cli.print_warning("Test warning")
            mock_print.assert_called_with("⚠️  Test warning")
    
    def test_load_json_file_success(self):
        """Test successful JSON file loading."""
        test_data = {"test": "data"}
        test_file = os.path.join(self.temp_dir, "test.json")
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.cli.load_json_file(test_file)
        assert result == test_data
    
    def test_load_json_file_not_found(self):
        """Test JSON file loading with non-existent file."""
        with pytest.raises(ValueError, match="File not found"):
            self.cli.load_json_file("nonexistent.json")
    
    def test_load_json_file_invalid_json(self):
        """Test JSON file loading with invalid JSON."""
        test_file = os.path.join(self.temp_dir, "invalid.json")
        
        with open(test_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            self.cli.load_json_file(test_file)
    
    def test_save_json_file_success(self):
        """Test successful JSON file saving."""
        test_data = {"test": "data"}
        test_file = os.path.join(self.temp_dir, "output.json")
        
        self.cli.save_json_file(test_data, test_file)
        
        with open(test_file, 'r') as f:
            result = json.load(f)
        
        assert result == test_data
    
    def test_save_json_file_error(self):
        """Test JSON file saving with error."""
        # Try to save to a directory (should fail)
        test_data = {"test": "data"}
        test_file = self.temp_dir  # Directory, not file
        
        with pytest.raises(ValueError, match="Error writing file"):
            self.cli.save_json_file(test_data, test_file)
    
    def test_validate_symbol_data_valid(self):
        """Test symbol data validation with valid data."""
        valid_data = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical"
        }
        
        assert self.cli.validate_symbol_data(valid_data) is True
    
    def test_validate_symbol_data_missing_fields(self):
        """Test symbol data validation with missing fields."""
        invalid_data = {
            "id": "test_symbol",
            "name": "Test Symbol"
            # Missing 'system' field
        }
        
        assert self.cli.validate_symbol_data(invalid_data) is False
    
    def test_validate_symbol_data_empty_fields(self):
        """Test symbol data validation with empty fields."""
        invalid_data = {
            "id": "",
            "name": "Test Symbol",
            "system": "electrical"
        }
        
        assert self.cli.validate_symbol_data(invalid_data) is False
    
    def test_validate_symbol_data_invalid_system(self):
        """Test symbol data validation with invalid system."""
        data_with_warning = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "invalid_system"
        }
        
        with patch.object(self.cli, 'print_warning') as mock_warning:
            result = self.cli.validate_symbol_data(data_with_warning)
            assert result is True
            mock_warning.assert_called_once()
    
    def test_create_symbol_from_file(self):
        """Test symbol creation from file."""
        # Create test file
        test_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical",
            "description": "Test description"
        }
        test_file = os.path.join(self.temp_dir, "symbol.json")
        
        with open(test_file, 'w') as f:
            json.dump(test_symbol, f)
        
        # Mock symbol manager
        self.mock_symbol_manager.create_symbol.return_value = test_symbol
        
        # Create args
        args = Mock()
        args.file = test_file
        args.output = None
        
        result = self.cli.create_symbol(args)
        assert result == 0
        self.mock_symbol_manager.create_symbol.assert_called_once_with(test_symbol)
    
    def test_create_symbol_from_command_line(self):
        """Test symbol creation from command line arguments."""
        # Mock symbol manager
        test_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical"
        }
        self.mock_symbol_manager.create_symbol.return_value = test_symbol
        
        # Create args
        args = Mock()
        args.file = None
        args.id = "test_symbol"
        args.name = "Test Symbol"
        args.system = "electrical"
        args.description = "Test description"
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = None
        args.output = None
        
        result = self.cli.create_symbol(args)
        assert result == 0
        
        # Verify the symbol data passed to create_symbol
        call_args = self.mock_symbol_manager.create_symbol.call_args[0][0]
        assert call_args["id"] == "test_symbol"
        assert call_args["name"] == "Test Symbol"
        assert call_args["system"] == "electrical"
        assert call_args["description"] == "Test description"
        assert call_args["tags"] == []
        assert call_args["svg"]["content"] == "<svg></svg>"
    
    def test_create_symbol_with_tags_and_properties(self):
        """Test symbol creation with tags and properties."""
        # Mock symbol manager
        test_symbol = {"id": "test_symbol"}
        self.mock_symbol_manager.create_symbol.return_value = test_symbol
        
        # Create args
        args = Mock()
        args.file = None
        args.id = "test_symbol"
        args.name = "Test Symbol"
        args.system = "electrical"
        args.description = None
        args.category = None
        args.tags = "tag1,tag2,tag3"
        args.svg_content = "<svg>test</svg>"
        args.properties = '{"key": "value"}'
        args.output = None
        
        result = self.cli.create_symbol(args)
        assert result == 0
        
        # Verify the symbol data
        call_args = self.mock_symbol_manager.create_symbol.call_args[0][0]
        assert call_args["tags"] == ["tag1", "tag2", "tag3"]
        assert call_args["svg"]["content"] == "<svg>test</svg>"
        assert call_args["properties"] == {"key": "value"}
    
    def test_create_symbol_invalid_properties_json(self):
        """Test symbol creation with invalid properties JSON."""
        args = Mock()
        args.file = None
        args.id = "test_symbol"
        args.name = "Test Symbol"
        args.system = "electrical"
        args.description = None
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = "{ invalid json }"
        args.output = None
        
        result = self.cli.create_symbol(args)
        assert result == 1
    
    def test_create_symbol_validation_failure(self):
        """Test symbol creation with validation failure."""
        args = Mock()
        args.file = None
        args.id = ""  # Empty ID should fail validation
        args.name = "Test Symbol"
        args.system = "electrical"
        args.description = None
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = None
        args.output = None
        
        result = self.cli.create_symbol(args)
        assert result == 1
    
    def test_create_symbol_manager_error(self):
        """Test symbol creation when symbol manager fails."""
        self.mock_symbol_manager.create_symbol.return_value = None
        
        args = Mock()
        args.file = None
        args.id = "test_symbol"
        args.name = "Test Symbol"
        args.system = "electrical"
        args.description = None
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = None
        args.output = None
        
        result = self.cli.create_symbol(args)
        assert result == 1
    
    def test_update_symbol_from_file(self):
        """Test symbol update from file."""
        # Create test file
        update_data = {
            "name": "Updated Symbol",
            "description": "Updated description"
        }
        test_file = os.path.join(self.temp_dir, "update.json")
        
        with open(test_file, 'w') as f:
            json.dump(update_data, f)
        
        # Mock symbol manager
        updated_symbol = {"id": "test_symbol", "name": "Updated Symbol"}
        self.mock_symbol_manager.update_symbol.return_value = updated_symbol
        
        # Create args
        args = Mock()
        args.id = "test_symbol"
        args.file = test_file
        args.output = None
        
        result = self.cli.update_symbol(args)
        assert result == 0
        self.mock_symbol_manager.update_symbol.assert_called_once_with("test_symbol", update_data)
    
    def test_update_symbol_from_command_line(self):
        """Test symbol update from command line arguments."""
        # Mock symbol manager
        updated_symbol = {"id": "test_symbol", "name": "Updated Symbol"}
        self.mock_symbol_manager.update_symbol.return_value = updated_symbol
        
        # Create args
        args = Mock()
        args.id = "test_symbol"
        args.file = None
        args.name = "Updated Symbol"
        args.system = None
        args.description = "Updated description"
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = None
        args.output = None
        
        result = self.cli.update_symbol(args)
        assert result == 0
        
        # Verify the update data
        call_args = self.mock_symbol_manager.update_symbol.call_args[0][1]
        assert call_args["name"] == "Updated Symbol"
        assert call_args["description"] == "Updated description"
    
    def test_update_symbol_no_data(self):
        """Test symbol update with no update data."""
        args = Mock()
        args.id = "test_symbol"
        args.file = None
        args.name = None
        args.system = None
        args.description = None
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = None
        args.output = None
        
        result = self.cli.update_symbol(args)
        assert result == 1
    
    def test_update_symbol_not_found(self):
        """Test symbol update when symbol not found."""
        self.mock_symbol_manager.update_symbol.return_value = None
        
        args = Mock()
        args.id = "nonexistent_symbol"
        args.file = None
        args.name = "Updated Symbol"
        args.system = None
        args.description = None
        args.category = None
        args.tags = None
        args.svg_content = None
        args.properties = None
        args.output = None
        
        result = self.cli.update_symbol(args)
        assert result == 1
    
    def test_delete_symbol_success(self):
        """Test symbol deletion with confirmation."""
        self.mock_symbol_manager.delete_symbol.return_value = True
        
        args = Mock()
        args.id = "test_symbol"
        args.force = False
        
        with patch('builtins.input', return_value='y'):
            result = self.cli.delete_symbol(args)
        
        assert result == 0
        self.mock_symbol_manager.delete_symbol.assert_called_once_with("test_symbol")
    
    def test_delete_symbol_cancelled(self):
        """Test symbol deletion when user cancels."""
        args = Mock()
        args.id = "test_symbol"
        args.force = False
        
        with patch('builtins.input', return_value='n'):
            result = self.cli.delete_symbol(args)
        
        assert result == 0
        self.mock_symbol_manager.delete_symbol.assert_not_called()
    
    def test_delete_symbol_force(self):
        """Test symbol deletion with force flag."""
        self.mock_symbol_manager.delete_symbol.return_value = True
        
        args = Mock()
        args.id = "test_symbol"
        args.force = True
        
        result = self.cli.delete_symbol(args)
        assert result == 0
        self.mock_symbol_manager.delete_symbol.assert_called_once_with("test_symbol")
    
    def test_delete_symbol_not_found(self):
        """Test symbol deletion when symbol not found."""
        self.mock_symbol_manager.delete_symbol.return_value = False
        
        args = Mock()
        args.id = "nonexistent_symbol"
        args.force = True
        
        result = self.cli.delete_symbol(args)
        assert result == 1
    
    def test_list_symbols_all(self):
        """Test listing all symbols."""
        test_symbols = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"}
        ]
        self.mock_symbol_manager.list_symbols.return_value = test_symbols
        
        args = Mock()
        args.system = None
        args.query = None
        args.limit = None
        args.output = None
        
        result = self.cli.list_symbols(args)
        assert result == 0
        self.mock_symbol_manager.list_symbols.assert_called_once_with(system=None)
    
    def test_list_symbols_with_system_filter(self):
        """Test listing symbols with system filter."""
        test_symbols = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"}
        ]
        self.mock_symbol_manager.list_symbols.return_value = test_symbols
        
        args = Mock()
        args.system = "electrical"
        args.query = None
        args.limit = None
        args.output = None
        
        result = self.cli.list_symbols(args)
        assert result == 0
        self.mock_symbol_manager.list_symbols.assert_called_once_with(system="electrical")
    
    def test_list_symbols_with_search(self):
        """Test listing symbols with search query."""
        test_symbols = [
            {"id": "symbol1", "name": "Test Symbol", "system": "electrical"}
        ]
        self.mock_symbol_manager.search_symbols.return_value = test_symbols
        
        args = Mock()
        args.system = None
        args.query = "test"
        args.limit = None
        args.output = None
        
        result = self.cli.list_symbols(args)
        assert result == 0
        self.mock_symbol_manager.search_symbols.assert_called_once_with("test", system=None)
    
    def test_list_symbols_with_limit(self):
        """Test listing symbols with limit."""
        test_symbols = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"},
            {"id": "symbol3", "name": "Symbol 3", "system": "plumbing"}
        ]
        self.mock_symbol_manager.list_symbols.return_value = test_symbols
        
        args = Mock()
        args.system = None
        args.query = None
        args.limit = 2
        args.output = None
        
        result = self.cli.list_symbols(args)
        assert result == 0
    
    def test_list_symbols_empty(self):
        """Test listing symbols when none found."""
        self.mock_symbol_manager.list_symbols.return_value = []
        
        args = Mock()
        args.system = None
        args.query = None
        args.limit = None
        args.output = None
        
        result = self.cli.list_symbols(args)
        assert result == 0
    
    def test_get_symbol_success(self):
        """Test getting a specific symbol."""
        test_symbol = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "electrical"
        }
        self.mock_symbol_manager.get_symbol.return_value = test_symbol
        
        args = Mock()
        args.id = "test_symbol"
        args.output = None
        
        with patch('builtins.print') as mock_print:
            result = self.cli.get_symbol(args)
        
        assert result == 0
        self.mock_symbol_manager.get_symbol.assert_called_once_with("test_symbol")
        mock_print.assert_called()
    
    def test_get_symbol_not_found(self):
        """Test getting a symbol that doesn't exist."""
        self.mock_symbol_manager.get_symbol.return_value = None
        
        args = Mock()
        args.id = "nonexistent_symbol"
        args.output = None
        
        result = self.cli.get_symbol(args)
        assert result == 1
    
    def test_bulk_import_success(self):
        """Test bulk import of symbols."""
        # Create test file
        test_symbols = [
            {
                "id": "bulk1",
                "name": "Bulk Symbol 1",
                "system": "electrical"
            },
            {
                "id": "bulk2",
                "name": "Bulk Symbol 2",
                "system": "mechanical"
            }
        ]
        test_file = os.path.join(self.temp_dir, "bulk_symbols.json")
        
        with open(test_file, 'w') as f:
            json.dump(test_symbols, f)
        
        # Mock symbol manager
        self.mock_symbol_manager.create_symbol.return_value = {"id": "test"}
        
        args = Mock()
        args.file = test_file
        args.output = None
        
        result = self.cli.bulk_import(args)
        assert result == 0
        assert self.mock_symbol_manager.create_symbol.call_count == 2
    
    def test_bulk_import_with_errors(self):
        """Test bulk import with some errors."""
        # Create test file
        test_symbols = [
            {
                "id": "valid1",
                "name": "Valid Symbol",
                "system": "electrical"
            },
            {
                "id": "",  # Invalid - empty ID
                "name": "Invalid Symbol",
                "system": "electrical"
            }
        ]
        test_file = os.path.join(self.temp_dir, "bulk_symbols.json")
        
        with open(test_file, 'w') as f:
            json.dump(test_symbols, f)
        
        # Mock symbol manager
        self.mock_symbol_manager.create_symbol.return_value = {"id": "test"}
        
        args = Mock()
        args.file = test_file
        args.output = None
        
        result = self.cli.bulk_import(args)
        assert result == 1  # Should return 1 due to validation errors
        assert self.mock_symbol_manager.create_symbol.call_count == 1  # Only valid symbol
    
    def test_bulk_export_success(self):
        """Test bulk export of symbols."""
        test_symbols = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"}
        ]
        self.mock_symbol_manager.list_symbols.return_value = test_symbols
        
        output_file = os.path.join(self.temp_dir, "exported_symbols.json")
        
        args = Mock()
        args.output = output_file
        args.system = None
        args.limit = None
        
        result = self.cli.bulk_export(args)
        assert result == 0
        
        # Verify file was created
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            exported_data = json.load(f)
        
        assert "export_info" in exported_data
        assert "symbols" in exported_data
        assert len(exported_data["symbols"]) == 2
    
    def test_bulk_export_no_symbols(self):
        """Test bulk export when no symbols exist."""
        self.mock_symbol_manager.list_symbols.return_value = []
        
        output_file = os.path.join(self.temp_dir, "exported_symbols.json")
        
        args = Mock()
        args.output = output_file
        args.system = None
        args.limit = None
        
        result = self.cli.bulk_export(args)
        assert result == 1
    
    def test_get_statistics_success(self):
        """Test getting symbol statistics."""
        test_stats = {
            "total_symbols": 10,
            "systems": {"electrical": 5, "mechanical": 3, "plumbing": 2},
            "symbol_sizes": {"small": 3, "medium": 5, "large": 2}
        }
        self.mock_symbol_manager.get_symbol_statistics.return_value = test_stats
        
        args = Mock()
        args.output = None
        
        with patch('builtins.print') as mock_print:
            result = self.cli.get_statistics(args)
        
        assert result == 0
        self.mock_symbol_manager.get_symbol_statistics.assert_called_once()
        mock_print.assert_called()
    
    def test_setup_parser(self):
        """Test argument parser setup."""
        parser = self.cli.setup_parser()
        assert parser is not None
        
        # Test that all subcommands are added
        subcommands = [action.dest for action in parser._actions if hasattr(action, 'dest')]
        expected_commands = ['create', 'update', 'delete', 'list', 'get', 'bulk-import', 'bulk-export', 'stats']
        
        for command in expected_commands:
            assert command in subcommands
    
    def test_run_with_help(self):
        """Test CLI run with help command."""
        with patch('sys.argv', ['symbol_manager_cli.py', '--help']):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                result = self.cli.run()
                assert result == 1
                mock_help.assert_called_once()
    
    def test_run_with_no_command(self):
        """Test CLI run with no command."""
        with patch('sys.argv', ['symbol_manager_cli.py']):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                result = self.cli.run()
                assert result == 1
                mock_help.assert_called_once()
    
    def test_run_with_unknown_command(self):
        """Test CLI run with unknown command."""
        with patch('sys.argv', ['symbol_manager_cli.py', 'unknown']):
            result = self.cli.run()
            assert result == 1

    def test_validate_file_valid_and_invalid(self):
        """Test validate --file with valid and invalid symbols."""
        valid_symbol = {
            "id": "val1", "name": "Valid 1", "system": "mechanical", "svg": {"content": "<svg></svg>"}
        }
        invalid_symbol = {
            "id": "inv1", "name": "", "system": "invalid", "svg": {"content": ""}
        }
        test_file = os.path.join(self.temp_dir, "symbols.json")
        with open(test_file, 'w') as f:
            json.dump([valid_symbol, invalid_symbol], f)
        args = Mock()
        args.file = test_file
        args.dir = None
        args.output = None
        args.schema_info = False
        # Patch print to capture output
        with patch('builtins.print') as mock_print:
            exit_code = self.cli.validate_symbols(args)
            assert exit_code == 1  # Not all valid
            calls = [c[0][0] for c in mock_print.call_args_list]
            assert any("Valid" in call for call in calls)
            assert any("Invalid" in call for call in calls)

    def test_validate_dir_mixed(self):
        """Test validate --dir with a directory of valid and invalid symbol files."""
        valid_symbol = {
            "id": "val2", "name": "Valid 2", "system": "mechanical", "svg": {"content": "<svg></svg>"}
        }
        invalid_symbol = {
            "id": "inv2", "name": "", "system": "invalid", "svg": {"content": ""}
        }
        dir_path = os.path.join(self.temp_dir, "symbols")
        os.makedirs(dir_path, exist_ok=True)
        with open(os.path.join(dir_path, "valid.json"), 'w') as f:
            json.dump(valid_symbol, f)
        with open(os.path.join(dir_path, "invalid.json"), 'w') as f:
            json.dump(invalid_symbol, f)
        args = Mock()
        args.file = None
        args.dir = dir_path
        args.output = None
        args.schema_info = False
        with patch('builtins.print') as mock_print:
            exit_code = self.cli.validate_symbols(args)
            assert exit_code == 1
            calls = [c[0][0] for c in mock_print.call_args_list]
            assert any("Valid" in call for call in calls)
            assert any("Invalid" in call for call in calls)

    def test_validate_schema_info(self):
        """Test validate --file with --schema-info option."""
        valid_symbol = {
            "id": "val3", "name": "Valid 3", "system": "mechanical", "svg": {"content": "<svg></svg>"}
        }
        test_file = os.path.join(self.temp_dir, "symbol.json")
        with open(test_file, 'w') as f:
            json.dump(valid_symbol, f)
        args = Mock()
        args.file = test_file
        args.dir = None
        args.output = None
        args.schema_info = True
        with patch('builtins.print') as mock_print:
            exit_code = self.cli.validate_symbols(args)
            assert exit_code == 0
            calls = [c[0][0] for c in mock_print.call_args_list]
            assert any("Schema Info" in call for call in calls)

    def test_validate_output_file(self):
        """Test validate --file with --output option."""
        valid_symbol = {
            "id": "val4", "name": "Valid 4", "system": "mechanical", "svg": {"content": "<svg></svg>"}
        }
        test_file = os.path.join(self.temp_dir, "symbol.json")
        with open(test_file, 'w') as f:
            json.dump(valid_symbol, f)
        output_file = os.path.join(self.temp_dir, "results.json")
        args = Mock()
        args.file = test_file
        args.dir = None
        args.output = output_file
        args.schema_info = False
        exit_code = self.cli.validate_symbols(args)
        assert exit_code == 0
        assert os.path.exists(output_file)
        with open(output_file) as f:
            data = json.load(f)
        assert data['summary']['valid_symbols'] == 1
        assert data['summary']['invalid_symbols'] == 0

    def test_validate_exit_codes(self):
        """Test validate exit codes for all valid and some invalid symbols."""
        valid_symbol = {
            "id": "val5", "name": "Valid 5", "system": "mechanical", "svg": {"content": "<svg></svg>"}
        }
        invalid_symbol = {
            "id": "inv5", "name": "", "system": "invalid", "svg": {"content": ""}
        }
        test_file = os.path.join(self.temp_dir, "symbols.json")
        with open(test_file, 'w') as f:
            json.dump([valid_symbol, invalid_symbol], f)
        args = Mock()
        args.file = test_file
        args.dir = None
        args.output = None
        args.schema_info = False
        # All valid
        with patch.object(self.cli.symbol_manager, 'validate_batch_with_details', return_value={
            'total_symbols': 2, 'valid_symbols': 2, 'invalid_symbols': 0, 'validation_details': [
                {'is_valid': True, 'errors': [], 'index': 0, 'symbol_name': 'val5'},
                {'is_valid': True, 'errors': [], 'index': 1, 'symbol_name': 'inv5'}
            ]
        }):
            exit_code = self.cli.validate_symbols(args)
            assert exit_code == 0
        # Some invalid
        with patch.object(self.cli.symbol_manager, 'validate_batch_with_details', return_value={
            'total_symbols': 2, 'valid_symbols': 1, 'invalid_symbols': 1, 'validation_details': [
                {'is_valid': True, 'errors': [], 'index': 0, 'symbol_name': 'val5'},
                {'is_valid': False, 'errors': [{'field_path': 'name', 'message': 'Empty'}], 'index': 1, 'symbol_name': 'inv5'}
            ]
        }):
            exit_code = self.cli.validate_symbols(args)
            assert exit_code == 1

def run_cli(args, env=None):
    cmd = [sys.executable, '-m', 'arx_svg_parser.cmd.symbol_manager_cli'] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result

def test_help():
    result = run_cli(['--help'])
    assert result.returncode == 0
    assert 'usage' in result.stdout.lower()
    assert 'Available commands' in result.stdout or 'create' in result.stdout

def test_config_precedence(tmp_path):
    # Create a config file
    config_path = tmp_path / 'config.yaml'
    config_path.write_text('log_level: DEBUG\n')
    result = run_cli(['--config', str(config_path), 'list'])
    # Should not error, even if no symbols
    assert result.returncode in (0, 1)
    assert 'log_level' not in result.stderr

@pytest.mark.skip(reason='Requires symbol data to be present')
def test_list_symbols():
    result = run_cli(['list'])
    assert result.returncode in (0, 1)
    # Should print something about symbols or no symbols found
    assert 'symbol' in result.stdout.lower() or 'no symbols' in result.stdout.lower()

if __name__ == "__main__":
    pytest.main([__file__]) 