"""
Smart Tagging Kits Service

Provides comprehensive QR + BLE tag assignment to maintainable objects with
persistent tag-to-object mapping and offline/short-range scan resolution.
"""

import json
import time
import uuid
import hashlib
import sqlite3
import qrcode
import base64
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging
import re
from contextlib import contextmanager
import csv
import io

# Initialize logger
logger = logging.getLogger(__name__)


class TagType(Enum):
    """Tag type enumeration."""
    QR = "qr"
    BLE = "ble"
    HYBRID = "hybrid"


class TagStatus(Enum):
    """Tag status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    CONFLICT = "conflict"
    EXPIRED = "expired"


class ScanResult(Enum):
    """Scan result enumeration."""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    EXPIRED = "expired"
    INVALID = "invalid"
    OFFLINE = "offline"


@dataclass
class TagData:
    """Tag data structure."""
    tag_id: str
    tag_type: TagType
    tag_data: str
    object_id: Optional[str]
    status: TagStatus
    created_at: datetime
    assigned_at: Optional[datetime]
    last_scan_at: Optional[datetime]
    scan_count: int
    metadata: Dict[str, Any]
    device_id: str
    user_id: str


@dataclass
class ObjectMapping:
    """Object mapping structure."""
    object_id: str
    tag_id: str
    tag_type: TagType
    assigned_at: datetime
    assigned_by: str
    device_id: str
    metadata: Dict[str, Any]
    version: int


@dataclass
class ScanHistory:
    """Scan history structure."""
    scan_id: str
    tag_id: str
    tag_type: TagType
    object_id: Optional[str]
    scan_time: datetime
    device_id: str
    user_id: str
    location: Optional[Dict[str, float]]
    result: ScanResult
    response_time: float


@dataclass
class AssignmentHistory:
    """Assignment history structure."""
    assignment_id: str
    tag_id: str
    object_id: str
    action: str  # "assign", "remove", "update"
    assigned_by: str
    device_id: str
    timestamp: datetime
    metadata: Dict[str, Any]


class SmartTaggingService:
    """
    Smart tagging service for QR + BLE tag management.
    
    Provides comprehensive tag assignment, scanning, resolution, and management
    capabilities with offline support and persistent mapping.
    """
    
    def __init__(self, db_path: str = "smart_tagging.db"):
        self.db_path = db_path
        self.tag_database = {}
        self.object_mappings = {}
        self.scan_history = []
        self.assignment_history = []
        self._lock = threading.RLock()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Initialize database
        self._initialize_database()
        
        # Load existing data
        self._load_existing_data()
        
        logger.info("Smart Tagging Service initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for tag management."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Tags table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        tag_id TEXT PRIMARY KEY,
                        tag_type TEXT NOT NULL,
                        tag_data TEXT NOT NULL UNIQUE,
                        object_id TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        assigned_at TEXT,
                        last_scan_at TEXT,
                        scan_count INTEGER DEFAULT 0,
                        metadata TEXT,
                        device_id TEXT NOT NULL,
                        user_id TEXT NOT NULL
                    )
                """)
                
                # Object mappings table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS object_mappings (
                        object_id TEXT NOT NULL,
                        tag_id TEXT NOT NULL,
                        tag_type TEXT NOT NULL,
                        assigned_at TEXT NOT NULL,
                        assigned_by TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        metadata TEXT,
                        version INTEGER DEFAULT 1,
                        PRIMARY KEY (object_id, tag_id),
                        FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
                    )
                """)
                
                # Scan history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scan_history (
                        scan_id TEXT PRIMARY KEY,
                        tag_id TEXT NOT NULL,
                        tag_type TEXT NOT NULL,
                        object_id TEXT,
                        scan_time TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        location TEXT,
                        result TEXT NOT NULL,
                        response_time REAL,
                        FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
                    )
                """)
                
                # Assignment history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS assignment_history (
                        assignment_id TEXT PRIMARY KEY,
                        tag_id TEXT NOT NULL,
                        object_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        assigned_by TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_object_id ON tags (object_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_status ON tags (status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_history_tag_id ON scan_history (tag_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_history_time ON scan_history (scan_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_assignment_history_tag_id ON assignment_history (tag_id)")
                
                conn.commit()
            logger.info("Smart Tagging database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _load_existing_data(self):
        """Load existing tag data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load tags
                cursor = conn.execute("""
                    SELECT tag_id, tag_type, tag_data, object_id, status, created_at,
                           assigned_at, last_scan_at, scan_count, metadata, device_id, user_id
                    FROM tags
                """)
                
                for row in cursor.fetchall():
                    tag_data = TagData(
                        tag_id=row[0],
                        tag_type=TagType(row[1]),
                        tag_data=row[2],
                        object_id=row[3],
                        status=TagStatus(row[4]),
                        created_at=datetime.fromisoformat(row[5]),
                        assigned_at=datetime.fromisoformat(row[6]) if row[6] else None,
                        last_scan_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        scan_count=row[8],
                        metadata=json.loads(row[9]) if row[9] else {},
                        device_id=row[10],
                        user_id=row[11]
                    )
                    self.tag_database[row[0]] = tag_data
                
                # Load object mappings
                cursor = conn.execute("""
                    SELECT object_id, tag_id, tag_type, assigned_at, assigned_by,
                           device_id, metadata, version
                    FROM object_mappings
                """)
                
                for row in cursor.fetchall():
                    mapping = ObjectMapping(
                        object_id=row[0],
                        tag_id=row[1],
                        tag_type=TagType(row[2]),
                        assigned_at=datetime.fromisoformat(row[3]),
                        assigned_by=row[4],
                        device_id=row[5],
                        metadata=json.loads(row[6]) if row[6] else {},
                        version=row[7]
                    )
                    self.object_mappings[(row[0], row[1])] = mapping
                
                logger.info(f"Loaded {len(self.tag_database)} tags and {len(self.object_mappings)} mappings")
        except Exception as e:
            logger.error(f"Failed to load existing data: {e}")
    
    def assign_tag(self, object_id: str, tag_type: TagType, tag_data: str, 
                   user_id: str, device_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assign QR or BLE tag to maintainable object.
        
        Args:
            object_id: Object ID to assign tag to
            tag_type: Type of tag (QR, BLE, or HYBRID)
            tag_data: Tag data content
            user_id: User performing the assignment
            device_id: Device performing the assignment
            metadata: Additional metadata for the assignment
            
        Returns:
            Assignment result with status and details
        """
        try:
            with self._lock:
                # Validate tag data
                validation_result = self.validate_tag(tag_data, tag_type)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": validation_result["error"],
                        "tag_id": None
                    }
                
                # Check if tag is already assigned
                existing_tag = self._find_tag_by_data(tag_data)
                if existing_tag and existing_tag.object_id:
                    return {
                        "success": False,
                        "error": f"Tag {tag_data} is already assigned to object {existing_tag.object_id}",
                        "tag_id": existing_tag.tag_id
                    }
                
                # Create or update tag
                tag_id = self._generate_tag_id(tag_data, tag_type)
                
                if existing_tag:
                    # Update existing tag
                    existing_tag.object_id = object_id
                    existing_tag.status = TagStatus.ASSIGNED
                    existing_tag.assigned_at = datetime.now()
                    existing_tag.metadata.update(metadata or {})
                    tag_data_obj = existing_tag
                else:
                    # Create new tag
                    tag_data_obj = TagData(
                        tag_id=tag_id,
                        tag_type=tag_type,
                        tag_data=tag_data,
                        object_id=object_id,
                        status=TagStatus.ASSIGNED,
                        created_at=datetime.now(),
                        assigned_at=datetime.now(),
                        last_scan_at=None,
                        scan_count=0,
                        metadata=metadata or {},
                        device_id=device_id,
                        user_id=user_id
                    )
                    self.tag_database[tag_id] = tag_data_obj
                
                # Create object mapping
                mapping = ObjectMapping(
                    object_id=object_id,
                    tag_id=tag_id,
                    tag_type=tag_type,
                    assigned_at=datetime.now(),
                    assigned_by=user_id,
                    device_id=device_id,
                    metadata=metadata or {},
                    version=1
                )
                self.object_mappings[(object_id, tag_id)] = mapping
                
                # Record assignment history
                history = AssignmentHistory(
                    assignment_id=str(uuid.uuid4()),
                    tag_id=tag_id,
                    object_id=object_id,
                    action="assign",
                    assigned_by=user_id,
                    device_id=device_id,
                    timestamp=datetime.now(),
                    metadata=metadata or {}
                )
                self.assignment_history.append(history)
                
                # Save to database
                self._save_tag_to_db(tag_data_obj)
                self._save_mapping_to_db(mapping)
                self._save_assignment_history_to_db(history)
                
                # Clear cache
                self._clear_cache()
                
                logger.info(f"Tag {tag_id} assigned to object {object_id}")
                
                return {
                    "success": True,
                    "tag_id": tag_id,
                    "object_id": object_id,
                    "tag_type": tag_type.value,
                    "assigned_at": tag_data_obj.assigned_at.isoformat(),
                    "message": f"Tag {tag_data} successfully assigned to object {object_id}"
                }
                
        except Exception as e:
            logger.error(f"Tag assignment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tag_id": None
            }
    
    def validate_tag(self, tag_data: str, tag_type: TagType) -> Dict[str, Any]:
        """
        Validate tag format and uniqueness.
        
        Args:
            tag_data: Tag data to validate
            tag_type: Type of tag to validate
            
        Returns:
            Validation result with status and details
        """
        try:
            # Basic format validation
            if not tag_data or len(tag_data.strip()) == 0:
                return {
                    "valid": False,
                    "error": "Tag data cannot be empty"
                }
            
            # Tag type specific validation
            if tag_type == TagType.QR:
                # QR code validation
                if len(tag_data) < 3 or len(tag_data) > 1000:
                    return {
                        "valid": False,
                        "error": "QR tag data must be between 3 and 1000 characters"
                    }
                
                # Check for valid QR code format
                if not re.match(r'^[A-Za-z0-9\-_\.]+$', tag_data):
                    return {
                        "valid": False,
                        "error": "QR tag data contains invalid characters"
                    }
            
            elif tag_type == TagType.BLE:
                # BLE beacon validation
                if len(tag_data) != 16 and len(tag_data) != 32:
                    return {
                        "valid": False,
                        "error": "BLE tag data must be 16 or 32 characters"
                    }
                
                # Check for valid hex format
                if not re.match(r'^[0-9A-Fa-f]+$', tag_data):
                    return {
                        "valid": False,
                        "error": "BLE tag data must be hexadecimal format"
                    }
            
            elif tag_type == TagType.HYBRID:
                # Hybrid tag validation (both QR and BLE)
                qr_part, ble_part = tag_data.split(':', 1) if ':' in tag_data else (tag_data, '')
                
                qr_valid = len(qr_part) >= 3 and len(qr_part) <= 1000
                ble_valid = len(ble_part) in [16, 32] and re.match(r'^[0-9A-Fa-f]*$', ble_part)
                
                if not qr_valid or not ble_valid:
                    return {
                        "valid": False,
                        "error": "Hybrid tag must have valid QR and BLE components"
                    }
            
            # Check uniqueness
            existing_tag = self._find_tag_by_data(tag_data)
            if existing_tag:
                return {
                    "valid": False,
                    "error": f"Tag {tag_data} already exists",
                    "existing_tag_id": existing_tag.tag_id
                }
            
            return {
                "valid": True,
                "message": "Tag validation successful"
            }
            
        except Exception as e:
            logger.error(f"Tag validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def scan_tag(self, tag_data: str, tag_type: TagType, user_id: str, 
                 device_id: str, location: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Scan and resolve tag to object mapping.
        
        Args:
            tag_data: Tag data to scan
            tag_type: Type of tag being scanned
            user_id: User performing the scan
            device_id: Device performing the scan
            location: Optional location data
            
        Returns:
            Scan result with object information
        """
        try:
            start_time = time.time()
            
            # Find tag in database
            tag = self._find_tag_by_data(tag_data)
            
            if not tag:
                result = ScanResult.NOT_FOUND
                object_id = None
                response_time = time.time() - start_time
                
                # Record scan history
                self._record_scan_history(tag_data, tag_type, None, user_id, device_id, 
                                        location, result, response_time)
                
                return {
                    "success": False,
                    "result": result.value,
                    "error": f"Tag {tag_data} not found",
                    "object_id": None,
                    "response_time": response_time
                }
            
            # Check tag status
            if tag.status == TagStatus.EXPIRED:
                result = ScanResult.EXPIRED
                object_id = None
            elif tag.status == TagStatus.INACTIVE:
                result = ScanResult.INVALID
                object_id = None
            elif tag.object_id:
                result = ScanResult.SUCCESS
                object_id = tag.object_id
                
                # Update scan count and last scan time
                tag.scan_count += 1
                tag.last_scan_at = datetime.now()
                self._save_tag_to_db(tag)
            else:
                result = ScanResult.NOT_FOUND
                object_id = None
            
            response_time = time.time() - start_time
            
            # Record scan history
            self._record_scan_history(tag_data, tag_type, object_id, user_id, device_id,
                                    location, result, response_time)
            
            if result == ScanResult.SUCCESS:
                # Get object details
                object_details = self._get_object_details(object_id)
                
                return {
                    "success": True,
                    "result": result.value,
                    "object_id": object_id,
                    "object_details": object_details,
                    "tag_id": tag.tag_id,
                    "tag_type": tag.tag_type.value,
                    "scan_count": tag.scan_count,
                    "response_time": response_time
                }
            else:
                return {
                    "success": False,
                    "result": result.value,
                    "error": f"Tag scan failed: {result.value}",
                    "object_id": None,
                    "response_time": response_time
                }
                
        except Exception as e:
            logger.error(f"Tag scanning failed: {e}")
            return {
                "success": False,
                "result": ScanResult.INVALID.value,
                "error": str(e),
                "object_id": None,
                "response_time": time.time() - start_time
            }
    
    def resolve_object(self, tag_data: str, tag_type: TagType) -> Dict[str, Any]:
        """
        Resolve tag to object mapping (offline capable).
        
        Args:
            tag_data: Tag data to resolve
            tag_type: Type of tag to resolve
            
        Returns:
            Object resolution result
        """
        try:
            # Check cache first
            cache_key = f"{tag_data}_{tag_type.value}"
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                if time.time() - cached_result["timestamp"] < self._cache_ttl:
                    return cached_result["data"]
            
            # Find tag in database
            tag = self._find_tag_by_data(tag_data)
            
            if not tag:
                result = {
                    "success": False,
                    "found": False,
                    "error": f"Tag {tag_data} not found",
                    "object_id": None
                }
            elif tag.status != TagStatus.ASSIGNED:
                result = {
                    "success": False,
                    "found": True,
                    "error": f"Tag {tag_data} is not assigned (status: {tag.status.value})",
                    "object_id": None
                }
            else:
                # Get object details
                object_details = self._get_object_details(tag.object_id)
                
                result = {
                    "success": True,
                    "found": True,
                    "object_id": tag.object_id,
                    "object_details": object_details,
                    "tag_id": tag.tag_id,
                    "tag_type": tag.tag_type.value,
                    "assigned_at": tag.assigned_at.isoformat() if tag.assigned_at else None
                }
            
            # Cache result
            self._cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Object resolution failed: {e}")
            return {
                "success": False,
                "found": False,
                "error": str(e),
                "object_id": None
            }
    
    def get_tag_history(self, tag_data: str) -> List[Dict[str, Any]]:
        """
        Get complete tag assignment and usage history.
        
        Args:
            tag_data: Tag data to get history for
            
        Returns:
            List of historical events for the tag
        """
        try:
            tag = self._find_tag_by_data(tag_data)
            if not tag:
                return []
            
            history = []
            
            # Add tag creation event
            history.append({
                "event_type": "created",
                "timestamp": tag.created_at.isoformat(),
                "user_id": tag.user_id,
                "device_id": tag.device_id,
                "details": {
                    "tag_type": tag.tag_type.value,
                    "status": tag.status.value
                }
            })
            
            # Add assignment events
            assignment_events = [h for h in self.assignment_history if h.tag_id == tag.tag_id]
            for event in assignment_events:
                history.append({
                    "event_type": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.assigned_by,
                    "device_id": event.device_id,
                    "details": {
                        "object_id": event.object_id,
                        "metadata": event.metadata
                    }
                })
            
            # Add scan events (last 10 scans)
            scan_events = [s for s in self.scan_history if s.tag_id == tag.tag_id]
            scan_events.sort(key=lambda x: x.scan_time, reverse=True)
            
            for scan in scan_events[:10]:
                history.append({
                    "event_type": "scanned",
                    "timestamp": scan.scan_time.isoformat(),
                    "user_id": scan.user_id,
                    "device_id": scan.device_id,
                    "details": {
                        "result": scan.result.value,
                        "response_time": scan.response_time,
                        "location": scan.location
                    }
                })
            
            # Sort by timestamp
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get tag history: {e}")
            return []
    
    def update_tag_mapping(self, tag_data: str, object_id: str, user_id: str, 
                          device_id: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Update tag-to-object mapping.
        
        Args:
            tag_data: Tag data to update
            object_id: New object ID to assign
            user_id: User performing the update
            device_id: Device performing the update
            metadata: Additional metadata
            
        Returns:
            Success status of the update
        """
        try:
            with self._lock:
                tag = self._find_tag_by_data(tag_data)
                if not tag:
                    return False
                
                # Update tag assignment
                old_object_id = tag.object_id
                tag.object_id = object_id
                tag.assigned_at = datetime.now()
                tag.metadata.update(metadata or {})
                
                # Update or create object mapping
                mapping_key = (object_id, tag.tag_id)
                if mapping_key in self.object_mappings:
                    # Update existing mapping
                    mapping = self.object_mappings[mapping_key]
                    mapping.version += 1
                    mapping.assigned_at = datetime.now()
                    mapping.assigned_by = user_id
                    mapping.metadata.update(metadata or {})
                else:
                    # Create new mapping
                    mapping = ObjectMapping(
                        object_id=object_id,
                        tag_id=tag.tag_id,
                        tag_type=tag.tag_type,
                        assigned_at=datetime.now(),
                        assigned_by=user_id,
                        device_id=device_id,
                        metadata=metadata or {},
                        version=1
                    )
                    self.object_mappings[mapping_key] = mapping
                
                # Record assignment history
                history = AssignmentHistory(
                    assignment_id=str(uuid.uuid4()),
                    tag_id=tag.tag_id,
                    object_id=object_id,
                    action="update",
                    assigned_by=user_id,
                    device_id=device_id,
                    timestamp=datetime.now(),
                    metadata=metadata or {}
                )
                self.assignment_history.append(history)
                
                # Save to database
                self._save_tag_to_db(tag)
                self._save_mapping_to_db(mapping)
                self._save_assignment_history_to_db(history)
                
                # Clear cache
                self._clear_cache()
                
                logger.info(f"Tag {tag_data} mapping updated from {old_object_id} to {object_id}")
                return True
                
        except Exception as e:
            logger.error(f"Tag mapping update failed: {e}")
            return False
    
    def remove_tag_assignment(self, tag_data: str, user_id: str, device_id: str) -> bool:
        """
        Remove tag assignment from object.
        
        Args:
            tag_data: Tag data to remove assignment from
            user_id: User performing the removal
            device_id: Device performing the removal
            
        Returns:
            Success status of the removal
        """
        try:
            with self._lock:
                tag = self._find_tag_by_data(tag_data)
                if not tag or not tag.object_id:
                    return False
                
                object_id = tag.object_id
                
                # Update tag status
                tag.object_id = None
                tag.status = TagStatus.UNASSIGNED
                tag.assigned_at = None
                
                # Remove object mapping
                mapping_key = (object_id, tag.tag_id)
                if mapping_key in self.object_mappings:
                    del self.object_mappings[mapping_key]
                
                # Record assignment history
                history = AssignmentHistory(
                    assignment_id=str(uuid.uuid4()),
                    tag_id=tag.tag_id,
                    object_id=object_id,
                    action="remove",
                    assigned_by=user_id,
                    device_id=device_id,
                    timestamp=datetime.now(),
                    metadata={"removed_at": datetime.now().isoformat()}
                )
                self.assignment_history.append(history)
                
                # Save to database
                self._save_tag_to_db(tag)
                self._save_assignment_history_to_db(history)
                
                # Remove mapping from database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM object_mappings 
                        WHERE object_id = ? AND tag_id = ?
                    """, (object_id, tag.tag_id))
                    conn.commit()
                
                # Clear cache
                self._clear_cache()
                
                logger.info(f"Tag {tag_data} assignment removed from object {object_id}")
                return True
                
        except Exception as e:
            logger.error(f"Tag assignment removal failed: {e}")
            return False
    
    def get_object_tags(self, object_id: str) -> List[Dict[str, Any]]:
        """
        Get all tags assigned to an object.
        
        Args:
            object_id: Object ID to get tags for
            
        Returns:
            List of tags assigned to the object
        """
        try:
            tags = []
            
            for tag in self.tag_database.values():
                if tag.object_id == object_id:
                    tags.append({
                        "tag_id": tag.tag_id,
                        "tag_type": tag.tag_type.value,
                        "tag_data": tag.tag_data,
                        "status": tag.status.value,
                        "assigned_at": tag.assigned_at.isoformat() if tag.assigned_at else None,
                        "scan_count": tag.scan_count,
                        "last_scan_at": tag.last_scan_at.isoformat() if tag.last_scan_at else None,
                        "metadata": tag.metadata
                    })
            
            return tags
            
        except Exception as e:
            logger.error(f"Failed to get object tags: {e}")
            return []
    
    def bulk_assign_tags(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk assign multiple tags to objects.
        
        Args:
            assignments: List of assignment dictionaries
            
        Returns:
            Bulk assignment results
        """
        try:
            results = {
                "total": len(assignments),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for assignment in assignments:
                try:
                    result = self.assign_tag(
                        object_id=assignment["object_id"],
                        tag_type=TagType(assignment["tag_type"]),
                        tag_data=assignment["tag_data"],
                        user_id=assignment["user_id"],
                        device_id=assignment["device_id"],
                        metadata=assignment.get("metadata")
                    )
                    
                    if result["success"]:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append({
                            "tag_data": assignment["tag_data"],
                            "error": result["error"]
                        })
                        
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "tag_data": assignment.get("tag_data", "unknown"),
                        "error": str(e)
                    })
            
            logger.info(f"Bulk assignment completed: {results['successful']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Bulk assignment failed: {e}")
            return {
                "total": len(assignments),
                "successful": 0,
                "failed": len(assignments),
                "errors": [{"error": str(e)}]
            }
    
    def export_tag_data(self, format: str = "json") -> str:
        """
        Export tag data in specified format.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            if format.lower() == "json":
                export_data = {
                    "tags": [asdict(tag) for tag in self.tag_database.values()],
                    "mappings": [asdict(mapping) for mapping in self.object_mappings.values()],
                    "export_timestamp": datetime.now().isoformat(),
                    "total_tags": len(self.tag_database),
                    "total_mappings": len(self.object_mappings)
                }
                return json.dumps(export_data, indent=2, default=str)
            
            elif format.lower() == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "tag_id", "tag_type", "tag_data", "object_id", "status",
                    "created_at", "assigned_at", "scan_count", "device_id", "user_id"
                ])
                
                # Write data
                for tag in self.tag_database.values():
                    writer.writerow([
                        tag.tag_id, tag.tag_type.value, tag.tag_data, tag.object_id,
                        tag.status.value, tag.created_at.isoformat(),
                        tag.assigned_at.isoformat() if tag.assigned_at else "",
                        tag.scan_count, tag.device_id, tag.user_id
                    ])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Tag data export failed: {e}")
            return ""
    
    def import_tag_data(self, data: str, format: str) -> Dict[str, Any]:
        """
        Import tag data from specified format.
        
        Args:
            data: Data to import
            format: Import format (json, csv)
            
        Returns:
            Import results
        """
        try:
            results = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            if format.lower() == "json":
                import_data = json.loads(data)
                tags_data = import_data.get("tags", [])
                
                for tag_data in tags_data:
                    try:
                        # Convert string timestamps back to datetime
                        if "created_at" in tag_data:
                            tag_data["created_at"] = datetime.fromisoformat(tag_data["created_at"])
                        if "assigned_at" in tag_data and tag_data["assigned_at"]:
                            tag_data["assigned_at"] = datetime.fromisoformat(tag_data["assigned_at"])
                        if "last_scan_at" in tag_data and tag_data["last_scan_at"]:
                            tag_data["last_scan_at"] = datetime.fromisoformat(tag_data["last_scan_at"])
                        
                        # Create tag object
                        tag = TagData(**tag_data)
                        self.tag_database[tag.tag_id] = tag
                        self._save_tag_to_db(tag)
                        
                        results["successful"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append({
                            "tag_data": tag_data.get("tag_data", "unknown"),
                            "error": str(e)
                        })
                
                results["total"] = len(tags_data)
            
            elif format.lower() == "csv":
                reader = csv.DictReader(io.StringIO(data))
                
                for row in reader:
                    try:
                        # Create tag object from CSV row
                        tag = TagData(
                            tag_id=row["tag_id"],
                            tag_type=TagType(row["tag_type"]),
                            tag_data=row["tag_data"],
                            object_id=row["object_id"] if row["object_id"] else None,
                            status=TagStatus(row["status"]),
                            created_at=datetime.fromisoformat(row["created_at"]),
                            assigned_at=datetime.fromisoformat(row["assigned_at"]) if row["assigned_at"] else None,
                            last_scan_at=None,
                            scan_count=int(row["scan_count"]),
                            metadata={},
                            device_id=row["device_id"],
                            user_id=row["user_id"]
                        )
                        
                        self.tag_database[tag.tag_id] = tag
                        self._save_tag_to_db(tag)
                        
                        results["successful"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append({
                            "tag_data": row.get("tag_data", "unknown"),
                            "error": str(e)
                        })
                
                results["total"] = sum(1 for _ in csv.DictReader(io.StringIO(data)))
            
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            logger.info(f"Tag data import completed: {results['successful']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Tag data import failed: {e}")
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "errors": [{"error": str(e)}]
            }
    
    def get_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get tag analytics and usage statistics.
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=period_days)
            
            # Filter recent data
            recent_scans = [s for s in self.scan_history if s.scan_time >= cutoff_date]
            recent_assignments = [a for a in self.assignment_history if a.timestamp >= cutoff_date]
            
            # Calculate statistics
            total_tags = len(self.tag_database)
            assigned_tags = len([t for t in self.tag_database.values() if t.status == TagStatus.ASSIGNED])
            unassigned_tags = total_tags - assigned_tags
            
            # Scan statistics
            total_scans = len(recent_scans)
            successful_scans = len([s for s in recent_scans if s.result == ScanResult.SUCCESS])
            avg_response_time = sum(s.response_time for s in recent_scans) / len(recent_scans) if recent_scans else 0
            
            # Assignment statistics
            total_assignments = len(recent_assignments)
            assignments_by_type = {}
            for assignment in recent_assignments:
                tag = self.tag_database.get(assignment.tag_id)
                if tag:
                    tag_type = tag.tag_type.value
                    assignments_by_type[tag_type] = assignments_by_type.get(tag_type, 0) + 1
            
            # Most scanned tags
            tag_scan_counts = {}
            for scan in recent_scans:
                tag_scan_counts[scan.tag_id] = tag_scan_counts.get(scan.tag_id, 0) + 1
            
            most_scanned = sorted(tag_scan_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "period_days": period_days,
                "total_tags": total_tags,
                "assigned_tags": assigned_tags,
                "unassigned_tags": unassigned_tags,
                "assignment_rate": assigned_tags / total_tags if total_tags > 0 else 0,
                "total_scans": total_scans,
                "successful_scans": successful_scans,
                "scan_success_rate": successful_scans / total_scans if total_scans > 0 else 0,
                "avg_response_time": avg_response_time,
                "total_assignments": total_assignments,
                "assignments_by_type": assignments_by_type,
                "most_scanned_tags": [
                    {
                        "tag_id": tag_id,
                        "scan_count": count,
                        "tag_data": self.tag_database.get(tag_id, {}).tag_data if tag_id in self.tag_database else "Unknown"
                    }
                    for tag_id, count in most_scanned
                ]
            }
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return {"error": str(e)}
    
    # Helper methods
    
    def _find_tag_by_data(self, tag_data: str) -> Optional[TagData]:
        """Find tag by tag data."""
        for tag in self.tag_database.values():
            if tag.tag_data == tag_data:
                return tag
        return None
    
    def _generate_tag_id(self, tag_data: str, tag_type: TagType) -> str:
        """Generate unique tag ID."""
        hash_input = f"{tag_data}_{tag_type.value}_{time.time()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _get_object_details(self, object_id: str) -> Dict[str, Any]:
        """Get object details (placeholder implementation)."""
        # In a real implementation, this would fetch object details from the object management system
        return {
            "object_id": object_id,
            "name": f"Object {object_id}",
            "type": "maintainable",
            "location": "Building A",
            "status": "active"
        }
    
    def _record_scan_history(self, tag_data: str, tag_type: TagType, object_id: Optional[str],
                           user_id: str, device_id: str, location: Optional[Dict[str, float]],
                           result: ScanResult, response_time: float):
        """Record scan history."""
        tag = self._find_tag_by_data(tag_data)
        if tag:
            scan = ScanHistory(
                scan_id=str(uuid.uuid4()),
                tag_id=tag.tag_id,
                tag_type=tag_type,
                object_id=object_id,
                scan_time=datetime.now(),
                device_id=device_id,
                user_id=user_id,
                location=location,
                result=result,
                response_time=response_time
            )
            self.scan_history.append(scan)
            self._save_scan_history_to_db(scan)
    
    def _clear_cache(self):
        """Clear the cache."""
        self._cache.clear()
    
    def _save_tag_to_db(self, tag: TagData):
        """Save tag to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tags 
                    (tag_id, tag_type, tag_data, object_id, status, created_at,
                     assigned_at, last_scan_at, scan_count, metadata, device_id, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tag.tag_id, tag.tag_type.value, tag.tag_data, tag.object_id,
                    tag.status.value, tag.created_at.isoformat(),
                    tag.assigned_at.isoformat() if tag.assigned_at else None,
                    tag.last_scan_at.isoformat() if tag.last_scan_at else None,
                    tag.scan_count, json.dumps(tag.metadata), tag.device_id, tag.user_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save tag to database: {e}")
    
    def _save_mapping_to_db(self, mapping: ObjectMapping):
        """Save object mapping to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO object_mappings 
                    (object_id, tag_id, tag_type, assigned_at, assigned_by,
                     device_id, metadata, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mapping.object_id, mapping.tag_id, mapping.tag_type.value,
                    mapping.assigned_at.isoformat(), mapping.assigned_by,
                    mapping.device_id, json.dumps(mapping.metadata), mapping.version
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save mapping to database: {e}")
    
    def _save_scan_history_to_db(self, scan: ScanHistory):
        """Save scan history to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO scan_history 
                    (scan_id, tag_id, tag_type, object_id, scan_time, device_id,
                     user_id, location, result, response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scan.scan_id, scan.tag_id, scan.tag_type.value, scan.object_id,
                    scan.scan_time.isoformat(), scan.device_id, scan.user_id,
                    json.dumps(scan.location) if scan.location else None,
                    scan.result.value, scan.response_time
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save scan history to database: {e}")
    
    def _save_assignment_history_to_db(self, history: AssignmentHistory):
        """Save assignment history to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO assignment_history 
                    (assignment_id, tag_id, object_id, action, assigned_by,
                     device_id, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    history.assignment_id, history.tag_id, history.object_id,
                    history.action, history.assigned_by, history.device_id,
                    history.timestamp.isoformat(), json.dumps(history.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save assignment history to database: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the tagging service."""
        try:
            total_tags = len(self.tag_database)
            assigned_tags = len([t for t in self.tag_database.values() if t.status == TagStatus.ASSIGNED])
            total_scans = len(self.scan_history)
            total_assignments = len(self.assignment_history)
            
            # Calculate average response time from recent scans
            recent_scans = [s for s in self.scan_history if s.scan_time >= datetime.now() - timedelta(hours=1)]
            avg_response_time = sum(s.response_time for s in recent_scans) / len(recent_scans) if recent_scans else 0
            
            return {
                "total_tags": total_tags,
                "assigned_tags": assigned_tags,
                "unassigned_tags": total_tags - assigned_tags,
                "assignment_rate": assigned_tags / total_tags if total_tags > 0 else 0,
                "total_scans": total_scans,
                "total_assignments": total_assignments,
                "avg_response_time": avg_response_time,
                "cache_size": len(self._cache),
                "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)} 