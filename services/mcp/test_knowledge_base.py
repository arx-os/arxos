#!/usr/bin/env python3
"""
Test script for Knowledge Base System

This script tests the knowledge base functionality including search,
jurisdiction management, version control, and references.
"""

import asyncio
import logging
from datetime import datetime

from knowledge.knowledge_base import KnowledgeBase, CodeRequirement
from knowledge.search_engine import SearchEngine, SearchQuery
from knowledge.jurisdiction_manager import JurisdictionManager, JurisdictionAmendment
from knowledge.version_control import VersionControl, CodeVersionInfo
from knowledge.code_reference import CodeReference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_knowledge_base():
    """Test knowledge base functionality"""
    logger.info("🧪 Testing Knowledge Base System...")

    # Initialize components
    kb = KnowledgeBase()
    search = SearchEngine()
    jurisdiction = JurisdictionManager()
    version_control = VersionControl()
    code_ref = CodeReference()

    try:
        # Test 1: Get supported codes
        logger.info("📋 Test 1: Getting supported codes...")
        codes = await kb.get_supported_codes()
        logger.info(f"✅ Supported codes: {codes}")

        # Test 2: Search codes
        logger.info("🔍 Test 2: Searching codes...")
        search_query = SearchQuery(query="occupant load", max_results=5)
        all_requirements = await kb.search_codes("", None, None)
        results = await search.search(search_query, all_requirements)
        logger.info(f"✅ Search results: {len(results)} found")

        # Test 3: Get code section
        logger.info("📖 Test 3: Getting code section...")
        section = await kb.get_code_section("IBC", "1004.1.1")
        if section:
            logger.info(f"✅ Found section: {section.title}")

        # Test 4: Get jurisdictions
        logger.info("🏛️ Test 4: Getting jurisdictions...")
        jurisdictions = await jurisdiction.get_all_jurisdictions()
        logger.info(f"✅ Found {len(jurisdictions)} jurisdictions")

        # Test 5: Get jurisdiction amendments
        logger.info("📝 Test 5: Getting jurisdiction amendments...")
        amendments = await jurisdiction.get_jurisdiction_amendments("California")
        logger.info(f"✅ Found {len(amendments)} amendments for California")

        # Test 6: Get code versions
        logger.info("📚 Test 6: Getting code versions...")
        versions = await version_control.get_code_versions("IBC")
        logger.info(f"✅ Found {len(versions)} versions for IBC")

        # Test 7: Get active version
        logger.info("⭐ Test 7: Getting active version...")
        active_version = await version_control.get_active_version("IBC")
        if active_version:
            logger.info(f"✅ Active version: {active_version.version_number}")

        # Test 8: Get cross references
        logger.info("🔗 Test 8: Getting cross references...")
        references = await code_ref.get_cross_references("IBC", "1004.1.1")
        logger.info(f"✅ Found {len(references)} cross references")

        # Test 9: Get statistics
        logger.info("📊 Test 9: Getting statistics...")
        kb_stats = await kb.get_statistics()
        jurisdiction_stats = await jurisdiction.get_amendment_statistics()
        version_stats = await version_control.get_version_statistics()
        reference_stats = await code_ref.get_reference_statistics()

        logger.info(f"✅ Knowledge base stats: {kb_stats}")
        logger.info(f"✅ Jurisdiction stats: {jurisdiction_stats}")
        logger.info(f"✅ Version stats: {version_stats}")
        logger.info(f"✅ Reference stats: {reference_stats}")

        logger.info("🎉 All knowledge base tests passed!")

    except Exception as e:
        logger.error(f"❌ Knowledge base test failed: {e}")
        raise


async def test_search_functionality():
    """Test search functionality specifically"""
    logger.info("🔍 Testing Search Functionality...")

    kb = KnowledgeBase()
    search = SearchEngine()

    try:
        # Get all requirements
        all_requirements = await kb.search_codes("", None, None)
        logger.info(f"📚 Total code requirements: {len(all_requirements)}")

        # Test different search queries
        test_queries = [
            "occupant load",
            "fire safety",
            "electrical",
            "accessibility",
            "egress",
        ]

        for query in test_queries:
            logger.info(f"🔍 Testing search: '{query}'")
            search_query = SearchQuery(query=query, max_results=3)
            results = await search.search(search_query, all_requirements)
            logger.info(f"✅ Found {len(results)} results for '{query}'")

            if results:
                top_result = results[0]
                logger.info(f"   Top result: {top_result.code_requirement.title}")
                logger.info(f"   Relevance: {top_result.relevance_score:.3f}")

        logger.info("🎉 Search functionality tests passed!")

    except Exception as e:
        logger.error(f"❌ Search test failed: {e}")
        raise


async def test_jurisdiction_functionality():
    """Test jurisdiction functionality specifically"""
    logger.info("🏛️ Testing Jurisdiction Functionality...")

    jurisdiction = JurisdictionManager()

    try:
        # Get all jurisdictions
        jurisdictions = await jurisdiction.get_all_jurisdictions()
        logger.info(f"📋 Found {len(jurisdictions)} jurisdictions")

        for jur in jurisdictions:
            logger.info(f"🏛️ {jur.jurisdiction}: {jur.country}")
            if jur.state:
                logger.info(f"   State: {jur.state}")
            logger.info(f"   Code standards: {jur.code_standards}")
            logger.info(f"   Amendments: {jur.amendments_count}")

        # Test jurisdiction compliance
        compliance = await jurisdiction.check_jurisdiction_compliance(
            "California", "IBC", "1004.1.1"
        )
        logger.info(f"✅ California compliance check: {compliance}")

        logger.info("🎉 Jurisdiction functionality tests passed!")

    except Exception as e:
        logger.error(f"❌ Jurisdiction test failed: {e}")
        raise


async def main():
    """Main test function"""
    logger.info("🚀 Starting Knowledge Base System Tests...")

    try:
        await test_knowledge_base()
        await test_search_functionality()
        await test_jurisdiction_functionality()

        logger.info("🎉 All tests completed successfully!")

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
