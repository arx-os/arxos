#!/usr/bin/env python3
"""
Security Audit Script

This script performs a comprehensive security audit of the Arxos codebase,
identifying and fixing security vulnerabilities.

Security Focus Areas:
- Input validation and sanitization
- Authentication and authorization
- SQL injection prevention
- XSS prevention
- Dependency vulnerabilities
- Configuration security
- Error handling security

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import ast


class SecurityVulnerability:
    """Represents a security vulnerability"""
    
    def __init__(self, file_path: str, line_number: int, vulnerability_type: str, 
                 description: str, severity: str, fix_suggestion: str):
        self.file_path = file_path
        self.line_number = line_number
        self.vulnerability_type = vulnerability_type
        self.description = description
        self.severity = severity
        self.fix_suggestion = fix_suggestion


class SecurityAuditor:
    """Performs security audit of the codebase"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.vulnerabilities: List[SecurityVulnerability] = []
        
        # Security patterns to check
        self.dangerous_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*[\'"][^\'"]*\+\s*\w+',
                r'cursor\.execute\s*\(\s*[\'"][^\'"]*\+\s*\w+',
                r'f\s*[\'"][^\'"]*\{[^}]*\}\s*[\'"]\s*\.execute',
            ],
            'xss': [
                r'innerHTML\s*=',
                r'outerHTML\s*=',
                r'document\.write\s*\(',
                r'eval\s*\(',
            ],
            'command_injection': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'subprocess\.Popen\s*\(',
                r'exec\s*\(',
            ],
            'path_traversal': [
                r'open\s*\(\s*\w+\s*\+\s*[\'"]\.\./',
                r'Path\s*\(\s*\w+\s*\+\s*[\'"]\.\./',
            ],
            'hardcoded_credentials': [
                r'password\s*=\s*[\'"][^\'"]+[\'"]',
                r'api_key\s*=\s*[\'"][^\'"]+[\'"]',
                r'token\s*=\s*[\'"][^\'"]+[\'"]',
            ],
            'weak_crypto': [
                r'hashlib\.md5\s*\(',
                r'hashlib\.sha1\s*\(',
                r'base64\.b64encode\s*\(',
            ],
            'insecure_deserialization': [
                r'pickle\.loads\s*\(',
                r'yaml\.load\s*\(',
                r'json\.loads\s*\(\s*request\.data',
            ]
        }
    
    def audit_project(self) -> List[SecurityVulnerability]:
        """Perform comprehensive security audit"""
        print("🔒 Starting Security Audit")
        print("=" * 50)
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
            
            try:
                self._audit_file(file_path)
            except Exception as e:
                print(f"❌ Error auditing {file_path}: {e}")
        
        return self.vulnerabilities
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during audit"""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'node_modules',
            'tests',
            'test_',
            '_test.py'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _audit_file(self, file_path: Path):
        """Audit a single file for security vulnerabilities"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for dangerous patterns
            for vuln_type, patterns in self.dangerous_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        self._add_vulnerability(
                            str(file_path), line_number, vuln_type,
                            f"Potential {vuln_type.replace('_', ' ')} vulnerability",
                            "HIGH" if vuln_type in ['sql_injection', 'command_injection'] else "MEDIUM",
                            self._get_fix_suggestion(vuln_type)
                        )
            
            # Check for additional security issues
            self._check_input_validation(file_path, content)
            self._check_authentication(file_path, content)
            self._check_error_handling(file_path, content)
            
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    def _check_input_validation(self, file_path: Path, content: str):
        """Check for proper input validation"""
        # Look for direct use of request data without validation
        patterns = [
            r'request\.form\[[\'"][^\'"]+[\'"]\]',
            r'request\.args\[[\'"][^\'"]+[\'"]\]',
            r'request\.json\[[\'"][^\'"]+[\'"]\]',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                self._add_vulnerability(
                    str(file_path), line_number, "input_validation",
                    "Direct use of request data without validation",
                    "MEDIUM",
                    "Add input validation and sanitization"
                )
    
    def _check_authentication(self, file_path: Path, content: str):
        """Check for authentication issues"""
        # Look for endpoints without authentication
        if 'app.post(' in content or 'app.get(' in content:
            if not re.search(r'@.*auth|@.*login|@.*secure', content):
                self._add_vulnerability(
                    str(file_path), 0, "authentication",
                    "Endpoint without authentication decorator",
                    "HIGH",
                    "Add authentication decorator to secure endpoints"
                )
    
    def _check_error_handling(self, file_path: Path, content: str):
        """Check for insecure error handling"""
        # Look for bare except clauses
        if re.search(r'except\s*:', content):
            self._add_vulnerability(
                str(file_path), 0, "error_handling",
                "Bare except clause may expose sensitive information",
                "MEDIUM",
                "Use specific exception types and avoid exposing internal details"
            )
    
    def _add_vulnerability(self, file_path: str, line_number: int, 
                          vuln_type: str, description: str, 
                          severity: str, fix_suggestion: str):
        """Add a security vulnerability to the list"""
        vuln = SecurityVulnerability(
            file_path=file_path,
            line_number=line_number,
            vulnerability_type=vuln_type,
            description=description,
            severity=severity,
            fix_suggestion=fix_suggestion
        )
        self.vulnerabilities.append(vuln)
    
    def _get_fix_suggestion(self, vuln_type: str) -> str:
        """Get fix suggestion for vulnerability type"""
        suggestions = {
            'sql_injection': 'Use parameterized queries or ORM',
            'xss': 'Use proper output encoding and CSP headers',
            'command_injection': 'Use subprocess with shell=False and validate input',
            'path_traversal': 'Use Path.resolve() and validate file paths',
            'hardcoded_credentials': 'Use environment variables or secure configuration',
            'weak_crypto': 'Use strong cryptographic algorithms (SHA-256, bcrypt)',
            'insecure_deserialization': 'Use safe deserialization methods',
            'input_validation': 'Add comprehensive input validation and sanitization'
        }
        return suggestions.get(vuln_type, 'Review and fix according to security best practices')
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate security audit report"""
        report = []
        report.append("🔒 SECURITY AUDIT REPORT")
        report.append("=" * 50)
        report.append(f"Total Vulnerabilities Found: {len(self.vulnerabilities)}")
        report.append("")
        
        # Group by severity
        high_vulns = [v for v in self.vulnerabilities if v.severity == "HIGH"]
        medium_vulns = [v for v in self.vulnerabilities if v.severity == "MEDIUM"]
        low_vulns = [v for v in self.vulnerabilities if v.severity == "LOW"]
        
        report.append(f"🔴 HIGH Severity: {len(high_vulns)}")
        report.append(f"🟡 MEDIUM Severity: {len(medium_vulns)}")
        report.append(f"🟢 LOW Severity: {len(low_vulns)}")
        report.append("")
        
        # List vulnerabilities by severity
        for severity, vulns in [("HIGH", high_vulns), ("MEDIUM", medium_vulns), ("LOW", low_vulns)]:
            if vulns:
                report.append(f"📋 {severity} SEVERITY VULNERABILITIES")
                report.append("-" * 40)
                for vuln in vulns:
                    report.append(f"File: {vuln.file_path}:{vuln.line_number}")
                    report.append(f"Type: {vuln.vulnerability_type}")
                    report.append(f"Description: {vuln.description}")
                    report.append(f"Fix: {vuln.fix_suggestion}")
                    report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"📄 Report saved to {output_file}")
        
        return report_text


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/security_audit.py [--fix] [--report output_file]")
        sys.exit(1)
    
    project_root = "."
    fix_mode = "--fix" in sys.argv
    report_mode = "--report" in sys.argv
    
    auditor = SecurityAuditor(project_root)
    vulnerabilities = auditor.audit_project()
    
    if report_mode:
        output_file = sys.argv[sys.argv.index("--report") + 1] if len(sys.argv) > sys.argv.index("--report") + 1 else "security_audit_report.txt"
        report = auditor.generate_report(output_file)
        print(report)
    else:
        report = auditor.generate_report()
        print(report)
    
    if fix_mode:
        print("\n🔧 Applying security fixes...")
        # TODO: Implement automatic fixes
        print("Automatic fixes not yet implemented. Please review and fix manually.")
    
    if vulnerabilities:
        print(f"\n❌ Found {len(vulnerabilities)} security vulnerabilities!")
        sys.exit(1)
    else:
        print("\n✅ No security vulnerabilities found!")
        sys.exit(0)


if __name__ == "__main__":
    main() 