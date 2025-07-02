"""
Advanced Version Control Service
Handles branching, merging, conflict resolution, annotations, and comments for floor data
"""

import json
import hashlib
import difflib
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import sqlite3
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

class VersionType(Enum):
    """Version types"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    BRANCH = "branch"

class BranchStatus(Enum):
    """Branch status"""
    ACTIVE = "active"
    MERGED = "merged"
    DELETED = "deleted"
    CONFLICT = "conflict"

class MergeStatus(Enum):
    """Merge status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

class ConflictType(Enum):
    """Conflict types"""
    OBJECT_MODIFIED = "object_modified"
    OBJECT_DELETED = "object_deleted"
    OBJECT_ADDED = "object_added"
    PROPERTY_CONFLICT = "property_conflict"

@dataclass
class Version:
    """Version information"""
    version_id: str
    floor_id: str
    building_id: str
    branch_name: str
    parent_version_id: Optional[str] = None
    version_type: VersionType = VersionType.MINOR
    version_number: str = ""
    commit_message: str = ""
    author: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    data_hash: str = ""
    data_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Branch:
    """Branch information"""
    branch_name: str
    floor_id: str
    building_id: str
    base_version_id: str
    current_version_id: str
    status: BranchStatus = BranchStatus.ACTIVE
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MergeRequest:
    """Merge request information"""
    merge_id: str
    source_branch: str
    target_branch: str
    floor_id: str
    building_id: str
    status: MergeStatus = MergeStatus.PENDING
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    merged_at: Optional[datetime] = None
    merged_by: Optional[str] = None
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    resolution_strategy: str = "manual"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conflict:
    """Conflict information"""
    conflict_id: str
    merge_id: str
    conflict_type: ConflictType
    object_id: Optional[str] = None
    property_name: Optional[str] = None
    source_value: Any = None
    target_value: Any = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

class ConflictResolution:
    """Conflict resolution strategies and utilities"""
    
    @staticmethod
    def resolve_object_conflict(conflict: Conflict, strategy: str = "manual") -> Dict[str, Any]:
        """Resolve object-level conflicts"""
        if strategy == "source_wins":
            return {"resolution": "source", "value": conflict.source_value}
        elif strategy == "target_wins":
            return {"resolution": "target", "value": conflict.target_value}
        elif strategy == "merge":
            return {"resolution": "merge", "value": conflict.source_value}
        else:
            return {"resolution": "manual", "value": None}
    
    @staticmethod
    def resolve_property_conflict(conflict: Conflict, strategy: str = "manual") -> Dict[str, Any]:
        """Resolve property-level conflicts"""
        if strategy == "source_wins":
            return {"resolution": "source", "value": conflict.source_value}
        elif strategy == "target_wins":
            return {"resolution": "target", "value": conflict.target_value}
        elif strategy == "merge":
            # For properties, try to merge intelligently
            if isinstance(conflict.source_value, dict) and isinstance(conflict.target_value, dict):
                merged = conflict.source_value.copy()
                merged.update(conflict.target_value)
                return {"resolution": "merge", "value": merged}
            else:
                return {"resolution": "source", "value": conflict.source_value}
        else:
            return {"resolution": "manual", "value": None}

@dataclass
class Annotation:
    """Version annotation"""
    annotation_id: str
    version_id: str
    floor_id: str
    building_id: str
    object_id: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    annotation_type: str = "note"
    title: str = ""
    content: str = ""
    author: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Comment:
    """Comment on version or annotation"""
    comment_id: str
    parent_id: str  # version_id or annotation_id
    parent_type: str  # "version" or "annotation"
    author: str = ""
    content: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class VersionControlService:
    """Advanced version control service"""
    
    def __init__(self, db_path: str = "./data/version_control.db", storage_path: str = "./data/versions"):
        self.db_path = db_path
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize version control database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versions (
                version_id TEXT PRIMARY KEY,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                branch_name TEXT NOT NULL,
                parent_version_id TEXT,
                version_type TEXT NOT NULL,
                version_number TEXT,
                commit_message TEXT,
                author TEXT,
                created_at TEXT NOT NULL,
                data_hash TEXT,
                data_size INTEGER,
                metadata TEXT
            )
        ''')
        
        # Create branches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branches (
                branch_name TEXT,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                base_version_id TEXT NOT NULL,
                current_version_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                description TEXT,
                metadata TEXT,
                PRIMARY KEY (branch_name, floor_id, building_id)
            )
        ''')
        
        # Create merge_requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS merge_requests (
                merge_id TEXT PRIMARY KEY,
                source_branch TEXT NOT NULL,
                target_branch TEXT NOT NULL,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                merged_at TEXT,
                merged_by TEXT,
                conflicts TEXT,
                resolution_strategy TEXT,
                description TEXT,
                metadata TEXT
            )
        ''')
        
        # Create conflicts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflicts (
                conflict_id TEXT PRIMARY KEY,
                merge_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                object_id TEXT,
                property_name TEXT,
                source_value TEXT,
                target_value TEXT,
                resolution TEXT,
                resolved_by TEXT,
                resolved_at TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Create annotations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                annotation_id TEXT PRIMARY KEY,
                version_id TEXT NOT NULL,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                object_id TEXT,
                position_x REAL,
                position_y REAL,
                annotation_type TEXT NOT NULL,
                title TEXT,
                content TEXT,
                author TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                parent_id TEXT NOT NULL,
                parent_type TEXT NOT NULL,
                author TEXT,
                content TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_versions_floor ON versions(floor_id, building_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_versions_branch ON versions(branch_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_branches_floor ON branches(floor_id, building_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_merge_requests_floor ON merge_requests(floor_id, building_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotations_version ON annotations(version_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, parent_type)')
        
        conn.commit()
        conn.close()
    
    def create_version(self, floor_data: Dict[str, Any], floor_id: str, building_id: str,
                      branch_name: str, commit_message: str, author: str,
                      parent_version_id: Optional[str] = None,
                      version_type: VersionType = VersionType.MINOR) -> Dict[str, Any]:
        """Create a new version"""
        try:
            # Generate version ID and hash
            version_id = str(uuid.uuid4())
            data_json = json.dumps(floor_data, sort_keys=True)
            data_hash = hashlib.sha256(data_json.encode()).hexdigest()
            
            # Generate version number
            version_number = self._generate_version_number(branch_name, version_type)
            
            # Create version record
            version = Version(
                version_id=version_id,
                floor_id=floor_id,
                building_id=building_id,
                branch_name=branch_name,
                parent_version_id=parent_version_id,
                version_type=version_type,
                version_number=version_number,
                commit_message=commit_message,
                author=author,
                data_hash=data_hash,
                data_size=len(data_json)
            )
            
            # Store version data
            version_file = self.storage_path / f"{version_id}.json"
            with open(version_file, 'w') as f:
                json.dump(floor_data, f, indent=2)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO versions (
                    version_id, floor_id, building_id, branch_name, parent_version_id,
                    version_type, version_number, commit_message, author, created_at,
                    data_hash, data_size, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                version.version_id, version.floor_id, version.building_id,
                version.branch_name, version.parent_version_id,
                version.version_type.value, version.version_number,
                version.commit_message, version.author, version.created_at.isoformat(),
                version.data_hash, version.data_size, json.dumps(version.metadata)
            ))
            
            # Update branch current version
            cursor.execute('''
                UPDATE branches SET current_version_id = ?, last_updated = ?
                WHERE branch_name = ? AND floor_id = ? AND building_id = ?
            ''', (version_id, datetime.utcnow().isoformat(), branch_name, floor_id, building_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created version {version_number} for branch {branch_name}")
            return {
                "success": True,
                "version_id": version_id,
                "version_number": version_number,
                "data_hash": data_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            return {"success": False, "message": str(e)}
    
    def create_branch(self, branch_name: str, floor_id: str, building_id: str,
                     base_version_id: str, created_by: str, description: str = "") -> Dict[str, Any]:
        """Create a new branch"""
        try:
            # Check if branch already exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT branch_name FROM branches 
                WHERE branch_name = ? AND floor_id = ? AND building_id = ?
            ''', (branch_name, floor_id, building_id))
            
            if cursor.fetchone():
                conn.close()
                return {"success": False, "message": "Branch already exists"}
            
            # Create branch
            branch = Branch(
                branch_name=branch_name,
                floor_id=floor_id,
                building_id=building_id,
                base_version_id=base_version_id,
                current_version_id=base_version_id,
                created_by=created_by,
                description=description
            )
            
            cursor.execute('''
                INSERT INTO branches (
                    branch_name, floor_id, building_id, base_version_id, current_version_id,
                    status, created_by, created_at, last_updated, description, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                branch.branch_name, branch.floor_id, branch.building_id,
                branch.base_version_id, branch.current_version_id,
                branch.status.value, branch.created_by,
                branch.created_at.isoformat(), branch.last_updated.isoformat(),
                branch.description, json.dumps(branch.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created branch {branch_name}")
            return {"success": True, "branch_name": branch_name}
            
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return {"success": False, "message": str(e)}
    
    def get_branches(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get all branches for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM branches 
                WHERE floor_id = ? AND building_id = ?
                ORDER BY created_at DESC
            ''', (floor_id, building_id))
            
            branches = []
            for row in cursor.fetchall():
                branch = {
                    "branch_name": row[0],
                    "floor_id": row[1],
                    "building_id": row[2],
                    "base_version_id": row[3],
                    "current_version_id": row[4],
                    "status": row[5],
                    "created_by": row[6],
                    "created_at": row[7],
                    "last_updated": row[8],
                    "description": row[9],
                    "metadata": json.loads(row[10]) if row[10] else {}
                }
                branches.append(branch)
            
            conn.close()
            return {"success": True, "branches": branches}
            
        except Exception as e:
            logger.error(f"Failed to get branches: {e}")
            return {"success": False, "message": str(e)}
    
    def get_version_history(self, floor_id: str, building_id: str, branch_name: Optional[str] = None) -> Dict[str, Any]:
        """Get version history for a floor or branch"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if branch_name:
                cursor.execute('''
                    SELECT * FROM versions 
                    WHERE floor_id = ? AND building_id = ? AND branch_name = ?
                    ORDER BY created_at DESC
                ''', (floor_id, building_id, branch_name))
            else:
                cursor.execute('''
                    SELECT * FROM versions 
                    WHERE floor_id = ? AND building_id = ?
                    ORDER BY created_at DESC
                ''', (floor_id, building_id))
            
            versions = []
            for row in cursor.fetchall():
                version = {
                    "version_id": row[0],
                    "floor_id": row[1],
                    "building_id": row[2],
                    "branch_name": row[3],
                    "parent_version_id": row[4],
                    "version_type": row[5],
                    "version_number": row[6],
                    "commit_message": row[7],
                    "author": row[8],
                    "created_at": row[9],
                    "data_hash": row[10],
                    "data_size": row[11],
                    "metadata": json.loads(row[12]) if row[12] else {}
                }
                versions.append(version)
            
            conn.close()
            return {"success": True, "versions": versions}
            
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return {"success": False, "message": str(e)}
    
    def get_version_data(self, version_id: str) -> Dict[str, Any]:
        """Get version data"""
        try:
            version_file = self.storage_path / f"{version_id}.json"
            if not version_file.exists():
                return {"success": False, "message": "Version data not found"}
            
            with open(version_file, 'r') as f:
                data = json.load(f)
            
            return {"success": True, "data": data}
            
        except Exception as e:
            logger.error(f"Failed to get version data: {e}")
            return {"success": False, "message": str(e)}
    
    def create_merge_request(self, source_branch: str, target_branch: str,
                           floor_id: str, building_id: str, created_by: str,
                           description: str = "") -> Dict[str, Any]:
        """Create a merge request"""
        try:
            merge_id = str(uuid.uuid4())
            
            # Check for conflicts
            conflicts = self._detect_conflicts(source_branch, target_branch, floor_id, building_id)
            
            merge_request = MergeRequest(
                merge_id=merge_id,
                source_branch=source_branch,
                target_branch=target_branch,
                floor_id=floor_id,
                building_id=building_id,
                created_by=created_by,
                description=description,
                conflicts=conflicts,
                status=MergeStatus.CONFLICT if conflicts else MergeStatus.PENDING
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO merge_requests (
                    merge_id, source_branch, target_branch, floor_id, building_id,
                    status, created_by, created_at, conflicts, resolution_strategy,
                    description, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                merge_request.merge_id, merge_request.source_branch,
                merge_request.target_branch, merge_request.floor_id,
                merge_request.building_id, merge_request.status.value,
                merge_request.created_by, merge_request.created_at.isoformat(),
                json.dumps(merge_request.conflicts), merge_request.resolution_strategy,
                merge_request.description, json.dumps(merge_request.metadata)
            ))
            
            # Store conflicts
            for conflict in conflicts:
                conflict_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO conflicts (
                        conflict_id, merge_id, conflict_type, object_id, property_name,
                        source_value, target_value, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    conflict_id, merge_id, conflict["type"],
                    conflict.get("object_id"), conflict.get("property_name"),
                    json.dumps(conflict.get("source_value")),
                    json.dumps(conflict.get("target_value")),
                    datetime.utcnow().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created merge request {merge_id}")
            return {
                "success": True,
                "merge_id": merge_id,
                "conflicts": conflicts,
                "has_conflicts": len(conflicts) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to create merge request: {e}")
            return {"success": False, "message": str(e)}
    
    def resolve_conflict(self, conflict_id: str, resolution: str, resolved_by: str) -> Dict[str, Any]:
        """Resolve a conflict"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE conflicts SET 
                    resolution = ?, resolved_by = ?, resolved_at = ?
                WHERE conflict_id = ?
            ''', (resolution, resolved_by, datetime.utcnow().isoformat(), conflict_id))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "conflict_id": conflict_id}
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            return {"success": False, "message": str(e)}
    
    def execute_merge(self, merge_id: str, executed_by: str) -> Dict[str, Any]:
        """Execute a merge"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get merge request
            cursor.execute('SELECT * FROM merge_requests WHERE merge_id = ?', (merge_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Merge request not found"}
            
            # Check if all conflicts are resolved
            cursor.execute('''
                SELECT COUNT(*) FROM conflicts 
                WHERE merge_id = ? AND resolution IS NULL
            ''', (merge_id,))
            
            unresolved_conflicts = cursor.fetchone()[0]
            if unresolved_conflicts > 0:
                return {"success": False, "message": f"{unresolved_conflicts} conflicts unresolved"}
            
            # Perform merge
            # This is a simplified merge - in practice, you'd want more sophisticated logic
            source_branch = row[1]
            target_branch = row[2]
            floor_id = row[3]
            building_id = row[4]
            
            # Update target branch with source branch's current version
            cursor.execute('''
                SELECT current_version_id FROM branches 
                WHERE branch_name = ? AND floor_id = ? AND building_id = ?
            ''', (source_branch, floor_id, building_id))
            
            source_version = cursor.fetchone()[0]
            
            cursor.execute('''
                UPDATE branches SET current_version_id = ?, last_updated = ?
                WHERE branch_name = ? AND floor_id = ? AND building_id = ?
            ''', (source_version, datetime.utcnow().isoformat(), target_branch, floor_id, building_id))
            
            # Update merge request status
            cursor.execute('''
                UPDATE merge_requests SET 
                    status = ?, merged_at = ?, merged_by = ?
                WHERE merge_id = ?
            ''', (MergeStatus.COMPLETED.value, datetime.utcnow().isoformat(), executed_by, merge_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Executed merge {merge_id}")
            return {"success": True, "merge_id": merge_id}
            
        except Exception as e:
            logger.error(f"Failed to execute merge: {e}")
            return {"success": False, "message": str(e)}
    
    def add_annotation(self, version_id: str, floor_id: str, building_id: str,
                      title: str, content: str, author: str,
                      object_id: Optional[str] = None,
                      position_x: Optional[float] = None,
                      position_y: Optional[float] = None,
                      annotation_type: str = "note") -> Dict[str, Any]:
        """Add an annotation to a version"""
        try:
            annotation = Annotation(
                annotation_id=str(uuid.uuid4()),
                version_id=version_id,
                floor_id=floor_id,
                building_id=building_id,
                object_id=object_id,
                position_x=position_x,
                position_y=position_y,
                annotation_type=annotation_type,
                title=title,
                content=content,
                author=author
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO annotations (
                    annotation_id, version_id, floor_id, building_id, object_id,
                    position_x, position_y, annotation_type, title, content,
                    author, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                annotation.annotation_id, annotation.version_id,
                annotation.floor_id, annotation.building_id,
                annotation.object_id, annotation.position_x,
                annotation.position_y, annotation.annotation_type,
                annotation.title, annotation.content, annotation.author,
                annotation.created_at.isoformat(), annotation.updated_at.isoformat(),
                json.dumps(annotation.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "annotation_id": annotation.annotation_id}
            
        except Exception as e:
            logger.error(f"Failed to add annotation: {e}")
            return {"success": False, "message": str(e)}
    
    def get_annotations(self, version_id: str) -> Dict[str, Any]:
        """Get annotations for a version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM annotations WHERE version_id = ?
                ORDER BY created_at
            ''', (version_id,))
            
            annotations = []
            for row in cursor.fetchall():
                annotation = {
                    "annotation_id": row[0],
                    "version_id": row[1],
                    "floor_id": row[2],
                    "building_id": row[3],
                    "object_id": row[4],
                    "position_x": row[5],
                    "position_y": row[6],
                    "annotation_type": row[7],
                    "title": row[8],
                    "content": row[9],
                    "author": row[10],
                    "created_at": row[11],
                    "updated_at": row[12],
                    "metadata": json.loads(row[13]) if row[13] else {}
                }
                annotations.append(annotation)
            
            conn.close()
            return {"success": True, "annotations": annotations}
            
        except Exception as e:
            logger.error(f"Failed to get annotations: {e}")
            return {"success": False, "message": str(e)}
    
    def add_comment(self, parent_id: str, parent_type: str, content: str, author: str) -> Dict[str, Any]:
        """Add a comment to a version or annotation"""
        try:
            comment = Comment(
                comment_id=str(uuid.uuid4()),
                parent_id=parent_id,
                parent_type=parent_type,
                content=content,
                author=author
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO comments (
                    comment_id, parent_id, parent_type, author, content,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comment.comment_id, comment.parent_id, comment.parent_type,
                comment.author, comment.content, comment.created_at.isoformat(),
                comment.updated_at.isoformat(), json.dumps(comment.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "comment_id": comment.comment_id}
            
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return {"success": False, "message": str(e)}
    
    def get_comments(self, parent_id: str, parent_type: str) -> Dict[str, Any]:
        """Get comments for a version or annotation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM comments 
                WHERE parent_id = ? AND parent_type = ?
                ORDER BY created_at
            ''', (parent_id, parent_type))
            
            comments = []
            for row in cursor.fetchall():
                comment = {
                    "comment_id": row[0],
                    "parent_id": row[1],
                    "parent_type": row[2],
                    "author": row[3],
                    "content": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "metadata": json.loads(row[7]) if row[7] else {}
                }
                comments.append(comment)
            
            conn.close()
            return {"success": True, "comments": comments}
            
        except Exception as e:
            logger.error(f"Failed to get comments: {e}")
            return {"success": False, "message": str(e)}
    
    def search_annotations(self, floor_id: str, building_id: str, query: str) -> Dict[str, Any]:
        """Search annotations by content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM annotations 
                WHERE floor_id = ? AND building_id = ? 
                AND (title LIKE ? OR content LIKE ?)
                ORDER BY created_at DESC
            ''', (floor_id, building_id, f"%{query}%", f"%{query}%"))
            
            annotations = []
            for row in cursor.fetchall():
                annotation = {
                    "annotation_id": row[0],
                    "version_id": row[1],
                    "floor_id": row[2],
                    "building_id": row[3],
                    "object_id": row[4],
                    "position_x": row[5],
                    "position_y": row[6],
                    "annotation_type": row[7],
                    "title": row[8],
                    "content": row[9],
                    "author": row[10],
                    "created_at": row[11],
                    "updated_at": row[12],
                    "metadata": json.loads(row[13]) if row[13] else {}
                }
                annotations.append(annotation)
            
            conn.close()
            return {"success": True, "annotations": annotations, "query": query}
            
        except Exception as e:
            logger.error(f"Failed to search annotations: {e}")
            return {"success": False, "message": str(e)}
    
    def _generate_version_number(self, branch_name: str, version_type: VersionType) -> str:
        """Generate version number"""
        # Simplified version numbering - in practice, you'd want more sophisticated logic
        timestamp = datetime.utcnow().strftime("%Y%m%d.%H%M%S")
        return f"{branch_name}-{version_type.value}-{timestamp}"
    
    def _detect_conflicts(self, source_branch: str, target_branch: str,
                         floor_id: str, building_id: str) -> List[Dict[str, Any]]:
        """Detect conflicts between branches"""
        try:
            # Get current versions of both branches
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT current_version_id FROM branches 
                WHERE branch_name = ? AND floor_id = ? AND building_id = ?
            ''', (source_branch, floor_id, building_id))
            source_version = cursor.fetchone()
            
            cursor.execute('''
                SELECT current_version_id FROM branches 
                WHERE branch_name = ? AND floor_id = ? AND building_id = ?
            ''', (target_branch, floor_id, building_id))
            target_version = cursor.fetchone()
            
            if not source_version or not target_version:
                return []
            
            # Get version data
            source_data = self.get_version_data(source_version[0])
            target_data = self.get_version_data(target_version[0])
            
            if not source_data["success"] or not target_data["success"]:
                return []
            
            # Simple conflict detection - compare objects
            conflicts = []
            source_objects = source_data["data"].get("objects", [])
            target_objects = target_data["data"].get("objects", [])
            
            # Create object maps
            source_map = {obj.get("id"): obj for obj in source_objects}
            target_map = {obj.get("id"): obj for obj in target_objects}
            
            # Check for conflicts
            for obj_id in set(source_map.keys()) | set(target_map.keys()):
                if obj_id in source_map and obj_id in target_map:
                    # Object exists in both - check for modifications
                    if source_map[obj_id] != target_map[obj_id]:
                        conflicts.append({
                            "type": ConflictType.OBJECT_MODIFIED.value,
                            "object_id": obj_id,
                            "source_value": source_map[obj_id],
                            "target_value": target_map[obj_id]
                        })
                elif obj_id in source_map:
                    # Object only in source
                    conflicts.append({
                        "type": ConflictType.OBJECT_ADDED.value,
                        "object_id": obj_id,
                        "source_value": source_map[obj_id]
                    })
                else:
                    # Object only in target
                    conflicts.append({
                        "type": ConflictType.OBJECT_DELETED.value,
                        "object_id": obj_id,
                        "target_value": target_map[obj_id]
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return []

# Global service instance - lazy singleton
_version_control_service = None

def get_version_control_service() -> VersionControlService:
    """Get the global version control service instance (lazy singleton)"""
    global _version_control_service
    if _version_control_service is None:
        _version_control_service = VersionControlService()
    return _version_control_service

# For backward compatibility
version_control_service = get_version_control_service() 