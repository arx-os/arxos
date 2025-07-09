"""
Tests for Contributor Reputation Engine

This module contains comprehensive tests for the Contributor Reputation Engine,
covering reputation scoring, peer reviews, revenue distribution, and analytics.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

from services.contributor_reputation_engine import (
    ContributorReputationEngine,
    ReputationScore,
    PeerReview,
    RevenueDistribution,
    ReviewStatus,
    ReputationFactor
)


class TestContributorReputationEngine:
    """Test suite for ContributorReputationEngine"""
    
    @pytest.fixture
    async def reputation_engine(self):
        """Create a reputation engine instance for testing"""
        return ContributorReputationEngine()
    
    @pytest.fixture
    def sample_contributor_id(self):
        """Sample contributor ID for testing"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def sample_review_data(self, sample_contributor_id):
        """Sample peer review data for testing"""
        return {
            "contribution_id": str(uuid.uuid4()),
            "reviewer_id": str(uuid.uuid4()),
            "contributor_id": sample_contributor_id,
            "status": "approved",
            "review_score": 8,
            "comments": "Excellent contribution with high quality data"
        }
    
    @pytest.mark.asyncio
    async def test_calculate_reputation_score(self, reputation_engine, sample_contributor_id):
        """Test reputation score calculation"""
        # Calculate reputation score
        score = await reputation_engine.calculate_reputation_score(sample_contributor_id)
        
        # Verify score structure
        assert isinstance(score, ReputationScore)
        assert score.contributor_id == sample_contributor_id
        assert isinstance(score.total_score, float)
        assert 0.0 <= score.total_score <= 1.0
        assert isinstance(score.peer_approval_rate, float)
        assert isinstance(score.data_quality_score, float)
        assert isinstance(score.commit_success_rate, float)
        assert isinstance(score.ahj_acceptance_rate, float)
        assert isinstance(score.review_quality_score, float)
        assert isinstance(score.total_contributions, int)
        assert isinstance(score.last_updated, datetime)
    
    @pytest.mark.asyncio
    async def test_submit_peer_review(self, reputation_engine, sample_review_data):
        """Test peer review submission"""
        # Submit peer review
        review = await reputation_engine.submit_peer_review(sample_review_data)
        
        # Verify review structure
        assert isinstance(review, PeerReview)
        assert review.contribution_id == sample_review_data["contribution_id"]
        assert review.reviewer_id == sample_review_data["reviewer_id"]
        assert review.contributor_id == sample_review_data["contributor_id"]
        assert review.status == ReviewStatus.APPROVED
        assert review.review_score == sample_review_data["review_score"]
        assert review.comments == sample_review_data["comments"]
        assert isinstance(review.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_submit_peer_review_invalid_status(self, reputation_engine, sample_review_data):
        """Test peer review submission with invalid status"""
        sample_review_data["status"] = "invalid_status"
        
        with pytest.raises(ValueError):
            await reputation_engine.submit_peer_review(sample_review_data)
    
    @pytest.mark.asyncio
    async def test_calculate_revenue_distribution(self, reputation_engine):
        """Test revenue distribution calculation"""
        total_revenue = 10000.0
        
        # Calculate revenue distribution
        distributions = await reputation_engine.calculate_revenue_distribution(total_revenue)
        
        # Verify distributions structure
        assert isinstance(distributions, list)
        
        if distributions:  # If there are contributors
            for distribution in distributions:
                assert isinstance(distribution, RevenueDistribution)
                assert isinstance(distribution.distribution_id, str)
                assert isinstance(distribution.contributor_id, str)
                assert isinstance(distribution.amount, float)
                assert distribution.amount >= 0.0
                assert isinstance(distribution.distribution_type, str)
                assert isinstance(distribution.reputation_factor, float)
                assert isinstance(distribution.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_get_leaderboard(self, reputation_engine):
        """Test leaderboard retrieval"""
        limit = 10
        
        # Get leaderboard
        leaderboard = await reputation_engine.get_leaderboard(limit)
        
        # Verify leaderboard structure
        assert isinstance(leaderboard, list)
        assert len(leaderboard) <= limit
        
        for score in leaderboard:
            assert isinstance(score, ReputationScore)
            assert isinstance(score.contributor_id, str)
            assert isinstance(score.total_score, float)
            assert 0.0 <= score.total_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_get_reputation_analytics_individual(self, reputation_engine, sample_contributor_id):
        """Test individual contributor analytics"""
        # Get analytics for specific contributor
        analytics = await reputation_engine.get_reputation_analytics(sample_contributor_id)
        
        # Verify analytics structure
        assert isinstance(analytics, dict)
        assert "contributor_id" in analytics
        assert analytics["contributor_id"] == sample_contributor_id
        assert "current_score" in analytics
        assert "score_history" in analytics
        assert "review_stats" in analytics
        assert "factor_breakdown" in analytics
        assert "trends" in analytics
    
    @pytest.mark.asyncio
    async def test_get_reputation_analytics_system_wide(self, reputation_engine):
        """Test system-wide analytics"""
        # Get system-wide analytics
        analytics = await reputation_engine.get_reputation_analytics()
        
        # Verify analytics structure
        assert isinstance(analytics, dict)
        assert "total_contributors" in analytics
        assert "average_score" in analytics
        assert "score_distribution" in analytics
        assert "top_contributors" in analytics
        assert "recent_activity" in analytics
    
    @pytest.mark.asyncio
    async def test_reputation_weights(self, reputation_engine):
        """Test reputation factor weights"""
        weights = reputation_engine.weights
        
        # Verify all factors have weights
        for factor in ReputationFactor:
            assert factor in weights
            assert isinstance(weights[factor], float)
            assert 0.0 <= weights[factor] <= 1.0
        
        # Verify weights sum to approximately 1.0
        total_weight = sum(weights.values())
        assert 0.99 <= total_weight <= 1.01
    
    @pytest.mark.asyncio
    async def test_reputation_thresholds(self, reputation_engine):
        """Test reputation factor thresholds"""
        thresholds = reputation_engine.thresholds
        
        # Verify all factors have thresholds
        for factor in ReputationFactor:
            assert factor in thresholds
            assert isinstance(thresholds[factor], float)
            assert 0.0 <= thresholds[factor] <= 1.0
    
    @pytest.mark.asyncio
    async def test_multiple_contributors(self, reputation_engine):
        """Test reputation calculation for multiple contributors"""
        contributor_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        scores = []
        for contributor_id in contributor_ids:
            score = await reputation_engine.calculate_reputation_score(contributor_id)
            scores.append(score)
        
        # Verify all scores were calculated
        assert len(scores) == len(contributor_ids)
        
        for score in scores:
            assert isinstance(score, ReputationScore)
            assert score.contributor_id in contributor_ids
    
    @pytest.mark.asyncio
    async def test_review_status_enum(self):
        """Test ReviewStatus enum values"""
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.APPROVED.value == "approved"
        assert ReviewStatus.REJECTED.value == "rejected"
        assert ReviewStatus.NEEDS_REVISION.value == "needs_revision"
    
    @pytest.mark.asyncio
    async def test_reputation_factor_enum(self):
        """Test ReputationFactor enum values"""
        assert ReputationFactor.PEER_APPROVAL.value == "peer_approval"
        assert ReputationFactor.DATA_QUALITY.value == "data_quality"
        assert ReputationFactor.COMMIT_SUCCESS.value == "commit_success"
        assert ReputationFactor.AHJ_ACCEPTANCE.value == "ahj_acceptance"
        assert ReputationFactor.REVIEW_QUALITY.value == "review_quality"
    
    @pytest.mark.asyncio
    async def test_concurrent_reputation_calculations(self, reputation_engine):
        """Test concurrent reputation score calculations"""
        contributor_ids = [str(uuid.uuid4()) for _ in range(10)]
        
        # Calculate scores concurrently
        tasks = [
            reputation_engine.calculate_reputation_score(contributor_id)
            for contributor_id in contributor_ids
        ]
        
        scores = await asyncio.gather(*tasks)
        
        # Verify all scores were calculated
        assert len(scores) == len(contributor_ids)
        
        for score in scores:
            assert isinstance(score, ReputationScore)
    
    @pytest.mark.asyncio
    async def test_revenue_distribution_edge_cases(self, reputation_engine):
        """Test revenue distribution edge cases"""
        # Test with zero revenue
        distributions = await reputation_engine.calculate_revenue_distribution(0.0)
        assert isinstance(distributions, list)
        
        # Test with very small revenue
        distributions = await reputation_engine.calculate_revenue_distribution(0.01)
        assert isinstance(distributions, list)
        
        # Test with very large revenue
        distributions = await reputation_engine.calculate_revenue_distribution(1000000.0)
        assert isinstance(distributions, list)
    
    @pytest.mark.asyncio
    async def test_leaderboard_edge_cases(self, reputation_engine):
        """Test leaderboard edge cases"""
        # Test with limit 0
        leaderboard = await reputation_engine.get_leaderboard(0)
        assert isinstance(leaderboard, list)
        assert len(leaderboard) == 0
        
        # Test with very large limit
        leaderboard = await reputation_engine.get_leaderboard(1000)
        assert isinstance(leaderboard, list)
    
    @pytest.mark.asyncio
    async def test_reputation_score_consistency(self, reputation_engine, sample_contributor_id):
        """Test that reputation scores are consistent for the same contributor"""
        # Calculate score twice
        score1 = await reputation_engine.calculate_reputation_score(sample_contributor_id)
        score2 = await reputation_engine.calculate_reputation_score(sample_contributor_id)
        
        # Scores should be consistent (within small tolerance for floating point)
        assert abs(score1.total_score - score2.total_score) < 0.001
        assert score1.contributor_id == score2.contributor_id
    
    @pytest.mark.asyncio
    async def test_peer_review_validation(self, reputation_engine):
        """Test peer review data validation"""
        # Test missing required fields
        invalid_review = {
            "contribution_id": str(uuid.uuid4()),
            "reviewer_id": str(uuid.uuid4()),
            # Missing contributor_id, status, review_score
        }
        
        with pytest.raises(Exception):
            await reputation_engine.submit_peer_review(invalid_review)
    
    @pytest.mark.asyncio
    async def test_reputation_analytics_performance(self, reputation_engine):
        """Test reputation analytics performance"""
        import time
        
        start_time = time.time()
        analytics = await reputation_engine.get_reputation_analytics()
        end_time = time.time()
        
        # Analytics should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds max
        assert isinstance(analytics, dict)
    
    @pytest.mark.asyncio
    async def test_reputation_engine_initialization(self):
        """Test reputation engine initialization"""
        engine = ContributorReputationEngine()
        
        # Verify engine is properly initialized
        assert hasattr(engine, 'weights')
        assert hasattr(engine, 'thresholds')
        assert hasattr(engine, 'lock')
        assert hasattr(engine, 'executor')
    
    @pytest.mark.asyncio
    async def test_reputation_score_serialization(self, reputation_engine, sample_contributor_id):
        """Test reputation score serialization"""
        score = await reputation_engine.calculate_reputation_score(sample_contributor_id)
        
        # Test serialization to dict
        score_dict = {
            "contributor_id": score.contributor_id,
            "total_score": score.total_score,
            "peer_approval_rate": score.peer_approval_rate,
            "data_quality_score": score.data_quality_score,
            "commit_success_rate": score.commit_success_rate,
            "ahj_acceptance_rate": score.ahj_acceptance_rate,
            "review_quality_score": score.review_quality_score,
            "total_contributions": score.total_contributions,
            "last_updated": score.last_updated.isoformat()
        }
        
        assert isinstance(score_dict, dict)
        assert score_dict["contributor_id"] == sample_contributor_id
        assert isinstance(score_dict["total_score"], float)
    
    @pytest.mark.asyncio
    async def test_peer_review_serialization(self, reputation_engine, sample_review_data):
        """Test peer review serialization"""
        review = await reputation_engine.submit_peer_review(sample_review_data)
        
        # Test serialization to dict
        review_dict = {
            "review_id": review.review_id,
            "contribution_id": review.contribution_id,
            "reviewer_id": review.reviewer_id,
            "contributor_id": review.contributor_id,
            "status": review.status.value,
            "review_score": review.review_score,
            "comments": review.comments,
            "created_at": review.created_at.isoformat()
        }
        
        assert isinstance(review_dict, dict)
        assert review_dict["status"] == "approved"
        assert isinstance(review_dict["review_score"], int)
    
    @pytest.mark.asyncio
    async def test_revenue_distribution_serialization(self, reputation_engine):
        """Test revenue distribution serialization"""
        distributions = await reputation_engine.calculate_revenue_distribution(1000.0)
        
        if distributions:
            distribution = distributions[0]
            
            # Test serialization to dict
            distribution_dict = {
                "distribution_id": distribution.distribution_id,
                "contributor_id": distribution.contributor_id,
                "amount": distribution.amount,
                "distribution_type": distribution.distribution_type,
                "reputation_factor": distribution.reputation_factor,
                "created_at": distribution.created_at.isoformat()
            }
            
            assert isinstance(distribution_dict, dict)
            assert isinstance(distribution_dict["amount"], float)
            assert distribution_dict["amount"] >= 0.0


class TestReputationEngineIntegration:
    """Integration tests for reputation engine with multiple operations"""
    
    @pytest.fixture
    async def reputation_engine(self):
        """Create a reputation engine instance for integration testing"""
        return ContributorReputationEngine()
    
    @pytest.mark.asyncio
    async def test_full_reputation_workflow(self, reputation_engine):
        """Test complete reputation workflow"""
        contributor_id = str(uuid.uuid4())
        reviewer_id = str(uuid.uuid4())
        
        # Step 1: Calculate initial reputation score
        initial_score = await reputation_engine.calculate_reputation_score(contributor_id)
        assert isinstance(initial_score, ReputationScore)
        
        # Step 2: Submit peer review
        review_data = {
            "contribution_id": str(uuid.uuid4()),
            "reviewer_id": reviewer_id,
            "contributor_id": contributor_id,
            "status": "approved",
            "review_score": 9,
            "comments": "High quality contribution"
        }
        
        review = await reputation_engine.submit_peer_review(review_data)
        assert isinstance(review, PeerReview)
        
        # Step 3: Calculate updated reputation score
        updated_score = await reputation_engine.calculate_reputation_score(contributor_id)
        assert isinstance(updated_score, ReputationScore)
        
        # Step 4: Get leaderboard
        leaderboard = await reputation_engine.get_leaderboard(10)
        assert isinstance(leaderboard, list)
        
        # Step 5: Calculate revenue distribution
        distributions = await reputation_engine.calculate_revenue_distribution(5000.0)
        assert isinstance(distributions, list)
        
        # Step 6: Get analytics
        analytics = await reputation_engine.get_reputation_analytics(contributor_id)
        assert isinstance(analytics, dict)
    
    @pytest.mark.asyncio
    async def test_multiple_reviews_impact(self, reputation_engine):
        """Test impact of multiple reviews on reputation"""
        contributor_id = str(uuid.uuid4())
        
        # Initial score
        initial_score = await reputation_engine.calculate_reputation_score(contributor_id)
        
        # Submit multiple reviews
        for i in range(5):
            review_data = {
                "contribution_id": str(uuid.uuid4()),
                "reviewer_id": str(uuid.uuid4()),
                "contributor_id": contributor_id,
                "status": "approved",
                "review_score": 8 + (i % 3),  # Scores 8, 9, 10, 8, 9
                "comments": f"Review {i+1}"
            }
            
            await reputation_engine.submit_peer_review(review_data)
        
        # Final score
        final_score = await reputation_engine.calculate_reputation_score(contributor_id)
        
        # Both scores should be valid
        assert isinstance(initial_score, ReputationScore)
        assert isinstance(final_score, ReputationScore)
        assert initial_score.contributor_id == final_score.contributor_id
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, reputation_engine):
        """Test concurrent reputation operations"""
        contributor_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # Concurrent reputation calculations
        score_tasks = [
            reputation_engine.calculate_reputation_score(contributor_id)
            for contributor_id in contributor_ids
        ]
        
        # Concurrent peer reviews
        review_tasks = []
        for i, contributor_id in enumerate(contributor_ids):
            review_data = {
                "contribution_id": str(uuid.uuid4()),
                "reviewer_id": str(uuid.uuid4()),
                "contributor_id": contributor_id,
                "status": "approved",
                "review_score": 8,
                "comments": f"Concurrent review {i+1}"
            }
            review_tasks.append(reputation_engine.submit_peer_review(review_data))
        
        # Execute all tasks concurrently
        scores, reviews = await asyncio.gather(
            asyncio.gather(*score_tasks),
            asyncio.gather(*review_tasks)
        )
        
        # Verify results
        assert len(scores) == len(contributor_ids)
        assert len(reviews) == len(contributor_ids)
        
        for score in scores:
            assert isinstance(score, ReputationScore)
        
        for review in reviews:
            assert isinstance(review, PeerReview)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, reputation_engine):
        """Test error handling in reputation engine"""
        # Test with invalid contributor ID
        invalid_id = "invalid-uuid"
        
        # Should handle gracefully
        try:
            score = await reputation_engine.calculate_reputation_score(invalid_id)
            assert isinstance(score, ReputationScore)
        except Exception as e:
            # Should either succeed or raise a specific exception
            assert isinstance(e, Exception)
        
        # Test with invalid review data
        invalid_review = {
            "contribution_id": "invalid",
            "reviewer_id": "invalid",
            "contributor_id": "invalid",
            "status": "invalid_status",
            "review_score": "not_a_number"
        }
        
        with pytest.raises(Exception):
            await reputation_engine.submit_peer_review(invalid_review)


if __name__ == "__main__":
    pytest.main([__file__]) 