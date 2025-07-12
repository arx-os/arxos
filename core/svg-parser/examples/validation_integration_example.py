"""
Validation Integration Example

This script demonstrates the comprehensive validation integration
across all symbol management services including SymbolManager, JSONSymbolLibrary,
and API endpoints.

Author: Arxos Development Team
Date: 2024
"""

import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any

from services.symbol_manager import SymbolManager
from services.json_symbol_library import JSONSymbolLibrary
from services.symbol_schema_validator import SymbolSchemaValidator


def create_temp_library() -> str:
    """Create a temporary symbol library for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create library structure
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
    
    return temp_dir


def create_sample_symbols() -> List[Dict[str, Any]]:
    """Create sample symbols for testing validation."""
    return [
        {
            "id": "valve_001",
            "name": "Control Valve",
            "system": "mechanical",
            "svg": {
                "content": "<svg><circle cx='50' cy='50' r='25' fill='blue'/></svg>",
                "width": 100,
                "height": 100
            },
            "description": "A control valve symbol",
            "category": "valve",
            "properties": {"type": "control", "size": "2inch"},
            "connections": [{"x": 50, "y": 25}, {"x": 50, "y": 75}],
            "tags": ["valve", "control", "mechanical"],
            "metadata": {"created_by": "example"}
        },
        {
            "id": "pump_001",
            "name": "Centrifugal Pump",
            "system": "mechanical",
            "svg": {
                "content": "<svg><circle cx='50' cy='50' r='30' fill='green'/></svg>",
                "width": 100,
                "height": 100
            },
            "description": "A centrifugal pump symbol",
            "category": "pump",
            "properties": {"type": "centrifugal", "power": "10hp"},
            "connections": [{"x": 50, "y": 20}, {"x": 50, "y": 80}],
            "tags": ["pump", "mechanical"],
            "metadata": {"created_by": "example"}
        },
        {
            "id": "invalid_symbol",
            "name": "",  # Invalid: empty name
            "system": "invalid_system",  # Invalid: not in enum
            "svg": {
                "content": "",  # Invalid: empty content
                "width": "not_a_number"  # Invalid: should be number
            }
        }
    ]


def demonstrate_symbol_manager_validation():
    """Demonstrate validation integration in SymbolManager."""
    print("\n=== SymbolManager Validation Integration ===")
    
    temp_library = create_temp_library()
    manager = SymbolManager(temp_library)
    symbols = create_sample_symbols()
    
    try:
        # Test single symbol validation
        print("1. Testing single symbol validation...")
        valid_symbol = symbols[0]
        invalid_symbol = symbols[2]
        
        # Validate valid symbol
        result = manager.validate_symbol_with_details(valid_symbol)
        print(f"   Valid symbol validation: {result['is_valid']}")
        if not result['is_valid']:
            print(f"   Errors: {result['errors']}")
        
        # Validate invalid symbol
        result = manager.validate_symbol_with_details(invalid_symbol)
        print(f"   Invalid symbol validation: {result['is_valid']}")
        if not result['is_valid']:
            print(f"   Errors: {result['errors']}")
        
        # Test batch validation
        print("\n2. Testing batch validation...")
        batch_result = manager.validate_batch_with_details(symbols)
        print(f"   Total symbols: {batch_result['total_symbols']}")
        print(f"   Valid symbols: {batch_result['valid_symbols']}")
        print(f"   Invalid symbols: {batch_result['invalid_symbols']}")
        
        # Test bulk create with validation
        print("\n3. Testing bulk create with validation...")
        created_symbols = manager.bulk_create_symbols(symbols)
        print(f"   Successfully created: {len(created_symbols)} symbols")
        
        # Test bulk update with validation
        print("\n4. Testing bulk update with validation...")
        updates = [
            {"id": "valve_001", "description": "Updated control valve"},
            {"id": "nonexistent", "description": "This should fail"}
        ]
        updated_symbols = manager.bulk_update_symbols(updates)
        print(f"   Successfully updated: {len(updated_symbols)} symbols")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_library)


def demonstrate_json_symbol_library_validation():
    """Demonstrate validation integration in JSONSymbolLibrary."""
    print("\n=== JSONSymbolLibrary Validation Integration ===")
    
    temp_library = create_temp_library()
    library = JSONSymbolLibrary(temp_library)
    symbols = create_sample_symbols()
    
    try:
        # Test validation method
        print("1. Testing symbol validation...")
        valid_symbol = symbols[0]
        invalid_symbol = symbols[2]
        
        print(f"   Valid symbol validation: {library.validate_symbol(valid_symbol)}")
        print(f"   Invalid symbol validation: {library.validate_symbol(invalid_symbol)}")
        
        # Test file loading with validation
        print("\n2. Testing file loading with validation...")
        
        # Create valid symbol file
        valid_file = Path(temp_library) / "symbols" / "mechanical" / "valid_symbol.json"
        with open(valid_file, 'w') as f:
            json.dump(valid_symbol, f)
        
        # Create invalid symbol file
        invalid_file = Path(temp_library) / "symbols" / "mechanical" / "invalid_symbol.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_symbol, f)
        
        # Load symbols (should only load valid ones)
        loaded_symbols = library.load_all_symbols()
        print(f"   Loaded symbols: {len(loaded_symbols)}")
        print(f"   Symbol IDs: {list(loaded_symbols.keys())}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_library)


def demonstrate_schema_validator_features():
    """Demonstrate comprehensive schema validator features."""
    print("\n=== Schema Validator Features ===")
    
    validator = SymbolSchemaValidator()
    symbols = create_sample_symbols()
    
    # Test single symbol validation
    print("1. Testing single symbol validation...")
    valid_symbol = symbols[0]
    is_valid, errors = validator.validate_symbol(valid_symbol)
    print(f"   Valid symbol: {is_valid}")
    if not is_valid:
        print(f"   Errors: {errors}")
    
    # Test batch validation
    print("\n2. Testing batch validation...")
    results = validator.validate_symbols(symbols)
    valid_count = sum(1 for r in results if r['valid'])
    print(f"   Valid symbols: {valid_count}/{len(results)}")
    
    # Test file validation
    print("\n3. Testing file validation...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(symbols, f)
        file_path = f.name
    
    try:
        is_valid, errors = validator.validate_file(file_path)
        print(f"   File validation: {is_valid}")
        if not is_valid:
            print(f"   Errors: {errors}")
    finally:
        os.unlink(file_path)
    
    # Test library validation
    print("\n4. Testing library validation...")
    temp_library = create_temp_library()
    try:
        # Create some symbol files
        symbols_dir = Path(temp_library) / "symbols" / "mechanical"
        for i, symbol in enumerate(symbols[:2]):  # Use first 2 valid symbols
            with open(symbols_dir / f"symbol_{i}.json", 'w') as f:
                json.dump(symbol, f)
        
        is_valid, errors = validator.validate_library(temp_library)
        print(f"   Library validation: {is_valid}")
        if not is_valid:
            print(f"   Errors: {errors}")
    finally:
        import shutil
        shutil.rmtree(temp_library)
    
    # Test report generation
    print("\n5. Testing report generation...")
    report = validator.generate_validation_report(symbols)
    print(f"   Report summary: {report['summary']}")
    
    # Test schema info
    print("\n6. Testing schema information...")
    schema_info = validator.get_schema_info()
    print(f"   Schema version: {schema_info['schema_version']}")
    print(f"   Required fields: {schema_info['required_fields']}")


def demonstrate_validation_error_handling():
    """Demonstrate comprehensive error handling in validation."""
    print("\n=== Validation Error Handling ===")
    
    validator = SymbolSchemaValidator()
    
    # Test various error scenarios
    error_cases = [
        None,  # None data
        "not_a_dict",  # Non-dict data
        {},  # Empty dict
        {"id": "test"},  # Missing required fields
        {"id": "test", "name": "", "system": "mechanical", "svg": {"content": ""}},  # Invalid data
        {"id": "test", "name": "Test", "system": "invalid_system", "svg": {"content": "<svg></svg>"}},  # Invalid system
    ]
    
    for i, test_case in enumerate(error_cases):
        print(f"\n{i+1}. Testing error case: {type(test_case).__name__}")
        try:
            is_valid, errors = validator.validate_symbol(test_case)
            print(f"   Valid: {is_valid}")
            if not is_valid:
                print(f"   Errors: {errors}")
        except Exception as e:
            print(f"   Exception: {e}")


def demonstrate_validation_performance():
    """Demonstrate validation performance with large datasets."""
    print("\n=== Validation Performance ===")
    
    validator = SymbolSchemaValidator()
    manager = SymbolManager(create_temp_library())
    
    # Create large dataset
    large_dataset = []
    for i in range(100):
        symbol = {
            "id": f"symbol_{i:03d}",
            "name": f"Symbol {i}",
            "system": "mechanical" if i % 2 == 0 else "electrical",
            "svg": {
                "content": f"<svg><circle cx='50' cy='50' r='{25 + i % 10}'/></svg>",
                "width": 100,
                "height": 100
            },
            "description": f"Symbol {i} description",
            "category": "test",
            "properties": {"index": i},
            "connections": [],
            "tags": ["test", f"symbol_{i}"],
            "metadata": {"created_by": "performance_test"}
        }
        large_dataset.append(symbol)
    
    # Add some invalid symbols
    for i in range(10):
        invalid_symbol = {
            "id": f"invalid_{i}",
            "name": "",  # Invalid
            "system": "invalid_system",  # Invalid
            "svg": {"content": ""}  # Invalid
        }
        large_dataset.append(invalid_symbol)
    
    print(f"Testing with {len(large_dataset)} symbols...")
    
    # Test validator performance
    import time
    start_time = time.time()
    results = validator.validate_symbols(large_dataset)
    validator_time = time.time() - start_time
    
    valid_count = sum(1 for r in results if r['valid'])
    print(f"   Validator: {valid_count}/{len(results)} valid in {validator_time:.3f}s")
    
    # Test manager performance
    start_time = time.time()
    batch_result = manager.validate_batch_with_details(large_dataset)
    manager_time = time.time() - start_time
    
    print(f"   Manager: {batch_result['valid_symbols']}/{batch_result['total_symbols']} valid in {manager_time:.3f}s")


def main():
    """Run all validation integration demonstrations."""
    print("Validation Integration Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_symbol_manager_validation()
        demonstrate_json_symbol_library_validation()
        demonstrate_schema_validator_features()
        demonstrate_validation_error_handling()
        demonstrate_validation_performance()
        
        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 