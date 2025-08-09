"""
Voting and Proposal Engine
Manages governance proposals, voting sessions, and automated decision triggers
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import json
import logging

from services.models.board_roles import services.models.board_roles
    governance_board,
    BoardMember,
    Proposal,
    Vote,
    VoteType,
    PermissionType
)

logger = logging.getLogger(__name__)


class ProposalType(Enum):
    """Types of governance proposals"""
    FUND_RELEASE = "fund_release"
    MILESTONE_APPROVAL = "milestone_approval"
    PROJECT_APPROVAL = "project_approval"
    POLICY_CHANGE = "policy_change"
    BOARD_APPOINTMENT = "board_appointment"
    EMERGENCY_DECISION = "emergency_decision"
    BYLAW_AMENDMENT = "bylaw_amendment"
    BUDGET_APPROVAL = "budget_approval"


class ProposalStatus(Enum):
    """Proposal status states"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    VETOED = "vetoed"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class VotingSession:
    """Manages a voting session for a proposal"""

    def __init__(self, proposal: Proposal):
        self.proposal = proposal
        self.votes: Dict[str, Vote] = {}
        self.start_time = datetime.utcnow()
        self.end_time = proposal.deadline
        self.is_active = True
        self.quorum_reached = False
        self.decision_made = False
        self.final_result = None

    def add_vote(self, voter_id: str, vote_type: VoteType, weight: int, reasoning: str = "", is_override: bool = False) -> bool:
        """Add a vote to the session"""

        if not self.is_active:
            raise ValueError("Voting session is not active")

        if voter_id in self.votes:
            raise ValueError(f"Voter {voter_id} has already voted")

        # Check if voter is eligible
        member = governance_board.get_member_by_user_id(voter_id)
        if not member or not member.is_active:
            raise ValueError(f"User {voter_id} is not an active board member")

        # Check if voter has permission to vote
        if not governance_board.has_permission(voter_id, PermissionType.VOTE_ON_PROPOSAL):
            raise ValueError(f"User {voter_id} does not have voting permission")

        # Create vote
        vote = Vote(
            id=str(uuid.uuid4(),
            proposal_id=self.proposal.id,
            voter_id=voter_id,
            vote_type=vote_type,
            weight=weight,
            timestamp=datetime.utcnow(),
            reasoning=reasoning,
            is_override=is_override
        )

        self.votes[voter_id] = vote

        # Update proposal vote counts
        if vote_type == VoteType.APPROVE:
            self.proposal.votes_approve += 1
            self.proposal.approved_weight += weight
        elif vote_type == VoteType.REJECT:
            self.proposal.votes_reject += 1
            self.proposal.rejected_weight += weight
        elif vote_type == VoteType.ABSTAIN:
            self.proposal.votes_abstain += 1

        self.proposal.total_weight += weight

        logger.info(f"Vote added: {voter_id} voted {vote_type.value} on proposal {self.proposal.id}")

        # Check if quorum reached
        self._check_quorum()

        # Check if decision can be made
        self._check_decision()

        return True

    def _check_quorum(self):
        """Check if quorum has been reached"""
        active_members = governance_board.get_active_members()
        total_possible_weight = sum(member.voting_weight for member in active_members)
        current_weight = sum(vote.weight for vote in self.votes.values()

        quorum_threshold = governance_board.quorum_threshold
        if current_weight / total_possible_weight >= quorum_threshold:
            self.quorum_reached = True
            logger.info(f"Quorum reached for proposal {self.proposal.id}")

    def _check_decision(self):
        """Check if a decision can be made"""
        if not self.quorum_reached:
            return

        total_votes = self.proposal.votes_approve + self.proposal.votes_reject
        if total_votes == 0:
            return

        approval_threshold = governance_board.approval_threshold

        # Check for veto
        veto_votes = [vote for vote in self.votes.values() if vote.vote_type == VoteType.VETO]
        if veto_votes:
            self._make_decision(ProposalStatus.VETOED, "Proposal vetoed")
            return

        # Check approval threshold
        approval_ratio = self.proposal.approved_weight / self.proposal.total_weight
        if approval_ratio >= approval_threshold:
            self._make_decision(ProposalStatus.APPROVED, "Proposal approved by majority")
        elif approval_ratio < (1 - approval_threshold):
            self._make_decision(ProposalStatus.REJECTED, "Proposal rejected by majority")

    def _make_decision(self, status: ProposalStatus, reason: str):
        """Make final decision on proposal"""
        self.proposal.status = status.value
        self.decision_made = True
        self.final_result = status
        self.is_active = False

        logger.info(f"Proposal {self.proposal.id} decision: {status.value} - {reason}")

    def get_voting_summary(self) -> Dict:
        """Get comprehensive voting summary"""
        return {
            "proposal_id": self.proposal.id,
            "title": self.proposal.title,
            "status": self.proposal.status,
            "total_votes": len(self.votes),
            "votes_approve": self.proposal.votes_approve,
            "votes_reject": self.proposal.votes_reject,
            "votes_abstain": self.proposal.votes_abstain,
            "total_weight": self.proposal.total_weight,
            "approved_weight": self.proposal.approved_weight,
            "rejected_weight": self.proposal.rejected_weight,
            "quorum_reached": self.quorum_reached,
            "decision_made": self.decision_made,
            "final_result": self.final_result.value if self.final_result else None,
            "time_remaining": (self.end_time - datetime.utcnow().total_seconds() if self.is_active else 0,
            "votes": [
                {
                    "voter_id": vote.voter_id,
                    "vote_type": vote.vote_type.value,
                    "weight": vote.weight,
                    "timestamp": vote.timestamp.isoformat(),
                    "reasoning": vote.reasoning,
                    "is_override": vote.is_override
                }
                for vote in self.votes.values()
            ]
        }


class ProposalEngine:
    """Manages proposal creation, voting, and decision automation"""

    def __init__(self):
        self.proposals: Dict[str, Proposal] = {}
        self.voting_sessions: Dict[str, VotingSession] = {}
        self.logger = logging.getLogger(__name__)

    def create_proposal(
        self,
        title: str,
        description: str,
        proposal_type: ProposalType,
        created_by: str,
        deadline_days: int = 7,
        votes_required: Optional[int] = None,
        metadata: Optional[Dict] = None,
        attachments: Optional[List[str]] = None
    ) -> Proposal:
        """Create a new governance proposal"""

        # Validate creator permissions
        if not governance_board.has_permission(created_by, PermissionType.CREATE_PROPOSAL):
            raise ValueError(f"User {created_by} does not have permission to create proposals")

        # Create proposal
        proposal_id = str(uuid.uuid4()
        created_date = datetime.utcnow()
        deadline = created_date + timedelta(days=deadline_days)

        # Set default votes required if not specified
        if votes_required is None:
            active_members = governance_board.get_active_members()
            votes_required = max(3, len(active_members) // 2)

        proposal = Proposal(
            id=proposal_id,
            title=title,
            description=description,
            proposal_type=proposal_type.value,
            created_by=created_by,
            created_date=created_date,
            deadline=deadline,
            status=ProposalStatus.SUBMITTED.value,
            votes_required=votes_required,
            votes_approve=0,
            votes_reject=0,
            votes_abstain=0,
            total_weight=0,
            approved_weight=0,
            rejected_weight=0,
            metadata=metadata or {},
            attachments=attachments or []
        )

        self.proposals[proposal_id] = proposal

        # Create voting session
        voting_session = VotingSession(proposal)
        self.voting_sessions[proposal_id] = voting_session

        self.logger.info(f"Created proposal {proposal_id}: {title}")

        return proposal

    def submit_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote_type: VoteType,
        reasoning: str = "",
        is_override: bool = False
    ) -> bool:
        """Submit a vote on a proposal"""

        if proposal_id not in self.voting_sessions:
            raise ValueError(f"Proposal {proposal_id} not found")

        voting_session = self.voting_sessions[proposal_id]

        # Get voter's voting weight'
        member = governance_board.get_member_by_user_id(voter_id)
        if not member:
            raise ValueError(f"User {voter_id} is not a board member")

        weight = member.voting_weight

        # Check for veto permission
        if vote_type == VoteType.VETO:
            if not governance_board.has_permission(voter_id, PermissionType.VETO_PROPOSAL):
                raise ValueError(f"User {voter_id} does not have veto permission")

        # Check for override permission
        if is_override:
            if not governance_board.has_permission(voter_id, PermissionType.OVERRIDE_VOTE):
                raise ValueError(f"User {voter_id} does not have override permission")

        return voting_session.add_vote(voter_id, vote_type, weight, reasoning, is_override)

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get proposal by ID"""
        return self.proposals.get(proposal_id)

    def get_voting_session(self, proposal_id: str) -> Optional[VotingSession]:
        """Get voting session by proposal ID"""
        return self.voting_sessions.get(proposal_id)

    def get_active_proposals(self) -> List[Proposal]:
        """Get all active proposals"""
        return [
            proposal for proposal in self.proposals.values()
            if proposal.status in [ProposalStatus.SUBMITTED.value, ProposalStatus.VOTING.value]
        ]

    def get_proposals_by_type(self, proposal_type: ProposalType) -> List[Proposal]:
        """Get proposals by type"""
        return [
            proposal for proposal in self.proposals.values()
            if proposal.proposal_type == proposal_type.value
        ]

    def get_proposals_by_creator(self, creator_id: str) -> List[Proposal]:
        """Get proposals by creator"""
        return [
            proposal for proposal in self.proposals.values()
            if proposal.created_by == creator_id
        ]

    def update_proposal(
        self,
        proposal_id: str,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        deadline_days: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update a proposal"""

        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal = self.proposals[proposal_id]

        # Check permissions
        if proposal.created_by != user_id and not governance_board.has_permission(user_id, PermissionType.EDIT_PROPOSAL):
            raise ValueError(f"User {user_id} does not have permission to edit this proposal")

        # Update fields
        if title:
            proposal.title = title
        if description:
            proposal.description = description
        if deadline_days:
            proposal.deadline = datetime.utcnow() + timedelta(days=deadline_days)
        if metadata:
            proposal.metadata.update(metadata)

        self.logger.info(f"Updated proposal {proposal_id}")
        return True

    def withdraw_proposal(self, proposal_id: str, user_id: str, reason: str = "") -> bool:
        """Withdraw a proposal"""

        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal = self.proposals[proposal_id]

        # Check permissions
        if proposal.created_by != user_id and not governance_board.has_permission(user_id, PermissionType.DELETE_PROPOSAL):
            raise ValueError(f"User {user_id} does not have permission to withdraw this proposal")

        proposal.status = ProposalStatus.WITHDRAWN.value

        # End voting session
        if proposal_id in self.voting_sessions:
            self.voting_sessions[proposal_id].is_active = False

        self.logger.info(f"Withdrew proposal {proposal_id}: {reason}")
        return True

    def get_proposal_summary(self, proposal_id: str) -> Dict:
        """Get comprehensive proposal summary"""

        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal = self.proposals[proposal_id]
        voting_session = self.voting_sessions.get(proposal_id)

        summary = {
            "id": proposal.id,
            "title": proposal.title,
            "description": proposal.description,
            "proposal_type": proposal.proposal_type,
            "created_by": proposal.created_by,
            "created_date": proposal.created_date.isoformat(),
            "deadline": proposal.deadline.isoformat(),
            "status": proposal.status,
            "votes_required": proposal.votes_required,
            "votes_approve": proposal.votes_approve,
            "votes_reject": proposal.votes_reject,
            "votes_abstain": proposal.votes_abstain,
            "total_weight": proposal.total_weight,
            "approved_weight": proposal.approved_weight,
            "rejected_weight": proposal.rejected_weight,
            "metadata": proposal.metadata,
            "attachments": proposal.attachments
        }

        if voting_session:
            summary["voting_summary"] = voting_session.get_voting_summary()

        return summary

    def get_board_voting_stats(self) -> Dict:
        """Get voting statistics for board members"""

        stats = {}
        active_members = governance_board.get_active_members()

        for member in active_members:
            member_stats = {
                "total_votes": 0,
                "approve_votes": 0,
                "reject_votes": 0,
                "abstain_votes": 0,
                "veto_votes": 0,
                "participation_rate": 0.0
            }

            # Count votes across all proposals
            total_proposals = len(self.proposals)
            for proposal in self.proposals.values():
                voting_session = self.voting_sessions.get(proposal.id)
                if voting_session and member.user_id in voting_session.votes:
                    vote = voting_session.votes[member.user_id]
                    member_stats["total_votes"] += 1

                    if vote.vote_type == VoteType.APPROVE:
                        member_stats["approve_votes"] += 1
                    elif vote.vote_type == VoteType.REJECT:
                        member_stats["reject_votes"] += 1
                    elif vote.vote_type == VoteType.ABSTAIN:
                        member_stats["abstain_votes"] += 1
                    elif vote.vote_type == VoteType.VETO:
                        member_stats["veto_votes"] += 1

            if total_proposals > 0:
                member_stats["participation_rate"] = member_stats["total_votes"] / total_proposals

            stats[member.user_id] = member_stats

        return stats

    def cleanup_expired_proposals(self):
        """Clean up expired proposals and voting sessions"""

        current_time = datetime.utcnow()
        expired_proposals = []

        for proposal_id, proposal in self.proposals.items():
            if (proposal.status in [ProposalStatus.SUBMITTED.value, ProposalStatus.VOTING.value] and
                current_time > proposal.deadline):

                # Mark as expired
                proposal.status = ProposalStatus.EXPIRED.value
                expired_proposals.append(proposal_id)

                # End voting session
                if proposal_id in self.voting_sessions:
                    self.voting_sessions[proposal_id].is_active = False

        if expired_proposals:
            self.logger.info(f"Cleaned up {len(expired_proposals)} expired proposals")

        return expired_proposals


# Global proposal engine instance
proposal_engine = ProposalEngine() )))
