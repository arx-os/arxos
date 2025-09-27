# ArxOS API Reference

## Overview

The ArxOS API provides comprehensive access to all building management functionality through a RESTful interface. The API follows REST principles with resource-based URLs and standard HTTP methods.

## Base URL

```
https://api.arxos.com/v1
```

## Authentication

All API requests require authentication using JWT tokens or API keys.

### JWT Authentication
```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication
```http
X-API-Key: <api_key>
```

## Response Format

All API responses are in JSON format with the following structure:

### Success Response
```json
{
  "data": <response_data>,
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "building_id",
      "reason": "required field missing"
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Standard Users**: 1000 requests per hour
- **Premium Users**: 5000 requests per hour
- **Enterprise Users**: 10000 requests per hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248600
```

## Analytics API

### Energy Data

#### Get Energy Consumption Data
```http
GET /api/analytics/energy/data
```

**Query Parameters:**
- `building_id` (optional): Filter by building ID
- `start_time` (optional): Start time (ISO 8601)
- `end_time` (optional): End time (ISO 8601)
- `energy_type` (optional): Filter by energy type

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "building_id": "building_001",
      "space_id": "space_001",
      "asset_id": "asset_001",
      "energy_type": "electricity",
      "consumption": 1250.5,
      "cost": 15.0,
      "efficiency": 85.0,
      "temperature": 22.0,
      "humidity": 45.0,
      "occupancy": 10,
      "weather_data": {
        "temperature": 22.0,
        "humidity": 45.0,
        "wind_speed": 5.0,
        "solar_radiation": 500.0,
        "cloud_cover": 30.0,
        "precipitation": 0.0
      }
    }
  ]
}
```

#### Post Energy Data
```http
POST /api/analytics/energy/data
```

**Request Body:**
```json
{
  "timestamp": "2024-01-15T10:00:00Z",
  "building_id": "building_001",
  "space_id": "space_001",
  "asset_id": "asset_001",
  "energy_type": "electricity",
  "consumption": 1250.5,
  "cost": 15.0,
  "efficiency": 85.0,
  "temperature": 22.0,
  "humidity": 45.0,
  "occupancy": 10
}
```

#### Get Energy Recommendations
```http
GET /api/analytics/energy/recommendations
```

**Query Parameters:**
- `building_id` (optional): Filter by building ID

**Response:**
```json
{
  "data": [
    {
      "id": "rec_001",
      "building_id": "building_001",
      "space_id": "space_001",
      "asset_id": "asset_001",
      "type": "efficiency",
      "title": "Optimize HVAC Setpoints",
      "description": "Adjust temperature setpoints by 2°F during off-hours",
      "priority": 1,
      "potential_savings": 50.0,
      "implementation_cost": 25.0,
      "payback_period": "P6M",
      "confidence": 0.9,
      "status": "pending"
    }
  ]
}
```

### Predictive Analytics

#### Get Forecasts
```http
GET /api/analytics/predictive/forecasts
```

**Query Parameters:**
- `metric` (required): Metric to forecast
- `duration` (optional): Forecast duration (e.g., "24h", "7d")

**Response:**
```json
{
  "data": {
    "id": "forecast_001",
    "model_id": "model_001",
    "target": "energy_consumption",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-16T10:00:00Z",
    "interval": "PT1H",
    "values": [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "value": 1250.0,
        "lower_bound": 1100.0,
        "upper_bound": 1400.0,
        "confidence": 0.85
      }
    ],
    "confidence": 0.85,
    "accuracy": 0.87
  }
}
```

## IT Management API

### Assets

#### Get Assets
```http
GET /api/it/assets
```

**Query Parameters:**
- `type` (optional): Filter by asset type
- `status` (optional): Filter by asset status
- `building` (optional): Filter by building
- `room` (optional): Filter by room

**Response:**
```json
{
  "data": [
    {
      "id": "asset_001",
      "name": "Dell Latitude 5520",
      "type": "laptop",
      "category": "Computers",
      "brand": "Dell",
      "model": "Latitude 5520",
      "serial_number": "ABC123",
      "asset_tag": "LAP-001",
      "location": {
        "building": "main",
        "floor": "2",
        "room": "classroom-205",
        "room_number": "205",
        "department": "IT",
        "zone": "north"
      },
      "status": "active",
      "condition": "good",
      "purchase_date": "2023-01-15T00:00:00Z",
      "warranty_expiry": "2026-01-15T00:00:00Z",
      "purchase_price": 1200.0,
      "current_value": 1000.0,
      "supplier": "Dell"
    }
  ]
}
```

#### Create Asset
```http
POST /api/it/assets
```

**Request Body:**
```json
{
  "name": "Dell Latitude 5520",
  "type": "laptop",
  "category": "Computers",
  "brand": "Dell",
  "model": "Latitude 5520",
  "serial_number": "ABC123",
  "asset_tag": "LAP-001",
  "location": {
    "building": "main",
    "floor": "2",
    "room": "classroom-205"
  },
  "purchase_price": 1200.0,
  "current_value": 1000.0,
  "supplier": "Dell"
}
```

#### Get Assets by Room
```http
GET /api/it/assets/room/{room_path}
```

**Path Parameters:**
- `room_path`: Building path (e.g., "/buildings/main/floors/2/rooms/classroom-205")

### Room Setups

#### Get Room Setups
```http
GET /api/it/rooms
```

**Query Parameters:**
- `setup_type` (optional): Filter by setup type
- `building` (optional): Filter by building
- `room` (optional): Filter by room
- `include_templates` (optional): Include templates (true/false)

**Response:**
```json
{
  "data": [
    {
      "id": "setup_001",
      "name": "Classroom 205 - Traditional",
      "description": "Traditional classroom setup with projector and doc camera",
      "room": {
        "building": "main",
        "floor": "2",
        "room": "classroom-205"
      },
      "setup_type": "traditional",
      "assets": [
        {
          "asset_id": "asset_001",
          "position": {
            "x": 10.0,
            "y": 5.0,
            "z": 8.0,
            "rotation": 0.0,
            "mount_type": "ceiling"
          },
          "is_primary": true,
          "is_required": true
        }
      ],
      "connections": [
        {
          "id": "conn_001",
          "from_asset": "asset_001",
          "to_asset": "asset_002",
          "type": "hdmi",
          "port": "hdmi_out",
          "is_active": true
        }
      ],
      "is_active": true
    }
  ]
}
```

#### Create Room Setup
```http
POST /api/it/rooms
```

**Request Body:**
```json
{
  "room_path": "/buildings/main/floors/2/rooms/classroom-205",
  "setup_type": "traditional",
  "created_by": "admin@school.edu"
}
```

#### Get Room Summary
```http
GET /api/it/rooms/summary/{room_path}
```

**Response:**
```json
{
  "data": {
    "room_path": "/buildings/main/floors/2/rooms/classroom-205",
    "setup_type": "traditional",
    "is_active": true,
    "total_assets": 3,
    "asset_types": {
      "projector": 1,
      "doc_camera": 1,
      "docking_station": 1
    },
    "work_orders": 2,
    "open_work_orders": 1,
    "last_updated": "2024-01-15T10:00:00Z"
  }
}
```

### Work Orders

#### Get Work Orders
```http
GET /api/it/workorders
```

**Query Parameters:**
- `status` (optional): Filter by status
- `type` (optional): Filter by type
- `priority` (optional): Filter by priority
- `assigned_to` (optional): Filter by assignee
- `building` (optional): Filter by building
- `room` (optional): Filter by room

**Response:**
```json
{
  "data": [
    {
      "id": "wo_001",
      "title": "Install New Projector",
      "description": "Install and configure new Epson projector in classroom 205",
      "type": "installation",
      "priority": "high",
      "status": "open",
      "location": {
        "building": "main",
        "floor": "2",
        "room": "classroom-205"
      },
      "requested_by": "teacher@school.edu",
      "assigned_to": "",
      "assets": [],
      "parts": [],
      "estimated_time": "PT2H",
      "actual_time": "PT0S",
      "cost": 0.0,
      "created_at": "2024-01-15T10:00:00Z",
      "due_date": "2024-01-20T17:00:00Z"
    }
  ]
}
```

#### Create Work Order
```http
POST /api/it/workorders
```

**Request Body:**
```json
{
  "room_path": "/buildings/main/floors/2/rooms/classroom-205",
  "title": "Install New Projector",
  "description": "Install and configure new Epson projector",
  "type": "installation",
  "priority": "high",
  "requested_by": "teacher@school.edu"
}
```

## Workflow API

### Workflows

#### Get Workflows
```http
GET /api/workflow/workflows
```

**Response:**
```json
{
  "data": [
    {
      "id": "workflow_001",
      "name": "Energy Optimization",
      "description": "Automated energy optimization workflow",
      "status": "active",
      "triggers": [
        {
          "id": "trigger_001",
          "type": "schedule",
          "config": {
            "cron": "0 0 * * *"
          }
        }
      ],
      "nodes": [
        {
          "id": "node_001",
          "type": "action",
          "name": "Check Energy Usage",
          "config": {
            "action_type": "api_call",
            "endpoint": "/api/analytics/energy/data"
          }
        }
      ],
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Execute Workflow
```http
POST /api/workflow/workflows/{workflow_id}/execute
```

**Request Body:**
```json
{
  "input": {
    "building_id": "building_001",
    "parameters": {
      "threshold": 1000.0
    }
  }
}
```

## CMMS/CAFM API

### Facilities

#### Get Buildings
```http
GET /api/facility/buildings
```

**Response:**
```json
{
  "data": [
    {
      "id": "building_001",
      "name": "Main Building",
      "address": "123 School St",
      "city": "Anytown",
      "state": "CA",
      "zip_code": "12345",
      "country": "USA",
      "building_type": "educational",
      "status": "active",
      "floors": 3,
      "total_area": 50000.0,
      "year_built": 2020,
      "owner": "School District",
      "manager": "Facilities Manager",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Get Work Orders
```http
GET /api/facility/workorders
```

**Query Parameters:**
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority
- `building_id` (optional): Filter by building
- `assigned_to` (optional): Filter by assignee

**Response:**
```json
{
  "data": [
    {
      "id": "wo_001",
      "title": "HVAC Maintenance",
      "description": "Quarterly HVAC system maintenance",
      "type": "maintenance",
      "priority": "medium",
      "status": "open",
      "building_id": "building_001",
      "space_id": "space_001",
      "asset_id": "asset_001",
      "requested_by": "facilities@school.edu",
      "assigned_to": "technician@school.edu",
      "estimated_duration": "PT4H",
      "actual_duration": "PT0S",
      "cost": 0.0,
      "created_at": "2024-01-15T10:00:00Z",
      "due_date": "2024-01-20T17:00:00Z"
    }
  ]
}
```

## Hardware Platform API

### Devices

#### Get Devices
```http
GET /api/hardware/devices
```

**Response:**
```json
{
  "data": [
    {
      "id": "device_001",
      "name": "Temperature Sensor 001",
      "type": "sensor",
      "category": "environmental",
      "model": "TempSense Pro",
      "firmware_version": "1.2.3",
      "status": "online",
      "location": {
        "building": "main",
        "floor": "2",
        "room": "classroom-205"
      },
      "protocol": "mqtt",
      "connection_status": "connected",
      "last_seen": "2024-01-15T10:00:00Z",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Certifications

#### Get Certifications
```http
GET /api/hardware/certifications
```

**Response:**
```json
{
  "data": [
    {
      "id": "cert_001",
      "device_id": "device_001",
      "test_suite": "safety_basic",
      "status": "passed",
      "score": 95.5,
      "tested_at": "2024-01-15T10:00:00Z",
      "expires_at": "2025-01-15T10:00:00Z",
      "certificate_url": "https://api.arxos.com/certificates/cert_001.pdf"
    }
  ]
}
```

## Error Codes

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Validation Error Details

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "building_id",
        "code": "required",
        "message": "building_id is required"
      },
      {
        "field": "email",
        "code": "invalid_format",
        "message": "email must be a valid email address"
      }
    ]
  }
}
```

## Pagination

List endpoints support pagination using query parameters:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `sort`: Sort field (default: created_at)
- `order`: Sort order (asc/desc, default: desc)

**Response Headers:**
```http
X-Total-Count: 150
X-Page-Count: 8
X-Current-Page: 1
X-Per-Page: 20
```

**Response Body:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Webhooks

ArxOS supports webhooks for real-time notifications:

### Webhook Events

- `asset.created`
- `asset.updated`
- `asset.deleted`
- `workorder.created`
- `workorder.updated`
- `workorder.completed`
- `energy.anomaly_detected`
- `workflow.executed`
- `workflow.failed`

### Webhook Payload

```json
{
  "event": "asset.created",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "id": "asset_001",
    "name": "Dell Latitude 5520",
    "type": "laptop"
  }
}
```

### Webhook Security

Webhooks are secured using HMAC-SHA256 signatures:

```http
X-ArxOS-Signature: sha256=abc123def456...
```

## SDKs and Libraries

### Go SDK
```go
import "github.com/arx-os/arxos-sdk-go"

client := arxos.NewClient("https://api.arxos.com", "your-api-key")
assets, err := client.Assets.List(context.Background(), &arxos.AssetListOptions{
    Type: "laptop",
})
```

### Python SDK
```python
import arxos

client = arxos.Client("https://api.arxos.com", "your-api-key")
assets = client.assets.list(type="laptop")
```

### JavaScript SDK
```javascript
import { ArxOSClient } from '@arx-os/sdk-js';

const client = new ArxOSClient('https://api.arxos.com', 'your-api-key');
const assets = await client.assets.list({ type: 'laptop' });
```

## Support

For API support and questions:

- **Documentation**: https://docs.arxos.com
- **Support Email**: api-support@arxos.com
- **Status Page**: https://status.arxos.com
- **GitHub Issues**: https://github.com/arx-os/arxos/issues
