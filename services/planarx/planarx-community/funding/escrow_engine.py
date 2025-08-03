"""
Funding Escrow Engine for Planarx Community Platform
Manages secure fund releases based on milestone approvals and governance oversight
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


class EscrowStatus(Enum):
    """Escrow account status states"""
    PENDING = "pending"
    ACTIVE = "active"
    MILESTONE_RELEASE = "milestone_release"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class MilestoneStatus(Enum):
    """Milestone approval status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    OVERRIDE_APPROVED = "override_approved"


class TransactionType(Enum):
    """Transaction types for audit trail"""
    ESCROW_CREATED = "escrow_created"
    FUNDS_DEPOSITED = "funds_deposited"
    MILESTONE_SUBMITTED = "milestone_submitted"
    MILESTONE_APPROVED = "milestone_approved"
    MILESTONE_REJECTED = "milestone_rejected"
    FUNDS_RELEASED = "funds_released"
    OVERRIDE_APPROVED = "override_approved"
    ESCROW_CANCELLED = "escrow_cancelled"


@dataclass
class Milestone:
    """Milestone definition with approval tracking"""
    id: str
    title: str
    description: str
    amount: Decimal
    due_date: datetime
    status: MilestoneStatus
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    evidence_urls: List[str] = None
    
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
        if self.evidence_urls is None:
            self.evidence_urls = []


@dataclass
class Transaction:
    """Audit transaction record"""
    id: str
    escrow_id: str
    transaction_type: TransactionType
    amount: Optional[Decimal]
    description: str
    timestamp: datetime
    user_id: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EscrowAccount:
    """Escrow account with milestone tracking"""
    id: str
    project_id: str
    creator_id: str
    total_amount: Decimal
    current_balance: Decimal
    status: EscrowStatus
    created_at: datetime
    milestones: List[Milestone]
    transactions: List[Transaction]
    governance_board: List[str]
    auto_release_enabled: bool = True
    dispute_resolution: Optional[str] = None
    
    def __post_init__(self):
        if self.milestones is None:
            self.milestones = []
        if self.transactions is None:
            self.transactions = []
        if self.governance_board is None:
            self.governance_board = []


class EscrowEngine:
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Core escrow management engine"""
    
    def __init__(self):
        self.escrow_accounts: Dict[str, EscrowAccount] = {}
        self.pending_approvals: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_escrow_account(
        self,
        project_id: str,
        creator_id: str,
        total_amount: Decimal,
        milestones: List[Dict],
        governance_board: List[str],
        auto_release: bool = True
    ) -> EscrowAccount:
        """Create a new escrow account for a project"""
        
        escrow_id = str(uuid.uuid4())
        
        # Convert milestone dicts to Milestone objects
        milestone_objects = []
        for i, milestone_data in enumerate(milestones):
            milestone = Milestone(
                id=str(uuid.uuid4()),
                title=milestone_data["title"],
                description=milestone_data["description"],
                amount=Decimal(str(milestone_data["amount"])),
                due_date=datetime.fromisoformat(milestone_data["due_date"]),
                status=MilestoneStatus.PENDING
            )
            milestone_objects.append(milestone)
        
        escrow_account = EscrowAccount(
            id=escrow_id,
            project_id=project_id,
            creator_id=creator_id,
            total_amount=total_amount,
            current_balance=Decimal("0"),
            status=EscrowStatus.PENDING,
            created_at=datetime.utcnow(),
            milestones=milestone_objects,
            transactions=[],
            governance_board=governance_board,
            auto_release_enabled=auto_release
        )
        
        # Add initial transaction
        initial_transaction = Transaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=TransactionType.ESCROW_CREATED,
            amount=None,
            description=f"Escrow account created for project {project_id}",
            timestamp=datetime.utcnow(),
            metadata={
                "total_amount": str(total_amount),
                "milestone_count": len(milestone_objects),
                "governance_board_size": len(governance_board)
            }
        )
        escrow_account.transactions.append(initial_transaction)
        
        self.escrow_accounts[escrow_id] = escrow_account
        self.logger.info(f"Created escrow account {escrow_id} for project {project_id}")
        
        return escrow_account
    
    def deposit_funds(self, escrow_id: str, amount: Decimal, user_id: str) -> bool:
        """Deposit funds into escrow account"""
        
        if escrow_id not in self.escrow_accounts:
            raise ValueError(f"Escrow account {escrow_id} not found")
        
        escrow = self.escrow_accounts[escrow_id]
        
        if escrow.status != EscrowStatus.PENDING and escrow.status != EscrowStatus.ACTIVE:
            raise ValueError(f"Cannot deposit funds to escrow in {escrow.status} status")
        
        escrow.current_balance += amount
        
        # Add transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=TransactionType.FUNDS_DEPOSITED,
            amount=amount,
            description=f"Funds deposited by user {user_id}",
            timestamp=datetime.utcnow(),
            user_id=user_id
        )
        escrow.transactions.append(transaction)
        
        # Activate escrow if target reached
        if escrow.current_balance >= escrow.total_amount:
            escrow.status = EscrowStatus.ACTIVE
            self.logger.info(f"Escrow account {escrow_id} activated")
        
        self.logger.info(f"Deposited {amount} to escrow {escrow_id}")
        return True
    
    def submit_milestone(
        self,
        escrow_id: str,
        milestone_id: str,
        evidence_urls: List[str],
        creator_id: str
    ) -> bool:
        """Submit a milestone for approval"""
        
        if escrow_id not in self.escrow_accounts:
            raise ValueError(f"Escrow account {escrow_id} not found")
        
        escrow = self.escrow_accounts[escrow_id]
        
        if escrow.status != EscrowStatus.ACTIVE:
            raise ValueError(f"Cannot submit milestone to escrow in {escrow.status} status")
        
        # Find milestone
        milestone = None
        for m in escrow.milestones:
            if m.id == milestone_id:
                milestone = m
                break
        
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        if milestone.status != MilestoneStatus.PENDING:
            raise ValueError(f"Milestone {milestone_id} already submitted or completed")
        
        # Update milestone
        milestone.status = MilestoneStatus.SUBMITTED
        milestone.submitted_at = datetime.utcnow()
        milestone.evidence_urls = evidence_urls
        
        # Add transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=TransactionType.MILESTONE_SUBMITTED,
            amount=milestone.amount,
            description=f"Milestone '{milestone.title}' submitted for approval",
            timestamp=datetime.utcnow(),
            user_id=creator_id,
            metadata={
                "milestone_id": milestone_id,
                "evidence_urls": evidence_urls
            }
        )
        escrow.transactions.append(transaction)
        
        # Notify governance board
        self._notify_governance_board(escrow_id, milestone_id)
        
        self.logger.info(f"Milestone {milestone_id} submitted for approval")
        return True
    
    def approve_milestone(
        self,
        escrow_id: str,
        milestone_id: str,
        approver_id: str,
        is_override: bool = False
    ) -> bool:
        """Approve a milestone and release funds"""
        
        if escrow_id not in self.escrow_accounts:
            raise ValueError(f"Escrow account {escrow_id} not found")
        
        escrow = self.escrow_accounts[escrow_id]
        
        # Verify approver is on governance board
        if approver_id not in escrow.governance_board:
            raise ValueError(f"User {approver_id} not authorized to approve milestones")
        
        # Find milestone
        milestone = None
        for m in escrow.milestones:
            if m.id == milestone_id:
                milestone = m
                break
        
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        if milestone.status != MilestoneStatus.SUBMITTED:
            raise ValueError(f"Milestone {milestone_id} not in submitted status")
        
        # Update milestone
        milestone.status = MilestoneStatus.OVERRIDE_APPROVED if is_override else MilestoneStatus.APPROVED
        milestone.approved_at = datetime.utcnow()
        milestone.approved_by = approver_id
        
        # Release funds
        escrow.current_balance -= milestone.amount
        
        # Add transaction
        transaction_type = TransactionType.OVERRIDE_APPROVED if is_override else TransactionType.MILESTONE_APPROVED
        transaction = Transaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=transaction_type,
            amount=milestone.amount,
            description=f"Milestone '{milestone.title}' approved by {approver_id}",
            timestamp=datetime.utcnow(),
            user_id=approver_id,
            metadata={
                "milestone_id": milestone_id,
                "is_override": is_override
            }
        )
        escrow.transactions.append(transaction)
        
        # Add fund release transaction
        release_transaction = Transaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=TransactionType.FUNDS_RELEASED,
            amount=milestone.amount,
            description=f"Funds released for milestone '{milestone.title}'",
            timestamp=datetime.utcnow(),
            user_id=escrow.creator_id,
            metadata={
                "milestone_id": milestone_id,
                "recipient": escrow.creator_id
            }
        )
        escrow.transactions.append(release_transaction)
        
        # Check if all milestones completed
        if self._all_milestones_completed(escrow):
            escrow.status = EscrowStatus.COMPLETED
            self.logger.info(f"Escrow account {escrow_id} completed")
        
        self.logger.info(f"Milestone {milestone_id} approved and funds released")
        return True
    
    def reject_milestone(
        self,
        escrow_id: str,
        milestone_id: str,
        rejector_id: str,
        reason: str
    ) -> bool:
        """Reject a milestone"""
        
        if escrow_id not in self.escrow_accounts:
            raise ValueError(f"Escrow account {escrow_id} not found")
        
        escrow = self.escrow_accounts[escrow_id]
        
        # Verify rejector is on governance board
        if rejector_id not in escrow.governance_board:
            raise ValueError(f"User {rejector_id} not authorized to reject milestones")
        
        # Find milestone
        milestone = None
        for m in escrow.milestones:
            if m.id == milestone_id:
                milestone = m
                break
        
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        if milestone.status != MilestoneStatus.SUBMITTED:
            raise ValueError(f"Milestone {milestone_id} not in submitted status")
        
        # Update milestone
        milestone.status = MilestoneStatus.REJECTED
        milestone.rejection_reason = reason
        
        # Add transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=TransactionType.MILESTONE_REJECTED,
            amount=milestone.amount,
            description=f"Milestone '{milestone.title}' rejected: {reason}",
            timestamp=datetime.utcnow(),
            user_id=rejector_id,
            metadata={
                "milestone_id": milestone_id,
                "rejection_reason": reason
            }
        )
        escrow.transactions.append(transaction)
        
        self.logger.info(f"Milestone {milestone_id} rejected: {reason}")
        return True
    
    def get_escrow_summary(self, escrow_id: str) -> Dict:
        """Get comprehensive escrow account summary"""
        
        if escrow_id not in self.escrow_accounts:
            raise ValueError(f"Escrow account {escrow_id} not found")
        
        escrow = self.escrow_accounts[escrow_id]
        
        # Calculate statistics
        total_milestones = len(escrow.milestones)
        completed_milestones = len([m for m in escrow.milestones if m.status in [MilestoneStatus.APPROVED, MilestoneStatus.OVERRIDE_APPROVED]])
        pending_milestones = len([m for m in escrow.milestones if m.status == MilestoneStatus.SUBMITTED])
        total_released = sum(m.amount for m in escrow.milestones if m.status in [MilestoneStatus.APPROVED, MilestoneStatus.OVERRIDE_APPROVED])
        
        return {
            "escrow_id": escrow_id,
            "project_id": escrow.project_id,
            "creator_id": escrow.creator_id,
            "status": escrow.status.value,
            "total_amount": str(escrow.total_amount),
            "current_balance": str(escrow.current_balance),
            "total_released": str(total_released),
            "funding_progress": float(escrow.current_balance / escrow.total_amount * 100),
            "milestone_stats": {
                "total": total_milestones,
                "completed": completed_milestones,
                "pending_approval": pending_milestones,
                "remaining": total_milestones - completed_milestones
            },
            "governance_board": escrow.governance_board,
            "auto_release_enabled": escrow.auto_release_enabled,
            "created_at": escrow.created_at.isoformat(),
            "recent_transactions": [
                {
                    "id": t.id,
                    "type": t.transaction_type.value,
                    "amount": str(t.amount) if t.amount else None,
                    "description": t.description,
                    "timestamp": t.timestamp.isoformat(),
                    "user_id": t.user_id
                }
                for t in sorted(escrow.transactions, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }
    
    def get_milestone_details(self, escrow_id: str, milestone_id: str) -> Dict:
        """Get detailed milestone information"""
        
        if escrow_id not in self.escrow_accounts:
            raise ValueError(f"Escrow account {escrow_id} not found")
        
        escrow = self.escrow_accounts[escrow_id]
        
        milestone = None
        for m in escrow.milestones:
            if m.id == milestone_id:
                milestone = m
                break
        
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        return {
            "id": milestone.id,
            "title": milestone.title,
            "description": milestone.description,
            "amount": str(milestone.amount),
            "status": milestone.status.value,
            "due_date": milestone.due_date.isoformat(),
            "submitted_at": milestone.submitted_at.isoformat() if milestone.submitted_at else None,
            "approved_at": milestone.approved_at.isoformat() if milestone.approved_at else None,
            "approved_by": milestone.approved_by,
            "rejection_reason": milestone.rejection_reason,
            "evidence_urls": milestone.evidence_urls,
            "is_overdue": datetime.utcnow() > milestone.due_date and milestone.status == MilestoneStatus.PENDING
        }
    
    def _notify_governance_board(self, escrow_id: str, milestone_id: str):
        """Notify governance board of milestone submission"""
        if escrow_id not in self.pending_approvals:
            self.pending_approvals[escrow_id] = []
        
        if milestone_id not in self.pending_approvals[escrow_id]:
            self.pending_approvals[escrow_id].append(milestone_id)
    
    def _all_milestones_completed(self, escrow: EscrowAccount) -> bool:
        """Check if all milestones are completed"""
        return all(
            m.status in [MilestoneStatus.APPROVED, MilestoneStatus.OVERRIDE_APPROVED]
            for m in escrow.milestones
        )
    
    def get_pending_approvals(self, user_id: str) -> List[Dict]:
        """Get pending approvals for a governance board member"""
        pending = []
        
        for escrow_id, milestone_ids in self.pending_approvals.items():
            if escrow_id in self.escrow_accounts:
                escrow = self.escrow_accounts[escrow_id]
                if user_id in escrow.governance_board:
                    for milestone_id in milestone_ids:
                        milestone = next((m for m in escrow.milestones if m.id == milestone_id), None)
                        if milestone and milestone.status == MilestoneStatus.SUBMITTED:
                            pending.append({
                                "escrow_id": escrow_id,
                                "milestone_id": milestone_id,
                                "project_id": escrow.project_id,
                                "milestone_title": milestone.title,
                                "amount": str(milestone.amount),
                                "submitted_at": milestone.submitted_at.isoformat() if milestone.submitted_at else None
                            })
        
        return pending


# Global escrow engine instance
escrow_engine = EscrowEngine() 