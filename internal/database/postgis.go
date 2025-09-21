package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
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
	db               *sql.DB
	config           PostGISConfig
	connStr          string // Optional connection string override
	spatialOptimizer *SpatialIndexOptimizer
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

// NewPostGISConnection creates and connects to PostGIS database
func NewPostGISConnection(ctx context.Context) (*PostGISDB, error) {
	// Get connection string from environment
	connStr := os.Getenv("DATABASE_URL")
	if connStr == "" {
		connStr = os.Getenv("ARXOS_DATABASE_URL")
	}
	if connStr == "" {
		// Use default development connection
		connStr = "host=localhost port=5432 user=arxos password=arxos dbname=arxos sslmode=disable"
	}

	// Parse connection string to extract components
	// For simplicity, we'll use the connection string directly in Connect
	config := PostGISConfig{
		Host:            "localhost",
		Port:            5432,
		Database:        "arxos",
		User:            "arxos",
		Password:        "arxos",
		SSLMode:         "disable",
		MaxConnections:  25,
		ConnMaxLifetime: 30 * time.Minute,
		SpatialRef:      4326,
	}

	db := NewPostGISDB(config)
	// Override the connection string
	db.connStr = connStr
	if err := db.connectWithString(ctx, connStr); err != nil {
		return nil, err
	}

	return db, nil
}

// connectWithString establishes connection using provided connection string
func (p *PostGISDB) connectWithString(ctx context.Context, connStr string) error {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(p.config.MaxConnections)
	db.SetMaxIdleConns(p.config.MaxConnections / 4)
	db.SetConnMaxLifetime(p.config.ConnMaxLifetime)

	// Test connection
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}

	p.db = db

	// Initialize PostGIS extensions
	if err := p.initPostGIS(ctx); err != nil {
		p.db.Close()
		return fmt.Errorf("failed to initialize PostGIS: %w", err)
	}

	logger.Info("Connected to PostGIS database")
	return nil
}

// initPostGIS initializes PostGIS extensions
func (p *PostGISDB) initPostGIS(ctx context.Context) error {
	// Check if PostGIS extension exists
	var exists bool
	err := p.db.QueryRowContext(ctx,
		"SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis')").Scan(&exists)
	if err != nil {
		return fmt.Errorf("failed to check PostGIS extension: %w", err)
	}

	if !exists {
		// Try to create PostGIS extension
		_, err = p.db.ExecContext(ctx, "CREATE EXTENSION IF NOT EXISTS postgis")
		if err != nil {
			logger.Warn("Could not create PostGIS extension (may require superuser): %v", err)
			// Continue anyway - the extension might be installed at database level
		}
	}

	// Create spatial tables if they don't exist
	if err := p.createSpatialTables(ctx); err != nil {
		return fmt.Errorf("failed to create spatial tables: %w", err)
	}

	return nil
}

// InitializeSpatialOptimizer initializes the spatial index optimizer
func (p *PostGISDB) InitializeSpatialOptimizer(ctx context.Context) error {
	if p.spatialOptimizer == nil {
		p.spatialOptimizer = NewSpatialIndexOptimizer(p)
	}

	// Run initial optimization
	if err := p.spatialOptimizer.OptimizeIndices(ctx); err != nil {
		return fmt.Errorf("failed to optimize spatial indices: %w", err)
	}

	return nil
}

// GetSpatialOptimizer returns the spatial index optimizer
func (p *PostGISDB) GetSpatialOptimizer() *SpatialIndexOptimizer {
	if p.spatialOptimizer == nil {
		p.spatialOptimizer = NewSpatialIndexOptimizer(p)
	}
	return p.spatialOptimizer
}

// Close closes the database connection
func (p *PostGISDB) Close() error {
	if p.db != nil {
		return p.db.Close()
	}
	return nil
}

// Query executes a query that returns rows
func (p *PostGISDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return p.db.QueryContext(ctx, query, args...)
}

// QueryRow executes a query that returns at most one row
func (p *PostGISDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return p.db.QueryRowContext(ctx, query, args...)
}

// Exec executes a query without returning any rows
func (p *PostGISDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return p.db.ExecContext(ctx, query, args...)
}

// Connect establishes connection with path parameter (for interface compatibility)
func (p *PostGISDB) Connect(ctx context.Context, dbPath string) error {
	// Ignore dbPath for PostGIS - use configured connection
	return p.ConnectToPostGIS(ctx)
}

// ConnectToPostGIS establishes connection to PostGIS database
func (p *PostGISDB) ConnectToPostGIS(ctx context.Context) error {
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
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Query for coverage data
	query := `
		SELECT
			floor_number,
			ST_AsGeoJSON(ST_ConvexHull(ST_Collect(location))) as coverage_area,
			COUNT(*) as point_count,
			AVG(confidence_score) as avg_confidence
		FROM point_cloud
		WHERE building_id = $1 AND location IS NOT NULL
		GROUP BY floor_number
		ORDER BY floor_number`

	rows, err := p.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to query coverage map: %w", err)
	}
	defer rows.Close()

	coverageMap := &spatial.CoverageMap{
		BuildingID:     buildingID,
		ScannedRegions: make([]spatial.ScannedRegion, 0),
		LastUpdated:    time.Now(),
	}

	for rows.Next() {
		var floorNum int
		var coverageGeoJSON sql.NullString
		var pointCount int
		var avgConfidence sql.NullFloat64

		if err := rows.Scan(&floorNum, &coverageGeoJSON, &pointCount, &avgConfidence); err != nil {
			continue
		}

		scannedRegion := spatial.ScannedRegion{
			ID:         fmt.Sprintf("%s-floor-%d", buildingID, floorNum),
			BuildingID: buildingID,
			Floor:      floorNum,
			ScanDate:   time.Now(),
			ScanType:   "mixed",
			Confidence: avgConfidence.Float64,
		}

		coverageMap.ScannedRegions = append(coverageMap.ScannedRegions, scannedRegion)
	}

	return coverageMap, nil
}

func (p *PostGISDB) CalculateCoveragePercentage(buildingID string) (float64, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Calculate coverage as ratio of scanned area to total building area
	query := `
		WITH building_bounds AS (
			SELECT ST_Area(ST_ConvexHull(ST_Collect(location))) as total_area
			FROM equipment
			WHERE building_id = $1 AND location IS NOT NULL
		),
		scanned_area AS (
			SELECT ST_Area(ST_ConvexHull(ST_Collect(location))) as covered_area
			FROM point_cloud
			WHERE building_id = $1 AND location IS NOT NULL
				AND confidence_score > 0.5
		)
		SELECT
			CASE
				WHEN b.total_area > 0 THEN (s.covered_area / b.total_area) * 100
				ELSE 0
			END as coverage_percentage
		FROM building_bounds b, scanned_area s`

	var percentage sql.NullFloat64
	err := p.db.QueryRowContext(ctx, query, buildingID).Scan(&percentage)
	if err != nil {
		return 0, fmt.Errorf("failed to calculate coverage: %w", err)
	}

	return percentage.Float64, nil
}

func (p *PostGISDB) GetRegionConfidence(buildingID string, point spatial.Point3D) (spatial.ConfidenceLevel, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Find average confidence score for points near the given location
	query := `
		SELECT AVG(confidence_score) as avg_confidence
		FROM point_cloud
		WHERE building_id = $1
			AND ST_DWithin(
				location,
				ST_SetSRID(ST_MakePoint($2, $3, $4), 4326),
				5.0  -- 5 meter radius
			)`

	var avgConfidence sql.NullFloat64
	err := p.db.QueryRowContext(ctx, query, buildingID, point.X, point.Y, point.Z).Scan(&avgConfidence)
	if err != nil || !avgConfidence.Valid {
		return spatial.CONFIDENCE_ESTIMATED, nil
	}

	// Map confidence score to level
	switch {
	case avgConfidence.Float64 >= 0.9:
		return spatial.CONFIDENCE_HIGH, nil
	case avgConfidence.Float64 >= 0.7:
		return spatial.CONFIDENCE_MEDIUM, nil
	case avgConfidence.Float64 >= 0.5:
		return spatial.CONFIDENCE_LOW, nil
	default:
		return spatial.CONFIDENCE_ESTIMATED, nil
	}
}

func (p *PostGISDB) GetUnscannedAreas(buildingID string) ([]spatial.SpatialExtent, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Find areas within building bounds that have no scan coverage
	query := `
		WITH building_envelope AS (
			SELECT
				floor_number,
				ST_ConvexHull(ST_Collect(location)) as envelope
			FROM equipment
			WHERE building_id = $1 AND location IS NOT NULL
			GROUP BY floor_number
		),
		scanned_areas AS (
			SELECT
				floor_number,
				ST_ConvexHull(ST_Collect(ST_Buffer(location, 2))) as coverage
			FROM point_cloud
			WHERE building_id = $1 AND location IS NOT NULL
				AND confidence_score > 0.5
			GROUP BY floor_number
		)
		SELECT
			b.floor_number,
			ST_AsText(ST_Difference(b.envelope, COALESCE(s.coverage, 'POLYGON EMPTY'::geometry))) as unscanned
		FROM building_envelope b
		LEFT JOIN scanned_areas s ON b.floor_number = s.floor_number
		WHERE ST_Area(ST_Difference(b.envelope, COALESCE(s.coverage, 'POLYGON EMPTY'::geometry))) > 1`

	rows, err := p.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to find unscanned areas: %w", err)
	}
	defer rows.Close()

	var unscannedAreas []spatial.SpatialExtent
	for rows.Next() {
		var floorNumber int
		var unscannedWKT string

		if err := rows.Scan(&floorNumber, &unscannedWKT); err != nil {
			continue
		}

		// Parse WKT to extract bounds
		// For simplicity, we'll create a bounding box from the WKT
		extent := spatial.SpatialExtent{
			MinX:  0,  // Would parse from WKT
			MaxX:  100,
			MinY:  0,
			MaxY:  100,
			MinZ:  float64(floorNumber) * 3.0,
			MaxZ:  float64(floorNumber)*3.0 + 3.0,
		}
		unscannedAreas = append(unscannedAreas, extent)
	}

	return unscannedAreas, nil
}

func (p *PostGISDB) QueryPointsInRegion(boundary spatial.SpatialExtent) ([]spatial.Point3D, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Query points within the specified boundary
	query := `
		SELECT
			ST_X(location) as x,
			ST_Y(location) as y,
			ST_Z(location) as z
		FROM point_cloud
		WHERE location && ST_MakeEnvelope($1, $2, $3, $4, 4326)
			AND ST_Z(location) >= $5 AND ST_Z(location) <= $6
		LIMIT 10000`  // Limit for performance

	rows, err := p.db.QueryContext(ctx, query,
		boundary.MinX, boundary.MinY,
		boundary.MaxX, boundary.MaxY,
		boundary.MinZ, boundary.MaxZ)
	if err != nil {
		return nil, fmt.Errorf("failed to query points: %w", err)
	}
	defer rows.Close()

	var points []spatial.Point3D
	for rows.Next() {
		var x, y, z sql.NullFloat64
		if err := rows.Scan(&x, &y, &z); err != nil {
			continue
		}

		if x.Valid && y.Valid && z.Valid {
			points = append(points, spatial.Point3D{
				X: x.Float64,
				Y: y.Float64,
				Z: z.Float64,
			})
		}
	}

	return points, nil
}

func (p *PostGISDB) GetPointCloudMetadata(scanID string) (map[string]interface{}, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Retrieve metadata for a scan
	query := `
		SELECT
			COUNT(*) as point_count,
			MIN(timestamp) as scan_start,
			MAX(timestamp) as scan_end,
			AVG(confidence_score) as avg_confidence,
			MIN(confidence_score) as min_confidence,
			MAX(confidence_score) as max_confidence,
			ST_XMin(ST_Collect(location)) as min_x,
			ST_XMax(ST_Collect(location)) as max_x,
			ST_YMin(ST_Collect(location)) as min_y,
			ST_YMax(ST_Collect(location)) as max_y,
			MIN(ST_Z(location)) as min_z,
			MAX(ST_Z(location)) as max_z
		FROM point_cloud
		WHERE scan_id = $1`

	var pointCount int
	var scanStart, scanEnd sql.NullTime
	var avgConf, minConf, maxConf sql.NullFloat64
	var minX, maxX, minY, maxY, minZ, maxZ sql.NullFloat64

	err := p.db.QueryRowContext(ctx, query, scanID).Scan(
		&pointCount, &scanStart, &scanEnd,
		&avgConf, &minConf, &maxConf,
		&minX, &maxX, &minY, &maxY, &minZ, &maxZ,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get metadata: %w", err)
	}

	metadata := map[string]interface{}{
		"scan_id":           scanID,
		"point_count":       pointCount,
		"scan_start":        scanStart.Time,
		"scan_end":          scanEnd.Time,
		"avg_confidence":    avgConf.Float64,
		"min_confidence":    minConf.Float64,
		"max_confidence":    maxConf.Float64,
		"bounding_box": map[string]float64{
			"min_x": minX.Float64,
			"max_x": maxX.Float64,
			"min_y": minY.Float64,
			"max_y": maxY.Float64,
			"min_z": minZ.Float64,
			"max_z": maxZ.Float64,
		},
	}

	return metadata, nil
}

// GetFloorPlan retrieves a floor plan by ID
func (p *PostGISDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	query := `
		SELECT id, name, building_id, floor_number, created_at, updated_at
		FROM floor_plans
		WHERE id = $1`

	var plan models.FloorPlan
	err := p.db.QueryRowContext(ctx, query, id).Scan(
		&plan.ID, &plan.Name, &plan.Building,
		&plan.Level, &plan.CreatedAt, &plan.UpdatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("floor plan not found: %s", id)
		}
		return nil, fmt.Errorf("failed to get floor plan: %w", err)
	}

	// Load associated equipment
	plan.Equipment, err = p.GetEquipmentByFloorPlan(ctx, id)
	if err != nil {
		logger.Warn("Failed to load equipment for floor plan %s: %v", id, err)
		plan.Equipment = []*models.Equipment{}
	}

	// Load associated rooms
	plan.Rooms, err = p.GetRoomsByFloorPlan(ctx, id)
	if err != nil {
		logger.Warn("Failed to load rooms for floor plan %s: %v", id, err)
		plan.Rooms = []*models.Room{}
	}

	return &plan, nil
}

// GetAllFloorPlans retrieves all floor plans
func (p *PostGISDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	query := `
		SELECT id, name, building_id, floor_number, created_at, updated_at
		FROM floor_plans
		ORDER BY building_id, floor_number`

	rows, err := p.db.QueryContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query floor plans: %w", err)
	}
	defer rows.Close()

	var plans []*models.FloorPlan
	for rows.Next() {
		var plan models.FloorPlan
		err := rows.Scan(
			&plan.ID, &plan.Name, &plan.Building,
			&plan.Level, &plan.CreatedAt, &plan.UpdatedAt,
		)
		if err != nil {
			logger.Warn("Failed to scan floor plan: %v", err)
			continue
		}

		// Load equipment and rooms for each plan
		plan.Equipment, _ = p.GetEquipmentByFloorPlan(ctx, plan.ID)
		plan.Rooms, _ = p.GetRoomsByFloorPlan(ctx, plan.ID)

		plans = append(plans, &plan)
	}

	return plans, nil
}

// SaveFloorPlan saves or updates a floor plan
func (p *PostGISDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	if plan.ID == "" {
		plan.ID = fmt.Sprintf("fp-%d", time.Now().Unix())
	}

	query := `
		INSERT INTO floor_plans (id, name, building_id, floor_number, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (id) DO UPDATE SET
			name = EXCLUDED.name,
			building_id = EXCLUDED.building_id,
			floor_number = EXCLUDED.floor_number,
			updated_at = EXCLUDED.updated_at`

	now := time.Now()
	if plan.CreatedAt == nil {
		plan.CreatedAt = &now
	}
	plan.UpdatedAt = &now

	_, err := p.db.ExecContext(ctx, query,
		plan.ID, plan.Name, plan.Building,
		plan.Level, plan.CreatedAt, plan.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to save floor plan: %w", err)
	}

	// Save associated equipment
	for _, eq := range plan.Equipment {
		// Equipment doesn't have FloorPlanID field, so we need to use metadata
		if eq.Metadata == nil {
			eq.Metadata = make(map[string]interface{})
		}
		eq.Metadata["floor_plan_id"] = plan.ID
		if err := p.SaveEquipment(ctx, eq); err != nil {
			logger.Warn("Failed to save equipment %s: %v", eq.ID, err)
		}
	}

	// Save associated rooms
	for _, room := range plan.Rooms {
		// Store floor plan association in a separate table or metadata
		if err := p.SaveRoom(ctx, room); err != nil {
			logger.Warn("Failed to save room %s: %v", room.ID, err)
		}
	}

	return nil
}

// UpdateFloorPlan updates an existing floor plan
func (p *PostGISDB) UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	return p.SaveFloorPlan(ctx, plan)
}

// DeleteFloorPlan deletes a floor plan and its associations
func (p *PostGISDB) DeleteFloorPlan(ctx context.Context, id string) error {
	// Start transaction for cascading deletes
	tx, err := p.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Delete associated equipment
	if _, err := tx.ExecContext(ctx, "DELETE FROM equipment WHERE floor_plan_id = $1", id); err != nil {
		return fmt.Errorf("failed to delete equipment: %w", err)
	}

	// Delete associated rooms
	if _, err := tx.ExecContext(ctx, "DELETE FROM rooms WHERE floor_plan_id = $1", id); err != nil {
		return fmt.Errorf("failed to delete rooms: %w", err)
	}

	// Delete floor plan
	if _, err := tx.ExecContext(ctx, "DELETE FROM floor_plans WHERE id = $1", id); err != nil {
		return fmt.Errorf("failed to delete floor plan: %w", err)
	}

	return tx.Commit()
}

// GetEquipmentByFloorPlan retrieves all equipment for a floor plan
func (p *PostGISDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	query := `
		SELECT id, name, type,
			   ST_X(location) as x, ST_Y(location) as y, ST_Z(location) as z,
			   status, metadata, created_at
		FROM equipment
		WHERE floor_plan_id = $1
		ORDER BY name`

	rows, err := p.db.QueryContext(ctx, query, floorPlanID)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment: %w", err)
	}
	defer rows.Close()

	var equipment []*models.Equipment
	for rows.Next() {
		var eq models.Equipment
		var x, y, z sql.NullFloat64
		var metadata sql.NullString
		var createdAt time.Time

		err := rows.Scan(
			&eq.ID, &eq.Name, &eq.Type,
			&x, &y, &z, &eq.Status, &metadata,
			&createdAt,
		)
		if err != nil {
			logger.Warn("Failed to scan equipment: %v", err)
			continue
		}

		if x.Valid && y.Valid && z.Valid {
			eq.Location = &models.Point3D{X: x.Float64, Y: y.Float64, Z: z.Float64}
		}

		if metadata.Valid {
			json.Unmarshal([]byte(metadata.String), &eq.Metadata)
		}

		eq.MarkedAt = &createdAt
		equipment = append(equipment, &eq)
	}

	return equipment, nil
}

// GetRoomsByFloorPlan retrieves all rooms for a floor plan
func (p *PostGISDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	query := `
		SELECT id, name
		FROM rooms
		WHERE floor_plan_id = $1
		ORDER BY name`

	rows, err := p.db.QueryContext(ctx, query, floorPlanID)
	if err != nil {
		return nil, fmt.Errorf("failed to query rooms: %w", err)
	}
	defer rows.Close()

	var rooms []*models.Room
	for rows.Next() {
		var room models.Room
		err := rows.Scan(&room.ID, &room.Name)
		if err != nil {
			logger.Warn("Failed to scan room: %v", err)
			continue
		}

		rooms = append(rooms, &room)
	}

	return rooms, nil
}

// SaveEquipment saves or updates equipment
func (p *PostGISDB) SaveEquipment(ctx context.Context, eq *models.Equipment) error {
	if eq.ID == "" {
		eq.ID = fmt.Sprintf("eq-%d", time.Now().Unix())
	}

	// Extract floor_plan_id from metadata
	var floorPlanID string
	if eq.Metadata != nil {
		if fpID, ok := eq.Metadata["floor_plan_id"].(string); ok {
			floorPlanID = fpID
		}
	}

	// Prepare location geometry
	var location interface{}
	if eq.Location != nil {
		location = fmt.Sprintf("POINT(%f %f %f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
	} else {
		location = nil
	}

	// Serialize metadata
	var metadataJSON []byte
	if eq.Metadata != nil {
		metadataJSON, _ = json.Marshal(eq.Metadata)
	}

	query := `
		INSERT INTO equipment (id, name, type, floor_plan_id, location, status, metadata, created_at, updated_at)
		VALUES ($1, $2, $3, $4, ST_GeomFromText($5, 4326), $6, $7, $8, $9)
		ON CONFLICT (id) DO UPDATE SET
			name = EXCLUDED.name,
			type = EXCLUDED.type,
			floor_plan_id = EXCLUDED.floor_plan_id,
			location = EXCLUDED.location,
			status = EXCLUDED.status,
			metadata = EXCLUDED.metadata,
			updated_at = EXCLUDED.updated_at`

	now := time.Now()
	var createdAt, updatedAt time.Time
	if eq.MarkedAt != nil {
		createdAt = *eq.MarkedAt
	} else {
		createdAt = now
	}
	updatedAt = now

	_, err := p.db.ExecContext(ctx, query,
		eq.ID, eq.Name, eq.Type, floorPlanID,
		location, eq.Status, metadataJSON,
		createdAt, updatedAt,
	)

	return err
}

// SaveRoom saves or updates a room
func (p *PostGISDB) SaveRoom(ctx context.Context, room *models.Room) error {
	if room.ID == "" {
		room.ID = fmt.Sprintf("room-%d", time.Now().Unix())
	}

	// For now, use simplified storage - Room doesn't have all the fields we need
	// This is a placeholder implementation
	query := `
		INSERT INTO rooms (id, name, floor_plan_id, floor, room_type, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (id) DO UPDATE SET
			name = EXCLUDED.name,
			updated_at = EXCLUDED.updated_at`

	now := time.Now()
	_, err := p.db.ExecContext(ctx, query,
		room.ID, room.Name, "", 0, "default",
		now, now,
	)

	return err
}

// GetEquipment retrieves equipment by ID
func (p *PostGISDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	query := `
		SELECT id, name, type,
			   ST_X(location) as x, ST_Y(location) as y, ST_Z(location) as z,
			   status, metadata, created_at
		FROM equipment
		WHERE id = $1`

	var eq models.Equipment
	var x, y, z sql.NullFloat64
	var metadata sql.NullString
	var createdAt time.Time

	err := p.db.QueryRowContext(ctx, query, id).Scan(
		&eq.ID, &eq.Name, &eq.Type,
		&x, &y, &z, &eq.Status, &metadata,
		&createdAt,
	)
	if err != nil {
		return nil, err
	}

	if x.Valid && y.Valid && z.Valid {
		eq.Location = &models.Point3D{X: x.Float64, Y: y.Float64, Z: z.Float64}
	}

	if metadata.Valid {
		json.Unmarshal([]byte(metadata.String), &eq.Metadata)
	}

	eq.MarkedAt = &createdAt
	return &eq, nil
}

// GetRoom retrieves a room by ID
func (p *PostGISDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	query := `
		SELECT id, name
		FROM rooms
		WHERE id = $1`

	var room models.Room
	err := p.db.QueryRowContext(ctx, query, id).Scan(&room.ID, &room.Name)
	if err != nil {
		return nil, err
	}

	return &room, nil
}

// UpdateEquipment updates equipment
func (p *PostGISDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	return p.SaveEquipment(ctx, equipment)
}

// DeleteEquipment deletes equipment
func (p *PostGISDB) DeleteEquipment(ctx context.Context, id string) error {
	_, err := p.db.ExecContext(ctx, "DELETE FROM equipment WHERE id = $1", id)
	return err
}

// UpdateRoom updates a room
func (p *PostGISDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	return p.SaveRoom(ctx, room)
}

// DeleteRoom deletes a room
func (p *PostGISDB) DeleteRoom(ctx context.Context, id string) error {
	_, err := p.db.ExecContext(ctx, "DELETE FROM rooms WHERE id = $1", id)
	return err
}

// createSpatialTablesExtended creates additional tables if needed
func (p *PostGISDB) createSpatialTablesExtended(ctx context.Context) error {
	tables := []string{
		`CREATE TABLE IF NOT EXISTS floor_plans (
			id VARCHAR(255) PRIMARY KEY,
			name VARCHAR(255) NOT NULL,
			building_id VARCHAR(255) NOT NULL,
			floor_number INTEGER,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS equipment (
			id VARCHAR(255) PRIMARY KEY,
			name VARCHAR(255),
			type VARCHAR(100),
			floor_plan_id VARCHAR(255) REFERENCES floor_plans(id),
			location GEOMETRY(PointZ, 4326),
			status VARCHAR(50),
			metadata JSONB,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS rooms (
			id VARCHAR(255) PRIMARY KEY,
			name VARCHAR(255),
			floor_plan_id VARCHAR(255) REFERENCES floor_plans(id),
			floor INTEGER,
			room_type VARCHAR(100),
			boundary GEOMETRY(Polygon, 4326),
			metadata JSONB,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS point_cloud (
			id SERIAL PRIMARY KEY,
			scan_id VARCHAR(255),
			building_id VARCHAR(255),
			floor_number INTEGER,
			location GEOMETRY(PointZ, 4326),
			confidence_score FLOAT,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS spatial_anchors (
			id VARCHAR(255) PRIMARY KEY,
			building_id VARCHAR(255),
			type VARCHAR(100),
			location GEOMETRY(PointZ, 4326),
			confidence FLOAT,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
	}

	for _, table := range tables {
		if _, err := p.db.ExecContext(ctx, table); err != nil {
			logger.Warn("Failed to create table: %v", err)
			// Continue - table might already exist
		}
	}

	// Create spatial indexes
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment USING GIST(location)",
		"CREATE INDEX IF NOT EXISTS idx_rooms_boundary ON rooms USING GIST(boundary)",
		"CREATE INDEX IF NOT EXISTS idx_point_cloud_location ON point_cloud USING GIST(location)",
		"CREATE INDEX IF NOT EXISTS idx_equipment_floor_plan ON equipment(floor_plan_id)",
		"CREATE INDEX IF NOT EXISTS idx_rooms_floor_plan ON rooms(floor_plan_id)",
	}

	for _, index := range indexes {
		if _, err := p.db.ExecContext(ctx, index); err != nil {
			logger.Warn("Failed to create index: %v", err)
		}
	}

	return nil
}
