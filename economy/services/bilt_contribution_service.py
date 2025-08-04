"""
BILT Contribution Service

Handles contribution-based minting with secondary user verification.
Each contribution must be verified by another user before BILT is minted.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
from uuid import uuid4

from economy.contracts.bilt_contract import BILTContract
from economy.models.contribution import Contribution, ContributionStatus, ContributionLevel
from economy.models.verification import Verification

logger = logging.getLogger(__name__)

class ContributionService:
    """Service for managing BILT contributions and minting"""
    
    def __init__(self):
        self.bilt_contract = BILTContract()
        self.contributions: Dict[str, Contribution] = {}
        self.verifications: Dict[str, List[Verification]] = {}
    
    async def create_contribution(
        self,
        user_id: str,
        contribution_type: str,
        data: Dict[str, Any],
        level: ContributionLevel
    ) -> Contribution:
        """Create a new contribution that requires verification"""
        
        contribution_id = str(uuid4())
        
        contribution = Contribution(
            id=contribution_id,
            user_id=user_id,
            type=contribution_type,
            data=data,
            level=level,
            status=ContributionStatus.PENDING_VERIFICATION,
            created_at=datetime.utcnow(),
            bilt_amount=self._calculate_bilt_amount(level)
        )
        
        self.contributions[contribution_id] = contribution
        self.verifications[contribution_id] = []
        
        logger.info(f"Created contribution {contribution_id} by user {user_id} for {contribution.bilt_amount} BILT")
        
        return contribution
    
    async def verify_contribution(
        self,
        contribution_id: str,
        verifier_id: str,
        approved: bool,
        feedback: Optional[str] = None
    ) -> bool:
        """Verify a contribution by a secondary user"""
        
        if contribution_id not in self.contributions:
            raise ValueError(f"Contribution {contribution_id} not found")
        
        contribution = self.contributions[contribution_id]
        
        # Prevent self-verification
        if verifier_id == contribution.user_id:
            raise ValueError("Users cannot verify their own contributions")
        
        # Create verification record
        verification = Verification(
            contribution_id=contribution_id,
            verifier_id=verifier_id,
            approved=approved,
            feedback=feedback,
            verified_at=datetime.utcnow()
        )
        
        self.verifications[contribution_id].append(verification)
        
        # Check if contribution should be approved/rejected
        verifications = self.verifications[contribution_id]
        approved_count = sum(1 for v in verifications if v.approved)
        total_count = len(verifications)
        
        # Require at least 1 approval for minting
        if approved_count >= 1:
            await self._mint_bilt(contribution)
            contribution.status = ContributionStatus.APPROVED
            logger.info(f"Contribution {contribution_id} approved and {contribution.bilt_amount} BILT minted")
            return True
        elif total_count >= 2 and approved_count == 0:
            # Reject if 2+ verifications and no approvals
            contribution.status = ContributionStatus.REJECTED
            logger.info(f"Contribution {contribution_id} rejected")
            return False
        
        return False
    
    async def _mint_bilt(self, contribution: Contribution):
        """Mint BILT tokens for approved contribution"""
        try:
            await self.bilt_contract.mint_tokens(
                user_id=contribution.user_id,
                amount=contribution.bilt_amount,
                reason=f"Contribution: {contribution.type}"
            )
            logger.info(f"Minted {contribution.bilt_amount} BILT for user {contribution.user_id}")
        except Exception as e:
            logger.error(f"Failed to mint BILT for contribution {contribution.id}: {e}")
            raise
    
    def _calculate_bilt_amount(self, level: ContributionLevel) -> int:
        """Calculate BILT amount based on contribution level"""
        amounts = {
            ContributionLevel.BARE_MINIMUM: 1,
            ContributionLevel.BASIC: 5,
            ContributionLevel.STANDARD: 15,
            ContributionLevel.ADVANCED: 50,
            ContributionLevel.EXPERT: 100
        }
        return amounts.get(level, 1)
    
    async def get_user_contributions(self, user_id: str) -> List[Contribution]:
        """Get all contributions by a user"""
        return [c for c in self.contributions.values() if c.user_id == user_id]
    
    async def get_pending_verifications(self, exclude_user_id: str) -> List[Contribution]:
        """Get contributions pending verification (excluding user's own)"""
        return [
            c for c in self.contributions.values() 
            if c.status == ContributionStatus.PENDING_VERIFICATION 
            and c.user_id != exclude_user_id
        ]
    
    async def get_contribution_status(self, contribution_id: str) -> Optional[Contribution]:
        """Get status of a specific contribution"""
        return self.contributions.get(contribution_id)
    
    async def get_user_bilt_balance(self, user_id: str) -> int:
        """Get user's BILT balance"""
        return await self.bilt_contract.get_balance(user_id)
    
    async def get_contribution_statistics(self) -> Dict[str, Any]:
        """Get overall contribution statistics"""
        total_contributions = len(self.contributions)
        approved_contributions = len([c for c in self.contributions.values() if c.status == ContributionStatus.APPROVED])
        pending_contributions = len([c for c in self.contributions.values() if c.status == ContributionStatus.PENDING_VERIFICATION])
        total_bilt_minted = sum(c.bilt_amount for c in self.contributions.values() if c.status == ContributionStatus.APPROVED)
        
        return {
            "total_contributions": total_contributions,
            "approved_contributions": approved_contributions,
            "pending_contributions": pending_contributions,
            "total_bilt_minted": total_bilt_minted,
            "approval_rate": approved_contributions / total_contributions if total_contributions > 0 else 0
        } 