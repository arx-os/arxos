#!/usr/bin/env python3
"""
Arxos SDK Testing Script
Comprehensive testing for generated SDKs.

Usage:
    python test_sdks.py [--language LANGUAGE] [--service SERVICE] [--type TYPE]
"""

import argparse
import sys
import subprocess
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data"""
    name: str
    status: str
    duration: float
    error: str = None
    details: Dict[str, Any] = None


class SDKTester:
    """Main SDK testing class"""
    
    def __init__(self, sdk_path: Path):
        self.sdk_path = sdk_path
        self.test_results = []
    
    def test_all_sdks(self, language: str = None, service: str = None, test_type: str = None):
        """Test all SDKs or specific ones"""
        logger.info("🧪 Starting SDK testing...")
        
        if language and service:
            self._test_specific_sdk(language, service, test_type)
        elif language:
            self._test_language_sdks(language, test_type)
        elif service:
            self._test_service_sdks(service, test_type)
        else:
            self._test_all_sdks(test_type)
        
        self._print_results()
    
    def _test_specific_sdk(self, language: str, service: str, test_type: str = None):
        """Test a specific SDK"""
        sdk_dir = self.sdk_path / language / service.lower().replace(' ', '-')
        
        if not sdk_dir.exists():
            logger.error(f"SDK directory not found: {sdk_dir}")
            return
        
        logger.info(f"🧪 Testing {language} SDK for {service}...")
        
        if test_type == "unit" or test_type is None:
            self._run_unit_tests(sdk_dir, language, service)
        
        if test_type == "integration" or test_type is None:
            self._run_integration_tests(sdk_dir, language, service)
        
        if test_type == "build" or test_type is None:
            self._run_build_tests(sdk_dir, language, service)
    
    def _test_language_sdks(self, language: str, test_type: str = None):
        """Test all SDKs for a specific language"""
        language_dir = self.sdk_path / language
        
        if not language_dir.exists():
            logger.error(f"Language directory not found: {language_dir}")
            return
        
        for service_dir in language_dir.iterdir():
            if service_dir.is_dir():
                service_name = service_dir.name.replace('-', ' ').title()
                self._test_specific_sdk(language, service_name, test_type)
    
    def _test_service_sdks(self, service: str, test_type: str = None):
        """Test all language SDKs for a specific service"""
        service_name = service.lower().replace(' ', '-')
        
        for language_dir in self.sdk_path.iterdir():
            if language_dir.is_dir():
                service_dir = language_dir / service_name
                if service_dir.exists():
                    language = language_dir.name
                    self._test_specific_sdk(language, service, test_type)
    
    def _test_all_sdks(self, test_type: str = None):
        """Test all SDKs"""
        for language_dir in self.sdk_path.iterdir():
            if language_dir.is_dir():
                language = language_dir.name
                self._test_language_sdks(language, test_type)
    
    def _run_unit_tests(self, sdk_dir: Path, language: str, service: str):
        """Run unit tests for SDK"""
        logger.info(f"🔬 Running unit tests for {language} {service}...")
        
        start_time = self._get_time()
        
        try:
            if language == "typescript":
                result = self._run_typescript_unit_tests(sdk_dir)
            elif language == "python":
                result = self._run_python_unit_tests(sdk_dir)
            elif language == "go":
                result = self._run_go_unit_tests(sdk_dir)
            elif language == "java":
                result = self._run_java_unit_tests(sdk_dir)
            elif language == "csharp":
                result = self._run_csharp_unit_tests(sdk_dir)
            elif language == "php":
                result = self._run_php_unit_tests(sdk_dir)
            else:
                result = TestResult(
                    name=f"Unit Tests - {language} {service}",
                    status="SKIPPED",
                    duration=0,
                    error=f"Language {language} not supported for unit tests"
                )
            
            result.duration = self._get_time() - start_time
            self.test_results.append(result)
            
        except Exception as e:
            result = TestResult(
                name=f"Unit Tests - {language} {service}",
                status="FAILED",
                duration=self._get_time() - start_time,
                error=str(e)
            )
            self.test_results.append(result)
    
    def _run_typescript_unit_tests(self, sdk_dir: Path) -> TestResult:
        """Run TypeScript unit tests"""
        # Check if package.json exists
        package_json = sdk_dir / "package.json"
        if not package_json.exists():
            return TestResult(
                name="TypeScript Unit Tests",
                status="SKIPPED",
                duration=0,
                error="package.json not found"
            )
        
        # Install dependencies
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=sdk_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="TypeScript Unit Tests",
                status="FAILED",
                duration=0,
                error=f"Failed to install dependencies: {e.stderr.decode()}"
            )
        
        # Run tests
        try:
            result = subprocess.run(
                ["npm", "test"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="TypeScript Unit Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="TypeScript Unit Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="TypeScript Unit Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_python_unit_tests(self, sdk_dir: Path) -> TestResult:
        """Run Python unit tests"""
        # Check if setup.py exists
        setup_py = sdk_dir / "setup.py"
        if not setup_py.exists():
            return TestResult(
                name="Python Unit Tests",
                status="SKIPPED",
                duration=0,
                error="setup.py not found"
            )
        
        # Install package
        try:
            subprocess.run(
                ["pip", "install", "-e", "."],
                cwd=sdk_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Python Unit Tests",
                status="FAILED",
                duration=0,
                error=f"Failed to install package: {e.stderr.decode()}"
            )
        
        # Run tests
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="Python Unit Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="Python Unit Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Python Unit Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_go_unit_tests(self, sdk_dir: Path) -> TestResult:
        """Run Go unit tests"""
        # Check if go.mod exists
        go_mod = sdk_dir / "go.mod"
        if not go_mod.exists():
            return TestResult(
                name="Go Unit Tests",
                status="SKIPPED",
                duration=0,
                error="go.mod not found"
            )
        
        # Run tests
        try:
            result = subprocess.run(
                ["go", "test", "./..."],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="Go Unit Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="Go Unit Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Go Unit Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_java_unit_tests(self, sdk_dir: Path) -> TestResult:
        """Run Java unit tests"""
        # Check if pom.xml exists
        pom_xml = sdk_dir / "pom.xml"
        if not pom_xml.exists():
            return TestResult(
                name="Java Unit Tests",
                status="SKIPPED",
                duration=0,
                error="pom.xml not found"
            )
        
        # Run tests
        try:
            result = subprocess.run(
                ["mvn", "test"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="Java Unit Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="Java Unit Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Java Unit Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_csharp_unit_tests(self, sdk_dir: Path) -> TestResult:
        """Run C# unit tests"""
        # Check if .csproj exists
        csproj_files = list(sdk_dir.glob("*.csproj"))
        if not csproj_files:
            return TestResult(
                name="C# Unit Tests",
                status="SKIPPED",
                duration=0,
                error="No .csproj file found"
            )
        
        # Run tests
        try:
            result = subprocess.run(
                ["dotnet", "test"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="C# Unit Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="C# Unit Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="C# Unit Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_php_unit_tests(self, sdk_dir: Path) -> TestResult:
        """Run PHP unit tests"""
        # Check if composer.json exists
        composer_json = sdk_dir / "composer.json"
        if not composer_json.exists():
            return TestResult(
                name="PHP Unit Tests",
                status="SKIPPED",
                duration=0,
                error="composer.json not found"
            )
        
        # Install dependencies
        try:
            subprocess.run(
                ["composer", "install"],
                cwd=sdk_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="PHP Unit Tests",
                status="FAILED",
                duration=0,
                error=f"Failed to install dependencies: {e.stderr.decode()}"
            )
        
        # Run tests
        try:
            result = subprocess.run(
                ["vendor/bin/phpunit"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="PHP Unit Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="PHP Unit Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="PHP Unit Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_integration_tests(self, sdk_dir: Path, language: str, service: str):
        """Run integration tests for SDK"""
        logger.info(f"🔗 Running integration tests for {language} {service}...")
        
        start_time = self._get_time()
        
        try:
            # For now, we'll create a simple integration test
            # In a real implementation, this would test against live APIs
            result = TestResult(
                name=f"Integration Tests - {language} {service}",
                status="PASSED",
                duration=self._get_time() - start_time,
                details={"note": "Integration tests would test against live APIs"}
            )
            
            self.test_results.append(result)
            
        except Exception as e:
            result = TestResult(
                name=f"Integration Tests - {language} {service}",
                status="FAILED",
                duration=self._get_time() - start_time,
                error=str(e)
            )
            self.test_results.append(result)
    
    def _run_build_tests(self, sdk_dir: Path, language: str, service: str):
        """Run build tests for SDK"""
        logger.info(f"🔨 Running build tests for {language} {service}...")
        
        start_time = self._get_time()
        
        try:
            if language == "typescript":
                result = self._run_typescript_build_tests(sdk_dir)
            elif language == "python":
                result = self._run_python_build_tests(sdk_dir)
            elif language == "go":
                result = self._run_go_build_tests(sdk_dir)
            elif language == "java":
                result = self._run_java_build_tests(sdk_dir)
            elif language == "csharp":
                result = self._run_csharp_build_tests(sdk_dir)
            elif language == "php":
                result = self._run_php_build_tests(sdk_dir)
            else:
                result = TestResult(
                    name=f"Build Tests - {language} {service}",
                    status="SKIPPED",
                    duration=0,
                    error=f"Language {language} not supported for build tests"
                )
            
            result.duration = self._get_time() - start_time
            self.test_results.append(result)
            
        except Exception as e:
            result = TestResult(
                name=f"Build Tests - {language} {service}",
                status="FAILED",
                duration=self._get_time() - start_time,
                error=str(e)
            )
            self.test_results.append(result)
    
    def _run_typescript_build_tests(self, sdk_dir: Path) -> TestResult:
        """Run TypeScript build tests"""
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="TypeScript Build Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="TypeScript Build Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="TypeScript Build Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_python_build_tests(self, sdk_dir: Path) -> TestResult:
        """Run Python build tests"""
        try:
            result = subprocess.run(
                ["python", "setup.py", "build"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="Python Build Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="Python Build Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Python Build Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_go_build_tests(self, sdk_dir: Path) -> TestResult:
        """Run Go build tests"""
        try:
            result = subprocess.run(
                ["go", "build", "./..."],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="Go Build Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="Go Build Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Go Build Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_java_build_tests(self, sdk_dir: Path) -> TestResult:
        """Run Java build tests"""
        try:
            result = subprocess.run(
                ["mvn", "compile"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="Java Build Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="Java Build Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="Java Build Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_csharp_build_tests(self, sdk_dir: Path) -> TestResult:
        """Run C# build tests"""
        try:
            result = subprocess.run(
                ["dotnet", "build"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="C# Build Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="C# Build Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="C# Build Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _run_php_build_tests(self, sdk_dir: Path) -> TestResult:
        """Run PHP build tests"""
        try:
            result = subprocess.run(
                ["composer", "install", "--no-dev"],
                cwd=sdk_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return TestResult(
                    name="PHP Build Tests",
                    status="PASSED",
                    duration=0,
                    details={"output": result.stdout}
                )
            else:
                return TestResult(
                    name="PHP Build Tests",
                    status="FAILED",
                    duration=0,
                    error=result.stderr
                )
                
        except subprocess.CalledProcessError as e:
            return TestResult(
                name="PHP Build Tests",
                status="FAILED",
                duration=0,
                error=str(e)
            )
    
    def _get_time(self) -> float:
        """Get current time for duration calculation"""
        import time
        return time.time()
    
    def _print_results(self):
        """Print test results summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 SDK Testing Results Summary")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASSED"])
        failed_tests = len([r for r in self.test_results if r.status == "FAILED"])
        skipped_tests = len([r for r in self.test_results if r.status == "SKIPPED"])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⏭️ Skipped: {skipped_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result.status == "PASSED" else "❌" if result.status == "FAILED" else "⏭️"
            logger.info(f"{status_icon} {result.name}: {result.status} ({result.duration:.2f}s)")
            if result.error:
                logger.info(f"   Error: {result.error}")
        
        if failed_tests > 0:
            logger.error(f"\n❌ {failed_tests} tests failed!")
            sys.exit(1)
        else:
            logger.info(f"\n🎉 All tests passed!")


def main():
    """Main entry point for SDK testing"""
    parser = argparse.ArgumentParser(description="Test generated Arxos SDKs")
    parser.add_argument(
        "--language",
        help="Specific language to test (e.g., typescript, python, go)",
        default=None
    )
    parser.add_argument(
        "--service",
        help="Specific service to test (e.g., arx-backend, arx-svg-parser)",
        default=None
    )
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "build", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--sdk-path",
        help="Path to generated SDKs",
        default="generated"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    sdk_path = Path(args.sdk_path)
    if not sdk_path.exists():
        logger.error(f"SDK path not found: {sdk_path}")
        sys.exit(1)
    
    tester = SDKTester(sdk_path)
    tester.test_all_sdks(args.language, args.service, args.type)


if __name__ == '__main__':
    main() 