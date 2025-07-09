#!/usr/bin/env python3
"""
Realtime Telemetry CLI Tool

This tool provides a command-line interface for real-time telemetry operations, including starting the server, ingesting data, generating simulated data, monitoring alerts, and managing alert rules.

Usage examples:
  python -m arx_svg_parser.cmd.realtime_telemetry_cli start-server --config telemetry_config.json
  python -m arx_svg_parser.cmd.realtime_telemetry_cli ingest-data --file telemetry.json
  python -m arx_svg_parser.cmd.realtime_telemetry_cli generate-simulated --output simulated.jsonl --count 100
  python -m arx_svg_parser.cmd.realtime_telemetry_cli monitor-alerts --duration 60
  python -m arx_svg_parser.cmd.realtime_telemetry_cli list-alert-rules

Options can also be set via environment variables or config files if config support is added.
"""

import argparse
import json
import sys
import asyncio
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Use relative imports for package context
from ..services.realtime_telemetry import RealtimeTelemetryService

from services.telemetry import generate_simulated_telemetry

try:
    import yaml
except ImportError:
    yaml = None

def load_config(args) -> dict:
    config = {}
    config_file = getattr(args, 'config', None) or os.environ.get('ARXOS_TELEMETRY_CLI_CONFIG')
    if config_file:
        ext = Path(config_file).suffix.lower()
        try:
            with open(config_file, 'r') as f:
                if ext in ['.yaml', '.yml'] and yaml:
                    config = yaml.safe_load(f)
                elif ext == '.json':
                    config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    else:
        for default in [Path.cwd() / 'arxos_cli_config.yaml', Path.home() / 'arxos_cli_config.yaml']:
            if default.exists() and yaml:
                with open(default, 'r') as f:
                    config = yaml.safe_load(f)
                break
    for key, value in os.environ.items():
        if key.startswith('ARXOS_TELEMETRY_CLI_'):
            config[key[len('ARXOS_TELEMETRY_CLI_'):].lower()] = value
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v
    return config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeTelemetryCLI:
    """CLI interface for real-time telemetry"""
    
    def __init__(self):
        self.processor = None
        self.server = None
        self.config = None
    
    def start_server(self, config_file: str = None, websocket_port: int = 8765, 
                    http_port: int = 8080, buffer_size: int = 10000) -> None:
        """Start the real-time telemetry server"""
        try:
            # Load config from file if provided
            if config_file:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                self.config = TelemetryConfig(**config_data)
            else:
                self.config = TelemetryConfig(
                    websocket_port=websocket_port,
                    http_port=http_port,
                    buffer_size=buffer_size
                )
            
            logger.info("Starting real-time telemetry server...")
            logger.info(f"WebSocket port: {self.config.websocket_port}")
            logger.info(f"HTTP port: {self.config.http_port}")
            logger.info(f"Buffer size: {self.config.buffer_size}")
            
            # Start the system
            start_realtime_telemetry(self.config)
        
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)
    
    def ingest_data(self, data_file: str, delay: float = 0.0) -> None:
        """Ingest data from file"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            logger.info(f"Ingesting data from {data_file}")
            
            with open(data_file, 'r') as f:
                if data_file.endswith('.json'):
                    data = json.load(f)
                    if isinstance(data, list):
                        for record in data:
                            self.processor.ingest_data(record)
                            if delay > 0:
                                time.sleep(delay)
                    else:
                        self.processor.ingest_data(data)
                else:
                    # Assume JSONL format
                    for line in f:
                        record = json.loads(line.strip())
                        self.processor.ingest_data(record)
                        if delay > 0:
                            time.sleep(delay)
            
            logger.info("Data ingestion completed")
        
        except Exception as e:
            logger.error(f"Failed to ingest data: {e}")
    
    def generate_simulated_data(self, output_file: str, sources: List[str] = None, 
                               types: List[str] = None, count: int = 100, 
                               delay: float = 0.1) -> None:
        """Generate and ingest simulated telemetry data"""
        if sources is None:
            sources = ["sensor_001", "sensor_002", "sensor_003"]
        
        if types is None:
            types = ["temperature", "pressure", "vibration", "current"]
        
        try:
            logger.info(f"Generating {count} simulated records...")
            
            # Generate simulated data
            records = generate_simulated_telemetry(sources, types, count)
            
            # Save to file
            with open(output_file, 'w') as f:
                for record in records:
                    f.write(json.dumps(record) + '\n')
            
            logger.info(f"Simulated data saved to {output_file}")
            
            # Ingest data if processor is available
            if self.processor:
                logger.info("Ingesting simulated data...")
                for record in records:
                    self.processor.ingest_data(record)
                    if delay > 0:
                        time.sleep(delay)
                logger.info("Simulated data ingestion completed")
        
        except Exception as e:
            logger.error(f"Failed to generate simulated data: {e}")
    
    def monitor_alerts(self, duration: int = 60, interval: float = 1.0) -> None:
        """Monitor alerts in real-time"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            logger.info(f"Monitoring alerts for {duration} seconds...")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                alerts = self.processor.get_alerts(limit=10)
                
                if alerts:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Recent Alerts:")
                    for alert in alerts[-5:]:  # Show last 5 alerts
                        print(f"  - {alert['description']} ({alert['severity']})")
                
                dashboard_data = self.processor.get_dashboard_data()
                print(f"\rStatus: {dashboard_data['system_status']} | "
                      f"Events: {dashboard_data['total_events']} | "
                      f"Alerts: {dashboard_data['active_alerts']}", end='')
                
                time.sleep(interval)
            
            print("\nMonitoring completed")
        
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
    
    def list_alert_rules(self) -> None:
        """List configured alert rules"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            rules = self.processor.alert_rules
            
            if not rules:
                print("No alert rules configured")
                return
            
            print("Configured Alert Rules:")
            print("-" * 50)
            
            for rule_id, rule in rules.items():
                print(f"ID: {rule_id}")
                print(f"Name: {rule.name}")
                print(f"Condition: {rule.condition}")
                print(f"Severity: {rule.severity}")
                print(f"Enabled: {rule.enabled}")
                print(f"Actions: {', '.join(rule.actions)}")
                print("-" * 50)
        
        except Exception as e:
            logger.error(f"Failed to list alert rules: {e}")
    
    def add_alert_rule(self, rule_file: str) -> None:
        """Add alert rule from file"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            with open(rule_file, 'r') as f:
                rule_data = json.load(f)
            
            rule = AlertRule(**rule_data)
            self.processor.add_alert_rule(rule)
            
            logger.info(f"Added alert rule: {rule.name}")
        
        except Exception as e:
            logger.error(f"Failed to add alert rule: {e}")
    
    def remove_alert_rule(self, rule_id: str) -> None:
        """Remove alert rule"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            self.processor.remove_alert_rule(rule_id)
            logger.info(f"Removed alert rule: {rule_id}")
        
        except Exception as e:
            logger.error(f"Failed to remove alert rule: {e}")
    
    def get_dashboard_data(self) -> None:
        """Get current dashboard data"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            data = self.processor.get_dashboard_data()
            print(json.dumps(data, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
    
    def get_patterns(self, limit: int = 10) -> None:
        """Get recent patterns"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        
        try:
            patterns = self.processor.get_patterns(limit)
            
            if not patterns:
                print("No patterns detected")
                return
            
            print(f"Recent Patterns (last {len(patterns)}):")
            print("-" * 50)
            
            for pattern in patterns:
                print(f"ID: {pattern.pattern_id}")
                print(f"Type: {pattern.failure_type.value}")
                print(f"Source: {pattern.source}")
                print(f"Confidence: {pattern.confidence:.3f}")
                print(f"Severity: {pattern.severity:.3f}")
                print(f"Description: {pattern.description}")
                print("-" * 50)
        
        except Exception as e:
            logger.error(f"Failed to get patterns: {e}")
    
    def create_sample_config(self, output_file: str) -> None:
        """Create a sample configuration file"""
        try:
            config = {
                "buffer_size": 10000,
                "processing_interval": 1.0,
                "alert_threshold": 0.8,
                "max_history_size": 100000,
                "enable_websocket": True,
                "websocket_port": 8765,
                "enable_http": True,
                "http_port": 8080,
                "enable_dashboard": True,
                "dashboard_port": 8081
            }
            
            with open(output_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Sample configuration saved to {output_file}")
        
        except Exception as e:
            logger.error(f"Failed to create sample config: {e}")
    
    def create_sample_alert_rule(self, output_file: str) -> None:
        """Create a sample alert rule file"""
        try:
            rule = {
                "rule_id": "sample_rule",
                "name": "Sample Alert Rule",
                "condition": "threshold",
                "parameters": {
                    "field": "temperature",
                    "operator": ">",
                    "value": 80.0
                },
                "severity": "warning",
                "enabled": True,
                "actions": ["log_alert", "send_notification"]
            }
            
            with open(output_file, 'w') as f:
                json.dump(rule, f, indent=2)
            
            logger.info(f"Sample alert rule saved to {output_file}")
        
        except Exception as e:
            logger.error(f"Failed to create sample alert rule: {e}")
    
    def get_analytics(self, data_type: str = None) -> None:
        """Get analytics results"""
        if not self.processor:
            logger.error("Processor not initialized. Start server first.")
            return
        try:
            results = self.processor.get_analytics_results(data_type)
            print(json.dumps(results, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to get analytics results: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Real-Time Telemetry CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start server command
    start_parser = subparsers.add_parser('start', help='Start real-time telemetry server')
    start_parser.add_argument('--config', help='Configuration file path')
    start_parser.add_argument('--websocket-port', type=int, default=8765, help='WebSocket port')
    start_parser.add_argument('--http-port', type=int, default=8080, help='HTTP port')
    start_parser.add_argument('--buffer-size', type=int, default=10000, help='Buffer size')
    
    # Ingest data command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest data from file')
    ingest_parser.add_argument('data_file', help='Data file path')
    ingest_parser.add_argument('--delay', type=float, default=0.0, help='Delay between records')
    
    # Generate simulated data command
    generate_parser = subparsers.add_parser('generate', help='Generate simulated telemetry data')
    generate_parser.add_argument('output_file', help='Output file path')
    generate_parser.add_argument('--sources', nargs='+', default=['sensor_001', 'sensor_002'], help='Data sources')
    generate_parser.add_argument('--types', nargs='+', default=['temperature', 'pressure'], help='Data types')
    generate_parser.add_argument('--count', type=int, default=100, help='Number of records')
    generate_parser.add_argument('--delay', type=float, default=0.1, help='Delay between records')
    
    # Monitor alerts command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor alerts in real-time')
    monitor_parser.add_argument('--duration', type=int, default=60, help='Monitoring duration (seconds)')
    monitor_parser.add_argument('--interval', type=float, default=1.0, help='Update interval (seconds)')
    
    # List alert rules command
    subparsers.add_parser('list-rules', help='List configured alert rules')
    
    # Add alert rule command
    add_rule_parser = subparsers.add_parser('add-rule', help='Add alert rule from file')
    add_rule_parser.add_argument('rule_file', help='Alert rule file path')
    
    # Remove alert rule command
    remove_rule_parser = subparsers.add_parser('remove-rule', help='Remove alert rule')
    remove_rule_parser.add_argument('rule_id', help='Alert rule ID')
    
    # Get dashboard data command
    subparsers.add_parser('dashboard', help='Get current dashboard data')
    
    # Get patterns command
    patterns_parser = subparsers.add_parser('patterns', help='Get recent patterns')
    patterns_parser.add_argument('--limit', type=int, default=10, help='Number of patterns to show')
    
    # Create sample config command
    config_parser = subparsers.add_parser('create-config', help='Create sample configuration file')
    config_parser.add_argument('output_file', help='Output file path')
    
    # Create sample alert rule command
    rule_parser = subparsers.add_parser('create-rule', help='Create sample alert rule file')
    rule_parser.add_argument('output_file', help='Output file path')
    
    # Get analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Get analytics results')
    analytics_parser.add_argument('--data-type', type=str, default=None, help='Data type (e.g., temperature)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = RealtimeTelemetryCLI()
    
    try:
        if args.command == 'start':
            cli.start_server(args.config, args.websocket_port, args.http_port, args.buffer_size)
        
        elif args.command == 'ingest':
            cli.ingest_data(args.data_file, args.delay)
        
        elif args.command == 'generate':
            cli.generate_simulated_data(args.output_file, args.sources, args.types, args.count, args.delay)
        
        elif args.command == 'monitor':
            cli.monitor_alerts(args.duration, args.interval)
        
        elif args.command == 'list-rules':
            cli.list_alert_rules()
        
        elif args.command == 'add-rule':
            cli.add_alert_rule(args.rule_file)
        
        elif args.command == 'remove-rule':
            cli.remove_alert_rule(args.rule_id)
        
        elif args.command == 'dashboard':
            cli.get_dashboard_data()
        
        elif args.command == 'patterns':
            cli.get_patterns(args.limit)
        
        elif args.command == 'create-config':
            cli.create_sample_config(args.output_file)
        
        elif args.command == 'create-rule':
            cli.create_sample_alert_rule(args.output_file)
        
        elif args.command == 'analytics':
            cli.get_analytics(args.data_type)
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 