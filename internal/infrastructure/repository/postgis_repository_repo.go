package repository

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/building"
)

// PostGISRepositoryRepository implements building.RepositoryRepository for PostGIS
type PostGISRepositoryRepository struct {
	db *sql.DB
}

// NewPostGISRepositoryRepository creates a new PostGIS repository repository
func NewPostGISRepositoryRepository(db *sql.DB) building.RepositoryRepository {
	return &PostGISRepositoryRepository{
		db: db,
	}
}

// Create creates a new building repository
func (r *PostGISRepositoryRepository) Create(ctx context.Context, repo *building.BuildingRepository) error {
	query := `
		INSERT INTO building_repositories (
			id, name, type, floors, structure_json, current_version_id, 
			created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`

	// Serialize structure to JSON (simplified for now)
	structureJSON := `{"ifc_files":[],"plans":[],"equipment":[],"operations":{},"integrations":[]}`

	// Handle nil current version
	var currentVersionID interface{}
	if repo.Current != nil {
		currentVersionID = repo.Current.ID
	}

	_, err := r.db.ExecContext(ctx, query,
		repo.ID,
		repo.Name,
		string(repo.Type),
		repo.Floors,
		structureJSON,
		currentVersionID,
		repo.CreatedAt,
		repo.UpdatedAt,
	)

	return err
}

// GetByID retrieves a repository by ID
func (r *PostGISRepositoryRepository) GetByID(ctx context.Context, id string) (*building.BuildingRepository, error) {
	query := `
		SELECT id, name, type, floors, structure_json, current_version_id,
			   created_at, updated_at
		FROM building_repositories
		WHERE id = $1
	`

	var repo building.BuildingRepository
	var typeStr string
	var structureJSON string
	var currentVersionID sql.NullString

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&repo.ID,
		&repo.Name,
		&typeStr,
		&repo.Floors,
		&structureJSON,
		&currentVersionID,
		&repo.CreatedAt,
		&repo.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("repository not found")
		}
		return nil, err
	}

	// Convert type string to BuildingType
	repo.Type = building.BuildingType(typeStr)

	// TODO: Deserialize structure JSON
	// For now, create empty structure
	repo.Structure = building.RepositoryStructure{}

	// Set current version ID if exists
	if currentVersionID.Valid {
		// TODO: Load actual version object
		repo.Current = &building.Version{ID: currentVersionID.String}
	}

	return &repo, nil
}

// GetByName retrieves a repository by name
func (r *PostGISRepositoryRepository) GetByName(ctx context.Context, name string) (*building.BuildingRepository, error) {
	query := `
		SELECT id, name, type, floors, structure_json, current_version_id,
			   created_at, updated_at
		FROM building_repositories
		WHERE name = $1
	`

	var repo building.BuildingRepository
	var typeStr string
	var structureJSON string
	var currentVersionID sql.NullString

	err := r.db.QueryRowContext(ctx, query, name).Scan(
		&repo.ID,
		&repo.Name,
		&typeStr,
		&repo.Floors,
		&structureJSON,
		&currentVersionID,
		&repo.CreatedAt,
		&repo.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("repository not found")
		}
		return nil, err
	}

	// Convert type string to BuildingType
	repo.Type = building.BuildingType(typeStr)

	// TODO: Deserialize structure JSON
	repo.Structure = building.RepositoryStructure{}

	// Set current version ID if exists
	if currentVersionID.Valid {
		repo.Current = &building.Version{ID: currentVersionID.String}
	}

	return &repo, nil
}

// List retrieves all repositories
func (r *PostGISRepositoryRepository) List(ctx context.Context) ([]*building.BuildingRepository, error) {
	query := `
		SELECT id, name, type, floors, structure_json, current_version_id,
			   created_at, updated_at
		FROM building_repositories
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var repos []*building.BuildingRepository
	for rows.Next() {
		var repo building.BuildingRepository
		var typeStr string
		var structureJSON string
		var currentVersionID sql.NullString

		err := rows.Scan(
			&repo.ID,
			&repo.Name,
			&typeStr,
			&repo.Floors,
			&structureJSON,
			&currentVersionID,
			&repo.CreatedAt,
			&repo.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}

		repo.Type = building.BuildingType(typeStr)
		repo.Structure = building.RepositoryStructure{}

		if currentVersionID.Valid {
			repo.Current = &building.Version{ID: currentVersionID.String}
		}

		repos = append(repos, &repo)
	}

	return repos, nil
}

// Update updates an existing repository
func (r *PostGISRepositoryRepository) Update(ctx context.Context, repo *building.BuildingRepository) error {
	query := `
		UPDATE building_repositories
		SET name = $2, type = $3, floors = $4, structure_json = $5,
			current_version_id = $6, updated_at = $7
		WHERE id = $1
	`

	// Serialize structure to JSON (simplified for now)
	structureJSON := `{"ifc_files":[],"plans":[],"equipment":[],"operations":{},"integrations":[]}`

	var currentVersionID sql.NullString
	if repo.Current != nil {
		currentVersionID.String = repo.Current.ID
		currentVersionID.Valid = true
	}

	_, err := r.db.ExecContext(ctx, query,
		repo.ID,
		repo.Name,
		string(repo.Type),
		repo.Floors,
		structureJSON,
		currentVersionID,
		repo.UpdatedAt,
	)

	return err
}

// Delete deletes a repository
func (r *PostGISRepositoryRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM building_repositories WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}
