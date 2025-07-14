#!/usr/bin/env python3
"""
Weekly Slow Query Review Script for Arxos Database Performance

This script automates the weekly review of slow query logs, generating
performance reports and sending notifications to the engineering team.

Features:
- Automated weekly execution via cron or GitHub Actions
- Comprehensive performance analysis and reporting
- Integration with Arxos logging standards
- Email notifications for critical issues
- Dashboard data generation

Usage:
    python weekly_slow_query_review.py [--config config.yaml]
    python weekly_slow_query_review.py --help
"""

import os
import sys
import yaml
import argparse
import smtplib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import structlog
import psycopg2
from psycopg2.extras import RealDictCursor

# Import the slow query parser
from parse_slow_queries import SlowQueryParser, QueryAnalysis

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)

class WeeklySlowQueryReview:
    """
    Automated weekly review of slow query logs with performance analysis.
    
    Follows Arxos logging standards and integrates with existing infrastructure.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the weekly review system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.parser = SlowQueryParser(self.config.get('log_directory', 'pg_log'))
        self.report_data = {}
        
        # Performance tracking
        self.metrics = {
            'total_queries_analyzed': 0,
            'critical_issues_found': 0,
            'warning_issues_found': 0,
            'processing_time_ms': 0,
            'notifications_sent': 0,
            'reports_generated': 0
        }
        
        logger.info("weekly_review_initialized",
                   config_loaded=config_path is not None,
                   log_directory=self.config.get('log_directory'))
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'log_directory': 'pg_log',
            'output_directory': 'reports',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'arxos_db',
                'user': 'arxos_app',
                'password': os.getenv('DB_PASSWORD', '')
            },
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': os.getenv('EMAIL_USERNAME', ''),
                'password': os.getenv('EMAIL_PASSWORD', ''),
                'from_address': 'performance@arxos.com',
                'to_addresses': ['engineering@arxos.com']
            },
            'thresholds': {
                'critical_duration_ms': 5000,
                'warning_duration_ms': 1000,
                'critical_frequency_per_hour': 10,
                'warning_frequency_per_hour': 5
            },
            'retention': {
                'log_files_days': 30,
                'reports_days': 90
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
                    logger.info("config_loaded_from_file",
                               file=config_path)
            except Exception as e:
                logger.error("failed_to_load_config",
                           file=config_path,
                           error=str(e))
        
        return default_config
    
    def run_weekly_review(self) -> bool:
        """
        Execute the complete weekly review process.
        
        Returns:
            True if review completed successfully, False otherwise
        """
        start_time = datetime.now()
        
        logger.info("starting_weekly_review")
        
        try:
            # Step 1: Parse slow query logs
            if not self._parse_slow_query_logs():
                logger.error("failed_to_parse_slow_query_logs")
                return False
            
            # Step 2: Analyze queries
            self._analyze_queries()
            
            # Step 3: Generate reports
            if not self._generate_reports():
                logger.error("failed_to_generate_reports")
                return False
            
            # Step 4: Store metrics in database
            if not self._store_metrics_in_database():
                logger.error("failed_to_store_metrics")
                return False
            
            # Step 5: Send notifications
            if self.config['email']['enabled']:
                self._send_notifications()
            
            # Step 6: Cleanup old data
            self._cleanup_old_data()
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['processing_time_ms'] = processing_time
            
            logger.info("weekly_review_completed",
                       processing_time_ms=round(processing_time, 2),
                       total_queries=self.metrics['total_queries_analyzed'],
                       critical_issues=self.metrics['critical_issues_found'],
                       warning_issues=self.metrics['warning_issues_found'])
            
            return True
            
        except Exception as e:
            logger.error("weekly_review_failed",
                        error=str(e))
            return False
    
    def _parse_slow_query_logs(self) -> bool:
        """
        Parse slow query logs for the review period.
        
        Returns:
            True if parsing successful, False otherwise
        """
        # Calculate review period (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        logger.info("parsing_slow_query_logs",
                   start_date=start_date.isoformat(),
                   end_date=end_date.isoformat())
        
        # Parse log files
        if not self.parser.parse_log_files():
            return False
        
        # Filter queries for the review period
        self.parser.queries = [
            q for q in self.parser.queries
            if start_date <= q.timestamp <= end_date
        ]
        
        self.metrics['total_queries_analyzed'] = len(self.parser.queries)
        
        logger.info("slow_query_logs_parsed",
                   total_queries=len(self.parser.queries))
        
        return True
    
    def _analyze_queries(self) -> None:
        """Analyze parsed queries for performance issues."""
        logger.info("analyzing_queries")
        
        self.parser.analyze_queries()
        
        # Count issues by severity
        for analysis in self.parser.analysis_results:
            if analysis.severity == 'critical':
                self.metrics['critical_issues_found'] += 1
            elif analysis.severity == 'warning':
                self.metrics['warning_issues_found'] += 1
        
        logger.info("query_analysis_completed",
                   total_patterns=len(self.parser.analysis_results),
                   critical_issues=self.metrics['critical_issues_found'],
                   warning_issues=self.metrics['warning_issues_found'])
    
    def _generate_reports(self) -> bool:
        """
        Generate comprehensive performance reports.
        
        Returns:
            True if reports generated successfully, False otherwise
        """
        try:
            output_dir = Path(self.config['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp for report files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate JSON report
            json_report_path = output_dir / f"slow_query_report_{timestamp}.json"
            self.parser.generate_report('json', str(json_report_path))
            
            # Generate CSV report
            csv_report_path = output_dir / f"slow_query_report_{timestamp}.csv"
            self.parser.generate_report('csv', str(csv_report_path))
            
            # Generate summary report
            summary_report_path = output_dir / f"performance_summary_{timestamp}.md"
            self._generate_summary_report(summary_report_path)
            
            # Store report metadata
            self.report_data = {
                'timestamp': timestamp,
                'json_report': str(json_report_path),
                'csv_report': str(csv_report_path),
                'summary_report': str(summary_report_path),
                'total_queries': self.metrics['total_queries_analyzed'],
                'critical_issues': self.metrics['critical_issues_found'],
                'warning_issues': self.metrics['warning_issues_found']
            }
            
            self.metrics['reports_generated'] = 3
            
            logger.info("reports_generated",
                       json_report=str(json_report_path),
                       csv_report=str(csv_report_path),
                       summary_report=str(summary_report_path))
            
            return True
            
        except Exception as e:
            logger.error("failed_to_generate_reports",
                        error=str(e))
            return False
    
    def _generate_summary_report(self, output_path: Path) -> None:
        """
        Generate a human-readable summary report.
        
        Args:
            output_path: Path to output file
        """
        with open(output_path, 'w') as f:
            f.write("# Arxos Database Performance Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Period:** Last 7 days\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Queries Analyzed:** {self.metrics['total_queries_analyzed']}\n")
            f.write(f"- **Critical Issues:** {self.metrics['critical_issues_found']}\n")
            f.write(f"- **Warning Issues:** {self.metrics['warning_issues_found']}\n")
            f.write(f"- **Processing Time:** {self.metrics['processing_time_ms']:.2f} ms\n\n")
            
            if self.parser.analysis_results:
                f.write("## Critical Performance Issues\n\n")
                critical_queries = [q for q in self.parser.analysis_results if q.severity == 'critical']
                for i, query in enumerate(critical_queries[:5], 1):
                    f.write(f"### Issue {i}\n")
                    f.write(f"- **Query Hash:** {query.query_hash}\n")
                    f.write(f"- **Average Duration:** {query.avg_duration_ms:.2f} ms\n")
                    f.write(f"- **Max Duration:** {query.max_duration_ms} ms\n")
                    f.write(f"- **Frequency:** {query.frequency_per_hour:.2f} per hour\n")
                    f.write(f"- **Total Executions:** {query.total_executions}\n")
                    f.write(f"- **Sample Query:**\n```sql\n{query.sample_statement[:200]}...\n```\n\n")
                
                f.write("## Warning Performance Issues\n\n")
                warning_queries = [q for q in self.parser.analysis_results if q.severity == 'warning']
                for i, query in enumerate(warning_queries[:3], 1):
                    f.write(f"### Issue {i}\n")
                    f.write(f"- **Query Hash:** {query.query_hash}\n")
                    f.write(f"- **Average Duration:** {query.avg_duration_ms:.2f} ms\n")
                    f.write(f"- **Frequency:** {query.frequency_per_hour:.2f} per hour\n")
                    f.write(f"- **Sample Query:**\n```sql\n{query.sample_statement[:150]}...\n```\n\n")
            
            f.write("## Recommendations\n\n")
            if self.metrics['critical_issues_found'] > 0:
                f.write("1. **Immediate Action Required:** Address critical performance issues\n")
                f.write("2. **Query Optimization:** Review and optimize slow queries\n")
                f.write("3. **Index Analysis:** Consider adding missing indexes\n")
            elif self.metrics['warning_issues_found'] > 0:
                f.write("1. **Monitor Warning Issues:** Keep track of warning-level queries\n")
                f.write("2. **Proactive Optimization:** Consider optimizing warning queries\n")
            else:
                f.write("1. **Good Performance:** No critical issues found\n")
                f.write("2. **Continue Monitoring:** Maintain current performance levels\n")
    
    def _store_metrics_in_database(self) -> bool:
        """
        Store analysis results in the database for trend tracking.
        
        Returns:
            True if storage successful, False otherwise
        """
        try:
            db_config = self.config['database']
            
            # Connect to database
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Store individual slow queries
                for query in self.parser.queries:
                    cursor.execute("""
                        INSERT INTO slow_query_log (
                            timestamp, duration_ms, statement, query_hash,
                            user_name, database_name, application_name,
                            client_ip, process_id, session_id, severity
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        query.timestamp, query.duration_ms, query.statement,
                        query.query_hash, query.user, query.database,
                        query.application, query.client_ip, query.process_id,
                        query.session_id, self._determine_severity(query.duration_ms)
                    ))
                
                # Store analysis results
                for analysis in self.parser.analysis_results:
                    cursor.execute("""
                        INSERT INTO audit_logs (
                            object_type, object_id, action, payload
                        ) VALUES (%s, %s, %s, %s)
                    """, (
                        'slow_query_analysis', analysis.query_hash, 'weekly_review',
                        json.dumps({
                            'total_executions': analysis.total_executions,
                            'avg_duration_ms': analysis.avg_duration_ms,
                            'max_duration_ms': analysis.max_duration_ms,
                            'frequency_per_hour': analysis.frequency_per_hour,
                            'severity': analysis.severity,
                            'users': list(analysis.users),
                            'applications': list(analysis.applications)
                        })
                    ))
                
                conn.commit()
            
            conn.close()
            
            logger.info("metrics_stored_in_database",
                       total_queries=len(self.parser.queries),
                       total_analyses=len(self.parser.analysis_results))
            
            return True
            
        except Exception as e:
            logger.error("failed_to_store_metrics_in_database",
                        error=str(e))
            return False
    
    def _determine_severity(self, duration_ms: int) -> str:
        """
        Determine severity based on duration thresholds.
        
        Args:
            duration_ms: Query duration in milliseconds
            
        Returns:
            Severity level: 'critical', 'warning', or 'info'
        """
        thresholds = self.config['thresholds']
        
        if duration_ms >= thresholds['critical_duration_ms']:
            return 'critical'
        elif duration_ms >= thresholds['warning_duration_ms']:
            return 'warning'
        else:
            return 'info'
    
    def _send_notifications(self) -> None:
        """Send email notifications for critical issues."""
        if self.metrics['critical_issues_found'] == 0:
            logger.info("no_critical_issues_no_notification_sent")
            return
        
        try:
            email_config = self.config['email']
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = ', '.join(email_config['to_addresses'])
            msg['Subject'] = f"🚨 Arxos Database Performance Alert - {self.metrics['critical_issues_found']} Critical Issues"
            
            # Create email body
            body = self._create_email_body()
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            self.metrics['notifications_sent'] = 1
            
            logger.info("notification_sent",
                       recipients=email_config['to_addresses'],
                       critical_issues=self.metrics['critical_issues_found'])
            
        except Exception as e:
            logger.error("failed_to_send_notification",
                        error=str(e))
    
    def _create_email_body(self) -> str:
        """
        Create HTML email body with performance summary.
        
        Returns:
            HTML email content
        """
        critical_queries = [q for q in self.parser.analysis_results if q.severity == 'critical']
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .critical {{ color: #d32f2f; font-weight: bold; }}
                .warning {{ color: #f57c00; font-weight: bold; }}
                .info {{ color: #1976d2; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>🚨 Arxos Database Performance Alert</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Period:</strong> Last 7 days</p>
            
            <h3>Summary</h3>
            <ul>
                <li><strong>Total Queries Analyzed:</strong> {self.metrics['total_queries_analyzed']}</li>
                <li class="critical"><strong>Critical Issues:</strong> {self.metrics['critical_issues_found']}</li>
                <li class="warning"><strong>Warning Issues:</strong> {self.metrics['warning_issues_found']}</li>
            </ul>
            
            <h3>Critical Performance Issues</h3>
            <table>
                <tr>
                    <th>Query Hash</th>
                    <th>Avg Duration (ms)</th>
                    <th>Max Duration (ms)</th>
                    <th>Frequency/Hour</th>
                    <th>Executions</th>
                </tr>
        """
        
        for query in critical_queries[:5]:
            body += f"""
                <tr>
                    <td>{query.query_hash}</td>
                    <td>{query.avg_duration_ms:.2f}</td>
                    <td>{query.max_duration_ms}</td>
                    <td>{query.frequency_per_hour:.2f}</td>
                    <td>{query.total_executions}</td>
                </tr>
            """
        
        body += """
            </table>
            
            <h3>Recommendations</h3>
            <ul>
                <li>Review and optimize the critical queries listed above</li>
                <li>Consider adding missing indexes</li>
                <li>Monitor query performance trends</li>
                <li>Check the full report for detailed analysis</li>
            </ul>
            
            <p><em>This is an automated report from the Arxos Database Performance Monitoring System.</em></p>
        </body>
        </html>
        """
        
        return body
    
    def _cleanup_old_data(self) -> None:
        """Clean up old log files and reports."""
        try:
            # Clean up old log files
            log_dir = Path(self.config['log_directory'])
            retention_days = self.config['retention']['log_files_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.debug("deleted_old_log_file",
                               file=str(log_file))
            
            # Clean up old reports
            reports_dir = Path(self.config['output_directory'])
            retention_days = self.config['retention']['reports_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for report_file in reports_dir.glob("*.json"):
                if report_file.stat().st_mtime < cutoff_date.timestamp():
                    report_file.unlink()
                    logger.debug("deleted_old_report",
                               file=str(report_file))
            
            logger.info("cleanup_completed")
            
        except Exception as e:
            logger.error("cleanup_failed",
                        error=str(e))


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Run weekly slow query review and performance analysis"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (YAML format)"
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
    
    # Run weekly review
    reviewer = WeeklySlowQueryReview(args.config)
    success = reviewer.run_weekly_review()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 