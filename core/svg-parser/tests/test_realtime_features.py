"""
Tests for Real-time Features
Tests WebSocket connections, user presence, collaborative editing, and cache management
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from services.realtime_service import (
    RealTimeService as RealtimeService, WebSocketManager, 
    CollaborativeEditingManager, ConflictResolutionManager,
    LockType, ConflictSeverity, UserPresence, EditingLock, Conflict
)
from ..services.cache_service import (
    CacheService, RedisCacheManager, IntelligentPreloader,
    CacheStrategy, CachePriority, CacheDecorator
)

class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    @pytest.fixture
    def websocket_manager(self):
        return WebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        websocket = Mock()
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, websocket_manager, mock_websocket):
        """Test WebSocket connection and disconnection"""
        user_id = "test_user"
        username = "Test User"
        
        # Test connection
        await websocket_manager.connect(mock_websocket, user_id, username)
        
        assert user_id in websocket_manager.active_connections
        assert user_id in websocket_manager.user_presence
        assert websocket_manager.user_presence[user_id].username == username
        assert websocket_manager.user_presence[user_id].is_active
        
        # Test disconnection
        await websocket_manager.disconnect(user_id)
        
        assert user_id not in websocket_manager.active_connections
        assert not websocket_manager.user_presence[user_id].is_active
    
    @pytest.mark.asyncio
    async def test_join_and_leave_room(self, websocket_manager, mock_websocket):
        """Test joining and leaving rooms"""
        user_id = "test_user"
        room_id = "test_room"
        
        # Connect user first
        await websocket_manager.connect(mock_websocket, user_id, "Test User")
        
        # Test joining room
        await websocket_manager.join_room(user_id, room_id)
        
        assert room_id in websocket_manager.room_connections
        assert user_id in websocket_manager.room_connections[room_id]
        assert websocket_manager.user_presence[user_id].floor_id == room_id
        
        # Test leaving room
        await websocket_manager.leave_room(user_id, room_id)
        
        assert user_id not in websocket_manager.room_connections[room_id]
        assert websocket_manager.user_presence[user_id].floor_id is None
    
    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, websocket_manager, mock_websocket):
        """Test broadcasting messages to room"""
        user_id = "test_user"
        room_id = "test_room"
        message = {"type": "test", "data": "test_message"}
        
        # Setup user in room
        await websocket_manager.connect(mock_websocket, user_id, "Test User")
        await websocket_manager.join_room(user_id, room_id)
        
        # Test broadcast
        await websocket_manager.broadcast_to_room(room_id, message)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_send_to_user(self, websocket_manager, mock_websocket):
        """Test sending message to specific user"""
        user_id = "test_user"
        message = {"type": "test", "data": "test_message"}
        
        # Connect user
        await websocket_manager.connect(mock_websocket, user_id, "Test User")
        
        # Test send to user
        await websocket_manager.send_to_user(user_id, message)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_send_room_state(self, websocket_manager, mock_websocket):
        """Test sending room state to user"""
        user_id = "test_user"
        room_id = "test_room"
        
        # Setup user in room
        await websocket_manager.connect(mock_websocket, user_id, "Test User")
        await websocket_manager.join_room(user_id, room_id)
        
        # Test sending room state
        await websocket_manager.send_room_state(user_id, room_id)
        
        # Verify room state message was sent
        mock_websocket.send_text.assert_called()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "room_state"
        assert sent_message["room_id"] == room_id

class TestCollaborativeEditingManager:
    """Test collaborative editing functionality"""
    
    @pytest.fixture
    def websocket_manager(self):
        return WebSocketManager()
    
    @pytest.fixture
    def editing_manager(self, websocket_manager):
        return CollaborativeEditingManager(websocket_manager)
    
    @pytest.mark.asyncio
    async def test_acquire_lock(self, editing_manager, websocket_manager, mock_websocket):
        """Test acquiring editing locks"""
        user_id = "test_user"
        username = "Test User"
        resource_id = "test_resource"
        lock_type = LockType.FLOOR_EDIT
        
        # Connect user
        await websocket_manager.connect(mock_websocket, user_id, username)
        
        # Test acquiring lock
        success, lock_id = await editing_manager.acquire_lock(
            user_id, username, lock_type, resource_id
        )
        
        assert success
        assert lock_id is not None
        assert lock_id in websocket_manager.editing_locks
        
        lock = websocket_manager.editing_locks[lock_id]
        assert lock.user_id == user_id
        assert lock.resource_id == resource_id
        assert lock.lock_type == lock_type
    
    @pytest.mark.asyncio
    async def test_acquire_lock_conflict(self, editing_manager, websocket_manager, mock_websocket):
        """Test lock acquisition when resource is already locked"""
        user_id_1 = "test_user_1"
        user_id_2 = "test_user_2"
        username = "Test User"
        resource_id = "test_resource"
        lock_type = LockType.FLOOR_EDIT
        
        # Connect users
        await websocket_manager.connect(mock_websocket, user_id_1, username)
        await websocket_manager.connect(mock_websocket, user_id_2, username)
        
        # First user acquires lock
        success1, lock_id1 = await editing_manager.acquire_lock(
            user_id_1, username, lock_type, resource_id
        )
        assert success1
        
        # Second user tries to acquire same lock
        success2, result2 = await editing_manager.acquire_lock(
            user_id_2, username, lock_type, resource_id
        )
        
        assert not success2
        assert "locked by" in result2
    
    @pytest.mark.asyncio
    async def test_release_lock(self, editing_manager, websocket_manager, mock_websocket):
        """Test releasing editing locks"""
        user_id = "test_user"
        username = "Test User"
        resource_id = "test_resource"
        lock_type = LockType.FLOOR_EDIT
        
        # Connect user and acquire lock
        await websocket_manager.connect(mock_websocket, user_id, username)
        success, lock_id = await editing_manager.acquire_lock(
            user_id, username, lock_type, resource_id
        )
        
        # Test releasing lock
        release_success = await editing_manager.release_lock(lock_id, user_id)
        
        assert release_success
        assert lock_id not in websocket_manager.editing_locks
    
    @pytest.mark.asyncio
    async def test_release_user_locks(self, editing_manager, websocket_manager, mock_websocket):
        """Test releasing all locks for a user"""
        user_id = "test_user"
        username = "Test User"
        
        # Connect user and acquire multiple locks
        await websocket_manager.connect(mock_websocket, user_id, username)
        
        await editing_manager.acquire_lock(user_id, username, LockType.FLOOR_EDIT, "resource1")
        await editing_manager.acquire_lock(user_id, username, LockType.OBJECT_EDIT, "resource2")
        
        # Test releasing all user locks
        await editing_manager.release_user_locks(user_id)
        
        # Verify all locks are released
        for lock in websocket_manager.editing_locks.values():
            assert lock.user_id != user_id

class TestConflictResolutionManager:
    """Test conflict resolution functionality"""
    
    @pytest.fixture
    def websocket_manager(self):
        return WebSocketManager()
    
    @pytest.fixture
    def conflict_manager(self, websocket_manager):
        return ConflictResolutionManager(websocket_manager)
    
    @pytest.mark.asyncio
    async def test_detect_conflict(self, conflict_manager, websocket_manager, mock_websocket):
        """Test conflict detection"""
        user_id_1 = "test_user_1"
        user_id_2 = "test_user_2"
        resource_id = "test_resource"
        
        # Connect users
        await websocket_manager.connect(mock_websocket, user_id_1, "User 1")
        await websocket_manager.connect(mock_websocket, user_id_2, "User 2")
        
        # Test conflict detection
        conflict_id = await conflict_manager.detect_conflict(
            resource_id, user_id_1, user_id_2,
            "edit_conflict", "Both users edited the same object",
            ConflictSeverity.MEDIUM
        )
        
        assert conflict_id is not None
        assert conflict_id in websocket_manager.conflicts
        
        conflict = websocket_manager.conflicts[conflict_id]
        assert conflict.resource_id == resource_id
        assert conflict.user_id_1 == user_id_1
        assert conflict.user_id_2 == user_id_2
        assert not conflict.resolved
    
    @pytest.mark.asyncio
    async def test_resolve_conflict(self, conflict_manager, websocket_manager, mock_websocket):
        """Test conflict resolution"""
        user_id_1 = "test_user_1"
        user_id_2 = "test_user_2"
        resource_id = "test_resource"
        
        # Connect users and create conflict
        await websocket_manager.connect(mock_websocket, user_id_1, "User 1")
        await websocket_manager.connect(mock_websocket, user_id_2, "User 2")
        
        conflict_id = await conflict_manager.detect_conflict(
            resource_id, user_id_1, user_id_2,
            "edit_conflict", "Test conflict"
        )
        
        # Test conflict resolution
        resolution_success = await conflict_manager.resolve_conflict(
            conflict_id, "accept_mine", user_id_1
        )
        
        assert resolution_success
        assert websocket_manager.conflicts[conflict_id].resolved
        assert websocket_manager.conflicts[conflict_id].resolution == "accept_mine"

class TestCacheService:
    """Test cache service functionality"""
    
    @pytest.fixture
    def cache_service(self):
        return CacheService("redis://localhost:6379")
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, cache_service):
        """Test basic cache operations"""
        # Test setting and getting cache
        test_data = {"test": "data", "number": 123}
        success = await cache_service.set_floor_data("test_floor", test_data)
        assert success
        
        cached_data = await cache_service.get_floor_data("test_floor")
        assert cached_data == test_data
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_service):
        """Test cache invalidation"""
        # Set some test data
        await cache_service.set_floor_data("test_floor", {"data": "test"})
        
        # Test invalidation
        count = await cache_service.invalidate_floor("test_floor")
        assert count > 0
        
        # Verify data is no longer cached
        cached_data = await cache_service.get_floor_data("test_floor")
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """Test cache statistics"""
        stats = await cache_service.get_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "evictions" in stats
        assert "preloads" in stats

class TestRealTimeService:
    """Test main real-time service integration"""
    
    @pytest.fixture
    def realtime_service(self):
        return RealtimeService()
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown(self, realtime_service):
        """Test service startup and shutdown"""
        # Test startup
        await realtime_service.start()
        
        # Verify services are running
        assert realtime_service.websocket_manager.cleanup_task is not None
        
        # Test shutdown
        await realtime_service.stop()
        
        # Verify cleanup task is cancelled
        assert realtime_service.websocket_manager.cleanup_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_handle_websocket_message(self, realtime_service):
        """Test WebSocket message handling"""
        user_id = "test_user"
        
        # Test join room message
        join_message = {
            "type": "join_room",
            "room_id": "test_room"
        }
        
        await realtime_service.handle_websocket_message(user_id, join_message)
        
        # Verify user joined room
        assert "test_room" in realtime_service.websocket_manager.room_connections
        assert user_id in realtime_service.websocket_manager.room_connections["test_room"]
    
    @pytest.mark.asyncio
    async def test_handle_acquire_lock(self, realtime_service):
        """Test lock acquisition message handling"""
        user_id = "test_user"
        
        # Setup user presence
        realtime_service.websocket_manager.user_presence[user_id] = UserPresence(
            user_id=user_id, username="Test User"
        )
        
        # Test acquire lock message
        lock_message = {
            "type": "acquire_lock",
            "lock_type": "floor_edit",
            "resource_id": "test_resource",
            "metadata": {}
        }
        
        await realtime_service.handle_websocket_message(user_id, lock_message)
        
        # Verify lock was acquired
        assert len(realtime_service.websocket_manager.editing_locks) > 0

class TestIntelligentPreloader:
    """Test intelligent preloading functionality"""
    
    @pytest.fixture
    def cache_manager(self):
        return RedisCacheManager()
    
    @pytest.fixture
    def preloader(self, cache_manager):
        return IntelligentPreloader(cache_manager)
    
    @pytest.mark.asyncio
    async def test_preload_related_data(self, preloader):
        """Test preloading related data"""
        floor_id = "test_floor"
        
        # Test preloading floor access data
        await preloader.preload_related_data(floor_id, "floor_access")
        
        # Verify preload history is updated
        assert floor_id in preloader.preload_history
        assert len(preloader.preload_history[floor_id]) > 0
    
    @pytest.mark.asyncio
    async def test_predict_and_preload(self, preloader):
        """Test prediction and preloading"""
        user_id = "test_user"
        floor_id = "test_floor"
        
        # Test prediction and preload
        await preloader.predict_and_preload(user_id, floor_id)
        
        # Verify preload history is updated
        assert floor_id in preloader.preload_history

class TestCacheDecorator:
    """Test cache decorator functionality"""
    
    @pytest.fixture
    def cache_manager(self):
        return RedisCacheManager()
    
    @pytest.fixture
    def cache_decorator(self, cache_manager):
        return CacheDecorator(cache_manager, CacheStrategy.FLOOR_DATA)
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self, cache_decorator, cache_manager):
        """Test cache decorator"""
        # Mock function
        call_count = 0
        
        @cache_decorator
        async def test_function(floor_id):
            nonlocal call_count
            call_count += 1
            return {"floor_id": floor_id, "data": "test"}
        
        # First call should execute function
        result1 = await test_function("test_floor")
        assert call_count == 1
        assert result1["floor_id"] == "test_floor"
        
        # Second call should use cache
        result2 = await test_function("test_floor")
        assert call_count == 1  # Should not increment
        assert result2 == result1

# Integration tests
class TestRealTimeIntegration:
    """Integration tests for real-time features"""
    
    @pytest.mark.asyncio
    async def test_full_collaborative_workflow(self):
        """Test full collaborative editing workflow"""
        # Create services
        realtime_service = RealtimeService()
        cache_service = CacheService()
        
        # Start services
        await realtime_service.start()
        await cache_service.start()
        
        try:
            # Simulate two users connecting
            mock_ws1 = Mock()
            mock_ws1.send_text = AsyncMock()
            mock_ws2 = Mock()
            mock_ws2.send_text = AsyncMock()
            
            # Connect users
            await realtime_service.websocket_manager.connect(mock_ws1, "user1", "User 1")
            await realtime_service.websocket_manager.connect(mock_ws2, "user2", "User 2")
            
            # Join same room
            await realtime_service.websocket_manager.join_room("user1", "test_room")
            await realtime_service.websocket_manager.join_room("user2", "test_room")
            
            # User 1 acquires lock
            success, lock_id = await realtime_service.collaborative_editing.acquire_lock(
                "user1", "User 1", LockType.FLOOR_EDIT, "test_resource"
            )
            assert success
            
            # User 2 tries to acquire same lock (should fail)
            success2, result2 = await realtime_service.collaborative_editing.acquire_lock(
                "user2", "User 2", LockType.FLOOR_EDIT, "test_resource"
            )
            assert not success2
            
            # User 1 releases lock
            release_success = await realtime_service.collaborative_editing.release_lock(lock_id, "user1")
            assert release_success
            
            # User 2 can now acquire lock
            success3, lock_id3 = await realtime_service.collaborative_editing.acquire_lock(
                "user2", "User 2", LockType.FLOOR_EDIT, "test_resource"
            )
            assert success3
            
        finally:
            # Cleanup
            await realtime_service.stop()
            await cache_service.stop()
    
    @pytest.mark.asyncio
    async def test_cache_with_realtime_integration(self):
        """Test cache integration with real-time features"""
        realtime_service = RealtimeService()
        cache_service = CacheService()
        
        await realtime_service.start()
        await cache_service.start()
        
        try:
            # Test floor data caching
            floor_data = {"objects": [], "routes": [], "grid": {}}
            await cache_service.set_floor_data("test_floor", floor_data)
            
            # Verify data is cached
            cached_data = await cache_service.get_floor_data("test_floor")
            assert cached_data == floor_data
            
            # Test cache invalidation on floor update
            count = await cache_service.invalidate_floor("test_floor")
            assert count > 0
            
            # Verify data is no longer cached
            cached_data = await cache_service.get_floor_data("test_floor")
            assert cached_data is None
            
        finally:
            await realtime_service.stop()
            await cache_service.stop()

if __name__ == "__main__":
    pytest.main([__file__]) 