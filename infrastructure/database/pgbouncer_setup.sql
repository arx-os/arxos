-- PgBouncer Connection Pooling Configuration
-- Production-ready connection pooling for high-traffic optimization engine
-- Supports thousands of concurrent connections with enterprise security

-- =============================================================================
-- DATABASE PREPARATION FOR PGBOUNCER
-- =============================================================================

-- Create pgbouncer admin user
CREATE USER pgbouncer_admin WITH PASSWORD 'pgb_secure_2024!';
GRANT CONNECT ON DATABASE arxos_db_pg17 TO pgbouncer_admin;

-- Create application connection users with different privilege levels
CREATE USER arxos_api_user WITH PASSWORD 'arxos_api_2024!';
CREATE USER arxos_optimizer_user WITH PASSWORD 'arxos_opt_2024!';
CREATE USER arxos_analytics_user WITH PASSWORD 'arxos_analytics_2024!';
CREATE USER arxos_readonly_user WITH PASSWORD 'arxos_read_2024!';

-- Grant appropriate permissions to application users
-- API User - Full CRUD access
GRANT CONNECT ON DATABASE arxos_db_pg17 TO arxos_api_user;
GRANT USAGE ON SCHEMA public TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO arxos_api_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO arxos_api_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arxos_api_user;

-- Optimizer User - Full access plus optimization functions
GRANT CONNECT ON DATABASE arxos_db_pg17 TO arxos_optimizer_user;
GRANT USAGE ON SCHEMA public TO arxos_optimizer_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO arxos_optimizer_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO arxos_optimizer_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arxos_optimizer_user;

-- Analytics User - Read access plus materialized view refresh
GRANT CONNECT ON DATABASE arxos_db_pg17 TO arxos_analytics_user;
GRANT USAGE ON SCHEMA public TO arxos_analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO arxos_analytics_user;
GRANT REFRESH ON ALL MATERIALIZED VIEWS IN SCHEMA public TO arxos_analytics_user;
GRANT EXECUTE ON FUNCTION refresh_all_analytics_views() TO arxos_analytics_user;

-- Read-only User - Dashboard and reporting access
GRANT CONNECT ON DATABASE arxos_db_pg17 TO arxos_readonly_user;
GRANT USAGE ON SCHEMA public TO arxos_readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO arxos_readonly_user;
GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA public TO arxos_readonly_user;

-- =============================================================================
-- CONNECTION STATISTICS AND MONITORING FUNCTIONS
-- =============================================================================

-- Function to monitor current connections
CREATE OR REPLACE FUNCTION get_connection_stats()
RETURNS TABLE(
    database_name name,
    username name,
    client_addr inet,
    state text,
    query_start timestamptz,
    backend_start timestamptz,
    connection_count bigint
)
LANGUAGE sql
AS $$
SELECT 
    datname as database_name,
    usename as username,
    client_addr,
    state,
    query_start,
    backend_start,
    COUNT(*) OVER (PARTITION BY usename) as connection_count
FROM pg_stat_activity 
WHERE datname IS NOT NULL
ORDER BY backend_start DESC;
$$;

-- Function to analyze connection patterns
CREATE OR REPLACE FUNCTION analyze_connection_patterns()
RETURNS TABLE(
    username name,
    total_connections bigint,
    active_connections bigint,
    idle_connections bigint,
    avg_connection_duration interval
)
LANGUAGE sql
AS $$
SELECT 
    usename as username,
    COUNT(*) as total_connections,
    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections,
    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections,
    AVG(NOW() - backend_start) as avg_connection_duration
FROM pg_stat_activity 
WHERE datname IS NOT NULL
GROUP BY usename
ORDER BY total_connections DESC;
$$;

-- =============================================================================
-- PGBOUNCER CONFIGURATION PREPARATION
-- =============================================================================

-- Function to generate PgBouncer configuration
CREATE OR REPLACE FUNCTION generate_pgbouncer_config()
RETURNS TABLE(config_section text, config_content text)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Database section
    RETURN QUERY SELECT 
        '[databases]'::text as config_section,
        E'arxos_production = host=localhost port=5432 dbname=arxos_db_pg17 user=pgbouncer_admin\n' ||
        E'arxos_api = host=localhost port=5432 dbname=arxos_db_pg17 user=arxos_api_user\n' ||
        E'arxos_optimization = host=localhost port=5432 dbname=arxos_db_pg17 user=arxos_optimizer_user\n' ||
        E'arxos_analytics = host=localhost port=5432 dbname=arxos_db_pg17 user=arxos_analytics_user\n' ||
        E'arxos_readonly = host=localhost port=5432 dbname=arxos_db_pg17 user=arxos_readonly_user\n'
        as config_content;
    
    -- PgBouncer settings
    RETURN QUERY SELECT 
        '[pgbouncer]'::text,
        E'listen_addr = *\n' ||
        E'listen_port = 6432\n' ||
        E'auth_type = md5\n' ||
        E'auth_file = /etc/pgbouncer/userlist.txt\n' ||
        E'admin_users = pgbouncer_admin\n' ||
        E'pool_mode = transaction\n' ||
        E'max_client_conn = 1000\n' ||
        E'default_pool_size = 20\n' ||
        E'min_pool_size = 5\n' ||
        E'reserve_pool_size = 10\n' ||
        E'max_db_connections = 100\n' ||
        E'max_user_connections = 50\n' ||
        E'server_round_robin = 1\n' ||
        E'ignore_startup_parameters = extra_float_digits\n' ||
        E'application_name_add_host = 1\n' ||
        E'server_lifetime = 3600\n' ||
        E'server_idle_timeout = 600\n' ||
        E'log_connections = 1\n' ||
        E'log_disconnections = 1\n' ||
        E'log_pooler_errors = 1\n' ||
        E'stats_period = 60\n' ||
        E'verbose = 0\n'
        as config_content;
END;
$$;

-- =============================================================================
-- CONNECTION POOL OPTIMIZATION FUNCTIONS
-- =============================================================================

-- Function to calculate optimal pool sizes based on workload
CREATE OR REPLACE FUNCTION calculate_optimal_pool_size(
    expected_concurrent_users INTEGER DEFAULT 500,
    avg_query_duration_ms INTEGER DEFAULT 100,
    target_response_time_ms INTEGER DEFAULT 200
)
RETURNS TABLE(
    workload_type text,
    recommended_pool_size integer,
    max_connections integer,
    reasoning text
)
LANGUAGE plpgsql
AS $$
DECLARE
    api_pool_size INTEGER;
    optimization_pool_size INTEGER;
    analytics_pool_size INTEGER;
    readonly_pool_size INTEGER;
BEGIN
    -- Calculate pool sizes based on Little's Law: L = λW
    -- Where L = pool size, λ = arrival rate, W = service time
    
    -- API workload (70% of traffic, fast queries)
    api_pool_size := CEIL(expected_concurrent_users * 0.7 * (avg_query_duration_ms::NUMERIC / 1000) / (target_response_time_ms::NUMERIC / 1000));
    
    -- Optimization workload (10% of traffic, longer queries)
    optimization_pool_size := CEIL(expected_concurrent_users * 0.1 * (avg_query_duration_ms::NUMERIC * 5 / 1000) / (target_response_time_ms::NUMERIC / 1000));
    
    -- Analytics workload (15% of traffic, medium queries)
    analytics_pool_size := CEIL(expected_concurrent_users * 0.15 * (avg_query_duration_ms::NUMERIC * 2 / 1000) / (target_response_time_ms::NUMERIC / 1000));
    
    -- Read-only workload (5% of traffic, fast queries)
    readonly_pool_size := CEIL(expected_concurrent_users * 0.05 * (avg_query_duration_ms::NUMERIC / 1000) / (target_response_time_ms::NUMERIC / 1000));
    
    -- Return recommendations
    RETURN QUERY VALUES
        ('api_workload', api_pool_size, api_pool_size * 2, 'Fast CRUD operations, high concurrency'),
        ('optimization_workload', optimization_pool_size, optimization_pool_size * 3, 'Long-running optimization algorithms'),
        ('analytics_workload', analytics_pool_size, analytics_pool_size * 2, 'Materialized view refresh and reporting'),
        ('readonly_workload', readonly_pool_size, readonly_pool_size * 2, 'Dashboard queries and monitoring');
END;
$$;

-- Function to monitor pool performance
CREATE OR REPLACE FUNCTION get_pool_performance_metrics()
RETURNS TABLE(
    metric_name text,
    current_value numeric,
    recommended_action text
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_connections INTEGER;
    active_connections INTEGER;
    idle_connections INTEGER;
    connection_utilization NUMERIC;
BEGIN
    -- Get current connection statistics
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN state = 'active' THEN 1 END),
        COUNT(CASE WHEN state = 'idle' THEN 1 END)
    INTO total_connections, active_connections, idle_connections
    FROM pg_stat_activity 
    WHERE datname IS NOT NULL;
    
    connection_utilization := CASE 
        WHEN total_connections > 0 THEN active_connections::NUMERIC / total_connections * 100
        ELSE 0 
    END;
    
    -- Return performance metrics with recommendations
    RETURN QUERY VALUES
        ('total_connections', total_connections::NUMERIC, 
         CASE 
             WHEN total_connections > 80 THEN 'Consider increasing max_db_connections'
             WHEN total_connections < 10 THEN 'Pool size may be too large'
             ELSE 'Connection count optimal'
         END),
        ('active_connections', active_connections::NUMERIC,
         CASE 
             WHEN active_connections > total_connections * 0.8 THEN 'High utilization - monitor performance'
             WHEN active_connections < total_connections * 0.2 THEN 'Low utilization - consider reducing pool size'
             ELSE 'Active connection ratio optimal'
         END),
        ('connection_utilization_pct', connection_utilization,
         CASE 
             WHEN connection_utilization > 80 THEN 'Very high utilization - add more pool connections'
             WHEN connection_utilization > 60 THEN 'Moderate utilization - monitor trends'
             WHEN connection_utilization < 20 THEN 'Low utilization - consider reducing pool size'
             ELSE 'Utilization within optimal range'
         END),
        ('idle_connections', idle_connections::NUMERIC,
         CASE 
             WHEN idle_connections > total_connections * 0.5 THEN 'Many idle connections - reduce server_idle_timeout'
             WHEN idle_connections = 0 THEN 'No idle connections - may need larger pool'
             ELSE 'Idle connection count reasonable'
         END);
END;
$$;

-- =============================================================================
-- LOAD TESTING PREPARATION FUNCTIONS
-- =============================================================================

-- Function to simulate connection load for testing
CREATE OR REPLACE FUNCTION simulate_connection_load(
    concurrent_connections INTEGER DEFAULT 50,
    duration_seconds INTEGER DEFAULT 60
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    query_count INTEGER := 0;
    i INTEGER;
BEGIN
    start_time := clock_timestamp();
    end_time := start_time + (duration_seconds || ' seconds')::INTERVAL;
    
    -- Simulate load by running queries
    WHILE clock_timestamp() < end_time LOOP
        -- Simulate various types of queries
        FOR i IN 1..10 LOOP
            PERFORM COUNT(*) FROM buildings; -- Fast query
            PERFORM COUNT(*) FROM rooms WHERE building_id = (i % 5) + 1; -- Medium query
            IF i % 3 = 0 THEN
                PERFORM * FROM building_analytics LIMIT 1; -- Materialized view query
            END IF;
            query_count := query_count + 1;
        END LOOP;
        
        -- Small pause to prevent overwhelming
        PERFORM pg_sleep(0.01);
    END LOOP;
    
    RETURN 'Load test completed: ' || query_count || ' queries in ' || duration_seconds || ' seconds';
END;
$$;

-- =============================================================================
-- CONNECTION HEALTH MONITORING
-- =============================================================================

-- Create table for connection health history
CREATE TABLE IF NOT EXISTS connection_health_log (
    id SERIAL PRIMARY KEY,
    total_connections INTEGER NOT NULL,
    active_connections INTEGER NOT NULL,
    idle_connections INTEGER NOT NULL,
    utilization_percentage NUMERIC(5,2) NOT NULL,
    avg_query_duration_ms NUMERIC(10,3),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to log connection health
CREATE OR REPLACE FUNCTION log_connection_health()
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    total_conn INTEGER;
    active_conn INTEGER;
    idle_conn INTEGER;
    utilization NUMERIC;
    avg_duration NUMERIC;
BEGIN
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN state = 'active' THEN 1 END),
        COUNT(CASE WHEN state = 'idle' THEN 1 END)
    INTO total_conn, active_conn, idle_conn
    FROM pg_stat_activity 
    WHERE datname IS NOT NULL;
    
    utilization := CASE 
        WHEN total_conn > 0 THEN active_conn::NUMERIC / total_conn * 100
        ELSE 0 
    END;
    
    -- Get average query duration (simplified calculation)
    SELECT AVG(EXTRACT(epoch FROM NOW() - query_start) * 1000)
    INTO avg_duration
    FROM pg_stat_activity 
    WHERE state = 'active' AND query_start IS NOT NULL;
    
    INSERT INTO connection_health_log (
        total_connections,
        active_connections, 
        idle_connections,
        utilization_percentage,
        avg_query_duration_ms
    ) VALUES (
        total_conn,
        active_conn,
        idle_conn,
        utilization,
        avg_duration
    );
END;
$$;

-- =============================================================================
-- PGBOUNCER INSTALLATION AND SETUP SUMMARY
-- =============================================================================

-- View to show recommended PgBouncer setup
CREATE OR REPLACE VIEW pgbouncer_setup_summary AS
SELECT 
    'Configuration Files' as setup_step,
    E'1. Create /etc/pgbouncer/pgbouncer.ini with generated config\n' ||
    E'2. Create /etc/pgbouncer/userlist.txt with user credentials\n' ||
    E'3. Start PgBouncer: sudo systemctl start pgbouncer\n' ||
    E'4. Connect via: psql -h localhost -p 6432 -d arxos_production -U arxos_api_user'
    as instructions
UNION ALL
SELECT 
    'Recommended Pool Sizes',
    'API: 20 connections, Optimization: 10 connections, Analytics: 15 connections, Read-only: 5 connections'
UNION ALL
SELECT
    'Connection Strings',
    E'API: postgresql://arxos_api_user:password@localhost:6432/arxos_api\n' ||
    E'Optimization: postgresql://arxos_optimizer_user:password@localhost:6432/arxos_optimization\n' ||
    E'Analytics: postgresql://arxos_analytics_user:password@localhost:6432/arxos_analytics\n' ||
    E'Read-only: postgresql://arxos_readonly_user:password@localhost:6432/arxos_readonly'
UNION ALL
SELECT
    'Monitoring',
    'Use get_pool_performance_metrics() and log_connection_health() functions for monitoring';

-- Test the configuration generation
SELECT 'PgBouncer Configuration Generation Test:' as status;
SELECT config_section, config_content FROM generate_pgbouncer_config();

-- Test optimal pool size calculation
SELECT 'Optimal Pool Size Recommendations:' as status;
SELECT * FROM calculate_optimal_pool_size(500, 100, 200);

-- Test current connection analysis
SELECT 'Current Connection Analysis:' as status;
SELECT * FROM analyze_connection_patterns();

-- Show setup summary
SELECT 'PgBouncer Setup Summary:' as status;
SELECT * FROM pgbouncer_setup_summary;

COMMENT ON FUNCTION generate_pgbouncer_config() IS 'Generates PgBouncer configuration for production deployment';
COMMENT ON FUNCTION calculate_optimal_pool_size(integer, integer, integer) IS 'Calculates optimal connection pool sizes based on workload characteristics';
COMMENT ON TABLE connection_health_log IS 'Connection health monitoring data - should be populated by scheduled job';