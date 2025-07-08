# Usage Guide

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
```python
from arx_svg_parser import SVGProcessor

# Initialize processor
processor = SVGProcessor()

# Process SVG file
result = processor.process_file("floor_plan.svg")
print(f"Found {len(result.symbols)} symbols")
```

## Configuration

### JSON Configuration
Create `config.json`:

```json
{
  "symbol_library_path": "../arx-symbol-library",
  "output_format": "bim",
  "validation_level": "strict",
  "logging": {
    "level": "INFO",
    "file": "arx_parser.log"
  },
  "api": {
    "host": "localhost",
    "port": 8000,
    "debug": false
  }
}
```

### Loading Configuration
```python
import json
from arx_svg_parser import load_config

config = load_config('config.json')
processor = SVGProcessor(config)
```

## API Usage

### Start Server
```bash
python -m arx_svg_parser.api.main
```

### Available Endpoints
- `GET /api/v1/symbols` - List symbols
- `POST /api/v1/symbols` - Create symbol
- `GET /api/v1/symbols/{id}` - Get symbol
- `PUT /api/v1/symbols/{id}` - Update symbol
- `DELETE /api/v1/symbols/{id}` - Delete symbol

### Example API Calls
```python
import requests

# List symbols
response = requests.get('http://localhost:8000/api/v1/symbols')
symbols = response.json()

# Create symbol
symbol_data = {
    "name": "HVAC Unit",
    "system": "mechanical",
    "svg": {"content": "<g>...</g>"}
}
response = requests.post('http://localhost:8000/api/v1/symbols', json=symbol_data)
```

## CLI Usage

### Symbol Management
```bash
# List symbols
python -m arx_svg_parser.cmd.symbol_manager_cli list

# Create symbol
python -m arx_svg_parser.cmd.symbol_manager_cli create --name "HVAC Unit" --system mechanical

# Update symbol
python -m arx_svg_parser.cmd.symbol_manager_cli update --id hvac_unit --name "Updated HVAC"

# Delete symbol
python -m arx_svg_parser.cmd.symbol_manager_cli delete --id hvac_unit
```

### Validation
```bash
# Validate single symbol
python -m arx_svg_parser.cmd.symbol_manager_cli validate --id hvac_unit

# Validate library
python -m arx_svg_parser.cmd.symbol_manager_cli validate-library --output report.json
```

### Bulk Operations
```bash
# Bulk import
python -m arx_svg_parser.cmd.symbol_manager_cli bulk-import --file symbols.json

# Bulk export
python -m arx_svg_parser.cmd.symbol_manager_cli bulk-export --format json --output exported_symbols.json
```

## Symbol Library

### JSON Format
Symbols are stored in JSON format with the following structure:

```json
{
  "name": "HVAC Unit",
  "system": "mechanical",
  "description": "Air handling unit",
  "svg": {
    "content": "<g id=\"hvac\">...</g>"
  },
  "properties": {
    "capacity": "5000 CFM",
    "voltage": "480V"
  },
  "connections": [
    {
      "type": "electrical",
      "position": {"x": 10, "y": 20}
    }
  ],
  "tags": ["hvac", "mechanical", "air-handling"],
  "metadata": {
    "version": "1.0",
    "created": "2024-01-01T00:00:00Z",
    "author": "system"
  }
}
```

### System Organization
Symbols are organized by system type:
- `mechanical/` - HVAC, plumbing, etc.
- `electrical/` - Electrical components
- `security/` - Security systems
- `network/` - Network infrastructure

### Validation
All symbols must conform to the JSON schema:
```bash
python -m arx_svg_parser.validate_symbols
```

## Advanced Features

### Custom Symbol Creation
```python
from arx_svg_parser.models.symbol import Symbol

# Create custom symbol
symbol = Symbol(
    name="Custom Component",
    system="mechanical",
    svg_content="<g id=\"custom\">...</g>",
    properties={"custom_prop": "value"}
)

# Save to library
symbol_manager = SymbolManager()
symbol_manager.create_symbol(symbol)
```

### Bulk Operations
```python
from arx_svg_parser.services.symbol_manager import SymbolManager

# Bulk import
symbol_manager = SymbolManager()
result = symbol_manager.bulk_create_symbols(symbols_list)

# Bulk export
exported = symbol_manager.bulk_export_symbols(format="json")
```

### API Integration
```python
from arx_svg_parser.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test API endpoints
response = client.get("/api/v1/symbols")
assert response.status_code == 200
```

## Error Handling

### Common Errors
1. **Invalid JSON**: Check symbol file format
2. **Schema Validation**: Verify symbol structure
3. **Missing Dependencies**: Install required packages
4. **Permission Errors**: Check file permissions

### Debugging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Process with detailed output
processor = SVGProcessor(debug=True)
result = processor.process_file("test.svg")
```

## Performance Optimization

### Caching
```python
from arx_svg_parser.services.json_symbol_library import JSONSymbolLibrary

# Enable caching
library = JSONSymbolLibrary(enable_cache=True)
symbols = library.get_all_symbols()  # Cached on first load
```

### Batch Processing
```python
# Process multiple files
for file in svg_files:
    result = processor.process_file(file)
    # Process results in batches
```

### Memory Management
```python
# Clear cache when needed
library.clear_cache()

# Process large files in chunks
processor.process_large_file("large.svg", chunk_size=1000)
```

## Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_symbol_management.py
```

### Integration Tests
```bash
# Run integration tests
python -m pytest tests/test_integration.py

# Run API tests
python -m pytest tests/test_api_endpoints.py
```

### Performance Tests
```bash
# Run performance tests
python -m pytest tests/test_performance.py
```

## Deployment

### Docker
```bash
# Build image
docker build -t arx-svg-parser .

# Run container
docker run -p 8000:8000 arx-svg-parser
```

### Production Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python -m arx_svg_parser.api.main --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Installation Issues
1. **Python Version**: Ensure Python 3.8+
2. **Dependencies**: Install all requirements
3. **Permissions**: Check file permissions
4. **Path Issues**: Verify import paths

### Runtime Issues
1. **Memory Errors**: Increase memory limits
2. **Timeout Errors**: Adjust timeout settings
3. **Connection Errors**: Check network connectivity
4. **Validation Errors**: Verify data format

### Performance Issues
1. **Slow Processing**: Enable caching
2. **Memory Usage**: Optimize batch sizes
3. **API Response**: Implement pagination
4. **File I/O**: Use async operations

## Support

### Documentation
- [API Reference](API_DOCUMENTATION.md)
- [Component Documentation](COMPONENT_DOCUMENTATION.md)
- [Testing Guide](TESTING_SUMMARY.md)

### Examples
- [Usage Examples](examples/)
- [API Examples](examples/api_examples.py)
- [CLI Examples](examples/cli_examples.py)

### Community
- GitHub Issues: Report bugs and feature requests
- Documentation: Comprehensive guides and tutorials
- Examples: Sample code and use cases 