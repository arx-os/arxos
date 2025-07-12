"""
Logic Engine CLI Commands

This module provides comprehensive command-line interface for logic engine
functionality including rule management, rule execution, rule chains,
and performance monitoring.

Usage Examples:
    arx logic health
    arx logic rules list
    arx logic rules create --name "Validation Rule" --type validation
    arx logic rules execute --rule-id rule_123 --data '{"test": "value"}'
    arx logic chains create --name "Workflow" --rules rule1,rule2
    arx logic performance
    arx logic statistics
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from services.logic_engine import (
    LogicEngine,
    RuleType,
    RuleStatus,
    ExecutionStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def logic():
    """Logic Engine commands."""
    pass


@logic.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def health(format: str):
    """
    Get logic engine health status.
    
    Examples:
        arx logic health
        arx logic health --format json
    """
    try:
        engine = LogicEngine()
        
        logger.info("Getting logic engine health status")
        metrics = engine.get_performance_metrics()
        
        health_status = {
            "status": "healthy" if metrics['success_rate'] > 95 else "degraded",
            "total_rules": metrics['total_rules'],
            "active_rules": metrics['active_rules'],
            "total_chains": metrics['total_chains'],
            "active_chains": metrics['active_chains'],
            "success_rate": metrics['success_rate'],
            "average_execution_time": metrics['average_execution_time']
        }
        
        if format == 'json':
            click.echo(json.dumps(health_status, indent=2))
        elif format == 'csv':
            click.echo("status,total_rules,active_rules,success_rate,avg_execution_time")
            click.echo(f"{health_status['status']},{health_status['total_rules']},{health_status['active_rules']},{health_status['success_rate']:.1f},{health_status['average_execution_time']:.3f}")
        else:
            click.echo("Logic Engine Health Status")
            click.echo("=" * 30)
            click.echo(f"Status: {health_status['status']}")
            click.echo(f"Total Rules: {health_status['total_rules']}")
            click.echo(f"Active Rules: {health_status['active_rules']}")
            click.echo(f"Total Chains: {health_status['total_chains']}")
            click.echo(f"Active Chains: {health_status['active_chains']}")
            click.echo(f"Success Rate: {health_status['success_rate']:.1f}%")
            click.echo(f"Avg Execution Time: {health_status['average_execution_time']:.3f}s")
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@logic.group()
def rules():
    """Rule management commands."""
    pass


@rules.command()
@click.option('--rule-type', help='Filter by rule type')
@click.option('--status', help='Filter by status')
@click.option('--tags', help='Filter by tags (comma-separated)')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def list(rule_type: Optional[str], status: Optional[str], tags: Optional[str], format: str):
    """
    List all rules with optional filtering.
    
    Examples:
        arx logic rules list
        arx logic rules list --rule-type validation
        arx logic rules list --status active
    """
    try:
        engine = LogicEngine()
        
        logger.info("Getting list of rules")
        
        # Convert parameters to enums
        rule_type_enum = None
        if rule_type:
            try:
                rule_type_enum = RuleType(rule_type)
            except ValueError:
                click.echo(f"Error: Invalid rule type '{rule_type}'", err=True)
                sys.exit(1)
        
        status_enum = None
        if status:
            try:
                status_enum = RuleStatus(status)
            except ValueError:
                click.echo(f"Error: Invalid status '{status}'", err=True)
                sys.exit(1)
        
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]
        
        rules = engine.list_rules(rule_type_enum, status_enum, tags_list)
        
        if format == 'json':
            click.echo(json.dumps([{
                'rule_id': r.rule_id,
                'name': r.name,
                'rule_type': r.rule_type.value,
                'status': r.status.value,
                'priority': r.priority,
                'execution_count': r.execution_count,
                'success_rate': (r.success_count / r.execution_count * 100) if r.execution_count > 0 else 0
            } for r in rules], indent=2))
        elif format == 'csv':
            click.echo("rule_id,name,rule_type,status,priority,execution_count,success_rate")
            for rule in rules:
                success_rate = (rule.success_count / rule.execution_count * 100) if rule.execution_count > 0 else 0
                click.echo(f"{rule.rule_id},{rule.name},{rule.rule_type.value},{rule.status.value},{rule.priority},{rule.execution_count},{success_rate:.1f}")
        else:
            click.echo(f"Rules ({len(rules)} total)")
            click.echo("=" * 50)
            
            if rules:
                for rule in rules:
                    status_icon = "🟢" if rule.status == RuleStatus.ACTIVE else "🔴"
                    success_rate = (rule.success_count / rule.execution_count * 100) if rule.execution_count > 0 else 0
                    click.echo(f"{status_icon} {rule.name} ({rule.rule_id})")
                    click.echo(f"    Type: {rule.rule_type.value}")
                    click.echo(f"    Status: {rule.status.value}")
                    click.echo(f"    Priority: {rule.priority}")
                    click.echo(f"    Executions: {rule.execution_count}")
                    click.echo(f"    Success Rate: {success_rate:.1f}%")
                    click.echo()
            else:
                click.echo("No rules found.")
        
    except Exception as e:
        logger.error(f"Failed to list rules: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@rules.command()
@click.option('--name', required=True, help='Rule name')
@click.option('--description', required=True, help='Rule description')
@click.option('--type', 'rule_type', required=True, type=click.Choice(['conditional', 'transformation', 'validation', 'workflow', 'analysis']), help='Rule type')
@click.option('--conditions', required=True, help='Conditions (JSON)')
@click.option('--actions', required=True, help='Actions (JSON)')
@click.option('--priority', default=1, type=int, help='Rule priority')
@click.option('--tags', help='Tags (comma-separated)')
def create(name: str, description: str, rule_type: str, conditions: str, actions: str, priority: int, tags: Optional[str]):
    """
    Create a new rule.
    
    Examples:
        arx logic rules create --name "Age Validation" --description "Validate user age" --type validation --conditions '[{"field": "age", "operator": "greater_than", "value": 18}]' --actions '[{"type": "set_field", "field": "validated", "value": true}]'
    """
    try:
        engine = LogicEngine()
        
        # Parse JSON inputs
        try:
            conditions_data = json.loads(conditions)
            actions_data = json.loads(actions)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            sys.exit(1)
        
        # Parse tags
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]
        
        logger.info(f"Creating rule: {name}")
        
        rule_id = engine.create_rule(
            name=name,
            description=description,
            rule_type=RuleType(rule_type),
            conditions=conditions_data,
            actions=actions_data,
            priority=priority,
            tags=tags_list
        )
        
        click.echo(f"Rule created successfully!")
        click.echo(f"Rule ID: {rule_id}")
        click.echo(f"Name: {name}")
        click.echo(f"Type: {rule_type}")
        click.echo(f"Priority: {priority}")
        
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@rules.command()
@click.option('--rule-id', required=True, help='Rule identifier')
@click.option('--data', required=True, help='Input data (JSON)')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def execute(rule_id: str, data: str, format: str):
    """
    Execute a specific rule.
    
    Examples:
        arx logic rules execute --rule-id rule_123 --data '{"user": {"age": 25}}'
    """
    try:
        engine = LogicEngine()
        
        # Parse input data
        try:
            input_data = json.loads(data)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            sys.exit(1)
        
        logger.info(f"Executing rule: {rule_id}")
        
        execution = engine.execute_rule(rule_id, input_data)
        
        if format == 'json':
            click.echo(json.dumps({
                'execution_id': execution.execution_id,
                'rule_id': execution.rule_id,
                'status': execution.status.value,
                'execution_time': execution.execution_time,
                'error_message': execution.error_message,
                'output_data': execution.output_data
            }, indent=2))
        elif format == 'csv':
            click.echo("execution_id,rule_id,status,execution_time,error_message")
            click.echo(f"{execution.execution_id},{execution.rule_id},{execution.status.value},{execution.execution_time:.3f},{execution.error_message or ''}")
        else:
            click.echo(f"Rule Execution Result")
            click.echo("=" * 30)
            click.echo(f"Execution ID: {execution.execution_id}")
            click.echo(f"Rule ID: {execution.rule_id}")
            click.echo(f"Status: {execution.status.value}")
            click.echo(f"Execution Time: {execution.execution_time:.3f}s")
            if execution.error_message:
                click.echo(f"Error: {execution.error_message}")
            click.echo(f"Output Data: {json.dumps(execution.output_data, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to execute rule: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@logic.group()
def chains():
    """Rule chain management commands."""
    pass


@chains.command()
@click.option('--name', required=True, help='Chain name')
@click.option('--description', required=True, help='Chain description')
@click.option('--rules', required=True, help='Rule IDs (comma-separated)')
@click.option('--execution-order', default='sequential', type=click.Choice(['sequential', 'parallel', 'conditional']), help='Execution order')
def create(name: str, description: str, rules: str, execution_order: str):
    """
    Create a new rule chain.
    
    Examples:
        arx logic chains create --name "User Workflow" --description "Complete user processing workflow" --rules "rule1,rule2,rule3" --execution-order sequential
    """
    try:
        engine = LogicEngine()
        
        # Parse rule IDs
        rule_ids = [rule_id.strip() for rule_id in rules.split(',')]
        
        logger.info(f"Creating rule chain: {name}")
        
        chain_id = engine.create_rule_chain(
            name=name,
            description=description,
            rules=rule_ids,
            execution_order=execution_order
        )
        
        click.echo(f"Rule chain created successfully!")
        click.echo(f"Chain ID: {chain_id}")
        click.echo(f"Name: {name}")
        click.echo(f"Rules: {len(rule_ids)} rules")
        click.echo(f"Execution Order: {execution_order}")
        
    except Exception as e:
        logger.error(f"Failed to create rule chain: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@chains.command()
@click.option('--chain-id', required=True, help='Chain identifier')
@click.option('--data', required=True, help='Input data (JSON)')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def execute(chain_id: str, data: str, format: str):
    """
    Execute a rule chain.
    
    Examples:
        arx logic chains execute --chain-id chain_123 --data '{"user": {"age": 25}}'
    """
    try:
        engine = LogicEngine()
        
        # Parse input data
        try:
            input_data = json.loads(data)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            sys.exit(1)
        
        logger.info(f"Executing rule chain: {chain_id}")
        
        executions = engine.execute_rule_chain(chain_id, input_data)
        
        if format == 'json':
            click.echo(json.dumps({
                'chain_id': chain_id,
                'total_executions': len(executions),
                'successful_executions': len([e for e in executions if e.status == ExecutionStatus.SUCCESS]),
                'failed_executions': len([e for e in executions if e.status != ExecutionStatus.SUCCESS]),
                'total_execution_time': sum(e.execution_time for e in executions),
                'executions': [{
                    'rule_id': e.rule_id,
                    'status': e.status.value,
                    'execution_time': e.execution_time,
                    'error_message': e.error_message
                } for e in executions]
            }, indent=2))
        elif format == 'csv':
            click.echo("chain_id,total_executions,successful_executions,failed_executions,total_execution_time")
            successful = len([e for e in executions if e.status == ExecutionStatus.SUCCESS])
            failed = len([e for e in executions if e.status != ExecutionStatus.SUCCESS])
            total_time = sum(e.execution_time for e in executions)
            click.echo(f"{chain_id},{len(executions)},{successful},{failed},{total_time:.3f}")
        else:
            click.echo(f"Rule Chain Execution Result")
            click.echo("=" * 40)
            click.echo(f"Chain ID: {chain_id}")
            click.echo(f"Total Executions: {len(executions)}")
            click.echo(f"Successful: {len([e for e in executions if e.status == ExecutionStatus.SUCCESS])}")
            click.echo(f"Failed: {len([e for e in executions if e.status != ExecutionStatus.SUCCESS])}")
            click.echo(f"Total Time: {sum(e.execution_time for e in executions):.3f}s")
            
            for i, execution in enumerate(executions, 1):
                status_icon = "🟢" if execution.status == ExecutionStatus.SUCCESS else "🔴"
                click.echo(f"\n{i}. {status_icon} Rule: {execution.rule_id}")
                click.echo(f"   Status: {execution.status.value}")
                click.echo(f"   Time: {execution.execution_time:.3f}s")
                if execution.error_message:
                    click.echo(f"   Error: {execution.error_message}")
        
    except Exception as e:
        logger.error(f"Failed to execute rule chain: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@logic.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def performance(format: str):
    """
    Get logic engine performance metrics.
    
    Examples:
        arx logic performance
        arx logic performance --format json
    """
    try:
        engine = LogicEngine()
        
        logger.info("Getting performance metrics")
        metrics = engine.get_performance_metrics()
        
        if format == 'json':
            click.echo(json.dumps(metrics, indent=2))
        elif format == 'csv':
            click.echo("total_executions,successful_executions,failed_executions,success_rate,avg_execution_time,total_rules,active_rules")
            click.echo(f"{metrics['total_executions']},{metrics['successful_executions']},{metrics['failed_executions']},{metrics['success_rate']:.1f},{metrics['average_execution_time']:.3f},{metrics['total_rules']},{metrics['active_rules']}")
        else:
            click.echo("Logic Engine Performance Metrics")
            click.echo("=" * 40)
            click.echo(f"Total Executions: {metrics['total_executions']}")
            click.echo(f"Successful Executions: {metrics['successful_executions']}")
            click.echo(f"Failed Executions: {metrics['failed_executions']}")
            click.echo(f"Success Rate: {metrics['success_rate']:.1f}%")
            click.echo(f"Average Execution Time: {metrics['average_execution_time']:.3f}s")
            click.echo(f"Total Rules: {metrics['total_rules']}")
            click.echo(f"Active Rules: {metrics['active_rules']}")
            click.echo(f"Total Chains: {metrics['total_chains']}")
            click.echo(f"Active Chains: {metrics['active_chains']}")
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@logic.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def statistics(format: str):
    """
    Get detailed statistics about rules and executions.
    
    Examples:
        arx logic statistics
        arx logic statistics --format json
    """
    try:
        engine = LogicEngine()
        
        logger.info("Getting detailed statistics")
        
        # Get rules by type and status
        rules_by_type = {}
        rules_by_status = {}
        
        for rule in engine.rules.values():
            rule_type = rule.rule_type.value
            rule_status = rule.status.value
            
            rules_by_type[rule_type] = rules_by_type.get(rule_type, 0) + 1
            rules_by_status[rule_status] = rules_by_status.get(rule_status, 0) + 1
        
        # Get top performing rules
        top_performing_rules = []
        for rule in engine.rules.values():
            if rule.execution_count > 0:
                success_rate = (rule.success_count / rule.execution_count * 100)
                top_performing_rules.append({
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'execution_count': rule.execution_count,
                    'success_rate': success_rate,
                    'avg_execution_time': rule.avg_execution_time
                })
        
        # Sort by success rate
        top_performing_rules.sort(key=lambda x: x['success_rate'], reverse=True)
        top_performing_rules = top_performing_rules[:10]  # Top 10
        
        # Get execution trends
        metrics = engine.get_performance_metrics()
        execution_trends = {
            'total_executions': metrics['total_executions'],
            'success_rate': metrics['success_rate'],
            'avg_execution_time': metrics['average_execution_time']
        }
        
        stats = {
            'rules_by_type': rules_by_type,
            'rules_by_status': rules_by_status,
            'top_performing_rules': top_performing_rules,
            'execution_trends': execution_trends
        }
        
        if format == 'json':
            click.echo(json.dumps(stats, indent=2))
        elif format == 'csv':
            # CSV output for rules by type
            click.echo("rule_type,count")
            for rule_type, count in rules_by_type.items():
                click.echo(f"{rule_type},{count}")
        else:
            click.echo("Logic Engine Statistics")
            click.echo("=" * 30)
            
            click.echo(f"\nRules by Type:")
            for rule_type, count in rules_by_type.items():
                click.echo(f"  {rule_type}: {count}")
            
            click.echo(f"\nRules by Status:")
            for status, count in rules_by_status.items():
                click.echo(f"  {status}: {count}")
            
            click.echo(f"\nTop Performing Rules:")
            for i, rule in enumerate(top_performing_rules, 1):
                click.echo(f"  {i}. {rule['name']} ({rule['rule_id']})")
                click.echo(f"     Executions: {rule['execution_count']}")
                click.echo(f"     Success Rate: {rule['success_rate']:.1f}%")
                click.echo(f"     Avg Time: {rule['avg_execution_time']:.3f}s")
            
            click.echo(f"\nExecution Trends:")
            click.echo(f"  Total Executions: {execution_trends['total_executions']}")
            click.echo(f"  Success Rate: {execution_trends['success_rate']:.1f}%")
            click.echo(f"  Avg Execution Time: {execution_trends['avg_execution_time']:.3f}s")
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@logic.command()
def types():
    """
    Get all available rule types.
    
    Examples:
        arx logic types
    """
    rule_types = [
        {
            "type": "conditional",
            "name": "Conditional Rule",
            "description": "Rules that evaluate conditions and execute actions based on results"
        },
        {
            "type": "transformation",
            "name": "Transformation Rule",
            "description": "Rules that transform data from one format to another"
        },
        {
            "type": "validation",
            "name": "Validation Rule",
            "description": "Rules that validate data integrity and business rules"
        },
        {
            "type": "workflow",
            "name": "Workflow Rule",
            "description": "Rules that orchestrate complex workflows and processes"
        },
        {
            "type": "analysis",
            "name": "Analysis Rule",
            "description": "Rules that perform data analysis and pattern recognition"
        }
    ]
    
    click.echo("Available Rule Types")
    click.echo("=" * 30)
    
    for rule_type in rule_types:
        click.echo(f"{rule_type['name']} ({rule_type['type']})")
        click.echo(f"  {rule_type['description']}")
        click.echo()


@logic.command()
def operators():
    """
    Get all available condition operators.
    
    Examples:
        arx logic operators
    """
    operators = [
        ("equals", "Check if value equals the expected value"),
        ("not_equals", "Check if value does not equal the expected value"),
        ("greater_than", "Check if value is greater than the expected value"),
        ("greater_than_or_equal", "Check if value is greater than or equal to the expected value"),
        ("less_than", "Check if value is less than the expected value"),
        ("less_than_or_equal", "Check if value is less than or equal to the expected value"),
        ("contains", "Check if value contains the expected value"),
        ("not_contains", "Check if value does not contain the expected value"),
        ("starts_with", "Check if value starts with the expected value"),
        ("ends_with", "Check if value ends with the expected value"),
        ("is_empty", "Check if value is empty or null"),
        ("is_not_empty", "Check if value is not empty"),
        ("is_null", "Check if value is null"),
        ("is_not_null", "Check if value is not null"),
        ("matches", "Check if value matches a regular expression pattern"),
        ("in", "Check if value is in a list of expected values"),
        ("not_in", "Check if value is not in a list of expected values")
    ]
    
    click.echo("Available Condition Operators")
    click.echo("=" * 40)
    
    for operator, description in operators:
        click.echo(f"{operator}")
        click.echo(f"  {description}")
        click.echo()


if __name__ == "__main__":
    logic() 