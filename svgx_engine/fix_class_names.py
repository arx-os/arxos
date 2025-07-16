#!/usr/bin/env python3
"""
Fix SVGX Engine Service Class Names and Imports

This script fixes class naming inconsistencies and updates imports
to match the actual class names in the service files.
"""

import os
import re
from pathlib import Path

def fix_class_names_in_file(file_path, class_mappings):
    """Fix class names in a specific file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for old_name, new_name in class_mappings.items():
        # Fix class definitions
        content = re.sub(
            rf'class\s+{re.escape(old_name)}\b',
            f'class {new_name}',
            content
        )
        
        # Fix any references to the class within the file
        content = re.sub(
            rf'\b{re.escape(old_name)}\b',
            new_name,
            content
        )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed class names in {file_path}")
        return True
    return False

def update_services_init():
    """Update the services __init__.py with correct imports"""
    init_path = Path("services/__init__.py")
    
    # Define the correct imports based on actual class names
    correct_imports = {
        # Core Services
        "SVGXErrorHandlerService": "SVGXErrorHandler",
        "SVGXPerformanceMonitorService": "SVGXPerformanceProfiler", 
        "SVGXAccessControlService": "SVGXAccessControlService",  # Will be fixed
        "SVGXAdvancedSecurityService": "SVGXAdvancedSecurityService",
        "SVGXTelemetryService": "SVGXTelemetryIngestor",
        "SVGXRealtimeTelemetryService": "SVGXTelemetryIngestor",  # Use same as telemetry
        "SVGXPerformanceOptimizationService": "SVGXPerformanceOptimizer",
        "SVGXPerformanceUtilsService": "SVGXPerformanceProfiler",  # Use profiler
        
        # BIM Services
        "SVGXBIMBuilderService": "SVGXBIMBuilderService",
        "SVGXBIMExportService": "SVGXBIMExportService",  # Will be fixed
        "SVGXBIMValidatorService": "SVGXBIMValidatorService",
        
        # Symbol Management Services
        "SVGXSymbolManagerService": "SVGXSymbolManagerService",  # Need to check if exists
        "SVGXExportInteroperabilityService": "SVGXExportInteroperabilityService",  # Will be fixed
        "SVGXSymbolRecognitionService": "SVGXSymbolRecognitionService",
        "SVGXAdvancedSymbolManagementService": "AdvancedSymbolManagementService",  # Missing SVGX prefix
        "SVGXSymbolSchemaValidationService": "SVGXSymbolSchemaValidationService",
        "SVGXSymbolRendererService": "SVGXSymbolRendererService",
        "SVGXSymbolGenerator": "SVGXSymbolGenerator",
        "symbol_generator_service": "symbol_generator_service",
        
        # Advanced Services
        "SVGXAdvancedCachingService": "SVGXAdvancedCachingService",
        "SVGXPersistenceExportService": "SVGXPersistenceExportService",
    }
    
    # Read current init file
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update imports
    for old_import, actual_class in correct_imports.items():
        # Find the file that contains this class
        class_file = None
        for py_file in Path("services").glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            with open(py_file, 'r', encoding='utf-8') as f:
                if f"class {actual_class}" in f.read():
                    class_file = py_file.stem
                    break
        
        if class_file:
            # Update the import line
            old_import_line = f"from .{class_file} import {old_import}"
            new_import_line = f"from .{class_file} import {actual_class} as {old_import}"
            
            content = content.replace(old_import_line, new_import_line)
    
    # Write updated content
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Updated services/__init__.py with correct imports")

def main():
    """Main function to fix all class naming issues"""
    print("Fixing SVGX Engine service class names...")
    
    # Define class name fixes
    class_fixes = {
        # Fix duplicate SVGX prefixes
        "SVGXSVGXAccessControlService": "SVGXAccessControlService",
        "SVGXSVGXBIMExportService": "SVGXBIMExportService", 
        "SVGXSVGXExportInteroperabilityService": "SVGXExportInteroperabilityService",
        
        # Fix missing SVGX prefixes
        "AdvancedSymbolManagementService": "SVGXAdvancedSymbolManagementService",
        "BIMHealthCheckerService": "SVGXBIMHealthCheckerService",
        "BIMAssemblyService": "SVGXBIMAssemblyService",
        "DatabaseService": "SVGXDatabaseService",
        "PersistenceService": "SVGXPersistenceService",
        "SecurityService": "SVGXSecurityService",
    }
    
    # Fix class names in service files
    services_dir = Path("services")
    for py_file in services_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        fix_class_names_in_file(py_file, class_fixes)
    
    # Update the services __init__.py
    update_services_init()
    
    print("Class name fixes completed!")

if __name__ == "__main__":
    main() 