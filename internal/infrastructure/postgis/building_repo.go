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
		INSERT INTO buildings (id, name, address, coordinates, created_at, updated_at)
		VALUES ($1, $2, $3, ST_GeomFromText($4, 4326), $5, $6)
	`

	var coordStr string
	if b.Coordinates != nil {
		coordStr = fmt.Sprintf("POINT(%f %f)", b.Coordinates.X, b.Coordinates.Y)
	}

	_, err := r.db.ExecContext(ctx, query,
		b.ID.String(),
		b.Name,
		b.Address,
		coordStr,
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
	var coordStr sql.NullString

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

	// Parse coordinates from PostGIS POINT
	if coordStr.Valid {
		b.Coordinates = parsePoint(coordStr.String)
	}

	return &b, nil
}

// Update updates an existing building
func (r *BuildingRepository) Update(ctx context.Context, b *domain.Building) error {
	query := `
		UPDATE buildings
		SET name = $2, address = $3, coordinates = ST_GeomFromText($4, 4326), updated_at = $5
		WHERE id = $1
	`

	var coordStr string
	if b.Coordinates != nil {
		coordStr = fmt.Sprintf("POINT(%f %f)", b.Coordinates.X, b.Coordinates.Y)
	}

	_, err := r.db.ExecContext(ctx, query,
		b.ID.String(),
		b.Name,
		b.Address,
		coordStr,
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
		var coordStr sql.NullString

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

		// Parse coordinates from PostGIS POINT
		if coordStr.Valid {
			b.Coordinates = parsePoint(coordStr.String)
		}

		buildings = append(buildings, &b)
	}

	return buildings, nil
}

// GetByAddress retrieves a building by address
func (r *BuildingRepository) GetByAddress(ctx context.Context, address string) (*domain.Building, error) {
	query := `
		SELECT id, name, address, ST_AsText(coordinates), created_at, updated_at
		FROM buildings
		WHERE address = $1
		LIMIT 1
	`

	var b domain.Building
	var coordStr sql.NullString

	err := r.db.QueryRowContext(ctx, query, address).Scan(
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

	// Parse coordinates from PostGIS POINT
	if coordStr.Valid {
		b.Coordinates = parsePoint(coordStr.String)
	}

	return &b, nil
}

// GetEquipment retrieves all equipment for a building
func (r *BuildingRepository) GetEquipment(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, type, model,
		       ST_AsText(location), status, created_at, updated_at
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
		var locStr sql.NullString
		var floorID, roomID sql.NullString

		err := rows.Scan(
			&e.ID,
			&e.BuildingID,
			&floorID,
			&roomID,
			&e.Name,
			&e.Type,
			&e.Model,
			&locStr,
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

		// Parse location from PostGIS POINT
		if locStr.Valid {
			e.Location = parsePoint(locStr.String)
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
