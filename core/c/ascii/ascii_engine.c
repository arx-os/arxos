/**
 * ASCII-BIM Spatial Engine - Implementation
 * 
 * Converts ArxObjects into 2D and 3D ASCII art representations
 * for field worker navigation and building visualization.
 */

#include "ascii_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>

// ============================================================================
// Internal Helper Functions
// ============================================================================

/**
 * Safe string duplication
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
 * Calculate bounding box for a set of ArxObjects
 */
static void calculate_bounds(ArxObject** objects, int object_count, 
                           ArxPoint3D* min, ArxPoint3D* max) {
    if (object_count == 0) return;
    
    // Initialize with first object
    ArxGeometry geom;
    arx_object_get_geometry(objects[0], &geom);
    *min = geom.bounding_box.min;
    *max = geom.bounding_box.max;
    
    // Find min/max across all objects
    for (int i = 1; i < object_count; i++) {
        arx_object_get_geometry(objects[i], &geom);
        
        if (geom.bounding_box.min.x < min->x) min->x = geom.bounding_box.min.x;
        if (geom.bounding_box.min.y < min->y) min->y = geom.bounding_box.min.y;
        if (geom.bounding_box.min.z < min->z) min->z = geom.bounding_box.min.z;
        
        if (geom.bounding_box.max.x > max->x) max->x = geom.bounding_box.max.x;
        if (geom.bounding_box.max.y > max->y) max->y = geom.bounding_box.max.y;
        if (geom.bounding_box.max.z > max->z) max->z = geom.bounding_box.max.z;
    }
}

/**
 * Get ASCII character for building element type
 */
static char get_element_char(ArxObjectType type, const ASCIIRenderOptions* options) {
    switch (type) {
        case ARX_TYPE_WALL:
        case ARX_TYPE_EXTERIOR_WALL:
        case ARX_TYPE_INTERIOR_WALL:
            return options->wall_char;
            
        case ARX_TYPE_DOOR:
        case ARX_TYPE_EXTERIOR_DOOR:
        case ARX_TYPE_INTERIOR_DOOR:
            return options->door_char;
            
        case ARX_TYPE_WINDOW:
        case ARX_TYPE_EXTERIOR_WINDOW:
        case ARX_TYPE_INTERIOR_WINDOW:
            return options->window_char;
            
        case ARX_TYPE_ROOM:
        case ARX_TYPE_SPACE:
            return options->room_char;
            
        case ARX_TYPE_FURNITURE:
        case ARX_TYPE_EQUIPMENT:
            return options->furniture_char;
            
        case ARX_TYPE_ELECTRICAL:
        case ARX_TYPE_MECHANICAL:
        case ARX_TYPE_PLUMBING:
            return options->mep_char;
            
        default:
            return '#';
    }
}

// ============================================================================
// Canvas Management
// ============================================================================

ASCII2DCanvas* ascii_2d_canvas_create(int width, int height, const ArxPoint3D* origin, double scale) {
    if (width <= 0 || height <= 0) return NULL;
    
    ASCII2DCanvas* canvas = malloc(sizeof(ASCII2DCanvas));
    if (!canvas) return NULL;
    
    canvas->width = width;
    canvas->height = height;
    canvas->origin = *origin;
    canvas->scale = scale;
    canvas->background = ' ';
    
    // Allocate 2D grid
    canvas->grid = malloc(height * sizeof(char*));
    if (!canvas->grid) {
        free(canvas);
        return NULL;
    }
    
    for (int i = 0; i < height; i++) {
        canvas->grid[i] = malloc(width * sizeof(char));
        if (!canvas->grid[i]) {
            // Cleanup on failure
            for (int j = 0; j < i; j++) {
                free(canvas->grid[j]);
            }
            free(canvas->grid);
            free(canvas);
            return NULL;
        }
        // Initialize with background
        memset(canvas->grid[i], canvas->background, width);
    }
    
    return canvas;
}

void ascii_2d_canvas_destroy(ASCII2DCanvas* canvas) {
    if (!canvas) return;
    
    if (canvas->grid) {
        for (int i = 0; i < canvas->height; i++) {
            if (canvas->grid[i]) {
                free(canvas->grid[i]);
            }
        }
        free(canvas->grid);
    }
    
    free(canvas);
}

void ascii_2d_canvas_clear(ASCII2DCanvas* canvas) {
    if (!canvas || !canvas->grid) return;
    
    for (int i = 0; i < canvas->height; i++) {
        if (canvas->grid[i]) {
            memset(canvas->grid[i], canvas->background, canvas->width);
        }
    }
}

void ascii_2d_canvas_set_pixel(ASCII2DCanvas* canvas, int x, int y, char value) {
    if (!canvas || !canvas->grid || x < 0 || x >= canvas->width || y < 0 || y >= canvas->height) {
        return;
    }
    
    canvas->grid[y][x] = value;
}

char ascii_2d_canvas_get_pixel(ASCII2DCanvas* canvas, int x, int y) {
    if (!canvas || !canvas->grid || x < 0 || x >= canvas->width || y < 0 || y >= canvas->height) {
        return '\0';
    }
    
    return canvas->grid[y][x];
}

ASCII3DCanvas* ascii_3d_canvas_create(int width, int height, int depth, 
                                      const ArxPoint3D* origin, double scale) {
    if (width <= 0 || height <= 0 || depth <= 0) return NULL;
    
    ASCII3DCanvas* canvas = malloc(sizeof(ASCII3DCanvas));
    if (!canvas) return NULL;
    
    canvas->width = width;
    canvas->height = height;
    canvas->depth = depth;
    canvas->origin = *origin;
    canvas->scale = scale;
    canvas->background = ' ';
    
    // Allocate 3D grid
    canvas->grid = malloc(depth * sizeof(char**));
    if (!canvas->grid) {
        free(canvas);
        return NULL;
    }
    
    for (int z = 0; z < depth; z++) {
        canvas->grid[z] = malloc(height * sizeof(char*));
        if (!canvas->grid[z]) {
            // Cleanup on failure
            for (int k = 0; k < z; k++) {
                for (int j = 0; j < height; j++) {
                    free(canvas->grid[k][j]);
                }
                free(canvas->grid[k]);
            }
            free(canvas->grid);
            free(canvas);
            return NULL;
        }
        
        for (int y = 0; y < height; y++) {
            canvas->grid[z][y] = malloc(width * sizeof(char));
            if (!canvas->grid[z][y]) {
                // Cleanup on failure
                for (int j = 0; j < y; j++) {
                    free(canvas->grid[z][j]);
                }
                free(canvas->grid[z]);
                for (int k = 0; k < z; k++) {
                    for (int j = 0; j < height; j++) {
                        free(canvas->grid[k][j]);
                    }
                    free(canvas->grid[k]);
                }
                free(canvas->grid);
                free(canvas);
                return NULL;
            }
            // Initialize with background
            memset(canvas->grid[z][y], canvas->background, width);
        }
    }
    
    return canvas;
}

void ascii_3d_canvas_destroy(ASCII3DCanvas* canvas) {
    if (!canvas) return;
    
    if (canvas->grid) {
        for (int z = 0; z < canvas->depth; z++) {
            if (canvas->grid[z]) {
                for (int y = 0; y < canvas->height; y++) {
                    if (canvas->grid[z][y]) {
                        free(canvas->grid[z][y]);
                    }
                }
                free(canvas->grid[z]);
            }
        }
        free(canvas->grid);
    }
    
    free(canvas);
}

void ascii_3d_canvas_clear(ASCII3DCanvas* canvas) {
    if (!canvas || !canvas->grid) return;
    
    for (int z = 0; z < canvas->depth; z++) {
        if (canvas->grid[z]) {
            for (int y = 0; y < canvas->height; y++) {
                if (canvas->grid[z][y]) {
                    memset(canvas->grid[z][y], canvas->background, canvas->width);
                }
            }
        }
    }
}

void ascii_3d_canvas_set_voxel(ASCII3DCanvas* canvas, int x, int y, int z, char value) {
    if (!canvas || !canvas->grid || x < 0 || x >= canvas->width || 
        y < 0 || y >= canvas->height || z < 0 || z >= canvas->depth) {
        return;
    }
    
    canvas->grid[z][y][x] = value;
}

char ascii_3d_canvas_get_voxel(ASCII3DCanvas* canvas, int x, int y, int z) {
    if (!canvas || !canvas->grid || x < 0 || x >= canvas->width || 
        y < 0 || y >= canvas->height || z < 0 || z >= canvas->depth) {
        return '\0';
    }
    
    return canvas->grid[z][y][x];
}

// ============================================================================
// Coordinate Conversion
// ============================================================================

bool world_to_canvas_2d(const ArxPoint3D* world_point, const ASCII2DCanvas* canvas,
                        int* canvas_x, int* canvas_y) {
    if (!world_point || !canvas || !canvas_x || !canvas_y) return false;
    
    // Convert world coordinates to canvas coordinates
    double dx = world_point->x - canvas->origin.x;
    double dy = world_point->y - canvas->origin.y;
    
    *canvas_x = (int)(dx * canvas->scale);
    *canvas_y = (int)(dy * canvas->scale);
    
    // Ensure coordinates are within canvas bounds
    if (*canvas_x < 0) *canvas_x = 0;
    if (*canvas_x >= canvas->width) *canvas_x = canvas->width - 1;
    if (*canvas_y < 0) *canvas_y = 0;
    if (*canvas_y >= canvas->height) *canvas_y = canvas->height - 1;
    
    return true;
}

bool world_to_canvas_3d(const ArxPoint3D* world_point, const ASCII3DCanvas* canvas,
                        int* canvas_x, int* canvas_y, int* canvas_z) {
    if (!world_point || !canvas || !canvas_x || !canvas_y || !canvas_z) return false;
    
    // Convert world coordinates to canvas coordinates
    double dx = world_point->x - canvas->origin.x;
    double dy = world_point->y - canvas->origin.y;
    double dz = world_point->z - canvas->origin.z;
    
    *canvas_x = (int)(dx * canvas->scale);
    *canvas_y = (int)(dy * canvas->scale);
    *canvas_z = (int)(dz * canvas->scale);
    
    // Ensure coordinates are within canvas bounds
    if (*canvas_x < 0) *canvas_x = 0;
    if (*canvas_x >= canvas->width) *canvas_x = canvas->width - 1;
    if (*canvas_y < 0) *canvas_y = 0;
    if (*canvas_y >= canvas->height) *canvas_y = canvas->height - 1;
    if (*canvas_z < 0) *canvas_z = 0;
    if (*canvas_z >= canvas->depth) *canvas_z = canvas->depth - 1;
    
    return true;
}

// ============================================================================
// Object Rendering
// ============================================================================

bool render_arx_object_2d(ASCII2DCanvas* canvas, const ArxObject* obj, 
                          const ASCIIRenderOptions* options) {
    if (!canvas || !obj || !options) return false;
    
    ArxGeometry geom;
    if (!arx_object_get_geometry(obj, &geom)) return false;
    
    // Get character for this element type
    char element_char = get_element_char(obj->type, options);
    
    // Convert bounding box to canvas coordinates
    int min_x, min_y, max_x, max_y;
    if (!world_to_canvas_2d(&geom.bounding_box.min, canvas, &min_x, &min_y)) return false;
    if (!world_to_canvas_2d(&geom.bounding_box.max, canvas, &max_x, &max_y)) return false;
    
    // Draw the element as a rectangle
    for (int y = min_y; y <= max_y; y++) {
        for (int x = min_x; x <= max_x; x++) {
            ascii_2d_canvas_set_pixel(canvas, x, y, element_char);
        }
    }
    
    // Add label if requested
    if (options->show_labels && obj->name) {
        int label_x = min_x;
        int label_y = min_y - 1;
        if (label_y >= 0 && label_y < canvas->height) {
            // Simple label placement - just first few characters
            int len = strlen(obj->name);
            int max_len = max_x - min_x + 1;
            if (len > max_len) len = max_len;
            
            for (int i = 0; i < len && (label_x + i) < canvas->width; i++) {
                ascii_2d_canvas_set_pixel(canvas, label_x + i, label_y, obj->name[i]);
            }
        }
    }
    
    return true;
}

bool render_wall_2d(ASCII2DCanvas* canvas, const ArxObject* wall, 
                    const ASCIIRenderOptions* options) {
    if (!canvas || !wall || !options) return false;
    
    ArxGeometry geom;
    if (!arx_object_get_geometry(wall, &geom)) return false;
    
    // Walls are rendered as lines between points
    if (geom.points && geom.point_count >= 2) {
        for (int i = 0; i < geom.point_count - 1; i++) {
            int x1, y1, x2, y2;
            if (world_to_canvas_2d(&geom.points[i], canvas, &x1, &y1) &&
                world_to_canvas_2d(&geom.points[i + 1], canvas, &x2, &y2)) {
                
                // Simple line drawing using Bresenham's algorithm
                int dx = abs(x2 - x1);
                int dy = abs(y2 - y1);
                int sx = x1 < x2 ? 1 : -1;
                int sy = y1 < y2 ? 1 : -1;
                int err = dx - dy;
                
                int x = x1, y = y1;
                while (true) {
                    ascii_2d_canvas_set_pixel(canvas, x, y, options->wall_char);
                    
                    if (x == x2 && y == y2) break;
                    
                    int e2 = 2 * err;
                    if (e2 > -dy) {
                        err -= dy;
                        x += sx;
                    }
                    if (e2 < dx) {
                        err += dx;
                        y += sy;
                    }
                }
            }
        }
    }
    
    return true;
}

bool render_room_2d(ASCII2DCanvas* canvas, const ArxObject* room,
                    const ASCIIRenderOptions* options) {
    if (!canvas || !room || !options) return false;
    
    ArxGeometry geom;
    if (!arx_object_get_geometry(room, &geom)) return false;
    
    // Rooms are rendered as filled areas
    int min_x, min_y, max_x, max_y;
    if (!world_to_canvas_2d(&geom.bounding_box.min, canvas, &min_x, &min_y)) return false;
    if (!world_to_canvas_2d(&geom.bounding_box.max, canvas, &max_x, &max_y)) return false;
    
    // Fill the room area
    for (int y = min_y; y <= max_y; y++) {
        for (int x = min_x; x <= max_x; x++) {
            ascii_2d_canvas_set_pixel(canvas, x, y, options->room_char);
        }
    }
    
    // Add room name as label
    if (options->show_labels && room->name) {
        int center_x = (min_x + max_x) / 2;
        int center_y = (min_y + max_y) / 2;
        
        if (center_x >= 0 && center_x < canvas->width && center_y >= 0 && center_y < canvas->height) {
            int len = strlen(room->name);
            int start_x = center_x - len / 2;
            
            for (int i = 0; i < len && (start_x + i) >= 0 && (start_x + i) < canvas->width; i++) {
                ascii_2d_canvas_set_pixel(canvas, start_x + i, center_y, room->name[i]);
            }
        }
    }
    
    return true;
}

// ============================================================================
// Core ASCII Generation
// ============================================================================

char* generate_2d_floor_plan(ArxObject** objects, int object_count, 
                             const ASCIIRenderOptions* options) {
    if (!objects || object_count <= 0 || !options) return NULL;
    
    // Calculate building bounds
    ArxPoint3D min_bound, max_bound;
    calculate_bounds(objects, object_count, &min_bound, &max_bound);
    
    // Determine canvas size
    double building_width = max_bound.x - min_bound.x;
    double building_height = max_bound.y - min_bound.y;
    
    int canvas_width = (int)(building_width * options->scale);
    int canvas_height = (int)(building_height * options->scale);
    
    // Apply maximum size constraints
    if (options->max_width > 0 && canvas_width > options->max_width) {
        canvas_width = options->max_width;
    }
    if (options->max_height > 0 && canvas_height > options->max_height) {
        canvas_height = options->max_height;
    }
    
    // Create canvas
    ASCII2DCanvas* canvas = ascii_2d_canvas_create(canvas_width, canvas_height, &min_bound, options->scale);
    if (!canvas) return NULL;
    
    // Render all objects
    for (int i = 0; i < object_count; i++) {
        if (objects[i]) {
            render_arx_object_2d(canvas, objects[i], options);
        }
    }
    
    // Convert canvas to string
    char* result = malloc((canvas_width + 1) * canvas_height + 1);
    if (!result) {
        ascii_2d_canvas_destroy(canvas);
        return NULL;
    }
    
    int pos = 0;
    for (int y = 0; y < canvas_height; y++) {
        for (int x = 0; x < canvas_width; x++) {
            result[pos++] = ascii_2d_canvas_get_pixel(canvas, x, y);
        }
        result[pos++] = '\n';
    }
    result[pos] = '\0';
    
    ascii_2d_canvas_destroy(canvas);
    return result;
}

char* generate_3d_building_view(ArxObject** objects, int object_count,
                                const ASCIIRenderOptions* options) {
    if (!objects || object_count <= 0 || !options) return NULL;
    
    // Calculate building bounds
    ArxPoint3D min_bound, max_bound;
    calculate_bounds(objects, object_count, &min_bound, &max_bound);
    
    // Determine canvas size
    double building_width = max_bound.x - min_bound.x;
    double building_height = max_bound.y - min_bound.y;
    double building_depth = max_bound.z - min_bound.z;
    
    int canvas_width = (int)(building_width * options->scale);
    int canvas_height = (int)(building_height * options->scale);
    int canvas_depth = (int)(building_depth * options->scale);
    
    // Apply maximum size constraints
    if (options->max_width > 0 && canvas_width > options->max_width) {
        canvas_width = options->max_width;
    }
    if (options->max_height > 0 && canvas_height > options->max_height) {
        canvas_height = options->max_height;
    }
    
    // Create canvas
    ASCII3DCanvas* canvas = ascii_3d_canvas_create(canvas_width, canvas_height, canvas_depth, &min_bound, options->scale);
    if (!canvas) return NULL;
    
    // Render all objects in 3D
    for (int i = 0; i < object_count; i++) {
        if (objects[i]) {
            render_arx_object_3d(canvas, objects[i], options);
        }
    }
    
    // Convert 3D canvas to string (showing each floor)
    int total_size = (canvas_width + 1) * canvas_height * canvas_depth + canvas_depth + 1;
    char* result = malloc(total_size);
    if (!result) {
        ascii_3d_canvas_destroy(canvas);
        return NULL;
    }
    
    int pos = 0;
    for (int z = 0; z < canvas_depth; z++) {
        // Add floor separator
        if (z > 0) {
            for (int x = 0; x < canvas_width; x++) {
                result[pos++] = '-';
            }
            result[pos++] = '\n';
        }
        
        // Add floor label
        char floor_label[32];
        snprintf(floor_label, sizeof(floor_label), "Floor %d", z);
        int label_len = strlen(floor_label);
        for (int i = 0; i < label_len && i < canvas_width; i++) {
            result[pos++] = floor_label[i];
        }
        result[pos++] = '\n';
        
        // Add floor content
        for (int y = 0; y < canvas_height; y++) {
            for (int x = 0; x < canvas_width; x++) {
                result[pos++] = ascii_3d_canvas_get_voxel(canvas, x, y, z);
            }
            result[pos++] = '\n';
        }
    }
    result[pos] = '\0';
    
    ascii_3d_canvas_destroy(canvas);
    return result;
}

bool generate_both_representations(ArxObject** objects, int object_count,
                                  const ASCIIRenderOptions* options,
                                  char** floor_plan_2d, char** building_3d) {
    if (!objects || object_count <= 0 || !options || !floor_plan_2d || !building_3d) {
        return false;
    }
    
    *floor_plan_2d = generate_2d_floor_plan(objects, object_count, options);
    *building_3d = generate_3d_building_view(objects, object_count, options);
    
    return (*floor_plan_2d != NULL && *building_3d != NULL);
}

// ============================================================================
// Utility Functions
// ============================================================================

char get_ascii_char_for_element_type(ArxObjectType type, const ASCIIRenderOptions* options) {
    if (!options) return '#';
    return get_element_char(type, options);
}

bool is_ascii_char_valid(char c) {
    return (c >= 32 && c <= 126) || c == '\n' || c == '\t';
}

char get_ascii_char_for_confidence(double confidence) {
    if (confidence >= 0.9) return '█';      // High confidence
    if (confidence >= 0.7) return '▓';      // Medium-high confidence
    if (confidence >= 0.5) return '▒';      // Medium confidence
    if (confidence >= 0.3) return '░';      // Low-medium confidence
    return '·';                             // Low confidence
}

// ============================================================================
// Default Options
// ============================================================================

ASCIIRenderOptions* get_default_ascii_options(void) {
    ASCIIRenderOptions* options = malloc(sizeof(ASCIIRenderOptions));
    if (!options) return NULL;
    
    options->show_labels = true;
    options->show_coordinates = false;
    options->show_legend = true;
    options->optimize_spacing = true;
    options->max_width = 120;
    options->max_height = 40;
    options->wall_char = '#';
    options->door_char = 'D';
    options->window_char = 'W';
    options->room_char = ' ';
    options->furniture_char = 'F';
    options->mep_char = 'M';
    
    return options;
}

void free_ascii_options(ASCIIRenderOptions* options) {
    if (options) {
        free(options);
    }
}

// ============================================================================
// Placeholder Functions (to be implemented)
// ============================================================================

bool render_arx_object_3d(ASCII3DCanvas* canvas, const ArxObject* obj,
                          const ASCIIRenderOptions* options) {
    // TODO: Implement 3D rendering
    return false;
}

bool render_door_2d(ASCII2DCanvas* canvas, const ArxObject* door,
                    const ASCIIRenderOptions* options) {
    // TODO: Implement door rendering
    return false;
}

bool render_window_2d(ASCII2DCanvas* canvas, const ArxObject* window,
                      const ASCIIRenderOptions* options) {
    // TODO: Implement window rendering
    return false;
}

bool render_mep_element_2d(ASCII2DCanvas* canvas, const ArxObject* element,
                           const ASCIIRenderOptions* options) {
    // TODO: Implement MEP element rendering
    return false;
}

bool calculate_building_layout(ArxObject** objects, int object_count,
                              ArxPoint3D* layout_center, double* layout_bounds) {
    // TODO: Implement layout calculation
    return false;
}

char* generate_navigation_grid(ArxObject** objects, int object_count,
                               const ArxPoint3D* start_point,
                               const ArxPoint3D* end_point) {
    // TODO: Implement navigation grid
    return NULL;
}

bool find_shortest_path(ArxObject** objects, int object_count,
                        const ArxPoint3D* start, const ArxPoint3D* end,
                        ArxPoint3D** path, int* path_length) {
    // TODO: Implement pathfinding
    return false;
}

char* optimize_ascii_output(const char* ascii_input, int max_width, int max_height) {
    // TODO: Implement ASCII optimization
    return NULL;
}

char* add_ascii_labels(const char* ascii_input, ArxObject** objects, int object_count) {
    // TODO: Implement label addition
    return NULL;
}

char* generate_ascii_legend(const ASCIIRenderOptions* options) {
    // TODO: Implement legend generation
    return NULL;
}

char* format_ascii_for_terminal(const char* ascii_input) {
    // TODO: Implement terminal formatting
    return NULL;
}

char* format_ascii_for_mobile(const char* ascii_input) {
    // TODO: Implement mobile formatting
    return NULL;
}

char* format_ascii_for_print(const char* ascii_input) {
    // TODO: Implement print formatting
    return NULL;
}

bool canvas_to_world_2d(int canvas_x, int canvas_y, const ASCII2DCanvas* canvas,
                        ArxPoint3D* world_point) {
    // TODO: Implement reverse coordinate conversion
    return false;
}

bool canvas_to_world_3d(int canvas_x, int canvas_y, int canvas_z, const ASCII3DCanvas* canvas,
                        ArxPoint3D* world_point) {
    // TODO: Implement reverse coordinate conversion
    return false;
}
