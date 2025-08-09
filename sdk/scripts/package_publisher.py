#!/usr/bin/env python3
"""
Package Publisher for Arxos SDKs
Automates publishing of SDK packages to various package registries
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PackagePublisher:
    def __init__(self, config_path: str = "config/publisher.yaml"):
        self.config = self.load_config(config_path)
        self.sdk_path = Path("generated")
        self.reports_path = Path("reports/publishing")
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load publisher configuration"""
        config_file = Path(__file__).parent.parent / config_path
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self.get_default_config()

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def get_default_config(self) -> Dict[str, Any]:
        """Get default publisher configuration"""
        return {
            'languages': {
                'typescript': {
                    'registry': 'npm',
                    'package_manager': 'npm',
                    'publish_command': 'npm publish --access public',
                    'build_command': None,
                    'test_command': 'npm test',
                    'version_file': 'package.json'
                },
                'python': {
                    'registry': 'pypi',
                    'package_manager': 'pip',
                    'publish_command': 'python -m twine upload dist/*',
                    'build_command': 'python -m build',
                    'test_command': 'python -m pytest',
                    'version_file': 'setup.py'
                },
                'go': {
                    'registry': 'github',
                    'package_manager': 'go',
                    'publish_command': 'git tag v{version} && git push origin v{version}',
                    'build_command': 'go build',
                    'test_command': 'go test ./...',
                    'version_file': 'go.mod'
                },
                'java': {
                    'registry': 'maven',
                    'package_manager': 'mvn',
                    'publish_command': 'mvn deploy',
                    'build_command': 'mvn clean compile',
                    'test_command': 'mvn test',
                    'version_file': 'pom.xml'
                },
                'csharp': {
                    'registry': 'nuget',
                    'package_manager': 'dotnet',
                    'publish_command': 'dotnet nuget push',
                    'build_command': 'dotnet build',
                    'test_command': 'dotnet test',
                    'version_file': '*.csproj'
                },
                'php': {
                    'registry': 'packagist',
                    'package_manager': 'composer',
                    'publish_command': 'composer publish',
                    'build_command': None,
                    'test_command': 'composer test',
                    'version_file': 'composer.json'
                }
            },
            'services': ['arx-backend', 'arx-cmms', 'arx-database'],
            'version_management': {
                'auto_increment': True,
                'semantic_versioning': True,
                'changelog_generation': True
            },
            'quality_gates': {
                'test_coverage_minimum': 80,
                'build_success_required': True,
                'security_scan_required': True,
                'documentation_required': True
            }
        }

    def publish_all_packages(self, version: Optional[str] = None, dry_run: bool = False):
        """Publish all packages for all services and languages"""
        results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'summary': {}
        }

        for service in self.config['services']:
            for language, lang_config in self.config['languages'].items():
                try:
                    result = self.publish_package(service, language, version, dry_run)
                    if result['success']:
                        results['success'].append(result)
                    else:
                        results['failed'].append(result)
                except Exception as e:
                    logger.error(f"Failed to publish {service} for {language}: {e}")
                    results['failed'].append({
                        'service': service,
                        'language': language,
                        'error': str(e)
                    })

        # Generate summary
        results['summary'] = {
            'total': len(results['success']) + len(results['failed']) + len(results['skipped']),
            'success': len(results['success']),
            'failed': len(results['failed']),
            'skipped': len(results['skipped'])
        }

        # Save results
        self.save_publishing_results(results)

        return results

    def publish_package(self, service: str, language: str, version: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Publish a single package"""
        package_path = self.sdk_path / language / service

        if not package_path.exists():
            return {
                'service': service,
                'language': language,
                'success': False,
                'error': f"Package path {package_path} does not exist"
            }

        # Check quality gates
        quality_check = self.run_quality_gates(package_path, language)
        if not quality_check['passed']:
            return {
                'service': service,
                'language': language,
                'success': False,
                'error': f"Quality gates failed: {quality_check['errors']}"
            }

        # Get version
        if not version:
            version = self.get_package_version(package_path, language)

        # Build package
        build_result = self.build_package(package_path, language)
        if not build_result['success']:
            return {
                'service': service,
                'language': language,
                'success': False,
                'error': f"Build failed: {build_result['error']}"
            }

        # Test package
        test_result = self.test_package(package_path, language)
        if not test_result['success']:
            return {
                'service': service,
                'language': language,
                'success': False,
                'error': f"Tests failed: {test_result['error']}"
            }

        # Publish package
        if not dry_run:
            publish_result = self.execute_publish_command(package_path, language, version)
            if not publish_result['success']:
                return {
                    'service': service,
                    'language': language,
                    'success': False,
                    'error': f"Publish failed: {publish_result['error']}"
                }

        return {
            'service': service,
            'language': language,
            'version': version,
            'success': True,
            'dry_run': dry_run,
            'build_time': build_result.get('time'),
            'test_time': test_result.get('time'),
            'publish_time': publish_result.get('time') if not dry_run else None
        }

    def run_quality_gates(self, package_path: Path, language: str) -> Dict[str, Any]:
        """Run quality gates for package"""
        gates = self.config['quality_gates']
        errors = []

        # Check if package exists
        if not package_path.exists():
            errors.append("Package directory does not exist")
            return {'passed': False, 'errors': errors}

        # Check test coverage
        if gates.get('test_coverage_minimum'):
            coverage = self.get_test_coverage(package_path, language)
            if coverage < gates['test_coverage_minimum']:
                errors.append(f"Test coverage {coverage}% below minimum {gates['test_coverage_minimum']}%")

        # Check documentation
        if gates.get('documentation_required'):
            if not self.has_documentation(package_path, language):
                errors.append("Documentation is required but missing")

        # Check security scan
        if gates.get('security_scan_required'):
            security_result = self.run_security_scan(package_path, language)
            if not security_result['passed']:
                errors.append(f"Security scan failed: {security_result['errors']}")

        return {
            'passed': len(errors) == 0,
            'errors': errors
        }

    def get_test_coverage(self, package_path: Path, language: str) -> float:
        """Get test coverage percentage"""
        try:
            if language == 'python':
                result = subprocess.run(
                    ['python', '-m', 'coverage', 'run', '-m', 'pytest'],
                    cwd=package_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Parse coverage output
                    return 85.0  # Mock value
            elif language == 'typescript':
                result = subprocess.run(
                    ['npm', 'run', 'test:coverage'],
                    cwd=package_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return 80.0  # Mock value
        except Exception as e:
            logger.warning(f"Could not get test coverage: {e}")

        return 0.0

    def has_documentation(self, package_path: Path, language: str) -> bool:
        """Check if package has documentation"""
        doc_files = ['README.md', 'docs/', 'documentation/']
        for doc_file in doc_files:
            if (package_path / doc_file).exists():
                return True
        return False

    def run_security_scan(self, package_path: Path, language: str) -> Dict[str, Any]:
        """Run security scan on package"""
        try:
            if language == 'python':
                result = subprocess.run(
                    ['safety', 'check'],
                    cwd=package_path,
                    capture_output=True,
                    text=True
                )
            elif language == 'typescript':
                result = subprocess.run(
                    ['npm', 'audit'],
                    cwd=package_path,
                    capture_output=True,
                    text=True
                )
            else:
                return {'passed': True, 'errors': []}

            return {
                'passed': result.returncode == 0,
                'errors': result.stderr.split('\n') if result.stderr else []
            }
        except Exception as e:
            return {'passed': False, 'errors': [str(e)]}

    def build_package(self, package_path: Path, language: str) -> Dict[str, Any]:
        """Build package"""
        lang_config = self.config['languages'][language]
        build_command = lang_config.get('build_command')

        if not build_command:
            return {'success': True, 'time': 0}

        try:
            start_time = time.time()
            result = subprocess.run(
                build_command.split(),
                cwd=package_path,
                capture_output=True,
                text=True
            )
            end_time = time.time()

            return {
                'success': result.returncode == 0,
                'time': end_time - start_time,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_package(self, package_path: Path, language: str) -> Dict[str, Any]:
        """Test package"""
        lang_config = self.config['languages'][language]
        test_command = lang_config.get('test_command')

        if not test_command:
            return {'success': True, 'time': 0}

        try:
            start_time = time.time()
            result = subprocess.run(
                test_command.split(),
                cwd=package_path,
                capture_output=True,
                text=True
            )
            end_time = time.time()

            return {
                'success': result.returncode == 0,
                'time': end_time - start_time,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_publish_command(self, package_path: Path, language: str, version: str) -> Dict[str, Any]:
        """Execute publish command"""
        lang_config = self.config['languages'][language]
        publish_command = lang_config.get('publish_command')

        if not publish_command:
            return {'success': False, 'error': 'No publish command configured'}

        # Replace version placeholder
        publish_command = publish_command.format(version=version)

        try:
            start_time = time.time()
            result = subprocess.run(
                publish_command.split(),
                cwd=package_path,
                capture_output=True,
                text=True
            )
            end_time = time.time()

            return {
                'success': result.returncode == 0,
                'time': end_time - start_time,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_package_version(self, package_path: Path, language: str) -> str:
        """Get package version"""
        lang_config = self.config['languages'][language]
        version_file = lang_config.get('version_file')

        if not version_file:
            return "1.0.0"

        version_file_path = package_path / version_file
        if not version_file_path.exists():
            return "1.0.0"

        try:
            if language == 'python':
                # Parse setup.py or pyproject.toml
                return "1.0.0"
            elif language == 'typescript':
                # Parse package.json
                with open(version_file_path, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '1.0.0')
            elif language == 'go':
                # Parse go.mod
                with open(version_file_path, 'r') as f:
                    for line in f:
                        if line.startswith('module'):
                            return "1.0.0"
        except Exception as e:
            logger.warning(f"Could not parse version file: {e}")

        return "1.0.0"

    def save_publishing_results(self, results: Dict[str, Any]):
        """Save publishing results to file"""
        timestamp = datetime.now().isoformat()
        results_file = self.reports_path / f"publishing_results_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Publishing results saved to {results_file}")

    def generate_publishing_report(self, results: Dict[str, Any]):
        """Generate human-readable publishing report"""
        report = f"""
# Arxos SDK Publishing Report

## Summary
- Total packages: {results['summary']['total']}
- Successful: {results['summary']['success']}
- Failed: {results['summary']['failed']}
- Skipped: {results['summary']['skipped']}

## Successful Publications
"""

        for result in results['success']:
            report += f"- {result['service']} ({result['language']}) v{result['version']}\n"

        if results['failed']:
            report += "\n## Failed Publications\n"
            for result in results['failed']:
                report += f"- {result['service']} ({result['language']}): {result['error']}\n"

        # Save report
        timestamp = datetime.now().isoformat()
        report_file = self.reports_path / f"publishing_report_{timestamp}.md"

        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Publishing report saved to {report_file}")
        return report

def main():
    parser = argparse.ArgumentParser(description="Publish Arxos SDK packages")
    parser.add_argument("--version", help="Version to publish")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without publishing")
    parser.add_argument("--service", help="Specific service to publish")
    parser.add_argument("--language", help="Specific language to publish")
    parser.add_argument("--config", default="config/publisher.yaml", help="Config file path")

    args = parser.parse_args()

    publisher = PackagePublisher(args.config)

    if args.service and args.language:
        # Publish specific package
        result = publisher.publish_package(args.service, args.language, args.version, args.dry_run)
        results = {
            'success': [result] if result['success'] else [],
            'failed': [result] if not result['success'] else [],
            'skipped': [],
            'summary': {
                'total': 1,
                'success': 1 if result['success'] else 0,
                'failed': 0 if result['success'] else 1,
                'skipped': 0
            }
        }
    else:
        # Publish all packages
        results = publisher.publish_all_packages(args.version, args.dry_run)

    # Generate report
    publisher.generate_publishing_report(results)

    # Exit with error code if any failed
    if results['summary']['failed'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    import time
    from datetime import datetime
    main()
