# ADR-001: Use PostGIS as Single Database

## Status
Accepted

## Date
2024-11-15

## Context
ArxOS initially used a hybrid SQLite/PostGIS approach for data storage. This architecture split responsibilities between:
- SQLite: Core application data, metadata, and configuration
- PostGIS: Spatial data and geographic queries

This hybrid approach caused several critical issues:
- **Data Consistency**: Transactions couldn't span both databases, leading to partial updates
- **Complex Synchronization**: Required custom logic to keep data in sync between databases
- **Performance Degradation**: JOIN operations across databases were impossible, requiring application-level joins
- **Deployment Complexity**: Two different database systems to manage, backup, and monitor
- **Development Overhead**: Duplicate repository interfaces and complex transaction management

## Decision
We will use PostgreSQL with PostGIS extension as the sole database for ArxOS, eliminating SQLite entirely.

## Consequences

### Positive
- **Unified Data Model**: All data in one place with ACID guarantees
- **Better Performance**: Native JOINs between spatial and non-spatial data
- **Simplified Architecture**: Single connection pool, single backup strategy
- **Enhanced Capabilities**: Access to PostgreSQL's advanced features (JSONB, arrays, full-text search)
- **Easier Clustering**: PostgreSQL's mature replication and clustering options
- **Better Monitoring**: Single set of metrics and logs to monitor

### Negative
- **Increased Requirements**: Requires PostgreSQL installation (vs embedded SQLite)
- **Higher Resource Usage**: PostgreSQL uses more memory and disk than SQLite
- **No Offline Mode**: Cannot run without database server (SQLite allowed embedded operation)
- **Migration Complexity**: Existing installations need data migration

### Mitigation Strategies
1. **Easy Setup**: Provide Docker Compose for one-command setup
2. **Cloud Options**: Support managed PostgreSQL services (RDS, Cloud SQL)
3. **Resource Optimization**: Document PostgreSQL tuning for different deployment sizes
4. **Migration Tools**: Automated migration scripts for existing deployments
5. **Development Mode**: Include PostgreSQL in development container

## Implementation
1. Migrate all SQLite schemas to PostgreSQL
2. Update repository interfaces to use PostgreSQL
3. Remove SQLite dependencies from go.mod
4. Update configuration to use single database connection
5. Create migration scripts for existing deployments
6. Update documentation and deployment guides

## References
- [Issue #47: Database Architecture Refactor](https://github.com/arxos/arxos/issues/47)
- [PostgreSQL vs SQLite Performance Comparison](https://www.postgresql.org/about/featurematrix/)
- [PostGIS Documentation](https://postgis.net/documentation/)