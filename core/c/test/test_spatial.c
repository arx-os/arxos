/**
 * @file test_spatial.c
 * @brief Test suite for ArxSpatialIndex System
 * 
 * Tests spatial indexing, querying, and operations for building objects.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include "../spatial/arx_spatial.h"
#include "../arxobject/arxobject.h"

// ============================================================================
// TEST HELPER FUNCTIONS
// ============================================================================

/**
 * @brief Create a test ArxObject with specified properties
 */
static ArxObject* create_test_object(const char* id, ArxObjectType type, 
                                   double x, double y, double z, 
                                   double width, double height, double depth) {
    ArxObject* obj = arx_object_create(id, type, "Test Object", "Test Description");
    if (!obj) return NULL;
    
    // Set geometry
    ArxGeometry geometry = {0};
    geometry.bounding_box.min.x = x;
    geometry.bounding_box.min.y = y;
    geometry.bounding_box.min.z = z;
    geometry.bounding_box.max.x = x + width;
    geometry.bounding_box.max.y = y + height;
    geometry.bounding_box.max.z = z + depth;
    
    geometry.point_count = 8;
    geometry.points = malloc(8 * sizeof(ArxPoint3D));
    if (geometry.points) {
        // Create 8 corner points of the bounding box
        geometry.points[0] = (ArxPoint3D){x, y, z};
        geometry.points[1] = (ArxPoint3D){x + width, y, z};
        geometry.points[2] = (ArxPoint3D){x, y + height, z};
        geometry.points[3] = (ArxPoint3D){x + width, y + height, z};
        geometry.points[4] = (ArxPoint3D){x, y, z + depth};
        geometry.points[5] = (ArxPoint3D){x + width, y, z + depth};
        geometry.points[6] = (ArxPoint3D){x, y + height, z + depth};
        geometry.points[7] = (ArxPoint3D){x + width, y + height, z + depth};
    }
    
    arx_object_set_geometry(obj, &geometry);
    
    // Clean up temporary geometry
    if (geometry.points) free(geometry.points);
    
    return obj;
}

/**
 * @brief Free test results array
 */
static void free_test_results(ArxSpatialResult** results, int count) {
    if (!results) return;
    for (int i = 0; i < count; i++) {
        if (results[i]) free(results[i]);
    }
    free(results);
}

// ============================================================================
// SPATIAL INDEX CREATION TESTS
// ============================================================================

static void test_spatial_index_creation(void) {
    printf("Testing spatial index creation...\n");
    
    // Test default index creation
    ArxSpatialIndex* index = arx_spatial_create_default_index();
    assert(index != NULL);
    assert(index->total_objects == 0);
    assert(index->config.max_depth == 8);
    assert(index->config.use_octree == true);
    assert(index->config.enable_caching == true);
    
    // Test custom index creation
    ArxSpatialConfig custom_config = {
        .max_depth = 12,
        .min_objects_per_node = 2,
        .max_objects_per_node = 16,
        .split_threshold = 0.9,
        .use_octree = false,
        .enable_compression = true,
        .enable_caching = false,
        .cache_size = 500
    };
    
    ArxSpatialIndex* custom_index = arx_spatial_create_index(&custom_config);
    assert(custom_index != NULL);
    assert(custom_index->config.max_depth == 12);
    assert(custom_index->config.use_octree == false);
    assert(custom_index->config.enable_caching == false);
    
    // Cleanup
    arx_spatial_destroy_index(index);
    arx_spatial_destroy_index(custom_index);
    
    printf("   Spatial index creation tests passed\n");
}

// ============================================================================
// OBJECT INDEXING TESTS
// ============================================================================

static void test_object_indexing(void) {
    printf("Testing object indexing...\n");
    
    ArxSpatialIndex* index = arx_spatial_create_default_index();
    assert(index != NULL);
    
    // Create test objects
    ArxObject* obj1 = create_test_object("obj1", ARX_OBJECT_TYPE_WALL, 0, 0, 0, 10, 3, 0.2);
    ArxObject* obj2 = create_test_object("obj2", ARX_OBJECT_TYPE_DOOR, 5, 0, 0, 1, 2.1, 0.1);
    ArxObject* obj3 = create_test_object("obj3", ARX_OBJECT_TYPE_WINDOW, 2, 1, 0, 1.5, 1.2, 0.1);
    
    assert(obj1 != NULL && obj2 != NULL && obj3 != NULL);
    
    // Test adding objects
    assert(arx_spatial_add_object(index, obj1) == true);
    assert(arx_spatial_add_object(index, obj2) == true);
    assert(arx_spatial_add_object(index, obj3) == true);
    assert(index->total_objects == 3);
    
    // Test removing objects
    assert(arx_spatial_remove_object(index, "obj2") == true);
    assert(index->total_objects == 2);
    assert(arx_spatial_remove_object(index, "nonexistent") == false);
    
    // Test adding object back
    assert(arx_spatial_add_object(index, obj2) == true);
    assert(index->total_objects == 3);
    
    // Cleanup
    arx_object_destroy(obj1);
    arx_object_destroy(obj2);
    arx_object_destroy(obj3);
    arx_spatial_destroy_index(index);
    
    printf("   Object indexing tests passed\n");
}

// ============================================================================
// SPATIAL QUERY TESTS
// ============================================================================

static void test_spatial_queries(void) {
    printf("Testing spatial queries...\n");
    
    ArxSpatialIndex* index = arx_spatial_create_default_index();
    assert(index != NULL);
    
    // Create test objects in a grid pattern
    ArxObject* objects[9];
    int obj_count = 0;
    
    for (int x = 0; x < 3; x++) {
        for (int y = 0; y < 3; y++) {
            char id[16];
            snprintf(id, sizeof(id), "obj_%d_%d", x, y);
            objects[obj_count] = create_test_object(id, ARX_OBJECT_TYPE_WALL, 
                                                 x * 10, y * 10, 0, 8, 8, 0.2);
            assert(objects[obj_count] != NULL);
            assert(arx_spatial_add_object(index, objects[obj_count]));
            obj_count++;
        }
    }
    
    assert(index->total_objects == 9);
    
    // Test range query
    ArxBoundingBox query_range = {{5, 5, 0}, {25, 25, 10}};
    int result_count = 0;
    ArxSpatialResult** results = arx_spatial_query_range(index, &query_range, &result_count);
    
    assert(results != NULL);
    assert(result_count > 0);
    printf("   Range query returned %d results\n", result_count);
    
    free_test_results(results, result_count);
    
    // Test point query
    ArxPoint3D query_point = {15, 15, 5};
    results = arx_spatial_query_point(index, &query_point, &result_count);
    
    assert(results != NULL);
    assert(result_count > 0);
    printf("   Point query returned %d results\n", result_count);
    
    free_test_results(results, result_count);
    
    // Test nearest neighbor query
    ArxPoint3D near_point = {5, 5, 5};
    results = arx_spatial_query_nearest(index, &near_point, 20.0, 5, &result_count);
    
    assert(results != NULL);
    assert(result_count > 0);
    printf("   Nearest neighbor query returned %d results\n", result_count);
    
    free_test_results(results, result_count);
    
    // Cleanup
    for (int i = 0; i < obj_count; i++) {
        arx_object_destroy(objects[i]);
    }
    arx_spatial_destroy_index(index);
    
    printf("   Spatial query tests passed\n");
}

// ============================================================================
// SPATIAL OPERATIONS TESTS
// ============================================================================

static void test_spatial_operations(void) {
    printf("Testing spatial operations...\n");
    
    // Create test objects
    ArxObject* obj1 = create_test_object("obj1", ARX_OBJECT_TYPE_WALL, 0, 0, 0, 10, 10, 0.2);
    ArxObject* obj2 = create_test_object("obj2", ARX_OBJECT_TYPE_WALL, 5, 5, 0, 10, 10, 0.2);
    ArxObject* obj3 = create_test_object("obj3", ARX_OBJECT_TYPE_WALL, 20, 20, 0, 5, 5, 0.2);
    
    assert(obj1 != NULL && obj2 != NULL && obj3 != NULL);
    
    // Test intersection
    assert(arx_spatial_objects_intersect(obj1, obj2, 0.0) == true);
    assert(arx_spatial_objects_intersect(obj1, obj3, 0.0) == false);
    
    // Test distance
    double dist = arx_spatial_objects_distance(obj1, obj3);
    assert(dist > 0.0);
    printf("   Distance between obj1 and obj3: %.2f\n", dist);
    
    // Test overlap volume
    double overlap = arx_spatial_objects_overlap_volume(obj1, obj2);
    assert(overlap > 0.0);
    printf("   Overlap volume between obj1 and obj2: %.2f\n", overlap);
    
    // Test containment
    ArxObject* small_obj = create_test_object("small", ARX_OBJECT_TYPE_DOOR, 1, 1, 0, 1, 1, 0.1);
    assert(small_obj != NULL);
    assert(arx_spatial_object_inside(small_obj, obj1) == true);
    assert(arx_spatial_object_inside(obj1, small_obj) == false);
    
    // Cleanup
    arx_object_destroy(obj1);
    arx_object_destroy(obj2);
    arx_object_destroy(obj3);
    arx_object_destroy(small_obj);
    
    printf("   Spatial operations tests passed\n");
}

// ============================================================================
// BOUNDING BOX TESTS
// ============================================================================

static void test_bounding_boxes(void) {
    printf("Testing bounding box operations...\n");
    
    // Test bounding box creation
    ArxPoint3D points[] = {
        {0, 0, 0}, {10, 5, 3}, {-2, 8, 1}, {15, -3, 7}
    };
    
    ArxBoundingBox bbox = arx_spatial_create_bounding_box(points, 4);
    assert(bbox.min.x == -2);
    assert(bbox.min.y == -3);
    assert(bbox.min.z == 0);
    assert(bbox.max.x == 15);
    assert(bbox.max.y == 8);
    assert(bbox.max.z == 7);
    
    // Test bounding box expansion
    ArxPoint3D new_point = {20, 10, -5};
    arx_spatial_expand_bounding_box(&bbox, &new_point);
    assert(bbox.min.x == -2);
    assert(bbox.min.y == -3);
    assert(bbox.min.z == -5);
    assert(bbox.max.x == 20);
    assert(bbox.max.y == 10);
    assert(bbox.max.z == 7);
    
    // Test point containment
    ArxPoint3D inside_point = {5, 2, 3};
    ArxPoint3D outside_point = {25, 15, 10};
    
    assert(arx_spatial_bounding_box_contains_point(&bbox, &inside_point) == true);
    assert(arx_spatial_bounding_box_contains_point(&bbox, &outside_point) == false);
    
    // Test intersection
    ArxBoundingBox bbox2 = {{5, 5, 5}, {25, 25, 25}};
    ArxBoundingBox bbox3 = {{30, 30, 30}, {40, 40, 40}};
    
    assert(arx_spatial_bounding_boxes_intersect(&bbox, &bbox2) == true);
    assert(arx_spatial_bounding_boxes_intersect(&bbox, &bbox3) == false);
    
    // Test volume and surface area
    double volume = arx_spatial_bounding_box_volume(&bbox);
    double surface_area = arx_spatial_bounding_box_surface_area(&bbox);
    
    assert(volume > 0.0);
    assert(surface_area > 0.0);
    printf("   Bounding box volume: %.2f, surface area: %.2f\n", volume, surface_area);
    
    printf("   Bounding box tests passed\n");
}

// ============================================================================
// PERFORMANCE TESTS
// ============================================================================

static void test_performance_metrics(void) {
    printf("Testing performance metrics...\n");
    
    ArxSpatialIndex* index = arx_spatial_create_default_index();
    assert(index != NULL);
    
    // Add some objects to generate metrics
    for (int i = 0; i < 100; i++) {
        char id[16];
        snprintf(id, sizeof(id), "perf_obj_%d", i);
        ArxObject* obj = create_test_object(id, ARX_OBJECT_TYPE_WALL, 
                                          i * 2, i * 2, 0, 1, 1, 0.1);
        if (obj) {
            arx_spatial_add_object(index, obj);
            arx_object_destroy(obj); // Clean up immediately
        }
    }
    
    // Test statistics
    char* stats = arx_spatial_get_statistics(index);
    assert(stats != NULL);
    printf("   Statistics:\n%s\n", stats);
    free(stats);
    
    // Test memory usage
    size_t memory = arx_spatial_get_memory_usage(index);
    assert(memory > 0);
    printf("   Memory usage: %zu bytes\n", memory);
    
    // Cleanup
    arx_spatial_destroy_index(index);
    
    printf("   Performance metrics tests passed\n");
}

// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

int main(void) {
    printf("Running ArxSpatialIndex System Tests...\n\n");
    
    test_spatial_index_creation();
    test_object_indexing();
    test_spatial_queries();
    test_spatial_operations();
    test_bounding_boxes();
    test_performance_metrics();
    
    printf("\nAll ArxSpatialIndex tests passed successfully!\n");
    return 0;
}
