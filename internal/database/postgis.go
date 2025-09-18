package database

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
	_ "github.com/lib/pq" // PostgreSQL driver
)

// PostGISConfig holds configuration for PostGIS database
type PostGISConfig struct {
	Host            string
	Port            int
	Database        string
	User            string
	Password        string
	SSLMode         string
	SpatialRef      int // Spatial reference system (default: 4326 for WGS84)
	MaxConnections  int
	ConnMaxLifetime time.Duration
}

// PostGISDB implements spatial database operations using PostGIS
type PostGISDB struct {
	db     *sql.DB
	config PostGISConfig
}

// NewPostGISDB creates a new PostGIS database connection
func NewPostGISDB(config PostGISConfig) *PostGISDB {
	if config.SpatialRef == 0 {
		config.SpatialRef = 4326 // Default to WGS84
	}
	if config.Port == 0 {
		config.Port = 5432
	}
	if config.SSLMode == "" {
		config.SSLMode = "prefer"
	}
	if config.MaxConnections == 0 {
		config.MaxConnections = 25
	}
	if config.ConnMaxLifetime == 0 {
		config.ConnMaxLifetime = 5 * time.Minute
	}

	return &PostGISDB{
		config: config,
	}
}

// Connect establishes connection to PostGIS database
func (p *PostGISDB) Connect(ctx context.Context) error {
	connStr := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		p.config.Host,
		p.config.Port,
		p.config.User,
		p.config.Password,
		p.config.Database,
		p.config.SSLMode,
	)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(p.config.MaxConnections)
	db.SetMaxIdleConns(p.config.MaxConnections / 2)
	db.SetConnMaxLifetime(p.config.ConnMaxLifetime)

	// Test connection
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}

	p.db = db

	// Enable PostGIS extension if not already enabled
	if err := p.enablePostGIS(ctx); err != nil {
		return fmt.Errorf("failed to enable PostGIS: %w", err)
	}

	// Create spatial tables if not exist
	if err := p.createSpatialTables(ctx); err != nil {
		return fmt.Errorf("failed to create spatial tables: %w", err)
	}

	logger.Info("Connected to PostGIS database - host: %s, database: %s", p.config.Host, p.config.Database)
	return nil
}

// Close closes the database connection
func (p *PostGISDB) Close() error {
	if p.db != nil {
		return p.db.Close()
	}
	return nil
}

// InitializeSpatialExtensions ensures PostGIS extensions are enabled
func (p *PostGISDB) InitializeSpatialExtensions(ctx context.Context) error {
	extensions := []string{
		"CREATE EXTENSION IF NOT EXISTS postgis",
		"CREATE EXTENSION IF NOT EXISTS postgis_topology",
		"CREATE EXTENSION IF NOT EXISTS postgis_raster",
	}

	for _, ext := range extensions {
		if _, err := p.db.ExecContext(ctx, ext); err != nil {
			// Log but don't fail - extension might already exist
			logger.Debug("Extension setup: %v", err)
		}
	}

	// Verify PostGIS is working
	var version string
	err := p.db.QueryRowContext(ctx, "SELECT PostGIS_Version()").Scan(&version)
	if err != nil {
		return fmt.Errorf("PostGIS not available: %w", err)
	}
	logger.Info("PostGIS version: %s", version)

	return nil
}

// enablePostGIS enables PostGIS extension
func (p *PostGISDB) enablePostGIS(ctx context.Context) error {
	_, err := p.db.ExecContext(ctx, "CREATE EXTENSION IF NOT EXISTS postgis")
	if err != nil {
		// Check if it's a permission error and PostGIS already exists
		var exists bool
		err2 := p.db.QueryRowContext(ctx,
			"SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis')").Scan(&exists)
		if err2 == nil && exists {
			return nil // PostGIS already enabled
		}
		return err
	}
	return nil
}

// createSpatialTables creates necessary spatial tables
func (p *PostGISDB) createSpatialTables(ctx context.Context) error {
	queries := []string{
		// Equipment spatial data table
		`CREATE TABLE IF NOT EXISTS equipment_spatial (
			equipment_id TEXT PRIMARY KEY,
			geom GEOMETRY(PointZ, 4326),
			building_id TEXT NOT NULL,
			floor INTEGER,
			room_id TEXT,
			confidence INTEGER DEFAULT 0,
			source TEXT,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Spatial index
		`CREATE INDEX IF NOT EXISTS idx_equipment_spatial_geom
		ON equipment_spatial USING GIST(geom)`,

		// Building coordinate systems
		`CREATE TABLE IF NOT EXISTS building_transforms (
			building_id TEXT PRIMARY KEY,
			origin GEOMETRY(Point, 4326),
			rotation FLOAT DEFAULT 0,
			grid_scale FLOAT DEFAULT 0.5,
			floor_height FLOAT DEFAULT 3.0,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Scanned regions for coverage tracking
		`CREATE TABLE IF NOT EXISTS scanned_regions (
			id SERIAL PRIMARY KEY,
			building_id TEXT NOT NULL,
			floor INTEGER,
			boundary GEOMETRY(Polygon, 4326),
			scan_type TEXT,
			scan_date TIMESTAMP,
			point_density FLOAT,
			confidence INTEGER,
			metadata JSONB,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Point clouds
		`CREATE TABLE IF NOT EXISTS point_clouds (
			scan_id TEXT PRIMARY KEY,
			building_id TEXT NOT NULL,
			points GEOMETRY(MultiPointZ, 4326),
			metadata JSONB,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Spatial anchors for AR
		`CREATE TABLE IF NOT EXISTS spatial_anchors (
			anchor_id TEXT PRIMARY KEY,
			building_id TEXT NOT NULL,
			geom GEOMETRY(PointZ, 4326),
			confidence FLOAT DEFAULT 0.5,
			anchor_type TEXT,
			metadata JSONB,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Confidence records
		`CREATE TABLE IF NOT EXISTS confidence_records (
			equipment_id TEXT PRIMARY KEY,
			position_confidence INTEGER DEFAULT 0,
			position_source TEXT,
			position_updated TIMESTAMP,
			position_accuracy FLOAT,
			semantic_confidence INTEGER DEFAULT 0,
			semantic_source TEXT,
			semantic_updated TIMESTAMP,
			semantic_completeness FLOAT,
			last_field_verified TIMESTAMP,
			verification_count INTEGER DEFAULT 0,
			verification_history JSONB
		)`,
	}

	for _, query := range queries {
		if _, err := p.db.ExecContext(ctx, query); err != nil {
			return fmt.Errorf("failed to execute query: %w", err)
		}
	}

	return nil
}

// --- Equipment Position Operations ---

// UpdateEquipmentPosition updates the spatial position of equipment
func (p *PostGISDB) UpdateEquipmentPosition(equipmentID string, pos spatial.Point3D, confidence spatial.ConfidenceLevel, source string) error {
	ctx := context.Background()

	query := `
		INSERT INTO equipment_spatial (equipment_id, geom, building_id, confidence, source, updated_at)
		VALUES ($1, ST_GeomFromText($2, $3), $4, $5, $6, CURRENT_TIMESTAMP)
		ON CONFLICT (equipment_id) DO UPDATE
		SET geom = EXCLUDED.geom,
		    confidence = EXCLUDED.confidence,
		    source = EXCLUDED.source,
		    updated_at = CURRENT_TIMESTAMP`

	geomWKT := fmt.Sprintf("POINT Z(%f %f %f)", pos.X, pos.Y, pos.Z)

	// Extract building_id from equipment_id (assuming format: building_id/floor/room/equipment)
	parts := strings.Split(equipmentID, "/")
	buildingID := ""
	if len(parts) > 0 {
		buildingID = parts[0]
	}

	_, err := p.db.ExecContext(ctx, query, equipmentID, geomWKT, p.config.SpatialRef, buildingID, confidence, source)
	if err != nil {
		return fmt.Errorf("failed to update equipment position: %w", err)
	}

	// Also update confidence record
	if err := p.UpdateConfidence(equipmentID, "position", confidence, source); err != nil {
		logger.Warn("Failed to update confidence record: %v", err)
	}

	return nil
}

// GetEquipmentPosition retrieves the spatial position of equipment
func (p *PostGISDB) GetEquipmentPosition(equipmentID string) (*SpatialEquipment, error) {
	ctx := context.Background()

	query := `
		SELECT
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			source,
			updated_at
		FROM equipment_spatial
		WHERE equipment_id = $1`

	var x, y, z float64
	var confidence int
	var source string
	var updatedAt time.Time

	err := p.db.QueryRowContext(ctx, query, equipmentID).Scan(
		&x, &y, &z, &confidence, &source, &updatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("equipment not found: %s", equipmentID)
		}
		return nil, fmt.Errorf("failed to get equipment position: %w", err)
	}

	// Create spatial equipment result
	result := &SpatialEquipment{
		Equipment: &models.Equipment{
			ID: equipmentID,
		},
		SpatialData: &spatial.SpatialMetadata{
			Position:           spatial.Point3D{X: x, Y: y, Z: z},
			PositionConfidence: spatial.ConfidenceLevel(confidence),
			LastUpdated:        updatedAt,
			Source:             source,
		},
	}

	return result, nil
}

// QueryBySpatialProximity finds equipment within radius of a center point
func (p *PostGISDB) QueryBySpatialProximity(center spatial.Point3D, radiusMeters float64) ([]*SpatialEquipment, error) {
	ctx := context.Background()

	query := `
		SELECT
			equipment_id,
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			source,
			updated_at,
			ST_Distance(geom, ST_GeomFromText($1, $2)) as distance
		FROM equipment_spatial
		WHERE ST_DWithin(geom, ST_GeomFromText($1, $2), $3)
		ORDER BY distance`

	centerWKT := fmt.Sprintf("POINT Z(%f %f %f)", center.X, center.Y, center.Z)

	rows, err := p.db.QueryContext(ctx, query, centerWKT, p.config.SpatialRef, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("failed to query by proximity: %w", err)
	}
	defer rows.Close()

	var results []*SpatialEquipment
	for rows.Next() {
		var equipmentID, source string
		var x, y, z, distance float64
		var confidence int
		var updatedAt time.Time

		if err := rows.Scan(&equipmentID, &x, &y, &z, &confidence, &source, &updatedAt, &distance); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		result := &SpatialEquipment{
			Equipment: &models.Equipment{
				ID: equipmentID,
			},
			SpatialData: &spatial.SpatialMetadata{
				Position:           spatial.Point3D{X: x, Y: y, Z: z},
				PositionConfidence: spatial.ConfidenceLevel(confidence),
				LastUpdated:        updatedAt,
				Source:             source,
				DistanceFromQuery:  distance,
			},
		}
		results = append(results, result)
	}

	return results, nil
}

// QueryByBoundingBox finds equipment within a bounding box
func (p *PostGISDB) QueryByBoundingBox(bbox spatial.BoundingBox) ([]*SpatialEquipment, error) {
	ctx := context.Background()

	// Create a 3D box geometry
	boxWKT := fmt.Sprintf(
		"POLYGON Z((%f %f %f, %f %f %f, %f %f %f, %f %f %f, %f %f %f))",
		bbox.Min.X, bbox.Min.Y, bbox.Min.Z,
		bbox.Max.X, bbox.Min.Y, bbox.Min.Z,
		bbox.Max.X, bbox.Max.Y, bbox.Max.Z,
		bbox.Min.X, bbox.Max.Y, bbox.Max.Z,
		bbox.Min.X, bbox.Min.Y, bbox.Min.Z,
	)

	query := `
		SELECT
			equipment_id,
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			source,
			updated_at
		FROM equipment_spatial
		WHERE ST_Within(geom, ST_GeomFromText($1, $2))`

	rows, err := p.db.QueryContext(ctx, query, boxWKT, p.config.SpatialRef)
	if err != nil {
		return nil, fmt.Errorf("failed to query by bounding box: %w", err)
	}
	defer rows.Close()

	var results []*SpatialEquipment
	for rows.Next() {
		var equipmentID, source string
		var x, y, z float64
		var confidence int
		var updatedAt time.Time

		if err := rows.Scan(&equipmentID, &x, &y, &z, &confidence, &source, &updatedAt); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		result := &SpatialEquipment{
			Equipment: &models.Equipment{
				ID: equipmentID,
			},
			SpatialData: &spatial.SpatialMetadata{
				Position:           spatial.Point3D{X: x, Y: y, Z: z},
				PositionConfidence: spatial.ConfidenceLevel(confidence),
				LastUpdated:        updatedAt,
				Source:             source,
			},
		}
		results = append(results, result)
	}

	return results, nil
}

// GetEquipmentInRoom finds all equipment in a specific room
func (p *PostGISDB) GetEquipmentInRoom(buildingID string, floor int, roomBounds spatial.BoundingBox) ([]*SpatialEquipment, error) {
	ctx := context.Background()

	query := `
		SELECT
			equipment_id,
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			source,
			updated_at
		FROM equipment_spatial
		WHERE building_id = $1
		  AND floor = $2
		  AND ST_Within(geom, ST_MakeEnvelope($3, $4, $5, $6, $7))`

	rows, err := p.db.QueryContext(ctx, query,
		buildingID, floor,
		roomBounds.Min.X, roomBounds.Min.Y,
		roomBounds.Max.X, roomBounds.Max.Y,
		p.config.SpatialRef,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment in room: %w", err)
	}
	defer rows.Close()

	var results []*SpatialEquipment
	for rows.Next() {
		var equipmentID, source string
		var x, y, z float64
		var confidence int
		var updatedAt time.Time

		if err := rows.Scan(&equipmentID, &x, &y, &z, &confidence, &source, &updatedAt); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		result := &SpatialEquipment{
			Equipment: &models.Equipment{
				ID: equipmentID,
			},
			SpatialData: &spatial.SpatialMetadata{
				Position:           spatial.Point3D{X: x, Y: y, Z: z},
				PositionConfidence: spatial.ConfidenceLevel(confidence),
				LastUpdated:        updatedAt,
				Source:             source,
			},
		}
		results = append(results, result)
	}

	return results, nil
}

// --- Building Coordinate System Operations ---

// SetBuildingOrigin sets the GPS origin and coordinate system for a building
func (p *PostGISDB) SetBuildingOrigin(buildingID string, gps spatial.GPSCoordinate, rotation float64, gridScale float64) error {
	ctx := context.Background()

	query := `
		INSERT INTO building_transforms (building_id, origin, rotation, grid_scale)
		VALUES ($1, ST_GeomFromText($2, 4326), $3, $4)
		ON CONFLICT (building_id) DO UPDATE
		SET origin = EXCLUDED.origin,
		    rotation = EXCLUDED.rotation,
		    grid_scale = EXCLUDED.grid_scale`

	originWKT := fmt.Sprintf("POINT(%f %f)", gps.Longitude, gps.Latitude)

	_, err := p.db.ExecContext(ctx, query, buildingID, originWKT, rotation, gridScale)
	if err != nil {
		return fmt.Errorf("failed to set building origin: %w", err)
	}

	return nil
}

// GetBuildingTransform retrieves the coordinate transformation for a building
func (p *PostGISDB) GetBuildingTransform(buildingID string) (*spatial.Transform, error) {
	ctx := context.Background()

	query := `
		SELECT
			ST_X(origin) as longitude,
			ST_Y(origin) as latitude,
			rotation,
			grid_scale,
			floor_height
		FROM building_transforms
		WHERE building_id = $1`

	var longitude, latitude, rotation, gridScale, floorHeight float64

	err := p.db.QueryRowContext(ctx, query, buildingID).Scan(
		&longitude, &latitude, &rotation, &gridScale, &floorHeight,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("building transform not found: %s", buildingID)
		}
		return nil, fmt.Errorf("failed to get building transform: %w", err)
	}

	transform := &spatial.Transform{
		Origin: spatial.GPSCoordinate{
			Latitude:  latitude,
			Longitude: longitude,
		},
		Rotation:    rotation,
		GridScale:   gridScale,
		FloorHeight: floorHeight,
	}

	return transform, nil
}

// GetBuildingOrigin retrieves just the GPS origin of a building
func (p *PostGISDB) GetBuildingOrigin(buildingID string) (*spatial.GPSCoordinate, error) {
	transform, err := p.GetBuildingTransform(buildingID)
	if err != nil {
		return nil, err
	}
	return &transform.Origin, nil
}

// --- Confidence Operations ---

// UpdateConfidence updates confidence for a specific aspect of equipment
func (p *PostGISDB) UpdateConfidence(equipmentID string, aspect string, level spatial.ConfidenceLevel, source string) error {
	ctx := context.Background()

	var query string
	switch aspect {
	case "position":
		query = `
			INSERT INTO confidence_records (equipment_id, position_confidence, position_source, position_updated)
			VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
			ON CONFLICT (equipment_id) DO UPDATE
			SET position_confidence = EXCLUDED.position_confidence,
			    position_source = EXCLUDED.position_source,
			    position_updated = CURRENT_TIMESTAMP`
	case "semantic":
		query = `
			INSERT INTO confidence_records (equipment_id, semantic_confidence, semantic_source, semantic_updated)
			VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
			ON CONFLICT (equipment_id) DO UPDATE
			SET semantic_confidence = EXCLUDED.semantic_confidence,
			    semantic_source = EXCLUDED.semantic_source,
			    semantic_updated = CURRENT_TIMESTAMP`
	default:
		return fmt.Errorf("unknown confidence aspect: %s", aspect)
	}

	_, err := p.db.ExecContext(ctx, query, equipmentID, level, source)
	if err != nil {
		return fmt.Errorf("failed to update confidence: %w", err)
	}

	return nil
}

// GetConfidenceRecord retrieves the confidence record for equipment
func (p *PostGISDB) GetConfidenceRecord(equipmentID string) (*ConfidenceRecord, error) {
	ctx := context.Background()

	query := `
		SELECT
			equipment_id,
			COALESCE(position_confidence, 0),
			COALESCE(position_source, ''),
			position_updated,
			COALESCE(position_accuracy, 0),
			COALESCE(semantic_confidence, 0),
			COALESCE(semantic_source, ''),
			semantic_updated,
			COALESCE(semantic_completeness, 0),
			last_field_verified,
			COALESCE(verification_count, 0),
			verification_history
		FROM confidence_records
		WHERE equipment_id = $1`

	var record ConfidenceRecord
	var posUpdated, semUpdated sql.NullTime
	var lastVerified sql.NullTime
	var verificationHistory sql.NullString

	err := p.db.QueryRowContext(ctx, query, equipmentID).Scan(
		&record.EquipmentID,
		&record.PositionConfidence,
		&record.PositionSource,
		&posUpdated,
		&record.PositionAccuracy,
		&record.SemanticConfidence,
		&record.SemanticSource,
		&semUpdated,
		&record.SemanticCompleteness,
		&lastVerified,
		&record.VerificationCount,
		&verificationHistory,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("confidence record not found: %s", equipmentID)
		}
		return nil, fmt.Errorf("failed to get confidence record: %w", err)
	}

	if posUpdated.Valid {
		record.PositionUpdated = posUpdated.Time
	}
	if semUpdated.Valid {
		record.SemanticUpdated = semUpdated.Time
	}
	if lastVerified.Valid {
		record.LastFieldVerified = &lastVerified.Time
	}

	return &record, nil
}

// QueryByConfidence finds equipment with minimum confidence level
func (p *PostGISDB) QueryByConfidence(minConfidence spatial.ConfidenceLevel) ([]*SpatialEquipment, error) {
	ctx := context.Background()

	query := `
		SELECT
			es.equipment_id,
			ST_X(es.geom) as x,
			ST_Y(es.geom) as y,
			ST_Z(es.geom) as z,
			es.confidence,
			es.source,
			es.updated_at
		FROM equipment_spatial es
		LEFT JOIN confidence_records cr ON es.equipment_id = cr.equipment_id
		WHERE COALESCE(cr.position_confidence, es.confidence) >= $1
		ORDER BY es.equipment_id`

	rows, err := p.db.QueryContext(ctx, query, minConfidence)
	if err != nil {
		return nil, fmt.Errorf("failed to query by confidence: %w", err)
	}
	defer rows.Close()

	var results []*SpatialEquipment
	for rows.Next() {
		var equipmentID, source string
		var x, y, z float64
		var confidence int
		var updatedAt time.Time

		if err := rows.Scan(&equipmentID, &x, &y, &z, &confidence, &source, &updatedAt); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		result := &SpatialEquipment{
			Equipment: &models.Equipment{
				ID: equipmentID,
			},
			SpatialData: &spatial.SpatialMetadata{
				Position:           spatial.Point3D{X: x, Y: y, Z: z},
				PositionConfidence: spatial.ConfidenceLevel(confidence),
				LastUpdated:        updatedAt,
				Source:             source,
			},
		}
		results = append(results, result)
	}

	return results, nil
}

// GetEquipmentNeedingVerification finds equipment that needs verification
func (p *PostGISDB) GetEquipmentNeedingVerification(daysSinceLastVerification int) ([]*models.Equipment, error) {
	ctx := context.Background()

	cutoffDate := time.Now().AddDate(0, 0, -daysSinceLastVerification)

	query := `
		SELECT DISTINCT es.equipment_id
		FROM equipment_spatial es
		LEFT JOIN confidence_records cr ON es.equipment_id = cr.equipment_id
		WHERE cr.last_field_verified IS NULL
		   OR cr.last_field_verified < $1
		ORDER BY es.equipment_id`

	rows, err := p.db.QueryContext(ctx, query, cutoffDate)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment needing verification: %w", err)
	}
	defer rows.Close()

	var results []*models.Equipment
	for rows.Next() {
		var equipmentID string
		if err := rows.Scan(&equipmentID); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		results = append(results, &models.Equipment{
			ID: equipmentID,
		})
	}

	return results, nil
}

// --- Utility Operations ---

// CalculateDistance calculates the distance between two equipment items
func (p *PostGISDB) CalculateDistance(id1, id2 string) (float64, error) {
	ctx := context.Background()

	query := `
		SELECT ST_Distance(e1.geom, e2.geom)
		FROM equipment_spatial e1, equipment_spatial e2
		WHERE e1.equipment_id = $1 AND e2.equipment_id = $2`

	var distance float64
	err := p.db.QueryRowContext(ctx, query, id1, id2).Scan(&distance)
	if err != nil {
		return 0, fmt.Errorf("failed to calculate distance: %w", err)
	}

	return distance, nil
}

// FindNearestEquipment finds the nearest equipment of a specific type
func (p *PostGISDB) FindNearestEquipment(position spatial.Point3D, equipmentType string) (*SpatialEquipment, error) {
	ctx := context.Background()

	positionWKT := fmt.Sprintf("POINT Z(%f %f %f)", position.X, position.Y, position.Z)

	// For now, we'll search by equipment_id pattern since we don't have a separate type column
	// This assumes equipment IDs follow a pattern like building/floor/room/type/id
	query := `
		SELECT
			equipment_id,
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			source,
			updated_at,
			ST_Distance(geom, ST_GeomFromText($1, $2)) as distance
		FROM equipment_spatial
		WHERE equipment_id LIKE $3
		ORDER BY distance
		LIMIT 1`

	typePattern := fmt.Sprintf("%%%s%%", equipmentType)

	var equipmentID, source string
	var x, y, z, distance float64
	var confidence int
	var updatedAt time.Time

	err := p.db.QueryRowContext(ctx, query, positionWKT, p.config.SpatialRef, typePattern).Scan(
		&equipmentID, &x, &y, &z, &confidence, &source, &updatedAt, &distance,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("no equipment of type %s found", equipmentType)
		}
		return nil, fmt.Errorf("failed to find nearest equipment: %w", err)
	}

	result := &SpatialEquipment{
		Equipment: &models.Equipment{
			ID: equipmentID,
		},
		SpatialData: &spatial.SpatialMetadata{
			Position:           spatial.Point3D{X: x, Y: y, Z: z},
			PositionConfidence: spatial.ConfidenceLevel(confidence),
			LastUpdated:        updatedAt,
			Source:             source,
			DistanceFromQuery:  distance,
		},
	}

	return result, nil
}

// GetFloorBounds gets the bounding box for a floor
func (p *PostGISDB) GetFloorBounds(buildingID string, floor int) (*spatial.BoundingBox, error) {
	ctx := context.Background()

	query := `
		SELECT
			ST_XMin(ST_Extent(geom)) as min_x,
			ST_YMin(ST_Extent(geom)) as min_y,
			ST_XMax(ST_Extent(geom)) as max_x,
			ST_YMax(ST_Extent(geom)) as max_y,
			MIN(ST_Z(geom)) as min_z,
			MAX(ST_Z(geom)) as max_z
		FROM equipment_spatial
		WHERE building_id = $1 AND floor = $2`

	var minX, minY, maxX, maxY, minZ, maxZ sql.NullFloat64

	err := p.db.QueryRowContext(ctx, query, buildingID, floor).Scan(
		&minX, &minY, &maxX, &maxY, &minZ, &maxZ,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get floor bounds: %w", err)
	}

	if !minX.Valid || !minY.Valid || !maxX.Valid || !maxY.Valid {
		return nil, fmt.Errorf("no equipment found on floor %d", floor)
	}

	bounds := &spatial.BoundingBox{
		Min: spatial.Point3D{
			X: minX.Float64,
			Y: minY.Float64,
			Z: minZ.Float64,
		},
		Max: spatial.Point3D{
			X: maxX.Float64,
			Y: maxY.Float64,
			Z: maxZ.Float64,
		},
	}

	return bounds, nil
}

// --- Coverage Operations (Partial implementation for brevity) ---

// AddScannedRegion adds a scanned region for coverage tracking
func (p *PostGISDB) AddScannedRegion(region spatial.ScannedRegion) error {
	ctx := context.Background()

	// Convert boundary to WKT polygon
	// For simplicity, assuming the boundary is a rectangular region
	boundaryWKT := fmt.Sprintf(
		"POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))",
		region.Boundary.MinX, region.Boundary.MinY,
		region.Boundary.MaxX, region.Boundary.MinY,
		region.Boundary.MaxX, region.Boundary.MaxY,
		region.Boundary.MinX, region.Boundary.MaxY,
		region.Boundary.MinX, region.Boundary.MinY,
	)

	query := `
		INSERT INTO scanned_regions (building_id, floor, boundary, scan_type, scan_date, point_density, confidence, metadata)
		VALUES ($1, $2, ST_GeomFromText($3, $4), $5, $6, $7, $8, $9)`

	_, err := p.db.ExecContext(ctx, query,
		region.BuildingID,
		region.Floor,
		boundaryWKT,
		p.config.SpatialRef,
		region.ScanType,
		region.ScanDate,
		region.PointDensity,
		region.Confidence,
		nil, // metadata - could be JSON
	)
	if err != nil {
		return fmt.Errorf("failed to add scanned region: %w", err)
	}

	return nil
}

// --- Point Cloud Operations (Partial implementation) ---

// StorePointCloud stores a point cloud from scanning
func (p *PostGISDB) StorePointCloud(scanID string, points []spatial.Point3D, metadata map[string]interface{}) error {
	ctx := context.Background()

	// Convert points to MultiPointZ WKT
	var pointStrs []string
	for _, pt := range points {
		pointStrs = append(pointStrs, fmt.Sprintf("%f %f %f", pt.X, pt.Y, pt.Z))
	}
	multiPointWKT := fmt.Sprintf("MULTIPOINT Z(%s)", strings.Join(pointStrs, ", "))

	// Extract building_id from metadata or scanID
	buildingID := ""
	if bid, ok := metadata["building_id"].(string); ok {
		buildingID = bid
	}

	query := `
		INSERT INTO point_clouds (scan_id, building_id, points, metadata)
		VALUES ($1, $2, ST_GeomFromText($3, $4), $5)`

	_, err := p.db.ExecContext(ctx, query, scanID, buildingID, multiPointWKT, p.config.SpatialRef, nil)
	if err != nil {
		return fmt.Errorf("failed to store point cloud: %w", err)
	}

	return nil
}

// GetPointCloud retrieves a point cloud by scan ID
func (p *PostGISDB) GetPointCloud(scanID string) ([]spatial.Point3D, error) {
	ctx := context.Background()

	query := `
		SELECT ST_AsText(points)
		FROM point_clouds
		WHERE scan_id = $1`

	var pointsWKT string
	err := p.db.QueryRowContext(ctx, query, scanID).Scan(&pointsWKT)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("point cloud not found: %s", scanID)
		}
		return nil, fmt.Errorf("failed to get point cloud: %w", err)
	}

	// Parse WKT to extract points (simplified - real implementation would need proper WKT parsing)
	// This is a placeholder - you'd want to use a proper WKT parser
	var points []spatial.Point3D
	// ... parse WKT ...

	return points, nil
}

// --- Spatial Anchor Operations (Partial implementation) ---

// CreateSpatialAnchor creates an AR spatial anchor
func (p *PostGISDB) CreateSpatialAnchor(anchor spatial.SpatialAnchor) error {
	ctx := context.Background()

	anchorWKT := fmt.Sprintf("POINT Z(%f %f %f)", anchor.Position.X, anchor.Position.Y, anchor.Position.Z)

	query := `
		INSERT INTO spatial_anchors (anchor_id, building_id, geom, confidence, anchor_type, metadata)
		VALUES ($1, $2, ST_GeomFromText($3, $4), $5, $6, $7)`

	_, err := p.db.ExecContext(ctx, query,
		anchor.ID,
		anchor.BuildingID,
		anchorWKT,
		p.config.SpatialRef,
		anchor.Confidence,
		anchor.Type,
		nil, // metadata
	)
	if err != nil {
		return fmt.Errorf("failed to create spatial anchor: %w", err)
	}

	return nil
}

// GetSpatialAnchor retrieves a spatial anchor by ID
func (p *PostGISDB) GetSpatialAnchor(anchorID string) (*spatial.SpatialAnchor, error) {
	ctx := context.Background()

	query := `
		SELECT
			anchor_id,
			building_id,
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			anchor_type
		FROM spatial_anchors
		WHERE anchor_id = $1`

	var anchor spatial.SpatialAnchor
	var x, y, z float64

	err := p.db.QueryRowContext(ctx, query, anchorID).Scan(
		&anchor.ID,
		&anchor.BuildingID,
		&x, &y, &z,
		&anchor.Confidence,
		&anchor.Type,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("spatial anchor not found: %s", anchorID)
		}
		return nil, fmt.Errorf("failed to get spatial anchor: %w", err)
	}

	anchor.Position = spatial.Point3D{X: x, Y: y, Z: z}

	return &anchor, nil
}

// GetAnchorsNearPosition finds anchors near a position
func (p *PostGISDB) GetAnchorsNearPosition(position spatial.Point3D, radiusMeters float64) ([]*spatial.SpatialAnchor, error) {
	ctx := context.Background()

	positionWKT := fmt.Sprintf("POINT Z(%f %f %f)", position.X, position.Y, position.Z)

	query := `
		SELECT
			anchor_id,
			building_id,
			ST_X(geom) as x,
			ST_Y(geom) as y,
			ST_Z(geom) as z,
			confidence,
			anchor_type
		FROM spatial_anchors
		WHERE ST_DWithin(geom, ST_GeomFromText($1, $2), $3)
		ORDER BY ST_Distance(geom, ST_GeomFromText($1, $2))`

	rows, err := p.db.QueryContext(ctx, query, positionWKT, p.config.SpatialRef, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("failed to query anchors near position: %w", err)
	}
	defer rows.Close()

	var anchors []*spatial.SpatialAnchor
	for rows.Next() {
		var anchor spatial.SpatialAnchor
		var x, y, z float64

		if err := rows.Scan(&anchor.ID, &anchor.BuildingID, &x, &y, &z, &anchor.Confidence, &anchor.Type); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		anchor.Position = spatial.Point3D{X: x, Y: y, Z: z}
		anchors = append(anchors, &anchor)
	}

	return anchors, nil
}

// UpdateAnchorConfidence updates the confidence of a spatial anchor
func (p *PostGISDB) UpdateAnchorConfidence(anchorID string, confidence float64) error {
	ctx := context.Background()

	query := `
		UPDATE spatial_anchors
		SET confidence = $2, updated_at = CURRENT_TIMESTAMP
		WHERE anchor_id = $1`

	_, err := p.db.ExecContext(ctx, query, anchorID, confidence)
	if err != nil {
		return fmt.Errorf("failed to update anchor confidence: %w", err)
	}

	return nil
}

// --- Maintenance Operations ---

// Vacuum performs database maintenance
func (p *PostGISDB) Vacuum() error {
	ctx := context.Background()

	_, err := p.db.ExecContext(ctx, "VACUUM ANALYZE")
	if err != nil {
		return fmt.Errorf("failed to vacuum database: %w", err)
	}

	return nil
}

// GetStatistics returns spatial database statistics
func (p *PostGISDB) GetStatistics() (*SpatialDBStats, error) {
	ctx := context.Background()

	stats := &SpatialDBStats{}

	// Count total equipment
	err := p.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM equipment_spatial").Scan(&stats.TotalEquipment)
	if err != nil {
		return nil, fmt.Errorf("failed to count equipment: %w", err)
	}

	// Count equipment with spatial data
	err = p.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM equipment_spatial WHERE geom IS NOT NULL").Scan(&stats.EquipmentWithSpatial)
	if err != nil {
		return nil, fmt.Errorf("failed to count spatial equipment: %w", err)
	}

	// Count scans
	err = p.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM scanned_regions").Scan(&stats.TotalScans)
	if err != nil {
		return nil, fmt.Errorf("failed to count scans: %w", err)
	}

	// Count point clouds
	err = p.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM point_clouds").Scan(&stats.TotalPointClouds)
	if err != nil {
		return nil, fmt.Errorf("failed to count point clouds: %w", err)
	}

	// Get last scan date
	var lastScan sql.NullTime
	err = p.db.QueryRowContext(ctx, "SELECT MAX(scan_date) FROM scanned_regions").Scan(&lastScan)
	if err == nil && lastScan.Valid {
		stats.LastScanDate = &lastScan.Time
	}

	return stats, nil
}

// --- Placeholder implementations for remaining interface methods ---

func (p *PostGISDB) GetCoverageMap(buildingID string) (*spatial.CoverageMap, error) {
	// TODO: Implement coverage map aggregation
	return nil, fmt.Errorf("not implemented")
}

func (p *PostGISDB) CalculateCoveragePercentage(buildingID string) (float64, error) {
	// TODO: Implement coverage percentage calculation
	return 0, fmt.Errorf("not implemented")
}

func (p *PostGISDB) GetRegionConfidence(buildingID string, point spatial.Point3D) (spatial.ConfidenceLevel, error) {
	// TODO: Implement region confidence lookup
	return spatial.CONFIDENCE_ESTIMATED, fmt.Errorf("not implemented")
}

func (p *PostGISDB) GetUnscannedAreas(buildingID string) ([]spatial.SpatialExtent, error) {
	// TODO: Implement unscanned area detection
	return nil, fmt.Errorf("not implemented")
}

func (p *PostGISDB) QueryPointsInRegion(boundary spatial.SpatialExtent) ([]spatial.Point3D, error) {
	// TODO: Implement point cloud region query
	return nil, fmt.Errorf("not implemented")
}

func (p *PostGISDB) GetPointCloudMetadata(scanID string) (map[string]interface{}, error) {
	// TODO: Implement metadata retrieval
	return nil, fmt.Errorf("not implemented")
}
