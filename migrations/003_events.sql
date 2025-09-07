-- Event system for real-time notifications

-- Events table to store all building events
CREATE TABLE IF NOT EXISTS building_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    object_id UUID,
    object_path TEXT,
    building_id UUID,
    
    -- Event data
    before_state JSONB,
    after_state JSONB,
    metadata JSONB DEFAULT '{}',
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    -- Indexing for queries
    INDEX idx_events_type (event_type),
    INDEX idx_events_object (object_id),
    INDEX idx_events_created (created_at DESC),
    INDEX idx_events_building (building_id)
);

-- Function to notify on object changes
CREATE OR REPLACE FUNCTION notify_object_change()
RETURNS TRIGGER AS $$
DECLARE
    event_type TEXT;
    event_data JSONB;
    channel TEXT;
BEGIN
    -- Determine event type
    IF TG_OP = 'INSERT' THEN
        event_type := 'object.created';
        event_data := json_build_object(
            'operation', TG_OP,
            'object_id', NEW.id,
            'path', NEW.path,
            'object_type', NEW.object_type,
            'building_id', NEW.building_id,
            'state', json_build_object(
                'status', NEW.status,
                'health', NEW.health,
                'needs_repair', NEW.needs_repair
            )
        );
    ELSIF TG_OP = 'UPDATE' THEN
        event_type := 'object.updated';
        event_data := json_build_object(
            'operation', TG_OP,
            'object_id', NEW.id,
            'path', NEW.path,
            'object_type', NEW.object_type,
            'building_id', NEW.building_id,
            'before', json_build_object(
                'status', OLD.status,
                'health', OLD.health,
                'needs_repair', OLD.needs_repair
            ),
            'after', json_build_object(
                'status', NEW.status,
                'health', NEW.health,
                'needs_repair', NEW.needs_repair
            ),
            'changed_fields', (
                SELECT json_object_agg(key, value)
                FROM (
                    SELECT key, value
                    FROM jsonb_each(to_jsonb(NEW))
                    WHERE to_jsonb(NEW) -> key != to_jsonb(OLD) -> key
                ) AS changes
            )
        );
    ELSIF TG_OP = 'DELETE' THEN
        event_type := 'object.deleted';
        event_data := json_build_object(
            'operation', TG_OP,
            'object_id', OLD.id,
            'path', OLD.path,
            'object_type', OLD.object_type,
            'building_id', OLD.building_id
        );
    END IF;
    
    -- Insert into events table
    INSERT INTO building_events (
        event_type,
        object_id,
        object_path,
        building_id,
        before_state,
        after_state,
        metadata
    ) VALUES (
        event_type,
        COALESCE(NEW.id, OLD.id),
        COALESCE(NEW.path, OLD.path),
        COALESCE(NEW.building_id, OLD.building_id),
        CASE WHEN TG_OP != 'INSERT' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN to_jsonb(NEW) ELSE NULL END,
        event_data
    );
    
    -- Send notification on multiple channels
    channel := 'arxos_events';
    PERFORM pg_notify(channel, event_data::text);
    
    -- Building-specific channel
    channel := 'building_' || COALESCE(NEW.building_id, OLD.building_id)::text;
    PERFORM pg_notify(channel, event_data::text);
    
    -- Type-specific channel
    channel := 'type_' || COALESCE(NEW.object_type, OLD.object_type);
    PERFORM pg_notify(channel, event_data::text);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for object changes
DROP TRIGGER IF EXISTS track_object_changes ON building_objects;
CREATE TRIGGER track_object_changes
AFTER INSERT OR UPDATE OR DELETE ON building_objects
FOR EACH ROW EXECUTE FUNCTION notify_object_change();

-- Function to get recent events
CREATE OR REPLACE FUNCTION get_recent_events(
    since TIMESTAMP DEFAULT NOW() - INTERVAL '1 hour',
    limit_count INTEGER DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    event_type VARCHAR,
    object_path TEXT,
    created_at TIMESTAMP,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.event_type,
        e.object_path,
        e.created_at,
        e.metadata
    FROM building_events e
    WHERE e.created_at >= since
    ORDER BY e.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;