"""
Onboarding Flow with Community Guidelines Integration
Handles user onboarding with mandatory guidelines acceptance
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Onboarding flow steps"""

    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    GUIDELINES_REVIEW = "guidelines_review"
    GUIDELINES_ACCEPTANCE = "guidelines_acceptance"
    PREFERENCES = "preferences"
    VERIFICATION = "verification"
    COMPLETE = "complete"


class OnboardingStatus(Enum):
    """Onboarding status"""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


@dataclass
class OnboardingSession:
    """User onboarding session"""

    id: str
    user_id: str
    current_step: OnboardingStep
    status: OnboardingStatus
    started_at: datetime
    completed_at: Optional[datetime]
    steps_completed: List[str]
    guidelines_accepted: bool
    guidelines_version: str
    acceptance_timestamp: Optional[datetime]
    user_data: Dict

    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = []
        if self.user_data is None:
            self.user_data = {}


@dataclass
class GuidelinesAcceptance:
    """Guidelines acceptance record"""

    id: str
    user_id: str
    guidelines_version: str
    accepted_at: datetime
    ip_address: str
    user_agent: str
    acceptance_method: str  # "onboarding", "update", "re-acceptance"
    previous_acceptance: Optional[str]

    def __post_init__(self):
        if self.previous_acceptance is None:
            self.previous_acceptance = None


class OnboardingFlow:
    """Manages user onboarding with guidelines integration"""

    def __init__(self):
        self.sessions: Dict[str, OnboardingSession] = {}
        self.guidelines_acceptances: Dict[str, List[GuidelinesAcceptance]] = {}
        self.current_guidelines_version = "1.0.0"
        self.onboarding_timeout_days = 30

        self.logger = logging.getLogger(__name__)

    def start_onboarding(
        self, user_id: str, user_data: Dict = None
    ) -> OnboardingSession:
        """Start onboarding process for a new user"""

        session_id = str(uuid.uuid4())

        session = OnboardingSession(
            id=session_id,
            user_id=user_id,
            current_step=OnboardingStep.WELCOME,
            status=OnboardingStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            completed_at=None,
            steps_completed=[],
            guidelines_accepted=False,
            guidelines_version=self.current_guidelines_version,
            acceptance_timestamp=None,
            user_data=user_data or {},
        )

        self.sessions[session_id] = session

        self.logger.info(f"Started onboarding for user {user_id}, session {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Get onboarding session by ID"""
        return self.sessions.get(session_id)

    def get_user_session(self, user_id: str) -> Optional[OnboardingSession]:
        """Get active onboarding session for user"""
        for session in self.sessions.values():
            if (
                session.user_id == user_id
                and session.status == OnboardingStatus.IN_PROGRESS
            ):
                return session
        return None

    def advance_step(
        self, session_id: str, step_data: Dict = None
    ) -> OnboardingSession:
        """Advance to next onboarding step"""

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != OnboardingStatus.IN_PROGRESS:
            raise ValueError(f"Session {session_id} is not in progress")

        # Mark current step as completed
        session.steps_completed.append(session.current_step.value)

        # Update user data if provided
        if step_data:
            session.user_data.update(step_data)

        # Determine next step
        next_step = self._get_next_step(session.current_step)
        session.current_step = next_step

        # Check if onboarding is complete
        if next_step == OnboardingStep.COMPLETE:
            session.status = OnboardingStatus.COMPLETED
            session.completed_at = datetime.utcnow()

        self.logger.info(f"Advanced session {session_id} to step {next_step.value}")
        return session

    def _get_next_step(self, current_step: OnboardingStep) -> OnboardingStep:
        """Determine next step in onboarding flow"""

        step_sequence = [
            OnboardingStep.WELCOME,
            OnboardingStep.PROFILE_SETUP,
            OnboardingStep.GUIDELINES_REVIEW,
            OnboardingStep.GUIDELINES_ACCEPTANCE,
            OnboardingStep.PREFERENCES,
            OnboardingStep.VERIFICATION,
            OnboardingStep.COMPLETE,
        ]

        try:
            current_index = step_sequence.index(current_step)
            return step_sequence[current_index + 1]
        except (ValueError, IndexError):
            return OnboardingStep.COMPLETE

    def accept_guidelines(
        self, session_id: str, ip_address: str, user_agent: str
    ) -> OnboardingSession:
        """Accept community guidelines"""

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.current_step != OnboardingStep.GUIDELINES_ACCEPTANCE:
            raise ValueError("Not at guidelines acceptance step")

        # Record acceptance
        acceptance = GuidelinesAcceptance(
            id=str(uuid.uuid4()),
            user_id=session.user_id,
            guidelines_version=session.guidelines_version,
            accepted_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            acceptance_method="onboarding",
            previous_acceptance=None,
        )

        # Store acceptance record
        if session.user_id not in self.guidelines_acceptances:
            self.guidelines_acceptances[session.user_id] = []
        self.guidelines_acceptances[session.user_id].append(acceptance)

        # Update session
        session.guidelines_accepted = True
        session.acceptance_timestamp = datetime.utcnow()

        self.logger.info(
            f"User {session.user_id} accepted guidelines version {session.guidelines_version}"
        )
        return session

    def check_guidelines_acceptance(self, user_id: str) -> bool:
        """Check if user has accepted current guidelines version"""

        if user_id not in self.guidelines_acceptances:
            return False

        acceptances = self.guidelines_acceptances[user_id]
        if not acceptances:
            return False

        # Check if user has accepted current version
        latest_acceptance = max(acceptances, key=lambda a: a.accepted_at)
        return latest_acceptance.guidelines_version == self.current_guidelines_version

    def get_guidelines_acceptance_history(
        self, user_id: str
    ) -> List[GuidelinesAcceptance]:
        """Get user's guidelines acceptance history"""

        return self.guidelines_acceptances.get(user_id, [])

    def require_guidelines_reacceptance(self, user_id: str) -> bool:
        """Check if user needs to re-accept guidelines due to version update"""

        if not self.check_guidelines_acceptance(user_id):
            return True

        # Check if guidelines version has been updated since last acceptance
        acceptances = self.get_guidelines_acceptance_history(user_id)
        if not acceptances:
            return True

        latest_acceptance = max(acceptances, key=lambda a: a.accepted_at)
        return latest_acceptance.guidelines_version != self.current_guidelines_version

    def update_guidelines_version(self, new_version: str):
        """Update guidelines version (triggers re-acceptance requirement)"""

        old_version = self.current_guidelines_version
        self.current_guidelines_version = new_version

        self.logger.info(
            f"Updated guidelines version from {old_version} to {new_version}"
        )

    def abandon_session(self, session_id: str) -> OnboardingSession:
        """Abandon onboarding session"""

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = OnboardingStatus.ABANDONED
        session.completed_at = datetime.utcnow()

        self.logger.info(f"Abandoned onboarding session {session_id}")
        return session

    def cleanup_expired_sessions(self):
        """Clean up expired onboarding sessions"""

        cutoff_date = datetime.utcnow() - timedelta(days=self.onboarding_timeout_days)
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if (
                session.status == OnboardingStatus.IN_PROGRESS
                and session.started_at < cutoff_date
            ):
                session.status = OnboardingStatus.EXPIRED
                session.completed_at = datetime.utcnow()
                expired_sessions.append(session_id)

        if expired_sessions:
            self.logger.info(
                f"Cleaned up {len(expired_sessions)} expired onboarding sessions"
            )

    def get_onboarding_stats(self) -> Dict:
        """Get onboarding statistics"""

        total_sessions = len(self.sessions)
        completed_sessions = len(
            [
                s
                for s in self.sessions.values()
                if s.status == OnboardingStatus.COMPLETED
            ]
        )
        abandoned_sessions = len(
            [
                s
                for s in self.sessions.values()
                if s.status == OnboardingStatus.ABANDONED
            ]
        )
        expired_sessions = len(
            [s for s in self.sessions.values() if s.status == OnboardingStatus.EXPIRED]
        )

        # Calculate completion rate
        active_sessions = total_sessions - expired_sessions
        completion_rate = (
            (completed_sessions / active_sessions * 100) if active_sessions > 0 else 0
        )

        # Step completion statistics
        step_stats = {}
        for step in OnboardingStep:
            step_stats[step.value] = len(
                [s for s in self.sessions.values() if step.value in s.steps_completed]
            )

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "abandoned_sessions": abandoned_sessions,
            "expired_sessions": expired_sessions,
            "completion_rate": round(completion_rate, 2),
            "step_completion_stats": step_stats,
            "current_guidelines_version": self.current_guidelines_version,
        }


class OnboardingUI:
    """Frontend onboarding interface components"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_welcome_step(self, session: OnboardingSession) -> Dict:
        """Generate welcome step data"""

        return {
            "step": "welcome",
            "title": "Welcome to Arxos",
            "subtitle": "Join the future of construction technology",
            "content": {
                "message": "Welcome to the Arxos community! We're excited to have you join us in advancing construction technology.",
                "features": [
                    "Submit and review construction technology proposals",
                    "Collaborate with industry professionals",
                    "Access funding for innovative projects",
                    "Build your reputation and earn recognition",
                ],
                "next_button": "Get Started",
            },
        }

    def generate_profile_setup_step(self, session: OnboardingSession) -> Dict:
        """Generate profile setup step data"""

        return {
            "step": "profile_setup",
            "title": "Complete Your Profile",
            "subtitle": "Help us personalize your experience",
            "content": {
                "fields": [
                    {
                        "name": "display_name",
                        "label": "Display Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "Your professional name",
                    },
                    {
                        "name": "bio",
                        "label": "Professional Bio",
                        "type": "textarea",
                        "required": False,
                        "placeholder": "Tell us about your background in construction technology",
                    },
                    {
                        "name": "expertise",
                        "label": "Areas of Expertise",
                        "type": "multiselect",
                        "required": False,
                        "options": [
                            "BIM and Digital Twins",
                            "Construction Management",
                            "Structural Engineering",
                            "MEP Systems",
                            "Sustainability",
                            "Safety and Compliance",
                            "Project Planning",
                            "Technology Integration",
                        ],
                    },
                    {
                        "name": "experience_level",
                        "label": "Experience Level",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Student",
                            "Early Career (1-5 years)",
                            "Mid Career (5-15 years)",
                            "Senior Professional (15+ years)",
                            "Industry Leader",
                        ],
                    },
                ],
                "next_button": "Continue",
            },
        }

    def generate_guidelines_review_step(self, session: OnboardingSession) -> Dict:
        """Generate guidelines review step data"""

        return {
            "step": "guidelines_review",
            "title": "Community Guidelines",
            "subtitle": "Please review our community standards",
            "content": {
                "message": "To ensure a safe and productive environment, all community members must review and understand our guidelines.",
                "guidelines_version": session.guidelines_version,
                "sections": [
                    {
                        "title": "Core Principles",
                        "items": [
                            "Professional Excellence",
                            "Respect and Inclusion",
                            "Constructive Collaboration",
                            "Safety and Compliance",
                            "Transparency and Accountability",
                        ],
                    },
                    {
                        "title": "Prohibited Behavior",
                        "items": [
                            "Safety Violations (Immediate Ban)",
                            "Harassment and Abuse (Temporary Ban)",
                            "Spam and Misinformation (Warning)",
                            "Professional Misconduct (Review)",
                            "Minor Violations (Warning)",
                        ],
                    },
                    {
                        "title": "Content Standards",
                        "items": [
                            "Accurate technical information",
                            "Professional language and conduct",
                            "Constructive feedback and discussions",
                            "Safety-focused contributions",
                            "Original work or proper attribution",
                        ],
                    },
                ],
                "next_button": "I Understand",
            },
        }

    def generate_guidelines_acceptance_step(self, session: OnboardingSession) -> Dict:
        """Generate guidelines acceptance step data"""

        return {
            "step": "guidelines_acceptance",
            "title": "Accept Community Guidelines",
            "subtitle": "Confirm your agreement to follow our standards",
            "content": {
                "message": "By accepting these guidelines, you agree to follow our community standards and understand the consequences of violations.",
                "guidelines_version": session.guidelines_version,
                "acceptance_text": "I have read, understood, and agree to follow the Arxos Community Guidelines. I understand that violations may result in warnings, restrictions, or account termination.",
                "checkbox_label": "I accept the community guidelines",
                "checkbox_required": True,
                "next_button": "Accept and Continue",
            },
        }

    def generate_preferences_step(self, session: OnboardingSession) -> Dict:
        """Generate preferences step data"""

        return {
            "step": "preferences",
            "title": "Set Your Preferences",
            "subtitle": "Customize your Arxos experience",
            "content": {
                "sections": [
                    {
                        "title": "Notification Preferences",
                        "fields": [
                            {
                                "name": "email_notifications",
                                "label": "Email Notifications",
                                "type": "checkbox",
                                "default": True,
                                "description": "Receive updates about your proposals and community activity",
                            },
                            {
                                "name": "collaboration_alerts",
                                "label": "Collaboration Alerts",
                                "type": "checkbox",
                                "default": True,
                                "description": "Get notified about collaboration opportunities",
                            },
                            {
                                "name": "funding_updates",
                                "label": "Funding Updates",
                                "type": "checkbox",
                                "default": True,
                                "description": "Receive updates about funding opportunities and project status",
                            },
                        ],
                    },
                    {
                        "title": "Privacy Settings",
                        "fields": [
                            {
                                "name": "profile_visibility",
                                "label": "Profile Visibility",
                                "type": "select",
                                "default": "public",
                                "options": [
                                    {
                                        "value": "public",
                                        "label": "Public - Visible to all users",
                                    },
                                    {
                                        "value": "community",
                                        "label": "Community - Visible to registered users",
                                    },
                                    {
                                        "value": "private",
                                        "label": "Private - Visible to collaborators only",
                                    },
                                ],
                            },
                            {
                                "name": "activity_sharing",
                                "label": "Share Activity",
                                "type": "checkbox",
                                "default": True,
                                "description": "Allow your activity to be visible to the community",
                            },
                        ],
                    },
                ],
                "next_button": "Save Preferences",
            },
        }

    def generate_verification_step(self, session: OnboardingSession) -> Dict:
        """Generate verification step data"""

        return {
            "step": "verification",
            "title": "Verify Your Account",
            "subtitle": "Complete your registration",
            "content": {
                "message": "To ensure account security and prevent abuse, we need to verify your email address.",
                "verification_methods": [
                    {
                        "type": "email",
                        "label": "Email Verification",
                        "description": "We'll send a verification link to your email address",
                        "required": True,
                    }
                ],
                "resend_button": "Resend Verification",
                "next_button": "Complete Setup",
            },
        }

    def generate_completion_step(self, session: OnboardingSession) -> Dict:
        """Generate completion step data"""

        return {
            "step": "complete",
            "title": "Welcome to Arxos!",
            "subtitle": "Your account is ready",
            "content": {
                "message": "Congratulations! You've successfully completed the onboarding process and are now a member of the Arxos community.",
                "next_steps": [
                    "Explore the platform and discover projects",
                    "Submit your first proposal or comment",
                    "Connect with other community members",
                    "Build your reputation and earn badges",
                ],
                "dashboard_button": "Go to Dashboard",
                "explore_button": "Explore Projects",
            },
        }

    def generate_step_data(self, session: OnboardingSession) -> Dict:
        """Generate data for current onboarding step"""

        step_generators = {
            OnboardingStep.WELCOME: self.generate_welcome_step,
            OnboardingStep.PROFILE_SETUP: self.generate_profile_setup_step,
            OnboardingStep.GUIDELINES_REVIEW: self.generate_guidelines_review_step,
            OnboardingStep.GUIDELINES_ACCEPTANCE: self.generate_guidelines_acceptance_step,
            OnboardingStep.PREFERENCES: self.generate_preferences_step,
            OnboardingStep.VERIFICATION: self.generate_verification_step,
            OnboardingStep.COMPLETE: self.generate_completion_step,
        }

        generator = step_generators.get(session.current_step)
        if generator:
            return generator(session)
        else:
            return {"error": "Unknown step"}

    def validate_step_data(self, step: OnboardingStep, data: Dict) -> Dict:
        """Validate step data and return errors if any"""

        errors = {}

        if step == OnboardingStep.PROFILE_SETUP:
            if not data.get("display_name"):
                errors["display_name"] = "Display name is required"
            if not data.get("experience_level"):
                errors["experience_level"] = "Experience level is required"

        elif step == OnboardingStep.GUIDELINES_ACCEPTANCE:
            if not data.get("guidelines_accepted"):
                errors["guidelines_accepted"] = (
                    "You must accept the community guidelines to continue"
                )

        elif step == OnboardingStep.PREFERENCES:
            # Preferences are optional, no validation needed
            pass

        return errors


# Global onboarding flow instance
onboarding_flow = OnboardingFlow()
onboarding_ui = OnboardingUI()
