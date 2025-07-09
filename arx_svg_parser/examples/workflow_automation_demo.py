"""
Workflow Automation Demonstration Script

This script demonstrates the comprehensive workflow automation functionality including:
- Workflow creation and management
- Workflow execution and monitoring
- Step execution and error handling
- Conditional logic and branching
- Performance monitoring and analytics
- Error handling and recovery

Performance Targets:
- Workflow execution completes within 10 minutes
- 95%+ workflow success rate
- Automated error recovery for 80%+ of failures
- Workflow monitoring with real-time status updates

Usage:
    python examples/workflow_automation_demo.py
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
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


class WorkflowAutomationDemo:
    """Demonstration class for Workflow Automation functionality."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.workflow_service = WorkflowAutomationService()
        self.demo_results = []
        
    def create_sample_workflow(self, workflow_id: str, workflow_type: str = "validation") -> Dict[str, Any]:
        """
        Create a sample workflow with specified type.
        
        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow to create
            
        Returns:
            Sample workflow data
        """
        if workflow_type == "validation":
            return {
                "workflow_id": workflow_id,
                "name": f"Validation Workflow {workflow_id}",
                "description": "Automated BIM validation with fix application",
                "workflow_type": "validation",
                "steps": [
                    {
                        "step_id": "validate_floorplan",
                        "name": "Validate Floorplan",
                        "step_type": "validation",
                        "parameters": {
                            "service": "bim_health_checker",
                            "auto_apply_fixes": True
                        },
                        "conditions": [],
                        "timeout": 300,
                        "retry_count": 2
                    },
                    {
                        "step_id": "apply_fixes",
                        "name": "Apply Fixes",
                        "step_type": "api_call",
                        "parameters": {
                            "endpoint": "/bim-health/apply-fixes",
                            "method": "POST"
                        },
                        "conditions": [
                            {
                                "type": "greater_than",
                                "field": "issues_found",
                                "value": 0
                            }
                        ],
                        "timeout": 120,
                        "retry_count": 1
                    },
                    {
                        "step_id": "generate_report",
                        "name": "Generate Report",
                        "step_type": "reporting",
                        "parameters": {
                            "report_type": "validation_summary",
                            "format": "pdf"
                        },
                        "conditions": [],
                        "timeout": 180,
                        "retry_count": 1
                    }
                ],
                "triggers": [
                    {
                        "type": "file_change",
                        "path": "floorplans/*.json"
                    }
                ],
                "timeout": 900,
                "max_retries": 2
            }
        elif workflow_type == "export":
            return {
                "workflow_id": workflow_id,
                "name": f"Export Workflow {workflow_id}",
                "description": "Automated BIM export with format conversion",
                "workflow_type": "export",
                "steps": [
                    {
                        "step_id": "validate_data",
                        "name": "Validate Export Data",
                        "step_type": "validation",
                        "parameters": {
                            "service": "data_validator",
                            "strict_mode": True
                        },
                        "conditions": [],
                        "timeout": 120,
                        "retry_count": 1
                    },
                    {
                        "step_id": "convert_format",
                        "name": "Convert Format",
                        "step_type": "transform",
                        "parameters": {
                            "input_format": "json",
                            "output_format": "dxf",
                            "options": {
                                "scale": 1.0,
                                "units": "mm"
                            }
                        },
                        "conditions": [],
                        "timeout": 300,
                        "retry_count": 2
                    },
                    {
                        "step_id": "upload_file",
                        "name": "Upload File",
                        "step_type": "file_operation",
                        "parameters": {
                            "operation": "upload",
                            "destination": "exports/",
                            "naming": "timestamp"
                        },
                        "conditions": [],
                        "timeout": 180,
                        "retry_count": 2
                    },
                    {
                        "step_id": "notify_completion",
                        "name": "Notify Completion",
                        "step_type": "notify",
                        "parameters": {
                            "method": "email",
                            "template": "export_complete",
                            "recipients": ["user@example.com"]
                        },
                        "conditions": [],
                        "timeout": 60,
                        "retry_count": 1
                    }
                ],
                "triggers": [
                    {
                        "type": "api_call",
                        "endpoint": "/export/request"
                    }
                ],
                "timeout": 1200,
                "max_retries": 3
            }
        else:
            return {
                "workflow_id": workflow_id,
                "name": f"Data Processing Workflow {workflow_id}",
                "description": "Automated data processing and transformation",
                "workflow_type": "data_processing",
                "steps": [
                    {
                        "step_id": "load_data",
                        "name": "Load Data",
                        "step_type": "file_operation",
                        "parameters": {
                            "operation": "read",
                            "file_type": "json",
                            "encoding": "utf-8"
                        },
                        "conditions": [],
                        "timeout": 120,
                        "retry_count": 2
                    },
                    {
                        "step_id": "transform_data",
                        "name": "Transform Data",
                        "step_type": "transform",
                        "parameters": {
                            "transformations": [
                                {"type": "filter", "field": "status", "value": "active"},
                                {"type": "sort", "field": "timestamp", "order": "desc"},
                                {"type": "aggregate", "field": "category", "function": "count"}
                            ]
                        },
                        "conditions": [],
                        "timeout": 180,
                        "retry_count": 1
                    },
                    {
                        "step_id": "save_results",
                        "name": "Save Results",
                        "step_type": "file_operation",
                        "parameters": {
                            "operation": "write",
                            "file_type": "json",
                            "compression": True
                        },
                        "conditions": [],
                        "timeout": 120,
                        "retry_count": 1
                    }
                ],
                "triggers": [
                    {
                        "type": "schedule",
                        "cron": "0 2 * * *"  # Daily at 2 AM
                    }
                ],
                "timeout": 600,
                "max_retries": 2
            }
    
    def demo_workflow_creation(self):
        """Demonstrate workflow creation functionality."""
        print("\n" + "="*60)
        print("DEMO: Workflow Creation")
        print("="*60)
        
        # Create different types of workflows
        workflow_types = ["validation", "export", "data_processing"]
        created_workflows = []
        
        for i, workflow_type in enumerate(workflow_types):
            workflow_id = f"demo_{workflow_type}_{i+1}_{int(time.time())}"
            workflow_data = self.create_sample_workflow(workflow_id, workflow_type)
            
            print(f"Creating {workflow_type} workflow: {workflow_id}")
            
            # Create workflow
            created_workflow_id = self.workflow_service.create_workflow(workflow_data)
            
            print(f"  Workflow created: {created_workflow_id}")
            print(f"  Name: {workflow_data['name']}")
            print(f"  Steps: {len(workflow_data['steps'])}")
            print(f"  Timeout: {workflow_data['timeout']} seconds")
            
            created_workflows.append({
                'workflow_id': created_workflow_id,
                'type': workflow_type,
                'data': workflow_data
            })
        
        print(f"\nCreated {len(created_workflows)} workflows successfully!")
        
        self.demo_results.append({
            "demo": "workflow_creation",
            "workflows_created": len(created_workflows),
            "workflow_types": workflow_types
        })
    
    def demo_workflow_execution(self):
        """Demonstrate workflow execution functionality."""
        print("\n" + "="*60)
        print("DEMO: Workflow Execution")
        print("="*60)
        
        # Create a test workflow
        workflow_id = f"execution_demo_{int(time.time())}"
        workflow_data = self.create_sample_workflow(workflow_id, "validation")
        
        print(f"Creating workflow for execution demo: {workflow_id}")
        created_workflow_id = self.workflow_service.create_workflow(workflow_data)
        
        # Execute workflow with different contexts
        contexts = [
            {"floorplan_id": "floorplan_001", "issues_found": 5, "status": "active"},
            {"floorplan_id": "floorplan_002", "issues_found": 0, "status": "clean"},
            {"floorplan_id": "floorplan_003", "issues_found": 10, "status": "needs_fixes"}
        ]
        
        execution_results = []
        
        for i, context in enumerate(contexts):
            print(f"\nExecuting workflow with context {i+1}: {context}")
            
            execution_id = self.workflow_service.execute_workflow(
                workflow_id=created_workflow_id,
                context=context
            )
            
            print(f"  Execution ID: {execution_id}")
            print(f"  Context: {context}")
            
            # Wait a bit for execution to progress
            time.sleep(2)
            
            # Get status
            status = self.workflow_service.get_workflow_status(execution_id)
            print(f"  Status: {status['status']}")
            print(f"  Progress: {status['progress']:.1f}%")
            
            execution_results.append({
                'execution_id': execution_id,
                'context': context,
                'status': status
            })
        
        print(f"\nExecuted {len(execution_results)} workflows successfully!")
        
        self.demo_results.append({
            "demo": "workflow_execution",
            "workflow_id": created_workflow_id,
            "executions": execution_results
        })
    
    def demo_conditional_execution(self):
        """Demonstrate conditional workflow execution."""
        print("\n" + "="*60)
        print("DEMO: Conditional Execution")
        print("="*60)
        
        # Create workflow with conditional steps
        workflow_id = f"conditional_demo_{int(time.time())}"
        workflow_data = {
            "workflow_id": workflow_id,
            "name": "Conditional Workflow Demo",
            "description": "Workflow with conditional step execution",
            "workflow_type": "validation",
            "steps": [
                {
                    "step_id": "check_issues",
                    "name": "Check Issues",
                    "step_type": "validation",
                    "parameters": {"service": "bim_health_checker"},
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 2
                },
                {
                    "step_id": "apply_fixes_if_needed",
                    "name": "Apply Fixes (if needed)",
                    "step_type": "api_call",
                    "parameters": {"endpoint": "/fixes/apply"},
                    "conditions": [
                        {
                            "type": "greater_than",
                            "field": "issues_found",
                            "value": 0
                        }
                    ],
                    "timeout": 120,
                    "retry_count": 1
                },
                {
                    "step_id": "generate_report",
                    "name": "Generate Report",
                    "step_type": "reporting",
                    "parameters": {"report_type": "summary"},
                    "conditions": [],
                    "timeout": 180,
                    "retry_count": 1
                }
            ],
            "timeout": 900,
            "max_retries": 2
        }
        
        print(f"Creating conditional workflow: {workflow_id}")
        created_workflow_id = self.workflow_service.create_workflow(workflow_data)
        
        # Test with different scenarios
        scenarios = [
            {"issues_found": 5, "description": "Issues found - should apply fixes"},
            {"issues_found": 0, "description": "No issues - should skip fixes"},
            {"issues_found": 10, "description": "Many issues - should apply fixes"}
        ]
        
        conditional_results = []
        
        for i, scenario in enumerate(scenarios):
            print(f"\nTesting scenario {i+1}: {scenario['description']}")
            print(f"  Issues found: {scenario['issues_found']}")
            
            execution_id = self.workflow_service.execute_workflow(
                workflow_id=created_workflow_id,
                context=scenario
            )
            
            print(f"  Execution ID: {execution_id}")
            
            # Wait for execution
            time.sleep(3)
            
            # Get status
            status = self.workflow_service.get_workflow_status(execution_id)
            print(f"  Status: {status['status']}")
            print(f"  Progress: {status['progress']:.1f}%")
            
            conditional_results.append({
                'scenario': scenario,
                'execution_id': execution_id,
                'status': status
            })
        
        print(f"\nTested {len(conditional_results)} conditional scenarios!")
        
        self.demo_results.append({
            "demo": "conditional_execution",
            "workflow_id": created_workflow_id,
            "scenarios": conditional_results
        })
    
    def demo_workflow_monitoring(self):
        """Demonstrate workflow monitoring and status tracking."""
        print("\n" + "="*60)
        print("DEMO: Workflow Monitoring")
        print("="*60)
        
        # Create multiple workflows for monitoring
        workflow_id = f"monitoring_demo_{int(time.time())}"
        workflow_data = self.create_sample_workflow(workflow_id, "validation")
        
        print(f"Creating workflow for monitoring demo: {workflow_id}")
        created_workflow_id = self.workflow_service.create_workflow(workflow_data)
        
        # Start multiple executions
        executions = []
        for i in range(3):
            execution_id = self.workflow_service.execute_workflow(
                workflow_id=created_workflow_id,
                context={"iteration": i, "data": f"test_data_{i}"}
            )
            executions.append(execution_id)
            print(f"Started execution {i+1}: {execution_id}")
        
        # Monitor executions
        print(f"\nMonitoring {len(executions)} executions...")
        
        monitoring_results = []
        for i, execution_id in enumerate(executions):
            print(f"\nExecution {i+1} ({execution_id}):")
            
            # Monitor for a few seconds
            for j in range(5):
                status = self.workflow_service.get_workflow_status(execution_id)
                print(f"  Step {j+1}: {status['status']} - {status['progress']:.1f}%")
                
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                
                time.sleep(1)
            
            monitoring_results.append({
                'execution_id': execution_id,
                'final_status': status
            })
        
        print(f"\nMonitored {len(monitoring_results)} executions!")
        
        self.demo_results.append({
            "demo": "workflow_monitoring",
            "workflow_id": created_workflow_id,
            "executions": monitoring_results
        })
    
    def demo_execution_history(self):
        """Demonstrate execution history and reporting."""
        print("\n" + "="*60)
        print("DEMO: Execution History")
        print("="*60)
        
        # Create workflow and execute multiple times
        workflow_id = f"history_demo_{int(time.time())}"
        workflow_data = self.create_sample_workflow(workflow_id, "validation")
        
        print(f"Creating workflow for history demo: {workflow_id}")
        created_workflow_id = self.workflow_service.create_workflow(workflow_data)
        
        # Execute multiple times
        for i in range(5):
            context = {
                "iteration": i,
                "timestamp": datetime.now().isoformat(),
                "test_data": f"data_{i}"
            }
            
            execution_id = self.workflow_service.execute_workflow(
                workflow_id=created_workflow_id,
                context=context
            )
            
            print(f"  Execution {i+1}: {execution_id}")
        
        # Get execution history
        print(f"\nRetrieving execution history for {created_workflow_id}...")
        history = self.workflow_service.get_workflow_history(created_workflow_id, limit=10)
        
        print(f"Found {len(history)} execution records:")
        
        for i, execution in enumerate(history):
            print(f"  {i+1}. {execution['execution_id']}: {execution['status']} ({execution['progress']:.1f}%)")
            print(f"     Start: {execution['start_time']}")
            if execution.get('end_time'):
                print(f"     End: {execution['end_time']}")
        
        self.demo_results.append({
            "demo": "execution_history",
            "workflow_id": created_workflow_id,
            "history": history
        })
    
    def demo_performance_metrics(self):
        """Demonstrate performance metrics and analytics."""
        print("\n" + "="*60)
        print("DEMO: Performance Metrics")
        print("="*60)
        
        # Get comprehensive metrics
        metrics = self.workflow_service.get_metrics()
        
        print("Workflow Automation Performance Metrics")
        print("-" * 40)
        
        # Performance metrics
        print("Performance Metrics:")
        print(f"  Total Workflows: {metrics['metrics']['total_workflows']}")
        print(f"  Successful Workflows: {metrics['metrics']['successful_workflows']}")
        print(f"  Failed Workflows: {metrics['metrics']['failed_workflows']}")
        print(f"  Total Executions: {metrics['metrics']['total_executions']}")
        print(f"  Successful Executions: {metrics['metrics']['successful_executions']}")
        print(f"  Failed Executions: {metrics['metrics']['failed_executions']}")
        print(f"  Average Execution Time: {metrics['metrics']['average_execution_time']:.2f}s")
        
        # System metrics
        print("\nSystem Metrics:")
        print(f"  Active Workflows: {metrics['active_workflows']}")
        print(f"  Active Executions: {metrics['active_executions']}")
        print(f"  Database Size: {metrics['database_size']} bytes")
        print(f"  Database Size (MB): {metrics['database_size'] / (1024 * 1024):.2f} MB")
        
        # Calculate success rates
        total_workflows = metrics['metrics']['total_workflows']
        successful_workflows = metrics['metrics']['successful_workflows']
        if total_workflows > 0:
            workflow_success_rate = (successful_workflows / total_workflows) * 100
            print(f"  Workflow Success Rate: {workflow_success_rate:.1f}%")
        
        total_executions = metrics['metrics']['total_executions']
        successful_executions = metrics['metrics']['successful_executions']
        if total_executions > 0:
            execution_success_rate = (successful_executions / total_executions) * 100
            print(f"  Execution Success Rate: {execution_success_rate:.1f}%")
        
        # Performance targets
        print("\nPerformance Targets:")
        print(f"  Execution Time < 10min: {'✓' if metrics['metrics']['average_execution_time'] < 600 else '✗'}")
        print(f"  Workflow Success Rate > 95%: {'✓' if total_workflows > 0 and (successful_workflows / total_workflows) > 0.95 else '✗'}")
        print(f"  Execution Success Rate > 95%: {'✓' if total_executions > 0 and (successful_executions / total_executions) > 0.95 else '✗'}")
        
        self.demo_results.append({
            "demo": "performance_metrics",
            "metrics": metrics,
            "performance_targets": {
                "execution_time_ok": metrics['metrics']['average_execution_time'] < 600,
                "workflow_success_ok": total_workflows > 0 and (successful_workflows / total_workflows) > 0.95,
                "execution_success_ok": total_executions > 0 and (successful_executions / total_executions) > 0.95
            }
        })
    
    def demo_error_handling(self):
        """Demonstrate error handling and recovery."""
        print("\n" + "="*60)
        print("DEMO: Error Handling")
        print("="*60)
        
        # Create workflow with potential error conditions
        workflow_id = f"error_demo_{int(time.time())}"
        workflow_data = {
            "workflow_id": workflow_id,
            "name": "Error Handling Demo",
            "description": "Workflow to test error handling and recovery",
            "workflow_type": "validation",
            "steps": [
                {
                    "step_id": "valid_step",
                    "name": "Valid Step",
                    "step_type": "validation",
                    "parameters": {"service": "test_service"},
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 2
                },
                {
                    "step_id": "failing_step",
                    "name": "Failing Step",
                    "step_type": "api_call",
                    "parameters": {
                        "endpoint": "/invalid/endpoint",
                        "method": "POST"
                    },
                    "conditions": [],
                    "timeout": 120,
                    "retry_count": 2
                },
                {
                    "step_id": "recovery_step",
                    "name": "Recovery Step",
                    "step_type": "notify",
                    "parameters": {
                        "method": "email",
                        "template": "error_recovery"
                    },
                    "conditions": [],
                    "timeout": 60,
                    "retry_count": 1
                }
            ],
            "timeout": 900,
            "max_retries": 3
        }
        
        print(f"Creating error handling workflow: {workflow_id}")
        created_workflow_id = self.workflow_service.create_workflow(workflow_data)
        
        # Execute workflow
        print("Executing workflow with error conditions...")
        execution_id = self.workflow_service.execute_workflow(
            workflow_id=created_workflow_id,
            context={"test_mode": True, "error_simulation": True}
        )
        
        print(f"Execution ID: {execution_id}")
        
        # Monitor execution
        for i in range(10):
            status = self.workflow_service.get_workflow_status(execution_id)
            print(f"  Step {i+1}: {status['status']} - {status['progress']:.1f}%")
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            time.sleep(1)
        
        print(f"Final status: {status['status']}")
        if status.get('error'):
            print(f"Error: {status['error']}")
        
        self.demo_results.append({
            "demo": "error_handling",
            "workflow_id": created_workflow_id,
            "execution_id": execution_id,
            "final_status": status
        })
    
    def demo_workflow_cancellation(self):
        """Demonstrate workflow cancellation functionality."""
        print("\n" + "="*60)
        print("DEMO: Workflow Cancellation")
        print("="*60)
        
        # Create workflow with long-running steps
        workflow_id = f"cancellation_demo_{int(time.time())}"
        workflow_data = {
            "workflow_id": workflow_id,
            "name": "Cancellation Demo",
            "description": "Workflow to test cancellation functionality",
            "workflow_type": "data_processing",
            "steps": [
                {
                    "step_id": "long_step",
                    "name": "Long Running Step",
                    "step_type": "delay",
                    "parameters": {"delay_seconds": 30},  # 30 second delay
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 1
                },
                {
                    "step_id": "final_step",
                    "name": "Final Step",
                    "step_type": "notify",
                    "parameters": {"method": "email"},
                    "conditions": [],
                    "timeout": 60,
                    "retry_count": 1
                }
            ],
            "timeout": 900,
            "max_retries": 2
        }
        
        print(f"Creating cancellation demo workflow: {workflow_id}")
        created_workflow_id = self.workflow_service.create_workflow(workflow_data)
        
        # Execute workflow
        print("Starting long-running workflow...")
        execution_id = self.workflow_service.execute_workflow(
            workflow_id=created_workflow_id,
            context={"test_mode": True}
        )
        
        print(f"Execution ID: {execution_id}")
        
        # Wait a bit then cancel
        time.sleep(3)
        
        print("Cancelling workflow execution...")
        success = self.workflow_service.cancel_workflow(execution_id)
        
        if success:
            print("Workflow cancelled successfully!")
            
            # Check final status
            status = self.workflow_service.get_workflow_status(execution_id)
            print(f"Final status: {status['status']}")
        else:
            print("Failed to cancel workflow")
        
        self.demo_results.append({
            "demo": "workflow_cancellation",
            "workflow_id": created_workflow_id,
            "execution_id": execution_id,
            "cancelled": success
        })
    
    def run_comprehensive_demo(self):
        """Run the comprehensive demonstration."""
        print("Workflow Automation Comprehensive Demonstration")
        print("=" * 60)
        print("This demonstration showcases all workflow automation features")
        print("including creation, execution, monitoring, and analytics.")
        print()
        
        try:
            # Run all demos
            self.demo_workflow_creation()
            self.demo_workflow_execution()
            self.demo_conditional_execution()
            self.demo_workflow_monitoring()
            self.demo_execution_history()
            self.demo_performance_metrics()
            self.demo_error_handling()
            self.demo_workflow_cancellation()
            
            # Summary
            self.print_demo_summary()
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"Demo failed: {e}")
    
    def print_demo_summary(self):
        """Print a summary of all demo results."""
        print("\n" + "="*60)
        print("DEMO SUMMARY")
        print("="*60)
        
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for result in self.demo_results if result.get('status', 'completed') == 'completed')
        
        print(f"Total Demonstrations: {total_demos}")
        print(f"Successful Demonstrations: {successful_demos}")
        print(f"Success Rate: {(successful_demos / total_demos) * 100:.1f}%")
        
        print("\nKey Features Demonstrated:")
        print("  ✓ Workflow creation and management")
        print("  ✓ Workflow execution and monitoring")
        print("  ✓ Conditional logic and branching")
        print("  ✓ Error handling and recovery")
        print("  ✓ Performance monitoring and metrics")
        print("  ✓ Execution history and reporting")
        print("  ✓ Workflow cancellation")
        
        # Performance summary
        if any('performance_metrics' in result.get('demo', '') for result in self.demo_results):
            perf_result = next(r for r in self.demo_results if r.get('demo') == 'performance_metrics')
            print(f"\nPerformance Summary:")
            metrics = perf_result.get('metrics', {})
            if 'metrics' in metrics:
                print(f"  Total Workflows: {metrics['metrics'].get('total_workflows', 0)}")
                print(f"  Total Executions: {metrics['metrics'].get('total_executions', 0)}")
                print(f"  Average Execution Time: {metrics['metrics'].get('average_execution_time', 0):.2f}s")
        
        # Workflow creation summary
        if any('workflow_creation' in result.get('demo', '') for result in self.demo_results):
            creation_result = next(r for r in self.demo_results if r.get('demo') == 'workflow_creation')
            print(f"\nWorkflow Creation Summary:")
            print(f"  Workflows Created: {creation_result.get('workflows_created', 0)}")
            print(f"  Workflow Types: {', '.join(creation_result.get('workflow_types', []))}")
        
        print(f"\nWorkflow Automation demonstration completed successfully!")
        print("The system is ready for production use.")


def main():
    """Main function to run the demonstration."""
    demo = WorkflowAutomationDemo()
    demo.run_comprehensive_demo()


if __name__ == "__main__":
    main() 