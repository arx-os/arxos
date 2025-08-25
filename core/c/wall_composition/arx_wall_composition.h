#ifndef ARX_WALL_COMPOSITION_H
#define ARX_WALL_COMPOSITION_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// CONSTANTS AND ENUMS
// =============================================================================

// Unit types for measurement
typedef enum {
    ARX_UNIT_NANOMETER = 0,
    ARX_UNIT_MICROMETER,
    ARX_UNIT_MILLIMETER,
    ARX_UNIT_CENTIMETER,
    ARX_UNIT_METER,
    ARX_UNIT_INCH,
    ARX_UNIT_FOOT
} arx_unit_t;

// Validation states
typedef enum {
    ARX_VALIDATION_PENDING = 0,
    ARX_VALIDATION_PARTIAL,
    ARX_VALIDATION_COMPLETE,
    ARX_VALIDATION_CONFLICT
} arx_validation_state_t;

// Wall types
typedef enum {
    ARX_WALL_TYPE_INTERIOR = 0,
    ARX_WALL_TYPE_EXTERIOR,
    ARX_WALL_TYPE_LOAD_BEARING,
    ARX_WALL_TYPE_PARTITION,
    ARX_WALL_TYPE_FIRE_RATED,
    ARX_WALL_TYPE_SOUND_RATED
} arx_wall_type_t;

// Curved wall types
typedef enum {
    ARX_CURVE_TYPE_LINEAR = 0,
    ARX_CURVE_TYPE_ARC,
    ARX_CURVE_TYPE_BEZIER_QUADRATIC,
    ARX_CURVE_TYPE_BEZIER_CUBIC,
    ARX_CURVE_TYPE_SPLINE
} arx_curve_type_t;

// =============================================================================
// CORE DATA STRUCTURES
// =============================================================================

// 3D point with nanometer precision
typedef struct {
    int64_t x, y, z;  // Stored in nanometers
    arx_unit_t unit;  // Display unit
} arx_smart_point_3d_t;

// Wall segment with properties
typedef struct {
    uint64_t id;
    arx_smart_point_3d_t start_point;
    arx_smart_point_3d_t end_point;
    double length;        // mm
    double height;        // mm
    double thickness;     // mm
    double confidence;    // 0.0 - 1.0
    double orientation;   // degrees
    arx_wall_type_t wall_type;
    char material[64];
    char fire_rating[32];
    uint64_t arx_object_ids[16];  // Max 16 ArxObjects per segment
    uint8_t arx_object_count;
    time_t created_at;
} arx_wall_segment_t;

// Wall connection between segments
typedef struct {
    uint64_t segment1_id;
    uint64_t segment2_id;
    double connection_confidence;
    double gap_distance;      // mm
    double angle_difference;  // degrees
    bool is_parallel;
    bool is_perpendicular;
    bool is_connected;
} arx_wall_connection_t;

// Wall structure composed of multiple segments
typedef struct {
    uint64_t id;
    arx_wall_segment_t* segments;
    uint32_t segment_count;
    uint32_t segment_capacity;
    arx_smart_point_3d_t start_point;
    arx_smart_point_3d_t end_point;
    double total_length;      // mm
    double max_height;        // mm
    double avg_thickness;     // mm
    double overall_confidence; // 0.0 - 1.0
    arx_validation_state_t validation_state;
    uint64_t arx_object_ids[32];  // Max 32 ArxObjects per structure
    uint8_t arx_object_count;
    char building_id[64];
    char floor_id[64];
    char room_id[64];
    arx_wall_type_t primary_wall_type;
    char notes[256];
    time_t created_at;
    time_t updated_at;
} arx_wall_structure_t;

// Curved wall segment with mathematical curve support
typedef struct {
    arx_wall_segment_t base;
    arx_curve_type_t curve_type;
    union {
        struct {
            double radius;        // mm
            double start_angle;   // radians
            double end_angle;     // radians
            arx_smart_point_3d_t center;
        } arc;
        struct {
            arx_smart_point_3d_t control1;
            arx_smart_point_3d_t control2;
            arx_smart_point_3d_t control3;  // For cubic Bézier
        } bezier;
    } curve_data;
    double curve_length;     // mm
    uint32_t approximation_points;  // Number of points for curve approximation
} arx_curved_wall_segment_t;

// Spatial index node for quadtree
typedef struct arx_quad_node {
    struct {
        int64_t min_x, min_y, max_x, max_y;
    } bounds;
    uint64_t* object_ids;
    uint32_t object_count;
    uint32_t object_capacity;
    struct arx_quad_node* children[4];
    bool is_leaf;
    uint8_t depth;
} arx_quad_node_t;

// Spatial index for efficient wall queries
typedef struct {
    arx_quad_node_t* root;
    uint32_t max_objects_per_node;
    uint8_t max_depth;
    uint64_t* object_lookup;  // Array of ArxObject IDs
    uint32_t object_count;
    uint32_t object_capacity;
} arx_spatial_index_t;

// Composition engine configuration
typedef struct {
    double max_gap_distance;      // mm
    double parallel_threshold;    // degrees
    double min_wall_length;       // mm
    double max_wall_length;       // mm
    double confidence_threshold;  // 0.0 - 1.0
    uint32_t max_curve_approximation_points;
    bool enable_curved_walls;
    bool enable_advanced_validation;
} arx_composition_config_t;

// =============================================================================
// CORE FUNCTIONS
// =============================================================================

// Smart Point 3D Operations
arx_smart_point_3d_t arx_smart_point_3d_new(int64_t x, int64_t y, int64_t z, arx_unit_t unit);
void arx_smart_point_3d_to_nanometers(const arx_smart_point_3d_t* point, int64_t* x, int64_t* y, int64_t* z);
void arx_smart_point_3d_to_millimeters(const arx_smart_point_3d_t* point, double* x, double* y, double* z);
void arx_smart_point_3d_to_meters(const arx_smart_point_3d_t* point, double* x, double* y, double* z);
double arx_smart_point_3d_distance(const arx_smart_point_3d_t* p1, const arx_smart_point_3d_t* p2);
bool arx_smart_point_3d_equals(const arx_smart_point_3d_t* p1, const arx_smart_point_3d_t* p2);

// Wall Segment Operations
arx_wall_segment_t* arx_wall_segment_new(void);
void arx_wall_segment_free(arx_wall_segment_t* segment);
void arx_wall_segment_set_points(arx_wall_segment_t* segment, 
                                const arx_smart_point_3d_t* start, 
                                const arx_smart_point_3d_t* end);
void arx_wall_segment_calculate_properties(arx_wall_segment_t* segment);
bool arx_wall_segment_add_arx_object(arx_wall_segment_t* segment, uint64_t arx_object_id);

// Curved Wall Segment Operations
arx_curved_wall_segment_t* arx_curved_wall_segment_new(void);
void arx_curved_wall_segment_free(arx_curved_wall_segment_t* segment);
void arx_curved_wall_segment_set_arc(arx_curved_wall_segment_t* segment,
                                    const arx_smart_point_3d_t* center,
                                    double radius, double start_angle, double end_angle);
void arx_curved_wall_segment_set_bezier_quadratic(arx_curved_wall_segment_t* segment,
                                                  const arx_smart_point_3d_t* control1,
                                                  const arx_smart_point_3d_t* control2);
void arx_curved_wall_segment_set_bezier_cubic(arx_curved_wall_segment_t* segment,
                                             const arx_smart_point_3d_t* control1,
                                             const arx_smart_point_3d_t* control2,
                                             const arx_smart_point_3d_t* control3);
void arx_curved_wall_segment_calculate_properties(arx_curved_wall_segment_t* segment);
arx_smart_point_3d_t* arx_curved_wall_segment_approximate_curve(const arx_curved_wall_segment_t* segment,
                                                                 uint32_t* point_count);

// Wall Structure Operations
arx_wall_structure_t* arx_wall_structure_new(void);
void arx_wall_structure_free(arx_wall_structure_t* structure);
bool arx_wall_structure_add_segment(arx_wall_structure_t* structure, 
                                   const arx_wall_segment_t* segment);
void arx_wall_structure_recalculate_properties(arx_wall_structure_t* structure);
double arx_wall_structure_get_total_length(const arx_wall_structure_t* structure);
double arx_wall_structure_get_max_height(const arx_wall_structure_t* structure);
double arx_wall_structure_get_overall_confidence(const arx_wall_structure_t* structure);

// Wall Connection Operations
arx_wall_connection_t* arx_wall_connection_new(uint64_t segment1_id, uint64_t segment2_id);
void arx_wall_connection_free(arx_wall_connection_t* connection);
void arx_wall_connection_calculate_properties(arx_wall_connection_t* connection,
                                            const arx_wall_segment_t* seg1,
                                            const arx_wall_segment_t* seg2);

// Spatial Index Operations
arx_spatial_index_t* arx_spatial_index_new(uint32_t max_objects_per_node, uint8_t max_depth);
void arx_spatial_index_free(arx_spatial_index_t* index);
void arx_spatial_index_clear(arx_spatial_index_t* index);
void arx_spatial_index_insert(arx_spatial_index_t* index, uint64_t object_id, 
                             const arx_smart_point_3d_t* point);
uint64_t* arx_spatial_index_query_nearby(const arx_spatial_index_t* index,
                                        const arx_smart_point_3d_t* point,
                                        double radius_mm,
                                        uint32_t* result_count);
uint64_t* arx_spatial_index_query_bounds(const arx_spatial_index_t* index,
                                        const arx_smart_point_3d_t* min_point,
                                        const arx_smart_point_3d_t* max_point,
                                        uint32_t* result_count);

// Wall Composition Engine
typedef struct arx_wall_composition_engine arx_wall_composition_engine_t;

arx_wall_composition_engine_t* arx_wall_composition_engine_new(const arx_composition_config_t* config);
void arx_wall_composition_engine_free(arx_wall_composition_engine_t* engine);

// Main composition function
arx_wall_structure_t** arx_wall_composition_engine_compose_walls(arx_wall_composition_engine_t* engine,
                                                                const arx_wall_segment_t* segments,
                                                                uint32_t segment_count,
                                                                uint32_t* structure_count);

// Wall detection and analysis
arx_wall_connection_t** arx_wall_composition_engine_detect_connections(arx_wall_composition_engine_t* engine,
                                                                      const arx_wall_segment_t* segments,
                                                                      uint32_t segment_count,
                                                                      uint32_t* connection_count);

// Validation and confidence scoring
void arx_wall_composition_engine_calculate_confidence(arx_wall_composition_engine_t* engine,
                                                     arx_wall_structure_t** structures,
                                                     uint32_t structure_count);
arx_wall_structure_t** arx_wall_composition_engine_filter_by_confidence(arx_wall_composition_engine_t* engine,
                                                                       const arx_wall_structure_t* const* structures,
                                                                       uint32_t structure_count,
                                                                       uint32_t* filtered_count);

// Utility functions
arx_composition_config_t arx_composition_config_default(void);
void arx_composition_config_set_advanced(arx_composition_config_t* config, bool enable);

// Memory management
void arx_wall_composition_free_structures(arx_wall_structure_t** structures, uint32_t count);
void arx_wall_composition_free_connections(arx_wall_connection_t** connections, uint32_t count);
void arx_wall_composition_free_points(arx_smart_point_3d_t* points);

#ifdef __cplusplus
}
#endif

#endif // ARX_WALL_COMPOSITION_H
