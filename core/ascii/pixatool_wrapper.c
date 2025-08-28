#include "pixatool_engine.h"
#include "arxobject.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>

// Convert ArxObject to pixel data for rendering
void arxobject_to_pixels(ASCIICanvas* canvas, ArxObject* obj, float scale) {
    if (!canvas || !obj) return;
    
    // Convert world coordinates to canvas coordinates
    int x = (int)(obj->x * scale);
    int y = (int)(obj->y * scale);
    
    // Determine material type based on ArxObject type
    MaterialType material = MATERIAL_EMPTY;
    
    if (strstr(obj->path, "wall")) {
        material = MATERIAL_WALL;
    } else if (strstr(obj->path, "door")) {
        material = MATERIAL_DOOR;
    } else if (strstr(obj->path, "window")) {
        material = MATERIAL_WINDOW;
    } else if (strstr(obj->path, "electrical") || strstr(obj->path, "panel")) {
        material = MATERIAL_PANEL;
    } else if (strstr(obj->path, "outlet")) {
        material = MATERIAL_OUTLET;
    } else if (strstr(obj->path, "equipment")) {
        material = MATERIAL_EQUIPMENT;
    } else if (strstr(obj->path, "room")) {
        // Determine room type
        if (strstr(obj->path, "office")) {
            material = MATERIAL_ROOM_OFFICE;
        } else if (strstr(obj->path, "corridor") || strstr(obj->path, "hall")) {
            material = MATERIAL_ROOM_CORRIDOR;
        } else if (strstr(obj->path, "classroom") || strstr(obj->path, "class")) {
            material = MATERIAL_ROOM_CLASSROOM;
        } else {
            material = MATERIAL_ROOM_LARGE;
        }
    }
    
    // Render based on object type
    if (material == MATERIAL_WALL) {
        // Calculate wall endpoints
        int x2 = x + (int)(obj->width * scale);
        int y2 = y + (int)(obj->height * scale);
        
        // Draw wall perimeter
        render_wall(canvas, x, y, x2, y, obj->confidence);
        render_wall(canvas, x2, y, x2, y2, obj->confidence);
        render_wall(canvas, x2, y2, x, y2, obj->confidence);
        render_wall(canvas, x, y2, x, y, obj->confidence);
    } else if (material == MATERIAL_DOOR) {
        int width = (int)(obj->width * scale);
        int horizontal = (obj->width > obj->height) ? 1 : 0;
        render_door(canvas, x, y, width, horizontal);
    } else if (material >= MATERIAL_ROOM_OFFICE && material <= MATERIAL_ROOM_LARGE) {
        // Fill room area
        int width = (int)(obj->width * scale);
        int height = (int)(obj->height * scale);
        fill_room(canvas, x, y, width, height, material);
    } else {
        // Render as equipment
        render_equipment(canvas, x, y, material);
    }
}

// Render floor plan from ArxObjects
char* render_floor_plan_pixatool(ArxObject** objects, int count, int width, int height, float scale) {
    // Create canvas
    ASCIICanvas* canvas = create_ascii_canvas(width, height);
    canvas->scale_factor = scale;
    
    // Clear canvas with empty material
    for (int i = 0; i < width * height; i++) {
        canvas->render_buffer[i].material_type = MATERIAL_EMPTY;
        canvas->render_buffer[i].depth = 0.0;
        canvas->render_buffer[i].luminance = 0.0;
    }
    
    // Render each object
    for (int i = 0; i < count; i++) {
        if (objects[i]) {
            arxobject_to_pixels(canvas, objects[i], scale);
        }
    }
    
    // Apply rendering pipeline
    render_to_ascii(canvas);
    
    // Copy result
    char* result = (char*)malloc((width * height + height + 1) * sizeof(char));
    int pos = 0;
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            result[pos++] = canvas->ascii_buffer[y * width + x];
        }
        result[pos++] = '\n';
    }
    result[pos] = '\0';
    
    // Clean up
    destroy_canvas(canvas);
    
    return result;
}

// Render with specific zoom level and material focus
char* render_zoom_level_pixatool(ArxObject** objects, int count, int width, int height, int zoom_level) {
    // Scale factors for different zoom levels (from vision.md)
    float scales[] = {
        0.01,    // Campus:    1 char = 100m
        0.1,     // Building:  1 char = 10m
        1.0,     // Floor:     1 char = 1m
        1.0,     // Room:      1 char = 1m
        10.0,    // Equipment: 1 char = 10cm
        100.0,   // Component: 1 char = 1cm
        1000.0   // Chip:      1 char = 1mm
    };
    
    float scale = scales[zoom_level % 7];
    
    // Create canvas
    ASCIICanvas* canvas = create_ascii_canvas(width, height);
    canvas->scale_factor = scale;
    
    // Set depth range based on zoom level
    canvas->depth_range_min = 0.0;
    canvas->depth_range_max = 100.0 / scale;
    
    // Clear canvas
    memset(canvas->render_buffer, 0, width * height * sizeof(PixelData));
    
    // Filter and render objects appropriate for zoom level
    for (int i = 0; i < count; i++) {
        if (!objects[i]) continue;
        
        int should_render = 0;
        
        switch (zoom_level) {
            case 0: // Campus - only buildings
                should_render = strstr(objects[i]->path, "building") != NULL;
                break;
            case 1: // Building - floors and major structures
                should_render = strstr(objects[i]->path, "floor") != NULL ||
                               strstr(objects[i]->path, "building") != NULL;
                break;
            case 2: // Floor - rooms and walls
            case 3: // Room
                should_render = strstr(objects[i]->path, "room") != NULL ||
                               strstr(objects[i]->path, "wall") != NULL ||
                               strstr(objects[i]->path, "door") != NULL ||
                               strstr(objects[i]->path, "window") != NULL;
                break;
            case 4: // Equipment
                should_render = strstr(objects[i]->path, "equipment") != NULL ||
                               strstr(objects[i]->path, "panel") != NULL ||
                               strstr(objects[i]->path, "outlet") != NULL;
                break;
            case 5: // Component
                should_render = strstr(objects[i]->path, "circuit") != NULL ||
                               strstr(objects[i]->path, "component") != NULL;
                break;
            case 6: // Chip
                should_render = strstr(objects[i]->path, "chip") != NULL ||
                               strstr(objects[i]->path, "sensor") != NULL;
                break;
            default:
                should_render = 1;
        }
        
        if (should_render) {
            arxobject_to_pixels(canvas, objects[i], scale);
        }
    }
    
    // Apply rendering pipeline
    render_to_ascii(canvas);
    
    // Build result string with zoom-specific formatting
    int buffer_size = (width * height * 2) + (height * 2) + 1024;
    char* result = (char*)calloc(buffer_size, sizeof(char));
    int pos = 0;
    
    // Add header based on zoom level
    const char* zoom_names[] = {
        "Campus", "Building", "Floor", "Room",
        "Equipment", "Component", "Chip"
    };
    
    pos += sprintf(result + pos, "╔");
    for (int i = 0; i < width - 2; i++) {
        pos += sprintf(result + pos, "═");
    }
    pos += sprintf(result + pos, "╗\n");
    
    pos += sprintf(result + pos, "║ Zoom: %s (1 char = ", zoom_names[zoom_level % 7]);
    
    switch (zoom_level) {
        case 0: pos += sprintf(result + pos, "100m"); break;
        case 1: pos += sprintf(result + pos, "10m"); break;
        case 2:
        case 3: pos += sprintf(result + pos, "1m"); break;
        case 4: pos += sprintf(result + pos, "10cm"); break;
        case 5: pos += sprintf(result + pos, "1cm"); break;
        case 6: pos += sprintf(result + pos, "1mm"); break;
    }
    
    // Pad to width
    int header_len = strlen(result + pos - width);
    for (int i = header_len; i < width - 3; i++) {
        pos += sprintf(result + pos, " ");
    }
    pos += sprintf(result + pos, "║\n");
    
    // Add separator
    pos += sprintf(result + pos, "╠");
    for (int i = 0; i < width - 2; i++) {
        pos += sprintf(result + pos, "═");
    }
    pos += sprintf(result + pos, "╣\n");
    
    // Add canvas content
    for (int y = 0; y < height; y++) {
        pos += sprintf(result + pos, "║");
        for (int x = 0; x < width - 2; x++) {
            if (x < canvas->width && y < canvas->height) {
                result[pos++] = canvas->ascii_buffer[y * canvas->width + x];
            } else {
                result[pos++] = ' ';
            }
        }
        pos += sprintf(result + pos, "║\n");
    }
    
    // Add footer
    pos += sprintf(result + pos, "╚");
    for (int i = 0; i < width - 2; i++) {
        pos += sprintf(result + pos, "═");
    }
    pos += sprintf(result + pos, "╝\n");
    
    result[pos] = '\0';
    
    // Clean up
    destroy_canvas(canvas);
    
    return result;
}