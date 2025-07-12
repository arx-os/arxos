"""
Task Trigger Mapping System for Planarx Project Management

This module provides comprehensive mapping between project tasks and build system
triggers, including funding release gates and automated workflow orchestration.

Features:
- Task-to-build system mapping
- Funding release gate automation
- Workflow orchestration and triggers
- Real-time status synchronization
- Automated milestone tracking
- Comprehensive audit trail

Performance Targets:
- Task mapping updates within 1 second
- Funding gate evaluation within 5 seconds
- Workflow orchestration completes within 10 seconds
- Real-time sync maintains 99.9% accuracy
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from pathlib import Path

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
import sqlite3
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Trigger types for task mapping"""
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    MILESTONE_REACH = "milestone_reach"
    FUNDING_RELEASE = "funding_release"
    QUALITY_GATE = "quality_gate"
    DEPLOYMENT = "deployment"
    APPROVAL = "approval"
    CUSTOM = "custom"


class TriggerStatus(Enum):
    """Trigger status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskTrigger:
    """Task trigger mapping"""
    trigger_id: str
    task_id: str
    project_id: str
    trigger_type: TriggerType
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    status: TriggerStatus
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowOrchestration:
    """Workflow orchestration configuration"""
    workflow_id: str
    project_id: str
    name: str
    description: str
    triggers: List[str]
    steps: List[Dict[str, Any]]
    status: TriggerStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FundingGateMapping:
    """Funding gate mapping configuration"""
    gate_id: str
    project_id: str
    milestone_id: str
    amount: float
    conditions: List[Dict[str, Any]]
    triggers: List[str]
    status: TriggerStatus
    created_at: datetime
    updated_at: datetime
    released_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TaskTriggerMap:
    """
    Comprehensive task trigger mapping system for Planarx project management.
    
    Features:
    - Task-to-build system mapping
    - Funding release gate automation
    - Workflow orchestration and triggers
    - Real-time status synchronization
    - Automated milestone tracking
    - Comprehensive audit trail
    """
    
    def __init__(self, db_path: str = "task_trigger_map.db"):
        """Initialize the task trigger mapping system."""
        self.db_path = db_path
        self.triggers: Dict[str, TaskTrigger] = {}
        self.workflows: Dict[str, WorkflowOrchestration] = {}
        self.funding_gates: Dict[str, FundingGateMapping] = {}
        
        # Trigger handlers
        self.trigger_handlers: Dict[TriggerType, Callable] = {
            TriggerType.TASK_START: self._handle_task_start,
            TriggerType.TASK_COMPLETE: self._handle_task_complete,
            TriggerType.MILESTONE_REACH: self._handle_milestone_reach,
            TriggerType.FUNDING_RELEASE: self._handle_funding_release,
            TriggerType.QUALITY_GATE: self._handle_quality_gate,
            TriggerType.DEPLOYMENT: self._handle_deployment,
            TriggerType.APPROVAL: self._handle_approval,
            TriggerType.CUSTOM: self._handle_custom_trigger
        }
        
        # Performance tracking
        self.metrics = {
            "total_triggers_created": 0,
            "total_triggers_executed": 0,
            "total_workflows_orchestrated": 0,
            "total_funding_gates_processed": 0,
            "average_trigger_execution_time": 0.0,
            "success_rate": 0.0
        }
        
        # Initialize database
        self._init_database()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_triggers (
                    trigger_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    executed_at TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_orchestrations (
                    workflow_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    triggers TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS funding_gate_mappings (
                    gate_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    milestone_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    conditions TEXT NOT NULL,
                    triggers TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    released_at TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
    
    async def _start_background_tasks(self):
        """Start background tasks for task trigger mapping."""
        tasks = [
            asyncio.create_task(self._process_triggers()),
            asyncio.create_task(self._orchestrate_workflows()),
            asyncio.create_task(self._check_funding_gates()),
            asyncio.create_task(self._sync_status()),
            asyncio.create_task(self._update_metrics())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def create_task_trigger(
        self,
        task_id: str,
        project_id: str,
        trigger_type: TriggerType,
        conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]]
    ) -> str:
        """
        Create a task trigger mapping.
        
        Args:
            task_id: Task identifier
            project_id: Project identifier
            trigger_type: Type of trigger
            conditions: Trigger conditions
            actions: Trigger actions
            
        Returns:
            Trigger ID
        """
        trigger_id = str(uuid.uuid4())
        trigger = TaskTrigger(
            trigger_id=trigger_id,
            task_id=task_id,
            project_id=project_id,
            trigger_type=trigger_type,
            conditions=conditions,
            actions=actions,
            status=TriggerStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.triggers[trigger_id] = trigger
        await self._save_task_trigger(trigger)
        
        self.metrics["total_triggers_created"] += 1
        logger.info(f"Created task trigger: {trigger_id} for task {task_id}")
        
        return trigger_id
    
    async def create_workflow_orchestration(
        self,
        project_id: str,
        name: str,
        description: str,
        triggers: List[str],
        steps: List[Dict[str, Any]]
    ) -> str:
        """
        Create a workflow orchestration.
        
        Args:
            project_id: Project identifier
            name: Workflow name
            description: Workflow description
            triggers: List of trigger IDs
            steps: Workflow steps
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowOrchestration(
            workflow_id=workflow_id,
            project_id=project_id,
            name=name,
            description=description,
            triggers=triggers,
            steps=steps,
            status=TriggerStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.workflows[workflow_id] = workflow
        await self._save_workflow_orchestration(workflow)
        
        self.metrics["total_workflows_orchestrated"] += 1
        logger.info(f"Created workflow orchestration: {workflow_id} for project {project_id}")
        
        return workflow_id
    
    async def create_funding_gate_mapping(
        self,
        project_id: str,
        milestone_id: str,
        amount: float,
        conditions: List[Dict[str, Any]],
        triggers: List[str]
    ) -> str:
        """
        Create a funding gate mapping.
        
        Args:
            project_id: Project identifier
            milestone_id: Milestone identifier
            amount: Funding amount
            conditions: Release conditions
            triggers: Associated triggers
            
        Returns:
            Gate ID
        """
        gate_id = str(uuid.uuid4())
        gate = FundingGateMapping(
            gate_id=gate_id,
            project_id=project_id,
            milestone_id=milestone_id,
            amount=amount,
            conditions=conditions,
            triggers=triggers,
            status=TriggerStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.funding_gates[gate_id] = gate
        await self._save_funding_gate_mapping(gate)
        
        self.metrics["total_funding_gates_processed"] += 1
        logger.info(f"Created funding gate mapping: {gate_id} for project {project_id}")
        
        return gate_id
    
    async def execute_trigger(self, trigger_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a task trigger.
        
        Args:
            trigger_id: Trigger identifier
            context: Execution context
            
        Returns:
            Execution result
        """
        start_time = time.time()
        
        try:
            if trigger_id not in self.triggers:
                raise ValueError(f"Trigger {trigger_id} not found")
            
            trigger = self.triggers[trigger_id]
            
            # Check if conditions are met
            if not await self._evaluate_trigger_conditions(trigger, context or {}):
                return {
                    "success": False,
                    "message": "Trigger conditions not met",
                    "trigger_id": trigger_id
                }
            
            # Execute trigger
            handler = self.trigger_handlers.get(trigger.trigger_type)
            if handler:
                result = await handler(trigger, context or {})
            else:
                result = {"success": False, "message": f"No handler for trigger type {trigger.trigger_type}"}
            
            # Update trigger status
            trigger.status = TriggerStatus.COMPLETED if result["success"] else TriggerStatus.FAILED
            trigger.executed_at = datetime.utcnow()
            trigger.updated_at = datetime.utcnow()
            await self._save_task_trigger(trigger)
            
            # Execute actions
            if result["success"]:
                await self._execute_trigger_actions(trigger, context or {})
            
            # Update metrics
            execution_time = time.time() - start_time
            self.metrics["total_triggers_executed"] += 1
            self.metrics["average_trigger_execution_time"] = (
                (self.metrics["average_trigger_execution_time"] + execution_time) / 2
            )
            
            return {
                "success": result["success"],
                "trigger_id": trigger_id,
                "execution_time": execution_time,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing trigger {trigger_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "trigger_id": trigger_id,
                "execution_time": time.time() - start_time
            }
    
    async def _evaluate_trigger_conditions(self, trigger: TaskTrigger, context: Dict[str, Any]) -> bool:
        """Evaluate trigger conditions."""
        try:
            for condition in trigger.conditions:
                condition_type = condition.get("type")
                
                if condition_type == "task_status":
                    task_id = condition.get("task_id")
                    expected_status = condition.get("status")
                    # Check task status
                    if not await self._check_task_status(task_id, expected_status):
                        return False
                
                elif condition_type == "milestone_completion":
                    milestone_id = condition.get("milestone_id")
                    # Check milestone completion
                    if not await self._check_milestone_completion(milestone_id):
                        return False
                
                elif condition_type == "approval_status":
                    approval_id = condition.get("approval_id")
                    # Check approval status
                    if not await self._check_approval_status(approval_id):
                        return False
                
                elif condition_type == "quality_gate":
                    quality_gate_id = condition.get("quality_gate_id")
                    # Check quality gate status
                    if not await self._check_quality_gate_status(quality_gate_id):
                        return False
                
                elif condition_type == "custom":
                    # Custom condition evaluation
                    if not await self._evaluate_custom_condition(condition, context):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating trigger conditions: {e}")
            return False
    
    async def _check_task_status(self, task_id: str, expected_status: str) -> bool:
        """Check task status."""
        # Mock implementation - in real system, check actual task status
        return True
    
    async def _check_milestone_completion(self, milestone_id: str) -> bool:
        """Check milestone completion."""
        # Mock implementation - in real system, check actual milestone
        return True
    
    async def _check_approval_status(self, approval_id: str) -> bool:
        """Check approval status."""
        # Mock implementation - in real system, check actual approval
        return True
    
    async def _check_quality_gate_status(self, quality_gate_id: str) -> bool:
        """Check quality gate status."""
        # Mock implementation - in real system, check actual quality gate
        return True
    
    async def _evaluate_custom_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate custom condition."""
        # Mock implementation - in real system, evaluate custom conditions
        return True
    
    async def _handle_task_start(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task start trigger."""
        logger.info(f"Handling task start trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Task start handled successfully"}
    
    async def _handle_task_complete(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task complete trigger."""
        logger.info(f"Handling task complete trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Task complete handled successfully"}
    
    async def _handle_milestone_reach(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle milestone reach trigger."""
        logger.info(f"Handling milestone reach trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Milestone reach handled successfully"}
    
    async def _handle_funding_release(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle funding release trigger."""
        logger.info(f"Handling funding release trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Funding release handled successfully"}
    
    async def _handle_quality_gate(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quality gate trigger."""
        logger.info(f"Handling quality gate trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Quality gate handled successfully"}
    
    async def _handle_deployment(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deployment trigger."""
        logger.info(f"Handling deployment trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Deployment handled successfully"}
    
    async def _handle_approval(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle approval trigger."""
        logger.info(f"Handling approval trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Approval handled successfully"}
    
    async def _handle_custom_trigger(self, trigger: TaskTrigger, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom trigger."""
        logger.info(f"Handling custom trigger: {trigger.trigger_id}")
        return {"success": True, "message": "Custom trigger handled successfully"}
    
    async def _execute_trigger_actions(self, trigger: TaskTrigger, context: Dict[str, Any]):
        """Execute trigger actions."""
        try:
            for action in trigger.actions:
                action_type = action.get("type")
                
                if action_type == "webhook":
                    await self._execute_webhook_action(action, context)
                elif action_type == "notification":
                    await self._execute_notification_action(action, context)
                elif action_type == "workflow":
                    await self._execute_workflow_action(action, context)
                elif action_type == "funding_release":
                    await self._execute_funding_release_action(action, context)
                elif action_type == "custom":
                    await self._execute_custom_action(action, context)
            
            logger.info(f"Executed actions for trigger: {trigger.trigger_id}")
            
        except Exception as e:
            logger.error(f"Error executing trigger actions: {e}")
    
    async def _execute_webhook_action(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Execute webhook action."""
        url = action.get("url")
        method = action.get("method", "POST")
        headers = action.get("headers", {})
        data = action.get("data", {})
        
        # Mock webhook execution
        logger.info(f"Executing webhook: {method} {url}")
    
    async def _execute_notification_action(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Execute notification action."""
        channel = action.get("channel")
        message = action.get("message")
        
        # Mock notification execution
        logger.info(f"Sending notification to {channel}: {message}")
    
    async def _execute_workflow_action(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Execute workflow action."""
        workflow_id = action.get("workflow_id")
        
        # Mock workflow execution
        logger.info(f"Executing workflow: {workflow_id}")
    
    async def _execute_funding_release_action(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Execute funding release action."""
        gate_id = action.get("gate_id")
        amount = action.get("amount")
        
        # Mock funding release execution
        logger.info(f"Releasing funding: ${amount} for gate {gate_id}")
    
    async def _execute_custom_action(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Execute custom action."""
        action_name = action.get("name")
        
        # Mock custom action execution
        logger.info(f"Executing custom action: {action_name}")
    
    async def _process_triggers(self):
        """Process triggers in background."""
        while True:
            try:
                # Process pending triggers
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in trigger processing: {e}")
    
    async def _orchestrate_workflows(self):
        """Orchestrate workflows in background."""
        while True:
            try:
                # Orchestrate workflows
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in workflow orchestration: {e}")
    
    async def _check_funding_gates(self):
        """Check funding gates in background."""
        while True:
            try:
                # Check funding gates
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in funding gate checking: {e}")
    
    async def _sync_status(self):
        """Sync status in background."""
        while True:
            try:
                # Sync status with external systems
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in status sync: {e}")
    
    async def _update_metrics(self):
        """Update metrics in background."""
        while True:
            try:
                # Calculate success rate
                total_executed = self.metrics["total_triggers_executed"]
                if total_executed > 0:
                    self.metrics["success_rate"] = 0.95  # Mock success rate
                
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
    
    async def _save_task_trigger(self, trigger: TaskTrigger):
        """Save task trigger to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO task_triggers 
                (trigger_id, task_id, project_id, trigger_type, conditions, actions,
                 status, created_at, updated_at, executed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trigger.trigger_id,
                trigger.task_id,
                trigger.project_id,
                trigger.trigger_type.value,
                json.dumps(trigger.conditions),
                json.dumps(trigger.actions),
                trigger.status.value,
                trigger.created_at.isoformat(),
                trigger.updated_at.isoformat(),
                trigger.executed_at.isoformat() if trigger.executed_at else None,
                json.dumps(trigger.metadata)
            ))
            conn.commit()
    
    async def _save_workflow_orchestration(self, workflow: WorkflowOrchestration):
        """Save workflow orchestration to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_orchestrations 
                (workflow_id, project_id, name, description, triggers, steps,
                 status, created_at, updated_at, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow.workflow_id,
                workflow.project_id,
                workflow.name,
                workflow.description,
                json.dumps(workflow.triggers),
                json.dumps(workflow.steps),
                workflow.status.value,
                workflow.created_at.isoformat(),
                workflow.updated_at.isoformat(),
                workflow.completed_at.isoformat() if workflow.completed_at else None,
                json.dumps(workflow.metadata)
            ))
            conn.commit()
    
    async def _save_funding_gate_mapping(self, gate: FundingGateMapping):
        """Save funding gate mapping to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO funding_gate_mappings 
                (gate_id, project_id, milestone_id, amount, conditions, triggers,
                 status, created_at, updated_at, released_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gate.gate_id,
                gate.project_id,
                gate.milestone_id,
                gate.amount,
                json.dumps(gate.conditions),
                json.dumps(gate.triggers),
                gate.status.value,
                gate.created_at.isoformat(),
                gate.updated_at.isoformat(),
                gate.released_at.isoformat() if gate.released_at else None,
                json.dumps(gate.metadata)
            ))
            conn.commit()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def get_triggers(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get task triggers."""
        triggers = []
        for trigger in self.triggers.values():
            if project_id is None or trigger.project_id == project_id:
                triggers.append(asdict(trigger))
        return triggers
    
    def get_workflows(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflow orchestrations."""
        workflows = []
        for workflow in self.workflows.values():
            if project_id is None or workflow.project_id == project_id:
                workflows.append(asdict(workflow))
        return workflows
    
    def get_funding_gates(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get funding gate mappings."""
        gates = []
        for gate in self.funding_gates.values():
            if project_id is None or gate.project_id == project_id:
                gates.append(asdict(gate))
        return gates 