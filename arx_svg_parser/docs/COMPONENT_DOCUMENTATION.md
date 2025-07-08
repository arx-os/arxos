# Component Documentation

## Architecture Overview

```
arx_svg_parser/
├── Core Services
│   ├── SVG Parser
│   ├── BIM Assembly Pipeline
│   ├── Symbol Recognition
│   └── Rule Engine
├── Data Management
│   ├── Symbol Library (JSON + Hardcoded)
│   ├── BIM Models
│   └── Rule Definitions
├── API Layer
│   ├── FastAPI Endpoints
│   ├── Authentication
│   └── Validation
└── Utilities
    ├── CLI Tools
    ├── Testing Framework
    └── Documentation
```

## Core Components

### Symbol Library
- **JSON Symbols**: Dynamic loading from external JSON files
- **Hardcoded Symbols**: Built-in symbol definitions
- **System-based Organization**: Symbols organized by system type
- **Metadata Support**: Rich symbol metadata and properties

### Current Status
- JSON symbols: Dynamic loading functional
- Symbol validation: Schema-based validation
- Bulk operations: Import/export support
- API endpoints: Full CRUD operations

### JSON Examples:
- Dynamic loading from ../arx-symbol-library/*.json files
- Schema validation for all symbols
- Metadata extraction and validation
- System-based filtering and search

### Funding Source Integration
- All symbols can now include an optional `funding_source` property in their JSON definition. This is parsed as a top-level field and can be used for tracking the source of funding for each symbol/component.

## Service Dependencies

### Core Dependencies
- **FastAPI**: Web framework for API endpoints
- **Pydantic**: Data validation and serialization
- **jsonschema**: JSON schema validation
- **uvicorn**: ASGI server for development

### Symbol Management
- **JSONSymbolLibrary**: JSON-based symbol loading and caching
- **SymbolManager**: CRUD operations for symbols
- **SymbolSchemaValidator**: Schema validation service

### Authentication & Security
- **JWT**: Token-based authentication
- **Role-based Access Control**: Permission management
- **Password Hashing**: Secure credential storage

### Data Processing
- **SVG Processing**: XML parsing and manipulation
- **BIM Assembly**: Element creation and relationships
- **Rule Engine**: Dynamic rule evaluation

### Utilities
- **CLI Tools**: Command-line interface
- **Testing Framework**: Unit and integration tests
- **Logging**: Structured logging system

## Component Integration

### Symbol Library Integration
- **JSONSymbolLibrary**: Primary symbol loading service
- **SymbolManager**: CRUD operations and validation
- **Schema Validation**: JSON schema compliance checking
- **Bulk Operations**: Import/export functionality

### API Layer Integration
- **FastAPI Router**: RESTful endpoints
- **Authentication Middleware**: JWT token validation
- **Validation Middleware**: Request/response validation
- **Error Handling**: Global exception management

### CLI Integration
- **Command Parsing**: Argument handling
- **File Operations**: JSON file management
- **Validation**: Schema and data validation
- **Output Formatting**: User-friendly display

## Development Guidelines

### Code Standards
- **Type Hints**: Required for all functions
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Graceful error management
- **Testing**: Unit and integration tests

### Symbol Management
- **JSON Format**: All symbols in JSON format
- **Schema Validation**: JSON schema compliance
- **Metadata**: Rich symbol metadata
- **Versioning**: Symbol version tracking

### API Design
- **RESTful**: Standard HTTP methods
- **Validation**: Request/response validation
- **Authentication**: JWT-based security
- **Documentation**: OpenAPI/Swagger docs

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization

## Performance Considerations

### Symbol Library
- **Caching**: In-memory symbol caching
- **Lazy Loading**: On-demand symbol loading
- **Indexing**: Fast symbol lookup
- **Compression**: Efficient storage

### API Performance
- **Pagination**: Large result sets
- **Filtering**: Efficient querying
- **Caching**: Response caching
- **Background Processing**: Async operations

### Data Processing
- **Streaming**: Large file processing
- **Batch Operations**: Bulk processing
- **Memory Management**: Efficient resource usage
- **Concurrency**: Parallel processing

## Security Implementation

### Authentication
- **JWT Tokens**: Secure token-based auth
- **Password Hashing**: bcrypt for security
- **Session Management**: Token expiration
- **Refresh Tokens**: Secure token renewal

### Authorization
- **Role-based Access**: Permission levels
- **Resource Protection**: Endpoint security
- **Input Validation**: Request sanitization
- **Rate Limiting**: API abuse prevention

### Data Security
- **Input Sanitization**: XSS prevention
- **SQL Injection**: Parameterized queries
- **File Upload**: Secure file handling
- **Encryption**: Sensitive data protection

## Monitoring and Logging

### Application Monitoring
- **Health Checks**: Service availability
- **Performance Metrics**: Response times
- **Error Tracking**: Exception monitoring
- **Usage Analytics**: API usage patterns

### Logging Strategy
- **Structured Logging**: JSON format logs
- **Log Levels**: Appropriate verbosity
- **Log Rotation**: File management
- **Centralized Logging**: Aggregated logs

### Alerting
- **Error Alerts**: Critical failures
- **Performance Alerts**: Slow responses
- **Security Alerts**: Suspicious activity
- **Capacity Alerts**: Resource limits

## Deployment Considerations

### Environment Configuration
- **Environment Variables**: Configuration management
- **Database Connections**: Connection pooling
- **External Services**: API integrations
- **Security Settings**: Production hardening

### Containerization
- **Docker**: Application containerization
- **Docker Compose**: Multi-service orchestration
- **Health Checks**: Container monitoring
- **Resource Limits**: Memory and CPU constraints

### CI/CD Pipeline
- **Automated Testing**: Test execution
- **Code Quality**: Linting and formatting
- **Security Scanning**: Vulnerability detection
- **Deployment Automation**: Automated releases

## Troubleshooting Guide

### Common Issues
1. **Symbol Loading**: Check JSON file format and schema
2. **API Errors**: Verify authentication and permissions
3. **Performance Issues**: Monitor resource usage
4. **Validation Errors**: Check data format compliance

### Debugging Tools
- **Log Analysis**: Structured log review
- **API Testing**: Endpoint validation
- **Schema Validation**: JSON schema checking
- **Performance Profiling**: Resource usage analysis

### Support Resources
- **Documentation**: Comprehensive guides
- **API Reference**: Endpoint documentation
- **Examples**: Usage examples and demos
- **Community**: Developer support channels 