"""
Contributor Reputation Engine Service

This module implements a comprehensive reputation scoring system for building data contributors.
It tracks peer approval, data quality, commit reliability, and AHJ acceptance to calculate
reputation scores that influence share distributions and API revenue payouts.
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class ReputationFactor(Enum):
    """Reputation scoring factors"""
    PEER_APPROVAL = "peer_approval"
    DATA_QUALITY = "data_quality"
    COMMIT_SUCCESS = "commit_success"
    AHJ_ACCEPTANCE = "ahj_acceptance"
    REVIEW_QUALITY = "review_quality"


class ReviewStatus(Enum):
    """Peer review status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class ReputationScore:
    """Reputation score data structure"""
    contributor_id: str
    total_score: float
    peer_approval_rate: float
    data_quality_score: float
    commit_success_rate: float
    ahj_acceptance_rate: float
    review_quality_score: float
    total_contributions: int
    last_updated: datetime


@dataclass
class PeerReview:
    """Peer review data structure"""
    review_id: str
    contribution_id: str
    reviewer_id: str
    contributor_id: str
    status: ReviewStatus
    review_score: int
    comments: str
    created_at: datetime


@dataclass
class RevenueDistribution:
    """Revenue distribution data structure"""
    distribution_id: str
    contributor_id: str
    amount: float
    distribution_type: str
    reputation_factor: float
    created_at: datetime


class ContributorReputationEngine:
    """
    Core reputation engine that calculates and manages contributor reputation scores.
    
    This engine implements a multi-factor scoring system that considers:
    - Peer approval rates and review quality
    - Data quality and richness metrics
    - Commit success rates and bug-free contributions
    - AHJ acceptance and regulatory compliance
    - Revenue distribution based on reputation scores
    """
    
    def __init__(self, db_connection=None):
        """Initialize the reputation engine"""
        self.db_connection = db_connection
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.lock = threading.RLock()
        
        # Default reputation weights
        self.weights = {
            ReputationFactor.PEER_APPROVAL: 0.25,
            ReputationFactor.DATA_QUALITY: 0.30,
            ReputationFactor.COMMIT_SUCCESS: 0.20,
            ReputationFactor.AHJ_ACCEPTANCE: 0.15,
            ReputationFactor.REVIEW_QUALITY: 0.10
        }
        
        # Minimum thresholds for reputation factors
        self.thresholds = {
            ReputationFactor.PEER_APPROVAL: 0.70,
            ReputationFactor.DATA_QUALITY: 0.75,
            ReputationFactor.COMMIT_SUCCESS: 0.90,
            ReputationFactor.AHJ_ACCEPTANCE: 0.85,
            ReputationFactor.REVIEW_QUALITY: 0.80
        }
        
        logger.info("Contributor Reputation Engine initialized")
    
    async def calculate_reputation_score(self, contributor_id: str) -> ReputationScore:
        """
        Calculate comprehensive reputation score for a contributor.
        
        Args:
            contributor_id: Unique identifier for the contributor
            
        Returns:
            ReputationScore object with calculated scores
        """
        try:
            with self.lock:
                # Gather all reputation factors
                peer_approval_rate = await self._calculate_peer_approval_rate(contributor_id)
                data_quality_score = await self._calculate_data_quality_score(contributor_id)
                commit_success_rate = await self._calculate_commit_success_rate(contributor_id)
                ahj_acceptance_rate = await self._calculate_ahj_acceptance_rate(contributor_id)
                review_quality_score = await self._calculate_review_quality_score(contributor_id)
                
                # Calculate weighted total score
                total_score = (
                    peer_approval_rate * self.weights[ReputationFactor.PEER_APPROVAL] +
                    data_quality_score * self.weights[ReputationFactor.DATA_QUALITY] +
                    commit_success_rate * self.weights[ReputationFactor.COMMIT_SUCCESS] +
                    ahj_acceptance_rate * self.weights[ReputationFactor.AHJ_ACCEPTANCE] +
                    review_quality_score * self.weights[ReputationFactor.REVIEW_QUALITY]
                )
                
                # Get total contributions count
                total_contributions = await self._get_total_contributions(contributor_id)
                
                reputation_score = ReputationScore(
                    contributor_id=contributor_id,
                    total_score=total_score,
                    peer_approval_rate=peer_approval_rate,
                    data_quality_score=data_quality_score,
                    commit_success_rate=commit_success_rate,
                    ahj_acceptance_rate=ahj_acceptance_rate,
                    review_quality_score=review_quality_score,
                    total_contributions=total_contributions,
                    last_updated=datetime.utcnow()
                )
                
                # Store reputation score
                await self._store_reputation_score(reputation_score)
                
                logger.info(f"Calculated reputation score for {contributor_id}: {total_score:.2f}")
                return reputation_score
                
        except Exception as e:
            logger.error(f"Error calculating reputation score for {contributor_id}: {e}")
            raise
    
    async def submit_peer_review(self, review_data: Dict[str, Any]) -> PeerReview:
        """
        Submit a peer review for a contribution.
        
        Args:
            review_data: Dictionary containing review information
            
        Returns:
            PeerReview object
        """
        try:
            review = PeerReview(
                review_id=str(uuid.uuid4()),
                contribution_id=review_data["contribution_id"],
                reviewer_id=review_data["reviewer_id"],
                contributor_id=review_data["contributor_id"],
                status=ReviewStatus(review_data["status"]),
                review_score=review_data["review_score"],
                comments=review_data.get("comments", ""),
                created_at=datetime.utcnow()
            )
            
            # Store the review
            await self._store_peer_review(review)
            
            # Update reputation scores for both reviewer and contributor
            await self._update_reputation_after_review(review)
            
            logger.info(f"Peer review submitted: {review.review_id}")
            return review
            
        except Exception as e:
            logger.error(f"Error submitting peer review: {e}")
            raise
    
    async def calculate_revenue_distribution(self, total_revenue: float) -> List[RevenueDistribution]:
        """
        Calculate revenue distribution based on reputation scores.
        
        Args:
            total_revenue: Total revenue to distribute
            
        Returns:
            List of RevenueDistribution objects
        """
        try:
            # Get all contributor reputation scores
            contributor_scores = await self._get_all_reputation_scores()
            
            if not contributor_scores:
                logger.warning("No contributor scores found for revenue distribution")
                return []
            
            # Calculate total reputation score
            total_reputation = sum(score.total_score for score in contributor_scores)
            
            if total_reputation == 0:
                logger.warning("Total reputation score is zero, cannot distribute revenue")
                return []
            
            distributions = []
            
            for score in contributor_scores:
                # Calculate proportional share based on reputation
                reputation_share = score.total_score / total_reputation
                distribution_amount = total_revenue * reputation_share
                
                distribution = RevenueDistribution(
                    distribution_id=str(uuid.uuid4()),
                    contributor_id=score.contributor_id,
                    amount=distribution_amount,
                    distribution_type="reputation_based",
                    reputation_factor=reputation_share,
                    created_at=datetime.utcnow()
                )
                
                distributions.append(distribution)
                
                # Store the distribution
                await self._store_revenue_distribution(distribution)
            
            logger.info(f"Calculated revenue distribution for {len(distributions)} contributors")
            return distributions
            
        except Exception as e:
            logger.error(f"Error calculating revenue distribution: {e}")
            raise
    
    async def get_leaderboard(self, limit: int = 50) -> List[ReputationScore]:
        """
        Get top contributors by reputation score.
        
        Args:
            limit: Maximum number of contributors to return
            
        Returns:
            List of ReputationScore objects sorted by total score
        """
        try:
            scores = await self._get_all_reputation_scores()
            sorted_scores = sorted(scores, key=lambda x: x.total_score, reverse=True)
            return sorted_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            raise
    
    async def get_reputation_analytics(self, contributor_id: str = None) -> Dict[str, Any]:
        """
        Get comprehensive reputation analytics.
        
        Args:
            contributor_id: Optional contributor ID for specific analytics
            
        Returns:
            Dictionary containing analytics data
        """
        try:
            if contributor_id:
                # Individual contributor analytics
                score = await self._get_reputation_score(contributor_id)
                history = await self._get_reputation_history(contributor_id)
                reviews = await self._get_contributor_reviews(contributor_id)
                
                analytics = {
                    "contributor_id": contributor_id,
                    "current_score": score.total_score if score else 0,
                    "score_history": [asdict(h) for h in history],
                    "review_stats": self._calculate_review_stats(reviews),
                    "factor_breakdown": {
                        "peer_approval": score.peer_approval_rate if score else 0,
                        "data_quality": score.data_quality_score if score else 0,
                        "commit_success": score.commit_success_rate if score else 0,
                        "ahj_acceptance": score.ahj_acceptance_rate if score else 0,
                        "review_quality": score.review_quality_score if score else 0
                    } if score else {},
                    "trends": self._calculate_trends(history)
                }
            else:
                # System-wide analytics
                all_scores = await self._get_all_reputation_scores()
                total_contributors = len(all_scores)
                avg_score = sum(s.total_score for s in all_scores) / total_contributors if total_contributors > 0 else 0
                
                analytics = {
                    "total_contributors": total_contributors,
                    "average_score": avg_score,
                    "score_distribution": self._calculate_score_distribution(all_scores),
                    "top_contributors": [asdict(s) for s in all_scores[:10]],
                    "recent_activity": await self._get_recent_activity()
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting reputation analytics: {e}")
            raise
    
    async def _calculate_peer_approval_rate(self, contributor_id: str) -> float:
        """Calculate peer approval rate for a contributor"""
        try:
            # Mock implementation - in real system, query database
            reviews = await self._get_contributor_reviews(contributor_id)
            
            if not reviews:
                return 0.0
            
            approved_reviews = [r for r in reviews if r.status == ReviewStatus.APPROVED]
            approval_rate = len(approved_reviews) / len(reviews)
            
            return min(approval_rate, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating peer approval rate: {e}")
            return 0.0
    
    async def _calculate_data_quality_score(self, contributor_id: str) -> float:
        """Calculate data quality score for a contributor"""
        try:
            # Mock implementation - in real system, analyze contribution quality
            contributions = await self._get_contributor_contributions(contributor_id)
            
            if not contributions:
                return 0.0
            
            quality_scores = []
            for contribution in contributions:
                # Analyze data completeness, accuracy, and usefulness
                completeness = self._assess_data_completeness(contribution)
                accuracy = self._assess_data_accuracy(contribution)
                usefulness = self._assess_data_usefulness(contribution)
                
                avg_quality = (completeness + accuracy + usefulness) / 3
                quality_scores.append(avg_quality)
            
            return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating data quality score: {e}")
            return 0.0
    
    async def _calculate_commit_success_rate(self, contributor_id: str) -> float:
        """Calculate commit success rate for a contributor"""
        try:
            # Mock implementation - in real system, analyze commit history
            commits = await self._get_contributor_commits(contributor_id)
            
            if not commits:
                return 0.0
            
            successful_commits = [c for c in commits if not c.get("has_issues", False)]
            success_rate = len(successful_commits) / len(commits)
            
            return min(success_rate, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating commit success rate: {e}")
            return 0.0
    
    async def _calculate_ahj_acceptance_rate(self, contributor_id: str) -> float:
        """Calculate AHJ acceptance rate for a contributor"""
        try:
            # Mock implementation - in real system, query AHJ acceptance data
            ahj_reviews = await self._get_ahj_reviews(contributor_id)
            
            if not ahj_reviews:
                return 0.0
            
            accepted_reviews = [r for r in ahj_reviews if r.get("status") == "accepted"]
            acceptance_rate = len(accepted_reviews) / len(ahj_reviews)
            
            return min(acceptance_rate, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating AHJ acceptance rate: {e}")
            return 0.0
    
    async def _calculate_review_quality_score(self, contributor_id: str) -> float:
        """Calculate review quality score for a contributor"""
        try:
            # Mock implementation - in real system, analyze review quality
            reviews = await self._get_reviews_by_contributor(contributor_id)
            
            if not reviews:
                return 0.0
            
            quality_scores = []
            for review in reviews:
                # Assess review thoroughness, helpfulness, and accuracy
                thoroughness = self._assess_review_thoroughness(review)
                helpfulness = self._assess_review_helpfulness(review)
                accuracy = self._assess_review_accuracy(review)
                
                avg_quality = (thoroughness + helpfulness + accuracy) / 3
                quality_scores.append(avg_quality)
            
            return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating review quality score: {e}")
            return 0.0
    
    async def _get_total_contributions(self, contributor_id: str) -> int:
        """Get total number of contributions for a contributor"""
        try:
            # Mock implementation - in real system, query database
            contributions = await self._get_contributor_contributions(contributor_id)
            return len(contributions)
            
        except Exception as e:
            logger.error(f"Error getting total contributions: {e}")
            return 0
    
    # Database operations (mock implementations)
    async def _store_reputation_score(self, score: ReputationScore) -> None:
        """Store reputation score in database"""
        # Mock implementation
        pass
    
    async def _store_peer_review(self, review: PeerReview) -> None:
        """Store peer review in database"""
        # Mock implementation
        pass
    
    async def _store_revenue_distribution(self, distribution: RevenueDistribution) -> None:
        """Store revenue distribution in database"""
        # Mock implementation
        pass
    
    async def _get_reputation_score(self, contributor_id: str) -> Optional[ReputationScore]:
        """Get reputation score from database"""
        # Mock implementation
        return None
    
    async def _get_all_reputation_scores(self) -> List[ReputationScore]:
        """Get all reputation scores from database"""
        # Mock implementation
        return []
    
    async def _get_contributor_reviews(self, contributor_id: str) -> List[PeerReview]:
        """Get reviews for a contributor"""
        # Mock implementation
        return []
    
    async def _get_contributor_contributions(self, contributor_id: str) -> List[Dict]:
        """Get contributions for a contributor"""
        # Mock implementation
        return []
    
    async def _get_contributor_commits(self, contributor_id: str) -> List[Dict]:
        """Get commits for a contributor"""
        # Mock implementation
        return []
    
    async def _get_ahj_reviews(self, contributor_id: str) -> List[Dict]:
        """Get AHJ reviews for a contributor"""
        # Mock implementation
        return []
    
    async def _get_reviews_by_contributor(self, contributor_id: str) -> List[PeerReview]:
        """Get reviews submitted by a contributor"""
        # Mock implementation
        return []
    
    async def _get_reputation_history(self, contributor_id: str) -> List[Dict]:
        """Get reputation history for a contributor"""
        # Mock implementation
        return []
    
    async def _get_recent_activity(self) -> List[Dict]:
        """Get recent reputation activity"""
        # Mock implementation
        return []
    
    async def _update_reputation_after_review(self, review: PeerReview) -> None:
        """Update reputation scores after a review"""
        # Mock implementation
        pass
    
    # Assessment helper methods
    def _assess_data_completeness(self, contribution: Dict) -> float:
        """Assess data completeness"""
        # Mock implementation
        return 0.8
    
    def _assess_data_accuracy(self, contribution: Dict) -> float:
        """Assess data accuracy"""
        # Mock implementation
        return 0.9
    
    def _assess_data_usefulness(self, contribution: Dict) -> float:
        """Assess data usefulness"""
        # Mock implementation
        return 0.85
    
    def _assess_review_thoroughness(self, review: PeerReview) -> float:
        """Assess review thoroughness"""
        # Mock implementation
        return 0.8
    
    def _assess_review_helpfulness(self, review: PeerReview) -> float:
        """Assess review helpfulness"""
        # Mock implementation
        return 0.85
    
    def _assess_review_accuracy(self, review: PeerReview) -> float:
        """Assess review accuracy"""
        # Mock implementation
        return 0.9
    
    def _calculate_review_stats(self, reviews: List[PeerReview]) -> Dict[str, Any]:
        """Calculate review statistics"""
        if not reviews:
            return {"total_reviews": 0, "approval_rate": 0.0, "avg_score": 0.0}
        
        total_reviews = len(reviews)
        approved_reviews = len([r for r in reviews if r.status == ReviewStatus.APPROVED])
        approval_rate = approved_reviews / total_reviews
        avg_score = sum(r.review_score for r in reviews) / total_reviews
        
        return {
            "total_reviews": total_reviews,
            "approval_rate": approval_rate,
            "avg_score": avg_score
        }
    
    def _calculate_trends(self, history: List[Dict]) -> Dict[str, Any]:
        """Calculate reputation trends"""
        if not history:
            return {"trend": "stable", "change_rate": 0.0}
        
        # Mock trend calculation
        return {"trend": "increasing", "change_rate": 0.05}
    
    def _calculate_score_distribution(self, scores: List[ReputationScore]) -> Dict[str, int]:
        """Calculate score distribution"""
        distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}
        
        for score in scores:
            if score.total_score >= 0.9:
                distribution["excellent"] += 1
            elif score.total_score >= 0.7:
                distribution["good"] += 1
            elif score.total_score >= 0.5:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1
        
        return distribution 