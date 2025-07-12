# Arxos API Documentation

## Overview

The Arxos API provides comprehensive RESTful endpoints for SVG-BIM conversion, symbol management, security controls, and advanced features. This documentation covers all available endpoints with examples and usage guidelines.

## Base URL

```
https://api.arxos.com/api/v1
```

## Authentication

All API endpoints require authentication. Use the following headers:

```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

## Response Format

All API responses follow this standard format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-12-19T10:30:00Z"
}
```

## Error Handling

Errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "timestamp": "2024-12-19T10:30:00Z"
}
```

---

## 🔐 Security Endpoints

### Privacy Controls

#### Classify Data
**POST** `/security/privacy/classify`

Classify data based on content and type for privacy controls.

**Request Body:**
```json
{
  "data_type": "building_data",
  "content": {
    "building_id": "building_001",
    "floors": 5,
    "systems": ["electrical", "plumbing"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "data_type": "building_data",
    "classification": "internal",
    "classification_level": "INTERNAL"
  }
}
```

#### Apply Privacy Controls
**POST** `/security/privacy/controls`

Apply privacy controls to data based on classification.

**Request Body:**
```json
{
  "data": {
    "building_info": "sensitive data"
  },
  "classification": "confidential"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "data": "encrypted_data_here",
    "privacy_metadata": {
      "classification": "confidential",
      "encryption_required": true,
      "audit_required": true,
      "retention_days": 1095,
      "sharing_allowed": false
    }
  }
}
```

#### Anonymize Data
**POST** `/security/privacy/anonymize`

Anonymize data for external sharing.

**Request Body:**
```json
{
  "data": {
    "user_id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "building_data": "non-sensitive"
  },
  "fields_to_anonymize": ["user_id", "email", "name"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "anonymized_data": {
      "user_id": "anon_a1b2c3d4",
      "email": "anon_e5f6g7h8",
      "name": "anon_i9j0k1l2",
      "building_data": "non-sensitive"
    }
  }
}
```

### Encryption

#### Encrypt Data
**POST** `/security/encryption/encrypt`

Encrypt data using specified layer.

**Request Body:**
```json
{
  "data": "sensitive building information",
  "layer": "storage"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "encrypted_data": "a1b2c3d4e5f6...",
    "layer": "storage",
    "data_size": 256
  }
}
```

#### Decrypt Data
**POST** `/security/encryption/decrypt`

Decrypt data using specified layer.

**Request Body:**
```json
{
  "encrypted_data": "a1b2c3d4e5f6...",
  "layer": "storage"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "decrypted_data": "sensitive building information",
    "layer": "storage"
  }
}
```

#### Rotate Encryption Keys
**POST** `/security/encryption/rotate-keys`

Rotate encryption keys.

**Request Body:**
```json
{
  "key_type": "all"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Successfully rotated all encryption keys",
    "rotation_timestamp": "2024-12-19T10:30:00Z"
  }
}
```

#### Get Encryption Metrics
**GET** `/security/encryption/metrics`

Get encryption performance metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_operations": 1250,
    "total_time_ms": 12500.0,
    "average_time_ms": 10.0
  }
}
```

### Audit Trail

#### Log Audit Event
**POST** `/security/audit/log`

Log audit event with full details.

**Request Body:**
```json
{
  "event_type": "data_access",
  "user_id": "user123",
  "resource_id": "building_001",
  "action": "read",
  "details": {
    "data_type": "building_data",
    "classification": "internal"
  },
  "correlation_id": "corr_123456",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "success": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "event_id": "evt_a1b2c3d4e5f6",
    "timestamp": "2024-12-19T10:30:00Z",
    "status": "logged"
  }
}
```

#### Get Audit Logs
**GET** `/security/audit/logs`

Get audit logs with filtering.

**Query Parameters:**
- `event_type` (optional): Filter by event type
- `user_id` (optional): Filter by user ID
- `resource_id` (optional): Filter by resource ID
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)

**Response:**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "event_id": "evt_a1b2c3d4e5f6",
        "event_type": "data_access",
        "user_id": "user123",
        "resource_id": "building_001",
        "action": "read",
        "timestamp": "2024-12-19T10:30:00Z",
        "correlation_id": "corr_123456",
        "details": { ... },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "success": true
      }
    ],
    "total_count": 1,
    "filters_applied": { ... }
  }
}
```

#### Generate Compliance Report
**POST** `/security/audit/compliance-report`

Generate compliance report.

**Request Body:**
```json
{
  "report_type": "data_access",
  "start_date": "2024-12-01T00:00:00Z",
  "end_date": "2024-12-19T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_type": "data_access",
    "total_events": 1250,
    "unique_users": 45,
    "unique_resources": 23,
    "successful_access": 1200,
    "failed_access": 50,
    "events_by_user": { ... },
    "events_by_resource": { ... }
  }
}
```

#### Enforce Retention Policies
**POST** `/security/audit/enforce-retention`

Enforce data retention policies.

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Retention policies enforced successfully",
    "timestamp": "2024-12-19T10:30:00Z"
  }
}
```

#### Get Audit Metrics
**GET** `/security/audit/metrics`

Get audit trail performance metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_events": 1250,
    "events_by_type": {
      "data_access": 800,
      "user_login": 200,
      "permission_change": 50,
      "encryption_operation": 200
    },
    "average_logging_time_ms": 0.8
  }
}
```

### Role-Based Access Control (RBAC)

#### Create Role
**POST** `/security/rbac/roles`

Create role with specific permissions.

**Request Body:**
```json
{
  "role_name": "Building Administrator",
  "permissions": ["building:read", "building:write", "floor:read", "system:read"],
  "description": "Full building management permissions"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "role_id": "role_a1b2c3d4e5f6",
    "role_name": "Building Administrator",
    "permissions": ["building:read", "building:write", "floor:read", "system:read"],
    "description": "Full building management permissions"
  }
}
```

#### Assign User to Role
**POST** `/security/rbac/assign`

Assign user to role.

**Request Body:**
```json
{
  "user_id": "user123",
  "role_id": "role_a1b2c3d4e5f6"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "User user123 assigned to role role_a1b2c3d4e5f6",
    "user_id": "user123",
    "role_id": "role_a1b2c3d4e5f6"
  }
}
```

#### Check Permission
**POST** `/security/rbac/check-permission`

Check if user has permission for action on resource.

**Request Body:**
```json
{
  "user_id": "user123",
  "resource": "building",
  "action": "read"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "resource": "building",
    "action": "read",
    "has_permission": true
  }
}
```

#### Get User Permissions
**GET** `/security/rbac/users/{user_id}/permissions`

Get all permissions for user.

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "permissions": ["building:read", "building:write", "floor:read", "system:read"],
    "permission_count": 4
  }
}
```

#### Remove User from Role
**DELETE** `/security/rbac/assign`

Remove user from role.

**Request Body:**
```json
{
  "user_id": "user123",
  "role_id": "role_a1b2c3d4e5f6"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "User user123 removed from role role_a1b2c3d4e5f6",
    "user_id": "user123",
    "role_id": "role_a1b2c3d4e5f6"
  }
}
```

#### Get RBAC Metrics
**GET** `/security/rbac/metrics`

Get RBAC performance metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_permission_checks": 5000,
    "successful_checks": 4800,
    "failed_checks": 200,
    "average_check_time_ms": 0.8
  }
}
```

### AHJ API Integration

#### Create Inspection Layer
**POST** `/security/ahj/inspections`

Create AHJ inspection layer.

**Request Body:**
```json
{
  "building_id": "building_001",
  "ahj_id": "ahj_001",
  "inspector_id": "inspector_123",
  "metadata": {
    "inspection_type": "annual",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "layer_id": "layer_a1b2c3d4e5f6",
    "building_id": "building_001",
    "ahj_id": "ahj_001",
    "inspector_id": "inspector_123",
    "created_at": "2024-12-19T10:30:00Z"
  }
}
```

#### Add Inspection Annotation
**POST** `/security/ahj/annotations`

Add inspection annotation.

**Request Body:**
```json
{
  "layer_id": "layer_a1b2c3d4e5f6",
  "inspector_id": "inspector_123",
  "location": {
    "floor": 1,
    "room": "101",
    "system": "fire_safety"
  },
  "annotation_type": "violation",
  "description": "Missing fire extinguisher in room 101",
  "severity": "critical",
  "code_reference": "IFC 906.1",
  "image_attachments": ["violation_photo_001.jpg"],
  "metadata": {
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "annotation_id": "ann_a1b2c3d4e5f6",
    "layer_id": "layer_a1b2c3d4e5f6",
    "annotation_type": "violation",
    "severity": "critical",
    "created_at": "2024-12-19T10:30:00Z"
  }
}
```

#### Add Code Violation
**POST** `/security/ahj/violations`

Add building code violation.

**Request Body:**
```json
{
  "layer_id": "layer_a1b2c3d4e5f6",
  "inspector_id": "inspector_123",
  "code_section": "IFC 906.1",
  "description": "Fire extinguisher required but not present",
  "severity": "critical",
  "location": {
    "floor": 1,
    "room": "101"
  },
  "required_action": "Install fire extinguisher within 30 days",
  "deadline": "2025-01-18T10:30:00Z",
  "metadata": {
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "violation_id": "viol_a1b2c3d4e5f6",
    "layer_id": "layer_a1b2c3d4e5f6",
    "code_section": "IFC 906.1",
    "severity": "critical",
    "created_at": "2024-12-19T10:30:00Z"
  }
}
```

#### Get Inspection History
**GET** `/security/ahj/inspections/{layer_id}`

Get complete inspection history.

**Response:**
```json
{
  "success": true,
  "data": {
    "layer_id": "layer_a1b2c3d4e5f6",
    "building_id": "building_001",
    "ahj_id": "ahj_001",
    "inspector_id": "inspector_123",
    "created_at": "2024-12-19T10:30:00Z",
    "status": "violation_found",
    "annotations": [
      {
        "annotation_id": "ann_a1b2c3d4e5f6",
        "timestamp": "2024-12-19T10:30:00Z",
        "type": "violation",
        "description": "Missing fire extinguisher in room 101",
        "severity": "critical",
        "code_reference": "IFC 906.1",
        "location": { ... }
      }
    ],
    "violations": [
      {
        "violation_id": "viol_a1b2c3d4e5f6",
        "timestamp": "2024-12-19T10:30:00Z",
        "code_section": "IFC 906.1",
        "description": "Fire extinguisher required but not present",
        "severity": "critical",
        "required_action": "Install fire extinguisher within 30 days",
        "deadline": "2025-01-18T10:30:00Z",
        "status": "open"
      }
    ],
    "metadata": { ... }
  }
}
```

#### Get AHJ Jurisdictions
**GET** `/security/ahj/jurisdictions`

Get all supported AHJ jurisdictions.

**Response:**
```json
{
  "success": true,
  "data": {
    "jurisdictions": [
      {
        "ahj_id": "ahj_001",
        "name": "City of Seattle Building Department",
        "state": "WA",
        "type": "municipal",
        "contact_info": {
          "phone": "(206) 684-8600",
          "email": "building@seattle.gov",
          "address": "700 5th Ave, Seattle, WA 98104"
        },
        "supported_codes": ["IBC", "IRC", "IMC", "IFC", "IEBC"]
      }
    ],
    "total_count": 3
  }
}
```

#### Get Building Inspections
**GET** `/security/ahj/buildings/{building_id}/inspections`

Get all inspections for a building.

**Response:**
```json
{
  "success": true,
  "data": {
    "building_id": "building_001",
    "inspections": [
      {
        "layer_id": "layer_a1b2c3d4e5f6",
        "ahj_id": "ahj_001",
        "inspector_id": "inspector_123",
        "created_at": "2024-12-19T10:30:00Z",
        "status": "violation_found",
        "annotation_count": 1,
        "violation_count": 1
      }
    ],
    "total_count": 1
  }
}
```

#### Update Violation Status
**PUT** `/security/ahj/violations/{violation_id}`

Update violation status.

**Request Body:**
```json
{
  "status": "in_progress",
  "notes": "Fire extinguisher ordered"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "violation_id": "viol_a1b2c3d4e5f6",
    "status": "in_progress",
    "updated_at": "2024-12-19T10:30:00Z"
  }
}
```

#### Generate AHJ Compliance Report
**POST** `/security/ahj/compliance-report`

Generate compliance report for building.

**Request Body:**
```json
{
  "building_id": "building_001",
  "start_date": "2024-12-01T00:00:00Z",
  "end_date": "2024-12-19T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "building_id": "building_001",
    "report_generated": "2024-12-19T10:30:00Z",
    "total_inspections": 1,
    "total_violations": 1,
    "violations_by_severity": {
      "minor": 0,
      "moderate": 0,
      "major": 0,
      "critical": 1
    },
    "open_violations": 1,
    "resolved_violations": 0,
    "compliance_score": 75.0
  }
}
```

#### Get AHJ Metrics
**GET** `/security/ahj/metrics`

Get AHJ API performance metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_inspections": 50,
    "total_annotations": 125,
    "total_violations": 75,
    "average_inspection_time_ms": 85.0,
    "jurisdictions_supported": 3
  }
}
```

### Data Retention

#### Create Retention Policy
**POST** `/security/retention/policies`

Create data retention policy.

**Request Body:**
```json
{
  "data_type": "building_data",
  "retention_period_days": 1825,
  "deletion_strategy": "archive_delete",
  "description": "Building data - 5 year retention",
  "metadata": {
    "compliance_standard": "SOX"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "policy_id": "policy_a1b2c3d4e5f6",
    "data_type": "building_data",
    "retention_period_days": 1825,
    "deletion_strategy": "archive_delete",
    "description": "Building data - 5 year retention"
  }
}
```

#### Apply Retention Policy
**POST** `/security/retention/apply`

Apply retention policy to data.

**Request Body:**
```json
{
  "data_id": "building_001",
  "policy_id": "policy_a1b2c3d4e5f6",
  "data_type": "building_data"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "data_id": "building_001",
    "policy_id": "policy_a1b2c3d4e5f6",
    "applied_at": "2024-12-19T10:30:00Z"
  }
}
```

#### Schedule Data Deletion
**POST** `/security/retention/schedule-deletion`

Schedule data for deletion.

**Request Body:**
```json
{
  "data_id": "temp_data_789",
  "deletion_date": "2024-12-20T10:30:00Z",
  "deletion_strategy": "hard_delete"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_a1b2c3d4e5f6",
    "data_id": "temp_data_789",
    "scheduled_at": "2024-12-19T10:30:00Z"
  }
}
```

#### Execute Retention Policies
**POST** `/security/retention/execute`

Execute scheduled retention policies.

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs_executed": 5,
    "jobs_failed": 0,
    "data_deleted": 25,
    "data_archived": 10,
    "errors": []
  }
}
```

#### Archive Data
**POST** `/security/retention/archive`

Archive data for long-term storage.

**Request Body:**
```json
{
  "data_id": "old_building_data",
  "archive_path": "/custom/archive/path"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "data_id": "old_building_data",
    "archived_at": "2024-12-19T10:30:00Z",
    "success": true
  }
}
```

#### Get Retention Policies
**GET** `/security/retention/policies`

Get all retention policies.

**Response:**
```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "policy_id": "policy_a1b2c3d4e5f6",
        "data_type": "building_data",
        "retention_period_days": 1825,
        "deletion_strategy": "archive_delete",
        "description": "Building data - 5 year retention",
        "created_at": "2024-12-19T10:30:00Z",
        "active": true,
        "metadata": { ... }
      }
    ],
    "total_count": 8
  }
}
```

#### Get Data Lifecycle
**GET** `/security/retention/lifecycle`

Get data lifecycle information.

**Query Parameters:**
- `data_id` (optional): Specific data ID

**Response:**
```json
{
  "success": true,
  "data": {
    "lifecycle": [
      {
        "data_id": "building_001",
        "data_type": "building_data",
        "policy_id": "policy_a1b2c3d4e5f6",
        "created_at": "2024-12-19T10:30:00Z",
        "last_accessed": "2024-12-19T10:30:00Z",
        "deletion_date": "2029-12-19T10:30:00Z",
        "status": "active",
        "metadata": { ... }
      }
    ],
    "total_count": 1
  }
}
```

#### Generate Retention Compliance Report
**POST** `/security/retention/compliance-report`

Generate compliance report for data retention.

**Request Body:**
```json
{
  "start_date": "2024-12-01T00:00:00Z",
  "end_date": "2024-12-19T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_generated": "2024-12-19T10:30:00Z",
    "total_data_items": 100,
    "active_data": 80,
    "archived_data": 15,
    "deleted_data": 5,
    "compliance_violations": 0,
    "compliance_score": 100.0,
    "data_by_type": {
      "building_data": 50,
      "user_data": 30,
      "audit_logs": 20
    }
  }
}
```

#### Get Retention Metrics
**GET** `/security/retention/metrics`

Get data retention performance metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_policies": 8,
    "total_data_items": 100,
    "total_deletions": 25,
    "total_archives": 15,
    "average_deletion_time_ms": 150.0,
    "compliance_violations": 0
  }
}
```

### Integrated Security

#### Secure Data Access
**POST** `/security/secure-access`

Secure data access with full security controls.

**Request Body:**
```json
{
  "user_id": "user123",
  "resource_id": "building",
  "action": "read",
  "data": {
    "building_info": "sensitive data"
  },
  "data_type": "building_data",
  "correlation_id": "corr_123456"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "data": "encrypted_data_here",
    "privacy_metadata": {
      "classification": "internal",
      "encryption_required": true,
      "audit_required": true,
      "retention_days": 730,
      "sharing_allowed": false
    }
  }
}
```

#### Get Security Metrics
**GET** `/security/metrics`

Get comprehensive security metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "privacy_controls": {
      "data_classifications": 8,
      "privacy_rules": 5
    },
    "encryption": {
      "total_operations": 1250,
      "average_time_ms": 10.0
    },
    "audit_trail": {
      "total_events": 5000,
      "average_logging_time_ms": 0.8
    },
    "rbac": {
      "total_permission_checks": 5000,
      "average_check_time_ms": 0.8
    },
    "overall": {
      "total_operations": 6250,
      "average_operation_time_ms": 5.4
    }
  }
}
```

#### Security Health Check
**GET** `/security/health`

Health check for security services.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "services": {
      "privacy_controls": "operational",
      "encryption": "operational",
      "audit_trail": "operational",
      "rbac": "operational",
      "ahj_api": "operational",
      "data_retention": "operational"
    },
    "timestamp": "2024-12-19T10:30:00Z"
  }
}
```

---

## 🔧 Core Platform Endpoints

### Health Check
**GET** `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "SVG-BIM API is running",
  "version": "1.0.0"
}
```

### SVG Upload
**POST** `/upload/svg`

Upload and parse SVG file.

**Request:**
```http
POST /upload/svg
Content-Type: multipart/form-data

file: [SVG file]
```

**Response:**
```json
{
  "success": true,
  "message": "SVG uploaded and parsed successfully",
  "element_count": 150,
  "svg_id": "svg_150_12345"
}
```

### BIM Assembly
**POST** `/assemble/bim`

Assemble BIM from SVG content.

**Request:**
```http
POST /assemble/bim
Content-Type: application/x-www-form-urlencoded

svg_content: <svg>...</svg>
format: json
validation_level: standard
```

**Response:**
```json
{
  "success": true,
  "message": "BIM assembled successfully",
  "file_path": "/tmp/bim_12345.json",
  "format": "json"
}
```

### BIM Export
**GET** `/export/bim/{file_id}`

Export BIM data in specified format.

**Query Parameters:**
- `format` (optional): Export format (json, xml, etc.)

**Response:**
```json
{
  "success": true,
  "message": "BIM exported successfully",
  "file_path": "/tmp/bim_12345.json",
  "format": "json"
}
```

### BIM Query
**GET** `/query/bim/{file_id}`

Query BIM data.

**Query Parameters:**
- `query_type` (optional): Query type (summary, elements, systems, etc.)

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "element_count": 150,
      "system_count": 5,
      "space_count": 10
    }
  },
  "count": 150
}
```

### File Download
**GET** `/download/{file_path:path}`

Download generated files.

**Response:**
File download with appropriate headers.

---

## 📊 Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid input parameters | 400 |
| `AUTHENTICATION_ERROR` | Invalid or missing authentication | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

---

## 🔒 Security Considerations

### Authentication
- All endpoints require valid authentication tokens
- Tokens expire after 24 hours
- Refresh tokens available for extended sessions

### Rate Limiting
- 1000 requests per hour per user
- 100 requests per minute per endpoint
- Rate limit headers included in responses

### Data Protection
- All sensitive data encrypted at rest
- TLS 1.3 for data in transit
- Audit trail for all data access
- Privacy controls applied automatically

### Compliance
- GDPR compliant data handling
- HIPAA compliant for healthcare data
- SOX compliant audit trails
- Industry-standard security practices

---

## 📚 Additional Resources

- [User Guide](./USER_GUIDE.md) - End-user documentation
- [Admin Guide](./ADMIN_GUIDE.md) - System administration
- [Integration Guide](./INTEGRATION_GUIDE.md) - Third-party integrations
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions

---

**API Version**: 1.0.0  
**Last Updated**: December 19, 2024  
**Contact**: api-support@arxos.com 