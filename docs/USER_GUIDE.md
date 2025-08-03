
# Arxos User Guide

## Getting Started

### Installation
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
pip install -r requirements.txt
```

### Configuration
1. Copy `config.example.yaml` to `config.yaml`
2. Update configuration values
3. Set environment variables

### Running the Application
```bash
python -m uvicorn main:app --reload
```

## Features

### AI Service
- Natural language processing
- Geometry validation
- Voice command processing

### GUS Service
- General user support
- Knowledge base queries
- PDF analysis

### SVGX Engine
- CAD-level precision
- Building information modeling
- Code compilation and validation

## Usage Examples

### Using the AI Service
```python
from services.ai import AIQueryRequest

request = AIQueryRequest(
    query="Analyze this building design",
    user_id="user123",
    context={"building_type": "residential"}
)

response = await ai_service.process_query(request)
print(response.content)
```

### Using the GUS Service
```python
from services.gus import GUSQueryRequest

request = GUSQueryRequest(
    query="What are the building codes for residential construction?",
    user_id="user123"
)

response = await gus_service.process_query(request)
print(response.content)
```

### Using the SVGX Engine
```python
from svgx_engine import SVGXEngine

engine = SVGXEngine()
result = engine.compile("your-svgx-code")
print(result)
```

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Ensure valid JWT token
2. **Rate Limiting**: Reduce request frequency
3. **Validation Errors**: Check input format

### Getting Help
- Check the logs for detailed error messages
- Review the API documentation
- Contact support with error details
