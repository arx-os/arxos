/**
 * ASCII Engine Test Suite
 * Tests the ASCII-BIM Spatial Engine functionality
 */

#include "../ascii/ascii_engine.h"
#include "../arxobject/arxobject.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// Test function declarations
static void test_ascii_canvas_2d(void);
static void test_ascii_canvas_3d(void);
static void test_ascii_generation(void);
static void test_ascii_options(void);

int main() {
    printf("=== ASCII Engine Test Suite ===\n");
    
    test_ascii_canvas_2d();
    test_ascii_canvas_3d();
    test_ascii_generation();
    test_ascii_options();
    
    printf("All ASCII engine tests passed!\n");
    return 0;
}

static void test_ascii_canvas_2d(void) {
    printf("Testing 2D ASCII canvas...\n");
    
    ArxPoint3D origin = {0, 0, 0};
    ASCII2DCanvas* canvas = ascii_2d_canvas_create(10, 5, &origin, 1.0);
    assert(canvas != NULL);
    assert(canvas->width == 10);
    assert(canvas->height == 5);
    
    // Test pixel operations
    ascii_2d_canvas_set_pixel(canvas, 5, 2, 'X');
    char pixel = ascii_2d_canvas_get_pixel(canvas, 5, 2);
    assert(pixel == 'X');
    
    // Test bounds checking
    ascii_2d_canvas_set_pixel(canvas, 15, 10, 'Y'); // Should be ignored
    pixel = ascii_2d_canvas_get_pixel(canvas, 15, 10);
    assert(pixel == '\0');
    
    ascii_2d_canvas_destroy(canvas);
    printf("  2D canvas tests passed\n");
}

static void test_ascii_canvas_3d(void) {
    printf("Testing 3D ASCII canvas...\n");
    
    ArxPoint3D origin = {0, 0, 0};
    ASCII3DCanvas* canvas = ascii_3d_canvas_create(8, 6, 4, &origin, 1.0);
    assert(canvas != NULL);
    assert(canvas->width == 8);
    assert(canvas->height == 6);
    assert(canvas->depth == 4);
    
    // Test voxel operations
    ascii_3d_canvas_set_voxel(canvas, 4, 3, 2, 'Z');
    char voxel = ascii_3d_canvas_get_voxel(canvas, 4, 3, 2);
    assert(voxel == 'Z');
    
    // Test bounds checking
    ascii_3d_canvas_set_voxel(canvas, 20, 15, 10, 'W'); // Should be ignored
    voxel = ascii_3d_canvas_get_voxel(canvas, 20, 15, 10);
    assert(voxel == '\0');
    
    ascii_3d_canvas_destroy(canvas);
    printf("  3D canvas tests passed\n");
}

static void test_ascii_generation(void) {
    printf("Testing ASCII generation...\n");
    
    // Create test ArxObjects
    ArxObject* wall = arx_object_create(ARX_TYPE_WALL, "Test Wall");
    ArxObject* room = arx_object_create(ARX_TYPE_ROOM, "Test Room");
    
    // Set geometry for wall
    ArxGeometry wall_geom = {0};
    wall_geom.position = (ArxPoint3D){10, 10, 0};
    wall_geom.bounding_box.min = (ArxPoint3D){10, 10, 0};
    wall_geom.bounding_box.max = (ArxPoint3D){50, 12, 0};
    arx_object_set_geometry(wall, &wall_geom);
    
    // Set geometry for room
    ArxGeometry room_geom = {0};
    room_geom.position = (ArxPoint3D){20, 20, 0};
    room_geom.bounding_box.min = (ArxPoint3D){20, 20, 0};
    room_geom.bounding_box.max = (ArxPoint3D){80, 60, 0};
    arx_object_set_geometry(room, &room_geom);
    
    // Create ArxObject array
    ArxObject* objects[] = {wall, room};
    int object_count = 2;
    
    // Get default options
    ASCIIRenderOptions* options = get_default_ascii_options();
    assert(options != NULL);
    
    // Test 2D generation
    char* floor_plan = generate_2d_floor_plan(objects, object_count, options);
    assert(floor_plan != NULL);
    assert(strlen(floor_plan) > 0);
    
    // Test 3D generation
    char* building_3d = generate_3d_building_view(objects, object_count, options);
    assert(building_3d != NULL);
    assert(strlen(building_3d) > 0);
    
    // Test both representations
    char* plan_2d, *building_3d_both;
    bool success = generate_both_representations(objects, object_count, options, &plan_2d, &building_3d_both);
    assert(success);
    assert(plan_2d != NULL);
    assert(building_3d_both != NULL);
    
    // Cleanup
    free(floor_plan);
    free(building_3d);
    free(plan_2d);
    free(building_3d_both);
    free_ascii_options(options);
    
    arx_object_destroy(wall);
    arx_object_destroy(room);
    
    printf("  ASCII generation tests passed\n");
}

static void test_ascii_options(void) {
    printf("Testing ASCII options...\n");
    
    ASCIIRenderOptions* options = get_default_ascii_options();
    assert(options != NULL);
    
    // Test default values
    assert(options->show_labels == true);
    assert(options->wall_char == '#');
    assert(options->door_char == 'D');
    assert(options->window_char == 'W');
    assert(options->room_char == ' ');
    assert(options->furniture_char == 'F');
    assert(options->mep_char == 'M');
    
    // Test element type mapping
    char wall_char = get_ascii_char_for_element_type(ARX_TYPE_WALL, options);
    assert(wall_char == '#');
    
    char door_char = get_ascii_char_for_element_type(ARX_TYPE_DOOR, options);
    assert(door_char == 'D');
    
    char unknown_char = get_ascii_char_for_element_type(ARX_TYPE_UNKNOWN, options);
    assert(unknown_char == '#');
    
    // Test confidence mapping
    char high_conf = get_ascii_char_for_confidence(0.95);
    assert(high_conf == '█');
    
    char low_conf = get_ascii_char_for_confidence(0.2);
    assert(low_conf == '·');
    
    // Test character validation
    assert(is_ascii_char_valid('A') == true);
    assert(is_ascii_char_valid('5') == true);
    assert(is_ascii_char_valid('\n') == true);
    assert(is_ascii_char_valid('\0') == false);
    
    free_ascii_options(options);
    printf("  ASCII options tests passed\n");
}
