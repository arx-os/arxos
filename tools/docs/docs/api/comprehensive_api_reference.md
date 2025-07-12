# Comprehensive API Reference for Arxos Platform

## Overview

The Arxos Platform API provides comprehensive endpoints for version control, route management, floor-specific operations, and advanced building management features. This document covers all API endpoints with detailed examples, error codes, and troubleshooting guides.

**Base URL:** `https://api.arxos.io/v1`

## Table of Contents

1. [Authentication](#authentication)
2. [Version Control API](#version-control-api)
3. [Route Management API](#route-management-api)
4. [Floor Management API](#floor-management-api)
5. [Error Codes and Troubleshooting](#error-codes-and-troubleshooting)
6. [Rate Limiting](#rate-limiting)
7. [Security](#security)

---

## Authentication

### JWT Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### API Key Authentication (Data Vendors)

Data vendor endpoints use API key authentication:

```
X-API-Key: <your-api-key>
```

### Role-Based Access Control

The platform supports the following roles:
- **admin**: Full access to all endpoints
- **editor**: Can create, read, update, delete (CRUD) operations
- **viewer**: Read-only access
- **maintenance**: Limited CRUD access for maintenance operations

---

## Version Control API

The Version Control API provides comprehensive version management for building data, including version creation, branch management, merge requests, and conflict resolution.

### Version Management

#### POST /api/version-control/versions

Create a new version of floor data.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "floor_id": "floor-001",
  "building_id": "building-001",
  "data": {
    "objects": [
      {
        "id": "room-001",
        "type": "room",
        "x": 100,
        "y": 100,
        "width": 50,
        "height": 50
      },
      {
        "id": "device-001",
        "type": "device",
        "x": 150,
        "y": 150
      }
    ],
    "metadata": {
      "name": "Ground Floor",
      "level": 0,
      "area": 1000.0
    }
  },
  "branch": "main",
  "message": "Initial floor layout",
  "version_type": "major"
}
```

**Response:**
```json
{
  "success": true,
  "version_id": "v1.0.0-abc123",
  "version_number": 1,
  "data_hash": "sha256:abc123...",
  "version": {
    "id": "v1.0.0-abc123",
    "floor_id": "floor-001",
    "building_id": "building-001",
    "branch": "main",
    "version_number": 1,
    "message": "Initial floor layout",
    "version_type": "major",
    "created_by": "user-001",
    "created_at": "2024-01-15T10:30:00Z",
    "object_count": 2
  }
}
```

#### GET /api/version-control/versions/{version_id}

Retrieve a specific version.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "success": true,
  "version": {
    "id": "v1.0.0-abc123",
    "floor_id": "floor-001",
    "building_id": "building-001",
    "branch": "main",
    "version_number": 1,
    "message": "Initial floor layout",
    "version_type": "major",
    "created_by": "user-001",
    "created_at": "2024-01-15T10:30:00Z",
    "object_count": 2
  },
  "data": {
    "objects": [...],
    "metadata": {...}
  }
}
```

#### GET /api/version-control/floors/{floor_id}/buildings/{building_id}/history

Get version history for a floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Query Parameters:**
- `limit` (optional): Number of versions to return (default: 50, max: 100)
- `offset` (optional): Number of versions to skip (default: 0)
- `branch` (optional): Filter by branch name

**Response:**
```json
{
  "success": true,
  "versions": [
    {
      "id": "v1.0.1-def456",
      "floor_id": "floor-001",
      "building_id": "building-001",
      "branch": "main",
      "version_number": 2,
      "message": "Added new room",
      "version_type": "minor",
      "created_by": "user-001",
      "created_at": "2024-01-15T11:00:00Z",
      "object_count": 3
    },
    {
      "id": "v1.0.0-abc123",
      "floor_id": "floor-001",
      "building_id": "building-001",
      "branch": "main",
      "version_number": 1,
      "message": "Initial floor layout",
      "version_type": "major",
      "created_by": "user-001",
      "created_at": "2024-01-15T10:30:00Z",
      "object_count": 2
    }
  ],
  "total_count": 2,
  "has_more": false
}
```

### Branch Management

#### POST /api/version-control/branches

Create a new branch.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "branch_name": "feature-new-layout",
  "floor_id": "floor-001",
  "building_id": "building-001",
  "base_version_id": "v1.0.0-abc123",
  "description": "New layout design branch"
}
```

**Response:**
```json
{
  "success": true,
  "branch_name": "feature-new-layout",
  "branch": {
    "name": "feature-new-layout",
    "floor_id": "floor-001",
    "building_id": "building-001",
    "base_version_id": "v1.0.0-abc123",
    "description": "New layout design branch",
    "created_by": "user-001",
    "created_at": "2024-01-15T12:00:00Z",
    "status": "active"
  }
}
```

#### GET /api/version-control/floors/{floor_id}/buildings/{building_id}/branches

List all branches for a floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "success": true,
  "branches": [
    {
      "name": "main",
      "floor_id": "floor-001",
      "building_id": "building-001",
      "latest_version_id": "v1.0.1-def456",
      "latest_version_number": 2,
      "created_by": "user-001",
      "created_at": "2024-01-15T10:30:00Z",
      "status": "active"
    },
    {
      "name": "feature-new-layout",
      "floor_id": "floor-001",
      "building_id": "building-001",
      "latest_version_id": "v1.0.0-abc123",
      "latest_version_number": 1,
      "created_by": "user-001",
      "created_at": "2024-01-15T12:00:00Z",
      "status": "active"
    }
  ]
}
```

### Merge Requests

#### POST /api/version-control/merge-requests

Create a merge request.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "source_version_id": "v1.0.2-ghi789",
  "target_version_id": "v1.0.1-def456",
  "title": "Merge new layout changes",
  "description": "This merge request includes the new room layout design",
  "reviewers": ["user-002", "user-003"]
}
```

**Response:**
```json
{
  "success": true,
  "merge_request_id": "mr-001",
  "merge_request": {
    "id": "mr-001",
    "source_version_id": "v1.0.2-ghi789",
    "target_version_id": "v1.0.1-def456",
    "title": "Merge new layout changes",
    "description": "This merge request includes the new room layout design",
    "status": "open",
    "created_by": "user-001",
    "created_at": "2024-01-15T14:00:00Z",
    "reviewers": ["user-002", "user-003"],
    "conflicts": []
  }
}
```

#### POST /api/version-control/merge-requests/{merge_request_id}/execute

Execute a merge request.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "resolution_strategy": "auto",
  "conflict_resolutions": {}
}
```

**Response:**
```json
{
  "success": true,
  "merged_version_id": "v1.1.0-jkl012",
  "merge_request": {
    "id": "mr-001",
    "status": "merged",
    "merged_at": "2024-01-15T15:00:00Z",
    "merged_by": "user-002"
  }
}
```

### Annotations and Comments

#### POST /api/version-control/versions/{version_id}/annotations

Add an annotation to a version.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "content": "This room needs additional lighting",
  "position": {
    "x": 150,
    "y": 200
  },
  "type": "note",
  "object_id": "room-001"
}
```

**Response:**
```json
{
  "success": true,
  "annotation_id": "ann-001",
  "annotation": {
    "id": "ann-001",
    "version_id": "v1.0.0-abc123",
    "content": "This room needs additional lighting",
    "position": {
      "x": 150,
      "y": 200
    },
    "type": "note",
    "object_id": "room-001",
    "created_by": "user-001",
    "created_at": "2024-01-15T16:00:00Z"
  }
}
```

#### POST /api/version-control/versions/{version_id}/comments

Add a comment to a version.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "content": "Great layout design! Consider adding more exits for safety."
}
```

**Response:**
```json
{
  "success": true,
  "comment_id": "com-001",
  "comment": {
    "id": "com-001",
    "version_id": "v1.0.0-abc123",
    "content": "Great layout design! Consider adding more exits for safety.",
    "created_by": "user-001",
    "created_at": "2024-01-15T16:30:00Z"
  }
}
```

---

## Route Management API

The Route Management API provides comprehensive route planning and management capabilities for buildings, including evacuation routes, access routes, and optimization features.

### Route Operations

#### POST /api/routes

Create a new route.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "floor_id": "floor-001",
  "building_id": "building-001",
  "name": "Primary Evacuation Route",
  "route_type": "evacuation",
  "waypoints": [
    {
      "x": 100,
      "y": 100,
      "type": "start"
    },
    {
      "x": 200,
      "y": 200,
      "type": "waypoint"
    },
    {
      "x": 300,
      "y": 300,
      "type": "end"
    }
  ],
  "properties": {
    "distance": 250.0,
    "estimated_time": 120,
    "accessibility": true,
    "capacity": 100
  }
}
```

**Response:**
```json
{
  "success": true,
  "route_id": "route-001",
  "route": {
    "id": "route-001",
    "floor_id": "floor-001",
    "building_id": "building-001",
    "name": "Primary Evacuation Route",
    "route_type": "evacuation",
    "waypoints": [...],
    "properties": {
      "distance": 250.0,
      "estimated_time": 120,
      "accessibility": true,
      "capacity": 100
    },
    "created_by": "user-001",
    "created_at": "2024-01-15T17:00:00Z",
    "status": "active"
  }
}
```

#### GET /api/routes/{route_id}

Retrieve a specific route.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "success": true,
  "route": {
    "id": "route-001",
    "floor_id": "floor-001",
    "building_id": "building-001",
    "name": "Primary Evacuation Route",
    "route_type": "evacuation",
    "waypoints": [...],
    "properties": {...},
    "created_by": "user-001",
    "created_at": "2024-01-15T17:00:00Z",
    "status": "active"
  }
}
```

#### PUT /api/routes/{route_id}

Update a route.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "name": "Updated Evacuation Route",
  "waypoints": [
    {
      "x": 100,
      "y": 100,
      "type": "start"
    },
    {
      "x": 250,
      "y": 250,
      "type": "waypoint"
    },
    {
      "x": 400,
      "y": 400,
      "type": "end"
    }
  ],
  "properties": {
    "distance": 300.0,
    "estimated_time": 150,
    "accessibility": true,
    "capacity": 120
  }
}
```

**Response:**
```json
{
  "success": true,
  "route": {
    "id": "route-001",
    "name": "Updated Evacuation Route",
    "waypoints": [...],
    "properties": {...},
    "updated_at": "2024-01-15T18:00:00Z"
  }
}
```

#### DELETE /api/routes/{route_id}

Delete a route.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "success": true,
  "message": "Route deleted successfully"
}
```

#### GET /api/floors/{floor_id}/routes

Get all routes for a floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Query Parameters:**
- `route_type` (optional): Filter by route type (evacuation, access, maintenance)
- `status` (optional): Filter by status (active, inactive, draft)

**Response:**
```json
{
  "success": true,
  "routes": [
    {
      "id": "route-001",
      "name": "Primary Evacuation Route",
      "route_type": "evacuation",
      "properties": {
        "distance": 250.0,
        "estimated_time": 120
      },
      "status": "active"
    },
    {
      "id": "route-002",
      "name": "Access Route A",
      "route_type": "access",
      "properties": {
        "distance": 180.0,
        "estimated_time": 90
      },
      "status": "active"
    }
  ],
  "total_count": 2
}
```

### Route Optimization

#### POST /api/routes/{route_id}/optimize

Optimize a route.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "optimization_type": "shortest_path",
  "constraints": {
    "avoid_obstacles": true,
    "prefer_accessible": true,
    "max_distance": 500.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "route": {
    "id": "route-001",
    "optimized_waypoints": [...],
    "properties": {
      "original_distance": 300.0,
      "optimized_distance": 250.0,
      "savings_percentage": 16.7
    }
  }
}
```

### Route Validation

#### POST /api/routes/validate

Validate route parameters.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "floor_id": "floor-001",
  "waypoints": [...],
  "route_type": "evacuation"
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "validation_results": {
    "waypoints_valid": true,
    "distance_acceptable": true,
    "accessibility_compliant": true,
    "safety_compliant": true
  },
  "warnings": [
    "Route passes through restricted area"
  ]
}
```

---

## Floor Management API

The Floor Management API provides comprehensive floor-specific operations including creation, updates, comparison, analytics, and export functionality.

### Floor Operations

#### POST /api/floors

Create a new floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "building_id": "building-001",
  "name": "Ground Floor",
  "level": 0,
  "area": 1000.0,
  "metadata": {
    "floor_type": "office",
    "max_occupancy": 50,
    "accessibility": true,
    "floor_height": 3.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "floor_id": "floor-001",
  "floor": {
    "id": "floor-001",
    "building_id": "building-001",
    "name": "Ground Floor",
    "level": 0,
    "area": 1000.0,
    "metadata": {...},
    "created_by": "user-001",
    "created_at": "2024-01-15T19:00:00Z",
    "status": "active"
  }
}
```

#### GET /api/floors/{floor_id}

Retrieve a specific floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "success": true,
  "floor": {
    "id": "floor-001",
    "building_id": "building-001",
    "name": "Ground Floor",
    "level": 0,
    "area": 1000.0,
    "metadata": {...},
    "object_count": 25,
    "route_count": 3,
    "created_by": "user-001",
    "created_at": "2024-01-15T19:00:00Z",
    "status": "active"
  }
}
```

#### PUT /api/floors/{floor_id}

Update a floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "name": "Updated Ground Floor",
  "area": 1200.0,
  "metadata": {
    "floor_type": "retail",
    "max_occupancy": 75,
    "accessibility": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "floor": {
    "id": "floor-001",
    "name": "Updated Ground Floor",
    "area": 1200.0,
    "metadata": {...},
    "updated_at": "2024-01-15T20:00:00Z"
  }
}
```

#### DELETE /api/floors/{floor_id}

Delete a floor.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "success": true,
  "message": "Floor deleted successfully"
}
```

### Floor Comparison

#### POST /api/floors/compare

Compare two floors.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "floor_id_1": "floor-001",
  "floor_id_2": "floor-002",
  "comparison_type": "comprehensive"
}
```

**Response:**
```json
{
  "success": true,
  "comparison": {
    "similarity_score": 0.85,
    "differences": {
      "added_objects": [
        {
          "id": "room-003",
          "type": "room",
          "properties": {...}
        }
      ],
      "modified_objects": [
        {
          "id": "room-001",
          "changes": {
            "width": {"from": 50, "to": 60},
            "height": {"from": 50, "to": 60}
          }
        }
      ],
      "removed_objects": [],
      "metadata_differences": {
        "area": {"from": 1000.0, "to": 1200.0}
      }
    },
    "summary": {
      "total_objects_1": 25,
      "total_objects_2": 26,
      "common_objects": 24,
      "unique_objects_1": 1,
      "unique_objects_2": 2
    }
  }
}
```

### Floor Analytics

#### GET /api/floors/{floor_id}/analytics

Get floor analytics.

**Headers:** `Authorization: Bearer <jwt-token>`

**Query Parameters:**
- `analytics_type` (optional): Type of analytics (basic, detailed, performance)

**Response:**
```json
{
  "success": true,
  "analytics": {
    "object_count": 25,
    "area_utilization": 0.75,
    "object_distribution": {
      "rooms": 8,
      "devices": 12,
      "furniture": 5
    },
    "route_efficiency": {
      "average_distance": 180.0,
      "coverage_percentage": 0.95
    },
    "accessibility_score": 0.88,
    "safety_score": 0.92,
    "performance_metrics": {
      "load_time": 0.5,
      "render_time": 0.3,
      "memory_usage": 45.2
    }
  }
}
```

### Floor Export

#### POST /api/floors/{floor_id}/export

Export floor data.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "export_format": "json",
  "include_objects": true,
  "include_routes": true,
  "include_metadata": true
}
```

**Response:**
```json
{
  "success": true,
  "export": {
    "download_url": "https://api.arxos.io/exports/floor-001-20240115.json",
    "file_size": 245760,
    "expires_at": "2024-01-16T19:00:00Z",
    "format": "json"
  }
}
```

### Grid Calibration

#### POST /api/floors/{floor_id}/calibrate

Calibrate floor grid.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "grid_data": {
    "origin_x": 0,
    "origin_y": 0,
    "pixels_per_unit": 10,
    "unit": "feet",
    "reference_points": [
      {
        "pixel_x": 100,
        "pixel_y": 100,
        "real_x": 10.0,
        "real_y": 10.0
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "calibration": {
    "grid": {
      "origin_x": 0,
      "origin_y": 0,
      "pixels_per_unit": 10,
      "unit": "feet",
      "accuracy": 0.98
    },
    "calibrated_at": "2024-01-15T21:00:00Z"
  }
}
```

---

## Error Codes and Troubleshooting

### HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate branch) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid floor_id format",
    "details": {
      "field": "floor_id",
      "value": "invalid-id",
      "expected": "string matching pattern ^[a-z0-9-]+$"
    },
    "timestamp": "2024-01-15T22:00:00Z",
    "request_id": "req-abc123"
  }
}
```

### Common Error Codes

#### Version Control Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `VERSION_NOT_FOUND` | Version does not exist | Check version ID and permissions |
| `BRANCH_ALREADY_EXISTS` | Branch name already exists | Use a different branch name |
| `MERGE_CONFLICT` | Merge conflicts detected | Resolve conflicts before merging |
| `INVALID_VERSION_TYPE` | Invalid version type | Use: major, minor, patch |
| `PERMISSION_DENIED` | Insufficient permissions | Check user role and permissions |

#### Route Management Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `ROUTE_NOT_FOUND` | Route does not exist | Check route ID |
| `INVALID_WAYPOINTS` | Invalid waypoint format | Ensure waypoints have x, y coordinates |
| `ROUTE_TOO_LONG` | Route exceeds maximum length | Optimize route or increase limits |
| `ACCESSIBILITY_VIOLATION` | Route not accessible | Add accessible waypoints |
| `SAFETY_VIOLATION` | Route violates safety requirements | Review safety constraints |

#### Floor Management Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `FLOOR_NOT_FOUND` | Floor does not exist | Check floor ID |
| `INVALID_FLOOR_DATA` | Invalid floor data format | Validate data structure |
| `FLOOR_ALREADY_EXISTS` | Floor already exists | Use unique floor identifier |
| `EXPORT_FAILED` | Export operation failed | Check export parameters |
| `CALIBRATION_FAILED` | Grid calibration failed | Verify reference points |

### Troubleshooting Guide

#### Authentication Issues

**Problem**: 401 Unauthorized errors
**Solutions**:
1. Verify JWT token is valid and not expired
2. Check token format: `Authorization: Bearer <token>`
3. Ensure user has required permissions
4. Regenerate token if needed

#### Rate Limiting Issues

**Problem**: 429 Too Many Requests errors
**Solutions**:
1. Implement exponential backoff
2. Reduce request frequency
3. Use bulk operations where possible
4. Contact support for rate limit increases

#### Validation Errors

**Problem**: 422 Unprocessable Entity errors
**Solutions**:
1. Check request body format
2. Validate required fields
3. Ensure data types are correct
4. Review field constraints

#### Performance Issues

**Problem**: Slow response times
**Solutions**:
1. Use pagination for large datasets
2. Implement caching
3. Optimize queries
4. Use async operations where appropriate

#### Data Consistency Issues

**Problem**: Inconsistent data across operations
**Solutions**:
1. Use version control for data changes
2. Implement proper locking mechanisms
3. Validate data before operations
4. Use transactions for multi-step operations

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

### Rate Limit Tiers

| Tier | Requests/Second | Burst | Description |
|------|----------------|-------|-------------|
| Anonymous | 10 | 20 | Unauthenticated requests |
| Authenticated | 50 | 100 | Standard user requests |
| Premium | 100 | 200 | Premium user requests |
| Admin | 200 | 500 | Administrative requests |
| API Key | 1000 | 2000 | Data vendor requests |

### Rate Limit Strategies

1. **Exponential Backoff**: Retry with increasing delays
2. **Request Queuing**: Queue requests when limits are reached
3. **Bulk Operations**: Use batch endpoints for multiple operations
4. **Caching**: Cache responses to reduce API calls

---

## Security

### Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy`: Comprehensive CSP policy
- `Referrer-Policy: strict-origin-when-cross-origin`

### Data Protection

1. **Encryption**: All data encrypted in transit and at rest
2. **Access Control**: Role-based access control (RBAC)
3. **Audit Logging**: Comprehensive audit trails
4. **Data Validation**: Input validation and sanitization
5. **Rate Limiting**: Protection against abuse

### Best Practices

1. **Use HTTPS**: Always use HTTPS for API calls
2. **Secure Tokens**: Store tokens securely and rotate regularly
3. **Validate Input**: Validate all input data
4. **Handle Errors**: Implement proper error handling
5. **Monitor Usage**: Monitor API usage and performance 