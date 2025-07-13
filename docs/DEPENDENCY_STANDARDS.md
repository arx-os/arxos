# Python Dependency Standards

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

# Using our custom script
python scripts/security_audit.py
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

## Scripts

### Standardization Script
```bash
# Update all dependencies to use ~= constraints
python scripts/standardize_dependencies.py --update

# Run security audit
python scripts/standardize_dependencies.py --audit

# Create CI validation scripts
python scripts/standardize_dependencies.py --ci
```

### Security Audit Script
```bash
# Run comprehensive security audit
python scripts/security_audit.py

# Generate JSON report
python scripts/security_audit.py --format json --output audit_report.json
```

### CI Validation Script
```bash
# Run CI validation
python scripts/ci_dependency_check.py
```

## Compliance Checklist

- [ ] All dependencies use `~=` constraints
- [ ] No `==` version pins in dependency files
- [ ] Security audits run regularly
- [ ] Lock files are up to date
- [ ] CI validation passes
- [ ] Documentation is current

## Migration Guide

### From == to ~=

1. **Identify exact pins**:
   ```bash
   grep -r "==" requirements.txt pyproject.toml
   ```

2. **Update constraints**:
   ```bash
   # Replace == with ~= in all files
   sed -i 's/==/~=/g' requirements.txt
   ```

3. **Regenerate lock files**:
   ```bash
   pip freeze > requirements-lock.txt
   ```

4. **Test thoroughly**:
   ```bash
   python -m pytest
   ```

### From >= to ~=

1. **Identify minimum versions**:
   ```bash
   grep -r ">=" pyproject.toml
   ```

2. **Update to compatible release**:
   ```toml
   # Before
   "fastapi>=0.104.0"
   
   # After
   "fastapi~=0.104.0"
   ```

3. **Test compatibility**:
   ```bash
   pip install -e .
   python -m pytest
   ```

## Security Considerations

### Critical Vulnerabilities
- **Immediate action required**
- Update to patched version
- Consider alternative packages if needed

### High Severity Vulnerabilities
- **Update within 1 week**
- Test thoroughly after update
- Monitor for regressions

### Medium/Low Severity Vulnerabilities
- **Update within 1 month**
- Include in regular maintenance
- Document any workarounds

## Monitoring

### Automated Monitoring
- CI/CD pipeline validation
- Regular security scans
- Dependency update notifications

### Manual Monitoring
- Monthly dependency reviews
- Quarterly security assessments
- Annual dependency audits

## Support

For questions about dependency management:
1. Check this documentation
2. Review existing examples
3. Run validation scripts
4. Contact the development team 