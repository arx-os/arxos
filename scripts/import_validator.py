#!/usr/bin/env python3
"""
Import System Validator and Refactoring Tool

This script validates and refactors import statements across the Arxos codebase
to ensure all imports use absolute paths for better maintainability and reliability.
"""

import os
import re
import sys
import ast
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImportType(Enum):
    """Types of imports that can be detected."""
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    STANDARD_LIBRARY = "standard_library"
    THIRD_PARTY = "third_party"

@dataclass
class ImportIssue:
    """Represents an import issue found in the codebase."""
    file_path: str
    line_number: int
    import_statement: str
    issue_type: str
    description: str
    suggested_fix: Optional[str] = None

class ImportValidator:
    """Validates and refactors import statements across the codebase."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.issues: List[ImportIssue] = []
        
        # Standard library modules (should not be converted)
        self.standard_library_modules = {
            'os', 'sys', 're', 'json', 'logging', 'typing', 'pathlib',
            'datetime', 'time', 'uuid', 'hashlib', 'base64', 'math',
            'statistics', 'collections', 'itertools', 'functools',
            'contextlib', 'io', 'tempfile', 'shutil', 'glob', 'fnmatch',
            'asyncio', 'threading', 'multiprocessing', 'subprocess',
            'urllib', 'http', 'socket', 'ssl', 'email', 'mimetypes',
            'csv', 'pickle', 'sqlite3', 'xml', 'html', 'urllib3',
            'unittest', 'pytest', 'doctest', 'traceback', 'inspect',
            'abc', 'enum', 'dataclasses', 'weakref', 'copy', 'pprint'
        }
        
        # Third-party modules (should not be converted)
        self.third_party_modules = {
            'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 'alembic',
            'psycopg2', 'redis', 'celery', 'requests', 'httpx',
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy',
            'pytest', 'pytest-asyncio', 'pytest-cov', 'black', 'flake8',
            'mypy', 'isort', 'pre-commit', 'jinja2', 'markdown',
            'pyyaml', 'toml', 'click', 'rich', 'tqdm', 'colorama',
            'python-dotenv', 'cryptography', 'bcrypt', 'jwt',
            'pillow', 'opencv-python', 'tensorflow', 'torch',
            'scikit-learn', 'xgboost', 'lightgbm', 'plotly',
            'bokeh', 'dash', 'streamlit', 'gradio', 'transformers',
            'openai', 'anthropic', 'langchain', 'llama-index'
        }
        
        # Project-specific import mappings
        self.import_mappings = {
            # SVGX Engine mappings
            'from ..utils.errors import': 'from svgx_engine.utils.errors import',
            'from ..models.database import': 'from svgx_engine.models.database import',
            'from ..services.logic_engine import': 'from svgx_engine.services.logic_engine import',
            'from ..database.models import': 'from svgx_engine.database.models import',
            'from ..config.settings import': 'from svgx_engine.config.settings import',
            
            # Arx SVG Parser mappings
            'from ..services.': 'from arx_svg_parser.services.',
            'from ..routers.': 'from arx_svg_parser.routers.',
            'from ..api.': 'from arx_svg_parser.api.',
            'from ..models.': 'from arx_svg_parser.models.',
            'from ..utils.': 'from arx_svg_parser.utils.',
            'from ..cli_commands.': 'from arx_svg_parser.cli_commands.',
            'from ..middleware.': 'from arx_svg_parser.middleware.',
            
            # Common relative patterns
            'from .': 'from svgx_engine.',
            'from ..': 'from svgx_engine.',
        }
    
    def scan_directory(self, directory: str) -> List[ImportIssue]:
        """Scan a directory for import issues."""
        directory_path = Path(directory)
        issues = []
        
        for file_path in directory_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue
                
            file_issues = self._analyze_file(file_path)
            issues.extend(file_issues)
        
        return issues
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during analysis."""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            'node_modules',
            'venv',
            'env',
            '.venv',
            'build',
            'dist',
            '*.egg-info',
            'migrations',
            'alembic',
        ]
        
        for pattern in skip_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    def _analyze_file(self, file_path: Path) -> List[ImportIssue]:
        """Analyze a single file for import issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                import_issues = self._analyze_line(line, line_num, file_path)
                issues.extend(import_issues)
                
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            issues.append(ImportIssue(
                file_path=str(file_path),
                line_number=0,
                import_statement="",
                issue_type="file_error",
                description=f"Could not analyze file: {e}"
            ))
        
        return issues
    
    def _analyze_line(self, line: str, line_num: int, file_path: Path) -> List[ImportIssue]:
        """Analyze a single line for import issues."""
        issues = []
        
        # Skip comments and empty lines
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            return issues
        
        # Check for relative imports
        relative_import_patterns = [
            r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*) import',
            r'from \.([a-zA-Z_][a-zA-Z0-9_]*) import',
            r'import \.\.([a-zA-Z_][a-zA-Z0-9_]*)',
            r'import \.([a-zA-Z_][a-zA-Z0-9_]*)',
        ]
        
        for pattern in relative_import_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                relative_path = match.group(1)
                suggested_fix = self._suggest_absolute_import(line, relative_path, file_path)
                
                issues.append(ImportIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    import_statement=line.strip(),
                    issue_type="relative_import",
                    description=f"Relative import found: {match.group(0)}",
                    suggested_fix=suggested_fix
                ))
        
        return issues
    
    def _suggest_absolute_import(self, line: str, relative_path: str, file_path: Path) -> Optional[str]:
        """Suggest an absolute import replacement."""
        # Try to map based on common patterns
        for pattern, replacement in self.import_mappings.items():
            if pattern in line:
                return line.replace(pattern, replacement)
        
        # Try to determine the correct absolute path based on file location
        try:
            relative_to_project = file_path.relative_to(self.project_root)
            if 'svgx_engine' in str(relative_to_project):
                # This is in the svgx_engine package
                return line.replace(f'from ..{relative_path}', f'from svgx_engine.{relative_path}')
            elif 'arx_svg_parser' in str(relative_to_project):
                # This is in the arx_svg_parser package
                return line.replace(f'from ..{relative_path}', f'from arx_svg_parser.{relative_path}')
        except ValueError:
            pass
        
        return None
    
    def generate_report(self, issues: List[ImportIssue]) -> str:
        """Generate a comprehensive report of import issues."""
        if not issues:
            return "✅ No import issues found!"
        
        report = []
        report.append("# Import Validation Report")
        report.append(f"Generated: {datetime.datetime.now().isoformat()}")
        report.append(f"Total issues found: {len(issues)}")
        report.append("")
        
        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        for issue_type, type_issues in issues_by_type.items():
            report.append(f"## {issue_type.replace('_', ' ').title()} Issues ({len(type_issues)})")
            report.append("")
            
            for issue in type_issues:
                report.append(f"### {issue.file_path}:{issue.line_number}")
                report.append(f"**Issue:** {issue.description}")
                report.append(f"**Line:** `{issue.import_statement}`")
                if issue.suggested_fix:
                    report.append(f"**Suggested Fix:** `{issue.suggested_fix}`")
                report.append("")
        
        return "\n".join(report)
    
    def fix_imports(self, issues: List[ImportIssue], dry_run: bool = True) -> Dict[str, int]:
        """Fix import issues by converting relative imports to absolute imports."""
        if dry_run:
            logger.info("DRY RUN MODE - No files will be modified")
        
        stats = {
            'files_processed': 0,
            'imports_fixed': 0,
            'errors': 0
        }
        
        # Group issues by file
        issues_by_file = {}
        for issue in issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            try:
                if self._fix_file_imports(file_path, file_issues, dry_run):
                    stats['files_processed'] += 1
                    stats['imports_fixed'] += len([i for i in file_issues if i.suggested_fix])
            except Exception as e:
                logger.error(f"Error fixing imports in {file_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def _fix_file_imports(self, file_path: str, issues: List[ImportIssue], dry_run: bool) -> bool:
        """Fix imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            modified = False
            
            # Sort issues by line number in descending order to avoid line number shifts
            sorted_issues = sorted(issues, key=lambda x: x.line_number, reverse=True)
            
            for issue in sorted_issues:
                if issue.suggested_fix and issue.line_number <= len(lines):
                    line_index = issue.line_number - 1
                    original_line = lines[line_index]
                    new_line = issue.suggested_fix
                    
                    if original_line.strip() != new_line.strip():
                        if not dry_run:
                            lines[line_index] = new_line
                            logger.info(f"Fixed import in {file_path}:{issue.line_number}")
                        else:
                            logger.info(f"Would fix import in {file_path}:{issue.line_number}")
                            logger.info(f"  From: {original_line.strip()}")
                            logger.info(f"  To:   {new_line.strip()}")
                        
                        modified = True
            
            if modified and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
            
            return modified
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False

def main():
    """Main entry point for the import validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate and fix import statements")
    parser.add_argument("--scan", action="store_true", help="Scan for import issues")
    parser.add_argument("--fix", action="store_true", help="Fix import issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--directory", default="svgx_engine", help="Directory to scan (default: svgx_engine)")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    validator = ImportValidator()
    
    if args.scan:
        logger.info(f"Scanning {args.directory} for import issues...")
        issues = validator.scan_directory(args.directory)
        
        report = validator.generate_report(issues)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            logger.info(f"Report written to {args.output}")
        else:
            print(report)
        
        return len(issues) == 0
    
    elif args.fix:
        logger.info(f"Fixing import issues in {args.directory}...")
        issues = validator.scan_directory(args.directory)
        
        if not issues:
            logger.info("No import issues found!")
            return True
        
        stats = validator.fix_imports(issues, dry_run=args.dry_run)
        
        logger.info(f"Import fixing complete:")
        logger.info(f"  Files processed: {stats['files_processed']}")
        logger.info(f"  Imports fixed: {stats['imports_fixed']}")
        logger.info(f"  Errors: {stats['errors']}")
        
        return stats['errors'] == 0
    
    else:
        parser.print_help()
        return False

if __name__ == "__main__":
    import datetime
    success = main()
    sys.exit(0 if success else 1) 