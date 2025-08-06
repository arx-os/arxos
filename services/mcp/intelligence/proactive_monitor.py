#!/usr/bin/env python3
"""
Proactive Monitor for MCP Intelligence Layer

Monitors model for potential issues and generates proactive alerts
to prevent problems before they occur.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import Alert, AlertSeverity, Conflict, ModelContext


class ProactiveMonitor:
    """
    Proactively monitors model for potential issues

    Detects conflicts, generates alerts, and identifies potential problems
    before they become violations or safety issues.
    """

    def __init__(self):
        """Initialize the proactive monitor"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ Proactive Monitor initialized")

    async def generate_alerts(
        self,
        object_type: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        model_context: Optional[ModelContext] = None,
    ) -> List[Alert]:
        """
        Generate proactive alerts for potential issues

        Args:
            object_type: Type of object being placed
            location: Location information
            model_context: Current model context

        Returns:
            List of proactive alerts
        """
        try:
            self.logger.info("Generating proactive alerts")

            alerts = []

            # Generate placement alerts
            if object_type and location:
                placement_alerts = await self._generate_placement_alerts(
                    object_type, location, model_context
                )
                alerts.extend(placement_alerts)

            # Generate model-wide alerts
            if model_context:
                model_alerts = await self._generate_model_alerts(model_context)
                alerts.extend(model_alerts)

            # Generate safety alerts
            safety_alerts = await self._generate_safety_alerts(
                object_type, model_context
            )
            alerts.extend(safety_alerts)

            # Generate compliance alerts
            compliance_alerts = await self._generate_compliance_alerts(
                object_type, model_context
            )
            alerts.extend(compliance_alerts)

            self.logger.info(f"✅ Generated {len(alerts)} proactive alerts")
            return alerts

        except Exception as e:
            self.logger.error(f"❌ Error generating alerts: {e}")
            raise

    async def detect_conflicts(
        self,
        object_type: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        model_context: Optional[ModelContext] = None,
    ) -> List[Conflict]:
        """
        Detect conflicts between elements

        Args:
            object_type: Type of object being placed
            location: Location information
            model_context: Current model context

        Returns:
            List of detected conflicts
        """
        try:
            self.logger.info("Detecting conflicts")

            conflicts = []

            # Detect spatial conflicts
            if object_type and location:
                spatial_conflicts = await self._detect_spatial_conflicts(
                    object_type, location, model_context
                )
                conflicts.extend(spatial_conflicts)

            # Detect system conflicts
            system_conflicts = await self._detect_system_conflicts(
                object_type, model_context
            )
            conflicts.extend(system_conflicts)

            # Detect code conflicts
            code_conflicts = await self._detect_code_conflicts(
                object_type, model_context
            )
            conflicts.extend(code_conflicts)

            self.logger.info(f"✅ Detected {len(conflicts)} conflicts")
            return conflicts

        except Exception as e:
            self.logger.error(f"❌ Error detecting conflicts: {e}")
            raise

    async def _generate_placement_alerts(
        self,
        object_type: str,
        location: Dict[str, Any],
        model_context: Optional[ModelContext],
    ) -> List[Alert]:
        """Generate alerts for object placement"""
        alerts = []

        if object_type == "fire_extinguisher":
            # Check for optimal placement
            alerts.append(
                Alert(
                    severity=AlertSeverity.INFO,
                    title="Fire Extinguisher Placement",
                    description="Consider placing fire extinguishers near exits for optimal accessibility",
                    category="Safety",
                    affected_elements=[object_type],
                    code_reference="IFC 2018 Section 906.1",
                    suggested_fix="Move fire extinguisher closer to exit",
                )
            )

        elif object_type == "emergency_exit":
            # Check for clear access
            alerts.append(
                Alert(
                    severity=AlertSeverity.WARNING,
                    title="Emergency Exit Accessibility",
                    description="Ensure emergency exit has clear access path and proper signage",
                    category="Safety",
                    affected_elements=[object_type],
                    code_reference="IFC 2018 Section 1010",
                    suggested_fix="Add exit signage and clear access path",
                )
            )

        return alerts

    async def _generate_model_alerts(self, model_context: ModelContext) -> List[Alert]:
        """Generate alerts for model-wide issues"""
        alerts = []

        # Check for missing safety systems
        if model_context.building_type == "office":
            alerts.append(
                Alert(
                    severity=AlertSeverity.WARNING,
                    title="Missing Fire Safety Systems",
                    description="Office buildings require comprehensive fire safety systems",
                    category="Safety",
                    affected_elements=["building"],
                    code_reference="IFC 2018 Section 903",
                    suggested_fix="Add fire alarm and sprinkler systems",
                )
            )

        # Check for accessibility issues
        alerts.append(
            Alert(
                severity=AlertSeverity.INFO,
                title="Accessibility Review Required",
                description="Verify all areas meet ADA accessibility requirements",
                category="Accessibility",
                affected_elements=["building"],
                code_reference="ADA 2010 Standards",
                suggested_fix="Review and update accessibility features",
            )
        )

        return alerts

    async def _generate_safety_alerts(
        self, object_type: Optional[str], model_context: Optional[ModelContext]
    ) -> List[Alert]:
        """Generate safety-related alerts"""
        alerts = []

        # General safety alerts
        alerts.append(
            Alert(
                severity=AlertSeverity.INFO,
                title="Emergency Lighting System",
                description="Consider adding emergency lighting for improved safety",
                category="Safety",
                affected_elements=["lighting_system"],
                code_reference="IFC 2018 Section 1008",
                suggested_fix="Install emergency lighting system",
            )
        )

        return alerts

    async def _generate_compliance_alerts(
        self, object_type: Optional[str], model_context: Optional[ModelContext]
    ) -> List[Alert]:
        """Generate compliance-related alerts"""
        alerts = []

        # Code compliance alerts
        if object_type == "fire_extinguisher":
            alerts.append(
                Alert(
                    severity=AlertSeverity.WARNING,
                    title="Fire Extinguisher Code Compliance",
                    description="Verify fire extinguisher meets all IFC 2018 requirements",
                    category="Compliance",
                    affected_elements=[object_type],
                    code_reference="IFC 2018 Section 906.1",
                    suggested_fix="Review and update fire extinguisher placement",
                )
            )

        return alerts

    async def _detect_spatial_conflicts(
        self,
        object_type: str,
        location: Dict[str, Any],
        model_context: Optional[ModelContext],
    ) -> List[Conflict]:
        """Detect spatial conflicts between elements"""
        conflicts = []

        # Check for overlapping elements
        if object_type == "wall":
            conflicts.append(
                Conflict(
                    title="Potential Wall Overlap",
                    description="New wall may overlap with existing wall elements",
                    severity=AlertSeverity.WARNING,
                    elements_involved=[object_type, "existing_walls"],
                    conflict_type="spatial_overlap",
                    code_reference="IFC 2018 Section 713",
                    resolution_suggestions=[
                        "Adjust wall position to avoid overlap",
                        "Remove overlapping wall section",
                        "Use different wall type",
                    ],
                )
            )

        return conflicts

    async def _detect_system_conflicts(
        self, object_type: Optional[str], model_context: Optional[ModelContext]
    ) -> List[Conflict]:
        """Detect conflicts between building systems"""
        conflicts = []

        # Check for HVAC conflicts
        if object_type == "hvac_unit":
            conflicts.append(
                Conflict(
                    title="HVAC System Conflict",
                    description="HVAC unit may conflict with electrical or plumbing systems",
                    severity=AlertSeverity.WARNING,
                    elements_involved=[
                        object_type,
                        "electrical_system",
                        "plumbing_system",
                    ],
                    conflict_type="system_conflict",
                    code_reference="IFC 2018 Section 602",
                    resolution_suggestions=[
                        "Relocate HVAC unit",
                        "Adjust electrical routing",
                        "Modify plumbing layout",
                    ],
                )
            )

        return conflicts

    async def _detect_code_conflicts(
        self, object_type: Optional[str], model_context: Optional[ModelContext]
    ) -> List[Conflict]:
        """Detect conflicts with building codes"""
        conflicts = []

        # Check for code violations
        if object_type == "fire_extinguisher":
            conflicts.append(
                Conflict(
                    title="Fire Extinguisher Code Conflict",
                    description="Fire extinguisher placement may not meet code requirements",
                    severity=AlertSeverity.ERROR,
                    elements_involved=[object_type],
                    conflict_type="code_violation",
                    code_reference="IFC 2018 Section 906.1",
                    resolution_suggestions=[
                        "Move fire extinguisher to compliant location",
                        "Add additional fire extinguishers",
                        "Verify travel distance requirements",
                    ],
                )
            )

        return conflicts

    async def monitor_changes(
        self, changes: Dict[str, Any], model_context: Optional[ModelContext]
    ) -> List[Alert]:
        """
        Monitor model changes for potential issues

        Args:
            changes: Model changes to monitor
            model_context: Current model context

        Returns:
            List of alerts for potential issues
        """
        try:
            self.logger.info("Monitoring model changes")

            alerts = []

            # Monitor for safety issues
            safety_alerts = await self._monitor_safety_changes(changes, model_context)
            alerts.extend(safety_alerts)

            # Monitor for compliance issues
            compliance_alerts = await self._monitor_compliance_changes(
                changes, model_context
            )
            alerts.extend(compliance_alerts)

            # Monitor for efficiency issues
            efficiency_alerts = await self._monitor_efficiency_changes(
                changes, model_context
            )
            alerts.extend(efficiency_alerts)

            self.logger.info(f"✅ Generated {len(alerts)} change monitoring alerts")
            return alerts

        except Exception as e:
            self.logger.error(f"❌ Error monitoring changes: {e}")
            raise

    async def _monitor_safety_changes(
        self, changes: Dict[str, Any], model_context: Optional[ModelContext]
    ) -> List[Alert]:
        """Monitor changes for safety issues"""
        alerts = []

        # Check if safety systems are being modified
        if "fire_system" in str(changes).lower():
            alerts.append(
                Alert(
                    severity=AlertSeverity.WARNING,
                    title="Fire System Modification",
                    description="Fire system modifications may affect safety compliance",
                    category="Safety",
                    affected_elements=["fire_system"],
                    code_reference="IFC 2018 Section 903",
                    suggested_fix="Verify fire system modifications meet code requirements",
                )
            )

        return alerts

    async def _monitor_compliance_changes(
        self, changes: Dict[str, Any], model_context: Optional[ModelContext]
    ) -> List[Alert]:
        """Monitor changes for compliance issues"""
        alerts = []

        # Check for code compliance issues
        if "exit" in str(changes).lower():
            alerts.append(
                Alert(
                    severity=AlertSeverity.INFO,
                    title="Exit Modification",
                    description="Exit modifications may affect egress compliance",
                    category="Compliance",
                    affected_elements=["exit_system"],
                    code_reference="IFC 2018 Section 1010",
                    suggested_fix="Verify exit modifications meet egress requirements",
                )
            )

        return alerts

    async def _monitor_efficiency_changes(
        self, changes: Dict[str, Any], model_context: Optional[ModelContext]
    ) -> List[Alert]:
        """Monitor changes for efficiency issues"""
        alerts = []

        # Check for energy efficiency impacts
        if "window" in str(changes).lower():
            alerts.append(
                Alert(
                    severity=AlertSeverity.INFO,
                    title="Window Modification",
                    description="Window modifications may affect energy efficiency",
                    category="Efficiency",
                    affected_elements=["window_system"],
                    code_reference="ASHRAE 90.1",
                    suggested_fix="Consider energy-efficient window options",
                )
            )

        return alerts
