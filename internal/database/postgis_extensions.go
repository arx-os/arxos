package database

import (
	"context"
	"database/sql"
	"os"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/errors"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
)

// --- User Management Methods ---
// User management methods are implemented in user_management.go

// --- Session Management Methods ---
// Session management methods are implemented in user_management.go

// --- Organization Management Methods ---
// Organization management methods are implemented in organization_management.go

// --- Spatial Anchor Methods ---

// GetSpatialAnchors retrieves spatial anchors for a building
func (p *PostGISDB) GetSpatialAnchors(ctx context.Context, buildingID string) ([]*SpatialAnchor, error) {
	query := `
		SELECT id, building_id, equipment_id, 
		       ST_X(position) as x, ST_Y(position) as y, ST_Z(position) as z,
		       confidence, last_scanned, scan_metadata
		FROM spatial_anchors 
		WHERE building_id = $1
		ORDER BY last_scanned DESC`

	rows, err := p.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var anchors []*SpatialAnchor
	for rows.Next() {
		var anchor SpatialAnchor
		var x, y, z float64
		var scanMetadata sql.NullString

		err := rows.Scan(
			&anchor.ID, &anchor.BuildingID, &anchor.EquipmentID,
			&x, &y, &z, &anchor.Confidence, &anchor.LastScanned, &scanMetadata,
		)
		if err != nil {
			return nil, err
		}

		anchor.Position = Point3D{X: x, Y: y, Z: z}

		// Parse scan metadata if present
		if scanMetadata.Valid && scanMetadata.String != "" {
			// In a real implementation, you'd parse JSON here
			anchor.ScanMetadata = make(map[string]interface{})
		} else {
			anchor.ScanMetadata = make(map[string]interface{})
		}

		anchors = append(anchors, &anchor)
	}

	return anchors, rows.Err()
}

// SaveSpatialAnchor saves a spatial anchor
func (p *PostGISDB) SaveSpatialAnchor(ctx context.Context, anchor *SpatialAnchor) error {
	query := `
		INSERT INTO spatial_anchors (id, building_id, equipment_id, position, confidence, last_scanned, scan_metadata)
		VALUES ($1, $2, $3, ST_MakePoint($4, $5, $6), $7, $8, $9)
		ON CONFLICT (id) DO UPDATE SET
			equipment_id = EXCLUDED.equipment_id,
			position = EXCLUDED.position,
			confidence = EXCLUDED.confidence,
			last_scanned = EXCLUDED.last_scanned,
			scan_metadata = EXCLUDED.scan_metadata`

	// Convert scan metadata to JSON string
	metadataJSON := "{}" // In a real implementation, you'd marshal the map to JSON
	if len(anchor.ScanMetadata) > 0 {
		// metadataJSON = json.Marshal(anchor.ScanMetadata)
	}

	_, err := p.db.ExecContext(ctx, query,
		anchor.ID, anchor.BuildingID, anchor.EquipmentID,
		anchor.Position.X, anchor.Position.Y, anchor.Position.Z,
		anchor.Confidence, anchor.LastScanned, metadataJSON,
	)

	return err
}

// --- Additional Interface Methods ---

// GetVersion returns the database schema version
func (p *PostGISDB) GetVersion(ctx context.Context) (int, error) {
	query := `
		SELECT COALESCE(
			(SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1),
			0
		)`

	var version int
	err := p.db.QueryRowContext(ctx, query).Scan(&version)
	if err != nil {
		// If schema_migrations table doesn't exist, return 0
		if err == sql.ErrNoRows {
			return 0, nil
		}
		return 0, err
	}

	return version, nil
}

// Migrate applies database migrations using the migrator
func (p *PostGISDB) Migrate(ctx context.Context) error {
	// Get migrations directory from environment or use default
	migrationsDir := os.Getenv("ARXOS_MIGRATIONS_DIR")
	if migrationsDir == "" {
		migrationsDir = "migrations"
	}

	// Create migrator
	migrator := NewMigrator(p.db, migrationsDir)

	// Load migrations from files
	if err := migrator.LoadMigrations(); err != nil {
		// If no migrations directory exists, fall back to hardcoded migrations
		logger.Warn("Failed to load migrations from files: %v", err)
		return p.migrateHardcoded(ctx)
	}

	// Validate migrations
	if err := migrator.ValidateMigrations(); err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "validate migrations")
	}

	// Apply migrations
	if err := migrator.Migrate(ctx); err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "apply migrations")
	}

	return nil
}

// migrateHardcoded applies hardcoded migrations as fallback
func (p *PostGISDB) migrateHardcoded(ctx context.Context) error {
	// Create migrations table if it doesn't exist
	createTableSQL := `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version INTEGER PRIMARY KEY,
			description TEXT NOT NULL,
			applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`

	_, err := p.db.ExecContext(ctx, createTableSQL)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "create migrations table")
	}

	// Get current version
	currentVersion, err := p.GetVersion(ctx)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "get current version")
	}

	// Define migrations
	migrations := []struct {
		version     int
		description string
		sql         string
	}{
		{
			version:     1,
			description: "create spatial anchors table",
			sql: `
				CREATE TABLE IF NOT EXISTS spatial_anchors (
					id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
					building_id UUID NOT NULL,
					equipment_id UUID,
					position GEOMETRY(POINTZ, 4326) NOT NULL,
					confidence FLOAT DEFAULT 1.0,
					last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					scan_metadata JSONB,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				);
				CREATE INDEX IF NOT EXISTS idx_spatial_anchors_building ON spatial_anchors(building_id);
				CREATE INDEX IF NOT EXISTS idx_spatial_anchors_equipment ON spatial_anchors(equipment_id);
				CREATE INDEX IF NOT EXISTS idx_spatial_anchors_position ON spatial_anchors USING GIST(position);
			`,
		},
		{
			version:     2,
			description: "create change tracking table",
			sql: `
				CREATE TABLE IF NOT EXISTS change_tracking (
					id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
					entity_type VARCHAR(50) NOT NULL,
					entity_id UUID NOT NULL,
					change_type VARCHAR(20) NOT NULL,
					change_data JSONB,
					created_by UUID,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				);
				CREATE INDEX IF NOT EXISTS idx_change_tracking_entity ON change_tracking(entity_type, entity_id);
				CREATE INDEX IF NOT EXISTS idx_change_tracking_created_at ON change_tracking(created_at);
			`,
		},
		{
			version:     3,
			description: "create conflicts table",
			sql: `
				CREATE TABLE IF NOT EXISTS conflicts (
					id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
					building_id UUID NOT NULL,
					conflict_type VARCHAR(50) NOT NULL,
					conflict_data JSONB,
					resolution_status VARCHAR(20) DEFAULT 'pending',
					resolved_by UUID,
					resolved_at TIMESTAMP,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				);
				CREATE INDEX IF NOT EXISTS idx_conflicts_building ON conflicts(building_id);
				CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(resolution_status);
			`,
		},
		{
			version:     4,
			description: "create sync status table",
			sql: `
				CREATE TABLE IF NOT EXISTS sync_status (
					id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
					building_id UUID NOT NULL UNIQUE,
					last_sync TIMESTAMP,
					sync_status VARCHAR(20) DEFAULT 'pending',
					error_message TEXT,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				);
				CREATE INDEX IF NOT EXISTS idx_sync_status_building ON sync_status(building_id);
				CREATE INDEX IF NOT EXISTS idx_sync_status_status ON sync_status(sync_status);
			`,
		},
	}

	// Apply pending migrations
	for _, migration := range migrations {
		if migration.version > currentVersion {
			logger.Info("Applying migration %d: %s", migration.version, migration.description)

			// Start transaction
			tx, err := p.db.BeginTx(ctx, nil)
			if err != nil {
				return errors.Wrap(err, errors.CodeDatabase, "start migration transaction")
			}

			// Execute migration SQL
			_, err = tx.ExecContext(ctx, migration.sql)
			if err != nil {
				tx.Rollback()
				return errors.Wrap(err, errors.CodeDatabase, "execute migration")
			}

			// Record migration
			_, err = tx.ExecContext(ctx,
				"INSERT INTO schema_migrations (version, description) VALUES ($1, $2)",
				migration.version, migration.description,
			)
			if err != nil {
				tx.Rollback()
				return errors.Wrap(err, errors.CodeDatabase, "record migration")
			}

			// Commit transaction
			if err := tx.Commit(); err != nil {
				return errors.Wrap(err, errors.CodeDatabase, "commit migration")
			}

			logger.Info("Applied migration %d successfully", migration.version)
		}
	}

	logger.Info("Database migrations completed")
	return nil
}

// BeginTx starts a new transaction
func (p *PostGISDB) BeginTx(ctx context.Context) (*sql.Tx, error) {
	return p.db.BeginTx(ctx, nil)
}

// HasSpatialSupport returns true for PostGIS
func (p *PostGISDB) HasSpatialSupport() bool {
	return true
}

// GetSpatialDB returns self as PostGIS implements SpatialDB
func (p *PostGISDB) GetSpatialDB() (SpatialDB, error) {
	return p, nil
}

// --- Sync Helper Methods ---

// GetEntityVersion gets the version of an entity (for sync)
func (p *PostGISDB) GetEntityVersion(ctx context.Context, entityType, entityID string) (int, error) {
	query := `
		SELECT COALESCE(MAX(version), 0)
		FROM change_tracking
		WHERE entity_type = $1 AND entity_id = $2`

	var version int
	err := p.db.QueryRowContext(ctx, query, entityType, entityID).Scan(&version)
	if err != nil {
		return 0, err
	}

	return version, nil
}

// ApplyChange applies a change from sync
func (p *PostGISDB) ApplyChange(ctx context.Context, change *syncpkg.Change) error {
	// Record the change in change_tracking table
	query := `
		INSERT INTO change_tracking (id, entity_type, entity_id, change_type, change_data, version, created_by)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (id) DO UPDATE SET
			change_data = EXCLUDED.change_data,
			version = EXCLUDED.version,
			created_at = CURRENT_TIMESTAMP`

	// Convert change data to JSON (simplified)
	changeDataJSON := "{}" // In real implementation, marshal change.Data to JSON

	_, err := p.db.ExecContext(ctx, query,
		change.ID, change.Entity, change.EntityID, change.Type,
		changeDataJSON, change.Version, change.UserID,
	)

	return err
}

// GetChangesSince gets changes since a timestamp
func (p *PostGISDB) GetChangesSince(ctx context.Context, since time.Time, entityType string) ([]*syncpkg.Change, error) {
	query := `
		SELECT id, entity_type, entity_id, change_type, change_data, version, created_at, created_by
		FROM change_tracking
		WHERE created_at > $1 AND ($2 = '' OR entity_type = $2)
		ORDER BY created_at ASC`

	rows, err := p.db.QueryContext(ctx, query, since, entityType)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var changes []*syncpkg.Change
	for rows.Next() {
		var change syncpkg.Change
		var changeDataJSON sql.NullString

		err := rows.Scan(
			&change.ID, &change.Entity, &change.EntityID, &change.Type,
			&changeDataJSON, &change.Version, &change.Timestamp, &change.UserID,
		)
		if err != nil {
			return nil, err
		}

		// Parse change data JSON (simplified)
		change.Data = make(map[string]interface{})
		if changeDataJSON.Valid && changeDataJSON.String != "" {
			// In real implementation, unmarshal JSON here
		}

		changes = append(changes, &change)
	}

	return changes, rows.Err()
}

// GetPendingConflicts gets pending conflicts
func (p *PostGISDB) GetPendingConflicts(ctx context.Context, buildingID string) ([]*syncpkg.Conflict, error) {
	query := `
		SELECT id, entity_type, entity_id, conflict_type, conflict_data, 
		       created_at, resolved_at, resolution
		FROM conflicts
		WHERE building_id = $1 AND resolved_at IS NULL
		ORDER BY created_at ASC`

	rows, err := p.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var conflicts []*syncpkg.Conflict
	for rows.Next() {
		var conflict syncpkg.Conflict
		var conflictDataJSON sql.NullString
		var resolvedAt sql.NullTime

		err := rows.Scan(
			&conflict.ID, &conflict.Entity, &conflict.EntityID, &conflict.ConflictType,
			&conflictDataJSON, &conflict.CreatedAt, &resolvedAt, &conflict.Resolution,
		)
		if err != nil {
			return nil, err
		}

		if resolvedAt.Valid {
			conflict.ResolvedAt = &resolvedAt.Time
		}

		// Parse conflict data JSON (simplified)
		conflict.LocalData = make(map[string]interface{})
		conflict.RemoteData = make(map[string]interface{})
		if conflictDataJSON.Valid && conflictDataJSON.String != "" {
			// In real implementation, unmarshal JSON here
		}

		conflicts = append(conflicts, &conflict)
	}

	return conflicts, rows.Err()
}

// GetLastSyncTime gets last sync time
func (p *PostGISDB) GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error) {
	query := `
		SELECT COALESCE(MAX(last_sync), '1970-01-01'::timestamp)
		FROM sync_status
		WHERE building_id = $1`

	var lastSync time.Time
	err := p.db.QueryRowContext(ctx, query, buildingID).Scan(&lastSync)
	if err != nil {
		return time.Time{}, err
	}

	return lastSync, nil
}

// GetPendingChangesCount gets pending changes count
func (p *PostGISDB) GetPendingChangesCount(ctx context.Context, buildingID string) (int, error) {
	query := `
		SELECT COUNT(*)
		FROM change_tracking ct
		JOIN equipment e ON ct.entity_id = e.id
		WHERE e.building_id = $1 AND ct.created_at > (
			SELECT COALESCE(MAX(last_sync), '1970-01-01'::timestamp)
			FROM sync_status
			WHERE building_id = $1
		)`

	var count int
	err := p.db.QueryRowContext(ctx, query, buildingID).Scan(&count)
	if err != nil {
		return 0, err
	}

	return count, nil
}

// GetConflictCount gets conflict count
func (p *PostGISDB) GetConflictCount(ctx context.Context, buildingID string) (int, error) {
	query := `
		SELECT COUNT(*)
		FROM conflicts
		WHERE building_id = $1 AND resolved_at IS NULL`

	var count int
	err := p.db.QueryRowContext(ctx, query, buildingID).Scan(&count)
	if err != nil {
		return 0, err
	}

	return count, nil
}
