-- Fix partitioning indexes - create indexes without CONCURRENTLY for partitioned tables

-- =============================================================================
-- AUDIT LOGS INDEXES (without transaction, without CONCURRENTLY)
-- =============================================================================

-- Indexes on partitioned audit_logs
CREATE INDEX IF NOT EXISTS audit_logs_user_time_idx ON audit_logs (user_id, created_at);
CREATE INDEX IF NOT EXISTS audit_logs_object_type_idx ON audit_logs (object_type, created_at);
CREATE INDEX IF NOT EXISTS audit_logs_action_idx ON audit_logs (action, created_at);
CREATE INDEX IF NOT EXISTS audit_logs_payload_gin_idx ON audit_logs USING GIN (payload);

-- =============================================================================
-- OBJECT HISTORY INDEXES
-- =============================================================================

-- Indexes for object_history partitions
CREATE INDEX IF NOT EXISTS object_history_object_idx ON object_history (object_type, object_id, created_at);
CREATE INDEX IF NOT EXISTS object_history_user_idx ON object_history (user_id, created_at);
CREATE INDEX IF NOT EXISTS object_history_change_gin_idx ON object_history USING GIN (change_data);

-- =============================================================================
-- DEVICES INDEXES
-- =============================================================================

-- Indexes for devices partitions
CREATE INDEX IF NOT EXISTS devices_type_status_idx ON devices (type, status);
CREATE INDEX IF NOT EXISTS devices_room_idx ON devices (room_id);
CREATE INDEX IF NOT EXISTS devices_system_idx ON devices (system, subtype);
CREATE INDEX IF NOT EXISTS devices_spatial_idx ON devices USING GIST (geom);
CREATE INDEX IF NOT EXISTS devices_project_idx ON devices (project_id);

-- =============================================================================
-- COMMENTS INDEXES
-- =============================================================================

-- Indexes for comments partitions
CREATE INDEX IF NOT EXISTS comments_object_time_idx ON comments (object_id, created_at);
CREATE INDEX IF NOT EXISTS comments_user_time_idx ON comments (user_id, created_at);
CREATE INDEX IF NOT EXISTS comments_parent_idx ON comments (parent_id);

-- =============================================================================
-- OPTIMIZATION RESULTS INDEXES
-- =============================================================================

-- Indexes for optimization results (regular indexes work on partitioned tables)
CREATE INDEX IF NOT EXISTS optimization_results_building_time_idx ON optimization_results (building_id, created_at);
CREATE INDEX IF NOT EXISTS optimization_results_algorithm_idx ON optimization_results (algorithm_type, created_at);
CREATE INDEX IF NOT EXISTS optimization_results_score_idx ON optimization_results (optimization_score DESC, created_at);
CREATE INDEX IF NOT EXISTS optimization_results_pareto_idx ON optimization_results (pareto_rank, crowding_distance DESC) WHERE pareto_rank IS NOT NULL;
CREATE INDEX IF NOT EXISTS optimization_results_parameters_gin_idx ON optimization_results USING GIN (parameters);

-- =============================================================================
-- TEST PARTITIONING FUNCTIONALITY
-- =============================================================================

-- Insert sample optimization results to test partitioning
INSERT INTO optimization_results (
    building_id, 
    algorithm_type, 
    optimization_score, 
    convergence_rate, 
    execution_time_ms, 
    parameters, 
    objectives,
    constraints_satisfied,
    constraints_violated,
    created_at
) VALUES 
(9, 'genetic', 87.5, 0.92, 245.7, 
 '{"population_size": 100, "mutation_rate": 0.05, "crossover_rate": 0.8}',
 '{"space_utilization": 85.2, "energy_efficiency": 92.1}',
 15, 2, '2024-12-01 10:00:00'),
(9, 'nsga-ii', 91.3, 0.94, 312.1,
 '{"population_size": 50, "generations": 200}',
 '{"space_utilization": 88.1, "energy_efficiency": 94.5, "cost": -420}',
 18, 1, '2024-12-02 14:30:00'),
(10, 'constraint_solver', 78.9, 0.89, 156.3,
 '{"solver": "CPLEX", "time_limit": 300}',
 '{"feasibility": true, "optimality_gap": 0.02}',
 12, 3, '2024-12-03 09:15:00');

-- Test the partition functionality
SELECT 'Partition test results:' as status;
SELECT 
    schemaname, 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE 'optimization_results_%'
ORDER BY tablename;

-- Show partition performance summary
SELECT * FROM partition_performance_summary;

-- Test partition maintenance function
SELECT daily_partition_maintenance();

-- Verify partition exclusion is working
EXPLAIN (COSTS OFF, BUFFERS OFF) 
SELECT COUNT(*) FROM optimization_results 
WHERE created_at >= '2024-12-02' AND created_at < '2024-12-03';

-- Show optimizer statistics after partitioning
SELECT 
    funcname as function_name,
    calls,
    ROUND((total_time / NULLIF(calls, 0))::numeric, 3) as avg_time_ms
FROM pg_stat_user_functions 
WHERE funcname LIKE '%partition%' OR funcname LIKE '%optimization%'
ORDER BY calls DESC;