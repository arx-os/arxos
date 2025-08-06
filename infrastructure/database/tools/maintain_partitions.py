#!/usr/bin/env python3
"""
Table Partition Maintenance Automation Tool

This script automates the creation of new partitions and cleanup of old ones
for partitioned tables. It follows Arxos standards for structured logging
and comprehensive maintenance operations.

Features:
- Automatically creates new monthly partitions
- Removes old partitions based on retention policy
- Validates partition integrity
- Generates maintenance reports
- Supports scheduled execution

Usage:
    python maintain_partitions.py [--database-url postgresql://...]
    python maintain_partitions.py --help
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import structlog
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)


@dataclass
class PartitionInfo:
    """Information about a database partition."""

    partition_name: str
    parent_table: str
    start_date: datetime
    end_date: datetime
    row_count: int
    size_mb: float
    is_active: bool


@dataclass
class MaintenanceResult:
    """Result of a maintenance operation."""

    operation: str
    table_name: str
    partition_name: str
    success: bool
    execution_time_ms: float
    rows_affected: int
    error_message: Optional[str]


@dataclass
class MaintenanceSummary:
    """Summary of maintenance operations."""

    maintenance_timestamp: datetime
    database_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    partitions_created: int
    partitions_dropped: int
    total_time_ms: float
    maintenance_results: List[MaintenanceResult]
    recommendations: List[str]


class PartitionMaintainer:
    """
    Maintainer for automated partition management.

    Follows Arxos logging standards with structured logging, performance monitoring,
    and comprehensive maintenance operations.
    """

    def __init__(self, database_url: str):
        """
        Initialize the partition maintainer.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.connection = None
        self.maintenance_results = None

        # Performance tracking
        self.metrics = {
            "operations_executed": 0,
            "total_execution_time_ms": 0,
            "errors": 0,
            "warnings": 0,
        }

        # Partitioned tables configuration
        self.partitioned_tables = {
            "audit_logs_partitioned": {
                "partition_key": "created_at",
                "retention_months": 12,
                "create_ahead_months": 3,
            },
            "object_history_partitioned": {
                "partition_key": "changed_at",
                "retention_months": 12,
                "create_ahead_months": 3,
            },
            "slow_query_log_partitioned": {
                "partition_key": "timestamp",
                "retention_months": 6,
                "create_ahead_months": 3,
            },
            "chat_messages_partitioned": {
                "partition_key": "created_at",
                "retention_months": 12,
                "create_ahead_months": 3,
            },
        }

        logger.info(
            "partition_maintainer_initialized",
            database_url=self._mask_password(database_url),
        )

    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if "@" in url and ":" in url:
            parts = url.split("@")
            if len(parts) == 2:
                auth_part = parts[0]
                if ":" in auth_part:
                    user_pass = auth_part.split("://")
                    if len(user_pass) == 2:
                        protocol = user_pass[0]
                        credentials = user_pass[1]
                        if ":" in credentials:
                            user = credentials.split(":")[0]
                            return f"{protocol}://{user}:***@{parts[1]}"
        return url

    def connect(self) -> bool:
        """
        Establish database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(self.database_url)
            logger.info("database_connection_established")
            return True
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            return False

    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("database_connection_closed")

    def run_maintenance(self) -> bool:
        """
        Run comprehensive partition maintenance.

        Returns:
            True if maintenance successful, False otherwise
        """
        start_time = datetime.now()

        if not self.connect():
            return False

        try:
            logger.info("starting_partition_maintenance")

            # Get database information
            db_info = self._get_database_info()

            # Run maintenance for each partitioned table
            maintenance_results = []

            for table_name, config in self.partitioned_tables.items():
                logger.info(
                    "maintaining_table",
                    table_name=table_name,
                    retention_months=config["retention_months"],
                )

                # Create new partitions
                create_results = self._create_new_partitions(table_name, config)
                maintenance_results.extend(create_results)

                # Drop old partitions
                drop_results = self._drop_old_partitions(table_name, config)
                maintenance_results.extend(drop_results)

                # Validate partitions
                validation_results = self._validate_partitions(table_name)
                maintenance_results.extend(validation_results)

            # Generate maintenance summary
            self.maintenance_results = self._generate_maintenance_summary(
                db_info, maintenance_results
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["total_execution_time_ms"] = processing_time

            logger.info(
                "partition_maintenance_completed",
                operations_executed=self.metrics["operations_executed"],
                processing_time_ms=round(processing_time, 2),
            )

            return True

        except Exception as e:
            logger.error("partition_maintenance_failed", error=str(e))
            return False
        finally:
            self.disconnect()

    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT current_database() as database_name")
            result = cursor.fetchone()
            return dict(result)

    def _create_new_partitions(
        self, table_name: str, config: Dict[str, Any]
    ) -> List[MaintenanceResult]:
        """
        Create new partitions for the specified table.

        Args:
            table_name: Name of the partitioned table
            config: Table configuration

        Returns:
            List of maintenance results
        """
        results = []
        create_ahead_months = config["create_ahead_months"]
        partition_key = config["partition_key"]

        # Get existing partitions
        existing_partitions = self._get_existing_partitions(table_name)

        # Calculate date range for new partitions
        current_date = datetime.now()
        end_date = current_date + timedelta(days=30 * create_ahead_months)

        # Create partitions for each month
        partition_date = current_date
        while partition_date <= end_date:
            partition_name = self._generate_partition_name(table_name, partition_date)

            # Check if partition already exists
            if not any(p.partition_name == partition_name for p in existing_partitions):
                result = self._create_single_partition(
                    table_name, partition_name, partition_date, partition_key
                )
                results.append(result)

            # Move to next month
            partition_date = partition_date + timedelta(days=30)

        return results

    def _drop_old_partitions(
        self, table_name: str, config: Dict[str, Any]
    ) -> List[MaintenanceResult]:
        """
        Drop old partitions based on retention policy.

        Args:
            table_name: Name of the partitioned table
            config: Table configuration

        Returns:
            List of maintenance results
        """
        results = []
        retention_months = config["retention_months"]

        # Get existing partitions
        existing_partitions = self._get_existing_partitions(table_name)

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=30 * retention_months)

        # Drop partitions older than retention period
        for partition in existing_partitions:
            if partition.start_date < cutoff_date and not partition.is_active:
                result = self._drop_single_partition(
                    table_name, partition.partition_name
                )
                results.append(result)

        return results

    def _validate_partitions(self, table_name: str) -> List[MaintenanceResult]:
        """
        Validate partition integrity and performance.

        Args:
            table_name: Name of the partitioned table

        Returns:
            List of maintenance results
        """
        results = []

        # Get existing partitions
        existing_partitions = self._get_existing_partitions(table_name)

        # Validate each partition
        for partition in existing_partitions:
            result = self._validate_single_partition(table_name, partition)
            results.append(result)

        return results

    def _get_existing_partitions(self, table_name: str) -> List[PartitionInfo]:
        """Get information about existing partitions."""
        partitions = []

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        c.relname as partition_name,
                        pg_get_expr(c.relpartbound, c.oid) as partition_expression,
                        pg_size_pretty(pg_total_relation_size(c.oid)) as size_pretty,
                        pg_total_relation_size(c.oid) as size_bytes,
                        c.reltuples as row_count
                    FROM pg_class c
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = 'public'
                    AND c.relname LIKE %s
                    AND c.relispartition = true
                    ORDER BY c.relname
                """,
                    (f"{table_name}_p%",),
                )

                for row in cursor.fetchall():
                    partition_name = row["partition_name"]
                    partition_expression = row["partition_expression"]

                    # Parse partition boundaries from expression
                    start_date, end_date = self._parse_partition_boundaries(
                        partition_expression
                    )

                    # Check if partition is active (has data)
                    is_active = row["row_count"] > 0

                    partitions.append(
                        PartitionInfo(
                            partition_name=partition_name,
                            parent_table=table_name,
                            start_date=start_date,
                            end_date=end_date,
                            row_count=row["row_count"],
                            size_mb=row["size_bytes"] / (1024 * 1024),
                            is_active=is_active,
                        )
                    )

        except Exception as e:
            logger.error(
                "failed_to_get_existing_partitions", table_name=table_name, error=str(e)
            )

        return partitions

    def _parse_partition_boundaries(
        self, partition_expression: str
    ) -> Tuple[datetime, datetime]:
        """Parse partition boundaries from PostgreSQL expression."""
        try:
            # Extract date values from expression like "FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')"
            if "FROM ('" in partition_expression and "') TO ('" in partition_expression:
                start_str = partition_expression.split("FROM ('")[1].split("') TO")[0]
                end_str = partition_expression.split("') TO ('")[1].split("')")[0]

                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")

                return start_date, end_date
        except Exception as e:
            logger.warning(
                "failed_to_parse_partition_boundaries",
                expression=partition_expression,
                error=str(e),
            )

        # Return default values if parsing fails
        return datetime.now(), datetime.now() + timedelta(days=30)

    def _generate_partition_name(
        self, table_name: str, partition_date: datetime
    ) -> str:
        """Generate partition name based on table and date."""
        return f"{table_name}_p{partition_date.strftime('%Y_%m')}"

    def _create_single_partition(
        self,
        table_name: str,
        partition_name: str,
        partition_date: datetime,
        partition_key: str,
    ) -> MaintenanceResult:
        """Create a single partition."""
        start_time = time.time()

        try:
            # Calculate partition boundaries
            start_date = partition_date.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1)

            # Create partition SQL
            sql = f"""
                CREATE TABLE {partition_name} PARTITION OF {table_name}
                FOR VALUES FROM ('{start_date.strftime('%Y-%m-%d')}') 
                TO ('{end_date.strftime('%Y-%m-%d')}')
            """

            with self.connection.cursor() as cursor:
                cursor.execute(sql)

            execution_time_ms = (time.time() - start_time) * 1000

            # Log the operation
            self._log_maintenance_operation(
                table_name, "create_partition", partition_name
            )

            return MaintenanceResult(
                operation="create_partition",
                table_name=table_name,
                partition_name=partition_name,
                success=True,
                execution_time_ms=execution_time_ms,
                rows_affected=0,
                error_message=None,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "failed_to_create_partition",
                table_name=table_name,
                partition_name=partition_name,
                error=str(e),
            )

            return MaintenanceResult(
                operation="create_partition",
                table_name=table_name,
                partition_name=partition_name,
                success=False,
                execution_time_ms=execution_time_ms,
                rows_affected=0,
                error_message=str(e),
            )

    def _drop_single_partition(
        self, table_name: str, partition_name: str
    ) -> MaintenanceResult:
        """Drop a single partition."""
        start_time = time.time()

        try:
            # Get row count before dropping
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {partition_name}")
                row_count = cursor.fetchone()[0]

            # Drop partition
            sql = f"DROP TABLE {partition_name}"

            with self.connection.cursor() as cursor:
                cursor.execute(sql)

            execution_time_ms = (time.time() - start_time) * 1000

            # Log the operation
            self._log_maintenance_operation(
                table_name, "drop_partition", partition_name
            )

            return MaintenanceResult(
                operation="drop_partition",
                table_name=table_name,
                partition_name=partition_name,
                success=True,
                execution_time_ms=execution_time_ms,
                rows_affected=row_count,
                error_message=None,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "failed_to_drop_partition",
                table_name=table_name,
                partition_name=partition_name,
                error=str(e),
            )

            return MaintenanceResult(
                operation="drop_partition",
                table_name=table_name,
                partition_name=partition_name,
                success=False,
                execution_time_ms=execution_time_ms,
                rows_affected=0,
                error_message=str(e),
            )

    def _validate_single_partition(
        self, table_name: str, partition: PartitionInfo
    ) -> MaintenanceResult:
        """Validate a single partition."""
        start_time = time.time()

        try:
            # Check partition integrity
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {partition.partition_name}")
                actual_row_count = cursor.fetchone()[0]

            # Validate row count matches expected
            is_valid = actual_row_count == partition.row_count

            execution_time_ms = (time.time() - start_time) * 1000

            return MaintenanceResult(
                operation="validate_partition",
                table_name=table_name,
                partition_name=partition.partition_name,
                success=is_valid,
                execution_time_ms=execution_time_ms,
                rows_affected=actual_row_count,
                error_message=None if is_valid else "Row count mismatch",
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "failed_to_validate_partition",
                table_name=table_name,
                partition_name=partition.partition_name,
                error=str(e),
            )

            return MaintenanceResult(
                operation="validate_partition",
                table_name=table_name,
                partition_name=partition.partition_name,
                success=False,
                execution_time_ms=execution_time_ms,
                rows_affected=0,
                error_message=str(e),
            )

    def _log_maintenance_operation(
        self, table_name: str, operation: str, partition_name: str
    ) -> None:
        """Log maintenance operation to audit log."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_logs_partitioned (object_type, object_id, action, payload)
                    VALUES (%s, %s, %s, %s)
                """,
                    (
                        "partition_maintenance",
                        partition_name,
                        operation,
                        json.dumps(
                            {
                                "table_name": table_name,
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                    ),
                )
        except Exception as e:
            logger.warning("failed_to_log_maintenance_operation", error=str(e))

    def _generate_maintenance_summary(
        self, db_info: Dict[str, Any], maintenance_results: List[MaintenanceResult]
    ) -> MaintenanceSummary:
        """Generate summary of maintenance operations."""
        if not maintenance_results:
            return MaintenanceSummary(
                maintenance_timestamp=datetime.now(),
                database_name=db_info["database_name"],
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                partitions_created=0,
                partitions_dropped=0,
                total_time_ms=0.0,
                maintenance_results=[],
                recommendations=[],
            )

        # Calculate summary statistics
        total_operations = len(maintenance_results)
        successful_operations = len([r for r in maintenance_results if r.success])
        failed_operations = total_operations - successful_operations
        partitions_created = len(
            [
                r
                for r in maintenance_results
                if r.operation == "create_partition" and r.success
            ]
        )
        partitions_dropped = len(
            [
                r
                for r in maintenance_results
                if r.operation == "drop_partition" and r.success
            ]
        )
        total_time_ms = sum(r.execution_time_ms for r in maintenance_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(maintenance_results)

        return MaintenanceSummary(
            maintenance_timestamp=datetime.now(),
            database_name=db_info["database_name"],
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            partitions_created=partitions_created,
            partitions_dropped=partitions_dropped,
            total_time_ms=total_time_ms,
            maintenance_results=maintenance_results,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, maintenance_results: List[MaintenanceResult]
    ) -> List[str]:
        """Generate recommendations based on maintenance results."""
        recommendations = []

        # Analyze operation success rates
        operation_types = {}
        for result in maintenance_results:
            if result.operation not in operation_types:
                operation_types[result.operation] = {"success": 0, "total": 0}
            operation_types[result.operation]["total"] += 1
            if result.success:
                operation_types[result.operation]["success"] += 1

        for operation, stats in operation_types.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            if success_rate < 100:
                recommendations.append(
                    f"{operation}: {success_rate:.1f}% success rate - review needed"
                )
            else:
                recommendations.append(f"{operation}: 100% success rate - excellent")

        # Analyze performance
        avg_execution_time = sum(
            r.execution_time_ms for r in maintenance_results
        ) / len(maintenance_results)
        if avg_execution_time > 1000:
            recommendations.append(
                f"Average execution time: {avg_execution_time:.1f}ms - consider optimization"
            )
        else:
            recommendations.append(
                f"Average execution time: {avg_execution_time:.1f}ms - good performance"
            )

        # Analyze partition distribution
        created_count = len(
            [
                r
                for r in maintenance_results
                if r.operation == "create_partition" and r.success
            ]
        )
        dropped_count = len(
            [
                r
                for r in maintenance_results
                if r.operation == "drop_partition" and r.success
            ]
        )

        if created_count > 0:
            recommendations.append(f"Created {created_count} new partitions")
        if dropped_count > 0:
            recommendations.append(f"Dropped {dropped_count} old partitions")

        return recommendations

    def generate_report(
        self, output_format: str = "json", output_file: Optional[str] = None
    ) -> str:
        """
        Generate maintenance report in specified format.

        Args:
            output_format: 'json' or 'markdown'
            output_file: Optional output file path

        Returns:
            Generated report content
        """
        if not self.maintenance_results:
            logger.warning("no_maintenance_results_to_report")
            return ""

        logger.info(
            "generating_maintenance_report",
            format=output_format,
            total_operations=self.maintenance_results.total_operations,
        )

        if output_format.lower() == "json":
            return self._generate_json_report(output_file)
        elif output_format.lower() == "markdown":
            return self._generate_markdown_report(output_file)
        else:
            logger.error("unsupported_output_format", format=output_format)
            return ""

    def _generate_json_report(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format report."""
        report = {
            "metadata": {
                "maintenance_timestamp": self.maintenance_results.maintenance_timestamp.isoformat(),
                "database_name": self.maintenance_results.database_name,
                "total_operations": self.maintenance_results.total_operations,
                "processing_metrics": self.metrics,
            },
            "summary": {
                "successful_operations": self.maintenance_results.successful_operations,
                "failed_operations": self.maintenance_results.failed_operations,
                "partitions_created": self.maintenance_results.partitions_created,
                "partitions_dropped": self.maintenance_results.partitions_dropped,
                "total_time_ms": self.maintenance_results.total_time_ms,
                "recommendations": self.maintenance_results.recommendations,
            },
            "maintenance_results": [
                asdict(result)
                for result in self.maintenance_results.maintenance_results
            ],
        }

        content = json.dumps(report, indent=2, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(content)
            logger.info("json_report_saved", file=output_file)

        return content

    def _generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """Generate Markdown format report."""
        content = f"""# Partition Maintenance Report

**Generated:** {self.maintenance_results.maintenance_timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Database:** {self.maintenance_results.database_name}  
**Total Operations:** {self.maintenance_results.total_operations}

## Executive Summary

- **Successful Operations:** {self.maintenance_results.successful_operations}
- **Failed Operations:** {self.maintenance_results.failed_operations}
- **Partitions Created:** {self.maintenance_results.partitions_created}
- **Partitions Dropped:** {self.maintenance_results.partitions_dropped}
- **Total Time:** {self.maintenance_results.total_time_ms:.1f}ms

## Maintenance Recommendations

"""

        for rec in self.maintenance_results.recommendations:
            content += f"- {rec}\n"

        content += "\n## Detailed Results\n\n"

        for result in self.maintenance_results.maintenance_results:
            status = "✅" if result.success else "❌"
            content += f"### {status} {result.operation.title()}\n\n"
            content += f"- **Table:** {result.table_name}\n"
            content += f"- **Partition:** {result.partition_name}\n"
            content += f"- **Execution Time:** {result.execution_time_ms:.2f}ms\n"
            content += f"- **Rows Affected:** {result.rows_affected}\n"

            if result.error_message:
                content += f"- **Error:** {result.error_message}\n"

            content += "\n"

        if output_file:
            with open(output_file, "w") as f:
                f.write(content)
            logger.info("markdown_report_saved", file=output_file)

        return content


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Maintain table partitions automatically"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://localhost/arxos_db"),
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown"],
        default="json",
        help="Output format for the report (default: json)",
    )
    parser.add_argument(
        "--output-file", help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Run maintenance
    maintainer = PartitionMaintainer(args.database_url)
    success = maintainer.run_maintenance()

    if success:
        # Generate report
        report_content = maintainer.generate_report(
            output_format=args.output_format, output_file=args.output_file
        )

        # Print summary
        if maintainer.maintenance_results:
            print("\n" + "=" * 60)
            print("PARTITION MAINTENANCE SUMMARY")
            print("=" * 60)
            print(
                f"Total operations: {maintainer.maintenance_results.total_operations}"
            )
            print(f"Successful: {maintainer.maintenance_results.successful_operations}")
            print(f"Failed: {maintainer.maintenance_results.failed_operations}")
            print(
                f"Partitions created: {maintainer.maintenance_results.partitions_created}"
            )
            print(
                f"Partitions dropped: {maintainer.maintenance_results.partitions_dropped}"
            )
            print("\nRecommendations:")
            for rec in maintainer.maintenance_results.recommendations:
                print(f"- {rec}")
            print("=" * 60)

        # Print report if no output file specified
        if not args.output_file and report_content:
            print("\n" + report_content)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
