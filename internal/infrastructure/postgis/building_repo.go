package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
)

// BuildingRepository implements building repository for PostGIS
type BuildingRepository struct {
	db *sql.DB
}

// NewBuildingRepository creates a new PostGIS building repository
func NewBuildingRepository(db *sql.DB) *BuildingRepository {
	return &BuildingRepository{
		db: db,
	}
}

// Create creates a new building in PostGIS
func (r *BuildingRepository) Create(ctx context.Context, b *domain.Building) error {
	query := `
		INSERT INTO buildings (id, name, address, coordinates, created_at, updated_at)
		VALUES ($1, $2, $3, ST_GeomFromText($4, 4326), $5, $6)
	`

	_, err := r.db.ExecContext(ctx, query,
		b.ID,
		b.Name,
		b.Address,
		fmt.Sprintf("POINT(%f %f)", b.Coordinates.X, b.Coordinates.Y),
		b.CreatedAt,
		b.UpdatedAt,
	)

	return err
}

// GetByID retrieves a building by ID
func (r *BuildingRepository) GetByID(ctx context.Context, id string) (*domain.Building, error) {
	query := `
		SELECT id, name, address, ST_AsText(coordinates), created_at, updated_at
		FROM buildings
		WHERE id = $1
	`

	var b domain.Building
	var coordStr string

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&b.ID,
		&b.Name,
		&b.Address,
		&coordStr,
		&b.CreatedAt,
		&b.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("building not found")
		}
		return nil, err
	}

	// Parse coordinates (simplified)
	b.Coordinates = &domain.Location{X: 0, Y: 0} // TODO: Parse PostGIS point

	return &b, nil
}

// Update updates an existing building
func (r *BuildingRepository) Update(ctx context.Context, b *domain.Building) error {
	query := `
		UPDATE buildings
		SET name = $2, address = $3, coordinates = ST_GeomFromText($4, 4326), updated_at = $5
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		b.ID,
		b.Name,
		b.Address,
		fmt.Sprintf("POINT(%f %f)", b.Coordinates.X, b.Coordinates.Y),
		b.UpdatedAt,
	)

	return err
}

// Delete deletes a building by ID
func (r *BuildingRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM buildings WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// List retrieves buildings with optional filtering
func (r *BuildingRepository) List(ctx context.Context, filter *domain.BuildingFilter) ([]*domain.Building, error) {
	query := `
		SELECT id, name, address, ST_AsText(coordinates), created_at, updated_at
		FROM buildings
		ORDER BY created_at DESC
		LIMIT $1 OFFSET $2
	`

	limit := 100
	offset := 0

	if filter != nil {
		if filter.Limit > 0 {
			limit = filter.Limit
		}
		if filter.Offset > 0 {
			offset = filter.Offset
		}
	}

	rows, err := r.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var buildings []*domain.Building

	for rows.Next() {
		var b domain.Building
		var coordStr string

		err := rows.Scan(
			&b.ID,
			&b.Name,
			&b.Address,
			&coordStr,
			&b.CreatedAt,
			&b.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		// Parse coordinates (simplified)
		b.Coordinates = &domain.Location{X: 0, Y: 0} // TODO: Parse PostGIS point

		buildings = append(buildings, &b)
	}

	return buildings, nil
}
