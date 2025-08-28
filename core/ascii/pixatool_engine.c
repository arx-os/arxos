/*
 * Arxos ASCII-BIM Engine - Pixatool-Inspired Implementation
 * High-performance 3D building model to ASCII conversion
 * Optimized for sub-10ms building plan rendering
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>

// Core data structures for 3D -> ASCII conversion
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

// Material types enum
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

// Pre-computed ASCII character sets optimized for building plans
static const ASCIICharacterSet BUILDING_CHARSET[] = {
    // Structural elements (walls, foundations) - using simple ASCII
    {'#', 1.0, 1, 0},   // Solid wall - maximum density
    {'%', 0.8, 1, 0},   // Thick wall - high density  
    {'=', 0.6, 1, 0},   // Medium wall - medium density
    {'-', 0.4, 1, 0},   // Thin wall - low density
    
    // Edge/boundary characters - using ASCII approximations
    {'|', 0.7, 0, 1},   // Vertical edge
    {'-', 0.7, 0, 1},   // Horizontal edge
    {'+', 0.7, 0, 1},   // Corner/junction
    {'L', 0.7, 0, 1},   // L-corner
    {'J', 0.7, 0, 1},   // J-corner
    {'7', 0.7, 0, 1},   // 7-corner
    {'T', 0.7, 0, 1},   // T-junction
    {'_', 0.7, 0, 1},   // Bottom edge
    {'^', 0.7, 0, 1},   // Top junction
    {'<', 0.7, 0, 1},   // Left junction
    {'>', 0.7, 0, 1},   // Right junction
    
    // Doors
    {'D', 0.7, 0, 0},   // Double door
    {'d', 0.6, 0, 0},   // Single door
    {'/', 0.6, 0, 0},   // Door swing
    
    // Windows
    {'=', 0.3, 0, 0},   // Window horizontal
    {'|', 0.3, 0, 0},   // Window vertical
    {'W', 0.3, 0, 0},   // Window marker
    
    // Equipment and details
    {'@', 0.9, 0, 0},   // Electrical panel
    {'&', 0.8, 0, 0},   // Junction box
    {'o', 0.5, 0, 0},   // Outlet/fixture
    {'O', 0.6, 0, 0},   // Equipment center
    
    // Room fill patterns
    {':', 0.3, 0, 0},   // Room interior - classroom
    {'%', 0.4, 0, 0},   // Room interior - office
    {'.', 0.2, 0, 0},   // Room interior - corridor
    {'*', 0.1, 0, 0},   // Room interior - large space
    {' ', 0.0, 0, 0},   // Empty space
};

// Material-specific character mapping - using ASCII
static const char MATERIAL_CHARS[][4] = {
    [MATERIAL_EMPTY] = {' ', ' ', ' ', ' '},
    [MATERIAL_WALL] = {'#', '%', '=', '-'},
    [MATERIAL_DOOR] = {'D', 'd', '/', '\\'},
    [MATERIAL_WINDOW] = {'=', '=', '=', '='},
    [MATERIAL_EQUIPMENT] = {'@', '&', 'o', 'O'},
    [MATERIAL_OUTLET] = {'o', 'o', 'O', 'O'},
    [MATERIAL_PANEL] = {'@', '@', '&', '&'},
    [MATERIAL_ROOM_OFFICE] = {'%', '.', '*', ' '},
    [MATERIAL_ROOM_CORRIDOR] = {'.', '*', ' ', ' '},
    [MATERIAL_ROOM_CLASSROOM] = {':', '*', ' ', ' '},
    [MATERIAL_ROOM_LARGE] = {'*', ' ', ' ', ' '}
};

// Edge detection kernel (Sobel operator)
static const float SOBEL_X[3][3] = {
    {-1, 0, 1},
    {-2, 0, 2},
    {-1, 0, 1}
};

static const float SOBEL_Y[3][3] = {
    {-1, -2, -1},
    { 0,  0,  0},
    { 1,  2,  1}
};

// Initialize ASCII canvas
ASCIICanvas* create_ascii_canvas(int width, int height) {
    ASCIICanvas* canvas = (ASCIICanvas*)malloc(sizeof(ASCIICanvas));
    canvas->width = width;
    canvas->height = height;
    canvas->ascii_buffer = (char*)calloc(width * height + 1, sizeof(char));
    canvas->render_buffer = (PixelData*)calloc(width * height, sizeof(PixelData));
    canvas->scale_factor = 1.0;
    canvas->depth_range_min = 0.0;
    canvas->depth_range_max = 100.0;
    return canvas;
}

// Apply Sobel edge detection
void detect_edges(ASCIICanvas* canvas) {
    PixelData* temp = (PixelData*)malloc(canvas->width * canvas->height * sizeof(PixelData));
    memcpy(temp, canvas->render_buffer, canvas->width * canvas->height * sizeof(PixelData));
    
    for (int y = 1; y < canvas->height - 1; y++) {
        for (int x = 1; x < canvas->width - 1; x++) {
            float gx = 0, gy = 0;
            
            // Apply Sobel operator
            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    int idx = (y + dy) * canvas->width + (x + dx);
                    float depth = temp[idx].depth;
                    gx += depth * SOBEL_X[dy + 1][dx + 1];
                    gy += depth * SOBEL_Y[dy + 1][dx + 1];
                }
            }
            
            // Calculate edge strength
            float edge_strength = sqrt(gx * gx + gy * gy);
            canvas->render_buffer[y * canvas->width + x].edge_strength = edge_strength;
        }
    }
    
    free(temp);
}

// Select appropriate edge character based on connectivity
char select_edge_char(ASCIICanvas* canvas, int x, int y) {
    if (x <= 0 || x >= canvas->width - 1 || y <= 0 || y >= canvas->height - 1) {
        return '|';
    }
    
    PixelData* buffer = canvas->render_buffer;
    int idx = y * canvas->width + x;
    
    // Check connectivity in 4 directions
    int top = (y > 0) && (buffer[idx - canvas->width].edge_strength > 0.3);
    int bottom = (y < canvas->height - 1) && (buffer[idx + canvas->width].edge_strength > 0.3);
    int left = (x > 0) && (buffer[idx - 1].edge_strength > 0.3);
    int right = (x < canvas->width - 1) && (buffer[idx + 1].edge_strength > 0.3);
    
    // Select appropriate ASCII character
    if (top && bottom && left && right) return '+';
    if (top && bottom && left) return '+';
    if (top && bottom && right) return '+';
    if (top && left && right) return '+';
    if (bottom && left && right) return '+';
    if (top && bottom) return '|';
    if (left && right) return '-';
    if (top && right) return 'L';
    if (top && left) return 'J';
    if (bottom && right) return 'r';
    if (bottom && left) return '7';
    
    return '*';
}

// Map depth and material to ASCII character
char depth_to_ascii(float depth, float edge_strength, MaterialType material) {
    // Strong edges get box-drawing characters
    if (edge_strength > 0.5) {
        return '|';  // Will be refined by select_edge_char
    }
    
    // Map depth to density level (0-3)
    float normalized_depth = fmin(fmax(depth, 0.0), 1.0);
    int density_level = (int)(normalized_depth * 3.999);
    
    // Return material-specific character
    return MATERIAL_CHARS[material][density_level];
}

// Apply anti-aliasing using bilinear interpolation
void apply_antialiasing(ASCIICanvas* canvas) {
    PixelData* temp = (PixelData*)malloc(canvas->width * canvas->height * sizeof(PixelData));
    memcpy(temp, canvas->render_buffer, canvas->width * canvas->height * sizeof(PixelData));
    
    for (int y = 1; y < canvas->height - 1; y++) {
        for (int x = 1; x < canvas->width - 1; x++) {
            int idx = y * canvas->width + x;
            float sum_luminance = 0;
            float sum_depth = 0;
            int count = 0;
            
            // Sample 3x3 neighborhood
            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    int sample_idx = (y + dy) * canvas->width + (x + dx);
                    float weight = (dx == 0 && dy == 0) ? 2.0 : 1.0;
                    sum_luminance += temp[sample_idx].luminance * weight;
                    sum_depth += temp[sample_idx].depth * weight;
                    count += weight;
                }
            }
            
            canvas->render_buffer[idx].luminance = sum_luminance / count;
            canvas->render_buffer[idx].depth = sum_depth / count;
        }
    }
    
    free(temp);
}

// Apply ordered dithering for smooth gradients
void apply_dithering(ASCIICanvas* canvas) {
    // 4x4 Bayer matrix for ordered dithering
    static const float BAYER_MATRIX[4][4] = {
        { 0.0/16,  8.0/16,  2.0/16, 10.0/16},
        {12.0/16,  4.0/16, 14.0/16,  6.0/16},
        { 3.0/16, 11.0/16,  1.0/16,  9.0/16},
        {15.0/16,  7.0/16, 13.0/16,  5.0/16}
    };
    
    for (int y = 0; y < canvas->height; y++) {
        for (int x = 0; x < canvas->width; x++) {
            int idx = y * canvas->width + x;
            float threshold = BAYER_MATRIX[y % 4][x % 4];
            
            // Apply dithering to luminance
            float luminance = canvas->render_buffer[idx].luminance;
            if (luminance > 0.1 && luminance < 0.9) {
                luminance += (threshold - 0.5) * 0.2;
                canvas->render_buffer[idx].luminance = fmin(fmax(luminance, 0.0), 1.0);
            }
        }
    }
}

// Main rendering pipeline
void render_to_ascii(ASCIICanvas* canvas) {
    // Step 1: Edge detection
    detect_edges(canvas);
    
    // Step 2: Anti-aliasing
    apply_antialiasing(canvas);
    
    // Step 3: Dithering
    apply_dithering(canvas);
    
    // Step 4: Convert to ASCII
    for (int y = 0; y < canvas->height; y++) {
        for (int x = 0; x < canvas->width; x++) {
            int idx = y * canvas->width + x;
            PixelData* pixel = &canvas->render_buffer[idx];
            
            char ascii_char;
            
            // Strong edges get special treatment
            if (pixel->edge_strength > 0.5) {
                ascii_char = select_edge_char(canvas, x, y);
            } else {
                // Use material-specific character based on depth
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
}

// Render a wall segment
void render_wall(ASCIICanvas* canvas, int x1, int y1, int x2, int y2, float depth) {
    // Bresenham's line algorithm
    int dx = abs(x2 - x1);
    int dy = abs(y2 - y1);
    int sx = (x1 < x2) ? 1 : -1;
    int sy = (y1 < y2) ? 1 : -1;
    int err = dx - dy;
    
    while (1) {
        if (x1 >= 0 && x1 < canvas->width && y1 >= 0 && y1 < canvas->height) {
            int idx = y1 * canvas->width + x1;
            canvas->render_buffer[idx].depth = depth;
            canvas->render_buffer[idx].material_type = MATERIAL_WALL;
            canvas->render_buffer[idx].luminance = 0.8;
        }
        
        if (x1 == x2 && y1 == y2) break;
        
        int e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x1 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y1 += sy;
        }
    }
}

// Render a door
void render_door(ASCIICanvas* canvas, int x, int y, int width, int horizontal) {
    if (x >= 0 && x < canvas->width && y >= 0 && y < canvas->height) {
        int idx = y * canvas->width + x;
        canvas->render_buffer[idx].depth = 0.5;
        canvas->render_buffer[idx].material_type = MATERIAL_DOOR;
        canvas->render_buffer[idx].luminance = 0.6;
        
        // Extend door representation
        if (horizontal && width > 0) {
            for (int i = 1; i < width && x + i < canvas->width; i++) {
                int door_idx = y * canvas->width + x + i;
                canvas->render_buffer[door_idx].depth = 0.5;
                canvas->render_buffer[door_idx].material_type = MATERIAL_DOOR;
                canvas->render_buffer[door_idx].luminance = 0.6;
            }
        }
    }
}

// Render equipment
void render_equipment(ASCIICanvas* canvas, int x, int y, MaterialType type) {
    if (x >= 0 && x < canvas->width && y >= 0 && y < canvas->height) {
        int idx = y * canvas->width + x;
        canvas->render_buffer[idx].depth = 0.7;
        canvas->render_buffer[idx].material_type = type;
        canvas->render_buffer[idx].luminance = 0.9;
    }
}

// Fill room with pattern
void fill_room(ASCIICanvas* canvas, int x, int y, int width, int height, MaterialType room_type) {
    for (int dy = 0; dy < height; dy++) {
        for (int dx = 0; dx < width; dx++) {
            int px = x + dx;
            int py = y + dy;
            if (px >= 0 && px < canvas->width && py >= 0 && py < canvas->height) {
                int idx = py * canvas->width + px;
                // Only fill if empty
                if (canvas->render_buffer[idx].material_type == MATERIAL_EMPTY) {
                    canvas->render_buffer[idx].depth = 0.2;
                    canvas->render_buffer[idx].material_type = room_type;
                    canvas->render_buffer[idx].luminance = 0.3;
                }
            }
        }
    }
}

// Print ASCII canvas to terminal
void print_canvas(ASCIICanvas* canvas) {
    for (int y = 0; y < canvas->height; y++) {
        for (int x = 0; x < canvas->width; x++) {
            putchar(canvas->ascii_buffer[y * canvas->width + x]);
        }
        putchar('\n');
    }
}

// Clean up
void destroy_canvas(ASCIICanvas* canvas) {
    if (canvas) {
        free(canvas->ascii_buffer);
        free(canvas->render_buffer);
        free(canvas);
    }
}