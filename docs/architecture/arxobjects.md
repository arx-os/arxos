# 🔧 ArxObject Hierarchical System

## 🎯 **ArxObject System Overview**

The **ArxObject Hierarchical System** is the revolutionary core of Arxos that transforms buildings into navigable filesystems. Every building component becomes an intelligent, self-aware ArxObject that understands its context, relationships, confidence levels, and real-time status.

**Core Innovation**: Buildings become navigable filesystems where every component has a path and can contain infinite depth of sub-components, all accessible through Git-like CLI operations.

## 🏗️ **Building as Filesystem Architecture**

### **Hierarchical File Tree System**

Buildings are structured as navigable filesystems where every component has a path and can contain infinite depth of sub-components.

```c
/*
 * ArxObject Hierarchical File Tree System
 * Buildings structured as navigable file systems with typed components
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

// Forward declarations
typedef struct ArxObject ArxObject;
typedef struct ArxObjectType ArxObjectType;

// ArxObject acts like a filesystem node with typed properties
struct ArxObject {
    // File tree structure
    char* name;                     // Object name (e.g., "panel-a", "circuit-7")  
    char* path;                     // Full path (e.g., "/electrical/panel-a/circuit-7/outlet-3")
    ArxObject* parent;              // Parent object in tree
    ArxObject** children;           // Array of child objects
    int child_count;               // Number of children
    int child_capacity;            // Allocated capacity for children
    
    // Object type and behavior
    ArxObjectType* type;           // Type definition with methods
    void* type_data;               // Type-specific data structure
    
    // Core properties (like file metadata)
    char* id;                      // Unique identifier
    uint64_t created_time;         // Creation timestamp
    uint64_t modified_time;        // Last modification time
    uint32_t permissions;          // Access permissions (read/write/execute)
    char* owner;                   // Object owner
    char* group;                   // Object group
    
    // Spatial and physical properties
    float position[3];             // X, Y, Z coordinates
    float orientation[4];          // Quaternion rotation
    float dimensions[3];           // Width, height, depth
    
    // Dynamic properties (key-value store)
    char** property_keys;          // Property names
    void** property_values;        // Property values
    char** property_types;         // Property type strings
    int property_count;            // Number of properties
    
    // Relationships and constraints
    ArxObject** connected_to;      // Objects this connects to
    int connection_count;          // Number of connections
    char** constraints;            // Constraint expressions
    int constraint_count;          // Number of constraints
    
    // Performance and monitoring
    float* performance_metrics;    // Real-time performance data
    int metric_count;             // Number of metrics
    uint64_t last_updated;        // Last update timestamp
};

// Type system for different ArxObject categories
struct ArxObjectType {
    char* type_name;               // Type name (e.g., "electrical_panel", "hvac_unit")
    char* category;                // Category (e.g., "electrical", "hvac", "structural")
    
    // Type-specific methods (like file type handlers)
    int (*init)(ArxObject* obj, void* init_data);
    int (*destroy)(ArxObject* obj);
    int (*get_property)(ArxObject* obj, const char* key, void* value);
    int (*set_property)(ArxObject* obj, const char* key, void* value);
    int (*validate_constraints)(ArxObject* obj);
    int (*simulate)(ArxObject* obj, float delta_time);
    int (*serialize)(ArxObject* obj, char** output);
    int (*deserialize)(ArxObject* obj, const char* input);
    
    // Type-specific property definitions
    char** required_properties;    // Properties this type must have
    char** optional_properties;    // Properties this type may have
    int required_count;
    int optional_count;
};
```

## 🌳 **Complete Building Hierarchy Examples**

### **Full Building File Tree Structure**

```
/campus/east-region/building-47/
├── /structural/
│   ├── /foundation/
│   │   ├── /footings/footing-[1-24]/
│   │   └── /slab/
│   ├── /frame/
│   │   ├── /columns/column-[a1-d8]/
│   │   └── /beams/beam-[1-156]/
│   └── /walls/
│       ├── /exterior/north-wall/
│       │   ├── /windows/window-[1-8]/
│       │   └── /insulation/
│       └── /interior/partition-[1-47]/
├── /electrical/
│   ├── /service-entrance/
│   │   ├── /meter/
│   │   └── /main-disconnect/
│   ├── /distribution/
│   │   ├── /main-panel/
│   │   │   ├── /breakers/breaker-[1-42]/
│   │   │   └── /circuits/circuit-[1-42]/
│   │   │       ├── /circuit-1/
│   │   │       │   ├── /outlets/outlet-[1-8]/
│   │   │       │   └── /junction-boxes/j-box-[1-3]/
│   │   │       └── ...
│   │   └── /sub-panels/panel-[a-c]/
│   └── /emergency-power/
│       ├── /generator/
│       └── /transfer-switch/
├── /hvac/
│   ├── /air-handlers/ahu-[1-3]/
│   │   ├── /ahu-1/
│   │   │   ├── /supply-fan/
│   │   │   │   ├── /motor/
│   │   │   │   │   ├── /windings/
│   │   │   │   │   └── /bearings/
│   │   │   │   └── /vfd-controller/
│   │   │   │       ├── /power-electronics/
│   │   │   │       └── /control-board/
│   │   │   │           ├── /cpu/
│   │   │   │           └── /memory/
│   │   │   ├── /cooling-coil/
│   │   │   └── /filter-bank/
│   │   └── ...
│   └── /controls/
│       ├── /building-automation-system/
│       └── /sensors/temp-sensor-[1-47]/
├── /network/
│   ├── /core-infrastructure/
│   │   ├── /mdf/
│   │   │   ├── /core-switch/
│   │   │   │   ├── /line-cards/card-[1-4]/
│   │   │   │   └── /supervisor-engine/
│   │   │   │       └── /asics/asic-[1-8]/
│   │   │   └── /patch-panels/
│   │   └── /idfs/idf-[1-8]/
│   └── /endpoints/
│       ├── /access-points/ap-[1-32]/
│       └── /network-jacks/jack-[1-247]/
└── /plumbing/
    ├── /water-supply/
    │   ├── /water-service/
    │   │   ├── /water-meter/
    │   │   └── /main-shutoff/
    │   └── /distribution/
    │       ├── /hot-water-system/
    │       └── /cold-water-distribution/
    └── /drainage-system/
        ├── /waste-lines/
        └── /vent-system/
```

## 🖥️ **CLI Navigation Commands**

### **Filesystem-Style Building Navigation**

```bash
# Navigate building like filesystem
arx @building-47 ls /electrical/                           # List electrical systems
arx @building-47 ls /electrical/main-panel/               # List circuits in main panel  
arx @building-47 find /electrical -type outlet            # Find all outlets
arx @building-47 tree /hvac/air-handling-units/           # Show HVAC tree structure

# Object inspection
arx @building-47 inspect /electrical/main-panel/circuit-1/outlet-3
arx @building-47 cat /hvac/ahu-1/supply-fan/properties    # Show all properties
arx @building-47 stat /structural/columns/column-a1       # Show object metadata

# Property operations  
arx @building-47 get /electrical/main-panel/circuit-1 --property load_current
arx @building-47 set /hvac/ahu-1 --property supply_air_temp=72
arx @building-47 query "SELECT path FROM /electrical WHERE type='outlet' AND load > 15A"

# Tree operations
arx @building-47 mkdir /electrical/emergency-power        # Add new system branch
arx @building-47 mv /electrical/subpanel-a /electrical/emergency-power/
arx @building-47 cp /hvac/controls/zone-controllers/template /hvac/controls/zone-controllers/floor-3

# Infinite zoom navigation
arx @building-47 zoom campus                      # See whole campus
arx @building-47 zoom building                    # Building overview
arx @building-47 zoom floor --level 2             # Floor plan
arx @building-47 zoom room --id mechanical-room   # Room detail
arx @building-47 zoom equipment --id plc-cabinet  # Equipment internals
arx @building-47 zoom chip --component cpu-module # Silicon level
```

## 🔧 **Type System Implementation**

### **Dynamic Type Registration**

```c
// Type registration system
typedef struct {
    ArxObjectType** types;
    int type_count;
    int type_capacity;
} TypeRegistry;

// Register a new ArxObject type
int register_arxobject_type(TypeRegistry* registry, ArxObjectType* type) {
    // Validate type definition
    if (!validate_type_definition(type)) {
        return -1;
    }
    
    // Check if type already exists
    for (int i = 0; i < registry->type_count; i++) {
        if (strcmp(registry->types[i]->type_name, type->type_name) == 0) {
            return -2; // Type already exists
        }
    }
    
    // Add type to registry
    if (registry->type_count >= registry->type_capacity) {
        // Expand capacity
        registry->type_capacity *= 2;
        registry->types = realloc(registry->types, 
                                 registry->type_capacity * sizeof(ArxObjectType*));
    }
    
    registry->types[registry->type_count++] = type;
    return 0;
}
```

### **Type-Specific Method Implementation**

```c
// Electrical panel type implementation
static int electrical_panel_init(ArxObject* obj, void* init_data) {
    ElectricalPanelData* data = (ElectricalPanelData*)init_data;
    
    // Set required properties
    set_object_property(obj, "voltage", &data->voltage, "float");
    set_object_property(obj, "amperage", &data->amperage, "float");
    set_object_property(obj, "phase_count", &data->phase_count, "int");
    set_object_property(obj, "breaker_count", &data->breaker_count, "int");
    
    // Initialize child objects (circuits)
    for (int i = 0; i < data->circuit_count; i++) {
        ArxObject* circuit = create_arxobject("circuit", obj);
        circuit->name = malloc(32);
        sprintf(circuit->name, "circuit-%d", i + 1);
        
        // Set circuit properties
        set_object_property(circuit, "load_current", &data->circuits[i].load_current, "float");
        set_object_property(circuit, "voltage", &data->circuits[i].voltage, "float");
        
        add_child_object(obj, circuit);
    }
    
    return 0;
}

static int electrical_panel_simulate(ArxObject* obj, float delta_time) {
    // Simulate electrical panel behavior
    float total_load = 0.0f;
    
    // Calculate total load from all circuits
    for (int i = 0; i < obj->child_count; i++) {
        ArxObject* circuit = obj->children[i];
        float load_current;
        if (get_object_property(circuit, "load_current", &load_current) == 0) {
            total_load += load_current;
        }
    }
    
    // Update panel properties
    set_object_property(obj, "total_load", &total_load, "float");
    
    // Check for overload conditions
    float max_amperage;
    if (get_object_property(obj, "amperage", &max_amperage) == 0) {
        if (total_load > max_amperage * 0.8) {
            // Trigger warning
            trigger_warning(obj, "Panel load at 80% capacity");
        }
    }
    
    return 0;
}
```

## 🌐 **Real-Time Property System**

### **Dynamic Property Management**

```c
// Property system implementation
typedef struct {
    char* key;
    void* value;
    char* type;
    uint64_t last_updated;
    float confidence;
    ArxObject* source;
} DynamicProperty;

// Set object property
int set_object_property(ArxObject* obj, const char* key, void* value, const char* type) {
    // Check if property already exists
    for (int i = 0; i < obj->property_count; i++) {
        if (strcmp(obj->property_keys[i], key) == 0) {
            // Update existing property
            obj->property_values[i] = value;
            obj->property_types[i] = strdup(type);
            return 0;
        }
    }
    
    // Add new property
    if (obj->property_count >= obj->property_capacity) {
        obj->property_capacity *= 2;
        obj->property_keys = realloc(obj->property_keys, 
                                    obj->property_capacity * sizeof(char*));
        obj->property_values = realloc(obj->property_values, 
                                      obj->property_capacity * sizeof(void*));
        obj->property_types = realloc(obj->property_types, 
                                     obj->property_capacity * sizeof(char*));
    }
    
    obj->property_keys[obj->property_count] = strdup(key);
    obj->property_values[obj->property_count] = value;
    obj->property_types[obj->property_count] = strdup(type);
    obj->property_count++;
    
    // Update modification time
    obj->modified_time = get_current_timestamp();
    
    return 0;
}

// Get object property
int get_object_property(ArxObject* obj, const char* key, void* value) {
    for (int i = 0; i < obj->property_count; i++) {
        if (strcmp(obj->property_keys[i], key) == 0) {
            // Copy value based on type
            if (strcmp(obj->property_types[i], "float") == 0) {
                *(float*)value = *(float*)obj->property_values[i];
            } else if (strcmp(obj->property_types[i], "int") == 0) {
                *(int*)value = *(int*)obj->property_values[i];
            } else if (strcmp(obj->property_types[i], "string") == 0) {
                strcpy((char*)value, (char*)obj->property_values[i]);
            }
            return 0;
        }
    }
    return -1; // Property not found
}
```

## 🔗 **Relationship and Constraint System**

### **Object Connections**

```c
// Connection system
typedef struct {
    ArxObject* target;
    char* connection_type;
    float strength;
    ArxObject* connection_point;
} ObjectConnection;

// Connect two objects
int connect_objects(ArxObject* obj1, ArxObject* obj2, const char* connection_type) {
    // Add connection to obj1
    if (obj1->connection_count >= obj1->connection_capacity) {
        obj1->connection_capacity *= 2;
        obj1->connected_to = realloc(obj1->connected_to, 
                                    obj1->connection_capacity * sizeof(ArxObject*));
    }
    
    obj1->connected_to[obj1->connection_count++] = obj2;
    
    // Add reverse connection to obj2
    if (obj2->connection_count >= obj2->connection_capacity) {
        obj2->connection_capacity *= 2;
        obj2->connected_to = realloc(obj2->connected_to, 
                                    obj2->connection_capacity * sizeof(ArxObject*));
    }
    
    obj2->connected_to[obj2->connection_count++] = obj1;
    
    return 0;
}

// Find connected objects
ArxObject** find_connected_objects(ArxObject* obj, const char* type_filter) {
    ArxObject** connected = malloc(obj->connection_count * sizeof(ArxObject*));
    int connected_count = 0;
    
    for (int i = 0; i < obj->connection_count; i++) {
        ArxObject* connected_obj = obj->connected_to[i];
        
        if (type_filter == NULL || 
            strcmp(connected_obj->type->type_name, type_filter) == 0) {
            connected[connected_count++] = connected_obj;
        }
    }
    
    // Resize array to actual count
    connected = realloc(connected, connected_count * sizeof(ArxObject*));
    return connected;
}
```

### **Constraint System**

```c
// Constraint system
typedef struct {
    char* expression;
    char* constraint_type;
    float threshold;
    ArxObject* target;
} Constraint;

// Add constraint to object
int add_constraint(ArxObject* obj, const char* expression, const char* type, float threshold) {
    if (obj->constraint_count >= obj->constraint_capacity) {
        obj->constraint_capacity *= 2;
        obj->constraints = realloc(obj->constraints, 
                                  obj->constraint_capacity * sizeof(char*));
    }
    
    obj->constraints[obj->constraint_count++] = strdup(expression);
    
    return 0;
}

// Validate object constraints
int validate_object_constraints(ArxObject* obj) {
    for (int i = 0; i < obj->constraint_count; i++) {
        if (!evaluate_constraint(obj, obj->constraints[i])) {
            return -1; // Constraint violation
        }
    }
    return 0; // All constraints satisfied
}
```

## 📊 **Performance Monitoring System**

### **Real-Time Metrics**

```c
// Performance monitoring
typedef struct {
    char* metric_name;
    float value;
    uint64_t timestamp;
    float min_value;
    float max_value;
    float average_value;
    int sample_count;
} PerformanceMetric;

// Add performance metric
int add_performance_metric(ArxObject* obj, const char* metric_name, float value) {
    // Find existing metric
    for (int i = 0; i < obj->metric_count; i++) {
        if (strcmp(obj->performance_metrics[i].metric_name, metric_name) == 0) {
            // Update existing metric
            PerformanceMetric* metric = &obj->performance_metrics[i];
            metric->value = value;
            metric->timestamp = get_current_timestamp();
            
            // Update statistics
            if (value < metric->min_value) metric->min_value = value;
            if (value > metric->max_value) metric->max_value = value;
            
            metric->average_value = (metric->average_value * metric->sample_count + value) / 
                                   (metric->sample_count + 1);
            metric->sample_count++;
            
            return 0;
        }
    }
    
    // Add new metric
    if (obj->metric_count >= obj->metric_capacity) {
        obj->metric_capacity *= 2;
        obj->performance_metrics = realloc(obj->performance_metrics, 
                                         obj->metric_capacity * sizeof(PerformanceMetric));
    }
    
    PerformanceMetric* new_metric = &obj->performance_metrics[obj->metric_count++];
    new_metric->metric_name = strdup(metric_name);
    new_metric->value = value;
    new_metric->timestamp = get_current_timestamp();
    new_metric->min_value = value;
    new_metric->max_value = value;
    new_metric->average_value = value;
    new_metric->sample_count = 1;
    
    return 0;
}
```

## 🚀 **Advanced Features**

### **Infinite Depth Navigation**

```c
// Navigate to any depth in the object tree
ArxObject* navigate_to_path(ArxObject* root, const char* path) {
    char* path_copy = strdup(path);
    char* token = strtok(path_copy, "/");
    
    ArxObject* current = root;
    
    while (token != NULL) {
        // Find child with matching name
        ArxObject* child = find_child_by_name(current, token);
        if (child == NULL) {
            free(path_copy);
            return NULL; // Path not found
        }
        
        current = child;
        token = strtok(NULL, "/");
    }
    
    free(path_copy);
    return current;
}

// Find child by name
ArxObject* find_child_by_name(ArxObject* parent, const char* name) {
    for (int i = 0; i < parent->child_count; i++) {
        if (strcmp(parent->children[i]->name, name) == 0) {
            return parent->children[i];
        }
    }
    return NULL;
}
```

### **Pattern Matching and Search**

```c
// Search for objects matching patterns
ArxObject** search_objects(ArxObject* root, const char* pattern, int* result_count) {
    ArxObject** results = malloc(1000 * sizeof(ArxObject*)); // Initial capacity
    *result_count = 0;
    
    search_objects_recursive(root, pattern, results, result_count);
    
    // Resize to actual count
    results = realloc(results, *result_count * sizeof(ArxObject*));
    return results;
}

// Recursive search implementation
void search_objects_recursive(ArxObject* obj, const char* pattern, 
                             ArxObject** results, int* result_count) {
    // Check if this object matches the pattern
    if (matches_pattern(obj, pattern)) {
        results[*result_count] = obj;
        (*result_count)++;
    }
    
    // Recursively search children
    for (int i = 0; i < obj->child_count; i++) {
        search_objects_recursive(obj->children[i], pattern, results, result_count);
    }
}

// Pattern matching
int matches_pattern(ArxObject* obj, const char* pattern) {
    // Simple pattern matching - can be enhanced with regex
    if (strstr(obj->name, pattern) != NULL) {
        return 1;
    }
    
    if (strstr(obj->path, pattern) != NULL) {
        return 1;
    }
    
    // Check properties
    for (int i = 0; i < obj->property_count; i++) {
        if (strstr(obj->property_keys[i], pattern) != NULL) {
            return 1;
        }
    }
    
    return 0;
}
```

## 🏆 **Key Benefits**

### **Universal Accessibility**

- **Filesystem Navigation** - Navigate buildings like file systems
- **CLI Integration** - Terminal-first design for power users
- **Infinite Depth** - No limit to component nesting
- **Type Safety** - Strong typing for building components

### **Real-Time Intelligence**

- **Live Properties** - Real-time updates and monitoring
- **Performance Metrics** - Continuous performance tracking
- **Constraint Validation** - Automatic constraint checking
- **Relationship Tracking** - Complete connection mapping

### **Developer Experience**

- **Simple API** - Easy to create and manage objects
- **Type System** - Extensible type definitions
- **Property System** - Dynamic key-value storage
- **Search Capabilities** - Powerful pattern matching

---

**The ArxObject system transforms buildings into intelligent, navigable, programmable infrastructure that can be managed like software.** 🔧✨
