package database

import (
	"context"
	"database/sql"
)

// Interface defines the database interface following Clean Architecture principles
type Interface interface {
	// Connection management
	Connect() error
	Close() error
	Ping() error

	// Transaction management
	BeginTx(ctx context.Context) (*sql.Tx, error)
	CommitTx(tx *sql.Tx) error
	RollbackTx(tx *sql.Tx) error

	// Query execution
	Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error)
	QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row
	Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error)

	// Spatial operations
	ExecuteSpatialQuery(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error)
	GetSpatialData(ctx context.Context, table string, id string) (interface{}, error)

	// Migration
	Migrate(ctx context.Context) error

	// Health check
	IsHealthy() bool
	GetStats() map[string]interface{}
}
