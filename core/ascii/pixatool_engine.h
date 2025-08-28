#ifndef PIXATOOL_ENGINE_H
#define PIXATOOL_ENGINE_H

#include <stdint.h>

// Material types for different building elements
typedef enum {
    MATERIAL_EMPTY = 0,
    MATERIAL_WALL,
    MATERIAL_DOOR,
    MATERIAL_WINDOW,
    MATERIAL_EQUIPMENT,
    MATERIAL_OUTLET,
    MATERIAL_PANEL,
    MATERIAL_ROOM_OFFICE,
    MATERIAL_ROOM_CORRIDOR,
    MATERIAL_ROOM_CLASSROOM,
    MATERIAL_ROOM_LARGE
} MaterialType;

// Core data structures
typedef struct {
    float depth;         // Z-buffer depth value
    float luminance;     // Brightness 0.0-1.0
    float edge_strength; // Edge detection result
    int material_type;   // Wall, door, equipment, etc.
    float normal_x, normal_y, normal_z; // Surface normal
} PixelData;

typedef struct {
    char character;      // ASCII character to display
    float density;       // Character visual density 0.0-1.0
    int is_structural;   // 1 for walls/structure, 0 for details
    int is_edge;         // 1 for edges/boundaries
} ASCIICharacterSet;

typedef struct {
    int width, height;
    char* ascii_buffer;
    PixelData* render_buffer;
    float scale_factor;
    float depth_range_min, depth_range_max;
} ASCIICanvas;

// Canvas management
ASCIICanvas* create_ascii_canvas(int width, int height);
void destroy_canvas(ASCIICanvas* canvas);

// Rendering pipeline
void render_to_ascii(ASCIICanvas* canvas);
void detect_edges(ASCIICanvas* canvas);
void apply_antialiasing(ASCIICanvas* canvas);
void apply_dithering(ASCIICanvas* canvas);

// Drawing primitives
void render_wall(ASCIICanvas* canvas, int x1, int y1, int x2, int y2, float depth);
void render_door(ASCIICanvas* canvas, int x, int y, int width, int horizontal);
void render_equipment(ASCIICanvas* canvas, int x, int y, MaterialType type);
void fill_room(ASCIICanvas* canvas, int x, int y, int width, int height, MaterialType room_type);

// Character selection
char select_edge_char(ASCIICanvas* canvas, int x, int y);
char depth_to_ascii(float depth, float edge_strength, MaterialType material);

// Output
void print_canvas(ASCIICanvas* canvas);

#endif // PIXATOOL_ENGINE_H