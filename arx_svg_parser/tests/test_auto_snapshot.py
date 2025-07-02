"""
Tests for Auto-Snapshot Service

Tests cover:
- Configuration management
- Change detection
- Intelligent scheduling
- Cleanup operations
- Service lifecycle
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from arx_svg_parser.services.auto_snapshot import (
    AutoSnapshotService, SnapshotConfig, SnapshotTrigger, 
    SnapshotPriority, ChangeMetrics, ChangeDetector,
    IntelligentSnapshotScheduler, SnapshotCleanupManager,
    create_auto_snapshot_service
)


class TestSnapshotConfig:
    """Test SnapshotConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = SnapshotConfig()
        
        assert config.enabled is True
        assert config.time_interval_minutes == 15
        assert config.change_threshold == 10
        assert config.major_edit_threshold == 25
        assert config.max_snapshots_per_hour == 4
        assert config.max_snapshots_per_day == 24
        assert config.retention_days == 30
        assert config.cleanup_enabled is True
        assert config.compression_enabled is True
        assert config.backup_enabled is True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = SnapshotConfig(
            enabled=False,
            time_interval_minutes=30,
            change_threshold=20,
            major_edit_threshold=50,
            max_snapshots_per_hour=2,
            max_snapshots_per_day=12,
            retention_days=60,
            cleanup_enabled=False,
            compression_enabled=False,
            backup_enabled=False
        )
        
        assert config.enabled is False
        assert config.time_interval_minutes == 30
        assert config.change_threshold == 20
        assert config.major_edit_threshold == 50
        assert config.max_snapshots_per_hour == 2
        assert config.max_snapshots_per_day == 12
        assert config.retention_days == 60
        assert config.cleanup_enabled is False
        assert config.compression_enabled is False
        assert config.backup_enabled is False


class TestChangeMetrics:
    """Test ChangeMetrics class"""
    
    def test_default_metrics(self):
        """Test default metrics values"""
        metrics = ChangeMetrics()
        
        assert metrics.object_count == 0
        assert metrics.edit_count == 0
        assert metrics.deletion_count == 0
        assert metrics.addition_count == 0
        assert metrics.modification_count == 0
        assert metrics.last_change_time is None
        assert metrics.change_velocity == 0.0
        assert metrics.complexity_score == 0.0
    
    def test_custom_metrics(self):
        """Test custom metrics values"""
        now = datetime.utcnow()
        metrics = ChangeMetrics(
            object_count=100,
            edit_count=25,
            deletion_count=5,
            addition_count=10,
            modification_count=10,
            last_change_time=now,
            change_velocity=2.5,
            complexity_score=15.0
        )
        
        assert metrics.object_count == 100
        assert metrics.edit_count == 25
        assert metrics.deletion_count == 5
        assert metrics.addition_count == 10
        assert metrics.modification_count == 10
        assert metrics.last_change_time == now
        assert metrics.change_velocity == 2.5
        assert metrics.complexity_score == 15.0


class TestChangeDetector:
    """Test ChangeDetector class"""
    
    def setup_method(self):
        """Setup test method"""
        self.detector = ChangeDetector()
        self.floor_id = "test_floor_001"
    
    def test_detect_changes_no_previous_data(self):
        """Test change detection with no previous data"""
        current_data = {
            "rooms": [{"object_id": "room_001", "name": "Test Room"}],
            "devices": [{"object_id": "device_001", "name": "Test Device"}]
        }
        
        metrics = self.detector.detect_changes(self.floor_id, current_data)
        
        assert metrics.addition_count == 2
        assert metrics.edit_count == 2
        assert metrics.deletion_count == 0
        assert metrics.modification_count == 0
        assert metrics.object_count == 2
        assert metrics.last_change_time is not None
    
    def test_detect_changes_with_additions(self):
        """Test change detection with additions"""
        previous_data = {
            "rooms": [{"object_id": "room_001", "name": "Test Room"}]
        }
        
        current_data = {
            "rooms": [{"object_id": "room_001", "name": "Test Room"}],
            "devices": [{"object_id": "device_001", "name": "Test Device"}]
        }
        
        metrics = self.detector.detect_changes(self.floor_id, current_data, previous_data)
        
        assert metrics.addition_count == 1
        assert metrics.edit_count == 1
        assert metrics.deletion_count == 0
        assert metrics.modification_count == 0
    
    def test_detect_changes_with_deletions(self):
        """Test change detection with deletions"""
        previous_data = {
            "rooms": [{"object_id": "room_001", "name": "Test Room"}],
            "devices": [{"object_id": "device_001", "name": "Test Device"}]
        }
        
        current_data = {
            "rooms": [{"object_id": "room_001", "name": "Test Room"}]
        }
        
        metrics = self.detector.detect_changes(self.floor_id, current_data, previous_data)
        
        assert metrics.addition_count == 0
        assert metrics.edit_count == 1
        assert metrics.deletion_count == 1
        assert metrics.modification_count == 0
    
    def test_detect_changes_with_modifications(self):
        """Test change detection with modifications"""
        previous_data = {
            "rooms": [{"object_id": "room_001", "name": "Old Room Name"}]
        }
        
        current_data = {
            "rooms": [{"object_id": "room_001", "name": "New Room Name"}]
        }
        
        metrics = self.detector.detect_changes(self.floor_id, current_data, previous_data)
        
        assert metrics.addition_count == 0
        assert metrics.edit_count == 1
        assert metrics.deletion_count == 0
        assert metrics.modification_count == 1
    
    def test_count_objects(self):
        """Test object counting"""
        data = {
            "rooms": [{"object_id": "room_001"}],
            "devices": [{"object_id": "device_001"}, {"object_id": "device_002"}],
            "walls": [{"object_id": "wall_001"}],
            "labels": [],
            "zones": [{"object_id": "zone_001"}]
        }
        
        count = self.detector._count_objects(data)
        assert count == 5
    
    def test_calculate_complexity_score(self):
        """Test complexity score calculation"""
        data = {
            "rooms": [{"object_id": "room_001"}],
            "devices": [{"object_id": "device_001", "upstream": ["panel_001"]}],
            "panels": [{"object_id": "panel_001"}]
        }
        
        score = self.detector._calculate_complexity_score(data)
        assert score > 0  # Should have some complexity


class TestIntelligentSnapshotScheduler:
    """Test IntelligentSnapshotScheduler class"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = SnapshotConfig()
        self.scheduler = IntelligentSnapshotScheduler(self.config)
        self.floor_id = "test_floor_001"
    
    def test_should_create_snapshot_time_based(self):
        """Test time-based snapshot creation"""
        change_metrics = ChangeMetrics(edit_count=5)
        
        should_create, priority, reason = self.scheduler.should_create_snapshot(
            self.floor_id, change_metrics, SnapshotTrigger.TIME_BASED
        )
        
        # Should create first snapshot
        assert should_create is True
        assert priority == SnapshotPriority.NORMAL
        assert "First snapshot" in reason
    
    def test_should_create_snapshot_change_threshold(self):
        """Test change threshold snapshot creation"""
        change_metrics = ChangeMetrics(edit_count=15)  # Above threshold
        
        should_create, priority, reason = self.scheduler.should_create_snapshot(
            self.floor_id, change_metrics, SnapshotTrigger.CHANGE_THRESHOLD
        )
        
        assert should_create is True
        assert "Change threshold met" in reason
    
    def test_should_create_snapshot_major_edit(self):
        """Test major edit snapshot creation"""
        change_metrics = ChangeMetrics(edit_count=30)  # Above major edit threshold
        
        should_create, priority, reason = self.scheduler.should_create_snapshot(
            self.floor_id, change_metrics, SnapshotTrigger.MAJOR_EDIT
        )
        
        assert should_create is True
        assert priority == SnapshotPriority.HIGH
        assert "Major edit detected" in reason
    
    def test_should_create_snapshot_manual(self):
        """Test manual snapshot creation"""
        change_metrics = ChangeMetrics(edit_count=0)
        
        should_create, priority, reason = self.scheduler.should_create_snapshot(
            self.floor_id, change_metrics, SnapshotTrigger.MANUAL
        )
        
        assert should_create is True
        assert priority == SnapshotPriority.HIGH
    
    def test_rate_limits_hourly(self):
        """Test hourly rate limiting"""
        # Add snapshots to exceed hourly limit
        for i in range(self.config.max_snapshots_per_hour + 1):
            self.scheduler.record_snapshot(self.floor_id, datetime.utcnow())
        
        change_metrics = ChangeMetrics(edit_count=10)
        should_create, _, reason = self.scheduler.should_create_snapshot(
            self.floor_id, change_metrics, SnapshotTrigger.CHANGE_THRESHOLD
        )
        
        assert should_create is False
        assert "Rate limit exceeded" in reason
    
    def test_calculate_priority(self):
        """Test priority calculation"""
        change_metrics = ChangeMetrics(edit_count=50)  # High change count
        
        priority = self.scheduler._calculate_priority(change_metrics)
        assert priority == SnapshotPriority.CRITICAL


class TestSnapshotCleanupManager:
    """Test SnapshotCleanupManager class"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = SnapshotConfig(retention_days=7)
        self.manager = SnapshotCleanupManager(self.config)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots(self):
        """Test cleanup of old snapshots"""
        # Create test snapshots
        now = datetime.utcnow()
        old_date = now - timedelta(days=10)  # Older than retention period
        recent_date = now - timedelta(days=3)  # Within retention period
        
        snapshots = [
            {
                "id": 1,
                "created_at": old_date.isoformat(),
                "is_auto_save": True
            },
            {
                "id": 2,
                "created_at": recent_date.isoformat(),
                "is_auto_save": True
            },
            {
                "id": 3,
                "created_at": old_date.isoformat(),
                "is_auto_save": False  # Manual snapshot
            }
        ]
        
        cleaned_snapshots = await self.manager.cleanup_old_snapshots("test_floor", snapshots)
        
        # Should keep recent auto-snapshot and manual snapshot
        assert len(cleaned_snapshots) == 2
        assert cleaned_snapshots[0]["id"] == 2  # Recent auto-snapshot
        assert cleaned_snapshots[1]["id"] == 3  # Manual snapshot
    
    def test_get_cleanup_stats(self):
        """Test cleanup statistics"""
        stats = self.manager.get_cleanup_stats()
        
        assert "total_cleanups" in stats
        assert "total_removed" in stats
        assert stats["total_cleanups"] == 0
        assert stats["total_removed"] == 0


class TestAutoSnapshotService:
    """Test AutoSnapshotService class"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = SnapshotConfig()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.service = AutoSnapshotService(self.config, self.temp_db.name)
    
    def teardown_method(self):
        """Teardown test method"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization"""
        assert self.service.config == self.config
        assert self.service.scheduler is not None
        assert self.service.change_detector is not None
        assert self.service.cleanup_manager is not None
        assert self.service.running is False
    
    @pytest.mark.asyncio
    async def test_service_start_stop(self):
        """Test service start and stop"""
        await self.service.start()
        assert self.service.running is True
        
        await self.service.stop()
        assert self.service.running is False
    
    @pytest.mark.asyncio
    async def test_track_changes_no_snapshot(self):
        """Test change tracking without creating snapshot"""
        current_data = {"rooms": [{"object_id": "room_001"}]}
        
        result = await self.service.track_changes("test_floor", current_data)
        
        # Should not create snapshot for small changes
        assert result is None
    
    @pytest.mark.asyncio
    async def test_track_changes_with_snapshot(self):
        """Test change tracking with snapshot creation"""
        # Create large change to trigger snapshot
        current_data = {
            "rooms": [{"object_id": f"room_{i}"} for i in range(20)]
        }
        
        result = await self.service.track_changes("test_floor", current_data)
        
        # Should create snapshot for large changes
        assert result is not None
        assert result["floor_id"] == "test_floor"
        assert result["is_auto_save"] is True
    
    @pytest.mark.asyncio
    async def test_create_manual_snapshot(self):
        """Test manual snapshot creation"""
        current_data = {"rooms": [{"object_id": "room_001"}]}
        
        # Mock the _get_floor_data method
        with patch.object(self.service, '_get_floor_data', return_value=current_data):
            snapshot = await self.service._create_snapshot(
                floor_id="test_floor",
                data=current_data,
                change_metrics=ChangeMetrics(),
                trigger=SnapshotTrigger.MANUAL,
                priority=SnapshotPriority.NORMAL,
                reason="Test manual snapshot",
                user_id="test_user"
            )
        
        assert snapshot is not None
        assert snapshot["floor_id"] == "test_floor"
        assert snapshot["trigger"] == "manual"
        assert snapshot["is_auto_save"] is False
    
    def test_determine_trigger(self):
        """Test trigger determination"""
        # Test major edit trigger
        metrics = ChangeMetrics(edit_count=30)
        trigger = self.service._determine_trigger(metrics)
        assert trigger == SnapshotTrigger.MAJOR_EDIT
        
        # Test change threshold trigger
        metrics = ChangeMetrics(edit_count=15)
        trigger = self.service._determine_trigger(metrics)
        assert trigger == SnapshotTrigger.CHANGE_THRESHOLD
        
        # Test time-based trigger
        metrics = ChangeMetrics(edit_count=5)
        trigger = self.service._determine_trigger(metrics)
        assert trigger == SnapshotTrigger.TIME_BASED
    
    def test_generate_description(self):
        """Test description generation"""
        metrics = ChangeMetrics(
            addition_count=5,
            modification_count=3,
            deletion_count=1
        )
        
        description = self.service._generate_description(
            SnapshotTrigger.CHANGE_THRESHOLD,
            metrics,
            "Test reason"
        )
        
        assert "Auto-snapshot" in description
        assert "5 added" in description
        assert "3 modified" in description
        assert "1 deleted" in description
    
    def test_generate_tags(self):
        """Test tag generation"""
        metrics = ChangeMetrics(
            addition_count=5,
            modification_count=3,
            deletion_count=1
        )
        
        tags = self.service._generate_tags(
            SnapshotTrigger.CHANGE_THRESHOLD,
            SnapshotPriority.HIGH,
            metrics
        )
        
        assert "change_threshold" in tags
        assert "high" in tags
        assert "auto-snapshot" in tags
        assert "additions" in tags
        assert "modifications" in tags
        assert "deletions" in tags
    
    def test_add_remove_callback(self):
        """Test callback management"""
        callback = Mock()
        
        self.service.add_snapshot_callback(callback)
        assert callback in self.service.snapshot_callbacks
        
        self.service.remove_snapshot_callback(callback)
        assert callback not in self.service.snapshot_callbacks
    
    def test_get_service_stats(self):
        """Test service statistics"""
        stats = self.service.get_service_stats()
        
        assert "active_floors" in stats
        assert "running" in stats
        assert "config" in stats
        assert "cleanup_stats" in stats
        assert "scheduler_stats" in stats


class TestAutoSnapshotIntegration:
    """Integration tests for auto-snapshot functionality"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = SnapshotConfig(
            time_interval_minutes=1,  # Short interval for testing
            change_threshold=5,
            max_snapshots_per_hour=10
        )
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.service = AutoSnapshotService(self.config, self.temp_db.name)
    
    def teardown_method(self):
        """Teardown test method"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete auto-snapshot workflow"""
        # Start service
        await self.service.start()
        
        # Track changes that should trigger snapshot
        current_data = {
            "rooms": [{"object_id": f"room_{i}"} for i in range(10)]
        }
        
        result = await self.service.track_changes("test_floor", current_data)
        
        # Should create snapshot
        assert result is not None
        assert result["floor_id"] == "test_floor"
        
        # Check that snapshot was recorded
        assert len(self.service.scheduler.snapshot_history["test_floor"]) == 1
        
        # Stop service
        await self.service.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_floors(self):
        """Test auto-snapshot with multiple floors"""
        await self.service.start()
        
        # Add multiple floors
        floors = ["floor_1", "floor_2", "floor_3"]
        
        for floor_id in floors:
            current_data = {
                "rooms": [{"object_id": f"room_{floor_id}_{i}"} for i in range(8)]
            }
            
            result = await self.service.track_changes(floor_id, current_data)
            assert result is not None
        
        # Check that all floors have snapshots
        for floor_id in floors:
            assert len(self.service.scheduler.snapshot_history[floor_id]) == 1
        
        await self.service.stop()


class TestFactoryFunction:
    """Test factory function"""
    
    def test_create_auto_snapshot_service_default(self):
        """Test creating service with default config"""
        service = create_auto_snapshot_service()
        
        assert isinstance(service, AutoSnapshotService)
        assert service.config.enabled is True
        assert service.config.time_interval_minutes == 15
    
    def test_create_auto_snapshot_service_custom(self):
        """Test creating service with custom config"""
        config = SnapshotConfig(
            enabled=False,
            time_interval_minutes=30,
            change_threshold=20
        )
        
        service = create_auto_snapshot_service(config)
        
        assert isinstance(service, AutoSnapshotService)
        assert service.config.enabled is False
        assert service.config.time_interval_minutes == 30
        assert service.config.change_threshold == 20


# Performance tests
class TestAutoSnapshotPerformance:
    """Performance tests for auto-snapshot service"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = SnapshotConfig()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.service = AutoSnapshotService(self.config, self.temp_db.name)
    
    def teardown_method(self):
        """Teardown test method"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @pytest.mark.asyncio
    async def test_large_data_performance(self):
        """Test performance with large data sets"""
        # Create large data set
        current_data = {
            "rooms": [{"object_id": f"room_{i}", "name": f"Room {i}"} for i in range(1000)],
            "devices": [{"object_id": f"device_{i}", "name": f"Device {i}"} for i in range(500)],
            "walls": [{"object_id": f"wall_{i}", "name": f"Wall {i}"} for i in range(200)]
        }
        
        start_time = datetime.utcnow()
        
        # Track changes
        result = await self.service.track_changes("test_floor", current_data)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (less than 5 seconds)
        assert duration < 5.0
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_rapid_changes_performance(self):
        """Test performance with rapid changes"""
        await self.service.start()
        
        start_time = datetime.utcnow()
        
        # Make many rapid changes
        for i in range(50):
            current_data = {
                "rooms": [{"object_id": f"room_{i}_{j}"} for j in range(5)]
            }
            
            await self.service.track_changes("test_floor", current_data)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should handle rapid changes efficiently
        assert duration < 10.0
        
        await self.service.stop()


if __name__ == "__main__":
    pytest.main([__file__]) 