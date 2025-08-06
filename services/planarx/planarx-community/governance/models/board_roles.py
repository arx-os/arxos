"""
Governance Board Role Schema
Defines roles, permissions, and constraints for the Planarx governance board
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


class RoleType(Enum):
    """Governance board role types"""

    CHAIR = "chair"
    VICE_CHAIR = "vice_chair"
    TREASURER = "treasurer"
    SECRETARY = "secretary"
    TECHNICAL_REVIEWER = "technical_reviewer"
    FINANCIAL_REVIEWER = "financial_reviewer"
    COMMUNITY_REPRESENTATIVE = "community_representative"
    LEGAL_ADVISOR = "legal_advisor"
    SUSTAINABILITY_EXPERT = "sustainability_expert"
    BOARD_MEMBER = "board_member"


class PermissionType(Enum):
    """Permission types for governance actions"""

    # Proposal Management
    CREATE_PROPOSAL = "create_proposal"
    EDIT_PROPOSAL = "edit_proposal"
    DELETE_PROPOSAL = "delete_proposal"

    # Voting
    VOTE_ON_PROPOSAL = "vote_on_proposal"
    VETO_PROPOSAL = "veto_proposal"
    OVERRIDE_VOTE = "override_vote"

    # Fund Management
    APPROVE_FUND_RELEASE = "approve_fund_release"
    REJECT_FUND_RELEASE = "reject_fund_release"
    OVERRIDE_FUND_RELEASE = "override_fund_release"
    VIEW_FINANCIAL_DATA = "view_financial_data"

    # Milestone Management
    APPROVE_MILESTONE = "approve_milestone"
    REJECT_MILESTONE = "reject_milestone"
    OVERRIDE_MILESTONE = "override_milestone"

    # User Management
    ASSIGN_BOARD_ROLES = "assign_board_roles"
    REMOVE_BOARD_ROLES = "remove_board_roles"
    SUSPEND_BOARD_MEMBER = "suspend_board_member"

    # Governance
    CALL_EMERGENCY_MEETING = "call_emergency_meeting"
    AMEND_BYLAWS = "amend_bylaws"
    OVERRIDE_QUORUM = "override_quorum"

    # Reporting
    VIEW_AUDIT_LOGS = "view_audit_logs"
    GENERATE_REPORTS = "generate_reports"
    EXPORT_DATA = "export_data"


class VoteType(Enum):
    """Vote types for proposals"""

    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    VETO = "veto"


@dataclass
class RolePermission:
    """Permission configuration for a role"""

    role_type: RoleType
    permissions: Set[PermissionType]
    weight: int  # Voting weight (1-10)
    can_override: bool
    can_veto: bool
    max_terms: int
    term_duration_days: int
    required_experience_years: int
    required_skills: List[str]
    description: str


@dataclass
class BoardMember:
    """Governance board member"""

    id: str
    user_id: str
    role_type: RoleType
    display_name: str
    email: str
    appointed_date: datetime
    term_end_date: datetime
    is_active: bool
    voting_weight: int
    permissions: Set[PermissionType]
    participation_score: float
    decisions_made: int
    decisions_correct: int
    reputation_score: float
    skills: List[str]
    bio: str
    contact_info: Dict

    def __post_init__(self):
        if self.participation_score is None:
            self.participation_score = 0.0
        if self.decisions_made is None:
            self.decisions_made = 0
        if self.decisions_correct is None:
            self.decisions_correct = 0
        if self.reputation_score is None:
            self.reputation_score = 0.0
        if self.skills is None:
            self.skills = []
        if self.contact_info is None:
            self.contact_info = {}


@dataclass
class Proposal:
    """Governance proposal"""

    id: str
    title: str
    description: str
    proposal_type: str
    created_by: str
    created_date: datetime
    deadline: datetime
    status: str
    votes_required: int
    votes_approve: int
    votes_reject: int
    votes_abstain: int
    total_weight: int
    approved_weight: int
    rejected_weight: int
    metadata: Dict
    attachments: List[str]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.attachments is None:
            self.attachments = []


@dataclass
class Vote:
    """Individual vote on a proposal"""

    id: str
    proposal_id: str
    voter_id: str
    vote_type: VoteType
    weight: int
    timestamp: datetime
    reasoning: str
    is_override: bool


class GovernanceBoard:
    """Governance board management system"""

    def __init__(self):
        self.members: Dict[str, BoardMember] = {}
        self.proposals: Dict[str, Proposal] = {}
        self.votes: Dict[str, List[Vote]] = {}
        self.role_permissions: Dict[RoleType, RolePermission] = {}
        self.quorum_threshold: float = 0.6
        self.approval_threshold: float = 0.7
        self.logger = logging.getLogger(__name__)

        # Initialize role permissions
        self._initialize_role_permissions()

    def _initialize_role_permissions(self):
        """Initialize default role permissions"""

        # Chair - Full administrative powers
        self.role_permissions[RoleType.CHAIR] = RolePermission(
            role_type=RoleType.CHAIR,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.EDIT_PROPOSAL,
                PermissionType.DELETE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.VETO_PROPOSAL,
                PermissionType.OVERRIDE_VOTE,
                PermissionType.APPROVE_FUND_RELEASE,
                PermissionType.REJECT_FUND_RELEASE,
                PermissionType.OVERRIDE_FUND_RELEASE,
                PermissionType.VIEW_FINANCIAL_DATA,
                PermissionType.APPROVE_MILESTONE,
                PermissionType.REJECT_MILESTONE,
                PermissionType.OVERRIDE_MILESTONE,
                PermissionType.ASSIGN_BOARD_ROLES,
                PermissionType.REMOVE_BOARD_ROLES,
                PermissionType.SUSPEND_BOARD_MEMBER,
                PermissionType.CALL_EMERGENCY_MEETING,
                PermissionType.AMEND_BYLAWS,
                PermissionType.OVERRIDE_QUORUM,
                PermissionType.VIEW_AUDIT_LOGS,
                PermissionType.GENERATE_REPORTS,
                PermissionType.EXPORT_DATA,
            },
            weight=10,
            can_override=True,
            can_veto=True,
            max_terms=3,
            term_duration_days=365,
            required_experience_years=10,
            required_skills=["leadership", "governance", "strategic_planning"],
            description="Board chair with full administrative powers",
        )

        # Vice Chair - Deputy powers
        self.role_permissions[RoleType.VICE_CHAIR] = RolePermission(
            role_type=RoleType.VICE_CHAIR,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.EDIT_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.VETO_PROPOSAL,
                PermissionType.APPROVE_FUND_RELEASE,
                PermissionType.REJECT_FUND_RELEASE,
                PermissionType.VIEW_FINANCIAL_DATA,
                PermissionType.APPROVE_MILESTONE,
                PermissionType.REJECT_MILESTONE,
                PermissionType.ASSIGN_BOARD_ROLES,
                PermissionType.CALL_EMERGENCY_MEETING,
                PermissionType.VIEW_AUDIT_LOGS,
                PermissionType.GENERATE_REPORTS,
            },
            weight=8,
            can_override=True,
            can_veto=True,
            max_terms=3,
            term_duration_days=365,
            required_experience_years=8,
            required_skills=["leadership", "governance", "project_management"],
            description="Deputy chair with most administrative powers",
        )

        # Treasurer - Financial oversight
        self.role_permissions[RoleType.TREASURER] = RolePermission(
            role_type=RoleType.TREASURER,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.APPROVE_FUND_RELEASE,
                PermissionType.REJECT_FUND_RELEASE,
                PermissionType.OVERRIDE_FUND_RELEASE,
                PermissionType.VIEW_FINANCIAL_DATA,
                PermissionType.GENERATE_REPORTS,
                PermissionType.EXPORT_DATA,
            },
            weight=7,
            can_override=True,
            can_veto=False,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=5,
            required_skills=["finance", "accounting", "budgeting"],
            description="Financial oversight and fund management",
        )

        # Technical Reviewer - Technical expertise
        self.role_permissions[RoleType.TECHNICAL_REVIEWER] = RolePermission(
            role_type=RoleType.TECHNICAL_REVIEWER,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.APPROVE_MILESTONE,
                PermissionType.REJECT_MILESTONE,
                PermissionType.VIEW_AUDIT_LOGS,
            },
            weight=6,
            can_override=False,
            can_veto=False,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=5,
            required_skills=["architecture", "engineering", "construction"],
            description="Technical expertise for project reviews",
        )

        # Financial Reviewer - Financial expertise
        self.role_permissions[RoleType.FINANCIAL_REVIEWER] = RolePermission(
            role_type=RoleType.FINANCIAL_REVIEWER,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.APPROVE_FUND_RELEASE,
                PermissionType.REJECT_FUND_RELEASE,
                PermissionType.VIEW_FINANCIAL_DATA,
                PermissionType.GENERATE_REPORTS,
            },
            weight=6,
            can_override=False,
            can_veto=False,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=5,
            required_skills=["finance", "investment", "risk_management"],
            description="Financial expertise for funding decisions",
        )

        # Community Representative - Community voice
        self.role_permissions[RoleType.COMMUNITY_REPRESENTATIVE] = RolePermission(
            role_type=RoleType.COMMUNITY_REPRESENTATIVE,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.APPROVE_MILESTONE,
                PermissionType.REJECT_MILESTONE,
            },
            weight=5,
            can_override=False,
            can_veto=False,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=3,
            required_skills=["community_engagement", "communication", "advocacy"],
            description="Community voice and representation",
        )

        # Legal Advisor - Legal expertise
        self.role_permissions[RoleType.LEGAL_ADVISOR] = RolePermission(
            role_type=RoleType.LEGAL_ADVISOR,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.VETO_PROPOSAL,
                PermissionType.VIEW_AUDIT_LOGS,
                PermissionType.AMEND_BYLAWS,
            },
            weight=7,
            can_override=False,
            can_veto=True,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=7,
            required_skills=["legal", "compliance", "regulatory"],
            description="Legal expertise and compliance oversight",
        )

        # Sustainability Expert - Environmental expertise
        self.role_permissions[RoleType.SUSTAINABILITY_EXPERT] = RolePermission(
            role_type=RoleType.SUSTAINABILITY_EXPERT,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
                PermissionType.APPROVE_MILESTONE,
                PermissionType.REJECT_MILESTONE,
            },
            weight=5,
            can_override=False,
            can_veto=False,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=4,
            required_skills=[
                "sustainability",
                "environmental_science",
                "green_building",
            ],
            description="Environmental and sustainability expertise",
        )

        # Board Member - General member
        self.role_permissions[RoleType.BOARD_MEMBER] = RolePermission(
            role_type=RoleType.BOARD_MEMBER,
            permissions={
                PermissionType.CREATE_PROPOSAL,
                PermissionType.VOTE_ON_PROPOSAL,
            },
            weight=3,
            can_override=False,
            can_veto=False,
            max_terms=2,
            term_duration_days=365,
            required_experience_years=2,
            required_skills=["governance", "collaboration"],
            description="General board member with basic voting rights",
        )

    def add_board_member(
        self,
        user_id: str,
        role_type: RoleType,
        display_name: str,
        email: str,
        skills: List[str],
        bio: str,
        contact_info: Dict,
    ) -> BoardMember:
        """Add a new board member"""

        # Validate role requirements
        role_perm = self.role_permissions[role_type]

        # Check if user already has a role
        for member in self.members.values():
            if member.user_id == user_id and member.is_active:
                raise ValueError(f"User {user_id} already has an active board role")

        # Create board member
        member_id = str(uuid.uuid4())
        appointed_date = datetime.utcnow()
        term_end_date = appointed_date + timedelta(days=role_perm.term_duration_days)

        member = BoardMember(
            id=member_id,
            user_id=user_id,
            role_type=role_type,
            display_name=display_name,
            email=email,
            appointed_date=appointed_date,
            term_end_date=term_end_date,
            is_active=True,
            voting_weight=role_perm.weight,
            permissions=role_perm.permissions.copy(),
            participation_score=0.0,
            decisions_made=0,
            decisions_correct=0,
            reputation_score=0.0,
            skills=skills,
            bio=bio,
            contact_info=contact_info,
        )

        self.members[member_id] = member
        self.logger.info(
            f"Added board member {display_name} with role {role_type.value}"
        )

        return member

    def remove_board_member(self, member_id: str, reason: str = "") -> bool:
        """Remove a board member"""
        if member_id not in self.members:
            raise ValueError(f"Board member {member_id} not found")

        member = self.members[member_id]
        member.is_active = False

        self.logger.info(f"Removed board member {member.display_name}: {reason}")
        return True

    def suspend_board_member(
        self, member_id: str, duration_days: int, reason: str
    ) -> bool:
        """Suspend a board member temporarily"""
        if member_id not in self.members:
            raise ValueError(f"Board member {member_id} not found")

        member = self.members[member_id]
        member.is_active = False
        member.term_end_date = datetime.utcnow() + timedelta(days=duration_days)

        self.logger.info(
            f"Suspended board member {member.display_name} for {duration_days} days: {reason}"
        )
        return True

    def has_permission(self, user_id: str, permission: PermissionType) -> bool:
        """Check if user has specific permission"""
        for member in self.members.values():
            if (
                member.user_id == user_id
                and member.is_active
                and permission in member.permissions
            ):
                return True
        return False

    def get_member_by_user_id(self, user_id: str) -> Optional[BoardMember]:
        """Get board member by user ID"""
        for member in self.members.values():
            if member.user_id == user_id and member.is_active:
                return member
        return None

    def get_active_members(self) -> List[BoardMember]:
        """Get all active board members"""
        return [member for member in self.members.values() if member.is_active]

    def get_members_by_role(self, role_type: RoleType) -> List[BoardMember]:
        """Get all members with specific role"""
        return [
            member
            for member in self.members.values()
            if member.role_type == role_type and member.is_active
        ]

    def update_participation_score(self, member_id: str, score: float):
        """Update member participation score"""
        if member_id in self.members:
            self.members[member_id].participation_score = max(0.0, min(1.0, score))

    def update_reputation_score(self, member_id: str, score: float):
        """Update member reputation score"""
        if member_id in self.members:
            self.members[member_id].reputation_score = max(0.0, min(10.0, score))

    def get_board_summary(self) -> Dict:
        """Get comprehensive board summary"""
        active_members = self.get_active_members()

        role_counts = {}
        for role_type in RoleType:
            role_counts[role_type.value] = len(self.get_members_by_role(role_type))

        total_weight = sum(member.voting_weight for member in active_members)
        avg_participation = (
            sum(member.participation_score for member in active_members)
            / len(active_members)
            if active_members
            else 0
        )

        return {
            "total_members": len(active_members),
            "role_distribution": role_counts,
            "total_voting_weight": total_weight,
            "average_participation": avg_participation,
            "quorum_threshold": self.quorum_threshold,
            "approval_threshold": self.approval_threshold,
            "members": [
                {
                    "id": member.id,
                    "display_name": member.display_name,
                    "role": member.role_type.value,
                    "voting_weight": member.voting_weight,
                    "participation_score": member.participation_score,
                    "reputation_score": member.reputation_score,
                    "appointed_date": member.appointed_date.isoformat(),
                    "term_end_date": member.term_end_date.isoformat(),
                }
                for member in active_members
            ],
        }


# Global governance board instance
governance_board = GovernanceBoard()
