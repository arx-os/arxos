"""
Reputation Scoring Engine
Gamified scoring system for user contributions with anti-abuse validation
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ContributionType(Enum):
    """Types of contributions that earn reputation points"""
    DRAFT_SUBMITTED = "draft_submitted"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_REJECTED = "draft_rejected"
    COMMENT_ADDED = "comment_added"
    COMMENT_HELPFUL = "comment_helpful"
    COMMENT_REPLY = "comment_reply"
    THREAD_RESOLVED = "thread_resolved"
    THREAD_ASSIGNED = "thread_assigned"
    ANNOTATION_ADDED = "annotation_added"
    VOTE_CAST = "vote_cast"
    VOTE_RECEIVED = "vote_received"
    MENTION_RECEIVED = "mention_received"
    COLLABORATION_SESSION = "collaboration_session"
    MILESTONE_REACHED = "milestone_reached"
    FUNDING_CONTRIBUTION = "funding_contribution"
    MODERATION_ACTION = "moderation_action"
    COMMUNITY_HELP = "community_help"
    DOCUMENTATION_CONTRIBUTION = "documentation_contribution"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class ReputationTier(Enum):
    """User reputation tiers with associated privileges"""
    NEWCOMER = "newcomer"  # 0-99 points
    CONTRIBUTOR = "contributor"  # 100-499 points
    REGULAR = "regular"  # 500-999 points
    EXPERT = "expert"  # 1000-2499 points
    MASTER = "master"  # 2500-4999 points
    LEGEND = "legend"  # 5000+ points


@dataclass
class ContributionEvent:
    """Individual contribution event that earns reputation points"""
    id: str
    user_id: str
    contribution_type: ContributionType
    points_earned: int
    timestamp: datetime
    metadata: Dict
    validated: bool
    abuse_score: float

    def __post_init__(self):
        pass
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
        if self.abuse_score is None:
            self.abuse_score = 0.0


@dataclass
class UserReputation:
    """User's reputation profile"""
    user_id: str
    total_points: int
    current_tier: ReputationTier
    tier_points: int  # Points within current tier
    contribution_count: int
    last_activity: datetime
    reputation_history: List[Dict]
    badges: List[str]
    privileges: List[str]

    def __post_init__(self):
        if self.reputation_history is None:
            self.reputation_history = []
        if self.badges is None:
            self.badges = []
        if self.privileges is None:
            self.privileges = []


@dataclass
class AbuseDetection:
    """Abuse detection and prevention system"""
    user_id: str
    suspicious_events: List[Dict]
    abuse_score: float
    warning_count: int
    last_warning: datetime
    is_flagged: bool
    review_required: bool

    def __post_init__(self):
        if self.suspicious_events is None:
            self.suspicious_events = []
        if self.abuse_score is None:
            self.abuse_score = 0.0


class ReputationScoringEngine:
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
    """Main reputation scoring engine with anti-abuse protection"""

    def __init__(self):
        self.user_reputations: Dict[str, UserReputation] = {}
        self.contribution_events: Dict[str, ContributionEvent] = {}
        self.abuse_detection: Dict[str, AbuseDetection] = {}
        self.scoring_rules: Dict[ContributionType, Dict] = {}
        self.tier_thresholds: Dict[ReputationTier, int] = {}
        self.privilege_rules: Dict[ReputationTier, List[str]] = {}

        self.logger = logging.getLogger(__name__)

        self._initialize_scoring_rules()
        self._initialize_tier_thresholds()
        self._initialize_privilege_rules()

    def _initialize_scoring_rules(self):
        """Initialize scoring rules for different contribution types"""

        self.scoring_rules = {
            ContributionType.DRAFT_SUBMITTED: {
                "base_points": 10,
                "multiplier": 1.0,
                "daily_limit": 50,
                "quality_bonus": True
            },
            ContributionType.DRAFT_APPROVED: {
                "base_points": 50,
                "multiplier": 1.0,
                "daily_limit": 200,
                "quality_bonus": True
            },
            ContributionType.DRAFT_REJECTED: {
                "base_points": -5,
                "multiplier": 1.0,
                "daily_limit": 20,
                "quality_bonus": False
            },
            ContributionType.COMMENT_ADDED: {
                "base_points": 2,
                "multiplier": 1.0,
                "daily_limit": 100,
                "quality_bonus": True
            },
            ContributionType.COMMENT_HELPFUL: {
                "base_points": 5,
                "multiplier": 1.0,
                "daily_limit": 50,
                "quality_bonus": True
            },
            ContributionType.COMMENT_REPLY: {
                "base_points": 3,
                "multiplier": 1.0,
                "daily_limit": 75,
                "quality_bonus": True
            },
            ContributionType.THREAD_RESOLVED: {
                "base_points": 15,
                "multiplier": 1.0,
                "daily_limit": 30,
                "quality_bonus": True
            },
            ContributionType.THREAD_ASSIGNED: {
                "base_points": 5,
                "multiplier": 1.0,
                "daily_limit": 20,
                "quality_bonus": False
            },
            ContributionType.ANNOTATION_ADDED: {
                "base_points": 3,
                "multiplier": 1.0,
                "daily_limit": 50,
                "quality_bonus": True
            },
            ContributionType.VOTE_CAST: {
                "base_points": 1,
                "multiplier": 1.0,
                "daily_limit": 200,
                "quality_bonus": False
            },
            ContributionType.VOTE_RECEIVED: {
                "base_points": 2,
                "multiplier": 1.0,
                "daily_limit": 100,
                "quality_bonus": False
            },
            ContributionType.MENTION_RECEIVED: {
                "base_points": 1,
                "multiplier": 1.0,
                "daily_limit": 50,
                "quality_bonus": False
            },
            ContributionType.COLLABORATION_SESSION: {
                "base_points": 5,
                "multiplier": 1.0,
                "daily_limit": 40,
                "quality_bonus": True
            },
            ContributionType.MILESTONE_REACHED: {
                "base_points": 25,
                "multiplier": 1.0,
                "daily_limit": 10,
                "quality_bonus": True
            },
            ContributionType.FUNDING_CONTRIBUTION: {
                "base_points": 10,
                "multiplier": 1.0,
                "daily_limit": 100,
                "quality_bonus": False
            },
            ContributionType.MODERATION_ACTION: {
                "base_points": 20,
                "multiplier": 1.0,
                "daily_limit": 20,
                "quality_bonus": True
            },
            ContributionType.COMMUNITY_HELP: {
                "base_points": 15,
                "multiplier": 1.0,
                "daily_limit": 30,
                "quality_bonus": True
            },
            ContributionType.DOCUMENTATION_CONTRIBUTION: {
                "base_points": 20,
                "multiplier": 1.0,
                "daily_limit": 25,
                "quality_bonus": True
            },
            ContributionType.BUG_REPORT: {
                "base_points": 5,
                "multiplier": 1.0,
                "daily_limit": 50,
                "quality_bonus": True
            },
            ContributionType.FEATURE_REQUEST: {
                "base_points": 8,
                "multiplier": 1.0,
                "daily_limit": 40,
                "quality_bonus": True
            }
        }

    def _initialize_tier_thresholds(self):
        """Initialize reputation tier thresholds"""

        self.tier_thresholds = {
            ReputationTier.NEWCOMER: 0,
            ReputationTier.CONTRIBUTOR: 100,
            ReputationTier.REGULAR: 500,
            ReputationTier.EXPERT: 1000,
            ReputationTier.MASTER: 2500,
            ReputationTier.LEGEND: 5000
        }

    def _initialize_privilege_rules(self):
        """Initialize privileges for each reputation tier"""

        self.privilege_rules = {
            ReputationTier.NEWCOMER: [
                "basic_comment",
                "basic_vote",
                "view_drafts"
            ],
            ReputationTier.CONTRIBUTOR: [
                "submit_drafts",
                "create_threads",
                "add_annotations",
                "receive_mentions"
            ],
            ReputationTier.REGULAR: [
                "moderate_comments",
                "assign_threads",
                "priority_support",
                "collaboration_access"
            ],
            ReputationTier.EXPERT: [
                "approve_drafts",
                "moderate_content",
                "funding_priority",
                "feature_requests"
            ],
            ReputationTier.MASTER: [
                "admin_access",
                "grant_approval",
                "system_config",
                "mentor_others"
            ],
            ReputationTier.LEGEND: [
                "all_privileges",
                "platform_influence",
                "exclusive_access",
                "founder_status"
            ]
        }

    def record_contribution(
        self,
        user_id: str,
        contribution_type: ContributionType,
        metadata: Dict = None,
        quality_score: float = 1.0
    ) -> Optional[ContributionEvent]:
        """Record a contribution and award reputation points"""

        try:
            # Validate contribution
            if not self._validate_contribution(user_id, contribution_type):
                self.logger.warning(f"Invalid contribution from user {user_id}: {contribution_type}")
                return None

            # Check daily limits
            if self._exceeds_daily_limit(user_id, contribution_type):
                self.logger.warning(f"Daily limit exceeded for user {user_id}: {contribution_type}")
                return None

            # Calculate points
            points = self._calculate_points(contribution_type, quality_score)

            # Check for abuse
            abuse_score = self._detect_abuse(user_id, contribution_type, points)

            # Create contribution event
            event = ContributionEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                contribution_type=contribution_type,
                points_earned=points,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                validated=abuse_score < 0.7,  # Threshold for validation
                abuse_score=abuse_score
            )

            # Store event
            self.contribution_events[event.id] = event

            # Update user reputation
            self._update_user_reputation(user_id, event)

            # Log contribution
            self.logger.info(f"Contribution recorded: {user_id} earned {points} points for {contribution_type}")

            return event

        except Exception as e:
            self.logger.error(f"Error recording contribution: {e}")
            return None

    def _validate_contribution(self, user_id: str, contribution_type: ContributionType) -> bool:
        """Validate if a contribution is legitimate"""

        # Check if user exists and is not banned
        if user_id not in self.user_reputations:
            # Create new user reputation
            self.user_reputations[user_id] = UserReputation(
                user_id=user_id,
                total_points=0,
                current_tier=ReputationTier.NEWCOMER,
                tier_points=0,
                contribution_count=0,
                last_activity=datetime.utcnow(),
                reputation_history=[],
                badges=[],
                privileges=[]
            )

        # Check abuse detection
        if user_id in self.abuse_detection:
            abuse = self.abuse_detection[user_id]
            if abuse.is_flagged or abuse.abuse_score > 0.8:
                return False

        # Check contribution type validity
        if contribution_type not in self.scoring_rules:
            return False

        return True

    def _exceeds_daily_limit(self, user_id: str, contribution_type: ContributionType) -> bool:
        """Check if user has exceeded daily limit for contribution type"""

        today = datetime.utcnow().date()
        daily_limit = self.scoring_rules[contribution_type]["daily_limit"]

        # Count today's contributions of this type'
        today_contributions = 0
        for event in self.contribution_events.values():
            if (event.user_id == user_id and
                event.contribution_type == contribution_type and
                event.timestamp.date() == today):
                today_contributions += 1

        return today_contributions >= daily_limit

    def _calculate_points(self, contribution_type: ContributionType, quality_score: float) -> int:
        """Calculate points for a contribution based on type and quality"""

        rules = self.scoring_rules[contribution_type]
        base_points = rules["base_points"]
        multiplier = rules["multiplier"]

        # Apply quality bonus if applicable
        if rules["quality_bonus"] and quality_score > 0.8:
            multiplier *= 1.2  # 20% bonus for high quality

        points = int(base_points * multiplier * quality_score)

        # Ensure minimum points for positive contributions
        if base_points > 0 and points < 1:
            points = 1

        return points

    def _detect_abuse(self, user_id: str, contribution_type: ContributionType, points: int) -> float:
        """Detect potential abuse patterns"""

        abuse_score = 0.0

        # Initialize abuse detection if needed
        if user_id not in self.abuse_detection:
            self.abuse_detection[user_id] = AbuseDetection(
                user_id=user_id,
                suspicious_events=[],
                abuse_score=0.0,
                warning_count=0,
                last_warning=datetime.utcnow(),
                is_flagged=False,
                review_required=False
            )

        abuse = self.abuse_detection[user_id]

        # Check for rapid-fire contributions
        recent_events = [
            event for event in self.contribution_events.values()
            if (event.user_id == user_id and
                event.timestamp > datetime.utcnow() - timedelta(minutes=5)
        ]

        if len(recent_events) > 10:
            abuse_score += 0.3

        # Check for suspicious point patterns
        if points > 100 and abuse.abuse_score > 0.5:
            abuse_score += 0.2

        # Check for repetitive contributions
        today_events = [
            event for event in self.contribution_events.values()
            if (event.user_id == user_id and
                event.contribution_type == contribution_type and
                event.timestamp.date() == datetime.utcnow().date()
        ]

        if len(today_events) > 20:
            abuse_score += 0.4

        # Update abuse detection
        abuse.abuse_score = min(1.0, abuse.abuse_score + abuse_score)
        abuse.suspicious_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "contribution_type": contribution_type.value,
            "points": points,
            "abuse_score": abuse_score
        })

        # Flag for review if abuse score is high
        if abuse.abuse_score > 0.7:
            abuse.is_flagged = True
            abuse.review_required = True

        return abuse.abuse_score

    def _update_user_reputation(self, user_id: str, event: ContributionEvent):
        """Update user's reputation based on contribution event"""

        reputation = self.user_reputations[user_id]

        # Add points
        reputation.total_points += event.points_earned
        reputation.contribution_count += 1
        reputation.last_activity = datetime.utcnow()

        # Check for tier upgrade
        new_tier = self._calculate_tier(reputation.total_points)
        if new_tier != reputation.current_tier:
            old_tier = reputation.current_tier
            reputation.current_tier = new_tier
            reputation.tier_points = reputation.total_points - self.tier_thresholds[new_tier]

            # Add to history
            reputation.reputation_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "old_tier": old_tier.value,
                "new_tier": new_tier.value,
                "total_points": reputation.total_points,
                "event_type": "tier_upgrade"
            })

            # Update privileges
            reputation.privileges = self.privilege_rules[new_tier]

            self.logger.info(f"User {user_id} upgraded from {old_tier} to {new_tier}")
        else:
            reputation.tier_points = reputation.total_points - self.tier_thresholds[reputation.current_tier]

        # Add event to history
        reputation.reputation_history.append({
            "timestamp": event.timestamp.isoformat(),
            "contribution_type": event.contribution_type.value,
            "points_earned": event.points_earned,
            "total_points": reputation.total_points,
            "event_type": "contribution"
        })

    def _calculate_tier(self, total_points: int) -> ReputationTier:
        """Calculate reputation tier based on total points"""

        for tier in reversed(list(ReputationTier)):
            if total_points >= self.tier_thresholds[tier]:
                return tier

        return ReputationTier.NEWCOMER

    def get_user_reputation(self, user_id: str) -> Optional[UserReputation]:
        """Get user's reputation profile"""

        if user_id not in self.user_reputations:
            return None

        return self.user_reputations[user_id]

    def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        """Get top users by reputation points"""

        users = list(self.user_reputations.values()
        users.sort(key=lambda u: u.total_points, reverse=True)

        leaderboard = []
        for i, user in enumerate(users[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "user_id": user.user_id,
                "total_points": user.total_points,
                "current_tier": user.current_tier.value,
                "contribution_count": user.contribution_count,
                "last_activity": user.last_activity.isoformat()
            })

        return leaderboard

    def get_user_contributions(
        self,
        user_id: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[ContributionEvent]:
        """Get user's contribution history"""

        contributions = []

        for event in self.contribution_events.values():
            if event.user_id == user_id:
                if start_date and event.timestamp < start_date:
                    continue
                if end_date and event.timestamp > end_date:
                    continue
                contributions.append(event)

        # Sort by timestamp (newest first)
        contributions.sort(key=lambda e: e.timestamp, reverse=True)
        return contributions

    def get_contribution_stats(self, user_id: str) -> Dict:
        """Get detailed contribution statistics for a user"""

        if user_id not in self.user_reputations:
            return {}

        reputation = self.user_reputations[user_id]
        contributions = self.get_user_contributions(user_id)

        # Count contributions by type
        contribution_counts = Counter()
        for event in contributions:
            contribution_counts[event.contribution_type] += 1

        # Calculate recent activity
        recent_activity = len([
            event for event in contributions
            if event.timestamp > datetime.utcnow() - timedelta(days=7)
        ])

        # Calculate average points per contribution
        avg_points = reputation.total_points / max(reputation.contribution_count, 1)

        return {
            "user_id": user_id,
            "total_points": reputation.total_points,
            "current_tier": reputation.current_tier.value,
            "tier_points": reputation.tier_points,
            "contribution_count": reputation.contribution_count,
            "recent_activity": recent_activity,
            "average_points": round(avg_points, 2),
            "contribution_breakdown": dict(contribution_counts),
            "privileges": reputation.privileges,
            "badges": reputation.badges,
            "last_activity": reputation.last_activity.isoformat()
        }

    def flag_user_for_review(self, user_id: str, reason: str):
        """Flag a user for manual review"""

        if user_id in self.abuse_detection:
            abuse = self.abuse_detection[user_id]
            abuse.review_required = True
            abuse.warning_count += 1
            abuse.last_warning = datetime.utcnow()

            abuse.suspicious_events.append({
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason,
                "action": "manual_flag"
            })

            self.logger.warning(f"User {user_id} flagged for review: {reason}")

    def clear_abuse_flag(self, user_id: str, moderator_id: str):
        """Clear abuse flag for a user"""

        if user_id in self.abuse_detection:
            abuse = self.abuse_detection[user_id]
            abuse.is_flagged = False
            abuse.review_required = False
            abuse.abuse_score = max(0.0, abuse.abuse_score - 0.3)

            abuse.suspicious_events.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "flag_cleared",
                "moderator_id": moderator_id
            })

            self.logger.info(f"Abuse flag cleared for user {user_id} by moderator {moderator_id}")

    def get_abuse_reports(self) -> List[Dict]:
        """Get all users flagged for abuse review"""

        reports = []

        for user_id, abuse in self.abuse_detection.items():
            if abuse.review_required:
                reputation = self.user_reputations.get(user_id)

                reports.append({
                    "user_id": user_id,
                    "abuse_score": abuse.abuse_score,
                    "warning_count": abuse.warning_count,
                    "last_warning": abuse.last_warning.isoformat(),
                    "suspicious_events": abuse.suspicious_events,
                    "user_reputation": reputation.total_points if reputation else 0,
                    "user_tier": reputation.current_tier.value if reputation else "newcomer"
                })

        # Sort by abuse score (highest first)
        reports.sort(key=lambda r: r["abuse_score"], reverse=True)
        return reports


# Global reputation engine instance
reputation_engine = ReputationScoringEngine()
