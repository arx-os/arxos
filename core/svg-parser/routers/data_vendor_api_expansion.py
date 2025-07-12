"""
Data Vendor API Expansion Router

Provides RESTful API endpoints for advanced analytics, data masking,
encryption, compliance checking, and data export capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from services.data_vendor_api_expansion import (
    data_vendor_api_expansion,
    DataMaskingLevel,
    ComplianceType,
    AnalyticsMetrics
)
from utils.auth import get_current_user
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/vendor", tags=["Data Vendor API Expansion"])


@router.get("/analytics", response_model=Dict[str, Any])
async def get_vendor_analytics(
    vendor_id: Optional[str] = Query(None, description="Specific vendor ID to analyze"),
    time_range: Optional[str] = Query("30d", description="Time range for analysis (1d, 7d, 30d, 90d, 1y)"),
    metrics: Optional[List[str]] = Query(None, description="Specific metrics to calculate"),
    current_user: Any = Depends(get_current_user)
):
    """
    Get comprehensive analytics for vendor data.
    
    Returns detailed analytics including trends, predictions, and performance metrics.
    """
    try:
        logger.info(f"Analytics request for vendor_id: {vendor_id}, time_range: {time_range}")
        
        analytics = data_vendor_api_expansion.get_analytics(
            vendor_id=vendor_id,
            time_range=time_range,
            metrics=metrics
        )
        
        # Convert to dictionary for JSON response
        analytics_dict = {
            "total_records": analytics.total_records,
            "unique_vendors": analytics.unique_vendors,
            "data_quality_score": analytics.data_quality_score,
            "compliance_score": analytics.compliance_score,
            "last_updated": analytics.last_updated.isoformat(),
            "trends": analytics.trends,
            "predictions": analytics.predictions,
            "request_metadata": {
                "vendor_id": vendor_id,
                "time_range": time_range,
                "metrics_requested": metrics,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Analytics generated successfully for vendor_id: {vendor_id}")
        return analytics_dict
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.post("/mask-data", response_model=Dict[str, Any])
async def mask_sensitive_data(
    data: Dict[str, Any] = Body(..., description="Data to mask"),
    masking_level: DataMaskingLevel = Body(DataMaskingLevel.PARTIAL, description="Level of masking to apply"),
    custom_rules: Optional[Dict[str, Any]] = Body(None, description="Custom masking rules"),
    current_user: Any = Depends(get_current_user)
):
    """
    Mask sensitive data according to configured rules.
    
    Applies data masking to protect sensitive information while preserving data structure.
    """
    try:
        logger.info(f"Data masking request with level: {masking_level}")
        
        # Convert custom rules if provided
        converted_rules = None
        if custom_rules:
            from services.data_vendor_api_expansion import DataMaskingRule
            converted_rules = {}
            for field_name, rule_data in custom_rules.items():
                converted_rules[field_name] = DataMaskingRule(
                    field_name=field_name,
                    masking_level=DataMaskingLevel(rule_data.get("masking_level", "partial")),
                    custom_pattern=rule_data.get("custom_pattern"),
                    replacement_char=rule_data.get("replacement_char", "*"),
                    preserve_length=rule_data.get("preserve_length", True)
                )
        
        masked_data = data_vendor_api_expansion.mask_sensitive_data(
            data=data,
            masking_level=masking_level,
            custom_rules=converted_rules
        )
        
        response = {
            "masked_data": masked_data,
            "masking_applied": {
                "level": masking_level.value,
                "fields_processed": len(data),
                "custom_rules_used": bool(custom_rules)
            },
            "metadata": {
                "original_data_keys": list(data.keys()),
                "masked_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Data masking completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error masking data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mask data: {str(e)}")


@router.post("/encrypt-data", response_model=Dict[str, Any])
async def encrypt_sensitive_data(
    data: Dict[str, Any] = Body(..., description="Data to encrypt"),
    current_user: Any = Depends(get_current_user)
):
    """
    Encrypt sensitive data using AES-256 encryption.
    
    Encrypts sensitive fields while preserving non-sensitive data structure.
    """
    try:
        logger.info("Data encryption request")
        
        encrypted_data = data_vendor_api_expansion.encrypt_sensitive_data(data=data)
        
        # Count encrypted fields
        encrypted_fields = [
            key for key in data.keys() 
            if data_vendor_api_expansion._is_sensitive_field(key)
        ]
        
        response = {
            "encrypted_data": encrypted_data,
            "encryption_summary": {
                "total_fields": len(data),
                "encrypted_fields": len(encrypted_fields),
                "encrypted_field_names": encrypted_fields
            },
            "metadata": {
                "encryption_method": "AES-256",
                "encrypted_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Data encryption completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error encrypting data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to encrypt data: {str(e)}")


@router.post("/decrypt-data", response_model=Dict[str, Any])
async def decrypt_sensitive_data(
    encrypted_data: Dict[str, Any] = Body(..., description="Encrypted data to decrypt"),
    current_user: Any = Depends(get_current_user)
):
    """
    Decrypt sensitive data.
    
    Decrypts previously encrypted data while preserving data structure.
    """
    try:
        logger.info("Data decryption request")
        
        decrypted_data = data_vendor_api_expansion.decrypt_sensitive_data(encrypted_data=encrypted_data)
        
        # Count decrypted fields
        decrypted_fields = [
            key for key in encrypted_data.keys() 
            if data_vendor_api_expansion._is_sensitive_field(key)
        ]
        
        response = {
            "decrypted_data": decrypted_data,
            "decryption_summary": {
                "total_fields": len(encrypted_data),
                "decrypted_fields": len(decrypted_fields),
                "decrypted_field_names": decrypted_fields
            },
            "metadata": {
                "decryption_method": "AES-256",
                "decrypted_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Data decryption completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error decrypting data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to decrypt data: {str(e)}")


@router.post("/compliance-check", response_model=Dict[str, Any])
async def check_compliance(
    data: Dict[str, Any] = Body(..., description="Data to check for compliance"),
    compliance_type: ComplianceType = Body(..., description="Type of compliance to check"),
    current_user: Any = Depends(get_current_user)
):
    """
    Check data compliance with specified regulations.
    
    Performs comprehensive compliance checks for GDPR, HIPAA, CCPA, and SOX.
    """
    try:
        logger.info(f"Compliance check request for type: {compliance_type}")
        
        compliance_results = data_vendor_api_expansion.check_compliance(
            data=data,
            compliance_type=compliance_type
        )
        
        response = {
            "compliance_results": compliance_results,
            "compliance_type": compliance_type.value,
            "metadata": {
                "checked_at": datetime.now().isoformat(),
                "data_fields_checked": list(data.keys()),
                "compliance_standards": {
                    "gdpr": "General Data Protection Regulation",
                    "hipaa": "Health Insurance Portability and Accountability Act",
                    "ccpa": "California Consumer Privacy Act",
                    "sox": "Sarbanes-Oxley Act"
                }
            }
        }
        
        logger.info(f"Compliance check completed for {compliance_type.value}")
        return response
        
    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check compliance: {str(e)}")


@router.get("/audit-log", response_model=Dict[str, Any])
async def get_audit_log(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    limit: int = Query(100, description="Maximum number of entries to return"),
    current_user: Any = Depends(get_current_user)
):
    """
    Get audit log entries with optional filtering.
    
    Returns comprehensive audit trail for compliance and security tracking.
    """
    try:
        logger.info(f"Audit log request with filters: event_type={event_type}, start_date={start_date}, end_date={end_date}")
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        audit_entries = data_vendor_api_expansion.get_audit_log(
            event_type=event_type,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        # Apply limit
        audit_entries = audit_entries[:limit]
        
        response = {
            "audit_entries": audit_entries,
            "summary": {
                "total_entries": len(audit_entries),
                "event_types": list(set(entry.get("event_type") for entry in audit_entries)),
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            "metadata": {
                "requested_at": datetime.now().isoformat(),
                "filters_applied": {
                    "event_type": event_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                }
            }
        }
        
        logger.info(f"Audit log retrieved successfully with {len(audit_entries)} entries")
        return response
        
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")


@router.post("/export-data", response_model=Dict[str, Any])
async def export_data(
    data: Dict[str, Any] = Body(..., description="Data to export"),
    export_format: str = Body("json", description="Export format (json, csv, xml, yaml)"),
    include_analytics: bool = Body(True, description="Include analytics in export"),
    mask_sensitive: bool = Body(True, description="Mask sensitive data in export"),
    current_user: Any = Depends(get_current_user)
):
    """
    Export data in various formats with optional analytics and masking.
    
    Supports multiple export formats with comprehensive data processing options.
    """
    try:
        logger.info(f"Data export request: format={export_format}, include_analytics={include_analytics}, mask_sensitive={mask_sensitive}")
        
        exported_data = data_vendor_api_expansion.export_data(
            data=data,
            export_format=export_format,
            include_analytics=include_analytics,
            mask_sensitive=mask_sensitive
        )
        
        response = {
            "exported_data": exported_data,
            "export_summary": {
                "format": export_format,
                "include_analytics": include_analytics,
                "mask_sensitive": mask_sensitive,
                "data_size_bytes": len(exported_data.encode('utf-8'))
            },
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "supported_formats": ["json", "csv", "xml", "yaml"]
            }
        }
        
        logger.info(f"Data export completed successfully in {export_format} format")
        return response
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.get("/performance-metrics", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: Any = Depends(get_current_user)
):
    """
    Get performance metrics for the Data Vendor API Expansion service.
    
    Returns comprehensive performance and operational metrics.
    """
    try:
        logger.info("Performance metrics request")
        
        metrics = data_vendor_api_expansion.get_performance_metrics()
        
        response = {
            "performance_metrics": metrics,
            "service_status": {
                "status": "operational",
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "capabilities": {
                "analytics": True,
                "data_masking": True,
                "encryption": True,
                "compliance_checking": True,
                "audit_logging": True,
                "data_export": True
            }
        }
        
        logger.info("Performance metrics retrieved successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint for the Data Vendor API Expansion service.
    
    Returns service health status and basic operational information.
    """
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Data Vendor API Expansion",
            "version": "1.0.0",
            "checks": {
                "encryption": data_vendor_api_expansion.encryption_key is not None,
                "masking_rules": len(data_vendor_api_expansion.masking_rules) > 0,
                "compliance_configs": len(data_vendor_api_expansion.compliance_configs) > 0,
                "audit_logging": True
            }
        }
        
        # Check if all critical components are available
        all_healthy = all(health_status["checks"].values())
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/supported-formats", response_model=Dict[str, Any])
async def get_supported_formats():
    """
    Get supported export formats and compliance types.
    
    Returns comprehensive list of supported formats and compliance standards.
    """
    try:
        response = {
            "export_formats": {
                "json": {
                    "description": "JavaScript Object Notation",
                    "content_type": "application/json",
                    "compression": False
                },
                "csv": {
                    "description": "Comma-Separated Values",
                    "content_type": "text/csv",
                    "compression": False
                },
                "xml": {
                    "description": "Extensible Markup Language",
                    "content_type": "application/xml",
                    "compression": False
                },
                "yaml": {
                    "description": "YAML Ain't Markup Language",
                    "content_type": "application/x-yaml",
                    "compression": False
                }
            },
            "compliance_types": {
                "gdpr": {
                    "name": "General Data Protection Regulation",
                    "description": "EU data protection regulation",
                    "enabled": True
                },
                "hipaa": {
                    "name": "Health Insurance Portability and Accountability Act",
                    "description": "US healthcare data protection",
                    "enabled": True
                },
                "ccpa": {
                    "name": "California Consumer Privacy Act",
                    "description": "California data privacy regulation",
                    "enabled": True
                },
                "sox": {
                    "name": "Sarbanes-Oxley Act",
                    "description": "US financial reporting regulation",
                    "enabled": True
                }
            },
            "masking_levels": {
                "none": "No masking applied",
                "partial": "Partial masking with pattern preservation",
                "full": "Complete masking with replacement characters",
                "custom": "Custom masking rules applied"
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting supported formats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported formats: {str(e)}") 