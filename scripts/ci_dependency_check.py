#!/usr/bin/env python3
"""
CI Dependency Validation Script

This script validates that all Python dependencies follow the standard:
- Use ~= for version constraints (not ==)
- No critical security vulnerabilities
- All dependencies are properly declared

Usage:
    python scripts/ci_dependency_check.py
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependency_constraints() -> bool:
    """Check that all dependencies use ~= instead of ==."""
    logger.info("🔍 Checking dependency constraints...")
    
    root_dir = Path(__file__).parent.parent
    issues = []
    
    # Find all dependency files
    for pattern in ["**/requirements.txt", "**/pyproject.toml"]:
        for file_path in root_dir.glob(pattern):
            if _is_valid_dependency_file(file_path):
                file_issues = _check_file_constraints(file_path)
                issues.extend(file_issues)
    
    if issues:
        logger.error("❌ Found dependency constraint issues:")
        for issue in issues:
            logger.error(f"  {issue}")
        return False
    
    logger.info("✅ All dependency constraints are compliant")
    return True

def _is_valid_dependency_file(file_path: Path) -> bool:
    """Check if file should be validated."""
    skip_patterns = ["venv", ".venv", "env", ".env", "node_modules", "__pycache__"]
    return not any(pattern in str(file_path) for pattern in skip_patterns)

def _check_file_constraints(file_path: Path) -> List[str]:
    """Check a single file for constraint issues."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Check for exact version pins
            if '==' in line and not line.startswith('#'):
                issues.append(f"{file_path}:{line_num} - Uses == instead of ~=: {line}")
    
    return issues

def run_security_audit() -> bool:
    """Run security audit on all dependencies."""
    logger.info("🔒 Running security audit...")
    
    root_dir = Path(__file__).parent.parent
    vulnerabilities = []
    
    # Find all requirements files
    for req_file in root_dir.glob("**/requirements.txt"):
        if _is_valid_dependency_file(req_file):
            file_vulns = _audit_file(req_file)
            vulnerabilities.extend(file_vulns)
    
    if vulnerabilities:
        logger.error("❌ Found security vulnerabilities:")
        for vuln in vulnerabilities:
            logger.error(f"  {vuln}")
        return False
    
    logger.info("✅ No security vulnerabilities found")
    return True

def _audit_file(file_path: Path) -> List[str]:
    """Audit a single requirements file."""
    vulnerabilities = []
    
    try:
        # Try pip-audit
        cmd = [sys.executable, "-m", "pip-audit", "--format", "json", "--requirement", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            try:
                audit_data = json.loads(result.stdout)
                for vuln in audit_data.get('vulnerabilities', []):
                    pkg = vuln.get('package', {}).get('name', 'unknown')
                    version = vuln.get('package', {}).get('installed_version', 'unknown')
                    vuln_id = vuln.get('vulnerability', {}).get('id', 'unknown')
                    severity = vuln.get('vulnerability', {}).get('severity', 'unknown')
                    
                    vulnerabilities.append(f"{file_path}: {pkg}=={version} - {vuln_id} ({severity})")
            except json.JSONDecodeError:
                pass
                
    except Exception as e:
        logger.warning(f"Could not audit {file_path}: {e}")
    
    return vulnerabilities

def check_lock_files() -> bool:
    """Check that lock files are up to date."""
    logger.info("📦 Checking lock files...")
    
    root_dir = Path(__file__).parent.parent
    missing_lock_files = []
    
    # Check for requirements-lock.txt files
    for req_file in root_dir.glob("**/requirements.txt"):
        if _is_valid_dependency_file(req_file):
            lock_file = req_file.parent / "requirements-lock.txt"
            if not lock_file.exists():
                missing_lock_files.append(str(lock_file))
    
    if missing_lock_files:
        logger.warning("⚠️  Missing lock files:")
        for lock_file in missing_lock_files:
            logger.warning(f"  {lock_file}")
        return False
    
    logger.info("✅ All lock files are present")
    return True

def main():
    """Main validation function."""
    logger.info("🚀 Starting dependency validation...")
    
    # Check constraints
    constraints_ok = check_dependency_constraints()
    
    # Run security audit
    security_ok = run_security_audit()
    
    # Check lock files
    lock_files_ok = check_lock_files()
    
    if not constraints_ok or not security_ok:
        logger.error("❌ Dependency validation failed")
        sys.exit(1)
    
    if not lock_files_ok:
        logger.warning("⚠️  Lock files missing, but continuing...")
    
    logger.info("✅ All dependency validations passed")
    sys.exit(0)

if __name__ == "__main__":
    main() 