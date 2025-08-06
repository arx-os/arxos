#!/usr/bin/env python3
"""
Version Manager for Arxos SDKs
Manages versioning, changelog generation, and release automation
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VersionManager:
    def __init__(self, config_path: str = "config/version.yaml"):
        self.config = self.load_config(config_path)
        self.sdk_path = Path("generated")
        self.changelog_path = Path("changelogs")
        self.changelog_path.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load version configuration"""
        config_file = Path(__file__).parent.parent / config_path
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self.get_default_config()

        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    def get_default_config(self) -> Dict[str, Any]:
        """Get default version configuration"""
        return {
            "versioning": {
                "strategy": "semantic",
                "auto_increment": True,
                "require_changelog": True,
                "git_tags": True,
            },
            "services": {
                "arx-backend": {
                    "current_version": "1.0.0",
                    "version_file": "package.json",
                    "changelog_file": "CHANGELOG.md",
                },
                "arx-cmms": {
                    "current_version": "1.0.0",
                    "version_file": "package.json",
                    "changelog_file": "CHANGELOG.md",
                },
                "arx-database": {
                    "current_version": "1.0.0",
                    "version_file": "package.json",
                    "changelog_file": "CHANGELOG.md",
                },
            },
            "languages": {
                "typescript": {
                    "version_file": "package.json",
                    "version_field": "version",
                },
                "python": {"version_file": "setup.py", "version_field": "version"},
                "go": {"version_file": "go.mod", "version_field": "version"},
                "java": {"version_file": "pom.xml", "version_field": "version"},
                "csharp": {"version_file": "*.csproj", "version_field": "Version"},
                "php": {"version_file": "composer.json", "version_field": "version"},
            },
        }

    def get_current_version(self, service: str) -> str:
        """Get current version for a service"""
        service_config = self.config["services"].get(service, {})
        return service_config.get("current_version", "1.0.0")

    def calculate_next_version(self, service: str, change_type: str = "patch") -> str:
        """Calculate next version based on change type"""
        current_version = self.get_current_version(service)

        if self.config["versioning"]["strategy"] == "semantic":
            return self.calculate_semantic_version(current_version, change_type)
        else:
            return self.calculate_simple_version(current_version)

    def calculate_semantic_version(self, current_version: str, change_type: str) -> str:
        """Calculate semantic version"""
        major, minor, patch = map(int, current_version.split("."))

        if change_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif change_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"

    def calculate_simple_version(self, current_version: str) -> str:
        """Calculate simple version increment"""
        try:
            version_num = int(current_version)
            return str(version_num + 1)
        except ValueError:
            return "1.0.0"

    def update_version_files(
        self, service: str, new_version: str, language: str = None
    ):
        """Update version files for a service"""
        if language:
            languages = [language]
        else:
            languages = self.config["languages"].keys()

        for lang in languages:
            lang_config = self.config["languages"][lang]
            version_file = lang_config["version_file"]
            version_field = lang_config["version_field"]

            package_path = self.sdk_path / lang / service
            if not package_path.exists():
                continue

            version_file_path = package_path / version_file
            if not version_file_path.exists():
                continue

            self.update_version_file(
                version_file_path, version_field, new_version, lang
            )

    def update_version_file(
        self, file_path: Path, field: str, new_version: str, language: str
    ):
        """Update version in a specific file"""
        try:
            if language == "typescript" or language == "php":
                # JSON files
                with open(file_path, "r") as f:
                    data = json.load(f)

                data[field] = new_version

                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)

            elif language == "python":
                # Python setup.py
                with open(file_path, "r") as f:
                    content = f.read()

                # Update version in setup.py
                pattern = r'version\s*=\s*["\']([^"\']+)["\']'
                replacement = f'version="{new_version}"'
                content = re.sub(pattern, replacement, content)

                with open(file_path, "w") as f:
                    f.write(content)

            elif language == "go":
                # Go module file
                with open(file_path, "r") as f:
                    content = f.read()

                # Update version in go.mod
                pattern = r"go\s+(\d+\.\d+)"
                replacement = f"go 1.21"
                content = re.sub(pattern, replacement, content)

                with open(file_path, "w") as f:
                    f.write(content)

            elif language == "java":
                # Maven pom.xml
                with open(file_path, "r") as f:
                    content = f.read()

                # Update version in pom.xml
                pattern = r"<version>([^<]+)</version>"
                replacement = f"<version>{new_version}</version>"
                content = re.sub(pattern, replacement, content)

                with open(file_path, "w") as f:
                    f.write(content)

            elif language == "csharp":
                # C# project file
                with open(file_path, "r") as f:
                    content = f.read()

                # Update version in .csproj
                pattern = r"<Version>([^<]+)</Version>"
                replacement = f"<Version>{new_version}</Version>"
                content = re.sub(pattern, replacement, content)

                with open(file_path, "w") as f:
                    f.write(content)

            logger.info(f"Updated {file_path} to version {new_version}")

        except Exception as e:
            logger.error(f"Failed to update {file_path}: {e}")

    def generate_changelog(
        self, service: str, new_version: str, changes: List[Dict[str, str]]
    ):
        """Generate changelog for a service"""
        changelog_file = self.changelog_path / f"{service}_CHANGELOG.md"

        # Read existing changelog
        existing_content = ""
        if changelog_file.exists():
            with open(changelog_file, "r") as f:
                existing_content = f.read()

        # Generate new changelog entry
        timestamp = datetime.now().strftime("%Y-%m-%d")
        changelog_entry = f"""
## [{new_version}] - {timestamp}

"""

        # Group changes by type
        change_types = {
            "feature": [],
            "bugfix": [],
            "breaking": [],
            "documentation": [],
            "other": [],
        }

        for change in changes:
            change_type = change.get("type", "other")
            if change_type in change_types:
                change_types[change_type].append(change)
            else:
                change_types["other"].append(change)

        # Add changes to changelog
        for change_type, changes_list in change_types.items():
            if changes_list:
                changelog_entry += f"### {change_type.title()}\n"
                for change in changes_list:
                    changelog_entry += f"- {change['description']}\n"
                changelog_entry += "\n"

        # Combine with existing content
        new_content = changelog_entry + existing_content

        # Write changelog
        with open(changelog_file, "w") as f:
            f.write(new_content)

        logger.info(f"Generated changelog for {service} v{new_version}")
        return changelog_file

    def create_git_tag(self, service: str, version: str):
        """Create git tag for version"""
        if not self.config["versioning"]["git_tags"]:
            return

        try:
            tag_name = f"{service}-v{version}"
            message = f"Release {service} v{version}"

            subprocess.run(["git", "tag", "-a", tag_name, "-m", message], check=True)

            subprocess.run(["git", "push", "origin", tag_name], check=True)

            logger.info(f"Created git tag {tag_name}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create git tag: {e}")

    def analyze_changes(
        self, service: str, since_version: str = None
    ) -> List[Dict[str, str]]:
        """Analyze changes since last version"""
        changes = []

        try:
            # Get git log since last version
            if since_version:
                cmd = ["git", "log", f"{service}-v{since_version}..HEAD", "--oneline"]
            else:
                cmd = ["git", "log", "--oneline", "-n", "50"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        change = self.parse_commit_message(line)
                        if change:
                            changes.append(change)

        except Exception as e:
            logger.warning(f"Could not analyze changes: {e}")

        return changes

    def parse_commit_message(self, commit_line: str) -> Optional[Dict[str, str]]:
        """Parse commit message to extract change information"""
        # Extract commit hash and message
        parts = commit_line.split(" ", 1)
        if len(parts) != 2:
            return None

        commit_hash, message = parts

        # Determine change type based on message
        change_type = "other"
        if any(word in message.lower() for word in ["feat", "feature", "add", "new"]):
            change_type = "feature"
        elif any(word in message.lower() for word in ["fix", "bug", "patch"]):
            change_type = "bugfix"
        elif any(word in message.lower() for word in ["break", "breaking"]):
            change_type = "breaking"
        elif any(word in message.lower() for word in ["doc", "readme", "docs"]):
            change_type = "documentation"

        return {
            "hash": commit_hash,
            "message": message,
            "type": change_type,
            "description": message,
        }

    def release_service(
        self, service: str, change_type: str = "patch", dry_run: bool = False
    ):
        """Release a service with new version"""
        current_version = self.get_current_version(service)
        new_version = self.calculate_next_version(service, change_type)

        logger.info(f"Releasing {service} from v{current_version} to v{new_version}")

        # Analyze changes
        changes = self.analyze_changes(service, current_version)

        # Generate changelog
        changelog_file = self.generate_changelog(service, new_version, changes)

        if not dry_run:
            # Update version files
            self.update_version_files(service, new_version)

            # Create git tag
            self.create_git_tag(service, new_version)

            # Update config
            self.config["services"][service]["current_version"] = new_version
            self.save_config()

        return {
            "service": service,
            "old_version": current_version,
            "new_version": new_version,
            "changes": changes,
            "changelog_file": changelog_file,
            "dry_run": dry_run,
        }

    def save_config(self):
        """Save updated configuration"""
        config_file = Path(__file__).parent.parent / "config" / "version.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_release_summary(self, releases: List[Dict[str, Any]]) -> str:
        """Generate release summary"""
        summary = "# Arxos SDK Release Summary\n\n"

        for release in releases:
            summary += f"## {release['service']} v{release['new_version']}\n"
            summary += f"- Previous version: {release['old_version']}\n"
            summary += f"- Changes: {len(release['changes'])}\n"
            summary += f"- Changelog: {release['changelog_file']}\n\n"

        return summary


def main():
    parser = argparse.ArgumentParser(description="Manage Arxos SDK versions")
    parser.add_argument("--service", help="Specific service to release")
    parser.add_argument(
        "--change-type",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Type of version change",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run without making changes"
    )
    parser.add_argument(
        "--config", default="config/version.yaml", help="Config file path"
    )
    parser.add_argument(
        "--list-versions", action="store_true", help="List current versions"
    )

    args = parser.parse_args()

    manager = VersionManager(args.config)

    if args.list_versions:
        print("Current versions:")
        for service, config in manager.config["services"].items():
            print(f"  {service}: {config['current_version']}")
        return

    if args.service:
        # Release specific service
        result = manager.release_service(args.service, args.change_type, args.dry_run)
        releases = [result]
    else:
        # Release all services
        releases = []
        for service in manager.config["services"]:
            result = manager.release_service(service, args.change_type, args.dry_run)
            releases.append(result)

    # Generate summary
    summary = manager.get_release_summary(releases)
    print(summary)

    # Save summary to file
    timestamp = datetime.now().isoformat()
    summary_file = manager.changelog_path / f"release_summary_{timestamp}.md"
    with open(summary_file, "w") as f:
        f.write(summary)

    logger.info(f"Release summary saved to {summary_file}")


if __name__ == "__main__":
    main()
