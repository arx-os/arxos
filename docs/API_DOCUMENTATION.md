
# Arxos API Documentation

## Overview
The Arxos platform provides a comprehensive API for building information modeling and CAD operations.

## Authentication
All API endpoints require authentication using JWT tokens signed with HS256. Tokens must be sent in the `Authorization` header. Expired or malformed tokens return 401; insufficient permissions return 403.

### Headers
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

## Endpoints

### Unified Building API

The platform provides a unified Building API exposed under `/api/v1/buildings`.
Unified routes are enabled by default and can be disabled via configuration `features.use_unified_api=false`. When disabled, the legacy routes are used. All endpoints require a valid JWT.

- POST `/api/v1/buildings/` — Create a building
- GET `/api/v1/buildings/` — List buildings with filters and pagination
- GET `/api/v1/buildings/{building_id}` — Retrieve building details
- PUT `/api/v1/buildings/{building_id}` — Update building
- DELETE `/api/v1/buildings/{building_id}` — Delete building

Example (create):
```bash
curl -X POST "http://localhost:8000/api/v1/buildings/" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Tower",
       "building_type": "commercial",
       "status": "active",
       "address": {"street": "1 Test Way", "city": "Testville", "state": "TS", "postal_code": "00000", "country": "USA"}
     }'
```

### AI Conversion Service

#### PDF to ArxObject Conversion
- `POST /api/v1/buildings/convert` - Convert PDF to ArxObjects with AI
- `GET /api/v1/buildings/{building_id}/conversion-status` - Get conversion status
- `GET /api/v1/buildings/{building_id}/arxobjects` - Get building ArxObjects with filtering
- `POST /api/v1/buildings/{building_id}/arxobjects/batch` - Batch create ArxObjects

#### Validation & Confidence
- `POST /api/v1/arxobjects/{id}/validate` - Submit field validation
- `GET /api/v1/arxobjects/{id}/confidence` - Get confidence scores
- `POST /api/v1/buildings/{building_id}/validation-strategy` - Generate validation strategy
- `GET /api/v1/buildings/{building_id}/uncertainties` - Get critical uncertainties
- `POST /api/v1/validations/propagate` - Propagate validation to similar objects

#### Real-time Updates
- `GET /api/v1/buildings/{building_id}/validation-stream` - SSE stream for validation updates
- `WS /api/v1/buildings/{building_id}/collaborate` - WebSocket for real-time collaboration

### AI Service
- `POST /api/v1/query` - Process AI queries
- `POST /api/v1/geometry/validate` - Validate geometry
- `POST /api/v1/voice/process` - Process voice commands

### GUS Service
- `POST /api/v1/query` - Process GUS queries
- `POST /api/v1/task` - Execute GUS tasks
- `POST /api/v1/knowledge` - Query knowledge base
- `POST /api/v1/pdf_analysis` - Analyze PDF documents

### SVGX Engine
- `GET /api/v1/health` - Health check
- `POST /api/v1/compile` - Compile SVGX code
- `POST /api/v1/validate` - Validate SVGX code

## Error Responses
```json
{
    "error": "Error message",
    "status_code": 400,
    "details": "Additional error details"
}
```

## Rate Limiting
- 100 requests per hour per user
- 1000 requests per day per user

## Examples

### Convert PDF to ArxObjects
```bash
curl -X POST "http://localhost:8000/api/v1/buildings/convert" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: multipart/form-data" \
     -F "pdf=@floor_plan.pdf" \
     -F "building_name=Office Building" \
     -F "building_type=commercial" \
     -F "approximate_size=50000sqft"
```

Response:
```json
{
    "building_id": "bld_123456",
    "arxobjects_created": 1847,
    "overall_confidence": 0.73,
    "validation_strategy": {
        "critical_validations": [
            {
                "id": "val_001",
                "type": "establish_scale",
                "description": "Measure one wall to establish building scale",
                "impact_score": 0.95
            }
        ],
        "high_impact_validations": [...]
    },
    "uncertainties": [
        {
            "object_id": "arx_room_101",
            "confidence": 0.45,
            "reason": "OCR uncertainty on room label"
        }
    ]
}
```

### Submit Field Validation
```bash
curl -X POST "http://localhost:8000/api/v1/arxobjects/arx_wall_001/validate" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
         "validation_type": "dimension_verification",
         "measured_value": 10.5,
         "units": "meters",
         "validator": "field_tech_01",
         "confidence": 0.95
     }'
```

Response:
```json
{
    "object_id": "arx_wall_001",
    "old_confidence": 0.65,
    "new_confidence": 0.90,
    "cascaded_updates": 23,
    "affected_objects": ["arx_wall_002", "arx_room_101"],
    "validation_impact": 0.85
}
```

### Get ArxObjects with Filtering
```bash
curl -X GET "http://localhost:8000/api/v1/buildings/bld_123456/arxobjects?type=wall&min_confidence=0.7" \
     -H "Authorization: Bearer <token>"
```

Response:
```json
{
    "arxobjects": [
        {
            "id": "arx_wall_001",
            "type": "wall",
            "data": {
                "material": "drywall",
                "thickness": 0.15,
                "height": 3.0
            },
            "confidence": {
                "classification": 0.95,
                "position": 0.88,
                "properties": 0.75,
                "relationships": 0.82,
                "overall": 0.85
            },
            "relationships": [...]
        }
    ],
    "total": 234,
    "filtered": 189
}
```

### Stream Validation Updates (SSE)
```bash
curl -X GET "http://localhost:8000/api/v1/buildings/bld_123456/validation-stream" \
     -H "Authorization: Bearer <token>" \
     -H "Accept: text/event-stream"
```

Stream output:
```
data: {"type":"validation_submitted","object_id":"arx_wall_001","confidence_before":0.65}

data: {"type":"confidence_updated","object_id":"arx_wall_001","confidence_after":0.90}

data: {"type":"cascade_update","affected_objects":23,"average_improvement":0.12}
```

### Process AI Query
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
         "query": "Analyze this building design",
         "user_id": "user123",
         "context": {"building_type": "residential"}
     }'
```

### Execute GUS Task
```bash
curl -X POST "http://localhost:8000/api/v1/task" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
         "task": "knowledge_search",
         "parameters": {"topic": "building_codes"},
         "user_id": "user123"
     }'
```
