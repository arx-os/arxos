"""
REST API for MCP Validation System

This module provides REST API endpoints for building validation that can be integrated
with CAD applications without hindering user actions. The API focuses on:
- Non-intrusive validation (highlighting only)
- Real-time validation feedback
- CAD-friendly response formats
- WebSocket support for live updates
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from validate.rule_engine import MCPRuleEngine
from models.mcp_models import BuildingModel, BuildingObject, ComplianceReport

logger = logging.getLogger(__name__)


class BuildingValidationRequest(BaseModel):
    """Request model for building validation"""
    building_id: str
    building_name: str
    objects: List[Dict[str, Any]]
    mcp_files: Optional[List[str]] = []


class RealtimeValidationRequest(BaseModel):
    """Request model for real-time validation"""
    building_id: str
    building_name: str
    objects: List[Dict[str, Any]]
    changed_objects: Optional[List[str]] = []


class HighlightRequest(BaseModel):
    """Request model for object highlights"""
    object_ids: List[str]


class MCPValidationAPI:
    """
    REST API for MCP validation system using FastAPI
    
    Provides endpoints for:
    - Building model validation
    - Real-time validation feedback
    - CAD integration support
    - Non-intrusive highlighting
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.app = FastAPI(
            title="MCP Validation API",
            description="REST API for building code validation with CAD integration",
            version="1.0.0"
        )
        self.host = host
        self.port = port
        self.engine = MCPRuleEngine()
        
        # Enable CORS for CAD integration
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
        # Validation cache for performance
        self.validation_cache = {}
        
    def _register_routes(self):
        """Register API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        
        @self.app.post("/api/v1/validate")
        async def validate_building(request: BuildingValidationRequest):
            """Validate building model (non-intrusive)"""
            try:
                # Parse building model
                building_model = self._parse_building_model(request.dict())
                
                # Run validation
                compliance_report = self.engine.validate_building_model(
                    building_model, request.mcp_files
                )
                
                # Return CAD-friendly response (highlights only)
                return self._format_cad_response(compliance_report)
                
            except Exception as e:
                logger.error(f"Validation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/validate/realtime")
        async def validate_realtime(request: RealtimeValidationRequest):
            """Real-time validation for live CAD updates"""
            try:
                # Parse building model
                building_model = self._parse_building_model(request.dict())
                
                # Run incremental validation
                validation_result = self._validate_incremental(
                    building_model, request.changed_objects
                )
                
                # Return real-time highlights
                return {
                    "type": "realtime_validation",
                    "timestamp": datetime.now().isoformat(),
                    "highlights": validation_result['highlights'],
                    "warnings": validation_result['warnings'],
                    "errors": validation_result['errors']
                }
                
            except Exception as e:
                logger.error(f"Real-time validation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/highlights")
        async def get_highlights(request: HighlightRequest):
            """Get validation highlights for specific objects"""
            try:
                # Get highlights for specific objects
                highlights = self._get_object_highlights(request.object_ids)
                
                return {
                    "highlights": highlights,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Highlights error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/mcp/codes")
        async def get_available_codes():
            """Get available building codes"""
            try:
                codes = self._get_available_codes()
                return {
                    "codes": codes,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Codes error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/mcp/jurisdictions")
        async def get_jurisdictions():
            """Get available jurisdictions"""
            try:
                jurisdictions = self._get_available_jurisdictions()
                return {
                    "jurisdictions": jurisdictions,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Jurisdictions error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/performance")
        async def get_performance():
            """Get performance metrics"""
            try:
                metrics = self.engine.get_performance_metrics()
                return {
                    "metrics": metrics,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Performance error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _parse_building_model(self, data: Dict[str, Any]) -> BuildingModel:
        """Parse building model from request data"""
        try:
            # Handle different input formats
            if 'building_model' in data:
                building_data = data['building_model']
            else:
                building_data = data
            
            # Create building model
            building_model = BuildingModel(
                building_id=building_data.get('building_id', 'unknown'),
                building_name=building_data.get('building_name', 'Unknown Building'),
                objects=[]
            )
            
            # Parse objects
            objects_data = building_data.get('objects', [])
            for obj_data in objects_data:
                obj = BuildingObject(
                    object_id=obj_data['object_id'],
                    object_type=obj_data['object_type'],
                    properties=obj_data.get('properties', {}),
                    location=obj_data.get('location', {}),
                    connections=obj_data.get('connections', [])
                )
                building_model.objects.append(obj)
            
            return building_model
            
        except Exception as e:
            raise ValueError(f"Invalid building model format: {e}")
    
    def _format_cad_response(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Format response for CAD integration (non-intrusive highlights)"""
        highlights = []
        warnings = []
        errors = []
        
        # Process validation results
        for report in compliance_report.validation_reports:
            for result in report.results:
                for violation in result.violations:
                    # Create CAD-friendly highlight
                    highlight = {
                        "object_id": violation.object_id,
                        "type": "violation",
                        "severity": violation.severity.value,
                        "message": violation.message,
                        "code_reference": violation.code_reference,
                        "category": result.rule_category.value,
                        "suggestions": self._get_suggestions(violation)
                    }
                    
                    if violation.severity.value == "error":
                        errors.append(highlight)
                    elif violation.severity.value == "warning":
                        warnings.append(highlight)
                    else:
                        highlights.append(highlight)
        
        return {
            "type": "validation_result",
            "timestamp": datetime.now().isoformat(),
            "building_id": compliance_report.building_id,
            "overall_compliance": compliance_report.overall_compliance_score,
            "highlights": highlights,
            "warnings": warnings,
            "errors": errors,
            "recommendations": compliance_report.recommendations,
            "summary": {
                "total_violations": compliance_report.total_violations,
                "critical_violations": compliance_report.critical_violations,
                "warnings": len(warnings),
                "highlights": len(highlights)
            }
        }
    
    def _validate_incremental(self, building_model: BuildingModel, 
                             changed_objects: List[str]) -> Dict[str, Any]:
        """Validate only changed objects for real-time feedback"""
        highlights = []
        warnings = []
        errors = []
        
        # Get objects that changed
        changed_objs = [obj for obj in building_model.objects 
                       if obj.object_id in changed_objects]
        
        # Run validation on changed objects only
        for obj in changed_objs:
            # Quick validation for common issues
            obj_highlights = self._validate_single_object(obj, building_model)
            
            for highlight in obj_highlights:
                if highlight['severity'] == 'error':
                    errors.append(highlight)
                elif highlight['severity'] == 'warning':
                    warnings.append(highlight)
                else:
                    highlights.append(highlight)
        
        return {
            "highlights": highlights,
            "warnings": warnings,
            "errors": errors
        }
    
    def _validate_single_object(self, obj: BuildingObject, 
                               building_model: BuildingModel) -> List[Dict[str, Any]]:
        """Validate a single object for real-time feedback"""
        highlights = []
        
        # Quick validation rules
        if obj.object_type == "electrical_outlet":
            if obj.properties.get('location') in ['bathroom', 'kitchen']:
                if not obj.properties.get('gfci_protected', False):
                    highlights.append({
                        "object_id": obj.object_id,
                        "type": "violation",
                        "severity": "error",
                        "message": "GFCI protection required for wet locations",
                        "code_reference": "NEC 210.8(A)",
                        "category": "electrical_safety",
                        "suggestions": ["Add GFCI protection to outlet"]
                    })
        
        elif obj.object_type == "room":
            area = obj.properties.get('area', 0)
            if area > 100:  # Large room
                highlights.append({
                    "object_id": obj.object_id,
                    "type": "highlight",
                    "severity": "info",
                    "message": "Large room - consider egress requirements",
                    "code_reference": "IBC 1003.1",
                    "category": "fire_safety_egress",
                    "suggestions": ["Verify egress path requirements"]
                })
        
        return highlights
    
    def _get_object_highlights(self, object_ids: List[str]) -> List[Dict[str, Any]]:
        """Get highlights for specific objects"""
        highlights = []
        
        # This would typically query the validation cache
        # For now, return empty list
        return highlights
    
    def _get_available_codes(self) -> List[Dict[str, Any]]:
        """Get available building codes"""
        return [
            {
                "code": "NEC-2023",
                "name": "National Electrical Code 2023",
                "jurisdiction": "US",
                "categories": ["electrical_safety", "electrical_design"],
                "rules_count": 12
            },
            {
                "code": "IBC-2024",
                "name": "International Building Code 2024",
                "jurisdiction": "US",
                "categories": ["structural", "fire_safety_egress"],
                "rules_count": 15
            },
            {
                "code": "IPC-2024",
                "name": "International Plumbing Code 2024",
                "jurisdiction": "US",
                "categories": ["plumbing_water_supply", "plumbing_drainage"],
                "rules_count": 13
            },
            {
                "code": "IMC-2024",
                "name": "International Mechanical Code 2024",
                "jurisdiction": "US",
                "categories": ["mechanical_hvac", "mechanical_ventilation"],
                "rules_count": 16
            }
        ]
    
    def _get_available_jurisdictions(self) -> List[Dict[str, Any]]:
        """Get available jurisdictions"""
        return [
            {
                "country": "US",
                "state": None,
                "city": None,
                "name": "United States (Base)",
                "codes": ["NEC-2023", "IBC-2024", "IPC-2024", "IMC-2024"]
            },
            {
                "country": "US",
                "state": "CA",
                "city": None,
                "name": "California",
                "codes": ["NEC-2023-CA", "IBC-2024", "IPC-2024", "IMC-2024"]
            }
        ]
    
    def _get_suggestions(self, violation) -> List[str]:
        """Get suggestions for fixing violations"""
        # This would be based on the violation type
        return ["Review applicable building code requirements"]
    
    def run(self, debug: bool = False):
        """Run the API server"""
        import uvicorn
        logger.info(f"Starting MCP Validation API on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info" if not debug else "debug")


# WebSocket support for real-time updates
class MCPWebSocket:
    """WebSocket support for real-time validation updates"""
    
    def __init__(self, api: MCPValidationAPI):
        self.api = api
        # WebSocket implementation would go here
        # For now, this is a placeholder for future development
    
    def broadcast_validation_update(self, building_id: str, highlights: List[Dict]):
        """Broadcast validation updates to connected clients"""
        # WebSocket broadcast implementation
        pass


if __name__ == "__main__":
    # Run the API server
    api = MCPValidationAPI()
    api.run(debug=True) 