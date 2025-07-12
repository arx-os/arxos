"""
Comprehensive Test Suite for Workflow Automation Service

This test suite covers all aspects of the workflow automation functionality including:
- Workflow creation and management
- Workflow execution and monitoring
- Step execution and error handling
- Conditional logic and branching
- Performance monitoring and metrics
- Error handling and recovery
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import time
import threading

from services.workflow_automation import (
    WorkflowAutomationService,
    WorkflowStatus,
    WorkflowType,
    StepType,
    ConditionType,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowExecution,
    StepExecution
)


class TestWorkflowAutomationService:
    """Test suite for the WorkflowAutomationService."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            import os
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.fixture
    def workflow_service(self, temp_db_path):
        """Create a workflow automation service instance for testing."""
        return WorkflowAutomationService(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_workflow_data(self):
        """Sample workflow data for testing."""
        return {
            "workflow_id": "test_workflow_001",
            "name": "Test Workflow",
            "description": "A test workflow for validation",
            "workflow_type": "validation",
            "steps": [
                {
                    "step_id": "validate_data",
                    "name": "Validate Data",
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
                    "step_id": "generate_report",
                    "name": "Generate Report",
                    "step_type": "reporting",
                    "parameters": {
                        "report_type": "validation_summary",
                        "format": "pdf"
                    },
                    "conditions": [
                        {
                            "type": "greater_than",
                            "field": "issues_found",
                            "value": 0
                        }
                    ],
                    "timeout": 180,
                    "retry_count": 1
                }
            ],
            "triggers": [
                {
                    "type": "file_change",
                    "path": "data/*.json"
                }
            ],
            "timeout": 900,
            "max_retries": 3
        }
    
    @pytest.fixture
    def complex_workflow_data(self):
        """Complex workflow data with multiple step types."""
        return {
            "workflow_id": "complex_workflow_001",
            "name": "Complex Test Workflow",
            "description": "A complex workflow with multiple step types",
            "workflow_type": "data_processing",
            "steps": [
                {
                    "step_id": "load_data",
                    "name": "Load Data",
                    "step_type": "file_operation",
                    "parameters": {
                        "operation": "read",
                        "file_type": "json"
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
                            {"type": "sort", "field": "timestamp", "order": "desc"}
                        ]
                    },
                    "conditions": [],
                    "timeout": 180,
                    "retry_count": 1
                },
                {
                    "step_id": "validate_results",
                    "name": "Validate Results",
                    "step_type": "validation",
                    "parameters": {
                        "service": "data_validator",
                        "strict_mode": True
                    },
                    "conditions": [
                        {
                            "type": "greater_than",
                            "field": "records_processed",
                            "value": 0
                        }
                    ],
                    "timeout": 120,
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
                },
                {
                    "step_id": "notify_completion",
                    "name": "Notify Completion",
                    "step_type": "notify",
                    "parameters": {
                        "method": "email",
                        "template": "processing_complete",
                        "recipients": ["user@example.com"]
                    },
                    "conditions": [],
                    "timeout": 60,
                    "retry_count": 1
                }
            ],
            "triggers": [
                {
                    "type": "schedule",
                    "cron": "0 2 * * *"
                }
            ],
            "timeout": 1200,
            "max_retries": 3
        }
    
    def test_service_initialization(self, workflow_service):
        """Test service initialization and database setup."""
        assert workflow_service is not None
        assert workflow_service.db_path is not None
        assert workflow_service.lock is not None
        assert isinstance(workflow_service.metrics, dict)
        assert len(workflow_service.workflows) > 0  # Default workflows loaded
        assert workflow_service.running is True
    
    def test_generate_execution_id(self, workflow_service):
        """Test execution ID generation."""
        execution_id = workflow_service._generate_execution_id()
        
        assert execution_id is not None
        assert execution_id.startswith("exec_")
        assert len(execution_id) > 8
    
    def test_generate_step_execution_id(self, workflow_service):
        """Test step execution ID generation."""
        step_execution_id = workflow_service._generate_step_execution_id()
        
        assert step_execution_id is not None
        assert step_execution_id.startswith("step_")
        assert len(step_execution_id) > 8
    
    def test_create_workflow_from_dict(self, workflow_service, sample_workflow_data):
        """Test workflow creation from dictionary data."""
        workflow = workflow_service._create_workflow_from_dict(sample_workflow_data)
        
        assert workflow.workflow_id == "test_workflow_001"
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow for validation"
        assert workflow.workflow_type == WorkflowType.VALIDATION
        assert len(workflow.steps) == 2
        assert workflow.timeout == 900
        assert workflow.max_retries == 3
        
        # Check steps
        assert workflow.steps[0].step_id == "validate_data"
        assert workflow.steps[0].step_type == StepType.VALIDATION
        assert workflow.steps[1].step_id == "generate_report"
        assert workflow.steps[1].step_type == StepType.REPORTING
    
    def test_evaluate_condition(self, workflow_service):
        """Test condition evaluation."""
        context = {
            "issues_found": 5,
            "status": "active",
            "name": "test_object",
            "value": None
        }
        
        # Test equals condition
        condition = {"type": "equals", "field": "status", "value": "active"}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test not equals condition
        condition = {"type": "not_equals", "field": "status", "value": "inactive"}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test greater than condition
        condition = {"type": "greater_than", "field": "issues_found", "value": 3}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test less than condition
        condition = {"type": "less_than", "field": "issues_found", "value": 10}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test contains condition
        condition = {"type": "contains", "field": "name", "value": "test"}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test not contains condition
        condition = {"type": "not_contains", "field": "name", "value": "invalid"}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test exists condition
        condition = {"type": "exists", "field": "status"}
        assert workflow_service._evaluate_condition(condition, context) is True
        
        # Test not exists condition
        condition = {"type": "not_exists", "field": "missing_field"}
        assert workflow_service._evaluate_condition(condition, context) is True
    
    def test_evaluate_conditions(self, workflow_service):
        """Test multiple condition evaluation."""
        context = {
            "issues_found": 5,
            "status": "active",
            "records_processed": 100
        }
        
        # Test empty conditions
        conditions = []
        assert workflow_service._evaluate_conditions(conditions, context) is True
        
        # Test single condition
        conditions = [
            {"type": "greater_than", "field": "issues_found", "value": 0}
        ]
        assert workflow_service._evaluate_conditions(conditions, context) is True
        
        # Test multiple conditions (all true)
        conditions = [
            {"type": "greater_than", "field": "issues_found", "value": 0},
            {"type": "equals", "field": "status", "value": "active"},
            {"type": "greater_than", "field": "records_processed", "value": 50}
        ]
        assert workflow_service._evaluate_conditions(conditions, context) is True
        
        # Test multiple conditions (one false)
        conditions = [
            {"type": "greater_than", "field": "issues_found", "value": 0},
            {"type": "equals", "field": "status", "value": "inactive"},  # False
            {"type": "greater_than", "field": "records_processed", "value": 50}
        ]
        assert workflow_service._evaluate_conditions(conditions, context) is False
    
    def test_execute_validation_step(self, workflow_service):
        """Test validation step execution."""
        step = WorkflowStep(
            step_id="test_validation",
            name="Test Validation",
            step_type=StepType.VALIDATION,
            parameters={
                "service": "bim_health_checker",
                "auto_apply_fixes": True
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"floorplan_id": "test_floorplan"}
        
        result = workflow_service._execute_validation_step(step, context)
        
        assert result['status'] == 'success'
        assert 'issues_found' in result
        assert 'auto_fixes_applied' in result
        assert 'validation_time' in result
    
    def test_execute_export_step(self, workflow_service):
        """Test export step execution."""
        step = WorkflowStep(
            step_id="test_export",
            name="Test Export",
            step_type=StepType.EXPORT,
            parameters={
                "format": "dxf",
                "destination": "exports/",
                "options": {"scale": 1.0}
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": "test_data"}
        
        result = workflow_service._execute_export_step(step, context)
        
        assert result['status'] == 'success'
        assert 'file_path' in result
        assert 'file_size' in result
        assert 'export_time' in result
    
    def test_execute_transform_step(self, workflow_service):
        """Test transform step execution."""
        step = WorkflowStep(
            step_id="test_transform",
            name="Test Transform",
            step_type=StepType.TRANSFORM,
            parameters={
                "transformations": [
                    {"type": "filter", "field": "status", "value": "active"},
                    {"type": "sort", "field": "timestamp", "order": "desc"}
                ]
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": [{"status": "active", "timestamp": 1234567890}]}
        
        result = workflow_service._execute_transform_step(step, context)
        
        assert result['status'] == 'success'
        assert 'records_processed' in result
        assert 'transformations_applied' in result
        assert 'processing_time' in result
    
    def test_execute_notify_step(self, workflow_service):
        """Test notify step execution."""
        step = WorkflowStep(
            step_id="test_notify",
            name="Test Notify",
            step_type=StepType.NOTIFY,
            parameters={
                "method": "email",
                "template": "test_template",
                "recipients": ["user@example.com"]
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"result": "test_result"}
        
        result = workflow_service._execute_notify_step(step, context)
        
        assert result['status'] == 'success'
        assert result['method'] == 'email'
        assert 'recipients' in result
        assert 'template' in result
        assert 'sent_time' in result
    
    def test_execute_condition_step(self, workflow_service):
        """Test condition step execution."""
        step = WorkflowStep(
            step_id="test_condition",
            name="Test Condition",
            step_type=StepType.CONDITION,
            parameters={
                "conditions": [
                    {"type": "greater_than", "field": "value", "value": 0},
                    {"type": "equals", "field": "status", "value": "active"}
                ]
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"value": 5, "status": "active"}
        
        result = workflow_service._execute_condition_step(step, context)
        
        assert result['status'] == 'success'
        assert result['result'] is True
        assert result['conditions_evaluated'] == 2
    
    def test_execute_loop_step(self, workflow_service):
        """Test loop step execution."""
        step = WorkflowStep(
            step_id="test_loop",
            name="Test Loop",
            step_type=StepType.LOOP,
            parameters={
                "items": ["item1", "item2", "item3"],
                "max_iterations": 10
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": "test_data"}
        
        result = workflow_service._execute_loop_step(step, context)
        
        assert result['status'] == 'success'
        assert result['iterations'] == 3
        assert len(result['results']) == 3
    
    def test_execute_parallel_step(self, workflow_service):
        """Test parallel step execution."""
        sub_step1 = WorkflowStep(
            step_id="sub_step_1",
            name="Sub Step 1",
            step_type=StepType.VALIDATION,
            parameters={"service": "test_service"},
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        sub_step2 = WorkflowStep(
            step_id="sub_step_2",
            name="Sub Step 2",
            step_type=StepType.EXPORT,
            parameters={"format": "json"},
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        step = WorkflowStep(
            step_id="test_parallel",
            name="Test Parallel",
            step_type=StepType.PARALLEL,
            parameters={
                "steps": [sub_step1, sub_step2]
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": "test_data"}
        
        result = workflow_service._execute_parallel_step(step, context)
        
        assert result['status'] == 'success'
        assert result['parallel_executions'] == 2
        assert len(result['results']) == 2
    
    def test_execute_delay_step(self, workflow_service):
        """Test delay step execution."""
        step = WorkflowStep(
            step_id="test_delay",
            name="Test Delay",
            step_type=StepType.DELAY,
            parameters={
                "delay_seconds": 1
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": "test_data"}
        
        start_time = time.time()
        result = workflow_service._execute_delay_step(step, context)
        end_time = time.time()
        
        assert result['status'] == 'success'
        assert result['delay_seconds'] == 1
        assert 'completed_at' in result
        assert end_time - start_time >= 1  # Should have delayed
    
    def test_execute_api_call_step(self, workflow_service):
        """Test API call step execution."""
        step = WorkflowStep(
            step_id="test_api_call",
            name="Test API Call",
            step_type=StepType.API_CALL,
            parameters={
                "endpoint": "/api/test",
                "method": "POST",
                "data": {"test": "data"}
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": "test_data"}
        
        result = workflow_service._execute_api_call_step(step, context)
        
        assert result['status'] == 'success'
        assert result['endpoint'] == "/api/test"
        assert result['method'] == "POST"
        assert 'response_code' in result
        assert 'response_time' in result
    
    def test_execute_file_operation_step(self, workflow_service):
        """Test file operation step execution."""
        step = WorkflowStep(
            step_id="test_file_op",
            name="Test File Operation",
            step_type=StepType.FILE_OPERATION,
            parameters={
                "operation": "read",
                "file_path": "test.json",
                "file_type": "json"
            },
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"data": "test_data"}
        
        result = workflow_service._execute_file_operation_step(step, context)
        
        assert result['status'] == 'success'
        assert result['operation'] == "read"
        assert result['file_path'] == "test.json"
        assert 'file_size' in result
        assert 'operation_time' in result
    
    def test_create_workflow(self, workflow_service, sample_workflow_data):
        """Test workflow creation."""
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        
        assert workflow_id == "test_workflow_001"
        assert workflow_id in workflow_service.workflows
        
        workflow = workflow_service.workflows[workflow_id]
        assert workflow.name == "Test Workflow"
        assert workflow.workflow_type == WorkflowType.VALIDATION
        assert len(workflow.steps) == 2
    
    def test_execute_workflow(self, workflow_service, sample_workflow_data):
        """Test workflow execution."""
        # Create workflow first
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        
        # Execute workflow
        context = {"floorplan_id": "test_floorplan", "data": "test_data"}
        execution_id = workflow_service.execute_workflow(workflow_id, context)
        
        assert execution_id is not None
        assert execution_id in workflow_service.executions
        
        execution = workflow_service.executions[execution_id]
        assert execution.workflow_id == workflow_id
        assert execution.status == WorkflowStatus.PENDING
        assert execution.context == context
    
    def test_get_workflow_status(self, workflow_service, sample_workflow_data):
        """Test workflow status retrieval."""
        # Create and execute workflow
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        context = {"test": "data"}
        execution_id = workflow_service.execute_workflow(workflow_id, context)
        
        # Get status
        status = workflow_service.get_workflow_status(execution_id)
        
        assert status['execution_id'] == execution_id
        assert status['workflow_id'] == workflow_id
        assert status['status'] in ['pending', 'running', 'completed', 'failed']
        assert 'start_time' in status
    
    def test_cancel_workflow(self, workflow_service, sample_workflow_data):
        """Test workflow cancellation."""
        # Create and execute workflow
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        execution_id = workflow_service.execute_workflow(workflow_id, {})
        
        # Cancel workflow
        success = workflow_service.cancel_workflow(execution_id)
        
        assert success is True
        
        # Check status
        status = workflow_service.get_workflow_status(execution_id)
        assert status['status'] == 'cancelled'
    
    def test_get_workflow_history(self, workflow_service, sample_workflow_data):
        """Test workflow history retrieval."""
        # Create workflow
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        
        # Execute multiple times
        for i in range(3):
            workflow_service.execute_workflow(workflow_id, {"iteration": i})
        
        # Get history
        history = workflow_service.get_workflow_history(workflow_id, limit=10)
        
        assert len(history) > 0
        assert all('execution_id' in execution for execution in history)
        assert all('status' in execution for execution in history)
        assert all('start_time' in execution for execution in history)
    
    def test_get_metrics(self, workflow_service, sample_workflow_data):
        """Test metrics retrieval."""
        # Create and execute some workflows
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        for i in range(3):
            workflow_service.execute_workflow(workflow_id, {"test": i})
        
        metrics = workflow_service.get_metrics()
        
        assert 'metrics' in metrics
        assert 'active_workflows' in metrics
        assert 'active_executions' in metrics
        assert 'database_size' in metrics
        assert metrics['active_workflows'] > 0
    
    def test_list_workflows(self, workflow_service, sample_workflow_data):
        """Test workflow listing."""
        # Create workflow
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        
        workflows = workflow_service.list_workflows()
        
        assert len(workflows) > 0
        workflow = next((w for w in workflows if w['workflow_id'] == workflow_id), None)
        assert workflow is not None
        assert workflow['name'] == "Test Workflow"
        assert workflow['workflow_type'] == "validation"
        assert workflow['steps_count'] == 2
    
    def test_complex_workflow_execution(self, workflow_service, complex_workflow_data):
        """Test complex workflow with multiple step types."""
        # Create complex workflow
        workflow_id = workflow_service.create_workflow(complex_workflow_data)
        
        # Execute workflow
        context = {
            "input_file": "data.json",
            "records_processed": 100,
            "status": "active"
        }
        execution_id = workflow_service.execute_workflow(workflow_id, context)
        
        # Check execution
        assert execution_id is not None
        assert execution_id in workflow_service.executions
        
        execution = workflow_service.executions[execution_id]
        assert execution.workflow_id == workflow_id
        assert execution.context == context
    
    def test_workflow_with_conditions(self, workflow_service):
        """Test workflow execution with conditional steps."""
        workflow_data = {
            "workflow_id": "conditional_workflow",
            "name": "Conditional Workflow",
            "description": "Workflow with conditional steps",
            "workflow_type": "validation",
            "steps": [
                {
                    "step_id": "check_condition",
                    "name": "Check Condition",
                    "step_type": "validation",
                    "parameters": {"service": "test"},
                    "conditions": [
                        {
                            "type": "greater_than",
                            "field": "issues_found",
                            "value": 0
                        }
                    ],
                    "timeout": 300,
                    "retry_count": 2
                },
                {
                    "step_id": "always_run",
                    "name": "Always Run",
                    "step_type": "notify",
                    "parameters": {"method": "email"},
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 2
                }
            ],
            "timeout": 900,
            "max_retries": 3
        }
        
        workflow_id = workflow_service.create_workflow(workflow_data)
        
        # Execute with condition that should be met
        context = {"issues_found": 5}
        execution_id = workflow_service.execute_workflow(workflow_id, context)
        
        assert execution_id is not None
    
    def test_workflow_error_handling(self, workflow_service):
        """Test workflow error handling and retry logic."""
        workflow_data = {
            "workflow_id": "error_test_workflow",
            "name": "Error Test Workflow",
            "description": "Workflow to test error handling",
            "workflow_type": "validation",
            "steps": [
                {
                    "step_id": "failing_step",
                    "name": "Failing Step",
                    "step_type": "validation",
                    "parameters": {"service": "invalid_service"},
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 2
                }
            ],
            "timeout": 900,
            "max_retries": 3
        }
        
        workflow_id = workflow_service.create_workflow(workflow_data)
        execution_id = workflow_service.execute_workflow(workflow_id, {})
        
        # Check that execution was created
        assert execution_id is not None
        assert execution_id in workflow_service.executions
    
    def test_performance_targets(self, workflow_service, sample_workflow_data):
        """Test that workflow execution meets performance targets."""
        import time
        
        # Create workflow
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        
        # Execute workflow and measure time
        start_time = time.time()
        execution_id = workflow_service.execute_workflow(workflow_id, {})
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance targets
        assert execution_time < 600  # Should complete within 10 minutes
        assert execution_id is not None
        
        # Check metrics
        metrics = workflow_service.get_metrics()
        assert metrics['metrics']['total_workflows'] > 0
    
    def test_concurrent_workflow_execution(self, workflow_service, sample_workflow_data):
        """Test concurrent workflow execution."""
        import threading
        import time
        
        # Create workflow
        workflow_id = workflow_service.create_workflow(sample_workflow_data)
        
        execution_ids = []
        errors = []
        
        def execute_workflow_worker(iteration):
            try:
                execution_id = workflow_service.execute_workflow(
                    workflow_id, 
                    {"iteration": iteration}
                )
                execution_ids.append(execution_id)
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent executions
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=execute_workflow_worker,
                args=(i,)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent execution errors: {errors}"
        assert len(execution_ids) == 5
        assert all(execution_id in workflow_service.executions for execution_id in execution_ids)
    
    def test_workflow_persistence(self, temp_db_path, sample_workflow_data):
        """Test that workflow data persists across service instances."""
        workflow_id = "persistence_test_workflow"
        
        # Create first service instance and create workflow
        service1 = WorkflowAutomationService(db_path=temp_db_path)
        workflow_id_created = service1.create_workflow(sample_workflow_data)
        
        # Create second service instance and check workflow exists
        service2 = WorkflowAutomationService(db_path=temp_db_path)
        workflows = service2.list_workflows()
        
        workflow = next((w for w in workflows if w['workflow_id'] == workflow_id_created), None)
        assert workflow is not None
        assert workflow['name'] == "Test Workflow"
    
    def test_edge_cases(self, workflow_service):
        """Test various edge cases."""
        # Test with empty workflow
        empty_workflow_data = {
            "workflow_id": "empty_workflow",
            "name": "Empty Workflow",
            "description": "Workflow with no steps",
            "workflow_type": "validation",
            "steps": [],
            "timeout": 900,
            "max_retries": 3
        }
        
        workflow_id = workflow_service.create_workflow(empty_workflow_data)
        execution_id = workflow_service.execute_workflow(workflow_id, {})
        
        assert execution_id is not None
        
        # Test with very large workflow ID
        large_id = "x" * 1000
        large_workflow_data = empty_workflow_data.copy()
        large_workflow_data["workflow_id"] = large_id
        
        large_workflow_id = workflow_service.create_workflow(large_workflow_data)
        assert large_workflow_id == large_id
        
        # Test with special characters in workflow ID
        special_id = "workflow-with-special-chars!@#$%^&*()"
        special_workflow_data = empty_workflow_data.copy()
        special_workflow_data["workflow_id"] = special_id
        
        special_workflow_id = workflow_service.create_workflow(special_workflow_data)
        assert special_workflow_id == special_id


class TestWorkflowStepExecution:
    """Test suite for workflow step execution functionality."""
    
    @pytest.fixture
    def workflow_service(self, temp_db_path):
        """Create a workflow automation service instance for testing."""
        return WorkflowAutomationService(db_path=temp_db_path)
    
    def test_step_execution_with_retry(self, workflow_service):
        """Test step execution with retry logic."""
        step = WorkflowStep(
            step_id="retry_test_step",
            name="Retry Test Step",
            step_type=StepType.VALIDATION,
            parameters={"service": "test_service"},
            conditions=[],
            timeout=300,
            retry_count=2
        )
        
        context = {"test": "data"}
        execution_id = "test_execution"
        
        # Mock step execution to fail first, then succeed
        original_execute = workflow_service._execute_validation_step
        
        call_count = 0
        def mock_execute(step, context):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated failure")
            return {"status": "success", "result": "success"}
        
        workflow_service._execute_validation_step = mock_execute
        
        try:
            result = workflow_service._execute_step(step, context, execution_id)
            assert result['status'] == 'success'
            assert call_count == 2  # Should have retried once
        finally:
            workflow_service._execute_validation_step = original_execute
    
    def test_step_execution_timeout(self, workflow_service):
        """Test step execution timeout handling."""
        step = WorkflowStep(
            step_id="timeout_test_step",
            name="Timeout Test Step",
            step_type=StepType.DELAY,
            parameters={"delay_seconds": 10},  # Longer than timeout
            conditions=[],
            timeout=1,  # Short timeout
            retry_count=1
        )
        
        context = {"test": "data"}
        execution_id = "test_execution"
        
        result = workflow_service._execute_step(step, context, execution_id)
        
        # Should fail due to timeout
        assert result['status'] == 'failed'
        assert 'timeout' in result['error'].lower() or 'timeout' in str(result['error']).lower()
    
    def test_conditional_step_execution(self, workflow_service):
        """Test conditional step execution."""
        step = WorkflowStep(
            step_id="conditional_step",
            name="Conditional Step",
            step_type=StepType.VALIDATION,
            parameters={"service": "test_service"},
            conditions=[
                {
                    "type": "equals",
                    "field": "status",
                    "value": "active"
                }
            ],
            timeout=300,
            retry_count=2
        )
        
        # Test with condition that should be met
        context = {"status": "active"}
        execution_id = "test_execution"
        
        result = workflow_service._execute_step(step, context, execution_id)
        assert result['status'] == 'success'
        
        # Test with condition that should not be met
        context = {"status": "inactive"}
        result = workflow_service._execute_step(step, context, execution_id)
        # Should be skipped due to condition
        assert result is None or result.get('status') == 'skipped'


class TestWorkflowPerformance:
    """Test suite for workflow performance aspects."""
    
    @pytest.fixture
    def workflow_service(self, temp_db_path):
        """Create a workflow automation service instance for testing."""
        return WorkflowAutomationService(db_path=temp_db_path)
    
    def test_workflow_execution_performance(self, workflow_service):
        """Test workflow execution performance."""
        import time
        
        # Create a simple workflow
        workflow_data = {
            "workflow_id": "perf_test_workflow",
            "name": "Performance Test Workflow",
            "description": "Workflow for performance testing",
            "workflow_type": "validation",
            "steps": [
                {
                    "step_id": "step_1",
                    "name": "Step 1",
                    "step_type": "validation",
                    "parameters": {"service": "test"},
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 1
                },
                {
                    "step_id": "step_2",
                    "name": "Step 2",
                    "step_type": "notify",
                    "parameters": {"method": "email"},
                    "conditions": [],
                    "timeout": 300,
                    "retry_count": 1
                }
            ],
            "timeout": 900,
            "max_retries": 2
        }
        
        workflow_id = workflow_service.create_workflow(workflow_data)
        
        # Execute workflow and measure performance
        start_time = time.time()
        execution_id = workflow_service.execute_workflow(workflow_id, {})
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance checks
        assert execution_time < 600  # Should complete within 10 minutes
        assert execution_id is not None
        
        # Check metrics
        metrics = workflow_service.get_metrics()
        assert metrics['metrics']['total_workflows'] > 0
        assert metrics['metrics']['successful_workflows'] > 0
    
    def test_large_workflow_execution(self, workflow_service):
        """Test execution of large workflows with many steps."""
        # Create workflow with many steps
        steps = []
        for i in range(20):  # 20 steps
            steps.append({
                "step_id": f"step_{i}",
                "name": f"Step {i}",
                "step_type": "validation",
                "parameters": {"service": "test", "step_number": i},
                "conditions": [],
                "timeout": 300,
                "retry_count": 1
            })
        
        workflow_data = {
            "workflow_id": "large_workflow",
            "name": "Large Workflow",
            "description": "Workflow with many steps",
            "workflow_type": "data_processing",
            "steps": steps,
            "timeout": 1800,
            "max_retries": 2
        }
        
        workflow_id = workflow_service.create_workflow(workflow_data)
        
        # Execute workflow
        start_time = time.time()
        execution_id = workflow_service.execute_workflow(workflow_id, {})
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance checks
        assert execution_time < 600  # Should complete within 10 minutes
        assert execution_id is not None
        
        # Check that all steps were processed
        status = workflow_service.get_workflow_status(execution_id)
        assert status['status'] in ['completed', 'running', 'pending']


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 