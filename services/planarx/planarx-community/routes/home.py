"""
Planarx Community Platform - Homepage Routes

Main routes for the Planarx community platform homepage including:
- Project discovery and browsing
- Featured designs and trending projects
- Community overview and statistics
- Search and filtering functionality
- User onboarding and welcome flow
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import asyncio

from ..models.project import Project, ProjectStatus, ProjectCategory
from ..models.user import User, UserRole
from ..models.draft import Draft, DraftStatus
from ..services.project_service import ProjectService
from ..services.user_service import UserService
from ..services.reputation_service import ReputationService
from ..services.engagement_service import EngagementService
from ..utils.auth import get_current_user, require_auth
from ..utils.pagination import PaginationParams

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/home", tags=["Homepage"])

# Initialize services
project_service = ProjectService()
user_service = UserService()
reputation_service = ReputationService()
engagement_service = EngagementService()


# Pydantic Models for API

class HomepageStats(BaseModel):
    """
    Class for HomepageStats functionality

Attributes:
        None

Methods:
        None

Example:
        instance = HomepageStats()
        result = instance.method()
        print(result)
    """
    total_projects: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    total_users: int = Field(..., description="Total number of users")
    total_funding_raised: float = Field(..., description="Total funding raised")
    projects_this_month: int = Field(..., description="Projects created this month")
    top_contributors: List[Dict[str, Any]] = Field(..., description="Top contributors")
    trending_projects: List[Dict[str, Any]] = Field(..., description="Trending projects")
    featured_projects: List[Dict[str, Any]] = Field(..., description="Featured projects")


class ProjectSearchParams(BaseModel):
    category: Optional[str] = Field(None, description="Project category filter")
    status: Optional[str] = Field(None, description="Project status filter")
    funding_min: Optional[float] = Field(None, description="Minimum funding amount")
    funding_max: Optional[float] = Field(None, description="Maximum funding amount")
    tags: Optional[List[str]] = Field(None, description="Project tags filter")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order")


class ProjectDiscoveryResponse(BaseModel):
    projects: List[Dict[str, Any]] = Field(..., description="List of projects")
    total_count: int = Field(..., description="Total number of projects")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# Homepage Routes

@router.get("/", response_class=HTMLResponse)
async def homepage():
    """Render the main homepage."""
    try:
        # Get homepage data
        stats = await get_homepage_stats()
        featured_projects = await get_featured_projects()
        trending_projects = await get_trending_projects()
        recent_projects = await get_recent_projects()

        # Render homepage template
        return render_homepage_template(
            stats=stats,
            featured_projects=featured_projects,
            trending_projects=trending_projects,
            recent_projects=recent_projects
        )

    except Exception as e:
        logger.error(f"Error rendering homepage: {e}")
        raise HTTPException(status_code=500, detail="Failed to load homepage")


@router.get("/api/stats", response_model=HomepageStats)
async def get_homepage_stats():
    """Get homepage statistics and overview data."""
    try:
        # Get basic stats
        total_projects = await project_service.get_total_projects()
        active_projects = await project_service.get_active_projects_count()
        total_users = await user_service.get_total_users()
        total_funding = await project_service.get_total_funding_raised()
        projects_this_month = await project_service.get_projects_this_month()

        # Get top contributors
        top_contributors = await reputation_service.get_top_contributors(limit=10)

        # Get trending projects
        trending_projects = await project_service.get_trending_projects(limit=6)

        # Get featured projects
        featured_projects = await project_service.get_featured_projects(limit=6)

        return HomepageStats(
            total_projects=total_projects,
            active_projects=active_projects,
            total_users=total_users,
            total_funding_raised=total_funding,
            projects_this_month=projects_this_month,
            top_contributors=top_contributors,
            trending_projects=trending_projects,
            featured_projects=featured_projects
        )

    except Exception as e:
        logger.error(f"Error getting homepage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get homepage stats")


@router.get("/api/discover", response_model=ProjectDiscoveryResponse)
async def discover_projects(
    category: Optional[str] = Query(None, description="Project category"),
    status: Optional[str] = Query(None, description="Project status"),
    funding_min: Optional[float] = Query(None, description="Minimum funding"),
    funding_max: Optional[float] = Query(None, description="Maximum funding"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=50, description="Page size")
):
    """Discover and browse projects with filtering and pagination."""
    try:
        # Parse tags
        tag_list = tags.split(",") if tags else None

        # Build search parameters
        search_params = ProjectSearchParams(
            category=category,
            status=status,
            funding_min=funding_min,
            funding_max=funding_max,
            tags=tag_list,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get pagination parameters
        pagination = PaginationParams(page=page, page_size=page_size)

        # Search projects
        projects, total_count = await project_service.search_projects(
            search_params, pagination
        )

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        return ProjectDiscoveryResponse(
            projects=projects,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error discovering projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to discover projects")


@router.get("/api/featured")
async def get_featured_projects():
    """Get featured projects for homepage."""
    try:
        featured_projects = await project_service.get_featured_projects(limit=6)
        return {"featured_projects": featured_projects}

    except Exception as e:
        logger.error(f"Error getting featured projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get featured projects")


@router.get("/api/trending")
async def get_trending_projects():
    """Get trending projects based on engagement metrics."""
    try:
        trending_projects = await project_service.get_trending_projects(limit=6)
        return {"trending_projects": trending_projects}

    except Exception as e:
        logger.error(f"Error getting trending projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending projects")


@router.get("/api/recent")
async def get_recent_projects():
    """Get recently created projects."""
    try:
        recent_projects = await project_service.get_recent_projects(limit=8)
        return {"recent_projects": recent_projects}

    except Exception as e:
        logger.error(f"Error getting recent projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent projects")


@router.get("/api/categories")
async def get_project_categories():
    """Get available project categories."""
    try:
        categories = await project_service.get_project_categories()
        return {"categories": categories}

    except Exception as e:
        logger.error(f"Error getting project categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project categories")


@router.get("/api/tags")
async def get_popular_tags():
    """Get popular project tags."""
    try:
        popular_tags = await project_service.get_popular_tags(limit=20)
        return {"popular_tags": popular_tags}

    except Exception as e:
        logger.error(f"Error getting popular tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular tags")


@router.get("/api/search")
async def search_projects(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=50, description="Page size")
):
    """Search projects by title, description, and tags."""
    try:
        # Get pagination parameters
        pagination = PaginationParams(page=page, page_size=page_size)

        # Search projects
        projects, total_count = await project_service.search_projects_by_text(
            q, pagination
        )

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "projects": projects,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "query": q
        }

    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to search projects")


# Helper Functions

async def get_homepage_stats() -> Dict[str, Any]:
    """Get homepage statistics."""
    try:
        # Get basic stats
        total_projects = await project_service.get_total_projects()
        active_projects = await project_service.get_active_projects_count()
        total_users = await user_service.get_total_users()
        total_funding = await project_service.get_total_funding_raised()
        projects_this_month = await project_service.get_projects_this_month()

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_users": total_users,
            "total_funding_raised": total_funding,
            "projects_this_month": projects_this_month
        }

    except Exception as e:
        logger.error(f"Error getting homepage stats: {e}")
        return {
            "total_projects": 0,
            "active_projects": 0,
            "total_users": 0,
            "total_funding_raised": 0.0,
            "projects_this_month": 0
        }


async def get_featured_projects() -> List[Dict[str, Any]]:
    """Get featured projects for homepage."""
    try:
        return await project_service.get_featured_projects(limit=6)
    except Exception as e:
        logger.error(f"Error getting featured projects: {e}")
        return []


async def get_trending_projects() -> List[Dict[str, Any]]:
    """Get trending projects based on engagement."""
    try:
        return await project_service.get_trending_projects(limit=6)
    except Exception as e:
        logger.error(f"Error getting trending projects: {e}")
        return []


async def get_recent_projects() -> List[Dict[str, Any]]:
    """Get recently created projects."""
    try:
        return await project_service.get_recent_projects(limit=8)
    except Exception as e:
        logger.error(f"Error getting recent projects: {e}")
        return []


def render_homepage_template(
    stats: Dict[str, Any],
    featured_projects: List[Dict[str, Any]],
    trending_projects: List[Dict[str, Any]],
    recent_projects: List[Dict[str, Any]]
) -> str:
    """Render the homepage HTML template."""
    # This would typically use a template engine like Jinja2
    # For now, return a simple HTML structure
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Planarx Community - Building the Future Together</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50">
        <header class="bg-white shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-6">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-gray-900">Planarx Community</h1>
                    </div>
                    <nav class="flex space-x-8">
                        <a href="/discover" class="text-gray-500 hover:text-gray-900">Discover</a>
                        <a href="/submit" class="text-gray-500 hover:text-gray-900">Submit Design</a>
                        <a href="/about" class="text-gray-500 hover:text-gray-900">About</a>
                        <a href="/login" class="text-gray-500 hover:text-gray-900">Login</a>
                    </nav>
                </div>
            </div>
        </header>

        <main>
            <!-- Hero Section -->
            <section class="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 class="text-4xl font-bold mb-4">Building the Future Together</h2>
                    <p class="text-xl mb-8">Join the community of creators, designers, and builders shaping the future of architecture and construction.</p>
                    <div class="flex justify-center space-x-4">
                        <a href="/submit" class="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100">Submit Your Design</a>
                        <a href="/discover" class="border border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600">Explore Projects</a>
                    </div>
                </div>
            </section>

            <!-- Stats Section -->
            <section class="py-12 bg-white">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="grid grid-cols-2 md:grid-cols-5 gap-8 text-center">
                        <div>
                            <div class="text-3xl font-bold text-blue-600">{stats['total_projects']}</div>
                            <div class="text-gray-600">Projects</div>
                        </div>
                        <div>
                            <div class="text-3xl font-bold text-green-600">{stats['active_projects']}</div>
                            <div class="text-gray-600">Active</div>
                        </div>
                        <div>
                            <div class="text-3xl font-bold text-purple-600">{stats['total_users']}</div>
                            <div class="text-gray-600">Creators</div>
                        </div>
                        <div>
                            <div class="text-3xl font-bold text-yellow-600">${stats['total_funding_raised']:,.0f}</div>
                            <div class="text-gray-600">Raised</div>
                        </div>
                        <div>
                            <div class="text-3xl font-bold text-red-600">{stats['projects_this_month']}</div>
                            <div class="text-gray-600">This Month</div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Featured Projects -->
            <section class="py-12">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h3 class="text-2xl font-bold text-gray-900 mb-8">Featured Projects</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {render_project_cards(featured_projects)}
                    </div>
                </div>
            </section>

            <!-- Trending Projects -->
            <section class="py-12 bg-gray-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h3 class="text-2xl font-bold text-gray-900 mb-8">Trending Now</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {render_project_cards(trending_projects)}
                    </div>
                </div>
            </section>

            <!-- Recent Projects -->
            <section class="py-12">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h3 class="text-2xl font-bold text-gray-900 mb-8">Recently Added</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {render_project_cards(recent_projects)}
                    </div>
                </div>
            </section>
        </main>

        <footer class="bg-gray-800 text-white py-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Planarx Community</h4>
                        <p class="text-gray-300">Building the future of architecture and construction through community collaboration.</p>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Community</h4>
                        <ul class="space-y-2 text-gray-300">
                            <li><a href="/guidelines" class="hover:text-white">Guidelines</a></li>
                            <li><a href="/moderation" class="hover:text-white">Moderation</a></li>
                            <li><a href="/governance" class="hover:text-white">Governance</a></li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Resources</h4>
                        <ul class="space-y-2 text-gray-300">
                            <li><a href="/help" class="hover:text-white">Help Center</a></li>
                            <li><a href="/api" class="hover:text-white">API</a></li>
                            <li><a href="/docs" class="hover:text-white">Documentation</a></li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Connect</h4>
                        <ul class="space-y-2 text-gray-300">
                            <li><a href="/discord" class="hover:text-white">Discord</a></li>
                            <li><a href="/twitter" class="hover:text-white">Twitter</a></li>
                            <li><a href="/github" class="hover:text-white">GitHub</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </footer>
    </body>
    </html>
    """


def render_project_cards(projects: List[Dict[str, Any]]) -> str:
    """Render project cards HTML."""
    if not projects:
        return '<div class="col-span-full text-center text-gray-500">No projects found</div>'

    cards = []
    for project in projects:
        cards.append(f"""
        <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            <div class="aspect-w-16 aspect-h-9 bg-gray-200">
                <img src="{project.get('image_url', '/static/placeholder.jpg')}" alt="{project.get('title', 'Project')}" class="w-full h-full object-cover">
            </div>
            <div class="p-6">
                <h4 class="text-lg font-semibold text-gray-900 mb-2">{project.get('title', 'Untitled Project')}</h4>
                <p class="text-gray-600 text-sm mb-4">{project.get('description', '')[:100]}...</p>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-500">by {project.get('creator_name', 'Anonymous')}</span>
                    <span class="text-sm font-semibold text-green-600">${project.get('funding_raised', 0):,.0f}</span>
                </div>
            </div>
        </div>
        """)
    return ''.join(cards)


# Error handling middleware
@router.exception_handler(Exception)
async def homepage_exception_handler(request, exc):
    """Handle exceptions in homepage endpoints."""
    logger.error(f"Homepage error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error in homepage",
            "timestamp": datetime.now().isoformat()
        }
    )
