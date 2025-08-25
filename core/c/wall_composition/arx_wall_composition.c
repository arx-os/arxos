#include "arx_wall_composition.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>

// =============================================================================
// CONSTANTS AND HELPER FUNCTIONS
// =============================================================================

// Conversion factors (compile-time constants)
static const double CONVERSION_FACTORS[] = {
    1.0,           // Nanometer
    1e3,           // Micrometer
    1e6,           // Millimeter
    1e7,           // Centimeter
    1e9,           // Meter
    2.54e7,        // Inch
    3.048e8        // Foot
};

// Mathematical constants
#define PI 3.14159265358979323846
#define DEG_TO_RAD (PI / 180.0)
#define RAD_TO_DEG (180.0 / PI)

// Helper function to convert units to nanometers
static int64_t convert_to_nanometers(int64_t value, arx_unit_t unit) {
    if (unit >= 0 && unit <= ARX_UNIT_FOOT) {
        return (int64_t)(value * CONVERSION_FACTORS[unit]);
    }
    return value; // Default to no conversion
}

// Helper function to convert from nanometers to target unit
static double convert_from_nanometers(int64_t nanometers, arx_unit_t unit) {
    if (unit >= 0 && unit <= ARX_UNIT_FOOT) {
        return (double)nanometers / CONVERSION_FACTORS[unit];
    }
    return (double)nanometers;
}

// =============================================================================
// SMART POINT 3D IMPLEMENTATION
// =============================================================================

arx_smart_point_3d_t arx_smart_point_3d_new(int64_t x, int64_t y, int64_t z, arx_unit_t unit) {
    arx_smart_point_3d_t point;
    point.x = convert_to_nanometers(x, unit);
    point.y = convert_to_nanometers(y, unit);
    point.z = convert_to_nanometers(z, unit);
    point.unit = unit;
    return point;
}

void arx_smart_point_3d_to_nanometers(const arx_smart_point_3d_t* point, int64_t* x, int64_t* y, int64_t* z) {
    if (point && x && y && z) {
        *x = point->x;
        *y = point->y;
        *z = point->z;
    }
}

void arx_smart_point_3d_to_millimeters(const arx_smart_point_3d_t* point, double* x, double* y, double* z) {
    if (point && x && y && z) {
        *x = convert_from_nanometers(point->x, ARX_UNIT_MILLIMETER);
        *y = convert_from_nanometers(point->y, ARX_UNIT_MILLIMETER);
        *z = convert_from_nanometers(point->z, ARX_UNIT_MILLIMETER);
    }
}

void arx_smart_point_3d_to_meters(const arx_smart_point_3d_t* point, double* x, double* y, double* z) {
    if (point && x && y && z) {
        *x = convert_from_nanometers(point->x, ARX_UNIT_METER);
        *y = convert_from_nanometers(point->y, ARX_UNIT_METER);
        *z = convert_from_nanometers(point->z, ARX_UNIT_METER);
    }
}

double arx_smart_point_3d_distance(const arx_smart_point_3d_t* p1, const arx_smart_point_3d_t* p2) {
    if (!p1 || !p2) return 0.0;
    
    int64_t dx = p1->x - p2->x;
    int64_t dy = p1->y - p2->y;
    int64_t dz = p1->z - p2->z;
    
    double distance_nm = sqrt((double)(dx * dx + dy * dy + dz * dz));
    return convert_from_nanometers((int64_t)distance_nm, ARX_UNIT_MILLIMETER);
}

bool arx_smart_point_3d_equals(const arx_smart_point_3d_t* p1, const arx_smart_point_3d_t* p2) {
    if (!p1 || !p2) return false;
    return p1->x == p2->x && p1->y == p2->y && p1->z == p2->z && p1->unit == p2->unit;
}

// =============================================================================
// WALL SEGMENT IMPLEMENTATION
// =============================================================================

arx_wall_segment_t* arx_wall_segment_new(void) {
    arx_wall_segment_t* segment = (arx_wall_segment_t*)malloc(sizeof(arx_wall_segment_t));
    if (segment) {
        memset(segment, 0, sizeof(arx_wall_segment_t));
        segment->id = 0;
        segment->length = 0.0;
        segment->height = 0.0;
        segment->thickness = 0.0;
        segment->confidence = 0.0;
        segment->orientation = 0.0;
        segment->wall_type = ARX_WALL_TYPE_INTERIOR;
        segment->arx_object_count = 0;
        segment->created_at = time(NULL);
    }
    return segment;
}

void arx_wall_segment_free(arx_wall_segment_t* segment) {
    if (segment) {
        free(segment);
    }
}

void arx_wall_segment_set_points(arx_wall_segment_t* segment, 
                                const arx_smart_point_3d_t* start, 
                                const arx_smart_point_3d_t* end) {
    if (segment && start && end) {
        segment->start_point = *start;
        segment->end_point = *end;
        arx_wall_segment_calculate_properties(segment);
    }
}

void arx_wall_segment_calculate_properties(arx_wall_segment_t* segment) {
    if (!segment) return;
    
    // Calculate length
    segment->length = arx_smart_point_3d_distance(&segment->start_point, &segment->end_point);
    
    // Calculate orientation (angle from horizontal)
    if (segment->length > 0.0) {
        int64_t dx = segment->end_point.x - segment->start_point.x;
        int64_t dy = segment->end_point.y - segment->start_point.y;
        double angle_rad = atan2((double)dy, (double)dx);
        segment->orientation = angle_rad * RAD_TO_DEG;
        
        // Normalize to 0-360 degrees
        if (segment->orientation < 0) {
            segment->orientation += 360.0;
        }
    }
}

bool arx_wall_segment_add_arx_object(arx_wall_segment_t* segment, uint64_t arx_object_id) {
    if (!segment || segment->arx_object_count >= 16) return false;
    
    segment->arx_object_ids[segment->arx_object_count] = arx_object_id;
    segment->arx_object_count++;
    return true;
}

// =============================================================================
// CURVED WALL SEGMENT IMPLEMENTATION
// =============================================================================

arx_curved_wall_segment_t* arx_curved_wall_segment_new(void) {
    arx_curved_wall_segment_t* segment = (arx_curved_wall_segment_t*)malloc(sizeof(arx_curved_wall_segment_t));
    if (segment) {
        memset(segment, 0, sizeof(arx_curved_wall_segment_t));
        segment->base.id = 0;
        segment->curve_type = ARX_CURVE_TYPE_LINEAR;
        segment->curve_length = 0.0;
        segment->approximation_points = 32; // Default approximation
        segment->base.created_at = time(NULL);
    }
    return segment;
}

void arx_curved_wall_segment_free(arx_curved_wall_segment_t* segment) {
    if (segment) {
        free(segment);
    }
}

void arx_curved_wall_segment_set_arc(arx_curved_wall_segment_t* segment,
                                    const arx_smart_point_3d_t* center,
                                    double radius, double start_angle, double end_angle) {
    if (!segment || !center) return;
    
    segment->curve_type = ARX_CURVE_TYPE_ARC;
    segment->curve_data.arc.center = *center;
    segment->curve_data.arc.radius = radius;
    segment->curve_data.arc.start_angle = start_angle;
    segment->curve_data.arc.end_angle = end_angle;
    
    // Calculate curve length
    double angle_diff = fabs(end_angle - start_angle);
    if (angle_diff > 2 * PI) angle_diff = 2 * PI;
    segment->curve_length = radius * angle_diff;
    
    // Set base segment points (approximate start and end)
    double start_rad = start_angle;
    double end_rad = end_angle;
    
    segment->base.start_point.x = center->x + (int64_t)(radius * cos(start_rad));
    segment->base.start_point.y = center->y + (int64_t)(radius * sin(start_rad));
    segment->base.start_point.z = center->z;
    segment->base.start_point.unit = center->unit;
    
    segment->base.end_point.x = center->x + (int64_t)(radius * cos(end_rad));
    segment->base.end_point.y = center->y + (int64_t)(radius * sin(end_rad));
    segment->base.end_point.z = center->z;
    segment->base.end_point.unit = center->unit;
    
    arx_wall_segment_calculate_properties(&segment->base);
}

void arx_curved_wall_segment_set_bezier_quadratic(arx_curved_wall_segment_t* segment,
                                                  const arx_smart_point_3d_t* control1,
                                                  const arx_smart_point_3d_t* control2) {
    if (!segment || !control1 || !control2) return;
    
    segment->curve_type = ARX_CURVE_TYPE_BEZIER_QUADRATIC;
    segment->curve_data.bezier.control1 = *control1;
    segment->curve_data.bezier.control2 = *control2;
    
    // Set base segment points
    segment->base.start_point = *control1;
    segment->base.end_point = *control2;
    
    // Calculate approximate curve length using control points
    double dx = (double)(control2->x - control1->x);
    double dy = (double)(control2->y - control1->y);
    double dz = (double)(control2->z - control1->z);
    segment->curve_length = sqrt(dx*dx + dy*dy + dz*dz) / 1e6; // Convert to mm
    
    arx_wall_segment_calculate_properties(&segment->base);
}

void arx_curved_wall_segment_set_bezier_cubic(arx_curved_wall_segment_t* segment,
                                             const arx_smart_point_3d_t* control1,
                                             const arx_smart_point_3d_t* control2,
                                             const arx_smart_point_3d_t* control3) {
    if (!segment || !control1 || !control2 || !control3) return;
    
    segment->curve_type = ARX_CURVE_TYPE_BEZIER_CUBIC;
    segment->curve_data.bezier.control1 = *control1;
    segment->curve_data.bezier.control2 = *control2;
    segment->curve_data.bezier.control3 = *control3;
    
    // Set base segment points
    segment->base.start_point = *control1;
    segment->base.end_point = *control3;
    
    // Calculate approximate curve length using control points
    double dx1 = (double)(control2->x - control1->x);
    double dy1 = (double)(control2->y - control1->y);
    double dz1 = (double)(control2->z - control1->z);
    double dx2 = (double)(control3->x - control2->x);
    double dy2 = (double)(control3->y - control2->y);
    double dz2 = (double)(control3->z - control2->z);
    
    double len1 = sqrt(dx1*dx1 + dy1*dy1 + dz1*dz1);
    double len2 = sqrt(dx2*dx2 + dy2*dy2 + dz2*dz2);
    segment->curve_length = (len1 + len2) / 1e6; // Convert to mm
    
    arx_wall_segment_calculate_properties(&segment->base);
}

void arx_curved_wall_segment_calculate_properties(arx_curved_wall_segment_t* segment) {
    if (!segment) return;
    
    // Calculate base properties
    arx_wall_segment_calculate_properties(&segment->base);
    
    // Update curve-specific properties
    switch (segment->curve_type) {
        case ARX_CURVE_TYPE_ARC:
            // Arc properties already calculated in set_arc
            break;
        case ARX_CURVE_TYPE_BEZIER_QUADRATIC:
        case ARX_CURVE_TYPE_BEZIER_CUBIC:
            // Bézier properties already calculated in set_bezier functions
            break;
        default:
            segment->curve_length = segment->base.length;
            break;
    }
}

arx_smart_point_3d_t* arx_curved_wall_segment_approximate_curve(const arx_curved_wall_segment_t* segment,
                                                                 uint32_t* point_count) {
    if (!segment || !point_count) return NULL;
    
    uint32_t num_points = segment->approximation_points;
    if (num_points < 2) num_points = 2;
    
    arx_smart_point_3d_t* points = (arx_smart_point_3d_t*)malloc(num_points * sizeof(arx_smart_point_3d_t));
    if (!points) return NULL;
    
    *point_count = num_points;
    
    switch (segment->curve_type) {
        case ARX_CURVE_TYPE_ARC: {
            double start_angle = segment->curve_data.arc.start_angle;
            double end_angle = segment->curve_data.arc.end_angle;
            double radius = segment->curve_data.arc.radius;
            const arx_smart_point_3d_t* center = &segment->curve_data.arc.center;
            
            for (uint32_t i = 0; i < num_points; i++) {
                double t = (double)i / (double)(num_points - 1);
                double angle = start_angle + t * (end_angle - start_angle);
                
                points[i].x = center->x + (int64_t)(radius * cos(angle));
                points[i].y = center->y + (int64_t)(radius * sin(angle));
                points[i].z = center->z;
                points[i].unit = center->unit;
            }
            break;
        }
        
        case ARX_CURVE_TYPE_BEZIER_QUADRATIC: {
            const arx_smart_point_3d_t* p0 = &segment->base.start_point;
            const arx_smart_point_3d_t* p1 = &segment->curve_data.bezier.control1;
            const arx_smart_point_3d_t* p2 = &segment->base.end_point;
            
            for (uint32_t i = 0; i < num_points; i++) {
                double t = (double)i / (double)(num_points - 1);
                double u = 1.0 - t;
                
                // Quadratic Bézier: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
                points[i].x = (int64_t)(u*u * p0->x + 2*u*t * p1->x + t*t * p2->x);
                points[i].y = (int64_t)(u*u * p0->y + 2*u*t * p1->y + t*t * p2->y);
                points[i].z = (int64_t)(u*u * p0->z + 2*u*t * p1->z + t*t * p2->z);
                points[i].unit = p0->unit;
            }
            break;
        }
        
        case ARX_CURVE_TYPE_BEZIER_CUBIC: {
            const arx_smart_point_3d_t* p0 = &segment->base.start_point;
            const arx_smart_point_3d_t* p1 = &segment->curve_data.bezier.control1;
            const arx_smart_point_3d_t* p2 = &segment->curve_data.bezier.control2;
            const arx_smart_point_3d_t* p3 = &segment->base.end_point;
            
            for (uint32_t i = 0; i < num_points; i++) {
                double t = (double)i / (double)(num_points - 1);
                double u = 1.0 - t;
                
                // Cubic Bézier: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
                points[i].x = (int64_t)(u*u*u * p0->x + 3*u*u*t * p1->x + 3*u*t*t * p2->x + t*t*t * p3->x);
                points[i].y = (int64_t)(u*u*u * p0->y + 3*u*u*t * p1->y + 3*u*t*t * p2->y + t*t*t * p3->y);
                points[i].z = (int64_t)(u*u*u * p0->z + 3*u*u*t * p1->z + 3*u*t*t * p2->z + t*t*t * p3->z);
                points[i].unit = p0->unit;
            }
            break;
        }
        
        default:
            // Linear - just return start and end points
            points[0] = segment->base.start_point;
            if (num_points > 1) {
                points[num_points - 1] = segment->base.end_point;
            }
            break;
    }
    
    return points;
}

// =============================================================================
// WALL STRUCTURE IMPLEMENTATION
// =============================================================================

arx_wall_structure_t* arx_wall_structure_new(void) {
    arx_wall_structure_t* structure = (arx_wall_structure_t*)malloc(sizeof(arx_wall_structure_t));
    if (structure) {
        memset(structure, 0, sizeof(arx_wall_structure_t));
        structure->id = 0;
        structure->segments = NULL;
        structure->segment_count = 0;
        structure->segment_capacity = 0;
        structure->total_length = 0.0;
        structure->max_height = 0.0;
        structure->avg_thickness = 0.0;
        structure->overall_confidence = 0.0;
        structure->validation_state = ARX_VALIDATION_PENDING;
        structure->arx_object_count = 0;
        structure->primary_wall_type = ARX_WALL_TYPE_INTERIOR;
        structure->created_at = time(NULL);
        structure->updated_at = time(NULL);
    }
    return structure;
}

void arx_wall_structure_free(arx_wall_structure_t* structure) {
    if (structure) {
        if (structure->segments) {
            free(structure->segments);
        }
        free(structure);
    }
}

bool arx_wall_structure_add_segment(arx_wall_structure_t* structure, 
                                   const arx_wall_segment_t* segment) {
    if (!structure || !segment) return false;
    
    // Expand capacity if needed
    if (structure->segment_count >= structure->segment_capacity) {
        uint32_t new_capacity = structure->segment_capacity == 0 ? 4 : structure->segment_capacity * 2;
        arx_wall_segment_t* new_segments = (arx_wall_segment_t*)realloc(structure->segments, 
                                                                       new_capacity * sizeof(arx_wall_segment_t));
        if (!new_segments) return false;
        
        structure->segments = new_segments;
        structure->segment_capacity = new_capacity;
    }
    
    // Add segment
    structure->segments[structure->segment_count] = *segment;
    structure->segment_count++;
    
    // Recalculate properties
    arx_wall_structure_recalculate_properties(structure);
    
    return true;
}

void arx_wall_structure_recalculate_properties(arx_wall_structure_t* structure) {
    if (!structure || structure->segment_count == 0) return;
    
    // Calculate total length
    structure->total_length = 0.0;
    structure->max_height = 0.0;
    double total_thickness = 0.0;
    double weighted_confidence = 0.0;
    double total_weight = 0.0;
    
    // Find extreme points
    int64_t min_x = structure->segments[0].start_point.x;
    int64_t min_y = structure->segments[0].start_point.y;
    int64_t max_x = structure->segments[0].start_point.x;
    int64_t max_y = structure->segments[0].start_point.y;
    
    for (uint32_t i = 0; i < structure->segment_count; i++) {
        const arx_wall_segment_t* segment = &structure->segments[i];
        
        // Accumulate properties
        structure->total_length += segment->length;
        if (segment->height > structure->max_height) {
            structure->max_height = segment->height;
        }
        total_thickness += segment->thickness;
        
        // Weight confidence by segment length
        weighted_confidence += segment->confidence * segment->length;
        total_weight += segment->length;
        
        // Update extreme points
        if (segment->start_point.x < min_x) min_x = segment->start_point.x;
        if (segment->start_point.x > max_x) max_x = segment->start_point.x;
        if (segment->start_point.y < min_y) min_y = segment->start_point.y;
        if (segment->start_point.y > max_y) max_y = segment->start_point.y;
        
        if (segment->end_point.x < min_x) min_x = segment->end_point.x;
        if (segment->end_point.x > max_x) max_x = segment->end_point.x;
        if (segment->end_point.y < min_y) min_y = segment->end_point.y;
        if (segment->end_point.y > max_y) max_y = segment->end_point.y;
    }
    
    // Calculate averages
    structure->avg_thickness = total_thickness / structure->segment_count;
    structure->overall_confidence = total_weight > 0.0 ? (float)(weighted_confidence / total_weight) : 0.0f;
    
    // Update bounding box
    structure->start_point.x = min_x;
    structure->start_point.y = min_y;
    structure->start_point.z = structure->segments[0].start_point.z;
    structure->start_point.unit = structure->segments[0].start_point.unit;
    
    structure->end_point.x = max_x;
    structure->end_point.y = max_y;
    structure->end_point.z = structure->segments[0].start_point.z;
    structure->end_point.unit = structure->segments[0].start_point.unit;
    
    structure->updated_at = time(NULL);
}

double arx_wall_structure_get_total_length(const arx_wall_structure_t* structure) {
    return structure ? structure->total_length : 0.0;
}

double arx_wall_structure_get_max_height(const arx_wall_structure_t* structure) {
    return structure ? structure->max_height : 0.0;
}

double arx_wall_structure_get_overall_confidence(const arx_wall_structure_t* structure) {
    return structure ? structure->overall_confidence : 0.0;
}

// =============================================================================
// WALL CONNECTION IMPLEMENTATION
// =============================================================================

arx_wall_connection_t* arx_wall_connection_new(uint64_t segment1_id, uint64_t segment2_id) {
    arx_wall_connection_t* connection = (arx_wall_connection_t*)malloc(sizeof(arx_wall_connection_t));
    if (connection) {
        connection->segment1_id = segment1_id;
        connection->segment2_id = segment2_id;
        connection->connection_confidence = 0.0;
        connection->gap_distance = 0.0;
        connection->angle_difference = 0.0;
        connection->is_parallel = false;
        connection->is_perpendicular = false;
        connection->is_connected = false;
    }
    return connection;
}

void arx_wall_connection_free(arx_wall_connection_t* connection) {
    if (connection) {
        free(connection);
    }
}

void arx_wall_connection_calculate_properties(arx_wall_connection_t* connection,
                                            const arx_wall_segment_t* seg1,
                                            const arx_wall_segment_t* seg2) {
    if (!connection || !seg1 || !seg2) return;
    
    // Calculate gap distance between wall endpoints
    double min_distance = INFINITY;
    
    // Check all endpoint combinations
    double dist1 = arx_smart_point_3d_distance(&seg1->start_point, &seg2->start_point);
    double dist2 = arx_smart_point_3d_distance(&seg1->start_point, &seg2->end_point);
    double dist3 = arx_smart_point_3d_distance(&seg1->end_point, &seg2->start_point);
    double dist4 = arx_smart_point_3d_distance(&seg1->end_point, &seg2->end_point);
    
    min_distance = fmin(fmin(dist1, dist2), fmin(dist3, dist4));
    connection->gap_distance = min_distance;
    
    // Calculate angle difference
    double angle_diff = fabs(seg1->orientation - seg2->orientation);
    if (angle_diff > 180.0) {
        angle_diff = 360.0 - angle_diff;
    }
    connection->angle_difference = angle_diff;
    
    // Determine connection type
    connection->is_parallel = angle_diff < 5.0; // 5 degree tolerance
    connection->is_perpendicular = fabs(angle_diff - 90.0) < 5.0; // 5 degree tolerance
    connection->is_connected = min_distance < 50.0; // 50mm tolerance
    
    // Calculate connection confidence based on alignment and proximity
    double angle_confidence = 1.0 - (angle_diff / 180.0);
    double distance_confidence = 1.0 - (min_distance / 1000.0); // 1m max distance
    if (distance_confidence < 0.0) distance_confidence = 0.0;
    
    connection->connection_confidence = (angle_confidence + distance_confidence) / 2.0;
}

// =============================================================================
// SPATIAL INDEX IMPLEMENTATION (QUADTREE)
// =============================================================================

arx_spatial_index_t* arx_spatial_index_new(uint32_t max_objects_per_node, uint8_t max_depth) {
    arx_spatial_index_t* index = (arx_spatial_index_t*)malloc(sizeof(arx_spatial_index_t));
    if (index) {
        index->root = NULL;
        index->max_objects_per_node = max_objects_per_node;
        index->max_depth = max_depth;
        index->object_lookup = NULL;
        index->object_count = 0;
        index->object_capacity = 0;
    }
    return index;
}

void arx_spatial_index_free(arx_spatial_index_t* index) {
    if (index) {
        // TODO: Implement recursive quadtree cleanup
        if (index->object_lookup) {
            free(index->object_lookup);
        }
        free(index);
    }
}

void arx_spatial_index_clear(arx_spatial_index_t* index) {
    if (index) {
        // TODO: Implement recursive quadtree cleanup
        index->root = NULL;
        index->object_count = 0;
    }
}

void arx_spatial_index_insert(arx_spatial_index_t* index, uint64_t object_id, 
                             const arx_smart_point_3d_t* point) {
    if (!index || !point) return;
    
    // TODO: Implement quadtree insertion
    // For now, just store in object lookup
    if (index->object_count >= index->object_capacity) {
        uint32_t new_capacity = index->object_capacity == 0 ? 16 : index->object_capacity * 2;
        uint64_t* new_lookup = (uint64_t*)realloc(index->object_lookup, new_capacity * sizeof(uint64_t));
        if (!new_lookup) return;
        
        index->object_lookup = new_lookup;
        index->object_capacity = new_capacity;
    }
    
    index->object_lookup[index->object_count] = object_id;
    index->object_count++;
}

uint64_t* arx_spatial_index_query_nearby(const arx_spatial_index_t* index,
                                        const arx_smart_point_3d_t* point,
                                        double radius_mm,
                                        uint32_t* result_count) {
    if (!index || !point || !result_count) return NULL;
    
    // TODO: Implement quadtree query
    // For now, return all objects (inefficient but functional)
    *result_count = index->object_count;
    
    if (index->object_count == 0) return NULL;
    
    uint64_t* results = (uint64_t*)malloc(index->object_count * sizeof(uint64_t));
    if (results) {
        memcpy(results, index->object_lookup, index->object_count * sizeof(uint64_t));
    }
    
    return results;
}

uint64_t* arx_spatial_index_query_bounds(const arx_spatial_index_t* index,
                                        const arx_smart_point_3d_t* min_point,
                                        const arx_smart_point_3d_t* max_point,
                                        uint32_t* result_count) {
    if (!index || !min_point || !max_point || !result_count) return NULL;
    
    // TODO: Implement quadtree bounds query
    // For now, return all objects (inefficient but functional)
    *result_count = index->object_count;
    
    if (index->object_count == 0) return NULL;
    
    uint64_t* results = (uint64_t*)malloc(index->object_count * sizeof(uint64_t));
    if (results) {
        memcpy(results, index->object_lookup, index->object_count * sizeof(uint64_t));
    }
    
    return results;
}

// =============================================================================
// WALL COMPOSITION ENGINE IMPLEMENTATION
// =============================================================================

// Forward declaration of the engine structure
struct arx_wall_composition_engine {
    arx_spatial_index_t* spatial_index;
    arx_composition_config_t config;
};

arx_wall_composition_engine_t* arx_wall_composition_engine_new(const arx_composition_config_t* config) {
    arx_wall_composition_engine_t* engine = (arx_wall_composition_engine_t*)malloc(sizeof(arx_wall_composition_engine_t));
    if (engine) {
        engine->spatial_index = arx_spatial_index_new(10, 8);
        if (config) {
            engine->config = *config;
        } else {
            engine->config = arx_composition_config_default();
        }
    }
    return engine;
}

void arx_wall_composition_engine_free(arx_wall_composition_engine_t* engine) {
    if (engine) {
        if (engine->spatial_index) {
            arx_spatial_index_free(engine->spatial_index);
        }
        free(engine);
    }
}

arx_wall_structure_t** arx_wall_composition_engine_compose_walls(arx_wall_composition_engine_t* engine,
                                                                const arx_wall_segment_t* segments,
                                                                uint32_t segment_count,
                                                                uint32_t* structure_count) {
    if (!engine || !segments || !structure_count) return NULL;
    
    // TODO: Implement full wall composition algorithm
    // For now, create one structure per segment
    *structure_count = segment_count;
    
    if (segment_count == 0) return NULL;
    
    arx_wall_structure_t** structures = (arx_wall_structure_t**)malloc(segment_count * sizeof(arx_wall_structure_t*));
    if (!structures) return NULL;
    
    for (uint32_t i = 0; i < segment_count; i++) {
        structures[i] = arx_wall_structure_new();
        if (structures[i]) {
            arx_wall_structure_add_segment(structures[i], &segments[i]);
        }
    }
    
    return structures;
}

arx_wall_connection_t** arx_wall_composition_engine_detect_connections(arx_wall_composition_engine_t* engine,
                                                                      const arx_wall_segment_t* segments,
                                                                      uint32_t segment_count,
                                                                      uint32_t* connection_count) {
    if (!engine || !segments || !connection_count) return NULL;
    
    // TODO: Implement connection detection algorithm
    // For now, create connections between adjacent segments
    *connection_count = segment_count > 1 ? segment_count - 1 : 0;
    
    if (*connection_count == 0) return NULL;
    
    arx_wall_connection_t** connections = (arx_wall_connection_t**)malloc(*connection_count * sizeof(arx_wall_connection_t*));
    if (!connections) return NULL;
    
    for (uint32_t i = 0; i < *connection_count; i++) {
        connections[i] = arx_wall_connection_new(segments[i].id, segments[i + 1].id);
        if (connections[i]) {
            arx_wall_connection_calculate_properties(connections[i], &segments[i], &segments[i + 1]);
        }
    }
    
    return connections;
}

void arx_wall_composition_engine_calculate_confidence(arx_wall_composition_engine_t* engine,
                                                     arx_wall_structure_t** structures,
                                                     uint32_t structure_count) {
    if (!engine || !structures) return;
    
    for (uint32_t i = 0; i < structure_count; i++) {
        if (structures[i]) {
            arx_wall_structure_recalculate_properties(structures[i]);
        }
    }
}

arx_wall_structure_t** arx_wall_composition_engine_filter_by_confidence(arx_wall_composition_engine_t* engine,
                                                                       const arx_wall_structure_t* const* structures,
                                                                       uint32_t structure_count,
                                                                       uint32_t* filtered_count) {
    if (!engine || !structures || !filtered_count) return NULL;
    
    // Count structures above confidence threshold
    uint32_t count = 0;
    for (uint32_t i = 0; i < structure_count; i++) {
        if (structures[i] && structures[i]->overall_confidence >= engine->config.confidence_threshold) {
            count++;
        }
    }
    
    *filtered_count = count;
    
    if (count == 0) return NULL;
    
    // Create filtered array
    arx_wall_structure_t** filtered = (arx_wall_structure_t**)malloc(count * sizeof(arx_wall_structure_t*));
    if (!filtered) return NULL;
    
    uint32_t j = 0;
    for (uint32_t i = 0; i < structure_count; i++) {
        if (structures[i] && structures[i]->overall_confidence >= engine->config.confidence_threshold) {
            filtered[j++] = (arx_wall_structure_t*)structures[i];
        }
    }
    
    return filtered;
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

arx_composition_config_t arx_composition_config_default(void) {
    arx_composition_config_t config;
    config.max_gap_distance = 50.0;           // 50mm gap tolerance
    config.parallel_threshold = 5.0;          // 5 degrees tolerance for parallel walls
    config.min_wall_length = 100.0;           // 100mm minimum wall length
    config.max_wall_length = 50000.0;         // 50m maximum wall length
    config.confidence_threshold = 0.6;        // 60% confidence threshold
    config.max_curve_approximation_points = 32;
    config.enable_curved_walls = true;
    config.enable_advanced_validation = false;
    return config;
}

void arx_composition_config_set_advanced(arx_composition_config_t* config, bool enable) {
    if (config) {
        config->enable_advanced_validation = enable;
        if (enable) {
            config->max_curve_approximation_points = 64;
        } else {
            config->max_curve_approximation_points = 32;
        }
    }
}

// =============================================================================
// MEMORY MANAGEMENT
// =============================================================================

void arx_wall_composition_free_structures(arx_wall_structure_t** structures, uint32_t count) {
    if (structures) {
        for (uint32_t i = 0; i < count; i++) {
            if (structures[i]) {
                arx_wall_structure_free(structures[i]);
            }
        }
        free(structures);
    }
}

void arx_wall_composition_free_connections(arx_wall_connection_t** connections, uint32_t count) {
    if (connections) {
        for (uint32_t i = 0; i < count; i++) {
            if (connections[i]) {
                arx_wall_connection_free(connections[i]);
            }
        }
        free(connections);
    }
}

void arx_wall_composition_free_points(arx_smart_point_3d_t* points) {
    if (points) {
        free(points);
    }
}
