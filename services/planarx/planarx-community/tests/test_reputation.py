"""
Reputation System Tests
Tests for reputation scoring, badges, and grant eligibility
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from ..reputation.scoring_engine import ReputationScoringEngine, ContributionType, ReputationTier
from ..reputation.badges import BadgeSystem, BadgeType, BadgeRarity
from ..funding.grant_eligibility import GrantEligibilityEngine, GrantType, EligibilityStatus
from ..reputation.routes import router
from ..main import app


class TestReputationScoringEngine:
    """Test reputation scoring engine"""
    
    def setup_method(self):
        self.engine = ReputationScoringEngine()
    
    def test_create_contribution_event(self):
        """Test creating contribution events"""
        event = self.engine.record_contribution(
            user_id="test-user",
            contribution_type=ContributionType.DRAFT_SUBMITTED,
            metadata={"draft_id": "draft-123"},
            quality_score=1.0
        )
        
        assert event is not None
        assert event.user_id == "test-user"
        assert event.contribution_type == ContributionType.DRAFT_SUBMITTED
        assert event.points_earned > 0
        assert event.validated == True
    
    def test_reputation_tier_calculation(self):
        """Test reputation tier calculation"""
        # Test newcomer tier
        tier = self.engine._calculate_tier(50)
        assert tier == ReputationTier.NEWCOMER
        
        # Test contributor tier
        tier = self.engine._calculate_tier(150)
        assert tier == ReputationTier.CONTRIBUTOR
        
        # Test expert tier
        tier = self.engine._calculate_tier(1200)
        assert tier == ReputationTier.EXPERT
        
        # Test legend tier
        tier = self.engine._calculate_tier(6000)
        assert tier == ReputationTier.LEGEND
    
    def test_daily_limit_enforcement(self):
        """Test daily limit enforcement"""
        user_id = "test-user"
        contribution_type = ContributionType.COMMENT_ADDED
        
        # Add contributions up to limit
        for i in range(100):  # Daily limit is 100
            event = self.engine.record_contribution(
                user_id=user_id,
                contribution_type=contribution_type,
                metadata={"comment_id": f"comment-{i}"}
            )
            assert event is not None
        
        # Try to exceed limit
        event = self.engine.record_contribution(
            user_id=user_id,
            contribution_type=contribution_type,
            metadata={"comment_id": "comment-101"}
        )
        assert event is None
    
    def test_abuse_detection(self):
        """Test abuse detection system"""
        user_id = "test-user"
        
        # Normal contribution
        event = self.engine.record_contribution(
            user_id=user_id,
            contribution_type=ContributionType.COMMENT_ADDED
        )
        assert event.abuse_score < 0.5
        
        # Simulate rapid-fire contributions
        for i in range(15):  # More than 10 in 5 minutes
            self.engine.record_contribution(
                user_id=user_id,
                contribution_type=ContributionType.COMMENT_ADDED
            )
        
        # Check abuse detection
        abuse = self.engine.abuse_detection.get(user_id)
        assert abuse is not None
        assert abuse.abuse_score > 0.3
    
    def test_user_reputation_creation(self):
        """Test automatic user reputation creation"""
        user_id = "new-user"
        
        # First contribution should create reputation
        event = self.engine.record_contribution(
            user_id=user_id,
            contribution_type=ContributionType.DRAFT_SUBMITTED
        )
        
        reputation = self.engine.get_user_reputation(user_id)
        assert reputation is not None
        assert reputation.user_id == user_id
        assert reputation.total_points > 0
        assert reputation.current_tier == ReputationTier.NEWCOMER
    
    def test_tier_upgrade(self):
        """Test reputation tier upgrades"""
        user_id = "upgrade-user"
        
        # Add enough points to reach contributor tier
        for i in range(10):
            self.engine.record_contribution(
                user_id=user_id,
                contribution_type=ContributionType.DRAFT_SUBMITTED
            )
        
        reputation = self.engine.get_user_reputation(user_id)
        assert reputation.current_tier == ReputationTier.CONTRIBUTOR
        
        # Check history for tier upgrade event
        tier_upgrades = [
            event for event in reputation.reputation_history
            if event.get("event_type") == "tier_upgrade"
        ]
        assert len(tier_upgrades) > 0
    
    def test_leaderboard_generation(self):
        """Test leaderboard generation"""
        # Create multiple users with different points
        users = ["user1", "user2", "user3"]
        
        for i, user_id in enumerate(users):
            for j in range((i + 1) * 5):  # Different point levels
                self.engine.record_contribution(
                    user_id=user_id,
                    contribution_type=ContributionType.COMMENT_ADDED
                )
        
        leaderboard = self.engine.get_leaderboard(limit=10)
        
        assert len(leaderboard) > 0
        # Should be sorted by total_points (highest first)
        assert leaderboard[0]["total_points"] >= leaderboard[-1]["total_points"]
    
    def test_contribution_statistics(self):
        """Test contribution statistics calculation"""
        user_id = "stats-user"
        
        # Add various contributions
        contribution_types = [
            ContributionType.DRAFT_SUBMITTED,
            ContributionType.COMMENT_ADDED,
            ContributionType.THREAD_RESOLVED,
            ContributionType.ANNOTATION_ADDED
        ]
        
        for contribution_type in contribution_types:
            self.engine.record_contribution(
                user_id=user_id,
                contribution_type=contribution_type
            )
        
        stats = self.engine.get_contribution_stats(user_id)
        
        assert stats["user_id"] == user_id
        assert stats["total_points"] > 0
        assert stats["contribution_count"] == 4
        assert "comment_added" in stats["contribution_breakdown"]
    
    def test_abuse_flag_management(self):
        """Test abuse flag management"""
        user_id = "abuse-user"
        
        # Flag user for review
        self.engine.flag_user_for_review(user_id, "Suspicious activity")
        
        abuse = self.engine.abuse_detection.get(user_id)
        assert abuse is not None
        assert abuse.review_required == True
        assert abuse.warning_count == 1
        
        # Clear flag
        self.engine.clear_abuse_flag(user_id, "moderator-123")
        
        abuse = self.engine.abuse_detection.get(user_id)
        assert abuse.review_required == False
        assert abuse.is_flagged == False


class TestBadgeSystem:
    """Test badge system"""
    
    def setup_method(self):
        self.badge_system = BadgeSystem()
    
    def test_badge_creation(self):
        """Test badge creation and storage"""
        badges = self.badge_system.get_all_badges()
        
        assert len(badges) > 0
        
        # Check specific badges exist
        badge_ids = [badge.id for badge in badges]
        assert "contributor" in badge_ids
        assert "expert" in badge_ids
        assert "legend" in badge_ids
    
    def test_badge_awarding(self):
        """Test awarding badges to users"""
        user_id = "test-user"
        badge_id = "contributor"
        
        # Award badge
        user_badge = self.badge_system.award_badge(user_id, badge_id)
        
        assert user_badge is not None
        assert user_badge.user_id == user_id
        assert user_badge.badge_id == badge_id
        assert user_badge.progress == 1.0
        
        # Check user badges
        user_badges = self.badge_system.get_user_badges(user_id)
        assert len(user_badges) == 1
        assert user_badges[0].badge_id == badge_id
    
    def test_duplicate_badge_prevention(self):
        """Test prevention of duplicate badge awards"""
        user_id = "test-user"
        badge_id = "contributor"
        
        # Award badge first time
        user_badge1 = self.badge_system.award_badge(user_id, badge_id)
        assert user_badge1 is not None
        
        # Try to award same badge again
        user_badge2 = self.badge_system.award_badge(user_id, badge_id)
        assert user_badge2 is None
    
    def test_badge_progress_tracking(self):
        """Test badge progress tracking"""
        user_id = "progress-user"
        badge_id = "expert"
        
        # Set progress
        self.badge_system.update_badge_progress(user_id, badge_id, 0.75)
        
        progress = self.badge_system.get_badge_progress(user_id, badge_id)
        assert progress == 0.75
    
    def test_badge_eligibility_checking(self):
        """Test badge eligibility checking"""
        user_id = "eligibility-user"
        
        # Mock user stats
        user_stats = {
            "total_contributions": 1,
            "reputation_tier": "newcomer",
            "drafts_submitted": 1,
            "helpful_comments": 100,
            "threads_resolved": 25
        }
        
        eligible_badges = self.badge_system.check_badge_eligibility(user_id, user_stats)
        
        assert len(eligible_badges) > 0
        
        # Check that contributor badge is eligible
        contributor_badge = next(
            (badge for badge in eligible_badges if badge.id == "contributor"),
            None
        )
        assert contributor_badge is not None
    
    def test_badge_recommendations(self):
        """Test badge recommendations"""
        user_id = "recommendation-user"
        
        # Mock user stats
        user_stats = {
            "total_contributions": 50,
            "reputation_tier": "regular",
            "drafts_submitted": 10,
            "helpful_comments": 50,
            "threads_resolved": 20
        }
        
        recommendations = self.badge_system.get_badge_recommendations(user_id, user_stats)
        
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "badge_id" in rec
            assert "badge_details" in rec
            assert "progress" in rec
            assert "remaining_effort" in rec
    
    def test_badge_summary(self):
        """Test badge summary generation"""
        user_id = "summary-user"
        
        # Award some badges
        self.badge_system.award_badge(user_id, "contributor")
        self.badge_system.award_badge(user_id, "expert")
        
        summary = self.badge_system.get_user_badge_summary(user_id)
        
        assert summary["user_id"] == user_id
        assert summary["total_badges"] == 2
        assert "badges_by_rarity" in summary
        assert "total_badge_points" in summary
        assert len(summary["all_badges"]) == 2
    
    def test_badge_leaderboard(self):
        """Test badge leaderboard generation"""
        # Award badges to multiple users
        users = ["user1", "user2", "user3"]
        
        for i, user_id in enumerate(users):
            self.badge_system.award_badge(user_id, "contributor")
            if i > 0:
                self.badge_system.award_badge(user_id, "expert")
        
        leaderboard = self.badge_system.get_leaderboard_by_badges(limit=10)
        
        assert len(leaderboard) > 0
        # Should be sorted by total_badge_points (highest first)
        assert leaderboard[0]["total_badge_points"] >= leaderboard[-1]["total_badge_points"]


class TestGrantEligibilityEngine:
    """Test grant eligibility engine"""
    
    def setup_method(self):
        self.engine = GrantEligibilityEngine()
    
    def test_eligibility_rules_initialization(self):
        """Test initialization of eligibility rules"""
        rules = self.engine.eligibility_rules
        
        assert len(rules) > 0
        
        # Check specific grant types exist
        assert GrantType.FEATURE_DEVELOPMENT in rules
        assert GrantType.BUG_FIX in rules
        assert GrantType.DOCUMENTATION in rules
    
    def test_user_eligibility_checking(self):
        """Test user eligibility checking"""
        user_id = "test-user"
        grant_type = GrantType.BUG_FIX
        
        # Mock user reputation and badges
        user_reputation = {
            "current_tier": "contributor",
            "total_points": 150,
            "contribution_count": 10
        }
        user_badges = ["bug_hunter"]
        
        eligibility = self.engine.check_user_eligibility(
            user_id=user_id,
            grant_type=grant_type,
            user_reputation=user_reputation,
            user_badges=user_badges
        )
        
        assert eligibility.user_id == user_id
        assert eligibility.grant_type == grant_type
        assert eligibility.status in [EligibilityStatus.ELIGIBLE, EligibilityStatus.PENDING, EligibilityStatus.INELIGIBLE]
        assert eligibility.eligibility_score >= 0.0
        assert eligibility.eligibility_score <= 1.0
    
    def test_tier_eligibility_checking(self):
        """Test tier eligibility checking"""
        # Test valid tier progression
        assert self.engine._check_tier_eligibility("expert", "contributor") == True
        assert self.engine._check_tier_eligibility("master", "expert") == True
        assert self.engine._check_tier_eligibility("legend", "newcomer") == True
        
        # Test invalid tier progression
        assert self.engine._check_tier_eligibility("newcomer", "expert") == False
        assert self.engine._check_tier_eligibility("contributor", "master") == False
    
    def test_priority_level_calculation(self):
        """Test priority level calculation"""
        user_reputation = {
            "current_tier": "expert",
            "total_points": 1200,
            "contribution_count": 50
        }
        
        rules = self.engine.eligibility_rules[GrantType.FEATURE_DEVELOPMENT]
        priority = self.engine._calculate_priority_level(user_reputation, rules)
        
        assert priority > 0
        assert isinstance(priority, int)
    
    def test_funding_limit_calculation(self):
        """Test funding limit calculation"""
        user_reputation = {
            "current_tier": "expert",
            "total_points": 1200,
            "contribution_count": 50
        }
        
        rules = self.engine.eligibility_rules[GrantType.FEATURE_DEVELOPMENT]
        funding_limit = self.engine._calculate_funding_limit(user_reputation, rules)
        
        assert funding_limit > 0
        assert funding_limit <= rules.max_funding_amount * 2.0  # Max multiplier
    
    def test_funding_priority_calculation(self):
        """Test comprehensive funding priority calculation"""
        user_id = "priority-user"
        user_reputation = {
            "current_tier": "expert",
            "total_points": 1200
        }
        user_stats = {
            "total_contributions": 100,
            "recent_activity": 25,
            "consecutive_days": 30,
            "quality_score": 0.9,
            "average_points": 12.0
        }
        
        priority = self.engine.calculate_funding_priority(
            user_id=user_id,
            user_reputation=user_reputation,
            user_stats=user_stats
        )
        
        assert priority.user_id == user_id
        assert priority.total_priority > 0
        assert priority.funding_multiplier > 1.0
        assert priority.escrow_priority > 0
    
    def test_eligibility_summary(self):
        """Test eligibility summary generation"""
        user_id = "summary-user"
        
        # Check eligibility for all grant types
        user_reputation = {
            "current_tier": "expert",
            "total_points": 1200,
            "contribution_count": 50
        }
        user_badges = ["expert", "quality_controller"]
        
        for grant_type in GrantType:
            self.engine.check_user_eligibility(
                user_id=user_id,
                grant_type=grant_type,
                user_reputation=user_reputation,
                user_badges=user_badges
            )
        
        summary = self.engine.get_user_eligibility_summary(user_id)
        
        assert "eligible_grants" in summary
        assert "pending_grants" in summary
        assert "ineligible_grants" in summary
        assert summary["total_grants"] == len(GrantType)
    
    def test_funding_priority_leaderboard(self):
        """Test funding priority leaderboard"""
        # Create multiple users with different priorities
        users = ["user1", "user2", "user3"]
        
        for i, user_id in enumerate(users):
            user_reputation = {
                "current_tier": "expert",
                "total_points": 1000 + (i * 500)
            }
            user_stats = {
                "total_contributions": 50 + (i * 25),
                "recent_activity": 20 + (i * 5),
                "consecutive_days": 15 + (i * 5),
                "quality_score": 0.8 + (i * 0.1),
                "average_points": 10.0 + (i * 2.0)
            }
            
            self.engine.calculate_funding_priority(
                user_id=user_id,
                user_reputation=user_reputation,
                user_stats=user_stats
            )
        
        leaderboard = self.engine.get_funding_priority_leaderboard(limit=10)
        
        assert len(leaderboard) > 0
        # Should be sorted by total_priority (highest first)
        assert leaderboard[0]["total_priority"] >= leaderboard[-1]["total_priority"]
    
    def test_visibility_rules(self):
        """Test grant visibility rules"""
        grant_type = GrantType.FEATURE_DEVELOPMENT
        
        # Test different user tiers
        test_cases = [
            ("newcomer", False),
            ("contributor", False),
            ("regular", True),
            ("expert", True),
            ("master", True)
        ]
        
        for user_tier, expected_can_view in test_cases:
            rules = self.engine.get_grant_visibility_rules(grant_type, user_tier)
            assert rules["can_view"] == expected_can_view
    
    def test_escrow_rules(self):
        """Test escrow rules retrieval"""
        grant_type = GrantType.FEATURE_DEVELOPMENT
        escrow_rules = self.engine.get_escrow_rules(grant_type)
        
        assert "auto_approval" in escrow_rules
        assert "review_required" in escrow_rules
        assert "milestone_validation" in escrow_rules
    
    def test_review_requirements(self):
        """Test review requirements retrieval"""
        grant_type = GrantType.FEATURE_DEVELOPMENT
        review_requirements = self.engine.get_review_requirements(grant_type)
        
        assert "expert_review" in review_requirements
        assert "community_vote" in review_requirements
        assert "technical_assessment" in review_requirements


class TestReputationRoutes:
    """Test reputation API routes"""
    
    def setup_method(self):
        self.client = TestClient(app)
        # Add reputation routes to app
        app.include_router(router)
    
    @patch('planarx_community.reputation.routes.get_current_user')
    def test_record_contribution(self, mock_get_user):
        """Test recording contribution via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        response = self.client.post("/reputation/contribute", json={
            "contribution_type": "draft_submitted",
            "metadata": {"draft_id": "draft-123"},
            "quality_score": 1.0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "event" in data
    
    @patch('planarx_community.reputation.routes.get_current_user')
    def test_get_user_reputation(self, mock_get_user):
        """Test getting user reputation via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # First create some reputation
        reputation_engine = ReputationScoringEngine() # Assuming reputation_engine is defined elsewhere or needs to be imported
        reputation_engine.record_contribution(
            user_id="test-user",
            contribution_type=ContributionType.DRAFT_SUBMITTED
        )
        
        response = self.client.get("/reputation/profile/test-user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "profile" in data
    
    @patch('planarx_community.reputation.routes.get_current_user')
    def test_get_leaderboard(self, mock_get_user):
        """Test getting reputation leaderboard via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        response = self.client.get("/reputation/leaderboard?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "leaderboard" in data
    
    @patch('planarx_community.reputation.routes.get_current_user')
    def test_get_all_badges(self, mock_get_user):
        """Test getting all badges via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        response = self.client.get("/reputation/badges")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "badges" in data
        assert len(data["badges"]) > 0
    
    @patch('planarx_community.reputation.routes.get_current_user')
    def test_get_user_badges(self, mock_get_user):
        """Test getting user badges via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # Award a badge first
        badge_system = BadgeSystem() # Assuming badge_system is defined elsewhere or needs to be imported
        badge_system.award_badge("test-user", "contributor")
        
        response = self.client.get("/reputation/user/test-user/badges")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "badges" in data
        assert len(data["badges"]) > 0
    
    @patch('planarx_community.reputation.routes.get_current_user')
    def test_get_grant_eligibility(self, mock_get_user):
        """Test getting grant eligibility via API"""
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_get_user.return_value = mock_user
        
        # Create some reputation first
        reputation_engine = ReputationScoringEngine() # Assuming reputation_engine is defined elsewhere or needs to be imported
        reputation_engine.record_contribution(
            user_id="test-user",
            contribution_type=ContributionType.DRAFT_SUBMITTED
        )
        
        response = self.client.get("/reputation/grant-eligibility/test-user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "eligibility" in data
        assert "funding_priority" in data


class TestReputationIntegration:
    """Integration tests for reputation system"""
    
    def setup_method(self):
        self.scoring_engine = ReputationScoringEngine()
        self.badge_system = BadgeSystem()
        self.grant_engine = GrantEligibilityEngine()
    
    def test_full_reputation_workflow(self):
        """Test complete reputation workflow"""
        user_id = "workflow-user"
        
        # 1. Record contributions
        contributions = [
            (ContributionType.DRAFT_SUBMITTED, {"draft_id": "draft-1"}),
            (ContributionType.COMMENT_ADDED, {"comment_id": "comment-1"}),
            (ContributionType.THREAD_RESOLVED, {"thread_id": "thread-1"}),
            (ContributionType.ANNOTATION_ADDED, {"annotation_id": "annotation-1"})
        ]
        
        for contribution_type, metadata in contributions:
            event = self.scoring_engine.record_contribution(
                user_id=user_id,
                contribution_type=contribution_type,
                metadata=metadata
            )
            assert event is not None
        
        # 2. Check reputation
        reputation = self.scoring_engine.get_user_reputation(user_id)
        assert reputation is not None
        assert reputation.total_points > 0
        assert reputation.contribution_count == 4
        
        # 3. Check badge eligibility
        user_stats = self.scoring_engine.get_contribution_stats(user_id)
        eligible_badges = self.badge_system.check_badge_eligibility(user_id, user_stats)
        assert len(eligible_badges) > 0
        
        # 4. Award badges
        for badge in eligible_badges:
            user_badge = self.badge_system.award_badge(user_id, badge.id)
            assert user_badge is not None
        
        # 5. Check grant eligibility
        user_badges = [badge.badge_id for badge in self.badge_system.get_user_badges(user_id)]
        eligibility = self.grant_engine.check_user_eligibility(
            user_id=user_id,
            grant_type=GrantType.BUG_FIX,
            user_reputation={
                "current_tier": reputation.current_tier.value,
                "total_points": reputation.total_points,
                "contribution_count": reputation.contribution_count
            },
            user_badges=user_badges
        )
        
        assert eligibility is not None
        assert eligibility.status in [EligibilityStatus.ELIGIBLE, EligibilityStatus.PENDING, EligibilityStatus.INELIGIBLE]
        
        # 6. Calculate funding priority
        priority = self.grant_engine.calculate_funding_priority(
            user_id=user_id,
            user_reputation={
                "current_tier": reputation.current_tier.value,
                "total_points": reputation.total_points
            },
            user_stats=user_stats
        )
        
        assert priority.total_priority > 0
        assert priority.funding_multiplier > 1.0
    
    def test_reputation_abuse_detection_workflow(self):
        """Test reputation abuse detection workflow"""
        user_id = "abuse-user"
        
        # 1. Normal contributions
        for i in range(5):
            event = self.scoring_engine.record_contribution(
                user_id=user_id,
                contribution_type=ContributionType.COMMENT_ADDED
            )
            assert event.abuse_score < 0.5
        
        # 2. Rapid-fire contributions (abuse)
        for i in range(15):
            event = self.scoring_engine.record_contribution(
                user_id=user_id,
                contribution_type=ContributionType.COMMENT_ADDED
            )
        
        # 3. Check abuse detection
        abuse = self.scoring_engine.abuse_detection.get(user_id)
        assert abuse is not None
        assert abuse.abuse_score > 0.3
        assert abuse.review_required == True
        
        # 4. Flag for review
        self.scoring_engine.flag_user_for_review(user_id, "Suspicious activity")
        assert abuse.warning_count == 1
        
        # 5. Clear flag
        self.scoring_engine.clear_abuse_flag(user_id, "moderator-123")
        assert abuse.review_required == False
        assert abuse.is_flagged == False
    
    def test_badge_progression_workflow(self):
        """Test badge progression workflow"""
        user_id = "badge-user"
        
        # 1. Start with no badges
        user_badges = self.badge_system.get_user_badges(user_id)
        assert len(user_badges) == 0
        
        # 2. Add contributions to earn badges
        contributions_needed = {
            "contributor": 1,
            "comment_king": 100,
            "helper": 25
        }
        
        for badge_name, count in contributions_needed.items():
            for i in range(count):
                self.scoring_engine.record_contribution(
                    user_id=user_id,
                    contribution_type=ContributionType.COMMENT_ADDED
                )
        
        # 3. Check badge eligibility
        user_stats = self.scoring_engine.get_contribution_stats(user_id)
        eligible_badges = self.badge_system.check_badge_eligibility(user_id, user_stats)
        
        # 4. Award eligible badges
        for badge in eligible_badges:
            user_badge = self.badge_system.award_badge(user_id, badge.id)
            assert user_badge is not None
        
        # 5. Check final badge count
        final_badges = self.badge_system.get_user_badges(user_id)
        assert len(final_badges) > 0
        
        # 6. Check badge summary
        summary = self.badge_system.get_user_badge_summary(user_id)
        assert summary["total_badges"] == len(final_badges)
        assert summary["total_badge_points"] > 0


if __name__ == "__main__":
    pytest.main([__file__]) 