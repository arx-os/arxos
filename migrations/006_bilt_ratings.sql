-- BILT Rating system for real-time building valuation
-- Tracks building ratings from 0z (minimal data) to 1A (complete digital twin)

CREATE TABLE IF NOT EXISTS bilt_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    
    -- Current rating
    current_grade VARCHAR(5) NOT NULL, -- e.g., '0z', '0y', '1A'
    numeric_score DECIMAL(5,2) NOT NULL CHECK (numeric_score >= 0 AND numeric_score <= 100),
    version BIGINT NOT NULL DEFAULT 1,
    
    -- Component scores (0-100 each)
    structure_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    inventory_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    metadata_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    sensors_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    history_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    quality_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    activity_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    
    -- Metadata
    calculation_method VARCHAR(50) DEFAULT 'v1_algorithmic',
    last_calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one rating per building (latest version)
    UNIQUE(building_id)
);

-- Indexes for efficient queries
CREATE INDEX idx_bilt_ratings_building_id ON bilt_ratings(building_id);
CREATE INDEX idx_bilt_ratings_grade ON bilt_ratings(current_grade, numeric_score DESC);
CREATE INDEX idx_bilt_ratings_updated ON bilt_ratings(updated_at DESC);

-- Historical rating changes for tracking value progression
CREATE TABLE IF NOT EXISTS bilt_rating_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    
    -- Rating change details
    old_grade VARCHAR(5),
    new_grade VARCHAR(5) NOT NULL,
    old_score DECIMAL(5,2),
    new_score DECIMAL(5,2) NOT NULL,
    
    -- What triggered this rating change
    trigger_reason TEXT NOT NULL, -- 'object_added', 'sensor_installed', 'property_updated', etc.
    trigger_object_id UUID, -- Reference to specific object that triggered change
    trigger_source VARCHAR(50), -- 'api', 'terminal', 'webhook', 'system'
    
    -- Component score changes
    structure_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    inventory_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    metadata_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    sensors_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    history_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    quality_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    activity_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for rating history queries
CREATE INDEX idx_bilt_rating_history_building ON bilt_rating_history(building_id, created_at DESC);
CREATE INDEX idx_bilt_rating_history_grade ON bilt_rating_history(new_grade, created_at DESC);
CREATE INDEX idx_bilt_rating_history_trigger ON bilt_rating_history(trigger_reason, created_at DESC);

-- Function to update rating timestamp
CREATE OR REPLACE FUNCTION update_bilt_rating_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update timestamps and versions
CREATE TRIGGER bilt_rating_update_timestamp
    BEFORE UPDATE ON bilt_ratings
    FOR EACH ROW
    EXECUTE FUNCTION update_bilt_rating_timestamp();

-- Function to log rating changes to history
CREATE OR REPLACE FUNCTION log_bilt_rating_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if there's an actual grade or significant score change
    IF (OLD.current_grade IS DISTINCT FROM NEW.current_grade) OR 
       (ABS(OLD.numeric_score - NEW.numeric_score) >= 0.1) THEN
        
        INSERT INTO bilt_rating_history (
            building_id,
            old_grade, new_grade,
            old_score, new_score,
            trigger_reason,
            structure_score, inventory_score, metadata_score,
            sensors_score, history_score, quality_score, activity_score
        ) VALUES (
            NEW.building_id,
            OLD.current_grade, NEW.current_grade,
            OLD.numeric_score, NEW.numeric_score,
            COALESCE(current_setting('arxos.rating_trigger_reason', true), 'system_recalculation'),
            NEW.structure_score, NEW.inventory_score, NEW.metadata_score,
            NEW.sensors_score, NEW.history_score, NEW.quality_score, NEW.activity_score
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically log rating changes
CREATE TRIGGER bilt_rating_history_trigger
    AFTER UPDATE ON bilt_ratings
    FOR EACH ROW
    EXECUTE FUNCTION log_bilt_rating_change();

-- View for latest ratings with building info
CREATE OR REPLACE VIEW current_bilt_ratings AS
SELECT 
    r.building_id,
    b.name as building_name,
    r.current_grade,
    r.numeric_score,
    r.structure_score,
    r.inventory_score,
    r.metadata_score,
    r.sensors_score,
    r.history_score,
    r.quality_score,
    r.activity_score,
    r.last_calculated_at,
    r.updated_at,
    r.version
FROM bilt_ratings r
JOIN buildings b ON r.building_id = b.id
ORDER BY r.numeric_score DESC;

-- View for rating trends (last 30 days)
CREATE OR REPLACE VIEW bilt_rating_trends AS
SELECT 
    building_id,
    COUNT(*) as changes_count,
    MIN(new_score) as lowest_score,
    MAX(new_score) as highest_score,
    AVG(new_score) as avg_score,
    LAST_VALUE(new_grade) OVER (PARTITION BY building_id ORDER BY created_at 
                                RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as current_grade,
    FIRST_VALUE(new_score) OVER (PARTITION BY building_id ORDER BY created_at 
                                RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as starting_score,
    LAST_VALUE(new_score) OVER (PARTITION BY building_id ORDER BY created_at 
                               RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as ending_score
FROM bilt_rating_history 
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY building_id;