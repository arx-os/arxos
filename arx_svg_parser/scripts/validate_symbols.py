#!/usr/bin/env python3
"""
JSON Schema Validation Script for Symbol Files

This script validates all JSON symbol files against the defined schema.
Used in CI/CD pipelines to ensure symbol file compliance.

Usage:
    python validate_symbols.py [--schema-path PATH] [--symbols-path PATH] [--verbose]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import jsonschema
from jsonschema import ValidationError


class SymbolValidator:
    """Validates symbol files against JSON schema."""
    
    def __init__(self, schema_path: str, symbols_path: str, verbose: bool = False):
        self.schema_path = Path(schema_path)
        self.symbols_path = Path(symbols_path)
        self.verbose = verbose
        self.schema = None
        self.validation_errors = []
        
    def load_schema(self) -> bool:
        """Load and validate the JSON schema."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            
            # Validate the schema itself
            jsonschema.Draft7Validator.check_schema(self.schema)
            
            if self.verbose:
                print(f"✓ Schema loaded from: {self.schema_path}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Schema file not found: {self.schema_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in schema file: {e}")
            return False
        except jsonschema.SchemaError as e:
            print(f"❌ Invalid schema: {e}")
            return False
    
    def find_symbol_files(self) -> List[Path]:
        """Find all JSON symbol files recursively."""
        symbol_files = []
        
        if not self.symbols_path.exists():
            print(f"❌ Symbols directory not found: {self.symbols_path}")
            return symbol_files
        
        for file_path in self.symbols_path.rglob("*.json"):
            # Skip schema files and index files
            if (file_path.name in ["symbol.schema.json", "index.json", "categories.json", "systems.json"] or
                "schemas" in file_path.parts):
                continue
            symbol_files.append(file_path)
        
        if self.verbose:
            print(f"Found {len(symbol_files)} symbol files to validate")
        
        return symbol_files
    
    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate a single symbol file against the schema."""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                symbol_data = json.load(f)
            
            # Validate against schema
            validator = jsonschema.Draft7Validator(self.schema)
            validation_errors = list(validator.iter_errors(symbol_data))
            
            if validation_errors:
                for error in validation_errors:
                    error_path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                    errors.append(f"  {error_path}: {error.message}")
            
            return len(errors) == 0, errors
            
        except FileNotFoundError:
            errors.append("  File not found")
            return False, errors
        except json.JSONDecodeError as e:
            errors.append(f"  Invalid JSON: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"  Unexpected error: {e}")
            return False, errors
    
    def validate_all_files(self) -> bool:
        """Validate all symbol files and return overall success status."""
        if not self.load_schema():
            return False
        
        symbol_files = self.find_symbol_files()
        if not symbol_files:
            print("❌ No symbol files found to validate")
            return False
        
        total_files = len(symbol_files)
        valid_files = 0
        invalid_files = 0
        
        print(f"Validating {total_files} symbol files...")
        print("-" * 50)
        
        for file_path in symbol_files:
            relative_path = file_path.relative_to(self.symbols_path)
            is_valid, errors = self.validate_file(file_path)
            
            if is_valid:
                valid_files += 1
                if self.verbose:
                    print(f"✓ {relative_path}")
            else:
                invalid_files += 1
                print(f"❌ {relative_path}")
                for error in errors:
                    print(error)
                print()
        
        print("-" * 50)
        print(f"Validation Summary:")
        print(f"  Total files: {total_files}")
        print(f"  Valid files: {valid_files}")
        print(f"  Invalid files: {invalid_files}")
        
        if invalid_files > 0:
            print(f"\n❌ Validation failed: {invalid_files} file(s) have errors")
            return False
        else:
            print(f"\n✓ All {total_files} symbol files are valid!")
            return True
    
    def generate_report(self, output_path: str = None) -> None:
        """Generate a detailed validation report."""
        if not self.load_schema():
            return
        
        symbol_files = self.find_symbol_files()
        report = {
            "validation_timestamp": str(Path().cwd()),
            "schema_path": str(self.schema_path),
            "symbols_path": str(self.symbols_path),
            "total_files": len(symbol_files),
            "valid_files": [],
            "invalid_files": []
        }
        
        for file_path in symbol_files:
            relative_path = str(file_path.relative_to(self.symbols_path))
            is_valid, errors = self.validate_file(file_path)
            
            if is_valid:
                report["valid_files"].append(relative_path)
            else:
                report["invalid_files"].append({
                    "file": relative_path,
                    "errors": errors
                })
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"Validation report saved to: {output_path}")
        else:
            print(json.dumps(report, indent=2))


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Validate JSON symbol files against schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_symbols.py
  python validate_symbols.py --verbose
  python validate_symbols.py --schema-path ../arx-symbol-library/schemas/symbol.schema.json
  python validate_symbols.py --report validation_report.json
        """
    )
    
    parser.add_argument(
        "--schema-path",
        default="../arx-symbol-library/schemas/symbol.schema.json",
        help="Path to JSON schema file (default: ../arx-symbol-library/schemas/symbol.schema.json)"
    )
    
    parser.add_argument(
        "--symbols-path",
        default="../arx-symbol-library",
        help="Path to symbols directory (default: ../arx-symbol-library)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--report",
        help="Generate detailed validation report to specified file"
    )
    
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if validation fails (for CI/CD)"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    schema_path = Path(args.schema_path)
    symbols_path = Path(args.symbols_path)
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    
    if not symbols_path.exists():
        print(f"❌ Symbols directory not found: {symbols_path}")
        sys.exit(1)
    
    # Create validator and run validation
    validator = SymbolValidator(
        schema_path=str(schema_path),
        symbols_path=str(symbols_path),
        verbose=args.verbose
    )
    
    success = validator.validate_all_files()
    
    # Generate report if requested
    if args.report:
        validator.generate_report(args.report)
    
    # Exit with appropriate code
    if not success and args.exit_code:
        sys.exit(1)
    elif not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 