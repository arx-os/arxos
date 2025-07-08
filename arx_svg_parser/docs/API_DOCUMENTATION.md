# Arxos SVG-BIM API Documentation

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Authentication](#authentication)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Python 3.8+
- FastAPI
- Uvicorn (for server)
- Required dependencies (see requirements.txt)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start the API Server
```bash
# Development server
uvicorn arx_svg_parser.api.api_layer:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn arx_svg_parser.api.api_layer:app --host 0.0.0.0 --port 8000
```

## Quick Start

### 1. Basic BIM Assembly
```python
import requests

# Assemble BIM from SVG
response = requests.post("http://localhost:8000/bim/assemble", json={
    "svg_data": "<svg>...</svg>",
    "user_id": "user123",
    "project_id": "project456"
})

model_id = response.json()["model_id"]
print(f"BIM Model ID: {model_id}")
```

### 2. Query BIM Model
```python
# Query rooms in the model
response = requests.post("http://localhost:8000/bim/query", json={
    "model_id": model_id,
    "user_id": "user123",
    "project_id": "project456",
    "query": {"type": "room"}
})

rooms = response.json()["results"]
print(f"Found {len(rooms)} rooms")
```

### 3. Export BIM Model
```python
# Export to JSON
response = requests.post("http://localhost:8000/bim/export", json={
    "model_id": model_id,
    "user_id": "user123",
    "project_id": "project456",
    "format": "json"
})

bim_data = response.json()["data"]
```

## API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
All endpoints require authentication via JWT tokens in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Endpoints

#### 1. BIM Assembly
**POST** `/bim/assemble`

Assembles a BIM model from SVG data.

**Request Body:**
```json
{
    "svg_data": "<svg>...</svg>",
    "user_id": "string",
    "project_id": "string",
    "metadata": {
        "building_name": "string",
        "floor_number": "integer",
        "description": "string"
    },
    "options": {
        "validate_geometry": true,
        "auto_resolve_conflicts": true,
        "performance_level": "high"
    }
}
```

**Response:**
```json
{
    "success": true,
    "model_id": "string",
    "elements_count": 10,
    "systems_count": 3,
    "spaces_count": 5,
    "relationships_count": 15,
    "warnings": [],
    "processing_time": 1.23
}
```

#### 2. BIM Query
**POST** `/bim/query`

Queries BIM model elements.

**Request Body:**
```json
{
    "model_id": "string",
    "user_id": "string",
    "project_id": "string",
    "query": {
        "type": "room|wall|device|system",
        "properties": {
            "room_type": "office",
            "area_min": 50.0
        },
        "spatial": {
            "bounds": [x1, y1, x2, y2],
            "contains_point": [x, y]
        }
    },
    "options": {
        "include_geometry": true,
        "include_relationships": true,
        "limit": 100
    }
}
```

**Response:**
```json
{
    "success": true,
    "results": [
        {
            "id": "string",
            "type": "room",
            "name": "Office 101",
            "properties": {},
            "geometry": {},
            "relationships": []
        }
    ],
    "total_count": 10,
    "query_time": 0.05
}
```

#### 3. BIM Export
**POST** `/bim/export`

Exports BIM model in various formats.

**Request Body:**
```json
{
    "model_id": "string",
    "user_id": "string",
    "project_id": "string",
    "format": "json|csv|xml|ifc|gbxml",
    "options": {
        "pretty_print": true,
        "include_metadata": true,
        "compression": false
    }
}
```

**Response:**
```json
{
    "success": true,
    "format": "json",
    "data": "string",
    "file_size": 1024,
    "export_time": 0.12
}
```

#### 4. BIM Validation
**POST** `/bim/validate`

Validates BIM model consistency.

**Request Body:**
```json
{
    "model_id": "string",
    "user_id": "string",
    "project_id": "string",
    "validation_rules": {
        "check_geometry": true,
        "check_relationships": true,
        "check_properties": true
    }
}
```

**Response:**
```json
{
    "success": true,
    "valid": true,
    "errors": [],
    "warnings": [],
    "validation_time": 0.08
}
```

#### 5. Health Check
**GET** `/health`

Returns system health status.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "services": {
        "database": "connected",
        "cache": "connected",
        "storage": "available"
    }
}
```

#### 6. Webhook Registration
**POST** `/webhooks/register`

Registers webhook endpoints for events.

**Request Body:**
```json
{
    "url": "https://your-webhook-url.com/events",
    "events": ["bim.assembled", "bim.exported", "bim.validated"],
    "secret": "webhook_secret",
    "user_id": "string"
}
```

**Response:**
```json
{
    "success": true,
    "webhook_id": "string",
    "status": "active"
}
```

#### 7. File Download
**GET** `/files/{file_id}`

Downloads exported files.

**Response:**
```
File content with appropriate Content-Type header
```

## Authentication

### JWT Token Structure
```json
{
    "user_id": "string",
    "project_id": "string",
    "permissions": ["read", "write", "admin"],
    "exp": 1640995200
}
```

### Token Generation
```python
import jwt
from datetime import datetime, timedelta

def generate_token(user_id: str, project_id: str, secret: str):
    payload = {
        "user_id": user_id,
        "project_id": project_id,
        "permissions": ["read", "write"],
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

## Error Handling

### Error Response Format
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid SVG data",
        "details": {
            "field": "svg_data",
            "issue": "Malformed XML"
        }
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes
- `AUTHENTICATION_ERROR`: Invalid or missing token
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND_ERROR`: Resource not found
- `PROCESSING_ERROR`: Internal processing error
- `RATE_LIMIT_ERROR`: Too many requests
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable

### Error Handling Example
```python
import requests

try:
    response = requests.post("http://localhost:8000/bim/assemble", json={
        "svg_data": "<svg>...</svg>",
        "user_id": "user123",
        "project_id": "project456"
    })
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print(f"Success: {result['model_id']}")
        else:
            print(f"Error: {result['error']['message']}")
    else:
        print(f"HTTP Error: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

## Best Practices

### 1. Request Optimization
- Use appropriate batch sizes for large datasets
- Include only necessary fields in queries
- Use pagination for large result sets

### 2. Error Handling
- Always check response status codes
- Implement retry logic for transient errors
- Log errors for debugging

### 3. Performance
- Use connection pooling for multiple requests
- Cache frequently accessed data
- Use compression for large payloads

### 4. Security
- Validate all input data
- Use HTTPS in production
- Implement rate limiting
- Sanitize SVG data

### 5. Monitoring
- Track API usage and performance
- Monitor error rates
- Set up alerts for critical issues

## Examples

### Complete Workflow Example
```python
import requests
import json

class ArxosClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def assemble_bim(self, svg_data: str, user_id: str, project_id: str):
        """Assemble BIM from SVG data."""
        response = requests.post(
            f"{self.base_url}/bim/assemble",
            headers=self.headers,
            json={
                "svg_data": svg_data,
                "user_id": user_id,
                "project_id": project_id
            }
        )
        return response.json()
    
    def query_rooms(self, model_id: str, user_id: str, project_id: str):
        """Query rooms in BIM model."""
        response = requests.post(
            f"{self.base_url}/bim/query",
            headers=self.headers,
            json={
                "model_id": model_id,
                "user_id": user_id,
                "project_id": project_id,
                "query": {"type": "room"}
            }
        )
        return response.json()
    
    def export_model(self, model_id: str, user_id: str, project_id: str, format: str):
        """Export BIM model."""
        response = requests.post(
            f"{self.base_url}/bim/export",
            headers=self.headers,
            json={
                "model_id": model_id,
                "user_id": user_id,
                "project_id": project_id,
                "format": format
            }
        )
        return response.json()

# Usage
client = ArxosClient("http://localhost:8000", "your_token")

# Assemble BIM
svg_data = "<svg>...</svg>"
result = client.assemble_bim(svg_data, "user123", "project456")
model_id = result["model_id"]

# Query rooms
rooms = client.query_rooms(model_id, "user123", "project456")

# Export model
export = client.export_model(model_id, "user123", "project456", "json")
```

### Batch Processing Example
```python
def process_multiple_svgs(svg_files: list, client: ArxosClient):
    """Process multiple SVG files in batch."""
    results = []
    
    for svg_file in svg_files:
        with open(svg_file, 'r') as f:
            svg_data = f.read()
        
        try:
            result = client.assemble_bim(svg_data, "user123", "project456")
            results.append({
                "file": svg_file,
                "success": True,
                "model_id": result["model_id"]
            })
        except Exception as e:
            results.append({
                "file": svg_file,
                "success": False,
                "error": str(e)
            })
    
    return results
```

### Webhook Integration Example
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle webhook events from Arxos API."""
    event = request.json
    
    if event["event"] == "bim.assembled":
        # Handle BIM assembly completion
        model_id = event["data"]["model_id"]
        print(f"BIM model {model_id} assembled successfully")
        
    elif event["event"] == "bim.exported":
        # Handle BIM export completion
        export_id = event["data"]["export_id"]
        print(f"BIM export {export_id} completed")
    
    return {"status": "received"}, 200

if __name__ == "__main__":
    app.run(port=5000)
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
**Problem:** 401 Unauthorized errors
**Solution:** Check token validity and expiration

#### 2. Validation Errors
**Problem:** 400 Bad Request with validation errors
**Solution:** Validate SVG data format and required fields

#### 3. Processing Timeouts
**Problem:** Long processing times for large SVGs
**Solution:** Use batch processing or optimize SVG size

#### 4. Memory Issues
**Problem:** Out of memory errors
**Solution:** Process smaller batches or increase server memory

#### 5. Network Issues
**Problem:** Connection timeouts
**Solution:** Implement retry logic with exponential backoff

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring
Monitor API performance:
```python
import time

start_time = time.time()
response = client.assemble_bim(svg_data, user_id, project_id)
processing_time = time.time() - start_time
print(f"Processing time: {processing_time:.2f} seconds")
```

### Support
For additional support:
- Check the logs for detailed error messages
- Review the API documentation
- Contact the development team with specific error details 