"""
Knowledge Base API Routes

This module provides REST API endpoints for the knowledge base system,
including search, jurisdiction management, version control, and references.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from knowledge.knowledge_base import KnowledgeBase, CodeRequirement
from knowledge.search_engine import SearchEngine, SearchQuery, SearchResult
from knowledge.jurisdiction_manager import (
    JurisdictionManager,
    JurisdictionInfo,
    JurisdictionAmendment,
)
from knowledge.version_control import VersionControl, CodeVersionInfo, CodeChange
from knowledge.code_reference import CodeReference, CodeReferenceManager

from auth.authentication import get_current_user, require_permission, Permission

logger = logging.getLogger(__name__)

# Initialize components
knowledge_base = KnowledgeBase()
search_engine = SearchEngine()
jurisdiction_manager = JurisdictionManager()
version_control = VersionControl()
code_reference_manager = CodeReferenceManager()

# Create router
router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request model"""

    query: str = Field(..., description="Search query")
    code_standard: Optional[str] = Field(None, description="Filter by code standard")
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    version: Optional[str] = Field(None, description="Filter by version")
    max_results: int = Field(50, description="Maximum number of results")
    min_relevance: float = Field(0.1, description="Minimum relevance score")


class SearchResponse(BaseModel):
    """Search response model"""

    results: List[SearchResult]
    statistics: Dict[str, Any]
    query: str
    total_results: int


class CodeSectionRequest(BaseModel):
    """Code section request model"""

    code_standard: str = Field(..., description="Code standard")
    section_number: str = Field(..., description="Section number")


class JurisdictionComplianceRequest(BaseModel):
    """Jurisdiction compliance request model"""

    jurisdiction: str = Field(..., description="Jurisdiction")
    code_standard: str = Field(..., description="Code standard")
    section_number: str = Field(..., description="Section number")


# Knowledge Base Routes
@router.get("/codes", response_model=Dict[str, str])
async def get_supported_codes(current_user=Depends(get_current_user)):
    """Get list of supported building codes"""
    try:
        codes = await knowledge_base.get_supported_codes()
        return codes
    except Exception as e:
        logger.error(f"❌ Error getting supported codes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get supported codes")


@router.get(
    "/codes/{code_standard}/sections/{section_number}", response_model=CodeRequirement
)
async def get_code_section(
    code_standard: str, section_number: str, current_user=Depends(get_current_user)
):
    """Get a specific code section"""
    try:
        section = await knowledge_base.get_code_section(code_standard, section_number)
        if not section:
            raise HTTPException(status_code=404, detail="Code section not found")
        return section
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting code section: {e}")
        raise HTTPException(status_code=500, detail="Failed to get code section")


@router.post("/codes", response_model=Dict[str, bool])
async def add_code_section(
    code_requirement: CodeRequirement,
    current_user=Depends(require_permission(Permission.MANAGE_CODES)),
):
    """Add a new code section"""
    try:
        success = await knowledge_base.add_code_section(code_requirement)
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error adding code section: {e}")
        raise HTTPException(status_code=500, detail="Failed to add code section")


@router.put(
    "/codes/{code_standard}/sections/{section_number}", response_model=Dict[str, bool]
)
async def update_code_section(
    code_standard: str,
    section_number: str,
    updates: Dict[str, Any],
    current_user=Depends(require_permission(Permission.MANAGE_CODES)),
):
    """Update a code section"""
    try:
        success = await knowledge_base.update_code_section(
            code_standard, section_number, updates
        )
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error updating code section: {e}")
        raise HTTPException(status_code=500, detail="Failed to update code section")


@router.delete(
    "/codes/{code_standard}/sections/{section_number}", response_model=Dict[str, bool]
)
async def delete_code_section(
    code_standard: str,
    section_number: str,
    current_user=Depends(require_permission(Permission.MANAGE_CODES)),
):
    """Delete a code section"""
    try:
        success = await knowledge_base.delete_code_section(
            code_standard, section_number
        )
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error deleting code section: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete code section")


@router.get("/codes/statistics", response_model=Dict[str, Any])
async def get_knowledge_base_statistics(current_user=Depends(get_current_user)):
    """Get knowledge base statistics"""
    try:
        stats = await knowledge_base.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting knowledge base statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# Search Routes
@router.post("/search", response_model=SearchResponse)
async def search_codes(
    search_request: SearchRequest, current_user=Depends(get_current_user)
):
    """Search building codes"""
    try:
        # Get all code requirements for search
        all_requirements = await knowledge_base.search_codes("", None, None)

        # Perform search
        search_query = SearchQuery(
            query=search_request.query,
            code_standard=search_request.code_standard,
            jurisdiction=search_request.jurisdiction,
            version=search_request.version,
            max_results=search_request.max_results,
            min_relevance=search_request.min_relevance,
        )

        results = await search_engine.search(search_query, all_requirements)
        statistics = await search_engine.get_search_statistics(results)

        return SearchResponse(
            results=results,
            statistics=statistics,
            query=search_request.query,
            total_results=len(results),
        )
    except Exception as e:
        logger.error(f"❌ Error searching codes: {e}")
        raise HTTPException(status_code=500, detail="Failed to search codes")


@router.get("/search/suggestions", response_model=List[str])
async def get_search_suggestions(
    query: str = Query(..., description="Partial search query"),
    current_user=Depends(get_current_user),
):
    """Get search suggestions"""
    try:
        suggestions = await search_engine.get_search_suggestions(query)
        return suggestions
    except Exception as e:
        logger.error(f"❌ Error getting search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search suggestions")


# Jurisdiction Routes
@router.get("/jurisdictions", response_model=List[JurisdictionInfo])
async def get_all_jurisdictions(current_user=Depends(get_current_user)):
    """Get all jurisdictions"""
    try:
        jurisdictions = await jurisdiction_manager.get_all_jurisdictions()
        return jurisdictions
    except Exception as e:
        logger.error(f"❌ Error getting jurisdictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jurisdictions")


@router.get("/jurisdictions/{jurisdiction}", response_model=JurisdictionInfo)
async def get_jurisdiction_info(
    jurisdiction: str, current_user=Depends(get_current_user)
):
    """Get information about a specific jurisdiction"""
    try:
        jurisdiction_info = await jurisdiction_manager.get_jurisdiction_info(
            jurisdiction
        )
        if not jurisdiction_info:
            raise HTTPException(status_code=404, detail="Jurisdiction not found")
        return jurisdiction_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting jurisdiction info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jurisdiction info")


@router.get(
    "/jurisdictions/{jurisdiction}/amendments",
    response_model=List[JurisdictionAmendment],
)
async def get_jurisdiction_amendments(
    jurisdiction: str,
    code_standard: Optional[str] = Query(None, description="Filter by code standard"),
    current_user=Depends(get_current_user),
):
    """Get amendments for a jurisdiction"""
    try:
        amendments = await jurisdiction_manager.get_jurisdiction_amendments(
            jurisdiction, code_standard
        )
        return amendments
    except Exception as e:
        logger.error(f"❌ Error getting jurisdiction amendments: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get jurisdiction amendments"
        )


@router.post("/jurisdictions/amendments", response_model=Dict[str, bool])
async def add_jurisdiction_amendment(
    amendment: JurisdictionAmendment,
    current_user=Depends(require_permission(Permission.MANAGE_JURISDICTIONS)),
):
    """Add a jurisdiction amendment"""
    try:
        success = await jurisdiction_manager.add_jurisdiction_amendment(amendment)
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error adding jurisdiction amendment: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to add jurisdiction amendment"
        )


@router.post("/jurisdictions/compliance", response_model=Dict[str, Any])
async def check_jurisdiction_compliance(
    request: JurisdictionComplianceRequest, current_user=Depends(get_current_user)
):
    """Check jurisdiction compliance for a code section"""
    try:
        compliance = await jurisdiction_manager.check_jurisdiction_compliance(
            request.jurisdiction, request.code_standard, request.section_number
        )
        return compliance
    except Exception as e:
        logger.error(f"❌ Error checking jurisdiction compliance: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to check jurisdiction compliance"
        )


@router.get("/jurisdictions/statistics", response_model=Dict[str, Any])
async def get_jurisdiction_statistics(current_user=Depends(get_current_user)):
    """Get jurisdiction amendment statistics"""
    try:
        stats = await jurisdiction_manager.get_amendment_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting jurisdiction statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get jurisdiction statistics"
        )


# Version Control Routes
@router.get("/versions", response_model=List[CodeVersionInfo])
async def get_code_versions(
    code_standard: Optional[str] = Query(None, description="Filter by code standard"),
    current_user=Depends(get_current_user),
):
    """Get code versions"""
    try:
        versions = await version_control.get_code_versions(code_standard)
        return versions
    except Exception as e:
        logger.error(f"❌ Error getting code versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get code versions")


@router.get("/versions/{code_standard}/active", response_model=CodeVersionInfo)
async def get_active_version(
    code_standard: str, current_user=Depends(get_current_user)
):
    """Get active version for a code standard"""
    try:
        version = await version_control.get_active_version(code_standard)
        if not version:
            raise HTTPException(status_code=404, detail="Active version not found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting active version: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active version")


@router.post("/versions", response_model=Dict[str, bool])
async def add_code_version(
    version_info: CodeVersionInfo,
    current_user=Depends(require_permission(Permission.MANAGE_VERSIONS)),
):
    """Add a new code version"""
    try:
        success = await version_control.add_code_version(version_info)
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error adding code version: {e}")
        raise HTTPException(status_code=500, detail="Failed to add code version")


@router.put(
    "/versions/{code_standard}/{version_number}/activate",
    response_model=Dict[str, bool],
)
async def activate_version(
    code_standard: str,
    version_number: str,
    current_user=Depends(require_permission(Permission.MANAGE_VERSIONS)),
):
    """Activate a code version"""
    try:
        success = await version_control.activate_version(code_standard, version_number)
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error activating version: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate version")


@router.get("/versions/{code_standard}/timeline", response_model=List[Dict[str, Any]])
async def get_version_timeline(
    code_standard: str, current_user=Depends(get_current_user)
):
    """Get version timeline for a code standard"""
    try:
        timeline = await version_control.get_version_timeline(code_standard)
        return timeline
    except Exception as e:
        logger.error(f"❌ Error getting version timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to get version timeline")


@router.get("/versions/statistics", response_model=Dict[str, Any])
async def get_version_statistics(current_user=Depends(get_current_user)):
    """Get version control statistics"""
    try:
        stats = await version_control.get_version_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting version statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get version statistics")


# Code Reference Routes
@router.get(
    "/references/{code_standard}/{section_number}/cross-references",
    response_model=List[CodeReference],
)
async def get_cross_references(
    code_standard: str, section_number: str, current_user=Depends(get_current_user)
):
    """Get cross-references for a code section"""
    try:
        references = await code_reference_manager.get_cross_references(
            code_standard, section_number
        )
        return references
    except Exception as e:
        logger.error(f"❌ Error getting cross references: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cross references")


@router.get(
    "/references/{code_standard}/{section_number}/related",
    response_model=List[CodeReference],
)
async def get_related_sections(
    code_standard: str, section_number: str, current_user=Depends(get_current_user)
):
    """Get related sections for a code section"""
    try:
        references = await code_reference_manager.get_related_sections(
            code_standard, section_number
        )
        return references
    except Exception as e:
        logger.error(f"❌ Error getting related sections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get related sections")


@router.get(
    "/references/{code_standard}/{section_number}/all",
    response_model=List[CodeReference],
)
async def get_all_references(
    code_standard: str, section_number: str, current_user=Depends(get_current_user)
):
    """Get all references for a code section"""
    try:
        references = await code_reference_manager.get_all_references(
            code_standard, section_number
        )
        return references
    except Exception as e:
        logger.error(f"❌ Error getting all references: {e}")
        raise HTTPException(status_code=500, detail="Failed to get all references")


@router.post("/references", response_model=Dict[str, bool])
async def add_code_reference(
    reference: CodeReference,
    current_user=Depends(require_permission(Permission.MANAGE_REFERENCES)),
):
    """Add a code reference"""
    try:
        success = await code_reference_manager.add_code_reference(reference)
        return {"success": success}
    except Exception as e:
        logger.error(f"❌ Error adding code reference: {e}")
        raise HTTPException(status_code=500, detail="Failed to add code reference")


@router.get("/references/statistics", response_model=Dict[str, Any])
async def get_reference_statistics(current_user=Depends(get_current_user)):
    """Get code reference statistics"""
    try:
        stats = await code_reference_manager.get_reference_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting reference statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get reference statistics"
        )


@router.get(
    "/references/{code_standard}/{section_number}/chain",
    response_model=List[Dict[str, Any]],
)
async def get_reference_chain(
    code_standard: str,
    section_number: str,
    max_depth: int = Query(3, description="Maximum depth of reference chain"),
    current_user=Depends(get_current_user),
):
    """Get reference chain for a code section"""
    try:
        chain = await code_reference_manager.get_reference_chain(
            code_standard, section_number, max_depth
        )
        return chain
    except Exception as e:
        logger.error(f"❌ Error getting reference chain: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reference chain")


# Health check route
@router.get("/health", response_model=Dict[str, str])
async def knowledge_base_health():
    """Health check for knowledge base system"""
    return {"status": "healthy", "message": "Knowledge base system is operational"}
