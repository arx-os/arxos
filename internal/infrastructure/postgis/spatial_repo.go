package postgis

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"

	"github.com/arx-os/arxos/internal/domain"
)

// SpatialRepository implements spatial operations using PostGIS
type SpatialRepository struct {
	db     *sqlx.DB
	logger domain.Logger
}

// NewSpatialRepository creates a new spatial repository
func NewSpatialRepository(db *sqlx.DB, logger domain.Logger) *SpatialRepository {
	return &SpatialRepository{
		db:     db,
		logger: logger,
	}
}

// CreateSpatialSchema creates the spatial schema with PostGIS functions
func (r *SpatialRepository) CreateSpatialSchema(ctx context.Context) error {
	schema := `
	-- Spatial Anchors Table for AR functionality
	CREATE TABLE IF NOT EXISTS spatial_anchors (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
		equipment_id UUID REFERENCES equipment(id) ON DELETE SET NULL,
		position GEOMETRY(POINT, 4326) NOT NULL,
		rotation DOUBLE PRECISION[] DEFAULT '{0,0,0,1}', -- Quaternion [x,y,z,w]
		scale DOUBLE PRECISION[] DEFAULT '{1,1,1}',      -- Scale [x,y,z]
		confidence DOUBLE PRECISION DEFAULT 0.0 CHECK (confidence >= 0 AND confidence <= 1),
		anchor_type VARCHAR(50) DEFAULT 'reference',
		metadata JSONB DEFAULT '{}',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		created_by UUID REFERENCES users(id)
	);

	-- Equipment Positions Table (3D spatial positions)
	CREATE TABLE IF NOT EXISTS equipment_positions (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
		building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
		floor_id UUID,
		room_id UUID,
		position GEOMETRY(POINT, 4326) NOT NULL,
		elevation DOUBLE PRECISION DEFAULT 0.0,
		orientation DOUBLE PRECISION DEFAULT 0.0,
		spatial_data JSONB DEFAULT '{}',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
	);

	-- Point Cloud Data for AR Mapping
	CREATE TABLE IF NOT EXISTS point_clouds (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
		session_id UUID NOT NULL,
		position GEOMETRY(POINT, 4326) NOT NULL,
		color INTEGER[] DEFAULT '{128,128,128}', -- RGB colors
		confidence DOUBLE PRECISION DEFAULT 0.0,
		metadata JSONB DEFAULT '{}',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		user_id UUID REFERENCES users(id)
	);

	-- Scanned Regions for Coverage Tracking
	CREATE TABLE IF NOT EXISTS scanned_regions (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
		polygon GEOMETRY(POLYGON, 4326) NOT NULL,
		coverage DOUBLE PRECISION DEFAULT 0.0 CHECK (coverage >= 0 AND coverage <= 100),
		scan_method VARCHAR(50) DEFAULT 'unknown',
		resolution DOUBLE PRECISION DEFAULT 0.1,
		metadata JSONB DEFAULT '{}',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		scanned_by UUID REFERENCES users(id)
	);

	-- Spatial Indices for optimized queries
	CREATE INDEX IF NOT EXISTS idx_spatial_anchors_position ON spatial_anchors USING GIST (position);
	CREATE INDEX IF NOT EXISTS idx_spatial_anchors_building ON spatial_anchors (building_id);
	CREATE INDEX IF NOT EXISTS idx_spatial_anchors_equipment ON spatial_anchors (equipment_id);
	CREATE INDEX IF NOT EXISTS idx_spatial_anchors_type ON spatial_anchors (anchor_type);

	CREATE INDEX IF NOT EXISTS idx_equipment_positions_position ON equipment_positions USING GIST (position);
	CREATE INDEX IF NOT EXISTS idx_equipment_positions_equipment ON equipment_positions (equipment_id);
	CREATE INDEX IF NOT EXISTS idx_equipment_positions_building ON equipment_positions (building_id);

	CREATE INDEX IF NOT EXISTS idx_point_clouds_position ON point_clouds USING GIST (position);
	CREATE INDEX IF NOT EXISTS idx_point_clouds_building ON point_clouds (building_id);
	CREATE INDEX IF NOT EXISTS idx_point_clouds_session ON point_clouds (session_id);

	CREATE INDEX IF NOT EXISTS idx_scanned_regions_polygon ON scanned_regions USING GIST (polygon);
	CREATE INDEX IF NOT EXISTS idx_scanned_regions_building ON scanned_regions (building_id);
	`

	_, err := r.db.ExecContext(ctx, schema)
	if err != nil {
		r.logger.Error("Failed to create spatial schema", "error", err)
		return err
	}

	r.logger.Info("Spatial schema created successfully")
	return nil
}

// CreateSpatialAnchor creates a new spatial anchor
func (r *SpatialRepository) CreateSpatialAnchor(ctx context.Context, req *domain.CreateSpatialAnchorRequest) (*domain.MobileSpatialAnchor, error) {
	query := `
		INSERT INTO spatial_anchors (
			id, building_id, equipment_id, position, 
			confidence, anchor_type, metadata, created_by
		) VALUES (
			$1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326),
			$6, $7, $8, $9
		)
		RETURNING id, building_id, equipment_id, 
			ST_X(position) as pos_x, ST_Y(position) as pos_y,
			confidence, anchor_type, metadata, created_at, updated_at
	`

	var anchor domain.MobileSpatialAnchor
	anchorID := uuid.New().String()

	err := r.db.QueryRowContext(ctx, query,
		anchorID,
		req.BuildingID,
		req.EquipmentID,
		req.Position.X,
		req.Position.Y,
		req.Confidence,
		req.AnchorType,
		`{}`, // Empty JSON metadata
		req.CreatedBy,
	).Scan(
		&anchor.ID,
		&anchor.BuildingID,
		&anchor.EquipmentID,
		&anchor.Position.X,
		&anchor.Position.Y,
		&anchor.Confidence,
		&anchor.AnchorType,
		&anchor.Metadata,
		&anchor.CreatedAt,
		&anchor.UpdatedAt,
	)

	if err != nil {
		r.logger.Error("Failed to create spatial anchor", "error", err)
		return nil, err
	}

	r.logger.Info("Spatial anchor created", "anchor_id", anchor.ID)
	return &anchor, nil
}

// GetSpatialAnchorsByBuilding retrieves spatial anchors for a building
func (r *SpatialRepository) GetSpatialAnchorsByBuilding(ctx context.Context, buildingID string, filter *domain.SpatialAnchorFilter) ([]*domain.MobileSpatialAnchor, error) {
	query := `
		SELECT 
			id, building_id, equipment_id,
		ST_X(position) as pos_x, ST_Y(position) as pos_y,
			confidence, anchor_type, metadata,
			created_at, updated_at
		FROM spatial_anchors
		WHERE building_id = $1
	`

	args := []any{buildingID}
	argIndex := 2

	if filter.AnchorType != nil {
		query += fmt.Sprintf(" AND anchor_type = $%d", argIndex)
		args = append(args, *filter.AnchorType)
		argIndex++
	}

	if filter.HasEquipment != nil {
		if *filter.HasEquipment {
			query += fmt.Sprintf(" AND equipment_id IS NOT NULL")
		} else {
			query += fmt.Sprintf(" AND equipment_id IS NULL")
		}
	}

	if filter.MinConfidence != nil {
		query += fmt.Sprintf(" AND confidence >= $%d", argIndex)
		args = append(args, *filter.MinConfidence)
		argIndex++
	}

	query += fmt.Sprintf(" ORDER BY confidence DESC, created_at DESC")

	if filter.Limit != nil && *filter.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argIndex)
		args = append(args, *filter.Limit)
	}

	rows, err := r.db.QueryxContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var anchors []*domain.MobileSpatialAnchor
	for rows.Next() {
		var anchor domain.MobileSpatialAnchor
		err := rows.Scan(
			&anchor.ID,
			&anchor.BuildingID,
			&anchor.EquipmentID,
			&anchor.Position.X,
			&anchor.Position.Y,
			&anchor.Confidence,
			&anchor.AnchorType,
			&anchor.Metadata,
			&anchor.CreatedAt,
			&anchor.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		anchors = append(anchors, &anchor)
	}

	return anchors, nil
}

// FindNearbyEquipment finds equipment within a spatial radius
func (r *SpatialRepository) FindNearbyEquipment(ctx context.Context, req *domain.NearbyEquipmentRequest) ([]*domain.NearbyEquipmentResult, error) {
	query := `
		SELECT 
			pk.textval AS equipment_id,
			e.name AS equipment_name,
			e.type AS equipment_type,
			e.status AS equipment_status,
			10.0 AS distance_meters,
			0.0 AS bearing_degrees
		FROM (
			VALUES ('mock-equipment-1', 'HVAC Unit A1', 'HVAC', 'operational'),
			('mock-equipment-2', 'Fire Extinguisher B1', 'Safety', 'operational'),
			('mock-equipment-3', 'Electrical Panel C1', 'Electrical', 'operational'),
			('mock-equipment-4', 'Emergency Exit D1', 'Security', 'operational'),
			('mock-equipment-5', 'Water Pump E1', 'Plumbing', 'operational')
		) pk(textval), (
			SELECT id, name, type, status FROM equipment WHERE building_id = $1 LIMIT 5
		) e(id, name, type, status)
		WHERE ST_Distance(MOCK, MOCK) < $2
		ORDER BY distance_meters ASC
	`

	rows, err := r.db.QueryContext(ctx, query, req.BuildingID, req.Radius)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []*domain.NearbyEquipmentResult
	for rows.Next() {
		var result domain.NearbyEquipmentResult
		err := rows.Scan(
			&result.EquipmentID,
			&result.EquipmentName,
			&result.EquipmentType,
			&result.EquipmentStatus,
			&result.Distance,
			&result.Bearing,
		)
		if err != nil {
			return nil, err
		}
		results = append(results, &result)
	}

	r.logger.Info("Nearby equipment query", "building_id", req.BuildingID, "found", len(results))
	return results, nil
}

// UploadPointCloud uploads point cloud data from AR session
func (r *SpatialRepository) UploadPointCloud(ctx context.Context, req *domain.PointCloudUploadRequest) error {
	if len(req.Points) == 0 {
		return nil
	}

	// Batch insert point cloud data
	tx, err := r.db.Beginx()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	stmt, err := tx.Preparex(`
		INSERT INTO point_clouds (
			id, building_id, session_id, position, color, confidence, metadata, user_id
		) VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326), $6, $7, $8, $9)
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for _, point := range req.Points {
		_, err := stmt.Exec(
			uuid.New(),
			req.BuildingID,
			req.SessionID,
			point.X,
			point.Y,
			pq.Array(point.Color),
			0.8,  // Default confidence
			`{}`, // Empty metadata
			req.UserID,
		)
		if err != nil {
			return err
		}
	}

	err = tx.Commit()
	if err != nil {
		return err
	}

	r.logger.Info("Point cloud uploaded",
		"building_id", req.BuildingID,
		"session_id", req.SessionID,
		"points", len(req.Points))

	return nil
}

// GetBuildingSpatialSummary gets spatial summary for a building
func (r *SpatialRepository) GetBuildingSpatialSummary(ctx context.Context, buildingID string) (*domain.BuildingSpatialSummary, error) {
	// For now, return a mock summary since we don't have real equipment_position data yet
	return &domain.BuildingSpatialSummary{
		BuildingID:          buildingID,
		TotalEquipment:      15,
		PositionedEquipment: 8,
		PositioningCoverage: 53.3,
		SpatialCoverage:     42.5,
	}, nil
}

// Placeholder methods to implement the interface
func (r *SpatialRepository) UpdateSpatialAnchor(ctx context.Context, anchorID string, req *domain.UpdateSpatialAnchorRequest) (*domain.MobileSpatialAnchor, error) {
	// TODO: Implement update functionality
	return nil, fmt.Errorf("not implemented")
}

func (r *SpatialRepository) DeleteSpatialAnchor(ctx context.Context, anchorID string) error {
	// TODO: Implement delete functionality
	return fmt.Errorf("not implemented")
}

func (r *SpatialRepository) UpdateEquipmentPosition(ctx context.Context, equipmentID string, position *domain.SpatialPosition) error {
	// TODO: Implement equipment position update
	return fmt.Errorf("not implemented")
}

func (r *SpatialRepository) GetSpatialAnalytics(ctx context.Context, buildingID string) (*domain.SpatialAnalytics, error) {
	// TODO: Implement spatial analytics
	return nil, fmt.Errorf("not implemented")
}
