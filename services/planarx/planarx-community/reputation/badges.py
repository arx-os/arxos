"""
Badge System
Assigns badges to users based on achievements and contribution patterns
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BadgeType(Enum):
    """Types of badges that can be earned"""
    CONTRIBUTOR = "contributor"
    EXPERT = "expert"
    MASTER = "master"
    LEGEND = "legend"
    FIRST_DRAFT = "first_draft"
    DRAFT_MASTER = "draft_master"
    COMMENT_KING = "comment_king"
    HELPER = "helper"
    MODERATOR = "moderator"
    COLLABORATOR = "collaborator"
    FUNDER = "funder"
    MILESTONE_CHAMPION = "milestone_champion"
    QUALITY_CONTROLLER = "quality_controller"
    COMMUNITY_BUILDER = "community_builder"
    DOCUMENTATION_HERO = "documentation_hero"
    BUG_HUNTER = "bug_hunter"
    FEATURE_CRAFTER = "feature_crafter"
    VOTING_CHAMPION = "voting_champion"
    MENTION_MAGNET = "mention_magnet"
    SESSION_LEADER = "session_leader"
    RESOLUTION_EXPERT = "resolution_expert"
    ANNOTATION_ARTIST = "annotation_artist"
    CONSISTENCY_KING = "consistency_king"
    INNOVATOR = "innovator"


class BadgeRarity(Enum):
    """Badge rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Badge:
    """Individual badge definition"""
    id: str
    name: str
    description: str
    badge_type: BadgeType
    rarity: BadgeRarity
    icon: str
    color: str
    criteria: Dict
    points_reward: int
    created_at: datetime
    
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
        if self.criteria is None:
            self.criteria = {}


@dataclass
class UserBadge:
    """User's earned badge"""
    id: str
    user_id: str
    badge_id: str
    earned_at: datetime
    progress: float  # 0.0 to 1.0 for progress tracking
    metadata: Dict
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BadgeSystem:
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
    """Badge assignment and tracking system"""
    
    def __init__(self):
        self.badges: Dict[str, Badge] = {}
        self.user_badges: Dict[str, List[UserBadge]] = {}
        self.badge_progress: Dict[str, Dict[str, float]] = {}  # user_id -> badge_id -> progress
        
        self.logger = logging.getLogger(__name__)
        
        self._initialize_badges()
    
    def _initialize_badges(self):
        """Initialize all available badges"""
        
        self.badges = {
            "contributor": Badge(
                id="contributor",
                name="Contributor",
                description="Made your first contribution to the community",
                badge_type=BadgeType.CONTRIBUTOR,
                rarity=BadgeRarity.COMMON,
                icon="🌟",
                color="#4CAF50",
                criteria={"total_contributions": 1},
                points_reward=10,
                created_at=datetime.utcnow()
            ),
            
            "expert": Badge(
                id="expert",
                name="Expert",
                description="Reached expert level through consistent contributions",
                badge_type=BadgeType.EXPERT,
                rarity=BadgeRarity.UNCOMMON,
                icon="⭐",
                color="#2196F3",
                criteria={"reputation_tier": "expert"},
                points_reward=50,
                created_at=datetime.utcnow()
            ),
            
            "master": Badge(
                id="master",
                name="Master",
                description="Achieved master status in the community",
                badge_type=BadgeType.MASTER,
                rarity=BadgeRarity.RARE,
                icon="👑",
                color="#FF9800",
                criteria={"reputation_tier": "master"},
                points_reward=100,
                created_at=datetime.utcnow()
            ),
            
            "legend": Badge(
                id="legend",
                name="Legend",
                description="Became a legend in the Planarx community",
                badge_type=BadgeType.LEGEND,
                rarity=BadgeRarity.LEGENDARY,
                icon="🏆",
                color="#E91E63",
                criteria={"reputation_tier": "legend"},
                points_reward=500,
                created_at=datetime.utcnow()
            ),
            
            "first_draft": Badge(
                id="first_draft",
                name="First Draft",
                description="Submitted your first draft",
                badge_type=BadgeType.FIRST_DRAFT,
                rarity=BadgeRarity.COMMON,
                icon="📝",
                color="#4CAF50",
                criteria={"drafts_submitted": 1},
                points_reward=15,
                created_at=datetime.utcnow()
            ),
            
            "draft_master": Badge(
                id="draft_master",
                name="Draft Master",
                description="Submitted 50+ drafts",
                badge_type=BadgeType.DRAFT_MASTER,
                rarity=BadgeRarity.RARE,
                icon="📚",
                color="#9C27B0",
                criteria={"drafts_submitted": 50},
                points_reward=200,
                created_at=datetime.utcnow()
            ),
            
            "comment_king": Badge(
                id="comment_king",
                name="Comment King",
                description="Made 100+ helpful comments",
                badge_type=BadgeType.COMMENT_KING,
                rarity=BadgeRarity.UNCOMMON,
                icon="💬",
                color="#607D8B",
                criteria={"helpful_comments": 100},
                points_reward=75,
                created_at=datetime.utcnow()
            ),
            
            "helper": Badge(
                id="helper",
                name="Helper",
                description="Helped resolve 25+ threads",
                badge_type=BadgeType.HELPER,
                rarity=BadgeRarity.UNCOMMON,
                icon="🤝",
                color="#4CAF50",
                criteria={"threads_resolved": 25},
                points_reward=100,
                created_at=datetime.utcnow()
            ),
            
            "moderator": Badge(
                id="moderator",
                name="Moderator",
                description="Performed 50+ moderation actions",
                badge_type=BadgeType.MODERATOR,
                rarity=BadgeRarity.RARE,
                icon="🛡️",
                color="#FF5722",
                criteria={"moderation_actions": 50},
                points_reward=150,
                created_at=datetime.utcnow()
            ),
            
            "collaborator": Badge(
                id="collaborator",
                name="Collaborator",
                description="Participated in 20+ collaboration sessions",
                badge_type=BadgeType.COLLABORATOR,
                rarity=BadgeRarity.UNCOMMON,
                icon="👥",
                color="#2196F3",
                criteria={"collaboration_sessions": 20},
                points_reward=80,
                created_at=datetime.utcnow()
            ),
            
            "funder": Badge(
                id="funder",
                name="Funder",
                description="Contributed to 10+ projects",
                badge_type=BadgeType.FUNDER,
                rarity=BadgeRarity.UNCOMMON,
                icon="💰",
                color="#FFC107",
                criteria={"funding_contributions": 10},
                points_reward=100,
                created_at=datetime.utcnow()
            ),
            
            "milestone_champion": Badge(
                id="milestone_champion",
                name="Milestone Champion",
                description="Reached 10+ project milestones",
                badge_type=BadgeType.MILESTONE_CHAMPION,
                rarity=BadgeRarity.RARE,
                icon="🎯",
                color="#E91E63",
                criteria={"milestones_reached": 10},
                points_reward=200,
                created_at=datetime.utcnow()
            ),
            
            "quality_controller": Badge(
                id="quality_controller",
                name="Quality Controller",
                description="Maintained high quality standards",
                badge_type=BadgeType.QUALITY_CONTROLLER,
                rarity=BadgeRarity.EPIC,
                icon="✨",
                color="#9C27B0",
                criteria={"quality_score": 0.9, "total_contributions": 100},
                points_reward=300,
                created_at=datetime.utcnow()
            ),
            
            "community_builder": Badge(
                id="community_builder",
                name="Community Builder",
                description="Built strong community connections",
                badge_type=BadgeType.COMMUNITY_BUILDER,
                rarity=BadgeRarity.EPIC,
                icon="🏗️",
                color="#795548",
                criteria={"mentions_received": 50, "positive_votes": 200},
                points_reward=250,
                created_at=datetime.utcnow()
            ),
            
            "documentation_hero": Badge(
                id="documentation_hero",
                name="Documentation Hero",
                description="Contributed to documentation",
                badge_type=BadgeType.DOCUMENTATION_HERO,
                rarity=BadgeRarity.RARE,
                icon="📖",
                color="#607D8B",
                criteria={"documentation_contributions": 25},
                points_reward=150,
                created_at=datetime.utcnow()
            ),
            
            "bug_hunter": Badge(
                id="bug_hunter",
                name="Bug Hunter",
                description="Reported 20+ bugs",
                badge_type=BadgeType.BUG_HUNTER,
                rarity=BadgeRarity.UNCOMMON,
                icon="🐛",
                color="#FF5722",
                criteria={"bug_reports": 20},
                points_reward=100,
                created_at=datetime.utcnow()
            ),
            
            "feature_crafter": Badge(
                id="feature_crafter",
                name="Feature Crafter",
                description="Submitted 15+ feature requests",
                badge_type=BadgeType.FEATURE_CRAFTER,
                rarity=BadgeRarity.UNCOMMON,
                icon="💡",
                color="#FF9800",
                criteria={"feature_requests": 15},
                points_reward=120,
                created_at=datetime.utcnow()
            ),
            
            "voting_champion": Badge(
                id="voting_champion",
                name="Voting Champion",
                description="Cast 500+ votes",
                badge_type=BadgeType.VOTING_CHAMPION,
                rarity=BadgeRarity.UNCOMMON,
                icon="🗳️",
                color="#2196F3",
                criteria={"votes_cast": 500},
                points_reward=80,
                created_at=datetime.utcnow()
            ),
            
            "mention_magnet": Badge(
                id="mention_magnet",
                name="Mention Magnet",
                description="Received 100+ mentions",
                badge_type=BadgeType.MENTION_MAGNET,
                rarity=BadgeRarity.UNCOMMON,
                icon="📢",
                color="#E91E63",
                criteria={"mentions_received": 100},
                points_reward=90,
                created_at=datetime.utcnow()
            ),
            
            "session_leader": Badge(
                id="session_leader",
                name="Session Leader",
                description="Led 30+ collaboration sessions",
                badge_type=BadgeType.SESSION_LEADER,
                rarity=BadgeRarity.RARE,
                icon="🎮",
                color="#9C27B0",
                criteria={"sessions_led": 30},
                points_reward=200,
                created_at=datetime.utcnow()
            ),
            
            "resolution_expert": Badge(
                id="resolution_expert",
                name="Resolution Expert",
                description="Resolved 50+ threads",
                badge_type=BadgeType.RESOLUTION_EXPERT,
                rarity=BadgeRarity.RARE,
                icon="✅",
                color="#4CAF50",
                criteria={"threads_resolved": 50},
                points_reward=180,
                created_at=datetime.utcnow()
            ),
            
            "annotation_artist": Badge(
                id="annotation_artist",
                name="Annotation Artist",
                description="Created 100+ annotations",
                badge_type=BadgeType.ANNOTATION_ARTIST,
                rarity=BadgeRarity.UNCOMMON,
                icon="🎨",
                color="#FF5722",
                criteria={"annotations_created": 100},
                points_reward=120,
                created_at=datetime.utcnow()
            ),
            
            "consistency_king": Badge(
                id="consistency_king",
                name="Consistency King",
                description="Contributed for 30+ consecutive days",
                badge_type=BadgeType.CONSISTENCY_KING,
                rarity=BadgeRarity.EPIC,
                icon="📅",
                color="#607D8B",
                criteria={"consecutive_days": 30},
                points_reward=400,
                created_at=datetime.utcnow()
            ),
            
            "innovator": Badge(
                id="innovator",
                name="Innovator",
                description="Introduced groundbreaking ideas",
                badge_type=BadgeType.INNOVATOR,
                rarity=BadgeRarity.LEGENDARY,
                icon="🚀",
                color="#E91E63",
                criteria={"innovative_contributions": 10, "reputation_tier": "expert"},
                points_reward=500,
                created_at=datetime.utcnow()
            )
        }
    
    def check_badge_eligibility(self, user_id: str, user_stats: Dict) -> List[Badge]:
        """Check which badges a user is eligible for"""
        
        eligible_badges = []
        earned_badges = self.get_user_badges(user_id)
        earned_badge_ids = {badge.badge_id for badge in earned_badges}
        
        for badge_id, badge in self.badges.items():
            if badge_id in earned_badge_ids:
                continue
            
            if self._meets_criteria(badge.criteria, user_stats):
                eligible_badges.append(badge)
        
        return eligible_badges
    
    def _meets_criteria(self, criteria: Dict, user_stats: Dict) -> bool:
        """Check if user meets badge criteria"""
        
        for criterion, required_value in criteria.items():
            if criterion not in user_stats:
                return False
            
            user_value = user_stats[criterion]
            
            # Handle different types of criteria
            if isinstance(required_value, (int, float)):
                if user_value < required_value:
                    return False
            elif isinstance(required_value, str):
                if user_value != required_value:
                    return False
            elif isinstance(required_value, dict):
                # Handle complex criteria
                if not self._meets_complex_criteria(required_value, user_stats):
                    return False
        
        return True
    
    def _meets_complex_criteria(self, criteria: Dict, user_stats: Dict) -> bool:
        """Handle complex badge criteria"""
        
        # Example: quality_score with minimum contributions
        if "quality_score" in criteria and "total_contributions" in criteria:
            quality_score = user_stats.get("quality_score", 0)
            total_contributions = user_stats.get("total_contributions", 0)
            
            return (quality_score >= criteria["quality_score"] and 
                   total_contributions >= criteria["total_contributions"])
        
        return True
    
    def award_badge(self, user_id: str, badge_id: str, metadata: Dict = None) -> Optional[UserBadge]:
        """Award a badge to a user"""
        
        if badge_id not in self.badges:
            self.logger.error(f"Badge {badge_id} not found")
            return None
        
        badge = self.badges[badge_id]
        
        # Check if user already has this badge
        user_badges = self.get_user_badges(user_id)
        if any(ub.badge_id == badge_id for ub in user_badges):
            self.logger.warning(f"User {user_id} already has badge {badge_id}")
            return None
        
        # Create user badge
        user_badge = UserBadge(
            id=str(uuid.uuid4()),
            user_id=user_id,
            badge_id=badge_id,
            earned_at=datetime.utcnow(),
            progress=1.0,
            metadata=metadata or {}
        )
        
        # Store user badge
        if user_id not in self.user_badges:
            self.user_badges[user_id] = []
        self.user_badges[user_id].append(user_badge)
        
        # Update progress tracking
        if user_id not in self.badge_progress:
            self.badge_progress[user_id] = {}
        self.badge_progress[user_id][badge_id] = 1.0
        
        self.logger.info(f"Awarded badge {badge_id} to user {user_id}")
        return user_badge
    
    def get_user_badges(self, user_id: str) -> List[UserBadge]:
        """Get all badges earned by a user"""
        
        return self.user_badges.get(user_id, [])
    
    def get_badge_progress(self, user_id: str, badge_id: str) -> float:
        """Get progress towards earning a badge (0.0 to 1.0)"""
        
        if user_id not in self.badge_progress:
            return 0.0
        
        return self.badge_progress.get(user_id, {}).get(badge_id, 0.0)
    
    def update_badge_progress(self, user_id: str, badge_id: str, progress: float):
        """Update progress towards earning a badge"""
        
        if user_id not in self.badge_progress:
            self.badge_progress[user_id] = {}
        
        self.badge_progress[user_id][badge_id] = min(1.0, max(0.0, progress))
    
    def get_badge_details(self, badge_id: str) -> Optional[Badge]:
        """Get detailed information about a badge"""
        
        return self.badges.get(badge_id)
    
    def get_all_badges(self) -> List[Badge]:
        """Get all available badges"""
        
        return list(self.badges.values())
    
    def get_badges_by_rarity(self, rarity: BadgeRarity) -> List[Badge]:
        """Get badges filtered by rarity"""
        
        return [badge for badge in self.badges.values() if badge.rarity == rarity]
    
    def get_user_badge_summary(self, user_id: str) -> Dict:
        """Get comprehensive badge summary for a user"""
        
        user_badges = self.get_user_badges(user_id)
        
        # Count badges by rarity
        rarity_counts = {}
        for badge in user_badges:
            badge_details = self.get_badge_details(badge.badge_id)
            if badge_details:
                rarity = badge_details.rarity.value
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        # Calculate total points from badges
        total_badge_points = sum(
            self.get_badge_details(badge.badge_id).points_reward
            for badge in user_badges
            if self.get_badge_details(badge.badge_id)
        )
        
        return {
            "user_id": user_id,
            "total_badges": len(user_badges),
            "badges_by_rarity": rarity_counts,
            "total_badge_points": total_badge_points,
            "recent_badges": [
                {
                    "badge_id": badge.badge_id,
                    "earned_at": badge.earned_at.isoformat(),
                    "badge_details": asdict(self.get_badge_details(badge.badge_id))
                }
                for badge in sorted(user_badges, key=lambda b: b.earned_at, reverse=True)[:5]
            ],
            "all_badges": [
                {
                    "badge_id": badge.badge_id,
                    "earned_at": badge.earned_at.isoformat(),
                    "progress": badge.progress,
                    "badge_details": asdict(self.get_badge_details(badge.badge_id))
                }
                for badge in user_badges
            ]
        }
    
    def get_leaderboard_by_badges(self, limit: int = 50) -> List[Dict]:
        """Get leaderboard based on badge points"""
        
        user_scores = {}
        
        for user_id, user_badges in self.user_badges.items():
            total_points = sum(
                self.get_badge_details(badge.badge_id).points_reward
                for badge in user_badges
                if self.get_badge_details(badge.badge_id)
            )
            user_scores[user_id] = total_points
        
        # Sort by points (highest first)
        sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
        
        leaderboard = []
        for i, (user_id, points) in enumerate(sorted_users[:limit]):
            user_badges = self.get_user_badges(user_id)
            
            leaderboard.append({
                "rank": i + 1,
                "user_id": user_id,
                "total_badge_points": points,
                "total_badges": len(user_badges),
                "recent_badge": user_badges[-1].badge_id if user_badges else None
            })
        
        return leaderboard
    
    def check_consecutive_days(self, user_id: str, contribution_dates: List[datetime]) -> int:
        """Check consecutive days of contribution"""
        
        if not contribution_dates:
            return 0
        
        # Sort dates and remove duplicates
        unique_dates = sorted(list(set(date.date() for date in contribution_dates)))
        
        if not unique_dates:
            return 0
        
        consecutive_days = 1
        max_consecutive = 1
        
        for i in range(1, len(unique_dates)):
            days_diff = (unique_dates[i] - unique_dates[i-1]).days
            
            if days_diff == 1:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 1
        
        return max_consecutive
    
    def calculate_quality_score(self, user_id: str, contributions: List) -> float:
        """Calculate user's quality score based on contributions"""
        
        if not contributions:
            return 0.0
        
        # Calculate various quality metrics
        total_contributions = len(contributions)
        positive_feedback = sum(1 for c in contributions if getattr(c, 'positive_feedback', False))
        helpful_comments = sum(1 for c in contributions if getattr(c, 'helpful', False))
        resolved_threads = sum(1 for c in contributions if getattr(c, 'resolved', False))
        
        # Weighted quality score
        quality_score = (
            (positive_feedback / total_contributions) * 0.4 +
            (helpful_comments / total_contributions) * 0.3 +
            (resolved_threads / total_contributions) * 0.3
        )
        
        return min(1.0, quality_score)
    
    def get_badge_recommendations(self, user_id: str, user_stats: Dict) -> List[Dict]:
        """Get personalized badge recommendations"""
        
        recommendations = []
        earned_badges = self.get_user_badges(user_id)
        earned_badge_ids = {badge.badge_id for badge in earned_badges}
        
        for badge_id, badge in self.badges.items():
            if badge_id in earned_badge_ids:
                continue
            
            progress = self._calculate_badge_progress(badge.criteria, user_stats)
            
            if progress > 0.0:
                recommendations.append({
                    "badge_id": badge_id,
                    "badge_details": asdict(badge),
                    "progress": progress,
                    "remaining_effort": self._calculate_remaining_effort(badge.criteria, user_stats)
                })
        
        # Sort by progress (highest first)
        recommendations.sort(key=lambda r: r["progress"], reverse=True)
        return recommendations[:10]  # Top 10 recommendations
    
    def _calculate_badge_progress(self, criteria: Dict, user_stats: Dict) -> float:
        """Calculate progress towards earning a badge"""
        
        progress_values = []
        
        for criterion, required_value in criteria.items():
            if criterion not in user_stats:
                progress_values.append(0.0)
                continue
            
            user_value = user_stats[criterion]
            
            if isinstance(required_value, (int, float)):
                progress = min(1.0, user_value / required_value)
                progress_values.append(progress)
            else:
                # For non-numeric criteria, either 0 or 1
                progress_values.append(1.0 if user_value == required_value else 0.0)
        
        return sum(progress_values) / len(progress_values) if progress_values else 0.0
    
    def _calculate_remaining_effort(self, criteria: Dict, user_stats: Dict) -> Dict:
        """Calculate remaining effort needed for each criterion"""
        
        remaining = {}
        
        for criterion, required_value in criteria.items():
            user_value = user_stats.get(criterion, 0)
            
            if isinstance(required_value, (int, float)):
                remaining_value = max(0, required_value - user_value)
                remaining[criterion] = remaining_value
        
        return remaining


# Global badge system instance
badge_system = BadgeSystem() 