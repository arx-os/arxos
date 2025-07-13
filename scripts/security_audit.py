#!/usr/bin/env python3
"""
Security Audit Script for Python Dependencies

This script runs comprehensive security audits on all Python dependencies
in the Arxos project using multiple tools.

Usage:
    python scripts/security_audit.py [--format json|text] [--output file]
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Security auditor for Python dependencies."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.results = {}
        
    def run_comprehensive_audit(self) -> Dict:
        """Run comprehensive security audit using multiple tools."""
        logger.info("🔒 Starting comprehensive security audit...")
        
        # Find all dependency files
        dependency_files = self._find_dependency_files()
        
        if not dependency_files:
            logger.warning("No dependency files found")
            return {}
        
        # Run audits with different tools
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'files_audited': len(dependency_files),
            'pip_audit': {},
            'safety': {},
            'bandit': {},
            'summary': {
                'total_vulnerabilities': 0,
                'critical_vulnerabilities': 0,
                'high_vulnerabilities': 0,
                'medium_vulnerabilities': 0,
                'low_vulnerabilities': 0
            }
        }
        
        for dep_file in dependency_files:
            logger.info(f"Auditing {dep_file}")
            
            # Run pip-audit
            pip_audit_results = self._run_pip_audit(dep_file)
            audit_results['pip_audit'][str(dep_file)] = pip_audit_results
            
            # Run safety
            safety_results = self._run_safety(dep_file)
            audit_results['safety'][str(dep_file)] = safety_results
            
            # Run bandit (for Python files)
            bandit_results = self._run_bandit(dep_file.parent)
            audit_results['bandit'][str(dep_file.parent)] = bandit_results
        
        # Calculate summary statistics
        audit_results['summary'] = self._calculate_summary(audit_results)
        
        self.results = audit_results
        return audit_results
    
    def _find_dependency_files(self) -> List[Path]:
        """Find all dependency files in the project."""
        dependency_files = []
        
        patterns = [
            "**/requirements.txt",
            "**/pyproject.toml",
            "**/Pipfile"
        ]
        
        for pattern in patterns:
            for file_path in self.root_dir.glob(pattern):
                if self._is_valid_file(file_path):
                    dependency_files.append(file_path)
        
        return dependency_files
    
    def _is_valid_file(self, file_path: Path) -> bool:
        """Check if file should be audited."""
        skip_patterns = [
            "venv", ".venv", "env", ".env",
            "node_modules", "__pycache__", ".git",
            "build", "dist", ".tox", ".pytest_cache"
        ]
        
        return not any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _run_pip_audit(self, file_path: Path) -> Dict:
        """Run pip-audit on a dependency file."""
        results = {
            'success': False,
            'vulnerabilities': [],
            'error': None
        }
        
        try:
            cmd = [
                sys.executable, "-m", "pip-audit",
                "--format", "json",
                "--requirement", str(file_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            if result.returncode == 0:
                try:
                    audit_data = json.loads(result.stdout)
                    results['vulnerabilities'] = audit_data.get('vulnerabilities', [])
                    results['success'] = True
                except json.JSONDecodeError:
                    results['error'] = "Failed to parse pip-audit output"
            else:
                results['error'] = result.stderr
                
        except subprocess.TimeoutExpired:
            results['error'] = "Audit timed out"
        except FileNotFoundError:
            results['error'] = "pip-audit not available"
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _run_safety(self, file_path: Path) -> Dict:
        """Run safety check on a dependency file."""
        results = {
            'success': False,
            'vulnerabilities': [],
            'error': None
        }
        
        try:
            cmd = [
                sys.executable, "-m", "safety",
                "check",
                "--json",
                "--file", str(file_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            if result.returncode == 0:
                try:
                    safety_data = json.loads(result.stdout)
                    results['vulnerabilities'] = safety_data
                    results['success'] = True
                except json.JSONDecodeError:
                    results['error'] = "Failed to parse safety output"
            else:
                results['error'] = result.stderr
                
        except subprocess.TimeoutExpired:
            results['error'] = "Audit timed out"
        except FileNotFoundError:
            results['error'] = "safety not available"
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _run_bandit(self, directory: Path) -> Dict:
        """Run bandit on Python files in a directory."""
        results = {
            'success': False,
            'issues': [],
            'error': None
        }
        
        try:
            cmd = [
                sys.executable, "-m", "bandit",
                "-r", str(directory),
                "-f", "json",
                "--exclude", "tests,venv,.venv,__pycache__"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            if result.returncode == 0:
                try:
                    bandit_data = json.loads(result.stdout)
                    results['issues'] = bandit_data.get('results', [])
                    results['success'] = True
                except json.JSONDecodeError:
                    results['error'] = "Failed to parse bandit output"
            else:
                results['error'] = result.stderr
                
        except subprocess.TimeoutExpired:
            results['error'] = "Audit timed out"
        except FileNotFoundError:
            results['error'] = "bandit not available"
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _calculate_summary(self, audit_results: Dict) -> Dict:
        """Calculate summary statistics from audit results."""
        summary = {
            'total_vulnerabilities': 0,
            'critical_vulnerabilities': 0,
            'high_vulnerabilities': 0,
            'medium_vulnerabilities': 0,
            'low_vulnerabilities': 0,
            'files_with_vulnerabilities': 0
        }
        
        # Count pip-audit vulnerabilities
        for file_results in audit_results['pip_audit'].values():
            if file_results['success']:
                vulns = file_results['vulnerabilities']
                if vulns:
                    summary['files_with_vulnerabilities'] += 1
                    summary['total_vulnerabilities'] += len(vulns)
                    
                    for vuln in vulns:
                        severity = vuln.get('vulnerability', {}).get('severity', 'unknown').lower()
                        if severity == 'critical':
                            summary['critical_vulnerabilities'] += 1
                        elif severity == 'high':
                            summary['high_vulnerabilities'] += 1
                        elif severity == 'medium':
                            summary['medium_vulnerabilities'] += 1
                        elif severity == 'low':
                            summary['low_vulnerabilities'] += 1
        
        # Count safety vulnerabilities
        for file_results in audit_results['safety'].values():
            if file_results['success']:
                vulns = file_results['vulnerabilities']
                if vulns:
                    summary['total_vulnerabilities'] += len(vulns)
                    
                    for vuln in vulns:
                        severity = vuln.get('severity', 'unknown').lower()
                        if severity == 'critical':
                            summary['critical_vulnerabilities'] += 1
                        elif severity == 'high':
                            summary['high_vulnerabilities'] += 1
                        elif severity == 'medium':
                            summary['medium_vulnerabilities'] += 1
                        elif severity == 'low':
                            summary['low_vulnerabilities'] += 1
        
        return summary
    
    def print_report(self, format_type: str = "text") -> None:
        """Print audit report in specified format."""
        if not self.results:
            logger.error("No audit results available. Run audit first.")
            return
        
        if format_type == "json":
            print(json.dumps(self.results, indent=2))
        else:
            self._print_text_report()
    
    def _print_text_report(self) -> None:
        """Print audit report in human-readable text format."""
        print("=" * 80)
        print("SECURITY AUDIT REPORT")
        print("=" * 80)
        print(f"Generated: {self.results['timestamp']}")
        print(f"Files audited: {self.results['files_audited']}")
        print()
        
        # Print summary
        summary = self.results['summary']
        print("SUMMARY:")
        print(f"  Total vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"  Critical: {summary['critical_vulnerabilities']}")
        print(f"  High: {summary['high_vulnerabilities']}")
        print(f"  Medium: {summary['medium_vulnerabilities']}")
        print(f"  Low: {summary['low_vulnerabilities']}")
        print(f"  Files with vulnerabilities: {summary['files_with_vulnerabilities']}")
        print()
        
        # Print detailed results
        print("DETAILED RESULTS:")
        print("-" * 80)
        
        # pip-audit results
        print("PIP-AUDIT RESULTS:")
        for file_path, results in self.results['pip_audit'].items():
            print(f"\n{file_path}:")
            if results['success']:
                if results['vulnerabilities']:
                    for vuln in results['vulnerabilities']:
                        pkg = vuln.get('package', {}).get('name', 'unknown')
                        version = vuln.get('package', {}).get('installed_version', 'unknown')
                        vuln_id = vuln.get('vulnerability', {}).get('id', 'unknown')
                        severity = vuln.get('vulnerability', {}).get('severity', 'unknown')
                        print(f"  ❌ {pkg}=={version} - {vuln_id} ({severity})")
                else:
                    print("  ✅ No vulnerabilities found")
            else:
                print(f"  ⚠️  Error: {results['error']}")
        
        # safety results
        print("\nSAFETY RESULTS:")
        for file_path, results in self.results['safety'].items():
            print(f"\n{file_path}:")
            if results['success']:
                if results['vulnerabilities']:
                    for vuln in results['vulnerabilities']:
                        pkg = vuln.get('package', 'unknown')
                        version = vuln.get('installed_version', 'unknown')
                        vuln_id = vuln.get('vulnerability_id', 'unknown')
                        severity = vuln.get('severity', 'unknown')
                        print(f"  ❌ {pkg}=={version} - {vuln_id} ({severity})")
                else:
                    print("  ✅ No vulnerabilities found")
            else:
                print(f"  ⚠️  Error: {results['error']}")
        
        # bandit results
        print("\nBANDIT RESULTS:")
        for directory, results in self.results['bandit'].items():
            print(f"\n{directory}:")
            if results['success']:
                if results['issues']:
                    for issue in results['issues']:
                        severity = issue.get('issue_severity', 'unknown')
                        confidence = issue.get('issue_confidence', 'unknown')
                        issue_id = issue.get('issue_text', 'unknown')
                        file_path = issue.get('filename', 'unknown')
                        line_num = issue.get('line_number', 'unknown')
                        print(f"  ⚠️  {file_path}:{line_num} - {issue_id} ({severity}/{confidence})")
                else:
                    print("  ✅ No security issues found")
            else:
                print(f"  ⚠️  Error: {results['error']}")
        
        print("\n" + "=" * 80)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Security audit for Python dependencies")
    parser.add_argument("--format", choices=["json", "text"], default="text", 
                       help="Output format")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--root", type=str, default=".", help="Root directory to scan")
    
    args = parser.parse_args()
    
    root_dir = Path(args.root)
    auditor = SecurityAuditor(root_dir)
    
    # Run audit
    results = auditor.run_comprehensive_audit()
    
    # Print or save report
    if args.output:
        with open(args.output, 'w') as f:
            if args.format == "json":
                json.dump(results, f, indent=2)
            else:
                # For text format, we need to capture the output
                import io
                from contextlib import redirect_stdout
                
                output = io.StringIO()
                with redirect_stdout(output):
                    auditor.print_report("text")
                
                f.write(output.getvalue())
        
        logger.info(f"Report saved to {args.output}")
    else:
        auditor.print_report(args.format)
    
    # Exit with error code if vulnerabilities found
    summary = results.get('summary', {})
    if summary.get('critical_vulnerabilities', 0) > 0 or summary.get('high_vulnerabilities', 0) > 0:
        logger.error("Critical or high severity vulnerabilities found!")
        sys.exit(1)
    elif summary.get('total_vulnerabilities', 0) > 0:
        logger.warning("Vulnerabilities found, but none are critical or high severity")
        sys.exit(0)
    else:
        logger.info("No vulnerabilities found!")
        sys.exit(0)

if __name__ == "__main__":
    main() 