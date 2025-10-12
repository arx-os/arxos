package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
)

// FloorRepository implements floor repository for PostGIS
type FloorRepository struct {
	db *sql.DB
}

// NewFloorRepository creates a new PostGIS floor repository
func NewFloorRepository(db *sql.DB) *FloorRepository {
	return &FloorRepository{
		db: db,
	}
}

// Create creates a new floor in PostGIS
func (r *FloorRepository) Create(ctx context.Context, f *domain.Floor) error {
	query := `
		INSERT INTO floors (id, building_id, name, level, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`

	_, err := r.db.ExecContext(ctx, query,
		f.ID.String(),
		f.BuildingID.String(),
		f.Name,
		f.Level,
		f.CreatedAt,
		f.UpdatedAt,
	)

	return err
}

// GetByID retrieves a floor by ID
func (r *FloorRepository) GetByID(ctx context.Context, id string) (*domain.Floor, error) {
	query := `
		SELECT id, building_id, name, level, created_at, updated_at
		FROM floors
		WHERE id = $1
	`

	var f domain.Floor

	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&f.ID,
		&f.BuildingID,
		&f.Name,
		&f.Level,
		&f.CreatedAt,
		&f.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("floor not found")
		}
		return nil, err
	}

	return &f, nil
}

// GetByBuilding retrieves all floors for a building
func (r *FloorRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*domain.Floor, error) {
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

// Update updates an existing floor
func (r *FloorRepository) Update(ctx context.Context, f *domain.Floor) error {
	query := `
		UPDATE floors
		SET name = $2, level = $3, updated_at = $4
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		f.ID.String(),
		f.Name,
		f.Level,
		f.UpdatedAt,
	)

	return err
}

// Delete deletes a floor by ID
func (r *FloorRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM floors WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// List retrieves floors with optional filtering
func (r *FloorRepository) List(ctx context.Context, buildingID string, limit, offset int) ([]*domain.Floor, error) {
	query := `
		SELECT id, building_id, name, level, created_at, updated_at
		FROM floors
		WHERE 1=1
	`

	args := []any{}
	argCount := 1

	// Filter by building if provided
	if buildingID != "" {
		query += fmt.Sprintf(" AND building_id = $%d", argCount)
		args = append(args, buildingID)
		argCount++
	}

	query += " ORDER BY level ASC"

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

// GetRooms retrieves all rooms on a floor
func (r *FloorRepository) GetRooms(ctx context.Context, floorID string) ([]*domain.Room, error) {
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

// GetEquipment retrieves all equipment on a floor
func (r *FloorRepository) GetEquipment(ctx context.Context, floorID string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE floor_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, floorID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var equipment []*domain.Equipment

	for rows.Next() {
		var e domain.Equipment
		var roomID sql.NullString
		var locX, locY, locZ sql.NullFloat64

		err := rows.Scan(
			&e.ID,
			&e.BuildingID,
			&e.FloorID,
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
