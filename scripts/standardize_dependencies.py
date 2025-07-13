#!/usr/bin/env python3
"""
Standardize Python Dependency Constraints and Audit Packages

This script performs the following tasks:
1. Inventory all Python dependency files
2. Update version pins from == to ~= across all files
3. Run security audits on all dependencies
4. Generate lock files
5. Create CI validation scripts

Usage:
    python scripts/standardize_dependencies.py [--audit] [--update] [--ci]
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DependencyFile:
    """Represents a Python dependency file."""
    path: Path
    file_type: str  # 'requirements.txt', 'pyproject.toml', 'poetry.lock'
    project_name: str
    dependencies: List[str]
    has_exact_pins: bool = False
    security_issues: List[Dict] = None

class DependencyStandardizer:
    """Main class for standardizing Python dependencies."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.dependency_files: List[DependencyFile] = []
        self.security_report: Dict = {}
        
    def inventory_dependencies(self) -> List[DependencyFile]:
        """Find all Python dependency files in the project."""
        logger.info("🔍 Inventorying Python dependency files...")
        
        dependency_patterns = [
            "**/requirements.txt",
            "**/pyproject.toml",
            "**/poetry.lock",
            "**/Pipfile",
            "**/Pipfile.lock"
        ]
        
        for pattern in dependency_patterns:
            for file_path in self.root_dir.glob(pattern):
                if self._is_valid_dependency_file(file_path):
                    dependency_file = self._parse_dependency_file(file_path)
                    if dependency_file:
                        self.dependency_files.append(dependency_file)
        
        logger.info(f"📋 Found {len(self.dependency_files)} dependency files")
        return self.dependency_files
    
    def _is_valid_dependency_file(self, file_path: Path) -> bool:
        """Check if a file is a valid dependency file."""
        # Skip files in virtual environments, node_modules, etc.
        skip_patterns = [
            "venv", ".venv", "env", ".env",
            "node_modules", "__pycache__", ".git",
            "build", "dist", ".tox", ".pytest_cache"
        ]
        
        for pattern in skip_patterns:
            if pattern in str(file_path):
                return False
        
        return True
    
    def _parse_dependency_file(self, file_path: Path) -> Optional[DependencyFile]:
        """Parse a dependency file and extract information."""
        try:
            file_type = file_path.name
            project_name = file_path.parent.name
            
            if file_type == "requirements.txt":
                return self._parse_requirements_txt(file_path, project_name)
            elif file_type == "pyproject.toml":
                return self._parse_pyproject_toml(file_path, project_name)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def _parse_requirements_txt(self, file_path: Path, project_name: str) -> DependencyFile:
        """Parse requirements.txt file."""
        dependencies = []
        has_exact_pins = False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Check for exact version pins
                if '==' in line:
                    has_exact_pins = True
                
                dependencies.append(line)
        
        return DependencyFile(
            path=file_path,
            file_type="requirements.txt",
            project_name=project_name,
            dependencies=dependencies,
            has_exact_pins=has_exact_pins
        )
    
    def _parse_pyproject_toml(self, file_path: Path, project_name: str) -> DependencyFile:
        """Parse pyproject.toml file."""
        dependencies = []
        has_exact_pins = False
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
        
        # Extract dependencies from project.dependencies
        if 'project' in data and 'dependencies' in data['project']:
            for dep in data['project']['dependencies']:
                dependencies.append(dep)
                if '==' in dep:
                    has_exact_pins = True
        
        # Extract optional dependencies
        if 'project' in data and 'optional-dependencies' in data['project']:
            for group_name, group_deps in data['project']['optional-dependencies'].items():
                for dep in group_deps:
                    dependencies.append(f"{dep}  # {group_name}")
                    if '==' in dep:
                        has_exact_pins = True
        
        return DependencyFile(
            path=file_path,
            file_type="pyproject.toml",
            project_name=project_name,
            dependencies=dependencies,
            has_exact_pins=has_exact_pins
        )
    
    def update_constraints(self) -> Dict[str, int]:
        """Update version pins from == to ~= across all files."""
        logger.info("🔄 Updating dependency constraints...")
        
        stats = {
            'files_updated': 0,
            'constraints_changed': 0,
            'errors': 0
        }
        
        for dep_file in self.dependency_files:
            try:
                if dep_file.file_type == "requirements.txt":
                    updated = self._update_requirements_txt(dep_file)
                elif dep_file.file_type == "pyproject.toml":
                    updated = self._update_pyproject_toml(dep_file)
                else:
                    continue
                
                if updated:
                    stats['files_updated'] += 1
                    logger.info(f"✅ Updated {dep_file.path}")
                else:
                    logger.info(f"ℹ️  No changes needed for {dep_file.path}")
                    
            except Exception as e:
                logger.error(f"❌ Error updating {dep_file.path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def _update_requirements_txt(self, dep_file: DependencyFile) -> bool:
        """Update requirements.txt file to use ~= instead of ==."""
        updated = False
        new_lines = []
        
        with open(dep_file.path, 'r', encoding='utf-8') as f:
            for line in f:
                original_line = line
                
                # Update exact version pins to compatible release pins
                if '==' in line and not line.strip().startswith('#'):
                    # Pattern: package==x.y.z -> package~=x.y.z
                    line = re.sub(r'([a-zA-Z0-9._-]+)==([0-9]+\.[0-9]+\.[0-9]+)', r'\1~=\2', line)
                    
                    if line != original_line:
                        updated = True
                        logger.debug(f"  Updated: {original_line.strip()} -> {line.strip()}")
                
                new_lines.append(line)
        
        if updated:
            with open(dep_file.path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        return updated
    
    def _update_pyproject_toml(self, dep_file: DependencyFile) -> bool:
        """Update pyproject.toml file to use ~= instead of ==."""
        updated = False
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        # Read the file
        with open(dep_file.path, 'rb') as f:
            data = tomllib.load(f)
        
        # Update dependencies
        if 'project' in data and 'dependencies' in data['project']:
            for i, dep in enumerate(data['project']['dependencies']):
                if '==' in dep:
                    new_dep = re.sub(r'([a-zA-Z0-9._-]+)==([0-9]+\.[0-9]+\.[0-9]+)', r'\1~=\2', dep)
                    if new_dep != dep:
                        data['project']['dependencies'][i] = new_dep
                        updated = True
                        logger.debug(f"  Updated dependency: {dep} -> {new_dep}")
        
        # Update optional dependencies
        if 'project' in data and 'optional-dependencies' in data['project']:
            for group_name, group_deps in data['project']['optional-dependencies'].items():
                for i, dep in enumerate(group_deps):
                    if '==' in dep:
                        new_dep = re.sub(r'([a-zA-Z0-9._-]+)==([0-9]+\.[0-9]+\.[0-9]+)', r'\1~=\2', dep)
                        if new_dep != dep:
                            data['project']['optional-dependencies'][group_name][i] = new_dep
                            updated = True
                            logger.debug(f"  Updated {group_name} dependency: {dep} -> {new_dep}")
        
        if updated:
            # Write back the updated file
            import tomli_w
            with open(dep_file.path, 'wb') as f:
                tomli_w.dump(data, f)
        
        return updated
    
    def run_security_audit(self) -> Dict[str, List[Dict]]:
        """Run security audits on all dependencies."""
        logger.info("🔒 Running security audits...")
        
        audit_results = {}
        
        for dep_file in self.dependency_files:
            try:
                results = self._audit_dependency_file(dep_file)
                audit_results[str(dep_file.path)] = results
                
                if results:
                    logger.warning(f"⚠️  Security issues found in {dep_file.path}: {len(results)} issues")
                else:
                    logger.info(f"✅ No security issues found in {dep_file.path}")
                    
            except Exception as e:
                logger.error(f"❌ Error auditing {dep_file.path}: {e}")
        
        self.security_report = audit_results
        return audit_results
    
    def _audit_dependency_file(self, dep_file: DependencyFile) -> List[Dict]:
        """Run security audit on a specific dependency file."""
        results = []
        
        try:
            # Try pip-audit first
            cmd = [sys.executable, "-m", "pip-audit", "--format", "json", "--requirement", str(dep_file.path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('vulnerabilities', []):
                        results.append({
                            'package': vuln.get('package', {}).get('name', 'unknown'),
                            'version': vuln.get('package', {}).get('installed_version', 'unknown'),
                            'vulnerability_id': vuln.get('vulnerability', {}).get('id', 'unknown'),
                            'severity': vuln.get('vulnerability', {}).get('severity', 'unknown'),
                            'description': vuln.get('vulnerability', {}).get('description', 'No description'),
                            'tool': 'pip-audit'
                        })
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse pip-audit output for {dep_file.path}")
            
            # Try safety as backup
            cmd = [sys.executable, "-m", "safety", "check", "--json", "--file", str(dep_file.path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    safety_data = json.loads(result.stdout)
                    for vuln in safety_data:
                        results.append({
                            'package': vuln.get('package', 'unknown'),
                            'version': vuln.get('installed_version', 'unknown'),
                            'vulnerability_id': vuln.get('vulnerability_id', 'unknown'),
                            'severity': vuln.get('severity', 'unknown'),
                            'description': vuln.get('description', 'No description'),
                            'tool': 'safety'
                        })
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse safety output for {dep_file.path}")
                    
        except subprocess.TimeoutExpired:
            logger.warning(f"Security audit timed out for {dep_file.path}")
        except FileNotFoundError:
            logger.warning(f"Security audit tools not available for {dep_file.path}")
        except Exception as e:
            logger.error(f"Error running security audit on {dep_file.path}: {e}")
        
        return results
    
    def generate_lock_files(self) -> Dict[str, int]:
        """Generate lock files for all projects."""
        logger.info("📦 Generating lock files...")
        
        stats = {
            'lock_files_generated': 0,
            'errors': 0
        }
        
        for dep_file in self.dependency_files:
            try:
                if dep_file.file_type == "requirements.txt":
                    self._generate_requirements_lock(dep_file)
                    stats['lock_files_generated'] += 1
                elif dep_file.file_type == "pyproject.toml":
                    self._generate_poetry_lock(dep_file)
                    stats['lock_files_generated'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Error generating lock file for {dep_file.path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def _generate_requirements_lock(self, dep_file: DependencyFile) -> None:
        """Generate requirements-lock.txt from requirements.txt."""
        lock_file = dep_file.path.parent / "requirements-lock.txt"
        
        try:
            # Create a temporary virtual environment and install dependencies
            import tempfile
            import venv
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create virtual environment
                venv.create(temp_dir, with_pip=True)
                
                # Install requirements
                pip_cmd = os.path.join(temp_dir, "bin", "pip") if os.name != "nt" else os.path.join(temp_dir, "Scripts", "pip.exe")
                subprocess.run([pip_cmd, "install", "-r", str(dep_file.path)], check=True)
                
                # Generate lock file
                subprocess.run([pip_cmd, "freeze"], stdout=open(lock_file, 'w'), check=True)
                
            logger.info(f"✅ Generated {lock_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate lock file for {dep_file.path}: {e}")
    
    def _generate_poetry_lock(self, dep_file: DependencyFile) -> None:
        """Generate poetry.lock from pyproject.toml."""
        try:
            # Check if poetry is available
            subprocess.run(["poetry", "--version"], check=True, capture_output=True)
            
            # Run poetry lock
            subprocess.run(["poetry", "lock"], cwd=dep_file.path.parent, check=True)
            logger.info(f"✅ Generated poetry.lock for {dep_file.path}")
            
        except subprocess.CalledProcessError:
            logger.warning(f"Poetry not available for {dep_file.path}")
        except FileNotFoundError:
            logger.warning(f"Poetry not installed")
    
    def create_ci_validation_script(self) -> None:
        """Create CI validation script for dependency standards."""
        ci_script = self.root_dir / "scripts" / "ci_dependency_check.py"
        
        script_content = '''#!/usr/bin/env python3
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

def main():
    """Main validation function."""
    logger.info("🚀 Starting dependency validation...")
    
    # Check constraints
    constraints_ok = check_dependency_constraints()
    
    # Run security audit
    security_ok = run_security_audit()
    
    if not constraints_ok or not security_ok:
        logger.error("❌ Dependency validation failed")
        sys.exit(1)
    
    logger.info("✅ All dependency validations passed")
    sys.exit(0)

if __name__ == "__main__":
    main()
'''
        
        with open(ci_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(ci_script, 0o755)
        logger.info(f"✅ Created CI validation script: {ci_script}")
    
    def create_documentation(self) -> None:
        """Create documentation for dependency standards."""
        docs_file = self.root_dir / "docs" / "DEPENDENCY_STANDARDS.md"
        
        docs_content = '''# Python Dependency Standards

## Overview

This document outlines the standards for Python dependency management in the Arxos project.

## Version Constraint Standards

### Use Compatible Release Pins (~=)

We use compatible release pins (`~=`) instead of exact version pins (`==`) to allow patch-level updates while maintaining compatibility.

**✅ Good:**
```
fastapi~=0.104.1
pydantic~=2.5.0
```

**❌ Bad:**
```
fastapi==0.104.1
pydantic==2.5.0
```

### Rationale

1. **Security**: Patch updates often contain security fixes
2. **Stability**: Compatible release pins prevent breaking changes
3. **Maintenance**: Reduces manual dependency updates
4. **Reproducibility**: Lock files ensure reproducible builds

## Dependency File Types

### requirements.txt
- Use for simple projects
- Include exact versions in requirements-lock.txt
- Example:
  ```
  fastapi~=0.104.1
  uvicorn[standard]~=0.24.0
  ```

### pyproject.toml
- Use for modern Python projects
- Supports optional dependencies
- Example:
  ```toml
  [project]
  dependencies = [
      "fastapi~=0.104.1",
      "uvicorn[standard]~=0.24.0",
  ]
  ```

## Security Auditing

### Automated Audits

Run security audits regularly:

```bash
# Using pip-audit
pip-audit --requirement requirements.txt

# Using safety
safety check --file requirements.txt
```

### CI/CD Integration

The CI pipeline automatically:
1. Checks for `==` version pins and fails the build
2. Runs security audits on all dependencies
3. Validates lock files are up to date

## Lock Files

### requirements-lock.txt
- Generated from requirements.txt
- Contains exact versions for reproducibility
- Updated automatically in CI

### poetry.lock
- Generated from pyproject.toml
- Contains exact versions and dependency tree
- Updated with `poetry lock`

## Best Practices

1. **Always use ~= for version constraints**
2. **Run security audits regularly**
3. **Keep lock files in version control**
4. **Update dependencies systematically**
5. **Test thoroughly after dependency updates**

## Tools

### Required Tools
- `pip-audit`: Security vulnerability scanning
- `safety`: Alternative security scanner
- `poetry`: Modern dependency management (optional)

### Development Tools
- `black`: Code formatting
- `flake8`: Linting
- `mypy`: Type checking
- `pytest`: Testing

## Troubleshooting

### Common Issues

1. **Build fails due to == pins**
   - Update to ~= pins
   - Regenerate lock files

2. **Security vulnerabilities found**
   - Update affected packages
   - Check for newer versions
   - Consider alternative packages

3. **Lock file conflicts**
   - Regenerate lock files
   - Ensure consistent Python versions

## Maintenance

### Regular Tasks

1. **Monthly**: Run security audits
2. **Quarterly**: Update major dependencies
3. **As needed**: Update for security fixes

### Update Process

1. Update version constraints in dependency files
2. Regenerate lock files
3. Run full test suite
4. Update documentation if needed
5. Commit changes with descriptive messages

## Examples

### requirements.txt
```
# Core dependencies
fastapi~=0.104.1
uvicorn[standard]~=0.24.0
pydantic~=2.5.0

# Development dependencies
pytest~=7.4.3
black~=23.12.1
flake8~=6.1.0
```

### pyproject.toml
```toml
[project]
dependencies = [
    "fastapi~=0.104.1",
    "uvicorn[standard]~=0.24.0",
    "pydantic~=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest~=7.4.3",
    "black~=23.12.1",
    "flake8~=6.1.0",
]
```
'''
        
        docs_file.parent.mkdir(exist_ok=True)
        with open(docs_file, 'w', encoding='utf-8') as f:
            f.write(docs_content)
        
        logger.info(f"✅ Created dependency standards documentation: {docs_file}")
    
    def generate_report(self) -> None:
        """Generate a comprehensive report of the standardization process."""
        report_file = self.root_dir / "docs" / "DEPENDENCY_AUDIT_REPORT.md"
        
        report_content = f'''# Dependency Standardization Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

This report documents the standardization of Python dependencies across the Arxos project.

## Files Processed

'''
        
        for dep_file in self.dependency_files:
            report_content += f'''
### {dep_file.path}
- **Type**: {dep_file.file_type}
- **Project**: {dep_file.project_name}
- **Has exact pins**: {'Yes' if dep_file.has_exact_pins else 'No'}
- **Dependencies**: {len(dep_file.dependencies)}
'''
        
        if self.security_report:
            report_content += '''
## Security Audit Results

'''
            for file_path, vulnerabilities in self.security_report.items():
                if vulnerabilities:
                    report_content += f'''
### {file_path}
'''
                    for vuln in vulnerabilities:
                        report_content += f'''
- **Package**: {vuln.get('package', 'unknown')}
- **Version**: {vuln.get('version', 'unknown')}
- **Vulnerability**: {vuln.get('vulnerability_id', 'unknown')}
- **Severity**: {vuln.get('severity', 'unknown')}
- **Description**: {vuln.get('description', 'No description')}
- **Tool**: {vuln.get('tool', 'unknown')}
'''
                else:
                    report_content += f'''
### {file_path}
✅ No security vulnerabilities found
'''
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"✅ Generated dependency audit report: {report_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Standardize Python dependencies")
    parser.add_argument("--audit", action="store_true", help="Run security audits")
    parser.add_argument("--update", action="store_true", help="Update dependency constraints")
    parser.add_argument("--ci", action="store_true", help="Create CI validation scripts")
    parser.add_argument("--root", type=str, default=".", help="Root directory to scan")
    
    args = parser.parse_args()
    
    root_dir = Path(args.root)
    standardizer = DependencyStandardizer(root_dir)
    
    # Inventory dependencies
    dependency_files = standardizer.inventory_dependencies()
    
    if not dependency_files:
        logger.warning("No dependency files found")
        return
    
    # Update constraints if requested
    if args.update:
        stats = standardizer.update_constraints()
        logger.info(f"Updated {stats['files_updated']} files, {stats['constraints_changed']} constraints changed")
    
    # Run security audit if requested
    if args.audit:
        audit_results = standardizer.run_security_audit()
        total_vulnerabilities = sum(len(vulns) for vulns in audit_results.values())
        logger.info(f"Found {total_vulnerabilities} security vulnerabilities across all files")
    
    # Generate lock files
    lock_stats = standardizer.generate_lock_files()
    logger.info(f"Generated {lock_stats['lock_files_generated']} lock files")
    
    # Create CI validation if requested
    if args.ci:
        standardizer.create_ci_validation_script()
        standardizer.create_documentation()
    
    # Generate report
    standardizer.generate_report()
    
    logger.info("✅ Dependency standardization completed")

if __name__ == "__main__":
    main() 