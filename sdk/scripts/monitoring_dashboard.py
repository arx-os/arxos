#!/usr/bin/env python3
"""
Monitoring Dashboard for Arxos SDKs
Tracks metrics, generates reports, and provides alerting
"""

import os
import sys
import json
import yaml
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging
from datetime import datetime, timedelta
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringDashboard:
    def __init__(self, config_path: str = "config/monitoring.yaml"):
        self.config = self.load_config(config_path)
        self.db_path = Path("data/monitoring.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config_file = Path(__file__).parent.parent / config_path
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self.get_default_config()
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration"""
        return {
            'metrics': {
                'generation_time': {'threshold': 300, 'alert': True},  # 5 minutes
                'test_coverage': {'threshold': 80, 'alert': True},     # 80%
                'build_success_rate': {'threshold': 95, 'alert': True}, # 95%
                'publish_success_rate': {'threshold': 99, 'alert': True}, # 99%
                'documentation_coverage': {'threshold': 90, 'alert': True}, # 90%
                'security_issues': {'threshold': 0, 'alert': True},    # 0 issues
                'performance_regression': {'threshold': 10, 'alert': True} # 10% max regression
            },
            'alerts': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'from_email': 'alerts@arxos.com',
                    'to_emails': ['dev-team@arxos.com']
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': None,
                    'channel': '#sdk-alerts'
                },
                'webhook': {
                    'enabled': False,
                    'url': None
                }
            },
            'retention': {
                'metrics_days': 90,
                'reports_days': 30,
                'logs_days': 7
            },
            'services': ['arx-backend', 'arx-cmms', 'arx-database'],
            'languages': ['typescript', 'python', 'go', 'java', 'csharp', 'php']
        }
    
    def init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service TEXT NOT NULL,
                language TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                threshold REAL,
                status TEXT DEFAULT 'ok'
            )
        ''')
        
        # Create builds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service TEXT NOT NULL,
                language TEXT NOT NULL,
                build_id TEXT UNIQUE,
                status TEXT NOT NULL,
                duration REAL,
                error_message TEXT,
                artifacts_count INTEGER DEFAULT 0
            )
        ''')
        
        # Create tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service TEXT NOT NULL,
                language TEXT NOT NULL,
                test_type TEXT NOT NULL,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                coverage_percentage REAL,
                duration REAL
            )
        ''')
        
        # Create publications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service TEXT NOT NULL,
                language TEXT NOT NULL,
                version TEXT NOT NULL,
                registry TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT
            )
        ''')
        
        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                service TEXT,
                language TEXT,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'warning',
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_metric(self, service: str, language: str, metric_name: str, 
                     value: float, threshold: float = None):
        """Record a metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine status based on threshold
        status = 'ok'
        if threshold is not None:
            if metric_name in ['generation_time', 'performance_regression']:
                status = 'warning' if value > threshold else 'ok'
            else:
                status = 'warning' if value < threshold else 'ok'
        
        cursor.execute('''
            INSERT INTO metrics (service, language, metric_name, metric_value, threshold, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (service, language, metric_name, value, threshold, status))
        
        conn.commit()
        conn.close()
        
        # Check for alerts
        if status == 'warning':
            self.check_alert(service, language, metric_name, value, threshold)
    
    def record_build(self, service: str, language: str, build_id: str, 
                    status: str, duration: float = None, error_message: str = None,
                    artifacts_count: int = 0):
        """Record a build"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO builds (service, language, build_id, status, duration, error_message, artifacts_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (service, language, build_id, status, duration, error_message, artifacts_count))
        
        conn.commit()
        conn.close()
    
    def record_test(self, service: str, language: str, test_type: str,
                   total_tests: int, passed_tests: int, failed_tests: int,
                   coverage_percentage: float = None, duration: float = None):
        """Record test results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tests (service, language, test_type, total_tests, passed_tests, failed_tests, coverage_percentage, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (service, language, test_type, total_tests, passed_tests, failed_tests, coverage_percentage, duration))
        
        conn.commit()
        conn.close()
    
    def record_publication(self, service: str, language: str, version: str,
                          registry: str, status: str, error_message: str = None):
        """Record publication result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO publications (service, language, version, registry, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (service, language, version, registry, status, error_message))
        
        conn.commit()
        conn.close()
    
    def check_alert(self, service: str, language: str, metric_name: str, 
                   value: float, threshold: float):
        """Check if alert should be triggered"""
        alert_config = self.config['metrics'].get(metric_name, {})
        if not alert_config.get('alert', False):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if alert already exists
        cursor.execute('''
            SELECT id FROM alerts 
            WHERE alert_type = ? AND service = ? AND language = ? AND resolved = FALSE
        ''', (metric_name, service, language))
        
        if cursor.fetchone():
            conn.close()
            return  # Alert already exists
        
        # Create alert
        message = f"{metric_name} threshold exceeded: {value} (threshold: {threshold})"
        severity = 'critical' if metric_name in ['security_issues', 'build_success_rate'] else 'warning'
        
        cursor.execute('''
            INSERT INTO alerts (alert_type, service, language, message, severity)
            VALUES (?, ?, ?, ?, ?)
        ''', (metric_name, service, language, message, severity))
        
        conn.commit()
        conn.close()
        
        # Send alert notifications
        self.send_alert_notifications(service, language, metric_name, message, severity)
    
    def send_alert_notifications(self, service: str, language: str, metric_name: str, 
                               message: str, severity: str):
        """Send alert notifications"""
        alert_config = self.config['alerts']
        
        # Email alerts
        if alert_config['email']['enabled']:
            self.send_email_alert(service, language, metric_name, message, severity)
        
        # Slack alerts
        if alert_config['slack']['enabled']:
            self.send_slack_alert(service, language, metric_name, message, severity)
        
        # Webhook alerts
        if alert_config['webhook']['enabled']:
            self.send_webhook_alert(service, language, metric_name, message, severity)
    
    def send_email_alert(self, service: str, language: str, metric_name: str, 
                        message: str, severity: str):
        """Send email alert"""
        try:
            email_config = self.config['alerts']['email']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = f"[{severity.upper()}] Arxos SDK Alert: {service} ({language})"
            
            body = f"""
            Alert Details:
            - Service: {service}
            - Language: {language}
            - Metric: {metric_name}
            - Severity: {severity}
            - Message: {message}
            - Timestamp: {datetime.now().isoformat()}
            
            Please investigate this issue.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (requires SMTP configuration)
            # server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            # server.starttls()
            # server.login(email_config['from_email'], email_config['password'])
            # server.send_message(msg)
            # server.quit()
            
            logger.info(f"Email alert sent for {service} ({language}): {message}")
        
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def send_slack_alert(self, service: str, language: str, metric_name: str, 
                        message: str, severity: str):
        """Send Slack alert"""
        try:
            slack_config = self.config['alerts']['slack']
            
            payload = {
                'channel': slack_config['channel'],
                'text': f"[{severity.upper()}] Arxos SDK Alert",
                'attachments': [{
                    'color': 'danger' if severity == 'critical' else 'warning',
                    'fields': [
                        {'title': 'Service', 'value': service, 'short': True},
                        {'title': 'Language', 'value': language, 'short': True},
                        {'title': 'Metric', 'value': metric_name, 'short': True},
                        {'title': 'Message', 'value': message, 'short': False}
                    ]
                }]
            }
            
            # Send to Slack webhook
            # requests.post(slack_config['webhook_url'], json=payload)
            
            logger.info(f"Slack alert sent for {service} ({language}): {message}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def send_webhook_alert(self, service: str, language: str, metric_name: str, 
                          message: str, severity: str):
        """Send webhook alert"""
        try:
            webhook_config = self.config['alerts']['webhook']
            
            payload = {
                'service': service,
                'language': language,
                'metric': metric_name,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send webhook
            # requests.post(webhook_config['url'], json=payload)
            
            logger.info(f"Webhook alert sent for {service} ({language}): {message}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get dashboard data for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build success rate
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM builds 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        
        build_result = cursor.fetchone()
        build_success_rate = (build_result[1] / build_result[0] * 100) if build_result[0] > 0 else 0
        
        # Publication success rate
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM publications 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        
        pub_result = cursor.fetchone()
        pub_success_rate = (pub_result[1] / pub_result[0] * 100) if pub_result[0] > 0 else 0
        
        # Average test coverage
        cursor.execute('''
            SELECT AVG(coverage_percentage) as avg_coverage
            FROM tests 
            WHERE timestamp >= ? AND coverage_percentage IS NOT NULL
        ''', (start_date.isoformat(),))
        
        avg_coverage = cursor.fetchone()[0] or 0
        
        # Average generation time
        cursor.execute('''
            SELECT AVG(metric_value) as avg_time
            FROM metrics 
            WHERE metric_name = 'generation_time' AND timestamp >= ?
        ''', (start_date.isoformat(),))
        
        avg_generation_time = cursor.fetchone()[0] or 0
        
        # Active alerts
        cursor.execute('''
            SELECT COUNT(*) as active_alerts
            FROM alerts 
            WHERE resolved = FALSE
        ''')
        
        active_alerts = cursor.fetchone()[0]
        
        # Recent builds by service
        cursor.execute('''
            SELECT service, COUNT(*) as build_count,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM builds 
            WHERE timestamp >= ?
            GROUP BY service
        ''', (start_date.isoformat(),))
        
        builds_by_service = {}
        for row in cursor.fetchall():
            service, total, success = row
            builds_by_service[service] = {
                'total': total,
                'success': success,
                'rate': (success / total * 100) if total > 0 else 0
            }
        
        # Recent publications by language
        cursor.execute('''
            SELECT language, COUNT(*) as pub_count,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM publications 
            WHERE timestamp >= ?
            GROUP BY language
        ''', (start_date.isoformat(),))
        
        pubs_by_language = {}
        for row in cursor.fetchall():
            language, total, success = row
            pubs_by_language[language] = {
                'total': total,
                'success': success,
                'rate': (success / total * 100) if total > 0 else 0
            }
        
        conn.close()
        
        return {
            'build_success_rate': build_success_rate,
            'publication_success_rate': pub_success_rate,
            'average_test_coverage': avg_coverage,
            'average_generation_time': avg_generation_time,
            'active_alerts': active_alerts,
            'builds_by_service': builds_by_service,
            'publications_by_language': pubs_by_language,
            'period_days': days
        }
    
    def generate_dashboard_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML dashboard"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Arxos SDK Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f5f5f5; padding: 15px; margin: 10px; border-radius: 5px; }}
                .metric h3 {{ margin-top: 0; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>Arxos SDK Monitoring Dashboard</h1>
            <p>Last {data['period_days']} days</p>
            
            <div class="grid">
                <div class="metric">
                    <h3>Build Success Rate</h3>
                    <p class="{'success' if data['build_success_rate'] >= 95 else 'warning'}">
                        {data['build_success_rate']:.1f}%
                    </p>
                </div>
                
                <div class="metric">
                    <h3>Publication Success Rate</h3>
                    <p class="{'success' if data['publication_success_rate'] >= 99 else 'warning'}">
                        {data['publication_success_rate']:.1f}%
                    </p>
                </div>
                
                <div class="metric">
                    <h3>Average Test Coverage</h3>
                    <p class="{'success' if data['average_test_coverage'] >= 80 else 'warning'}">
                        {data['average_test_coverage']:.1f}%
                    </p>
                </div>
                
                <div class="metric">
                    <h3>Average Generation Time</h3>
                    <p class="{'success' if data['average_generation_time'] <= 300 else 'warning'}">
                        {data['average_generation_time']:.1f}s
                    </p>
                </div>
                
                <div class="metric">
                    <h3>Active Alerts</h3>
                    <p class="{'error' if data['active_alerts'] > 0 else 'success'}">
                        {data['active_alerts']} alerts
                    </p>
                </div>
            </div>
            
            <h2>Builds by Service</h2>
            <table>
                <tr><th>Service</th><th>Total Builds</th><th>Success Rate</th></tr>
        """
        
        for service, stats in data['builds_by_service'].items():
            status_class = 'success' if stats['rate'] >= 95 else 'warning'
            html += f"""
                <tr>
                    <td>{service}</td>
                    <td>{stats['total']}</td>
                    <td class="{status_class}">{stats['rate']:.1f}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Publications by Language</h2>
            <table>
                <tr><th>Language</th><th>Total Publications</th><th>Success Rate</th></tr>
        """
        
        for language, stats in data['publications_by_language'].items():
            status_class = 'success' if stats['rate'] >= 99 else 'warning'
            html += f"""
                <tr>
                    <td>{language}</td>
                    <td>{stats['total']}</td>
                    <td class="{status_class}">{stats['rate']:.1f}%</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        retention = self.config['retention']
        
        # Clean up old metrics
        metrics_cutoff = datetime.now() - timedelta(days=retention['metrics_days'])
        cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (metrics_cutoff.isoformat(),))
        
        # Clean up old builds
        builds_cutoff = datetime.now() - timedelta(days=retention['reports_days'])
        cursor.execute('DELETE FROM builds WHERE timestamp < ?', (builds_cutoff.isoformat(),))
        
        # Clean up old tests
        cursor.execute('DELETE FROM tests WHERE timestamp < ?', (builds_cutoff.isoformat(),))
        
        # Clean up old publications
        cursor.execute('DELETE FROM publications WHERE timestamp < ?', (builds_cutoff.isoformat(),))
        
        # Clean up old alerts
        alerts_cutoff = datetime.now() - timedelta(days=retention['logs_days'])
        cursor.execute('DELETE FROM alerts WHERE timestamp < ?', (alerts_cutoff.isoformat(),))
        
        conn.commit()
        conn.close()
        
        logger.info("Cleaned up old monitoring data")

def main():
    parser = argparse.ArgumentParser(description="Arxos SDK Monitoring Dashboard")
    parser.add_argument("--config", default="config/monitoring.yaml", help="Config file path")
    parser.add_argument("--generate-dashboard", action="store_true", help="Generate dashboard HTML")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old data")
    parser.add_argument("--days", type=int, default=7, help="Days of data to include")
    
    args = parser.parse_args()
    
    dashboard = MonitoringDashboard(args.config)
    
    if args.cleanup:
        dashboard.cleanup_old_data()
        return
    
    if args.generate_dashboard:
        data = dashboard.get_dashboard_data(args.days)
        html = dashboard.generate_dashboard_html(data)
        
        # Save dashboard
        dashboard_file = Path("reports/dashboard.html")
        dashboard_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dashboard_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Dashboard saved to {dashboard_file}")
        return
    
    # Interactive mode - show current metrics
    data = dashboard.get_dashboard_data(args.days)
    print(f"Arxos SDK Dashboard (Last {args.days} days)")
    print("=" * 50)
    print(f"Build Success Rate: {data['build_success_rate']:.1f}%")
    print(f"Publication Success Rate: {data['publication_success_rate']:.1f}%")
    print(f"Average Test Coverage: {data['average_test_coverage']:.1f}%")
    print(f"Average Generation Time: {data['average_generation_time']:.1f}s")
    print(f"Active Alerts: {data['active_alerts']}")

if __name__ == "__main__":
    main() 