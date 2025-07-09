#!/usr/bin/env python3
"""
Data API Structuring CLI Tool

Command-line interface for structured JSON endpoints with system object lists,
filtering, pagination, contributor attribution, and data anonymization.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.data_api_structuring import (
    DataAPIStructuringService, QueryFilter, ObjectType, ObjectStatus, 
    ObjectCondition, ContributorRole
)
from utils.logger import get_logger

logger = get_logger(__name__)


class DataAPIStructuringCLI:
    """Command-line interface for Data API Structuring management."""
    
    def __init__(self):
        self.service = DataAPIStructuringService()
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
            if parsed_args.command == "query":
                self.query_objects(parsed_args)
            elif parsed_args.command == "get":
                self.get_object(parsed_args)
            elif parsed_args.command == "contributor":
                self.get_objects_by_contributor(parsed_args)
            elif parsed_args.command == "summary":
                self.get_system_summary(parsed_args)
            elif parsed_args.command == "analytics":
                self.get_analytics(parsed_args)
            elif parsed_args.command == "export":
                self.export_objects(parsed_args)
            elif parsed_args.command == "filters":
                self.get_filters(parsed_args)
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
            description="Data API Structuring CLI Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  data-api query --object-type mechanical --status active --page 1 --page-size 50
  data-api get --object-id obj_0001
  data-api contributor --contributor-id contrib_001 --page 1 --page-size 20
  data-api summary
  data-api analytics --days 30
  data-api export --format json --output objects.json
  data-api filters --type object-types
  data-api status
  data-api health
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Query command
        query_parser = subparsers.add_parser("query", help="Query system objects")
        query_parser.add_argument("--object-type", help="Filter by object type")
        query_parser.add_argument("--status", help="Filter by status")
        query_parser.add_argument("--condition", help="Filter by condition")
        query_parser.add_argument("--contributor-id", help="Filter by contributor ID")
        query_parser.add_argument("--date-from", help="Filter by installation date from (ISO format)")
        query_parser.add_argument("--date-to", help="Filter by installation date to (ISO format)")
        query_parser.add_argument("--page", type=int, default=1, help="Page number")
        query_parser.add_argument("--page-size", type=int, default=50, help="Page size")
        query_parser.add_argument("--sort-by", default="created_at", help="Sort by field")
        query_parser.add_argument("--sort-order", default="desc", help="Sort order (asc/desc)")
        query_parser.add_argument("--user-id", help="User ID for access control")
        query_parser.add_argument("--user-license-level", default="basic", help="User license level")
        query_parser.add_argument("--output", help="Output file for results")
        
        # Get object command
        get_parser = subparsers.add_parser("get", help="Get specific object")
        get_parser.add_argument("--object-id", required=True, help="Object ID to retrieve")
        get_parser.add_argument("--user-id", help="User ID for access control")
        get_parser.add_argument("--user-license-level", default="basic", help="User license level")
        get_parser.add_argument("--output", help="Output file for results")
        
        # Contributor command
        contributor_parser = subparsers.add_parser("contributor", help="Get objects by contributor")
        contributor_parser.add_argument("--contributor-id", required=True, help="Contributor ID")
        contributor_parser.add_argument("--object-type", help="Filter by object type")
        contributor_parser.add_argument("--status", help="Filter by status")
        contributor_parser.add_argument("--condition", help="Filter by condition")
        contributor_parser.add_argument("--date-from", help="Filter by installation date from (ISO format)")
        contributor_parser.add_argument("--date-to", help="Filter by installation date to (ISO format)")
        contributor_parser.add_argument("--page", type=int, default=1, help="Page number")
        contributor_parser.add_argument("--page-size", type=int, default=50, help="Page size")
        contributor_parser.add_argument("--user-id", help="User ID for access control")
        contributor_parser.add_argument("--user-license-level", default="basic", help="User license level")
        contributor_parser.add_argument("--output", help="Output file for results")
        
        # Summary command
        summary_parser = subparsers.add_parser("summary", help="Get system summary")
        summary_parser.add_argument("--user-id", help="User ID for access control")
        summary_parser.add_argument("--user-license-level", default="basic", help="User license level")
        summary_parser.add_argument("--output", help="Output file for results")
        
        # Analytics command
        analytics_parser = subparsers.add_parser("analytics", help="Get access analytics")
        analytics_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
        analytics_parser.add_argument("--output", help="Output file for results")
        
        # Export command
        export_parser = subparsers.add_parser("export", help="Export objects")
        export_parser.add_argument("--object-type", help="Filter by object type")
        export_parser.add_argument("--status", help="Filter by status")
        export_parser.add_argument("--condition", help="Filter by condition")
        export_parser.add_argument("--contributor-id", help="Filter by contributor ID")
        export_parser.add_argument("--date-from", help="Filter by installation date from (ISO format)")
        export_parser.add_argument("--date-to", help="Filter by installation date to (ISO format)")
        export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
        export_parser.add_argument("--user-id", help="User ID for access control")
        export_parser.add_argument("--user-license-level", default="basic", help="User license level")
        export_parser.add_argument("--output", help="Output file for exported data")
        
        # Filters command
        filters_parser = subparsers.add_parser("filters", help="Get available filters")
        filters_parser.add_argument("--type", choices=["object-types", "statuses", "conditions", "contributors"], 
                                  help="Type of filters to get")
        filters_parser.add_argument("--output", help="Output file for results")
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Get service status")
        status_parser.add_argument("--detailed", action="store_true", help="Detailed status information")
        status_parser.add_argument("--output", help="Output file for results")
        
        # Health command
        health_parser = subparsers.add_parser("health", help="Health check")
        health_parser.add_argument("--detailed", action="store_true", help="Detailed health information")
        health_parser.add_argument("--output", help="Output file for results")
        
        return parser
    
    def query_objects(self, args):
        """Execute object query."""
        print("🔍 Querying System Objects")
        print("=" * 40)
        
        # Build filters
        filters = QueryFilter()
        
        if args.object_type:
            try:
                filters.object_type = ObjectType(args.object_type.lower())
            except ValueError:
                print(f"❌ Invalid object type: {args.object_type}")
                sys.exit(1)
        
        if args.status:
            try:
                filters.status = ObjectStatus(args.status.lower())
            except ValueError:
                print(f"❌ Invalid status: {args.status}")
                sys.exit(1)
        
        if args.condition:
            try:
                filters.condition = ObjectCondition(args.condition.lower())
            except ValueError:
                print(f"❌ Invalid condition: {args.condition}")
                sys.exit(1)
        
        if args.contributor_id:
            filters.contributor_id = args.contributor_id
        
        if args.date_from:
            try:
                from datetime import datetime
                filters.date_from = datetime.fromisoformat(args.date_from)
            except ValueError:
                print(f"❌ Invalid date_from format: {args.date_from}")
                sys.exit(1)
        
        if args.date_to:
            try:
                from datetime import datetime
                filters.date_to = datetime.fromisoformat(args.date_to)
            except ValueError:
                print(f"❌ Invalid date_to format: {args.date_to}")
                sys.exit(1)
        
        # Execute query
        result = self.service.query_system_objects(
            filters=filters,
            page=args.page,
            page_size=args.page_size,
            sort_by=args.sort_by,
            sort_order=args.sort_order,
            user_id=args.user_id,
            user_license_level=args.user_license_level
        )
        
        print(f"📊 Query Results:")
        print(f"  - Total Objects: {result.pagination.total_count}")
        print(f"  - Page: {result.pagination.page} of {result.pagination.total_pages}")
        print(f"  - Objects Returned: {len(result.objects)}")
        print(f"  - Anonymized: {result.anonymized_count}")
        print(f"  - Query Time: {result.query_time:.3f}s")
        
        if result.objects:
            print(f"\n📋 Object Details:")
            for i, obj in enumerate(result.objects[:5], 1):
                print(f"  {i}. {obj.object_id} - {obj.name}")
                print(f"     - Type: {obj.object_type.value}")
                print(f"     - Status: {obj.status.value}")
                print(f"     - Condition: {obj.condition.value}")
                print(f"     - Contributor: {obj.contributor_name}")
                print()
            
            if len(result.objects) > 5:
                print(f"  ... and {len(result.objects) - 5} more objects")
        
        # Save results if output specified
        if args.output:
            result_data = {
                "objects": [asdict(obj) for obj in result.objects],
                "pagination": asdict(result.pagination),
                "filters_applied": result.filters_applied,
                "query_time": result.query_time,
                "anonymized_count": result.anonymized_count
            }
            self._save_json_file(args.output, result_data)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Object query completed!")
    
    def get_object(self, args):
        """Get specific object."""
        print(f"📋 Getting Object: {args.object_id}")
        print("=" * 40)
        
        obj = self.service.get_system_object(
            object_id=args.object_id,
            user_id=args.user_id,
            user_license_level=args.user_license_level
        )
        
        if not obj:
            print(f"❌ Object {args.object_id} not found")
            sys.exit(1)
        
        print(f"✅ Object Retrieved:")
        print(f"  - ID: {obj.object_id}")
        print(f"  - Name: {obj.name}")
        print(f"  - Type: {obj.object_type.value}")
        print(f"  - Status: {obj.status.value}")
        print(f"  - Condition: {obj.condition.value}")
        print(f"  - Installation Date: {obj.installation_date.isoformat()}")
        print(f"  - Contributor: {obj.contributor_name}")
        print(f"  - Location: {obj.location}")
        
        if obj.last_maintenance_date:
            print(f"  - Last Maintenance: {obj.last_maintenance_date.isoformat()}")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, asdict(obj))
            print(f"💾 Object details saved to: {args.output}")
        
        print("🎉 Object retrieval completed!")
    
    def get_objects_by_contributor(self, args):
        """Get objects by contributor."""
        print(f"👤 Getting Objects by Contributor: {args.contributor_id}")
        print("=" * 40)
        
        # Build filters
        filters = QueryFilter()
        
        if args.object_type:
            try:
                filters.object_type = ObjectType(args.object_type.lower())
            except ValueError:
                print(f"❌ Invalid object type: {args.object_type}")
                sys.exit(1)
        
        if args.status:
            try:
                filters.status = ObjectStatus(args.status.lower())
            except ValueError:
                print(f"❌ Invalid status: {args.status}")
                sys.exit(1)
        
        if args.condition:
            try:
                filters.condition = ObjectCondition(args.condition.lower())
            except ValueError:
                print(f"❌ Invalid condition: {args.condition}")
                sys.exit(1)
        
        if args.date_from:
            try:
                from datetime import datetime
                filters.date_from = datetime.fromisoformat(args.date_from)
            except ValueError:
                print(f"❌ Invalid date_from format: {args.date_from}")
                sys.exit(1)
        
        if args.date_to:
            try:
                from datetime import datetime
                filters.date_to = datetime.fromisoformat(args.date_to)
            except ValueError:
                print(f"❌ Invalid date_to format: {args.date_to}")
                sys.exit(1)
        
        # Execute query
        result = self.service.get_objects_by_contributor(
            contributor_id=args.contributor_id,
            filters=filters,
            page=args.page,
            page_size=args.page_size,
            user_id=args.user_id,
            user_license_level=args.user_license_level
        )
        
        print(f"📊 Contributor Objects:")
        print(f"  - Contributor ID: {args.contributor_id}")
        print(f"  - Total Objects: {result.pagination.total_count}")
        print(f"  - Page: {result.pagination.page} of {result.pagination.total_pages}")
        print(f"  - Objects Returned: {len(result.objects)}")
        print(f"  - Anonymized: {result.anonymized_count}")
        print(f"  - Query Time: {result.query_time:.3f}s")
        
        if result.objects:
            print(f"\n📋 Object Details:")
            for i, obj in enumerate(result.objects[:5], 1):
                print(f"  {i}. {obj.object_id} - {obj.name}")
                print(f"     - Type: {obj.object_type.value}")
                print(f"     - Status: {obj.status.value}")
                print(f"     - Condition: {obj.condition.value}")
                print()
            
            if len(result.objects) > 5:
                print(f"  ... and {len(result.objects) - 5} more objects")
        
        # Save results if output specified
        if args.output:
            result_data = {
                "contributor_id": args.contributor_id,
                "objects": [asdict(obj) for obj in result.objects],
                "pagination": asdict(result.pagination),
                "filters_applied": result.filters_applied,
                "query_time": result.query_time,
                "anonymized_count": result.anonymized_count
            }
            self._save_json_file(args.output, result_data)
            print(f"💾 Results saved to: {args.output}")
        
        print("🎉 Contributor objects query completed!")
    
    def get_system_summary(self, args):
        """Get system summary."""
        print("📊 Getting System Summary")
        print("=" * 40)
        
        summary = self.service.get_system_summary(
            user_id=args.user_id,
            user_license_level=args.user_license_level
        )
        
        print(f"📈 System Summary:")
        print(f"  - Total Objects: {summary['total_objects']}")
        print(f"  - Recent Installations (30 days): {summary['recent_installations']}")
        print(f"  - Generated At: {summary['generated_at']}")
        
        if summary['objects_by_type']:
            print(f"\n📋 Objects by Type:")
            for obj_type, count in summary['objects_by_type'].items():
                print(f"  - {obj_type}: {count}")
        
        if summary['objects_by_status']:
            print(f"\n📋 Objects by Status:")
            for status, count in summary['objects_by_status'].items():
                print(f"  - {status}: {count}")
        
        if summary['objects_by_condition']:
            print(f"\n📋 Objects by Condition:")
            for condition, count in summary['objects_by_condition'].items():
                print(f"  - {condition}: {count}")
        
        if summary['objects_by_contributor']:
            print(f"\n📋 Objects by Contributor:")
            for contributor_id, count in summary['objects_by_contributor'].items():
                print(f"  - {contributor_id}: {count}")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, summary)
            print(f"💾 Summary saved to: {args.output}")
        
        print("🎉 System summary completed!")
    
    def get_analytics(self, args):
        """Get access analytics."""
        print(f"📊 Getting Access Analytics (Last {args.days} days)")
        print("=" * 40)
        
        analytics = self.service.get_access_analytics(days=args.days)
        
        print(f"📈 Analytics Summary:")
        print(f"  - Period: {analytics['period_days']} days")
        print(f"  - Total Access: {analytics['total_access']}")
        print(f"  - Avg Response Time: {analytics['avg_response_time']:.3f}s")
        print(f"  - Total Objects Returned: {analytics['total_objects_returned']}")
        print(f"  - Total Objects Anonymized: {analytics['total_objects_anonymized']}")
        print(f"  - Anonymization Rate: {analytics['anonymization_rate']:.1%}")
        
        if analytics['access_by_endpoint']:
            print(f"\n📋 Access by Endpoint:")
            for endpoint, count in analytics['access_by_endpoint'].items():
                print(f"  - {endpoint}: {count}")
        
        # Save results if output specified
        if args.output:
            self._save_json_file(args.output, analytics)
            print(f"💾 Analytics saved to: {args.output}")
        
        print("🎉 Analytics generation completed!")
    
    def export_objects(self, args):
        """Export objects."""
        print(f"📤 Exporting Objects ({args.format.upper()})")
        print("=" * 40)
        
        # Build filters
        filters = QueryFilter()
        
        if args.object_type:
            try:
                filters.object_type = ObjectType(args.object_type.lower())
            except ValueError:
                print(f"❌ Invalid object type: {args.object_type}")
                sys.exit(1)
        
        if args.status:
            try:
                filters.status = ObjectStatus(args.status.lower())
            except ValueError:
                print(f"❌ Invalid status: {args.status}")
                sys.exit(1)
        
        if args.condition:
            try:
                filters.condition = ObjectCondition(args.condition.lower())
            except ValueError:
                print(f"❌ Invalid condition: {args.condition}")
                sys.exit(1)
        
        if args.contributor_id:
            filters.contributor_id = args.contributor_id
        
        if args.date_from:
            try:
                from datetime import datetime
                filters.date_from = datetime.fromisoformat(args.date_from)
            except ValueError:
                print(f"❌ Invalid date_from format: {args.date_from}")
                sys.exit(1)
        
        if args.date_to:
            try:
                from datetime import datetime
                filters.date_to = datetime.fromisoformat(args.date_to)
            except ValueError:
                print(f"❌ Invalid date_to format: {args.date_to}")
                sys.exit(1)
        
        # Export objects
        exported_data = self.service.export_objects(
            filters=filters,
            format=args.format,
            user_id=args.user_id,
            user_license_level=args.user_license_level
        )
        
        print(f"✅ Export completed")
        print(f"   - Format: {args.format.upper()}")
        print(f"   - Data Size: {len(exported_data)} characters")
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(exported_data)
            print(f"💾 Data saved to: {args.output}")
        else:
            print(f"📄 Exported Data Preview:")
            print("-" * 20)
            print(exported_data[:500] + "..." if len(exported_data) > 500 else exported_data)
        
        print("🎉 Object export completed!")
    
    def get_filters(self, args):
        """Get available filters."""
        print("🔍 Getting Available Filters")
        print("=" * 40)
        
        if args.type == "object-types" or not args.type:
            print("📋 Object Types:")
            object_types = [obj_type.value for obj_type in ObjectType]
            for obj_type in object_types:
                print(f"  - {obj_type}")
            print()
        
        if args.type == "statuses" or not args.type:
            print("📋 Statuses:")
            statuses = [status.value for status in ObjectStatus]
            for status in statuses:
                print(f"  - {status}")
            print()
        
        if args.type == "conditions" or not args.type:
            print("📋 Conditions:")
            conditions = [condition.value for condition in ObjectCondition]
            for condition in conditions:
                print(f"  - {condition}")
            print()
        
        if args.type == "contributors" or not args.type:
            print("📋 Contributors:")
            contributors = [
                {"contributor_id": "contrib_001", "name": "John Smith", "role": "owner"},
                {"contributor_id": "contrib_002", "name": "Sarah Johnson", "role": "contributor"},
                {"contributor_id": "contrib_003", "name": "Mike Wilson", "role": "viewer"},
                {"contributor_id": "contrib_004", "name": "Lisa Brown", "role": "admin"}
            ]
            for contributor in contributors:
                print(f"  - {contributor['contributor_id']}: {contributor['name']} ({contributor['role']})")
        
        # Save results if output specified
        if args.output:
            filters_data = {
                "object_types": [obj_type.value for obj_type in ObjectType],
                "statuses": [status.value for status in ObjectStatus],
                "conditions": [condition.value for condition in ObjectCondition],
                "contributors": [
                    {"contributor_id": "contrib_001", "name": "John Smith", "role": "owner"},
                    {"contributor_id": "contrib_002", "name": "Sarah Johnson", "role": "contributor"},
                    {"contributor_id": "contrib_003", "name": "Mike Wilson", "role": "viewer"},
                    {"contributor_id": "contrib_004", "name": "Lisa Brown", "role": "admin"}
                ]
            }
            self._save_json_file(args.output, filters_data)
            print(f"💾 Filters saved to: {args.output}")
        
        print("🎉 Filters retrieval completed!")
    
    def get_status(self, args):
        """Get service status."""
        print("📊 Data API Structuring Service Status")
        print("=" * 40)
        
        metrics = self.service.get_performance_metrics()
        
        if "error" in metrics:
            print(f"❌ Error: {metrics['error']}")
            sys.exit(1)
        
        print(f"📈 Performance Metrics:")
        print(f"  - Total Objects: {metrics['total_objects']}")
        print(f"  - Recent Access: {metrics['recent_access']}")
        print(f"  - Avg Response Time: {metrics['avg_response_time']:.3f}s")
        print(f"  - Database Size: {metrics['database_size']} bytes")
        
        if args.detailed and metrics['objects_by_type']:
            print(f"\n📋 Objects by Type:")
            for obj_type, count in metrics['objects_by_type'].items():
                print(f"  - {obj_type}: {count}")
        
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
        """Health check for data API service."""
        print("🏥 Data API Structuring Service Health Check")
        print("=" * 40)
        
        metrics = self.service.get_performance_metrics()
        
        if "error" in metrics:
            print("❌ Service Health: FAILED")
            print(f"   Error: {metrics['error']}")
            sys.exit(1)
        
        # Determine health status
        avg_response_time = metrics.get("avg_response_time", 0.0)
        total_objects = metrics.get("total_objects", 0)
        
        if avg_response_time < 0.5 and total_objects > 0:
            health_status = "✅ HEALTHY"
        elif avg_response_time < 1.0 and total_objects > 0:
            health_status = "⚠️  DEGRADED"
        else:
            health_status = "❌ UNHEALTHY"
        
        print(f"🏥 Health Status: {health_status}")
        print(f"\n📊 Health Metrics:")
        print(f"  - Avg Response Time: {avg_response_time:.3f}s")
        print(f"  - Total Objects: {total_objects}")
        print(f"  - Recent Access: {metrics.get('recent_access', 0)}")
        print(f"  - Database Size: {metrics.get('database_size', 0)} bytes")
        
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
                "service": "Data API Structuring"
            }
            self._save_json_file(args.output, health_data)
            print(f"💾 Health check results saved to: {args.output}")
        
        if health_status == "❌ UNHEALTHY":
            sys.exit(1)
        
        print("🎉 Health check completed!")
    
    # Helper methods
    
    def _save_json_file(self, file_path: str, data: Dict[str, Any]):
        """Save JSON file with error handling."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save file: {e}")


def main():
    """Main entry point for CLI."""
    cli = DataAPIStructuringCLI()
    cli.run()


if __name__ == "__main__":
    main() 