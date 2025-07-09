#!/usr/bin/env python3
"""
Security Testing Script for Arxos Platform

This script performs comprehensive security testing including:
- Authentication testing
- Authorization testing
- Input validation testing
- Data protection testing
- Audit logging testing
- Network security testing
"""

import requests
import json
import time
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional
import logging
import argparse
import csv
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityTestResult:
    """Security test result data class"""
    test_name: str
    category: str
    status: str
    details: Dict
    vulnerability_level: str  # low, medium, high, critical
    recommendation: str

class SecurityTester:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.results = []
        
    def run_security_tests(self) -> List[SecurityTestResult]:
        """Run comprehensive security tests"""
        logger.info("Starting security testing")
        
        # Authentication tests
        auth_results = self.test_authentication()
        self.results.extend(auth_results)
        
        # Authorization tests
        authz_results = self.test_authorization()
        self.results.extend(authz_results)
        
        # Input validation tests
        input_results = self.test_input_validation()
        self.results.extend(input_results)
        
        # Data protection tests
        data_results = self.test_data_protection()
        self.results.extend(data_results)
        
        # Audit logging tests
        audit_results = self.test_audit_logging()
        self.results.extend(audit_results)
        
        # Network security tests
        network_results = self.test_network_security()
        self.results.extend(network_results)
        
        return self.results
    
    def test_authentication(self) -> List[SecurityTestResult]:
        """Test authentication mechanisms"""
        logger.info("Testing authentication")
        results = []
        
        # Test valid API key
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/api/v1/health", headers=headers)
            
            if response.status_code == 200:
                results.append(SecurityTestResult(
                    test_name="Valid API Key Authentication",
                    category="authentication",
                    status="passed",
                    details={"status_code": response.status_code},
                    vulnerability_level="low",
                    recommendation="Authentication working correctly"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="Valid API Key Authentication",
                    category="authentication",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix API key authentication"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Valid API Key Authentication",
                category="authentication",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate authentication error"
            ))
        
        # Test invalid API key
        try:
            headers = {"Authorization": "Bearer invalid-key"}
            response = requests.get(f"{self.base_url}/api/v1/health", headers=headers)
            
            if response.status_code == 401:
                results.append(SecurityTestResult(
                    test_name="Invalid API Key Rejection",
                    category="authentication",
                    status="passed",
                    details={"status_code": response.status_code},
                    vulnerability_level="low",
                    recommendation="Invalid key rejection working correctly"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="Invalid API Key Rejection",
                    category="authentication",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix invalid key rejection"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Invalid API Key Rejection",
                category="authentication",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate authentication error"
            ))
        
        # Test missing API key
        try:
            response = requests.get(f"{self.base_url}/api/v1/health")
            
            if response.status_code == 401:
                results.append(SecurityTestResult(
                    test_name="Missing API Key Rejection",
                    category="authentication",
                    status="passed",
                    details={"status_code": response.status_code},
                    vulnerability_level="low",
                    recommendation="Missing key rejection working correctly"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="Missing API Key Rejection",
                    category="authentication",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix missing key rejection"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Missing API Key Rejection",
                category="authentication",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate authentication error"
            ))
        
        return results
    
    def test_authorization(self) -> List[SecurityTestResult]:
        """Test authorization and access control"""
        logger.info("Testing authorization")
        results = []
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Test RBAC permission checking
        try:
            data = {
                "user_id": "test_user",
                "resource": "building",
                "action": "read"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/security/rbac/check-permission",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if "has_permission" in result_data:
                    results.append(SecurityTestResult(
                        test_name="RBAC Permission Check",
                        category="authorization",
                        status="passed",
                        details={"response": result_data},
                        vulnerability_level="low",
                        recommendation="RBAC working correctly"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name="RBAC Permission Check",
                        category="authorization",
                        status="failed",
                        details={"response": result_data},
                        vulnerability_level="medium",
                        recommendation="Fix RBAC response format"
                    ))
            else:
                results.append(SecurityTestResult(
                    test_name="RBAC Permission Check",
                    category="authorization",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix RBAC endpoint"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="RBAC Permission Check",
                category="authorization",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate RBAC error"
            ))
        
        # Test resource isolation
        try:
            # Test access to restricted resource
            response = requests.get(
                f"{self.base_url}/api/v1/security/audit/logs",
                headers=headers
            )
            
            if response.status_code == 403:
                results.append(SecurityTestResult(
                    test_name="Resource Isolation",
                    category="authorization",
                    status="passed",
                    details={"status_code": response.status_code},
                    vulnerability_level="low",
                    recommendation="Resource isolation working correctly"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="Resource Isolation",
                    category="authorization",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix resource isolation"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Resource Isolation",
                category="authorization",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate authorization error"
            ))
        
        return results
    
    def test_input_validation(self) -> List[SecurityTestResult]:
        """Test input validation and sanitization"""
        logger.info("Testing input validation")
        results = []
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Test SQL injection prevention
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "admin'--",
            "1' OR '1'='1'--"
        ]
        
        for i, malicious_input in enumerate(malicious_inputs):
            try:
                data = {
                    "user_id": malicious_input,
                    "resource": "building",
                    "action": "read"
                }
                response = requests.post(
                    f"{self.base_url}/api/v1/security/rbac/check-permission",
                    json=data,
                    headers=headers
                )
                
                # Check if request was handled safely
                if response.status_code in [400, 401, 403, 422]:
                    results.append(SecurityTestResult(
                        test_name=f"SQL Injection Prevention {i+1}",
                        category="input_validation",
                        status="passed",
                        details={"input": malicious_input, "status_code": response.status_code},
                        vulnerability_level="low",
                        recommendation="SQL injection prevention working"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name=f"SQL Injection Prevention {i+1}",
                        category="input_validation",
                        status="failed",
                        details={"input": malicious_input, "status_code": response.status_code},
                        vulnerability_level="critical",
                        recommendation="Fix SQL injection vulnerability"
                    ))
            except Exception as e:
                results.append(SecurityTestResult(
                    test_name=f"SQL Injection Prevention {i+1}",
                    category="input_validation",
                    status="error",
                    details={"input": malicious_input, "error": str(e)},
                    vulnerability_level="high",
                    recommendation="Investigate input validation error"
                ))
        
        # Test XSS prevention
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for i, xss_input in enumerate(xss_inputs):
            try:
                data = {
                    "data": {"test": xss_input},
                    "classification": "internal"
                }
                response = requests.post(
                    f"{self.base_url}/api/v1/security/privacy/controls",
                    json=data,
                    headers=headers
                )
                
                # Check if XSS was prevented
                if response.status_code in [400, 422]:
                    results.append(SecurityTestResult(
                        test_name=f"XSS Prevention {i+1}",
                        category="input_validation",
                        status="passed",
                        details={"input": xss_input, "status_code": response.status_code},
                        vulnerability_level="low",
                        recommendation="XSS prevention working"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name=f"XSS Prevention {i+1}",
                        category="input_validation",
                        status="failed",
                        details={"input": xss_input, "status_code": response.status_code},
                        vulnerability_level="high",
                        recommendation="Fix XSS vulnerability"
                    ))
            except Exception as e:
                results.append(SecurityTestResult(
                    test_name=f"XSS Prevention {i+1}",
                    category="input_validation",
                    status="error",
                    details={"input": xss_input, "error": str(e)},
                    vulnerability_level="high",
                    recommendation="Investigate XSS prevention error"
                ))
        
        # Test file upload validation
        try:
            # Test malicious file upload
            files = {'file': ('test.php', b'<?php echo "malicious"; ?>', 'text/plain')}
            response = requests.post(
                f"{self.base_url}/api/v1/upload/svg",
                files=files,
                headers=headers
            )
            
            if response.status_code in [400, 422]:
                results.append(SecurityTestResult(
                    test_name="File Upload Validation",
                    category="input_validation",
                    status="passed",
                    details={"status_code": response.status_code},
                    vulnerability_level="low",
                    recommendation="File upload validation working"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="File Upload Validation",
                    category="input_validation",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix file upload validation"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="File Upload Validation",
                category="input_validation",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate file upload error"
            ))
        
        return results
    
    def test_data_protection(self) -> List[SecurityTestResult]:
        """Test data protection mechanisms"""
        logger.info("Testing data protection")
        results = []
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Test encryption
        try:
            test_data = {"sensitive": "data", "user_id": "12345"}
            response = requests.post(
                f"{self.base_url}/api/v1/security/encryption/encrypt",
                json={"data": test_data, "layer": "storage"},
                headers=headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if "encrypted_data" in result_data:
                    results.append(SecurityTestResult(
                        test_name="Data Encryption",
                        category="data_protection",
                        status="passed",
                        details={"encryption_layer": "storage"},
                        vulnerability_level="low",
                        recommendation="Encryption working correctly"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name="Data Encryption",
                        category="data_protection",
                        status="failed",
                        details={"response": result_data},
                        vulnerability_level="high",
                        recommendation="Fix encryption response format"
                    ))
            else:
                results.append(SecurityTestResult(
                    test_name="Data Encryption",
                    category="data_protection",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix encryption endpoint"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Data Encryption",
                category="data_protection",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate encryption error"
            ))
        
        # Test privacy controls
        try:
            test_data = {"user_info": "sensitive", "building_data": "confidential"}
            response = requests.post(
                f"{self.base_url}/api/v1/security/privacy/controls",
                json={"data": test_data, "classification": "confidential"},
                headers=headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if "privacy_metadata" in result_data:
                    results.append(SecurityTestResult(
                        test_name="Privacy Controls",
                        category="data_protection",
                        status="passed",
                        details={"classification": "confidential"},
                        vulnerability_level="low",
                        recommendation="Privacy controls working correctly"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name="Privacy Controls",
                        category="data_protection",
                        status="failed",
                        details={"response": result_data},
                        vulnerability_level="medium",
                        recommendation="Fix privacy controls response format"
                    ))
            else:
                results.append(SecurityTestResult(
                    test_name="Privacy Controls",
                    category="data_protection",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix privacy controls endpoint"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Privacy Controls",
                category="data_protection",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate privacy controls error"
            ))
        
        return results
    
    def test_audit_logging(self) -> List[SecurityTestResult]:
        """Test audit logging and compliance"""
        logger.info("Testing audit logging")
        results = []
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Test audit event logging
        try:
            audit_data = {
                "event_type": "security_test",
                "user_id": "test_user",
                "resource_id": "test_resource",
                "action": "read",
                "details": {"test": "audit_logging"},
                "correlation_id": "test_corr_123",
                "ip_address": "127.0.0.1",
                "user_agent": "SecurityTest/1.0",
                "success": True
            }
            response = requests.post(
                f"{self.base_url}/api/v1/security/audit/log",
                json=audit_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if "event_id" in result_data:
                    results.append(SecurityTestResult(
                        test_name="Audit Event Logging",
                        category="audit_logging",
                        status="passed",
                        details={"event_id": result_data["event_id"]},
                        vulnerability_level="low",
                        recommendation="Audit logging working correctly"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name="Audit Event Logging",
                        category="audit_logging",
                        status="failed",
                        details={"response": result_data},
                        vulnerability_level="medium",
                        recommendation="Fix audit logging response format"
                    ))
            else:
                results.append(SecurityTestResult(
                    test_name="Audit Event Logging",
                    category="audit_logging",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix audit logging endpoint"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Audit Event Logging",
                category="audit_logging",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate audit logging error"
            ))
        
        # Test compliance reporting
        try:
            report_data = {
                "report_type": "data_access",
                "start_date": "2024-12-01T00:00:00Z",
                "end_date": "2024-12-19T23:59:59Z"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/security/audit/compliance-report",
                json=report_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if "total_events" in result_data:
                    results.append(SecurityTestResult(
                        test_name="Compliance Reporting",
                        category="audit_logging",
                        status="passed",
                        details={"total_events": result_data["total_events"]},
                        vulnerability_level="low",
                        recommendation="Compliance reporting working correctly"
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name="Compliance Reporting",
                        category="audit_logging",
                        status="failed",
                        details={"response": result_data},
                        vulnerability_level="medium",
                        recommendation="Fix compliance reporting response format"
                    ))
            else:
                results.append(SecurityTestResult(
                    test_name="Compliance Reporting",
                    category="audit_logging",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="high",
                    recommendation="Fix compliance reporting endpoint"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Compliance Reporting",
                category="audit_logging",
                status="error",
                details={"error": str(e)},
                vulnerability_level="high",
                recommendation="Investigate compliance reporting error"
            ))
        
        return results
    
    def test_network_security(self) -> List[SecurityTestResult]:
        """Test network security measures"""
        logger.info("Testing network security")
        results = []
        
        # Test HTTPS enforcement
        try:
            # Try HTTP request
            response = requests.get(f"http://{self.base_url.replace('https://', '').replace('http://', '')}/health", allow_redirects=False)
            
            if response.status_code in [301, 302, 308]:
                results.append(SecurityTestResult(
                    test_name="HTTPS Enforcement",
                    category="network_security",
                    status="passed",
                    details={"redirect_status": response.status_code},
                    vulnerability_level="low",
                    recommendation="HTTPS enforcement working correctly"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="HTTPS Enforcement",
                    category="network_security",
                    status="failed",
                    details={"status_code": response.status_code},
                    vulnerability_level="medium",
                    recommendation="Enable HTTPS enforcement"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="HTTPS Enforcement",
                category="network_security",
                status="error",
                details={"error": str(e)},
                vulnerability_level="medium",
                recommendation="Investigate HTTPS enforcement"
            ))
        
        # Test security headers
        try:
            response = requests.get(f"{self.base_url}/health")
            headers = response.headers
            
            security_headers = {
                "X-Frame-Options": "Frame options header",
                "X-Content-Type-Options": "Content type options header",
                "X-XSS-Protection": "XSS protection header",
                "Strict-Transport-Security": "HSTS header",
                "Content-Security-Policy": "CSP header"
            }
            
            missing_headers = []
            for header, description in security_headers.items():
                if header not in headers:
                    missing_headers.append(description)
            
            if not missing_headers:
                results.append(SecurityTestResult(
                    test_name="Security Headers",
                    category="network_security",
                    status="passed",
                    details={"headers_present": list(security_headers.keys())},
                    vulnerability_level="low",
                    recommendation="Security headers properly configured"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="Security Headers",
                    category="network_security",
                    status="failed",
                    details={"missing_headers": missing_headers},
                    vulnerability_level="medium",
                    recommendation=f"Add missing security headers: {', '.join(missing_headers)}"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Security Headers",
                category="network_security",
                status="error",
                details={"error": str(e)},
                vulnerability_level="medium",
                recommendation="Investigate security headers"
            ))
        
        # Test rate limiting
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(20):
                response = requests.get(f"{self.base_url}/health")
                responses.append(response.status_code)
                time.sleep(0.1)
            
            # Check if rate limiting is working
            if 429 in responses:
                results.append(SecurityTestResult(
                    test_name="Rate Limiting",
                    category="network_security",
                    status="passed",
                    details={"rate_limit_triggered": True},
                    vulnerability_level="low",
                    recommendation="Rate limiting working correctly"
                ))
            else:
                results.append(SecurityTestResult(
                    test_name="Rate Limiting",
                    category="network_security",
                    status="failed",
                    details={"responses": responses},
                    vulnerability_level="medium",
                    recommendation="Enable rate limiting"
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Rate Limiting",
                category="network_security",
                status="error",
                details={"error": str(e)},
                vulnerability_level="medium",
                recommendation="Investigate rate limiting"
            ))
        
        return results
    
    def analyze_results(self) -> Dict:
        """Analyze security test results"""
        analysis = {
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': len([r for r in self.results if r.status == 'passed']),
                'failed_tests': len([r for r in self.results if r.status == 'failed']),
                'error_tests': len([r for r in self.results if r.status == 'error']),
                'critical_vulnerabilities': len([r for r in self.results if r.vulnerability_level == 'critical']),
                'high_vulnerabilities': len([r for r in self.results if r.vulnerability_level == 'high']),
                'medium_vulnerabilities': len([r for r in self.results if r.vulnerability_level == 'medium']),
                'low_vulnerabilities': len([r for r in self.results if r.vulnerability_level == 'low'])
            },
            'categories': {},
            'recommendations': []
        }
        
        # Analyze by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'error': 0,
                    'vulnerabilities': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                }
            
            categories[result.category]['total'] += 1
            categories[result.category][result.status] += 1
            categories[result.category]['vulnerabilities'][result.vulnerability_level] += 1
        
        analysis['categories'] = categories
        
        # Generate recommendations
        critical_vulns = [r for r in self.results if r.vulnerability_level == 'critical']
        high_vulns = [r for r in self.results if r.vulnerability_level == 'high']
        
        if critical_vulns:
            analysis['recommendations'].append(f"CRITICAL: {len(critical_vulns)} critical vulnerabilities found. Fix immediately.")
        
        if high_vulns:
            analysis['recommendations'].append(f"HIGH: {len(high_vulns)} high severity vulnerabilities found. Fix within 24 hours.")
        
        failed_tests = [r for r in self.results if r.status == 'failed']
        if failed_tests:
            analysis['recommendations'].append(f"FAILED: {len(failed_tests)} tests failed. Review and fix.")
        
        if analysis['summary']['passed_tests'] == analysis['summary']['total_tests']:
            analysis['recommendations'].append("All security tests passed. System is secure.")
        
        return analysis
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate security test report"""
        report = f"""
# Arxos Platform Security Test Report

## Test Summary
- **Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Base URL**: {self.base_url}
- **Total Tests**: {analysis['summary']['total_tests']}
- **Passed Tests**: {analysis['summary']['passed_tests']}
- **Failed Tests**: {analysis['summary']['failed_tests']}
- **Error Tests**: {analysis['summary']['error_tests']}

## Vulnerability Summary
- **Critical**: {analysis['summary']['critical_vulnerabilities']}
- **High**: {analysis['summary']['high_vulnerabilities']}
- **Medium**: {analysis['summary']['medium_vulnerabilities']}
- **Low**: {analysis['summary']['low_vulnerabilities']}

## Category Analysis
"""
        
        for category, stats in analysis['categories'].items():
            report += f"""
### {category.title()}
- **Total Tests**: {stats['total']}
- **Passed**: {stats['passed']}
- **Failed**: {stats['failed']}
- **Errors**: {stats['error']}
- **Vulnerabilities**: Critical={stats['vulnerabilities']['critical']}, High={stats['vulnerabilities']['high']}, Medium={stats['vulnerabilities']['medium']}, Low={stats['vulnerabilities']['low']}
"""
        
        report += f"""
## Detailed Results
"""
        
        for result in self.results:
            status_icon = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
            report += f"""
### {status_icon} {result.test_name}
- **Category**: {result.category}
- **Status**: {result.status}
- **Vulnerability Level**: {result.vulnerability_level}
- **Details**: {result.details}
- **Recommendation**: {result.recommendation}
"""
        
        report += f"""
## Recommendations
"""
        for recommendation in analysis['recommendations']:
            report += f"- {recommendation}\n"
        
        return report
    
    def save_results(self, analysis: Dict, output_file: str):
        """Save results to file"""
        # Save detailed results as JSON
        json_file = output_file.replace('.csv', '.json')
        with open(json_file, 'w') as f:
            json.dump({
                'results': [vars(r) for r in self.results],
                'analysis': analysis
            }, f, indent=2)
        
        # Save summary as CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Test Name', 'Category', 'Status', 'Vulnerability Level', 'Recommendation'
            ])
            
            for result in self.results:
                writer.writerow([
                    result.test_name,
                    result.category,
                    result.status,
                    result.vulnerability_level,
                    result.recommendation
                ])
        
        logger.info(f"Results saved to {json_file} and {output_file}")

def main():
    """Main security testing function"""
    parser = argparse.ArgumentParser(description='Security Testing for Arxos Platform')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL for testing')
    parser.add_argument('--api-key', default='test-api-key', help='API key for authentication')
    parser.add_argument('--output', default='security_test_results.csv', help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize security tester
    tester = SecurityTester(args.base_url, args.api_key)
    
    logger.info(f"Running security tests against {args.base_url}")
    
    # Run security tests
    results = tester.run_security_tests()
    
    # Analyze results
    analysis = tester.analyze_results()
    
    # Generate report
    report = tester.generate_report(analysis)
    
    # Save results
    tester.save_results(analysis, args.output)
    
    # Print summary
    print("\n" + "="*50)
    print("SECURITY TEST SUMMARY")
    print("="*50)
    print(f"Total Tests: {analysis['summary']['total_tests']}")
    print(f"Passed: {analysis['summary']['passed_tests']}")
    print(f"Failed: {analysis['summary']['failed_tests']}")
    print(f"Errors: {analysis['summary']['error_tests']}")
    print(f"Critical Vulnerabilities: {analysis['summary']['critical_vulnerabilities']}")
    print(f"High Vulnerabilities: {analysis['summary']['high_vulnerabilities']}")
    
    print("\nRECOMMENDATIONS:")
    for recommendation in analysis['recommendations']:
        print(f"- {recommendation}")
    
    print(f"\nDetailed report saved to: {args.output}")
    print("="*50)

if __name__ == "__main__":
    main() 