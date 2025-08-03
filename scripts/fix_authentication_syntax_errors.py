#!/usr/bin/env python3
"""
Fix Authentication Syntax Errors

This script fixes the syntax errors introduced during the authentication
application process, specifically removing duplicate function definitions
and fixing indentation issues.

Target Files:
- services/ai/main.py
- services/gus/main.py
- svgx_engine/app.py
- services/planarx/planarx-community/main.py

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


class AuthenticationSyntaxFixer:
    """Fixes syntax errors introduced during authentication application"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.files_with_syntax_errors = [
            "services/ai/main.py",
            "services/gus/main.py",
            "svgx_engine/app.py",
            "services/planarx/planarx-community/main.py"
        ]
    
    def fix_syntax_errors(self):
        """Fix syntax errors in all affected files"""
        print("🔧 Fixing Authentication Syntax Errors")
        print("=" * 50)
        
        success_count = 0
        error_count = 0
        
        for file_path in self.files_with_syntax_errors:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue
            
            try:
                if self._fix_file(full_path):
                    print(f"✅ Fixed syntax errors in: {file_path}")
                    success_count += 1
                else:
                    print(f"ℹ️  No syntax errors found in: {file_path}")
                    
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                error_count += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Summary:")
        print(f"   ✅ Successfully fixed: {success_count} files")
        print(f"   ❌ Errors: {error_count} files")
        print(f"   📁 Total processed: {len(self.files_with_syntax_errors)} files")
    
    def _fix_file(self, file_path: Path) -> bool:
        """Fix syntax errors in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix duplicate function definitions
            content = self._fix_duplicate_functions(content)
            
            # Fix indentation issues
            content = self._fix_indentation(content)
            
            # Fix import issues
            content = self._fix_imports(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False
    
    def _fix_duplicate_functions(self, content: str) -> str:
        """Fix duplicate function definitions"""
        # Pattern to match duplicate function definitions
        # This matches patterns like:
        # async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
        # async def health_check(user: User = Depends(get_current_user)):
        
        # Remove the first duplicate line
        content = re.sub(
            r'async def endpoint_name\(request: Request, user: User = Depends\(get_current_user\)\):\n',
            '',
            content
        )
        
        # Fix the remaining function definitions
        content = re.sub(
            r'async def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*\n\s*async def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):',
            r'async def \2',
            content
        )
        
        return content
    
    def _fix_indentation(self, content: str) -> str:
        """Fix indentation issues"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix common indentation issues
            if line.strip().startswith('async def ') and ':' in line:
                # Ensure proper indentation for function definitions
                if not line.startswith('    ') and not line.startswith('\t'):
                    line = '    ' + line.lstrip()
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_imports(self, content: str) -> str:
        """Fix import issues"""
        # Ensure proper imports for authentication
        if "from core.security.auth_middleware" not in content:
            # Add authentication import
            import_pattern = r'^import\s+.*$|^from\s+.*\s+import\s+.*$'
            imports = re.findall(import_pattern, content, re.MULTILINE)
            
            if imports:
                last_import = imports[-1]
                auth_import = "from core.security.auth_middleware import get_current_user, User"
                content = content.replace(last_import, f"{last_import}\n{auth_import}")
            else:
                auth_import = "from core.security.auth_middleware import get_current_user, User"
                content = f"{auth_import}\n\n{content}"
        
        return content
    
    def create_syntax_fix_example(self):
        """Create an example of proper endpoint definition"""
        example = '''
# Example of Proper Endpoint Definition with Authentication

from fastapi import FastAPI, Depends, HTTPException
from core.security.auth_middleware import get_current_user, User
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    user_id: str

@app.get("/health")
async def health_check(user: User = Depends(get_current_user)):
    """Health check endpoint with authentication"""
    return {
        "status": "healthy",
        "user_id": user.id,
        "service": "example"
    }

@app.post("/api/v1/query")
async def process_query(request: QueryRequest, user: User = Depends(get_current_user)):
    """Process query endpoint with authentication"""
    try:
        # Process the query
        return {
            "success": True,
            "query": request.query,
            "user_id": user.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
        
        example_path = self.project_root / "docs" / "proper_endpoint_example.py"
        example_path.parent.mkdir(exist_ok=True)
        
        with open(example_path, 'w') as f:
            f.write(example)
        
        print(f"📝 Created proper endpoint example: {example_path}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fix_authentication_syntax_errors.py [--dry-run] [--example]")
        sys.exit(1)
    
    project_root = "."
    dry_run = "--dry-run" in sys.argv
    create_example = "--example" in sys.argv
    
    fixer = AuthenticationSyntaxFixer(project_root)
    
    if create_example:
        fixer.create_syntax_fix_example()
    
    if not dry_run:
        fixer.fix_syntax_errors()
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Files that would be fixed:")
        for file_path in fixer.files_with_syntax_errors:
            full_path = Path(project_root) / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (not found)")


if __name__ == "__main__":
    main() 