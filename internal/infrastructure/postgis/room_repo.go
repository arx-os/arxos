package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
)

// RoomRepository implements room repository for PostGIS
type RoomRepository struct {
	db *sql.DB
}

// NewRoomRepository creates a new PostGIS room repository
func NewRoomRepository(db *sql.DB) *RoomRepository {
	return &RoomRepository{
		db: db,
	}
}

// Create creates a new room in PostGIS
func (r *RoomRepository) Create(ctx context.Context, room *domain.Room) error {
	query := `
		INSERT INTO rooms (id, floor_id, name, room_number, width, height, area, geometry, center_point, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
	`

	// Convert location to PostGIS geometry if available
	var geometry any
	var centerPoint any

	if room.Location != nil {
		// Create center point from location
		centerPoint = fmt.Sprintf("POINT(%f %f)", room.Location.X, room.Location.Y)

		// If we have width and height, create a simple rectangular geometry
		if room.Width > 0 && room.Height > 0 {
			halfWidth := room.Width / 2.0
			halfHeight := room.Height / 2.0
			minX := room.Location.X - halfWidth
			maxX := room.Location.X + halfWidth
			minY := room.Location.Y - halfHeight
			maxY := room.Location.Y + halfHeight

			geometry = fmt.Sprintf("POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))",
				minX, minY, maxX, minY, maxX, maxY, minX, maxY, minX, minY)
		}
	}

	// Use nil for zero values to satisfy CHECK constraints
	var width, height, area any
	if room.Width > 0 {
		width = room.Width
		if room.Height > 0 {
			height = room.Height
			area = room.Width * room.Height
		}
	}
	if room.Height > 0 && width == nil {
		height = room.Height
	}

	_, err := r.db.ExecContext(ctx, query,
		room.ID.String(),
		room.FloorID.String(),
		room.Name,
		room.Number,
		width,  // NULL if 0
		height, // NULL if 0
		area,   // NULL if either dimension is 0
		geometry,
		centerPoint,
		room.CreatedAt,
		room.UpdatedAt,
	)

	return err
}

// GetByID retrieves a room by ID
func (r *RoomRepository) GetByID(ctx context.Context, id string) (*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, room_number, width, height, area,
		       ST_X(center_point) as center_x, ST_Y(center_point) as center_y,
		       created_at, updated_at
		FROM rooms
		WHERE id = $1
	`

	var room domain.Room
	var width, height, area sql.NullFloat64
	var centerX, centerY sql.NullFloat64

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&room.ID,
		&room.FloorID,
		&room.Name,
		&room.Number,
		&width,
		&height,
		&area,
		&centerX,
		&centerY,
		&room.CreatedAt,
		&room.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("room not found")
		}
		return nil, err
	}

	// Set geometry fields if they exist
	if width.Valid {
		room.Width = width.Float64
	}
	if height.Valid {
		room.Height = height.Float64
	}
	if centerX.Valid && centerY.Valid {
		room.Location = &domain.Location{
			X: centerX.Float64,
			Y: centerY.Float64,
			Z: 0, // Default Z to 0 for 2D rooms
		}
	}

	return &room, nil
}

// GetByNumber retrieves a room by floor ID and room number
func (r *RoomRepository) GetByNumber(ctx context.Context, floorID, number string) (*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, room_number, width, height, area,
		       ST_X(center_point) as center_x, ST_Y(center_point) as center_y,
		       created_at, updated_at
		FROM rooms
		WHERE floor_id = $1 AND room_number = $2
	`

	var room domain.Room
	var width, height, area sql.NullFloat64
	var centerX, centerY sql.NullFloat64

	err := r.db.QueryRowContext(ctx, query, floorID, number).Scan(
		&room.ID,
		&room.FloorID,
		&room.Name,
		&room.Number,
		&width,
		&height,
		&area,
		&centerX,
		&centerY,
		&room.CreatedAt,
		&room.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, nil // Room not found - return nil without error for duplicate check
	}

	if err != nil {
		return nil, fmt.Errorf("failed to get room by number: %w", err)
	}

	// Set geometry fields if they exist
	if width.Valid {
		room.Width = width.Float64
	}
	if height.Valid {
		room.Height = height.Float64
	}
	if centerX.Valid && centerY.Valid {
		room.Location = &domain.Location{
			X: centerX.Float64,
			Y: centerY.Float64,
			Z: 0,
		}
	}

	return &room, nil
}

// GetByFloor retrieves all rooms on a floor
func (r *RoomRepository) GetByFloor(ctx context.Context, floorID string) ([]*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, room_number, width, height, area,
		       ST_X(center_point) as center_x, ST_Y(center_point) as center_y,
		       created_at, updated_at
		FROM rooms
		WHERE floor_id = $1
		ORDER BY room_number ASC
	`

	rows, err := r.db.QueryContext(ctx, query, floorID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var rooms []*domain.Room

	for rows.Next() {
		var room domain.Room
		var width, height, area sql.NullFloat64
		var centerX, centerY sql.NullFloat64

		err := rows.Scan(
			&room.ID,
			&room.FloorID,
			&room.Name,
			&room.Number,
			&width,
			&height,
			&area,
			&centerX,
			&centerY,
			&room.CreatedAt,
			&room.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		// Set geometry fields if they exist
		if width.Valid {
			room.Width = width.Float64
		}
		if height.Valid {
			room.Height = height.Float64
		}
		if centerX.Valid && centerY.Valid {
			room.Location = &domain.Location{
				X: centerX.Float64,
				Y: centerY.Float64,
				Z: 0,
			}
		}

		rooms = append(rooms, &room)
	}

	return rooms, nil
}

// GetByNumber retrieves a room by floor and room number
// List retrieves rooms with optional filtering
func (r *RoomRepository) List(ctx context.Context, floorID string, limit, offset int) ([]*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, room_number, created_at, updated_at
		FROM rooms
		WHERE 1=1
	`

	args := []any{}
	argCount := 1

	// Filter by floor if provided
	if floorID != "" {
		query += fmt.Sprintf(" AND floor_id = $%d", argCount)
		args = append(args, floorID)
		argCount++
	}

	query += " ORDER BY room_number ASC"

	// Add pagination
	if limit <= 0 {
		limit = 100
	}
	query += fmt.Sprintf(" LIMIT $%d OFFSET $%d", argCount, argCount+1)
	args = append(args, limit, offset)

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var rooms []*domain.Room

	for rows.Next() {
		var room domain.Room

		err := rows.Scan(
			&room.ID,
			&room.FloorID,
			&room.Name,
			&room.Number,
			&room.CreatedAt,
			&room.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		rooms = append(rooms, &room)
	}

	return rooms, nil
}

// Update updates an existing room
func (r *RoomRepository) Update(ctx context.Context, room *domain.Room) error {
	query := `
		UPDATE rooms
		SET name = $2, room_number = $3, updated_at = $4
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		room.ID.String(),
		room.Name,
		room.Number,
		room.UpdatedAt,
	)

	return err
}

// Delete deletes a room by ID
func (r *RoomRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM rooms WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// GetEquipment retrieves all equipment in a room
func (r *RoomRepository) GetEquipment(ctx context.Context, roomID string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE room_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, roomID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var equipment []*domain.Equipment

	for rows.Next() {
		var e domain.Equipment
		var locX, locY, locZ sql.NullFloat64

		err := rows.Scan(
			&e.ID,
			&e.BuildingID,
			&e.FloorID,
			&e.RoomID,
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

// GetRoomsInBounds retrieves rooms within a bounding box
func (r *RoomRepository) GetRoomsInBounds(ctx context.Context, minX, minY, maxX, maxY float64) ([]*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, room_number, width, height, area,
		       ST_X(center_point) as center_x, ST_Y(center_point) as center_y,
		       created_at, updated_at
		FROM rooms
		WHERE geometry && ST_MakeEnvelope($1, $2, $3, $4, 4326)
		ORDER BY room_number ASC
	`

	rows, err := r.db.QueryContext(ctx, query, minX, minY, maxX, maxY)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanRoomRows(rows)
}

// GetRoomsNearPoint retrieves rooms within a radius of a point
func (r *RoomRepository) GetRoomsNearPoint(ctx context.Context, x, y, radiusMeters float64) ([]*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, room_number, width, height, area,
		       ST_X(center_point) as center_x, ST_Y(center_point) as center_y,
		       created_at, updated_at
		FROM rooms
		WHERE ST_DWithin(
			center_point::geography,
			ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
			$3
		)
		ORDER BY ST_Distance(center_point::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography)
	`

	rows, err := r.db.QueryContext(ctx, query, x, y, radiusMeters)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanRoomRows(rows)
}

// GetRoomGeometry retrieves room geometry as GeoJSON
func (r *RoomRepository) GetRoomGeometry(ctx context.Context, roomID string) (string, error) {
	query := `
		SELECT ST_AsGeoJSON(geometry) as geojson
		FROM rooms
		WHERE id = $1 AND geometry IS NOT NULL
	`

	var geojson string
	err := r.db.QueryRowContext(ctx, query, roomID).Scan(&geojson)
	if err != nil {
		if err == sql.ErrNoRows {
			return "", fmt.Errorf("room geometry not found")
		}
		return "", err
	}

	return geojson, nil
}

// scanRoomRows is a helper function to scan room rows with geometry data
func (r *RoomRepository) scanRoomRows(rows *sql.Rows) ([]*domain.Room, error) {
	var rooms []*domain.Room

	for rows.Next() {
		var room domain.Room
		var width, height, area sql.NullFloat64
		var centerX, centerY sql.NullFloat64

		err := rows.Scan(
			&room.ID,
			&room.FloorID,
			&room.Name,
			&room.Number,
			&width,
			&height,
			&area,
			&centerX,
			&centerY,
			&room.CreatedAt,
			&room.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		// Set geometry fields if they exist
		if width.Valid {
			room.Width = width.Float64
		}
		if height.Valid {
			room.Height = height.Float64
		}
		if centerX.Valid && centerY.Valid {
			room.Location = &domain.Location{
				X: centerX.Float64,
				Y: centerY.Float64,
				Z: 0,
			}
		}

		rooms = append(rooms, &room)
	}

	return rooms, nil
}
