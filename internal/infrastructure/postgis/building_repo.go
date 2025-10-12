package postgis

import (
	"context"
	"database/sql"
	"fmt"
	"regexp"
	"strconv"
	"strings"

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
		INSERT INTO buildings (id, arxos_id, name, address, latitude, longitude, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`

	var lat, lon sql.NullFloat64
	if b.Coordinates != nil {
		lat = sql.NullFloat64{Float64: b.Coordinates.Y, Valid: true}
		lon = sql.NullFloat64{Float64: b.Coordinates.X, Valid: true}
	}

	// Generate arxos_id from building ID
	arxosID := b.ID.String()

	_, err := r.db.ExecContext(ctx, query,
		b.ID.String(),
		arxosID,
		b.Name,
		b.Address,
		lat,
		lon,
		b.CreatedAt,
		b.UpdatedAt,
	)

	return err
}

// GetByID retrieves a building by ID
func (r *BuildingRepository) GetByID(ctx context.Context, id string) (*domain.Building, error) {
	query := `
		SELECT id, name, address, latitude, longitude, created_at, updated_at
		FROM buildings
		WHERE id = $1
	`

	var b domain.Building
	var lat, lon sql.NullFloat64

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&b.ID,
		&b.Name,
		&b.Address,
		&lat,
		&lon,
		&b.CreatedAt,
		&b.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("building not found")
		}
		return nil, err
	}

	// Parse coordinates from lat/lon columns
	if lat.Valid && lon.Valid {
		b.Coordinates = &domain.Location{
			X: lon.Float64, // Longitude is X
			Y: lat.Float64, // Latitude is Y
			Z: 0,
		}
	}

	return &b, nil
}

// Update updates an existing building
func (r *BuildingRepository) Update(ctx context.Context, b *domain.Building) error {
	query := `
		UPDATE buildings
		SET name = $2, address = $3, latitude = $4, longitude = $5, updated_at = $6
		WHERE id = $1
	`

	var lat, lon sql.NullFloat64
	if b.Coordinates != nil {
		lat = sql.NullFloat64{Float64: b.Coordinates.Y, Valid: true}
		lon = sql.NullFloat64{Float64: b.Coordinates.X, Valid: true}
	}

	_, err := r.db.ExecContext(ctx, query,
		b.ID.String(),
		b.Name,
		b.Address,
		lat,
		lon,
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
		SELECT id, name, address, latitude, longitude, created_at, updated_at
		FROM buildings
		WHERE 1=1`

	args := []any{}
	argCount := 1

	// Add filters
	if filter != nil {
		if filter.Name != nil {
			query += fmt.Sprintf(" AND name ILIKE $%d", argCount)
			args = append(args, "%"+*filter.Name+"%")
			argCount++
		}
		if filter.Address != nil {
			query += fmt.Sprintf(" AND address ILIKE $%d", argCount)
			args = append(args, "%"+*filter.Address+"%")
			argCount++
		}
	}

	query += " ORDER BY created_at DESC"

	// Add pagination
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

	query += fmt.Sprintf(" LIMIT $%d OFFSET $%d", argCount, argCount+1)
	args = append(args, limit, offset)

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var buildings []*domain.Building

	for rows.Next() {
		var b domain.Building
		var address sql.NullString
		var lat, lon sql.NullFloat64

		err := rows.Scan(
			&b.ID,
			&b.Name,
			&address,
			&lat,
			&lon,
			&b.CreatedAt,
			&b.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		// Set address if valid
		if address.Valid {
			b.Address = address.String
		}

		// Parse coordinates from lat/lon columns
		if lat.Valid && lon.Valid {
			b.Coordinates = &domain.Location{
				X: lon.Float64,
				Y: lat.Float64,
				Z: 0,
			}
		}

		buildings = append(buildings, &b)
	}

	return buildings, nil
}

// GetByAddress retrieves a building by address
func (r *BuildingRepository) GetByAddress(ctx context.Context, address string) (*domain.Building, error) {
	query := `
		SELECT id, name, address, latitude, longitude, created_at, updated_at
		FROM buildings
		WHERE address = $1
		LIMIT 1
	`

	var b domain.Building
	var lat, lon sql.NullFloat64

	err := r.db.QueryRowContext(ctx, query, address).Scan(
		&b.ID,
		&b.Name,
		&b.Address,
		&lat,
		&lon,
		&b.CreatedAt,
		&b.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("building not found")
		}
		return nil, err
	}

	// Parse coordinates from lat/lon columns
	if lat.Valid && lon.Valid {
		b.Coordinates = &domain.Location{
			X: lon.Float64,
			Y: lat.Float64,
			Z: 0,
		}
	}

	return &b, nil
}

// GetEquipment retrieves all equipment for a building
func (r *BuildingRepository) GetEquipment(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE building_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var equipment []*domain.Equipment

	for rows.Next() {
		var e domain.Equipment
		var floorID, roomID sql.NullString
		var locX, locY, locZ sql.NullFloat64

		err := rows.Scan(
			&e.ID,
			&e.BuildingID,
			&floorID,
			&roomID,
			&e.Name,
			&e.Type,
			&e.Model,
			&locX,
			&locY,
			&locZ,
			&e.Status,
			&e.CreatedAt,
			&e.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		// Set nullable fields
		if floorID.Valid {
			e.FloorID.Legacy = floorID.String
		}
		if roomID.Valid {
			e.RoomID.Legacy = roomID.String
		}

		// Parse location from x/y/z columns
		if locX.Valid && locY.Valid {
			e.Location = &domain.Location{
				X: locX.Float64,
				Y: locY.Float64,
				Z: 0,
			}
			if locZ.Valid {
				e.Location.Z = locZ.Float64
			}
		}

		equipment = append(equipment, &e)
	}

	return equipment, nil
}

// GetFloors retrieves all floors for a building
func (r *BuildingRepository) GetFloors(ctx context.Context, buildingID string) ([]*domain.Floor, error) {
	query := `
		SELECT id, building_id, name, level, created_at, updated_at
		FROM floors
		WHERE building_id = $1
		ORDER BY level ASC
	`

	rows, err := r.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var floors []*domain.Floor

	for rows.Next() {
		var f domain.Floor

		err := rows.Scan(
			&f.ID,
			&f.BuildingID,
			&f.Name,
			&f.Level,
			&f.CreatedAt,
			&f.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		floors = append(floors, &f)
	}

	return floors, nil
}

// parsePoint parses a PostGIS POINT string into a Location
// Format: "POINT(longitude latitude)" or "POINT(x y z)"
func parsePoint(pointStr string) *domain.Location {
	if pointStr == "" {
		return nil
	}

	// Match POINT(x y) or POINT(x y z)
	re := regexp.MustCompile(`POINT\s*\(([^)]+)\)`)
	matches := re.FindStringSubmatch(pointStr)
	if len(matches) < 2 {
		return nil
	}

	coords := strings.Fields(matches[1])
	if len(coords) < 2 {
		return nil
	}

	x, err1 := strconv.ParseFloat(coords[0], 64)
	y, err2 := strconv.ParseFloat(coords[1], 64)

	if err1 != nil || err2 != nil {
		return nil
	}

	loc := &domain.Location{
		X: x,
		Y: y,
		Z: 0,
	}

	// Parse Z coordinate if present
	if len(coords) >= 3 {
		z, err := strconv.ParseFloat(coords[2], 64)
		if err == nil {
			loc.Z = z
		}
	}

	return loc
}
