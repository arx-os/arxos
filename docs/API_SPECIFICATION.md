# Arxos Platform API Specification

## Overview

The Arxos Platform provides a comprehensive RESTful API for building management operations. This API follows RESTful principles, uses JSON for data exchange, and includes comprehensive error handling and security features.

## Base URL

```
Production: https://api.arxos.com/v1
Staging: https://staging-api.arxos.com/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### JWT Bearer Token Authentication

All API endpoints require authentication using JWT Bearer tokens.

```http
Authorization: Bearer <your-jwt-token>
```

### Authentication Endpoints

#### POST /auth/login
Authenticate user and receive access tokens.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "securePassword123!",
  "client_info": {
    "user_agent": "Arxos-Web/1.0",
    "ip_address": "192.168.1.1"
  }
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "user@example.com",
    "roles": ["manager"],
    "permissions": ["read_building", "create_building"]
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### POST /auth/logout
Logout user and invalidate tokens.

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Buildings API

### GET /buildings
Retrieve list of buildings with pagination and filtering.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 50, max: 200)
- `status` (string): Filter by building status
- `search` (string): Search by name or address
- `created_after` (datetime): Filter by creation date
- `sort_by` (string): Sort field (name, created_at, updated_at)
- `sort_order` (string): Sort direction (asc, desc)

**Example Request:**
```http
GET /buildings?page=1&page_size=20&status=operational&search=downtown&sort_by=name&sort_order=asc
```

**Response:**
```json
{
  "success": true,
  "data": {
    "buildings": [
      {
        "id": "building_123",
        "name": "Downtown Office Complex",
        "address": {
          "street": "123 Main Street",
          "city": "New York",
          "state": "NY",
          "postal_code": "10001",
          "country": "USA"
        },
        "status": "operational",
        "description": "Modern office complex in downtown area",
        "coordinates": {
          "latitude": 40.7128,
          "longitude": -74.0060,
          "elevation": 10.0
        },
        "dimensions": {
          "width": 50.0,
          "length": 80.0,
          "height": 120.0,
          "unit": "meters"
        },
        "floors_count": 25,
        "rooms_count": 500,
        "devices_count": 150,
        "created_at": "2023-01-15T10:30:00Z",
        "updated_at": "2023-08-20T14:22:00Z",
        "created_by": "admin_001",
        "metadata": {
          "building_type": "commercial",
          "year_built": 2020,
          "certifications": ["LEED Gold", "Energy Star"]
        }
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### POST /buildings
Create a new building.

**Request:**
```json
{
  "name": "New Office Building",
  "address": {
    "street": "456 Business Ave",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "USA"
  },
  "description": "State-of-the-art office building",
  "coordinates": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "elevation": 15.0
  },
  "dimensions": {
    "width": 40.0,
    "length": 60.0,
    "height": 100.0,
    "unit": "meters"
  },
  "metadata": {
    "building_type": "commercial",
    "year_built": 2024,
    "expected_completion": "2024-12-31"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "building_id": "building_456",
    "message": "Building created successfully"
  },
  "building": {
    "id": "building_456",
    "name": "New Office Building",
    "status": "planned",
    "created_at": "2024-01-15T09:30:00Z"
  }
}
```

### GET /buildings/{building_id}
Retrieve specific building details.

**Path Parameters:**
- `building_id` (string, required): Building identifier

**Query Parameters:**
- `include_floors` (boolean): Include floors data (default: false)
- `include_rooms` (boolean): Include rooms data (default: false)
- `include_devices` (boolean): Include devices data (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "building": {
      "id": "building_123",
      "name": "Downtown Office Complex",
      "address": {
        "street": "123 Main Street",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA"
      },
      "status": "operational",
      "description": "Modern office complex",
      "coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "elevation": 10.0
      },
      "dimensions": {
        "width": 50.0,
        "length": 80.0,
        "height": 120.0,
        "unit": "meters"
      },
      "area": 4000.0,
      "volume": 480000.0,
      "floors": [
        {
          "id": "floor_001",
          "name": "Ground Floor",
          "floor_number": 0,
          "area": 800.0
        }
      ],
      "created_at": "2023-01-15T10:30:00Z",
      "updated_at": "2023-08-20T14:22:00Z"
    }
  }
}
```

### PUT /buildings/{building_id}
Update building information.

**Request:**
```json
{
  "name": "Updated Building Name",
  "description": "Updated description",
  "metadata": {
    "renovation_year": 2024,
    "certifications": ["LEED Platinum"]
  }
}
```

### PUT /buildings/{building_id}/status
Update building status.

**Request:**
```json
{
  "status": "under_construction",
  "reason": "Starting renovation project",
  "updated_by": "manager_001"
}
```

### DELETE /buildings/{building_id}
Delete a building (soft delete with audit trail).

**Query Parameters:**
- `force` (boolean): Permanent deletion (admin only, default: false)
- `cascade` (boolean): Delete related floors/rooms/devices (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Building deleted successfully",
    "deleted_at": "2024-01-15T16:45:00Z"
  }
}
```

## Floors API

### GET /buildings/{building_id}/floors
Retrieve floors for a specific building.

**Response:**
```json
{
  "success": true,
  "data": {
    "floors": [
      {
        "id": "floor_001",
        "building_id": "building_123",
        "name": "Ground Floor",
        "floor_number": 0,
        "description": "Main entrance and lobby",
        "area": 800.0,
        "status": "operational",
        "rooms_count": 15,
        "devices_count": 25,
        "created_at": "2023-01-15T11:00:00Z"
      }
    ]
  }
}
```

### POST /buildings/{building_id}/floors
Create a new floor in a building.

**Request:**
```json
{
  "name": "Executive Floor",
  "floor_number": 20,
  "description": "Executive offices and conference rooms",
  "area": 750.0,
  "metadata": {
    "access_level": "restricted",
    "security_clearance": "executive"
  }
}
```

### GET /floors/{floor_id}
Retrieve specific floor details.

### PUT /floors/{floor_id}
Update floor information.

### DELETE /floors/{floor_id}
Delete a floor.

## Rooms API

### GET /floors/{floor_id}/rooms
Retrieve rooms for a specific floor.

**Response:**
```json
{
  "success": true,
  "data": {
    "rooms": [
      {
        "id": "room_001",
        "floor_id": "floor_001",
        "name": "Conference Room A",
        "room_number": "101A",
        "room_type": "conference",
        "area": 25.0,
        "capacity": 12,
        "status": "available",
        "amenities": ["projector", "whiteboard", "video_conference"],
        "devices_count": 8,
        "created_at": "2023-01-15T12:00:00Z"
      }
    ]
  }
}
```

### POST /floors/{floor_id}/rooms
Create a new room in a floor.

**Request:**
```json
{
  "name": "Meeting Room B",
  "room_number": "205B",
  "room_type": "meeting",
  "area": 20.0,
  "capacity": 8,
  "amenities": ["projector", "whiteboard"],
  "metadata": {
    "booking_enabled": true,
    "max_booking_hours": 4
  }
}
```

## Devices API

### GET /rooms/{room_id}/devices
Retrieve devices for a specific room.

**Response:**
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "id": "device_001",
        "room_id": "room_001",
        "name": "Temperature Sensor",
        "device_id": "TEMP_001",
        "device_type": "sensor",
        "manufacturer": "SensorTech",
        "model": "ST-TEMP-v2",
        "status": "operational",
        "last_reading": {
          "temperature": 22.5,
          "humidity": 45.0,
          "timestamp": "2024-01-15T16:30:00Z"
        },
        "installed_at": "2023-01-15T14:00:00Z",
        "last_maintenance": "2023-12-01T10:00:00Z"
      }
    ]
  }
}
```

### POST /rooms/{room_id}/devices
Install a new device in a room.

**Request:**
```json
{
  "name": "Smart Thermostat",
  "device_id": "THERMO_001",
  "device_type": "hvac",
  "manufacturer": "SmartHome",
  "model": "SH-THERMO-Pro",
  "configuration": {
    "target_temperature": 22.0,
    "schedule_enabled": true,
    "remote_access": true
  }
}
```

## Users API

### GET /users
Retrieve users (admin/manager access required).

### POST /users
Create a new user.

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1-555-0123",
  "roles": ["operator"],
  "metadata": {
    "department": "facilities",
    "employee_id": "EMP001"
  }
}
```

### GET /users/{user_id}
Retrieve specific user details.

### PUT /users/{user_id}
Update user information.

### PUT /users/{user_id}/roles
Update user roles (admin access required).

**Request:**
```json
{
  "roles": ["manager", "operator"],
  "updated_by": "admin_001",
  "reason": "Promotion to management role"
}
```

## Search API

### GET /search
Global search across all entities.

**Query Parameters:**
- `q` (string, required): Search query
- `types` (array): Entity types to search (buildings, floors, rooms, devices, users)
- `limit` (integer): Maximum results per type (default: 10)
- `include_metadata` (boolean): Include metadata in results

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "downtown office",
    "results": {
      "buildings": [
        {
          "id": "building_123",
          "name": "Downtown Office Complex",
          "type": "building",
          "score": 0.95,
          "highlight": "Downtown Office Complex"
        }
      ],
      "rooms": [
        {
          "id": "room_456",
          "name": "Downtown Conference Room",
          "type": "room",
          "score": 0.82,
          "building_name": "Downtown Office Complex"
        }
      ]
    },
    "total_results": 15,
    "execution_time_ms": 45
  }
}
```

## Analytics API

### GET /analytics/dashboard
Retrieve dashboard metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_buildings": 25,
      "total_floors": 180,
      "total_rooms": 2500,
      "total_devices": 8750,
      "operational_buildings": 23,
      "maintenance_buildings": 2
    },
    "occupancy": {
      "current_occupancy_rate": 78.5,
      "peak_hours": ["09:00-11:00", "14:00-16:00"],
      "low_occupancy_rooms": 45
    },
    "device_health": {
      "operational_devices": 8450,
      "maintenance_required": 125,
      "offline_devices": 175,
      "health_score": 96.5
    },
    "energy_usage": {
      "current_month_kwh": 125000,
      "previous_month_kwh": 132000,
      "efficiency_improvement": 5.3,
      "top_consumers": ["HVAC", "Lighting", "Equipment"]
    }
  }
}
```

## Reporting API

### GET /reports/buildings
Generate building reports.

**Query Parameters:**
- `format` (string): Report format (json, csv, pdf)
- `date_range` (string): Date range filter
- `include_details` (boolean): Include detailed information

### POST /reports/custom
Create custom report.

**Request:**
```json
{
  "report_name": "Monthly Occupancy Report",
  "entities": ["buildings", "rooms"],
  "filters": {
    "building_status": ["operational"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "metrics": ["occupancy_rate", "device_health", "energy_usage"],
  "format": "pdf",
  "schedule": {
    "frequency": "monthly",
    "delivery_email": "manager@example.com"
  }
}
```

## Webhooks API

### POST /webhooks
Register webhook endpoint.

**Request:**
```json
{
  "url": "https://your-app.com/webhooks/arxos",
  "events": ["building.created", "device.status_changed", "room.occupied"],
  "secret": "your-webhook-secret",
  "active": true,
  "metadata": {
    "app_name": "Facility Management System"
  }
}
```

### Webhook Event Format

**Building Created Event:**
```json
{
  "event_type": "building.created",
  "event_id": "evt_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "building": {
      "id": "building_123",
      "name": "New Office Building",
      "status": "planned"
    },
    "created_by": "admin_001"
  },
  "signature": "sha256=abc123def456..."
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field_errors": {
        "name": ["Building name is required"],
        "address.postal_code": ["Invalid postal code format"]
      }
    },
    "request_id": "req_123456789",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### HTTP Status Codes

- `200 OK`: Successful GET requests
- `201 Created`: Successful POST requests that create resources
- `204 No Content`: Successful DELETE requests
- `400 Bad Request`: Invalid request data or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflicts (duplicate names, etc.)
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side errors

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: Missing authentication token
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `VALIDATION_ERROR`: Input validation failed
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `RESOURCE_CONFLICT`: Resource conflicts with existing data
- `RATE_LIMIT_EXCEEDED`: Too many requests in time window
- `INTERNAL_ERROR`: Unexpected server error

## Rate Limiting

### Rate Limit Headers

All API responses include rate limiting headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Rate Limits by User Role

- **Guest**: 100 requests/hour
- **User**: 1,000 requests/hour
- **Manager**: 5,000 requests/hour
- **Admin**: 10,000 requests/hour

## Pagination

### Query Parameters

- `page`: Page number (1-based, default: 1)
- `page_size`: Items per page (default: 50, max: 200)

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 1500,
    "total_pages": 30,
    "has_next": true,
    "has_prev": false,
    "next_url": "/api/v1/buildings?page=2&page_size=50",
    "prev_url": null
  }
}
```

## API Versioning

### URL Versioning

Current API version: `v1`

```http
GET /api/v1/buildings
```

### Version Support

- `v1`: Current stable version
- `v2`: Future version (planned)

### Deprecation Policy

- New versions are backward compatible for at least 12 months
- Deprecated endpoints return `X-API-Deprecated` header
- Breaking changes require major version increment

## Security Considerations

### HTTPS Only
All API communications must use HTTPS in production.

### Input Validation
All inputs are validated and sanitized to prevent injection attacks.

### CORS Policy
Cross-Origin Resource Sharing (CORS) is configured for web applications.

```http
Access-Control-Allow-Origin: https://app.arxos.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

### Content Security
- Request/response size limits: 10MB
- Request timeout: 30 seconds
- File upload limits: 50MB per file

## SDK and Client Libraries

### Official SDKs
- **Python**: `pip install arxos-python-sdk`
- **JavaScript/TypeScript**: `npm install arxos-js-sdk`
- **Go**: `go get github.com/arxos/go-sdk`

### Example Usage (Python)

```python
from arxos_sdk import ArxosClient

client = ArxosClient(
    base_url="https://api.arxos.com/v1",
    api_token="your-api-token"
)

# Create building
building = client.buildings.create({
    "name": "New Office Building",
    "address": {
        "street": "123 Business Ave",
        "city": "San Francisco",
        "state": "CA"
    }
})

# List buildings
buildings = client.buildings.list(page=1, page_size=20)

# Get building details
building_details = client.buildings.get(building.id)
```

This API specification provides comprehensive coverage of the Arxos Platform's capabilities while maintaining consistency, security, and ease of use for developers.