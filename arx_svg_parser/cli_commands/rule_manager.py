#!/usr/bin/env python3
"""
Rule Manager CLI Tool

This tool provides a command-line interface for managing building code validation rules.

Usage examples:
  python -m arx_svg_parser.cmd.rule_manager load rules/
  python -m arx_svg_parser.cmd.rule_manager list --format json
  python -m arx_svg_parser.cmd.rule_manager test fire_safety_rule --data test_data.json
  python -m arx_svg_parser.cmd.rule_manager enable fire_safety_rule
  python -m arx_svg_parser.cmd.rule_manager validate my_rule.json

Options can also be set via environment variables if config support is added.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Use relative imports for package context
from ..services.rule_engine import EnhancedRuleEngine, RuleDefinition

try:
    import yaml
except ImportError:
    yaml = None

def load_config(args) -> dict:
    config = {}
    config_file = getattr(args, 'config', None) or os.environ.get('ARXOS_RULE_MANAGER_CONFIG')
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
        if key.startswith('ARXOS_RULE_MANAGER_'):
            config[key[len('ARXOS_RULE_MANAGER_'):].lower()] = value
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v
    return config

def main():
    parser = argparse.ArgumentParser(
        description="Manage building code validation rules",
        epilog="""
Examples:
  python -m arx_svg_parser.cmd.rule_manager load rules/
  python -m arx_svg_parser.cmd.rule_manager list --format json
  python -m arx_svg_parser.cmd.rule_manager test fire_safety_rule --data test_data.json
  python -m arx_svg_parser.cmd.rule_manager enable fire_safety_rule
  python -m arx_svg_parser.cmd.rule_manager validate my_rule.json
  python -m arx_svg_parser.cmd.rule_manager --config arxos_cli_config.yaml list
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Load rules command
    load_parser = subparsers.add_parser('load', help='Load rules from file or directory')
    load_parser.add_argument('source', help='Path to rule file (.json) or directory')
    load_parser.add_argument('--pattern', default='*.json', help='File pattern for directory loading (default: *.json)')
    
    # List rules command
    list_parser = subparsers.add_parser('list', help='List loaded rules')
    list_parser.add_argument('--type', help='Filter by rule type')
    list_parser.add_argument('--enabled-only', action='store_true', help='Show only enabled rules')
    list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    
    # Test rule command
    test_parser = subparsers.add_parser('test', help='Test a rule against sample data')
    test_parser.add_argument('rule_name', help='Name of the rule to test')
    test_parser.add_argument('--data', help='Path to JSON file with test data')
    test_parser.add_argument('--format', choices=['simple', 'detailed'], default='detailed', help='Output format')
    
    # Enable/disable rule commands
    enable_parser = subparsers.add_parser('enable', help='Enable a rule')
    enable_parser.add_argument('rule_name', help='Name of the rule to enable')
    
    disable_parser = subparsers.add_parser('disable', help='Disable a rule')
    disable_parser.add_argument('rule_name', help='Name of the rule to disable')
    
    # Validate rule command
    validate_parser = subparsers.add_parser('validate', help='Validate a rule definition')
    validate_parser.add_argument('rule_file', help='Path to rule file to validate')
    
    args = parser.parse_args()
    config = load_config(args)
    
    if not config.get('command'):
        parser.print_help()
        return
    
    # Initialize rule engine
    rule_engine = EnhancedRuleEngine()
    
    try:
        if config['command'] == 'load':
            load_rules(rule_engine, config['source'], config['pattern'])
        elif config['command'] == 'list':
            list_rules(rule_engine, config['type'], config['enabled_only'], config['format'])
        elif config['command'] == 'test':
            test_rule(rule_engine, config['rule_name'], config['data'], config['format'])
        elif config['command'] == 'enable':
            enable_rule(rule_engine, config['rule_name'])
        elif config['command'] == 'disable':
            disable_rule(rule_engine, config['rule_name'])
        elif config['command'] == 'validate':
            validate_rule(rule_engine, config['rule_file'])
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def load_rules(rule_engine: EnhancedRuleEngine, source: str, pattern: str):
    """Load rules from file or directory"""
    source_path = Path(source)
    
    if source_path.is_file():
        rules = rule_engine.load_rules_from_file(source)
        print(f"Loaded {len(rules)} rules from {source}")
    elif source_path.is_dir():
        rules = rule_engine.load_rules_from_directory(source, pattern)
        print(f"Loaded {len(rules)} rules from directory {source}")
    else:
        raise FileNotFoundError(f"Source not found: {source}")
    
    # Print summary
    rule_types = {}
    for rule in rules:
        rule_types[rule.rule_type] = rule_types.get(rule.rule_type, 0) + 1
    
    print("\nRule summary:")
    for rule_type, count in rule_types.items():
        print(f"  {rule_type}: {count} rules")


def list_rules(rule_engine: EnhancedRuleEngine, rule_type: str, enabled_only: bool, format: str):
    """List loaded rules"""
    rules = rule_engine.list_rules(rule_type, enabled_only)
    
    if not rules:
        print("No rules found.")
        return
    
    if format == 'json':
        print(json.dumps(rules, indent=2))
    else:
        # Table format
        print(f"{'Rule Name':<30} {'Type':<15} {'Severity':<10} {'Priority':<8} {'Status':<8}")
        print("-" * 80)
        
        for rule in rules:
            status = "Enabled" if rule['enabled'] else "Disabled"
            print(f"{rule['rule_name']:<30} {rule['rule_type']:<15} {rule['severity']:<10} {rule['priority']:<8} {status:<8}")
        
        print(f"\nTotal: {len(rules)} rules")


def test_rule(rule_engine: EnhancedRuleEngine, rule_name: str, data_file: str, format: str):
    """Test a rule against sample data"""
    # Get the rule
    rule = rule_engine.get_rule(rule_name)
    if not rule:
        raise ValueError(f"Rule not found: {rule_name}")
    
    # Load test data
    if data_file:
        with open(data_file, 'r') as f:
            test_data = json.load(f)
    else:
        # Use sample test data
        test_data = create_sample_test_data(rule.rule_type)
    
    # Test the rule
    result = rule_engine.test_rule(rule, test_data)
    
    if format == 'simple':
        print(f"Rule: {result['rule_name']}")
        print(f"Passed: {result['passed']}")
        if not result['passed']:
            print(f"Message: {result['message']}")
    else:
        # Detailed format
        print(json.dumps(result, indent=2))


def enable_rule(rule_engine: EnhancedRuleEngine, rule_name: str):
    """Enable a rule"""
    if rule_engine.enable_rule(rule_name):
        print(f"Rule '{rule_name}' enabled successfully")
    else:
        print(f"Rule '{rule_name}' not found")


def disable_rule(rule_engine: EnhancedRuleEngine, rule_name: str):
    """Disable a rule"""
    if rule_engine.disable_rule(rule_name):
        print(f"Rule '{rule_name}' disabled successfully")
    else:
        print(f"Rule '{rule_name}' not found")


def validate_rule(rule_engine: EnhancedRuleEngine, rule_file: str):
    """Validate a rule definition"""
    try:
        with open(rule_file, 'r') as f:
            rule_data = json.load(f)
        
        errors = rule_engine.validate_rule_definition(rule_data)
        
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Rule definition is valid!")
            
            # Show rule summary
            rule = rule_engine._parse_rule_definition(rule_data)
            print(f"\nRule summary:")
            print(f"  Name: {rule.rule_name}")
            print(f"  Type: {rule.rule_type}")
            print(f"  Version: {rule.version}")
            print(f"  Severity: {rule.severity}")
            print(f"  Priority: {rule.priority}")
            print(f"  Conditions: {len(rule.conditions)}")
            print(f"  Actions: {len(rule.actions)}")
            print(f"  Enabled: {rule.enabled}")
    
    except Exception as e:
        print(f"Error validating rule: {e}")


def create_sample_test_data(rule_type: str) -> Dict[str, Any]:
    """Create sample test data based on rule type"""
    if rule_type == 'structural':
        return {
            'structural': {
                'loads': {
                    'dead_load': 100,
                    'live_load': 50,
                    'snow_load': 30
                },
                'materials': {
                    'concrete': {
                        'strength': 4000,
                        'density': 150
                    }
                }
            }
        }
    elif rule_type == 'fire_safety':
        return {
            'fire_safety': {
                'fire_ratings': {
                    'walls': 3,
                    'doors': 2
                },
                'egress': {
                    'exit_width': 42,
                    'exit_distance': 150
                }
            }
        }
    elif rule_type == 'accessibility':
        return {
            'accessibility': {
                'clear_width': 42,
                'doors': {
                    'entrance': {
                        'width': 36,
                        'threshold': 0.5
                    }
                }
            }
        }
    elif rule_type == 'energy':
        return {
            'energy': {
                'insulation': {
                    'walls': 25,
                    'roof': 35
                },
                'windows': {
                    'u_factor': 0.30,
                    'shgc': 0.20
                }
            }
        }
    else:
        return {
            'building_type': 'commercial',
            'floors': 5,
            'occupancy': 'office'
        }


if __name__ == '__main__':
    main() 