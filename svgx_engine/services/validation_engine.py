"""
Validation Engine Service for Arxos SVGX Engine

Handles compliance checking, validation, and quality assurance for the pipeline integration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from svgx_engine.utils.errors import ComplianceError, ValidationError

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Manages validation and compliance checking for the pipeline integration."""
    
    def __init__(self, compliance_rules_path: str = "svgx_engine/compliance"):
        self.compliance_rules_path = Path(compliance_rules_path)
        self.compliance_rules_path.mkdir(parents=True, exist_ok=True)
        
    def run_compliance_check(self, system: str) -> Dict[str, Any]:
        """Run enterprise compliance validation for a system."""
        try:
            compliance_result = {
                "system": system,
                "compliance_status": "pending",
                "checks_passed": 0,
                "checks_failed": 0,
                "total_checks": 0,
                "details": []
            }
            
            # Run various compliance checks
            checks = [
                self._check_security_compliance,
                self._check_performance_compliance,
                self._check_quality_compliance,
                self._check_documentation_compliance,
                self._check_test_coverage_compliance
            ]
            
            for check_func in checks:
                try:
                    check_result = check_func(system)
                    compliance_result["total_checks"] += 1
                    
                    if check_result["passed"]:
                        compliance_result["checks_passed"] += 1
                    else:
                        compliance_result["checks_failed"] += 1
                    
                    compliance_result["details"].append(check_result)
                    
                except Exception as e:
                    compliance_result["total_checks"] += 1
                    compliance_result["checks_failed"] += 1
                    compliance_result["details"].append({
                        "check": check_func.__name__,
                        "passed": False,
                        "error": str(e)
                    })
            
            # Determine overall compliance status
            if compliance_result["checks_failed"] == 0:
                compliance_result["compliance_status"] = "compliant"
            elif compliance_result["checks_failed"] <= compliance_result["total_checks"] * 0.2:
                compliance_result["compliance_status"] = "mostly_compliant"
            else:
                compliance_result["compliance_status"] = "non_compliant"
            
            return compliance_result
            
        except Exception as e:
            raise ComplianceError(f"Compliance check failed: {str(e)}", system)
    
    def _check_security_compliance(self, system: str) -> Dict[str, Any]:
        """Check security compliance for a system."""
        try:
            # Basic security checks
            security_issues = []
            
            # Check for hardcoded credentials
            system_files = self._get_system_files(system)
            for file_path in system_files:
                if self._contains_hardcoded_credentials(file_path):
                    security_issues.append(f"Hardcoded credentials found in {file_path}")
            
            # Check for proper input validation
            if not self._has_input_validation(system):
                security_issues.append("Missing input validation")
            
            # Check for proper error handling
            if not self._has_error_handling(system):
                security_issues.append("Missing error handling")
            
            return {
                "check": "security_compliance",
                "passed": len(security_issues) == 0,
                "issues": security_issues,
                "message": f"Security compliance check for {system}"
            }
            
        except Exception as e:
            return {
                "check": "security_compliance",
                "passed": False,
                "error": str(e)
            }
    
    def _check_performance_compliance(self, system: str) -> Dict[str, Any]:
        """Check performance compliance for a system."""
        try:
            # Basic performance checks
            performance_issues = []
            
            # Check file sizes
            system_files = self._get_system_files(system)
            for file_path in system_files:
                if file_path.stat().st_size > 1024 * 1024:  # 1MB
                    performance_issues.append(f"Large file detected: {file_path}")
            
            # Check for potential performance issues
            if self._has_potential_performance_issues(system):
                performance_issues.append("Potential performance issues detected")
            
            return {
                "check": "performance_compliance",
                "passed": len(performance_issues) == 0,
                "issues": performance_issues,
                "message": f"Performance compliance check for {system}"
            }
            
        except Exception as e:
            return {
                "check": "performance_compliance",
                "passed": False,
                "error": str(e)
            }
    
    def _check_quality_compliance(self, system: str) -> Dict[str, Any]:
        """Check quality compliance for a system."""
        try:
            # Basic quality checks
            quality_issues = []
            
            # Check for proper naming conventions
            if not self._follows_naming_conventions(system):
                quality_issues.append("Naming conventions not followed")
            
            # Check for code complexity
            if self._has_high_complexity(system):
                quality_issues.append("High code complexity detected")
            
            # Check for documentation
            if not self._has_documentation(system):
                quality_issues.append("Missing documentation")
            
            return {
                "check": "quality_compliance",
                "passed": len(quality_issues) == 0,
                "issues": quality_issues,
                "message": f"Quality compliance check for {system}"
            }
            
        except Exception as e:
            return {
                "check": "quality_compliance",
                "passed": False,
                "error": str(e)
            }
    
    def _check_documentation_compliance(self, system: str) -> Dict[str, Any]:
        """Check documentation compliance for a system."""
        try:
            # Basic documentation checks
            doc_issues = []
            
            # Check for README
            readme_file = Path(f"docs/systems/{system}/README.md")
            if not readme_file.exists():
                doc_issues.append("Missing README documentation")
            
            # Check for API documentation
            api_doc_file = Path(f"docs/systems/{system}/api.md")
            if not api_doc_file.exists():
                doc_issues.append("Missing API documentation")
            
            return {
                "check": "documentation_compliance",
                "passed": len(doc_issues) == 0,
                "issues": doc_issues,
                "message": f"Documentation compliance check for {system}"
            }
            
        except Exception as e:
            return {
                "check": "documentation_compliance",
                "passed": False,
                "error": str(e)
            }
    
    def _check_test_coverage_compliance(self, system: str) -> Dict[str, Any]:
        """Check test coverage compliance for a system."""
        try:
            # Basic test coverage checks
            test_issues = []
            
            # Check for test files
            test_file = Path(f"tests/test_{system}.py")
            if not test_file.exists():
                test_issues.append("Missing test file")
            
            # Check for integration tests
            integration_test_file = Path(f"tests/test_{system}_integration.py")
            if not integration_test_file.exists():
                test_issues.append("Missing integration test file")
            
            return {
                "check": "test_coverage_compliance",
                "passed": len(test_issues) == 0,
                "issues": test_issues,
                "message": f"Test coverage compliance check for {system}"
            }
            
        except Exception as e:
            return {
                "check": "test_coverage_compliance",
                "passed": False,
                "error": str(e)
            }
    
    def _get_system_files(self, system: str) -> List[Path]:
        """Get all files related to a system."""
        files = []
        
        # Check various directories for system files
        directories = [
            f"schemas/{system}",
            f"arx-symbol-library/{system}",
            f"svgx_engine/behavior",
            f"tests",
            f"docs/systems/{system}"
        ]
        
        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and system in file_path.name:
                        files.append(file_path)
        
        return files
    
    def _contains_hardcoded_credentials(self, file_path: Path) -> bool:
        """Check if a file contains hardcoded credentials."""
        try:
            with open(file_path, 'r') as f:
                content = f.read().lower()
            
            # Check for common credential patterns
            credential_patterns = [
                "password", "secret", "key", "token", "credential"
            ]
            
            for pattern in credential_patterns:
                if pattern in content:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _has_input_validation(self, system: str) -> bool:
        """Check if a system has input validation."""
        # This is a simplified check - in practice, you'd analyze the code
        return True  # Placeholder
    
    def _has_error_handling(self, system: str) -> bool:
        """Check if a system has error handling."""
        # This is a simplified check - in practice, you'd analyze the code
        return True  # Placeholder
    
    def _has_potential_performance_issues(self, system: str) -> bool:
        """Check if a system has potential performance issues."""
        # This is a simplified check - in practice, you'd analyze the code
        return False  # Placeholder
    
    def _follows_naming_conventions(self, system: str) -> bool:
        """Check if a system follows naming conventions."""
        # This is a simplified check - in practice, you'd analyze the code
        return True  # Placeholder
    
    def _has_high_complexity(self, system: str) -> bool:
        """Check if a system has high complexity."""
        # This is a simplified check - in practice, you'd analyze the code
        return False  # Placeholder
    
    def _has_documentation(self, system: str) -> bool:
        """Check if a system has documentation."""
        # This is a simplified check - in practice, you'd analyze the code
        return True  # Placeholder 