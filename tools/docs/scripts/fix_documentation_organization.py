#!/usr/bin/env python3
"""
Fix Documentation Organization Script

This script fixes the documentation organization issues by:
1. Restoring original files from backups
2. Properly organizing them into the docs structure
3. Cleaning up backup files
4. Creating proper documentation indexes

Usage:
    python scripts/fix_documentation_organization.py
"""

import os
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import re

def handle_errors(func):
    """
    Decorator to handle errors securely.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Value error in {func.__name__}: {e}")
            raise HTTPException(status_code=400, detail="Invalid input")
        except FileNotFoundError as e:
            logger.error(f"File not found in {func.__name__}: {e}")
            raise HTTPException(status_code=404, detail="Resource not found")
        except PermissionError as e:
            logger.error(f"Permission error in {func.__name__}: {e}")
            raise HTTPException(status_code=403, detail="Access denied")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper


class DocumentationFixer:
    """Fixes documentation organization issues."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.repositories = self._discover_repositories()

    def _discover_repositories(self) -> List[Path]:
        """Discover all repository directories."""
        repositories = []

        # Main repositories (directories starting with 'arx-')
        for item in self.root_dir.iterdir():
            if item.is_dir() and item.name.startswith('arx-'):
                repositories.append(item)

        # Add root directory for platform-level docs
        repositories.append(self.root_dir)

        return repositories

    def fix_documentation(self):
        """Main method to fix documentation organization."""
        print("🔧 Starting documentation organization fix...")

        # First, restore original files from backups import backups
        self._restore_from_backups()

        # Then properly organize them
        for repo in self.repositories:
            print(f"\n📁 Processing repository: {repo.name}")
            self._organize_repository_docs(repo)

        # Clean up backup files
        self._cleanup_backups()

        print("\n✅ Documentation organization fix complete!")

    def _restore_from_backups(self):
        """Restore original files from backup files."""
        print("🔄 Restoring files from backups...")

        for repo in self.repositories:
            backup_files = list(repo.rglob("*.backup"))

            for backup_file in backup_files:
                # Determine original filename
                original_name = backup_file.stem  # Remove .backup extension
                original_path = backup_file.parent / original_name

                # If original doesn't exist, restore from backup import backup'
                if not original_path.exists():
                    print(f"  📄 Restoring {original_name} from backup")
                    shutil.copy2(backup_file, original_path)

    def _organize_repository_docs(self, repo_path: Path):
        """Organize documentation for a specific repository."""

        # Create docs directory structure
        docs_dir = repo_path / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Create subdirectories
        subdirs = [
            "architecture",
            "api",
            "deployment",
            "development",
            "user-guides",
            "troubleshooting"
        ]

        for subdir in subdirs:
            (docs_dir / subdir).mkdir(exist_ok=True)

        # Find all .md files in the repository (excluding docs/ and backup files)
        md_files = []
        for md_file in repo_path.rglob("*.md"):
            if "docs/" not in str(md_file.relative_to(repo_path)) and not md_file.name.endswith('.backup'):
                md_files.append(md_file)

        # Organize files
        for md_file in md_files:
            self._organize_md_file(md_file, docs_dir)

        # Create repository-specific documentation index
        self._create_repo_docs_index(repo_path, docs_dir)

    def _organize_md_file(self, md_file: Path, docs_dir: Path):
        """Organize a single .md file into the appropriate docs subdirectory."""

        # Determine the appropriate subdirectory based on filename and content
        target_subdir = self._determine_target_subdir(md_file)
        target_dir = docs_dir / target_subdir

        # Create target filename
        target_filename = self._create_target_filename(md_file)
        target_path = target_dir / target_filename

        # Move the file if it's not already in the right place'
        if md_file != target_path and not target_path.exists():
            print(f"  📄 Moving {md_file.name} → docs/{target_subdir}/{target_filename}")

            # Create backup of original
            backup_path = md_file.with_suffix(md_file.suffix + '.backup')
            shutil.copy2(md_file, backup_path)

            # Move to new location
            shutil.move(str(md_file), str(target_path))

            # Update any internal links in the moved file
            self._update_file_links(target_path, md_file.name, target_filename)

    def _determine_target_subdir(self, md_file: Path) -> str:
        """Determine the appropriate docs subdirectory for a file."""

        filename = md_file.name.lower()

        try:
            content = md_file.read_text(encoding='utf-8').lower()
        except Exception as e:
            content = ""

        # Architecture and design docs
        if any(keyword in filename for keyword in ['architecture', 'design', 'system', 'component', 'platform']):
            return "architecture"

        # API documentation
        if any(keyword in filename for keyword in ['api', 'endpoint', 'rest', 'graphql', 'integration']):
            return "api"

        # Deployment and infrastructure
        if any(keyword in filename for keyword in ['deploy', 'infra', 'kubernetes', 'docker', 'aws', 'monitoring']):
            return "deployment"

        # Development guides
        if any(keyword in filename for keyword in ['dev', 'setup', 'install', 'build', 'test', 'developer', 'development']):
            return "development"

        # User guides and tutorials
        if any(keyword in filename for keyword in ['user', 'guide', 'tutorial', 'howto', 'usage', 'training']):
            return "user-guides"

        # Troubleshooting and support
        if any(keyword in filename for keyword in ['trouble', 'faq', 'support', 'debug', 'error']):
            return "troubleshooting"

        # Default to development for README files
        if filename == 'readme.md':
            return "development"

        # Analyze content to determine category
        if any(keyword in content for keyword in ['api', 'endpoint', 'request', 'response', 'integration']):
            return "api"
        elif any(keyword in content for keyword in ['deploy', 'infrastructure', 'kubernetes', 'monitoring']):
            return "deployment"
        elif any(keyword in content for keyword in ['setup', 'install', 'development', 'build', 'developer']):
            return "development"
        elif any(keyword in content for keyword in ['user', 'guide', 'tutorial', 'usage', 'training']):
            return "user-guides"
        elif any(keyword in content for keyword in ['trouble', 'error', 'debug', 'fix']):
            return "troubleshooting"
        else:
            return "development"  # Default

    def _create_target_filename(self, md_file: Path) -> str:
        """Create an appropriate target filename."""

        # Remove common prefixes and create clean filename
        filename = md_file.stem.lower()

        # Remove common prefixes
        prefixes_to_remove = ['readme', 'index', 'main']
        for prefix in prefixes_to_remove:
            if filename.startswith(prefix):
                filename = filename[len(prefix):].lstrip('_-')
                break

        # If filename is empty after removing prefix, use original
        if not filename:
            filename = md_file.stem.lower()

        # Clean up filename
        filename = re.sub(r'[^a-z0-9_-]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_')

        return f"{filename}.md"

    def _update_file_links(self, file_path: Path, old_name: str, new_name: str):
        """Update internal links in a moved file."""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Update relative links to the file itself
            old_pattern = rf'\[([^\]]*)\]\(([^)]*{re.escape(old_name)})\)'
            new_content = re.sub(old_pattern, rf'[\1]({new_name})', content)

            if new_content != content:
                file_path.write_text(new_content, encoding='utf-8')

        except Exception as e:
            print(f"    ⚠️  Warning: Could not update links in {file_path.name}: {e}")

    def _create_repo_docs_index(self, repo_path: Path, docs_dir: Path):
        """Create a documentation index for a repository."""

        index_content = f"""# {repo_path.name} Documentation

This directory contains organized documentation for the {repo_path.name} repository.

## Documentation Structure

"""

        # Add sections for each subdirectory
        subdirs = ["architecture", "api", "deployment", "development", "user-guides", "troubleshooting"]

        for subdir in subdirs:
            subdir_path = docs_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*.md"))
                if files:
                    index_content += f"\n### {subdir.replace('-', ' ').title()}\n\n"
                    for file in sorted(files):
                        title = file.stem.replace('_', ' ').title()
                        index_content += f"- [{title}]({subdir}/{file.name})\n"

        # Write the index
        index_file = docs_dir / "README.md"
        index_file.write_text(index_content, encoding='utf-8')
        print(f"  📝 Created documentation index: docs/README.md")

    def _cleanup_backups(self):
        """Clean up backup files after successful organization."""
        print("\n🧹 Cleaning up backup files...")

        backup_count = 0
        for repo in self.repositories:
            backup_files = list(repo.rglob("*.backup"))
            for backup_file in backup_files:
                try:
                    backup_file.unlink()
                    backup_count += 1
                except Exception as e:
                    print(f"    ⚠️  Could not remove backup {backup_file}: {e}")

        print(f"  🗑️  Removed {backup_count} backup files")

def main():
    """Main function."""
    fixer = DocumentationFixer()
    fixer.fix_documentation()

if __name__ == "__main__":
    main()
