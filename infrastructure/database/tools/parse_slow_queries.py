#!/usr/bin/env python3
"""
Slow Query Log Parser for Arxos Database Performance Tuning

This script parses PostgreSQL slow query logs to identify performance bottlenecks
and generate actionable insights for database optimization.

Features:
- Parse timestamps, durations, and statements from log files
- Rank queries by execution time and frequency
- Generate CSV and JSON reports for performance review
- Structured logging following Arxos standards
- Performance monitoring and metrics collection

Usage:
    python parse_slow_queries.py [log_directory] [--output-format json|csv]
    python parse_slow_queries.py --help
"""

import os
import sys
import re
import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import structlog
from dateutil import parser as date_parser
import pandas as pd

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)


@dataclass
class SlowQuery:
    """Represents a parsed slow query entry."""

    timestamp: datetime
    duration_ms: int
    statement: str
    user: Optional[str] = None
    database: Optional[str] = None
    application: Optional[str] = None
    client_ip: Optional[str] = None
    process_id: Optional[str] = None
    session_id: Optional[str] = None
    query_hash: Optional[str] = None
    execution_plan: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Generate query hash for deduplication."""
        if not self.query_hash:
            import hashlib

            normalized_query = re.sub(r"\s+", " ", self.statement.strip()).lower()
            self.query_hash = hashlib.md5(normalized_query.encode()).hexdigest()[:8]


@dataclass
class QueryAnalysis:
    """Analysis results for a query pattern."""

    query_hash: str
    sample_statement: str
    total_executions: int
    avg_duration_ms: float
    max_duration_ms: int
    min_duration_ms: int
    total_duration_ms: int
    frequency_per_hour: float
    last_seen: datetime
    first_seen: datetime
    users: Set[str]
    databases: Set[str]
    applications: Set[str]
    severity: str  # 'critical', 'warning', 'info'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query_hash": self.query_hash,
            "sample_statement": self.sample_statement,
            "total_executions": self.total_executions,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "max_duration_ms": self.max_duration_ms,
            "min_duration_ms": self.min_duration_ms,
            "total_duration_ms": self.total_duration_ms,
            "frequency_per_hour": round(self.frequency_per_hour, 2),
            "last_seen": self.last_seen.isoformat(),
            "first_seen": self.first_seen.isoformat(),
            "users": list(self.users),
            "databases": list(self.databases),
            "applications": list(self.applications),
            "severity": self.severity,
        }


class SlowQueryParser:
    """
    Parser for PostgreSQL slow query logs with performance analysis.

    Follows Arxos logging standards with structured logging, performance monitoring,
    and comprehensive error handling.
    """

    def __init__(self, log_directory: str = "pg_log"):
        """
        Initialize the slow query parser.

        Args:
            log_directory: Directory containing PostgreSQL log files
        """
        self.log_directory = Path(log_directory)
        self.queries: List[SlowQuery] = []
        self.analysis_results: List[QueryAnalysis] = []

        # Performance tracking
        self.metrics = {
            "total_logs_processed": 0,
            "total_queries_found": 0,
            "processing_time_ms": 0,
            "errors": 0,
            "warnings": 0,
            "files_processed": 0,
        }

        # Regex patterns for parsing PostgreSQL slow query logs
        self.log_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}) \[(\d+)\]: \[(\d+)-(\d+)\] "
            r"user=([^,]+),db=([^,]+),app=([^,]+),client=([^ ]+) "
            r"duration: (\d+\.?\d*) ms  statement: (.+)",
            re.DOTALL,
        )

        # Alternative pattern for different log formats
        self.alt_log_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}) \[(\d+)\] "
            r"user=([^,]+),db=([^,]+),app=([^,]+),client=([^ ]+) "
            r"duration: (\d+\.?\d*) ms  (.+)",
            re.DOTALL,
        )

        logger.info(
            "slow_query_parser_initialized",
            log_directory=str(self.log_directory),
            patterns_configured=2,
        )

    def parse_log_files(self, file_pattern: str = "postgresql-slow-*.log") -> bool:
        """
        Parse all slow query log files in the directory.

        Args:
            file_pattern: Glob pattern for log files

        Returns:
            True if parsing was successful, False otherwise
        """
        start_time = datetime.now()

        if not self.log_directory.exists():
            logger.error("log_directory_not_found", path=str(self.log_directory))
            return False

        # Find all matching log files
        log_files = list(self.log_directory.glob(file_pattern))
        log_files.sort()  # Process in chronological order

        if not log_files:
            logger.warning(
                "no_log_files_found",
                pattern=file_pattern,
                directory=str(self.log_directory),
            )
            return True

        logger.info(
            "found_log_files", count=len(log_files), files=[f.name for f in log_files]
        )

        # Process each log file
        for log_file in log_files:
            try:
                self._parse_single_log_file(log_file)
                self.metrics["files_processed"] += 1
            except Exception as e:
                logger.error(
                    "failed_to_parse_log_file", file=str(log_file), error=str(e)
                )
                self.metrics["errors"] += 1

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics["processing_time_ms"] = processing_time

        logger.info(
            "log_parsing_completed",
            total_files=self.metrics["files_processed"],
            total_queries=self.metrics["total_queries_found"],
            processing_time_ms=round(processing_time, 2),
            errors=self.metrics["errors"],
        )

        return True

    def _parse_single_log_file(self, log_file: Path) -> None:
        """
        Parse a single log file.

        Args:
            log_file: Path to the log file to parse
        """
        logger.debug("parsing_log_file", file=str(log_file))

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Split content into lines and process each line
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                self.metrics["total_logs_processed"] += 1

                # Skip empty lines and comments
                if not line.strip() or line.strip().startswith("#"):
                    continue

                # Try to parse the line as a slow query log entry
                query = self._parse_log_line(line, line_num)
                if query:
                    self.queries.append(query)
                    self.metrics["total_queries_found"] += 1

                    logger.debug(
                        "parsed_slow_query",
                        duration_ms=query.duration_ms,
                        user=query.user,
                        database=query.database,
                        line=line_num,
                    )

        except Exception as e:
            logger.error("failed_to_read_log_file", file=str(log_file), error=str(e))
            raise

    def _parse_log_line(self, line: str, line_num: int) -> Optional[SlowQuery]:
        """
        Parse a single log line to extract slow query information.

        Args:
            line: The log line to parse
            line_num: Line number for error reporting

        Returns:
            SlowQuery object if parsing successful, None otherwise
        """
        try:
            # Try primary pattern first
            match = self.log_pattern.match(line)
            if match:
                return self._create_query_from_match(match, line_num)

            # Try alternative pattern
            match = self.alt_log_pattern.match(line)
            if match:
                return self._create_query_from_alt_match(match, line_num)

            # If no pattern matches, log as warning
            if line.strip() and not line.strip().startswith("#"):
                logger.warning(
                    "unparseable_log_line",
                    line_number=line_num,
                    line_preview=line[:100],
                )
                self.metrics["warnings"] += 1

            return None

        except Exception as e:
            logger.error(
                "failed_to_parse_line",
                line_number=line_num,
                line_preview=line[:100],
                error=str(e),
            )
            self.metrics["errors"] += 1
            return None

    def _create_query_from_match(self, match, line_num: int) -> SlowQuery:
        """Create SlowQuery object from regex match."""
        (
            timestamp_str,
            process_id,
            session_id,
            _,
            user,
            database,
            application,
            client_ip,
            duration_str,
            statement,
        ) = match.groups()

        try:
            timestamp = date_parser.parse(timestamp_str)
            duration_ms = int(float(duration_str))

            return SlowQuery(
                timestamp=timestamp,
                duration_ms=duration_ms,
                statement=statement.strip(),
                user=user,
                database=database,
                application=application,
                client_ip=client_ip,
                process_id=process_id,
                session_id=session_id,
            )
        except Exception as e:
            logger.error("failed_to_create_query", line_number=line_num, error=str(e))
            raise

    def _create_query_from_alt_match(self, match, line_num: int) -> SlowQuery:
        """Create SlowQuery object from alternative regex match."""
        (
            timestamp_str,
            process_id,
            user,
            database,
            application,
            client_ip,
            duration_str,
            statement,
        ) = match.groups()

        try:
            timestamp = date_parser.parse(timestamp_str)
            duration_ms = int(float(duration_str))

            return SlowQuery(
                timestamp=timestamp,
                duration_ms=duration_ms,
                statement=statement.strip(),
                user=user,
                database=database,
                application=application,
                client_ip=client_ip,
                process_id=process_id,
            )
        except Exception as e:
            logger.error(
                "failed_to_create_query_alt", line_number=line_num, error=str(e)
            )
            raise

    def analyze_queries(self) -> None:
        """
        Analyze parsed queries to identify patterns and performance issues.
        """
        if not self.queries:
            logger.warning("no_queries_to_analyze")
            return

        logger.info("starting_query_analysis", total_queries=len(self.queries))

        # Group queries by hash
        query_groups = defaultdict(list)
        for query in self.queries:
            query_groups[query.query_hash].append(query)

        # Analyze each query group
        for query_hash, queries in query_groups.items():
            analysis = self._analyze_query_group(query_hash, queries)
            self.analysis_results.append(analysis)

        # Sort by severity and impact
        self.analysis_results.sort(
            key=lambda x: (self._severity_score(x.severity), x.total_duration_ms),
            reverse=True,
        )

        logger.info(
            "query_analysis_completed",
            total_patterns=len(self.analysis_results),
            critical_queries=len(
                [q for q in self.analysis_results if q.severity == "critical"]
            ),
            warning_queries=len(
                [q for q in self.analysis_results if q.severity == "warning"]
            ),
        )

    def _analyze_query_group(
        self, query_hash: str, queries: List[SlowQuery]
    ) -> QueryAnalysis:
        """
        Analyze a group of similar queries.

        Args:
            query_hash: Hash identifying the query pattern
            queries: List of similar queries

        Returns:
            QueryAnalysis object with analysis results
        """
        durations = [q.duration_ms for q in queries]
        timestamps = [q.timestamp for q in queries]

        # Calculate time span for frequency calculation
        time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600
        frequency_per_hour = len(queries) / max(time_span_hours, 1)

        # Determine severity based on duration and frequency
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        if max_duration > 5000 or (avg_duration > 1000 and frequency_per_hour > 10):
            severity = "critical"
        elif max_duration > 1000 or (avg_duration > 500 and frequency_per_hour > 5):
            severity = "warning"
        else:
            severity = "info"

        return QueryAnalysis(
            query_hash=query_hash,
            sample_statement=queries[0].statement,
            total_executions=len(queries),
            avg_duration_ms=avg_duration,
            max_duration_ms=max_duration,
            min_duration_ms=min(durations),
            total_duration_ms=sum(durations),
            frequency_per_hour=frequency_per_hour,
            last_seen=max(timestamps),
            first_seen=min(timestamps),
            users=set(q.user for q in queries if q.user),
            databases=set(q.database for q in queries if q.database),
            applications=set(q.application for q in queries if q.application),
            severity=severity,
        )

    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score for sorting."""
        return {"critical": 3, "warning": 2, "info": 1}.get(severity, 0)

    def generate_report(
        self, output_format: str = "json", output_file: Optional[str] = None
    ) -> str:
        """
        Generate performance report in specified format.

        Args:
            output_format: 'json' or 'csv'
            output_file: Optional output file path

        Returns:
            Generated report content
        """
        if not self.analysis_results:
            logger.warning("no_analysis_results_to_report")
            return ""

        logger.info(
            "generating_performance_report",
            format=output_format,
            total_queries=len(self.analysis_results),
        )

        if output_format.lower() == "json":
            return self._generate_json_report(output_file)
        elif output_format.lower() == "csv":
            return self._generate_csv_report(output_file)
        else:
            logger.error("unsupported_output_format", format=output_format)
            return ""

    def _generate_json_report(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format report."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_queries_analyzed": len(self.queries),
                "total_patterns_found": len(self.analysis_results),
                "processing_metrics": self.metrics,
            },
            "summary": {
                "critical_queries": len(
                    [q for q in self.analysis_results if q.severity == "critical"]
                ),
                "warning_queries": len(
                    [q for q in self.analysis_results if q.severity == "warning"]
                ),
                "info_queries": len(
                    [q for q in self.analysis_results if q.severity == "info"]
                ),
                "total_duration_ms": sum(
                    q.total_duration_ms for q in self.analysis_results
                ),
            },
            "queries": [q.to_dict() for q in self.analysis_results],
        }

        content = json.dumps(report, indent=2, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(content)
            logger.info("json_report_saved", file=output_file)

        return content

    def _generate_csv_report(self, output_file: Optional[str] = None) -> str:
        """Generate CSV format report."""
        if not self.analysis_results:
            return ""

        # Create CSV content
        output = []
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Query Hash",
                "Sample Statement",
                "Total Executions",
                "Avg Duration (ms)",
                "Max Duration (ms)",
                "Min Duration (ms)",
                "Total Duration (ms)",
                "Frequency per Hour",
                "Last Seen",
                "First Seen",
                "Users",
                "Databases",
                "Applications",
                "Severity",
            ]
        )

        # Write data rows
        for analysis in self.analysis_results:
            writer.writerow(
                [
                    analysis.query_hash,
                    (
                        analysis.sample_statement[:100] + "..."
                        if len(analysis.sample_statement) > 100
                        else analysis.sample_statement
                    ),
                    analysis.total_executions,
                    round(analysis.avg_duration_ms, 2),
                    analysis.max_duration_ms,
                    analysis.min_duration_ms,
                    analysis.total_duration_ms,
                    round(analysis.frequency_per_hour, 2),
                    analysis.last_seen.isoformat(),
                    analysis.first_seen.isoformat(),
                    ";".join(analysis.users),
                    ";".join(analysis.databases),
                    ";".join(analysis.applications),
                    analysis.severity,
                ]
            )

        content = "".join(output)

        if output_file:
            with open(output_file, "w", newline="") as f:
                f.write(content)
            logger.info("csv_report_saved", file=output_file)

        return content

    def get_performance_insights(self) -> Dict[str, Any]:
        """
        Generate actionable performance insights.

        Returns:
            Dictionary with performance insights and recommendations
        """
        if not self.analysis_results:
            return {}

        critical_queries = [
            q for q in self.analysis_results if q.severity == "critical"
        ]
        warning_queries = [q for q in self.analysis_results if q.severity == "warning"]

        insights = {
            "summary": {
                "total_queries_analyzed": len(self.queries),
                "critical_issues": len(critical_queries),
                "warning_issues": len(warning_queries),
                "total_impact_ms": sum(
                    q.total_duration_ms for q in self.analysis_results
                ),
            },
            "recommendations": [],
        }

        # Generate recommendations
        if critical_queries:
            insights["recommendations"].append(
                {
                    "priority": "high",
                    "type": "critical_queries",
                    "message": f"Found {len(critical_queries)} critical performance issues requiring immediate attention",
                    "queries": [q.query_hash for q in critical_queries[:5]],
                }
            )

        if warning_queries:
            insights["recommendations"].append(
                {
                    "priority": "medium",
                    "type": "warning_queries",
                    "message": f"Found {len(warning_queries)} queries that should be optimized",
                    "queries": [q.query_hash for q in warning_queries[:5]],
                }
            )

        # Check for frequent slow queries
        frequent_queries = [
            q for q in self.analysis_results if q.frequency_per_hour > 10
        ]
        if frequent_queries:
            insights["recommendations"].append(
                {
                    "priority": "medium",
                    "type": "frequent_queries",
                    "message": f"Found {len(frequent_queries)} frequently executed slow queries",
                    "queries": [q.query_hash for q in frequent_queries[:3]],
                }
            )

        return insights


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Parse PostgreSQL slow query logs for performance analysis"
    )
    parser.add_argument(
        "log_directory",
        nargs="?",
        default="pg_log",
        help="Directory containing PostgreSQL log files (default: pg_log)",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "csv"],
        default="json",
        help="Output format for the report (default: json)",
    )
    parser.add_argument(
        "--output-file", help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--file-pattern",
        default="postgresql-slow-*.log",
        help="File pattern for log files (default: postgresql-slow-*.log)",
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
                structlog.stdlib.PositionalArgumentsFormatter(),
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

    # Initialize parser
    parser_instance = SlowQueryParser(args.log_directory)

    # Parse log files
    if not parser_instance.parse_log_files(args.file_pattern):
        logger.error("failed_to_parse_log_files")
        sys.exit(1)

    # Analyze queries
    parser_instance.analyze_queries()

    # Generate insights
    insights = parser_instance.get_performance_insights()

    # Generate report
    report_content = parser_instance.generate_report(
        output_format=args.output_format, output_file=args.output_file
    )

    # Print insights summary
    if insights:
        print("\n" + "=" * 60)
        print("PERFORMANCE INSIGHTS SUMMARY")
        print("=" * 60)
        print(
            f"Total queries analyzed: {insights['summary']['total_queries_analyzed']}"
        )
        print(f"Critical issues: {insights['summary']['critical_issues']}")
        print(f"Warning issues: {insights['summary']['warning_issues']}")
        print(f"Total impact: {insights['summary']['total_impact_ms']} ms")
        print("\nRecommendations:")
        for rec in insights["recommendations"]:
            print(f"- [{rec['priority'].upper()}] {rec['message']}")
        print("=" * 60)

    # Print report if no output file specified
    if not args.output_file and report_content:
        print("\n" + report_content)

    logger.info(
        "slow_query_analysis_completed",
        output_format=args.output_format,
        output_file=args.output_file,
    )


if __name__ == "__main__":
    main()
