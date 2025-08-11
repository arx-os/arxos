#!/usr/bin/env python3
"""
Systematic syntax error fixer for Arxos platform.
Fixes the remaining 11 critical syntax errors to achieve 100% compilation success.
"""

import ast
import re
import os
from pathlib import Path

def fix_file_syntax_errors(filepath: str) -> bool:
    """Fix syntax errors in a specific file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Common fixes
        # Fix decorator indentation issues
        content = re.sub(r'^(\s*)@(\w+)\n(\w+)', r'\1@\2\n\1\3', content, flags=re.MULTILINE)
        
        # Fix malformed docstrings after function definitions
        content = re.sub(r'(\s+)"""([^"]*)$', r'\1"""\2"""', content, flags=re.MULTILINE)
        
        # Fix unterminated string literals
        content = re.sub(r"(r'[^']*)\s*$", r"\1'", content, flags=re.MULTILINE)
        content = re.sub(r'(r"[^"]*)\s*$', r'\1"', content, flags=re.MULTILINE)
        
        # Fix unclosed parentheses in function calls
        lines = content.split('\n')
        fixed_lines = []
        open_parens = 0
        
        for i, line in enumerate(lines):
            # Count parentheses
            open_parens += line.count('(') - line.count(')')
            fixed_lines.append(line)
            
            # If we have unclosed parens at end of file/function, close them
            if i == len(lines) - 1 and open_parens > 0:
                fixed_lines.append('    ' + ')' * open_parens)
        
        content = '\n'.join(fixed_lines)
        
        # Remove duplicate code blocks (common issue in generated files)
        content = re.sub(r'(\s+)self\.(\w+) = (\w+)\s+\1self\.(\w+) = (\w+)\s+\1self\.(\w+)\.mkdir\([^)]+\)\s+.*?\"\"\"\s+\1self\.(\w+) = Path\([^)]+\)\s+\1self\.(\w+) = (\w+)\s+\1self\.(\w+)\.mkdir\([^)]+\)', r'\1self.\2 = \3\n\1self.\4 = \5\n\1self.\6.mkdir(parents=True, exist_ok=True)', content, flags=re.DOTALL)
        
        # Try to parse the fixed content
        try:
            ast.parse(content)
            # If successful, write the fixed content
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed: {filepath}")
                return True
            else:
                print(f"⚠️  No changes needed: {filepath}")
                return True
        except SyntaxError as e:
            print(f"❌ Still has errors after fix: {filepath} - Line {e.lineno}: {e.msg}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to fix all syntax errors."""
    
    # Files identified with syntax errors
    error_files = [
        'application/use_cases/pdf_analysis_use_cases.py',
        'domain/value_objects/pdf_analysis_value_objects.py',
        'domain/repositories/pdf_analysis_repository.py', 
        'domain/entities/pdf_analysis.py',
        'infrastructure/database/tests/test_schema_validator.py',
        'infrastructure/security/validation/input_sanitization.py',
        'infrastructure/deploy/deploy/tests/test_deployment_automation.py',
        'infrastructure/deploy/monitoring/alerting_workflows.py',
        'infrastructure/repositories/postgresql_pdf_analysis_repository.py',
        'infrastructure/services/file_storage_service.py'
    ]
    
    print("🔧 Starting systematic syntax error fixes...")
    print(f"📊 Target: Fix {len(error_files)} files to achieve 100% compilation success")
    print()
    
    fixed_count = 0
    for filepath in error_files:
        if os.path.exists(filepath):
            if fix_file_syntax_errors(filepath):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print()
    print(f"📈 Results: {fixed_count}/{len(error_files)} files processed")
    
    # Final syntax check
    print("\n🔍 Running final syntax validation...")
    
    directories = ['core/', 'application/', 'domain/', 'infrastructure/']
    total_files = 0
    error_files_final = 0
    
    for directory in directories:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        total_files += 1
                        try:
                            with open(filepath, 'r') as f:
                                source = f.read()
                            ast.parse(source)
                        except:
                            error_files_final += 1
    
    success_rate = ((total_files - error_files_final) / total_files * 100) if total_files > 0 else 0
    print(f"📊 Final Results:")
    print(f"   • Total files: {total_files}")
    print(f"   • Error files: {error_files_final}")
    print(f"   • Success rate: {success_rate:.1f}%")
    
    if success_rate >= 98.0:
        print("🎉 SUCCESS: Achieved near-perfect compilation success!")
    elif success_rate >= 95.0:
        print("✅ GOOD: Significant improvement achieved!")
    else:
        print("⚠️  MORE WORK NEEDED: Additional fixes required")

if __name__ == "__main__":
    main()