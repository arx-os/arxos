-- Create validation tables for confidence system

-- Validation submissions table
CREATE TABLE IF NOT EXISTS validation_submissions (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT REFERENCES arx_objects(id) ON DELETE CASCADE,
    object_uuid VARCHAR(255) NOT NULL,
    validation_type VARCHAR(50) NOT NULL,
    validator_id BIGINT REFERENCES users(id),
    validator_name VARCHAR(255),
    confidence FLOAT DEFAULT 0.0,
    data JSONB,
    photo_url TEXT,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_validation_object (object_id),
    INDEX idx_validation_status (status),
    INDEX idx_validation_created (created_at DESC)
);

-- Validation patterns table for pattern learning
CREATE TABLE IF NOT EXISTS validation_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence_threshold FLOAT DEFAULT 0.7,
    application_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    learned_from_object_id BIGINT REFERENCES arx_objects(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_pattern_type (pattern_type),
    INDEX idx_pattern_confidence (confidence_threshold)
);

-- Validation propagation history
CREATE TABLE IF NOT EXISTS validation_propagations (
    id BIGSERIAL PRIMARY KEY,
    source_validation_id BIGINT REFERENCES validation_submissions(id),
    source_object_id BIGINT REFERENCES arx_objects(id),
    target_object_id BIGINT REFERENCES arx_objects(id),
    propagation_type VARCHAR(50), -- 'cascade', 'pattern', 'similarity'
    confidence_before FLOAT,
    confidence_after FLOAT,
    decay_factor FLOAT DEFAULT 1.0,
    distance INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_propagation_source (source_object_id),
    INDEX idx_propagation_target (target_object_id),
    INDEX idx_propagation_type (propagation_type)
);

-- Validation queue for objects needing validation
CREATE TABLE IF NOT EXISTS validation_queue (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT REFERENCES arx_objects(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0, -- Higher priority = more urgent
    reason VARCHAR(255),
    flagged_by BIGINT REFERENCES users(id),
    flagged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_to BIGINT REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'assigned', 'completed', 'skipped'
    
    UNIQUE(object_id),
    INDEX idx_queue_status (status),
    INDEX idx_queue_priority (priority DESC, flagged_at ASC),
    INDEX idx_queue_assigned (assigned_to)
);

-- Validation statistics for leaderboard
CREATE TABLE IF NOT EXISTS validation_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    total_validations INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    pattern_contributions INTEGER DEFAULT 0,
    objects_improved INTEGER DEFAULT 0,
    total_confidence_added FLOAT DEFAULT 0.0,
    streak_days INTEGER DEFAULT 0,
    last_validation_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id),
    INDEX idx_stats_validations (total_validations DESC),
    INDEX idx_stats_confidence (total_confidence_added DESC)
);

-- Confidence cache table for performance
CREATE TABLE IF NOT EXISTS confidence_cache (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT REFERENCES arx_objects(id) ON DELETE CASCADE,
    confidence_type VARCHAR(50), -- 'overall', 'classification', 'position', etc.
    confidence_value FLOAT NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    dependencies JSONB, -- IDs of related objects affecting this confidence
    
    UNIQUE(object_id, confidence_type),
    INDEX idx_cache_object (object_id),
    INDEX idx_cache_expires (expires_at),
    INDEX idx_cache_type (confidence_type)
);

-- Create function to update validation stats
CREATE OR REPLACE FUNCTION update_validation_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'processed' AND OLD.status != 'processed' THEN
        -- Update or insert validation stats
        INSERT INTO validation_stats (
            user_id,
            total_validations,
            successful_validations,
            last_validation_date,
            updated_at
        )
        VALUES (
            NEW.validator_id,
            1,
            CASE WHEN NEW.confidence > 0.7 THEN 1 ELSE 0 END,
            CURRENT_DATE,
            NOW()
        )
        ON CONFLICT (user_id) DO UPDATE SET
            total_validations = validation_stats.total_validations + 1,
            successful_validations = validation_stats.successful_validations + 
                CASE WHEN NEW.confidence > 0.7 THEN 1 ELSE 0 END,
            last_validation_date = CURRENT_DATE,
            streak_days = CASE 
                WHEN validation_stats.last_validation_date = CURRENT_DATE - INTERVAL '1 day'
                THEN validation_stats.streak_days + 1
                ELSE 1
            END,
            updated_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for validation stats
CREATE TRIGGER update_stats_on_validation
AFTER UPDATE ON validation_submissions
FOR EACH ROW
EXECUTE FUNCTION update_validation_stats();

-- Function to calculate confidence decay based on distance
CREATE OR REPLACE FUNCTION calculate_confidence_decay(
    base_confidence FLOAT,
    distance INTEGER,
    decay_type VARCHAR DEFAULT 'exponential'
) RETURNS FLOAT AS $$
BEGIN
    CASE decay_type
        WHEN 'exponential' THEN
            RETURN base_confidence * POWER(0.85, distance);
        WHEN 'linear' THEN
            RETURN GREATEST(0, base_confidence - (distance * 0.1));
        WHEN 'inverse_square' THEN
            RETURN base_confidence / (1 + POWER(distance, 2) * 0.1);
        ELSE
            RETURN base_confidence * POWER(0.9, distance);
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar objects for pattern application
CREATE OR REPLACE FUNCTION find_similar_objects(
    source_object_id BIGINT,
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 100
) RETURNS TABLE (
    object_id BIGINT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o2.id AS object_id,
        -- Calculate similarity based on type, system, and properties
        (
            CASE WHEN o1.type = o2.type THEN 0.4 ELSE 0 END +
            CASE WHEN o1.system = o2.system THEN 0.3 ELSE 0 END +
            CASE 
                WHEN o1.data IS NOT NULL AND o2.data IS NOT NULL 
                THEN 0.3 * (
                    1 - (
                        jsonb_array_length(
                            COALESCE((o1.data - o2.data)::jsonb, '[]'::jsonb)
                        )::FLOAT / 
                        GREATEST(
                            jsonb_array_length(COALESCE(o1.data::jsonb, '{}'::jsonb)),
                            jsonb_array_length(COALESCE(o2.data::jsonb, '{}'::jsonb)),
                            1
                        )
                    )
                )
                ELSE 0 
            END
        ) AS similarity_score
    FROM arx_objects o1, arx_objects o2
    WHERE 
        o1.id = source_object_id
        AND o2.id != source_object_id
        AND o2.confidence->>'overall' < '0.7'  -- Only find objects needing validation
    HAVING similarity_score >= similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending validations for a user
CREATE OR REPLACE FUNCTION get_pending_validations(
    user_id_param BIGINT DEFAULT NULL,
    limit_param INTEGER DEFAULT 10
) RETURNS TABLE (
    queue_id BIGINT,
    object_id BIGINT,
    object_uuid VARCHAR,
    object_type VARCHAR,
    priority INTEGER,
    reason VARCHAR,
    current_confidence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vq.id AS queue_id,
        vq.object_id,
        o.uuid AS object_uuid,
        o.type AS object_type,
        vq.priority,
        vq.reason,
        (o.confidence->>'overall')::FLOAT AS current_confidence
    FROM validation_queue vq
    JOIN arx_objects o ON vq.object_id = o.id
    WHERE 
        vq.status = 'pending'
        AND (user_id_param IS NULL OR vq.assigned_to IS NULL OR vq.assigned_to = user_id_param)
    ORDER BY 
        vq.priority DESC,
        vq.flagged_at ASC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;

-- Add sample validation patterns
INSERT INTO validation_patterns (pattern_type, pattern_data, confidence_threshold)
VALUES 
    ('wall_dimensions', '{"min_height": 2400, "max_height": 3600, "min_thickness": 100, "max_thickness": 300}', 0.8),
    ('door_standard', '{"standard_width": [800, 900, 1000], "standard_height": [2000, 2100]}', 0.75),
    ('room_classification', '{"min_area": 9, "aspect_ratio_range": [0.5, 2.0]}', 0.7)
ON CONFLICT DO NOTHING;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_arx_objects_confidence 
ON arx_objects ((confidence->>'overall'));

CREATE INDEX IF NOT EXISTS idx_arx_objects_type_system 
ON arx_objects (type, system);

-- Add validation-related columns to arx_objects if they don't exist
ALTER TABLE arx_objects 
ADD COLUMN IF NOT EXISTS validation_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_validated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS validation_priority INTEGER DEFAULT 0;