package utils

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// IDMapper provides utilities for mapping between UUID and legacy IDs
// This enables gradual migration while maintaining backward compatibility
type IDMapper struct {
	db     *sqlx.DB
	logger domain.Logger
}

// NewIDMapper creates a new ID mapper
func NewIDMapper(db *sqlx.DB, logger domain.Logger) *IDMapper {
	return &IDMapper{
		db:     db,
		logger: logger,
	}
}

// IDMapping represents a mapping between UUID and legacy ID
type IDMapping struct {
	UUID     string    `db:"uuid_id"`
	Legacy   string    `db:"legacy_id"`
	Table    string    `db:"table_name"`
	Created  time.Time `db:"created_at"`
	Migrated bool      `db:"migrated"`
}

// CreateMapping creates a mapping between UUID and legacy ID
func (m *IDMapper) CreateMapping(ctx context.Context, table, uuidID, legacyID string) error {
	query := `
		INSERT INTO id_mappings (uuid_id, legacy_id, table_name, created_at, migrated)
		VALUES ($1, $2, $3, $4, $5)
		ON CONFLICT (uuid_id, legacy_id, table_name) DO NOTHING
	`

	_, err := m.db.ExecContext(ctx, query, uuidID, legacyID, table, time.Now(), false)
	if err != nil {
		m.logger.Error("Failed to create ID mapping", map[string]any{
			"table":     table,
			"uuid_id":   uuidID,
			"legacy_id": legacyID,
			"error":     err,
		})
		return fmt.Errorf("failed to create ID mapping: %w", err)
	}

	return nil
}

// GetUUIDFromLegacy retrieves the UUID for a given legacy ID
func (m *IDMapper) GetUUIDFromLegacy(ctx context.Context, table, legacyID string) (string, error) {
	query := `
		SELECT uuid_id FROM id_mappings 
		WHERE legacy_id = $1 AND table_name = $2
	`

	var uuidID string
	err := m.db.GetContext(ctx, &uuidID, query, legacyID, table)
	if err != nil {
		if err == sql.ErrNoRows {
			return "", fmt.Errorf("no UUID mapping found for legacy ID %s in table %s", legacyID, table)
		}
		return "", fmt.Errorf("failed to get UUID from legacy ID: %w", err)
	}

	return uuidID, nil
}

// GetLegacyFromUUID retrieves the legacy ID for a given UUID
func (m *IDMapper) GetLegacyFromUUID(ctx context.Context, table, uuidID string) (string, error) {
	query := `
		SELECT legacy_id FROM id_mappings 
		WHERE uuid_id = $1 AND table_name = $2
	`

	var legacyID string
	err := m.db.GetContext(ctx, &legacyID, query, uuidID, table)
	if err != nil {
		if err == sql.ErrNoRows {
			return "", fmt.Errorf("no legacy mapping found for UUID %s in table %s", uuidID, table)
		}
		return "", fmt.Errorf("failed to get legacy ID from UUID: %w", err)
	}

	return legacyID, nil
}

// ResolveID resolves an ID to its canonical form (UUID if available)
func (m *IDMapper) ResolveID(ctx context.Context, table string, id types.ID) (types.ID, error) {
	if id.IsEmpty() {
		return types.ID{}, fmt.Errorf("cannot resolve empty ID")
	}

	// If we already have a UUID, return as-is
	if id.UUID != "" {
		return id, nil
	}

	// Try to find UUID for legacy ID
	uuidID, err := m.GetUUIDFromLegacy(ctx, table, id.Legacy)
	if err != nil {
		// If no mapping exists, create a new UUID and mapping
		newUUID := uuid.New().String()
		if err := m.CreateMapping(ctx, table, newUUID, id.Legacy); err != nil {
			return types.ID{}, fmt.Errorf("failed to create mapping for legacy ID: %w", err)
		}

		return types.ID{
			UUID:   newUUID,
			Legacy: id.Legacy,
		}, nil
	}

	return types.ID{
		UUID:   uuidID,
		Legacy: id.Legacy,
	}, nil
}

// MigrateTableIDs migrates all IDs in a table from legacy to UUID format
func (m *IDMapper) MigrateTableIDs(ctx context.Context, table string) error {
	m.logger.Info("Starting ID migration for table", map[string]any{
		"table": table,
	})

	// Get all records with legacy IDs but no UUID
	query := fmt.Sprintf(`
		SELECT id FROM %s 
		WHERE uuid_id IS NULL OR uuid_id = ''
	`, table)

	rows, err := m.db.QueryContext(ctx, query)
	if err != nil {
		return fmt.Errorf("failed to query table %s: %w", table, err)
	}
	defer rows.Close()

	var migratedCount int
	for rows.Next() {
		var legacyID string
		if err := rows.Scan(&legacyID); err != nil {
			m.logger.Error("Failed to scan legacy ID", map[string]any{
				"table": table,
				"error": err,
			})
			continue
		}

		// Generate new UUID
		newUUID := uuid.New().String()

		// Update the record with UUID
		updateQuery := fmt.Sprintf(`
			UPDATE %s SET uuid_id = $1 WHERE id = $2
		`, table)

		_, err := m.db.ExecContext(ctx, updateQuery, newUUID, legacyID)
		if err != nil {
			m.logger.Error("Failed to update record with UUID", map[string]any{
				"table":     table,
				"legacy_id": legacyID,
				"uuid":      newUUID,
				"error":     err,
			})
			continue
		}

		// Create mapping
		if err := m.CreateMapping(ctx, table, newUUID, legacyID); err != nil {
			m.logger.Error("Failed to create ID mapping", map[string]any{
				"table":     table,
				"legacy_id": legacyID,
				"uuid":      newUUID,
				"error":     err,
			})
			continue
		}

		migratedCount++
	}

	m.logger.Info("Completed ID migration for table", map[string]any{
		"table":          table,
		"migrated_count": migratedCount,
	})

	return nil
}

// GetMigrationStatus returns the migration status for a table
func (m *IDMapper) GetMigrationStatus(ctx context.Context, table string) (map[string]any, error) {
	// Count total records
	var totalRecords int
	countQuery := fmt.Sprintf(`SELECT COUNT(*) FROM %s`, table)
	err := m.db.GetContext(ctx, &totalRecords, countQuery)
	if err != nil {
		return nil, fmt.Errorf("failed to count records: %w", err)
	}

	// Count records with UUIDs
	var uuidRecords int
	uuidQuery := fmt.Sprintf(`SELECT COUNT(*) FROM %s WHERE uuid_id IS NOT NULL AND uuid_id != ''`, table)
	err = m.db.GetContext(ctx, &uuidRecords, uuidQuery)
	if err != nil {
		return nil, fmt.Errorf("failed to count UUID records: %w", err)
	}

	// Count mappings
	var mappingCount int
	mappingQuery := `SELECT COUNT(*) FROM id_mappings WHERE table_name = $1`
	err = m.db.GetContext(ctx, &mappingCount, mappingQuery, table)
	if err != nil {
		return nil, fmt.Errorf("failed to count mappings: %w", err)
	}

	return map[string]any{
		"table":          table,
		"total_records":  totalRecords,
		"uuid_records":   uuidRecords,
		"legacy_records": totalRecords - uuidRecords,
		"mappings":       mappingCount,
		"migration_pct":  float64(uuidRecords) / float64(totalRecords) * 100,
	}, nil
}

// CreateIDMappingsTable creates the ID mappings table if it doesn't exist
func (m *IDMapper) CreateIDMappingsTable(ctx context.Context) error {
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

	_, err := m.db.ExecContext(ctx, query)
	if err != nil {
		return fmt.Errorf("failed to create ID mappings table: %w", err)
	}

	return nil
}
