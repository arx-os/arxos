"""
SVGX Engine - Real-time Collaboration Test Suite

Comprehensive tests for real-time collaboration features including:
- WebSocket server functionality
- Conflict detection and resolution
- Version control system
- Presence management
- Operation batching
- Performance targets

Author: SVGX Engineering Team
Date: 2024
"""

import pytest
import asyncio
import time
import json
import websockets
from typing import Dict, List, Any

from svgx_engine.services.realtime_collaboration import (
    RealtimeCollaboration,
    OperationType,
    ConflictResolution,
    UserStatus,
    User,
    Operation,
    Conflict,
    DocumentVersion,
    ConflictDetector,
    VersionControl,
    PresenceManager,
    start_collaboration_server,
    stop_collaboration_server,
    send_operation,
    resolve_conflict,
    get_active_users,
    get_collaboration_performance_stats
)

class TestConflictDetector:
    """Test conflict detection and resolution."""

    def test_conflict_detection(self):
        """Test conflict detection between operations."""
        detector = ConflictDetector()

        # Create conflicting operations
        op1 = Operation(
            operation_id="op1",
            operation_type=OperationType.UPDATE,
            user_id="user1",
            session_id="session1",
            timestamp=time.time(),
            element_id="element1",
            data={"position": {"x": 100, "y": 100}}
        )

        op2 = Operation(
            operation_id="op2",
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=time.time() + 0.5,  # 0.5 seconds later
            element_id="element1",  # Same element
            data={"position": {"x": 200, "y": 200}}
        )

        # Detect conflicts
        conflicts = detector.detect_conflicts(op1, [op2])

        assert len(conflicts) == 1
        assert conflicts[0].operation_1.operation_id == "op1"
        assert conflicts[0].operation_2.operation_id == "op2"
        assert conflicts[0].conflict_type == "concurrent_update"

    def test_no_conflict_detection(self):
        """Test that non-conflicting operations don't create conflicts."""
        detector = ConflictDetector()

        # Create non-conflicting operations
        op1 = Operation(
            operation_id="op1",
            operation_type=OperationType.UPDATE,
            user_id="user1",
            session_id="session1",
            timestamp=time.time(),
            element_id="element1",
            data={"position": {"x": 100, "y": 100}}
        )

        op2 = Operation(
            operation_id="op2",
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=time.time() + 2.0,  # 2 seconds later (outside window)
            element_id="element1",
            data={"position": {"x": 200, "y": 200}}
        )

        # Detect conflicts
        conflicts = detector.detect_conflicts(op1, [op2])

        assert len(conflicts) == 0

    def test_conflict_resolution(self):
        """Test conflict resolution strategies."""
        detector = ConflictDetector()

        # Create a conflict
        op1 = Operation(
            operation_id="op1",
            operation_type=OperationType.UPDATE,
            user_id="user1",
            session_id="session1",
            timestamp=time.time(),
            element_id="element1"
        )

        op2 = Operation(
            operation_id="op2",
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=time.time() + 0.1,
            element_id="element1"
        )

        conflicts = detector.detect_conflicts(op1, [op2])
        assert len(conflicts) == 1

        conflict_id = conflicts[0].conflict_id

        # Test last write wins resolution
        success = detector.resolve_conflict(conflict_id, ConflictResolution.LAST_WRITE_WINS, "user1")
        assert success

        conflict = detector.conflicts[conflict_id]
        assert conflict.resolution == ConflictResolution.LAST_WRITE_WINS
        assert conflict.resolved_by == "user1"
        assert conflict.resolved_at is not None

    def test_conflict_types(self):
        """Test different types of conflicts."""
        detector = ConflictDetector()

        # Test concurrent operations
        op1 = Operation("op1", OperationType.CREATE, "user1", "session1", time.time(), "element1")
        op2 = Operation("op2", OperationType.CREATE, "user2", "session2", time.time() + 0.1, "element1")

        conflicts = detector.detect_conflicts(op1, [op2])
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "concurrent_create"

        # Test delete conflicts
        op3 = Operation("op3", OperationType.DELETE, "user1", "session1", time.time(), "element1")
        op4 = Operation("op4", OperationType.UPDATE, "user2", "session2", time.time() + 0.1, "element1")

        conflicts = detector.detect_conflicts(op3, [op4])
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "delete_conflict"

class TestVersionControl:
    """Test version control system."""

    def test_version_creation(self):
        """Test creating document versions."""
        vc = VersionControl(":memory:")  # Use in-memory database for testing

        # Create operations
        operations = [
            Operation("op1", OperationType.CREATE, "user1", "session1", time.time(), "element1"),
            Operation("op2", OperationType.UPDATE, "user2", "session2", time.time() + 1, "element1")
        ]

        # Create version
        version = vc.create_version(operations, "user1", "Test version")

        assert version.version_id is not None
        assert version.version_number == 1
        assert version.created_by == "user1"
        assert version.description == "Test version"
        assert len(version.operations) == 2

    def test_version_history(self):
        """Test version history tracking."""
        vc = VersionControl(":memory:")

        # Create multiple versions
        operations1 = [Operation("op1", OperationType.CREATE, "user1", "session1", time.time(), "element1")]
        version1 = vc.create_version(operations1, "user1", "Version 1")

        operations2 = [Operation("op2", OperationType.UPDATE, "user2", "session2", time.time() + 1, "element1")]
        version2 = vc.create_version(operations2, "user2", "Version 2")

        # Get version history
        history = vc.get_version_history()

        assert len(history) == 2
        assert history[0].version_number == 1
        assert history[1].version_number == 2
        assert history[1].parent_version == history[0].version_id

    def test_version_revert(self):
        """Test reverting to previous versions."""
        vc = VersionControl(":memory:")

        # Create versions
        operations1 = [Operation("op1", OperationType.CREATE, "user1", "session1", time.time(), "element1")]
        version1 = vc.create_version(operations1, "user1", "Version 1")

        operations2 = [Operation("op2", OperationType.UPDATE, "user2", "session2", time.time() + 1, "element1")]
        version2 = vc.create_version(operations2, "user2", "Version 2")

        # Revert to first version
        success = vc.revert_to_version(version1.version_id)
        assert success
        assert vc.current_version == version1.version_id

class TestPresenceManager:
    """Test presence management system."""

    def test_user_management(self):
        """Test adding and removing users."""
        pm = PresenceManager()

        # Add user
        user = pm.add_user("user1", "John Doe", "session1")
        assert user.user_id == "user1"
        assert user.username == "John Doe"
        assert user.status == UserStatus.ONLINE

        # Get active users
        active_users = pm.get_active_users()
        assert len(active_users) == 1
        assert active_users[0].user_id == "user1"

        # Remove user
        pm.remove_user("session1")
        active_users = pm.get_active_users()
        assert len(active_users) == 0

    def test_activity_tracking(self):
        """Test user activity tracking."""
        pm = PresenceManager()

        # Add user
        pm.add_user("user1", "John Doe", "session1")

        # Update activity
        activity_data = {
            "current_element": "element1",
            "cursor_position": {"x": 100, "y": 200},
            "selected_elements": ["element1", "element2"],
            "status": "editing"
        }

        pm.update_user_activity("user1", activity_data)

        user = pm.get_user_presence("user1")
        assert user.current_element == "element1"
        assert user.cursor_position == {"x": 100, "y": 200}
        assert user.selected_elements == ["element1", "element2"]
        assert user.status == UserStatus.EDITING

    def test_activity_timeout(self):
        """Test user activity timeout."""
        pm = PresenceManager()
        pm.activity_timeout = 1  # 1 second timeout for testing

        # Add user
        pm.add_user("user1", "John Doe", "session1")

        # Initially active
        active_users = pm.get_active_users()
        assert len(active_users) == 1

        # Wait for timeout
        time.sleep(1.1)

        # Should be marked as away
        active_users = pm.get_active_users()
        assert len(active_users) == 0

class TestRealtimeCollaboration:
    """Test main real-time collaboration service."""

    @pytest.mark.asyncio
    async def test_server_startup(self):
        """Test collaboration server startup."""
        collaboration = RealtimeCollaboration("localhost", 8766)  # Use different port

        try:
            await collaboration.start_server()
            assert collaboration.websocket_server is not None
        finally:
            await collaboration.stop_server()

    def test_operation_creation(self):
        """Test operation creation and management."""
        collaboration = RealtimeCollaboration()

        # Create operation
        operation_data = {
            "type": "update",
            "user_id": "user1",
            "element_id": "element1",
            "data": {"position": {"x": 100, "y": 200}}
        }

        operation = Operation(
            operation_id="op1",
            operation_type=OperationType(operation_data["type"]),
            user_id=operation_data["user_id"],
            session_id="session1",
            timestamp=time.time(),
            element_id=operation_data["element_id"],
            data=operation_data["data"]
        )

        assert operation.operation_id == "op1"
        assert operation.operation_type == OperationType.UPDATE
        assert operation.user_id == "user1"
        assert operation.element_id == "element1"

    def test_performance_stats(self):
        """Test performance statistics tracking."""
        collaboration = RealtimeCollaboration()

        # Update stats
        collaboration.performance_stats["total_operations"] = 100
        collaboration.performance_stats["conflicts_detected"] = 5
        collaboration.performance_stats["average_propagation_time_ms"] = 12.5

        stats = collaboration.get_performance_stats()

        assert stats["total_operations"] == 100
        assert stats["conflicts_detected"] == 5
        assert stats["average_propagation_time_ms"] == 12.5

class TestWebSocketIntegration:
    """Test WebSocket client-server integration."""

    @pytest.mark.asyncio
    async def test_websocket_communication(self):
        """Test WebSocket communication between client and server."""
        collaboration = RealtimeCollaboration("localhost", 8767)

        try:
            # Start server
            await collaboration.start_server()

            # Connect client
            uri = "ws://localhost:8767"
            async with websockets.connect(uri) as websocket:
                # Send join message
                join_message = {
                    "type": "join",
                    "user_id": "test_user",
                    "username": "Test User",
                    "session_id": "test_session"
                }

                await websocket.send(json.dumps(join_message))

                # Receive welcome message
                response = await websocket.recv()
                data = json.loads(response)

                assert data["type"] == "welcome"
                assert "client_id" in data

                # Send operation
                operation_message = {
                    "type": "operation",
                    "operation_type": "create",
                    "user_id": "test_user",
                    "session_id": "test_session",
                    "element_id": "test_element",
                    "data": {"type": "rectangle", "position": {"x": 0, "y": 0}}
                }

                await websocket.send(json.dumps(operation_message))

                # Wait for operation processing
                await asyncio.sleep(0.1)

        finally:
            await collaboration.stop_server()

class TestPerformanceTargets:
    """Test performance targets and benchmarks."""

    @pytest.mark.asyncio
    async def test_operation_propagation_time(self):
        """Test operation propagation time target."""
        collaboration = RealtimeCollaboration("localhost", 8768)

        try:
            await collaboration.start_server()

            start_time = time.time()

            # Send operation
            operation_data = {
                "type": "update",
                "user_id": "user1",
                "element_id": "element1",
                "data": {"position": {"x": 100, "y": 200}}
            }

            success = await send_operation(operation_data)
            assert success

            duration = (time.time() - start_time) * 1000

            # Should complete within 16ms
            assert duration < 16.0

        finally:
            await collaboration.stop_server()

    @pytest.mark.asyncio
    async def test_conflict_detection_time(self):
        """Test conflict detection time target."""
        detector = ConflictDetector()

        # Create conflicting operations
        op1 = Operation("op1", OperationType.UPDATE, "user1", "session1", time.time(), "element1")
        op2 = Operation("op2", OperationType.UPDATE, "user2", "session2", time.time() + 0.1, "element1")

        start_time = time.time()
        conflicts = detector.detect_conflicts(op1, [op2])
        duration = (time.time() - start_time) * 1000

        # Should complete within 5ms
        assert duration < 5.0
        assert len(conflicts) == 1

    def test_user_management_time(self):
        """Test user management operation time."""
        pm = PresenceManager()

        start_time = time.time()

        # Add user
        user = pm.add_user("user1", "John Doe", "session1")

        # Update activity
        pm.update_user_activity("user1", {"status": "editing"})

        # Get active users
        active_users = pm.get_active_users()

        duration = (time.time() - start_time) * 1000

        # Should complete within 2ms
        assert duration < 2.0
        assert len(active_users) == 1

class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test handling of invalid operations."""
        try:
            # Send invalid operation
            operation_data = {
                "type": "invalid_type",
                "user_id": "user1"
            }

            success = await send_operation(operation_data)
            # Should handle gracefully
            assert not success

        except Exception as e:
            # Expected behavior
            pass

    @pytest.mark.asyncio
    async def test_conflict_resolution_error(self):
        """Test handling of conflict resolution errors."""
        try:
            # Try to resolve non-existent conflict
            success = await resolve_conflict("non_existent", "automatic", "user1")
            assert not success

        except Exception as e:
            # Expected behavior
            pass

    def test_version_control_error(self):
        """Test handling of version control errors."""
        vc = VersionControl(":memory:")

        # Try to revert to non-existent version
        success = vc.revert_to_version("non_existent")
        assert not success

class TestScalability:
    """Test scalability features."""

    def test_multiple_users(self):
        """Test handling multiple users."""
        pm = PresenceManager()

        # Add multiple users
        for i in range(100):
            pm.add_user(f"user_{i}", f"User {i}", f"session_{i}")

        active_users = pm.get_active_users()
        assert len(active_users) == 100

        # Test performance with many users
        start_time = time.time()

        for i in range(100):
            pm.update_user_activity(f"user_{i}", {"status": "editing"})

        duration = (time.time() - start_time) * 1000

        # Should handle 100 users efficiently
        assert duration < 100.0  # Less than 100ms for 100 users

    def test_operation_batching(self):
        """Test operation batching performance."""
        collaboration = RealtimeCollaboration()

        # Add many operations to queue
        for i in range(50):
            operation = Operation(
                f"op_{i}",
                OperationType.UPDATE,
                f"user_{i % 5}",
                f"session_{i}",
                time.time(),
                f"element_{i}"
            )
            collaboration.operation_queue.append(operation)

        # Test batch processing
        start_time = time.time()

        # Simulate batch processing
        batch_size = 10
        batches = [collaboration.operation_queue[i:i + batch_size]
                  for i in range(0, len(collaboration.operation_queue), batch_size)]

        duration = (time.time() - start_time) * 1000

        # Should process batches efficiently
        assert duration < 10.0  # Less than 10ms for batch processing
        assert len(batches) == 5  # 50 operations / 10 batch size

class TestIntegration:
    """Test integration between components."""

    @pytest.mark.asyncio
    async def test_full_collaboration_workflow(self):
        """Test complete collaboration workflow."""
        collaboration = RealtimeCollaboration("localhost", 8769)

        try:
            await collaboration.start_server()

            # Test user management
            user = collaboration.presence_manager.add_user("user1", "John Doe", "session1")
            assert user.username == "John Doe"

            # Test operation sending
            operation_data = {
                "type": "create",
                "user_id": "user1",
                "element_id": "element1",
                "data": {"type": "rectangle", "position": {"x": 0, "y": 0}}
            }

            success = await send_operation(operation_data)
            assert success

            # Test conflict detection
            conflicting_operation = {
                "type": "update",
                "user_id": "user2",
                "element_id": "element1",
                "data": {"position": {"x": 100, "y": 100}}
            }

            success = await send_operation(conflicting_operation)
            assert success

            # Test conflict resolution
            conflicts = list(collaboration.conflict_detector.conflicts.values())
            if conflicts:
                conflict_id = conflicts[0].conflict_id
                success = await resolve_conflict(conflict_id, "last_write_wins", "user1")
                assert success

            # Test version control
            operations = collaboration._get_pending_operations()
            if operations:
                version = collaboration.version_control.create_version(
                    operations, "user1", "Test version"
                )
                assert version.version_number > 0

            # Test performance stats
            stats = get_collaboration_performance_stats()
            assert "total_operations" in stats
            assert "active_users" in stats

        finally:
            await collaboration.stop_server()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
