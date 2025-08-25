/**
 * ASCII-BIM Spatial Engine - Header
 * 
 * Converts ArxObjects into 2D and 3D ASCII art representations
 * for field worker navigation and building visualization.
 * 
 * Performance targets:
 * - 2D floor plan generation: <10ms
 * - 3D building rendering: <50ms
 * - ASCII optimization: <5ms
 */

#ifndef ASCII_ENGINE_H
#define ASCII_ENGINE_H

#include "../arxobject/arxobject.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// ASCII Canvas and Rendering
// ============================================================================

/**
 * ASCII canvas for 2D floor plans
 */
typedef struct {
    char** grid;           // 2D character grid
    int width;             // Canvas width in characters
    int height;            // Canvas height in characters
    ArxPoint3D origin;     // World coordinate origin
    double scale;          // Pixels per millimeter
    char background;       // Background character
} ASCII2DCanvas;

/**
 * ASCII canvas for 3D building views
 */
typedef struct {
    char*** grid;          // 3D character grid
    int width;             // Canvas width
    int height;            // Canvas height  
    int depth;             // Canvas depth (floors)
    ArxPoint3D origin;     // World coordinate origin
    double scale;          // Scale factor
    char background;       // Background character
} ASCII3DCanvas;

/**
 * Rendering options for ASCII generation
 */
typedef struct {
    bool show_labels;       // Show object names/labels
    bool show_coordinates;  // Show coordinate grid
    bool show_legend;       // Show element type legend
    bool optimize_spacing;  // Optimize character spacing
    int max_width;          // Maximum output width
    int max_height;         // Maximum output height
    char wall_char;         // Character for walls
    char door_char;         // Character for doors
    char window_char;       // Character for windows
    char room_char;         // Character for rooms
    char furniture_char;    // Character for furniture
    char mep_char;          // Character for MEP systems
} ASCIIRenderOptions;

// ============================================================================
// Core ASCII Generation Functions
// ============================================================================

/**
 * Generate 2D ASCII floor plan from ArxObjects
 */
char* generate_2d_floor_plan(ArxObject** objects, int object_count, 
                             const ASCIIRenderOptions* options);

/**
 * Generate 3D ASCII building view from ArxObjects
 */
char* generate_3d_building_view(ArxObject** objects, int object_count,
                                const ASCIIRenderOptions* options);

/**
 * Generate both 2D and 3D representations
 */
bool generate_both_representations(ArxObject** objects, int object_count,
                                  const ASCIIRenderOptions* options,
                                  char** floor_plan_2d, char** building_3d);

// ============================================================================
// Canvas Management
// ============================================================================

/**
 * Create and manage 2D ASCII canvas
 */
ASCII2DCanvas* ascii_2d_canvas_create(int width, int height, const ArxPoint3D* origin, double scale);
void ascii_2d_canvas_destroy(ASCII2DCanvas* canvas);
void ascii_2d_canvas_clear(ASCII2DCanvas* canvas);
void ascii_2d_canvas_set_pixel(ASCII2DCanvas* canvas, int x, int y, char value);
char ascii_2d_canvas_get_pixel(ASCII2DCanvas* canvas, int x, int y);

/**
 * Create and manage 3D ASCII canvas
 */
ASCII3DCanvas* ascii_3d_canvas_create(int width, int height, int depth, 
                                      const ArxPoint3D* origin, double scale);
void ascii_3d_canvas_destroy(ASCII3DCanvas* canvas);
void ascii_3d_canvas_clear(ASCII3DCanvas* canvas);
void ascii_3d_canvas_set_voxel(ASCII3DCanvas* canvas, int x, int y, int z, char value);
char ascii_3d_canvas_get_voxel(ASCII3DCanvas* canvas, int x, int y, int z);

// ============================================================================
// Object Rendering
// ============================================================================

/**
 * Render individual ArxObjects to ASCII
 */
bool render_arx_object_2d(ASCII2DCanvas* canvas, const ArxObject* obj, 
                          const ASCIIRenderOptions* options);
bool render_arx_object_3d(ASCII3DCanvas* canvas, const ArxObject* obj,
                          const ASCIIRenderOptions* options);

/**
 * Render specific building element types
 */
bool render_wall_2d(ASCII2DCanvas* canvas, const ArxObject* wall, 
                    const ASCIIRenderOptions* options);
bool render_room_2d(ASCII2DCanvas* canvas, const ArxObject* room,
                    const ASCIIRenderOptions* options);
bool render_door_2d(ASCII2DCanvas* canvas, const ArxObject* door,
                    const ASCIIRenderOptions* options);
bool render_window_2d(ASCII2DCanvas* canvas, const ArxObject* window,
                      const ASCIIRenderOptions* options);
bool render_mep_element_2d(ASCII2DCanvas* canvas, const ArxObject* element,
                           const ASCIIRenderOptions* options);

// ============================================================================
// Spatial Layout and Navigation
// ============================================================================

/**
 * Calculate optimal layout for building elements
 */
bool calculate_building_layout(ArxObject** objects, int object_count,
                              ArxPoint3D* layout_center, double* layout_bounds);

/**
 * Generate navigation grid for field workers
 */
char* generate_navigation_grid(ArxObject** objects, int object_count,
                               const ArxPoint3D* start_point,
                               const ArxPoint3D* end_point);

/**
 * Find shortest path between two points
 */
bool find_shortest_path(ArxObject** objects, int object_count,
                        const ArxPoint3D* start, const ArxPoint3D* end,
                        ArxPoint3D** path, int* path_length);

// ============================================================================
// ASCII Optimization and Formatting
// ============================================================================

/**
 * Optimize ASCII output for readability
 */
char* optimize_ascii_output(const char* ascii_input, int max_width, int max_height);

/**
 * Add labels and annotations
 */
char* add_ascii_labels(const char* ascii_input, ArxObject** objects, int object_count);

/**
 * Generate legend and key
 */
char* generate_ascii_legend(const ArxRenderOptions* options);

/**
 * Format ASCII for different output devices
 */
char* format_ascii_for_terminal(const char* ascii_input);
char* format_ascii_for_mobile(const char* ascii_input);
char* format_ascii_for_print(const char* ascii_input);

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Convert world coordinates to canvas coordinates
 */
bool world_to_canvas_2d(const ArxPoint3D* world_point, const ASCII2DCanvas* canvas,
                        int* canvas_x, int* canvas_y);
bool world_to_canvas_3d(const ArxPoint3D* world_point, const ASCII3DCanvas* canvas,
                        int* canvas_x, int* canvas_y, int* canvas_z);

/**
 * Convert canvas coordinates to world coordinates
 */
bool canvas_to_world_2d(int canvas_x, int canvas_y, const ASCII2DCanvas* canvas,
                        ArxPoint3D* world_point);
bool canvas_to_world_3d(int canvas_x, int canvas_y, int canvas_z, const ASCII3DCanvas* canvas,
                        ArxPoint3D* world_point);

/**
 * ASCII character utilities
 */
char get_ascii_char_for_element_type(ArxObjectType type, const ASCIIRenderOptions* options);
bool is_ascii_char_valid(char c);
char get_ascii_char_for_confidence(double confidence);

// ============================================================================
// Default Options
// ============================================================================

/**
 * Get default rendering options
 */
ASCIIRenderOptions* get_default_ascii_options(void);

/**
 * Free rendering options
 */
void free_ascii_options(ASCIIRenderOptions* options);

#ifdef __cplusplus
}
#endif

#endif // ASCII_ENGINE_H
