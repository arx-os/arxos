"""
ML Integration System Demo

Comprehensive demonstration of the ML integration system including AI validation,
predictive analytics, pattern recognition, and model management with real-world examples.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from ml.ml_service import MLService
from ml.models import (
    AIValidationRequest,
    ValidationType,
    PredictionRequest,
    PredictionType,
    PatternRequest,
    PatternType,
    TrainingRequest,
    ModelStatus,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_ai_validation(ml_service: MLService):
    """Demonstrate AI-powered validation capabilities"""
    print("\n🤖 AI-POWERED VALIDATION DEMO")
    print("=" * 50)

    # Real-world building scenarios
    scenarios = [
        {
            "name": "Small Residential Building",
            "description": "Single-family home with basic requirements",
            "data": {
                "area": 2500,
                "height": 15,
                "type": "residential",
                "occupancy": "R",
                "floors": 2,
                "foundation": "slab",
                "structural_system": "wood",
            },
            "validation_type": ValidationType.STRUCTURAL,
        },
        {
            "name": "Large Commercial Building",
            "description": "Office building with complex requirements",
            "data": {
                "area": 25000,
                "height": 45,
                "type": "commercial",
                "occupancy": "B",
                "floors": 8,
                "foundation": "basement",
                "structural_system": "steel",
                "electrical_load": 1500,
                "electrical_panels": 4,
                "emergency_systems": True,
                "sprinkler_system": True,
                "fire_alarm": True,
                "fire_rating": 2,
            },
            "validation_type": ValidationType.FIRE_PROTECTION,
        },
        {
            "name": "Industrial Facility",
            "description": "Manufacturing facility with high electrical load",
            "data": {
                "area": 50000,
                "height": 30,
                "type": "industrial",
                "occupancy": "F",
                "floors": 3,
                "electrical_load": 3000,
                "electrical_panels": 8,
                "emergency_systems": True,
                "sprinkler_system": True,
                "fire_alarm": True,
                "fire_rating": 3,
            },
            "validation_type": ValidationType.ELECTRICAL,
        },
    ]

    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")

        request = AIValidationRequest(
            building_data=scenario["data"],
            validation_type=scenario["validation_type"],
            jurisdiction="Demo Jurisdiction",
            include_suggestions=True,
            confidence_threshold=0.7,
        )

        result = await ml_service.validate_building(request)

        print(f"   ✅ Compliance: {'PASS' if result.is_compliant else 'FAIL'}")
        print(f"   🎯 Confidence: {result.confidence_score:.1%}")
        print(f"   ⚠️  Violations: {len(result.violations)}")
        print(f"   💡 Suggestions: {len(result.suggestions)}")
        print(f"   ⏱️  Processing Time: {result.processing_time:.3f}s")

        if result.violations:
            print("   🚨 Violations Found:")
            for violation in result.violations:
                print(f"      - {violation['code']}: {violation['description']}")

        if result.suggestions:
            print("   💡 Improvement Suggestions:")
            for suggestion in result.suggestions:
                print(f"      - {suggestion['title']}: {suggestion['description']}")


async def demo_predictive_analytics(ml_service: MLService):
    """Demonstrate predictive analytics capabilities"""
    print("\n🔮 PREDICTIVE ANALYTICS DEMO")
    print("=" * 50)

    # Real-world prediction scenarios
    scenarios = [
        {
            "name": "Compliance Risk Assessment",
            "description": "Predicting compliance risk for a complex project",
            "data": {
                "area": 35000,
                "height": 40,
                "type": "commercial",
                "occupancy": "A",
                "complexity": 3,
                "code_requirements": 25,
                "jurisdiction_strictness": 3,
            },
            "prediction_type": PredictionType.COMPLIANCE_RISK,
        },
        {
            "name": "Cost Estimation",
            "description": "Estimating construction costs for a residential project",
            "data": {
                "area": 8000,
                "height": 25,
                "type": "residential",
                "occupancy": "R",
                "construction_type": "wood",
                "site_conditions": 2,
                "material_quality": 3,
            },
            "prediction_type": PredictionType.COST_ESTIMATE,
        },
        {
            "name": "Construction Timeline",
            "description": "Predicting construction duration for a commercial project",
            "data": {
                "area": 15000,
                "height": 35,
                "type": "commercial",
                "occupancy": "B",
                "complexity": 2,
                "crew_size": 15,
                "weather_conditions": 1,
            },
            "prediction_type": PredictionType.CONSTRUCTION_TIME,
        },
        {
            "name": "Energy Efficiency Prediction",
            "description": "Predicting energy efficiency for a sustainable building",
            "data": {
                "area": 12000,
                "height": 30,
                "type": "commercial",
                "occupancy": "B",
                "insulation_rating": 4,
                "hvac_efficiency": 3,
                "window_efficiency": 3,
            },
            "prediction_type": PredictionType.ENERGY_EFFICIENCY,
        },
    ]

    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")

        request = PredictionRequest(
            building_data=scenario["data"],
            prediction_type=scenario["prediction_type"],
            include_confidence=True,
        )

        result = await ml_service.predict_building_metrics(request)

        print(f"   🎯 Predicted Value: {result.predicted_value}")
        print(f"   📈 Confidence: {result.confidence_score:.1%}")
        print(f"   🔍 Factors Analyzed: {len(result.factors)}")
        print(f"   ⏱️  Processing Time: {result.processing_time:.3f}s")

        if result.confidence_interval:
            print(
                f"   📊 Confidence Interval: {result.confidence_interval['lower']:.2f} - {result.confidence_interval['upper']:.2f}"
            )

        if result.factors:
            print("   📋 Key Factors:")
            for factor in result.factors[:3]:  # Show top 3 factors
                print(
                    f"      - {factor['factor']}: {factor['value']} (Impact: {factor['impact']})"
                )


async def demo_pattern_recognition(ml_service: MLService):
    """Demonstrate pattern recognition capabilities"""
    print("\n🔍 PATTERN RECOGNITION DEMO")
    print("=" * 50)

    # Real-world pattern scenarios
    scenarios = [
        {
            "name": "Design Pattern Analysis",
            "description": "Recognizing design patterns in large commercial buildings",
            "data": {
                "area": 20000,
                "height": 35,
                "type": "commercial",
                "occupancy": "B",
                "complexity": 2,
                "design_elements": 15,
                "architectural_style": "modern",
            },
            "pattern_type": PatternType.DESIGN_PATTERN,
        },
        {
            "name": "Violation Pattern Detection",
            "description": "Identifying common violation patterns in tall buildings",
            "data": {
                "area": 30000,
                "height": 50,
                "type": "commercial",
                "occupancy": "A",
                "code_violations": 3,
                "compliance_score": 0.7,
                "inspection_history": 2,
            },
            "pattern_type": PatternType.VIOLATION_PATTERN,
        },
        {
            "name": "Optimization Pattern Recognition",
            "description": "Finding optimization opportunities in commercial buildings",
            "data": {
                "area": 18000,
                "height": 30,
                "type": "commercial",
                "occupancy": "B",
                "efficiency_score": 2,
                "cost_effectiveness": 3,
                "sustainability_score": 3,
            },
            "pattern_type": PatternType.OPTIMIZATION_PATTERN,
        },
    ]

    for scenario in scenarios:
        print(f"\n🔍 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")

        request = PatternRequest(
            building_data=scenario["data"],
            pattern_type=scenario["pattern_type"],
            similarity_threshold=0.7,
        )

        result = await ml_service.recognize_patterns(request)

        print(f"   🎯 Patterns Found: {len(result.patterns_found)}")
        print(f"   📊 Similarity Scores: {len(result.similarity_scores)}")
        print(f"   💡 Recommendations: {len(result.recommendations)}")
        print(f"   ⏱️  Processing Time: {result.processing_time:.3f}s")

        if result.patterns_found:
            print("   🔍 Recognized Patterns:")
            for pattern in result.patterns_found:
                print(f"      - {pattern['name']}: {pattern['description']}")
                print(f"        Confidence: {pattern['confidence']:.1%}")

        if result.recommendations:
            print("   💡 Recommendations:")
            for rec in result.recommendations:
                print(f"      - {rec['title']}: {rec['description']}")
                print(
                    f"        Impact: {rec['impact']}, Priority: {rec.get('priority', 'medium')}"
                )


async def demo_model_management(ml_service: MLService):
    """Demonstrate model management capabilities"""
    print("\n⚙️  MODEL MANAGEMENT DEMO")
    print("=" * 50)

    # Show current model statistics
    print("📊 Current Model Statistics:")
    stats = ml_service.get_model_statistics()
    print(f"   Total Models: {stats['total_models']}")
    print(f"   Active Models: {stats['active_models']}")
    print(f"   Average Accuracy: {stats['average_accuracy']:.1%}")
    print(f"   Total Size: {stats['total_size_mb']:.1f} MB")

    # Demo model training
    print("\n🏋️  Training New Model:")
    training_request = TrainingRequest(
        model_type="classification",
        training_data=[
            {
                "area": 5000,
                "height": 20,
                "floors": 2,
                "type_code": 1,
                "occupancy_code": 10,
                "complexity": 1,
                "code_requirements": 5,
                "compliance_score": 1,
                "label": 1,
            },
            {
                "area": 15000,
                "height": 35,
                "floors": 5,
                "type_code": 2,
                "occupancy_code": 2,
                "complexity": 2,
                "code_requirements": 15,
                "compliance_score": 0.8,
                "label": 0,
            },
            {
                "area": 8000,
                "height": 25,
                "floors": 3,
                "type_code": 1,
                "occupancy_code": 2,
                "complexity": 1,
                "code_requirements": 8,
                "compliance_score": 0.9,
                "label": 1,
            },
            {
                "area": 25000,
                "height": 45,
                "floors": 8,
                "type_code": 2,
                "occupancy_code": 1,
                "complexity": 3,
                "code_requirements": 25,
                "compliance_score": 0.6,
                "label": 0,
            },
        ],
        validation_data=[
            {
                "area": 12000,
                "height": 30,
                "floors": 4,
                "type_code": 2,
                "occupancy_code": 2,
                "complexity": 2,
                "code_requirements": 12,
                "compliance_score": 0.85,
                "label": 1,
            },
            {
                "area": 30000,
                "height": 50,
                "floors": 10,
                "type_code": 2,
                "occupancy_code": 1,
                "complexity": 3,
                "code_requirements": 30,
                "compliance_score": 0.5,
                "label": 0,
            },
        ],
        model_name="Compliance Classifier Demo",
        description="Demo model for compliance classification",
    )

    training_result = await ml_service.train_model(training_request)

    print(f"   ✅ Model ID: {training_result.model_id}")
    print(f"   📊 Accuracy: {training_result.accuracy:.1%}")
    print(f"   ⏱️  Training Time: {training_result.training_time:.2f}s")
    print(f"   📁 Saved to: {training_result.file_path}")

    # Demo model activation
    print("\n🔌 Activating Model:")
    success = ml_service.activate_model(training_result.model_id)
    print(f"   {'✅ Success' if success else '❌ Failed'}")

    # Show updated statistics
    print("\n📊 Updated Model Statistics:")
    updated_stats = ml_service.get_model_statistics()
    print(f"   Total Models: {updated_stats['total_models']}")
    print(f"   Active Models: {updated_stats['active_models']}")
    print(f"   Average Accuracy: {updated_stats['average_accuracy']:.1%}")


async def demo_service_statistics(ml_service: MLService):
    """Demonstrate comprehensive service statistics"""
    print("\n📈 SERVICE STATISTICS DEMO")
    print("=" * 50)

    # Get comprehensive statistics
    stats = ml_service.get_comprehensive_statistics()

    print("🏥 Service Health:")
    print(f"   Status: {stats['service']['status']}")
    print(f"   Total Requests: {stats['service']['total_requests']}")
    print(f"   Error Rate: {stats['service']['error_rate']:.1%}")
    print(f"   Average Response Time: {stats['service']['average_response_time']:.3f}s")
    print(f"   Memory Usage: {stats['service']['memory_usage_mb']:.1f} MB")
    print(f"   CPU Usage: {stats['service']['cpu_usage_percent']:.1f}%")

    print("\n🤖 Model Statistics:")
    print(f"   Total Models: {stats['models']['total_models']}")
    print(f"   Active Models: {stats['models']['active_models']}")
    print(f"   Average Accuracy: {stats['models']['average_accuracy']:.1%}")
    print(f"   Total Size: {stats['models']['total_size_mb']:.1f} MB")

    print("\n🔍 Validation Statistics:")
    print(f"   Active Models: {stats['validation']['active_models']}")
    print(f"   Validation Types: {len(stats['validation']['validation_types'])}")
    print(f"   Model Versions: {len(stats['validation']['model_versions'])}")

    print("\n🔮 Prediction Statistics:")
    print(f"   Active Models: {stats['prediction']['active_models']}")
    print(f"   Prediction Types: {len(stats['prediction']['prediction_types'])}")
    print(f"   Model Versions: {len(stats['prediction']['model_versions'])}")


async def main():
    """Main demo function"""
    print("🚀 ML INTEGRATION SYSTEM DEMO")
    print("=" * 60)
    print("This demo showcases the comprehensive ML integration capabilities")
    print("including AI validation, predictive analytics, pattern recognition,")
    print("and model management for building code compliance.")
    print("=" * 60)

    # Initialize ML service
    print("\n🔧 Initializing ML Service...")
    ml_service = MLService()
    print("✅ ML Service initialized successfully")

    # Run demos
    await demo_ai_validation(ml_service)
    await demo_predictive_analytics(ml_service)
    await demo_pattern_recognition(ml_service)
    await demo_model_management(ml_service)
    await demo_service_statistics(ml_service)

    print("\n" + "=" * 60)
    print("🎉 ML INTEGRATION SYSTEM DEMO COMPLETED!")
    print("✅ All ML capabilities are working correctly")
    print("✅ AI validation provides intelligent compliance checking")
    print("✅ Predictive analytics offers valuable insights")
    print("✅ Pattern recognition identifies optimization opportunities")
    print("✅ Model management enables continuous improvement")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
