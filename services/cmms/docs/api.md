# CMMS Service API Documentation

## Overview

The CMMS (Computerized Maintenance Management System) service provides integration with external CMMS systems for maintenance data synchronization and workflow management.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

All endpoints require authentication. Include the following header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### CMMS Connections

#### List CMMS Connections
```http
GET /cmms/connections
```

**Response:**
```json
{
  "connections": [
    {
      "id": 1,
      "name": "Upkeep CMMS",
      "type": "upkeep",
      "base_url": "https://api.upkeep.com",
      "is_active": true,
      "last_sync": "2024-01-15T10:30:00Z",
      "last_sync_status": "success",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get CMMS Connection
```http
GET /cmms/connections/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "Upkeep CMMS",
  "type": "upkeep",
  "base_url": "https://api.upkeep.com",
  "api_key": "***",
  "username": "user@example.com",
  "sync_interval_min": 60,
  "is_active": true,
  "last_sync": "2024-01-15T10:30:00Z",
  "last_sync_status": "success",
  "last_sync_error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Create CMMS Connection
```http
POST /cmms/connections
```

**Request Body:**
```json
{
  "name": "New CMMS Connection",
  "type": "upkeep",
  "base_url": "https://api.upkeep.com",
  "api_key": "your-api-key",
  "username": "user@example.com",
  "password": "password",
  "sync_interval_min": 60,
  "is_active": true
}
```

**Response:**
```json
{
  "id": 2,
  "message": "CMMS connection created successfully"
}
```

#### Update CMMS Connection
```http
PUT /cmms/connections/{id}
```

**Request Body:**
```json
{
  "name": "Updated CMMS Connection",
  "sync_interval_min": 120,
  "is_active": false
}
```

#### Delete CMMS Connection
```http
DELETE /cmms/connections/{id}
```

#### Test CMMS Connection
```http
POST /cmms/connections/{id}/test
```

**Response:**
```json
{
  "success": true,
  "message": "Connection test successful"
}
```

### CMMS Field Mappings

#### Get Field Mappings
```http
GET /cmms/connections/{connectionId}/mappings
```

**Response:**
```json
{
  "mappings": [
    {
      "id": 1,
      "cmms_connection_id": 1,
      "arxos_field": "asset_id",
      "cmms_field": "equipment_id",
      "data_type": "string",
      "is_required": true,
      "default_value": null,
      "transform_rule": null
    }
  ]
}
```

#### Create Field Mapping
```http
POST /cmms/connections/{connectionId}/mappings
```

**Request Body:**
```json
{
  "arxos_field": "schedule_type",
  "cmms_field": "maintenance_type",
  "data_type": "string",
  "is_required": true,
  "default_value": "preventive",
  "transform_rule": "{\"type\": \"string_manipulation\", \"operation\": \"uppercase\"}"
}
```

### Maintenance Schedules

#### Get Maintenance Schedules
```http
GET /cmms/maintenance-schedules
```

**Query Parameters:**
- `connection_id` (optional): Filter by CMMS connection
- `asset_id` (optional): Filter by asset
- `status` (optional): Filter by status (active, inactive)
- `limit` (optional): Number of records to return (default: 50)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
```json
{
  "schedules": [
    {
      "id": 1,
      "asset_id": 123,
      "cmms_connection_id": 1,
      "cmms_asset_id": "EQ-001",
      "schedule_type": "preventive",
      "frequency": "monthly",
      "interval": 1,
      "description": "Monthly HVAC filter replacement",
      "instructions": "Replace air filters and clean ducts",
      "estimated_hours": 2.5,
      "priority": "medium",
      "is_active": true,
      "next_due_date": "2024-02-15T00:00:00Z",
      "last_completed": "2024-01-15T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Work Orders

#### Get Work Orders
```http
GET /cmms/work-orders
```

**Query Parameters:**
- `connection_id` (optional): Filter by CMMS connection
- `asset_id` (optional): Filter by asset
- `status` (optional): Filter by status (open, in_progress, completed, cancelled)
- `priority` (optional): Filter by priority (low, medium, high, critical)
- `limit` (optional): Number of records to return (default: 50)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
```json
{
  "work_orders": [
    {
      "id": 1,
      "asset_id": 123,
      "cmms_connection_id": 1,
      "cmms_work_order_id": "WO-001",
      "work_order_number": "WO-2024-001",
      "type": "preventive",
      "status": "in_progress",
      "priority": "medium",
      "description": "HVAC filter replacement",
      "instructions": "Replace air filters and clean ducts",
      "assigned_to": "John Doe",
      "estimated_hours": 2.5,
      "actual_hours": 1.5,
      "cost": 150.00,
      "parts_used": "[\"air_filter\", \"duct_tape\"]",
      "created_date": "2024-01-15T00:00:00Z",
      "scheduled_date": "2024-01-20T00:00:00Z",
      "started_date": "2024-01-20T08:00:00Z",
      "completed_date": null,
      "created_at": "2024-01-15T00:00:00Z",
      "updated_at": "2024-01-20T08:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Equipment Specifications

#### Get Equipment Specifications
```http
GET /cmms/equipment-specifications
```

**Query Parameters:**
- `connection_id` (optional): Filter by CMMS connection
- `asset_id` (optional): Filter by asset
- `spec_type` (optional): Filter by spec type (technical, operational, maintenance)
- `limit` (optional): Number of records to return (default: 50)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
```json
{
  "specifications": [
    {
      "id": 1,
      "asset_id": 123,
      "cmms_connection_id": 1,
      "cmms_asset_id": "EQ-001",
      "spec_type": "technical",
      "spec_name": "voltage",
      "spec_value": "220",
      "unit": "V",
      "min_value": 200.0,
      "max_value": 240.0,
      "is_critical": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Sync Management

#### Manual Sync
```http
POST /cmms/connections/{id}/sync
```

**Request Body:**
```json
{
  "sync_type": "schedules" // schedules, work_orders, specs, all
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sync completed successfully",
  "result": {
    "records_processed": 10,
    "records_created": 5,
    "records_updated": 3,
    "records_failed": 2,
    "status": "partial"
  }
}
```

#### Get Sync Logs
```http
GET /cmms/connections/{id}/sync-logs
```

**Query Parameters:**
- `limit` (optional): Number of logs to return (default: 20)
- `sync_type` (optional): Filter by sync type

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "cmms_connection_id": 1,
      "sync_type": "schedules",
      "status": "success",
      "records_processed": 10,
      "records_created": 5,
      "records_updated": 3,
      "records_failed": 2,
      "error_details": null,
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:05:00Z"
    }
  ]
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "details": "Field 'name' is required"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "details": "Database connection failed"
}
```

## Data Transformation Rules

The CMMS service supports data transformation rules for field mapping. These are specified as JSON in the `transform_rule` field:

### String Manipulation
```json
{
  "type": "string_manipulation",
  "operation": "uppercase|lowercase|trim|replace",
  "parameters": {
    "search": "old_text",
    "replace": "new_text"
  }
}
```

### Date Format
```json
{
  "type": "date_format",
  "input_format": "MM/DD/YYYY",
  "output_format": "YYYY-MM-DD"
}
```

### Type Conversion
```json
{
  "type": "type_conversion",
  "target_type": "number|boolean|string"
}
```

### Conditional Logic
```json
{
  "type": "conditional",
  "conditions": [
    {
      "field": "status",
      "operator": "equals",
      "value": "active",
      "result": "true"
    }
  ],
  "default": "false"
}
```

## Rate Limiting

The API implements rate limiting:
- 100 requests per minute per user
- 1000 requests per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
``` 