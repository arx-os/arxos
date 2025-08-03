"""
Build Hooks Integration for Planarx Project Management

This module provides comprehensive integration between Planarx project management
and build system progress, including funding release gates and automated triggers.

Features:
- Webhook interface for build system integration
- Funding release gate automation
- Task progress tracking and synchronization
- Automated milestone completion
- Real-time status updates
- Audit trail for all build events

Performance Targets:
- Webhook processing completes within 2 seconds
- Funding release gates process within 5 seconds
- Task synchronization maintains 99.9% accuracy
- Real-time updates delivered within 1 second
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
import aiohttp
import sqlite3
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class BuildEventType(Enum):
    """Build event types"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    MILESTONE_REACHED = "milestone_reached"
    FUNDING_RELEASED = "funding_released"
    BUILD_FAILED = "build_failed"
    QUALITY_GATE_PASSED = "quality_gate_passed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"


class FundingReleaseStatus(Enum):
    """Funding release status"""
    PENDING = "pending"
    APPROVED = "approved"
    RELEASED = "released"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


@dataclass
class BuildEvent:
    """Build event data structure"""
    event_id: str
    event_type: BuildEventType
    project_id: str
    task_id: Optional[str] = None
    milestone_id: Optional[str] = None
    funding_amount: Optional[float] = None
    build_data: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
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
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.build_data is None:
            self.build_data = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FundingReleaseGate:
    """Funding release gate configuration"""
    gate_id: str
    project_id: str
    milestone_id: str
    amount: float
    conditions: List[Dict[str, Any]]
    status: FundingReleaseStatus
    created_at: datetime
    updated_at: datetime
    released_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskProgress:
    """Task progress tracking"""
    task_id: str
    project_id: str
    status: TaskStatus
    progress_percentage: float
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    actual_duration: Optional[timedelta] = None
    dependencies: List[str] = None
    blockers: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.blockers is None:
            self.blockers = []
        if self.metadata is None:
            self.metadata = {}


class BuildHooksIntegration:
    """
    Comprehensive build hooks integration system for Planarx project management.
    
    Features:
    - Webhook interface for build system integration
    - Funding release gate automation
    - Task progress tracking and synchronization
    - Automated milestone completion
    - Real-time status updates
    - Audit trail for all build events
    """
    
    def __init__(self, db_path: str = "build_hooks.db"):
        """Initialize the build hooks integration system."""
        self.db_path = db_path
        self.webhook_secret = self._load_webhook_secret()
        self.build_events: Dict[str, BuildEvent] = {}
        self.funding_gates: Dict[str, FundingReleaseGate] = {}
        self.task_progress: Dict[str, TaskProgress] = {}
        
        # Performance tracking
        self.metrics = {
            "total_webhooks_processed": 0,
            "total_funding_releases": 0,
            "total_task_updates": 0,
            "total_milestone_completions": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }
        
        # Initialize database
        self._init_database()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    def _load_webhook_secret(self) -> str:
        """Load webhook secret from environment or generate default."""
        import os
        secret = os.getenv("BUILD_HOOKS_SECRET", "default-secret-key")
        if secret == "default-secret-key":
            logger.warning("Using default webhook secret - set BUILD_HOOKS_SECRET for production")
        return secret
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS build_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    task_id TEXT,
                    milestone_id TEXT,
                    funding_amount REAL,
                    build_data TEXT,
                    metadata TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS funding_release_gates (
                    gate_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    milestone_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    conditions TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    released_at TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_progress (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percentage REAL NOT NULL,
                    start_time TEXT,
                    completion_time TEXT,
                    estimated_duration TEXT,
                    actual_duration TEXT,
                    dependencies TEXT,
                    blockers TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
    
    async def _start_background_tasks(self):
        """Start background tasks for build hooks integration."""
        tasks = [
            asyncio.create_task(self._process_build_events()),
            asyncio.create_task(self._check_funding_gates()),
            asyncio.create_task(self._sync_task_progress()),
            asyncio.create_task(self._update_metrics())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """
        Process incoming webhook from build system.
        
        Args:
            payload: Webhook payload
            signature: HMAC signature for validation
            
        Returns:
            Processing result
        """
        start_time = time.time()
        
        try:
            # Validate webhook signature
            if not self._validate_webhook_signature(payload, signature):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Extract event data
            event_type = BuildEventType(payload.get("event_type"))
            project_id = payload.get("project_id")
            
            if not project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing project_id in payload"
                )
            
            # Create build event
            event = BuildEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                project_id=project_id,
                task_id=payload.get("task_id"),
                milestone_id=payload.get("milestone_id"),
                funding_amount=payload.get("funding_amount"),
                build_data=payload.get("build_data", {}),
                metadata=payload.get("metadata", {})
            )
            
            # Process event based on type
            await self._process_build_event(event)
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics["total_webhooks_processed"] += 1
            self.metrics["average_processing_time"] = (
                (self.metrics["average_processing_time"] + processing_time) / 2
            )
            
            return {
                "success": True,
                "event_id": event.event_id,
                "processing_time": processing_time,
                "message": f"Event {event_type.value} processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _validate_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Validate webhook HMAC signature."""
        try:
            payload_str = json.dumps(payload, sort_keys=True)
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False
    
    async def _process_build_event(self, event: BuildEvent):
        """Process build event based on type."""
        try:
            # Store event
            self.build_events[event.event_id] = event
            await self._save_build_event(event)
            
            # Process based on event type
            if event.event_type == BuildEventType.TASK_STARTED:
                await self._handle_task_started(event)
            elif event.event_type == BuildEventType.TASK_COMPLETED:
                await self._handle_task_completed(event)
            elif event.event_type == BuildEventType.MILESTONE_REACHED:
                await self._handle_milestone_reached(event)
            elif event.event_type == BuildEventType.FUNDING_RELEASED:
                await self._handle_funding_released(event)
            elif event.event_type == BuildEventType.BUILD_FAILED:
                await self._handle_build_failed(event)
            elif event.event_type == BuildEventType.QUALITY_GATE_PASSED:
                await self._handle_quality_gate_passed(event)
            elif event.event_type == BuildEventType.QUALITY_GATE_FAILED:
                await self._handle_quality_gate_failed(event)
            elif event.event_type == BuildEventType.DEPLOYMENT_STARTED:
                await self._handle_deployment_started(event)
            elif event.event_type == BuildEventType.DEPLOYMENT_COMPLETED:
                await self._handle_deployment_completed(event)
            elif event.event_type == BuildEventType.DEPLOYMENT_FAILED:
                await self._handle_deployment_failed(event)
            
            logger.info(f"Processed build event: {event.event_type.value} for project {event.project_id}")
            
        except Exception as e:
            logger.error(f"Error processing build event: {e}")
            raise
    
    async def _handle_task_started(self, event: BuildEvent):
        """Handle task started event."""
        if event.task_id:
            progress = TaskProgress(
                task_id=event.task_id,
                project_id=event.project_id,
                status=TaskStatus.IN_PROGRESS,
                progress_percentage=0.0,
                start_time=event.timestamp
            )
            
            self.task_progress[event.task_id] = progress
            await self._save_task_progress(progress)
    
    async def _handle_task_completed(self, event: BuildEvent):
        """Handle task completed event."""
        if event.task_id and event.task_id in self.task_progress:
            progress = self.task_progress[event.task_id]
            progress.status = TaskStatus.COMPLETED
            progress.progress_percentage = 100.0
            progress.completion_time = event.timestamp
            
            if progress.start_time:
                progress.actual_duration = event.timestamp - progress.start_time
            
            await self._save_task_progress(progress)
            self.metrics["total_task_updates"] += 1
    
    async def _handle_milestone_reached(self, event: BuildEvent):
        """Handle milestone reached event."""
        if event.milestone_id:
            # Check funding gates for this milestone
            await self._check_milestone_funding_gates(event.project_id, event.milestone_id)
            self.metrics["total_milestone_completions"] += 1
    
    async def _handle_funding_released(self, event: BuildEvent):
        """Handle funding released event."""
        if event.funding_amount:
            self.metrics["total_funding_releases"] += 1
            logger.info(f"Funding released: ${event.funding_amount} for project {event.project_id}")
    
    async def _handle_build_failed(self, event: BuildEvent):
        """Handle build failed event."""
        if event.task_id and event.task_id in self.task_progress:
            progress = self.task_progress[event.task_id]
            progress.status = TaskStatus.FAILED
            await self._save_task_progress(progress)
    
    async def _handle_quality_gate_passed(self, event: BuildEvent):
        """Handle quality gate passed event."""
        # Trigger next phase or milestone
        await self._trigger_next_phase(event.project_id)
    
    async def _handle_quality_gate_failed(self, event: BuildEvent):
        """Handle quality gate failed event."""
        # Trigger rollback or remediation
        await self._trigger_remediation(event.project_id)
    
    async def _handle_deployment_started(self, event: BuildEvent):
        """Handle deployment started event."""
        logger.info(f"Deployment started for project {event.project_id}")
    
    async def _handle_deployment_completed(self, event: BuildEvent):
        """Handle deployment completed event."""
        logger.info(f"Deployment completed for project {event.project_id}")
    
    async def _handle_deployment_failed(self, event: BuildEvent):
        """Handle deployment failed event."""
        logger.error(f"Deployment failed for project {event.project_id}")
    
    async def create_funding_release_gate(
        self,
        project_id: str,
        milestone_id: str,
        amount: float,
        conditions: List[Dict[str, Any]]
    ) -> str:
        """
        Create a funding release gate.
        
        Args:
            project_id: Project identifier
            milestone_id: Milestone identifier
            amount: Funding amount
            conditions: Release conditions
            
        Returns:
            Gate ID
        """
        gate_id = str(uuid.uuid4())
        gate = FundingReleaseGate(
            gate_id=gate_id,
            project_id=project_id,
            milestone_id=milestone_id,
            amount=amount,
            conditions=conditions,
            status=FundingReleaseStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.funding_gates[gate_id] = gate
        await self._save_funding_gate(gate)
        
        logger.info(f"Created funding gate: {gate_id} for project {project_id}")
        return gate_id
    
    async def _check_milestone_funding_gates(self, project_id: str, milestone_id: str):
        """Check funding gates for milestone completion."""
        for gate_id, gate in self.funding_gates.items():
            if (gate.project_id == project_id and 
                gate.milestone_id == milestone_id and 
                gate.status == FundingReleaseStatus.PENDING):
                
                # Check if conditions are met
                if await self._evaluate_funding_conditions(gate):
                    gate.status = FundingReleaseStatus.APPROVED
                    gate.updated_at = datetime.utcnow()
                    await self._save_funding_gate(gate)
                    
                    # Trigger funding release
                    await self._trigger_funding_release(gate)
    
    async def _evaluate_funding_conditions(self, gate: FundingReleaseGate) -> bool:
        """Evaluate funding release conditions."""
        try:
            for condition in gate.conditions:
                condition_type = condition.get("type")
                
                if condition_type == "task_completion":
                    task_id = condition.get("task_id")
                    if task_id in self.task_progress:
                        task = self.task_progress[task_id]
                        if task.status != TaskStatus.COMPLETED:
                            return False
                
                elif condition_type == "quality_gate":
                    quality_gate_id = condition.get("quality_gate_id")
                    # Check quality gate status
                    if not await self._check_quality_gate_status(quality_gate_id):
                        return False
                
                elif condition_type == "milestone_completion":
                    milestone_id = condition.get("milestone_id")
                    # Check milestone completion
                    if not await self._check_milestone_completion(milestone_id):
                        return False
                
                elif condition_type == "approval":
                    approval_id = condition.get("approval_id")
                    # Check approval status
                    if not await self._check_approval_status(approval_id):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating funding conditions: {e}")
            return False
    
    async def _check_quality_gate_status(self, quality_gate_id: str) -> bool:
        """Check quality gate status."""
        # Mock implementation - in real system, check actual quality gate
        return True
    
    async def _check_milestone_completion(self, milestone_id: str) -> bool:
        """Check milestone completion status."""
        # Mock implementation - in real system, check actual milestone
        return True
    
    async def _check_approval_status(self, approval_id: str) -> bool:
        """Check approval status."""
        # Mock implementation - in real system, check actual approval
        return True
    
    async def _trigger_funding_release(self, gate: FundingReleaseGate):
        """Trigger funding release."""
        try:
            gate.status = FundingReleaseStatus.RELEASED
            gate.released_at = datetime.utcnow()
            gate.updated_at = datetime.utcnow()
            await self._save_funding_gate(gate)
            
            # Create funding release event
            event = BuildEvent(
                event_id=str(uuid.uuid4()),
                event_type=BuildEventType.FUNDING_RELEASED,
                project_id=gate.project_id,
                milestone_id=gate.milestone_id,
                funding_amount=gate.amount,
                metadata={"gate_id": gate.gate_id}
            )
            
            await self._process_build_event(event)
            
            logger.info(f"Funding released: ${gate.amount} for project {gate.project_id}")
            
        except Exception as e:
            logger.error(f"Error triggering funding release: {e}")
    
    async def _trigger_next_phase(self, project_id: str):
        """Trigger next phase after quality gate passed."""
        logger.info(f"Triggering next phase for project {project_id}")
    
    async def _trigger_remediation(self, project_id: str):
        """Trigger remediation after quality gate failed."""
        logger.info(f"Triggering remediation for project {project_id}")
    
    async def _process_build_events(self):
        """Process build events in background."""
        while True:
            try:
                # Process any pending events
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in build events processing: {e}")
    
    async def _check_funding_gates(self):
        """Check funding gates in background."""
        while True:
            try:
                # Check for gates that need evaluation
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in funding gates checking: {e}")
    
    async def _sync_task_progress(self):
        """Sync task progress in background."""
        while True:
            try:
                # Sync task progress with external systems
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in task progress sync: {e}")
    
    async def _update_metrics(self):
        """Update metrics in background."""
        while True:
            try:
                # Calculate success rate
                total_events = self.metrics["total_webhooks_processed"]
                if total_events > 0:
                    self.metrics["success_rate"] = 0.95  # Mock success rate
                
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
    
    async def _save_build_event(self, event: BuildEvent):
        """Save build event to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO build_events 
                (event_id, event_type, project_id, task_id, milestone_id, 
                 funding_amount, build_data, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.project_id,
                event.task_id,
                event.milestone_id,
                event.funding_amount,
                json.dumps(event.build_data),
                json.dumps(event.metadata),
                event.timestamp.isoformat()
            ))
            conn.commit()
    
    async def _save_funding_gate(self, gate: FundingReleaseGate):
        """Save funding gate to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO funding_release_gates 
                (gate_id, project_id, milestone_id, amount, conditions, status,
                 created_at, updated_at, released_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gate.gate_id,
                gate.project_id,
                gate.milestone_id,
                gate.amount,
                json.dumps(gate.conditions),
                gate.status.value,
                gate.created_at.isoformat(),
                gate.updated_at.isoformat(),
                gate.released_at.isoformat() if gate.released_at else None,
                json.dumps(gate.metadata)
            ))
            conn.commit()
    
    async def _save_task_progress(self, progress: TaskProgress):
        """Save task progress to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO task_progress 
                (task_id, project_id, status, progress_percentage, start_time,
                 completion_time, estimated_duration, actual_duration,
                 dependencies, blockers, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress.task_id,
                progress.project_id,
                progress.status.value,
                progress.progress_percentage,
                progress.start_time.isoformat() if progress.start_time else None,
                progress.completion_time.isoformat() if progress.completion_time else None,
                str(progress.estimated_duration) if progress.estimated_duration else None,
                str(progress.actual_duration) if progress.actual_duration else None,
                json.dumps(progress.dependencies),
                json.dumps(progress.blockers),
                json.dumps(progress.metadata)
            ))
            conn.commit()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def get_build_events(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get build events."""
        events = []
        for event in self.build_events.values():
            if project_id is None or event.project_id == project_id:
                events.append(asdict(event))
        return events
    
    def get_funding_gates(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get funding gates."""
        gates = []
        for gate in self.funding_gates.values():
            if project_id is None or gate.project_id == project_id:
                gates.append(asdict(gate))
        return gates
    
    def get_task_progress(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get task progress."""
        progress_list = []
        for progress in self.task_progress.values():
            if project_id is None or progress.project_id == project_id:
                progress_list.append(asdict(progress))
        return progress_list 