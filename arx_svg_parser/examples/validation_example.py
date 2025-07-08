#!/usr/bin/env python3
"""
Schema Validation Example

This script demonstrates how to use the schema validation
in both CLI and API contexts.

Author: Arxos Development Team
Date: 2024
"""

import json
import subprocess
import sys
from pathlib import Path

def create_test_symbols():
    """Create test symbols for validation examples."""
    
    # Valid symbol
    valid_symbol = {
        "id": "test_valid_symbol",
        "name": "Valid Test Symbol",
        "system": "electrical",
        "description": "A valid test symbol",
        "svg": {
            "content": "<svg width='50' height='50'><circle cx='25' cy='25' r='20' fill='blue'/></svg>"
        },
        "properties": {
            "voltage": "220V",
            "current": "10A"
        },
        "connections": [
            {
                "id": "input_1",
                "type": "input",
                "x": 0,
                "y": 25,
                "label": "Input 1"
            },
            {
                "id": "output_1",
                "type": "output",
                "x": 50,
                "y": 25,
                "label": "Output 1"
            }
        ]
    }
    
    # Invalid symbols
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
        }
    ]
    
    # Save to files
    with open("valid_symbol.json", "w") as f:
        json.dump(valid_symbol, f, indent=2)
    
    with open("invalid_symbols.json", "w") as f:
        json.dump(invalid_symbols, f, indent=2)
    
    with open("mixed_symbols.json", "w") as f:
        json.dump([valid_symbol] + invalid_symbols, f, indent=2)
    
    print("✅ Created test symbol files:")
    print("  - valid_symbol.json")
    print("  - invalid_symbols.json")
    print("  - mixed_symbols.json")

def test_cli_validation():
    """Test CLI validation commands."""
    print("\n🔧 Testing CLI Validation")
    print("=" * 50)
    
    commands = [
        ("python cmd/symbol_manager_cli.py validate --file valid_symbol.json", "Validate single valid symbol"),
        ("python cmd/symbol_manager_cli.py validate --file invalid_symbols.json", "Validate invalid symbols"),
        ("python cmd/symbol_manager_cli.py validate --file mixed_symbols.json", "Validate mixed symbols"),
        ("python cmd/symbol_manager_cli.py validate --file valid_symbol.json --output validation_results.json", "Validate with output file")
    ]
    
    for command, description in commands:
        print(f"\n{description}")
        print(f"Command: {command}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            if result.stdout:
                print("Output:")
                print(result.stdout)
            
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            
            print(f"Exit code: {result.returncode}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def test_api_validation():
    """Test API validation endpoint (requires running server)."""
    print("\n🌐 Testing API Validation")
    print("=" * 50)
    
    # Example API calls (would need server running)
    api_examples = [
        {
            "name": "Valid Symbol API Test",
            "method": "POST",
            "endpoint": "/api/v1/symbols/validate",
            "data": {
                "symbols": [
                    {
                        "id": "api_test_symbol",
                        "name": "API Test Symbol",
                        "system": "electrical",
                        "svg": {"content": "<svg></svg>"}
                    }
                ]
            }
        },
        {
            "name": "Invalid Symbol API Test",
            "method": "POST",
            "endpoint": "/api/v1/symbols/validate",
            "data": {
                "symbols": [
                    {
                        "id": "Invalid-ID!",
                        "name": "Invalid Symbol",
                        "system": "electrical",
                        "svg": {"content": "<svg></svg>"}
                    }
                ]
            }
        }
    ]
    
    print("API validation examples (requires running server):")
    for example in api_examples:
        print(f"\n{example['name']}")
        print(f"Method: {example['method']}")
        print(f"Endpoint: {example['endpoint']}")
        print(f"Data: {json.dumps(example['data'], indent=2)}")

def test_integration():
    """Test validation integration in create/update operations."""
    print("\n🔗 Testing Integration")
    print("=" * 50)
    
    # Test create with valid symbol
    print("\n1. Creating valid symbol:")
    try:
        result = subprocess.run([
            "python", "cmd/symbol_manager_cli.py", "create",
            "--file", "valid_symbol.json"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Valid symbol created successfully")
        else:
            print("❌ Failed to create valid symbol")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test create with invalid symbol
    print("\n2. Attempting to create invalid symbol:")
    try:
        result = subprocess.run([
            "python", "cmd/symbol_manager_cli.py", "create",
            "--id", "Invalid-ID!",
            "--name", "Invalid Symbol",
            "--system", "electrical"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode != 0:
            print("✅ Invalid symbol correctly rejected")
        else:
            print("❌ Invalid symbol was accepted")
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    cleanup_files = [
        "valid_symbol.json",
        "invalid_symbols.json", 
        "mixed_symbols.json",
        "validation_results.json"
    ]
    
    for file in cleanup_files:
        try:
            Path(file).unlink(missing_ok=True)
            print(f"  ✅ Removed {file}")
        except Exception as e:
            print(f"  ❌ Failed to remove {file}: {e}")

def main():
    """Main function to demonstrate validation."""
    print("Arxos Schema Validation - Example Usage")
    print("=" * 50)
    
    # Create test files
    create_test_symbols()
    
    # Test CLI validation
    test_cli_validation()
    
    # Test API validation examples
    test_api_validation()
    
    # Test integration
    test_integration()
    
    # Cleanup
    cleanup()
    
    print("\n✅ Validation example completed!")

if __name__ == "__main__":
    main() 