#!/usr/bin/env python3
"""
Fix Critical Syntax Errors Only

This script focuses on fixing only the most critical syntax errors
that prevent basic compilation, without attempting complex fixes.
"""

import os
import sys
from pathlib import Path


def fix_critical_syntax_errors():
    """Fix the most critical syntax errors that prevent compilation."""

    # Directories to exclude
    exclude_dirs = {
        'venv', '__pycache__', '.git', 'node_modules',
        '.pytest_cache', '.mypy_cache', '.coverage'
    }

    def should_process_file(file_path):
        """Check if file should be processed."""
        for part in file_path.parts:
            if part in exclude_dirs:
                return False
        return file_path.suffix == '.py'

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if should_process_file(file_path):
                    python_files.append(file_path)

    print(f"🔍 Found {len(python_files)} Python files to check")

    fixed_count = 0
    error_count = 0

    # Import here for access to the exception class
    import py_compile
    import re

    def insert_pass_for_empty_blocks(text: str) -> tuple[str, bool]:
        """Insert 'pass' for empty def/class blocks to fix IndentationError."""
        lines = text.splitlines()
        changed = False
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r'^(?P<indent>\s*)(def|class)\s+[^:]+:\s*(#.*)?$', line)
            if m:
                base_indent = m.group('indent')
                next_i = i + 1
                # Skip blank lines and inline comments to find the next significant line
                while next_i < len(lines) and (lines[next_i].strip() == '' or lines[next_i].lstrip().startswith('#')):
                    next_i += 1
                if next_i >= len(lines):
                    # End of file: insert pass
                    lines.insert(i + 1, base_indent + '    pass')
                    changed = True
                    i += 2
                    continue
                # Determine indentation of next significant line
                next_line = lines[next_i]
                next_indent_len = len(next_line) - len(next_line.lstrip(' '))
                base_indent_len = len(base_indent)
                if next_indent_len <= base_indent_len:
                    # Not indented; insert pass directly after def/class
                    lines.insert(i + 1, base_indent + '    pass')
                    changed = True
                    i += 2
                    continue
            i += 1
        return ('\n'.join(lines) + ('\n' if text.endswith('\n') else ''), changed)

    for file_path in python_files:
        try:
            # Try to compile the file
            py_compile.compile(str(file_path), doraise=True)
            continue  # File compiles fine
        except (py_compile.PyCompileError, SyntaxError, IndentationError):
            # File has syntax errors, try to fix them
            print(f"🔧 Fixing critical syntax errors in {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                fixed = False

                # Fix 1: Unterminated string literals ("""" -> """)
                if '""""' in content:
                    content = content.replace('""""', '"""')
                    fixed = True

                # Fix 1b: Unterminated string literals for single quotes ('''' -> ''')
                if "''''" in content:
                    content = content.replace("''''", "'''")
                    fixed = True

                # Fix 2: Extra quotes at end of docstrings ("""' -> """) and ('''" -> ''')
                if '"""\'' in content:
                    content = content.replace('"""\'', '"""')
                    fixed = True
                if "'''\"" in content:
                    content = content.replace("'''\"", "'''")
                    fixed = True

                # Fix 3: Malformed function signatures with extra commas
                # Pattern: async def func(, param) -> async def func(param)
                if re.search(r'async def (\w+)\(,\s*([^)]+)\)', content):
                    content = re.sub(
                        r'async def (\w+)\(,\s*([^)]+)\)',
                        r'async def \1(\2)',
                        content
                    )
                    fixed = True

                # Fix 4: Extra closing parentheses at end of lines (e.g., main() )) -> main())
                content_new = re.sub(r'(\b\w+\([^\)]*\))\s*\)\s*$', r'\1', content, flags=re.MULTILINE)
                if content_new != content:
                    content = content_new
                    fixed = True

                # Fix 5: Remove stray trailing quote after a closing parenthesis at EOL: ... )" or ... )'
                content_new = re.sub(r'\)\s*["\']\s*$', ')', content, flags=re.MULTILINE)
                if content_new != content:
                    content = content_new
                    fixed = True

                # Fix 6: Remove stray trailing quote after a triple-quoted close followed by ) ] , at EOL
                # Examples: """)" -> """),  ''')," -> '''),
                content_new = re.sub(r'((?:"""|\'\'\'))(\s*[\)\],]+)\s*["\']\s*$', r'\1\2', content, flags=re.MULTILINE)
                if content_new != content:
                    content = content_new
                    fixed = True

                # Fix 7: Insert pass for empty def/class blocks
                content_after_pass, changed_pass = insert_pass_for_empty_blocks(content)
                if changed_pass:
                    content = content_after_pass
                    fixed = True

                if fixed:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    # Verify the fix worked
                    try:
                        py_compile.compile(str(file_path), doraise=True)
                        print(f"✅ Successfully fixed {file_path}")
                        fixed_count += 1
                    except (py_compile.PyCompileError, SyntaxError, IndentationError) as e:
                        print(f"❌ Still has syntax errors: {file_path} - {e}")
                        error_count += 1
                else:
                    # No simple fix applied; mark as error to investigate later
                    error_count += 1
                    print(f"⚠️  No simple fix applied for {file_path}")

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                error_count += 1

    print(f"\n📊 Summary:")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Files with errors: {error_count}")

    return fixed_count, error_count


def main():
    """Main entry point."""
    print("🔧 Fixing critical syntax errors...")

    fixed, errors = fix_critical_syntax_errors()

    # Final compilation check
    print("\n🔍 Final compilation check...")
    import subprocess
    result = subprocess.run([
        'bash', '-lc',
        "find . -name '*.py' -type f -print0 | xargs -0 -n1 python3 -m py_compile"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("🎉 All Python files compile successfully!")
        return True
    else:
        print("⚠️  Some files still have syntax errors.")
        # Show a small snippet of stderr to avoid flooding
        print(result.stderr.splitlines()[:20])
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
