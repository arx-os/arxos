#!/usr/bin/env python3
"""
Fix relative import issues in SVGX Engine services.
This script adds try-except blocks to handle import errors gracefully.
"""

import os
import re
import sys
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix relative imports in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match relative imports from utils
    pattern = r'from \.\.utils\.(\w+) import (.+)'
    
    def replace_import(match):
        module = match.group(1)
        imports = match.group(2)
        
        # Create the try-except block
        replacement = f'''try:
    from ..utils.{module} import {imports}
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.{module} import {imports}'''
        
        return replacement
    
    # Replace all relative imports
    new_content = re.sub(pattern, replace_import, content)
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Fixed imports in {file_path}")

def main():
    """Fix imports in all service files."""
    svgx_engine_dir = Path(__file__).parent
    services_dir = svgx_engine_dir / 'services'
    
    # Fix imports in service files
    for file_path in services_dir.glob('*.py'):
        if file_path.name != '__init__.py':
            fix_imports_in_file(file_path)
    
    print("Import fixes completed!")

if __name__ == '__main__':
    main() 