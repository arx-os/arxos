#ifndef ARX_DATABASE_H
#define ARX_DATABASE_H

#include <stdbool.h>
#include <stdint.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// DATABASE CONFIGURATION AND TYPES
// ============================================================================

typedef enum {
    ARX_DB_POSTGRESQL = 0,
    ARX_DB_SQLITE = 1,
    ARX_DB_MYSQL = 2
} ArxDatabaseType;

typedef enum {
    ARX_DB_LOG_LEVEL_ERROR = 0,
    ARX_DB_LOG_LEVEL_WARN = 1,
    ARX_DB_LOG_LEVEL_INFO = 2,
    ARX_DB_LOG_LEVEL_DEBUG = 3
} ArxDatabaseLogLevel;

typedef enum {
    ARX_DB_OP_SUCCESS = 0,
    ARX_DB_OP_ERROR = 1,
    ARX_DB_OP_NOT_FOUND = 2,
    ARX_DB_OP_DUPLICATE = 3,
    ARX_DB_OP_INVALID = 4,
    ARX_DB_OP_TIMEOUT = 5
} ArxDatabaseResult;

// ============================================================================
// CONNECTION CONFIGURATION
// ============================================================================

typedef struct {
    ArxDatabaseType type;
    char* host;
    int port;
    char* database;
    char* username;
    char* password;
    char* ssl_mode;
    int max_connections;
    int max_idle_connections;
    int connection_lifetime_seconds;
    int idle_timeout_seconds;
    bool enable_prepared_statements;
    ArxDatabaseLogLevel log_level;
    bool enable_metrics;
    char* connection_string;
} ArxDatabaseConfig;

// ============================================================================
// CONNECTION POOL STATISTICS
// ============================================================================

typedef struct {
    int max_open_connections;
    int open_connections;
    int in_use_connections;
    int idle_connections;
    int64_t wait_count;
    double wait_duration_ms;
    int64_t max_idle_closed;
    int64_t max_lifetime_closed;
    time_t last_stats_update;
} ArxConnectionPoolStats;

// ============================================================================
// QUERY OPTIMIZATION
// ============================================================================

typedef struct {
    char* query;
    char** params;
    int param_count;
    bool use_prepared_statement;
    int timeout_seconds;
    bool enable_cache;
    char* cache_key;
} ArxQuery;

typedef struct {
    char* name;
    char* value;
} ArxQueryParameter;

typedef struct {
    ArxQueryParameter* parameters;
    int count;
    int capacity;
} ArxQueryParameters;

// ============================================================================
// TRANSACTION MANAGEMENT
// ============================================================================

typedef struct {
    uint64_t transaction_id;
    time_t start_time;
    bool is_active;
    int statement_count;
    char* description;
} ArxTransaction;

// ============================================================================
// QUERY RESULTS
// ============================================================================

typedef struct {
    char** column_names;
    char*** rows;
    int row_count;
    int column_count;
    int64_t affected_rows;
    uint64_t last_insert_id;
    char* error_message;
} ArxQueryResult;

typedef struct {
    char* field_name;
    char* field_value;
    char* field_type;
} ArxResultField;

typedef struct {
    ArxResultField* fields;
    int field_count;
    int capacity;
} ArxResultRow;

// ============================================================================
// PERFORMANCE METRICS
// ============================================================================

typedef struct {
    uint64_t total_queries;
    uint64_t successful_queries;
    uint64_t failed_queries;
    double avg_query_time_ms;
    double slowest_query_time_ms;
    double fastest_query_time_ms;
    uint64_t cache_hits;
    uint64_t cache_misses;
    uint64_t connection_errors;
    uint64_t transaction_count;
    uint64_t rollback_count;
    time_t last_metrics_reset;
} ArxDatabaseMetrics;

// ============================================================================
// CORE DATABASE FUNCTIONS
// ============================================================================

/**
 * @brief Initialize the database system
 * @param config Database configuration
 * @return true on success, false on failure
 */
bool arx_database_init(const ArxDatabaseConfig* config);

/**
 * @brief Cleanup and shutdown the database system
 */
void arx_database_cleanup(void);

/**
 * @brief Get database connection status
 * @return true if connected, false otherwise
 */
bool arx_database_is_connected(void);

/**
 * @brief Test database connectivity
 * @return true if connection test passes, false otherwise
 */
bool arx_database_test_connection(void);

// ============================================================================
// CONNECTION POOL MANAGEMENT
// ============================================================================

/**
 * @brief Get connection pool statistics
 * @return Pointer to connection pool stats (caller must not free)
 */
const ArxConnectionPoolStats* arx_database_get_pool_stats(void);

/**
 * @brief Reset connection pool statistics
 */
void arx_database_reset_pool_stats(void);

/**
 * @brief Configure connection pool settings
 * @param max_open Maximum open connections
 * @param max_idle Maximum idle connections
 * @param lifetime Connection lifetime in seconds
 * @param idle_timeout Idle timeout in seconds
 * @return true on success, false on failure
 */
bool arx_database_configure_pool(int max_open, int max_idle, int lifetime, int idle_timeout);

// ============================================================================
// TRANSACTION MANAGEMENT
// ============================================================================

/**
 * @brief Begin a new transaction
 * @param description Transaction description
 * @return Transaction ID on success, 0 on failure
 */
uint64_t arx_database_begin_transaction(const char* description);

/**
 * @brief Commit a transaction
 * @param transaction_id Transaction ID
 * @return true on success, false on failure
 */
bool arx_database_commit_transaction(uint64_t transaction_id);

/**
 * @brief Rollback a transaction
 * @param transaction_id Transaction ID
 * @return true on success, false on failure
 */
bool arx_database_rollback_transaction(uint64_t transaction_id);

/**
 * @brief Get transaction status
 * @param transaction_id Transaction ID
 * @return Pointer to transaction info (caller must not free)
 */
const ArxTransaction* arx_database_get_transaction(uint64_t transaction_id);

// ============================================================================
// QUERY EXECUTION
// ============================================================================

/**
 * @brief Execute a query with parameters
 * @param query SQL query string
 * @param params Query parameters
 * @param param_count Number of parameters
 * @return Query result (caller must free with arx_database_free_result)
 */
ArxQueryResult* arx_database_execute_query(const char* query, const char** params, int param_count);

/**
 * @brief Execute a query without parameters
 * @param query SQL query string
 * @return Query result (caller must free with arx_database_free_result)
 */
ArxQueryResult* arx_database_execute_simple_query(const char* query);

/**
 * @brief Execute a prepared statement
 * @param statement_name Name of prepared statement
 * @param params Query parameters
 * @param param_count Number of parameters
 * @return Query result (caller must free with arx_database_free_result)
 */
ArxQueryResult* arx_database_execute_prepared(const char* statement_name, const char** params, int param_count);

/**
 * @brief Prepare a statement for later execution
 * @param statement_name Name for the prepared statement
 * @param query SQL query string
 * @return true on success, false on failure
 */
bool arx_database_prepare_statement(const char* statement_name, const char* query);

// ============================================================================
// RESULT MANAGEMENT
// ============================================================================

/**
 * @brief Free a query result
 * @param result Query result to free
 */
void arx_database_free_result(ArxQueryResult* result);

/**
 * @brief Get field value from result row
 * @param result Query result
 * @param row_index Row index (0-based)
 * @param column_name Column name
 * @return Field value or NULL if not found
 */
const char* arx_database_get_field_value(const ArxQueryResult* result, int row_index, const char* column_name);

/**
 * @brief Get field value by column index
 * @param result Query result
 * @param row_index Row index (0-based)
 * @param column_index Column index (0-based)
 * @return Field value or NULL if invalid indices
 */
const char* arx_database_get_field_value_by_index(const ArxQueryResult* result, int row_index, int column_index);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Escape a string for safe SQL usage
 * @param input Input string to escape
 * @return Escaped string (caller must free)
 */
char* arx_database_escape_string(const char* input);

/**
 * @brief Get the last error message
 * @return Last error message (caller must not free)
 */
const char* arx_database_get_last_error(void);

/**
 * @brief Clear the last error message
 */
void arx_database_clear_last_error(void);

/**
 * @brief Get database metrics
 * @return Pointer to database metrics (caller must not free)
 */
const ArxDatabaseMetrics* arx_database_get_metrics(void);

/**
 * @brief Reset database metrics
 */
void arx_database_reset_metrics(void);

/**
 * @brief Check if database is healthy
 * @return true if healthy, false otherwise
 */
bool arx_database_is_healthy(void);

// ============================================================================
// SCHEMA MANAGEMENT
// ============================================================================

/**
 * @brief Create a table
 * @param table_name Name of table to create
 * @param schema SQL schema definition
 * @return true on success, false on failure
 */
bool arx_database_create_table(const char* table_name, const char* schema);

/**
 * @brief Drop a table
 * @param table_name Name of table to drop
 * @return true on success, false on failure
 */
bool arx_database_drop_table(const char* table_name);

/**
 * @brief Check if table exists
 * @param table_name Name of table to check
 * @return true if exists, false otherwise
 */
bool arx_database_table_exists(const char* table_name);

/**
 * @brief Get table schema
 * @param table_name Name of table
 * @return Table schema (caller must free)
 */
char* arx_database_get_table_schema(const char* table_name);

// ============================================================================
// INDEX MANAGEMENT
// ============================================================================

/**
 * @brief Create an index
 * @param table_name Name of table
 * @param index_name Name of index
 * @param columns Comma-separated column names
 * @param index_type Type of index (e.g., "btree", "hash")
 * @return true on success, false on failure
 */
bool arx_database_create_index(const char* table_name, const char* index_name, const char* columns, const char* index_type);

/**
 * @brief Drop an index
 * @param table_name Name of table
 * @param index_name Name of index
 * @return true on success, false on failure
 */
bool arx_database_drop_index(const char* table_name, const char* index_name);

// ============================================================================
// BACKUP AND RECOVERY
// ============================================================================

/**
 * @brief Create database backup
 * @param backup_path Path for backup file
 * @return true on success, false on failure
 */
bool arx_database_create_backup(const char* backup_path);

/**
 * @brief Restore database from backup
 * @param backup_path Path to backup file
 * @return true on success, false on failure
 */
bool arx_database_restore_backup(const char* backup_path);

/**
 * @brief Verify backup integrity
 * @param backup_path Path to backup file
 * @return true if backup is valid, false otherwise
 */
bool arx_database_verify_backup(const char* backup_path);

#ifdef __cplusplus
}
#endif

#endif // ARX_DATABASE_H

