package sqlite_to_postgis

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	_ "github.com/mattn/go-sqlite3"
	_ "github.com/lib/pq"
)

// Migrator handles migration from SQLite to PostGIS
type Migrator struct {
	sqliteDB  *sqlx.DB
	postgisDB *sqlx.DB
	config    Config
	stats     MigrationStats
}

// Config contains migration configuration
type Config struct {
	SQLitePath     string
	PostGISConnStr string
	BatchSize      int
	DryRun         bool
	Verbose        bool
}

// MigrationStats tracks migration statistics
type MigrationStats struct {
	BuildingsMigrated  int
	EquipmentMigrated  int
	UsersMigrated      int
	ErrorCount         int
	StartTime          time.Time
	EndTime            time.Time
}

// NewMigrator creates a new migrator instance
func NewMigrator(config Config) (*Migrator, error) {
	// Open SQLite connection
	sqliteDB, err := sqlx.Connect("sqlite3", config.SQLitePath)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to SQLite: %w", err)
	}

	// Open PostGIS connection
	postgisDB, err := sqlx.Connect("postgres", config.PostGISConnStr)
	if err != nil {
		sqliteDB.Close()
		return nil, fmt.Errorf("failed to connect to PostGIS: %w", err)
	}

	// Verify PostGIS extension
	var version string
	err = postgisDB.Get(&version, "SELECT PostGIS_Version()")
	if err != nil {
		sqliteDB.Close()
		postgisDB.Close()
		return nil, fmt.Errorf("PostGIS not available: %w", err)
	}

	if config.BatchSize == 0 {
		config.BatchSize = 100
	}

	return &Migrator{
		sqliteDB:  sqliteDB,
		postgisDB: postgisDB,
		config:    config,
		stats:     MigrationStats{StartTime: time.Now()},
	}, nil
}

// Close closes database connections
func (m *Migrator) Close() error {
	var errs []error
	if err := m.sqliteDB.Close(); err != nil {
		errs = append(errs, err)
	}
	if err := m.postgisDB.Close(); err != nil {
		errs = append(errs, err)
	}
	if len(errs) > 0 {
		return fmt.Errorf("errors closing connections: %v", errs)
	}
	return nil
}

// Migrate performs the complete migration
func (m *Migrator) Migrate(ctx context.Context) error {
	log.Println("Starting SQLite to PostGIS migration...")

	// Start transaction for PostGIS
	tx, err := m.postgisDB.BeginTxx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}
	defer tx.Rollback()

	// Migrate buildings
	if err := m.migrateBuildings(ctx, tx); err != nil {
		return fmt.Errorf("failed to migrate buildings: %w", err)
	}

	// Migrate equipment
	if err := m.migrateEquipment(ctx, tx); err != nil {
		return fmt.Errorf("failed to migrate equipment: %w", err)
	}

	// Migrate users
	if err := m.migrateUsers(ctx, tx); err != nil {
		return fmt.Errorf("failed to migrate users: %w", err)
	}

	// Commit transaction if not dry run
	if !m.config.DryRun {
		if err := tx.Commit(); err != nil {
			return fmt.Errorf("failed to commit transaction: %w", err)
		}
	}

	m.stats.EndTime = time.Now()
	return nil
}

// migrateBuildings migrates building data
func (m *Migrator) migrateBuildings(ctx context.Context, tx *sqlx.Tx) error {
	log.Println("Migrating buildings...")

	// Query SQLite buildings
	rows, err := m.sqliteDB.QueryContext(ctx, `
		SELECT id, arxos_id, name, address,
		       latitude, longitude, altitude, rotation,
		       created_at, updated_at
		FROM buildings
	`)
	if err != nil {
		return fmt.Errorf("failed to query buildings: %w", err)
	}
	defer rows.Close()

	// Prepare PostGIS insert
	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO buildings (
			id, arxos_id, name, address,
			origin, rotation,
			created_at, updated_at
		) VALUES (
			$1, $2, $3, $4,
			ST_SetSRID(ST_MakePoint($5, $6, $7), 4326), $8,
			$9, $10
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare insert statement: %w", err)
	}
	defer stmt.Close()

	count := 0
	for rows.Next() {
		var (
			id        string
			arxosID   string
			name      string
			address   sql.NullString
			lat       sql.NullFloat64
			lon       sql.NullFloat64
			alt       sql.NullFloat64
			rotation  sql.NullFloat64
			createdAt time.Time
			updatedAt time.Time
		)

		err := rows.Scan(&id, &arxosID, &name, &address,
			&lat, &lon, &alt, &rotation,
			&createdAt, &updatedAt)
		if err != nil {
			m.stats.ErrorCount++
			log.Printf("Error scanning building: %v", err)
			continue
		}

		// Convert ID to UUID
		buildingID, err := uuid.Parse(id)
		if err != nil {
			// Generate new UUID if invalid
			buildingID = uuid.New()
		}

		// Execute insert if not dry run
		if !m.config.DryRun {
			_, err = stmt.ExecContext(ctx,
				buildingID, arxosID, name, address.String,
				lon.Float64, lat.Float64, alt.Float64, rotation.Float64,
				createdAt, updatedAt,
			)
			if err != nil {
				m.stats.ErrorCount++
				log.Printf("Error inserting building %s: %v", arxosID, err)
				continue
			}
		}

		count++
		m.stats.BuildingsMigrated++

		if m.config.Verbose && count%10 == 0 {
			log.Printf("Migrated %d buildings...", count)
		}
	}

	log.Printf("Migrated %d buildings", m.stats.BuildingsMigrated)
	return nil
}

// migrateEquipment migrates equipment data
func (m *Migrator) migrateEquipment(ctx context.Context, tx *sqlx.Tx) error {
	log.Println("Migrating equipment...")

	// Query SQLite equipment
	rows, err := m.sqliteDB.QueryContext(ctx, `
		SELECT id, building_id, path, name, type,
		       x_coord, y_coord, z_coord,
		       status, confidence,
		       created_at, updated_at
		FROM equipment
	`)
	if err != nil {
		return fmt.Errorf("failed to query equipment: %w", err)
	}
	defer rows.Close()

	// Prepare PostGIS insert
	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO equipment (
			id, building_id, path, name, type,
			position, status, confidence,
			created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5,
			ST_SetSRID(ST_MakePoint($6, $7, $8), 4326), $9, $10,
			$11, $12
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare equipment insert: %w", err)
	}
	defer stmt.Close()

	// Also prepare query to get building origin for coordinate transformation
	buildingStmt, err := tx.PrepareContext(ctx, `
		SELECT ST_X(origin), ST_Y(origin), ST_Z(origin), rotation
		FROM buildings WHERE id = $1
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare building query: %w", err)
	}
	defer buildingStmt.Close()

	count := 0
	for rows.Next() {
		var (
			id          string
			buildingID  string
			path        string
			name        string
			eqType      string
			xCoord      sql.NullFloat64
			yCoord      sql.NullFloat64
			zCoord      sql.NullFloat64
			status      sql.NullString
			confidence  sql.NullInt64
			createdAt   time.Time
			updatedAt   time.Time
		)

		err := rows.Scan(&id, &buildingID, &path, &name, &eqType,
			&xCoord, &yCoord, &zCoord,
			&status, &confidence,
			&createdAt, &updatedAt)
		if err != nil {
			m.stats.ErrorCount++
			log.Printf("Error scanning equipment: %v", err)
			continue
		}

		// Convert IDs to UUID
		equipmentID, err := uuid.Parse(id)
		if err != nil {
			equipmentID = uuid.New()
		}

		bldgID, err := uuid.Parse(buildingID)
		if err != nil {
			m.stats.ErrorCount++
			log.Printf("Invalid building ID for equipment %s: %v", name, err)
			continue
		}

		// Get building origin for coordinate transformation
		var originLon, originLat, originAlt, rotation sql.NullFloat64
		err = buildingStmt.QueryRowContext(ctx, bldgID).Scan(
			&originLon, &originLat, &originAlt, &rotation,
		)
		if err != nil {
			// If building not found, use equipment coordinates as-is
			originLon.Float64 = 0
			originLat.Float64 = 0
			originAlt.Float64 = 0
		}

		// Transform local coordinates to global if we have building origin
		globalLon := originLon.Float64 + xCoord.Float64/111111.0 // Simple conversion
		globalLat := originLat.Float64 + yCoord.Float64/111111.0
		globalAlt := originAlt.Float64 + zCoord.Float64

		// Execute insert if not dry run
		if !m.config.DryRun {
			_, err = stmt.ExecContext(ctx,
				equipmentID, bldgID, path, name, eqType,
				globalLon, globalLat, globalAlt,
				status.String, confidence.Int64,
				createdAt, updatedAt,
			)
			if err != nil {
				m.stats.ErrorCount++
				log.Printf("Error inserting equipment %s: %v", name, err)
				continue
			}
		}

		count++
		m.stats.EquipmentMigrated++

		if m.config.Verbose && count%100 == 0 {
			log.Printf("Migrated %d equipment items...", count)
		}
	}

	log.Printf("Migrated %d equipment items", m.stats.EquipmentMigrated)
	return nil
}

// migrateUsers migrates user data
func (m *Migrator) migrateUsers(ctx context.Context, tx *sqlx.Tx) error {
	log.Println("Migrating users...")

	// Query SQLite users
	rows, err := m.sqliteDB.QueryContext(ctx, `
		SELECT id, email, full_name, password_hash,
		       role, status, last_login,
		       created_at, updated_at
		FROM users
	`)
	if err != nil {
		// Users table might not exist in SQLite
		log.Printf("Skipping users migration: %v", err)
		return nil
	}
	defer rows.Close()

	// Prepare PostGIS insert
	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO users (
			id, email, full_name, password_hash,
			role, status, last_login,
			created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare user insert: %w", err)
	}
	defer stmt.Close()

	count := 0
	for rows.Next() {
		var (
			id           string
			email        string
			fullName     sql.NullString
			passwordHash string
			role         string
			status       string
			lastLogin    sql.NullTime
			createdAt    time.Time
			updatedAt    time.Time
		)

		err := rows.Scan(&id, &email, &fullName, &passwordHash,
			&role, &status, &lastLogin,
			&createdAt, &updatedAt)
		if err != nil {
			m.stats.ErrorCount++
			log.Printf("Error scanning user: %v", err)
			continue
		}

		// Convert ID to UUID
		userID, err := uuid.Parse(id)
		if err != nil {
			userID = uuid.New()
		}

		// Execute insert if not dry run
		if !m.config.DryRun {
			_, err = stmt.ExecContext(ctx,
				userID, email, fullName.String, passwordHash,
				role, status, lastLogin.Time,
				createdAt, updatedAt,
			)
			if err != nil {
				m.stats.ErrorCount++
				log.Printf("Error inserting user %s: %v", email, err)
				continue
			}
		}

		count++
		m.stats.UsersMigrated++
	}

	log.Printf("Migrated %d users", m.stats.UsersMigrated)
	return nil
}

// GetStats returns migration statistics
func (m *Migrator) GetStats() MigrationStats {
	return m.stats
}

// PrintSummary prints migration summary
func (m *Migrator) PrintSummary() {
	duration := m.stats.EndTime.Sub(m.stats.StartTime)

	fmt.Println("\n=== Migration Summary ===")
	fmt.Printf("Duration: %v\n", duration)
	fmt.Printf("Buildings migrated: %d\n", m.stats.BuildingsMigrated)
	fmt.Printf("Equipment migrated: %d\n", m.stats.EquipmentMigrated)
	fmt.Printf("Users migrated: %d\n", m.stats.UsersMigrated)
	fmt.Printf("Errors: %d\n", m.stats.ErrorCount)

	if m.config.DryRun {
		fmt.Println("\nDRY RUN - No data was actually migrated")
	}
}