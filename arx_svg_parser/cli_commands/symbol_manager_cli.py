#!/usr/bin/env python3
"""
Symbol Manager CLI

A command-line interface for managing SVG symbols in the Arxos system.
Provides commands for creating, updating, deleting, and listing symbols.

Author: Arxos Development Team
Date: 2024

Configuration:
  - CLI options (highest precedence)
  - Environment variables (ARXOS_SYMBOL_MANAGER_*)
  - Config file (YAML/JSON, --config or arxos_cli_config.yaml)

Example config YAML:
  symbol_library_path: ./symbols/
  log_level: INFO
  db_path: ./data/symbols.db

Example usage:
  python -m arx_svg_parser.cmd.symbol_manager_cli --config arxos_cli_config.yaml list
  ARXOS_SYMBOL_MANAGER_LOG_LEVEL=DEBUG python -m arx_svg_parser.cmd.symbol_manager_cli list
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

# Use relative imports for package context
try:
    from ..services.symbol_manager import SymbolManager
    from ..services.json_symbol_library import JSONSymbolLibrary
    from ..services.schema_validation import SymbolSchemaValidator
    from ..utils.auth import User, UserRole
except ImportError:
    # Fallback for direct script execution
    from services.symbol_manager import SymbolManager
    from services.json_symbol_library import JSONSymbolLibrary
    from services.schema_validation import SymbolSchemaValidator
    from utils.auth import User, UserRole

def load_config(args) -> dict:
    """Load config from file, env, and merge with CLI args."""
    config = {}
    # 1. Config file
    config_file = getattr(args, 'config', None) or os.environ.get('ARXOS_SYMBOL_MANAGER_CONFIG')
    if config_file:
        ext = Path(config_file).suffix.lower()
        try:
            with open(config_file, 'r') as f:
                if ext in ['.yaml', '.yml'] and yaml:
                    config = yaml.safe_load(f)
                elif ext == '.json':
                    config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    else:
        # Try default config in CWD or home
        for default in [Path.cwd() / 'arxos_cli_config.yaml', Path.home() / 'arxos_cli_config.yaml']:
            if default.exists() and yaml:
                with open(default, 'r') as f:
                    config = yaml.safe_load(f)
                break
    # 2. Env vars
    for key, value in os.environ.items():
        if key.startswith('ARXOS_SYMBOL_MANAGER_'):
            config[key[len('ARXOS_SYMBOL_MANAGER_'):].lower()] = value
    # 3. CLI args (highest precedence)
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v
    return config

class SymbolManagerCLI:
    """Command-line interface for symbol management operations."""
    
    def __init__(self):
        """Initialize the CLI with symbol manager and library."""
        self.symbol_manager = SymbolManager()
        self.symbol_library = JSONSymbolLibrary()
        self.schema_validator = SymbolSchemaValidator()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/cli.log', mode='a')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"ℹ️  {message}")
    
    def print_warning(self, message: str):
        """Print warning message."""
        print(f"⚠️  {message}")
    
    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Load and parse JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
    
    def save_json_file(self, data: Dict[str, Any], file_path: str):
        """Save data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Error writing file {file_path}: {e}")
    
    def validate_symbol_data(self, data: Dict[str, Any]) -> bool:
        """Validate symbol data against JSON schema."""
        valid, errors = self.schema_validator.validate_symbol(data)
        
        if not valid:
            for error in errors:
                self.print_error(f"Validation error: {error}")
            return False
        
        return True
    
    def create_symbol(self, args):
        """Create a new symbol."""
        try:
            # Load symbol data
            if args.file:
                symbol_data = self.load_json_file(args.file)
            else:
                # Create from command line arguments
                symbol_data = {
                    'id': args.id,
                    'name': args.name,
                    'system': args.system,
                    'description': args.description,
                    'category': args.category,
                    'tags': args.tags.split(',') if args.tags else [],
                    'svg': {
                        'content': args.svg_content or '<svg></svg>'
                    }
                }
                
                if args.properties:
                    try:
                        symbol_data['properties'] = json.loads(args.properties)
                    except json.JSONDecodeError:
                        self.print_error("Invalid JSON in properties argument")
                        return 1
            
            # Validate symbol data
            if not self.validate_symbol_data(symbol_data):
                return 1
            
            # Create symbol
            created_symbol = self.symbol_manager.create_symbol(symbol_data)
            
            if created_symbol:
                self.print_success(f"Symbol '{created_symbol['id']}' created successfully")
                if args.output:
                    self.save_json_file(created_symbol, args.output)
                    self.print_info(f"Symbol data saved to: {args.output}")
                return 0
            else:
                self.print_error("Failed to create symbol")
                return 1
                
        except ValueError as e:
            self.print_error(str(e))
            return 1
        except Exception as e:
            self.logger.error(f"Create symbol failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def update_symbol(self, args):
        """Update an existing symbol."""
        try:
            # Load update data
            if args.file:
                update_data = self.load_json_file(args.file)
            else:
                # Create update data from command line arguments
                update_data = {}
                
                if args.name:
                    update_data['name'] = args.name
                if args.system:
                    update_data['system'] = args.system
                if args.description:
                    update_data['description'] = args.description
                if args.category:
                    update_data['category'] = args.category
                if args.tags:
                    update_data['tags'] = args.tags.split(',')
                if args.svg_content:
                    update_data['svg'] = {'content': args.svg_content}
                if args.properties:
                    try:
                        update_data['properties'] = json.loads(args.properties)
                    except json.JSONDecodeError:
                        self.print_error("Invalid JSON in properties argument")
                        return 1
            
            if not update_data:
                self.print_error("No update data provided")
                return 1
            
            # Update symbol
            updated_symbol = self.symbol_manager.update_symbol(args.id, update_data)
            
            if updated_symbol:
                self.print_success(f"Symbol '{args.id}' updated successfully")
                if args.output:
                    self.save_json_file(updated_symbol, args.output)
                    self.print_info(f"Updated symbol data saved to: {args.output}")
                return 0
            else:
                self.print_error(f"Symbol '{args.id}' not found")
                return 1
                
        except ValueError as e:
            self.print_error(str(e))
            return 1
        except Exception as e:
            self.logger.error(f"Update symbol failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def delete_symbol(self, args):
        """Delete a symbol."""
        try:
            # Confirm deletion
            if not args.force:
                confirm = input(f"Are you sure you want to delete symbol '{args.id}'? (y/N): ")
                if confirm.lower() != 'y':
                    self.print_info("Deletion cancelled")
                    return 0
            
            # Delete symbol
            deleted = self.symbol_manager.delete_symbol(args.id)
            
            if deleted:
                self.print_success(f"Symbol '{args.id}' deleted successfully")
                return 0
            else:
                self.print_error(f"Symbol '{args.id}' not found")
                return 1
                
        except Exception as e:
            self.logger.error(f"Delete symbol failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def list_symbols(self, args):
        """List symbols with optional filtering."""
        try:
            # Get symbols
            if args.query:
                symbols = self.symbol_manager.search_symbols(args.query, system=args.system)
            else:
                symbols = self.symbol_manager.list_symbols(system=args.system)
            
            if not symbols:
                self.print_info("No symbols found")
                return 0
            
            # Apply pagination
            total_count = len(symbols)
            if args.limit:
                symbols = symbols[:args.limit]
            
            # Display symbols
            self.print_info(f"Found {len(symbols)} symbols (total: {total_count})")
            print()
            
            for i, symbol in enumerate(symbols, 1):
                print(f"{i}. {symbol['id']} - {symbol['name']}")
                print(f"   System: {symbol['system']}")
                if symbol.get('description'):
                    print(f"   Description: {symbol['description']}")
                if symbol.get('category'):
                    print(f"   Category: {symbol['category']}")
                if symbol.get('tags'):
                    print(f"   Tags: {', '.join(symbol['tags'])}")
                print()
            
            # Save to file if requested
            if args.output:
                self.save_json_file({'symbols': symbols, 'total_count': total_count}, args.output)
                self.print_info(f"Symbol list saved to: {args.output}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"List symbols failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def get_symbol(self, args):
        """Get a specific symbol by ID."""
        try:
            symbol = self.symbol_manager.get_symbol(args.id)
            
            if symbol:
                if args.output:
                    self.save_json_file(symbol, args.output)
                    self.print_info(f"Symbol data saved to: {args.output}")
                else:
                    print(json.dumps(symbol, indent=2, ensure_ascii=False))
                
                return 0
            else:
                self.print_error(f"Symbol '{args.id}' not found")
                return 1
                
        except Exception as e:
            self.logger.error(f"Get symbol failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def bulk_import(self, args):
        """Bulk import symbols from file."""
        try:
            # Load symbols data
            symbols_data = self.load_json_file(args.file)
            
            if not isinstance(symbols_data, list):
                if isinstance(symbols_data, dict) and 'symbols' in symbols_data:
                    symbols_data = symbols_data['symbols']
                else:
                    self.print_error("File must contain a list of symbols or an object with 'symbols' key")
                    return 1
            
            if not symbols_data:
                self.print_error("No symbols found in file")
                return 1
            
            self.print_info(f"Importing {len(symbols_data)} symbols...")
            
            # Import symbols
            successful = 0
            failed = 0
            errors = []
            
            for i, symbol_data in enumerate(symbols_data, 1):
                try:
                    if self.validate_symbol_data(symbol_data):
                        self.symbol_manager.create_symbol(symbol_data)
                        successful += 1
                        print(f"  ✅ {i}/{len(symbols_data)}: {symbol_data['id']}")
                    else:
                        failed += 1
                        errors.append(f"Symbol {i}: Validation failed")
                        print(f"  ❌ {i}/{len(symbols_data)}: Validation failed")
                except Exception as e:
                    failed += 1
                    errors.append(f"Symbol {i}: {str(e)}")
                    print(f"  ❌ {i}/{len(symbols_data)}: {str(e)}")
            
            # Summary
            print()
            self.print_success(f"Import completed: {successful} successful, {failed} failed")
            
            if errors and args.output:
                error_data = {
                    'summary': {
                        'total': len(symbols_data),
                        'successful': successful,
                        'failed': failed
                    },
                    'errors': errors
                }
                self.save_json_file(error_data, args.output)
                self.print_info(f"Error details saved to: {args.output}")
            
            return 0 if failed == 0 else 1
            
        except Exception as e:
            self.logger.error(f"Bulk import failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def bulk_export(self, args):
        """Bulk export symbols to file."""
        try:
            # Get symbols
            if args.system:
                symbols = self.symbol_manager.list_symbols(system=args.system)
            else:
                symbols = self.symbol_manager.list_symbols()
            
            if not symbols:
                self.print_error("No symbols found to export")
                return 1
            
            # Apply limit if specified
            if args.limit:
                symbols = symbols[:args.limit]
            
            # Export data
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_symbols': len(symbols),
                    'system_filter': args.system,
                    'limit_applied': args.limit
                },
                'symbols': symbols
            }
            
            # Save to file
            self.save_json_file(export_data, args.output)
            self.print_success(f"Exported {len(symbols)} symbols to: {args.output}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Bulk export failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def get_statistics(self, args):
        """Get symbol statistics."""
        try:
            stats = self.symbol_manager.get_symbol_statistics()
            
            if args.output:
                self.save_json_file(stats, args.output)
                self.print_info(f"Statistics saved to: {args.output}")
            else:
                print("Symbol Statistics")
                print("=" * 50)
                print(f"Total Symbols: {stats['total_symbols']}")
                print()
                print("By System:")
                for system, count in stats['systems'].items():
                    print(f"  {system}: {count}")
                print()
                print("Symbol Sizes:")
                for size_range, count in stats['symbol_sizes'].items():
                    print(f"  {size_range}: {count}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Get statistics failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def validate_symbols(self, args):
        """Validate symbol data against JSON schema (file, directory, or batch)."""
        try:
            # Support directory validation
            if args.dir:
                dir_path = Path(args.dir)
                if not dir_path.is_dir():
                    self.print_error(f"Not a directory: {args.dir}")
                    return 1
                symbol_files = list(dir_path.glob("*.json"))
                if not symbol_files:
                    self.print_warning(f"No JSON files found in directory: {args.dir}")
                    return 1
                all_symbols = []
                for file in symbol_files:
                    try:
                        symbols_data = self.load_json_file(str(file))
                        if isinstance(symbols_data, dict):
                            all_symbols.append(symbols_data)
                        elif isinstance(symbols_data, list):
                            all_symbols.extend(symbols_data)
                    except Exception as e:
                        self.print_error(f"Failed to load {file}: {e}")
                symbols = all_symbols
                is_single = False
            else:
                # Load symbols from file
                symbols_data = self.load_json_file(args.file)
                if isinstance(symbols_data, dict):
                    symbols = [symbols_data]
                    is_single = True
                elif isinstance(symbols_data, list):
                    symbols = symbols_data
                    is_single = False
                else:
                    self.print_error("File must contain a symbol object or array of symbols")
                    return 1

            # Validate symbols with detailed error reporting
            results = self.symbol_manager.validate_batch_with_details(symbols)
            valid_count = results["valid_symbols"]
            total_count = results["total_symbols"]
            invalid_count = results["invalid_symbols"]

            # Display results
            print(f"Validation Results: {valid_count}/{total_count} symbols valid")
            print("=" * 50)
            for detail in results["validation_details"]:
                idx = detail.get("index", "?")
                name = detail.get("symbol_name", "?")
                if detail["is_valid"]:
                    print(f"✅ Symbol {idx} ({name}): Valid")
                else:
                    print(f"❌ Symbol {idx} ({name}): Invalid")
                    for error in detail["errors"]:
                        print(f"    - {error['field_path']}: {error['message']}")

            # Save detailed results if requested
            if args.output:
                output_data = {
                    'summary': {
                        'total_symbols': total_count,
                        'valid_symbols': valid_count,
                        'invalid_symbols': invalid_count
                    },
                    'details': results["validation_details"]
                }
                self.save_json_file(output_data, args.output)
                self.print_info(f"Validation results saved to: {args.output}")

            # Print schema info if requested
            if getattr(args, 'schema_info', False):
                schema_info = self.schema_validator.get_schema_info()
                print("\nSchema Info:")
                print(json.dumps(schema_info, indent=2))

            # Return appropriate exit code
            return 0 if valid_count == total_count else 1

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1
    
    def validate_library(self, args):
        """Validate the entire symbol library and optionally save a report."""
        try:
            symbols = list(self.symbol_library.load_all_symbols().values())
            results = self.symbol_manager.validate_batch_with_details(symbols)
            valid_count = results["valid_symbols"]
            total_count = results["total_symbols"]
            invalid_count = results["invalid_symbols"]
            print(f"Library Validation Results: {valid_count}/{total_count} symbols valid")
            print("=" * 50)
            for detail in results["validation_details"]:
                idx = detail.get("index", "?")
                name = detail.get("symbol_name", "?")
                if detail["is_valid"]:
                    print(f"✅ Symbol {idx} ({name}): Valid")
                else:
                    print(f"❌ Symbol {idx} ({name}): Invalid")
                    for error in detail["errors"]:
                        print(f"    - {error['field_path']}: {error['message']}")
            if args.output:
                output_data = {
                    'summary': {
                        'total_symbols': total_count,
                        'valid_symbols': valid_count,
                        'invalid_symbols': invalid_count
                    },
                    'details': results["validation_details"]
                }
                self.save_json_file(output_data, args.output)
                self.print_info(f"Validation report saved to: {args.output}")
            return 0 if valid_count == total_count else 1
        except Exception as e:
            self.logger.error(f"Library validation failed: {e}")
            self.print_error(f"Unexpected error: {e}")
            return 1

    def setup_parser(self):
        """Setup command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Arxos Symbol Manager CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Create a symbol from file
  python symbol_manager_cli.py create --file symbol.json

  # Create a symbol from command line
  python symbol_manager_cli.py create --id "test_symbol" --name "Test Symbol" --system electrical

  # Update a symbol
  python symbol_manager_cli.py update --id "test_symbol" --name "Updated Symbol"

  # List all symbols
  python symbol_manager_cli.py list

  # Search symbols
  python symbol_manager_cli.py list --query "electrical" --system electrical

  # Delete a symbol
  python symbol_manager_cli.py delete --id "test_symbol"

  # Bulk import
  python symbol_manager_cli.py bulk-import --file symbols.json

  # Bulk export
  python symbol_manager_cli.py bulk-export --output exported_symbols.json

  # Validate a file
  python symbol_manager_cli.py validate --file symbol.json

  # Validate all symbols in a directory
  python symbol_manager_cli.py validate --dir symbols/

  # Validate and print schema info
  python symbol_manager_cli.py validate --file symbol.json --schema-info
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Create symbol command
        create_parser = subparsers.add_parser('create', help='Create a new symbol')
        create_parser.add_argument('--file', help='JSON file containing symbol data')
        create_parser.add_argument('--id', help='Symbol ID')
        create_parser.add_argument('--name', help='Symbol name')
        create_parser.add_argument('--system', help='System category')
        create_parser.add_argument('--description', help='Symbol description')
        create_parser.add_argument('--category', help='Symbol category')
        create_parser.add_argument('--tags', help='Comma-separated tags')
        create_parser.add_argument('--svg-content', help='SVG content')
        create_parser.add_argument('--properties', help='JSON string of custom properties')
        create_parser.add_argument('--output', help='Output file for created symbol data')
        
        # Update symbol command
        update_parser = subparsers.add_parser('update', help='Update an existing symbol')
        update_parser.add_argument('--id', required=True, help='Symbol ID to update')
        update_parser.add_argument('--file', help='JSON file containing update data')
        update_parser.add_argument('--name', help='New symbol name')
        update_parser.add_argument('--system', help='New system category')
        update_parser.add_argument('--description', help='New description')
        update_parser.add_argument('--category', help='New category')
        update_parser.add_argument('--tags', help='Comma-separated tags')
        update_parser.add_argument('--svg-content', help='New SVG content')
        update_parser.add_argument('--properties', help='JSON string of custom properties')
        update_parser.add_argument('--output', help='Output file for updated symbol data')
        
        # Delete symbol command
        delete_parser = subparsers.add_parser('delete', help='Delete a symbol')
        delete_parser.add_argument('--id', required=True, help='Symbol ID to delete')
        delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
        
        # List symbols command
        list_parser = subparsers.add_parser('list', help='List symbols')
        list_parser.add_argument('--system', help='Filter by system')
        list_parser.add_argument('--query', help='Search query')
        list_parser.add_argument('--limit', type=int, help='Limit number of results')
        list_parser.add_argument('--output', help='Output file for symbol list')
        
        # Get symbol command
        get_parser = subparsers.add_parser('get', help='Get a specific symbol')
        get_parser.add_argument('--id', required=True, help='Symbol ID')
        get_parser.add_argument('--output', help='Output file for symbol data')
        
        # Bulk import command
        bulk_import_parser = subparsers.add_parser('bulk-import', help='Bulk import symbols from file')
        bulk_import_parser.add_argument('--file', required=True, help='JSON file containing symbols')
        bulk_import_parser.add_argument('--output', help='Output file for error details')
        
        # Bulk export command
        bulk_export_parser = subparsers.add_parser('bulk-export', help='Bulk export symbols to file')
        bulk_export_parser.add_argument('--output', required=True, help='Output file for exported symbols')
        bulk_export_parser.add_argument('--system', help='Filter by system')
        bulk_export_parser.add_argument('--limit', type=int, help='Limit number of symbols')
        
        # Statistics command
        stats_parser = subparsers.add_parser('stats', help='Get symbol statistics')
        stats_parser.add_argument('--output', help='Output file for statistics')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate symbol data (file or directory)')
        validate_parser.add_argument('--file', help='JSON file containing symbol(s) to validate')
        validate_parser.add_argument('--dir', help='Directory containing symbol JSON files to validate')
        validate_parser.add_argument('--output', help='Output file for validation results')
        validate_parser.add_argument('--schema-info', action='store_true', help='Print schema information')
        # Validate library command
        validate_lib_parser = subparsers.add_parser('validate-library', help='Validate the entire symbol library')
        validate_lib_parser.add_argument('--output', help='Output file for validation report')
        return parser
    
    def run(self):
        """Run the CLI."""
        parser = self.setup_parser()
        parser.add_argument('--config', help='Path to YAML/JSON config file')
        args = parser.parse_args()
        config = load_config(args)
        # Optionally use config for library path, log level, etc.
        # Example: self.symbol_library = JSONSymbolLibrary(config.get('symbol_library_path', ...))
        if not config.get('command'):
            parser.print_help()
            return 1
        
        # Execute command
        if args.command == 'create':
            return self.create_symbol(args)
        elif args.command == 'update':
            return self.update_symbol(args)
        elif args.command == 'delete':
            return self.delete_symbol(args)
        elif args.command == 'list':
            return self.list_symbols(args)
        elif args.command == 'get':
            return self.get_symbol(args)
        elif args.command == 'bulk-import':
            return self.bulk_import(args)
        elif args.command == 'bulk-export':
            return self.bulk_export(args)
        elif args.command == 'stats':
            return self.get_statistics(args)
        elif args.command == 'validate':
            return self.validate_symbols(args)
        elif args.command == 'validate-library':
            return self.validate_library(args)
        else:
            self.print_error(f"Unknown command: {args.command}")
            return 1

def main():
    cli = SymbolManagerCLI()
    cli.run()

if __name__ == "__main__":
    main() 