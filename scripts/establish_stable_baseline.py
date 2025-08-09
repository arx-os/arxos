#!/usr/bin/env python3
"""
Establish Stable Compilation Baseline

This script systematically fixes all critical syntax errors to establish
a stable compilation baseline for the Arxos codebase.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Set

class StableBaselineFixer:
    """Fix all critical syntax errors to establish stable compilation."""

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
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return False
        return file_path.suffix == '.py'

    def fix_common_syntax_errors(self, file_path: Path) -> bool:
        """Fix the most common syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            fixed = False

            # Fix 1: Unterminated string literals ("""" -> """)
            if '""""' in content:
                content = content.replace('""""', '"""')
                fixed = True

            # Fix 2: Extra quotes at end of docstrings ("""' -> """)
            content = content.replace('"""\'', '"""')
            if '"""\'' in original_content:
                fixed = True

            # Fix 3: Malformed function signatures with extra commas
            # Pattern: async def func(, param) -> async def func(param)
            import re
            content = re.sub(
                r'async def (\w+)\(,\s*([^)]+)\)',
                r'async def \1(\2)',
                content
            )
            if re.search(r'async def (\w+)\(,\s*([^)]+)\)', original_content):
                fixed = True

            # Fix 4: Missing closing parentheses in function definitions
            # Pattern: async def func(param: -> async def func(param):
            content = re.sub(
                r'async def (\w+)\(([^)]*):\s*(\w+):\s*User = Depends\(([^)]+)\):',
                r'async def \1(\2, \3: User = Depends(\4)):',
                content
            )
            if re.search(r'async def (\w+)\(([^)]*):\s*(\w+):\s*User = Depends\(([^)]+)\):', original_content):
                fixed = True

            # Fix 5: Extra closing parentheses at end of functions
            # Pattern: } ))))))))))))))))))) -> }
            content = re.sub(r'\}\s*\){10,}', '}', content)
            if re.search(r'\}\s*\){10,}', original_content):
                fixed = True

            # Fix 6: Remove extra parentheses in function calls
            # Pattern: func(, param) -> func(param)
            content = re.sub(r'\(\s*,', '(', content)
            if re.search(r'\(\s*,', original_content):
                fixed = True

            # Fix 7: Fix malformed docstrings with extra quotes
            content = re.sub(r'"""\s*\'', '"""', content)
            if re.search(r'"""\s*\'', original_content):
                fixed = True

            if fixed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing {file_path}: {e}")

        return False

    def fix_empty_function_bodies(self, file_path: Path) -> bool:
        """Fix empty function bodies that cause syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Add pass statements to empty function bodies
            import re
            content = re.sub(
                r'def\s+(\w+)\s*\([^)]*\):\s*\n\s*"""[^"]*"""\s*\n\s*(?!\s)',
                r'def \1(\2):\n        """\3"""\n        pass\n        ',
                content
            )

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing empty functions in {file_path}: {e}")

        return False

    def fix_import_statements(self, file_path: Path) -> bool:
        """Fix malformed import statements."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix incomplete import statements
            import re
            content = re.sub(
                r'from\s+(\w+)\s*\nfrom\s+(\w+)',
                r'from \1 import \1\nfrom \2 import \2',
                content
            )

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            self.errors.append(f"Error fixing imports in {file_path}: {e}")

        return False

    def process_all_files(self):
        """Process all Python files and fix syntax errors."""
        print("🔧 Establishing stable compilation baseline...")

        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if self.should_process_file(file_path):
                        python_files.append(file_path)

        print(f"📁 Found {len(python_files)} Python files to process")

        for file_path in python_files:
            try:
                # Try to compile the file first
                import py_compile
                py_compile.compile(str(file_path), doraise=True)
                continue  # File compiles fine, skip it
            except (SyntaxError, IndentationError):
                # File has syntax errors, try to fix them
                print(f"🔧 Fixing syntax errors in {file_path}")

                fixed = False
                fixed |= self.fix_common_syntax_errors(file_path)
                fixed |= self.fix_empty_function_bodies(file_path)
                fixed |= self.fix_import_statements(file_path)

                if fixed:
                    self.fixed_files.append(str(file_path))

                    # Verify the fix worked
                    try:
                        py_compile.compile(str(file_path), doraise=True)
                        print(f"✅ Successfully fixed {file_path}")
                    except (SyntaxError, IndentationError) as e:
                        print(f"❌ Still has syntax errors: {file_path} - {e}")
                        self.errors.append(f"Failed to fix {file_path}: {e}")

        print(f"\n📊 Summary:")
        print(f"   Files fixed: {len(self.fixed_files)}")
        print(f"   Errors encountered: {len(self.errors)}")

        if self.fixed_files:
            print(f"\n✅ Fixed files:")
            for file in self.fixed_files:
                print(f"   - {file}")

        if self.errors:
            print(f"\n❌ Errors:")
            for error in self.errors:
                print(f"   - {error}")

def main():
    """Main entry point."""
    fixer = StableBaselineFixer()
    fixer.process_all_files()

    # Final compilation check
    print("\n🔍 Final compilation check...")
    import subprocess
    result = subprocess.run([
        'find', '.', '-name', '*.py', '-type', 'f',
        '-exec', 'python3', '-m', 'py_compile', '{}', ';'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("🎉 All Python files compile successfully!")
    else:
        print("⚠️  Some files still have syntax errors:")
        print(result.stderr)

if __name__ == "__main__":
    main()
