# ArxOS Cloud Setup Guide

## Overview

ArxOS now supports cloud synchronization and distributed storage backends. This guide covers the cloud-ready features added in Phase 0 of the platform evolution.

## New Features

### 1. Configuration System

ArxOS now uses a flexible configuration system that supports multiple operational modes:

- **Local Mode** - Traditional offline operation with local storage
- **Cloud Mode** - Full cloud synchronization with remote storage
- **Hybrid Mode** - Local operation with optional cloud backup

### 2. Storage Abstraction

The storage layer has been abstracted to support multiple backends:

- **Local** - File system storage (default)
- **S3** - Amazon S3 or compatible storage (coming soon)
- **GCS** - Google Cloud Storage (coming soon)
- **Azure** - Azure Blob Storage (coming soon)

### 3. Telemetry

Optional telemetry for understanding usage patterns and improving the platform:

- Event tracking for commands and operations
- Performance metrics collection
- Error reporting for debugging
- Fully opt-in with configurable sampling

## Getting Started

### Initialize Configuration

Create a default configuration file:

```bash
arx config init --mode local
```

For cloud-ready setup:

```bash
arx config init --mode hybrid
```

### View Configuration

Check your current configuration:

```bash
arx config show
```

### Modify Configuration

Update configuration values:

```bash
# Enable cloud features
arx config set cloud.enabled true

# Set cloud API endpoint
arx config set cloud.url https://api.arxos.io

# Enable telemetry
arx config set telemetry.enabled true

# Set storage backend
arx config set storage.backend s3
arx config set storage.bucket my-arxos-bucket
arx config set storage.region us-east-1
```

### Validate Configuration

Ensure your configuration is valid:

```bash
arx config validate
```

## Environment Variables

Configuration can be overridden using environment variables:

```bash
# Operating mode
export ARXOS_MODE=cloud

# Cloud settings
export ARXOS_CLOUD_URL=https://api.arxos.io
export ARXOS_API_KEY=your-api-key
export ARXOS_ORG_ID=your-org-id

# Storage settings
export ARXOS_STORAGE_BACKEND=s3
export ARXOS_STORAGE_BUCKET=my-bucket
export ARXOS_STORAGE_REGION=us-east-1

# Feature flags
export ARXOS_CLOUD_SYNC=true
export ARXOS_AI_ENABLED=true
export ARXOS_TELEMETRY=true

# Storage credentials
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Configuration File

The configuration file is stored at:
- `~/.arxos/config.json` (default)
- `./arxos.json` (project-specific)
- Custom path via `--config` flag

Example configuration:

```json
{
  "mode": "hybrid",
  "version": "0.1.0",
  "state_dir": "/Users/username/.arxos",
  "cache_dir": "/Users/username/.arxos/cache",
  "cloud": {
    "enabled": true,
    "base_url": "https://api.arxos.io",
    "api_key": "********1234",
    "org_id": "org-123",
    "sync_enabled": true,
    "sync_interval": 300000000000
  },
  "storage": {
    "backend": "local",
    "local_path": "/Users/username/.arxos/data",
    "cloud_bucket": "",
    "cloud_region": ""
  },
  "api": {
    "timeout": 30000000000,
    "retry_attempts": 3,
    "retry_delay": 1000000000,
    "user_agent": "ArxOS-CLI/0.1.0"
  },
  "telemetry": {
    "enabled": false,
    "endpoint": "https://telemetry.arxos.io",
    "sample_rate": 0.1,
    "debug": false,
    "anonymous_id": ""
  },
  "features": {
    "cloud_sync": true,
    "ai_integration": false,
    "offline_mode": false,
    "beta_features": false,
    "analytics": false,
    "auto_update": false
  }
}
```

## Command-Line Flags

New global flags are available:

```bash
# Use custom configuration file
arx --config /path/to/config.json <command>

# Run in offline mode (disables cloud sync)
arx --offline <command>

# Enable verbose logging
arx -v <command>

# Output in JSON format
arx --json <command>
```

## Storage Manager

The storage manager provides:

- **Automatic retry** on failures
- **Fallback storage** for redundancy
- **Cache layer** for performance
- **Sync capability** between backends

### Storage Operations

All storage operations now go through the abstraction layer:

```go
// Put data to storage
err := storageManager.Put(ctx, "building/floor1.json", data)

// Get data from storage
data, err := storageManager.Get(ctx, "building/floor1.json")

// Check existence
exists, err := storageManager.Exists(ctx, "building/floor1.json")

// List keys with prefix
keys, err := storageManager.List(ctx, "building/")

// Stream large files
reader, err := storageManager.GetReader(ctx, "building/floor1.pdf")
defer reader.Close()
```

## Telemetry

Telemetry helps improve ArxOS by collecting anonymous usage data:

### What's Collected

- Command execution (name, duration, success/failure)
- Feature usage patterns
- Error occurrences (no sensitive data)
- Performance metrics

### Privacy

- Fully opt-in (disabled by default)
- Anonymous identifiers only
- No personal or building data collected
- Configurable sampling rate
- Local debugging mode available

### Enable Telemetry

```bash
# Enable telemetry
arx config set telemetry.enabled true

# Set sampling rate (0.1 = 10% of events)
arx config set telemetry.sample_rate 0.1

# Enable debug mode (logs telemetry locally)
arx config set telemetry.debug true
```

## Testing Cloud Features

### Run Tests

```bash
# Test configuration system
go test ./internal/config -v

# Test storage abstraction
go test ./internal/storage -v

# Run all tests
go test ./... -v
```

### Integration Testing

```bash
# Test local storage
arx --offline import test.pdf
arx --offline map

# Test with configuration
arx --config test-config.json import test.pdf

# Test verbose mode
arx -v config show
```

## Migration from Previous Version

Existing ArxOS installations will continue to work without modification:

1. Default configuration uses local mode
2. Existing `.arxos` directories are preserved
3. No cloud features are enabled by default
4. Commands work exactly as before

To enable cloud features:

1. Run `arx config init --mode hybrid`
2. Configure cloud settings as needed
3. Enable desired features
4. Test with `arx config validate`

## Troubleshooting

### Configuration Issues

```bash
# Reset to defaults
rm ~/.arxos/config.json
arx config init

# Validate configuration
arx config validate

# Check environment overrides
arx config show | grep "Environment"
```

### Storage Issues

```bash
# Test storage backend
arx --verbose config validate

# Use offline mode if cloud is unavailable
arx --offline <command>

# Check storage paths
arx config show | grep "Storage"
```

### Telemetry Issues

```bash
# Disable telemetry
arx config set telemetry.enabled false

# Or via environment
export ARXOS_TELEMETRY=false
```

## Security Considerations

### API Keys

- Never commit API keys to version control
- Use environment variables for sensitive data
- Keys are masked in configuration files
- Rotate keys regularly

### Storage Credentials

- Use IAM roles when possible (AWS/GCP)
- Store credentials in environment variables
- Never log credentials
- Use minimal required permissions

### Network Security

- All cloud communication uses TLS 1.3
- Certificate validation is enforced
- Configurable timeouts and retries
- Offline mode for sensitive environments

## Next Steps

The cloud foundation is now in place. Future phases will add:

- **Phase 1**: Cloud sync and web interface
- **Phase 2**: PDF access control system
- **Phase 3**: Mobile app with AR
- **Phase 4**: AI integration
- **Phase 5**: Viral growth features

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for details.

## Support

For issues or questions:
- Check the [documentation](https://github.com/joelpate/arxos/tree/main/docs)
- Open an [issue](https://github.com/joelpate/arxos/issues)
- Review the [implementation roadmap](IMPLEMENTATION_ROADMAP.md)