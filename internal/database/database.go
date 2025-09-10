package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/joelpate/arxos/pkg/models"
)

// DB represents the database interface for ArxOS
type DB interface {
	// Core operations
	Connect(ctx context.Context, dbPath string) error
	Close() error
	
	// Transaction support
	BeginTx(ctx context.Context) (*sql.Tx, error)
	
	// Floor plan operations
	GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error)
	GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error)
	SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error
	UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error
	DeleteFloorPlan(ctx context.Context, id string) error
	
	// Equipment operations
	GetEquipment(ctx context.Context, id string) (*models.Equipment, error)
	GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error)
	SaveEquipment(ctx context.Context, equipment *models.Equipment) error
	UpdateEquipment(ctx context.Context, equipment *models.Equipment) error
	DeleteEquipment(ctx context.Context, id string) error
	
	// Room operations
	GetRoom(ctx context.Context, id string) (*models.Room, error)
	GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error)
	SaveRoom(ctx context.Context, room *models.Room) error
	UpdateRoom(ctx context.Context, room *models.Room) error
	DeleteRoom(ctx context.Context, id string) error
	
	// Query operations
	Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error)
	QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row
	Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error)
	
	// Migration operations
	Migrate(ctx context.Context) error
	GetVersion(ctx context.Context) (int, error)
}

// Config holds database configuration
type Config struct {
	DatabasePath string
	MaxOpenConns int
	MaxIdleConns int
	MaxLifetime  time.Duration
}

// NewConfig creates a new database configuration with defaults
func NewConfig(dbPath string) *Config {
	return &Config{
		DatabasePath: dbPath,
		MaxOpenConns: 25,
		MaxIdleConns: 5,
		MaxLifetime:  5 * time.Minute,
	}
}

// QueryResult represents the result of a custom query
type QueryResult struct {
	Columns []string
	Rows    [][]interface{}
}

// Change represents a change in the database for audit purposes
type Change struct {
	ID          string
	ObjectID    string
	ObjectType  string
	Operation   string // create, update, delete
	OldValue    string // JSON
	NewValue    string // JSON
	Timestamp   time.Time
	User        string
	Branch      string
	CommitHash  string
}

// Conflict represents a merge conflict between data sources
type Conflict struct {
	ID         string
	ObjectID   string
	ObjectType string
	Source     string
	OurValue   string // JSON
	TheirValue string // JSON
	Resolved   bool
	Resolution string // JSON of resolved value
	Timestamp  time.Time
}

// Error types
var (
	ErrNotFound      = fmt.Errorf("record not found")
	ErrAlreadyExists = fmt.Errorf("record already exists")
	ErrInvalidQuery  = fmt.Errorf("invalid query")
	ErrTransaction   = fmt.Errorf("transaction error")
)