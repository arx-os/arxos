(#!/usr/bin/env python3
"""
Critical Syntax Error Fixer

This script fixes the most critical syntax errors that prevent compilation.
Focuses on the most common and blocking issues.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

class CriticalSyntaxFixer:
    """Fix critical syntax errors that prevent compilation."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.fixed_files = []
        self.errors = []

        # Directories to exclude
        self.exclude_dirs = {
            'venv', '__pycache__', '.git', 'node_modules',
            '.pytest_cache', '.mypy_cache', '.coverage'
        }

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        # Skip virtual environment and cache directories
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return False

        # Only process Python files
        return file_path.suffix == '.py'

    def fix_malformed_docstrings(self, file_path: Path) -> bool:
        """Fix malformed docstrings that cause syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix common malformed docstring patterns
            # Pattern: """\nArgs:\n    param: Description\nReturns:\n    Description\nRaises:\n    Exception: Description\nExample:\n    result = func(param)\n    print(result)\n"""
            lines = content.split('\n')
            fixed_lines = []
            i = 0

            while i < len(lines):
                line = lines[i]

                # Check for malformed docstring pattern
                if line.strip().startswith('""") and i + 1 < len(lines):"
                    # Look for the pattern that causes issues
                    if 'Args:' in line or 'Returns:' in line or 'Raises:' in line:
                        # Find the end of the docstring
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().endswith('"""):"
                            j += 1

                        if j < len(lines):
                            # Replace the malformed docstring with a simple one
                            fixed_lines.append(line.strip().replace('""", '"""TODO: Add proper documentation."""))
                            i = j + 1
                            continue

                fixed_lines.append(line)
                i += 1

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing docstrings in {file_path}: {e}")

        return False

    def fix_function_signatures(self, file_path: Path) -> bool:
        """Fix function signature syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix function signatures with missing closing parentheses
            lines = content.split('\n')
            fixed_lines = []

            for i, line in enumerate(lines):
                # Check for function definitions with missing closing parentheses
                if line.strip().startswith('async def ') or line.strip().startswith('def '):
                    # Look for the pattern where a parameter is on the next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('current_user: User = Depends(') and not line.strip().endswith(')'):
                            # Fix the function signature
                            fixed_line = line.rstrip() + ', ' + next_line.rstrip(',:') + ')
                            fixed_lines.append(fixed_line)
                            # Skip the next line since we merged it
                            i += 1
                            continue

                fixed_lines.append(line)

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing function signatures in {file_path}: {e}")

        return False

    def fix_import_statements(self, file_path: Path) -> bool:
        """Fix malformed import statements."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix incomplete import statements
            lines = content.split('\n')
            fixed_lines = []

            for line in lines:
                # Fix incomplete imports like "from services.module"
                if line.strip().startswith('from ') and not line.strip().endswith('import'):
                    if 'import' not in line:
                        # Extract module name and create proper import
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            module = parts[1]
                            fixed_line = f"from {module} import {module.split('.')[-1]}"
                            fixed_lines.append(fixed_line)
                            continue

                fixed_lines.append(line)

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing imports in {file_path}: {e}")

        return False

    def fix_empty_function_bodies(self, file_path: Path) -> bool:
        """Add proper implementations for empty function bodies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Find functions with empty bodies and add TODO comments
            lines = content.split('\n')
            fixed_lines = []
            i = 0

            while i < len(lines):
                line = lines[i]

                # Check for function definition
                if line.strip().startswith('def ') and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()

                    # If the next line is just pass, add a TODO comment
                    if next_line == 'pass':
                        fixed_lines.append(line)
                        fixed_lines.append('    """TODO: Implement this function.""")
                        fixed_lines.append('    pass')
                        i += 1
                        continue

                fixed_lines.append(line)
                i += 1

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing empty function bodies in {file_path}: {e}")

        return False

    def process_file(self, file_path: Path) -> bool:
        """Process a single file and fix all syntax errors."""
        if not self.should_process_file(file_path):
            return False

        print(f"Processing: {file_path}")

        fixed = False

        # Apply fixes in order
        if self.fix_malformed_docstrings(file_path):
            fixed = True
            print(f"  ✓ Fixed docstrings")

        if self.fix_function_signatures(file_path):
            fixed = True
            print(f"  ✓ Fixed function signatures")

        if self.fix_import_statements(file_path):
            fixed = True
            print(f"  ✓ Fixed import statements")

        if self.fix_empty_function_bodies(file_path):
            fixed = True
            print(f"  ✓ Fixed empty function bodies")

        if fixed:
            self.fixed_files.append(str(file_path)
        return fixed

    def process_directory(self, directory: Path) -> int:
        """Process all Python files in a directory recursively."""
        fixed_count = 0

        for file_path in directory.rglob('*.py'):
            if self.process_file(file_path):
                fixed_count += 1

        return fixed_count

    def run(self) -> Dict[str, any]:
        """Run the syntax error fixer on the entire codebase."""
        print("🔧 Critical Syntax Error Fixer")
        print("=" * 50)

        # Process the root directory
        fixed_count = self.process_directory(self.root_dir)

        print(f"\n📊 Results:")
        print(f"  Files fixed: {fixed_count}")
        print(f"  Errors encountered: {len(self.errors)}")

        if self.errors:
            print(f"\n❌ Errors:")
            for error in self.errors:
                print(f"  {error}")

        if self.fixed_files:
            print(f"\n✅ Fixed files:")
            for file_path in self.fixed_files:
                print(f"  {file_path}")

        return {
            'fixed_count': fixed_count,
            'errors': self.errors,
            'fixed_files': self.fixed_files
        }

def main():
    """Main entry point for the syntax error fixer."""
    fixer = CriticalSyntaxFixer()
    results = fixer.run()

    if results['errors']:
        sys.exit(1)
    else:
        print(f"\n🎉 Critical syntax error fixing completed successfully!")
        print(f"Fixed {results['fixed_count']} files.")

if __name__ == "__main__":
    main()
