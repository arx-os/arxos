/**
 * @file arx_building.h
 * @brief ArxBuilding Management System
 * 
 * Manages complete building state, including objects, spatial indexing,
 * version control, and validation. This is the central coordinator
 * for all building operations.
 */

#ifndef ARX_BUILDING_H
#define ARX_BUILDING_H

#include <time.h>
#include <stdbool.h>
#include "../arxobject/arxobject.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct ArxSpatialIndex ArxSpatialIndex;
typedef struct ArxVersionControl ArxVersionControl;
typedef struct ArxValidationEngine ArxValidationEngine;
typedef struct ArxBuilding ArxBuilding;

/**
 * @brief Building metadata and configuration
 */
typedef struct {
    char* name;
    char* description;
    char* location;
    char* architect;
    char* owner;
    time_t created_at;
    time_t last_modified;
    ArxPoint3D dimensions;
    int floor_count;
    double total_area;
    char* building_code;
    char* version;
} ArxBuildingMetadata;

/**
 * @brief Building statistics and metrics
 */
typedef struct {
    int total_objects;
    int objects_by_type[ARX_OBJECT_TYPE_COUNT];
    double total_volume;
    double total_area;
    ArxBoundingBox bounds;
    int validation_errors;
    int validation_warnings;
    time_t last_validation;
} ArxBuildingStats;

/**
 * @brief Main building structure
 */
typedef struct ArxBuilding {
    ArxBuildingMetadata metadata;
    ArxBuildingStats stats;
    
    // Core data
    ArxObject** objects;
    int object_count;
    int object_capacity;
    
    // Subsystems
    ArxSpatialIndex* spatial_index;
    ArxVersionControl* version_control;
    ArxValidationEngine* validation_engine;
    
    // State
    bool is_modified;
    bool is_validated;
    pthread_rwlock_t lock;
    
    // Memory management
    bool is_allocated;
} ArxBuilding;

// ============================================================================
// BUILDING LIFECYCLE MANAGEMENT
// ============================================================================

/**
 * @brief Create a new building instance
 * @param name Building name
 * @param description Building description
 * @return New ArxBuilding instance or NULL on failure
 */
ArxBuilding* arx_building_create(const char* name, const char* description);

/**
 * @brief Destroy a building instance and free all resources
 * @param building Building to destroy
 */
void arx_building_destroy(ArxBuilding* building);

/**
 * @brief Clone a building instance
 * @param building Building to clone
 * @return New cloned building instance or NULL on failure
 */
ArxBuilding* arx_building_clone(const ArxBuilding* building);

/**
 * @brief Check if building is valid
 * @param building Building to validate
 * @return true if valid, false otherwise
 */
bool arx_building_is_valid(const ArxBuilding* building);

// ============================================================================
// OBJECT MANAGEMENT
// ============================================================================

/**
 * @brief Add an object to the building
 * @param building Building to add object to
 * @param object Object to add
 * @return true on success, false on failure
 */
bool arx_building_add_object(ArxBuilding* building, ArxObject* object);

/**
 * @brief Remove an object from the building
 * @param building Building to remove object from
 * @param object_id ID of object to remove
 * @return true on success, false on failure
 */
bool arx_building_remove_object(ArxBuilding* building, const char* object_id);

/**
 * @brief Get an object by ID
 * @param building Building to search in
 * @param object_id ID of object to find
 * @return ArxObject pointer or NULL if not found
 */
ArxObject* arx_building_get_object(const ArxBuilding* building, const char* object_id);

/**
 * @brief Get all objects of a specific type
 * @param building Building to search in
 * @param type Type of objects to find
 * @param count Output parameter for number of objects found
 * @return Array of ArxObject pointers or NULL if none found
 */
ArxObject** arx_building_get_objects_by_type(const ArxBuilding* building, 
                                            ArxObjectType type, int* count);

/**
 * @brief Get objects within a spatial range
 * @param building Building to search in
 * @param range Bounding box to search within
 * @param count Output parameter for number of objects found
 * @return Array of ArxObject pointers or NULL if none found
 */
ArxObject** arx_building_get_objects_in_range(const ArxBuilding* building,
                                             const ArxBoundingBox* range, int* count);

// ============================================================================
// SPATIAL OPERATIONS
// ============================================================================

/**
 * @brief Update building spatial index
 * @param building Building to update
 * @return true on success, false on failure
 */
bool arx_building_update_spatial_index(ArxBuilding* building);

/**
 * @brief Get building bounding box
 * @param building Building to get bounds for
 * @return Bounding box containing all objects
 */
ArxBoundingBox arx_building_get_bounds(const ArxBuilding* building);

/**
 * @brief Check if point is inside building
 * @param building Building to check
 * @param point Point to check
 * @return true if point is inside, false otherwise
 */
bool arx_building_contains_point(const ArxBuilding* building, const ArxPoint3D* point);

/**
 * @brief Get objects intersecting with a given object
 * @param building Building to search in
 * @param object Object to check intersections with
 * @param count Output parameter for number of intersecting objects
 * @return Array of intersecting ArxObject pointers or NULL if none found
 */
ArxObject** arx_building_get_intersecting_objects(const ArxBuilding* building,
                                                 const ArxObject* object, int* count);

// ============================================================================
// VALIDATION
// ============================================================================

/**
 * @brief Validate entire building
 * @param building Building to validate
 * @return true if valid, false if validation errors found
 */
bool arx_building_validate(ArxBuilding* building);

/**
 * @brief Get validation status
 * @param building Building to check
 * @return Validation status
 */
ArxValidationStatus arx_building_get_validation_status(const ArxBuilding* building);

/**
 * @brief Get validation errors
 * @param building Building to check
 * @param count Output parameter for number of errors
 * @return Array of validation records or NULL if none
 */
ArxValidationRecord** arx_building_get_validation_errors(const ArxBuilding* building, int* count);

// ============================================================================
// STATISTICS AND METRICS
// ============================================================================

/**
 * @brief Update building statistics
 * @param building Building to update stats for
 * @return true on success, false on failure
 */
bool arx_building_update_stats(ArxBuilding* building);

/**
 * @brief Get building statistics
 * @param building Building to get stats for
 * @return Building statistics
 */
ArxBuildingStats arx_building_get_stats(const ArxBuilding* building);

/**
 * @brief Calculate building metrics
 * @param building Building to calculate metrics for
 * @return true on success, false on failure
 */
bool arx_building_calculate_metrics(ArxBuilding* building);

// ============================================================================
// PERSISTENCE
// ============================================================================

/**
 * @brief Save building to file
 * @param building Building to save
 * @param filepath File path to save to
 * @return true on success, false on failure
 */
bool arx_building_save_to_file(const ArxBuilding* building, const char* filepath);

/**
 * @brief Load building from file
 * @param filepath File path to load from
 * @return Loaded building instance or NULL on failure
 */
ArxBuilding* arx_building_load_from_file(const char* filepath);

/**
 * @brief Export building to ASCII art
 * @param building Building to export
 * @param options Rendering options
 * @return ASCII art string or NULL on failure
 */
char* arx_building_export_ascii(const ArxBuilding* building, const void* options);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Get building summary as string
 * @param building Building to summarize
 * @return Summary string or NULL on failure
 */
char* arx_building_get_summary(const ArxBuilding* building);

/**
 * @brief Check if building has been modified
 * @param building Building to check
 * @return true if modified, false otherwise
 */
bool arx_building_is_modified(const ArxBuilding* building);

/**
 * @brief Mark building as saved (clear modified flag)
 * @param building Building to mark as saved
 */
void arx_building_mark_saved(ArxBuilding* building);

/**
 * @brief Get building memory usage
 * @param building Building to check
 * @return Memory usage in bytes
 */
size_t arx_building_get_memory_usage(const ArxBuilding* building);

#ifdef __cplusplus
}
#endif

#endif // ARX_BUILDING_H
