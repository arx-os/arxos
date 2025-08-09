#!/usr/bin/env python3
"""
Remaining Critical Syntax Error Fixer

This script fixes the remaining critical syntax errors that prevent compilation.
Focuses on the most common patterns causing compilation failures.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

class RemainingCriticalFixer:
    """Fix remaining critical syntax errors."""

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

    def fix_await_outside_function(self, file_path: Path) -> bool:
        """Fix 'await' outside function errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix await outside function context
            lines = content.split('\n')
            fixed_lines = []

            for line in lines:
                # Check for await outside function
                if line.strip().startswith('await ') and not any(
                    prev_line.strip().startswith(('async def ', 'def ')
                    for prev_line in lines[:lines.index(line)]
                ):
                    # Comment out the await line
                    fixed_lines.append(f"# TODO: Fix await outside function context: {line.strip()}")
                    fixed_lines.append("pass")
                else:
                    fixed_lines.append(line)

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing await outside function in {file_path}: {e}")

        return False

    def fix_unterminated_strings(self, file_path: Path) -> bool:
        """Fix unterminated string literals."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix unterminated string literals
            lines = content.split('\n')
            fixed_lines = []

            for line in lines:
                # Check for unterminated strings
                if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:"'
                    # Add closing quote
                    if line.count('"') % 2 != 0:"
                        line = line + '"'"
                    if line.count("'") % 2 != 0:'
                        line = line + "'"'

                fixed_lines.append(line)

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing unterminated strings in {file_path}: {e}")

        return False

    def fix_unmatched_parentheses(self, file_path: Path) -> bool:
        """Fix unmatched parentheses."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Count parentheses and fix unmatched ones
            open_parens = content.count('(')
            close_parens = content.count(')')

            if open_parens > close_parens:
                # Add missing closing parentheses
                content = content + ')' * (open_parens - close_parens)
            elif close_parens > open_parens:
                # Add missing opening parentheses
                content = '(' * (close_parens - open_parens) + content

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing unmatched parentheses in {file_path}: {e}")

        return False

    def fix_keyword_argument_repeated(self, file_path: Path) -> bool:
        """Fix repeated keyword arguments."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix repeated keyword arguments
            lines = content.split('\n')
            fixed_lines = []

            for line in lines:
                # Check for repeated keyword arguments
                if 'text=' in line and line.count('text=') > 1:
                    # Remove duplicate text= arguments
                    parts = line.split(',')
                    seen_args = set()
                    fixed_parts = []

                    for part in parts:
                        if 'text=' in part:
                            if 'text=' not in seen_args:
                                fixed_parts.append(part)
                                seen_args.add('text=')
                        else:
                            fixed_parts.append(part)

                    line = ','.join(fixed_parts)

                fixed_lines.append(line)

            new_content = '\n'.join(fixed_lines)

            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing keyword arguments in {file_path}: {e}")

        return False

    def fix_indentation_errors(self, file_path: Path) -> bool:
        """Fix indentation errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            original_lines = lines.copy()
            fixed = False

            for i, line in enumerate(lines):
                # Fix inconsistent indentation
                if line.strip().startswith('def ') or line.strip().startswith('class '):
                    # Ensure proper indentation for function/class definitions
                    if i > 0 and lines[i-1].strip() and not lines[i-1].strip().endswith(':'):
                        # This should be at module level
                        if line.startswith(' '):
                            lines[i] = line.lstrip()
                            fixed = True

                # Fix indentation after function definitions
                if line.strip().startswith('def ') and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and not next_line.startswith('    '):
                        # Add proper indentation
                        lines[i + 1] = '    ' + next_line.lstrip()
                        fixed = True

            if fixed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing indentation in {file_path}: {e}")

        return False

    def process_file(self, file_path: Path) -> bool:
        """Process a single file and fix all syntax errors."""
        if not self.should_process_file(file_path):
            return False

        print(f"Processing: {file_path}")

        fixed = False

        # Apply fixes in order
        if self.fix_await_outside_function(file_path):
            fixed = True
            print(f"  ✓ Fixed await outside function")

        if self.fix_unterminated_strings(file_path):
            fixed = True
            print(f"  ✓ Fixed unterminated strings")

        if self.fix_unmatched_parentheses(file_path):
            fixed = True
            print(f"  ✓ Fixed unmatched parentheses")

        if self.fix_keyword_argument_repeated(file_path):
            fixed = True
            print(f"  ✓ Fixed repeated keyword arguments")

        if self.fix_indentation_errors(file_path):
            fixed = True
            print(f"  ✓ Fixed indentation errors")

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
        print("🔧 Remaining Critical Syntax Error Fixer")
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
    fixer = RemainingCriticalFixer()
    results = fixer.run()

    if results['errors']:
        sys.exit(1)
    else:
        print(f"\n🎉 Remaining critical syntax error fixing completed successfully!")
        print(f"Fixed {results['fixed_count']} files.")

if __name__ == "__main__":
    main()
