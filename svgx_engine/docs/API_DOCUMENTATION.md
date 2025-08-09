# SVGX Engine API Documentation

## Overview

The SVGX Engine API provides a comprehensive REST interface for parsing, evaluating, simulating, and compiling SVGX content. The API is designed to meet CTO performance targets and provides real-time interactive capabilities.

**Base URL**: `https://svgx-engine.example.com/api/v1`

**Content-Type**: `application/json`

## Authentication

All API requests require authentication using API keys:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://svgx-engine.example.com/api/v1/health
```

## Performance Targets

- **UI Response Time**: < 16ms
- **Redraw Time**: < 32ms
- **Physics Simulation**: < 100ms
- **Batch Processing**: Enabled for non-critical updates

## Endpoints

### Health Check

#### GET /health

Check the health status of the SVGX Engine service.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "performance": {
    "avg_response_time_ms": 12.5,
    "total_requests": 15420,
    "error_rate": 0.02
  }
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy

### Metrics

#### GET /metrics

Get detailed performance metrics and statistics.

**Response**:
```json
{
  "total_requests": 15420,
  "avg_response_time_ms": 12.5,
  "error_rate": 0.02,
  "cache_stats": {
    "hits": 12340,
    "misses": 3080,
    "hit_rate": 0.80
  },
  "performance_targets": {
    "ui_response_time_ms": 16,
    "redraw_time_ms": 32,
    "physics_simulation_ms": 100
  }
}
```

### Parse SVGX

#### POST /parse

Parse SVGX content and return structured elements.

**Request**:
```json
{
  "content": "<svgx><circle id=\"test\" cx=\"100\" cy=\"100\" r=\"50\"/></svgx>",
  "options": {
    "validate": true,
    "include_metadata": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "elements": [
    {
      "id": "test",
      "type": "circle",
      "attributes": {
        "cx": "100",
        "cy": "100",
        "r": "50"
      },
      "behaviors": [],
      "metadata": {
        "line_number": 1,
        "column_number": 10
      }
    }
  ],
  "statistics": {
    "total_elements": 1,
    "parse_time_ms": 8.5
  }
}
```

**Status Codes**:
- `200 OK`: Parsing successful
- `400 Bad Request`: Invalid SVGX content
- `422 Unprocessable Entity`: Validation errors

### Evaluate Behaviors

#### POST /evaluate

Evaluate behaviors and interactions in SVGX content.

**Request**:
```json
{
  "content": "<svgx><circle id=\"test\" cx=\"100\" cy=\"100\" r=\"50\"><behavior><on-click><set-attribute name=\"fill\" value=\"blue\"/></on-click></behavior></circle></svgx>",
  "options": {
    "interactive": true,
    "include_physics": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "behaviors": [
    {
      "element_id": "test",
      "event_type": "click",
      "actions": [
        {
          "type": "set_attribute",
          "name": "fill",
          "value": "blue"
        }
      ]
    }
  ],
  "physics": {
    "gravity_enabled": false,
    "collision_detection": false
  },
  "statistics": {
    "evaluation_time_ms": 15.2
  }
}
```

### Simulate Physics

#### POST /simulate

Run physics simulation on SVGX content.

**Request**:
```json
{
  "content": "<svgx><circle id=\"ball\" cx=\"100\" cy=\"100\" r=\"20\" mass=\"1.0\"/></svgx>",
  "options": {
    "duration": 2.0,
    "gravity": true,
    "collisions": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "simulation": {
    "duration": 2.0,
    "frames": [
      {
        "time": 0.0,
        "elements": [
          {
            "id": "ball",
            "position": {"x": 100, "y": 100},
            "velocity": {"x": 0, "y": 0}
          }
        ]
      }
    ],
    "statistics": {
      "total_frames": 120,
      "collision_count": 0,
      "simulation_time_ms": 85.3
    }
  }
}
```

### Interactive Operations

#### POST /interactive

Handle interactive operations like clicks, drags, and hovers.

**Request**:
```json
{
  "operation": "click",
  "element_id": "test-circle",
  "coordinates": {
    "x": 100,
    "y": 100
  },
  "modifiers": {
    "ctrl": false,
    "shift": false,
    "alt": false
  }
}
```

**Response**:
```json
{
  "success": true,
  "operation": "click",
  "element_id": "test-circle",
  "result": {
    "attributes_changed": [
      {
        "name": "fill",
        "old_value": "red",
        "new_value": "blue"
      }
    ],
    "behaviors_triggered": 1
  },
  "state": {
    "selected_elements": ["test-circle"],
    "hovered_element": null
  }
}
```

**Supported Operations**:
- `click`: Mouse click on element
- `drag_start`: Start dragging element
- `drag_move`: Continue dragging
- `drag_end`: End dragging
- `hover`: Mouse hover over element
- `select`: Select element
- `deselect`: Deselect element

### Precision Management

#### POST /precision

Set precision level for coordinate calculations.

**Request**:
```json
{
  "level": "compute",
  "coordinates": {
    "x": 100.123456,
    "y": 200.789012
  }
}
```

**Response**:
```json
{
  "success": true,
  "level": "compute",
  "coordinates": {
    "x": 100.123456,
    "y": 200.789012
  },
  "precision_info": {
    "decimal_places": 6,
    "fixed_point": true
  }
}
```

**Precision Levels**:
- `ui`: UI-level precision (2 decimal places)
- `edit`: Edit-level precision (4 decimal places)
- `compute`: Compute-level precision (6 decimal places)

### Get Interactive State

#### GET /state

Get current interactive state.

**Response**:
```json
{
  "selected_elements": ["element1", "element2"],
  "hovered_element": "element3",
  "drag_state": {
    "active": false,
    "element_id": null,
    "start_coordinates": null
  },
  "constraints": [
    {
      "type": "distance",
      "elements": ["element1", "element2"],
      "value": 100.0
    }
  ],
  "precision_level": "ui"
}
```

### Compile to SVG

#### POST /compile/svg

Compile SVGX content to standard SVG.

**Request**:
```json
{
  "content": "<svgx><circle id=\"test\" cx=\"100\" cy=\"100\" r=\"50\"/></svgx>",
  "options": {
    "format": "svg",
    "include_styles": true,
    "optimize": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "output": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"200\" height=\"200\"><circle id=\"test\" cx=\"100\" cy=\"100\" r=\"50\" fill=\"red\"/></svg>",
  "statistics": {
    "compilation_time_ms": 12.8,
    "output_size_bytes": 156
  }
}
```

### Compile to JSON

#### POST /compile/json

Compile SVGX content to JSON representation.

**Request**:
```json
{
  "content": "<svgx><circle id=\"test\" cx=\"100\" cy=\"100\" r=\"50\"/></svgx>",
  "options": {
    "format": "json",
    "include_metadata": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "output": {
    "type": "svgx",
    "elements": [
      {
        "id": "test",
        "type": "circle",
        "attributes": {
          "cx": "100",
          "cy": "100",
          "r": "50"
        }
      }
    ],
    "metadata": {
      "version": "1.0",
      "compiled_at": "2024-01-15T10:30:00Z"
    }
  },
  "statistics": {
    "compilation_time_ms": 8.2,
    "output_size_bytes": 245
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "PARSE_ERROR",
    "message": "Invalid SVGX syntax at line 2, column 15",
    "details": {
      "line": 2,
      "column": 15,
      "context": "<invalid-tag>"
    }
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Input validation failed | 400 |
| `PARSE_ERROR` | SVGX parsing failed | 400 |
| `RUNTIME_ERROR` | Runtime execution error | 500 |
| `PERFORMANCE_ERROR` | Performance target exceeded | 500 |
| `SECURITY_ERROR` | Security validation failed | 403 |
| `COMPILATION_ERROR` | Compilation failed | 500 |
| `DATABASE_ERROR` | Database operation failed | 500 |
| `SERVICE_ERROR` | Service unavailable | 503 |

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default**: 1000 requests per minute per API key
- **Burst**: Up to 100 requests per second
- **Headers**: Rate limit information included in response headers

```bash
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642234560
```

## Caching

The API supports caching for improved performance:

- **Cache-Control**: `max-age=3600` for GET requests
- **ETag**: Entity tags for conditional requests
- **Cache Keys**: Based on content hash and options

## WebSocket Support

For real-time interactive features, WebSocket connections are available:

```javascript
const ws = new WebSocket('wss://svgx-engine.example.com/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

## SDK Examples

### Python SDK

```python
from svgx_engine import SVGXEngine

engine = SVGXEngine(api_key="YOUR_API_KEY")

# Parse SVGX
result = engine.parse(svgx_content)
print(f"Parsed {len(result.elements)} elements")

# Evaluate behaviors
behaviors = engine.evaluate(svgx_content, interactive=True)
print(f"Found {len(behaviors)} behaviors")

# Interactive operation
response = engine.interactive("click", "element-id", x=100, y=100)
print(f"Changed {len(response.attributes_changed)} attributes")
```

### JavaScript SDK

```javascript
import { SVGXEngine } from '@svgx/engine';

const engine = new SVGXEngine({ apiKey: 'YOUR_API_KEY' });

// Parse SVGX
const result = await engine.parse(svgxContent);
console.log(`Parsed ${result.elements.length} elements`);

// Interactive operation
const response = await engine.interactive('click', 'element-id', {
  x: 100,
  y: 100
});
console.log(`Changed ${response.attributesChanged.length} attributes`);
```

## Performance Monitoring

### Metrics Endpoint

The `/metrics` endpoint provides detailed performance metrics:

- Request counts and rates
- Response time percentiles
- Error rates and types
- Cache hit rates
- Resource utilization

### Health Checks

Health checks verify:

- Service availability
- Database connectivity
- Cache functionality
- Performance targets
- Security status

## Security

### Input Validation

All inputs are validated for:

- SVGX syntax compliance
- Security vulnerabilities
- Resource limits
- Malicious content

### Authentication

- API key authentication required
- Rate limiting per API key
- Request logging and auditing
- IP-based restrictions (optional)

### CORS

Cross-Origin Resource Sharing is configured for:

- Allowed origins
- Allowed methods
- Allowed headers
- Credentials support

## Deployment

### Docker

```bash
docker run -p 8000:8000 svgx-engine:latest
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATABASE_URL` | Database connection URL | `sqlite:///app/data/svgx_engine.db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `API_KEY` | API authentication key | Required |
| `TELEMETRY_ENABLED` | Enable telemetry | `true` |
| `CACHE_ENABLED` | Enable caching | `true` |
| `PERFORMANCE_MONITORING` | Enable performance monitoring | `true` |
| `SECURITY_AUDITING` | Enable security auditing | `true` |

## Support

For API support and questions:

- **Documentation**: https://docs.svgx-engine.com
- **GitHub**: https://github.com/svgx-engine
- **Email**: api-support@svgx-engine.com
- **Slack**: #svgx-engine-api

## Changelog

### v1.0.0 (2024-01-15)

- Initial API release
- Core parsing and evaluation
- Interactive operations
- Physics simulation
- Compilation to SVG/JSON
- Performance monitoring
- Security features
- Comprehensive documentation
