# ArxOS IfcOpenShell Service API Documentation

## Overview

The ArxOS IfcOpenShell Service provides comprehensive IFC (Industry Foundation Classes) processing capabilities including parsing, validation, spatial queries, and performance monitoring. This service is designed for production use with enterprise-grade features.

## Base URL

- **Development**: `http://localhost:5000`
- **Production**: `http://ifcopenshell-service:5000`
- **Load Balanced**: `http://nginx/api/ifcopenshell/`

## Authentication

The service supports JWT-based authentication for production deployments.

### Headers

```http
Authorization: Bearer <jwt_token>
Content-Type: application/octet-stream
```

### Environment Configuration

```bash
IFC_AUTH_ENABLED=true
IFC_JWT_SECRET=your_secure_jwt_secret_key
```

## API Endpoints

### Health Check

#### GET /health

Basic health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "ifcopenshell",
  "version": "0.8.3",
  "timestamp": "2024-01-01T00:00:00Z",
  "cache_enabled": true,
  "max_file_size_mb": 200
}
```

#### GET /api/monitoring/health

Detailed health check with service status and metrics.

**Response**:
```json
{
  "status": "healthy",
  "service": "ifcopenshell",
  "version": "0.8.3",
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime_seconds": 3600,
  "performance": {
    "requests_total": 150,
    "requests_per_second": 2.5,
    "error_rate": 0.02,
    "processing_time_p95": 1.2
  },
  "cache": {
    "hits": 100,
    "misses": 50,
    "hit_rate_percent": 66.67,
    "redis_connected": true
  },
  "errors": {
    "total_errors": 3,
    "error_counts": {
      "IFCParseError": 2,
      "ValidationError": 1
    }
  },
  "configuration": {
    "max_file_size_mb": 200,
    "cache_enabled": true,
    "cache_ttl_seconds": 7200
  }
}
```

### IFC Processing

#### POST /api/parse

Parse an IFC file and extract entity information.

**Request**:
- **Method**: POST
- **Content-Type**: application/octet-stream
- **Body**: Raw IFC file data (max 200MB)

**Response**:
```json
{
  "success": true,
  "buildings": 1,
  "spaces": 25,
  "equipment": 15,
  "walls": 40,
  "doors": 8,
  "windows": 12,
  "total_entities": 101,
  "metadata": {
    "ifc_version": "IFC4",
    "file_size": 5242880,
    "processing_time": "2.345s",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "IFC_PARSE_ERROR",
    "message": "Failed to parse IFC file: Invalid IFC format",
    "details": {
      "file_size": 5242880,
      "ifcopenshell_version": "0.8.3",
      "suggestions": [
        "Try re-exporting the IFC file from your CAD software",
        "Ensure the IFC file is compatible with IFC4 format"
      ]
    },
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /api/validate

Validate an IFC file for compliance and errors.

**Request**:
- **Method**: POST
- **Content-Type**: application/octet-stream
- **Body**: Raw IFC file data (max 200MB)

**Response**:
```json
{
  "success": true,
  "valid": true,
  "warnings": [
    "No spaces found in IFC file",
    "IFC version IFC2X3 may not be fully supported"
  ],
  "errors": [],
  "compliance": {
    "buildingSMART": true,
    "IFC4": false,
    "spatial_consistency": true,
    "data_integrity": true
  },
  "metadata": {
    "ifc_version": "IFC2X3",
    "file_size": 5242880,
    "processing_time": "3.456s",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "entity_counts": {
    "IfcBuilding": 1,
    "IfcSpace": 0,
    "IfcWall": 40,
    "IfcDoor": 8,
    "IfcWindow": 12
  },
  "spatial_issues": [],
  "schema_issues": []
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "IFC_VALIDATION_ERROR",
    "message": "Validation failed: Invalid IFC schema",
    "details": {
      "file_size": 5242880,
      "guidance": [
        "Ensure the IFC file follows buildingSMART standards",
        "Check spatial relationships and containment hierarchy"
      ]
    },
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Spatial Operations

#### POST /api/spatial/query

Perform spatial queries on IFC data.

**Request**:
- **Method**: POST
- **Content-Type**: application/octet-stream
- **Body**: Raw IFC file data + JSON query parameters

**Query Types**:

##### Within Bounds Query

```json
{
  "operation": "within_bounds",
  "bounds": {
    "min": [0, 0, 0],
    "max": [100, 100, 100]
  }
}
```

**Response**:
```json
{
  "success": true,
  "query_type": "within_bounds",
  "bounds": {
    "min": [0, 0, 0],
    "max": [100, 100, 100]
  },
  "results": [
    {
      "global_id": "0x1234567890abcdef",
      "name": "Office Space 101",
      "type": "IfcSpace",
      "coordinates": [[10, 10, 0], [20, 20, 0]],
      "center": [15, 15, 0]
    }
  ],
  "total_found": 1,
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "entity_types_searched": ["IfcSpace", "IfcWall", "IfcSlab"]
  }
}
```

##### Proximity Query

```json
{
  "operation": "proximity",
  "center": [50, 50, 0],
  "radius": 25.0
}
```

**Response**:
```json
{
  "success": true,
  "query_type": "proximity",
  "center": [50, 50, 0],
  "radius": 25.0,
  "results": [
    {
      "global_id": "0x2345678901bcdefg",
      "name": "Meeting Room A",
      "type": "IfcSpace",
      "center": [45, 45, 0],
      "distance": 7.07
    }
  ],
  "total_found": 1,
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

##### Spatial Relationships Query

```json
{
  "operation": "spatial_relationships",
  "entity_id": "0x1234567890abcdef"
}
```

**Response**:
```json
{
  "success": true,
  "query_type": "spatial_relationships",
  "entity_id": "0x1234567890abcdef",
  "entity_type": "IfcSpace",
  "relationships": {
    "contained_in": [
      {
        "global_id": "0x3456789012cdefgh",
        "name": "Ground Floor",
        "type": "IfcBuildingStorey"
      }
    ],
    "contains": [],
    "adjacent_to": [
      {
        "global_id": "0x4567890123defghi",
        "name": "Corridor",
        "type": "IfcSpace"
      }
    ],
    "overlaps_with": []
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

##### Spatial Statistics Query

```json
{
  "operation": "statistics"
}
```

**Response**:
```json
{
  "success": true,
  "query_type": "spatial_statistics",
  "statistics": {
    "total_entities": 101,
    "entity_counts": {
      "IfcSpace": 25,
      "IfcWall": 40,
      "IfcSlab": 15,
      "IfcBeam": 8,
      "IfcColumn": 12,
      "IfcDoor": 8,
      "IfcWindow": 12,
      "IfcBuildingStorey": 3
    },
    "spatial_coverage": {
      "width": 100.0,
      "height": 50.0,
      "depth": 20.0,
      "area": 5000.0,
      "volume": 100000.0
    },
    "bounding_box": {
      "min": [0, 0, 0],
      "max": [100, 50, 20]
    },
    "spatial_density": 0.00101
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /api/spatial/bounds

Get spatial bounds and coverage information for an IFC model.

**Request**:
- **Method**: POST
- **Content-Type**: application/octet-stream
- **Body**: Raw IFC file data

**Response**:
```json
{
  "success": true,
  "bounding_box": {
    "min": [0, 0, 0],
    "max": [100, 50, 20]
  },
  "spatial_coverage": {
    "width": 100.0,
    "height": 50.0,
    "depth": 20.0,
    "area": 5000.0,
    "volume": 100000.0
  },
  "entity_counts": {
    "IfcBuilding": 1,
    "IfcSpace": 25,
    "IfcWall": 40,
    "IfcDoor": 8,
    "IfcWindow": 12
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "total_entities": 86
  }
}
```

### Monitoring and Metrics

#### GET /metrics

Get service metrics and performance data.

**Response**:
```json
{
  "success": true,
  "service": "ifcopenshell",
  "timestamp": "2024-01-01T00:00:00Z",
  "cache_stats": {
    "hits": 150,
    "misses": 75,
    "sets": 100,
    "evictions": 5,
    "hit_rate_percent": 66.67,
    "local_cache_size": 25,
    "redis_connected": true
  },
  "performance_metrics": {
    "uptime_seconds": 3600,
    "requests_total": 225,
    "requests_per_second": 0.0625,
    "error_rate": 0.02,
    "requests_by_endpoint": {
      "parse": {
        "total": 100,
        "success": 98,
        "errors": 2,
        "avg_time": 2.5
      },
      "validate": {
        "total": 75,
        "success": 75,
        "errors": 0,
        "avg_time": 3.2
      }
    },
    "processing_time_percentiles": {
      "p50": 2.1,
      "p90": 4.5,
      "p95": 6.2,
      "p99": 8.9
    },
    "memory_usage": [
      {
        "timestamp": 1704067200,
        "rss": 524288000,
        "vms": 1073741824
      }
    ]
  },
  "configuration": {
    "max_file_size_mb": 200,
    "cache_ttl_seconds": 7200,
    "cache_enabled": true
  }
}
```

#### GET /api/monitoring/stats

Get detailed service statistics.

**Response**:
```json
{
  "success": true,
  "service": "ifcopenshell",
  "timestamp": "2024-01-01T00:00:00Z",
  "performance_metrics": {
    "uptime_seconds": 3600,
    "requests_total": 225,
    "requests_per_second": 0.0625,
    "error_rate": 0.02,
    "requests_by_endpoint": {
      "parse": {
        "total": 100,
        "success": 98,
        "errors": 2,
        "avg_time": 2.5
      }
    },
    "processing_time_percentiles": {
      "p50": 2.1,
      "p90": 4.5,
      "p95": 6.2,
      "p99": 8.9
    }
  },
  "cache_statistics": {
    "hits": 150,
    "misses": 75,
    "hit_rate_percent": 66.67,
    "redis_connected": true
  },
  "error_statistics": {
    "total_errors": 5,
    "error_counts": {
      "IFCParseError": 3,
      "ValidationError": 2
    },
    "error_rate": 0.02
  },
  "system_info": {
    "python_version": "3.9+",
    "ifcopenshell_version": "0.8.3",
    "flask_version": "2.3.3"
  }
}
```

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional_info": "value",
      "suggestions": ["Helpful suggestion 1", "Helpful suggestion 2"]
    },
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `NO_DATA` | No IFC data provided | 400 |
| `FILE_TOO_LARGE` | File exceeds size limit | 413 |
| `IFC_PARSE_ERROR` | IFC parsing failed | 400 |
| `IFC_VALIDATION_ERROR` | IFC validation failed | 400 |
| `SPATIAL_QUERY_ERROR` | Spatial query failed | 400 |
| `CACHE_ERROR` | Cache operation failed | 500 |
| `CONFIGURATION_ERROR` | Configuration error | 500 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `VALIDATION_ERROR` | General validation error | 500 |
| `METRICS_ERROR` | Metrics collection failed | 500 |

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad Request (client error) |
| 401 | Unauthorized (authentication required) |
| 413 | Payload Too Large (file size limit) |
| 500 | Internal Server Error |

## Rate Limiting

The service implements rate limiting to prevent abuse:

- **API Endpoints**: 10 requests per second
- **IFC Processing**: 5 requests per second
- **Burst Allowance**: Temporary spikes allowed

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
```

## Caching

The service uses Redis for caching with the following behavior:

- **Parse Results**: Cached for 2 hours (7200 seconds)
- **Validation Results**: Cached for 2 hours
- **Spatial Queries**: Cached for 1 hour (3600 seconds)
- **Cache Key**: MD5 hash of file data + operation type

Cache status is included in responses:

```json
{
  "cache_hit": true,
  "cache_key": "ifc:parse:abc123def456",
  "cache_ttl": 7200
}
```

## Performance Considerations

### File Size Limits

- **Maximum File Size**: 200MB
- **Recommended Size**: <50MB for optimal performance
- **Processing Time**: Typically 1-5 seconds for files <10MB

### Memory Usage

- **Base Memory**: ~500MB
- **Per Request**: ~50MB additional
- **Peak Memory**: ~2GB for large files

### Concurrent Requests

- **Recommended**: 10-20 concurrent requests
- **Maximum**: 50 concurrent requests
- **Scaling**: Horizontal scaling recommended for higher loads

## Examples

### Python Client Example

```python
import requests
import json

# Parse IFC file
with open('building.ifc', 'rb') as f:
    ifc_data = f.read()

response = requests.post(
    'http://localhost:5000/api/parse',
    data=ifc_data,
    headers={'Content-Type': 'application/octet-stream'}
)

result = response.json()
print(f"Found {result['total_entities']} entities")

# Validate IFC file
response = requests.post(
    'http://localhost:5000/api/validate',
    data=ifc_data,
    headers={'Content-Type': 'application/octet-stream'}
)

result = response.json()
print(f"Validation: {'Valid' if result['valid'] else 'Invalid'}")
print(f"Warnings: {len(result['warnings'])}")
print(f"Errors: {len(result['errors'])}")

# Spatial query
query_params = {
    "operation": "within_bounds",
    "bounds": {"min": [0, 0, 0], "max": [100, 100, 100]}
}

response = requests.post(
    'http://localhost:5000/api/spatial/query',
    data=ifc_data,
    headers={'Content-Type': 'application/octet-stream'},
    json=query_params
)

result = response.json()
print(f"Found {result['total_found']} entities within bounds")
```

### cURL Examples

```bash
# Parse IFC file
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @building.ifc \
  http://localhost:5000/api/parse

# Validate IFC file
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @building.ifc \
  http://localhost:5000/api/validate

# Get service health
curl http://localhost:5000/health

# Get metrics
curl http://localhost:5000/metrics
```

### JavaScript Client Example

```javascript
// Parse IFC file
async function parseIFC(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/parse', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// Validate IFC file
async function validateIFC(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/validate', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// Usage
const fileInput = document.getElementById('ifc-file');
fileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  
  const parseResult = await parseIFC(file);
  console.log('Parse result:', parseResult);
  
  const validateResult = await validateIFC(file);
  console.log('Validation result:', validateResult);
});
```

## Support

For technical support and questions:

- **Documentation**: https://docs.arxos.com/ifcopenshell
- **API Reference**: https://api.arxos.com/docs
- **Support Email**: support@arxos.com
- **Issue Tracking**: https://github.com/arx-os/arxos/issues

---

**Last Updated**: 2024-01-01  
**API Version**: 1.0.0  
**Service Version**: 0.8.3
