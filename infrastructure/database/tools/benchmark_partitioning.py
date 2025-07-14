#!/usr/bin/env python3
"""
Table Partitioning Performance Benchmark Tool

This script benchmarks query performance before and after table partitioning
to measure the effectiveness of partitioning strategies. It follows Arxos
standards for structured logging and comprehensive performance analysis.

Features:
- Measures query performance before and after partitioning
- Tests common query patterns (time-based, filtering, aggregation)
- Generates detailed performance reports
- Provides before/after comparison metrics
- Supports automated CI/CD integration

Usage:
    python benchmark_partitioning.py [--database-url postgresql://...]
    python benchmark_partitioning.py --help
"""

import os
import sys
import argparse
import json
import time
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
class QueryResult:
    """Results of a single query benchmark."""
    query_name: str
    table_name: str
    execution_time_ms: float
    row_count: int
    plan_type: str  # 'seq_scan', 'index_scan', 'partition_scan'
    buffer_hits: int
    buffer_reads: int
    cache_hit_ratio: float
    partition_used: Optional[str]

@dataclass
class BenchmarkResult:
    """Results of a complete benchmark run."""
    benchmark_name: str
    table_name: str
    query_type: str
    before_result: QueryResult
    after_result: QueryResult
    improvement_percentage: float
    improvement_factor: float

@dataclass
class BenchmarkSummary:
    """Summary of all benchmark results."""
    benchmark_timestamp: datetime
    database_name: str
    total_queries: int
    total_improvement: float
    average_improvement: float
    best_improvement: float
    worst_improvement: float
    benchmark_results: List[BenchmarkResult]
    recommendations: List[str]

class PartitioningBenchmarker:
    """
    Benchmarker for measuring partitioning performance improvements.
    
    Follows Arxos logging standards with structured logging, performance monitoring,
    and comprehensive analysis of query performance.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the partitioning benchmarker.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.connection = None
        self.benchmark_results = None
        
        # Performance tracking
        self.metrics = {
            'queries_executed': 0,
            'total_execution_time_ms': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Benchmark queries
        self.benchmark_queries = {
            'time_range_queries': [
                {
                    'name': 'recent_audit_logs',
                    'query': """
                        SELECT * FROM audit_logs 
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                        ORDER BY created_at DESC
                        LIMIT 1000
                    """,
                    'table': 'audit_logs'
                },
                {
                    'name': 'monthly_audit_logs',
                    'query': """
                        SELECT * FROM audit_logs 
                        WHERE created_at >= DATE_TRUNC('month', NOW())
                        ORDER BY created_at DESC
                    """,
                    'table': 'audit_logs'
                },
                {
                    'name': 'recent_object_history',
                    'query': """
                        SELECT * FROM object_history 
                        WHERE changed_at >= NOW() - INTERVAL '30 days'
                        ORDER BY changed_at DESC
                        LIMIT 1000
                    """,
                    'table': 'object_history'
                },
                {
                    'name': 'slow_queries_critical',
                    'query': """
                        SELECT * FROM slow_query_log 
                        WHERE severity = 'critical' 
                        AND timestamp >= NOW() - INTERVAL '7 days'
                        ORDER BY duration_ms DESC
                    """,
                    'table': 'slow_query_log'
                }
            ],
            'aggregation_queries': [
                {
                    'name': 'audit_logs_by_action',
                    'query': """
                        SELECT action, COUNT(*) as count
                        FROM audit_logs 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY action
                        ORDER BY count DESC
                    """,
                    'table': 'audit_logs'
                },
                {
                    'name': 'object_history_by_type',
                    'query': """
                        SELECT object_type, change_type, COUNT(*) as count
                        FROM object_history 
                        WHERE changed_at >= NOW() - INTERVAL '30 days'
                        GROUP BY object_type, change_type
                        ORDER BY count DESC
                    """,
                    'table': 'object_history'
                },
                {
                    'name': 'slow_queries_by_severity',
                    'query': """
                        SELECT severity, COUNT(*) as count, AVG(duration_ms) as avg_duration
                        FROM slow_query_log 
                        WHERE timestamp >= NOW() - INTERVAL '7 days'
                        GROUP BY severity
                        ORDER BY count DESC
                    """,
                    'table': 'slow_query_log'
                }
            ],
            'filtering_queries': [
                {
                    'name': 'audit_logs_by_user',
                    'query': """
                        SELECT * FROM audit_logs 
                        WHERE user_id = 1 
                        AND created_at >= NOW() - INTERVAL '30 days'
                        ORDER BY created_at DESC
                    """,
                    'table': 'audit_logs'
                },
                {
                    'name': 'object_history_by_object',
                    'query': """
                        SELECT * FROM object_history 
                        WHERE object_id = 'room_123' 
                        AND changed_at >= NOW() - INTERVAL '90 days'
                        ORDER BY changed_at DESC
                    """,
                    'table': 'object_history'
                },
                {
                    'name': 'slow_queries_by_duration',
                    'query': """
                        SELECT * FROM slow_query_log 
                        WHERE duration_ms > 1000 
                        AND timestamp >= NOW() - INTERVAL '7 days'
                        ORDER BY duration_ms DESC
                    """,
                    'table': 'slow_query_log'
                }
            ]
        }
        
        logger.info("partitioning_benchmarker_initialized",
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
    
    def run_benchmarks(self) -> bool:
        """
        Run comprehensive performance benchmarks.
        
        Returns:
            True if benchmarks successful, False otherwise
        """
        start_time = datetime.now()
        
        if not self.connect():
            return False
        
        try:
            logger.info("starting_partitioning_benchmarks")
            
            # Get database information
            db_info = self._get_database_info()
            
            # Run benchmarks for each query type
            benchmark_results = []
            
            for query_type, queries in self.benchmark_queries.items():
                logger.info("benchmarking_query_type",
                           query_type=query_type,
                           query_count=len(queries))
                
                for query_info in queries:
                    result = self._benchmark_query(query_info, query_type)
                    if result:
                        benchmark_results.append(result)
                        self.metrics['queries_executed'] += 1
            
            # Generate benchmark summary
            self.benchmark_results = self._generate_benchmark_summary(
                db_info, benchmark_results)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['total_execution_time_ms'] = processing_time
            
            logger.info("partitioning_benchmarks_completed",
                       queries_executed=self.metrics['queries_executed'],
                       processing_time_ms=round(processing_time, 2))
            
            return True
            
        except Exception as e:
            logger.error("partitioning_benchmarks_failed",
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
    
    def _benchmark_query(self, query_info: Dict[str, Any], query_type: str) -> Optional[BenchmarkResult]:
        """
        Benchmark a single query before and after partitioning.
        
        Args:
            query_info: Query information
            query_type: Type of query being benchmarked
            
        Returns:
            BenchmarkResult object with before/after comparison
        """
        try:
            query_name = query_info['name']
            query_sql = query_info['query']
            table_name = query_info['table']
            
            logger.debug("benchmarking_query",
                        query_name=query_name,
                        table_name=table_name)
            
            # Test original table (before partitioning)
            before_result = self._execute_query_with_metrics(
                query_sql, table_name, "before")
            
            # Test partitioned table (after partitioning)
            partitioned_query = self._adapt_query_for_partitioning(query_sql, table_name)
            after_result = self._execute_query_with_metrics(
                partitioned_query, f"{table_name}_partitioned", "after")
            
            if before_result and after_result:
                # Calculate improvement
                improvement_percentage = self._calculate_improvement(
                    before_result.execution_time_ms, after_result.execution_time_ms)
                improvement_factor = before_result.execution_time_ms / after_result.execution_time_ms
                
                return BenchmarkResult(
                    benchmark_name=query_name,
                    table_name=table_name,
                    query_type=query_type,
                    before_result=before_result,
                    after_result=after_result,
                    improvement_percentage=improvement_percentage,
                    improvement_factor=improvement_factor
                )
            
            return None
            
        except Exception as e:
            logger.error("failed_to_benchmark_query",
                        query_name=query_info.get('name', 'unknown'),
                        error=str(e))
            self.metrics['errors'] += 1
            return None
    
    def _execute_query_with_metrics(self, query_sql: str, table_name: str, phase: str) -> Optional[QueryResult]:
        """
        Execute a query and collect performance metrics.
        
        Args:
            query_sql: SQL query to execute
            table_name: Name of the table being queried
            phase: 'before' or 'after' partitioning
            
        Returns:
            QueryResult with performance metrics
        """
        try:
            # Enable query statistics
            with self.connection.cursor() as cursor:
                cursor.execute("SET track_io_timing = ON")
                cursor.execute("SET track_functions = ALL")
            
            # Execute query with timing
            start_time = time.time()
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query_sql)
                results = cursor.fetchall()
                
                # Get execution plan
                cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_sql}")
                plan_result = cursor.fetchone()
                execution_plan = plan_result[0] if plan_result else None
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Extract metrics from execution plan
            plan_metrics = self._extract_plan_metrics(execution_plan)
            
            return QueryResult(
                query_name=f"{table_name}_{phase}",
                table_name=table_name,
                execution_time_ms=execution_time_ms,
                row_count=len(results),
                plan_type=plan_metrics.get('plan_type', 'unknown'),
                buffer_hits=plan_metrics.get('buffer_hits', 0),
                buffer_reads=plan_metrics.get('buffer_reads', 0),
                cache_hit_ratio=plan_metrics.get('cache_hit_ratio', 0.0),
                partition_used=plan_metrics.get('partition_used')
            )
            
        except Exception as e:
            logger.error("failed_to_execute_query",
                        table_name=table_name,
                        phase=phase,
                        error=str(e))
            return None
    
    def _extract_plan_metrics(self, execution_plan: Optional[Dict]) -> Dict[str, Any]:
        """Extract performance metrics from execution plan."""
        if not execution_plan:
            return {}
        
        try:
            # Extract basic metrics
            plan_type = 'unknown'
            buffer_hits = 0
            buffer_reads = 0
            partition_used = None
            
            # Analyze plan structure
            if 'Plan' in execution_plan:
                plan = execution_plan['Plan']
                
                # Determine plan type
                if 'Node Type' in plan:
                    node_type = plan['Node Type']
                    if 'Seq Scan' in node_type:
                        plan_type = 'seq_scan'
                    elif 'Index Scan' in node_type:
                        plan_type = 'index_scan'
                    elif 'Partition' in node_type:
                        plan_type = 'partition_scan'
                
                # Extract buffer metrics
                if 'Shared Hit Blocks' in plan:
                    buffer_hits = plan['Shared Hit Blocks']
                if 'Shared Read Blocks' in plan:
                    buffer_reads = plan['Shared Read Blocks']
                
                # Calculate cache hit ratio
                total_blocks = buffer_hits + buffer_reads
                cache_hit_ratio = buffer_hits / total_blocks if total_blocks > 0 else 0.0
            
            return {
                'plan_type': plan_type,
                'buffer_hits': buffer_hits,
                'buffer_reads': buffer_reads,
                'cache_hit_ratio': cache_hit_ratio,
                'partition_used': partition_used
            }
            
        except Exception as e:
            logger.warning("failed_to_extract_plan_metrics",
                          error=str(e))
            return {}
    
    def _adapt_query_for_partitioning(self, query_sql: str, table_name: str) -> str:
        """
        Adapt query to use partitioned table.
        
        Args:
            query_sql: Original query SQL
            table_name: Original table name
            
        Returns:
            Modified query SQL for partitioned table
        """
        # Replace table name with partitioned version
        partitioned_table = f"{table_name}_partitioned"
        return query_sql.replace(table_name, partitioned_table)
    
    def _calculate_improvement(self, before_time: float, after_time: float) -> float:
        """Calculate performance improvement percentage."""
        if before_time == 0:
            return 0.0
        
        improvement = ((before_time - after_time) / before_time) * 100
        return round(improvement, 2)
    
    def _generate_benchmark_summary(self, db_info: Dict[str, Any], benchmark_results: List[BenchmarkResult]) -> BenchmarkSummary:
        """Generate summary of all benchmark results."""
        if not benchmark_results:
            return BenchmarkSummary(
                benchmark_timestamp=datetime.now(),
                database_name=db_info['database_name'],
                total_queries=0,
                total_improvement=0.0,
                average_improvement=0.0,
                best_improvement=0.0,
                worst_improvement=0.0,
                benchmark_results=[],
                recommendations=[]
            )
        
        # Calculate summary statistics
        improvements = [r.improvement_percentage for r in benchmark_results]
        total_improvement = sum(improvements)
        average_improvement = total_improvement / len(improvements)
        best_improvement = max(improvements)
        worst_improvement = min(improvements)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(benchmark_results)
        
        return BenchmarkSummary(
            benchmark_timestamp=datetime.now(),
            database_name=db_info['database_name'],
            total_queries=len(benchmark_results),
            total_improvement=total_improvement,
            average_improvement=average_improvement,
            best_improvement=best_improvement,
            worst_improvement=worst_improvement,
            benchmark_results=benchmark_results,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, benchmark_results: List[BenchmarkResult]) -> List[str]:
        """Generate recommendations based on benchmark results."""
        recommendations = []
        
        # Analyze overall performance
        improvements = [r.improvement_percentage for r in benchmark_results]
        avg_improvement = sum(improvements) / len(improvements)
        
        if avg_improvement > 50:
            recommendations.append("Excellent performance improvement - partitioning is highly effective")
        elif avg_improvement > 20:
            recommendations.append("Good performance improvement - partitioning provides benefits")
        elif avg_improvement > 0:
            recommendations.append("Modest performance improvement - consider query optimization")
        else:
            recommendations.append("No performance improvement - review partitioning strategy")
        
        # Analyze by query type
        query_type_results = {}
        for result in benchmark_results:
            if result.query_type not in query_type_results:
                query_type_results[result.query_type] = []
            query_type_results[result.query_type].append(result.improvement_percentage)
        
        for query_type, improvements in query_type_results.items():
            avg_improvement = sum(improvements) / len(improvements)
            recommendations.append(f"{query_type}: {avg_improvement:.1f}% average improvement")
        
        # Identify best and worst performing queries
        best_query = max(benchmark_results, key=lambda r: r.improvement_percentage)
        worst_query = min(benchmark_results, key=lambda r: r.improvement_percentage)
        
        recommendations.append(f"Best performing query: {best_query.benchmark_name} ({best_query.improvement_percentage:.1f}% improvement)")
        recommendations.append(f"Worst performing query: {worst_query.benchmark_name} ({worst_query.improvement_percentage:.1f}% improvement)")
        
        return recommendations
    
    def generate_report(self, output_format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Generate benchmark report in specified format.
        
        Args:
            output_format: 'json' or 'markdown'
            output_file: Optional output file path
            
        Returns:
            Generated report content
        """
        if not self.benchmark_results:
            logger.warning("no_benchmark_results_to_report")
            return ""
        
        logger.info("generating_benchmark_report",
                   format=output_format,
                   total_queries=self.benchmark_results.total_queries)
        
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
                'benchmark_timestamp': self.benchmark_results.benchmark_timestamp.isoformat(),
                'database_name': self.benchmark_results.database_name,
                'total_queries': self.benchmark_results.total_queries,
                'processing_metrics': self.metrics
            },
            'summary': {
                'total_improvement': self.benchmark_results.total_improvement,
                'average_improvement': self.benchmark_results.average_improvement,
                'best_improvement': self.benchmark_results.best_improvement,
                'worst_improvement': self.benchmark_results.worst_improvement,
                'recommendations': self.benchmark_results.recommendations
            },
            'benchmark_results': [asdict(result) for result in self.benchmark_results.benchmark_results]
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
        content = f"""# Table Partitioning Performance Benchmark Report

**Generated:** {self.benchmark_results.benchmark_timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Database:** {self.benchmark_results.database_name}  
**Total Queries:** {self.benchmark_results.total_queries}

## Executive Summary

- **Average Improvement:** {self.benchmark_results.average_improvement:.1f}%
- **Best Improvement:** {self.benchmark_results.best_improvement:.1f}%
- **Worst Improvement:** {self.benchmark_results.worst_improvement:.1f}%
- **Total Improvement:** {self.benchmark_results.total_improvement:.1f}%

## Performance Recommendations

"""
        
        for rec in self.benchmark_results.recommendations:
            content += f"- {rec}\n"
        
        content += "\n## Detailed Benchmark Results\n\n"
        
        for result in self.benchmark_results.benchmark_results:
            content += f"### {result.benchmark_name.title()}\n\n"
            content += f"- **Table:** {result.table_name}\n"
            content += f"- **Query Type:** {result.query_type}\n"
            content += f"- **Improvement:** {result.improvement_percentage:.1f}% ({result.improvement_factor:.2f}x faster)\n\n"
            
            content += "#### Before Partitioning\n"
            content += f"- **Execution Time:** {result.before_result.execution_time_ms:.2f}ms\n"
            content += f"- **Row Count:** {result.before_result.row_count}\n"
            content += f"- **Plan Type:** {result.before_result.plan_type}\n"
            content += f"- **Cache Hit Ratio:** {result.before_result.cache_hit_ratio:.2f}\n\n"
            
            content += "#### After Partitioning\n"
            content += f"- **Execution Time:** {result.after_result.execution_time_ms:.2f}ms\n"
            content += f"- **Row Count:** {result.after_result.row_count}\n"
            content += f"- **Plan Type:** {result.after_result.plan_type}\n"
            content += f"- **Cache Hit Ratio:** {result.after_result.cache_hit_ratio:.2f}\n\n"
            
            if result.after_result.partition_used:
                content += f"- **Partition Used:** {result.after_result.partition_used}\n\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("markdown_report_saved",
                       file=output_file)
        
        return content


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Benchmark table partitioning performance"
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
    
    # Run benchmarks
    benchmarker = PartitioningBenchmarker(args.database_url)
    success = benchmarker.run_benchmarks()
    
    if success:
        # Generate report
        report_content = benchmarker.generate_report(
            output_format=args.output_format,
            output_file=args.output_file
        )
        
        # Print summary
        if benchmarker.benchmark_results:
            print("\n" + "="*60)
            print("PARTITIONING BENCHMARK SUMMARY")
            print("="*60)
            print(f"Total queries: {benchmarker.benchmark_results.total_queries}")
            print(f"Average improvement: {benchmarker.benchmark_results.average_improvement:.1f}%")
            print(f"Best improvement: {benchmarker.benchmark_results.best_improvement:.1f}%")
            print(f"Worst improvement: {benchmarker.benchmark_results.worst_improvement:.1f}%")
            print("\nRecommendations:")
            for rec in benchmarker.benchmark_results.recommendations:
                print(f"- {rec}")
            print("="*60)
        
        # Print report if no output file specified
        if not args.output_file and report_content:
            print("\n" + report_content)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 