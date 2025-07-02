# Arx SVG Parser

A FastAPI microservice for parsing SVG files and extracting building information.

## Installation

```bash
git clone https://github.com/arx/arx_svg_parser.git
cd arx_svg_parser
```

## Usage

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## API Endpoints

- `POST /parse` - Parse SVG file
- `POST /annotate` - Annotate SVG elements
- `POST /scale` - Scale SVG elements
- `POST /bim` - Generate BIM data

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Overview

This microservice provides SVG parsing and analysis capabilities for the Arx platform.

### Directory Structure

```
arx_svg_parser/
├── app.py                 # FastAPI application entry point
├── auth.py               # Authentication utilities
├── bim_builder.py        # BIM data generation
├── classifier.py         # Element classification
├── db.py                 # Database operations
├── geometry_utils.py     # Geometric calculations
├── models/               # Data models
│   ├── __init__.py
│   ├── annotate.py
│   ├── bim.py
│   ├── ingest.py
│   ├── parse.py
│   ├── scale.py
│   └── system_elements.py
├── routers/              # API route handlers
│   ├── annotate.py
│   ├── bim.py
│   ├── ingest.py
│   ├── parse.py
│   └── scale.py
├── services/             # Business logic services
│   ├── bim_extraction.py
│   ├── bim_extractor.py
│   ├── svg_reader.py
│   ├── svg_symbol_library.py
│   ├── svg_writer.py
│   ├── transform.py
│   └── vision_pipeline.py
├── svg_parser.py         # Core SVG parsing logic
├── tasks.py              # Background task processing
├── tests/                # Unit tests
│   ├── test_annotate.py
│   ├── test_bim_builder.py
│   ├── test_classifier.py
│   ├── test_geometry_utils.py
│   ├── test_ingest.py
│   ├── test_parse.py
│   ├── test_scale.py
│   ├── test_svg_parser.py
│   ├── test_tasks.py
│   └── test_webhook.py
├── webhook.py            # Webhook handling
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── README.md           # This file
```

## User Roles & Data Flow

### Roles
1. **Admin**: Full access to all features
2. **Editor**: Can annotate and modify SVGs
3. **Viewer**: Read-only access to parsed data

### Data Flow
1. **Upload**: SVG files uploaded via API
2. **Parse**: SVG elements extracted and classified
3. **Annotate**: Users add metadata and notes
4. **Scale**: Apply real-world measurements
5. **Export**: Generate BIM/IFC data

## Setup

1. Clone  
   ```bash
   git clone https://github.com/arx/arx_svg_parser.git
   cd arx_svg_parser
   ```
2. Environment Setup  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run  
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Key API Endpoints

| Endpoint                                 | Method | Description                                      |
|------------------------------------------|--------|--------------------------------------------------|
| `/v1/parse/recognize-symbols`            | POST   | Recognize symbols in text or SVG                  |
| `/v1/parse/render-symbols`               | POST   | Render recognized symbols into SVG                |
| `/v1/parse/auto-recognize-and-render`    | POST   | Upload PDF/SVG, auto-recognize and render symbols |
| `/v1/parse/extract-bim`                  | POST   | Extract BIM data from SVG with dynamic symbols    |

## Typical Workflow

1. **Upload a PDF or SVG drawing**
2. **Auto-recognize and render symbols**
   - Use `/v1/parse/auto-recognize-and-render` to process the file
   - Returns SVG with symbols rendered and recognition stats
3. **(Optional) Update symbol positions or remove symbols**
   - Use `/v1/parse/update-symbol-position` or `/v1/parse/remove-symbol`
4. **Extract BIM data**
   - Use `/v1/parse/extract-bim` with the annotated SVG
   - Returns structured BIM data (devices, rooms, systems)

## Example API Usage

### 1. Recognize Symbols in Text
```bash
curl -X POST http://localhost:8000/v1/parse/recognize-symbols \
  -H "Content-Type: application/json" \
  -d '{
    "content": "AHU-1 AIR HANDLING UNIT RTU-1 ROOFTOP UNIT VAV-1",
    "content_type": "text",
    "confidence_threshold": 0.5
  }'
```

### 2. Render Recognized Symbols into SVG
```bash
curl -X POST http://localhost:8000/v1/parse/render-symbols \
  -F "svg_content=@drawing.svg" \
  -F "building_id=TEST_BUILDING" \
  -F "floor_label=FLOOR_1"
```

### 3. Auto-Recognize and Render (PDF/SVG Upload)
```bash
curl -X POST http://localhost:8000/v1/parse/auto-recognize-and-render \
  -F "file=@drawing.svg" \
  -F "building_id=TEST_BUILDING" \
  -F "floor_label=FLOOR_1" \
  -F "confidence_threshold=0.5"
```

### 4. Extract BIM Data from SVG
```bash
curl -X POST http://localhost:8000/v1/parse/extract-bim \
  -F "svg_content=@annotated.svg" \
  -F "building_id=TEST_BUILDING" \
  -F "floor_label=FLOOR_1"
```

## Example Response: Symbol Recognition
```json
{
  "recognized_symbols": [
    {"symbol_id": "ahu", "symbol_data": {"display_name": "Air Handling Unit (AHU)", ...}, "confidence": 0.95, ...},
    ...
  ],
  "total_recognized": 5,
  "symbol_library_info": {"total_symbols": 129, ...},
  "confidence_threshold": 0.5,
  "content_type": "text"
}
```

## Example Response: Rendered SVG
```json
{
  "svg": "<svg>...</svg>",
  "rendered_symbols": [
    {"symbol_id": "ahu", "object_id": "ahu_12345678", ...},
    ...
  ],
  "total_recognized": 5,
  "total_rendered": 5,
  "building_id": "TEST_BUILDING",
  "floor_label": "FLOOR_1"
}
```

## Example Response: BIM Extraction
```json
{
  "devices": [
    {"name": "Air Handling Unit (AHU)", "system": "mechanical", "position": {"x": 100, "y": 100}, ...},
    ...
  ],
  "rooms": [
    {"name": "Room 101", "type": "general", "devices": [ ... ]},
    ...
  ],
  "systems": {"mechanical": [ ... ], "electrical": [ ... ]},
  "relationships": []
}
```

## Running the Service

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
3. Access the OpenAPI docs at:
   - [http://localhost:8000/docs](http://localhost:8000/docs)

## Testing

- Run all unit tests:
  ```bash
  pytest tests/
  ```
- Run API endpoint tests:
  ```bash
  python test_api_endpoints.py
  ```

## See Also
- [PDF_UPLOAD_GUIDE.md](./PDF_UPLOAD_GUIDE.md) for PDF-specific workflow and troubleshooting

## Object ID Service

A unified `ObjectIDService` is provided in `services/object_id_service.py` for generating and validating both system-specific and legacy object IDs. This matches the backend Go implementation and ensures consistent object ID handling across the platform.

### Usage Example

```python
from services.object_id_service import ObjectIDService

# Generate a system-specific object ID
object_id = ObjectIDService.generate_system_object_id('electrical', 1, 2, 1, 1)
# -> 'epnl1.spnl2.jb01.lf01'

# Validate a system-specific object ID
is_valid = ObjectIDService.is_valid_system_object_id('epnl1.spnl2.jb01.lf01', 'electrical')

# Validate any object ID (system or legacy)
is_valid_any = ObjectIDService.is_valid_any_object_id('BUILDING_L1_E_AHU_001')

# Detect system from object ID
system = ObjectIDService.detect_system_from_id('epnl1.spnl2.jb01.lf01')

# Parse a system object ID
parsed = ObjectIDService.parse_system_object_id('epnl1.spnl2.jb01.lf01')
# -> ('electrical', 1, 2, 1, 1)
```

See the code in `services/object_id_service.py` for full details.

## Generic Validation Framework

A reusable validation framework is provided in `services/validation_framework.py`. This framework allows you to define field-level, model-level, and warning-level validators for any Pydantic model, and aggregate errors and warnings in a consistent way.

### Usage Example

```python
from pydantic import BaseModel
from services.validation_framework import Validator

class MyModel(BaseModel):
    name: str
    age: int

validator = Validator()
validator.add_field_validator('age', lambda v: "Must be >= 0" if v < 0 else None)
validator.add_model_validator(lambda m: "Name cannot be empty" if not m.name else None)

m = MyModel(name="", age=-1)
result = validator.validate(m)
print(result.is_valid, result.errors)
```

You can reuse the same validator for multiple models, or create specialized validators for each model type. See the code in `services/validation_framework.py` for details.

## Centralized Response Helpers

A comprehensive response helper package is provided in `utils/` for standardized API responses across the entire Arxos platform.

### Key Features

- **Standardized Response Format** - Consistent JSON structure for all API responses
- **Error Handling** - Centralized exception handling with automatic logging
- **Response Types** - Specialized helpers for common operations (success, error, list, created, updated, deleted)
- **Pagination Support** - Built-in pagination for list responses
- **Error Codes** - Standardized error codes across the platform
- **Logging Integration** - Automatic error logging with context

### Quick Usage

```python
from utils.response_helpers import success_response, error_response
from utils.error_handlers import handle_exception

# Success response
return success_response(
    data={"user_id": "123", "name": "John Doe"},
    message="User created successfully"
)

# Error response
return error_response(
    message="User not found",
    error_code="USER_NOT_FOUND",
    status_code=404
)

# Exception handling
try:
    # Your code here
    pass
except Exception as e:
    return handle_exception(e)
```

### Available Response Types

- `success_response()` - Standard success responses
- `error_response()` - Standard error responses
- `list_response()` - Paginated list responses
- `created_response()` - Resource creation (201)
- `updated_response()` - Resource updates
- `deleted_response()` - Resource deletion
- `validation_error_response()` - Validation errors (422)
- `not_found_response()` - Not found errors (404)
- `unauthorized_response()` - Authentication errors (401)
- `forbidden_response()` - Permission errors (403)
- `server_error_response()` - Server errors (500)

See `utils/README.md` for comprehensive documentation and examples.
