
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
