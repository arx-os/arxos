#!/usr/bin/env python3
"""
Smart Tagging Kits CLI Tool

Command-line interface for QR + BLE tag assignment, scanning, validation,
and management with offline capabilities.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.smart_tagging_kits import (
    SmartTaggingService, TagType, TagStatus, ScanResult
)
from utils.logger import get_logger

logger = get_logger(__name__)


class SmartTaggingCLI:
    """Command-line interface for Smart Tagging Kits management."""
    
    def __init__(self):
        self.service = SmartTaggingService()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for CLI operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def run(self, args: List[str] = None):
        """Main CLI entry point."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            if parsed_args.command == "assign":
                self.assign_tag(parsed_args)
            elif parsed_args.command == "scan":
                self.scan_tag(parsed_args)
            elif parsed_args.command == "resolve":
                self.resolve_tag(parsed_args)
            elif parsed_args.command == "validate":
                self.validate_tag(parsed_args)
            elif parsed_args.command == "history":
                self.get_tag_history(parsed_args)
            elif parsed_args.command == "update":
                self.update_tag(parsed_args)
            elif parsed_args.command == "remove":
                self.remove_tag(parsed_args)
            elif parsed_args.command == "inventory":
                self.get_inventory(parsed_args)
            elif parsed_args.command == "bulk-assign":
                self.bulk_assign(parsed_args)
            elif parsed_args.command == "export":
                self.export_data(parsed_args)
            elif parsed_args.command == "import":
                self.import_data(parsed_args)
            elif parsed_args.command == "analytics":
                self.get_analytics(parsed_args)
            elif parsed_args.command == "generate":
                self.generate_tag(parsed_args)
            elif parsed_args.command == "cleanup":
                self.cleanup_tags(parsed_args)
            elif parsed_args.command == "status":
                self.get_status(parsed_args)
            elif parsed_args.command == "health":
                self.health_check(parsed_args)
            else:
                parser.print_help()
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"CLI operation failed: {e}")
            sys.exit(1)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Smart Tagging Kits CLI Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  smart-tags assign --object-id obj_123 --tag-type qr --tag-data QR123456 --user-id user1 --device-id device1
  smart-tags scan --tag-data QR123456 --tag-type qr --user-id user1 --device-id device1
  smart-tags resolve --tag-data QR123456 --tag-type qr
  smart-tags validate --tag-data QR123456 --tag-type qr
  smart-tags history --tag-data QR123456
  smart-tags update --tag-data QR123456 --object-id obj_456 --user-id user1 --device-id device1
  smart-tags remove --tag-data QR123456 --user-id user1 --device-id device1
  smart-tags inventory --status assigned
  smart-tags bulk-assign --file assignments.json
  smart-tags export --format json
  smart-tags import --file tags.csv --format csv
  smart-tags analytics --period 30
  smart-tags generate --tag-type qr --prefix BUILDING
  smart-tags cleanup --days-old 90 --dry-run
  smart-tags status
  smart-tags health
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Assign command
        assign_parser = subparsers.add_parser("assign", help="Assign tag to object")
        assign_parser.add_argument("--object-id", required=True, help="Object ID to assign tag to")
        assign_parser.add_argument("--tag-type", required=True, choices=["qr", "ble", "hybrid"], help="Type of tag")
        assign_parser.add_argument("--tag-data", required=True, help="Tag data content")
        assign_parser.add_argument("--user-id", required=True, help="User performing the assignment")
        assign_parser.add_argument("--device-id", required=True, help="Device performing the assignment")
        assign_parser.add_argument("--metadata", help="Additional metadata JSON file")
        assign_parser.add_argument("--output", help="Output file for assignment results")
        
        # Scan command
        scan_parser = subparsers.add_parser("scan", help="Scan and resolve tag")
        scan_parser.add_argument("--tag-data", required=True, help="Tag data to scan")
        scan_parser.add_argument("--tag-type", required=True, choices=["qr", "ble", "hybrid"], help="Type of tag")
        scan_parser.add_argument("--user-id", required=True, help="User performing the scan")
        scan_parser.add_argument("--device-id", required=True, help="Device performing the scan")
        scan_parser.add_argument("--location", help="Location data JSON file")
        scan_parser.add_argument("--output", help="Output file for scan results")
        
        # Resolve command
        resolve_parser = subparsers.add_parser("resolve", help="Resolve tag offline")
        resolve_parser.add_argument("--tag-data", required=True, help="Tag data to resolve")
        resolve_parser.add_argument("--tag-type", required=True, choices=["qr", "ble", "hybrid"], help="Type of tag")
        resolve_parser.add_argument("--output", help="Output file for resolution results")
        
        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate tag format")
        validate_parser.add_argument("--tag-data", required=True, help="Tag data to validate")
        validate_parser.add_argument("--tag-type", required=True, choices=["qr", "ble", "hybrid"], help="Type of tag")
        validate_parser.add_argument("--output", help="Output file for validation results")
        
        # History command
        history_parser = subparsers.add_parser("history", help="Get tag history")
        history_parser.add_argument("--tag-data", required=True, help="Tag data to get history for")
        history_parser.add_argument("--output", help="Output file for history results")
        
        # Update command
        update_parser = subparsers.add_parser("update", help="Update tag mapping")
        update_parser.add_argument("--tag-data", required=True, help="Tag data to update")
        update_parser.add_argument("--object-id", required=True, help="New object ID to assign")
        update_parser.add_argument("--user-id", required=True, help="User performing the update")
        update_parser.add_argument("--device-id", required=True, help="Device performing the update")
        update_parser.add_argument("--metadata", help="Additional metadata JSON file")
        update_parser.add_argument("--output", help="Output file for update results")
        
        # Remove command
        remove_parser = subparsers.add_parser("remove", help="Remove tag assignment")
        remove_parser.add_argument("--tag-data", required=True, help="Tag data to remove assignment from")
        remove_parser.add_argument("--user-id", required=True, help="User performing the removal")
        remove_parser.add_argument("--device-id", required=True, help="Device performing the removal")
        remove_parser.add_argument("--output", help="Output file for removal results")
        
        # Inventory command
        inventory_parser = subparsers.add_parser("inventory", help="Get tag inventory")
        inventory_parser.add_argument("--status", help="Filter by tag status")
        inventory_parser.add_argument("--tag-type", help="Filter by tag type")
        inventory_parser.add_argument("--limit", type=int, default=100, help="Maximum number of results")
        inventory_parser.add_argument("--offset", type=int, default=0, help="Number of results to skip")
        inventory_parser.add_argument("--output", help="Output file for inventory results")
        
        # Bulk assign command
        bulk_parser = subparsers.add_parser("bulk-assign", help="Bulk assign tags")
        bulk_parser.add_argument("--file", required=True, help="JSON file with assignments")
        bulk_parser.add_argument("--output", help="Output file for bulk assignment results")
        
        # Export command
        export_parser = subparsers.add_parser("export", help="Export tag data")
        export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
        export_parser.add_argument("--output", help="Output file for exported data")
        
        # Import command
        import_parser = subparsers.add_parser("import", help="Import tag data")
        import_parser.add_argument("--file", required=True, help="File to import from")
        import_parser.add_argument("--format", required=True, choices=["json", "csv"], help="Import format")
        import_parser.add_argument("--output", help="Output file for import results")
        
        # Analytics command
        analytics_parser = subparsers.add_parser("analytics", help="Get tag analytics")
        analytics_parser.add_argument("--period", type=int, default=30, help="Analysis period in days")
        analytics_parser.add_argument("--output", help="Output file for analytics results")
        
        # Generate command
        generate_parser = subparsers.add_parser("generate", help="Generate new tag")
        generate_parser.add_argument("--tag-type", required=True, choices=["qr", "ble", "hybrid"], help="Type of tag to generate")
        generate_parser.add_argument("--prefix", help="Optional prefix for tag data")
        generate_parser.add_argument("--metadata", help="Additional metadata JSON file")
        generate_parser.add_argument("--output", help="Output file for generated tag")
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old tags")
        cleanup_parser.add_argument("--days-old", type=int, default=90, help="Remove tags older than specified days")
        cleanup_parser.add_argument("--dry-run", action="store_true", help="Perform dry run without actual deletion")
        cleanup_parser.add_argument("--output", help="Output file for cleanup results")
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Get service status")
        status_parser.add_argument("--detailed", action="store_true", help="Detailed status information")
        status_parser.add_argument("--output", help="Output file for status results")
        
        # Health command
        health_parser = subparsers.add_parser("health", help="Health check")
        health_parser.add_argument("--detailed", action="store_true", help="Detailed health information")
        health_parser.add_argument("--output", help="Output file for health check results")
        
        return parser
    
    def assign_tag(self, args):
        """Execute tag assignment."""
        print("��️  Assigning Tag to Object")
        print("=" * 40)
        
        # Load metadata if provided
        metadata = None
        if args.metadata:
            metadata = self._load_json_file(args.metadata, "Metadata file")
        
        # Perform assignment
        result = self.service.assign_tag(
            object_id=args.object_id,
            tag_type=TagType(args.tag_type),
            tag_data=args.tag_data,
            user_id=args.user_id,
            device_id=args.device_id,
            metadata=metadata
        )
        
        if result["success"]:
            print(f"✅ Tag assignment successful")
            print(f"   - Tag ID: {result['tag_id']}")
            print(f"   - Object ID: {result['object_id']}")
            print(f"   - Tag Type: {result['tag_type']}")
            print(f"   - Assigned At: {result['assigned_at']}")
            print(f"   - Message: {result['message']}")
        else:
            print(f"❌ Tag assignment failed: {result['error']}")
            sys.exit(1)
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag assignment completed!")
    
    def scan_tag(self, args):
        """Execute tag scanning."""
        print("🔍 Scanning Tag")
        print("=" * 40)
        
        # Load location data if provided
        location = None
        if args.location:
            location = self._load_json_file(args.location, "Location file")
        
        # Perform scan
        result = self.service.scan_tag(
            tag_data=args.tag_data,
            tag_type=TagType(args.tag_type),
            user_id=args.user_id,
            device_id=args.device_id,
            location=location
        )
        
        if result["success"]:
            print(f"✅ Tag scan successful")
            print(f"   - Result: {result['result']}")
            print(f"   - Object ID: {result['object_id']}")
            print(f"   - Tag ID: {result['tag_id']}")
            print(f"   - Tag Type: {result['tag_type']}")
            print(f"   - Scan Count: {result['scan_count']}")
            print(f"   - Response Time: {result['response_time']:.3f}s")
            
            if result.get('object_details'):
                details = result['object_details']
                print(f"   - Object Name: {details.get('name', 'N/A')}")
                print(f"   - Object Type: {details.get('type', 'N/A')}")
                print(f"   - Object Location: {details.get('location', 'N/A')}")
        else:
            print(f"❌ Tag scan failed: {result['error']}")
            print(f"   - Result: {result['result']}")
            print(f"   - Response Time: {result['response_time']:.3f}s")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag scanning completed!")
    
    def resolve_tag(self, args):
        """Execute tag resolution."""
        print("🔍 Resolving Tag (Offline)")
        print("=" * 40)
        
        # Perform resolution
        result = self.service.resolve_object(args.tag_data, TagType(args.tag_type))
        
        if result["success"]:
            print(f"✅ Tag resolution successful")
            print(f"   - Found: {result['found']}")
            if result['found']:
                print(f"   - Object ID: {result['object_id']}")
                print(f"   - Tag ID: {result['tag_id']}")
                print(f"   - Tag Type: {result['tag_type']}")
                print(f"   - Assigned At: {result['assigned_at']}")
                
                if result.get('object_details'):
                    details = result['object_details']
                    print(f"   - Object Name: {details.get('name', 'N/A')}")
                    print(f"   - Object Type: {details.get('type', 'N/A')}")
                    print(f"   - Object Location: {details.get('location', 'N/A')}")
            else:
                print(f"   - Error: {result['error']}")
        else:
            print(f"❌ Tag resolution failed: {result['error']}")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag resolution completed!")
    
    def validate_tag(self, args):
        """Execute tag validation."""
        print("✅ Validating Tag")
        print("=" * 40)
        
        # Perform validation
        result = self.service.validate_tag(args.tag_data, TagType(args.tag_type))
        
        if result["valid"]:
            print(f"✅ Tag validation successful")
            print(f"   - Tag Data: {args.tag_data}")
            print(f"   - Tag Type: {args.tag_type}")
            print(f"   - Message: {result['message']}")
        else:
            print(f"❌ Tag validation failed")
            print(f"   - Tag Data: {args.tag_data}")
            print(f"   - Tag Type: {args.tag_type}")
            print(f"   - Error: {result['error']}")
            
            if 'existing_tag_id' in result:
                print(f"   - Existing Tag ID: {result['existing_tag_id']}")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag validation completed!")
    
    def get_tag_history(self, args):
        """Get tag history."""
        print(f"📚 Tag History: {args.tag_data}")
        print("=" * 40)
        
        # Get history
        history = self.service.get_tag_history(args.tag_data)
        
        if history:
            print(f"📋 Found {len(history)} historical events")
            print()
            
            for i, event in enumerate(history, 1):
                print(f"  {i}. {event['event_type'].upper()}")
                print(f"     - Timestamp: {event['timestamp']}")
                print(f"     - User: {event['user_id']}")
                print(f"     - Device: {event['device_id']}")
                
                if event['event_type'] in ['assign', 'update', 'remove']:
                    print(f"     - Object ID: {event['details']['object_id']}")
                
                if event['event_type'] == 'scanned':
                    print(f"     - Result: {event['details']['result']}")
                    print(f"     - Response Time: {event['details']['response_time']:.3f}s")
                
                print()
        else:
            print("📭 No history found for this tag")
        
        # Save results if output specified
        if args.output:
            history_data = {
                "tag_data": args.tag_data,
                "history": history,
                "total_events": len(history)
            }
            self._save_json_file(args.output, history_data)
            print(f"💾 History saved to: {args.output}")
        
        print("🎉 Tag history retrieval completed!")
    
    def update_tag(self, args):
        """Update tag mapping."""
        print("🔄 Updating Tag Mapping")
        print("=" * 40)
        
        # Load metadata if provided
        metadata = None
        if args.metadata:
            metadata = self._load_json_file(args.metadata, "Metadata file")
        
        # Perform update
        success = self.service.update_tag_mapping(
            tag_data=args.tag_data,
            object_id=args.object_id,
            user_id=args.user_id,
            device_id=args.device_id,
            metadata=metadata
        )
        
        if success:
            print(f"✅ Tag mapping updated successfully")
            print(f"   - Tag Data: {args.tag_data}")
            print(f"   - New Object ID: {args.object_id}")
            print(f"   - Updated By: {args.user_id}")
            print(f"   - Device: {args.device_id}")
        else:
            print(f"❌ Tag mapping update failed")
            sys.exit(1)
        
        # Save results if output specified
        if args.output:
            result = {
                "success": success,
                "tag_data": args.tag_data,
                "object_id": args.object_id,
                "updated_at": datetime.now().isoformat()
            }
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag mapping update completed!")
    
    def remove_tag(self, args):
        """Remove tag assignment."""
        print("🗑️  Removing Tag Assignment")
        print("=" * 40)
        
        # Perform removal
        success = self.service.remove_tag_assignment(
            tag_data=args.tag_data,
            user_id=args.user_id,
            device_id=args.device_id
        )
        
        if success:
            print(f"✅ Tag assignment removed successfully")
            print(f"   - Tag Data: {args.tag_data}")
            print(f"   - Removed By: {args.user_id}")
            print(f"   - Device: {args.device_id}")
        else:
            print(f"❌ Tag assignment removal failed")
            sys.exit(1)
        
        # Save results if output specified
        if args.output:
            result = {
                "success": success,
                "tag_data": args.tag_data,
                "removed_at": datetime.now().isoformat()
            }
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag assignment removal completed!")
    
    def get_inventory(self, args):
        """Get tag inventory."""
        print("📋 Tag Inventory")
        print("=" * 40)
        
        # Get inventory from service
        all_tags = []
        for tag_id, tag_data in self.service.tag_database.items():
            tag_dict = {
                "tag_id": tag_data.tag_id,
                "tag_type": tag_data.tag_type.value,
                "tag_data": tag_data.tag_data,
                "object_id": tag_data.object_id,
                "status": tag_data.status.value,
                "created_at": tag_data.created_at.isoformat(),
                "assigned_at": tag_data.assigned_at.isoformat() if tag_data.assigned_at else None,
                "scan_count": tag_data.scan_count,
                "last_scan_at": tag_data.last_scan_at.isoformat() if tag_data.last_scan_at else None,
                "device_id": tag_data.device_id,
                "user_id": tag_data.user_id
            }
            
            # Apply filters
            if args.status and tag_data.status.value != args.status:
                continue
            if args.tag_type and tag_data.tag_type.value != args.tag_type:
                continue
            
            all_tags.append(tag_dict)
        
        # Apply pagination
        total_count = len(all_tags)
        paginated_results = all_tags[args.offset:args.offset + args.limit]
        
        print(f"📊 Inventory Summary:")
        print(f"  - Total Tags: {total_count}")
        print(f"  - Showing: {len(paginated_results)}")
        print(f"  - Limit: {args.limit}")
        print(f"  - Offset: {args.offset}")
        
        if args.status:
            print(f"  - Filtered by Status: {args.status}")
        if args.tag_type:
            print(f"  - Filtered by Type: {args.tag_type}")
        
        print(f"\n📋 Tag Details:")
        for i, tag in enumerate(paginated_results, 1):
            print(f"  {i}. {tag['tag_id']}")
            print(f"     - Type: {tag['tag_type']}")
            print(f"     - Data: {tag['tag_data']}")
            print(f"     - Status: {tag['status']}")
            print(f"     - Object: {tag['object_id'] or 'Unassigned'}")
            print(f"     - Scans: {tag['scan_count']}")
            print(f"     - Created: {tag['created_at']}")
            print()
        
        # Save results if output specified
        if args.output:
            inventory_data = {
                "tags": paginated_results,
                "total_count": total_count,
                "limit": args.limit,
                "offset": args.offset,
                "filters": {
                    "status": args.status,
                    "tag_type": args.tag_type
                }
            }
            self._save_json_file(args.output, inventory_data)
            print(f"💾 Inventory saved to: {args.output}")
        
        print("🎉 Tag inventory retrieval completed!")
    
    def bulk_assign(self, args):
        """Execute bulk tag assignment."""
        print("📦 Bulk Tag Assignment")
        print("=" * 40)
        
        # Load assignments from file
        assignments = self._load_json_file(args.file, "Assignments file")
        
        if not isinstance(assignments, list):
            print("❌ Assignments file must contain a list of assignments")
            sys.exit(1)
        
        print(f"📋 Processing {len(assignments)} assignments...")
        
        # Perform bulk assignment
        result = self.service.bulk_assign_tags(assignments)
        
        print(f"📊 Bulk Assignment Results:")
        print(f"  - Total: {result['total']}")
        print(f"  - Successful: {result['successful']}")
        print(f"  - Failed: {result['failed']}")
        print(f"  - Success Rate: {result['successful'] / result['total'] * 100:.1f}%")
        
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  - {error['tag_data']}: {error['error']}")
            if len(result['errors']) > 5:
                print(f"  ... and {len(result['errors']) - 5} more errors")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Bulk tag assignment completed!")
    
    def export_data(self, args):
        """Export tag data."""
        print(f"📤 Exporting Tag Data ({args.format.upper()})")
        print("=" * 40)
        
        # Perform export
        exported_data = self.service.export_tag_data(args.format)
        
        if exported_data:
            print(f"✅ Export successful")
            print(f"   - Format: {args.format.upper()}")
            print(f"   - Data Size: {len(exported_data)} characters")
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(exported_data)
                print(f"💾 Data saved to: {args.output}")
            else:
                print(f"📄 Exported Data:")
                print("-" * 20)
                print(exported_data[:500] + "..." if len(exported_data) > 500 else exported_data)
        else:
            print(f"❌ Export failed")
            sys.exit(1)
        
        print("🎉 Tag data export completed!")
    
    def import_data(self, args):
        """Import tag data."""
        print(f"📥 Importing Tag Data ({args.format.upper()})")
        print("=" * 40)
        
        # Load data from file
        with open(args.file, 'r') as f:
            data = f.read()
        
        print(f"📋 Importing from: {args.file}")
        print(f"   - Format: {args.format.upper()}")
        print(f"   - Data Size: {len(data)} characters")
        
        # Perform import
        result = self.service.import_tag_data(data, args.format)
        
        print(f"📊 Import Results:")
        print(f"  - Total: {result['total']}")
        print(f"  - Successful: {result['successful']}")
        print(f"  - Failed: {result['failed']}")
        print(f"  - Success Rate: {result['successful'] / result['total'] * 100:.1f}%")
        
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  - {error['tag_data']}: {error['error']}")
            if len(result['errors']) > 5:
                print(f"  ... and {len(result['errors']) - 5} more errors")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag data import completed!")
    
    def get_analytics(self, args):
        """Get tag analytics."""
        print(f"📊 Tag Analytics (Last {args.period} days)")
        print("=" * 40)
        
        # Get analytics
        analytics = self.service.get_analytics(args.period)
        
        if "error" in analytics:
            print(f"❌ Analytics generation failed: {analytics['error']}")
            sys.exit(1)
        
        print(f"📈 Analytics Summary:")
        print(f"  - Period: {analytics['period_days']} days")
        print(f"  - Total Tags: {analytics['total_tags']}")
        print(f"  - Assigned Tags: {analytics['assigned_tags']}")
        print(f"  - Unassigned Tags: {analytics['unassigned_tags']}")
        print(f"  - Assignment Rate: {analytics['assignment_rate']:.1%}")
        print(f"  - Total Scans: {analytics['total_scans']}")
        print(f"  - Successful Scans: {analytics['successful_scans']}")
        print(f"  - Scan Success Rate: {analytics['scan_success_rate']:.1%}")
        print(f"  - Avg Response Time: {analytics['avg_response_time']:.3f}s")
        print(f"  - Total Assignments: {analytics['total_assignments']}")
        
        if analytics['assignments_by_type']:
            print(f"\n📋 Assignments by Type:")
            for tag_type, count in analytics['assignments_by_type'].items():
                print(f"  - {tag_type.upper()}: {count}")
        
        if analytics['most_scanned_tags']:
            print(f"\n🏆 Most Scanned Tags:")
            for i, tag in enumerate(analytics['most_scanned_tags'][:5], 1):
                print(f"  {i}. {tag['tag_data']} ({tag['scan_count']} scans)")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, analytics)
            print(f"💾 Analytics saved to: {args.output}")
        
        print("🎉 Tag analytics generation completed!")
    
    def generate_tag(self, args):
        """Generate new tag."""
        print(f"🎲 Generating New Tag ({args.tag_type.upper()})")
        print("=" * 40)
        
        # Load metadata if provided
        metadata = None
        if args.metadata:
            metadata = self._load_json_file(args.metadata, "Metadata file")
        
        # Generate tag data
        import uuid
        import time
        
        tag_type_enum = TagType(args.tag_type)
        
        if tag_type_enum == TagType.QR:
            tag_data = f"{args.prefix or 'QR'}{int(time.time())}{uuid.uuid4().hex[:8]}"
        elif tag_type_enum == TagType.BLE:
            tag_data = uuid.uuid4().hex[:16]
        elif tag_type_enum == TagType.HYBRID:
            qr_part = f"{args.prefix or 'QR'}{int(time.time())}{uuid.uuid4().hex[:8]}"
            ble_part = uuid.uuid4().hex[:16]
            tag_data = f"{qr_part}:{ble_part}"
        else:
            print(f"❌ Unsupported tag type: {args.tag_type}")
            sys.exit(1)
        
        # Validate generated tag
        validation_result = self.service.validate_tag(tag_data, tag_type_enum)
        
        if validation_result["valid"]:
            print(f"✅ Tag generated successfully")
            print(f"   - Tag Data: {tag_data}")
            print(f"   - Tag Type: {args.tag_type.upper()}")
            print(f"   - Prefix: {args.prefix or 'None'}")
            print(f"   - Generated At: {datetime.now().isoformat()}")
        else:
            print(f"❌ Generated tag validation failed: {validation_result['error']}")
            sys.exit(1)
        
        # Save results if output specified
        if args.output:
            result = {
                "tag_data": tag_data,
                "tag_type": tag_type_enum.value,
                "generated_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self._save_json_file(args.output, result)
            print(f"💾 Generated tag saved to: {args.output}")
        
        print("🎉 Tag generation completed!")
    
    def cleanup_tags(self, args):
        """Clean up old tags."""
        print(f"🧹 Cleaning Up Old Tags (Older than {args.days_old} days)")
        print("=" * 40)
        
        # Find old unused tags
        cutoff_date = datetime.now() - timedelta(days=args.days_old)
        
        old_tags = []
        for tag in self.service.tag_database.values():
            if (tag.created_at < cutoff_date and 
                tag.status == TagStatus.UNASSIGNED and 
                tag.scan_count == 0):
                old_tags.append(tag)
        
        print(f"📋 Cleanup Summary:")
        print(f"  - Cutoff Date: {cutoff_date.isoformat()}")
        print(f"  - Tags to Remove: {len(old_tags)}")
        print(f"  - Dry Run: {args.dry_run}")
        
        if old_tags:
            print(f"\n📋 Tags to be removed:")
            for i, tag in enumerate(old_tags[:10], 1):
                print(f"  {i}. {tag.tag_data} ({tag.tag_type.value}) - Created: {tag.created_at.isoformat()}")
            if len(old_tags) > 10:
                print(f"  ... and {len(old_tags) - 10} more tags")
        
        if args.dry_run:
            print(f"\n🔍 This was a dry run - no tags were actually removed")
        else:
            if old_tags:
                print(f"\n🗑️  Removing {len(old_tags)} old unused tags...")
                removed_count = 0
                for tag in old_tags:
                    try:
                        del self.service.tag_database[tag.tag_id]
                        removed_count += 1
                    except Exception as e:
                        print(f"  ❌ Failed to remove tag {tag.tag_id}: {e}")
                
                print(f"✅ Successfully removed {removed_count} tags")
            else:
                print(f"✅ No old unused tags found")
        
        # Save results if output specified
        if args.output:
            result = {
                "dry_run": args.dry_run,
                "days_old": args.days_old,
                "cutoff_date": cutoff_date.isoformat(),
                "tags_to_remove": len(old_tags),
                "tags_removed": 0 if args.dry_run else len(old_tags),
                "message": f"{'Would remove' if args.dry_run else 'Removed'} {len(old_tags)} old unused tags"
            }
            self._save_json_file(args.output, result)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Tag cleanup completed!")
    
    def get_status(self, args):
        """Get service status."""
        print("📊 Smart Tagging Service Status")
        print("=" * 40)
        
        # Get status
        metrics = self.service.get_performance_metrics()
        
        if "error" in metrics:
            print(f"❌ Error: {metrics['error']}")
            sys.exit(1)
        
        print(f"📈 Performance Metrics:")
        print(f"  - Total Tags: {metrics['total_tags']}")
        print(f"  - Assigned Tags: {metrics['assigned_tags']}")
        print(f"  - Unassigned Tags: {metrics['unassigned_tags']}")
        print(f"  - Assignment Rate: {metrics['assignment_rate']:.1%}")
        print(f"  - Total Scans: {metrics['total_scans']}")
        print(f"  - Total Assignments: {metrics['total_assignments']}")
        print(f"  - Avg Response Time: {metrics['avg_response_time']:.3f}s")
        print(f"  - Cache Size: {metrics['cache_size']}")
        print(f"  - Database Size: {metrics['database_size']} bytes")
        
        if args.detailed:
            print(f"\n📋 Detailed Information:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  - {key}: {value:.3f}")
                else:
                    print(f"  - {key}: {value}")
        
        # Save results if output specified
        if args.output:
            status_data = {
                "service_status": "operational",
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
            self._save_json_file(args.output, status_data)
            print(f"💾 Status saved to: {args.output}")
        
        print("🎉 Status check completed!")
    
    def health_check(self, args):
        """Health check for tagging service."""
        print("🏥 Smart Tagging Service Health Check")
        print("=" * 40)
        
        # Check service health
        metrics = self.service.get_performance_metrics()
        
        if "error" in metrics:
            print("❌ Service Health: FAILED")
            print(f"   Error: {metrics['error']}")
            sys.exit(1)
        
        # Determine health status
        assignment_rate = metrics.get("assignment_rate", 0.0)
        avg_response_time = metrics.get("avg_response_time", 0.0)
        
        if assignment_rate >= 0.5 and avg_response_time < 1.0:
            health_status = "✅ HEALTHY"
        elif assignment_rate >= 0.3 and avg_response_time < 2.0:
            health_status = "⚠️  DEGRADED"
        else:
            health_status = "❌ UNHEALTHY"
        
        print(f"🏥 Health Status: {health_status}")
        print(f"\n📊 Health Metrics:")
        print(f"  - Assignment Rate: {assignment_rate:.1%}")
        print(f"  - Avg Response Time: {avg_response_time:.3f}s")
        print(f"  - Total Tags: {metrics['total_tags']}")
        print(f"  - Total Scans: {metrics['total_scans']}")
        print(f"  - Database Size: {metrics['database_size']} bytes")
        
        if args.detailed:
            print(f"\n📋 Detailed Health Information:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  - {key}: {value:.3f}")
                else:
                    print(f"  - {key}: {value}")
        
        # Save results if output specified
        if args.output:
            health_data = {
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "service": "Smart Tagging Kits"
            }
            self._save_json_file(args.output, health_data)
            print(f"💾 Health check results saved to: {args.output}")
        
        if health_status == "❌ UNHEALTHY":
            sys.exit(1)
        
        print("🎉 Health check completed!")
    
    # Helper methods
    
    def _load_json_file(self, file_path: str, description: str) -> Dict[str, Any]:
        """Load JSON file with error handling."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ {description} not found: {file_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {description}: {e}")
            sys.exit(1)
    
    def _save_json_file(self, file_path: str, data: Dict[str, Any]):
        """Save JSON file with error handling."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save file: {e}")


def main():
    """Main entry point for CLI."""
    cli = SmartTaggingCLI()
    cli.run()


if __name__ == "__main__":
    main() 