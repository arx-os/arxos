package postgis

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/google/uuid"
)

// EquipmentRepository implements the equipment.Repository interface using PostGIS
type EquipmentRepository struct {
	client *Client
}

// NewEquipmentRepository creates a new PostGIS equipment repository
func NewEquipmentRepository(client *Client) *EquipmentRepository {
	return &EquipmentRepository{client: client}
}

// Create creates new equipment in the database
func (r *EquipmentRepository) Create(ctx context.Context, e *equipment.Equipment) error {
	var positionGeom, positionLocalJSON interface{}

	if e.Position != nil {
		positionGeom = fmt.Sprintf("ST_SetSRID(ST_MakePoint(%f, %f, %f), 4326)",
			e.Position.X, e.Position.Y, e.Position.Z)
	} else {
		positionGeom = nil
	}

	if e.PositionLocal != nil {
		localJSON, _ := json.Marshal(e.PositionLocal)
		positionLocalJSON = localJSON
	}

	metadataJSON, _ := json.Marshal(e.Metadata)

	query := `
		INSERT INTO equipment (
			id, building_id, path, name, type,
			position, position_local, confidence, status, metadata
		) VALUES (
			$1, $2, $3, $4, $5,
			$6, $7, $8, $9, $10
		)
	`

	_, err := r.client.db.ExecContext(ctx, query,
		e.ID, e.BuildingID, e.Path, e.Name, e.Type,
		positionGeom, positionLocalJSON, e.Confidence, e.Status, metadataJSON)

	if err != nil {
		return fmt.Errorf("failed to create equipment: %w", err)
	}

	return nil
}

// GetByID retrieves equipment by UUID
func (r *EquipmentRepository) GetByID(ctx context.Context, id uuid.UUID) (*equipment.Equipment, error) {
	query := `
		SELECT
			id, building_id, path, name, type,
			ST_X(position) as x, ST_Y(position) as y, ST_Z(position) as z,
			position_local, confidence, status, metadata,
			created_at, updated_at
		FROM equipment
		WHERE id = $1
	`

	var e equipment.Equipment
	var x, y, z sql.NullFloat64
	var positionLocalJSON, metadataJSON []byte

	err := r.client.db.QueryRowContext(ctx, query, id).Scan(
		&e.ID, &e.BuildingID, &e.Path, &e.Name, &e.Type,
		&x, &y, &z,
		&positionLocalJSON, &e.Confidence, &e.Status, &metadataJSON,
		&e.CreatedAt, &e.UpdatedAt)

	if err == sql.ErrNoRows {
		return nil, equipment.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Parse position
	if x.Valid && y.Valid {
		e.Position = &equipment.Position{
			X: x.Float64,
			Y: y.Float64,
			Z: z.Float64,
		}
	}

	// Parse local position
	if positionLocalJSON != nil {
		var localPos equipment.Position
		if err := json.Unmarshal(positionLocalJSON, &localPos); err == nil {
			e.PositionLocal = &localPos
		}
	}

	// Parse metadata
	if metadataJSON != nil {
		json.Unmarshal(metadataJSON, &e.Metadata)
	}

	return &e, nil
}

// GetByPath retrieves equipment by building ID and path
func (r *EquipmentRepository) GetByPath(ctx context.Context, buildingID uuid.UUID, path string) (*equipment.Equipment, error) {
	query := `
		SELECT
			id, building_id, path, name, type,
			ST_X(position) as x, ST_Y(position) as y, ST_Z(position) as z,
			position_local, confidence, status, metadata,
			created_at, updated_at
		FROM equipment
		WHERE building_id = $1 AND path = $2
	`

	var e equipment.Equipment
	var x, y, z sql.NullFloat64
	var positionLocalJSON, metadataJSON []byte

	err := r.client.db.QueryRowContext(ctx, query, buildingID, path).Scan(
		&e.ID, &e.BuildingID, &e.Path, &e.Name, &e.Type,
		&x, &y, &z,
		&positionLocalJSON, &e.Confidence, &e.Status, &metadataJSON,
		&e.CreatedAt, &e.UpdatedAt)

	if err == sql.ErrNoRows {
		return nil, equipment.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Parse position
	if x.Valid && y.Valid {
		e.Position = &equipment.Position{
			X: x.Float64,
			Y: y.Float64,
			Z: z.Float64,
		}
	}

	// Parse local position
	if positionLocalJSON != nil {
		var localPos equipment.Position
		if err := json.Unmarshal(positionLocalJSON, &localPos); err == nil {
			e.PositionLocal = &localPos
		}
	}

	// Parse metadata
	if metadataJSON != nil {
		json.Unmarshal(metadataJSON, &e.Metadata)
	}

	return &e, nil
}

// Update updates existing equipment
func (r *EquipmentRepository) Update(ctx context.Context, e *equipment.Equipment) error {
	var positionGeom string
	var positionLocalJSON interface{}

	if e.Position != nil {
		positionGeom = fmt.Sprintf("ST_SetSRID(ST_MakePoint(%f, %f, %f), 4326)",
			e.Position.X, e.Position.Y, e.Position.Z)
	} else {
		positionGeom = "NULL"
	}

	if e.PositionLocal != nil {
		localJSON, _ := json.Marshal(e.PositionLocal)
		positionLocalJSON = localJSON
	}

	metadataJSON, _ := json.Marshal(e.Metadata)

	query := `
		UPDATE equipment
		SET name = $2, type = $3,
		    position = ` + positionGeom + `,
		    position_local = $4, confidence = $5,
		    status = $6, metadata = $7,
		    updated_at = NOW()
		WHERE id = $1
	`

	result, err := r.client.db.ExecContext(ctx, query,
		e.ID, e.Name, e.Type,
		positionLocalJSON, e.Confidence, e.Status, metadataJSON)

	if err != nil {
		return fmt.Errorf("failed to update equipment: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return equipment.ErrNotFound
	}

	return nil
}

// Delete deletes equipment by ID
func (r *EquipmentRepository) Delete(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM equipment WHERE id = $1`

	result, err := r.client.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete equipment: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return equipment.ErrNotFound
	}

	return nil
}

// List retrieves equipment with optional filtering
func (r *EquipmentRepository) List(ctx context.Context, filter equipment.Filter) ([]*equipment.Equipment, error) {
	query := `
		SELECT
			id, building_id, path, name, type,
			ST_X(position) as x, ST_Y(position) as y, ST_Z(position) as z,
			position_local, confidence, status, metadata,
			created_at, updated_at
		FROM equipment
		WHERE 1=1
	`

	args := []interface{}{}
	argNum := 1

	if filter.BuildingID != uuid.Nil {
		query += fmt.Sprintf(" AND building_id = $%d", argNum)
		args = append(args, filter.BuildingID)
		argNum++
	}

	if filter.Type != "" {
		query += fmt.Sprintf(" AND type = $%d", argNum)
		args = append(args, filter.Type)
		argNum++
	}

	if filter.Status != "" {
		query += fmt.Sprintf(" AND status = $%d", argNum)
		args = append(args, filter.Status)
		argNum++
	}

	query += " ORDER BY path ASC"

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
		return nil, fmt.Errorf("failed to list equipment: %w", err)
	}
	defer rows.Close()

	equipmentList := make([]*equipment.Equipment, 0)

	for rows.Next() {
		var e equipment.Equipment
		var x, y, z sql.NullFloat64
		var positionLocalJSON, metadataJSON []byte

		err := rows.Scan(
			&e.ID, &e.BuildingID, &e.Path, &e.Name, &e.Type,
			&x, &y, &z,
			&positionLocalJSON, &e.Confidence, &e.Status, &metadataJSON,
			&e.CreatedAt, &e.UpdatedAt)

		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		// Parse position
		if x.Valid && y.Valid {
			e.Position = &equipment.Position{
				X: x.Float64,
				Y: y.Float64,
				Z: z.Float64,
			}
		}

		// Parse local position
		if positionLocalJSON != nil {
			var localPos equipment.Position
			if err := json.Unmarshal(positionLocalJSON, &localPos); err == nil {
				e.PositionLocal = &localPos
			}
		}

		// Parse metadata
		if metadataJSON != nil {
			json.Unmarshal(metadataJSON, &e.Metadata)
		}

		equipmentList = append(equipmentList, &e)
	}

	return equipmentList, nil
}

// FindNearby finds equipment within radius of a point
func (r *EquipmentRepository) FindNearby(ctx context.Context, center equipment.Position, radiusMeters float64) ([]*equipment.Equipment, error) {
	query := `
		SELECT
			id, building_id, path, name, type,
			ST_X(position) as x, ST_Y(position) as y, ST_Z(position) as z,
			position_local, confidence, status, metadata,
			created_at, updated_at,
			ST_Distance(position::geography, ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)::geography) as distance
		FROM equipment
		WHERE position IS NOT NULL
		AND ST_DWithin(
			position::geography,
			ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)::geography,
			$4
		)
		ORDER BY distance ASC
	`

	rows, err := r.client.db.QueryContext(ctx, query,
		center.X, center.Y, center.Z, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("failed to find nearby equipment: %w", err)
	}
	defer rows.Close()

	equipmentList := make([]*equipment.Equipment, 0)

	for rows.Next() {
		var e equipment.Equipment
		var x, y, z sql.NullFloat64
		var positionLocalJSON, metadataJSON []byte
		var distance float64

		err := rows.Scan(
			&e.ID, &e.BuildingID, &e.Path, &e.Name, &e.Type,
			&x, &y, &z,
			&positionLocalJSON, &e.Confidence, &e.Status, &metadataJSON,
			&e.CreatedAt, &e.UpdatedAt, &distance)

		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		// Parse position
		if x.Valid && y.Valid {
			e.Position = &equipment.Position{
				X: x.Float64,
				Y: y.Float64,
				Z: z.Float64,
			}
		}

		// Parse local position
		if positionLocalJSON != nil {
			var localPos equipment.Position
			if err := json.Unmarshal(positionLocalJSON, &localPos); err == nil {
				e.PositionLocal = &localPos
			}
		}

		// Parse metadata
		if metadataJSON != nil {
			json.Unmarshal(metadataJSON, &e.Metadata)
		}

		equipmentList = append(equipmentList, &e)
	}

	return equipmentList, nil
}

// FindInBuilding finds all equipment in a building
func (r *EquipmentRepository) FindInBuilding(ctx context.Context, buildingID uuid.UUID) ([]*equipment.Equipment, error) {
	return r.List(ctx, equipment.Filter{BuildingID: buildingID})
}
