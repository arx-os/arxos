"""
Auto-Snapshot Service for Arxos Platform

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

logger = logging.getLogger(__name__)


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


class SnapshotType(Enum):
    """Types of snapshots"""
    AUTO = "auto"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SYSTEM = "system"


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
        
        for priority, threshold in sorted(self.config.priority_thresholds.items(), 
                                        key=lambda x: x[1], reverse=True):
            if total_changes >= threshold:
                return priority
        
        return SnapshotPriority.LOW
    
    def _get_last_snapshot_time(self, floor_id: str) -> Optional[datetime]:
        """Get the timestamp of the last snapshot for a floor"""
        history = self.snapshot_history[floor_id]
        return history[-1] if history else None
    
    def record_snapshot(self, floor_id: str, timestamp: datetime):
        """Record a snapshot creation"""
        self.snapshot_history[floor_id].append(timestamp)
    
    def update_activity(self, floor_id: str, activity_data: Dict[str, Any]):
        """Update floor activity data"""
        self.floor_activity[floor_id].update(activity_data)


class ChangeDetector:
    """Detects and analyzes changes in floor data"""
    
    def __init__(self):
        self.change_history: Dict[str, List[Dict]] = defaultdict(list)
        self.object_states: Dict[str, Dict] = defaultdict(dict)
        
    def detect_changes(self, floor_id: str, current_data: Dict[str, Any], 
                      previous_data: Optional[Dict[str, Any]] = None) -> ChangeMetrics:
        """Detect changes between current and previous data"""
        metrics = ChangeMetrics()
        
        if not previous_data:
            # First snapshot - count all objects as additions
            metrics.addition_count = self._count_objects(current_data)
            metrics.last_change_time = datetime.utcnow()
            return metrics
        
        # Compare current and previous data
        changes = self._compare_data(current_data, previous_data)
        
        metrics.addition_count = len(changes.get('added', []))
        metrics.deletion_count = len(changes.get('removed', []))
        metrics.modification_count = len(changes.get('modified', []))
        metrics.edit_count = metrics.addition_count + metrics.deletion_count + metrics.modification_count
        metrics.object_count = self._count_objects(current_data)
        metrics.last_change_time = datetime.utcnow()
        
        # Calculate change velocity
        metrics.change_velocity = self._calculate_change_velocity(floor_id, metrics.edit_count)
        
        # Calculate complexity score
        metrics.complexity_score = self._calculate_complexity_score(current_data)
        
        # Store change history
        self.change_history[floor_id].append({
            'timestamp': datetime.utcnow(),
            'metrics': metrics,
            'changes': changes
        })
        
        return metrics
    
    def _count_objects(self, data: Dict[str, Any]) -> int:
        """Count total objects in the data"""
        count = 0
        for key in ['rooms', 'walls', 'devices', 'labels', 'zones', 'panels', 'connectors', 'routes', 'pins']:
            if key in data and isinstance(data[key], list):
                count += len(data[key])
        return count
    
    def _compare_data(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, List]:
        """Compare current and previous data to find changes"""
        changes = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        # Compare each object type
        for object_type in ['rooms', 'walls', 'devices', 'labels', 'zones', 'panels', 'connectors', 'routes', 'pins']:
            current_objects = current.get(object_type, [])
            previous_objects = previous.get(object_type, [])
            
            # Create lookup dictionaries
            current_lookup = {obj.get('object_id', obj.get('id')): obj for obj in current_objects}
            previous_lookup = {obj.get('object_id', obj.get('id')): obj for obj in previous_objects}
            
            # Find additions
            for obj_id, obj in current_lookup.items():
                if obj_id not in previous_lookup:
                    changes['added'].append({
                        'object_id': obj_id,
                        'object_type': object_type,
                        'data': obj
                    })
            
            # Find deletions
            for obj_id, obj in previous_lookup.items():
                if obj_id not in current_lookup:
                    changes['removed'].append({
                        'object_id': obj_id,
                        'object_type': object_type,
                        'data': obj
                    })
            
            # Find modifications
            for obj_id, current_obj in current_lookup.items():
                if obj_id in previous_lookup:
                    previous_obj = previous_lookup[obj_id]
                    if self._objects_different(current_obj, previous_obj):
                        changes['modified'].append({
                            'object_id': obj_id,
                            'object_type': object_type,
                            'previous': previous_obj,
                            'current': current_obj
                        })
        
        return changes
    
    def _objects_different(self, obj1: Dict, obj2: Dict) -> bool:
        """Check if two objects are different"""
        # Create a hash of the objects for comparison
        hash1 = hashlib.md5(json.dumps(obj1, sort_keys=True).encode()).hexdigest()
        hash2 = hashlib.md5(json.dumps(obj2, sort_keys=True).encode()).hexdigest()
        return hash1 != hash2
    
    def _calculate_change_velocity(self, floor_id: str, current_changes: int) -> float:
        """Calculate the rate of changes over time"""
        history = self.change_history[floor_id]
        if len(history) < 2:
            return 0.0
        
        # Look at last 10 changes
        recent_history = history[-10:]
        if len(recent_history) < 2:
            return 0.0
        
        first_time = recent_history[0]['timestamp']
        last_time = recent_history[-1]['timestamp']
        
        if (last_time - first_time).total_seconds() == 0:
            return 0.0
        
        total_changes = sum(entry['metrics'].edit_count for entry in recent_history)
        time_span_minutes = (last_time - first_time).total_seconds() / 60
        
        return total_changes / time_span_minutes if time_span_minutes > 0 else 0.0
    
    def _calculate_complexity_score(self, data: Dict[str, Any]) -> float:
        """Calculate complexity score based on object types and relationships"""
        score = 0.0
        
        # Base score for each object type
        type_weights = {
            'rooms': 1.0,
            'walls': 0.5,
            'devices': 2.0,
            'labels': 0.1,
            'zones': 1.5,
            'panels': 3.0,
            'connectors': 1.0,
            'routes': 2.5,
            'pins': 0.5
        }
        
        for object_type, weight in type_weights.items():
            objects = data.get(object_type, [])
            score += len(objects) * weight
        
        # Bonus for relationships
        relationship_count = 0
        for obj_type, objects in data.items():
            for obj in objects:
                if isinstance(obj, dict):
                    # Count relationship fields
                    for field in ['upstream', 'downstream', 'connected_to', 'room_id', 'panel_id']:
                        if field in obj and obj[field]:
                            relationship_count += 1
        
        score += relationship_count * 0.5
        
        return score


class SnapshotCleanupManager:
    """Manages cleanup of old snapshots based on policies"""
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.cleanup_history: List[Dict] = []
        
    async def cleanup_old_snapshots(self, floor_id: str, snapshots: List[Dict]) -> List[Dict]:
        """Clean up old snapshots based on retention policy"""
        if not self.config.cleanup_enabled:
            return snapshots
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
        
        # Separate snapshots by type
        manual_snapshots = [s for s in snapshots if not s.get('is_auto_save', False)]
        auto_snapshots = [s for s in snapshots if s.get('is_auto_save', False)]
        
        # Keep all manual snapshots
        snapshots_to_keep = manual_snapshots.copy()
        
        # Apply retention policy to auto-snapshots
        for snapshot in auto_snapshots:
            snapshot_date = datetime.fromisoformat(snapshot['created_at'].replace('Z', '+00:00'))
            if snapshot_date > cutoff_date:
                snapshots_to_keep.append(snapshot)
        
        # Sort by creation date (newest first)
        snapshots_to_keep.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Log cleanup operation
        removed_count = len(snapshots) - len(snapshots_to_keep)
        if removed_count > 0:
            cleanup_record = {
                'floor_id': floor_id,
                'timestamp': datetime.utcnow(),
                'removed_count': removed_count,
                'kept_count': len(snapshots_to_keep),
                'cutoff_date': cutoff_date.isoformat()
            }
            self.cleanup_history.append(cleanup_record)
            logger.info(f"Cleaned up {removed_count} old snapshots for floor {floor_id}")
        
        return snapshots_to_keep
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        if not self.cleanup_history:
            return {'total_cleanups': 0, 'total_removed': 0}
        
        total_cleanups = len(self.cleanup_history)
        total_removed = sum(record['removed_count'] for record in self.cleanup_history)
        
        return {
            'total_cleanups': total_cleanups,
            'total_removed': total_removed,
            'last_cleanup': self.cleanup_history[-1] if self.cleanup_history else None
        }


class AutoSnapshotService:
    """Main auto-snapshot service"""
    
    def __init__(self, config: SnapshotConfig, db_path: str = "arxos_dev.db"):
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
        """Track changes and potentially create a snapshot"""
        
        # Detect changes
        change_metrics = self.change_detector.detect_changes(floor_id, current_data, previous_data)
        
        # Update activity
        self.scheduler.update_activity(floor_id, {
            'last_activity': datetime.utcnow(),
            'user_id': user_id,
            'session_id': session_id,
            'change_metrics': change_metrics
        })
        
        # Check if snapshot should be created
        trigger = self._determine_trigger(change_metrics)
        should_create, priority, reason = self.scheduler.should_create_snapshot(
            floor_id, change_metrics, trigger
        )
        
        if should_create:
            return await self._create_snapshot(
                floor_id, current_data, change_metrics, trigger, priority, reason,
                user_id, session_id
            )
        
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
        """Create a snapshot"""
        
        # Generate description
        description = self._generate_description(trigger, change_metrics, reason)
        
        # Create metadata
        metadata = SnapshotMetadata(
            trigger=trigger,
            priority=priority,
            change_metrics=change_metrics,
            user_id=user_id,
            session_id=session_id,
            description=description,
            tags=self._generate_tags(trigger, priority, change_metrics),
            system_events=[]
        )
        
        # Create snapshot record
        snapshot = {
            'floor_id': floor_id,
            'data': data,
            'metadata': metadata,
            'created_at': datetime.utcnow().isoformat(),
            'is_auto_save': trigger != SnapshotTrigger.MANUAL,
            'priority': priority.value,
            'trigger': trigger.value,
            'description': description,
            'tags': metadata.tags
        }
        
        # Store snapshot
        await self._store_snapshot(snapshot)
        
        # Record in scheduler
        self.scheduler.record_snapshot(floor_id, datetime.utcnow())
        
        # Notify callbacks
        for callback in self.snapshot_callbacks:
            try:
                await callback(snapshot)
            except Exception as e:
                logger.error(f"Error in snapshot callback: {e}")
        
        logger.info(f"Created auto-snapshot for floor {floor_id}: {description}")
        return snapshot
    
    def _generate_description(self, trigger: SnapshotTrigger, 
                            change_metrics: ChangeMetrics, reason: str) -> str:
        """Generate a description for the snapshot"""
        if trigger == SnapshotTrigger.MANUAL:
            return "Manual snapshot"
        
        change_summary = []
        if change_metrics.addition_count > 0:
            change_summary.append(f"{change_metrics.addition_count} added")
        if change_metrics.modification_count > 0:
            change_summary.append(f"{change_metrics.modification_count} modified")
        if change_metrics.deletion_count > 0:
            change_summary.append(f"{change_metrics.deletion_count} deleted")
        
        change_text = ", ".join(change_summary) if change_summary else "no changes"
        
        return f"Auto-snapshot ({trigger.value}): {change_text} - {reason}"
    
    def _generate_tags(self, trigger: SnapshotTrigger, priority: SnapshotPriority,
                      change_metrics: ChangeMetrics) -> List[str]:
        """Generate tags for the snapshot"""
        tags = [trigger.value, priority.value, 'auto-snapshot']
        
        if change_metrics.addition_count > 0:
            tags.append('additions')
        if change_metrics.modification_count > 0:
            tags.append('modifications')
        if change_metrics.deletion_count > 0:
            tags.append('deletions')
        
        if change_metrics.complexity_score > 10:
            tags.append('complex')
        
        return tags
    
    async def _store_snapshot(self, snapshot: Dict):
        """Store snapshot in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert into drawing_versions table
            cursor.execute("""
                INSERT INTO drawing_versions (
                    floor_id, svg, version_number, user_id, action_type,
                    description, tags, metadata, is_auto_save, file_size,
                    checksum, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot['floor_id'],
                json.dumps(snapshot['data']),
                self._get_next_version_number(snapshot['floor_id']),
                snapshot['metadata'].user_id or 1,
                'snapshot',
                snapshot['description'],
                json.dumps(snapshot['tags']),
                json.dumps(snapshot['metadata'].__dict__),
                snapshot['is_auto_save'],
                len(json.dumps(snapshot['data'])),
                hashlib.sha256(json.dumps(snapshot['data']).encode()).hexdigest(),
                snapshot['created_at']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing snapshot: {e}")
            raise
    
    def _get_next_version_number(self, floor_id: str) -> int:
        """Get the next version number for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(version_number) FROM drawing_versions 
                WHERE floor_id = ?
            """, (floor_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return (result[0] or 0) + 1
            
        except Exception as e:
            logger.error(f"Error getting next version number: {e}")
            return 1
    
    async def _time_based_snapshot_loop(self):
        """Background loop for time-based snapshots"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for floor_id in self.active_floors:
                    # Get current floor data
                    current_data = await self._get_floor_data(floor_id)
                    if current_data:
                        await self.track_changes(floor_id, current_data)
                        
            except Exception as e:
                logger.error(f"Error in time-based snapshot loop: {e}")
    
    async def _cleanup_loop(self):
        """Background loop for cleanup operations"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour
                
                # Get all floors with snapshots
                floors = await self._get_floors_with_snapshots()
                
                for floor_id in floors:
                    snapshots = await self._get_floor_snapshots(floor_id)
                    cleaned_snapshots = await self.cleanup_manager.cleanup_old_snapshots(
                        floor_id, snapshots
                    )
                    
                    # Update database with cleaned snapshots
                    await self._update_floor_snapshots(floor_id, cleaned_snapshots)
                    
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _get_floor_data(self, floor_id: str) -> Optional[Dict[str, Any]]:
        """Get current floor data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest version data
            cursor.execute("""
                SELECT svg FROM drawing_versions 
                WHERE floor_id = ? 
                ORDER BY version_number DESC 
                LIMIT 1
            """, (floor_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting floor data: {e}")
            return None
    
    async def _get_floors_with_snapshots(self) -> List[str]:
        """Get list of floors that have snapshots"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT floor_id FROM drawing_versions
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            return [str(row[0]) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting floors with snapshots: {e}")
            return []
    
    async def _get_floor_snapshots(self, floor_id: str) -> List[Dict]:
        """Get all snapshots for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM drawing_versions 
                WHERE floor_id = ? 
                ORDER BY created_at DESC
            """, (floor_id,))
            
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            conn.close()
            
            snapshots = []
            for row in results:
                snapshot = dict(zip(columns, row))
                snapshots.append(snapshot)
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Error getting floor snapshots: {e}")
            return []
    
    async def _update_floor_snapshots(self, floor_id: str, snapshots: List[Dict]):
        """Update floor snapshots after cleanup"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete all snapshots for this floor
            cursor.execute("DELETE FROM drawing_versions WHERE floor_id = ?", (floor_id,))
            
            # Re-insert cleaned snapshots
            for snapshot in snapshots:
                cursor.execute("""
                    INSERT INTO drawing_versions (
                        floor_id, svg, version_number, user_id, action_type,
                        description, tags, metadata, is_auto_save, file_size,
                        checksum, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot['floor_id'],
                    snapshot['svg'],
                    snapshot['version_number'],
                    snapshot['user_id'],
                    snapshot['action_type'],
                    snapshot['description'],
                    snapshot['tags'],
                    snapshot['metadata'],
                    snapshot['is_auto_save'],
                    snapshot['file_size'],
                    snapshot['checksum'],
                    snapshot['created_at']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating floor snapshots: {e}")
    
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
            'active_floors': len(self.active_floors),
            'running': self.running,
            'config': self.config.__dict__,
            'cleanup_stats': self.cleanup_manager.get_cleanup_stats(),
            'scheduler_stats': {
                'floor_activity_count': len(self.scheduler.floor_activity),
                'snapshot_history_count': len(self.scheduler.snapshot_history)
            }
        }


# Factory function to create auto-snapshot service
def create_auto_snapshot_service(config: Optional[SnapshotConfig] = None) -> AutoSnapshotService:
    """Create and configure an auto-snapshot service"""
    if config is None:
        config = SnapshotConfig()
    
    return AutoSnapshotService(config)

# Global service instance
auto_snapshot_service = create_auto_snapshot_service()

# Global service instance
auto_snapshot_service = create_auto_snapshot_service() 