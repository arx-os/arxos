# Coordinate Transformations Precision Update

## Overview

This document describes the comprehensive update to coordinate transformation utilities to integrate with the precision system. All transformation operations now use `PrecisionMath`, `PrecisionCoordinate`, and include precision validation hooks and error handling.

## Key Features

### 1. Precision-Aware CoordinateTransformation Class

The `CoordinateTransformation` class has been completely refactored to:
- Use `PrecisionMath` for all arithmetic operations
- Integrate precision validation hooks
- Provide comprehensive error handling
- Support individual transformation operations (scale, rotate, translate)

### 2. Enhanced Unit Conversion System

The `convert_units` function has been updated to:
- Use precision math for all calculations
- Support extended unit types (km, yd, mi, px, pt, pc)
- Include comprehensive validation
- Provide detailed error reporting

### 3. Batch Coordinate Transformation

The `transform_coordinates_batch` function now:
- Converts coordinates to `PrecisionCoordinate` instances
- Uses precision math for all transformations
- Validates results against configurable thresholds
- Provides detailed error handling

## Updated Functions

### CoordinateTransformation Class

#### `__init__(config: Optional[PrecisionConfig] = None)`
Initialize coordinate transformation with precision configuration.

**Parameters:**
- `config`: Precision configuration (optional, uses default if not provided)

**Example:**
```python
from svgx_engine.core.precision_coordinate import CoordinateTransformation
from svgx_engine.core.precision_config import config_manager

config = config_manager.get_default_config()
transformer = CoordinateTransformation(config)
```

#### `create_transformation_matrix(scale: float = 1.0, rotation: float = 0.0, translation: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> np.ndarray`
Create a 4x4 transformation matrix with precision validation.

**Parameters:**
- `scale`: Scale factor (must be positive)
- `rotation`: Rotation angle in radians
- `translation`: Translation vector (dx, dy, dz)

**Returns:**
- `np.ndarray`: 4x4 transformation matrix

**Validation:**
- Scale factor must be positive
- Rotation angle warnings for values outside [-2π, 2π]

**Example:**
```python
# Create identity matrix
identity = transformer.create_transformation_matrix()

# Create scaling matrix
scale_matrix = transformer.create_transformation_matrix(scale=2.0)

# Create translation matrix
trans_matrix = transformer.create_transformation_matrix(translation=(1.0, 2.0, 3.0))

# Create complex transformation
complex_matrix = transformer.create_transformation_matrix(
    scale=2.0,
    rotation=math.pi/4,
    translation=(1.0, 1.0, 0.0)
)
```

#### `apply_transformation(coordinate: PrecisionCoordinate, matrix: np.ndarray) -> PrecisionCoordinate`
Apply transformation matrix to coordinate with precision validation.

**Parameters:**
- `coordinate`: Coordinate to transform
- `matrix`: 4x4 transformation matrix

**Returns:**
- `PrecisionCoordinate`: Transformed coordinate

**Validation:**
- Matrix must be 4x4
- Transformed coordinates validated against maximum range

**Example:**
```python
coord = PrecisionCoordinate(1.0, 2.0, 3.0)
matrix = transformer.create_transformation_matrix(scale=2.0)
transformed = transformer.apply_transformation(coord, matrix)
```

#### `scale_coordinate(coordinate: PrecisionCoordinate, scale_factor: float) -> PrecisionCoordinate`
Scale a coordinate with precision validation.

**Parameters:**
- `coordinate`: Coordinate to scale
- `scale_factor`: Scale factor (must be positive)

**Returns:**
- `PrecisionCoordinate`: Scaled coordinate

**Example:**
```python
coord = PrecisionCoordinate(1.0, 2.0, 3.0)
scaled = transformer.scale_coordinate(coord, 2.0)
# Result: PrecisionCoordinate(2.0, 4.0, 6.0)
```

#### `rotate_coordinate(coordinate: PrecisionCoordinate, angle: float, center: Optional[PrecisionCoordinate] = None) -> PrecisionCoordinate`
Rotate a coordinate around a center point with precision validation.

**Parameters:**
- `coordinate`: Coordinate to rotate
- `angle`: Rotation angle in radians
- `center`: Center point for rotation (default: origin)

**Returns:**
- `PrecisionCoordinate`: Rotated coordinate

**Example:**
```python
coord = PrecisionCoordinate(1.0, 0.0, 0.0)
center = PrecisionCoordinate(1.0, 1.0, 0.0)

# Rotate 90 degrees around center
rotated = transformer.rotate_coordinate(coord, math.pi/2, center)
```

#### `translate_coordinate(coordinate: PrecisionCoordinate, dx: float, dy: float, dz: float = 0.0) -> PrecisionCoordinate`
Translate a coordinate with precision validation.

**Parameters:**
- `coordinate`: Coordinate to translate
- `dx`: X translation offset
- `dy`: Y translation offset
- `dz`: Z translation offset (default: 0.0)

**Returns:**
- `PrecisionCoordinate`: Translated coordinate

**Example:**
```python
coord = PrecisionCoordinate(1.0, 2.0, 3.0)
translated = transformer.translate_coordinate(coord, 1.0, 2.0, 3.0)
# Result: PrecisionCoordinate(2.0, 4.0, 6.0)
```

### Unit Conversion Functions

#### `convert_units(value: str, from_unit: str, to_unit: str) -> float`
Convert between different units with precision validation.

**Parameters:**
- `value`: Value to convert (string with unit or numeric)
- `from_unit`: Source unit
- `to_unit`: Target unit

**Supported Units:**
- Metric: mm, cm, m, km
- Imperial: in, ft, yd, mi
- Digital: px, pt, pc

**Returns:**
- `float`: Converted value

**Validation:**
- Unknown units raise ValueError
- Negative values generate warnings
- Results validated against min/max thresholds

**Example:**
```python
from svgx_engine.parser.geometry import SVGXGeometry

geometry = SVGXGeometry()

# Basic conversions
result = geometry.convert_units("10mm", "mm", "cm")  # 1.0
result = geometry.convert_units("5cm", "cm", "mm")   # 50.0
result = geometry.convert_units("2m", "m", "mm")     # 2000.0

# Extended units
result = geometry.convert_units("1km", "km", "m")    # 1000.0
result = geometry.convert_units("3ft", "ft", "yd")   # 1.0
result = geometry.convert_units("96px", "px", "mm")  # ~25.4
```

### Batch Transformation Functions

#### `transform_coordinates_batch(coordinates: List[List[float]], source_system: str, target_system: str, transformation_matrix: Optional[List[List[float]]] = None) -> List[List[float]]`
Transform coordinates between different coordinate systems with precision validation.

**Parameters:**
- `coordinates`: List of [x, y] coordinates to transform
- `source_system`: Source coordinate system
- `target_system`: Target coordinate system
- `transformation_matrix`: Optional 4x4 transformation matrix

**Returns:**
- `List[List[float]]`: Transformed coordinates

**Supported Systems:**
- svg
- real_world_meters
- real_world_feet

**Example:**
```python
from core.svg_parser.services.transform import transform_coordinates_batch

coordinates = [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]
matrix = [
    [2.0, 0.0, 0.0, 0.0],
    [0.0, 2.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
]

transformed = transform_coordinates_batch(
    coordinates, "svg", "real_world", matrix
)
```

#### `apply_matrix_transformation_precision(coordinates: List[PrecisionCoordinate], matrix: List[List[float]], config: Optional[PrecisionConfig] = None) -> List[List[float]]`
Apply 4x4 transformation matrix to precision coordinates with validation.

**Parameters:**
- `coordinates`: List of PrecisionCoordinate instances
- `matrix`: 4x4 transformation matrix
- `config`: Precision configuration (optional)

**Returns:**
- `List[List[float]]`: Transformed coordinates as [x, y] lists

**Example:**
```python
from core.svg_parser.services.transform import apply_matrix_transformation_precision

precision_coords = [
    PrecisionCoordinate(0.0, 0.0, 0.0),
    PrecisionCoordinate(1.0, 1.0, 0.0)
]

transformed = apply_matrix_transformation_precision(
    precision_coords, scale_matrix
)
```

## Validation Rules

### Coordinate Transformation Validation

```python
# Configuration for coordinate transformation validation
validation_rules = {
    'max_coordinate': 1e6,        # Maximum coordinate value
    'min_scale_factor': 1e-6,     # Minimum scale factor
    'max_scale_factor': 1e6,      # Maximum scale factor
    'max_rotation_angle': 2 * math.pi,  # Maximum rotation angle
    'min_transformation_result': 1e-12,  # Minimum transformation result
    'max_transformation_result': 1e12    # Maximum transformation result
}
```

### Unit Conversion Validation

```python
# Configuration for unit conversion validation
validation_rules = {
    'max_unit_value': 1e9,        # Maximum input value
    'min_unit_result': 1e-12,     # Minimum conversion result
    'max_unit_result': 1e12,      # Maximum conversion result
    'supported_units': [           # Supported unit types
        'mm', 'cm', 'm', 'km',
        'in', 'ft', 'yd', 'mi',
        'px', 'pt', 'pc'
    ]
}
```

## Configuration

### Precision Configuration

```python
from svgx_engine.core.precision_config import PrecisionConfig

config = PrecisionConfig(
    enable_geometric_validation=True,
    enable_coordinate_validation=True,
    validation_rules={
        'max_coordinate': 1e6,
        'min_scale_factor': 1e-6,
        'max_scale_factor': 1e6,
        'max_rotation_angle': 2 * math.pi,
        'max_unit_value': 1e9,
        'min_unit_result': 1e-12,
        'max_unit_result': 1e12
    }
)
```

### Hook Configuration

```python
from svgx_engine.core.precision_hooks import hook_manager, HookType

# Register custom validation hooks
def custom_transformation_hook(context: HookContext) -> HookContext:
    # Custom validation logic
    return context

hook_manager.register_hook(
    hook_id="custom_transformation",
    hook_type=HookType.GEOMETRIC_CONSTRAINT,
    function=custom_transformation_hook,
    priority=0
)
```

## Error Handling

### Error Types

1. **PrecisionErrorType.GEOMETRIC_ERROR**: Invalid geometric parameters
2. **PrecisionErrorType.TRANSFORMATION_ERROR**: Transformation operation failures
3. **PrecisionErrorType.CALCULATION_ERROR**: Mathematical calculation errors

### Error Severity Levels

1. **PrecisionErrorSeverity.WARNING**: Non-critical issues
2. **PrecisionErrorSeverity.ERROR**: Critical issues that may affect results

### Error Recovery

```python
from svgx_engine.core.precision_errors import PrecisionErrorHandler

# Configure error handling
error_handler = PrecisionErrorHandler()
error_handler.set_recovery_strategy(
    PrecisionErrorType.TRANSFORMATION_ERROR,
    "fallback_to_identity"
)
```

## Testing

### Running Tests

```bash
# Run all coordinate transformation tests
pytest tests/test_coordinate_transformations_precision.py -v

# Run specific test class
pytest tests/test_coordinate_transformations_precision.py::TestCoordinateTransformationClass -v

# Run specific test method
pytest tests/test_coordinate_transformations_precision.py::TestCoordinateTransformationClass::test_transformation_matrix_creation -v
```

### Test Coverage

The test suite covers:
- ✅ Transformation matrix creation and validation
- ✅ Individual transformation operations (scale, rotate, translate)
- ✅ Batch coordinate transformation
- ✅ Unit conversion with extended unit support
- ✅ Error handling and recovery
- ✅ Precision validation hooks
- ✅ Edge cases and boundary conditions

## Performance Characteristics

### Computational Performance
- **Fast transformations**: Optimized numpy operations with precision math
- **Memory efficient**: Minimal memory overhead for precision operations
- **Scalable**: Efficient batch processing for large coordinate sets

### Precision Accuracy
- **Sub-millimeter precision**: 0.001mm tolerance maintained through transformations
- **64-bit floating point**: numpy.float64 for performance
- **Decimal backup**: Decimal class for maximum precision when needed

## Migration Guide

### From Legacy Transformation Functions

**Before:**
```python
# Old transformation approach
coord = PrecisionCoordinate(1.0, 2.0, 3.0)
scaled = coord.scale(2.0)  # Direct scaling
```

**After:**
```python
# New precision-aware approach
transformer = CoordinateTransformation()
coord = PrecisionCoordinate(1.0, 2.0, 3.0)
scaled = transformer.scale_coordinate(coord, 2.0)  # With validation
```

### From Legacy Unit Conversion

**Before:**
```python
# Old unit conversion
def convert_units_simple(value, from_unit, to_unit):
    # Basic conversion without validation
    pass
```

**After:**
```python
# New precision-aware unit conversion
geometry = SVGXGeometry()
result = geometry.convert_units("10mm", "mm", "cm")  # With validation
```

## Usage Examples

### Complete Transformation Pipeline

```python
from svgx_engine.core.precision_coordinate import CoordinateTransformation, PrecisionCoordinate
from svgx_engine.core.precision_config import config_manager

# Initialize with configuration
config = config_manager.get_default_config()
transformer = CoordinateTransformation(config)

# Create coordinate
coord = PrecisionCoordinate(1.0, 2.0, 3.0)

# Apply complex transformation
matrix = transformer.create_transformation_matrix(
    scale=2.0,
    rotation=math.pi/4,
    translation=(1.0, 1.0, 0.0)
)

transformed = transformer.apply_transformation(coord, matrix)
print(f"Original: {coord}")
print(f"Transformed: {transformed}")
```

### Batch Processing

```python
from core.svg_parser.services.transform import transform_coordinates_batch

# Process multiple coordinates
coordinates = [
    [0.0, 0.0],
    [1.0, 1.0],
    [2.0, 2.0],
    [3.0, 3.0]
]

# Transform with matrix
matrix = [
    [2.0, 0.0, 0.0, 1.0],
    [0.0, 2.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
]

transformed = transform_coordinates_batch(
    coordinates, "svg", "real_world", matrix
)

for i, (original, result) in enumerate(zip(coordinates, transformed)):
    print(f"Point {i}: {original} -> {result}")
```

### Unit Conversion Pipeline

```python
from svgx_engine.parser.geometry import SVGXGeometry

geometry = SVGXGeometry()

# Convert various units
conversions = [
    ("10mm", "mm", "cm"),
    ("5cm", "cm", "mm"),
    ("2m", "m", "mm"),
    ("1in", "in", "mm"),
    ("1km", "km", "m"),
    ("3ft", "ft", "yd")
]

for value, from_unit, to_unit in conversions:
    result = geometry.convert_units(value, from_unit, to_unit)
    print(f"{value} ({from_unit} -> {to_unit}) = {result}")
```

## Troubleshooting

### Common Issues

1. **Invalid Scale Factor Error**
   - **Cause**: Negative or zero scale factor
   - **Solution**: Ensure scale factor is positive

2. **Unknown Unit Error**
   - **Cause**: Unsupported unit type
   - **Solution**: Use supported units (mm, cm, m, km, in, ft, yd, mi, px, pt, pc)

3. **Matrix Shape Error**
   - **Cause**: Non-4x4 transformation matrix
   - **Solution**: Ensure matrix is 4x4 for homogeneous coordinates

4. **Coordinate Range Error**
   - **Cause**: Coordinates exceed maximum range
   - **Solution**: Check coordinate values and adjust validation rules if needed

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check configuration
config = config_manager.get_default_config()
print(f"Validation enabled: {config.enable_geometric_validation}")
print(f"Validation rules: {config.validation_rules}")
```

## Future Enhancements

### Planned Features

1. **Advanced Transformation Types**
   - Shear transformations
   - Non-uniform scaling
   - 3D rotation around arbitrary axes

2. **Extended Unit Support**
   - Additional metric units (µm, nm)
   - Additional imperial units (chains, furlongs)
   - Custom unit definitions

3. **Performance Optimizations**
   - GPU acceleration for large batches
   - Parallel processing for multiple transformations
   - Memory pooling for coordinate objects

4. **Advanced Validation**
   - Geometric constraint validation
   - Physical unit validation
   - Custom validation rules

### Integration Points

1. **CAD System Integration**
   - AutoCAD transformation compatibility
   - Revit coordinate system support
   - SketchUp transformation matrices

2. **GIS System Integration**
   - WGS84 coordinate transformations
   - UTM projection support
   - Custom projection systems

3. **Real-time Applications**
   - AR/VR coordinate transformations
   - Real-time tracking systems
   - Mobile device coordinate systems
