# Coordinate Validation Specification

## Overview

This document defines the coordinate validation system for the Arxos platform, providing consistent validation rules and utilities across Python and Go components for 2D coordinate processing.

## Coordinate Definition

A 2D coordinate is defined as a point in 2-dimensional space with X and Y values:

```typescript
interface Coordinate2D {
  x: number;  // X coordinate value
  y: number;  // Y coordinate value
}
```

## Validation Rules

### Default Validation Configuration

- **Value Range**: -1,000,000 to +1,000,000
- **NaN Values**: Not allowed (configurable)
- **Infinite Values**: Not allowed (configurable)
- **Data Type**: Must be numeric (float64 in Go, float in Python)

### Validation Checks

1. **Type Validation**: Both X and Y must be numeric values
2. **Range Validation**: Values must be within configured min/max bounds
3. **Special Value Validation**: NaN and infinite values are rejected by default
4. **Finite Validation**: Values must be finite numbers

## Implementation

### Go Implementation

Located in `arx-backend/utils/coordinate_utils.go`

```go
// Basic validation
coord := Coordinate2D{X: 100.5, Y: 200.75}
config := DefaultCoordinateConfig()
valid := IsValidCoordinate2D(coord, config)

// With custom configuration
config := CoordinateValidationConfig{
    MinValue: -1000,
    MaxValue: 1000,
    AllowNaN: false,
    AllowInf: false,
}
```

### Python Implementation

Located in `arx_svg_parser/utils/coordinate_utils.py`

```python
# Basic validation
coord = (100.5, 200.75)
valid = is_valid_coordinate(coord, dim=2, min_value=-1e6, max_value=1e6)

# With custom configuration
valid = is_valid_coordinate(coord, dim=2, min_value=-1000, max_value=1000)
```

## API Endpoints

### 1. Single Coordinate Validation

**Endpoint**: `POST /api/v1/coordinates/validate`

**Request**:
```json
{
  "coordinate": {
    "x": 100.5,
    "y": 200.75
  },
  "config": {
    "minValue": -1000,
    "maxValue": 1000,
    "allowNaN": false,
    "allowInf": false
  }
}
```

**Response**:
```json
{
  "valid": true,
  "coordinate": {
    "x": 100.5,
    "y": 200.75
  }
}
```

### 2. Batch Coordinate Validation

**Endpoint**: `POST /api/v1/coordinates/validate-batch`

**Request**:
```json
{
  "coordinates": [
    {"x": 100, "y": 200},
    {"x": 300, "y": 400},
    {"x": 500, "y": 600}
  ],
  "config": {
    "minValue": -1000,
    "maxValue": 1000
  }
}
```

**Response**:
```json
{
  "valid": true,
  "results": [
    {
      "valid": true,
      "coordinate": {"x": 100, "y": 200}
    },
    {
      "valid": true,
      "coordinate": {"x": 300, "y": 400}
    },
    {
      "valid": true,
      "coordinate": {"x": 500, "y": 600}
    }
  ],
  "summary": {
    "total": 3,
    "valid": 3,
    "invalid": 0
  }
}
```

### 3. Coordinate Parsing

**Endpoint**: `POST /api/v1/coordinates/parse`

**Request**:
```json
{
  "x": "100.5",
  "y": "200.75",
  "config": {
    "minValue": -1000,
    "maxValue": 1000
  }
}
```

**Response**:
```json
{
  "success": true,
  "coordinate": {
    "x": 100.5,
    "y": 200.75
  }
}
```

### 4. Geometric Operations

**Endpoint**: `POST /api/v1/coordinates/geometry`

**Supported Operations**:
- `distance`: Calculate Euclidean distance between two points
- `midpoint`: Calculate midpoint between two points
- `boundingBox`: Calculate bounding box for a set of points
- `pointInPolygon`: Check if a point is inside a polygon

**Example Request**:
```json
{
  "operation": "distance",
  "coordinates": [
    {"x": 0, "y": 0},
    {"x": 3, "y": 4}
  ]
}
```

**Response**:
```json
{
  "operation": "distance",
  "result": 5.0
}
```

## Error Handling

### Validation Errors

When validation fails, the API returns detailed error information:

```json
{
  "valid": false,
  "coordinate": {
    "x": 2000000,
    "y": 200.75
  },
  "errors": [
    "X coordinate 2000000 is outside valid range [-1000000, 1000000]"
  ]
}
```

### Common Error Scenarios

1. **Out of Range**: Values exceed configured min/max bounds
2. **NaN Values**: Non-numeric values when `allowNaN` is false
3. **Infinite Values**: Infinite values when `allowInf` is false
4. **Invalid Format**: Non-numeric strings in parsing operations
5. **Insufficient Data**: Missing required coordinates for operations

## Best Practices

### 1. Configuration Management

- Use default configuration for most cases
- Customize validation rules based on specific use cases
- Document configuration choices in your application

### 2. Error Handling

- Always check validation results before processing coordinates
- Provide meaningful error messages to users
- Log validation failures for debugging

### 3. Performance Considerations

- Use batch validation for multiple coordinates
- Cache validation results when appropriate
- Consider coordinate normalization for large datasets

### 4. Security

- Validate all input coordinates before processing
- Sanitize coordinate strings before parsing
- Implement rate limiting for API endpoints

## Testing

### Unit Tests

Both Go and Python implementations include comprehensive unit tests covering:

- Valid coordinate scenarios
- Invalid coordinate scenarios
- Edge cases (NaN, infinite, boundary values)
- Geometric operations
- Error conditions

### Integration Tests

API endpoints are tested with:

- Valid requests
- Invalid requests
- Error conditions
- Performance benchmarks

## Usage Examples

### Go Usage

```go
package main

import (
    "fmt"
    "arx-backend/utils"
)

func main() {
    // Validate a coordinate
    coord := utils.Coordinate2D{X: 100.5, Y: 200.75}
    config := utils.DefaultCoordinateConfig()

    if utils.IsValidCoordinate2D(coord, config) {
        fmt.Println("Coordinate is valid")

        // Calculate distance
        other := utils.Coordinate2D{X: 300, Y: 400}
        distance := utils.Distance2D(coord, other)
        fmt.Printf("Distance: %f\n", distance)
    } else {
        fmt.Println("Coordinate is invalid")
    }
}
```

### Python Usage

```python
from arx_svg_parser.utils.coordinate_utils import is_valid_coordinate, distance_2d

# Validate a coordinate
coord = (100.5, 200.75)
if is_valid_coordinate(coord, dim=2, min_value=-1e6, max_value=1e6):
    print("Coordinate is valid")

    # Calculate distance
    other = (300, 400)
    distance = distance_2d(coord, other)
    print(f"Distance: {distance}")
else:
    print("Coordinate is invalid")
```

### API Usage

```javascript
// Validate coordinate via API
const response = await fetch('/api/v1/coordinates/validate', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        coordinate: { x: 100.5, y: 200.75 },
        config: {
            minValue: -1000,
            maxValue: 1000
        }
    })
});

const result = await response.json();
if (result.valid) {
    console.log('Coordinate is valid');
} else {
    console.log('Validation errors:', result.errors);
}
```

## Migration Guide

### From Legacy Systems

1. **Identify coordinate usage**: Find all coordinate processing code
2. **Update validation**: Replace existing validation with new utilities
3. **Test thoroughly**: Ensure all coordinate operations work correctly
4. **Update documentation**: Document new validation rules

### Version Compatibility

- Version 1.0: Initial implementation with basic validation
- Future versions will maintain backward compatibility
- Deprecated features will be announced in advance

## Support and Maintenance

### Documentation

- API documentation: Available via OpenAPI specification
- Code documentation: Inline comments and examples
- Usage guides: This specification and examples

### Support

- Issues: Report via GitHub issues
- Questions: Contact development team
- Updates: Follow release notes for changes

### Contributing

- Follow coding standards for both Go and Python
- Include tests for new features
- Update documentation for changes
- Review existing implementations for consistency
