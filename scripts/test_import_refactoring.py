#!/usr/bin/env python3
"""
Test Import Refactoring Script

This script tests the import refactoring approach by:
1. Scanning for relative imports
2. Validating the suggested fixes
3. Testing the refactored imports
4. Ensuring no regressions are introduced
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import importlib.util

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from import_validator import ImportValidator, ImportIssue

class ImportRefactoringTester:
    """Tests the import refactoring process."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.validator = ImportValidator(str(self.project_root))
        self.test_results = []
    
    def run_comprehensive_test(self) -> bool:
        """Run comprehensive import refactoring tests."""
        print("🔍 Starting comprehensive import refactoring tests...")
        
        tests = [
            self.test_import_detection,
            self.test_suggestion_generation,
            self.test_import_fixing,
            self.test_import_validation,
            self.test_no_regressions
        ]
        
        all_passed = True
        for test_func in tests:
            print(f"\n📋 Running {test_func.__name__}...")
            try:
                result = test_func()
                if result:
                    print(f"  ✅ {test_func.__name__} passed")
                else:
                    print(f"  ❌ {test_func.__name__} failed")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {test_func.__name__} failed with error: {e}")
                all_passed = False
        
        return all_passed
    
    def test_import_detection(self) -> bool:
        """Test that relative imports are properly detected."""
        print("  Scanning for relative imports...")
        
        # Scan the svgx_engine directory
        issues = self.validator.scan_directory("svgx_engine")
        
        relative_imports = [i for i in issues if i.issue_type == "relative_import"]
        
        print(f"  Found {len(relative_imports)} relative imports")
        
        if not relative_imports:
            print("  ⚠️  No relative imports found - this might be good or indicate an issue")
            return True
        
        # Check that we can detect the common patterns
        expected_patterns = [
            "from ..utils.",
            "from ..models.",
            "from ..services.",
            "from .",
            "from .."
        ]
        
        found_patterns = set()
        for issue in relative_imports:
            for pattern in expected_patterns:
                if pattern in issue.import_statement:
                    found_patterns.add(pattern)
        
        print(f"  Detected patterns: {found_patterns}")
        
        return len(found_patterns) > 0
    
    def test_suggestion_generation(self) -> bool:
        """Test that appropriate absolute import suggestions are generated."""
        print("  Testing suggestion generation...")
        
        issues = self.validator.scan_directory("svgx_engine")
        relative_imports = [i for i in issues if i.issue_type == "relative_import"]
        
        suggestions_with_fixes = [i for i in relative_imports if i.suggested_fix]
        
        print(f"  Generated {len(suggestions_with_fixes)} suggestions out of {len(relative_imports)} issues")
        
        # Check that suggestions follow expected patterns
        valid_suggestions = 0
        for issue in suggestions_with_fixes:
            if any(pattern in issue.suggested_fix for pattern in [
                "from svgx_engine.",
                "from arx_svg_parser."
            ]):
                valid_suggestions += 1
        
        print(f"  Valid suggestions: {valid_suggestions}/{len(suggestions_with_fixes)}")
        
        return valid_suggestions > 0
    
    def test_import_fixing(self) -> bool:
        """Test the import fixing functionality with a dry run."""
        print("  Testing import fixing (dry run)...")
        
        issues = self.validator.scan_directory("svgx_engine")
        
        if not issues:
            print("  No issues to fix")
            return True
        
        # Run a dry run
        stats = self.validator.fix_imports(issues, dry_run=True)
        
        print(f"  Dry run results:")
        print(f"    Files that would be processed: {stats['files_processed']}")
        print(f"    Imports that would be fixed: {stats['imports_fixed']}")
        print(f"    Errors: {stats['errors']}")
        
        return stats['errors'] == 0
    
    def test_import_validation(self) -> bool:
        """Test that the refactored imports are valid."""
        print("  Testing import validation...")
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy a few test files
            test_files = [
                "svgx_engine/services/logic_engine.py",
                "svgx_engine/services/database.py",
                "svgx_engine/utils/errors.py"
            ]
            
            for file_path in test_files:
                if Path(file_path).exists():
                    dest_path = temp_path / Path(file_path).name
                    shutil.copy2(file_path, dest_path)
            
            # Test that we can import the modules
            try:
                # Add the project root to Python path
                sys.path.insert(0, str(self.project_root))
                
                # Try importing key modules
                test_imports = [
                    "svgx_engine.services.logic_engine",
                    "svgx_engine.services.database",
                    "svgx_engine.utils.errors"
                ]
                
                successful_imports = 0
                for module_name in test_imports:
                    try:
                        module = importlib.import_module(module_name)
                        successful_imports += 1
                        print(f"    ✅ Successfully imported {module_name}")
                    except ImportError as e:
                        print(f"    ❌ Failed to import {module_name}: {e}")
                
                return successful_imports > 0
                
            except Exception as e:
                print(f"    ❌ Import validation failed: {e}")
                return False
    
    def test_no_regressions(self) -> bool:
        """Test that no regressions are introduced."""
        print("  Testing for regressions...")
        
        # Check that existing functionality still works
        try:
            # Test that we can still run basic tests
            test_scripts = [
                "tests/svgx_engine/test_simple_imports.py",
                "tests/svgx_engine/test_basic_imports.py"
            ]
            
            successful_tests = 0
            for test_script in test_scripts:
                if Path(test_script).exists():
                    try:
                        result = subprocess.run(
                            [sys.executable, test_script],
                            capture_output=True,
                            text=True,
                            cwd=self.project_root,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            successful_tests += 1
                            print(f"    ✅ {test_script} passed")
                        else:
                            print(f"    ❌ {test_script} failed: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        print(f"    ⏰ {test_script} timed out")
                    except Exception as e:
                        print(f"    ❌ {test_script} failed with error: {e}")
            
            return successful_tests > 0
            
        except Exception as e:
            print(f"    ❌ Regression test failed: {e}")
            return False
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("# Import Refactoring Test Report")
        report.append("")
        
        # Scan for issues
        issues = self.validator.scan_directory("svgx_engine")
        relative_imports = [i for i in issues if i.issue_type == "relative_import"]
        
        report.append(f"## Summary")
        report.append(f"- Total issues found: {len(issues)}")
        report.append(f"- Relative imports: {len(relative_imports)}")
        report.append(f"- Files with issues: {len(set(i.file_path for i in issues))}")
        report.append("")
        
        if relative_imports:
            report.append("## Relative Import Details")
            report.append("")
            
            # Group by file
            issues_by_file = {}
            for issue in relative_imports:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
            
            for file_path, file_issues in issues_by_file.items():
                report.append(f"### {file_path}")
                for issue in file_issues:
                    report.append(f"- Line {issue.line_number}: {issue.import_statement}")
                    if issue.suggested_fix:
                        report.append(f"  Suggested: {issue.suggested_fix}")
                report.append("")
        
        return "\n".join(report)

def main():
    """Main entry point for the import refactoring test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test import refactoring process")
    parser.add_argument("--report", help="Generate test report to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    tester = ImportRefactoringTester()
    
    # Run tests
    success = tester.run_comprehensive_test()
    
    # Generate report if requested
    if args.report:
        report = tester.generate_test_report()
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"\n📄 Test report written to {args.report}")
    
    if success:
        print("\n✅ All import refactoring tests passed!")
    else:
        print("\n❌ Some import refactoring tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 