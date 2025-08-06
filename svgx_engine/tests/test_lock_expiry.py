import pytest
import time
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from svgx_engine.runtime.advanced_behavior_engine import AdvancedBehaviorEngine
from svgx_engine.services.api_interface import app


class TestLockExpiryAndTimeouts:
    """Test suite for lock expiry and timeout functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = AdvancedBehaviorEngine()
        self.client = TestClient(app)
        self.canvas_id = "test-canvas-123"
        self.object_id = "test-object-456"
        self.session_id = "test-session-789"
        self.user_id = "test-user-101"

    def test_lock_timeout_configuration(self):
        """Test lock timeout configuration methods."""
        # Test default timeout
        assert self.engine.get_lock_timeout() == 300  # 5 minutes default

        # Test setting timeout
        self.engine.set_lock_timeout(600)  # 10 minutes
        assert self.engine.get_lock_timeout() == 600

        # Test setting back to default
        self.engine.set_lock_timeout(300)
        assert self.engine.get_lock_timeout() == 300

    def test_lock_acquisition_with_timestamp(self):
        """Test that locks are created with proper timestamp and timeout."""
        result = self.engine.lock_object(
            self.canvas_id, self.object_id, self.session_id, self.user_id
        )

        assert result["status"] == "lock_acquired"
        assert "lock_info" in result
        assert "timestamp" in result["lock_info"]
        assert "timeout_seconds" in result["lock_info"]
        assert result["lock_info"]["timeout_seconds"] == 300
        assert "expires_at" in result

        # Verify lock exists in engine
        lock_status = self.engine.get_lock_status(self.canvas_id, self.object_id)
        assert lock_status["status"] == "locked"
        assert lock_status["lock_info"]["session_id"] == self.session_id
        assert lock_status["lock_info"]["user_id"] == self.user_id

    def test_lock_expiry_detection(self):
        """Test that expired locks are detected and removed."""
        # Create a lock
        self.engine.lock_object(
            self.canvas_id, self.object_id, self.session_id, self.user_id
        )

        # Manually expire the lock by modifying timestamp
        lock_info = self.engine.locks[self.canvas_id][self.object_id]
        expired_timestamp = (
            datetime.utcnow() - timedelta(seconds=400)
        ).isoformat()  # 400 seconds ago
        lock_info["timestamp"] = expired_timestamp

        # Check lock status - should detect expiry and remove lock
        lock_status = self.engine.get_lock_status(self.canvas_id, self.object_id)
        assert lock_status["status"] == "unlocked"

        # Verify lock was removed
        assert self.object_id not in self.engine.locks[self.canvas_id]

    def test_lock_conflict_with_expiry(self):
        """Test that expired locks don't block new lock acquisition."""
        # Create a lock
        self.engine.lock_object(
            self.canvas_id, self.object_id, self.session_id, self.user_id
        )

        # Manually expire the lock
        lock_info = self.engine.locks[self.canvas_id][self.object_id]
        expired_timestamp = (datetime.utcnow() - timedelta(seconds=400)).isoformat()
        lock_info["timestamp"] = expired_timestamp

        # Try to acquire lock with different session - should succeed
        new_session_id = "new-session-999"
        result = self.engine.lock_object(
            self.canvas_id, self.object_id, new_session_id, self.user_id
        )
        assert result["status"] == "lock_acquired"
        assert result["lock_info"]["session_id"] == new_session_id

    def test_cleanup_expired_locks(self):
        """Test the background cleanup of expired locks."""
        # Create multiple locks
        self.engine.lock_object(self.canvas_id, "obj1", self.session_id, self.user_id)
        self.engine.lock_object(self.canvas_id, "obj2", self.session_id, self.user_id)
        self.engine.lock_object(self.canvas_id, "obj3", self.session_id, self.user_id)

        # Manually expire some locks
        self.engine.locks[self.canvas_id]["obj1"]["timestamp"] = (
            datetime.utcnow() - timedelta(seconds=400)
        ).isoformat()
        self.engine.locks[self.canvas_id]["obj2"]["timestamp"] = (
            datetime.utcnow() - timedelta(seconds=400)
        ).isoformat()

        # Run cleanup
        self.engine._cleanup_expired_locks()

        # Verify expired locks were removed
        assert "obj1" not in self.engine.locks[self.canvas_id]
        assert "obj2" not in self.engine.locks[self.canvas_id]
        assert "obj3" in self.engine.locks[self.canvas_id]  # Still valid

    def test_release_session_locks(self):
        """Test releasing all locks for a session."""
        # Create locks for multiple objects
        self.engine.lock_object(self.canvas_id, "obj1", self.session_id, self.user_id)
        self.engine.lock_object(self.canvas_id, "obj2", self.session_id, self.user_id)
        self.engine.lock_object(self.canvas_id, "obj3", "other-session", "other-user")

        # Release session locks
        result = self.engine.release_session_locks(self.session_id)

        assert result["status"] == "session_locks_released"
        assert result["session_id"] == self.session_id
        assert result["count"] == 2
        assert len(result["released_locks"]) == 2

        # Verify locks were released
        assert "obj1" not in self.engine.locks[self.canvas_id]
        assert "obj2" not in self.engine.locks[self.canvas_id]
        assert "obj3" in self.engine.locks[self.canvas_id]  # Other session's lock

    def test_get_all_locks(self):
        """Test getting all active locks with expiry filtering."""
        # Create locks
        self.engine.lock_object(self.canvas_id, "obj1", self.session_id, self.user_id)
        self.engine.lock_object(self.canvas_id, "obj2", self.session_id, self.user_id)

        # Manually expire one lock
        self.engine.locks[self.canvas_id]["obj1"]["timestamp"] = (
            datetime.utcnow() - timedelta(seconds=400)
        ).isoformat()

        # Get all locks - should filter out expired
        all_locks = self.engine.get_all_locks(self.canvas_id)

        assert self.canvas_id in all_locks
        assert "obj1" not in all_locks[self.canvas_id]  # Expired
        assert "obj2" in all_locks[self.canvas_id]  # Still valid

    def test_get_all_locks_filtered(self):
        """Test getting all locks with canvas filtering."""
        # Create locks on multiple canvases
        self.engine.lock_object("canvas1", "obj1", self.session_id, self.user_id)
        self.engine.lock_object("canvas2", "obj2", self.session_id, self.user_id)

        # Get locks for specific canvas
        all_locks = self.engine.get_all_locks("canvas1")

        assert "canvas1" in all_locks
        assert "canvas2" not in all_locks
        assert "obj1" in all_locks["canvas1"]

    @pytest.mark.asyncio
    async def test_api_set_lock_timeout(self):
        """Test the API endpoint for setting lock timeout."""
        response = self.client.post(
            "/runtime/lock-timeout/", json={"timeout_seconds": 600}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["timeout_seconds"] == 600

    @pytest.mark.asyncio
    async def test_api_set_lock_timeout_invalid(self):
        """Test API endpoint with invalid timeout values."""
        # Test negative timeout
        response = self.client.post(
            "/runtime/lock-timeout/", json={"timeout_seconds": -1}
        )
        assert response.status_code == 400

        # Test zero timeout
        response = self.client.post(
            "/runtime/lock-timeout/", json={"timeout_seconds": 0}
        )
        assert response.status_code == 400

        # Test missing timeout
        response = self.client.post("/runtime/lock-timeout/", json={})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_api_get_lock_timeout(self):
        """Test the API endpoint for getting lock timeout."""
        response = self.client.get("/runtime/lock-timeout/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "timeout_seconds" in data

    @pytest.mark.asyncio
    async def test_api_release_session_locks(self):
        """Test the API endpoint for releasing session locks."""
        # Create locks directly in the engine instance used by the API
        from svgx_engine.services.api_interface import engine

        # Create some locks
        engine.lock_object(self.canvas_id, "obj1", self.session_id, self.user_id)
        engine.lock_object(self.canvas_id, "obj2", self.session_id, self.user_id)

        response = self.client.post(
            "/runtime/release-session-locks/", json={"session_id": self.session_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "session_locks_released"
        assert data["session_id"] == self.session_id
        assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_api_release_session_locks_missing_session(self):
        """Test API endpoint with missing session_id."""
        response = self.client.post("/runtime/release-session-locks/", json={})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_api_get_all_locks(self):
        """Test the API endpoint for getting all locks."""
        # Create locks directly in the engine instance used by the API
        from svgx_engine.services.api_interface import engine

        # Create some locks
        engine.lock_object(self.canvas_id, "obj1", self.session_id, self.user_id)
        engine.lock_object("canvas2", "obj2", self.session_id, self.user_id)

        response = self.client.get("/runtime/all-locks/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "all_locks" in data
        assert data["total_locks"] >= 2

    @pytest.mark.asyncio
    async def test_api_get_all_locks_filtered(self):
        """Test the API endpoint for getting all locks with canvas filter."""
        # Create locks directly in the engine instance used by the API
        from svgx_engine.services.api_interface import engine

        # Create locks on multiple canvases
        engine.lock_object("canvas1", "obj1", self.session_id, self.user_id)
        engine.lock_object("canvas2", "obj2", self.session_id, self.user_id)

        response = self.client.get("/runtime/all-locks/?canvas_id=canvas1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "canvas1" in data["all_locks"]
        assert "canvas2" not in data["all_locks"]

    def test_lock_expiry_integration(self):
        """Integration test for complete lock expiry workflow."""
        # Set a short timeout for testing
        self.engine.set_lock_timeout(1)  # 1 second timeout

        # Acquire lock
        result = self.engine.lock_object(
            self.canvas_id, self.object_id, self.session_id, self.user_id
        )
        assert result["status"] == "lock_acquired"

        # Manually expire the lock
        lock_info = self.engine.locks[self.canvas_id][self.object_id]
        expired_timestamp = (datetime.utcnow() - timedelta(seconds=2)).isoformat()
        lock_info["timestamp"] = expired_timestamp

        # Try to acquire lock again - should succeed
        new_session = "new-session-123"
        result = self.engine.lock_object(
            self.canvas_id, self.object_id, new_session, self.user_id
        )
        assert result["status"] == "lock_acquired"
        assert result["lock_info"]["session_id"] == new_session

    def test_background_cleanup_task(self):
        """Test that background cleanup task is started."""
        # Verify cleanup task is started during initialization
        # This is mostly a smoke test since we can't easily test the background thread
        assert hasattr(self.engine, "_cleanup_expired_locks")
        assert hasattr(self.engine, "cleanup_interval_seconds")
        assert self.engine.cleanup_interval_seconds == 60

    def test_lock_expiry_edge_cases(self):
        """Test edge cases for lock expiry."""
        # Test with very short timeout
        self.engine.set_lock_timeout(1)

        # Acquire lock
        self.engine.lock_object(
            self.canvas_id, self.object_id, self.session_id, self.user_id
        )

        # Immediately expire
        lock_info = self.engine.locks[self.canvas_id][self.object_id]
        lock_info["timestamp"] = (datetime.utcnow() - timedelta(seconds=2)).isoformat()

        # Should be able to acquire again
        result = self.engine.lock_object(
            self.canvas_id, self.object_id, "new-session", self.user_id
        )
        assert result["status"] == "lock_acquired"

    def test_multiple_canvas_locks(self):
        """Test lock expiry across multiple canvases."""
        # Create locks on multiple canvases
        self.engine.lock_object("canvas1", "obj1", self.session_id, self.user_id)
        self.engine.lock_object("canvas2", "obj2", self.session_id, self.user_id)

        # Expire one lock
        self.engine.locks["canvas1"]["obj1"]["timestamp"] = (
            datetime.utcnow() - timedelta(seconds=400)
        ).isoformat()

        # Run cleanup
        self.engine._cleanup_expired_locks()

        # Verify only expired lock was removed
        assert "obj1" not in self.engine.locks["canvas1"]
        assert "obj2" in self.engine.locks["canvas2"]

    def test_lock_expiry_with_different_timeouts(self):
        """Test that different timeout settings work correctly."""
        # Set custom timeout
        self.engine.set_lock_timeout(10)  # 10 seconds

        # Acquire lock
        self.engine.lock_object(
            self.canvas_id, self.object_id, self.session_id, self.user_id
        )

        # Expire after 11 seconds (should be expired)
        lock_info = self.engine.locks[self.canvas_id][self.object_id]
        lock_info["timestamp"] = (datetime.utcnow() - timedelta(seconds=11)).isoformat()

        # Check status - should be expired
        lock_status = self.engine.get_lock_status(self.canvas_id, self.object_id)
        assert lock_status["status"] == "unlocked"

        # Reset timeout
        self.engine.set_lock_timeout(300)
