# ARXOS API Reference

## 🎯 **Overview**

The ARXOS API provides a comprehensive REST interface for building information management, ArxObject operations, and real-time collaboration. The API is built with Go and Chi router, following REST principles with JSON responses.

## 🔐 **Authentication**

### **JWT Token Authentication**
All protected endpoints require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### **Token Acquisition**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_here",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "account_type": "professional"
  }
}
```

### **Token Refresh**
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

---

## 🌐 **Base URL & Versioning**

### **Base URL**
```
Development: http://localhost:8080
Production: https://api.arxos.com
```

### **API Versioning**
All endpoints are versioned under `/api/v1/`:
```
/api/v1/arxobjects
/api/v1/buildings
/api/v1/auth
```

---

## 📡 **Core Endpoints**

### **Health & Status**
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ai_service": "connected"
  }
}
```

### **Authentication Endpoints**
```http
POST   /api/v1/auth/login          # User login
POST   /api/v1/auth/logout         # User logout
POST   /api/v1/auth/refresh        # Refresh token
POST   /api/v1/auth/register       # User registration
GET    /api/v1/auth/profile        # Get user profile
PUT    /api/v1/auth/profile        # Update user profile
```

### **ArxObject Endpoints**
```http
GET    /api/v1/arxobjects         # List ArxObjects
POST   /api/v1/arxobjects         # Create ArxObject
GET    /api/v1/arxobjects/{id}    # Get ArxObject by ID
PUT    /api/v1/arxobjects/{id}    # Update ArxObject
DELETE /api/v1/arxobjects/{id}    # Delete ArxObject
GET    /api/v1/arxobjects/{id}/relationships  # Get relationships
POST   /api/v1/arxobjects/{id}/relationships  # Add relationship
```

### **Building Endpoints**
```http
GET    /api/v1/buildings           # List buildings
POST   /api/v1/buildings           # Create building
GET    /api/v1/buildings/{id}      # Get building by ID
PUT    /api/v1/buildings/{id}      # Update building
DELETE /api/v1/buildings/{id}      # Delete building
GET    /api/v1/buildings/{id}/arxobjects  # Get building ArxObjects
```

### **AI Service Endpoints**
```http
POST   /api/v1/ai/ingest          # Ingest PDF/IFC/DWG
GET    /api/v1/ai/status/{job_id} # Get ingestion status
POST   /api/v1/ai/process         # Process building data
GET    /api/v1/ai/models          # List available AI models
```

---

## 📊 **Data Models**

### **ArxObject Model**
```json
{
  "id": "arx_123",
  "type": "electrical_outlet",
  "name": "Receptacle A1",
  "system": "electrical",
  "detail_level": 1,
  "data": {
    "voltage": "120V",
    "amperage": "20A",
    "circuit": "A1",
    "manufacturer": "Leviton"
  },
  "confidence": {
    "classification": 0.95,
    "position": 0.90,
    "properties": 0.85,
    "relationships": 0.80,
    "overall": 0.88
  },
  "geometry": {
    "type": "point",
    "coordinates": [123.45, 67.89, 0.0]
  },
  "relationships": [
    {
      "type": "feeds",
      "target_id": "panel_001",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "source": "pdf",
    "created": "2024-01-15T10:30:00Z",
    "validated": false
  }
}
```

### **Building Model**
```json
{
  "id": "building_456",
  "name": "Main Office Building",
  "address": "123 Business St, City, State",
  "type": "office",
  "floors": 5,
  "area_sqft": 50000,
  "geometry": {
    "type": "polygon",
    "coordinates": [[[x1,y1], [x2,y2], [x3,y3], [x1,y1]]]
  },
  "metadata": {
    "created": "2024-01-15T10:30:00Z",
    "last_modified": "2024-01-15T10:30:00Z"
  }
}
```

---

## 🔍 **Query Parameters**

### **ArxObject Filtering**
```http
GET /api/v1/arxobjects?system=electrical&min_confidence=0.8&limit=50
```

**Available Filters:**
- `system` - Filter by building system (structural, electrical, mechanical, etc.)
- `type` - Filter by ArxObject type
- `min_confidence` - Minimum confidence score (0.0-1.0)
- `max_confidence` - Maximum confidence score (0.0-1.0)
- `detail_level` - Filter by detail level (0-4)
- `validated` - Filter by validation status (true/false)

### **Spatial Queries**
```http
GET /api/v1/arxobjects?bbox=123.4,67.8,123.5,67.9
GET /api/v1/arxobjects?radius=100&center=123.45,67.89
```

**Spatial Parameters:**
- `bbox` - Bounding box (x1,y1,x2,y2)
- `radius` - Search radius in meters
- `center` - Center point (x,y)
- `floor` - Floor level for 3D queries

### **Pagination**
```http
GET /api/v1/arxobjects?page=2&limit=25
```

**Pagination Parameters:**
- `page` - Page number (starts at 1)
- `limit` - Items per page (max 100)
- `offset` - Alternative to page (starts at 0)

---

## 📤 **File Upload**

### **PDF Ingestion**
```http
POST /api/v1/ai/ingest
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <pdf_file>
building_id: building_123
options: {
  "extract_symbols": true,
  "coordinate_system": "auto",
  "confidence_threshold": 0.7
}
```

**Response:**
```json
{
  "job_id": "job_789",
  "status": "processing",
  "estimated_time": 30,
  "message": "PDF uploaded successfully, processing started"
}
```

### **Status Check**
```http
GET /api/v1/ai/status/job_789
```

**Response:**
```json
{
  "job_id": "job_789",
  "status": "completed",
  "progress": 100,
  "result": {
    "arxobjects_created": 45,
    "confidence_avg": 0.87,
    "processing_time": 28.5
  }
}
```

---

## 🔄 **Real-time Updates**

### **WebSocket Connection**
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'arxobject.updated':
      updateArxObject(data.payload);
      break;
    case 'building.changed':
      refreshBuildingView(data.payload);
      break;
    case 'validation.completed':
      showValidationResult(data.payload);
      break;
  }
};
```

### **WebSocket Events**
```json
{
  "type": "arxobject.updated",
  "payload": {
    "id": "arx_123",
    "changes": ["confidence", "geometry"],
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## 📝 **Error Handling**

### **Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid ArxObject data",
    "details": [
      {
        "field": "type",
        "message": "Type is required"
      }
    ],
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123"
  }
}
```

### **HTTP Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### **Common Error Codes**
- `AUTHENTICATION_FAILED` - Invalid credentials
- `TOKEN_EXPIRED` - JWT token expired
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `VALIDATION_ERROR` - Request data validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

## 🚀 **Rate Limiting**

### **Default Limits**
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **Premium**: 5000 requests/hour

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1642248000
```

---

## 📚 **SDK & Examples**

### **JavaScript Example**
```javascript
class ArxosAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }
  
  async getArxObjects(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${this.baseURL}/api/v1/arxobjects?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  async createArxObject(arxObject) {
    const response = await fetch(`${this.baseURL}/api/v1/arxobjects`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(arxObject)
    });
    
    return response.json();
  }
}

// Usage
const api = new ArxosAPI('http://localhost:8080', 'your_token');
const electricalObjects = await api.getArxObjects({ system: 'electrical' });
```

### **Go Example**
```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type ArxosClient struct {
    BaseURL string
    Token   string
    Client  *http.Client
}

func (c *ArxosClient) GetArxObjects(filters map[string]string) ([]ArxObject, error) {
    req, err := http.NewRequest("GET", c.BaseURL+"/api/v1/arxobjects", nil)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Authorization", "Bearer "+c.Token)
    
    resp, err := c.Client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var arxObjects []ArxObject
    if err := json.NewDecoder(resp.Body).Decode(&arxObjects); err != nil {
        return nil, err
    }
    
    return arxObjects, nil
}
```

---

## 🔗 **Related Documentation**

- **Authentication**: See [Security Architecture](../architecture/overview.md#security-architecture)
- **ArxObjects**: Read [ArxObject System](../architecture/arxobjects.md)
- **Development**: Follow [Development Guide](../development/guide.md)
- **Quick Start**: Get started with [Quick Start](../quick-start.md)

---

## 🆘 **Support**

- **API Issues**: Check error responses and status codes
- **Authentication**: Verify JWT token validity and expiration
- **Rate Limits**: Monitor rate limit headers
- **Development**: Use [Development Setup](../development/setup.md) for local testing
