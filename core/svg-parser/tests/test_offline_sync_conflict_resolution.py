"""
Comprehensive Test Suite for Offline Sync & Conflict Resolution Service

This test suite covers all aspects of the offline sync and conflict resolution
functionality including:
- Two-way sync operations
- Conflict detection algorithms
- Safe merging strategies
- Rollback capabilities
- Performance metrics
- Error handling and edge cases
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

from services.offline_sync_conflict_resolution import (
    OfflineSyncConflictResolutionService,
    SyncStatus,
    ConflictType,
    SyncOperation,
    SyncState,
    ConflictResolution
)


class TestOfflineSyncConflictResolutionService:
    """Test suite for the OfflineSyncConflictResolutionService."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            import os
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.fixture
    def sync_service(self, temp_db_path):
        """Create a sync service instance for testing."""
        return OfflineSyncConflictResolutionService(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_local_data(self):
        """Sample local data for testing."""
        return {
            "id": "object_001",
            "name": "Test Object",
            "type": "equipment",
            "location": {"x": 100, "y": 200},
            "properties": {"status": "active", "priority": "high"},
            "last_modified": 1640995200,  # 2022-01-01
            "last_sync_timestamp": 1640995200
        }
    
    @pytest.fixture
    def sample_remote_data(self):
        """Sample remote data for testing."""
        return {
            "id": "object_001",
            "name": "Test Object",
            "type": "equipment",
            "location": {"x": 150, "y": 250},
            "properties": {"status": "inactive", "priority": "medium"},
            "last_modified": 1640995300,  # 2022-01-01 + 100 seconds
            "last_sync_timestamp": 1640995200
        }
    
    @pytest.fixture
    def sample_changes(self):
        """Sample local changes for testing."""
        return [
            {
                "id": "object_001",
                "name": "Updated Test Object",
                "type": "equipment",
                "location": {"x": 100, "y": 200},
                "properties": {"status": "active", "priority": "high"},
                "last_modified": 1640995400,
                "last_sync_timestamp": 1640995200
            },
            {
                "id": "object_002",
                "name": "New Object",
                "type": "system",
                "location": {"x": 300, "y": 400},
                "properties": {"status": "active", "priority": "low"},
                "last_modified": 1640995500,
                "last_sync_timestamp": 1640995200
            }
        ]
    
    @pytest.fixture
    def sample_remote_state(self):
        """Sample remote state for testing."""
        return {
            "objects": {
                "object_001": {
                    "id": "object_001",
                    "name": "Test Object",
                    "type": "equipment",
                    "location": {"x": 150, "y": 250},
                    "properties": {"status": "inactive", "priority": "medium"},
                    "last_modified": 1640995300,
                    "last_sync_timestamp": 1640995200
                },
                "object_003": {
                    "id": "object_003",
                    "name": "Remote Object",
                    "type": "system",
                    "location": {"x": 500, "y": 600},
                    "properties": {"status": "active", "priority": "medium"},
                    "last_modified": 1640995600,
                    "last_sync_timestamp": 1640995200
                }
            },
            "last_updated": 1640995600
        }
    
    def test_service_initialization(self, sync_service):
        """Test service initialization and database setup."""
        assert sync_service is not None
        assert sync_service.db_path is not None
        assert sync_service.lock is not None
        assert isinstance(sync_service.metrics, dict)
    
    def test_generate_operation_id(self, sync_service):
        """Test operation ID generation."""
        device_id = "test_device_001"
        operation_type = "sync"
        
        operation_id = sync_service._generate_operation_id(device_id, operation_type)
        
        assert operation_id is not None
        assert device_id in operation_id
        assert operation_type in operation_id
        assert "_" in operation_id
    
    def test_calculate_data_hash(self, sync_service, sample_local_data):
        """Test data hash calculation."""
        hash1 = sync_service._calculate_data_hash(sample_local_data)
        hash2 = sync_service._calculate_data_hash(sample_local_data)
        
        # Same data should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash length
        
        # Different data should produce different hash
        modified_data = sample_local_data.copy()
        modified_data["name"] = "Modified Object"
        hash3 = sync_service._calculate_data_hash(modified_data)
        
        assert hash1 != hash3
    
    def test_detect_conflicts_no_conflict(self, sync_service, sample_local_data):
        """Test conflict detection when no conflict exists."""
        # Same data should not have conflicts
        conflict_type = sync_service.detect_conflicts(sample_local_data, sample_local_data)
        assert conflict_type is None
    
    def test_detect_conflicts_modification_conflict(self, sync_service, sample_local_data, sample_remote_data):
        """Test detection of modification conflicts."""
        # Modify both local and remote data after last sync
        local_data = sample_local_data.copy()
        remote_data = sample_remote_data.copy()
        
        local_data["last_modified"] = 1640995400  # After last sync
        remote_data["last_modified"] = 1640995300  # After last sync
        
        conflict_type = sync_service.detect_conflicts(local_data, remote_data)
        
        assert conflict_type == ConflictType.MODIFICATION_CONFLICT
    
    def test_detect_conflicts_deletion_conflict(self, sync_service, sample_local_data, sample_remote_data):
        """Test detection of deletion conflicts."""
        local_data = sample_local_data.copy()
        remote_data = sample_remote_data.copy()
        
        local_data["deleted"] = True
        remote_data["deleted"] = False
        
        conflict_type = sync_service.detect_conflicts(local_data, remote_data)
        
        assert conflict_type == ConflictType.DELETION_CONFLICT
    
    def test_detect_conflicts_creation_conflict(self, sync_service, sample_local_data, sample_remote_data):
        """Test detection of creation conflicts."""
        local_data = sample_local_data.copy()
        remote_data = sample_remote_data.copy()
        
        # Same ID but different creation timestamps
        local_data["created_at"] = 1640995200
        remote_data["created_at"] = 1640995300
        
        conflict_type = sync_service.detect_conflicts(local_data, remote_data)
        
        assert conflict_type == ConflictType.CREATION_CONFLICT
    
    def test_resolve_conflict_auto_strategy(self, sync_service, sample_local_data, sample_remote_data):
        """Test automatic conflict resolution."""
        conflict_type = ConflictType.MODIFICATION_CONFLICT
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=conflict_type,
            local_data=sample_local_data,
            remote_data=sample_remote_data,
            resolution_strategy="auto"
        )
        
        assert resolved_data is not None
        assert "id" in resolved_data
        assert resolved_data["id"] == "object_001"
        
        # Should merge properties from both versions
        assert "properties" in resolved_data
        assert "location" in resolved_data
    
    def test_resolve_conflict_local_strategy(self, sync_service, sample_local_data, sample_remote_data):
        """Test local-first conflict resolution."""
        conflict_type = ConflictType.MODIFICATION_CONFLICT
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=conflict_type,
            local_data=sample_local_data,
            remote_data=sample_remote_data,
            resolution_strategy="local"
        )
        
        assert resolved_data == sample_local_data
    
    def test_resolve_conflict_remote_strategy(self, sync_service, sample_local_data, sample_remote_data):
        """Test remote-first conflict resolution."""
        conflict_type = ConflictType.MODIFICATION_CONFLICT
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=conflict_type,
            local_data=sample_local_data,
            remote_data=sample_remote_data,
            resolution_strategy="remote"
        )
        
        assert resolved_data == sample_remote_data
    
    def test_resolve_conflict_manual_strategy(self, sync_service, sample_local_data, sample_remote_data):
        """Test manual conflict resolution."""
        conflict_type = ConflictType.MODIFICATION_CONFLICT
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=conflict_type,
            local_data=sample_local_data,
            remote_data=sample_remote_data,
            resolution_strategy="manual"
        )
        
        assert resolved_data["requires_manual_resolution"] is True
        assert resolved_data["local_data"] == sample_local_data
        assert resolved_data["remote_data"] == sample_remote_data
    
    def test_merge_modifications(self, sync_service, sample_local_data, sample_remote_data):
        """Test merging of modifications."""
        merged_data = sync_service._merge_modifications(sample_local_data, sample_remote_data)
        
        assert merged_data is not None
        assert merged_data["id"] == "object_001"
        assert "merge_timestamp" in merged_data
        assert merged_data["last_modified"] == max(
            sample_local_data["last_modified"],
            sample_remote_data["last_modified"]
        )
    
    def test_sync_data_success(self, sync_service, sample_changes, sample_remote_state):
        """Test successful sync operation."""
        device_id = "test_device_001"
        
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=sample_changes,
            remote_data=sample_remote_state
        )
        
        assert result["status"] == "success"
        assert "operation_id" in result
        assert result["synced_changes"] >= 0
        assert result["conflicts_resolved"] >= 0
        assert result["duration_ms"] > 0
    
    def test_sync_data_with_conflicts(self, sync_service, sample_changes, sample_remote_state):
        """Test sync operation with conflicts."""
        device_id = "test_device_002"
        
        # Modify sample changes to create conflicts
        conflicting_changes = sample_changes.copy()
        conflicting_changes[0]["last_modified"] = 1640995700  # After remote modification
        
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=conflicting_changes,
            remote_data=sample_remote_state
        )
        
        assert result["status"] == "success"
        assert result["conflicts_resolved"] >= 0
    
    def test_sync_data_empty_changes(self, sync_service, sample_remote_state):
        """Test sync operation with no local changes."""
        device_id = "test_device_003"
        
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=[],
            remote_data=sample_remote_state
        )
        
        assert result["status"] == "success"
        assert result["synced_changes"] == 0
    
    def test_sync_data_invalid_device_id(self, sync_service, sample_changes, sample_remote_state):
        """Test sync operation with invalid device ID."""
        with pytest.raises(Exception):
            sync_service.sync_data(
                device_id="",  # Empty device ID
                local_changes=sample_changes,
                remote_data=sample_remote_state
            )
    
    def test_get_sync_status_new_device(self, sync_service):
        """Test getting sync status for a new device."""
        device_id = "new_device_001"
        
        status = sync_service.get_sync_status(device_id)
        
        assert status["device_id"] == device_id
        assert status["status"] == "not_initialized"
        assert status["unsynced_changes"] == 0
    
    def test_get_sync_status_existing_device(self, sync_service, sample_changes, sample_remote_state):
        """Test getting sync status for an existing device."""
        device_id = "existing_device_001"
        
        # Perform a sync first
        sync_service.sync_data(
            device_id=device_id,
            local_changes=sample_changes,
            remote_data=sample_remote_state
        )
        
        # Get status
        status = sync_service.get_sync_status(device_id)
        
        assert status["device_id"] == device_id
        assert status["status"] in ["completed", "pending"]
        assert status["total_operations"] > 0
    
    def test_get_sync_history(self, sync_service, sample_changes, sample_remote_state):
        """Test getting sync history."""
        device_id = "history_device_001"
        
        # Perform multiple syncs
        for i in range(3):
            sync_service.sync_data(
                device_id=device_id,
                local_changes=sample_changes,
                remote_data=sample_remote_state
            )
        
        # Get history
        history = sync_service.get_sync_history(device_id, limit=10)
        
        assert len(history) > 0
        assert all("operation_id" in op for op in history)
        assert all("timestamp" in op for op in history)
    
    def test_rollback_sync_success(self, sync_service, sample_changes, sample_remote_state):
        """Test successful sync rollback."""
        device_id = "rollback_device_001"
        
        # Perform a sync first
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=sample_changes,
            remote_data=sample_remote_state
        )
        
        operation_id = result["operation_id"]
        
        # Rollback the operation
        rollback_result = sync_service.rollback_sync(device_id, operation_id)
        
        assert rollback_result["status"] == "success"
        assert rollback_result["rolled_back_operation"] == operation_id
    
    def test_rollback_sync_invalid_operation(self, sync_service):
        """Test rollback with invalid operation ID."""
        device_id = "invalid_device_001"
        invalid_operation_id = "invalid_operation_001"
        
        with pytest.raises(ValueError):
            sync_service.rollback_sync(device_id, invalid_operation_id)
    
    def test_get_metrics(self, sync_service, sample_changes, sample_remote_state):
        """Test getting sync metrics."""
        # Perform some syncs to generate metrics
        for i in range(3):
            sync_service.sync_data(
                device_id=f"metrics_device_{i:03d}",
                local_changes=sample_changes,
                remote_data=sample_remote_state
            )
        
        metrics = sync_service.get_metrics()
        
        assert "metrics" in metrics
        assert "total_devices" in metrics
        assert "database_size" in metrics
        assert metrics["total_devices"] >= 0
        assert metrics["database_size"] > 0
    
    def test_cleanup_old_operations(self, sync_service, sample_changes, sample_remote_state):
        """Test cleanup of old operations."""
        # Perform some syncs
        for i in range(5):
            sync_service.sync_data(
                device_id=f"cleanup_device_{i:03d}",
                local_changes=sample_changes,
                remote_data=sample_remote_state
            )
        
        # Clean up operations older than 1 day (should keep recent ones)
        deleted_count = sync_service.cleanup_old_operations(days=1)
        
        assert deleted_count >= 0  # May be 0 if all operations are recent
    
    def test_concurrent_sync_operations(self, sync_service, sample_changes, sample_remote_state):
        """Test concurrent sync operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def sync_worker(device_id):
            try:
                result = sync_service.sync_data(
                    device_id=device_id,
                    local_changes=sample_changes,
                    remote_data=sample_remote_state
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent syncs
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=sync_worker,
                args=(f"concurrent_device_{i:03d}",)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent sync errors: {errors}"
        assert len(results) == 5
        assert all(result["status"] == "success" for result in results)
    
    def test_large_data_sync(self, sync_service, sample_remote_state):
        """Test sync with large amounts of data."""
        # Create large dataset
        large_changes = []
        for i in range(1000):
            change = {
                "id": f"large_object_{i:04d}",
                "name": f"Large Object {i}",
                "type": "equipment",
                "location": {"x": i * 10, "y": i * 20},
                "properties": {
                    "status": "active" if i % 2 == 0 else "inactive",
                    "priority": "high" if i % 3 == 0 else "medium" if i % 3 == 1 else "low",
                    "data": "x" * 1000  # Large data field
                },
                "last_modified": 1640995200 + i,
                "last_sync_timestamp": 1640995200
            }
            large_changes.append(change)
        
        device_id = "large_data_device_001"
        
        # Perform sync with large data
        start_time = time.time()
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=large_changes,
            remote_data=sample_remote_state
        )
        end_time = time.time()
        
        assert result["status"] == "success"
        assert result["synced_changes"] >= 0
        assert (end_time - start_time) < 60  # Should complete within 60 seconds
    
    def test_error_handling_invalid_data(self, sync_service):
        """Test error handling with invalid data."""
        device_id = "error_device_001"
        
        # Test with invalid data structure
        invalid_changes = [{"invalid": "data", "missing": "required_fields"}]
        invalid_remote_data = {"invalid": "structure"}
        
        with pytest.raises(Exception):
            sync_service.sync_data(
                device_id=device_id,
                local_changes=invalid_changes,
                remote_data=invalid_remote_data
            )
    
    def test_database_persistence(self, temp_db_path, sample_changes, sample_remote_state):
        """Test that sync data persists across service instances."""
        device_id = "persistence_device_001"
        
        # Create first service instance and perform sync
        service1 = OfflineSyncConflictResolutionService(db_path=temp_db_path)
        result1 = service1.sync_data(
            device_id=device_id,
            local_changes=sample_changes,
            remote_data=sample_remote_state
        )
        
        # Create second service instance and check status
        service2 = OfflineSyncConflictResolutionService(db_path=temp_db_path)
        status = service2.get_sync_status(device_id)
        
        assert status["device_id"] == device_id
        assert status["status"] != "not_initialized"
    
    def test_performance_metrics(self, sync_service, sample_changes, sample_remote_state):
        """Test performance metrics collection."""
        device_id = "performance_device_001"
        
        # Perform sync and check metrics
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=sample_changes,
            remote_data=sample_remote_state
        )
        
        metrics = sync_service.get_metrics()
        
        assert metrics["metrics"]["total_syncs"] > 0
        assert metrics["metrics"]["successful_syncs"] > 0
        assert metrics["metrics"]["average_sync_time"] >= 0
    
    def test_conflict_resolution_strategies(self, sync_service, sample_local_data, sample_remote_data):
        """Test all conflict resolution strategies."""
        conflict_type = ConflictType.MODIFICATION_CONFLICT
        
        strategies = ["auto", "local", "remote", "manual"]
        
        for strategy in strategies:
            resolved_data = sync_service.resolve_conflict(
                conflict_type=conflict_type,
                local_data=sample_local_data,
                remote_data=sample_remote_data,
                resolution_strategy=strategy
            )
            
            assert resolved_data is not None
            
            if strategy == "local":
                assert resolved_data == sample_local_data
            elif strategy == "remote":
                assert resolved_data == sample_remote_data
            elif strategy == "manual":
                assert resolved_data["requires_manual_resolution"] is True
    
    def test_sync_state_management(self, sync_service, sample_changes, sample_remote_state):
        """Test sync state management and persistence."""
        device_id = "state_device_001"
        
        # Initial state should be not initialized
        initial_status = sync_service.get_sync_status(device_id)
        assert initial_status["status"] == "not_initialized"
        
        # Perform sync
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=sample_changes,
            remote_data=sample_remote_state
        )
        
        # Check updated state
        updated_status = sync_service.get_sync_status(device_id)
        assert updated_status["status"] in ["completed", "pending"]
        assert updated_status["total_operations"] > 0
    
    def test_edge_cases(self, sync_service):
        """Test various edge cases."""
        # Test with empty data
        empty_result = sync_service.sync_data(
            device_id="empty_device_001",
            local_changes=[],
            remote_data={"objects": {}}
        )
        assert empty_result["status"] == "success"
        
        # Test with very large object IDs
        large_id = "x" * 1000
        large_changes = [{"id": large_id, "name": "Large ID Object"}]
        
        large_result = sync_service.sync_data(
            device_id="large_id_device_001",
            local_changes=large_changes,
            remote_data={"objects": {}}
        )
        assert large_result["status"] == "success"
        
        # Test with special characters in device ID
        special_device_id = "device-with-special-chars!@#$%^&*()"
        special_result = sync_service.sync_data(
            device_id=special_device_id,
            local_changes=[],
            remote_data={"objects": {}}
        )
        assert special_result["status"] == "success"


class TestConflictResolution:
    """Test suite for conflict resolution functionality."""
    
    @pytest.fixture
    def sync_service(self, temp_db_path):
        """Create a sync service instance for testing."""
        return OfflineSyncConflictResolutionService(db_path=temp_db_path)
    
    def test_modification_conflict_resolution(self, sync_service):
        """Test resolution of modification conflicts."""
        local_data = {
            "id": "test_001",
            "name": "Local Name",
            "properties": {"status": "active"},
            "last_modified": 1640995400
        }
        
        remote_data = {
            "id": "test_001",
            "name": "Remote Name",
            "properties": {"status": "inactive"},
            "last_modified": 1640995300
        }
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=ConflictType.MODIFICATION_CONFLICT,
            local_data=local_data,
            remote_data=remote_data,
            resolution_strategy="auto"
        )
        
        assert resolved_data["id"] == "test_001"
        assert "merge_timestamp" in resolved_data
        assert resolved_data["last_modified"] == 1640995400  # Should prefer more recent
    
    def test_deletion_conflict_resolution(self, sync_service):
        """Test resolution of deletion conflicts."""
        local_data = {
            "id": "test_002",
            "name": "Local Object",
            "deleted": True,
            "last_modified": 1640995400
        }
        
        remote_data = {
            "id": "test_002",
            "name": "Remote Object",
            "deleted": False,
            "last_modified": 1640995300
        }
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=ConflictType.DELETION_CONFLICT,
            local_data=local_data,
            remote_data=remote_data,
            resolution_strategy="auto"
        )
        
        # Should keep the non-deleted version
        assert resolved_data["deleted"] is False
    
    def test_creation_conflict_resolution(self, sync_service):
        """Test resolution of creation conflicts."""
        local_data = {
            "id": "test_003",
            "name": "Local Object",
            "created_at": 1640995200,
            "last_modified": 1640995400
        }
        
        remote_data = {
            "id": "test_003",
            "name": "Remote Object",
            "created_at": 1640995300,
            "last_modified": 1640995300
        }
        
        resolved_data = sync_service.resolve_conflict(
            conflict_type=ConflictType.CREATION_CONFLICT,
            local_data=local_data,
            remote_data=remote_data,
            resolution_strategy="auto"
        )
        
        # Should prefer the version with more recent creation
        assert resolved_data["created_at"] == 1640995300


class TestPerformanceAndScalability:
    """Test suite for performance and scalability aspects."""
    
    @pytest.fixture
    def sync_service(self, temp_db_path):
        """Create a sync service instance for testing."""
        return OfflineSyncConflictResolutionService(db_path=temp_db_path)
    
    def test_sync_performance_targets(self, sync_service):
        """Test that sync operations meet performance targets."""
        import time
        
        # Create test data
        changes = []
        for i in range(100):
            changes.append({
                "id": f"perf_object_{i:03d}",
                "name": f"Performance Object {i}",
                "type": "equipment",
                "last_modified": 1640995200 + i
            })
        
        remote_data = {"objects": {}}
        device_id = "performance_test_device"
        
        # Measure sync performance
        start_time = time.time()
        result = sync_service.sync_data(
            device_id=device_id,
            local_changes=changes,
            remote_data=remote_data
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Performance targets
        assert duration < 60  # Should complete within 60 seconds
        assert result["duration_ms"] < 60000  # Duration in milliseconds
        assert result["status"] == "success"
    
    def test_conflict_detection_accuracy(self, sync_service):
        """Test conflict detection accuracy."""
        # Test cases for different conflict types
        test_cases = [
            {
                "local": {"id": "test", "name": "Local", "last_modified": 1640995400},
                "remote": {"id": "test", "name": "Remote", "last_modified": 1640995300},
                "expected": ConflictType.MODIFICATION_CONFLICT
            },
            {
                "local": {"id": "test", "deleted": True},
                "remote": {"id": "test", "deleted": False},
                "expected": ConflictType.DELETION_CONFLICT
            },
            {
                "local": {"id": "test", "created_at": 1640995200},
                "remote": {"id": "test", "created_at": 1640995300},
                "expected": ConflictType.CREATION_CONFLICT
            }
        ]
        
        for test_case in test_cases:
            conflict_type = sync_service.detect_conflicts(
                test_case["local"],
                test_case["remote"]
            )
            
            if test_case["expected"]:
                assert conflict_type == test_case["expected"]
    
    def test_safe_merging_accuracy(self, sync_service):
        """Test safe merging accuracy."""
        local_data = {
            "id": "merge_test",
            "name": "Local Name",
            "properties": {"status": "active", "priority": "high"},
            "location": {"x": 100, "y": 200},
            "last_modified": 1640995400
        }
        
        remote_data = {
            "id": "merge_test",
            "name": "Remote Name",
            "properties": {"status": "inactive", "priority": "medium"},
            "location": {"x": 150, "y": 250},
            "last_modified": 1640995300
        }
        
        merged_data = sync_service._merge_modifications(local_data, remote_data)
        
        # Should preserve all fields
        assert merged_data["id"] == "merge_test"
        assert "name" in merged_data
        assert "properties" in merged_data
        assert "location" in merged_data
        assert "merge_timestamp" in merged_data
        assert merged_data["last_modified"] == 1640995400  # More recent timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 