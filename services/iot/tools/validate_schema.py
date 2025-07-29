#!/usr/bin/env python3
"""
ArxHAL Schema Validator

CLI tool for validating ArxHAL schemas and ArxDriver configurations.
This tool ensures that hardware abstraction layer definitions are properly formatted
and compatible with the Arxos platform.

Usage:
    python validate_schema.py <schema_file>
    python validate_schema.py --validate-all
    python validate_schema.py --generate-example
"""

import json
import yaml
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from jsonschema import validate


class ArxHALValidator:
    """Validator for ArxHAL schemas and ArxDriver configurations."""
    
    def __init__(self):
        self.arxhal_schema = self._load_arxhal_schema()
        self.arxdriver_schema = self._load_arxdriver_schema()
        self.validation_errors = []
        self.validation_warnings = []
    
    def _load_arxhal_schema(self) -> Dict[str, Any]:
        """Load the ArxHAL JSON schema."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["object_type", "version", "description", "inputs", "outputs"],
            "properties": {
                "$schema": {"type": "string"},
                "object_type": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "device_id": {"type": "string"},
                "manufacturer": {"type": "string"},
                "model": {"type": "string"},
                "inputs": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["unit", "type", "description"],
                        "properties": {
                            "unit": {"type": "string"},
                            "type": {"type": "string", "enum": ["float", "int", "boolean"]},
                            "description": {"type": "string"},
                            "range": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                            "accuracy": {"type": "string"},
                            "protocol_mapping": {"type": "object"}
                        }
                    }
                },
                "outputs": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["type", "description"],
                        "properties": {
                            "unit": {"type": "string"},
                            "type": {"type": "string", "enum": ["float", "int", "boolean"]},
                            "description": {"type": "string"},
                            "range": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                            "default": {"oneOf": [{"type": "number"}, {"type": "boolean"}]},
                            "protocol_mapping": {"type": "object"}
                        }
                    }
                },
                "behavior_profile": {"type": "string"},
                "alarms": {"type": "object"},
                "metadata": {"type": "object"}
            }
        }
    
    def _load_arxdriver_schema(self) -> Dict[str, Any]:
        """Load the ArxDriver YAML schema."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "type", "object_type", "protocol", "status", "source", "version"],
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string", "const": "driver"},
                "object_type": {"type": "string"},
                "protocol": {"type": "string"},
                "status": {"type": "string", "enum": ["draft", "published", "deprecated"]},
                "source": {"type": "string", "enum": ["community", "vendor", "arxos"]},
                "version": {"type": "string"},
                "shares": {"type": "array"},
                "linked_hardware": {"type": "object"},
                "register_map": {"type": "object"},
                "communication": {"type": "object"},
                "fault_handling": {"type": "object"},
                "validation": {"type": "object"},
                "mapped_to": {"type": "string"}
            }
        }
    
    def validate_arxhal_schema(self, file_path: str) -> bool:
        """Validate an ArxHAL schema file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate against JSON schema
            validate(instance=data, schema=self.arxhal_schema)
            
            # Additional business logic validation
            self._validate_arxhal_business_logic(data, file_path)
            
            if not self.validation_errors:
                print(f"✅ ArxHAL schema '{file_path}' is valid")
                return True
            else:
                print(f"❌ ArxHAL schema '{file_path}' has validation errors:")
                for error in self.validation_errors:
                    print(f"  - {error}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON syntax error in '{file_path}': {e}")
            return False
        except jsonschema.exceptions.ValidationError as e:
            print(f"❌ Schema validation error in '{file_path}': {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error validating '{file_path}': {e}")
            return False
    
    def validate_arxdriver_config(self, file_path: str) -> bool:
        """Validate an ArxDriver configuration file."""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate against YAML schema
            validate(instance=data, schema=self.arxdriver_schema)
            
            # Additional business logic validation
            self._validate_arxdriver_business_logic(data, file_path)
            
            if not self.validation_errors:
                print(f"✅ ArxDriver config '{file_path}' is valid")
                return True
            else:
                print(f"❌ ArxDriver config '{file_path}' has validation errors:")
                for error in self.validation_errors:
                    print(f"  - {error}")
                return False
                
        except yaml.YAMLError as e:
            print(f"❌ YAML syntax error in '{file_path}': {e}")
            return False
        except jsonschema.exceptions.ValidationError as e:
            print(f"❌ Schema validation error in '{file_path}': {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error validating '{file_path}': {e}")
            return False
    
    def _validate_arxhal_business_logic(self, data: Dict[str, Any], file_path: str):
        """Validate ArxHAL business logic rules."""
        # Check for required fields
        required_fields = ["object_type", "version", "description", "inputs", "outputs"]
        for field in required_fields:
            if field not in data:
                self.validation_errors.append(f"Missing required field: {field}")
        
        # Validate object_type format
        if "object_type" in data:
            object_type = data["object_type"]
            if not isinstance(object_type, str) or len(object_type) < 2:
                self.validation_errors.append("object_type must be a non-empty string")
        
        # Validate version format
        if "version" in data:
            version = data["version"]
            if not isinstance(version, str) or not version.count('.') == 2:
                self.validation_errors.append("version must be in format X.Y.Z")
        
        # Validate inputs and outputs
        for io_type in ["inputs", "outputs"]:
            if io_type in data:
                io_data = data[io_type]
                if not isinstance(io_data, dict):
                    self.validation_errors.append(f"{io_type} must be an object")
                else:
                    for field_name, field_def in io_data.items():
                        if not isinstance(field_def, dict):
                            self.validation_errors.append(f"{io_type}.{field_name} must be an object")
                        else:
                            # Validate field definition
                            if "type" not in field_def:
                                self.validation_errors.append(f"{io_type}.{field_name} missing 'type' field")
                            elif field_def["type"] not in ["float", "int", "boolean"]:
                                self.validation_errors.append(f"{io_type}.{field_name} invalid type: {field_def['type']}")
                            
                            # Validate range if present
                            if "range" in field_def:
                                range_val = field_def["range"]
                                if not isinstance(range_val, list) or len(range_val) != 2:
                                    self.validation_errors.append(f"{io_type}.{field_name} range must be [min, max]")
                                elif range_val[0] >= range_val[1]:
                                    self.validation_errors.append(f"{io_type}.{field_name} range min must be < max")
    
    def _validate_arxdriver_business_logic(self, data: Dict[str, Any], file_path: str):
        """Validate ArxDriver business logic rules."""
        # Check for required fields
        required_fields = ["id", "type", "object_type", "protocol", "status", "source", "version"]
        for field in required_fields:
            if field not in data:
                self.validation_errors.append(f"Missing required field: {field}")
        
        # Validate ID format
        if "id" in data:
            id_val = data["id"]
            if not isinstance(id_val, str) or '.' not in id_val:
                self.validation_errors.append("id must be in format 'category.subcategory.protocol.vendor'")
        
        # Validate register_map if present
        if "register_map" in data:
            register_map = data["register_map"]
            if not isinstance(register_map, dict):
                self.validation_errors.append("register_map must be an object")
            else:
                for register_name, register_def in register_map.items():
                    if not isinstance(register_def, dict):
                        self.validation_errors.append(f"register_map.{register_name} must be an object")
                    else:
                        if "address" not in register_def:
                            self.validation_errors.append(f"register_map.{register_name} missing 'address' field")
                        if "type" not in register_def:
                            self.validation_errors.append(f"register_map.{register_name} missing 'type' field")
    
    def validate_all_schemas(self, directory: str) -> bool:
        """Validate all schema files in a directory."""
        directory_path = Path(directory)
        if not directory_path.exists():
            print(f"❌ Directory '{directory}' does not exist")
            return False
        
        valid_count = 0
        total_count = 0
        
        # Find all JSON schema files
        for json_file in directory_path.rglob("*.json"):
            if "schema" in json_file.name.lower():
                total_count += 1
                if self.validate_arxhal_schema(str(json_file)):
                    valid_count += 1
        
        # Find all YAML driver files
        for yaml_file in directory_path.rglob("*.yaml"):
            if "driver" in yaml_file.name.lower():
                total_count += 1
                if self.validate_arxdriver_config(str(yaml_file)):
                    valid_count += 1
        
        print(f"\n📊 Validation Summary: {valid_count}/{total_count} files valid")
        return valid_count == total_count
    
    def generate_example_schema(self, output_file: str):
        """Generate an example ArxHAL schema."""
        example_schema = {
            "$schema": "https://arxos.dev/specs/arxhal.schema.json",
            "object_type": "example_device",
            "version": "1.0.0",
            "description": "Example ArxHAL schema for demonstration",
            "inputs": {
                "temperature": {
                    "unit": "°C",
                    "type": "float",
                    "description": "Temperature sensor reading",
                    "range": [-40, 80],
                    "accuracy": "±0.5°C"
                },
                "humidity": {
                    "unit": "%",
                    "type": "float",
                    "description": "Relative humidity sensor",
                    "range": [0, 100],
                    "accuracy": "±2%"
                }
            },
            "outputs": {
                "relay": {
                    "type": "boolean",
                    "description": "Relay control output",
                    "default": False
                },
                "pwm": {
                    "unit": "%",
                    "type": "float",
                    "description": "PWM output control",
                    "range": [0, 100],
                    "default": 0
                }
            },
            "behavior_profile": "example_standard_v1",
            "alarms": {
                "high_temp": {
                    "description": "High temperature alarm",
                    "threshold": 30,
                    "unit": "°C",
                    "severity": "warning"
                }
            },
            "metadata": {
                "manufacturer": "example_vendor",
                "model": "example_device",
                "category": "sensor",
                "tags": ["example", "sensor", "demo"]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(example_schema, f, indent=2)
        
        print(f"✅ Example schema generated: {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ArxHAL Schema Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_schema.py arx-hal/schemas/ahu_schema.json
  python validate_schema.py arx-drivers/protocols/modbus_driver.yaml
  python validate_schema.py --validate-all arx-hal/
  python validate_schema.py --generate-example example_schema.json
        """
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="Schema file to validate (JSON for ArxHAL, YAML for ArxDriver)"
    )
    
    parser.add_argument(
        "--validate-all",
        metavar="DIRECTORY",
        help="Validate all schema files in directory"
    )
    
    parser.add_argument(
        "--generate-example",
        metavar="OUTPUT_FILE",
        help="Generate example ArxHAL schema"
    )
    
    args = parser.parse_args()
    
    validator = ArxHALValidator()
    
    if args.generate_example:
        validator.generate_example_schema(args.generate_example)
        return
    
    if args.validate_all:
        success = validator.validate_all_schemas(args.validate_all)
        sys.exit(0 if success else 1)
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ File '{args.file}' does not exist")
            sys.exit(1)
        
        if args.file.endswith('.json'):
            success = validator.validate_arxhal_schema(args.file)
        elif args.file.endswith('.yaml') or args.file.endswith('.yml'):
            success = validator.validate_arxdriver_config(args.file)
        else:
            print(f"❌ Unsupported file type: {args.file}")
            print("Supported types: .json (ArxHAL), .yaml/.yml (ArxDriver)")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
    
    # No arguments provided
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main() 