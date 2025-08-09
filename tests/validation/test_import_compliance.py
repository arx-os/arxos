#!/usr/bin/env python3
"""
Import Compliance Test - Verify Absolute Import Usage
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ImportComplianceChecker:
    """
    Checker for import compliance across the codebase.

    This class verifies that all imports follow the established patterns:
    - No relative imports (from . or from ..)
    - All imports use absolute paths from the package root
    - Import statements are properly formatted
    """

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.svgx_engine_path = os.path.join(self.project_root, "svgx_engine")
        self.issues = []
        self.stats = {
            "files_checked": 0,
            "files_with_relative_imports": 0,
            "relative_imports_found": 0,
            "files_with_issues": 0
        }

    def check_all_files(self) -> Dict[str, Any]:
        """
        Check all Python files in the svgx_engine directory.

        Returns:
            Dictionary with compliance results and statistics
        """
        logger.info("Starting import compliance check...")

        python_files = self._find_python_files()
        logger.info(f"Found {len(python_files)} Python files to check")

        for file_path in python_files:
            self._check_file(file_path)

        return {
            "compliant": len(self.issues) == 0,
            "issues": self.issues,
            "statistics": self.stats
        }

    def _find_python_files(self) -> List[str]:
        """Find all Python files in the svgx_engine directory."""
        python_files = []

        for root, dirs, files in os.walk(self.svgx_engine_path):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def _check_file(self, file_path: str) -> None:
        """Check a single file for import compliance."""
        self.stats["files_checked"] += 1

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            relative_imports = self._find_relative_imports(content, file_path)

            if relative_imports:
                self.stats["files_with_relative_imports"] += 1
                self.stats["relative_imports_found"] += len(relative_imports)

                issue = {
                    "file": file_path,
                    "relative_imports": relative_imports,
                    "severity": "error"
                }
                self.issues.append(issue)
                self.stats["files_with_issues"] += 1

                logger.warning(f"Found {len(relative_imports)} relative imports in {file_path}")

        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")
            self.stats["files_with_issues"] += 1

    def _find_relative_imports(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find relative imports in file content."""
        relative_imports = []

        # Pattern to match relative imports
        patterns = [
            r'from \.\.?[a-zA-Z_][a-zA-Z0-9_.]* import',
            r'from \.\.?[a-zA-Z_][a-zA-Z0-9_.]* import \*',
            r'import \.\.?[a-zA-Z_][a-zA-Z0-9_.]*',
        ]

        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue

            for pattern in patterns:
                if re.search(pattern, line):
                    relative_imports.append({
                        "line_number": line_num,
                        "line_content": line,
                        "pattern": pattern
                    })
                    break

        return relative_imports

    def suggest_fixes(self, file_path: str) -> List[str]:
        """
        Suggest fixes for relative imports in a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of suggested fixes
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            fixes = []
            lines = content.split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()

                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue

                # Check for relative imports and suggest fixes
                if line.startswith('from .') or line.startswith('from ..'):
                    suggested_fix = self._suggest_import_fix(line, file_path)
                    if suggested_fix:
                        fixes.append(f"Line {line_num + 1}: {line} -> {suggested_fix}")

            return fixes

        except Exception as e:
            logger.error(f"Error suggesting fixes for {file_path}: {e}")
            return []

    def _suggest_import_fix(self, import_line: str, file_path: str) -> str:
        """
        Suggest a fix for a relative import line.

        Args:
            import_line: The import line to fix
            file_path: Path to the file containing the import

        Returns:
            Suggested absolute import line
        """
        # Extract the module path from the import the
        match = re.match(r'from (\.+)([a-zA-Z_][a-zA-Z0-9_.]*) import', import_line)
        if not match:
            return None

        dots, module_path = match.groups()
        num_dots = len(dots)

        # Calculate the relative path from the file to the svgx_engine root
        file_rel_path = os.path.relpath(file_path, self.svgx_engine_path)
        file_dir_depth = len(file_rel_path.split(os.sep)) - 1  # -1 for the file itself

        # Calculate how many levels up we need to go
        levels_up = num_dots - 1

        if levels_up > file_dir_depth:
            # This would go beyond the package root, which is invalid
            return None

        # Build the absolute import path
        if levels_up == 0:
            # Same directory
            absolute_path = f"svgx_engine.{module_path}"
        else:
            # Need to go up levels_up directories
            current_dir = os.path.dirname(file_rel_path)
            for _ in range(levels_up):
                current_dir = os.path.dirname(current_dir)

            if current_dir == '.':
                absolute_path = f"svgx_engine.{module_path}"
            else:
                absolute_path = f"svgx_engine.{current_dir.replace(os.sep, '.')}.{module_path}"

        # Replace the relative import with absolute import
        return import_line.replace(f"from {dots}{module_path}", f"from {absolute_path}")

    def generate_report(self) -> str:
        """Generate a comprehensive compliance report."""
        report = []
        report.append("=" * 80)
        report.append("IMPORT COMPLIANCE REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("SUMMARY:")
        report.append(f"  Files checked: {self.stats['files_checked']}")
        report.append(f"  Files with relative imports: {self.stats['files_with_relative_imports']}")
        report.append(f"  Total relative imports found: {self.stats['relative_imports_found']}")
        report.append(f"  Files with issues: {self.stats['files_with_issues']}")
        report.append("")

        if self.issues:
            report.append("ISSUES FOUND:")
            report.append("-" * 40)

            for issue in self.issues:
                report.append(f"File: {issue['file']}")
                report.append(f"Severity: {issue['severity']}")
                report.append("Relative imports:")

                for rel_import in issue['relative_imports']:
                    report.append(f"  Line {rel_import['line_number']}: {rel_import['line_content']}")

                # Suggest fixes
                fixes = self.suggest_fixes(issue['file'])
                if fixes:
                    report.append("Suggested fixes:")
                    for fix in fixes:
                        report.append(f"  {fix}")

                report.append("")
        else:
            report.append("✅ NO ISSUES FOUND - All imports are compliant!")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        report.append("1. Use absolute imports from the package root (svgx_engine.*)")
        report.append("2. Avoid relative imports (from . or from ..)")
        report.append("3. Import specific classes/functions rather than using 'import *'")
        report.append("4. Keep imports organized and grouped logically")
        report.append("")

        report.append("=" * 80)

        return "\n".join(report)

def test_import_compliance():
    """Test function to run import compliance check."""
    checker = ImportComplianceChecker()
    results = checker.check_all_files()

    print(checker.generate_report())

    # Assert that no relative imports are found
    assert results["compliant"], f"Found {len(results['issues'])} files with relative imports"

    return results

def test_specific_files():
    """Test specific files that should have been fixed."""
    checker = ImportComplianceChecker()

    # List of files that should now use absolute imports
    critical_files = [
        "svgx_engine/domain/services/building_service.py",
        "svgx_engine/domain/events/building_events.py",
        "svgx_engine/domain/repositories/building_repository.py",
        "svgx_engine/domain/entities/building.py",
        "svgx_engine/infrastructure/container.py",
        "svgx_engine/infrastructure/repositories/in_memory_building_repository.py",
        "svgx_engine/application/dto/building_dto.py",
        "svgx_engine/application/use_cases/building_use_cases.py"
    ]

    all_compliant = True

    for file_path in critical_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            relative_imports = checker._find_relative_imports(content, full_path)

            if relative_imports:
                print(f"❌ {file_path} still has relative imports:")
                for rel_import in relative_imports:
                    print(f"    Line {rel_import['line_number']}: {rel_import['line_content']}")
                all_compliant = False
            else:
                print(f"✅ {file_path} is compliant")
        else:
            print(f"⚠️  {file_path} not found")

    assert all_compliant, "Critical files still have relative imports"
    return True

if __name__ == "__main__":
    # Run the compliance check
    results = test_import_compliance()

    # Test specific files
    test_specific_files()

    print("\n🎉 All import compliance tests passed!")
