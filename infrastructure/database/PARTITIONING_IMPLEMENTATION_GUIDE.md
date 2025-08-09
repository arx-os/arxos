# Table Partitioning Implementation Guide

## Overview

This guide provides comprehensive documentation for implementing table partitioning in the Arxos database to improve performance and manageability of large audit/log/history tables.

## Architecture

### Partitioning Strategy

The Arxos database implements **range partitioning by date** for time-series tables:

#### Target Tables

1. **audit_logs_partitioned** - Audit trail data
   - Partition Key: `created_at`
   - Retention: 12 months
   - Strategy: Monthly partitions

2. **object_history_partitioned** - Object change history
   - Partition Key: `changed_at`
   - Retention: 12 months
   - Strategy: Monthly partitions

3. **slow_query_log_partitioned** - Performance monitoring
   - Partition Key: `timestamp`
   - Retention: 6 months
   - Strategy: Monthly partitions

4. **chat_messages_partitioned** - Communication logs
   - Partition Key: `created_at`
   - Retention: 12 months
   - Strategy: Monthly partitions

#### Partition Structure

```
audit_logs_partitioned (parent table)
├── audit_logs_p2024_01 (partition for Jan 2024)
├── audit_logs_p2024_02 (partition for Feb 2024)
├── audit_logs_p2024_03 (partition for Mar 2024)
├── ...
├── audit_logs_p2024_12 (partition for Dec 2024)
└── audit_logs_p_default (default partition for future data)
```

## Implementation Phases

### Phase 1: Analysis and Planning

#### 1.1 Run Partitioning Analysis

```bash
# Analyze tables for partitioning suitability
python tools/analyze_partitioning.py \
  --database-url postgresql://localhost/arxos_db \
  --output-format markdown \
  --output-file partitioning_analysis.md
```

#### 1.2 Review Analysis Results

The analysis tool provides:

- **Table Metrics**: Size, row count, insert rates
- **Partitioning Candidates**: Tables suitable for partitioning
- **Strategy Recommendations**: Range vs list vs hybrid
- **Performance Estimates**: Expected improvements
- **Migration Plans**: Step-by-step implementation

#### 1.3 Example Analysis Output

```markdown
# Table Partitioning Analysis Report

## Executive Summary
- Partition Candidates: 4
- High Priority Tables: 2
- Medium Priority Tables: 2

## Performance Estimates
- Query Improvement: 60-90%
- Insert Improvement: 40-70%
- Storage Savings: 20-40%

## Recommendations
- Partition audit_logs using range_by_date strategy
- Partition object_history using range_by_date strategy
- Partition slow_query_log using range_by_date strategy
- Partition chat_messages using range_by_date strategy
```

### Phase 2: Migration Implementation

#### 2.1 Apply Partitioning Migration

```bash
# Apply the partitioning migration
psql -d arxos_db -f migrations/007_add_partitioning.sql
```

#### 2.2 Verify Migration Success

```sql
-- Check partition creation
SELECT
    schemaname,
    tablename,
    partitiontablename,
    partitionname,
    partitionrangestart,
    partitionrangeend
FROM pg_partitions
WHERE tablename LIKE '%_partitioned'
ORDER BY tablename, partitionname;

-- Verify data migration
SELECT COUNT(*) FROM audit_logs_partitioned;
SELECT COUNT(*) FROM object_history_partitioned;
SELECT COUNT(*) FROM slow_query_log_partitioned;
SELECT COUNT(*) FROM chat_messages_partitioned;
```

#### 2.3 Update Application Queries

**Before Partitioning:**
```sql
SELECT * FROM audit_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

**After Partitioning:**
```sql
SELECT * FROM audit_logs_partitioned
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

### Phase 3: Performance Benchmarking

#### 3.1 Run Performance Benchmarks

```bash
# Benchmark query performance improvements
python tools/benchmark_partitioning.py \
  --database-url postgresql://localhost/arxos_db \
  --output-format markdown \
  --output-file performance_benchmark.md
```

#### 3.2 Benchmark Query Types

The benchmarking tool tests:

1. **Time Range Queries**
   - Recent audit logs (7 days)
   - Monthly audit logs
   - Recent object history (30 days)
   - Critical slow queries (7 days)

2. **Aggregation Queries**
   - Audit logs by action
   - Object history by type
   - Slow queries by severity

3. **Filtering Queries**
   - Audit logs by user
   - Object history by object
   - Slow queries by duration

#### 3.3 Example Benchmark Results

```markdown
# Partitioning Performance Benchmark Report

## Executive Summary
- Average Improvement: 75.2%
- Best Improvement: 89.1%
- Worst Improvement: 45.3%

## Query Performance Results
- recent_audit_logs: 82.3% improvement
- monthly_audit_logs: 89.1% improvement
- recent_object_history: 78.5% improvement
- slow_queries_critical: 71.2% improvement
```

### Phase 4: Maintenance Automation

#### 4.1 Set Up Automated Maintenance

```bash
# Run partition maintenance
python tools/maintain_partitions.py \
  --database-url postgresql://localhost/arxos_db \
  --output-format markdown \
  --output-file maintenance_report.md
```

#### 4.2 Maintenance Operations

The maintenance tool performs:

1. **Create New Partitions**
   - Creates partitions 3 months ahead
   - Ensures continuous data insertion

2. **Drop Old Partitions**
   - Removes partitions after retention period
   - Frees up storage space

3. **Validate Partitions**
   - Checks partition integrity
   - Verifies data consistency

#### 4.3 Example Maintenance Output

```markdown
# Partition Maintenance Report

## Executive Summary
- Total Operations: 8
- Successful Operations: 8
- Partitions Created: 4
- Partitions Dropped: 2

## Maintenance Results
- ✅ create_partition: audit_logs_p2025_01
- ✅ create_partition: object_history_p2025_01
- ✅ create_partition: slow_query_log_p2025_01
- ✅ create_partition: chat_messages_p2025_01
- ✅ drop_partition: audit_logs_p2023_01 (12 months old)
- ✅ drop_partition: object_history_p2023_01 (12 months old)
```

## Tools Reference

### 1. Partitioning Analysis Tool

**File**: `tools/analyze_partitioning.py`

**Purpose**: Identifies tables suitable for partitioning

**Features**:
- Analyzes table size and activity metrics
- Recommends partitioning strategies
- Estimates performance improvements
- Generates migration plans

**Usage**:
```bash
python tools/analyze_partitioning.py [--database-url postgresql://...]
```

**Output Formats**:
- JSON: Machine-readable analysis results
- Markdown: Human-readable reports

### 2. Performance Benchmarking Tool

**File**: `tools/benchmark_partitioning.py`

**Purpose**: Measures query performance improvements

**Features**:
- Tests before/after query performance
- Analyzes execution plans
- Measures cache hit ratios
- Generates performance reports

**Usage**:
```bash
python tools/benchmark_partitioning.py [--database-url postgresql://...]
```

**Benchmark Categories**:
- Time range queries
- Aggregation queries
- Filtering queries

### 3. Partition Maintenance Tool

**File**: `tools/maintain_partitions.py`

**Purpose**: Automates partition lifecycle management

**Features**:
- Creates new partitions ahead of time
- Drops old partitions based on retention
- Validates partition integrity
- Logs maintenance operations

**Usage**:
```bash
python tools/maintain_partitions.py [--database-url postgresql://...]
```

**Maintenance Operations**:
- Create partitions 3 months ahead
- Drop partitions after retention period
- Validate partition data integrity

## Configuration

### Partitioned Tables Configuration

```python
partitioned_tables = {
    'audit_logs_partitioned': {
        'partition_key': 'created_at',
        'retention_months': 12,
        'create_ahead_months': 3
    },
    'object_history_partitioned': {
        'partition_key': 'changed_at',
        'retention_months': 12,
        'create_ahead_months': 3
    },
    'slow_query_log_partitioned': {
        'partition_key': 'timestamp',
        'retention_months': 6,
        'create_ahead_months': 3
    },
    'chat_messages_partitioned': {
        'partition_key': 'created_at',
        'retention_months': 12,
        'create_ahead_months': 3
    }
}
```

### Retention Policies

| Table | Retention Period | Reason |
|-------|-----------------|---------|
| audit_logs | 12 months | Compliance and audit requirements |
| object_history | 12 months | Change tracking and rollback |
| slow_query_log | 6 months | Performance analysis and optimization |
| chat_messages | 12 months | Communication history |

## Best Practices

### 1. Query Optimization

#### Use Partition Pruning

**Good**:
```sql
-- Query uses partition pruning
SELECT * FROM audit_logs_partitioned
WHERE created_at >= '2024-01-01'
AND created_at < '2024-02-01';
```

**Avoid**:
```sql
-- Query cannot use partition pruning
SELECT * FROM audit_logs_partitioned
WHERE created_at::text LIKE '2024%';
```

#### Leverage Partition Keys

**Good**:
```sql
-- Uses partition key in WHERE clause
SELECT * FROM object_history_partitioned
WHERE changed_at >= NOW() - INTERVAL '30 days'
ORDER BY changed_at DESC;
```

**Avoid**:
```sql
-- Doesn't use partition key effectively
SELECT * FROM object_history_partitioned
WHERE object_id = 'room_123'
ORDER BY changed_at DESC;
```

### 2. Index Strategy

#### Parent Table Indexes

Create indexes on the parent table, not individual partitions:

```sql
-- Good: Index on parent table
CREATE INDEX idx_audit_logs_partitioned_user_id
ON audit_logs_partitioned (user_id);

-- Avoid: Index on individual partition
CREATE INDEX idx_audit_logs_p2024_01_user_id
ON audit_logs_p2024_01 (user_id);
```

#### Composite Indexes

Use composite indexes for common query patterns:

```sql
-- Composite index for user activity queries
CREATE INDEX idx_audit_logs_partitioned_user_created
ON audit_logs_partitioned (user_id, created_at);

-- Composite index for object history queries
CREATE INDEX idx_object_history_partitioned_object_changed
ON object_history_partitioned (object_id, changed_at);
```

### 3. Maintenance Schedule

#### Automated Maintenance

Set up cron jobs for regular maintenance:

```bash
# Daily partition validation
0 2 * * * python /path/to/maintain_partitions.py --validate-only

# Weekly full maintenance
0 3 * * 0 python /path/to/maintain_partitions.py

# Monthly performance benchmarking
0 4 1 * * python /path/to/benchmark_partitioning.py
```

#### Manual Maintenance

For special cases, run maintenance manually:

```bash
# Create partitions for specific date range
python tools/maintain_partitions.py --create-partitions 2024-01 2024-12

# Drop old partitions immediately
python tools/maintain_partitions.py --drop-old-partitions

# Validate all partitions
python tools/maintain_partitions.py --validate-only
```

## Troubleshooting

### Common Issues

#### 1. Missing Partitions

**Symptoms**: INSERT fails with "no partition" error

**Solution**:
```bash
# Create missing partition
python tools/maintain_partitions.py --create-missing-partitions

# Check partition coverage
SELECT * FROM pg_partitions WHERE tablename = 'audit_logs_partitioned';
```

#### 2. Poor Query Performance

**Symptoms**: Queries still slow after partitioning

**Solutions**:
```sql
-- Check if query uses partition pruning
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM audit_logs_partitioned
WHERE created_at >= NOW() - INTERVAL '7 days';

-- Verify indexes exist
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'audit_logs_partitioned';
```

#### 3. Partition Imbalance

**Symptoms**: Some partitions much larger than others

**Solutions**:
```sql
-- Check partition sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename LIKE 'audit_logs_p%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Consider sub-partitioning if needed
ALTER TABLE audit_logs_partitioned
PARTITION BY RANGE (created_at, user_id);
```

### Performance Monitoring

#### Query Performance Tracking

```sql
-- Monitor partition usage
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE tablename LIKE '%_partitioned'
ORDER BY n_tup_ins DESC;
```

#### Partition Health Checks

```sql
-- Check partition data distribution
SELECT
    partition_name,
    start_date,
    end_date,
    row_count,
    size_mb
FROM v_partition_sizes
ORDER BY size_mb DESC;
```

## Migration Safety

### Rollback Procedures

#### 1. Emergency Rollback

```sql
-- Use the rollback function
SELECT rollback_partitioning_migration();
```

#### 2. Manual Rollback

```sql
-- Drop partitioned tables
DROP TABLE IF EXISTS audit_logs_partitioned CASCADE;
DROP TABLE IF EXISTS object_history_partitioned CASCADE;
DROP TABLE IF EXISTS slow_query_log_partitioned CASCADE;
DROP TABLE IF EXISTS chat_messages_partitioned CASCADE;

-- Recreate original tables
CREATE TABLE audit_logs AS SELECT * FROM audit_logs_backup;
CREATE TABLE object_history AS SELECT * FROM object_history_backup;
CREATE TABLE slow_query_log AS SELECT * FROM slow_query_log_backup;
CREATE TABLE chat_messages AS SELECT * FROM chat_messages_backup;
```

### Backup Strategy

#### Before Migration

```bash
# Create backups of original tables
pg_dump -t audit_logs -t object_history -t slow_query_log -t chat_messages \
  arxos_db > pre_partitioning_backup.sql
```

#### After Migration

```bash
# Verify data integrity
python tools/validate_partitioning.py --check-data-integrity
```

## Conclusion

Table partitioning provides significant performance improvements for large time-series tables in the Arxos database. The implementation includes:

1. **Comprehensive Analysis**: Tools to identify partitioning candidates
2. **Safe Migration**: Rollback capabilities and data preservation
3. **Performance Monitoring**: Benchmarking and validation tools
4. **Automated Maintenance**: Partition lifecycle management
5. **Best Practices**: Query optimization and index strategies

The partitioning system is designed to be transparent to applications while providing substantial performance benefits for time-based queries and data management operations.
