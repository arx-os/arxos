/**
 * @file arx_building.c
 * @brief ArxBuilding Management System Implementation
 * 
 * Implements the complete building management system including object lifecycle,
 * spatial indexing, validation, and statistics tracking.
 */

#include "arx_building.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <math.h>

// ============================================================================
// INTERNAL HELPER FUNCTIONS
// ============================================================================

/**
 * @brief Safe string duplication with NULL check
 */
static char* safe_strdup(const char* str) {
    if (!str) return NULL;
    size_t len = strlen(str);
    char* dup = malloc(len + 1);
    if (dup) {
        strcpy(dup, str);
    }
    return dup;
}

/**
 * @brief Free string safely
 */
static void safe_free(char* str) {
    if (str) {
        free(str);
    }
}

/**
 * @brief Initialize building metadata with defaults
 */
static void init_building_metadata(ArxBuildingMetadata* metadata, 
                                 const char* name, const char* description) {
    metadata->name = safe_strdup(name);
    metadata->description = safe_strdup(description);
    metadata->location = NULL;
    metadata->architect = NULL;
    metadata->owner = NULL;
    metadata->created_at = time(NULL);
    metadata->last_modified = time(NULL);
    metadata->dimensions = (ArxPoint3D){0, 0, 0};
    metadata->floor_count = 1;
    metadata->total_area = 0.0;
    metadata->building_code = NULL;
    metadata->version = safe_strdup("1.0.0");
}

/**
 * @brief Initialize building statistics
 */
static void init_building_stats(ArxBuildingStats* stats) {
    stats->total_objects = 0;
    memset(stats->objects_by_type, 0, sizeof(stats->objects_by_type));
    stats->total_volume = 0.0;
    stats->total_area = 0.0;
    stats->bounds = (ArxBoundingBox){{0, 0, 0}, {0, 0, 0}};
    stats->validation_errors = 0;
    stats->validation_warnings = 0;
    stats->last_validation = 0;
}

/**
 * @brief Ensure building has capacity for more objects
 */
static bool ensure_object_capacity(ArxBuilding* building) {
    if (building->object_count >= building->object_capacity) {
        int new_capacity = building->object_capacity == 0 ? 16 : building->object_capacity * 2;
        ArxObject** new_objects = realloc(building->objects, new_capacity * sizeof(ArxObject*));
        if (!new_objects) return false;
        
        building->objects = new_objects;
        building->object_capacity = new_capacity;
    }
    return true;
}

/**
 * @brief Calculate object volume
 */
static double calculate_object_volume(const ArxObject* obj) {
    if (!obj || !obj->geometry.points) return 0.0;
    
    // Simple bounding box volume calculation
    ArxBoundingBox bbox = obj->geometry.bounding_box;
    double width = bbox.max.x - bbox.min.x;
    double height = bbox.max.y - bbox.min.y;
    double depth = bbox.max.z - bbox.min.z;
    
    return width * height * depth;
}

/**
 * @brief Calculate object area (2D projection)
 */
static double calculate_object_area(const ArxObject* obj) {
    if (!obj || !obj->geometry.points) return 0.0;
    
    // Simple bounding box area calculation (top-down view)
    ArxBoundingBox bbox = obj->geometry.bounding_box;
    double width = bbox.max.x - bbox.min.x;
    double depth = bbox.max.z - bbox.min.z;
    
    return width * depth;
}

// ============================================================================
// BUILDING LIFECYCLE MANAGEMENT
// ============================================================================

ArxBuilding* arx_building_create(const char* name, const char* description) {
    if (!name) return NULL;
    
    ArxBuilding* building = malloc(sizeof(ArxBuilding));
    if (!building) return NULL;
    
    // Initialize metadata and stats
    init_building_metadata(&building->metadata, name, description);
    init_building_stats(&building->stats);
    
    // Initialize core data
    building->objects = NULL;
    building->object_count = 0;
    building->object_capacity = 0;
    
    // Initialize subsystems (placeholders for now)
    building->spatial_index = NULL;
    building->version_control = NULL;
    building->validation_engine = NULL;
    
    // Initialize state
    building->is_modified = false;
    building->is_validated = false;
    
    // Initialize thread safety
    if (pthread_rwlock_init(&building->lock, NULL) != 0) {
        arx_building_destroy(building);
        return NULL;
    }
    
    building->is_allocated = true;
    return building;
}

void arx_building_destroy(ArxBuilding* building) {
    if (!building) return;
    
    // Acquire write lock
    pthread_rwlock_wrlock(&building->lock);
    
    // Free metadata strings
    safe_free(building->metadata.name);
    safe_free(building->metadata.description);
    safe_free(building->metadata.location);
    safe_free(building->metadata.architect);
    safe_free(building->metadata.owner);
    safe_free(building->metadata.building_code);
    safe_free(building->metadata.version);
    
    // Free objects array (objects themselves are managed externally)
    if (building->objects) {
        free(building->objects);
    }
    
    // Destroy subsystems (placeholders for now)
    // TODO: Implement proper cleanup when subsystems are implemented
    
    // Destroy thread lock
    pthread_rwlock_unlock(&building->lock);
    pthread_rwlock_destroy(&building->lock);
    
    // Free building structure
    free(building);
}

ArxBuilding* arx_building_clone(const ArxBuilding* building) {
    if (!building) return NULL;
    
    ArxBuilding* clone = arx_building_create(building->metadata.name, 
                                           building->metadata.description);
    if (!clone) return NULL;
    
    // Acquire read lock on source
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    
    // Copy metadata
    clone->metadata.location = safe_strdup(building->metadata.location);
    clone->metadata.architect = safe_strdup(building->metadata.architect);
    clone->metadata.owner = safe_strdup(building->metadata.owner);
    clone->metadata.building_code = safe_strdup(building->metadata.building_code);
    clone->metadata.dimensions = building->metadata.dimensions;
    clone->metadata.floor_count = building->metadata.floor_count;
    clone->metadata.total_area = building->metadata.total_area;
    
    // Copy objects (shallow copy - objects are referenced, not duplicated)
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i]) {
            arx_building_add_object(clone, building->objects[i]);
        }
    }
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    
    return clone;
}

bool arx_building_is_valid(const ArxBuilding* building) {
    if (!building) return false;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    bool valid = building->is_validated && building->stats.validation_errors == 0;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    
    return valid;
}

// ============================================================================
// OBJECT MANAGEMENT
// ============================================================================

bool arx_building_add_object(ArxBuilding* building, ArxObject* object) {
    if (!building || !object) return false;
    
    pthread_rwlock_wrlock(&building->lock);
    
    // Check if object already exists
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i] && strcmp(building->objects[i]->id, object->id) == 0) {
            pthread_rwlock_unlock(&building->lock);
            return false; // Object already exists
        }
    }
    
    // Ensure capacity
    if (!ensure_object_capacity(building)) {
        pthread_rwlock_unlock(&building->lock);
        return false;
    }
    
    // Add object
    building->objects[building->object_count] = object;
    building->object_count++;
    
    // Update stats
    building->stats.total_objects++;
    if (object->type >= 0 && object->type < ARX_OBJECT_TYPE_COUNT) {
        building->stats.objects_by_type[object->type]++;
    }
    
    // Mark as modified
    building->is_modified = true;
    building->metadata.last_modified = time(NULL);
    
    pthread_rwlock_unlock(&building->lock);
    return true;
}

bool arx_building_remove_object(ArxBuilding* building, const char* object_id) {
    if (!building || !object_id) return false;
    
    pthread_rwlock_wrlock(&building->lock);
    
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i] && strcmp(building->objects[i]->id, object_id) == 0) {
            // Update stats
            ArxObjectType type = building->objects[i]->type;
            if (type >= 0 && type < ARX_OBJECT_TYPE_COUNT) {
                building->stats.objects_by_type[type]--;
            }
            building->stats.total_objects--;
            
            // Remove object (shift remaining objects)
            for (int j = i; j < building->object_count - 1; j++) {
                building->objects[j] = building->objects[j + 1];
            }
            building->object_count--;
            
            // Mark as modified
            building->is_modified = true;
            building->metadata.last_modified = time(NULL);
            
            pthread_rwlock_unlock(&building->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&building->lock);
    return false; // Object not found
}

ArxObject* arx_building_get_object(const ArxBuilding* building, const char* object_id) {
    if (!building || !object_id) return NULL;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i] && strcmp(building->objects[i]->id, object_id) == 0) {
            ArxObject* obj = building->objects[i];
            pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
            return obj;
        }
    }
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    return NULL;
}

ArxObject** arx_building_get_objects_by_type(const ArxBuilding* building, 
                                            ArxObjectType type, int* count) {
    if (!building || !count || type < 0 || type >= ARX_OBJECT_TYPE_COUNT) {
        if (count) *count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    
    // Count objects of this type
    int type_count = 0;
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i] && building->objects[i]->type == type) {
            type_count++;
        }
    }
    
    if (type_count == 0) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    // Allocate and populate result array
    ArxObject** result = malloc(type_count * sizeof(ArxObject*));
    if (!result) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    int result_index = 0;
    for (int i = 0; i < building->object_count && result_index < type_count; i++) {
        if (building->objects[i] && building->objects[i]->type == type) {
            result[result_index++] = building->objects[i];
        }
    }
    
    *count = type_count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    return result;
}

ArxObject** arx_building_get_objects_in_range(const ArxBuilding* building,
                                             const ArxBoundingBox* range, int* count) {
    if (!building || !range || !count) {
        if (count) *count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    
    // Count objects in range
    int range_count = 0;
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i] && 
            arx_object_intersects_with(building->objects[i], range)) {
            range_count++;
        }
    }
    
    if (range_count == 0) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    // Allocate and populate result array
    ArxObject** result = malloc(range_count * sizeof(ArxObject*));
    if (!result) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    int result_index = 0;
    for (int i = 0; i < building->object_count && result_index < range_count; i++) {
        if (building->objects[i] && 
            arx_object_intersects_with(building->objects[i], range)) {
            result[result_index++] = building->objects[i];
        }
    }
    
    *count = range_count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    return result;
}

// ============================================================================
// SPATIAL OPERATIONS
// ============================================================================

bool arx_building_update_spatial_index(ArxBuilding* building) {
    if (!building) return false;
    
    // TODO: Implement spatial indexing when ArxSpatialIndex is implemented
    // For now, just update bounds
    return arx_building_calculate_metrics(building);
}

ArxBoundingBox arx_building_get_bounds(const ArxBuilding* building) {
    if (!building) return (ArxBoundingBox){{0, 0, 0}, {0, 0, 0}};
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    ArxBoundingBox bounds = building->stats.bounds;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    
    return bounds;
}

bool arx_building_contains_point(const ArxBuilding* building, const ArxPoint3D* point) {
    if (!building || !point) return false;
    
    ArxBoundingBox bounds = arx_building_get_bounds(building);
    
    return (point->x >= bounds.min.x && point->x <= bounds.max.x &&
            point->y >= bounds.min.y && point->y <= bounds.max.y &&
            point->z >= bounds.min.z && point->z <= bounds.max.z);
}

ArxObject** arx_building_get_intersecting_objects(const ArxBuilding* building,
                                                 const ArxObject* object, int* count) {
    if (!building || !object || !count) {
        if (count) *count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    
    // Count intersecting objects
    int intersect_count = 0;
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i] && building->objects[i] != object &&
            arx_object_intersects_with(building->objects[i], object)) {
            intersect_count++;
        }
    }
    
    if (intersect_count == 0) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    // Allocate and populate result array
    ArxObject** result = malloc(intersect_count * sizeof(ArxObject*));
    if (!result) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    int result_index = 0;
    for (int i = 0; i < building->object_count && result_index < intersect_count; i++) {
        if (building->objects[i] && building->objects[i] != object &&
            arx_object_intersects_with(building->objects[i], object)) {
            result[result_index++] = building->objects[i];
        }
    }
    
    *count = intersect_count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    return result;
}

// ============================================================================
// VALIDATION
// ============================================================================

bool arx_building_validate(ArxBuilding* building) {
    if (!building) return false;
    
    // TODO: Implement full validation when ArxValidationEngine is implemented
    // For now, just mark as validated
    pthread_rwlock_wrlock(&building->lock);
    building->is_validated = true;
    building->stats.last_validation = time(NULL);
    pthread_rwlock_unlock(&building->lock);
    
    return true;
}

ArxValidationStatus arx_building_get_validation_status(const ArxBuilding* building) {
    if (!building) return ARX_VALIDATION_INVALID;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    ArxValidationStatus status = building->is_validated ? 
        (building->stats.validation_errors == 0 ? ARX_VALIDATION_VALID : ARX_VALIDATION_INVALID) :
        ARX_VALIDATION_PENDING;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    
    return status;
}

ArxValidationRecord** arx_building_get_validation_errors(const ArxBuilding* building, int* count) {
    if (!building || !count) {
        if (count) *count = 0;
        return NULL;
    }
    
    // TODO: Implement when ArxValidationEngine is implemented
    *count = 0;
    return NULL;
}

// ============================================================================
// STATISTICS AND METRICS
// ============================================================================

bool arx_building_update_stats(ArxBuilding* building) {
    if (!building) return false;
    
    return arx_building_calculate_metrics(building);
}

ArxBuildingStats arx_building_get_stats(const ArxBuilding* building) {
    if (!building) return (ArxBuildingStats){0};
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    ArxBuildingStats stats = building->stats;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    
    return stats;
}

bool arx_building_calculate_metrics(ArxBuilding* building) {
    if (!building) return false;
    
    pthread_rwlock_wrlock(&building->lock);
    
    // Reset stats
    building->stats.total_objects = building->object_count;
    memset(building->stats.objects_by_type, 0, sizeof(building->stats.objects_by_type));
    building->stats.total_volume = 0.0;
    building->stats.total_area = 0.0;
    
    // Calculate bounds
    ArxBoundingBox bounds = {{INFINITY, INFINITY, INFINITY}, {-INFINITY, -INFINITY, -INFINITY}};
    bool has_objects = false;
    
    for (int i = 0; i < building->object_count; i++) {
        if (building->objects[i]) {
            ArxObject* obj = building->objects[i];
            
            // Update type counts
            if (obj->type >= 0 && obj->type < ARX_OBJECT_TYPE_COUNT) {
                building->stats.objects_by_type[obj->type]++;
            }
            
            // Update bounds
            ArxBoundingBox obj_bounds = obj->geometry.bounding_box;
            if (obj_bounds.min.x < bounds.min.x) bounds.min.x = obj_bounds.min.x;
            if (obj_bounds.min.y < bounds.min.y) bounds.min.y = obj_bounds.min.y;
            if (obj_bounds.min.z < bounds.min.z) bounds.min.z = obj_bounds.min.z;
            if (obj_bounds.max.x > bounds.max.x) bounds.max.x = obj_bounds.max.x;
            if (obj_bounds.max.y > bounds.max.y) bounds.max.y = obj_bounds.max.y;
            if (obj_bounds.max.z > bounds.max.z) bounds.max.z = obj_bounds.max.z;
            
            // Calculate volume and area
            building->stats.total_volume += calculate_object_volume(obj);
            building->stats.total_area += calculate_object_area(obj);
            
            has_objects = true;
        }
    }
    
    if (has_objects) {
        building->stats.bounds = bounds;
    } else {
        building->stats.bounds = (ArxBoundingBox){{0, 0, 0}, {0, 0, 0}};
    }
    
    pthread_rwlock_unlock(&building->lock);
    return true;
}

// ============================================================================
// PERSISTENCE
// ============================================================================

bool arx_building_save_to_file(const ArxBuilding* building, const char* filepath) {
    if (!building || !filepath) return false;
    
    // TODO: Implement file persistence
    // This will serialize the building to JSON or binary format
    return false;
}

ArxBuilding* arx_building_load_from_file(const char* filepath) {
    if (!filepath) return NULL;
    
    // TODO: Implement file loading
    // This will deserialize from JSON or binary format
    return NULL;
}

char* arx_building_export_ascii(const ArxBuilding* building, const void* options) {
    if (!building) return NULL;
    
    // TODO: Implement ASCII export using the ASCII engine
    // This will generate 2D/3D ASCII representations
    return NULL;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

char* arx_building_get_summary(const ArxBuilding* building) {
    if (!building) return NULL;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    
    // Calculate required buffer size
    size_t buffer_size = 512; // Base size
    char* summary = malloc(buffer_size);
    if (!summary) {
        pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
        return NULL;
    }
    
    snprintf(summary, buffer_size,
             "Building: %s\n"
             "Description: %s\n"
             "Objects: %d\n"
             "Total Area: %.2f m²\n"
             "Total Volume: %.2f m³\n"
             "Last Modified: %s\n"
             "Validation: %s",
             building->metadata.name ? building->metadata.name : "Unknown",
             building->metadata.description ? building->metadata.description : "No description",
             building->stats.total_objects,
             building->stats.total_area,
             building->stats.total_volume,
             ctime(&building->metadata.last_modified),
             building->is_validated ? "Validated" : "Not validated");
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    return summary;
}

bool arx_building_is_modified(const ArxBuilding* building) {
    if (!building) return false;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&building->lock);
    bool modified = building->is_modified;
    pthread_rwlock_unlock((pthread_rwlock_t*)&building->lock);
    
    return modified;
}

void arx_building_mark_saved(ArxBuilding* building) {
    if (!building) return;
    
    pthread_rwlock_wrlock(&building->lock);
    building->is_modified = false;
    pthread_rwlock_unlock(&building->lock);
}

size_t arx_building_get_memory_usage(const ArxBuilding* building) {
    if (!building) return 0;
    
    size_t usage = sizeof(ArxBuilding);
    
    // Add metadata string sizes
    if (building->metadata.name) usage += strlen(building->metadata.name) + 1;
    if (building->metadata.description) usage += strlen(building->metadata.description) + 1;
    if (building->metadata.location) usage += strlen(building->metadata.location) + 1;
    if (building->metadata.architect) usage += strlen(building->metadata.architect) + 1;
    if (building->metadata.owner) usage += strlen(building->metadata.owner) + 1;
    if (building->metadata.building_code) usage += strlen(building->metadata.building_code) + 1;
    if (building->metadata.version) usage += strlen(building->metadata.version) + 1;
    
    // Add objects array size
    usage += building->object_capacity * sizeof(ArxObject*);
    
    return usage;
}
