# Changelog

## [Latest] - 2024-12-01

### Added
- **Symbol Library**: All JSON symbol files now include optional `funding_source` property for tracking asset funding sources
- **JSON Schema Validation**: Comprehensive JSON schema validation for all symbols
- **Bulk Operations**: Import/export functionality with background processing
- **CLI Tools**: Comprehensive command-line interface for symbol management
- **API Endpoints**: Full REST API with authentication and authorization
- **Schema Validator**: JSON schema validation service with detailed error reporting

### Changed
- **Symbol Format**: Migrated from YAML to JSON format for all symbol files
- **JSON Parser**: Enhanced `load_symbol_library()` function to extract `funding_source` from JSON properties
- **Validation**: Updated validation to use JSON schema instead of YAML validation
- **Documentation**: Updated all documentation to reflect JSON-only symbol format

### Fixed
- **Symbol Loading**: Improved JSON symbol loading performance
- **Validation**: Enhanced JSON schema validation with detailed error messages
- **API**: Fixed authentication and authorization issues
- **CLI**: Improved error handling and user feedback

## [Previous] - 2024-11-30

### Added
- **Symbol Management**: CRUD operations for symbol management
- **Authentication**: JWT-based authentication system
- **Authorization**: Role-based access control
- **Bulk Operations**: Background processing for large datasets
- **Progress Tracking**: Real-time job monitoring
- **Error Handling**: Comprehensive error reporting

### Changed
- **Symbol Library**: Enhanced JSON symbol library with caching
- **API Design**: Improved REST API design and documentation
- **CLI Interface**: Enhanced command-line interface
- **Testing**: Expanded test coverage and integration tests

### Fixed
- **Performance**: Optimized symbol loading and caching
- **Security**: Enhanced authentication and authorization
- **Validation**: Improved JSON schema validation
- **Documentation**: Updated API and CLI documentation

## [Earlier] - 2024-11-29

### Added
- **JSON Symbol Library**: New JSON-based symbol library implementation
- **Symbol Manager**: CRUD operations for symbol management
- **Schema Validation**: JSON schema validation service
- **API Framework**: FastAPI-based REST API
- **CLI Framework**: Command-line interface framework
- **Testing Framework**: Comprehensive testing suite

### Changed
- **Architecture**: Migrated from YAML to JSON for symbol storage
- **Validation**: Implemented JSON schema validation
- **API**: Designed RESTful API endpoints
- **CLI**: Created command-line interface

### Fixed
- **Symbol Loading**: Improved symbol loading performance
- **Validation**: Enhanced validation with detailed error messages
- **Documentation**: Updated documentation for JSON format
- **Testing**: Expanded test coverage

## [Initial] - 2024-11-28

### Added
- **Project Structure**: Initial project structure and organization
- **Basic Services**: Core service implementations
- **Documentation**: Initial documentation and guides
- **Testing**: Basic testing framework
- **Configuration**: Project configuration and setup

### Changed
- **None**: Initial release

### Fixed
- **None**: Initial release
