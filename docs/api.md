# ArxOS API Documentation

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

ArxOS uses JWT bearer tokens for authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /auth/login
Authenticate user and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "abc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### POST /auth/logout
Invalidate the current session.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "abc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "abc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "full_name": "John Doe",
    "role": "viewer"
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "abc...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

### Buildings

#### GET /buildings
List all buildings accessible to the user.

**Query Parameters:**
- `limit` (optional): Maximum number of results (default: 100, max: 1000)
- `offset` (optional): Number of results to skip for pagination

**Response:**
```json
{
  "buildings": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "arxos_id": "MAIN-OFFICE",
      "name": "Main Office Building",
      "address": "123 Main St",
      "origin": {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "altitude": 0
      },
      "rotation": 0,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

#### POST /buildings/create
Create a new building.

**Request:**
```json
{
  "arxos_id": "NEW-BUILDING",
  "name": "New Building",
  "address": "456 New St",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "rotation": 0
}
```

**Response:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "arxos_id": "NEW-BUILDING",
  "name": "New Building",
  "address": "456 New St",
  "origin": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 0
  },
  "rotation": 0,
  "created_at": "2024-01-02T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

#### GET /buildings/{id}
Get a specific building by ID.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "arxos_id": "MAIN-OFFICE",
  "name": "Main Office Building",
  "address": "123 Main St",
  "origin": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 0
  },
  "rotation": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /buildings/{id}
Update a building.

**Request:**
```json
{
  "name": "Updated Building Name",
  "address": "789 Updated St",
  "latitude": 37.7750,
  "longitude": -122.4195,
  "rotation": 45
}
```

#### DELETE /buildings/{id}
Delete a building.

**Response:**
```json
{
  "success": true,
  "message": "Building deleted successfully"
}
```

### Equipment

#### GET /equipment
List equipment in a building.

**Query Parameters:**
- `building_id` (required): Building UUID
- `status` (optional): Filter by status (operational, degraded, failed, offline, maintenance, unknown)
- `type` (optional): Filter by equipment type
- `limit` (optional): Maximum number of results
- `offset` (optional): Number of results to skip

**Response:**
```json
{
  "equipment": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "building_id": "550e8400-e29b-41d4-a716-446655440000",
      "path": "1/101/OUTLET-001",
      "name": "Main Outlet",
      "type": "electrical.outlet",
      "status": "operational",
      "position": {
        "longitude": -122.4194,
        "latitude": 37.7749,
        "altitude": 10.5
      },
      "confidence": 2,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

#### POST /equipment/create
Create new equipment.

**Request:**
```json
{
  "building_id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "1/102/SWITCH-001",
  "name": "Light Switch",
  "type": "electrical.switch",
  "status": "operational",
  "position": {
    "longitude": -122.4194,
    "latitude": 37.7749,
    "altitude": 11.0
  }
}
```

#### GET /equipment/{id}
Get specific equipment by ID.

#### PUT /equipment/{id}
Update equipment.

**Request:**
```json
{
  "name": "Updated Equipment Name",
  "status": "maintenance",
  "position": {
    "longitude": -122.4195,
    "latitude": 37.7750,
    "altitude": 11.5
  }
}
```

#### DELETE /equipment/{id}
Delete equipment.

### Spatial Queries

#### GET /spatial/nearby
Find equipment near a location.

**Query Parameters:**
- `lat` (required): Latitude
- `lon` (required): Longitude
- `radius` (required): Radius in meters

**Response:**
```json
{
  "equipment": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "path": "1/101/OUTLET-001",
      "name": "Main Outlet",
      "distance_meters": 5.2,
      "building_name": "Main Office"
    }
  ]
}
```

#### GET /spatial/within
Find equipment within bounds.

**Query Parameters:**
- `bounds` (required): Comma-separated minLon,minLat,maxLon,maxLat

#### GET /spatial/floor
Find equipment on a specific floor.

**Query Parameters:**
- `building` (required): Building ID
- `floor` (required): Floor number

### Users

#### GET /users/me
Get current user profile.

**Response:**
```json
{
  "id": "850e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "technician",
  "status": "active",
  "last_login": "2024-01-02T12:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /users
List all users (admin/manager only).

**Query Parameters:**
- `limit` (optional): Maximum number of results
- `offset` (optional): Number of results to skip

#### GET /users/{id}
Get specific user by ID.

#### PUT /users/{id}
Update user profile.

**Request:**
```json
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "role": "manager",
  "status": "active"
}
```

#### POST /users/{id}/password
Change user password.

**Request:**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

### File Upload

#### POST /upload/pdf
Upload a PDF floor plan for processing.

**Request:**
- Content-Type: multipart/form-data
- Field: `file` (PDF file)
- Field: `building_id` (Building UUID)

**Response:**
```json
{
  "upload_id": "abc123",
  "status": "processing",
  "message": "PDF upload received and is being processed"
}
```

#### GET /upload/progress
Check upload processing progress.

**Query Parameters:**
- `upload_id` (required): Upload ID from upload response

**Response:**
```json
{
  "id": "abc123",
  "file_name": "floor_plan.pdf",
  "file_size": 2048000,
  "uploaded": 2048000,
  "status": "completed",
  "started_at": "2024-01-02T12:00:00Z",
  "completed_at": "2024-01-02T12:01:00Z"
}
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message",
  "code": "400"
}
```

Common HTTP status codes:
- `200 OK`: Request successful
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `500 Internal Server Error`: Server error

## Rate Limiting

API requests are rate-limited to 100 requests per minute per client by default. Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704201600
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```http
GET /api/v1/buildings?limit=20&offset=40
```

This retrieves 20 buildings starting from the 41st result.

## Filtering

Many endpoints support filtering via query parameters:

```http
GET /api/v1/equipment?building_id=xxx&status=failed&type=electrical
```

## Sorting

List endpoints typically return results sorted by creation date (newest first) unless otherwise specified.