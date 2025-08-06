"""
Tests for Governance Board System
Comprehensive test suite for governance roles, voting, and user management
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from governance.models.board_roles import (
    governance_board,
    BoardMember,
    RoleType,
    PermissionType,
    EscrowStatus,
    MilestoneStatus,
)

from governance.voting_engine import (
    proposal_engine,
    Proposal,
    Vote,
    VoteType,
    ProposalType,
    ProposalStatus,
    VotingSession,
)

from mod.user_roles import governance_user_manager, UserProfile, UserRole


class TestGovernanceBoard:
    """Test cases for governance board core functionality"""

    def setup_method(self):
        """Reset governance board state before each test"""
        governance_board.members.clear()
        governance_board.pending_approvals.clear()
        proposal_engine.proposals.clear()
        proposal_engine.voting_sessions.clear()
        governance_user_manager.users.clear()
        governance_user_manager.role_assignments.clear()
        governance_user_manager.participation_logs.clear()

    def test_create_board_member(self):
        """Test creating a new board member"""
        member = governance_board.add_board_member(
            user_id="user-123",
            role_type=RoleType.CHAIR,
            display_name="Sarah Johnson",
            email="sarah@example.com",
            skills=["leadership", "governance", "strategic_planning"],
            bio="Experienced leader with 10+ years in governance",
            contact_info={"phone": "+1-555-0123", "linkedin": "sarah-johnson"},
        )

        assert member.user_id == "user-123"
        assert member.role_type == RoleType.CHAIR
        assert member.display_name == "Sarah Johnson"
        assert member.is_active is True
        assert member.voting_weight == 10
        assert len(member.permissions) > 0
        assert "leadership" in member.skills

    def test_role_permissions(self):
        """Test role-specific permissions"""
        # Test chair permissions
        chair_permissions = governance_board.role_permissions[
            RoleType.CHAIR
        ].permissions
        assert PermissionType.CREATE_PROPOSAL in chair_permissions
        assert PermissionType.VETO_PROPOSAL in chair_permissions
        assert PermissionType.OVERRIDE_FUND_RELEASE in chair_permissions

        # Test treasurer permissions
        treasurer_permissions = governance_board.role_permissions[
            RoleType.TREASURER
        ].permissions
        assert PermissionType.APPROVE_FUND_RELEASE in treasurer_permissions
        assert PermissionType.VIEW_FINANCIAL_DATA in treasurer_permissions
        assert PermissionType.VETO_PROPOSAL not in treasurer_permissions

        # Test board member permissions
        member_permissions = governance_board.role_permissions[
            RoleType.BOARD_MEMBER
        ].permissions
        assert PermissionType.CREATE_PROPOSAL in member_permissions
        assert PermissionType.VOTE_ON_PROPOSAL in member_permissions
        assert PermissionType.VETO_PROPOSAL not in member_permissions

    def test_has_permission(self):
        """Test permission checking"""
        # Add board member
        member = governance_board.add_board_member(
            user_id="user-123",
            role_type=RoleType.CHAIR,
            display_name="Sarah Johnson",
            email="sarah@example.com",
            skills=["leadership"],
            bio="Test bio",
            contact_info={},
        )

        # Test permissions
        assert governance_board.has_permission(
            "user-123", PermissionType.CREATE_PROPOSAL
        )
        assert governance_board.has_permission("user-123", PermissionType.VETO_PROPOSAL)
        assert governance_board.has_permission(
            "user-123", PermissionType.OVERRIDE_FUND_RELEASE
        )

        # Test non-member
        assert not governance_board.has_permission(
            "user-456", PermissionType.CREATE_PROPOSAL
        )

    def test_remove_board_member(self):
        """Test removing a board member"""
        member = governance_board.add_board_member(
            user_id="user-123",
            role_type=RoleType.CHAIR,
            display_name="Sarah Johnson",
            email="sarah@example.com",
            skills=["leadership"],
            bio="Test bio",
            contact_info={},
        )

        success = governance_board.remove_board_member(member.id, "Term expired")

        assert success is True
        assert not member.is_active
        assert member.id in governance_board.members

    def test_suspend_board_member(self):
        """Test suspending a board member"""
        member = governance_board.add_board_member(
            user_id="user-123",
            role_type=RoleType.CHAIR,
            display_name="Sarah Johnson",
            email="sarah@example.com",
            skills=["leadership"],
            bio="Test bio",
            contact_info={},
        )

        success = governance_board.suspend_board_member(
            member.id, duration_days=30, reason="Violation of code of conduct"
        )

        assert success is True
        assert not member.is_active
        assert member.term_end_date > datetime.utcnow()

    def test_get_board_summary(self):
        """Test getting board summary"""
        # Add multiple members
        governance_board.add_board_member(
            user_id="user-1",
            role_type=RoleType.CHAIR,
            display_name="Sarah Johnson",
            email="sarah@example.com",
            skills=["leadership"],
            bio="Test bio",
            contact_info={},
        )

        governance_board.add_board_member(
            user_id="user-2",
            role_type=RoleType.TREASURER,
            display_name="Michael Chen",
            email="michael@example.com",
            skills=["finance"],
            bio="Test bio",
            contact_info={},
        )

        summary = governance_board.get_board_summary()

        assert summary["total_members"] == 2
        assert summary["role_distribution"]["chair"] == 1
        assert summary["role_distribution"]["treasurer"] == 1
        assert summary["total_voting_weight"] == 17  # 10 + 7
        assert summary["active_board_members"] == 2


class TestVotingEngine:
    """Test cases for voting and proposal engine"""

    def setup_method(self):
        """Reset voting engine state before each test"""
        proposal_engine.proposals.clear()
        proposal_engine.voting_sessions.clear()

        # Add board members for testing
        governance_board.add_board_member(
            user_id="voter-1",
            role_type=RoleType.CHAIR,
            display_name="Sarah Johnson",
            email="sarah@example.com",
            skills=["leadership"],
            bio="Test bio",
            contact_info={},
        )

        governance_board.add_board_member(
            user_id="voter-2",
            role_type=RoleType.TREASURER,
            display_name="Michael Chen",
            email="michael@example.com",
            skills=["finance"],
            bio="Test bio",
            contact_info={},
        )

    def test_create_proposal(self):
        """Test creating a new proposal"""
        proposal = proposal_engine.create_proposal(
            title="Approve Project Funding",
            description="Approve funding for sustainable office complex",
            proposal_type=ProposalType.FUND_RELEASE,
            created_by="voter-1",
            deadline_days=7,
            metadata={"project_id": "proj-123", "amount": 5000},
        )

        assert proposal.title == "Approve Project Funding"
        assert proposal.proposal_type == "fund_release"
        assert proposal.created_by == "voter-1"
        assert proposal.status == "submitted"
        assert proposal.votes_required > 0

        # Check voting session created
        assert proposal.id in proposal_engine.voting_sessions
        voting_session = proposal_engine.voting_sessions[proposal.id]
        assert voting_session.is_active is True

    def test_submit_vote(self):
        """Test submitting a vote on a proposal"""
        # Create proposal
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Submit vote
        success = proposal_engine.submit_vote(
            proposal_id=proposal.id,
            voter_id="voter-1",
            vote_type=VoteType.APPROVE,
            reasoning="This proposal aligns with our goals",
        )

        assert success is True

        # Check vote recorded
        voting_session = proposal_engine.get_voting_session(proposal.id)
        assert "voter-1" in voting_session.votes
        assert voting_session.votes["voter-1"].vote_type == VoteType.APPROVE
        assert proposal.votes_approve == 1

    def test_vote_with_veto(self):
        """Test voting with veto power"""
        # Create proposal
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Submit veto vote
        success = proposal_engine.submit_vote(
            proposal_id=proposal.id,
            voter_id="voter-1",
            vote_type=VoteType.VETO,
            reasoning="This proposal violates our bylaws",
        )

        assert success is True

        # Check proposal vetoed
        voting_session = proposal_engine.get_voting_session(proposal.id)
        assert voting_session.final_result == ProposalStatus.VETOED
        assert proposal.status == "vetoed"

    def test_quorum_reached(self):
        """Test quorum calculation"""
        # Add more board members
        governance_board.add_board_member(
            user_id="voter-3",
            role_type=RoleType.BOARD_MEMBER,
            display_name="John Doe",
            email="john@example.com",
            skills=["governance"],
            bio="Test bio",
            contact_info={},
        )

        # Create proposal
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Submit votes to reach quorum
        proposal_engine.submit_vote(proposal.id, "voter-1", VoteType.APPROVE)
        proposal_engine.submit_vote(proposal.id, "voter-2", VoteType.APPROVE)

        voting_session = proposal_engine.get_voting_session(proposal.id)
        assert voting_session.quorum_reached is True

    def test_proposal_approval(self):
        """Test proposal approval workflow"""
        # Create proposal
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Submit approval votes
        proposal_engine.submit_vote(proposal.id, "voter-1", VoteType.APPROVE)
        proposal_engine.submit_vote(proposal.id, "voter-2", VoteType.APPROVE)

        voting_session = proposal_engine.get_voting_session(proposal.id)
        assert voting_session.final_result == ProposalStatus.APPROVED
        assert proposal.status == "approved"

    def test_proposal_rejection(self):
        """Test proposal rejection workflow"""
        # Create proposal
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Submit rejection votes
        proposal_engine.submit_vote(proposal.id, "voter-1", VoteType.REJECT)
        proposal_engine.submit_vote(proposal.id, "voter-2", VoteType.REJECT)

        voting_session = proposal_engine.get_voting_session(proposal.id)
        assert voting_session.final_result == ProposalStatus.REJECTED
        assert proposal.status == "rejected"

    def test_get_proposal_summary(self):
        """Test getting proposal summary"""
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        proposal_engine.submit_vote(proposal.id, "voter-1", VoteType.APPROVE)

        summary = proposal_engine.get_proposal_summary(proposal.id)

        assert summary["id"] == proposal.id
        assert summary["title"] == "Test Proposal"
        assert summary["status"] == "submitted"
        assert summary["votes_approve"] == 1
        assert "voting_summary" in summary

    def test_unauthorized_vote(self):
        """Test voting by unauthorized user"""
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Try to vote with unauthorized user
        with pytest.raises(
            ValueError, match="User unauthorized-user is not an active board member"
        ):
            proposal_engine.submit_vote(
                proposal_id=proposal.id,
                voter_id="unauthorized-user",
                vote_type=VoteType.APPROVE,
            )

    def test_duplicate_vote(self):
        """Test preventing duplicate votes"""
        proposal = proposal_engine.create_proposal(
            title="Test Proposal",
            description="Test proposal description",
            proposal_type=ProposalType.POLICY_CHANGE,
            created_by="voter-1",
        )

        # Submit first vote
        proposal_engine.submit_vote(proposal.id, "voter-1", VoteType.APPROVE)

        # Try to submit duplicate vote
        with pytest.raises(ValueError, match="Voter voter-1 has already voted"):
            proposal_engine.submit_vote(proposal.id, "voter-1", VoteType.REJECT)


class TestGovernanceUserManager:
    """Test cases for governance user management"""

    def setup_method(self):
        """Reset user manager state before each test"""
        governance_user_manager.users.clear()
        governance_user_manager.role_assignments.clear()
        governance_user_manager.participation_logs.clear()
        governance_board.members.clear()

    def test_create_user_profile(self):
        """Test creating a user profile"""
        user = governance_user_manager.create_user_profile(
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            skills=["governance", "leadership"],
            experience_years=5,
            bio="Test bio",
            contact_info={"phone": "+1-555-0123"},
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.roles == {UserRole.USER.value}
        assert user.is_active is True
        assert "governance" in user.skills
        assert user.experience_years == 5

    def test_assign_governance_role(self):
        """Test assigning a governance role to a user"""
        # Create user
        user = governance_user_manager.create_user_profile(
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            skills=["leadership", "governance", "strategic_planning"],
            experience_years=10,
            bio="Test bio",
            contact_info={},
        )

        # Add board member for assignment permission
        governance_board.add_board_member(
            user_id="admin",
            role_type=RoleType.CHAIR,
            display_name="Admin User",
            email="admin@example.com",
            skills=["leadership"],
            bio="Admin bio",
            contact_info={},
        )

        # Assign role
        board_member = governance_user_manager.assign_governance_role(
            user_id=user.id,
            role_type=RoleType.CHAIR,
            assigned_by="admin",
            reason="Experienced leader",
        )

        assert board_member is not None
        assert board_member.user_id == user.id
        assert board_member.role_type == RoleType.CHAIR
        assert user.board_member_id == board_member.id
        assert RoleType.CHAIR.value in user.governance_roles
        assert len(user.governance_permissions) > 0

    def test_assign_role_insufficient_experience(self):
        """Test role assignment with insufficient experience"""
        user = governance_user_manager.create_user_profile(
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            skills=["leadership"],
            experience_years=2,  # Less than required 10 years for chair
            bio="Test bio",
            contact_info={},
        )

        # Add admin
        governance_board.add_board_member(
            user_id="admin",
            role_type=RoleType.CHAIR,
            display_name="Admin User",
            email="admin@example.com",
            skills=["leadership"],
            bio="Admin bio",
            contact_info={},
        )

        # Try to assign chair role
        with pytest.raises(
            ValueError, match="User does not meet experience requirement"
        ):
            governance_user_manager.assign_governance_role(
                user_id=user.id, role_type=RoleType.CHAIR, assigned_by="admin"
            )

    def test_assign_role_insufficient_skills(self):
        """Test role assignment with insufficient skills"""
        user = governance_user_manager.create_user_profile(
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            skills=["leadership"],  # Missing required skills
            experience_years=10,
            bio="Test bio",
            contact_info={},
        )

        # Add admin
        governance_board.add_board_member(
            user_id="admin",
            role_type=RoleType.CHAIR,
            display_name="Admin User",
            email="admin@example.com",
            skills=["leadership"],
            bio="Admin bio",
            contact_info={},
        )

        # Try to assign chair role
        with pytest.raises(ValueError, match="User missing required skills"):
            governance_user_manager.assign_governance_role(
                user_id=user.id, role_type=RoleType.CHAIR, assigned_by="admin"
            )

    def test_remove_governance_role(self):
        """Test removing a governance role"""
        # Create user and assign role
        user = governance_user_manager.create_user_profile(
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            skills=["leadership", "governance", "strategic_planning"],
            experience_years=10,
            bio="Test bio",
            contact_info={},
        )

        # Add admin
        governance_board.add_board_member(
            user_id="admin",
            role_type=RoleType.CHAIR,
            display_name="Admin User",
            email="admin@example.com",
            skills=["leadership"],
            bio="Admin bio",
            contact_info={},
        )

        # Assign role
        governance_user_manager.assign_governance_role(
            user_id=user.id, role_type=RoleType.CHAIR, assigned_by="admin"
        )

        # Remove role
        success = governance_user_manager.remove_governance_role(
            user_id=user.id, removed_by="admin", reason="Term expired"
        )

        assert success is True
        assert user.board_member_id is None
        assert len(user.governance_roles) == 0
        assert len(user.governance_permissions) == 0

    def test_get_governance_candidates(self):
        """Test getting eligible candidates for governance roles"""
        # Create users with different skill sets
        user1 = governance_user_manager.create_user_profile(
            username="user1",
            email="user1@example.com",
            display_name="User 1",
            skills=["leadership", "governance", "strategic_planning"],
            experience_years=12,
            bio="Test bio",
            contact_info={},
        )

        user2 = governance_user_manager.create_user_profile(
            username="user2",
            email="user2@example.com",
            display_name="User 2",
            skills=["finance", "accounting", "budgeting"],
            experience_years=8,
            bio="Test bio",
            contact_info={},
        )

        user3 = governance_user_manager.create_user_profile(
            username="user3",
            email="user3@example.com",
            display_name="User 3",
            skills=["governance"],
            experience_years=3,  # Insufficient experience
            bio="Test bio",
            contact_info={},
        )

        # Get candidates for chair role
        candidates = governance_user_manager.get_governance_candidates(RoleType.CHAIR)

        assert len(candidates) == 1
        assert candidates[0]["user"].id == user1.id
        assert candidates[0]["eligibility_score"] > 0.8

        # Get candidates for treasurer role
        candidates = governance_user_manager.get_governance_candidates(
            RoleType.TREASURER
        )

        assert len(candidates) == 1
        assert candidates[0]["user"].id == user2.id

    def test_get_governance_summary(self):
        """Test getting governance user summary"""
        # Create users
        governance_user_manager.create_user_profile(
            username="user1",
            email="user1@example.com",
            display_name="User 1",
            skills=["leadership"],
            experience_years=10,
            bio="Test bio",
            contact_info={},
        )

        governance_user_manager.create_user_profile(
            username="user2",
            email="user2@example.com",
            display_name="User 2",
            skills=["finance"],
            experience_years=8,
            bio="Test bio",
            contact_info={},
        )

        summary = governance_user_manager.get_governance_summary()

        assert summary["total_users"] == 2
        assert summary["governance_users"] == 0  # No roles assigned yet
        assert summary["active_board_members"] == 0
        assert summary["suspended_board_members"] == 0

    def test_update_scores(self):
        """Test updating user participation and reputation scores"""
        user = governance_user_manager.create_user_profile(
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            skills=["leadership"],
            experience_years=5,
            bio="Test bio",
            contact_info={},
        )

        # Update scores
        governance_user_manager.update_participation_score(user.id, 0.85)
        governance_user_manager.update_reputation_score(user.id, 8.5)

        assert user.participation_score == 0.85
        assert user.reputation_score == 8.5

    def test_search_users(self):
        """Test user search functionality"""
        governance_user_manager.create_user_profile(
            username="sarah_johnson",
            email="sarah@example.com",
            display_name="Sarah Johnson",
            skills=["leadership"],
            experience_years=10,
            bio="Test bio",
            contact_info={},
        )

        governance_user_manager.create_user_profile(
            username="michael_chen",
            email="michael@example.com",
            display_name="Michael Chen",
            skills=["finance"],
            experience_years=8,
            bio="Test bio",
            contact_info={},
        )

        # Search by name
        results = governance_user_manager.search_users("Sarah")
        assert len(results) == 1
        assert results[0].username == "sarah_johnson"

        # Search by username
        results = governance_user_manager.search_users("michael")
        assert len(results) == 1
        assert results[0].username == "michael_chen"

        # Search with role filter
        results = governance_user_manager.search_users("", role_filter="user")
        assert len(results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
