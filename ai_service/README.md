# Arxos AI Service - Field Worker Assistance

## Purpose
Lightweight AI assistance for field workers mapping buildings:
1. **Input Validation** - Validate field worker observations in real-time
2. **Component Suggestions** - Help identify building elements during AR input
3. **Quality Scoring** - Assess contribution quality for BILT token rewards
4. **Real-time Assistance** - Provide help during mobile AR sessions
5. **Building Plan Ingestion** - Process multiple file formats to create ASCII art BIM

## What This Service Does
- **Simple Validation** - Check if field worker input makes sense
- **Component Recognition** - Basic identification of common building elements
- **Quality Assessment** - Score contributions for token rewards
- **Mobile Integration** - Work seamlessly with mobile AR app
- **Multi-Format Ingestion** - Process PDF, IFC, DWG, HEIC photos of building plans

## What This Service Does NOT Do
- **Complex AI/ML Processing** - No heavy neural network inference
- **Advanced Computer Vision** - No complex image analysis
- **3D Reconstruction** - No complex LiDAR processing
- **Model Training** - No complex ML pipeline
- **Desktop BIM Tools** - No complex CAD-like features

## Architecture
```
ai_service/
├── field_assistance/    # AI help for field workers
│   ├── component_validator.py    # Validate input
│   ├── suggestion_engine.py      # Suggest components
│   └── quality_scorer.py         # Score contributions
├── ingestion/           # Building plan file processing
│   ├── base_parser.py           # Abstract parser interface
│   ├── pdf_parser.py            # PDF building plan parser
│   ├── ingestion_manager.py     # Coordinate all parsers
│   └── __init__.py              # Module exports
├── mobile_integration/  # Mobile app integration (future)
├── simple_vision/       # Basic computer vision (future)
├── utils/              # Shared utilities (future)
├── main.py             # FastAPI service
└── requirements.txt    # Dependencies
```

## Supported File Formats
- **PDF** - Building plans and floor plans (current)
- **IFC** - Building Information Modeling files (future)
- **DWG** - AutoCAD drawings (future)
- **HEIC** - Photos of paper building plans (future)
- **Other formats** - Extensible parser system

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start service
python main.py
```

## Endpoints

### Field Worker Assistance
- `POST /validate/component` - Validate field worker input
- `POST /suggest/component` - Suggest component type from photo/text
- `POST /score/quality` - Score contribution quality for BILT tokens

### Building Plan Ingestion
- `POST /ingest/building-plan` - Process building plan file
- `GET /ingest/supported-formats` - List supported file formats
- `POST /ingest/validate-file` - Validate file without processing
- `GET /ingest/parser-status` - Status of all parsers

### System
- `GET /health` - Service health check

## Performance Targets
- **Input Validation**: <100ms response time
- **Component Suggestions**: <200ms response time
- **Quality Scoring**: <500ms response time
- **PDF Ingestion**: <5 seconds for typical building
- **Memory Usage**: <100MB total service memory

## Adding New File Format Support
1. Create new parser class inheriting from `BaseParser`
2. Implement required abstract methods
3. Register parser with `IngestionManager`
4. Add to supported formats list

Example:
```python
from .base_parser import BaseParser

class IFCParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.supported_formats = ['ifc']
        self.parser_name = "IFCParser"
    
    async def can_parse(self, file_path: str) -> bool:
        # Implementation here
        pass
    
    # ... implement other required methods
```

## Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Start with auto-reload
python main.py
```