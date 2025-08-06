#!/usr/bin/env python3
"""
MCP Intelligence Layer Demo

Demonstrates the capabilities of the MCP Intelligence Layer including
context analysis, suggestions, proactive monitoring, and real-time validation.
"""

import asyncio
import json
from typing import Dict, Any
from datetime import datetime

from intelligence.intelligence_service import MCPIntelligenceService
from intelligence.models import SuggestionType, AlertSeverity, ValidationStatus


class IntelligenceDemo:
    """Demo class for showcasing intelligence layer capabilities"""

    def __init__(self):
        """Initialize the demo"""
        self.intelligence_service = MCPIntelligenceService()
        self.demo_model_state = self._create_demo_model_state()

    def _create_demo_model_state(self) -> Dict[str, Any]:
        """Create a demo model state"""
        return {
            "building_type": "office",
            "jurisdiction": "IFC_2018",
            "floor_count": 2,
            "total_area": 5000.0,
            "occupancy_type": "business",
            "elements": [
                {
                    "id": "wall_1",
                    "type": "wall",
                    "location": {"x": 0, "y": 0, "width": 20, "height": 3},
                },
                {"id": "door_1", "type": "door", "location": {"x": 10, "y": 0}},
                {"id": "window_1", "type": "window", "location": {"x": 5, "y": 0}},
            ],
            "systems": [
                {
                    "id": "electrical_1",
                    "type": "electrical",
                    "location": {"x": 15, "y": 15},
                },
                {"id": "hvac_1", "type": "hvac", "location": {"x": 18, "y": 18}},
            ],
            "violations": [],
        }

    async def demo_context_analysis(self):
        """Demo context analysis for object placement"""
        print("\n" + "=" * 60)
        print("🎯 DEMO: Context Analysis for Fire Extinguisher Placement")
        print("=" * 60)

        # Provide context for fire extinguisher placement
        context = await self.intelligence_service.provide_context(
            object_type="fire_extinguisher",
            location={"x": 5, "y": 5, "floor": 1},
            model_state=self.demo_model_state,
        )

        print(f"✅ Context Analysis Complete")
        print(
            f"📊 User Intent: {context.user_intent.action} (confidence: {context.user_intent.confidence:.2f})"
        )
        print(f"🏗️ Building Type: {context.model_context.building_type}")
        print(f"📋 Jurisdiction: {context.model_context.jurisdiction}")

        print(f"\n💡 Suggestions Generated: {len(context.suggestions)}")
        for i, suggestion in enumerate(context.suggestions[:3], 1):
            print(f"  {i}. {suggestion.title}")
            print(f"     Type: {suggestion.type.value}")
            print(f"     Priority: {suggestion.priority}")
            print(f"     Confidence: {suggestion.confidence:.2f}")
            print(f"     Description: {suggestion.description}")
            print()

        print(f"⚠️ Alerts Generated: {len(context.alerts)}")
        for alert in context.alerts[:2]:
            print(f"  - {alert.title} ({alert.severity.value})")
            print(f"    {alert.description}")
            print()

        print(f"🔍 Validation Status: {context.validation_result.status.value}")
        print(f"📝 Validation Message: {context.validation_result.message}")

        return context

    async def demo_suggestions(self):
        """Demo intelligent suggestions"""
        print("\n" + "=" * 60)
        print("💡 DEMO: Intelligent Suggestions")
        print("=" * 60)

        # Generate suggestions for adding a fire extinguisher
        suggestions = await self.intelligence_service.generate_suggestions(
            action="add_fire_extinguisher", model_state=self.demo_model_state
        )

        print(f"✅ Generated {len(suggestions)} suggestions")

        # Group suggestions by type
        suggestions_by_type = {}
        for suggestion in suggestions:
            suggestion_type = suggestion.type.value
            if suggestion_type not in suggestions_by_type:
                suggestions_by_type[suggestion_type] = []
            suggestions_by_type[suggestion_type].append(suggestion)

        for suggestion_type, type_suggestions in suggestions_by_type.items():
            print(f"\n📋 {suggestion_type.upper()} Suggestions:")
            for suggestion in type_suggestions:
                print(f"  • {suggestion.title}")
                print(
                    f"    Priority: {suggestion.priority}, Confidence: {suggestion.confidence:.2f}"
                )
                if suggestion.code_reference:
                    print(f"    Code: {suggestion.code_reference}")
                print(f"    {suggestion.description}")
                print()

        return suggestions

    async def demo_realtime_validation(self):
        """Demo real-time validation"""
        print("\n" + "=" * 60)
        print("⚡ DEMO: Real-time Validation")
        print("=" * 60)

        # Simulate model changes
        changes = {
            "elements": [
                {
                    "id": "fire_ext_1",
                    "type": "fire_extinguisher",
                    "location": {"x": 25, "y": 25, "floor": 1},
                    "properties": {"capacity": "10lb", "type": "ABC"},
                }
            ],
            "modifications": [
                {
                    "element_id": "wall_1",
                    "change": "extended",
                    "new_dimensions": {"width": 25, "height": 3},
                }
            ],
        }

        # Perform real-time validation
        validation_result = await self.intelligence_service.validate_realtime(
            model_changes=changes, model_state=self.demo_model_state
        )

        print(f"✅ Real-time Validation Complete")
        print(f"📊 Status: {validation_result.status.value}")
        print(f"📝 Message: {validation_result.message}")
        print(f"🎯 Confidence: {validation_result.confidence:.2f}")

        if validation_result.violations:
            print(f"\n❌ Violations Found: {len(validation_result.violations)}")
            for violation in validation_result.violations:
                print(f"  - {violation.get('description', 'Unknown violation')}")

        if validation_result.warnings:
            print(f"\n⚠️ Warnings: {len(validation_result.warnings)}")
            for warning in validation_result.warnings:
                print(f"  - {warning.get('description', 'Unknown warning')}")

        if validation_result.suggestions:
            print(f"\n💡 Fix Suggestions: {len(validation_result.suggestions)}")
            for suggestion in validation_result.suggestions[:2]:
                print(f"  - {suggestion.title}")
                print(f"    {suggestion.description}")

        return validation_result

    async def demo_code_references(self):
        """Demo code reference retrieval"""
        print("\n" + "=" * 60)
        print("📚 DEMO: Building Code References")
        print("=" * 60)

        # Get code reference for fire extinguisher requirements
        code_ref = await self.intelligence_service.get_code_reference(
            requirement="906.1", jurisdiction="IFC_2018"
        )

        print(f"✅ Code Reference Retrieved")
        print(f"📋 Code: {code_ref.code}")
        print(f"📄 Section: {code_ref.section}")
        print(f"📝 Title: {code_ref.title}")
        print(f"📖 Description: {code_ref.description}")
        print(f"🌍 Jurisdiction: {code_ref.jurisdiction}")

        print(f"\n📋 Requirements:")
        for i, requirement in enumerate(code_ref.requirements, 1):
            print(f"  {i}. {requirement}")

        if code_ref.exceptions:
            print(f"\n⚠️ Exceptions:")
            for exception in code_ref.exceptions:
                print(f"  - {exception}")

        return code_ref

    async def demo_proactive_monitoring(self):
        """Demo proactive monitoring"""
        print("\n" + "=" * 60)
        print("🔍 DEMO: Proactive Monitoring")
        print("=" * 60)

        # Perform proactive monitoring
        alerts = await self.intelligence_service.monitor_proactive(
            self.demo_model_state
        )

        print(f"✅ Proactive Monitoring Complete")
        print(f"⚠️ Alerts Generated: {len(alerts)}")

        # Group alerts by severity
        alerts_by_severity = {}
        for alert in alerts:
            severity = alert.severity.value
            if severity not in alerts_by_severity:
                alerts_by_severity[severity] = []
            alerts_by_severity[severity].append(alert)

        for severity, severity_alerts in alerts_by_severity.items():
            print(f"\n{severity.upper()} Alerts ({len(severity_alerts)}):")
            for alert in severity_alerts:
                print(f"  • {alert.title}")
                print(f"    Category: {alert.category}")
                print(f"    {alert.description}")
                if alert.suggested_fix:
                    print(f"    💡 Fix: {alert.suggested_fix}")
                print()

        return alerts

    async def demo_improvements(self):
        """Demo improvement suggestions"""
        print("\n" + "=" * 60)
        print("🚀 DEMO: Model Improvement Suggestions")
        print("=" * 60)

        # Get improvement suggestions
        improvements = await self.intelligence_service.suggest_improvements(
            self.demo_model_state
        )

        print(f"✅ Improvement Analysis Complete")
        print(f"💡 Improvements Suggested: {len(improvements)}")

        for improvement in improvements:
            print(f"\n📋 {improvement.title}")
            print(f"   Category: {improvement.category}")
            print(f"   Impact Score: {improvement.impact_score:.2f}")
            print(f"   Effort Required: {improvement.effort_required}")
            print(f"   Cost Impact: {improvement.cost_impact}")
            print(f"   Time Impact: {improvement.time_impact}")
            print(f"   Description: {improvement.description}")

            if improvement.implementation_steps:
                print(f"   📋 Implementation Steps:")
                for i, step in enumerate(improvement.implementation_steps, 1):
                    print(f"      {i}. {step}")
            print()

        return improvements

    async def run_full_demo(self):
        """Run the complete intelligence layer demo"""
        print("🧠 MCP Intelligence Layer Demo")
        print("=" * 60)
        print("This demo showcases the intelligent capabilities of the MCP service")
        print("including context analysis, suggestions, validation, and monitoring.")
        print()

        try:
            # Run all demos
            await self.demo_context_analysis()
            await self.demo_suggestions()
            await self.demo_realtime_validation()
            await self.demo_code_references()
            await self.demo_proactive_monitoring()
            await self.demo_improvements()

            print("\n" + "=" * 60)
            print("🎉 DEMO COMPLETE!")
            print("=" * 60)
            print("The MCP Intelligence Layer provides comprehensive")
            print("intelligent assistance for building design and code compliance.")
            print()
            print("Key Features Demonstrated:")
            print("✅ Context-aware analysis")
            print("✅ Intelligent suggestions")
            print("✅ Real-time validation")
            print("✅ Building code references")
            print("✅ Proactive monitoring")
            print("✅ Improvement suggestions")
            print()

        except Exception as e:
            print(f"❌ Demo error: {e}")
            raise


async def main():
    """Main demo function"""
    demo = IntelligenceDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())
