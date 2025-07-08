"""
Arxos CLI - Command Line Interface for Building Repository Management.

This module provides the main CLI interface for Arxos, implementing
infrastructure-as-code style commands for building management.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import yaml

from models.arxfile import ArxfileManager, ArxfileSchema, Permission, PermissionLevel
from services.version_control import VersionControlService
from services.access_control import AccessControlService
from services.bim_assembly import EnhancedBIMAssemblyService
from services.validation_framework import ValidationFramework
from utils.logger import get_logger

logger = get_logger(__name__)


class ArxCLI:
    """Main CLI class for Arxos building repository management."""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.arxfile_manager = ArxfileManager()
        self.version_control = None
        self.access_control = None
        self.bim_assembly = None
        self.validation = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='arx',
            description='Arxos - Building Repository Management CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  arx init building-001 "Downtown Office" commercial
  arx pull building-001
  arx commit -m "Updated electrical layout"
  arx merge feature-branch main
  arx rollback v1.2.0
  arx share user123 25.0
            """
        )
        
        # Global options
        parser.add_argument(
            '--config', '-c',
            default='arxfile.yaml',
            help='Path to arxfile.yaml (default: arxfile.yaml)'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress output except errors'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands'
        )
        
        # Init command
        init_parser = subparsers.add_parser(
            'init',
            help='Initialize a new building repository'
        )
        init_parser.add_argument(
            'building_id',
            help='Unique building identifier'
        )
        init_parser.add_argument(
            'building_name',
            help='Human-readable building name'
        )
        init_parser.add_argument(
            'building_type',
            help='Type of building (commercial, residential, etc.)'
        )
        init_parser.add_argument(
            '--address',
            nargs='+',
            help='Building address components'
        )
        init_parser.add_argument(
            '--owner',
            required=True,
            help='Building owner ID'
        )
        init_parser.add_argument(
            '--floors',
            type=int,
            default=1,
            help='Number of floors (default: 1)'
        )
        init_parser.add_argument(
            '--area',
            type=float,
            help='Total building area in square feet'
        )
        
        # Pull command
        pull_parser = subparsers.add_parser(
            'pull',
            help='Pull latest changes from building repository'
        )
        pull_parser.add_argument(
            'building_id',
            help='Building identifier'
        )
        pull_parser.add_argument(
            '--branch',
            default='main',
            help='Branch to pull from (default: main)'
        )
        pull_parser.add_argument(
            '--force',
            action='store_true',
            help='Force pull and overwrite local changes'
        )
        
        # Commit command
        commit_parser = subparsers.add_parser(
            'commit',
            help='Commit changes to building repository'
        )
        commit_parser.add_argument(
            '-m', '--message',
            required=True,
            help='Commit message'
        )
        commit_parser.add_argument(
            '--type',
            choices=['major', 'minor', 'patch'],
            default='patch',
            help='Version type (default: patch)'
        )
        commit_parser.add_argument(
            '--author',
            help='Commit author (default: current user)'
        )
        
        # Merge command
        merge_parser = subparsers.add_parser(
            'merge',
            help='Merge branches in building repository'
        )
        merge_parser.add_argument(
            'source_branch',
            help='Source branch to merge from'
        )
        merge_parser.add_argument(
            'target_branch',
            help='Target branch to merge into'
        )
        merge_parser.add_argument(
            '--no-ff',
            action='store_true',
            help='Create merge commit even if fast-forward possible'
        )
        
        # Rollback command
        rollback_parser = subparsers.add_parser(
            'rollback',
            help='Rollback to previous version'
        )
        rollback_parser.add_argument(
            'version',
            help='Version to rollback to'
        )
        rollback_parser.add_argument(
            '--force',
            action='store_true',
            help='Force rollback even if conflicts exist'
        )
        
        # Share command
        share_parser = subparsers.add_parser(
            'share',
            help='Share building repository with user'
        )
        share_parser.add_argument(
            'user_id',
            help='User ID to share with'
        )
        share_parser.add_argument(
            'percentage',
            type=float,
            help='Share percentage (0-100)'
        )
        share_parser.add_argument(
            '--type',
            choices=['equity', 'revenue', 'data', 'access'],
            default='access',
            help='Share type (default: access)'
        )
        share_parser.add_argument(
            '--expires',
            help='Expiration date (YYYY-MM-DD)'
        )
        
        # Status command
        status_parser = subparsers.add_parser(
            'status',
            help='Show building repository status'
        )
        status_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed status information'
        )
        
        # Log command
        log_parser = subparsers.add_parser(
            'log',
            help='Show commit history'
        )
        log_parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of commits to show (default: 10)'
        )
        log_parser.add_argument(
            '--branch',
            default='main',
            help='Branch to show log for (default: main)'
        )
        
        # Validate command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate building repository'
        )
        validate_parser.add_argument(
            '--level',
            choices=['basic', 'standard', 'comprehensive', 'compliance'],
            default='standard',
            help='Validation level (default: standard)'
        )
        validate_parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix validation issues where possible'
        )
        
        # Export command
        export_parser = subparsers.add_parser(
            'export',
            help='Export building data'
        )
        export_parser.add_argument(
            '--format',
            choices=['json', 'yaml', 'svg', 'ifc', 'gltf'],
            default='json',
            help='Export format (default: json)'
        )
        export_parser.add_argument(
            '--output',
            help='Output file path'
        )
        export_parser.add_argument(
            '--floors',
            nargs='+',
            help='Specific floors to export'
        )
        
        # Import command
        import_parser = subparsers.add_parser(
            'import',
            help='Import building data'
        )
        import_parser.add_argument(
            'file_path',
            help='File to import'
        )
        import_parser.add_argument(
            '--format',
            choices=['json', 'yaml', 'svg', 'ifc'],
            help='Import format (auto-detected if not specified)'
        )
        import_parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing data'
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        try:
            parsed_args = self.parser.parse_args(args)
            
            if not parsed_args.command:
                self.parser.print_help()
                return 1
            
            # Initialize services
            self._initialize_services(parsed_args.config)
            
            # Execute command
            command_method = getattr(self, f'cmd_{parsed_args.command}', None)
            if command_method:
                return command_method(parsed_args)
            else:
                logger.error(f"Unknown command: {parsed_args.command}")
                return 1
                
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            return 130
        except Exception as e:
            logger.error(f"CLI error: {e}")
            if parsed_args.verbose:
                raise
            return 1
    
    def _initialize_services(self, config_path: str):
        """Initialize service instances."""
        try:
            # Load arxfile if it exists
            if os.path.exists(config_path):
                self.arxfile_manager = ArxfileManager(config_path)
                self.arxfile_manager.load()
            
            # Initialize services
            self.version_control = VersionControlService()
            self.access_control = AccessControlService()
            self.bim_assembly = EnhancedBIMAssemblyService()
            self.validation = ValidationFramework()
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def cmd_init(self, args) -> int:
        """Initialize a new building repository."""
        try:
            # Parse address
            address = {}
            if args.address:
                # Simple address parsing - could be enhanced
                address = {
                    'street': ' '.join(args.address),
                    'city': '',
                    'state': '',
                    'zip': ''
                }
            
            # Create new arxfile
            schema = self.arxfile_manager.create_new(
                building_id=args.building_id,
                building_name=args.building_name,
                building_type=args.building_type,
                address=address,
                owner_id=args.owner,
                floor_count=args.floors
            )
            
            # Set additional properties
            if args.area:
                schema.total_area_sqft = args.area
            
            # Save arxfile
            self.arxfile_manager.save(schema)
            
            # Initialize version control
            self.version_control.initialize_repository(args.building_id)
            
            logger.info(f"Initialized building repository: {args.building_id}")
            logger.info(f"Arxfile created: {args.config}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            return 1
    
    def cmd_pull(self, args) -> int:
        """Pull latest changes from building repository."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Pull changes
            result = self.version_control.pull_changes(
                building_id=args.building_id,
                branch=args.branch,
                force=args.force
            )
            
            if result.get('success'):
                logger.info(f"Successfully pulled changes from {args.branch}")
                if result.get('changes'):
                    logger.info(f"Applied {len(result['changes'])} changes")
            else:
                logger.error(f"Failed to pull changes: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to pull changes: {e}")
            return 1
    
    def cmd_commit(self, args) -> int:
        """Commit changes to building repository."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Get current changes
            changes = self.version_control.get_pending_changes(
                building_id=self.arxfile_manager.schema.building_id
            )
            
            if not changes:
                logger.info("No changes to commit")
                return 0
            
            # Create commit
            result = self.version_control.create_version(
                data=changes,
                floor_id="all",  # Could be more specific
                building_id=self.arxfile_manager.schema.building_id,
                branch="main",
                message=args.message,
                version_type=args.type,
                created_by=args.author or "cli-user"
            )
            
            if result.get('success'):
                logger.info(f"Committed changes: {result.get('version_id')}")
            else:
                logger.error(f"Failed to commit: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return 1
    
    def cmd_merge(self, args) -> int:
        """Merge branches in building repository."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Create merge request
            result = self.version_control.create_merge_request(
                source_branch=args.source_branch,
                target_branch=args.target_branch,
                building_id=self.arxfile_manager.schema.building_id,
                created_by="cli-user",
                title=f"Merge {args.source_branch} into {args.target_branch}",
                description=f"CLI merge from {args.source_branch} to {args.target_branch}"
            )
            
            if result.get('success'):
                logger.info(f"Created merge request: {result.get('merge_request_id')}")
                
                # Auto-merge if no conflicts
                if not result.get('conflicts'):
                    merge_result = self.version_control.merge_request(
                        merge_request_id=result['merge_request_id'],
                        approved_by="cli-user"
                    )
                    
                    if merge_result.get('success'):
                        logger.info("Successfully merged branches")
                    else:
                        logger.error(f"Failed to merge: {merge_result.get('error')}")
                        return 1
                else:
                    logger.warning(f"Merge conflicts detected: {result['conflicts']}")
            else:
                logger.error(f"Failed to create merge request: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to merge branches: {e}")
            return 1
    
    def cmd_rollback(self, args) -> int:
        """Rollback to previous version."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Rollback to version
            result = self.version_control.rollback_to_version(
                building_id=self.arxfile_manager.schema.building_id,
                version_id=args.version,
                force=args.force
            )
            
            if result.get('success'):
                logger.info(f"Successfully rolled back to version: {args.version}")
            else:
                logger.error(f"Failed to rollback: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            return 1
    
    def cmd_share(self, args) -> int:
        """Share building repository with user."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Validate share percentage
            if args.percentage < 0 or args.percentage > 100:
                logger.error("Share percentage must be between 0 and 100")
                return 1
            
            # Check available shares
            available = self.arxfile_manager.schema.get_available_shares()
            if args.percentage > available:
                logger.error(f"Insufficient shares available. Only {available}% remaining")
                return 1
            
            # Add share
            from models.arxfile import ShareDistribution, ShareType
            share = ShareDistribution(
                contributor_id=args.user_id,
                share_type=ShareType(args.type),
                percentage=args.percentage,
                start_date=datetime.now()
            )
            
            self.arxfile_manager.schema.add_share(share)
            self.arxfile_manager.save()
            
            logger.info(f"Shared {args.percentage}% ({args.type}) with {args.user_id}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to share repository: {e}")
            return 1
    
    def cmd_status(self, args) -> int:
        """Show building repository status."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            schema = self.arxfile_manager.schema
            
            print(f"Building: {schema.building_name} ({schema.building_id})")
            print(f"Type: {schema.building_type}")
            print(f"Floors: {schema.floor_count}")
            print(f"Owner: {schema.owner_id}")
            print(f"License: {schema.license_status}")
            print(f"Last Modified: {schema.last_modified}")
            
            if args.detailed:
                print(f"\nShares: {schema.get_total_shares()}% allocated")
                print(f"Contracts: {len(schema.contracts)} active")
                print(f"Permissions: {len(schema.permissions)} granted")
                
                # Show recent commits
                commits = self.version_control.get_version_history(
                    floor_id="all",
                    building_id=schema.building_id,
                    limit=5
                )
                
                if commits.get('success') and commits.get('versions'):
                    print("\nRecent Commits:")
                    for commit in commits['versions'][:5]:
                        print(f"  {commit['version_id']}: {commit['message']}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to show status: {e}")
            return 1
    
    def cmd_log(self, args) -> int:
        """Show commit history."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Get commit history
            result = self.version_control.get_version_history(
                floor_id="all",
                building_id=self.arxfile_manager.schema.building_id,
                limit=args.limit
            )
            
            if result.get('success') and result.get('versions'):
                print(f"Commit History ({args.branch}):")
                for commit in result['versions']:
                    print(f"  {commit['version_id']} - {commit['created_at']}")
                    print(f"    {commit['message']}")
                    print(f"    Author: {commit['created_by']}")
                    print()
            else:
                logger.info("No commits found")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to show log: {e}")
            return 1
    
    def cmd_validate(self, args) -> int:
        """Validate building repository."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Validate arxfile
            issues = self.arxfile_manager.validate()
            
            if issues:
                logger.warning("Arxfile validation issues found:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("Arxfile validation passed")
            
            # Validate building data
            result = self.validation.validate_building(
                building_id=self.arxfile_manager.schema.building_id,
                level=args.level
            )
            
            if result.get('success'):
                validation_result = result.get('result', {})
                if validation_result.get('issues'):
                    logger.warning(f"Building validation issues found: {len(validation_result['issues'])}")
                    for issue in validation_result['issues']:
                        logger.warning(f"  - {issue}")
                else:
                    logger.info("Building validation passed")
            else:
                logger.error(f"Validation failed: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to validate: {e}")
            return 1
    
    def cmd_export(self, args) -> int:
        """Export building data."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Export building data
            result = self.bim_assembly.export_building(
                building_id=self.arxfile_manager.schema.building_id,
                format=args.format,
                floors=args.floors
            )
            
            if result.get('success'):
                output_path = args.output or f"building_export.{args.format}"
                
                with open(output_path, 'w') as f:
                    if args.format in ['json', 'yaml']:
                        f.write(result['data'])
                    else:
                        f.write(result['content'])
                
                logger.info(f"Exported building data to: {output_path}")
            else:
                logger.error(f"Export failed: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to export: {e}")
            return 1
    
    def cmd_import(self, args) -> int:
        """Import building data."""
        try:
            if not self.arxfile_manager.schema:
                logger.error("No arxfile.yaml found. Run 'arx init' first.")
                return 1
            
            # Import building data
            result = self.bim_assembly.import_building(
                file_path=args.file_path,
                format=args.format,
                building_id=self.arxfile_manager.schema.building_id,
                overwrite=args.overwrite
            )
            
            if result.get('success'):
                logger.info(f"Successfully imported: {args.file_path}")
                logger.info(f"Imported {result.get('object_count', 0)} objects")
            else:
                logger.error(f"Import failed: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to import: {e}")
            return 1


def main():
    """Main entry point for the CLI."""
    cli = ArxCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main()) 