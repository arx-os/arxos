# Troubleshooting

This guide helps diagnose and resolve common issues with the Arxos CLI.

## Quick Diagnostics

### Run Built-in Diagnostics

```bash
# Comprehensive system check
arxos diagnose --full-report

# Specific diagnostics
arxos diagnose --connectivity
arxos diagnose --performance  
arxos diagnose --cache

# Generate diagnostic report
arxos diagnose --export=diagnostic-report.json
```

### Check System Status

```bash
# Overall CLI health
arxos health

# Connection status
arxos connection status

# Authentication status  
arxos auth status

# Performance metrics
arxos perf monitor --duration=30s
```

## Common Issues and Solutions

### Authentication Issues

#### "Authentication Failed" Error

**Symptoms:**
```
Error: Authentication failed. Invalid credentials or expired token.
```

**Solutions:**
```bash
# Check current auth status
arxos auth status

# Try refreshing token
arxos auth token refresh

# Re-login if refresh fails
arxos auth logout
arxos auth login --org="your-org"

# Check API endpoint configuration
arxos config get auth.endpoint
```

#### "Permission Denied" Error

**Symptoms:**
```
Error: Permission denied. Insufficient privileges for operation.
```

**Solutions:**
```bash
# Check your permissions
arxos auth permissions

# Verify you're in correct organization
arxos auth status

# Request access from building admin
arxos request-access --building=building-name --level=contributor

# Switch to different organization if needed
arxos auth org switch --org="different-org"
```

#### Token Expired Issues

**Symptoms:**
```
Error: Token has expired. Please re-authenticate.
```

**Solutions:**
```bash
# Auto-refresh token
arxos auth token refresh

# Set auto-refresh in config
arxos config set auth.auto-refresh=true

# Check token expiration
arxos auth token info

# Manual re-login
arxos auth login --org="your-org"
```

### Connection Issues

#### "Cannot Connect to Building" Error

**Symptoms:**
```
Error: Cannot connect to building://org/building-name
```

**Solutions:**
```bash
# Test connectivity
arxos connection test

# Check building availability
arxos buildings list --org="your-org"

# Verify building URI format
arxos connect building://correct-org/correct-building-name

# Check network connectivity
arxos network status

# Try with different endpoint
arxos connect building://org/building --endpoint="https://backup-api.arxos.io"
```

#### Network Timeout Issues

**Symptoms:**
```
Error: Request timeout after 30s
```

**Solutions:**
```bash
# Increase timeout
arxos config set connection.timeout=60s

# Check network latency
arxos network latency-test

# Use connection pooling
arxos config set connection.pooling=true

# Switch to faster endpoint
arxos config set connection.endpoint="https://fast-api.arxos.io"
```

#### Intermittent Connection Drops

**Symptoms:**
- Commands randomly fail with connection errors
- Sync stops working intermittently

**Solutions:**
```bash
# Enable connection retry
arxos config set connection.retry=true
arxos config set connection.max-retries=3

# Use connection keepalive
arxos config set connection.keepalive=true

# Monitor connection stability
arxos connection monitor --duration=10m

# Switch to more stable endpoint
arxos config set connection.endpoint="https://stable-api.arxos.io"
```

### Query Issues

#### "Query Too Slow" Performance

**Symptoms:**
- Queries taking >10 seconds
- High memory usage during queries

**Solutions:**
```bash
# Profile the slow query
arxos profile query "your-slow-query"

# Add spatial bounds to query
arxos find outlets in floor:45 where voltage=120  # Instead of unbounded

# Use spatial indexing
arxos find outlets --spatial-index=octree

# Enable query caching
arxos config set query-cache.enabled=true

# Optimize query pattern
arxos find outlets where voltage=120 in floor:45  # More specific first
```

#### "Query Syntax Error"

**Symptoms:**
```
Error: Syntax error in query at position 23
```

**Solutions:**
```bash
# Check query syntax documentation
arxos help query-language

# Validate query syntax
arxos query-validate "your-query"

# Use query builder for complex queries
arxos query-builder --interactive

# Check for common syntax mistakes
# Wrong: arxos find outlets where voltage = 120
# Right: arxos find outlets where voltage=120
```

#### "No Results Found" When Data Exists

**Symptoms:**
- Query returns empty results
- Know data exists in building

**Solutions:**
```bash
# Check connection scope
arxos connection status

# Verify object types
arxos find * --limit=10  # See what objects exist

# Check property names
arxos get outlet:some-id --full  # See available properties

# Check case sensitivity
arxos find outlets where voltage=120  # voltage, not Voltage

# Clear query cache
arxos cache clear --type=query
```

### Sync and Collaboration Issues

#### Sync Not Working

**Symptoms:**
- Changes not appearing for other users
- Not receiving real-time updates

**Solutions:**
```bash
# Check sync status
arxos sync status

# Test WebSocket connection
arxos network websocket-test

# Force sync
arxos sync push
arxos sync pull

# Reset sync state
arxos sync reset --confirm

# Enable sync debugging
arxos debug sync --level=verbose
```

#### Conflict Resolution Problems

**Symptoms:**
- Conflicts not resolving automatically
- Manual conflicts appearing frequently

**Solutions:**
```bash
# List active conflicts
arxos conflicts list

# Resolve conflicts manually
arxos conflict resolve <conflict-id> --choose=local

# Change conflict resolution strategy
arxos config set conflict-resolution=auto

# Enable conflict notifications
arxos notifications enable --types=conflicts

# Coordinate with team members
arxos presence show  # See who else is working
```

#### Sync Performance Issues

**Symptoms:**
- Long delays in sync updates
- High bandwidth usage

**Solutions:**
```bash
# Enable differential sync
arxos config set sync.differential=true

# Reduce sync frequency
arxos config set sync.update-interval=2s

# Compress sync data
arxos config set sync.compression=true

# Limit sync scope
arxos sync scope --area=floor:45 --systems=electrical

# Monitor sync performance
arxos sync monitor --show-bandwidth
```

### Cache Issues

#### Cache Not Working

**Symptoms:**
- Repeated queries are slow
- High API usage

**Solutions:**
```bash
# Check cache status
arxos cache status

# Enable caching
arxos config set cache.enabled=true

# Increase cache size
arxos config set cache.memory.size=2GB

# Clear corrupted cache
arxos cache clear --all --confirm

# Rebuild cache
arxos cache rebuild
```

#### Cache Taking Too Much Space

**Symptoms:**
- Disk space warnings
- Slow system performance

**Solutions:**
```bash
# Check cache size
arxos cache stats

# Reduce cache size limits
arxos config set cache.disk.size=5GB

# Clear old cache entries
arxos cache clean --older-than=7days

# Configure cache eviction
arxos config set cache.eviction=lru

# Move cache location
arxos config set cache.location="/path/to/faster/disk"
```

### Performance Issues

#### High Memory Usage

**Symptoms:**
- CLI consuming >4GB RAM
- System slowdown during operations

**Solutions:**
```bash
# Monitor memory usage
arxos memory monitor --duration=5m

# Reduce object cache size
arxos config set memory.max-objects=50000

# Enable lazy loading
arxos config set loading.relationships=lazy

# Use streaming for large queries
arxos find outlets --stream

# Profile memory leaks
arxos memory leak-check
```

#### Slow Command Execution

**Symptoms:**
- All commands are slow
- High CPU usage

**Solutions:**
```bash
# Profile command performance
arxos profile cpu --duration=60s

# Check for inefficient queries
arxos slow-queries --threshold=1s

# Optimize configuration
arxos auto-tune --analyze-period=1day

# Update CLI to latest version
arxos update --check

# Clear all caches
arxos cache clear --all
```

### Data Issues

#### Constraint Violations

**Symptoms:**
```
Error: Constraint violation: voltage-mismatch
```

**Solutions:**
```bash
# Check constraint details
arxos constraint-info voltage-mismatch

# Get suggested fixes
arxos suggest-fix outlet:R45-23 --constraint=voltage-mismatch

# Override constraint (if permitted)
arxos override-constraint outlet:R45-23 voltage-mismatch --reason="temporary"

# Validate all constraints
arxos validate-constraints --all
```

#### Data Corruption

**Symptoms:**
- Inconsistent object properties
- Missing relationships
- Constraint violations appearing randomly

**Solutions:**
```bash
# Run data integrity check
arxos integrity-check --full

# Repair data inconsistencies
arxos repair-data --fix=all

# Rebuild spatial indexes
arxos spatial rebuild-indexes

# Restore from backup if needed
arxos backup list
arxos restore backup-name --confirm

# Contact support for severe corruption
arxos support create-ticket --severity=high
```

## Advanced Troubleshooting

### Debug Mode

#### Enable Comprehensive Debugging

```bash
# Enable all debugging
arxos debug enable --all

# Enable specific debug categories
arxos debug enable --categories=query,sync,cache

# Set debug level
arxos debug level --set=verbose

# Debug specific operations
arxos debug trace "find outlets in floor:45"
```

#### Debug Output Analysis

```bash
# View debug logs
arxos logs --level=debug --tail=100

# Filter debug logs
arxos logs --category=query --since=1h

# Export debug information
arxos debug export --output=debug-info.json

# Analyze debug patterns
arxos debug analyze --timeframe=1day
```

### Performance Profiling

#### CPU Profiling

```bash
# Profile CPU usage
arxos profile cpu --duration=120s --output=cpu-profile.json

# Profile specific operations
arxos profile operation "find outlets where voltage=120"

# Generate performance report
arxos profile report --format=html --output=profile-report.html
```

#### Memory Profiling

```bash
# Profile memory allocation
arxos profile memory --track-allocations --duration=60s

# Analyze memory leaks
arxos memory leak-analysis --output=leak-report.json

# Monitor memory in real-time
arxos memory monitor --live --duration=10m
```

### Network Diagnostics

#### Connection Testing

```bash
# Test all endpoints
arxos network test-endpoints

# Measure latency to different services
arxos network latency --service=api,sync,cache

# Test WebSocket connectivity
arxos network websocket-test --duration=30s

# Monitor network traffic
arxos network monitor --show-breakdown --duration=5m
```

#### Bandwidth Analysis

```bash
# Monitor bandwidth usage
arxos network bandwidth --live

# Analyze bandwidth patterns
arxos network bandwidth-analysis --timeframe=1week

# Optimize network settings
arxos network optimize --connection-type=cellular
```

### Configuration Validation

#### Validate Configuration

```bash
# Validate all configuration
arxos config validate --comprehensive

# Check for deprecated settings
arxos config check-deprecated

# Optimize configuration
arxos config optimize --workload-type=query-heavy

# Reset to recommended defaults
arxos config reset --keep-auth
```

#### Configuration Debugging

```bash
# Show effective configuration
arxos config dump --effective

# Trace configuration sources
arxos config trace --setting=cache.size

# Validate configuration syntax
arxos config lint
```

## Getting Help

### Self-Help Resources

```bash
# Built-in help system
arxos help
arxos help <command>

# Show examples for commands
arxos examples <command>

# Check CLI version and updates
arxos version --check-updates

# View changelog
arxos changelog --since-version=1.0
```

### Support Options

```bash
# Create support ticket
arxos support create-ticket --category=technical --priority=high

# Export diagnostic information for support
arxos support export-diagnostics --include=logs,config,performance

# Check service status
arxos support service-status

# View known issues
arxos support known-issues
```

### Community Resources

```bash
# Access community documentation
arxos docs open --topic=troubleshooting

# Search community forums
arxos community search "your issue"

# Submit bug report
arxos bug-report --include-diagnostics

# Request feature
arxos feature-request --category=cli
```

## Preventive Maintenance

### Regular Health Checks

```bash
# Schedule daily health checks
arxos schedule health-check --daily --time=6am --email-report

# Set up monitoring alerts
arxos monitor alerts --metric=query-time --threshold=5s

# Configure automatic cache cleanup
arxos schedule cache-cleanup --weekly --day=sunday
```

### Configuration Backup

```bash
# Backup configuration
arxos config backup --output=config-backup.json

# Backup authentication tokens
arxos auth backup --output=auth-backup.json

# Create full CLI state backup
arxos backup create-full --output=cli-backup.tar.gz
```

### Update Management

```bash
# Check for CLI updates
arxos update check

# Enable automatic updates
arxos config set update.automatic=true

# Set update channel
arxos config set update.channel=stable

# Update CLI manually
arxos update install --version=latest
```

## Recovery Procedures

### Complete CLI Reset

```bash
# Backup current state
arxos backup create-full --output=pre-reset-backup.tar.gz

# Reset CLI to defaults
arxos reset --all --confirm

# Restore authentication
arxos auth login --org="your-org"

# Restore connection
arxos connect building://your-org/your-building

# Test basic functionality
arxos find floors --limit=5
```

### Data Recovery

```bash
# List available backups
arxos backup list --remote

# Restore from specific backup
arxos restore backup-2024-01-15 --confirm

# Selective restore
arxos restore backup-name --objects="outlets in floor:45"

# Verify restored data
arxos validate-constraints --all
```

### Emergency Procedures

```bash
# Emergency contact support
arxos emergency-contact --issue="data-corruption"

# Export critical data
arxos export "critical-systems" --format=json --output=emergency-backup.json

# Switch to backup service
arxos config set connection.endpoint="https://backup-api.arxos.io"

# Enable safe mode
arxos config set safe-mode=true
```