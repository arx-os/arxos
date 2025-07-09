"""
Advanced Infrastructure & Performance Service

This service provides advanced infrastructure features for scalability and performance:
- Hierarchical SVG grouping for large buildings
- Advanced caching system for calculations
- Distributed processing for complex operations
- Real-time collaboration with conflict resolution
- Advanced compression algorithms
- Microservices architecture for scalability

Performance Targets:
- System handles buildings with 10,000+ objects
- Calculation cache reduces processing time by 80%
- Distributed processing scales linearly
- Real-time collaboration supports 50+ concurrent users
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import uuid
import hashlib
import zlib
import gzip
import lz4
import pickle
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging
from contextlib import contextmanager
import redis
import asyncio
from collections import defaultdict, OrderedDict
import math
import lz4.frame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy enumeration."""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


class CompressionLevel(Enum):
    """Compression level enumeration."""
    NONE = 0
    FAST = 1
    BALANCED = 2
    MAXIMUM = 3


class ProcessingMode(Enum):
    """Processing mode enumeration."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DISTRIBUTED = "distributed"


@dataclass
class CacheEntry:
    """Represents a cache entry."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size: int
    ttl: Optional[timedelta] = None


@dataclass
class ProcessingTask:
    """Represents a processing task."""
    task_id: str
    task_type: str
    data: Dict[str, Any]
    priority: int
    created_at: datetime
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class CollaborationSession:
    """Represents a collaboration session."""
    session_id: str
    users: List[str]
    document_id: str
    created_at: datetime
    last_activity: datetime
    changes: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]


class AdvancedInfrastructure:
    """
    Advanced Infrastructure & Performance service for scalability and performance.
    
    This service provides comprehensive infrastructure features including
    hierarchical SVG grouping, advanced caching, distributed processing,
    real-time collaboration, compression algorithms, and microservices architecture.
    """
    
    def __init__(self, db_path: str = "advanced_infrastructure.db", 
                 redis_url: str = "redis://localhost:6379"):
        """
        Initialize the advanced infrastructure service.
        
        Args:
            db_path: Path to the database file
            redis_url: Redis connection URL
        """
        self.db_path = db_path
        self.redis_url = redis_url
        self.cache = OrderedDict()
        self.cache_strategy = CacheStrategy.LRU
        self.max_cache_size = 1000
        self.max_cache_memory = 100 * 1024 * 1024  # 100MB
        
        # Processing pools
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        
        # Collaboration
        self.sessions: Dict[str, CollaborationSession] = {}
        self.session_lock = threading.RLock()
        
        # Performance metrics
        self.total_operations = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.processing_tasks = 0
        self.collaboration_sessions = 0
        
        # Initialize components
        self._init_database()
        self._init_redis()
        self._init_compression()
        
        self.redis_client = None  # Always define
        self._shutdown = False    # Shutdown flag
        
        logger.info("Advanced Infrastructure service initialized successfully")
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB NOT NULL,
                        created_at TEXT NOT NULL,
                        accessed_at TEXT NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        size INTEGER NOT NULL,
                        ttl TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processing_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        result TEXT,
                        error TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS collaboration_sessions (
                        session_id TEXT PRIMARY KEY,
                        users TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_activity TEXT NOT NULL,
                        changes TEXT,
                        conflicts TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS svg_groups (
                        group_id TEXT PRIMARY KEY,
                        parent_id TEXT,
                        name TEXT NOT NULL,
                        elements TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.commit()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _init_compression(self) -> None:
        """Initialize compression algorithms."""
        self.compression_algorithms = {
            'gzip': gzip,
            'zlib': zlib,
            'lz4': lz4.frame
        }
    
    def create_hierarchical_svg_group(self, name: str, elements: List[Dict[str, Any]],
                                    parent_id: Optional[str] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a hierarchical SVG group for organizing large building elements.
        
        Args:
            name: Group name
            elements: List of SVG elements
            parent_id: Parent group ID
            metadata: Additional metadata
            
        Returns:
            Group ID
        """
        try:
            group_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Create group structure
            group_data = {
                'group_id': group_id,
                'parent_id': parent_id,
                'name': name,
                'elements': elements,
                'metadata': metadata or {},
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO svg_groups 
                    (group_id, parent_id, name, elements, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    group_id,
                    parent_id,
                    name,
                    json.dumps(elements),
                    json.dumps(metadata or {}),
                    now.isoformat(),
                    now.isoformat()
                ))
                conn.commit()
            
            logger.info(f"Created SVG group: {group_id} ({name})")
            return group_id
            
        except Exception as e:
            logger.error(f"Failed to create SVG group: {e}")
            raise
    
    def get_svg_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get SVG group by ID.
        
        Args:
            group_id: Group identifier
            
        Returns:
            Group data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT group_id, parent_id, name, elements, metadata,
                           created_at, updated_at
                    FROM svg_groups
                    WHERE group_id = ?
                """, (group_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'group_id': row[0],
                        'parent_id': row[1],
                        'name': row[2],
                        'elements': json.loads(row[3]),
                        'metadata': json.loads(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get SVG group {group_id}: {e}")
            return None
    
    def get_svg_hierarchy(self, root_group_id: str) -> Dict[str, Any]:
        """
        Get complete SVG hierarchy starting from root group.
        
        Args:
            root_group_id: Root group identifier
            
        Returns:
            Complete hierarchy structure
        """
        try:
            hierarchy = {}
            
            def build_hierarchy(group_id: str, level: int = 0) -> Dict[str, Any]:
                group = self.get_svg_group(group_id)
                if not group:
                    return {}
                
                hierarchy_node = {
                    'group_id': group['group_id'],
                    'name': group['name'],
                    'elements': group['elements'],
                    'metadata': group['metadata'],
                    'level': level,
                    'children': []
                }
                
                # Find children
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT group_id FROM svg_groups WHERE parent_id = ?
                    """, (group_id,))
                    
                    for child_row in cursor.fetchall():
                        child_hierarchy = build_hierarchy(child_row[0], level + 1)
                        if child_hierarchy:
                            hierarchy_node['children'].append(child_hierarchy)
                
                return hierarchy_node
            
            hierarchy = build_hierarchy(root_group_id)
            return hierarchy
            
        except Exception as e:
            logger.error(f"Failed to get SVG hierarchy: {e}")
            return {}
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None,
                  strategy: Optional[CacheStrategy] = None) -> bool:
        """
        Set value in cache with specified strategy.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            strategy: Cache strategy
            
        Returns:
            True if successful
        """
        try:
            if strategy is None:
                strategy = self.cache_strategy
            elif isinstance(strategy, str):
                strategy = CacheStrategy(strategy)
            
            # Serialize value
            serialized_value = pickle.dumps(value)
            size = len(serialized_value)
            
            # Check memory limits
            if size > self.max_cache_memory:
                logger.warning(f"Value too large for cache: {size} bytes")
                return False
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                size=size,
                ttl=timedelta(seconds=ttl) if ttl else None
            )
            
            # Apply cache strategy
            if strategy == CacheStrategy.LRU:
                self._apply_lru_strategy(entry)
            elif strategy == CacheStrategy.LFU:
                self._apply_lfu_strategy(entry)
            elif strategy == CacheStrategy.FIFO:
                self._apply_fifo_strategy(entry)
            elif strategy == CacheStrategy.TTL:
                self._apply_ttl_strategy(entry)
            
            # Save to database
            self._save_cache_entry(entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache entry: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            # Try memory cache first
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if entry.ttl and datetime.now() - entry.created_at > entry.ttl:
                    del self.cache[key]
                    return None
                
                # Update access info
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                self.cache_hits += 1
                
                return entry.value
            
            # Try database cache
            entry = self._load_cache_entry(key)
            if entry:
                # Check TTL
                if entry.ttl and datetime.now() - entry.created_at > entry.ttl:
                    self._remove_cache_entry(key)
                    return None
                
                # Move to memory cache
                self.cache[key] = entry
                self.cache_hits += 1
                
                return entry.value
            
            self.cache_misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache entry: {e}")
            return None
    
    def _apply_lru_strategy(self, entry: CacheEntry) -> None:
        """Apply LRU cache strategy."""
        if entry.key in self.cache:
            del self.cache[entry.key]
        
        self.cache[entry.key] = entry
        
        # Remove oldest if cache is full
        if len(self.cache) > self.max_cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
    
    def _apply_lfu_strategy(self, entry: CacheEntry) -> None:
        """Apply LFU cache strategy."""
        if entry.key in self.cache:
            existing_entry = self.cache[entry.key]
            entry.access_count = existing_entry.access_count + 1
        
        self.cache[entry.key] = entry
        
        # Remove least frequently used if cache is full
        if len(self.cache) > self.max_cache_size:
            least_used_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k].access_count)
            del self.cache[least_used_key]
    
    def _apply_fifo_strategy(self, entry: CacheEntry) -> None:
        """Apply FIFO cache strategy."""
        self.cache[entry.key] = entry
        
        # Remove oldest if cache is full
        if len(self.cache) > self.max_cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
    
    def _apply_ttl_strategy(self, entry: CacheEntry) -> None:
        """Apply TTL cache strategy."""
        if not entry.ttl:
            return
        
        self.cache[entry.key] = entry
        
        # Remove expired entries
        now = datetime.now()
        expired_keys = [
            key for key, cache_entry in self.cache.items()
            if cache_entry.ttl and now - cache_entry.created_at > cache_entry.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def _save_cache_entry(self, entry: CacheEntry) -> None:
        """Save cache entry to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, created_at, accessed_at, access_count, size, ttl)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key,
                    pickle.dumps(entry.value),
                    entry.created_at.isoformat(),
                    entry.accessed_at.isoformat(),
                    entry.access_count,
                    entry.size,
                    entry.ttl.total_seconds() if entry.ttl else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save cache entry: {e}")
            raise
    
    def _load_cache_entry(self, key: str) -> Optional[CacheEntry]:
        """Load cache entry from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT value, created_at, accessed_at, access_count, size, ttl
                    FROM cache_entries WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if row:
                    return CacheEntry(
                        key=key,
                        value=pickle.loads(row[0]),
                        created_at=datetime.fromisoformat(row[1]),
                        accessed_at=datetime.fromisoformat(row[2]),
                        access_count=row[3],
                        size=row[4],
                        ttl=timedelta(seconds=row[5]) if row[5] else None
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to load cache entry: {e}")
            raise
    
    def _remove_cache_entry(self, key: str) -> None:
        """Remove cache entry from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to remove cache entry: {e}")
            raise
    
    def process_distributed_task(self, task_type: str, data: Dict[str, Any],
                               priority: int = 1, mode: ProcessingMode = ProcessingMode.PARALLEL) -> str:
        """
        Process a distributed task with specified mode.
        
        Args:
            task_type: Type of task
            data: Task data
            priority: Task priority
            mode: Processing mode
            
        Returns:
            Task ID
        """
        try:
            task_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Create task
            task = ProcessingTask(
                task_id=task_id,
                task_type=task_type,
                data=data,
                priority=priority,
                created_at=now,
                status="pending"
            )
            
            # Save task
            self._save_processing_task(task)
            
            # Process based on mode
            if mode == ProcessingMode.SEQUENTIAL:
                self._process_sequential_task(task)
            elif mode == ProcessingMode.PARALLEL:
                self._process_parallel_task(task)
            elif mode == ProcessingMode.DISTRIBUTED:
                self._process_distributed_task(task)
            
            self.processing_tasks += 1
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to process distributed task: {e}")
            raise
    
    def _process_sequential_task(self, task: ProcessingTask) -> None:
        """Process task sequentially."""
        try:
            task.status = "processing"
            self._update_processing_task(task)
            
            # Process based on task type
            if task.task_type == "svg_optimization":
                result = self._optimize_svg(task.data)
            elif task.task_type == "calculation":
                result = self._perform_calculation(task.data)
            elif task.task_type == "compression":
                result = self._compress_data(task.data)
            else:
                result = task.data
            
            task.result = result
            task.status = "completed"
            self._update_processing_task(task)
            
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            self._update_processing_task(task)
    
    def _process_parallel_task(self, task: ProcessingTask) -> None:
        """Process task in parallel."""
        future = self.thread_pool.submit(self._process_sequential_task, task)
        # Task will be updated when future completes
    
    def _process_distributed_task(self, task: ProcessingTask) -> None:
        """Process task in distributed mode."""
        future = self.process_pool.submit(self._process_sequential_task, task)
        # Task will be updated when future completes
    
    def _optimize_svg(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize SVG data."""
        svg_content = data.get('svg', '')
        
        # Remove unnecessary whitespace
        optimized = ' '.join(svg_content.split())
        
        # Remove comments
        import re
        optimized = re.sub(r'<!--.*?-->', '', optimized)
        
        return {
            'original_size': len(svg_content),
            'optimized_size': len(optimized),
            'compression_ratio': (1 - len(optimized) / len(svg_content)) * 100,
            'optimized_svg': optimized
        }
    
    def _perform_calculation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform calculation task."""
        operation = data.get('operation', 'add')
        values = data.get('values', [])
        
        if operation == 'add':
            result = sum(values)
        elif operation == 'multiply':
            result = math.prod(values)
        elif operation == 'average':
            result = sum(values) / len(values) if values else 0
        else:
            result = values
        
        return {
            'operation': operation,
            'values': values,
            'result': result
        }
    
    def _compress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compress data using various algorithms."""
        content = data.get('content', '')
        algorithm = data.get('algorithm', 'gzip')
        level = data.get('level', CompressionLevel.BALANCED)
        if isinstance(level, int):
            level = CompressionLevel(level)
        elif isinstance(level, str):
            level = CompressionLevel[level.upper()]
        if algorithm == 'gzip':
            compressed = gzip.compress(content.encode(), compresslevel=level.value)
        elif algorithm == 'zlib':
            compressed = zlib.compress(content.encode(), level=level.value)
        elif algorithm == 'lz4':
            compressed = lz4.frame.compress(content.encode())
        else:
            compressed = content.encode()
        
        return {
            'original_size': len(content),
            'compressed_size': len(compressed),
            'compression_ratio': (1 - len(compressed) / len(content)) * 100 if len(content) else 0,
            'algorithm': algorithm,
            'compressed_data': compressed
        }
    
    def _save_processing_task(self, task: ProcessingTask) -> None:
        """Save processing task to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO processing_tasks 
                    (task_id, task_type, data, priority, created_at, status, result, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id,
                    task.task_type,
                    json.dumps(task.data),
                    task.priority,
                    task.created_at.isoformat(),
                    task.status,
                    json.dumps(task.result) if task.result else None,
                    task.error
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save processing task: {e}")
            raise
    
    def _update_processing_task(self, task: ProcessingTask) -> None:
        """Update processing task in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE processing_tasks 
                    SET status = ?, result = ?, error = ?
                    WHERE task_id = ?
                """, (
                    task.status,
                    json.dumps(task.result) if task.result else None,
                    task.error,
                    task.task_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update processing task: {e}")
            raise
    
    def create_collaboration_session(self, document_id: str, users: List[str]) -> str:
        """
        Create a collaboration session for real-time editing.
        
        Args:
            document_id: Document identifier
            users: List of user IDs
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            session = CollaborationSession(
                session_id=session_id,
                users=users,
                document_id=document_id,
                created_at=now,
                last_activity=now,
                changes=[],
                conflicts=[]
            )
            
            with self.session_lock:
                self.sessions[session_id] = session
                self._save_collaboration_session(session)
            
            self.collaboration_sessions += 1
            logger.info(f"Created collaboration session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create collaboration session: {e}")
            raise
    
    def join_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """
        Join an existing collaboration session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            True if successful
        """
        try:
            with self.session_lock:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    if user_id not in session.users:
                        session.users.append(user_id)
                        session.last_activity = datetime.now()
                        self._update_collaboration_session(session)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to join collaboration session: {e}")
            return False
    
    def add_collaboration_change(self, session_id: str, user_id: str, 
                               change: Dict[str, Any]) -> bool:
        """
        Add a change to collaboration session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            change: Change data
            
        Returns:
            True if successful
        """
        try:
            with self.session_lock:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    
                    # Add change
                    change_data = {
                        'id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'timestamp': datetime.now().isoformat(),
                        'change': change
                    }
                    
                    session.changes.append(change_data)
                    session.last_activity = datetime.now()
                    
                    # Check for conflicts
                    conflicts = self._detect_conflicts(session, change_data)
                    if conflicts:
                        session.conflicts.extend(conflicts)
                    
                    self._update_collaboration_session(session)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to add collaboration change: {e}")
            return False
    
    def _detect_conflicts(self, session: CollaborationSession, 
                         new_change: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts in collaboration session."""
        conflicts = []
        
        # Simple conflict detection based on element ID
        new_element_id = new_change['change'].get('element_id')
        if new_element_id:
            for existing_change in session.changes[-10:]:  # Check last 10 changes
                if (existing_change['user_id'] != new_change['user_id'] and
                    existing_change['change'].get('element_id') == new_element_id):
                    conflicts.append({
                        'new_change': new_change,
                        'conflicting_change': existing_change,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return conflicts
    
    def _save_collaboration_session(self, session: CollaborationSession) -> None:
        """Save collaboration session to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO collaboration_sessions 
                    (session_id, users, document_id, created_at, last_activity, changes, conflicts)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    json.dumps(session.users),
                    session.document_id,
                    session.created_at.isoformat(),
                    session.last_activity.isoformat(),
                    json.dumps(session.changes),
                    json.dumps(session.conflicts)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save collaboration session: {e}")
            raise
    
    def _update_collaboration_session(self, session: CollaborationSession) -> None:
        """Update collaboration session in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE collaboration_sessions 
                    SET users = ?, last_activity = ?, changes = ?, conflicts = ?
                    WHERE session_id = ?
                """, (
                    json.dumps(session.users),
                    session.last_activity.isoformat(),
                    json.dumps(session.changes),
                    json.dumps(session.conflicts),
                    session.session_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update collaboration session: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics
        """
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        return {
            'total_operations': self.total_operations,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.cache),
            'processing_tasks': self.processing_tasks,
            'collaboration_sessions': self.collaboration_sessions,
            'active_sessions': len(self.sessions),
            'memory_usage': sum(entry.size for entry in self.cache.values()),
            'max_cache_size': self.max_cache_size,
            'max_cache_memory': self.max_cache_memory
        }
    
    def shutdown(self) -> None:
        if getattr(self, '_shutdown', False):
            return
        self._shutdown = True
        logger.info("Shutting down Advanced Infrastructure service...")
        
        # Shutdown thread pools
        if hasattr(self, 'thread_pool'):
            try:
                self.thread_pool.shutdown(wait=True)
            except Exception as e:
                logger.warning(f"Thread pool shutdown error: {e}")
        if hasattr(self, 'process_pool'):
            try:
                self.process_pool.shutdown(wait=True)
            except Exception as e:
                logger.warning(f"Process pool shutdown error: {e}")
        
        # Close Redis connection
        if hasattr(self, 'redis_client') and self.redis_client:
            try:
                self.redis_client.close()
            except Exception as e:
                logger.warning(f"Redis client close error: {e}")
        
        logger.info("Advanced Infrastructure service shutdown complete")
    
    def __del__(self):
        try:
            if hasattr(self, 'shutdown'):
                self.shutdown()
        except Exception as e:
            logger.warning(f"Exception in __del__: {e}") 