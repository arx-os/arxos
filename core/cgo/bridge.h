/**
 * @file bridge.h
 * @brief C-Go Bridge Interface for ARXOS Core
 * 
 * Provides the interface layer between Go services and C core components.
 * This enables Go to call C functions directly for performance-critical operations.
 */

#ifndef ARXOS_CGO_BRIDGE_H
#define ARXOS_CGO_BRIDGE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "arxobject/arxobject.h"
#include "ascii/ascii_engine.h"
#include "building/arx_building.h"
#include "version/arx_version.h"
#include "spatial/arx_spatial.h"
#include "ingestion/arx_ingestion.h"
#include "auth/arx_auth.h"
#include "database/arx_database.h"
#include "wall_composition/arx_wall_composition.h"

// ============================================================================
// CGO EXPORT MACROS
// ============================================================================

#ifdef _WIN32
    #define CGO_EXPORT __declspec(dllexport)
#else
    #define CGO_EXPORT __attribute__((visibility("default")))
#endif

// ============================================================================
// ARXOBJECT BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Create ArxObject from Go
 * @param id Object ID string
 * @param type Object type enum value
 * @param name Object name string
 * @param description Object description string
 * @return Pointer to created ArxObject or NULL on failure
 */
CGO_EXPORT ArxObject* cgo_arx_object_create(const char* id, int type, 
                                           const char* name, const char* description);

/**
 * @brief Destroy ArxObject from Go
 * @param obj Pointer to ArxObject to destroy
 */
CGO_EXPORT void cgo_arx_object_destroy(ArxObject* obj);

/**
 * @brief Set ArxObject property from Go
 * @param obj Pointer to ArxObject
 * @param key Property key string
 * @param value Property value string
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_object_set_property(ArxObject* obj, const char* key, const char* value);

/**
 * @brief Get ArxObject property from Go
 * @param obj Pointer to ArxObject
 * @param key Property key string
 * @return Property value string (caller must free) or NULL if not found
 */
CGO_EXPORT char* cgo_arx_object_get_property(ArxObject* obj, const char* key);

// ============================================================================
// ASCII ENGINE BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Generate 2D floor plan from Go
 * @param objects Array of ArxObject pointers
 * @param object_count Number of objects
 * @param width Canvas width in characters
 * @param height Canvas height in characters
 * @param scale Pixels per millimeter
 * @return ASCII string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_generate_2d_floor_plan(ArxObject** objects, int object_count,
                                           int width, int height, double scale);

/**
 * @brief Generate 3D building view from Go
 * @param objects Array of ArxObject pointers
 * @param object_count Number of objects
 * @param width Canvas width in characters
 * @param height Canvas height in characters
 * @param depth Canvas depth in characters
 * @param scale Pixels per millimeter
 * @return ASCII string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_generate_3d_building_view(ArxObject** objects, int object_count,
                                              int width, int height, int depth, double scale);

// ============================================================================
// BUILDING MANAGEMENT BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Create ArxBuilding from Go
 * @param name Building name string
 * @param description Building description string
 * @return Pointer to created ArxBuilding or NULL on failure
 */
CGO_EXPORT ArxBuilding* cgo_arx_building_create(const char* name, const char* description);

/**
 * @brief Destroy ArxBuilding from Go
 * @param building Pointer to ArxBuilding to destroy
 */
CGO_EXPORT void cgo_arx_building_destroy(ArxBuilding* building);

/**
 * @brief Add object to building from Go
 * @param building Pointer to ArxBuilding
 * @param object Pointer to ArxObject to add
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_building_add_object(ArxBuilding* building, ArxObject* object);

/**
 * @brief Get building statistics from Go
 * @param building Pointer to ArxBuilding
 * @return Statistics string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_building_get_summary(ArxBuilding* building);

// ============================================================================
// VERSION CONTROL BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Initialize version control repository from Go
 * @param repo_path Repository path string
 * @param author_name Author name string
 * @param author_email Author email string
 * @return Pointer to ArxVersionControl or NULL on failure
 */
CGO_EXPORT ArxVersionControl* cgo_arx_version_init_repo(const char* repo_path,
                                                       const char* author_name,
                                                       const char* author_email);

/**
 * @brief Commit changes from Go
 * @param vc Pointer to ArxVersionControl
 * @param message Commit message string
 * @param author Author name string (optional, uses default if NULL)
 * @param email Author email string (optional, uses default if NULL)
 * @return Commit hash string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_version_commit(ArxVersionControl* vc, const char* message,
                                       const char* author, const char* email);

/**
 * @brief Get commit history from Go
 * @param vc Pointer to ArxVersionControl
 * @param max_commits Maximum number of commits to return
 * @return History string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_version_get_history(ArxVersionControl* vc, int max_commits);

// ============================================================================
// SPATIAL INDEXING BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Create spatial index from Go
 * @param max_depth Maximum octree depth
 * @param use_octree Whether to use octree (true) or R-tree (false)
 * @return Pointer to ArxSpatialIndex or NULL on failure
 */
CGO_EXPORT ArxSpatialIndex* cgo_arx_spatial_create_index(int max_depth, bool use_octree);

/**
 * @brief Add object to spatial index from Go
 * @param index Pointer to ArxSpatialIndex
 * @param object Pointer to ArxObject to add
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_spatial_add_object(ArxSpatialIndex* index, ArxObject* object);

/**
 * @brief Query spatial index from Go
 * @param index Pointer to ArxSpatialIndex
 * @param query_type Query type (0=range, 1=point, 2=nearest, 3=intersect)
 * @param x X coordinate or range start
 * @param y Y coordinate or range start
 * @param z Z coordinate or range start
 * @param x2 X range end (for range queries)
 * @param y2 Y range end (for range queries)
 * @param z2 Z range end (for range queries)
 * @param radius Search radius (for nearest queries)
 * @param max_results Maximum results to return
 * @param result_count Output parameter for actual result count
 * @return Array of ArxObject pointers (caller must free) or NULL on failure
 */
CGO_EXPORT ArxObject** cgo_arx_spatial_query(ArxSpatialIndex* index, int query_type,
                                            double x, double y, double z,
                                            double x2, double y2, double z2,
                                            double radius, int max_results,
                                            int* result_count);

/**
 * @brief Get spatial index statistics from Go
 * @param index Pointer to ArxSpatialIndex
 * @return Statistics string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_spatial_get_statistics(ArxSpatialIndex* index);

// ============================================================================
// INGESTION BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Initialize ingestion system from Go
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_ingestion_init(void);

/**
 * @brief Cleanup ingestion system from Go
 */
CGO_EXPORT void cgo_arx_ingestion_cleanup(void);

/**
 * @brief Detect file format from Go
 * @param filepath File path string
 * @return File format enum value
 */
CGO_EXPORT int cgo_arx_ingestion_detect_format(const char* filepath);

/**
 * @brief Get file metadata from Go
 * @param filepath File path string
 * @param metadata Output metadata structure
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_ingestion_get_metadata(const char* filepath, void* metadata);

/**
 * @brief Process file and create ArxObjects from Go
 * @param filepath File path string
 * @param options Processing options structure
 * @return Processing result structure (caller must free)
 */
CGO_EXPORT void* cgo_arx_ingestion_process_file(const char* filepath, const void* options);

/**
 * @brief Free ingestion result from Go
 * @param result Result structure to free
 */
CGO_EXPORT void cgo_arx_ingestion_free_result(void* result);

/**
 * @brief Get default ingestion options from Go
 * @return Default options structure
 */
CGO_EXPORT void* cgo_arx_ingestion_get_default_options(void);

/**
 * @brief Validate ingestion options from Go
 * @param options Options structure to validate
 * @return true if valid, false if invalid
 */
CGO_EXPORT bool cgo_arx_ingestion_validate_options(const void* options);

/**
 * @brief Get supported formats from Go
 * @param formats Output array of format strings
 * @param max_formats Maximum number of formats to return
 * @return Number of formats returned
 */
CGO_EXPORT int cgo_arx_ingestion_get_supported_formats(char** formats, int max_formats);

/**
 * @brief Get ingestion statistics from Go
 * @return Statistics string (caller must free)
 */
CGO_EXPORT char* cgo_arx_ingestion_get_statistics(void);

/**
 * @brief Clear ingestion statistics from Go
 */
CGO_EXPORT void cgo_arx_ingestion_clear_statistics(void);

// ============================================================================
// AUTHENTICATION BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Initialize authentication system from Go
 * @param options Authentication options structure
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_auth_init(const void* options);

/**
 * @brief Cleanup authentication system from Go
 */
CGO_EXPORT void cgo_arx_auth_cleanup(void);

/**
 * @brief Create JWT token from Go
 * @param claims JWT claims structure
 * @param secret Secret key string
 * @return JWT token structure (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_auth_create_jwt(const void* claims, const char* secret);

/**
 * @brief Parse JWT token from Go
 * @param token_string Raw JWT token string
 * @param secret Secret key string
 * @return JWT token structure (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_auth_parse_jwt(const char* token_string, const char* secret);

/**
 * @brief Verify JWT token from Go
 * @param token JWT token structure
 * @param secret Secret key string
 * @return true if valid, false otherwise
 */
CGO_EXPORT bool cgo_arx_auth_verify_jwt(const void* token, const char* secret);

/**
 * @brief Destroy JWT token from Go
 * @param token JWT token structure to destroy
 */
CGO_EXPORT void cgo_arx_auth_destroy_jwt(void* token);

/**
 * @brief Hash password from Go
 * @param password Plain text password
 * @param cost bcrypt cost factor
 * @return Hashed password (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_auth_hash_password(const char* password, int cost);

/**
 * @brief Verify password from Go
 * @param password Plain text password
 * @param hash Hashed password
 * @return true if password matches, false otherwise
 */
CGO_EXPORT bool cgo_arx_auth_verify_password(const char* password, const char* secret);

/**
 * @brief Generate secure password from Go
 * @param length Password length
 * @param include_symbols Whether to include symbols
 * @return Generated password (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_auth_generate_password(int length, bool include_symbols);

/**
 * @brief Create user from Go
 * @param username Username string
 * @param email Email string
 * @param password Plain text password
 * @param is_admin Whether user is admin
 * @return User structure (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_auth_create_user(const char* username, const char* email,
                                          const char* password, bool is_admin);

/**
 * @brief Authenticate user from Go
 * @param username Username or email
 * @param password Plain text password
 * @return Authentication result (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_auth_authenticate_user(const char* username, const char* password);

/**
 * @brief Get user by ID from Go
 * @param user_id User ID
 * @return User structure (caller must free) or NULL if not found
 */
CGO_EXPORT void* cgo_arx_auth_get_user(uint32_t user_id);

/**
 * @brief Get user by username from Go
 * @param username Username string
 * @return User structure (caller must free) or NULL if not found
 */
CGO_EXPORT void* cgo_arx_auth_get_user_by_username(const char* username);

/**
 * @brief Update user password from Go
 * @param user_id User ID
 * @param old_password Old password
 * @param new_password New password
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_auth_update_password(uint32_t user_id, const char* old_password,
                                            const char* new_password);

/**
 * @brief Destroy user from Go
 * @param user User structure to destroy
 */
CGO_EXPORT void cgo_arx_auth_destroy_user(void* user);

/**
 * @brief Generate refresh token from Go
 * @param user_id User ID
 * @param user_agent User agent string
 * @param ip_address IP address string
 * @return Refresh token (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_auth_generate_refresh_token(uint32_t user_id, const char* user_agent,
                                                     const char* ip_address);

/**
 * @brief Validate refresh token from Go
 * @param token Refresh token string
 * @return User ID if valid, 0 on failure
 */
CGO_EXPORT uint32_t cgo_arx_auth_validate_refresh_token(const char* token);

/**
 * @brief Revoke refresh token from Go
 * @param token Refresh token string
 * @param reason Reason for revocation
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_auth_revoke_refresh_token(const char* token, const char* reason);

/**
 * @brief Cleanup expired refresh tokens from Go
 * @return Number of tokens cleaned up
 */
CGO_EXPORT int cgo_arx_auth_cleanup_refresh_tokens(void);

/**
 * @brief Generate 2FA secret from Go
 * @param user_id User ID
 * @return Secret key (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_auth_generate_2fa_secret(uint32_t user_id);

/**
 * @brief Verify 2FA token from Go
 * @param user_id User ID
 * @param token 2FA token string
 * @return true if valid, false otherwise
 */
CGO_EXPORT bool cgo_arx_auth_verify_2fa_token(uint32_t user_id, const char* token);

/**
 * @brief Enable 2FA for user from Go
 * @param user_id User ID
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_auth_enable_2fa(uint32_t user_id);

/**
 * @brief Disable 2FA for user from Go
 * @param user_id User ID
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_auth_disable_2fa(uint32_t user_id);

/**
 * @brief Generate secure token from Go
 * @param length Token length in bytes
 * @return Generated token (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_auth_generate_secure_token(int length);

/**
 * @brief Get authentication statistics from Go
 * @return Statistics string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_auth_get_statistics(void);

/**
 * @brief Check authentication system health from Go
 * @return true if healthy, false otherwise
 */
CGO_EXPORT bool cgo_arx_auth_is_healthy(void);

// ============================================================================
// DATABASE BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Initialize database system from Go
 * @param config Database configuration (caller must free)
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_init(const void* config);

/**
 * @brief Cleanup database system from Go
 */
CGO_EXPORT void cgo_arx_database_cleanup(void);

/**
 * @brief Check database connection status from Go
 * @return true if connected, false otherwise
 */
CGO_EXPORT bool cgo_arx_database_is_connected(void);

/**
 * @brief Test database connectivity from Go
 * @return true if connection test passes, false otherwise
 */
CGO_EXPORT bool cgo_arx_database_test_connection(void);

/**
 * @brief Get connection pool statistics from Go
 * @return Connection pool stats (caller must not free) or NULL on failure
 */
CGO_EXPORT const void* cgo_arx_database_get_pool_stats(void);

/**
 * @brief Reset connection pool statistics from Go
 */
CGO_EXPORT void cgo_arx_database_reset_pool_stats(void);

/**
 * @brief Configure connection pool from Go
 * @param max_open Maximum open connections
 * @param max_idle Maximum idle connections
 * @param lifetime Connection lifetime in seconds
 * @param idle_timeout Idle timeout in seconds
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_configure_pool(int max_open, int max_idle, int lifetime, int idle_timeout);

/**
 * @brief Begin transaction from Go
 * @param description Transaction description
 * @return Transaction ID on success, 0 on failure
 */
CGO_EXPORT uint64_t cgo_arx_database_begin_transaction(const char* description);

/**
 * @brief Commit transaction from Go
 * @param transaction_id Transaction ID
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_commit_transaction(uint64_t transaction_id);

/**
 * @brief Rollback transaction from Go
 * @param transaction_id Transaction ID
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_rollback_transaction(uint64_t transaction_id);

/**
 * @brief Get transaction status from Go
 * @param transaction_id Transaction ID
 * @return Transaction info (caller must not free) or NULL on failure
 */
CGO_EXPORT const void* cgo_arx_database_get_transaction(uint64_t transaction_id);

/**
 * @brief Execute query from Go
 * @param query SQL query string
 * @param params Query parameters array
 * @param param_count Number of parameters
 * @return Query result (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_database_execute_query(const char* query, const char** params, int param_count);

/**
 * @brief Execute simple query from Go
 * @param query SQL query string
 * @return Query result (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_database_execute_simple_query(const char* query);

/**
 * @brief Execute prepared statement from Go
 * @param statement_name Name of prepared statement
 * @param params Query parameters array
 * @param param_count Number of parameters
 * @return Query result (caller must free) or NULL on failure
 */
CGO_EXPORT void* cgo_arx_database_execute_prepared(const char* statement_name, const char** params, int param_count);

/**
 * @brief Prepare statement from Go
 * @param statement_name Name for prepared statement
 * @param query SQL query string
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_prepare_statement(const char* statement_name, const char* query);

/**
 * @brief Free query result from Go
 * @param result Query result to free
 */
CGO_EXPORT void cgo_arx_database_free_result(void* result);

/**
 * @brief Get field value by name from Go
 * @param result Query result
 * @param row_index Row index (0-based)
 * @param column_name Column name
 * @return Field value or NULL if not found
 */
CGO_EXPORT const char* cgo_arx_database_get_field_value(const void* result, int row_index, const char* column_name);

/**
 * @brief Get field value by index from Go
 * @param result Query result
 * @param row_index Row index (0-based)
 * @param column_index Column index (0-based)
 * @return Field value or NULL if invalid indices
 */
CGO_EXPORT const char* cgo_arx_database_get_field_value_by_index(const void* result, int row_index, int column_index);

/**
 * @brief Escape string for SQL from Go
 * @param input Input string to escape
 * @return Escaped string (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_database_escape_string(const char* input);

/**
 * @brief Get last database error from Go
 * @return Last error message (caller must not free)
 */
CGO_EXPORT const char* cgo_arx_database_get_last_error(void);

/**
 * @brief Clear last database error from Go
 */
CGO_EXPORT void cgo_arx_database_clear_last_error(void);

/**
 * @brief Get database metrics from Go
 * @return Database metrics (caller must not free) or NULL on failure
 */
CGO_EXPORT const void* cgo_arx_database_get_metrics(void);

/**
 * @brief Reset database metrics from Go
 */
CGO_EXPORT void cgo_arx_database_reset_metrics(void);

/**
 * @brief Check database health from Go
 * @return true if healthy, false otherwise
 */
CGO_EXPORT bool cgo_arx_database_is_healthy(void);

/**
 * @brief Create table from Go
 * @param table_name Name of table to create
 * @param schema SQL schema definition
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_create_table(const char* table_name, const char* schema);

/**
 * @brief Drop table from Go
 * @param table_name Name of table to drop
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_drop_table(const char* table_name);

/**
 * @brief Check table exists from Go
 * @param table_name Name of table to check
 * @return true if exists, false otherwise
 */
CGO_EXPORT bool cgo_arx_database_table_exists(const char* table_name);

/**
 * @brief Get table schema from Go
 * @param table_name Name of table
 * @return Table schema (caller must free) or NULL on failure
 */
CGO_EXPORT char* cgo_arx_database_get_table_schema(const char* table_name);

/**
 * @brief Create index from Go
 * @param table_name Name of table
 * @param index_name Name of index
 * @param columns Comma-separated column names
 * @param index_type Type of index
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_create_index(const char* table_name, const char* index_name, const char* columns, const char* index_type);

/**
 * @brief Drop index from Go
 * @param table_name Name of table
 * @param index_name Name of index
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_drop_index(const char* table_name, const char* index_name);

/**
 * @brief Create database backup from Go
 * @param backup_path Path for backup file
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_create_backup(const char* backup_path);

/**
 * @brief Restore database from backup from Go
 * @param backup_path Path to backup file
 * @return true on success, false on failure
 */
CGO_EXPORT bool cgo_arx_database_restore_backup(const char* backup_path);

/**
 * @brief Verify backup integrity from Go
 * @param backup_path Path to backup file
 * @return true if backup is valid, false otherwise
 */
CGO_EXPORT bool cgo_arx_database_verify_backup(const char* backup_path);

// ============================================================================
// WALL COMPOSITION BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Create wall composition engine from Go
 * @param max_gap_distance Maximum gap distance for wall connections (mm)
 * @param parallel_threshold Threshold for considering walls parallel (degrees)
 * @param confidence_threshold Minimum confidence threshold for composition
 * @return Pointer to wall composition engine or NULL on failure
 */
CGO_EXPORT arx_wall_composition_engine_t* cgo_wall_composition_engine_create(double max_gap_distance, 
                                                                           double parallel_threshold, 
                                                                           double confidence_threshold);

/**
 * @brief Destroy wall composition engine from Go
 * @param engine Pointer to wall composition engine to destroy
 */
CGO_EXPORT void cgo_wall_composition_engine_destroy(arx_wall_composition_engine_t* engine);

/**
 * @brief Create wall segment from Go
 * @param id Segment ID
 * @param start_x Start X coordinate (mm)
 * @param start_y Start Y coordinate (mm)
 * @param start_z Start Z coordinate (mm)
 * @param end_x End X coordinate (mm)
 * @param end_y End Y coordinate (mm)
 * @param end_z End Z coordinate (mm)
 * @param height Wall height (mm)
 * @param thickness Wall thickness (mm)
 * @param confidence Segment confidence (0.0-1.0)
 * @return Pointer to wall segment or NULL on failure
 */
CGO_EXPORT arx_wall_segment_t* cgo_wall_segment_create(uint64_t id, 
                                                       double start_x, double start_y, double start_z,
                                                       double end_x, double end_y, double end_z,
                                                       double height, double thickness, double confidence);

/**
 * @brief Destroy wall segment from Go
 * @param segment Pointer to wall segment to destroy
 */
CGO_EXPORT void cgo_wall_segment_destroy(arx_wall_segment_t* segment);

/**
 * @brief Create curved wall segment from Go
 * @param id Segment ID
 * @param curve_type Type of curve (linear, arc, bezier)
 * @param center_x Center X coordinate for arcs (mm)
 * @param center_y Center Y coordinate for arcs (mm)
 * @param center_z Center Z coordinate for arcs (mm)
 * @param radius Radius for arcs (mm)
 * @param start_angle Start angle for arcs (radians)
 * @param end_angle End angle for arcs (radians)
 * @param height Wall height (mm)
 * @param thickness Wall thickness (mm)
 * @param confidence Segment confidence (0.0-1.0)
 * @return Pointer to curved wall segment or NULL on failure
 */
CGO_EXPORT arx_curved_wall_segment_t* cgo_curved_wall_segment_create(uint64_t id,
                                                                     arx_curve_type_t curve_type,
                                                                     double center_x, double center_y, double center_z,
                                                                     double radius, double start_angle, double end_angle,
                                                                     double height, double thickness, double confidence);

/**
 * @brief Destroy curved wall segment from Go
 * @param segment Pointer to curved wall segment to destroy
 */
CGO_EXPORT void cgo_curved_wall_segment_destroy(arx_curved_wall_segment_t* segment);

/**
 * @brief Compose walls from segments from Go
 * @param engine Wall composition engine
 * @param segments Array of wall segment pointers
 * @param segment_count Number of segments
 * @param structure_count Output parameter for number of structures created
 * @return Array of wall structure pointers (caller must free) or NULL on failure
 */
CGO_EXPORT arx_wall_structure_t** cgo_wall_composition_compose_walls(arx_wall_composition_engine_t* engine,
                                                                     arx_wall_segment_t** segments,
                                                                     uint32_t segment_count,
                                                                     uint32_t* structure_count);

/**
 * @brief Detect wall connections from Go
 * @param engine Wall composition engine
 * @param segments Array of wall segment pointers
 * @param segment_count Number of segments
 * @param connection_count Output parameter for number of connections detected
 * @return Array of wall connection pointers (caller must free) or NULL on failure
 */
CGO_EXPORT arx_wall_connection_t** cgo_wall_composition_detect_connections(arx_wall_composition_engine_t* engine,
                                                                          arx_wall_segment_t** segments,
                                                                          uint32_t segment_count,
                                                                          uint32_t* connection_count);

/**
 * @brief Get wall structure properties from Go
 * @param structure Wall structure pointer
 * @param total_length Output parameter for total length (mm)
 * @param max_height Output parameter for maximum height (mm)
 * @param overall_confidence Output parameter for overall confidence (0.0-1.0)
 */
CGO_EXPORT void cgo_wall_structure_get_properties(arx_wall_structure_t* structure,
                                                 double* total_length,
                                                 double* max_height,
                                                 double* overall_confidence);

/**
 * @brief Free wall structures array from Go
 * @param structures Array of wall structure pointers
 * @param count Number of structures in array
 */
CGO_EXPORT void cgo_wall_composition_free_structures(arx_wall_structure_t** structures, uint32_t count);

/**
 * @brief Free wall connections array from Go
 * @param connections Array of wall connection pointers
 * @param count Number of connections in array
 */
CGO_EXPORT void cgo_wall_composition_free_connections(arx_wall_connection_t** connections, uint32_t count);

// ============================================================================
// UTILITY BRIDGE FUNCTIONS
// ============================================================================

/**
 * @brief Free string returned from C functions
 * @param str String pointer to free
 */
CGO_EXPORT void cgo_free_string(char* str);

/**
 * @brief Free object array returned from C functions
 * @param objects Array of ArxObject pointers to free
 * @param count Number of objects in array
 */
CGO_EXPORT void cgo_free_object_array(ArxObject** objects, int count);

/**
 * @brief Get last error message from C functions
 * @return Error message string (caller must free) or NULL if no error
 */
CGO_EXPORT char* cgo_get_last_error(void);

/**
 * @brief Clear last error message
 */
CGO_EXPORT void cgo_clear_last_error(void);

#ifdef __cplusplus
}
#endif

#endif // ARXOS_CGO_BRIDGE_H
