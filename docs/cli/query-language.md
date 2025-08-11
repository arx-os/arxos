# Query Language Reference

The Arxos Query Language (AQL) is designed specifically for architectural and building systems, with spatial relationships and object dependencies as first-class concepts.

## Query Syntax Overview

### Basic Query Structure

```sql
SELECT [fields] 
FROM [object-type] 
WHERE [conditions] 
[SPATIAL clauses]
[RELATIONSHIP clauses]
```

### Simple Queries

```bash
# Find all outlets
arxos find outlets

# Find outlets on specific floor
arxos find outlets in floor:45

# Find outlets with specific properties
arxos find outlets where voltage=120
```

## Object Selection

### Basic Object Types

```bash
# Structural elements
arxos find beams
arxos find columns  
arxos find walls
arxos find slabs

# MEP elements
arxos find outlets
arxos find fixtures
arxos find ducts
arxos find pipes

# Spaces
arxos find rooms
arxos find floors
arxos find zones
```

### Object Identification

```bash
# By ID
arxos get outlet:R45-23

# By pattern
arxos find outlets where id matches "R45-*"

# By type and subtype
arxos find electrical.outlets
arxos find structural.beams.steel
```

## Spatial Queries

### Location-Based Queries

```bash
# Objects at coordinates
arxos find * at coordinates:(100,200,300)

# Objects within radius
arxos find outlets within 10ft of beam:B-101

# Objects in geometric region
arxos find walls in bbox:(0,0,0)-(100,100,15)

# Objects on specific level
arxos find * on level:300mm  # 300mm above floor
```

### Spatial Relationships

```bash
# Adjacent objects
arxos find walls adjacent-to room:R-205

# Contained objects  
arxos find outlets contained-in wall:W-101

# Objects above/below
arxos find beams above slab:S-45
arxos find pipes below ceiling:C-45

# Intersection queries
arxos find * intersecting beam:B-101
```

### Distance and Proximity

```bash
# Nearest objects
arxos find nearest-5 outlets to coordinates:(100,200,300)

# Distance filtering
arxos find pipes where distance-to(outlet:R45-23) < 5ft

# Path queries
arxos find path from outlet:R45-23 to panel:MP-1
```

## Property Filtering

### Basic Property Queries

```bash
# Equality
arxos find outlets where voltage=120

# Comparison operators
arxos find beams where load-capacity > 5000lbs
arxos find rooms where area >= 200sqft

# String matching
arxos find walls where material contains "concrete"
arxos find outlets where id matches "R45-*"
```

### Multiple Conditions

```bash
# AND conditions
arxos find outlets where voltage=120 AND amperage=20

# OR conditions  
arxos find walls where material="concrete" OR material="steel"

# Complex expressions
arxos find beams where (material="steel" AND load-capacity>5000) OR (material="wood" AND grade="douglas-fir")
```

### Property Existence

```bash
# Has property
arxos find outlets where has-property:gfci

# Missing property
arxos find walls where missing-property:fire-rating

# Property comparison
arxos find beams where load-capacity > design-load
```

## Relationship Queries

### Direct Relationships

```bash
# Connected objects
arxos find outlets connected-to circuit:C-101

# Supported/supporting
arxos find beams supported-by column:COL-23
arxos find slabs supporting beam:B-101

# Served by
arxos find outlets served-by panel:MP-1
arxos find fixtures served-by pipe:P-205
```

### Relationship Traversal

```bash
# Chain relationships
arxos trace electrical-path from outlet:R45-23 to source

# Multi-hop relationships
arxos find outlets -> circuit -> panel where panel.location="basement"

# Dependency chains
arxos find dependencies-of beam:B-101
arxos find depends-on column:COL-23
```

### System Relationships

```bash
# Objects in same system
arxos find electrical same-system-as outlet:R45-23

# Cross-system relationships
arxos find structural supporting electrical
arxos find mechanical intersecting structural
```

## Advanced Queries

### Aggregation

```bash
# Count objects
arxos count outlets in floor:45

# Sum properties
arxos sum load-capacity from beams in floor:45

# Group by properties
arxos group outlets by circuit showing count,total-load
```

### Calculation Queries

```bash
# Calculate distances
arxos calculate distance from outlet:R45-23 to panel:MP-1

# Calculate loads
arxos calculate total-load on beam:B-101

# Calculate areas/volumes
arxos calculate area of room:R-205
arxos calculate volume of duct:D-101
```

### Conditional Queries

```bash
# If-then logic
arxos find outlets where if(gfci=true) then amperage>=20

# Case statements
arxos select outlets.id, case 
    when voltage=120 then "standard"
    when voltage=240 then "high-power" 
    else "unknown" 
  end as type
```

## Query Modifiers

### Output Formatting

```bash
# Specify output format
arxos find outlets --format=json
arxos find outlets --format=table
arxos find outlets --format=csv

# Select specific fields
arxos select id,voltage,amperage from outlets

# Sort results
arxos find outlets order-by voltage desc
```

### Query Optimization

```bash
# Use spatial indexing
arxos find outlets --spatial-index=octree

# Specify cache behavior
arxos find outlets --cache=force-refresh

# Limit results
arxos find outlets limit 100

# Explain query execution
arxos explain "find outlets in floor:45"
```

### Query Scope

```bash
# Query specific building sections
arxos find outlets --scope=floor:45

# Cross-building queries
arxos find similar-outlets --compare-buildings=sf-main,sf-north

# Historical queries
arxos find outlets --as-of="2024-01-15T10:00:00Z"
```

## Complex Query Examples

### Structural Analysis Queries

```bash
# Find overloaded beams
arxos find beams where current-load > design-load * 0.9

# Find columns supporting critical loads
arxos find columns supporting (beams where load-capacity > 10000lbs)

# Find walls with insufficient fire rating
arxos find walls adjacent-to (rooms where occupancy="assembly") and fire-rating < 2hr
```

### MEP System Queries

```bash
# Find electrical outlets without GFCI in wet locations
arxos find outlets where location-type="wet" and gfci=false

# Find oversized ducts
arxos find ducts where diameter > required-diameter * 1.2

# Find pipes with insufficient insulation
arxos find pipes where fluid-temp > 140F and insulation-r-value < 10
```

### Space and Occupancy Queries

```bash
# Find overcrowded rooms
arxos find rooms where occupant-count > capacity

# Find rooms with inadequate lighting
arxos find rooms where illumination < required-illumination

# Find accessible route violations  
arxos find paths where accessible=true and width < 44inches
```

## Query Functions

### Spatial Functions

```sql
distance(object1, object2)          -- Distance between objects
area(object)                        -- Area of 2D object
volume(object)                      -- Volume of 3D object  
intersects(object1, object2)        -- Whether objects intersect
contains(container, contained)       -- Whether one object contains another
```

### Property Functions

```sql
has-property(object, property)      -- Whether object has property
get-property(object, property)      -- Get property value
typeof(object)                      -- Object type
subtype(object)                     -- Object subtype
```

### System Functions

```sql
connected-to(object1, object2)      -- Whether objects are connected
path-between(object1, object2)      -- Path between objects
system-of(object)                   -- System containing object
load-on(structural-object)          -- Current load on object
```

## Query Variables and Parameterization

### Using Variables

```bash
# Set query variables
arxos set-var floor_num=45
arxos set-var voltage_standard=120

# Use variables in queries
arxos find outlets in floor:$floor_num where voltage=$voltage_standard
```

### Parameterized Queries

```bash
# Save parameterized query
arxos save-query "outlets-by-floor" "find outlets in floor:{floor_id} where voltage={voltage}"

# Execute saved query
arxos run-query "outlets-by-floor" --floor_id=45 --voltage=120
```

## Query Performance Tips

1. **Use spatial indexing** for location-based queries
2. **Limit scope** to specific floors or systems when possible
3. **Cache frequently-used results** with `--cache=enabled`
4. **Use specific object IDs** rather than broad searches when possible
5. **Combine filters early** rather than post-filtering large result sets

## Error Handling

The query engine provides detailed error messages:

```bash
# Syntax error example
arxos find outlets where voltage=  
# Error: Incomplete WHERE clause at position 23

# Permission error example  
arxos modify beam:B-101 load-capacity=5000lbs
# Error: Insufficient permissions. Requires: structural.contributor

# Object not found error
arxos get outlet:INVALID-123
# Error: Object not found: outlet:INVALID-123
```