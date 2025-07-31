# Construction Management API Reference

## Overview

The Construction Management API provides comprehensive endpoints for managing construction projects, schedules, documents, inspections, safety, and cost tracking. This API integrates with existing Arxos services (AI, IoT, BIM, CMMS) to provide a complete construction project management solution.

## Base URL

```
Production: https://api.arxos.com/construction/v1
Staging: https://staging-api.arxos.com/construction/v1
Development: http://localhost:8000/construction/v1
```

## Authentication

All API endpoints require authentication using JWT tokens.

### Headers
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

### Token Format
```json
{
  "sub": "user-id",
  "exp": 1640995200,
  "iat": 1640908800,
  "role": "project_manager"
}
```

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "name",
      "issue": "Field is required"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Input validation failed | 400 |
| `AUTHENTICATION_ERROR` | Invalid or missing token | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `CONFLICT` | Resource conflict | 409 |
| `INTERNAL_ERROR` | Server error | 500 |

---

## Projects API

### Get Projects
Retrieve a list of construction projects.

**Endpoint:** `GET /projects`

**Query Parameters:**
- `status` (optional): Filter by project status
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Downtown Office Complex",
        "description": "Modern office building with 20 floors",
        "start_date": "2024-01-15",
        "end_date": "2025-06-30",
        "budget": 25000000.00,
        "status": "in_progress",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "created_by": "user-123",
        "updated_by": "user-123"
      }
    ],
    "pagination": {
      "total": 25,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### Create Project
Create a new construction project.

**Endpoint:** `POST /projects`

**Request Body:**
```json
{
  "name": "Downtown Office Complex",
  "description": "Modern office building with 20 floors",
  "start_date": "2024-01-15",
  "end_date": "2025-06-30",
  "budget": 25000000.00,
  "location": {
    "address": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Downtown Office Complex",
    "description": "Modern office building with 20 floors",
    "start_date": "2024-01-15",
    "end_date": "2025-06-30",
    "budget": 25000000.00,
    "status": "planning",
    "created_at": "2024-01-01T12:00:00Z",
    "created_by": "user-123"
  }
}
```

### Get Project
Retrieve a specific construction project.

**Endpoint:** `GET /projects/{project_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Downtown Office Complex",
    "description": "Modern office building with 20 floors",
    "start_date": "2024-01-15",
    "end_date": "2025-06-30",
    "budget": 25000000.00,
    "status": "in_progress",
    "location": {
      "address": "123 Main Street",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060
      }
    },
    "statistics": {
      "total_tasks": 150,
      "completed_tasks": 45,
      "total_documents": 75,
      "safety_incidents": 2,
      "budget_used": 8500000.00,
      "budget_remaining": 16500000.00
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "created_by": "user-123",
    "updated_by": "user-123"
  }
}
```

### Update Project
Update an existing construction project.

**Endpoint:** `PUT /projects/{project_id}`

**Request Body:**
```json
{
  "name": "Downtown Office Complex - Updated",
  "description": "Modern office building with 20 floors and rooftop garden",
  "end_date": "2025-08-30",
  "budget": 27500000.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Downtown Office Complex - Updated",
    "description": "Modern office building with 20 floors and rooftop garden",
    "start_date": "2024-01-15",
    "end_date": "2025-08-30",
    "budget": 27500000.00,
    "status": "in_progress",
    "updated_at": "2024-01-15T11:00:00Z",
    "updated_by": "user-123"
  }
}
```

### Delete Project
Delete a construction project.

**Endpoint:** `DELETE /projects/{project_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted": true,
    "deleted_at": "2024-01-15T12:00:00Z"
  }
}
```

---

## Schedules API

### Get Project Schedule
Retrieve the schedule for a specific project.

**Endpoint:** `GET /projects/{project_id}/schedule`

**Query Parameters:**
- `include_dependencies` (optional): Include task dependencies (default: true)
- `include_critical_path` (optional): Include critical path analysis (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "schedule": [
      {
        "id": "task-123",
        "name": "Foundation Excavation",
        "description": "Excavate foundation for building",
        "start_date": "2024-01-15",
        "end_date": "2024-02-15",
        "duration_days": 32,
        "progress": 75.0,
        "status": "in_progress",
        "assigned_to": "user-456",
        "priority": 1,
        "dependencies": ["task-122"],
        "is_critical": true,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "critical_path": [
      "task-123",
      "task-124",
      "task-125"
    ],
    "total_duration": 450,
    "completion_percentage": 30.0
  }
}
```

### Create Schedule Task
Create a new task in the project schedule.

**Endpoint:** `POST /projects/{project_id}/schedule`

**Request Body:**
```json
{
  "name": "Foundation Excavation",
  "description": "Excavate foundation for building",
  "start_date": "2024-01-15",
  "end_date": "2024-02-15",
  "assigned_to": "user-456",
  "priority": 1,
  "dependencies": ["task-122"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task-123",
    "name": "Foundation Excavation",
    "description": "Excavate foundation for building",
    "start_date": "2024-01-15",
    "end_date": "2024-02-15",
    "duration_days": 32,
    "progress": 0.0,
    "status": "pending",
    "assigned_to": "user-456",
    "priority": 1,
    "dependencies": ["task-122"],
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### Update Task Progress
Update the progress of a specific task.

**Endpoint:** `PUT /projects/{project_id}/schedule/{task_id}/progress`

**Request Body:**
```json
{
  "progress": 75.0,
  "status": "in_progress",
  "notes": "Foundation excavation completed, ready for concrete pour"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task-123",
    "progress": 75.0,
    "status": "in_progress",
    "notes": "Foundation excavation completed, ready for concrete pour",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Documents API

### Get Project Documents
Retrieve documents for a specific project.

**Endpoint:** `GET /projects/{project_id}/documents`

**Query Parameters:**
- `type` (optional): Filter by document type
- `search` (optional): Search in document names and content
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "doc-123",
        "name": "Building Plans - Floor 1",
        "type": "blueprint",
        "file_path": "/documents/project-123/building-plans-floor1.pdf",
        "file_size": 2048576,
        "mime_type": "application/pdf",
        "version": "1.2",
        "uploaded_by": "user-123",
        "uploaded_at": "2024-01-01T12:00:00Z",
        "metadata": {
          "floor": 1,
          "scale": "1:100",
          "revision": "B"
        },
        "tags": ["blueprint", "floor1", "architectural"]
      }
    ],
    "pagination": {
      "total": 75,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### Upload Document
Upload a new document to the project.

**Endpoint:** `POST /projects/{project_id}/documents`

**Request Body:** (multipart/form-data)
```
file: [binary file data]
name: "Building Plans - Floor 2"
type: "blueprint"
tags: ["blueprint", "floor2", "architectural"]
metadata: {
  "floor": 2,
  "scale": "1:100",
  "revision": "A"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "doc-124",
    "name": "Building Plans - Floor 2",
    "type": "blueprint",
    "file_path": "/documents/project-123/building-plans-floor2.pdf",
    "file_size": 1876543,
    "mime_type": "application/pdf",
    "version": "1.0",
    "uploaded_by": "user-123",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "metadata": {
      "floor": 2,
      "scale": "1:100",
      "revision": "A"
    },
    "tags": ["blueprint", "floor2", "architectural"]
  }
}
```

### Get Document
Retrieve a specific document.

**Endpoint:** `GET /projects/{project_id}/documents/{document_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "doc-123",
    "name": "Building Plans - Floor 1",
    "type": "blueprint",
    "file_path": "/documents/project-123/building-plans-floor1.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "version": "1.2",
    "uploaded_by": "user-123",
    "uploaded_at": "2024-01-01T12:00:00Z",
    "metadata": {
      "floor": 1,
      "scale": "1:100",
      "revision": "B"
    },
    "tags": ["blueprint", "floor1", "architectural"],
    "download_url": "https://api.arxos.com/construction/v1/projects/project-123/documents/doc-123/download",
    "preview_url": "https://api.arxos.com/construction/v1/projects/project-123/documents/doc-123/preview"
  }
}
```

### Download Document
Download a document file.

**Endpoint:** `GET /projects/{project_id}/documents/{document_id}/download`

**Response:** Binary file data with appropriate headers.

---

## Inspections API

### Get Project Inspections
Retrieve inspections for a specific project.

**Endpoint:** `GET /projects/{project_id}/inspections`

**Query Parameters:**
- `type` (optional): Filter by inspection type
- `status` (optional): Filter by inspection status
- `inspector_id` (optional): Filter by inspector
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "inspections": [
      {
        "id": "insp-123",
        "inspection_type": "structural",
        "location": {
          "floor": 5,
          "area": "North Wing",
          "coordinates": {
            "latitude": 40.7128,
            "longitude": -74.0060
          }
        },
        "inspector_id": "user-456",
        "scheduled_date": "2024-01-20",
        "completed_date": "2024-01-20",
        "status": "completed",
        "findings": {
          "overall_status": "pass",
          "issues": [
            {
              "type": "minor",
              "description": "Minor crack in concrete",
              "recommendation": "Monitor and repair if worsens"
            }
          ],
          "recommendations": "Continue with construction"
        },
        "photos": [
          {
            "id": "photo-123",
            "url": "https://api.arxos.com/construction/v1/inspections/insp-123/photos/photo-123",
            "description": "Crack in concrete wall",
            "taken_at": "2024-01-20T10:30:00Z"
          }
        ],
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-20T15:00:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### Create Inspection
Create a new inspection for the project.

**Endpoint:** `POST /projects/{project_id}/inspections`

**Request Body:**
```json
{
  "inspection_type": "electrical",
  "location": {
    "floor": 3,
    "area": "East Wing",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  },
  "inspector_id": "user-456",
  "scheduled_date": "2024-01-25",
  "notes": "Electrical inspection for floor 3"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "insp-124",
    "inspection_type": "electrical",
    "location": {
      "floor": 3,
      "area": "East Wing",
      "coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060
      }
    },
    "inspector_id": "user-456",
    "scheduled_date": "2024-01-25",
    "status": "scheduled",
    "notes": "Electrical inspection for floor 3",
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

### Complete Inspection
Complete an inspection with findings.

**Endpoint:** `PUT /projects/{project_id}/inspections/{inspection_id}/complete`

**Request Body:**
```json
{
  "findings": {
    "overall_status": "pass",
    "issues": [
      {
        "type": "minor",
        "description": "Loose electrical outlet",
        "recommendation": "Tighten outlet screws"
      }
    ],
    "recommendations": "Electrical work approved for this floor"
  },
  "photos": [
    {
      "description": "Electrical panel inspection",
      "file": "[binary photo data]"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "insp-124",
    "status": "completed",
    "completed_date": "2024-01-25T14:30:00Z",
    "findings": {
      "overall_status": "pass",
      "issues": [
        {
          "type": "minor",
          "description": "Loose electrical outlet",
          "recommendation": "Tighten outlet screws"
        }
      ],
      "recommendations": "Electrical work approved for this floor"
    },
    "photos": [
      {
        "id": "photo-124",
        "url": "https://api.arxos.com/construction/v1/inspections/insp-124/photos/photo-124",
        "description": "Electrical panel inspection",
        "taken_at": "2024-01-25T14:30:00Z"
      }
    ],
    "updated_at": "2024-01-25T14:30:00Z"
  }
}
```

---

## Safety API

### Get Safety Incidents
Retrieve safety incidents for a specific project.

**Endpoint:** `GET /projects/{project_id}/safety/incidents`

**Query Parameters:**
- `severity` (optional): Filter by incident severity
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "incidents": [
      {
        "id": "incident-123",
        "incident_type": "slip_and_fall",
        "severity": "minor",
        "location": {
          "floor": 2,
          "area": "Construction Zone A",
          "coordinates": {
            "latitude": 40.7128,
            "longitude": -74.0060
          }
        },
        "description": "Worker slipped on wet surface",
        "reported_by": "user-789",
        "reported_at": "2024-01-15T10:30:00Z",
        "resolved_at": "2024-01-15T11:00:00Z",
        "resolution": "Surface cleaned and warning signs posted",
        "photos": [
          {
            "id": "photo-123",
            "url": "https://api.arxos.com/construction/v1/safety/incidents/incident-123/photos/photo-123",
            "description": "Wet surface area",
            "taken_at": "2024-01-15T10:30:00Z"
          }
        ]
      }
    ],
    "pagination": {
      "total": 5,
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

### Report Safety Incident
Report a new safety incident.

**Endpoint:** `POST /projects/{project_id}/safety/incidents`

**Request Body:**
```json
{
  "incident_type": "equipment_malfunction",
  "severity": "moderate",
  "location": {
    "floor": 4,
    "area": "Construction Zone B",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  },
  "description": "Crane malfunction during operation",
  "photos": [
    {
      "description": "Malfunctioning crane",
      "file": "[binary photo data]"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "incident-124",
    "incident_type": "equipment_malfunction",
    "severity": "moderate",
    "location": {
      "floor": 4,
      "area": "Construction Zone B",
      "coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060
      }
    },
    "description": "Crane malfunction during operation",
    "reported_by": "user-789",
    "reported_at": "2024-01-15T12:00:00Z",
    "photos": [
      {
        "id": "photo-124",
        "url": "https://api.arxos.com/construction/v1/safety/incidents/incident-124/photos/photo-124",
        "description": "Malfunctioning crane",
        "taken_at": "2024-01-15T12:00:00Z"
      }
    ]
  }
}
```

### Get Safety Alerts
Retrieve real-time safety alerts for a project.

**Endpoint:** `GET /projects/{project_id}/safety/alerts`

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert-123",
        "type": "weather_warning",
        "severity": "high",
        "title": "Severe Weather Alert",
        "message": "Thunderstorm approaching construction site",
        "location": {
          "coordinates": {
            "latitude": 40.7128,
            "longitude": -74.0060
          }
        },
        "created_at": "2024-01-15T14:30:00Z",
        "expires_at": "2024-01-15T18:00:00Z"
      }
    ],
    "active_alerts": 2,
    "last_updated": "2024-01-15T14:30:00Z"
  }
}
```

---

## Cost Tracking API

### Get Project Costs
Retrieve cost tracking data for a specific project.

**Endpoint:** `GET /projects/{project_id}/costs`

**Query Parameters:**
- `category` (optional): Filter by cost category
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `status` (optional): Filter by approval status
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "costs": [
      {
        "id": "cost-123",
        "category": "materials",
        "description": "Concrete for foundation",
        "amount": 150000.00,
        "date": "2024-01-15",
        "approved_by": "user-123",
        "status": "approved",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "summary": {
      "total_budget": 25000000.00,
      "total_spent": 8500000.00,
      "total_approved": 9000000.00,
      "total_pending": 500000.00,
      "budget_remaining": 16500000.00,
      "budget_utilization": 34.0
    },
    "pagination": {
      "total": 150,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### Add Cost Entry
Add a new cost entry to the project.

**Endpoint:** `POST /projects/{project_id}/costs`

**Request Body:**
```json
{
  "category": "labor",
  "description": "Electrical contractor work - Week 3",
  "amount": 25000.00,
  "date": "2024-01-20",
  "notes": "Additional electrical work required for floor 3"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "cost-124",
    "category": "labor",
    "description": "Electrical contractor work - Week 3",
    "amount": 25000.00,
    "date": "2024-01-20",
    "status": "pending",
    "notes": "Additional electrical work required for floor 3",
    "created_at": "2024-01-20T10:30:00Z"
  }
}
```

### Approve Cost
Approve a cost entry.

**Endpoint:** `PUT /projects/{project_id}/costs/{cost_id}/approve`

**Request Body:**
```json
{
  "notes": "Approved - within budget and necessary for project timeline"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "cost-124",
    "status": "approved",
    "approved_by": "user-123",
    "approved_at": "2024-01-20T14:00:00Z",
    "notes": "Approved - within budget and necessary for project timeline"
  }
}
```

---

## Reporting API

### Get Project Report
Generate a comprehensive project report.

**Endpoint:** `GET /projects/{project_id}/reports/overview`

**Query Parameters:**
- `start_date` (optional): Report start date (YYYY-MM-DD)
- `end_date` (optional): Report end date (YYYY-MM-DD)
- `include_details` (optional): Include detailed breakdown (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "schedule": {
      "total_tasks": 150,
      "completed_tasks": 45,
      "in_progress_tasks": 30,
      "pending_tasks": 75,
      "completion_percentage": 30.0,
      "days_ahead": 5,
      "days_behind": 0
    },
    "safety": {
      "total_incidents": 2,
      "minor_incidents": 1,
      "moderate_incidents": 1,
      "major_incidents": 0,
      "days_since_last_incident": 15,
      "safety_score": 95.0
    },
    "costs": {
      "total_budget": 25000000.00,
      "total_spent": 8500000.00,
      "budget_utilization": 34.0,
      "cost_variance": 500000.00,
      "cost_variance_percentage": 2.0
    },
    "quality": {
      "total_inspections": 25,
      "passed_inspections": 23,
      "failed_inspections": 2,
      "pass_rate": 92.0,
      "open_issues": 5,
      "resolved_issues": 20
    },
    "documents": {
      "total_documents": 75,
      "recent_uploads": 15,
      "pending_reviews": 3
    },
    "generated_at": "2024-01-31T23:59:59Z"
  }
}
```

### Get Safety Report
Generate a detailed safety report.

**Endpoint:** `GET /projects/{project_id}/reports/safety`

**Query Parameters:**
- `start_date` (optional): Report start date (YYYY-MM-DD)
- `end_date` (optional): Report end date (YYYY-MM-DD)
- `include_incidents` (optional): Include incident details (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "summary": {
      "total_incidents": 2,
      "incident_rate": 0.13,
      "safety_score": 95.0,
      "days_without_incident": 15
    },
    "incidents_by_type": [
      {
        "type": "slip_and_fall",
        "count": 1,
        "percentage": 50.0
      },
      {
        "type": "equipment_malfunction",
        "count": 1,
        "percentage": 50.0
      }
    ],
    "incidents_by_severity": [
      {
        "severity": "minor",
        "count": 1,
        "percentage": 50.0
      },
      {
        "severity": "moderate",
        "count": 1,
        "percentage": 50.0
      }
    ],
    "trends": {
      "monthly_incidents": [2, 1, 0, 1, 2, 1, 0],
      "safety_score_trend": [92, 94, 95, 93, 95, 96, 95]
    },
    "recommendations": [
      "Increase safety training frequency",
      "Install additional safety equipment",
      "Review equipment maintenance schedule"
    ],
    "generated_at": "2024-01-31T23:59:59Z"
  }
}
```

### Get Cost Report
Generate a detailed cost report.

**Endpoint:** `GET /projects/{project_id}/reports/costs`

**Query Parameters:**
- `start_date` (optional): Report start date (YYYY-MM-DD)
- `end_date` (optional): Report end date (YYYY-MM-DD)
- `include_breakdown` (optional): Include cost breakdown (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "summary": {
      "total_budget": 25000000.00,
      "total_spent": 8500000.00,
      "total_approved": 9000000.00,
      "total_pending": 500000.00,
      "budget_remaining": 16500000.00,
      "budget_utilization": 34.0,
      "cost_variance": 500000.00,
      "cost_variance_percentage": 2.0
    },
    "costs_by_category": [
      {
        "category": "materials",
        "amount": 4000000.00,
        "percentage": 47.1
      },
      {
        "category": "labor",
        "amount": 3000000.00,
        "percentage": 35.3
      },
      {
        "category": "equipment",
        "amount": 1000000.00,
        "percentage": 11.8
      },
      {
        "category": "overhead",
        "amount": 500000.00,
        "percentage": 5.9
      }
    ],
    "monthly_trends": [
      {
        "month": "2024-01",
        "planned": 8000000.00,
        "actual": 8500000.00,
        "variance": 500000.00
      }
    ],
    "forecast": {
      "estimated_completion_cost": 24000000.00,
      "estimated_variance": -1000000.00,
      "confidence_level": 85.0
    },
    "generated_at": "2024-01-31T23:59:59Z"
  }
}
```

---

## WebSocket API

### Real-time Updates
Connect to WebSocket for real-time project updates.

**Endpoint:** `WS /projects/{project_id}/ws`

**Connection:**
```javascript
const ws = new WebSocket('wss://api.arxos.com/construction/v1/projects/project-123/ws');
```

**Message Types:**

#### Project Update
```json
{
  "type": "project_update",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "field": "status",
    "old_value": "in_progress",
    "new_value": "completed",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Task Update
```json
{
  "type": "task_update",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "task-123",
    "field": "progress",
    "old_value": 50.0,
    "new_value": 75.0,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Safety Alert
```json
{
  "type": "safety_alert",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "alert_id": "alert-123",
    "type": "weather_warning",
    "severity": "high",
    "title": "Severe Weather Alert",
    "message": "Thunderstorm approaching construction site",
    "timestamp": "2024-01-15T14:30:00Z"
  }
}
```

#### Cost Update
```json
{
  "type": "cost_update",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "cost_id": "cost-123",
    "field": "status",
    "old_value": "pending",
    "new_value": "approved",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Standard Rate Limit**: 1000 requests per hour per user
- **Burst Rate Limit**: 100 requests per minute per user
- **Document Upload**: 50 uploads per hour per user
- **WebSocket Connections**: 10 concurrent connections per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640995200
```

---

## SDK Examples

### JavaScript/TypeScript SDK

```javascript
// Install SDK
npm install @arxos/construction-sdk

// Initialize client
import { ConstructionClient } from '@arxos/construction-sdk';

const client = new ConstructionClient({
  baseUrl: 'https://api.arxos.com/construction/v1',
  token: 'your-jwt-token'
});

// Get projects
const projects = await client.projects.list({
  status: 'in_progress',
  limit: 20
});

// Create project
const project = await client.projects.create({
  name: 'Downtown Office Complex',
  description: 'Modern office building with 20 floors',
  start_date: '2024-01-15',
  end_date: '2025-06-30',
  budget: 25000000.00
});

// Upload document
const document = await client.documents.upload(project.id, {
  file: fileData,
  name: 'Building Plans',
  type: 'blueprint'
});

// Real-time updates
client.websocket.connect(project.id, {
  onProjectUpdate: (update) => console.log('Project updated:', update),
  onSafetyAlert: (alert) => console.log('Safety alert:', alert)
});
```

### Python SDK

```python
# Install SDK
pip install arxos-construction-sdk

# Initialize client
from arxos_construction import ConstructionClient

client = ConstructionClient(
    base_url='https://api.arxos.com/construction/v1',
    token='your-jwt-token'
)

# Get projects
projects = client.projects.list(
    status='in_progress',
    limit=20
)

# Create project
project = client.projects.create({
    'name': 'Downtown Office Complex',
    'description': 'Modern office building with 20 floors',
    'start_date': '2024-01-15',
    'end_date': '2025-06-30',
    'budget': 25000000.00
})

# Upload document
document = client.documents.upload(
    project_id=project['id'],
    file_path='building_plans.pdf',
    name='Building Plans',
    type='blueprint'
)

# Real-time updates
def on_project_update(update):
    print(f"Project updated: {update}")

def on_safety_alert(alert):
    print(f"Safety alert: {alert}")

client.websocket.connect(
    project_id=project.id,
    on_project_update=on_project_update,
    on_safety_alert=on_safety_alert
)
```

---

## Support

For API support and questions:

- **Documentation**: https://docs.arxos.com/construction-api
- **SDK Documentation**: https://docs.arxos.com/construction-sdk
- **API Status**: https://status.arxos.com
- **Support Email**: construction-api@arxos.com
- **Developer Community**: https://community.arxos.com

**Created:** $(date)
**Status:** API Reference Complete
**Version:** 1.0.0
**Next Steps:** Implementation and testing 