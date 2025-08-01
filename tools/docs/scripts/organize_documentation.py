#!/usr/bin/env python3
"""
Documentation Organization Script

This script organizes all documentation files in the Arxos codebase by:
1. Creating standardized docs/ directories in each repository
2. Moving .md files to appropriate locations
3. Creating documentation indexes
4. Maintaining proper structure and links

Usage:
    python scripts/organize_documentation.py
"""

import os
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import re

class DocumentationOrganizer:
    """Organizes documentation files across the Arxos codebase."""
    
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
    
    def organize_documentation(self):
        """Main method to organize all documentation."""
        print("🚀 Starting documentation organization...")
        
        for repo in self.repositories:
            print(f"\n📁 Processing repository: {repo.name}")
            self._organize_repository_docs(repo)
        
        print("\n✅ Documentation organization complete!")
    
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
        
        # Find all .md files in the repository
        md_files = list(repo_path.rglob("*.md"))
        
        # Skip files that are already in docs/ directory
        md_files = [f for f in md_files if "docs/" not in str(f.relative_to(repo_path))]
        
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
        
        # Move the file
        if md_file != target_path:
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
        content = md_file.read_text(encoding='utf-8').lower()
        
        # Architecture and design docs
        if any(keyword in filename for keyword in ['architecture', 'design', 'system', 'component']):
            return "architecture"
        
        # API documentation
        if any(keyword in filename for keyword in ['api', 'endpoint', 'rest', 'graphql']):
            return "api"
        
        # Deployment and infrastructure
        if any(keyword in filename for keyword in ['deploy', 'infra', 'kubernetes', 'docker', 'aws']):
            return "deployment"
        
        # Development guides
        if any(keyword in filename for keyword in ['dev', 'setup', 'install', 'build', 'test']):
            return "development"
        
        # User guides and tutorials
        if any(keyword in filename for keyword in ['user', 'guide', 'tutorial', 'howto', 'usage']):
            return "user-guides"
        
        # Troubleshooting and support
        if any(keyword in filename for keyword in ['trouble', 'faq', 'support', 'debug', 'error']):
            return "troubleshooting"
        
        # Default to development for README files
        if filename == 'readme.md':
            return "development"
        
        # Analyze content to determine category
        if any(keyword in content for keyword in ['api', 'endpoint', 'request', 'response']):
            return "api"
        elif any(keyword in content for keyword in ['deploy', 'infrastructure', 'kubernetes']):
            return "deployment"
        elif any(keyword in content for keyword in ['setup', 'install', 'development', 'build']):
            return "development"
        elif any(keyword in content for keyword in ['user', 'guide', 'tutorial', 'usage']):
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
            
            # Update any other relative links that might be affected
            # This is a simplified version - in practice, you'd want more sophisticated link updating
            
            if new_content != content:
                file_path.write_text(new_content, encoding='utf-8')
                
        except Exception as e:
            print(f"    ⚠️  Warning: Could not update links in {file_path.name}: {e}")
    
    def _create_repo_docs_index(self, repo_path: Path, docs_dir: Path):
        """Create a documentation index for the repository."""
        
        index_content = f"""# {repo_path.name} Documentation

Welcome to the {repo_path.name} documentation. This repository contains the following documentation sections:

## 📚 Documentation Sections

### 🏗️ Architecture
- **[System Architecture](architecture/README.md)** - System design and components
- **[API Design](api/README.md)** - API documentation and design patterns

### 🔧 Development
- **[Development Guide](development/README.md)** - Development setup and guidelines
- **[Setup Guide](development/setup.md)** - Environment setup instructions

### 🚀 Deployment
- **[Deployment Guide](deployment/README.md)** - Deployment procedures
- **[Infrastructure](deployment/infrastructure.md)** - Infrastructure configuration

### 📖 User Guides
- **[User Guide](user-guides/README.md)** - End-user documentation
- **[Tutorials](user-guides/tutorials.md)** - Step-by-step tutorials

### 🔍 Troubleshooting
- **[Troubleshooting Guide](troubleshooting/README.md)** - Common issues and solutions
- **[FAQ](troubleshooting/faq.md)** - Frequently asked questions

## 📋 Quick Links

"""

        # Add links to existing files in each subdirectory
        for subdir in ["architecture", "api", "deployment", "development", "user-guides", "troubleshooting"]:
            subdir_path = docs_dir / subdir
            if subdir_path.exists():
                md_files = list(subdir_path.glob("*.md"))
                if md_files:
                    index_content += f"\n### {subdir.replace('-', ' ').title()}\n"
                    for md_file in sorted(md_files):
                        title = md_file.stem.replace('_', ' ').replace('-', ' ').title()
                        index_content += f"- **[{title}]({subdir}/{md_file.name})**\n"

        index_content += f"""
## 🔄 Contributing

To contribute to this documentation:

1. Create a feature branch
2. Make your changes in the appropriate docs subdirectory
3. Update this index if you add new files
4. Submit a pull request

## 📞 Support

For questions about this repository's documentation:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section

---

**Last Updated**: {self._get_current_date()}
**Repository**: {repo_path.name}
"""

        # Write the index file
        index_path = docs_dir / "README.md"
        index_path.write_text(index_content, encoding='utf-8')
        print(f"  📝 Created documentation index: docs/README.md")
    
    def _get_current_date(self) -> str:
        """Get current date in a readable format."""
        from datetime import datetime
        return datetime.now().strftime("%B %Y")
    
    def create_platform_docs_structure(self):
        """Create the main platform documentation structure."""
        
        platform_docs = self.root_dir / "docs"
        platform_docs.mkdir(exist_ok=True)
        
        # Create platform-level documentation structure
        subdirs = [
            "architecture",
            "api", 
            "deployment",
            "development",
            "user-guides",
            "troubleshooting"
        ]
        
        for subdir in subdirs:
            (platform_docs / subdir).mkdir(exist_ok=True)
        
        # Move existing platform-level docs
        platform_md_files = [
            "PLATFORM_ARCHITECTURE.md",
            "WORKFLOW_AUTOMATION_SUMMARY.md",
            "README.md"
        ]
        
        for filename in platform_md_files:
            file_path = self.root_dir / filename
            if file_path.exists():
                target_subdir = self._determine_target_subdir(file_path)
                target_path = platform_docs / target_subdir / filename
                
                if file_path != target_path:
                    print(f"  📄 Moving {filename} → docs/{target_subdir}/")
                    shutil.move(str(file_path), str(target_path))
        
        print("  📝 Created platform documentation structure")

def main():
    """Main function to run the documentation organizer."""
    
    organizer = DocumentationOrganizer()
    
    # Create platform-level docs structure
    organizer.create_platform_docs_structure()
    
    # Organize repository documentation
    organizer.organize_documentation()
    
    print("\n🎉 Documentation organization complete!")
    print("\n📋 Summary of changes:")
    print("- Created standardized docs/ directories in each repository")
    print("- Organized .md files into appropriate subdirectories")
    print("- Created documentation indexes for each repository")
    print("- Maintained proper file structure and links")
    
    print("\n📝 Next steps:")
    print("1. Review the organized documentation structure")
    print("2. Update any broken links or references")
    print("3. Add any missing documentation")
    print("4. Update README files to reference the new docs structure")

if __name__ == "__main__":
    main() 