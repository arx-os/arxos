# SSH Terminal Interface

The Arxos SSH terminal provides universal access to the mesh network from any device with an SSH client. No special software required - just SSH.

## Architecture

```
User Device → SSH Client → Arxos Terminal → Mesh Node → RF Network
           Any SSH         Port 2222      Ed25519 Auth   LoRa Radio
```

## Features

### Universal Compatibility
- Works with any SSH client (OpenSSH, PuTTY, Termux, etc.)
- No installation required on user device
- Supports all platforms (Linux, macOS, Windows, mobile)
- Terminal-based UI using ratatui

### Secure Authentication
- Ed25519 key-based authentication (no passwords)
- Optional password authentication for initial setup
- Per-node access control
- Audit logging of all commands

### Real-Time Mesh Access
- Direct connection to mesh nodes
- Live packet monitoring
- Network topology visualization
- RSSI signal strength display

## Connection Methods

### Basic Connection
```bash
# Connect with default settings
ssh arxos@mesh-node.local -p 2222

# Connect to specific IP
ssh arxos@192.168.1.100 -p 2222
```

### Key-Based Authentication (Recommended)
```bash
# Generate Ed25519 key pair
ssh-keygen -t ed25519 -f ~/.ssh/arxos_key

# Connect with key
ssh -i ~/.ssh/arxos_key arxos@mesh-node.local -p 2222
```

### Password Authentication (Initial Setup)
```bash
# Connect with password prompt
ssh arxos@mesh-node.local -p 2222
Password: [enter setup password]
```

### Auto-Connect Configuration
```bash
# ~/.ssh/config
Host arxos
    HostName mesh-node.local
    Port 2222
    User arxos
    IdentityFile ~/.ssh/arxos_key
    ServerAliveInterval 30
    ServerAliveCountMax 3

# Then simply:
ssh arxos
```

## Terminal Commands

### Connection Management
```bash
connect                 # Connect to mesh node
disconnect             # Disconnect from node
config                 # Show current configuration
status                 # Connection and mesh status
```

### Document Commands
```bash
load-plan <file>       # Load PDF/IFC building plan
view-floor [n]         # View floor n (ASCII art)
list-floors           # List all floors in building
show-equipment [n]    # Show equipment on floor n
export-arxobjects     # Export as 13-byte objects
```

### ArxObject Queries
```bash
arxos query <search>   # Query objects
  Examples:
    arxos query "room:127"
    arxos query "type:outlet status:faulty"
    arxos query "floor:2 type:light"
    arxos query "building:0x0001"

arxos scan [location]  # Trigger LiDAR scan
arxos show <id>       # Show object details
arxos update <id>     # Update object attributes
```

### Mesh Network Commands
```bash
arxos mesh            # Show mesh statistics
arxos mesh nodes      # List all nodes
arxos mesh routes     # Show routing table
arxos mesh packets    # Monitor packets (live)
arxos mesh rssi       # Signal strength map
```

### Database Operations
```bash
arxos db stats        # Database statistics
arxos db sync         # Force synchronization
arxos db export       # Export to SQL dump
arxos db query <sql>  # Raw SQL query (read-only)
```

### System Commands
```bash
help                  # Show command help
clear                 # Clear terminal
history               # Command history
quit/exit            # Exit terminal
```

## Terminal UI Layout

```
╔═══════════════════════════════════════════════════════════╗
║ Arxos Terminal v1.0.0 | Building: Jefferson Elementary    ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ┌─────────┐  ┌─────────┐  ┌─────────┐                 ║
║  │  127    │  │  128    │  │  129    │                 ║
║  │Lab [O]  │  │Class    │  │Computer │                 ║
║  │   [L]   │  │  [L][V] │  │  [D][D] │                 ║
║  └───| |───┘  └───| |───┘  └───| |───┘                 ║
║                                                           ║
║ > arxos query "room:127 type:outlet"                     ║
║ Found 2 objects:                                         ║
║   [0x0001:0x0201] Outlet @ (5.2, 3.1, 0.3)m            ║
║   [0x0001:0x0201] Outlet @ (5.2, 6.4, 0.3)m            ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║ Connected: mesh-01 | RSSI: -67dBm | Nodes: 12 | Uptime: 4h║
╚═══════════════════════════════════════════════════════════╝
```

## Advanced Features

### Batch Operations
```bash
# Execute commands from file
ssh arxos@mesh-node.local -p 2222 < commands.txt

# Pipe query results
ssh arxos@mesh-node.local -p 2222 "arxos query 'type:outlet'" | grep faulty
```

### Monitoring Mode
```bash
# Live packet monitor
ssh arxos@mesh-node.local -p 2222 "arxos mesh packets --follow"

# Watch mesh topology changes
watch -n 5 'ssh arxos "arxos mesh nodes"'
```

### Scripting Integration
```python
#!/usr/bin/env python3
import subprocess
import json

def query_arxos(query):
    cmd = f'ssh arxos "arxos query \\"{query}\\""'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

# Find all faulty outlets
faulty = query_arxos("type:outlet status:faulty")
print(f"Faulty outlets:\n{faulty}")
```

### Configuration File
```toml
# ~/.config/arxos/terminal.toml
[connection]
host = "mesh-gateway.local"
port = 2222
username = "arxos"
timeout_seconds = 30

[auth]
private_key_path = "~/.ssh/arxos_key"
known_hosts_path = "~/.ssh/known_hosts"

[display]
color_scheme = "dark"
ascii_art = true
auto_refresh = true
refresh_interval = 5
```

## Security Considerations

### Key Management
- Store private keys securely (chmod 600)
- Use different keys for different access levels
- Rotate keys periodically
- Never share private keys

### Network Security
- SSH provides encrypted transport
- All commands are logged
- Rate limiting prevents abuse
- Mesh nodes verify signatures

### Access Control
```bash
# Admin commands (require admin key)
arxos admin update-firmware
arxos admin set-config
arxos admin add-node

# Read-only access (default)
arxos query
arxos mesh
arxos view-floor
```

## Performance

### Connection Metrics
- Initial connection: <1 second
- Command latency: <100ms local, <500ms remote
- Query response: <50ms for indexed queries
- Throughput: 100+ commands/second

### Resource Usage
- Terminal client: ~10MB RAM
- SSH daemon: ~5MB RAM per connection
- CPU usage: <1% idle, <5% active
- Network: ~1KB/s monitoring, ~10KB/s active

## Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
ping mesh-node.local

# Check SSH port
nmap -p 2222 mesh-node.local

# Verbose connection
ssh -vvv arxos@mesh-node.local -p 2222

# Clear known hosts
ssh-keygen -R "[mesh-node.local]:2222"
```

### Authentication Problems
```bash
# Check key permissions
ls -la ~/.ssh/arxos_key
# Should be: -rw------- (600)

# Test key
ssh-add -l | grep arxos

# Generate new key
ssh-keygen -t ed25519 -f ~/.ssh/arxos_key_new
```

### Performance Issues
```bash
# Check mesh status
arxos mesh stats

# Monitor network
arxos mesh packets --stats

# Database health
arxos db stats
```

## Examples

### Building Survey Workflow
```bash
# 1. Connect to mesh
ssh arxos

# 2. Load building plan
> load-plan school_plans.pdf

# 3. View first floor
> view-floor 1

# 4. Query specific room
> arxos query "room:127"

# 5. Update equipment status
> arxos update 0x0001:0x0201:127 status:verified

# 6. Export for reporting
> export-arxobjects /tmp/survey_results.arxo
```

### Emergency Response Mode
```bash
# Quick connection with minimal UI
ssh arxos -t "arxos emergency"

# Shows critical information only:
EMERGENCY MODE - JEFFERSON ELEMENTARY
Floor 1: Clear exits at North, South
Floor 2: Blocked exit at West
Fire equipment: 12 extinguishers OK
Evacuation routes: 3 available
Occupancy estimate: 150-200
```

### Maintenance Inspection
```bash
# Schedule-based queries
arxos query "type:hvac next_service:<30days"
arxos query "type:fire_alarm last_test:>6months"
arxos query "floor:2 status:maintenance"
```

## Integration with Other Tools

### With tmux/screen
```bash
# Persistent session
tmux new -s arxos
ssh arxos
# Detach: Ctrl-B D
# Reattach: tmux attach -t arxos
```

### With monitoring systems
```bash
# Nagios/Icinga check
check_arxos_mesh() {
    nodes=$(ssh arxos "arxos mesh nodes" | grep active | wc -l)
    if [ $nodes -lt 10 ]; then
        echo "CRITICAL: Only $nodes mesh nodes active"
        exit 2
    fi
    echo "OK: $nodes mesh nodes active"
    exit 0
}
```

### With logging systems
```bash
# Send to syslog
ssh arxos "arxos mesh packets" | logger -t arxos-mesh

# JSON output for parsing
ssh arxos "arxos query --json 'floor:1'" | jq '.objects[]'
```

## Best Practices

1. **Use key-based authentication** - More secure than passwords
2. **Set up SSH config** - Simplifies connection commands
3. **Monitor mesh health** - Check RSSI and node count regularly
4. **Batch operations** - Group commands for efficiency
5. **Log important queries** - Maintain audit trail
6. **Test emergency mode** - Ensure rapid access when needed
7. **Keep terminal updated** - Latest version has bug fixes
8. **Use screen/tmux** - Persistent sessions for long operations

---

*The terminal is the interface. SSH is the protocol. Simplicity is the strength.*