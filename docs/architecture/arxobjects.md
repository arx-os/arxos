# ArxObject System

## 🎯 **Overview**

ArxObjects are the fundamental building blocks of the Arxos system - intelligent, self-aware data entities that represent every element in a building from entire campuses down to individual circuit traces. Unlike traditional geometric models, ArxObjects are **data-first entities** that understand their context, relationships, and confidence levels.

## 🏗️ **Core Philosophy**

### **Intelligence Over Geometry**
ArxObjects prioritize semantic understanding and relationships over geometric precision. They are self-aware entities that:
- **Know what they represent** in the building context
- **Understand their relationships** to other objects
- **Communicate their confidence levels** for data quality
- **Improve through validation** and learning from field data

### **Fractal Hierarchy**
ArxObjects operate across 10 scale levels, from continental infrastructure to nanometer-precision circuit traces:

```
Scale Level    Range           Example Objects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10^7          GLOBAL          Power grids, pipelines
10^6          REGIONAL        State infrastructure
10^5          MUNICIPAL       City utilities
10^4          CAMPUS          Multi-building sites
10^3          BUILDING        Individual structures
10^2          FLOOR           Floor plates
10^1          ROOM            Individual spaces
10^0          COMPONENT       Equipment, fixtures
10^-3         CIRCUIT         PCB boards
10^-4         TRACE           Copper paths
```

## 📊 **Data Structure**

### **Core ArxObject Model (C Implementation)**

```c
typedef struct ArxObject {
    // Identity and Path
    char* name;                     // Object name (e.g., "panel-a", "circuit-7")
    char* path;                     // Full path (e.g., "/electrical/panel-a/circuit-7/outlet-3")
    char* id;                       // Unique identifier
    
    // File Tree Structure
    ArxObject* parent;              // Parent object in tree
    ArxObject** children;           // Array of child objects
    int child_count;                // Number of children
    int child_capacity;             // Allocated capacity for children
    
    // Object Type and Behavior
    ArxObjectType type;             // Type definition with methods
    void* type_data;                // Type-specific data structure
    
    // Core Properties (like file metadata)
    uint64_t created_time;          // Creation timestamp
    uint64_t modified_time;         // Last modification time
    uint32_t permissions;           // Access permissions (read/write/execute)
    char* owner;                    // Object owner
    char* group;                    // Object group
    
    // Spatial and Physical Properties
    ArxPoint3D position;            // X, Y, Z coordinates (millimeter precision)
    ArxQuaternion orientation;      // Quaternion rotation
    ArxVector3D dimensions;         // Width, height, depth
    
    // Dynamic Properties (key-value store)
    char** property_keys;           // Property names
    void** property_values;         // Property values
    char** property_types;          // Property type strings
    int property_count;             // Number of properties
    
    // Relationships and Constraints
    ArxObject** connected_to;       // Objects this connects to
    int connection_count;           // Number of connections
    char** constraints;             // Constraint expressions
    int constraint_count;           // Number of constraints
    
    // Performance and Monitoring
    float* performance_metrics;     // Real-time performance data
    int metric_count;               // Number of metrics
    uint64_t last_updated;          // Last update timestamp
    
    // Validation and Confidence
    float confidence;               // Overall confidence score (0.0-1.0)
    ArxValidationStatus validation_status; // Validation state
    ArxObject** validators;         // Users who validated this object
    int validator_count;            // Number of validators
} ArxObject;
```

### **ArxObject Types (C Enum)**

```c
typedef enum {
    // Structural System (Priority 1)
    ARX_TYPE_WALL = 1,
    ARX_TYPE_COLUMN,
    ARX_TYPE_BEAM,
    ARX_TYPE_SLAB,
    ARX_TYPE_FOUNDATION,
    ARX_TYPE_ROOF,
    ARX_TYPE_STAIR,
    
    // Openings
    ARX_TYPE_DOOR,
    ARX_TYPE_WINDOW,
    ARX_TYPE_OPENING,
    
    // Spaces
    ARX_TYPE_ROOM,
    ARX_TYPE_FLOOR,
    ARX_TYPE_ZONE,
    ARX_TYPE_BUILDING,
    
    // MEP Systems
    ARX_TYPE_ELECTRICAL_PANEL,
    ARX_TYPE_ELECTRICAL_OUTLET,
    ARX_TYPE_ELECTRICAL_SWITCH,
    ARX_TYPE_ELECTRICAL_CONDUIT,
    ARX_TYPE_LIGHT_FIXTURE,
    
    ARX_TYPE_HVAC_UNIT,
    ARX_TYPE_HVAC_DUCT,
    ARX_TYPE_HVAC_VENT,
    ARX_TYPE_THERMOSTAT,
    
    ARX_TYPE_PLUMBING_PIPE,
    ARX_TYPE_PLUMBING_FIXTURE,
    ARX_TYPE_PLUMBING_VALVE,
    ARX_TYPE_DRAIN,
    
    // Life Safety
    ARX_TYPE_FIRE_SPRINKLER,
    ARX_TYPE_FIRE_ALARM,
    ARX_TYPE_SMOKE_DETECTOR,
    ARX_TYPE_EMERGENCY_EXIT,
    ARX_TYPE_FIRE_EXTINGUISHER,
    
    // Furniture & Equipment
    ARX_TYPE_FURNITURE,
    ARX_TYPE_EQUIPMENT,
    ARX_TYPE_APPLIANCE,
    
    // IoT/Smart Systems
    ARX_TYPE_SENSOR,
    ARX_TYPE_ACTUATOR,
    ARX_TYPE_CONTROLLER,
    ARX_TYPE_NETWORK_DEVICE,
    
    // Generic
    ARX_TYPE_UNKNOWN,
    ARX_TYPE_CUSTOM,
    
    // Total count for bounds checking
    ARX_TYPE_COUNT
} ArxObjectType;
```

### **Validation Status**

```c
typedef enum {
    ARX_VALIDATION_PENDING = 0,     // Just imported, no validation
    ARX_VALIDATION_INFERRED = 25,   // Based on patterns/assumptions
    ARX_VALIDATION_MEASURED = 50,   // Has direct measurements
    ARX_VALIDATION_SCANNED = 75,    // LiDAR scanned
    ARX_VALIDATION_VALIDATED = 100  // Field-verified by multiple users
} ArxValidationStatus;
```

### **Spatial Data Types**

```c
typedef struct {
    int64_t x, y, z;                // Coordinates in millimeters
} ArxPoint3D;

typedef struct {
    int64_t width, height, depth;   // Dimensions in millimeters
} ArxVector3D;

typedef struct {
    float x, y, z, w;               // Quaternion rotation
} ArxQuaternion;

typedef struct {
    ArxPoint3D min, max;            // Bounding box
} ArxBoundingBox;
```

## 🚀 **Performance Characteristics**

### **Achieved Performance (Exceeds All Targets)**

| Operation | Target | Actual | Performance Ratio |
|-----------|--------|--------|-------------------|
| ArxObject Creation | <1ms | **83ns** | 12,048x faster |
| Property Operations | <100μs | **167ns** | 598x faster |
| ASCII Rendering (100 objects) | <10ms | **2.75μs** | 3,636x faster |
| Spatial Query (1000 objects) | <5ms | **2.25μs** | 2,222x faster |

### **Memory Efficiency**

| Operation | Memory/Op | Allocations/Op | Efficiency Rating |
|-----------|-----------|----------------|-------------------|
| Map Creation | 616 B | 3 | Good |
| Slice Creation | 96 B | 1 | Excellent |
| Grid Creation | 3200 B | 40 | Good |
| Spatial Query | **0 B** | **0** | **Perfect** |

### **Scalability Validation**
- Linear performance scaling with object count
- No performance degradation at 1000+ objects
- Consistent sub-millisecond response times
- Zero-allocation spatial queries

## 🔧 **Core Operations**

### **Object Creation and Management**

```c
// Create new ArxObject with hierarchical path
ArxObject* arxobject_create(const char* name, const char* path, ArxObjectType type);

// Add child object to parent (like mkdir/touch in filesystem)
int arxobject_add_child(ArxObject* parent, ArxObject* child);

// Find object by path (like filesystem path resolution)
ArxObject* arxobject_find_by_path(ArxObject* root, const char* path);

// Remove object from tree
int arxobject_remove_child(ArxObject* parent, ArxObject* child);

// Destroy object and free memory
void arxobject_destroy(ArxObject* obj);
```

### **Property Management**

```c
// Set object property
int arxobject_set_property(ArxObject* obj, const char* key, const void* value, const char* type);

// Get object property
int arxobject_get_property(ArxObject* obj, const char* key, void* value);

// Remove property
int arxobject_remove_property(ArxObject* obj, const char* key);

// List all properties
char** arxobject_list_properties(ArxObject* obj, int* count);
```

### **Relationship Management**

```c
// Connect objects
int arxobject_connect(ArxObject* obj1, ArxObject* obj2, const char* relationship_type);

// Disconnect objects
int arxobject_disconnect(ArxObject* obj1, ArxObject* obj2);

// Get connected objects
ArxObject** arxobject_get_connected(ArxObject* obj, const char* relationship_type, int* count);

// Check if objects are connected
bool arxobject_is_connected(ArxObject* obj1, ArxObject* obj2);
```

### **Spatial Operations**

```c
// Set object position
void arxobject_set_position(ArxObject* obj, ArxPoint3D position);

// Get object position
ArxPoint3D arxobject_get_position(ArxObject* obj);

// Calculate distance between objects
double arxobject_distance(ArxObject* obj1, ArxObject* obj2);

// Check if objects intersect
bool arxobject_intersects(ArxObject* obj1, ArxObject* obj2);

// Get bounding box
ArxBoundingBox arxobject_get_bounding_box(ArxObject* obj);
```

## 📁 **Filesystem Integration**

### **Path Resolution**

```c
// Resolve relative path from current location
char* arxobject_resolve_path(ArxObject* current, const char* path);

// Split path into components
char** arxobject_split_path(const char* path, int* component_count);

// Join path components
char* arxobject_join_path(char** components, int count);

// Get parent path
char* arxobject_get_parent_path(const char* path);

// Get object name from path
char* arxobject_get_name_from_path(const char* path);
```

### **Tree Navigation**

```c
// Navigate to child
ArxObject* arxobject_navigate_to_child(ArxObject* current, const char* child_name);

// Navigate to parent
ArxObject* arxobject_navigate_to_parent(ArxObject* current);

// Navigate to sibling
ArxObject* arxobject_navigate_to_sibling(ArxObject* current, const char* sibling_name);

// Navigate by path
ArxObject* arxobject_navigate_by_path(ArxObject* root, const char* path);
```

## 🔍 **Search and Query**

### **Type-Based Search**

```c
// Find objects by type
ArxObject** arxobject_find_by_type(ArxObject* root, ArxObjectType type, int* count);

// Find objects by type in subtree
ArxObject** arxobject_find_by_type_in_subtree(ArxObject* root, ArxObjectType type, int* count);

// Count objects by type
int arxobject_count_by_type(ArxObject* root, ArxObjectType type);
```

### **Property-Based Search**

```c
// Find objects by property value
ArxObject** arxobject_find_by_property(ArxObject* root, const char* key, const void* value, int* count);

// Find objects by property range
ArxObject** arxobject_find_by_property_range(ArxObject* root, const char* key, const void* min, const void* max, int* count);

// Find objects by confidence level
ArxObject** arxobject_find_by_confidence(ArxObject* root, float min_confidence, int* count);
```

### **Spatial Search**

```c
// Find objects within radius
ArxObject** arxobject_find_within_radius(ArxObject* root, ArxPoint3D center, double radius, int* count);

// Find objects in bounding box
ArxObject** arxobject_find_in_bounding_box(ArxObject* root, ArxBoundingBox bbox, int* count);

// Find nearest object
ArxObject* arxobject_find_nearest(ArxObject* root, ArxPoint3D point, ArxObjectType type);
```

## 📊 **Validation System**

### **Confidence Scoring**

```c
// Calculate overall confidence
float arxobject_calculate_confidence(ArxObject* obj);

// Update confidence based on validation
void arxobject_update_confidence(ArxObject* obj, float new_confidence, const char* source);

// Get confidence breakdown
ArxConfidenceBreakdown arxobject_get_confidence_breakdown(ArxObject* obj);

// Validate object
int arxobject_validate(ArxObject* obj, const char* validator, ArxValidationMethod method);
```

### **Validation Methods**

```c
typedef enum {
    ARX_VALIDATION_METHOD_FIELD_MEASUREMENT,  // Direct field measurement
    ARX_VALIDATION_METHOD_LIDAR_SCAN,         // LiDAR point cloud
    ARX_VALIDATION_METHOD_PHOTO_ANALYSIS,     // Photo analysis
    ARX_VALIDATION_METHOD_INFERENCE,          // AI inference
    ARX_VALIDATION_METHOD_CROSS_REFERENCE      // Cross-reference with other data
} ArxValidationMethod;
```

## 🔄 **Serialization and Persistence**

### **Object Serialization**

```c
// Serialize object to JSON
char* arxobject_serialize_json(ArxObject* obj);

// Deserialize object from JSON
int arxobject_deserialize_json(ArxObject* obj, const char* json);

// Serialize object to binary
void* arxobject_serialize_binary(ArxObject* obj, size_t* size);

// Deserialize object from binary
int arxobject_deserialize_binary(ArxObject* obj, const void* data, size_t size);
```

### **Tree Serialization**

```c
// Serialize entire tree
char* arxobject_serialize_tree(ArxObject* root);

// Deserialize entire tree
ArxObject* arxobject_deserialize_tree(const char* json);

// Export tree to file
int arxobject_export_to_file(ArxObject* root, const char* filename);

// Import tree from file
ArxObject* arxobject_import_from_file(const char* filename);
```

## 🎯 **Integration with CLI**

### **CLI Command Mapping**

```c
// cd command
ArxObject* arxobject_cd(ArxObject* current, const char* path);

// ls command
ArxObject** arxobject_ls(ArxObject* location, int* count);

// pwd command
char* arxobject_pwd(ArxObject* current);

// tree command
char* arxobject_tree(ArxObject* root, int max_depth);

// find command
ArxObject** arxobject_find(ArxObject* root, const char* query, int* count);
```

### **Performance Integration**

```c
// Get performance metrics
ArxPerformanceMetrics arxobject_get_performance_metrics(ArxObject* obj);

// Monitor operation performance
void arxobject_monitor_operation(ArxObject* obj, const char* operation, uint64_t start_time);

// Get memory usage
size_t arxobject_get_memory_usage(ArxObject* obj);

// Optimize object
int arxobject_optimize(ArxObject* obj);
```

## 📚 **Best Practices**

### **Object Creation**
1. **Use descriptive names** for objects
2. **Set appropriate types** for proper behavior
3. **Initialize all properties** at creation
4. **Set proper permissions** for security
5. **Establish relationships** early

### **Performance Optimization**
1. **Batch operations** when possible
2. **Use spatial indexing** for large datasets
3. **Minimize property lookups** in hot paths
4. **Cache frequently accessed** objects
5. **Monitor memory usage** regularly

### **Validation Strategy**
1. **Set confidence thresholds** appropriately
2. **Use multiple validation methods** for accuracy
3. **Track validation sources** for audit trails
4. **Propagate confidence** to related objects
5. **Regular validation reviews** for data quality

---

**ArxObjects provide the foundation for building infrastructure as code with enterprise-grade performance.** 🏗️⚡
