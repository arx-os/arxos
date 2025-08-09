# Arxos API Documentation

## Overview

Welcome to the comprehensive API documentation for the Arxos platform. This documentation provides live, explorable API specifications for all backend services, promoting contract-first development practices.

## 📚 **Available APIs**

### **Core Services**

#### [SVG-BIM Parser API](./svg_parser_api_spec.yaml)
- **Service**: `arx_svg_parser`
- **Language**: Python (FastAPI)
- **Port**: 8082
- **Description**: SVG to BIM conversion and management
- **Features**: Symbol recognition, BIM assembly, export interoperability
- **Documentation**: [SVG Parser API Docs](./svg_parser_api_spec.yaml)

#### [Arx Backend API](./arx_backend_api_spec.yaml)
- **Service**: `arx-backend`
- **Language**: Go (Chi Router)
- **Port**: 8080
- **Description**: Core backend services and business logic
- **Features**: Asset management, BIM operations, CMMS integration
- **Documentation**: [Backend API Docs](./arx_backend_api_spec.yaml)

#### [CMMS Service API](./cmms_api_spec.yaml)
- **Service**: `arx-cmms`
- **Language**: Go
- **Port**: 8081
- **Description**: Computerized Maintenance Management System
- **Features**: Work orders, maintenance schedules, asset tracking
- **Documentation**: [CMMS API Docs](./cmms_api_spec.yaml)

#### [Database Infrastructure API](./database_api_spec.yaml)
- **Service**: `arx-database`
- **Language**: Python (Alembic)
- **Description**: Database schema management and monitoring
- **Features**: Schema validation, performance monitoring, migrations
- **Documentation**: [Database API Docs](./database_api_spec.yaml)

## 🚀 **Quick Start**

### **1. View API Documentation**

Each service provides interactive Swagger UI documentation:

```bash
# SVG Parser API
http://localhost:8082/docs

# Arx Backend API
http://localhost:8080/docs

# CMMS Service API
http://localhost:8081/docs
```

### **2. Download OpenAPI Specs**

```bash
# Download all API specifications
curl http://localhost:8082/openapi.json > svg_parser_api_spec.yaml
curl http://localhost:8080/openapi.json > arx_backend_api_spec.yaml
curl http://localhost:8081/openapi.json > cmms_api_spec.yaml
```

### **3. Generate Client SDKs**

```bash
# Generate TypeScript client for SVG Parser
npx @openapitools/openapi-generator-cli generate \
  -i svg_parser_api_spec.yaml \
  -g typescript-fetch \
  -o clients/svg-parser-typescript

# Generate Python client for Backend API
npx @openapitools/openapi-generator-cli generate \
  -i arx_backend_api_spec.yaml \
  -g python \
  -o clients/backend-python
```

## 🔧 **Development Workflow**

### **Contract-First Development**

1. **Define API Contract**: Start with OpenAPI specification
2. **Generate Stubs**: Use tools to generate server stubs
3. **Implement Logic**: Fill in the business logic
4. **Validate**: Ensure implementation matches specification
5. **Document**: Keep documentation synchronized

### **API Versioning**

All APIs follow semantic versioning:
- **v1**: Current stable version
- **v2**: Next major version (when available)
- **Beta**: Experimental features

### **Authentication**

All APIs support multiple authentication methods:
- **JWT Bearer Token**: Primary authentication method
- **API Key**: For service-to-service communication
- **OAuth2**: For third-party integrations

## 📊 **API Standards**

### **Response Format**

All APIs follow a consistent response format:

```json
{
  "status": "success|error",
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid"
}
```

### **Error Handling**

Standard error responses:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": { ... }
  }
}
```

### **Pagination**

List endpoints support pagination:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

## 🧪 **Testing APIs**

### **Using Swagger UI**

1. Navigate to the service's `/docs` endpoint
2. Click "Authorize" to set authentication
3. Test endpoints directly in the browser
4. View request/response examples

### **Using curl**

```bash
# Example: Get health status
curl -X GET "http://localhost:8080/api/health" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Example: Create a project
curl -X POST "http://localhost:8080/api/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "My Project"}'
```

### **Using Postman**

1. Import the OpenAPI specification
2. Set up environment variables
3. Use the generated collection
4. Test all endpoints systematically

## 🔍 **API Monitoring**

### **Health Checks**

All services provide health check endpoints:

```bash
# SVG Parser
curl http://localhost:8082/health

# Backend API
curl http://localhost:8080/api/health

# CMMS Service
curl http://localhost:8081/health
```

### **Metrics**

Prometheus metrics available at `/metrics`:

```bash
# Get metrics
curl http://localhost:8080/metrics
curl http://localhost:8082/metrics
curl http://localhost:8081/metrics
```

## 📝 **Contributing**

### **Adding New Endpoints**

1. **Update OpenAPI Spec**: Add endpoint definition
2. **Implement Handler**: Create the endpoint handler
3. **Add Tests**: Write comprehensive tests
4. **Update Documentation**: Keep docs synchronized
5. **Validate**: Run API validation tests

### **API Review Process**

1. **Specification Review**: Validate OpenAPI spec
2. **Implementation Review**: Code review with API focus
3. **Testing Review**: Ensure comprehensive test coverage
4. **Documentation Review**: Verify documentation accuracy
5. **Integration Testing**: Test with other services

## 🛠️ **Tools and Utilities**

### **OpenAPI Tools**

```bash
# Validate OpenAPI specifications
npx @apidevtools/swagger-cli validate svg_parser_api_spec.yaml

# Lint OpenAPI specs
npx spectral lint svg_parser_api_spec.yaml

# Generate documentation
npx @redocly/cli build-docs svg_parser_api_spec.yaml -o docs/svg-parser.html
```

### **CI/CD Integration**

The API specifications are automatically validated in CI/CD:

- **OpenAPI Validation**: Ensures spec compliance
- **Contract Testing**: Validates implementation against spec
- **Documentation Generation**: Auto-generates docs
- **Client SDK Generation**: Creates client libraries

## 📞 **Support**

### **Getting Help**

- **API Issues**: Create GitHub issues with API tag
- **Documentation**: Submit PRs for documentation improvements
- **Questions**: Use GitHub Discussions
- **Emergency**: Contact the development team

### **Resources**

- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Go Chi Router](https://github.com/go-chi/chi)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

---

**Last Updated**: 2024-12-19
**Version**: 1.0.0
**Maintainer**: Arxos Development Team
