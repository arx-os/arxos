-- Migration 002: Confidence tracking and coverage
-- Adds confidence tracking and coverage mapping capabilities

-- Confidence records for equipment
CREATE TABLE IF NOT EXISTS confidence_records (
    equipment_id VARCHAR(255) PRIMARY KEY,
    -- Position confidence
    position_confidence INTEGER DEFAULT 0 CHECK (position_confidence >= 0 AND position_confidence <= 3),
    position_source VARCHAR(50),
    position_updated TIMESTAMP,
    position_accuracy FLOAT, -- estimated accuracy in meters
    -- Semantic confidence
    semantic_confidence INTEGER DEFAULT 0 CHECK (semantic_confidence >= 0 AND semantic_confidence <= 3),
    semantic_source VARCHAR(50),
    semantic_updated TIMESTAMP,
    semantic_completeness FLOAT CHECK (semantic_completeness >= 0 AND semantic_completeness <= 1),
    -- Verification tracking
    last_field_verified TIMESTAMP,
    verification_count INTEGER DEFAULT 0,
    verification_history JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coverage tracking for buildings
CREATE TABLE IF NOT EXISTS coverage_maps (
    building_id VARCHAR(255) PRIMARY KEY REFERENCES building_spatial_refs(building_id) ON DELETE CASCADE,
    total_area FLOAT, -- square meters
    scanned_area FLOAT DEFAULT 0,
    coverage_percentage FLOAT GENERATED ALWAYS AS (
        CASE
            WHEN total_area > 0 THEN (scanned_area / total_area * 100)
            ELSE 0
        END
    ) STORED,
    last_scan_date TIMESTAMP,
    scan_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Point cloud storage (chunked for large scans)
CREATE TABLE IF NOT EXISTS point_clouds (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(255) REFERENCES scanned_regions(scan_id) ON DELETE CASCADE,
    building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    points GEOMETRY(MULTIPOINTZ, 0),
    colors INTEGER[], -- RGB colors if available
    intensities FLOAT[], -- LiDAR intensity values
    metadata JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scan_id, chunk_index)
);

-- Spatial anchors for AR integration
CREATE TABLE IF NOT EXISTS spatial_anchors (
    id VARCHAR(255) PRIMARY KEY,
    building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id) ON DELETE CASCADE,
    world_position GEOMETRY(POINTZ, 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    device_type VARCHAR(100),
    metadata JSONB
);

-- Create indexes
CREATE INDEX idx_confidence_equipment ON confidence_records(equipment_id);
CREATE INDEX idx_confidence_position ON confidence_records(position_confidence);
CREATE INDEX idx_confidence_semantic ON confidence_records(semantic_confidence);
CREATE INDEX idx_confidence_verified ON confidence_records(last_field_verified);

CREATE INDEX idx_coverage_building ON coverage_maps(building_id);
CREATE INDEX idx_coverage_percentage ON coverage_maps(coverage_percentage);

CREATE INDEX idx_point_clouds_scan ON point_clouds(scan_id);
CREATE INDEX idx_point_clouds_building ON point_clouds(building_id);
CREATE INDEX idx_point_clouds_points ON point_clouds USING GIST(points);

CREATE INDEX idx_anchors_building ON spatial_anchors(building_id);
CREATE INDEX idx_anchors_position ON spatial_anchors USING GIST(world_position);

-- Function to calculate equipment confidence score
CREATE OR REPLACE FUNCTION calculate_confidence_score(equipment_id VARCHAR)
RETURNS FLOAT AS $$
DECLARE
    pos_conf INTEGER;
    sem_conf INTEGER;
    last_verify TIMESTAMP;
    days_since_verify INTEGER;
    score FLOAT;
BEGIN
    SELECT
        position_confidence,
        semantic_confidence,
        last_field_verified
    INTO pos_conf, sem_conf, last_verify
    FROM confidence_records
    WHERE confidence_records.equipment_id = calculate_confidence_score.equipment_id;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    -- Base score from confidence levels
    score := (pos_conf * 0.6 + sem_conf * 0.4) / 3.0;

    -- Apply time decay if verified
    IF last_verify IS NOT NULL THEN
        days_since_verify := EXTRACT(DAY FROM (CURRENT_TIMESTAMP - last_verify));
        -- Decay factor: loses 10% confidence per 30 days
        score := score * (1.0 - LEAST(days_since_verify / 300.0, 0.5));
    END IF;

    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- Function to update coverage after scan
CREATE OR REPLACE FUNCTION update_coverage_after_scan()
RETURNS TRIGGER AS $$
DECLARE
    new_area FLOAT;
    total FLOAT;
BEGIN
    -- Calculate total scanned area for the building
    SELECT
        COALESCE(SUM(ST_Area(region_boundary)), 0) INTO new_area
    FROM scanned_regions
    WHERE building_id = COALESCE(NEW.building_id, OLD.building_id);

    -- Update coverage map
    INSERT INTO coverage_maps (building_id, scanned_area, last_scan_date, scan_count)
    VALUES (
        COALESCE(NEW.building_id, OLD.building_id),
        new_area,
        CURRENT_TIMESTAMP,
        1
    )
    ON CONFLICT (building_id) DO UPDATE SET
        scanned_area = new_area,
        last_scan_date = CURRENT_TIMESTAMP,
        scan_count = coverage_maps.scan_count + 1,
        last_updated = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic coverage updates
DROP TRIGGER IF EXISTS update_coverage ON scanned_regions;
CREATE TRIGGER update_coverage
    AFTER INSERT OR UPDATE OR DELETE ON scanned_regions
    FOR EACH ROW
    EXECUTE FUNCTION update_coverage_after_scan();

-- Add update timestamp triggers
CREATE TRIGGER update_confidence_records_updated_at
    BEFORE UPDATE ON confidence_records
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coverage_maps_updated_at
    BEFORE UPDATE ON coverage_maps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();