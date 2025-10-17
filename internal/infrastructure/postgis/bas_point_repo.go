package postgis

import (
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/pkg/naming"
)

// BASPointRepository implements BAS point repository for PostGIS
type BASPointRepository struct {
	db *sql.DB
}

// NewBASPointRepository creates a new PostGIS BAS point repository
func NewBASPointRepository(db *sql.DB) *BASPointRepository {
	return &BASPointRepository{
		db: db,
	}
}

// Create creates a new BAS point in PostGIS
func (r *BASPointRepository) Create(point *domain.BASPoint) error {
	query := `
		INSERT INTO bas_points (
			id, building_id, bas_system_id, room_id, floor_id, equipment_id,
			point_name, path, device_id, object_type, object_instance,
			description, units, point_type, location_text,
			writeable, min_value, max_value,
			mapped, mapping_confidence,
			imported_at, import_source,
			added_in_version, removed_in_version,
			metadata, created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6,
			$7, $8, $9, $10, $11,
			$12, $13, $14, $15,
			$16, $17, $18,
			$19, $20,
			$21, $22,
			$23, $24,
			$25, $26, $27
		)
	`

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(point.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.Exec(query,
		point.ID.String(), point.BuildingID.String(), point.BASSystemID.String(),
		nullableID(point.RoomID), nullableID(point.FloorID), nullableID(point.EquipmentID),
		point.PointName, point.Path, point.DeviceID, point.ObjectType, point.ObjectInstance,
		point.Description, point.Units, point.PointType, point.LocationText,
		point.Writeable, point.MinValue, point.MaxValue,
		point.Mapped, point.MappingConfidence,
		point.ImportedAt, point.ImportSource,
		nullableID(point.AddedInVersion), nullableID(point.RemovedInVersion),
		metadataJSON, point.CreatedAt, point.UpdatedAt,
	)

	return err
}

// GetByID retrieves a BAS point by ID
func (r *BASPointRepository) GetByID(id types.ID) (*domain.BASPoint, error) {
	query := `
		SELECT
			id, building_id, bas_system_id, room_id, floor_id, equipment_id,
			point_name, path, device_id, object_type, object_instance,
			description, units, point_type, location_text,
			writeable, min_value, max_value,
			current_value, current_value_numeric, current_value_boolean, last_updated,
			mapped, mapping_confidence,
			imported_at, import_source,
			added_in_version, removed_in_version,
			metadata, created_at, updated_at
		FROM bas_points
		WHERE id = $1 AND removed_in_version IS NULL
	`

	point := &domain.BASPoint{}
	var roomID, floorID, equipmentID, addedInVersion, removedInVersion, path sql.NullString
	var objectInstance sql.NullInt64
	var minValue, maxValue, currentNumeric sql.NullFloat64
	var currentValue, currentBoolean, lastUpdated sql.NullTime
	var metadataJSON []byte

	err := r.db.QueryRow(query, id.String()).Scan(
		&point.ID, &point.BuildingID, &point.BASSystemID,
		&roomID, &floorID, &equipmentID,
		&point.PointName, &path, &point.DeviceID, &point.ObjectType, &objectInstance,
		&point.Description, &point.Units, &point.PointType, &point.LocationText,
		&point.Writeable, &minValue, &maxValue,
		&currentValue, &currentNumeric, &currentBoolean, &lastUpdated,
		&point.Mapped, &point.MappingConfidence,
		&point.ImportedAt, &point.ImportSource,
		&addedInVersion, &removedInVersion,
		&metadataJSON, &point.CreatedAt, &point.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("BAS point not found")
		}
		return nil, err
	}

	// Handle nullable fields
	if roomID.Valid {
		id := types.FromString(roomID.String)
		point.RoomID = &id
	}
	if floorID.Valid {
		id := types.FromString(floorID.String)
		point.FloorID = &id
	}
	if equipmentID.Valid {
		id := types.FromString(equipmentID.String)
		point.EquipmentID = &id
	}
	if objectInstance.Valid {
		val := int(objectInstance.Int64)
		point.ObjectInstance = &val
	}
	if minValue.Valid {
		point.MinValue = &minValue.Float64
	}
	if maxValue.Valid {
		point.MaxValue = &maxValue.Float64
	}
	if addedInVersion.Valid {
		id := types.FromString(addedInVersion.String)
		point.AddedInVersion = &id
	}
	if removedInVersion.Valid {
		id := types.FromString(removedInVersion.String)
		point.RemovedInVersion = &id
	}
	if path.Valid {
		point.Path = path.String
	}

	// Unmarshal metadata JSON
	if len(metadataJSON) > 0 {
		point.Metadata = make(map[string]interface{})
		if err := json.Unmarshal(metadataJSON, &point.Metadata); err != nil {
			return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
		}
	}

	return point, nil
}

// Update updates an existing BAS point
func (r *BASPointRepository) Update(point *domain.BASPoint) error {
	query := `
		UPDATE bas_points SET
			point_name = $1,
			room_id = $2,
			floor_id = $3,
			equipment_id = $4,
			description = $5,
			units = $6,
			point_type = $7,
			location_text = $8,
			writeable = $9,
			min_value = $10,
			max_value = $11,
			current_value = $12,
			current_value_numeric = $13,
			current_value_boolean = $14,
			last_updated = $15,
			mapped = $16,
			mapping_confidence = $17,
			metadata = $18,
			updated_at = NOW()
		WHERE id = $19
	`

	// Marshal metadata to JSON
	metadataJSON, err := json.Marshal(point.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.Exec(query,
		point.PointName,
		nullableID(point.RoomID), nullableID(point.FloorID), nullableID(point.EquipmentID),
		point.Description, point.Units, point.PointType, point.LocationText,
		point.Writeable, point.MinValue, point.MaxValue,
		point.CurrentValue, point.CurrentValueNumeric, point.CurrentValueBoolean, point.LastUpdated,
		point.Mapped, point.MappingConfidence,
		metadataJSON,
		point.ID.String(),
	)

	return err
}

// Delete soft-deletes a BAS point by setting removed_in_version
func (r *BASPointRepository) Delete(id types.ID) error {
	query := `
		UPDATE bas_points
		SET removed_in_version = $1, updated_at = NOW()
		WHERE id = $2
	`

	// Note: Version ID could come from context in the future
	// For now, use nil for soft delete (marks as removed but doesn't track version)
	// When version control is fully wired, pass context.Context to this method
	// and extract version ID via: versionID := ctx.Value("version_id")

	_, err := r.db.Exec(query, nil, id.String())
	return err
}

// List retrieves BAS points with filtering
func (r *BASPointRepository) List(filter domain.BASPointFilter, limit, offset int) ([]*domain.BASPoint, error) {
	query, args := r.buildListQuery(filter, limit, offset)

	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	points := make([]*domain.BASPoint, 0)
	for rows.Next() {
		point, err := r.scanBASPoint(rows)
		if err != nil {
			return nil, err
		}
		points = append(points, point)
	}

	return points, nil
}

// Count counts BAS points matching filter
func (r *BASPointRepository) Count(filter domain.BASPointFilter) (int, error) {
	query, args := r.buildCountQuery(filter)

	var count int
	err := r.db.QueryRow(query, args...).Scan(&count)
	if err != nil {
		return 0, err
	}

	return count, nil
}

// ListByBuilding retrieves all BAS points for a building
func (r *BASPointRepository) ListByBuilding(buildingID types.ID) ([]*domain.BASPoint, error) {
	return r.List(domain.BASPointFilter{
		BuildingID: &buildingID,
	}, 10000, 0)
}

// ListByBASSystem retrieves all BAS points for a BAS system
func (r *BASPointRepository) ListByBASSystem(systemID types.ID) ([]*domain.BASPoint, error) {
	return r.List(domain.BASPointFilter{
		BASSystemID: &systemID,
	}, 10000, 0)
}

// ListByRoom retrieves all BAS points for a room
func (r *BASPointRepository) ListByRoom(roomID types.ID) ([]*domain.BASPoint, error) {
	return r.List(domain.BASPointFilter{
		RoomID: &roomID,
	}, 1000, 0)
}

// ListByEquipment retrieves all BAS points for equipment
func (r *BASPointRepository) ListByEquipment(equipmentID types.ID) ([]*domain.BASPoint, error) {
	return r.List(domain.BASPointFilter{
		EquipmentID: &equipmentID,
	}, 1000, 0)
}

// ListUnmapped retrieves unmapped BAS points for a building
func (r *BASPointRepository) ListUnmapped(buildingID types.ID) ([]*domain.BASPoint, error) {
	mapped := false
	return r.List(domain.BASPointFilter{
		BuildingID: &buildingID,
		Mapped:     &mapped,
	}, 10000, 0)
}

// BulkCreate creates multiple BAS points in a single transaction
func (r *BASPointRepository) BulkCreate(points []*domain.BASPoint) error {
	if len(points) == 0 {
		return nil
	}

	tx, err := r.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		INSERT INTO bas_points (
			id, building_id, bas_system_id, room_id, floor_id, equipment_id,
			point_name, device_id, object_type, object_instance,
			description, units, point_type, location_text,
			writeable, min_value, max_value,
			mapped, mapping_confidence,
			imported_at, import_source,
			metadata, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, point := range points {
		// Marshal metadata to JSON for this point
		metadataJSON, err := json.Marshal(point.Metadata)
		if err != nil {
			return fmt.Errorf("failed to marshal metadata for point %s: %w", point.PointName, err)
		}

		_, err = stmt.Exec(
			point.ID.String(), point.BuildingID.String(), point.BASSystemID.String(),
			nullableID(point.RoomID), nullableID(point.FloorID), nullableID(point.EquipmentID),
			point.PointName, point.DeviceID, point.ObjectType, point.ObjectInstance,
			point.Description, point.Units, point.PointType, point.LocationText,
			point.Writeable, point.MinValue, point.MaxValue,
			point.Mapped, point.MappingConfidence,
			point.ImportedAt, point.ImportSource,
			metadataJSON, point.CreatedAt, point.UpdatedAt,
		)
		if err != nil {
			return fmt.Errorf("failed to insert point %s: %w", point.PointName, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// BulkUpdate updates multiple BAS points in a single transaction
func (r *BASPointRepository) BulkUpdate(points []*domain.BASPoint) error {
	if len(points) == 0 {
		return nil
	}

	tx, err := r.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		UPDATE bas_points SET
			room_id = $1,
			equipment_id = $2,
			description = $3,
			mapped = $4,
			mapping_confidence = $5,
			metadata = $6,
			updated_at = NOW()
		WHERE id = $7
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, point := range points {
		_, err := stmt.Exec(
			nullableID(point.RoomID),
			nullableID(point.EquipmentID),
			point.Description,
			point.Mapped,
			point.MappingConfidence,
			point.Metadata,
			point.ID.String(),
		)
		if err != nil {
			return fmt.Errorf("failed to update point %s: %w", point.PointName, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// MapToRoom maps a BAS point to a room and generates the full path
func (r *BASPointRepository) MapToRoom(pointID, roomID types.ID, confidence int) error {
	// First, get the point to retrieve its name
	point, err := r.GetByID(pointID)
	if err != nil {
		return fmt.Errorf("failed to get BAS point: %w", err)
	}

	// Get room information to generate path
	roomQuery := `
		SELECT r.number, r.floor_id, f.level, f.building_id, b.name
		FROM rooms r
		JOIN floors f ON r.floor_id = f.id
		JOIN buildings b ON f.building_id = b.id
		WHERE r.id = $1
	`

	var roomNumber string
	var floorLevel int
	var floorID, buildingID string
	var buildingName string

	err = r.db.QueryRow(roomQuery, roomID.String()).Scan(
		&roomNumber, &floorID, &floorLevel, &buildingID, &buildingName,
	)
	if err != nil {
		return fmt.Errorf("failed to get room information: %w", err)
	}

	// Generate path components
	buildingCode := naming.BuildingCodeFromName(buildingName)
	floorCode := naming.FloorCodeFromLevel(fmt.Sprintf("%d", floorLevel))
	roomCode := naming.RoomCodeFromName(roomNumber)
	systemCode := "BAS"
	pointCode := point.PointName

	// Generate full path
	fullPath := naming.GenerateEquipmentPath(
		buildingCode,
		floorCode,
		roomCode,
		systemCode,
		pointCode,
	)

	// Update point with room mapping and full path
	query := `
		UPDATE bas_points SET
			room_id = $1,
			path = $2,
			mapped = true,
			mapping_confidence = $3,
			updated_at = NOW()
		WHERE id = $4
	`

	result, err := r.db.Exec(query, roomID.String(), fullPath, confidence, pointID.String())
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("BAS point not found")
	}

	return nil
}

// MapToEquipment maps a BAS point to equipment
func (r *BASPointRepository) MapToEquipment(pointID, equipmentID types.ID, confidence int) error {
	query := `
		UPDATE bas_points SET
			equipment_id = $1,
			mapped = true,
			mapping_confidence = $2,
			updated_at = NOW()
		WHERE id = $3
	`

	result, err := r.db.Exec(query, equipmentID.String(), confidence, pointID.String())
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("BAS point not found")
	}

	return nil
}

// buildListQuery builds a dynamic query based on filter
func (r *BASPointRepository) buildListQuery(filter domain.BASPointFilter, limit, offset int) (string, []interface{}) {
	query := `
		SELECT
			id, building_id, bas_system_id, room_id, floor_id, equipment_id,
			point_name, path, device_id, object_type, object_instance,
			description, units, point_type, location_text,
			writeable, min_value, max_value,
			current_value, current_value_numeric, current_value_boolean, last_updated,
			mapped, mapping_confidence,
			imported_at, import_source,
			added_in_version, removed_in_version,
			metadata, created_at, updated_at
		FROM bas_points
		WHERE removed_in_version IS NULL
	`

	args := make([]interface{}, 0)
	argCount := 1

	if filter.BuildingID != nil {
		query += fmt.Sprintf(" AND building_id = $%d", argCount)
		args = append(args, filter.BuildingID.String())
		argCount++
	}

	if filter.BASSystemID != nil {
		query += fmt.Sprintf(" AND bas_system_id = $%d", argCount)
		args = append(args, filter.BASSystemID.String())
		argCount++
	}

	if filter.RoomID != nil {
		query += fmt.Sprintf(" AND room_id = $%d", argCount)
		args = append(args, filter.RoomID.String())
		argCount++
	}

	if filter.FloorID != nil {
		query += fmt.Sprintf(" AND floor_id = $%d", argCount)
		args = append(args, filter.FloorID.String())
		argCount++
	}

	if filter.EquipmentID != nil {
		query += fmt.Sprintf(" AND equipment_id = $%d", argCount)
		args = append(args, filter.EquipmentID.String())
		argCount++
	}

	if filter.PointType != "" {
		query += fmt.Sprintf(" AND point_type = $%d", argCount)
		args = append(args, filter.PointType)
		argCount++
	}

	if filter.ObjectType != "" {
		query += fmt.Sprintf(" AND object_type = $%d", argCount)
		args = append(args, filter.ObjectType)
		argCount++
	}

	if filter.DeviceID != "" {
		query += fmt.Sprintf(" AND device_id = $%d", argCount)
		args = append(args, filter.DeviceID)
		argCount++
	}

	if filter.Mapped != nil {
		query += fmt.Sprintf(" AND mapped = $%d", argCount)
		args = append(args, *filter.Mapped)
		argCount++
	}

	query += " ORDER BY point_name"

	if limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argCount)
		args = append(args, limit)
		argCount++
	}

	if offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argCount)
		args = append(args, offset)
	}

	return query, args
}

// buildCountQuery builds a count query based on filter
func (r *BASPointRepository) buildCountQuery(filter domain.BASPointFilter) (string, []interface{}) {
	query := `SELECT COUNT(*) FROM bas_points WHERE removed_in_version IS NULL`

	args := make([]interface{}, 0)
	argCount := 1

	if filter.BuildingID != nil {
		query += fmt.Sprintf(" AND building_id = $%d", argCount)
		args = append(args, filter.BuildingID.String())
		argCount++
	}

	if filter.BASSystemID != nil {
		query += fmt.Sprintf(" AND bas_system_id = $%d", argCount)
		args = append(args, filter.BASSystemID.String())
		argCount++
	}

	if filter.RoomID != nil {
		query += fmt.Sprintf(" AND room_id = $%d", argCount)
		args = append(args, filter.RoomID.String())
		argCount++
	}

	if filter.Mapped != nil {
		query += fmt.Sprintf(" AND mapped = $%d", argCount)
		args = append(args, *filter.Mapped)
		argCount++
	}

	return query, args
}

// scanBASPoint scans a row into a BASPoint entity
func (r *BASPointRepository) scanBASPoint(scanner interface {
	Scan(dest ...interface{}) error
}) (*domain.BASPoint, error) {
	point := &domain.BASPoint{}
	var roomID, floorID, equipmentID, addedInVersion, removedInVersion, path sql.NullString
	var objectInstance sql.NullInt64
	var minValue, maxValue, currentNumeric sql.NullFloat64
	var currentValue, importSource sql.NullString
	var currentBoolean sql.NullBool
	var lastUpdated sql.NullTime
	var metadataJSON []byte

	err := scanner.Scan(
		&point.ID, &point.BuildingID, &point.BASSystemID,
		&roomID, &floorID, &equipmentID,
		&point.PointName, &path, &point.DeviceID, &point.ObjectType, &objectInstance,
		&point.Description, &point.Units, &point.PointType, &point.LocationText,
		&point.Writeable, &minValue, &maxValue,
		&currentValue, &currentNumeric, &currentBoolean, &lastUpdated,
		&point.Mapped, &point.MappingConfidence,
		&point.ImportedAt, &importSource,
		&addedInVersion, &removedInVersion,
		&metadataJSON, &point.CreatedAt, &point.UpdatedAt,
	)

	if err != nil {
		return nil, err
	}

	// Handle nullable fields
	if roomID.Valid {
		id := types.FromString(roomID.String)
		point.RoomID = &id
	}
	if floorID.Valid {
		id := types.FromString(floorID.String)
		point.FloorID = &id
	}
	if equipmentID.Valid {
		id := types.FromString(equipmentID.String)
		point.EquipmentID = &id
	}
	if objectInstance.Valid {
		val := int(objectInstance.Int64)
		point.ObjectInstance = &val
	}
	if minValue.Valid {
		point.MinValue = &minValue.Float64
	}
	if maxValue.Valid {
		point.MaxValue = &maxValue.Float64
	}
	if currentValue.Valid {
		point.CurrentValue = &currentValue.String
	}
	if currentNumeric.Valid {
		point.CurrentValueNumeric = &currentNumeric.Float64
	}
	if currentBoolean.Valid {
		point.CurrentValueBoolean = &currentBoolean.Bool
	}
	if lastUpdated.Valid {
		point.LastUpdated = &lastUpdated.Time
	}
	if importSource.Valid {
		point.ImportSource = importSource.String
	}
	if addedInVersion.Valid {
		id := types.FromString(addedInVersion.String)
		point.AddedInVersion = &id
	}
	if removedInVersion.Valid {
		id := types.FromString(removedInVersion.String)
		point.RemovedInVersion = &id
	}
	if path.Valid {
		point.Path = path.String
	}

	// Unmarshal metadata JSON
	if len(metadataJSON) > 0 {
		point.Metadata = make(map[string]interface{})
		if err := json.Unmarshal(metadataJSON, &point.Metadata); err != nil {
			return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
		}
	}

	return point, nil
}

// nullableID converts a pointer to ID to sql.NullString
func nullableID(id *types.ID) sql.NullString {
	if id == nil {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: id.String(), Valid: true}
}

// GetByPath retrieves a BAS point by exact path match
func (r *BASPointRepository) GetByPath(exactPath string) (*domain.BASPoint, error) {
	query := `
		SELECT
			id, building_id, bas_system_id, room_id, floor_id, equipment_id,
			point_name, device_id, object_type, object_instance,
			description, units, point_type, location_text,
			writeable, min_value, max_value,
			current_value, current_value_numeric, current_value_boolean, last_updated,
			mapped, mapping_confidence,
			imported_at, import_source,
			added_in_version, removed_in_version,
			metadata, path, created_at, updated_at
		FROM bas_points
		WHERE path = $1 AND removed_in_version IS NULL
	`

	point := &domain.BASPoint{}
	var roomID, floorID, equipmentID, addedInVersion, removedInVersion sql.NullString
	var objectInstance sql.NullInt64
	var minValue, maxValue, currentNumeric sql.NullFloat64
	var currentValue sql.NullString
	var currentBoolean sql.NullBool
	var lastUpdated sql.NullTime
	var importSource sql.NullString
	var path sql.NullString
	var metadataJSON []byte

	err := r.db.QueryRow(query, exactPath).Scan(
		&point.ID, &point.BuildingID, &point.BASSystemID,
		&roomID, &floorID, &equipmentID,
		&point.PointName, &point.DeviceID, &point.ObjectType, &objectInstance,
		&point.Description, &point.Units, &point.PointType, &point.LocationText,
		&point.Writeable, &minValue, &maxValue,
		&currentValue, &currentNumeric, &currentBoolean, &lastUpdated,
		&point.Mapped, &point.MappingConfidence,
		&point.ImportedAt, &importSource,
		&addedInVersion, &removedInVersion,
		&metadataJSON, &path, &point.CreatedAt, &point.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("BAS point not found at path: %s", exactPath)
		}
		return nil, err
	}

	// Unmarshal metadata
	if len(metadataJSON) > 0 {
		if err := json.Unmarshal(metadataJSON, &point.Metadata); err != nil {
			return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
		}
	}

	// Handle nullable fields
	if roomID.Valid {
		id := types.FromString(roomID.String)
		point.RoomID = &id
	}
	if floorID.Valid {
		id := types.FromString(floorID.String)
		point.FloorID = &id
	}
	if equipmentID.Valid {
		id := types.FromString(equipmentID.String)
		point.EquipmentID = &id
	}
	if objectInstance.Valid {
		val := int(objectInstance.Int64)
		point.ObjectInstance = &val
	}
	if minValue.Valid {
		point.MinValue = &minValue.Float64
	}
	if maxValue.Valid {
		point.MaxValue = &maxValue.Float64
	}
	if currentValue.Valid {
		point.CurrentValue = &currentValue.String
	}
	if currentNumeric.Valid {
		point.CurrentValueNumeric = &currentNumeric.Float64
	}
	if currentBoolean.Valid {
		point.CurrentValueBoolean = &currentBoolean.Bool
	}
	if lastUpdated.Valid {
		point.LastUpdated = &lastUpdated.Time
	}
	if importSource.Valid {
		point.ImportSource = importSource.String
	}
	if addedInVersion.Valid {
		id := types.FromString(addedInVersion.String)
		point.AddedInVersion = &id
	}
	if removedInVersion.Valid {
		id := types.FromString(removedInVersion.String)
		point.RemovedInVersion = &id
	}
	if path.Valid {
		point.Path = path.String
	}

	return point, nil
}

// FindByPath retrieves BAS points matching a path pattern (supports wildcards)
// Pattern examples: /B1/3/*/BAS/*, /B1/*/301/BAS/AI-*
func (r *BASPointRepository) FindByPath(pathPattern string) ([]*domain.BASPoint, error) {
	// Convert path pattern to SQL LIKE pattern
	sqlPattern := naming.ToSQLPattern(pathPattern)

	// Validate pattern has at least some specificity
	if sqlPattern == "%" || sqlPattern == "/%" {
		return nil, fmt.Errorf("path pattern too broad, must include at least one specific segment")
	}

	query := `
		SELECT
			id, building_id, bas_system_id, room_id, floor_id, equipment_id,
			point_name, device_id, object_type, object_instance,
			description, units, point_type, location_text,
			writeable, min_value, max_value,
			current_value, current_value_numeric, current_value_boolean, last_updated,
			mapped, mapping_confidence,
			imported_at, import_source,
			added_in_version, removed_in_version,
			metadata, path, created_at, updated_at
		FROM bas_points
		WHERE path LIKE $1 AND removed_in_version IS NULL
		ORDER BY path ASC
	`

	rows, err := r.db.Query(query, sqlPattern)
	if err != nil {
		return nil, fmt.Errorf("failed to query BAS points by path pattern: %w", err)
	}
	defer rows.Close()

	var points []*domain.BASPoint
	for rows.Next() {
		point := &domain.BASPoint{}
		var roomID, floorID, equipmentID, addedInVersion, removedInVersion sql.NullString
		var objectInstance sql.NullInt64
		var minValue, maxValue, currentNumeric sql.NullFloat64
		var currentValue sql.NullString
		var currentBoolean sql.NullBool
		var lastUpdated sql.NullTime
		var importSource sql.NullString
		var path sql.NullString
		var metadataJSON []byte

		err := rows.Scan(
			&point.ID, &point.BuildingID, &point.BASSystemID,
			&roomID, &floorID, &equipmentID,
			&point.PointName, &point.DeviceID, &point.ObjectType, &objectInstance,
			&point.Description, &point.Units, &point.PointType, &point.LocationText,
			&point.Writeable, &minValue, &maxValue,
			&currentValue, &currentNumeric, &currentBoolean, &lastUpdated,
			&point.Mapped, &point.MappingConfidence,
			&point.ImportedAt, &importSource,
			&addedInVersion, &removedInVersion,
			&metadataJSON, &path, &point.CreatedAt, &point.UpdatedAt,
		)

		if err != nil {
			return nil, err
		}

		// Unmarshal metadata
		if len(metadataJSON) > 0 {
			if err := json.Unmarshal(metadataJSON, &point.Metadata); err != nil {
				return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
			}
		}

		// Handle nullable fields
		if roomID.Valid {
			id := types.FromString(roomID.String)
			point.RoomID = &id
		}
		if floorID.Valid {
			id := types.FromString(floorID.String)
			point.FloorID = &id
		}
		if equipmentID.Valid {
			id := types.FromString(equipmentID.String)
			point.EquipmentID = &id
		}
		if objectInstance.Valid {
			val := int(objectInstance.Int64)
			point.ObjectInstance = &val
		}
		if minValue.Valid {
			point.MinValue = &minValue.Float64
		}
		if maxValue.Valid {
			point.MaxValue = &maxValue.Float64
		}
		if currentValue.Valid {
			point.CurrentValue = &currentValue.String
		}
		if currentNumeric.Valid {
			point.CurrentValueNumeric = &currentNumeric.Float64
		}
		if currentBoolean.Valid {
			point.CurrentValueBoolean = &currentBoolean.Bool
		}
		if lastUpdated.Valid {
			point.LastUpdated = &lastUpdated.Time
		}
		if importSource.Valid {
			point.ImportSource = importSource.String
		}
		if addedInVersion.Valid {
			id := types.FromString(addedInVersion.String)
			point.AddedInVersion = &id
		}
		if removedInVersion.Valid {
			id := types.FromString(removedInVersion.String)
			point.RemovedInVersion = &id
		}
		if path.Valid {
			point.Path = path.String
		}

		points = append(points, point)
	}

	return points, nil
}
