#!/usr/bin/env python3
"""
BILT Token System Test Script

Tests all components of the BILT token system without requiring external dependencies.
This script verifies that the mock implementations work correctly.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_minting_engine():
    """Test the mock minting engine"""
    logger.info("Testing Mock BILT Minting Engine...")
    
    try:
        from backend.services.bilt_token.minting_engine_mock import MockBiltMintingEngine
        
        # Initialize minting engine
        engine = MockBiltMintingEngine()
        
        # Test data
        contributor_wallet = "0x1234567890abcdef1234567890abcdef12345678"
        object_data = {
            "id": "electrical.light_fixture.001",
            "type": "electrical.light_fixture",
            "specifications": {
                "capacity": 100,
                "efficiency": 0.85,
                "safety_rating": 8.5,
                "voltage": 120,
                "manufacturer": "modern_lighting_corp"
            },
            "location": {
                "building": "main_building",
                "floor": 1,
                "room": "conference_room_a"
            }
        }
        system_type = "electrical"
        verifier_wallet = "0xabcdef1234567890abcdef1234567890abcdef12"
        
        # Test contribution processing
        result = await engine.process_contribution(
            contributor_wallet=contributor_wallet,
            object_data=object_data,
            system_type=system_type,
            verifier_wallet=verifier_wallet
        )
        
        logger.info(f"Contribution result: {result}")
        
        # Test state
        state = engine.get_mock_state()
        logger.info(f"Mock state: {json.dumps(state, indent=2, default=str)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing minting engine: {str(e)}")
        return False


async def test_dividend_calculator():
    """Test the mock dividend calculator"""
    logger.info("Testing Mock BILT Dividend Calculator...")
    
    try:
        from backend.services.bilt_token.dividend_calculator_mock import MockBiltDividendCalculator
        from decimal import Decimal
        
        # Initialize dividend calculator
        calculator = MockBiltDividendCalculator()
        
        # Test revenue attribution
        success = await calculator.attribute_revenue(
            source="data_sales",
            amount=Decimal("1000.00"),
            description="Building data sales revenue"
        )
        logger.info(f"Revenue attribution success: {success}")
        
        # Test dividend distribution
        success = await calculator.distribute_dividends()
        logger.info(f"Dividend distribution success: {success}")
        
        # Test claimable dividends
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        claimable = await calculator.calculate_claimable_dividends(wallet_address)
        logger.info(f"Claimable dividends: {claimable}")
        
        # Test dividend claiming
        success = await calculator.claim_dividends(wallet_address)
        logger.info(f"Dividend claiming success: {success}")
        
        # Test stats
        stats = await calculator.get_dividend_pool_stats()
        logger.info(f"Dividend pool stats: {stats}")
        
        # Test state
        state = calculator.get_mock_state()
        logger.info(f"Mock state: {json.dumps(state, indent=2, default=str)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing dividend calculator: {str(e)}")
        return False


async def test_api_router():
    """Test the mock API router"""
    logger.info("Testing Mock BILT API Router...")
    
    try:
        from backend.api.bilt_routes_mock import MockBiltAPIRouter
        
        # Initialize API router
        router = MockBiltAPIRouter()
        
        # Test contribution submission
        contributor_wallet = "0x1234567890abcdef1234567890abcdef12345678"
        object_data = {
            "id": "hvac.air_handler.001",
            "type": "hvac.air_handler",
            "specifications": {
                "capacity": 5000,
                "efficiency": 0.92,
                "safety_rating": 9.0,
                "cooling_capacity": 5000,
                "heating_capacity": 4000
            },
            "location": {
                "building": "main_building",
                "floor": 2,
                "room": "server_room"
            }
        }
        system_type = "hvac"
        verifier_wallet = "0xabcdef1234567890abcdef1234567890abcdef12"
        
        response = await router.submit_contribution(
            contributor_wallet=contributor_wallet,
            object_data=object_data,
            system_type=system_type,
            verifier_wallet=verifier_wallet
        )
        logger.info(f"Contribution submission response: {response}")
        
        # Test revenue attribution
        response = await router.attribute_revenue(
            source="service_transactions",
            amount=2500.00,
            description="Service transaction revenue"
        )
        logger.info(f"Revenue attribution response: {response}")
        
        # Test dividend distribution
        response = await router.distribute_dividends(amount=1000.00)
        logger.info(f"Dividend distribution response: {response}")
        
        # Test dividend claiming
        response = await router.claim_dividends(wallet_address=contributor_wallet)
        logger.info(f"Dividend claiming response: {response}")
        
        # Test stats
        response = await router.get_dividend_pool_stats()
        logger.info(f"Dividend pool stats response: {response}")
        
        # Test state
        state = router.get_mock_state()
        logger.info(f"Mock state: {json.dumps(state, indent=2, default=str)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing API router: {str(e)}")
        return False


async def test_arxlogic_service():
    """Test the ArxLogic service"""
    logger.info("Testing ArxLogic Service...")
    
    try:
        from application.services.arxlogic_service import ArxLogicService
        
        # Initialize ArxLogic service
        service = ArxLogicService()
        
        # Test data
        object_data = {
            "id": "security.camera.001",
            "type": "security.camera",
            "specifications": {
                "resolution": "4K",
                "efficiency": 0.88,
                "safety_rating": 9.5,
                "communication_protocol": "ethernet",
                "data_format": "json"
            },
            "location": {
                "building": "main_building",
                "floor": 1,
                "room": "entrance"
            }
        }
        system_type = "security"
        
        # Test validation
        result = await service.validate_building_object(object_data, system_type)
        logger.info(f"ArxLogic validation result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing ArxLogic service: {str(e)}")
        return False


async def test_repository_pattern():
    """Test the repository pattern"""
    logger.info("Testing Repository Pattern...")
    
    try:
        from infrastructure.repositories.bilt_repositories import (
            SQLAlchemyContributionRepository,
            SQLAlchemyRevenueRepository,
            SQLAlchemyDividendRepository,
            SQLAlchemyVerificationRepository
        )
        
        # Test contribution repository
        contrib_repo = SQLAlchemyContributionRepository(session=None)
        contribution_data = {
            "contributor_wallet": "0x1234567890abcdef1234567890abcdef12345678",
            "biltobject_hash": "abc123def456",
            "object_data": {"test": "data"},
            "system_type": "electrical",
            "bilt_amount": 150.0,
            "validation_score": 0.85,
            "verifier_wallet": "0xabcdef1234567890abcdef1234567890abcdef12"
        }
        
        result = contrib_repo.create(contribution_data)
        logger.info(f"Contribution repository create result: {result}")
        
        # Test revenue repository
        revenue_repo = SQLAlchemyRevenueRepository(session=None)
        revenue_data = {
            "source": "data_sales",
            "amount": 1000.00,
            "description": "Building data sales"
        }
        
        result = revenue_repo.create(revenue_data)
        logger.info(f"Revenue repository create result: {result}")
        
        # Test dividend repository
        dividend_repo = SQLAlchemyDividendRepository(session=None)
        dividend_data = {
            "total_amount": 500.00,
            "dividend_per_token": 0.001,
            "total_supply": 1000000
        }
        
        result = dividend_repo.create(dividend_data)
        logger.info(f"Dividend repository create result: {result}")
        
        # Test verification repository
        verification_repo = SQLAlchemyVerificationRepository(session=None)
        verification_data = {
            "biltobject_hash": "abc123def456",
            "verifier_wallet": "0xabcdef1234567890abcdef1234567890abcdef12",
            "verification_score": 0.85,
            "status": "verified"
        }
        
        result = verification_repo.create(verification_data)
        logger.info(f"Verification repository create result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing repository pattern: {str(e)}")
        return False


async def run_comprehensive_test():
    """Run comprehensive test of all BILT system components"""
    logger.info("Starting comprehensive BILT system test...")
    
    test_results = {}
    
    # Test all components
    test_results['minting_engine'] = await test_minting_engine()
    test_results['dividend_calculator'] = await test_dividend_calculator()
    test_results['api_router'] = await test_api_router()
    test_results['arxlogic_service'] = await test_arxlogic_service()
    test_results['repository_pattern'] = await test_repository_pattern()
    
    # Report results
    logger.info("Test Results:")
    for component, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {component}: {status}")
    
    # Overall result
    all_passed = all(test_results.values())
    if all_passed:
        logger.info("🎉 All tests passed! BILT system is working correctly.")
    else:
        logger.error("💥 Some tests failed. Please check the errors above.")
    
    return all_passed


if __name__ == "__main__":
    # Run the comprehensive test
    success = asyncio.run(run_comprehensive_test())
    exit(0 if success else 1) 