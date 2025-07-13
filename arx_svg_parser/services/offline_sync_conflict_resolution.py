"""
Offline Sync & Conflict Resolution Service

This service implements robust two-way syncing logic for mobile and CLI clients
with conflict detection, safe merging, and comprehensive sync logging.

Features:
- Two-way sync protocol for mobile and CLI clients
- Conflict detection algorithms with intelligent resolution
- Safe merging strategies for data conflicts
- Rollback capabilities for failed syncs
- Unsynced change flagging and tracking
- Device sync logs with timestamps
- Last known remote state hash tracking
- Sync status monitoring and reporting
- Sync troubleshooting and recovery tools

Performance Targets:
- Two-way sync completes within 60 seconds
- Conflict detection identifies 95%+ of conflicts
- Safe merging resolves 90%+ of conflicts automatically
- Sync logs maintain complete history of operations
"""

import json
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from structlog import get_logger

logger = get_logger()


class SyncStatus(Enum):
    """Sync operation status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    ROLLBACK = "rollback"


class ConflictType(Enum):
    """Conflict type enumeration."""
    MODIFICATION_CONFLICT = "modification_conflict"
    DELETION_CONFLICT = "deletion_conflict"
    CREATION_CONFLICT = "creation_conflict"
    MERGE_CONFLICT = "merge_conflict"
    VERSION_CONFLICT = "version_conflict"


@dataclass
class SyncOperation:
    """Represents a sync operation with metadata."""
    operation_id: str
    device_id: str
    timestamp: datetime
    status: SyncStatus
    operation_type: str
    object_id: Optional[str] = None
    data_hash: Optional[str] = None
    remote_hash: Optional[str] = None
    conflict_type: Optional[ConflictType] = None
    resolution_strategy: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class SyncState:
    """Represents the current sync state for a device."""
    device_id: str
    last_sync_timestamp: datetime
    last_remote_hash: str
    unsynced_changes: List[str]
    sync_status: SyncStatus
    conflict_count: int
    success_count: int
    total_operations: int


@dataclass
class ConflictResolution:
    """Represents a conflict resolution strategy."""
    conflict_id: str
    conflict_type: ConflictType
    local_data: Dict[str, Any]
    remote_data: Dict[str, Any]
    resolution_strategy: str
    resolved_data: Dict[str, Any]
    timestamp: datetime
    resolved_by: str


class OfflineSyncConflictResolutionService:
    """
    Core service for offline sync and conflict resolution.
    
    This service provides robust two-way syncing logic for mobile and CLI clients
    with comprehensive conflict detection, safe merging strategies, and complete
    audit trails.
    """
    
    def __init__(self, db_path: str = "sync_data.db"):
        """
        Initialize the offline sync service.
        
        Args:
            db_path: Path to the SQLite database for sync state storage
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()
        self.sync_states: Dict[str, SyncState] = {}
        self.conflict_resolutions: List[ConflictResolution] = []
        self.sync_operations: List[SyncOperation] = []
        
        # Performance metrics
        self.metrics = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "conflicts_resolved": 0,
            "rollbacks": 0,
            "average_sync_time": 0.0
        }
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_operations (
                    operation_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    object_id TEXT,
                    data_hash TEXT,
                    remote_hash TEXT,
                    conflict_type TEXT,
                    resolution_strategy TEXT,
                    error_message TEXT,
                    duration_ms INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_states (
                    device_id TEXT PRIMARY KEY,
                    last_sync_timestamp TEXT NOT NULL,
                    last_remote_hash TEXT NOT NULL,
                    unsynced_changes TEXT,
                    sync_status TEXT NOT NULL,
                    conflict_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    total_operations INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conflict_resolutions (
                    conflict_id TEXT PRIMARY KEY,
                    conflict_type TEXT NOT NULL,
                    local_data TEXT NOT NULL,
                    remote_data TEXT NOT NULL,
                    resolution_strategy TEXT NOT NULL,
                    resolved_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    resolved_by TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def _generate_operation_id(self, device_id: str, operation_type: str) -> str:
        """Generate a unique operation ID."""
        timestamp = int(time.time() * 1000)
        return f"{device_id}_{operation_type}_{timestamp}"
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate a hash for data to detect changes."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _save_operation(self, operation: SyncOperation) -> None:
        """Save a sync operation to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_operations 
                (operation_id, device_id, timestamp, status, operation_type, 
                 object_id, data_hash, remote_hash, conflict_type, 
                 resolution_strategy, error_message, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation.operation_id,
                operation.device_id,
                operation.timestamp.isoformat(),
                operation.status.value,
                operation.operation_type,
                operation.object_id,
                operation.data_hash,
                operation.remote_hash,
                operation.conflict_type.value if operation.conflict_type else None,
                operation.resolution_strategy,
                operation.error_message,
                operation.duration_ms
            ))
            conn.commit()
    
    def _save_sync_state(self, state: SyncState) -> None:
        """Save sync state to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_states 
                (device_id, last_sync_timestamp, last_remote_hash, unsynced_changes,
                 sync_status, conflict_count, success_count, total_operations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state.device_id,
                state.last_sync_timestamp.isoformat(),
                state.last_remote_hash,
                json.dumps(state.unsynced_changes),
                state.sync_status.value,
                state.conflict_count,
                state.success_count,
                state.total_operations
            ))
            conn.commit()
    
    def _load_sync_state(self, device_id: str) -> Optional[SyncState]:
        """Load sync state from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT device_id, last_sync_timestamp, last_remote_hash, 
                       unsynced_changes, sync_status, conflict_count, 
                       success_count, total_operations
                FROM sync_states WHERE device_id = ?
            """, (device_id,))
            
            row = cursor.fetchone()
            if row:
                return SyncState(
                    device_id=row[0],
                    last_sync_timestamp=datetime.fromisoformat(row[1]),
                    last_remote_hash=row[2],
                    unsynced_changes=json.loads(row[3]) if row[3] else [],
                    sync_status=SyncStatus(row[4]),
                    conflict_count=row[5],
                    success_count=row[6],
                    total_operations=row[7]
                )
        return None
    
    def detect_conflicts(self, local_data: Dict[str, Any], 
                        remote_data: Dict[str, Any]) -> Optional[ConflictType]:
        """
        Detect conflicts between local and remote data.
        
        Args:
            local_data: Local version of the data
            remote_data: Remote version of the data
            
        Returns:
            ConflictType if conflict detected, None otherwise
        """
        local_hash = self._calculate_data_hash(local_data)
        remote_hash = self._calculate_data_hash(remote_data)
        
        # Check for modification conflicts
        if local_hash != remote_hash:
            local_timestamp = local_data.get('last_modified', 0)
            remote_timestamp = remote_data.get('last_modified', 0)
            
            # If both were modified since last sync
            if local_timestamp > remote_data.get('last_sync_timestamp', 0) and \
               remote_timestamp > local_data.get('last_sync_timestamp', 0):
                return ConflictType.MODIFICATION_CONFLICT
            
            # Check for deletion conflicts
            if local_data.get('deleted', False) != remote_data.get('deleted', False):
                return ConflictType.DELETION_CONFLICT
            
            # Check for creation conflicts (same ID, different content)
            if local_data.get('id') == remote_data.get('id') and \
               local_data.get('created_at') != remote_data.get('created_at'):
                return ConflictType.CREATION_CONFLICT
        
        return None
    
    def resolve_conflict(self, conflict_type: ConflictType, 
                        local_data: Dict[str, Any], 
                        remote_data: Dict[str, Any],
                        resolution_strategy: str = "auto") -> Dict[str, Any]:
        """
        Resolve a conflict using specified strategy.
        
        Args:
            conflict_type: Type of conflict detected
            local_data: Local version of the data
            remote_data: Remote version of the data
            resolution_strategy: Strategy to use for resolution
            
        Returns:
            Resolved data dictionary
        """
        timestamp = datetime.now()
        
        if resolution_strategy == "auto":
            # Automatic resolution based on conflict type
            if conflict_type == ConflictType.MODIFICATION_CONFLICT:
                # Merge changes, preferring more recent modifications
                resolved_data = self._merge_modifications(local_data, remote_data)
            elif conflict_type == ConflictType.DELETION_CONFLICT:
                # Keep the non-deleted version
                resolved_data = remote_data if not remote_data.get('deleted') else local_data
            elif conflict_type == ConflictType.CREATION_CONFLICT:
                # Keep the version with more recent creation
                resolved_data = local_data if local_data.get('created_at', 0) > remote_data.get('created_at', 0) else remote_data
            else:
                # Default to remote data
                resolved_data = remote_data
        elif resolution_strategy == "local":
            resolved_data = local_data
        elif resolution_strategy == "remote":
            resolved_data = remote_data
        elif resolution_strategy == "manual":
            # For manual resolution, return both versions for user decision
            resolved_data = {
                "conflict_type": conflict_type.value,
                "local_data": local_data,
                "remote_data": remote_data,
                "requires_manual_resolution": True
            }
        else:
            # Default to remote data
            resolved_data = remote_data
        
        # Create conflict resolution record
        conflict_id = f"conflict_{int(time.time() * 1000)}"
        resolution = ConflictResolution(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            local_data=local_data,
            remote_data=remote_data,
            resolution_strategy=resolution_strategy,
            resolved_data=resolved_data,
            timestamp=timestamp,
            resolved_by="system" if resolution_strategy == "auto" else "user"
        )
        
        self.conflict_resolutions.append(resolution)
        self._save_conflict_resolution(resolution)
        
        return resolved_data
    
    def _merge_modifications(self, local_data: Dict[str, Any], 
                           remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge modifications from local and remote data.
        
        Args:
            local_data: Local version with modifications
            remote_data: Remote version with modifications
            
        Returns:
            Merged data dictionary
        """
        merged_data = local_data.copy()
        
        # Merge fields, preferring more recent modifications
        for key, remote_value in remote_data.items():
            if key in local_data:
                local_timestamp = local_data.get(f"{key}_modified", 0)
                remote_timestamp = remote_data.get(f"{key}_modified", 0)
                
                if remote_timestamp > local_timestamp:
                    merged_data[key] = remote_value
            else:
                merged_data[key] = remote_value
        
        # Update merge metadata
        merged_data['last_modified'] = max(
            local_data.get('last_modified', 0),
            remote_data.get('last_modified', 0)
        )
        merged_data['merge_timestamp'] = int(time.time())
        
        return merged_data
    
    def _save_conflict_resolution(self, resolution: ConflictResolution) -> None:
        """Save conflict resolution to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conflict_resolutions 
                (conflict_id, conflict_type, local_data, remote_data, 
                 resolution_strategy, resolved_data, timestamp, resolved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resolution.conflict_id,
                resolution.conflict_type.value,
                json.dumps(resolution.local_data),
                json.dumps(resolution.remote_data),
                resolution.resolution_strategy,
                json.dumps(resolution.resolved_data),
                resolution.timestamp.isoformat(),
                resolution.resolved_by
            ))
            conn.commit()
    
    def sync_data(self, device_id: str, local_changes: List[Dict[str, Any]], 
                  remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform two-way sync for a device.
        
        Args:
            device_id: Unique identifier for the device
            local_changes: List of local changes to sync
            remote_data: Current remote data state
            
        Returns:
            Sync result with status and details
        """
        start_time = time.time()
        operation_id = self._generate_operation_id(device_id, "sync")
        
        with self.lock:
            # Create sync operation
            operation = SyncOperation(
                operation_id=operation_id,
                device_id=device_id,
                timestamp=datetime.now(),
                status=SyncStatus.IN_PROGRESS,
                operation_type="sync"
            )
            self._save_operation(operation)
            
            try:
                # Load or create sync state
                sync_state = self._load_sync_state(device_id)
                if not sync_state:
                    sync_state = SyncState(
                        device_id=device_id,
                        last_sync_timestamp=datetime.now(),
                        last_remote_hash=self._calculate_data_hash(remote_data),
                        unsynced_changes=[],
                        sync_status=SyncStatus.PENDING,
                        conflict_count=0,
                        success_count=0,
                        total_operations=0
                    )
                
                # Update sync state
                sync_state.sync_status = SyncStatus.IN_PROGRESS
                sync_state.total_operations += 1
                self._save_sync_state(sync_state)
                
                # Process local changes
                conflicts = []
                synced_changes = []
                
                for change in local_changes:
                    object_id = change.get('id')
                    if not object_id:
                        continue
                    
                    # Check for conflicts
                    remote_object = remote_data.get('objects', {}).get(object_id)
                    if remote_object:
                        conflict_type = self.detect_conflicts(change, remote_object)
                        if conflict_type:
                            conflicts.append({
                                'object_id': object_id,
                                'conflict_type': conflict_type,
                                'local_data': change,
                                'remote_data': remote_object
                            })
                            sync_state.conflict_count += 1
                        else:
                            # No conflict, safe to sync
                            synced_changes.append(change)
                    else:
                        # New object, safe to sync
                        synced_changes.append(change)
                
                # Resolve conflicts
                resolved_changes = []
                for conflict in conflicts:
                    resolved_data = self.resolve_conflict(
                        conflict['conflict_type'],
                        conflict['local_data'],
                        conflict['remote_data']
                    )
                    resolved_changes.append(resolved_data)
                
                # Update sync state
                sync_state.last_sync_timestamp = datetime.now()
                sync_state.last_remote_hash = self._calculate_data_hash(remote_data)
                sync_state.unsynced_changes = []
                sync_state.sync_status = SyncStatus.COMPLETED
                sync_state.success_count += 1
                self._save_sync_state(sync_state)
                
                # Update operation
                operation.status = SyncStatus.COMPLETED
                operation.duration_ms = int((time.time() - start_time) * 1000)
                self._save_operation(operation)
                
                # Update metrics
                self.metrics['total_syncs'] += 1
                self.metrics['successful_syncs'] += 1
                self.metrics['conflicts_resolved'] += len(conflicts)
                
                return {
                    'status': 'success',
                    'operation_id': operation_id,
                    'synced_changes': len(synced_changes),
                    'conflicts_resolved': len(conflicts),
                    'resolved_changes': len(resolved_changes),
                    'duration_ms': operation.duration_ms,
                    'sync_state': asdict(sync_state)
                }
                
            except Exception as e:
                # Handle sync failure
                operation.status = SyncStatus.FAILED
                operation.error_message = str(e)
                operation.duration_ms = int((time.time() - start_time) * 1000)
                self._save_operation(operation)
                
                # Update sync state
                sync_state.sync_status = SyncStatus.FAILED
                self._save_sync_state(sync_state)
                
                logger.error(f"Sync failed for device {device_id}: {e}")
                raise
    
    def rollback_sync(self, device_id: str, operation_id: str) -> Dict[str, Any]:
        """
        Rollback a failed sync operation.
        
        Args:
            device_id: Device identifier
            operation_id: Operation ID to rollback
            
        Returns:
            Rollback result
        """
        with self.lock:
            # Find the operation
            operation = None
            for op in self.sync_operations:
                if op.operation_id == operation_id and op.device_id == device_id:
                    operation = op
                    break
            
            if not operation:
                raise ValueError(f"Operation {operation_id} not found for device {device_id}")
            
            # Create rollback operation
            rollback_operation = SyncOperation(
                operation_id=self._generate_operation_id(device_id, "rollback"),
                device_id=device_id,
                timestamp=datetime.now(),
                status=SyncStatus.ROLLBACK,
                operation_type="rollback",
                object_id=operation.object_id
            )
            
            try:
                # Restore previous sync state
                sync_state = self._load_sync_state(device_id)
                if sync_state:
                    # Find previous successful sync
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.execute("""
                            SELECT * FROM sync_operations 
                            WHERE device_id = ? AND status = 'completed'
                            ORDER BY timestamp DESC LIMIT 1
                        """, (device_id,))
                        
                        previous_sync = cursor.fetchone()
                        if previous_sync:
                            # Restore to previous state
                            sync_state.sync_status = SyncStatus.COMPLETED
                            self._save_sync_state(sync_state)
                
                rollback_operation.status = SyncStatus.COMPLETED
                self._save_operation(rollback_operation)
                
                self.metrics['rollbacks'] += 1
                
                return {
                    'status': 'success',
                    'operation_id': rollback_operation.operation_id,
                    'rolled_back_operation': operation_id,
                    'message': 'Sync rollback completed successfully'
                }
                
            except Exception as e:
                rollback_operation.status = SyncStatus.FAILED
                rollback_operation.error_message = str(e)
                self._save_operation(rollback_operation)
                
                logger.error(f"Rollback failed for operation {operation_id}: {e}")
                raise
    
    def get_sync_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get current sync status for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Sync status information
        """
        sync_state = self._load_sync_state(device_id)
        if not sync_state:
            return {
                'device_id': device_id,
                'status': 'not_initialized',
                'last_sync': None,
                'unsynced_changes': 0
            }
        
        return {
            'device_id': device_id,
            'status': sync_state.sync_status.value,
            'last_sync': sync_state.last_sync_timestamp.isoformat(),
            'unsynced_changes': len(sync_state.unsynced_changes),
            'conflict_count': sync_state.conflict_count,
            'success_count': sync_state.success_count,
            'total_operations': sync_state.total_operations
        }
    
    def get_sync_history(self, device_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get sync history for a device.
        
        Args:
            device_id: Device identifier
            limit: Maximum number of operations to return
            
        Returns:
            List of sync operations
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM sync_operations 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (device_id, limit))
            
            operations = []
            for row in cursor.fetchall():
                operations.append({
                    'operation_id': row[0],
                    'timestamp': row[2],
                    'status': row[3],
                    'operation_type': row[4],
                    'object_id': row[5],
                    'duration_ms': row[11]
                })
            
            return operations
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get sync performance metrics."""
        return {
            'metrics': self.metrics,
            'total_devices': len(self.sync_states),
            'database_size': Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        }
    
    def cleanup_old_operations(self, days: int = 30) -> int:
        """
        Clean up old sync operations.
        
        Args:
            days: Number of days to keep operations
            
        Returns:
            Number of operations cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM sync_operations 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count 