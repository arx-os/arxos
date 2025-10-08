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
		INSERT INTO equipment (id, building_id, floor_id, room_id, name, type, model, location, status, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, ST_GeomFromText($8, 4326), $9, $10, $11)
	`

	var floorID, roomID, locationStr any

	// Handle nullable fields
	if !e.FloorID.IsEmpty() {
		floorID = e.FloorID.String()
	}
	if !e.RoomID.IsEmpty() {
		roomID = e.RoomID.String()
	}
	if e.Location != nil {
		locationStr = fmt.Sprintf("POINT(%f %f %f)", e.Location.X, e.Location.Y, e.Location.Z)
	}

	_, err := r.db.ExecContext(ctx, query,
		e.ID.String(),
		e.BuildingID.String(),
		floorID,
		roomID,
		e.Name,
		e.Type,
		e.Model,
		locationStr,
		e.Status,
		e.CreatedAt,
		e.UpdatedAt,
	)

	return err
}

// GetByID retrieves equipment by ID
func (r *EquipmentRepository) GetByID(ctx context.Context, id string) (*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, type, model,
		       ST_AsText(location), status, created_at, updated_at
		FROM equipment
		WHERE id = $1
	`

	var e domain.Equipment
	var locStr sql.NullString
	var floorID, roomID sql.NullString

	err := r.db.QueryRowContext(ctx, query, id).Scan(
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

	// Parse location from PostGIS POINT
	if locStr.Valid {
		e.Location = parsePoint(locStr.String)
	}

	return &e, nil
}

// GetByBuilding retrieves equipment by building ID
func (r *EquipmentRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
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

	return r.scanEquipmentRows(rows)
}

// GetByType retrieves equipment by type
func (r *EquipmentRepository) GetByType(ctx context.Context, equipmentType string) ([]*domain.Equipment, error) {
	query := `
		SELECT id, building_id, floor_id, room_id, name, type, model,
		       ST_AsText(location), status, created_at, updated_at
		FROM equipment
		WHERE type = $1
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
		SELECT id, building_id, floor_id, room_id, name, type, model,
		       ST_AsText(location), status, created_at, updated_at
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
			query += fmt.Sprintf(" AND type = $%d", argCount)
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
		SET name = $2, type = $3, model = $4, location = ST_GeomFromText($5, 4326),
		    status = $6, updated_at = $7
		WHERE id = $1
	`

	var locationStr any
	if e.Location != nil {
		locationStr = fmt.Sprintf("POINT(%f %f %f)", e.Location.X, e.Location.Y, e.Location.Z)
	}

	_, err := r.db.ExecContext(ctx, query,
		e.ID.String(),
		e.Name,
		e.Type,
		e.Model,
		locationStr,
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
		SELECT id, building_id, floor_id, room_id, name, type, model,
		       ST_AsText(location), status, created_at, updated_at
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
