# ArxOS API Documentation

## Overview

The ArxOS API is a RESTful HTTP API that provides programmatic access to building intelligence data. All API endpoints return JSON and use standard HTTP status codes.

## Base URL

```
Production: https://api.arxos.io
Development: http://localhost:8080
```

## Authentication

ArxOS uses token-based authentication. Obtain tokens via the login endpoint and include them in the `Authorization` header.

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@arxos.io",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "admin",
    "email": "admin@arxos.io",
    "name": "Admin User",
    "role": "admin"
  }
}
```

### Using Tokens

Include the access token in all authenticated requests:

```http
Authorization: Bearer <access_token>
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

## Endpoints

### Buildings

#### List Buildings

```http
GET /api/v1/buildings?page=1&limit=20&sort=name
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `sort` (string): Sort field (name, created, updated)
- `order` (string): Sort order (asc, desc)
- `search` (string): Search term

**Response:**
```json
{
  "data": [
    {
      "id": "bldg_123",
      "name": "Main Office",
      "building": "HQ",
      "level": 1,
      "rooms": [...],
      "equipment": [...],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:45:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

#### Get Building

```http
GET /api/v1/buildings/{id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "bldg_123",
  "name": "Main Office",
  "building": "HQ",
  "level": 1,
  "rooms": [
    {
      "id": "room_1",
      "name": "Conference Room A",
      "bounds": {
        "min_x": 0,
        "min_y": 0,
        "max_x": 10,
        "max_y": 8
      }
    }
  ],
  "equipment": [
    {
      "id": "eq_1",
      "name": "Switch SW-01",
      "type": "switch",
      "status": "normal",
      "location": {"x": 5, "y": 4}
    }
  ]
}
```

#### Create Building

```http
POST /api/v1/buildings
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Building",
  "building": "Building A",
  "level": 2
}
```

#### Update Building

```http
PUT /api/v1/buildings/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "level": 3
}
```

#### Delete Building

```http
DELETE /api/v1/buildings/{id}
Authorization: Bearer <token>
```

### Equipment

#### List Equipment

```http
GET /api/v1/equipment?building_id={id}&type=switch&status=failed
Authorization: Bearer <token>
```

**Query Parameters:**
- `building_id` (string): Filter by building
- `room_id` (string): Filter by room
- `type` (string): Equipment type (switch, outlet, panel, etc.)
- `status` (string): Status (normal, needs-repair, failed)
- `near` (string): Equipment ID for proximity search
- `distance` (float): Distance in meters for proximity search

#### Get Equipment

```http
GET /api/v1/equipment/{id}
Authorization: Bearer <token>
```

#### Create Equipment

```http
POST /api/v1/equipment
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Switch SW-02",
  "type": "switch",
  "building_id": "bldg_123",
  "room_id": "room_1",
  "location": {"x": 5, "y": 4},
  "status": "normal",
  "metadata": {
    "model": "Cisco 2960",
    "serial": "ABC123"
  }
}
```

#### Update Equipment

```http
PATCH /api/v1/equipment/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "failed",
  "notes": "No power, needs replacement"
}
```

#### Delete Equipment

```http
DELETE /api/v1/equipment/{id}
Authorization: Bearer <token>
```

### Connections

#### Create Connection

```http
POST /api/v1/connections
Authorization: Bearer <token>
Content-Type: application/json

{
  "from_equipment_id": "outlet_2b",
  "to_equipment_id": "panel_1",
  "connection_type": "power",
  "metadata": {
    "circuit": "A-12",
    "voltage": "120V"
  }
}
```

#### List Connections

```http
GET /api/v1/connections?equipment_id={id}&type=power
Authorization: Bearer <token>
```

#### Delete Connection

```http
DELETE /api/v1/connections/{id}
Authorization: Bearer <token>
```

### Sync

#### Push Changes

```http
POST /api/v1/sync/push
Authorization: Bearer <token>
Content-Type: application/json

{
  "building_id": "bldg_123",
  "last_sync": "2024-01-20T10:00:00Z",
  "changes": [
    {
      "type": "update",
      "entity": "equipment",
      "entity_id": "eq_1",
      "data": {...},
      "timestamp": "2024-01-20T11:30:00Z"
    }
  ]
}
```

#### Pull Changes

```http
POST /api/v1/sync/pull
Authorization: Bearer <token>
Content-Type: application/json

{
  "building_id": "bldg_123",
  "last_sync": "2024-01-20T10:00:00Z"
}
```

**Response:**
```json
{
  "building_id": "bldg_123",
  "changes": [...],
  "conflicts": [...],
  "last_sync": "2024-01-20T12:00:00Z"
}
```

#### Sync Status

```http
GET /api/v1/sync/status?building_id={id}
Authorization: Bearer <token>
```

### Search

#### Global Search

```http
GET /api/v1/search?q=switch&type=equipment&limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "results": [
    {
      "type": "equipment",
      "id": "sw_1",
      "name": "Switch SW-01",
      "building": "Main Office",
      "relevance": 0.95
    }
  ],
  "total": 15,
  "query": "switch"
}
```

### Analytics

#### Building Statistics

```http
GET /api/v1/analytics/buildings/{id}/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_equipment": 145,
  "equipment_by_type": {
    "switch": 12,
    "outlet": 85,
    "panel": 8
  },
  "equipment_by_status": {
    "normal": 120,
    "needs-repair": 20,
    "failed": 5
  },
  "total_rooms": 25,
  "last_updated": "2024-01-20T14:45:00Z"
}
```

#### Failure Analysis

```http
GET /api/v1/analytics/failures?building_id={id}&period=7d
Authorization: Bearer <token>
```

### Users

#### Get Current User

```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

#### Update Profile

```http
PATCH /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com"
}
```

#### Change Password

```http
POST /api/v1/users/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

## Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `204 No Content` - Request succeeded, no content to return
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Error Responses

```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "email",
    "message": "Invalid email format"
  }
}
```

## Rate Limiting

API requests are limited to:
- **Anonymous**: 60 requests per hour
- **Authenticated**: 1000 requests per hour
- **Enterprise**: Custom limits

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination:

```http
GET /api/v1/buildings?page=2&limit=50
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "meta": {
    "page": 2,
    "per_page": 50,
    "total": 234,
    "total_pages": 5,
    "has_next": true,
    "has_prev": true
  }
}
```

## Filtering

Use query parameters for filtering:

```http
GET /api/v1/equipment?type=switch&status=failed&building_id=123
```

## Sorting

Sort results using the `sort` and `order` parameters:

```http
GET /api/v1/buildings?sort=updated_at&order=desc
```

## Webhooks

Configure webhooks to receive real-time updates:

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["equipment.failed", "building.updated"],
  "secret": "webhook_secret_key"
}
```

## WebSocket Events

Connect to receive real-time updates:

```javascript
const ws = new WebSocket('wss://api.arxos.io/ws');
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_access_token'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

## SDK Examples

### JavaScript/TypeScript

```javascript
import { ArxOS } from '@arxos/sdk';

const client = new ArxOS({
  apiKey: 'your_api_key',
  baseURL: 'https://api.arxos.io'
});

// List buildings
const buildings = await client.buildings.list();

// Update equipment
await client.equipment.update('eq_123', {
  status: 'failed',
  notes: 'Needs replacement'
});
```

### Python

```python
from arxos import Client

client = Client(api_key="your_api_key")

# List buildings
buildings = client.buildings.list()

# Update equipment
client.equipment.update("eq_123", {
    "status": "failed",
    "notes": "Needs replacement"
})
```

### Go

```go
import "github.com/arxos/arxos-go"

client := arxos.NewClient("your_api_key")

// List buildings
buildings, err := client.Buildings.List(nil)

// Update equipment
err := client.Equipment.Update("eq_123", &arxos.EquipmentUpdate{
    Status: "failed",
    Notes:  "Needs replacement",
})
```

## Postman Collection

Download our [Postman Collection](https://api.arxos.io/postman) for easy API testing.

## OpenAPI Specification

Access the OpenAPI 3.0 specification at:
```
https://api.arxos.io/openapi.json
```

## Support

- **Documentation**: https://docs.arxos.io
- **Status Page**: https://status.arxos.io
- **Support Email**: support@arxos.io
- **GitHub Issues**: https://github.com/arxos/arxos/issues