# SVGX Engine API Integration Guide

## Overview

The SVGX Engine provides a comprehensive API for real-time collaborative SVG editing, user management, and system monitoring. This guide covers all aspects of integrating with the SVGX Engine API.

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
3. [WebSocket Integration](#websocket-integration)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Code Examples](#code-examples)
7. [Best Practices](#best-practices)
8. [Testing](#testing)

## Authentication

### JWT Authentication

The SVGX Engine uses JWT (JSON Web Tokens) for authentication. All API endpoints except login and health checks require authentication.

#### Login Process

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "user_id": "user_123",
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "editor",
    "permissions": ["read", "write", "edit"],
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T12:00:00Z"
  }
}
```

#### Using Access Tokens

Include the access token in the Authorization header:

```bash
curl -X GET http://localhost:8000/runtime/canvases/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Token Refresh

When the access token expires, use the refresh token to get a new one:

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Role-Based Access Control

The SVGX Engine supports three user roles:

- **Admin**: Full system access, user management, system configuration
- **Editor**: Create, edit, and manage canvases
- **Viewer**: Read-only access to canvases

## API Endpoints

### Core Endpoints

#### Canvas Management

**List Canvases**
```bash
GET /runtime/canvases/
```

**Create Canvas**
```bash
POST /runtime/canvases/
{
  "name": "My Canvas",
  "description": "A collaborative SVG canvas"
}
```

**Get Canvas**
```bash
GET /runtime/canvases/{canvas_id}
```

**Delete Canvas**
```bash
DELETE /runtime/canvases/{canvas_id}
```

#### Runtime Operations

**Handle UI Event**
```bash
POST /runtime/ui-event/
{
  "event_type": "edit",
  "canvas_id": "canvas_123",
  "object_id": "obj_456",
  "data": {
    "x": 100,
    "y": 200,
    "width": 150,
    "height": 100
  }
}
```

**Undo Action**
```bash
POST /runtime/undo/
{
  "canvas_id": "canvas_123"
}
```

**Redo Action**
```bash
POST /runtime/redo/
{
  "canvas_id": "canvas_123"
}
```

#### Lock Management

**Acquire Lock**
```bash
POST /runtime/lock/
{
  "canvas_id": "canvas_123",
  "object_id": "obj_456"
}
```

**Release Lock**
```bash
POST /runtime/unlock/
{
  "canvas_id": "canvas_123",
  "object_id": "obj_456"
}
```

**Get Lock Status**
```bash
GET /runtime/lock-status/?canvas_id=canvas_123&object_ids=obj_456,obj_789
```

### Monitoring Endpoints

**Get System Metrics**
```bash
GET /metrics/
```

**Get Health Summary**
```bash
GET /health/summary/
```

**Get Prometheus Metrics**
```bash
GET /metrics/prometheus
```

### State Management

**Persist State**
```bash
POST /state/persist/
{
  "key": "canvas_state_123",
  "value": { "objects": [...] },
  "state_type": "canvas",
  "version": 1,
  "metadata": { "user_id": "user_123" }
}
```

**Retrieve State**
```bash
GET /state/retrieve/canvas_state_123?state_type=canvas
```

## WebSocket Integration

### Connection

Connect to the WebSocket endpoint with authentication:

```javascript
const token = 'your_jwt_token';
const canvasId = 'canvas_123';
const sessionId = 'session_456';

const ws = new WebSocket(
  `ws://localhost:8000/runtime/events?canvas_id=${canvasId}&session_id=${sessionId}&token=${token}`
);
```

### Handshake

Send initial handshake message:

```javascript
ws.onopen = () => {
  ws.send(JSON.stringify({
    event_type: 'handshake',
    canvas_id: canvasId,
    session_id: sessionId,
    user_id: 'user_123'
  }));
};
```

### Event Types

#### Edit Operations
```javascript
ws.send(JSON.stringify({
  event_type: 'edit_operation',
  canvas_id: 'canvas_123',
  object_id: 'obj_456',
  data: {
    operation: 'move',
    x: 100,
    y: 200
  }
}));
```

#### Lock Requests
```javascript
ws.send(JSON.stringify({
  event_type: 'lock_request',
  canvas_id: 'canvas_123',
  object_id: 'obj_456'
}));
```

#### User Activity
```javascript
ws.send(JSON.stringify({
  event_type: 'user_activity',
  canvas_id: 'canvas_123',
  data: {
    activity: 'drawing',
    tool: 'rectangle'
  }
}));
```

### Message Handling

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'handshake_ack':
      console.log('Connected to collaboration server');
      break;
      
    case 'lock_acquired':
      console.log('Lock acquired:', message.data);
      break;
      
    case 'lock_released':
      console.log('Lock released:', message.data);
      break;
      
    case 'edit_operation':
      handleRemoteEdit(message.data);
      break;
      
    case 'user_joined':
      console.log('User joined:', message.data.username);
      break;
      
    case 'user_left':
      console.log('User left:', message.data.username);
      break;
      
    case 'conflict_detected':
      handleConflict(message.data);
      break;
      
    default:
      console.log('Unknown message type:', message.type);
  }
};
```

## Error Handling

### Error Response Format

All API errors return a consistent JSON format:

```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "field": "canvas_id",
    "issue": "Required field missing"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

- `400`: Bad Request - Invalid request data
- `401`: Unauthorized - Authentication required or invalid
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `409`: Conflict - Resource conflict (e.g., object already locked)
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

### Error Handling Example

```javascript
async function makeApiCall(endpoint, data) {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`${error.error}: ${error.message}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```

## Rate Limiting

### Rate Limit Headers

API responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Handling

```javascript
function handleRateLimit(response) {
  const limit = response.headers.get('X-RateLimit-Limit');
  const remaining = response.headers.get('X-RateLimit-Remaining');
  const reset = response.headers.get('X-RateLimit-Reset');
  
  if (remaining === '0') {
    const resetTime = new Date(reset * 1000);
    console.log(`Rate limit exceeded. Reset at: ${resetTime}`);
    return false;
  }
  
  return true;
}
```

## Code Examples

### JavaScript/TypeScript Client

```typescript
class SVGXClient {
  private baseUrl: string;
  private token: string;
  
  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }
  
  async login(username: string, password: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    if (!response.ok) {
      throw new Error('Login failed');
    }
    
    const data = await response.json();
    this.token = data.access_token;
  }
  
  async getCanvases(): Promise<Canvas[]> {
    const response = await fetch(`${this.baseUrl}/runtime/canvases/`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch canvases');
    }
    
    const data = await response.json();
    return data.canvases;
  }
  
  async createCanvas(name: string, description?: string): Promise<Canvas> {
    const response = await fetch(`${this.baseUrl}/runtime/canvases/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({ name, description })
    });
    
    if (!response.ok) {
      throw new Error('Failed to create canvas');
    }
    
    return await response.json();
  }
  
  async sendUIEvent(canvasId: string, eventType: string, data: any): Promise<void> {
    const response = await fetch(`${this.baseUrl}/runtime/ui-event/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({
        event_type: eventType,
        canvas_id: canvasId,
        data
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to send UI event');
    }
  }
}
```

### Python Client

```python
import requests
import json
from typing import Dict, List, Optional

class SVGXClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """Login to SVGX Engine."""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            return True
        return False
    
    def get_canvases(self) -> List[Dict]:
        """Get list of canvases."""
        response = self.session.get(f"{self.base_url}/runtime/canvases/")
        response.raise_for_status()
        return response.json()['canvases']
    
    def create_canvas(self, name: str, description: str = "") -> Dict:
        """Create a new canvas."""
        response = self.session.post(
            f"{self.base_url}/runtime/canvases/",
            json={"name": name, "description": description}
        )
        response.raise_for_status()
        return response.json()
    
    def send_ui_event(self, canvas_id: str, event_type: str, data: Dict) -> None:
        """Send UI event to canvas."""
        response = self.session.post(
            f"{self.base_url}/runtime/ui-event/",
            json={
                "event_type": event_type,
                "canvas_id": canvas_id,
                "data": data
            }
        )
        response.raise_for_status()
    
    def get_health(self) -> Dict:
        """Get system health status."""
        response = self.session.get(f"{self.base_url}/health/summary/")
        response.raise_for_status()
        return response.json()
```

### WebSocket Client (JavaScript)

```javascript
class SVGXWebSocket {
  constructor(baseUrl, token, canvasId, sessionId) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.canvasId = canvasId;
    this.sessionId = sessionId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect() {
    const wsUrl = `${this.baseUrl.replace('http', 'ws')}/runtime/events?canvas_id=${this.canvasId}&session_id=${this.sessionId}&token=${this.token}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Send handshake
      this.send({
        event_type: 'handshake',
        canvas_id: this.canvasId,
        session_id: this.sessionId
      });
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.handleReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
  
  handleMessage(message) {
    switch (message.type) {
      case 'handshake_ack':
        console.log('Handshake acknowledged');
        break;
      case 'edit_operation':
        this.handleEditOperation(message.data);
        break;
      case 'lock_update':
        this.handleLockUpdate(message.data);
        break;
      case 'user_activity':
        this.handleUserActivity(message.data);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }
  
  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'User initiated disconnect');
    }
  }
}
```

## Best Practices

### Authentication

1. **Store tokens securely**: Use secure storage for JWT tokens
2. **Handle token expiration**: Implement automatic token refresh
3. **Validate permissions**: Check user permissions before operations

### WebSocket Management

1. **Implement reconnection**: Handle connection drops gracefully
2. **Rate limit messages**: Don't flood the WebSocket with messages
3. **Handle conflicts**: Implement conflict resolution for concurrent edits
4. **Clean up resources**: Properly close connections on page unload

### Error Handling

1. **Graceful degradation**: Handle API failures gracefully
2. **User feedback**: Provide clear error messages to users
3. **Retry logic**: Implement retry mechanisms for transient failures
4. **Logging**: Log errors for debugging

### Performance

1. **Batch operations**: Group related API calls when possible
2. **Caching**: Cache frequently accessed data
3. **Pagination**: Use pagination for large datasets
4. **Compression**: Enable gzip compression for API responses

## Testing

### API Testing

```python
import pytest
import requests

class TestSVGXAPI:
    def setup_method(self):
        self.base_url = "http://localhost:8000"
        self.client = SVGXClient(self.base_url)
    
    def test_login(self):
        """Test user login."""
        success = self.client.login("test@example.com", "password123")
        assert success
        assert self.client.token is not None
    
    def test_create_canvas(self):
        """Test canvas creation."""
        self.client.login("test@example.com", "password123")
        canvas = self.client.create_canvas("Test Canvas", "Test description")
        assert canvas["name"] == "Test Canvas"
        assert canvas["description"] == "Test description"
    
    def test_get_canvases(self):
        """Test canvas listing."""
        self.client.login("test@example.com", "password123")
        canvases = self.client.get_canvases()
        assert isinstance(canvases, list)
    
    def test_health_check(self):
        """Test health endpoint."""
        health = self.client.get_health()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
```

### WebSocket Testing

```javascript
describe('SVGX WebSocket', () => {
  let ws;
  
  beforeEach(() => {
    ws = new SVGXWebSocket('ws://localhost:8000', 'token', 'canvas_123', 'session_456');
  });
  
  afterEach(() => {
    ws.disconnect();
  });
  
  test('should connect successfully', (done) => {
    ws.onopen = () => {
      expect(ws.ws.readyState).toBe(WebSocket.OPEN);
      done();
    };
    
    ws.connect();
  });
  
  test('should handle edit operations', (done) => {
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'edit_operation') {
        expect(message.data.operation).toBe('move');
        done();
      }
    };
    
    ws.connect();
    ws.send({
      event_type: 'edit_operation',
      canvas_id: 'canvas_123',
      object_id: 'obj_456',
      data: { operation: 'move', x: 100, y: 200 }
    });
  });
});
```

## Support

For additional support:

- **Documentation**: [https://docs.svgx-engine.com](https://docs.svgx-engine.com)
- **API Reference**: [https://api.svgx-engine.com/docs](https://api.svgx-engine.com/docs)
- **GitHub Issues**: [https://github.com/svgx-engine/issues](https://github.com/svgx-engine/issues)
- **Email Support**: support@svgx-engine.com

## Version History

- **v1.0.0**: Initial release with core collaborative editing features
- **v1.1.0**: Added advanced lock management and conflict resolution
- **v1.2.0**: Implemented state persistence and backup functionality
- **v1.3.0**: Added monitoring, metrics, and health checks
- **v1.4.0**: Enhanced security with rate limiting and RBAC 