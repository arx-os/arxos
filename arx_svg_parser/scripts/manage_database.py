#!/usr/bin/env python3
"""
Database Management Script for Arxos SVG-BIM Integration System.

This script provides command-line tools for database operations including:
- Running migrations
- Creating backups
- Restoring backups
- Database maintenance
- Health checks
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import init_database, close_database, get_db_manager
from services.backup_service import create_backup_service
from services.database_service import DatabaseService
from utils.logging_config import initialize_logging, get_logger
from utils.errors import DatabaseError, BackupError


def run_migrations():
    """Run database migrations."""
    try:
        logger.info("Running database migrations...")
        
        # Import and run Alembic
        from alembic import command
        from alembic.config import Config
        
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run upgrade
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def create_backup(backup_dir: str = "backups"):
    """Create a database backup."""
    try:
        logger.info("Creating database backup...")
        
        service = create_backup_service(backup_dir)
        backup_path = service.create_backup()
        
        logger.info(f"Backup created successfully: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


def restore_backup(backup_path: str, verify: bool = True):
    """Restore database from backup."""
    try:
        logger.info(f"Restoring database from backup: {backup_path}")
        
        service = create_backup_service()
        success = service.restore_backup(backup_path, verify)
        
        if success:
            logger.info("Database restored successfully")
            return True
        else:
            logger.error("Database restore failed")
            return False
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def list_backups(backup_dir: str = "backups"):
    """List available backups."""
    try:
        logger.info("Listing available backups...")
        
        service = create_backup_service(backup_dir)
        backups = service.list_backups()
        
        if not backups:
            print("No backups found.")
            return
        
        print(f"\nFound {len(backups)} backup(s):")
        print("-" * 80)
        
        for backup in backups:
            print(f"Filename: {backup['filename']}")
            print(f"Created: {backup['created_at']}")
            print(f"Size: {backup['size']:,} bytes")
            print(f"Database Version: {backup.get('database_version', 'Unknown')}")
            print("-" * 80)
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")


def verify_backup(backup_path: str):
    """Verify a backup file."""
    try:
        logger.info(f"Verifying backup: {backup_path}")
        
        service = create_backup_service()
        is_valid = service.verify_backup(backup_path)
        
        if is_valid:
            logger.info("Backup verification passed")
            print("✓ Backup verification passed")
        else:
            logger.error("Backup verification failed")
            print("✗ Backup verification failed")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        return False


def check_database_health():
    """Check database health and connectivity."""
    try:
        logger.info("Checking database health...")
        
        # Initialize database
        init_database()
        
        # Test database service
        db_service = DatabaseService()
        
        # Test basic operations
        models = db_service.list_bim_models()
        symbols = db_service.list_symbols()
        
        print("✓ Database connection successful")
        print(f"✓ Found {len(models)} BIM models")
        print(f"✓ Found {len(symbols)} symbols")
        print("✓ Database health check passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        print(f"✗ Database health check failed: {e}")
        return False


def reset_database():
    """Reset database (drop all tables and recreate)."""
    try:
        logger.info("Resetting database...")
        
        # Get database manager
        db_manager = get_db_manager()
        
        # Drop all tables
        from models.database import Base
        Base.metadata.drop_all(bind=db_manager.engine)
        
        # Recreate tables
        init_database()
        
        logger.info("Database reset completed successfully")
        print("✓ Database reset completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        print(f"✗ Database reset failed: {e}")
        return False


def show_database_info():
    """Show database information."""
    try:
        logger.info("Getting database information...")
        
        # Get database configuration
        from models.database import DatabaseConfig
        config = DatabaseConfig.from_env()
        
        print("Database Configuration:")
        print(f"  URL: {config.database_url}")
        print(f"  Pool Size: {config.pool_size}")
        print(f"  Max Overflow: {config.max_overflow}")
        print(f"  Pool Timeout: {config.pool_timeout}")
        print(f"  Pool Recycle: {config.pool_recycle}")
        print(f"  Echo: {config.echo}")
        
        # Test connection
        db_service = DatabaseService()
        models = db_service.list_bim_models()
        symbols = db_service.list_symbols()
        
        print(f"\nDatabase Statistics:")
        print(f"  BIM Models: {len(models)}")
        print(f"  Symbols: {len(symbols)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        print(f"✗ Failed to get database info: {e}")
        return False


def main():
    """Main function for database management."""
    parser = argparse.ArgumentParser(description="Database Management for Arxos SVG-BIM System")
    parser.add_argument("command", choices=[
        "migrate", "backup", "restore", "list-backups", "verify-backup",
        "health", "reset", "info"
    ], help="Command to execute")
    
    parser.add_argument("--backup-dir", default="backups", help="Backup directory")
    parser.add_argument("--backup-path", help="Path to backup file (for restore/verify)")
    parser.add_argument("--no-verify", action="store_true", help="Skip verification for restore")
    parser.add_argument("--force", action="store_true", help="Force operation without confirmation")
    
    args = parser.parse_args()
    
    # Initialize logging
    initialize_logging()
    global logger
    logger = get_logger(__name__)
    
    try:
        if args.command == "migrate":
            success = run_migrations()
            sys.exit(0 if success else 1)
        
        elif args.command == "backup":
            backup_path = create_backup(args.backup_dir)
            sys.exit(0 if backup_path else 1)
        
        elif args.command == "restore":
            if not args.backup_path:
                print("Error: --backup-path is required for restore command")
                sys.exit(1)
            
            if not args.force:
                response = input(f"Are you sure you want to restore from {args.backup_path}? This will overwrite the current database. (y/N): ")
                if response.lower() != 'y':
                    print("Restore cancelled")
                    sys.exit(0)
            
            success = restore_backup(args.backup_path, not args.no_verify)
            sys.exit(0 if success else 1)
        
        elif args.command == "list-backups":
            list_backups(args.backup_dir)
            sys.exit(0)
        
        elif args.command == "verify-backup":
            if not args.backup_path:
                print("Error: --backup-path is required for verify-backup command")
                sys.exit(1)
            
            success = verify_backup(args.backup_path)
            sys.exit(0 if success else 1)
        
        elif args.command == "health":
            success = check_database_health()
            sys.exit(0 if success else 1)
        
        elif args.command == "reset":
            if not args.force:
                response = input("Are you sure you want to reset the database? This will delete all data. (y/N): ")
                if response.lower() != 'y':
                    print("Reset cancelled")
                    sys.exit(0)
            
            success = reset_database()
            sys.exit(0 if success else 1)
        
        elif args.command == "info":
            success = show_database_info()
            sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        close_database()


if __name__ == "__main__":
    main() 