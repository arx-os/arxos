#!/usr/bin/env python3
"""
Symbol Schema Validator Service Example

This script demonstrates the comprehensive validation capabilities of the
SymbolSchemaValidator service, including individual symbol validation,
file validation, library validation, and detailed error reporting.

Author: Arxos Development Team
Date: 2024
"""

import json
import os
import tempfile
from pathlib import Path
from services.symbol_schema_validator import SymbolSchemaValidator

def create_test_data():
    """Create test data for validation examples."""
    
    # Valid symbols
    valid_symbols = [
        {
            "id": "electrical_outlet",
            "name": "Electrical Outlet",
            "system": "electrical",
            "description": "Standard electrical outlet",
            "svg": {
                "content": "<svg width='50' height='50'><circle cx='25' cy='25' r='20' fill='black'/></svg>"
            },
            "properties": {
                "voltage": "220V",
                "current": "10A"
            },
            "connections": [
                {
                    "id": "power_in",
                    "type": "input",
                    "x": 0,
                    "y": 25,
                    "label": "Power In"
                }
            ]
        },
        {
            "id": "mechanical_valve",
            "name": "Mechanical Valve",
            "system": "mechanical",
            "description": "Control valve for mechanical systems",
            "svg": {
                "content": "<svg width='50' height='50'><rect width='40' height='30' fill='blue'/></svg>"
            },
            "properties": {
                "pressure": "100PSI",
                "material": "steel"
            }
        }
    ]
    
    # Invalid symbols with various issues
    invalid_symbols = [
        {
            "id": "Invalid-ID!",  # Invalid ID pattern
            "name": "Invalid Symbol 1",
            "system": "electrical",
            "svg": {"content": "<svg></svg>"}
        },
        {
            "id": "valid_id",
            "name": "Invalid Symbol 2",
            "system": "not_a_system",  # Invalid system
            "svg": {"content": "<svg></svg>"}
        },
        {
            "id": "valid_id",
            "name": "Invalid Symbol 3",
            "system": "electrical",
            "svg": {}  # Missing content
        },
        {
            "id": "valid_id",
            "name": "Invalid Symbol 4",
            "system": "electrical",
            "svg": {"content": ""}  # Empty content
        },
        {
            "id": "valid_id",
            "name": "Invalid Symbol 5",
            "system": "electrical"
            # Missing required svg field
        }
    ]
    
    return valid_symbols, invalid_symbols

def create_test_files(valid_symbols, invalid_symbols):
    """Create test files for validation."""
    
    # Create valid symbol file
    with open("valid_symbols.json", "w") as f:
        json.dump(valid_symbols, f, indent=2)
    
    # Create invalid symbols file
    with open("invalid_symbols.json", "w") as f:
        json.dump(invalid_symbols, f, indent=2)
    
    # Create mixed symbols file
    with open("mixed_symbols.json", "w") as f:
        json.dump(valid_symbols + invalid_symbols, f, indent=2)
    
    # Create single symbol file
    with open("single_symbol.json", "w") as f:
        json.dump(valid_symbols[0], f, indent=2)
    
    print("✅ Created test files:")
    print("  - valid_symbols.json")
    print("  - invalid_symbols.json")
    print("  - mixed_symbols.json")
    print("  - single_symbol.json")

def create_test_library(valid_symbols, invalid_symbols):
    """Create a test library structure."""
    
    # Create library directory
    library_dir = Path("test_library")
    library_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (library_dir / "electrical").mkdir(exist_ok=True)
    (library_dir / "mechanical").mkdir(exist_ok=True)
    (library_dir / "invalid").mkdir(exist_ok=True)
    
    # Create valid symbol files
    for i, symbol in enumerate(valid_symbols):
        system_dir = library_dir / symbol["system"]
        file_path = system_dir / f"{symbol['id']}.json"
        with open(file_path, "w") as f:
            json.dump(symbol, f, indent=2)
    
    # Create invalid symbol files
    for i, symbol in enumerate(invalid_symbols):
        file_path = library_dir / "invalid" / f"invalid_{i}.json"
        with open(file_path, "w") as f:
            json.dump(symbol, f, indent=2)
    
    # Create a non-JSON file (should be ignored)
    with open(library_dir / "readme.txt", "w") as f:
        f.write("This is not a JSON file")
    
    print("✅ Created test library structure:")
    print("  - test_library/")
    print("    - electrical/")
    print("    - mechanical/")
    print("    - invalid/")
    print("    - readme.txt")

def demonstrate_individual_validation(validator, valid_symbols, invalid_symbols):
    """Demonstrate individual symbol validation."""
    print("\n🔍 Individual Symbol Validation")
    print("=" * 50)
    
    # Test valid symbols
    print("\nValid Symbols:")
    for i, symbol in enumerate(valid_symbols):
        is_valid, errors = validator.validate_symbol(symbol)
        print(f"  Symbol {i+1}: {'✅ Valid' if is_valid else '❌ Invalid'}")
        if errors:
            for error in errors:
                print(f"    - {error['field_path']}: {error['message']}")
    
    # Test invalid symbols
    print("\nInvalid Symbols:")
    for i, symbol in enumerate(invalid_symbols):
        is_valid, errors = validator.validate_symbol(symbol)
        print(f"  Symbol {i+1}: {'✅ Valid' if is_valid else '❌ Invalid'}")
        if errors:
            for error in errors:
                print(f"    - {error['field_path']}: {error['message']}")

def demonstrate_file_validation(validator):
    """Demonstrate file validation."""
    print("\n📁 File Validation")
    print("=" * 50)
    
    test_files = [
        "single_symbol.json",
        "valid_symbols.json",
        "invalid_symbols.json",
        "mixed_symbols.json"
    ]
    
    for file_path in test_files:
        print(f"\nValidating {file_path}:")
        result = validator.validate_symbol_file(file_path)
        
        stats = result["statistics"]
        print(f"  Total Symbols: {stats['total_symbols']}")
        print(f"  Valid Symbols: {stats['valid_symbols']}")
        print(f"  Invalid Symbols: {stats['invalid_symbols']}")
        print(f"  Overall: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
        
        # Show detailed results for invalid files
        if not result['valid'] and 'results' in result:
            print("  Details:")
            for symbol_result in result['results']:
                if not symbol_result['valid']:
                    print(f"    Symbol {symbol_result['symbol_id']}:")
                    for error in symbol_result['errors']:
                        print(f"      - {error['field_path']}: {error['message']}")

def demonstrate_library_validation(validator):
    """Demonstrate library validation."""
    print("\n📚 Library Validation")
    print("=" * 50)
    
    result = validator.validate_library("test_library")
    
    stats = result["statistics"]
    print(f"Library Statistics:")
    print(f"  Total Files: {stats['total_files']}")
    print(f"  Valid Files: {stats['valid_files']}")
    print(f"  Invalid Files: {stats['invalid_files']}")
    print(f"  Total Symbols: {stats['total_symbols']}")
    print(f"  Valid Symbols: {stats['valid_symbols']}")
    print(f"  Invalid Symbols: {stats['invalid_symbols']}")
    print(f"  Overall: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    
    # Show file-level results
    print("\nFile-level Results:")
    for file_result in result["file_results"]:
        file_path = file_result.get("file_path", "unknown")
        file_stats = file_result.get("statistics", {})
        print(f"  {file_path}:")
        print(f"    Symbols: {file_stats.get('total_symbols', 0)}")
        print(f"    Valid: {file_stats.get('valid_symbols', 0)}")
        print(f"    Invalid: {file_stats.get('invalid_symbols', 0)}")
        print(f"    Status: {'✅ Valid' if file_result.get('valid', False) else '❌ Invalid'}")

def demonstrate_batch_validation(validator, valid_symbols, invalid_symbols):
    """Demonstrate batch validation."""
    print("\n📦 Batch Validation")
    print("=" * 50)
    
    # Test batch with mixed validity
    all_symbols = valid_symbols + invalid_symbols
    result = validator.validate_symbols_batch(all_symbols)
    
    stats = result["statistics"]
    print(f"Batch Statistics:")
    print(f"  Total Symbols: {stats['total_symbols']}")
    print(f"  Valid Symbols: {stats['valid_symbols']}")
    print(f"  Invalid Symbols: {stats['invalid_symbols']}")
    print(f"  Overall: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    
    # Show detailed results
    print("\nDetailed Results:")
    for symbol_result in result["results"]:
        status = "✅ Valid" if symbol_result['valid'] else "❌ Invalid"
        print(f"  {symbol_result['symbol_id']}: {status}")
        if not symbol_result['valid']:
            for error in symbol_result['errors']:
                print(f"    - {error['field_path']}: {error['message']}")

def demonstrate_error_reporting(validator, invalid_symbols):
    """Demonstrate detailed error reporting."""
    print("\n🚨 Error Reporting")
    print("=" * 50)
    
    for i, symbol in enumerate(invalid_symbols):
        print(f"\nInvalid Symbol {i+1}:")
        is_valid, errors = validator.validate_symbol(symbol)
        
        for error in errors:
            print(f"  Field: {error['field_path']}")
            print(f"  Type: {error['error_type']}")
            print(f"  Message: {error['message']}")
            print(f"  Validator: {error['validator']}")
            if error['validator_value']:
                print(f"  Expected: {error['validator_value']}")

def demonstrate_report_generation(validator, valid_symbols, invalid_symbols):
    """Demonstrate report generation."""
    print("\n📊 Report Generation")
    print("=" * 50)
    
    # Create a validation result
    all_symbols = valid_symbols + invalid_symbols
    result = validator.validate_symbols_batch(all_symbols)
    
    # Generate summary
    summary = validator.get_validation_summary(result)
    print("Validation Summary:")
    print(summary)
    
    # Export detailed report
    report_file = "validation_report.json"
    validator.export_validation_report(result, report_file)
    print(f"\n✅ Detailed report exported to: {report_file}")
    
    # Show schema information
    schema_info = validator.get_schema_info()
    print(f"\nSchema Information:")
    print(f"  Schema Path: {schema_info['schema_path']}")
    print(f"  Schema Version: {schema_info['schema_version']}")
    print(f"  Title: {schema_info['title']}")
    print(f"  Required Fields: {', '.join(schema_info['required_fields'])}")
    print(f"  Properties: {', '.join(schema_info['properties'])}")

def cleanup():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    cleanup_files = [
        "valid_symbols.json",
        "invalid_symbols.json",
        "mixed_symbols.json",
        "single_symbol.json",
        "validation_report.json"
    ]
    
    for file in cleanup_files:
        try:
            Path(file).unlink(missing_ok=True)
            print(f"  ✅ Removed {file}")
        except Exception as e:
            print(f"  ❌ Failed to remove {file}: {e}")
    
    # Remove test library directory
    try:
        import shutil
        shutil.rmtree("test_library", ignore_errors=True)
        print("  ✅ Removed test_library/")
    except Exception as e:
        print(f"  ❌ Failed to remove test_library/: {e}")

def main():
    """Main function to demonstrate the schema validator service."""
    print("Arxos Symbol Schema Validator Service - Example Usage")
    print("=" * 60)
    
    try:
        # Initialize validator
        print("Initializing SymbolSchemaValidator...")
        validator = SymbolSchemaValidator()
        print("✅ Validator initialized successfully")
        
        # Create test data
        valid_symbols, invalid_symbols = create_test_data()
        create_test_files(valid_symbols, invalid_symbols)
        create_test_library(valid_symbols, invalid_symbols)
        
        # Demonstrate various validation features
        demonstrate_individual_validation(validator, valid_symbols, invalid_symbols)
        demonstrate_file_validation(validator)
        demonstrate_library_validation(validator)
        demonstrate_batch_validation(validator, valid_symbols, invalid_symbols)
        demonstrate_error_reporting(validator, invalid_symbols)
        demonstrate_report_generation(validator, valid_symbols, invalid_symbols)
        
        print("\n✅ Schema validator example completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Schema file not found: {e}")
        print("Please ensure the schema file exists at: arx-symbol-library/schemas/symbol.schema.json")
    except Exception as e:
        print(f"❌ Error during validation example: {e}")
    
    finally:
        cleanup()

if __name__ == "__main__":
    main() 