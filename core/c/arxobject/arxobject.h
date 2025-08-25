/**
 * ArxObject Runtime Engine - Core Header
 * 
 * This is the foundation of the Building Infrastructure-as-Code platform.
 * ArxObjects represent programmable building components with physics simulation,
 * constraint propagation, and real-time building automation capabilities.
 * 
 * Performance targets:
 * - ArxObject operations: <1ms response time
 * - Spatial calculations: <10ms for complex queries
 * - Constraint propagation: <5ms for building-wide updates
 */

#ifndef ARXOBJECT_H
#define ARXOBJECT_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include <pthread.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Core Data Types
// ============================================================================

/**
 * ArxObject types - the building element categories
 * These represent the "DNA of buildings" - every physical component
 * in a building maps to one of these types
 */
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

/**
 * Validation status for field worker contributions
 */
typedef enum {
    ARX_VALIDATION_PENDING = 0,
    ARX_VALIDATION_VALIDATED,
    ARX_VALIDATION_FAILED,
    ARX_VALIDATION_PARTIAL
} ArxValidationStatus;

/**
 * 3D point with millimeter precision
 * Using int64 for high precision without floating point overhead
 */
typedef struct {
    int64_t x;  // X coordinate in millimeters
    int64_t y;  // Y coordinate in millimeters  
    int64_t z;  // Z coordinate in millimeters
} ArxPoint3D;

/**
 * Bounding box for spatial calculations
 */
typedef struct {
    ArxPoint3D min;  // Minimum corner
    ArxPoint3D max;  // Maximum corner
} ArxBoundingBox;

/**
 * Spatial geometry with position, rotation, and scale
 */
typedef struct {
    ArxPoint3D position;           // Center point
    ArxBoundingBox bounding_box;   // Spatial bounds
    double rotation;               // Rotation in degrees
    double scale;                  // Scale factor
    ArxPoint3D* points;           // Complex shape points (optional)
    int point_count;              // Number of points
    ArxPoint3D* vertices;         // 3D mesh vertices (optional)
    int vertex_count;             // Number of vertices
    int* faces;                   // Face indices (optional)
    int face_count;               // Number of faces
} ArxGeometry;

/**
 * Property value union for flexible metadata storage
 */
typedef union {
    int64_t int_value;
    double float_value;
    char* string_value;
    bool bool_value;
    ArxPoint3D point_value;
    void* custom_value;
} ArxPropertyValue;

/**
 * Property type for type-safe property access
 */
typedef enum {
    ARX_PROP_INT,
    ARX_PROP_FLOAT,
    ARX_PROP_STRING,
    ARX_PROP_BOOL,
    ARX_PROP_POINT,
    ARX_PROP_CUSTOM
} ArxPropertyType;

/**
 * Property definition with type and value
 */
typedef struct {
    char* key;
    ArxPropertyType type;
    ArxPropertyValue value;
    bool is_required;
    char* description;
} ArxProperty;

/**
 * Relationship between ArxObjects
 */
typedef struct {
    char* id;
    char* type;                    // "contains", "connects_to", "adjacent_to"
    char* target_id;               // Target ArxObject ID
    char* source_id;               // Source ArxObject ID
    ArxProperty* properties;       // Relationship properties
    int property_count;
    double confidence;             // 0.0 to 1.0
    time_t created_at;
} ArxRelationship;

/**
 * Validation record from field workers
 */
typedef struct {
    char* id;
    time_t timestamp;
    char* validated_by;            // Field worker ID
    char* method;                  // "photo", "lidar", "manual"
    char* evidence;                // Photo URLs, scan data
    double confidence;             // 0.0 to 1.0
    char* notes;
} ArxValidationRecord;

/**
 * Constraint rule for validation
 */
typedef struct {
    char* id;
    char* name;
    char* description;
    ArxProperty* conditions;       // When this constraint applies
    ArxProperty* requirements;     // What must be true
    double severity;               // 0.0 to 1.0 (how important)
    char* error_message;
} ArxConstraint;

/**
 * Physics simulation model
 */
typedef struct {
    char* model_type;              // "hvac_thermal", "electrical_load", etc.
    ArxProperty* parameters;       // Model parameters
    int parameter_count;
    void* simulation_data;         // Opaque simulation state
    size_t data_size;
} ArxPhysicsModel;

// ============================================================================
// Core ArxObject Structure
// ============================================================================

/**
 * ArxObject - the programmable building component
 * This is the "DNA of buildings" - every physical component inherits from this
 */
typedef struct ArxObject {
    // Core Identity
    char* id;                      // Unique identifier
    ArxObjectType type;            // Building element type
    char* name;                    // Human-readable name
    char* description;             // Detailed description
    
    // Hierarchy
    char* building_id;             // Parent building
    char* floor_id;                // Floor level
    char* zone_id;                 // Zone/area
    char* parent_id;               // Parent component
    
    // Spatial Properties
    ArxGeometry geometry;          // Position, size, shape
    
    // Properties and Metadata
    ArxProperty* properties;       // Key-value properties
    int property_count;
    char* material;                // Material type
    char* color;                   // Visual color
    
    // Relationships
    ArxRelationship* relationships; // Connections to other objects
    int relationship_count;
    
    // Validation & Confidence
    ArxValidationStatus validation_status;
    ArxValidationRecord* validations;
    int validation_count;
    double confidence;             // 0.0 to 1.0
    double* confidence_factors;    // Per-factor confidence scores
    int confidence_factor_count;
    
    // Constraints
    ArxConstraint* constraints;    // Validation rules
    int constraint_count;
    
    // Physics & Simulation
    ArxPhysicsModel* physics;      // Behavioral simulation
    
    // Source & Versioning
    char* source_type;             // "pdf", "ifc", "lidar", "manual"
    char* source_file;             // Source file path
    int source_page;               // Page number (for PDFs)
    int version;                   // Version number
    
    // Timestamps
    time_t created_at;
    time_t updated_at;
    time_t validated_at;
    
    // Metadata
    char** tags;                   // Searchable tags
    int tag_count;
    uint32_t flags;                // Bit flags for filtering
    char* hash;                    // Content hash for deduplication
    
    // Thread Safety
    pthread_rwlock_t lock;         // Read-write lock for concurrent access
    
    // Memory Management
    bool is_allocated;             // Track if this object was dynamically allocated
} ArxObject;

// ============================================================================
// Core Function Declarations
// ============================================================================

/**
 * ArxObject Lifecycle Management
 */
ArxObject* arx_object_create(ArxObjectType type, const char* name);
void arx_object_destroy(ArxObject* obj);
ArxObject* arx_object_clone(const ArxObject* obj);
bool arx_object_is_valid(const ArxObject* obj);

/**
 * Property Management
 */
bool arx_object_set_property(ArxObject* obj, const char* key, ArxPropertyType type, ArxPropertyValue value);
bool arx_object_get_property(const ArxObject* obj, const char* key, ArxPropertyValue* value);
bool arx_object_has_property(const ArxObject* obj, const char* key);
bool arx_object_remove_property(ArxObject* obj, const char* key);

/**
 * Geometry and Spatial Operations
 */
bool arx_object_set_geometry(ArxObject* obj, const ArxGeometry* geometry);
bool arx_object_get_geometry(const ArxObject* obj, ArxGeometry* geometry);
bool arx_object_update_position(ArxObject* obj, const ArxPoint3D* position);
bool arx_object_is_point_inside(const ArxObject* obj, const ArxPoint3D* point);
bool arx_object_intersects_with(const ArxObject* obj, const ArxObject* other);

/**
 * Relationship Management
 */
bool arx_object_add_relationship(ArxObject* obj, const ArxRelationship* relationship);
bool arx_object_remove_relationship(ArxObject* obj, const char* relationship_id);
ArxRelationship* arx_object_get_relationships(const ArxObject* obj, const char* type, int* count);
bool arx_object_has_relationship(const ArxObject* obj, const char* target_id, const char* type);

/**
 * Validation and Confidence
 */
bool arx_object_add_validation(ArxObject* obj, const ArxValidationRecord* validation);
bool arx_object_is_validated(const ArxObject* obj);
double arx_object_get_confidence(const ArxObject* obj);
bool arx_object_update_confidence(ArxObject* obj, double confidence);

/**
 * Constraint Validation
 */
bool arx_object_add_constraint(ArxObject* obj, const ArxConstraint* constraint);
bool arx_object_validate_constraints(const ArxObject* obj, ArxValidationRecord* result);
bool arx_object_check_constraint(const ArxObject* obj, const char* constraint_id);

/**
 * Physics and Simulation
 */
bool arx_object_set_physics_model(ArxObject* obj, const ArxPhysicsModel* model);
bool arx_object_simulate(ArxObject* obj, const char* simulation_type, ArxProperty* parameters, int param_count);
bool arx_object_get_simulation_result(const ArxObject* obj, ArxProperty* result, int* result_count);

/**
 * Serialization and Persistence
 */
char* arx_object_to_json(const ArxObject* obj);
ArxObject* arx_object_from_json(const char* json);
char* arx_object_to_binary(const ArxObject* obj, size_t* size);
ArxObject* arx_object_from_binary(const char* data, size_t size);

/**
 * Utility Functions
 */
char* arx_object_get_type_name(ArxObjectType type);
ArxObjectType arx_object_get_type_from_name(const char* name);
bool arx_object_calculate_hash(ArxObject* obj);
bool arx_object_is_type(const ArxObject* obj, ArxObjectType type);

/**
 * Memory Management
 */
void arx_object_free_string(char* str);
void arx_object_free_properties(ArxProperty* props, int count);
void arx_object_free_relationships(ArxRelationship* rels, int count);
void arx_object_free_validations(ArxValidationRecord* vals, int count);

#ifdef __cplusplus
}
#endif

#endif // ARXOBJECT_H
