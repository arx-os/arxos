package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	_ "github.com/lib/pq"
	_ "github.com/mattn/go-sqlite3"
	"go.uber.org/zap"
)

// DatabaseType represents supported database types
type DatabaseType string

const (
	DatabaseSQLite     DatabaseType = "sqlite"
	DatabasePostgreSQL DatabaseType = "postgresql"
	DatabaseMySQL      DatabaseType = "mysql"
)

// DatabaseConfig holds database configuration
type DatabaseConfig struct {
	Type             DatabaseType  `json:"type"`
	Host             string        `json:"host"`
	Port             int           `json:"port"`
	Database         string        `json:"database"`
	Username         string        `json:"username"`
	Password         string        `json:"password"`
	SSLMode          string        `json:"ssl_mode"`
	MaxConnections   int           `json:"max_connections"`
	MaxIdleConns     int           `json:"max_idle_conns"`
	ConnMaxLifetime  time.Duration `json:"conn_max_lifetime"`
	ConnectionString string        `json:"connection_string"`
}

// BIMModel represents a BIM model in the database
type BIMModel struct {
	ID            string                 `json:"id" db:"id"`
	Name          string                 `json:"name" db:"name"`
	Description   string                 `json:"description" db:"description"`
	ModelData     json.RawMessage        `json:"model_data" db:"model_data"`
	ModelMetadata json.RawMessage        `json:"model_metadata" db:"model_metadata"`
	CreatedBy     string                 `json:"created_by" db:"created_by"`
	ProjectID     string                 `json:"project_id" db:"project_id"`
	Version       string                 `json:"version" db:"version"`
	CreatedAt     time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at" db:"updated_at"`
	Status        string                 `json:"status" db:"status"`
	Tags          []string               `json:"tags" db:"tags"`
	Properties    map[string]interface{} `json:"properties" db:"properties"`
}

// SymbolLibrary represents a symbol library in the database
type SymbolLibrary struct {
	ID         string                 `json:"id" db:"id"`
	Name       string                 `json:"name" db:"name"`
	Category   string                 `json:"category" db:"category"`
	System     string                 `json:"system" db:"system"`
	SymbolData json.RawMessage        `json:"symbol_data" db:"symbol_data"`
	Metadata   json.RawMessage        `json:"metadata" db:"metadata"`
	CreatedBy  string                 `json:"created_by" db:"created_by"`
	CreatedAt  time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at" db:"updated_at"`
	Status     string                 `json:"status" db:"status"`
	Version    string                 `json:"version" db:"version"`
	Properties map[string]interface{} `json:"properties" db:"properties"`
}

// ValidationJob represents a validation job in the database
type ValidationJob struct {
	ID             string                 `json:"id" db:"id"`
	JobType        string                 `json:"job_type" db:"job_type"`
	Status         string                 `json:"status" db:"status"`
	Progress       int                    `json:"progress" db:"progress"`
	TotalItems     int                    `json:"total_items" db:"total_items"`
	ProcessedItems int                    `json:"processed_items" db:"processed_items"`
	Errors         []string               `json:"errors" db:"errors"`
	Warnings       []string               `json:"warnings" db:"warnings"`
	ResultData     json.RawMessage        `json:"result_data" db:"result_data"`
	CreatedBy      string                 `json:"created_by" db:"created_by"`
	CreatedAt      time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at" db:"updated_at"`
	CompletedAt    *time.Time             `json:"completed_at" db:"completed_at"`
	Properties     map[string]interface{} `json:"properties" db:"properties"`
}

// ExportJob represents an export job in the database
type ExportJob struct {
	ID             string                 `json:"id" db:"id"`
	JobType        string                 `json:"job_type" db:"job_type"`
	ExportFormat   string                 `json:"export_format" db:"export_format"`
	Status         string                 `json:"status" db:"status"`
	Progress       int                    `json:"progress" db:"progress"`
	TotalItems     int                    `json:"total_items" db:"total_items"`
	ProcessedItems int                    `json:"processed_items" db:"processed_items"`
	FilePath       string                 `json:"file_path" db:"file_path"`
	FileSize       int64                  `json:"file_size" db:"file_size"`
	Errors         []string               `json:"errors" db:"errors"`
	CreatedBy      string                 `json:"created_by" db:"created_by"`
	CreatedAt      time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at" db:"updated_at"`
	CompletedAt    *time.Time             `json:"completed_at" db:"completed_at"`
	Properties     map[string]interface{} `json:"properties" db:"properties"`
}

// User represents a user in the database
type User struct {
	ID           string                 `json:"id" db:"id"`
	Username     string                 `json:"username" db:"username"`
	Email        string                 `json:"email" db:"email"`
	PasswordHash string                 `json:"password_hash" db:"password_hash"`
	FirstName    string                 `json:"first_name" db:"first_name"`
	LastName     string                 `json:"last_name" db:"last_name"`
	Role         string                 `json:"role" db:"role"`
	Status       string                 `json:"status" db:"status"`
	CreatedAt    time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at" db:"updated_at"`
	LastLoginAt  *time.Time             `json:"last_login_at" db:"last_login_at"`
	Properties   map[string]interface{} `json:"properties" db:"properties"`
}

// DatabaseService provides comprehensive database operations
type DatabaseService struct {
	config         *DatabaseConfig
	db             *sql.DB
	logger         *zap.Logger
	mu             sync.RWMutex
	connectionPool *ConnectionPool
	transactionMgr *TransactionManager
	stateManager   *StateManager
}

// NewDatabaseService creates a new database service
func NewDatabaseService(config *DatabaseConfig, logger *zap.Logger) (*DatabaseService, error) {
	ds := &DatabaseService{
		config: config,
		logger: logger,
	}

	// Initialize connection pool
	ds.connectionPool = NewConnectionPool(config, logger)

	// Initialize transaction manager
	ds.transactionMgr = NewTransactionManager(logger)

	// Initialize state manager
	ds.stateManager = NewStateManager(logger)

	// Connect to database
	if err := ds.connect(); err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Initialize database schema
	if err := ds.initializeSchema(); err != nil {
		return nil, fmt.Errorf("failed to initialize database schema: %w", err)
	}

	logger.Info("Database service initialized",
		zap.String("type", string(config.Type)),
		zap.String("database", config.Database),
		zap.String("host", config.Host),
		zap.Int("port", config.Port),
	)

	return ds, nil
}

// connect establishes database connection
func (ds *DatabaseService) connect() error {
	var err error

	switch ds.config.Type {
	case DatabaseSQLite:
		ds.db, err = sql.Open("sqlite3", ds.config.ConnectionString)
	case DatabasePostgreSQL:
		ds.db, err = sql.Open("postgres", ds.config.ConnectionString)
	default:
		return fmt.Errorf("unsupported database type: %s", ds.config.Type)
	}

	if err != nil {
		return fmt.Errorf("failed to open database connection: %w", err)
	}

	// Configure connection pool
	ds.db.SetMaxOpenConns(ds.config.MaxConnections)
	ds.db.SetMaxIdleConns(ds.config.MaxIdleConns)
	ds.db.SetConnMaxLifetime(ds.config.ConnMaxLifetime)

	// Test connection
	if err := ds.db.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	return nil
}

// initializeSchema creates database tables if they don't exist
func (ds *DatabaseService) initializeSchema() error {
	schema := ds.getSchemaSQL()

	_, err := ds.db.Exec(schema)
	if err != nil {
		return fmt.Errorf("failed to initialize schema: %w", err)
	}

	return nil
}

// getSchemaSQL returns the SQL schema for creating tables
func (ds *DatabaseService) getSchemaSQL() string {
	switch ds.config.Type {
	case DatabaseSQLite:
		return ds.getSQLiteSchema()
	case DatabasePostgreSQL:
		return ds.getPostgreSQLSchema()
	default:
		return ds.getSQLiteSchema() // Default to SQLite
	}
}

// getSQLiteSchema returns SQLite-specific schema
func (ds *DatabaseService) getSQLiteSchema() string {
	return `
	CREATE TABLE IF NOT EXISTS bim_models (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		description TEXT,
		model_data TEXT NOT NULL,
		model_metadata TEXT,
		created_by TEXT,
		project_id TEXT,
		version TEXT DEFAULT '1.0',
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		status TEXT DEFAULT 'active',
		tags TEXT,
		properties TEXT
	);

	CREATE TABLE IF NOT EXISTS symbol_libraries (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		category TEXT,
		system TEXT,
		symbol_data TEXT NOT NULL,
		metadata TEXT,
		created_by TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		status TEXT DEFAULT 'active',
		version TEXT DEFAULT '1.0',
		properties TEXT
	);

	CREATE TABLE IF NOT EXISTS validation_jobs (
		id TEXT PRIMARY KEY,
		job_type TEXT NOT NULL,
		status TEXT DEFAULT 'pending',
		progress INTEGER DEFAULT 0,
		total_items INTEGER DEFAULT 0,
		processed_items INTEGER DEFAULT 0,
		errors TEXT,
		warnings TEXT,
		result_data TEXT,
		created_by TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		completed_at DATETIME,
		properties TEXT
	);

	CREATE TABLE IF NOT EXISTS export_jobs (
		id TEXT PRIMARY KEY,
		job_type TEXT NOT NULL,
		export_format TEXT NOT NULL,
		status TEXT DEFAULT 'pending',
		progress INTEGER DEFAULT 0,
		total_items INTEGER DEFAULT 0,
		processed_items INTEGER DEFAULT 0,
		file_path TEXT,
		file_size INTEGER DEFAULT 0,
		errors TEXT,
		created_by TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		completed_at DATETIME,
		properties TEXT
	);

	CREATE TABLE IF NOT EXISTS users (
		id TEXT PRIMARY KEY,
		username TEXT UNIQUE NOT NULL,
		email TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		first_name TEXT,
		last_name TEXT,
		role TEXT DEFAULT 'user',
		status TEXT DEFAULT 'active',
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		last_login_at DATETIME,
		properties TEXT
	);

	CREATE INDEX IF NOT EXISTS idx_bim_models_project_id ON bim_models(project_id);
	CREATE INDEX IF NOT EXISTS idx_bim_models_created_by ON bim_models(created_by);
	CREATE INDEX IF NOT EXISTS idx_bim_models_status ON bim_models(status);
	CREATE INDEX IF NOT EXISTS idx_symbol_libraries_category ON symbol_libraries(category);
	CREATE INDEX IF NOT EXISTS idx_symbol_libraries_system ON symbol_libraries(system);
	CREATE INDEX IF NOT EXISTS idx_validation_jobs_status ON validation_jobs(status);
	CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);
	CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
	CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
	`
}

// getPostgreSQLSchema returns PostgreSQL-specific schema
func (ds *DatabaseService) getPostgreSQLSchema() string {
	return `
	CREATE TABLE IF NOT EXISTS bim_models (
		id VARCHAR(255) PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		description TEXT,
		model_data JSONB NOT NULL,
		model_metadata JSONB,
		created_by VARCHAR(255),
		project_id VARCHAR(255),
		version VARCHAR(50) DEFAULT '1.0',
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		status VARCHAR(50) DEFAULT 'active',
		tags TEXT[],
		properties JSONB
	);

	CREATE TABLE IF NOT EXISTS symbol_libraries (
		id VARCHAR(255) PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		category VARCHAR(255),
		system VARCHAR(255),
		symbol_data JSONB NOT NULL,
		metadata JSONB,
		created_by VARCHAR(255),
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		status VARCHAR(50) DEFAULT 'active',
		version VARCHAR(50) DEFAULT '1.0',
		properties JSONB
	);

	CREATE TABLE IF NOT EXISTS validation_jobs (
		id VARCHAR(255) PRIMARY KEY,
		job_type VARCHAR(255) NOT NULL,
		status VARCHAR(50) DEFAULT 'pending',
		progress INTEGER DEFAULT 0,
		total_items INTEGER DEFAULT 0,
		processed_items INTEGER DEFAULT 0,
		errors TEXT[],
		warnings TEXT[],
		result_data JSONB,
		created_by VARCHAR(255),
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		completed_at TIMESTAMP,
		properties JSONB
	);

	CREATE TABLE IF NOT EXISTS export_jobs (
		id VARCHAR(255) PRIMARY KEY,
		job_type VARCHAR(255) NOT NULL,
		export_format VARCHAR(50) NOT NULL,
		status VARCHAR(50) DEFAULT 'pending',
		progress INTEGER DEFAULT 0,
		total_items INTEGER DEFAULT 0,
		processed_items INTEGER DEFAULT 0,
		file_path TEXT,
		file_size BIGINT DEFAULT 0,
		errors TEXT[],
		created_by VARCHAR(255),
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		completed_at TIMESTAMP,
		properties JSONB
	);

	CREATE TABLE IF NOT EXISTS users (
		id VARCHAR(255) PRIMARY KEY,
		username VARCHAR(255) UNIQUE NOT NULL,
		email VARCHAR(255) UNIQUE NOT NULL,
		password_hash VARCHAR(255) NOT NULL,
		first_name VARCHAR(255),
		last_name VARCHAR(255),
		role VARCHAR(50) DEFAULT 'user',
		status VARCHAR(50) DEFAULT 'active',
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		last_login_at TIMESTAMP,
		properties JSONB
	);

	CREATE INDEX IF NOT EXISTS idx_bim_models_project_id ON bim_models(project_id);
	CREATE INDEX IF NOT EXISTS idx_bim_models_created_by ON bim_models(created_by);
	CREATE INDEX IF NOT EXISTS idx_bim_models_status ON bim_models(status);
	CREATE INDEX IF NOT EXISTS idx_symbol_libraries_category ON symbol_libraries(category);
	CREATE INDEX IF NOT EXISTS idx_symbol_libraries_system ON symbol_libraries(system);
	CREATE INDEX IF NOT EXISTS idx_validation_jobs_status ON validation_jobs(status);
	CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);
	CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
	CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
	`
}

// GetDB returns the underlying database connection
func (ds *DatabaseService) GetDB() *sql.DB {
	return ds.db
}

// Close closes the database connection
func (ds *DatabaseService) Close() error {
	ds.logger.Info("Closing database service")

	if ds.db != nil {
		return ds.db.Close()
	}

	return nil
}

// HealthCheck performs a database health check
func (ds *DatabaseService) HealthCheck() error {
	if ds.db == nil {
		return fmt.Errorf("database connection is nil")
	}

	return ds.db.Ping()
}

// GetStats returns database statistics
func (ds *DatabaseService) GetStats() map[string]interface{} {
	stats := ds.db.Stats()

	return map[string]interface{}{
		"max_open_connections": stats.MaxOpenConnections,
		"open_connections":     stats.OpenConnections,
		"in_use":               stats.InUse,
		"idle":                 stats.Idle,
		"wait_count":           stats.WaitCount,
		"wait_duration":        stats.WaitDuration,
		"max_idle_closed":      stats.MaxIdleClosed,
		"max_lifetime_closed":  stats.MaxLifetimeClosed,
	}
}
