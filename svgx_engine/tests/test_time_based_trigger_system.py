"""
Tests for SVGX Engine Time-based Trigger System

Covers:
- TimeBasedTriggerSystem logic (create, pause, resume, cancel, delete)
- Trigger execution and monitoring
- Async operations and event integration
- Edge cases and error handling
- Follows Arxos standards: absolute imports, global instances, modular tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.time_based_trigger_system import (
    time_based_trigger_system, TimeBasedTriggerSystem, Trigger, TriggerType, TriggerStatus
)
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority

@pytest.fixture(autouse=True)
def clear_trigger_state():
    # Clear all trigger state before each test
    time_based_trigger_system.triggers.clear()
    time_based_trigger_system.execution_history.clear()
    yield
    time_based_trigger_system.triggers.clear()
    time_based_trigger_system.execution_history.clear()

@pytest.fixture(autouse=True)
async def manage_trigger_system():
    # Start the trigger system before tests
    await time_based_trigger_system.start()
    yield
    # Stop the trigger system after tests
    await time_based_trigger_system.stop()

class TestTimeBasedTriggerSystemLogic:
    def test_create_one_time_trigger(self):
        target_time = datetime.utcnow() + timedelta(seconds=10)
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="test_trigger",
            name="Test One Time Trigger",
            target_time=target_time,
            description="A test one-time trigger",
            timezone="UTC",
            metadata={"test": True}
        )
        
        assert trigger.id == "test_trigger"
        assert trigger.type == TriggerType.ONE_TIME
        assert trigger.name == "Test One Time Trigger"
        assert trigger.target_time == target_time
        assert trigger.status == TriggerStatus.ACTIVE
        assert trigger.metadata["test"] == True
        assert trigger in time_based_trigger_system.get_triggers()

    def test_create_periodic_trigger(self):
        start_time = datetime.utcnow() + timedelta(seconds=5)
        trigger = time_based_trigger_system.create_periodic_trigger(
            trigger_id="periodic_trigger",
            name="Test Periodic Trigger",
            start_time=start_time,
            interval_seconds=60.0,
            description="A test periodic trigger",
            max_executions=5
        )
        
        assert trigger.id == "periodic_trigger"
        assert trigger.type == TriggerType.PERIODIC
        assert trigger.interval_seconds == 60.0
        assert trigger.max_executions == 5
        assert trigger.status == TriggerStatus.ACTIVE

    def test_create_interval_trigger(self):
        trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="interval_trigger",
            name="Test Interval Trigger",
            interval_seconds=30.0,
            description="A test interval trigger"
        )
        
        assert trigger.id == "interval_trigger"
        assert trigger.type == TriggerType.INTERVAL
        assert trigger.interval_seconds == 30.0
        assert trigger.status == TriggerStatus.ACTIVE

    def test_create_cron_trigger(self):
        trigger = time_based_trigger_system.create_cron_trigger(
            trigger_id="cron_trigger",
            name="Test Cron Trigger",
            cron_expression="0 12 * * *",  # Daily at noon
            description="A test cron trigger"
        )
        
        assert trigger.id == "cron_trigger"
        assert trigger.type == TriggerType.CRON
        assert trigger.cron_expression == "0 12 * * *"
        assert trigger.status == TriggerStatus.ACTIVE

    def test_pause_and_resume_trigger(self):
        # Create a trigger
        trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="pause_test",
            name="Pause Test Trigger",
            interval_seconds=60.0
        )
        
        # Pause the trigger
        result = time_based_trigger_system.pause_trigger("pause_test")
        assert result == True
        assert trigger.status == TriggerStatus.PAUSED
        
        # Resume the trigger
        result = time_based_trigger_system.resume_trigger("pause_test")
        assert result == True
        assert trigger.status == TriggerStatus.ACTIVE

    def test_resume_non_paused_trigger(self):
        # Create a trigger
        time_based_trigger_system.create_interval_trigger(
            trigger_id="resume_test",
            name="Resume Test Trigger",
            interval_seconds=60.0
        )
        
        # Try to resume a non-paused trigger
        result = time_based_trigger_system.resume_trigger("resume_test")
        assert result == False

    def test_cancel_trigger(self):
        # Create a trigger
        trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="cancel_test",
            name="Cancel Test Trigger",
            interval_seconds=60.0
        )
        
        # Cancel the trigger
        result = time_based_trigger_system.cancel_trigger("cancel_test")
        assert result == True
        assert trigger.status == TriggerStatus.CANCELLED
        assert trigger.next_execution is None

    def test_delete_trigger(self):
        # Create a trigger
        time_based_trigger_system.create_interval_trigger(
            trigger_id="delete_test",
            name="Delete Test Trigger",
            interval_seconds=60.0
        )
        
        # Delete the trigger
        result = time_based_trigger_system.delete_trigger("delete_test")
        assert result == True
        assert time_based_trigger_system.get_trigger("delete_test") is None

    def test_get_trigger(self):
        # Create a trigger
        original_trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="get_test",
            name="Get Test Trigger",
            interval_seconds=60.0
        )
        
        # Get the trigger
        retrieved_trigger = time_based_trigger_system.get_trigger("get_test")
        assert retrieved_trigger is not None
        assert retrieved_trigger.id == "get_test"
        assert retrieved_trigger == original_trigger

    def test_get_triggers_with_status_filter(self):
        # Create triggers with different statuses
        trigger1 = time_based_trigger_system.create_interval_trigger(
            trigger_id="active_trigger",
            name="Active Trigger",
            interval_seconds=60.0
        )
        
        trigger2 = time_based_trigger_system.create_interval_trigger(
            trigger_id="paused_trigger",
            name="Paused Trigger",
            interval_seconds=60.0
        )
        time_based_trigger_system.pause_trigger("paused_trigger")
        
        # Get active triggers
        active_triggers = time_based_trigger_system.get_triggers(TriggerStatus.ACTIVE)
        assert len(active_triggers) == 1
        assert active_triggers[0].id == "active_trigger"
        
        # Get paused triggers
        paused_triggers = time_based_trigger_system.get_triggers(TriggerStatus.PAUSED)
        assert len(paused_triggers) == 1
        assert paused_triggers[0].id == "paused_trigger"

    def test_get_due_triggers(self):
        # Create a trigger that should be due
        past_time = datetime.utcnow() - timedelta(seconds=10)
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="due_trigger",
            name="Due Trigger",
            target_time=past_time
        )
        
        # Get due triggers
        due_triggers = time_based_trigger_system.get_due_triggers()
        assert len(due_triggers) == 1
        assert due_triggers[0].id == "due_trigger"

    def test_get_execution_history(self):
        # Create a trigger
        time_based_trigger_system.create_interval_trigger(
            trigger_id="history_test",
            name="History Test Trigger",
            interval_seconds=1.0
        )
        
        # Get execution history (should be empty initially)
        history = time_based_trigger_system.get_execution_history("history_test")
        assert len(history) == 0

    def test_clear_execution_history(self):
        # Create a trigger
        time_based_trigger_system.create_interval_trigger(
            trigger_id="clear_history_test",
            name="Clear History Test Trigger",
            interval_seconds=60.0
        )
        
        # Clear execution history
        time_based_trigger_system.clear_execution_history("clear_history_test")
        history = time_based_trigger_system.get_execution_history("clear_history_test")
        assert len(history) == 0

    def test_get_system_status(self):
        # Create some triggers
        time_based_trigger_system.create_interval_trigger(
            trigger_id="status_test1",
            name="Status Test Trigger 1",
            interval_seconds=60.0
        )
        
        time_based_trigger_system.create_interval_trigger(
            trigger_id="status_test2",
            name="Status Test Trigger 2",
            interval_seconds=60.0
        )
        
        # Pause one trigger
        time_based_trigger_system.pause_trigger("status_test2")
        
        # Get system status
        status = time_based_trigger_system.get_system_status()
        assert status["total_triggers"] == 2
        assert status["active_triggers"] == 1
        assert status["paused_triggers"] == 1
        assert status["running"] == True

    def test_trigger_with_max_executions(self):
        # Create a trigger with max executions
        trigger = time_based_trigger_system.create_periodic_trigger(
            trigger_id="max_exec_test",
            name="Max Executions Test",
            start_time=datetime.utcnow(),
            interval_seconds=1.0,
            max_executions=3
        )
        
        assert trigger.max_executions == 3
        assert trigger.current_executions == 0

    def test_trigger_timezone_handling(self):
        # Create a trigger with timezone
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="timezone_test",
            name="Timezone Test",
            target_time=datetime.utcnow() + timedelta(hours=1),
            timezone="America/New_York"
        )
        
        assert trigger.timezone == "America/New_York"

class TestTimeBasedTriggerSystemAsync:
    @pytest.mark.asyncio
    async def test_trigger_execution(self):
        # Create a trigger that should execute immediately
        past_time = datetime.utcnow() - timedelta(seconds=1)
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="async_test",
            name="Async Test Trigger",
            target_time=past_time
        )
        
        # Wait a bit for execution
        await asyncio.sleep(2)
        
        # Check execution history
        history = time_based_trigger_system.get_execution_history("async_test")
        assert len(history) >= 1
        assert history[0]["success"] == True

    @pytest.mark.asyncio
    async def test_interval_trigger_execution(self):
        # Create an interval trigger
        trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="interval_async_test",
            name="Interval Async Test",
            interval_seconds=1.0,
            max_executions=2
        )
        
        # Wait for executions
        await asyncio.sleep(3)
        
        # Check execution history
        history = time_based_trigger_system.get_execution_history("interval_async_test")
        assert len(history) >= 1
        
        # Check trigger status
        updated_trigger = time_based_trigger_system.get_trigger("interval_async_test")
        assert updated_trigger.current_executions >= 1

    @pytest.mark.asyncio
    async def test_trigger_pause_during_execution(self):
        # Create an interval trigger
        trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="pause_async_test",
            name="Pause Async Test",
            interval_seconds=1.0
        )
        
        # Wait a bit for execution
        await asyncio.sleep(1)
        
        # Pause the trigger
        time_based_trigger_system.pause_trigger("pause_async_test")
        
        # Wait more time
        await asyncio.sleep(2)
        
        # Check that trigger is paused
        updated_trigger = time_based_trigger_system.get_trigger("pause_async_test")
        assert updated_trigger.status == TriggerStatus.PAUSED

    @pytest.mark.asyncio
    async def test_system_start_stop(self):
        # Test system start/stop functionality
        await time_based_trigger_system.stop()
        assert time_based_trigger_system.running == False
        
        await time_based_trigger_system.start()
        assert time_based_trigger_system.running == True

class TestTimeBasedTriggerSystemIntegration:
    @pytest.mark.asyncio
    async def test_trigger_event_integration(self):
        # Create a trigger
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="integration_test",
            name="Integration Test",
            target_time=datetime.utcnow() - timedelta(seconds=1)
        )
        
        # Wait for execution
        await asyncio.sleep(2)
        
        # Check that trigger events are processed by the behavior engine
        # This is tested indirectly through the execution history
        history = time_based_trigger_system.get_execution_history("integration_test")
        assert len(history) >= 1
        assert history[0]["success"] == True

    def test_trigger_metadata_handling(self):
        # Create a trigger with metadata
        metadata = {"user_id": "123", "priority": "high", "category": "maintenance"}
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="metadata_test",
            name="Metadata Test",
            target_time=datetime.utcnow() + timedelta(seconds=10),
            metadata=metadata
        )
        
        assert trigger.metadata == metadata
        assert trigger.metadata["user_id"] == "123"
        assert trigger.metadata["priority"] == "high"

    def test_trigger_error_handling(self):
        # Test handling of non-existent triggers
        result = time_based_trigger_system.pause_trigger("nonexistent")
        assert result == False
        
        result = time_based_trigger_system.resume_trigger("nonexistent")
        assert result == False
        
        result = time_based_trigger_system.cancel_trigger("nonexistent")
        assert result == False
        
        result = time_based_trigger_system.delete_trigger("nonexistent")
        assert result == False

    def test_trigger_calculation_methods(self):
        # Test trigger next execution calculation
        future_time = datetime.utcnow() + timedelta(minutes=5)
        trigger = time_based_trigger_system.create_one_time_trigger(
            trigger_id="calc_test",
            name="Calculation Test",
            target_time=future_time
        )
        
        # Test that next execution is calculated correctly
        assert trigger.next_execution == future_time
        
        # Test interval trigger calculation
        interval_trigger = time_based_trigger_system.create_interval_trigger(
            trigger_id="interval_calc_test",
            name="Interval Calculation Test",
            interval_seconds=60.0
        )
        
        # Next execution should be in the future
        assert interval_trigger.next_execution > datetime.utcnow() 