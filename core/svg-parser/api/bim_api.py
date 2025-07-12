"""
BIM API & Service Layer (FastAPI)

- Exposes BIM assembly, query, validation, and export endpoints
- Supports user/project context for multi-user, multi-project workflows
- Provides webhook/event hooks for assembly completion, conflict detection, etc.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import io
import json
import logging
from datetime import datetime

from services.bim_assembly import BIMAssemblyPipeline
from services.persistence_export_interoperability import (
    BIMSerializer, BIMExporter, ExportFormat, ExportOptions, PersistenceExportManager,
    create_persistence_manager
)
from services.robust_error_handling import create_error_handler
from utils.errors import BIMAssemblyError, ExportError, ValidationError

logger = logging.getLogger(__name__)

app = FastAPI(title="Arxos BIM API", version="1.0")

# CORS (allow all for demo; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory webhook registry (for demo)
webhook_registry: Dict[str, List[str]] = {}

# In-memory BIM model store (for demo; use DB in production)
bim_models: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models for API ---
class BIMAssemblyRequest(BaseModel):
    svg_data: str
    user_id: str
    project_id: str
    metadata: Optional[Dict[str, Any]] = None

class BIMQueryRequest(BaseModel):
    model_id: str
    user_id: str
    project_id: str
    query: Optional[Dict[str, Any]] = None

class BIMValidationRequest(BaseModel):
    model_id: str
    user_id: str
    project_id: str

class BIMExportRequest(BaseModel):
    model_id: str
    user_id: str
    project_id: str
    format: ExportFormat = ExportFormat.JSON
    options: Optional[Dict[str, Any]] = None

class WebhookRegistrationRequest(BaseModel):
    event: str
    url: str
    user_id: str
    project_id: str

# --- API Endpoints ---

@app.post("/bim/assemble", summary="Assemble BIM from SVG", response_model=Dict[str, Any])
def assemble_bim(request: BIMAssemblyRequest, background_tasks: BackgroundTasks):
    """Assemble a BIM model from SVG data, with user/project context."""
    handler = create_error_handler()
    try:
        # Assemble BIM
        pipeline = BIMAssemblyPipeline()
        svg_data = {"svg": request.svg_data, "metadata": request.model_metadata or {}}
        result = pipeline.assemble_bim(svg_data, metadata={
            "user_id": request.user_id,
            "project_id": request.project_id
        })
        model_id = str(uuid.uuid4())
        bim_models[model_id] = BIMSerializer.to_dict(result)
        # Trigger webhooks for assembly completion
        background_tasks.add_task(trigger_webhooks, "assembly_completed", model_id, request.user_id, request.project_id)
        return {"model_id": model_id, "result": bim_models[model_id]}
    except Exception as e:
        handler.handle_exception(e, "BIM assembly API")
        return JSONResponse(status_code=500, content={"error": str(e), "report": handler.get_report_dict(success=False)})

@app.post("/bim/query", summary="Query BIM model", response_model=Dict[str, Any])
def query_bim(request: BIMQueryRequest):
    """Query a BIM model by ID and property filters."""
    model = bim_models.get(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    # Simple property-based query (MVP)
    if request.query:
        filtered = [el for el in model.get("rooms", []) if all(el.get(k) == v for k, v in request.query.items())]
        return {"rooms": filtered}
    return model

@app.post("/bim/validate", summary="Validate BIM model", response_model=Dict[str, Any])
def validate_bim(request: BIMValidationRequest):
    """Validate a BIM model by ID."""
    model = bim_models.get(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    # For demo, just check required fields
    errors = []
    if not model.get("rooms"):
        errors.append("No rooms present")
    if not model.get("walls"):
        errors.append("No walls present")
    return {"valid": not errors, "errors": errors}

@app.post("/bim/export", summary="Export BIM model", response_model=Dict[str, Any])
def export_bim(request: BIMExportRequest):
    """Export a BIM model in the specified format."""
    model = bim_models.get(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        bim_model = BIMSerializer.from_dict(model, BIMAssemblyPipeline.AssemblyResult)
        options = ExportOptions(format=request.format, **(request.options or {}))
        exporter = BIMExporter()
        export_data = exporter.export_bim_model(bim_model, options)
        if isinstance(export_data, bytes):
            return StreamingResponse(io.BytesIO(export_data), media_type="application/octet-stream")
        return {"export": export_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/register", summary="Register webhook for events")
def register_webhook(request: WebhookRegistrationRequest):
    """Register a webhook URL for a specific event, user, and project."""
    key = f"{request.event}:{request.user_id}:{request.project_id}"
    if key not in webhook_registry:
        webhook_registry[key] = []
    webhook_registry[key].append(request.url)
    return {"status": "registered", "event": request.event, "url": request.url}

# --- Event/Webhook Triggering ---
def trigger_webhooks(event: str, model_id: str, user_id: str, project_id: str):
    key = f"{event}:{user_id}:{project_id}"
    urls = webhook_registry.get(key, [])
    for url in urls:
        try:
            import requests
            payload = {"event": event, "model_id": model_id, "user_id": user_id, "project_id": project_id, "timestamp": datetime.utcnow().isoformat()}
            requests.post(url, json=payload, timeout=2)
            logger.info(f"Webhook triggered: {url} for event {event}")
        except Exception as e:
            logger.error(f"Failed to trigger webhook {url}: {e}")

# --- Health Check ---
@app.get("/health", summary="Health check")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()} 