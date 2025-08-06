"""
Planarx Community - Onboarding Flow System

Comprehensive onboarding system for new users including:
- Multi-step onboarding process
- Progress tracking and analytics
- Engagement tools and gamification
- Automated guidance and notifications
- Community introduction and guidelines
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class OnboardingStep(str, Enum):
    """Onboarding step enumeration."""

    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    COMMUNITY_GUIDELINES = "community_guidelines"
    FIRST_PROJECT = "first_project"
    CONNECTIONS = "connections"
    EXPLORATION = "exploration"
    FINAL = "final"


class OnboardingStatus(str, Enum):
    """Onboarding status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class OnboardingStepData:
    """Data for a specific onboarding step."""

    step_id: str
    step_type: OnboardingStep
    title: str
    description: str
    required: bool
    estimated_time: int  # minutes
    order: int
    dependencies: List[str]  # List of step IDs that must be completed first
    completion_criteria: Dict[str, Any]
    rewards: Dict[str, Any]  # Rewards for completing this step


@dataclass
class UserOnboardingProgress:
    """User's onboarding progress."""

    user_id: str
    current_step: OnboardingStep
    status: OnboardingStatus
    started_at: datetime
    completed_at: Optional[datetime]
    step_progress: Dict[str, Dict[str, Any]]  # step_id -> progress data
    total_time_spent: int  # minutes
    engagement_score: float  # 0-100
    rewards_earned: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class OnboardingAnalytics:
    """Analytics data for onboarding."""

    total_users: int
    completion_rate: float
    average_time: float  # minutes
    dropoff_points: List[Dict[str, Any]]
    step_completion_rates: Dict[str, float]
    engagement_metrics: Dict[str, Any]


@dataclass
class EngagementTool:
    """Tool for user engagement during onboarding."""

    tool_id: str
    name: str
    description: str
    trigger_step: OnboardingStep
    trigger_condition: Dict[str, Any]
    action_type: str  # notification, reward, guidance, etc.
    action_data: Dict[str, Any]


class OnboardingFlowService:
    """Service for managing the onboarding flow."""

    def __init__(self):
        """Initialize the onboarding flow service."""
        self.onboarding_steps: Dict[str, OnboardingStepData] = {}
        self.user_progress: Dict[str, UserOnboardingProgress] = {}
        self.engagement_tools: List[EngagementTool] = []
        self._initialize_onboarding_steps()
        self._initialize_engagement_tools()

    def _initialize_onboarding_steps(self):
        """Initialize the default onboarding steps."""
        steps = [
            OnboardingStepData(
                step_id="welcome",
                step_type=OnboardingStep.WELCOME,
                title="Welcome to Planarx",
                description="Get started with your journey in the Planarx community",
                required=True,
                estimated_time=2,
                order=1,
                dependencies=[],
                completion_criteria={"viewed_welcome": True},
                rewards={"badge": "welcome_badge", "points": 10},
            ),
            OnboardingStepData(
                step_id="profile_setup",
                step_type=OnboardingStep.PROFILE_SETUP,
                title="Complete Your Profile",
                description="Tell us about yourself and your interests",
                required=True,
                estimated_time=5,
                order=2,
                dependencies=["welcome"],
                completion_criteria={"profile_complete": True, "avatar_uploaded": True},
                rewards={"badge": "profile_badge", "points": 25},
            ),
            OnboardingStepData(
                step_id="community_guidelines",
                step_type=OnboardingStep.COMMUNITY_GUIDELINES,
                title="Community Guidelines",
                description="Learn about our community standards and best practices",
                required=True,
                estimated_time=3,
                order=3,
                dependencies=["profile_setup"],
                completion_criteria={"guidelines_read": True, "quiz_passed": True},
                rewards={"badge": "guidelines_badge", "points": 15},
            ),
            OnboardingStepData(
                step_id="first_project",
                step_type=OnboardingStep.FIRST_PROJECT,
                title="Create Your First Project",
                description="Start building by creating your first design project",
                required=True,
                estimated_time=15,
                order=4,
                dependencies=["community_guidelines"],
                completion_criteria={
                    "project_created": True,
                    "project_has_content": True,
                },
                rewards={"badge": "first_project_badge", "points": 50},
            ),
            OnboardingStepData(
                step_id="connections",
                step_type=OnboardingStep.CONNECTIONS,
                title="Connect with Others",
                description="Follow other creators and join the community",
                required=False,
                estimated_time=5,
                order=5,
                dependencies=["first_project"],
                completion_criteria={"followed_users": 3, "joined_groups": 1},
                rewards={"badge": "social_badge", "points": 20},
            ),
            OnboardingStepData(
                step_id="exploration",
                step_type=OnboardingStep.EXPLORATION,
                title="Explore the Platform",
                description="Discover projects, categories, and features",
                required=False,
                estimated_time=8,
                order=6,
                dependencies=["connections"],
                completion_criteria={"explored_categories": 3, "viewed_projects": 10},
                rewards={"badge": "explorer_badge", "points": 30},
            ),
            OnboardingStepData(
                step_id="final",
                step_type=OnboardingStep.FINAL,
                title="You're All Set!",
                description="Complete your onboarding and start creating",
                required=True,
                estimated_time=2,
                order=7,
                dependencies=["exploration"],
                completion_criteria={"onboarding_survey": True},
                rewards={"badge": "onboarding_complete_badge", "points": 100},
            ),
        ]

        for step in steps:
            self.onboarding_steps[step.step_id] = step

    def _initialize_engagement_tools(self):
        """Initialize engagement tools for onboarding."""
        tools = [
            EngagementTool(
                tool_id="welcome_notification",
                name="Welcome Notification",
                description="Send welcome message to new users",
                trigger_step=OnboardingStep.WELCOME,
                trigger_condition={"step_completed": True},
                action_type="notification",
                action_data={"template": "welcome_message", "channel": "email"},
            ),
            EngagementTool(
                tool_id="profile_reminder",
                name="Profile Completion Reminder",
                description="Remind users to complete their profile",
                trigger_step=OnboardingStep.PROFILE_SETUP,
                trigger_condition={
                    "time_spent": 300,
                    "step_completed": False,
                },  # 5 minutes
                action_type="notification",
                action_data={"template": "profile_reminder", "channel": "in_app"},
            ),
            EngagementTool(
                tool_id="first_project_guidance",
                name="First Project Guidance",
                description="Provide guidance for creating first project",
                trigger_step=OnboardingStep.FIRST_PROJECT,
                trigger_condition={"step_started": True},
                action_type="guidance",
                action_data={
                    "type": "interactive_tutorial",
                    "content": "project_creation_guide",
                },
            ),
            EngagementTool(
                tool_id="community_introduction",
                name="Community Introduction",
                description="Introduce users to community features",
                trigger_step=OnboardingStep.CONNECTIONS,
                trigger_condition={"step_completed": True},
                action_type="reward",
                action_data={"type": "bonus_points", "amount": 25},
            ),
        ]

        self.engagement_tools = tools

    async def start_onboarding(self, user_id: str) -> UserOnboardingProgress:
        """Start onboarding for a new user."""
        try:
            # Create onboarding progress
            progress = UserOnboardingProgress(
                user_id=user_id,
                current_step=OnboardingStep.WELCOME,
                status=OnboardingStatus.IN_PROGRESS,
                started_at=datetime.now(),
                completed_at=None,
                step_progress={},
                total_time_spent=0,
                engagement_score=0.0,
                rewards_earned=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.user_progress[user_id] = progress

            # Trigger welcome engagement
            await self._trigger_engagement_tools(
                user_id, OnboardingStep.WELCOME, "step_started"
            )

            logger.info(f"Started onboarding for user {user_id}")
            return progress

        except Exception as e:
            logger.error(f"Error starting onboarding for user {user_id}: {e}")
            raise

    async def get_user_progress(self, user_id: str) -> Optional[UserOnboardingProgress]:
        """Get user's onboarding progress."""
        try:
            return self.user_progress.get(user_id)
        except Exception as e:
            logger.error(f"Error getting progress for user {user_id}: {e}")
            return None

    async def update_step_progress(
        self, user_id: str, step_id: str, progress_data: Dict[str, Any]
    ) -> bool:
        """Update progress for a specific step."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return False

            # Update step progress
            if step_id not in progress.step_progress:
                progress.step_progress[step_id] = {}

            progress.step_progress[step_id].update(progress_data)
            progress.updated_at = datetime.now()

            # Check if step is completed
            step = self.onboarding_steps.get(step_id)
            if step and self._is_step_completed(step, progress_data):
                await self._complete_step(user_id, step_id)

            logger.info(f"Updated progress for user {user_id}, step {step_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating step progress: {e}")
            return False

    async def complete_step(self, user_id: str, step_id: str) -> bool:
        """Manually complete a step."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return False

            step = self.onboarding_steps.get(step_id)
            if not step:
                return False

            # Check dependencies
            if not self._check_dependencies(progress, step):
                return False

            await self._complete_step(user_id, step_id)
            return True

        except Exception as e:
            logger.error(f"Error completing step: {e}")
            return False

    async def get_current_step(self, user_id: str) -> Optional[OnboardingStepData]:
        """Get the current step for a user."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return None

            return self.onboarding_steps.get(progress.current_step.value)

        except Exception as e:
            logger.error(f"Error getting current step for user {user_id}: {e}")
            return None

    async def get_next_step(self, user_id: str) -> Optional[OnboardingStepData]:
        """Get the next step for a user."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return None

            current_step = self.onboarding_steps.get(progress.current_step.value)
            if not current_step:
                return None

            # Find next step
            next_step = None
            for step in self.onboarding_steps.values():
                if step.order > current_step.order:
                    if not next_step or step.order < next_step.order:
                        next_step = step

            return next_step

        except Exception as e:
            logger.error(f"Error getting next step for user {user_id}: {e}")
            return None

    async def get_onboarding_analytics(self) -> OnboardingAnalytics:
        """Get analytics for the onboarding flow."""
        try:
            total_users = len(self.user_progress)
            completed_users = len(
                [
                    p
                    for p in self.user_progress.values()
                    if p.status == OnboardingStatus.COMPLETED
                ]
            )
            completion_rate = completed_users / total_users if total_users > 0 else 0

            # Calculate average completion time
            completion_times = []
            for progress in self.user_progress.values():
                if progress.completed_at and progress.started_at:
                    time_diff = (
                        progress.completed_at - progress.started_at
                    ).total_seconds() / 60
                    completion_times.append(time_diff)

            average_time = (
                sum(completion_times) / len(completion_times) if completion_times else 0
            )

            # Calculate dropoff points
            dropoff_points = await self._calculate_dropoff_points()

            # Calculate step completion rates
            step_completion_rates = await self._calculate_step_completion_rates()

            # Calculate engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics()

            return OnboardingAnalytics(
                total_users=total_users,
                completion_rate=completion_rate,
                average_time=average_time,
                dropoff_points=dropoff_points,
                step_completion_rates=step_completion_rates,
                engagement_metrics=engagement_metrics,
            )

        except Exception as e:
            logger.error(f"Error getting onboarding analytics: {e}")
            return OnboardingAnalytics(
                total_users=0,
                completion_rate=0.0,
                average_time=0.0,
                dropoff_points=[],
                step_completion_rates={},
                engagement_metrics={},
            )

    async def get_user_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized recommendations for a user."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return []

            recommendations = []

            # Based on current step
            if progress.current_step == OnboardingStep.PROFILE_SETUP:
                recommendations.append(
                    {
                        "type": "profile_completion",
                        "title": "Complete Your Profile",
                        "description": "Add more details to help others discover you",
                        "priority": "high",
                    }
                )

            elif progress.current_step == OnboardingStep.FIRST_PROJECT:
                recommendations.append(
                    {
                        "type": "project_creation",
                        "title": "Create Your First Project",
                        "description": "Start building and sharing your designs",
                        "priority": "high",
                    }
                )

            elif progress.current_step == OnboardingStep.CONNECTIONS:
                recommendations.append(
                    {
                        "type": "community_connection",
                        "title": "Connect with Creators",
                        "description": "Follow other designers and join groups",
                        "priority": "medium",
                    }
                )

            # Based on engagement score
            if progress.engagement_score < 50:
                recommendations.append(
                    {
                        "type": "engagement_boost",
                        "title": "Explore More Features",
                        "description": "Try different tools to get more out of Planarx",
                        "priority": "medium",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {e}")
            return []

    async def send_onboarding_notification(
        self, user_id: str, notification_type: str, data: Dict[str, Any] = None
    ) -> bool:
        """Send onboarding notification to user."""
        try:
            # In real implementation, this would send via email, push notification, etc.
            logger.info(f"Sent {notification_type} notification to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending onboarding notification: {e}")
            return False

    async def award_reward(
        self, user_id: str, reward_type: str, reward_data: Dict[str, Any]
    ) -> bool:
        """Award a reward to a user."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return False

            # Add reward to user's earned rewards
            reward_id = f"{reward_type}_{uuid.uuid4().hex[:8]}"
            progress.rewards_earned.append(reward_id)
            progress.updated_at = datetime.now()

            # Update engagement score
            progress.engagement_score = min(100, progress.engagement_score + 10)

            logger.info(f"Awarded {reward_type} reward to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error awarding reward: {e}")
            return False

    # Helper methods

    async def _complete_step(self, user_id: str, step_id: str) -> bool:
        """Complete a step and move to the next one."""
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return False

            step = self.onboarding_steps.get(step_id)
            if not step:
                return False

            # Award rewards
            if step.rewards:
                await self.award_reward(user_id, "step_completion", step.rewards)

            # Move to next step
            next_step = await self.get_next_step(user_id)
            if next_step:
                progress.current_step = next_step.step_type
            else:
                # Onboarding completed
                progress.status = OnboardingStatus.COMPLETED
                progress.completed_at = datetime.now()

            progress.updated_at = datetime.now()

            # Trigger engagement tools
            await self._trigger_engagement_tools(
                user_id, step.step_type, "step_completed"
            )

            logger.info(f"Completed step {step_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error completing step: {e}")
            return False

    def _is_step_completed(
        self, step: OnboardingStepData, progress_data: Dict[str, Any]
    ) -> bool:
        """Check if a step is completed based on criteria."""
        try:
            for criterion, required_value in step.completion_criteria.items():
                if (
                    criterion not in progress_data
                    or progress_data[criterion] != required_value
                ):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking step completion: {e}")
            return False

    def _check_dependencies(
        self, progress: UserOnboardingProgress, step: OnboardingStepData
    ) -> bool:
        """Check if step dependencies are met."""
        try:
            for dependency in step.dependencies:
                if dependency not in progress.step_progress:
                    return False
                # Check if dependency step is completed
                dependency_step = self.onboarding_steps.get(dependency)
                if dependency_step:
                    dependency_progress = progress.step_progress[dependency]
                    if not self._is_step_completed(
                        dependency_step, dependency_progress
                    ):
                        return False
            return True
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False

    async def _trigger_engagement_tools(
        self, user_id: str, step_type: OnboardingStep, trigger_type: str
    ) -> None:
        """Trigger engagement tools for a step."""
        try:
            for tool in self.engagement_tools:
                if tool.trigger_step == step_type:
                    # Check trigger condition
                    if self._check_trigger_condition(tool, trigger_type):
                        await self._execute_engagement_tool(user_id, tool)
        except Exception as e:
            logger.error(f"Error triggering engagement tools: {e}")

    def _check_trigger_condition(self, tool: EngagementTool, trigger_type: str) -> bool:
        """Check if engagement tool trigger condition is met."""
        try:
            condition = tool.trigger_condition
            if trigger_type in condition:
                return condition[trigger_type]
            return False
        except Exception as e:
            logger.error(f"Error checking trigger condition: {e}")
            return False

    async def _execute_engagement_tool(
        self, user_id: str, tool: EngagementTool
    ) -> bool:
        """Execute an engagement tool."""
        try:
            if tool.action_type == "notification":
                await self.send_onboarding_notification(
                    user_id, tool.name, tool.action_data
                )
            elif tool.action_type == "reward":
                await self.award_reward(user_id, tool.name, tool.action_data)
            elif tool.action_type == "guidance":
                # In real implementation, this would show guidance UI
                logger.info(f"Showing guidance: {tool.action_data}")

            return True
        except Exception as e:
            logger.error(f"Error executing engagement tool: {e}")
            return False

    async def _calculate_dropoff_points(self) -> List[Dict[str, Any]]:
        """Calculate dropoff points in onboarding."""
        try:
            dropoff_points = []

            for step in self.onboarding_steps.values():
                started_count = 0
                completed_count = 0

                for progress in self.user_progress.values():
                    if step.step_id in progress.step_progress:
                        started_count += 1
                        step_progress = progress.step_progress[step.step_id]
                        if self._is_step_completed(step, step_progress):
                            completed_count += 1

                if started_count > 0:
                    dropoff_rate = 1 - (completed_count / started_count)
                    dropoff_points.append(
                        {
                            "step": step.step_id,
                            "step_name": step.title,
                            "dropoff_rate": dropoff_rate,
                            "started_count": started_count,
                            "completed_count": completed_count,
                        }
                    )

            # Sort by dropoff rate (highest first)
            dropoff_points.sort(key=lambda x: x["dropoff_rate"], reverse=True)
            return dropoff_points

        except Exception as e:
            logger.error(f"Error calculating dropoff points: {e}")
            return []

    async def _calculate_step_completion_rates(self) -> Dict[str, float]:
        """Calculate completion rates for each step."""
        try:
            completion_rates = {}

            for step in self.onboarding_steps.values():
                total_users = len(self.user_progress)
                completed_users = 0

                for progress in self.user_progress.values():
                    if step.step_id in progress.step_progress:
                        step_progress = progress.step_progress[step.step_id]
                        if self._is_step_completed(step, step_progress):
                            completed_users += 1

                completion_rate = (
                    completed_users / total_users if total_users > 0 else 0
                )
                completion_rates[step.step_id] = completion_rate

            return completion_rates

        except Exception as e:
            logger.error(f"Error calculating step completion rates: {e}")
            return {}

    async def _calculate_engagement_metrics(self) -> Dict[str, Any]:
        """Calculate engagement metrics."""
        try:
            total_users = len(self.user_progress)
            if total_users == 0:
                return {}

            engagement_scores = [
                p.engagement_score for p in self.user_progress.values()
            ]
            avg_engagement = sum(engagement_scores) / len(engagement_scores)

            high_engagement_users = len(
                [p for p in self.user_progress.values() if p.engagement_score >= 70]
            )
            low_engagement_users = len(
                [p for p in self.user_progress.values() if p.engagement_score < 30]
            )

            return {
                "average_engagement_score": avg_engagement,
                "high_engagement_users": high_engagement_users,
                "low_engagement_users": low_engagement_users,
                "engagement_distribution": {
                    "high": high_engagement_users / total_users,
                    "medium": (
                        total_users - high_engagement_users - low_engagement_users
                    )
                    / total_users,
                    "low": low_engagement_users / total_users,
                },
            }

        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return {}


# Global onboarding flow service instance
onboarding_flow_service = OnboardingFlowService()
