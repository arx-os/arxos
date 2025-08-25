/**
 * @file arx_spatial.h
 * @brief ArxSpatialIndex System
 * 
 * Provides efficient spatial indexing and querying for building objects using
 * octree and R-tree data structures. Enables fast spatial operations like
 * range queries, nearest neighbor searches, and collision detection.
 */

#ifndef ARX_SPATIAL_H
#define ARX_SPATIAL_H

#include <stdbool.h>
#include <stdint.h>
#include "../arxobject/arxobject.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct ArxSpatialNode ArxSpatialNode;
typedef struct ArxSpatialIndex ArxSpatialIndex;
typedef struct ArxSpatialQuery ArxSpatialQuery;
typedef struct ArxSpatialResult ArxSpatialResult;

/**
 * @brief Spatial query types
 */
typedef enum {
    ARX_SPATIAL_QUERY_RANGE,        // Objects within bounding box
    ARX_SPATIAL_QUERY_POINT,        // Objects containing point
    ARX_SPATIAL_QUERY_NEAREST,      // Nearest objects to point
    ARX_SPATIAL_QUERY_INTERSECT,    // Objects intersecting with object
    ARX_SPATIAL_QUERY_RAYCAST,      // Objects hit by ray
    ARX_SPATIAL_QUERY_VISIBILITY    // Objects visible from point
} ArxSpatialQueryType;

/**
 * @brief Spatial query parameters
 */
typedef struct ArxSpatialQuery {
    ArxSpatialQueryType type;
    
    // Query-specific parameters
    union {
        struct {
            ArxBoundingBox range;    // For range queries
        } range_query;
        
        struct {
            ArxPoint3D point;        // For point queries
            double radius;            // For nearest neighbor
            int max_results;          // Maximum results to return
        } point_query;
        
        struct {
            ArxObject* object;       // For intersection queries
            double tolerance;         // Intersection tolerance
        } intersect_query;
        
        struct {
            ArxPoint3D origin;       // Ray origin
            ArxPoint3D direction;    // Ray direction
            double max_distance;      // Maximum ray distance
        } raycast_query;
        
        struct {
            ArxPoint3D viewpoint;    // View point
            double max_distance;      // Maximum visibility distance
            double fov_angle;        // Field of view angle
        } visibility_query;
    } params;
    
    // Filter options
    ArxObjectType* type_filter;      // Filter by object types
    int type_filter_count;           // Number of type filters
    double min_size;                 // Minimum object size
    double max_size;                 // Maximum object size
    bool include_inactive;           // Include inactive objects
} ArxSpatialQuery;

/**
 * @brief Spatial query result
 */
typedef struct ArxSpatialResult {
    ArxObject* object;               // Found object
    double distance;                 // Distance from query point/object
    double relevance_score;          // Relevance score (0.0 to 1.0)
    ArxPoint3D intersection_point;   // Intersection point (if applicable)
    ArxBoundingBox overlap_region;   // Overlap region (if applicable)
} ArxSpatialResult;

/**
 * @brief Octree node for spatial subdivision
 */
typedef struct ArxSpatialNode {
    ArxBoundingBox bounds;           // Node bounding box
    ArxObject** objects;             // Objects in this node
    int object_count;                // Number of objects
    int object_capacity;             // Capacity of objects array
    
    // Child nodes (octree subdivision)
    ArxSpatialNode* children[8];     // 8 children for 3D subdivision
    bool is_leaf;                    // Is this a leaf node
    int depth;                       // Node depth in tree
    
    // Spatial properties
    double center_x, center_y, center_z; // Node center
    double half_size;                // Half-size of node
} ArxSpatialNode;

/**
 * @brief R-tree node for hierarchical spatial indexing
 */
typedef struct ArxRTreeNode {
    ArxBoundingBox bounds;           // Node bounding box
    ArxObject** objects;             // Objects in this node
    int object_count;                // Number of objects
    int object_capacity;             // Capacity of objects array
    
    // Child nodes (R-tree structure)
    ArxRTreeNode** children;         // Child nodes
    int child_count;                 // Number of children
    int child_capacity;              // Capacity of children array
    
    // R-tree properties
    bool is_leaf;                    // Is this a leaf node
    int depth;                       // Node depth in tree
    int min_objects;                 // Minimum objects per node
    int max_objects;                 // Maximum objects per node
} ArxRTreeNode;

/**
 * @brief Spatial index configuration
 */
typedef struct {
    int max_depth;                   // Maximum tree depth
    int min_objects_per_node;        // Minimum objects per node
    int max_objects_per_node;        // Maximum objects per node
    double split_threshold;          // Split threshold for subdivision
    bool use_octree;                 // Use octree instead of R-tree
    bool enable_compression;         // Enable spatial compression
    bool enable_caching;             // Enable query result caching
    int cache_size;                  // Cache size in entries
} ArxSpatialConfig;

/**
 * @brief Main spatial index structure
 */
typedef struct ArxSpatialIndex {
    ArxSpatialConfig config;         // Index configuration
    
    // Index structures
    ArxSpatialNode* octree_root;     // Octree root node
    ArxRTreeNode* rtree_root;        // R-tree root node
    
    // Object tracking
    ArxObject** all_objects;         // All indexed objects
    int total_objects;               // Total number of objects
    int total_capacity;              // Total capacity
    
    // Performance metrics
    uint64_t query_count;            // Total queries performed
    uint64_t cache_hits;             // Cache hit count
    uint64_t cache_misses;           // Cache miss count
    double avg_query_time_ms;        // Average query time in milliseconds
    
    // Cache system
    ArxSpatialQuery* query_cache;    // Query cache
    ArxSpatialResult** result_cache; // Result cache
    int cache_index;                 // Current cache index
    int cache_size;                  // Cache size
    
    // Thread safety
    pthread_rwlock_t lock;
    
    // Memory management
    bool is_allocated;
} ArxSpatialIndex;

// ============================================================================
// SPATIAL INDEX CREATION AND DESTRUCTION
// ============================================================================

/**
 * @brief Create a new spatial index
 * @param config Spatial index configuration
 * @return New ArxSpatialIndex instance or NULL on failure
 */
ArxSpatialIndex* arx_spatial_create_index(const ArxSpatialConfig* config);

/**
 * @brief Destroy a spatial index and free all resources
 * @param index Spatial index to destroy
 */
void arx_spatial_destroy_index(ArxSpatialIndex* index);

/**
 * @brief Initialize spatial index with default configuration
 * @return New ArxSpatialIndex instance with defaults or NULL on failure
 */
ArxSpatialIndex* arx_spatial_create_default_index(void);

// ============================================================================
// OBJECT INDEXING
// ============================================================================

/**
 * @brief Add an object to the spatial index
 * @param index Spatial index to add object to
 * @param object Object to add
 * @return true on success, false on failure
 */
bool arx_spatial_add_object(ArxSpatialIndex* index, ArxObject* object);

/**
 * @brief Remove an object from the spatial index
 * @param index Spatial index to remove object from
 * @param object_id ID of object to remove
 * @return true on success, false on failure
 */
bool arx_spatial_remove_object(ArxSpatialIndex* index, const char* object_id);

/**
 * @brief Update an object's position in the spatial index
 * @param index Spatial index to update
 * @param object_id ID of object to update
 * @param new_position New position
 * @return true on success, false on failure
 */
bool arx_spatial_update_object_position(ArxSpatialIndex* index, 
                                       const char* object_id, 
                                       const ArxPoint3D* new_position);

/**
 * @brief Rebuild the entire spatial index
 * @param index Spatial index to rebuild
 * @return true on success, false on failure
 */
bool arx_spatial_rebuild_index(ArxSpatialIndex* index);

/**
 * @brief Optimize the spatial index for better performance
 * @param index Spatial index to optimize
 * @return true on success, false on failure
 */
bool arx_spatial_optimize_index(ArxSpatialIndex* index);

// ============================================================================
// SPATIAL QUERIES
// ============================================================================

/**
 * @brief Perform a spatial query
 * @param index Spatial index to query
 * @param query Query parameters
 * @param result_count Output parameter for number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query(const ArxSpatialIndex* index, 
                                    const ArxSpatialQuery* query, 
                                    int* result_count);

/**
 * @brief Find objects within a bounding box
 * @param index Spatial index to query
 * @param range Bounding box range
 * @param result_count Output parameter for number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query_range(const ArxSpatialIndex* index, 
                                          const ArxBoundingBox* range, 
                                          int* result_count);

/**
 * @brief Find objects containing a point
 * @param index Spatial index to query
 * @param point Point to search for
 * @param result_count Output parameter for number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query_point(const ArxSpatialIndex* index, 
                                          const ArxPoint3D* point, 
                                          int* result_count);

/**
 * @brief Find nearest objects to a point
 * @param index Spatial index to query
 * @param point Point to search from
 * @param radius Search radius
 * @param max_results Maximum number of results
 * @param result_count Output parameter for actual number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query_nearest(const ArxSpatialIndex* index, 
                                            const ArxPoint3D* point, 
                                            double radius, 
                                            int max_results, 
                                            int* result_count);

/**
 * @brief Find objects intersecting with another object
 * @param index Spatial index to query
 * @param object Object to check intersections with
 * @param tolerance Intersection tolerance
 * @param result_count Output parameter for number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query_intersect(const ArxSpatialIndex* index, 
                                              const ArxObject* object, 
                                              double tolerance, 
                                              int* result_count);

/**
 * @brief Perform raycast query
 * @param index Spatial index to query
 * @param origin Ray origin point
 * @param direction Ray direction vector
 * @param max_distance Maximum ray distance
 * @param result_count Output parameter for number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query_raycast(const ArxSpatialIndex* index, 
                                            const ArxPoint3D* origin, 
                                            const ArxPoint3D* direction, 
                                            double max_distance, 
                                            int* result_count);

/**
 * @brief Find objects visible from a viewpoint
 * @param index Spatial index to query
 * @param viewpoint View point
 * @param max_distance Maximum visibility distance
 * @param fov_angle Field of view angle
 * @param result_count Output parameter for number of results
 * @return Array of spatial results or NULL on failure
 */
ArxSpatialResult** arx_spatial_query_visibility(const ArxSpatialIndex* index, 
                                               const ArxPoint3D* viewpoint, 
                                               double max_distance, 
                                               double fov_angle, 
                                               int* result_count);

// ============================================================================
// SPATIAL OPERATIONS
// ============================================================================

/**
 * @brief Check if two objects intersect
 * @param obj1 First object
 * @param obj2 Second object
 * @param tolerance Intersection tolerance
 * @return true if objects intersect, false otherwise
 */
bool arx_spatial_objects_intersect(const ArxObject* obj1, 
                                  const ArxObject* obj2, 
                                  double tolerance);

/**
 * @brief Calculate distance between two objects
 * @param obj1 First object
 * @param obj2 Second object
 * @return Distance between objects
 */
double arx_spatial_objects_distance(const ArxObject* obj1, const ArxObject* obj2);

/**
 * @brief Calculate overlap volume between two objects
 * @param obj1 First object
 * @param obj2 Second object
 * @return Overlap volume
 */
double arx_spatial_objects_overlap_volume(const ArxObject* obj1, const ArxObject* obj2);

/**
 * @brief Check if object is inside another object
 * @param inner Inner object
 * @param outer Outer object
 * @return true if inner is inside outer, false otherwise
 */
bool arx_spatial_object_inside(const ArxObject* inner, const ArxObject* outer);

/**
 * @brief Find collision pairs in a set of objects
 * @param objects Array of objects to check
 * @param object_count Number of objects
 * @param tolerance Collision tolerance
 * @param collision_count Output parameter for number of collisions
 * @return Array of collision pairs or NULL if none found
 */
ArxSpatialResult** arx_spatial_find_collisions(ArxObject** objects, 
                                              int object_count, 
                                              double tolerance, 
                                              int* collision_count);

// ============================================================================
// SPATIAL ANALYSIS
// ============================================================================

/**
 * @brief Calculate spatial density in a region
 * @param index Spatial index to analyze
 * @param region Region to analyze
 * @return Spatial density (objects per unit volume)
 */
double arx_spatial_calculate_density(const ArxSpatialIndex* index, 
                                   const ArxBoundingBox* region);

/**
 * @brief Find spatial clusters in the index
 * @param index Spatial index to analyze
 * @param min_cluster_size Minimum cluster size
 * @param cluster_count Output parameter for number of clusters
 * @return Array of cluster bounding boxes or NULL if none found
 */
ArxBoundingBox* arx_spatial_find_clusters(const ArxSpatialIndex* index, 
                                         int min_cluster_size, 
                                         int* cluster_count);

/**
 * @brief Calculate spatial coverage statistics
 * @param index Spatial index to analyze
 * @param region Region to analyze
 * @return Coverage statistics string or NULL on failure
 */
char* arx_spatial_calculate_coverage(const ArxSpatialIndex* index, 
                                   const ArxBoundingBox* region);

// ============================================================================
// PERFORMANCE AND STATISTICS
// ============================================================================

/**
 * @brief Get spatial index statistics
 * @param index Spatial index to get stats for
 * @return Statistics string or NULL on failure
 */
char* arx_spatial_get_statistics(const ArxSpatialIndex* index);

/**
 * @brief Get spatial index performance metrics
 * @param index Spatial index to get metrics for
 * @return Performance metrics string or NULL on failure
 */
char* arx_spatial_get_performance_metrics(const ArxSpatialIndex* index);

/**
 * @brief Clear performance metrics
 * @param index Spatial index to clear metrics for
 */
void arx_spatial_clear_metrics(ArxSpatialIndex* index);

/**
 * @brief Get spatial index memory usage
 * @param index Spatial index to check
 * @return Memory usage in bytes
 */
size_t arx_spatial_get_memory_usage(const ArxSpatialIndex* index);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Create a bounding box from points
 * @param points Array of points
 * @param point_count Number of points
 * @return Bounding box containing all points
 */
ArxBoundingBox arx_spatial_create_bounding_box(const ArxPoint3D* points, int point_count);

/**
 * @brief Expand bounding box to include point
 * @param bbox Bounding box to expand
 * @param point Point to include
 */
void arx_spatial_expand_bounding_box(ArxBoundingBox* bbox, const ArxPoint3D* point);

/**
 * @brief Check if bounding box contains point
 * @param bbox Bounding box to check
 * @param point Point to check
 * @return true if point is inside, false otherwise
 */
bool arx_spatial_bounding_box_contains_point(const ArxBoundingBox* bbox, 
                                           const ArxPoint3D* point);

/**
 * @brief Check if two bounding boxes intersect
 * @param bbox1 First bounding box
 * @param bbox2 Second bounding box
 * @return true if boxes intersect, false otherwise
 */
bool arx_spatial_bounding_boxes_intersect(const ArxBoundingBox* bbox1, 
                                        const ArxBoundingBox* bbox2);

/**
 * @brief Calculate bounding box volume
 * @param bbox Bounding box to calculate volume for
 * @return Volume of bounding box
 */
double arx_spatial_bounding_box_volume(const ArxBoundingBox* bbox);

/**
 * @brief Calculate bounding box surface area
 * @param bbox Bounding box to calculate area for
 * @return Surface area of bounding box
 */
double arx_spatial_bounding_box_surface_area(const ArxBoundingBox* bbox);

#ifdef __cplusplus
}
#endif

#endif // ARX_SPATIAL_H
