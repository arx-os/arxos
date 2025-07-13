#!/usr/bin/env python3
"""
CI Script to Check for Duplicate Utility Functions

This script scans the codebase for common utility function patterns
that should be moved to arx_common instead of being duplicated.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Common patterns that should use arx_common utilities
DUPLICATE_PATTERNS = {
    # Date/time patterns
    r'datetime\.utcnow\(\)\.isoformat\(\)': {
        'message': 'Use arx_common.date_utils.get_current_timestamp_iso() instead',
        'severity': 'warning'
    },
    r'datetime\.utcnow\(\)': {
        'message': 'Use arx_common.date_utils.get_current_timestamp() instead',
        'severity': 'warning'
    },
    r'datetime\.now\(\)\.isoformat\(\)': {
        'message': 'Use arx_common.date_utils.get_current_timestamp_iso() instead',
        'severity': 'warning'
    },
    
    # Object manipulation patterns
    r'def flatten': {
        'message': 'Use arx_common.object_utils.flatten_dict() instead',
        'severity': 'error'
    },
    r'def deep_merge': {
        'message': 'Use arx_common.object_utils.deep_merge() instead',
        'severity': 'error'
    },
    r'def remove_none': {
        'message': 'Use arx_common.object_utils.remove_none_values() instead',
        'severity': 'error'
    },
    
    # Request handling patterns
    r'def get_client_ip': {
        'message': 'Use arx_common.request_utils.get_client_ip() instead',
        'severity': 'error'
    },
    r'def get_user_agent': {
        'message': 'Use arx_common.request_utils.get_user_agent() instead',
        'severity': 'error'
    },
    r'def validate_required_params': {
        'message': 'Use arx_common.request_utils.validate_required_params() instead',
        'severity': 'error'
    },
    
    # Common utility patterns
    r'def create_object_id': {
        'message': 'Use arx_common.object_utils.create_object_id() instead',
        'severity': 'error'
    },
    r'def parse_timestamp': {
        'message': 'Use arx_common.date_utils.parse_timestamp() instead',
        'severity': 'error'
    },
    r'def format_timestamp': {
        'message': 'Use arx_common.date_utils.format_timestamp() instead',
        'severity': 'error'
    }
}

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    'arx_common',
    'tests/arx_common',
    '__pycache__',
    '.git',
    'node_modules',
    'venv',
    'env',
    '.venv'
}

# File extensions to scan
INCLUDE_EXTENSIONS = {'.py'}

def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    # Skip excluded directories
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Skip non-Python files
    if file_path.suffix not in INCLUDE_EXTENSIONS:
        return True
    
    return False

def scan_file(file_path: Path) -> List[Dict]:
    """Scan a single file for duplicate patterns."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        for line_num, line in enumerate(lines, 1):
            for pattern, config in DUPLICATE_PATTERNS.items():
                if re.search(pattern, line):
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'line_content': line.strip(),
                        'pattern': pattern,
                        'message': config['message'],
                        'severity': config['severity']
                    })
    
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return issues

def scan_directory(root_path: Path) -> List[Dict]:
    """Scan directory recursively for duplicate patterns."""
    all_issues = []
    
    for file_path in root_path.rglob('*'):
        if file_path.is_file() and not should_skip_file(file_path):
            issues = scan_file(file_path)
            all_issues.extend(issues)
    
    return all_issues

def print_issues(issues: List[Dict]) -> None:
    """Print issues in a formatted way."""
    if not issues:
        print("✅ No duplicate utility patterns found!")
        return
    
    # Group by severity
    errors = [i for i in issues if i['severity'] == 'error']
    warnings = [i for i in issues if i['severity'] == 'warning']
    
    if errors:
        print(f"\n❌ Found {len(errors)} ERROR(s):")
        for issue in errors:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['line_content']}")
            print(f"    → {issue['message']}")
            print()
    
    if warnings:
        print(f"\n⚠️  Found {len(warnings)} WARNING(s):")
        for issue in warnings:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['line_content']}")
            print(f"    → {issue['message']}")
            print()

def main():
    """Main function."""
    if len(sys.argv) > 1:
        root_path = Path(sys.argv[1])
    else:
        root_path = Path.cwd()
    
    if not root_path.exists():
        print(f"Error: Path {root_path} does not exist")
        sys.exit(1)
    
    print(f"🔍 Scanning {root_path} for duplicate utility patterns...")
    
    issues = scan_directory(root_path)
    
    print_issues(issues)
    
    # Exit with error code if there are errors
    error_count = len([i for i in issues if i['severity'] == 'error'])
    if error_count > 0:
        print(f"❌ Found {error_count} error(s) that need to be fixed!")
        sys.exit(1)
    
    print("✅ All checks passed!")

if __name__ == "__main__":
    main() 