"""
User Agreement Flags System
Tracks user agreement to community guidelines and manages compliance status
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class AgreementStatus(Enum):
    """User agreement status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AgreementType(Enum):
    """Types of agreements"""
    COMMUNITY_GUIDELINES = "community_guidelines"
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    FUNDING_AGREEMENT = "funding_agreement"
    COLLABORATION_AGREEMENT = "collaboration_agreement"


@dataclass
class UserAgreement:
    """User agreement record"""
    id: str
    user_id: str
    agreement_type: AgreementType
    agreement_version: str
    status: AgreementStatus
    accepted_at: Optional[datetime]
    declined_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: str
    user_agent: str
    acceptance_method: str  # "onboarding", "update", "re-acceptance", "manual"
    metadata: Dict
    
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
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ComplianceStatus:
    """User compliance status"""
    user_id: str
    is_compliant: bool
    missing_agreements: List[AgreementType]
    expired_agreements: List[AgreementType]
    last_compliance_check: datetime
    compliance_score: float  # 0.0 to 1.0
    restrictions: List[str]
    
    def __post_init__(self):
        if self.missing_agreements is None:
            self.missing_agreements = []
        if self.expired_agreements is None:
            self.expired_agreements = []
        if self.restrictions is None:
            self.restrictions = []


class UserAgreementManager:
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
    """Manages user agreements and compliance"""
    
    def __init__(self):
        self.user_agreements: Dict[str, List[UserAgreement]] = {}
        self.compliance_status: Dict[str, ComplianceStatus] = {}
        self.agreement_versions: Dict[AgreementType, str] = {}
        self.required_agreements: Set[AgreementType] = set()
        self.agreement_expiry_days: Dict[AgreementType, int] = {}
        
        self.logger = logging.getLogger(__name__)
        
        self._initialize_agreements()
    
    def _initialize_agreements(self):
        """Initialize agreement configurations"""
        
        # Set current agreement versions
        self.agreement_versions = {
            AgreementType.COMMUNITY_GUIDELINES: "1.0.0",
            AgreementType.PRIVACY_POLICY: "2.1.0",
            AgreementType.TERMS_OF_SERVICE: "3.0.0",
            AgreementType.FUNDING_AGREEMENT: "1.0.0",
            AgreementType.COLLABORATION_AGREEMENT: "1.0.0"
        }
        
        # Set required agreements
        self.required_agreements = {
            AgreementType.COMMUNITY_GUIDELINES,
            AgreementType.PRIVACY_POLICY,
            AgreementType.TERMS_OF_SERVICE
        }
        
        # Set expiry periods (days)
        self.agreement_expiry_days = {
            AgreementType.COMMUNITY_GUIDELINES: 365,  # 1 year
            AgreementType.PRIVACY_POLICY: 730,  # 2 years
            AgreementType.TERMS_OF_SERVICE: 1095,  # 3 years
            AgreementType.FUNDING_AGREEMENT: 365,
            AgreementType.COLLABORATION_AGREEMENT: 180  # 6 months
        }
    
    def accept_agreement(
        self,
        user_id: str,
        agreement_type: AgreementType,
        ip_address: str,
        user_agent: str,
        acceptance_method: str = "manual",
        metadata: Dict = None
    ) -> UserAgreement:
        """Accept an agreement"""
        
        agreement_version = self.agreement_versions.get(agreement_type)
        if not agreement_version:
            raise ValueError(f"Unknown agreement type: {agreement_type}")
        
        # Calculate expiry date
        expiry_days = self.agreement_expiry_days.get(agreement_type, 365)
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        # Create agreement record
        agreement = UserAgreement(
            id=str(uuid.uuid4()),
            user_id=user_id,
            agreement_type=agreement_type,
            agreement_version=agreement_version,
            status=AgreementStatus.ACCEPTED,
            accepted_at=datetime.utcnow(),
            declined_at=None,
            expires_at=expires_at,
            revoked_at=None,
            ip_address=ip_address,
            user_agent=user_agent,
            acceptance_method=acceptance_method,
            metadata=metadata or {}
        )
        
        # Store agreement
        if user_id not in self.user_agreements:
            self.user_agreements[user_id] = []
        
        # Revoke previous agreements of same type
        for existing_agreement in self.user_agreements[user_id]:
            if existing_agreement.agreement_type == agreement_type:
                existing_agreement.status = AgreementStatus.REVOKED
                existing_agreement.revoked_at = datetime.utcnow()
        
        self.user_agreements[user_id].append(agreement)
        
        # Update compliance status
        self._update_compliance_status(user_id)
        
        self.logger.info(f"User {user_id} accepted {agreement_type.value} version {agreement_version}")
        return agreement
    
    def decline_agreement(
        self,
        user_id: str,
        agreement_type: AgreementType,
        ip_address: str,
        user_agent: str,
        reason: str = None
    ) -> UserAgreement:
        """Decline an agreement"""
        
        agreement_version = self.agreement_versions.get(agreement_type)
        if not agreement_version:
            raise ValueError(f"Unknown agreement type: {agreement_type}")
        
        # Create declined agreement record
        agreement = UserAgreement(
            id=str(uuid.uuid4()),
            user_id=user_id,
            agreement_type=agreement_type,
            agreement_version=agreement_version,
            status=AgreementStatus.DECLINED,
            accepted_at=None,
            declined_at=datetime.utcnow(),
            expires_at=None,
            revoked_at=None,
            ip_address=ip_address,
            user_agent=user_agent,
            acceptance_method="declined",
            metadata={"reason": reason} if reason else {}
        )
        
        # Store agreement
        if user_id not in self.user_agreements:
            self.user_agreements[user_id] = []
        
        self.user_agreements[user_id].append(agreement)
        
        # Update compliance status
        self._update_compliance_status(user_id)
        
        self.logger.info(f"User {user_id} declined {agreement_type.value}")
        return agreement
    
    def revoke_agreement(
        self,
        user_id: str,
        agreement_type: AgreementType,
        reason: str = None
    ) -> Optional[UserAgreement]:
        """Revoke an agreement (admin action)"""
        
        if user_id not in self.user_agreements:
            return None
        
        for agreement in self.user_agreements[user_id]:
            if (agreement.agreement_type == agreement_type and 
                agreement.status == AgreementStatus.ACCEPTED):
                
                agreement.status = AgreementStatus.REVOKED
                agreement.revoked_at = datetime.utcnow()
                if reason:
                    agreement.metadata["revocation_reason"] = reason
                
                # Update compliance status
                self._update_compliance_status(user_id)
                
                self.logger.info(f"Revoked {agreement_type.value} for user {user_id}")
                return agreement
        
        return None
    
    def check_agreement_status(
        self,
        user_id: str,
        agreement_type: AgreementType
    ) -> Optional[UserAgreement]:
        """Check current agreement status for user"""
        
        if user_id not in self.user_agreements:
            return None
        
        # Find the most recent accepted agreement
        current_agreement = None
        for agreement in self.user_agreements[user_id]:
            if agreement.agreement_type == agreement_type:
                if agreement.status == AgreementStatus.ACCEPTED:
                    if (current_agreement is None or 
                        agreement.accepted_at > current_agreement.accepted_at):
                        current_agreement = agreement
        
        return current_agreement
    
    def is_agreement_valid(
        self,
        user_id: str,
        agreement_type: AgreementType
    ) -> bool:
        """Check if user has a valid agreement"""
        
        agreement = self.check_agreement_status(user_id, agreement_type)
        if not agreement:
            return False
        
        # Check if agreement has expired
        if agreement.expires_at and agreement.expires_at < datetime.utcnow():
            agreement.status = AgreementStatus.EXPIRED
            self._update_compliance_status(user_id)
            return False
        
        return True
    
    def get_user_agreements(self, user_id: str) -> List[UserAgreement]:
        """Get all agreements for a user"""
        
        return self.user_agreements.get(user_id, [])
    
    def get_agreement_history(
        self,
        user_id: str,
        agreement_type: AgreementType
    ) -> List[UserAgreement]:
        """Get agreement history for specific type"""
        
        agreements = self.get_user_agreements(user_id)
        return [a for a in agreements if a.agreement_type == agreement_type]
    
    def _update_compliance_status(self, user_id: str):
        """Update user's compliance status"""
        
        missing_agreements = []
        expired_agreements = []
        restrictions = []
        
        # Check required agreements
        for agreement_type in self.required_agreements:
            if not self.is_agreement_valid(user_id, agreement_type):
                missing_agreements.append(agreement_type)
                
                # Add restrictions based on missing agreements
                if agreement_type == AgreementType.COMMUNITY_GUIDELINES:
                    restrictions.extend([
                        "cannot_submit_drafts",
                        "cannot_comment",
                        "cannot_collaborate"
                    ])
                elif agreement_type == AgreementType.PRIVACY_POLICY:
                    restrictions.extend([
                        "cannot_access_personal_data",
                        "limited_profile_visibility"
                    ])
                elif agreement_type == AgreementType.TERMS_OF_SERVICE:
                    restrictions.extend([
                        "cannot_fund_projects",
                        "cannot_receive_funding"
                    ])
        
        # Check for expired agreements
        for agreement_type in self.required_agreements:
            agreement = self.check_agreement_status(user_id, agreement_type)
            if (agreement and agreement.expires_at and 
                agreement.expires_at < datetime.utcnow()):
                expired_agreements.append(agreement_type)
        
        # Calculate compliance score
        total_required = len(self.required_agreements)
        valid_agreements = total_required - len(missing_agreements)
        compliance_score = valid_agreements / total_required if total_required > 0 else 0.0
        
        # Determine if user is compliant
        is_compliant = len(missing_agreements) == 0 and len(expired_agreements) == 0
        
        compliance_status = ComplianceStatus(
            user_id=user_id,
            is_compliant=is_compliant,
            missing_agreements=missing_agreements,
            expired_agreements=expired_agreements,
            last_compliance_check=datetime.utcnow(),
            compliance_score=compliance_score,
            restrictions=restrictions
        )
        
        self.compliance_status[user_id] = compliance_status
    
    def get_compliance_status(self, user_id: str) -> ComplianceStatus:
        """Get user's compliance status"""
        
        if user_id not in self.compliance_status:
            self._update_compliance_status(user_id)
        
        return self.compliance_status[user_id]
    
    def check_user_compliance(self, user_id: str) -> bool:
        """Check if user is compliant with all required agreements"""
        
        compliance_status = self.get_compliance_status(user_id)
        return compliance_status.is_compliant
    
    def get_user_restrictions(self, user_id: str) -> List[str]:
        """Get current restrictions for user"""
        
        compliance_status = self.get_compliance_status(user_id)
        return compliance_status.restrictions
    
    def update_agreement_version(
        self,
        agreement_type: AgreementType,
        new_version: str
    ):
        """Update agreement version (triggers re-acceptance requirement)"""
        
        old_version = self.agreement_versions.get(agreement_type)
        self.agreement_versions[agreement_type] = new_version
        
        self.logger.info(f"Updated {agreement_type.value} version from {old_version} to {new_version}")
    
    def require_reacceptance(self, user_id: str, agreement_type: AgreementType) -> bool:
        """Check if user needs to re-accept agreement due to version update"""
        
        current_version = self.agreement_versions.get(agreement_type)
        if not current_version:
            return False
        
        agreement = self.check_agreement_status(user_id, agreement_type)
        if not agreement:
            return True
        
        return agreement.agreement_version != current_version
    
    def get_pending_agreements(self, user_id: str) -> List[AgreementType]:
        """Get agreements that user needs to accept"""
        
        pending = []
        
        for agreement_type in self.required_agreements:
            if not self.is_agreement_valid(user_id, agreement_type):
                pending.append(agreement_type)
        
        return pending
    
    def get_expiring_agreements(self, user_id: str, days_ahead: int = 30) -> List[Dict]:
        """Get agreements that will expire soon"""
        
        expiring = []
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        for agreement_type in self.required_agreements:
            agreement = self.check_agreement_status(user_id, agreement_type)
            if (agreement and agreement.expires_at and 
                agreement.expires_at <= cutoff_date):
                
                days_until_expiry = (agreement.expires_at - datetime.utcnow()).days
                
                expiring.append({
                    "agreement_type": agreement_type.value,
                    "agreement_version": agreement.agreement_version,
                    "expires_at": agreement.expires_at.isoformat(),
                    "days_until_expiry": days_until_expiry
                })
        
        return expiring
    
    def cleanup_expired_agreements(self):
        """Mark expired agreements as expired"""
        
        expired_count = 0
        
        for user_id, agreements in self.user_agreements.items():
            for agreement in agreements:
                if (agreement.status == AgreementStatus.ACCEPTED and
                    agreement.expires_at and 
                    agreement.expires_at < datetime.utcnow()):
                    
                    agreement.status = AgreementStatus.EXPIRED
                    expired_count += 1
            
            # Update compliance status for user
            self._update_compliance_status(user_id)
        
        if expired_count > 0:
            self.logger.info(f"Marked {expired_count} agreements as expired")
    
    def get_compliance_stats(self) -> Dict:
        """Get compliance statistics across all users"""
        
        total_users = len(self.user_agreements)
        compliant_users = 0
        non_compliant_users = 0
        
        agreement_stats = {}
        for agreement_type in AgreementType:
            agreement_stats[agreement_type.value] = {
                "total_users": 0,
                "compliant_users": 0,
                "non_compliant_users": 0
            }
        
        for user_id in self.user_agreements:
            compliance_status = self.get_compliance_status(user_id)
            
            if compliance_status.is_compliant:
                compliant_users += 1
            else:
                non_compliant_users += 1
            
            # Count by agreement type
            for agreement_type in self.required_agreements:
                agreement_stats[agreement_type.value]["total_users"] += 1
                
                if agreement_type not in compliance_status.missing_agreements:
                    agreement_stats[agreement_type.value]["compliant_users"] += 1
                else:
                    agreement_stats[agreement_type.value]["non_compliant_users"] += 1
        
        return {
            "total_users": total_users,
            "compliant_users": compliant_users,
            "non_compliant_users": non_compliant_users,
            "compliance_rate": (compliant_users / total_users * 100) if total_users > 0 else 0,
            "agreement_stats": agreement_stats
        }


# Global agreement manager instance
agreement_manager = UserAgreementManager() 