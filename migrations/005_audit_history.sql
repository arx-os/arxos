-- Audit history table for tracking all changes
CREATE TABLE IF NOT EXISTS object_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_id UUID NOT NULL,
    building_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    
    -- Object state at time of operation
    path TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    parent_id UUID,
    
    -- Changed data
    old_properties JSONB,
    new_properties JSONB,
    old_state JSONB,
    new_state JSONB,
    old_metrics JSONB,
    new_metrics JSONB,
    
    -- Change metadata
    changed_fields TEXT[], -- Array of field names that changed
    change_summary TEXT, -- Human-readable summary
    
    -- Who/what made the change
    user_id UUID, -- Future: user who made the change
    api_key_id UUID, -- Future: API key used
    source VARCHAR(50), -- 'api', 'terminal', 'webhook', 'system'
    source_ip INET, -- IP address of requester
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    object_created_at TIMESTAMP,
    object_updated_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_history_object_id ON object_history(object_id, created_at DESC);
CREATE INDEX idx_history_building_id ON object_history(building_id, created_at DESC);
CREATE INDEX idx_history_operation ON object_history(operation, created_at DESC);
CREATE INDEX idx_history_created_at ON object_history(created_at DESC);
CREATE INDEX idx_history_path ON object_history(path);

-- Function to track object changes
CREATE OR REPLACE FUNCTION track_object_history()
RETURNS TRIGGER AS $$
DECLARE
    changed_fields TEXT[];
    change_summary TEXT;
    v_source VARCHAR(50);
BEGIN
    -- Determine source (could be set via session variable in future)
    v_source := COALESCE(current_setting('arxos.source', true), 'system');
    
    IF TG_OP = 'INSERT' THEN
        INSERT INTO object_history (
            object_id, building_id, operation,
            path, name, object_type, parent_id,
            new_properties, new_state, new_metrics,
            source, created_at,
            object_created_at, object_updated_at
        ) VALUES (
            NEW.id, NEW.building_id, 'INSERT',
            NEW.path, NEW.name, NEW.object_type, NEW.parent_id,
            NEW.properties, NEW.state, NEW.metrics,
            v_source, CURRENT_TIMESTAMP,
            NEW.created_at, NEW.updated_at
        );
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- Determine which fields changed
        changed_fields := ARRAY[]::TEXT[];
        
        IF OLD.path IS DISTINCT FROM NEW.path THEN
            changed_fields := array_append(changed_fields, 'path');
        END IF;
        IF OLD.name IS DISTINCT FROM NEW.name THEN
            changed_fields := array_append(changed_fields, 'name');
        END IF;
        IF OLD.properties IS DISTINCT FROM NEW.properties THEN
            changed_fields := array_append(changed_fields, 'properties');
        END IF;
        IF OLD.state IS DISTINCT FROM NEW.state THEN
            changed_fields := array_append(changed_fields, 'state');
        END IF;
        IF OLD.metrics IS DISTINCT FROM NEW.metrics THEN
            changed_fields := array_append(changed_fields, 'metrics');
        END IF;
        
        -- Create change summary
        change_summary := 'Updated ' || array_to_string(changed_fields, ', ');
        
        INSERT INTO object_history (
            object_id, building_id, operation,
            path, name, object_type, parent_id,
            old_properties, new_properties,
            old_state, new_state,
            old_metrics, new_metrics,
            changed_fields, change_summary,
            source, created_at,
            object_created_at, object_updated_at
        ) VALUES (
            NEW.id, NEW.building_id, 'UPDATE',
            NEW.path, NEW.name, NEW.object_type, NEW.parent_id,
            OLD.properties, NEW.properties,
            OLD.state, NEW.state,
            OLD.metrics, NEW.metrics,
            changed_fields, change_summary,
            v_source, CURRENT_TIMESTAMP,
            NEW.created_at, NEW.updated_at
        );
        
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO object_history (
            object_id, building_id, operation,
            path, name, object_type, parent_id,
            old_properties, old_state, old_metrics,
            source, created_at,
            object_created_at, object_updated_at
        ) VALUES (
            OLD.id, OLD.building_id, 'DELETE',
            OLD.path, OLD.name, OLD.object_type, OLD.parent_id,
            OLD.properties, OLD.state, OLD.metrics,
            v_source, CURRENT_TIMESTAMP,
            OLD.created_at, OLD.updated_at
        );
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for history tracking
CREATE TRIGGER object_history_trigger
AFTER INSERT OR UPDATE OR DELETE ON building_objects
FOR EACH ROW EXECUTE FUNCTION track_object_history();

-- Bulk operations tracking table
CREATE TABLE IF NOT EXISTS bulk_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id),
    operation_type VARCHAR(50) NOT NULL, -- 'update', 'delete', 'create'
    
    -- Operation details
    filter JSONB, -- Filter criteria used
    changes JSONB, -- Changes applied
    affected_count INTEGER DEFAULT 0,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- Results
    affected_objects UUID[], -- Array of affected object IDs
    
    -- Metadata
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bulk_operations_building ON bulk_operations(building_id, created_at DESC);
CREATE INDEX idx_bulk_operations_status ON bulk_operations(status, created_at DESC);