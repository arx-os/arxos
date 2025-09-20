package database

import (
	"context"
	"time"

	"github.com/arx-os/arxos/pkg/models"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
)

// ExtendedDB extends the base DB interface with additional operations
type ExtendedDB interface {
	DB

	// User list operations
	ListUsers(ctx context.Context, limit, offset int) ([]*models.User, error)

	// Change tracking operations
	GetEntityVersion(ctx context.Context, entityType, entityID string) (int, error)
	ApplyChange(ctx context.Context, change *syncpkg.Change) error
	GetChangesSince(ctx context.Context, since time.Time, entityType string) ([]*syncpkg.Change, error)

	// Conflict management operations
	GetPendingConflicts(ctx context.Context, buildingID string) ([]*syncpkg.Conflict, error)
	SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error
	ResolveConflict(ctx context.Context, conflictID string, resolution string) error

	// Sync status operations
	GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error)
	UpdateLastSyncTime(ctx context.Context, buildingID string, syncTime time.Time) error
	GetPendingChangesCount(ctx context.Context, buildingID string) (int, error)
	GetConflictCount(ctx context.Context, buildingID string) (int, error)
}

// ExtendedOperations provides default implementations for extended operations
type ExtendedOperations struct {
	DB
}

// NewExtendedDB wraps a DB with extended operations
func NewExtendedDB(db DB) ExtendedDB {
	return &ExtendedOperations{DB: db}
}

// ListUsers returns a paginated list of users
func (e *ExtendedOperations) ListUsers(ctx context.Context, limit, offset int) ([]*models.User, error) {
	query := `
		SELECT id, email, username, full_name, role, is_active,
		       email_verified, phone, avatar_url, last_login,
		       created_at, updated_at
		FROM users
		ORDER BY created_at DESC
		LIMIT $1 OFFSET $2
	`

	rows, err := e.Query(ctx, query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []*models.User
	for rows.Next() {
		user := &models.User{}
		err := rows.Scan(
			&user.ID, &user.Email, &user.Username, &user.FullName,
			&user.Role, &user.IsActive, &user.EmailVerified,
			&user.Phone, &user.AvatarURL, &user.LastLogin,
			&user.CreatedAt, &user.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		users = append(users, user)
	}

	return users, rows.Err()
}

// GetEntityVersion returns the current version of an entity
func (e *ExtendedOperations) GetEntityVersion(ctx context.Context, entityType, entityID string) (int, error) {
	query := `
		SELECT version FROM entity_versions
		WHERE entity_type = $1 AND entity_id = $2
	`

	var version int
	row := e.QueryRow(ctx, query, entityType, entityID)
	err := row.Scan(&version)
	if err != nil {
		// If no version exists, return 0
		return 0, nil
	}

	return version, nil
}

// ApplyChange applies a change to the database
func (e *ExtendedOperations) ApplyChange(ctx context.Context, change *syncpkg.Change) error {
	// Begin transaction
	tx, err := e.BeginTx(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Record the change in change log
	_, err = tx.ExecContext(ctx, `
		INSERT INTO change_log (id, type, entity, entity_id, timestamp, data, version)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`, change.ID, change.Type, change.Entity, change.EntityID,
		change.Timestamp, change.Data, change.Version)
	if err != nil {
		return err
	}

	// Update entity version
	_, err = tx.ExecContext(ctx, `
		INSERT INTO entity_versions (entity_type, entity_id, version, updated_at)
		VALUES ($1, $2, $3, $4)
		ON CONFLICT (entity_type, entity_id)
		DO UPDATE SET version = $3, updated_at = $4
	`, change.Entity, change.EntityID, change.Version, time.Now())
	if err != nil {
		return err
	}

	return tx.Commit()
}

// GetChangesSince retrieves changes since a given timestamp
func (e *ExtendedOperations) GetChangesSince(ctx context.Context, since time.Time, entityType string) ([]*syncpkg.Change, error) {
	query := `
		SELECT id, type, entity, entity_id, timestamp, data, version
		FROM change_log
		WHERE timestamp > $1
	`
	args := []interface{}{since}

	if entityType != "" {
		query += " AND entity = $2"
		args = append(args, entityType)
	}

	query += " ORDER BY timestamp ASC"

	rows, err := e.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var changes []*syncpkg.Change
	for rows.Next() {
		change := &syncpkg.Change{}
		err := rows.Scan(
			&change.ID, &change.Type, &change.Entity,
			&change.EntityID, &change.Timestamp, &change.Data,
			&change.Version,
		)
		if err != nil {
			return nil, err
		}
		changes = append(changes, change)
	}

	return changes, rows.Err()
}

// GetPendingConflicts retrieves pending conflicts for a building
func (e *ExtendedOperations) GetPendingConflicts(ctx context.Context, buildingID string) ([]*syncpkg.Conflict, error) {
	query := `
		SELECT id, entity, entity_id, conflict_type, local_version,
		       remote_version, local_data, remote_data, created_at
		FROM conflicts
		WHERE building_id = $1 AND resolved = false
		ORDER BY created_at DESC
	`

	rows, err := e.Query(ctx, query, buildingID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var conflicts []*syncpkg.Conflict
	for rows.Next() {
		conflict := &syncpkg.Conflict{}
		err := rows.Scan(
			&conflict.ID, &conflict.Entity, &conflict.EntityID,
			&conflict.ConflictType, &conflict.LocalVersion,
			&conflict.RemoteVersion, &conflict.LocalData,
			&conflict.RemoteData, &conflict.CreatedAt,
		)
		if err != nil {
			return nil, err
		}
		conflicts = append(conflicts, conflict)
	}

	return conflicts, rows.Err()
}

// SaveConflict saves a conflict to the database
func (e *ExtendedOperations) SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error {
	query := `
		INSERT INTO conflicts (
			id, entity, entity_id, conflict_type,
			local_version, remote_version,
			local_data, remote_data, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	_, err := e.Exec(ctx, query,
		conflict.ID, conflict.Entity, conflict.EntityID,
		conflict.ConflictType, conflict.LocalVersion,
		conflict.RemoteVersion, conflict.LocalData,
		conflict.RemoteData, time.Now(),
	)

	return err
}

// ResolveConflict marks a conflict as resolved
func (e *ExtendedOperations) ResolveConflict(ctx context.Context, conflictID string, resolution string) error {
	query := `
		UPDATE conflicts
		SET resolved = true, resolution = $2, resolved_at = $3
		WHERE id = $1
	`

	_, err := e.Exec(ctx, query, conflictID, resolution, time.Now())
	return err
}

// GetLastSyncTime returns the last sync time for a building
func (e *ExtendedOperations) GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error) {
	query := `
		SELECT last_sync FROM sync_status
		WHERE building_id = $1
	`

	var lastSync time.Time
	row := e.QueryRow(ctx, query, buildingID)
	err := row.Scan(&lastSync)
	if err != nil {
		// If no sync status exists, return zero time
		return time.Time{}, nil
	}

	return lastSync, nil
}

// UpdateLastSyncTime updates the last sync time for a building
func (e *ExtendedOperations) UpdateLastSyncTime(ctx context.Context, buildingID string, syncTime time.Time) error {
	query := `
		INSERT INTO sync_status (building_id, last_sync, updated_at)
		VALUES ($1, $2, $3)
		ON CONFLICT (building_id)
		DO UPDATE SET last_sync = $2, updated_at = $3
	`

	_, err := e.Exec(ctx, query, buildingID, syncTime, time.Now())
	return err
}

// GetPendingChangesCount returns the count of pending changes
func (e *ExtendedOperations) GetPendingChangesCount(ctx context.Context, buildingID string) (int, error) {
	query := `
		SELECT COUNT(*) FROM change_log
		WHERE building_id = $1 AND synced = false
	`

	var count int
	row := e.QueryRow(ctx, query, buildingID)
	err := row.Scan(&count)

	return count, err
}

// GetConflictCount returns the count of unresolved conflicts
func (e *ExtendedOperations) GetConflictCount(ctx context.Context, buildingID string) (int, error) {
	query := `
		SELECT COUNT(*) FROM conflicts
		WHERE building_id = $1 AND resolved = false
	`

	var count int
	row := e.QueryRow(ctx, query, buildingID)
	err := row.Scan(&count)

	return count, err
}