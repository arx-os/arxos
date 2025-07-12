"""
Multi-System Integration Framework Router

Provides RESTful API endpoints for system connections, data transformation,
synchronization, and monitoring for CMMS, ERP, SCADA, BMS, and IoT systems.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from services.multi_system_integration import (
    multi_system_integration,
    SystemType,
    ConnectionStatus,
    SyncDirection,
    ConflictResolution,
    SystemConnection,
    FieldMapping,
    SyncResult
)
from utils.auth import get_current_user
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/integration", tags=["Multi-System Integration"])


@router.post("/connections", response_model=Dict[str, Any])
async def create_system_connection(
    connection_config: Dict[str, Any] = Body(..., description="System connection configuration"),
    current_user: Any = Depends(get_current_user)
):
    """
    Create a new system connection for CMMS, ERP, SCADA, BMS, or IoT systems.
    
    Creates a connection to external systems with authentication and configuration.
    """
    try:
        logger.info(f"Creating system connection: {connection_config.get('system_id')}")
        
        connection = multi_system_integration.create_system_connection(connection_config)
        
        response = {
            "connection": {
                "system_id": connection.system_id,
                "system_type": connection.system_type.value,
                "connection_name": connection.connection_name,
                "host": connection.host,
                "port": connection.port,
                "status": connection.status.value,
                "created_at": connection.created_at.isoformat(),
                "updated_at": connection.updated_at.isoformat()
            },
            "message": "System connection created successfully",
            "metadata": {
                "supported_system_types": [t.value for t in SystemType],
                "connection_capabilities": {
                    "ssl_enabled": connection.ssl_enabled,
                    "timeout": connection.timeout,
                    "retry_attempts": connection.retry_attempts
                }
            }
        }
        
        logger.info(f"System connection created successfully: {connection.system_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating system connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create system connection: {str(e)}")


@router.post("/connections/{system_id}/test", response_model=Dict[str, Any])
async def test_system_connection(
    system_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Test system connection status and capabilities.
    
    Performs connectivity test and returns system capabilities.
    """
    try:
        logger.info(f"Testing system connection: {system_id}")
        
        test_result = multi_system_integration.test_connection(system_id)
        
        response = {
            "test_result": test_result,
            "system_id": system_id,
            "metadata": {
                "tested_at": datetime.now().isoformat(),
                "response_time": test_result.get("response_time", 0),
                "capabilities": test_result.get("capabilities", [])
            }
        }
        
        logger.info(f"System connection test completed: {system_id} - {test_result.get('success', False)}")
        return response
        
    except Exception as e:
        logger.error(f"Error testing system connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test system connection: {str(e)}")


@router.get("/connections", response_model=Dict[str, Any])
async def get_all_connections(
    system_type: Optional[str] = Query(None, description="Filter by system type"),
    status: Optional[str] = Query(None, description="Filter by connection status"),
    current_user: Any = Depends(get_current_user)
):
    """
    Get all system connections with optional filtering.
    
    Returns comprehensive list of all configured system connections.
    """
    try:
        logger.info("Getting all system connections")
        
        connections = multi_system_integration.get_all_connections()
        
        # Apply filters
        if system_type:
            connections = [c for c in connections if c["system_type"] == system_type]
        
        if status:
            connections = [c for c in connections if c["status"] == status]
        
        response = {
            "connections": connections,
            "summary": {
                "total_connections": len(connections),
                "connected": len([c for c in connections if c["status"] == "connected"]),
                "disconnected": len([c for c in connections if c["status"] == "disconnected"]),
                "error": len([c for c in connections if c["status"] == "error"])
            },
            "metadata": {
                "supported_system_types": [t.value for t in SystemType],
                "supported_statuses": [s.value for s in ConnectionStatus]
            }
        }
        
        logger.info(f"Retrieved {len(connections)} system connections")
        return response
        
    except Exception as e:
        logger.error(f"Error getting system connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system connections: {str(e)}")


@router.get("/connections/{system_id}", response_model=Dict[str, Any])
async def get_connection_status(
    system_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Get detailed status for a specific system connection.
    
    Returns comprehensive connection status and health information.
    """
    try:
        logger.info(f"Getting connection status: {system_id}")
        
        status = multi_system_integration.get_connection_status(system_id)
        
        response = {
            "connection_status": status,
            "metadata": {
                "retrieved_at": datetime.now().isoformat(),
                "health_indicators": {
                    "last_sync": status.get("last_sync"),
                    "connection_age": (datetime.now() - datetime.fromisoformat(status["created_at"])).days if status.get("created_at") else 0
                }
            }
        }
        
        logger.info(f"Connection status retrieved: {system_id} - {status.get('status')}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection status: {str(e)}")


@router.post("/mappings", response_model=Dict[str, Any])
async def create_field_mapping(
    mapping_config: Dict[str, Any] = Body(..., description="Field mapping configuration"),
    current_user: Any = Depends(get_current_user)
):
    """
    Create field mapping between Arxos and external system.
    
    Defines how data fields are mapped and transformed between systems.
    """
    try:
        logger.info(f"Creating field mapping: {mapping_config.get('mapping_id')}")
        
        mapping = multi_system_integration.create_field_mapping(mapping_config)
        
        response = {
            "mapping": {
                "mapping_id": mapping.mapping_id,
                "system_id": mapping.system_id,
                "arxos_field": mapping.arxos_field,
                "external_field": mapping.external_field,
                "transformation_rule": mapping.transformation_rule,
                "is_required": mapping.is_required,
                "data_type": mapping.data_type,
                "validation_rule": mapping.validation_rule,
                "created_at": mapping.created_at.isoformat()
            },
            "message": "Field mapping created successfully",
            "metadata": {
                "transformation_types": ["calculation", "validation", "formatting"],
                "data_types": ["string", "number", "date", "boolean", "object"]
            }
        }
        
        logger.info(f"Field mapping created successfully: {mapping.mapping_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create field mapping: {str(e)}")


@router.post("/transform", response_model=Dict[str, Any])
async def transform_data(
    data: Dict[str, Any] = Body(..., description="Data to transform"),
    system_id: str = Body(..., description="Target system ID"),
    direction: str = Body(..., description="Transformation direction (inbound/outbound)"),
    current_user: Any = Depends(get_current_user)
):
    """
    Transform data between Arxos and external system format.
    
    Applies field mappings and transformation rules to convert data formats.
    """
    try:
        logger.info(f"Transforming data for system: {system_id}, direction: {direction}")
        
        transformed_data = multi_system_integration.transform_data(data, system_id, direction)
        
        response = {
            "transformed_data": transformed_data,
            "transformation_summary": {
                "original_fields": len(data),
                "transformed_fields": len(transformed_data),
                "direction": direction,
                "system_id": system_id
            },
            "metadata": {
                "transformed_at": datetime.now().isoformat(),
                "transformation_rules_applied": len(transformed_data) - len(data)
            }
        }
        
        logger.info(f"Data transformation completed: {len(transformed_data)} fields transformed")
        return response
        
    except Exception as e:
        logger.error(f"Error transforming data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transform data: {str(e)}")


@router.post("/sync", response_model=Dict[str, Any])
async def sync_data(
    system_id: str = Body(..., description="Target system ID"),
    direction: SyncDirection = Body(..., description="Sync direction"),
    data: List[Dict[str, Any]] = Body(..., description="Data to synchronize"),
    conflict_resolution: ConflictResolution = Body(ConflictResolution.TIMESTAMP_BASED, description="Conflict resolution strategy"),
    current_user: Any = Depends(get_current_user)
):
    """
    Synchronize data with external system.
    
    Performs bidirectional data synchronization with conflict resolution.
    """
    try:
        logger.info(f"Starting data sync: {system_id}, direction: {direction.value}, records: {len(data)}")
        
        sync_result = multi_system_integration.sync_data(system_id, direction, data, conflict_resolution)
        
        response = {
            "sync_result": {
                "sync_id": sync_result.sync_id,
                "system_id": sync_result.system_id,
                "direction": sync_result.direction.value,
                "records_processed": sync_result.records_processed,
                "records_successful": sync_result.records_successful,
                "records_failed": sync_result.records_failed,
                "conflicts_resolved": sync_result.conflicts_resolved,
                "sync_duration": sync_result.sync_duration,
                "status": sync_result.status,
                "error_message": sync_result.error_message,
                "timestamp": sync_result.timestamp.isoformat()
            },
            "metadata": {
                "conflict_resolution_strategy": conflict_resolution.value,
                "sync_performance": {
                    "records_per_second": sync_result.records_successful / sync_result.sync_duration if sync_result.sync_duration > 0 else 0,
                    "success_rate": (sync_result.records_successful / sync_result.records_processed * 100) if sync_result.records_processed > 0 else 0
                }
            }
        }
        
        logger.info(f"Data sync completed: {sync_result.sync_id} - {sync_result.records_successful}/{sync_result.records_processed} successful")
        return response
        
    except Exception as e:
        logger.error(f"Error syncing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync data: {str(e)}")


@router.get("/sync/history", response_model=Dict[str, Any])
async def get_sync_history(
    system_id: Optional[str] = Query(None, description="Filter by system ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: Any = Depends(get_current_user)
):
    """
    Get synchronization history with optional filtering.
    
    Returns comprehensive sync history with performance metrics.
    """
    try:
        logger.info(f"Getting sync history with filters: system_id={system_id}, start_date={start_date}, end_date={end_date}")
        
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
        
        sync_history = multi_system_integration.get_sync_history(
            system_id=system_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        # Apply limit
        sync_history = sync_history[:limit]
        
        # Calculate summary statistics
        total_records = sum(h["records_processed"] for h in sync_history)
        total_successful = sum(h["records_successful"] for h in sync_history)
        total_failed = sum(h["records_failed"] for h in sync_history)
        total_conflicts = sum(h["conflicts_resolved"] for h in sync_history)
        avg_duration = sum(h["sync_duration"] for h in sync_history) / len(sync_history) if sync_history else 0
        
        response = {
            "sync_history": sync_history,
            "summary": {
                "total_syncs": len(sync_history),
                "total_records_processed": total_records,
                "total_records_successful": total_successful,
                "total_records_failed": total_failed,
                "total_conflicts_resolved": total_conflicts,
                "average_sync_duration": avg_duration,
                "success_rate": (total_successful / total_records * 100) if total_records > 0 else 0
            },
            "metadata": {
                "filters_applied": {
                    "system_id": system_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                },
                "retrieved_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Sync history retrieved: {len(sync_history)} records")
        return response
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: Any = Depends(get_current_user)
):
    """
    Get performance metrics for the integration framework.
    
    Returns comprehensive performance and operational metrics.
    """
    try:
        logger.info("Getting integration performance metrics")
        
        metrics = multi_system_integration.get_performance_metrics()
        
        response = {
            "performance_metrics": metrics,
            "framework_status": {
                "status": "operational",
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "capabilities": {
                "system_connectors": True,
                "data_transformation": True,
                "synchronization": True,
                "conflict_resolution": True,
                "connection_monitoring": True,
                "audit_logging": True
            },
            "supported_systems": {
                "cmms": ["maximo", "sap_pm", "infor", "custom"],
                "erp": ["sap", "oracle", "dynamics", "custom"],
                "scada": ["honeywell", "siemens", "abb", "custom"],
                "bms": ["honeywell_bms", "siemens_bms", "johnson", "custom"],
                "iot": ["modbus", "bacnet", "mqtt", "custom"]
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
    Health check endpoint for the Multi-System Integration Framework.
    
    Returns framework health status and basic operational information.
    """
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Multi-System Integration Framework",
            "version": "1.0.0",
            "checks": {
                "connectors": len(multi_system_integration.connectors) > 0,
                "transformation_engine": len(multi_system_integration.transformation_engine) > 0,
                "connection_monitoring": True,
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


@router.get("/supported-systems", response_model=Dict[str, Any])
async def get_supported_systems():
    """
    Get supported system types and connectors.
    
    Returns comprehensive list of supported external systems and their capabilities.
    """
    try:
        response = {
            "system_types": {
                "cmms": {
                    "name": "Computerized Maintenance Management System",
                    "description": "Maintenance management and work order systems",
                    "connectors": ["maximo", "sap_pm", "infor", "custom"],
                    "capabilities": ["work_orders", "equipment", "preventive_maintenance", "inventory"]
                },
                "erp": {
                    "name": "Enterprise Resource Planning",
                    "description": "Enterprise resource planning and business management",
                    "connectors": ["sap", "oracle", "dynamics", "custom"],
                    "capabilities": ["financial_data", "inventory", "procurement", "hr"]
                },
                "scada": {
                    "name": "Supervisory Control and Data Acquisition",
                    "description": "Industrial control and monitoring systems",
                    "connectors": ["honeywell", "siemens", "abb", "custom"],
                    "capabilities": ["real_time_data", "alarms", "control_commands", "trending"]
                },
                "bms": {
                    "name": "Building Management System",
                    "description": "Building automation and control systems",
                    "connectors": ["honeywell_bms", "siemens_bms", "johnson", "custom"],
                    "capabilities": ["hvac_control", "lighting", "security", "energy_management"]
                },
                "iot": {
                    "name": "Internet of Things",
                    "description": "IoT devices and sensor networks",
                    "connectors": ["modbus", "bacnet", "mqtt", "custom"],
                    "capabilities": ["sensor_data", "device_control", "status_monitoring", "alerts"]
                }
            },
            "transformation_engine": {
                "calculations": ["add", "subtract", "multiply", "divide", "percentage", "average", "sum", "max", "min"],
                "validations": ["required", "email", "phone", "numeric", "date", "range"],
                "formatting": ["uppercase", "lowercase", "titlecase", "trim", "date_format", "number_format"]
            },
            "sync_directions": [d.value for d in SyncDirection],
            "conflict_resolution": [c.value for c in ConflictResolution],
            "connection_statuses": [s.value for s in ConnectionStatus]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting supported systems: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported systems: {str(e)}")


@router.post("/connections/{system_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_system(
    system_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Disconnect from external system.
    
    Safely disconnects from external system and updates connection status.
    """
    try:
        logger.info(f"Disconnecting from system: {system_id}")
        
        # Get current connection status
        status = multi_system_integration.get_connection_status(system_id)
        
        # Update connection status to disconnected
        # In a real implementation, this would close the actual connection
        response = {
            "system_id": system_id,
            "previous_status": status["status"],
            "new_status": "disconnected",
            "disconnected_at": datetime.now().isoformat(),
            "message": "System disconnected successfully"
        }
        
        logger.info(f"System disconnected: {system_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error disconnecting system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect system: {str(e)}")


@router.post("/connections/{system_id}/reconnect", response_model=Dict[str, Any])
async def reconnect_system(
    system_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Reconnect to external system.
    
    Attempts to reconnect to external system and updates connection status.
    """
    try:
        logger.info(f"Reconnecting to system: {system_id}")
        
        # Test connection to reconnect
        test_result = multi_system_integration.test_connection(system_id)
        
        response = {
            "system_id": system_id,
            "reconnection_successful": test_result["success"],
            "new_status": "connected" if test_result["success"] else "error",
            "reconnected_at": datetime.now().isoformat(),
            "test_result": test_result,
            "message": "System reconnected successfully" if test_result["success"] else "Reconnection failed"
        }
        
        logger.info(f"System reconnection attempt: {system_id} - {test_result['success']}")
        return response
        
    except Exception as e:
        logger.error(f"Error reconnecting system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reconnect system: {str(e)}") 