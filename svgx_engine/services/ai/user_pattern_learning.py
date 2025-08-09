"""
User Pattern Learning Service for AI Integration

This module provides advanced user behavior tracking and pattern recognition including:
- User behavior tracking and analysis
- Pattern recognition and learning
- Personalized recommendations
- Usage analytics and insights
- Adaptive interface optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from svgx_engine.services.notifications import UnifiedNotificationSystem

logger = logging.getLogger(__name__)


class UserActionType(str, Enum):
    """Types of user actions"""
    LOGIN = "login"
    LOGOUT = "logout"
    NAVIGATION = "navigation"
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    VIEW = "view"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SHARE = "share"
    COMMENT = "comment"
    LIKE = "like"
    BOOKMARK = "bookmark"
    PRINT = "print"
    EMAIL = "email"
    NOTIFICATION = "notification"
    SETTINGS = "settings"
    HELP = "help"


class UserContext(str, Enum):
    """User context types"""
    CAD_DESIGN = "cad_design"
    PROJECT_MANAGEMENT = "project_management"
    DOCUMENT_VIEWING = "document_viewing"
    COLLABORATION = "collaboration"
    ADMINISTRATION = "administration"
    REPORTING = "reporting"
    SETTINGS = "settings"
    HELP_SUPPORT = "help_support"


class PatternType(str, Enum):
    """Types of user patterns"""
    FREQUENCY = "frequency"
    SEQUENCE = "sequence"
    TIMING = "timing"
    PREFERENCE = "preference"
    EFFICIENCY = "efficiency"
    COLLABORATION = "collaboration"
    ERROR_PATTERN = "error_pattern"
    FEATURE_USAGE = "feature_usage"


class UserAction(BaseModel):
    """Individual user action record"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    action_type: UserActionType = Field(..., description="Type of action")
    context: UserContext = Field(..., description="User context")
    resource_id: Optional[str] = Field(None, description="Resource being acted upon")
    resource_type: Optional[str] = Field(None, description="Type of resource")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: Optional[float] = Field(None, description="Action duration in seconds")
    success: bool = Field(default=True, description="Whether action was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    location: Optional[Tuple[float, float]] = Field(None, description="Geographic location")


class UserSession(BaseModel):
    """User session information"""
    id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    actions_count: int = Field(default=0)
    contexts_used: Set[UserContext] = Field(default_factory=set)
    resources_accessed: Set[str] = Field(default_factory=set)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[Tuple[float, float]] = None
    device_info: Dict[str, Any] = Field(default_factory=dict)


class UserPattern(BaseModel):
    """Identified user pattern"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User identifier")
    pattern_type: PatternType = Field(..., description="Type of pattern")
    context: UserContext = Field(..., description="Context where pattern occurs")
    pattern_data: Dict[str, Any] = Field(..., description="Pattern data")
    confidence: float = Field(..., description="Pattern confidence score (0-1)")
    frequency: int = Field(..., description="Pattern frequency")
    first_observed: datetime = Field(default_factory=datetime.utcnow)
    last_observed: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Whether pattern is still active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPreference(BaseModel):
    """User preference derived from patterns"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User identifier")
    preference_type: str = Field(..., description="Type of preference")
    preference_key: str = Field(..., description="Preference key")
    preference_value: Any = Field(..., description="Preference value")
    confidence: float = Field(..., description="Preference confidence score (0-1)")
    source_pattern: Optional[UUID] = Field(None, description="Source pattern ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRecommendation(BaseModel):
    """Personalized user recommendation"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User identifier")
    recommendation_type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Recommendation description")
    action_url: Optional[str] = Field(None, description="Action URL")
    priority: int = Field(default=1, description="Recommendation priority (1-5)")
    confidence: float = Field(..., description="Recommendation confidence score (0-1)")
    source_patterns: List[UUID] = Field(default_factory=list, description="Source pattern IDs")
    is_dismissed: bool = Field(default=False, description="Whether recommendation was dismissed")
    is_applied: bool = Field(default=False, description="Whether recommendation was applied")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Recommendation expiration")


class UserAnalytics(BaseModel):
    """User analytics summary"""
    user_id: str = Field(..., description="User identifier")
    total_sessions: int = Field(default=0)
    total_actions: int = Field(default=0)
    average_session_duration: float = Field(default=0.0)
    most_used_context: Optional[UserContext] = None
    most_used_features: List[str] = Field(default_factory=list)
    efficiency_score: float = Field(default=0.0)
    collaboration_score: float = Field(default=0.0)
    error_rate: float = Field(default=0.0)
    patterns_identified: int = Field(default=0)
    preferences_learned: int = Field(default=0)
    recommendations_generated: int = Field(default=0)
    last_activity: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPatternLearningService:
    """Service for learning and analyzing user patterns"""

    def __init__(self):
        pass
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
        self.actions: Dict[UUID, UserAction] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.patterns: Dict[UUID, UserPattern] = {}
        self.preferences: Dict[UUID, UserPreference] = {}
        self.recommendations: Dict[UUID, UserRecommendation] = {}
        self.analytics: Dict[str, UserAnalytics] = {}
        self.notification_system = UnifiedNotificationSystem()

        logger.info("UserPatternLearningService initialized")

    async def record_user_action(
        self,
        user_id: str,
        session_id: str,
        action_type: UserActionType,
        context: UserContext,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        duration: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Tuple[float, float]] = None
    ) -> UserAction:
        """Record a user action"""
        action = UserAction(
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,
            context=context,
            resource_id=resource_id,
            resource_type=resource_type,
            metadata=metadata or {},
            duration=duration,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location
        )

        self.actions[action.id] = action

        # Update session information
        await self._update_session(session_id, user_id, action)

        # Trigger pattern analysis
        await self._analyze_patterns(user_id)

        logger.info(f"Recorded user action: {action_type.value} for user {user_id}")
        return action

    async def start_user_session(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Tuple[float, float]] = None,
        device_info: Dict[str, Any] = None
    ) -> UserSession:
        """Start a new user session"""
        session = UserSession(
            id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            device_info=device_info or {}
        )

        self.sessions[session_id] = session
        logger.info(f"Started user session: {session_id} for user {user_id}")
        return session

    async def end_user_session(self, session_id: str) -> Optional[UserSession]:
        """End a user session"""
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return None

        session = self.sessions[session_id]
        session.end_time = datetime.utcnow()
        session.duration = (session.end_time - session.start_time).total_seconds()

        # Update analytics
        await self._update_user_analytics(session.user_id)

        logger.info(f"Ended user session: {session_id} (duration: {session.duration}s)")
        return session

    async def get_user_actions(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_type: Optional[UserActionType] = None,
        context: Optional[UserContext] = None
    ) -> List[UserAction]:
        """Get user actions with optional filters"""
        actions = [a for a in self.actions.values() if a.user_id == user_id]

        if start_date:
            actions = [a for a in actions if a.timestamp >= start_date]
        if end_date:
            actions = [a for a in actions if a.timestamp <= end_date]
        if action_type:
            actions = [a for a in actions if a.action_type == action_type]
        if context:
            actions = [a for a in actions if a.context == context]

        return sorted(actions, key=lambda x: x.timestamp)

    async def get_user_sessions(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UserSession]:
        """Get user sessions with optional filters"""
        sessions = [s for s in self.sessions.values() if s.user_id == user_id]

        if start_date:
            sessions = [s for s in sessions if s.start_time >= start_date]
        if end_date:
            sessions = [s for s in sessions if s.start_time <= end_date]

        return sorted(sessions, key=lambda x: x.start_time, reverse=True)

    async def get_user_patterns(
        self,
        user_id: str,
        pattern_type: Optional[PatternType] = None,
        context: Optional[UserContext] = None,
        active_only: bool = True
    ) -> List[UserPattern]:
        """Get user patterns with optional filters"""
        patterns = [p for p in self.patterns.values() if p.user_id == user_id]

        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        if context:
            patterns = [p for p in patterns if p.context == context]
        if active_only:
            patterns = [p for p in patterns if p.is_active]

        return sorted(patterns, key=lambda x: x.last_observed, reverse=True)

    async def get_user_preferences(
        self,
        user_id: str,
        preference_type: Optional[str] = None
    ) -> List[UserPreference]:
        """Get user preferences with optional filters"""
        preferences = [p for p in self.preferences.values() if p.user_id == user_id]

        if preference_type:
            preferences = [p for p in preferences if p.preference_type == preference_type]

        return sorted(preferences, key=lambda x: x.confidence, reverse=True)

    async def get_user_recommendations(
        self,
        user_id: str,
        recommendation_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[UserRecommendation]:
        """Get user recommendations with optional filters"""
        recommendations = [r for r in self.recommendations.values() if r.user_id == user_id]

        if recommendation_type:
            recommendations = [r for r in recommendations if r.recommendation_type == recommendation_type]
        if active_only:
            recommendations = [r for r in recommendations if not r.is_dismissed and not r.is_applied]
            # Filter out expired recommendations
            current_time = datetime.utcnow()
            recommendations = [r for r in recommendations if not r.expires_at or r.expires_at > current_time]

        return sorted(recommendations, key=lambda x: (x.priority, x.confidence), reverse=True)

    async def get_user_analytics(self, user_id: str) -> Optional[UserAnalytics]:
        """Get user analytics"""
        return self.analytics.get(user_id)

    async def _update_session(self, session_id: str, user_id: str, action: UserAction):
        """Update session information with new action"""
        if session_id not in self.sessions:
            # Create session if it doesn't exist'
            await self.start_user_session(user_id, session_id)

        session = self.sessions[session_id]
        session.actions_count += 1
        session.contexts_used.add(action.context)

        if action.resource_id:
            session.resources_accessed.add(action.resource_id)

        if not session.ip_address and action.ip_address:
            session.ip_address = action.ip_address
        if not session.user_agent and action.user_agent:
            session.user_agent = action.user_agent
        if not session.location and action.location:
            session.location = action.location

    async def _analyze_patterns(self, user_id: str):
        """Analyze user patterns based on recent actions"""
        # Get recent actions for the user
        recent_actions = await self.get_user_actions(
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        if len(recent_actions) < 10:
            return  # Need more data for pattern analysis

        # Analyze frequency patterns
        await self._analyze_frequency_patterns(user_id, recent_actions)

        # Analyze sequence patterns
        await self._analyze_sequence_patterns(user_id, recent_actions)

        # Analyze timing patterns
        await self._analyze_timing_patterns(user_id, recent_actions)

        # Analyze preference patterns
        await self._analyze_preference_patterns(user_id, recent_actions)

        # Generate recommendations based on patterns
        await self._generate_recommendations(user_id)

    async def _analyze_frequency_patterns(self, user_id: str, actions: List[UserAction]):
        """Analyze frequency-based patterns"""
        # Group actions by type and context
        action_counts = {}
        context_counts = {}

        for action in actions:
            key = (action.action_type, action.context)
            action_counts[key] = action_counts.get(key, 0) + 1
            context_counts[action.context] = context_counts.get(action.context, 0) + 1

        # Identify high-frequency patterns
        for (action_type, context), count in action_counts.items():
            if count >= 5:  # Threshold for pattern recognition
                pattern = UserPattern(
                    user_id=user_id,
                    pattern_type=PatternType.FREQUENCY,
                    context=context,
                    pattern_data={
                        "action_type": action_type.value,
                        "frequency": count,
                        "time_period": "30_days"
                    },
                    confidence=min(count / 20.0, 1.0),  # Normalize confidence
                    frequency=count
                )

                # Update existing pattern or create new one
                existing_pattern = await self._find_existing_pattern(
                    user_id, PatternType.FREQUENCY, context, action_type.value
                )

                if existing_pattern:
                    existing_pattern.pattern_data["frequency"] = count
                    existing_pattern.confidence = pattern.confidence
                    existing_pattern.frequency = count
                    existing_pattern.last_observed = datetime.utcnow()
                else:
                    self.patterns[pattern.id] = pattern

    async def _analyze_sequence_patterns(self, user_id: str, actions: List[UserAction]):
        """Analyze sequence-based patterns"""
        # Look for common action sequences
        sequences = {}

        for i in range(len(actions) - 1):
            seq = (actions[i].action_type, actions[i + 1].action_type)
            sequences[seq] = sequences.get(seq, 0) + 1

        # Identify common sequences
        for (action1, action2), count in sequences.items():
            if count >= 3:  # Threshold for sequence pattern
                pattern = UserPattern(
                    user_id=user_id,
                    pattern_type=PatternType.SEQUENCE,
                    context=UserContext.CAD_DESIGN,  # Default context
                    pattern_data={
                        "sequence": [action1.value, action2.value],
                        "frequency": count,
                        "time_period": "30_days"
                    },
                    confidence=min(count / 10.0, 1.0),
                    frequency=count
                )

                self.patterns[pattern.id] = pattern

    async def _analyze_timing_patterns(self, user_id: str, actions: List[UserAction]):
        """Analyze timing-based patterns"""
        # Group actions by hour of day
        hourly_counts = {}

        for action in actions:
            hour = action.timestamp.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        # Find peak usage hours
        if hourly_counts:
            peak_hour = max(hourly_counts, key=hourly_counts.get)
            peak_count = hourly_counts[peak_hour]

            if peak_count >= 5:  # Threshold for timing pattern
                pattern = UserPattern(
                    user_id=user_id,
                    pattern_type=PatternType.TIMING,
                    context=UserContext.CAD_DESIGN,  # Default context
                    pattern_data={
                        "peak_hour": peak_hour,
                        "peak_count": peak_count,
                        "hourly_distribution": hourly_counts
                    },
                    confidence=min(peak_count / 15.0, 1.0),
                    frequency=peak_count
                )

                self.patterns[pattern.id] = pattern

    async def _analyze_preference_patterns(self, user_id: str, actions: List[UserAction]):
        """Analyze preference-based patterns"""
        # Analyze resource preferences
        resource_counts = {}
        context_preferences = {}

        for action in actions:
            if action.resource_id:
                resource_counts[action.resource_id] = resource_counts.get(action.resource_id, 0) + 1

            context_preferences[action.context] = context_preferences.get(action.context, 0) + 1

        # Create preferences based on usage patterns
        for resource_id, count in resource_counts.items():
            if count >= 3:  # Threshold for preference
                preference = UserPreference(
                    user_id=user_id,
                    preference_type="resource_usage",
                    preference_key=resource_id,
                    preference_value=count,
                    confidence=min(count / 10.0, 1.0)
                self.preferences[preference.id] = preference

        # Context preferences
        if context_preferences:
            preferred_context = max(context_preferences, key=context_preferences.get)
            preference = UserPreference(
                user_id=user_id,
                preference_type="context_preference",
                preference_key="preferred_context",
                preference_value=preferred_context.value,
                confidence=min(context_preferences[preferred_context] / 20.0, 1.0)
            self.preferences[preference.id] = preference

    async def _find_existing_pattern(
        self,
        user_id: str,
        pattern_type: PatternType,
        context: UserContext,
        pattern_key: str
    ) -> Optional[UserPattern]:
        """Find existing pattern for user"""
        for pattern in self.patterns.values():
            if (pattern.user_id == user_id and
                pattern.pattern_type == pattern_type and
                pattern.context == context and
                pattern.pattern_data.get("action_type") == pattern_key):
                return pattern
        return None

    async def _generate_recommendations(self, user_id: str):
        """Generate personalized recommendations based on patterns"""
        patterns = await self.get_user_patterns(user_id, active_only=True)
        preferences = await self.get_user_preferences(user_id)

        recommendations = []

        # Generate recommendations based on frequency patterns
        for pattern in patterns:
            if pattern.pattern_type == PatternType.FREQUENCY:
                if pattern.pattern_data.get("action_type") == UserActionType.CREATE.value:
                    recommendation = UserRecommendation(
                        user_id=user_id,
                        recommendation_type="feature_usage",
                        title="Create Templates",
                        description="You frequently create new items. Consider creating templates to speed up your workflow.",
                        action_url="/templates/create",
                        priority=3,
                        confidence=pattern.confidence,
                        source_patterns=[pattern.id]
                    )
                    recommendations.append(recommendation)

                elif pattern.pattern_data.get("action_type") == UserActionType.EXPORT.value:
                    recommendation = UserRecommendation(
                        user_id=user_id,
                        recommendation_type="workflow_optimization",
                        title="Batch Export",
                        description="You export frequently. Consider using batch export features to save time.",
                        action_url="/export/batch",
                        priority=2,
                        confidence=pattern.confidence,
                        source_patterns=[pattern.id]
                    )
                    recommendations.append(recommendation)

        # Generate recommendations based on timing patterns
        for pattern in patterns:
            if pattern.pattern_type == PatternType.TIMING:
                peak_hour = pattern.pattern_data.get("peak_hour")
                if peak_hour is not None:
                    recommendation = UserRecommendation(
                        user_id=user_id,
                        recommendation_type="schedule_optimization",
                        title="Peak Usage Time",
                        description=f"You're most active at {peak_hour}:00. Consider scheduling important tasks during this time.",'
                        priority=1,
                        confidence=pattern.confidence,
                        source_patterns=[pattern.id]
                    )
                    recommendations.append(recommendation)

        # Generate recommendations based on preferences
        for preference in preferences:
            if preference.preference_type == "context_preference":
                if preference.preference_value == UserContext.CAD_DESIGN.value:
                    recommendation = UserRecommendation(
                        user_id=user_id,
                        recommendation_type="feature_discovery",
                        title="Advanced CAD Features",
                        description="You use CAD design frequently. Explore advanced features like parametric modeling and constraints.",
                        action_url="/cad/advanced-features",
                        priority=4,
                        confidence=preference.confidence,
                        source_patterns=[]
                    )
                    recommendations.append(recommendation)

        # Add recommendations to storage
        for recommendation in recommendations:
            self.recommendations[recommendation.id] = recommendation

    async def _update_user_analytics(self, user_id: str):
        """Update user analytics based on recent activity"""
        actions = await self.get_user_actions(user_id)
        sessions = await self.get_user_sessions(user_id)
        patterns = await self.get_user_patterns(user_id)
        preferences = await self.get_user_preferences(user_id)
        recommendations = await self.get_user_recommendations(user_id)

        if not actions:
            return

        # Calculate analytics
        total_actions = len(actions)
        total_sessions = len(sessions)

        # Calculate average session duration
        session_durations = [s.duration for s in sessions if s.duration]
        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0.0

        # Find most used context
        context_counts = {}
        for action in actions:
            context_counts[action.context] = context_counts.get(action.context, 0) + 1

        most_used_context = max(context_counts, key=context_counts.get) if context_counts else None

        # Find most used features (action types)
        action_type_counts = {}
        for action in actions:
            action_type_counts[action.action_type] = action_type_counts.get(action.action_type, 0) + 1

        most_used_features = sorted(action_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_used_features = [feature[0].value for feature in most_used_features]

        # Calculate efficiency score (successful actions / total actions)
        successful_actions = sum(1 for action in actions if action.success)
        efficiency_score = successful_actions / total_actions if total_actions > 0 else 0.0

        # Calculate collaboration score (shared resources, comments, etc.)
        collaboration_actions = sum(1 for action in actions if action.action_type in [
            UserActionType.SHARE, UserActionType.COMMENT, UserActionType.LIKE
        ])
        collaboration_score = collaboration_actions / total_actions if total_actions > 0 else 0.0

        # Calculate error rate
        failed_actions = sum(1 for action in actions if not action.success)
        error_rate = failed_actions / total_actions if total_actions > 0 else 0.0

        # Get last activity
        last_activity = max(action.timestamp for action in actions) if actions else None

        analytics = UserAnalytics(
            user_id=user_id,
            total_sessions=total_sessions,
            total_actions=total_actions,
            average_session_duration=avg_session_duration,
            most_used_context=most_used_context,
            most_used_features=most_used_features,
            efficiency_score=efficiency_score,
            collaboration_score=collaboration_score,
            error_rate=error_rate,
            patterns_identified=len(patterns),
            preferences_learned=len(preferences),
            recommendations_generated=len(recommendations),
            last_activity=last_activity
        )

        self.analytics[user_id] = analytics

    async def dismiss_recommendation(self, recommendation_id: UUID) -> bool:
        """Dismiss a user recommendation"""
        if recommendation_id not in self.recommendations:
            return False

        recommendation = self.recommendations[recommendation_id]
        recommendation.is_dismissed = True

        logger.info(f"Dismissed recommendation: {recommendation_id}")
        return True

    async def apply_recommendation(self, recommendation_id: UUID) -> bool:
        """Mark a recommendation as applied"""
        if recommendation_id not in self.recommendations:
            return False

        recommendation = self.recommendations[recommendation_id]
        recommendation.is_applied = True

        logger.info(f"Applied recommendation: {recommendation_id}")
        return True

    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user insights"""
        analytics = await self.get_user_analytics(user_id)
        patterns = await self.get_user_patterns(user_id)
        preferences = await self.get_user_preferences(user_id)
        recommendations = await self.get_user_recommendations(user_id)

        insights = {
            "analytics": analytics.dict() if analytics else None,
            "patterns": [p.dict() for p in patterns],
            "preferences": [p.dict() for p in preferences],
            "recommendations": [r.dict() for r in recommendations],
            "summary": {
                "total_patterns": len(patterns),
                "total_preferences": len(preferences),
                "active_recommendations": len([r for r in recommendations if not r.is_dismissed and not r.is_applied]),
                "efficiency_score": analytics.efficiency_score if analytics else 0.0,
                "collaboration_score": analytics.collaboration_score if analytics else 0.0
            }
        }

        return insights
