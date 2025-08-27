// arxobject_bridge.c - Implementation of CGO bridge
#include "arxobject_bridge.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

// ============================================================================
// Internal State
// ============================================================================

// Simple in-memory storage for demo (replace with actual C core)
typedef struct ArxObjectNode {
    ArxObject* obj;
    struct ArxObjectNode* next;
} ArxObjectNode;

static ArxObjectNode* object_list = NULL;
static uint64_t next_id = 1;
static char last_error[1024] = {0};
static int log_level = 2; // Default to warnings

// Performance tracking
static struct {
    uint64_t total_queries;
    uint64_t total_creates;
    uint64_t total_updates;
    double total_query_time_ms;
    double total_create_time_ms;
    double total_update_time_ms;
} perf_stats = {0};

// ============================================================================
// Helper Functions
// ============================================================================

static void set_error(const char* msg) {
    strncpy(last_error, msg, sizeof(last_error) - 1);
    last_error[sizeof(last_error) - 1] = '\0';
}

static double get_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1000000.0;
}

static char* strdup_safe(const char* s) {
    if (!s) return NULL;
    char* copy = malloc(strlen(s) + 1);
    if (copy) strcpy(copy, s);
    return copy;
}

// ============================================================================
// Initialization and Cleanup
// ============================================================================

ArxResult* arx_initialize(const char* config_json) {
    ArxResult* result = malloc(sizeof(ArxResult));
    result->success = true;
    result->message = strdup_safe("ArxObject system initialized");
    result->data = NULL;
    
    // Reset state
    object_list = NULL;
    next_id = 1;
    memset(&perf_stats, 0, sizeof(perf_stats));
    
    return result;
}

void arx_cleanup(void) {
    // Free all objects
    ArxObjectNode* current = object_list;
    while (current) {
        ArxObjectNode* next = current->next;
        arx_object_free(current->obj);
        free(current);
        current = next;
    }
    object_list = NULL;
}

// ============================================================================
// Object CRUD Operations
// ============================================================================

ArxObject* arx_object_create(
    const char* name,
    const char* path,
    ArxObjectType type,
    int32_t x_mm,
    int32_t y_mm,
    int32_t z_mm
) {
    double start_time = get_time_ms();
    
    ArxObject* obj = calloc(1, sizeof(ArxObject));
    if (!obj) {
        set_error("Failed to allocate memory for ArxObject");
        return NULL;
    }
    
    obj->id = next_id++;
    obj->name = strdup_safe(name);
    obj->path = strdup_safe(path);
    obj->obj_type = type;
    obj->world_x_mm = x_mm;
    obj->world_y_mm = y_mm;
    obj->world_z_mm = z_mm;
    obj->confidence = 0.5; // Default confidence
    obj->is_validated = false;
    
    // Default dimensions based on type
    switch (type) {
        case ARX_TYPE_WALL:
            obj->width_mm = 3000;  // 3m
            obj->height_mm = 2400; // 2.4m
            obj->depth_mm = 200;   // 20cm
            break;
        case ARX_TYPE_DOOR:
            obj->width_mm = 900;   // 90cm
            obj->height_mm = 2100; // 2.1m
            obj->depth_mm = 50;    // 5cm
            break;
        case ARX_TYPE_WINDOW:
            obj->width_mm = 1200;  // 1.2m
            obj->height_mm = 1500; // 1.5m
            obj->depth_mm = 100;   // 10cm
            break;
        default:
            obj->width_mm = 1000;
            obj->height_mm = 1000;
            obj->depth_mm = 1000;
    }
    
    // Add to list
    ArxObjectNode* node = malloc(sizeof(ArxObjectNode));
    node->obj = obj;
    node->next = object_list;
    object_list = node;
    
    // Update performance stats
    double elapsed = get_time_ms() - start_time;
    perf_stats.total_creates++;
    perf_stats.total_create_time_ms += elapsed;
    
    return obj;
}

ArxObject* arx_object_get(uint64_t id) {
    ArxObjectNode* current = object_list;
    while (current) {
        if (current->obj->id == id) {
            return current->obj;
        }
        current = current->next;
    }
    set_error("Object not found");
    return NULL;
}

ArxResult* arx_object_update(ArxObject* obj) {
    double start_time = get_time_ms();
    
    ArxResult* result = malloc(sizeof(ArxResult));
    
    // Find and update object
    ArxObjectNode* current = object_list;
    while (current) {
        if (current->obj->id == obj->id) {
            // Update fields (shallow copy for now)
            current->obj->world_x_mm = obj->world_x_mm;
            current->obj->world_y_mm = obj->world_y_mm;
            current->obj->world_z_mm = obj->world_z_mm;
            current->obj->confidence = obj->confidence;
            current->obj->is_validated = obj->is_validated;
            
            result->success = true;
            result->message = strdup_safe("Object updated successfully");
            
            // Update performance stats
            double elapsed = get_time_ms() - start_time;
            perf_stats.total_updates++;
            perf_stats.total_update_time_ms += elapsed;
            
            return result;
        }
        current = current->next;
    }
    
    result->success = false;
    result->message = strdup_safe("Object not found");
    return result;
}

ArxResult* arx_object_delete(uint64_t id) {
    ArxResult* result = malloc(sizeof(ArxResult));
    
    ArxObjectNode* prev = NULL;
    ArxObjectNode* current = object_list;
    
    while (current) {
        if (current->obj->id == id) {
            if (prev) {
                prev->next = current->next;
            } else {
                object_list = current->next;
            }
            
            arx_object_free(current->obj);
            free(current);
            
            result->success = true;
            result->message = strdup_safe("Object deleted successfully");
            return result;
        }
        prev = current;
        current = current->next;
    }
    
    result->success = false;
    result->message = strdup_safe("Object not found");
    return result;
}

void arx_object_free(ArxObject* obj) {
    if (!obj) return;
    
    free(obj->name);
    free(obj->path);
    free(obj->child_ids);
    free(obj->properties_json);
    free(obj->metadata_json);
    free(obj);
}

// ============================================================================
// Query Operations
// ============================================================================

ArxQueryResult* arx_query_by_path(const char* path_pattern) {
    double start_time = get_time_ms();
    
    ArxQueryResult* result = calloc(1, sizeof(ArxQueryResult));
    
    // Count matching objects
    size_t count = 0;
    ArxObjectNode* current = object_list;
    while (current) {
        if (current->obj->path && strstr(current->obj->path, path_pattern)) {
            count++;
        }
        current = current->next;
    }
    
    // Allocate array
    result->objects = calloc(count, sizeof(ArxObject*));
    result->count = count;
    
    // Fill array
    size_t i = 0;
    current = object_list;
    while (current && i < count) {
        if (current->obj->path && strstr(current->obj->path, path_pattern)) {
            result->objects[i++] = current->obj;
        }
        current = current->next;
    }
    
    // Update performance stats
    double elapsed = get_time_ms() - start_time;
    perf_stats.total_queries++;
    perf_stats.total_query_time_ms += elapsed;
    
    return result;
}

ArxQueryResult* arx_query_by_type(ArxObjectType type) {
    double start_time = get_time_ms();
    
    ArxQueryResult* result = calloc(1, sizeof(ArxQueryResult));
    
    // Count matching objects
    size_t count = 0;
    ArxObjectNode* current = object_list;
    while (current) {
        if (current->obj->obj_type == type) {
            count++;
        }
        current = current->next;
    }
    
    // Allocate array
    result->objects = calloc(count, sizeof(ArxObject*));
    result->count = count;
    
    // Fill array
    size_t i = 0;
    current = object_list;
    while (current && i < count) {
        if (current->obj->obj_type == type) {
            result->objects[i++] = current->obj;
        }
        current = current->next;
    }
    
    // Update performance stats
    double elapsed = get_time_ms() - start_time;
    perf_stats.total_queries++;
    perf_stats.total_query_time_ms += elapsed;
    
    return result;
}

ArxQueryResult* arx_query_by_confidence(float min_confidence) {
    double start_time = get_time_ms();
    
    ArxQueryResult* result = calloc(1, sizeof(ArxQueryResult));
    
    // Count matching objects
    size_t count = 0;
    ArxObjectNode* current = object_list;
    while (current) {
        if (current->obj->confidence >= min_confidence) {
            count++;
        }
        current = current->next;
    }
    
    // Allocate array
    result->objects = calloc(count, sizeof(ArxObject*));
    result->count = count;
    
    // Fill array
    size_t i = 0;
    current = object_list;
    while (current && i < count) {
        if (current->obj->confidence >= min_confidence) {
            result->objects[i++] = current->obj;
        }
        current = current->next;
    }
    
    // Update performance stats
    double elapsed = get_time_ms() - start_time;
    perf_stats.total_queries++;
    perf_stats.total_query_time_ms += elapsed;
    
    return result;
}

void arx_query_result_free(ArxQueryResult* result) {
    if (!result) return;
    free(result->objects);
    free(result->error_message);
    free(result);
}

// ============================================================================
// Spatial Operations
// ============================================================================

double arx_spatial_distance(uint64_t id1, uint64_t id2) {
    ArxObject* obj1 = arx_object_get(id1);
    ArxObject* obj2 = arx_object_get(id2);
    
    if (!obj1 || !obj2) {
        return -1.0; // Error
    }
    
    double dx = obj1->world_x_mm - obj2->world_x_mm;
    double dy = obj1->world_y_mm - obj2->world_y_mm;
    double dz = obj1->world_z_mm - obj2->world_z_mm;
    
    return sqrt(dx*dx + dy*dy + dz*dz);
}

bool arx_spatial_within_bounds(uint64_t id, const ArxBoundingBox* bounds) {
    ArxObject* obj = arx_object_get(id);
    if (!obj || !bounds) return false;
    
    return obj->world_x_mm >= bounds->min.x && obj->world_x_mm <= bounds->max.x &&
           obj->world_y_mm >= bounds->min.y && obj->world_y_mm <= bounds->max.y &&
           obj->world_z_mm >= bounds->min.z && obj->world_z_mm <= bounds->max.z;
}

// ============================================================================
// ASCII Rendering (Simplified)
// ============================================================================

char* arx_ascii_render_2d(ArxObject** objects, size_t count, int width, int height) {
    // Allocate buffer
    size_t buffer_size = (width + 1) * height + 1;
    char* buffer = calloc(buffer_size, sizeof(char));
    
    // Fill with spaces
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            buffer[y * (width + 1) + x] = ' ';
        }
        buffer[y * (width + 1) + width] = '\n';
    }
    
    // Render objects (simplified)
    for (size_t i = 0; i < count; i++) {
        ArxObject* obj = objects[i];
        
        // Convert world coordinates to ASCII coordinates (simplified)
        int x = (obj->world_x_mm / 1000) % width;
        int y = (obj->world_y_mm / 1000) % height;
        
        if (x >= 0 && x < width && y >= 0 && y < height) {
            char symbol = ' ';
            switch (obj->obj_type) {
                case ARX_TYPE_WALL: symbol = '#'; break;
                case ARX_TYPE_DOOR: symbol = 'D'; break;
                case ARX_TYPE_WINDOW: symbol = 'W'; break;
                case ARX_TYPE_COLUMN: symbol = 'O'; break;
                default: symbol = '?'; break;
            }
            buffer[y * (width + 1) + x] = symbol;
        }
    }
    
    return buffer;
}

// ============================================================================
// Performance Metrics
// ============================================================================

ArxPerformanceStats* arx_get_performance_stats(void) {
    ArxPerformanceStats* stats = malloc(sizeof(ArxPerformanceStats));
    
    // Count objects
    size_t object_count = 0;
    ArxObjectNode* current = object_list;
    while (current) {
        object_count++;
        current = current->next;
    }
    
    stats->total_objects = object_count;
    stats->total_queries = perf_stats.total_queries;
    stats->avg_query_time_ms = perf_stats.total_queries > 0 ? 
        perf_stats.total_query_time_ms / perf_stats.total_queries : 0;
    stats->avg_create_time_ms = perf_stats.total_creates > 0 ?
        perf_stats.total_create_time_ms / perf_stats.total_creates : 0;
    stats->avg_update_time_ms = perf_stats.total_updates > 0 ?
        perf_stats.total_update_time_ms / perf_stats.total_updates : 0;
    stats->memory_usage_bytes = object_count * sizeof(ArxObject);
    
    return stats;
}

void arx_performance_stats_free(ArxPerformanceStats* stats) {
    free(stats);
}

// ============================================================================
// Utility Functions
// ============================================================================

const char* arx_get_last_error(void) {
    return last_error;
}

void arx_set_log_level(int level) {
    log_level = level;
}

const char* arx_get_version(void) {
    return "1.0.0-cgo";
}