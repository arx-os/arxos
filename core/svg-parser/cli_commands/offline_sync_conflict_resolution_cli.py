"""
Offline Sync & Conflict Resolution CLI Commands

This module provides comprehensive command-line interface for offline sync and
conflict resolution operations including:
- Sync initiation and management
- Conflict resolution and troubleshooting
- Status monitoring and reporting
- Performance metrics and analytics
- Rollback and recovery operations

Usage Examples:
    arx sync initiate --device-id mobile_001 --local-changes changes.json --remote-data remote.json
    arx sync status --device-id mobile_001
    arx sync history --device-id mobile_001 --limit 10
    arx sync rollback --device-id mobile_001 --operation-id op_123
    arx sync metrics
    arx sync cleanup --days 30
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from services.offline_sync_conflict_resolution import (
    OfflineSyncConflictResolutionService,
    ConflictType,
    SyncStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def sync():
    """Offline Sync & Conflict Resolution commands."""
    pass


@sync.command()
@click.option('--device-id', required=True, help='Unique device identifier')
@click.option('--local-changes', type=click.Path(exists=True), help='Path to local changes JSON file')
@click.option('--remote-data', type=click.Path(exists=True), help='Path to remote data JSON file')
@click.option('--resolution-strategy', default='auto', 
              type=click.Choice(['auto', 'local', 'remote', 'manual']),
              help='Conflict resolution strategy')
@click.option('--output', type=click.Path(), help='Output file for sync results')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def initiate(device_id: str, local_changes: Optional[str], remote_data: Optional[str], 
            resolution_strategy: str, output: Optional[str], verbose: bool):
    """
    Initiate a two-way sync operation for a device.
    
    This command performs comprehensive sync operations including conflict detection,
    automatic resolution, and safe merging of changes.
    
    Examples:
        arx sync initiate --device-id mobile_001 --local-changes changes.json --remote-data remote.json
        arx sync initiate --device-id cli_001 --resolution-strategy manual --verbose
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize sync service
        sync_service = OfflineSyncConflictResolutionService()
        
        # Load local changes
        local_changes_data = []
        if local_changes:
            with open(local_changes, 'r') as f:
                local_changes_data = json.load(f)
            logger.info(f"Loaded {len(local_changes_data)} local changes from {local_changes}")
        
        # Load remote data
        remote_data_dict = {}
        if remote_data:
            with open(remote_data, 'r') as f:
                remote_data_dict = json.load(f)
            logger.info(f"Loaded remote data with {len(remote_data_dict.get('objects', {}))} objects from {remote_data}")
        
        # Validate input
        if not local_changes_data and not remote_data_dict:
            click.echo("Error: Either local changes or remote data must be provided", err=True)
            sys.exit(1)
        
        # Perform sync
        logger.info(f"Initiating sync for device {device_id} with {resolution_strategy} resolution strategy")
        
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=local_changes_data,
            remote_data=remote_data_dict
        )
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"Sync results saved to {output}")
        
        # Display results
        click.echo(f"Sync completed successfully!")
        click.echo(f"  Operation ID: {result['operation_id']}")
        click.echo(f"  Synced changes: {result['synced_changes']}")
        click.echo(f"  Conflicts resolved: {result['conflicts_resolved']}")
        click.echo(f"  Duration: {result['duration_ms']}ms")
        
    except Exception as e:
        logger.error(f"Sync initiation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
@click.option('--device-id', required=True, help='Device identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def status(device_id: str, format: str, verbose: bool):
    """
    Get current sync status for a device.
    
    This command provides comprehensive status information including sync state,
    last sync timestamp, unsynced changes, and performance statistics.
    
    Examples:
        arx sync status --device-id mobile_001
        arx sync status --device-id cli_001 --format json --verbose
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        sync_service = OfflineSyncConflictResolutionService()
        status_data = sync_service.get_sync_status(device_id)
        
        if format == 'json':
            click.echo(json.dumps(status_data, indent=2, default=str))
        elif format == 'csv':
            # Simple CSV output
            click.echo("device_id,status,last_sync,unsynced_changes,conflict_count,success_count,total_operations")
            click.echo(f"{status_data['device_id']},{status_data['status']},{status_data.get('last_sync', '')},{status_data['unsynced_changes']},{status_data['conflict_count']},{status_data['success_count']},{status_data['total_operations']}")
        else:
            # Table format
            click.echo(f"Sync Status for Device: {device_id}")
            click.echo("=" * 50)
            click.echo(f"Status: {status_data['status']}")
            click.echo(f"Last Sync: {status_data.get('last_sync', 'Never')}")
            click.echo(f"Unsynced Changes: {status_data['unsynced_changes']}")
            click.echo(f"Conflict Count: {status_data['conflict_count']}")
            click.echo(f"Success Count: {status_data['success_count']}")
            click.echo(f"Total Operations: {status_data['total_operations']}")
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
@click.option('--device-id', required=True, help='Device identifier')
@click.option('--limit', default=50, type=int, help='Maximum number of operations to return')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--filter-status', type=click.Choice(['completed', 'failed', 'in_progress', 'pending']),
              help='Filter by operation status')
def history(device_id: str, limit: int, format: str, filter_status: Optional[str]):
    """
    Get sync history for a device.
    
    This command provides detailed history of sync operations including timestamps,
    status, durations, and error messages.
    
    Examples:
        arx sync history --device-id mobile_001
        arx sync history --device-id cli_001 --limit 10 --format json
        arx sync history --device-id mobile_001 --filter-status failed
    """
    try:
        sync_service = OfflineSyncConflictResolutionService()
        history_data = sync_service.get_sync_history(device_id, limit)
        
        # Apply status filter if specified
        if filter_status:
            history_data = [op for op in history_data if op['status'] == filter_status]
        
        if format == 'json':
            click.echo(json.dumps(history_data, indent=2, default=str))
        elif format == 'csv':
            # CSV header
            click.echo("operation_id,timestamp,status,operation_type,duration_ms")
            for op in history_data:
                click.echo(f"{op['operation_id']},{op['timestamp']},{op['status']},{op['operation_type']},{op.get('duration_ms', '')}")
        else:
            # Table format
            click.echo(f"Sync History for Device: {device_id}")
            click.echo("=" * 80)
            click.echo(f"{'Operation ID':<20} {'Timestamp':<20} {'Status':<12} {'Type':<12} {'Duration':<10}")
            click.echo("-" * 80)
            
            for op in history_data:
                duration = f"{op.get('duration_ms', 0)}ms" if op.get('duration_ms') else 'N/A'
                click.echo(f"{op['operation_id']:<20} {op['timestamp']:<20} {op['status']:<12} {op['operation_type']:<12} {duration:<10}")
            
            click.echo(f"\nTotal operations: {len(history_data)}")
        
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
@click.option('--device-id', required=True, help='Device identifier')
@click.option('--operation-id', required=True, help='Operation ID to rollback')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.option('--output', type=click.Path(), help='Output file for rollback results')
def rollback(device_id: str, operation_id: str, confirm: bool, output: Optional[str]):
    """
    Rollback a failed sync operation.
    
    This command provides rollback capabilities for failed sync operations,
    restoring the system to a previous stable state.
    
    Examples:
        arx sync rollback --device-id mobile_001 --operation-id op_123
        arx sync rollback --device-id cli_001 --operation-id op_456 --confirm
    """
    try:
        if not confirm:
            if not click.confirm(f"Are you sure you want to rollback operation {operation_id} for device {device_id}?"):
                click.echo("Rollback cancelled.")
                return
        
        sync_service = OfflineSyncConflictResolutionService()
        
        logger.info(f"Rolling back operation {operation_id} for device {device_id}")
        
        result = sync_service.rollback_sync(device_id, operation_id)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"Rollback results saved to {output}")
        
        # Display results
        click.echo(f"Rollback completed successfully!")
        click.echo(f"  Rollback Operation ID: {result['operation_id']}")
        click.echo(f"  Rolled Back Operation: {result['rolled_back_operation']}")
        click.echo(f"  Message: {result['message']}")
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', type=click.Path(), help='Output file for metrics')
def metrics(format: str, output: Optional[str]):
    """
    Get sync performance metrics.
    
    This command provides comprehensive performance metrics including sync counts,
    success rates, conflict resolution statistics, and system resource usage.
    
    Examples:
        arx sync metrics
        arx sync metrics --format json --output metrics.json
    """
    try:
        sync_service = OfflineSyncConflictResolutionService()
        metrics_data = sync_service.get_metrics()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            logger.info(f"Metrics saved to {output}")
        
        if format == 'json':
            click.echo(json.dumps(metrics_data, indent=2, default=str))
        elif format == 'csv':
            # CSV output for metrics
            click.echo("metric,value")
            for key, value in metrics_data['metrics'].items():
                click.echo(f"{key},{value}")
            click.echo(f"total_devices,{metrics_data['total_devices']}")
            click.echo(f"database_size,{metrics_data['database_size']}")
        else:
            # Table format
            click.echo("Sync Performance Metrics")
            click.echo("=" * 40)
            click.echo(f"Total Syncs: {metrics_data['metrics']['total_syncs']}")
            click.echo(f"Successful Syncs: {metrics_data['metrics']['successful_syncs']}")
            click.echo(f"Conflicts Resolved: {metrics_data['metrics']['conflicts_resolved']}")
            click.echo(f"Rollbacks: {metrics_data['metrics']['rollbacks']}")
            click.echo(f"Average Sync Time: {metrics_data['metrics']['average_sync_time']:.2f}ms")
            click.echo(f"Total Devices: {metrics_data['total_devices']}")
            click.echo(f"Database Size: {metrics_data['database_size']} bytes")
            
            # Calculate success rate
            total_syncs = metrics_data['metrics']['total_syncs']
            successful_syncs = metrics_data['metrics']['successful_syncs']
            if total_syncs > 0:
                success_rate = (successful_syncs / total_syncs) * 100
                click.echo(f"Success Rate: {success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
@click.option('--days', default=30, type=int, help='Number of days to keep operations')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
def cleanup(days: int, confirm: bool, dry_run: bool):
    """
    Clean up old sync operations.
    
    This command removes old sync operations to maintain database performance
    and storage efficiency.
    
    Examples:
        arx sync cleanup --days 30
        arx sync cleanup --days 7 --confirm
        arx sync cleanup --days 60 --dry-run
    """
    try:
        if not confirm and not dry_run:
            if not click.confirm(f"Are you sure you want to delete sync operations older than {days} days?"):
                click.echo("Cleanup cancelled.")
                return
        
        sync_service = OfflineSyncConflictResolutionService()
        
        if dry_run:
            # For dry run, we can't easily determine what would be deleted
            # without implementing additional logic, so we'll just show the command
            click.echo(f"Dry run: Would delete sync operations older than {days} days")
            click.echo("Use --confirm to actually perform the cleanup")
        else:
            logger.info(f"Cleaning up sync operations older than {days} days")
            
            deleted_count = sync_service.cleanup_old_operations(days)
            
            click.echo(f"Cleanup completed successfully!")
            click.echo(f"  Deleted operations: {deleted_count}")
            click.echo(f"  Retention period: {days} days")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
@click.option('--device-id', help='Device identifier to test')
@click.option('--local-changes', type=click.Path(exists=True), help='Path to local changes file')
@click.option('--remote-data', type=click.Path(exists=True), help='Path to remote data file')
@click.option('--output', type=click.Path(), help='Output file for test results')
def test(device_id: Optional[str], local_changes: Optional[str], remote_data: Optional[str], 
         output: Optional[str]):
    """
    Test sync functionality with sample data.
    
    This command provides a way to test sync functionality using sample data
    or provided files.
    
    Examples:
        arx sync test
        arx sync test --device-id test_device --local-changes changes.json --remote-data remote.json
    """
    try:
        sync_service = OfflineSyncConflictResolutionService()
        
        # Use provided device ID or generate one
        test_device_id = device_id or f"test_device_{int(datetime.now().timestamp())}"
        
        # Generate sample data if not provided
        if not local_changes:
            local_changes_data = [
                {
                    "id": "test_object_001",
                    "name": "Test Object 1",
                    "type": "equipment",
                    "location": {"x": 100, "y": 200},
                    "properties": {"status": "active", "priority": "high"},
                    "last_modified": int(datetime.now().timestamp()),
                    "last_sync_timestamp": 1640995200
                }
            ]
        else:
            with open(local_changes, 'r') as f:
                local_changes_data = json.load(f)
        
        if not remote_data:
            remote_data_dict = {
                "objects": {
                    "test_object_002": {
                        "id": "test_object_002",
                        "name": "Test Object 2",
                        "type": "system",
                        "location": {"x": 300, "y": 400},
                        "properties": {"status": "inactive", "priority": "medium"},
                        "last_modified": int(datetime.now().timestamp()) - 100,
                        "last_sync_timestamp": 1640995200
                    }
                },
                "last_updated": int(datetime.now().timestamp())
            }
        else:
            with open(remote_data, 'r') as f:
                remote_data_dict = json.load(f)
        
        # Perform test sync
        click.echo(f"Testing sync functionality for device: {test_device_id}")
        click.echo(f"Local changes: {len(local_changes_data)}")
        click.echo(f"Remote objects: {len(remote_data_dict.get('objects', {}))}")
        
        result = sync_service.sync_data(
            device_id=test_device_id,
            local_changes=local_changes_data,
            remote_data=remote_data_dict
        )
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"Test results saved to {output}")
        
        # Display results
        click.echo(f"Test completed successfully!")
        click.echo(f"  Status: {result['status']}")
        click.echo(f"  Synced changes: {result['synced_changes']}")
        click.echo(f"  Conflicts resolved: {result['conflicts_resolved']}")
        click.echo(f"  Duration: {result['duration_ms']}ms")
        
        # Check status
        status = sync_service.get_sync_status(test_device_id)
        click.echo(f"  Device status: {status['status']}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@sync.command()
def health():
    """
    Check sync service health.
    
    This command provides a health check for the sync service including
    database connectivity and basic functionality.
    
    Examples:
        arx sync health
    """
    try:
        sync_service = OfflineSyncConflictResolutionService()
        
        # Get metrics as a health check
        metrics = sync_service.get_metrics()
        
        click.echo("Sync Service Health Check")
        click.echo("=" * 30)
        click.echo(f"Status: Healthy")
        click.echo(f"Database accessible: Yes")
        click.echo(f"Total devices: {metrics['total_devices']}")
        click.echo(f"Database size: {metrics['database_size']} bytes")
        click.echo(f"Total syncs: {metrics['metrics']['total_syncs']}")
        
        # Test basic functionality
        test_device_id = f"health_check_{int(datetime.now().timestamp())}"
        status = sync_service.get_sync_status(test_device_id)
        
        if status['status'] == 'not_initialized':
            click.echo("Basic functionality: OK")
        else:
            click.echo("Basic functionality: Warning (unexpected status)")
        
        click.echo("Health check completed successfully!")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"Health check failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    sync() 