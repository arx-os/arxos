package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/spatial"
)

// SpatialQueries provides PostGIS spatial query operations
type SpatialQueries struct {
	client *Client
}

// NewSpatialQueries creates a new spatial queries handler
func NewSpatialQueries(client *Client) *SpatialQueries {
	return &SpatialQueries{client: client}
}

// FindEquipmentNearby finds equipment within a radius of a point (in meters)
func (sq *SpatialQueries) FindEquipmentNearby(ctx context.Context, center spatial.WGS84Coordinate, radiusMeters float64) ([]map[string]interface{}, error) {
	query := `
		SELECT
			e.id, e.path, e.name, e.type, e.status,
			ST_AsGeoJSON(e.position) as geometry,
			ST_Distance(
				e.position::geography,
				ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)::geography
			) as distance_meters,
			b.arxos_id as building_arxos_id,
			b.name as building_name
		FROM equipment e
		JOIN buildings b ON e.building_id = b.id
		WHERE e.position IS NOT NULL
		AND ST_DWithin(
			e.position::geography,
			ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)::geography,
			$4
		)
		ORDER BY distance_meters ASC
	`

	rows, err := sq.client.db.QueryContext(ctx, query,
		center.Longitude, center.Latitude, center.Altitude, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("spatial query failed: %w", err)
	}
	defer rows.Close()

	results := make([]map[string]interface{}, 0)
	for rows.Next() {
		var id, path, name, eqType, status string
		var geometry string
		var distance float64
		var buildingArxosID, buildingName string

		err := rows.Scan(&id, &path, &name, &eqType, &status,
			&geometry, &distance, &buildingArxosID, &buildingName)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		results = append(results, map[string]interface{}{
			"id":                id,
			"path":              path,
			"name":              name,
			"type":              eqType,
			"status":            status,
			"geometry":          geometry,
			"distance_meters":   distance,
			"building_arxos_id": buildingArxosID,
			"building_name":     buildingName,
		})
	}

	return results, nil
}

// FindEquipmentWithinBounds finds equipment within a bounding box
func (sq *SpatialQueries) FindEquipmentWithinBounds(ctx context.Context, minLon, minLat, maxLon, maxLat float64) ([]map[string]interface{}, error) {
	query := `
		SELECT
			e.id, e.path, e.name, e.type, e.status,
			ST_AsGeoJSON(e.position) as geometry,
			b.arxos_id as building_arxos_id,
			b.name as building_name
		FROM equipment e
		JOIN buildings b ON e.building_id = b.id
		WHERE e.position IS NOT NULL
		AND ST_Within(
			e.position,
			ST_MakeEnvelope($1, $2, $3, $4, 4326)
		)
		ORDER BY e.path
	`

	rows, err := sq.client.db.QueryContext(ctx, query, minLon, minLat, maxLon, maxLat)
	if err != nil {
		return nil, fmt.Errorf("bounds query failed: %w", err)
	}
	defer rows.Close()

	results := make([]map[string]interface{}, 0)
	for rows.Next() {
		var id, path, name, eqType, status string
		var geometry string
		var buildingArxosID, buildingName string

		err := rows.Scan(&id, &path, &name, &eqType, &status,
			&geometry, &buildingArxosID, &buildingName)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		results = append(results, map[string]interface{}{
			"id":                id,
			"path":              path,
			"name":              name,
			"type":              eqType,
			"status":            status,
			"geometry":          geometry,
			"building_arxos_id": buildingArxosID,
			"building_name":     buildingName,
		})
	}

	return results, nil
}

// FindEquipmentOnFloor finds equipment within a floor's boundaries
func (sq *SpatialQueries) FindEquipmentOnFloor(ctx context.Context, buildingID, floorNumber string) ([]map[string]interface{}, error) {
	query := `
		SELECT
			e.id, e.path, e.name, e.type, e.status,
			ST_AsGeoJSON(e.position) as geometry,
			f.name as floor_name
		FROM equipment e
		JOIN floors f ON ST_Within(e.position, f.boundary)
		JOIN buildings b ON f.building_id = b.id
		WHERE b.arxos_id = $1 AND f.number = $2
		ORDER BY e.path
	`

	rows, err := sq.client.db.QueryContext(ctx, query, buildingID, floorNumber)
	if err != nil {
		return nil, fmt.Errorf("floor query failed: %w", err)
	}
	defer rows.Close()

	results := make([]map[string]interface{}, 0)
	for rows.Next() {
		var id, path, name, eqType, status string
		var geometry string
		var floorName sql.NullString

		err := rows.Scan(&id, &path, &name, &eqType, &status,
			&geometry, &floorName)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		result := map[string]interface{}{
			"id":       id,
			"path":     path,
			"name":     name,
			"type":     eqType,
			"status":   status,
			"geometry": geometry,
		}

		if floorName.Valid {
			result["floor_name"] = floorName.String
		}

		results = append(results, result)
	}

	return results, nil
}

// FindNearestEquipment finds the N nearest equipment to a point
func (sq *SpatialQueries) FindNearestEquipment(ctx context.Context, center spatial.WGS84Coordinate, limit int) ([]map[string]interface{}, error) {
	query := `
		SELECT
			e.id, e.path, e.name, e.type, e.status,
			ST_AsGeoJSON(e.position) as geometry,
			ST_Distance(
				e.position::geography,
				ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)::geography
			) as distance_meters,
			b.arxos_id as building_arxos_id,
			b.name as building_name
		FROM equipment e
		JOIN buildings b ON e.building_id = b.id
		WHERE e.position IS NOT NULL
		ORDER BY e.position <-> ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)
		LIMIT $4
	`

	rows, err := sq.client.db.QueryContext(ctx, query,
		center.Longitude, center.Latitude, center.Altitude, limit)
	if err != nil {
		return nil, fmt.Errorf("nearest query failed: %w", err)
	}
	defer rows.Close()

	results := make([]map[string]interface{}, 0)
	for rows.Next() {
		var id, path, name, eqType, status string
		var geometry string
		var distance float64
		var buildingArxosID, buildingName string

		err := rows.Scan(&id, &path, &name, &eqType, &status,
			&geometry, &distance, &buildingArxosID, &buildingName)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		results = append(results, map[string]interface{}{
			"id":                id,
			"path":              path,
			"name":              name,
			"type":              eqType,
			"status":            status,
			"geometry":          geometry,
			"distance_meters":   distance,
			"building_arxos_id": buildingArxosID,
			"building_name":     buildingName,
		})
	}

	return results, nil
}

// CalculateCoverage calculates the spatial coverage percentage of a building
func (sq *SpatialQueries) CalculateCoverage(ctx context.Context, buildingID string) (float64, error) {
	// This query calculates what percentage of the building has equipment coverage
	// It's a simplified version - a real implementation would use floor boundaries
	query := `
		WITH building_bounds AS (
			SELECT ST_Envelope(ST_Collect(position)) as envelope
			FROM equipment e
			JOIN buildings b ON e.building_id = b.id
			WHERE b.arxos_id = $1 AND e.position IS NOT NULL
		),
		equipment_coverage AS (
			SELECT ST_Union(ST_Buffer(e.position::geography, 5)::geometry) as coverage
			FROM equipment e
			JOIN buildings b ON e.building_id = b.id
			WHERE b.arxos_id = $1 AND e.position IS NOT NULL
		)
		SELECT
			COALESCE(
				ST_Area(ec.coverage::geography) / NULLIF(ST_Area(bb.envelope::geography), 0) * 100,
				0
			) as coverage_percentage
		FROM building_bounds bb, equipment_coverage ec
	`

	var coverage float64
	err := sq.client.db.QueryRowContext(ctx, query, buildingID).Scan(&coverage)
	if err != nil {
		if err == sql.ErrNoRows {
			return 0, nil
		}
		return 0, fmt.Errorf("coverage query failed: %w", err)
	}

	// Cap at 100%
	if coverage > 100 {
		coverage = 100
	}

	return coverage, nil
}

// CreateSpatialIndices ensures all spatial indices are created
func (sq *SpatialQueries) CreateSpatialIndices(ctx context.Context) error {
	indices := []string{
		// Spatial indices for equipment
		`CREATE INDEX IF NOT EXISTS idx_equipment_position_gist
		 ON equipment USING GIST(position)`,

		`CREATE INDEX IF NOT EXISTS idx_equipment_position_geography
		 ON equipment USING GIST((position::geography))`,

		// Spatial indices for buildings
		`CREATE INDEX IF NOT EXISTS idx_buildings_origin_gist
		 ON buildings USING GIST(origin)`,

		// Spatial indices for floors
		`CREATE INDEX IF NOT EXISTS idx_floors_boundary_gist
		 ON floors USING GIST(boundary)`,

		// Spatial indices for rooms
		`CREATE INDEX IF NOT EXISTS idx_rooms_boundary_gist
		 ON rooms USING GIST(boundary)`,

		// Compound indices for common queries
		`CREATE INDEX IF NOT EXISTS idx_equipment_building_position
		 ON equipment(building_id, position)`,

		`CREATE INDEX IF NOT EXISTS idx_equipment_status_position
		 ON equipment(status) WHERE position IS NOT NULL`,
	}

	for _, idx := range indices {
		if _, err := sq.client.db.ExecContext(ctx, idx); err != nil {
			return fmt.Errorf("failed to create index: %w", err)
		}
	}

	// Analyze tables to update statistics for query planner
	tables := []string{"buildings", "equipment", "floors", "rooms"}
	for _, table := range tables {
		if _, err := sq.client.db.ExecContext(ctx, "ANALYZE "+table); err != nil {
			return fmt.Errorf("failed to analyze table %s: %w", table, err)
		}
	}

	return nil
}
