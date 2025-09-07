# ArxOS API Documentation

## Overview

The ArxOS API provides comprehensive access to building data, real-time events, and market operations. All endpoints support JSON and use standard HTTP methods.

## Base URL

```
http://localhost:3000
```

## Authentication

Currently uses API key authentication. Include the key in the header:

```http
X-API-Key: your-api-key
```

## Response Format

All responses follow this structure:

```json
{
  "data": { ... },      // For successful responses
  "error": {            // For error responses
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

## HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Core Endpoints

### Building Objects

#### List Objects
```http
GET /api/objects?path=/electrical&type=outlet&needs_repair=true
```

Query Parameters:
- `path` - Filter by path prefix
- `type` - Filter by object type
- `needs_repair` - Filter by repair status
- `status` - Filter by status
- `limit` - Maximum results (default: 100)

Response:
```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "path": "/electrical/outlets/outlet_1A",
      "object_type": "outlet",
      "location": {
        "space": "/spaces/floor_1/room_101",
        "x": 10.5,
        "y": 2.3,
        "z": 1.2
      },
      "state": {
        "status": "active",
        "health": "good",
        "needs_repair": false
      },
      "properties": {
        "voltage": 120,
        "amperage": 15
      }
    }
  ]
}
```

#### Create Object
```http
POST /api/objects
Content-Type: application/json

{
  "path": "/electrical/outlets/outlet_new",
  "object_type": "outlet",
  "location_x": 10.5,
  "location_y": 2.3,
  "location_z": 1.2,
  "properties": {
    "voltage": 120,
    "circuit": 15
  }
}
```

#### Update Object
```http
PATCH /api/objects/{id}
Content-Type: application/json

{
  "status": "failed",
  "needs_repair": true,
  "health": 25
}
```

#### Delete Object
```http
DELETE /api/objects/{id}
```

### SQL Query Execution

#### Execute Query
```http
POST /api/query
Content-Type: application/json

{
  "sql": "SELECT * FROM building_objects WHERE needs_repair = true"
}
```

⚠️ **Security Note**: Queries are executed with read-only permissions.

Response:
```json
{
  "data": {
    "columns": ["id", "path", "type", "status"],
    "rows": [
      ["123...", "/electrical/outlet_1", "outlet", "failed"]
    ]
  }
}
```

## BILT Rating System

### Get Building Rating
```http
GET /api/buildings/{building_id}/rating
```

Response:
```json
{
  "data": {
    "building_id": "building-123",
    "current_grade": "0m",
    "numeric_score": 52.5,
    "components": {
      "structure_score": 65.0,
      "inventory_score": 45.0,
      "metadata_score": 55.0,
      "sensors_score": 30.0,
      "history_score": 40.0,
      "quality_score": 70.0,
      "activity_score": 60.0
    },
    "last_updated": "2024-01-15T10:30:00Z",
    "version": 42
  }
}
```

### Get Rating Breakdown
```http
GET /api/buildings/{building_id}/rating/breakdown
```

Returns detailed analysis with recommendations for improvement.

### Get Rating History
```http
GET /api/buildings/{building_id}/rating/history?limit=100
```

Returns chronological rating changes with triggers.

## Market & Token System

### Record Contribution
```http
POST /api/contributions
Content-Type: application/json

{
  "contributor_id": "worker-123",
  "building_id": "building-456",
  "contribution_type": "object_documentation",
  "data_hash": "sha256:abc123...",
  "metadata": {
    "description": "Documented HVAC unit specifications",
    "photos": ["url1", "url2"]
  }
}
```

Response includes token rewards distributed.

### Get Contributor Profile
```http
GET /api/contributors/{contributor_id}/profile
```

Response:
```json
{
  "data": {
    "contributor_id": "worker-123",
    "reputation_score": 450.5,
    "trust_level": "trusted",
    "total_contributions": 234,
    "verified_contributions": 220,
    "badges": [
      {
        "badge_type": "quality_contributor",
        "earned_at": "2024-01-10T15:00:00Z"
      }
    ]
  }
}
```

### Get Token Balance
```http
GET /api/contributors/{contributor_id}/balance
```

### Get Building Token Info
```http
GET /api/tokens/{building_id}
```

Returns BILT token supply, price, and market data.

## Real-time Events (SSE)

### Subscribe to Events
```http
GET /api/events?event_types=object.updated,rating.changed&path_pattern=/electrical
```

Query Parameters:
- `event_types` - Comma-separated event types to filter
- `path_pattern` - Filter by object path prefix
- `building_id` - Filter by building
- `object_type` - Filter by object type

Example client:
```javascript
const eventSource = new EventSource('/api/events?event_types=rating.changed');

eventSource.addEventListener('bilt.rating.changed', (event) => {
    const data = JSON.parse(event.data);
    console.log('Rating changed:', data);
});
```

Event Types:
- `object.created`, `object.updated`, `object.deleted`
- `state.changed`, `metric.recorded`
- `maintenance.scheduled`
- `alert.raised`, `alert.resolved`
- `bilt.rating.changed`, `bilt.rating.calculated`

## Webhook Management

### Create Webhook
```http
POST /api/webhooks
Content-Type: application/json

{
  "name": "Trading System Webhook",
  "url": "https://trading.example.com/webhook",
  "secret": "hmac-secret-key",
  "event_types": ["bilt.rating.changed"],
  "path_pattern": "/electrical",
  "retry_count": 3,
  "timeout_seconds": 30
}
```

### List Webhooks
```http
GET /api/webhooks?active_only=true
```

### Test Webhook
```http
POST /api/webhooks/{id}/test
```

Sends test payload to verify configuration.

### Webhook Security

Webhooks include HMAC signature in header:
```
X-ArxOS-Signature: sha256=<signature>
```

Verify signature:
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Bulk Operations

### Bulk Update
```http
POST /api/bulk/update
Content-Type: application/json

{
  "building_id": "building-123",
  "filter": {
    "path_pattern": "/electrical/circuits",
    "object_type": "outlet"
  },
  "changes": {
    "properties": {
      "maintenance_due": "2024-12-01"
    },
    "merge_json": true
  }
}
```

### Preview Bulk Update
```http
POST /api/bulk/update/preview
```

Same request body, returns affected objects without making changes.

### Get Operation Status
```http
GET /api/bulk/operations/{operation_id}
```

## Health & Monitoring

### Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "database": {
    "status": "healthy",
    "active_connections": 5,
    "response_time_ms": 2
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Readiness Check (Kubernetes)
```http
GET /api/health/ready
```

### Liveness Check (Kubernetes)
```http
GET /api/health/live
```

## Rate Limiting

API requests are rate limited:
- **Default**: 100 requests per minute
- **Bulk operations**: 10 requests per minute
- **Query endpoint**: 20 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642334400
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid building_id format",
    "details": {
      "field": "building_id",
      "expected": "UUID",
      "received": "invalid-id"
    }
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR` - Invalid request parameters
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication failed
- `RATE_LIMITED` - Too many requests
- `DATABASE_ERROR` - Database operation failed
- `INTERNAL_ERROR` - Server error

## Example Integrations

### N8N Workflow
```json
{
  "nodes": [{
    "name": "Get Failed Equipment",
    "type": "n8n-nodes-base.httpRequest",
    "parameters": {
      "method": "GET",
      "url": "http://arxos:3000/api/objects",
      "queryParameters": {
        "needs_repair": "true"
      },
      "headerParameters": {
        "X-API-Key": "{{$credentials.arxos.apiKey}}"
      }
    }
  }]
}
```

### Python Client
```python
import requests
import sseclient

class ArxOSClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {'X-API-Key': api_key}
    
    def list_objects(self, **filters):
        response = requests.get(
            f"{self.base_url}/api/objects",
            params=filters,
            headers=self.headers
        )
        return response.json()
    
    def subscribe_events(self, event_types):
        url = f"{self.base_url}/api/events"
        params = {'event_types': ','.join(event_types)}
        
        response = requests.get(url, params=params, 
                               headers=self.headers, stream=True)
        client = sseclient.SSEClient(response)
        
        for event in client.events():
            yield json.loads(event.data)
```

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
```
GET /api-docs/openapi.json
```

Interactive documentation:
```
GET /docs
```