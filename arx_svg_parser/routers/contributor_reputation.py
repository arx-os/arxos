"""
Contributor Reputation Engine API Router

This module provides RESTful API endpoints for the Contributor Reputation Engine,
including reputation scoring, peer reviews, revenue distribution, and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from services.contributor_reputation_engine import (
    ContributorReputationEngine,
    ReputationScore,
    PeerReview,
    RevenueDistribution,
    ReviewStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reputation", tags=["Contributor Reputation"])

# Initialize the reputation engine
reputation_engine = ContributorReputationEngine()


@router.get("/profile/{contributor_id}")
async def get_contributor_profile(contributor_id: str) -> Dict[str, Any]:
    """
    Get reputation profile for a specific contributor.
    
    Args:
        contributor_id: Unique identifier for the contributor
        
    Returns:
        Dictionary containing reputation profile data
    """
    try:
        # Calculate current reputation score
        reputation_score = await reputation_engine.calculate_reputation_score(contributor_id)
        
        # Get analytics for the contributor
        analytics = await reputation_engine.get_reputation_analytics(contributor_id)
        
        profile = {
            "contributor_id": contributor_id,
            "reputation_score": reputation_score.total_score,
            "factor_scores": {
                "peer_approval_rate": reputation_score.peer_approval_rate,
                "data_quality_score": reputation_score.data_quality_score,
                "commit_success_rate": reputation_score.commit_success_rate,
                "ahj_acceptance_rate": reputation_score.ahj_acceptance_rate,
                "review_quality_score": reputation_score.review_quality_score
            },
            "total_contributions": reputation_score.total_contributions,
            "last_updated": reputation_score.last_updated.isoformat(),
            "analytics": analytics
        }
        
        logger.info(f"Retrieved reputation profile for {contributor_id}")
        return profile
        
    except Exception as e:
        logger.error(f"Error getting reputation profile for {contributor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reputation profile: {str(e)}")


@router.post("/review")
async def submit_peer_review(review_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit a peer review for a contribution.
    
    Args:
        review_data: Dictionary containing review information
        
    Returns:
        Dictionary containing the submitted review data
    """
    try:
        # Validate required fields
        required_fields = ["contribution_id", "reviewer_id", "contributor_id", "status", "review_score"]
        for field in required_fields:
            if field not in review_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate review score
        review_score = review_data["review_score"]
        if not isinstance(review_score, int) or review_score < 1 or review_score > 10:
            raise HTTPException(status_code=400, detail="Review score must be an integer between 1 and 10")
        
        # Validate status
        try:
            ReviewStatus(review_data["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid review status")
        
        # Submit the review
        review = await reputation_engine.submit_peer_review(review_data)
        
        response = {
            "review_id": review.review_id,
            "contribution_id": review.contribution_id,
            "reviewer_id": review.reviewer_id,
            "contributor_id": review.contributor_id,
            "status": review.status.value,
            "review_score": review.review_score,
            "comments": review.comments,
            "created_at": review.created_at.isoformat()
        }
        
        logger.info(f"Peer review submitted: {review.review_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting peer review: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit peer review: {str(e)}")


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of contributors to return")
) -> Dict[str, Any]:
    """
    Get top contributors by reputation score.
    
    Args:
        limit: Maximum number of contributors to return (1-100)
        
    Returns:
        Dictionary containing leaderboard data
    """
    try:
        leaderboard = await reputation_engine.get_leaderboard(limit)
        
        leaderboard_data = []
        for i, score in enumerate(leaderboard, 1):
            leaderboard_data.append({
                "rank": i,
                "contributor_id": score.contributor_id,
                "reputation_score": score.total_score,
                "total_contributions": score.total_contributions,
                "factor_scores": {
                    "peer_approval_rate": score.peer_approval_rate,
                    "data_quality_score": score.data_quality_score,
                    "commit_success_rate": score.commit_success_rate,
                    "ahj_acceptance_rate": score.ahj_acceptance_rate,
                    "review_quality_score": score.review_quality_score
                },
                "last_updated": score.last_updated.isoformat()
            })
        
        response = {
            "leaderboard": leaderboard_data,
            "total_contributors": len(leaderboard_data),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Retrieved leaderboard with {len(leaderboard_data)} contributors")
        return response
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


@router.post("/calculate")
async def recalculate_reputation_scores(contributor_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recalculate reputation scores for contributors.
    
    Args:
        contributor_ids: Optional list of contributor IDs to recalculate. If None, recalculates all.
        
    Returns:
        Dictionary containing recalculation results
    """
    try:
        results = []
        
        if contributor_ids:
            # Recalculate specific contributors
            for contributor_id in contributor_ids:
                try:
                    score = await reputation_engine.calculate_reputation_score(contributor_id)
                    results.append({
                        "contributor_id": contributor_id,
                        "reputation_score": score.total_score,
                        "status": "success"
                    })
                except Exception as e:
                    results.append({
                        "contributor_id": contributor_id,
                        "error": str(e),
                        "status": "failed"
                    })
        else:
            # Recalculate all contributors (get from leaderboard)
            leaderboard = await reputation_engine.get_leaderboard(1000)  # Get all
            for score in leaderboard:
                try:
                    new_score = await reputation_engine.calculate_reputation_score(score.contributor_id)
                    results.append({
                        "contributor_id": score.contributor_id,
                        "reputation_score": new_score.total_score,
                        "status": "success"
                    })
                except Exception as e:
                    results.append({
                        "contributor_id": score.contributor_id,
                        "error": str(e),
                        "status": "failed"
                    })
        
        success_count = len([r for r in results if r["status"] == "success"])
        failed_count = len([r for r in results if r["status"] == "failed"])
        
        response = {
            "results": results,
            "summary": {
                "total_processed": len(results),
                "successful": success_count,
                "failed": failed_count
            },
            "completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Recalculated reputation scores: {success_count} successful, {failed_count} failed")
        return response
        
    except Exception as e:
        logger.error(f"Error recalculating reputation scores: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to recalculate reputation scores: {str(e)}")


@router.get("/analytics")
async def get_reputation_analytics(
    contributor_id: Optional[str] = Query(None, description="Optional contributor ID for specific analytics")
) -> Dict[str, Any]:
    """
    Get reputation analytics.
    
    Args:
        contributor_id: Optional contributor ID for specific analytics
        
    Returns:
        Dictionary containing analytics data
    """
    try:
        analytics = await reputation_engine.get_reputation_analytics(contributor_id)
        
        response = {
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Retrieved reputation analytics for {contributor_id or 'all contributors'}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting reputation analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reputation analytics: {str(e)}")


@router.post("/distribute")
async def process_revenue_distribution(
    total_revenue: float = Query(..., gt=0, description="Total revenue to distribute")
) -> Dict[str, Any]:
    """
    Process revenue distribution based on reputation scores.
    
    Args:
        total_revenue: Total revenue to distribute
        
    Returns:
        Dictionary containing distribution results
    """
    try:
        distributions = await reputation_engine.calculate_revenue_distribution(total_revenue)
        
        distribution_data = []
        total_distributed = 0
        
        for distribution in distributions:
            distribution_data.append({
                "distribution_id": distribution.distribution_id,
                "contributor_id": distribution.contributor_id,
                "amount": distribution.amount,
                "distribution_type": distribution.distribution_type,
                "reputation_factor": distribution.reputation_factor,
                "created_at": distribution.created_at.isoformat()
            })
            total_distributed += distribution.amount
        
        response = {
            "distributions": distribution_data,
            "summary": {
                "total_revenue": total_revenue,
                "total_distributed": total_distributed,
                "distributions_count": len(distributions),
                "average_distribution": total_distributed / len(distributions) if distributions else 0
            },
            "processed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Processed revenue distribution: ${total_revenue} distributed to {len(distributions)} contributors")
        return response
        
    except Exception as e:
        logger.error(f"Error processing revenue distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process revenue distribution: {str(e)}")


@router.get("/reviews/{contributor_id}")
async def get_contributor_reviews(
    contributor_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of reviews to return")
) -> Dict[str, Any]:
    """
    Get reviews for a specific contributor.
    
    Args:
        contributor_id: Contributor ID to get reviews for
        limit: Maximum number of reviews to return
        
    Returns:
        Dictionary containing review data
    """
    try:
        # This would typically query the database for reviews
        # For now, return mock data
        reviews = []
        
        response = {
            "contributor_id": contributor_id,
            "reviews": reviews,
            "total_reviews": len(reviews),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Retrieved {len(reviews)} reviews for contributor {contributor_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting reviews for {contributor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")


@router.get("/history/{contributor_id}")
async def get_reputation_history(
    contributor_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history to retrieve")
) -> Dict[str, Any]:
    """
    Get reputation history for a contributor.
    
    Args:
        contributor_id: Contributor ID to get history for
        days: Number of days of history to retrieve
        
    Returns:
        Dictionary containing reputation history
    """
    try:
        # This would typically query the database for historical data
        # For now, return mock data
        history = []
        
        response = {
            "contributor_id": contributor_id,
            "history": history,
            "days_requested": days,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Retrieved reputation history for contributor {contributor_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting reputation history for {contributor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reputation history: {str(e)}")


@router.get("/stats")
async def get_reputation_stats() -> Dict[str, Any]:
    """
    Get overall reputation system statistics.
    
    Returns:
        Dictionary containing system statistics
    """
    try:
        # Get leaderboard for stats
        leaderboard = await reputation_engine.get_leaderboard(1000)  # Get all
        
        if not leaderboard:
            return {
                "total_contributors": 0,
                "average_score": 0,
                "score_distribution": {"excellent": 0, "good": 0, "average": 0, "poor": 0},
                "generated_at": datetime.utcnow().isoformat()
            }
        
        total_contributors = len(leaderboard)
        average_score = sum(score.total_score for score in leaderboard) / total_contributors
        
        # Calculate score distribution
        distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}
        for score in leaderboard:
            if score.total_score >= 0.9:
                distribution["excellent"] += 1
            elif score.total_score >= 0.7:
                distribution["good"] += 1
            elif score.total_score >= 0.5:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1
        
        response = {
            "total_contributors": total_contributors,
            "average_score": average_score,
            "score_distribution": distribution,
            "top_contributor": {
                "contributor_id": leaderboard[0].contributor_id,
                "score": leaderboard[0].total_score
            } if leaderboard else None,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Retrieved reputation stats: {total_contributors} contributors, avg score: {average_score:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting reputation stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reputation stats: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the reputation engine.
    
    Returns:
        Dictionary containing health status
    """
    try:
        # Basic health check
        leaderboard = await reputation_engine.get_leaderboard(1)
        
        response = {
            "status": "healthy",
            "engine_available": True,
            "contributors_accessible": len(leaderboard) >= 0,
            "checked_at": datetime.utcnow().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "engine_available": False,
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        } 