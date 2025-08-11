# Transaction System

The Arxos transaction system ensures that complex building modifications maintain integrity across all ArxObjects, relationships, and constraints. Transactions provide ACID guarantees for building data operations.

## Transaction Concepts

### Why Transactions Matter

Building modifications often affect multiple objects and systems:
- Moving a beam requires updating structural loads on connected elements
- Changing electrical circuits affects multiple outlets and load calculations
- Modifying walls impacts adjacent spaces and mounted objects

### ACID Properties

**Atomicity**: All operations succeed or all fail
**Consistency**: Building constraints are maintained
**Isolation**: Concurrent transactions don't interfere
**Durability**: Committed changes are permanent

## Basic Transaction Operations

### Starting Transactions

```bash
# Begin transaction
arxos transaction begin

# Begin with description
arxos transaction begin --description="Relocate electrical panel MP-1"

# Begin with timeout
arxos transaction begin --timeout=30m

# Begin read-only transaction
arxos transaction begin --read-only
```

### Committing and Rolling Back

```bash
# Commit current transaction
arxos transaction commit

# Commit with message
arxos transaction commit --message="Successfully relocated panel MP-1"

# Rollback current transaction
arxos transaction rollback

# Rollback with reason
arxos transaction rollback --reason="Constraint violations detected"
```

### Transaction Status

```bash
# Check current transaction
arxos transaction status

# List active transactions
arxos transaction list

# Show transaction details
arxos transaction info <transaction-id>
```

## Transaction Examples

### Simple Transaction

```bash
# Begin transaction
arxos transaction begin --description="Update outlet voltage"

# Make changes
arxos set outlet:R45-23.voltage=240
arxos set outlet:R45-23.amperage=30
arxos set outlet:R45-23.gfci=true

# Validate constraints
arxos validate-constraints outlet:R45-23

# Commit if valid
arxos transaction commit
```

### Complex Multi-Object Transaction

```bash
# Begin transaction
arxos transaction begin --description="Relocate beam B-101"

# Move beam to new position
arxos move beam:B-101 to coordinates:(150,200,300)

# Update structural loads
arxos recalculate structural-loads affected-by beam:B-101

# Update connected objects
arxos update connections-to beam:B-101

# Validate structural integrity
arxos validate-structure floor:45

# Check for conflicts
arxos check-conflicts beam:B-101

# Commit if all validations pass
arxos transaction commit
```

### Conditional Transaction

```bash
# Begin transaction with conditions
arxos transaction begin --if="beam:B-101.current-load < design-load"

# Make conditional changes
arxos modify beam:B-101 load-capacity=8000lbs \
  --only-if="current-load < 6000lbs"

# Auto-commit if conditions met
arxos transaction commit --if-conditions-met
```

## Advanced Transaction Features

### Nested Transactions

```bash
# Begin main transaction
arxos transaction begin --name="electrical-renovation"

  # Begin nested transaction
  arxos transaction begin --name="panel-relocation" --nested

    # Relocate panel operations
    arxos move panel:MP-1 to room:R-150
    arxos reroute circuits connected-to panel:MP-1
    
  # Commit or rollback nested transaction
  arxos transaction commit --nested

  # Continue with main transaction
  arxos update circuit-labels for panel:MP-1

# Commit main transaction
arxos transaction commit
```

### Transaction Savepoints

```bash
# Begin transaction
arxos transaction begin

# Create savepoint
arxos savepoint create "before-structural-changes"

# Make some changes
arxos modify beam:B-101 load-capacity=7000lbs

# Create another savepoint
arxos savepoint create "after-beam-modification"

# Make more changes that might fail
arxos modify column:COL-23 height=12ft

# Rollback to savepoint if needed
arxos savepoint rollback "before-structural-changes"

# Or commit the transaction
arxos transaction commit
```

### Batch Transactions

```bash
# Begin batch transaction
arxos batch-transaction begin --description="Update all outlets in floor 45"

# Batch operations are automatically transactional
arxos batch-set "outlets in floor:45" gfci=true amperage=20

# Validate all changes
arxos batch-validate "outlets in floor:45"

# Commit batch transaction
arxos batch-transaction commit
```

## Transaction Validation

### Pre-Commit Validation

```bash
# Validate transaction before commit
arxos transaction validate

# Validate specific aspects
arxos transaction validate --constraints
arxos transaction validate --relationships
arxos transaction validate --spatial-conflicts

# Show what would be affected by commit
arxos transaction impact-analysis
```

### Constraint Checking

```bash
# Check constraints during transaction
arxos check-constraints --transaction-scope

# Validate against building codes
arxos code-compliance-check --transaction-scope

# Check for cascading effects
arxos cascade-impact-check
```

### Dry Run Mode

```bash
# Run transaction in dry-run mode
arxos transaction begin --dry-run

# Make changes (simulated)
arxos modify beam:B-101 load-capacity=8000lbs
arxos recalculate structural-loads affected-by beam:B-101

# See what would happen without actual changes
arxos transaction preview-commit

# End dry run
arxos transaction end-dry-run
```

## Concurrent Transaction Management

### Transaction Isolation Levels

```bash
# Read uncommitted (lowest isolation)
arxos transaction begin --isolation=read-uncommitted

# Read committed (default)
arxos transaction begin --isolation=read-committed

# Repeatable read
arxos transaction begin --isolation=repeatable-read

# Serializable (highest isolation)
arxos transaction begin --isolation=serializable
```

### Lock Management

```bash
# Acquire explicit locks
arxos lock object outlet:R45-23 --mode=exclusive
arxos lock system electrical.floor:45 --mode=shared

# View current locks
arxos locks list

# Check for lock conflicts
arxos locks check-conflicts

# Release locks
arxos unlock outlet:R45-23
```

### Deadlock Handling

```bash
# Set deadlock timeout
arxos transaction begin --deadlock-timeout=30s

# Enable deadlock detection
arxos config set deadlock-detection=enabled

# View deadlock history
arxos deadlocks list --recent
```

## Transaction Recovery

### Failed Transaction Recovery

```bash
# View failed transactions
arxos transaction failures list

# Get failure details
arxos transaction failure-details <transaction-id>

# Retry failed transaction
arxos transaction retry <transaction-id>

# Fix issues and retry
arxos transaction retry <transaction-id> --fix-constraints
```

### Partial Commit Recovery

```bash
# Handle partial commits
arxos transaction recover --partial-commit-id=<id>

# View uncommitted changes
arxos transaction uncommitted-changes

# Apply compensation actions
arxos transaction compensate <transaction-id>
```

### Transaction Log Analysis

```bash
# View transaction log
arxos transaction log

# Analyze transaction patterns
arxos transaction analyze --timeframe="last-week"

# Export transaction history
arxos transaction export --format=json --since="2024-01-01"
```

## Performance Optimization

### Transaction Batching

```bash
# Batch multiple small transactions
arxos transaction batch begin

# Add operations to batch
arxos transaction batch add "set outlet:R45-23.voltage=240"
arxos transaction batch add "set outlet:R45-24.voltage=240"

# Execute batch
arxos transaction batch execute

# Commit batch
arxos transaction batch commit
```

### Transaction Caching

```bash
# Enable transaction-level caching
arxos transaction begin --cache=enabled

# Pre-load objects for transaction
arxos transaction preload objects "outlets in floor:45"

# Use cached constraint validation
arxos transaction validate --use-cache
```

### Parallel Transaction Processing

```bash
# Begin parallel transaction
arxos transaction begin --parallel

# Define independent operation groups
arxos transaction group create "electrical-updates"
arxos transaction group create "mechanical-updates"

# Execute groups in parallel
arxos transaction execute-parallel
```

## Transaction Monitoring

### Real-Time Monitoring

```bash
# Monitor active transactions
arxos transaction monitor --live

# Monitor specific transaction
arxos transaction monitor <transaction-id>

# Set up transaction alerts
arxos transaction alert --on=long-running --threshold=5m
```

### Transaction Metrics

```bash
# View transaction statistics
arxos transaction stats

# Performance metrics
arxos transaction performance --timeframe="last-day"

# Success/failure rates
arxos transaction success-rate --by-operation-type
```

### Transaction Auditing

```bash
# Audit transaction history
arxos transaction audit --user=alice --timeframe="last-week"

# Track object changes by transaction
arxos transaction trace-changes outlet:R45-23

# Export audit report
arxos transaction audit-report --format=pdf
```

## Best Practices

### Transaction Design

1. **Keep transactions small** - Minimize scope and duration
2. **Group related operations** - Logical units of work
3. **Validate early** - Check constraints before major operations
4. **Use savepoints** - For complex multi-step transactions
5. **Handle failures gracefully** - Implement proper error handling

### Performance Tips

1. **Pre-load related objects** - Reduce lock contention
2. **Use appropriate isolation levels** - Balance consistency and performance
3. **Batch similar operations** - Reduce transaction overhead
4. **Monitor lock usage** - Avoid deadlocks
5. **Use read-only transactions** - For query-heavy operations

### Error Handling

```bash
# Set up automatic rollback on constraint violations
arxos transaction begin --auto-rollback-on=constraint-violation

# Define retry policies
arxos transaction begin --retry-policy=exponential-backoff --max-retries=3

# Set up notification on failures
arxos transaction begin --notify-on-failure=admin@company.com
```

## Transaction Configuration

### Global Settings

```bash
# Set default transaction timeout
arxos config set transaction-timeout=10m

# Set default isolation level
arxos config set transaction-isolation=read-committed

# Enable/disable auto-commit
arxos config set auto-commit=false
```

### Per-Transaction Settings

```bash
# Custom timeout for specific transaction
arxos transaction begin --timeout=1h

# Custom validation rules
arxos transaction begin --validate=strict

# Custom notification settings
arxos transaction begin --notify=slack:#arxos-alerts
```