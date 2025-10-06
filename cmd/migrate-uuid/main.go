package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	_ "github.com/lib/pq"
)

func main() {
	// Get database connection string from environment
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://arxos:arxos@localhost:5432/arxos?sslmode=disable"
	}

	// Connect to database
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Test connection
	if err := db.Ping(); err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}

	fmt.Println("Connected to database successfully")

	// Create ID mappings table
	fmt.Println("Creating ID mappings table...")
	if err := createIDMappingsTable(db); err != nil {
		log.Fatalf("Failed to create ID mappings table: %v", err)
	}

	// Add UUID columns to existing tables
	fmt.Println("Adding UUID columns to existing tables...")
	if err := addUUIDColumns(db); err != nil {
		log.Fatalf("Failed to add UUID columns: %v", err)
	}

	// Generate UUIDs for existing records
	fmt.Println("Generating UUIDs for existing records...")
	if err := generateUUIDsForExistingRecords(db); err != nil {
		log.Fatalf("Failed to generate UUIDs: %v", err)
	}

	// Create ID mappings
	fmt.Println("Creating ID mappings...")
	if err := createIDMappings(db); err != nil {
		log.Fatalf("Failed to create ID mappings: %v", err)
	}

	fmt.Println("Migration completed successfully!")
}

// ConsoleLogger implements domain.Logger for console output
type ConsoleLogger struct{}

func (l *ConsoleLogger) Info(msg string, fields ...any) {
	fmt.Printf("[INFO] %s", msg)
	if len(fields) > 0 {
		fmt.Printf(" %v", fields)
	}
	fmt.Println()
}

func (l *ConsoleLogger) Error(msg string, fields ...any) {
	fmt.Printf("[ERROR] %s", msg)
	if len(fields) > 0 {
		fmt.Printf(" %v", fields)
	}
	fmt.Println()
}

func (l *ConsoleLogger) Debug(msg string, fields ...any) {
	fmt.Printf("[DEBUG] %s", msg)
	if len(fields) > 0 {
		fmt.Printf(" %v", fields)
	}
	fmt.Println()
}

func (l *ConsoleLogger) Warn(msg string, fields ...any) {
	fmt.Printf("[WARN] %s", msg)
	if len(fields) > 0 {
		fmt.Printf(" %v", fields)
	}
	fmt.Println()
}

func (l *ConsoleLogger) Fatal(msg string, fields ...any) {
	fmt.Printf("[FATAL] %s", msg)
	if len(fields) > 0 {
		fmt.Printf(" %v", fields)
	}
	fmt.Println()
	os.Exit(1)
}

// createIDMappingsTable creates the ID mappings table
func createIDMappingsTable(db *sql.DB) error {
	query := `
		CREATE TABLE IF NOT EXISTS id_mappings (
			id SERIAL PRIMARY KEY,
			uuid_id VARCHAR(36) NOT NULL,
			legacy_id VARCHAR(255) NOT NULL,
			table_name VARCHAR(100) NOT NULL,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			migrated BOOLEAN DEFAULT FALSE,
			UNIQUE(uuid_id, legacy_id, table_name)
		);

		CREATE INDEX IF NOT EXISTS idx_id_mappings_uuid ON id_mappings(uuid_id);
		CREATE INDEX IF NOT EXISTS idx_id_mappings_legacy ON id_mappings(legacy_id);
		CREATE INDEX IF NOT EXISTS idx_id_mappings_table ON id_mappings(table_name);
	`

	_, err := db.Exec(query)
	return err
}

// addUUIDColumns adds UUID columns to existing tables
func addUUIDColumns(db *sql.DB) error {
	tables := []string{
		"organizations", "users", "buildings", "floors",
		"zones", "rooms", "equipment", "points", "alarms",
	}

	for _, table := range tables {
		query := fmt.Sprintf(`
			ALTER TABLE %s ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();
			CREATE INDEX IF NOT EXISTS idx_%s_uuid ON %s(uuid_id);
		`, table, table, table)

		if _, err := db.Exec(query); err != nil {
			return fmt.Errorf("failed to add UUID column to %s: %w", table, err)
		}
	}

	return nil
}

// generateUUIDsForExistingRecords generates UUIDs for existing records
func generateUUIDsForExistingRecords(db *sql.DB) error {
	tables := []string{
		"organizations", "users", "buildings", "floors",
		"zones", "rooms", "equipment", "points", "alarms",
	}

	for _, table := range tables {
		query := fmt.Sprintf(`
			UPDATE %s SET uuid_id = gen_random_uuid() WHERE uuid_id IS NULL
		`, table)

		result, err := db.Exec(query)
		if err != nil {
			return fmt.Errorf("failed to generate UUIDs for %s: %w", table, err)
		}

		rowsAffected, _ := result.RowsAffected()
		fmt.Printf("Generated UUIDs for %d records in %s\n", rowsAffected, table)
	}

	return nil
}

// createIDMappings creates ID mappings for all tables
func createIDMappings(db *sql.DB) error {
	tables := []string{
		"organizations", "users", "buildings", "floors",
		"zones", "rooms", "equipment", "points", "alarms",
	}

	for _, table := range tables {
		query := fmt.Sprintf(`
			INSERT INTO id_mappings (uuid_id, legacy_id, table_name, created_at, migrated)
			SELECT uuid_id, id, '%s', CURRENT_TIMESTAMP, FALSE
			FROM %s 
			WHERE uuid_id IS NOT NULL AND id IS NOT NULL
			ON CONFLICT (uuid_id, legacy_id, table_name) DO NOTHING
		`, table, table)

		result, err := db.Exec(query)
		if err != nil {
			return fmt.Errorf("failed to create mappings for %s: %w", table, err)
		}

		rowsAffected, _ := result.RowsAffected()
		fmt.Printf("Created %d mappings for %s\n", rowsAffected, table)
	}

	return nil
}
