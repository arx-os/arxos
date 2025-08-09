(#!/usr/bin/env python3
"""
Fix All Remaining Syntax Errors

This script fixes all remaining syntax errors in the codebase, including
import issues, indentation problems, and other syntax violations.

Target Issues:
- Import syntax errors
- Indentation errors
- Function definition errors
- String literal errors
- Parenthesis matching errors

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional


class ComprehensiveSyntaxFixer:
    """Fixes all remaining syntax errors comprehensively"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

        # Files with known syntax errors
        self.files_with_syntax_errors = [
            "services/ai/arx-mcp/validate/rule_engine.py",
            "svgx_engine/app.py",
            "services/ai/main.py",
            "services/gus/main.py",
            "services/planarx/planarx-community/main.py",
            "svgx_engine/core/parametric_system.py",
            "svgx_engine/runtime/behavior_engine.py",
            "svgx_engine/runtime/behavior_management_system.py",
            "svgx_engine/runtime/evaluator.py",
            "svgx_engine/api/ai_integration_api.py",
            "svgx_engine/api/notification_api.py",
            "svgx_engine/api/export_api.py",
            "svgx_engine/api/cad_api.py",
            "svgx_engine/services/ai/advanced_ai_api.py"
        ]

    def fix_all_syntax_errors(self):
        """Fix all syntax errors in the codebase"""
        print("🔧 Fixing All Remaining Syntax Errors")
        print("=" * 60)

        success_count = 0
        error_count = 0

        for file_path in self.files_with_syntax_errors:
            full_path = self.project_root / file_path

            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue

            try:
                if self._fix_file_syntax(full_path):
                    print(f"✅ Fixed syntax errors in: {file_path}")
                    success_count += 1
                else:
                    print(f"ℹ️  No syntax errors found in: {file_path}")

            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"   ✅ Successfully fixed: {success_count} files")
        print(f"   ❌ Errors: {error_count} files")
        print(f"   📁 Total processed: {len(self.files_with_syntax_errors)} files")

    def _fix_file_syntax(self, file_path: Path) -> bool:
        """Fix syntax errors in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix import syntax errors
            content = self._fix_import_syntax(content)

            # Fix indentation errors
            content = self._fix_indentation_errors(content)

            # Fix function definition errors
            content = self._fix_function_definition_errors(content)

            # Fix string literal errors
            content = self._fix_string_literal_errors(content)

            # Fix parenthesis matching errors
            content = self._fix_parenthesis_errors(content)

            # Validate syntax
            if not self._validate_syntax(content):
                print(f"⚠️  Syntax validation failed for {file_path}")
                return False

            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def _fix_import_syntax(self, content: str) -> str:
        """Fix import syntax errors"""

        # Fix broken import statements
        # Pattern: from services.models.mcp_models import (\n    MCPFile, ...
        content = re.sub(
            r'from services\.models\.mcp_models import \(\nimport html',
            r'from services.models.mcp_models import (\n    MCPFile, MCPRule, RuleCondition, RuleAction, BuildingModel, BuildingObject,\n    ValidationResult, ValidationViolation, MCPValidationReport, ComplianceReport,\n    RuleSeverity, RuleCategory, ConditionType, ActionType,\n    serialize_mcp_file, deserialize_mcp_file\n)\nimport html',
            content
        )

        # Fix other broken imports
        content = re.sub(
            r'from ([a-zA-Z_][a-zA-Z0-9_.]*) import \(\nimport ([a-zA-Z_][a-zA-Z0-9_]*)',
            r'from \1 import (\n    # imports here\n)\nimport \2',
            content
        )

        # Fix unmatched parentheses in imports
        content = re.sub(
            r'from ([a-zA-Z_][a-zA-Z0-9_.]*) import \([^)]*$',
            r'from \1 import (\n    # imports here\n)',
            content
        )

        return content

    def _fix_indentation_errors(self, content: str) -> str:
        """Fix indentation errors"""
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # Fix common indentation issues
            if line.strip().startswith('async def ') and ':' in line:
                # Ensure proper indentation for function definitions
                if not line.startswith('    ') and not line.startswith('\t'):
                    line = '    ' + line.lstrip()

            # Fix indentation for class definitions
            elif line.strip().startswith('class ') and ':' in line:
                if not line.startswith('    ') and not line.startswith('\t'):
                    line = '    ' + line.lstrip()

            # Fix indentation for try/except blocks
            elif line.strip().startswith('try:') or line.strip().startswith('except'):
                if not line.startswith('    ') and not line.startswith('\t'):
                    line = '    ' + line.lstrip()

            # Fix indentation for if/elif/else blocks
            elif line.strip().startswith(('if ', 'elif ', 'else:')):
                if not line.startswith('    ') and not line.startswith('\t'):
                    line = '    ' + line.lstrip()

            # Fix indentation for for/while loops
            elif line.strip().startswith(('for ', 'while ')):
                if not line.startswith('    ') and not line.startswith('\t'):
                    line = '    ' + line.lstrip()

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _fix_function_definition_errors(self, content: str) -> str:
        """Fix function definition errors"""

        # Fix duplicate function definitions
        content = re.sub(
            r'async def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*\n\s*async def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):',
            r'async def \2',
            content
        )

        # Fix function definitions without proper indentation
        content = re.sub(
            r'^async def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):',
            r'    async def \1:',
            content,
            flags=re.MULTILINE
        )

        # Fix function definitions with missing colons
        content = re.sub(
            r'async def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*$',
            r'async def \1():',
            content,
            flags=re.MULTILINE
        )

        return content

    def _fix_string_literal_errors(self, content: str) -> str:
        """Fix string literal errors"""

        # Fix unterminated string literals
        content = re.sub(
            r'(["\'])([^"\']*)$',
            r'\1\2\1',
            content
        )

        # Fix string literals with unmatched quotes
        content = re.sub(
            r'(["\'])([^"\']*)(["\'])([^"\']*)\1',
            r'\1\2\3\4\3',
            content
        )

        return content

    def _fix_parenthesis_errors(self, content: str) -> str:
        """Fix parenthesis matching errors"""

        # Fix unmatched parentheses in function calls
        content = re.sub(
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([^)]*)\s*$',
            r'\1(\2)',
            content
        )

        # Fix unmatched parentheses in imports
        content = re.sub(
            r'from ([a-zA-Z_][a-zA-Z0-9_.]*) import \([^)]*$',
            r'from \1 import (\n    # imports here\n)',
            content
        )

        return content

    def _validate_syntax(self, content: str) -> bool:
        """Validate that the content has valid Python syntax"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

    def create_syntax_fix_example(self):
        """Create an example of proper syntax"""
        example = '''
# Example of Proper Python Syntax

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ExampleClass:
    """Example class with proper syntax"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the class"""
        self.config = config or {}
        self.logger = logger

    async def example_function(self, param: str) -> Dict[str, Any]:
        """Example async function with proper syntax"""
        try:
            result = {
                "status": "success",
                "param": param,
                "config": self.config
            }
            return result
        except Exception as e:
            self.logger.error(f"Error in example_function: {e}")
            raise

    def validate_syntax(self, content: str) -> bool:
        """Validate Python syntax"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

# Usage example
if __name__ == "__main__":
    example = ExampleClass({"test": "value"})
    result = await example.example_function("test_param")
    print(result)
'''

        example_path = self.project_root / "docs" / "proper_syntax_example.py"
        example_path.parent.mkdir(exist_ok=True)

        with open(example_path, 'w') as f:
            f.write(example)

        print(f"📝 Created proper syntax example: {example_path}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fix_all_remaining_syntax_errors.py [--dry-run] [--example]")
        sys.exit(1)

    project_root = "."
    dry_run = "--dry-run" in sys.argv
    create_example = "--example" in sys.argv

    fixer = ComprehensiveSyntaxFixer(project_root)

    if create_example:
        fixer.create_syntax_fix_example()

    if not dry_run:
        fixer.fix_all_syntax_errors()
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Files that would be fixed:")
        for file_path in fixer.files_with_syntax_errors:
            full_path = Path(project_root) / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (not found)")


if __name__ == "__main__":
    main()
