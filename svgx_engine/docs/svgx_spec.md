# SVGX Specification

## Overview

SVGX (Scalable Vector Graphics Extended) is a programmable spatial markup format that extends SVG with geometric precision, object semantics, programmable behavior, and spatial simulation capabilities suitable for CAD-level use cases.

## Core Principles

### 1. Backward Compatibility
SVGX maintains full compatibility with standard SVG while adding semantic extensions through the `arx:` namespace.

### 2. Geometric Precision
- Sub-mm precision support
- DXF-style units and path accuracy
- Precision attributes for CAD-grade accuracy

### 3. Object Intelligence
- Semantic markup for building elements
- System-level organization
- Programmable logic and behaviors

### 4. Spatial Awareness
- 2.5D and 3D layering support
- Z-index management
- Floorplan abstraction

## Namespace Definition

### Base Namespace
```xml
xmlns:arx="http://arxos.io/svgx"
```

### Core Attributes

#### Object Identification
```xml
arx:object="system.subsystem.component.instance"
arx:type="category.subcategory.specific_type"
arx:system="system_name"
```

#### Precision and Units
```xml
arx:precision="0.1mm"
arx:units="mm|cm|m|in|ft"
arx:scale="1.0"
```

#### Spatial Properties
```xml
arx:floor="1"
arx:room="A101"
arx:zone="mechanical"
arx:layer="electrical"
```

#### Behavior and Physics
```xml
arx:behavior="behavior_id"
arx:physics="physics_config"
arx:simulation="simulation_type"
```

## Element Types

### 1. Basic Elements
All standard SVG elements are supported with SVGX extensions:

```xml
<rect x="10" y="10" width="100" height="50"
      arx:object="electrical.panel.main"
      arx:type="electrical.panel.distribution"
      arx:system="electrical"/>
```

### 2. Semantic Elements

#### `<arx:object>`
Defines a semantic object with properties:
```xml
<arx:object id="light_fixture_01" type="electrical.light_fixture">
  <arx:properties>
    <arx:property name="voltage" value="120" unit="V"/>
    <arx:property name="power" value="20" unit="W"/>
    <arx:property name="lamp_type" value="LED"/>
  </arx:properties>
</arx:object>
```

#### `<arx:behavior>`
Defines programmable behavior:
```xml
<arx:behavior id="light_control">
  <arx:variables>
    <arx:variable name="voltage" value="120" unit="V"/>
    <arx:variable name="resistance" value="720" unit="ohm"/>
  </arx:variables>
  <arx:calculations>
    <arx:calculation name="current" formula="voltage / resistance"/>
    <arx:calculation name="power" formula="voltage * current"/>
  </arx:calculations>
  <arx:triggers>
    <arx:trigger event="motion_detected" action="turn_on"/>
    <arx:trigger event="no_motion" action="turn_off" delay="300"/>
  </arx:triggers>
</arx:behavior>
```

#### `<arx:physics>`
Defines physical properties:
```xml
<arx:physics id="fixture_physics">
  <arx:mass value="2.5" unit="kg"/>
  <arx:anchor point="ceiling"/>
  <arx:forces>
    <arx:force name="gravity" direction="down" magnitude="9.81"/>
    <arx:force name="wind" direction="horizontal" magnitude="0.5"/>
  </arx:forces>
  <arx:constraints>
    <arx:constraint type="fixed" point="mounting_point"/>
  </arx:constraints>
</arx:physics>
```

#### `<arx:system>`
Defines system-level organization:
```xml
<arx:system id="electrical_system" type="electrical">
  <arx:components>
    <arx:component ref="panel_main"/>
    <arx:component ref="light_fixture_01"/>
    <arx:component ref="outlet_01"/>
  </arx:components>
  <arx:connections>
    <arx:connection from="panel_main" to="light_fixture_01" type="power"/>
    <arx:connection from="panel_main" to="outlet_01" type="power"/>
  </arx:connections>
</arx:system>
```

## Data Types

### 1. Units
- **Length**: mm, cm, m, in, ft
- **Angle**: deg, rad
- **Time**: s, ms, min, h
- **Power**: W, kW, VA
- **Voltage**: V, kV
- **Current**: A, mA
- **Resistance**: ohm, kohm
- **Temperature**: C, F, K

### 2. Coordinates
- **2D**: (x, y) in specified units
- **2.5D**: (x, y, z) with z-index
- **3D**: (x, y, z) with full 3D coordinates

### 3. Colors
- Standard SVG color formats
- Extended with semantic colors:
  - `arx:color="electrical"`
  - `arx:color="mechanical"`
  - `arx:color="plumbing"`
  - `arx:color="fire_alarm"`

## Validation Rules

### 1. Object References
- All `arx:object` references must be valid
- Circular references are not allowed
- Object IDs must be unique within the document

### 2. Behavior Validation
- Variable names must be valid identifiers
- Formula syntax must be correct
- Trigger events must be defined
- Action handlers must exist

### 3. Physics Validation
- Mass values must be positive
- Force vectors must be valid
- Constraint points must exist
- Anchor points must be defined

### 4. System Validation
- Component references must be valid
- Connection endpoints must exist
- System types must be recognized
- Hierarchy must be acyclic

## Compatibility Matrix

### SVG Compatibility
| SVG Feature | SVGX Support | Notes |
|-------------|--------------|-------|
| Basic Shapes | ✅ Full | All standard shapes supported |
| Paths | ✅ Full | Enhanced with precision |
| Text | ✅ Full | With semantic markup |
| Gradients | ✅ Full | Standard SVG gradients |
| Filters | ✅ Full | Standard SVG filters |
| Animations | ✅ Full | Enhanced with behaviors |

### CAD Compatibility
| CAD Feature | SVGX Support | Notes |
|-------------|--------------|-------|
| Precision | ✅ Full | Sub-mm precision |
| Layers | ✅ Full | Semantic layering |
| Dimensions | ✅ Full | Smart dimensions |
| Constraints | ✅ Full | Geometric constraints |
| Annotations | ✅ Full | Rich annotations |

### BIM Compatibility
| BIM Feature | SVGX Support | Notes |
|-------------|--------------|-------|
| Object Properties | ✅ Full | Rich property sets |
| Spatial Relationships | ✅ Full | 3D spatial awareness |
| System Classification | ✅ Full | Multi-system support |
| Behavior Modeling | ✅ Full | Programmable behaviors |
| Physics Simulation | ✅ Full | Real-time simulation |

## File Extensions

### Primary Formats
- `.svgx` - SVGX format (recommended)
- `.svg` - Standard SVG (backward compatible)

### Export Formats
- `.ifc` - IFC format (BIM export)
- `.json` - JSON format (programmatic access)
- `.gltf` - GLTF format (3D visualization)
- `.dxf` - DXF format (CAD compatibility)

## Version History

### Version 1.0 (Current)
- Basic SVGX format definition
- Core namespace attributes
- Behavior and physics support
- Multi-format export

### Version 1.1 (Planned)
- Advanced constraint system
- Real-time collaboration
- AI-powered recognition
- Mobile support

### Version 2.0 (Future)
- 3D geometry support
- Advanced simulation
- Cloud integration
- Industry standards compliance

## Implementation Notes

### Parser Requirements
- XML namespace support
- Custom attribute handling
- Validation and error reporting
- Performance optimization

### Runtime Requirements
- Behavior engine
- Physics simulation
- Real-time updates
- Memory management

### Compiler Requirements
- Multi-format output
- Optimization strategies
- Error handling
- Performance benchmarks

## Best Practices

### 1. Object Naming
- Use hierarchical naming: `system.subsystem.component.instance`
- Be descriptive and consistent
- Include version information when needed

### 2. Precision
- Specify precision appropriate for the use case
- Use consistent units throughout
- Consider manufacturing tolerances

### 3. Organization
- Group related elements in systems
- Use semantic layers for organization
- Maintain clear hierarchy

### 4. Performance
- Minimize complex calculations in behaviors
- Use efficient physics models
- Optimize for real-time rendering

## Security Considerations

### 1. Code Execution
- Behaviors run in sandboxed environment
- Formula evaluation is restricted
- External calls are validated

### 2. Data Validation
- All inputs are validated
- Object references are checked
- System integrity is maintained

### 3. Access Control
- Role-based access to systems
- Permission-based modifications
- Audit trail for changes

## Future Extensions

### 1. AI Integration
- Automatic object recognition
- Smart behavior generation
- Predictive maintenance

### 2. IoT Integration
- Real-time sensor data
- Device communication
- Edge computing support

### 3. Cloud Services
- Collaborative editing
- Version control
- Analytics and reporting

---

This specification defines the SVGX format for programmable spatial markup. For implementation details, see the architecture documentation and API reference.
