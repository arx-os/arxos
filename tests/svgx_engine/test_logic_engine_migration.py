"""
Test Logic Engine Service Migration

This test suite verifies that the Logic Engine service has been successfully
migrated to the SVGX Engine with all functionality intact.
"""

import pytest
import tempfile
import os
from datetime import datetime
from typing import Dict, Any

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


class TestLogicEngineMigration:
    """Test suite for Logic Engine service migration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def logic_engine(self, temp_db):
        """Create a Logic Engine instance for testing."""
        return LogicEngine(db_path=temp_db)
    
    def test_logic_engine_initialization(self, logic_engine):
        """Test that the Logic Engine initializes correctly."""
        assert logic_engine is not None
        assert hasattr(logic_engine, 'rules')
        assert hasattr(logic_engine, 'rule_chains')
        assert hasattr(logic_engine, 'builtin_functions')
        assert hasattr(logic_engine, 'executor')
        
        # Check that built-in functions are loaded
        assert len(logic_engine.builtin_functions) > 50
        assert 'len' in logic_engine.builtin_functions
        assert 'str' in logic_engine.builtin_functions
        assert 'sum' in logic_engine.builtin_functions
        assert 'upper' in logic_engine.builtin_functions
        assert 'lower' in logic_engine.builtin_functions
        assert 'math_add' in logic_engine.builtin_functions
        assert 'uuid_generate' in logic_engine.builtin_functions
    
    def test_rule_creation(self, logic_engine):
        """Test creating a new rule."""
        conditions = [
            {
                "field": "user.age",
                "operator": ">=",
                "value": 18
            }
        ]
        
        actions = [
            {
                "type": "set_field",
                "field": "user.status",
                "value": "adult"
            }
        ]
        
        rule_id = logic_engine.create_rule(
            name="Age Check Rule",
            description="Check if user is adult",
            rule_type=RuleType.VALIDATION,
            conditions=conditions,
            actions=actions,
            priority=1,
            tags=["validation", "age"]
        )
        
        assert rule_id is not None
        assert len(rule_id) > 0
        
        # Verify rule was created
        rule = logic_engine.get_rule(rule_id)
        assert rule is not None
        assert rule.name == "Age Check Rule"
        assert rule.rule_type == RuleType.VALIDATION
        assert rule.status == RuleStatus.ACTIVE
    
    def test_rule_execution(self, logic_engine):
        """Test executing a rule."""
        # Create a simple rule
        conditions = [
            {
                "field": "data.value",
                "operator": ">",
                "value": 10
            }
        ]
        
        actions = [
            {
                "type": "set_field",
                "field": "data.result",
                "value": "high"
            }
        ]
        
        rule_id = logic_engine.create_rule(
            name="Value Check Rule",
            description="Check if value is high",
            rule_type=RuleType.CONDITIONAL,
            conditions=conditions,
            actions=actions
        )
        
        # Test execution with condition met
        test_data = {"data": {"value": 15}}
        execution = logic_engine.execute_rule(rule_id, test_data)
        
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["data"]["result"] == "high"
        assert execution.execution_time > 0
        
        # Test execution with condition not met
        test_data = {"data": {"value": 5}}
        execution = logic_engine.execute_rule(rule_id, test_data)
        
        assert execution.status == ExecutionStatus.SUCCESS
        assert "result" not in execution.output_data["data"]
    
    def test_rule_chain_creation(self, logic_engine):
        """Test creating a rule chain."""
        # Create multiple rules
        rule_ids = []
        
        for i in range(3):
            rule_id = logic_engine.create_rule(
                name=f"Test Rule {i}",
                description=f"Test rule {i}",
                rule_type=RuleType.TRANSFORMATION,
                conditions=[{"field": "data.step", "operator": "==", "value": i}],
                actions=[{"type": "set_field", "field": f"data.result_{i}", "value": f"processed_{i}"}]
            )
            rule_ids.append(rule_id)
        
        # Create rule chain
        chain_id = logic_engine.create_rule_chain(
            name="Test Chain",
            description="Test rule chain",
            rules=rule_ids,
            execution_order="sequential"
        )
        
        assert chain_id is not None
        assert len(chain_id) > 0
    
    def test_rule_chain_execution(self, logic_engine):
        """Test executing a rule chain."""
        # Create rules for chain
        rule_ids = []
        
        for i in range(2):
            rule_id = logic_engine.create_rule(
                name=f"Chain Rule {i}",
                description=f"Chain rule {i}",
                rule_type=RuleType.TRANSFORMATION,
                conditions=[{"field": "data.ready", "operator": "==", "value": True}],
                actions=[{"type": "set_field", "field": f"data.step_{i}", "value": f"completed_{i}"}]
            )
            rule_ids.append(rule_id)
        
        # Create and execute chain
        chain_id = logic_engine.create_rule_chain(
            name="Test Chain",
            description="Test rule chain",
            rules=rule_ids,
            execution_order="sequential"
        )
        
        test_data = {"data": {"ready": True}}
        executions = logic_engine.execute_rule_chain(chain_id, test_data)
        
        assert len(executions) == 2
        assert all(execution.status == ExecutionStatus.SUCCESS for execution in executions)
        assert executions[0].output_data["data"]["step_0"] == "completed_0"
        assert executions[1].output_data["data"]["step_1"] == "completed_1"
    
    def test_builtin_functions(self, logic_engine):
        """Test built-in functions work correctly."""
        context = DataContext(
            data={"test": "Hello World"},
            variables={},
            functions=logic_engine.builtin_functions,
            metadata={}
        )
        
        # Test string functions
        assert logic_engine.builtin_functions['upper']("hello") == "HELLO"
        assert logic_engine.builtin_functions['lower']("WORLD") == "world"
        assert logic_engine.builtin_functions['contains']("hello world", "world") == True
        
        # Test math functions
        assert logic_engine.builtin_functions['math_add'](5, 3) == 8.0
        assert logic_engine.builtin_functions['math_multiply'](4, 6) == 24.0
        
        # Test array functions
        test_array = [1, 2, 3, 4, 5]
        assert logic_engine.builtin_functions['array_length'](test_array) == 5
        assert logic_engine.builtin_functions['array_contains'](test_array, 3) == True
        
        # Test object functions
        test_obj = {"a": 1, "b": 2}
        assert logic_engine.builtin_functions['has_key'](test_obj, "a") == True
        assert logic_engine.builtin_functions['get_value'](test_obj, "b") == 2
    
    def test_complex_condition_evaluation(self, logic_engine):
        """Test complex condition evaluation."""
        conditions = [
            {
                "field": "user.age",
                "operator": ">=",
                "value": 18
            },
            {
                "field": "user.status",
                "operator": "==",
                "value": "active"
            }
        ]
        
        actions = [
            {
                "type": "set_field",
                "field": "user.can_access",
                "value": True
            }
        ]
        
        rule_id = logic_engine.create_rule(
            name="Complex Access Rule",
            description="Check user access rights",
            rule_type=RuleType.VALIDATION,
            conditions=conditions,
            actions=actions
        )
        
        # Test with valid data
        test_data = {
            "user": {
                "age": 25,
                "status": "active"
            }
        }
        
        execution = logic_engine.execute_rule(rule_id, test_data)
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["user"]["can_access"] == True
        
        # Test with invalid data
        test_data = {
            "user": {
                "age": 16,
                "status": "active"
            }
        }
        
        execution = logic_engine.execute_rule(rule_id, test_data)
        assert execution.status == ExecutionStatus.SUCCESS
        assert "can_access" not in execution.output_data["user"]
    
    def test_field_path_evaluation(self, logic_engine):
        """Test field path evaluation with nested objects."""
        conditions = [
            {
                "field": "data.user.profile.email",
                "operator": "contains",
                "value": "@"
            }
        ]
        
        actions = [
            {
                "type": "set_field",
                "field": "data.user.profile.verified",
                "value": True
            }
        ]
        
        rule_id = logic_engine.create_rule(
            name="Email Validation Rule",
            description="Validate email format",
            rule_type=RuleType.VALIDATION,
            conditions=conditions,
            actions=actions
        )
        
        test_data = {
            "data": {
                "user": {
                    "profile": {
                        "email": "test@example.com"
                    }
                }
            }
        }
        
        execution = logic_engine.execute_rule(rule_id, test_data)
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.output_data["data"]["user"]["profile"]["verified"] == True
    
    def test_performance_metrics(self, logic_engine):
        """Test performance metrics collection."""
        # Create and execute a rule
        rule_id = logic_engine.create_rule(
            name="Performance Test Rule",
            description="Test performance metrics",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "==", "value": True}],
            actions=[{"type": "set_field", "field": "result", "value": "success"}]
        )
        
        # Execute rule multiple times
        for _ in range(5):
            logic_engine.execute_rule(rule_id, {"test": True})
        
        # Check performance metrics
        metrics = logic_engine.get_performance_metrics()
        assert metrics["total_executions"] >= 5
        assert metrics["successful_executions"] >= 5
        assert metrics["average_execution_time"] > 0
        
        # Check rule statistics
        stats = logic_engine.get_rule_statistics(rule_id)
        assert stats["execution_count"] >= 5
        assert stats["success_count"] >= 5
        assert stats["avg_execution_time"] > 0
    
    def test_error_handling(self, logic_engine):
        """Test error handling in rule execution."""
        # Create a rule with invalid field reference
        rule_id = logic_engine.create_rule(
            name="Error Test Rule",
            description="Test error handling",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "nonexistent.field", "operator": "==", "value": True}],
            actions=[{"type": "set_field", "field": "result", "value": "success"}]
        )
        
        # Execute rule - should handle error gracefully
        execution = logic_engine.execute_rule(rule_id, {"test": True})
        assert execution.status == ExecutionStatus.SUCCESS  # Conditions not met, not an error
        assert "result" not in execution.output_data
    
    def test_rule_management(self, logic_engine):
        """Test rule management operations."""
        # Create a rule
        rule_id = logic_engine.create_rule(
            name="Management Test Rule",
            description="Test rule management",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "==", "value": True}],
            actions=[{"type": "set_field", "field": "result", "value": "success"}]
        )
        
        # List rules
        rules = logic_engine.list_rules()
        assert len(rules) >= 1
        assert any(rule.rule_id == rule_id for rule in rules)
        
        # Update rule
        success = logic_engine.update_rule(rule_id, {"name": "Updated Rule Name"})
        assert success == True
        
        updated_rule = logic_engine.get_rule(rule_id)
        assert updated_rule.name == "Updated Rule Name"
        
        # Delete rule
        success = logic_engine.delete_rule(rule_id)
        assert success == True
        
        deleted_rule = logic_engine.get_rule(rule_id)
        assert deleted_rule is None
    
    def test_shutdown(self, logic_engine):
        """Test graceful shutdown."""
        # Create some rules
        rule_id = logic_engine.create_rule(
            name="Shutdown Test Rule",
            description="Test shutdown",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "test", "operator": "==", "value": True}],
            actions=[{"type": "set_field", "field": "result", "value": "success"}]
        )
        
        # Shutdown engine
        logic_engine.shutdown()
        
        # Verify shutdown completed
        assert logic_engine.executor._shutdown == True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 