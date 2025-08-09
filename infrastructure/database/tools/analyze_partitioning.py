#!/usr/bin/env python3
"""
Table Partitioning Analysis Tool for Arxos Database

This script analyzes database tables to identify candidates for partitioning
based on size, insert volume, and query patterns. It follows Arxos standards
for structured logging and comprehensive analysis.

Features:
- Identifies large tables with high insert volumes
- Analyzes query patterns and access frequency
- Recommends partitioning strategies (range, list, hybrid)
- Estimates performance improvements
- Generates migration plans

Usage:
    python analyze_partitioning.py [--database-url postgresql://...]
    python analyze_partitioning.py --help
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

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)

@dataclass
class TableMetrics:
    """Metrics for a database table."""
    table_name: str
    row_count: int
    table_size_mb: float
    index_size_mb: float
    total_size_mb: float
    avg_row_size_bytes: int
    last_vacuum: Optional[datetime]
    last_analyze: Optional[datetime]
    insert_rate_per_day: float
    update_rate_per_day: float
    delete_rate_per_day: float
    read_rate_per_day: float
    partition_candidate: bool
    recommended_strategy: Optional[str]
    partition_key: Optional[str]
    estimated_improvement: Optional[str]

@dataclass
class PartitioningPlan:
    """Partitioning plan for a table."""
    table_name: str
    strategy: str  # 'range', 'list', 'hybrid'
    partition_key: str
    partition_expression: str
    initial_partitions: List[str]
    maintenance_schedule: str
    estimated_improvement: str
    migration_steps: List[str]
    rollback_plan: List[str]

@dataclass
class PartitioningAnalysis:
    """Complete partitioning analysis results."""
    analysis_timestamp: datetime
    database_name: str
    tables_analyzed: int
    partition_candidates: int
    high_priority_tables: List[str]
    medium_priority_tables: List[str]
    low_priority_tables: List[str]
    table_metrics: List[TableMetrics]
    partitioning_plans: List[PartitioningPlan]
    recommendations: List[str]
    performance_estimates: Dict[str, Any]

class PartitioningAnalyzer:
    """
    Analyzer for identifying table partitioning candidates.

    Follows Arxos logging standards with structured logging, performance monitoring,
    and comprehensive analysis of table characteristics.
    """

    def __init__(self, database_url: str):
        """
        Initialize the partitioning analyzer.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.connection = None
        self.analysis_results = None

        # Performance tracking
        self.metrics = {
            'tables_analyzed': 0,
            'partition_candidates_found': 0,
            'processing_time_ms': 0,
            'errors': 0,
            'warnings': 0
        }

        # Partitioning criteria
        self.partitioning_criteria = {
            'size_threshold_mb': 1000,  # 1GB
            'row_count_threshold': 1000000,  # 1M rows
            'insert_rate_threshold': 1000,  # 1000 inserts/day
            'query_frequency_threshold': 100,  # 100 queries/day
            'age_threshold_days': 180  # 6 months
        }

        # Target tables for analysis
        self.target_tables = [
            'audit_logs',
            'object_history',
            'slow_query_log',
            'chat_messages',
            'comments',
            'assignments'
        ]

        # Partitioning strategies
        self.strategies = {
            'range_by_date': {
                'description': 'Range partitioning by timestamp',
                'suitable_for': ['audit_logs', 'object_history', 'slow_query_log', 'chat_messages'],
                'partition_key': 'created_at',
                'expression': 'PARTITION BY RANGE (created_at)'
            },
            'list_by_tenant': {
                'description': 'List partitioning by tenant/project',
                'suitable_for': ['audit_logs', 'object_history'],
                'partition_key': 'project_id',
                'expression': 'PARTITION BY LIST (project_id)'
            },
            'hybrid_date_tenant': {
                'description': 'Hybrid partitioning by date and tenant',
                'suitable_for': ['audit_logs', 'object_history'],
                'partition_key': '(created_at, project_id)',
                'expression': 'PARTITION BY RANGE (created_at)'
            }
        }

        logger.info("partitioning_analyzer_initialized",
                    database_url=self._mask_password(database_url))

    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if '@' in url and ':' in url:
            parts = url.split('@')
            if len(parts) == 2:
                auth_part = parts[0]
                if ':' in auth_part:
                    user_pass = auth_part.split('://')
                    if len(user_pass) == 2:
                        protocol = user_pass[0]
                        credentials = user_pass[1]
                        if ':' in credentials:
                            user = credentials.split(':')[0]
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
            logger.error("database_connection_failed",
                         error=str(e))
            return False

    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("database_connection_closed")

    def analyze_tables(self) -> bool:
        """
        Perform comprehensive table analysis for partitioning.

        Returns:
            True if analysis successful, False otherwise
        """
        start_time = datetime.now()

        if not self.connect():
            return False

        try:
            logger.info("starting_partitioning_analysis")

            # Get database information
            db_info = self._get_database_info()

            # Analyze each target table
            table_metrics = []
            partitioning_plans = []

            for table_name in self.target_tables:
                metrics = self._analyze_table(table_name)
                if metrics:
                    table_metrics.append(metrics)
                    self.metrics['tables_analyzed'] += 1

                    if metrics.partition_candidate:
                        plan = self._create_partitioning_plan(metrics)
                        if plan:
                            partitioning_plans.append(plan)
                            self.metrics['partition_candidates_found'] += 1

            # Generate analysis results
            self.analysis_results = PartitioningAnalysis(
                analysis_timestamp=datetime.now(),
                database_name=db_info['database_name'],
                tables_analyzed=len(table_metrics),
                partition_candidates=len(partitioning_plans),
                high_priority_tables=[t.table_name for t in table_metrics if t.total_size_mb > 5000],
                medium_priority_tables=[t.table_name for t in table_metrics if 1000 <= t.total_size_mb <= 5000],
                low_priority_tables=[t.table_name for t in table_metrics if t.total_size_mb < 1000],
                table_metrics=table_metrics,
                partitioning_plans=partitioning_plans,
                recommendations=self._generate_recommendations(table_metrics, partitioning_plans),
                performance_estimates=self._estimate_performance_improvements(partitioning_plans)
            )
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['processing_time_ms'] = processing_time

            logger.info("partitioning_analysis_completed",
                        tables_analyzed=self.metrics['tables_analyzed'],
                        partition_candidates=self.metrics['partition_candidates_found'],
                        processing_time_ms=round(processing_time, 2))
            return True

        except Exception as e:
            logger.error("partitioning_analysis_failed",
                         error=str(e))
            return False
        finally:
            self.disconnect()

    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT current_database() as database_name")
            result = cursor.fetchone()
            return dict(result)

    def _analyze_table(self, table_name: str) -> Optional[TableMetrics]:
        """
        Analyze a single table for partitioning suitability.

        Args:
            table_name: Name of the table to analyze

        Returns:
            TableMetrics object with analysis results
        """
        try:
            logger.debug("analyzing_table",
                        table=table_name)

            # Check if table exists
            if not self._table_exists(table_name):
                logger.warning("table_not_found",
                             table=table_name)
                return None

            # Get table size and row count
            size_info = self._get_table_size_info(table_name)

            # Get activity metrics
            activity_metrics = self._get_activity_metrics(table_name)

            # Get maintenance info
            maintenance_info = self._get_maintenance_info(table_name)

            # Determine if table is a partitioning candidate
            partition_candidate = self._is_partition_candidate(size_info, activity_metrics)

            # Determine recommended strategy
            recommended_strategy = self._recommend_partitioning_strategy(table_name, activity_metrics)

            # Determine partition key
            partition_key = self._determine_partition_key(table_name, recommended_strategy)

            # Estimate improvement
            estimated_improvement = self._estimate_improvement(size_info, activity_metrics)

            return TableMetrics(
                table_name=table_name,
                row_count=size_info['row_count'],
                table_size_mb=size_info['table_size_mb'],
                index_size_mb=size_info['index_size_mb'],
                total_size_mb=size_info['total_size_mb'],
                avg_row_size_bytes=size_info['avg_row_size_bytes'],
                last_vacuum=maintenance_info['last_vacuum'],
                last_analyze=maintenance_info['last_analyze'],
                insert_rate_per_day=activity_metrics['insert_rate_per_day'],
                update_rate_per_day=activity_metrics['update_rate_per_day'],
                delete_rate_per_day=activity_metrics['delete_rate_per_day'],
                read_rate_per_day=activity_metrics['read_rate_per_day'],
                partition_candidate=partition_candidate,
                recommended_strategy=recommended_strategy,
                partition_key=partition_key,
                estimated_improvement=estimated_improvement
            )

        except Exception as e:
            logger.error("failed_to_analyze_table",
                         table=table_name,
                         error=str(e))
            self.metrics['errors'] += 1
            return None

    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            """, (table_name,))
            return cursor.fetchone() is not None

    def _get_table_size_info(self, table_name: str) -> Dict[str, Any]:
        """Get table size and row count information."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                    n_live_tup as row_count,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_size_bytes,
                    pg_relation_size(schemaname||'.'||tablename) as table_size_bytes,
                    pg_indexes_size(schemaname||'.'||tablename) as index_size_bytes
                FROM pg_stat_user_tables
                WHERE tablename = %s
            """, (table_name,))
            result = cursor.fetchone()
            if result:
                total_size_mb = result['total_size_bytes'] / (1024 * 1024)
                table_size_mb = result['table_size_bytes'] / (1024 * 1024)
                index_size_mb = result['index_size_bytes'] / (1024 * 1024)
                avg_row_size = result['table_size_bytes'] / max(result['row_count'], 1)

                return {
                    'row_count': result['row_count'],
                    'total_size_mb': round(total_size_mb, 2),
                    'table_size_mb': round(table_size_mb, 2),
                    'index_size_mb': round(index_size_mb, 2),
                    'avg_row_size_bytes': int(avg_row_size),
                    'total_operations': result['total_operations']
                }
            else:
                return {
                    'row_count': 0,
                    'total_size_mb': 0,
                    'table_size_mb': 0,
                    'index_size_mb': 0,
                    'avg_row_size_bytes': 0,
                    'total_operations': 0
                }

    def _get_activity_metrics(self, table_name: str) -> Dict[str, float]:
        """Get table activity metrics."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                    CASE
                        WHEN age(now(), last_vacuum) IS NOT NULL
                        THEN EXTRACT(EPOCH FROM age(now(), last_vacuum)) / 86400
                        ELSE 30
                    END as days_since_vacuum
                FROM pg_stat_user_tables
                WHERE tablename = %s
            """, (table_name,))
            result = cursor.fetchone()
            if result:
                days_since_vacuum = result['days_since_vacuum']
                if days_since_vacuum == 0:
                    days_since_vacuum = 1

                return {
                    'insert_rate_per_day': round(result['inserts'] / days_since_vacuum, 2),
                    'update_rate_per_day': round(result['updates'] / days_since_vacuum, 2),
                    'delete_rate_per_day': round(result['deletes'] / days_since_vacuum, 2),
                    'read_rate_per_day': round(result['total_operations'] / days_since_vacuum, 2)
                }
            else:
                return {
                    'insert_rate_per_day': 0,
                    'update_rate_per_day': 0,
                    'delete_rate_per_day': 0,
                    'read_rate_per_day': 0
                }

    def _get_maintenance_info(self, table_name: str) -> Dict[str, Optional[datetime]]:
        """Get table maintenance information."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE tablename = %s
            """, (table_name,))
            result = cursor.fetchone()
            if result:
                return {
                    'last_vacuum': result['last_vacuum'],
                    'last_analyze': result['last_analyze']
                }
            else:
                return {
                    'last_vacuum': None,
                    'last_analyze': None
                }

    def _is_partition_candidate(self, size_info: Dict[str, Any], activity_metrics: Dict[str, float]) -> bool:
        """Determine if table is a partitioning candidate."""
        # Check size threshold
        if size_info['total_size_mb'] < self.partitioning_criteria['size_threshold_mb']:
            return False

        # Check row count threshold
        if size_info['row_count'] < self.partitioning_criteria['row_count_threshold']:
            return False

        # Check insert rate threshold
        if activity_metrics['insert_rate_per_day'] < self.partitioning_criteria['insert_rate_threshold']:
            return False

        return True

    def _recommend_partitioning_strategy(self, table_name: str, activity_metrics: Dict[str, float]) -> Optional[str]:
        """Recommend partitioning strategy for table."""
        if table_name in ['audit_logs', 'object_history', 'slow_query_log']:
            return 'range_by_date'
        elif table_name in ['chat_messages', 'comments']:
            return 'range_by_date'
        elif activity_metrics['insert_rate_per_day'] > 5000:
            return 'range_by_date'
        else:
            return None

    def _determine_partition_key(self, table_name: str, strategy: Optional[str]) -> Optional[str]:
        """Determine partition key for table."""
        if strategy == 'range_by_date':
            return 'created_at'
        elif strategy == 'list_by_tenant':
            return 'project_id'
        elif strategy == 'hybrid_date_tenant':
            return '(created_at, project_id)'
        else:
            return None

    def _estimate_improvement(self, size_info: Dict[str, Any], activity_metrics: Dict[str, float]) -> Optional[str]:
        """Estimate performance improvement from partitioning."""
        if size_info['total_size_mb'] > 5000:
            return "High (80-90% query improvement)"
        elif size_info['total_size_mb'] > 1000:
            return "Medium (60-80% query improvement)"
        elif size_info['total_size_mb'] > 100:
            return "Low (40-60% query improvement)"
        else:
            return None

    def _create_partitioning_plan(self, metrics: TableMetrics) -> Optional[PartitioningPlan]:
        """Create detailed partitioning plan for table."""
        if not metrics.recommended_strategy:
            return None

        strategy_info = self.strategies.get(metrics.recommended_strategy, {})

        # Generate initial partitions
        initial_partitions = self._generate_initial_partitions(metrics.table_name, metrics.recommended_strategy)

        # Generate migration steps
        migration_steps = self._generate_migration_steps(metrics.table_name, metrics.recommended_strategy)

        # Generate rollback plan
        rollback_plan = self._generate_rollback_plan(metrics.table_name)

        return PartitioningPlan(
            table_name=metrics.table_name,
            strategy=metrics.recommended_strategy,
            partition_key=metrics.partition_key,
            partition_expression=strategy_info.get('expression', ''),
            initial_partitions=initial_partitions,
            maintenance_schedule='Monthly',
            estimated_improvement=metrics.estimated_improvement,
            migration_steps=migration_steps,
            rollback_plan=rollback_plan
        )

    def _generate_initial_partitions(self, table_name: str, strategy: str) -> List[str]:
        """Generate initial partition names."""
        if strategy == 'range_by_date':
            # Generate monthly partitions for the next 12 months
            partitions = []
            current_date = datetime.now()
            for i in range(12):
                partition_date = current_date + timedelta(days=30*i)
                partition_name = f"{table_name}_p{partition_date.strftime('%Y_%m')}"
                partitions.append(partition_name)
            return partitions
        elif strategy == 'list_by_tenant':
            # Generate partitions for common project IDs
            return [f"{table_name}_p_project_{i}" for i in range(1, 11)]
        else:
            return []

    def _generate_migration_steps(self, table_name: str, strategy: str) -> List[str]:
        """Generate migration steps for partitioning."""
        steps = [
            f"1. Create partitioned parent table {table_name}_partitioned",
            f"2. Create initial partitions for {strategy} strategy",
            f"3. Migrate existing data to partitioned structure",
            f"4. Create indexes on partitioned table",
            f"5. Update application queries to use parent table",
            f"6. Drop original table and rename partitioned table",
            f"7. Update foreign key constraints"
        ]
        return steps

    def _generate_rollback_plan(self, table_name: str) -> List[str]:
        """Generate rollback plan for partitioning."""
        steps = [
            f"1. Create backup of partitioned table {table_name}",
            f"2. Recreate original table structure",
            f"3. Migrate data back to original table",
            f"4. Recreate indexes on original table",
            f"5. Update application queries to use original table",
            f"6. Drop partitioned table"
        ]
        return steps

    def _generate_recommendations(self, table_metrics: List[TableMetrics], partitioning_plans: List[PartitioningPlan]) -> List[str]:
        """Generate partitioning recommendations."""
        recommendations = []

        # High priority tables
        high_priority = [t for t in table_metrics if t.total_size_mb > 5000]
        if high_priority:
            recommendations.append(f"Prioritize partitioning for {len(high_priority)} large tables (>5GB)")

        # Medium priority tables
        medium_priority = [t for t in table_metrics if 1000 <= t.total_size_mb <= 5000]
        if medium_priority:
            recommendations.append(f"Plan partitioning for {len(medium_priority)} medium tables (1-5GB)")

        # Specific recommendations
        for plan in partitioning_plans:
            recommendations.append(f"Partition {plan.table_name} using {plan.strategy} strategy")

        # Performance recommendations
        total_size = sum(t.total_size_mb for t in table_metrics)
        if total_size > 10000:
            recommendations.append(f"Total table size: {total_size:.1f}MB - significant storage savings expected")

        return recommendations

    def _estimate_performance_improvements(self, partitioning_plans: List[PartitioningPlan]) -> Dict[str, Any]:
        """Estimate performance improvements from partitioning."""
        total_tables = len(partitioning_plans)
        total_size_mb = sum(plan.table_name for plan in partitioning_plans)  # Placeholder

        return {
            'estimated_query_improvement': '60-90%',
            'estimated_insert_improvement': '40-70%',
            'estimated_storage_savings': '20-40%',
            'estimated_maintenance_improvement': '50-80%',
            'tables_to_partition': total_tables,
            'total_size_affected_mb': total_size_mb
        }

    def generate_report(self, output_format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Generate analysis report in specified format.

        Args:
            output_format: 'json' or 'markdown'
            output_file: Optional output file path

        Returns:
            Generated report content
        """
        if not self.analysis_results:
            logger.warning("no_analysis_results_to_report")
            return ""

        logger.info("generating_partitioning_report",
                   format=output_format,
                   partition_candidates=self.analysis_results.partition_candidates)

        if output_format.lower() == "json":
            return self._generate_json_report(output_file)
        elif output_format.lower() == "markdown":
            return self._generate_markdown_report(output_file)
        else:
            logger.error("unsupported_output_format",
                        format=output_format)
            return ""

    def _generate_json_report(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format report."""
        report = {
            'metadata': {
                'analysis_timestamp': self.analysis_results.analysis_timestamp.isoformat(),
                'database_name': self.analysis_results.database_name,
                'tables_analyzed': self.analysis_results.tables_analyzed,
                'processing_metrics': self.metrics
            },
            'summary': {
                'partition_candidates': self.analysis_results.partition_candidates,
                'high_priority_tables': self.analysis_results.high_priority_tables,
                'medium_priority_tables': self.analysis_results.medium_priority_tables,
                'low_priority_tables': self.analysis_results.low_priority_tables,
                'recommendations': self.analysis_results.recommendations,
                'performance_estimates': self.analysis_results.performance_estimates
            },
            'table_metrics': [asdict(metrics) for metrics in self.analysis_results.table_metrics],
            'partitioning_plans': [asdict(plan) for plan in self.analysis_results.partitioning_plans]
        }

        content = json.dumps(report, indent=2, default=str)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("json_report_saved",
                       file=output_file)

        return content

    def _generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """Generate Markdown format report."""
        content = f"""# Table Partitioning Analysis Report

        **Generated:** {self.analysis_results.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        **Database:** {self.analysis_results.database_name}
        **Tables Analyzed:** {self.analysis_results.tables_analyzed}

        ## Executive Summary

        - **Partition Candidates:** {self.analysis_results.partition_candidates}
        - **High Priority Tables:** {len(self.analysis_results.high_priority_tables)}
        - **Medium Priority Tables:** {len(self.analysis_results.medium_priority_tables)}
        - **Low Priority Tables:** {len(self.analysis_results.low_priority_tables)}

        ## Performance Estimates

        - **Query Improvement:** {self.analysis_results.performance_estimates['estimated_query_improvement']}
        - **Insert Improvement:** {self.analysis_results.performance_estimates['estimated_insert_improvement']}
        - **Storage Savings:** {self.analysis_results.performance_estimates['estimated_storage_savings']}
        - **Maintenance Improvement:** {self.analysis_results.performance_estimates['estimated_maintenance_improvement']}

        ## Recommendations

        """

        for rec in self.analysis_results.recommendations:
            content += f"- {rec}\n"

        content += "\n## Detailed Table Analysis\n\n"

        for metrics in self.analysis_results.table_metrics:
            content += f"### {metrics.table_name.title()}\n\n"
            content += f"- **Total Size:** {metrics.total_size_mb}MB\n"
            content += f"- **Row Count:** {metrics.row_count:,}\n"
            content += f"- **Insert Rate:** {metrics.insert_rate_per_day}/day\n"
            content += f"- **Partition Candidate:** {'Yes' if metrics.partition_candidate else 'No'}\n"

            if metrics.recommended_strategy:
                content += f"- **Recommended Strategy:** {metrics.recommended_strategy}\n"
                content += f"- **Partition Key:** {metrics.partition_key}\n"
                content += f"- **Estimated Improvement:** {metrics.estimated_improvement}\n"

            content += "\n"

        content += "\n## Partitioning Plans\n\n"

        for plan in self.analysis_results.partitioning_plans:
            content += f"### {plan.table_name.title()}\n\n"
            content += f"- **Strategy:** {plan.strategy}\n"
            content += f"- **Partition Key:** {plan.partition_key}\n"
            content += f"- **Expression:** {plan.partition_expression}\n"
            content += f"- **Maintenance Schedule:** {plan.maintenance_schedule}\n"
            content += f"- **Estimated Improvement:** {plan.estimated_improvement}\n\n"

            content += "#### Migration Steps\n\n"
            for step in plan.migration_steps:
                content += f"- {step}\n"

            content += "\n#### Rollback Plan\n\n"
            for step in plan.rollback_plan:
                content += f"- {step}\n"

            content += "\n"

        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("markdown_report_saved",
                       file=output_file)

        return content


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Analyze database tables for partitioning candidates"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://localhost/arxos_db"),
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown"],
        default="json",
        help="Output format for the report (default: json)"
    )
    parser.add_argument(
        "--output-file",
        help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Run analysis
    analyzer = PartitioningAnalyzer(args.database_url)
    success = analyzer.analyze_tables()

    if success:
        # Generate report
        report_content = analyzer.generate_report(
            output_format=args.output_format,
            output_file=args.output_file
        )

        # Print summary
        if analyzer.analysis_results:
            print("\n" + "="*60)
            print("TABLE PARTITIONING ANALYSIS SUMMARY")
            print("="*60)
            print(f"Tables analyzed: {analyzer.analysis_results.tables_analyzed}")
            print(f"Partition candidates: {analyzer.analysis_results.partition_candidates}")
            print(f"High priority tables: {len(analyzer.analysis_results.high_priority_tables)}")
            print(f"Medium priority tables: {len(analyzer.analysis_results.medium_priority_tables)}")
            print("\nRecommendations:")
            for rec in analyzer.analysis_results.recommendations:
                print(f"- {rec}")
            print("="*60)

        # Print report if no output file specified
        if not args.output_file and report_content:
            print("\n" + report_content)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
