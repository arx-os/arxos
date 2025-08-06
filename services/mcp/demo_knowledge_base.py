#!/usr/bin/env python3
"""
Knowledge Base System Demo

This script demonstrates the knowledge base functionality with real-world examples
including building code search, jurisdiction compliance, and version management.
"""

import asyncio
import logging
from datetime import datetime

from knowledge.knowledge_base import KnowledgeBase, CodeRequirement
from knowledge.search_engine import SearchEngine, SearchQuery
from knowledge.jurisdiction_manager import JurisdictionManager
from knowledge.version_control import VersionControl
from knowledge.code_reference import CodeReference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_building_code_search():
    """Demonstrate building code search functionality"""
    logger.info("🔍 DEMO: Building Code Search")
    logger.info("=" * 50)

    kb = KnowledgeBase()
    search = SearchEngine()

    # Get all code requirements
    all_requirements = await kb.search_codes("", None, None)
    logger.info(f"📚 Knowledge base contains {len(all_requirements)} code sections")

    # Demo 1: Search for occupant load requirements
    logger.info("\n🏢 Demo 1: Occupant Load Requirements")
    search_query = SearchQuery(query="occupant load calculation", max_results=3)
    results = await search.search(search_query, all_requirements)

    for i, result in enumerate(results, 1):
        logger.info(
            f"\n{i}. {result.code_requirement.code_standard} {result.code_requirement.section_number}"
        )
        logger.info(f"   Title: {result.code_requirement.title}")
        logger.info(f"   Relevance: {result.relevance_score:.3f}")
        logger.info(f"   Matched terms: {', '.join(result.matched_terms)}")

    # Demo 2: Search for electrical safety
    logger.info("\n⚡ Demo 2: Electrical Safety Requirements")
    search_query = SearchQuery(query="GFCI protection electrical safety", max_results=3)
    results = await search.search(search_query, all_requirements)

    for i, result in enumerate(results, 1):
        logger.info(
            f"\n{i}. {result.code_requirement.code_standard} {result.code_requirement.section_number}"
        )
        logger.info(f"   Title: {result.code_requirement.title}")
        logger.info(f"   Relevance: {result.relevance_score:.3f}")

    # Demo 3: Search for accessibility
    logger.info("\n♿ Demo 3: Accessibility Requirements")
    search_query = SearchQuery(
        query="ADA accessibility new construction", max_results=3
    )
    results = await search.search(search_query, all_requirements)

    for i, result in enumerate(results, 1):
        logger.info(
            f"\n{i}. {result.code_requirement.code_standard} {result.code_requirement.section_number}"
        )
        logger.info(f"   Title: {result.code_requirement.title}")
        logger.info(f"   Relevance: {result.relevance_score:.3f}")


async def demo_jurisdiction_compliance():
    """Demonstrate jurisdiction compliance functionality"""
    logger.info("\n🏛️ DEMO: Jurisdiction Compliance")
    logger.info("=" * 50)

    jurisdiction = JurisdictionManager()

    # Demo 1: Get all jurisdictions
    jurisdictions = await jurisdiction.get_all_jurisdictions()
    logger.info(f"📋 Available jurisdictions: {len(jurisdictions)}")

    for jur in jurisdictions:
        logger.info(f"\n🏛️ {jur.jurisdiction}")
        logger.info(f"   Country: {jur.country}")
        if jur.state:
            logger.info(f"   State: {jur.state}")
        logger.info(f"   Code standards: {', '.join(jur.code_standards)}")
        logger.info(f"   Local amendments: {jur.amendments_count}")

    # Demo 2: Check California compliance
    logger.info("\n🌴 Demo 2: California Compliance Check")
    compliance = await jurisdiction.check_jurisdiction_compliance(
        "California", "IBC", "1004.1.1"
    )

    logger.info(f"Jurisdiction: {compliance['jurisdiction']}")
    logger.info(f"Code standard: {compliance['code_standard']}")
    logger.info(f"Section: {compliance['section_number']}")
    logger.info(f"Has amendments: {compliance['has_amendments']}")

    if compliance["amendments"]:
        for amendment in compliance["amendments"]:
            logger.info(f"   Amendment type: {amendment['amendment_type']}")
            logger.info(f"   Effective date: {amendment['effective_date']}")
            logger.info(f"   Reason: {amendment['reason']}")

    # Demo 3: Get California amendments
    logger.info("\n📝 Demo 3: California Amendments")
    amendments = await jurisdiction.get_jurisdiction_amendments("California")

    for amendment in amendments:
        logger.info(f"\n{amendment.code_standard} {amendment.section_number}")
        logger.info(f"Type: {amendment.amendment_type}")
        logger.info(f"Effective: {amendment.effective_date.strftime('%Y-%m-%d')}")


async def demo_version_control():
    """Demonstrate version control functionality"""
    logger.info("\n📚 DEMO: Version Control")
    logger.info("=" * 50)

    version_control = VersionControl()

    # Demo 1: Get all versions
    logger.info("\n📋 Demo 1: Available Code Versions")
    versions = await version_control.get_code_versions()

    for version in versions:
        status = "⭐ ACTIVE" if version.is_active else "📄 INACTIVE"
        logger.info(f"\n{status} {version.code_standard} {version.version_number}")
        logger.info(f"   Release date: {version.release_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Effective date: {version.effective_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Changes: {version.change_summary}")

    # Demo 2: Get active versions
    logger.info("\n⭐ Demo 2: Active Versions")
    code_standards = ["IBC", "NEC", "ADA"]

    for standard in code_standards:
        active_version = await version_control.get_active_version(standard)
        if active_version:
            logger.info(f"\n{standard}: {active_version.version_number}")
            logger.info(
                f"   Release: {active_version.release_date.strftime('%Y-%m-%d')}"
            )
            logger.info(
                f"   Effective: {active_version.effective_date.strftime('%Y-%m-%d')}"
            )
        else:
            logger.info(f"\n{standard}: No active version found")

    # Demo 3: Get version timeline
    logger.info("\n📅 Demo 3: IBC Version Timeline")
    timeline = await version_control.get_version_timeline("IBC")

    for version in timeline:
        status = "⭐" if version["is_active"] else "📄"
        logger.info(f"\n{status} {version['version']}")
        logger.info(f"   Release: {version['release_date']}")
        logger.info(f"   Effective: {version['effective_date']}")
        logger.info(f"   Changes: {version['change_summary']}")


async def demo_code_references():
    """Demonstrate code reference functionality"""
    logger.info("\n🔗 DEMO: Code References")
    logger.info("=" * 50)

    code_ref = CodeReference()

    # Demo 1: Get cross references
    logger.info("\n🔗 Demo 1: Cross References for IBC 1004.1.1")
    cross_refs = await code_ref.get_cross_references("IBC", "1004.1.1")

    for ref in cross_refs:
        logger.info(
            f"\n{ref.source_code} {ref.source_section} → {ref.target_code} {ref.target_section}"
        )
        logger.info(f"Type: {ref.reference_type}")
        logger.info(f"Description: {ref.description}")

    # Demo 2: Get related sections
    logger.info("\n📖 Demo 2: Related Sections for NEC 210.8")
    related = await code_ref.get_related_sections("NEC", "210.8")

    for ref in related:
        logger.info(
            f"\n{ref.source_code} {ref.source_section} → {ref.target_code} {ref.target_section}"
        )
        logger.info(f"Type: {ref.reference_type}")
        logger.info(f"Description: {ref.description}")

    # Demo 3: Get reference chain
    logger.info("\n🔗 Demo 3: Reference Chain for IBC 1004.1.1")
    chain = await code_ref.get_reference_chain("IBC", "1004.1.1", max_depth=2)

    for ref in chain:
        indent = "  " * ref["depth"]
        logger.info(f"{indent}📄 {ref['source']} → {ref['target']}")
        logger.info(f"{indent}   Type: {ref['type']}")
        logger.info(f"{indent}   Description: {ref['description']}")


async def demo_statistics():
    """Demonstrate system statistics"""
    logger.info("\n📊 DEMO: System Statistics")
    logger.info("=" * 50)

    kb = KnowledgeBase()
    jurisdiction = JurisdictionManager()
    version_control = VersionControl()
    code_ref = CodeReference()

    # Get all statistics
    kb_stats = await kb.get_statistics()
    jurisdiction_stats = await jurisdiction.get_amendment_statistics()
    version_stats = await version_control.get_version_statistics()
    reference_stats = await code_ref.get_reference_statistics()

    logger.info("\n📚 Knowledge Base Statistics:")
    logger.info(f"   Total sections: {kb_stats['total_sections']}")
    logger.info(f"   Active sections: {kb_stats['active_sections']}")
    logger.info(f"   Supported codes: {kb_stats['supported_codes']}")

    logger.info("\n🏛️ Jurisdiction Statistics:")
    logger.info(f"   Total amendments: {jurisdiction_stats['total_amendments']}")
    logger.info(f"   Active amendments: {jurisdiction_stats['active_amendments']}")

    logger.info("\n📚 Version Control Statistics:")
    logger.info(f"   Total versions: {version_stats['total_versions']}")
    logger.info(f"   Active versions: {version_stats['active_versions']}")

    logger.info("\n🔗 Reference Statistics:")
    logger.info(f"   Total references: {reference_stats['total_references']}")
    logger.info(f"   Active references: {reference_stats['active_references']}")


async def main():
    """Main demo function"""
    logger.info("🚀 KNOWLEDGE BASE SYSTEM DEMO")
    logger.info("=" * 60)
    logger.info("This demo showcases the comprehensive knowledge base system")
    logger.info("for building codes, jurisdiction management, and compliance.")
    logger.info("=" * 60)

    try:
        await demo_building_code_search()
        await demo_jurisdiction_compliance()
        await demo_version_control()
        await demo_code_references()
        await demo_statistics()

        logger.info("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        logger.info("The knowledge base system is ready for production use.")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
