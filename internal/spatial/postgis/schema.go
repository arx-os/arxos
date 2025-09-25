package postgis

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/database"
)

// Schema defines the PostGIS database schema for spatial data
type Schema struct {
	db *sql.DB
}

// NewSchema creates a new schema manager
func NewSchema(db *sql.DB) *Schema {
	return &Schema{db: db}
}

// CreateExtensions enables required PostGIS extensions
func (s *Schema) CreateExtensions() error {
	extensions := []string{
		"CREATE EXTENSION IF NOT EXISTS postgis",
		"CREATE EXTENSION IF NOT EXISTS postgis_topology",
		"CREATE EXTENSION IF NOT EXISTS fuzzystrmatch",
		"CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder",
	}

	for _, ext := range extensions {
		if _, err := s.db.Exec(ext); err != nil {
			// Some extensions might not be available, log but don't fail
			fmt.Printf("Warning: Could not create extension: %v\n", err)
		}
	}

	return nil
}

// CreateTables creates all spatial tables
func (s *Schema) CreateTables() error {
	queries := []string{
		// Building spatial reference table
		`CREATE TABLE IF NOT EXISTS building_spatial_refs (
			building_id VARCHAR(255) PRIMARY KEY,
			origin_gps GEOGRAPHY(POINT, 4326),
			origin_local GEOMETRY(POINT, 0),
			rotation_degrees FLOAT,
			grid_scale FLOAT DEFAULT 0.5,
			floor_height FLOAT DEFAULT 3.0,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Equipment positions table
		`CREATE TABLE IF NOT EXISTS equipment_positions (
			equipment_id VARCHAR(255) PRIMARY KEY,
			building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id),
			position_3d GEOMETRY(POINTZ, 0),
			position_confidence INTEGER DEFAULT 0,
			position_source VARCHAR(50),
			position_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			bounding_box GEOMETRY(POLYGON, 0),
			orientation FLOAT[3],
			grid_x INTEGER,
			grid_y INTEGER,
			floor INTEGER
		)`,

		// Scanned regions tracking table
		`CREATE TABLE IF NOT EXISTS scanned_regions (
			id SERIAL PRIMARY KEY,
			building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id),
			scan_id VARCHAR(255) UNIQUE,
			region_boundary GEOMETRY(POLYGON, 0),
			scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			scan_type VARCHAR(50),
			point_density FLOAT,
			confidence_score FLOAT,
			raw_data_url TEXT,
			metadata JSONB
		)`,

		// Point cloud storage table
		`CREATE TABLE IF NOT EXISTS point_clouds (
			id SERIAL PRIMARY KEY,
			scan_id VARCHAR(255) REFERENCES scanned_regions(scan_id),
			building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id),
			chunk_index INTEGER,
			points GEOMETRY(MULTIPOINTZ, 0),
			colors INTEGER[],
			intensities FLOAT[],
			metadata JSONB,
			processed BOOLEAN DEFAULT FALSE,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,

		// Confidence records table
		`CREATE TABLE IF NOT EXISTS confidence_records (
			equipment_id VARCHAR(255) PRIMARY KEY,
			position_confidence INTEGER DEFAULT 0,
			position_source VARCHAR(50),
			position_updated TIMESTAMP,
			position_accuracy FLOAT,
			semantic_confidence INTEGER DEFAULT 0,
			semantic_source VARCHAR(50),
			semantic_updated TIMESTAMP,
			semantic_completeness FLOAT,
			last_field_verified TIMESTAMP,
			verification_count INTEGER DEFAULT 0,
			verification_history JSONB
		)`,

		// Spatial anchors for AR
		`CREATE TABLE IF NOT EXISTS spatial_anchors (
			id VARCHAR(255) PRIMARY KEY,
			building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id),
			world_position GEOMETRY(POINTZ, 0),
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			last_seen TIMESTAMP,
			confidence FLOAT,
			metadata JSONB
		)`,

		// Coverage tracking table
		`CREATE TABLE IF NOT EXISTS coverage_maps (
			building_id VARCHAR(255) PRIMARY KEY REFERENCES building_spatial_refs(building_id),
			total_area FLOAT,
			scanned_area FLOAT,
			coverage_percentage FLOAT GENERATED ALWAYS AS (
				CASE
					WHEN total_area > 0 THEN (scanned_area / total_area * 100)
					ELSE 0
				END
			) STORED,
			last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
	}

	for _, query := range queries {
		if _, err := s.db.Exec(query); err != nil {
			return fmt.Errorf("failed to create table: %w", err)
		}
	}

	return nil
}

// CreateIndexes creates spatial and performance indexes
func (s *Schema) CreateIndexes() error {
	indexes := []string{
		// Spatial indexes
		"CREATE INDEX IF NOT EXISTS idx_equipment_position_3d ON equipment_positions USING GIST(position_3d)",
		"CREATE INDEX IF NOT EXISTS idx_equipment_bbox ON equipment_positions USING GIST(bounding_box)",
		"CREATE INDEX IF NOT EXISTS idx_scanned_regions_boundary ON scanned_regions USING GIST(region_boundary)",
		"CREATE INDEX IF NOT EXISTS idx_point_clouds_points ON point_clouds USING GIST(points)",
		"CREATE INDEX IF NOT EXISTS idx_spatial_anchors_position ON spatial_anchors USING GIST(world_position)",

		// Regular indexes
		"CREATE INDEX IF NOT EXISTS idx_equipment_building ON equipment_positions(building_id)",
		"CREATE INDEX IF NOT EXISTS idx_equipment_confidence ON equipment_positions(position_confidence)",
		"CREATE INDEX IF NOT EXISTS idx_equipment_grid ON equipment_positions(grid_x, grid_y, floor)",
		"CREATE INDEX IF NOT EXISTS idx_scanned_regions_building ON scanned_regions(building_id)",
		"CREATE INDEX IF NOT EXISTS idx_scanned_regions_date ON scanned_regions(scan_date DESC)",
		"CREATE INDEX IF NOT EXISTS idx_point_clouds_scan ON point_clouds(scan_id)",
		"CREATE INDEX IF NOT EXISTS idx_confidence_equipment ON confidence_records(equipment_id)",
		"CREATE INDEX IF NOT EXISTS idx_anchors_building ON spatial_anchors(building_id)",
	}

	for _, idx := range indexes {
		if _, err := s.db.Exec(idx); err != nil {
			return fmt.Errorf("failed to create index: %w", err)
		}
	}

	return nil
}

// CreateFunctions creates stored procedures and functions
func (s *Schema) CreateFunctions() error {
	functions := []string{
		// Function to calculate distance between equipment
		`CREATE OR REPLACE FUNCTION equipment_distance(id1 VARCHAR, id2 VARCHAR)
		RETURNS FLOAT AS $$
		DECLARE
			pos1 GEOMETRY;
			pos2 GEOMETRY;
		BEGIN
			SELECT position_3d INTO pos1 FROM equipment_positions WHERE equipment_id = id1;
			SELECT position_3d INTO pos2 FROM equipment_positions WHERE equipment_id = id2;

			IF pos1 IS NULL OR pos2 IS NULL THEN
				RETURN NULL;
			END IF;

			RETURN ST_Distance(pos1, pos2);
		END;
		$$ LANGUAGE plpgsql`,

		// Function to find equipment within radius
		`CREATE OR REPLACE FUNCTION equipment_within_radius(
			center_point GEOMETRY,
			radius_meters FLOAT
		)
		RETURNS TABLE(equipment_id VARCHAR, distance FLOAT) AS $$
		BEGIN
			RETURN QUERY
			SELECT
				e.equipment_id,
				ST_Distance(e.position_3d, center_point) as distance
			FROM equipment_positions e
			WHERE ST_DWithin(e.position_3d, center_point, radius_meters)
			ORDER BY distance;
		END;
		$$ LANGUAGE plpgsql`,

		// Function to update coverage after scan
		`CREATE OR REPLACE FUNCTION update_coverage_after_scan()
		RETURNS TRIGGER AS $$
		DECLARE
			new_area FLOAT;
			total FLOAT;
		BEGIN
			-- Calculate new scanned area
			SELECT
				SUM(ST_Area(region_boundary)) INTO new_area
			FROM scanned_regions
			WHERE building_id = NEW.building_id;

			-- Get total area
			SELECT total_area INTO total
			FROM coverage_maps
			WHERE building_id = NEW.building_id;

			-- Update coverage
			UPDATE coverage_maps
			SET
				scanned_area = COALESCE(new_area, 0),
				last_updated = CURRENT_TIMESTAMP
			WHERE building_id = NEW.building_id;

			RETURN NEW;
		END;
		$$ LANGUAGE plpgsql`,

		// Trigger for coverage updates
		`CREATE TRIGGER update_coverage
		AFTER INSERT OR UPDATE OR DELETE ON scanned_regions
		FOR EACH ROW
		EXECUTE FUNCTION update_coverage_after_scan()`,
	}

	for _, fn := range functions {
		if _, err := s.db.Exec(fn); err != nil {
			// Functions might already exist, log but continue
			fmt.Printf("Warning: Function creation issue: %v\n", err)
		}
	}

	return nil
}

// Initialize creates the complete schema
func (s *Schema) Initialize() error {
	// Enable extensions
	if err := s.CreateExtensions(); err != nil {
		return fmt.Errorf("failed to create extensions: %w", err)
	}

	// Create tables
	if err := s.CreateTables(); err != nil {
		return fmt.Errorf("failed to create tables: %w", err)
	}

	// Create indexes
	if err := s.CreateIndexes(); err != nil {
		return fmt.Errorf("failed to create indexes: %w", err)
	}

	// Create functions
	if err := s.CreateFunctions(); err != nil {
		return fmt.Errorf("failed to create functions: %w", err)
	}

	return nil
}

// Migrate applies schema migrations
func (s *Schema) Migrate(fromVersion, toVersion int) error {
	// Use the migrator package for schema migrations
	migrator := database.NewMigrator(s.db, "migrations/")

	// Load and validate migrations
	if err := migrator.LoadMigrations(); err != nil {
		return fmt.Errorf("failed to load migrations: %w", err)
	}

	if err := migrator.ValidateMigrations(); err != nil {
		return fmt.Errorf("migration validation failed: %w", err)
	}

	// Apply migrations
	return migrator.Migrate(context.Background())
}
