#!/usr/bin/env python3
"""
Report API Routes for MCP Service

This module provides API endpoints for report generation and management.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from auth.authentication import get_current_user, require_permission, Permission
from report.report_service import create_report_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/reports", tags=["reports"])


# Pydantic models for request/response
class ReportGenerationRequest(BaseModel):
    building_id: str
    report_type: str = (
        "comprehensive"  # comprehensive, violation_summary, executive_summary
    )
    include_email: bool = False
    email_recipients: List[str] = []
    email_subject: Optional[str] = None
    email_message: Optional[str] = None


class ReportGenerationResponse(BaseModel):
    success: bool
    report_path: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    report_type: str
    generated_at: str
    cloud_urls: Dict[str, str] = {}
    error: Optional[str] = None


class EmailReportRequest(BaseModel):
    report_path: str
    recipients: List[str]
    subject: Optional[str] = None
    message: Optional[str] = None


class ReportHistoryItem(BaseModel):
    filename: str
    file_path: str
    file_size: int
    report_type: Optional[str] = None
    building_id: Optional[str] = None
    created_at: str
    modified_at: str


class ReportHistoryResponse(BaseModel):
    reports: List[ReportHistoryItem]
    total_count: int
    filtered_count: int


# Initialize report service
def get_report_service():
    """Get report service instance"""
    config = {
        "reports_dir": os.getenv("REPORTS_DIR", "reports"),
        "email": {
            "smtp_host": os.getenv("SMTP_HOST"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_email": os.getenv("FROM_EMAIL", "noreply@arxos.com"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        },
        "storage": {
            "aws": {
                "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "bucket": os.getenv("AWS_S3_BUCKET"),
            },
            "azure": {
                "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
                "container": os.getenv("AZURE_STORAGE_CONTAINER"),
            },
        },
    }
    return create_report_service(config)


# API Endpoints


@router.post("/generate", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest,
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    """
    Generate a building code compliance report

    Requires: read_validation permission
    """
    try:
        # Check permissions
        if not current_user.has_permission(Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403, detail="Permission denied: read_validation required"
            )

        # Get validation data from cache or perform validation
        from cache.redis_manager import redis_manager

        validation_data = await redis_manager.get_cached_validation(request.building_id)

        if not validation_data:
            raise HTTPException(
                status_code=404, detail="Validation data not found for building"
            )

        # Get building information
        building_info = {
            "building_id": request.building_id,
            "building_name": f"Building {request.building_id}",
            "location": "Unknown",
            "building_type": "Commercial",
            "construction_year": "2024",
            "total_area": "Unknown",
            "floors": "Unknown",
            "occupancy_type": "Mixed",
            "fire_rating": "Unknown",
            "structural_system": "Unknown",
        }

        # Generate report
        if request.include_email and request.email_recipients:
            result = await report_service.generate_and_send_report(
                validation_data,
                building_info,
                request.email_recipients,
                request.report_type,
            )
        else:
            result = await report_service.generate_compliance_report(
                validation_data, building_info, request.report_type
            )

        return ReportGenerationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


@router.post("/email", response_model=Dict[str, Any])
async def send_report_email(
    request: EmailReportRequest,
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    """
    Send a report via email

    Requires: read_validation permission
    """
    try:
        # Check permissions
        if not current_user.has_permission(Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403, detail="Permission denied: read_validation required"
            )

        # Send email
        result = await report_service.send_report_email(
            request.report_path, request.recipients, request.subject, request.message
        )

        return result

    except Exception as e:
        logger.error(f"Failed to send report email: {e}")
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


@router.get("/download/{filename}")
async def download_report(
    filename: str,
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    """
    Download a generated report

    Requires: read_validation permission
    """
    try:
        # Check permissions
        if not current_user.has_permission(Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403, detail="Permission denied: read_validation required"
            )

        # Check if file exists
        file_path = report_service.reports_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        # Return file response
        return FileResponse(
            path=str(file_path), filename=filename, media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/history", response_model=ReportHistoryResponse)
async def get_report_history(
    building_id: Optional[str] = None,
    limit: int = 50,
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    """
    Get report generation history

    Requires: read_validation permission
    """
    try:
        # Check permissions
        if not current_user.has_permission(Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403, detail="Permission denied: read_validation required"
            )

        # Get report history
        reports = await report_service.get_report_history(building_id, limit)

        return ReportHistoryResponse(
            reports=[ReportHistoryItem(**report) for report in reports],
            total_count=len(reports),
            filtered_count=len(reports),
        )

    except Exception as e:
        logger.error(f"Failed to get report history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get report history: {str(e)}"
        )


@router.delete("/{filename}")
async def delete_report(
    filename: str,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    report_service=Depends(get_report_service),
):
    """
    Delete a report file

    Requires: system_admin permission
    """
    try:
        # Delete report
        result = await report_service.delete_report(filename)

        if not result["success"]:
            raise HTTPException(
                status_code=404, detail=result.get("error", "Failed to delete report")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete report: {str(e)}"
        )


@router.get("/stats")
async def get_report_stats(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    report_service=Depends(get_report_service),
):
    """
    Get report generation statistics

    Requires: system_admin permission
    """
    try:
        # Get all reports
        reports = await report_service.get_report_history(limit=1000)

        # Calculate statistics
        total_reports = len(reports)
        total_size = sum(report["file_size"] for report in reports)

        # Group by report type
        report_types = {}
        for report in reports:
            report_type = report.get("report_type", "unknown")
            if report_type not in report_types:
                report_types[report_type] = 0
            report_types[report_type] += 1

        # Group by building
        buildings = {}
        for report in reports:
            building_id = report.get("building_id", "unknown")
            if building_id not in buildings:
                buildings[building_id] = 0
            buildings[building_id] += 1

        stats = {
            "total_reports": total_reports,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "report_types": report_types,
            "buildings": buildings,
            "generated_at": datetime.now().isoformat(),
        }

        return stats

    except Exception as e:
        logger.error(f"Failed to get report stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get report stats: {str(e)}"
        )


@router.post("/generate-from-validation")
async def generate_report_from_validation(
    building_id: str,
    report_type: str = "comprehensive",
    include_email: bool = False,
    email_recipients: List[str] = [],
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    """
    Generate report from validation results

    This endpoint performs validation and generates a report in one operation.
    """
    try:
        # Check permissions
        if not current_user.has_permission(Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403, detail="Permission denied: read_validation required"
            )

        # Perform validation (this would integrate with your validation service)
        from validate.rule_engine import MCPRuleEngine

        rule_engine = MCPRuleEngine()

        # Create a sample building model for validation
        building_model = {
            "building_id": building_id,
            "building_name": f"Building {building_id}",
            "objects": [],
            "metadata": {},
        }

        # Perform validation
        validation_data = rule_engine.validate_building_model(building_model, [])

        # Building information
        building_info = {
            "building_id": building_id,
            "building_name": f"Building {building_id}",
            "location": "Unknown",
            "building_type": "Commercial",
            "construction_year": "2024",
            "total_area": "Unknown",
            "floors": "Unknown",
            "occupancy_type": "Mixed",
            "fire_rating": "Unknown",
            "structural_system": "Unknown",
        }

        # Generate report
        if include_email and email_recipients:
            result = await report_service.generate_and_send_report(
                validation_data, building_info, email_recipients, report_type
            )
        else:
            result = await report_service.generate_compliance_report(
                validation_data, building_info, report_type
            )

        return result

    except Exception as e:
        logger.error(f"Failed to generate report from validation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


# Health check endpoint for report service
@router.get("/health")
async def report_service_health():
    """Health check for report service"""
    try:
        report_service = get_report_service()

        # Check if reports directory exists and is writable
        reports_dir = report_service.reports_dir
        if not reports_dir.exists():
            reports_dir.mkdir(exist_ok=True)

        # Test file creation
        test_file = reports_dir / "health_test.txt"
        test_file.write_text("health check")
        test_file.unlink()

        return {
            "status": "healthy",
            "service": "report_service",
            "reports_dir": str(reports_dir),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Report service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "report_service",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
