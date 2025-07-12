"""
Annotation and Comment Thread System
Enables threaded comments on individual ArxObject elements with mentions and resolution
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class CommentStatus(Enum):
    """Comment status states"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ARCHIVED = "archived"
    SPAM = "spam"


class CommentType(Enum):
    """Types of comments"""
    GENERAL = "general"
    QUESTION = "question"
    SUGGESTION = "suggestion"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    REVIEW = "review"


@dataclass
class Comment:
    """Individual comment in a thread"""
    id: str
    thread_id: str
    author_id: str
    author_name: str
    content: str
    comment_type: CommentType
    status: CommentStatus
    created_at: datetime
    updated_at: datetime
    parent_id: Optional[str]
    mentions: List[str]
    metadata: Dict
    reactions: Dict[str, List[str]]  # reaction_type -> [user_ids]
    
    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []
        if self.metadata is None:
            self.metadata = {}
        if self.reactions is None:
            self.reactions = {}


@dataclass
class CommentThread:
    """Thread of comments on an ArxObject"""
    id: str
    draft_id: str
    arx_object_id: str
    object_type: str
    object_path: str
    title: str
    description: str
    status: CommentStatus
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_to: Optional[str]
    priority: str
    tags: List[str]
    comments: List[Comment]
    subscribers: List[str]
    
    def __post_init__(self):
        if self.comments is None:
            self.comments = []
        if self.subscribers is None:
            self.subscribers = []
        if self.tags is None:
            self.tags = []


@dataclass
class Annotation:
    """Visual annotation on an ArxObject"""
    id: str
    thread_id: str
    annotation_type: str
    coordinates: Dict
    style: Dict
    content: str
    created_at: datetime
    created_by: str
    
    def __post_init__(self):
        if self.style is None:
            self.style = {}


class AnnotationManager:
    """Manages annotation and comment threads"""
    
    def __init__(self):
        self.threads: Dict[str, CommentThread] = {}
        self.annotations: Dict[str, List[Annotation]] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_thread(
        self,
        draft_id: str,
        arx_object_id: str,
        object_type: str,
        object_path: str,
        title: str,
        description: str,
        created_by: str,
        priority: str = "normal",
        tags: List[str] = None
    ) -> CommentThread:
        """Create a new comment thread"""
        
        thread_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        thread = CommentThread(
            id=thread_id,
            draft_id=draft_id,
            arx_object_id=arx_object_id,
            object_type=object_type,
            object_path=object_path,
            title=title,
            description=description,
            status=CommentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            assigned_to=None,
            priority=priority,
            tags=tags or [],
            comments=[],
            subscribers=[created_by]
        )
        
        self.threads[thread_id] = thread
        
        # Initialize annotations list
        self.annotations[thread_id] = []
        
        # Add to user subscriptions
        if created_by not in self.user_subscriptions:
            self.user_subscriptions[created_by] = set()
        self.user_subscriptions[created_by].add(thread_id)
        
        self.logger.info(f"Created comment thread {thread_id} for object {arx_object_id}")
        return thread
    
    def add_comment(
        self,
        thread_id: str,
        author_id: str,
        author_name: str,
        content: str,
        comment_type: CommentType = CommentType.GENERAL,
        parent_id: Optional[str] = None,
        metadata: Dict = None
    ) -> Comment:
        """Add a comment to a thread"""
        
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")
        
        thread = self.threads[thread_id]
        
        # Extract mentions from content
        mentions = self._extract_mentions(content)
        
        # Create comment
        comment_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        comment = Comment(
            id=comment_id,
            thread_id=thread_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            comment_type=comment_type,
            status=CommentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            parent_id=parent_id,
            mentions=mentions,
            metadata=metadata or {},
            reactions={}
        )
        
        # Add to thread
        thread.comments.append(comment)
        thread.updated_at = now
        
        # Add subscribers for mentions
        for user_id in mentions:
            if user_id not in thread.subscribers:
                thread.subscribers.append(user_id)
            
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(thread_id)
        
        self.logger.info(f"Added comment {comment_id} to thread {thread_id}")
        return comment
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract user mentions from comment content"""
        # Pattern to match @username mentions
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, content)
        
        # Convert usernames to user IDs (in real implementation, this would query user database)
        user_ids = []
        for username in mentions:
            # This is a simplified mapping - in real implementation, query user database
            user_id = f"user-{username}"
            user_ids.append(user_id)
        
        return user_ids
    
    def reply_to_comment(
        self,
        comment_id: str,
        author_id: str,
        author_name: str,
        content: str,
        comment_type: CommentType = CommentType.GENERAL
    ) -> Comment:
        """Reply to a specific comment"""
        
        # Find the parent comment
        parent_comment = None
        parent_thread_id = None
        
        for thread in self.threads.values():
            for comment in thread.comments:
                if comment.id == comment_id:
                    parent_comment = comment
                    parent_thread_id = thread.id
                    break
            if parent_comment:
                break
        
        if not parent_comment:
            raise ValueError(f"Comment {comment_id} not found")
        
        # Add reply
        reply = self.add_comment(
            thread_id=parent_thread_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            comment_type=comment_type,
            parent_id=comment_id
        )
        
        return reply
    
    def update_comment(
        self,
        comment_id: str,
        user_id: str,
        new_content: str
    ) -> bool:
        """Update an existing comment"""
        
        for thread in self.threads.values():
            for comment in thread.comments:
                if comment.id == comment_id and comment.author_id == user_id:
                    comment.content = new_content
                    comment.updated_at = datetime.utcnow()
                    comment.mentions = self._extract_mentions(new_content)
                    
                    thread.updated_at = datetime.utcnow()
                    
                    self.logger.info(f"Updated comment {comment_id}")
                    return True
        
        return False
    
    def resolve_thread(self, thread_id: str, resolved_by: str, resolution_note: str = "") -> bool:
        """Mark a thread as resolved"""
        
        if thread_id not in self.threads:
            return False
        
        thread = self.threads[thread_id]
        thread.status = CommentStatus.RESOLVED
        thread.updated_at = datetime.utcnow()
        
        # Add resolution comment
        self.add_comment(
            thread_id=thread_id,
            author_id=resolved_by,
            author_name="System",
            content=f"Thread resolved{f': {resolution_note}' if resolution_note else ''}",
            comment_type=CommentType.GENERAL
        )
        
        self.logger.info(f"Resolved thread {thread_id}")
        return True
    
    def assign_thread(self, thread_id: str, assigned_to: str, assigned_by: str) -> bool:
        """Assign a thread to a user"""
        
        if thread_id not in self.threads:
            return False
        
        thread = self.threads[thread_id]
        thread.assigned_to = assigned_to
        thread.updated_at = datetime.utcnow()
        
        # Add assignment comment
        self.add_comment(
            thread_id=thread_id,
            author_id=assigned_by,
            author_name="System",
            content=f"Thread assigned to @{assigned_to}",
            comment_type=CommentType.GENERAL
        )
        
        # Add assignee to subscribers
        if assigned_to not in thread.subscribers:
            thread.subscribers.append(assigned_to)
        
        if assigned_to not in self.user_subscriptions:
            self.user_subscriptions[assigned_to] = set()
        self.user_subscriptions[assigned_to].add(thread_id)
        
        self.logger.info(f"Assigned thread {thread_id} to {assigned_to}")
        return True
    
    def add_reaction(
        self,
        comment_id: str,
        user_id: str,
        reaction_type: str
    ) -> bool:
        """Add a reaction to a comment"""
        
        for thread in self.threads.values():
            for comment in thread.comments:
                if comment.id == comment_id:
                    if reaction_type not in comment.reactions:
                        comment.reactions[reaction_type] = []
                    
                    if user_id not in comment.reactions[reaction_type]:
                        comment.reactions[reaction_type].append(user_id)
                    
                    self.logger.info(f"Added reaction {reaction_type} to comment {comment_id}")
                    return True
        
        return False
    
    def remove_reaction(
        self,
        comment_id: str,
        user_id: str,
        reaction_type: str
    ) -> bool:
        """Remove a reaction from a comment"""
        
        for thread in self.threads.values():
            for comment in thread.comments:
                if comment.id == comment_id:
                    if (reaction_type in comment.reactions and 
                        user_id in comment.reactions[reaction_type]):
                        comment.reactions[reaction_type].remove(user_id)
                        
                        if not comment.reactions[reaction_type]:
                            del comment.reactions[reaction_type]
                    
                    self.logger.info(f"Removed reaction {reaction_type} from comment {comment_id}")
                    return True
        
        return False
    
    def subscribe_to_thread(self, thread_id: str, user_id: str) -> bool:
        """Subscribe a user to a thread"""
        
        if thread_id not in self.threads:
            return False
        
        thread = self.threads[thread_id]
        
        if user_id not in thread.subscribers:
            thread.subscribers.append(user_id)
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(thread_id)
        
        self.logger.info(f"User {user_id} subscribed to thread {thread_id}")
        return True
    
    def unsubscribe_from_thread(self, thread_id: str, user_id: str) -> bool:
        """Unsubscribe a user from a thread"""
        
        if thread_id not in self.threads:
            return False
        
        thread = self.threads[thread_id]
        
        if user_id in thread.subscribers:
            thread.subscribers.remove(user_id)
        
        if user_id in self.user_subscriptions and thread_id in self.user_subscriptions[user_id]:
            self.user_subscriptions[user_id].remove(thread_id)
        
        self.logger.info(f"User {user_id} unsubscribed from thread {thread_id}")
        return True
    
    def get_thread(self, thread_id: str) -> Optional[CommentThread]:
        """Get a thread by ID"""
        return self.threads.get(thread_id)
    
    def get_threads_by_draft(self, draft_id: str) -> List[CommentThread]:
        """Get all threads for a draft"""
        return [
            thread for thread in self.threads.values()
            if thread.draft_id == draft_id
        ]
    
    def get_threads_by_object(self, arx_object_id: str) -> List[CommentThread]:
        """Get all threads for a specific ArxObject"""
        return [
            thread for thread in self.threads.values()
            if thread.arx_object_id == arx_object_id
        ]
    
    def get_user_threads(self, user_id: str) -> List[CommentThread]:
        """Get threads where user is subscribed or assigned"""
        user_threads = []
        
        for thread in self.threads.values():
            if (user_id in thread.subscribers or 
                thread.assigned_to == user_id or 
                thread.created_by == user_id):
                user_threads.append(thread)
        
        return user_threads
    
    def get_threads_by_status(self, status: CommentStatus) -> List[CommentThread]:
        """Get threads by status"""
        return [
            thread for thread in self.threads.values()
            if thread.status == status
        ]
    
    def search_threads(self, query: str, draft_id: Optional[str] = None) -> List[CommentThread]:
        """Search threads by content"""
        results = []
        query_lower = query.lower()
        
        for thread in self.threads.values():
            if draft_id and thread.draft_id != draft_id:
                continue
            
            # Search in thread title and description
            if (query_lower in thread.title.lower() or 
                query_lower in thread.description.lower()):
                results.append(thread)
                continue
            
            # Search in comments
            for comment in thread.comments:
                if query_lower in comment.content.lower():
                    results.append(thread)
                    break
        
        return results
    
    def add_annotation(
        self,
        thread_id: str,
        annotation_type: str,
        coordinates: Dict,
        content: str,
        created_by: str,
        style: Dict = None
    ) -> Annotation:
        """Add a visual annotation to a thread"""
        
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")
        
        annotation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        annotation = Annotation(
            id=annotation_id,
            thread_id=thread_id,
            annotation_type=annotation_type,
            coordinates=coordinates,
            style=style or {},
            content=content,
            created_at=now,
            created_by=created_by
        )
        
        self.annotations[thread_id].append(annotation)
        
        self.logger.info(f"Added annotation {annotation_id} to thread {thread_id}")
        return annotation
    
    def get_annotations(self, thread_id: str) -> List[Annotation]:
        """Get all annotations for a thread"""
        return self.annotations.get(thread_id, [])
    
    def get_thread_summary(self, thread_id: str) -> Dict:
        """Get comprehensive thread summary"""
        
        if thread_id not in self.threads:
            return {}
        
        thread = self.threads[thread_id]
        
        # Count comments by type
        comment_counts = {}
        for comment in thread.comments:
            comment_type = comment.comment_type.value
            comment_counts[comment_type] = comment_counts.get(comment_type, 0) + 1
        
        # Count reactions
        total_reactions = 0
        for comment in thread.comments:
            for reaction_users in comment.reactions.values():
                total_reactions += len(reaction_users)
        
        return {
            "id": thread.id,
            "draft_id": thread.draft_id,
            "arx_object_id": thread.arx_object_id,
            "object_type": thread.object_type,
            "object_path": thread.object_path,
            "title": thread.title,
            "description": thread.description,
            "status": thread.status.value,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "created_by": thread.created_by,
            "assigned_to": thread.assigned_to,
            "priority": thread.priority,
            "tags": thread.tags,
            "subscriber_count": len(thread.subscribers),
            "comment_count": len(thread.comments),
            "comment_counts": comment_counts,
            "total_reactions": total_reactions,
            "annotation_count": len(self.annotations.get(thread_id, [])),
            "comments": [
                {
                    "id": comment.id,
                    "author_id": comment.author_id,
                    "author_name": comment.author_name,
                    "content": comment.content,
                    "comment_type": comment.comment_type.value,
                    "status": comment.status.value,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat(),
                    "parent_id": comment.parent_id,
                    "mentions": comment.mentions,
                    "reactions": comment.reactions
                }
                for comment in thread.comments
            ],
            "annotations": [
                {
                    "id": annotation.id,
                    "annotation_type": annotation.annotation_type,
                    "coordinates": annotation.coordinates,
                    "style": annotation.style,
                    "content": annotation.content,
                    "created_at": annotation.created_at.isoformat(),
                    "created_by": annotation.created_by
                }
                for annotation in self.annotations.get(thread_id, [])
            ]
        }


# Global annotation manager instance
annotation_manager = AnnotationManager() 