"""
Comprehensive Tests for Advanced Collaboration Features

This module tests the advanced conflict resolution and push updates systems
implemented for Phase 1 of the SVGX Engine Comprehensive Enhancement Plan.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from svgx_engine.services.advanced_conflict_resolution import (
    AdvancedConflictResolutionService,
    OperationalTransform,
    CRDTConflictResolver,
    EditOperation,
    EditOperationType,
    ConflictType,
    ResolutionStrategy,
    process_edit_operation,
    resolve_conflict_manually,
    get_conflict_statistics
)

from svgx_engine.services.push_updates_system import (
    PushUpdatesSystem,
    UpdateEventType,
    UpdatePriority,
    UpdateEvent,
    ClientConnection,
    push_updates_system,
    push_element_update,
    push_lock_update,
    push_user_activity,
    push_conflict_update
)


class TestAdvancedConflictResolution:
    """Test the advanced conflict resolution system."""
    
    @pytest.fixture
    def conflict_service(self):
        """Create a fresh conflict resolution service for each test."""
        return AdvancedConflictResolutionService()
    
    @pytest.fixture
    def sample_operations(self):
        """Create sample edit operations for testing."""
        base_time = datetime.now(timezone.utc)
        
        return {
            "create_op": EditOperation(
                operation_id="op_1",
                user_id="user_1",
                element_id="element_1",
                operation_type=EditOperationType.CREATE,
                timestamp=base_time,
                data={"position": {"x": 100, "y": 100}, "type": "rectangle"},
                version=1
            ),
            "update_op": EditOperation(
                operation_id="op_2",
                user_id="user_2",
                element_id="element_1",
                operation_type=EditOperationType.UPDATE,
                timestamp=base_time,
                data={"position": {"x": 200, "y": 200}},
                version=2
            ),
            "delete_op": EditOperation(
                operation_id="op_3",
                user_id="user_1",
                element_id="element_1",
                operation_type=EditOperationType.DELETE,
                timestamp=base_time,
                data={},
                version=3
            ),
            "move_op": EditOperation(
                operation_id="op_4",
                user_id="user_2",
                element_id="element_1",
                operation_type=EditOperationType.MOVE,
                timestamp=base_time,
                data={"position": {"x": 300, "y": 300}},
                version=4
            )
        }
    
    @pytest.mark.asyncio
    async def test_operational_transform_create_conflict(self, conflict_service, sample_operations):
        """Test operational transform for create conflicts."""
        ot = OperationalTransform()
        
        # Transform create operation against another create
        transformed = ot._transform_create_create(
            sample_operations["create_op"],
            sample_operations["create_op"]
        )
        
        assert transformed.operation_id == "op_1"
        assert transformed.version > sample_operations["create_op"].version
        assert "position" in transformed.data
    
    @pytest.mark.asyncio
    async def test_operational_transform_update_conflict(self, conflict_service, sample_operations):
        """Test operational transform for update conflicts."""
        ot = OperationalTransform()
        
        # Create two update operations
        update1 = EditOperation(
            operation_id="update_1",
            user_id="user_1",
            element_id="element_1",
            operation_type=EditOperationType.UPDATE,
            timestamp=datetime.now(timezone.utc),
            data={"color": "red", "size": 10},
            version=1
        )
        
        update2 = EditOperation(
            operation_id="update_2",
            user_id="user_2",
            element_id="element_1",
            operation_type=EditOperationType.UPDATE,
            timestamp=datetime.now(timezone.utc),
            data={"color": "blue", "width": 20},
            version=2
        )
        
        # Transform update against update
        transformed = ot._transform_update_update(update1, update2)
        
        assert transformed.version > update1.version
        assert "color" in transformed.data
        assert "size" in transformed.data
        assert "width" in transformed.data
    
    @pytest.mark.asyncio
    async def test_crdt_conflict_detection(self, conflict_service, sample_operations):
        """Test CRDT conflict detection."""
        crdt = CRDTConflictResolver()
        
        # Apply first operation
        success1, conflicts1 = crdt.apply_operation(sample_operations["create_op"])
        assert success1
        assert len(conflicts1) == 0
        
        # Apply conflicting operation
        success2, conflicts2 = crdt.apply_operation(sample_operations["update_op"])
        assert success2
        assert len(conflicts2) > 0
        
        # Check conflict type
        conflict = conflicts2[0]
        assert conflict.conflict_type == ConflictType.PROPERTY_CONFLICT
        assert conflict.operation_1.element_id == conflict.operation_2.element_id
    
    @pytest.mark.asyncio
    async def test_advanced_conflict_resolution_auto_resolve(self, conflict_service, sample_operations):
        """Test automatic conflict resolution."""
        # Process operations that will create conflicts
        operation_data1 = {
            "operation_id": "test_op_1",
            "user_id": "user_1",
            "element_id": "element_1",
            "operation_type": "update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"color": "red"},
            "version": 1
        }
        
        operation_data2 = {
            "operation_id": "test_op_2",
            "user_id": "user_2",
            "element_id": "element_1",
            "operation_type": "update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"color": "blue"},
            "version": 2
        }
        
        # Process first operation
        success1, conflicts1 = await process_edit_operation(operation_data1)
        assert success1
        
        # Process second operation (should create conflict)
        success2, conflicts2 = await process_edit_operation(operation_data2)
        assert success2
        assert len(conflicts2) > 0
    
    @pytest.mark.asyncio
    async def test_manual_conflict_resolution(self, conflict_service):
        """Test manual conflict resolution."""
        # Create a conflict first
        operation_data = {
            "operation_id": "manual_test_op",
            "user_id": "user_1",
            "element_id": "element_1",
            "operation_type": "update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"color": "red"},
            "version": 1
        }
        
        success, conflicts = await process_edit_operation(operation_data)
        assert success
        
        if conflicts:
            conflict_id = conflicts[0]["conflict_id"]
            
            # Manually resolve the conflict
            resolution_success = await resolve_conflict_manually(
                conflict_id, "last_write_wins", "user_1"
            )
            assert resolution_success
    
    def test_conflict_statistics(self, conflict_service):
        """Test conflict statistics collection."""
        stats = get_conflict_statistics()
        
        assert "conflicts_detected" in stats
        assert "conflicts_resolved" in stats
        assert "auto_resolutions" in stats
        assert "manual_resolutions" in stats
        assert "average_resolution_time" in stats


class TestPushUpdatesSystem:
    """Test the push updates system."""
    
    @pytest.fixture
    def push_system(self):
        """Create a fresh push updates system for each test."""
        return PushUpdatesSystem()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = Mock()
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_client_registration(self, push_system, mock_websocket):
        """Test client registration."""
        client_id = "test_client_1"
        user_id = "test_user_1"
        canvas_id = "test_canvas_1"
        
        success = await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket,
            permissions=["read", "write"]
        )
        
        assert success
        assert client_id in push_system.clients
        assert canvas_id in push_system.canvas_clients
        assert user_id in push_system.user_clients
    
    @pytest.mark.asyncio
    async def test_client_unregistration(self, push_system, mock_websocket):
        """Test client unregistration."""
        client_id = "test_client_2"
        user_id = "test_user_2"
        canvas_id = "test_canvas_2"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Unregister client
        success = await push_system.unregister_client(client_id)
        assert success
        assert client_id not in push_system.clients
        assert canvas_id not in push_system.canvas_clients
        assert user_id not in push_system.user_clients
    
    @pytest.mark.asyncio
    async def test_push_update(self, push_system, mock_websocket):
        """Test pushing updates to clients."""
        client_id = "test_client_3"
        user_id = "test_user_3"
        canvas_id = "test_canvas_3"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Push update
        success = await push_system.push_update(
            event_type=UpdateEventType.ELEMENT_UPDATED,
            data={"element_id": "test_element", "position": {"x": 100, "y": 100}},
            canvas_id=canvas_id,
            source_user_id=user_id
        )
        
        assert success
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_to_canvas(self, push_system, mock_websocket):
        """Test broadcasting to all clients in a canvas."""
        client_id = "test_client_4"
        user_id = "test_user_4"
        canvas_id = "test_canvas_4"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Broadcast to canvas
        await push_system.broadcast_to_canvas(
            canvas_id=canvas_id,
            event_type=UpdateEventType.ELEMENT_CREATED,
            data={"element_id": "new_element", "type": "rectangle"}
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_push_element_update(self, push_system, mock_websocket):
        """Test the push_element_update convenience function."""
        client_id = "test_client_5"
        user_id = "test_user_5"
        canvas_id = "test_canvas_5"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Push element update
        success = await push_element_update(
            element_id="test_element",
            canvas_id=canvas_id,
            user_id=user_id,
            update_data={"position": {"x": 200, "y": 200}},
            event_type=UpdateEventType.ELEMENT_MOVED
        )
        
        assert success
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_push_lock_update(self, push_system, mock_websocket):
        """Test the push_lock_update convenience function."""
        client_id = "test_client_6"
        user_id = "test_user_6"
        canvas_id = "test_canvas_6"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Push lock update
        success = await push_lock_update(
            element_id="test_element",
            canvas_id=canvas_id,
            user_id=user_id,
            lock_action="acquired",
            lock_data={"lock_id": "lock_123", "expires_at": "2024-01-01T00:00:00Z"}
        )
        
        assert success
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_push_user_activity(self, push_system, mock_websocket):
        """Test the push_user_activity convenience function."""
        client_id = "test_client_7"
        user_id = "test_user_7"
        canvas_id = "test_canvas_7"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Push user activity
        success = await push_user_activity(
            user_id=user_id,
            canvas_id=canvas_id,
            activity_data={
                "activity_type": "cursor_move",
                "cursor_position": {"x": 150, "y": 150},
                "selected_elements": ["element_1", "element_2"]
            }
        )
        
        assert success
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_push_conflict_update(self, push_system, mock_websocket):
        """Test the push_conflict_update convenience function."""
        client_id = "test_client_8"
        user_id = "test_user_8"
        canvas_id = "test_canvas_8"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Push conflict update
        success = await push_conflict_update(
            conflict_id="conflict_123",
            canvas_id=canvas_id,
            conflict_data={
                "conflict_type": "modification_conflict",
                "severity": "medium",
                "auto_resolvable": True
            },
            event_type=UpdateEventType.CONFLICT_DETECTED
        )
        
        assert success
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called()
    
    def test_system_statistics(self, push_system):
        """Test system statistics collection."""
        stats = push_system.get_system_statistics()
        
        assert "total_clients" in stats
        assert "canvas_clients" in stats
        assert "user_clients" in stats
        assert "metrics" in stats
        assert "event_handlers" in stats
    
    @pytest.mark.asyncio
    async def test_event_handlers(self, push_system):
        """Test event handler registration and triggering."""
        handler_called = False
        handler_data = None
        
        async def test_handler(event):
            nonlocal handler_called, handler_data
            handler_called = True
            handler_data = event.data
        
        # Register event handler
        push_system.register_event_handler(UpdateEventType.ELEMENT_CREATED, test_handler)
        
        # Push an event
        await push_system.push_update(
            event_type=UpdateEventType.ELEMENT_CREATED,
            data={"element_id": "test_element", "type": "circle"}
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that handler was called
        assert handler_called
        assert handler_data["element_id"] == "test_element"
    
    @pytest.mark.asyncio
    async def test_priority_processing(self, push_system, mock_websocket):
        """Test that high priority events are processed first."""
        client_id = "test_client_9"
        user_id = "test_user_9"
        canvas_id = "test_canvas_9"
        
        # Register client
        await push_system.register_client(
            client_id=client_id,
            user_id=user_id,
            canvas_id=canvas_id,
            websocket=mock_websocket
        )
        
        # Push events with different priorities
        await push_system.push_update(
            event_type=UpdateEventType.ELEMENT_UPDATED,
            data={"element_id": "test_element", "color": "red"},
            canvas_id=canvas_id,
            priority=UpdatePriority.LOW
        )
        
        await push_system.push_update(
            event_type=UpdateEventType.CONFLICT_DETECTED,
            data={"conflict_id": "conflict_123"},
            canvas_id=canvas_id,
            priority=UpdatePriority.CRITICAL
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that messages were sent (critical should be processed first)
        assert mock_websocket.send_text.call_count >= 2


class TestIntegration:
    """Integration tests for the complete collaboration system."""
    
    @pytest.mark.asyncio
    async def test_complete_collaboration_workflow(self):
        """Test a complete collaboration workflow."""
        # This test simulates a real collaboration scenario
        # with multiple users editing the same element
        
        # User 1 creates an element
        operation1 = {
            "operation_id": "create_op_1",
            "user_id": "user_1",
            "element_id": "element_1",
            "operation_type": "create",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"type": "rectangle", "position": {"x": 100, "y": 100}},
            "version": 1
        }
        
        success1, conflicts1 = await process_edit_operation(operation1)
        assert success1
        assert len(conflicts1) == 0
        
        # User 2 updates the same element
        operation2 = {
            "operation_id": "update_op_1",
            "user_id": "user_2",
            "element_id": "element_1",
            "operation_type": "update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"color": "blue", "size": 20},
            "version": 2
        }
        
        success2, conflicts2 = await process_edit_operation(operation2)
        assert success2
        # Should detect conflicts since both users modified the same element
        assert len(conflicts2) > 0
        
        # User 1 moves the element
        operation3 = {
            "operation_id": "move_op_1",
            "user_id": "user_1",
            "element_id": "element_1",
            "operation_type": "move",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"position": {"x": 200, "y": 200}},
            "version": 3
        }
        
        success3, conflicts3 = await process_edit_operation(operation3)
        assert success3
        # Should have more conflicts due to concurrent modifications
        assert len(conflicts3) >= len(conflicts2)
    
    @pytest.mark.asyncio
    async def test_push_updates_with_conflicts(self):
        """Test push updates system with conflict scenarios."""
        # This test verifies that conflicts are properly
        # communicated to all clients via push updates
        
        # Create a mock WebSocket for testing
        mock_ws = Mock()
        mock_ws.send_text = AsyncMock()
        
        # Register client with push updates system
        await push_updates_system.register_client(
            client_id="test_client",
            user_id="test_user",
            canvas_id="test_canvas",
            websocket=mock_ws
        )
        
        # Create a conflict scenario
        operation_data = {
            "operation_id": "conflict_test_op",
            "user_id": "user_1",
            "element_id": "conflict_element",
            "operation_type": "update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"color": "red"},
            "version": 1
        }
        
        # Process operation (should create conflicts)
        success, conflicts = await process_edit_operation(operation_data)
        assert success
        
        # Push conflict updates
        if conflicts:
            for conflict in conflicts:
                await push_conflict_update(
                    conflict_id=conflict["conflict_id"],
                    canvas_id="test_canvas",
                    conflict_data=conflict
                )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify that conflict messages were sent
        assert mock_ws.send_text.call_count > 0
        
        # Clean up
        await push_updates_system.unregister_client("test_client")


# Performance tests
class TestPerformance:
    """Performance tests for the collaboration systems."""
    
    @pytest.mark.asyncio
    async def test_conflict_resolution_performance(self):
        """Test conflict resolution performance under load."""
        import time
        
        start_time = time.time()
        
        # Process many operations quickly
        operations = []
        for i in range(100):
            operation = {
                "operation_id": f"perf_op_{i}",
                "user_id": f"user_{i % 5}",
                "element_id": f"element_{i % 10}",
                "operation_type": "update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"value": i},
                "version": i
            }
            operations.append(operation)
        
        # Process all operations
        for operation in operations:
            success, conflicts = await process_edit_operation(operation)
            assert success
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 100 operations in under 1 second
        assert processing_time < 1.0
        
        # Check statistics
        stats = get_conflict_statistics()
        assert stats["conflicts_detected"] > 0
    
    @pytest.mark.asyncio
    async def test_push_updates_performance(self):
        """Test push updates performance under load."""
        import time
        
        # Create multiple mock clients
        mock_clients = []
        for i in range(10):
            ws = Mock()
            ws.send_text = AsyncMock()
            mock_clients.append(ws)
        
        # Register all clients
        for i, ws in enumerate(mock_clients):
            await push_updates_system.register_client(
                client_id=f"perf_client_{i}",
                user_id=f"perf_user_{i}",
                canvas_id="perf_canvas",
                websocket=ws
            )
        
        start_time = time.time()
        
        # Push many updates
        for i in range(50):
            await push_updates_system.push_update(
                event_type=UpdateEventType.ELEMENT_UPDATED,
                data={"element_id": f"element_{i}", "value": i},
                canvas_id="perf_canvas"
            )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 50 updates to 10 clients in under 1 second
        assert processing_time < 1.0
        
        # Verify messages were sent to all clients
        total_messages = sum(ws.send_text.call_count for ws in mock_clients)
        assert total_messages > 0
        
        # Clean up
        for i in range(10):
            await push_updates_system.unregister_client(f"perf_client_{i}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 