/**
 * ArxObject Runtime Engine - Core Implementation
 * 
 * This implements the programmable building component system that serves
 * as the foundation for the Building Infrastructure-as-Code platform.
 */

#include "arxobject.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>

// ============================================================================
// Internal Helper Functions
// ============================================================================

/**
 * Generate a unique ID for ArxObjects
 * In production, this would use a proper UUID library
 */
static char* generate_id() {
    static int counter = 0;
    char* id = malloc(32);
    snprintf(id, 32, "arx_%d_%ld", counter++, time(NULL));
    return id;
}

/**
 * Safe string duplication with null checking
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
 * Safe string comparison with null checking
 */
static bool safe_strcmp(const char* a, const char* b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return strcmp(a, b) == 0;
}

/**
 * Initialize ArxObject with default values
 */
static void init_arx_object(ArxObject* obj, ArxObjectType type, const char* name) {
    assert(obj != NULL);
    
    // Core identity
    obj->id = generate_id();
    obj->type = type;
    obj->name = safe_strdup(name);
    obj->description = NULL;
    
    // Hierarchy
    obj->building_id = NULL;
    obj->floor_id = NULL;
    obj->zone_id = NULL;
    obj->parent_id = NULL;
    
    // Spatial properties
    memset(&obj->geometry, 0, sizeof(ArxGeometry));
    
    // Properties and metadata
    obj->properties = NULL;
    obj->property_count = 0;
    obj->material = NULL;
    obj->color = NULL;
    
    // Relationships
    obj->relationships = NULL;
    obj->relationship_count = 0;
    
    // Validation and confidence
    obj->validation_status = ARX_VALIDATION_PENDING;
    obj->validations = NULL;
    obj->validation_count = 0;
    obj->confidence = 0.5;  // Default medium confidence
    obj->confidence_factors = NULL;
    obj->confidence_factor_count = 0;
    
    // Constraints
    obj->constraints = NULL;
    obj->constraint_count = 0;
    
    // Physics and simulation
    obj->physics = NULL;
    
    // Source and versioning
    obj->source_type = NULL;
    obj->source_file = NULL;
    obj->source_page = 0;
    obj->version = 1;
    
    // Timestamps
    time_t now = time(NULL);
    obj->created_at = now;
    obj->updated_at = now;
    obj->validated_at = 0;
    
    // Metadata
    obj->tags = NULL;
    obj->tag_count = 0;
    obj->flags = 0;
    obj->hash = NULL;
    
    // Thread safety
    pthread_rwlock_init(&obj->lock, NULL);
    
    // Memory management
    obj->is_allocated = false;
}

// ============================================================================
// ArxObject Lifecycle Management
// ============================================================================

ArxObject* arx_object_create(ArxObjectType type, const char* name) {
    if (!name) return NULL;
    
    ArxObject* obj = malloc(sizeof(ArxObject));
    if (!obj) return NULL;
    
    init_arx_object(obj, type, name);
    obj->is_allocated = true;
    
    return obj;
}

void arx_object_destroy(ArxObject* obj) {
    if (!obj) return;
    
    // Acquire write lock for cleanup
    pthread_rwlock_wrlock(&obj->lock);
    
    // Free strings
    arx_object_free_string(obj->id);
    arx_object_free_string(obj->name);
    arx_object_free_string(obj->description);
    arx_object_free_string(obj->building_id);
    arx_object_free_string(obj->floor_id);
    arx_object_free_string(obj->zone_id);
    arx_object_free_string(obj->parent_id);
    arx_object_free_string(obj->material);
    arx_object_free_string(obj->color);
    arx_object_free_string(obj->source_type);
    arx_object_free_string(obj->source_file);
    arx_object_free_string(obj->hash);
    
    // Free arrays
    arx_object_free_properties(obj->properties, obj->property_count);
    arx_object_free_relationships(obj->relationships, obj->relationship_count);
    arx_object_free_validations(obj->validations, obj->validation_count);
    
    // Free tags
    if (obj->tags) {
        for (int i = 0; i < obj->tag_count; i++) {
            arx_object_free_string(obj->tags[i]);
        }
        free(obj->tags);
    }
    
    // Free confidence factors
    if (obj->confidence_factors) {
        free(obj->confidence_factors);
    }
    
    // Free constraints
    if (obj->constraints) {
        for (int i = 0; i < obj->constraint_count; i++) {
            arx_object_free_string(obj->constraints[i].id);
            arx_object_free_string(obj->constraints[i].name);
            arx_object_free_string(obj->constraints[i].description);
            arx_object_free_string(obj->constraints[i].error_message);
            arx_object_free_properties(obj->constraints[i].conditions, 0);
            arx_object_free_properties(obj->constraints[i].requirements, 0);
        }
        free(obj->constraints);
    }
    
    // Free physics model
    if (obj->physics) {
        arx_object_free_string(obj->physics->model_type);
        arx_object_free_properties(obj->physics->parameters, obj->physics->parameter_count);
        if (obj->physics->simulation_data) {
            free(obj->physics->simulation_data);
        }
        free(obj->physics);
    }
    
    // Free geometry arrays
    if (obj->geometry.points) free(obj->geometry.points);
    if (obj->geometry.vertices) free(obj->geometry.vertices);
    if (obj->geometry.faces) free(obj->geometry.faces);
    
    // Destroy lock
    pthread_rwlock_destroy(&obj->lock);
    
    // Free the object itself
    free(obj);
}

ArxObject* arx_object_clone(const ArxObject* obj) {
    if (!obj) return NULL;
    
    ArxObject* clone = arx_object_create(obj->type, obj->name);
    if (!clone) return NULL;
    
    // Acquire read lock on source
    pthread_rwlock_rdlock(&obj->lock);
    
    // Copy basic fields
    clone->description = safe_strdup(obj->description);
    clone->building_id = safe_strdup(obj->building_id);
    clone->floor_id = safe_strdup(obj->floor_id);
    clone->zone_id = safe_strdup(obj->zone_id);
    clone->parent_id = safe_strdup(obj->parent_id);
    clone->material = safe_strdup(obj->material);
    clone->color = safe_strdup(obj->color);
    clone->source_type = safe_strdup(obj->source_type);
    clone->source_file = safe_strdup(obj->source_file);
    clone->source_page = obj->source_page;
    clone->validation_status = obj->validation_status;
    clone->confidence = obj->confidence;
    clone->flags = obj->flags;
    clone->hash = safe_strdup(obj->hash);
    
    // Copy geometry (shallow copy for now)
    clone->geometry = obj->geometry;
    
    // TODO: Deep copy geometry arrays, properties, relationships, etc.
    
    pthread_rwlock_unlock(&obj->lock);
    
    return clone;
}

bool arx_object_is_valid(const ArxObject* obj) {
    if (!obj) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    bool valid = (obj->id != NULL && 
                  obj->name != NULL && 
                  obj->type > 0 && 
                  obj->type < ARX_TYPE_COUNT);
    
    pthread_rwlock_unlock(&obj->lock);
    return valid;
}

// ============================================================================
// Property Management
// ============================================================================

bool arx_object_set_property(ArxObject* obj, const char* key, ArxPropertyType type, ArxPropertyValue value) {
    if (!obj || !key) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Check if property already exists
    for (int i = 0; i < obj->property_count; i++) {
        if (safe_strcmp(obj->properties[i].key, key)) {
            // Update existing property
            obj->properties[i].type = type;
            obj->properties[i].value = value;
            obj->updated_at = time(NULL);
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    // Add new property
    ArxProperty* new_props = realloc(obj->properties, (obj->property_count + 1) * sizeof(ArxProperty));
    if (!new_props) {
        pthread_rwlock_unlock(&obj->lock);
        return false;
    }
    
    obj->properties = new_props;
    ArxProperty* new_prop = &obj->properties[obj->property_count];
    
    new_prop->key = safe_strdup(key);
    new_prop->type = type;
    new_prop->value = value;
    new_prop->is_required = false;
    new_prop->description = NULL;
    
    obj->property_count++;
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_get_property(const ArxObject* obj, const char* key, ArxPropertyValue* value) {
    if (!obj || !key || !value) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    for (int i = 0; i < obj->property_count; i++) {
        if (safe_strcmp(obj->properties[i].key, key)) {
            *value = obj->properties[i].value;
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return false;
}

bool arx_object_has_property(const ArxObject* obj, const char* key) {
    if (!obj || !key) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    for (int i = 0; i < obj->property_count; i++) {
        if (safe_strcmp(obj->properties[i].key, key)) {
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return false;
}

bool arx_object_remove_property(ArxObject* obj, const char* key) {
    if (!obj || !key) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    for (int i = 0; i < obj->property_count; i++) {
        if (safe_strcmp(obj->properties[i].key, key)) {
            // Free the property
            arx_object_free_string(obj->properties[i].key);
            arx_object_free_string(obj->properties[i].description);
            
            // Shift remaining properties
            for (int j = i; j < obj->property_count - 1; j++) {
                obj->properties[j] = obj->properties[j + 1];
            }
            
            obj->property_count--;
            obj->updated_at = time(NULL);
            
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return false;
}

// ============================================================================
// Geometry and Spatial Operations
// ============================================================================

bool arx_object_set_geometry(ArxObject* obj, const ArxGeometry* geometry) {
    if (!obj || !geometry) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Free existing geometry arrays
    if (obj->geometry.points) free(obj->geometry.points);
    if (obj->geometry.vertices) free(obj->geometry.vertices);
    if (obj->geometry.faces) free(obj->geometry.faces);
    
    // Copy basic geometry
    obj->geometry = *geometry;
    
    // Deep copy arrays
    if (geometry->points && geometry->point_count > 0) {
        obj->geometry.points = malloc(geometry->point_count * sizeof(ArxPoint3D));
        if (obj->geometry.points) {
            memcpy(obj->geometry.points, geometry->points, 
                   geometry->point_count * sizeof(ArxPoint3D));
        }
    }
    
    if (geometry->vertices && geometry->vertex_count > 0) {
        obj->geometry.vertices = malloc(geometry->vertex_count * sizeof(ArxPoint3D));
        if (obj->geometry.vertices) {
            memcpy(obj->geometry.vertices, geometry->vertices, 
                   geometry->vertex_count * sizeof(ArxPoint3D));
        }
    }
    
    if (geometry->faces && geometry->face_count > 0) {
        obj->geometry.faces = malloc(geometry->face_count * sizeof(int));
        if (obj->geometry.faces) {
            memcpy(obj->geometry.faces, geometry->faces, 
                   geometry->face_count * sizeof(int));
        }
    }
    
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_get_geometry(const ArxObject* obj, ArxGeometry* geometry) {
    if (!obj || !geometry) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    // Copy basic geometry
    *geometry = obj->geometry;
    
    // Deep copy arrays
    if (obj->geometry.points && obj->geometry.point_count > 0) {
        geometry->points = malloc(obj->geometry.point_count * sizeof(ArxPoint3D));
        if (geometry->points) {
            memcpy(geometry->points, obj->geometry.points, 
                   obj->geometry.point_count * sizeof(ArxPoint3D));
        }
    }
    
    if (obj->geometry.vertices && obj->geometry.vertex_count > 0) {
        geometry->vertices = malloc(obj->geometry.vertex_count * sizeof(ArxPoint3D));
        if (geometry->vertices) {
            memcpy(geometry->vertices, obj->geometry.vertices, 
                   obj->geometry.vertex_count * sizeof(ArxPoint3D));
        }
    }
    
    if (obj->geometry.faces && obj->geometry.face_count > 0) {
        geometry->faces = malloc(obj->geometry.face_count * sizeof(int));
        if (geometry->faces) {
            memcpy(geometry->faces, obj->geometry.faces, 
                   obj->geometry.face_count * sizeof(int));
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_update_position(ArxObject* obj, const ArxPoint3D* position) {
    if (!obj || !position) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    obj->geometry.position = *position;
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_is_point_inside(const ArxObject* obj, const ArxPoint3D* point) {
    if (!obj || !point) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    // Simple bounding box check for now
    // TODO: Implement proper point-in-polygon for complex shapes
    bool inside = (point->x >= obj->geometry.bounding_box.min.x &&
                   point->x <= obj->geometry.bounding_box.max.x &&
                   point->y >= obj->geometry.bounding_box.min.y &&
                   point->y <= obj->geometry.bounding_box.max.y &&
                   point->z >= obj->geometry.bounding_box.min.z &&
                   point->z <= obj->geometry.bounding_box.max.z);
    
    pthread_rwlock_unlock(&obj->lock);
    return inside;
}

bool arx_object_intersects_with(const ArxObject* obj, const ArxObject* other) {
    if (!obj || !other) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    pthread_rwlock_rdlock(&other->lock);
    
    // Simple bounding box intersection check
    bool intersects = !(obj->geometry.bounding_box.max.x < other->geometry.bounding_box.min.x ||
                        obj->geometry.bounding_box.min.x > other->geometry.bounding_box.max.x ||
                        obj->geometry.bounding_box.max.y < other->geometry.bounding_box.min.y ||
                        obj->geometry.bounding_box.min.y > other->geometry.bounding_box.max.y ||
                        obj->geometry.bounding_box.max.z < other->geometry.bounding_box.min.z ||
                        obj->geometry.bounding_box.min.z > other->geometry.bounding_box.max.z);
    
    pthread_rwlock_unlock(&other->lock);
    pthread_rwlock_unlock(&obj->lock);
    
    return intersects;
}

// ============================================================================
// Relationship Management
// ============================================================================

bool arx_object_add_relationship(ArxObject* obj, const ArxRelationship* relationship) {
    if (!obj || !relationship) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Check if relationship already exists
    for (int i = 0; i < obj->relationship_count; i++) {
        if (safe_strcmp(obj->relationships[i].target_id, relationship->target_id) &&
            safe_strcmp(obj->relationships[i].type, relationship->type)) {
            // Update existing relationship
            arx_object_free_string(obj->relationships[i].id);
            arx_object_free_string(obj->relationships[i].type);
            arx_object_free_string(obj->relationships[i].target_id);
            arx_object_free_string(obj->relationships[i].source_id);
            arx_object_free_properties(obj->relationships[i].properties, obj->relationships[i].property_count);
            
            obj->relationships[i] = *relationship;
            obj->relationships[i].id = safe_strdup(relationship->id);
            obj->relationships[i].type = safe_strdup(relationship->type);
            obj->relationships[i].target_id = safe_strdup(relationship->target_id);
            obj->relationships[i].source_id = safe_strdup(relationship->source_id);
            
            obj->updated_at = time(NULL);
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    // Add new relationship
    ArxRelationship* new_rels = realloc(obj->relationships, (obj->relationship_count + 1) * sizeof(ArxRelationship));
    if (!new_rels) {
        pthread_rwlock_unlock(&obj->lock);
        return false;
    }
    
    obj->relationships = new_rels;
    ArxRelationship* new_rel = &obj->relationships[obj->relationship_count];
    
    new_rel->id = safe_strdup(relationship->id);
    new_rel->type = safe_strdup(relationship->type);
    new_rel->target_id = safe_strdup(relationship->target_id);
    new_rel->source_id = safe_strdup(relationship->source_id);
    new_rel->confidence = relationship->confidence;
    new_rel->created_at = relationship->created_at;
    
    // Copy properties
    if (relationship->properties && relationship->property_count > 0) {
        new_rel->properties = malloc(relationship->property_count * sizeof(ArxProperty));
        if (new_rel->properties) {
            for (int i = 0; i < relationship->property_count; i++) {
                new_rel->properties[i] = relationship->properties[i];
                new_rel->properties[i].key = safe_strdup(relationship->properties[i].key);
                if (relationship->properties[i].type == ARX_PROP_STRING) {
                    new_rel->properties[i].value.string_value = safe_strdup(relationship->properties[i].value.string_value);
                }
            }
            new_rel->property_count = relationship->property_count;
        }
    } else {
        new_rel->properties = NULL;
        new_rel->property_count = 0;
    }
    
    obj->relationship_count++;
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_remove_relationship(ArxObject* obj, const char* relationship_id) {
    if (!obj || !relationship_id) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    for (int i = 0; i < obj->relationship_count; i++) {
        if (safe_strcmp(obj->relationships[i].id, relationship_id)) {
            // Free the relationship
            arx_object_free_string(obj->relationships[i].id);
            arx_object_free_string(obj->relationships[i].type);
            arx_object_free_string(obj->relationships[i].target_id);
            arx_object_free_string(obj->relationships[i].source_id);
            arx_object_free_properties(obj->relationships[i].properties, obj->relationships[i].property_count);
            
            // Shift remaining relationships
            for (int j = i; j < obj->relationship_count - 1; j++) {
                obj->relationships[j] = obj->relationships[j + 1];
            }
            
            obj->relationship_count--;
            obj->updated_at = time(NULL);
            
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return false;
}

ArxRelationship* arx_object_get_relationships(const ArxObject* obj, const char* type, int* count) {
    if (!obj || !count) return NULL;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    if (!type) {
        // Return all relationships
        *count = obj->relationship_count;
        ArxRelationship* all_rels = malloc(obj->relationship_count * sizeof(ArxRelationship));
        if (all_rels) {
            for (int i = 0; i < obj->relationship_count; i++) {
                all_rels[i] = obj->relationships[i];
                all_rels[i].id = safe_strdup(obj->relationships[i].id);
                all_rels[i].type = safe_strdup(obj->relationships[i].type);
                all_rels[i].target_id = safe_strdup(obj->relationships[i].target_id);
                all_rels[i].source_id = safe_strdup(obj->relationships[i].source_id);
            }
        }
        pthread_rwlock_unlock(&obj->lock);
        return all_rels;
    }
    
    // Count matching relationships
    int match_count = 0;
    for (int i = 0; i < obj->relationship_count; i++) {
        if (safe_strcmp(obj->relationships[i].type, type)) {
            match_count++;
        }
    }
    
    if (match_count == 0) {
        *count = 0;
        pthread_rwlock_unlock(&obj->lock);
        return NULL;
    }
    
    // Create filtered array
    ArxRelationship* filtered_rels = malloc(match_count * sizeof(ArxRelationship));
    if (!filtered_rels) {
        *count = 0;
        pthread_rwlock_unlock(&obj->lock);
        return NULL;
    }
    
    int idx = 0;
    for (int i = 0; i < obj->relationship_count; i++) {
        if (safe_strcmp(obj->relationships[i].type, type)) {
            filtered_rels[idx] = obj->relationships[i];
            filtered_rels[idx].id = safe_strdup(obj->relationships[i].id);
            filtered_rels[idx].type = safe_strdup(obj->relationships[i].type);
            filtered_rels[idx].target_id = safe_strdup(obj->relationships[i].target_id);
            filtered_rels[idx].source_id = safe_strdup(obj->relationships[i].source_id);
            idx++;
        }
    }
    
    *count = match_count;
    pthread_rwlock_unlock(&obj->lock);
    return filtered_rels;
}

bool arx_object_has_relationship(const ArxObject* obj, const char* target_id, const char* type) {
    if (!obj || !target_id) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    for (int i = 0; i < obj->relationship_count; i++) {
        if (safe_strcmp(obj->relationships[i].target_id, target_id)) {
            if (!type || safe_strcmp(obj->relationships[i].type, type)) {
                pthread_rwlock_unlock(&obj->lock);
                return true;
            }
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return false;
}

// ============================================================================
// Validation and Confidence
// ============================================================================

bool arx_object_add_validation(ArxObject* obj, const ArxValidationRecord* validation) {
    if (!obj || !validation) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Add validation record
    ArxValidationRecord* new_validations = realloc(obj->validations, (obj->validation_count + 1) * sizeof(ArxValidationRecord));
    if (!new_validations) {
        pthread_rwlock_unlock(&obj->lock);
        return false;
    }
    
    obj->validations = new_validations;
    ArxValidationRecord* new_val = &obj->validations[obj->validation_count];
    
    new_val->id = safe_strdup(validation->id);
    new_val->timestamp = validation->timestamp;
    new_val->validated_by = safe_strdup(validation->validated_by);
    new_val->method = safe_strdup(validation->method);
    new_val->evidence = safe_strdup(validation->evidence);
    new_val->confidence = validation->confidence;
    new_val->notes = safe_strdup(validation->notes);
    
    obj->validation_count++;
    
    // Update validation status based on confidence
    if (validation->confidence >= 0.9) {
        obj->validation_status = ARX_VALIDATION_VALIDATED;
        obj->validated_at = validation->timestamp;
    } else if (validation->confidence >= 0.5) {
        obj->validation_status = ARX_VALIDATION_PARTIAL;
    }
    
    // Update overall confidence
    obj->updateConfidence(obj);
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_is_validated(const ArxObject* obj) {
    if (!obj) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    bool is_validated = (obj->validation_status == ARX_VALIDATION_VALIDATED);
    pthread_rwlock_unlock(&obj->lock);
    
    return is_validated;
}

double arx_object_get_confidence(const ArxObject* obj) {
    if (!obj) return 0.0;
    
    pthread_rwlock_rdlock(&obj->lock);
    double confidence = obj->confidence;
    pthread_rwlock_unlock(&obj->lock);
    
    return confidence;
}

bool arx_object_update_confidence(ArxObject* obj, double confidence) {
    if (!obj || confidence < 0.0 || confidence > 1.0) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    obj->confidence = confidence;
    obj->updated_at = time(NULL);
    pthread_rwlock_unlock(&obj->lock);
    
    return true;
}

// ============================================================================
// Constraint Validation
// ============================================================================

bool arx_object_add_constraint(ArxObject* obj, const ArxConstraint* constraint) {
    if (!obj || !constraint) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Add constraint
    ArxConstraint* new_constraints = realloc(obj->constraints, (obj->constraint_count + 1) * sizeof(ArxConstraint));
    if (!new_constraints) {
        pthread_rwlock_unlock(&obj->lock);
        return false;
    }
    
    obj->constraints = new_constraints;
    ArxConstraint* new_const = &obj->constraints[obj->constraint_count];
    
    new_const->id = safe_strdup(constraint->id);
    new_const->name = safe_strdup(constraint->name);
    new_const->description = safe_strdup(constraint->description);
    new_const->severity = constraint->severity;
    new_const->error_message = safe_strdup(constraint->error_message);
    
    // Copy conditions and requirements
    if (constraint->conditions && constraint->property_count > 0) {
        new_const->conditions = malloc(constraint->property_count * sizeof(ArxProperty));
        if (new_const->conditions) {
            for (int i = 0; i < constraint->property_count; i++) {
                new_const->conditions[i] = constraint->conditions[i];
                new_const->conditions[i].key = safe_strdup(constraint->conditions[i].key);
            }
            new_const->property_count = constraint->property_count;
        }
    } else {
        new_const->conditions = NULL;
        new_const->property_count = 0;
    }
    
    obj->constraint_count++;
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_validate_constraints(const ArxObject* obj, ArxValidationRecord* result) {
    if (!obj || !result) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    // Simple constraint validation for now
    // TODO: Implement full constraint evaluation engine
    bool all_valid = true;
    double min_confidence = 1.0;
    
    for (int i = 0; i < obj->constraint_count; i++) {
        // Basic validation - check if required properties exist
        if (obj->constraints[i].requirements) {
            for (int j = 0; j < obj->constraints[i].property_count; j++) {
                if (obj->constraints[i].requirements[j].is_required) {
                    if (!arx_object_has_property(obj, obj->constraints[i].requirements[j].key)) {
                        all_valid = false;
                        min_confidence = 0.0;
                        break;
                    }
                }
            }
        }
        
        if (!all_valid) break;
    }
    
    // Create validation result
    result->id = "constraint_validation";
    result->timestamp = time(NULL);
    result->validated_by = "system";
    result->method = "constraint_check";
    result->evidence = "constraint_validation";
    result->confidence = min_confidence;
    result->notes = all_valid ? "All constraints satisfied" : "Constraint validation failed";
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_check_constraint(const ArxObject* obj, const char* constraint_id) {
    if (!obj || !constraint_id) return false;
    
    pthread_rwlock_rdlock(&obj->lock);
    
    for (int i = 0; i < obj->constraint_count; i++) {
        if (safe_strcmp(obj->constraints[i].id, constraint_id)) {
            // TODO: Implement actual constraint checking logic
            pthread_rwlock_unlock(&obj->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return false;
}

// ============================================================================
// Physics and Simulation
// ============================================================================

bool arx_object_set_physics_model(ArxObject* obj, const ArxPhysicsModel* model) {
    if (!obj || !model) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Free existing physics model
    if (obj->physics) {
        arx_object_free_string(obj->physics->model_type);
        arx_object_free_properties(obj->physics->parameters, obj->physics->parameter_count);
        if (obj->physics->simulation_data) {
            free(obj->physics->simulation_data);
        }
        free(obj->physics);
    }
    
    // Create new physics model
    obj->physics = malloc(sizeof(ArxPhysicsModel));
    if (!obj->physics) {
        pthread_rwlock_unlock(&obj->lock);
        return false;
    }
    
    obj->physics->model_type = safe_strdup(model->model_type);
    obj->physics->parameter_count = model->parameter_count;
    obj->physics->data_size = model->data_size;
    
    // Copy parameters
    if (model->parameters && model->parameter_count > 0) {
        obj->physics->parameters = malloc(model->parameter_count * sizeof(ArxProperty));
        if (obj->physics->parameters) {
            for (int i = 0; i < model->parameter_count; i++) {
                obj->physics->parameters[i] = model->parameters[i];
                obj->physics->parameters[i].key = safe_strdup(model->parameters[i].key);
            }
        }
    } else {
        obj->physics->parameters = NULL;
    }
    
    // Copy simulation data
    if (model->simulation_data && model->data_size > 0) {
        obj->physics->simulation_data = malloc(model->data_size);
        if (obj->physics->simulation_data) {
            memcpy(obj->physics->simulation_data, model->simulation_data, model->data_size);
        }
    } else {
        obj->physics->simulation_data = NULL;
    }
    
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_simulate(ArxObject* obj, const char* simulation_type, ArxProperty* parameters, int param_count) {
    if (!obj || !simulation_type) return false;
    
    // TODO: Implement actual physics simulation
    // This is a placeholder for the simulation engine
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Update simulation data based on parameters
    if (obj->physics && obj->physics->simulation_data) {
        // Placeholder: update simulation state
        // In real implementation, this would run physics calculations
    }
    
    obj->updated_at = time(NULL);
    
    pthread_rwlock_unlock(&obj->lock);
    return true;
}

bool arx_object_get_simulation_result(const ArxObject* obj, ArxProperty* result, int* result_count) {
    if (!obj || !result || !result_count) return false;
    
    // TODO: Implement simulation result extraction
    // This is a placeholder
    
    *result_count = 0;
    return true;
}

// ============================================================================
// Serialization and Persistence
// ============================================================================

char* arx_object_to_json(const ArxObject* obj) {
    if (!obj) return NULL;
    
    // TODO: Implement JSON serialization
    // This is a placeholder for the JSON engine
    
    char* json = malloc(1024);
    if (json) {
        snprintf(json, 1024, 
                "{\"id\":\"%s\",\"type\":\"%s\",\"name\":\"%s\",\"confidence\":%.2f}",
                obj->id ? obj->id : "",
                arx_object_get_type_name(obj->type),
                obj->name ? obj->name : "",
                obj->confidence);
    }
    
    return json;
}

ArxObject* arx_object_from_json(const char* json) {
    if (!json) return NULL;
    
    // TODO: Implement JSON deserialization
    // This is a placeholder for the JSON parser
    
    // For now, create a basic object
    ArxObject* obj = arx_object_create(ARX_TYPE_UNKNOWN, "JSON Import");
    if (obj) {
        // TODO: Parse JSON and populate object
    }
    
    return obj;
}

char* arx_object_to_binary(const ArxObject* obj, size_t* size) {
    if (!obj || !size) return NULL;
    
    // TODO: Implement binary serialization
    // This is a placeholder for the binary format
    
    *size = 0;
    return NULL;
}

ArxObject* arx_object_from_binary(const char* data, size_t size) {
    if (!data || size == 0) return NULL;
    
    // TODO: Implement binary deserialization
    // This is a placeholder for the binary parser
    
    return NULL;
}

// ============================================================================
// Utility Functions
// ============================================================================

bool arx_object_calculate_hash(ArxObject* obj) {
    if (!obj) return false;
    
    pthread_rwlock_wrlock(&obj->lock);
    
    // Create hash from core properties
    char hash_data[1024];
    snprintf(hash_data, sizeof(hash_data), "%s-%s-%ld-%ld-%ld-%s",
             arx_object_get_type_name(obj->type),
             obj->name ? obj->name : "",
             obj->geometry.position.x,
             obj->geometry.position.y,
             obj->geometry.position.z,
             obj->material ? obj->material : "");
    
    // Simple hash for now - should use crypto/sha256 in production
    unsigned long hash = 5381;
    int c;
    char* str = hash_data;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c;
    }
    
    // Convert to hex string
    if (obj->hash) free(obj->hash);
    obj->hash = malloc(17);
    if (obj->hash) {
        snprintf(obj->hash, 17, "%016lx", hash);
    }
    
    pthread_rwlock_unlock(&obj->lock);
    return (obj->hash != NULL);
}

// ============================================================================
// Memory Management
// ============================================================================

void arx_object_free_string(char* str) {
    if (str) free(str);
}

void arx_object_free_properties(ArxProperty* props, int count) {
    if (!props) return;
    
    for (int i = 0; i < count; i++) {
        arx_object_free_string(props[i].key);
        arx_object_free_string(props[i].description);
        
        // Free string values
        if (props[i].type == ARX_PROP_STRING && props[i].value.string_value) {
            arx_object_free_string(props[i].value.string_value);
        }
    }
    free(props);
}

void arx_object_free_relationships(ArxRelationship* rels, int count) {
    if (!rels) return;
    
    for (int i = 0; i < count; i++) {
        arx_object_free_string(rels[i].id);
        arx_object_free_string(rels[i].type);
        arx_object_free_string(rels[i].target_id);
        arx_object_free_string(rels[i].source_id);
        arx_object_free_properties(rels[i].properties, rels[i].property_count);
    }
    free(rels);
}

void arx_object_free_validations(ArxValidationRecord* vals, int count) {
    if (!vals) return;
    
    for (int i = 0; i < count; i++) {
        arx_object_free_string(vals[i].id);
        arx_object_free_string(vals[i].validated_by);
        arx_object_free_string(vals[i].method);
        arx_object_free_string(vals[i].evidence);
        arx_object_free_string(vals[i].notes);
    }
    free(vals);
}
