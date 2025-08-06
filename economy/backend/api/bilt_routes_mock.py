"""
Mock BILT Token API Routes

A development version that doesn't require FastAPI dependencies.
This allows the BILT API to be developed and tested without web framework dependencies.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ..services.bilt_token.minting_engine_mock import (
    MockBiltMintingEngine,
    VerificationResult,
)
from ..services.bilt_token.dividend_calculator_mock import (
    MockBiltDividendCalculator,
    DividendClaim,
)

logger = logging.getLogger(__name__)


@dataclass
class MockAPIResponse:
    """Mock API response structure"""

    status_code: int
    data: Dict[str, Any]
    message: str
    timestamp: datetime


class MockBiltAPIRouter:
    """
    Mock BILT Token API Router

    Development version that simulates API endpoints without requiring FastAPI.
    """

    def __init__(self):
        """Initialize mock API router"""
        self.minting_engine = MockBiltMintingEngine()
        self.dividend_calculator = MockBiltDividendCalculator()

        logger.info("Mock BILT API Router initialized")

    async def submit_contribution(
        self,
        contributor_wallet: str,
        object_data: Dict[str, Any],
        system_type: str,
        verifier_wallet: Optional[str] = None,
    ) -> MockAPIResponse:
        """
        Submit a new contribution for verification and minting
        """
        try:
            # Validate input
            if not contributor_wallet or not object_data or not system_type:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Missing required fields: contributor_wallet, object_data, system_type",
                    timestamp=datetime.utcnow(),
                )

            # Process contribution
            result = await self.minting_engine.process_contribution(
                contributor_wallet=contributor_wallet,
                object_data=object_data,
                system_type=system_type,
                verifier_wallet=verifier_wallet,
            )

            # Prepare response
            response_data = {
                "contribution_id": f"contrib_{datetime.utcnow().timestamp()}",
                "status": result.status.value,
                "bilt_amount": result.bilt_amount,
                "validation_score": result.validation_score,
                "fraud_score": result.fraud_score,
                "verification_notes": result.verification_notes,
                "timestamp": result.timestamp.isoformat(),
            }

            if result.status.value == "user_verified":
                status_code = 201
                message = "Contribution successfully verified and BILT tokens minted"
            elif result.status.value == "pending":
                status_code = 202
                message = "Contribution pending secondary user verification"
            else:
                status_code = 400
                message = f"Contribution rejected: {result.verification_notes}"

            return MockAPIResponse(
                status_code=status_code,
                data=response_data,
                message=message,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error in submit_contribution: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def verify_contribution(
        self,
        biltobject_hash: str,
        verifier_wallet: str,
        verification_data: Dict[str, Any],
    ) -> MockAPIResponse:
        """
        Perform secondary user verification of a contribution
        """
        try:
            # Validate input
            if not biltobject_hash or not verifier_wallet:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Missing required fields: biltobject_hash, verifier_wallet",
                    timestamp=datetime.utcnow(),
                )

            # Mock verification process
            verification_success = True  # Mock success
            verification_score = 0.85  # Mock score

            if verification_success:
                # Update contribution status
                response_data = {
                    "verification_id": f"verify_{datetime.utcnow().timestamp()}",
                    "biltobject_hash": biltobject_hash,
                    "verifier_wallet": verifier_wallet,
                    "verification_score": verification_score,
                    "status": "verified",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                return MockAPIResponse(
                    status_code=200,
                    data=response_data,
                    message="Contribution successfully verified",
                    timestamp=datetime.utcnow(),
                )
            else:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Verification failed",
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error in verify_contribution: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def get_contribution_status(self, biltobject_hash: str) -> MockAPIResponse:
        """
        Get the status of a contribution
        """
        try:
            # Mock contribution status
            response_data = {
                "biltobject_hash": biltobject_hash,
                "status": "verified",
                "bilt_amount": 150.0,
                "validation_score": 0.85,
                "contributor_wallet": "0x1234567890abcdef",
                "verifier_wallet": "0xabcdef1234567890",
                "created_at": datetime.utcnow().isoformat(),
                "verified_at": datetime.utcnow().isoformat(),
            }

            return MockAPIResponse(
                status_code=200,
                data=response_data,
                message="Contribution status retrieved successfully",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error in get_contribution_status: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def attribute_revenue(
        self, source: str, amount: float, description: Optional[str] = None
    ) -> MockAPIResponse:
        """
        Attribute revenue to the dividend pool
        """
        try:
            from decimal import Decimal

            # Validate input
            if not source or amount <= 0:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Invalid revenue source or amount",
                    timestamp=datetime.utcnow(),
                )

            # Attribute revenue
            success = await self.dividend_calculator.attribute_revenue(
                source=source, amount=Decimal(str(amount)), description=description
            )

            if success:
                response_data = {
                    "revenue_id": f"revenue_{datetime.utcnow().timestamp()}",
                    "source": source,
                    "amount": amount,
                    "description": description,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                return MockAPIResponse(
                    status_code=201,
                    data=response_data,
                    message="Revenue successfully attributed to dividend pool",
                    timestamp=datetime.utcnow(),
                )
            else:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Failed to attribute revenue",
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error in attribute_revenue: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def distribute_dividends(
        self, amount: Optional[float] = None
    ) -> MockAPIResponse:
        """
        Distribute dividends to all BILT token holders
        """
        try:
            from decimal import Decimal

            # Distribute dividends
            success = await self.dividend_calculator.distribute_dividends(
                amount=Decimal(str(amount)) if amount else None
            )

            if success:
                # Get updated stats
                stats = await self.dividend_calculator.get_dividend_pool_stats()

                response_data = {
                    "distribution_id": f"dist_{datetime.utcnow().timestamp()}",
                    "amount_distributed": amount or stats.get("current_pool", 0),
                    "total_distributed": stats.get("total_distributed", 0),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                return MockAPIResponse(
                    status_code=200,
                    data=response_data,
                    message="Dividends distributed successfully",
                    timestamp=datetime.utcnow(),
                )
            else:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Failed to distribute dividends",
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error in distribute_dividends: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def claim_dividends(self, wallet_address: str) -> MockAPIResponse:
        """
        Claim dividends for a wallet address
        """
        try:
            # Calculate claimable dividends
            claimable = await self.dividend_calculator.calculate_claimable_dividends(
                wallet_address
            )

            if claimable.claimable_amount <= 0:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="No claimable dividends for this wallet",
                    timestamp=datetime.utcnow(),
                )

            # Claim dividends
            success = await self.dividend_calculator.claim_dividends(wallet_address)

            if success:
                response_data = {
                    "claim_id": f"claim_{datetime.utcnow().timestamp()}",
                    "wallet_address": wallet_address,
                    "claimed_amount": float(claimable.claimable_amount),
                    "total_claimed": float(claimable.total_claimed),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                return MockAPIResponse(
                    status_code=200,
                    data=response_data,
                    message="Dividends claimed successfully",
                    timestamp=datetime.utcnow(),
                )
            else:
                return MockAPIResponse(
                    status_code=400,
                    data={},
                    message="Failed to claim dividends",
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error in claim_dividends: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def get_dividend_pool_stats(self) -> MockAPIResponse:
        """
        Get current dividend pool statistics
        """
        try:
            stats = await self.dividend_calculator.get_dividend_pool_stats()

            return MockAPIResponse(
                status_code=200,
                data=stats,
                message="Dividend pool statistics retrieved successfully",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error in get_dividend_pool_stats: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def get_claimable_dividends(self, wallet_address: str) -> MockAPIResponse:
        """
        Get claimable dividends for a wallet address
        """
        try:
            claimable = await self.dividend_calculator.calculate_claimable_dividends(
                wallet_address
            )

            response_data = {
                "wallet_address": wallet_address,
                "claimable_amount": float(claimable.claimable_amount),
                "last_claim_index": claimable.last_claim_index,
                "total_claimed": float(claimable.total_claimed),
            }

            return MockAPIResponse(
                status_code=200,
                data=response_data,
                message="Claimable dividends retrieved successfully",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error in get_claimable_dividends: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def get_revenue_sources(self) -> MockAPIResponse:
        """
        Get all revenue sources and their amounts
        """
        try:
            sources = await self.dividend_calculator.get_all_revenue_sources()

            response_data = {
                "revenue_sources": {k: float(v) for k, v in sources.items()},
                "total_revenue": sum(float(v) for v in sources.values()),
            }

            return MockAPIResponse(
                status_code=200,
                data=response_data,
                message="Revenue sources retrieved successfully",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error in get_revenue_sources: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def get_dividend_history(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> MockAPIResponse:
        """
        Get dividend distribution history
        """
        try:
            # Parse dates if provided
            start_dt = None
            end_dt = None

            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)

            # Get dividend history
            history = await self.dividend_calculator.get_dividend_history(
                start_dt, end_dt
            )

            response_data = {
                "distributions": [
                    {
                        "distribution_id": d.distribution_id,
                        "total_amount": float(d.total_amount),
                        "dividend_per_token": float(d.dividend_per_token),
                        "total_supply": d.total_supply,
                        "distribution_date": d.distribution_date.isoformat(),
                        "revenue_sources": [
                            {
                                "source_name": rs.source_name,
                                "amount": float(rs.amount),
                                "timestamp": rs.timestamp.isoformat(),
                                "description": rs.description,
                            }
                            for rs in d.revenue_sources
                        ],
                    }
                    for d in history
                ],
                "total_distributions": len(history),
            }

            return MockAPIResponse(
                status_code=200,
                data=response_data,
                message="Dividend history retrieved successfully",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error in get_dividend_history: {str(e)}")
            return MockAPIResponse(
                status_code=500,
                data={},
                message=f"Internal server error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    def get_mock_state(self) -> Dict[str, Any]:
        """
        Get the current mock state for debugging
        """
        return {
            "minting_engine": self.minting_engine.get_mock_state(),
            "dividend_calculator": self.dividend_calculator.get_mock_state(),
        }

    def reset_mock_state(self):
        """
        Reset the mock state for testing
        """
        self.minting_engine.reset_mock_state()
        self.dividend_calculator.reset_mock_state()
        logger.info("Mock API state reset")
