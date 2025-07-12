"""
BIM Collaboration Features

This module provides comprehensive BIM collaboration functionality:
- Real-time collaboration
- Version control
- Conflict resolution
- Team coordination
- Change tracking
- Permission management
"""

import logging
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from collections import defaultdict
import threading
import queue

from models.bim import (
    BIMElementBase, BIMSystem, BIMRelationship, BIMModel,
    Room, Wall, Door, Window, Device, SystemType, DeviceCategory
)
from services.bim_validator import BIMValidator, ValidationLevel
from utils.errors import CollaborationError, ConflictError, PermissionError

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """BIM collaboration modes"""
    REAL_TIME = "real_time"
    ASYNC = "async"
    VERSION_CONTROL = "version_control"
    REVIEW = "review"


class UserRole(Enum):
    """User roles in collaboration"""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    REVIEWER = "reviewer"


class ChangeType(Enum):
    """Types of changes in collaboration"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"
    RESIZE = "resize"
    PROPERTY_CHANGE = "property_change"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    LAST_WRITER_WINS = "last_writer_wins"
    MERGE = "merge"
    REJECT = "reject"


@dataclass
class User:
    """Collaboration user"""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: Set[str] = field(default_factory=set)
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None


@dataclass
class Change:
    """BIM change record"""
    change_id: str
    user_id: str
    timestamp: datetime
    change_type: ChangeType
    element_id: str
    element_type: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Version:
    """BIM model version"""
    version_id: str
    version_number: int
    timestamp: datetime
    user_id: str
    description: str
    changes: List[Change] = field(default_factory=list)
    model_snapshot: Optional[Dict[str, Any]] = None
    parent_version: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Conflict:
    """BIM collaboration conflict"""
    conflict_id: str
    element_id: str
    user_id_1: str
    user_id_2: str
    change_1: Change
    change_2: Change
    conflict_type: str
    severity: float  # 0.0 to 1.0
    resolution: Optional[ConflictResolution] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class CollaborationSession:
    """BIM collaboration session"""
    session_id: str
    model_id: str
    users: Dict[str, User] = field(default_factory=dict)
    active_changes: Dict[str, Change] = field(default_factory=dict)
    conflicts: List[Conflict] = field(default_factory=list)
    version_history: List[Version] = field(default_factory=list)
    permissions: Dict[str, Set[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BIMCollaborationService:
    """Comprehensive BIM collaboration service"""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.validator = BIMValidator()
        self.change_queue = queue.Queue()
        self.lock = threading.Lock()
        
        # Start background processing
        self._start_background_processing()
    
    def _start_background_processing(self):
        """Start background processing for collaboration."""
        def process_changes():
            while True:
                try:
                    change_data = self.change_queue.get(timeout=1)
                    self._process_change(change_data)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing change: {e}")
        
        thread = threading.Thread(target=process_changes, daemon=True)
        thread.start()
    
    def create_session(self, model_id: str, owner_id: str, 
                      owner_username: str, owner_email: str) -> str:
        """
        Create a new collaboration session.
        
        Args:
            model_id: ID of the BIM model
            owner_id: ID of the session owner
            owner_username: Username of the owner
            owner_email: Email of the owner
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Create owner user
        owner = User(
            user_id=owner_id,
            username=owner_username,
            email=owner_email,
            role=UserRole.OWNER,
            permissions={'read', 'write', 'admin', 'delete'}
        )
        
        # Create session
        session = CollaborationSession(
            session_id=session_id,
            model_id=model_id,
            users={owner_id: owner},
            permissions={owner_id: {'read', 'write', 'admin', 'delete'}}
        )
        
        with self.lock:
            self.sessions[session_id] = session
        
        logger.info(f"Created collaboration session {session_id} for model {model_id}")
        return session_id
    
    def join_session(self, session_id: str, user_id: str, username: str, 
                    email: str, role: UserRole = UserRole.VIEWER) -> bool:
        """
        Join an existing collaboration session.
        
        Args:
            session_id: Session ID to join
            user_id: User ID
            username: Username
            email: User email
            role: User role
            
        Returns:
            True if successfully joined
        """
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            # Create user
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                permissions=self._get_permissions_for_role(role)
            )
            
            session.users[user_id] = user
            session.permissions[user_id] = user.permissions
            session.last_activity = datetime.now(timezone.utc)
            
            logger.info(f"User {user_id} joined session {session_id} as {role.value}")
            return True
    
    def leave_session(self, session_id: str, user_id: str) -> bool:
        """
        Leave a collaboration session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            True if successfully left
        """
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            if user_id not in session.users:
                raise CollaborationError(f"User {user_id} not in session {session_id}")
            
            # Remove user
            del session.users[user_id]
            if user_id in session.permissions:
                del session.permissions[user_id]
            
            session.last_activity = datetime.now(timezone.utc)
            
            logger.info(f"User {user_id} left session {session_id}")
            return True
    
    def make_change(self, session_id: str, user_id: str, 
                   change_type: ChangeType, element_id: str,
                   element_type: str, new_value: Dict[str, Any],
                   old_value: Optional[Dict[str, Any]] = None,
                   description: str = "") -> str:
        """
        Make a change to the BIM model.
        
        Args:
            session_id: Session ID
            user_id: User ID
            change_type: Type of change
            element_id: Element ID
            element_type: Element type
            new_value: New value
            old_value: Old value
            description: Change description
            
        Returns:
            Change ID
        """
        # Check permissions
        if not self._check_permission(session_id, user_id, 'write'):
            raise PermissionError(f"User {user_id} does not have write permission")
        
        # Create change
        change = Change(
            change_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            change_type=change_type,
            element_id=element_id,
            element_type=element_type,
            old_value=old_value,
            new_value=new_value,
            description=description
        )
        
        # Add to session
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            session.active_changes[change.change_id] = change
            session.last_activity = datetime.now(timezone.utc)
        
        # Queue for processing
        self.change_queue.put({
            'session_id': session_id,
            'change': change
        })
        
        logger.info(f"Change {change.change_id} queued for processing")
        return change.change_id
    
    def _process_change(self, change_data: Dict[str, Any]):
        """Process a change in the background."""
        session_id = change_data['session_id']
        change = change_data['change']
        
        try:
            with self.lock:
                if session_id not in self.sessions:
                    return
                
                session = self.sessions[session_id]
                
                # Check for conflicts
                conflicts = self._detect_conflicts(session, change)
                
                if conflicts:
                    # Handle conflicts
                    for conflict in conflicts:
                        session.conflicts.append(conflict)
                        logger.warning(f"Conflict detected: {conflict.conflict_id}")
                else:
                    # Apply change
                    self._apply_change(session, change)
                    
                    # Create version if needed
                    if len(session.active_changes) % 10 == 0:  # Every 10 changes
                        self._create_version(session, change.user_id, "Auto-save")
        
        except Exception as e:
            logger.error(f"Error processing change {change.change_id}: {e}")
    
    def _detect_conflicts(self, session: CollaborationSession, 
                         new_change: Change) -> List[Conflict]:
        """Detect conflicts with existing changes."""
        conflicts = []
        
        for existing_change in session.active_changes.values():
            if (existing_change.element_id == new_change.element_id and
                existing_change.change_id != new_change.change_id):
                
                # Check for conflicts
                if self._changes_conflict(existing_change, new_change):
                    conflict = Conflict(
                        conflict_id=str(uuid.uuid4()),
                        element_id=new_change.element_id,
                        user_id_1=existing_change.user_id,
                        user_id_2=new_change.user_id,
                        change_1=existing_change,
                        change_2=new_change,
                        conflict_type="element_modification",
                        severity=0.8
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _changes_conflict(self, change1: Change, change2: Change) -> bool:
        """Check if two changes conflict."""
        # Same element, different users, overlapping time window
        time_diff = abs((change1.timestamp - change2.timestamp).total_seconds())
        
        return (change1.user_id != change2.user_id and
                change1.element_id == change2.element_id and
                time_diff < 300)  # 5 minutes window
    
    def _apply_change(self, session: CollaborationSession, change: Change):
        """Apply a change to the session."""
        # In a real implementation, this would update the actual BIM model
        # For now, we just track the change
        logger.info(f"Applied change {change.change_id} to element {change.element_id}")
    
    def _create_version(self, session: CollaborationSession, user_id: str, 
                       description: str) -> str:
        """Create a new version of the model."""
        version_id = str(uuid.uuid4())
        version_number = len(session.version_history) + 1
        
        # Get parent version
        parent_version = None
        if session.version_history:
            parent_version = session.version_history[-1].version_id
        
        version = Version(
            version_id=version_id,
            version_number=version_number,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            description=description,
            changes=list(session.active_changes.values()),
            parent_version=parent_version
        )
        
        session.version_history.append(version)
        session.active_changes.clear()  # Clear active changes after versioning
        
        logger.info(f"Created version {version_id} (v{version_number})")
        return version_id
    
    def resolve_conflict(self, session_id: str, conflict_id: str, 
                        resolution: ConflictResolution, 
                        resolved_by: str) -> bool:
        """
        Resolve a conflict.
        
        Args:
            session_id: Session ID
            conflict_id: Conflict ID
            resolution: Resolution strategy
            resolved_by: User ID who resolved the conflict
            
        Returns:
            True if successfully resolved
        """
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            # Find conflict
            conflict = None
            for c in session.conflicts:
                if c.conflict_id == conflict_id:
                    conflict = c
                    break
            
            if not conflict:
                raise CollaborationError(f"Conflict {conflict_id} not found")
            
            # Apply resolution
            conflict.resolution = resolution
            conflict.resolved_by = resolved_by
            conflict.resolved_at = datetime.now(timezone.utc)
            
            # Apply resolution strategy
            if resolution == ConflictResolution.LAST_WRITER_WINS:
                # Keep the most recent change
                if conflict.change_1.timestamp > conflict.change_2.timestamp:
                    self._apply_change(session, conflict.change_1)
                else:
                    self._apply_change(session, conflict.change_2)
            
            elif resolution == ConflictResolution.MERGE:
                # Merge changes (simplified)
                merged_change = self._merge_changes(conflict.change_1, conflict.change_2)
                self._apply_change(session, merged_change)
            
            elif resolution == ConflictResolution.REJECT:
                # Reject both changes
                pass  # Don't apply either change
            
            logger.info(f"Resolved conflict {conflict_id} with {resolution.value}")
            return True
    
    def _merge_changes(self, change1: Change, change2: Change) -> Change:
        """Merge two conflicting changes."""
        # Create merged change
        merged_value = change1.new_value.copy() if change1.new_value else {}
        
        if change2.new_value:
            merged_value.update(change2.new_value)
        
        return Change(
            change_id=str(uuid.uuid4()),
            user_id=f"{change1.user_id}+{change2.user_id}",
            timestamp=datetime.now(timezone.utc),
            change_type=change1.change_type,
            element_id=change1.element_id,
            element_type=change1.element_type,
            old_value=change1.old_value,
            new_value=merged_value,
            description=f"Merged changes from {change1.user_id} and {change2.user_id}"
        )
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get session status.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session status information
        """
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            return {
                'session_id': session_id,
                'model_id': session.model_id,
                'user_count': len(session.users),
                'active_changes': len(session.active_changes),
                'conflicts': len(session.conflicts),
                'versions': len(session.version_history),
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'users': [
                    {
                        'user_id': user.user_id,
                        'username': user.username,
                        'role': user.role.value,
                        'last_active': user.last_active.isoformat()
                    }
                    for user in session.users.values()
                ]
            }
    
    def get_changes(self, session_id: str, user_id: str, 
                   since_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get changes for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            since_timestamp: Get changes since this timestamp
            
        Returns:
            List of changes
        """
        if not self._check_permission(session_id, user_id, 'read'):
            raise PermissionError(f"User {user_id} does not have read permission")
        
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            changes = []
            for change in session.active_changes.values():
                if since_timestamp is None or change.timestamp >= since_timestamp:
                    changes.append({
                        'change_id': change.change_id,
                        'user_id': change.user_id,
                        'timestamp': change.timestamp.isoformat(),
                        'change_type': change.change_type.value,
                        'element_id': change.element_id,
                        'element_type': change.element_type,
                        'description': change.description
                    })
            
            return changes
    
    def get_conflicts(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get conflicts for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            List of conflicts
        """
        if not self._check_permission(session_id, user_id, 'read'):
            raise PermissionError(f"User {user_id} does not have read permission")
        
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            conflicts = []
            for conflict in session.conflicts:
                if conflict.resolution is None:  # Only unresolved conflicts
                    conflicts.append({
                        'conflict_id': conflict.conflict_id,
                        'element_id': conflict.element_id,
                        'user_id_1': conflict.user_id_1,
                        'user_id_2': conflict.user_id_2,
                        'conflict_type': conflict.conflict_type,
                        'severity': conflict.severity,
                        'change_1': {
                            'change_id': conflict.change_1.change_id,
                            'description': conflict.change_1.description,
                            'timestamp': conflict.change_1.timestamp.isoformat()
                        },
                        'change_2': {
                            'change_id': conflict.change_2.change_id,
                            'description': conflict.change_2.description,
                            'timestamp': conflict.change_2.timestamp.isoformat()
                        }
                    })
            
            return conflicts
    
    def get_versions(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            List of versions
        """
        if not self._check_permission(session_id, user_id, 'read'):
            raise PermissionError(f"User {user_id} does not have read permission")
        
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            versions = []
            for version in session.version_history:
                versions.append({
                    'version_id': version.version_id,
                    'version_number': version.version_number,
                    'timestamp': version.timestamp.isoformat(),
                    'user_id': version.user_id,
                    'description': version.description,
                    'change_count': len(version.changes),
                    'parent_version': version.parent_version,
                    'tags': version.tags
                })
            
            return versions
    
    def _check_permission(self, session_id: str, user_id: str, permission: str) -> bool:
        """Check if user has permission."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if user_id not in session.permissions:
            return False
        
        return permission in session.permissions[user_id]
    
    def _get_permissions_for_role(self, role: UserRole) -> Set[str]:
        """Get permissions for a role."""
        permissions = {'read'}
        
        if role in [UserRole.OWNER, UserRole.ADMIN]:
            permissions.update({'write', 'admin', 'delete'})
        elif role == UserRole.EDITOR:
            permissions.update({'write'})
        elif role == UserRole.REVIEWER:
            permissions.update({'write', 'review'})
        
        return permissions
    
    def create_branch(self, session_id: str, user_id: str, 
                     branch_name: str, description: str) -> str:
        """
        Create a new branch for collaboration.
        
        Args:
            session_id: Session ID
            user_id: User ID
            branch_name: Branch name
            description: Branch description
            
        Returns:
            Branch ID
        """
        if not self._check_permission(session_id, user_id, 'write'):
            raise PermissionError(f"User {user_id} does not have write permission")
        
        # Create new session for branch
        branch_session_id = str(uuid.uuid4())
        
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            parent_session = self.sessions[session_id]
            
            # Create branch session
            branch_session = CollaborationSession(
                session_id=branch_session_id,
                model_id=parent_session.model_id,
                users=parent_session.users.copy(),
                permissions=parent_session.permissions.copy()
            )
            
            # Copy version history
            branch_session.version_history = parent_session.version_history.copy()
            
            self.sessions[branch_session_id] = branch_session
        
        logger.info(f"Created branch {branch_session_id} from session {session_id}")
        return branch_session_id
    
    def merge_branch(self, target_session_id: str, source_session_id: str,
                    user_id: str, merge_strategy: ConflictResolution) -> bool:
        """
        Merge a branch into the target session.
        
        Args:
            target_session_id: Target session ID
            source_session_id: Source session ID
            user_id: User ID performing merge
            merge_strategy: Merge strategy
            
        Returns:
            True if successfully merged
        """
        if not self._check_permission(target_session_id, user_id, 'write'):
            raise PermissionError(f"User {user_id} does not have write permission")
        
        with self.lock:
            if target_session_id not in self.sessions or source_session_id not in self.sessions:
                raise CollaborationError("One or both sessions not found")
            
            target_session = self.sessions[target_session_id]
            source_session = self.sessions[source_session_id]
            
            # Merge changes
            for change in source_session.active_changes.values():
                # Check for conflicts
                conflicts = self._detect_conflicts(target_session, change)
                
                if conflicts:
                    # Apply merge strategy
                    if merge_strategy == ConflictResolution.MANUAL:
                        # Leave conflicts for manual resolution
                        target_session.conflicts.extend(conflicts)
                    elif merge_strategy == ConflictResolution.LAST_WRITER_WINS:
                        # Apply the most recent change
                        if not conflicts:  # No actual conflicts, just apply
                            self._apply_change(target_session, change)
                    elif merge_strategy == ConflictResolution.MERGE:
                        # Merge changes
                        merged_change = self._merge_changes(conflicts[0].change_1, conflicts[0].change_2)
                        self._apply_change(target_session, merged_change)
                else:
                    # No conflicts, apply change
                    self._apply_change(target_session, change)
            
            # Create merge version
            self._create_version(target_session, user_id, f"Merged from {source_session_id}")
            
            logger.info(f"Merged session {source_session_id} into {target_session_id}")
            return True
    
    def export_collaboration_data(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Export collaboration data for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Collaboration data
        """
        if not self._check_permission(session_id, user_id, 'read'):
            raise PermissionError(f"User {user_id} does not have read permission")
        
        with self.lock:
            if session_id not in self.sessions:
                raise CollaborationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            return {
                'session_id': session_id,
                'model_id': session.model_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'users': [
                    {
                        'user_id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role.value,
                        'last_active': user.last_active.isoformat()
                    }
                    for user in session.users.values()
                ],
                'changes': [
                    {
                        'change_id': change.change_id,
                        'user_id': change.user_id,
                        'timestamp': change.timestamp.isoformat(),
                        'change_type': change.change_type.value,
                        'element_id': change.element_id,
                        'element_type': change.element_type,
                        'description': change.description
                    }
                    for change in session.active_changes.values()
                ],
                'conflicts': [
                    {
                        'conflict_id': conflict.conflict_id,
                        'element_id': conflict.element_id,
                        'conflict_type': conflict.conflict_type,
                        'severity': conflict.severity,
                        'resolution': conflict.resolution.value if conflict.resolution else None
                    }
                    for conflict in session.conflicts
                ],
                'versions': [
                    {
                        'version_id': version.version_id,
                        'version_number': version.version_number,
                        'timestamp': version.timestamp.isoformat(),
                        'user_id': version.user_id,
                        'description': version.description
                    }
                    for version in session.version_history
                ]
            } 