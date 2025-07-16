#!/usr/bin/env python3
"""
Fix import issues and class name mismatches in SVGX Engine services.

This script addresses:
1. Duplicate try-except blocks in imports
2. Class name mismatches between files and __init__.py
3. Import path issues
"""

import os
import re
import glob
from pathlib import Path


def fix_duplicate_try_except(file_path: str) -> bool:
    """Fix duplicate try-except blocks in import statements."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match duplicate try-except blocks
    pattern = r'try:\s*\n\s*try:\s*\n\s*from \.\.utils\.errors import ([^;]+);\s*\nexcept ImportError:\s*\n\s*# Fallback for direct execution\s*\n\s*import sys\s*\n\s*import os\s*\n\s*sys\.path\.append\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)\s*\n\s*from utils\.errors import ([^;]+);\s*\nexcept ImportError:\s*\n\s*# Fallback for direct execution\s*\n\s*import sys\s*\n\s*import os\s*\n\s*sys\.path\.append\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)\s*\n\s*from utils\.errors import ([^;]+);\s*\n\s*from utils import errors'
    
    replacement = r'try:\n    from ..utils.errors import \1\nexcept ImportError:\n    # Fallback for direct execution\n    import sys\n    import os\n    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n    from utils.errors import \1'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def fix_class_names():
    """Fix class name mismatches between service files and __init__.py."""
    class_mappings = {
        'access_control.py': {
            'AccessControlService': 'SVGXAccessControlService'
        },
        'advanced_caching.py': {
            'AdvancedCachingSystem': 'SVGXAdvancedCachingService'
        },
        'advanced_security.py': {
            'AdvancedSecurityService': 'SVGXAdvancedSecurityService'
        },
        'advanced_symbol_management.py': {
            'AdvancedSymbolManagementService': 'SVGXAdvancedSymbolManagementService'
        },
        'bim_builder.py': {
            'BIMBuilderService': 'SVGXBIMBuilderService'
        },
        'bim_export.py': {
            'BIMExportService': 'SVGXBIMExportService'
        },
        'bim_validator.py': {
            'BIMValidatorService': 'SVGXBIMValidatorService'
        },
        'error_handler.py': {
            'ErrorHandlerService': 'SVGXErrorHandlerService'
        },
        'export_interoperability.py': {
            'ExportInteroperabilityService': 'SVGXExportInteroperabilityService'
        },
        'performance_monitor.py': {
            'PerformanceMonitorService': 'SVGXPerformanceMonitorService'
        },
        'performance_optimization.py': {
            'PerformanceOptimizationService': 'SVGXPerformanceOptimizationService'
        },
        'performance_utils.py': {
            'PerformanceUtilsService': 'SVGXPerformanceUtilsService'
        },
        'persistence_export.py': {
            'PersistenceExportService': 'SVGXPersistenceExportService'
        },
        'realtime_telemetry.py': {
            'RealtimeTelemetryService': 'SVGXRealtimeTelemetryService'
        },
        'symbol_manager.py': {
            'SymbolManagerService': 'SVGXSymbolManagerService'
        },
        'symbol_recognition.py': {
            'SymbolRecognitionService': 'SVGXSymbolRecognitionService'
        },
        'symbol_renderer.py': {
            'SymbolRendererService': 'SVGXSymbolRendererService'
        },
        'symbol_schema_validation.py': {
            'SymbolSchemaValidationService': 'SVGXSymbolSchemaValidationService'
        },
        'telemetry.py': {
            'TelemetryService': 'SVGXTelemetryService'
        }
    }
    
    services_dir = Path(__file__).parent.parent / 'services'
    
    for filename, mappings in class_mappings.items():
        file_path = services_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            for old_name, new_name in mappings.items():
                if old_name in content:
                    content = content.replace(old_name, new_name)
                    modified = True
                    print(f"Renamed {old_name} to {new_name} in {filename}")
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)


def main():
    """Main function to fix all import issues."""
    print("Fixing SVGX Engine import issues...")
    
    # Fix duplicate try-except blocks
    services_dir = Path(__file__).parent.parent / 'services'
    service_files = glob.glob(str(services_dir / '*.py'))
    
    fixed_files = []
    for file_path in service_files:
        if fix_duplicate_try_except(file_path):
            fixed_files.append(Path(file_path).name)
    
    if fixed_files:
        print(f"Fixed duplicate try-except blocks in: {', '.join(fixed_files)}")
    else:
        print("No duplicate try-except blocks found.")
    
    # Fix class names
    fix_class_names()
    
    print("Import issues fixed successfully!")


if __name__ == "__main__":
    main() 