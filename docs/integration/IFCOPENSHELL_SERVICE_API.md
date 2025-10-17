# IfcOpenShell Service API Documentation

**Service Version:** 1.0.0  
**IfcOpenShell Version:** 0.8.3  
**Last Updated:** October 17, 2025

---

## Overview

The IfcOpenShell service is a Python Flask microservice that provides comprehensive IFC (Industry Foundation Classes) file processing for ArxOS. It extracts detailed building information including entities, relationships, property sets, and spatial data.

**Key Capabilities:**
- Full entity extraction (not just counts)
- Spatial hierarchy preservation
- Property set (Pset) extraction
- 3D coordinate extraction
- buildingSMART compliance validation
- Spatial query operations

---

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ifcopenshell",
  "version": "0.8.3",
  "timestamp": "2025-10-17T12:00:00Z",
  "cache_enabled": true,
  "max_file_size_mb": 50.0
}
```

### Detailed Health Check

```http
GET /api/monitoring/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ifcopenshell",
  "version": "0.8.3",
  "timestamp": "2025-10-17T12:00:00Z",
  "uptime_seconds": 3600,
  "performance": {
    "requests_total": 150,
    "requests_per_second": 0.042,
    "error_rate": 0.02,
    "processing_time_p95": 2.5
  },
  "cache": {
    "hits": 85,
    "misses": 65,
    "hit_rate_percent": 56.67,
    "redis_connected": true
  },
  "errors": {
    "total_errors": 3,
    "error_counts": {"IFCParseError": 2, "ValidationError": 1}
  },
  "configuration": {
    "max_file_size_mb": 50.0,
    "cache_enabled": true,
    "cache_ttl_seconds": 3600
  }
}
```

---

## IFC Parsing Endpoint

### Parse IFC File

```http
POST /api/parse
Content-Type: application/octet-stream
```

**Request Body:** Raw IFC file data (binary)

**Response Structure:**

```json
{
  "success": true,
  
  // Legacy entity counts (backward compatibility)
  "buildings": 1,
  "spaces": 25,
  "equipment": 150,
  "walls": 200,
  "doors": 50,
  "windows": 75,
  "total_entities": 501,
  
  // Metadata
  "metadata": {
    "ifc_version": "IFC4",
    "file_size": 1024000,
    "processing_time": "2.5s",
    "timestamp": "2025-10-17T12:00:00Z"
  },
  
  // DETAILED ENTITY ARRAYS (for full extraction)
  
  "building_entities": [
    {
      "global_id": "2O2Fr$t4X7Zf8NOew3FLOH",
      "name": "Main Building",
      "description": "Corporate Headquarters",
      "long_name": "HQ Building",
      "address": {
        "address_lines": ["123 Main Street", "Suite 100"],
        "postal_code": "94105",
        "town": "San Francisco",
        "region": "California",
        "country": "USA"
      },
      "elevation": 0.0,
      "properties": {}
    }
  ],
  
  "floor_entities": [
    {
      "global_id": "3pDfk9sdF2x9483jdkFl03",
      "name": "Level 1",
      "long_name": "First Floor",
      "description": "Ground floor with lobby and offices",
      "elevation": 0.0,
      "height": 3.5,
      "properties": {}
    },
    {
      "global_id": "4qEgl0teG3y0594kflEm14",
      "name": "Level 2",
      "long_name": "Second Floor",
      "description": "Second floor with conference rooms",
      "elevation": 3.5,
      "height": 3.5,
      "properties": {}
    }
  ],
  
  "space_entities": [
    {
      "global_id": "0YgR8dkF3x0394jfkDl93",
      "name": "101",
      "long_name": "Room 101",
      "description": "Conference Room A",
      "floor_id": "3pDfk9sdF2x9483jdkFl03",
      "placement": {
        "x": 10.5,
        "y": 5.2,
        "z": 0.0
      },
      "bounding_box": null,
      "properties": {}
    }
  ],
  
  "equipment_entities": [
    {
      "global_id": "1KjDf8sdK3x8473hfkEl82",
      "name": "VAV-101",
      "description": "Variable Air Volume Box for Room 101",
      "object_type": "IfcAirTerminalBox",
      "tag": "VAV-101",
      "space_id": "0YgR8dkF3x0394jfkDl93",
      "placement": {
        "x": 10.5,
        "y": 5.2,
        "z": 3.0
      },
      "category": "hvac",
      "property_sets": [
        {
          "name": "Pset_AirTerminalBoxTypeCommon",
          "properties": {
            "NominalAirFlowRate": 500.0,
            "NominalPower": 1200.0,
            "FinishType": "Painted Steel"
          }
        }
      ],
      "classification": []
    }
  ],
  
  "relationships": [
    {
      "type": "contains",
      "relating_object": "3pDfk9sdF2x9483jdkFl03",
      "related_objects": [
        "0YgR8dkF3x0394jfkDl93",
        "1YhS9elG4y1405kgmEn04"
      ],
      "description": "Spatial containment"
    },
    {
      "type": "contains",
      "relating_object": "0YgR8dkF3x0394jfkDl93",
      "related_objects": [
        "1KjDf8sdK3x8473hfkEl82"
      ],
      "description": "Spatial containment"
    }
  ]
}
```

---

## Entity Array Schemas

### building_entities[]

Each building entity contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `global_id` | string | Yes | IFC GlobalId (unique identifier) |
| `name` | string | Yes | Building name |
| `description` | string | No | Building description |
| `long_name` | string | No | Extended building name |
| `address` | object | No | Structured address data |
| `elevation` | float | No | Reference elevation in meters |
| `properties` | object | No | Additional properties (reserved for future use) |

**Address Object:**
```json
{
  "address_lines": ["line1", "line2"],
  "postal_code": "12345",
  "town": "City Name",
  "region": "State/Province",
  "country": "Country Name"
}
```

### floor_entities[]

Each floor entity contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `global_id` | string | Yes | IFC GlobalId |
| `name` | string | Yes | Floor name (e.g., "Level 1") |
| `long_name` | string | No | Extended floor name |
| `description` | string | No | Floor description |
| `elevation` | float | Yes | Floor elevation in meters |
| `height` | float | No | Floor height in meters |
| `properties` | object | No | Additional properties |

**Note:** To link floors to buildings, use `IfcRelContainedInSpatialStructure` relationships or infer from IFC hierarchy.

### space_entities[]

Each space entity (room) contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `global_id` | string | Yes | IFC GlobalId |
| `name` | string | Yes | Space name (often room number) |
| `long_name` | string | No | Extended name |
| `description` | string | No | Space description |
| `floor_id` | string | No | Parent floor global_id |
| `placement` | object | No | 3D coordinates |
| `bounding_box` | object | No | Space bounding box (reserved) |
| `properties` | object | No | Additional properties |

**Placement Object:**
```json
{
  "x": 10.5,
  "y": 5.2,
  "z": 0.0
}
```

### equipment_entities[]

Each equipment entity contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `global_id` | string | Yes | IFC GlobalId |
| `name` | string | Yes | Equipment name |
| `description` | string | No | Equipment description |
| `object_type` | string | Yes | IFC type (e.g., "IfcAirTerminalBox") |
| `tag` | string | No | Equipment tag/identifier |
| `space_id` | string | No | Parent space global_id |
| `placement` | object | No | 3D coordinates |
| `category` | string | Yes | Arxos category (hvac, electrical, plumbing, etc.) |
| `property_sets` | array | No | Array of property sets |
| `classification` | array | No | Classification references (reserved) |

**Property Set Object:**
```json
{
  "name": "Pset_AirTerminalBoxTypeCommon",
  "properties": {
    "NominalAirFlowRate": 500.0,
    "NominalPower": 1200.0,
    "FinishType": "Painted Steel"
  }
}
```

**Category Mapping:**

The service automatically maps IFC types to Arxos categories:

| IFC Types | Arxos Category |
|-----------|---------------|
| IfcElectricDistributionBoard, IfcElectricGenerator | `electrical` |
| IfcAirTerminal, IfcAirTerminalBox, IfcBoiler, IfcChiller, IfcFan, IfcValve, IfcFlowTerminal | `hvac` |
| IfcSanitaryTerminal, IfcWasteTerminal | `plumbing` |
| IfcFireSuppressionTerminal, IfcAlarm, IfcSensor | `safety` |
| IfcLightFixture, IfcLamp | `lighting` |
| IfcCommunicationsAppliance, IfcAudioVisualAppliance | `network` |
| Others | `other` |

### relationships[]

Each relationship contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Relationship type (currently "contains") |
| `relating_object` | string | Yes | Parent entity global_id |
| `related_objects` | array | Yes | Array of child entity global_ids |
| `description` | string | No | Relationship description |

**Example:**
```json
{
  "type": "contains",
  "relating_object": "3pDfk9sdF2x9483jdkFl03",
  "related_objects": ["0YgR8dkF3x0394jfkDl93", "1YhS9elG4y1405kgmEn04"],
  "description": "Spatial containment"
}
```

---

## IFC Validation Endpoint

### Validate IFC File

```http
POST /api/validate
Content-Type: application/octet-stream
```

**Request Body:** Raw IFC file data (binary)

**Response:**
```json
{
  "success": true,
  "valid": true,
  "warnings": [
    "No IfcSite found - recommended for buildingSMART compliance"
  ],
  "errors": [],
  "compliance": {
    "buildingSMART": true,
    "IFC4": true,
    "spatial_consistency": true,
    "data_integrity": true
  },
  "metadata": {
    "ifc_version": "IFC4",
    "file_size": 1024000,
    "processing_time": 1.2,
    "timestamp": "2025-10-17T12:00:00Z"
  },
  "entity_counts": {
    "IfcProject": 1,
    "IfcBuilding": 1,
    "IfcBuildingStorey": 3,
    "IfcSpace": 25,
    "total_products": 500
  },
  "spatial_issues": [
    "Entity 1KjDf8sdK3x8473hfkEl82 missing ObjectPlacement"
  ],
  "schema_issues": []
}
```

---

## Spatial Query Endpoints

### Spatial Query

```http
POST /api/spatial/query
Content-Type: application/json
```

**Request Body:**
```json
{
  "operation": "within_bounds",
  "bounds": {
    "min": [0, 0, 0],
    "max": [100, 100, 100]
  }
}
```

**Note:** IFC data should be sent as query parameter or in multipart form (implementation varies)

**Response:**
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
      "global_id": "0YgR8dkF3x0394jfkDl93",
      "name": "Room 101",
      "type": "IfcSpace",
      "coordinates": [[10.5, 5.2, 0.0]],
      "center": [10.5, 5.2, 0.0]
    }
  ],
  "total_found": 1,
  "metadata": {
    "timestamp": "2025-10-17T12:00:00Z",
    "entity_types_searched": ["IfcSpace", "IfcWall", "IfcSlab", "IfcBeam", "IfcColumn", "IfcDoor", "IfcWindow"]
  }
}
```

**Supported Operations:**
- `within_bounds` - Find entities within 3D bounding box
- `spatial_relationships` - Find relationships for specific entity
- `proximity` - Find entities within radius of a point
- `statistics` - Get spatial statistics for entire model

### Get Spatial Bounds

```http
POST /api/spatial/bounds
Content-Type: application/octet-stream
```

**Request Body:** Raw IFC file data (binary)

**Response:**
```json
{
  "success": true,
  "bounding_box": {
    "min": [0.0, 0.0, 0.0],
    "max": [50.0, 30.0, 15.0]
  },
  "spatial_coverage": {
    "width": 50.0,
    "height": 30.0,
    "depth": 15.0,
    "area": 1500.0,
    "volume": 22500.0
  },
  "entity_counts": {
    "IfcSpace": 25,
    "IfcWall": 200,
    "IfcDoor": 50
  },
  "metadata": {
    "timestamp": "2025-10-17T12:00:00Z",
    "total_entities": 501
  }
}
```

---

## Service Metrics

### Get Metrics

```http
GET /metrics
```

**Response:**
```json
{
  "success": true,
  "service": "ifcopenshell",
  "timestamp": "2025-10-17T12:00:00Z",
  "cache_stats": {
    "hits": 85,
    "misses": 65,
    "sets": 150,
    "evictions": 5,
    "hit_rate_percent": 56.67,
    "local_cache_size": 12,
    "redis_connected": true
  },
  "performance_metrics": {
    "uptime_seconds": 3600,
    "requests_total": 150,
    "requests_per_second": 0.042,
    "error_rate": 0.02,
    "requests_by_endpoint": {
      "parse": {"total": 100, "success": 98, "errors": 2, "avg_time": 2.3},
      "validate": {"total": 50, "success": 50, "errors": 0, "avg_time": 1.1}
    },
    "processing_time_percentiles": {
      "p50": 1.5,
      "p90": 2.8,
      "p95": 3.2,
      "p99": 4.5
    },
    "memory_usage": [
      {"timestamp": 1697548800, "rss": 524288000, "vms": 1048576000}
    ]
  },
  "configuration": {
    "max_file_size_mb": 50.0,
    "cache_ttl_seconds": 3600,
    "cache_enabled": true
  }
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional": "context"
    },
    "timestamp": "2025-10-17T12:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NO_DATA` | 400 | No IFC data provided in request |
| `FILE_TOO_LARGE` | 413 | File exceeds maximum size limit |
| `INVALID_FORMAT` | 400 | File is not valid IFC format |
| `IFC_PARSE_ERROR` | 400 | Error parsing IFC file |
| `IFC_VALIDATION_ERROR` | 500 | Error during validation |
| `SPATIAL_QUERY_ERROR` | 500 | Spatial query failed |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Integration Guide for Go Developers

### Basic Integration

```go
// 1. Call the service
client := &http.Client{Timeout: 30 * time.Second}
resp, err := client.Post(
    "http://ifcopenshell-service:5000/api/parse",
    "application/octet-stream",
    bytes.NewReader(ifcData),
)

// 2. Parse response
var result map[string]interface{}
json.NewDecoder(resp.Body).Decode(&result)

// 3. Check success
if !result["success"].(bool) {
    return fmt.Errorf("IFC parsing failed: %v", result["error"])
}
```

### Extracting Entity Arrays

```go
// Extract building entities
buildingEntities := result["building_entities"].([]interface{})
for _, entity := range buildingEntities {
    bldg := entity.(map[string]interface{})
    
    // Create domain.Building
    building := &domain.Building{
        ID:      types.NewID(),
        Name:    bldg["name"].(string),
        Address: extractAddress(bldg["address"]),
    }
    
    // Map global_id for later reference
    globalIDMap[bldg["global_id"].(string)] = building.ID
}

// Extract floor entities
floorEntities := result["floor_entities"].([]interface{})
for _, entity := range floorEntities {
    flr := entity.(map[string]interface{})
    
    floor := &domain.Floor{
        ID:      types.NewID(),
        Name:    flr["name"].(string),
        Level:   inferLevel(flr["elevation"].(float64)),
    }
    
    globalIDMap[flr["global_id"].(string)] = floor.ID
}

// Extract space entities
spaceEntities := result["space_entities"].([]interface{})
for _, entity := range spaceEntities {
    spc := entity.(map[string]interface{})
    
    // Get parent floor ID
    floorGlobalID := spc["floor_id"].(string)
    floorID := globalIDMap[floorGlobalID]
    
    room := &domain.Room{
        ID:      types.NewID(),
        FloorID: floorID,
        Name:    spc["name"].(string),
        Number:  spc["name"].(string), // Use name as number if not specified
    }
    
    // Extract placement if available
    if placement, ok := spc["placement"].(map[string]interface{}); ok {
        room.Location = &domain.Location{
            X: placement["x"].(float64),
            Y: placement["y"].(float64),
            Z: placement["z"].(float64),
        }
    }
    
    globalIDMap[spc["global_id"].(string)] = room.ID
}

// Extract equipment entities
equipmentEntities := result["equipment_entities"].([]interface{})
for _, entity := range equipmentEntities {
    eq := entity.(map[string]interface{})
    
    // Get parent space ID
    spaceGlobalID := eq["space_id"].(string)
    roomID := globalIDMap[spaceGlobalID]
    
    equipment := &domain.Equipment{
        ID:       types.NewID(),
        RoomID:   roomID,
        Name:     eq["name"].(string),
        Type:     eq["object_type"].(string),
        Category: eq["category"].(string),
    }
    
    // Extract placement
    if placement, ok := eq["placement"].(map[string]interface{}); ok {
        equipment.Location = &domain.Location{
            X: placement["x"].(float64),
            Y: placement["y"].(float64),
            Z: placement["z"].(float64),
        }
    }
    
    // Extract property sets
    if propertySets, ok := eq["property_sets"].([]interface{}); ok {
        equipment.Metadata = extractPropertySets(propertySets)
    }
    
    globalIDMap[eq["global_id"].(string)] = equipment.ID
}
```

### Helper Functions

```go
// Extract address from IFC address object
func extractAddress(addressObj interface{}) string {
    if addressObj == nil {
        return ""
    }
    
    addr := addressObj.(map[string]interface{})
    lines := addr["address_lines"].([]interface{})
    town := addr["town"].(string)
    region := addr["region"].(string)
    country := addr["country"].(string)
    
    // Format as single address string
    addressParts := []string{}
    for _, line := range lines {
        addressParts = append(addressParts, line.(string))
    }
    if town != "" {
        addressParts = append(addressParts, town)
    }
    if region != "" {
        addressParts = append(addressParts, region)
    }
    if country != "" {
        addressParts = append(addressParts, country)
    }
    
    return strings.Join(addressParts, ", ")
}

// Extract property sets as metadata
func extractPropertySets(propertySets []interface{}) map[string]interface{} {
    metadata := make(map[string]interface{})
    
    for _, pset := range propertySets {
        psetObj := pset.(map[string]interface{})
        psetName := psetObj["name"].(string)
        properties := psetObj["properties"].(map[string]interface{})
        
        // Flatten property sets into metadata
        for propName, propValue := range properties {
            key := fmt.Sprintf("%s.%s", psetName, propName)
            metadata[key] = propValue
        }
    }
    
    return metadata
}

// Infer floor level from elevation
func inferLevel(elevation float64) int {
    // Simple heuristic: divide by typical floor height (3.5m)
    level := int(elevation / 3.5)
    if elevation < 0 {
        return -1 // Basement
    }
    return level
}
```

---

## Caching Behavior

### Cache Key Generation

The service uses MD5 hashing of IFC file content:

```python
cache_key = f"ifc:parse:{md5(ifc_data).hexdigest()}"
```

### Cache Tiers

1. **Redis Cache** (primary)
   - TTL: Configurable via `CACHE_TTL` (default 3600s)
   - Shared across service replicas
   - Automatic eviction on TTL expiry

2. **Local Memory Cache** (fallback)
   - TTL: Same as Redis
   - Per-instance cache
   - Automatic cleanup at 1000 entries

### Cache Hit Behavior

- Cache hit: Returns cached result in ~10ms
- Cache miss: Processes IFC file (1-5 seconds depending on size)
- Subsequent identical files use cached results

---

## Performance Characteristics

### Processing Times

| File Size | Entity Count | Typical Processing Time |
|-----------|--------------|------------------------|
| < 1 MB | < 100 | 0.5-1.0s |
| 1-10 MB | 100-1000 | 1.0-3.0s |
| 10-50 MB | 1000-5000 | 3.0-10.0s |
| 50-100 MB | 5000+ | 10.0-30.0s |

**Note:** Times are for initial processing. Cached requests return in ~10ms.

### Resource Requirements

- **Memory**: 512MB-2GB depending on IFC complexity
- **CPU**: Single-threaded processing (no parallel entity extraction currently)
- **Disk**: Minimal (Redis cache stored in memory by default)

### Scaling

**Horizontal Scaling:**
- Production deployment: 3 replicas with Nginx load balancing
- Each replica has independent local cache
- Shared Redis cache across all replicas
- Load balancer distributes requests round-robin

**Vertical Scaling:**
- Increase `MAX_FILE_SIZE` for larger files
- Increase memory limits for complex models
- Adjust cache TTL based on usage patterns

---

## Testing the Service

### Using curl

```bash
# Health check
curl http://localhost:5000/health

# Parse IFC file
curl -X POST http://localhost:5000/api/parse \
  -H "Content-Type: application/octet-stream" \
  --data-binary @building.ifc

# Validate IFC file
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/octet-stream" \
  --data-binary @building.ifc

# Get metrics
curl http://localhost:5000/metrics
```

### Using Python

```python
import requests

# Parse IFC file
with open('building.ifc', 'rb') as f:
    ifc_data = f.read()

response = requests.post(
    'http://localhost:5000/api/parse',
    data=ifc_data,
    headers={'Content-Type': 'application/octet-stream'}
)

result = response.json()
print(f"Buildings: {result['buildings']}")
print(f"Detailed entities: {len(result['building_entities'])}")
```

### Using Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "io/ioutil"
    "net/http"
)

func parseIFC(ifcData []byte) (map[string]interface{}, error) {
    client := &http.Client{}
    
    resp, err := client.Post(
        "http://localhost:5000/api/parse",
        "application/octet-stream",
        bytes.NewReader(ifcData),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return result, nil
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Flask environment |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Host to bind to |
| `PORT` | `5001` | Port to listen on |
| `MAX_FILE_SIZE` | `52428800` | Max file size in bytes (50MB) |
| `CACHE_ENABLED` | `true` | Enable caching |
| `CACHE_TTL` | `3600` | Cache TTL in seconds |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database number |
| `LOG_LEVEL` | `INFO` | Logging level |

### Docker Compose Configuration

```yaml
ifcopenshell-service:
  build: ./services/ifcopenshell-service
  ports:
    - "5000:5000"
  environment:
    - FLASK_ENV=production
    - MAX_FILE_SIZE=104857600  # 100MB
    - CACHE_ENABLED=true
    - REDIS_HOST=redis
  depends_on:
    - redis
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## Troubleshooting

### Common Issues

**1. Service Returns Only Counts, Not Entity Arrays**
- **Check**: Ensure using latest service version with entity extraction
- **Verify**: Response should include `building_entities`, `floor_entities`, etc.
- **Solution**: Update to service version 1.0.0+

**2. Empty Entity Arrays Despite Non-Zero Counts**
- **Cause**: IFC file may have entities that failed extraction
- **Check**: Review service logs for warnings about entity extraction failures
- **Solution**: Validate IFC file structure

**3. Missing Parent References (floor_id, space_id)**
- **Cause**: IFC file missing `IfcRelContainedInSpatialStructure` relationships
- **Check**: Validate IFC spatial hierarchy
- **Solution**: Use relationships array to establish links manually

**4. Property Sets Empty**
- **Cause**: IFC file may not include property sets (Psets)
- **Check**: Verify IFC export settings in CAD software
- **Solution**: Re-export IFC with property sets enabled

**5. Placement Coordinates Are Null**
- **Cause**: IFC entities missing `ObjectPlacement` or `IfcLocalPlacement`
- **Check**: Review IFC file completeness
- **Solution**: Add placement data in CAD software before export

---

## Best Practices

### For ArxOS Developers

1. **Always check `success` field** before processing results
2. **Handle missing optional fields** (placement, floor_id, space_id)
3. **Build global_id mapping** for cross-referencing entities
4. **Use property_sets** to populate Equipment.Metadata
5. **Validate category mapping** against Arxos taxonomy
6. **Wrap imports in transactions** for atomicity
7. **Log entity extraction counts** for debugging

### For IFC File Preparation

1. **Export from CAD with property sets** enabled
2. **Include spatial hierarchy** (Building → Storey → Space)
3. **Ensure entities have GlobalIds** (required for references)
4. **Add placement data** for 3D coordinates
5. **Use IFC4 schema** for best compatibility
6. **Validate with buildingSMART checker** before import

---

## Related Documentation

- [IfcOpenShell Integration Architecture](IFCOPENSHELL_INTEGRATION.md)
- [IFC Import User Guide](../guides/ifc-import-guide.md)
- [ArxOS API Documentation](../api/API_DOCUMENTATION.md)
- [Service Architecture](../architecture/SERVICE_ARCHITECTURE.md)

---

**Status**: Production-ready with full entity extraction ✅  
**Version**: 1.0.0  
**Last Updated**: October 17, 2025

