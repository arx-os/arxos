#!/usr/bin/env python3
"""
Comprehensive test runner for the Arxos project.

Runs all critical tests including unit tests, integration tests,
and end-to-end verification of the complete system.
"""

import os
import sys
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse


@dataclass
class TestResult:
    """Test result information."""
    name: str
    success: bool
    duration: float
    output: str
    error: Optional[str] = None


class ArxosTestRunner:
    """Comprehensive test runner for Arxos."""
    
    def __init__(self, verbose: bool = False):
        """Initialize test runner."""
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.results: List[TestResult] = []
        
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def run_all_tests(self) -> bool:
        """Run all test suites."""
        self.logger.info("Starting comprehensive Arxos test suite")
        
        test_suites = [
            ("Symbol Recognition Bridge", self._test_symbol_recognition_bridge),
            ("API Authentication", self._test_api_authentication),
            ("ArxObject Operations", self._test_arxobject_operations),
            ("Configuration Management", self._test_configuration),
            ("Docker Setup", self._test_docker_setup),
            ("Service Integration", self._test_service_integration),
        ]
        
        total_success = True
        
        for suite_name, test_func in test_suites:
            self.logger.info(f"Running {suite_name} tests...")
            
            start_time = time.time()
            try:
                success = test_func()
                duration = time.time() - start_time
                
                if success:
                    self.logger.info(f"✓ {suite_name} tests passed ({duration:.2f}s)")
                else:
                    self.logger.error(f"✗ {suite_name} tests failed ({duration:.2f}s)")
                    total_success = False
                    
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"✗ {suite_name} tests errored: {e} ({duration:.2f}s)")
                total_success = False
                
                self.results.append(TestResult(
                    name=suite_name,
                    success=False,
                    duration=duration,
                    output="",
                    error=str(e)
                ))
        
        # Generate test report
        self._generate_test_report()
        
        return total_success
        
    def _test_symbol_recognition_bridge(self) -> bool:
        """Test the symbol recognition bridge."""
        test_script = self.project_root / "tests" / "integration" / "test_symbol_recognition_bridge.py"
        
        if not test_script.exists():
            self.logger.warning(f"Test script not found: {test_script}")
            return False
            
        # Run Python tests
        return self._run_python_test(test_script, "bridge")
        
    def _test_api_authentication(self) -> bool:
        """Test API authentication."""
        test_script = self.project_root / "tests" / "integration" / "test_api_authentication.py"
        
        if not test_script.exists():
            self.logger.warning(f"Test script not found: {test_script}")
            return False
            
        # Run authentication tests
        return self._run_python_test(test_script, "auth")
        
    def _test_arxobject_operations(self) -> bool:
        """Test ArxObject operations."""
        test_script = self.project_root / "tests" / "unit" / "test_arxobject_operations.py"
        
        if not test_script.exists():
            self.logger.warning(f"Test script not found: {test_script}")
            return False
            
        # Run ArxObject tests
        return self._run_python_test(test_script, "validation")
        
    def _test_configuration(self) -> bool:
        """Test configuration management."""
        self.logger.info("Testing environment variable configuration...")
        
        # Test Go API configuration
        go_config_test = self._test_go_config()
        
        # Test Python configuration
        python_config_test = self._test_python_config()
        
        return go_config_test and python_config_test
        
    def _test_docker_setup(self) -> bool:
        """Test Docker setup."""
        self.logger.info("Testing Docker configuration...")
        
        docker_files = [
            "docker-compose.production.yml",
            "Dockerfile.go-api",
            "Dockerfile.svgx",
            "Dockerfile.python-api",
            "Dockerfile.gus",
            "Dockerfile.nginx"
        ]
        
        for docker_file in docker_files:
            file_path = self.project_root / docker_file
            if not file_path.exists():
                self.logger.error(f"Missing Docker file: {docker_file}")
                return False
                
        # Test Docker Compose syntax
        return self._test_docker_compose_syntax()
        
    def _test_service_integration(self) -> bool:
        """Test service integration."""
        self.logger.info("Testing service integration setup...")
        
        # Check that all services have proper configuration
        services = {
            "arxos-api": self.project_root / "arxos-api",
            "svgx_engine": self.project_root / "svgx_engine",
            "services/gus": self.project_root / "services" / "gus"
        }
        
        for service_name, service_path in services.items():
            if not service_path.exists():
                self.logger.error(f"Service directory not found: {service_name}")
                return False
                
        return True
        
    def _run_python_test(self, test_script: Path, test_group: Optional[str] = None) -> bool:
        """Run a Python test script."""
        cmd = [sys.executable, str(test_script)]
        if test_group:
            cmd.append(test_group)
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            self.results.append(TestResult(
                name=f"{test_script.name}:{test_group or 'all'}",
                success=result.returncode == 0,
                duration=0,  # Would need timing
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            ))
            
            if self.verbose and result.stdout:
                self.logger.debug(f"Test output:\n{result.stdout}")
                
            if result.returncode != 0 and result.stderr:
                self.logger.error(f"Test error:\n{result.stderr}")
                
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test timeout: {test_script}")
            return False
        except Exception as e:
            self.logger.error(f"Test execution error: {e}")
            return False
            
    def _test_go_config(self) -> bool:
        """Test Go API configuration."""
        go_api_dir = self.project_root / "arxos-api"
        if not go_api_dir.exists():
            self.logger.error("Go API directory not found")
            return False
            
        # Check for required files
        required_files = ["main.go", "auth.go", "go.mod"]
        for file_name in required_files:
            file_path = go_api_dir / file_name
            if not file_path.exists():
                self.logger.error(f"Missing Go API file: {file_name}")
                return False
                
        # Check for environment variable usage
        main_go = go_api_dir / "main.go"
        content = main_go.read_text()
        
        required_env_vars = ["PORT", "POSTGRES_PASSWORD", "JWT_SECRET"]
        for env_var in required_env_vars:
            if env_var not in content:
                self.logger.warning(f"Environment variable {env_var} not found in main.go")
                
        return True
        
    def _test_python_config(self) -> bool:
        """Test Python configuration."""
        config_file = self.project_root / "application" / "config.py"
        if not config_file.exists():
            self.logger.error("Python configuration file not found")
            return False
            
        # Try to import and validate configuration
        try:
            sys.path.insert(0, str(self.project_root))
            
            # Set minimal required environment variables
            os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
            os.environ.setdefault("ARXOS_ENV", "test")
            os.environ.setdefault("GUS_SERVICE_URL", "http://localhost:8083")
            
            from application.config import get_config, get_config_summary_info
            
            config = get_config()
            summary = get_config_summary_info()
            
            self.logger.info(f"Configuration loaded successfully: {summary}")
            return True
            
        except Exception as e:
            self.logger.error(f"Python configuration test failed: {e}")
            return False
            
    def _test_docker_compose_syntax(self) -> bool:
        """Test Docker Compose file syntax."""
        compose_file = self.project_root / "docker-compose.production.yml"
        
        try:
            # Try to validate Docker Compose syntax
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("Docker Compose syntax is valid")
                return True
            else:
                self.logger.error(f"Docker Compose syntax error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.warning("docker-compose not installed, skipping syntax check")
            return True  # Don't fail if docker-compose is not available
        except Exception as e:
            self.logger.error(f"Docker Compose test error: {e}")
            return False
            
    def _generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        report = {
            "timestamp": time.time(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "duration": r.duration,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        # Save report
        report_file = self.project_root / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Test report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("ARXOS TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {report['summary']['success_rate']:.1f}%")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if not result.success:
                    print(f"  ✗ {result.name}")
                    if result.error:
                        print(f"    Error: {result.error}")
                        
        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Arxos comprehensive test runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--suite", help="Run specific test suite")
    
    args = parser.parse_args()
    
    runner = ArxosTestRunner(verbose=args.verbose)
    
    if args.suite:
        # Run specific test suite
        suite_methods = {
            "bridge": runner._test_symbol_recognition_bridge,
            "auth": runner._test_api_authentication,
            "arxobject": runner._test_arxobject_operations,
            "config": runner._test_configuration,
            "docker": runner._test_docker_setup,
            "integration": runner._test_service_integration
        }
        
        if args.suite in suite_methods:
            success = suite_methods[args.suite]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(suite_methods.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()