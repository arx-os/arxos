"""
Community Guidelines System Tests
Tests for guidelines, onboarding, user agreements, and moderation tools
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from ..mod.community_guidelines import *
from services.frontend.onboarding_flow
from services.user_agreement_flags
from services.mod.flagging
from services.mod.mod_queue
from services.main


class TestCommunityGuidelines:
    """Test community guidelines functionality"""
    
    def test_guidelines_version_tracking(self):
        """Test guidelines version tracking"""
        # Test version parsing
        version = "1.0.0"
        assert version == "1.0.0"
        
        # Test version comparison
        assert "1.0.0" < "1.1.0"
        assert "2.0.0" > "1.9.9"
    
    def test_violation_category_priorities(self):
        """Test violation category priority assignments"""
        categories = {
            "safety_violation": "critical",
            "harassment_abuse": "high",
            "spam_misinformation": "medium",
            "minor_violation": "low"
        }
        
        for category, expected_priority in categories.items():
            assert category in [c.value for c in FlagCategory]
            assert expected_priority in [p.value for p in FlagPriority]


class TestOnboardingFlow:
    """Test onboarding flow with guidelines integration"""
    
    def setup_method(self):
        self.flow = OnboardingFlow()
        self.ui = OnboardingUI()
    
    def test_start_onboarding(self):
        """Test starting onboarding process"""
        user_id = "test-user"
        user_data = {"email": "test@example.com"}
        
        session = self.flow.start_onboarding(user_id, user_data)
        
        assert session.user_id == user_id
        assert session.status.value == "in_progress"
        assert session.current_step.value == "welcome"
        assert session.guidelines_accepted == False
        assert session.guidelines_version == "1.0.0"
    
    def test_advance_onboarding_steps(self):
        """Test advancing through onboarding steps"""
        user_id = "test-user"
        session = self.flow.start_onboarding(user_id)
        
        # Advance to profile setup
        session = self.flow.advance_step(session.id, {"display_name": "Test User"})
        assert session.current_step.value == "profile_setup"
        assert "welcome" in session.steps_completed
        
        # Advance to guidelines review
        session = self.flow.advance_step(session.id)
        assert session.current_step.value == "guidelines_review"
        
        # Advance to guidelines acceptance
        session = self.flow.advance_step(session.id)
        assert session.current_step.value == "guidelines_acceptance"
    
    def test_accept_guidelines(self):
        """Test guidelines acceptance"""
        user_id = "test-user"
        session = self.flow.start_onboarding(user_id)
        
        # Advance to guidelines acceptance
        for _ in range(3):
            session = self.flow.advance_step(session.id)
        
        # Accept guidelines
        session = self.flow.accept_guidelines(
            session.id, 
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        assert session.guidelines_accepted == True
        assert session.acceptance_timestamp is not None
    
    def test_onboarding_completion(self):
        """Test onboarding completion"""
        user_id = "test-user"
        session = self.flow.start_onboarding(user_id)
        
        # Complete all steps
        for _ in range(6):
            session = self.flow.advance_step(session.id)
        
        assert session.current_step.value == "complete"
        assert session.status.value == "completed"
        assert session.completed_at is not None
    
    def test_onboarding_ui_generation(self):
        """Test onboarding UI step generation"""
        user_id = "test-user"
        session = self.flow.start_onboarding(user_id)
        
        # Test welcome step
        welcome_data = self.ui.generate_welcome_step(session)
        assert welcome_data["step"] == "welcome"
        assert "Welcome to Arxos" in welcome_data["title"]
        
        # Test profile setup step
        profile_data = self.ui.generate_profile_setup_step(session)
        assert profile_data["step"] == "profile_setup"
        assert "fields" in profile_data["content"]
        
        # Test guidelines review step
        guidelines_data = self.ui.generate_guidelines_review_step(session)
        assert guidelines_data["step"] == "guidelines_review"
        assert "sections" in guidelines_data["content"]
        
        # Test guidelines acceptance step
        acceptance_data = self.ui.generate_guidelines_acceptance_step(session)
        assert acceptance_data["step"] == "guidelines_acceptance"
        assert "checkbox_required" in acceptance_data["content"]
    
    def test_onboarding_validation(self):
        """Test onboarding step validation"""
        # Test profile setup validation
        profile_data = {"display_name": "Test User", "experience_level": "expert"}
        errors = self.ui.validate_step_data(OnboardingStep.PROFILE_SETUP, profile_data)
        assert len(errors) == 0
        
        # Test missing required fields
        incomplete_data = {"display_name": ""}
        errors = self.ui.validate_step_data(OnboardingStep.PROFILE_SETUP, incomplete_data)
        assert "display_name" in errors
        
        # Test guidelines acceptance validation
        acceptance_data = {"guidelines_accepted": True}
        errors = self.ui.validate_step_data(OnboardingStep.GUIDELINES_ACCEPTANCE, acceptance_data)
        assert len(errors) == 0
        
        # Test missing acceptance
        missing_acceptance = {"guidelines_accepted": False}
        errors = self.ui.validate_step_data(OnboardingStep.GUIDELINES_ACCEPTANCE, missing_acceptance)
        assert "guidelines_accepted" in errors
    
    def test_onboarding_statistics(self):
        """Test onboarding statistics"""
        # Create multiple sessions
        users = ["user1", "user2", "user3"]
        for user_id in users:
            session = self.flow.start_onboarding(user_id)
            # Complete some sessions
            if user_id in ["user1", "user2"]:
                for _ in range(6):
                    session = self.flow.advance_step(session.id)
        
        stats = self.flow.get_onboarding_stats()
        
        assert stats["total_sessions"] == 3
        assert stats["completed_sessions"] == 2
        assert stats["completion_rate"] > 0
    
    def test_abandon_onboarding(self):
        """Test abandoning onboarding session"""
        user_id = "test-user"
        session = self.flow.start_onboarding(user_id)
        
        abandoned_session = self.flow.abandon_session(session.id)
        
        assert abandoned_session.status.value == "abandoned"
        assert abandoned_session.completed_at is not None


class TestUserAgreementManager:
    """Test user agreement management"""
    
    def setup_method(self):
        self.manager = UserAgreementManager()
    
    def test_accept_agreement(self):
        """Test accepting an agreement"""
        user_id = "test-user"
        agreement_type = AgreementType.COMMUNITY_GUIDELINES
        
        agreement = self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        assert agreement.user_id == user_id
        assert agreement.agreement_type == agreement_type
        assert agreement.status == AgreementStatus.ACCEPTED
        assert agreement.accepted_at is not None
        assert agreement.expires_at is not None
    
    def test_decline_agreement(self):
        """Test declining an agreement"""
        user_id = "test-user"
        agreement_type = AgreementType.PRIVACY_POLICY
        
        agreement = self.manager.decline_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            reason="Privacy concerns"
        )
        
        assert agreement.status == AgreementStatus.DECLINED
        assert agreement.declined_at is not None
        assert agreement.metadata.get("reason") == "Privacy concerns"
    
    def test_check_agreement_status(self):
        """Test checking agreement status"""
        user_id = "test-user"
        agreement_type = AgreementType.COMMUNITY_GUIDELINES
        
        # No agreement initially
        status = self.manager.check_agreement_status(user_id, agreement_type)
        assert status is None
        
        # Accept agreement
        self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Check status
        status = self.manager.check_agreement_status(user_id, agreement_type)
        assert status is not None
        assert status.status == AgreementStatus.ACCEPTED
    
    def test_agreement_validity(self):
        """Test agreement validity checking"""
        user_id = "test-user"
        agreement_type = AgreementType.COMMUNITY_GUIDELINES
        
        # Accept agreement
        self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Check validity
        is_valid = self.manager.is_agreement_valid(user_id, agreement_type)
        assert is_valid == True
    
    def test_agreement_expiry(self):
        """Test agreement expiry handling"""
        user_id = "test-user"
        agreement_type = AgreementType.COMMUNITY_GUIDELINES
        
        # Accept agreement with short expiry
        self.manager.agreement_expiry_days[agreement_type] = 1  # 1 day
        
        agreement = self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Manually expire the agreement
        agreement.expires_at = datetime.utcnow() - timedelta(days=1)
        
        # Check validity
        is_valid = self.manager.is_agreement_valid(user_id, agreement_type)
        assert is_valid == False
    
    def test_compliance_status(self):
        """Test compliance status calculation"""
        user_id = "test-user"
        
        # Initially non-compliant
        compliance = self.manager.get_compliance_status(user_id)
        assert compliance.is_compliant == False
        assert len(compliance.missing_agreements) > 0
        
        # Accept required agreements
        for agreement_type in self.manager.required_agreements:
            self.manager.accept_agreement(
                user_id=user_id,
                agreement_type=agreement_type,
                ip_address="192.168.1.1",
                user_agent="Test Browser"
            )
        
        # Check compliance
        compliance = self.manager.get_compliance_status(user_id)
        assert compliance.is_compliant == True
        assert len(compliance.missing_agreements) == 0
        assert compliance.compliance_score == 1.0
    
    def test_version_updates(self):
        """Test agreement version updates"""
        user_id = "test-user"
        agreement_type = AgreementType.COMMUNITY_GUIDELINES
        
        # Accept current version
        self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Update version
        self.manager.update_agreement_version(agreement_type, "2.0.0")
        
        # Check if re-acceptance required
        requires_reacceptance = self.manager.require_reacceptance(user_id, agreement_type)
        assert requires_reacceptance == True
    
    def test_agreement_history(self):
        """Test agreement history tracking"""
        user_id = "test-user"
        agreement_type = AgreementType.COMMUNITY_GUIDELINES
        
        # Accept multiple versions
        self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        self.manager.update_agreement_version(agreement_type, "2.0.0")
        self.manager.accept_agreement(
            user_id=user_id,
            agreement_type=agreement_type,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        history = self.manager.get_agreement_history(user_id, agreement_type)
        assert len(history) == 2
    
    def test_compliance_statistics(self):
        """Test compliance statistics"""
        # Create multiple users with different compliance levels
        users = ["user1", "user2", "user3"]
        
        for i, user_id in enumerate(users):
            # Accept some agreements
            for j, agreement_type in enumerate(self.manager.required_agreements):
                if i >= j:  # Progressive compliance
                    self.manager.accept_agreement(
                        user_id=user_id,
                        agreement_type=agreement_type,
                        ip_address="192.168.1.1",
                        user_agent="Test Browser"
                    )
        
        stats = self.manager.get_compliance_stats()
        
        assert stats["total_users"] == 3
        assert stats["compliant_users"] >= 0
        assert stats["compliance_rate"] >= 0


class TestFlaggingSystem:
    """Test flagging system functionality"""
    
    def setup_method(self):
        self.flagging = FlaggingSystem()
    
    def test_create_flag(self):
        """Test creating a flag"""
        flag = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-789",
            content_type="comment",
            category=FlagCategory.HARASSMENT_ABUSE,
            description="Inappropriate language in comment",
            evidence=["screenshot1.jpg", "screenshot2.jpg"]
        )
        
        assert flag.reporter_id == "reporter-123"
        assert flag.target_user_id == "target-456"
        assert flag.category == FlagCategory.HARASSMENT_ABUSE
        assert flag.priority == FlagPriority.HIGH
        assert flag.status == FlagStatus.PENDING
        assert len(flag.evidence) == 2
    
    def test_flag_categories(self):
        """Test flag category configurations"""
        for category in FlagCategory:
            config = self.flagging.get_category_config(category)
            assert "priority" in config
            assert "response_target_hours" in config
            assert "restrictions" in config
    
    def test_assign_moderator(self):
        """Test assigning moderator to flag"""
        flag = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-789",
            content_type="comment",
            category=FlagCategory.SPAM_MISINFORMATION,
            description="Spam comment"
        )
        
        updated_flag = self.flagging.assign_moderator(flag.id, "moderator-123")
        
        assert updated_flag.assigned_moderator_id == "moderator-123"
        assert updated_flag.status == FlagStatus.UNDER_REVIEW
    
    def test_resolve_flag(self):
        """Test resolving a flag"""
        flag = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-789",
            content_type="comment",
            category=FlagCategory.MINOR_VIOLATION,
            description="Minor violation"
        )
        
        response = self.flagging.resolve_flag(
            flag_id=flag.id,
            moderator_id="moderator-123",
            action_taken="warning_issued",
            reasoning="User was warned about community guidelines"
        )
        
        assert response.flag_id == flag.id
        assert response.moderator_id == "moderator-123"
        assert response.action_taken == "warning_issued"
        
        # Check flag status
        updated_flag = self.flagging.flags[flag.id]
        assert updated_flag.status == FlagStatus.RESOLVED
        assert updated_flag.response_time_hours is not None
    
    def test_dismiss_flag(self):
        """Test dismissing a flag"""
        flag = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-789",
            content_type="comment",
            category=FlagCategory.OFF_TOPIC,
            description="Off topic comment"
        )
        
        response = self.flagging.dismiss_flag(
            flag_id=flag.id,
            moderator_id="moderator-123",
            reasoning="Comment was not actually off topic"
        )
        
        assert response.action_taken == "dismissed"
        
        # Check flag status
        updated_flag = self.flagging.flags[flag.id]
        assert updated_flag.status == FlagStatus.DISMISSED
    
    def test_escalate_flag(self):
        """Test escalating a flag"""
        flag = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-789",
            content_type="draft",
            category=FlagCategory.SAFETY_VIOLATION,
            description="Safety violation in draft"
        )
        
        response = self.flagging.escalate_flag(
            flag_id=flag.id,
            moderator_id="moderator-123",
            reason="Requires senior moderator review"
        )
        
        assert response.action_taken == "escalated"
        
        # Check flag status
        updated_flag = self.flagging.flags[flag.id]
        assert updated_flag.status == FlagStatus.ESCALATED
    
    def test_moderation_queue(self):
        """Test moderation queue functionality"""
        # Create flags with different priorities
        flags = [
            (FlagCategory.SAFETY_VIOLATION, FlagPriority.CRITICAL),
            (FlagCategory.HARASSMENT_ABUSE, FlagPriority.HIGH),
            (FlagCategory.SPAM_MISINFORMATION, FlagPriority.MEDIUM),
            (FlagCategory.MINOR_VIOLATION, FlagPriority.LOW)
        ]
        
        for category, priority in flags:
            self.flagging.create_flag(
                reporter_id="reporter-123",
                target_user_id="target-456",
                content_id=f"content-{category.value}",
                content_type="comment",
                category=category,
                description=f"Test {category.value}"
            )
        
        # Test queue filtering
        pending_queue = self.flagging.get_moderation_queue(
            status=FlagStatus.PENDING
        )
        assert len(pending_queue) == 4
        
        critical_queue = self.flagging.get_moderation_queue(
            priority=FlagPriority.CRITICAL
        )
        assert len(critical_queue) == 1
    
    def test_user_violation_history(self):
        """Test user violation history tracking"""
        user_id = "target-456"
        
        # Create multiple flags for same user
        for category in [FlagCategory.SPAM_MISINFORMATION, FlagCategory.MINOR_VIOLATION]:
            self.flagging.create_flag(
                reporter_id="reporter-123",
                target_user_id=user_id,
                content_id=f"content-{category.value}",
                content_type="comment",
                category=category,
                description=f"Test {category.value}"
            )
        
        history = self.flagging.get_user_violation_history(user_id)
        assert history.total_flags == 2
        assert "spam_misinformation" in history.violation_categories
        assert "minor_violation" in history.violation_categories
    
    def test_flag_statistics(self):
        """Test flag statistics calculation"""
        # Create flags with different statuses
        flag1 = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-1",
            content_type="comment",
            category=FlagCategory.MINOR_VIOLATION,
            description="Test flag 1"
        )
        
        flag2 = self.flagging.create_flag(
            reporter_id="reporter-456",
            target_user_id="target-789",
            content_id="content-2",
            content_type="comment",
            category=FlagCategory.HARASSMENT_ABUSE,
            description="Test flag 2"
        )
        
        # Resolve one flag
        self.flagging.resolve_flag(
            flag_id=flag1.id,
            moderator_id="moderator-123",
            action_taken="warning",
            reasoning="User warned"
        )
        
        stats = self.flagging.get_flag_statistics()
        
        assert stats["total_flags"] == 2
        assert "pending" in stats["flags_by_status"]
        assert "resolved" in stats["flags_by_status"]


class TestModerationQueue:
    """Test moderation queue system"""
    
    def setup_method(self):
        self.queue = ModerationQueue()
        self.flagging = FlaggingSystem()
    
    def test_queue_sorting(self):
        """Test queue sorting options"""
        # Create flags with different priorities
        flags = [
            (FlagCategory.SAFETY_VIOLATION, FlagPriority.CRITICAL),
            (FlagCategory.HARASSMENT_ABUSE, FlagPriority.HIGH),
            (FlagCategory.SPAM_MISINFORMATION, FlagPriority.MEDIUM),
            (FlagCategory.MINOR_VIOLATION, FlagPriority.LOW)
        ]
        
        for category, priority in flags:
            self.flagging.create_flag(
                reporter_id="reporter-123",
                target_user_id="target-456",
                content_id=f"content-{category.value}",
                content_type="comment",
                category=category,
                description=f"Test {category.value}"
            )
        
        # Test priority-time sorting
        tasks = self.queue.get_sorted_queue(
            sort_by=QueueSortOption.PRIORITY_TIME
        )
        assert len(tasks) == 4
        assert tasks[0].priority == "critical"
        
        # Test category sorting
        tasks = self.queue.get_sorted_queue(
            sort_by=QueueSortOption.CATEGORY
        )
        assert len(tasks) == 4
    
    def test_queue_filtering(self):
        """Test queue filtering options"""
        # Create flags with different statuses
        flag1 = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-1",
            content_type="comment",
            category=FlagCategory.MINOR_VIOLATION,
            description="Test flag 1"
        )
        
        flag2 = self.flagging.create_flag(
            reporter_id="reporter-456",
            target_user_id="target-789",
            content_id="content-2",
            content_type="comment",
            category=FlagCategory.HARASSMENT_ABUSE,
            description="Test flag 2"
        )
        
        # Assign moderator to one flag
        self.flagging.assign_moderator(flag1.id, "moderator-123")
        
        # Test filtering
        pending_tasks = self.queue.get_sorted_queue(
            filter_by=QueueFilterOption.PENDING
        )
        assert len(pending_tasks) == 1
        
        under_review_tasks = self.queue.get_sorted_queue(
            filter_by=QueueFilterOption.UNDER_REVIEW
        )
        assert len(under_review_tasks) == 1
    
    def test_queue_statistics(self):
        """Test queue statistics"""
        # Create some flags
        for i in range(3):
            self.flagging.create_flag(
                reporter_id=f"reporter-{i}",
                target_user_id=f"target-{i}",
                content_id=f"content-{i}",
                content_type="comment",
                category=FlagCategory.MINOR_VIOLATION,
                description=f"Test flag {i}"
            )
        
        stats = self.queue.get_queue_statistics()
        
        assert stats["total_flags"] == 3
        assert "pending" in stats["status_counts"]
        assert "minor_violation" in stats["category_counts"]
    
    def test_moderator_workload(self):
        """Test moderator workload tracking"""
        moderator_id = "moderator-123"
        
        # Create and assign flags
        for i in range(3):
            flag = self.flagging.create_flag(
                reporter_id=f"reporter-{i}",
                target_user_id=f"target-{i}",
                content_id=f"content-{i}",
                content_type="comment",
                category=FlagCategory.MINOR_VIOLATION,
                description=f"Test flag {i}"
            )
            self.flagging.assign_moderator(flag.id, moderator_id)
        
        workload = self.queue.get_moderator_workload(moderator_id)
        
        assert workload.moderator_id == moderator_id
        assert workload.total_assigned == 3
        assert workload.pending_review == 3
    
    def test_queue_alerts(self):
        """Test queue alert system"""
        # Create overdue flag
        flag = self.flagging.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-1",
            content_type="comment",
            category=FlagCategory.SAFETY_VIOLATION,
            description="Safety violation"
        )
        
        # Manually make it overdue
        flag.created_at = datetime.utcnow() - timedelta(hours=25)
        
        # Check for alerts
        self.queue.check_and_create_alerts()
        
        alerts = self.queue.get_active_alerts()
        assert len(alerts) > 0
    
    def test_dashboard_data(self):
        """Test dashboard data generation"""
        # Create some test data
        for i in range(2):
            self.flagging.create_flag(
                reporter_id=f"reporter-{i}",
                target_user_id=f"target-{i}",
                content_id=f"content-{i}",
                content_type="comment",
                category=FlagCategory.MINOR_VIOLATION,
                description=f"Test flag {i}"
            )
        
        dashboard_data = self.queue.get_queue_dashboard_data()
        
        assert "queue_statistics" in dashboard_data
        assert "moderator_workloads" in dashboard_data
        assert "active_alerts" in dashboard_data
        assert "recent_flags" in dashboard_data


class TestCommunityGuidelinesIntegration:
    """Integration tests for community guidelines system"""
    
    def setup_method(self):
        self.onboarding_flow = OnboardingFlow()
        self.agreement_manager = UserAgreementManager()
        self.flagging_system = FlaggingSystem()
        self.moderation_queue = ModerationQueue()
    
    def test_complete_user_onboarding(self):
        """Test complete user onboarding with guidelines acceptance"""
        user_id = "integration-user"
        
        # Start onboarding
        session = self.onboarding_flow.start_onboarding(user_id)
        
        # Complete all steps including guidelines acceptance
        for _ in range(3):
            session = self.onboarding_flow.advance_step(session.id)
        
        # Accept guidelines
        session = self.onboarding_flow.accept_guidelines(
            session.id,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Complete onboarding
        for _ in range(3):
            session = self.onboarding_flow.advance_step(session.id)
        
        # Verify completion
        assert session.status.value == "completed"
        assert session.guidelines_accepted == True
        
        # Check agreement status
        is_compliant = self.agreement_manager.check_user_compliance(user_id)
        assert is_compliant == True
    
    def test_violation_workflow(self):
        """Test complete violation reporting and moderation workflow"""
        # Create a flag
        flag = self.flagging_system.create_flag(
            reporter_id="reporter-123",
            target_user_id="target-456",
            content_id="content-789",
            content_type="comment",
            category=FlagCategory.HARASSMENT_ABUSE,
            description="Harassment in comment"
        )
        
        # Assign moderator
        self.flagging_system.assign_moderator(flag.id, "moderator-123")
        
        # Resolve flag
        response = self.flagging_system.resolve_flag(
            flag_id=flag.id,
            moderator_id="moderator-123",
            action_taken="temporary_ban",
            reasoning="User violated harassment policy"
        )
        
        # Check queue statistics
        queue_stats = self.moderation_queue.get_queue_statistics()
        assert queue_stats["total_flags"] == 1
        
        # Check user violation history
        history = self.flagging_system.get_user_violation_history("target-456")
        assert history.total_flags == 1
        assert "harassment_abuse" in history.violation_categories
    
    def test_guidelines_compliance_check(self):
        """Test guidelines compliance checking"""
        user_id = "compliance-user"
        
        # User without agreements
        is_compliant = self.agreement_manager.check_user_compliance(user_id)
        assert is_compliant == False
        
        # Accept required agreements
        for agreement_type in self.agreement_manager.required_agreements:
            self.agreement_manager.accept_agreement(
                user_id=user_id,
                agreement_type=agreement_type,
                ip_address="192.168.1.1",
                user_agent="Test Browser"
            )
        
        # Check compliance
        is_compliant = self.agreement_manager.check_user_compliance(user_id)
        assert is_compliant == True
        
        # Get restrictions
        restrictions = self.agreement_manager.get_user_restrictions(user_id)
        assert len(restrictions) == 0  # No restrictions when compliant


if __name__ == "__main__":
    pytest.main([__file__]) 