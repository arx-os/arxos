#include <stdio.h>
#include <assert.h>
#include "pixatool_engine.h"

void test_canvas_creation() {
    printf("Testing canvas creation...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(80, 40);
    assert(canvas != NULL);
    assert(canvas->width == 80);
    assert(canvas->height == 40);
    assert(canvas->ascii_buffer != NULL);
    assert(canvas->render_buffer != NULL);
    
    destroy_canvas(canvas);
    printf("✓ Canvas creation test passed\n");
}

void test_wall_rendering() {
    printf("Testing wall rendering...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(20, 10);
    
    // Draw a simple room
    render_wall(canvas, 2, 2, 17, 2, 1.0);  // Top wall
    render_wall(canvas, 17, 2, 17, 7, 1.0); // Right wall
    render_wall(canvas, 17, 7, 2, 7, 1.0);  // Bottom wall
    render_wall(canvas, 2, 7, 2, 2, 1.0);   // Left wall
    
    // Render to ASCII
    render_to_ascii(canvas);
    
    // Check that walls were rendered
    int wall_count = 0;
    for (int i = 0; i < canvas->width * canvas->height; i++) {
        if (canvas->ascii_buffer[i] != ' ') {
            wall_count++;
        }
    }
    assert(wall_count > 0);
    
    printf("Room layout:\n");
    print_canvas(canvas);
    
    destroy_canvas(canvas);
    printf("✓ Wall rendering test passed\n");
}

void test_door_rendering() {
    printf("Testing door rendering...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(30, 15);
    
    // Draw walls with door
    render_wall(canvas, 5, 5, 25, 5, 1.0);   // Top wall
    render_wall(canvas, 25, 5, 25, 10, 1.0); // Right wall
    render_wall(canvas, 25, 10, 5, 10, 1.0); // Bottom wall
    render_wall(canvas, 5, 10, 5, 5, 1.0);   // Left wall
    
    // Add door in bottom wall
    render_door(canvas, 14, 10, 3, 1);
    
    // Render to ASCII
    render_to_ascii(canvas);
    
    printf("Room with door:\n");
    print_canvas(canvas);
    
    destroy_canvas(canvas);
    printf("✓ Door rendering test passed\n");
}

void test_equipment_rendering() {
    printf("Testing equipment rendering...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(20, 10);
    
    // Add various equipment
    render_equipment(canvas, 5, 3, MATERIAL_PANEL);
    render_equipment(canvas, 10, 3, MATERIAL_OUTLET);
    render_equipment(canvas, 15, 3, MATERIAL_EQUIPMENT);
    
    render_equipment(canvas, 5, 6, MATERIAL_OUTLET);
    render_equipment(canvas, 10, 6, MATERIAL_PANEL);
    render_equipment(canvas, 15, 6, MATERIAL_EQUIPMENT);
    
    // Render to ASCII
    render_to_ascii(canvas);
    
    printf("Equipment layout:\n");
    print_canvas(canvas);
    
    destroy_canvas(canvas);
    printf("✓ Equipment rendering test passed\n");
}

void test_room_filling() {
    printf("Testing room filling...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(40, 20);
    
    // Draw multiple rooms
    render_wall(canvas, 2, 2, 18, 2, 1.0);
    render_wall(canvas, 18, 2, 18, 8, 1.0);
    render_wall(canvas, 18, 8, 2, 8, 1.0);
    render_wall(canvas, 2, 8, 2, 2, 1.0);
    fill_room(canvas, 3, 3, 15, 5, MATERIAL_ROOM_OFFICE);
    
    render_wall(canvas, 20, 2, 36, 2, 1.0);
    render_wall(canvas, 36, 2, 36, 8, 1.0);
    render_wall(canvas, 36, 8, 20, 8, 1.0);
    render_wall(canvas, 20, 8, 20, 2, 1.0);
    fill_room(canvas, 21, 3, 15, 5, MATERIAL_ROOM_CLASSROOM);
    
    render_wall(canvas, 2, 10, 36, 10, 1.0);
    render_wall(canvas, 36, 10, 36, 16, 1.0);
    render_wall(canvas, 36, 16, 2, 16, 1.0);
    render_wall(canvas, 2, 16, 2, 10, 1.0);
    fill_room(canvas, 3, 11, 33, 5, MATERIAL_ROOM_CORRIDOR);
    
    // Render to ASCII
    render_to_ascii(canvas);
    
    printf("Multi-room layout:\n");
    print_canvas(canvas);
    
    destroy_canvas(canvas);
    printf("✓ Room filling test passed\n");
}

void test_edge_detection() {
    printf("Testing edge detection...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(15, 10);
    
    // Create a shape with clear edges
    for (int y = 3; y < 7; y++) {
        for (int x = 3; x < 12; x++) {
            int idx = y * canvas->width + x;
            canvas->render_buffer[idx].depth = 1.0;
            canvas->render_buffer[idx].material_type = MATERIAL_WALL;
        }
    }
    
    // Apply edge detection
    detect_edges(canvas);
    
    // Check that edges were detected
    int edge_count = 0;
    for (int y = 0; y < canvas->height; y++) {
        for (int x = 0; x < canvas->width; x++) {
            int idx = y * canvas->width + x;
            if (canvas->render_buffer[idx].edge_strength > 0.3) {
                edge_count++;
            }
        }
    }
    assert(edge_count > 0);
    
    // Render to ASCII
    render_to_ascii(canvas);
    
    printf("Edge detection result:\n");
    print_canvas(canvas);
    
    destroy_canvas(canvas);
    printf("✓ Edge detection test passed (%d edges detected)\n", edge_count);
}

void test_complete_building() {
    printf("Testing complete building floor plan...\n");
    
    ASCIICanvas* canvas = create_ascii_canvas(60, 30);
    
    // Main building outline
    render_wall(canvas, 5, 5, 55, 5, 1.0);   // Top
    render_wall(canvas, 55, 5, 55, 25, 1.0); // Right
    render_wall(canvas, 55, 25, 5, 25, 1.0); // Bottom
    render_wall(canvas, 5, 25, 5, 5, 1.0);   // Left
    
    // Interior walls - create 4 rooms
    render_wall(canvas, 5, 15, 30, 15, 0.8); // Horizontal divider left
    render_wall(canvas, 35, 15, 55, 15, 0.8); // Horizontal divider right
    render_wall(canvas, 30, 5, 30, 25, 0.8); // Vertical divider
    
    // Add doors
    render_door(canvas, 30, 10, 1, 0);  // Door between top rooms
    render_door(canvas, 30, 20, 1, 0);  // Door between bottom rooms
    render_door(canvas, 15, 15, 3, 1);  // Door in left divider
    render_door(canvas, 42, 15, 3, 1);  // Door in right divider
    
    // External doors
    render_door(canvas, 28, 25, 4, 1);  // Main entrance
    
    // Fill rooms with different patterns
    fill_room(canvas, 6, 6, 23, 8, MATERIAL_ROOM_OFFICE);      // Top-left: Office
    fill_room(canvas, 31, 6, 23, 8, MATERIAL_ROOM_CLASSROOM); // Top-right: Classroom
    fill_room(canvas, 6, 16, 23, 8, MATERIAL_ROOM_LARGE);     // Bottom-left: Large space
    fill_room(canvas, 31, 16, 23, 8, MATERIAL_ROOM_OFFICE);   // Bottom-right: Office
    
    // Add equipment
    render_equipment(canvas, 8, 8, MATERIAL_PANEL);    // Electrical panel in office
    render_equipment(canvas, 52, 8, MATERIAL_OUTLET);  // Outlet in classroom
    render_equipment(canvas, 8, 22, MATERIAL_OUTLET);  // Outlet in large room
    render_equipment(canvas, 52, 22, MATERIAL_PANEL);  // Panel in office
    
    // Apply full rendering pipeline
    detect_edges(canvas);
    apply_antialiasing(canvas);
    apply_dithering(canvas);
    
    // Convert to ASCII
    for (int y = 0; y < canvas->height; y++) {
        for (int x = 0; x < canvas->width; x++) {
            int idx = y * canvas->width + x;
            PixelData* pixel = &canvas->render_buffer[idx];
            
            char ascii_char;
            if (pixel->edge_strength > 0.5) {
                ascii_char = select_edge_char(canvas, x, y);
            } else {
                ascii_char = depth_to_ascii(
                    pixel->depth,
                    pixel->edge_strength,
                    pixel->material_type
                );
            }
            
            canvas->ascii_buffer[idx] = ascii_char;
        }
    }
    canvas->ascii_buffer[canvas->width * canvas->height] = '\0';
    
    printf("Complete building floor plan:\n");
    printf("╔══════════════════════════════════════════════════════════╗\n");
    printf("║  Building: HQ  │  Floor: 1  │  Scale: 1 char = 1m       ║\n");
    printf("╠══════════════════════════════════════════════════════════╣\n");
    
    for (int y = 0; y < canvas->height; y++) {
        printf("║");
        for (int x = 0; x < canvas->width; x++) {
            putchar(canvas->ascii_buffer[y * canvas->width + x]);
        }
        printf("║\n");
    }
    
    printf("╠══════════════════════════════════════════════════════════╣\n");
    printf("║ Legend: █=Wall ╬=Door ▣=Panel ○=Outlet ░▒=Rooms         ║\n");
    printf("╚══════════════════════════════════════════════════════════╝\n");
    
    destroy_canvas(canvas);
    printf("✓ Complete building test passed\n");
}

int main() {
    printf("\n");
    printf("═══════════════════════════════════════════\n");
    printf("   Pixatool ASCII-BIM Engine Test Suite    \n");
    printf("═══════════════════════════════════════════\n");
    printf("\n");
    
    test_canvas_creation();
    printf("\n");
    
    test_wall_rendering();
    printf("\n");
    
    test_door_rendering();
    printf("\n");
    
    test_equipment_rendering();
    printf("\n");
    
    test_room_filling();
    printf("\n");
    
    test_edge_detection();
    printf("\n");
    
    test_complete_building();
    printf("\n");
    
    printf("═══════════════════════════════════════════\n");
    printf("   All tests passed successfully! ✓        \n");
    printf("═══════════════════════════════════════════\n");
    printf("\n");
    
    return 0;
}