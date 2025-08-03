"""
Reputation System API Routes
FastAPI routes for reputation scoring, badges, and grant eligibility
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from datetime import datetime
import logging

from services.scoring_engine
from services.badges
from ..auth.auth_utils import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reputation", tags=["reputation"])


# Reputation Scoring Routes
@router.post("/contribute")
async def record_contribution(
    contribution_type: str,
    metadata: Dict = None,
    quality_score: float = 1.0,
    current_user: User = Depends(get_current_user):
    """Record a contribution and award reputation points"""
    
    try:
        contribution_enum = ContributionType(contribution_type)
        
        event = reputation_engine.record_contribution(
            user_id=current_user.id,
            contribution_type=contribution_enum,
            metadata=metadata or {},
            quality_score=quality_score
        )
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid contribution or daily limit exceeded")
        
        return {
            "success": True,
            "event": {
                "id": event.id,
                "contribution_type": event.contribution_type.value,
                "points_earned": event.points_earned,
                "timestamp": event.timestamp.isoformat(),
                "validated": event.validated,
                "abuse_score": event.abuse_score
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid contribution type: {e}")
    except Exception as e:
        logger.error(f"Error recording contribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to record contribution")


@router.get("/profile/{user_id}")
async def get_user_reputation(
    user_id: str,
    current_user: User = Depends(get_current_user):
    """Get user's reputation profile"""
    
    reputation = reputation_engine.get_user_reputation(user_id)
    if not reputation:
        raise HTTPException(status_code=404, detail="User reputation not found")
    
    # Get user badges
    user_badges = badge_system.get_user_badges(user_id)
    badge_summary = badge_system.get_user_badge_summary(user_id)
    
    # Get contribution statistics
    contribution_stats = reputation_engine.get_contribution_stats(user_id)
    
    # Get badge recommendations
    recommendations = badge_system.get_badge_recommendations(user_id, contribution_stats)
    
    return {
        "success": True,
        "profile": {
            "user_id": reputation.user_id,
            "total_points": reputation.total_points,
            "current_tier": reputation.current_tier.value,
            "tier_points": reputation.tier_points,
            "contribution_count": reputation.contribution_count,
            "last_activity": reputation.last_activity.isoformat(),
            "privileges": reputation.privileges,
            "reputation_history": reputation.reputation_history[-10:]  # Last 10 events
        },
        "badges": badge_summary,
        "stats": contribution_stats,
        "recommendations": recommendations
    }


@router.get("/leaderboard")
async def get_reputation_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user):
    """Get reputation leaderboard"""
    
    leaderboard = reputation_engine.get_leaderboard(limit)
    
    return {
        "success": True,
        "leaderboard": leaderboard
    }


@router.get("/contributions/{user_id}")
async def get_user_contributions(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user):
    """Get user's contribution history"""
    
    try:
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')
        
        contributions = reputation_engine.get_user_contributions(
            user_id, start_dt, end_dt
        )
        
        # Limit results
        contributions = contributions[:limit]
        
        return {
            "success": True,
            "contributions": [
                {
                    "id": c.id,
                    "contribution_type": c.contribution_type.value,
                    "points_earned": c.points_earned,
                    "timestamp": c.timestamp.isoformat(),
                    "metadata": c.metadata,
                    "validated": c.validated,
                    "abuse_score": c.abuse_score
                }
                for c in contributions
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")


@router.get("/stats/{user_id}")
async def get_user_stats(
    user_id: str,
    current_user: User = Depends(get_current_user):
    """Get detailed user statistics"""
    
    stats = reputation_engine.get_contribution_stats(user_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="User statistics not found")
    
    return {
        "success": True,
        "stats": stats
    }


# Badge Routes
@router.get("/badges")
async def get_all_badges(
    current_user: User = Depends(get_current_user):
    """Get all available badges"""
    
    badges = badge_system.get_all_badges()
    
    return {
        "success": True,
        "badges": [
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "badge_type": badge.badge_type.value,
                "rarity": badge.rarity.value,
                "icon": badge.icon,
                "color": badge.color,
                "criteria": badge.criteria,
                "points_reward": badge.points_reward
            }
            for badge in badges
        ]
    }


@router.get("/badges/{badge_id}")
async def get_badge_details(
    badge_id: str,
    current_user: User = Depends(get_current_user):
    """Get detailed information about a badge"""
    
    badge = badge_system.get_badge_details(badge_id)
    
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")
    
    return {
        "success": True,
        "badge": {
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "badge_type": badge.badge_type.value,
            "rarity": badge.rarity.value,
            "icon": badge.icon,
            "color": badge.color,
            "criteria": badge.criteria,
            "points_reward": badge.points_reward,
            "created_at": badge.created_at.isoformat()
        }
    }


@router.get("/badges/rarity/{rarity}")
async def get_badges_by_rarity(
    rarity: str,
    current_user: User = Depends(get_current_user):
    """Get badges filtered by rarity"""
    
    from services.planarx.planarx_community.reputation.badges import BadgeRarity
    
    try:
        rarity_enum = BadgeRarity(rarity)
        badges = badge_system.get_badges_by_rarity(rarity_enum)
        
        return {
            "success": True,
            "badges": [
                {
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "badge_type": badge.badge_type.value,
                    "rarity": badge.rarity.value,
                    "icon": badge.icon,
                    "color": badge.color
                }
                for badge in badges
            ]
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rarity value")


@router.get("/user/{user_id}/badges")
async def get_user_badges(
    user_id: str,
    current_user: User = Depends(get_current_user):
    """Get badges earned by a user"""
    
    user_badges = badge_system.get_user_badges(user_id)
    badge_summary = badge_system.get_user_badge_summary(user_id)
    
    return {
        "success": True,
        "badges": [
            {
                "id": badge.id,
                "badge_id": badge.badge_id,
                "earned_at": badge.earned_at.isoformat(),
                "progress": badge.progress,
                "metadata": badge.metadata
            }
            for badge in user_badges
        ],
        "summary": badge_summary
    }


@router.get("/user/{user_id}/badge-progress/{badge_id}")
async def get_badge_progress(
    user_id: str,
    badge_id: str,
    current_user: User = Depends(get_current_user):
    """Get user's progress towards earning a badge"""
    
    progress = badge_system.get_badge_progress(user_id, badge_id)
    badge_details = badge_system.get_badge_details(badge_id)
    
    if not badge_details:
        raise HTTPException(status_code=404, detail="Badge not found")
    
    return {
        "success": True,
        "progress": progress,
        "badge_details": {
            "id": badge_details.id,
            "name": badge_details.name,
            "description": badge_details.description,
            "icon": badge_details.icon,
            "color": badge_details.color
        }
    }


@router.get("/badge-leaderboard")
async def get_badge_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user):
    """Get leaderboard based on badge points"""
    
    leaderboard = badge_system.get_leaderboard_by_badges(limit)
    
    return {
        "success": True,
        "leaderboard": leaderboard
    }


# Abuse Detection Routes
@router.get("/abuse-reports")
async def get_abuse_reports(
    current_user: User = Depends(get_current_user):
    """Get all users flagged for abuse review"""
    
    # Check if user has moderation privileges
    user_reputation = reputation_engine.get_user_reputation(current_user.id)
    if not user_reputation or "moderate_content" not in user_reputation.privileges:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    reports = reputation_engine.get_abuse_reports()
    
    return {
        "success": True,
        "reports": reports
    }


@router.post("/flag-user/{user_id}")
async def flag_user_for_review(
    user_id: str,
    reason: str,
    current_user: User = Depends(get_current_user):
    """Flag a user for manual review"""
    
    # Check if user has moderation privileges
    user_reputation = reputation_engine.get_user_reputation(current_user.id)
    if not user_reputation or "moderate_content" not in user_reputation.privileges:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    reputation_engine.flag_user_for_review(user_id, reason)
    
    return {
        "success": True,
        "message": f"User {user_id} flagged for review"
    }


@router.post("/clear-flag/{user_id}")
async def clear_abuse_flag(
    user_id: str,
    current_user: User = Depends(get_current_user):
    """Clear abuse flag for a user"""
    
    # Check if user has moderation privileges
    user_reputation = reputation_engine.get_user_reputation(current_user.id)
    if not user_reputation or "moderate_content" not in user_reputation.privileges:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    reputation_engine.clear_abuse_flag(user_id, current_user.id)
    
    return {
        "success": True,
        "message": f"Abuse flag cleared for user {user_id}"
    }


# Grant Eligibility Routes
@router.get("/grant-eligibility/{user_id}")
async def get_grant_eligibility(
    user_id: str,
    current_user: User = Depends(get_current_user):
    """Get user's eligibility for different grant types"""
    
    from ..funding.grant_eligibility import grant_eligibility_engine, GrantType
    
    # Get user reputation and badges
    user_reputation = reputation_engine.get_user_reputation(user_id)
    if not user_reputation:
        raise HTTPException(status_code=404, detail="User reputation not found")
    
    user_badges = [badge.badge_id for badge in badge_system.get_user_badges(user_id)]
    
    # Check eligibility for each grant type
    eligibility_results = {}
    
    for grant_type in GrantType:
        eligibility = grant_eligibility_engine.check_user_eligibility(
            user_id=user_id,
            grant_type=grant_type,
            user_reputation={
                "current_tier": user_reputation.current_tier.value,
                "total_points": user_reputation.total_points,
                "contribution_count": user_reputation.contribution_count
            },
            user_badges=user_badges
        )
        
        eligibility_results[grant_type.value] = {
            "status": eligibility.status.value,
            "eligibility_score": eligibility.eligibility_score,
            "priority_level": eligibility.priority_level,
            "funding_limit": eligibility.funding_limit,
            "requirements_missing": eligibility.requirements_missing,
            "last_checked": eligibility.last_checked.isoformat()
        }
    
    # Get funding priority
    user_stats = reputation_engine.get_contribution_stats(user_id)
    funding_priority = grant_eligibility_engine.calculate_funding_priority(
        user_id=user_id,
        user_reputation={
            "current_tier": user_reputation.current_tier.value,
            "total_points": user_reputation.total_points
        },
        user_stats=user_stats or {}
    )
    
    return {
        "success": True,
        "eligibility": eligibility_results,
        "funding_priority": {
            "total_priority": funding_priority.total_priority,
            "funding_multiplier": funding_priority.funding_multiplier,
            "escrow_priority": funding_priority.escrow_priority,
            "reputation_bonus": funding_priority.reputation_bonus,
            "contribution_bonus": funding_priority.contribution_bonus,
            "consistency_bonus": funding_priority.consistency_bonus,
            "quality_bonus": funding_priority.quality_bonus
        }
    }


@router.get("/funding-priority-leaderboard")
async def get_funding_priority_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user):
    """Get leaderboard of users by funding priority"""
    
    from ..funding.grant_eligibility import grant_eligibility_engine
    
    leaderboard = grant_eligibility_engine.get_funding_priority_leaderboard(limit)
    
    return {
        "success": True,
        "leaderboard": leaderboard
    }


@router.get("/grant-visibility/{grant_type}")
async def get_grant_visibility_rules(
    grant_type: str,
    current_user: User = Depends(get_current_user):
    """Get visibility rules for a grant type"""
    
    from ..funding.grant_eligibility import grant_eligibility_engine, GrantType
    
    try:
        grant_enum = GrantType(grant_type)
        
        # Get current user's tier
        user_reputation = reputation_engine.get_user_reputation(current_user.id)
        user_tier = user_reputation.current_tier.value if user_reputation else "newcomer"
        
        visibility_rules = grant_eligibility_engine.get_grant_visibility_rules(
            grant_enum, user_tier
        )
        
        return {
            "success": True,
            "visibility_rules": visibility_rules
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid grant type")


@router.get("/escrow-rules/{grant_type}")
async def get_escrow_rules(
    grant_type: str,
    current_user: User = Depends(get_current_user):
    """Get escrow rules for a grant type"""
    
    from ..funding.grant_eligibility import grant_eligibility_engine, GrantType
    
    try:
        grant_enum = GrantType(grant_type)
        escrow_rules = grant_eligibility_engine.get_escrow_rules(grant_enum)
        
        return {
            "success": True,
            "escrow_rules": escrow_rules
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid grant type")


@router.get("/review-requirements/{grant_type}")
async def get_review_requirements(
    grant_type: str,
    current_user: User = Depends(get_current_user):
    """Get review requirements for a grant type"""
    
    from ..funding.grant_eligibility import grant_eligibility_engine, GrantType
    
    try:
        grant_enum = GrantType(grant_type)
        review_requirements = grant_eligibility_engine.get_review_requirements(grant_enum)
        
        return {
            "success": True,
            "review_requirements": review_requirements
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid grant type")


# Analytics Routes
@router.get("/analytics/eligibility-stats")
async def get_eligibility_stats(
    current_user: User = Depends(get_current_user):
    """Get statistics about grant eligibility across the platform"""
    
    from ..funding.grant_eligibility import grant_eligibility_engine
    
    # Check if user has admin privileges
    user_reputation = reputation_engine.get_user_reputation(current_user.id)
    if not user_reputation or "admin_access" not in user_reputation.privileges:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    stats = grant_eligibility_engine.get_eligibility_stats()
    
    return {
        "success": True,
        "stats": stats
    }


@router.get("/analytics/reputation-stats")
async def get_reputation_stats(
    current_user: User = Depends(get_current_user):
    """Get reputation system statistics"""
    
    # Check if user has admin privileges
    user_reputation = reputation_engine.get_user_reputation(current_user.id)
    if not user_reputation or "admin_access" not in user_reputation.privileges:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    # Calculate reputation statistics
    all_reputations = list(reputation_engine.user_reputations.values()
    
    if not all_reputations:
        return {
            "success": True,
            "stats": {
                "total_users": 0,
                "average_points": 0,
                "tier_distribution": {},
                "total_contributions": 0
            }
        }
    
    total_users = len(all_reputations)
    total_points = sum(r.total_points for r in all_reputations)
    total_contributions = sum(r.contribution_count for r in all_reputations)
    average_points = total_points / total_users
    
    # Tier distribution
    tier_distribution = {}
    for reputation in all_reputations:
        tier = reputation.current_tier.value
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
    
    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "average_points": round(average_points, 2),
            "tier_distribution": tier_distribution,
            "total_contributions": total_contributions,
            "total_points": total_points
        }
    }


# Search Routes
@router.get("/search/users")
async def search_users_by_reputation(
    query: str,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
    tier: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user):
    """Search users by reputation criteria"""
    
    # Get all reputations
    all_reputations = list(reputation_engine.user_reputations.values()
    
    # Filter by criteria
    filtered_reputations = []
    
    for reputation in all_reputations:
        # Check query match (would need user names in real implementation)
        if query.lower() in reputation.user_id.lower():
            pass  # Would check user display name in real implementation
        
        # Check point range
        if min_points and reputation.total_points < min_points:
            continue
        if max_points and reputation.total_points > max_points:
            continue
        
        # Check tier
        if tier and reputation.current_tier.value != tier:
            continue
        
        filtered_reputations.append(reputation)
    
    # Sort by total points (highest first)
    filtered_reputations.sort(key=lambda r: r.total_points, reverse=True)
    
    # Limit results
    results = filtered_reputations[:limit]
    
    return {
        "success": True,
        "users": [
            {
                "user_id": r.user_id,
                "total_points": r.total_points,
                "current_tier": r.current_tier.value,
                "contribution_count": r.contribution_count,
                "last_activity": r.last_activity.isoformat()
            }
            for r in results
        ]
    } 