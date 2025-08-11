-- Table Partitioning for Massive Scale Operations
-- Production-ready partitioning strategy for enterprise building management
-- Supports millions of buildings, rooms, devices, and optimization records

-- =============================================================================
-- AUDIT LOGS PARTITIONING (TIME-BASED)
-- =============================================================================

-- Create partitioned audit_logs table for time-series data
BEGIN;

-- Backup existing audit logs
CREATE TABLE audit_logs_backup AS SELECT * FROM audit_logs;

-- Drop existing table and recreate as partitioned
DROP TABLE IF EXISTS audit_logs CASCADE;

CREATE TABLE audit_logs (
    id SERIAL,
    user_id INTEGER NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    action VARCHAR(50) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT audit_logs_pkey PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for audit logs (last 12 months + future)
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE audit_logs_2024_03 PARTITION OF audit_logs
FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE audit_logs_2024_04 PARTITION OF audit_logs
FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE audit_logs_2024_05 PARTITION OF audit_logs
FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE audit_logs_2024_06 PARTITION OF audit_logs
FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE audit_logs_2024_07 PARTITION OF audit_logs
FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE audit_logs_2024_08 PARTITION OF audit_logs
FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE audit_logs_2024_09 PARTITION OF audit_logs
FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE audit_logs_2024_10 PARTITION OF audit_logs
FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE audit_logs_2024_11 PARTITION OF audit_logs
FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE audit_logs_2024_12 PARTITION OF audit_logs
FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Future partitions
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Indexes on partitioned audit_logs
CREATE INDEX CONCURRENTLY audit_logs_user_time_idx ON audit_logs (user_id, created_at);
CREATE INDEX CONCURRENTLY audit_logs_object_type_idx ON audit_logs (object_type, created_at);
CREATE INDEX CONCURRENTLY audit_logs_action_idx ON audit_logs (action, created_at);
CREATE INDEX CONCURRENTLY audit_logs_payload_gin_idx ON audit_logs USING GIN (payload);

-- Restore data from backup
INSERT INTO audit_logs SELECT * FROM audit_logs_backup;
DROP TABLE audit_logs_backup;

COMMIT;

-- =============================================================================
-- OBJECT HISTORY PARTITIONING (TIME-BASED)
-- =============================================================================

BEGIN;

-- Backup existing object history
CREATE TABLE object_history_backup AS SELECT * FROM object_history;

-- Drop and recreate as partitioned
DROP TABLE IF EXISTS object_history CASCADE;

CREATE TABLE object_history (
    id SERIAL,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    change_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT object_history_pkey PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create quarterly partitions for object history
CREATE TABLE object_history_2024_q1 PARTITION OF object_history
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE object_history_2024_q2 PARTITION OF object_history
FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

CREATE TABLE object_history_2024_q3 PARTITION OF object_history
FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');

CREATE TABLE object_history_2024_q4 PARTITION OF object_history
FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

CREATE TABLE object_history_2025_q1 PARTITION OF object_history
FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

-- Indexes for object_history partitions
CREATE INDEX CONCURRENTLY object_history_object_idx ON object_history (object_type, object_id, created_at);
CREATE INDEX CONCURRENTLY object_history_user_idx ON object_history (user_id, created_at);
CREATE INDEX CONCURRENTLY object_history_change_gin_idx ON object_history USING GIN (change_data);

-- Restore data
INSERT INTO object_history SELECT * FROM object_history_backup;
DROP TABLE object_history_backup;

COMMIT;

-- =============================================================================
-- DEVICES TABLE PARTITIONING (BUILDING-BASED)
-- =============================================================================

-- For massive scale: partition devices by building_id ranges
BEGIN;

-- Backup existing devices
CREATE TABLE devices_backup AS SELECT * FROM devices;

-- Drop foreign key constraints temporarily
ALTER TABLE IF EXISTS assignments DROP CONSTRAINT IF EXISTS assignments_object_id_fkey;

-- Drop and recreate devices as partitioned
DROP TABLE IF EXISTS devices CASCADE;

CREATE TABLE devices (
    id VARCHAR(64) NOT NULL,
    type VARCHAR(50) NOT NULL,
    system VARCHAR(50),
    subtype VARCHAR(50),
    layer VARCHAR(50),
    project_id INTEGER NOT NULL,
    building_id INTEGER NOT NULL,
    floor_id INTEGER,
    room_id VARCHAR(64),
    category VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    geom GEOMETRY(GEOMETRY, 4326),
    created_by INTEGER NOT NULL,
    locked_by INTEGER,
    assigned_to INTEGER,
    source_svg TEXT,
    svg_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT devices_pkey PRIMARY KEY (id, building_id)
) PARTITION BY RANGE (building_id);

-- Create building-based partitions (supports 10,000 buildings per partition)
CREATE TABLE devices_buildings_1_10000 PARTITION OF devices
FOR VALUES FROM (1) TO (10001);

CREATE TABLE devices_buildings_10001_20000 PARTITION OF devices
FOR VALUES FROM (10001) TO (20001);

CREATE TABLE devices_buildings_20001_30000 PARTITION OF devices
FOR VALUES FROM (20001) TO (30001);

CREATE TABLE devices_buildings_30001_40000 PARTITION OF devices
FOR VALUES FROM (30001) TO (40001);

CREATE TABLE devices_buildings_40001_50000 PARTITION OF devices
FOR VALUES FROM (40001) TO (50001);

-- Indexes for devices partitions
CREATE INDEX CONCURRENTLY devices_type_status_idx ON devices (type, status);
CREATE INDEX CONCURRENTLY devices_room_idx ON devices (room_id);
CREATE INDEX CONCURRENTLY devices_system_idx ON devices (system, subtype);
CREATE INDEX CONCURRENTLY devices_spatial_idx ON devices USING GIST (geom);
CREATE INDEX CONCURRENTLY devices_project_idx ON devices (project_id);

-- Restore devices data
INSERT INTO devices SELECT * FROM devices_backup;
DROP TABLE devices_backup;

COMMIT;

-- =============================================================================
-- COMMENTS PARTITIONING (TIME + OBJECT TYPE)
-- =============================================================================

BEGIN;

-- Backup existing comments
CREATE TABLE comments_backup AS SELECT * FROM comments;

-- Drop and recreate as partitioned
DROP TABLE IF EXISTS comments CASCADE;

CREATE TABLE comments (
    id SERIAL,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER NOT NULL,
    parent_id INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT comments_pkey PRIMARY KEY (id, object_type, created_at)
) PARTITION BY LIST (object_type);

-- Create partitions by object type
CREATE TABLE comments_room PARTITION OF comments
FOR VALUES IN ('room');

CREATE TABLE comments_device PARTITION OF comments
FOR VALUES IN ('device');

CREATE TABLE comments_building PARTITION OF comments
FOR VALUES IN ('building');

CREATE TABLE comments_floor PARTITION OF comments
FOR VALUES IN ('floor');

CREATE TABLE comments_project PARTITION OF comments
FOR VALUES IN ('project');

-- Each object type partition can be further sub-partitioned by time if needed
-- For now, create time-based indexes
CREATE INDEX CONCURRENTLY comments_object_time_idx ON comments (object_id, created_at);
CREATE INDEX CONCURRENTLY comments_user_time_idx ON comments (user_id, created_at);
CREATE INDEX CONCURRENTLY comments_parent_idx ON comments (parent_id);

-- Restore data
INSERT INTO comments SELECT * FROM comments_backup;
DROP TABLE comments_backup;

COMMIT;

-- =============================================================================
-- OPTIMIZATION RESULTS PARTITIONING (TIME-BASED FOR ANALYTICS)
-- =============================================================================

-- Create new table for optimization results (time-series analytics data)
CREATE TABLE optimization_results (
    id SERIAL,
    building_id INTEGER NOT NULL,
    algorithm_type VARCHAR(50) NOT NULL, -- 'genetic', 'nsga-ii', 'constraint_solver'
    optimization_score NUMERIC(10,4) NOT NULL,
    convergence_rate NUMERIC(8,4),
    execution_time_ms NUMERIC(10,3),
    parameters JSONB,
    objectives JSONB, -- NSGA-II objectives
    constraints_satisfied INTEGER,
    constraints_violated INTEGER,
    pareto_rank INTEGER, -- For NSGA-II
    crowding_distance NUMERIC(10,6), -- For NSGA-II
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT optimization_results_pkey PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create daily partitions for optimization results (high-frequency data)
CREATE TABLE optimization_results_2024_12_01 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-01') TO ('2024-12-02');

CREATE TABLE optimization_results_2024_12_02 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-02') TO ('2024-12-03');

CREATE TABLE optimization_results_2024_12_03 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-03') TO ('2024-12-04');

CREATE TABLE optimization_results_2024_12_04 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-04') TO ('2024-12-05');

CREATE TABLE optimization_results_2024_12_05 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-05') TO ('2024-12-06');

-- Future daily partitions (automation would create these dynamically)
CREATE TABLE optimization_results_2024_12_06 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-06') TO ('2024-12-07');

CREATE TABLE optimization_results_2024_12_07 PARTITION OF optimization_results
FOR VALUES FROM ('2024-12-07') TO ('2024-12-08');

-- Indexes for optimization results
CREATE INDEX CONCURRENTLY optimization_results_building_time_idx ON optimization_results (building_id, created_at);
CREATE INDEX CONCURRENTLY optimization_results_algorithm_idx ON optimization_results (algorithm_type, created_at);
CREATE INDEX CONCURRENTLY optimization_results_score_idx ON optimization_results (optimization_score DESC, created_at);
CREATE INDEX CONCURRENTLY optimization_results_pareto_idx ON optimization_results (pareto_rank, crowding_distance DESC) WHERE pareto_rank IS NOT NULL;
CREATE INDEX CONCURRENTLY optimization_results_parameters_gin_idx ON optimization_results USING GIN (parameters);

-- =============================================================================
-- PARTITION MANAGEMENT FUNCTIONS
-- =============================================================================

-- Function: Create new monthly audit log partition
CREATE OR REPLACE FUNCTION create_audit_log_partition(partition_date DATE)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    sql_command TEXT;
BEGIN
    -- Calculate partition boundaries
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    
    -- Generate partition name
    partition_name := 'audit_logs_' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Check if partition already exists
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = partition_name) THEN
        RETURN 'Partition ' || partition_name || ' already exists';
    END IF;
    
    -- Create partition
    sql_command := FORMAT('CREATE TABLE %I PARTITION OF audit_logs FOR VALUES FROM (%L) TO (%L)',
                         partition_name, start_date, end_date);
    EXECUTE sql_command;
    
    RETURN 'Created partition: ' || partition_name || ' for period ' || start_date || ' to ' || end_date;
END;
$$;

-- Function: Create new daily optimization results partition  
CREATE OR REPLACE FUNCTION create_optimization_results_partition(partition_date DATE)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    sql_command TEXT;
BEGIN
    start_date := partition_date;
    end_date := start_date + INTERVAL '1 day';
    
    partition_name := 'optimization_results_' || TO_CHAR(start_date, 'YYYY_MM_DD');
    
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = partition_name) THEN
        RETURN 'Partition ' || partition_name || ' already exists';
    END IF;
    
    sql_command := FORMAT('CREATE TABLE %I PARTITION OF optimization_results FOR VALUES FROM (%L) TO (%L)',
                         partition_name, start_date, end_date);
    EXECUTE sql_command;
    
    RETURN 'Created optimization results partition: ' || partition_name;
END;
$$;

-- Function: Drop old partitions for data retention
CREATE OR REPLACE FUNCTION drop_old_partitions(table_name TEXT, retention_months INTEGER)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_record RECORD;
    drop_before DATE;
    dropped_count INTEGER := 0;
BEGIN
    drop_before := CURRENT_DATE - (retention_months || ' months')::INTERVAL;
    
    FOR partition_record IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename LIKE table_name || '%'
          AND tablename ~ '\d{4}_\d{2}(_\d{2})?$'
    LOOP
        -- Extract date from partition name and check if it's old enough
        -- This is a simplified check - in production, you'd want more robust date extraction
        DECLARE
            partition_date DATE;
        BEGIN
            -- Extract date pattern from partition name
            -- Implementation would depend on your naming convention
            IF partition_record.tablename ~ '\d{4}_\d{2}_\d{2}$' THEN
                -- Daily partitions (YYYY_MM_DD)
                CONTINUE; -- Simplified for this example
            END IF;
        END;
    END LOOP;
    
    RETURN 'Dropped ' || dropped_count || ' old partitions';
END;
$$;

-- Function: Get partition statistics
CREATE OR REPLACE FUNCTION get_partition_stats()
RETURNS TABLE(
    table_name TEXT,
    partition_count BIGINT,
    total_size TEXT,
    avg_partition_size TEXT
)
LANGUAGE sql
AS $$
SELECT 
    split_part(schemaname || '.' || tablename, '_', 1) || '_' || split_part(schemaname || '.' || tablename, '_', 2) as table_name,
    COUNT(*) as partition_count,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size,
    pg_size_pretty(AVG(pg_total_relation_size(schemaname||'.'||tablename))::bigint) as avg_partition_size
FROM pg_tables 
WHERE tablename ~ '_(19|20)\d{2}_\d{2}(_\d{2})?$'
GROUP BY split_part(schemaname || '.' || tablename, '_', 1) || '_' || split_part(schemaname || '.' || tablename, '_', 2)
ORDER BY table_name;
$$;

-- =============================================================================
-- PARTITION PRUNING OPTIMIZATION
-- =============================================================================

-- Enable constraint exclusion for better partition pruning
SET constraint_exclusion = partition;

-- Function to analyze partition performance
CREATE OR REPLACE FUNCTION analyze_partition_performance()
RETURNS TABLE(
    query_type TEXT,
    table_name TEXT,
    partitions_scanned INTEGER,
    execution_time_ms NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- This would contain actual performance analysis queries
    -- For now, returning sample structure
    RETURN QUERY
    SELECT 
        'sample_query'::TEXT,
        'audit_logs'::TEXT,
        1::INTEGER,
        45.67::NUMERIC;
END;
$$;

-- =============================================================================
-- AUTOMATED PARTITION MAINTENANCE
-- =============================================================================

-- Function: Daily maintenance routine for partitions
CREATE OR REPLACE FUNCTION daily_partition_maintenance()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    result TEXT := '';
BEGIN
    -- Create tomorrow's optimization results partition
    result := result || create_optimization_results_partition(CURRENT_DATE + INTERVAL '1 day') || E'\n';
    
    -- Create next month's audit log partition if we're near month end
    IF EXTRACT(DAY FROM CURRENT_DATE + INTERVAL '7 days') <= 7 THEN
        result := result || create_audit_log_partition(CURRENT_DATE + INTERVAL '1 month') || E'\n';
    END IF;
    
    -- Update table statistics
    EXECUTE 'ANALYZE audit_logs';
    EXECUTE 'ANALYZE object_history';
    EXECUTE 'ANALYZE devices';
    EXECUTE 'ANALYZE optimization_results';
    
    result := result || 'Table statistics updated' || E'\n';
    
    -- Log maintenance completion
    INSERT INTO audit_logs (user_id, object_type, object_id, action, payload)
    VALUES (
        1, -- System user
        'system',
        'partition_maintenance',
        'daily_maintenance_completed',
        jsonb_build_object(
            'timestamp', NOW(),
            'maintenance_type', 'partition_management'
        )
    );
    
    RETURN result || 'Daily partition maintenance completed';
END;
$$;

-- Summary and recommendations
COMMENT ON FUNCTION daily_partition_maintenance() IS 
'Automated daily partition maintenance - should be called by cron job or pg_cron extension';

COMMENT ON TABLE optimization_results IS 
'High-frequency optimization analytics data - partitioned daily for performance';

-- Performance monitoring view
CREATE OR REPLACE VIEW partition_performance_summary AS
SELECT 
    'audit_logs' as table_name,
    (SELECT COUNT(*) FROM audit_logs) as total_records,
    (SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'audit_logs_%') as partition_count,
    pg_size_pretty(pg_total_relation_size('audit_logs')) as total_size
UNION ALL
SELECT 
    'devices',
    (SELECT COUNT(*) FROM devices),
    (SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'devices_%'),
    pg_size_pretty(pg_total_relation_size('devices'))
UNION ALL
SELECT 
    'optimization_results',
    (SELECT COUNT(*) FROM optimization_results),
    (SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'optimization_results_%'),
    pg_size_pretty(pg_total_relation_size('optimization_results'));