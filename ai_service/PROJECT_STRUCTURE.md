# AI Service Project Structure

## Overview
This document outlines the complete directory structure for the Arxos AI Service, designed for "Building Infrastructure as Code" with field worker assistance.

## Directory Structure

```
ai_service/
├── README.md                           # Service documentation
├── PROJECT_STRUCTURE.md               # This file - complete structure overview
├── requirements.txt                   # Python dependencies
├── main.py                           # FastAPI service entry point
│
├── field_assistance/                  # Field worker AI assistance
│   ├── __init__.py                   # Module exports
│   ├── component_validator.py        # Input validation
│   ├── suggestion_engine.py          # Component suggestions
│   └── quality_scorer.py             # BILT token scoring
│
├── ingestion/                         # Multi-format building plan processing
│   ├── __init__.py                   # Module exports
│   ├── base_parser.py                # Abstract parser interface
│   ├── pdf_parser.py                 # PDF building plan parser (implemented)
│   ├── ifc_parser.py                 # IFC parser (placeholder)
│   ├── dwg_parser.py                 # DWG parser (placeholder)
│   ├── heic_parser.py                # Photo parser (placeholder)
│   └── ingestion_manager.py          # Parser coordination
│
├── ascii_generation/                  # ASCII art building representations
│   ├── __init__.py                   # Module exports
│   ├── ascii_generator.py            # Main ASCII generator
│   ├── floor_plan_renderer.py        # 2D floor plan renderer
│   └── building_3d_renderer.py       # 3D building renderer
│
├── mobile_integration/                # Mobile AR app integration (future)
│   ├── __init__.py                   # Module exports
│   └── mobile_session_manager.py     # AR session management
│
├── simple_vision/                     # Basic computer vision (future)
│   ├── __init__.py                   # Module exports
│   └── image_analyzer.py             # Image analysis and OCR
│
├── utils/                             # Shared utilities
│   ├── __init__.py                   # Module exports
│   ├── config_manager.py             # Configuration management
│   └── logger_config.py              # Logging setup
│
└── tests/                             # Comprehensive testing
    ├── __init__.py                   # Test module
    └── test_field_assistance.py      # Field assistance tests
```

## Module Dependencies

### Core Dependencies
- **main.py** → field_assistance, ingestion, ascii_generation
- **ingestion_manager.py** → base_parser, pdf_parser, ifc_parser, dwg_parser, heic_parser
- **ascii_generator.py** → floor_plan_renderer, building_3d_renderer

### Utility Dependencies
- **All modules** → utils.config_manager, utils.logger_config
- **main.py** → utils.setup_logging

## Implementation Status

### ✅ Implemented (Ready for Development)
- **Field Assistance**: Complete validation, suggestion, and scoring system
- **PDF Ingestion**: Full PDF parsing with building element extraction
- **Base Architecture**: Abstract interfaces and manager classes
- **ASCII Generation**: 2D and 3D rendering framework

### 🔄 Partially Implemented (Placeholder Structure)
- **IFC Parser**: Abstract interface, needs IFC library integration
- **DWG Parser**: Abstract interface, needs AutoCAD library integration
- **HEIC Parser**: Abstract interface, needs image processing libraries
- **Mobile Integration**: Session management framework, needs AR integration
- **Simple Vision**: Image analysis framework, needs computer vision libraries

### 📋 Future Development Areas
- **Advanced Parsers**: IFC, DWG, HEIC implementation
- **Mobile AR**: Real-time communication and session management
- **Computer Vision**: OCR, image analysis, quality assessment
- **Performance Optimization**: Caching, parallel processing, memory management

## Development Workflow

### 1. Current Development (PDF Focus)
- Test PDF ingestion with sample building plans
- Validate ASCII art generation quality
- Optimize field worker assistance responses

### 2. Next Phase (Additional Formats)
- Implement IFC parser for BIM files
- Add DWG support for AutoCAD drawings
- Integrate photo processing for paper plans

### 3. Future Phase (Mobile & Vision)
- Develop mobile AR session management
- Implement basic computer vision features
- Create real-time field worker assistance

## Testing Strategy

### Unit Tests
- **Field Assistance**: Validation, suggestions, scoring
- **Ingestion**: Parser interfaces, file handling
- **ASCII Generation**: Rendering, coordinate scaling

### Integration Tests
- **End-to-End**: PDF → Parsing → ASCII → Validation
- **API Endpoints**: All FastAPI endpoints
- **Performance**: Response times, memory usage

### Test Coverage Targets
- **Core Modules**: >90% coverage
- **Parser Modules**: >80% coverage
- **Utility Modules**: >95% coverage

## Configuration Management

### Environment Variables
- **Service**: Name, version, debug mode, log level
- **Server**: Host, port, workers, reload
- **Database**: Host, port, name, credentials
- **AI Service**: File size limits, timeouts, memory limits
- **Field Assistance**: Response timeouts, suggestion limits
- **Ingestion**: Supported formats, parser limits

### Configuration Files
- **Development**: `.env` files for local development
- **Production**: Environment variables in deployment
- **Testing**: Test-specific configuration overrides

## Performance Targets

### Response Times
- **Input Validation**: <100ms
- **Component Suggestions**: <200ms
- **Quality Scoring**: <500ms
- **PDF Ingestion**: <5 seconds
- **ASCII Generation**: <2 seconds

### Resource Usage
- **Memory**: <100MB total service
- **CPU**: <50% during peak processing
- **Storage**: <1GB temporary file storage
- **Network**: <10MB per request

## Security Considerations

### Input Validation
- **File Uploads**: Size limits, format validation, virus scanning
- **User Input**: Sanitization, injection prevention
- **API Access**: Rate limiting, authentication, authorization

### Data Protection
- **Temporary Files**: Secure deletion, access controls
- **User Data**: Encryption, privacy compliance
- **System Access**: Minimal privileges, audit logging

## Deployment Architecture

### Service Components
- **FastAPI Service**: Main application server
- **Background Workers**: File processing, ASCII generation
- **Cache Layer**: Redis for session and result caching
- **Database**: PostgreSQL for persistent data storage

### Scaling Strategy
- **Horizontal**: Multiple service instances
- **Vertical**: Resource allocation per instance
- **Async**: Non-blocking I/O for concurrent requests
- **Caching**: Multi-level caching for performance

## Monitoring & Observability

### Metrics Collection
- **Performance**: Response times, throughput, error rates
- **Resources**: Memory, CPU, disk, network usage
- **Business**: File processing success, user satisfaction

### Logging Strategy
- **Structured Logging**: JSON format for machine processing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Size-based rotation with compression
- **Centralized Logging**: Aggregation for analysis

## Future Roadmap

### Short Term (1-3 months)
- Complete PDF ingestion testing
- Optimize ASCII art generation
- Implement basic IFC support

### Medium Term (3-6 months)
- Full multi-format support
- Mobile AR session management
- Basic computer vision features

### Long Term (6+ months)
- Advanced AI/ML integration
- Real-time mobile assistance
- Enterprise features and scaling

## Contributing Guidelines

### Code Standards
- **Python**: PEP 8, type hints, async/await
- **Documentation**: Docstrings, README updates
- **Testing**: Unit tests for new features
- **Performance**: Meet response time targets

### Development Process
- **Feature Branches**: Create for new functionality
- **Code Review**: Required for all changes
- **Testing**: Pass all tests before merge
- **Documentation**: Update relevant docs

This structure provides a solid foundation for building the "Pokemon Go for buildings" platform while maintaining clean architecture and extensibility for future development.
