package postgis

import (
	"context"
	"database/sql"

	"github.com/arx-os/arxos/internal/domain"
)

// FindEquipmentNearby finds equipment within a radius of a point
func (r *SpatialRepository) FindEquipmentNearby(ctx context.Context, lat, lon, radiusMeters float64, buildingID string) ([]*domain.Equipment, error) {
	query := `
		SELECT
			e.id,
			e.building_id,
			e.floor_id,
			e.room_id,
			e.name,
			e.type,
			e.model,
			ST_AsText(e.location) as location,
			e.status,
			e.created_at,
			e.updated_at,
			ST_Distance(
				e.location::geography,
				ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
			) as distance
		FROM equipment e
		WHERE ST_DWithin(
			e.location::geography,
			ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
			$3
		)
	`

	args := []any{lon, lat, radiusMeters}

	// Filter by building if provided
	if buildingID != "" {
		query += " AND e.building_id = $4"
		args = append(args, buildingID)
	}

	query += " ORDER BY distance ASC"

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		r.logger.Error("Failed to find nearby equipment", "error", err)
		return nil, err
	}
	defer rows.Close()

	var equipment []*domain.Equipment
	for rows.Next() {
		var e domain.Equipment
		var locStr sql.NullString
		var floorID, roomID sql.NullString
		var distance float64

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
			&distance,
		)

		if err != nil {
			r.logger.Error("Failed to scan equipment", "error", err)
			continue
		}

		// Set nullable fields
		if floorID.Valid {
			e.FloorID.Legacy = floorID.String
		}
		if roomID.Valid {
			e.RoomID.Legacy = roomID.String
		}

		// Parse location
		if locStr.Valid {
			e.Location = parsePoint(locStr.String)
		}

		equipment = append(equipment, &e)
	}

	r.logger.Info("Found nearby equipment", "count", len(equipment), "radius_meters", radiusMeters)
	return equipment, nil
}

// FindEquipmentWithinBounds finds equipment within a bounding box
func (r *SpatialRepository) FindEquipmentWithinBounds(ctx context.Context, minLat, minLon, maxLat, maxLon float64) ([]*domain.Equipment, error) {
	query := `
		SELECT
			e.id,
			e.building_id,
			e.floor_id,
			e.room_id,
			e.name,
			e.type,
			e.model,
			ST_AsText(e.location) as location,
			e.status,
			e.created_at,
			e.updated_at
		FROM equipment e
		WHERE ST_Within(
			e.location,
			ST_MakeEnvelope($1, $2, $3, $4, 4326)
		)
		ORDER BY e.created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, minLon, minLat, maxLon, maxLat)
	if err != nil {
		r.logger.Error("Failed to find equipment within bounds", "error", err)
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
			r.logger.Error("Failed to scan equipment", "error", err)
			continue
		}

		// Set nullable fields
		if floorID.Valid {
			e.FloorID.Legacy = floorID.String
		}
		if roomID.Valid {
			e.RoomID.Legacy = roomID.String
		}

		// Parse location
		if locStr.Valid {
			e.Location = parsePoint(locStr.String)
		}

		equipment = append(equipment, &e)
	}

	r.logger.Info("Found equipment within bounds", "count", len(equipment))
	return equipment, nil
}

// FindBuildingsNearby finds buildings within a radius of a point
func (r *SpatialRepository) FindBuildingsNearby(ctx context.Context, lat, lon, radiusMeters float64) ([]*domain.Building, error) {
	query := `
		SELECT
			b.id,
			b.name,
			b.address,
			ST_AsText(b.coordinates) as coordinates,
			b.created_at,
			b.updated_at,
			ST_Distance(
				b.coordinates::geography,
				ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
			) as distance
		FROM buildings b
		WHERE ST_DWithin(
			b.coordinates::geography,
			ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
			$3
		)
		ORDER BY distance ASC
	`

	rows, err := r.db.QueryContext(ctx, query, lon, lat, radiusMeters)
	if err != nil {
		r.logger.Error("Failed to find nearby buildings", "error", err)
		return nil, err
	}
	defer rows.Close()

	var buildings []*domain.Building
	for rows.Next() {
		var b domain.Building
		var coordStr sql.NullString
		var distance float64

		err := rows.Scan(
			&b.ID,
			&b.Name,
			&b.Address,
			&coordStr,
			&b.CreatedAt,
			&b.UpdatedAt,
			&distance,
		)

		if err != nil {
			r.logger.Error("Failed to scan building", "error", err)
			continue
		}

		// Parse coordinates
		if coordStr.Valid {
			b.Coordinates = parsePoint(coordStr.String)
		}

		buildings = append(buildings, &b)
	}

	r.logger.Info("Found nearby buildings", "count", len(buildings), "radius_meters", radiusMeters)
	return buildings, nil
}

// CalculateDistance calculates the distance between two points in meters
func (r *SpatialRepository) CalculateDistance(ctx context.Context, lat1, lon1, lat2, lon2 float64) (float64, error) {
	query := `
		SELECT ST_Distance(
			ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
			ST_SetSRID(ST_MakePoint($3, $4), 4326)::geography
		) as distance_meters
	`

	var distance float64
	err := r.db.QueryRowContext(ctx, query, lon1, lat1, lon2, lat2).Scan(&distance)
	if err != nil {
		r.logger.Error("Failed to calculate distance", "error", err)
		return 0, err
	}

	return distance, nil
}

// GetEquipmentInRadius gets equipment within a specific radius of coordinates
func (r *SpatialRepository) GetEquipmentInRadius(ctx context.Context, centerX, centerY, centerZ, radiusMeters float64) ([]*domain.Equipment, error) {
	// Use geography type for accurate distance calculation in meters
	query := `
		SELECT
			e.id,
			e.building_id,
			e.floor_id,
			e.room_id,
			e.name,
			e.type,
			e.model,
			ST_AsText(e.location) as location,
			e.status,
			e.created_at,
			e.updated_at,
			ST_Distance(
				e.location::geography,
				ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
			) as distance_meters
		FROM equipment e
		WHERE e.location IS NOT NULL
		  AND ST_DWithin(
			e.location::geography,
			ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
			$3
		  )
		ORDER BY distance_meters ASC
	`

	rows, err := r.db.QueryContext(ctx, query, centerX, centerY, radiusMeters)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var equipment []*domain.Equipment
	for rows.Next() {
		var e domain.Equipment
		var locStr sql.NullString
		var floorID, roomID sql.NullString
		var distance float64

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
			&distance,
		)

		if err != nil {
			continue
		}

		// Set nullable fields
		if floorID.Valid {
			e.FloorID.Legacy = floorID.String
		}
		if roomID.Valid {
			e.RoomID.Legacy = roomID.String
		}

		// Parse location
		if locStr.Valid {
			e.Location = parsePoint(locStr.String)
		}

		equipment = append(equipment, &e)
	}

	return equipment, nil
}
