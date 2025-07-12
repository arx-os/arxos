#!/usr/bin/env python3
"""
Script to update all metadata references in the codebase.

This script systematically updates all references to the 'metadata' field
in database models to use the new field names:
- BIMModel.metadata -> BIMModel.model_metadata
- SymbolLibrary.metadata -> SymbolLibrary.symbol_metadata
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_files_to_update() -> List[Path]:
    """Find all Python files that need to be updated."""
    project_root = Path(__file__).parent.parent
    files = []
    
    # Directories to search
    search_dirs = [
        'services',
        'routers', 
        'utils',
        'api',
        'models',
        'tests'
    ]
    
    for search_dir in search_dirs:
        dir_path = project_root / search_dir
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                files.append(py_file)
    
    return files


def update_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Update a single file with the new metadata field names."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Update BIMModel.metadata references
        # Pattern: model.metadata or db_model.metadata or existing_model.metadata
        content = re.sub(
            r'(\w+)\.metadata',
            lambda m: f'{m.group(1)}.model_metadata' if 'model' in m.group(1).lower() or 'bim' in m.group(1).lower() else m.group(0),
            content
        )
        
        # Update SymbolLibrary.metadata references
        # Pattern: symbol.metadata or db_symbol.metadata or existing_symbol.metadata
        content = re.sub(
            r'(\w+)\.metadata',
            lambda m: f'{m.group(1)}.symbol_metadata' if 'symbol' in m.group(1).lower() else m.group(0),
            content
        )
        
        # Update specific patterns for database models
        replacements = [
            # BIMModel specific
            ('model.metadata', 'model.model_metadata'),
            ('db_model.metadata', 'db_model.model_metadata'),
            ('existing_model.metadata', 'existing_model.model_metadata'),
            ('bim_model.metadata', 'bim_model.model_metadata'),
            
            # SymbolLibrary specific
            ('symbol.metadata', 'symbol.symbol_metadata'),
            ('db_symbol.metadata', 'db_symbol.symbol_metadata'),
            ('existing_symbol.metadata', 'existing_symbol.symbol_metadata'),
            ('symbol_match.metadata', 'symbol_match.symbol_metadata'),
            
            # Request/API specific
            ('request.metadata', 'request.model_metadata'),  # For BIM requests
            ('request.symbol_metadata', 'request.symbol_metadata'),  # For symbol requests
        ]
        
        for old_pattern, new_pattern in replacements:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                changes.append(f"  {old_pattern} -> {new_pattern}")
        
        # Update dictionary key references
        content = re.sub(
            r'"metadata":\s*(\w+)\.metadata',
            lambda m: f'"model_metadata": {m.group(1)}.model_metadata' if 'model' in m.group(1).lower() or 'bim' in m.group(1).lower() else f'"symbol_metadata": {m.group(1)}.symbol_metadata',
            content
        )
        
        # Update metadata field assignments
        content = re.sub(
            r'(\w+)\.metadata\s*=\s*(\w+)',
            lambda m: f'{m.group(1)}.model_metadata = {m.group(2)}' if 'model' in m.group(1).lower() or 'bim' in m.group(1).lower() else f'{m.group(1)}.symbol_metadata = {m.group(2)}',
            content
        )
        
        # Update metadata field access in conditions
        content = re.sub(
            r'(\w+)\.metadata\.get\(',
            lambda m: f'{m.group(1)}.model_metadata.get(' if 'model' in m.group(1).lower() or 'bim' in m.group(1).lower() else f'{m.group(1)}.symbol_metadata.get(',
            content
        )
        
        content = re.sub(
            r'(\w+)\.metadata\.update\(',
            lambda m: f'{m.group(1)}.model_metadata.update(' if 'model' in m.group(1).lower() or 'bim' in m.group(1).lower() else f'{m.group(1)}.symbol_metadata.update(',
            content
        )
        
        # Update metadata field access in string formatting
        content = re.sub(
            r'f["\']([^"\']*)\{(\w+)\.metadata\}([^"\']*)["\']',
            lambda m: f'f"{m.group(1)}{{{m.group(2)}.model_metadata}}{m.group(3)}"' if 'model' in m.group(2).lower() or 'bim' in m.group(2).lower() else f'f"{m.group(1)}{{{m.group(2)}.symbol_metadata}}{m.group(3)}"',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        else:
            return False, []
            
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False, [f"Error: {e}"]


def main():
    """Main function to update all metadata references."""
    print("Updating metadata references in codebase...")
    
    files = find_files_to_update()
    print(f"Found {len(files)} files to check")
    
    updated_files = 0
    total_changes = 0
    
    for file_path in files:
        try:
            was_updated, changes = update_file(file_path)
            if was_updated:
                updated_files += 1
                total_changes += len(changes)
                print(f"Updated {file_path}")
                for change in changes:
                    print(change)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"\nUpdate complete!")
    print(f"Updated {updated_files} files")
    print(f"Made {total_changes} changes")
    
    print("\nNext steps:")
    print("1. Review the changes to ensure they are correct")
    print("2. Run tests to verify functionality")
    print("3. Update any remaining manual references")
    print("4. Run database migrations")


if __name__ == "__main__":
    main() 