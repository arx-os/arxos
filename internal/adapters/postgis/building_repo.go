package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/google/uuid"
)

// BuildingRepository implements the building.Repository interface using PostGIS
type BuildingRepository struct {
	client *Client
}

// NewBuildingRepository creates a new PostGIS building repository
func NewBuildingRepository(client *Client) *BuildingRepository {
	return &BuildingRepository{client: client}
}

// Create creates a new building in the database
func (r *BuildingRepository) Create(ctx context.Context, b *building.Building) error {
	query := `
		INSERT INTO buildings (id, arxos_id, name, address, origin, rotation, metadata)
		VALUES ($1, $2, $3, $4, ST_SetSRID(ST_MakePoint($5, $6), 4326), $7, $8)
	`

	_, err := r.client.db.ExecContext(ctx, query,
		b.ID, b.ArxosID, b.Name, b.Address,
		b.Origin.Longitude, b.Origin.Latitude,
		b.Rotation, b.Metadata)

	if err != nil {
		return fmt.Errorf("failed to create building: %w", err)
	}

	return nil
}

// GetByID retrieves a building by its UUID
func (r *BuildingRepository) GetByID(ctx context.Context, id uuid.UUID) (*building.Building, error) {
	query := `
		SELECT
			id, arxos_id, name, address,
			ST_X(origin) as lon, ST_Y(origin) as lat,
			rotation, metadata, created_at, updated_at
		FROM buildings
		WHERE id = $1
	`

	var b building.Building
	var lon, lat sql.NullFloat64

	err := r.client.db.QueryRowContext(ctx, query, id).Scan(
		&b.ID, &b.ArxosID, &b.Name, &b.Address,
		&lon, &lat, &b.Rotation, &b.Metadata,
		&b.CreatedAt, &b.UpdatedAt)

	if err == sql.ErrNoRows {
		return nil, building.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	if lon.Valid && lat.Valid {
		b.Origin.Longitude = lon.Float64
		b.Origin.Latitude = lat.Float64
	}

	return &b, nil
}

// GetByArxosID retrieves a building by its ArxOS ID
func (r *BuildingRepository) GetByArxosID(ctx context.Context, arxosID string) (*building.Building, error) {
	query := `
		SELECT
			id, arxos_id, name, address,
			ST_X(origin) as lon, ST_Y(origin) as lat,
			rotation, metadata, created_at, updated_at
		FROM buildings
		WHERE arxos_id = $1
	`

	var b building.Building
	var lon, lat sql.NullFloat64

	err := r.client.db.QueryRowContext(ctx, query, arxosID).Scan(
		&b.ID, &b.ArxosID, &b.Name, &b.Address,
		&lon, &lat, &b.Rotation, &b.Metadata,
		&b.CreatedAt, &b.UpdatedAt)

	if err == sql.ErrNoRows {
		return nil, building.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	if lon.Valid && lat.Valid {
		b.Origin.Longitude = lon.Float64
		b.Origin.Latitude = lat.Float64
	}

	return &b, nil
}

// Update updates an existing building
func (r *BuildingRepository) Update(ctx context.Context, b *building.Building) error {
	query := `
		UPDATE buildings
		SET name = $2, address = $3,
		    origin = ST_SetSRID(ST_MakePoint($4, $5), 4326),
		    rotation = $6, metadata = $7, updated_at = NOW()
		WHERE id = $1
	`

	result, err := r.client.db.ExecContext(ctx, query,
		b.ID, b.Name, b.Address,
		b.Origin.Longitude, b.Origin.Latitude,
		b.Rotation, b.Metadata)

	if err != nil {
		return fmt.Errorf("failed to update building: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return building.ErrNotFound
	}

	return nil
}

// Delete deletes a building by ID
func (r *BuildingRepository) Delete(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM buildings WHERE id = $1`

	result, err := r.client.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete building: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return building.ErrNotFound
	}

	return nil
}

// List retrieves buildings with optional filtering
func (r *BuildingRepository) List(ctx context.Context, filter building.Filter) ([]*building.Building, error) {
	query := `
		SELECT
			id, arxos_id, name, address,
			ST_X(origin) as lon, ST_Y(origin) as lat,
			rotation, metadata, created_at, updated_at
		FROM buildings
		WHERE 1=1
	`

	args := []interface{}{}
	argNum := 1

	// Add filters
	if filter.Name != "" {
		query += fmt.Sprintf(" AND name ILIKE $%d", argNum)
		args = append(args, "%"+filter.Name+"%")
		argNum++
	}

	// Add sorting and pagination
	query += " ORDER BY created_at DESC"

	if filter.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argNum)
		args = append(args, filter.Limit)
		argNum++
	}

	if filter.Offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argNum)
		args = append(args, filter.Offset)
	}

	rows, err := r.client.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list buildings: %w", err)
	}
	defer rows.Close()

	buildings := make([]*building.Building, 0)

	for rows.Next() {
		var b building.Building
		var lon, lat sql.NullFloat64

		err := rows.Scan(
			&b.ID, &b.ArxosID, &b.Name, &b.Address,
			&lon, &lat, &b.Rotation, &b.Metadata,
			&b.CreatedAt, &b.UpdatedAt)

		if err != nil {
			return nil, fmt.Errorf("failed to scan building: %w", err)
		}

		if lon.Valid && lat.Valid {
			b.Origin.Longitude = lon.Float64
			b.Origin.Latitude = lat.Float64
		}

		buildings = append(buildings, &b)
	}

	return buildings, nil
}

// FindNearby finds buildings within a radius of a point (in meters)
func (r *BuildingRepository) FindNearby(ctx context.Context, lon, lat float64, radiusMeters float64) ([]*building.Building, error) {
	query := `
		SELECT
			id, arxos_id, name, address,
			ST_X(origin) as lon, ST_Y(origin) as lat,
			rotation, metadata, created_at, updated_at,
			ST_Distance(origin::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography) as distance
		FROM buildings
		WHERE ST_DWithin(
			origin::geography,
			ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
			$3
		)
		ORDER BY distance ASC
	`

	rows, err := r.client.db.QueryContext(ctx, query, lon, lat, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("failed to find nearby buildings: %w", err)
	}
	defer rows.Close()

	buildings := make([]*building.Building, 0)

	for rows.Next() {
		var b building.Building
		var bLon, bLat sql.NullFloat64
		var distance float64

		err := rows.Scan(
			&b.ID, &b.ArxosID, &b.Name, &b.Address,
			&bLon, &bLat, &b.Rotation, &b.Metadata,
			&b.CreatedAt, &b.UpdatedAt, &distance)

		if err != nil {
			return nil, fmt.Errorf("failed to scan building: %w", err)
		}

		if bLon.Valid && bLat.Valid {
			b.Origin.Longitude = bLon.Float64
			b.Origin.Latitude = bLat.Float64
		}

		buildings = append(buildings, &b)
	}

	return buildings, nil
}
