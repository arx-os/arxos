"""
Symbol Schema Validator Service

This module provides comprehensive validation services for SVG-BIM symbols
against the JSON schema, including individual symbol validation, file validation,
and library-wide validation with detailed error reporting.

Author: Arxos Development Team
Date: 2024
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import jsonschema
from jsonschema import ValidationError

# Setup logging
logger = logging.getLogger(__name__)

class SymbolSchemaValidator:
    """
    Comprehensive validator for SVG-BIM symbols against JSON schema.
    
    Provides validation for individual symbols, files, and entire libraries
    with detailed error reporting and statistics.
    """
    
    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        """
        Initialize the schema validator.
        
        Args:
            schema_path: Path to the JSON schema file. If None, uses default path.
        """
        if schema_path is None:
            # Default path relative to this file
            base = Path(__file__).parent.parent.parent
            schema_path = base / "arx-symbol-library" / "schemas" / "symbol.schema.json"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)
        
        logger.info(f"Initialized SymbolSchemaValidator with schema: {self.schema_path}")
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load and parse the JSON schema file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            logger.debug(f"Loaded schema from {self.schema_path}")
            return schema
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file {self.schema_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading schema from {self.schema_path}: {e}")
    
    def _format_validation_error(self, error: ValidationError) -> Dict[str, Any]:
        """
        Format a validation error into a detailed error report.
        
        Args:
            error: The ValidationError object from jsonschema
            
        Returns:
            Dict containing formatted error information
        """
        # Build the field path
        path_parts = []
        for part in error.path:
            path_parts.append(str(part))
        field_path = ".".join(path_parts) if path_parts else "root"
        
        # Determine error type and provide helpful messages
        error_type = "validation_error"
        if "required" in error.message.lower():
            error_type = "missing_required_field"
        elif "pattern" in error.message.lower():
            error_type = "invalid_pattern"
        elif "enum" in error.message.lower():
            error_type = "invalid_enum_value"
        elif "minLength" in error.message.lower():
            error_type = "string_too_short"
        elif "maxLength" in error.message.lower():
            error_type = "string_too_long"
        elif "type" in error.message.lower():
            error_type = "invalid_type"
        
        return {
            "field_path": field_path,
            "error_type": error_type,
            "message": error.message,
            "schema_path": list(error.schema_path),
            "validator": error.validator,
            "validator_value": error.validator_value
        }
    
    def validate_symbol(self, symbol_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a single symbol against the JSON schema.
        
        Args:
            symbol_data: Dictionary containing symbol data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            errors = list(self.validator.iter_errors(symbol_data))
            
            if not errors:
                return True, []
            
            # Format all errors
            formatted_errors = [self._format_validation_error(error) for error in errors]
            
            # Sort errors by field path for consistent reporting
            formatted_errors.sort(key=lambda x: x["field_path"])
            
            return False, formatted_errors
            
        except Exception as e:
            logger.error(f"Unexpected error during symbol validation: {e}")
            return False, [{
                "field_path": "unknown",
                "error_type": "validation_exception",
                "message": f"Validation failed with exception: {str(e)}",
                "schema_path": [],
                "validator": "unknown",
                "validator_value": None
            }]
    
    def validate_symbol_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate symbols from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing symbol(s)
            
        Returns:
            Dictionary with validation results and statistics
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "valid": False,
                "errors": [{"message": f"File not found: {file_path}"}],
                "statistics": {
                    "total_symbols": 0,
                    "valid_symbols": 0,
                    "invalid_symbols": 0
                }
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine if it's a single symbol or array
            if isinstance(data, dict):
                symbols = [data]
                is_single = True
            elif isinstance(data, list):
                symbols = data
                is_single = False
            else:
                return {
                    "valid": False,
                    "errors": [{"message": "File must contain a symbol object or array of symbols"}],
                    "statistics": {
                        "total_symbols": 0,
                        "valid_symbols": 0,
                        "invalid_symbols": 0
                    }
                }
            
            # Validate each symbol
            results = []
            valid_count = 0
            invalid_count = 0
            
            for i, symbol in enumerate(symbols):
                is_valid, errors = self.validate_symbol(symbol)
                
                result = {
                    "index": i,
                    "symbol_id": symbol.get("id", f"symbol_{i}"),
                    "valid": is_valid,
                    "errors": errors
                }
                
                results.append(result)
                
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
            
            return {
                "valid": invalid_count == 0,
                "file_path": str(file_path),
                "is_single_symbol": is_single,
                "results": results,
                "statistics": {
                    "total_symbols": len(symbols),
                    "valid_symbols": valid_count,
                    "invalid_symbols": invalid_count
                }
            }
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "file_path": str(file_path),
                "errors": [{"message": f"Invalid JSON in file: {str(e)}"}],
                "statistics": {
                    "total_symbols": 0,
                    "valid_symbols": 0,
                    "invalid_symbols": 0
                }
            }
        except Exception as e:
            return {
                "valid": False,
                "file_path": str(file_path),
                "errors": [{"message": f"Error reading file: {str(e)}"}],
                "statistics": {
                    "total_symbols": 0,
                    "valid_symbols": 0,
                    "invalid_symbols": 0
                }
            }
    
    def validate_library(self, library_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate all symbols in a symbol library.
        
        Args:
            library_path: Path to the symbol library directory
            
        Returns:
            Dictionary with comprehensive validation results
        """
        library_path = Path(library_path)
        
        if not library_path.exists():
            return {
                "valid": False,
                "errors": [{"message": f"Library path not found: {library_path}"}],
                "statistics": {
                    "total_files": 0,
                    "total_symbols": 0,
                    "valid_symbols": 0,
                    "invalid_symbols": 0,
                    "valid_files": 0,
                    "invalid_files": 0
                }
            }
        
        # Find all JSON files in the library
        json_files = []
        for root, dirs, files in os.walk(library_path):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(Path(root) / file)
        
        # Validate each file
        file_results = []
        total_symbols = 0
        valid_symbols = 0
        invalid_symbols = 0
        valid_files = 0
        invalid_files = 0
        
        for file_path in json_files:
            file_result = self.validate_symbol_file(file_path)
            file_results.append(file_result)
            
            stats = file_result.get("statistics", {})
            total_symbols += stats.get("total_symbols", 0)
            valid_symbols += stats.get("valid_symbols", 0)
            invalid_symbols += stats.get("invalid_symbols", 0)
            
            if file_result.get("valid", False):
                valid_files += 1
            else:
                invalid_files += 1
        
        # Generate summary
        overall_valid = invalid_symbols == 0
        
        return {
            "valid": overall_valid,
            "library_path": str(library_path),
            "file_results": file_results,
            "statistics": {
                "total_files": len(json_files),
                "total_symbols": total_symbols,
                "valid_symbols": valid_symbols,
                "invalid_symbols": invalid_symbols,
                "valid_files": valid_files,
                "invalid_files": invalid_files
            },
            "summary": {
                "validation_timestamp": datetime.now().isoformat(),
                "schema_version": self.schema.get("$schema", "unknown"),
                "overall_status": "valid" if overall_valid else "invalid"
            }
        }
    
    def validate_symbols_batch(self, symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of symbols with detailed reporting.
        
        Args:
            symbols: List of symbol dictionaries
            
        Returns:
            Dictionary with batch validation results
        """
        results = []
        valid_count = 0
        invalid_count = 0
        
        for i, symbol in enumerate(symbols):
            is_valid, errors = self.validate_symbol(symbol)
            
            result = {
                "index": i,
                "symbol_id": symbol.get("id", f"symbol_{i}"),
                "valid": is_valid,
                "errors": errors
            }
            
            results.append(result)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        return {
            "valid": invalid_count == 0,
            "results": results,
            "statistics": {
                "total_symbols": len(symbols),
                "valid_symbols": valid_count,
                "invalid_symbols": invalid_count
            }
        }
    
    def validate_symbols(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a list of symbols and return a list of results for each symbol.
        Each result is a dict with 'valid', 'errors', and 'symbol'.
        """
        results = []
        for symbol in symbols:
            is_valid, errors = self.validate_symbol(symbol)
            results.append({
                "valid": is_valid,
                "errors": errors,
                "symbol": symbol
            })
        return results
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of validation results.
        
        Args:
            validation_result: Result from any validation method
            
        Returns:
            Formatted summary string
        """
        stats = validation_result.get("statistics", {})
        
        if "total_files" in stats:
            # Library validation
            summary = f"Library Validation Summary:\n"
            summary += f"  Total Files: {stats.get('total_files', 0)}\n"
            summary += f"  Valid Files: {stats.get('valid_files', 0)}\n"
            summary += f"  Invalid Files: {stats.get('invalid_files', 0)}\n"
            summary += f"  Total Symbols: {stats.get('total_symbols', 0)}\n"
            summary += f"  Valid Symbols: {stats.get('valid_symbols', 0)}\n"
            summary += f"  Invalid Symbols: {stats.get('invalid_symbols', 0)}\n"
        else:
            # File or batch validation
            summary = f"Validation Summary:\n"
            summary += f"  Total Symbols: {stats.get('total_symbols', 0)}\n"
            summary += f"  Valid Symbols: {stats.get('valid_symbols', 0)}\n"
            summary += f"  Invalid Symbols: {stats.get('invalid_symbols', 0)}\n"
        
        summary += f"  Overall Status: {'✅ Valid' if validation_result.get('valid', False) else '❌ Invalid'}"
        
        return summary
    
    def export_validation_report(self, validation_result: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """
        Export validation results to a JSON file.
        
        Args:
            validation_result: Result from any validation method
            output_path: Path to save the report
        """
        output_path = Path(output_path)
        
        # Add metadata to the report
        report = {
            "validation_report": {
                "generated_at": datetime.now().isoformat(),
                "schema_path": str(self.schema_path),
                "schema_version": self.schema.get("$schema", "unknown")
            },
            "results": validation_result
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validation report exported to: {output_path}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded schema.
        
        Returns:
            Dictionary with schema information
        """
        return {
            "schema_path": str(self.schema_path),
            "schema_version": self.schema.get("$schema", "unknown"),
            "title": self.schema.get("title", "Unknown"),
            "description": self.schema.get("description", ""),
            "required_fields": self.schema.get("required", []),
            "properties": list(self.schema.get("properties", {}).keys())
        } 