-- Migration: Add Confidence System to ArxObjects
-- Date: 2024
-- Description: Adds confidence scoring, relationships, and validation tracking

-- Add confidence and validation columns to existing arx_objects table
ALTER TABLE arx_objects 
ADD COLUMN IF NOT EXISTS confidence JSONB DEFAULT '{"classification": 0.5, "position": 0.5, "properties": 0.5, "relationships": 0.5, "overall": 0.5}',
ADD COLUMN IF NOT EXISTS relationships JSONB[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS validation_state VARCHAR(20) DEFAULT 'pending' CHECK (validation_state IN ('pending', 'partial', 'complete', 'conflict')),
ADD COLUMN IF NOT EXISTS validated_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{"source": "unknown", "validated": false}';

-- Create validation tracking table
CREATE TABLE IF NOT EXISTS arx_validations (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT NOT NULL REFERENCES arx_objects(id) ON DELETE CASCADE,
    validation_type VARCHAR(50) NOT NULL,
    old_confidence JSONB NOT NULL,
    new_confidence JSONB NOT NULL,
    measured_value TEXT,
    units VARCHAR(20),
    validator VARCHAR(100) NOT NULL,
    validator_confidence FLOAT CHECK (validator_confidence >= 0 AND validator_confidence <= 1),
    evidence JSONB DEFAULT '{}',
    impact_score FLOAT,
    cascaded_objects INTEGER DEFAULT 0,
    pattern_learned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for querying
    INDEX idx_validation_object (object_id),
    INDEX idx_validation_type (validation_type),
    INDEX idx_validation_created (created_at DESC),
    INDEX idx_validation_validator (validator)
);

-- Create validation impact tracking
CREATE TABLE IF NOT EXISTS validation_impacts (
    id BIGSERIAL PRIMARY KEY,
    validation_id BIGINT NOT NULL REFERENCES arx_validations(id) ON DELETE CASCADE,
    affected_object_id BIGINT NOT NULL REFERENCES arx_objects(id) ON DELETE CASCADE,
    confidence_before JSONB NOT NULL,
    confidence_after JSONB NOT NULL,
    propagation_type VARCHAR(50), -- spatial, pattern, system
    propagation_distance INTEGER, -- hops from validated object
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(validation_id, affected_object_id),
    INDEX idx_impact_validation (validation_id),
    INDEX idx_impact_object (affected_object_id)
);

-- Create pattern library for learned patterns
CREATE TABLE IF NOT EXISTS arx_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL, -- wall_grid, room_layout, floor_typical, etc.
    building_type VARCHAR(50), -- office, residential, hospital, etc.
    pattern_data JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    occurrence_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_pattern_type (pattern_type),
    INDEX idx_pattern_building (building_type),
    INDEX idx_pattern_confidence (confidence DESC)
);

-- Create uncertainties table for tracking what needs validation
CREATE TABLE IF NOT EXISTS arx_uncertainties (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT NOT NULL REFERENCES arx_objects(id) ON DELETE CASCADE,
    uncertainty_type VARCHAR(50) NOT NULL,
    confidence_level FLOAT NOT NULL,
    reason TEXT,
    validation_priority FLOAT DEFAULT 0.5,
    suggested_validation TEXT,
    impact_score FLOAT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_uncertainty_object (object_id),
    INDEX idx_uncertainty_priority (validation_priority DESC),
    INDEX idx_uncertainty_resolved (resolved)
);

-- Add confidence-based indexes to arx_objects
CREATE INDEX IF NOT EXISTS idx_arx_confidence_overall ON arx_objects ((confidence->>'overall'));
CREATE INDEX IF NOT EXISTS idx_arx_confidence_classification ON arx_objects ((confidence->>'classification'));
CREATE INDEX IF NOT EXISTS idx_arx_validation_state ON arx_objects (validation_state);
CREATE INDEX IF NOT EXISTS idx_arx_validated_at ON arx_objects (validated_at) WHERE validated_at IS NOT NULL;

-- Create function to calculate confidence improvement
CREATE OR REPLACE FUNCTION calculate_confidence_improvement(
    old_conf JSONB,
    new_conf JSONB
) RETURNS FLOAT AS $$
BEGIN
    RETURN (new_conf->>'overall')::FLOAT - (old_conf->>'overall')::FLOAT;
END;
$$ LANGUAGE plpgsql;

-- Create function to propagate validation spatially
CREATE OR REPLACE FUNCTION propagate_spatial_validation(
    validated_object_id BIGINT,
    max_distance FLOAT DEFAULT 5.0  -- meters
) RETURNS TABLE (
    object_id BIGINT,
    distance FLOAT,
    confidence_boost FLOAT
) AS $$
DECLARE
    validated_geom GEOMETRY;
    validated_confidence FLOAT;
BEGIN
    -- Get validated object geometry and confidence
    SELECT geom, (confidence->>'overall')::FLOAT
    INTO validated_geom, validated_confidence
    FROM arx_objects
    WHERE id = validated_object_id;
    
    -- Find nearby objects and calculate confidence boost
    RETURN QUERY
    SELECT 
        o.id,
        ST_Distance(o.geom, validated_geom) as distance,
        CASE 
            WHEN ST_Distance(o.geom, validated_geom) < 1 THEN 0.15
            WHEN ST_Distance(o.geom, validated_geom) < 3 THEN 0.10
            ELSE 0.05
        END as confidence_boost
    FROM arx_objects o
    WHERE 
        o.id != validated_object_id
        AND ST_DWithin(o.geom, validated_geom, max_distance)
        AND o.validation_state != 'complete';
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update metadata on changes
CREATE OR REPLACE FUNCTION update_arx_object_metadata()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.metadata = jsonb_set(
        COALESCE(NEW.metadata, '{}'::jsonb),
        '{last_modified}',
        to_jsonb(NOW())
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_arx_object_metadata_trigger
BEFORE UPDATE ON arx_objects
FOR EACH ROW
EXECUTE FUNCTION update_arx_object_metadata();

-- Create view for low-confidence objects needing validation
CREATE OR REPLACE VIEW arx_objects_needing_validation AS
SELECT 
    o.id,
    o.uuid,
    o.type,
    o.system,
    (o.confidence->>'overall')::FLOAT as overall_confidence,
    o.validation_state,
    u.validation_priority,
    u.suggested_validation,
    u.impact_score
FROM arx_objects o
LEFT JOIN arx_uncertainties u ON u.object_id = o.id AND u.resolved = FALSE
WHERE 
    (o.confidence->>'overall')::FLOAT < 0.6
    OR o.validation_state = 'pending'
ORDER BY 
    u.validation_priority DESC NULLS LAST,
    (o.confidence->>'overall')::FLOAT ASC;

-- Create materialized view for building confidence metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS building_confidence_metrics AS
SELECT 
    COALESCE(parent_id, 0) as building_id,
    COUNT(*) as total_objects,
    AVG((confidence->>'overall')::FLOAT) as avg_confidence,
    COUNT(*) FILTER (WHERE (confidence->>'overall')::FLOAT > 0.85) as high_confidence_count,
    COUNT(*) FILTER (WHERE (confidence->>'overall')::FLOAT BETWEEN 0.6 AND 0.85) as medium_confidence_count,
    COUNT(*) FILTER (WHERE (confidence->>'overall')::FLOAT < 0.6) as low_confidence_count,
    COUNT(*) FILTER (WHERE validation_state = 'complete') as validated_count,
    COUNT(*) FILTER (WHERE validation_state = 'pending') as pending_validation_count
FROM arx_objects
GROUP BY COALESCE(parent_id, 0);

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_building_metrics_confidence 
ON building_confidence_metrics (avg_confidence DESC);

-- Function to refresh metrics (call periodically or after bulk updates)
CREATE OR REPLACE FUNCTION refresh_building_metrics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY building_confidence_metrics;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE arx_validations IS 'Tracks all field validations submitted for ArxObjects';
COMMENT ON TABLE validation_impacts IS 'Records the cascade impact of validations on related objects';
COMMENT ON TABLE arx_patterns IS 'Library of learned patterns for pattern-based validation propagation';
COMMENT ON TABLE arx_uncertainties IS 'Tracks uncertainties and prioritizes validation needs';
COMMENT ON COLUMN arx_objects.confidence IS 'Multi-dimensional confidence score (classification, position, properties, relationships, overall)';
COMMENT ON COLUMN arx_objects.validation_state IS 'Current validation state: pending, partial, complete, or conflict';

-- Migration completion message
DO $$
BEGIN
    RAISE NOTICE 'Confidence system migration completed successfully';
    RAISE NOTICE 'New tables created: arx_validations, validation_impacts, arx_patterns, arx_uncertainties';
    RAISE NOTICE 'ArxObjects table enhanced with confidence and validation tracking';
END $$;