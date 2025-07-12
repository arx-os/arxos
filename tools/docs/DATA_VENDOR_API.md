# Data Vendor API Documentation

## Overview

The Arxos Data Vendor API provides external data purchasers with secure access to building inventory data, industry benchmarks, and analytics. The API is designed with enterprise-grade security, comprehensive monitoring, and flexible access controls.

## Features

- **Secure Authentication**: API key-based authentication with role-based access control
- **Rate Limiting**: Configurable rate limits per vendor and access level
- **Comprehensive Logging**: All API requests are logged for auditing and billing
- **Access Control**: Tiered access levels (basic, premium, enterprise)
- **Real-time Monitoring**: Usage tracking and performance metrics
- **Billing Integration**: Automated billing based on usage and access levels

## Authentication

All API requests require an API key to be included in the request header:

```
X-API-Key: your_api_key_here
```

### API Key Format

API keys follow the format: `arx_[timestamp]_[random]`

Example: `arx_1234567890_abcdef123456`

## Access Levels

### Basic
- Access to public building data
- Rate limit: 1,000 requests/hour
- Monthly cost: $50

### Premium
- Access to public and basic building data
- Rate limit: 5,000 requests/hour
- Monthly cost: $150

### Enterprise
- Access to all building data
- Rate limit: 20,000 requests/hour
- Monthly cost: $500

## Rate Limiting

Rate limits are enforced per API key on a rolling window basis. When a rate limit is exceeded, the API returns:

```json
{
  "error": "Rate limit exceeded"
}
```

Status code: `429 Too Many Requests`

## API Endpoints

### 1. Get Available Buildings

Retrieve a list of buildings available to the vendor based on their access level.

**Endpoint:** `GET /api/vendor/buildings`

**Query Parameters:**
- `limit` (optional): Number of buildings to return (default: 50, max: 100)
- `offset` (optional): Number of buildings to skip (default: 0)
- `status` (optional): Filter by building status (active, inactive, etc.)

**Response:**
```json
{
  "buildings": [
    {
      "id": 1,
      "name": "Downtown Office Tower",
      "address": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zip_code": "10001",
      "building_type": "Office",
      "status": "active",
      "access_level": "public",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_more": true
  },
  "vendor_info": {
    "vendor_name": "DataCorp Inc",
    "access_level": "premium",
    "rate_limit": 5000
  }
}
```

### 2. Get Building Inventory

Retrieve detailed inventory data for a specific building.

**Endpoint:** `GET /api/vendor/buildings/{buildingId}/inventory`

**Path Parameters:**
- `buildingId`: ID of the building

**Query Parameters:**
- `limit` (optional): Number of assets to return (default: 100, max: 500)
- `offset` (optional): Number of assets to skip (default: 0)
- `category` (optional): Filter by asset category (HVAC, Electrical, Plumbing, etc.)
- `status` (optional): Filter by asset status (active, inactive, maintenance, etc.)

**Response:**
```json
{
  "building": {
    "id": 1,
    "name": "Downtown Office Tower",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "building_type": "Office"
  },
  "inventory": [
    {
      "id": "HVAC_001",
      "building_id": 1,
      "floor_id": 5,
      "room_id": "ROOM_501",
      "symbol_id": "ahu",
      "asset_type": "HVAC",
      "system": "Heating",
      "subsystem": "Air Handling",
      "location": {
        "floor": "5th Floor",
        "room": "501",
        "area": "North Wing",
        "x": 150.5,
        "y": 200.0,
        "coordinates": "150.5,200.0"
      },
      "specifications": {
        "manufacturer": "Carrier",
        "model": "48TC",
        "capacity": "10 tons",
        "efficiency": "SEER 16"
      },
      "metadata": {
        "installation_date": "2020-03-15",
        "warranty_expiry": "2025-03-15",
        "last_maintenance": "2024-01-10"
      },
      "age": 4,
      "efficiency_rating": "A",
      "lifecycle_stage": "operational",
      "estimated_value": 25000.00,
      "replacement_cost": 30000.00,
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 250,
    "limit": 100,
    "offset": 0,
    "has_more": true
  },
  "vendor_info": {
    "vendor_name": "DataCorp Inc",
    "access_level": "premium"
  }
}
```

### 3. Get Building Summary

Retrieve summary statistics for a specific building.

**Endpoint:** `GET /api/vendor/buildings/{buildingId}/summary`

**Path Parameters:**
- `buildingId`: ID of the building

**Response:**
```json
{
  "building": {
    "id": 1,
    "name": "Downtown Office Tower",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "building_type": "Office"
  },
  "summary": {
    "total_assets": 250,
    "total_value": 2500000.00,
    "avg_age": 8.5,
    "maintenance_due": 15,
    "critical_assets": 5,
    "category_breakdown": {
      "HVAC": 45,
      "Electrical": 80,
      "Plumbing": 60,
      "Fire Safety": 25,
      "Security": 40
    }
  },
  "vendor_info": {
    "vendor_name": "DataCorp Inc",
    "access_level": "premium"
  }
}
```

### 4. Get Industry Benchmarks

Retrieve industry benchmark data for equipment and systems.

**Endpoint:** `GET /api/vendor/industry-benchmarks`

**Query Parameters:**
- `building_type` (optional): Filter by building type (Office, Retail, Industrial, etc.)
- `region` (optional): Filter by region (North America, Europe, Asia, etc.)

**Response:**
```json
{
  "benchmarks": [
    {
      "id": 1,
      "equipment_type": "HVAC",
      "system": "Heating",
      "metric": "efficiency",
      "value": 85.5,
      "unit": "percent",
      "source": "ASHRAE",
      "year": 2023,
      "description": "Average heating system efficiency for commercial buildings",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "filters": {
    "building_type": "Office",
    "region": "North America"
  },
  "vendor_info": {
    "vendor_name": "DataCorp Inc",
    "access_level": "premium"
  }
}
```

## Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "error": "Error message description"
}
```

### Common Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Access denied to requested resource |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

## Usage Examples

### Python Example

```python
import requests
import json

# API Configuration
API_BASE_URL = "https://api.arxos.io/api/vendor"
API_KEY = "your_api_key_here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get available buildings
response = requests.get(f"{API_BASE_URL}/buildings", headers=headers)
if response.status_code == 200:
    buildings = response.json()
    print(f"Found {len(buildings['buildings'])} buildings")
    
    # Get inventory for first building
    if buildings['buildings']:
        building_id = buildings['buildings'][0]['id']
        inventory_response = requests.get(
            f"{API_BASE_URL}/buildings/{building_id}/inventory",
            headers=headers
        )
        if inventory_response.status_code == 200:
            inventory = inventory_response.json()
            print(f"Building has {len(inventory['inventory'])} assets")
```

### JavaScript Example

```javascript
const API_BASE_URL = 'https://api.arxos.io/api/vendor';
const API_KEY = 'your_api_key_here';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Get available buildings
async function getBuildings() {
    try {
        const response = await fetch(`${API_BASE_URL}/buildings`, { headers });
        if (response.ok) {
            const data = await response.json();
            console.log(`Found ${data.buildings.length} buildings`);
            return data.buildings;
        } else {
            console.error('Failed to fetch buildings:', response.status);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Get building inventory
async function getBuildingInventory(buildingId) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/buildings/${buildingId}/inventory`,
            { headers }
        );
        if (response.ok) {
            const data = await response.json();
            console.log(`Building has ${data.inventory.length} assets`);
            return data.inventory;
        } else {
            console.error('Failed to fetch inventory:', response.status);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### cURL Examples

```bash
# Get available buildings
curl -H "X-API-Key: your_api_key_here" \
     "https://api.arxos.io/api/vendor/buildings"

# Get building inventory
curl -H "X-API-Key: your_api_key_here" \
     "https://api.arxos.io/api/vendor/buildings/1/inventory"

# Get building summary
curl -H "X-API-Key: your_api_key_here" \
     "https://api.arxos.io/api/vendor/buildings/1/summary"

# Get industry benchmarks
curl -H "X-API-Key: your_api_key_here" \
     "https://api.arxos.io/api/vendor/industry-benchmarks?building_type=Office"
```

## Admin Management

### Admin API Endpoints

Administrators can manage API keys and monitor usage through dedicated admin endpoints:

#### Dashboard
- `GET /api/admin/data-vendor/dashboard` - Get overview metrics

#### API Key Management
- `GET /api/admin/data-vendor/keys` - List all API keys
- `POST /api/admin/data-vendor/keys` - Create new API key
- `GET /api/admin/data-vendor/keys/{id}` - Get API key details
- `PATCH /api/admin/data-vendor/keys/{id}/status` - Update API key status

#### Usage Monitoring
- `GET /api/admin/data-vendor/usage` - Get usage statistics
- `GET /api/admin/data-vendor/billing` - Get billing information

### CLI Tool

A command-line interface is available for managing API keys:

```bash
# Show dashboard
./data-vendor-cli dashboard

# List all API keys
./data-vendor-cli list

# Create new API key
./data-vendor-cli create --vendor "DataCorp Inc" --email "api@datacorp.com" --level premium

# Show API key details
./data-vendor-cli show --id 123

# Activate/deactivate API key
./data-vendor-cli activate --id 123
./data-vendor-cli deactivate --id 123

# Show usage statistics
./data-vendor-cli usage --days 30

# Show billing information
./data-vendor-cli billing
```

## Web Interface

A comprehensive web interface is available for managing data vendor API keys:

- **Dashboard**: Real-time metrics and usage trends
- **API Key Management**: Create, view, and manage API keys
- **Usage Tracking**: Detailed usage analytics and filtering
- **Billing**: Revenue tracking and vendor billing information

Access the web interface at: `https://admin.arxos.io/data-vendor-admin`

## Best Practices

### Rate Limiting
- Implement exponential backoff when hitting rate limits
- Monitor your usage to stay within limits
- Consider upgrading your access level if you frequently hit limits

### Error Handling
- Always check response status codes
- Implement retry logic for transient errors (5xx)
- Log errors for debugging and monitoring

### Data Processing
- Use pagination to handle large datasets
- Implement caching for frequently accessed data
- Process data in batches to avoid overwhelming your systems

### Security
- Keep your API key secure and never expose it in client-side code
- Rotate API keys regularly
- Monitor your usage for suspicious activity

## Support

For technical support or questions about the Data Vendor API:

- **Email**: api-support@arxos.io
- **Documentation**: https://docs.arxos.io/api
- **Status Page**: https://status.arxos.io
- **Developer Portal**: https://developers.arxos.io

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial release of Data Vendor API
- Support for building inventory and industry benchmarks
- API key authentication and rate limiting
- Admin management interface and CLI tool 