#include "arx_wall_composition.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>

// =============================================================================
// TEST HELPERS
// =============================================================================

#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("FAIL: %s\n", message); \
            return false; \
        } \
        printf("PASS: %s\n", message); \
    } while(0)

#define TEST_SECTION(name) \
    printf("\n=== %s ===\n", name)

// =============================================================================
// SMART POINT 3D TESTS
// =============================================================================

bool test_smart_point_3d_basic() {
    TEST_SECTION("Smart Point 3D Basic Operations");
    
    // Test creation with different units
    arx_smart_point_3d_t point1 = arx_smart_point_3d_new(1000, 2000, 3000, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t point2 = arx_smart_point_3d_new(1, 2, 3, ARX_UNIT_METER);
    
    // Test unit conversion
    int64_t x1, y1, z1;
    arx_smart_point_3d_to_nanometers(&point1, &x1, &y1, &z1);
    TEST_ASSERT(x1 == 1000000000, "Millimeter to nanometer conversion X");
    TEST_ASSERT(y1 == 2000000000, "Millimeter to nanometer conversion Y");
    TEST_ASSERT(z1 == 3000000000, "Millimeter to nanometer conversion Z");
    
    int64_t x2, y2, z2;
    arx_smart_point_3d_to_nanometers(&point2, &x2, &y2, &z2);
    TEST_ASSERT(x2 == 1000000000, "Meter to nanometer conversion X");
    TEST_ASSERT(y2 == 2000000000, "Meter to nanometer conversion Y");
    TEST_ASSERT(z2 == 3000000000, "Meter to nanometer conversion Z");
    
    // Test distance calculation
    double distance = arx_smart_point_3d_distance(&point1, &point2);
    TEST_ASSERT(distance == 0.0, "Distance between identical points should be 0");
    
    // Test equality
    TEST_ASSERT(arx_smart_point_3d_equals(&point1, &point2), "Points with same nanometer values should be equal");
    
    return true;
}

bool test_smart_point_3d_conversions() {
    TEST_SECTION("Smart Point 3D Unit Conversions");
    
    arx_smart_point_3d_t point = arx_smart_point_3d_new(1000, 2000, 3000, ARX_UNIT_MILLIMETER);
    
    // Test to millimeters
    double x_mm, y_mm, z_mm;
    arx_smart_point_3d_to_millimeters(&point, &x_mm, &y_mm, &z_mm);
    TEST_ASSERT(x_mm == 1000.0, "X coordinate in millimeters");
    TEST_ASSERT(y_mm == 2000.0, "Y coordinate in millimeters");
    TEST_ASSERT(z_mm == 3000.0, "Z coordinate in millimeters");
    
    // Test to meters
    double x_m, y_m, z_m;
    arx_smart_point_3d_to_meters(&point, &x_m, &y_m, &z_m);
    TEST_ASSERT(x_m == 1.0, "X coordinate in meters");
    TEST_ASSERT(y_m == 2.0, "Y coordinate in meters");
    TEST_ASSERT(z_m == 3.0, "Z coordinate in meters");
    
    return true;
}

// =============================================================================
// WALL SEGMENT TESTS
// =============================================================================

bool test_wall_segment_basic() {
    TEST_SECTION("Wall Segment Basic Operations");
    
    arx_wall_segment_t* segment = arx_wall_segment_new();
    TEST_ASSERT(segment != NULL, "Wall segment creation");
    TEST_ASSERT(segment->id == 0, "Initial ID should be 0");
    TEST_ASSERT(segment->length == 0.0, "Initial length should be 0");
    TEST_ASSERT(segment->confidence == 0.0, "Initial confidence should be 0");
    
    // Test setting points
    arx_smart_point_3d_t start = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(segment, &start, &end);
    TEST_ASSERT(segment->length == 1000.0, "Wall length calculation");
    TEST_ASSERT(segment->orientation == 0.0, "Horizontal wall orientation");
    
    // Test adding ArxObject
    TEST_ASSERT(arx_wall_segment_add_arx_object(segment, 12345), "Adding ArxObject");
    TEST_ASSERT(segment->arx_object_count == 1, "ArxObject count");
    TEST_ASSERT(segment->arx_object_ids[0] == 12345, "ArxObject ID storage");
    
    arx_wall_segment_free(segment);
    return true;
}

bool test_wall_segment_orientation() {
    TEST_SECTION("Wall Segment Orientation Calculation");
    
    arx_wall_segment_t* segment = arx_wall_segment_new();
    
    // Test vertical wall
    arx_smart_point_3d_t start = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end = arx_smart_point_3d_new(0, 1000, 0, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(segment, &start, &end);
    TEST_ASSERT(segment->orientation == 90.0, "Vertical wall orientation");
    
    // Test diagonal wall
    arx_smart_point_3d_t start2 = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end2 = arx_smart_point_3d_new(1000, 1000, 0, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(segment, &start2, &end2);
    TEST_ASSERT(segment->orientation == 45.0, "Diagonal wall orientation");
    
    arx_wall_segment_free(segment);
    return true;
}

// =============================================================================
// CURVED WALL SEGMENT TESTS
// =============================================================================

bool test_curved_wall_segment_arc() {
    TEST_SECTION("Curved Wall Segment Arc Operations");
    
    arx_curved_wall_segment_t* segment = arx_curved_wall_segment_new();
    TEST_ASSERT(segment != NULL, "Curved wall segment creation");
    
    // Test arc creation
    arx_smart_point_3d_t center = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    double radius = 1000.0; // 1m radius
    double start_angle = 0.0; // 0 degrees
    double end_angle = 90.0 * 3.14159265358979323846 / 180.0; // 90 degrees in radians
    
    arx_curved_wall_segment_set_arc(segment, &center, radius, start_angle, end_angle);
    TEST_ASSERT(segment->curve_type == ARX_CURVE_TYPE_ARC, "Arc curve type");
    TEST_ASSERT(segment->curve_data.arc.radius == radius, "Arc radius");
    TEST_ASSERT(segment->curve_length > 0, "Arc curve length calculation");
    
    // Test curve approximation
    uint32_t point_count;
    arx_smart_point_3d_t* points = arx_curved_wall_segment_approximate_curve(segment, &point_count);
    TEST_ASSERT(points != NULL, "Curve approximation points");
    TEST_ASSERT(point_count > 0, "Curve approximation point count");
    
    arx_wall_composition_free_points(points);
    arx_curved_wall_segment_free(segment);
    return true;
}

bool test_curved_wall_segment_bezier() {
    TEST_SECTION("Curved Wall Segment Bézier Operations");
    
    arx_curved_wall_segment_t* segment = arx_curved_wall_segment_new();
    
    // Test quadratic Bézier
    arx_smart_point_3d_t p0 = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t p1 = arx_smart_point_3d_new(500, 1000, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t p2 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    
    arx_curved_wall_segment_set_bezier_quadratic(segment, &p1, &p2);
    TEST_ASSERT(segment->curve_type == ARX_CURVE_TYPE_BEZIER_QUADRATIC, "Quadratic Bézier curve type");
    TEST_ASSERT(segment->curve_length > 0, "Quadratic Bézier curve length");
    
    // Test cubic Bézier
    arx_curved_wall_segment_t* segment2 = arx_curved_wall_segment_new();
    arx_smart_point_3d_t p3 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    
    arx_curved_wall_segment_set_bezier_cubic(segment2, &p1, &p2, &p3);
    TEST_ASSERT(segment2->curve_type == ARX_CURVE_TYPE_BEZIER_CUBIC, "Cubic Bézier curve type");
    TEST_ASSERT(segment2->curve_length > 0, "Cubic Bézier curve length");
    
    arx_curved_wall_segment_free(segment);
    arx_curved_wall_segment_free(segment2);
    return true;
}

// =============================================================================
// WALL STRUCTURE TESTS
// =============================================================================

bool test_wall_structure_basic() {
    TEST_SECTION("Wall Structure Basic Operations");
    
    arx_wall_structure_t* structure = arx_wall_structure_new();
    TEST_ASSERT(structure != NULL, "Wall structure creation");
    TEST_ASSERT(structure->segment_count == 0, "Initial segment count");
    TEST_ASSERT(structure->total_length == 0.0, "Initial total length");
    
    // Create and add segments
    arx_wall_segment_t* segment1 = arx_wall_segment_new();
    arx_wall_segment_t* segment2 = arx_wall_segment_new();
    
    arx_smart_point_3d_t start1 = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end1 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t start2 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end2 = arx_smart_point_3d_new(2000, 0, 0, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(segment1, &start1, &end1);
    arx_wall_segment_set_points(segment2, &start2, &end2);
    
    segment1->confidence = 0.8;
    segment2->confidence = 0.9;
    
    TEST_ASSERT(arx_wall_structure_add_segment(structure, segment1), "Adding first segment");
    TEST_ASSERT(arx_wall_structure_add_segment(structure, segment2), "Adding second segment");
    
    TEST_ASSERT(structure->segment_count == 2, "Segment count after addition");
    TEST_ASSERT(structure->total_length == 2000.0, "Total length calculation");
    TEST_ASSERT(structure->overall_confidence > 0.8, "Overall confidence calculation");
    
    arx_wall_segment_free(segment1);
    arx_wall_segment_free(segment2);
    arx_wall_structure_free(structure);
    return true;
}

// =============================================================================
// WALL CONNECTION TESTS
// =============================================================================

bool test_wall_connection_basic() {
    TEST_SECTION("Wall Connection Basic Operations");
    
    // Create two wall segments
    arx_wall_segment_t* seg1 = arx_wall_segment_new();
    arx_wall_segment_t* seg2 = arx_wall_segment_new();
    
    arx_smart_point_3d_t start1 = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end1 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t start2 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end2 = arx_smart_point_3d_new(2000, 0, 0, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(seg1, &start1, &end1);
    arx_wall_segment_set_points(seg2, &start2, &end2);
    
    // Create connection
    arx_wall_connection_t* connection = arx_wall_connection_new(1, 2);
    TEST_ASSERT(connection != NULL, "Wall connection creation");
    
    // Calculate connection properties
    arx_wall_connection_calculate_properties(connection, seg1, seg2);
    TEST_ASSERT(connection->is_connected, "Connected walls should be marked as connected");
    TEST_ASSERT(connection->gap_distance == 0.0, "Connected walls should have 0 gap");
    TEST_ASSERT(connection->is_parallel, "Parallel walls should be marked as parallel");
    
    arx_wall_segment_free(seg1);
    arx_wall_segment_free(seg2);
    arx_wall_connection_free(connection);
    return true;
}

// =============================================================================
// SPATIAL INDEX TESTS
// =============================================================================

bool test_spatial_index_basic() {
    TEST_SECTION("Spatial Index Basic Operations");
    
    arx_spatial_index_t* index = arx_spatial_index_new(10, 8);
    TEST_ASSERT(index != NULL, "Spatial index creation");
    
    // Insert objects
    arx_smart_point_3d_t point1 = arx_smart_point_3d_new(100, 100, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t point2 = arx_smart_point_3d_new(200, 200, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t point3 = arx_smart_point_3d_new(300, 300, 0, ARX_UNIT_MILLIMETER);
    
    arx_spatial_index_insert(index, 1, &point1);
    arx_spatial_index_insert(index, 2, &point2);
    arx_spatial_index_insert(index, 3, &point3);
    
    TEST_ASSERT(index->object_count == 3, "Object count after insertion");
    
    // Query nearby
    uint32_t result_count;
    uint64_t* results = arx_spatial_index_query_nearby(index, &point1, 1000.0, &result_count);
    TEST_ASSERT(results != NULL, "Nearby query results");
    TEST_ASSERT(result_count == 3, "Nearby query result count");
    
    free(results);
    arx_spatial_index_free(index);
    return true;
}

// =============================================================================
// WALL COMPOSITION ENGINE TESTS
// =============================================================================

bool test_wall_composition_engine_basic() {
    TEST_SECTION("Wall Composition Engine Basic Operations");
    
    arx_composition_config_t config = arx_composition_config_default();
    arx_wall_composition_engine_t* engine = arx_wall_composition_engine_new(&config);
    TEST_ASSERT(engine != NULL, "Composition engine creation");
    
    // Create test segments
    arx_wall_segment_t segments[3];
    arx_smart_point_3d_t start1 = arx_smart_point_3d_new(0, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end1 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t start2 = arx_smart_point_3d_new(1000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end2 = arx_smart_point_3d_new(2000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t start3 = arx_smart_point_3d_new(2000, 0, 0, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end3 = arx_smart_point_3d_new(3000, 0, 0, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(&segments[0], &start1, &end1);
    arx_wall_segment_set_points(&segments[1], &start2, &end2);
    arx_wall_segment_set_points(&segments[2], &start3, &end3);
    
    segments[0].id = 1;
    segments[1].id = 2;
    segments[2].id = 3;
    
    segments[0].confidence = 0.8;
    segments[1].confidence = 0.9;
    segments[2].confidence = 0.7;
    
    // Test wall composition
    uint32_t structure_count;
    arx_wall_structure_t** structures = arx_wall_composition_engine_compose_walls(engine, segments, 3, &structure_count);
    TEST_ASSERT(structures != NULL, "Wall composition results");
    TEST_ASSERT(structure_count == 3, "Structure count");
    
    // Test connection detection
    uint32_t connection_count;
    arx_wall_connection_t** connections = arx_wall_composition_engine_detect_connections(engine, segments, 3, &connection_count);
    TEST_ASSERT(connections != NULL, "Connection detection results");
    TEST_ASSERT(connection_count == 2, "Connection count");
    
    // Cleanup
    arx_wall_composition_free_structures(structures, structure_count);
    arx_wall_composition_free_connections(connections, connection_count);
    arx_wall_composition_engine_free(engine);
    
    return true;
}

// =============================================================================
// PERFORMANCE TESTS
// =============================================================================

bool test_performance_large_structures() {
    TEST_SECTION("Performance - Large Wall Structures");
    
    arx_composition_config_t config = arx_composition_config_default();
    arx_wall_composition_engine_t* engine = arx_wall_composition_engine_new(&config);
    
    const uint32_t num_segments = 1000;
    arx_wall_segment_t* segments = malloc(num_segments * sizeof(arx_wall_segment_t));
    
    // Create a large number of wall segments
    for (uint32_t i = 0; i < num_segments; i++) {
        arx_smart_point_3d_t start = arx_smart_point_3d_new(i * 1000, 0, 0, ARX_UNIT_MILLIMETER);
        arx_smart_point_3d_t end = arx_smart_point_3d_new((i + 1) * 1000, 0, 0, ARX_UNIT_MILLIMETER);
        
        arx_wall_segment_set_points(&segments[i], &start, &end);
        segments[i].id = i;
        segments[i].confidence = 0.8;
    }
    
    // Measure composition time
    clock_t start_time = clock();
    
    uint32_t structure_count;
    arx_wall_structure_t** structures = arx_wall_composition_engine_compose_walls(engine, segments, num_segments, &structure_count);
    
    clock_t end_time = clock();
    double elapsed = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;
    
    printf("Performance: Composed %d segments in %.6f seconds (%.0f segments/second)\n", 
           num_segments, elapsed, num_segments / elapsed);
    
    TEST_ASSERT(structures != NULL, "Large structure composition");
    TEST_ASSERT(structure_count == num_segments, "Large structure count");
    
    // Cleanup
    arx_wall_composition_free_structures(structures, structure_count);
    free(segments);
    arx_wall_composition_engine_free(engine);
    
    return true;
}

// =============================================================================
// MAIN TEST RUNNER
// =============================================================================

int main() {
    printf("ARX Wall Composition System - C Core Tests\n");
    printf("==========================================\n");
    
    bool all_tests_passed = true;
    
    // Run all test suites
    all_tests_passed &= test_smart_point_3d_basic();
    all_tests_passed &= test_smart_point_3d_conversions();
    all_tests_passed &= test_wall_segment_basic();
    all_tests_passed &= test_wall_segment_orientation();
    all_tests_passed &= test_curved_wall_segment_arc();
    all_tests_passed &= test_curved_wall_segment_bezier();
    all_tests_passed &= test_wall_structure_basic();
    all_tests_passed &= test_wall_connection_basic();
    all_tests_passed &= test_spatial_index_basic();
    all_tests_passed &= test_wall_composition_engine_basic();
    all_tests_passed &= test_performance_large_structures();
    
    printf("\n==========================================\n");
    if (all_tests_passed) {
        printf("ALL TESTS PASSED! ✅\n");
        printf("C Core Wall Composition System is ready for production!\n");
        return 0;
    } else {
        printf("SOME TESTS FAILED! ❌\n");
        printf("Please review and fix the failing tests.\n");
        return 1;
    }
}
