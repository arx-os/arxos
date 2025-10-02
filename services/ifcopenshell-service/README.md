# IfcOpenShell Service

A microservice for processing Industry Foundation Classes (IFC) files using IfcOpenShell, integrated with the ArxOS building management platform.

## Overview

This service provides enterprise-grade IFC processing capabilities including:
- IFC file parsing and entity extraction
- IFC validation and compliance checking
- Spatial operations and geometry processing
- Caching for improved performance
- Health monitoring and metrics

## Features

### Core Functionality
- **IFC Parsing**: Extract buildings, spaces, equipment, walls, doors, and windows from IFC files
- **IFC Validation**: Check files for buildingSMART compliance and spatial consistency
- **Health Monitoring**: Service health checks and status reporting
- **Metrics**: Performance and usage metrics collection

### Performance Features
- **Caching**: In-memory caching for processed IFC files
- **File Size Limits**: Configurable maximum file size limits
- **Error Handling**: Comprehensive error handling with detailed error codes
- **Logging**: Structured logging for debugging and monitoring

## API Endpoints

### Health Check
```http
GET /health
```
Returns service health status and configuration information.

**Response:**
```json
{
  "status": "healthy",
  "service": "ifcopenshell",
  "version": "0.8.3",
  "timestamp": "2024-01-01T00:00:00Z",
  "cache_enabled": true,
  "max_file_size": 104857600
}
```

### Parse IFC
```http
POST /api/parse
Content-Type: application/octet-stream
```
Parses an IFC file and extracts building data.

**Response:**
```json
{
  "success": true,
  "buildings": 1,
  "spaces": 25,
  "equipment": 150,
  "walls": 200,
  "doors": 50,
  "windows": 75,
  "total_entities": 501,
  "metadata": {
    "ifc_version": "IFC4",
    "file_size": 1024000,
    "processing_time": "2.5s",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Validate IFC
```http
POST /api/validate
Content-Type: application/octet-stream
```
Validates an IFC file for compliance and errors.

**Response:**
```json
{
  "success": true,
  "valid": true,
  "warnings": ["No spaces found in IFC file"],
  "errors": [],
  "compliance": {
    "buildingSMART": true,
    "ifc4": true,
    "spatial_consistency": false
  },
  "metadata": {
    "buildings": 1,
    "spaces": 0,
    "equipment": 25,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Metrics
```http
GET /metrics
```
Returns service metrics and performance data.

**Response:**
```json
{
  "ifc_requests_total": 150,
  "cache_size": 25,
  "max_file_size": 104857600,
  "cache_enabled": true
}
```

## Configuration

The service can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Flask environment (development/production) |
| `DEBUG` | `False` | Enable debug mode |
| `HOST` | `0.0.0.0` | Host to bind to |
| `PORT` | `5000` | Port to listen on |
| `MAX_FILE_SIZE` | `104857600` | Maximum file size in bytes (100MB) |
| `CACHE_ENABLED` | `True` | Enable caching |
| `CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |

## Installation

### Using Docker (Recommended)
```bash
# Build the service
docker build -t arxos-ifc-service:latest .

# Run the service
docker run -p 5000:5000 arxos-ifc-service:latest
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Integration with ArxOS

This service is designed to work seamlessly with the ArxOS platform:

1. **ArxOS Configuration**: Configure the service URL in ArxOS config
2. **Fallback Support**: ArxOS automatically falls back to native parsing if the service is unavailable
3. **Circuit Breaker**: ArxOS includes circuit breaker pattern for fault tolerance
4. **Health Monitoring**: ArxOS monitors service health and reports status

### ArxOS Configuration Example
```yaml
ifc:
  service:
    enabled: true
    url: "http://ifcopenshell-service:5000"
    timeout: "30s"
    retries: 3
  fallback:
    enabled: true
    parser: "native"
```

## Error Handling

The service provides detailed error responses with standardized error codes:

| Error Code | Description |
|------------|-------------|
| `NO_DATA` | No IFC data provided in request |
| `FILE_TOO_LARGE` | File size exceeds maximum allowed |
| `INVALID_FORMAT` | File is not a valid IFC format |
| `PARSE_ERROR` | Error parsing IFC file |
| `VALIDATION_ERROR` | Error validating IFC file |
| `INTERNAL_ERROR` | Internal server error |

**Error Response Format:**
```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds maximum allowed size of 104857600 bytes"
  }
}
```

## Performance Considerations

### File Size Limits
- Default maximum file size: 100MB
- Configurable via `MAX_FILE_SIZE` environment variable
- Large files may take longer to process

### Caching
- In-memory caching for processed IFC files
- Cache key based on file content hash
- Configurable TTL via `CACHE_TTL` environment variable

### Memory Usage
- Service uses approximately 512MB-2GB depending on file complexity
- Memory usage scales with IFC file size and complexity
- Consider resource limits in containerized deployments

## Monitoring and Logging

### Health Checks
- Service exposes `/health` endpoint for health monitoring
- Returns service status, version, and configuration
- Used by ArxOS for service availability monitoring

### Logging
- Structured logging with timestamps
- Log levels: INFO, WARN, ERROR, DEBUG
- Includes request/response timing and error details

### Metrics
- Request count and processing time
- Cache hit/miss ratios
- Error rates and types
- File size and processing statistics

## Development

### Project Structure
```
services/ifcopenshell-service/
├── Dockerfile              # Docker configuration
├── main.py                 # Flask application
├── requirements.txt        # Python dependencies
├── tests/                  # Test files
│   └── test_main.py       # Main test suite
└── README.md              # This file
```

### Adding New Features
1. Add new endpoints to `main.py`
2. Implement corresponding tests in `tests/test_main.py`
3. Update this README with new API documentation
4. Test with real IFC files

### Contributing
1. Follow Python PEP 8 style guidelines
2. Add tests for new functionality
3. Update documentation
4. Test with various IFC file formats and sizes

## Troubleshooting

### Common Issues

**Service won't start:**
- Check if port 5000 is available
- Verify Python dependencies are installed
- Check logs for error messages

**IFC parsing fails:**
- Verify IFC file format and version
- Check file size limits
- Review error messages in logs

**Performance issues:**
- Monitor memory usage
- Check cache configuration
- Consider file size limits

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG=true
python main.py
```

### Log Analysis
Check service logs for:
- Request/response timing
- Error details and stack traces
- Cache hit/miss ratios
- Memory usage patterns

## License

This service is part of the ArxOS project and follows the same licensing terms.
