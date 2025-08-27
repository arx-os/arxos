// arxobject_bridge.h - CGO bridge to ArxObject C core
#ifndef ARXOBJECT_BRIDGE_H
#define ARXOBJECT_BRIDGE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Core Data Types
// ============================================================================

// ArxObjectType enumeration
typedef enum {
    ARX_TYPE_UNKNOWN = 0,
    ARX_TYPE_BUILDING,
    ARX_TYPE_FLOOR,
    ARX_TYPE_ROOM,
    ARX_TYPE_WALL,
    ARX_TYPE_DOOR,
    ARX_TYPE_WINDOW,
    ARX_TYPE_COLUMN,
    ARX_TYPE_BEAM,
    ARX_TYPE_SLAB,
    ARX_TYPE_ROOF,
    ARX_TYPE_STAIR,
    ARX_TYPE_ELEVATOR,
    ARX_TYPE_EQUIPMENT,
    ARX_TYPE_FURNITURE,
    ARX_TYPE_FIXTURE,
    ARX_TYPE_PIPE,
    ARX_TYPE_DUCT,
    ARX_TYPE_CABLE,
    ARX_TYPE_SENSOR,
    ARX_TYPE_SYSTEM
} ArxObjectType;

// 3D Point structure
typedef struct {
    double x;
    double y;
    double z;
} ArxPoint3D;

// Bounding box structure
typedef struct {
    ArxPoint3D min;
    ArxPoint3D max;
} ArxBoundingBox;

// ArxObject structure (simplified for CGO)
typedef struct ArxObject {
    uint64_t id;                    // Unique identifier
    char* name;                      // Object name
    char* path;                      // Hierarchical path
    ArxObjectType obj_type;          // Object type (renamed to avoid Go keyword conflict)
    
    // Spatial properties (millimeter precision)
    int32_t world_x_mm;
    int32_t world_y_mm;
    int32_t world_z_mm;
    int32_t width_mm;
    int32_t height_mm;
    int32_t depth_mm;
    
    // Hierarchy
    uint64_t parent_id;
    uint64_t* child_ids;
    size_t child_count;
    
    // Confidence and validation
    float confidence;
    bool is_validated;
    
    // Metadata (JSON string for flexibility)
    char* properties_json;
    char* metadata_json;
} ArxObject;

// Query result structure
typedef struct {
    ArxObject** objects;
    size_t count;
    char* error_message;
} ArxQueryResult;

// Operation result structure
typedef struct {
    bool success;
    char* message;
    void* data;
} ArxResult;

// ============================================================================
// Initialization and Cleanup
// ============================================================================

// Initialize the ArxObject system
ArxResult* arx_initialize(const char* config_json);

// Cleanup and free resources
void arx_cleanup(void);

// ============================================================================
// Object CRUD Operations
// ============================================================================

// Create a new ArxObject
ArxObject* arx_object_create(
    const char* name,
    const char* path,
    ArxObjectType type,
    int32_t x_mm,
    int32_t y_mm,
    int32_t z_mm
);

// Get an ArxObject by ID
ArxObject* arx_object_get(uint64_t id);

// Update an ArxObject
ArxResult* arx_object_update(ArxObject* obj);

// Delete an ArxObject
ArxResult* arx_object_delete(uint64_t id);

// Free an ArxObject structure
void arx_object_free(ArxObject* obj);

// ============================================================================
// Query Operations
// ============================================================================

// Find objects by path pattern
ArxQueryResult* arx_query_by_path(const char* path_pattern);

// Find objects within a bounding box
ArxQueryResult* arx_query_by_bounds(const ArxBoundingBox* bounds);

// Find objects by type
ArxQueryResult* arx_query_by_type(ArxObjectType type);

// Find objects by confidence threshold
ArxQueryResult* arx_query_by_confidence(float min_confidence);

// Execute custom query (AQL string)
ArxQueryResult* arx_query_execute(const char* aql_query);

// Free query result
void arx_query_result_free(ArxQueryResult* result);

// ============================================================================
// Hierarchy Operations
// ============================================================================

// Add child to parent
ArxResult* arx_hierarchy_add_child(uint64_t parent_id, uint64_t child_id);

// Remove child from parent
ArxResult* arx_hierarchy_remove_child(uint64_t parent_id, uint64_t child_id);

// Get all children of an object
ArxQueryResult* arx_hierarchy_get_children(uint64_t parent_id);

// Get parent of an object
ArxObject* arx_hierarchy_get_parent(uint64_t child_id);

// Get full path to root
char* arx_hierarchy_get_path(uint64_t object_id);

// ============================================================================
// Spatial Operations
// ============================================================================

// Calculate distance between objects
double arx_spatial_distance(uint64_t id1, uint64_t id2);

// Check if object is within bounds
bool arx_spatial_within_bounds(uint64_t id, const ArxBoundingBox* bounds);

// Find nearest neighbors
ArxQueryResult* arx_spatial_nearest_neighbors(uint64_t id, size_t count);

// Check intersection
bool arx_spatial_intersects(uint64_t id1, uint64_t id2);

// Get bounding box
ArxBoundingBox* arx_spatial_get_bounds(uint64_t id);

// ============================================================================
// ASCII Rendering
// ============================================================================

// Render 2D ASCII representation
char* arx_ascii_render_2d(
    ArxObject** objects,
    size_t count,
    int width,
    int height
);

// Render 3D ASCII representation
char* arx_ascii_render_3d(
    ArxObject** objects,
    size_t count,
    int width,
    int height,
    int depth
);

// Render single object as ASCII
char* arx_ascii_render_object(ArxObject* obj);

// ============================================================================
// Validation and Confidence
// ============================================================================

// Mark object as validated
ArxResult* arx_validate_object(uint64_t id, const char* validator, float confidence);

// Propagate confidence to related objects
ArxResult* arx_propagate_confidence(uint64_t id);

// Calculate aggregate confidence for a building
float arx_calculate_building_confidence(uint64_t building_id);

// ============================================================================
// Performance Metrics
// ============================================================================

// Get performance statistics
typedef struct {
    uint64_t total_objects;
    uint64_t total_queries;
    double avg_query_time_ms;
    double avg_create_time_ms;
    double avg_update_time_ms;
    size_t memory_usage_bytes;
} ArxPerformanceStats;

ArxPerformanceStats* arx_get_performance_stats(void);
void arx_performance_stats_free(ArxPerformanceStats* stats);

// ============================================================================
// Utility Functions
// ============================================================================

// Get last error message
const char* arx_get_last_error(void);

// Set log level (0=none, 1=error, 2=warn, 3=info, 4=debug)
void arx_set_log_level(int level);

// Get version string
const char* arx_get_version(void);

#ifdef __cplusplus
}
#endif

#endif // ARXOBJECT_BRIDGE_H