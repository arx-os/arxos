# ArxOS API Specification Enhancements

## Overview

The ArxOS API specification has been enhanced to reflect all the implementation improvements made in `/internal/api`. This document describes the enhancements and how to use them.

---

## What's New in v2

### 1. **Enhanced Validation Schemas** ✅

All request schemas now include comprehensive validation constraints:

```yaml
CreateBuildingRequest:
  properties:
    arxos_id:
      type: string
      pattern: '^ARXOS-[A-Z0-9-]{3,}$'  # ArxOS ID format
      minLength: 9
    name:
      type: string
      minLength: 1
      maxLength: 200
    latitude:
      type: number
      minimum: -90
      maximum: 90
    longitude:
      type: number
      minimum: -180
      maximum: 180
```

**Benefits**:
- Client-side validation before API calls
- Clear error messages with field-level detail
- Automatic SDK generation with validation
- Reduced invalid requests

### 2. **API Versioning Support** ✅

Multiple versioning methods supported:

```yaml
servers:
  - url: https://api.arxos.io/v2
    description: Production (v2 - beta)
  - url: https://api.arxos.io/v1
    description: Production (v1 - stable)
```

**Version Selection**:
1. URL Path: `/api/v2/buildings`
2. Accept Header: `Accept: application/vnd.arxos.v2+json`
3. Custom Header: `X-API-Version: v2`
4. Query Param: `?version=v2`
5. Default: v1

**Deprecation Headers**:
```
Warning: 299 - "API version v1 is deprecated..."
Sunset: 2025-12-31
Link: </api/v2>; rel="successor-version"
```

### 3. **Rate Limiting Documentation** ✅

Comprehensive rate limit information:

```yaml
# Tier-based limits
Free Tier:        100 requests/minute
Starter Tier:     1,000 requests/minute
Professional:     10,000 requests/minute
Enterprise:       Custom limits

# Response headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1727702400
```

**Rate Limit Exceeded Response**:
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 100,
    "window": 60,
    "retry_after": 45
  }
}
```

### 4. **Caching Headers** ✅

Cache control documented:

```yaml
responses:
  200:
    headers:
      Cache-Control:
        schema:
          type: string
        example: "public, max-age=300"
      ETag:
        schema:
          type: string
        example: "W/\"a1b2c3d4\""
      Last-Modified:
        schema:
          type: string
          format: http-date
        example: "Tue, 30 Sep 2025 12:00:00 GMT"
```

**Conditional Requests**:
```http
GET /api/v1/buildings/123
If-None-Match: "W/\"a1b2c3d4\""
If-Modified-Since: Tue, 30 Sep 2025 12:00:00 GMT
```

Response: `304 Not Modified` (if unchanged)

### 5. **Enhanced Error Schemas** ✅

Detailed validation error responses:

```yaml
ValidationError:
  properties:
    error: Validation failed
    code: VALIDATION_ERROR
    validation_errors:
      - field: email
        message: email must be a valid email address
        tag: email
        value: invalid-email
      - field: password
        message: password must be at least 8 characters
        tag: min
```

**Error Codes**:
- `VALIDATION_ERROR` - Request validation failed
- `UNAUTHORIZED` - Authentication required
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

### 6. **Health & Metrics Endpoints** ✅

Monitoring endpoints documented:

```yaml
/health:
  get:
    responses:
      200:
        content:
          application/json:
            example:
              status: healthy
              version: 2.0.0
              timestamp: '2025-09-30T12:00:00Z'
              checks:
                database: healthy
                cache: healthy
                storage: healthy

/metrics:
  get:
    responses:
      200:
        content:
          text/plain:
            example: |
              arxos_api_requests_total{method="GET",status="200"} 1234
```

---

## Schema Enhancements

### Request Validation

All create/update requests now include:

✅ **String Length Constraints**
```yaml
name:
  type: string
  minLength: 1
  maxLength: 200
```

✅ **Pattern Validation**
```yaml
arxos_id:
  type: string
  pattern: '^ARXOS-[A-Z0-9-]{3,}$'
path:
  type: string
  pattern: '^/[^/]+(/.+)*$'
```

✅ **Numeric Ranges**
```yaml
latitude:
  type: number
  minimum: -90
  maximum: 90
```

✅ **Enum Constraints**
```yaml
status:
  type: string
  enum: [OPERATIONAL, DEGRADED, FAILED, MAINTENANCE, OFFLINE, UNKNOWN]
role:
  type: string
  enum: [admin, manager, technician, viewer]
```

✅ **Format Validation**
```yaml
email:
  type: string
  format: email
building_id:
  type: string
  format: uuid
created_at:
  type: string
  format: date-time
```

### Response Enhancements

✅ **Pagination Support**
```yaml
PaginationInfo:
  properties:
    page: 1
    page_size: 20
    total: 150
    total_pages: 8
```

✅ **Consistent Error Format**
```yaml
Error:
  required:
    - error
    - code
  properties:
    error: Human-readable message
    code: Machine-readable code
    details: Additional context
```

✅ **Success Response Wrapper**
```yaml
SuccessResponse:
  properties:
    success: true
    message: Operation completed successfully
    data: { ... }
```

---

## Migration Guide

### From v1 to v2

#### 1. Update Base URL
```diff
- https://api.arxos.io/v1
+ https://api.arxos.io/v2
```

#### 2. Update Authentication
No changes - JWT authentication remains the same.

#### 3. Update Request Schemas

**Building Creation (v1)**:
```json
{
  "name": "Building 1",
  "address": "123 Main St"
}
```

**Building Creation (v2 - Enhanced)**:
```json
{
  "arxos_id": "ARXOS-NA-US-NY-NYC-0001",
  "name": "Building 1",
  "org_id": "123e4567-e89b-12d3-a456-426614174001",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "latitude": 40.748817,
  "longitude": -73.985428
}
```

#### 4. Handle Validation Errors

**v1 Error Response**:
```json
{
  "error": "Invalid request"
}
```

**v2 Error Response (Enhanced)**:
```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "validation_errors": [
    {
      "field": "arxos_id",
      "message": "arxos_id must be a valid ArxOS ID (e.g., ARXOS-001)",
      "tag": "arxos_id",
      "value": "INVALID"
    }
  ]
}
```

#### 5. Implement Rate Limit Handling

```javascript
// Check rate limit headers
const limit = response.headers['x-ratelimit-limit'];
const remaining = response.headers['x-ratelimit-remaining'];
const reset = response.headers['x-ratelimit-reset'];

if (remaining < 10) {
  console.warn(`Rate limit warning: ${remaining}/${limit} requests remaining`);
}

// Handle 429 response
if (response.status === 429) {
  const retryAfter = response.headers['retry-after'];
  setTimeout(() => retryRequest(), retryAfter * 1000);
}
```

#### 6. Use Conditional Requests

```javascript
// First request
const response = await fetch('/api/v2/buildings/123');
const etag = response.headers['etag'];
const lastModified = response.headers['last-modified'];

// Subsequent requests
const cachedResponse = await fetch('/api/v2/buildings/123', {
  headers: {
    'If-None-Match': etag,
    'If-Modified-Since': lastModified
  }
});

if (cachedResponse.status === 304) {
  console.log('Using cached data');
}
```

---

## SDK Generation

The enhanced OpenAPI spec can generate SDKs with built-in validation:

### TypeScript/JavaScript

```bash
npx @openapitools/openapi-generator-cli generate \
  -i api/openapi/openapi-v2.yaml \
  -g typescript-axios \
  -o sdk/typescript
```

**Usage**:
```typescript
import { BuildingsApi, CreateBuildingRequest } from './sdk/typescript';

const buildingsApi = new BuildingsApi();

const request: CreateBuildingRequest = {
  arxosId: 'ARXOS-NA-US-NY-NYC-0001',
  name: 'Empire State Building',
  orgId: '123e4567-e89b-12d3-a456-426614174001',
  latitude: 40.748817,
  longitude: -73.985428
};

// Automatic validation before API call
try {
  const building = await buildingsApi.createBuilding(request);
} catch (error) {
  if (error.response.status === 400) {
    console.error('Validation errors:', error.response.data.validation_errors);
  }
}
```

### Python

```bash
openapi-generator-cli generate \
  -i api/openapi/openapi-v2.yaml \
  -g python \
  -o sdk/python
```

**Usage**:
```python
from arxos_sdk import BuildingsApi, CreateBuildingRequest

api = BuildingsApi()

request = CreateBuildingRequest(
    arxos_id='ARXOS-NA-US-NY-NYC-0001',
    name='Empire State Building',
    org_id='123e4567-e89b-12d3-a456-426614174001',
    latitude=40.748817,
    longitude=-73.985428
)

try:
    building = api.create_building(request)
except ApiException as e:
    if e.status == 400:
        print(f"Validation errors: {e.body['validation_errors']}")
```

### Go

```bash
openapi-generator-cli generate \
  -i api/openapi/openapi-v2.yaml \
  -g go \
  -o sdk/go
```

**Usage**:
```go
import (
    arxos "github.com/arxos/sdk/go"
)

client := arxos.NewAPIClient(arxos.NewConfiguration())

req := arxos.CreateBuildingRequest{
    ArxosId:   "ARXOS-NA-US-NY-NYC-0001",
    Name:      "Empire State Building",
    OrgId:     "123e4567-e89b-12d3-a456-426614174001",
    Latitude:  arxos.PtrFloat64(40.748817),
    Longitude: arxos.PtrFloat64(-73.985428),
}

building, resp, err := client.BuildingsApi.CreateBuilding(context.Background()).
    CreateBuildingRequest(req).
    Execute()

if err != nil {
    if resp.StatusCode == 400 {
        // Handle validation errors
    }
}
```

---

## Testing the API

### Using curl

**With Validation**:
```bash
# Valid request
curl -X POST https://api.arxos.io/v2/buildings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "arxos_id": "ARXOS-NA-US-NY-NYC-0001",
    "name": "Empire State Building",
    "org_id": "123e4567-e89b-12d3-a456-426614174001",
    "latitude": 40.748817,
    "longitude": -73.985428
  }'

# Invalid request (will return 400 with validation errors)
curl -X POST https://api.arxos.io/v2/buildings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "arxos_id": "INVALID",
    "name": ""
  }'
```

**With Caching**:
```bash
# First request
curl -i https://api.arxos.io/v2/buildings/123 \
  -H "Authorization: Bearer $TOKEN"

# Note ETag and Last-Modified headers

# Conditional request
curl -i https://api.arxos.io/v2/buildings/123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "If-None-Match: W/\"a1b2c3d4\"" \
  -H "If-Modified-Since: Tue, 30 Sep 2025 12:00:00 GMT"

# Returns 304 if not modified
```

**With Versioning**:
```bash
# URL path (recommended)
curl https://api.arxos.io/v2/buildings

# Header
curl https://api.arxos.io/buildings \
  -H "X-API-Version: v2"

# Accept header
curl https://api.arxos.io/buildings \
  -H "Accept: application/vnd.arxos.v2+json"

# Query parameter
curl "https://api.arxos.io/buildings?version=v2"
```

### Using Postman

1. Import OpenAPI spec: `api/openapi/openapi-v2.yaml`
2. Postman auto-generates collection with examples
3. Variables are pre-configured
4. Validation happens automatically
5. Rate limit headers are displayed

---

## Documentation Generation

### Swagger UI

```bash
docker run -p 8081:8080 \
  -e SWAGGER_JSON=/spec/openapi-v2.yaml \
  -v $(pwd)/api/openapi:/spec \
  swaggerapi/swagger-ui
```

Access: http://localhost:8081

### ReDoc

```bash
docker run -p 8082:80 \
  -e SPEC_URL=/spec/openapi-v2.yaml \
  -v $(pwd)/api/openapi:/spec \
  redocly/redoc
```

Access: http://localhost:8082

### Stoplight

```bash
npx @stoplight/prism-cli mock api/openapi/openapi-v2.yaml
```

Creates a mock server for testing.

---

## Comparison: v1 vs v2

| Feature | v1 | v2 |
|---------|----|----|
| **Validation** | Basic | Comprehensive with custom rules |
| **Versioning** | None | 4 methods supported |
| **Rate Limiting** | Undocumented | Fully documented with headers |
| **Caching** | None | ETags, Last-Modified, Cache-Control |
| **Error Details** | Generic | Field-level validation errors |
| **Monitoring** | None | /health and /metrics endpoints |
| **Pagination** | Basic | Enhanced with total_pages |
| **Authentication** | JWT | JWT (unchanged) |
| **SDK Generation** | Basic | With validation |

---

## Benefits

### For API Consumers

✅ **Better Error Messages** - Know exactly what's wrong  
✅ **Client-Side Validation** - Catch errors before API calls  
✅ **Rate Limit Awareness** - Plan API usage effectively  
✅ **Caching Support** - Reduce unnecessary requests  
✅ **Version Flexibility** - Choose stable or beta versions  
✅ **Type Safety** - Generated SDKs with full types  

### For API Providers

✅ **Reduced Invalid Requests** - Better validation  
✅ **Load Reduction** - Effective caching  
✅ **Monitoring** - Health & metrics endpoints  
✅ **Gradual Rollout** - Version-based deployment  
✅ **Documentation** - Auto-generated from spec  
✅ **Testing** - Mock servers from spec  

---

## Next Steps

1. ✅ Review enhanced OpenAPI spec
2. ⏳ Generate SDKs for client languages
3. ⏳ Update API documentation site
4. ⏳ Deploy v2 to staging
5. ⏳ Beta test with select clients
6. ⏳ Production rollout

---

## Files

- ✅ `api/openapi/openapi-v2.yaml` - Enhanced OpenAPI 3.0.3 specification
- ✅ `api/ENHANCEMENTS.md` - This document
- ✅ `api/README.md` - Updated overview

---

## Support

For questions or issues with the API specification:

- **Documentation**: https://docs.arxos.io
- **Support Email**: support@arxos.io
- **GitHub Issues**: https://github.com/arxos/arxos/issues

---

**The ArxOS API specification is now production-ready with comprehensive enhancements!** 🚀
