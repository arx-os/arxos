"""
Planarx Community Platform - Main Application
Integrates all community components including funding escrow system
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path

# Import routers
from routes.home import router as home_router
from drafts.draft_model import router as drafts_router
from mod.mod_dashboard import router as mod_router
from engagement.onboarding_flow import router as onboarding_router
from funding.routes.init_escrow import router as escrow_router
from core.security.auth_middleware import get_current_user, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Planarx Community Platform",
    description="A comprehensive community platform for building design and collaboration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include routers
app.include_router(home_router, prefix="/api")
app.include_router(drafts_router, prefix="/api/drafts")
app.include_router(mod_router, prefix="/api/mod")
app.include_router(onboarding_router, prefix="/api/onboarding")
app.include_router(escrow_router, prefix="/api/funding")

# Frontend routes
@app.get("/", response_class=HTMLResponse)
    async def homepage(user: User = Depends(get_current_user)):
    """Serve the main homepage"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Homepage not found")

@app.get("/submit", response_class=HTMLResponse)
    async def submit_page(user: User = Depends(get_current_user)):
    """Serve the project submission page"""
    try:
        with open("frontend/submit_design.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Submit page not found")

@app.get("/my-drafts", response_class=HTMLResponse)
    async def my_drafts_page(user: User = Depends(get_current_user)):
    """Serve the drafts management page"""
    try:
        with open("frontend/my_drafts.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Drafts page not found")

@app.get("/mod-dashboard", response_class=HTMLResponse)
    async def mod_dashboard_page(user: User = Depends(get_current_user)):
    """Serve the moderator dashboard page"""
    try:
        with open("frontend/mod_dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Moderator dashboard not found")

@app.get("/funding/{project_id}", response_class=HTMLResponse)
    async def funding_page(project_id: str, user: User = Depends(get_current_user)):
    """Serve the funding escrow panel for a specific project"""
    try:
        with open("funding/frontend/escrow_panel.html", "r", encoding="utf-8") as f:
            content = f.read()
            # Inject project ID into the page
            content = content.replace('esc-123456', f'esc-{project_id}')
            return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Funding page not found")

# Health check endpoint
@app.get("/health")
    async def health_check(user: User = Depends(get_current_user)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "home": "active",
            "drafts": "active",
            "moderation": "active",
            "onboarding": "active",
            "funding": "active"
        }
    }

# API documentation redirect
@app.get("/docs")
    async def docs_redirect(user: User = Depends(get_current_user)):
    """Redirect to API documentation"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")

# Error handlers
@app.exception_handler(404)
    async def not_found_handler(request, exc, user: User = Depends(get_current_user)):
    """Handle 404 errors"""
    return {
        "error": "Not found",
        "message": "The requested resource was not found",
        "path": str(request.url.path)
    }

@app.exception_handler(500)
    async def internal_error_handler(request, exc, user: User = Depends(get_current_user)):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }

# Startup event
@app.on_event("startup")
    async def startup_event(user: User = Depends(get_current_user)):
    """Application startup event"""
    logger.info("Planarx Community Platform starting up...")

    # Create necessary directories
    os.makedirs("data/projects", exist_ok=True)
    os.makedirs("data/drafts", exist_ok=True)
    os.makedirs("data/funding", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)

    logger.info("Planarx Community Platform started successfully")

# Shutdown event
@app.on_event("shutdown")
    async def shutdown_event(user: User = Depends(get_current_user)):
    """Application shutdown event"""
    logger.info("Planarx Community Platform shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
