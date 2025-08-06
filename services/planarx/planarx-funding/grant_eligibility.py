"""
Grant Eligibility System
Links reputation tiers to funding access, proposal visibility, and escrow priority rules
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GrantType(Enum):
    """Types of grants available"""

    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    COMMUNITY_EVENT = "community_event"
    RESEARCH = "research"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class EligibilityStatus(Enum):
    """Grant eligibility status"""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


@dataclass
class GrantEligibility:
    """Grant eligibility criteria and rules"""

    id: str
    grant_type: GrantType
    min_reputation_tier: str
    min_points: int
    required_badges: List[str]
    max_funding_amount: float
    priority_multiplier: float
    visibility_rules: Dict
    escrow_rules: Dict
    review_requirements: Dict

    def __post_init__(self):
        if self.required_badges is None:
            self.required_badges = []
        if self.visibility_rules is None:
            self.visibility_rules = {}
        if self.escrow_rules is None:
            self.escrow_rules = {}
        if self.review_requirements is None:
            self.review_requirements = {}


@dataclass
class UserEligibility:
    """User's eligibility for specific grants"""

    user_id: str
    grant_type: GrantType
    status: EligibilityStatus
    eligibility_score: float
    last_checked: datetime
    requirements_met: Dict
    requirements_missing: List[str]
    priority_level: int
    funding_limit: float

    def __post_init__(self):
        if self.requirements_met is None:
            self.requirements_met = {}
        if self.requirements_missing is None:
            self.requirements_missing = []


@dataclass
class FundingPriority:
    """Funding priority based on reputation and contribution history"""

    user_id: str
    base_priority: int
    reputation_bonus: float
    contribution_bonus: float
    consistency_bonus: float
    quality_bonus: float
    total_priority: float
    funding_multiplier: float
    escrow_priority: int

    def __post_init__(self):
        if self.reputation_bonus is None:
            self.reputation_bonus = 0.0
        if self.contribution_bonus is None:
            self.contribution_bonus = 0.0
        if self.consistency_bonus is None:
            self.consistency_bonus = 0.0
        if self.quality_bonus is None:
            self.quality_bonus = 0.0


class GrantEligibilityEngine:
    """Engine for managing grant eligibility and funding priorities"""

    def __init__(self):
        self.eligibility_rules: Dict[GrantType, GrantEligibility] = {}
        self.user_eligibility: Dict[str, List[UserEligibility]] = {}
        self.funding_priorities: Dict[str, FundingPriority] = {}

        self.logger = logging.getLogger(__name__)

        self._initialize_eligibility_rules()

    def _initialize_eligibility_rules(self):
        """Initialize eligibility rules for different grant types"""

        self.eligibility_rules = {
            GrantType.FEATURE_DEVELOPMENT: GrantEligibility(
                id="feature_development",
                grant_type=GrantType.FEATURE_DEVELOPMENT,
                min_reputation_tier="expert",
                min_points=1000,
                required_badges=["expert", "quality_controller"],
                max_funding_amount=5000.0,
                priority_multiplier=1.5,
                visibility_rules={
                    "min_tier": "regular",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": True,
                    "technical_assessment": True,
                },
            ),
            GrantType.BUG_FIX: GrantEligibility(
                id="bug_fix",
                grant_type=GrantType.BUG_FIX,
                min_reputation_tier="contributor",
                min_points=100,
                required_badges=["bug_hunter"],
                max_funding_amount=500.0,
                priority_multiplier=1.2,
                visibility_rules={
                    "min_tier": "newcomer",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": True,
                    "review_required": False,
                    "milestone_validation": False,
                },
                review_requirements={
                    "expert_review": False,
                    "community_vote": False,
                    "technical_assessment": True,
                },
            ),
            GrantType.DOCUMENTATION: GrantEligibility(
                id="documentation",
                grant_type=GrantType.DOCUMENTATION,
                min_reputation_tier="regular",
                min_points=500,
                required_badges=["documentation_hero"],
                max_funding_amount=1000.0,
                priority_multiplier=1.3,
                visibility_rules={
                    "min_tier": "contributor",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": False,
                    "technical_assessment": False,
                },
            ),
            GrantType.COMMUNITY_EVENT: GrantEligibility(
                id="community_event",
                grant_type=GrantType.COMMUNITY_EVENT,
                min_reputation_tier="regular",
                min_points=500,
                required_badges=["community_builder"],
                max_funding_amount=2000.0,
                priority_multiplier=1.4,
                visibility_rules={
                    "min_tier": "contributor",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": True,
                    "technical_assessment": False,
                },
            ),
            GrantType.RESEARCH: GrantEligibility(
                id="research",
                grant_type=GrantType.RESEARCH,
                min_reputation_tier="master",
                min_points=2500,
                required_badges=["expert", "innovator"],
                max_funding_amount=10000.0,
                priority_multiplier=2.0,
                visibility_rules={
                    "min_tier": "expert",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": True,
                    "technical_assessment": True,
                },
            ),
            GrantType.INFRASTRUCTURE: GrantEligibility(
                id="infrastructure",
                grant_type=GrantType.INFRASTRUCTURE,
                min_reputation_tier="expert",
                min_points=1000,
                required_badges=["expert", "quality_controller"],
                max_funding_amount=8000.0,
                priority_multiplier=1.8,
                visibility_rules={
                    "min_tier": "regular",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": True,
                    "technical_assessment": True,
                },
            ),
            GrantType.SECURITY: GrantEligibility(
                id="security",
                grant_type=GrantType.SECURITY,
                min_reputation_tier="expert",
                min_points=1000,
                required_badges=["expert", "moderator"],
                max_funding_amount=3000.0,
                priority_multiplier=1.6,
                visibility_rules={
                    "min_tier": "expert",
                    "show_details": False,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": False,
                    "technical_assessment": True,
                },
            ),
            GrantType.ACCESSIBILITY: GrantEligibility(
                id="accessibility",
                grant_type=GrantType.ACCESSIBILITY,
                min_reputation_tier="regular",
                min_points=500,
                required_badges=["helper"],
                max_funding_amount=1500.0,
                priority_multiplier=1.3,
                visibility_rules={
                    "min_tier": "contributor",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": True,
                    "technical_assessment": False,
                },
            ),
            GrantType.PERFORMANCE: GrantEligibility(
                id="performance",
                grant_type=GrantType.PERFORMANCE,
                min_reputation_tier="expert",
                min_points=1000,
                required_badges=["expert", "quality_controller"],
                max_funding_amount=4000.0,
                priority_multiplier=1.5,
                visibility_rules={
                    "min_tier": "regular",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": False,
                    "technical_assessment": True,
                },
            ),
            GrantType.INTEGRATION: GrantEligibility(
                id="integration",
                grant_type=GrantType.INTEGRATION,
                min_reputation_tier="expert",
                min_points=1000,
                required_badges=["expert", "collaborator"],
                max_funding_amount=6000.0,
                priority_multiplier=1.7,
                visibility_rules={
                    "min_tier": "regular",
                    "show_details": True,
                    "show_progress": True,
                },
                escrow_rules={
                    "auto_approval": False,
                    "review_required": True,
                    "milestone_validation": True,
                },
                review_requirements={
                    "expert_review": True,
                    "community_vote": True,
                    "technical_assessment": True,
                },
            ),
        }

    def check_user_eligibility(
        self,
        user_id: str,
        grant_type: GrantType,
        user_reputation: Dict,
        user_badges: List[str],
    ) -> UserEligibility:
        """Check user's eligibility for a specific grant type"""

        if grant_type not in self.eligibility_rules:
            raise ValueError(f"Unknown grant type: {grant_type}")

        rules = self.eligibility_rules[grant_type]
        requirements_met = {}
        requirements_missing = []
        eligibility_score = 0.0

        # Check reputation tier
        user_tier = user_reputation.get("current_tier", "newcomer")
        tier_eligible = self._check_tier_eligibility(
            user_tier, rules.min_reputation_tier
        )
        requirements_met["reputation_tier"] = tier_eligible
        if not tier_eligible:
            requirements_missing.append(
                f"Reputation tier: {user_tier} < {rules.min_reputation_tier}"
            )
        else:
            eligibility_score += 0.4

        # Check minimum points
        user_points = user_reputation.get("total_points", 0)
        points_eligible = user_points >= rules.min_points
        requirements_met["minimum_points"] = points_eligible
        if not points_eligible:
            requirements_missing.append(f"Points: {user_points} < {rules.min_points}")
        else:
            eligibility_score += 0.3

        # Check required badges
        badges_eligible = all(badge in user_badges for badge in rules.required_badges)
        requirements_met["required_badges"] = badges_eligible
        if not badges_eligible:
            missing_badges = [
                badge for badge in rules.required_badges if badge not in user_badges
            ]
            requirements_missing.append(f"Missing badges: {', '.join(missing_badges)}")
        else:
            eligibility_score += 0.3

        # Determine status
        if eligibility_score >= 0.9:
            status = EligibilityStatus.ELIGIBLE
        elif eligibility_score >= 0.6:
            status = EligibilityStatus.PENDING
        else:
            status = EligibilityStatus.INELIGIBLE

        # Calculate priority level
        priority_level = self._calculate_priority_level(user_reputation, rules)

        # Calculate funding limit
        funding_limit = self._calculate_funding_limit(user_reputation, rules)

        # Create eligibility record
        eligibility = UserEligibility(
            user_id=user_id,
            grant_type=grant_type,
            status=status,
            eligibility_score=eligibility_score,
            last_checked=datetime.utcnow(),
            requirements_met=requirements_met,
            requirements_missing=requirements_missing,
            priority_level=priority_level,
            funding_limit=funding_limit,
        )

        # Store eligibility
        if user_id not in self.user_eligibility:
            self.user_eligibility[user_id] = []

        # Update existing or add new
        existing_index = next(
            (
                i
                for i, e in enumerate(self.user_eligibility[user_id])
                if e.grant_type == grant_type
            ),
            None,
        )

        if existing_index is not None:
            self.user_eligibility[user_id][existing_index] = eligibility
        else:
            self.user_eligibility[user_id].append(eligibility)

        self.logger.info(
            f"Eligibility checked for user {user_id}, grant {grant_type}: {status}"
        )
        return eligibility

    def _check_tier_eligibility(self, user_tier: str, required_tier: str) -> bool:
        """Check if user tier meets required tier"""

        tier_hierarchy = {
            "newcomer": 0,
            "contributor": 1,
            "regular": 2,
            "expert": 3,
            "master": 4,
            "legend": 5,
        }

        user_level = tier_hierarchy.get(user_tier, 0)
        required_level = tier_hierarchy.get(required_tier, 0)

        return user_level >= required_level

    def _calculate_priority_level(
        self, user_reputation: Dict, rules: GrantEligibility
    ) -> int:
        """Calculate priority level based on user reputation and grant rules"""

        base_priority = 1

        # Reputation tier bonus
        tier_bonus = {
            "newcomer": 0,
            "contributor": 1,
            "regular": 2,
            "expert": 3,
            "master": 4,
            "legend": 5,
        }

        user_tier = user_reputation.get("current_tier", "newcomer")
        priority = base_priority + tier_bonus.get(user_tier, 0)

        # Apply grant-specific multiplier
        priority = int(priority * rules.priority_multiplier)

        return priority

    def _calculate_funding_limit(
        self, user_reputation: Dict, rules: GrantEligibility
    ) -> float:
        """Calculate funding limit based on user reputation and grant rules"""

        base_limit = rules.max_funding_amount

        # Apply reputation-based multiplier
        user_tier = user_reputation.get("current_tier", "newcomer")
        tier_multipliers = {
            "newcomer": 0.5,
            "contributor": 0.7,
            "regular": 1.0,
            "expert": 1.2,
            "master": 1.5,
            "legend": 2.0,
        }

        multiplier = tier_multipliers.get(user_tier, 1.0)
        funding_limit = base_limit * multiplier

        return funding_limit

    def calculate_funding_priority(
        self, user_id: str, user_reputation: Dict, user_stats: Dict
    ) -> FundingPriority:
        """Calculate comprehensive funding priority for a user"""

        base_priority = 1

        # Reputation bonus
        reputation_bonus = self._calculate_reputation_bonus(user_reputation)

        # Contribution bonus
        contribution_bonus = self._calculate_contribution_bonus(user_stats)

        # Consistency bonus
        consistency_bonus = self._calculate_consistency_bonus(user_stats)

        # Quality bonus
        quality_bonus = self._calculate_quality_bonus(user_reputation, user_stats)

        # Calculate total priority
        total_priority = (
            base_priority
            + reputation_bonus
            + contribution_bonus
            + consistency_bonus
            + quality_bonus
        )

        # Calculate funding multiplier
        funding_multiplier = 1.0 + (total_priority * 0.1)

        # Calculate escrow priority (higher is better)
        escrow_priority = int(total_priority * 10)

        priority = FundingPriority(
            user_id=user_id,
            base_priority=base_priority,
            reputation_bonus=reputation_bonus,
            contribution_bonus=contribution_bonus,
            consistency_bonus=consistency_bonus,
            quality_bonus=quality_bonus,
            total_priority=total_priority,
            funding_multiplier=funding_multiplier,
            escrow_priority=escrow_priority,
        )

        self.funding_priorities[user_id] = priority
        return priority

    def _calculate_reputation_bonus(self, user_reputation: Dict) -> float:
        """Calculate bonus based on reputation tier"""

        tier_bonuses = {
            "newcomer": 0.0,
            "contributor": 0.5,
            "regular": 1.0,
            "expert": 2.0,
            "master": 3.0,
            "legend": 5.0,
        }

        user_tier = user_reputation.get("current_tier", "newcomer")
        return tier_bonuses.get(user_tier, 0.0)

    def _calculate_contribution_bonus(self, user_stats: Dict) -> float:
        """Calculate bonus based on contribution history"""

        total_contributions = user_stats.get("total_contributions", 0)
        recent_activity = user_stats.get("recent_activity", 0)

        # Base contribution bonus
        contribution_bonus = min(2.0, total_contributions / 100)

        # Recent activity bonus
        activity_bonus = min(1.0, recent_activity / 50)

        return contribution_bonus + activity_bonus

    def _calculate_consistency_bonus(self, user_stats: Dict) -> float:
        """Calculate bonus based on consistency"""

        consecutive_days = user_stats.get("consecutive_days", 0)

        # Consistency bonus based on consecutive days
        if consecutive_days >= 30:
            return 2.0
        elif consecutive_days >= 14:
            return 1.0
        elif consecutive_days >= 7:
            return 0.5
        else:
            return 0.0

    def _calculate_quality_bonus(
        self, user_reputation: Dict, user_stats: Dict
    ) -> float:
        """Calculate bonus based on quality of contributions"""

        quality_score = user_stats.get("quality_score", 0.0)
        avg_points = user_stats.get("average_points", 0.0)

        # Quality score bonus
        quality_bonus = quality_score * 2.0

        # Points per contribution bonus
        points_bonus = min(1.0, avg_points / 10)

        return quality_bonus + points_bonus

    def get_user_eligibility_summary(self, user_id: str) -> Dict:
        """Get comprehensive eligibility summary for a user"""

        if user_id not in self.user_eligibility:
            return {
                "eligible_grants": [],
                "pending_grants": [],
                "ineligible_grants": [],
            }

        user_eligibilities = self.user_eligibility[user_id]

        eligible_grants = []
        pending_grants = []
        ineligible_grants = []

        for eligibility in user_eligibilities:
            grant_info = {
                "grant_type": eligibility.grant_type.value,
                "status": eligibility.status.value,
                "eligibility_score": eligibility.eligibility_score,
                "priority_level": eligibility.priority_level,
                "funding_limit": eligibility.funding_limit,
                "requirements_missing": eligibility.requirements_missing,
                "last_checked": eligibility.last_checked.isoformat(),
            }

            if eligibility.status == EligibilityStatus.ELIGIBLE:
                eligible_grants.append(grant_info)
            elif eligibility.status == EligibilityStatus.PENDING:
                pending_grants.append(grant_info)
            else:
                ineligible_grants.append(grant_info)

        return {
            "eligible_grants": eligible_grants,
            "pending_grants": pending_grants,
            "ineligible_grants": ineligible_grants,
            "total_grants": len(user_eligibilities),
        }

    def get_funding_priority_leaderboard(self, limit: int = 50) -> List[Dict]:
        """Get leaderboard of users by funding priority"""

        priorities = list(self.funding_priorities.values())
        priorities.sort(key=lambda p: p.total_priority, reverse=True)

        leaderboard = []
        for i, priority in enumerate(priorities[:limit]):
            leaderboard.append(
                {
                    "rank": i + 1,
                    "user_id": priority.user_id,
                    "total_priority": priority.total_priority,
                    "funding_multiplier": priority.funding_multiplier,
                    "escrow_priority": priority.escrow_priority,
                    "reputation_bonus": priority.reputation_bonus,
                    "contribution_bonus": priority.contribution_bonus,
                    "consistency_bonus": priority.consistency_bonus,
                    "quality_bonus": priority.quality_bonus,
                }
            )

        return leaderboard

    def get_grant_visibility_rules(self, grant_type: GrantType, user_tier: str) -> Dict:
        """Get visibility rules for a grant type based on user tier"""

        if grant_type not in self.eligibility_rules:
            return {}

        rules = self.eligibility_rules[grant_type]
        visibility_rules = rules.visibility_rules

        # Check if user can see this grant
        min_tier = visibility_rules.get("min_tier", "newcomer")
        can_view = self._check_tier_eligibility(user_tier, min_tier)

        return {
            "can_view": can_view,
            "show_details": (
                visibility_rules.get("show_details", False) if can_view else False
            ),
            "show_progress": (
                visibility_rules.get("show_progress", False) if can_view else False
            ),
            "min_tier_required": min_tier,
        }

    def get_escrow_rules(self, grant_type: GrantType) -> Dict:
        """Get escrow rules for a grant type"""

        if grant_type not in self.eligibility_rules:
            return {}

        rules = self.eligibility_rules[grant_type]
        return rules.escrow_rules

    def get_review_requirements(self, grant_type: GrantType) -> Dict:
        """Get review requirements for a grant type"""

        if grant_type not in self.eligibility_rules:
            return {}

        rules = self.eligibility_rules[grant_type]
        return rules.review_requirements

    def update_eligibility_rules(self, grant_type: GrantType, new_rules: Dict):
        """Update eligibility rules for a grant type"""

        if grant_type not in self.eligibility_rules:
            raise ValueError(f"Unknown grant type: {grant_type}")

        current_rules = self.eligibility_rules[grant_type]

        # Update rules
        for key, value in new_rules.items():
            if hasattr(current_rules, key):
                setattr(current_rules, key, value)

        self.logger.info(f"Updated eligibility rules for grant type: {grant_type}")

    def get_eligibility_stats(self) -> Dict:
        """Get statistics about grant eligibility across the platform"""

        total_users = len(self.user_eligibility)
        total_eligibilities = sum(
            len(eligibilities) for eligibilities in self.user_eligibility.values()
        )

        # Count by status
        status_counts = {"eligible": 0, "pending": 0, "ineligible": 0}
        grant_type_counts = {}

        for user_eligibilities in self.user_eligibility.values():
            for eligibility in user_eligibilities:
                status_counts[eligibility.status.value] += 1

                grant_type = eligibility.grant_type.value
                grant_type_counts[grant_type] = grant_type_counts.get(grant_type, 0) + 1

        return {
            "total_users": total_users,
            "total_eligibilities": total_eligibilities,
            "status_counts": status_counts,
            "grant_type_counts": grant_type_counts,
            "average_eligibility_score": sum(
                e.eligibility_score
                for eligibilities in self.user_eligibility.values()
                for e in eligibilities
            )
            / max(total_eligibilities, 1),
        }


# Global grant eligibility engine instance
grant_eligibility_engine = GrantEligibilityEngine()
