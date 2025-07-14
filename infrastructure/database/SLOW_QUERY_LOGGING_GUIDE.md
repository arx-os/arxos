# Slow Query Logging Guide for Arxos Database Performance

## Overview

The Arxos Slow Query Logging System provides comprehensive performance monitoring and analysis for PostgreSQL databases. This system enables data-driven performance optimization by identifying bottlenecks and tracking query performance trends over time.

## Architecture

### Components

1. **PostgreSQL Configuration** (`postgresql.conf`)
   - Enables slow query logging with structured output
   - Configures logging thresholds and rotation
   - Integrates with Arxos logging standards

2. **Slow Query Parser** (`tools/parse_slow_queries.py`)
   - Parses PostgreSQL slow query logs
   - Analyzes query patterns and performance
   - Generates JSON and CSV reports
   - Follows Arxos structured logging standards

3. **Database Storage** (`migrations/003_create_slow_query_log.sql`)
   - Stores parsed metrics for trend analysis
   - Provides optimized views for common queries
   - Includes maintenance functions for cleanup

4. **Weekly Review Automation** (`tools/weekly_slow_query_review.py`)
   - Automated weekly performance analysis
   - Email notifications for critical issues
   - Integration with Arxos infrastructure

5. **CI/CD Integration** (`.github/workflows/weekly_slow_query_review.yml`)
   - Automated weekly execution
   - Comprehensive testing and validation
   - Artifact generation and reporting

## Quick Start

### 1. Enable Slow Query Logging

#### PostgreSQL Configuration

Copy the provided `postgresql.conf` to your PostgreSQL data directory:

```bash
# Copy configuration
sudo cp postgresql.conf /etc/postgresql/15/main/postgresql.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Verify Configuration

```sql
-- Check if slow query logging is enabled
SHOW log_min_duration_statement;
SHOW logging_collector;
SHOW log_directory;
```

### 2. Install Dependencies

```bash
cd infrastructure/database
pip install -r requirements.txt
```

### 3. Run Database Migration

```bash
# Apply the slow query log table migration
psql -d your_database -f migrations/003_create_slow_query_log.sql
```

### 4. Test the Parser

```bash
# Parse existing log files
python tools/parse_slow_queries.py pg_log --output-format json

# Generate CSV report
python tools/parse_slow_queries.py pg_log --output-format csv --output-file report.csv
```

### 5. Run Weekly Review

```bash
# Run automated weekly review
python tools/weekly_slow_query_review.py --verbose
```

## Configuration

### PostgreSQL Configuration

The `postgresql.conf` file includes the following key settings:

```ini
# Slow query logging (queries > 500ms)
log_min_duration_statement = 500

# Structured log format
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Log rotation
log_rotation_age = 1d
log_rotation_size = 100MB

# Performance monitoring
track_activities = on
track_counts = on
track_io_timing = on
```

### Weekly Review Configuration

Create a `config.yaml` file for the weekly review:

```yaml
log_directory: pg_log
output_directory: reports
database:
  host: localhost
  port: 5432
  database: arxos_db
  user: arxos_app
  password: ${DB_PASSWORD}
email:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  username: ${EMAIL_USERNAME}
  password: ${EMAIL_PASSWORD}
  from_address: performance@arxos.com
  to_addresses: [engineering@arxos.com]
thresholds:
  critical_duration_ms: 5000
  warning_duration_ms: 1000
  critical_frequency_per_hour: 10
  warning_frequency_per_hour: 5
retention:
  log_files_days: 30
  reports_days: 90
```

## Usage Examples

### Basic Log Parsing

```bash
# Parse logs and generate JSON report
python tools/parse_slow_queries.py pg_log --output-format json

# Parse logs and generate CSV report
python tools/parse_slow_queries.py pg_log --output-format csv --output-file report.csv

# Parse specific log files
python tools/parse_slow_queries.py pg_log --file-pattern "postgresql-slow-2024-*.log"
```

### Weekly Review

```bash
# Run with default configuration
python tools/weekly_slow_query_review.py

# Run with custom configuration
python tools/weekly_slow_query_review.py --config config.yaml

# Enable verbose logging
python tools/weekly_slow_query_review.py --verbose
```

### Database Queries

```sql
-- View critical slow queries
SELECT * FROM v_critical_slow_queries;

-- View performance trends
SELECT * FROM v_query_performance_trends;

-- View user performance analysis
SELECT * FROM v_user_performance_analysis;

-- Get slow query statistics
SELECT * FROM get_slow_query_stats(7);

-- Clean up old logs
SELECT cleanup_old_slow_query_logs();
```

## Performance Tuning Checklist

### 1. Identify Critical Issues

```bash
# Run parser to identify critical queries
python tools/parse_slow_queries.py pg_log --output-format json | jq '.queries[] | select(.severity == "critical")'
```

### 2. Analyze Query Patterns

```sql
-- Find most frequent slow queries
SELECT query_hash, COUNT(*) as frequency, AVG(duration_ms) as avg_duration
FROM slow_query_log 
WHERE severity = 'critical'
GROUP BY query_hash
ORDER BY frequency DESC;
```

### 3. Check for Missing Indexes

```sql
-- Queries that might benefit from indexes
SELECT DISTINCT statement 
FROM slow_query_log 
WHERE duration_ms > 1000 
AND statement LIKE '%WHERE%'
AND statement NOT LIKE '%INDEX%';
```

### 4. Monitor Trends

```sql
-- Weekly performance trends
SELECT 
    DATE_TRUNC('week', timestamp) as week,
    COUNT(*) as total_queries,
    AVG(duration_ms) as avg_duration,
    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_count
FROM slow_query_log 
GROUP BY DATE_TRUNC('week', timestamp)
ORDER BY week DESC;
```

## Integration with Arxos Standards

### Logging Standards

The slow query logging system follows Arxos's established logging standards:

- **Structured Logging**: Uses `structlog` for consistent log formatting
- **Performance Monitoring**: Tracks processing times and metrics
- **Error Handling**: Comprehensive error handling with detailed logging
- **Context Tracking**: Includes correlation IDs and request context

### Code Standards

- **Type Hints**: All functions include comprehensive type annotations
- **Documentation**: Detailed docstrings and inline comments
- **Error Handling**: Graceful error handling with meaningful messages
- **Testing**: Comprehensive test coverage for all components

### Database Standards

- **Migration Management**: Uses Alembic for schema evolution
- **Index Strategy**: Comprehensive indexing for performance
- **Audit Logging**: Integrates with existing audit system
- **Data Retention**: Configurable retention policies

## Monitoring and Alerting

### Automated Alerts

The system provides automated alerts for:

- **Critical Queries**: Queries taking > 5 seconds
- **Frequent Slow Queries**: Queries executed > 10 times per hour
- **Performance Degradation**: Increasing average query times
- **Missing Indexes**: Queries that could benefit from indexes

### Dashboard Integration

The system generates data for dashboard integration:

```sql
-- Dashboard metrics
SELECT 
    COUNT(*) as total_queries,
    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_queries,
    AVG(duration_ms) as avg_duration,
    MAX(duration_ms) as max_duration
FROM slow_query_log 
WHERE timestamp > NOW() - INTERVAL '24 hours';
```

## Troubleshooting

### Common Issues

#### 1. No Log Files Generated

**Symptoms**: No slow query log files in `pg_log` directory

**Solutions**:
```bash
# Check PostgreSQL configuration
psql -c "SHOW log_min_duration_statement;"
psql -c "SHOW logging_collector;"

# Verify log directory permissions
ls -la /var/lib/postgresql/data/pg_log/

# Check PostgreSQL logs
sudo journalctl -u postgresql
```

#### 2. Parser Not Finding Queries

**Symptoms**: Parser runs but finds no queries

**Solutions**:
```bash
# Check log file format
head -5 pg_log/postgresql-slow-*.log

# Verify regex patterns match log format
python tools/parse_slow_queries.py pg_log --verbose
```

#### 3. Database Connection Issues

**Symptoms**: Weekly review fails to connect to database

**Solutions**:
```bash
# Check database connection
psql -h localhost -U arxos_app -d arxos_db -c "SELECT 1;"

# Verify environment variables
echo $DB_PASSWORD

# Test with explicit connection
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', database='arxos_db', user='arxos_app', password='your_password')
print('Connection successful')
"
```

### Performance Issues

#### High Memory Usage

**Symptoms**: Parser uses excessive memory

**Solutions**:
```bash
# Process logs in smaller batches
python tools/parse_slow_queries.py pg_log --batch-size 1000

# Use streaming processing for large files
python tools/parse_slow_queries.py pg_log --stream-process
```

#### Slow Database Queries

**Symptoms**: Database queries in weekly review are slow

**Solutions**:
```sql
-- Add indexes for slow query log table
CREATE INDEX CONCURRENTLY idx_slow_query_log_timestamp_severity 
ON slow_query_log (timestamp, severity);

-- Analyze table statistics
ANALYZE slow_query_log;
```

## Best Practices

### 1. Configuration Management

- Use environment variables for sensitive configuration
- Version control configuration files
- Document all configuration changes

### 2. Monitoring Strategy

- Set appropriate thresholds for your workload
- Monitor trends over time, not just absolute values
- Use multiple metrics for comprehensive analysis

### 3. Performance Optimization

- Review critical queries weekly
- Add indexes based on query patterns
- Consider query optimization before adding hardware

### 4. Data Management

- Implement proper retention policies
- Archive old logs for compliance
- Monitor disk usage for log files

### 5. Security

- Secure log file access
- Encrypt sensitive configuration
- Audit access to performance data

## Advanced Features

### Custom Query Analysis

```python
from parse_slow_queries import SlowQueryParser

# Create custom analysis
parser = SlowQueryParser('pg_log')
parser.parse_log_files()

# Custom filtering
critical_queries = [q for q in parser.queries if q.duration_ms > 5000]
user_queries = [q for q in parser.queries if q.user == 'specific_user']
```

### Integration with Monitoring Systems

```python
# Send metrics to monitoring system
import requests

def send_metrics(metrics):
    requests.post('https://monitoring.arxos.com/metrics', json=metrics)
```

### Custom Alerting

```python
# Custom alert conditions
def check_custom_alerts(analysis_results):
    for result in analysis_results:
        if result.avg_duration_ms > 10000:
            send_critical_alert(result)
        elif result.frequency_per_hour > 50:
            send_warning_alert(result)
```

## Conclusion

The Arxos Slow Query Logging System provides a comprehensive solution for database performance monitoring and optimization. By following the established patterns and integrating with existing infrastructure, it enables data-driven performance improvements while maintaining consistency with Arxos standards.

For additional support or questions, refer to the Arxos engineering documentation or contact the database team. 