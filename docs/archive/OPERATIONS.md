# ArxOS Operations Guide

Operational procedures for deploying, maintaining, and troubleshooting ArxOS.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Common Operations](#common-operations)
4. [Error Recovery](#error-recovery)
5. [Troubleshooting](#troubleshooting)
6. [Monitoring](#monitoring)

## Installation

### Binary Distribution

Download the latest release binary for your platform:

```bash
# Linux
wget https://github.com/arx-os/arxos/releases/latest/download/arxos-v0.1.0-linux.tar.gz
tar -xzf arxos-v0.1.0-linux.tar.gz
sudo mv arxos /usr/local/bin/

# macOS
wget https://github.com/arx-os/arxos/releases/latest/download/arxos-v0.1.0-macos.tar.gz
tar -xzf arxos-v0.1.0-macos.tar.gz
sudo mv arxos /usr/local/bin/

# Windows
# Download and extract arxos-v0.1.0-windows.zip
# Add to PATH or use directly
```

### From Source

```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
cargo build --release
sudo cp target/release/arxos /usr/local/bin/
```

### Verify Installation

```bash
arxos health
```

## Configuration

ArxOS loads configuration from (in precedence order):
1. Environment variables
2. `~/.arxos/config.toml`
3. `.arxos/config.toml` (project-specific)
4. Default configuration

### Environment Variables

```bash
export GIT_AUTHOR_NAME="Your Name"
export GIT_AUTHOR_EMAIL="you@example.com"
export ARXOS_LOG_LEVEL="info"
```

### Configuration File

Create `~/.arxos/config.toml`:

```toml
[user]
name = "Your Name"
email = "you@example.com"

[building]
auto_commit = true
validate_on_import = true

[performance]
max_parallel_threads = 8
show_progress = true
```

## Common Operations

### Import Building Data

```bash
# Dry run to preview changes
arxos import building.ifc --dry-run

# Actual import
arxos import building.ifc --repo ./buildings/building-name
```

### Git Operations

```bash
# Check status
arxos status --verbose

# Stage changes
arxos stage --all

# Commit changes
arxos commit "Add new equipment"

# View history
arxos history --limit 20

# Rollback to previous commit
git reset --hard HEAD~1  # Use native Git commands
```

### Search and Filter

```bash
# Search equipment
arxos search "VAV" --equipment

# Filter by floor
arxos filter --floor 2 --format json

# Complex search
arxos search "HVAC" --regex --case-sensitive --limit 100
```

### Render Visualization

```bash
# 3D visualization
arxos render --building "Main Building" --three-d --show-status

# Interactive mode
arxos interactive --building "Main Building" --show-rooms
```

## Error Recovery

ArxOS uses Git for data storage, providing built-in version control and rollback capabilities.

### Dry-Run Mode

Use `--dry-run` on destructive operations to preview changes:

```bash
# Preview import
arxos import building.ifc --dry-run

# Preview room creation
arxos room create --building "Main" --floor 1 --name "Room 101" --dry-run
```

### Retry Logic

ArxOS includes automatic retry logic for transient failures:

- **Network operations**: 3 attempts with exponential backoff
- **File operations**: Up to 5 attempts
- **Git operations**: 3 attempts with 100ms initial delay

### Rollback Operations

#### Undo Last Commit

```bash
# View what will be undone
arxos diff HEAD~1

# Soft reset (keeps changes staged)
git reset --soft HEAD~1

# Hard reset (discards changes)
git reset --hard HEAD~1
```

#### Undo Staged Changes

```bash
# Unstage specific file
arxos unstage building.yaml

# Unstage all files
arxos unstage --all
```

#### Restore Previous Version

```bash
# View commit history
arxos history --limit 20

# Checkout specific commit
git checkout <commit-hash> building.yaml

# Restore and commit
git commit -m "Rollback to previous version"
```

#### Emergency Recovery

If you've made a catastrophic change:

```bash
# Find last good commit
arxos history --verbose

# Hard reset to that commit
git reset --hard <commit-hash>

# Force push if needed (caution!)
git push --force origin main
```

### Backup Strategy

#### Automated Backups

Schedule regular backups using Git pushes:

```bash
# Create backup script
cat > backup.sh <<EOF
#!/bin/bash
cd /path/to/building/repo
git add .
git commit -m "Automated backup $(date)"
git push origin main
EOF

chmod +x backup.sh

# Add to crontab (hourly backups)
(crontab -l 2>/dev/null; echo "0 * * * * /path/to/backup.sh") | crontab -
```

#### Manual Backup

```bash
# Create full backup
tar -czf building-backup-$(date +%Y%m%d).tar.gz buildings/

# Backup to remote location
rsync -av buildings/ backup-server:/backups/arxos/
```

## Troubleshooting

### Health Checks

Run diagnostics:

```bash
# Full system check
arxos health

# Specific component
arxos health --component git --verbose
```

### Common Issues

#### "Git not available"

**Symptom**: Health check shows Git not found

**Solution**:
```bash
# Install Git
sudo apt-get install git  # Ubuntu/Debian
brew install git          # macOS
```

#### "Permission denied" on Repository

**Symptom**: Cannot write to Git repository

**Solution**:
```bash
# Fix permissions
chmod -R u+w buildings/
chown -R $(whoami) buildings/
```

#### "IFC file validation failed"

**Symptom**: Import fails with path validation error

**Solution**:
```bash
# Use absolute paths or files in current directory
arxos import /absolute/path/to/building.ifc
# or
cd /path/to/ifc/files
arxos import building.ifc
```

#### "Out of memory"

**Symptom**: Import fails on large buildings

**Solution**:
```bash
# Use spatial indexing
arxos import building.ifc --spatial-index

# Process in chunks (use smaller IFC file segments)
# Or increase system memory
```

#### "YAML parsing failed"

**Symptom**: Cannot read building YAML files

**Solution**:
```bash
# Validate YAML syntax
arxos validate --path building.yaml

# Restore from Git history
git checkout HEAD~1 building.yaml
```

### Logging

Enable debug logging:

```bash
export RUST_LOG=debug
arxos import building.ifc

# Or configure in config.toml
```

## Monitoring

### Watch Mode

Monitor building data in real-time:

```bash
# Watch all buildings
arxos watch

# Watch specific floor
arxos watch --building "Main" --floor 2

# Watch for sensor alerts only
arxos watch --building "Main" --alerts-only
```

### Performance Monitoring

Run benchmarks:

```bash
# Full benchmark suite
cargo bench --bench performance_benchmarks

# View historical performance
cat target/criterion/**/new/estimates.json
```

### Capacity Planning

See [BENCHMARKS.md](BENCHMARKS.md) for performance characteristics and capacity guidelines:

- Small buildings (< 100 entities): < 100ms operations
- Medium buildings (100-1,000 entities): < 500ms operations
- Large buildings (1,000-10,000 entities): < 2s operations

## Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Health check**: `arxos health --verbose`

## Emergency Contacts

For production-critical issues:
1. Run `arxos health --verbose`
2. Check Git history: `arxos history --limit 10`
3. Review logs: `export RUST_LOG=debug`
4. Create backup: See backup procedures above
5. Open GitHub issue with diagnostic output

