# Real-Time Sync & Collaboration

The Arxos CLI supports real-time collaboration, allowing multiple users to work on the same building simultaneously with automatic conflict resolution and live synchronization.

## Real-Time Sync Overview

### How It Works

- **Event-Driven Architecture**: All changes generate events that are distributed to connected clients
- **Operational Transforms**: Conflicting operations are automatically merged when possible
- **Conflict Resolution**: Smart algorithms resolve conflicts based on object types and change types
- **Live Updates**: See other users' changes in real-time with live cursors and change indicators

### Sync States

- **Connected**: Actively receiving live updates
- **Syncing**: Catching up with server state
- **Offline**: Working with local cache, changes queued
- **Conflict**: Manual intervention required for conflicting changes

## Setting Up Real-Time Sync

### Enable Sync Mode

```bash
# Connect with sync enabled (default)
arxos connect building://org/building --sync=enabled

# Connect in offline mode
arxos connect building://org/building --sync=offline

# Connect with specific sync preferences
arxos connect building://org/building --sync=enabled --conflict-resolution=auto
```

### Sync Configuration

```bash
# Configure sync settings
arxos config set sync.enabled=true
arxos config set sync.conflict-resolution=prompt
arxos config set sync.update-interval=1s

# View sync configuration
arxos config get sync
```

## Live Collaboration Features

### Presence Awareness

```bash
# View active users
arxos who --online

# Show user cursors and selections
arxos presence show

# Set your status
arxos presence set-status "Working on floor 45 electrical"

# View what others are working on
arxos presence activity
```

### Live Cursors and Selections

```bash
# Follow another user's work
arxos follow user:alice

# Show user selections in query results
arxos find outlets --show-user-selections

# Broadcast your current selection
arxos select outlet:R45-23 --broadcast
```

### Real-Time Notifications

```bash
# Enable change notifications
arxos notifications enable --types=modifications,creations,deletions

# Get notified when specific objects change
arxos watch outlet:R45-23 --notify=immediate

# Set up area-based notifications
arxos watch area floor:45 --notify=digest --interval=5m
```

## Change Synchronization

### Automatic Sync

```bash
# Changes are synced automatically by default
arxos set outlet:R45-23.voltage=240  # Syncs immediately

# Force sync of pending changes
arxos sync push

# Pull latest changes from server
arxos sync pull

# Full bidirectional sync
arxos sync
```

### Manual Sync Control

```bash
# Disable auto-sync temporarily
arxos sync pause

# Re-enable auto-sync
arxos sync resume

# Sync specific objects
arxos sync objects outlet:R45-23,outlet:R45-24

# Sync entire system
arxos sync system electrical.floor:45
```

### Change Queuing

```bash
# View pending changes
arxos sync queue

# Clear pending changes (lose local modifications)
arxos sync queue clear

# Prioritize specific changes
arxos sync queue prioritize outlet:R45-23

# Retry failed sync operations
arxos sync retry-failed
```

## Conflict Resolution

### Types of Conflicts

1. **Property Conflicts**: Same property modified by different users
2. **Relationship Conflicts**: Objects connected/disconnected simultaneously
3. **Spatial Conflicts**: Objects moved to conflicting positions
4. **Constraint Conflicts**: Changes that violate constraints when combined

### Automatic Resolution

```bash
# Set automatic resolution strategy
arxos config set conflict-resolution=auto

# Available auto-resolution strategies:
# - last-write-wins: Most recent change takes precedence
# - first-write-wins: First change takes precedence  
# - merge-compatible: Merge non-conflicting properties
# - user-priority: Higher priority user wins
```

### Manual Conflict Resolution

```bash
# View active conflicts
arxos conflicts list

# Get conflict details
arxos conflict details <conflict-id>

# Resolve conflict manually
arxos conflict resolve <conflict-id> --choose=local
arxos conflict resolve <conflict-id> --choose=remote
arxos conflict resolve <conflict-id> --choose=merged

# Create custom resolution
arxos conflict resolve <conflict-id> --custom="voltage=240,amperage=20"
```

### Three-Way Merge

```bash
# Perform three-way merge for complex conflicts
arxos merge --base=<base-version> --local=<local-changes> --remote=<remote-changes>

# Interactive merge tool
arxos merge --interactive <conflict-id>

# Preview merge result
arxos merge --preview <conflict-id>
```

## Collaborative Workflows

### Branching and Merging

```bash
# Create collaborative branch
arxos branch create "electrical-renovation" --collaborative

# Switch to branch
arxos branch switch "electrical-renovation"

# Merge branch back to main
arxos branch merge "electrical-renovation" --resolve-conflicts=auto

# View branch collaboration history
arxos branch history "electrical-renovation" --show-contributors
```

### Change Proposals

```bash
# Propose changes for review
arxos propose changes --title="Update outlet specifications" \
  --description="Standardize all outlets to 20A GFCI"

# Review pending proposals
arxos proposals list --assigned-to=me

# Approve proposal
arxos proposal approve <proposal-id>

# Request changes
arxos proposal request-changes <proposal-id> --comment="Check load calculations"
```

### Collaborative Editing Sessions

```bash
# Start collaborative session
arxos session start "Floor 45 MEP Review" --invite=alice,bob

# Join existing session
arxos session join <session-id>

# Share screen/view
arxos session share-view floor:45 --filter=electrical

# End session
arxos session end
```

## Offline Support

### Offline Mode

```bash
# Switch to offline mode
arxos offline enable

# Check offline status
arxos offline status

# View cached data
arxos offline cache list

# Sync when coming back online
arxos online --sync=full
```

### Conflict Resolution After Offline

```bash
# Resolve conflicts after coming online
arxos offline resolve-conflicts --strategy=interactive

# View offline changes before sync
arxos offline changes preview

# Selectively sync offline changes
arxos offline sync --selective
```

### Offline Cache Management

```bash
# Pre-cache data for offline work
arxos cache prefetch floor:45 --recursive

# Configure cache size
arxos cache config --max-size=1GB

# Clear offline cache
arxos cache clear --confirm
```

## Advanced Sync Features

### Event Streaming

```bash
# Stream live events
arxos events stream --filter="type=modification"

# Subscribe to specific object events
arxos events subscribe outlet:R45-23

# Custom event handlers
arxos events handler create --trigger="outlet.voltage.changed" \
  --action="notify-electrical-team"
```

### Operational Transforms

```bash
# View operation history
arxos operations history outlet:R45-23

# Apply operational transform
arxos operation apply <operation-id> --transform=true

# Undo operation with transform
arxos operation undo <operation-id> --preserve-later-changes
```

### Custom Sync Rules

```bash
# Define custom sync rules
arxos sync rule create "critical-systems" \
  --objects="structural.*,electrical.panels.*" \
  --priority=high \
  --conflict-resolution=manual

# List active sync rules
arxos sync rules list

# Disable sync rule
arxos sync rule disable "critical-systems"
```

## Monitoring and Diagnostics

### Sync Performance

```bash
# Monitor sync performance
arxos sync monitor --live

# View sync statistics
arxos sync stats --timeframe="last-hour"

# Diagnose sync issues
arxos sync diagnose
```

### Network Status

```bash
# Check network connectivity
arxos network status

# Test sync latency
arxos network latency-test

# Monitor bandwidth usage
arxos network monitor --duration=5m
```

### Debug Information

```bash
# Enable sync debugging
arxos debug sync --level=verbose

# View sync logs
arxos logs sync --tail=50

# Export sync diagnostics
arxos debug export-sync-info --output=sync-debug.json
```

## Security and Permissions

### Sync Permissions

```bash
# View sync permissions
arxos permissions sync

# Grant sync access
arxos permission grant user:alice sync:read,sync:write --object=floor:45

# Revoke sync access
arxos permission revoke user:bob sync:write --object=floor:45
```

### Audit Trail

```bash
# View collaboration audit trail
arxos audit collaboration --timeframe="last-week"

# Track specific user activity
arxos audit user alice --show-sync-events

# Export collaboration audit
arxos audit export --format=csv --include=sync-events
```

### Encryption

```bash
# Enable end-to-end encryption for sync
arxos config set sync.encryption=enabled

# View encryption status
arxos security sync-encryption status

# Rotate sync encryption keys
arxos security rotate-sync-keys
```

## Troubleshooting Sync Issues

### Common Issues

**Sync Stuck:**
```bash
# Reset sync state
arxos sync reset --confirm

# Force full resync
arxos sync full-refresh
```

**Conflicts Not Resolving:**
```bash
# Clear conflict state
arxos conflict clear-all --force

# Reset to server state
arxos reset-to-server --confirm
```

**Performance Issues:**
```bash
# Optimize sync performance
arxos sync optimize

# Reduce sync frequency
arxos config set sync.update-interval=5s
```

### Sync Health Check

```bash
# Run comprehensive sync health check
arxos health sync

# Test connectivity to sync servers
arxos health sync-connectivity

# Validate local sync state
arxos health sync-state-validation
```

### Recovery Procedures

```bash
# Recover from sync corruption
arxos sync recover --method=rebuild-from-server

# Backup current state before recovery
arxos backup create "pre-sync-recovery" --include=local-changes

# Restore from backup if needed
arxos restore "pre-sync-recovery" --confirm
```

## Best Practices

### Collaborative Workflows

1. **Communicate changes**: Use descriptive commit messages and status updates
2. **Work in focused areas**: Minimize overlapping work areas
3. **Regular sync breaks**: Periodically sync and resolve conflicts
4. **Use branches**: For major changes that might affect others
5. **Set up notifications**: Stay informed about relevant changes

### Conflict Prevention

1. **Coordinate modifications**: Communicate before major changes
2. **Use atomic transactions**: Group related changes together
3. **Regular pulls**: Keep local state up to date
4. **Lock critical objects**: For major structural changes
5. **Use staging areas**: Test changes before applying to main building

### Performance Optimization

1. **Selective sync**: Only sync relevant building areas
2. **Batch operations**: Group multiple changes together
3. **Optimize queries**: Use efficient query patterns
4. **Cache management**: Keep cache size reasonable
5. **Monitor bandwidth**: Be aware of sync data usage