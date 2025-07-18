"""
Test suite for SVGX Logic Engine Integration.

This module tests the integration of the logic engine with the runtime,
covering rule creation, execution, and performance monitoring.
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from runtime import SVGXRuntime
from logic_engine import LogicEngine, RuleType, RuleStatus


class TestLogicEngineIntegration:
    """Test suite for Logic Engine Integration."""
    
    @pytest.fixture
    def runtime(self):
        """Create a runtime instance for testing."""
        return SVGXRuntime()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return {
            'temperature': 25.5,
            'pressure': 101.3,
            'status': 'active',
            'position': {'x': 10, 'y': 20, 'z': 0},
            'timestamp': datetime.now().isoformat()
        }
    
    @pytest.fixture
    def sample_conditions(self):
        """Create sample rule conditions."""
        return [
            {
                'field': 'temperature',
                'operator': '>',
                'value': 30.0
            },
            {
                'field': 'status',
                'operator': '==',
                'value': 'active'
            }
        ]
    
    @pytest.fixture
    def sample_actions(self):
        """Create sample rule actions."""
        return [
            {
                'action_type': 'set_field',
                'field': 'alert_level',
                'value': 'high'
            },
            {
                'action_type': 'log',
                'message': 'Temperature threshold exceeded',
                'level': 'warning'
            }
        ]
    
    def test_logic_engine_initialization(self, runtime):
        """Test that logic engine is properly initialized."""
        assert runtime.logic_engine is not None
        assert isinstance(runtime.logic_engine, LogicEngine)
    
    def test_create_logic_rule(self, runtime, sample_conditions, sample_actions):
        """Test creating a logic rule."""
        rule_id = runtime.create_logic_rule(
            name="Temperature Alert Rule",
            description="Alert when temperature exceeds threshold",
            rule_type="conditional",
            conditions=sample_conditions,
            actions=sample_actions,
            priority=1,
            tags=["temperature", "alert"]
        )
        
        assert rule_id is not None
        assert isinstance(rule_id, str)
        assert len(rule_id) > 0
    
    def test_execute_logic_rules(self, runtime, sample_data):
        """Test executing logic rules."""
        # First create a rule
        conditions = [
            {
                'field': 'temperature',
                'operator': '>',
                'value': 20.0
            }
        ]
        
        actions = [
            {
                'action_type': 'set_field',
                'field': 'processed',
                'value': True
            }
        ]
        
        rule_id = runtime.create_logic_rule(
            name="Test Rule",
            description="Test rule for execution",
            rule_type="conditional",
            conditions=conditions,
            actions=actions
        )
        
        # Execute the rule
        results = runtime.execute_logic_rules(
            element_id="test_element",
            data=sample_data,
            rule_ids=[rule_id]
        )
        
        assert len(results) > 0
        assert results[0].status.value == "success"
    
    def test_execute_logic_rules_all(self, runtime, sample_data):
        """Test executing all available logic rules."""
        # Create multiple rules
        for i in range(3):
            conditions = [
                {
                    'field': 'temperature',
                    'operator': '>',
                    'value': 20.0 + i
                }
            ]
            
            actions = [
                {
                    'action_type': 'set_field',
                    'field': f'rule_{i}_executed',
                    'value': True
                }
            ]
            
            runtime.create_logic_rule(
                name=f"Test Rule {i}",
                description=f"Test rule {i}",
                rule_type="conditional",
                conditions=conditions,
                actions=actions
            )
        
        # Execute all rules
        results = runtime.execute_logic_rules(
            element_id="test_element",
            data=sample_data
        )
        
        assert len(results) >= 3
    
    def test_logic_engine_stats(self, runtime):
        """Test getting logic engine statistics."""
        stats = runtime.get_logic_engine_stats()
        
        assert "status" in stats
        assert stats["status"] != "error"
        
        if stats["status"] != "not_available":
            assert "total_executions" in stats
            assert "successful_executions" in stats
            assert "failed_executions" in stats
            assert "average_execution_time" in stats
    
    def test_logic_rule_creation_with_different_types(self, runtime):
        """Test creating rules with different types."""
        rule_types = ["conditional", "transformation", "validation", "workflow", "analysis"]
        
        for rule_type in rule_types:
            rule_id = runtime.create_logic_rule(
                name=f"Test {rule_type} rule",
                description=f"Test {rule_type} rule",
                rule_type=rule_type,
                conditions=[{"field": "test", "operator": "==", "value": "test"}],
                actions=[{"action_type": "set_field", "field": "test", "value": True}]
            )
            
            assert rule_id is not None
    
    def test_logic_rule_creation_with_priority(self, runtime):
        """Test creating rules with different priorities."""
        priorities = [1, 5, 10]
        
        for priority in priorities:
            rule_id = runtime.create_logic_rule(
                name=f"Priority {priority} rule",
                description=f"Test rule with priority {priority}",
                rule_type="conditional",
                conditions=[{"field": "test", "operator": "==", "value": "test"}],
                actions=[{"action_type": "set_field", "field": "test", "value": True}],
                priority=priority
            )
            
            assert rule_id is not None
    
    def test_logic_rule_creation_with_tags(self, runtime):
        """Test creating rules with tags."""
        tags = ["temperature", "alert", "critical"]
        
        rule_id = runtime.create_logic_rule(
            name="Tagged rule",
            description="Test rule with tags",
            rule_type="conditional",
            conditions=[{"field": "test", "operator": "==", "value": "test"}],
            actions=[{"action_type": "set_field", "field": "test", "value": True}],
            tags=tags
        )
        
        assert rule_id is not None
    
    def test_logic_engine_error_handling(self, runtime):
        """Test error handling in logic engine operations."""
        # Test with invalid rule type
        rule_id = runtime.create_logic_rule(
            name="Invalid rule",
            description="Test invalid rule",
            rule_type="invalid_type",
            conditions=[],
            actions=[]
        )
        
        # Should handle gracefully
        assert rule_id is not None
    
    def test_logic_engine_performance(self, runtime, sample_data):
        """Test logic engine performance with multiple rules."""
        import time
        
        # Create multiple rules
        rule_ids = []
        for i in range(10):
            rule_id = runtime.create_logic_rule(
                name=f"Performance Rule {i}",
                description=f"Performance test rule {i}",
                rule_type="conditional",
                conditions=[{"field": "temperature", "operator": ">", "value": 20.0}],
                actions=[{"action_type": "set_field", "field": f"rule_{i}", "value": True}]
            )
            rule_ids.append(rule_id)
        
        # Execute rules and measure performance
        start_time = time.time()
        results = runtime.execute_logic_rules(
            element_id="test_element",
            data=sample_data,
            rule_ids=rule_ids
        )
        execution_time = time.time() - start_time
        
        assert len(results) == 10
        assert execution_time < 1.0  # Should complete within 1 second
    
    def test_logic_engine_integration_with_advanced_behavior(self, runtime):
        """Test integration between logic engine and advanced behavior engine."""
        # Create a logic rule
        rule_id = runtime.create_logic_rule(
            name="Integration Test Rule",
            description="Test integration with advanced behavior",
            rule_type="conditional",
            conditions=[{"field": "status", "operator": "==", "value": "active"}],
            actions=[{"action_type": "set_field", "field": "integrated", "value": True}]
        )
        
        # Register advanced behavior
        behavior_config = {
            'rules': [
                {
                    'rule_id': 'advanced_rule_1',
                    'rule_type': 'safety',
                    'conditions': [
                        {
                            'type': 'simple',
                            'variable': 'temperature',
                            'operator': '>',
                            'value': 30.0
                        }
                    ],
                    'actions': [
                        {
                            'type': 'update',
                            'target_property': 'alert_level',
                            'value': 'high'
                        }
                    ],
                    'priority': 1
                }
            ]
        }
        
        runtime.register_advanced_behavior("test_element", behavior_config)
        
        # Both engines should work together
        assert rule_id is not None
        status = runtime.get_advanced_behavior_status()
        assert status['registered_rules'] > 0
    
    def test_logic_engine_lifecycle(self, runtime):
        """Test logic engine lifecycle operations."""
        # Create a rule
        rule_id = runtime.create_logic_rule(
            name="Lifecycle Test Rule",
            description="Test rule for lifecycle operations",
            rule_type="conditional",
            conditions=[{"field": "test", "operator": "==", "value": "test"}],
            actions=[{"action_type": "set_field", "field": "test", "value": True}]
        )
        
        # Get rule details
        rule = runtime.logic_engine.get_rule(rule_id)
        assert rule is not None
        assert rule.name == "Lifecycle Test Rule"
        
        # List all rules
        rules = runtime.logic_engine.list_rules()
        assert len(rules) > 0
        
        # Delete rule
        success = runtime.logic_engine.delete_rule(rule_id)
        assert success is True
        
        # Verify rule is deleted
        deleted_rule = runtime.logic_engine.get_rule(rule_id)
        assert deleted_rule is None
    
    def test_logic_engine_with_complex_data(self, runtime):
        """Test logic engine with complex data structures."""
        complex_data = {
            'nested': {
                'temperature': 25.5,
                'pressure': 101.3
            },
            'array': [1, 2, 3, 4, 5],
            'status': 'active',
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'user': 'test_user'
            }
        }
        
        # Create rule that works with complex data
        rule_id = runtime.create_logic_rule(
            name="Complex Data Rule",
            description="Test rule with complex data",
            rule_type="conditional",
            conditions=[
                {
                    'field': 'nested.temperature',
                    'operator': '>',
                    'value': 20.0
                },
                {
                    'field': 'status',
                    'operator': '==',
                    'value': 'active'
                }
            ],
            actions=[
                {
                    'action_type': 'set_field',
                    'field': 'processed',
                    'value': True
                }
            ]
        )
        
        # Execute rule
        results = runtime.execute_logic_rules(
            element_id="test_element",
            data=complex_data,
            rule_ids=[rule_id]
        )
        
        assert len(results) > 0
        assert results[0].status.value == "success"
    
    def test_logic_engine_concurrent_execution(self, runtime):
        """Test concurrent execution of logic rules."""
        import threading
        import time
        
        # Create multiple rules
        rule_ids = []
        for i in range(5):
            rule_id = runtime.create_logic_rule(
                name=f"Concurrent Rule {i}",
                description=f"Concurrent test rule {i}",
                rule_type="conditional",
                conditions=[{"field": "test", "operator": "==", "value": "test"}],
                actions=[{"action_type": "set_field", "field": f"concurrent_{i}", "value": True}]
            )
            rule_ids.append(rule_id)
        
        # Execute rules concurrently
        results = []
        threads = []
        
        def execute_rules():
            thread_results = runtime.execute_logic_rules(
                element_id="test_element",
                data={"test": "test"},
                rule_ids=rule_ids
            )
            results.extend(thread_results)
        
        # Start multiple threads
        for _ in range(3):
            thread = threading.Thread(target=execute_rules)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have executed rules multiple times
        assert len(results) >= 5
    
    def test_logic_engine_error_recovery(self, runtime):
        """Test logic engine error recovery."""
        # Create a rule that might cause errors
        rule_id = runtime.create_logic_rule(
            name="Error Recovery Rule",
            description="Test error recovery",
            rule_type="conditional",
            conditions=[{"field": "nonexistent", "operator": "==", "value": "test"}],
            actions=[{"action_type": "invalid_action", "field": "test", "value": True}]
        )
        
        # Execute rule - should handle errors gracefully
        results = runtime.execute_logic_rules(
            element_id="test_element",
            data={"test": "test"},
            rule_ids=[rule_id]
        )
        
        # Should not crash and should return results
        assert isinstance(results, list)
    
    def test_logic_engine_memory_usage(self, runtime):
        """Test logic engine memory usage with many rules."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many rules
        rule_ids = []
        for i in range(100):
            rule_id = runtime.create_logic_rule(
                name=f"Memory Test Rule {i}",
                description=f"Memory test rule {i}",
                rule_type="conditional",
                conditions=[{"field": "test", "operator": "==", "value": "test"}],
                actions=[{"action_type": "set_field", "field": f"memory_{i}", "value": True}]
            )
            rule_ids.append(rule_id)
        
        # Execute all rules
        results = runtime.execute_logic_rules(
            element_id="test_element",
            data={"test": "test"},
            rule_ids=rule_ids
        )
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB
        assert len(results) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 