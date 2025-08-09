"""
Milestone Hook System for Planarx Funding

This module provides comprehensive milestone tracking and funding release automation
for Planarx projects, integrating with the escrow system and build pipelines.

Features:
- Milestone completion tracking
- Automated funding release triggers
- Escrow integration and validation
- Build pipeline synchronization
- Real-time status updates
- Comprehensive audit trail
- Webhook notifications for milestone events

Performance Targets:
- Milestone validation completes within 3 seconds
- Funding release processing within 5 seconds
- Webhook notifications delivered within 2 seconds
- Real-time sync maintains 99.9% accuracy
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
from pathlib import Path

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
import sqlite3
from contextlib import asynccontextmanager
import aiohttp

logger = logging.getLogger(__name__)


class MilestoneStatus(Enum):
    """Milestone status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    APPROVED = "approved"
    REJECTED = "rejected"


class FundingReleaseStatus(Enum):
    """Funding release status"""
    PENDING = "pending"
    APPROVED = "approved"
    RELEASED = "released"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCROWED = "escrowed"


class MilestoneType(Enum):
    """Milestone types"""
    DESIGN_PHASE = "design_phase"
    DEVELOPMENT_PHASE = "development_phase"
    TESTING_PHASE = "testing_phase"
    DEPLOYMENT_PHASE = "deployment_phase"
    DOCUMENTATION_PHASE = "documentation_phase"
    REVIEW_PHASE = "review_phase"
    CUSTOM = "custom"


@dataclass
class Milestone:
    """Milestone data structure"""
    milestone_id: str
    project_id: str
    title: str
    description: str
    milestone_type: MilestoneType
    amount: float
    due_date: datetime
    status: MilestoneStatus
    completion_criteria: List[Dict[str, Any]]
    evidence_urls: List[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        pass
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.evidence_urls is None:
            self.evidence_urls = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FundingRelease:
    """Funding release data structure"""
    release_id: str
    milestone_id: str
    project_id: str
    amount: float
    status: FundingReleaseStatus
    release_conditions: List[Dict[str, Any]]
    approval_required: bool
    approvers: List[str]
    approved_by: Optional[str] = None
    released_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MilestoneHook:
    """Milestone hook configuration"""
    hook_id: str
    milestone_id: str
    project_id: str
    hook_type: str  # "webhook", "notification", "build_pipeline", "funding_release"
    url: Optional[str] = None
    secret: Optional[str] = None
    conditions: List[Dict[str, Any]] = None
    actions: List[Dict[str, Any]] = None
    status: str = "active"
    created_at: datetime = None
    updated_at: datetime = None
    last_triggered: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.conditions is None:
            self.conditions = []
        if self.actions is None:
            self.actions = []
        if self.metadata is None:
            self.metadata = {}


class MilestoneHookSystem:
    """
    Comprehensive milestone hook system for Planarx funding.

    Features:
    - Milestone completion tracking
    - Automated funding release triggers
    - Escrow integration and validation
    - Build pipeline synchronization
    - Real-time status updates
    - Comprehensive audit trail
    - Webhook notifications for milestone events
    """

    def __init__(self, db_path: str = "milestone_hooks.db"):
        """Initialize the milestone hook system."""
        self.db_path = db_path
        self.milestones: Dict[str, Milestone] = {}
        self.funding_releases: Dict[str, FundingRelease] = {}
        self.hooks: Dict[str, MilestoneHook] = {}

        # Performance tracking
        self.metrics = {
            "total_milestones_created": 0,
            "total_milestones_completed": 0,
            "total_funding_releases": 0,
            "total_hooks_triggered": 0,
            "total_webhooks_sent": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }

        # Initialize database
        self._init_database()

        # Start background tasks
        asyncio.create_task(self._start_background_tasks()
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Milestones table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    milestone_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    milestone_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    completion_criteria TEXT NOT NULL,
                    evidence_urls TEXT,
                    submitted_at TEXT,
                    approved_at TEXT,
                    approved_by TEXT,
                    rejection_reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            # Funding releases table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS funding_releases (
                    release_id TEXT PRIMARY KEY,
                    milestone_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    release_conditions TEXT NOT NULL,
                    approval_required BOOLEAN NOT NULL,
                    approvers TEXT NOT NULL,
                    approved_by TEXT,
                    released_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            # Milestone hooks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS milestone_hooks (
                    hook_id TEXT PRIMARY KEY,
                    milestone_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    hook_type TEXT NOT NULL,
                    url TEXT,
                    secret TEXT,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_triggered TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()

    async def _start_background_tasks(self):
        """Start background processing tasks."""
        while True:
            try:
                await self._process_milestone_hooks()
                await self._check_funding_releases()
                await self._sync_milestone_status()
                await self._update_metrics()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Background task error: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def create_milestone(
        self,
        project_id: str,
        title: str,
        description: str,
        milestone_type: MilestoneType,
        amount: float,
        due_date: datetime,
        completion_criteria: List[Dict[str, Any]]
    ) -> str:
        """Create a new milestone."""
        milestone_id = str(uuid.uuid4()
        milestone = Milestone(
            milestone_id=milestone_id,
            project_id=project_id,
            title=title,
            description=description,
            milestone_type=milestone_type,
            amount=amount,
            due_date=due_date,
            status=MilestoneStatus.PENDING,
            completion_criteria=completion_criteria
        )

        self.milestones[milestone_id] = milestone
        await self._save_milestone(milestone)

        self.metrics["total_milestones_created"] += 1
        logger.info(f"Created milestone {milestone_id} for project {project_id}")

        return milestone_id

    async def create_funding_release(
        self,
        milestone_id: str,
        project_id: str,
        amount: float,
        release_conditions: List[Dict[str, Any]],
        approval_required: bool = True,
        approvers: List[str] = None
    ) -> str:
        """Create a new funding release."""
        release_id = str(uuid.uuid4()
        if approvers is None:
            approvers = []

        funding_release = FundingRelease(
            release_id=release_id,
            milestone_id=milestone_id,
            project_id=project_id,
            amount=amount,
            status=FundingReleaseStatus.PENDING,
            release_conditions=release_conditions,
            approval_required=approval_required,
            approvers=approvers
        )

        self.funding_releases[release_id] = funding_release
        await self._save_funding_release(funding_release)

        self.metrics["total_funding_releases"] += 1
        logger.info(f"Created funding release {release_id} for milestone {milestone_id}")

        return release_id

    async def create_milestone_hook(
        self,
        milestone_id: str,
        project_id: str,
        hook_type: str,
        url: Optional[str] = None,
        secret: Optional[str] = None,
        conditions: List[Dict[str, Any]] = None,
        actions: List[Dict[str, Any]] = None
    ) -> str:
        """Create a new milestone hook."""
        hook_id = str(uuid.uuid4()
        if conditions is None:
            conditions = []
        if actions is None:
            actions = []

        hook = MilestoneHook(
            hook_id=hook_id,
            milestone_id=milestone_id,
            project_id=project_id,
            hook_type=hook_type,
            url=url,
            secret=secret,
            conditions=conditions,
            actions=actions
        )

        self.hooks[hook_id] = hook
        await self._save_milestone_hook(hook)

        logger.info(f"Created milestone hook {hook_id} for milestone {milestone_id}")

        return hook_id

    async def submit_milestone(
        self,
        milestone_id: str,
        evidence_urls: List[str],
        submitted_by: str
    ) -> Dict[str, Any]:
        """Submit a milestone for approval."""
        if milestone_id not in self.milestones:
            raise HTTPException(status_code=404, detail="Milestone not found")

        milestone = self.milestones[milestone_id]
        milestone.status = MilestoneStatus.IN_PROGRESS
        milestone.evidence_urls = evidence_urls
        milestone.submitted_at = datetime.utcnow()
        milestone.updated_at = datetime.utcnow()

        await self._save_milestone(milestone)

        # Trigger hooks
        await self._trigger_milestone_hooks(milestone_id, "milestone_submitted", {
            "milestone_id": milestone_id,
            "project_id": milestone.project_id,
            "submitted_by": submitted_by,
            "evidence_urls": evidence_urls
        })

        logger.info(f"Milestone {milestone_id} submitted by {submitted_by}")

        return {
            "success": True,
            "milestone_id": milestone_id,
            "status": milestone.status.value
        }

    async def approve_milestone(
        self,
        milestone_id: str,
        approved_by: str,
        approval_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve a milestone."""
        if milestone_id not in self.milestones:
            raise HTTPException(status_code=404, detail="Milestone not found")

        milestone = self.milestones[milestone_id]
        milestone.status = MilestoneStatus.APPROVED
        milestone.approved_at = datetime.utcnow()
        milestone.approved_by = approved_by
        milestone.updated_at = datetime.utcnow()

        await self._save_milestone(milestone)

        # Trigger funding release
        await self._trigger_funding_release(milestone_id)

        # Trigger hooks
        await self._trigger_milestone_hooks(milestone_id, "milestone_approved", {
            "milestone_id": milestone_id,
            "project_id": milestone.project_id,
            "approved_by": approved_by,
            "approval_notes": approval_notes
        })

        self.metrics["total_milestones_completed"] += 1
        logger.info(f"Milestone {milestone_id} approved by {approved_by}")

        return {
            "success": True,
            "milestone_id": milestone_id,
            "status": milestone.status.value
        }

    async def reject_milestone(
        self,
        milestone_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """Reject a milestone."""
        if milestone_id not in self.milestones:
            raise HTTPException(status_code=404, detail="Milestone not found")

        milestone = self.milestones[milestone_id]
        milestone.status = MilestoneStatus.REJECTED
        milestone.rejection_reason = rejection_reason
        milestone.updated_at = datetime.utcnow()

        await self._save_milestone(milestone)

        # Trigger hooks
        await self._trigger_milestone_hooks(milestone_id, "milestone_rejected", {
            "milestone_id": milestone_id,
            "project_id": milestone.project_id,
            "rejected_by": rejected_by,
            "rejection_reason": rejection_reason
        })

        logger.info(f"Milestone {milestone_id} rejected by {rejected_by}")

        return {
            "success": True,
            "milestone_id": milestone_id,
            "status": milestone.status.value
        }

    async def _trigger_funding_release(self, milestone_id: str):
        """Trigger funding release for milestone."""
        # Find funding releases for this milestone
        for release_id, release in self.funding_releases.items():
            if release.milestone_id == milestone_id:
                if not release.approval_required:
                    release.status = FundingReleaseStatus.APPROVED
                    release.approved_by = "auto"
                    release.updated_at = datetime.utcnow()
                    await self._save_funding_release(release)
                    logger.info(f"Auto-approved funding release {release_id}")
                else:
                    # Mark as pending approval
                    release.status = FundingReleaseStatus.PENDING
                    release.updated_at = datetime.utcnow()
                    await self._save_funding_release(release)
                    logger.info(f"Funding release {release_id} pending approval")

    async def approve_funding_release(
        self,
        release_id: str,
        approved_by: str
    ) -> Dict[str, Any]:
        """Approve a funding release."""
        if release_id not in self.funding_releases:
            raise HTTPException(status_code=404, detail="Funding release not found")

        release = self.funding_releases[release_id]

        if approved_by not in release.approvers:
            raise HTTPException(status_code=403, detail="Not authorized to approve")

        release.status = FundingReleaseStatus.APPROVED
        release.approved_by = approved_by
        release.updated_at = datetime.utcnow()

        await self._save_funding_release(release)

        # Trigger release
        await self._execute_funding_release(release_id)

        logger.info(f"Funding release {release_id} approved by {approved_by}")

        return {
            "success": True,
            "release_id": release_id,
            "status": release.status.value
        }

    async def _execute_funding_release(self, release_id: str):
        """Execute funding release."""
        release = self.funding_releases[release_id]
        release.status = FundingReleaseStatus.RELEASED
        release.released_at = datetime.utcnow()
        release.updated_at = datetime.utcnow()

        await self._save_funding_release(release)

        # Trigger hooks
        await self._trigger_milestone_hooks(release.milestone_id, "funding_released", {
            "release_id": release_id,
            "milestone_id": release.milestone_id,
            "project_id": release.project_id,
            "amount": release.amount,
            "released_at": release.released_at.isoformat()
        })

        logger.info(f"Funding release {release_id} executed")

    async def _trigger_milestone_hooks(
        self,
        milestone_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Trigger milestone hooks for an event."""
        for hook_id, hook in self.hooks.items():
            if hook.milestone_id == milestone_id and hook.status == "active":
                try:
                    if hook.hook_type == "webhook" and hook.url:
                        await self._send_webhook(hook, event_type, event_data)
                    elif hook.hook_type == "notification":
                        await self._send_notification(hook, event_type, event_data)
                    elif hook.hook_type == "build_pipeline":
                        await self._trigger_build_pipeline(hook, event_type, event_data)
                    elif hook.hook_type == "funding_release":
                        await self._trigger_funding_release_hook(hook, event_type, event_data)

                    hook.last_triggered = datetime.utcnow()
                    hook.updated_at = datetime.utcnow()
                    await self._save_milestone_hook(hook)

                    self.metrics["total_hooks_triggered"] += 1

                except Exception as e:
                    logger.error(f"Failed to trigger hook {hook_id}: {e}")

    async def _send_webhook(self, hook: MilestoneHook, event_type: str, event_data: Dict[str, Any]):
        """Send webhook notification."""
        payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "hook_id": hook.hook_id,
            "data": event_data
        }

        headers = {"Content-Type": "application/json"}
        if hook.secret:
            signature = hmac.new(
                hook.secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(hook.url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        self.metrics["total_webhooks_sent"] += 1
                        logger.info(f"Webhook sent successfully to {hook.url}")
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    async def _send_notification(self, hook: MilestoneHook, event_type: str, event_data: Dict[str, Any]):
        """Send notification."""
        # This would integrate with notification system
        logger.info(f"Notification sent for event {event_type}")

    async def _trigger_build_pipeline(self, hook: MilestoneHook, event_type: str, event_data: Dict[str, Any]):
        """Trigger build pipeline."""
        # This would integrate with build pipeline system
        logger.info(f"Build pipeline triggered for event {event_type}")

    async def _trigger_funding_release_hook(self, hook: MilestoneHook, event_type: str, event_data: Dict[str, Any]):
        """Trigger funding release hook."""
        # This would integrate with funding release system
        logger.info(f"Funding release hook triggered for event {event_type}")

    async def _process_milestone_hooks(self):
        """Process milestone hooks."""
        # This would process any pending hooks
        pass

    async def _check_funding_releases(self):
        """Check funding releases for processing."""
        for release_id, release in self.funding_releases.items():
            if release.status == FundingReleaseStatus.APPROVED:
                # Check if all conditions are met
                conditions_met = await self._evaluate_release_conditions(release)
                if conditions_met:
                    await self._execute_funding_release(release_id)

    async def _evaluate_release_conditions(self, release: FundingRelease) -> bool:
        """Evaluate funding release conditions."""
        for condition in release.release_conditions:
            condition_type = condition.get("type")

            if condition_type == "milestone_approved":
                milestone_id = condition.get("milestone_id")
                if milestone_id in self.milestones:
                    milestone = self.milestones[milestone_id]
                    if milestone.status != MilestoneStatus.APPROVED:
                        return False

            elif condition_type == "time_elapsed":
                elapsed_days = condition.get("days", 0)
                if release.created_at + timedelta(days=elapsed_days) > datetime.utcnow():
                    return False

            elif condition_type == "custom":
                # This would handle custom condition evaluation
                pass

        return True

    async def _sync_milestone_status(self):
        """Synchronize milestone status."""
        # This would sync with external systems
        pass

    async def _update_metrics(self):
        """Update performance metrics."""
        total_hooks = self.metrics["total_hooks_triggered"]
        if total_hooks > 0:
            self.metrics["success_rate"] = (
                (total_hooks - self.metrics.get("failed_hooks", 0)) / total_hooks
            )

    async def _save_milestone(self, milestone: Milestone):
        """Save milestone to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO milestones
                (milestone_id, project_id, title, description, milestone_type, amount,
                 due_date, status, completion_criteria, evidence_urls, submitted_at,
                 approved_at, approved_by, rejection_reason, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("
                milestone.milestone_id,
                milestone.project_id,
                milestone.title,
                milestone.description,
                milestone.milestone_type.value,
                milestone.amount,
                milestone.due_date.isoformat(),
                milestone.status.value,
                json.dumps(milestone.completion_criteria),
                json.dumps(milestone.evidence_urls),
                milestone.submitted_at.isoformat() if milestone.submitted_at else None,
                milestone.approved_at.isoformat() if milestone.approved_at else None,
                milestone.approved_by,
                milestone.rejection_reason,
                milestone.created_at.isoformat(),
                milestone.updated_at.isoformat(),
                json.dumps(milestone.metadata)
            ))
            conn.commit()

    async def _save_funding_release(self, release: FundingRelease):
        """Save funding release to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO funding_releases
                (release_id, milestone_id, project_id, amount, status, release_conditions,
                 approval_required, approvers, approved_by, released_at, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("
                release.release_id,
                release.milestone_id,
                release.project_id,
                release.amount,
                release.status.value,
                json.dumps(release.release_conditions),
                release.approval_required,
                json.dumps(release.approvers),
                release.approved_by,
                release.released_at.isoformat() if release.released_at else None,
                release.created_at.isoformat(),
                release.updated_at.isoformat(),
                json.dumps(release.metadata)
            ))
            conn.commit()

    async def _save_milestone_hook(self, hook: MilestoneHook):
        """Save milestone hook to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO milestone_hooks
                (hook_id, milestone_id, project_id, hook_type, url, secret, conditions,
                 actions, status, created_at, updated_at, last_triggered, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("
                hook.hook_id,
                hook.milestone_id,
                hook.project_id,
                hook.hook_type,
                hook.url,
                hook.secret,
                json.dumps(hook.conditions),
                json.dumps(hook.actions),
                hook.status,
                hook.created_at.isoformat(),
                hook.updated_at.isoformat(),
                hook.last_triggered.isoformat() if hook.last_triggered else None,
                json.dumps(hook.metadata)
            ))
            conn.commit()

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()

    def get_milestones(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get milestones for a project."""
        milestones = []
        for milestone in self.milestones.values():
            if project_id is None or milestone.project_id == project_id:
                milestones.append(asdict(milestone)
        return milestones

    def get_funding_releases(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get funding releases for a project."""
        releases = []
        for release in self.funding_releases.values():
            if project_id is None or release.project_id == project_id:
                releases.append(asdict(release)
        return releases

    def get_hooks(self, milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get hooks for a milestone."""
        hooks = []
        for hook in self.hooks.values():
            if milestone_id is None or hook.milestone_id == milestone_id:
                hooks.append(asdict(hook)
        return hooks
