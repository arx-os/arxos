"""
Backup and Recovery Service for Arxos SVG-BIM Integration System.

This module provides comprehensive backup and recovery functionality for
the database, including automated backups, restore operations, and
backup verification.
"""

import os
import shutil
import sqlite3
import logging
import zipfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib

from utils.errors import BackupError, DatabaseError
from models.database import DatabaseConfig, get_db_manager

logger = logging.getLogger(__name__)


class BackupService:
    """Service for database backup and recovery operations."""
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 10):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, include_metadata: bool = True) -> str:
        """
        Create a complete database backup.
        
        Args:
            include_metadata: Whether to include backup metadata
            
        Returns:
            Path to the backup file
        """
        try:
            # Get database configuration
            config = DatabaseConfig.from_env()
            db_path = config.database_url.replace('sqlite:///', '')
            
            if db_path == ':memory:':
                raise BackupError("Cannot backup in-memory database")
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"arx_svg_parser_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            # Create metadata file
            if include_metadata:
                metadata = self._create_backup_metadata(backup_path, db_path)
                metadata_path = backup_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Create compressed backup
            compressed_backup_path = backup_path.with_suffix('.zip')
            self._create_compressed_backup(backup_path, compressed_backup_path, metadata if include_metadata else None)
            
            # Clean up uncompressed backup
            backup_path.unlink()
            if include_metadata:
                metadata_path.unlink()
            
            # Clean old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {compressed_backup_path}")
            return str(compressed_backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise BackupError(f"Failed to create backup: {e}") from e
    
    def restore_backup(self, backup_path: str, verify: bool = True) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to the backup file
            verify: Whether to verify the backup before restoring
            
        Returns:
            True if restore was successful
        """
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_path}")
            
            # Extract backup if it's compressed
            if backup_path.suffix == '.zip':
                extracted_path = self._extract_backup(backup_path)
            else:
                extracted_path = backup_path
            
            # Verify backup if requested
            if verify and not self._verify_backup(extracted_path):
                raise BackupError("Backup verification failed")
            
            # Get current database path
            config = DatabaseConfig.from_env()
            db_path = config.database_url.replace('sqlite:///', '')
            
            if db_path == ':memory:':
                raise BackupError("Cannot restore to in-memory database")
            
            # Create backup of current database
            current_backup = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(db_path):
                shutil.copy2(db_path, current_backup)
            
            # Restore database
            shutil.copy2(extracted_path, db_path)
            
            # Clean up extracted files
            if backup_path.suffix == '.zip':
                shutil.rmtree(extracted_path.parent)
            
            logger.info(f"Database restored successfully from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise BackupError(f"Failed to restore backup: {e}") from e
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        try:
            backups = []
            for backup_file in self.backup_dir.glob("*.zip"):
                metadata = self._get_backup_metadata(backup_file)
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': backup_file.stat().st_size,
                    'created_at': metadata.get('created_at'),
                    'database_version': metadata.get('database_version'),
                    'checksum': metadata.get('checksum')
                })
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'] or '', reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            raise BackupError(f"Failed to list backups: {e}") from e
    
    def verify_backup(self, backup_path: str) -> bool:
        """Verify the integrity of a backup file."""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_path}")
            
            # Extract backup if it's compressed
            if backup_path.suffix == '.zip':
                extracted_path = self._extract_backup(backup_path)
            else:
                extracted_path = backup_path
            
            # Verify backup
            is_valid = self._verify_backup(extracted_path)
            
            # Clean up extracted files
            if backup_path.suffix == '.zip':
                shutil.rmtree(extracted_path.parent)
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _create_backup_metadata(self, backup_path: Path, original_db_path: str) -> Dict[str, Any]:
        """Create metadata for the backup."""
        try:
            # Calculate checksum
            with open(backup_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            
            # Get database info
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get row counts
            table_counts = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            
            conn.close()
            
            return {
                'created_at': datetime.now().isoformat(),
                'original_database': original_db_path,
                'backup_size': backup_path.stat().st_size,
                'checksum': checksum,
                'database_version': '1.0',
                'tables': tables,
                'table_counts': table_counts,
                'backup_type': 'full'
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup metadata: {e}")
            return {
                'created_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _create_compressed_backup(self, backup_path: Path, compressed_path: Path, metadata: Optional[Dict[str, Any]] = None):
        """Create a compressed backup file."""
        with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database file
            zipf.write(backup_path, backup_path.name)
            
            # Add metadata if provided
            if metadata:
                metadata_path = backup_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                zipf.write(metadata_path, metadata_path.name)
    
    def _extract_backup(self, backup_path: Path) -> Path:
        """Extract a compressed backup file."""
        extract_dir = self.backup_dir / f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        # Find the database file
        db_files = list(extract_dir.glob("*.db"))
        if not db_files:
            raise BackupError("No database file found in backup")
        
        return db_files[0]
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """Verify the integrity of a backup file."""
        try:
            # Try to open the database
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Check if it's a valid SQLite database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            # Check for required tables
            required_tables = ['bim_models', 'symbol_library']
            existing_tables = [table[0] for table in tables]
            
            for required_table in required_tables:
                if required_table not in existing_tables:
                    logger.warning(f"Required table '{required_table}' not found in backup")
                    conn.close()
                    return False
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _get_backup_metadata(self, backup_path: Path) -> Dict[str, Any]:
        """Get metadata from a backup file."""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Look for metadata file
                metadata_files = [f for f in zipf.namelist() if f.endswith('.json')]
                if metadata_files:
                    with zipf.open(metadata_files[0]) as f:
                        return json.load(f)
            
            # Return basic metadata if no metadata file found
            return {
                'created_at': datetime.fromtimestamp(backup_path.stat().st_mtime).isoformat(),
                'size': backup_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup metadata: {e}")
            return {}
    
    def _cleanup_old_backups(self):
        """Remove old backups to stay within the limit."""
        try:
            backups = list(self.backup_dir.glob("*.zip"))
            if len(backups) <= self.max_backups:
                return
            
            # Sort by modification time (oldest first)
            backups.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest backups
            to_remove = backups[:-self.max_backups]
            for backup in to_remove:
                backup.unlink()
                logger.info(f"Removed old backup: {backup.name}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def create_scheduled_backup(self) -> str:
        """Create a scheduled backup (for cron jobs)."""
        try:
            # Check if backup is needed (e.g., daily backup)
            last_backup = self._get_last_backup_time()
            if last_backup and datetime.now() - last_backup < timedelta(hours=24):
                logger.info("Skipping backup - last backup was less than 24 hours ago")
                return ""
            
            return self.create_backup(include_metadata=True)
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
            raise BackupError(f"Scheduled backup failed: {e}") from e
    
    def _get_last_backup_time(self) -> Optional[datetime]:
        """Get the time of the last backup."""
        try:
            backups = self.list_backups()
            if not backups:
                return None
            
            # Get the most recent backup
            latest_backup = backups[0]
            created_at = latest_backup.get('created_at')
            if created_at:
                return datetime.fromisoformat(created_at)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last backup time: {e}")
            return None


def create_backup_service(backup_dir: str = "backups", max_backups: int = 10) -> BackupService:
    """Create a backup service instance."""
    return BackupService(backup_dir=backup_dir, max_backups=max_backups)


def backup_database(backup_dir: str = "backups") -> str:
    """Convenience function to backup the database."""
    service = create_backup_service(backup_dir)
    return service.create_backup()


def restore_database(backup_path: str, verify: bool = True) -> bool:
    """Convenience function to restore the database."""
    service = create_backup_service()
    return service.restore_backup(backup_path, verify) 