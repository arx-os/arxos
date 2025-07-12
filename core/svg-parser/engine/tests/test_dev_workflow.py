#!/usr/bin/env python3
"""
Test Suite for Development Workflow Automation

This test suite validates the development workflow automation system including:
- CI/CD pipeline configuration validation
- Cursor integration testing
- Code quality tools validation
- Testing framework validation
- Security scanning validation
- Build and packaging validation

Usage:
    pytest tests/test_dev_workflow.py -v
"""

import pytest
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import shutil
import os

from scripts.validate_dev_workflow import DevelopmentWorkflowValidator


class TestDevelopmentWorkflowValidator:
    """Test cases for DevelopmentWorkflowValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return DevelopmentWorkflowValidator(verbose=True)
        
    @pytest.fixture
    def temp_project(self):
        """Create temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create basic project structure
            project_dir = Path(temp_dir) / "test_project"
            project_dir.mkdir()
            
            # Create .github/workflows directory
            workflows_dir = project_dir / ".github" / "workflows"
            workflows_dir.mkdir(parents=True)
            
            # Create .cursor directory
            cursor_dir = project_dir / ".cursor"
            cursor_dir.mkdir()
            
            # Create test project structure
            arx_dir = project_dir / "arx_svg_parser"
            arx_dir.mkdir()
            
            tests_dir = arx_dir / "tests"
            tests_dir.mkdir()
            
            yield project_dir
            
    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.verbose is True
        assert "timestamp" in validator.results
        assert "validation_results" in validator.results
        assert "summary" in validator.results
        
    def test_log_function(self, validator, capsys):
        """Test logging functionality."""
        validator.log("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        
        validator.log("Error message", "ERROR")
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Error message" in captured.out
        
    def test_run_command_success(self, validator):
        """Test successful command execution."""
        success, stdout, stderr = validator.run_command(["echo", "test"])
        assert success is True
        assert "test" in stdout
        assert stderr == ""
        
    def test_run_command_failure(self, validator):
        """Test failed command execution."""
        success, stdout, stderr = validator.run_command(["nonexistent_command"])
        assert success is False
        assert stdout == ""
        assert stderr != ""
        
    def test_run_command_timeout(self, validator):
        """Test command timeout handling."""
        success, stdout, stderr = validator.run_command(["sleep", "60"])
        assert success is False
        assert "timed out" in stderr


class TestCICDPipelineValidation:
    """Test cases for CI/CD pipeline validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_workflow_file_exists(self, validator, temp_project):
        """Test workflow file existence check."""
        # Create workflow file
        workflow_file = temp_project / ".github" / "workflows" / "dev_pipeline.yml"
        workflow_file.write_text("""
name: Development Pipeline
on:
  push:
    branches: [main, develop]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo "test"
""")
        
        # Change to temp project directory
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_ci_cd_pipeline()
            
            assert result["status"] == "PASS"
            assert "Workflow file exists" in result["checks"]
            assert len(result["errors"]) == 0
            
        finally:
            os.chdir(original_cwd)
            
    def test_workflow_file_missing(self, validator, temp_project):
        """Test workflow file missing scenario."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_ci_cd_pipeline()
            
            assert result["status"] == "FAIL"
            assert "Workflow file not found" in result["errors"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_workflow_yaml_syntax(self, validator, temp_project):
        """Test workflow YAML syntax validation."""
        workflow_file = temp_project / ".github" / "workflows" / "dev_pipeline.yml"
        workflow_file.write_text("""
name: Development Pipeline
on:
  push:
    branches: [main, develop]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo "test"
""")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_ci_cd_pipeline()
            
            assert result["status"] == "PASS"
            assert "Workflow YAML syntax is valid" in result["checks"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_workflow_invalid_yaml(self, validator, temp_project):
        """Test invalid YAML syntax."""
        workflow_file = temp_project / ".github" / "workflows" / "dev_pipeline.yml"
        workflow_file.write_text("""
name: Development Pipeline
on:
  push:
    branches: [main, develop
jobs:
  test:
    runs-on: ubuntu-latest
""")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_ci_cd_pipeline()
            
            assert result["status"] == "FAIL"
            assert "Invalid YAML syntax" in result["errors"][0]
            
        finally:
            os.chdir(original_cwd)
            
    def test_required_jobs_check(self, validator, temp_project):
        """Test required jobs validation."""
        workflow_file = temp_project / ".github" / "workflows" / "dev_pipeline.yml"
        workflow_file.write_text("""
name: Development Pipeline
on:
  push:
    branches: [main, develop]
jobs:
  lint-and-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Lint
        run: echo "lint"
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo "test"
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Integration
        run: echo "integration"
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Security
        run: echo "security"
  build-package:
    runs-on: ubuntu-latest
    steps:
      - name: Build
        run: echo "build"
""")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_ci_cd_pipeline()
            
            assert result["status"] == "PASS"
            for job in ["lint-and-quality", "unit-tests", "integration-tests", "security-scan", "build-package"]:
                assert f"Required job '{job}' exists" in result["checks"]
                
        finally:
            os.chdir(original_cwd)


class TestCursorIntegrationValidation:
    """Test cases for Cursor integration validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_cursor_file_exists(self, validator, temp_project):
        """Test Cursor context file existence."""
        cursor_file = temp_project / ".cursor" / "context.json"
        cursor_file.write_text('{"project": {"name": "Test"}}')
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_cursor_integration()
            
            assert result["status"] == "PASS"
            assert "Cursor context file exists" in result["checks"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_cursor_file_missing(self, validator, temp_project):
        """Test Cursor context file missing scenario."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_cursor_integration()
            
            assert result["status"] == "FAIL"
            assert "Cursor context file not found" in result["errors"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_cursor_json_syntax(self, validator, temp_project):
        """Test Cursor JSON syntax validation."""
        cursor_file = temp_project / ".cursor" / "context.json"
        cursor_file.write_text('{"project": {"name": "Test"}}')
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_cursor_integration()
            
            assert result["status"] == "PASS"
            assert len(result["errors"]) == 0
            
        finally:
            os.chdir(original_cwd)
            
    def test_cursor_invalid_json(self, validator, temp_project):
        """Test invalid JSON syntax."""
        cursor_file = temp_project / ".cursor" / "context.json"
        cursor_file.write_text('{"project": {"name": "Test"')
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_cursor_integration()
            
            assert result["status"] == "FAIL"
            assert "Invalid JSON syntax" in result["errors"][0]
            
        finally:
            os.chdir(original_cwd)
            
    def test_cursor_required_sections(self, validator, temp_project):
        """Test required sections validation."""
        cursor_file = temp_project / ".cursor" / "context.json"
        cursor_file.write_text('''
{
  "project": {"name": "Test"},
  "development_workflow": {"ci_cd": {}},
  "project_structure": {"modules": {}}
}
''')
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_cursor_integration()
            
            assert result["status"] == "PASS"
            for section in ["project", "development_workflow", "project_structure"]:
                assert f"Required section '{section}' exists" in result["checks"]
                
        finally:
            os.chdir(original_cwd)


class TestCodeQualityValidation:
    """Test cases for code quality tools validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_pyproject_toml_exists(self, validator, temp_project):
        """Test pyproject.toml existence."""
        pyproject_file = temp_project / "arx_svg_parser" / "pyproject.toml"
        pyproject_file.parent.mkdir(parents=True)
        pyproject_file.write_text("""
[project]
name = "test"
version = "1.0.0"

[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.8"

[tool.pytest.ini_options]
testpaths = ["tests"]
""")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_code_quality_tools()
            
            assert result["status"] == "PASS"
            assert "pyproject.toml exists" in result["checks"]
            assert "Black configuration exists" in result["checks"]
            assert "isort configuration exists" in result["checks"]
            assert "MyPy configuration exists" in result["checks"]
            assert "pytest configuration exists" in result["checks"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_pyproject_toml_missing(self, validator, temp_project):
        """Test pyproject.toml missing scenario."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_code_quality_tools()
            
            assert result["status"] == "PASS"  # Not a failure, just warning
            assert "pyproject.toml not found" in result["warnings"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_quality_tools_availability(self, validator):
        """Test quality tools availability check."""
        result = validator.validate_code_quality_tools()
        
        # These should be available in test environment
        assert "black" in [check.split()[0] for check in result["checks"] if "is available" in check]
        assert "flake8" in [check.split()[0] for check in result["checks"] if "is available" in check]


class TestTestingFrameworkValidation:
    """Test cases for testing framework validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_pytest_availability(self, validator):
        """Test pytest availability."""
        result = validator.validate_testing_frameworks()
        
        assert result["status"] == "PASS"
        assert "pytest is available" in result["checks"]
        
    def test_test_directory_structure(self, validator, temp_project):
        """Test test directory structure validation."""
        # Create test directories
        test_dirs = [
            "arx_svg_parser/tests/",
            "arx_svg_parser/tests/unit/",
            "arx_svg_parser/tests/integration/",
            "arx_svg_parser/tests/performance/"
        ]
        
        for test_dir in test_dirs:
            (temp_project / test_dir).mkdir(parents=True)
            
        # Create test file
        test_file = temp_project / "arx_svg_parser" / "tests" / "test_example.py"
        test_file.write_text("""
def test_example():
    assert True
""")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_testing_frameworks()
            
            assert result["status"] == "PASS"
            for test_dir in test_dirs:
                assert f"Test directory '{test_dir}' exists" in result["checks"]
            assert "Found 1 test files" in result["checks"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_coverage_configuration(self, validator, temp_project):
        """Test coverage configuration validation."""
        coverage_file = temp_project / "arx_svg_parser" / ".coveragerc"
        coverage_file.parent.mkdir(parents=True)
        coverage_file.write_text("""
[run]
source = arx_svg_parser

[report]
exclude_lines =
    pragma: no cover
    def __repr__
""")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_testing_frameworks()
            
            assert result["status"] == "PASS"
            assert "Coverage configuration exists" in result["checks"]
            
        finally:
            os.chdir(original_cwd)


class TestSecurityScanningValidation:
    """Test cases for security scanning validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_security_tools_availability(self, validator):
        """Test security tools availability."""
        result = validator.validate_security_scanning()
        
        # Check if tools are available (may not be in test environment)
        assert result["status"] == "PASS"
        
    def test_security_configuration_files(self, validator, temp_project):
        """Test security configuration files validation."""
        # Create security config files
        configs = [
            "arx_svg_parser/pyproject.toml",
            "requirements.txt",
            "arx_svg_parser/requirements.txt"
        ]
        
        for config in configs:
            config_path = temp_project / config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("# Security configuration")
            
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_security_scanning()
            
            assert result["status"] == "PASS"
            for config in configs:
                assert f"Security config '{config}' exists" in result["checks"]
                
        finally:
            os.chdir(original_cwd)


class TestBuildPackagingValidation:
    """Test cases for build and packaging validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_build_tools_availability(self, validator):
        """Test build tools availability."""
        result = validator.validate_build_packaging()
        
        assert result["status"] == "PASS"
        assert "python is available" in result["checks"]
        assert "pip is available" in result["checks"]
        
    def test_build_configuration_files(self, validator, temp_project):
        """Test build configuration files validation."""
        # Create build config files
        configs = [
            "arx_svg_parser/pyproject.toml",
            "arx_svg_parser/setup.py",
            "arx_svg_parser/requirements.txt"
        ]
        
        for config in configs:
            config_path = temp_project / config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("# Build configuration")
            
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            result = validator.validate_build_packaging()
            
            assert result["status"] == "PASS"
            for config in configs:
                assert f"Build config '{config}' exists" in result["checks"]
                
        finally:
            os.chdir(original_cwd)


class TestFullValidationWorkflow:
    """Test cases for full validation workflow."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DevelopmentWorkflowValidator()
        
    def test_run_validation_all_checks(self, validator):
        """Test running all validation checks."""
        checks = ["ci", "cursor", "quality", "tests", "security", "build"]
        results = validator.run_validation(checks)
        
        assert "validation_results" in results
        assert "summary" in results
        assert results["summary"]["total_checks"] > 0
        
        # Check that all requested checks were run
        for check in checks:
            assert check in results["validation_results"]
            
    def test_run_validation_specific_checks(self, validator):
        """Test running specific validation checks."""
        checks = ["tests", "quality"]
        results = validator.run_validation(checks)
        
        assert len(results["validation_results"]) == 2
        assert "tests" in results["validation_results"]
        assert "quality" in results["validation_results"]
        assert "ci" not in results["validation_results"]
        
    def test_validation_summary_calculation(self, validator):
        """Test validation summary calculation."""
        checks = ["tests", "quality"]
        results = validator.run_validation(checks)
        
        summary = results["summary"]
        assert summary["total_checks"] >= 0
        assert summary["passed"] >= 0
        assert summary["failed"] >= 0
        assert summary["warnings"] >= 0
        
    def test_save_report(self, validator, temp_project):
        """Test saving validation report."""
        checks = ["tests", "quality"]
        results = validator.run_validation(checks)
        
        report_file = temp_project / "validation_report.json"
        validator.save_report(str(report_file))
        
        assert report_file.exists()
        
        # Verify report content
        with open(report_file, 'r') as f:
            saved_results = json.load(f)
            
        assert "validation_results" in saved_results
        assert "summary" in saved_results
        assert saved_results["summary"]["total_checks"] == results["summary"]["total_checks"]


class TestIntegrationScenarios:
    """Integration test scenarios for development workflow."""
    
    def test_complete_workflow_validation(self, temp_project):
        """Test complete workflow validation scenario."""
        # Set up complete project structure
        validator = DevelopmentWorkflowValidator()
        
        # Create workflow file
        workflow_file = temp_project / ".github" / "workflows" / "dev_pipeline.yml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text("""
name: Development Pipeline
on:
  push:
    branches: [main, develop]
jobs:
  lint-and-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Lint
        run: echo "lint"
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo "test"
""")
        
        # Create Cursor context
        cursor_file = temp_project / ".cursor" / "context.json"
        cursor_file.parent.mkdir(parents=True)
        cursor_file.write_text('{"project": {"name": "Test"}, "development_workflow": {}}')
        
        # Create test structure
        test_dirs = [
            "arx_svg_parser/tests/",
            "arx_svg_parser/tests/unit/"
        ]
        
        for test_dir in test_dirs:
            (temp_project / test_dir).mkdir(parents=True)
            
        # Create test file
        test_file = temp_project / "arx_svg_parser" / "tests" / "test_example.py"
        test_file.write_text("def test_example(): assert True")
        
        # Create pyproject.toml
        pyproject_file = temp_project / "arx_svg_parser" / "pyproject.toml"
        pyproject_file.parent.mkdir(parents=True)
        pyproject_file.write_text("""
[project]
name = "test"
version = "1.0.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
""")
        
        # Run validation
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            results = validator.run_validation(["ci", "cursor", "tests"])
            
            # Should pass with minimal setup
            assert results["summary"]["failed"] == 0
            assert results["summary"]["total_checks"] > 0
            
        finally:
            os.chdir(original_cwd)
            
    def test_error_handling_scenarios(self, temp_project):
        """Test error handling scenarios."""
        validator = DevelopmentWorkflowValidator()
        
        # Test with missing files
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            results = validator.run_validation(["ci", "cursor"])
            
            # Should have some failures due to missing files
            assert results["summary"]["failed"] > 0
            
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 