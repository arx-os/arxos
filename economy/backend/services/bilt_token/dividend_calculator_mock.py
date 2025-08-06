"""
Mock BILT Token Dividend Calculator

A development version that doesn't require external dependencies like web3.
This allows the BILT dividend system to be developed and tested without blockchain dependencies.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class RevenueSource:
    """Revenue source data structure"""

    source_name: str
    amount: Decimal
    timestamp: datetime
    description: str


@dataclass
class DividendDistribution:
    """Dividend distribution data structure"""

    distribution_id: str
    total_amount: Decimal
    dividend_per_token: Decimal
    total_supply: int
    distribution_date: datetime
    revenue_sources: List[RevenueSource]


@dataclass
class DividendClaim:
    """Dividend claim data structure"""

    wallet_address: str
    claimable_amount: Decimal
    last_claim_index: int
    total_claimed: Decimal


class MockBiltDividendCalculator:
    """
    Mock BILT Token Dividend Calculator

    Development version that simulates blockchain operations without requiring web3.
    """

    def __init__(
        self,
        web3_provider: str = "mock://localhost:8545",
        bilt_contract_address: str = "0x0000000000000000000000000000000000000000",
        revenue_router_address: str = "0x0000000000000000000000000000000000000000",
        bilt_contract_abi: List[Dict] = None,
        revenue_router_abi: List[Dict] = None,
        repository_factory=None,
    ):
        self.web3_provider = web3_provider
        self.bilt_contract_address = bilt_contract_address
        self.revenue_router_address = revenue_router_address
        self.bilt_contract_abi = bilt_contract_abi or []
        self.revenue_router_abi = revenue_router_abi or []
        self.repository_factory = repository_factory

        # Mock blockchain state
        self.mock_contract_state = {
            "total_revenue": Decimal("0"),
            "total_dividends_distributed": Decimal("0"),
            "current_dividend_pool": Decimal("0"),
            "total_supply": 1000000,  # Mock total supply
            "balances": {},
            "revenue_sources": {},
            "dividend_history": [],
            "claim_data": {},
        }

        # Revenue sources configuration
        self.revenue_sources = {
            "data_sales": "Revenue from building data sales",
            "service_transactions": "Revenue from service transactions",
            "api_usage": "Revenue from API usage fees",
            "subscription_fees": "Revenue from subscription services",
            "consulting_services": "Revenue from consulting services",
            "direct_deposit": "Direct deposits to dividend pool",
        }

        logger.info("Mock BILT Dividend Calculator initialized")

    async def attribute_revenue(
        self, source: str, amount: Decimal, description: Optional[str] = None
    ) -> bool:
        """
        Attribute revenue to the dividend pool (mock)
        """
        try:
            # Validate source
            if source not in self.revenue_sources:
                logger.warning(f"Unknown revenue source: {source}")
                source = "direct_deposit"

            # Update mock state
            self.mock_contract_state["total_revenue"] += amount
            self.mock_contract_state["current_dividend_pool"] += amount

            # Track revenue by source
            if source not in self.mock_contract_state["revenue_sources"]:
                self.mock_contract_state["revenue_sources"][source] = Decimal("0")
            self.mock_contract_state["revenue_sources"][source] += amount

            logger.info(f"Mock revenue attributed: {amount} from {source}")
            return True

        except Exception as e:
            logger.error(f"Error attributing mock revenue: {str(e)}")
            return False

    async def distribute_dividends(self, amount: Optional[Decimal] = None) -> bool:
        """
        Distribute dividends to all BILT token holders (mock)
        """
        try:
            if amount is None:
                amount = self.mock_contract_state["current_dividend_pool"]

            if amount <= 0:
                logger.warning("No dividends to distribute")
                return False

            # Calculate dividend per token
            dividend_per_token = amount / Decimal(
                self.mock_contract_state["total_supply"]
            )

            # Update mock state
            self.mock_contract_state["current_dividend_pool"] -= amount
            self.mock_contract_state["total_dividends_distributed"] += amount

            # Record distribution
            distribution = {
                "id": f"dist_{datetime.utcnow().timestamp()}",
                "total_amount": amount,
                "dividend_per_token": dividend_per_token,
                "total_supply": self.mock_contract_state["total_supply"],
                "timestamp": datetime.utcnow(),
            }
            self.mock_contract_state["dividend_history"].append(distribution)

            logger.info(f"Mock dividends distributed: {amount}")
            return True

        except Exception as e:
            logger.error(f"Error distributing mock dividends: {str(e)}")
            return False

    async def calculate_claimable_dividends(self, wallet_address: str) -> DividendClaim:
        """
        Calculate claimable dividends for a wallet address (mock)
        """
        try:
            # Mock balance
            balance = self.mock_contract_state["balances"].get(wallet_address, 0)

            if balance == 0:
                return DividendClaim(
                    wallet_address=wallet_address,
                    claimable_amount=Decimal("0"),
                    last_claim_index=0,
                    total_claimed=Decimal("0"),
                )

            # Mock claimable amount (simplified calculation)
            claimable_amount = Decimal(str(balance)) * Decimal(
                "0.01"
            )  # 1% of balance as mock dividend

            # Get claim data
            claim_data = self.mock_contract_state["claim_data"].get(
                wallet_address, {"last_claim_index": 0, "total_claimed": 0.0}
            )

            return DividendClaim(
                wallet_address=wallet_address,
                claimable_amount=claimable_amount,
                last_claim_index=claim_data.get("last_claim_index", 0),
                total_claimed=Decimal(str(claim_data.get("total_claimed", 0))),
            )

        except Exception as e:
            logger.error(f"Error calculating mock claimable dividends: {str(e)}")
            return DividendClaim(
                wallet_address=wallet_address,
                claimable_amount=Decimal("0"),
                last_claim_index=0,
                total_claimed=Decimal("0"),
            )

    async def claim_dividends(self, wallet_address: str) -> bool:
        """
        Claim dividends for a wallet address (mock)
        """
        try:
            # Check if there are claimable dividends
            claimable = await self.calculate_claimable_dividends(wallet_address)

            if claimable.claimable_amount <= 0:
                logger.warning(f"No claimable dividends for {wallet_address}")
                return False

            # Update claim data
            if wallet_address not in self.mock_contract_state["claim_data"]:
                self.mock_contract_state["claim_data"][wallet_address] = {
                    "last_claim_index": 0,
                    "total_claimed": 0.0,
                }

            self.mock_contract_state["claim_data"][wallet_address][
                "total_claimed"
            ] += float(claimable.claimable_amount)

            logger.info(
                f"Mock dividends claimed: {claimable.claimable_amount} for {wallet_address}"
            )
            return True

        except Exception as e:
            logger.error(f"Error claiming mock dividends: {str(e)}")
            return False

    async def get_dividend_pool_stats(self) -> Dict[str, Any]:
        """
        Get current dividend pool statistics (mock)
        """
        try:
            return {
                "current_pool": float(
                    self.mock_contract_state["current_dividend_pool"]
                ),
                "total_revenue": float(self.mock_contract_state["total_revenue"]),
                "total_distributed": float(
                    self.mock_contract_state["total_dividends_distributed"]
                ),
                "total_supply": self.mock_contract_state["total_supply"],
                "database_total_revenue": float(
                    self.mock_contract_state["total_revenue"]
                ),
                "database_total_distributions": len(
                    self.mock_contract_state["dividend_history"]
                ),
            }

        except Exception as e:
            logger.error(f"Error getting mock dividend pool stats: {str(e)}")
            return {}

    async def get_revenue_by_source(self, source: str) -> Decimal:
        """
        Get total revenue by source (mock)
        """
        try:
            return self.mock_contract_state["revenue_sources"].get(source, Decimal("0"))

        except Exception as e:
            logger.error(f"Error getting mock revenue by source: {str(e)}")
            return Decimal("0")

    async def get_all_revenue_sources(self) -> Dict[str, Decimal]:
        """
        Get all revenue sources and their amounts (mock)
        """
        try:
            sources = {}
            for source in self.revenue_sources.keys():
                amount = await self.get_revenue_by_source(source)
                if amount > 0:
                    sources[source] = amount

            return sources

        except Exception as e:
            logger.error(f"Error getting all mock revenue sources: {str(e)}")
            return {}

    async def get_dividend_history(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[DividendDistribution]:
        """
        Get dividend distribution history (mock)
        """
        try:
            distributions = []
            for dist in self.mock_contract_state["dividend_history"]:
                # Filter by date if provided
                if start_date and dist["timestamp"] < start_date:
                    continue
                if end_date and dist["timestamp"] > end_date:
                    continue

                # Create mock revenue sources
                revenue_sources = [
                    RevenueSource(
                        source_name="mock_source",
                        amount=Decimal(str(dist["total_amount"])),
                        timestamp=dist["timestamp"],
                        description="Mock revenue source",
                    )
                ]

                distributions.append(
                    DividendDistribution(
                        distribution_id=dist["id"],
                        total_amount=Decimal(str(dist["total_amount"])),
                        dividend_per_token=Decimal(str(dist["dividend_per_token"])),
                        total_supply=dist["total_supply"],
                        distribution_date=dist["timestamp"],
                        revenue_sources=revenue_sources,
                    )
                )

            return distributions

        except Exception as e:
            logger.error(f"Error getting mock dividend history: {str(e)}")
            return []

    async def calculate_dividend_yield(self, period_days: int = 365) -> Dict[str, Any]:
        """
        Calculate dividend yield for the specified period (mock)
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)

            # Get distributions in period
            distributions = await self.get_dividend_history(start_date, end_date)

            if not distributions:
                return {
                    "total_dividends": Decimal("0"),
                    "average_dividend_per_token": Decimal("0"),
                    "yield_percentage": Decimal("0"),
                    "distribution_count": 0,
                }

            total_dividends = sum(d.total_amount for d in distributions)
            total_supply = distributions[-1].total_supply if distributions else 0

            if total_supply > 0:
                avg_dividend_per_token = total_dividends / Decimal(total_supply)
                yield_percentage = (total_dividends / Decimal(total_supply)) * Decimal(
                    "100"
                )
            else:
                avg_dividend_per_token = Decimal("0")
                yield_percentage = Decimal("0")

            return {
                "total_dividends": total_dividends,
                "average_dividend_per_token": avg_dividend_per_token,
                "yield_percentage": yield_percentage,
                "distribution_count": len(distributions),
                "period_days": period_days,
            }

        except Exception as e:
            logger.error(f"Error calculating mock dividend yield: {str(e)}")
            return {}

    def get_mock_state(self) -> Dict[str, Any]:
        """
        Get the current mock contract state for debugging
        """
        return self.mock_contract_state.copy()

    def reset_mock_state(self):
        """
        Reset the mock contract state for testing
        """
        self.mock_contract_state = {
            "total_revenue": Decimal("0"),
            "total_dividends_distributed": Decimal("0"),
            "current_dividend_pool": Decimal("0"),
            "total_supply": 1000000,
            "balances": {},
            "revenue_sources": {},
            "dividend_history": [],
            "claim_data": {},
        }
        logger.info("Mock dividend calculator state reset")
