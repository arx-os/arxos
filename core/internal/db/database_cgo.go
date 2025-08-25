package db

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/arxos/arxos/core/cgo"
)

// DatabaseManagerCGO provides CGO-optimized database operations
type DatabaseManagerCGO struct {
	hasCGO             bool
	config             *cgo.ArxDatabaseConfig
	poolStats          *cgo.ArxConnectionPoolStats
	metrics            *cgo.ArxDatabaseMetrics
	activeTransactions map[uint64]*cgo.ArxTransaction
	txMutex            sync.RWMutex
}

// NewDatabaseManagerCGO creates a new CGO-optimized database manager
func NewDatabaseManagerCGO() *DatabaseManagerCGO {
	dm := &DatabaseManagerCGO{
		hasCGO:             false,
		activeTransactions: make(map[uint64]*cgo.ArxTransaction),
	}

	// Initialize CGO database system
	if dm.initializeCGO() {
		dm.hasCGO = true
		log.Println("✅ CGO Database Manager initialized successfully")
	} else {
		log.Println("⚠️  CGO Database Manager using fallback implementation")
	}

	return dm
}

// initializeCGO initializes the CGO database system
func (dm *DatabaseManagerCGO) initializeCGO() bool {
	// Load configuration from environment
	config := dm.loadConfigFromEnv()
	dm.config = config

	// Initialize the CGO database system
	if !cgo.InitDatabase(config) {
		log.Printf("Failed to initialize CGO database: %s", cgo.GetDatabaseLastError())
		return false
	}

	// Test the connection to ensure everything is working
	if !cgo.TestDatabaseConnection() {
		log.Printf("CGO database connection test failed: %s", cgo.GetDatabaseLastError())
		return false
	}

	log.Println("CGO database system initialized successfully")
	return true
}

// loadConfigFromEnv loads database configuration from environment variables
func (dm *DatabaseManagerCGO) loadConfigFromEnv() *cgo.ArxDatabaseConfig {
	config := cgo.DefaultDatabaseConfig()

	// Override with environment variables
	if host := os.Getenv("DB_HOST"); host != "" {
		config.Host = host
	}

	if portStr := os.Getenv("DB_PORT"); portStr != "" {
		if port, err := strconv.Atoi(portStr); err == nil {
			config.Port = port
		}
	}

	if database := os.Getenv("DB_NAME"); database != "" {
		config.Database = database
	}

	if username := os.Getenv("DB_USER"); username != "" {
		config.Username = username
	}

	if password := os.Getenv("DB_PASSWORD"); password != "" {
		config.Password = password
	}

	if sslMode := os.Getenv("DB_SSL_MODE"); sslMode != "" {
		config.SSLMode = sslMode
	}

	if maxOpenStr := os.Getenv("DB_MAX_OPEN_CONNS"); maxOpenStr != "" {
		if maxOpen, err := strconv.Atoi(maxOpenStr); err == nil {
			config.MaxConnections = maxOpen
		}
	}

	if maxIdleStr := os.Getenv("DB_MAX_IDLE_CONNS"); maxIdleStr != "" {
		if maxIdle, err := strconv.Atoi(maxIdleStr); err == nil {
			config.MaxIdleConnections = maxIdle
		}
	}

	if lifetimeStr := os.Getenv("DB_CONN_MAX_LIFETIME"); lifetimeStr != "" {
		if lifetime, err := time.ParseDuration(lifetimeStr); err == nil {
			config.ConnectionLifetimeSecs = int(lifetime.Seconds())
		}
	}

	if idleTimeoutStr := os.Getenv("DB_CONN_MAX_IDLE_TIME"); idleTimeoutStr != "" {
		if idleTimeout, err := time.ParseDuration(idleTimeoutStr); err == nil {
			config.IdleTimeoutSecs = int(idleTimeout.Seconds())
		}
	}

	// Build connection string
	config.ConnectionString = config.BuildConnectionString()

	return config
}

// HasCGOBridge returns true if CGO is available and initialized
func (dm *DatabaseManagerCGO) HasCGOBridge() bool {
	return dm.hasCGO
}

// Close cleans up the database manager
func (dm *DatabaseManagerCGO) Close() error {
	if dm.hasCGO {
		cgo.CleanupDatabase()
	}
	return nil
}

// ============================================================================
// CONNECTION MANAGEMENT
// ============================================================================

// IsConnected returns true if the database is connected
func (dm *DatabaseManagerCGO) IsConnected() bool {
	if dm.hasCGO {
		return cgo.IsDatabaseConnected()
	}
	return false
}

// TestConnection tests database connectivity
func (dm *DatabaseManagerCGO) TestConnection() error {
	if dm.hasCGO {
		if !cgo.TestDatabaseConnection() {
			return fmt.Errorf("connection test failed: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// ============================================================================
// CONNECTION POOL MANAGEMENT
// ============================================================================

// GetPoolStats returns connection pool statistics
func (dm *DatabaseManagerCGO) GetPoolStats() *cgo.ArxConnectionPoolStats {
	if dm.hasCGO {
		return cgo.GetDatabasePoolStats()
	}
	return nil
}

// ConfigurePool configures the connection pool
func (dm *DatabaseManagerCGO) ConfigurePool(maxOpen, maxIdle int, lifetime, idleTimeout time.Duration) error {
	if dm.hasCGO {
		if !cgo.ConfigureDatabasePool(maxOpen, maxIdle, int(lifetime.Seconds()), int(idleTimeout.Seconds())) {
			return fmt.Errorf("failed to configure pool: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// ============================================================================
// TRANSACTION MANAGEMENT
// ============================================================================

// BeginTransaction begins a new transaction
func (dm *DatabaseManagerCGO) BeginTransaction(ctx context.Context, description string) (uint64, error) {
	if dm.hasCGO {
		txID := cgo.BeginTransaction(description)
		if txID == 0 {
			return 0, fmt.Errorf("failed to begin transaction: %s", cgo.GetDatabaseLastError())
		}

		// Store transaction info
		dm.txMutex.Lock()
		dm.activeTransactions[txID] = &cgo.ArxTransaction{
			TransactionID:  txID,
			StartTime:      time.Now(),
			IsActive:       true,
			StatementCount: 0,
			Description:    description,
		}
		dm.txMutex.Unlock()

		return txID, nil
	}
	return 0, fmt.Errorf("CGO bridge not available")
}

// CommitTransaction commits a transaction
func (dm *DatabaseManagerCGO) CommitTransaction(ctx context.Context, txID uint64) error {
	if dm.hasCGO {
		if !cgo.CommitTransaction(txID) {
			return fmt.Errorf("failed to commit transaction: %s", cgo.GetDatabaseLastError())
		}

		// Remove from active transactions
		dm.txMutex.Lock()
		delete(dm.activeTransactions, txID)
		dm.txMutex.Unlock()

		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// RollbackTransaction rollbacks a transaction
func (dm *DatabaseManagerCGO) RollbackTransaction(ctx context.Context, txID uint64) error {
	if dm.hasCGO {
		if !cgo.RollbackTransaction(txID) {
			return fmt.Errorf("failed to rollback transaction: %s", cgo.GetDatabaseLastError())
		}

		// Remove from active transactions
		dm.txMutex.Lock()
		delete(dm.activeTransactions, txID)
		dm.txMutex.Unlock()

		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// GetTransaction returns transaction information
func (dm *DatabaseManagerCGO) GetTransaction(txID uint64) *cgo.ArxTransaction {
	if dm.hasCGO {
		return cgo.GetTransaction(txID)
	}
	return nil
}

// ============================================================================
// QUERY EXECUTION
// ============================================================================

// ExecuteQuery executes a query with parameters
func (dm *DatabaseManagerCGO) ExecuteQuery(ctx context.Context, query string, params []string) (*cgo.ArxQueryResult, error) {
	if dm.hasCGO {
		result := cgo.ExecuteQuery(query, params)
		if result == nil {
			return nil, fmt.Errorf("failed to execute query: %s", cgo.GetDatabaseLastError())
		}
		return result, nil
	}
	return nil, fmt.Errorf("CGO bridge not available")
}

// ExecuteSimpleQuery executes a query without parameters
func (dm *DatabaseManagerCGO) ExecuteSimpleQuery(ctx context.Context, query string) (*cgo.ArxQueryResult, error) {
	if dm.hasCGO {
		result := cgo.ExecuteSimpleQuery(query)
		if result == nil {
			return nil, fmt.Errorf("failed to execute simple query: %s", cgo.GetDatabaseLastError())
		}
		return result, nil
	}
	return nil, fmt.Errorf("CGO bridge not available")
}

// ExecutePrepared executes a prepared statement
func (dm *DatabaseManagerCGO) ExecutePrepared(ctx context.Context, statementName string, params []string) (*cgo.ArxQueryResult, error) {
	if dm.hasCGO {
		result := cgo.ExecutePrepared(statementName, params)
		if result == nil {
			return nil, fmt.Errorf("failed to execute prepared statement: %s", cgo.GetDatabaseLastError())
		}
		return result, nil
	}
	return nil, fmt.Errorf("CGO bridge not available")
}

// PrepareStatement prepares a statement for later execution
func (dm *DatabaseManagerCGO) PrepareStatement(ctx context.Context, statementName, query string) error {
	if dm.hasCGO {
		if !cgo.PrepareStatement(statementName, query) {
			return fmt.Errorf("failed to prepare statement: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// ============================================================================
// RESULT PROCESSING
// ============================================================================

// GetFieldValue gets a field value by column name
func (dm *DatabaseManagerCGO) GetFieldValue(result *cgo.ArxQueryResult, rowIndex int, columnName string) string {
	if dm.hasCGO {
		return cgo.GetFieldValue(result, rowIndex, columnName)
	}
	return ""
}

// GetFieldValueByIndex gets a field value by column index
func (dm *DatabaseManagerCGO) GetFieldValueByIndex(result *cgo.ArxQueryResult, rowIndex, columnIndex int) string {
	if dm.hasCGO {
		return cgo.GetFieldValueByIndex(result, rowIndex, columnIndex)
	}
	return ""
}

// FreeQueryResult frees a query result
func (dm *DatabaseManagerCGO) FreeQueryResult(result *cgo.ArxQueryResult) {
	if dm.hasCGO {
		cgo.FreeQueryResult(result)
	}
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// EscapeString escapes a string for safe SQL usage
func (dm *DatabaseManagerCGO) EscapeString(input string) string {
	if dm.hasCGO {
		return cgo.EscapeString(input)
	}
	return input
}

// GetLastError returns the last database error
func (dm *DatabaseManagerCGO) GetLastError() string {
	if dm.hasCGO {
		return cgo.GetDatabaseLastError()
	}
	return "CGO bridge not available"
}

// ClearLastError clears the last database error
func (dm *DatabaseManagerCGO) ClearLastError() {
	if dm.hasCGO {
		cgo.ClearDatabaseLastError()
	}
}

// ============================================================================
// PERFORMANCE METRICS
// ============================================================================

// GetMetrics returns database performance metrics
func (dm *DatabaseManagerCGO) GetMetrics() *cgo.ArxDatabaseMetrics {
	if dm.hasCGO {
		return cgo.GetDatabaseMetrics()
	}
	return nil
}

// ResetMetrics resets database performance metrics
func (dm *DatabaseManagerCGO) ResetMetrics() {
	if dm.hasCGO {
		cgo.ResetDatabaseMetrics()
	}
}

// IsHealthy checks if the database is healthy
func (dm *DatabaseManagerCGO) IsHealthy() bool {
	if dm.hasCGO {
		return cgo.IsDatabaseHealthy()
	}
	return false
}

// ============================================================================
// SCHEMA MANAGEMENT
// ============================================================================

// CreateTable creates a database table
func (dm *DatabaseManagerCGO) CreateTable(ctx context.Context, tableName, schema string) error {
	if dm.hasCGO {
		if !cgo.CreateTable(tableName, schema) {
			return fmt.Errorf("failed to create table: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// DropTable drops a database table
func (dm *DatabaseManagerCGO) DropTable(ctx context.Context, tableName string) error {
	if dm.hasCGO {
		if !cgo.DropTable(tableName) {
			return fmt.Errorf("failed to drop table: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// TableExists checks if a table exists
func (dm *DatabaseManagerCGO) TableExists(ctx context.Context, tableName string) bool {
	if dm.hasCGO {
		return cgo.TableExists(tableName)
	}
	return false
}

// GetTableSchema gets a table's schema
func (dm *DatabaseManagerCGO) GetTableSchema(ctx context.Context, tableName string) (string, error) {
	if dm.hasCGO {
		schema := cgo.GetTableSchema(tableName)
		if schema == "" {
			return "", fmt.Errorf("failed to get table schema: %s", cgo.GetDatabaseLastError())
		}
		return schema, nil
	}
	return "", fmt.Errorf("CGO bridge not available")
}

// ============================================================================
// INDEX MANAGEMENT
// ============================================================================

// CreateIndex creates a database index
func (dm *DatabaseManagerCGO) CreateIndex(ctx context.Context, tableName, indexName, columns, indexType string) error {
	if dm.hasCGO {
		if !cgo.CreateIndex(tableName, indexName, columns, indexType) {
			return fmt.Errorf("failed to create index: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// DropIndex drops a database index
func (dm *DatabaseManagerCGO) DropIndex(ctx context.Context, tableName, indexName string) error {
	if dm.hasCGO {
		if !cgo.DropIndex(tableName, indexName) {
			return fmt.Errorf("failed to drop index: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// ============================================================================
// BACKUP AND RECOVERY
// ============================================================================

// CreateBackup creates a database backup
func (dm *DatabaseManagerCGO) CreateBackup(ctx context.Context, backupPath string) error {
	if dm.hasCGO {
		if !cgo.CreateBackup(backupPath) {
			return fmt.Errorf("failed to create backup: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// RestoreBackup restores a database from backup
func (dm *DatabaseManagerCGO) RestoreBackup(ctx context.Context, backupPath string) error {
	if dm.hasCGO {
		if !cgo.RestoreBackup(backupPath) {
			return fmt.Errorf("failed to restore backup: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// VerifyBackup verifies backup integrity
func (dm *DatabaseManagerCGO) VerifyBackup(ctx context.Context, backupPath string) error {
	if dm.hasCGO {
		if !cgo.VerifyBackup(backupPath) {
			return fmt.Errorf("failed to verify backup: %s", cgo.GetDatabaseLastError())
		}
		return nil
	}
	return fmt.Errorf("CGO bridge not available")
}

// ============================================================================
// COMPATIBILITY LAYER
// ============================================================================

// GetGormDB returns a GORM database instance for compatibility
// This allows existing code to work with the CGO manager
func (dm *DatabaseManagerCGO) GetGormDB() *sql.DB {
	// For now, return nil as we're focusing on CGO operations
	// In a full implementation, this could return a GORM wrapper around CGO
	return nil
}

// GetCGOStatus returns the current CGO status and configuration
func (dm *DatabaseManagerCGO) GetCGOStatus() map[string]interface{} {
	status := map[string]interface{}{
		"has_cgo": dm.hasCGO,
		"healthy": dm.IsHealthy(),
	}

	if dm.hasCGO {
		status["config"] = dm.config
		status["pool_stats"] = dm.GetPoolStats()
		status["metrics"] = dm.GetMetrics()
		status["active_transactions"] = len(dm.activeTransactions)
	}

	return status
}
