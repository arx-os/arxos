"""
Auto-Snapshot Service for SVGX Engine

This service provides intelligent snapshotting capabilities including:
- Auto-snapshot after major changes
- Time-based auto-snapshot
- Change threshold detection
- Snapshot cleanup policies
- Intelligent snapshot scheduling
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from collections import defaultdict, deque
import hashlib
import sqlite3
from pathlib import Path

from structlog import get_logger

logger = get_logger()


class SnapshotTrigger(Enum):
    """Types of snapshot triggers"""
    TIME_BASED = "time_based"
    CHANGE_THRESHOLD = "change_threshold"
    MAJOR_EDIT = "major_edit"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SYSTEM_EVENT = "system_event"


class SnapshotType(Enum):
    """Types of snapshots"""
    AUTO = "auto"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SYSTEM = "system"


class SnapshotPriority(Enum):
    """Snapshot priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChangeMetrics:
    """Metrics for tracking changes"""
    object_count: int = 0
    edit_count: int = 0
    deletion_count: int = 0
    addition_count: int = 0
    modification_count: int = 0
    last_change_time: Optional[datetime] = None
    change_velocity: float = 0.0  # Changes per minute
    complexity_score: float = 0.0  # Based on object types and relationships


@dataclass
class SnapshotConfig:
    """Configuration for auto-snapshot behavior"""
    enabled: bool = True
    time_interval_minutes: int = 15
    change_threshold: int = 10
    major_edit_threshold: int = 25
    max_snapshots_per_hour: int = 4
    max_snapshots_per_day: int = 24
    retention_days: int = 30
    cleanup_enabled: bool = True
    compression_enabled: bool = True
    backup_enabled: bool = True
    priority_thresholds: Dict[SnapshotPriority, int] = field(default_factory=lambda: {
        SnapshotPriority.LOW: 5,
        SnapshotPriority.NORMAL: 10,
        SnapshotPriority.HIGH: 20,
        SnapshotPriority.CRITICAL: 50
    })


@dataclass
class SnapshotMetadata:
    """Metadata for a snapshot"""
    trigger: SnapshotTrigger
    priority: SnapshotPriority
    change_metrics: ChangeMetrics
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    system_events: List[str] = field(default_factory=list)


class IntelligentSnapshotScheduler:
    """Intelligent scheduler for determining when to create snapshots"""
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.floor_activity: Dict[str, Dict] = defaultdict(dict)
        self.snapshot_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.change_patterns: Dict[str, Dict] = defaultdict(dict)
        
    def should_create_snapshot(self, floor_id: str, change_metrics: ChangeMetrics, 
                             trigger: SnapshotTrigger) -> tuple[bool, SnapshotPriority, str]:
        """Determine if a snapshot should be created"""
        
        # Check basic limits
        if not self._check_rate_limits(floor_id):
            return False, SnapshotPriority.LOW, "Rate limit exceeded"
        
        # Check time-based trigger
        if trigger == SnapshotTrigger.TIME_BASED:
            return self._check_time_based_trigger(floor_id, change_metrics)
        
        # Check change threshold trigger
        elif trigger == SnapshotTrigger.CHANGE_THRESHOLD:
            return self._check_change_threshold_trigger(floor_id, change_metrics)
        
        # Check major edit trigger
        elif trigger == SnapshotTrigger.MAJOR_EDIT:
            return self._check_major_edit_trigger(floor_id, change_metrics)
        
        # Manual and system events always create snapshots
        elif trigger in [SnapshotTrigger.MANUAL, SnapshotTrigger.SYSTEM_EVENT]:
            return True, SnapshotPriority.HIGH, f"{trigger.value} trigger"
        
        return False, SnapshotPriority.LOW, "No trigger conditions met"
    
    def _check_rate_limits(self, floor_id: str) -> bool:
        """Check if rate limits are exceeded"""
        now = datetime.utcnow()
        history = self.snapshot_history[floor_id]
        
        # Check hourly limit
        hour_ago = now - timedelta(hours=1)
        hourly_count = sum(1 for timestamp in history if timestamp > hour_ago)
        if hourly_count >= self.config.max_snapshots_per_hour:
            return False
        
        # Check daily limit
        day_ago = now - timedelta(days=1)
        daily_count = sum(1 for timestamp in history if timestamp > day_ago)
        if daily_count >= self.config.max_snapshots_per_day:
            return False
        
        return True
    
    def _check_time_based_trigger(self, floor_id: str, change_metrics: ChangeMetrics) -> tuple[bool, SnapshotPriority, str]:
        """Check if time-based snapshot should be created"""
        now = datetime.utcnow()
        last_snapshot = self._get_last_snapshot_time(floor_id)
        
        if not last_snapshot:
            return True, SnapshotPriority.NORMAL, "First snapshot"
        
        time_since_last = now - last_snapshot
        if time_since_last >= timedelta(minutes=self.config.time_interval_minutes):
            if change_metrics.edit_count > 0:
                priority = self._calculate_priority(change_metrics)
                return True, priority, f"Time-based trigger ({time_since_last.total_seconds() / 60:.1f} minutes)"
        
        return False, SnapshotPriority.LOW, "Time threshold not met"
    
    def _check_change_threshold_trigger(self, floor_id: str, change_metrics: ChangeMetrics) -> tuple[bool, SnapshotPriority, str]:
        """Check if change threshold snapshot should be created"""
        total_changes = (change_metrics.addition_count + 
                        change_metrics.modification_count + 
                        change_metrics.deletion_count)
        
        if total_changes >= self.config.change_threshold:
            priority = self._calculate_priority(change_metrics)
            return True, priority, f"Change threshold met ({total_changes} changes)"
        
        return False, SnapshotPriority.LOW, f"Insufficient changes ({total_changes})"
    
    def _check_major_edit_trigger(self, floor_id: str, change_metrics: ChangeMetrics) -> tuple[bool, SnapshotPriority, str]:
        """Check if major edit snapshot should be created"""
        if change_metrics.edit_count >= self.config.major_edit_threshold:
            return True, SnapshotPriority.HIGH, f"Major edit detected ({change_metrics.edit_count} edits)"
        
        return False, SnapshotPriority.LOW, f"Not a major edit ({change_metrics.edit_count} edits)"
    
    def _calculate_priority(self, change_metrics: ChangeMetrics) -> SnapshotPriority:
        """Calculate snapshot priority based on change metrics"""
        total_changes = (change_metrics.addition_count + 
                        change_metrics.modification_count + 
                        change_metrics.deletion_count)
        
        if total_changes >= self.config.priority_thresholds[SnapshotPriority.CRITICAL]:
            return SnapshotPriority.CRITICAL
        elif total_changes >= self.config.priority_thresholds[SnapshotPriority.HIGH]:
            return SnapshotPriority.HIGH
        elif total_changes >= self.config.priority_thresholds[SnapshotPriority.NORMAL]:
            return SnapshotPriority.NORMAL
        else:
            return SnapshotPriority.LOW
    
    def _get_last_snapshot_time(self, floor_id: str) -> Optional[datetime]:
        """Get the timestamp of the last snapshot for a floor"""
        history = self.snapshot_history[floor_id]
        return max(history) if history else None
    
    def record_snapshot(self, floor_id: str, timestamp: datetime):
        """Record a snapshot creation"""
        self.snapshot_history[floor_id].append(timestamp)
    
    def update_activity(self, floor_id: str, activity_data: Dict[str, Any]):
        """Update floor activity data"""
        self.floor_activity[floor_id].update(activity_data)


class ChangeDetector:
    """Detects changes in floor data"""
    
    def __init__(self):
        self.change_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.last_data: Dict[str, Dict] = {}
    
    def detect_changes(self, floor_id: str, current_data: Dict[str, Any], 
                      previous_data: Optional[Dict[str, Any]] = None) -> ChangeMetrics:
        """Detect changes between current and previous data"""
        
        if previous_data is None:
            previous_data = self.last_data.get(floor_id, {})
        
        metrics = ChangeMetrics()
        
        # Count objects
        current_objects = self._count_objects(current_data)
        previous_objects = self._count_objects(previous_data)
        metrics.object_count = current_objects
        
        # Detect changes
        if previous_data:
            changes = self._compare_data(current_data, previous_data)
            
            metrics.addition_count = len(changes.get('added', []))
            metrics.modification_count = len(changes.get('modified', []))
            metrics.deletion_count = len(changes.get('deleted', []))
            metrics.edit_count = metrics.addition_count + metrics.modification_count + metrics.deletion_count
        
        # Calculate change velocity
        metrics.change_velocity = self._calculate_change_velocity(floor_id, metrics.edit_count)
        
        # Calculate complexity score
        metrics.complexity_score = self._calculate_complexity_score(current_data)
        
        # Update last change time
        if metrics.edit_count > 0:
            metrics.last_change_time = datetime.utcnow()
        
        # Store current data for next comparison
        self.last_data[floor_id] = current_data.copy()
        
        # Record change in history
        self.change_history[floor_id].append({
            'timestamp': datetime.utcnow(),
            'edit_count': metrics.edit_count,
            'object_count': metrics.object_count
        })
        
        return metrics
    
    def _count_objects(self, data: Dict[str, Any]) -> int:
        """Count objects in data structure"""
        if isinstance(data, dict):
            return sum(self._count_objects(value) for value in data.values())
        elif isinstance(data, list):
            return sum(self._count_objects(item) for item in data)
        else:
            return 1
    
    def _compare_data(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, List]:
        """Compare current and previous data to detect changes"""
        changes = {
            'added': [],
            'modified': [],
            'deleted': []
        }
        
        # Find added and modified items
        for key, value in current.items():
            if key not in previous:
                changes['added'].append(key)
            elif self._objects_different(value, previous[key]):
                changes['modified'].append(key)
        
        # Find deleted items
        for key in previous:
            if key not in current:
                changes['deleted'].append(key)
        
        return changes
    
    def _objects_different(self, obj1: Dict, obj2: Dict) -> bool:
        """Check if two objects are different"""
        return obj1 != obj2
    
    def _calculate_change_velocity(self, floor_id: str, current_changes: int) -> float:
        """Calculate change velocity (changes per minute)"""
        history = self.change_history[floor_id]
        if len(history) < 2:
            return 0.0
        
        # Calculate velocity over last 10 minutes
        now = datetime.utcnow()
        recent_changes = [
            entry for entry in history
            if (now - entry['timestamp']).total_seconds() <= 600  # 10 minutes
        ]
        
        if not recent_changes:
            return 0.0
        
        total_changes = sum(entry['edit_count'] for entry in recent_changes)
        time_span = (now - recent_changes[0]['timestamp']).total_seconds() / 60  # minutes
        
        return total_changes / time_span if time_span > 0 else 0.0
    
    def _calculate_complexity_score(self, data: Dict[str, Any]) -> float:
        """Calculate complexity score based on data structure"""
        score = 0.0
        
        def traverse(obj, depth=0):
            nonlocal score
            if isinstance(obj, dict):
                score += len(obj) * (1 + depth * 0.1)
                for value in obj.values():
                    traverse(value, depth + 1)
            elif isinstance(obj, list):
                score += len(obj) * (1 + depth * 0.1)
                for item in obj:
                    traverse(item, depth + 1)
            else:
                score += 1
        
        traverse(data)
        return score


class SnapshotCleanupManager:
    """Manages cleanup of old snapshots"""
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.cleanup_stats = {'snapshots_removed': 0, 'storage_freed': 0}
    
    async def cleanup_old_snapshots(self, floor_id: str, snapshots: List[Dict]) -> List[Dict]:
        """Remove old snapshots based on retention policy"""
        if not self.config.cleanup_enabled:
            return snapshots
        
        now = datetime.utcnow()
        retention_cutoff = now - timedelta(days=self.config.retention_days)
        
        # Sort snapshots by timestamp
        sorted_snapshots = sorted(snapshots, key=lambda s: s.get('timestamp', now))
        
        # Keep snapshots within retention period
        kept_snapshots = []
        removed_count = 0
        
        for snapshot in sorted_snapshots:
            snapshot_time = snapshot.get('timestamp')
            if snapshot_time and snapshot_time > retention_cutoff:
                kept_snapshots.append(snapshot)
            else:
                removed_count += 1
                # In a real implementation, you would delete the actual snapshot data
        
        self.cleanup_stats['snapshots_removed'] += removed_count
        
        logger.info(f"Cleaned up {removed_count} old snapshots for floor {floor_id}")
        return kept_snapshots
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        return self.cleanup_stats.copy()


class AutoSnapshotService:
    """Main auto-snapshot service"""
    
    def __init__(self, config: SnapshotConfig, db_path: str = "svgx_engine.db"):
        self.config = config
        self.db_path = db_path
        self.scheduler = IntelligentSnapshotScheduler(config)
        self.change_detector = ChangeDetector()
        self.cleanup_manager = SnapshotCleanupManager(config)
        self.active_floors: Set[str] = set()
        self.snapshot_callbacks: List[Callable] = []
        self.running = False
        
    async def start(self):
        """Start the auto-snapshot service"""
        if self.running:
            return
        
        self.running = True
        logger.info("Auto-snapshot service started")
        
        # Start background tasks
        asyncio.create_task(self._time_based_snapshot_loop())
        asyncio.create_task(self._cleanup_loop())
        
    async def stop(self):
        """Stop the auto-snapshot service"""
        self.running = False
        logger.info("Auto-snapshot service stopped")
        
    async def track_changes(self, floor_id: str, current_data: Dict[str, Any], 
                          previous_data: Optional[Dict[str, Any]] = None,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> Optional[Dict]:
        """Track changes and potentially create snapshots"""
        
        if not self.config.enabled:
            return None
        
        # Detect changes
        change_metrics = self.change_detector.detect_changes(floor_id, current_data, previous_data)
        
        # Determine trigger
        trigger = self._determine_trigger(change_metrics)
        
        # Check if snapshot should be created
        should_create, priority, reason = self.scheduler.should_create_snapshot(
            floor_id, change_metrics, trigger
        )
        
        if should_create:
            # Create snapshot
            snapshot = await self._create_snapshot(
                floor_id, current_data, change_metrics, trigger, priority, reason,
                user_id, session_id
            )
            
            # Record snapshot
            self.scheduler.record_snapshot(floor_id, snapshot['timestamp'])
            
            # Notify callbacks
            for callback in self.snapshot_callbacks:
                try:
                    callback(snapshot)
                except Exception as e:
                    logger.error(f"Snapshot callback error: {e}")
            
            return snapshot
        
        return None
    
    def _determine_trigger(self, change_metrics: ChangeMetrics) -> SnapshotTrigger:
        """Determine the trigger type based on change metrics"""
        if change_metrics.edit_count >= self.config.major_edit_threshold:
            return SnapshotTrigger.MAJOR_EDIT
        elif change_metrics.edit_count >= self.config.change_threshold:
            return SnapshotTrigger.CHANGE_THRESHOLD
        else:
            return SnapshotTrigger.TIME_BASED
    
    async def _create_snapshot(self, floor_id: str, data: Dict[str, Any], 
                             change_metrics: ChangeMetrics, trigger: SnapshotTrigger,
                             priority: SnapshotPriority, reason: str,
                             user_id: Optional[str] = None,
                             session_id: Optional[str] = None) -> Dict:
        """Create a new snapshot"""
        
        timestamp = datetime.utcnow()
        version = await self._get_next_version_number(floor_id)
        
        # Generate snapshot ID
        snapshot_id = f"{floor_id}_v{version}_{int(timestamp.timestamp())}"
        
        # Create snapshot metadata
        metadata = SnapshotMetadata(
            trigger=trigger,
            priority=priority,
            change_metrics=change_metrics,
            user_id=user_id,
            session_id=session_id,
            description=self._generate_description(trigger, change_metrics, reason),
            tags=self._generate_tags(trigger, priority, change_metrics),
            system_events=[]
        )
        
        # Create snapshot
        snapshot = {
            'snapshot_id': snapshot_id,
            'floor_id': floor_id,
            'version': version,
            'timestamp': timestamp,
            'data': data,
            'metadata': metadata,
            'trigger': trigger.value,
            'priority': priority.value,
            'reason': reason,
            'user_id': user_id,
            'session_id': session_id,
            'compressed': self.config.compression_enabled,
            'backed_up': self.config.backup_enabled
        }
        
        # Store snapshot
        await self._store_snapshot(snapshot)
        
        logger.info(f"Created snapshot {snapshot_id} for floor {floor_id} ({reason})")
        return snapshot
    
    def _generate_description(self, trigger: SnapshotTrigger, 
                           change_metrics: ChangeMetrics, reason: str) -> str:
        """Generate snapshot description"""
        descriptions = {
            SnapshotTrigger.TIME_BASED: f"Time-based auto-snapshot: {reason}",
            SnapshotTrigger.CHANGE_THRESHOLD: f"Change threshold snapshot: {reason}",
            SnapshotTrigger.MAJOR_EDIT: f"Major edit snapshot: {reason}",
            SnapshotTrigger.MANUAL: f"Manual snapshot: {reason}",
            SnapshotTrigger.SYSTEM_EVENT: f"System event snapshot: {reason}",
            SnapshotTrigger.SCHEDULED: f"Scheduled snapshot: {reason}"
        }
        
        return descriptions.get(trigger, f"Auto-snapshot: {reason}")
    
    def _generate_tags(self, trigger: SnapshotTrigger, priority: SnapshotPriority,
                      change_metrics: ChangeMetrics) -> List[str]:
        """Generate snapshot tags"""
        tags = [
            f"trigger:{trigger.value}",
            f"priority:{priority.value}",
            f"changes:{change_metrics.edit_count}",
            f"objects:{change_metrics.object_count}"
        ]
        
        if change_metrics.addition_count > 0:
            tags.append(f"additions:{change_metrics.addition_count}")
        if change_metrics.modification_count > 0:
            tags.append(f"modifications:{change_metrics.modification_count}")
        if change_metrics.deletion_count > 0:
            tags.append(f"deletions:{change_metrics.deletion_count}")
        
        return tags
    
    async def _store_snapshot(self, snapshot: Dict):
        """Store snapshot in database"""
        # In a real implementation, this would store to database
        # For now, we'll just log the snapshot
        logger.debug(f"Stored snapshot: {snapshot['snapshot_id']}")
    
    async def _get_next_version_number(self, floor_id: str) -> int:
        """Get next version number for floor"""
        # In a real implementation, this would query the database
        # For now, return a simple increment
        return 1
    
    async def _time_based_snapshot_loop(self):
        """Background loop for time-based snapshots"""
        while self.running:
            try:
                for floor_id in self.active_floors:
                    floor_data = await self._get_floor_data(floor_id)
                    if floor_data:
                        await self.track_changes(floor_id, floor_data)
                
                await asyncio.sleep(self.config.time_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Time-based snapshot loop error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Background loop for cleanup"""
        while self.running:
            try:
                floors = await self._get_floors_with_snapshots()
                for floor_id in floors:
                    snapshots = await self._get_floor_snapshots(floor_id)
                    cleaned_snapshots = await self.cleanup_manager.cleanup_old_snapshots(floor_id, snapshots)
                    await self._update_floor_snapshots(floor_id, cleaned_snapshots)
                
                await asyncio.sleep(3600)  # Run cleanup every hour
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _get_floor_data(self, floor_id: str) -> Optional[Dict[str, Any]]:
        """Get current floor data"""
        # In a real implementation, this would query the database
        # For now, return None
        return None
    
    async def _get_floors_with_snapshots(self) -> List[str]:
        """Get list of floors that have snapshots"""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    async def _get_floor_snapshots(self, floor_id: str) -> List[Dict]:
        """Get snapshots for a floor"""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    async def _update_floor_snapshots(self, floor_id: str, snapshots: List[Dict]):
        """Update floor snapshots in database"""
        # In a real implementation, this would update the database
        # For now, just log
        logger.debug(f"Updated {len(snapshots)} snapshots for floor {floor_id}")
    
    def add_snapshot_callback(self, callback: Callable):
        """Add a callback to be called when snapshots are created"""
        self.snapshot_callbacks.append(callback)
    
    def remove_snapshot_callback(self, callback: Callable):
        """Remove a snapshot callback"""
        if callback in self.snapshot_callbacks:
            self.snapshot_callbacks.remove(callback)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'enabled': self.config.enabled,
            'active_floors': len(self.active_floors),
            'snapshot_callbacks': len(self.snapshot_callbacks),
            'cleanup_stats': self.cleanup_manager.get_cleanup_stats(),
            'running': self.running
        }


def create_auto_snapshot_service(config: Optional[SnapshotConfig] = None) -> AutoSnapshotService:
    """Factory function to create auto-snapshot service"""
    if config is None:
        config = SnapshotConfig()
    
    return AutoSnapshotService(config) 