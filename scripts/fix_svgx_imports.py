#!/usr/bin/env python3
"""
SVGX Engine Import Fixer

This script specifically fixes import issues in the SVGX Engine by converting
relative imports to absolute imports. It's designed to work with the specific
structure of the SVGX Engine codebase.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class SVGXImportFixer:
    """Specialized import fixer for SVGX Engine."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
        # SVGX Engine specific import mappings
        self.import_mappings = {
            # Runtime imports
            r'from \.evaluator import': 'from svgx_engine.runtime.evaluator import',
            r'from \.behavior_engine import': 'from svgx_engine.runtime.behavior_engine import',
            r'from \.advanced_behavior_engine import': 'from svgx_engine.runtime.advanced_behavior_engine import',
            r'from \.physics_engine import': 'from svgx_engine.runtime.physics_engine import',
            
            # Services imports
            r'from \.database import': 'from svgx_engine.services.database import',
            r'from \.metadata_service import': 'from svgx_engine.services.metadata_service import',
            r'from \.symbol_manager import': 'from svgx_engine.services.symbol_manager import',
            r'from \.symbol_recognition import': 'from svgx_engine.services.symbol_recognition import',
            r'from \.symbol_schema_validator import': 'from svgx_engine.services.symbol_schema_validator import',
            r'from \.symbol_renderer import': 'from svgx_engine.services.symbol_renderer import',
            r'from \.symbol_generator import': 'from svgx_engine.services.symbol_generator import',
            r'from \.advanced_export import': 'from svgx_engine.services.advanced_export import',
            r'from \.export_interoperability import': 'from svgx_engine.services.export_interoperability import',
            r'from \.persistence_export import': 'from svgx_engine.services.persistence_export import',
            r'from \.export_integration import': 'from svgx_engine.services.export_integration import',
            r'from \.bim_builder import': 'from svgx_engine.services.bim_builder import',
            r'from \.bim_export import': 'from svgx_engine.services.bim_export import',
            r'from \.bim_validator import': 'from svgx_engine.services.bim_validator import',
            r'from \.bim_assembly import': 'from svgx_engine.services.bim_assembly import',
            r'from \.bim_health import': 'from svgx_engine.services.bim_health import',
            r'from \.bim_extractor import': 'from svgx_engine.services.bim_extractor import',
            r'from \.advanced_caching import': 'from svgx_engine.services.advanced_caching import',
            r'from \.performance import': 'from svgx_engine.services.performance import',
            r'from \.performance_optimizer import': 'from svgx_engine.services.performance_optimizer import',
            r'from \.access_control import': 'from svgx_engine.services.access_control import',
            r'from \.advanced_security import': 'from svgx_engine.services.advanced_security import',
            r'from \.security import': 'from svgx_engine.services.security import',
            r'from \.security_hardener import': 'from svgx_engine.services.security_hardener import',
            r'from \.telemetry import': 'from svgx_engine.services.telemetry import',
            r'from \.realtime import': 'from svgx_engine.services.realtime import',
            r'from \.enhanced_simulation_engine import': 'from svgx_engine.services.enhanced_simulation_engine import',
            r'from \.interactive_capabilities import': 'from svgx_engine.services.interactive_capabilities import',
            r'from \.advanced_cad_features import': 'from svgx_engine.services.advanced_cad_features import',
            r'from \.realtime_collaboration import': 'from svgx_engine.services.realtime_collaboration import',
            r'from \.error_handler import': 'from svgx_engine.services.error_handler import',
            
            # Cache imports
            r'from \.redis_client import': 'from svgx_engine.services.cache.redis_client import',
            
            # Logging imports
            r'from \.structured_logger import': 'from svgx_engine.services.logging.structured_logger import',
            
            # Models imports
            r'from \.models\.': 'from svgx_engine.models.',
            r'from \.database\.models import': 'from svgx_engine.database.models import',
            
            # Utils imports
            r'from \.utils\.': 'from svgx_engine.utils.',
            r'from \.errors import': 'from svgx_engine.utils.errors import',
            r'from \.performance import': 'from svgx_engine.utils.performance import',
            r'from \.telemetry import': 'from svgx_engine.utils.telemetry import',
            
            # Config imports
            r'from \.config\.': 'from svgx_engine.config.',
            r'from \.settings import': 'from svgx_engine.config.settings import',
            
            # Parser imports
            r'from \.parser\.': 'from svgx_engine.parser.',
            r'from \.compiler\.': 'from svgx_engine.compiler.',
            
            # General relative imports (fallback)
            r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*) import': r'from svgx_engine.\1 import',
            r'from \.([a-zA-Z_][a-zA-Z0-9_]*) import': r'from svgx_engine.\1 import',
        }
    
    def fix_file(self, file_path: str, dry_run: bool = True) -> Tuple[bool, List[str]]:
        """Fix imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes = []
            
            # Apply each import mapping
            for pattern, replacement in self.import_mappings.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    original_line = match.group(0)
                    new_line = re.sub(pattern, replacement, original_line)
                    
                    if original_line != new_line:
                        changes.append(f"  {original_line} -> {new_line}")
                        content = content.replace(original_line, new_line)
            
            if changes and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed {len(changes)} imports in {file_path}")
            elif changes:
                print(f"📝 Would fix {len(changes)} imports in {file_path}")
                for change in changes:
                    print(change)
            
            return len(changes) > 0, changes
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False, []
    
    def fix_directory(self, directory: str, dry_run: bool = True) -> Dict[str, int]:
        """Fix imports in all Python files in a directory."""
        directory_path = Path(directory)
        stats = {
            'files_processed': 0,
            'files_modified': 0,
            'total_changes': 0,
            'errors': 0
        }
        
        for file_path in directory_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue
            
            try:
                modified, changes = self.fix_file(str(file_path), dry_run)
                stats['files_processed'] += 1
                
                if modified:
                    stats['files_modified'] += 1
                    stats['total_changes'] += len(changes)
                    
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped."""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            'venv',
            'env',
            '.venv',
            'build',
            'dist',
            '*.egg-info',
            'migrations',
            'alembic',
            'test_import_validator.py',  # Skip our test files
            'import_validator.py',
        ]
        
        for pattern in skip_patterns:
            if pattern in str(file_path):
                return True
        
        return False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix SVGX Engine imports")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--directory", default="svgx_engine", help="Directory to fix (default: svgx_engine)")
    parser.add_argument("--file", help="Fix a specific file")
    
    args = parser.parse_args()
    
    fixer = SVGXImportFixer()
    
    if args.file:
        # Fix a specific file
        modified, changes = fixer.fix_file(args.file, dry_run=args.dry_run)
        if modified:
            print(f"✅ Fixed {len(changes)} imports in {args.file}")
        else:
            print(f"ℹ️  No changes needed in {args.file}")
    else:
        # Fix entire directory
        print(f"🔧 Fixing imports in {args.directory}...")
        stats = fixer.fix_directory(args.directory, dry_run=args.dry_run)
        
        print(f"\n📊 Results:")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Files modified: {stats['files_modified']}")
        print(f"  Total changes: {stats['total_changes']}")
        print(f"  Errors: {stats['errors']}")
        
        if not args.dry_run:
            print(f"\n✅ Import fixing complete!")
        else:
            print(f"\n📝 Dry run complete - no files were modified")

if __name__ == "__main__":
    main() 