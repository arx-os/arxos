# CI/CD Symbol Validation

## Overview

This document describes the JSON schema validation system integrated into the CI/CD pipeline to ensure all symbol files comply with the defined schema.

## Components

### Validation Script
- **Location**: `arx_svg_parser/scripts/validate_symbols.py`
- **Purpose**: Validates all JSON symbol files against the schema
- **Features**:
  - Recursive file discovery
  - Detailed error reporting
  - CI/CD friendly exit codes
  - Report generation
  - Verbose output options

### CI/CD Integration
- **GitHub Actions**: `.github/workflows/validate-symbols.yml`
- **Shell Script**: `arx_svg_parser/scripts/ci_validate_symbols.sh`
- **Requirements**: `arx_svg_parser/requirements-ci.txt`

## Usage

### Local Validation
```bash
# Basic validation
cd arx_svg_parser
python scripts/validate_symbols.py

# Verbose output
python scripts/validate_symbols.py --verbose

# Custom paths
python scripts/validate_symbols.py \
  --schema-path ../arx-symbol-library/schemas/symbol.schema.json \
  --symbols-path ../arx-symbol-library

# Generate report
python scripts/validate_symbols.py --report validation_report.json
```

### Shell Script Usage
```bash
# Run validation
./arx_svg_parser/scripts/ci_validate_symbols.sh

# Install dependencies only
./arx_svg_parser/scripts/ci_validate_symbols.sh --install-deps

# Validate paths only
./arx_svg_parser/scripts/ci_validate_symbols.sh --validate-paths

# Generate report
./arx_svg_parser/scripts/ci_validate_symbols.sh --report
```

### GitHub Actions
The validation runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

## Configuration

### Schema Path
- **Default**: `../arx-symbol-library/schemas/symbol.schema.json`
- **Override**: Use `--schema-path` argument

### Symbols Path
- **Default**: `../arx-symbol-library`
- **Override**: Use `--symbols-path` argument

### Excluded Files
The validation script automatically excludes:
- Schema files (`symbol.schema.json`)
- Index files (`index.json`, `categories.json`, `systems.json`)
- Files in `schemas/` directories

## Error Handling

### Validation Errors
```json
{
  "file": "mechanical/hvac_unit.json",
  "errors": [
    "  system: 'invalid_system' is not one of ['mechanical', 'electrical', 'security', 'network']",
    "  svg: 'content' is a required property"
  ]
}
```

### Common Issues
1. **Missing required fields**: Ensure all required properties are present
2. **Invalid system types**: Use only valid system values
3. **Invalid JSON syntax**: Check for JSON formatting errors
4. **Schema violations**: Verify against the current schema

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Validate Symbol Files
on:
  push:
    branches: [ main, develop ]
    paths:
      - 'arx-symbol-library/**/*.json'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'arx-symbol-library/**/*.json'

jobs:
  validate-symbols:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - run: pip install jsonschema
    - run: python scripts/validate_symbols.py --verbose --exit-code
```

### GitLab CI
```yaml
validate_symbols:
  stage: test
  image: python:3.9
  script:
    - pip install jsonschema
    - python arx_svg_parser/scripts/validate_symbols.py --verbose --exit-code
  only:
    changes:
      - arx-symbol-library/**/*.json
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Validate Symbols') {
            steps {
                sh '''
                    pip install jsonschema
                    python arx_svg_parser/scripts/validate_symbols.py --verbose --exit-code
                '''
            }
        }
    }
}
```

## Testing

### Test Script
```bash
# Run validation tests
python arx_svg_parser/scripts/validate_symbols_test.py
```

### Test Coverage
The test script covers:
- Valid symbol validation
- Invalid symbol validation
- Missing schema handling
- Empty directory handling
- CLI functionality

## Monitoring

### Validation Reports
Reports include:
- Total files checked
- Valid files count
- Invalid files with detailed errors
- Validation timestamp
- Schema and paths used

### CI/CD Artifacts
- Validation reports are uploaded as artifacts
- Failed validations generate detailed comments on PRs
- Reports are preserved for analysis

## Troubleshooting

### Common Issues

#### Schema Not Found
```
❌ Schema file not found: ../arx-symbol-library/schemas/symbol.schema.json
```
**Solution**: Verify schema file exists and path is correct

#### No Symbol Files Found
```
❌ No symbol files found to validate
```
**Solution**: Check symbols directory path and file extensions

#### Python Dependencies
```
ModuleNotFoundError: No module named 'jsonschema'
```
**Solution**: Install dependencies with `pip install jsonschema`

#### Permission Issues
```
Permission denied: scripts/validate_symbols.py
```
**Solution**: Make script executable with `chmod +x scripts/validate_symbols.py`

### Debug Mode
```bash
# Enable verbose output
python scripts/validate_symbols.py --verbose

# Check paths
./scripts/ci_validate_symbols.sh --validate-paths

# Install dependencies
./scripts/ci_validate_symbols.sh --install-deps
```

## Best Practices

### Schema Development
1. **Version control**: Track schema changes in version control
2. **Backward compatibility**: Maintain backward compatibility when possible
3. **Documentation**: Document schema changes and requirements
4. **Testing**: Test schema changes with existing symbols

### Symbol Development
1. **Validation first**: Validate symbols before committing
2. **Schema compliance**: Follow the defined schema strictly
3. **Testing**: Test new symbols with the validation script
4. **Documentation**: Document symbol properties and requirements

### CI/CD Integration
1. **Early validation**: Run validation early in the pipeline
2. **Fast feedback**: Provide quick feedback on validation failures
3. **Detailed reports**: Generate detailed reports for analysis
4. **Artifact preservation**: Preserve validation artifacts

## Future Enhancements

### Planned Features
- **Incremental validation**: Only validate changed files
- **Parallel processing**: Validate files in parallel
- **Custom validators**: Support for custom validation rules
- **Integration testing**: Test symbol integration with applications

### Potential Improvements
- **Performance optimization**: Optimize validation performance
- **Enhanced reporting**: More detailed validation reports
- **Web interface**: Web-based validation interface
- **API integration**: REST API for validation 