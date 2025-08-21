package database

import (
	"log"
	"os"

	"github.com/jmoiron/sqlx"
	_ "github.com/mattn/go-sqlite3"
)

// DB wraps the database connection
type DB struct {
	*sqlx.DB
}

// Connect establishes a database connection
func Connect() (*DB, error) {
	// For testing purposes, use SQLite
	dbPath := "./test_data/arxos_test.db"

	// Create database directory if it doesn't exist
	dbDir := "./test_data"
	if err := os.MkdirAll(dbDir, 0755); err != nil {
		return nil, err
	}

	// Connect to SQLite database
	db, err := sqlx.Connect("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	// Initialize database schema
	if err := initializeSchema(db); err != nil {
		return nil, err
	}

	log.Println("✅ SQLite database connected successfully")
	return &DB{db}, nil
}

// Close closes the database connection
func (db *DB) Close() error {
	return db.DB.Close()
}

// initializeSchema creates the required tables
func initializeSchema(db *sqlx.DB) error {
	// Create pdf_buildings table
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS pdf_buildings (
			id TEXT PRIMARY KEY,
			name TEXT,
			address TEXT,
			total_floors INTEGER DEFAULT 0,
			total_objects INTEGER DEFAULT 0,
			created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			metadata TEXT
		)
	`)
	if err != nil {
		return err
	}

	// Create arx_objects table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS arx_objects (
			id TEXT NOT NULL,
			building_id TEXT NOT NULL,
			object_type INTEGER NOT NULL,
			system_type INTEGER NOT NULL,
			scale_level INTEGER NOT NULL,
			x_nano INTEGER NOT NULL,
			y_nano INTEGER NOT NULL,
			z_nano INTEGER NOT NULL,
			length_nano INTEGER NOT NULL,
			width_nano INTEGER NOT NULL,
			height_nano INTEGER NOT NULL,
			type_flags INTEGER NOT NULL,
			rotation_pack INTEGER,
			metadata_id INTEGER,
			parent_id INTEGER,
			properties TEXT,
			created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			PRIMARY KEY (id, building_id),
			FOREIGN KEY (building_id) REFERENCES pdf_buildings(id) ON DELETE CASCADE
		)
	`)
	if err != nil {
		return err
	}

	// Create indexes
	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_arx_objects_building ON arx_objects(building_id)")
	if err != nil {
		return err
	}

	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_arx_objects_type ON arx_objects(object_type)")
	if err != nil {
		return err
	}

	return nil
}
