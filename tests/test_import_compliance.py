#!/usr/bin/env python3
"""
Import Compliance Tests for Arxos

This module contains comprehensive tests for import compliance,
validation, and refactoring functionality.
"""

import os
import sys
import re
import importlib
import unittest
from pathlib import Path
from typing import List, Dict, Set, Optional


class ImportComplianceTest(unittest.TestCase):
    """Test suite for import compliance and validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.python_files = self._find_python_files()
        self.relative_imports = []
        self.absolute_imports = []
        
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        
        # Directories to scan
        scan_dirs = [
            'svgx_engine',
            'arx_svg_parser',
            'arx-backend',
            'arx_common',
            'core',
            'services',
            'tests',
            'scripts'
        ]
        
        # Patterns to exclude
        exclude_patterns = [
            r'__pycache__',
            r'\.pyc$',
            r'\.pyo$',
            r'\.pyd$',
            r'\.git',
            r'node_modules',
            r'venv',
            r'env',
            r'\.env',
            r'import_refactoring_backup'
        ]
        
        for scan_dir in scan_dirs:
            dir_path = self.project_root / scan_dir
            if dir_path.exists():
                for py_file in dir_path.rglob("*.py"):
                    # Check if file should be excluded
                    if not any(re.search(pattern, str(py_file)) for pattern in exclude_patterns):
                        python_files.append(py_file)
        
        return python_files

    def test_no_relative_imports(self):
        """Test that no relative imports exist in the codebase."""
        relative_imports = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if self._is_relative_import(line):
                        relative_imports.append({
                            'file': str(file_path),
                            'line': line_num,
                            'import': line
                        })
                        
            except Exception as e:
                self.fail(f"Error reading {file_path}: {e}")
        
        if relative_imports:
            # Show first 10 relative imports
            error_msg = f"Found {len(relative_imports)} relative imports:\n"
            for imp in relative_imports[:10]:
                error_msg += f"  - {imp['file']}:{imp['line']}: {imp['import']}\n"
            
            if len(relative_imports) > 10:
                error_msg += f"  ... and {len(relative_imports) - 10} more\n"
            
            self.fail(error_msg)

    def _is_relative_import(self, line: str) -> bool:
        """Check if a line contains a relative import."""
        line = line.strip()
        return (line.startswith('from .') or 
                line.startswith('from ..') or 
                line.startswith('import .') or 
                line.startswith('import ..'))

    def test_import_syntax_validity(self):
        """Test that all import statements have valid syntax."""
        syntax_errors = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for basic import syntax
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        if not self._is_valid_import_syntax(line):
                            syntax_errors.append({
                                'file': str(file_path),
                                'line': line_num,
                                'import': line,
                                'error': 'Invalid import syntax'
                            })
                            
            except Exception as e:
                syntax_errors.append({
                    'file': str(file_path),
                    'line': 0,
                    'import': '',
                    'error': f"Error reading file: {e}"
                })
        
        if syntax_errors:
            error_msg = f"Found {len(syntax_errors)} import syntax errors:\n"
            for error in syntax_errors[:10]:
                error_msg += f"  - {error['file']}:{error['line']}: {error['import']} ({error['error']})\n"
            
            if len(syntax_errors) > 10:
                error_msg += f"  ... and {len(syntax_errors) - 10} more\n"
            
            self.fail(error_msg)

    def _is_valid_import_syntax(self, line: str) -> bool:
        """Check if an import line has valid syntax."""
        # Basic syntax validation
        if line.startswith('import '):
            # Check for valid import statement
            parts = line.split()
            if len(parts) < 2:
                return False
            
            # Check for valid module names
            module_part = parts[1]
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', module_part):
                return False
                
        elif line.startswith('from '):
            # Check for valid from import statement
            if ' import ' not in line:
                return False
            
            parts = line.split(' import ')
            if len(parts) != 2:
                return False
            
            module_part = parts[0].replace('from ', '')
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', module_part):
                return False
                
        else:
            return False
        
        return True

    def test_module_importability(self):
        """Test that all modules can be imported successfully."""
        # Key modules to test
        modules_to_test = [
            'svgx_engine',
            'svgx_engine.services',
            'svgx_engine.models',
            'svgx_engine.utils',
            'svgx_engine.behavior',
            'svgx_engine.parser',
            'svgx_engine.runtime',
            'arx_svg_parser',
            'arx_svg_parser.services',
            'arx_svg_parser.models',
            'arx_svg_parser.utils',
            'arx_svg_parser.api',
            'arx_svg_parser.routers',
            'arx_common',
            'arx_common.models',
            'arx_common.utils',
        ]
        
        failed_imports = []
        
        # Add project root to Python path
        original_path = sys.path.copy()
        sys.path.insert(0, str(self.project_root))
        
        try:
            for module in modules_to_test:
                try:
                    importlib.import_module(module)
                except ImportError as e:
                    failed_imports.append({
                        'module': module,
                        'error': str(e)
                    })
                except Exception as e:
                    failed_imports.append({
                        'module': module,
                        'error': f"Unexpected error: {e}"
                    })
        finally:
            sys.path = original_path
        
        if failed_imports:
            error_msg = f"Failed to import {len(failed_imports)} modules:\n"
            for imp in failed_imports:
                error_msg += f"  - {imp['module']}: {imp['error']}\n"
            
            self.fail(error_msg)

    def test_import_consistency(self):
        """Test that imports are consistent across the codebase."""
        import_patterns = {}
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Extract the import pattern
                        if line.startswith('import '):
                            module = line.split('import ')[1].split(',')[0].strip()
                            pattern = f"import {module}"
                        else:
                            # from import
                            parts = line.split(' import ')
                            if len(parts) == 2:
                                module = parts[0].replace('from ', '')
                                pattern = f"from {module} import"
                            else:
                                continue
                        
                        if pattern not in import_patterns:
                            import_patterns[pattern] = []
                        
                        import_patterns[pattern].append({
                            'file': str(file_path),
                            'line': line_num
                        })
                        
            except Exception as e:
                print(f"Warning: Error reading {file_path}: {e}")
        
        # Check for inconsistent import patterns
        inconsistencies = []
        for pattern, usages in import_patterns.items():
            if len(usages) > 1:
                # Check if all usages are consistent
                files = [usage['file'] for usage in usages]
                if len(set(files)) > 1:
                    inconsistencies.append({
                        'pattern': pattern,
                        'usages': usages
                    })
        
        if inconsistencies:
            error_msg = f"Found {len(inconsistencies)} import inconsistencies:\n"
            for inc in inconsistencies[:5]:
                error_msg += f"  - Pattern: {inc['pattern']}\n"
                for usage in inc['usages'][:3]:
                    error_msg += f"    - {usage['file']}:{usage['line']}\n"
                if len(inc['usages']) > 3:
                    error_msg += f"    ... and {len(inc['usages']) - 3} more\n"
            
            self.fail(error_msg)

    def test_circular_imports(self):
        """Test for potential circular imports."""
        # This is a basic check - more sophisticated analysis would be needed
        # for a complete circular import detection
        circular_imports = []
        
        # Check for obvious circular import patterns
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for imports of the same module
                lines = content.split('\n')
                imports = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
                
                # Check for potential circular imports
                for i, imp1 in enumerate(imports):
                    for j, imp2 in enumerate(imports[i+1:], i+1):
                        if self._could_be_circular(imp1, imp2):
                            circular_imports.append({
                                'file': str(file_path),
                                'import1': imp1,
                                'import2': imp2
                            })
                            
            except Exception as e:
                print(f"Warning: Error checking {file_path} for circular imports: {e}")
        
        if circular_imports:
            error_msg = f"Found {len(circular_imports)} potential circular imports:\n"
            for circ in circular_imports[:10]:
                error_msg += f"  - {circ['file']}:\n"
                error_msg += f"    - {circ['import1']}\n"
                error_msg += f"    - {circ['import2']}\n"
            
            if len(circular_imports) > 10:
                error_msg += f"  ... and {len(circular_imports) - 10} more\n"
            
            self.fail(error_msg)

    def _could_be_circular(self, imp1: str, imp2: str) -> bool:
        """Check if two imports could potentially be circular."""
        # Extract module names
        module1 = self._extract_module_name(imp1)
        module2 = self._extract_module_name(imp2)
        
        if not module1 or not module2:
            return False
        
        # Check if modules are related
        if module1.startswith(module2) or module2.startswith(module1):
            return True
        
        return False

    def _extract_module_name(self, import_line: str) -> Optional[str]:
        """Extract module name from import line."""
        if import_line.startswith('import '):
            return import_line.split('import ')[1].split(',')[0].strip()
        elif import_line.startswith('from '):
            parts = import_line.split(' import ')
            if len(parts) == 2:
                return parts[0].replace('from ', '')
        
        return None

    def test_import_performance(self):
        """Test that imports don't cause performance issues."""
        import_times = {}
        
        # Key modules to test
        modules_to_test = [
            'svgx_engine',
            'svgx_engine.services',
            'arx_svg_parser',
            'arx_svg_parser.services',
        ]
        
        # Add project root to Python path
        original_path = sys.path.copy()
        sys.path.insert(0, str(self.project_root))
        
        try:
            for module in modules_to_test:
                import time
                start_time = time.time()
                
                try:
                    importlib.import_module(module)
                    end_time = time.time()
                    import_time = end_time - start_time
                    
                    import_times[module] = import_time
                    
                    # Fail if import takes too long (more than 1 second)
                    if import_time > 1.0:
                        self.fail(f"Import of {module} took {import_time:.2f} seconds (too slow)")
                        
                except Exception as e:
                    self.fail(f"Failed to import {module}: {e}")
                    
        finally:
            sys.path = original_path
        
        # Log import times for monitoring
        print("\nImport performance results:")
        for module, import_time in import_times.items():
            print(f"  - {module}: {import_time:.3f}s")

    def test_import_documentation(self):
        """Test that imports are properly documented."""
        undocumented_imports = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Check if there's documentation for this import
                        has_doc = self._has_import_documentation(lines, line_num)
                        
                        if not has_doc:
                            undocumented_imports.append({
                                'file': str(file_path),
                                'line': line_num,
                                'import': line
                            })
                            
            except Exception as e:
                print(f"Warning: Error checking {file_path} for import documentation: {e}")
        
        if undocumented_imports:
            # This is a warning, not a failure
            print(f"\nWarning: Found {len(undocumented_imports)} undocumented imports:")
            for imp in undocumented_imports[:10]:
                print(f"  - {imp['file']}:{imp['line']}: {imp['import']}")
            
            if len(undocumented_imports) > 10:
                print(f"  ... and {len(undocumented_imports) - 10} more")

    def _has_import_documentation(self, lines: List[str], line_num: int) -> bool:
        """Check if an import has proper documentation."""
        # Look for comments or docstrings around the import
        start_line = max(0, line_num - 3)
        end_line = min(len(lines), line_num + 3)
        
        for i in range(start_line, end_line):
            line = lines[i].strip()
            if line.startswith('#') or line.startswith('"""') or line.startswith("'''"):
                return True
        
        return False


def run_import_compliance_tests():
    """Run all import compliance tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ImportComplianceTest)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_import_compliance_tests()
    sys.exit(0 if success else 1) 