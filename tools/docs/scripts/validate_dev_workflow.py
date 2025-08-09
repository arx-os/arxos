#!/usr/bin/env python3
""""
Development Workflow Validation Script

This script validates the development workflow automation system including:
- CI/CD pipeline configuration
- Cursor integration setup
- Code quality tools
- Testing frameworks
- Security scanning
- Build and packaging

Usage:
    python scripts/validate_dev_workflow.py [options]

Options:
    --verbose          Enable verbose output
    --exit-code       Exit with non-zero code on validation failures
    --report          Generate detailed JSON report
    --check-ci        Validate CI/CD pipeline configuration
    --check-cursor    Validate Cursor integration
    --check-quality   Validate code quality tools
    --check-tests     Validate testing frameworks
    --check-security  Validate security scanning
    --check-build     Validate build and packaging
"""

import sys
import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import yaml

class DevelopmentWorkflowValidator:
    """Validator for development workflow automation system."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with optional verbosity."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str, str]:
        """Run command and return success status, stdout, and stderr."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def validate_ci_cd_pipeline(self) -> Dict[str, Any]:
        """Validate CI/CD pipeline configuration."""
        self.log("Validating CI/CD pipeline configuration...")

        results = {
            "status": "PASS",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check if workflow file exists
        workflow_file = Path(".github/workflows/dev_pipeline.yml")
        if not workflow_file.exists():
            results["status"] = "FAIL"
            results["errors"].append("CI/CD workflow file not found")
            return results

        results["checks"].append("Workflow file exists")

        # Validate workflow YAML syntax
        try:
            with open(workflow_file, 'r') as f:
                workflow_config = yaml.safe_load(f)

            # Check required fields
            required_fields = ["name", "on", "jobs"]
            for field in required_fields:
                if field not in workflow_config:
                    results["errors"].append(f"Missing required field: {field}")

            if results["errors"]:
                results["status"] = "FAIL"
            else:
                results["checks"].append("Workflow YAML syntax is valid")

        except yaml.YAMLError as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Invalid YAML syntax: {e}")

        # Check for required jobs
        if "jobs" in workflow_config:
            required_jobs = [
                "lint-and-quality",
                "unit-tests",
                "integration-tests",
                "security-scan",
                "build-package"
            ]

            for job in required_jobs:
                if job in workflow_config["jobs"]:
                    results["checks"].append(f"Required job '{job}' exists")
                else:
                    results["warnings"].append(f"Recommended job '{job}' not found")

        return results

    def validate_cursor_integration(self) -> Dict[str, Any]:
        """Validate Cursor integration setup."""
        self.log("Validating Cursor integration...")

        results = {
            "status": "PASS",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check if Cursor context file exists
        cursor_file = Path(".cursor/context.json")
        if not cursor_file.exists():
            results["status"] = "FAIL"
            results["errors"].append("Cursor context file not found")
            return results

        results["checks"].append("Cursor context file exists")

        # Validate JSON syntax
        try:
            with open(cursor_file, 'r') as f:
                cursor_config = json.load(f)

            # Check required sections
            required_sections = ["project", "development_workflow", "project_structure"]
            for section in required_sections:
                if section in cursor_config:
                    results["checks"].append(f"Required section '{section}' exists")
                else:
                    results["warnings"].append(f"Recommended section '{section}' not found")

        except json.JSONDecodeError as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Invalid JSON syntax: {e}")

        return results

    def validate_code_quality_tools(self) -> Dict[str, Any]:
        """Validate code quality tools configuration."""
        self.log("Validating code quality tools...")

        results = {
            "status": "PASS",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check pyproject.toml configuration

        if pyproject_file.exists():
            results["checks"].append("pyproject.toml exists")

            # Check for required tool configurations
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    config = tomllib.load(f)

                tools = config.get("tool", {})

                # Check Black configuration
                if "black" in tools:
                    results["checks"].append("Black configuration exists")
                else:
                    results["warnings"].append("Black configuration not found")

                # Check isort configuration
                if "isort" in tools:
                    results["checks"].append("isort configuration exists")
                else:
                    results["warnings"].append("isort configuration not found")

                # Check MyPy configuration
                if "mypy" in tools:
                    results["checks"].append("MyPy configuration exists")
                else:
                    results["warnings"].append("MyPy configuration not found")

                # Check pytest configuration
                if "pytest.ini_options" in tools:
                    results["checks"].append("pytest configuration exists")
                else:
                    results["warnings"].append("pytest configuration not found")

            except Exception as e:
                results["errors"].append(f"Error parsing pyproject.toml: {e}")
        else:
            results["warnings"].append("pyproject.toml not found")

        # Check if quality tools are available
        quality_tools = ["black", "isort", "flake8", "mypy", "bandit"]
        for tool in quality_tools:
            success, _, _ = self.run_command([tool, "--version"])
            if success:
                results["checks"].append(f"{tool} is available")
            else:
                results["warnings"].append(f"{tool} is not available")

        return results

    def validate_testing_frameworks(self) -> Dict[str, Any]:
        """Validate testing frameworks configuration."""
        self.log("Validating testing frameworks...")

        results = {
            "status": "PASS",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check pytest availability
        success, stdout, _ = self.run_command(["python", "-m", "pytest", "--version"])
        if success:
            results["checks"].append("pytest is available")
        else:
            results["errors"].append("pytest is not available")

        # Check test directory structure
        test_dirs = [

        ]

        for test_dir in test_dirs:
            if Path(test_dir).exists():
                results["checks"].append(f"Test directory '{test_dir}' exists")
            else:
                results["warnings"].append(f"Test directory '{test_dir}' not found")

        # Check for test files

        if test_files:
            results["checks"].append(f"Found {len(test_files)} test files")
        else:
            results["warnings"].append("No test files found")

        # Check coverage configuration

        if coverage_file.exists():
            results["checks"].append("Coverage configuration exists")
        else:
            results["warnings"].append("Coverage configuration not found")

        return results

    def validate_security_scanning(self) -> Dict[str, Any]:
        """Validate security scanning configuration."""
        self.log("Validating security scanning...")

        results = {
            "status": "PASS",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check bandit availability
        success, _, _ = self.run_command(["bandit", "--version"])
        if success:
            results["checks"].append("bandit is available")
        else:
            results["warnings"].append("bandit is not available")

        # Check safety availability
        success, _, _ = self.run_command(["safety", "--version"])
        if success:
            results["checks"].append("safety is available")
        else:
            results["warnings"].append("safety is not available")

        # Check for security configuration
        security_configs = [
            "requirements.txt"  # dependencies for safety
        ]

        for config in security_configs:
            if Path(config).exists():
                results["checks"].append(f"Security config '{config}' exists")
            else:
                results["warnings"].append(f"Security config '{config}' not found")

        return results

    def validate_build_packaging(self) -> Dict[str, Any]:
        """Validate build and packaging configuration."""
        self.log("Validating build and packaging...")

        results = {
            "status": "PASS",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check build tools availability
        build_tools = ["python", "pip", "build"]
        for tool in build_tools:
            success, _, _ = self.run_command([tool, "--version"])
            if success:
                results["checks"].append(f"{tool} is available")
            else:
                results["warnings"].append(f"{tool} is not available")

        # Check for build configuration files
        build_configs = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt"
        ]

        for config in build_configs:
            if Path(config).exists():
                results["checks"].append(f"Build config '{config}' exists")
            else:
                results["warnings"].append(f"Build config '{config}' not found")

        # Check if package can be built
        try:
            success, stdout, stderr = self.run_command(
                ["python", "-m", "build", "--dry-run"],

            )
            if success:
                results["checks"].append("Package can be built successfully")
            else:
                results["warnings"].append("Package build may have issues")
        except Exception as e:
            results["warnings"].append(f"Could not test package build: {e}")

        return results

    def run_validation(self, checks: List[str]) -> Dict[str, Any]:
        """Run specified validation checks."""
        self.log("Starting development workflow validation...")

        validation_functions = {
            "ci": self.validate_ci_cd_pipeline,
            "cursor": self.validate_cursor_integration,
            "quality": self.validate_code_quality_tools,
            "tests": self.validate_testing_frameworks,
            "security": self.validate_security_scanning,
            "build": self.validate_build_packaging
        }

        for check in checks:
            if check in validation_functions:
                self.log(f"Running {check} validation...")
                result = validation_functions[check]()
                self.results["validation_results"][check] = result

                # Update summary
                self.results["summary"]["total_checks"] += len(result["checks"])
                self.results["summary"]["passed"] += len(result["checks"])
                self.results["summary"]["failed"] += len(result["errors"])
                self.results["summary"]["warnings"] += len(result["warnings"])

                if result["status"] == "FAIL":
                    self.log(f"{check} validation failed", "ERROR")
                elif result["warnings"]:
                    self.log(f"{check} validation completed with warnings", "WARNING")
                else:
                    self.log(f"{check} validation passed", "INFO")
            else:
                self.log(f"Unknown validation check: {check}", "WARNING")

        return self.results

    def print_summary(self):
        """Print validation summary."""
        summary = self.results["summary"]

        print("\n" + "="*60)
        print("DEVELOPMENT WORKFLOW VALIDATION SUMMARY")
        print("="*60)

        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Warnings: {summary['warnings']}")

        if summary['failed'] > 0:
            print("\n❌ VALIDATION FAILED")
            print("Please fix the following issues:")
            for check, result in self.results["validation_results"].items():
                if result["errors"]:
                    print(f"\n{check.upper()} ERRORS:")
                    for error in result["errors"]:
                        print(f"  - {error}")
        elif summary['warnings'] > 0:
            print("\n⚠️  VALIDATION COMPLETED WITH WARNINGS")
            print("Consider addressing the following warnings:")
            for check, result in self.results["validation_results"].items():
                if result["warnings"]:
                    print(f"\n{check.upper()} WARNINGS:")
                    for warning in result["warnings"]:
                        print(f"  - {warning}")
        else:
            print("\n✅ VALIDATION PASSED")
            print("All checks passed successfully!")

        print("\n" + "="*60)

    def save_report(self, filename: str):
        """Save validation results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"Report saved to {filename}")

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate development workflow automation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--exit-code", action="store_true", help="Exit with non-zero code on failures")
    parser.add_argument("--report", help="Generate detailed JSON report")
    parser.add_argument("--check-ci", action="store_true", help="Validate CI/CD pipeline")
    parser.add_argument("--check-cursor", action="store_true", help="Validate Cursor integration")
    parser.add_argument("--check-quality", action="store_true", help="Validate code quality tools")
    parser.add_argument("--check-tests", action="store_true", help="Validate testing frameworks")
    parser.add_argument("--check-security", action="store_true", help="Validate security scanning")
    parser.add_argument("--check-build", action="store_true", help="Validate build and packaging")

    args = parser.parse_args()

    # Determine which checks to run
    checks = []
    if args.check_ci:
        checks.append("ci")
    if args.check_cursor:
        checks.append("cursor")
    if args.check_quality:
        checks.append("quality")
    if args.check_tests:
        checks.append("tests")
    if args.check_security:
        checks.append("security")
    if args.check_build:
        checks.append("build")

    # If no specific checks specified, run all
    if not checks:
        checks = ["ci", "cursor", "quality", "tests", "security", "build"]

    # Run validation
    validator = DevelopmentWorkflowValidator(verbose=args.verbose)
    results = validator.run_validation(checks)

    # Print summary
    validator.print_summary()

    # Save report if requested
    if args.report:
        validator.save_report(args.report)

    # Exit with appropriate code
    if args.exit_code and results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
