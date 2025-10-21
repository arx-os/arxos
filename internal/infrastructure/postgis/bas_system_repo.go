package postgis

import (
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/types"
)

// BASSystemRepository implements BAS system repository for PostGIS
type BASSystemRepository struct {
	db *sql.DB
}

// NewBASSystemRepository creates a new PostGIS BAS system repository
func NewBASSystemRepository(db *sql.DB) *BASSystemRepository {
	return &BASSystemRepository{
		db: db,
	}
}

// Create creates a new BAS system in PostGIS
func (r *BASSystemRepository) Create(system *bas.BASSystem) error {
	query := `
		INSERT INTO bas_systems (
			id, building_id, repository_id,
			name, system_type, vendor, version,
			host, port, protocol,
			enabled, read_only, sync_interval, last_sync,
			metadata, notes,
			created_at, updated_at, created_by
		) VALUES (
			$1, $2, $3,
			$4, $5, $6, $7,
			$8, $9, $10,
			$11, $12, $13, $14,
			$15, $16,
			$17, $18, $19
		)
	`

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(system.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.Exec(query,
		system.ID.String(), system.BuildingID.String(), nullableID(system.RepositoryID),
		system.Name, system.SystemType, system.Vendor, system.Version,
		system.Host, system.Port, nullableProtocol(system.Protocol),
		system.Enabled, system.ReadOnly, system.SyncInterval, system.LastSync,
		metadataJSON, system.Notes,
		system.CreatedAt, system.UpdatedAt, nullableID(system.CreatedBy),
	)

	return err
}

// GetByID retrieves a BAS system by ID
func (r *BASSystemRepository) GetByID(id types.ID) (*bas.BASSystem, error) {
	query := `
		SELECT
			id, building_id, repository_id,
			name, system_type, vendor, version,
			host, port, protocol,
			enabled, read_only, sync_interval, last_sync,
			metadata, notes,
			created_at, updated_at, created_by
		FROM bas_systems
		WHERE id = $1
	`

	system := &bas.BASSystem{}
	var repositoryID, createdBy sql.NullString
	var vendor, version, host, protocol, notes sql.NullString
	var port, syncInterval sql.NullInt64
	var lastSync sql.NullTime

	err := r.db.QueryRow(query, id.String()).Scan(
		&system.ID, &system.BuildingID, &repositoryID,
		&system.Name, &system.SystemType, &vendor, &version,
		&host, &port, &protocol,
		&system.Enabled, &system.ReadOnly, &syncInterval, &lastSync,
		&system.Metadata, &notes,
		&system.CreatedAt, &system.UpdatedAt, &createdBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("BAS system not found")
		}
		return nil, err
	}

	// Handle nullable fields
	if repositoryID.Valid {
		id := types.FromString(repositoryID.String)
		system.RepositoryID = &id
	}
	if vendor.Valid {
		system.Vendor = vendor.String
	}
	if version.Valid {
		system.Version = version.String
	}
	if host.Valid {
		system.Host = host.String
	}
	if port.Valid {
		val := int(port.Int64)
		system.Port = val
	}
	if protocol.Valid {
		proto := bas.BASProtocol(protocol.String)
		system.Protocol = &proto
	}
	if syncInterval.Valid {
		val := int(syncInterval.Int64)
		system.SyncInterval = &val
	}
	if lastSync.Valid {
		system.LastSync = &lastSync.Time
	}
	if notes.Valid {
		system.Notes = notes.String
	}
	if createdBy.Valid {
		id := types.FromString(createdBy.String)
		system.CreatedBy = &id
	}

	return system, nil
}

// Update updates an existing BAS system
func (r *BASSystemRepository) Update(system *bas.BASSystem) error {
	query := `
		UPDATE bas_systems SET
			name = $1,
			vendor = $2,
			version = $3,
			host = $4,
			port = $5,
			protocol = $6,
			enabled = $7,
			read_only = $8,
			sync_interval = $9,
			last_sync = $10,
			metadata = $11,
			notes = $12,
			updated_at = NOW()
		WHERE id = $13
	`

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(system.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.Exec(query,
		system.Name, system.Vendor, system.Version,
		system.Host, system.Port, nullableProtocol(system.Protocol),
		system.Enabled, system.ReadOnly, system.SyncInterval, system.LastSync,
		metadataJSON, system.Notes,
		system.ID.String(),
	)

	return err
}

// Delete deletes a BAS system (cascades to points)
func (r *BASSystemRepository) Delete(id types.ID) error {
	query := `DELETE FROM bas_systems WHERE id = $1`

	result, err := r.db.Exec(query, id.String())
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("BAS system not found")
	}

	return nil
}

// List retrieves all BAS systems for a building
func (r *BASSystemRepository) List(buildingID types.ID) ([]*bas.BASSystem, error) {
	query := `
		SELECT
			id, building_id, repository_id,
			name, system_type, vendor, version,
			host, port, protocol,
			enabled, read_only, sync_interval, last_sync,
			metadata, notes,
			created_at, updated_at, created_by
		FROM bas_systems
		WHERE building_id = $1
		ORDER BY name
	`

	rows, err := r.db.Query(query, buildingID.String())
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	systems := make([]*bas.BASSystem, 0)
	for rows.Next() {
		system := &bas.BASSystem{}
		var repositoryID, createdBy sql.NullString
		var vendor, version, host, protocol, notes sql.NullString
		var port, syncInterval sql.NullInt64
		var lastSync sql.NullTime
		var metadataJSON []byte // Scan JSONB as bytes first

		err := rows.Scan(
			&system.ID, &system.BuildingID, &repositoryID,
			&system.Name, &system.SystemType, &vendor, &version,
			&host, &port, &protocol,
			&system.Enabled, &system.ReadOnly, &syncInterval, &lastSync,
			&metadataJSON, &notes,
			&system.CreatedAt, &system.UpdatedAt, &createdBy,
		)

		if err != nil {
			return nil, err
		}

		// Parse metadata JSON
		if len(metadataJSON) > 0 {
			system.Metadata = make(map[string]any)
			if err := json.Unmarshal(metadataJSON, &system.Metadata); err != nil {
				// If unmarshal fails, initialize empty map
				system.Metadata = make(map[string]any)
			}
		} else {
			system.Metadata = make(map[string]any)
		}

		// Handle nullable fields
		if repositoryID.Valid {
			id := types.FromString(repositoryID.String)
			system.RepositoryID = &id
		}
		if vendor.Valid {
			system.Vendor = vendor.String
		}
		if version.Valid {
			system.Version = version.String
		}
		if host.Valid {
			system.Host = host.String
		}
		if port.Valid {
			val := int(port.Int64)
			system.Port = val
		}
		if protocol.Valid {
			proto := bas.BASProtocol(protocol.String)
			system.Protocol = &proto
		}
		if syncInterval.Valid {
			val := int(syncInterval.Int64)
			system.SyncInterval = &val
		}
		if lastSync.Valid {
			system.LastSync = &lastSync.Time
		}
		if notes.Valid {
			system.Notes = notes.String
		}
		if createdBy.Valid {
			id := types.FromString(createdBy.String)
			system.CreatedBy = &id
		}

		systems = append(systems, system)
	}

	return systems, nil
}

// GetByName retrieves a BAS system by name within a building
func (r *BASSystemRepository) GetByName(buildingID types.ID, name string) (*bas.BASSystem, error) {
	query := `
		SELECT
			id, building_id, repository_id,
			name, system_type, vendor, version,
			host, port, protocol,
			enabled, read_only, sync_interval, last_sync,
			metadata, notes,
			created_at, updated_at, created_by
		FROM bas_systems
		WHERE building_id = $1 AND name = $2
	`

	system := &bas.BASSystem{}
	var repositoryID, createdBy sql.NullString
	var vendor, version, host, protocol, notes sql.NullString
	var port, syncInterval sql.NullInt64
	var lastSync sql.NullTime

	err := r.db.QueryRow(query, buildingID.String(), name).Scan(
		&system.ID, &system.BuildingID, &repositoryID,
		&system.Name, &system.SystemType, &vendor, &version,
		&host, &port, &protocol,
		&system.Enabled, &system.ReadOnly, &syncInterval, &lastSync,
		&system.Metadata, &notes,
		&system.CreatedAt, &system.UpdatedAt, &createdBy,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("BAS system not found")
		}
		return nil, err
	}

	// Handle nullable fields (same logic as GetByID)
	if repositoryID.Valid {
		id := types.FromString(repositoryID.String)
		system.RepositoryID = &id
	}
	if vendor.Valid {
		system.Vendor = vendor.String
	}
	if version.Valid {
		system.Version = version.String
	}
	if host.Valid {
		system.Host = host.String
	}
	if port.Valid {
		val := int(port.Int64)
		system.Port = val
	}
	if protocol.Valid {
		proto := bas.BASProtocol(protocol.String)
		system.Protocol = &proto
	}
	if syncInterval.Valid {
		val := int(syncInterval.Int64)
		system.SyncInterval = &val
	}
	if lastSync.Valid {
		system.LastSync = &lastSync.Time
	}
	if notes.Valid {
		system.Notes = notes.String
	}
	if createdBy.Valid {
		id := types.FromString(createdBy.String)
		system.CreatedBy = &id
	}

	return system, nil
}

// nullableProtocol converts a pointer to BASProtocol to sql.NullString
func nullableProtocol(protocol *bas.BASProtocol) sql.NullString {
	if protocol == nil {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: string(*protocol), Valid: true}
}
