#!/usr/bin/env python3
"""
Context Analyzer for MCP Intelligence Layer

Analyzes user intent, model context, and changes to provide intelligent
insights for the MCP service.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import UserIntent, ModelContext, SuggestionType


class ContextAnalyzer:
    """
    Analyzes context for intelligent decision making

    Provides analysis of user intent, model context, and changes
    to support intelligent suggestions and validation.
    """

    def __init__(self):
        """Initialize the context analyzer"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ Context Analyzer initialized")

    async def analyze_user_intent(
        self,
        action: str,
        object_type: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UserIntent:
        """
        Analyze user intent from action and context

        Args:
            action: User action being performed
            object_type: Type of object being manipulated
            location: Location information
            context: Additional context

        Returns:
            Analyzed user intent
        """
        try:
            self.logger.info(f"Analyzing user intent for action: {action}")

            # Analyze action patterns
            intent_analysis = self._analyze_action_patterns(action, object_type)

            # Determine confidence based on available information
            confidence = self._calculate_intent_confidence(
                action, object_type, location
            )

            # Create user intent
            user_intent = UserIntent(
                action=action,
                object_type=object_type,
                location=location,
                confidence=confidence,
                context=context or {},
            )

            self.logger.info(
                f"✅ User intent analyzed: {action} (confidence: {confidence:.2f})"
            )
            return user_intent

        except Exception as e:
            self.logger.error(f"❌ Error analyzing user intent: {e}")
            raise

    async def analyze_model_context(self, model_state: Dict[str, Any]) -> ModelContext:
        """
        Analyze current model context

        Args:
            model_state: Current model state

        Returns:
            Analyzed model context
        """
        try:
            self.logger.info("Analyzing model context")

            # Extract building information
            building_type = model_state.get("building_type", "unknown")
            jurisdiction = model_state.get("jurisdiction", "unknown")
            floor_count = model_state.get("floor_count")
            total_area = model_state.get("total_area")
            occupancy_type = model_state.get("occupancy_type")

            # Extract elements and systems
            elements = model_state.get("elements", [])
            systems = model_state.get("systems", [])
            violations = model_state.get("violations", [])

            # Create model context
            model_context = ModelContext(
                building_type=building_type,
                jurisdiction=jurisdiction,
                floor_count=floor_count,
                total_area=total_area,
                occupancy_type=occupancy_type,
                elements=elements,
                systems=systems,
                violations=violations,
            )

            self.logger.info(
                f"✅ Model context analyzed: {building_type} building with {len(elements)} elements"
            )
            return model_context

        except Exception as e:
            self.logger.error(f"❌ Error analyzing model context: {e}")
            raise

    async def analyze_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze model changes for impact assessment

        Args:
            changes: Model changes to analyze

        Returns:
            Analysis of changes
        """
        try:
            self.logger.info("Analyzing model changes")

            analysis = {
                "change_type": self._determine_change_type(changes),
                "affected_elements": self._identify_affected_elements(changes),
                "impact_level": self._assess_impact_level(changes),
                "potential_conflicts": self._identify_potential_conflicts(changes),
                "compliance_impact": self._assess_compliance_impact(changes),
            }

            self.logger.info(
                f"✅ Changes analyzed: {analysis['change_type']} with {analysis['impact_level']} impact"
            )
            return analysis

        except Exception as e:
            self.logger.error(f"❌ Error analyzing changes: {e}")
            raise

    async def predict_user_needs(
        self, context: ModelContext, recent_actions: List[str]
    ) -> List[str]:
        """
        Predict what user might need next based on context

        Args:
            context: Current model context
            recent_actions: Recent user actions

        Returns:
            List of predicted user needs
        """
        try:
            self.logger.info("Predicting user needs")

            predictions = []

            # Analyze building type for common needs
            if context.building_type == "office":
                predictions.extend(
                    [
                        "Add fire extinguishers",
                        "Add emergency lighting",
                        "Verify egress paths",
                        "Add accessibility features",
                    ]
                )
            elif context.building_type == "residential":
                predictions.extend(
                    [
                        "Add smoke detectors",
                        "Verify bedroom egress",
                        "Add handrails",
                        "Check electrical outlets",
                    ]
                )

            # Analyze recent actions for patterns
            if "add_fire_extinguisher" in recent_actions:
                predictions.append("Add additional fire extinguishers")

            if "add_door" in recent_actions:
                predictions.append("Add door hardware")
                predictions.append("Verify door swing clearance")

            self.logger.info(f"✅ Predicted {len(predictions)} user needs")
            return predictions

        except Exception as e:
            self.logger.error(f"❌ Error predicting user needs: {e}")
            raise

    def _analyze_action_patterns(
        self, action: str, object_type: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze action patterns for intent understanding"""
        patterns = {
            "add": "creation",
            "modify": "modification",
            "delete": "removal",
            "move": "relocation",
            "copy": "duplication",
        }

        action_type = "unknown"
        for pattern, intent in patterns.items():
            if pattern in action.lower():
                action_type = intent
                break

        return {
            "action_type": action_type,
            "object_type": object_type,
            "complexity": self._assess_action_complexity(action, object_type),
        }

    def _calculate_intent_confidence(
        self,
        action: str,
        object_type: Optional[str],
        location: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate confidence in intent detection"""
        confidence = 0.5  # Base confidence

        # Increase confidence based on available information
        if object_type:
            confidence += 0.2

        if location:
            confidence += 0.2

        if action and len(action) > 3:
            confidence += 0.1

        return min(confidence, 1.0)

    def _determine_change_type(self, changes: Dict[str, Any]) -> str:
        """Determine the type of change being made"""
        if "add" in str(changes).lower():
            return "addition"
        elif "modify" in str(changes).lower():
            return "modification"
        elif "delete" in str(changes).lower():
            return "removal"
        elif "move" in str(changes).lower():
            return "relocation"
        else:
            return "unknown"

    def _identify_affected_elements(self, changes: Dict[str, Any]) -> List[str]:
        """Identify elements affected by changes"""
        affected = []

        # Extract element IDs from changes
        if "elements" in changes:
            for element in changes["elements"]:
                if "id" in element:
                    affected.append(element["id"])

        return affected

    def _assess_impact_level(self, changes: Dict[str, Any]) -> str:
        """Assess the impact level of changes"""
        change_count = len(changes.get("elements", []))

        if change_count == 0:
            return "none"
        elif change_count <= 2:
            return "low"
        elif change_count <= 5:
            return "medium"
        else:
            return "high"

    def _identify_potential_conflicts(self, changes: Dict[str, Any]) -> List[str]:
        """Identify potential conflicts from changes"""
        conflicts = []

        # Basic conflict detection logic
        # In a real implementation, this would check for spatial conflicts,
        # code violations, etc.

        return conflicts

    def _assess_compliance_impact(self, changes: Dict[str, Any]) -> str:
        """Assess the compliance impact of changes"""
        # Basic compliance impact assessment
        # In a real implementation, this would check against building codes

        return "minimal"  # Placeholder

    def _assess_action_complexity(self, action: str, object_type: Optional[str]) -> str:
        """Assess the complexity of an action"""
        if not object_type:
            return "unknown"

        # Simple complexity assessment
        complex_objects = ["fire_suppression_system", "electrical_panel", "hvac_system"]

        if object_type in complex_objects:
            return "high"
        elif object_type in ["wall", "door", "window"]:
            return "medium"
        else:
            return "low"
