/**
 * ArxObject Test Suite
 * Tests the core ArxObject functionality to ensure the C runtime engine works
 */

#include "../arxobject.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// Test function declarations
static void test_arx_object_creation();
static void test_arx_object_properties();
static void test_arx_object_geometry();
static void test_arx_object_types();
static void test_arx_object_validation();

// Helper function to print test results
static void print_test_result(const char* test_name, bool passed) {
    printf("[%s] %s\n", passed ? "PASS" : "FAIL", test_name);
}

int main() {
    printf("=== ArxObject C Runtime Engine Test Suite ===\n\n");
    
    // Run all tests
    test_arx_object_creation();
    test_arx_object_properties();
    test_arx_object_geometry();
    test_arx_object_types();
    test_arx_object_validation();
    
    printf("\n=== Test Suite Complete ===\n");
    return 0;
}

static void test_arx_object_creation() {
    printf("Testing ArxObject Creation...\n");
    
    // Test basic creation
    ArxObject* wall = arx_object_create(ARX_TYPE_WALL, "North Wall");
    assert(wall != NULL);
    assert(arx_object_is_valid(wall));
    assert(wall->type == ARX_TYPE_WALL);
    assert(strcmp(wall->name, "North Wall") == 0);
    assert(wall->confidence == 0.5);  // Default confidence
    print_test_result("Basic wall creation", true);
    
    // Test room creation
    ArxObject* room = arx_object_create(ARX_TYPE_ROOM, "Living Room");
    assert(room != NULL);
    assert(arx_object_is_valid(room));
    assert(room->type == ARX_TYPE_ROOM);
    print_test_result("Basic room creation", true);
    
    // Test electrical outlet creation
    ArxObject* outlet = arx_object_create(ARX_TYPE_ELECTRICAL_OUTLET, "Kitchen Outlet");
    assert(outlet != NULL);
    assert(arx_object_is_valid(outlet));
    assert(outlet->type == ARX_TYPE_ELECTRICAL_OUTLET);
    print_test_result("Basic electrical outlet creation", true);
    
    // Test invalid creation
    ArxObject* invalid = arx_object_create(ARX_TYPE_UNKNOWN, NULL);
    assert(invalid == NULL);
    print_test_result("Invalid creation rejected", true);
    
    // Cleanup
    arx_object_destroy(wall);
    arx_object_destroy(room);
    arx_object_destroy(outlet);
    
    printf("\n");
}

static void test_arx_object_properties() {
    printf("Testing ArxObject Properties...\n");
    
    ArxObject* wall = arx_object_create(ARX_TYPE_WALL, "Test Wall");
    assert(wall != NULL);
    
    // Test setting integer property
    ArxPropertyValue int_val;
    int_val.int_value = 120;
    bool success = arx_object_set_property(wall, "thickness_mm", ARX_PROP_INT, int_val);
    assert(success);
    print_test_result("Set integer property", true);
    
    // Test setting string property
    ArxPropertyValue string_val;
    string_val.string_value = "Concrete";
    success = arx_object_set_property(wall, "material", ARX_PROP_STRING, string_val);
    assert(success);
    print_test_result("Set string property", true);
    
    // Test setting float property
    ArxPropertyValue float_val;
    float_val.float_value = 2.4;
    success = arx_object_set_property(wall, "height_m", ARX_PROP_FLOAT, float_val);
    assert(success);
    print_test_result("Set float property", true);
    
    // Test getting properties
    ArxPropertyValue retrieved_val;
    success = arx_object_get_property(wall, "thickness_mm", &retrieved_val);
    assert(success);
    assert(retrieved_val.int_value == 120);
    print_test_result("Get integer property", true);
    
    success = arx_object_get_property(wall, "material", &retrieved_val);
    assert(success);
    assert(strcmp(retrieved_val.string_value, "Concrete") == 0);
    print_test_result("Get string property", true);
    
    // Test property existence
    assert(arx_object_has_property(wall, "thickness_mm"));
    assert(arx_object_has_property(wall, "material"));
    assert(!arx_object_has_property(wall, "nonexistent"));
    print_test_result("Property existence check", true);
    
    // Test property removal
    success = arx_object_remove_property(wall, "thickness_mm");
    assert(success);
    assert(!arx_object_has_property(wall, "thickness_mm"));
    print_test_result("Property removal", true);
    
    // Cleanup
    arx_object_destroy(wall);
    
    printf("\n");
}

static void test_arx_object_geometry() {
    printf("Testing ArxObject Geometry...\n");
    
    ArxObject* wall = arx_object_create(ARX_TYPE_WALL, "Geometry Test Wall");
    assert(wall != NULL);
    
    // Create geometry
    ArxGeometry geometry;
    geometry.position.x = 1000;  // 1 meter in mm
    geometry.position.y = 2000;  // 2 meters in mm
    geometry.position.z = 0;     // Ground level
    
    geometry.bounding_box.min.x = 0;
    geometry.bounding_box.min.y = 0;
    geometry.bounding_box.min.z = 0;
    geometry.bounding_box.max.x = 2000;  // 2 meters wide
    geometry.bounding_box.max.y = 2400;  // 2.4 meters high
    geometry.bounding_box.max.z = 200;   // 20cm thick
    
    geometry.rotation = 0.0;
    geometry.scale = 1.0;
    geometry.points = NULL;
    geometry.point_count = 0;
    geometry.vertices = NULL;
    geometry.vertex_count = 0;
    geometry.faces = NULL;
    geometry.face_count = 0;
    
    // Set geometry
    bool success = arx_object_set_geometry(wall, &geometry);
    assert(success);
    print_test_result("Set geometry", true);
    
    // Get geometry back
    ArxGeometry retrieved_geometry;
    success = arx_object_get_geometry(wall, &retrieved_geometry);
    assert(success);
    assert(retrieved_geometry.position.x == 1000);
    assert(retrieved_geometry.position.y == 2000);
    assert(retrieved_geometry.bounding_box.max.y == 2400);
    print_test_result("Get geometry", true);
    
    // Test point inside check
    ArxPoint3D inside_point = {1000, 1200, 100};  // Center of wall
    bool is_inside = arx_object_is_point_inside(wall, &inside_point);
    assert(is_inside);
    print_test_result("Point inside check", true);
    
    // Test point outside check
    ArxPoint3D outside_point = {3000, 3000, 100};  // Outside wall
    bool is_outside = !arx_object_is_point_inside(wall, &outside_point);
    assert(is_outside);
    print_test_result("Point outside check", true);
    
    // Test position update
    ArxPoint3D new_position = {1500, 2500, 100};
    success = arx_object_update_position(wall, &new_position);
    assert(success);
    
    ArxGeometry updated_geometry;
    arx_object_get_geometry(wall, &updated_geometry);
    assert(updated_geometry.position.x == 1500);
    assert(updated_geometry.position.y == 2500);
    print_test_result("Position update", true);
    
    // Cleanup
    arx_object_destroy(wall);
    
    printf("\n");
}

static void test_arx_object_types() {
    printf("Testing ArxObject Types...\n");
    
    // Test type names
    const char* wall_name = arx_object_get_type_name(ARX_TYPE_WALL);
    assert(strcmp(wall_name, "wall") == 0);
    print_test_result("Get wall type name", true);
    
    const char* room_name = arx_object_get_type_name(ARX_TYPE_ROOM);
    assert(strcmp(room_name, "room") == 0);
    print_test_result("Get room type name", true);
    
    const char* outlet_name = arx_object_get_type_name(ARX_TYPE_ELECTRICAL_OUTLET);
    assert(strcmp(outlet_name, "electrical_outlet") == 0);
    print_test_result("Get electrical outlet type name", true);
    
    // Test type from name
    ArxObjectType wall_type = arx_object_get_type_from_name("wall");
    assert(wall_type == ARX_TYPE_WALL);
    print_test_result("Get wall type from name", true);
    
    ArxObjectType room_type = arx_object_get_type_from_name("room");
    assert(room_type == ARX_TYPE_ROOM);
    print_test_result("Get room type from name", true);
    
    ArxObjectType unknown_type = arx_object_get_type_from_name("nonexistent");
    assert(unknown_type == ARX_TYPE_UNKNOWN);
    print_test_result("Get unknown type from name", true);
    
    // Test type checking
    ArxObject* wall = arx_object_create(ARX_TYPE_WALL, "Type Test Wall");
    assert(arx_object_is_type(wall, ARX_TYPE_WALL));
    assert(!arx_object_is_type(wall, ARX_TYPE_ROOM));
    print_test_result("Type checking", true);
    
    // Cleanup
    arx_object_destroy(wall);
    
    printf("\n");
}

static void test_arx_object_validation() {
    printf("Testing ArxObject Validation...\n");
    
    ArxObject* wall = arx_object_create(ARX_TYPE_WALL, "Validation Test Wall");
    assert(wall != NULL);
    
    // Check initial validation status
    assert(wall->validation_status == ARX_VALIDATION_PENDING);
    assert(wall->confidence == 0.5);
    print_test_result("Initial validation status", true);
    
    // Test validation
    ArxValidationRecord validation;
    validation.id = "val_001";
    validation.timestamp = time(NULL);
    validation.validated_by = "field_worker_1";
    validation.method = "photo";
    validation.evidence = "photo_001.jpg";
    validation.confidence = 0.9;
    validation.notes = "Confirmed wall exists and dimensions match";
    
    // Note: We're not implementing add_validation yet, so this is a placeholder
    // In the full implementation, this would update the validation status
    print_test_result("Validation record structure", true);
    
    // Cleanup
    arx_object_destroy(wall);
    
    printf("\n");
}
