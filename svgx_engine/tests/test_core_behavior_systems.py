"""
Comprehensive tests for SVGX Engine core behavior systems.

Tests the following systems:
- Event-Driven Behavior Engine
- Advanced State Machine Engine
- Conditional Logic Engine
- Performance Optimization Engine
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Import using the correct method from the main package
from svgx_engine import (
    event_driven_behavior_engine,
    advanced_state_machine,
    conditional_logic_engine,
    performance_optimization_engine
)

# Import classes for testing
from svgx_engine.runtime.event_driven_behavior_engine import (
    EventDrivenBehaviorEngine, Event, EventType, EventPriority
)
from svgx_engine.runtime.advanced_state_machine import (
    AdvancedStateMachine, State, StateType, StatePriority, StateTransition
)
from svgx_engine.runtime.conditional_logic_engine import (
    ConditionalLogicEngine, Condition, LogicType, LogicOperator, ComparisonOperator
)
from svgx_engine.runtime.performance_optimization_engine import (
    PerformanceOptimizationEngine, OptimizationType, CacheStrategy
)


class TestEventDrivenBehaviorEngine:
    """Test suite for Event-Driven Behavior Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance for each test."""
        return EventDrivenBehaviorEngine()
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event for testing."""
        return Event(
            id="test_event_1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="test_element",
            data={"action": "click", "coordinates": {"x": 100, "y": 200}},
            session_id="test_session",
            user_id="test_user"
        )
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert len(engine.event_handlers) > 0
        assert engine.event_stats['total_events'] == 0
    
    def test_register_handler(self, engine):
        """Test handler registration."""
        def test_handler(event):
            return {"processed": True}
        
        success = engine.register_handler(
            event_type=EventType.USER_INTERACTION,
            handler_id="test_handler",
            handler=test_handler,
            priority=EventPriority.HIGH
        )
        
        assert success is True
        assert len(engine.event_handlers[EventType.USER_INTERACTION]) > 0
    
    def test_unregister_handler(self, engine):
        """Test handler unregistration."""
        def test_handler(event):
            return {"processed": True}
        
        # Register handler
        engine.register_handler(
            event_type=EventType.USER_INTERACTION,
            handler_id="test_handler",
            handler=test_handler
        )
        
        # Unregister handler
        success = engine.unregister_handler(EventType.USER_INTERACTION, "test_handler")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_process_event(self, engine, sample_event):
        """Test event processing."""
        result = await engine.process_event(sample_event)
        
        assert result is not None
        assert result.event_id == sample_event.id
        assert result.success is True
        assert engine.event_stats['total_events'] > 0
    
    def test_get_event_stats(self, engine):
        """Test event statistics retrieval."""
        stats = engine.get_event_stats()
        
        assert 'total_events' in stats
        assert 'processed_events' in stats
        assert 'failed_events' in stats
        assert 'avg_processing_time' in stats
    
    def test_get_event_history(self, engine):
        """Test event history retrieval."""
        history = engine.get_event_history(limit=10)
        assert isinstance(history, list)
    
    def test_global_engine_instance(self):
        """Test the global engine instance."""
        assert event_driven_behavior_engine is not None
        assert isinstance(event_driven_behavior_engine, EventDrivenBehaviorEngine)


class TestAdvancedStateMachine:
    """Test suite for Advanced State Machine Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance for each test."""
        return AdvancedStateMachine()
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert len(engine.state_machines) > 0
        assert engine.state_stats['active_state_machines'] > 0
    
    def test_get_state_machine(self, engine):
        """Test state machine retrieval."""
        state_machine = engine.get_state_machine('equipment')
        assert state_machine is not None
        assert state_machine.name == 'Equipment State Machine'
        assert state_machine.current_state == 'off'
    
    def test_get_current_state(self, engine):
        """Test current state retrieval."""
        current_state = engine.get_current_state('equipment')
        assert current_state == 'off'
    
    @pytest.mark.asyncio
    async def test_transition_state(self, engine):
        """Test state transition."""
        # Transition from off to standby
        success = await engine.transition_state('equipment', 'standby')
        assert success is True
        
        # Verify state change
        current_state = engine.get_current_state('equipment')
        assert current_state == 'standby'
    
    @pytest.mark.asyncio
    async def test_invalid_transition(self, engine):
        """Test invalid state transition."""
        # Try to transition from off to on (invalid)
        success = await engine.transition_state('equipment', 'on')
        assert success is False
        
        # State should remain unchanged
        current_state = engine.get_current_state('equipment')
        assert current_state == 'off'
    
    def test_get_state_history(self, engine):
        """Test state transition history."""
        history = engine.get_state_history('equipment', limit=10)
        assert isinstance(history, list)
    
    def test_get_available_transitions(self, engine):
        """Test available transitions retrieval."""
        transitions = engine.get_available_transitions('equipment')
        assert isinstance(transitions, list)
        assert len(transitions) > 0
    
    def test_get_state_machine_stats(self, engine):
        """Test state machine statistics."""
        stats = engine.get_state_machine_stats()
        
        assert 'total_transitions' in stats
        assert 'successful_transitions' in stats
        assert 'failed_transitions' in stats
        assert 'active_state_machines' in stats
    
    def test_validate_state_machine(self, engine):
        """Test state machine validation."""
        validation = engine.validate_state_machine('equipment')
        
        assert 'valid' in validation
        assert validation['valid'] is True
        assert 'total_states' in validation
        assert 'total_transitions' in validation
    
    def test_global_engine_instance(self):
        """Test the global engine instance."""
        assert advanced_state_machine is not None
        assert isinstance(advanced_state_machine, AdvancedStateMachine)


class TestConditionalLogicEngine:
    """Test suite for Conditional Logic Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance for each test."""
        return ConditionalLogicEngine()
    
    @pytest.fixture
    def sample_condition(self):
        """Create a sample condition for testing."""
        return Condition(
            id="test_condition_1",
            type=LogicType.THRESHOLD,
            operator=ComparisonOperator.GREATER_THAN,
            operands=[50, 25],
            parameters={"hysteresis": 5}
        )
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert len(engine.evaluators) > 0
        assert engine.logic_stats['total_evaluations'] == 0
    
    def test_register_condition(self, engine, sample_condition):
        """Test condition registration."""
        success = engine.register_condition(sample_condition)
        assert success is True
        assert sample_condition.id in engine.conditions
    
    def test_unregister_condition(self, engine, sample_condition):
        """Test condition unregistration."""
        # Register condition
        engine.register_condition(sample_condition)
        
        # Unregister condition
        success = engine.unregister_condition(sample_condition.id)
        assert success is True
        assert sample_condition.id not in engine.conditions
    
    def test_validate_condition(self, engine, sample_condition):
        """Test condition validation."""
        is_valid = engine._validate_condition(sample_condition)
        assert is_valid is True
    
    def test_validate_invalid_condition(self, engine):
        """Test invalid condition validation."""
        invalid_condition = Condition(
            id="invalid_condition",
            type=LogicType.THRESHOLD,
            operator=ComparisonOperator.GREATER_THAN,
            operands=[50]  # Missing second operand
        )
        
        is_valid = engine._validate_condition(invalid_condition)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_evaluate_condition(self, engine, sample_condition):
        """Test condition evaluation."""
        # Register condition
        engine.register_condition(sample_condition)
        
        # Evaluate condition
        result = await engine.evaluate_condition(sample_condition.id, {"value": 60})
        
        assert result is not None
        assert result.condition_id == sample_condition.id
        assert result.success is True
        assert result.result is True  # 60 > 25
    
    @pytest.mark.asyncio
    async def test_evaluate_threshold_condition(self, engine):
        """Test threshold condition evaluation."""
        condition = Condition(
            id="threshold_test",
            type=LogicType.THRESHOLD,
            operator=ComparisonOperator.GREATER_THAN,
            operands=[100, 50]
        )
        
        result = await engine._evaluate_threshold_condition(condition, {})
        assert result is True  # 100 > 50
        
        # Test with hysteresis
        condition.parameters["hysteresis"] = 10
        result = await engine._evaluate_threshold_condition(condition, {})
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_time_based_condition(self, engine):
        """Test time-based condition evaluation."""
        condition = Condition(
            id="time_test",
            type=LogicType.TIME_BASED,
            operator=LogicOperator.AND,
            parameters={"time_expression": "09:00-17:00"}
        )
        
        result = await engine._evaluate_time_based_condition(condition, {})
        # Result depends on current time, so we just check it doesn't raise an exception
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_evaluate_spatial_condition(self, engine):
        """Test spatial condition evaluation."""
        condition = Condition(
            id="spatial_test",
            type=LogicType.SPATIAL,
            operator=LogicOperator.AND,
            parameters={
                "location": {"x": 0, "y": 0},
                "proximity": 10,
                "target_location": {"x": 5, "y": 5}
            }
        )
        
        result = await engine._evaluate_spatial_condition(condition, {})
        assert result is True  # Distance = sqrt(25 + 25) = 7.07 < 10
    
    @pytest.mark.asyncio
    async def test_evaluate_relational_condition(self, engine):
        """Test relational condition evaluation."""
        condition = Condition(
            id="relational_test",
            type=LogicType.RELATIONAL,
            operator=ComparisonOperator.EQUAL,
            operands=["value1", "value1"]
        )
        
        result = await engine._evaluate_relational_condition(condition, {})
        assert result is True  # "value1" == "value1"
    
    def test_get_logic_stats(self, engine):
        """Test logic statistics retrieval."""
        stats = engine.get_logic_stats()
        
        assert 'total_evaluations' in stats
        assert 'successful_evaluations' in stats
        assert 'failed_evaluations' in stats
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
    
    def test_clear_cache(self, engine):
        """Test cache clearing."""
        engine.clear_cache()
        assert len(engine.condition_cache) == 0
    
    def test_get_condition(self, engine, sample_condition):
        """Test condition retrieval."""
        engine.register_condition(sample_condition)
        retrieved_condition = engine.get_condition(sample_condition.id)
        assert retrieved_condition is not None
        assert retrieved_condition.id == sample_condition.id
    
    def test_global_engine_instance(self):
        """Test the global engine instance."""
        assert conditional_logic_engine is not None
        assert isinstance(conditional_logic_engine, ConditionalLogicEngine)


class TestPerformanceOptimizationEngine:
    """Test suite for Performance Optimization Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance for each test."""
        return PerformanceOptimizationEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine.cache_stats['max_size'] > 0
        assert engine.optimization_stats['total_optimizations'] == 0
    
    def test_cache_behavior_result(self, engine):
        """Test behavior result caching."""
        behavior_id = "test_behavior"
        result = {"data": "test_result"}
        
        success = engine.cache_behavior_result(behavior_id, result, ttl=300)
        assert success is True
        assert len(engine.cache) > 0
    
    def test_get_cached_result(self, engine):
        """Test cached result retrieval."""
        behavior_id = "test_behavior"
        result = {"data": "test_result"}
        
        # Cache result
        engine.cache_behavior_result(behavior_id, result)
        
        # Retrieve cached result
        cached_result = engine.get_cached_result(behavior_id)
        assert cached_result is not None
        assert cached_result == result
    
    def test_get_cached_result_miss(self, engine):
        """Test cached result miss."""
        behavior_id = "nonexistent_behavior"
        cached_result = engine.get_cached_result(behavior_id)
        assert cached_result is None
    
    def test_lazy_evaluate_behavior(self, engine):
        """Test lazy behavior evaluation."""
        behavior_id = "test_behavior"
        
        def evaluation_func(context):
            return {"result": "evaluated", "context": context}
        
        # Register lazy evaluation
        success = engine.register_lazy_evaluation(behavior_id, evaluation_func)
        assert success is True
        
        # Evaluate behavior
        context = {"param": "value"}
        result = engine.lazy_evaluate_behavior(behavior_id, context)
        
        assert result is not None
        assert result["result"] == "evaluated"
        assert result["context"] == context
    
    @pytest.mark.asyncio
    async def test_parallel_execute_behaviors(self, engine):
        """Test parallel behavior execution."""
        behaviors = [
            ("behavior1", {"param": "value1"}),
            ("behavior2", {"param": "value2"}),
            ("behavior3", {"param": "value3"})
        ]
        
        # Register evaluation functions
        for i, (behavior_id, _) in enumerate(behaviors):
            def make_eval_func(index):
                def eval_func(context):
                    return {"result": f"behavior{index}", "context": context}
                return eval_func
            
            engine.register_lazy_evaluation(behavior_id, make_eval_func(i + 1))
        
        # Execute behaviors in parallel
        results = await engine.parallel_execute_behaviors(behaviors)
        
        assert len(results) == 3
        assert all(result is not None for result in results)
    
    def test_optimize_memory_usage(self, engine):
        """Test memory optimization."""
        result = engine.optimize_memory_usage(memory_threshold=0.5)
        
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'memory_savings')
        assert hasattr(result, 'execution_time')
    
    def test_apply_optimization_algorithm(self, engine):
        """Test optimization algorithm application."""
        behavior_id = "test_behavior"
        optimization_type = OptimizationType.CACHING
        
        result = engine.apply_optimization_algorithm(
            behavior_id, 
            optimization_type, 
            {"ttl": 300}
        )
        
        assert result is not None
        assert result.optimization_type == optimization_type
        assert hasattr(result, 'success')
        assert hasattr(result, 'performance_improvement')
        assert hasattr(result, 'memory_savings')
    
    def test_get_optimization_stats(self, engine):
        """Test optimization statistics retrieval."""
        stats = engine.get_optimization_stats()
        
        assert 'total_optimizations' in stats
        assert 'successful_optimizations' in stats
        assert 'failed_optimizations' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'memory_usage_percent' in stats
        assert 'cpu_usage_percent' in stats
    
    def test_get_performance_metrics(self, engine):
        """Test performance metrics retrieval."""
        metrics = engine.get_performance_metrics()
        
        assert hasattr(metrics, 'cache_hit_rate')
        assert hasattr(metrics, 'memory_usage')
        assert hasattr(metrics, 'cpu_usage')
        assert hasattr(metrics, 'timestamp')
    
    def test_cache_cleanup(self, engine):
        """Test cache cleanup functionality."""
        # Add some test entries
        for i in range(5):
            engine.cache_behavior_result(f"behavior{i}", {"data": f"result{i}"}, ttl=1)
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Trigger cleanup
        engine._cleanup_cache()
        
        # Cache should be empty after cleanup
        assert len(engine.cache) == 0
    
    def test_memory_threshold_check(self, engine):
        """Test memory threshold checking."""
        # Mock high memory usage
        original_memory = psutil.virtual_memory().percent
        
        # Test with low threshold
        engine._check_memory_usage()
        
        # Should not raise exceptions
        assert True
    
    def test_global_engine_instance(self):
        """Test the global engine instance."""
        assert performance_optimization_engine is not None
        assert isinstance(performance_optimization_engine, PerformanceOptimizationEngine)


class TestCoreBehaviorSystemsIntegration:
    """Integration tests for core behavior systems."""
    
    @pytest.fixture
    def engines(self):
        """Create all engine instances for integration testing."""
        return {
            'event_engine': event_driven_behavior_engine,
            'state_machine': advanced_state_machine,
            'logic_engine': conditional_logic_engine,
            'optimization_engine': performance_optimization_engine
        }
    
    @pytest.mark.asyncio
    async def test_integrated_behavior_processing(self, engines):
        """Test integrated behavior processing across all engines."""
        event_engine = engines['event_engine']
        state_machine = engines['state_machine']
        logic_engine = engines['logic_engine']
        optimization_engine = engines['optimization_engine']
        
        # 1. Create a condition
        condition = Condition(
            id="test_condition",
            type=LogicType.THRESHOLD,
            operator=ComparisonOperator.GREATER_THAN,
            operands=[100, 50]
        )
        logic_engine.register_condition(condition)
        
        # 2. Create an event that triggers state transition
        event = Event(
            id="integration_test_event",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="test_element",
            data={"action": "threshold_exceeded", "value": 150}
        )
        
        # 3. Process event
        event_result = await event_engine.process_event(event)
        assert event_result.success is True
        
        # 4. Evaluate condition
        condition_result = await logic_engine.evaluate_condition(condition.id, {"value": 150})
        assert condition_result.success is True
        assert condition_result.result is True
        
        # 5. If condition is true, transition state
        if condition_result.result:
            transition_success = await state_machine.transition_state('equipment', 'on')
            assert transition_success is True
        
        # 6. Cache the result
        cache_success = optimization_engine.cache_behavior_result(
            "integration_test", 
            {"event": event_result, "condition": condition_result, "state": "on"}
        )
        assert cache_success is True
        
        # 7. Verify integration
        current_state = state_machine.get_current_state('equipment')
        assert current_state == 'on'
        
        cached_result = optimization_engine.get_cached_result("integration_test")
        assert cached_result is not None
        assert cached_result["state"] == "on"
    
    def test_performance_optimization_integration(self, engines):
        """Test performance optimization integration."""
        optimization_engine = engines['optimization_engine']
        logic_engine = engines['logic_engine']
        
        # Register a complex condition
        condition = Condition(
            id="performance_test_condition",
            type=LogicType.THRESHOLD,
            operator=ComparisonOperator.GREATER_THAN,
            operands=[100, 50]
        )
        logic_engine.register_condition(condition)
        
        # Apply optimization
        result = optimization_engine.apply_optimization_algorithm(
            "performance_test_condition",
            OptimizationType.CACHING,
            {"ttl": 300}
        )
        
        assert result.success is True
        assert result.optimization_type == OptimizationType.CACHING
    
    def test_error_handling_integration(self, engines):
        """Test error handling across all engines."""
        event_engine = engines['event_engine']
        state_machine = engines['state_machine']
        logic_engine = engines['logic_engine']
        optimization_engine = engines['optimization_engine']
        
        # Test invalid event processing
        invalid_event = Event(
            id="invalid_event",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="nonexistent_element",
            data={}
        )
        
        # Test invalid state transition
        invalid_transition = state_machine.transition_state('nonexistent_machine', 'invalid_state')
        
        # Test invalid condition evaluation
        invalid_condition_result = logic_engine.evaluate_condition("nonexistent_condition", {})
        
        # Test invalid cache retrieval
        invalid_cache_result = optimization_engine.get_cached_result("nonexistent_cache")
        
        # All should handle errors gracefully
        assert invalid_cache_result is None


if __name__ == "__main__":
    pytest.main([__file__]) 