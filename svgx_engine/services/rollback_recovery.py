#!/usr/bin/env python3
"""
Pipeline Rollback and Recovery System

Provides comprehensive rollback and recovery capabilities for pipeline operations,
including state management, backup/restore, and conflict resolution.
"""

import json
import logging
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib
import threading
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BackupPoint:
    """Backup point data structure."""
    id: str
    timestamp: float
    description: str
    system: str
    backup_type: str  # "full", "incremental", "schema", "symbols", "behavior"
    file_path: str
    checksum: str
    metadata: Dict[str, Any]
    size_bytes: int


@dataclass
class RollbackOperation:
    """Rollback operation data structure."""
    id: str
    timestamp: float
    operation_type: str  # "rollback", "restore", "conflict_resolution"
    target_backup_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class PipelineRollbackRecovery:
    """Comprehensive rollback and recovery system for pipeline operations."""
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 50):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_db_path = self.backup_dir / "backup_registry.db"
        self.rollback_db_path = self.backup_dir / "rollback_operations.db"
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize databases
        self._init_backup_database()
        self._init_rollback_database()
        
        # Lock for concurrent operations
        self._lock = threading.RLock()
    
    def _init_backup_database(self):
        """Initialize backup registry database."""
        try:
            conn = sqlite3.connect(self.backup_db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_points (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    description TEXT NOT NULL,
                    system TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            logger.info("Backup database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize backup database: {e}")
    
    def _init_rollback_database(self):
        """Initialize rollback operations database."""
        try:
            conn = sqlite3.connect(self.rollback_db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rollback_operations (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    operation_type TEXT NOT NULL,
                    target_backup_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
            conn.close()
            logger.info("Rollback database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize rollback database: {e}")
    
    def create_backup(self, system: str, backup_type: str = "full", 
                     description: str = None) -> Optional[str]:
        """Create a backup of the current system state."""
        with self._lock:
            try:
                backup_id = f"{system}_{backup_type}_{int(time.time())}"
                timestamp = time.time()
                
                # Create backup file
                backup_file = self.backup_dir / f"{backup_id}.zip"
                
                # Determine what to backup based on type
                if backup_type == "full":
                    success = self._create_full_backup(system, backup_file)
                elif backup_type == "schema":
                    success = self._create_schema_backup(system, backup_file)
                elif backup_type == "symbols":
                    success = self._create_symbols_backup(system, backup_file)
                elif backup_type == "behavior":
                    success = self._create_behavior_backup(system, backup_file)
                else:
                    logger.error(f"Unknown backup type: {backup_type}")
                    return None
                
                if not success:
                    return None
                
                # Calculate checksum
                checksum = self._calculate_file_checksum(backup_file)
                size_bytes = backup_file.stat().st_size
                
                # Create backup point record
                backup_point = BackupPoint(
                    id=backup_id,
                    timestamp=timestamp,
                    description=description or f"{backup_type} backup of {system}",
                    system=system,
                    backup_type=backup_type,
                    file_path=str(backup_file),
                    checksum=checksum,
                    metadata={
                        "created_by": "pipeline_system",
                        "version": "1.0.0"
                    },
                    size_bytes=size_bytes
                )
                
                # Save to database
                self._save_backup_point(backup_point)
                
                # Cleanup old backups
                self._cleanup_old_backups(system)
                
                logger.info(f"Created {backup_type} backup for {system}: {backup_id}")
                return backup_id
                
            except Exception as e:
                logger.error(f"Failed to create backup for {system}: {e}")
                return None
    
    def _create_full_backup(self, system: str, backup_file: Path) -> bool:
        """Create a full backup of the system."""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup schema
                schema_dir = Path("schemas") / system
                if schema_dir.exists():
                    for file_path in schema_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"schemas/{system}/{file_path.relative_to(schema_dir)}")
                
                # Backup symbols
                symbols_dir = Path("arx-symbol-library") / system
                if symbols_dir.exists():
                    for file_path in symbols_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"arx-symbol-library/{system}/{file_path.relative_to(symbols_dir)}")
                
                # Backup behavior
                behavior_dir = Path("svgx_engine/behavior")
                if behavior_dir.exists():
                    for file_path in behavior_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"svgx_engine/behavior/{file_path.relative_to(behavior_dir)}")
                
                # Backup documentation
                docs_dir = Path("docs/systems") / system
                if docs_dir.exists():
                    for file_path in docs_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"docs/systems/{system}/{file_path.relative_to(docs_dir)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create full backup: {e}")
            return False
    
    def _create_schema_backup(self, system: str, backup_file: Path) -> bool:
        """Create a schema-only backup."""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                schema_dir = Path("schemas") / system
                if schema_dir.exists():
                    for file_path in schema_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"schemas/{system}/{file_path.relative_to(schema_dir)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create schema backup: {e}")
            return False
    
    def _create_symbols_backup(self, system: str, backup_file: Path) -> bool:
        """Create a symbols-only backup."""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                symbols_dir = Path("arx-symbol-library") / system
                if symbols_dir.exists():
                    for file_path in symbols_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"arx-symbol-library/{system}/{file_path.relative_to(symbols_dir)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create symbols backup: {e}")
            return False
    
    def _create_behavior_backup(self, system: str, backup_file: Path) -> bool:
        """Create a behavior-only backup."""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                behavior_dir = Path("svgx_engine/behavior")
                if behavior_dir.exists():
                    for file_path in behavior_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(file_path, f"svgx_engine/behavior/{file_path.relative_to(behavior_dir)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create behavior backup: {e}")
            return False
    
    def restore_backup(self, backup_id: str, conflict_resolution: str = "manual") -> bool:
        """Restore a backup."""
        with self._lock:
            try:
                # Get backup point
                backup_point = self._get_backup_point(backup_id)
                if not backup_point:
                    logger.error(f"Backup {backup_id} not found")
                    return False
                
                # Create rollback operation
                rollback_id = f"restore_{backup_id}_{int(time.time())}"
                rollback_op = RollbackOperation(
                    id=rollback_id,
                    timestamp=time.time(),
                    operation_type="restore",
                    target_backup_id=backup_id,
                    status="in_progress",
                    metadata={"conflict_resolution": conflict_resolution}
                )
                
                self._save_rollback_operation(rollback_op)
                
                # Check for conflicts
                conflicts = self._detect_conflicts(backup_point)
                if conflicts:
                    if conflict_resolution == "manual":
                        logger.warning(f"Conflicts detected during restore: {conflicts}")
                        rollback_op.status = "failed"
                        rollback_op.error_message = f"Conflicts detected: {conflicts}"
                        self._update_rollback_operation(rollback_op)
                        return False
                    else:
                        # Auto-resolve conflicts
                        self._resolve_conflicts(conflicts, backup_point)
                
                # Restore backup
                success = self._restore_backup_files(backup_point)
                
                if success:
                    rollback_op.status = "completed"
                    logger.info(f"Successfully restored backup {backup_id}")
                else:
                    rollback_op.status = "failed"
                    rollback_op.error_message = "Restore operation failed"
                    logger.error(f"Failed to restore backup {backup_id}")
                
                self._update_rollback_operation(rollback_op)
                return success
                
            except Exception as e:
                logger.error(f"Failed to restore backup {backup_id}: {e}")
                return False
    
    def _detect_conflicts(self, backup_point: BackupPoint) -> List[str]:
        """Detect conflicts between current state and backup."""
        conflicts = []
        
        try:
            with zipfile.ZipFile(backup_point.file_path, 'r') as zipf:
                for file_info in zipf.filelist:
                    file_path = Path(file_info.filename)
                    
                    # Check if file exists and has been modified
                    if file_path.exists():
                        current_mtime = file_path.stat().st_mtime
                        backup_mtime = file_info.date_time
                        backup_timestamp = time.mktime(backup_mtime + (0, 0, 0))
                        
                        if current_mtime > backup_timestamp:
                            conflicts.append(str(file_path))
        
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[str], backup_point: BackupPoint):
        """Auto-resolve conflicts by backing up current state first."""
        try:
            # Create backup of current state
            current_backup_id = self.create_backup(
                backup_point.system, 
                "incremental", 
                f"Auto-backup before restore of {backup_point.id}"
            )
            
            if current_backup_id:
                logger.info(f"Created auto-backup {current_backup_id} to resolve conflicts")
            
        except Exception as e:
            logger.error(f"Failed to resolve conflicts: {e}")
    
    def _restore_backup_files(self, backup_point: BackupPoint) -> bool:
        """Restore files from backup."""
        try:
            with zipfile.ZipFile(backup_point.file_path, 'r') as zipf:
                # Extract all files
                zipf.extractall(".")
            
            logger.info(f"Restored {backup_point.backup_type} backup for {backup_point.system}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup files: {e}")
            return False
    
    def list_backups(self, system: str = None) -> List[BackupPoint]:
        """List available backups."""
        try:
            conn = sqlite3.connect(self.backup_db_path)
            cursor = conn.cursor()
            
            if system:
                cursor.execute("""
                    SELECT id, timestamp, description, system, backup_type, 
                           file_path, checksum, metadata, size_bytes
                    FROM backup_points 
                    WHERE system = ? 
                    ORDER BY timestamp DESC
                """, (system,))
            else:
                cursor.execute("""
                    SELECT id, timestamp, description, system, backup_type, 
                           file_path, checksum, metadata, size_bytes
                    FROM backup_points 
                    ORDER BY timestamp DESC
                """)
            
            backups = []
            for row in cursor.fetchall():
                backup = BackupPoint(
                    id=row[0],
                    timestamp=row[1],
                    description=row[2],
                    system=row[3],
                    backup_type=row[4],
                    file_path=row[5],
                    checksum=row[6],
                    metadata=json.loads(row[7]),
                    size_bytes=row[8]
                )
                backups.append(backup)
            
            conn.close()
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupPoint]:
        """Get information about a specific backup."""
        return self._get_backup_point(backup_id)
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        with self._lock:
            try:
                backup_point = self._get_backup_point(backup_id)
                if not backup_point:
                    logger.error(f"Backup {backup_id} not found")
                    return False
                
                # Delete backup file
                backup_file = Path(backup_point.file_path)
                if backup_file.exists():
                    backup_file.unlink()
                
                # Delete from database
                conn = sqlite3.connect(self.backup_db_path)
                conn.execute("DELETE FROM backup_points WHERE id = ?", (backup_id,))
                conn.commit()
                conn.close()
                
                logger.info(f"Deleted backup {backup_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete backup {backup_id}: {e}")
                return False
    
    def _get_backup_point(self, backup_id: str) -> Optional[BackupPoint]:
        """Get backup point from database."""
        try:
            conn = sqlite3.connect(self.backup_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, description, system, backup_type, 
                       file_path, checksum, metadata, size_bytes
                FROM backup_points 
                WHERE id = ?
            """, (backup_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return BackupPoint(
                    id=row[0],
                    timestamp=row[1],
                    description=row[2],
                    system=row[3],
                    backup_type=row[4],
                    file_path=row[5],
                    checksum=row[6],
                    metadata=json.loads(row[7]),
                    size_bytes=row[8]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get backup point: {e}")
            return None
    
    def _save_backup_point(self, backup_point: BackupPoint):
        """Save backup point to database."""
        try:
            conn = sqlite3.connect(self.backup_db_path)
            conn.execute("""
                INSERT INTO backup_points 
                (id, timestamp, description, system, backup_type, file_path, checksum, metadata, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backup_point.id,
                backup_point.timestamp,
                backup_point.description,
                backup_point.system,
                backup_point.backup_type,
                backup_point.file_path,
                backup_point.checksum,
                json.dumps(backup_point.metadata),
                backup_point.size_bytes
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save backup point: {e}")
    
    def _save_rollback_operation(self, rollback_op: RollbackOperation):
        """Save rollback operation to database."""
        try:
            conn = sqlite3.connect(self.rollback_db_path)
            conn.execute("""
                INSERT INTO rollback_operations 
                (id, timestamp, operation_type, target_backup_id, status, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rollback_op.id,
                rollback_op.timestamp,
                rollback_op.operation_type,
                rollback_op.target_backup_id,
                rollback_op.status,
                rollback_op.error_message,
                json.dumps(rollback_op.metadata or {})
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save rollback operation: {e}")
    
    def _update_rollback_operation(self, rollback_op: RollbackOperation):
        """Update rollback operation in database."""
        try:
            conn = sqlite3.connect(self.rollback_db_path)
            conn.execute("""
                UPDATE rollback_operations 
                SET status = ?, error_message = ?, metadata = ?
                WHERE id = ?
            """, (
                rollback_op.status,
                rollback_op.error_message,
                json.dumps(rollback_op.metadata or {}),
                rollback_op.id
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update rollback operation: {e}")
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""
    
    def _cleanup_old_backups(self, system: str):
        """Clean up old backups to stay within limits."""
        try:
            backups = self.list_backups(system)
            if len(backups) > self.max_backups:
                # Sort by timestamp and remove oldest
                backups.sort(key=lambda x: x.timestamp)
                to_delete = backups[:-self.max_backups]
                
                for backup in to_delete:
                    self.delete_backup(backup.id)
                
                logger.info(f"Cleaned up {len(to_delete)} old backups for {system}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify the integrity of a backup."""
        try:
            backup_point = self._get_backup_point(backup_id)
            if not backup_point:
                return False
            
            backup_file = Path(backup_point.file_path)
            if not backup_file.exists():
                return False
            
            # Verify checksum
            current_checksum = self._calculate_file_checksum(backup_file)
            if current_checksum != backup_point.checksum:
                logger.error(f"Checksum mismatch for backup {backup_id}")
                return False
            
            # Verify zip file integrity
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                if zipf.testzip() is not None:
                    logger.error(f"Zip file corruption detected in backup {backup_id}")
                    return False
            
            logger.info(f"Backup {backup_id} integrity verified")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify backup integrity: {e}")
            return False
    
    def get_rollback_history(self, system: str = None) -> List[RollbackOperation]:
        """Get rollback operation history."""
        try:
            conn = sqlite3.connect(self.rollback_db_path)
            cursor = conn.cursor()
            
            if system:
                # Get rollback operations for a specific system
                cursor.execute("""
                    SELECT ro.id, ro.timestamp, ro.operation_type, ro.target_backup_id,
                           ro.status, ro.error_message, ro.metadata
                    FROM rollback_operations ro
                    JOIN backup_points bp ON ro.target_backup_id = bp.id
                    WHERE bp.system = ?
                    ORDER BY ro.timestamp DESC
                """, (system,))
            else:
                cursor.execute("""
                    SELECT id, timestamp, operation_type, target_backup_id,
                           status, error_message, metadata
                    FROM rollback_operations 
                    ORDER BY timestamp DESC
                """)
            
            operations = []
            for row in cursor.fetchall():
                operation = RollbackOperation(
                    id=row[0],
                    timestamp=row[1],
                    operation_type=row[2],
                    target_backup_id=row[3],
                    status=row[4],
                    error_message=row[5],
                    metadata=json.loads(row[6]) if row[6] else {}
                )
                operations.append(operation)
            
            conn.close()
            return operations
            
        except Exception as e:
            logger.error(f"Failed to get rollback history: {e}")
            return []


# Global rollback recovery instance
rollback_recovery = PipelineRollbackRecovery()


def get_rollback_recovery() -> PipelineRollbackRecovery:
    """Get the global rollback recovery instance."""
    return rollback_recovery


@contextmanager
def backup_context(system: str, description: str = None):
    """Context manager for automatic backup creation."""
    backup_id = None
    try:
        # Create backup before operation
        backup_id = rollback_recovery.create_backup(system, "full", description)
        yield backup_id
    except Exception as e:
        # If operation fails, we have a backup to restore from
        if backup_id:
            logger.warning(f"Operation failed, backup {backup_id} is available for restore")
        raise


if __name__ == "__main__":
    # Example usage
    rollback = PipelineRollbackRecovery()
    
    # Create a backup
    backup_id = rollback.create_backup("electrical", "full", "Test backup")
    print(f"Created backup: {backup_id}")
    
    # List backups
    backups = rollback.list_backups("electrical")
    for backup in backups:
        print(f"Backup: {backup.id} - {backup.description}")
    
    # Verify backup integrity
    if rollback.verify_backup_integrity(backup_id):
        print("Backup integrity verified")
    
    # Get rollback history
    history = rollback.get_rollback_history("electrical")
    for op in history:
        print(f"Operation: {op.id} - {op.status}") 