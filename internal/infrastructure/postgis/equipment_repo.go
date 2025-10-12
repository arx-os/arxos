package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
)

// EquipmentRepository implements equipment repository for PostGIS
type EquipmentRepository struct {
	db *sql.DB
}

// NewEquipmentRepository creates a new PostGIS equipment repository
func NewEquipmentRepository(db *sql.DB) *EquipmentRepository {
	return &EquipmentRepository{
		db: db,
	}
}

// Create creates new equipment in PostGIS
func (r *EquipmentRepository) Create(ctx context.Context, e *domain.Equipment) error {
	query := `
		INSERT INTO equipment (id, building_id, floor_id, room_id, equipment_tag, name, equipment_type, model,
		                       location_x, location_y, location_z, status, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
	`

	var floorID, roomID sql.NullString
	var locX, locY, locZ sql.NullFloat64

	// Handle nullable fields
	if !e.FloorID.IsEmpty() {
		floorID = sql.NullString{String: e.FloorID.String(), Valid: true}
	}
	if !e.RoomID.IsEmpty() {
		roomID = sql.NullString{String: e.RoomID.String(), Valid: true}
	}
	if e.Location != nil {
		locX = sql.NullFloat64{Float64: e.Location.X, Valid: true}
		locY = sql.NullFloat64{Float64: e.Location.Y, Valid: true}
		locZ = sql.NullFloat64{Float64: e.Location.Z, Valid: true}
	}

	// Generate equipment tag (unique identifier)
	equipmentTag := e.ID.String()

	_, err := r.db.ExecContext(ctx, query,
		e.ID.String(),
		e.BuildingID.String(),
		floorID,
		roomID,
		equipmentTag,
		e.Name,
		e.Type,
		e.Model,
		locX,
		locY,
		locZ,
		e.Status,
		e.CreatedAt,
		e.UpdatedAt,
	)

	return err
}

// GetByID retrieves equipment by ID
func (r *EquipmentRepository) GetByID(ctx context.Context, id string) (*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE id = $1
	`

	var e domain.Equipment
	var floorID, roomID sql.NullString
	var locX, locY, locZ sql.NullFloat64

	err := r.db.QueryRowContext(ctx, query, id).Scan(
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
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("equipment not found")
		}
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

	return &e, nil
}

// GetByBuilding retrieves equipment by building ID
func (r *EquipmentRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
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

	return r.scanEquipmentRows(rows)
}

// GetByType retrieves equipment by type
func (r *EquipmentRepository) GetByType(ctx context.Context, equipmentType string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE equipment_type = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, equipmentType)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanEquipmentRows(rows)
}

// List retrieves equipment with optional filtering
func (r *EquipmentRepository) List(ctx context.Context, filter *domain.EquipmentFilter) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE 1=1`

	args := []any{}
	argCount := 1

	// Add filters
	if filter != nil {
		if filter.BuildingID != nil {
			query += fmt.Sprintf(" AND building_id = $%d", argCount)
			args = append(args, filter.BuildingID.String())
			argCount++
		}
		if filter.FloorID != nil {
			query += fmt.Sprintf(" AND floor_id = $%d", argCount)
			args = append(args, filter.FloorID.String())
			argCount++
		}
		if filter.RoomID != nil {
			query += fmt.Sprintf(" AND room_id = $%d", argCount)
			args = append(args, filter.RoomID.String())
			argCount++
		}
		if filter.Type != nil {
			query += fmt.Sprintf(" AND equipment_type = $%d", argCount)
			args = append(args, *filter.Type)
			argCount++
		}
		if filter.Status != nil {
			query += fmt.Sprintf(" AND status = $%d", argCount)
			args = append(args, *filter.Status)
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

	return r.scanEquipmentRows(rows)
}

// Update updates existing equipment
func (r *EquipmentRepository) Update(ctx context.Context, e *domain.Equipment) error {
	query := `
		UPDATE equipment
		SET name = $2, equipment_type = $3, model = $4,
		    location_x = $5, location_y = $6, location_z = $7,
		    status = $8, updated_at = $9
		WHERE id = $1
	`

	var locX, locY, locZ sql.NullFloat64
	if e.Location != nil {
		locX = sql.NullFloat64{Float64: e.Location.X, Valid: true}
		locY = sql.NullFloat64{Float64: e.Location.Y, Valid: true}
		locZ = sql.NullFloat64{Float64: e.Location.Z, Valid: true}
	}

	_, err := r.db.ExecContext(ctx, query,
		e.ID.String(),
		e.Name,
		e.Type,
		e.Model,
		locX,
		locY,
		locZ,
		e.Status,
		e.UpdatedAt,
	)

	return err
}

// Delete deletes equipment by ID
func (r *EquipmentRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM equipment WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// GetByLocation retrieves equipment by location (building, floor, room)
func (r *EquipmentRepository) GetByLocation(ctx context.Context, buildingID, floor, room string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, equipment_type, model,
		       location_x, location_y, location_z, status, created_at, updated_at
		FROM equipment
		WHERE building_id = $1`

	args := []any{buildingID}
	argCount := 2

	if floor != "" {
		query += fmt.Sprintf(" AND floor_id = $%d", argCount)
		args = append(args, floor)
		argCount++
	}

	if room != "" {
		query += fmt.Sprintf(" AND room_id = $%d", argCount)
		args = append(args, room)
	}

	query += " ORDER BY created_at DESC"

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return r.scanEquipmentRows(rows)
}

// scanEquipmentRows is a helper function to scan equipment rows
func (r *EquipmentRepository) scanEquipmentRows(rows *sql.Rows) ([]*domain.Equipment, error) {
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
