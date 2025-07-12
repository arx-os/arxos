# Arxos Platform Documentation

## Overview

This directory contains the consolidated documentation for the Arxos platform, a comprehensive SVG-BIM viewport management system with advanced features for building information modeling.

## Documentation Structure

### Core Documentation
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Complete developer guide with API reference, integration patterns, and best practices
- **[PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md)** - System architecture and design patterns
- **[BUSINESS_MODEL.md](BUSINESS_MODEL.md)** - Business model and market analysis
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines and development setup

### API Documentation
- **[COMPREHENSIVE_API_REFERENCE.md](COMPREHENSIVE_API_REFERENCE.md)** - Complete API reference for all services
- **[VIEWPORT_MANAGER_GUIDE.md](VIEWPORT_MANAGER_GUIDE.md)** - Consolidated viewport manager documentation (API, user guide, troubleshooting)

### User Documentation
- **[USER_GUIDES.md](USER_GUIDES.md)** - End-user guides and tutorials
- **[ONBOARDING.md](ONBOARDING.md)** - New user onboarding guide

### Deployment & Operations
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide (configuration, checklist, procedures)
- **[MONITORING_GUIDE.md](MONITORING_GUIDE.md)** - Monitoring, alerting, and logging setup
- **[LOGGING_STANDARDIZATION_GUIDE.md](LOGGING_STANDARDIZATION_GUIDE.md)** - Logging standards and implementation

### Development & Testing
- **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** - Testing strategies and implementation
- **[CODE_QUALITY_REVIEW.md](CODE_QUALITY_REVIEW.md)** - Code quality standards and review process

### Specialized Features
- **[FLOOR_VERSION_CONTROL_GUIDE.md](FLOOR_VERSION_CONTROL_GUIDE.md)** - Floor version control system documentation
- **[DATA_VENDOR_GUIDE.md](DATA_VENDOR_GUIDE.md)** - Data vendor integration and API
- **[BUILDING_SYSTEMS_LIBRARY.md](BUILDING_SYSTEMS_LIBRARY.md)** - Building systems and regulations

### Project Management
- **[DEVELOPMENT_PHASES.md](DEVELOPMENT_PHASES.md)** - Development roadmap and phases
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[RELEASE_NOTES.md](RELEASE_NOTES.md)** - Release notes and feature updates

## Quick Start

1. **For Developers**: Start with [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. **For Users**: Start with [USER_GUIDES.md](USER_GUIDES.md)
3. **For Deployment**: Start with [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
4. **For API Integration**: Start with [COMPREHENSIVE_API_REFERENCE.md](COMPREHENSIVE_API_REFERENCE.md)

## Documentation Standards

- All documentation follows markdown format
- Code examples include syntax highlighting
- API documentation includes request/response examples
- User guides include screenshots and step-by-step instructions
- Technical documentation includes architecture diagrams

## Contributing to Documentation

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to documentation.

## Support

For technical support or questions about the documentation, please refer to the appropriate guide or contact the development team.

## 📁 Repository-Specific Documentation

### Core Services
- **[arx-backend/README.md](../arx-backend/README.md)** - Go backend service documentation
- **[arx_svg_parser/README.md](../arx_svg_parser/README.md)** - SVG parsing and BIM processing service

### Frontend Applications
- **[arx-web-frontend/README.md](../arx-web-frontend/README.md)** - Web frontend application documentation

### Supporting Services
- **[arx-cmms/README.md](../arx-cmms/README.md)** - Computerized Maintenance Management System
- **[arx-database/README.md](../arx-database/README.md)** - Database schema and migrations
- **[arx-symbol-library/README.md](../arx-symbol-library/README.md)** - Building symbol library

### Development Tools
- **[arx-cli/README.md](../arx-cli/README.md)** - Command-line interface tools
- **[arx-devops/README.md](../arx-devops/README.md)** - DevOps and infrastructure tools

### New Engine Development
- **[arx-svg-engine/README.md](../arx-svg-engine/README.md)** - Next-generation SVG engine with geometry, physics, and BIM capabilities
  - **Architecture**: [arx-svg-engine/docs/architecture/](../arx-svg-engine/docs/architecture/) - Engine architecture and specifications
  - **API Reference**: [arx-svg-engine/docs/api/](../arx-svg-engine/docs/api/) - Engine API documentation
  - **Development Guides**: [arx-svg-engine/docs/guides/](../arx-svg-engine/docs/guides/) - Development and usage guides

## 🔧 Development Workflow

1. **Setup**: Follow [Onboarding](ONBOARDING.md) for initial setup
2. **Development**: Use [Developer Documentation](DEVELOPER_DOCUMENTATION.md) for implementation details
3. **Testing**: Run tests using [Testing Summary](TESTING_SUMMARY.md) procedures
4. **Deployment**: Deploy using [Deployment](DEPLOYMENT.md) guidelines
5. **Monitoring**: Monitor using [Monitoring Summary](MONITORING_SUMMARY.md) tools

## 🆕 Recent Updates

### January 2024: Repository Reorganization
- **arx-svg-engine**: New repository created for next-generation SVG engine development
- **Documentation Migration**: SVGX Specification and Agentic BIM documentation moved to `arx-svg-engine/docs/architecture/`
- **Architecture Separation**: Clear separation between current Arxos platform and new engine development

### SVG Engine Development
The new `arx-svg-engine` repository contains:
- **Core Engine**: Geometry, physics, and rendering fundamentals
- **Applications**: Editor, viewer, simulator, and collaboration tools
- **Integrations**: BIM, CAD, web, and mobile platform support
- **Services**: Microservices for model management, geometry processing, and real-time collaboration
- **Documentation**: Comprehensive architectural design, API reference, and development guides

## 📞 Support

- **Technical Issues**: Check [Developer Documentation](DEVELOPER_DOCUMENTATION.md) and [API Reference](COMPREHENSIVE_API_REFERENCE.md)
- **User Questions**: Refer to [User Guides](USER_GUIDES.md)
- **Integration Help**: Review [Data Vendor API](DATA_VENDOR_API.md) and [Floor Connector Guide](FLOOR_CONNECTOR_GUIDE.md)
- **Operations**: Use [Monitoring Summary](MONITORING_SUMMARY.md) and [Deployment](DEPLOYMENT.md)
- **SVG Engine**: Check [arx-svg-engine documentation](../arx-svg-engine/docs/) for new engine development

## 📝 Contributing

Please read [Contributing](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🛠️ Engineering Notes

### June 2024: PowerShell Migration Script Function Naming
- All functions in `run_funding_source_migration.ps1` previously named with the verb `Setup` (e.g., `Setup-SQLite`) have been renamed to use the approved verb `Initialize` (e.g., `Initialize-SQLite`).
- The function `Verify-Migration` has been renamed to `Test-Migration` to use the approved verb `Test`.
- This change follows [PowerShell approved verb best practices](https://learn.microsoft.com/en-us/powershell/scripting/developer/cmdlet/approved-verbs-for-windows-powershell-commands) and eliminates unapproved verb warnings.
- All function calls and definitions in the script have been updated accordingly.

---

*Last updated: January 2024*
