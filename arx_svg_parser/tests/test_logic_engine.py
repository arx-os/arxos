"""
Comprehensive Test Suite for Logic Engine Service

This test suite covers all aspects of the logic engine functionality including:
- Rule creation, management, and validation
- Rule execution and condition evaluation
- Rule chains and complex workflows
- Performance monitoring and statistics
- Error handling and recovery
- Built-in functions and operators
- Data transformation and validation
- Concurrent execution and stress testing

Performance Targets:
- Rule evaluation completes within 100ms for simple rules
- Complex rule chains complete within 500ms
- Support for 1000+ concurrent rule evaluations
- 99.9%+ rule execution accuracy
- Comprehensive rule validation and error handling
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
import os
import random

from services.logic_engine import (
    LogicEngine,
    Rule,
    RuleChain,
    RuleExecution,
    RuleType,
    RuleStatus,
    ExecutionStatus,
    DataContext
)


class TestLogicEngine:
    """Test suite for the LogicEngine."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.fixture
    def logic_engine(self, temp_db):
        """Create a logic engine instance for testing."""
        return LogicEngine(db_path=temp_db)
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return {
            "user": {
                "id": 123,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "age": 30,
                "active": True,
                "roles": ["user", "admin"],
                "profile": {
                    "bio": "Software developer",
                    "location": "New York"
                }
            },
            "order": {
                "id": "ORD-001",
                "amount": 150.50,
                "currency": "USD",
                "items": [
                    {"name": "Product 1", "price": 50.00, "quantity": 2},
                    {"name": "Product 2", "price": 50.50, "quantity": 1}
                ],
                "status": "pending"
            },
            "settings": {
                "notifications": True,
                "theme": "dark",
                "language": "en"
            }
        }
    
    def test_engine_initialization(self, logic_engine):
        """Test engine initialization and setup."""
        assert logic_engine is not None
        assert logic_engine.rules == {}
        assert logic_engine.rule_chains == {}
        assert logic_engine.total_executions == 0
        assert logic_engine.successful_executions == 0
        assert logic_engine.failed_executions == 0
        assert logic_engine.average_execution_time == 0.0
        assert len(logic_engine.builtin_functions) > 0
    
    def test_builtin_functions(self, logic_engine):
        """Test built-in functions availability."""
        functions = logic_engine.builtin_functions
        
        # Test string functions
        assert 'length' in functions
        assert 'lower' in functions
        assert 'upper' in functions
        assert 'trim' in functions
        assert 'contains' in functions
        
        # Test number functions
        assert 'abs' in functions
        assert 'round' in functions
        assert 'min' in functions
        assert 'max' in functions
        assert 'sum' in functions
        
        # Test array functions
        assert 'size' in functions
        assert 'isEmpty' in functions
        assert 'first' in functions
        assert 'last' in functions
        
        # Test logic functions
        assert 'if' in functions
        assert 'and' in functions
        assert 'or' in functions
        assert 'not' in functions
    
    def test_rule_creation(self, logic_engine):
        """Test rule creation functionality."""
        # Create a simple conditional rule
        rule_id = logic_engine.create_rule(
            name="Test User Validation",
            description="Validate user data",
            rule_type=RuleType.VALIDATION,
            conditions=[
                {
                    "field": "user.age",
                    "operator": "greater_than",
                    "value": 18
                },
                {
                    "field": "user.email",
                    "operator": "contains",
                    "value": "@"
                }
            ],
            actions=[
                {
                    "type": "set_field",
                    "field": "user.validated",
                    "value": True
                }
            ],
            priority=1,
            tags=["validation", "user"]
        )
        
        assert rule_id is not None
        
        # Verify rule was created
        rule = logic_engine.get_rule(rule_id)
        assert rule is not None
        assert rule.name == "Test User Validation"
        assert rule.rule_type == RuleType.VALIDATION
        assert rule.status == RuleStatus.ACTIVE
        assert len(rule.conditions) == 2
        assert len(rule.actions) == 1
        assert rule.priority == 1
        assert "validation" in rule.tags
        assert "user" in rule.tags
    
    def test_rule_validation(self, logic_engine):
        """Test rule validation."""
        # Test rule with missing name
        with pytest.raises(ValueError, match="Rule name is required"):
            logic_engine.create_rule(
                name="",
                description="Test",
                rule_type=RuleType.CONDITIONAL,
                conditions=[],
                actions=[]
            )
        
        # Test rule with no conditions
        with pytest.raises(ValueError, match="Rule must have at least one condition"):
            logic_engine.create_rule(
                name="Test Rule",
                description="Test",
                rule_type=RuleType.CONDITIONAL,
                conditions=[],
                actions=[{"type": "set_field", "field": "test", "value": "test"}]
            )
        
        # Test rule with no actions
        with pytest.raises(ValueError, match="Rule must have at least one action"):
            logic_engine.create_rule(
                name="Test Rule",
                description="Test",
                rule_type=RuleType.CONDITIONAL,
                conditions=[{"field": "test", "operator": "equals", "value": "test"}],
                actions=[]
            )
        
        # Test rule with invalid condition
        with pytest.raises(ValueError, match="Condition must have 'field'"):
            logic_engine.create_rule(
                name="Test Rule",
                description="Test",
                rule_type=RuleType.CONDITIONAL,
                conditions=[{"operator": "equals", "value": "test"}],
                actions=[{"type": "set_field", "field": "test", "value": "test"}]
            )
    
    def test_rule_execution(self, logic_engine, sample_data):
        """Test rule execution."""
        # Create a test rule
        rule_id = logic_engine.create_rule(
            name="Age Validation",
            description="Validate user age",
            rule_type=RuleType.VALIDATION,
            conditions=[
                {
                    "field": "user.age",
                    "operator": "greater_than",
                    "value": 18
                }
            ],
            actions=[
                {
                    "type": "set_field",
                    "field": "user.adult",
                    "value": True
                }
            ]
        )
        
        # Execute rule with valid data
        execution = logic_engine.execute_rule(rule_id, sample_data)
        
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.rule_id == rule_id
        assert execution.input_data == sample_data
        assert execution.output_data["user"]["adult"] is True
        assert execution.execution_time > 0
        assert execution.error_message is None
    
    def test_condition_evaluation(self, logic_engine):
        """Test condition evaluation with various operators."""
        context = DataContext(
            data={
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "active": True,
                "roles": ["user", "admin"],
                "score": 85.5
            },
            variables={},
            functions=logic_engine.builtin_functions,
            metadata={}
        )
        
        # Test equals operator
        condition = {"field": "name", "operator": "equals", "value": "John Doe"}
        assert logic_engine._evaluate_condition("John Doe", "equals", "John Doe") is True
        assert logic_engine._evaluate_condition("John Doe", "equals", "Jane Doe") is False
        
        # Test greater_than operator
        assert logic_engine._evaluate_condition(30, "greater_than", 18) is True
        assert logic_engine._evaluate_condition(30, "greater_than", 50) is False
        
        # Test contains operator
        assert logic_engine._evaluate_condition("john@example.com", "contains", "@") is True
        assert logic_engine._evaluate_condition("john@example.com", "contains", "gmail") is False
        
        # Test starts_with operator
        assert logic_engine._evaluate_condition("John Doe", "starts_with", "John") is True
        assert logic_engine._evaluate_condition("John Doe", "starts_with", "Jane") is False
        
        # Test is_empty operator
        assert logic_engine._evaluate_condition("", "is_empty", None) is True
        assert logic_engine._evaluate_condition("John", "is_empty", None) is False
        assert logic_engine._evaluate_condition([], "is_empty", None) is True
        assert logic_engine._evaluate_condition([1, 2, 3], "is_empty", None) is False
    
    def test_action_execution(self, logic_engine):
        """Test action execution."""
        data = {"user": {"name": "John", "age": 30}}
        
        # Test set_field action
        actions = [
            {
                "type": "set_field",
                "field": "user.validated",
                "value": True
            }
        ]
        
        context = DataContext(
            data=data,
            variables={},
            functions=logic_engine.builtin_functions,
            metadata={}
        )
        
        result = logic_engine._execute_actions(actions, context)
        assert result["user"]["validated"] is True
        
        # Test remove_field action
        actions = [
            {
                "type": "remove_field",
                "field": "user.age"
            }
        ]
        
        result = logic_engine._execute_actions(actions, context)
        assert "age" not in result["user"]
        
        # Test transform_field action
        actions = [
            {
                "type": "transform_field",
                "field": "user.name",
                "transformation": {
                    "type": "uppercase"
                }
            }
        ]
        
        result = logic_engine._execute_actions(actions, context)
        assert result["user"]["name"] == "JOHN"
    
    def test_field_value_access(self, logic_engine):
        """Test field value access using dot notation."""
        data = {
            "user": {
                "name": "John Doe",
                "profile": {
                    "age": 30,
                    "location": "New York"
                }
            },
            "items": [
                {"name": "Item 1", "price": 10.00},
                {"name": "Item 2", "price": 20.00}
            ]
        }
        
        context = DataContext(
            data=data,
            variables={},
            functions=logic_engine.builtin_functions,
            metadata={}
        )
        
        # Test simple field access
        value = logic_engine._get_field_value("user.name", context)
        assert value == "John Doe"
        
        # Test nested field access
        value = logic_engine._get_field_value("user.profile.age", context)
        assert value == 30
        
        # Test array access
        value = logic_engine._get_field_value("items[0].name", context)
        assert value == "Item 1"
        
        # Test non-existent field
        value = logic_engine._get_field_value("user.nonexistent", context)
        assert value is None
    
    def test_rule_chains(self, logic_engine, sample_data):
        """Test rule chain creation and execution."""
        # Create multiple rules
        rule1_id = logic_engine.create_rule(
            name="Validate User",
            description="Validate user data",
            rule_type=RuleType.VALIDATION,
            conditions=[
                {"field": "user.age", "operator": "greater_than", "value": 18}
            ],
            actions=[
                {"type": "set_field", "field": "user.validated", "value": True}
            ]
        )
        
        rule2_id = logic_engine.create_rule(
            name="Calculate Total",
            description="Calculate order total",
            rule_type=RuleType.TRANSFORMATION,
            conditions=[
                {"field": "order.items", "operator": "is_not_empty", "value": None}
            ],
            actions=[
                {
                    "type": "call_function",
                    "function": "sum",
                    "params": ["order.items[].price"],
                    "result_field": "order.total"
                }
            ]
        )
        
        # Create rule chain
        chain_id = logic_engine.create_rule_chain(
            name="Order Processing",
            description="Process order validation and calculation",
            rules=[rule1_id, rule2_id],
            execution_order="sequential"
        )
        
        # Execute rule chain
        executions = logic_engine.execute_rule_chain(chain_id, sample_data)
        
        assert len(executions) == 2
        assert all(e.status == ExecutionStatus.SUCCESS for e in executions)
        assert executions[0].rule_id == rule1_id
        assert executions[1].rule_id == rule2_id
    
    def test_rule_listing_and_filtering(self, logic_engine):
        """Test rule listing with various filters."""
        # Create rules of different types
        validation_rule = logic_engine.create_rule(
            name="Validation Rule",
            description="Test validation rule",
            rule_type=RuleType.VALIDATION,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}],
            tags=["validation"]
        )
        
        transformation_rule = logic_engine.create_rule(
            name="Transformation Rule",
            description="Test transformation rule",
            rule_type=RuleType.TRANSFORMATION,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}],
            tags=["transformation"]
        )
        
        # Test listing all rules
        all_rules = logic_engine.list_rules()
        assert len(all_rules) >= 2
        
        # Test filtering by type
        validation_rules = logic_engine.list_rules(rule_type=RuleType.VALIDATION)
        assert len(validation_rules) >= 1
        assert all(r.rule_type == RuleType.VALIDATION for r in validation_rules)
        
        # Test filtering by tags
        validation_rules = logic_engine.list_rules(tags=["validation"])
        assert len(validation_rules) >= 1
        assert any("validation" in r.tags for r in validation_rules)
    
    def test_rule_updates(self, logic_engine):
        """Test rule updates."""
        # Create a rule
        rule_id = logic_engine.create_rule(
            name="Original Name",
            description="Original description",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        # Update the rule
        updates = {
            "name": "Updated Name",
            "description": "Updated description",
            "priority": 5
        }
        
        success = logic_engine.update_rule(rule_id, updates)
        assert success is True
        
        # Verify updates
        rule = logic_engine.get_rule(rule_id)
        assert rule.name == "Updated Name"
        assert rule.description == "Updated description"
        assert rule.priority == 5
    
    def test_rule_deletion(self, logic_engine):
        """Test rule deletion."""
        # Create a rule
        rule_id = logic_engine.create_rule(
            name="Test Rule",
            description="Test description",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        # Verify rule exists
        assert logic_engine.get_rule(rule_id) is not None
        
        # Delete the rule
        success = logic_engine.delete_rule(rule_id)
        assert success is True
        
        # Verify rule is deleted
        assert logic_engine.get_rule(rule_id) is None
    
    def test_performance_metrics(self, logic_engine, sample_data):
        """Test performance metrics collection."""
        # Create and execute a rule
        rule_id = logic_engine.create_rule(
            name="Performance Test Rule",
            description="Test performance metrics",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "user.age", "operator": "greater_than", "value": 18}],
            actions=[{"type": "set_field", "field": "user.validated", "value": True}]
        )
        
        # Execute rule multiple times
        for _ in range(5):
            logic_engine.execute_rule(rule_id, sample_data)
        
        # Get performance metrics
        metrics = logic_engine.get_performance_metrics()
        
        assert metrics['total_executions'] >= 5
        assert metrics['successful_executions'] >= 5
        assert metrics['success_rate'] >= 95.0
        assert metrics['average_execution_time'] > 0
        assert metrics['total_rules'] >= 1
        assert metrics['active_rules'] >= 1
    
    def test_rule_statistics(self, logic_engine, sample_data):
        """Test rule statistics."""
        # Create and execute a rule
        rule_id = logic_engine.create_rule(
            name="Statistics Test Rule",
            description="Test rule statistics",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "user.age", "operator": "greater_than", "value": 18}],
            actions=[{"type": "set_field", "field": "user.validated", "value": True}]
        )
        
        # Execute rule
        logic_engine.execute_rule(rule_id, sample_data)
        
        # Get rule statistics
        stats = logic_engine.get_rule_statistics(rule_id)
        
        assert stats['rule_id'] == rule_id
        assert stats['name'] == "Statistics Test Rule"
        assert stats['execution_count'] >= 1
        assert stats['success_count'] >= 1
        assert stats['success_rate'] >= 95.0
        assert stats['average_execution_time'] > 0
    
    def test_error_handling(self, logic_engine):
        """Test error handling in rule execution."""
        # Test execution of non-existent rule
        with pytest.raises(ValueError, match="Rule.*not found"):
            logic_engine.execute_rule("nonexistent_rule", {})
        
        # Test execution of inactive rule
        rule_id = logic_engine.create_rule(
            name="Inactive Rule",
            description="Test inactive rule",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        # Deactivate the rule
        logic_engine.update_rule(rule_id, {"status": RuleStatus.INACTIVE})
        
        with pytest.raises(ValueError, match="Rule.*is not active"):
            logic_engine.execute_rule(rule_id, {})
    
    def test_complex_conditions(self, logic_engine, sample_data):
        """Test complex condition evaluation."""
        # Create rule with multiple conditions
        rule_id = logic_engine.create_rule(
            name="Complex Validation",
            description="Test complex conditions",
            rule_type=RuleType.VALIDATION,
            conditions=[
                {"field": "user.age", "operator": "greater_than", "value": 18},
                {"field": "user.email", "operator": "contains", "value": "@"},
                {"field": "user.active", "operator": "equals", "value": True}
            ],
            actions=[
                {"type": "set_field", "field": "user.validated", "value": True}
            ]
        )
        
        # Execute with valid data
        execution = logic_engine.execute_rule(rule_id, sample_data)
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["user"]["validated"] is True
        
        # Execute with invalid data
        invalid_data = sample_data.copy()
        invalid_data["user"]["age"] = 16
        
        execution = logic_engine.execute_rule(rule_id, invalid_data)
        assert execution.status == ExecutionStatus.SUCCESS  # Conditions not met is not an error
        assert "validated" not in execution.output_data["user"]
    
    def test_data_transformation(self, logic_engine):
        """Test data transformation actions."""
        data = {
            "user": {
                "name": "john doe",
                "email": "JOHN@EXAMPLE.COM",
                "bio": "  software developer  "
            }
        }
        
        # Create transformation rule
        rule_id = logic_engine.create_rule(
            name="Data Transformation",
            description="Transform user data",
            rule_type=RuleType.TRANSFORMATION,
            conditions=[{"field": "user.name", "operator": "is_not_empty", "value": None}],
            actions=[
                {
                    "type": "transform_field",
                    "field": "user.name",
                    "transformation": {"type": "uppercase"}
                },
                {
                    "type": "transform_field",
                    "field": "user.email",
                    "transformation": {"type": "lowercase"}
                },
                {
                    "type": "transform_field",
                    "field": "user.bio",
                    "transformation": {"type": "trim"}
                }
            ]
        )
        
        execution = logic_engine.execute_rule(rule_id, data)
        
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["user"]["name"] == "JOHN DOE"
        assert execution.output_data["user"]["email"] == "john@example.com"
        assert execution.output_data["user"]["bio"] == "software developer"
    
    def test_function_calls(self, logic_engine):
        """Test function calls in actions."""
        data = {
            "numbers": [1, 2, 3, 4, 5],
            "text": "hello world"
        }
        
        # Create rule with function calls
        rule_id = logic_engine.create_rule(
            name="Function Test",
            description="Test function calls",
            rule_type=RuleType.TRANSFORMATION,
            conditions=[{"field": "numbers", "operator": "is_not_empty", "value": None}],
            actions=[
                {
                    "type": "call_function",
                    "function": "sum",
                    "params": ["numbers"],
                    "result_field": "total"
                },
                {
                    "type": "call_function",
                    "function": "upper",
                    "params": ["text"],
                    "result_field": "uppercase_text"
                }
            ]
        )
        
        execution = logic_engine.execute_rule(rule_id, data)
        
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["total"] == 15
        assert execution.output_data["uppercase_text"] == "HELLO WORLD"
    
    def test_concurrent_execution(self, logic_engine, sample_data):
        """Test concurrent rule execution."""
        import threading
        import time
        
        # Create multiple rules
        rule_ids = []
        for i in range(5):
            rule_id = logic_engine.create_rule(
                name=f"Concurrent Rule {i}",
                description=f"Test concurrent rule {i}",
                rule_type=RuleType.CONDITIONAL,
                conditions=[{"field": "user.age", "operator": "greater_than", "value": 18}],
                actions=[{"type": "set_field", "field": f"result_{i}", "value": True}]
            )
            rule_ids.append(rule_id)
        
        results = []
        errors = []
        
        def execute_rule_worker(rule_id):
            try:
                execution = logic_engine.execute_rule(rule_id, sample_data)
                results.append(execution)
            except Exception as e:
                errors.append(e)
        
        # Execute rules concurrently
        threads = []
        for rule_id in rule_ids:
            thread = threading.Thread(target=execute_rule_worker, args=(rule_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent execution failed: {errors}"
        assert len(results) == 5
        assert all(r.status == ExecutionStatus.SUCCESS for r in results)
    
    def test_performance_targets(self, logic_engine, sample_data):
        """Test that engine meets performance targets."""
        # Create a simple rule
        rule_id = logic_engine.create_rule(
            name="Performance Test",
            description="Test performance targets",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "user.age", "operator": "greater_than", "value": 18}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        # Test execution time for simple rule
        start_time = time.time()
        execution = logic_engine.execute_rule(rule_id, sample_data)
        execution_time = time.time() - start_time
        
        # Should complete within 100ms for simple rules
        assert execution_time < 0.1, f"Simple rule execution took {execution_time}s, should be < 0.1s"
        
        # Test complex rule chain
        rule_ids = []
        for i in range(10):
            rule_id = logic_engine.create_rule(
                name=f"Chain Rule {i}",
                description=f"Test chain rule {i}",
                rule_type=RuleType.CONDITIONAL,
                conditions=[{"field": "user.age", "operator": "greater_than", "value": 18}],
                actions=[{"type": "set_field", "field": f"result_{i}", "value": True}]
            )
            rule_ids.append(rule_id)
        
        # Create rule chain
        chain_id = logic_engine.create_rule_chain(
            name="Performance Chain",
            description="Test performance chain",
            rules=rule_ids,
            execution_order="sequential"
        )
        
        # Test chain execution time
        start_time = time.time()
        executions = logic_engine.execute_rule_chain(chain_id, sample_data)
        chain_time = time.time() - start_time
        
        # Should complete within 500ms for complex rule chains
        assert chain_time < 0.5, f"Complex rule chain took {chain_time}s, should be < 0.5s"
        
        # Test accuracy
        success_rate = (len([e for e in executions if e.status == ExecutionStatus.SUCCESS]) / len(executions)) * 100
        assert success_rate >= 99.9, f"Success rate {success_rate}% is below 99.9% target"
    
    def test_edge_cases(self, logic_engine):
        """Test various edge cases."""
        # Test with empty data
        rule_id = logic_engine.create_rule(
            name="Empty Data Test",
            description="Test with empty data",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "is_empty", "value": None}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        execution = logic_engine.execute_rule(rule_id, {})
        assert execution.status == ExecutionStatus.SUCCESS
        
        # Test with null values
        data_with_nulls = {
            "null_field": None,
            "empty_string": "",
            "empty_array": [],
            "empty_object": {}
        }
        
        rule_id = logic_engine.create_rule(
            name="Null Values Test",
            description="Test with null values",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "null_field", "operator": "is_null", "value": None}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        execution = logic_engine.execute_rule(rule_id, data_with_nulls)
        assert execution.status == ExecutionStatus.SUCCESS
        
        # Test with very large data
        large_data = {
            "large_array": list(range(10000)),
            "large_string": "x" * 10000,
            "nested_data": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": "deep_value"
                            }
                        }
                    }
                }
            }
        }
        
        rule_id = logic_engine.create_rule(
            name="Large Data Test",
            description="Test with large data",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "nested_data.level1.level2.level3.level4.level5", "operator": "equals", "value": "deep_value"}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        execution = logic_engine.execute_rule(rule_id, large_data)
        assert execution.status == ExecutionStatus.SUCCESS


class TestLogicEngineIntegration:
    """Integration tests for logic engine functionality."""
    
    @pytest.fixture
    def logic_engine(self):
        """Create a logic engine for integration testing."""
        return LogicEngine()
    
    def test_full_rule_lifecycle(self, logic_engine):
        """Test complete rule lifecycle."""
        # 1. Create rule
        rule_id = logic_engine.create_rule(
            name="Lifecycle Test Rule",
            description="Test complete rule lifecycle",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        # 2. Verify rule exists
        rule = logic_engine.get_rule(rule_id)
        assert rule is not None
        assert rule.name == "Lifecycle Test Rule"
        
        # 3. Execute rule
        data = {"test": "test"}
        execution = logic_engine.execute_rule(rule_id, data)
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["result"] is True
        
        # 4. Update rule
        updates = {
            "name": "Updated Lifecycle Test Rule",
            "priority": 5
        }
        success = logic_engine.update_rule(rule_id, updates)
        assert success is True
        
        # 5. Verify update
        updated_rule = logic_engine.get_rule(rule_id)
        assert updated_rule.name == "Updated Lifecycle Test Rule"
        assert updated_rule.priority == 5
        
        # 6. Delete rule
        success = logic_engine.delete_rule(rule_id)
        assert success is True
        
        # 7. Verify deletion
        assert logic_engine.get_rule(rule_id) is None
    
    def test_complex_workflow(self, logic_engine):
        """Test complex workflow with multiple rules and chains."""
        # Create user validation rule
        validation_rule = logic_engine.create_rule(
            name="User Validation",
            description="Validate user data",
            rule_type=RuleType.VALIDATION,
            conditions=[
                {"field": "user.age", "operator": "greater_than", "value": 18},
                {"field": "user.email", "operator": "contains", "value": "@"}
            ],
            actions=[
                {"type": "set_field", "field": "user.validated", "value": True}
            ]
        )
        
        # Create data transformation rule
        transform_rule = logic_engine.create_rule(
            name="Data Transformation",
            description="Transform user data",
            rule_type=RuleType.TRANSFORMATION,
            conditions=[
                {"field": "user.validated", "operator": "equals", "value": True}
            ],
            actions=[
                {
                    "type": "transform_field",
                    "field": "user.name",
                    "transformation": {"type": "uppercase"}
                },
                {
                    "type": "transform_field",
                    "field": "user.email",
                    "transformation": {"type": "lowercase"}
                }
            ]
        )
        
        # Create calculation rule
        calculation_rule = logic_engine.create_rule(
            name="Order Calculation",
            description="Calculate order totals",
            rule_type=RuleType.TRANSFORMATION,
            conditions=[
                {"field": "order.items", "operator": "is_not_empty", "value": None}
            ],
            actions=[
                {
                    "type": "call_function",
                    "function": "sum",
                    "params": ["order.items[].price"],
                    "result_field": "order.total"
                }
            ]
        )
        
        # Create rule chain
        chain_id = logic_engine.create_rule_chain(
            name="Order Processing Workflow",
            description="Complete order processing workflow",
            rules=[validation_rule, transform_rule, calculation_rule],
            execution_order="sequential"
        )
        
        # Test workflow with valid data
        test_data = {
            "user": {
                "name": "john doe",
                "email": "JOHN@EXAMPLE.COM",
                "age": 25
            },
            "order": {
                "items": [
                    {"name": "Product 1", "price": 10.00},
                    {"name": "Product 2", "price": 20.00}
                ]
            }
        }
        
        executions = logic_engine.execute_rule_chain(chain_id, test_data)
        
        assert len(executions) == 3
        assert all(e.status == ExecutionStatus.SUCCESS for e in executions)
        
        # Check final result
        final_data = executions[-1].output_data
        assert final_data["user"]["validated"] is True
        assert final_data["user"]["name"] == "JOHN DOE"
        assert final_data["user"]["email"] == "john@example.com"
        assert final_data["order"]["total"] == 30.0
    
    def test_error_recovery(self, logic_engine):
        """Test error recovery and handling."""
        # Create rule that might fail
        rule_id = logic_engine.create_rule(
            name="Error Test Rule",
            description="Test error handling",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "nonexistent", "operator": "equals", "value": "test"}],
            actions=[{"type": "set_field", "field": "result", "value": True}]
        )
        
        # Execute rule - should handle gracefully
        execution = logic_engine.execute_rule(rule_id, {})
        
        # Should not crash, but may have error status
        assert execution is not None
        assert hasattr(execution, 'status')
        assert hasattr(execution, 'error_message')
    
    def test_performance_under_load(self, logic_engine):
        """Test performance under load."""
        import threading
        import time
        
        # Create multiple rules
        rule_ids = []
        for i in range(20):
            rule_id = logic_engine.create_rule(
                name=f"Load Test Rule {i}",
                description=f"Test rule for load testing {i}",
                rule_type=RuleType.CONDITIONAL,
                conditions=[{"field": "test", "operator": "equals", "value": "test"}],
                actions=[{"type": "set_field", "field": f"result_{i}", "value": True}]
            )
            rule_ids.append(rule_id)
        
        # Test concurrent execution
        results = []
        errors = []
        
        def worker(rule_id):
            try:
                for _ in range(10):  # Execute each rule 10 times
                    execution = logic_engine.execute_rule(rule_id, {"test": "test"})
                    results.append(execution)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for rule_id in rule_ids:
            thread = threading.Thread(target=worker, args=(rule_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Load test failed with errors: {errors}"
        assert len(results) == 200  # 20 rules * 10 executions each
        
        # Check performance metrics
        metrics = logic_engine.get_performance_metrics()
        assert metrics['total_executions'] >= 200
        assert metrics['success_rate'] >= 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 