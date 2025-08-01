# Arxos Scripts Directory

This directory contains organized scripts for the Arxos platform, categorized by their purpose and functionality.

## Directory Structure

```
scripts/
├── setup/                 # Environment setup and local dev bootstrap
├── deploy/                # Deployment and infrastructure automation
├── testing/               # Test execution, validation, and quality assurance
├── integration/           # Service integration and pipeline management
├── utils/                 # General-purpose tools and utilities
└── README.md             # This documentation file
```

## Directory Descriptions

### setup/
Environment setup scripts for local development and production environments.

**Files:**
- `setup_local.sh` - Local development environment setup script
- `setup_production_environment.sh` - Production environment configuration

**Usage:**
```bash
# Setup local development environment
./setup/setup_local.sh

# Setup production environment
./setup/setup_production_environment.sh [environment] [db_host] [db_port] [db_name] [db_user] [db_password]
```

### deploy/
Deployment and infrastructure automation scripts for CI/CD, Docker, and Kubernetes.

**Files:**
- `deploy_pipeline.sh` - Complete pipeline infrastructure deployment

**Usage:**
```bash
# Deploy the complete pipeline infrastructure
./deploy/deploy_pipeline.sh
```

### testing/
Scripts for running tests, validation, and quality assurance.

**Files:**
- `run_e2e_tests.py` - End-to-end testing for the complete Arxos pipeline
- `test_pipeline_integration.py` - Integration testing between Go orchestration and Python bridge
- `test_setup.py` - Environment setup validation and health checks

**Usage:**
```bash
# Run comprehensive E2E tests
python testing/run_e2e_tests.py

# Test pipeline integration
python testing/test_pipeline_integration.py

# Validate environment setup
python testing/test_setup.py
```

### integration/
Service integration and pipeline management scripts.

**Files:**
- `arx_integrate.py` - CLI tool for integrating building services into Arxos ecosystem
- `building_service_integration.py` - Comprehensive pipeline for building service integration
- `arx_pipeline.py` - Command-line interface for the Arxos pipeline system

**Usage:**
```bash
# Integrate a new building service
python integration/arx_integrate.py --service-type hvac --name "Smart HVAC System"

# Run the complete integration pipeline
python integration/building_service_integration.py

# Execute pipeline operations
python integration/arx_pipeline.py --system electrical --validate
```

### utils/
General-purpose tools, helpers, and one-off utilities.

**Files:**
- *(Currently empty - place general utilities here)*

## Script Categories Overview

### Environment Setup
Scripts in the `setup/` directory handle:
- Local development environment configuration
- Production environment setup
- Dependency installation
- Database initialization
- Service configuration

### Deployment & Infrastructure
Scripts in the `deploy/` directory handle:
- CI/CD pipeline deployment
- Docker container management
- Kubernetes orchestration
- Infrastructure provisioning
- Service deployment

### Testing & Quality Assurance
Scripts in the `testing/` directory handle:
- Unit test execution
- Integration testing
- End-to-end validation
- Performance benchmarking
- Environment health checks

### Service Integration
Scripts in the `integration/` directory handle:
- Building service integration
- Pipeline management
- System validation
- Schema generation
- Multi-system coordination

### Utilities
Scripts in the `utils/` directory handle:
- General-purpose tools
- Helper functions
- One-off utilities
- Data processing
- Format conversion

## Best Practices

1. **Script Organization**: Always place new scripts in the appropriate category directory
2. **Documentation**: Each script should have clear documentation and usage examples
3. **Error Handling**: Scripts should include proper error handling and exit codes
4. **Logging**: Use consistent logging patterns across all scripts
5. **Dependencies**: Document any external dependencies or requirements
6. **Testing**: Include tests for critical scripts in the testing directory

## Adding New Scripts

When adding new scripts:

1. **Categorize**: Determine which category the script belongs to
2. **Document**: Add clear documentation and usage examples
3. **Test**: Include appropriate tests in the testing directory
4. **Update**: Update this README if adding new categories

## Common Patterns

### Python Scripts
- Use shebang: `#!/usr/bin/env python3`
- Include docstrings with usage examples
- Add proper error handling and logging
- Use type hints where appropriate

### Shell Scripts
- Use shebang: `#!/bin/bash`
- Include set -e for error handling
- Add colored output for status messages
- Include help/usage information

### Environment Variables
- Use consistent naming conventions
- Document required environment variables
- Include validation for required variables

## Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure scripts have execute permissions (`chmod +x script.sh`)
2. **Path Issues**: Use relative paths or absolute paths consistently
3. **Dependencies**: Check that all required dependencies are installed
4. **Environment**: Verify that environment variables are set correctly

### Debug Mode
Most scripts support verbose/debug output. Use the `-v` or `--verbose` flag for detailed logging.

## Contributing

When contributing new scripts:

1. Follow the existing organization structure
2. Include comprehensive documentation
3. Add appropriate tests
4. Update this README if necessary
5. Follow the established coding standards

## Support

For issues with scripts:
1. Check the script's documentation
2. Review the troubleshooting section
3. Check logs for error messages
4. Verify environment setup
5. Contact the development team if issues persist 