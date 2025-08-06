"""
CAD Integration Module for MCP Validation

This module provides non-intrusive integration with CAD applications:
- Real-time validation feedback
- Object highlighting without blocking user actions
- CAD-friendly data formats
- WebSocket support for live updates
"""

import json
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from validate.rule_engine import MCPRuleEngine
from models.mcp_models import BuildingModel, BuildingObject


logger = logging.getLogger(__name__)


@dataclass
class CADHighlight:
    """Represents a highlight for CAD display"""

    object_id: str
    highlight_type: str  # 'error', 'warning', 'info', 'success'
    color: str  # Hex color code
    message: str
    code_reference: str
    category: str
    suggestions: List[str]
    timestamp: datetime


class CADIntegration:
    """
    CAD integration for non-intrusive building validation

    Features:
    - Real-time validation feedback
    - Non-blocking highlights
    - CAD-friendly data formats
    - WebSocket support for live updates
    """

    def __init__(self, engine: MCPRuleEngine = None):
        self.engine = engine or MCPRuleEngine()
        self.highlights = {}  # object_id -> CADHighlight
        self.callbacks = {}  # event_type -> callback functions
        self.validation_thread = None
        self.is_running = False

        # CAD-specific settings
        self.highlight_colors = {
            "error": "#FF0000",  # Red
            "warning": "#FFA500",  # Orange
            "info": "#0000FF",  # Blue
            "success": "#00FF00",  # Green
        }

        # Performance settings
        self.validation_delay = 0.5  # seconds between validations
        self.batch_size = 10  # objects per validation batch

    def start_realtime_validation(
        self, building_model: BuildingModel, mcp_files: List[str] = None
    ):
        """Start real-time validation in background thread"""
        if self.is_running:
            logger.warning("Real-time validation already running")
            return

        self.is_running = True
        self.validation_thread = threading.Thread(
            target=self._validation_worker,
            args=(building_model, mcp_files),
            daemon=True,
        )
        self.validation_thread.start()
        logger.info("Real-time validation started")

    def stop_realtime_validation(self):
        """Stop real-time validation"""
        self.is_running = False
        if self.validation_thread:
            self.validation_thread.join(timeout=1.0)
        logger.info("Real-time validation stopped")

    def _validation_worker(self, building_model: BuildingModel, mcp_files: List[str]):
        """Background worker for real-time validation"""
        while self.is_running:
            try:
                # Run validation
                compliance_report = self.engine.validate_building_model(
                    building_model, mcp_files or []
                )

                # Process results into highlights
                new_highlights = self._process_validation_results(compliance_report)

                # Update highlights
                self._update_highlights(new_highlights)

                # Notify CAD application
                self._notify_cad_update(new_highlights)

                # Wait before next validation
                time.sleep(self.validation_delay)

            except Exception as e:
                logger.error(f"Validation worker error: {e}")
                time.sleep(self.validation_delay)

    def _process_validation_results(self, compliance_report) -> Dict[str, CADHighlight]:
        """Process validation results into CAD highlights"""
        highlights = {}

        for report in compliance_report.validation_reports:
            for result in report.results:
                for violation in result.violations:
                    # Create CAD highlight
                    highlight = CADHighlight(
                        object_id=violation.object_id,
                        highlight_type=self._get_highlight_type(
                            violation.severity.value
                        ),
                        color=self.highlight_colors.get(
                            violation.severity.value, "#000000"
                        ),
                        message=violation.message,
                        code_reference=violation.code_reference,
                        category=result.rule_category.value,
                        suggestions=self._get_suggestions(violation),
                        timestamp=datetime.now(),
                    )

                    highlights[violation.object_id] = highlight

        return highlights

    def _get_highlight_type(self, severity: str) -> str:
        """Convert severity to highlight type"""
        severity_map = {
            "error": "error",
            "warning": "warning",
            "info": "info",
            "success": "success",
        }
        return severity_map.get(severity, "info")

    def _get_suggestions(self, violation) -> List[str]:
        """Get suggestions for fixing violations"""
        # This would be based on the violation type and code reference
        suggestions = []

        if "NEC 210.8" in violation.code_reference:
            suggestions.append("Add GFCI protection to outlet")
            suggestions.append("Verify outlet is in wet location")

        elif "IBC 1003" in violation.code_reference:
            suggestions.append("Verify means of egress requirements")
            suggestions.append("Check exit path accessibility")

        elif "IPC" in violation.code_reference:
            suggestions.append("Verify plumbing fixture requirements")
            suggestions.append("Check water supply and drainage")

        elif "IMC" in violation.code_reference:
            suggestions.append("Verify HVAC system requirements")
            suggestions.append("Check ventilation requirements")

        if not suggestions:
            suggestions.append("Review applicable building code requirements")

        return suggestions

    def _update_highlights(self, new_highlights: Dict[str, CADHighlight]):
        """Update highlights and detect changes"""
        changed_highlights = {}

        for obj_id, highlight in new_highlights.items():
            old_highlight = self.highlights.get(obj_id)

            # Check if highlight changed
            if not old_highlight or self._highlight_changed(old_highlight, highlight):
                changed_highlights[obj_id] = highlight
                self.highlights[obj_id] = highlight

        # Remove highlights for objects no longer in new_highlights
        removed_objects = []
        for obj_id in list(self.highlights.keys()):
            if obj_id not in new_highlights:
                removed_objects.append(obj_id)
                del self.highlights[obj_id]

        # Notify about changes
        if changed_highlights or removed_objects:
            self._notify_highlight_changes(changed_highlights, removed_objects)

    def _highlight_changed(self, old: CADHighlight, new: CADHighlight) -> bool:
        """Check if highlight has changed"""
        return (
            old.highlight_type != new.highlight_type
            or old.message != new.message
            or old.color != new.color
        )

    def _notify_cad_update(self, highlights: Dict[str, CADHighlight]):
        """Notify CAD application of validation updates"""
        if "validation_update" in self.callbacks:
            try:
                self.callbacks["validation_update"](highlights)
            except Exception as e:
                logger.error(f"CAD update callback error: {e}")

    def _notify_highlight_changes(
        self, changed_highlights: Dict[str, CADHighlight], removed_objects: List[str]
    ):
        """Notify CAD application of highlight changes"""
        if "highlight_changes" in self.callbacks:
            try:
                self.callbacks["highlight_changes"](changed_highlights, removed_objects)
            except Exception as e:
                logger.error(f"Highlight changes callback error: {e}")

    def validate_object_realtime(
        self, obj: BuildingObject, building_model: BuildingModel
    ) -> List[CADHighlight]:
        """Validate a single object in real-time"""
        highlights = []

        # Quick validation rules for common issues
        if obj.object_type == "electrical_outlet":
            if obj.properties.get("location") in ["bathroom", "kitchen"]:
                if not obj.properties.get("gfci_protected", False):
                    highlight = CADHighlight(
                        object_id=obj.object_id,
                        highlight_type="error",
                        color=self.highlight_colors["error"],
                        message="GFCI protection required for wet locations",
                        code_reference="NEC 210.8(A)",
                        category="electrical_safety",
                        suggestions=["Add GFCI protection to outlet"],
                        timestamp=datetime.now(),
                    )
                    highlights.append(highlight)

        elif obj.object_type == "room":
            area = obj.properties.get("area", 0)
            if area > 100:  # Large room
                highlight = CADHighlight(
                    object_id=obj.object_id,
                    highlight_type="info",
                    color=self.highlight_colors["info"],
                    message="Large room - consider egress requirements",
                    code_reference="IBC 1003.1",
                    category="fire_safety_egress",
                    suggestions=["Verify egress path requirements"],
                    timestamp=datetime.now(),
                )
                highlights.append(highlight)

        elif obj.object_type == "hvac_unit":
            capacity = obj.properties.get("capacity", 0)
            if capacity > 0:
                efficiency = obj.properties.get("efficiency_rating", 0)
                if efficiency < 80:
                    highlight = CADHighlight(
                        object_id=obj.object_id,
                        highlight_type="warning",
                        color=self.highlight_colors["warning"],
                        message="Low efficiency HVAC unit",
                        code_reference="IMC 901.1",
                        category="energy_efficiency",
                        suggestions=["Consider higher efficiency unit"],
                        timestamp=datetime.now(),
                    )
                    highlights.append(highlight)

        return highlights

    def get_highlights_for_object(self, object_id: str) -> Optional[CADHighlight]:
        """Get highlight for specific object"""
        return self.highlights.get(object_id)

    def get_all_highlights(self) -> Dict[str, CADHighlight]:
        """Get all current highlights"""
        return self.highlights.copy()

    def clear_highlights(self, object_ids: List[str] = None):
        """Clear highlights for specific objects or all objects"""
        if object_ids:
            for obj_id in object_ids:
                if obj_id in self.highlights:
                    del self.highlights[obj_id]
        else:
            self.highlights.clear()

    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for CAD events"""
        self.callbacks[event_type] = callback
        logger.info(f"Registered callback for event: {event_type}")

    def unregister_callback(self, event_type: str):
        """Unregister callback"""
        if event_type in self.callbacks:
            del self.callbacks[event_type]
            logger.info(f"Unregistered callback for event: {event_type}")

    def export_highlights_for_cad(self) -> Dict[str, Any]:
        """Export highlights in CAD-friendly format"""
        cad_highlights = {
            "type": "cad_highlights",
            "timestamp": datetime.now().isoformat(),
            "highlights": {},
        }

        for obj_id, highlight in self.highlights.items():
            cad_highlights["highlights"][obj_id] = {
                "type": highlight.highlight_type,
                "color": highlight.color,
                "message": highlight.message,
                "code_reference": highlight.code_reference,
                "category": highlight.category,
                "suggestions": highlight.suggestions,
                "timestamp": highlight.timestamp.isoformat(),
            }

        return cad_highlights

    def import_building_model_from_cad(self, cad_data: Dict[str, Any]) -> BuildingModel:
        """Import building model from CAD application"""
        try:
            # Handle different CAD data formats
            if "objects" in cad_data:
                objects_data = cad_data["objects"]
            elif "building_objects" in cad_data:
                objects_data = cad_data["building_objects"]
            else:
                raise ValueError("No building objects found in CAD data")

            # Create building model
            building_model = BuildingModel(
                building_id=cad_data.get("building_id", "cad_import"),
                building_name=cad_data.get("building_name", "CAD Import"),
                objects=[],
            )

            # Parse objects
            for obj_data in objects_data:
                obj = BuildingObject(
                    object_id=obj_data["id"],
                    object_type=obj_data["type"],
                    properties=obj_data.get("properties", {}),
                    location=obj_data.get("location", {}),
                    connections=obj_data.get("connections", []),
                )
                building_model.objects.append(obj)

            return building_model

        except Exception as e:
            logger.error(f"Failed to import building model from CAD: {e}")
            raise


class CADWebSocket:
    """WebSocket support for real-time CAD updates"""

    def __init__(self, cad_integration: CADIntegration):
        self.cad_integration = cad_integration
        self.connected_clients = []

        # Register callbacks
        self.cad_integration.register_callback(
            "validation_update", self._broadcast_update
        )
        self.cad_integration.register_callback(
            "highlight_changes", self._broadcast_changes
        )

    def _broadcast_update(self, highlights: Dict[str, CADHighlight]):
        """Broadcast validation update to connected clients"""
        message = {
            "type": "validation_update",
            "timestamp": datetime.now().isoformat(),
            "highlights": self.cad_integration.export_highlights_for_cad(),
        }

        # Broadcast to all connected clients
        for client in self.connected_clients:
            try:
                client.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                self.connected_clients.remove(client)

    def _broadcast_changes(
        self, changed_highlights: Dict[str, CADHighlight], removed_objects: List[str]
    ):
        """Broadcast highlight changes to connected clients"""
        message = {
            "type": "highlight_changes",
            "timestamp": datetime.now().isoformat(),
            "changed_highlights": {
                obj_id: {
                    "type": highlight.highlight_type,
                    "color": highlight.color,
                    "message": highlight.message,
                    "code_reference": highlight.code_reference,
                    "category": highlight.category,
                    "suggestions": highlight.suggestions,
                }
                for obj_id, highlight in changed_highlights.items()
            },
            "removed_objects": removed_objects,
        }

        # Broadcast to all connected clients
        for client in self.connected_clients:
            try:
                client.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send changes to client: {e}")
                self.connected_clients.remove(client)

    def add_client(self, client):
        """Add connected client"""
        self.connected_clients.append(client)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")

    def remove_client(self, client):
        """Remove disconnected client"""
        if client in self.connected_clients:
            self.connected_clients.remove(client)
            logger.info(
                f"Client disconnected. Total clients: {len(self.connected_clients)}"
            )


# Example CAD integration usage
def example_cad_integration():
    """Example of how to use CAD integration"""

    # Create CAD integration
    cad_integration = CADIntegration()

    # Register callbacks for CAD application
    def on_validation_update(highlights):
        print(f"Validation update: {len(highlights)} highlights")
        # Send highlights to CAD application

    def on_highlight_changes(changed, removed):
        print(f"Highlight changes: {len(changed)} changed, {len(removed)} removed")
        # Update CAD display

    cad_integration.register_callback("validation_update", on_validation_update)
    cad_integration.register_callback("highlight_changes", on_highlight_changes)

    # Start real-time validation
    # cad_integration.start_realtime_validation(building_model)

    # Export highlights for CAD
    highlights = cad_integration.export_highlights_for_cad()
    print(json.dumps(highlights, indent=2))


if __name__ == "__main__":
    example_cad_integration()
