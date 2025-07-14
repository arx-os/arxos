# {{ language.title() }} SDK API Reference

Complete API reference for the Arxos {{ language.title() }} SDK.

## 📋 Table of Contents

- [Authentication](#authentication)
- [Arx Backend API](#arx-backend-api)
- [SVG Parser API](#svg-parser-api)
- [CMMS Service API](#cmms-service-api)
- [Database Infrastructure API](#database-infrastructure-api)
- [Error Handling](#error-handling)
- [Types and Models](#types-and-models)

## 🔐 Authentication

### Client Initialization

```{{ language }}
{{ client_init_code }}
```

### Authentication Methods

#### API Key Authentication
```{{ language }}
{{ api_key_auth_code }}
```

#### OAuth 2.0 Authentication
```{{ language }}
{{ oauth_auth_code }}
```

#### Session Authentication
```{{ language }}
{{ session_auth_code }}
```

## 🏗️ Arx Backend API

### Authentication Endpoints

#### Login
```{{ language }}
{{ login_endpoint_code }}
```

**Parameters:**
- `username` (string): User's username or email
- `password` (string): User's password

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_123",
    "username": "john.doe",
    "email": "john@example.com",
    "role": "user"
  }
}
```

#### Validate Token
```{{ language }}
{{ validate_token_code }}
```

**Response:**
```json
{
  "valid": true,
  "user": {
    "id": "user_123",
    "username": "john.doe",
    "role": "user"
  }
}
```

### Health Check

#### Get Health Status
```{{ language }}
{{ health_check_code }}
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Project Management

#### List Projects
```{{ language }}
{{ list_projects_code }}
```

**Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20)
- `search` (string, optional): Search term

**Response:**
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "Office Building",
      "description": "Modern office complex",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### Create Project
```{{ language }}
{{ create_project_code }}
```

**Parameters:**
- `name` (string, required): Project name
- `description` (string, optional): Project description
- `type` (string, optional): Project type

**Response:**
```json
{
  "id": "proj_123",
  "name": "Office Building",
  "description": "Modern office complex",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Building Management

#### List Buildings
```{{ language }}
{{ list_buildings_code }}
```

#### Create Building
```{{ language }}
{{ create_building_code }}
```

#### Get Building
```{{ language }}
{{ get_building_code }}
```

### BIM Objects

#### List BIM Objects
```{{ language }}
{{ list_bim_objects_code }}
```

#### Create Wall
```{{ language }}
{{ create_wall_code }}
```

#### Create Room
```{{ language }}
{{ create_room_code }}
```

#### Create Device
```{{ language }}
{{ create_device_code }}
```

### Asset Management

#### List Assets
```{{ language }}
{{ list_assets_code }}
```

#### Create Asset
```{{ language }}
{{ create_asset_code }}
```

#### Update Asset
```{{ language }}
{{ update_asset_code }}
```

### CMMS Integration

#### List CMMS Connections
```{{ language }}
{{ list_cmms_connections_code }}
```

#### Create CMMS Connection
```{{ language }}
{{ create_cmms_connection_code }}
```

#### Sync CMMS Data
```{{ language }}
{{ sync_cmms_data_code }}
```

### Export Activities

#### List Export Activities
```{{ language }}
{{ list_export_activities_code }}
```

#### Create Export Activity
```{{ language }}
{{ create_export_activity_code }}
```

#### Get Export Status
```{{ language }}
{{ get_export_status_code }}
```

## 🎨 SVG Parser API

### Symbol Management

#### List Symbols
```{{ language }}
{{ list_symbols_code }}
```

#### Upload Symbol
```{{ language }}
{{ upload_symbol_code }}
```

#### Get Symbol
```{{ language }}
{{ get_symbol_code }}
```

### Drawing Management

#### List Drawings
```{{ language }}
{{ list_drawings_code }}
```

#### Upload Drawing
```{{ language }}
{{ upload_drawing_code }}
```

#### Parse Drawing
```{{ language }}
{{ parse_drawing_code }}
```

### Export Operations

#### Export to BIM
```{{ language }}
{{ export_to_bim_code }}
```

#### Export to CAD
```{{ language }}
{{ export_to_cad_code }}
```

## 🔧 CMMS Service API

### Connection Management

#### List Connections
```{{ language }}
{{ list_cmms_connections_code }}
```

#### Test Connection
```{{ language }}
{{ test_cmms_connection_code }}
```

### Field Mappings

#### List Field Mappings
```{{ language }}
{{ list_field_mappings_code }}
```

#### Create Field Mapping
```{{ language }}
{{ create_field_mapping_code }}
```

### Synchronization

#### Sync Work Orders
```{{ language }}
{{ sync_work_orders_code }}
```

#### Sync Equipment
```{{ language }}
{{ sync_equipment_code }}
```

#### Get Sync Status
```{{ language }}
{{ get_sync_status_code }}
```

## 🗄️ Database Infrastructure API

### Health Check

#### Get Database Health
```{{ language }}
{{ get_db_health_code }}
```

### Schema Management

#### List Schemas
```{{ language }}
{{ list_schemas_code }}
```

#### Get Schema
```{{ language }}
{{ get_schema_code }}
```

### Performance Monitoring

#### Get Performance Metrics
```{{ language }}
{{ get_performance_metrics_code }}
```

#### Get Query Statistics
```{{ language }}
{{ get_query_stats_code }}
```

## 🚨 Error Handling

### Error Types

```{{ language }}
{{ error_types_code }}
```

### Error Handling Examples

```{{ language }}
{{ error_handling_examples_code }}
```

### Retry Logic

```{{ language }}
{{ retry_logic_code }}
```

## 📊 Types and Models

### Common Types

```{{ language }}
{{ common_types_code }}
```

### Request Models

```{{ language }}
{{ request_models_code }}
```

### Response Models

```{{ language }}
{{ response_models_code }}
```

### Error Models

```{{ language }}
{{ error_models_code }}
```

## 🔧 Configuration

### Client Configuration

```{{ language }}
{{ client_config_code }}
```

### Request Configuration

```{{ language }}
{{ request_config_code }}
```

### Response Configuration

```{{ language }}
{{ response_config_code }}
```

## 📈 Performance

### Connection Pooling

```{{ language }}
{{ connection_pooling_code }}
```

### Request Batching

```{{ language }}
{{ request_batching_code }}
```

### Caching

```{{ language }}
{{ caching_code }}
```

## 🔒 Security

### TLS Configuration

```{{ language }}
{{ tls_config_code }}
```

### Certificate Validation

```{{ language }}
{{ cert_validation_code }}
```

### Input Validation

```{{ language }}
{{ input_validation_code }}
```

## 🧪 Testing

### Mock Client

```{{ language }}
{{ mock_client_code }}
```

### Test Utilities

```{{ language }}
{{ test_utilities_code }}
```

### Integration Tests

```{{ language }}
{{ integration_tests_code }}
``` 