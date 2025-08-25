package cgo

import (
	"errors"
	"fmt"
	"time"
)

// ============================================================================
// DATABASE TYPES AND ENUMS
// ============================================================================

// ArxDatabaseType represents the type of database
type ArxDatabaseType int

const (
	ArxDatabasePostgreSQL ArxDatabaseType = iota
	ArxDatabaseSQLite
	ArxDatabaseMySQL
)

// ArxDatabaseLogLevel represents the logging level for database operations
type ArxDatabaseLogLevel int

const (
	ArxDatabaseLogLevelError ArxDatabaseLogLevel = iota
	ArxDatabaseLogLevelWarn
	ArxDatabaseLogLevelInfo
	ArxDatabaseLogLevelDebug
)

// ArxDatabaseResult represents the result of a database operation
type ArxDatabaseResult int

const (
	ArxDatabaseOpSuccess ArxDatabaseResult = iota
	ArxDatabaseOpError
	ArxDatabaseOpNotFound
	ArxDatabaseOpDuplicate
	ArxDatabaseOpInvalid
	ArxDatabaseOpTimeout
)

// ============================================================================
// DATABASE CONFIGURATION STRUCTURES
// ============================================================================

// ArxDatabaseConfig holds database configuration parameters
type ArxDatabaseConfig struct {
	Type                   ArxDatabaseType
	Host                   string
	Port                   int
	Database               string
	Username               string
	Password               string
	SSLMode                string
	MaxConnections         int
	MaxIdleConnections     int
	ConnectionLifetimeSecs int
	IdleTimeoutSecs        int
	EnablePreparedStmts    bool
	LogLevel               ArxDatabaseLogLevel
	EnableMetrics          bool
	ConnectionString       string
}

// ArxConnectionPoolStats holds connection pool statistics
type ArxConnectionPoolStats struct {
	MaxOpenConnections int
	OpenConnections    int
	InUseConnections   int
	IdleConnections    int
	WaitCount          int64
	WaitDurationMs     float64
	MaxIdleClosed      int64
	MaxLifetimeClosed  int64
	LastStatsUpdate    time.Time
}

// ArxQuery represents a database query with parameters
type ArxQuery struct {
	Query                string
	Params               []string
	ParamCount           int
	UsePreparedStatement bool
	TimeoutSeconds       int
	EnableCache          bool
	CacheKey             string
}

// ArxQueryParameter represents a single query parameter
type ArxQueryParameter struct {
	Name  string
	Value string
}

// ArxQueryParameters holds a collection of query parameters
type ArxQueryParameters struct {
	Parameters []ArxQueryParameter
	Count      int
	Capacity   int
}

// ============================================================================
// TRANSACTION STRUCTURES
// ============================================================================

// ArxTransaction represents a database transaction
type ArxTransaction struct {
	TransactionID  uint64
	StartTime      time.Time
	IsActive       bool
	StatementCount int
	Description    string
}

// ============================================================================
// QUERY RESULT STRUCTURES
// ============================================================================

// ArxQueryResult represents the result of a database query
type ArxQueryResult struct {
	ColumnNames  []string
	Rows         [][]string
	RowCount     int
	ColumnCount  int
	AffectedRows int64
	LastInsertID uint64
	ErrorMessage string
}

// ArxResultField represents a single field in a query result
type ArxResultField struct {
	FieldName  string
	FieldValue string
	FieldType  string
}

// ArxResultRow represents a single row in a query result
type ArxResultRow struct {
	Fields     []ArxResultField
	FieldCount int
	Capacity   int
}

// ============================================================================
// PERFORMANCE METRICS STRUCTURES
// ============================================================================

// ArxDatabaseMetrics holds database performance metrics
type ArxDatabaseMetrics struct {
	TotalQueries       uint64
	SuccessfulQueries  uint64
	FailedQueries      uint64
	AvgQueryTimeMs     float64
	SlowestQueryTimeMs float64
	FastestQueryTimeMs float64
	CacheHits          uint64
	CacheMisses        uint64
	ConnectionErrors   uint64
	TransactionCount   uint64
	RollbackCount      uint64
	LastMetricsReset   time.Time
}

// ============================================================================
// CONVERSION FUNCTIONS
// ============================================================================

// Note: CGO conversion functions will be implemented in the main arxos.go file
// to avoid complex C struct handling in this types file

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// DefaultDatabaseConfig returns a default database configuration
func DefaultDatabaseConfig() *ArxDatabaseConfig {
	return &ArxDatabaseConfig{
		Type:                   ArxDatabasePostgreSQL,
		Host:                   "localhost",
		Port:                   5432,
		Database:               "arxos",
		Username:               "postgres",
		Password:               "",
		SSLMode:                "disable",
		MaxConnections:         100,
		MaxIdleConnections:     25,
		ConnectionLifetimeSecs: 3600, // 1 hour
		IdleTimeoutSecs:        1800, // 30 minutes
		EnablePreparedStmts:    true,
		LogLevel:               ArxDatabaseLogLevelInfo,
		EnableMetrics:          true,
		ConnectionString:       "",
	}
}

// ValidateDatabaseConfig validates database configuration parameters
func ValidateDatabaseConfig(config *ArxDatabaseConfig) error {
	if config == nil {
		return errors.New("database configuration cannot be nil")
	}

	if config.Host == "" {
		return errors.New("database host cannot be empty")
	}

	if config.Port <= 0 || config.Port > 65535 {
		return errors.New("invalid database port")
	}

	if config.Database == "" {
		return errors.New("database name cannot be empty")
	}

	if config.MaxConnections <= 0 {
		return errors.New("max connections must be positive")
	}

	if config.MaxIdleConnections <= 0 {
		return errors.New("max idle connections must be positive")
	}

	if config.MaxIdleConnections > config.MaxConnections {
		return errors.New("max idle connections cannot exceed max connections")
	}

	if config.ConnectionLifetimeSecs <= 0 {
		return errors.New("connection lifetime must be positive")
	}

	if config.IdleTimeoutSecs <= 0 {
		return errors.New("idle timeout must be positive")
	}

	return nil
}

// BuildConnectionString builds a connection string from configuration
func (config *ArxDatabaseConfig) BuildConnectionString() string {
	if config.ConnectionString != "" {
		return config.ConnectionString
	}

	switch config.Type {
	case ArxDatabasePostgreSQL:
		return fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
			config.Host, config.Port, config.Username, config.Password, config.Database, config.SSLMode)
	case ArxDatabaseSQLite:
		return config.Database
	case ArxDatabaseMySQL:
		return fmt.Sprintf("%s:%s@tcp(%s:%d)/%s",
			config.Username, config.Password, config.Host, config.Port, config.Database)
	default:
		return ""
	}
}
