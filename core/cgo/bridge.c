/**
 * @file bridge.c
 * @brief C-Go Bridge Implementation for ARXOS Core
 * 
 * Implements the bridge functions that enable Go to call C functions directly.
 * This provides a clean interface while maintaining the performance benefits of C.
 */

#include "bridge.h"
#include "ingestion/arx_ingestion.h"
#include "auth/arx_auth.h"
#include "database/arx_database.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// ============================================================================
// GLOBAL ERROR HANDLING
// ============================================================================

static char* last_error_message = NULL;

static void set_error(const char* format, ...) {
    if (last_error_message) {
        free(last_error_message);
    }
    
    va_list args;
    va_start(args, format);
    
    // Calculate required buffer size
    va_list args_copy;
    va_copy(args_copy, args);
    int size = vsnprintf(NULL, 0, format, args_copy);
    va_end(args_copy);
    
    if (size > 0) {
        last_error_message = malloc(size + 1);
        if (last_error_message) {
            vsnprintf(last_error_message, size + 1, format, args);
        }
    }
    
    va_end(args);
}

static void clear_error(void) {
    if (last_error_message) {
        free(last_error_message);
        last_error_message = NULL;
    }
}

// ============================================================================
// ARXOBJECT BRIDGE FUNCTIONS
// ============================================================================

ArxObject* cgo_arx_object_create(const char* id, int type, 
                                 const char* name, const char* description) {
    if (!id || !name) {
        set_error("Invalid parameters for ArxObject creation");
        return NULL;
    }
    
    ArxObjectType arx_type = (ArxObjectType)type;
    if (arx_type < 0 || arx_type >= ARX_OBJECT_TYPE_COUNT) {
        set_error("Invalid ArxObject type: %d", type);
        return NULL;
    }
    
    ArxObject* obj = arx_object_create(id, arx_type, name, description);
    if (!obj) {
        set_error("Failed to create ArxObject");
        return NULL;
    }
    
    clear_error();
    return obj;
}

void cgo_arx_object_destroy(ArxObject* obj) {
    if (obj) {
        arx_object_destroy(obj);
    }
}

bool cgo_arx_object_set_property(ArxObject* obj, const char* key, const char* value) {
    if (!obj || !key || !value) {
        set_error("Invalid parameters for property setting");
        return false;
    }
    
    ArxProperty prop = {0};
    prop.key = (char*)key;
    prop.value = (char*)value;
    prop.type = ARX_PROPERTY_TYPE_STRING;
    
    bool result = arx_object_set_property(obj, &prop);
    if (result) {
        clear_error();
    } else {
        set_error("Failed to set property %s", key);
    }
    
    return result;
}

char* cgo_arx_object_get_property(ArxObject* obj, const char* key) {
    if (!obj || !key) {
        set_error("Invalid parameters for property retrieval");
        return NULL;
    }
    
    ArxProperty* prop = arx_object_get_property(obj, key);
    if (!prop) {
        set_error("Property %s not found", key);
        return NULL;
    }
    
    char* result = NULL;
    if (prop->value) {
        result = strdup(prop->value);
        if (!result) {
            set_error("Failed to allocate memory for property value");
        }
    }
    
    if (result) {
        clear_error();
    }
    
    return result;
}

// ============================================================================
// ASCII ENGINE BRIDGE FUNCTIONS
// ============================================================================

char* cgo_generate_2d_floor_plan(ArxObject** objects, int object_count,
                                 int width, int height, double scale) {
    if (!objects || object_count <= 0 || width <= 0 || height <= 0 || scale <= 0) {
        set_error("Invalid parameters for 2D floor plan generation");
        return NULL;
    }
    
    ASCIIRenderOptions options = {0};
    options.width = width;
    options.height = height;
    options.scale = scale;
    options.background = ' ';
    options.origin = (ArxPoint3D){0, 0, 0};
    
    char* result = generate_2d_floor_plan(objects, object_count, &options);
    if (!result) {
        set_error("Failed to generate 2D floor plan");
        return NULL;
    }
    
    clear_error();
    return result;
}

char* cgo_generate_3d_building_view(ArxObject** objects, int object_count,
                                   int width, int height, int depth, double scale) {
    if (!objects || object_count <= 0 || width <= 0 || height <= 0 || depth <= 0 || scale <= 0) {
        set_error("Invalid parameters for 3D building view generation");
        return NULL;
    }
    
    ASCIIRenderOptions options = {0};
    options.width = width;
    options.height = height;
    options.scale = scale;
    options.background = ' ';
    options.origin = (ArxPoint3D){0, 0, 0};
    
    char* result = generate_3d_building_view(objects, object_count, &options);
    if (!result) {
        set_error("Failed to generate 3D building view");
        return NULL;
    }
    
    clear_error();
    return result;
}

// ============================================================================
// BUILDING MANAGEMENT BRIDGE FUNCTIONS
// ============================================================================

ArxBuilding* cgo_arx_building_create(const char* name, const char* description) {
    if (!name) {
        set_error("Building name is required");
        return NULL;
    }
    
    ArxBuilding* building = arx_building_create(name, description ? description : "");
    if (!building) {
        set_error("Failed to create ArxBuilding");
        return NULL;
    }
    
    clear_error();
    return building;
}

void cgo_arx_building_destroy(ArxBuilding* building) {
    if (building) {
        arx_building_destroy(building);
    }
}

bool cgo_arx_building_add_object(ArxBuilding* building, ArxObject* object) {
    if (!building || !object) {
        set_error("Invalid parameters for adding object to building");
        return false;
    }
    
    bool result = arx_building_add_object(building, object);
    if (result) {
        clear_error();
    } else {
        set_error("Failed to add object to building");
    }
    
    return result;
}

char* cgo_arx_building_get_summary(ArxBuilding* building) {
    if (!building) {
        set_error("Invalid building parameter");
        return NULL;
    }
    
    char* result = arx_building_get_summary(building);
    if (!result) {
        set_error("Failed to get building summary");
        return NULL;
    }
    
    clear_error();
    return result;
}

// ============================================================================
// VERSION CONTROL BRIDGE FUNCTIONS
// ============================================================================

ArxVersionControl* cgo_arx_version_init_repo(const char* repo_path,
                                            const char* author_name,
                                            const char* author_email) {
    if (!repo_path || !author_name || !author_email) {
        set_error("Repository path, author name, and email are required");
        return NULL;
    }
    
    ArxRepoConfig config = {0};
    config.author_name = (char*)author_name;
    config.author_email = (char*)author_email;
    config.max_branches = 100;
    config.max_commits = 10000;
    config.enable_compression = false;
    
    ArxVersionControl* vc = arx_version_init_repo(repo_path, &config);
    if (!vc) {
        set_error("Failed to initialize version control repository");
        return NULL;
    }
    
    clear_error();
    return vc;
}

char* cgo_arx_version_commit(ArxVersionControl* vc, const char* message,
                             const char* author, const char* email) {
    if (!vc || !message) {
        set_error("Version control and commit message are required");
        return NULL;
    }
    
    char* result = arx_version_commit(vc, message, author, email);
    if (!result) {
        set_error("Failed to create commit");
        return NULL;
    }
    
    clear_error();
    return result;
}

char* cgo_arx_version_get_history(ArxVersionControl* vc, int max_commits) {
    if (!vc || max_commits <= 0) {
        set_error("Invalid parameters for history retrieval");
        return NULL;
    }
    
    // For now, return a simple summary since the full history function is TODO
    char* result = malloc(256);
    if (result) {
        snprintf(result, 256, "Version control repository with %d commits (max %d shown)",
                vc->commit_count, max_commits);
        clear_error();
    } else {
        set_error("Failed to allocate memory for history");
    }
    
    return result;
}

// ============================================================================
// SPATIAL INDEXING BRIDGE FUNCTIONS
// ============================================================================

ArxSpatialIndex* cgo_arx_spatial_create_index(int max_depth, bool use_octree) {
    if (max_depth <= 0 || max_depth > 20) {
        set_error("Invalid max depth: must be between 1 and 20");
        return NULL;
    }
    
    ArxSpatialConfig config = {0};
    config.max_depth = max_depth;
    config.min_objects_per_node = 4;
    config.max_objects_per_node = 8;
    config.split_threshold = 0.8;
    config.use_octree = use_octree;
    config.enable_compression = false;
    config.enable_caching = true;
    config.cache_size = 1000;
    
    ArxSpatialIndex* index = arx_spatial_create_index(&config);
    if (!index) {
        set_error("Failed to create spatial index");
        return NULL;
    }
    
    clear_error();
    return index;
}

bool cgo_arx_spatial_add_object(ArxSpatialIndex* index, ArxObject* object) {
    if (!index || !object) {
        set_error("Invalid parameters for adding object to spatial index");
        return false;
    }
    
    bool result = arx_spatial_add_object(index, object);
    if (result) {
        clear_error();
    } else {
        set_error("Failed to add object to spatial index");
    }
    
    return result;
}

ArxObject** cgo_arx_spatial_query(ArxSpatialIndex* index, int query_type,
                                  double x, double y, double z,
                                  double x2, double y2, double z2,
                                  double radius, int max_results,
                                  int* result_count) {
    if (!index || !result_count || max_results <= 0) {
        set_error("Invalid parameters for spatial query");
        return NULL;
    }
    
    ArxObject** results = NULL;
    *result_count = 0;
    
    switch (query_type) {
        case 0: // Range query
            {
                ArxBoundingBox range = {{x, y, z}, {x2, y2, z2}};
                results = arx_spatial_query_range(index, &range, result_count);
            }
            break;
            
        case 1: // Point query
            {
                ArxPoint3D point = {x, y, z};
                results = arx_spatial_query_point(index, &point, result_count);
            }
            break;
            
        case 2: // Nearest neighbor query
            {
                ArxPoint3D point = {x, y, z};
                results = arx_spatial_query_nearest(index, &point, radius, max_results, result_count);
            }
            break;
            
        case 3: // Intersect query
            // TODO: Implement intersect query
            set_error("Intersect query not yet implemented");
            return NULL;
            
        default:
            set_error("Invalid query type: %d", query_type);
            return NULL;
    }
    
    if (results) {
        clear_error();
    }
    
    return results;
}

char* cgo_arx_spatial_get_statistics(ArxSpatialIndex* index) {
    if (!index) {
        set_error("Invalid spatial index parameter");
        return NULL;
    }
    
    char* result = arx_spatial_get_statistics(index);
    if (!result) {
        set_error("Failed to get spatial index statistics");
        return NULL;
    }
    
    clear_error();
    return result;
}

// ============================================================================
// INGESTION BRIDGE FUNCTIONS
// ============================================================================

bool cgo_arx_ingestion_init(void) {
    clear_error();
    return arx_ingestion_init();
}

void cgo_arx_ingestion_cleanup(void) {
    clear_error();
    arx_ingestion_cleanup();
}

int cgo_arx_ingestion_detect_format(const char* filepath) {
    clear_error();
    if (!filepath) {
        set_error("Filepath cannot be NULL");
        return -1;
    }
    return (int)arx_ingestion_detect_format(filepath);
}

bool cgo_arx_ingestion_get_metadata(const char* filepath, void* metadata) {
    clear_error();
    if (!filepath || !metadata) {
        set_error("Filepath and metadata cannot be NULL");
        return false;
    }
    return arx_ingestion_get_metadata(filepath, (ArxFileMetadata*)metadata);
}

void* cgo_arx_ingestion_process_file(const char* filepath, const void* options) {
    clear_error();
    if (!filepath) {
        set_error("Filepath cannot be NULL");
        return NULL;
    }
    
    const ArxIngestionOptions* opts = options ? (const ArxIngestionOptions*)options : NULL;
    ArxIngestionResult* result = arx_ingestion_process_file(filepath, opts);
    
    if (!result) {
        set_error("Failed to process file");
        return NULL;
    }
    
    return result;
}

void cgo_arx_ingestion_free_result(void* result) {
    clear_error();
    if (result) {
        arx_ingestion_free_result((ArxIngestionResult*)result);
    }
}

void* cgo_arx_ingestion_get_default_options(void) {
    clear_error();
    ArxIngestionOptions* options = malloc(sizeof(ArxIngestionOptions));
    if (!options) {
        set_error("Failed to allocate memory for options");
        return NULL;
    }
    
    *options = arx_ingestion_get_default_options();
    return options;
}

bool cgo_arx_ingestion_validate_options(const void* options) {
    clear_error();
    if (!options) {
        set_error("Options cannot be NULL");
        return false;
    }
    return arx_ingestion_validate_options((const ArxIngestionOptions*)options);
}

int cgo_arx_ingestion_get_supported_formats(char** formats, int max_formats) {
    clear_error();
    if (!formats || max_formats <= 0) {
        set_error("Formats array and max_formats must be valid");
        return 0;
    }
    return arx_ingestion_get_supported_formats(formats, max_formats);
}

char* cgo_arx_ingestion_get_statistics(void) {
    clear_error();
    return arx_ingestion_get_statistics();
}

void cgo_arx_ingestion_clear_statistics(void) {
    clear_error();
    arx_ingestion_clear_statistics();
}

// ============================================================================
// AUTHENTICATION BRIDGE FUNCTIONS
// ============================================================================

bool cgo_arx_auth_init(const void* options) {
    clear_error();
    if (options) {
        const ArxAuthOptions* opts = (const ArxAuthOptions*)options;
        bool result = arx_auth_init(opts);
        if (!result) {
            set_error("Failed to initialize authentication system");
        }
        return result;
    }
    return arx_auth_init(NULL);
}

void cgo_arx_auth_cleanup(void) {
    clear_error();
    arx_auth_cleanup();
}

void* cgo_arx_auth_create_jwt(const void* claims, const char* secret) {
    clear_error();
    if (!claims || !secret) {
        set_error("Claims and secret cannot be NULL");
        return NULL;
    }
    
    const ArxJWTClaims* jwt_claims = (const ArxJWTClaims*)claims;
    ArxJWTToken* token = arx_auth_create_jwt(jwt_claims, secret);
    
    if (!token) {
        set_error("Failed to create JWT token");
        return NULL;
    }
    
    return token;
}

void* cgo_arx_auth_parse_jwt(const char* token_string, const char* secret) {
    clear_error();
    if (!token_string || !secret) {
        set_error("Token string and secret cannot be NULL");
        return NULL;
    }
    
    ArxJWTToken* token = arx_auth_parse_jwt(token_string, secret);
    
    if (!token) {
        set_error("Failed to parse JWT token");
        return NULL;
    }
    
    return token;
}

bool cgo_arx_auth_verify_jwt(const void* token, const char* secret) {
    clear_error();
    if (!token || !secret) {
        set_error("Token and secret cannot be NULL");
        return false;
    }
    
    const ArxJWTToken* jwt_token = (const ArxJWTToken*)token;
    return arx_auth_verify_jwt(jwt_token, secret);
}

void cgo_arx_auth_destroy_jwt(void* token) {
    clear_error();
    if (token) {
        arx_auth_destroy_jwt((ArxJWTToken*)token);
    }
}

char* cgo_arx_auth_hash_password(const char* password, int cost) {
    clear_error();
    if (!password) {
        set_error("Password cannot be NULL");
        return NULL;
    }
    
    char* hash = arx_auth_hash_password(password, cost);
    if (!hash) {
        set_error("Failed to hash password");
        return NULL;
    }
    
    return hash;
}

bool cgo_arx_auth_verify_password(const char* password, const char* hash) {
    clear_error();
    if (!password || !hash) {
        set_error("Password and hash cannot be NULL");
        return false;
    }
    
    return arx_auth_verify_password(password, hash);
}

char* cgo_arx_auth_generate_password(int length, bool include_symbols) {
    clear_error();
    if (length <= 0) {
        set_error("Password length must be positive");
        return NULL;
    }
    
    char* password = arx_auth_generate_password(length, include_symbols);
    if (!password) {
        set_error("Failed to generate password");
        return NULL;
    }
    
    return password;
}

void* cgo_arx_auth_create_user(const char* username, const char* email,
                               const char* password, bool is_admin) {
    clear_error();
    if (!username || !email || !password) {
        set_error("Username, email, and password cannot be NULL");
        return NULL;
    }
    
    ArxUser* user = arx_auth_create_user(username, email, password, is_admin);
    if (!user) {
        set_error("Failed to create user");
        return NULL;
    }
    
    return user;
}

void* cgo_arx_auth_authenticate_user(const char* username, const char* password) {
    clear_error();
    if (!username || !password) {
        set_error("Username and password cannot be NULL");
        return NULL;
    }
    
    ArxAuthResult* result = arx_auth_authenticate_user(username, password);
    if (!result) {
        set_error("Failed to authenticate user");
        return NULL;
    }
    
    return result;
}

void* cgo_arx_auth_get_user(uint32_t user_id) {
    clear_error();
    ArxUser* user = arx_auth_get_user(user_id);
    if (!user) {
        set_error("User not found");
        return NULL;
    }
    
    return user;
}

void* cgo_arx_auth_get_user_by_username(const char* username) {
    clear_error();
    if (!username) {
        set_error("Username cannot be NULL");
        return NULL;
    }
    
    ArxUser* user = arx_auth_get_user_by_username(username);
    if (!user) {
        set_error("User not found");
        return NULL;
    }
    return user;
}

bool cgo_arx_auth_update_password(uint32_t user_id, const char* old_password,
                                 const char* new_password) {
    clear_error();
    if (!old_password || !new_password) {
        set_error("Old and new passwords cannot be NULL");
        return false;
    }
    
    bool result = arx_auth_update_password(user_id, old_password, new_password);
    if (!result) {
        set_error("Failed to update password");
    }
    
    return result;
}

void cgo_arx_auth_destroy_user(void* user) {
    clear_error();
    if (user) {
        arx_auth_destroy_user((ArxUser*)user);
    }
}

char* cgo_arx_auth_generate_refresh_token(uint32_t user_id, const char* user_agent,
                                         const char* ip_address) {
    clear_error();
    if (!user_agent || !ip_address) {
        set_error("User agent and IP address cannot be NULL");
        return NULL;
    }
    
    char* token = arx_auth_generate_refresh_token(user_id, user_agent, ip_address);
    if (!token) {
        set_error("Failed to generate refresh token");
        return NULL;
    }
    
    return token;
}

uint32_t cgo_arx_auth_validate_refresh_token(const char* token) {
    clear_error();
    if (!token) {
        set_error("Token cannot be NULL");
        return 0;
    }
    
    return arx_auth_validate_refresh_token(token);
}

bool cgo_arx_auth_revoke_refresh_token(const char* token, const char* reason) {
    clear_error();
    if (!token || !reason) {
        set_error("Token and reason cannot be NULL");
        return false;
    }
    
    bool result = arx_auth_revoke_refresh_token(token, reason);
    if (!result) {
        set_error("Failed to revoke refresh token");
    }
    
    return result;
}

int cgo_arx_auth_cleanup_refresh_tokens(void) {
    clear_error();
    return arx_auth_cleanup_refresh_tokens();
}

char* cgo_arx_auth_generate_2fa_secret(uint32_t user_id) {
    clear_error();
    char* secret = arx_auth_generate_2fa_secret(user_id);
    if (!secret) {
        set_error("Failed to generate 2FA secret");
        return NULL;
    }
    
    return secret;
}

bool cgo_arx_auth_verify_2fa_token(uint32_t user_id, const char* token) {
    clear_error();
    if (!token) {
        set_error("Token cannot be NULL");
        return false;
    }
    
    return arx_auth_verify_2fa_token(user_id, token);
}

bool cgo_arx_auth_enable_2fa(uint32_t user_id) {
    clear_error();
    bool result = arx_auth_enable_2fa(user_id);
    if (!result) {
        set_error("Failed to enable 2FA");
    }
    
    return result;
}

bool cgo_arx_auth_disable_2fa(uint32_t user_id) {
    clear_error();
    bool result = arx_auth_disable_2fa(user_id);
    if (!result) {
        set_error("Failed to disable 2FA");
    }
    
    return result;
}

char* cgo_arx_auth_generate_secure_token(int length) {
    clear_error();
    if (length <= 0) {
        set_error("Token length must be positive");
        return NULL;
    }
    
    char* token = arx_auth_generate_secure_token(length);
    if (!token) {
        set_error("Failed to generate secure token");
        return NULL;
    }
    
    return token;
}

char* cgo_arx_auth_get_statistics(void) {
    clear_error();
    return arx_auth_get_statistics();
}

bool cgo_arx_auth_is_healthy(void) {
    clear_error();
    return arx_auth_is_healthy();
}

// ============================================================================
// DATABASE BRIDGE FUNCTIONS
// ============================================================================

bool cgo_arx_database_init(const void* config) {
    clear_error();
    if (!config) {
        set_error("Invalid database configuration");
        return false;
    }
    
    const ArxDatabaseConfig* db_config = (const ArxDatabaseConfig*)config;
    bool result = arx_database_init(db_config);
    if (!result) {
        set_error("Failed to initialize database: %s", arx_database_get_last_error());
    }
    
    return result;
}

void cgo_arx_database_cleanup(void) {
    clear_error();
    arx_database_cleanup();
}

bool cgo_arx_database_is_connected(void) {
    clear_error();
    return arx_database_is_connected();
}

bool cgo_arx_database_test_connection(void) {
    clear_error();
    bool result = arx_database_test_connection();
    if (!result) {
        set_error("Database connection test failed: %s", arx_database_get_last_error());
    }
    
    return result;
}

const void* cgo_arx_database_get_pool_stats(void) {
    clear_error();
    return arx_database_get_pool_stats();
}

void cgo_arx_database_reset_pool_stats(void) {
    clear_error();
    arx_database_reset_pool_stats();
}

bool cgo_arx_database_configure_pool(int max_open, int max_idle, int lifetime, int idle_timeout) {
    clear_error();
    bool result = arx_database_configure_pool(max_open, max_idle, lifetime, idle_timeout);
    if (!result) {
        set_error("Failed to configure connection pool: %s", arx_database_get_last_error());
    }
    
    return result;
}

uint64_t cgo_arx_database_begin_transaction(const char* description) {
    clear_error();
    uint64_t transaction_id = arx_database_begin_transaction(description);
    if (transaction_id == 0) {
        set_error("Failed to begin transaction: %s", arx_database_get_last_error());
    }
    
    return transaction_id;
}

bool cgo_arx_database_commit_transaction(uint64_t transaction_id) {
    clear_error();
    bool result = arx_database_commit_transaction(transaction_id);
    if (!result) {
        set_error("Failed to commit transaction: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_rollback_transaction(uint64_t transaction_id) {
    clear_error();
    bool result = arx_database_rollback_transaction(transaction_id);
    if (!result) {
        set_error("Failed to rollback transaction: %s", arx_database_get_last_error());
    }
    
    return result;
}

const void* cgo_arx_database_get_transaction(uint64_t transaction_id) {
    clear_error();
    return arx_database_get_transaction(transaction_id);
}

void* cgo_arx_database_execute_query(const char* query, const char** params, int param_count) {
    clear_error();
    if (!query) {
        set_error("Query cannot be NULL");
        return NULL;
    }
    
    ArxQueryResult* result = arx_database_execute_query(query, params, param_count);
    if (!result) {
        set_error("Failed to execute query: %s", arx_database_get_last_error());
    }
    
    return result;
}

void* cgo_arx_database_execute_simple_query(const char* query) {
    clear_error();
    if (!query) {
        set_error("Query cannot be NULL");
        return NULL;
    }
    
    ArxQueryResult* result = arx_database_execute_simple_query(query);
    if (!result) {
        set_error("Failed to execute simple query: %s", arx_database_get_last_error());
    }
    
    return result;
}

void* cgo_arx_database_execute_prepared(const char* statement_name, const char** params, int param_count) {
    clear_error();
    if (!statement_name) {
        set_error("Statement name cannot be NULL");
        return NULL;
    }
    
    ArxQueryResult* result = arx_database_execute_prepared(statement_name, params, param_count);
    if (!result) {
        set_error("Failed to execute prepared statement: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_prepare_statement(const char* statement_name, const char* query) {
    clear_error();
    bool result = arx_database_prepare_statement(statement_name, query);
    if (!result) {
        set_error("Failed to prepare statement: %s", arx_database_get_last_error());
    }
    
    return result;
}

void cgo_arx_database_free_result(void* result) {
    if (result) {
        arx_database_free_result((ArxQueryResult*)result);
    }
}

const char* cgo_arx_database_get_field_value(const void* result, int row_index, const char* column_name) {
    if (!result || !column_name) {
        return NULL;
    }
    
    return arx_database_get_field_value((const ArxQueryResult*)result, row_index, column_name);
}

const char* cgo_arx_database_get_field_value_by_index(const void* result, int row_index, int column_index) {
    if (!result) {
        return NULL;
    }
    
    return arx_database_get_field_value_by_index((const ArxQueryResult*)result, row_index, column_index);
}

char* cgo_arx_database_escape_string(const char* input) {
    clear_error();
    if (!input) {
        set_error("Input string cannot be NULL");
        return NULL;
    }
    
    char* escaped = arx_database_escape_string(input);
    if (!escaped) {
        set_error("Failed to escape string: %s", arx_database_get_last_error());
    }
    
    return escaped;
}

const char* cgo_arx_database_get_last_error(void) {
    return arx_database_get_last_error();
}

void cgo_arx_database_clear_last_error(void) {
    arx_database_clear_last_error();
}

const void* cgo_arx_database_get_metrics(void) {
    clear_error();
    return arx_database_get_metrics();
}

void cgo_arx_database_reset_metrics(void) {
    clear_error();
    arx_database_reset_metrics();
}

bool cgo_arx_database_is_healthy(void) {
    clear_error();
    return arx_database_is_healthy();
}

bool cgo_arx_database_create_table(const char* table_name, const char* schema) {
    clear_error();
    if (!table_name || !schema) {
        set_error("Table name and schema cannot be NULL");
        return false;
    }
    
    bool result = arx_database_create_table(table_name, schema);
    if (!result) {
        set_error("Failed to create table: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_drop_table(const char* table_name) {
    clear_error();
    if (!table_name) {
        set_error("Table name cannot be NULL");
        return false;
    }
    
    bool result = arx_database_drop_table(table_name);
    if (!result) {
        set_error("Failed to drop table: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_table_exists(const char* table_name) {
    clear_error();
    if (!table_name) {
        set_error("Table name cannot be NULL");
        return false;
    }
    
    return arx_database_table_exists(table_name);
}

char* cgo_arx_database_get_table_schema(const char* table_name) {
    clear_error();
    if (!table_name) {
        set_error("Table name cannot be NULL");
        return NULL;
    }
    
    char* schema = arx_database_get_table_schema(table_name);
    if (!schema) {
        set_error("Failed to get table schema: %s", arx_database_get_last_error());
    }
    
    return schema;
}

bool cgo_arx_database_create_index(const char* table_name, const char* index_name, const char* columns, const char* index_type) {
    clear_error();
    if (!table_name || !index_name || !columns) {
        set_error("Table name, index name, and columns cannot be NULL");
        return false;
    }
    
    bool result = arx_database_create_index(table_name, index_name, columns, index_type);
    if (!result) {
        set_error("Failed to create index: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_drop_index(const char* table_name, const char* index_name) {
    clear_error();
    if (!table_name || !index_name) {
        set_error("Table name and index name cannot be NULL");
        return false;
    }
    
    bool result = arx_database_drop_index(table_name, index_name);
    if (!result) {
        set_error("Failed to drop index: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_create_backup(const char* backup_path) {
    clear_error();
    if (!backup_path) {
        set_error("Backup path cannot be NULL");
        return false;
    }
    
    bool result = arx_database_create_backup(backup_path);
    if (!result) {
        set_error("Failed to create backup: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_restore_backup(const char* backup_path) {
    clear_error();
    if (!backup_path) {
        set_error("Backup path cannot be NULL");
        return false;
    }
    
    bool result = arx_database_restore_backup(backup_path);
    if (!result) {
        set_error("Failed to restore backup: %s", arx_database_get_last_error());
    }
    
    return result;
}

bool cgo_arx_database_verify_backup(const char* backup_path) {
    clear_error();
    if (!backup_path) {
        set_error("Backup path cannot be NULL");
        return false;
    }
    
    return arx_database_verify_backup(backup_path);
}

// ============================================================================
// WALL COMPOSITION BRIDGE FUNCTIONS
// ============================================================================

arx_wall_composition_engine_t* cgo_wall_composition_engine_create(double max_gap_distance, 
                                                                 double parallel_threshold, 
                                                                 double confidence_threshold) {
    clear_error();
    
    arx_composition_config_t config = arx_composition_config_default();
    config.max_gap_distance = max_gap_distance;
    config.parallel_threshold = parallel_threshold;
    config.confidence_threshold = confidence_threshold;
    
    arx_wall_composition_engine_t* engine = arx_wall_composition_engine_new(&config);
    if (!engine) {
        set_error("Failed to create wall composition engine");
        return NULL;
    }
    
    clear_error();
    return engine;
}

void cgo_wall_composition_engine_destroy(arx_wall_composition_engine_t* engine) {
    if (engine) {
        arx_wall_composition_engine_free(engine);
    }
}

arx_wall_segment_t* cgo_wall_segment_create(uint64_t id, 
                                           double start_x, double start_y, double start_z,
                                           double end_x, double end_y, double end_z,
                                           double height, double thickness, double confidence) {
    clear_error();
    
    if (confidence < 0.0 || confidence > 1.0) {
        set_error("Confidence must be between 0.0 and 1.0");
        return NULL;
    }
    
    arx_wall_segment_t* segment = arx_wall_segment_new();
    if (!segment) {
        set_error("Failed to create wall segment");
        return NULL;
    }
    
    // Set segment properties
    segment->id = id;
    segment->height = height;
    segment->thickness = thickness;
    segment->confidence = confidence;
    
    // Create and set points
    arx_smart_point_3d_t start_point = arx_smart_point_3d_new((int64_t)start_x, (int64_t)start_y, (int64_t)start_z, ARX_UNIT_MILLIMETER);
    arx_smart_point_3d_t end_point = arx_smart_point_3d_new((int64_t)end_x, (int64_t)end_y, (int64_t)end_z, ARX_UNIT_MILLIMETER);
    
    arx_wall_segment_set_points(segment, &start_point, &end_point);
    
    clear_error();
    return segment;
}

void cgo_wall_segment_destroy(arx_wall_segment_t* segment) {
    if (segment) {
        arx_wall_segment_free(segment);
    }
}

arx_curved_wall_segment_t* cgo_curved_wall_segment_create(uint64_t id,
                                                          arx_curve_type_t curve_type,
                                                          double center_x, double center_y, double center_z,
                                                          double radius, double start_angle, double end_angle,
                                                          double height, double thickness, double confidence) {
    clear_error();
    
    if (confidence < 0.0 || confidence > 1.0) {
        set_error("Confidence must be between 0.0 and 1.0");
        return NULL;
    }
    
    arx_curved_wall_segment_t* segment = arx_curved_wall_segment_new();
    if (!segment) {
        set_error("Failed to create curved wall segment");
        return NULL;
    }
    
    // Set base properties
    segment->base.id = id;
    segment->base.height = height;
    segment->base.thickness = thickness;
    segment->base.confidence = confidence;
    
    // Set curve-specific properties based on type
    switch (curve_type) {
        case ARX_CURVE_TYPE_ARC: {
            arx_smart_point_3d_t center = arx_smart_point_3d_new((int64_t)center_x, (int64_t)center_y, (int64_t)center_z, ARX_UNIT_MILLIMETER);
            arx_curved_wall_segment_set_arc(segment, &center, radius, start_angle, end_angle);
            break;
        }
        case ARX_CURVE_TYPE_BEZIER_QUADRATIC: {
            arx_smart_point_3d_t control1 = arx_smart_point_3d_new((int64_t)center_x, (int64_t)center_y, (int64_t)center_z, ARX_UNIT_MILLIMETER);
            arx_smart_point_3d_t control2 = arx_smart_point_3d_new((int64_t)(center_x + radius), (int64_t)(center_y + radius), (int64_t)center_z, ARX_UNIT_MILLIMETER);
            arx_curved_wall_segment_set_bezier_quadratic(segment, &control1, &control2);
            break;
        }
        case ARX_CURVE_TYPE_BEZIER_CUBIC: {
            arx_smart_point_3d_t control1 = arx_smart_point_3d_new((int64_t)center_x, (int64_t)center_y, (int64_t)center_z, ARX_UNIT_MILLIMETER);
            arx_smart_point_3d_t control2 = arx_smart_point_3d_new((int64_t)(center_x + radius), (int64_t)(center_y + radius), (int64_t)center_z, ARX_UNIT_MILLIMETER);
            arx_smart_point_3d_t control3 = arx_smart_point_3d_new((int64_t)(center_x + radius * 2), (int64_t)(center_y + radius * 2), (int64_t)center_z, ARX_UNIT_MILLIMETER);
            arx_curved_wall_segment_set_bezier_cubic(segment, &control1, &control2, &control3);
            break;
        }
        default:
            set_error("Unsupported curve type: %d", curve_type);
            arx_curved_wall_segment_free(segment);
            return NULL;
    }
    
    clear_error();
    return segment;
}

void cgo_curved_wall_segment_destroy(arx_curved_wall_segment_t* segment) {
    if (segment) {
        arx_curved_wall_segment_free(segment);
    }
}

arx_wall_structure_t** cgo_wall_composition_compose_walls(arx_wall_composition_engine_t* engine,
                                                          arx_wall_segment_t** segments,
                                                          uint32_t segment_count,
                                                          uint32_t* structure_count) {
    clear_error();
    
    if (!engine || !segments || !structure_count) {
        set_error("Invalid parameters for wall composition");
        return NULL;
    }
    
    arx_wall_structure_t** structures = arx_wall_composition_engine_compose_walls(engine, segments, segment_count, structure_count);
    if (!structures) {
        set_error("Failed to compose walls");
        return NULL;
    }
    
    clear_error();
    return structures;
}

arx_wall_connection_t** cgo_wall_composition_detect_connections(arx_wall_composition_engine_t* engine,
                                                               arx_wall_segment_t** segments,
                                                               uint32_t segment_count,
                                                               uint32_t* connection_count) {
    clear_error();
    
    if (!engine || !segments || !connection_count) {
        set_error("Invalid parameters for connection detection");
        return NULL;
    }
    
    arx_wall_connection_t** connections = arx_wall_composition_engine_detect_connections(engine, segments, segment_count, connection_count);
    if (!connections) {
        set_error("Failed to detect wall connections");
        return NULL;
    }
    
    clear_error();
    return connections;
}

void cgo_wall_structure_get_properties(arx_wall_structure_t* structure,
                                      double* total_length,
                                      double* max_height,
                                      double* overall_confidence) {
    if (!structure || !total_length || !max_height || !overall_confidence) {
        return;
    }
    
    *total_length = arx_wall_structure_get_total_length(structure);
    *max_height = arx_wall_structure_get_max_height(structure);
    *overall_confidence = arx_wall_structure_get_overall_confidence(structure);
}

void cgo_wall_composition_free_structures(arx_wall_structure_t** structures, uint32_t count) {
    if (structures) {
        arx_wall_composition_free_structures(structures, count);
    }
}

void cgo_wall_composition_free_connections(arx_wall_connection_t** connections, uint32_t count) {
    if (connections) {
        arx_wall_composition_free_connections(connections, count);
    }
}

// ============================================================================
// UTILITY BRIDGE FUNCTIONS
// ============================================================================

void cgo_free_string(char* str) {
    if (str) {
        free(str);
    }
}

void cgo_free_object_array(ArxObject** objects, int count) {
    if (objects && count > 0) {
        // Note: We don't destroy the ArxObjects themselves, just free the array
        // The caller is responsible for managing ArxObject lifecycle
        free(objects);
    }
}

char* cgo_get_last_error(void) {
    if (last_error_message) {
        return strdup(last_error_message);
    }
    return NULL;
}

void cgo_clear_last_error(void) {
    clear_error();
}
