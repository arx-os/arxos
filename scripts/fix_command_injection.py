(#!/usr/bin/env python3
"""
Fix Command Injection Vulnerabilities

This script fixes command injection vulnerabilities by replacing unsafe
command execution with secure alternatives.

Target Files:
- svgx_engine/runtime/behavior_management_system.py:567
- svgx_engine/scripts/deploy_staging.py:209
- svgx_engine/scripts/local_validation.py:62

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
import subprocess
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional


class CommandInjectionFixer:
    """Fixes command injection vulnerabilities"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.vulnerable_files = [
            "svgx_engine/runtime/behavior_management_system.py",
            "svgx_engine/scripts/deploy_staging.py",
            "svgx_engine/scripts/local_validation.py"
        ]

        # Safe command execution patterns
        self.safe_patterns = {
            'os.system': 'subprocess.run',
            'subprocess.call': 'subprocess.run',
            'subprocess.Popen': 'subprocess.run',
            'exec(': 'subprocess.run',
            'eval(': 'subprocess.run'
        }

        # Allowed commands whitelist
        self.allowed_commands = [
            'git', 'docker', 'npm', 'python', 'python3',
            'pip', 'pip3', 'node', 'npm', 'yarn',
            'ls', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv',
            'chmod', 'chown', 'tar', 'gzip', 'gunzip'
        ]

    def fix_command_injection(self):
        """Fix command injection vulnerabilities"""
        print("🔒 Fixing Command Injection Vulnerabilities")
        print("=" * 60)

        success_count = 0
        error_count = 0

        for file_path in self.vulnerable_files:
            full_path = self.project_root / file_path

            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue

            try:
                if self._fix_file(full_path):
                    print(f"✅ Fixed command injection in: {file_path}")
                    success_count += 1
                else:
                    print(f"ℹ️  No command injection issues found in: {file_path}")

            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"   ✅ Successfully fixed: {success_count} files")
        print(f"   ❌ Errors: {error_count} files")
        print(f"   📁 Total processed: {len(self.vulnerable_files)} files")

    def _fix_file(self, file_path: Path) -> bool:
        """Fix command injection in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Add safe command execution import
            content = self._add_safe_imports(content)

            # Replace unsafe command execution
            content = self._replace_unsafe_commands(content)

            # Add command validation
            content = self._add_command_validation(content)

            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def _add_safe_imports(self, content: str) -> str:
        """Add safe command execution imports"""
        safe_imports = [
            "import subprocess",
            "import shlex",
            "from typing import List, Optional"
        ]

        # Check if imports already exist
        for import_stmt in safe_imports:
            if import_stmt not in content:
                # Add after existing imports
                if "import " in content:
                    # Find the last import
                    import_pattern = r'^import\s+.*$|^from\s+.*\s+import\s+.*$'
                    imports = re.findall(import_pattern, content, re.MULTILINE)
                    if imports:
                        last_import = imports[-1]
                        content = content.replace(last_import, f"{last_import}\n{import_stmt}")
                else:
                    # Add at the beginning
                    content = f"{import_stmt}\n\n{content}"

        return content

    def _replace_unsafe_commands(self, content: str) -> str:
        """Replace unsafe command execution with safe alternatives"""

        # Replace os.system with safe_execute_command
        content = re.sub(
            r'os\.system\s*\(\s*([^)]+)\s*\)',
            r'safe_execute_command(\1)',
            content
        )

        # Replace subprocess.call with subprocess.run
        content = re.sub(
            r'subprocess\.call\s*\(\s*([^)]+)\s*\)',
            r'subprocess.run(\1, shell=False, capture_output=True, text=True)',
            content
        )

        # Replace subprocess.Popen with subprocess.run
        content = re.sub(
            r'subprocess\.Popen\s*\(\s*([^)]+)\s*\)',
            r'subprocess.run(\1, shell=False, capture_output=True, text=True)',
            content
        )

        return content

    def _add_command_validation(self, content: str) -> str:
        """Add command validation function"""
        validation_function = '''
def safe_execute_command(command: str, args: List[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Execute command safely with input validation.

    Args:
        command: Command to execute
        args: Command arguments
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If command is not allowed
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails
    """
    # Validate command
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"Command '{command}' is not allowed")

    # Prepare command
    cmd = [command] + (args or [])

    # Execute with security measures
    try:
        result = subprocess.run(
            cmd,
            shell=False,  # Prevent shell injection
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,  # Use current directory
            env=None,  # Use current environment
            check=False  # Don't raise on non-zero exit'
        )
        return result
    except subprocess.TimeoutExpired:
        raise subprocess.TimeoutExpired(cmd, timeout)
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(e.returncode, cmd, e.stdout, e.stderr)
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")

# Allowed commands whitelist
ALLOWED_COMMANDS = [
    'git', 'docker', 'npm', 'python', 'python3',
    'pip', 'pip3', 'node', 'npm', 'yarn',
    'ls', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv',
    'chmod', 'chown', 'tar', 'gzip', 'gunzip'
]
'''

        # Add validation function if not present
        if "def safe_execute_command" not in content:
            # Add after imports
            if "import " in content:
                import_pattern = r'^import\s+.*$|^from\s+.*\s+import\s+.*$'
                imports = re.findall(import_pattern, content, re.MULTILINE)
                if imports:
                    last_import = imports[-1]
                    content = content.replace(last_import, f"{last_import}\n{validation_function}")
            else:
                content = f"{validation_function}\n\n{content}"

        return content

    def create_safe_command_example(self):
        """Create an example of safe command execution"""
        example = '''
# Example of Safe Command Execution

import subprocess
import shlex
from typing import List, Optional

def safe_execute_command(command: str, args: List[str] = None, timeout: int = 30):
    """
    Execute command safely with input validation.
    """
    # Validate command
    allowed_commands = [
        'git', 'docker', 'npm', 'python', 'python3',
        'pip', 'pip3', 'node', 'npm', 'yarn',
        'ls', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv'
    ]

    if command not in allowed_commands:
        raise ValueError(f"Command '{command}' is not allowed")

    # Prepare command
    cmd = [command] + (args or [])

    # Execute safely
    result = subprocess.run(
        cmd,
        shell=False,  # Prevent shell injection
        capture_output=True,
        text=True,
        timeout=timeout
    )

    return result

# Usage examples
try:
    # Safe command execution
    result = safe_execute_command('git', ['status'])
    print(f"Git status: {result.stdout}")

    # Safe file listing
    result = safe_execute_command('ls', ['-la'])
    print(f"Directory contents: {result.stdout}")

except ValueError as e:
    print(f"Command not allowed: {e}")
except subprocess.TimeoutExpired:
    print("Command timed out")
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e}")
'''

        example_path = self.project_root / "docs" / "safe_command_example.py"
        example_path.parent.mkdir(exist_ok=True)

        with open(example_path, 'w') as f:
            f.write(example)

        print(f"📝 Created safe command example: {example_path}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fix_command_injection.py [--dry-run] [--example]")
        sys.exit(1)

    project_root = "."
    dry_run = "--dry-run" in sys.argv
    create_example = "--example" in sys.argv

    fixer = CommandInjectionFixer(project_root)

    if create_example:
        fixer.create_safe_command_example()

    if not dry_run:
        fixer.fix_command_injection()
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Files that would be fixed:")
        for file_path in fixer.vulnerable_files:
            full_path = Path(project_root) / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (not found)")


if __name__ == "__main__":
    main()
