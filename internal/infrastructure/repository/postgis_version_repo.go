package repository

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/building"
)

// PostGISVersionRepository implements building.VersionRepository for PostGIS
type PostGISVersionRepository struct {
	db *sql.DB
}

// NewPostGISVersionRepository creates a new PostGIS version repository
func NewPostGISVersionRepository(db *sql.DB) building.VersionRepository {
	return &PostGISVersionRepository{
		db: db,
	}
}

// Create creates a new version
func (r *PostGISVersionRepository) Create(ctx context.Context, version *building.Version) error {
	query := `
		INSERT INTO building_versions (
			id, repository_id, tag, message, author, hash, parent_id,
			changes_json, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	// Serialize changes to JSON (simplified for now)
	changesJSON := `[]`

	var parentID sql.NullString
	if version.Parent != "" {
		parentID.String = version.Parent
		parentID.Valid = true
	}

	_, err := r.db.ExecContext(ctx, query,
		version.ID,
		version.RepositoryID,
		version.Tag,
		version.Message,
		version.Author,
		version.Hash,
		parentID,
		changesJSON,
		version.CreatedAt,
	)

	return err
}

// GetByID retrieves a version by ID
func (r *PostGISVersionRepository) GetByID(ctx context.Context, id string) (*building.Version, error) {
	query := `
		SELECT id, repository_id, tag, message, author, hash, parent_id,
			   changes_json, created_at
		FROM building_versions
		WHERE id = $1
	`

	var version building.Version
	var parentID sql.NullString
	var changesJSON string

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&version.ID,
		&version.RepositoryID,
		&version.Tag,
		&version.Message,
		&version.Author,
		&version.Hash,
		&parentID,
		&changesJSON,
		&version.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("version not found")
		}
		return nil, err
	}

	if parentID.Valid {
		version.Parent = parentID.String
	}

	// TODO: Deserialize changes JSON
	version.Changes = []building.Change{}

	return &version, nil
}

// GetByRepositoryAndTag retrieves a version by repository ID and tag
func (r *PostGISVersionRepository) GetByRepositoryAndTag(ctx context.Context, repoID, tag string) (*building.Version, error) {
	query := `
		SELECT id, repository_id, tag, message, author, hash, parent_id,
			   changes_json, created_at
		FROM building_versions
		WHERE repository_id = $1 AND tag = $2
	`

	var version building.Version
	var parentID sql.NullString
	var changesJSON string

	err := r.db.QueryRowContext(ctx, query, repoID, tag).Scan(
		&version.ID,
		&version.RepositoryID,
		&version.Tag,
		&version.Message,
		&version.Author,
		&version.Hash,
		&parentID,
		&changesJSON,
		&version.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("version not found")
		}
		return nil, err
	}

	if parentID.Valid {
		version.Parent = parentID.String
	}

	// TODO: Deserialize changes JSON
	version.Changes = []building.Change{}

	return &version, nil
}

// ListByRepository retrieves all versions for a repository
func (r *PostGISVersionRepository) ListByRepository(ctx context.Context, repoID string) ([]building.Version, error) {
	query := `
		SELECT id, repository_id, tag, message, author, hash, parent_id,
			   changes_json, created_at
		FROM building_versions
		WHERE repository_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, repoID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var versions []building.Version
	for rows.Next() {
		var version building.Version
		var parentID sql.NullString
		var changesJSON string

		err := rows.Scan(
			&version.ID,
			&version.RepositoryID,
			&version.Tag,
			&version.Message,
			&version.Author,
			&version.Hash,
			&parentID,
			&changesJSON,
			&version.CreatedAt,
		)
		if err != nil {
			return nil, err
		}

		if parentID.Valid {
			version.Parent = parentID.String
		}

		// TODO: Deserialize changes JSON
		version.Changes = []building.Change{}

		versions = append(versions, version)
	}

	return versions, nil
}

// GetLatest retrieves the latest version for a repository
func (r *PostGISVersionRepository) GetLatest(ctx context.Context, repoID string) (*building.Version, error) {
	query := `
		SELECT id, repository_id, tag, message, author, hash, parent_id,
			   changes_json, created_at
		FROM building_versions
		WHERE repository_id = $1
		ORDER BY created_at DESC
		LIMIT 1
	`

	var version building.Version
	var parentID sql.NullString
	var changesJSON string

	err := r.db.QueryRowContext(ctx, query, repoID).Scan(
		&version.ID,
		&version.RepositoryID,
		&version.Tag,
		&version.Message,
		&version.Author,
		&version.Hash,
		&parentID,
		&changesJSON,
		&version.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("no versions found")
		}
		return nil, err
	}

	if parentID.Valid {
		version.Parent = parentID.String
	}

	// TODO: Deserialize changes JSON
	version.Changes = []building.Change{}

	return &version, nil
}

// Update updates an existing version
func (r *PostGISVersionRepository) Update(ctx context.Context, version *building.Version) error {
	query := `
		UPDATE building_versions
		SET tag = $2, message = $3, author = $4, hash = $5, parent_id = $6,
			changes_json = $7
		WHERE id = $1
	`

	// Serialize changes to JSON (simplified for now)
	changesJSON := `[]`

	var parentID sql.NullString
	if version.Parent != "" {
		parentID.String = version.Parent
		parentID.Valid = true
	}

	_, err := r.db.ExecContext(ctx, query,
		version.ID,
		version.Tag,
		version.Message,
		version.Author,
		version.Hash,
		parentID,
		changesJSON,
	)

	return err
}

// Delete deletes a version
func (r *PostGISVersionRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM building_versions WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}
