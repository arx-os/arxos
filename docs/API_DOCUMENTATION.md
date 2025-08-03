
# Arxos API Documentation

## Overview
The Arxos platform provides a comprehensive API for building information modeling and CAD operations.

## Authentication
All API endpoints require authentication using JWT tokens.

### Headers
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

## Endpoints

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
