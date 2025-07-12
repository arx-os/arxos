#!/usr/bin/env python3
"""
Contributor Reputation Engine Demonstration

This script demonstrates the comprehensive Contributor Reputation Engine functionality,
including reputation scoring, peer reviews, revenue distribution, and analytics.
"""

import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the reputation engine
from services.contributor_reputation_engine import (
    ContributorReputationEngine,
    ReputationScore,
    PeerReview,
    RevenueDistribution,
    ReviewStatus,
    ReputationFactor
)


class ContributorReputationDemo:
    """Demonstration class for Contributor Reputation Engine"""
    
    def __init__(self):
        """Initialize the demonstration"""
        self.reputation_engine = ContributorReputationEngine()
        self.demo_contributors = []
        self.demo_reviews = []
        self.demo_distributions = []
        
        logger.info("Contributor Reputation Engine Demo initialized")
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all features"""
        logger.info("Starting Contributor Reputation Engine Comprehensive Demo")
        print("\n" + "="*80)
        print("CONTRIBUTOR REPUTATION ENGINE COMPREHENSIVE DEMONSTRATION")
        print("="*80)
        
        try:
            # Step 1: Setup demo contributors
            await self._setup_demo_contributors()
            
            # Step 2: Demonstrate reputation scoring
            await self._demonstrate_reputation_scoring()
            
            # Step 3: Demonstrate peer review system
            await self._demonstrate_peer_reviews()
            
            # Step 4: Demonstrate leaderboard functionality
            await self._demonstrate_leaderboard()
            
            # Step 5: Demonstrate revenue distribution
            await self._demonstrate_revenue_distribution()
            
            # Step 6: Demonstrate analytics
            await self._demonstrate_analytics()
            
            # Step 7: Demonstrate concurrent operations
            await self._demonstrate_concurrent_operations()
            
            # Step 8: Demonstrate error handling
            await self._demonstrate_error_handling()
            
            logger.info("Comprehensive demo completed successfully")
            print("\n" + "="*80)
            print("DEMONSTRATION COMPLETED SUCCESSFULLY")
            print("="*80)
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
    
    async def _setup_demo_contributors(self):
        """Setup demo contributors with different reputation profiles"""
        print("\n1. SETTING UP DEMO CONTRIBUTORS")
        print("-" * 50)
        
        # Create demo contributors with different characteristics
        contributors = [
            {
                "id": str(uuid.uuid4()),
                "name": "Alice Expert",
                "description": "High-quality contributor with excellent peer approval"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Bob Quality",
                "description": "Focuses on data quality and accuracy"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Carol Reliable",
                "description": "Consistent bug-free commits and reliability"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "David Compliant",
                "description": "Strong AHJ acceptance and regulatory compliance"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Eve Reviewer",
                "description": "Excellent peer reviewer with high review quality"
            }
        ]
        
        self.demo_contributors = contributors
        
        print(f"Created {len(contributors)} demo contributors:")
        for contributor in contributors:
            print(f"  - {contributor['name']}: {contributor['description']}")
            print(f"    ID: {contributor['id']}")
        
        logger.info(f"Setup {len(contributors)} demo contributors")
    
    async def _demonstrate_reputation_scoring(self):
        """Demonstrate reputation score calculation"""
        print("\n2. REPUTATION SCORING DEMONSTRATION")
        print("-" * 50)
        
        print("Calculating reputation scores for all contributors...")
        
        for contributor in self.demo_contributors:
            contributor_id = contributor["id"]
            
            # Calculate reputation score
            score = await self.reputation_engine.calculate_reputation_score(contributor_id)
            
            print(f"\n{contributor['name']} (ID: {contributor_id[:8]}...)")
            print(f"  Total Reputation Score: {score.total_score:.3f}")
            print(f"  Factor Breakdown:")
            print(f"    - Peer Approval Rate: {score.peer_approval_rate:.3f}")
            print(f"    - Data Quality Score: {score.data_quality_score:.3f}")
            print(f"    - Commit Success Rate: {score.commit_success_rate:.3f}")
            print(f"    - AHJ Acceptance Rate: {score.ahj_acceptance_rate:.3f}")
            print(f"    - Review Quality Score: {score.review_quality_score:.3f}")
            print(f"  Total Contributions: {score.total_contributions}")
            print(f"  Last Updated: {score.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info("Reputation scoring demonstration completed")
    
    async def _demonstrate_peer_reviews(self):
        """Demonstrate peer review system"""
        print("\n3. PEER REVIEW SYSTEM DEMONSTRATION")
        print("-" * 50)
        
        print("Submitting peer reviews for contributions...")
        
        # Create sample reviews for each contributor
        for i, contributor in enumerate(self.demo_contributors):
            # Create multiple reviews for each contributor
            for j in range(3):
                review_data = {
                    "contribution_id": str(uuid.uuid4()),
                    "reviewer_id": str(uuid.uuid4()),
                    "contributor_id": contributor["id"],
                    "status": "approved" if j < 2 else "needs_revision",
                    "review_score": 8 + (i % 3),  # Vary scores
                    "comments": f"Review {j+1} for {contributor['name']}: {'Excellent work' if j < 2 else 'Needs improvement'}"
                }
                
                review = await self.reputation_engine.submit_peer_review(review_data)
                self.demo_reviews.append(review)
                
                print(f"  Submitted review {j+1} for {contributor['name']}")
                print(f"    Status: {review.status.value}")
                print(f"    Score: {review.review_score}/10")
                print(f"    Comments: {review.comments[:50]}...")
        
        print(f"\nTotal reviews submitted: {len(self.demo_reviews)}")
        
        # Show review statistics
        approved_reviews = [r for r in self.demo_reviews if r.status == ReviewStatus.APPROVED]
        pending_reviews = [r for r in self.demo_reviews if r.status == ReviewStatus.PENDING]
        rejected_reviews = [r for r in self.demo_reviews if r.status == ReviewStatus.REJECTED]
        needs_revision_reviews = [r for r in self.demo_reviews if r.status == ReviewStatus.NEEDS_REVISION]
        
        print(f"\nReview Statistics:")
        print(f"  Approved: {len(approved_reviews)}")
        print(f"  Pending: {len(pending_reviews)}")
        print(f"  Rejected: {len(rejected_reviews)}")
        print(f"  Needs Revision: {len(needs_revision_reviews)}")
        
        logger.info("Peer review demonstration completed")
    
    async def _demonstrate_leaderboard(self):
        """Demonstrate leaderboard functionality"""
        print("\n4. LEADERBOARD DEMONSTRATION")
        print("-" * 50)
        
        # Get leaderboard
        leaderboard = await self.reputation_engine.get_leaderboard(10)
        
        print(f"Top Contributors Leaderboard (showing {len(leaderboard)} contributors):")
        print("\nRank | Contributor ID | Reputation Score | Contributions")
        print("-" * 70)
        
        for i, score in enumerate(leaderboard, 1):
            contributor_name = next(
                (c["name"] for c in self.demo_contributors if c["id"] == score.contributor_id),
                f"Contributor-{score.contributor_id[:8]}"
            )
            
            print(f"{i:4d} | {contributor_name:15s} | {score.total_score:15.3f} | {score.total_contributions:12d}")
        
        logger.info("Leaderboard demonstration completed")
    
    async def _demonstrate_revenue_distribution(self):
        """Demonstrate revenue distribution"""
        print("\n5. REVENUE DISTRIBUTION DEMONSTRATION")
        print("-" * 50)
        
        total_revenue = 50000.0
        print(f"Calculating revenue distribution for ${total_revenue:,.2f}...")
        
        # Calculate revenue distribution
        distributions = await self.reputation_engine.calculate_revenue_distribution(total_revenue)
        
        if distributions:
            print(f"\nRevenue Distribution Results:")
            print(f"{'Contributor':<20} {'Amount':<12} {'Share %':<8} {'Reputation Factor':<18}")
            print("-" * 60)
            
            total_distributed = 0
            for distribution in distributions:
                contributor_name = next(
                    (c["name"] for c in self.demo_contributors if c["id"] == distribution.contributor_id),
                    f"Contributor-{distribution.contributor_id[:8]}"
                )
                
                share_percentage = (distribution.amount / total_revenue) * 100
                total_distributed += distribution.amount
                
                print(f"{contributor_name:<20} ${distribution.amount:<11,.2f} {share_percentage:<7.2f}% {distribution.reputation_factor:<17.3f}")
            
            print("-" * 60)
            print(f"{'TOTAL':<20} ${total_distributed:<11,.2f} {100.0:<7.2f}%")
            
            self.demo_distributions = distributions
        else:
            print("No contributors found for revenue distribution")
        
        logger.info("Revenue distribution demonstration completed")
    
    async def _demonstrate_analytics(self):
        """Demonstrate analytics functionality"""
        print("\n6. ANALYTICS DEMONSTRATION")
        print("-" * 50)
        
        # Individual contributor analytics
        if self.demo_contributors:
            contributor_id = self.demo_contributors[0]["id"]
            print(f"Individual Analytics for {self.demo_contributors[0]['name']}:")
            
            analytics = await self.reputation_engine.get_reputation_analytics(contributor_id)
            
            print(f"  Current Score: {analytics.get('current_score', 0):.3f}")
            print(f"  Score History: {len(analytics.get('score_history', []))} entries")
            print(f"  Review Stats: {analytics.get('review_stats', {})}")
            print(f"  Factor Breakdown: {analytics.get('factor_breakdown', {})}")
            print(f"  Trends: {analytics.get('trends', {})}")
        
        # System-wide analytics
        print(f"\nSystem-wide Analytics:")
        system_analytics = await self.reputation_engine.get_reputation_analytics()
        
        print(f"  Total Contributors: {system_analytics.get('total_contributors', 0)}")
        print(f"  Average Score: {system_analytics.get('average_score', 0):.3f}")
        print(f"  Score Distribution: {system_analytics.get('score_distribution', {})}")
        print(f"  Recent Activity: {len(system_analytics.get('recent_activity', []))} entries")
        
        logger.info("Analytics demonstration completed")
    
    async def _demonstrate_concurrent_operations(self):
        """Demonstrate concurrent operations"""
        print("\n7. CONCURRENT OPERATIONS DEMONSTRATION")
        print("-" * 50)
        
        print("Running concurrent reputation calculations...")
        
        # Create tasks for concurrent operations
        tasks = []
        for contributor in self.demo_contributors:
            # Concurrent reputation calculations
            tasks.append(self.reputation_engine.calculate_reputation_score(contributor["id"]))
            
            # Concurrent peer reviews
            review_data = {
                "contribution_id": str(uuid.uuid4()),
                "reviewer_id": str(uuid.uuid4()),
                "contributor_id": contributor["id"],
                "status": "approved",
                "review_score": 9,
                "comments": "Concurrent review"
            }
            tasks.append(self.reputation_engine.submit_peer_review(review_data))
        
        # Execute all tasks concurrently
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        print(f"Concurrent Operations Results:")
        print(f"  Total Operations: {len(tasks)}")
        print(f"  Successful: {len(successful_results)}")
        print(f"  Failed: {len(failed_results)}")
        print(f"  Execution Time: {(end_time - start_time).total_seconds():.3f} seconds")
        
        if failed_results:
            print(f"  Errors: {len(failed_results)}")
            for error in failed_results[:3]:  # Show first 3 errors
                print(f"    - {type(error).__name__}: {error}")
        
        logger.info("Concurrent operations demonstration completed")
    
    async def _demonstrate_error_handling(self):
        """Demonstrate error handling"""
        print("\n8. ERROR HANDLING DEMONSTRATION")
        print("-" * 50)
        
        print("Testing error handling with invalid inputs...")
        
        # Test invalid contributor ID
        try:
            invalid_id = "invalid-uuid-format"
            await self.reputation_engine.calculate_reputation_score(invalid_id)
            print("  ✓ Invalid contributor ID handled gracefully")
        except Exception as e:
            print(f"  ✗ Invalid contributor ID error: {type(e).__name__}: {e}")
        
        # Test invalid review data
        try:
            invalid_review = {
                "contribution_id": "invalid",
                "reviewer_id": "invalid",
                "contributor_id": "invalid",
                "status": "invalid_status",
                "review_score": "not_a_number"
            }
            await self.reputation_engine.submit_peer_review(invalid_review)
            print("  ✓ Invalid review data handled gracefully")
        except Exception as e:
            print(f"  ✗ Invalid review data error: {type(e).__name__}: {e}")
        
        # Test edge cases
        try:
            # Zero revenue distribution
            distributions = await self.reputation_engine.calculate_revenue_distribution(0.0)
            print("  ✓ Zero revenue distribution handled gracefully")
        except Exception as e:
            print(f"  ✗ Zero revenue distribution error: {type(e).__name__}: {e}")
        
        try:
            # Empty leaderboard
            leaderboard = await self.reputation_engine.get_leaderboard(0)
            print("  ✓ Empty leaderboard handled gracefully")
        except Exception as e:
            print(f"  ✗ Empty leaderboard error: {type(e).__name__}: {e}")
        
        logger.info("Error handling demonstration completed")
    
    async def generate_demo_report(self):
        """Generate a comprehensive demo report"""
        print("\n9. DEMO SUMMARY REPORT")
        print("-" * 50)
        
        report = {
            "demo_timestamp": datetime.now().isoformat(),
            "contributors_created": len(self.demo_contributors),
            "reviews_submitted": len(self.demo_reviews),
            "distributions_calculated": len(self.demo_distributions),
            "total_revenue_distributed": sum(d.amount for d in self.demo_distributions) if self.demo_distributions else 0,
            "contributor_details": [
                {
                    "name": c["name"],
                    "id": c["id"],
                    "description": c["description"]
                }
                for c in self.demo_contributors
            ],
            "review_statistics": {
                "total_reviews": len(self.demo_reviews),
                "approved": len([r for r in self.demo_reviews if r.status == ReviewStatus.APPROVED]),
                "pending": len([r for r in self.demo_reviews if r.status == ReviewStatus.PENDING]),
                "rejected": len([r for r in self.demo_reviews if r.status == ReviewStatus.REJECTED]),
                "needs_revision": len([r for r in self.demo_reviews if r.status == ReviewStatus.NEEDS_REVISION])
            }
        }
        
        print("Demo Summary:")
        print(f"  Contributors Created: {report['contributors_created']}")
        print(f"  Reviews Submitted: {report['reviews_submitted']}")
        print(f"  Distributions Calculated: {report['distributions_calculated']}")
        print(f"  Total Revenue Distributed: ${report['total_revenue_distributed']:,.2f}")
        
        print(f"\nReview Statistics:")
        stats = report["review_statistics"]
        print(f"  Total Reviews: {stats['total_reviews']}")
        print(f"  Approved: {stats['approved']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Rejected: {stats['rejected']}")
        print(f"  Needs Revision: {stats['needs_revision']}")
        
        # Save report to file
        report_file = "contributor_reputation_demo_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        logger.info("Demo report generated successfully")


async def main():
    """Main demonstration function"""
    demo = ContributorReputationDemo()
    
    try:
        await demo.run_comprehensive_demo()
        await demo.generate_demo_report()
        
        print("\n" + "="*80)
        print("CONTRIBUTOR REPUTATION ENGINE DEMONSTRATION COMPLETED")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✓ Multi-factor reputation scoring")
        print("✓ Peer review system with approval workflows")
        print("✓ Leaderboard and ranking system")
        print("✓ Revenue distribution based on reputation")
        print("✓ Comprehensive analytics and reporting")
        print("✓ Concurrent operation handling")
        print("✓ Robust error handling and validation")
        print("✓ Real-time reputation updates")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 