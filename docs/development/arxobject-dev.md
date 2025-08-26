# ArxObject Development Guide

This guide covers developing with the ArxObject system, the core building intelligence data model that represents every building element as an intelligent, self-aware entity.

## Overview

ArxObjects are the fundamental building blocks of Arxos, representing everything from entire campuses down to individual microchips. They form a hierarchical, filesystem-like structure that enables infinite fractal zoom and intelligent building operations.

## Core Concepts

### 1. ArxObject Structure

Every ArxObject contains:

```c
typedef struct {
    // Core Identity
    char* id;                    // Unique identifier
    ArxObjectType type;          // Building element type
    char* name;                  // Human-readable name
    char* description;           // Detailed description
    
    // Spatial Information
    ArxPoint3D position;         // 3D position (mm precision)
    ArxBoundingBox bounds;       // Spatial bounds
    double rotation[3];          // Rotation around X, Y, Z axes
    
    // Hierarchical Structure
    ArxObject* parent;           // Parent object
    ArxObject** children;        // Array of child objects
    int child_count;             // Number of children
    int child_capacity;          // Array capacity
    
    // Properties and Metadata
    ArxProperty** properties;    // Dynamic property system
    int property_count;          // Number of properties
    ValidationStatus status;     // Validation state
    double confidence;           // Data confidence (0.0-1.0)
    
    // System Integration
    char* system;                // Building system (electrical, HVAC, etc.)
    char* manufacturer;          // Equipment manufacturer
    char* model;                 // Equipment model
    char* serial_number;         // Unique serial number
    
    // Timestamps
    time_t created_at;           // Creation timestamp
    time_t updated_at;           // Last update timestamp
    time_t validated_at;         // Last validation timestamp
} ArxObject;
```

### 2. ArxObject Types

The system defines comprehensive building element types:

```c
typedef enum {
    // Structural System (Priority 1)
    ARX_TYPE_WALL = 1,
    ARX_TYPE_COLUMN,
    ARX_TYPE_BEAM,
    ARX_TYPE_SLAB,
    ARX_TYPE_FOUNDATION,
    
    // Enclosure System
    ARX_TYPE_WINDOW,
    ARX_TYPE_DOOR,
    ARX_TYPE_ROOF,
    ARX_TYPE_CURTAIN_WALL,
    
    // Mechanical Systems
    ARX_TYPE_AIR_HANDLER,
    ARX_TYPE_VAV_BOX,
    ARX_TYPE_CHILLER,
    ARX_TYPE_BOILER,
    ARX_TYPE_PUMP,
    ARX_TYPE_FAN,
    
    // Electrical Systems
    ARX_TYPE_PANEL,
    ARX_TYPE_CIRCUIT,
    ARX_TYPE_OUTLET,
    ARX_TYPE_LIGHTING,
    ARX_TYPE_TRANSFORMER,
    
    // Plumbing Systems
    ARX_TYPE_PIPE,
    ARX_TYPE_VALVE,
    ARX_TYPE_FIXTURE,
    ARX_TYPE_PUMP_STATION,
    
    // Technology Systems
    ARX_TYPE_ACCESS_POINT,
    ARX_TYPE_CAMERA,
    ARX_TYPE_SENSOR,
    ARX_TYPE_CONTROLLER,
    
    // Special Types
    ARX_TYPE_BUILDING,
    ARX_TYPE_FLOOR,
    ARX_TYPE_ROOM,
    ARX_TYPE_ZONE,
    ARX_TYPE_EQUIPMENT,
    ARX_TYPE_FURNITURE,
    
    ARX_TYPE_COUNT
} ArxObjectType;
```

## Development Patterns

### 1. Creating ArxObjects

```c
// Create a new wall object
ArxObject* wall = arxobject_create(
    "wall_001",
    ARX_TYPE_WALL,
    "North Wall - Conference Room",
    "Exterior wall with window"
);

// Set spatial properties
arxobject_set_position(wall, (ArxPoint3D){10000, 0, 0}); // 10m from origin
arxobject_set_bounds(wall, (ArxBoundingBox){
    .min = {10000, 0, 0},
    .max = {10000, 5000, 3000} // 5m wide, 3m high
});

// Add properties
arxobject_set_property(wall, "material", "concrete");
arxobject_set_property(wall, "thickness", "200mm");
arxobject_set_property(wall, "insulation", "R-20");
```

### 2. Building Hierarchies

```c
// Create building structure
ArxObject* building = arxobject_create("bldg_001", ARX_TYPE_BUILDING, "HQ Building", "Main office building");
ArxObject* floor = arxobject_create("floor_1", ARX_TYPE_FLOOR, "First Floor", "Ground level");
ArxObject* room = arxobject_create("room_101", ARX_TYPE_ROOM, "Conference Room", "Main meeting room");

// Build hierarchy
arxobject_add_child(building, floor);
arxobject_add_child(floor, room);
arxobject_add_child(room, wall);

// Set system relationships
arxobject_set_property(room, "floor_number", "1");
arxobject_set_property(room, "room_number", "101");
arxobject_set_property(room, "area", "25.0");
```

### 3. Property System

```c
// Dynamic property management
arxobject_set_property(wall, "fire_rating", "2_hour");
arxobject_set_property(wall, "acoustic_rating", "STC_50");
arxobject_set_property(wall, "maintenance_cycle", "annual");

// Property types are automatically inferred
arxobject_set_property(wall, "temperature", 22.5);        // numeric
arxobject_set_property(wall, "is_active", true);          // boolean
arxobject_set_property(wall, "last_inspection", "2024-01-15"); // date

// Complex properties
arxobject_set_property(wall, "sensors", "temp_001,humidity_001");
arxobject_set_property(wall, "maintenance_history", "2023-01-15:inspected,2023-07-15:cleaned");
```

### 4. Spatial Operations

```c
// Spatial queries
ArxObject** nearby_objects = arxobject_find_nearby(
    wall, 
    (ArxPoint3D){10000, 2500, 1500}, // center point
    1000 // 1m radius
);

// Collision detection
bool collision = arxobject_check_collision(wall, nearby_objects[0]);

// Spatial relationships
ArxObject* above = arxobject_find_above(wall);
ArxObject* below = arxobject_find_below(wall);
ArxObject* adjacent = arxobject_find_adjacent(wall);
```

## Go Integration

### 1. CGO Bridge

The Go side interfaces with C through the CGO bridge:

```go
// Go-side ArxObject representation
type ArxObject struct {
    ID          string                 `json:"id"`
    Type        ArxObjectType          `json:"type"`
    Name        string                 `json:"name"`
    Description string                 `json:"description"`
    Position    Point3D                `json:"position"`
    Bounds      BoundingBox            `json:"bounds"`
    Properties  map[string]interface{} `json:"properties"`
    Children    []*ArxObject           `json:"children"`
    Parent      *ArxObject             `json:"parent"`
    Status      ValidationStatus       `json:"status"`
    Confidence  float64                `json:"confidence"`
}

// CGO function calls
//export ArxObjectCreate
func ArxObjectCreate(id, objectType, name, description *C.char) *C.ArxObject {
    // Implementation bridges Go and C
}
```

### 2. Performance Optimization

```go
// Batch operations for performance
func CreateMultipleWalls(positions []Point3D) []*ArxObject {
    walls := make([]*ArxObject, len(positions))
    
    // Use CGO batch operations
    C.arxobject_batch_create_begin()
    
    for i, pos := range positions {
        wall := &ArxObject{
            ID:       fmt.Sprintf("wall_%03d", i+1),
            Type:     ArxObjectTypeWall,
            Position: pos,
        }
        walls[i] = wall
    }
    
    C.arxobject_batch_create_end()
    return walls
}
```

## Best Practices

### 1. Memory Management

```c
// Always free ArxObjects when done
ArxObject* obj = arxobject_create("test", ARX_TYPE_WALL, "Test", "Test object");
// ... use object ...
arxobject_destroy(obj);

// For hierarchies, destroy from leaves up
arxobject_destroy_hierarchy(building); // Destroys entire tree
```

### 2. Error Handling

```c
// Check return values
ArxObject* obj = arxobject_create("test", ARX_TYPE_WALL, "Test", "Test");
if (obj == NULL) {
    fprintf(stderr, "Failed to create ArxObject\n");
    return -1;
}

// Validate operations
if (!arxobject_add_child(parent, child)) {
    fprintf(stderr, "Failed to add child\n");
    return -1;
}
```

### 3. Property Naming Conventions

```c
// Use consistent property names
arxobject_set_property(obj, "system_type", "electrical");
arxobject_set_property(obj, "manufacturer_code", "ABB");
arxobject_set_property(obj, "model_number", "XLP-2000");

// Avoid ambiguous names
// Bad: "type" (conflicts with ArxObjectType)
// Good: "equipment_type", "material_type"
```

### 4. Spatial Precision

```c
// Always use millimeter precision for internal coordinates
ArxPoint3D pos = {10000, 5000, 3000}; // 10m, 5m, 3m

// Convert to display units only for UI
double meters_x = pos.x / 1000.0;
double feet_x = pos.x / 304.8;
```

## Testing ArxObjects

### 1. Unit Tests

```c
// Test ArxObject creation
void test_arxobject_creation() {
    ArxObject* obj = arxobject_create("test", ARX_TYPE_WALL, "Test", "Test");
    assert(obj != NULL);
    assert(strcmp(obj->id, "test") == 0);
    assert(obj->type == ARX_TYPE_WALL);
    arxobject_destroy(obj);
}

// Test hierarchy operations
void test_hierarchy_operations() {
    ArxObject* parent = arxobject_create("parent", ARX_TYPE_ROOM, "Parent", "Parent room");
    ArxObject* child = arxobject_create("child", ARX_TYPE_WALL, "Child", "Child wall");
    
    assert(arxobject_add_child(parent, child));
    assert(parent->child_count == 1);
    assert(child->parent == parent);
    
    arxobject_destroy_hierarchy(parent);
}
```

### 2. Performance Tests

```c
// Benchmark ArxObject operations
void benchmark_arxobject_creation() {
    clock_t start = clock();
    
    for (int i = 0; i < 10000; i++) {
        char id[32];
        sprintf(id, "obj_%d", i);
        ArxObject* obj = arxobject_create(id, ARX_TYPE_WALL, "Test", "Test");
        arxobject_destroy(obj);
    }
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Created 10000 objects in %.3f seconds\n", time_spent);
}
```

## Integration Examples

### 1. PDF Floor Plan Processing

```c
// Process extracted building elements
ArxObject* process_floor_plan_elements(ExtractedElement* elements, int count) {
    ArxObject* floor = arxobject_create("floor_001", ARX_TYPE_FLOOR, "Floor", "Processed floor");
    
    for (int i = 0; i < count; i++) {
        ExtractedElement* elem = &elements[i];
        
        ArxObject* obj = arxobject_create(
            elem->id,
            map_element_type(elem->type),
            elem->name,
            elem->description
        );
        
        // Set spatial properties from PDF coordinates
        ArxPoint3D pos = convert_pdf_to_world_coords(elem->x, elem->y, elem->z);
        arxobject_set_position(obj, pos);
        
        arxobject_add_child(floor, obj);
    }
    
    return floor;
}
```

### 2. Real-time AR Updates

```c
// Update ArxObject from AR field data
void update_from_ar_data(ArxObject* obj, ARFieldData* field_data) {
    // Update position if AR data is more accurate
    if (field_data->confidence > obj->confidence) {
        arxobject_set_position(obj, field_data->position);
        obj->confidence = field_data->confidence;
        obj->updated_at = time(NULL);
    }
    
    // Add field validation properties
    arxobject_set_property(obj, "field_validated", "true");
    arxobject_set_property(obj, "field_validation_date", field_data->timestamp);
    arxobject_set_property(obj, "field_user", field_data->user_id);
}
```

## Next Steps

1. **CLI Integration**: Learn how ArxObjects integrate with the command-line interface
2. **ASCII Rendering**: Understand how ArxObjects are visualized in the terminal
3. **Version Control**: Explore building state management and change tracking
4. **API Development**: Build external interfaces for ArxObject operations

## Resources

- [ArxObject Architecture](../architecture/arxobjects.md)
- [ASCII-BIM System](../architecture/ascii-bim.md)
- [CLI Architecture](../architecture/cli-architecture.md)
- [Performance Report](../../core/PERFORMANCE_REPORT.md)
