# AR API Specification

## Overview

This document defines the API endpoints and data contracts for the Arxos Mobile AR application integration with the backend server.

## Base Configuration

- **Base URL**: `https://api.arxos.io/api/v1`
- **Authentication**: Bearer token (JWT)
- **Content Type**: `application/json`
- **API Version**: v1

## Authentication

The AR mobile app uses the existing authentication endpoints with extended session management for mobile devices.

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "device_info": {
    "platform": "ios",
    "device_id": "UUID",
    "app_version": "1.0.0"
  }
}

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

## AR-Specific Endpoints

### 1. Spatial Anchors

#### List Building Anchors
Retrieve all spatial anchors for a specific building.

```http
GET /api/v1/ar/buildings/{building_id}/anchors
Authorization: Bearer {token}

Query Parameters:
- floor_id (optional): Filter by specific floor
- room_id (optional): Filter by specific room
- platform (optional): Filter by platform (ios/android)

Response: 200 OK
{
  "anchors": [
    {
      "id": "anchor_abc123",
      "equipment_id": "equip_def456",
      "building_id": "build_789",
      "floor_id": "floor_1",
      "room_id": "room_101",
      "platform": "ios",
      "anchor_data": "base64_encoded_platform_specific_data",
      "position": {
        "x": 1.5,
        "y": 0.0,
        "z": -2.0
      },
      "rotation": {
        "x": 0.0,
        "y": 45.0,
        "z": 0.0
      },
      "scale": {
        "x": 1.0,
        "y": 1.0,
        "z": 1.0
      },
      "metadata": {
        "confidence": 0.95,
        "tracking_state": "normal"
      },
      "created_at": "2024-09-12T10:00:00Z",
      "updated_at": "2024-09-12T10:00:00Z",
      "created_by": "user_123"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 50
}
```

#### Create Anchor
Save a new spatial anchor for equipment placement.

```http
POST /api/v1/ar/anchors
Authorization: Bearer {token}
Content-Type: application/json

{
  "equipment_id": "equip_def456",
  "building_id": "build_789",
  "floor_id": "floor_1",
  "room_id": "room_101",
  "platform": "ios",
  "anchor_data": "base64_encoded_platform_specific_data",
  "position": {
    "x": 1.5,
    "y": 0.0,
    "z": -2.0
  },
  "rotation": {
    "x": 0.0,
    "y": 45.0,
    "z": 0.0
  },
  "scale": {
    "x": 1.0,
    "y": 1.0,
    "z": 1.0
  },
  "metadata": {
    "confidence": 0.95,
    "tracking_state": "normal",
    "environment_texture": "base64_encoded_texture"
  }
}

Response: 201 Created
{
  "anchor": {
    "id": "anchor_new123",
    ...
  }
}
```

#### Update Anchor
Update an existing spatial anchor (e.g., after refinement).

```http
PUT /api/v1/ar/anchors/{anchor_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "position": {
    "x": 1.6,
    "y": 0.0,
    "z": -2.1
  },
  "metadata": {
    "confidence": 0.98,
    "last_refined": "2024-09-12T11:00:00Z"
  }
}

Response: 200 OK
{
  "anchor": {
    "id": "anchor_abc123",
    ...
  }
}
```

#### Delete Anchor
Remove a spatial anchor.

```http
DELETE /api/v1/ar/anchors/{anchor_id}
Authorization: Bearer {token}

Response: 204 No Content
```

### 2. AR Equipment Operations

#### Get Nearby Equipment
Retrieve equipment near a GPS location or within AR session bounds.

```http
GET /api/v1/ar/equipment/nearby
Authorization: Bearer {token}

Query Parameters:
- lat: Latitude
- lng: Longitude  
- radius: Search radius in meters (default: 50)
- building_id: Limit to specific building

Response: 200 OK
{
  "equipment": [
    {
      "id": "equip_123",
      "name": "HVAC Unit 3",
      "type": "hvac",
      "distance_meters": 5.2,
      "direction_degrees": 45,
      "floor": "2nd Floor",
      "room": "Room 201",
      "has_anchor": true,
      "anchor_id": "anchor_abc123",
      "status": "normal"
    }
  ]
}
```

#### Create Equipment with AR
Create new equipment with spatial anchor in one request.

```http
POST /api/v1/ar/equipment
Authorization: Bearer {token}
Content-Type: application/json

{
  "equipment": {
    "name": "New HVAC Unit",
    "type": "hvac",
    "building_id": "build_789",
    "floor_id": "floor_2",
    "room_id": "room_201",
    "manufacturer": "Carrier",
    "model": "Infinity 19VS",
    "serial_number": "CAR789456",
    "status": "normal"
  },
  "anchor": {
    "platform": "ios",
    "anchor_data": "base64_encoded_data",
    "position": {
      "x": 2.0,
      "y": 0.5,
      "z": -3.0
    }
  }
}

Response: 201 Created
{
  "equipment": {
    "id": "equip_new456",
    ...
  },
  "anchor": {
    "id": "anchor_new789",
    ...
  }
}
```

### 3. AR Session Management

#### Start AR Session
Register an AR session for analytics and multi-user coordination.

```http
POST /api/v1/ar/sessions
Authorization: Bearer {token}
Content-Type: application/json

{
  "building_id": "build_789",
  "floor_id": "floor_1",
  "platform": "ios",
  "device_info": {
    "model": "iPhone 14 Pro",
    "os_version": "17.0",
    "ar_capabilities": ["lidar", "depth_api", "object_occlusion"]
  }
}

Response: 201 Created
{
  "session": {
    "id": "session_xyz",
    "token": "session_token_abc",
    "expires_at": "2024-09-12T12:00:00Z",
    "websocket_url": "wss://api.arxos.io/ar/sessions/session_xyz"
  }
}
```

#### End AR Session
Close an AR session and save analytics.

```http
POST /api/v1/ar/sessions/{session_id}/end
Authorization: Bearer {token}
Content-Type: application/json

{
  "duration_seconds": 300,
  "equipment_viewed": 15,
  "equipment_added": 2,
  "equipment_updated": 5,
  "anchors_created": 2
}

Response: 200 OK
{
  "session_summary": {
    "id": "session_xyz",
    "duration": 300,
    "actions": {
      "viewed": 15,
      "added": 2,
      "updated": 5
    }
  }
}
```

### 4. AR Cloud Sync

#### Upload AR World Map
Upload AR world mapping data for persistent cloud anchors.

```http
POST /api/v1/ar/worldmaps
Authorization: Bearer {token}
Content-Type: multipart/form-data

Form Data:
- building_id: "build_789"
- floor_id: "floor_1"
- platform: "ios"
- worldmap_data: [binary file]
- thumbnail: [image file]

Response: 201 Created
{
  "worldmap": {
    "id": "worldmap_123",
    "building_id": "build_789",
    "floor_id": "floor_1",
    "size_bytes": 1048576,
    "thumbnail_url": "https://storage.arxos.io/worldmaps/thumb_123.jpg",
    "created_at": "2024-09-12T10:00:00Z"
  }
}
```

#### Download AR World Map
Retrieve AR world mapping data for relocalization.

```http
GET /api/v1/ar/worldmaps/{worldmap_id}
Authorization: Bearer {token}

Response: 200 OK
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="worldmap_123.arworldmap"

[Binary worldmap data]
```

### 5. AR Analytics

#### Get AR Usage Statistics
Retrieve AR feature usage analytics.

```http
GET /api/v1/ar/analytics
Authorization: Bearer {token}

Query Parameters:
- building_id: Filter by building
- start_date: Start of date range (ISO 8601)
- end_date: End of date range (ISO 8601)
- group_by: day|week|month

Response: 200 OK
{
  "analytics": {
    "period": {
      "start": "2024-09-01T00:00:00Z",
      "end": "2024-09-30T23:59:59Z"
    },
    "sessions": {
      "total": 150,
      "average_duration_seconds": 240,
      "unique_users": 25
    },
    "equipment": {
      "viewed": 500,
      "added": 50,
      "updated": 200
    },
    "anchors": {
      "created": 75,
      "updated": 30,
      "deleted": 5
    },
    "platforms": {
      "ios": 100,
      "android": 50
    }
  }
}
```

## WebSocket Events

For real-time AR collaboration, the mobile app can connect to a WebSocket endpoint.

### Connection
```javascript
const ws = new WebSocket('wss://api.arxos.io/ar/sessions/{session_id}?token={session_token}');
```

### Event Types

#### Equipment Updated
```json
{
  "type": "equipment_updated",
  "data": {
    "equipment_id": "equip_123",
    "updated_by": "user_456",
    "changes": {
      "status": "failed",
      "notes": "Motor failure detected"
    }
  }
}
```

#### Anchor Added
```json
{
  "type": "anchor_added",
  "data": {
    "anchor_id": "anchor_new",
    "equipment_id": "equip_789",
    "added_by": "user_456",
    "position": {
      "x": 1.0,
      "y": 0.0,
      "z": -1.0
    }
  }
}
```

#### User Joined Session
```json
{
  "type": "user_joined",
  "data": {
    "user_id": "user_789",
    "name": "Jane Smith",
    "platform": "android"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "INVALID_ANCHOR_DATA",
    "message": "The provided anchor data is invalid or corrupted",
    "details": {
      "field": "anchor_data",
      "reason": "Base64 decoding failed"
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2024-09-12T10:00:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_ANCHOR_DATA` | 400 | Anchor data is corrupted or invalid |
| `PLATFORM_MISMATCH` | 400 | Anchor platform doesn't match device |
| `ANCHOR_LIMIT_EXCEEDED` | 429 | Too many anchors for building |
| `SESSION_EXPIRED` | 410 | AR session has expired |
| `WORLDMAP_TOO_LARGE` | 413 | World map exceeds size limit |

## Rate Limiting

- **Default Rate Limit**: 100 requests per minute per user
- **Anchor Creation**: 10 per minute per user
- **World Map Upload**: 1 per 5 minutes per user
- **Session Creation**: 5 per hour per user

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1694512800
```

## Pagination

List endpoints support pagination:

```http
GET /api/v1/ar/buildings/{building_id}/anchors?page=2&per_page=25

Response Headers:
X-Total-Count: 150
X-Page: 2
X-Per-Page: 25
Link: <.../anchors?page=3&per_page=25>; rel="next",
      <.../anchors?page=1&per_page=25>; rel="prev"
```

## Versioning

API version is specified in the URL path. When breaking changes are introduced, a new version will be created.

Current version: `v1`
Future versions: `v2`, `v3`, etc.

Deprecated endpoints will include a deprecation header:
```
Deprecation: true
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Link: <https://docs.arxos.io/api/migrations>; rel="deprecation"
```