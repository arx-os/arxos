#!/usr/bin/env python3
"""
Script to fix malformed docstrings in the Arxos codebase.
This script identifies and fixes the common malformed docstring pattern.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple

def find_malformed_docstrings(file_path: str) -> List[Tuple[int, str]]:
    """Find malformed docstrings in a file."""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match malformed docstrings
        pattern = r'"""[^"]*Perform [a-zA-Z_]+ operation[^"]*"""

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                issues.append((i, line.strip()))

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return issues

def fix_malformed_docstring(content: str, line_number: int, original_line: str) -> str:
    """Fix a malformed docstring by replacing it with a proper one."""
    lines = content.split('\n')

    # Find the function/class definition
    function_pattern = r'def\s+(\w+)\s*\('
    class_pattern = r'class\s+(\w+)
    # Look for the function/class name in the malformed docstring
    if 'Perform __init__ operation' in original_line:
        if 'class' in lines[line_number - 2]:
            # It's a class __init__ method'
            class_match = re.search(class_pattern, lines[line_number - 2])
            if class_match:
                class_name = class_match.group(1)
                proper_docstring = f'        """Initialize the {class_name.lower().replace("_", " ")}.'"
                proper_docstring += '\n        \n        Args:'
                proper_docstring += '\n            Various initialization parameters'
                proper_docstring += '\n            \n        Returns:'
                proper_docstring += '\n            None'
                proper_docstring += '\n            \n        Raises:'
                proper_docstring += '\n            None'
                proper_docstring += '\n        """
        else:
            # It's a function'
            proper_docstring = '        """Execute the function.'"
            proper_docstring += '\n        \n        Args:'
            proper_docstring += '\n            Function parameters'
            proper_docstring += '\n            \n        Returns:'
            proper_docstring += '\n            Function result'
            proper_docstring += '\n            \n        Raises:'
            proper_docstring += '\n            Exception: If the function fails'
            proper_docstring += '\n        """
    elif 'Perform __str__ operation' in original_line:
        proper_docstring = '        """Return string representation.'"
        proper_docstring += '\n        \n        Args:'
        proper_docstring += '\n            None'
        proper_docstring += '\n            \n        Returns:'
        proper_docstring += '\n            String representation'
        proper_docstring += '\n            \n        Raises:'
        proper_docstring += '\n            None'
        proper_docstring += '\n        """
    elif 'Perform __repr__ operation' in original_line:
        proper_docstring = '        """Return detailed string representation.'"
        proper_docstring += '\n        \n        Args:'
        proper_docstring += '\n            None'
        proper_docstring += '\n            \n        Returns:'
        proper_docstring += '\n            Detailed string representation'
        proper_docstring += '\n            \n        Raises:'
        proper_docstring += '\n            None'
        proper_docstring += '\n        """
    else:
        # Generic fix
        proper_docstring = '        """Execute the operation.'"
        proper_docstring += '\n        \n        Args:'
        proper_docstring += '\n            Operation parameters'
        proper_docstring += '\n            \n        Returns:'
        proper_docstring += '\n            Operation result'
        proper_docstring += '\n            \n        Raises:'
        proper_docstring += '\n            Exception: If the operation fails'
        proper_docstring += '\n        """

    # Replace the malformed docstring
    lines[line_number - 1] = proper_docstring

    return '\n'.join(lines)

def process_file(file_path: str) -> bool:
    """Process a single file and fix malformed docstrings."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = find_malformed_docstrings(file_path)

        if not issues:
            return False

        print(f"Fixing {len(issues)} malformed docstrings in {file_path}")

        # Fix each issue
        for line_number, original_line in issues:
            content = fix_malformed_docstring(content, line_number, original_line)

        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix malformed docstrings in the entire codebase."""
    print("🔧 Fixing Malformed Docstrings")
    print("=" * 50)

    # Directories to process
    directories = [
        'api',
        'application',
        'domain',
        'infrastructure',
        'services',
        'svgx_engine',
        'core'
    ]

    total_fixed = 0
    files_processed = 0

    for directory in directories:
        if not os.path.exists(directory):
            continue

        print(f"\nProcessing {directory}/...")

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if process_file(file_path):
                        total_fixed += 1
                    files_processed += 1

    print(f"\n📊 Results:")
    print(f"Files processed: {files_processed}")
    print(f"Files fixed: {total_fixed}")
    print("✅ Malformed docstring fixes completed!")

if __name__ == "__main__":
    main()
