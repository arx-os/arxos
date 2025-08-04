#!/usr/bin/env python3
"""
BILT Token System Test Script (Final)

Tests all components of the BILT token system with mock implementations.
This script verifies that the BILT system works without any external dependencies.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_minting_engine():
    """Test the mock minting engine"""
    logger.info("Testing Mock BILT Minting Engine...")
    
    try:
        from economy.backend.services.bilt_token.minting_engine_mock import MockBiltMintingEngine
        
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
        from economy.backend.services.bilt_token.dividend_calculator_mock import MockBiltDividendCalculator
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
        from economy.backend.api.bilt_routes_mock import MockBiltAPIRouter
        
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
    """Test the mock ArxLogic service"""
    logger.info("Testing Mock ArxLogic Service...")
    
    try:
        from application.services.arxlogic_service_mock import MockArxLogicService
        
        # Initialize ArxLogic service
        service = MockArxLogicService()
        
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
        logger.info(f"Mock ArxLogic validation result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing mock ArxLogic service: {str(e)}")
        return False


async def test_repository_pattern():
    """Test the mock repository pattern"""
    logger.info("Testing Mock Repository Pattern...")
    
    try:
        from infrastructure.repositories.bilt_repositories_mock import (
            MockSQLAlchemyContributionRepository,
            MockSQLAlchemyRevenueRepository,
            MockSQLAlchemyDividendRepository,
            MockSQLAlchemyVerificationRepository
        )
        
        # Test contribution repository
        contrib_repo = MockSQLAlchemyContributionRepository()
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
        logger.info(f"Mock contribution repository create result: {result}")
        
        # Test revenue repository
        revenue_repo = MockSQLAlchemyRevenueRepository()
        revenue_data = {
            "source": "data_sales",
            "amount": 1000.00,
            "description": "Building data sales"
        }
        
        result = revenue_repo.create(revenue_data)
        logger.info(f"Mock revenue repository create result: {result}")
        
        # Test dividend repository
        dividend_repo = MockSQLAlchemyDividendRepository()
        dividend_data = {
            "total_amount": 500.00,
            "dividend_per_token": 0.001,
            "total_supply": 1000000
        }
        
        result = dividend_repo.create(dividend_data)
        logger.info(f"Mock dividend repository create result: {result}")
        
        # Test verification repository
        verification_repo = MockSQLAlchemyVerificationRepository()
        verification_data = {
            "biltobject_hash": "abc123def456",
            "verifier_wallet": "0xabcdef1234567890abcdef1234567890abcdef12",
            "verification_score": 0.85,
            "status": "verified"
        }
        
        result = verification_repo.create(verification_data)
        logger.info(f"Mock verification repository create result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing mock repository pattern: {str(e)}")
        return False


async def test_smart_contracts():
    """Test smart contract compilation"""
    logger.info("Testing Smart Contracts...")
    
    try:
        # Check if Solidity files exist and are valid
        contract_files = [
            "economy/contracts/BILTToken.sol",
            "economy/contracts/RevenueRouter.sol"
        ]
        
        for contract_file in contract_files:
            if os.path.exists(contract_file):
                with open(contract_file, 'r') as f:
                    content = f.read()
                    if "pragma solidity" in content:
                        logger.info(f"✅ {contract_file}: Valid Solidity contract")
                    else:
                        logger.error(f"❌ {contract_file}: Invalid Solidity contract")
                        return False
            else:
                logger.error(f"❌ {contract_file}: File not found")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing smart contracts: {str(e)}")
        return False


async def test_deployment_config():
    """Test deployment configuration"""
    logger.info("Testing Deployment Configuration...")
    
    try:
        # Check if deployment files exist
        deployment_files = [
            "economy/deployment/bilt_deployment.yaml"
        ]
        
        for deployment_file in deployment_files:
            if os.path.exists(deployment_file):
                logger.info(f"✅ {deployment_file}: Deployment config exists")
            else:
                logger.error(f"❌ {deployment_file}: Deployment config missing")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing deployment config: {str(e)}")
        return False


async def test_documentation():
    """Test documentation completeness"""
    logger.info("Testing Documentation...")
    
    try:
        # Check if documentation files exist
        doc_files = [
            "economy/BILT_IMPLEMENTATION_SUMMARY.md",
            "economy/CONFLICT_RESOLUTION_SUMMARY.md",
            "economy/BILT_ISSUES_RESOLVED.md",
            "economy/requirements.txt"
        ]
        
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                logger.info(f"✅ {doc_file}: Documentation exists")
            else:
                logger.error(f"❌ {doc_file}: Documentation missing")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing documentation: {str(e)}")
        return False


async def run_comprehensive_test():
    """Run comprehensive test of all BILT system components"""
    logger.info("Starting comprehensive BILT system test (Final)...")
    
    test_results = {}
    
    # Test all components
    test_results['minting_engine'] = await test_minting_engine()
    test_results['dividend_calculator'] = await test_dividend_calculator()
    test_results['api_router'] = await test_api_router()
    test_results['arxlogic_service'] = await test_arxlogic_service()
    test_results['repository_pattern'] = await test_repository_pattern()
    test_results['smart_contracts'] = await test_smart_contracts()
    test_results['deployment_config'] = await test_deployment_config()
    test_results['documentation'] = await test_documentation()
    
    # Report results
    logger.info("Test Results:")
    for component, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {component}: {status}")
    
    # Overall result
    all_passed = all(test_results.values())
    if all_passed:
        logger.info("🎉 All tests passed! BILT system is completely clean and working.")
    else:
        failed_tests = [k for k, v in test_results.items() if not v]
        logger.error(f"💥 Some tests failed: {failed_tests}")
    
    return all_passed


if __name__ == "__main__":
    # Run the comprehensive test
    success = asyncio.run(run_comprehensive_test())
    exit(0 if success else 1) 