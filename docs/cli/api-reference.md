# API Reference

Complete command reference for the Arxos CLI. Commands are organized by functional area.

## Global Options

These options are available for all commands:

```bash
--help, -h              Show help information
--version, -v           Show version information
--config FILE           Use specific config file
--format FORMAT         Output format (json, table, csv, yaml)
--verbose, -V           Verbose output
--quiet, -q             Suppress non-essential output
--dry-run               Preview changes without executing
--no-cache              Disable caching for this command
--timeout DURATION      Command timeout (default: 30s)
```

## Authentication Commands

### `arxos auth`

Manage authentication and authorization.

#### `arxos auth login`
Login to Arxos with your credentials.

```bash
arxos auth login [OPTIONS]

Options:
  --org ORG               Organization name
  --interactive           Use browser-based login
  --api-key KEY          Login with API key
  --endpoint URL         Custom API endpoint
```

#### `arxos auth logout`
Logout and clear authentication tokens.

```bash
arxos auth logout [OPTIONS]

Options:
  --all                  Logout from all organizations
  --clear-cache         Clear all cached data
```

#### `arxos auth status`
Show current authentication status.

```bash
arxos auth status [OPTIONS]

Options:
  --show-token          Show current token (security risk)
  --show-permissions    Show detailed permissions
```

#### `arxos auth token`
Manage authentication tokens.

```bash
arxos auth token <SUBCOMMAND>

Subcommands:
  info                   Show token information
  refresh                Refresh expired token
  create                 Create new API token
  revoke                 Revoke token
```

## Connection Commands

### `arxos connect`
Connect to a building repository.

```bash
arxos connect <BUILDING_URI> [OPTIONS]

Arguments:
  BUILDING_URI          Building connection string (building://org/name)

Options:
  --read-only          Connect in read-only mode
  --coordinates SYSTEM Coordinate system (imperial, metric)
  --cache LEVEL        Cache level (none, basic, aggressive)
  --dev-mode           Enable development mode
```

### `arxos disconnect`
Disconnect from current building.

```bash
arxos disconnect [OPTIONS]

Options:
  --clear-cache        Clear local cache
  --save-state         Save current state
```

### `arxos connection`
Manage building connections.

```bash
arxos connection <SUBCOMMAND>

Subcommands:
  status               Show connection status
  test                 Test connection
  list                 List available buildings
  switch BUILDING      Switch to different building
```

## Query Commands

### `arxos find`
Find objects matching criteria.

```bash
arxos find <OBJECT_TYPE> [CONDITIONS] [OPTIONS]

Arguments:
  OBJECT_TYPE          Type of objects to find (outlets, beams, walls, etc.)
  CONDITIONS           WHERE clause conditions

Options:
  --in LOCATION        Limit search to location (floor:N, room:ID, etc.)
  --within DISTANCE    Within distance of point or object
  --limit NUMBER       Maximum results to return
  --order-by FIELD     Sort results by field
  --spatial-index TYPE Use specific spatial index (octree, r-tree, grid)
```

Examples:
```bash
arxos find outlets
arxos find outlets in floor:45
arxos find outlets where voltage=120
arxos find outlets within 10ft of beam:B-101
```

### `arxos get`
Get specific object by ID.

```bash
arxos get <OBJECT_ID> [OPTIONS]

Arguments:
  OBJECT_ID            Unique object identifier

Options:
  --full               Include all properties and relationships
  --relationships      Include relationship information
  --constraints        Include constraint information
  --history           Show modification history
```

### `arxos query`
Execute custom AQL query.

```bash
arxos query <QUERY> [OPTIONS]

Arguments:
  QUERY                Arxos Query Language statement

Options:
  --explain            Show query execution plan
  --cache DURATION     Cache results for duration
  --spatial-index TYPE Use specific spatial index
```

### `arxos count`
Count objects matching criteria.

```bash
arxos count <OBJECT_TYPE> [CONDITIONS] [OPTIONS]

Arguments:
  OBJECT_TYPE          Type of objects to count
  CONDITIONS           Optional WHERE clause conditions

Options:
  --in LOCATION        Limit count to location
  --group-by FIELD     Group results by field
```

## Object Manipulation Commands

### `arxos create`
Create new objects.

```bash
arxos create <OBJECT_TYPE> [OPTIONS]

Arguments:
  OBJECT_TYPE          Type of object to create

Options:
  --id ID              Unique identifier for object
  --template TEMPLATE  Create from template
  --property KEY=VALUE Set property value
  --location X,Y,Z     3D coordinates
  --connect-to OBJECT  Connect to existing object
```

### `arxos set`
Set object properties.

```bash
arxos set <OBJECT_ID>.<PROPERTY>=<VALUE> [OPTIONS]
arxos set <OBJECT_ID> <PROPERTY>=<VALUE> [<PROPERTY>=<VALUE>...] [OPTIONS]

Arguments:
  OBJECT_ID            Object to modify
  PROPERTY             Property name
  VALUE                New property value

Options:
  --validate-constraints    Validate constraints before setting
  --if CONDITION           Only set if condition is true
  --batch                  Process as batch operation
```

### `arxos modify`
Modify objects with advanced options.

```bash
arxos modify <OBJECT_ID> [CHANGES] [OPTIONS]

Arguments:
  OBJECT_ID            Object to modify
  CHANGES              Property changes to apply

Options:
  --add-property KEY=VALUE     Add new property
  --remove-property KEY        Remove property
  --validate-constraints       Validate constraints
  --cascade                    Apply changes to related objects
```

### `arxos delete`
Delete objects.

```bash
arxos delete <OBJECT_ID> [OPTIONS]

Arguments:
  OBJECT_ID            Object to delete

Options:
  --force              Force deletion ignoring dependencies
  --cascade            Delete dependent objects
  --confirm            Skip confirmation prompt
```

### `arxos move`
Move objects to new locations.

```bash
arxos move <OBJECT_ID> to <COORDINATES> [OPTIONS]

Arguments:
  OBJECT_ID            Object to move
  COORDINATES          New coordinates (x,y,z)

Options:
  --validate-constraints    Check constraints before moving
  --update-connections     Update connected objects
```

## Relationship Commands

### `arxos connect`
Connect objects together.

```bash
arxos connect <OBJECT1> to <OBJECT2> [OPTIONS]

Arguments:
  OBJECT1              Source object
  OBJECT2              Target object

Options:
  --relationship TYPE   Type of relationship
  --properties PROPS    Relationship properties
```

### `arxos disconnect`
Remove object connections.

```bash
arxos disconnect <OBJECT1> from <OBJECT2> [OPTIONS]

Arguments:
  OBJECT1              Source object
  OBJECT2              Target object

Options:
  --relationship TYPE   Specific relationship type to remove
```

### `arxos relationships`
View object relationships.

```bash
arxos relationships <OBJECT_ID> [OPTIONS]

Arguments:
  OBJECT_ID            Object to examine

Options:
  --type TYPE          Filter by relationship type
  --depth NUMBER       Relationship traversal depth
  --graph              Show relationship graph
```

## Transaction Commands

### `arxos transaction`
Manage transactions.

```bash
arxos transaction <SUBCOMMAND>

Subcommands:
  begin [OPTIONS]      Start new transaction
  commit               Commit current transaction
  rollback            Rollback current transaction
  status              Show transaction status
  validate            Validate transaction changes
```

#### Transaction Options
```bash
# Begin transaction options
--description TEXT       Transaction description
--timeout DURATION      Transaction timeout
--isolation LEVEL       Isolation level (read-committed, serializable, etc.)
--read-only             Read-only transaction
```

### `arxos savepoint`
Manage transaction savepoints.

```bash
arxos savepoint <SUBCOMMAND>

Subcommands:
  create NAME          Create savepoint
  rollback NAME        Rollback to savepoint  
  release NAME         Release savepoint
```

## Sync Commands

### `arxos sync`
Manage real-time synchronization.

```bash
arxos sync [SUBCOMMAND] [OPTIONS]

Subcommands:
  push                 Push local changes to server
  pull                 Pull changes from server
  status               Show sync status
  pause                Pause automatic sync
  resume               Resume automatic sync
  reset                Reset sync state
```

### `arxos conflicts`
Manage sync conflicts.

```bash
arxos conflicts <SUBCOMMAND>

Subcommands:
  list                 List active conflicts
  resolve ID           Resolve specific conflict
  resolve-all          Resolve all conflicts automatically
```

### `arxos watch`
Watch for real-time changes.

```bash
arxos watch <OBJECT_OR_AREA> [OPTIONS]

Arguments:
  OBJECT_OR_AREA       Object ID or area to watch

Options:
  --events TYPES       Event types to watch for
  --notify LEVEL       Notification level (immediate, digest)
  --duration TIME      How long to watch
```

## Validation Commands

### `arxos validate`
Validate objects and constraints.

```bash
arxos validate [TARGET] [OPTIONS]

Arguments:
  TARGET               Object, area, or query to validate

Options:
  --constraints        Validate constraints only
  --relationships      Validate relationships only
  --spatial-conflicts  Check for spatial conflicts
  --code-compliance    Check building code compliance
```

### `arxos constraints`
Manage object constraints.

```bash
arxos constraints <OBJECT_ID> [SUBCOMMAND] [OPTIONS]

Subcommands:
  list                 List object constraints
  check                Check constraint violations
  resolve              Resolve constraint violations
  override             Override constraint (requires permission)
```

## System Commands

### `arxos config`
Manage CLI configuration.

```bash
arxos config <SUBCOMMAND>

Subcommands:
  get KEY              Get configuration value
  set KEY=VALUE        Set configuration value
  list                 List all configuration
  reset                Reset to defaults
  validate             Validate configuration
```

### `arxos cache`
Manage caching system.

```bash
arxos cache <SUBCOMMAND>

Subcommands:
  status               Show cache status
  clear [TYPE]         Clear cache
  preload TARGET       Pre-load objects into cache
  stats                Show cache statistics
  optimize             Optimize cache configuration
```

### `arxos performance` (`arxos perf`)
Performance monitoring and optimization.

```bash
arxos perf <SUBCOMMAND>

Subcommands:
  monitor              Monitor performance live
  profile OPERATION    Profile specific operation
  benchmark            Run performance benchmarks
  report               Generate performance report
  optimize             Auto-optimize performance settings
```

## Import/Export Commands

### `arxos import`
Import building data.

```bash
arxos import [OPTIONS] <FILE>

Arguments:
  FILE                 File to import

Options:
  --format FORMAT      Input format (revit, autocad, ifc, csv, json)
  --type TYPE          Object type being imported
  --validate           Validate before import
  --batch-size SIZE    Import batch size
  --continue-on-error  Continue on validation errors
```

### `arxos export`
Export building data.

```bash
arxos export [TARGET] [OPTIONS]

Arguments:
  TARGET               Objects to export (query or object IDs)

Options:
  --format FORMAT      Export format (json, csv, revit, ifc)
  --output FILE        Output file path
  --include-relationships    Include relationship data
  --compress           Compress output
```

## Utility Commands

### `arxos help`
Show help information.

```bash
arxos help [COMMAND]

Arguments:
  COMMAND              Command to get help for
```

### `arxos version`
Show version information.

```bash
arxos version [OPTIONS]

Options:
  --detailed           Show detailed version information
  --check-updates      Check for available updates
```

### `arxos diagnose`
Diagnose system issues.

```bash
arxos diagnose [OPTIONS]

Options:
  --connectivity       Test connectivity
  --performance        Check performance issues
  --cache              Validate cache integrity
  --full-report        Generate comprehensive diagnostic report
```

## Batch Operations

### `arxos batch`
Execute batch operations.

```bash
arxos batch <SUBCOMMAND>

Subcommands:
  create TYPE          Batch create objects
  update QUERY         Batch update objects
  delete QUERY         Batch delete objects
  execute FILE         Execute batch commands from file
```

## Advanced Commands

### `arxos script`
Execute Arxos scripts.

```bash
arxos script <FILE> [OPTIONS]

Arguments:
  FILE                 Script file to execute

Options:
  --variables FILE     Variable definitions file
  --dry-run           Preview script execution
  --continue-on-error Continue on errors
```

### `arxos template`
Manage object templates.

```bash
arxos template <SUBCOMMAND>

Subcommands:
  list [TYPE]          List available templates
  create NAME          Create template from object
  apply NAME           Apply template to objects
  edit NAME            Edit template definition
```

### `arxos backup`
Backup and restore operations.

```bash
arxos backup <SUBCOMMAND>

Subcommands:
  create NAME          Create backup
  restore NAME         Restore from backup
  list                 List available backups
  delete NAME          Delete backup
```

## Exit Codes

The Arxos CLI uses standard exit codes:

- `0`: Success
- `1`: General error
- `2`: Misuse of shell command
- `64`: Command line usage error
- `65`: Data format error
- `66`: Cannot open input
- `67`: Addressee unknown
- `68`: Host name unknown
- `69`: Service unavailable
- `70`: Internal software error
- `71`: System error
- `72`: Critical OS file missing
- `73`: Can't create output file
- `74`: Input/output error
- `75`: Temporary failure
- `76`: Remote error in protocol
- `77`: Permission denied
- `78`: Configuration error

## Environment Variables

- `ARXOS_ORG`: Default organization
- `ARXOS_BUILDING`: Default building
- `ARXOS_API_KEY`: API key for authentication
- `ARXOS_ENDPOINT`: Custom API endpoint
- `ARXOS_CONFIG`: Path to configuration file
- `ARXOS_CACHE_DIR`: Cache directory location
- `ARXOS_LOG_LEVEL`: Logging level (debug, info, warn, error)
- `ARXOS_TIMEOUT`: Default command timeout
- `ARXOS_FORMAT`: Default output format

## Configuration Files

### Main Configuration
Location: `~/.arxos/config.json`

```json
{
  "auth": {
    "current_org": "my-org",
    "tokens": {...}
  },
  "connection": {
    "current": "building://my-org/my-building",
    "preferences": {...}
  },
  "cache": {
    "memory": {"size": "1GB"},
    "disk": {"size": "10GB"}
  },
  "sync": {
    "enabled": true,
    "conflict_resolution": "prompt"
  }
}
```

### User Preferences
Location: `~/.arxos/preferences.json`

```json
{
  "output_format": "table",
  "spatial_index": "octree",
  "coordinate_system": "imperial",
  "notifications": {
    "enabled": true,
    "types": ["modifications", "conflicts"]
  }
}
```