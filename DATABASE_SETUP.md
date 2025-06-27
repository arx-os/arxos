# Database Setup and Migration Guide

This document provides comprehensive instructions for setting up the Arxos database, running migrations, and seeding data across all environments.

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Environment Setup](#environment-setup)
4. [Running Migrations](#running-migrations)
5. [Seeding Data](#seeding-data)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

## Overview

The Arxos database consists of multiple schemas and tables that support:
- User management and authentication
- Building and asset inventory management
- CMMS integration and maintenance workflows
- Data vendor API access control
- Security monitoring and audit logging
- Compliance reporting and data retention
- Export activity tracking

## Database Schema

### Core Tables

#### Users and Authentication
- `users` - User accounts and authentication data
- `user_roles` - Role definitions and permissions
- `user_sessions` - Active user sessions

#### Building Management
- `buildings` - Building information and metadata
- `floors` - Floor plans and layouts
- `rooms` - Room information and specifications
- `building_assets` - Asset inventory and specifications
- `asset_history` - Asset maintenance and lifecycle history
- `asset_maintenance` - Scheduled and completed maintenance
- `asset_valuations` - Asset valuation records

#### Data Vendor API
- `data_vendor_api_keys` - API keys for external data access
- `api_key_usage` - API usage tracking and billing
- `data_vendor_requests` - Request history and analytics

#### Security and Monitoring
- `security_alerts` - Security event monitoring
- `audit_logs` - System activity logging
- `data_retention_policies` - Data retention configuration

#### Industry Benchmarks
- `industry_benchmarks` - Equipment and system performance benchmarks

### Migration Files

The database migrations are numbered sequentially and should be run in order:

1. `001_create_arx_schema.sql` - Core user and building schema
2. `002_create_asset_inventory_schema.sql` - Asset management and industry benchmarks
3. `003_create_cmms_integration_schema.sql` - CMMS integration tables
4. `004_create_maintenance_workflow_schema.sql` - Maintenance workflow management
5. `005_alter_cmms_connections_for_auth_and_sync.sql` - CMMS authentication enhancements
6. `006_enhance_audit_logs.sql` - Enhanced audit logging
7. `007_create_export_activity_tables.sql` - Export activity tracking
8. `008_create_compliance_tables.sql` - Compliance and reporting tables
9. `009_create_security_tables.sql` - Security monitoring and API usage
10. `010_add_missing_data_vendor_tables.sql` - Additional data vendor enhancements
11. `011_seed_industry_benchmarks_and_sample_data.sql` - Seed data and sample assets

## Environment Setup

### Prerequisites

1. **PostgreSQL** (version 12 or higher)
2. **psql** command-line client
3. **Database user** with appropriate permissions

### Environment Variables

Configure the following environment variables for each environment:

#### Development
```bash
export DEV_DB_HOST=localhost
export DEV_DB_PORT=5432
export DEV_DB_NAME=arxos_dev
export DEV_DB_USER=arxos_user
export DEV_DB_PASSWORD=your_secure_password
```

#### Staging
```bash
export STAGING_DB_HOST=staging-db.example.com
export STAGING_DB_PORT=5432
export STAGING_DB_NAME=arxos_staging
export STAGING_DB_USER=arxos_user
export STAGING_DB_PASSWORD=your_secure_password
```

#### Production
```bash
export PROD_DB_HOST=prod-db.example.com
export PROD_DB_PORT=5432
export PROD_DB_NAME=arxos_prod
export PROD_DB_USER=arxos_user
export PROD_DB_PASSWORD=your_secure_password
```

### Database Creation

Create the databases for each environment:

```sql
-- Development
CREATE DATABASE arxos_dev;
CREATE USER arxos_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE arxos_dev TO arxos_user;

-- Staging
CREATE DATABASE arxos_staging;
GRANT ALL PRIVILEGES ON DATABASE arxos_staging TO arxos_user;

-- Production
CREATE DATABASE arxos_prod;
GRANT ALL PRIVILEGES ON DATABASE arxos_prod TO arxos_user;
```

## Running Migrations

### Using the Migration Scripts

The project includes migration scripts for different platforms:

#### Linux/macOS (Bash)
```bash
# Make the script executable
chmod +x run_migrations.sh

# Run for all environments
./run_migrations.sh all

# Run for specific environment
./run_migrations.sh dev
./run_migrations.sh staging
./run_migrations.sh prod

# Show help
./run_migrations.sh --help
```

#### Windows (PowerShell)
```powershell
# Run for all environments
.\run_migrations.ps1 all

# Run for specific environment
.\run_migrations.ps1 dev
.\run_migrations.ps1 staging
.\run_migrations.ps1 prod

# Show help
.\run_migrations.ps1 -Help
```

#### Windows (Command Prompt)
```cmd
# Run for all environments
run_migrations.bat all

# Run for specific environment
run_migrations.bat dev
run_migrations.bat staging
run_migrations.bat prod
```

### Manual Migration Execution

If you prefer to run migrations manually:

```bash
# Set environment variables
export PGPASSWORD=your_password

# Run migrations in order
psql -h localhost -p 5432 -U arxos_user -d arxos_dev -f migrations/001_create_arx_schema.sql
psql -h localhost -p 5432 -U arxos_user -d arxos_dev -f migrations/002_create_asset_inventory_schema.sql
# ... continue for all migration files
```

### Migration Verification

After running migrations, verify the setup:

```sql
-- Check if all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check migration history
SELECT * FROM migrations ORDER BY executed_at;

-- Verify seed data
SELECT COUNT(*) FROM industry_benchmarks;
SELECT COUNT(*) FROM buildings;
SELECT COUNT(*) FROM building_assets;
```

## Seeding Data

### Industry Benchmarks

The system includes comprehensive industry benchmarks for:

- **HVAC Systems**: Efficiency ratings, performance metrics, lifecycle data
- **Electrical Systems**: Lighting, motors, transformers, UPS systems
- **Plumbing Systems**: Pumps, water heaters, backflow preventers
- **Fire Protection**: Fire pumps, sprinkler systems, alarm response times
- **Security Systems**: CCTV cameras, access control, intrusion detection
- **Cost Data**: Installation costs, replacement costs, maintenance costs
- **Energy Performance**: Building energy use intensity (EUI) benchmarks

### Sample Data

The seed data includes:

#### Buildings
- 10 sample buildings with different access levels (public, basic, premium, enterprise)
- Various building types (office, healthcare, education, retail, hospitality, industrial, data center, government)

#### Assets
- HVAC equipment (air handlers, chillers, VAV boxes)
- Electrical equipment (panels, UPS, lighting)
- Plumbing equipment (pumps, water heaters)
- Fire protection equipment (fire pumps, sprinkler systems)
- Security equipment (CCTV cameras, card readers)

#### API Keys
- Test API keys for different access levels
- Sample usage data for testing and development

### Customizing Seed Data

To customize the seed data for your environment:

1. **Modify the seed migration file** (`011_seed_industry_benchmarks_and_sample_data.sql`)
2. **Add your own buildings and assets**
3. **Update industry benchmarks** with your specific data
4. **Configure API keys** for your data vendors

Example of adding custom data:

```sql
-- Add custom building
INSERT INTO buildings (name, address, city, state, zip_code, building_type, status, access_level, owner_id) VALUES
('My Custom Building', '123 Custom St', 'My City', 'ST', '12345', 'Office', 'active', 'premium', 1);

-- Add custom industry benchmark
INSERT INTO industry_benchmarks (equipment_type, system, metric, value, unit, source, year, description) VALUES
('Custom Equipment', 'Custom System', 'custom_metric', 95.0, 'percent', 'Custom Source', 2024, 'Custom benchmark description');
```

## Troubleshooting

### Common Issues

#### Connection Errors
```
Error: could not connect to server
```

**Solution**: Verify database host, port, and credentials. Check firewall settings and network connectivity.

#### Permission Errors
```
Error: permission denied for table
```

**Solution**: Ensure the database user has appropriate permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO arxos_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO arxos_user;
```

#### Migration Already Applied
```
Error: relation already exists
```

**Solution**: This is normal if migrations have been run before. The scripts use `CREATE TABLE IF NOT EXISTS` to handle this safely.

#### psql Not Found
```
Error: psql: command not found
```

**Solution**: Install PostgreSQL client tools:
- **Ubuntu/Debian**: `sudo apt-get install postgresql-client`
- **macOS**: `brew install postgresql`
- **Windows**: Download from PostgreSQL website

### Migration Rollback

To rollback migrations (use with caution):

```sql
-- Drop all tables (WARNING: This will delete all data)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO arxos_user;
```

### Backup and Restore

#### Create Backup
```bash
pg_dump -h localhost -p 5432 -U arxos_user -d arxos_dev > backup.sql
```

#### Restore Backup
```bash
psql -h localhost -p 5432 -U arxos_user -d arxos_dev < backup.sql
```

## Security Considerations

### Database Security

1. **Use strong passwords** for database users
2. **Limit network access** to database servers
3. **Enable SSL connections** for production environments
4. **Regular security updates** for PostgreSQL
5. **Monitor database access** and audit logs

### API Key Security

1. **Rotate API keys** regularly
2. **Monitor API usage** for suspicious activity
3. **Implement rate limiting** to prevent abuse
4. **Log all API requests** for audit purposes
5. **Use HTTPS** for all API communications

### Data Privacy

1. **Anonymize sensitive data** in exports
2. **Implement data retention policies**
3. **Encrypt sensitive data** at rest and in transit
4. **Regular security audits** of data access
5. **Compliance with data protection regulations**

## Monitoring and Maintenance

### Database Monitoring

Monitor the following metrics:
- **Connection count** and performance
- **Query performance** and slow queries
- **Disk space** usage and growth
- **Backup success** and restore testing
- **Security alerts** and access patterns

### Regular Maintenance

1. **Weekly**: Check database logs and performance
2. **Monthly**: Review and update industry benchmarks
3. **Quarterly**: Security audit and access review
4. **Annually**: Full backup testing and disaster recovery drill

### Performance Optimization

1. **Index optimization** based on query patterns
2. **Query optimization** for slow operations
3. **Partitioning** for large tables
4. **Vacuum and analyze** operations
5. **Connection pooling** for high-traffic applications

## Support

For database-related issues:

1. **Check the logs** in the application and database
2. **Review this documentation** for common solutions
3. **Contact the development team** for complex issues
4. **Submit bug reports** with detailed error information

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Migration Best Practices](https://martinfowler.com/articles/evodb.html)
- [Security Hardening Guide](https://www.postgresql.org/docs/current/security.html) 