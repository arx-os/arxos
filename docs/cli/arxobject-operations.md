# ArxObject Operations

ArxObjects are the fundamental building blocks of the Arxos system. Every element in a building - from structural beams to electrical outlets - is represented as an ArxObject with properties, relationships, and constraints.

## Understanding ArxObjects

### Object Structure

Every ArxObject has:
- **Unique ID**: Globally unique identifier
- **Type**: Object category (structural, electrical, mechanical, etc.)
- **Properties**: Key-value pairs defining object characteristics
- **Relationships**: Connections to other ArxObjects
- **Constraints**: Rules that must be maintained
- **Spatial Data**: 3D position, orientation, and geometry

### Object Hierarchy

```
ArxObject
├── Structural
│   ├── Beam
│   ├── Column
│   ├── Wall
│   └── Slab
├── Electrical
│   ├── Outlet
│   ├── Panel
│   ├── Circuit
│   └── Fixture
├── Mechanical
│   ├── Duct
│   ├── Pipe
│   ├── Equipment
│   └── Valve
└── Architectural
    ├── Room
    ├── Door
    ├── Window
    └── Space
```

## Basic Object Operations

### Viewing Objects

```bash
# Get specific object
arxos get outlet:R45-23

# View object with all properties
arxos get outlet:R45-23 --full

# View object relationships
arxos get outlet:R45-23 --relationships

# View object constraints
arxos get outlet:R45-23 --constraints
```

### Creating Objects

```bash
# Create new outlet
arxos create outlet --id=R45-24 --voltage=120 --amperage=20 \
  --location=(100,200,300) --wall=W-101

# Create with relationship
arxos create outlet R45-25 \
  --connected-to circuit:C-101 \
  --mounted-on wall:W-101

# Create from template
arxos create outlet --template=standard-120v --id=R45-26
```

### Modifying Objects

```bash
# Set single property
arxos set outlet:R45-23.voltage=240

# Set multiple properties
arxos set outlet:R45-23 voltage=240 amperage=30 gfci=true

# Modify with validation
arxos modify outlet:R45-23 voltage=240 --validate-constraints

# Conditional modification
arxos modify outlet:R45-23 voltage=240 --if="current-voltage=120"
```

### Deleting Objects

```bash
# Delete object (with dependency check)
arxos delete outlet:R45-23

# Force delete (bypass dependency check)
arxos delete outlet:R45-23 --force

# Delete with cascade
arxos delete circuit:C-101 --cascade=connected-outlets
```

## Property Management

### Property Types

ArxObjects support various property types:

```bash
# String properties
arxos set wall:W-101.material="concrete"

# Numeric properties  
arxos set beam:B-101.load-capacity=5000lbs

# Boolean properties
arxos set outlet:R45-23.gfci=true

# Array properties
arxos set room:R-205.occupancy-types=["office", "meeting"]

# Object references
arxos set outlet:R45-23.circuit=circuit:C-101
```

### Property Validation

```bash
# Validate single property change
arxos validate outlet:R45-23.voltage=240

# Validate multiple changes
arxos validate outlet:R45-23 voltage=240 amperage=30

# Check property constraints
arxos check-constraints outlet:R45-23 --property=voltage
```

### Property History

```bash
# View property change history
arxos history outlet:R45-23.voltage

# Compare property values over time
arxos diff outlet:R45-23 --from="2024-01-01" --to="now"

# Restore previous property value
arxos restore outlet:R45-23.voltage --to="2024-01-15T10:00:00Z"
```

## Relationship Management

### Creating Relationships

```bash
# Connect objects
arxos connect outlet:R45-23 to circuit:C-101

# Create spatial relationship
arxos mount outlet:R45-23 on wall:W-101

# Create dependency relationship
arxos depends beam:B-101 on column:COL-23
```

### Viewing Relationships

```bash
# Show all relationships
arxos relationships outlet:R45-23

# Show specific relationship type
arxos relationships outlet:R45-23 --type=electrical

# Show relationship graph
arxos graph outlet:R45-23 --depth=2
```

### Modifying Relationships

```bash
# Change connection
arxos reconnect outlet:R45-23 from circuit:C-101 to circuit:C-102

# Remove relationship
arxos disconnect outlet:R45-23 from circuit:C-101

# Update relationship properties
arxos update-relationship outlet:R45-23->circuit:C-101 load=1500W
```

## Constraint System

### Understanding Constraints

Constraints ensure building integrity and code compliance:

- **Structural Constraints**: Load limits, material compatibility
- **Electrical Constraints**: Voltage matching, load balancing
- **Spatial Constraints**: Clearances, accessibility
- **Code Constraints**: Building code compliance

### Viewing Constraints

```bash
# Show all constraints for object
arxos constraints outlet:R45-23

# Show violated constraints
arxos constraints outlet:R45-23 --violated

# Show constraint details
arxos constraint-info electrical.voltage-matching
```

### Constraint Validation

```bash
# Validate all constraints
arxos validate-constraints outlet:R45-23

# Validate specific constraint type
arxos validate-constraints outlet:R45-23 --type=electrical

# Check constraint before modification
arxos pre-validate outlet:R45-23.voltage=240
```

### Constraint Resolution

```bash
# Get constraint violation suggestions
arxos suggest-fix outlet:R45-23 --constraint=voltage-mismatch

# Auto-resolve violations where possible
arxos auto-resolve outlet:R45-23 --constraint=load-imbalance

# Override constraint (with permissions)
arxos override-constraint outlet:R45-23 voltage-limit --reason="temporary-config"
```

## Advanced Object Operations

### Batch Operations

```bash
# Modify multiple objects
arxos batch-set "outlets in floor:45" gfci=true

# Create multiple objects from CSV
arxos import outlets --file=outlets.csv --validate

# Update objects based on query
arxos update "outlets where voltage=120" amperage=20
```

### Object Templates

```bash
# Create template from existing object
arxos create-template --from=outlet:R45-23 --name=standard-gfci-outlet

# List available templates
arxos templates list --type=outlet

# Apply template to object
arxos apply-template outlet:R45-24 --template=standard-gfci-outlet
```

### Object Versioning

```bash
# View object version history
arxos versions outlet:R45-23

# Compare versions
arxos diff outlet:R45-23 --version1=v1.0 --version2=v2.1

# Revert to previous version
arxos revert outlet:R45-23 --to-version=v1.5
```

### Object Cloning

```bash
# Clone object to new location
arxos clone outlet:R45-23 --new-id=R45-25 --location=(150,200,300)

# Clone with modifications
arxos clone outlet:R45-23 --new-id=R45-26 --modify="amperage=30"

# Clone entire system
arxos clone-system electrical.panel:MP-1 --to-floor=46
```

## Spatial Operations

### Position and Orientation

```bash
# Move object
arxos move outlet:R45-23 to (120,200,300)

# Rotate object
arxos rotate beam:B-101 by 90degrees around z-axis

# Scale object (where applicable)
arxos scale room:R-205 by factor=1.1
```

### Spatial Relationships

```bash
# Check spatial conflicts
arxos check-conflicts outlet:R45-23

# Find optimal position
arxos optimize-position outlet:R45-23 --criteria=accessibility,code-compliance

# Align objects
arxos align outlets in wall:W-101 --axis=vertical --spacing=6ft
```

### Geometry Operations

```bash
# Get object bounds
arxos bounds outlet:R45-23

# Calculate clearances
arxos clearances outlet:R45-23

# Check accessibility compliance
arxos accessibility-check outlet:R45-23
```

## System Integration

### Physics Engine Integration

```bash
# Trigger physics calculation
arxos calculate-physics beam:B-101

# Update structural analysis
arxos structural-analysis floor:45

# Simulate load changes
arxos simulate-load beam:B-101 additional-load=1000lbs
```

### BIM Integration

```bash
# Export to BIM format
arxos export outlet:R45-23 --format=revit

# Import from BIM
arxos import --file=drawing.rvt --type=electrical

# Sync with BIM model
arxos sync-bim --model=main-architectural.rvt
```

### Code Compliance

```bash
# Check building code compliance
arxos code-check outlet:R45-23 --code=NEC-2020

# Generate compliance report
arxos compliance-report room:R-205 --codes=IBC-2021,ADA

# Auto-correct violations
arxos auto-correct outlet:R45-23 --violations=height-requirement
```

## Error Handling and Recovery

### Common Errors

```bash
# Constraint violation
arxos set outlet:R45-23.voltage=480
# Error: Constraint violation - voltage mismatch with connected circuit

# Permission denied
arxos modify beam:B-101.load-capacity=10000lbs  
# Error: Insufficient permissions - requires structural.admin

# Object not found
arxos get outlet:INVALID-123
# Error: Object not found: outlet:INVALID-123
```

### Recovery Operations

```bash
# Validate and repair object
arxos repair outlet:R45-23

# Rebuild relationships
arxos rebuild-relationships outlet:R45-23

# Reset object to template defaults
arxos reset outlet:R45-23 --to-template=standard-outlet
```

### Audit and Logging

```bash
# View object modification log
arxos audit outlet:R45-23

# Show who modified object
arxos who-modified outlet:R45-23 --since="last-week"

# Export audit trail
arxos export-audit --objects="outlets in floor:45" --format=csv
```

## Performance Considerations

### Optimization Tips

1. **Batch operations** instead of individual object modifications
2. **Use transactions** for related changes
3. **Validate constraints** before making changes
4. **Cache frequently-accessed objects** with `--cache` flag
5. **Use specific object IDs** rather than queries when possible

### Monitoring

```bash
# Check object cache status
arxos cache-status outlet:R45-23

# Monitor constraint checking performance
arxos perf-monitor --operation=constraint-validation

# Profile query performance
arxos profile "find outlets where voltage=120"
```