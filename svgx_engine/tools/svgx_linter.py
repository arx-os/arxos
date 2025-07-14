#!/usr/bin/env python3
"""
SVGX Linter for syntax validation and error reporting.

This tool validates SVGX files against the schema and provides
detailed error reporting and suggestions.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import local modules
try:
    from parser.parser import SVGXParser
    from schema.svgx_schema import SVGXSchemaValidator
except ImportError:
    # Fallback for testing
    SVGXParser = None
    SVGXSchemaValidator = None

logger = logging.getLogger(__name__)


class SVGXLinter:
    """Linter for SVGX files with comprehensive validation."""
    
    def __init__(self):
        self.parser = SVGXParser() if SVGXParser else None
        self.validator = SVGXSchemaValidator() if SVGXSchemaValidator else None
        self.errors = []
        self.warnings = []
        self.info = []
    
    def lint_file(self, file_path: str) -> bool:
        """
        Lint an SVGX file.
        
        Args:
            file_path: Path to the SVGX file
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.lint_content(content, file_path)
            
        except FileNotFoundError:
            self.add_error(f"File not found: {file_path}")
            return False
        except Exception as e:
            self.add_error(f"Failed to read file {file_path}: {e}")
            return False
    
    def lint_content(self, content: str, source_name: str = "input") -> bool:
        """
        Lint SVGX content.
        
        Args:
            content: SVGX content as string
            source_name: Name of the source for error reporting
            
        Returns:
            True if content is valid, False otherwise
        """
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Basic XML validation
        if not self._validate_xml(content, source_name):
            return False
        
        # SVGX namespace validation
        if not self._validate_namespace(content, source_name):
            return False
        
        # Parse and validate structure
        if not self._validate_structure(content, source_name):
            return False
        
        # Validate arx: elements
        self._validate_arx_elements(content, source_name)
        
        # Validate attributes
        self._validate_attributes(content, source_name)
        
        # Check for common issues
        self._check_common_issues(content, source_name)
        
        return len(self.errors) == 0
    
    def _validate_xml(self, content: str, source_name: str) -> bool:
        """Validate basic XML structure."""
        try:
            ET.fromstring(content)
            return True
        except ET.ParseError as e:
            self.add_error(f"Invalid XML in {source_name}: {e}")
            return False
    
    def _validate_namespace(self, content: str, source_name: str) -> bool:
        """Validate SVGX namespace declaration."""
        if 'xmlns:arx="http://arxos.io/svgx"' not in content:
            self.add_error(f"Missing arx namespace declaration in {source_name}")
            return False
        
        if 'xmlns="http://www.w3.org/2000/svg"' not in content:
            self.add_warning(f"Missing SVG namespace declaration in {source_name}")
        
        return True
    
    def _validate_structure(self, content: str, source_name: str) -> bool:
        """Validate SVGX structure."""
        try:
            if self.parser:
                elements = self.parser.parse(content)
                
                # Check for root SVG element
                svg_elements = [elem for elem in elements if elem.tag == 'svg']
                if not svg_elements:
                    self.add_error(f"No root SVG element found in {source_name}")
                    return False
                
                # Check for at least one arx:object
                arx_objects = [elem for elem in elements if elem.tag == 'arx:object']
                if not arx_objects:
                    self.add_warning(f"No arx:object elements found in {source_name}")
            else:
                # Fallback validation
                if '<svg' not in content:
                    self.add_error(f"No root SVG element found in {source_name}")
                    return False
                
                if '<arx:object' not in content:
                    self.add_warning(f"No arx:object elements found in {source_name}")
            
            return True
            
        except Exception as e:
            self.add_error(f"Failed to parse SVGX structure in {source_name}: {e}")
            return False
    
    def _validate_arx_elements(self, content: str, source_name: str):
        """Validate arx: elements."""
        try:
            root = ET.fromstring(content)
            
            # Check arx:object elements
            for obj in root.findall('.//arx:object'):
                self._validate_arx_object(obj, source_name)
            
            # Check arx:behavior elements
            for behavior in root.findall('.//arx:behavior'):
                self._validate_arx_behavior(behavior, source_name)
            
            # Check arx:physics elements
            for physics in root.findall('.//arx:physics'):
                self._validate_arx_physics(physics, source_name)
                
        except Exception as e:
            self.add_error(f"Failed to validate arx: elements in {source_name}: {e}")
    
    def _validate_arx_object(self, obj: ET.Element, source_name: str):
        """Validate arx:object element."""
        # Check required attributes
        if not obj.get('id'):
            self.add_error(f"arx:object missing required 'id' attribute in {source_name}")
        
        if not obj.get('type'):
            self.add_error(f"arx:object missing required 'type' attribute in {source_name}")
        
        # Check for valid object type
        obj_type = obj.get('type', '')
        if obj_type and '.' not in obj_type:
            self.add_warning(f"arx:object type '{obj_type}' should use dot notation (e.g., 'electrical.light_fixture') in {source_name}")
    
    def _validate_arx_behavior(self, behavior: ET.Element, source_name: str):
        """Validate arx:behavior element."""
        # Check for variables
        variables = behavior.find('variables')
        if variables is not None:
            for var in variables.findall('variable'):
                if not var.get('name'):
                    self.add_error(f"Variable missing 'name' attribute in {source_name}")
        
        # Check for calculations
        calculations = behavior.find('calculations')
        if calculations is not None:
            for calc in calculations.findall('calculation'):
                if not calc.get('name'):
                    self.add_error(f"Calculation missing 'name' attribute in {source_name}")
                if not calc.get('formula'):
                    self.add_error(f"Calculation missing 'formula' attribute in {source_name}")
    
    def _validate_arx_physics(self, physics: ET.Element, source_name: str):
        """Validate arx:physics element."""
        # Check mass element
        mass = physics.find('mass')
        if mass is not None:
            if not mass.text or not mass.text.strip():
                self.add_error(f"Mass element has no value in {source_name}")
        
        # Check forces
        forces = physics.find('forces')
        if forces is not None:
            for force in forces.findall('force'):
                if not force.get('type'):
                    self.add_error(f"Force missing 'type' attribute in {source_name}")
    
    def _validate_attributes(self, content: str, source_name: str):
        """Validate arx: attributes."""
        try:
            root = ET.fromstring(content)
            
            # Check arx:precision attributes
            for elem in root.findall('.//*[@arx:precision]'):
                precision = elem.get('arx:precision')
                if precision and not self._is_valid_precision(precision):
                    self.add_error(f"Invalid arx:precision value '{precision}' in {source_name}")
            
            # Check arx:layer attributes
            for elem in root.findall('.//*[@arx:layer]'):
                layer = elem.get('arx:layer')
                if layer and not self._is_valid_layer(layer):
                    self.add_warning(f"Unusual layer name '{layer}' in {source_name}")
                    
        except Exception as e:
            self.add_error(f"Failed to validate attributes in {source_name}: {e}")
    
    def _is_valid_precision(self, precision: str) -> bool:
        """Check if precision value is valid."""
        try:
            # Should be a number followed by a unit
            import re
            pattern = r'^\d+(\.\d+)?(mm|cm|m|in|ft)$'
            return bool(re.match(pattern, precision))
        except:
            return False
    
    def _is_valid_layer(self, layer: str) -> bool:
        """Check if layer name is valid."""
        valid_layers = ['electrical', 'mechanical', 'plumbing', 'hvac', 'architecture', 'walls', 'doors', 'windows']
        return layer.lower() in valid_layers
    
    def _check_common_issues(self, content: str, source_name: str):
        """Check for common SVGX issues."""
        # Check for missing units
        if 'arx:precision' in content and 'mm' not in content and 'cm' not in content and 'm' not in content:
            self.add_warning(f"Consider adding units to arx:precision attributes in {source_name}")
        
        # Check for missing system attributes
        if 'arx:object' in content and 'system=' not in content:
            self.add_warning(f"Consider adding 'system' attributes to arx:object elements in {source_name}")
        
        # Check for missing behavior
        if 'arx:object' in content and 'arx:behavior' not in content:
            self.add_info(f"Consider adding behavior profiles to objects in {source_name}")
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)
    
    def print_report(self):
        """Print the linting report."""
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
        
        if self.info:
            print("ℹ️  INFO:")
            for info in self.info:
                print(f"  • {info}")
            print()
        
        if not self.errors and not self.warnings and not self.info:
            print("✅ No issues found!")
        elif not self.errors:
            print("✅ No errors found!")
        else:
            print(f"❌ Found {len(self.errors)} error(s), {len(self.warnings)} warning(s)")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="SVGX Linter")
    parser.add_argument("file", help="SVGX file to lint")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    linter = SVGXLinter()
    
    print(f"Linting {args.file}...")
    is_valid = linter.lint_file(args.file)
    
    linter.print_report()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main() 