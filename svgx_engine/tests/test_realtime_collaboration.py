"""
SVGX Engine - Real-time Collaboration Service Tests

Comprehensive test suite for the real-time collaboration service, covering:
- Security and authentication
- Conflict detection and resolution
- Version control operations
- Performance monitoring
- WebSocket communication
- Error handling and recovery
- Multi-user scenarios
- Rate limiting and validation

Author: SVGX Engineering Team
Date: 2024
"""

import pytest
import asyncio
import json
import time
import uuid
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import websockets
import threading
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.realtime_collaboration import (
    RealtimeCollaboration,
    OperationType,
    ConflictResolution,
    UserStatus,
    User,
    Operation,
    Conflict,
    DocumentVersion,
    SecurityManager,
    ConflictDetector,
    VersionControl,
    PresenceManager,
    start_collaboration_server,
    stop_collaboration_server,
    get_collaboration_performance_stats,
    send_operation,
    resolve_conflict,
    get_active_users
)

class TestSecurityManager:
    """Test security manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.security_manager = SecurityManager("test-secret-key")

    def test_generate_token(self):
        """Test token generation."""
        user_id = "test_user"
        session_id = "test_session"

        token = self.security_manager.generate_token(user_id, session_id)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_validate_token_valid(self):
        """Test valid token validation."""
        user_id = "test_user"
        session_id = "test_session"

        token = self.security_manager.generate_token(user_id, session_id)
        result = self.security_manager.validate_token(token)

        assert result is not None
        assert result["user_id"] == user_id
        assert result["session_id"] == session_id

    def test_validate_token_invalid(self):
        """Test invalid token validation."""
        result = self.security_manager.validate_token("invalid-token")
        assert result is None

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        user_id = "test_user"
        operation_type = "create"

        # Should allow operations within limit
        for i in range(10):
            assert self.security_manager.check_rate_limit(user_id, operation_type)

        # Should block when limit exceeded
        assert not self.security_manager.check_rate_limit(user_id, operation_type)

    def test_rate_limiting_different_operations(self):
        """Test rate limiting for different operation types."""
        user_id = "test_user"

        # Test different limits for different operations
        assert self.security_manager.check_rate_limit(user_id, "create")  # limit: 10
        assert self.security_manager.check_rate_limit(user_id, "update")  # limit: 50
        assert self.security_manager.check_rate_limit(user_id, "delete")  # limit: 5

class TestConflictDetector:
    """Test conflict detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.conflict_detector = ConflictDetector()

    def test_detect_conflicts_no_conflicts(self):
        """Test conflict detection when no conflicts exist."""
        operation1 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.CREATE,
            user_id="user1",
            session_id="session1",
            timestamp=datetime.now(),
            element_id="element1"
        )

        operation2 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.CREATE,
            user_id="user2",
            session_id="session2",
            timestamp=datetime.now(),
            element_id="element2"
        )

        conflicts = self.conflict_detector.detect_conflicts(operation1, [operation2])
        assert len(conflicts) == 0

    def test_detect_conflicts_same_element(self):
        """Test conflict detection for same element."""
        operation1 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user1",
            session_id="session1",
            timestamp=datetime.now(),
            element_id="element1"
        )

        operation2 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=datetime.now(),
            element_id="element1"
        )

        conflicts = self.conflict_detector.detect_conflicts(operation1, [operation2])
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "concurrent_update"

    def test_detect_conflicts_delete_conflict(self):
        """Test conflict detection for delete operations."""
        operation1 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.DELETE,
            user_id="user1",
            session_id="session1",
            timestamp=datetime.now(),
            element_id="element1"
        )

        operation2 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=datetime.now(),
            element_id="element1"
        )

        conflicts = self.conflict_detector.detect_conflicts(operation1, [operation2])
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "delete_conflict"
        assert conflicts[0].severity == "high"

    def test_resolve_conflict(self):
        """Test conflict resolution."""
        operation1 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user1",
            session_id="session1",
            timestamp=datetime.now(),
            element_id="element1"
        )

        operation2 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=datetime.now(),
            element_id="element1"
        )

        conflicts = self.conflict_detector.detect_conflicts(operation1, [operation2])
        assert len(conflicts) == 1

        conflict_id = conflicts[0].conflict_id
        success = self.conflict_detector.resolve_conflict(
            conflict_id, ConflictResolution.LAST_WRITE_WINS, "user1"
        )

        assert success
        assert conflicts[0].resolution == ConflictResolution.LAST_WRITE_WINS
        assert conflicts[0].resolved_by == "user1"

    def test_acquire_release_lock(self):
        """Test element locking functionality."""
        element_id = "test_element"
        user_id = "test_user"

        # Acquire lock
        assert self.conflict_detector.acquire_lock(element_id, user_id)

        # Try to acquire lock again (should fail)
        assert not self.conflict_detector.acquire_lock(element_id, "other_user")

        # Release lock
        assert self.conflict_detector.release_lock(element_id, user_id)

        # Try to release lock again (should fail)
        assert not self.conflict_detector.release_lock(element_id, user_id)

class TestVersionControl:
    """Test version control functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.version_control = VersionControl(":memory:")  # Use in-memory database

    def test_create_version(self):
        """Test version creation."""
        operations = [
            Operation(
                operation_id=str(uuid.uuid4()),
                operation_type=OperationType.CREATE,
                user_id="user1",
                session_id="session1",
                timestamp=datetime.now(),
                element_id="element1"
            )
        ]

        version = self.version_control.create_version(
            operations, "user1", "Test version"
        )

        assert version.version_id is not None
        assert version.version_number == 1
        assert version.created_by == "user1"
        assert version.description == "Test version"
        assert len(version.operations) == 1

    def test_get_version_history(self):
        """Test version history retrieval."""
        # Create multiple versions
        for i in range(3):
            operations = [
                Operation(
                    operation_id=str(uuid.uuid4()),
                    operation_type=OperationType.CREATE,
                    user_id=f"user{i}",
                    session_id=f"session{i}",
                    timestamp=datetime.now(),
                    element_id=f"element{i}"
                )
            ]

            self.version_control.create_version(
                operations, f"user{i}", f"Version {i+1}"
            )

        history = self.version_control.get_version_history()
        assert len(history) == 3
        assert history[0].version_number == 1
        assert history[1].version_number == 2
        assert history[2].version_number == 3

    def test_revert_to_version(self):
        """Test version reversion."""
        # Create a version first
        operations = [
            Operation(
                operation_id=str(uuid.uuid4()),
                operation_type=OperationType.CREATE,
                user_id="user1",
                session_id="session1",
                timestamp=datetime.now(),
                element_id="element1"
            )
        ]

        version = self.version_control.create_version(operations, "user1", "Test version")

        # Revert to the version
        success = self.version_control.revert_to_version(version.version_id)
        assert success

        # Check that a new revert version was created
        history = self.version_control.get_version_history()
        assert len(history) == 2
        assert history[1].description.startswith("Revert to version")

class TestPresenceManager:
    """Test presence management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.presence_manager = PresenceManager()

    def test_add_user(self):
        """Test user addition."""
        user = self.presence_manager.add_user("user1", "Test User", "session1")

        assert user.user_id == "user1"
        assert user.username == "Test User"
        assert user.session_id == "session1"
        assert user.status == UserStatus.ONLINE

    def test_remove_user(self):
        """Test user removal."""
        user = self.presence_manager.add_user("user1", "Test User", "session1")

        self.presence_manager.remove_user("session1")

        # Check that user status is updated
        assert user.status == UserStatus.OFFLINE

    def test_update_user_activity(self):
        """Test user activity updates."""
        user = self.presence_manager.add_user("user1", "Test User", "session1")

        activity_data = {
            "current_element": "element1",
            "cursor_position": {"x": 100, "y": 200},
            "selected_elements": ["element1", "element2"],
            "status": "editing",
            "connection_quality": 0.8
        }

        self.presence_manager.update_user_activity("user1", activity_data)

        assert user.current_element == "element1"
        assert user.cursor_position == {"x": 100, "y": 200}
        assert user.selected_elements == ["element1", "element2"]
        assert user.status == UserStatus.EDITING
        assert user.connection_quality == 0.8

    def test_get_active_users(self):
        """Test active users retrieval."""
        # Add users
        user1 = self.presence_manager.add_user("user1", "User 1", "session1")
        user2 = self.presence_manager.add_user("user2", "User 2", "session2")

        # Update activity for one user
        self.presence_manager.update_user_activity("user1", {})

        active_users = self.presence_manager.get_active_users()
        assert len(active_users) == 2  # Both should be active initially

    def test_get_user_presence(self):
        """Test user presence retrieval."""
        user = self.presence_manager.add_user("user1", "Test User", "session1")

        retrieved_user = self.presence_manager.get_user_presence("user1")
        assert retrieved_user == user

        # Test non-existent user
        assert self.presence_manager.get_user_presence("nonexistent") is None

class TestRealtimeCollaboration:
    """Test real-time collaboration functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collaboration = RealtimeCollaboration("localhost", 8765)

    def test_initialization(self):
        """Test service initialization."""
        assert self.collaboration.host == "localhost"
        assert self.collaboration.port == 8765
        assert self.collaboration.conflict_detector is not None
        assert self.collaboration.version_control is not None
        assert self.collaboration.presence_manager is not None
        assert self.collaboration.security_manager is not None

    def test_performance_stats(self):
        """Test performance statistics."""
        stats = self.collaboration.get_performance_stats()

        assert "total_operations" in stats
        assert "conflicts_detected" in stats
        assert "average_propagation_time" in stats
        assert "active_users" in stats
        assert "total_messages" in stats

    @pytest.mark.asyncio
    async def test_handle_join(self):
        """Test join message handling."""
        client_id = "test_client"
        data = {
            "user_id": "user1",
            "username": "Test User",
            "session_id": "session1",
            "token": self.collaboration.security_manager.generate_token("user1", "session1")
        }

        # Mock websocket client
        mock_websocket = AsyncMock()
        self.collaboration.clients[client_id] = mock_websocket

        await self.collaboration._handle_join(client_id, data)

        # Check that user was added to presence manager
        user = self.collaboration.presence_manager.get_user_presence("user1")
        assert user is not None
        assert user.username == "Test User"

    @pytest.mark.asyncio
    async def test_handle_operation(self):
        """Test operation message handling."""
        client_id = "test_client"

        # Add user first
        user = self.collaboration.presence_manager.add_user("user1", "Test User", "session1")
        self.collaboration.client_info[client_id] = {
            "user_id": "user1",
            "session_id": "session1"
        }

        data = {
            "operation_type": "create",
            "element_id": "element1",
            "data": {"x": 100, "y": 200}
        }

        # Mock websocket client
        mock_websocket = AsyncMock()
        self.collaboration.clients[client_id] = mock_websocket

        await self.collaboration._handle_operation(client_id, data)

        # Check that operation was processed
        stats = self.collaboration.get_performance_stats()
        assert stats["total_operations"] > 0

    @pytest.mark.asyncio
    async def test_handle_activity(self):
        """Test activity message handling."""
        client_id = "test_client"

        # Add user first
        user = self.collaboration.presence_manager.add_user("user1", "Test User", "session1")
        self.collaboration.client_info[client_id] = {
            "user_id": "user1",
            "session_id": "session1"
        }

        data = {
            "current_element": "element1",
            "cursor_position": {"x": 100, "y": 200},
            "status": "editing"
        }

        await self.collaboration._handle_activity(client_id, data)

        # Check that user activity was updated
        user = self.collaboration.presence_manager.get_user_presence("user1")
        assert user.current_element == "element1"
        assert user.status == UserStatus.EDITING

    @pytest.mark.asyncio
    async def test_handle_conflict_resolution(self):
        """Test conflict resolution message handling."""
        client_id = "test_client"

        # Create a conflict first
        operation1 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user1",
            session_id="session1",
            timestamp=datetime.now(),
            element_id="element1"
        )

        operation2 = Operation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE,
            user_id="user2",
            session_id="session2",
            timestamp=datetime.now(),
            element_id="element1"
        )

        conflicts = self.collaboration.conflict_detector.detect_conflicts(operation1, [operation2])
        assert len(conflicts) == 1

        conflict_id = conflicts[0].conflict_id
        data = {
            "conflict_id": conflict_id,
            "resolution": "last_write_wins"
        }

        self.collaboration.client_info[client_id] = {
            "user_id": "user1",
            "session_id": "session1"
        }

        await self.collaboration._handle_conflict_resolution(client_id, data)

        # Check that conflict was resolved
        conflict = self.collaboration.conflict_detector.conflicts[conflict_id]
        assert conflict.resolution == ConflictResolution.LAST_WRITE_WINS

    @pytest.mark.asyncio
    async def test_handle_version_control(self):
        """Test version control message handling."""
        client_id = "test_client"

        self.collaboration.client_info[client_id] = {
            "user_id": "user1",
            "session_id": "session1"
        }

        data = {
            "action": "create_version",
            "description": "Test version"
        }

        # Mock websocket client
        mock_websocket = AsyncMock()
        self.collaboration.clients[client_id] = mock_websocket

        await self.collaboration._handle_version_control(client_id, data)

        # Check that version was created
        history = self.collaboration.version_control.get_version_history()
        assert len(history) == 1
        assert history[0].description == "Test version"

class TestIntegration:
    """Integration tests for the collaboration service."""

    @pytest.mark.asyncio
    async def test_full_collaboration_workflow(self):
        """Test a complete collaboration workflow."""
        # Start collaboration server
        success = await start_collaboration_server("localhost", 8766)
        assert success

        try:
            # Test performance stats
            stats = get_collaboration_performance_stats()
            assert isinstance(stats, dict)

            # Test sending operation
            operation_data = {
                "operation_type": "create",
                "element_id": "test_element",
                "data": {"x": 100, "y": 200}
            }

            success = await send_operation(operation_data)
            assert success

            # Test getting active users
            users = get_active_users()
            assert isinstance(users, list)

        finally:
            # Stop collaboration server
            await stop_collaboration_server()

    @pytest.mark.asyncio
    async def test_conflict_resolution_workflow(self):
        """Test conflict resolution workflow."""
        # Start collaboration server
        success = await start_collaboration_server("localhost", 8767)
        assert success

        try:
            # Test conflict resolution
            success = await resolve_conflict("test_conflict", "last_write_wins", "user1")
            # This should fail since the conflict doesn't exist, but shouldn't crash
            assert isinstance(success, bool)

        finally:
            # Stop collaboration server
            await stop_collaboration_server()

class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collaboration = RealtimeCollaboration("localhost", 8765)

    @pytest.mark.asyncio
    async def test_invalid_json_message(self):
        """Test handling of invalid JSON messages."""
        client_id = "test_client"

        # Mock websocket client
        mock_websocket = AsyncMock()
        self.collaboration.clients[client_id] = mock_websocket

        # Test with invalid JSON
        await self.collaboration._process_message(client_id, "invalid json")

        # Should not crash and should log error
        # (We can't easily test logging in unit tests, but we can ensure no exception)
    @pytest.mark.asyncio
    async def test_unknown_message_type(self):
        """Test handling of unknown message types."""
        client_id = "test_client"

        # Mock websocket client
        mock_websocket = AsyncMock()
        self.collaboration.clients[client_id] = mock_websocket

        data = {
            "type": "unknown_type",
            "data": "test"
        }

        await self.collaboration._process_message(client_id, json.dumps(data)
        # Should not crash and should log warning

    @pytest.mark.asyncio
    async def test_operation_without_authentication(self):
        """Test operation handling without proper authentication."""
        client_id = "test_client"

        # Mock websocket client
        mock_websocket = AsyncMock()
        self.collaboration.clients[client_id] = mock_websocket

        data = {
            "operation_type": "create",
            "element_id": "element1"
        }

        await self.collaboration._handle_operation(client_id, data)

        # Should send error message to client
        mock_websocket.send.assert_called()
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "error"

    def test_rate_limit_exceeded(self):
        """Test rate limiting functionality."""
        user_id = "test_user"
        operation_type = "create"

        # Exceed rate limit
        for i in range(11):  # Limit is 10
            result = self.collaboration.security_manager.check_rate_limit(user_id, operation_type)
            if i < 10:
                assert result
            else:
                assert not result

class TestPerformance:
    """Test performance characteristics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collaboration = RealtimeCollaboration("localhost", 8765)

    def test_operation_creation_performance(self):
        """Test operation creation performance."""
        start_time = time.time()

        for i in range(100):
            operation = Operation(
                operation_id=str(uuid.uuid4()),
                operation_type=OperationType.CREATE,
                user_id=f"user{i}",
                session_id=f"session{i}",
                timestamp=datetime.now(),
                element_id=f"element{i}"
            )

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time (less than 1 second for 100 operations)
        assert duration < 1.0

    def test_conflict_detection_performance(self):
        """Test conflict detection performance."""
        # Create many operations
        operations = []
        for i in range(100):
            operation = Operation(
                operation_id=str(uuid.uuid4()),
                operation_type=OperationType.UPDATE,
                user_id=f"user{i % 10}",  # 10 different users
                session_id=f"session{i}",
                timestamp=datetime.now(),
                element_id=f"element{i % 5}"  # 5 different elements
            )
            operations.append(operation)

        start_time = time.time()

        # Test conflict detection
        for operation in operations[:10]:  # Test first 10 operations
            conflicts = self.collaboration.conflict_detector.detect_conflicts(
                operation, operations[:i] if i > 0 else []
            )

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 1.0

    def test_presence_management_performance(self):
        """Test presence management performance."""
        start_time = time.time()

        # Add many users
        for i in range(100):
            self.collaboration.presence_manager.add_user(
                f"user{i}", f"User {i}", f"session{i}"
            )

        # Update activity for all users
        for i in range(100):
            self.collaboration.presence_manager.update_user_activity(
                f"user{i}", {"current_element": f"element{i}"}
            )

        # Get active users
        active_users = self.collaboration.presence_manager.get_active_users()

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 1.0
        assert len(active_users) == 100

class TestConcurrency:
    """Test concurrency and thread safety."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collaboration = RealtimeCollaboration("localhost", 8765)

    def test_concurrent_operations(self):
        """Test concurrent operation handling."""
def create_operation(user_id):
            operation = Operation(
                operation_id=str(uuid.uuid4()),
                operation_type=OperationType.CREATE,
                user_id=user_id,
                session_id=f"session_{user_id}",
                timestamp=datetime.now(),
                element_id=f"element_{user_id}"
            )
            return operation

        # Create operations concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(50):
                future = executor.submit(create_operation, f"user{i}")
                futures.append(future)

            operations = [future.result() for future in futures]

        # All operations should be created successfully
        assert len(operations) == 50
        assert all(op.user_id.startswith("user") for op in operations)

    def test_concurrent_presence_updates(self):
        """Test concurrent presence updates."""
def update_presence(user_id):
            self.collaboration.presence_manager.add_user(
                user_id, f"User {user_id}", f"session_{user_id}"
            )
            self.collaboration.presence_manager.update_user_activity(
                user_id, {"current_element": f"element_{user_id}"}
            )
            return user_id

        # Update presence concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(50):
                future = executor.submit(update_presence, f"user{i}")
                futures.append(future)

            results = [future.result() for future in futures]

        # All updates should be successful
        assert len(results) == 50
        active_users = self.collaboration.presence_manager.get_active_users()
        assert len(active_users) == 50

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
