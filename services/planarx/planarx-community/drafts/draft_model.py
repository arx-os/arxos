"""
Planarx Community - Draft System

Draft management system for creators to save, edit, and version their designs
before submitting them for community review. Includes autosave functionality,
version control, and draft collaboration features.
"""

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DraftStatus(str, Enum):
    """Draft status enumeration."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DraftVisibility(str, Enum):
    """Draft visibility levels."""

    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


@dataclass
class DraftVersion:
    """Represents a version of a draft."""

    version_id: str
    version_number: int
    created_at: datetime
    created_by: str
    changes_summary: str
    file_path: str
    metadata: Dict[str, Any]
    is_autosave: bool = False


@dataclass
class DraftCollaborator:
    """Represents a collaborator on a draft."""

    user_id: str
    username: str
    role: str  # owner, editor, viewer
    joined_at: datetime
    permissions: List[str]


@dataclass
class DraftComment:
    """Represents a comment on a draft."""

    comment_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    parent_comment_id: Optional[str] = None
    resolved: bool = False


@dataclass
class Draft:
    """Main draft model for the Planarx community."""

    draft_id: str
    title: str
    description: str
    creator_id: str
    creator_name: str
    status: DraftStatus
    visibility: DraftVisibility
    category: str
    tags: List[str]
    current_version: int
    versions: List[DraftVersion]
    collaborators: List[DraftCollaborator]
    comments: List[DraftComment]
    funding_goal: Optional[float]
    project_duration: Optional[int]
    team_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_autosave: Optional[datetime]
    metadata: Dict[str, Any]


class DraftService:
    """Service for managing drafts and their lifecycle."""

    def __init__(self):
        """Initialize the draft service."""
        self.drafts: Dict[str, Draft] = {}
        self.autosave_interval = 300  # 5 minutes
        self.max_versions = 50
        self.max_draft_size = 100 * 1024 * 1024  # 100MB

    async def create_draft(
        self,
        creator_id: str,
        creator_name: str,
        title: str,
        description: str,
        category: str,
        tags: List[str] = None,
        funding_goal: Optional[float] = None,
        project_duration: Optional[int] = None,
        team_size: Optional[int] = None,
    ) -> Draft:
        """Create a new draft."""
        try:
            draft_id = str(uuid.uuid4())

            # Create initial version
            initial_version = DraftVersion(
                version_id=str(uuid.uuid4()),
                version_number=1,
                created_at=datetime.now(),
                created_by=creator_id,
                changes_summary="Initial draft creation",
                file_path=f"drafts/{draft_id}/v1.json",
                metadata={"files": [], "arxide_data": {}},
                is_autosave=False,
            )

            # Create draft
            draft = Draft(
                draft_id=draft_id,
                title=title,
                description=description,
                creator_id=creator_id,
                creator_name=creator_name,
                status=DraftStatus.DRAFT,
                visibility=DraftVisibility.PRIVATE,
                category=category,
                tags=tags or [],
                current_version=1,
                versions=[initial_version],
                collaborators=[
                    DraftCollaborator(
                        user_id=creator_id,
                        username=creator_name,
                        role="owner",
                        joined_at=datetime.now(),
                        permissions=["read", "write", "delete", "share"],
                    )
                ],
                comments=[],
                funding_goal=funding_goal,
                project_duration=project_duration,
                team_size=team_size,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_autosave=None,
                metadata={"created_from": "manual"},
            )

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Created draft {draft_id} for user {creator_id}")
            return draft

        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            raise

    async def get_draft(self, draft_id: str, user_id: str) -> Optional[Draft]:
        """Get a draft by ID with permission check."""
        try:
            draft = self.drafts.get(draft_id)
            if not draft:
                return None

            # Check if user has access
            if not self._can_access_draft(draft, user_id):
                return None

            return draft

        except Exception as e:
            logger.error(f"Error getting draft {draft_id}: {e}")
            return None

    async def get_user_drafts(
        self,
        user_id: str,
        status: Optional[DraftStatus] = None,
        visibility: Optional[DraftVisibility] = None,
    ) -> List[Draft]:
        """Get drafts for a user with optional filtering."""
        try:
            user_drafts = []

            for draft in self.drafts.values():
                # Check if user is creator or collaborator
                if not self._can_access_draft(draft, user_id):
                    continue

                # Apply filters
                if status and draft.status != status:
                    continue
                if visibility and draft.visibility != visibility:
                    continue

                user_drafts.append(draft)

            # Sort by updated_at descending
            user_drafts.sort(key=lambda x: x.updated_at, reverse=True)

            return user_drafts

        except Exception as e:
            logger.error(f"Error getting drafts for user {user_id}: {e}")
            return []

    async def update_draft(
        self, draft_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[Draft]:
        """Update a draft with new data."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft:
                return None

            # Check write permission
            if not self._can_write_draft(draft, user_id):
                return None

            # Create new version if there are significant changes
            should_create_version = self._should_create_version(updates)

            if should_create_version:
                new_version = DraftVersion(
                    version_id=str(uuid.uuid4()),
                    version_number=draft.current_version + 1,
                    created_at=datetime.now(),
                    created_by=user_id,
                    changes_summary=updates.get("changes_summary", "Draft updated"),
                    file_path=f"drafts/{draft_id}/v{draft.current_version + 1}.json",
                    metadata=updates.get("metadata", {}),
                    is_autosave=False,
                )

                draft.versions.append(new_version)
                draft.current_version += 1

                # Limit versions
                if len(draft.versions) > self.max_versions:
                    draft.versions = draft.versions[-self.max_versions :]

            # Update draft fields
            for key, value in updates.items():
                if hasattr(draft, key) and key not in [
                    "draft_id",
                    "creator_id",
                    "created_at",
                ]:
                    setattr(draft, key, value)

            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Updated draft {draft_id} by user {user_id}")
            return draft

        except Exception as e:
            logger.error(f"Error updating draft {draft_id}: {e}")
            return None

    async def autosave_draft(
        self, draft_id: str, user_id: str, data: Dict[str, Any]
    ) -> bool:
        """Autosave draft changes."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft:
                return False

            # Check if autosave is needed
            if draft.last_autosave and datetime.now() - draft.last_autosave < timedelta(
                seconds=self.autosave_interval
            ):
                return True

            # Create autosave version
            autosave_version = DraftVersion(
                version_id=str(uuid.uuid4()),
                version_number=draft.current_version + 1,
                created_at=datetime.now(),
                created_by=user_id,
                changes_summary="Autosave",
                file_path=f"drafts/{draft_id}/autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                metadata=data,
                is_autosave=True,
            )

            draft.versions.append(autosave_version)
            draft.current_version += 1
            draft.last_autosave = datetime.now()
            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.debug(f"Autosaved draft {draft_id}")
            return True

        except Exception as e:
            logger.error(f"Error autosaving draft {draft_id}: {e}")
            return False

    async def add_collaborator(
        self,
        draft_id: str,
        owner_id: str,
        collaborator_id: str,
        collaborator_name: str,
        role: str = "editor",
        permissions: List[str] = None,
    ) -> bool:
        """Add a collaborator to a draft."""
        try:
            draft = await self.get_draft(draft_id, owner_id)
            if not draft or draft.creator_id != owner_id:
                return False

            # Check if collaborator already exists
            for collaborator in draft.collaborators:
                if collaborator.user_id == collaborator_id:
                    return False

            # Add collaborator
            new_collaborator = DraftCollaborator(
                user_id=collaborator_id,
                username=collaborator_name,
                role=role,
                joined_at=datetime.now(),
                permissions=permissions or ["read", "write"],
            )

            draft.collaborators.append(new_collaborator)
            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Added collaborator {collaborator_id} to draft {draft_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding collaborator to draft {draft_id}: {e}")
            return False

    async def remove_collaborator(
        self, draft_id: str, owner_id: str, collaborator_id: str
    ) -> bool:
        """Remove a collaborator from a draft."""
        try:
            draft = await self.get_draft(draft_id, owner_id)
            if not draft or draft.creator_id != owner_id:
                return False

            # Remove collaborator
            draft.collaborators = [
                c for c in draft.collaborators if c.user_id != collaborator_id
            ]

            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Removed collaborator {collaborator_id} from draft {draft_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing collaborator from draft {draft_id}: {e}")
            return False

    async def add_comment(
        self,
        draft_id: str,
        user_id: str,
        username: str,
        content: str,
        parent_comment_id: Optional[str] = None,
    ) -> Optional[DraftComment]:
        """Add a comment to a draft."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft:
                return None

            comment = DraftComment(
                comment_id=str(uuid.uuid4()),
                user_id=user_id,
                username=username,
                content=content,
                created_at=datetime.now(),
                parent_comment_id=parent_comment_id,
            )

            draft.comments.append(comment)
            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Added comment to draft {draft_id} by user {user_id}")
            return comment

        except Exception as e:
            logger.error(f"Error adding comment to draft {draft_id}: {e}")
            return None

    async def resolve_comment(
        self, draft_id: str, user_id: str, comment_id: str
    ) -> bool:
        """Resolve a comment."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft:
                return False

            # Find and resolve comment
            for comment in draft.comments:
                if comment.comment_id == comment_id:
                    comment.resolved = True
                    draft.updated_at = datetime.now()

                    # Save draft
                    await self._save_draft(draft)

                    logger.info(f"Resolved comment {comment_id} in draft {draft_id}")
                    return True

            return False

        except Exception as e:
            logger.error(
                f"Error resolving comment {comment_id} in draft {draft_id}: {e}"
            )
            return False

    async def change_visibility(
        self, draft_id: str, user_id: str, visibility: DraftVisibility
    ) -> bool:
        """Change draft visibility."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft or draft.creator_id != user_id:
                return False

            draft.visibility = visibility
            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Changed visibility of draft {draft_id} to {visibility}")
            return True

        except Exception as e:
            logger.error(f"Error changing visibility of draft {draft_id}: {e}")
            return False

    async def submit_for_review(self, draft_id: str, user_id: str) -> bool:
        """Submit draft for community review."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft or draft.creator_id != user_id:
                return False

            # Validate draft is ready for submission
            if not self._validate_draft_for_submission(draft):
                return False

            draft.status = DraftStatus.IN_REVIEW
            draft.updated_at = datetime.now()

            # Save draft
            await self._save_draft(draft)

            logger.info(f"Submitted draft {draft_id} for review")
            return True

        except Exception as e:
            logger.error(f"Error submitting draft {draft_id} for review: {e}")
            return False

    async def delete_draft(self, draft_id: str, user_id: str) -> bool:
        """Delete a draft."""
        try:
            draft = await self.get_draft(draft_id, user_id)
            if not draft or draft.creator_id != user_id:
                return False

            # Remove from storage
            del self.drafts[draft_id]

            # Clean up files
            await self._cleanup_draft_files(draft_id)

            logger.info(f"Deleted draft {draft_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting draft {draft_id}: {e}")
            return False

    async def get_draft_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get draft statistics for a user."""
        try:
            user_drafts = await self.get_user_drafts(user_id)

            stats = {
                "total_drafts": len(user_drafts),
                "drafts_by_status": {},
                "drafts_by_category": {},
                "total_versions": 0,
                "total_comments": 0,
                "total_collaborators": 0,
            }

            for draft in user_drafts:
                # Status counts
                status = draft.status.value
                stats["drafts_by_status"][status] = (
                    stats["drafts_by_status"].get(status, 0) + 1
                )

                # Category counts
                category = draft.category
                stats["drafts_by_category"][category] = (
                    stats["drafts_by_category"].get(category, 0) + 1
                )

                # Version and comment counts
                stats["total_versions"] += len(draft.versions)
                stats["total_comments"] += len(draft.comments)
                stats["total_collaborators"] += len(draft.collaborators)

            return stats

        except Exception as e:
            logger.error(f"Error getting draft statistics for user {user_id}: {e}")
            return {}

    # Helper methods

    def _can_access_draft(self, draft: Draft, user_id: str) -> bool:
        """Check if user can access the draft."""
        # Creator can always access
        if draft.creator_id == user_id:
            return True

        # Check collaborators
        for collaborator in draft.collaborators:
            if collaborator.user_id == user_id:
                return True

        # Public drafts can be viewed by anyone
        if draft.visibility == DraftVisibility.PUBLIC:
            return True

        return False

    def _can_write_draft(self, draft: Draft, user_id: str) -> bool:
        """Check if user can write to the draft."""
        # Creator can always write
        if draft.creator_id == user_id:
            return True

        # Check collaborator permissions
        for collaborator in draft.collaborators:
            if collaborator.user_id == user_id and "write" in collaborator.permissions:
                return True

        return False

    def _should_create_version(self, updates: Dict[str, Any]) -> bool:
        """Determine if a new version should be created."""
        # Create version for significant changes
        significant_fields = [
            "title",
            "description",
            "category",
            "tags",
            "funding_goal",
        ]

        for field in significant_fields:
            if field in updates:
                return True

        # Create version for file changes
        if "metadata" in updates and "files" in updates["metadata"]:
            return True

        return False

    def _validate_draft_for_submission(self, draft: Draft) -> bool:
        """Validate that a draft is ready for submission."""
        # Check required fields
        if not draft.title or not draft.description:
            return False

        # Check if draft has content
        if not draft.versions or len(draft.versions) == 0:
            return False

        # Check if draft is in draft status
        if draft.status != DraftStatus.DRAFT:
            return False

        return True

    async def _save_draft(self, draft: Draft) -> bool:
        """Save draft to storage."""
        try:
            # In a real implementation, this would save to database
            self.drafts[draft.draft_id] = draft
            return True
        except Exception as e:
            logger.error(f"Error saving draft {draft.draft_id}: {e}")
            return False

    async def _cleanup_draft_files(self, draft_id: str) -> bool:
        """Clean up draft files from storage."""
        try:
            # In a real implementation, this would delete files from storage
            logger.info(f"Cleaned up files for draft {draft_id}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up files for draft {draft_id}: {e}")
            return False


# Global draft service instance
draft_service = DraftService()
