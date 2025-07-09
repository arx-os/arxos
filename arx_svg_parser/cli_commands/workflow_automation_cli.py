"""
Workflow Automation CLI Commands

This module provides comprehensive command-line interface for workflow automation
and orchestration operations including:
- Workflow creation and management
- Workflow execution and monitoring
- Execution history and reporting
- Performance metrics and analytics
- Workflow scheduling and triggers

Usage Examples:
    arx workflow create --workflow-id test_workflow --name "Test Workflow" --steps steps.json
    arx workflow execute --workflow-id test_workflow --context context.json
    arx workflow status --execution-id exec_123
    arx workflow history --workflow-id test_workflow --limit 10
    arx workflow metrics
    arx workflow list
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from services.workflow_automation import (
    WorkflowAutomationService,
    WorkflowType,
    WorkflowStatus,
    StepType,
    ConditionType
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def workflow():
    """Workflow Automation commands."""
    pass


@workflow.command()
@click.option('--workflow-id', required=True, help='Unique workflow identifier')
@click.option('--name', required=True, help='Workflow name')
@click.option('--description', help='Workflow description')
@click.option('--workflow-type', default='validation', type=click.Choice(['validation', 'export', 'reporting', 'data_processing', 'integration', 'cleanup']), help='Workflow type')
@click.option('--steps', type=click.Path(exists=True), help='Path to steps JSON file')
@click.option('--triggers', type=click.Path(exists=True), help='Path to triggers JSON file')
@click.option('--schedule', help='Cron schedule expression')
@click.option('--timeout', default=1800, type=int, help='Workflow timeout in seconds')
@click.option('--max-retries', default=3, type=int, help='Maximum retries')
@click.option('--output', type=click.Path(), help='Output file for workflow definition')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def create(workflow_id: str, name: str, description: str, workflow_type: str, steps: Optional[str],
           triggers: Optional[str], schedule: Optional[str], timeout: int, max_retries: int,
           output: Optional[str], format: str, verbose: bool):
    """
    Create a new workflow definition.
    
    This command allows creating custom workflows with steps, conditions,
    triggers, and scheduling options.
    
    Examples:
        arx workflow create --workflow-id test_workflow --name "Test Workflow" --steps steps.json
        arx workflow create --workflow-id export_workflow --name "Export Workflow" --workflow-type export --schedule "0 2 * * *"
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize workflow service
        workflow_service = WorkflowAutomationService()
        
        # Load steps from file or create default
        if steps:
            with open(steps, 'r') as f:
                steps_data = json.load(f)
            logger.info(f"Loaded steps from {steps}")
        else:
            # Create default steps
            steps_data = [
                {
                    "step_id": "default_step",
                    "name": "Default Step",
                    "step_type": "validation",
                    "parameters": {
                        "service": "default_service"
                    },
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 2
                }
            ]
            logger.info("Using default steps")
        
        # Load triggers from file or create default
        if triggers:
            with open(triggers, 'r') as f:
                triggers_data = json.load(f)
            logger.info(f"Loaded triggers from {triggers}")
        else:
            triggers_data = []
            logger.info("Using default triggers")
        
        # Create workflow data
        workflow_data = {
            "workflow_id": workflow_id,
            "name": name,
            "description": description or f"Workflow: {name}",
            "workflow_type": workflow_type,
            "steps": steps_data,
            "triggers": triggers_data,
            "schedule": schedule,
            "timeout": timeout,
            "max_retries": max_retries
        }
        
        # Create workflow
        created_workflow_id = workflow_service.create_workflow(workflow_data)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(workflow_data, f, indent=2, default=str)
            logger.info(f"Workflow definition saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'workflow_id': created_workflow_id,
                'name': name,
                'description': description,
                'workflow_type': workflow_type,
                'steps_count': len(steps_data),
                'timeout': timeout,
                'max_retries': max_retries,
                'created_at': datetime.now().isoformat()
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("workflow_id,name,description,workflow_type,steps_count,timeout,max_retries")
            click.echo(f"{created_workflow_id},{name},{description},{workflow_type},{len(steps_data)},{timeout},{max_retries}")
        else:
            # Table format
            click.echo(f"Workflow '{name}' created successfully!")
            click.echo("=" * 50)
            click.echo(f"Workflow ID: {created_workflow_id}")
            click.echo(f"Name: {name}")
            click.echo(f"Description: {description}")
            click.echo(f"Type: {workflow_type}")
            click.echo(f"Steps: {len(steps_data)}")
            click.echo(f"Timeout: {timeout} seconds")
            click.echo(f"Max Retries: {max_retries}")
            if schedule:
                click.echo(f"Schedule: {schedule}")
        
        logger.info(f"Workflow {created_workflow_id} created successfully")
        
    except Exception as e:
        logger.error(f"Workflow creation failed for {workflow_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--workflow-id', required=True, help='Workflow identifier')
@click.option('--context', type=click.Path(exists=True), help='Path to context JSON file')
@click.option('--priority', default='normal', type=click.Choice(['low', 'normal', 'high']), help='Execution priority')
@click.option('--output', type=click.Path(), help='Output file for execution result')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--wait', is_flag=True, help='Wait for execution to complete')
@click.option('--timeout', default=600, type=int, help='Wait timeout in seconds')
def execute(workflow_id: str, context: Optional[str], priority: str, output: Optional[str],
            format: str, wait: bool, timeout: int):
    """
    Execute a workflow.
    
    This command initiates workflow execution with optional context
    and priority settings.
    
    Examples:
        arx workflow execute --workflow-id test_workflow
        arx workflow execute --workflow-id export_workflow --context context.json --wait
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        # Load context from file or use empty
        execution_context = {}
        if context:
            with open(context, 'r') as f:
                execution_context = json.load(f)
            logger.info(f"Loaded context from {context}")
        
        # Execute workflow
        logger.info(f"Executing workflow {workflow_id}")
        execution_id = workflow_service.execute_workflow(
            workflow_id=workflow_id,
            context=execution_context
        )
        
        # Wait for completion if requested
        if wait:
            logger.info(f"Waiting for execution {execution_id} to complete...")
            start_time = datetime.now()
            
            while True:
                status = workflow_service.get_workflow_status(execution_id)
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    logger.warning(f"Execution timeout after {timeout} seconds")
                    break
                
                import time
                time.sleep(1)
        
        # Get final status
        status = workflow_service.get_workflow_status(execution_id)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'execution_id': execution_id,
                    'workflow_id': workflow_id,
                    'status': status,
                    'context': execution_context,
                    'priority': priority
                }, f, indent=2, default=str)
            logger.info(f"Execution result saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'status': status['status'],
                'progress': status['progress'],
                'current_step': status['current_step'],
                'start_time': status['start_time'],
                'end_time': status['end_time'],
                'error': status.get('error')
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("execution_id,workflow_id,status,progress,current_step,start_time,end_time")
            click.echo(f"{execution_id},{workflow_id},{status['status']},{status['progress']},{status.get('current_step', '')},{status['start_time']},{status.get('end_time', '')}")
        else:
            # Table format
            click.echo(f"Workflow execution started!")
            click.echo("=" * 40)
            click.echo(f"Execution ID: {execution_id}")
            click.echo(f"Workflow ID: {workflow_id}")
            click.echo(f"Status: {status['status']}")
            click.echo(f"Progress: {status['progress']:.1f}%")
            if status.get('current_step'):
                click.echo(f"Current Step: {status['current_step']}")
            click.echo(f"Start Time: {status['start_time']}")
            if status.get('end_time'):
                click.echo(f"End Time: {status['end_time']}")
            if status.get('error'):
                click.echo(f"Error: {status['error']}")
        
        logger.info(f"Workflow execution {execution_id} completed with status {status['status']}")
        
    except Exception as e:
        logger.error(f"Workflow execution failed for {workflow_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--execution-id', required=True, help='Execution identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for status')
def status(execution_id: str, format: str, output: Optional[str]):
    """
    Get status of a workflow execution.
    
    This command provides real-time status information about a workflow
    execution including progress and current step.
    
    Examples:
        arx workflow status --execution-id exec_123
        arx workflow status --execution-id exec_456 --format json
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        logger.info(f"Getting status for execution {execution_id}")
        status = workflow_service.get_workflow_status(execution_id)
        
        if 'error' in status:
            raise click.ClickException(f"Execution not found: {status['error']}")
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(status, f, indent=2, default=str)
            logger.info(f"Status saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(status, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("execution_id,workflow_id,status,progress,current_step,start_time,end_time,error")
            click.echo(f"{status['execution_id']},{status['workflow_id']},{status['status']},{status['progress']},{status.get('current_step', '')},{status['start_time']},{status.get('end_time', '')},{status.get('error', '')}")
        else:
            # Table format
            click.echo(f"Execution Status: {execution_id}")
            click.echo("=" * 40)
            click.echo(f"Workflow ID: {status['workflow_id']}")
            click.echo(f"Status: {status['status']}")
            click.echo(f"Progress: {status['progress']:.1f}%")
            if status.get('current_step'):
                click.echo(f"Current Step: {status['current_step']}")
            click.echo(f"Start Time: {status['start_time']}")
            if status.get('end_time'):
                click.echo(f"End Time: {status['end_time']}")
            if status.get('error'):
                click.echo(f"Error: {status['error']}")
        
    except Exception as e:
        logger.error(f"Failed to get status for {execution_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--workflow-id', required=True, help='Workflow identifier')
@click.option('--limit', default=50, type=int, help='Maximum number of results to return')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for history')
def history(workflow_id: str, limit: int, format: str, output: Optional[str]):
    """
    Get execution history for a workflow.
    
    This command provides detailed history of workflow executions including
    status, timing, and results.
    
    Examples:
        arx workflow history --workflow-id test_workflow
        arx workflow history --workflow-id export_workflow --limit 10 --format json
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        if limit < 1 or limit > 1000:
            raise click.BadParameter("Limit must be between 1 and 1000")
        
        logger.info(f"Getting execution history for workflow {workflow_id}")
        history = workflow_service.get_workflow_history(workflow_id, limit)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'workflow_id': workflow_id,
                    'executions': history,
                    'total_executions': len(history)
                }, f, indent=2, default=str)
            logger.info(f"History saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'workflow_id': workflow_id,
                'executions': history,
                'total_executions': len(history)
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("execution_id,workflow_id,status,start_time,end_time,current_step,progress,error")
            for execution in history:
                click.echo(f"{execution['execution_id']},{execution['workflow_id']},{execution['status']},{execution['start_time']},{execution.get('end_time', '')},{execution.get('current_step', '')},{execution['progress']},{execution.get('error', '')}")
        else:
            # Table format
            click.echo(f"Execution History for {workflow_id}")
            click.echo("=" * 50)
            click.echo(f"Total Executions: {len(history)}")
            
            if history:
                click.echo("\nRecent Executions:")
                click.echo("-" * 30)
                for execution in history[:10]:  # Show last 10
                    status_icon = "✓" if execution['status'] == 'completed' else "✗" if execution['status'] == 'failed' else "○"
                    click.echo(f"  {status_icon} {execution['execution_id']}: {execution['status']} ({execution['progress']:.1f}%)")
            else:
                click.echo("No execution history found.")
        
    except Exception as e:
        logger.error(f"Failed to get execution history for {workflow_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--execution-id', required=True, help='Execution identifier')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
def cancel(execution_id: str, format: str):
    """
    Cancel a workflow execution.
    
    This command allows cancelling running or pending workflow executions.
    
    Examples:
        arx workflow cancel --execution-id exec_123
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        logger.info(f"Cancelling execution {execution_id}")
        success = workflow_service.cancel_workflow(execution_id)
        
        if not success:
            raise click.ClickException(f"Execution {execution_id} not found or cannot be cancelled")
        
        # Get updated status
        status = workflow_service.get_workflow_status(execution_id)
        
        # Display results
        if format == 'json':
            click.echo(json.dumps({
                'execution_id': execution_id,
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat(),
                'final_status': status
            }, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("execution_id,status,cancelled_at")
            click.echo(f"{execution_id},cancelled,{datetime.now().isoformat()}")
        else:
            # Table format
            click.echo(f"Execution cancelled successfully!")
            click.echo("=" * 30)
            click.echo(f"Execution ID: {execution_id}")
            click.echo(f"Status: Cancelled")
            click.echo(f"Cancelled At: {datetime.now().isoformat()}")
        
        logger.info(f"Execution {execution_id} cancelled successfully")
        
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for metrics')
def metrics(format: str, output: Optional[str]):
    """
    Get workflow automation performance metrics.
    
    This command provides comprehensive performance metrics including
    workflow statistics, execution rates, and system health.
    
    Examples:
        arx workflow metrics
        arx workflow metrics --format json --output metrics.json
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        logger.info("Getting workflow automation metrics")
        metrics_data = workflow_service.get_metrics()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            logger.info(f"Metrics saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(metrics_data, indent=2, default=str))
        elif format == 'csv':
            # CSV output for metrics
            click.echo("metric,value")
            for key, value in metrics_data['metrics'].items():
                click.echo(f"{key},{value}")
            click.echo(f"active_workflows,{metrics_data['active_workflows']}")
            click.echo(f"active_executions,{metrics_data['active_executions']}")
            click.echo(f"database_size,{metrics_data['database_size']}")
        else:
            # Table format
            click.echo("Workflow Automation Performance Metrics")
            click.echo("=" * 40)
            click.echo(f"Total Workflows: {metrics_data['metrics']['total_workflows']}")
            click.echo(f"Successful Workflows: {metrics_data['metrics']['successful_workflows']}")
            click.echo(f"Failed Workflows: {metrics_data['metrics']['failed_workflows']}")
            click.echo(f"Total Executions: {metrics_data['metrics']['total_executions']}")
            click.echo(f"Successful Executions: {metrics_data['metrics']['successful_executions']}")
            click.echo(f"Failed Executions: {metrics_data['metrics']['failed_executions']}")
            click.echo(f"Average Execution Time: {metrics_data['metrics']['average_execution_time']:.2f} seconds")
            click.echo(f"Active Workflows: {metrics_data['active_workflows']}")
            click.echo(f"Active Executions: {metrics_data['active_executions']}")
            click.echo(f"Database Size: {metrics_data['database_size']} bytes")
            
            # Calculate success rates
            total_workflows = metrics_data['metrics']['total_workflows']
            successful_workflows = metrics_data['metrics']['successful_workflows']
            if total_workflows > 0:
                workflow_success_rate = (successful_workflows / total_workflows) * 100
                click.echo(f"Workflow Success Rate: {workflow_success_rate:.1f}%")
            
            total_executions = metrics_data['metrics']['total_executions']
            successful_executions = metrics_data['metrics']['successful_executions']
            if total_executions > 0:
                execution_success_rate = (successful_executions / total_executions) * 100
                click.echo(f"Execution Success Rate: {execution_success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), help='Output format')
@click.option('--output', type=click.Path(), help='Output file for workflow list')
def list(format: str, output: Optional[str]):
    """
    List all available workflows.
    
    This command provides access to all workflow definitions including
    their basic information and configuration.
    
    Examples:
        arx workflow list
        arx workflow list --format json --output workflows.json
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        logger.info("Getting workflow list")
        workflows = workflow_service.list_workflows()
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump(workflows, f, indent=2, default=str)
            logger.info(f"Workflow list saved to {output}")
        
        # Display results
        if format == 'json':
            click.echo(json.dumps(workflows, indent=2, default=str))
        elif format == 'csv':
            # CSV output
            click.echo("workflow_id,name,description,workflow_type,steps_count,timeout,max_retries")
            for workflow in workflows:
                click.echo(f"{workflow['workflow_id']},{workflow['name']},{workflow.get('description', '')},{workflow['workflow_type']},{workflow['steps_count']},{workflow['timeout']},{workflow['max_retries']}")
        else:
            # Table format
            click.echo("Available Workflows")
            click.echo("=" * 30)
            click.echo(f"Total Workflows: {len(workflows)}")
            
            for workflow in workflows:
                click.echo(f"\nWorkflow: {workflow['name']}")
                click.echo(f"  ID: {workflow['workflow_id']}")
                click.echo(f"  Type: {workflow['workflow_type']}")
                click.echo(f"  Steps: {workflow['steps_count']}")
                click.echo(f"  Timeout: {workflow['timeout']}s")
                click.echo(f"  Max Retries: {workflow['max_retries']}")
                if workflow.get('description'):
                    click.echo(f"  Description: {workflow['description']}")
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
@click.option('--workflow-id', help='Workflow identifier to test')
@click.option('--steps', type=click.Path(exists=True), help='Path to steps JSON file')
@click.option('--context', type=click.Path(exists=True), help='Path to context JSON file')
@click.option('--output', type=click.Path(), help='Output file for test results')
def test(workflow_id: Optional[str], steps: Optional[str], context: Optional[str], output: Optional[str]):
    """
    Test workflow automation functionality.
    
    This command provides a way to test workflow automation functionality
    using sample data or provided files.
    
    Examples:
        arx workflow test
        arx workflow test --workflow-id test_workflow --steps steps.json --context context.json
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        # Use provided workflow ID or generate one
        test_workflow_id = workflow_id or f"test_workflow_{int(datetime.now().timestamp())}"
        
        # Load steps from file or create sample
        if steps:
            with open(steps, 'r') as f:
                steps_data = json.load(f)
            logger.info(f"Loaded steps from {steps}")
        else:
            # Create sample steps
            steps_data = [
                {
                    "step_id": "test_step_1",
                    "name": "Test Step 1",
                    "step_type": "validation",
                    "parameters": {
                        "service": "test_service",
                        "auto_apply_fixes": True
                    },
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 2
                },
                {
                    "step_id": "test_step_2",
                    "name": "Test Step 2",
                    "step_type": "notify",
                    "parameters": {
                        "method": "email",
                        "template": "test_template",
                        "recipients": ["test@example.com"]
                    },
                    "conditions": [],
                    "timeout": 60,
                    "retry_count": 1
                }
            ]
            logger.info("Using sample steps")
        
        # Load context from file or create sample
        if context:
            with open(context, 'r') as f:
                test_context = json.load(f)
            logger.info(f"Loaded context from {context}")
        else:
            # Create sample context
            test_context = {
                "test_data": "sample_data",
                "timestamp": datetime.now().isoformat(),
                "test_mode": True
            }
            logger.info("Using sample context")
        
        # Create workflow
        workflow_data = {
            "workflow_id": test_workflow_id,
            "name": f"Test Workflow {test_workflow_id}",
            "description": "Test workflow for functionality testing",
            "workflow_type": "validation",
            "steps": steps_data,
            "timeout": 600,
            "max_retries": 2
        }
        
        created_workflow_id = workflow_service.create_workflow(workflow_data)
        
        # Execute workflow
        click.echo(f"Testing workflow automation for workflow: {created_workflow_id}")
        click.echo(f"Steps to execute: {len(steps_data)}")
        
        execution_id = workflow_service.execute_workflow(
            workflow_id=created_workflow_id,
            context=test_context
        )
        
        # Wait for completion
        logger.info(f"Waiting for test execution {execution_id} to complete...")
        start_time = datetime.now()
        timeout = 300  # 5 minutes
        
        while True:
            status = workflow_service.get_workflow_status(execution_id)
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                logger.warning(f"Test execution timeout after {timeout} seconds")
                break
            
            import time
            time.sleep(1)
        
        # Get final status
        final_status = workflow_service.get_workflow_status(execution_id)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                json.dump({
                    'workflow_id': created_workflow_id,
                    'execution_id': execution_id,
                    'status': final_status,
                    'context': test_context,
                    'steps': steps_data
                }, f, indent=2, default=str)
            logger.info(f"Test results saved to {output}")
        
        # Display results
        click.echo(f"Test completed successfully!")
        click.echo(f"  Workflow ID: {created_workflow_id}")
        click.echo(f"  Execution ID: {execution_id}")
        click.echo(f"  Status: {final_status['status']}")
        click.echo(f"  Progress: {final_status['progress']:.1f}%")
        click.echo(f"  Start Time: {final_status['start_time']}")
        if final_status.get('end_time'):
            click.echo(f"  End Time: {final_status['end_time']}")
        if final_status.get('error'):
            click.echo(f"  Error: {final_status['error']}")
        
        # Check status
        history = workflow_service.get_workflow_history(created_workflow_id, limit=1)
        if history:
            click.echo(f"  Workflow Status: Tested")
        else:
            click.echo(f"  Workflow Status: Not found")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflow.command()
def health():
    """
    Check workflow automation service health.
    
    This command provides a health check for the workflow automation service
    including database connectivity and basic functionality.
    
    Examples:
        arx workflow health
    """
    try:
        workflow_service = WorkflowAutomationService()
        
        # Get metrics as a health check
        metrics = workflow_service.get_metrics()
        
        click.echo("Workflow Automation Service Health Check")
        click.echo("=" * 40)
        click.echo(f"Status: Healthy")
        click.echo(f"Database accessible: Yes")
        click.echo(f"Active workflows: {metrics['active_workflows']}")
        click.echo(f"Active executions: {metrics['active_executions']}")
        click.echo(f"Database size: {metrics['database_size']} bytes")
        click.echo(f"Total workflows: {metrics['metrics']['total_workflows']}")
        
        # Test basic functionality
        workflows = workflow_service.list_workflows()
        if len(workflows) > 0:
            click.echo("Basic functionality: OK")
        else:
            click.echo("Basic functionality: Warning (no workflows found)")
        
        click.echo("Health check completed successfully!")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"Health check failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    workflow() 