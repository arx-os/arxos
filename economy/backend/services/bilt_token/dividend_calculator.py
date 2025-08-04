"""
BILT Token Dividend Calculator

Handles revenue attribution and dividend distribution calculations for BILT token holders.
Implements equal dividend distribution to all holders regardless of how they acquired their tokens.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal

import web3
from web3 import Web3
from web3.contract import Contract

from arxos.infrastructure.database.repositories import RepositoryFactory

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


class BiltDividendCalculator:
    """
    BILT Token Dividend Calculator
    
    Handles:
    1. Revenue attribution from platform activities
    2. Equal dividend distribution calculations
    3. Dividend claim tracking
    4. Revenue transparency reporting
    """
    
    def __init__(
        self,
        web3_provider: str,
        bilt_contract_address: str,
        revenue_router_address: str,
        bilt_contract_abi: List[Dict],
        revenue_router_abi: List[Dict],
        repository_factory: RepositoryFactory
    ):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.bilt_contract = self.web3.eth.contract(
            address=bilt_contract_address,
            abi=bilt_contract_abi
        )
        self.revenue_router = self.web3.eth.contract(
            address=revenue_router_address,
            abi=revenue_router_abi
        )
        self.repository_factory = repository_factory
        
        # Initialize repositories
        self.revenue_repo = repository_factory.get_revenue_repository()
        self.dividend_repo = repository_factory.get_dividend_repository()
        
        # Revenue sources configuration
        self.revenue_sources = {
            'data_sales': 'Revenue from building data sales',
            'service_transactions': 'Revenue from service transactions',
            'api_usage': 'Revenue from API usage fees',
            'subscription_fees': 'Revenue from subscription services',
            'consulting_services': 'Revenue from consulting services',
            'direct_deposit': 'Direct deposits to dividend pool'
        }
        
    async def attribute_revenue(
        self,
        source: str,
        amount: Decimal,
        description: Optional[str] = None
    ) -> bool:
        """
        Attribute revenue to the dividend pool
        
        Args:
            source: Revenue source name
            amount: Revenue amount
            description: Optional description of the revenue
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate source
            if source not in self.revenue_sources:
                logger.warning(f"Unknown revenue source: {source}")
                source = 'direct_deposit'
            
            # Convert to wei
            amount_wei = int(amount * 10**18)
            
            # Build transaction
            transaction = self.revenue_router.functions.attributeRevenue(
                source, amount_wei
            ).build_transaction({
                'from': self.web3.eth.default_account,
                'gas': 150000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.web3.eth.default_account)
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction, private_key=self._get_private_key()
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                # Record revenue in database
                revenue_data = {
                    'source': source,
                    'amount': float(amount),
                    'description': description or self.revenue_sources.get(source, ''),
                    'transaction_hash': tx_hash.hex(),
                    'timestamp': datetime.utcnow()
                }
                
                await self.revenue_repo.create(revenue_data)
                
                logger.info(f"Revenue attributed successfully: {amount} from {source}")
                return True
            else:
                logger.error("Revenue attribution transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"Error attributing revenue: {str(e)}")
            return False
    
    async def distribute_dividends(self, amount: Optional[Decimal] = None) -> bool:
        """
        Distribute dividends to all BILT token holders
        
        Args:
            amount: Amount to distribute (if None, distributes entire pool)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if amount is None:
                # Distribute entire dividend pool
                transaction = self.revenue_router.functions.distributeAllDividends()
            else:
                # Distribute specific amount
                amount_wei = int(amount * 10**18)
                transaction = self.revenue_router.functions.distributeDividends(amount_wei)
            
            # Build transaction
            tx = transaction.build_transaction({
                'from': self.web3.eth.default_account,
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.web3.eth.default_account)
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                tx, private_key=self._get_private_key()
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                # Get distribution details
                distribution_id = await self._get_latest_distribution_id()
                dividend_per_token = await self._calculate_dividend_per_token(amount)
                total_supply = self.bilt_contract.functions.totalSupply().call()
                
                # Record distribution in database
                distribution_data = {
                    'distribution_id': distribution_id,
                    'total_amount': float(amount) if amount else await self._get_dividend_pool_amount(),
                    'dividend_per_token': float(dividend_per_token),
                    'total_supply': total_supply,
                    'transaction_hash': tx_hash.hex(),
                    'timestamp': datetime.utcnow()
                }
                
                await self.dividend_repo.create(distribution_data)
                
                logger.info(f"Dividends distributed successfully: {amount}")
                return True
            else:
                logger.error("Dividend distribution transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"Error distributing dividends: {str(e)}")
            return False
    
    async def calculate_claimable_dividends(self, wallet_address: str) -> DividendClaim:
        """
        Calculate claimable dividends for a wallet address
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            DividendClaim with claimable amount and tracking data
        """
        try:
            # Get token balance
            balance = self.bilt_contract.functions.balanceOf(wallet_address).call()
            
            if balance == 0:
                return DividendClaim(
                    wallet_address=wallet_address,
                    claimable_amount=Decimal('0'),
                    last_claim_index=0,
                    total_claimed=Decimal('0')
                )
            
            # Get claimable amount from smart contract
            claimable_wei = self.bilt_contract.functions.getClaimableDividends(
                wallet_address
            ).call()
            
            claimable_amount = Decimal(claimable_wei) / Decimal(10**18)
            
            # Get tracking data from database
            claim_data = await self.dividend_repo.get_claim_data(wallet_address)
            
            return DividendClaim(
                wallet_address=wallet_address,
                claimable_amount=claimable_amount,
                last_claim_index=claim_data.get('last_claim_index', 0),
                total_claimed=Decimal(str(claim_data.get('total_claimed', 0)))
            )
            
        except Exception as e:
            logger.error(f"Error calculating claimable dividends: {str(e)}")
            return DividendClaim(
                wallet_address=wallet_address,
                claimable_amount=Decimal('0'),
                last_claim_index=0,
                total_claimed=Decimal('0')
            )
    
    async def claim_dividends(self, wallet_address: str) -> bool:
        """
        Claim dividends for a wallet address
        
        Args:
            wallet_address: Wallet address to claim dividends for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if there are claimable dividends
            claimable = await self.calculate_claimable_dividends(wallet_address)
            
            if claimable.claimable_amount <= 0:
                logger.warning(f"No claimable dividends for {wallet_address}")
                return False
            
            # Build transaction
            transaction = self.bilt_contract.functions.claimDividends(wallet_address)
            tx = transaction.build_transaction({
                'from': self.web3.eth.default_account,
                'gas': 150000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.web3.eth.default_account)
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                tx, private_key=self._get_private_key()
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                # Update claim tracking in database
                await self.dividend_repo.update_claim_data(
                    wallet_address,
                    claimable.claimable_amount,
                    tx_hash.hex()
                )
                
                logger.info(f"Dividends claimed successfully: {claimable.claimable_amount} for {wallet_address}")
                return True
            else:
                logger.error("Dividend claim transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"Error claiming dividends: {str(e)}")
            return False
    
    async def get_dividend_pool_stats(self) -> Dict[str, Any]:
        """
        Get current dividend pool statistics
        
        Returns:
            Dictionary with pool statistics
        """
        try:
            # Get stats from smart contract
            pool_stats = self.revenue_router.functions.getDividendPoolStats().call()
            
            # Get additional data from database
            total_revenue = await self.revenue_repo.get_total_revenue()
            total_distributions = await self.dividend_repo.get_total_distributions()
            
            return {
                'current_pool': Decimal(pool_stats[0]) / Decimal(10**18),
                'total_revenue': Decimal(pool_stats[1]) / Decimal(10**18),
                'total_distributed': Decimal(pool_stats[2]) / Decimal(10**18),
                'total_supply': pool_stats[3],
                'database_total_revenue': total_revenue,
                'database_total_distributions': total_distributions
            }
            
        except Exception as e:
            logger.error(f"Error getting dividend pool stats: {str(e)}")
            return {}
    
    async def get_revenue_by_source(self, source: str) -> Decimal:
        """
        Get total revenue by source
        
        Args:
            source: Revenue source name
            
        Returns:
            Total revenue from the specified source
        """
        try:
            # Get from smart contract
            revenue_wei = self.revenue_router.functions.getRevenueBySource(source).call()
            return Decimal(revenue_wei) / Decimal(10**18)
            
        except Exception as e:
            logger.error(f"Error getting revenue by source: {str(e)}")
            return Decimal('0')
    
    async def get_all_revenue_sources(self) -> Dict[str, Decimal]:
        """
        Get all revenue sources and their amounts
        
        Returns:
            Dictionary mapping source names to amounts
        """
        try:
            sources = {}
            for source in self.revenue_sources.keys():
                amount = await self.get_revenue_by_source(source)
                if amount > 0:
                    sources[source] = amount
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting all revenue sources: {str(e)}")
            return {}
    
    async def get_dividend_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DividendDistribution]:
        """
        Get dividend distribution history
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of dividend distributions
        """
        try:
            # Get from database
            distributions = await self.dividend_repo.get_distributions(
                start_date, end_date
            )
            
            result = []
            for dist in distributions:
                # Get revenue sources for this distribution
                revenue_sources = await self.revenue_repo.get_revenue_for_distribution(
                    dist['distribution_id']
                )
                
                sources = []
                for rev in revenue_sources:
                    sources.append(RevenueSource(
                        source_name=rev['source'],
                        amount=Decimal(str(rev['amount'])),
                        timestamp=rev['timestamp'],
                        description=rev['description']
                    ))
                
                result.append(DividendDistribution(
                    distribution_id=dist['distribution_id'],
                    total_amount=Decimal(str(dist['total_amount'])),
                    dividend_per_token=Decimal(str(dist['dividend_per_token'])),
                    total_supply=dist['total_supply'],
                    distribution_date=dist['timestamp'],
                    revenue_sources=sources
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting dividend history: {str(e)}")
            return []
    
    async def calculate_dividend_yield(self, period_days: int = 365) -> Dict[str, Any]:
        """
        Calculate dividend yield for the specified period
        
        Args:
            period_days: Number of days to calculate yield for
            
        Returns:
            Dictionary with yield statistics
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get distributions in period
            distributions = await self.get_dividend_history(start_date, end_date)
            
            if not distributions:
                return {
                    'total_dividends': Decimal('0'),
                    'average_dividend_per_token': Decimal('0'),
                    'yield_percentage': Decimal('0'),
                    'distribution_count': 0
                }
            
            total_dividends = sum(d.total_amount for d in distributions)
            total_supply = distributions[-1].total_supply if distributions else 0
            
            if total_supply > 0:
                avg_dividend_per_token = total_dividends / Decimal(total_supply)
                yield_percentage = (total_dividends / Decimal(total_supply)) * Decimal('100')
            else:
                avg_dividend_per_token = Decimal('0')
                yield_percentage = Decimal('0')
            
            return {
                'total_dividends': total_dividends,
                'average_dividend_per_token': avg_dividend_per_token,
                'yield_percentage': yield_percentage,
                'distribution_count': len(distributions),
                'period_days': period_days
            }
            
        except Exception as e:
            logger.error(f"Error calculating dividend yield: {str(e)}")
            return {}
    
    async def _get_latest_distribution_id(self) -> str:
        """Get the latest distribution ID"""
        try:
            counter = self.revenue_router.functions.dividendDistributionCounter().call()
            return f"dist_{counter}"
        except Exception as e:
            logger.error(f"Error getting latest distribution ID: {str(e)}")
            return f"dist_{datetime.utcnow().timestamp()}"
    
    async def _calculate_dividend_per_token(self, amount: Optional[Decimal]) -> Decimal:
        """Calculate dividend per token for a given amount"""
        try:
            if amount is None:
                amount = await self._get_dividend_pool_amount()
            
            total_supply = self.bilt_contract.functions.totalSupply().call()
            
            if total_supply == 0:
                return Decimal('0')
            
            return amount / Decimal(total_supply)
            
        except Exception as e:
            logger.error(f"Error calculating dividend per token: {str(e)}")
            return Decimal('0')
    
    async def _get_dividend_pool_amount(self) -> Decimal:
        """Get current dividend pool amount"""
        try:
            pool_stats = self.revenue_router.functions.getDividendPoolStats().call()
            return Decimal(pool_stats[0]) / Decimal(10**18)
        except Exception as e:
            logger.error(f"Error getting dividend pool amount: {str(e)}")
            return Decimal('0')
    
    def _get_private_key(self) -> str:
        """Get private key for transaction signing"""
        # This should be implemented securely based on your key management system
        return "YOUR_PRIVATE_KEY_HERE" 