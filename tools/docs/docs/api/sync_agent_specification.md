# Sync Agent Specification

## Overview

The Sync Agent provides automated synchronization between local and remote Arxos installations, supporting JSON-based project configuration and command chaining.

## Architecture

### Core Components
- **Sync Engine**: Handles file synchronization
- **Configuration Manager**: Manages JSON configuration
- **Command Processor**: Executes chained commands
- **Conflict Resolver**: Resolves synchronization conflicts
- **Status Reporter**: Reports sync status and progress

### Configuration Hierarchy
- Global: `~/.arxconfig.json`
- Project-level: `/arxfile.json`
- Environment-specific: `.env` files

## Project Structure

```
project/
├── arxfile.json               # Project metadata, permissions, sync info
├── symbols/                   # JSON symbol files
│   ├── mechanical/
│   ├── electrical/
│   └── security/
├── rules/                     # JSON rule definitions
├── models/                    # BIM models
├── reports/                   # Generated reports
└── .arxignore                 # Sync ignore patterns
```

## Configuration Files

### Global Configuration (`~/.arxconfig.json`)
```json
{
  "sync": {
    "enabled": true,
    "interval": 300,
    "conflict_resolution": "manual",
    "auto_backup": true
  },
  "remote": {
    "type": "sftp",
    "host": "sync.arxos.com",
    "port": 22,
    "username": "user",
    "key_file": "~/.ssh/id_rsa"
  },
  "notifications": {
    "email": "user@example.com",
    "webhook": "https://hooks.slack.com/..."
  }
}
```

### Project Configuration (`arxfile.json`)
```json
{
  "project_id": "building_001",
  "name": "Office Building Project",
  "description": "Commercial office building with 10 floors",
  "version": "1.0.0",
  "permissions": {
    "owner": "user@example.com",
    "editors": ["editor1@example.com", "editor2@example.com"],
    "viewers": ["viewer1@example.com"]
  },
  "sync": {
    "enabled": true,
    "remote_path": "/projects/building_001",
    "include_patterns": ["*.json", "*.svg", "*.bim"],
    "exclude_patterns": ["*.tmp", "*.log", "node_modules/"],
    "conflict_resolution": "auto"
  },
  "commands": {
    "pre_sync": [
      {
        "name": "validate_symbols",
        "command": "arx validate-symbols",
        "timeout": 300,
        "required": true
      },
      {
        "name": "run_tests",
        "command": "arx test",
        "timeout": 600,
        "required": false
      },
      {
        "name": "generate_reports",
        "command": "arx generate-reports",
        "timeout": 300,
        "required": false
      }
    ]
  },
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "last_modified": "2024-01-15T10:30:00Z",
    "tags": ["commercial", "office", "10-floors"]
  }
}
```

## Sync Operations

### File Synchronization
```python
class SyncAgent:
    def sync_files(self, local_path: str, remote_path: str):
        """Synchronize files between local and remote"""
        # Compare file timestamps
        # Upload new/modified files
        # Download remote changes
        # Resolve conflicts
        pass

    def resolve_conflicts(self, conflicts: List[Conflict]):
        """Resolve synchronization conflicts"""
        for conflict in conflicts:
            if conflict.resolution == "auto":
                self.auto_resolve(conflict)
            else:
                self.manual_resolve(conflict)
```

### Conflict Resolution
```python
class ConflictResolver:
    def auto_resolve(self, conflict: Conflict):
        """Automatically resolve conflicts based on rules"""
        if conflict.type == "symbol_file":
            # Use most recent version
            self.use_latest(conflict)
        elif conflict.type == "configuration":
            # Merge configurations
            self.merge_configs(conflict)
        elif conflict.type == "model":
            # Use local version with backup
            self.use_local_with_backup(conflict)

    def manual_resolve(self, conflict: Conflict):
        """Manual conflict resolution"""
        # Present options to user
        # Wait for user decision
        # Apply user choice
        pass
```

## Command Chaining

### Pre-sync Commands
```json
{
  "commands": {
    "pre_sync": [
      {
        "name": "validate_symbols",
        "command": "arx validate-symbols",
        "timeout": 300,
        "required": true
      },
      {
        "name": "run_tests",
        "command": "arx test",
        "timeout": 600,
        "required": false
      },
      {
        "name": "generate_reports",
        "command": "arx generate-reports",
        "timeout": 300,
        "required": false
      }
    ]
  }
}
```

### Post-sync Commands
```json
{
  "commands": {
    "post_sync": [
      {
        "name": "update_index",
        "command": "arx update-index",
        "timeout": 60,
        "required": true
      },
      {
        "name": "notify_team",
        "command": "arx notify --channel=team",
        "timeout": 30,
        "required": false
      }
    ]
  }
}
```

### Command Execution
```python
class CommandProcessor:
    def execute_chain(self, commands: List[Command]):
        """Execute a chain of commands"""
        results = []

        for command in commands:
            try:
                result = self.execute_command(command)
                results.append(result)

                if command.required and not result.success:
                    raise CommandError(f"Required command failed: {command.name}")

            except TimeoutError:
                raise CommandError(f"Command timed out: {command.name}")

        return results

    def execute_command(self, command: Command):
        """Execute a single command"""
        # Run command with timeout
        # Capture output and exit code
        # Return result
        pass
```

## Status Reporting

### Sync Status
```json
{
  "sync_id": "sync_20240115_103000",
  "status": "completed",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": "2024-01-15T10:32:00Z",
  "files_synced": 150,
  "conflicts_resolved": 2,
  "commands_executed": 4,
  "errors": [],
  "warnings": [
    "Some files were excluded due to size limits"
  ]
}
```

### Progress Reporting
```python
class StatusReporter:
    def report_progress(self, progress: Progress):
        """Report sync progress"""
        print(f"Syncing files: {progress.files_synced}/{progress.total_files}")
        print(f"Progress: {progress.percentage}%")

        if progress.current_file:
            print(f"Current file: {progress.current_file}")
```

## Error Handling

### Sync Errors
```python
class SyncError(Exception):
    def __init__(self, message: str, error_type: str, details: dict):
        self.message = message
        self.error_type = error_type
        self.details = details

class NetworkError(SyncError):
    def __init__(self, message: str, details: dict):
        super().__init__(message, "network", details)

class ConflictError(SyncError):
    def __init__(self, message: str, conflicts: List[Conflict]):
        super().__init__(message, "conflict", {"conflicts": conflicts})
```

### Error Recovery
```python
class ErrorHandler:
    def handle_error(self, error: SyncError):
        """Handle sync errors"""
        if error.error_type == "network":
            self.retry_with_backoff()
        elif error.error_type == "conflict":
            self.resolve_conflicts(error.details["conflicts"])
        elif error.error_type == "permission":
            self.request_permissions()
        else:
            self.log_error(error)
```

## Security

### Authentication
```python
class Authenticator:
    def authenticate(self, credentials: dict):
        """Authenticate with remote server"""
        # SSH key authentication
        # Username/password authentication
        # Token-based authentication
        pass

    def verify_permissions(self, permissions: dict):
        """Verify user permissions"""
        # Check read/write permissions
        # Check project access
        # Check role-based permissions
        pass
```

### Encryption
```python
class Encryptor:
    def encrypt_file(self, file_path: str, key: bytes):
        """Encrypt file for transmission"""
        # AES encryption
        # File compression
        # Integrity checking
        pass

    def decrypt_file(self, encrypted_data: bytes, key: bytes):
        """Decrypt received file"""
        # AES decryption
        # Integrity verification
        # File decompression
        pass
```

## Performance Optimization

### Incremental Sync
```python
class IncrementalSync:
    def get_changes(self, last_sync: datetime):
        """Get changes since last sync"""
        # Compare file timestamps
        # Compare file hashes
        # Identify new/modified files
        pass

    def sync_changes(self, changes: List[Change]):
        """Sync only changed files"""
        # Upload new files
        # Update modified files
        # Delete removed files
        pass
```

### Parallel Processing
```python
class ParallelProcessor:
    def sync_parallel(self, files: List[str]):
        """Sync files in parallel"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.sync_file, file) for file in files]
            results = [future.result() for future in futures]
        return results
```

## Monitoring and Logging

### Sync Monitoring
```python
class SyncMonitor:
    def monitor_sync(self, sync_id: str):
        """Monitor sync progress"""
        # Track file transfers
        # Monitor command execution
        # Report progress
        # Handle errors
        pass

    def log_sync_event(self, event: SyncEvent):
        """Log sync events"""
        # Log to file
        # Send to monitoring service
        # Generate alerts
        pass
```

### Metrics Collection
```python
class MetricsCollector:
    def collect_metrics(self, sync_session: SyncSession):
        """Collect sync metrics"""
        metrics = {
            "duration": sync_session.duration,
            "files_synced": sync_session.files_synced,
            "bytes_transferred": sync_session.bytes_transferred,
            "conflicts_resolved": sync_session.conflicts_resolved,
            "commands_executed": sync_session.commands_executed
        }
        return metrics
```

## Integration

### API Integration
```python
class SyncAPI:
    def start_sync(self, project_id: str):
        """Start sync via API"""
        # Validate project
        # Check permissions
        # Start sync process
        # Return sync ID
        pass

    def get_sync_status(self, sync_id: str):
        """Get sync status via API"""
        # Retrieve sync status
        # Return progress information
        pass
```

### Webhook Integration
```python
class WebhookNotifier:
    def notify_sync_complete(self, sync_result: SyncResult):
        """Notify via webhook when sync completes"""
        payload = {
            "event": "sync_complete",
            "project_id": sync_result.project_id,
            "sync_id": sync_result.sync_id,
            "status": sync_result.status,
            "timestamp": sync_result.timestamp
        }
        self.send_webhook(payload)
```
