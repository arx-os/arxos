package repository

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/building"
)

// PostGISIFCRepository implements building.IFCRepository for PostGIS
type PostGISIFCRepository struct {
	db *sql.DB
}

// NewPostGISIFCRepository creates a new PostGIS IFC repository
func NewPostGISIFCRepository(db *sql.DB) building.IFCRepository {
	return &PostGISIFCRepository{
		db: db,
	}
}

// Create creates a new IFC file record
func (r *PostGISIFCRepository) Create(ctx context.Context, ifcFile *building.IFCFile) error {
	query := `
		INSERT INTO ifc_files (
			id, name, path, version, discipline, size, entities,
			validated, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
	`

	_, err := r.db.ExecContext(ctx, query,
		ifcFile.ID,
		ifcFile.Name,
		ifcFile.Path,
		ifcFile.Version,
		ifcFile.Discipline,
		ifcFile.Size,
		ifcFile.Entities,
		ifcFile.Validated,
		ifcFile.CreatedAt,
		ifcFile.UpdatedAt,
	)

	return err
}

// GetByID retrieves an IFC file by ID
func (r *PostGISIFCRepository) GetByID(ctx context.Context, id string) (*building.IFCFile, error) {
	query := `
		SELECT id, name, path, version, discipline, size, entities,
			   validated, created_at, updated_at
		FROM ifc_files
		WHERE id = $1
	`

	var ifcFile building.IFCFile

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&ifcFile.ID,
		&ifcFile.Name,
		&ifcFile.Path,
		&ifcFile.Version,
		&ifcFile.Discipline,
		&ifcFile.Size,
		&ifcFile.Entities,
		&ifcFile.Validated,
		&ifcFile.CreatedAt,
		&ifcFile.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("IFC file not found")
		}
		return nil, err
	}

	return &ifcFile, nil
}

// GetByRepository retrieves all IFC files for a repository
func (r *PostGISIFCRepository) GetByRepository(ctx context.Context, repoID string) ([]building.IFCFile, error) {
	query := `
		SELECT id, name, path, version, discipline, size, entities,
			   validated, created_at, updated_at
		FROM ifc_files
		WHERE repository_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, repoID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var ifcFiles []building.IFCFile
	for rows.Next() {
		var ifcFile building.IFCFile

		err := rows.Scan(
			&ifcFile.ID,
			&ifcFile.Name,
			&ifcFile.Path,
			&ifcFile.Version,
			&ifcFile.Discipline,
			&ifcFile.Size,
			&ifcFile.Entities,
			&ifcFile.Validated,
			&ifcFile.CreatedAt,
			&ifcFile.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}

		ifcFiles = append(ifcFiles, ifcFile)
	}

	return ifcFiles, nil
}

// Update updates an existing IFC file
func (r *PostGISIFCRepository) Update(ctx context.Context, ifcFile *building.IFCFile) error {
	query := `
		UPDATE ifc_files
		SET name = $2, path = $3, version = $4, discipline = $5,
			size = $6, entities = $7, validated = $8, updated_at = $9
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		ifcFile.ID,
		ifcFile.Name,
		ifcFile.Path,
		ifcFile.Version,
		ifcFile.Discipline,
		ifcFile.Size,
		ifcFile.Entities,
		ifcFile.Validated,
		ifcFile.UpdatedAt,
	)

	return err
}

// Delete deletes an IFC file
func (r *PostGISIFCRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM ifc_files WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}
