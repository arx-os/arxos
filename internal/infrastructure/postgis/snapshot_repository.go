package postgis

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"
)

// SnapshotRepository implements building.SnapshotRepository using PostgreSQL
type SnapshotRepository struct {
	db *sqlx.DB
}

// NewSnapshotRepository creates a new PostgreSQL-backed snapshot repository
func NewSnapshotRepository(db *sqlx.DB) *SnapshotRepository {
	return &SnapshotRepository{
		db: db,
	}
}

// Create creates a new snapshot
func (r *SnapshotRepository) Create(ctxAny any, snapshot *building.Snapshot) error {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return fmt.Errorf("invalid context type")
	}

	// Calculate hash if not already set
	if snapshot.Hash == "" {
		snapshot.Hash = building.CalculateSnapshotHash(snapshot)
	}

	// Set creation time if not set
	if snapshot.CreatedAt.IsZero() {
		snapshot.CreatedAt = time.Now()
	}

	// Serialize metadata to JSON
	metadataJSON, err := building.SerializeObject(snapshot.Metadata)
	if err != nil {
		return fmt.Errorf("failed to serialize metadata: %w", err)
	}

	query := `
		INSERT INTO version_snapshots (
			hash, repository_id, building_tree, equipment_tree,
			spatial_tree, files_tree, operations_tree, metadata, created_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		ON CONFLICT (hash) DO NOTHING
	`

	_, err = r.db.ExecContext(ctx, query,
		snapshot.Hash,
		snapshot.RepositoryID,
		snapshot.BuildingTree,
		snapshot.EquipmentTree,
		snapshot.SpatialTree,
		snapshot.FilesTree,
		snapshot.OperationsTree,
		metadataJSON,
		snapshot.CreatedAt,
	)

	if err != nil {
		// Check for foreign key violations
		if pqErr, ok := err.(*pq.Error); ok {
			if pqErr.Code == "23503" { // Foreign key violation
				return fmt.Errorf("referenced object not found: %w", err)
			}
		}
		return fmt.Errorf("failed to create snapshot: %w", err)
	}

	return nil
}

// GetByHash retrieves a snapshot by its hash
func (r *SnapshotRepository) GetByHash(ctxAny any, hash string) (*building.Snapshot, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return nil, fmt.Errorf("invalid context type")
	}

	query := `
		SELECT hash, repository_id, building_tree, equipment_tree,
		       spatial_tree, files_tree, operations_tree, metadata, created_at
		FROM version_snapshots
		WHERE hash = $1
	`

	var snapshot building.Snapshot
	var metadataJSON []byte

	err := r.db.QueryRowContext(ctx, query, hash).Scan(
		&snapshot.Hash,
		&snapshot.RepositoryID,
		&snapshot.BuildingTree,
		&snapshot.EquipmentTree,
		&snapshot.SpatialTree,
		&snapshot.FilesTree,
		&snapshot.OperationsTree,
		&metadataJSON,
		&snapshot.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("snapshot not found: %s", hash)
	}
	if err != nil {
		return nil, fmt.Errorf("failed to load snapshot: %w", err)
	}

	// Deserialize metadata
	if err := building.DeserializeObject(metadataJSON, &snapshot.Metadata); err != nil {
		return nil, fmt.Errorf("failed to deserialize metadata: %w", err)
	}

	return &snapshot, nil
}

// ListByRepository lists all snapshots for a repository
func (r *SnapshotRepository) ListByRepository(ctxAny any, repoID string) ([]*building.Snapshot, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return nil, fmt.Errorf("invalid context type")
	}

	query := `
		SELECT hash, repository_id, building_tree, equipment_tree,
		       spatial_tree, files_tree, operations_tree, metadata, created_at
		FROM version_snapshots
		WHERE repository_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, repoID)
	if err != nil {
		return nil, fmt.Errorf("failed to list snapshots: %w", err)
	}
	defer rows.Close()

	var snapshots []*building.Snapshot
	for rows.Next() {
		var snapshot building.Snapshot
		var metadataJSON []byte

		err := rows.Scan(
			&snapshot.Hash,
			&snapshot.RepositoryID,
			&snapshot.BuildingTree,
			&snapshot.EquipmentTree,
			&snapshot.SpatialTree,
			&snapshot.FilesTree,
			&snapshot.OperationsTree,
			&metadataJSON,
			&snapshot.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan snapshot: %w", err)
		}

		// Deserialize metadata
		if err := building.DeserializeObject(metadataJSON, &snapshot.Metadata); err != nil {
			return nil, fmt.Errorf("failed to deserialize metadata: %w", err)
		}

		snapshots = append(snapshots, &snapshot)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating snapshots: %w", err)
	}

	return snapshots, nil
}

// GetLatest gets the latest snapshot for a repository
func (r *SnapshotRepository) GetLatest(ctxAny any, repoID string) (*building.Snapshot, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return nil, fmt.Errorf("invalid context type")
	}

	query := `
		SELECT hash, repository_id, building_tree, equipment_tree,
		       spatial_tree, files_tree, operations_tree, metadata, created_at
		FROM version_snapshots
		WHERE repository_id = $1
		ORDER BY created_at DESC
		LIMIT 1
	`

	var snapshot building.Snapshot
	var metadataJSON []byte

	err := r.db.QueryRowContext(ctx, query, repoID).Scan(
		&snapshot.Hash,
		&snapshot.RepositoryID,
		&snapshot.BuildingTree,
		&snapshot.EquipmentTree,
		&snapshot.SpatialTree,
		&snapshot.FilesTree,
		&snapshot.OperationsTree,
		&metadataJSON,
		&snapshot.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("no snapshots found for repository: %s", repoID)
	}
	if err != nil {
		return nil, fmt.Errorf("failed to load latest snapshot: %w", err)
	}

	// Deserialize metadata
	if err := building.DeserializeObject(metadataJSON, &snapshot.Metadata); err != nil {
		return nil, fmt.Errorf("failed to deserialize metadata: %w", err)
	}

	return &snapshot, nil
}

// Delete deletes a snapshot
func (r *SnapshotRepository) Delete(ctxAny any, hash string) error {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return fmt.Errorf("invalid context type")
	}

	query := `DELETE FROM version_snapshots WHERE hash = $1`

	result, err := r.db.ExecContext(ctx, query, hash)
	if err != nil {
		return fmt.Errorf("failed to delete snapshot: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("snapshot not found: %s", hash)
	}

	return nil
}
