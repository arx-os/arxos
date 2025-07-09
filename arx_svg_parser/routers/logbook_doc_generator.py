"""
Logbook to Doc Generator Router

Provides RESTful API endpoints for generating, retrieving, and monitoring documentation
from logbook entries in multiple formats (Markdown, JSON, HTML).
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from services.logbook_doc_generator import (
    LogbookDocGenerator, DocFormat, LogEntryType
)

router = APIRouter(prefix="/logbook-docs", tags=["Logbook to Doc Generator"])

generator = LogbookDocGenerator()

@router.post("/generate")
async def generate_documentation(
    doc_type: str = Body(..., description="Type of documentation: changelog, contributor_summary, system_evolution"),
    format: str = Body("markdown", description="Output format: markdown, json, html"),
    start_date: Optional[str] = Body(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Body(None, description="End date (ISO format)"),
    template_id: Optional[str] = Body(None, description="Template ID to use"),
    custom_variables: Optional[Dict[str, Any]] = Body(None, description="Custom variables for template")
) -> Dict[str, Any]:
    """
    Generate documentation from logbook entries.
    """
    try:
        fmt = DocFormat(format.lower())
        sd = datetime.fromisoformat(start_date) if start_date else None
        ed = datetime.fromisoformat(end_date) if end_date else None
        doc = generator.generate_documentation(
            doc_type=doc_type,
            format=fmt,
            start_date=sd,
            end_date=ed,
            template_id=template_id,
            custom_variables=custom_variables
        )
        return {
            "status": "success",
            "document_id": doc.document_id,
            "title": doc.title,
            "format": doc.format.value,
            "content": doc.content,
            "metadata": doc.metadata,
            "generated_at": doc.generated_at.isoformat(),
            "processing_time": doc.processing_time,
            "entry_count": doc.entry_count
        }
    except Exception as e:
        logging.error(f"Failed to generate documentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}")
async def get_document(document_id: str) -> Dict[str, Any]:
    """
    Retrieve a generated documentation by ID.
    """
    try:
        import sqlite3, json
        from datetime import datetime
        with sqlite3.connect(generator.db_path) as conn:
            cursor = conn.execute("SELECT title, format, content, metadata, generated_at, processing_time, entry_count FROM generated_docs WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
            return {
                "status": "success",
                "document_id": document_id,
                "title": row[0],
                "format": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "generated_at": row[4],
                "processing_time": row[5],
                "entry_count": row[6]
            }
    except Exception as e:
        logging.error(f"Failed to retrieve document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_logbook_doc_status() -> Dict[str, Any]:
    """
    Get Logbook Doc Generator service status and metrics.
    """
    try:
        metrics = generator.get_performance_metrics()
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 