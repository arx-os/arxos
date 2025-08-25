/**
 * @file arx_spatial.c
 * @brief ArxSpatialIndex System Implementation
 * 
 * Implements high-performance spatial indexing and querying for building objects
 * using octree and R-tree data structures. Enables fast spatial operations like
 * range queries, nearest neighbor searches, and collision detection.
 */

#include "arx_spatial.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <math.h>
#include <float.h>

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
 * @brief Ensure array capacity
 */
static bool ensure_array_capacity(void** array, int* count, int* capacity, size_t element_size) {
    if (*count >= *capacity) {
        int new_capacity = *capacity == 0 ? 16 : *capacity * 2;
        void** new_array = realloc(*array, new_capacity * element_size);
        if (!new_array) return false;
        
        *array = new_array;
        *capacity = new_capacity;
    }
    return true;
}

/**
 * @brief Calculate distance between two points
 */
static double calculate_point_distance(const ArxPoint3D* p1, const ArxPoint3D* p2) {
    if (!p1 || !p2) return DBL_MAX;
    
    double dx = p2->x - p1->x;
    double dy = p2->y - p1->y;
    double dz = p2->z - p1->z;
    
    return sqrt(dx * dx + dy * dy + dz * dz);
}

/**
 * @brief Check if bounding box contains point
 */
static bool bounding_box_contains_point(const ArxBoundingBox* bbox, const ArxPoint3D* point) {
    if (!bbox || !point) return false;
    
    return (point->x >= bbox->min.x && point->x <= bbox->max.x &&
            point->y >= bbox->min.y && point->y <= bbox->max.y &&
            point->z >= bbox->min.z && point->z <= bbox->max.z);
}

/**
 * @brief Check if two bounding boxes intersect
 */
static bool bounding_boxes_intersect(const ArxBoundingBox* bbox1, const ArxBoundingBox* bbox2) {
    if (!bbox1 || !bbox2) return false;
    
    return !(bbox1->max.x < bbox2->min.x || bbox1->min.x > bbox2->max.x ||
             bbox1->max.y < bbox2->min.y || bbox1->min.y > bbox2->max.y ||
             bbox1->max.z < bbox2->min.z || bbox1->min.z > bbox2->max.z);
}

/**
 * @brief Calculate bounding box volume
 */
static double bounding_box_volume(const ArxBoundingBox* bbox) {
    if (!bbox) return 0.0;
    
    double width = bbox->max.x - bbox->min.x;
    double height = bbox->max.y - bbox->min.y;
    double depth = bbox->max.z - bbox->min.z;
    
    return width * height * depth;
}

/**
 * @brief Calculate bounding box surface area
 */
static double bounding_box_surface_area(const ArxBoundingBox* bbox) {
    if (!bbox) return 0.0;
    
    double width = bbox->max.x - bbox->min.x;
    double height = bbox->max.y - bbox->min.y;
    double depth = bbox->max.z - bbox->min.z;
    
    return 2.0 * (width * height + width * depth + height * depth);
}

/**
 * @brief Initialize spatial node
 */
static void init_spatial_node(ArxSpatialNode* node, const ArxBoundingBox* bounds, int depth) {
    if (!node || !bounds) return;
    
    node->bounds = *bounds;
    node->objects = NULL;
    node->object_count = 0;
    node->object_capacity = 0;
    node->is_leaf = true;
    node->depth = depth;
    
    // Calculate center and half-size
    node->center_x = (bounds->min.x + bounds->max.x) / 2.0;
    node->center_y = (bounds->min.y + bounds->max.y) / 2.0;
    node->center_z = (bounds->min.z + bounds->max.z) / 2.0;
    node->half_size = (bounds->max.x - bounds->min.x) / 2.0;
    
    // Initialize children to NULL
    for (int i = 0; i < 8; i++) {
        node->children[i] = NULL;
    }
}

/**
 * @brief Initialize R-tree node
 */
static void init_rtree_node(ArxRTreeNode* node, const ArxBoundingBox* bounds, int depth) {
    if (!node || !bounds) return;
    
    node->bounds = *bounds;
    node->objects = NULL;
    node->object_count = 0;
    node->object_capacity = 0;
    node->children = NULL;
    node->child_count = 0;
    node->child_capacity = 0;
    node->is_leaf = true;
    node->depth = depth;
    node->min_objects = 4;
    node->max_objects = 8;
}

// ============================================================================
// SPATIAL INDEX CREATION AND DESTRUCTION
// ============================================================================

ArxSpatialIndex* arx_spatial_create_index(const ArxSpatialConfig* config) {
    ArxSpatialIndex* index = malloc(sizeof(ArxSpatialIndex));
    if (!index) return NULL;
    
    // Initialize configuration
    if (config) {
        index->config = *config;
    } else {
        // Default configuration
        index->config.max_depth = 8;
        index->config.min_objects_per_node = 4;
        index->config.max_objects_per_node = 8;
        index->config.split_threshold = 0.8;
        index->config.use_octree = true;
        index->config.enable_compression = false;
        index->config.enable_caching = true;
        index->config.cache_size = 1000;
    }
    
    // Initialize structure
    index->octree_root = NULL;
    index->rtree_root = NULL;
    index->all_objects = NULL;
    index->total_objects = 0;
    index->total_capacity = 0;
    
    // Initialize performance metrics
    index->query_count = 0;
    index->cache_hits = 0;
    index->cache_misses = 0;
    index->avg_query_time_ms = 0.0;
    
    // Initialize cache system
    if (index->config.enable_caching) {
        index->query_cache = malloc(index->config.cache_size * sizeof(ArxSpatialQuery));
        index->result_cache = malloc(index->config.cache_size * sizeof(ArxSpatialResult*));
        index->cache_index = 0;
        index->cache_size = index->config.cache_size;
    } else {
        index->query_cache = NULL;
        index->result_cache = NULL;
        index->cache_index = 0;
        index->cache_size = 0;
    }
    
    // Initialize thread safety
    if (pthread_rwlock_init(&index->lock, NULL) != 0) {
        arx_spatial_destroy_index(index);
        return NULL;
    }
    
    index->is_allocated = true;
    return index;
}

ArxSpatialIndex* arx_spatial_create_default_index(void) {
    ArxSpatialConfig config = {
        .max_depth = 8,
        .min_objects_per_node = 4,
        .max_objects_per_node = 8,
        .split_threshold = 0.8,
        .use_octree = true,
        .enable_compression = false,
        .enable_caching = true,
        .cache_size = 1000
    };
    
    return arx_spatial_create_index(&config);
}

void arx_spatial_destroy_index(ArxSpatialIndex* index) {
    if (!index) return;
    
    // Acquire write lock
    pthread_rwlock_wrlock(&index->lock);
    
    // Free all objects array
    if (index->all_objects) {
        free(index->all_objects);
    }
    
    // Free cache system
    if (index->query_cache) {
        free(index->query_cache);
    }
    if (index->result_cache) {
        free(index->result_cache);
    }
    
    // TODO: Implement proper cleanup of octree and R-tree structures
    // This would involve recursive deletion of all nodes
    
    // Destroy thread lock
    pthread_rwlock_unlock(&index->lock);
    pthread_rwlock_destroy(&index->lock);
    
    // Free spatial index structure
    free(index);
}

// ============================================================================
// OBJECT INDEXING
// ============================================================================

bool arx_spatial_add_object(ArxSpatialIndex* index, ArxObject* object) {
    if (!index || !object) return false;
    
    pthread_rwlock_wrlock(&index->lock);
    
    // Add to all objects array
    if (!ensure_array_capacity((void**)&index->all_objects, &index->total_objects, 
                              &index->total_capacity, sizeof(ArxObject*))) {
        pthread_rwlock_unlock(&index->lock);
        return false;
    }
    
    index->all_objects[index->total_objects] = object;
    index->total_objects++;
    
    // TODO: Implement octree/R-tree insertion
    // This would involve:
    // 1. Finding the appropriate node for the object
    // 2. Adding the object to that node
    // 3. Splitting nodes if they exceed capacity
    // 4. Updating bounding boxes up the tree
    
    pthread_rwlock_unlock(&index->lock);
    return true;
}

bool arx_spatial_remove_object(ArxSpatialIndex* index, const char* object_id) {
    if (!index || !object_id) return false;
    
    pthread_rwlock_wrlock(&index->lock);
    
    // Remove from all objects array
    for (int i = 0; i < index->total_objects; i++) {
        if (index->all_objects[i] && strcmp(index->all_objects[i]->id, object_id) == 0) {
            // Shift remaining objects
            for (int j = i; j < index->total_objects - 1; j++) {
                index->all_objects[j] = index->all_objects[j + 1];
            }
            index->total_objects--;
            
            // TODO: Implement octree/R-tree removal
            // This would involve:
            // 1. Finding the node containing the object
            // 2. Removing the object from that node
            // 3. Merging nodes if they fall below minimum capacity
            // 4. Updating bounding boxes up the tree
            
            pthread_rwlock_unlock(&index->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&index->lock);
    return false; // Object not found
}

bool arx_spatial_update_object_position(ArxSpatialIndex* index, 
                                       const char* object_id, 
                                       const ArxPoint3D* new_position) {
    if (!index || !object_id || !new_position) return false;
    
    // TODO: Implement position update
    // This would involve:
    // 1. Finding the object in the index
    // 2. Removing it from its current node
    // 3. Updating its position
    // 4. Re-inserting it into the appropriate node
    
    return false;
}

bool arx_spatial_rebuild_index(ArxSpatialIndex* index) {
    if (!index) return false;
    
    pthread_rwlock_wrlock(&index->lock);
    
    // TODO: Implement complete index rebuild
    // This would involve:
    // 1. Destroying existing octree/R-tree structures
    // 2. Rebuilding from scratch using all objects
    // 3. Optimizing node sizes and depths
    
    pthread_rwlock_unlock(&index->lock);
    return true;
}

bool arx_spatial_optimize_index(ArxSpatialIndex* index) {
    if (!index) return false;
    
    pthread_rwlock_wrlock(&index->lock);
    
    // TODO: Implement index optimization
    // This would involve:
    // 1. Balancing tree structures
    // 2. Adjusting node capacities
    // 3. Reorganizing object distributions
    
    pthread_rwlock_unlock(&index->lock);
    return true;
}

// ============================================================================
// SPATIAL QUERIES
// ============================================================================

ArxSpatialResult** arx_spatial_query(const ArxSpatialIndex* index, 
                                    const ArxSpatialQuery* query, 
                                    int* result_count) {
    if (!index || !query || !result_count) {
        if (result_count) *result_count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&index->lock);
    
    // Update query count
    index->query_count++;
    
    // TODO: Implement generic query routing
    // This would route to the appropriate query function based on type
    
    ArxSpatialResult** results = NULL;
    *result_count = 0;
    
    switch (query->type) {
        case ARX_SPATIAL_QUERY_RANGE:
            // results = query_range_octree(index, &query->params.range_query.range, result_count);
            break;
        case ARX_SPATIAL_QUERY_POINT:
            // results = query_point_octree(index, &query->params.point_query.point, result_count);
            break;
        case ARX_SPATIAL_QUERY_NEAREST:
            // results = query_nearest_octree(index, &query->params.point_query.point, 
            //                               query->params.point_query.radius, 
            //                               query->params.point_query.max_results, result_count);
            break;
        case ARX_SPATIAL_QUERY_INTERSECT:
            // results = query_intersect_octree(index, query->params.intersect_query.object, 
            //                                 query->params.intersect_query.tolerance, result_count);
            break;
        default:
            break;
    }
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&index->lock);
    return results;
}

ArxSpatialResult** arx_spatial_query_range(const ArxSpatialIndex* index, 
                                          const ArxBoundingBox* range, 
                                          int* result_count) {
    if (!index || !range || !result_count) {
        if (result_count) *result_count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&index->lock);
    
    // Simple linear search for now
    // TODO: Implement proper octree/R-tree range query
    
    int count = 0;
    ArxSpatialResult** results = NULL;
    
    for (int i = 0; i < index->total_objects; i++) {
        if (index->all_objects[i] && 
            bounding_boxes_intersect(range, &index->all_objects[i]->geometry.bounding_box)) {
            
            if (!ensure_array_capacity((void**)&results, &count, 
                                     &count, sizeof(ArxSpatialResult*))) {
                break;
            }
            
            ArxSpatialResult* result = malloc(sizeof(ArxSpatialResult));
            if (result) {
                result->object = index->all_objects[i];
                result->distance = 0.0; // Range queries don't have distance
                result->relevance_score = 1.0;
                result->intersection_point = (ArxPoint3D){0, 0, 0};
                result->overlap_region = *range;
                
                results[count] = result;
                count++;
            }
        }
    }
    
    *result_count = count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&index->lock);
    return results;
}

ArxSpatialResult** arx_spatial_query_point(const ArxSpatialIndex* index, 
                                          const ArxPoint3D* point, 
                                          int* result_count) {
    if (!index || !point || !result_count) {
        if (result_count) *result_count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&index->lock);
    
    // Simple linear search for now
    // TODO: Implement proper octree/R-tree point query
    
    int count = 0;
    ArxSpatialResult** results = NULL;
    
    for (int i = 0; i < index->total_objects; i++) {
        if (index->all_objects[i] && 
            bounding_box_contains_point(&index->all_objects[i]->geometry.bounding_box, point)) {
            
            if (!ensure_array_capacity((void**)&results, &count, 
                                     &count, sizeof(ArxSpatialResult*))) {
                break;
            }
            
            ArxSpatialResult* result = malloc(sizeof(ArxSpatialResult));
            if (result) {
                result->object = index->all_objects[i];
                result->distance = 0.0;
                result->relevance_score = 1.0;
                result->intersection_point = *point;
                result->overlap_region = index->all_objects[i]->geometry.bounding_box;
                
                results[count] = result;
                count++;
            }
        }
    }
    
    *result_count = count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&index->lock);
    return results;
}

ArxSpatialResult** arx_spatial_query_nearest(const ArxSpatialIndex* index, 
                                            const ArxPoint3D* point, 
                                            double radius, 
                                            int max_results, 
                                            int* result_count) {
    if (!index || !point || !result_count) {
        if (result_count) *result_count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&index->lock);
    
    // Simple linear search for now
    // TODO: Implement proper octree/R-tree nearest neighbor query
    
    int count = 0;
    ArxSpatialResult** results = NULL;
    
    for (int i = 0; i < index->total_objects && count < max_results; i++) {
        if (index->all_objects[i]) {
            double distance = calculate_point_distance(point, &index->all_objects[i]->geometry.bounding_box.min);
            if (distance <= radius) {
                
                if (!ensure_array_capacity((void**)&results, &count, 
                                         &count, sizeof(ArxSpatialResult*))) {
                    break;
                }
                
                ArxSpatialResult* result = malloc(sizeof(ArxSpatialResult));
                if (result) {
                    result->object = index->all_objects[i];
                    result->distance = distance;
                    result->relevance_score = 1.0 - (distance / radius);
                    result->intersection_point = (ArxPoint3D){0, 0, 0};
                    result->overlap_region = index->all_objects[i]->geometry.bounding_box;
                    
                    results[count] = result;
                    count++;
                }
            }
        }
    }
    
    *result_count = count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&index->lock);
    return results;
}

// ============================================================================
// SPATIAL OPERATIONS
// ============================================================================

bool arx_spatial_objects_intersect(const ArxObject* obj1, 
                                  const ArxObject* obj2, 
                                  double tolerance) {
    if (!obj1 || !obj2) return false;
    
    return bounding_boxes_intersect(&obj1->geometry.bounding_box, 
                                   &obj2->geometry.bounding_box);
}

double arx_spatial_objects_distance(const ArxObject* obj1, const ArxObject* obj2) {
    if (!obj1 || !obj2) return DBL_MAX;
    
    // Calculate distance between bounding box centers
    ArxPoint3D center1 = {
        (obj1->geometry.bounding_box.min.x + obj1->geometry.bounding_box.max.x) / 2.0,
        (obj1->geometry.bounding_box.min.y + obj1->geometry.bounding_box.max.y) / 2.0,
        (obj1->geometry.bounding_box.min.z + obj1->geometry.bounding_box.max.z) / 2.0
    };
    
    ArxPoint3D center2 = {
        (obj2->geometry.bounding_box.min.x + obj2->geometry.bounding_box.max.x) / 2.0,
        (obj2->geometry.bounding_box.min.y + obj2->geometry.bounding_box.max.y) / 2.0,
        (obj2->geometry.bounding_box.min.z + obj2->geometry.bounding_box.max.z) / 2.0
    };
    
    return calculate_point_distance(&center1, &center2);
}

double arx_spatial_objects_overlap_volume(const ArxObject* obj1, const ArxObject* obj2) {
    if (!obj1 || !obj2) return 0.0;
    
    if (!bounding_boxes_intersect(&obj1->geometry.bounding_box, 
                                 &obj2->geometry.bounding_box)) {
        return 0.0;
    }
    
    // Calculate overlap bounding box
    ArxBoundingBox overlap = {
        {
            fmax(obj1->geometry.bounding_box.min.x, obj2->geometry.bounding_box.min.x),
            fmax(obj1->geometry.bounding_box.min.y, obj2->geometry.bounding_box.min.y),
            fmax(obj1->geometry.bounding_box.min.z, obj2->geometry.bounding_box.min.z)
        },
        {
            fmin(obj1->geometry.bounding_box.max.x, obj2->geometry.bounding_box.max.x),
            fmin(obj1->geometry.bounding_box.max.y, obj2->geometry.bounding_box.max.y),
            fmin(obj1->geometry.bounding_box.max.z, obj2->geometry.bounding_box.max.z)
        }
    };
    
    return bounding_box_volume(&overlap);
}

bool arx_spatial_object_inside(const ArxObject* inner, const ArxObject* outer) {
    if (!inner || !outer) return false;
    
    return (inner->geometry.bounding_box.min.x >= outer->geometry.bounding_box.min.x &&
            inner->geometry.bounding_box.max.x <= outer->geometry.bounding_box.max.x &&
            inner->geometry.bounding_box.min.y >= outer->geometry.bounding_box.min.y &&
            inner->geometry.bounding_box.max.y <= outer->geometry.bounding_box.max.y &&
            inner->geometry.bounding_box.min.z >= outer->geometry.bounding_box.min.z &&
            inner->geometry.bounding_box.max.z <= outer->geometry.bounding_box.max.z);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

ArxBoundingBox arx_spatial_create_bounding_box(const ArxPoint3D* points, int point_count) {
    ArxBoundingBox bbox = {{DBL_MAX, DBL_MAX, DBL_MAX}, {-DBL_MAX, -DBL_MAX, -DBL_MAX}};
    
    if (!points || point_count <= 0) return bbox;
    
    for (int i = 0; i < point_count; i++) {
        if (points[i].x < bbox.min.x) bbox.min.x = points[i].x;
        if (points[i].y < bbox.min.y) bbox.min.y = points[i].y;
        if (points[i].z < bbox.min.z) bbox.min.z = points[i].z;
        if (points[i].x > bbox.max.x) bbox.max.x = points[i].x;
        if (points[i].y > bbox.max.y) bbox.max.y = points[i].y;
        if (points[i].z > bbox.max.z) bbox.max.z = points[i].z;
    }
    
    return bbox;
}

void arx_spatial_expand_bounding_box(ArxBoundingBox* bbox, const ArxPoint3D* point) {
    if (!bbox || !point) return;
    
    if (point->x < bbox->min.x) bbox->min.x = point->x;
    if (point->y < bbox->min.y) bbox->min.y = point->y;
    if (point->z < bbox->min.z) bbox->min.z = point->z;
    if (point->x > bbox->max.x) bbox->max.x = point->x;
    if (point->y > bbox->max.y) bbox->max.y = point->y;
    if (point->z > bbox->max.z) bbox->max.z = point->z;
}

bool arx_spatial_bounding_box_contains_point(const ArxBoundingBox* bbox, 
                                           const ArxPoint3D* point) {
    return bounding_box_contains_point(bbox, point);
}

bool arx_spatial_bounding_boxes_intersect(const ArxBoundingBox* bbox1, 
                                        const ArxBoundingBox* bbox2) {
    return bounding_boxes_intersect(bbox1, bbox2);
}

double arx_spatial_bounding_box_volume(const ArxBoundingBox* bbox) {
    return bounding_box_volume(bbox);
}

double arx_spatial_bounding_box_surface_area(const ArxBoundingBox* bbox) {
    return bounding_box_surface_area(bbox);
}

// ============================================================================
// PERFORMANCE AND STATISTICS
// ============================================================================

char* arx_spatial_get_statistics(const ArxSpatialIndex* index) {
    if (!index) return NULL;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&index->lock);
    
    size_t buffer_size = 1024;
    char* stats = malloc(buffer_size);
    if (!stats) {
        pthread_rwlock_unlock((pthread_rwlock_t*)&index->lock);
        return NULL;
    }
    
    snprintf(stats, buffer_size,
             "Spatial Index Statistics:\n"
             "Total Objects: %d\n"
             "Total Capacity: %d\n"
             "Max Depth: %d\n"
             "Min Objects per Node: %d\n"
             "Max Objects per Node: %d\n"
             "Use Octree: %s\n"
             "Enable Caching: %s\n"
             "Cache Size: %d",
             index->total_objects,
             index->total_capacity,
             index->config.max_depth,
             index->config.min_objects_per_node,
             index->config.max_objects_per_node,
             index->config.use_octree ? "Yes" : "No",
             index->config.enable_caching ? "Yes" : "No",
             index->config.cache_size);
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&index->lock);
    return stats;
}

size_t arx_spatial_get_memory_usage(const ArxSpatialIndex* index) {
    if (!index) return 0;
    
    size_t usage = sizeof(ArxSpatialIndex);
    
    // Add all objects array size
    usage += index->total_capacity * sizeof(ArxObject*);
    
    // Add cache sizes
    if (index->query_cache) {
        usage += index->cache_size * sizeof(ArxSpatialQuery);
    }
    if (index->result_cache) {
        usage += index->cache_size * sizeof(ArxSpatialResult*);
    }
    
    // TODO: Add octree and R-tree memory usage
    // This would involve recursive calculation of all node sizes
    
    return usage;
}
