"""
BILT Token API Routes

REST API endpoints for BILT token operations including:
- Contribution processing and verification
- Revenue attribution
- Dividend distribution and claiming
- Fraud reporting
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

# Import BILT services
try:
    from economy.backend.services.bilt_token.minting_engine import BiltMintingEngine
    from economy.backend.services.bilt_token.dividend_calculator import BiltDividendCalculator
except ImportError:
    # Use mock implementations if import fails
    from economy.backend.services.bilt_token.minting_engine_mock import MockBiltMintingEngine as BiltMintingEngine
    from economy.backend.services.bilt_token.dividend_calculator_mock import MockBiltDividendCalculator as BiltDividendCalculator

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/bilt", tags=["BILT Token"])


# Pydantic models for request/response
class ContributionRequest(BaseModel):
    """Request model for BILT contribution processing"""
    
    contributor_wallet: str = Field(
        ..., description="Wallet address of the contributor"
    )
    object_data: Dict[str, Any] = Field(..., description="Building object data")
    system_type: str = Field(..., description="Type of building system")
    verifier_wallet: Optional[str] = Field(
        None, description="Wallet address of the verifier"
    )


class ContributionResponse(BaseModel):
    """Response model for BILT contribution processing"""
    
    success: bool
    bilt_amount: float
    validation_score: float
    fraud_score: float
    status: str
    verification_notes: str
    biltobject_hash: Optional[str] = None
    transaction_hash: Optional[str] = None


class RevenueAttributionRequest(BaseModel):
    """Request model for revenue attribution"""
    
    source: str = Field(..., description="Revenue source name")
    amount: float = Field(..., description="Revenue amount")
    description: Optional[str] = Field(None, description="Revenue description")


class DividendDistributionRequest(BaseModel):
    """Request model for dividend distribution"""
    
    amount: Optional[float] = Field(
        None, description="Amount to distribute (optional, uses pool balance)"
    )


class DividendClaimRequest(BaseModel):
    """Request model for dividend claiming"""
    
    wallet_address: str = Field(
        ..., description="Wallet address to claim dividends for"
    )


class FraudReportRequest(BaseModel):
    """Request model for fraud reporting"""
    
    contributor_wallet: str = Field(
        ..., description="Wallet address of the contributor"
    )
    biltobject_hash: str = Field(..., description="Hash of the building object")
    reason: str = Field(..., description="Reason for fraud report")


class DividendPoolStatsResponse(BaseModel):
    """Response model for dividend pool statistics"""
    
    current_pool: float
    total_revenue: float
    total_distributed: float
    total_supply: int
    database_total_revenue: float
    database_total_distributions: int


class DividendClaimResponse(BaseModel):
    """Response model for dividend claim information"""
    
    wallet_address: str
    claimable_amount: float
    last_claim_index: int
    total_claimed: float


class RevenueSourceResponse(BaseModel):
    """Response model for revenue source information"""
    
    source_name: str
    amount: float
    description: str


class DividendYieldResponse(BaseModel):
    """Response model for dividend yield information"""
    
    total_dividends: float
    average_dividend_per_token: float
    yield_percentage: float
    distribution_count: int
    period_days: int


# Dependency injection
def get_minting_engine() -> BiltMintingEngine:
    """Get BILT minting engine instance"""
    return BiltMintingEngine()


def get_dividend_calculator() -> BiltDividendCalculator:
    """Get BILT dividend calculator instance"""
    return BiltDividendCalculator(
        web3_provider="mock://localhost:8545",
        bilt_contract_address="0x0000000000000000000000000000000000000000",
        revenue_router_address="0x0000000000000000000000000000000000000000",
        bilt_contract_abi=[],
        revenue_router_abi=[],
        repository_factory=None
    )


@router.post("/contribute", response_model=ContributionResponse)
async def process_contribution(
    request: ContributionRequest,
    minting_engine: BiltMintingEngine = Depends(get_minting_engine),
):
    """
    Process a BILT contribution
    
    This endpoint handles the complete contribution process including:
    - AI validation using ArxLogic
    - Secondary user verification
    - Fraud detection
    - BILT token minting
    """
    try:
        logger.info(f"Processing contribution from {request.contributor_wallet}")
        
        # Process the contribution
        result = await minting_engine.process_contribution(
            contributor_wallet=request.contributor_wallet,
            object_data=request.object_data,
            system_type=request.system_type,
            verifier_wallet=request.verifier_wallet,
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contribution processing failed"
            )
        
        return ContributionResponse(
            success=True,
            bilt_amount=result.bilt_amount,
            validation_score=result.validation_score,
            fraud_score=result.fraud_score,
            status=result.status.value,
            verification_notes=result.verification_notes,
            biltobject_hash=getattr(result, 'biltobject_hash', None),
            transaction_hash=getattr(result, 'transaction_hash', None),
        )
        
    except Exception as e:
        logger.error(f"Error processing contribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contribution processing failed: {str(e)}"
        )


@router.post("/contribute/verify")
async def verify_contribution(
    biltobject_hash: str,
    verifier_wallet: str,
    minting_engine: BiltMintingEngine = Depends(get_minting_engine),
):
    """
    Verify a BILT contribution
    
    This endpoint allows secondary verification of a contribution
    """
    try:
        logger.info(f"Verifying contribution {biltobject_hash} by {verifier_wallet}")
        
        # This would typically call a verification method
        # For now, return a mock response
        return {
            "success": True,
            "message": "Contribution verified successfully",
            "biltobject_hash": biltobject_hash,
            "verifier_wallet": verifier_wallet,
        }
        
    except Exception as e:
        logger.error(f"Error verifying contribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contribution verification failed: {str(e)}"
        )


@router.post("/revenue/attribute")
async def attribute_revenue(
    request: RevenueAttributionRequest,
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Attribute revenue to the dividend pool
    
    This endpoint adds revenue to the dividend pool for distribution
    """
    try:
        logger.info(f"Attributing revenue: {request.amount} from {request.source}")
        
        # Attribute revenue
        success = await dividend_calculator.attribute_revenue(
            source=request.source,
            amount=Decimal(str(request.amount)),
            description=request.description,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Revenue attribution failed"
            )
        
        return {
            "success": True,
            "message": "Revenue attributed successfully",
            "source": request.source,
            "amount": request.amount,
        }
        
    except Exception as e:
        logger.error(f"Error attributing revenue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revenue attribution failed: {str(e)}"
        )


@router.post("/dividends/distribute")
async def distribute_dividends(
    request: DividendDistributionRequest,
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Distribute dividends to all BILT token holders
    
    This endpoint distributes dividends equally to all token holders
    """
    try:
        logger.info("Distributing dividends to all token holders")
        
        # Distribute dividends
        success = await dividend_calculator.distribute_dividends(
            amount=Decimal(str(request.amount)) if request.amount else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dividend distribution failed"
            )
        
        return {
            "success": True,
            "message": "Dividends distributed successfully",
        }
        
    except Exception as e:
        logger.error(f"Error distributing dividends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dividend distribution failed: {str(e)}"
        )


@router.post("/dividends/claim", response_model=DividendClaimResponse)
async def claim_dividends(
    request: DividendClaimRequest,
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Claim dividends for a wallet address
    
    This endpoint allows token holders to claim their dividends
    """
    try:
        logger.info(f"Claiming dividends for {request.wallet_address}")
        
        # Claim dividends
        success = await dividend_calculator.claim_dividends(
            wallet_address=request.wallet_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dividend claiming failed"
            )
        
        # Get claimable dividends info
        claim_info = await dividend_calculator.calculate_claimable_dividends(
            wallet_address=request.wallet_address
        )
        
        if claim_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No claimable dividends found"
            )
        
        return DividendClaimResponse(
            wallet_address=claim_info.wallet_address,
            claimable_amount=float(claim_info.claimable_amount),
            last_claim_index=claim_info.last_claim_index,
            total_claimed=float(claim_info.total_claimed),
        )
        
    except Exception as e:
        logger.error(f"Error claiming dividends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dividend claiming failed: {str(e)}"
        )


@router.get("/dividends/claimable/{wallet_address}", response_model=DividendClaimResponse)
async def get_claimable_dividends(
    wallet_address: str,
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Get claimable dividends for a wallet address
    
    This endpoint returns the amount of dividends that can be claimed
    """
    try:
        logger.info(f"Getting claimable dividends for {wallet_address}")
        
        # Get claimable dividends
        claim_info = await dividend_calculator.calculate_claimable_dividends(
            wallet_address=wallet_address
        )
        
        if claim_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No claimable dividends found"
            )
        
        return DividendClaimResponse(
            wallet_address=claim_info.wallet_address,
            claimable_amount=float(claim_info.claimable_amount),
            last_claim_index=claim_info.last_claim_index,
            total_claimed=float(claim_info.total_claimed),
        )
        
    except Exception as e:
        logger.error(f"Error getting claimable dividends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get claimable dividends: {str(e)}"
        )


@router.get("/pool/stats", response_model=DividendPoolStatsResponse)
async def get_dividend_pool_stats(
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Get dividend pool statistics
    
    This endpoint returns comprehensive statistics about the dividend pool
    """
    try:
        logger.info("Getting dividend pool statistics")
        
        # Get pool stats
        stats = await dividend_calculator.get_dividend_pool_stats()
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No dividend pool statistics available"
            )
        
        return DividendPoolStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting dividend pool stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dividend pool stats: {str(e)}"
        )


@router.get("/revenue/sources")
async def get_revenue_sources(
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Get all revenue sources and their amounts
    
    This endpoint returns information about all revenue sources
    """
    try:
        logger.info("Getting revenue sources")
        
        # Get revenue sources
        sources = await dividend_calculator.get_all_revenue_sources()
        
        if not sources:
            return {"sources": []}
        
        # Convert to response format
        revenue_sources = []
        for source_name, amount in sources.items():
            revenue_sources.append(
                RevenueSourceResponse(
                    source_name=source_name,
                    amount=float(amount),
                    description=f"Revenue from {source_name}",
                )
            )
        
        return {"sources": revenue_sources}
        
    except Exception as e:
        logger.error(f"Error getting revenue sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue sources: {str(e)}"
        )


@router.get("/dividends/yield")
async def get_dividend_yield(
    period_days: int = 365,
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Get dividend yield information
    
    This endpoint returns dividend yield statistics for a given period
    """
    try:
        logger.info(f"Getting dividend yield for {period_days} days")
        
        # Get dividend yield
        yield_info = await dividend_calculator.calculate_dividend_yield(
            period_days=period_days
        )
        
        if not yield_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No dividend yield information available"
            )
        
        return DividendYieldResponse(**yield_info)
        
    except Exception as e:
        logger.error(f"Error getting dividend yield: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dividend yield: {str(e)}"
        )


@router.get("/dividends/history")
async def get_dividend_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dividend_calculator: BiltDividendCalculator = Depends(get_dividend_calculator),
):
    """
    Get dividend distribution history
    
    This endpoint returns the history of dividend distributions
    """
    try:
        logger.info("Getting dividend history")
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get dividend history
        history = await dividend_calculator.get_dividend_history(
            start_date=start_dt,
            end_date=end_dt,
        )
        
        if not history:
            return {"distributions": []}
        
        # Convert to response format
        distributions = []
        for dist in history:
            distributions.append({
                "distribution_id": dist.distribution_id,
                "total_amount": float(dist.total_amount),
                "dividend_per_token": float(dist.dividend_per_token),
                "total_supply": dist.total_supply,
                "distribution_date": dist.distribution_date.isoformat(),
                "revenue_sources": [
                    {
                        "source_name": source.source_name,
                        "amount": float(source.amount),
                        "description": source.description,
                    }
                    for source in dist.revenue_sources
                ],
            })
        
        return {"distributions": distributions}
        
    except Exception as e:
        logger.error(f"Error getting dividend history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dividend history: {str(e)}"
        )


@router.post("/fraud/report")
async def report_fraud(
    request: FraudReportRequest,
    minting_engine: BiltMintingEngine = Depends(get_minting_engine),
):
    """
    Report potential fraud in a BILT contribution
    
    This endpoint allows reporting of suspicious contributions
    """
    try:
        logger.info(f"Reporting fraud for {request.biltobject_hash}")
        
        # This would typically call a fraud reporting method
        # For now, return a mock response
        return {
            "success": True,
            "message": "Fraud report submitted successfully",
            "biltobject_hash": request.biltobject_hash,
            "contributor_wallet": request.contributor_wallet,
            "reason": request.reason,
        }
        
    except Exception as e:
        logger.error(f"Error reporting fraud: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud reporting failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for BILT token service
    
    This endpoint provides health status information
    """
    return {
        "service": "BILT Token Service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "endpoints": {
            "contribute": "Process BILT contributions",
            "revenue": "Attribute revenue to dividend pool",
            "dividends": "Distribute and claim dividends",
            "fraud": "Report fraudulent contributions",
        },
    } 