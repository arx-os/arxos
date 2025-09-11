# Configuration Directory

This directory contains configuration files for ArxOS components.

## Configuration Files

### arxd.yaml
Configuration for the ArxOS daemon. Defines:
- Watch directories for auto-import
- Sync intervals
- Driver settings
- Database connections

## Example Configuration

```yaml
# arxd.yaml
daemon:
  port: 8080
  watch_dirs:
    - /var/arxos/bim/
  sync_interval: 5m
  
database:
  type: sqlite
  path: .arxos/building.db
  
import:
  pdf:
    enabled: true
    ocr: true
  ifc:
    enabled: false
```

## Environment-Specific Configs

- `arxd.yaml` - Default configuration
- `arxd.dev.yaml` - Development overrides (gitignored)
- `arxd.prod.yaml` - Production settings (gitignored)

## Usage

```bash
# Use default config
arxd start

# Use specific config
arxd start --config configs/arxd.yaml

# Use environment variable
ARXD_CONFIG=configs/arxd.prod.yaml arxd start
```