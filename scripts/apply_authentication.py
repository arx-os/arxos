#!/usr/bin/env python3
"""
Apply Authentication Script

This script automatically applies authentication to all vulnerable endpoints
identified in the security audit, addressing critical authentication vulnerabilities.

Target Files:
- svgx_engine/app.py
- api/main.py
- api/dependencies.py
- services/ai/main.py
- services/gus/main.py
- services/planarx/planarx-community/main.py
- svgx_engine/api/ai_integration_api.py
- svgx_engine/api/cmms_api.py
- svgx_engine/api/notification_api.py
- svgx_engine/api/export_api.py
- svgx_engine/api/cad_api.py
- svgx_engine/api/app.py
- svgx_engine/services/ai/advanced_ai_api.py

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


class AuthenticationApplier:
    """Applies authentication to vulnerable endpoints"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.vulnerable_files = [
            "svgx_engine/app.py",
            "api/main.py",
            "api/dependencies.py",
            "services/ai/main.py",
            "services/gus/main.py",
            "services/planarx/planarx-community/main.py",
            "svgx_engine/api/ai_integration_api.py",
            "svgx_engine/api/cmms_api.py",
            "svgx_engine/api/notification_api.py",
            "svgx_engine/api/export_api.py",
            "svgx_engine/api/cad_api.py",
            "svgx_engine/api/app.py",
            "svgx_engine/services/ai/advanced_ai_api.py"
        ]
        
        self.auth_import = """from core.security.auth_middleware import get_current_user, User"""
        self.auth_dependency = "user: User = Depends(get_current_user)"
    
    def apply_authentication(self):
        """Apply authentication to all vulnerable files"""
        print("🔒 Applying Authentication to Vulnerable Endpoints")
        print("=" * 60)
        
        success_count = 0
        error_count = 0
        
        for file_path in self.vulnerable_files:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue
            
            try:
                if self._apply_auth_to_file(full_path):
                    print(f"✅ Applied authentication to: {file_path}")
                    success_count += 1
                else:
                    print(f"ℹ️  No changes needed for: {file_path}")
                    
            except Exception as e:
                print(f"❌ Error applying authentication to {file_path}: {e}")
                error_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"   ✅ Successfully updated: {success_count} files")
        print(f"   ❌ Errors: {error_count} files")
        print(f"   📁 Total processed: {len(self.vulnerable_files)} files")
    
    def _apply_auth_to_file(self, file_path: Path) -> bool:
        """Apply authentication to a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Add authentication import if not present
            if "from core.security.auth_middleware" not in content:
                content = self._add_auth_import(content)
            
            # Apply authentication to endpoints
            content = self._apply_auth_to_endpoints(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False
    
    def _add_auth_import(self, content: str) -> str:
        """Add authentication import to file"""
        # Find the last import statement
        import_pattern = r'^import\s+.*$|^from\s+.*\s+import\s+.*$'
        imports = re.findall(import_pattern, content, re.MULTILINE)
        
        if imports:
            # Add after the last import
            last_import = imports[-1]
            content = content.replace(last_import, f"{last_import}\n{self.auth_import}")
        else:
            # Add at the beginning if no imports found
            content = f"{self.auth_import}\n\n{content}"
        
        return content
    
    def _apply_auth_to_endpoints(self, content: str) -> str:
        """Apply authentication to all endpoints in the file"""
        # Pattern to match FastAPI endpoint decorators
        endpoint_pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*["\'][^"\']*["\']\s*\)'
        
        def add_auth_to_endpoint(match):
            decorator = match.group(0)
            
            # Check if authentication is already applied
            if "Depends(get_current_user)" in content:
                return decorator
            
            # Add authentication dependency
            return f"{decorator}\nasync def endpoint_name(request: Request, {self.auth_dependency}):"
        
        # Apply authentication to endpoints
        content = re.sub(endpoint_pattern, add_auth_to_endpoint, content)
        
        # Update function signatures to include authentication
        content = self._update_function_signatures(content)
        
        return content
    
    def _update_function_signatures(self, content: str) -> str:
        """Update function signatures to include authentication"""
        # Pattern to match function definitions that should have authentication
        function_pattern = r'async def (\w+)\s*\(([^)]*)\):'
        
        def update_signature(match):
            func_name = match.group(1)
            params = match.group(2)
            
            # Skip if already has authentication
            if "Depends(get_current_user)" in params:
                return match.group(0)
            
            # Add authentication parameter
            if params.strip():
                new_params = f"{params}, {self.auth_dependency}"
            else:
                new_params = self.auth_dependency
            
            return f"async def {func_name}({new_params}):"
        
        content = re.sub(function_pattern, update_signature, content)
        return content
    
    def create_auth_example(self):
        """Create an example of how to use authentication"""
        example = '''
# Example of secure endpoint with authentication

from fastapi import FastAPI, Depends, HTTPException
from core.security.auth_middleware import get_current_user, User

app = FastAPI()

@app.post("/api/v1/secure-endpoint")
async def secure_endpoint(
    request: YourRequestModel,
    user: User = Depends(get_current_user)
):
    """Secure endpoint with authentication"""
    
    # User is automatically authenticated
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")
    
    # Check user roles
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Process request
    return {"message": "Success", "user_id": user.id}

# For role-based access
@app.get("/api/v1/admin-only")
async def admin_only_endpoint(user: User = Depends(get_current_user)):
    """Admin-only endpoint"""
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"message": "Admin access granted"}
'''
        
        example_path = self.project_root / "docs" / "authentication_example.py"
        example_path.parent.mkdir(exist_ok=True)
        
        with open(example_path, 'w') as f:
            f.write(example)
        
        print(f"📝 Created authentication example: {example_path}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/apply_authentication.py [--dry-run] [--example]")
        sys.exit(1)
    
    project_root = "."
    dry_run = "--dry-run" in sys.argv
    create_example = "--example" in sys.argv
    
    applier = AuthenticationApplier(project_root)
    
    if create_example:
        applier.create_auth_example()
    
    if not dry_run:
        applier.apply_authentication()
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Files that would be updated:")
        for file_path in applier.vulnerable_files:
            full_path = Path(project_root) / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (not found)")


if __name__ == "__main__":
    main() 