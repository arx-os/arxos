#!/usr/bin/env python3
"""
Script to add missing type hints to key Python files in the Arxos codebase.

This script focuses on adding return type hints to methods that are missing them,
particularly in domain and application layer files.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Files to process (focus on key domain and application files)
TARGET_FILES = [
    "domain/value_objects.py",
    "domain/entities.py", 
    "application/services/building_service.py",
    "infrastructure/repositories/base.py",
]

# Common return type patterns
RETURN_TYPE_PATTERNS = {
    "__post_init__": "None",
    "__str__": "str",
    "__repr__": "str", 
    "__eq__": "bool",
    "__hash__": "int",
    "__len__": "int",
    "__bool__": "bool",
    "validate": "None",
    "_validate": "None",
    "to_dict": "Dict[str, Any]",
    "to_json": "str",
    "from_dict": "Self",
    "from_json": "Self",
}

# Method patterns that likely return None
NONE_RETURN_PATTERNS = [
    r"def\s+_.*\(", # Private methods often return None
    r"def\s+set_.*\(",  # Setters
    r"def\s+update_.*\(",  # Updates
    r"def\s+add_.*\(",  # Additions  
    r"def\s+remove_.*\(",  # Removals
    r"def\s+delete_.*\(",  # Deletions
    r"def\s+clear.*\(",  # Clear operations
    r"def\s+reset.*\(",  # Reset operations
]

# Method patterns that likely return bool
BOOL_RETURN_PATTERNS = [
    r"def\s+is_.*\(",
    r"def\s+has_.*\(",
    r"def\s+can_.*\(",
    r"def\s+should_.*\(",
    r"def\s+exists.*\(",
    r"def\s+contains.*\(",
]

# Method patterns that likely return List
LIST_RETURN_PATTERNS = [
    r"def\s+get_all.*\(",
    r"def\s+find_all.*\(",
    r"def\s+list_.*\(",
    r"def\s+find_by.*\(",  # Often returns lists
]


class TypeHintAdder:
    """Add missing type hints to Python files."""
    
    def __init__(self):
        self.modified_files: Set[str] = set()
        self.added_hints: Dict[str, int] = {}
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single file to add missing type hints."""
        if not file_path.exists():
            print(f"Warning: File {file_path} does not exist")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            content = self._add_type_hints_to_content(content, str(file_path))
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.modified_files.add(str(file_path))
                print(f"✓ Added type hints to {file_path}")
                return True
            else:
                print(f"- No changes needed for {file_path}")
                return False
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False
    
    def _add_type_hints_to_content(self, content: str, file_path: str) -> str:
        """Add type hints to content string."""
        lines = content.split('\n')
        modified_lines = []
        hints_added = 0
        
        for i, line in enumerate(lines):
            # Check if this is a method definition without return type
            method_match = re.match(r'^(\s*)(def\s+(\w+)\([^)]*\))(\s*):(.*)$', line)
            
            if method_match:
                indent, method_def, method_name, spaces, rest = method_match.groups()
                
                # Skip if already has return type annotation
                if '->' in method_def:
                    modified_lines.append(line)
                    continue
                
                # Determine return type based on patterns
                return_type = self._determine_return_type(method_name, method_def, lines, i)
                
                if return_type:
                    # Add the return type annotation
                    new_line = f"{indent}{method_def} -> {return_type}:{rest}"
                    modified_lines.append(new_line)
                    hints_added += 1
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        if hints_added > 0:
            self.added_hints[file_path] = hints_added
        
        return '\n'.join(modified_lines)
    
    def _determine_return_type(self, method_name: str, method_def: str, 
                             lines: List[str], line_index: int) -> Optional[str]:
        """Determine the appropriate return type for a method."""
        
        # Check exact method name matches first
        if method_name in RETURN_TYPE_PATTERNS:
            return RETURN_TYPE_PATTERNS[method_name]
        
        # Check pattern matches for None return types
        for pattern in NONE_RETURN_PATTERNS:
            if re.match(pattern, method_def.strip()):
                return "None"
        
        # Check pattern matches for bool return types  
        for pattern in BOOL_RETURN_PATTERNS:
            if re.match(pattern, method_def.strip()):
                return "bool"
        
        # Check pattern matches for list return types
        for pattern in LIST_RETURN_PATTERNS:
            if re.match(pattern, method_def.strip()):
                return "List[Any]"  # Generic list, could be more specific
        
        # Analyze method body for return statements
        return_type = self._analyze_method_body(lines, line_index)
        
        return return_type
    
    def _analyze_method_body(self, lines: List[str], start_index: int) -> Optional[str]:
        """Analyze method body to determine return type from return statements."""
        
        # Find method body (next few lines with proper indentation)
        method_line = lines[start_index]
        base_indent = len(method_line) - len(method_line.lstrip())
        
        # Look at next 10-15 lines for return statements
        end_index = min(start_index + 15, len(lines))
        
        has_return_none = False
        has_return_value = False
        return_types = set()
        
        for i in range(start_index + 1, end_index):
            if i >= len(lines):
                break
                
            line = lines[i]
            
            # Stop if we hit another method or class definition at same level
            if line.strip() and not line.startswith(' ' * (base_indent + 1)):
                if line.strip().startswith(('def ', 'class ', '@')):
                    break
            
            # Look for return statements
            stripped = line.strip()
            if stripped.startswith('return'):
                if stripped == 'return' or stripped == 'return None':
                    has_return_none = True
                else:
                    has_return_value = True
                    # Try to determine type from return value
                    if 'return True' in stripped or 'return False' in stripped:
                        return_types.add('bool')
                    elif 'return []' in stripped or 'return list(' in stripped:
                        return_types.add('List[Any]')
                    elif 'return {}' in stripped or 'return dict(' in stripped:
                        return_types.add('Dict[str, Any]')
                    elif 'return ""' in stripped or 'return str(' in stripped:
                        return_types.add('str')
                    elif re.search(r'return\s+\d+', stripped):
                        return_types.add('int')
                    elif 'return self' in stripped:
                        return_types.add('Self')
        
        # Determine return type based on analysis
        if return_types:
            if len(return_types) == 1:
                return list(return_types)[0]
            elif has_return_none:
                return f"Optional[{list(return_types)[0]}]"
        
        if has_return_none and not has_return_value:
            return "None"
        
        # If we can't determine, don't add a hint
        return None
    
    def process_all_files(self, base_path: Path) -> None:
        """Process all target files."""
        print("Adding missing type hints to key files...")
        print("=" * 50)
        
        for file_path in TARGET_FILES:
            full_path = base_path / file_path
            self.process_file(full_path)
        
        print("\n" + "=" * 50)
        print(f"Summary:")
        print(f"Files modified: {len(self.modified_files)}")
        print(f"Total type hints added: {sum(self.added_hints.values())}")
        
        if self.added_hints:
            print("\nHints added per file:")
            for file_path, count in self.added_hints.items():
                print(f"  {file_path}: {count}")


def main():
    """Main function."""
    # Get the repository root
    script_path = Path(__file__)
    repo_root = script_path.parent.parent
    
    print(f"Processing files in: {repo_root}")
    
    # Add type hints
    adder = TypeHintAdder()
    adder.process_all_files(repo_root)
    
    print("\nType hint addition completed!")
    print("\nNote: You may need to add these imports to files that use new type hints:")
    print("from typing import List, Dict, Any, Optional, Union, Set")
    print("from __future__ import annotations  # For Self type")


if __name__ == "__main__":
    main()