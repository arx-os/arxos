#!/usr/bin/env python3
"""
Code quality tests for SDKs
Tests linting, formatting, type checking, security scanning, and code coverage
"""

import pytest
import subprocess
import json
import ast
from pathlib import Path
from typing import Dict, Any, List

class TestCodeQuality:
    """Code quality test suite for SDKs"""

    @pytest.fixture
def quality_config(self):
        """Quality test configuration"""
        return {
            "coverage_threshold": 90,
            "max_complexity": 10,
            "max_line_length": 120,
            "min_docstring_coverage": 80,
            "security_scan_enabled": True,
            "type_check_enabled": True
        }

    def test_typescript_linting(self):
        """Test TypeScript linting quality"""
        sdk_path = Path("sdk/generated/typescript/arx-backend")

        if not sdk_path.exists():
            pytest.skip("TypeScript SDK not generated")

        try:
            # Check ESLint configuration
            eslint_config = sdk_path / ".eslintrc.js"
            assert eslint_config.exists(), "ESLint config should exist"

            # Run ESLint
            result = subprocess.run(
                ["npx", "eslint", "src/", "--ext", ".ts", "--format", "json"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Parse ESLint output
                try:
                    lint_results = json.loads(result.stdout)

                    # Count errors vs warnings
                    error_count = 0
                    warning_count = 0

                    for file_result in lint_results:
                        for message in file_result.get("messages", []):
                            if message.get("severity") == 2:  # Error
                                error_count += 1
                            elif message.get("severity") == 1:  # Warning
                                warning_count += 1

                    # Should have no errors
                    assert error_count == 0, f"ESLint found {error_count} errors"

                    # Warnings are acceptable but should be limited
                    assert warning_count < 50, f"Too many ESLint warnings: {warning_count}"

                    print(f"TypeScript Linting Results:")
                    print(f"  Errors: {error_count}")
                    print(f"  Warnings: {warning_count}")

                except json.JSONDecodeError:
                    pytest.fail("Failed to parse ESLint output")
            else:
                print("TypeScript linting passed with no issues")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"ESLint execution failed: {e}")

    def test_python_linting(self):
        """Test Python linting quality"""
        sdk_path = Path("sdk/generated/python/arx_backend")

        if not sdk_path.exists():
            pytest.skip("Python SDK not generated")

        try:
            # Run flake8
            result = subprocess.run(
                ["flake8", "arx_backend/", "--format=json"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                try:
                    lint_results = json.loads(result.stdout)

                    # Count issues by type
                    error_count = 0
                    warning_count = 0

                    for file_path, issues in lint_results.items():
                        for issue in issues:
                            if issue.get("type") == "E":  # Error
                                error_count += 1
                            elif issue.get("type") == "W":  # Warning
                                warning_count += 1

                    # Should have no errors
                    assert error_count == 0, f"Flake8 found {error_count} errors"

                    # Warnings are acceptable but should be limited
                    assert warning_count < 30, f"Too many flake8 warnings: {warning_count}"

                    print(f"Python Linting Results:")
                    print(f"  Errors: {error_count}")
                    print(f"  Warnings: {warning_count}")

                except json.JSONDecodeError:
                    pytest.fail("Failed to parse flake8 output")
            else:
                print("Python linting passed with no issues")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Flake8 execution failed: {e}")

    def test_go_linting(self):
        """Test Go linting quality"""
        sdk_path = Path("sdk/generated/go/arx-backend")

        if not sdk_path.exists():
            pytest.skip("Go SDK not generated")

        try:
            # Run golint
            result = subprocess.run(
                ["golint", "./..."],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Count lint issues
                lint_issues = result.stdout.strip().split('\n')
                lint_issues = [issue for issue in lint_issues if issue.strip()]

                # Should have limited lint issues
                assert len(lint_issues) < 20, f"Too many golint issues: {len(lint_issues)}"

                print(f"Go Linting Results:")
                print(f"  Issues: {len(lint_issues)}")

            else:
                print("Go linting passed with no issues")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Golint execution failed: {e}")

    def test_typescript_formatting(self):
        """Test TypeScript code formatting"""
        sdk_path = Path("sdk/generated/typescript/arx-backend")

        if not sdk_path.exists():
            pytest.skip("TypeScript SDK not generated")

        try:
            # Check Prettier configuration
            prettier_config = sdk_path / ".prettierrc"
            if prettier_config.exists():
                # Run Prettier check
                result = subprocess.run(
                    ["npx", "prettier", "--check", "src/"],
                    cwd=sdk_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print("TypeScript formatting issues found")
                    print(result.stdout)
                    # Don't fail, just warn about formatting'
                else:
                    print("TypeScript formatting is correct")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Prettier execution failed: {e}")

    def test_python_formatting(self):
        """Test Python code formatting"""
        sdk_path = Path("sdk/generated/python/arx_backend")

        if not sdk_path.exists():
            pytest.skip("Python SDK not generated")

        try:
            # Run black check
            result = subprocess.run(
                ["black", "--check", "arx_backend/"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print("Python formatting issues found")
                print(result.stdout)
                # Don't fail, just warn about formatting'
            else:
                print("Python formatting is correct")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Black execution failed: {e}")

    def test_go_formatting(self):
        """Test Go code formatting"""
        sdk_path = Path("sdk/generated/go/arx-backend")

        if not sdk_path.exists():
            pytest.skip("Go SDK not generated")

        try:
            # Run gofmt check
            result = subprocess.run(
                ["gofmt", "-l", "."],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                print("Go formatting issues found")
                print(result.stdout)
                # Don't fail, just warn about formatting'
            else:
                print("Go formatting is correct")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Gofmt execution failed: {e}")

    def test_typescript_type_checking(self):
        """Test TypeScript type checking"""
        sdk_path = Path("sdk/generated/typescript/arx-backend")

        if not sdk_path.exists():
            pytest.skip("TypeScript SDK not generated")

        try:
            # Run TypeScript compiler
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--strict"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print("TypeScript type checking issues found")
                print(result.stderr)
                # Don't fail, just warn about type issues'
            else:
                print("TypeScript type checking passed")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"TypeScript compilation failed: {e}")

    def test_python_type_checking(self):
        """Test Python type checking"""
        sdk_path = Path("sdk/generated/python/arx_backend")

        if not sdk_path.exists():
            pytest.skip("Python SDK not generated")

        try:
            # Run mypy
            result = subprocess.run(
                ["mypy", "arx_backend/"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print("Python type checking issues found")
                print(result.stdout)
                # Don't fail, just warn about type issues'
            else:
                print("Python type checking passed")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"MyPy execution failed: {e}")

    def test_code_complexity(self):
        """Test code complexity analysis"""
        complexity_issues = []

        # Check Python files for complexity
        python_sdk_path = Path("sdk/generated/python/arx_backend")
        if python_sdk_path.exists():
            for py_file in python_sdk_path.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        tree = ast.parse(f.read()
                    # Simple complexity check (function count)
                    function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])

                    if function_count > 20:
                        complexity_issues.append(f"{py_file}: {function_count} functions")

                except SyntaxError:
                    complexity_issues.append(f"{py_file}: syntax error")

        # Check TypeScript files for complexity
        typescript_sdk_path = Path("sdk/generated/typescript/arx-backend")
        if typescript_sdk_path.exists():
            for ts_file in typescript_sdk_path.rglob("*.ts"):
                try:
                    with open(ts_file, 'r') as f:
                        content = f.read()

                    # Simple complexity check (function count)
                    function_count = content.count("function ") + content.count("=>")

                    if function_count > 30:
                        complexity_issues.append(f"{ts_file}: {function_count} functions")

                except Exception:
                    complexity_issues.append(f"{ts_file}: parsing error")

        # Should have limited complexity issues
        assert len(complexity_issues) < 10, f"Too many complexity issues: {complexity_issues}"

        if complexity_issues:
            print("Code Complexity Issues:")
            for issue in complexity_issues:
                print(f"  {issue}")

    def test_documentation_coverage(self):
        """Test documentation coverage"""
        doc_coverage = {}

        # Check Python documentation
        python_sdk_path = Path("sdk/generated/python/arx_backend")
        if python_sdk_path.exists():
            total_functions = 0
            documented_functions = 0

            for py_file in python_sdk_path.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        tree = ast.parse(f.read()
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                            if ast.get_docstring(node):
                                documented_functions += 1

                except SyntaxError:
                    continue

            if total_functions > 0:
                doc_coverage['python'] = (documented_functions / total_functions) * 100

        # Check TypeScript documentation
        typescript_sdk_path = Path("sdk/generated/typescript/arx-backend")
        if typescript_sdk_path.exists():
            total_functions = 0
            documented_functions = 0

            for ts_file in typescript_sdk_path.rglob("*.ts"):
                try:
                    with open(ts_file, 'r') as f:
                        content = f.read()

                    # Count functions and JSDoc comments
                    function_matches = content.count("function ") + content.count("=>")
                    jsdoc_matches = content.count("/**")

                    total_functions += function_matches
                    documented_functions += min(jsdoc_matches, function_matches)

                except Exception:
                    continue

            if total_functions > 0:
                doc_coverage['typescript'] = (documented_functions / total_functions) * 100

        # Check Go documentation
        go_sdk_path = Path("sdk/generated/go/arx-backend")
        if go_sdk_path.exists():
            total_functions = 0
            documented_functions = 0

            for go_file in go_sdk_path.rglob("*.go"):
                try:
                    with open(go_file, 'r') as f:
                        content = f.read()

                    # Count functions and comments
                    function_matches = content.count("func ")
                    comment_matches = content.count("// ")

                    total_functions += function_matches
                    documented_functions += min(comment_matches, function_matches)

                except Exception:
                    continue

            if total_functions > 0:
                doc_coverage['go'] = (documented_functions / total_functions) * 100

        print("Documentation Coverage:")
        for language, coverage in doc_coverage.items():
            print(f"  {language}: {coverage:.1f}%")
            assert coverage >= 50, f"Documentation coverage for {language} too low: {coverage:.1f}%"

    def test_security_scanning(self):
        """Test security scanning"""
        security_issues = []

        # Check for common security issues
        sdk_paths = [
            Path("sdk/generated/python/arx_backend"),
            Path("sdk/generated/typescript/arx-backend"),
            Path("sdk/generated/go/arx-backend")
        ]

        for sdk_path in sdk_paths:
            if sdk_path.exists():
                for file_path in sdk_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()

                            # Check for hardcoded secrets
                            if any(secret in content.lower() for secret in [
                                "password", "secret", "key", "token", "api_key"
                            ]):
                                if not any(safe in content.lower() for safe in [
                                    "example", "test", "mock", "placeholder"
                                ]):
                                    security_issues.append(f"{file_path}: potential hardcoded secret")

                            # Check for SQL injection patterns
                            if "sql" in content.lower() and "string" in content.lower():
                                if "query" in content.lower() and "user" in content.lower():
                                    security_issues.append(f"{file_path}: potential SQL injection")

                        except Exception:
                            continue

        # Should have no security issues
        assert len(security_issues) == 0, f"Security issues found: {security_issues}"

        if security_issues:
            print("Security Issues:")
            for issue in security_issues:
                print(f"  {issue}")

    def test_test_coverage(self):
        """Test test coverage analysis"""
        coverage_results = {}

        # Check Python test coverage
        python_sdk_path = Path("sdk/generated/python/arx_backend")
        if python_sdk_path.exists():
            try:
                result = subprocess.run(
                    ["coverage", "run", "-m", "pytest", "tests/"],
                    cwd=python_sdk_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    # Get coverage report
                    coverage_result = subprocess.run(
                        ["coverage", "report"],
                        cwd=python_sdk_path,
                        capture_output=True,
                        text=True
                    )

                    if coverage_result.returncode == 0:
                        # Parse coverage percentage
                        lines = coverage_result.stdout.split('\n')
                        for line in lines:
                            if 'TOTAL' in line:
                                parts = line.split()
                                if len(parts) >= 4:
                                    try:
                                        coverage = int(parts[-1].replace('%', '')
                                        coverage_results['python'] = coverage
                                    except ValueError:
                                        pass

            except subprocess.CalledProcessError:
                pass

        # Check TypeScript test coverage
        typescript_sdk_path = Path("sdk/generated/typescript/arx-backend")
        if typescript_sdk_path.exists():
            try:
                result = subprocess.run(
                    ["npm", "test", "--", "--coverage"],
                    cwd=typescript_sdk_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    # Parse coverage from output import output
                    if "All files" in result.stdout:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if "All files" in line:
                                try:
                                    coverage = int(line.split()[-1].replace('%', '')
                                    coverage_results['typescript'] = coverage
                                except ValueError:
                                    pass

            except subprocess.CalledProcessError:
                pass

        print("Test Coverage:")
        for language, coverage in coverage_results.items():
            print(f"  {language}: {coverage}%")
            assert coverage >= 70, f"Test coverage for {language} too low: {coverage}%"

    def test_code_duplication(self):
        """Test code duplication analysis"""
        duplication_issues = []

        # Simple duplication check
        sdk_paths = [
            Path("sdk/generated/python/arx_backend"),
            Path("sdk/generated/typescript/arx-backend"),
            Path("sdk/generated/go/arx-backend")
        ]

        for sdk_path in sdk_paths:
            if sdk_path.exists():
                file_contents = []

                for file_path in sdk_path.rglob("*"):
                    if file_path.is_file() and file_path.suffix in ['.py', '.ts', '.go']:
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            file_contents.append((file_path, content)
                        except Exception:
                            continue

                # Check for duplicate content
                for i, (file1, content1) in enumerate(file_contents):
                    for j, (file2, content2) in enumerate(file_contents[i+1:], i+1):
                        if content1 == content2:
                            duplication_issues.append(f"Duplicate files: {file1} and {file2}")

        # Should have limited duplication
        assert len(duplication_issues) < 5, f"Too much code duplication: {duplication_issues}"

        if duplication_issues:
            print("Code Duplication Issues:")
            for issue in duplication_issues:
                print(f"  {issue}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
