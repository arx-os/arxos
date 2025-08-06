"""
Mock BILT Token System Repository Implementations

Mock implementations that don't require SQLAlchemy dependencies.
This allows the BILT repositories to be developed and tested without database dependencies.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal

from domain.repositories import (
    ContributionRepository,
    RevenueRepository,
    DividendRepository,
    VerificationRepository,
)

logger = logging.getLogger(__name__)


class MockSQLAlchemyContributionRepository(ContributionRepository):
    """Mock SQLAlchemy implementation of ContributionRepository."""

    def __init__(self, session=None):
        """Initialize with optional session (ignored in mock)"""
        self.session = session
        self.mock_data = {}
        logger.info("Mock Contribution Repository initialized")

    def create(self, contribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contribution record (mock)"""
        try:
            contribution_id = f"contrib_{datetime.utcnow().timestamp()}"
            contribution_data["id"] = contribution_id
            contribution_data["created_at"] = datetime.utcnow()

            self.mock_data[contribution_id] = contribution_data

            logger.info(f"Mock created contribution: {contribution_id}")
            return contribution_data

        except Exception as e:
            logger.error(f"Error creating mock contribution: {str(e)}")
            raise

    def get_by_id(self, contribution_id: str) -> Optional[Dict[str, Any]]:
        """Get contribution by ID (mock)"""
        try:
            return self.mock_data.get(contribution_id)

        except Exception as e:
            logger.error(f"Error getting mock contribution by ID: {str(e)}")
            return None

    def get_by_contributor(self, contributor_wallet: str) -> List[Dict[str, Any]]:
        """Get contributions by contributor wallet (mock)"""
        try:
            return [
                data
                for data in self.mock_data.values()
                if data.get("contributor_wallet") == contributor_wallet
            ]

        except Exception as e:
            logger.error(f"Error getting mock contributions by contributor: {str(e)}")
            return []

    def get_by_biltobject_hash(self, biltobject_hash: str) -> Optional[Dict[str, Any]]:
        """Get contribution by building object hash (mock)"""
        try:
            for data in self.mock_data.values():
                if data.get("biltobject_hash") == biltobject_hash:
                    return data
            return None

        except Exception as e:
            logger.error(f"Error getting mock contribution by object hash: {str(e)}")
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all contributions (mock)"""
        try:
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting all mock contributions: {str(e)}")
            return []

    def update(self, contribution_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a contribution (mock)"""
        try:
            if contribution_id in self.mock_data:
                data["id"] = contribution_id
                data["updated_at"] = datetime.utcnow()
                self.mock_data[contribution_id] = data

                logger.info(f"Mock updated contribution: {contribution_id}")
                return data
            else:
                raise ValueError(f"Contribution {contribution_id} not found")

        except Exception as e:
            logger.error(f"Error updating mock contribution: {str(e)}")
            raise

    def delete(self, contribution_id: str) -> bool:
        """Delete a contribution (mock)"""
        try:
            if contribution_id in self.mock_data:
                del self.mock_data[contribution_id]
                logger.info(f"Mock deleted contribution: {contribution_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting mock contribution: {str(e)}")
            return False

    def get_total_contributions(self) -> int:
        """Get total number of contributions (mock)"""
        try:
            return len(self.mock_data)

        except Exception as e:
            logger.error(f"Error getting total mock contributions: {str(e)}")
            return 0

    def get_contributions_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get contributions within date range (mock)"""
        try:
            # Mock implementation - return all contributions
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting mock contributions by date range: {str(e)}")
            return []


class MockSQLAlchemyRevenueRepository(RevenueRepository):
    """Mock SQLAlchemy implementation of RevenueRepository."""

    def __init__(self, session=None):
        """Initialize with optional session (ignored in mock)"""
        self.session = session
        self.mock_data = {}
        logger.info("Mock Revenue Repository initialized")

    def create(self, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new revenue record (mock)"""
        try:
            revenue_id = f"revenue_{datetime.utcnow().timestamp()}"
            revenue_data["id"] = revenue_id
            revenue_data["created_at"] = datetime.utcnow()

            self.mock_data[revenue_id] = revenue_data

            logger.info(f"Mock created revenue record: {revenue_id}")
            return revenue_data

        except Exception as e:
            logger.error(f"Error creating mock revenue record: {str(e)}")
            raise

    def get_by_id(self, revenue_id: str) -> Optional[Dict[str, Any]]:
        """Get revenue by ID (mock)"""
        try:
            return self.mock_data.get(revenue_id)

        except Exception as e:
            logger.error(f"Error getting mock revenue by ID: {str(e)}")
            return None

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get revenue by source (mock)"""
        try:
            return [
                data for data in self.mock_data.values() if data.get("source") == source
            ]

        except Exception as e:
            logger.error(f"Error getting mock revenue by source: {str(e)}")
            return []

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all revenue records (mock)"""
        try:
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting all mock revenue records: {str(e)}")
            return []

    def update(self, revenue_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a revenue record (mock)"""
        try:
            if revenue_id in self.mock_data:
                data["id"] = revenue_id
                data["updated_at"] = datetime.utcnow()
                self.mock_data[revenue_id] = data

                logger.info(f"Mock updated revenue record: {revenue_id}")
                return data
            else:
                raise ValueError(f"Revenue {revenue_id} not found")

        except Exception as e:
            logger.error(f"Error updating mock revenue record: {str(e)}")
            raise

    def delete(self, revenue_id: str) -> bool:
        """Delete a revenue record (mock)"""
        try:
            if revenue_id in self.mock_data:
                del self.mock_data[revenue_id]
                logger.info(f"Mock deleted revenue record: {revenue_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting mock revenue record: {str(e)}")
            return False

    def get_total_revenue(self) -> Decimal:
        """Get total revenue (mock)"""
        try:
            total = sum(
                Decimal(str(data.get("amount", 0))) for data in self.mock_data.values()
            )
            return total

        except Exception as e:
            logger.error(f"Error getting total mock revenue: {str(e)}")
            return Decimal("0")

    def get_revenue_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get revenue within date range (mock)"""
        try:
            # Mock implementation - return all revenue
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting mock revenue by date range: {str(e)}")
            return []

    def get_revenue_for_distribution(
        self, distribution_id: str
    ) -> List[Dict[str, Any]]:
        """Get revenue records for a specific distribution (mock)"""
        try:
            # Mock implementation - return all revenue
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting mock revenue for distribution: {str(e)}")
            return []


class MockSQLAlchemyDividendRepository(DividendRepository):
    """Mock SQLAlchemy implementation of DividendRepository."""

    def __init__(self, session=None):
        """Initialize with optional session (ignored in mock)"""
        self.session = session
        self.mock_data = {}
        logger.info("Mock Dividend Repository initialized")

    def create(self, dividend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dividend distribution record (mock)"""
        try:
            distribution_id = f"dist_{datetime.utcnow().timestamp()}"
            dividend_data["id"] = distribution_id
            dividend_data["created_at"] = datetime.utcnow()

            self.mock_data[distribution_id] = dividend_data

            logger.info(f"Mock created dividend distribution: {distribution_id}")
            return dividend_data

        except Exception as e:
            logger.error(f"Error creating mock dividend distribution: {str(e)}")
            raise

    def get_by_id(self, distribution_id: str) -> Optional[Dict[str, Any]]:
        """Get dividend distribution by ID (mock)"""
        try:
            return self.mock_data.get(distribution_id)

        except Exception as e:
            logger.error(f"Error getting mock dividend distribution by ID: {str(e)}")
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all dividend distributions (mock)"""
        try:
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting all mock dividend distributions: {str(e)}")
            return []

    def update(self, distribution_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a dividend distribution (mock)"""
        try:
            if distribution_id in self.mock_data:
                data["id"] = distribution_id
                data["updated_at"] = datetime.utcnow()
                self.mock_data[distribution_id] = data

                logger.info(f"Mock updated dividend distribution: {distribution_id}")
                return data
            else:
                raise ValueError(f"Distribution {distribution_id} not found")

        except Exception as e:
            logger.error(f"Error updating mock dividend distribution: {str(e)}")
            raise

    def delete(self, distribution_id: str) -> bool:
        """Delete a dividend distribution (mock)"""
        try:
            if distribution_id in self.mock_data:
                del self.mock_data[distribution_id]
                logger.info(f"Mock deleted dividend distribution: {distribution_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting mock dividend distribution: {str(e)}")
            return False

    def get_total_distributions(self) -> int:
        """Get total number of distributions (mock)"""
        try:
            return len(self.mock_data)

        except Exception as e:
            logger.error(f"Error getting total mock distributions: {str(e)}")
            return 0

    def get_distributions(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get distributions within date range (mock)"""
        try:
            # Mock implementation - return all distributions
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting mock distributions by date range: {str(e)}")
            return []

    def get_claim_data(self, wallet_address: str) -> Dict[str, Any]:
        """Get claim data for a wallet address (mock)"""
        try:
            return {
                "wallet_address": wallet_address,
                "last_claim_index": 0,
                "total_claimed": 0.0,
                "last_claim_date": None,
            }

        except Exception as e:
            logger.error(f"Error getting mock claim data: {str(e)}")
            return {
                "wallet_address": wallet_address,
                "last_claim_index": 0,
                "total_claimed": 0.0,
                "last_claim_date": None,
            }

    def update_claim_data(
        self, wallet_address: str, claim_amount: Decimal, transaction_hash: str
    ) -> Dict[str, Any]:
        """Update claim data for a wallet address (mock)"""
        try:
            claim_data = {
                "wallet_address": wallet_address,
                "claim_amount": float(claim_amount),
                "transaction_hash": transaction_hash,
                "claim_date": datetime.utcnow(),
            }

            logger.info(f"Mock updated claim data for wallet: {wallet_address}")
            return claim_data

        except Exception as e:
            logger.error(f"Error updating mock claim data: {str(e)}")
            raise


class MockSQLAlchemyVerificationRepository(VerificationRepository):
    """Mock SQLAlchemy implementation of VerificationRepository."""

    def __init__(self, session=None):
        """Initialize with optional session (ignored in mock)"""
        self.session = session
        self.mock_data = {}
        logger.info("Mock Verification Repository initialized")

    def create(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new verification record (mock)"""
        try:
            verification_id = f"verify_{datetime.utcnow().timestamp()}"
            verification_data["id"] = verification_id
            verification_data["created_at"] = datetime.utcnow()

            self.mock_data[verification_id] = verification_data

            logger.info(f"Mock created verification record: {verification_id}")
            return verification_data

        except Exception as e:
            logger.error(f"Error creating mock verification record: {str(e)}")
            raise

    def get_by_id(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """Get verification by ID (mock)"""
        try:
            return self.mock_data.get(verification_id)

        except Exception as e:
            logger.error(f"Error getting mock verification by ID: {str(e)}")
            return None

    def get_by_biltobject_hash(self, biltobject_hash: str) -> List[Dict[str, Any]]:
        """Get verifications by building object hash (mock)"""
        try:
            return [
                data
                for data in self.mock_data.values()
                if data.get("biltobject_hash") == biltobject_hash
            ]

        except Exception as e:
            logger.error(f"Error getting mock verifications by object hash: {str(e)}")
            return []

    def get_by_verifier(self, verifier_wallet: str) -> List[Dict[str, Any]]:
        """Get verifications by verifier wallet (mock)"""
        try:
            return [
                data
                for data in self.mock_data.values()
                if data.get("verifier_wallet") == verifier_wallet
            ]

        except Exception as e:
            logger.error(f"Error getting mock verifications by verifier: {str(e)}")
            return []

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all verifications (mock)"""
        try:
            return list(self.mock_data.values())

        except Exception as e:
            logger.error(f"Error getting all mock verifications: {str(e)}")
            return []

    def update(self, verification_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a verification (mock)"""
        try:
            if verification_id in self.mock_data:
                data["id"] = verification_id
                data["updated_at"] = datetime.utcnow()
                self.mock_data[verification_id] = data

                logger.info(f"Mock updated verification: {verification_id}")
                return data
            else:
                raise ValueError(f"Verification {verification_id} not found")

        except Exception as e:
            logger.error(f"Error updating mock verification: {str(e)}")
            raise

    def delete(self, verification_id: str) -> bool:
        """Delete a verification (mock)"""
        try:
            if verification_id in self.mock_data:
                del self.mock_data[verification_id]
                logger.info(f"Mock deleted verification: {verification_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting mock verification: {str(e)}")
            return False
