"""
Funding Escrow API Routes
Handles escrow account creation, fund deposits, and milestone management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
import logging

from ..escrow_engine import escrow_engine, EscrowAccount, MilestoneStatus, TransactionType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/funding/escrow", tags=["Funding Escrow"])


class MilestoneCreate(BaseModel):
    """Milestone creation request"""
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Milestone description")
    amount: Decimal = Field(..., description="Fund amount for this milestone")
    due_date: datetime = Field(..., description="Milestone due date")


class EscrowCreateRequest(BaseModel):
    """Escrow account creation request"""
    project_id: str = Field(..., description="Project ID")
    creator_id: str = Field(..., description="Project creator ID")
    total_amount: Decimal = Field(..., description="Total funding goal")
    milestones: List[MilestoneCreate] = Field(..., description="Project milestones")
    governance_board: List[str] = Field(..., description="Governance board member IDs")
    auto_release: bool = Field(True, description="Enable automatic fund release")


class FundDepositRequest(BaseModel):
    """Fund deposit request"""
    amount: Decimal = Field(..., description="Amount to deposit")
    user_id: str = Field(..., description="User making the deposit")


class MilestoneSubmitRequest(BaseModel):
    """Milestone submission request"""
    evidence_urls: List[str] = Field(..., description="Evidence URLs for milestone completion")


class MilestoneApprovalRequest(BaseModel):
    """Milestone approval/rejection request"""
    approver_id: str = Field(..., description="Governance board member ID")
    is_override: bool = Field(False, description="Override approval (for disputed cases)")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")


@router.post("/create", response_model=Dict)
async def create_escrow_account(request: EscrowCreateRequest):
    """Create a new escrow account for project funding"""
    try:
        # Validate milestone amounts sum to total
        milestone_sum = sum(m.amount for m in request.milestones)
        if milestone_sum != request.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Milestone amounts ({milestone_sum}) must equal total amount ({request.total_amount})"
            )
        
        # Convert to dict format for engine
        milestones_data = [
            {
                "title": m.title,
                "description": m.description,
                "amount": str(m.amount),
                "due_date": m.due_date.isoformat()
            }
            for m in request.milestones
        ]
        
        escrow_account = escrow_engine.create_escrow_account(
            project_id=request.project_id,
            creator_id=request.creator_id,
            total_amount=request.total_amount,
            milestones=milestones_data,
            governance_board=request.governance_board,
            auto_release=request.auto_release
        )
        
        logger.info(f"Created escrow account {escrow_account.id} for project {request.project_id}")
        
        return {
            "escrow_id": escrow_account.id,
            "status": "created",
            "message": "Escrow account created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create escrow account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create escrow account: {str(e)}"
        )


@router.post("/{escrow_id}/deposit", response_model=Dict)
async def deposit_funds(escrow_id: str, request: FundDepositRequest):
    """Deposit funds into escrow account"""
    try:
        success = escrow_engine.deposit_funds(
            escrow_id=escrow_id,
            amount=request.amount,
            user_id=request.user_id
        )
        
        if success:
            return {
                "escrow_id": escrow_id,
                "amount_deposited": str(request.amount),
                "status": "success",
                "message": "Funds deposited successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deposit funds"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to deposit funds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deposit funds: {str(e)}"
        )


@router.post("/{escrow_id}/milestones/{milestone_id}/submit", response_model=Dict)
async def submit_milestone(
    escrow_id: str,
    milestone_id: str,
    request: MilestoneSubmitRequest
):
    """Submit a milestone for approval"""
    try:
        success = escrow_engine.submit_milestone(
            escrow_id=escrow_id,
            milestone_id=milestone_id,
            evidence_urls=request.evidence_urls,
            creator_id=request.user_id  # Assuming user_id is passed in request
        )
        
        if success:
            return {
                "escrow_id": escrow_id,
                "milestone_id": milestone_id,
                "status": "submitted",
                "message": "Milestone submitted for approval"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to submit milestone"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit milestone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit milestone: {str(e)}"
        )


@router.post("/{escrow_id}/milestones/{milestone_id}/approve", response_model=Dict)
async def approve_milestone(
    escrow_id: str,
    milestone_id: str,
    request: MilestoneApprovalRequest
):
    """Approve a milestone and release funds"""
    try:
        success = escrow_engine.approve_milestone(
            escrow_id=escrow_id,
            milestone_id=milestone_id,
            approver_id=request.approver_id,
            is_override=request.is_override
        )
        
        if success:
            return {
                "escrow_id": escrow_id,
                "milestone_id": milestone_id,
                "status": "approved",
                "message": "Milestone approved and funds released"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to approve milestone"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to approve milestone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve milestone: {str(e)}"
        )


@router.post("/{escrow_id}/milestones/{milestone_id}/reject", response_model=Dict)
async def reject_milestone(
    escrow_id: str,
    milestone_id: str,
    request: MilestoneApprovalRequest
):
    """Reject a milestone"""
    if not request.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required"
        )
    
    try:
        success = escrow_engine.reject_milestone(
            escrow_id=escrow_id,
            milestone_id=milestone_id,
            rejector_id=request.approver_id,
            reason=request.rejection_reason
        )
        
        if success:
            return {
                "escrow_id": escrow_id,
                "milestone_id": milestone_id,
                "status": "rejected",
                "message": "Milestone rejected",
                "reason": request.rejection_reason
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reject milestone"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to reject milestone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject milestone: {str(e)}"
        )


@router.get("/{escrow_id}/summary", response_model=Dict)
async def get_escrow_summary(escrow_id: str):
    """Get comprehensive escrow account summary"""
    try:
        summary = escrow_engine.get_escrow_summary(escrow_id)
        return summary
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get escrow summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get escrow summary: {str(e)}"
        )


@router.get("/{escrow_id}/milestones/{milestone_id}", response_model=Dict)
async def get_milestone_details(escrow_id: str, milestone_id: str):
    """Get detailed milestone information"""
    try:
        details = escrow_engine.get_milestone_details(escrow_id, milestone_id)
        return details
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get milestone details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get milestone details: {str(e)}"
        )


@router.get("/pending-approvals/{user_id}", response_model=List[Dict])
async def get_pending_approvals(user_id: str):
    """Get pending approvals for a governance board member"""
    try:
        pending = escrow_engine.get_pending_approvals(user_id)
        return pending
        
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending approvals: {str(e)}"
        )


@router.get("/{escrow_id}/transactions", response_model=List[Dict])
async def get_escrow_transactions(escrow_id: str, limit: int = 50):
    """Get transaction history for an escrow account"""
    try:
        if escrow_id not in escrow_engine.escrow_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escrow account {escrow_id} not found"
            )
        
        escrow = escrow_engine.escrow_accounts[escrow_id]
        transactions = sorted(escrow.transactions, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "id": t.id,
                "type": t.transaction_type.value,
                "amount": str(t.amount) if t.amount else None,
                "description": t.description,
                "timestamp": t.timestamp.isoformat(),
                "user_id": t.user_id,
                "metadata": t.metadata
            }
            for t in transactions
        ]
        
    except Exception as e:
        logger.error(f"Failed to get escrow transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get escrow transactions: {str(e)}"
        ) 