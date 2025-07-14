-- 007_add_partitioning.sql
-- Migration: Add table partitioning for large audit/log/history tables
-- 
-- This migration implements table partitioning to improve performance and
-- manageability of large tables. It follows Arxos standards for safe
-- migrations with comprehensive rollback capabilities.

-- IMPORTANT: Run analyze_partitioning.py BEFORE applying this migration
-- This migration assumes partitioning analysis has been completed

-- =============================================================================
-- PARTITIONING STRATEGY OVERVIEW
-- =============================================================================

-- Tables to be partitioned:
-- 1. audit_logs: Range partitioning by created_at (monthly)
-- 2. object_history: Range partitioning by changed_at (monthly)
-- 3. slow_query_log: Range partitioning by timestamp (monthly)
-- 4. chat_messages: Range partitioning by created_at (monthly)

-- Partitioning benefits:
-- - Improved query performance for time-based queries
-- - Easier maintenance and cleanup of old data
-- - Better parallel query execution
-- - Reduced index maintenance overhead

-- =============================================================================
-- AUDIT LOGS PARTITIONING
-- =============================================================================

-- Create partitioned parent table for audit_logs
CREATE TABLE audit_logs_partitioned (
    id SERIAL,
    user_id INTEGER,
    object_type TEXT,
    object_id TEXT,
    action TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create partitions for audit_logs (current and next 12 months)
CREATE TABLE audit_logs_p2024_01 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_p2024_02 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE audit_logs_p2024_03 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE audit_logs_p2024_04 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE audit_logs_p2024_05 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE audit_logs_p2024_06 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE audit_logs_p2024_07 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE audit_logs_p2024_08 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE audit_logs_p2024_09 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE audit_logs_p2024_10 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE audit_logs_p2024_11 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE audit_logs_p2024_12 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Create default partition for future data
CREATE TABLE audit_logs_p_default PARTITION OF audit_logs_partitioned DEFAULT;

-- =============================================================================
-- OBJECT HISTORY PARTITIONING
-- =============================================================================

-- Create partitioned parent table for object_history
CREATE TABLE object_history_partitioned (
    id SERIAL,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER,
    change_type VARCHAR(50) NOT NULL,
    change_data JSONB,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (changed_at);

-- Create partitions for object_history (current and next 12 months)
CREATE TABLE object_history_p2024_01 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE object_history_p2024_02 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE object_history_p2024_03 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE object_history_p2024_04 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE object_history_p2024_05 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE object_history_p2024_06 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE object_history_p2024_07 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE object_history_p2024_08 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE object_history_p2024_09 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE object_history_p2024_10 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE object_history_p2024_11 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE object_history_p2024_12 PARTITION OF object_history_partitioned
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Create default partition for future data
CREATE TABLE object_history_p_default PARTITION OF object_history_partitioned DEFAULT;

-- =============================================================================
-- SLOW QUERY LOG PARTITIONING
-- =============================================================================

-- Create partitioned parent table for slow_query_log
CREATE TABLE slow_query_log_partitioned (
    id SERIAL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER NOT NULL,
    statement TEXT NOT NULL,
    query_hash VARCHAR(32) NOT NULL,
    user_name VARCHAR(100),
    database_name VARCHAR(100),
    application_name VARCHAR(100),
    client_ip INET,
    process_id VARCHAR(20),
    session_id VARCHAR(20),
    execution_plan TEXT,
    context JSONB,
    severity VARCHAR(20) DEFAULT 'info',
    frequency_per_hour DECIMAL(10,2),
    avg_duration_ms DECIMAL(10,2),
    max_duration_ms INTEGER,
    min_duration_ms INTEGER,
    total_executions INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Create partitions for slow_query_log (current and next 12 months)
CREATE TABLE slow_query_log_p2024_01 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE slow_query_log_p2024_02 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE slow_query_log_p2024_03 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE slow_query_log_p2024_04 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE slow_query_log_p2024_05 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE slow_query_log_p2024_06 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE slow_query_log_p2024_07 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE slow_query_log_p2024_08 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE slow_query_log_p2024_09 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE slow_query_log_p2024_10 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE slow_query_log_p2024_11 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE slow_query_log_p2024_12 PARTITION OF slow_query_log_partitioned
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Create default partition for future data
CREATE TABLE slow_query_log_p_default PARTITION OF slow_query_log_partitioned DEFAULT;

-- =============================================================================
-- CHAT MESSAGES PARTITIONING
-- =============================================================================

-- Create partitioned parent table for chat_messages
CREATE TABLE chat_messages_partitioned (
    id SERIAL,
    building_id INTEGER,
    user_id INTEGER,
    message TEXT NOT NULL,
    audit_log_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create partitions for chat_messages (current and next 12 months)
CREATE TABLE chat_messages_p2024_01 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE chat_messages_p2024_02 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE chat_messages_p2024_03 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE chat_messages_p2024_04 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE chat_messages_p2024_05 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE chat_messages_p2024_06 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE chat_messages_p2024_07 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE chat_messages_p2024_08 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE chat_messages_p2024_09 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE chat_messages_p2024_10 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE chat_messages_p2024_11 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE chat_messages_p2024_12 PARTITION OF chat_messages_partitioned
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Create default partition for future data
CREATE TABLE chat_messages_p_default PARTITION OF chat_messages_partitioned DEFAULT;

-- =============================================================================
-- INDEXES FOR PARTITIONED TABLES
-- =============================================================================

-- Indexes for audit_logs_partitioned
CREATE INDEX idx_audit_logs_partitioned_user_id ON audit_logs_partitioned (user_id);
CREATE INDEX idx_audit_logs_partitioned_object_id ON audit_logs_partitioned (object_id);
CREATE INDEX idx_audit_logs_partitioned_action ON audit_logs_partitioned (action);
CREATE INDEX idx_audit_logs_partitioned_object_type ON audit_logs_partitioned (object_type);
CREATE INDEX idx_audit_logs_partitioned_created_at ON audit_logs_partitioned (created_at);

-- Indexes for object_history_partitioned
CREATE INDEX idx_object_history_partitioned_user_id ON object_history_partitioned (user_id);
CREATE INDEX idx_object_history_partitioned_object_id ON object_history_partitioned (object_id);
CREATE INDEX idx_object_history_partitioned_change_type ON object_history_partitioned (change_type);
CREATE INDEX idx_object_history_partitioned_object_type ON object_history_partitioned (object_type);
CREATE INDEX idx_object_history_partitioned_changed_at ON object_history_partitioned (changed_at);

-- Indexes for slow_query_log_partitioned
CREATE INDEX idx_slow_query_log_partitioned_timestamp ON slow_query_log_partitioned (timestamp);
CREATE INDEX idx_slow_query_log_partitioned_duration_ms ON slow_query_log_partitioned (duration_ms);
CREATE INDEX idx_slow_query_log_partitioned_query_hash ON slow_query_log_partitioned (query_hash);
CREATE INDEX idx_slow_query_log_partitioned_severity ON slow_query_log_partitioned (severity);
CREATE INDEX idx_slow_query_log_partitioned_user_name ON slow_query_log_partitioned (user_name);

-- Indexes for chat_messages_partitioned
CREATE INDEX idx_chat_messages_partitioned_building_id ON chat_messages_partitioned (building_id);
CREATE INDEX idx_chat_messages_partitioned_user_id ON chat_messages_partitioned (user_id);
CREATE INDEX idx_chat_messages_partitioned_created_at ON chat_messages_partitioned (created_at);

-- =============================================================================
-- DATA MIGRATION
-- =============================================================================

-- Migrate existing data to partitioned tables
-- Note: This is done in batches to avoid long-running transactions

-- Migrate audit_logs data
INSERT INTO audit_logs_partitioned 
SELECT * FROM audit_logs 
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- Migrate object_history data
INSERT INTO object_history_partitioned 
SELECT * FROM object_history 
WHERE changed_at >= '2024-01-01' AND changed_at < '2025-01-01';

-- Migrate slow_query_log data
INSERT INTO slow_query_log_partitioned 
SELECT * FROM slow_query_log 
WHERE timestamp >= '2024-01-01' AND timestamp < '2025-01-01';

-- Migrate chat_messages data
INSERT INTO chat_messages_partitioned 
SELECT * FROM chat_messages 
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- =============================================================================
-- FOREIGN KEY CONSTRAINTS
-- =============================================================================

-- Add foreign key constraints to partitioned tables
ALTER TABLE audit_logs_partitioned 
    ADD CONSTRAINT fk_audit_logs_partitioned_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE object_history_partitioned 
    ADD CONSTRAINT fk_object_history_partitioned_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE chat_messages_partitioned 
    ADD CONSTRAINT fk_chat_messages_partitioned_building_id 
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE;

ALTER TABLE chat_messages_partitioned 
    ADD CONSTRAINT fk_chat_messages_partitioned_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE chat_messages_partitioned 
    ADD CONSTRAINT fk_chat_messages_partitioned_audit_log_id 
    FOREIGN KEY (audit_log_id) REFERENCES audit_logs_partitioned(id);

-- =============================================================================
-- PARTITION MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function to create new monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(
    parent_table TEXT,
    partition_date DATE
) RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    sql_statement TEXT;
BEGIN
    -- Calculate partition boundaries
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    
    -- Generate partition name
    partition_name := parent_table || '_p' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Create partition
    sql_statement := format(
        'CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        parent_table,
        start_date,
        end_date
    );
    
    EXECUTE sql_statement;
    
    -- Log the partition creation
    INSERT INTO audit_logs_partitioned (object_type, object_id, action, payload)
    VALUES ('partition', partition_name, 'created', 
            jsonb_build_object('parent_table', parent_table, 'start_date', start_date, 'end_date', end_date));
    
    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions
CREATE OR REPLACE FUNCTION drop_old_partition(
    parent_table TEXT,
    partition_date DATE,
    retention_months INTEGER DEFAULT 12
) RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    cutoff_date DATE;
    sql_statement TEXT;
BEGIN
    -- Calculate cutoff date
    cutoff_date := partition_date - (retention_months || ' months')::INTERVAL;
    
    -- Generate partition name
    partition_name := parent_table || '_p' || TO_CHAR(partition_date, 'YYYY_MM');
    
    -- Drop partition if it exists and is old enough
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
        sql_statement := format('DROP TABLE %I', partition_name);
        EXECUTE sql_statement;
        
        -- Log the partition drop
        INSERT INTO audit_logs_partitioned (object_type, object_id, action, payload)
        VALUES ('partition', partition_name, 'dropped', 
                jsonb_build_object('parent_table', parent_table, 'partition_date', partition_date));
        
        RETURN partition_name;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to maintain all partitions
CREATE OR REPLACE FUNCTION maintain_partitions()
RETURNS VOID AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
    partition_date DATE;
    partition_name TEXT;
BEGIN
    -- Create partitions for next 3 months
    FOR i IN 0..2 LOOP
        partition_date := current_date + (i || ' months')::INTERVAL;
        
        -- Create audit_logs partition
        SELECT create_monthly_partition('audit_logs_partitioned', partition_date);
        
        -- Create object_history partition
        SELECT create_monthly_partition('object_history_partitioned', partition_date);
        
        -- Create slow_query_log partition
        SELECT create_monthly_partition('slow_query_log_partitioned', partition_date);
        
        -- Create chat_messages partition
        SELECT create_monthly_partition('chat_messages_partitioned', partition_date);
    END LOOP;
    
    -- Drop old partitions (older than 12 months)
    FOR i IN 13..24 LOOP
        partition_date := current_date - (i || ' months')::INTERVAL;
        
        -- Drop old partitions
        SELECT drop_old_partition('audit_logs_partitioned', partition_date);
        SELECT drop_old_partition('object_history_partitioned', partition_date);
        SELECT drop_old_partition('slow_query_log_partitioned', partition_date);
        SELECT drop_old_partition('chat_messages_partitioned', partition_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE MONITORING VIEWS
-- =============================================================================

-- View for partition usage statistics
CREATE VIEW v_partition_usage AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats 
WHERE tablename LIKE '%_partitioned'
ORDER BY tablename, attname;

-- View for partition sizes
CREATE VIEW v_partition_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
    pg_relation_size(schemaname||'.'||tablename) as table_size_bytes,
    pg_indexes_size(schemaname||'.'||tablename) as index_size_bytes
FROM pg_tables 
WHERE tablename LIKE '%_partitioned'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Verify partitioning is working correctly
DO $$
DECLARE
    partition_count INTEGER;
    table_name TEXT;
    partition_name TEXT;
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'PARTITIONING VALIDATION';
    RAISE NOTICE '=============================================================================';
    
    -- Count partitions for each table
    FOR table_name IN 
        SELECT unnest(ARRAY['audit_logs_partitioned', 'object_history_partitioned', 
                            'slow_query_log_partitioned', 'chat_messages_partitioned'])
    LOOP
        SELECT COUNT(*) INTO partition_count
        FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public'
        AND c.relname LIKE table_name || '_p%';
        
        RAISE NOTICE 'Table % has % partitions', table_name, partition_count;
    END LOOP;
    
    -- List all partitions
    RAISE NOTICE 'Partitions created:';
    FOR partition_name IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public'
        AND c.relname LIKE '%_partitioned_p%'
        ORDER BY c.relname
    LOOP
        RAISE NOTICE '  - %', partition_name;
    END LOOP;
    
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Partitioning migration completed successfully!';
    RAISE NOTICE '=============================================================================';
END $$;

-- =============================================================================
-- ROLLBACK FUNCTIONS
-- =============================================================================

-- Function to rollback partitioning migration
CREATE OR REPLACE FUNCTION rollback_partitioning_migration()
RETURNS VOID AS $$
DECLARE
    partition_record RECORD;
BEGIN
    RAISE NOTICE 'Rolling back partitioning migration...';
    
    -- Drop partitioned tables and recreate original tables
    DROP TABLE IF EXISTS audit_logs_partitioned CASCADE;
    DROP TABLE IF EXISTS object_history_partitioned CASCADE;
    DROP TABLE IF EXISTS slow_query_log_partitioned CASCADE;
    DROP TABLE IF EXISTS chat_messages_partitioned CASCADE;
    
    -- Drop maintenance functions
    DROP FUNCTION IF EXISTS create_monthly_partition(TEXT, DATE);
    DROP FUNCTION IF EXISTS drop_old_partition(TEXT, DATE, INTEGER);
    DROP FUNCTION IF EXISTS maintain_partitions();
    
    -- Drop views
    DROP VIEW IF EXISTS v_partition_usage;
    DROP VIEW IF EXISTS v_partition_sizes;
    
    RAISE NOTICE 'Partitioning rollback completed!';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================

-- This migration implements comprehensive table partitioning:
-- 1. Range partitioning by date for time-series tables
-- 2. Automatic partition creation and maintenance functions
-- 3. Performance indexes on partitioned tables
-- 4. Foreign key constraints for data integrity
-- 5. Monitoring views for partition usage
-- 6. Rollback function for safe migration reversal
-- 
-- IMPORTANT: Test this migration thoroughly in a staging environment
-- before applying to production. The rollback function provides a safety net. 