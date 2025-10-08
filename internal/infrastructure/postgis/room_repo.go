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
		INSERT INTO rooms (id, floor_id, name, number, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`

	_, err := r.db.ExecContext(ctx, query,
		room.ID.String(),
		room.FloorID.String(),
		room.Name,
		room.Number,
		room.CreatedAt,
		room.UpdatedAt,
	)

	return err
}

// GetByID retrieves a room by ID
func (r *RoomRepository) GetByID(ctx context.Context, id string) (*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, number, created_at, updated_at
		FROM rooms
		WHERE id = $1
	`

	var room domain.Room

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&room.ID,
		&room.FloorID,
		&room.Name,
		&room.Number,
		&room.CreatedAt,
		&room.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("room not found")
		}
		return nil, err
	}

	return &room, nil
}

// GetByFloor retrieves all rooms on a floor
func (r *RoomRepository) GetByFloor(ctx context.Context, floorID string) ([]*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, number, created_at, updated_at
		FROM rooms
		WHERE floor_id = $1
		ORDER BY number ASC
	`

	rows, err := r.db.QueryContext(ctx, query, floorID)
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

// GetByNumber retrieves a room by floor and room number
func (r *RoomRepository) GetByNumber(ctx context.Context, floorID, number string) (*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, number, created_at, updated_at
		FROM rooms
		WHERE floor_id = $1 AND number = $2
		LIMIT 1
	`

	var room domain.Room

	err := r.db.QueryRowContext(ctx, query, floorID, number).Scan(
		&room.ID,
		&room.FloorID,
		&room.Name,
		&room.Number,
		&room.CreatedAt,
		&room.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("room not found")
		}
		return nil, err
	}

	return &room, nil
}

// Update updates an existing room
func (r *RoomRepository) Update(ctx context.Context, room *domain.Room) error {
	query := `
		UPDATE rooms
		SET name = $2, number = $3, updated_at = $4
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

// List retrieves rooms with optional filtering
func (r *RoomRepository) List(ctx context.Context, floorID string, limit, offset int) ([]*domain.Room, error) {
	query := `
		SELECT id, floor_id, name, number, created_at, updated_at
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

	query += " ORDER BY number ASC"

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

// GetEquipment retrieves all equipment in a room
func (r *RoomRepository) GetEquipment(ctx context.Context, roomID string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, type, model,
		       ST_AsText(location), status, created_at, updated_at
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
		var locStr sql.NullString

		err := rows.Scan(
			&e.ID,
			&e.BuildingID,
			&e.FloorID,
			&e.RoomID,
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

		// Parse location from PostGIS POINT
		if locStr.Valid {
			e.Location = parsePoint(locStr.String)
		}

		equipment = append(equipment, &e)
	}

	return equipment, nil
}
