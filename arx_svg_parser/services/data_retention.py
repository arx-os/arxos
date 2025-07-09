"""
Data Retention Service

This module provides automated data lifecycle management including:
- Configurable retention policies by data type
- Secure data deletion with verification
- Compliance with regulatory requirements
- Audit trail for all retention actions
- Data archiving and backup strategies
"""

import logging
import time
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import hashlib
import shutil
import os

from utils.logger import get_logger

logger = get_logger(__name__)


class RetentionPolicyType(Enum):
    """Data retention policy types"""
    IMMEDIATE = "immediate"           # Delete immediately
    SHORT_TERM = "short_term"         # 30 days
    MEDIUM_TERM = "medium_term"       # 1 year
    LONG_TERM = "long_term"           # 5 years
    PERMANENT = "permanent"           # Never delete
    REGULATORY = "regulatory"         # Based on regulations


class DeletionStrategy(Enum):
    """Data deletion strategies"""
    SOFT_DELETE = "soft_delete"       # Mark as deleted
    HARD_DELETE = "hard_delete"       # Remove from storage
    SECURE_DELETE = "secure_delete"   # Overwrite before deletion
    ARCHIVE_DELETE = "archive_delete" # Move to archive


class DataType(Enum):
    """Data types for retention policies"""
    BUILDING_DATA = "building_data"
    USER_DATA = "user_data"
    AUDIT_LOGS = "audit_logs"
    AHJ_DATA = "ahj_data"
    COMPLIANCE_REPORTS = "compliance_reports"
    SYSTEM_LOGS = "system_logs"
    BACKUP_DATA = "backup_data"
    TEMPORARY_DATA = "temporary_data"


@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    policy_id: str
    data_type: DataType
    retention_period_days: int
    deletion_strategy: DeletionStrategy
    description: str
    created_at: datetime
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataLifecycle:
    """Data lifecycle tracking"""
    data_id: str
    data_type: DataType
    policy_id: str
    created_at: datetime
    last_accessed: datetime
    deletion_date: datetime
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeletionJob:
    """Data deletion job"""
    job_id: str
    data_ids: List[str]
    deletion_strategy: DeletionStrategy
    scheduled_date: datetime
    status: str = "scheduled"
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)


class DataRetentionService:
    """Automated data lifecycle management service"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Retention policies and data lifecycle
        self.retention_policies: Dict[str, RetentionPolicy] = {}
        self.data_lifecycle: Dict[str, DataLifecycle] = {}
        self.deletion_jobs: Dict[str, DeletionJob] = {}
        
        # Archive storage configuration
        self.archive_config = {
            "archive_path": "./data/archive",
            "compression_enabled": True,
            "encryption_enabled": True,
            "max_archive_size_gb": 100
        }
        
        # Performance tracking
        self.retention_metrics = {
            "total_policies": 0,
            "total_data_items": 0,
            "total_deletions": 0,
            "total_archives": 0,
            "average_deletion_time_ms": 0.0,
            "compliance_violations": 0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Initialize default policies
        self._initialize_default_policies()
        
        # Start background cleanup thread
        self._start_cleanup_thread()
    
    def create_retention_policy(self, data_type: DataType, retention_period_days: int,
                               deletion_strategy: DeletionStrategy, description: str = "",
                               metadata: Dict[str, Any] = None) -> str:
        """
        Create data retention policy.
        
        Args:
            data_type: Type of data
            retention_period_days: Retention period in days
            deletion_strategy: Strategy for data deletion
            description: Policy description
            metadata: Additional metadata
            
        Returns:
            str: Policy ID
        """
        with self.lock:
            policy_id = str(uuid.uuid4())
            
            policy = RetentionPolicy(
                policy_id=policy_id,
                data_type=data_type,
                retention_period_days=retention_period_days,
                deletion_strategy=deletion_strategy,
                description=description,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            
            self.retention_policies[policy_id] = policy
            self.retention_metrics["total_policies"] += 1
            
            self.logger.info(f"Created retention policy {policy_id} for {data_type.value}")
            return policy_id
    
    def apply_retention_policy(self, data_id: str, policy_id: str, 
                             data_type: DataType = None) -> bool:
        """
        Apply retention policy to data.
        
        Args:
            data_id: Data ID to apply policy to
            policy_id: Policy ID to apply
            data_type: Optional data type override
            
        Returns:
            bool: Success status
        """
        with self.lock:
            if policy_id not in self.retention_policies:
                raise ValueError(f"Retention policy {policy_id} does not exist")
            
            policy = self.retention_policies[policy_id]
            
            # Calculate deletion date
            deletion_date = datetime.now() + timedelta(days=policy.retention_period_days)
            
            # Create or update lifecycle
            lifecycle = DataLifecycle(
                data_id=data_id,
                data_type=data_type or policy.data_type,
                policy_id=policy_id,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                deletion_date=deletion_date,
                metadata={"applied_at": datetime.now().isoformat()}
            )
            
            self.data_lifecycle[data_id] = lifecycle
            self.retention_metrics["total_data_items"] += 1
            
            self.logger.info(f"Applied retention policy {policy_id} to data {data_id}")
            return True
    
    def schedule_data_deletion(self, data_id: str, deletion_date: datetime = None,
                             deletion_strategy: DeletionStrategy = None) -> str:
        """
        Schedule data for deletion.
        
        Args:
            data_id: Data ID to delete
            deletion_date: Optional custom deletion date
            deletion_strategy: Optional custom deletion strategy
            
        Returns:
            str: Deletion job ID
        """
        with self.lock:
            if data_id not in self.data_lifecycle:
                raise ValueError(f"Data {data_id} not found in lifecycle")
            
            lifecycle = self.data_lifecycle[data_id]
            policy = self.retention_policies[lifecycle.policy_id]
            
            # Use provided values or defaults
            actual_deletion_date = deletion_date or lifecycle.deletion_date
            actual_deletion_strategy = deletion_strategy or policy.deletion_strategy
            
            # Create deletion job
            job_id = str(uuid.uuid4())
            job = DeletionJob(
                job_id=job_id,
                data_ids=[data_id],
                deletion_strategy=actual_deletion_strategy,
                scheduled_date=actual_deletion_date
            )
            
            self.deletion_jobs[job_id] = job
            
            self.logger.info(f"Scheduled deletion job {job_id} for data {data_id}")
            return job_id
    
    def execute_retention_policies(self) -> Dict[str, Any]:
        """
        Execute scheduled retention policies.
        
        Returns:
            Dict[str, Any]: Execution results
        """
        start_time = time.time()
        
        with self.lock:
            current_time = datetime.now()
            jobs_to_execute = []
            
            # Find jobs ready for execution
            for job_id, job in self.deletion_jobs.items():
                if job.status == "scheduled" and job.scheduled_date <= current_time:
                    jobs_to_execute.append(job_id)
            
            results = {
                "jobs_executed": 0,
                "jobs_failed": 0,
                "data_deleted": 0,
                "data_archived": 0,
                "errors": []
            }
            
            # Execute jobs
            for job_id in jobs_to_execute:
                try:
                    job = self.deletion_jobs[job_id]
                    job.status = "in_progress"
                    
                    # Execute deletion for each data item
                    for data_id in job.data_ids:
                        if self._execute_data_deletion(data_id, job.deletion_strategy):
                            results["data_deleted"] += 1
                        else:
                            results["errors"].append(f"Failed to delete data {data_id}")
                    
                    job.status = "completed"
                    job.completed_at = datetime.now()
                    results["jobs_executed"] += 1
                    
                except Exception as e:
                    job.status = "failed"
                    results["jobs_failed"] += 1
                    results["errors"].append(f"Job {job_id} failed: {str(e)}")
                    self.logger.error(f"Deletion job {job_id} failed: {e}")
            
            # Update metrics
            operation_time = (time.time() - start_time) * 1000
            self._update_metrics(operation_time)
            
            self.logger.info(f"Executed {results['jobs_executed']} retention policies")
            return results
    
    def archive_data(self, data_id: str, archive_path: str = None) -> bool:
        """
        Archive data for long-term storage.
        
        Args:
            data_id: Data ID to archive
            archive_path: Optional custom archive path
            
        Returns:
            bool: Success status
        """
        try:
            # Create archive directory if it doesn't exist
            archive_dir = archive_path or self.archive_config["archive_path"]
            os.makedirs(archive_dir, exist_ok=True)
            
            # Generate archive filename
            archive_filename = f"{data_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            archive_filepath = os.path.join(archive_dir, archive_filename)
            
            # Create archive (simulated)
            # In a real implementation, this would create an actual archive
            with open(archive_filepath, 'w') as f:
                f.write(f"Archived data {data_id} at {datetime.now().isoformat()}")
            
            # Update lifecycle
            with self.lock:
                if data_id in self.data_lifecycle:
                    self.data_lifecycle[data_id].status = "archived"
                    self.data_lifecycle[data_id].metadata["archived_at"] = datetime.now().isoformat()
                    self.data_lifecycle[data_id].metadata["archive_path"] = archive_filepath
                
                self.retention_metrics["total_archives"] += 1
            
            self.logger.info(f"Archived data {data_id} to {archive_filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to archive data {data_id}: {e}")
            return False
    
    def get_retention_policies(self) -> List[Dict[str, Any]]:
        """
        Get all retention policies.
        
        Returns:
            List[Dict[str, Any]]: List of retention policies
        """
        return [
            {
                "policy_id": policy.policy_id,
                "data_type": policy.data_type.value,
                "retention_period_days": policy.retention_period_days,
                "deletion_strategy": policy.deletion_strategy.value,
                "description": policy.description,
                "created_at": policy.created_at.isoformat(),
                "active": policy.active,
                "metadata": policy.metadata
            }
            for policy in self.retention_policies.values()
        ]
    
    def get_data_lifecycle(self, data_id: str = None) -> List[Dict[str, Any]]:
        """
        Get data lifecycle information.
        
        Args:
            data_id: Optional specific data ID
            
        Returns:
            List[Dict[str, Any]]: Data lifecycle information
        """
        with self.lock:
            if data_id:
                if data_id in self.data_lifecycle:
                    lifecycle = self.data_lifecycle[data_id]
                    return [{
                        "data_id": lifecycle.data_id,
                        "data_type": lifecycle.data_type.value,
                        "policy_id": lifecycle.policy_id,
                        "created_at": lifecycle.created_at.isoformat(),
                        "last_accessed": lifecycle.last_accessed.isoformat(),
                        "deletion_date": lifecycle.deletion_date.isoformat(),
                        "status": lifecycle.status,
                        "metadata": lifecycle.metadata
                    }]
                return []
            
            return [
                {
                    "data_id": lifecycle.data_id,
                    "data_type": lifecycle.data_type.value,
                    "policy_id": lifecycle.policy_id,
                    "created_at": lifecycle.created_at.isoformat(),
                    "last_accessed": lifecycle.last_accessed.isoformat(),
                    "deletion_date": lifecycle.deletion_date.isoformat(),
                    "status": lifecycle.status,
                    "metadata": lifecycle.metadata
                }
                for lifecycle in self.data_lifecycle.values()
            ]
    
    def generate_compliance_report(self, date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """
        Generate compliance report for data retention.
        
        Args:
            date_range: Optional date range for report
            
        Returns:
            Dict[str, Any]: Compliance report
        """
        with self.lock:
            # Filter data by date range if provided
            lifecycle_data = list(self.data_lifecycle.values())
            if date_range:
                start_date, end_date = date_range
                lifecycle_data = [
                    data for data in lifecycle_data
                    if start_date <= data.created_at <= end_date
                ]
            
            # Calculate compliance metrics
            total_data = len(lifecycle_data)
            active_data = len([d for d in lifecycle_data if d.status == "active"])
            archived_data = len([d for d in lifecycle_data if d.status == "archived"])
            deleted_data = len([d for d in lifecycle_data if d.status == "deleted"])
            
            # Check for compliance violations
            violations = []
            current_time = datetime.now()
            for data in lifecycle_data:
                if data.status == "active" and data.deletion_date < current_time:
                    violations.append({
                        "data_id": data.data_id,
                        "data_type": data.data_type.value,
                        "deletion_date": data.deletion_date.isoformat(),
                        "days_overdue": (current_time - data.deletion_date).days
                    })
            
            return {
                "report_generated": datetime.now().isoformat(),
                "date_range": {
                    "start": date_range[0].isoformat() if date_range else None,
                    "end": date_range[1].isoformat() if date_range else None
                },
                "total_data_items": total_data,
                "active_data": active_data,
                "archived_data": archived_data,
                "deleted_data": deleted_data,
                "compliance_violations": len(violations),
                "compliance_score": self._calculate_compliance_score(total_data, len(violations)),
                "data_by_type": self._group_data_by_type(lifecycle_data),
                "violations": violations,
                "retention_policies": len(self.retention_policies)
            }
    
    def _execute_data_deletion(self, data_id: str, deletion_strategy: DeletionStrategy) -> bool:
        """
        Execute data deletion with specified strategy.
        
        Args:
            data_id: Data ID to delete
            deletion_strategy: Deletion strategy to use
            
        Returns:
            bool: Success status
        """
        try:
            if deletion_strategy == DeletionStrategy.SOFT_DELETE:
                # Mark as deleted
                with self.lock:
                    if data_id in self.data_lifecycle:
                        self.data_lifecycle[data_id].status = "deleted"
                        self.data_lifecycle[data_id].metadata["deleted_at"] = datetime.now().isoformat()
            
            elif deletion_strategy == DeletionStrategy.HARD_DELETE:
                # Remove from storage
                with self.lock:
                    if data_id in self.data_lifecycle:
                        del self.data_lifecycle[data_id]
            
            elif deletion_strategy == DeletionStrategy.SECURE_DELETE:
                # Overwrite before deletion
                # In a real implementation, this would overwrite the data
                with self.lock:
                    if data_id in self.data_lifecycle:
                        del self.data_lifecycle[data_id]
            
            elif deletion_strategy == DeletionStrategy.ARCHIVE_DELETE:
                # Archive before deletion
                if self.archive_data(data_id):
                    with self.lock:
                        if data_id in self.data_lifecycle:
                            del self.data_lifecycle[data_id]
                else:
                    return False
            
            # Update metrics
            with self.lock:
                self.retention_metrics["total_deletions"] += 1
            
            self.logger.info(f"Deleted data {data_id} using {deletion_strategy.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete data {data_id}: {e}")
            return False
    
    def _initialize_default_policies(self):
        """Initialize default retention policies"""
        default_policies = [
            (DataType.BUILDING_DATA, 1825, DeletionStrategy.ARCHIVE_DELETE, "Building data - 5 years"),
            (DataType.USER_DATA, 1095, DeletionStrategy.SOFT_DELETE, "User data - 3 years"),
            (DataType.AUDIT_LOGS, 3650, DeletionStrategy.SECURE_DELETE, "Audit logs - 10 years"),
            (DataType.AHJ_DATA, 3650, DeletionStrategy.ARCHIVE_DELETE, "AHJ data - 10 years"),
            (DataType.COMPLIANCE_REPORTS, 2555, DeletionStrategy.ARCHIVE_DELETE, "Compliance reports - 7 years"),
            (DataType.SYSTEM_LOGS, 365, DeletionStrategy.HARD_DELETE, "System logs - 1 year"),
            (DataType.BACKUP_DATA, 1095, DeletionStrategy.HARD_DELETE, "Backup data - 3 years"),
            (DataType.TEMPORARY_DATA, 30, DeletionStrategy.HARD_DELETE, "Temporary data - 30 days")
        ]
        
        for data_type, retention_days, deletion_strategy, description in default_policies:
            self.create_retention_policy(data_type, retention_days, deletion_strategy, description)
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    # Execute retention policies every hour
                    self.execute_retention_policies()
                    time.sleep(3600)  # 1 hour
                except Exception as e:
                    self.logger.error(f"Cleanup thread error: {e}")
                    time.sleep(300)  # 5 minutes on error
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.info("Started background cleanup thread")
    
    def _calculate_compliance_score(self, total_data: int, violations: int) -> float:
        """Calculate compliance score"""
        if total_data == 0:
            return 100.0
        
        violation_rate = violations / total_data
        return max(0.0, 100.0 - (violation_rate * 100))
    
    def _group_data_by_type(self, lifecycle_data: List[DataLifecycle]) -> Dict[str, int]:
        """Group data by type"""
        type_counts = {}
        for data in lifecycle_data:
            data_type = data.data_type.value
            type_counts[data_type] = type_counts.get(data_type, 0) + 1
        return type_counts
    
    def _update_metrics(self, operation_time: float):
        """Update retention performance metrics"""
        current_avg = self.retention_metrics["average_deletion_time_ms"]
        total_deletions = self.retention_metrics["total_deletions"]
        
        if total_deletions > 0:
            self.retention_metrics["average_deletion_time_ms"] = (
                (current_avg * (total_deletions - 1) + operation_time) / total_deletions
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get retention performance metrics"""
        return self.retention_metrics.copy() 