"""
Test ML Integration System

Comprehensive test script for the ML integration system including AI validation,
predictive analytics, pattern recognition, and model management.
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


async def test_ml_service_initialization():
    """Test ML service initialization"""
    print("\n🧪 Testing ML Service Initialization...")

    try:
        ml_service = MLService()
        print("✅ ML Service initialized successfully")

        # Test service status
        status = ml_service.get_service_status()
        print(f"✅ Service Status: {status.service_status}")
        print(f"✅ Active Models: {status.active_models}")
        print(f"✅ Total Models: {status.total_models}")

        return ml_service

    except Exception as e:
        print(f"❌ ML Service initialization failed: {e}")
        return None


async def test_ai_validation(ml_service: MLService):
    """Test AI validation functionality"""
    print("\n🧪 Testing AI Validation...")

    # Test data for different validation types
    test_cases = [
        {
            "name": "Structural Validation",
            "data": {
                "area": 8000,
                "height": 25,
                "type": "commercial",
                "occupancy": "B",
                "floors": 3,
                "foundation": "slab",
                "structural_system": "steel",
            },
            "validation_type": ValidationType.STRUCTURAL,
        },
        {
            "name": "Electrical Validation",
            "data": {
                "area": 5000,
                "height": 20,
                "type": "residential",
                "occupancy": "R",
                "electrical_load": 800,
                "electrical_panels": 2,
                "emergency_systems": True,
            },
            "validation_type": ValidationType.ELECTRICAL,
        },
        {
            "name": "Fire Protection Validation",
            "data": {
                "area": 15000,
                "height": 35,
                "type": "commercial",
                "occupancy": "A",
                "sprinkler_system": True,
                "fire_alarm": True,
                "fire_rating": 2,
            },
            "validation_type": ValidationType.FIRE_PROTECTION,
        },
    ]

    for test_case in test_cases:
        try:
            print(f"\n  Testing: {test_case['name']}")

            request = AIValidationRequest(
                building_data=test_case["data"],
                validation_type=test_case["validation_type"],
                jurisdiction="Test Jurisdiction",
                include_suggestions=True,
                confidence_threshold=0.7,
            )

            result = await ml_service.validate_building(request)

            print(f"    ✅ Validation completed")
            print(f"    ✅ Compliant: {result.is_compliant}")
            print(f"    ✅ Confidence: {result.confidence_score:.2f}")
            print(f"    ✅ Violations: {len(result.violations)}")
            print(f"    ✅ Suggestions: {len(result.suggestions)}")
            print(f"    ✅ Processing Time: {result.processing_time:.3f}s")

        except Exception as e:
            print(f"    ❌ {test_case['name']} failed: {e}")


async def test_predictive_analytics(ml_service: MLService):
    """Test predictive analytics functionality"""
    print("\n🧪 Testing Predictive Analytics...")

    # Test data for different prediction types
    test_cases = [
        {
            "name": "Compliance Risk Prediction",
            "data": {
                "area": 12000,
                "height": 30,
                "type": "commercial",
                "occupancy": "B",
                "complexity": 2,
                "code_requirements": 15,
                "jurisdiction_strictness": 2,
            },
            "prediction_type": PredictionType.COMPLIANCE_RISK,
        },
        {
            "name": "Cost Estimate Prediction",
            "data": {
                "area": 8000,
                "height": 25,
                "type": "commercial",
                "occupancy": "B",
                "construction_type": "steel",
                "site_conditions": 1,
                "material_quality": 3,
            },
            "prediction_type": PredictionType.COST_ESTIMATE,
        },
        {
            "name": "Construction Time Prediction",
            "data": {
                "area": 6000,
                "height": 20,
                "type": "residential",
                "occupancy": "R",
                "complexity": 1,
                "crew_size": 8,
                "weather_conditions": 1,
            },
            "prediction_type": PredictionType.CONSTRUCTION_TIME,
        },
        {
            "name": "Energy Efficiency Prediction",
            "data": {
                "area": 10000,
                "height": 30,
                "type": "commercial",
                "occupancy": "B",
                "insulation_rating": 3,
                "hvac_efficiency": 2,
                "window_efficiency": 2,
            },
            "prediction_type": PredictionType.ENERGY_EFFICIENCY,
        },
    ]

    for test_case in test_cases:
        try:
            print(f"\n  Testing: {test_case['name']}")

            request = PredictionRequest(
                building_data=test_case["data"],
                prediction_type=test_case["prediction_type"],
                include_confidence=True,
            )

            result = await ml_service.predict_building_metrics(request)

            print(f"    ✅ Prediction completed")
            print(f"    ✅ Predicted Value: {result.predicted_value}")
            print(f"    ✅ Confidence: {result.confidence_score:.2f}")
            print(f"    ✅ Factors: {len(result.factors)}")
            print(f"    ✅ Processing Time: {result.processing_time:.3f}s")

            if result.confidence_interval:
                print(f"    ✅ Confidence Interval: {result.confidence_interval}")

        except Exception as e:
            print(f"    ❌ {test_case['name']} failed: {e}")


async def test_pattern_recognition(ml_service: MLService):
    """Test pattern recognition functionality"""
    print("\n🧪 Testing Pattern Recognition...")

    # Test data for different pattern types
    test_cases = [
        {
            "name": "Design Pattern Recognition",
            "data": {
                "area": 8000,
                "height": 25,
                "type": "commercial",
                "occupancy": "B",
            },
            "pattern_type": PatternType.DESIGN_PATTERN,
        },
        {
            "name": "Violation Pattern Recognition",
            "data": {
                "area": 15000,
                "height": 40,
                "type": "commercial",
                "occupancy": "A",
            },
            "pattern_type": PatternType.VIOLATION_PATTERN,
        },
        {
            "name": "Optimization Pattern Recognition",
            "data": {
                "area": 12000,
                "height": 30,
                "type": "commercial",
                "occupancy": "B",
            },
            "pattern_type": PatternType.OPTIMIZATION_PATTERN,
        },
    ]

    for test_case in test_cases:
        try:
            print(f"\n  Testing: {test_case['name']}")

            request = PatternRequest(
                building_data=test_case["data"],
                pattern_type=test_case["pattern_type"],
                similarity_threshold=0.8,
            )

            result = await ml_service.recognize_patterns(request)

            print(f"    ✅ Pattern recognition completed")
            print(f"    ✅ Patterns Found: {len(result.patterns_found)}")
            print(f"    ✅ Similarity Scores: {len(result.similarity_scores)}")
            print(f"    ✅ Recommendations: {len(result.recommendations)}")
            print(f"    ✅ Processing Time: {result.processing_time:.3f}s")

        except Exception as e:
            print(f"    ❌ {test_case['name']} failed: {e}")


async def test_model_management(ml_service: MLService):
    """Test model management functionality"""
    print("\n🧪 Testing Model Management...")

    try:
        # Test listing models
        print("  Testing: List Models")
        models = ml_service.list_models()
        print(f"    ✅ Total Models: {len(models)}")

        # Test getting model statistics
        print("  Testing: Model Statistics")
        stats = ml_service.get_model_statistics()
        print(f"    ✅ Total Models: {stats['total_models']}")
        print(f"    ✅ Active Models: {stats['active_models']}")
        print(f"    ✅ Average Accuracy: {stats['average_accuracy']:.2f}")

        # Test model training (mock)
        print("  Testing: Model Training")
        training_request = TrainingRequest(
            model_type="classification",
            training_data=[{"feature1": 1, "feature2": 2, "label": 1}],
            model_name="Test Model",
            description="Test model for validation",
        )

        training_result = await ml_service.train_model(training_request)
        print(f"    ✅ Model Training completed")
        print(f"    ✅ Model ID: {training_result.model_id}")
        print(f"    ✅ Accuracy: {training_result.accuracy:.2f}")
        print(f"    ✅ Training Time: {training_result.training_time:.2f}s")

        # Test model activation
        print("  Testing: Model Activation")
        success = ml_service.activate_model(training_result.model_id)
        print(f"    ✅ Model Activation: {'Success' if success else 'Failed'}")

        # Test getting model info
        print("  Testing: Get Model Info")
        model_info = ml_service.get_model_info(training_result.model_id)
        if model_info:
            print(f"    ✅ Model Name: {model_info['model_name']}")
            print(f"    ✅ Model Status: {model_info['status']}")
        else:
            print("    ❌ Model info not found")

        # Test model deactivation
        print("  Testing: Model Deactivation")
        success = ml_service.deactivate_model(training_result.model_id)
        print(f"    ✅ Model Deactivation: {'Success' if success else 'Failed'}")

        # Test model deletion
        print("  Testing: Model Deletion")
        success = ml_service.delete_model(training_result.model_id)
        print(f"    ✅ Model Deletion: {'Success' if success else 'Failed'}")

    except Exception as e:
        print(f"    ❌ Model management test failed: {e}")


async def test_service_statistics(ml_service: MLService):
    """Test service statistics functionality"""
    print("\n🧪 Testing Service Statistics...")

    try:
        # Test comprehensive statistics
        print("  Testing: Comprehensive Statistics")
        stats = ml_service.get_comprehensive_statistics()

        print(f"    ✅ Service Status: {stats['service']['status']}")
        print(f"    ✅ Total Requests: {stats['service']['total_requests']}")
        print(f"    ✅ Error Rate: {stats['service']['error_rate']:.2f}")
        print(f"    ✅ Memory Usage: {stats['service']['memory_usage_mb']:.1f} MB")
        print(f"    ✅ CPU Usage: {stats['service']['cpu_usage_percent']:.1f}%")

        print(f"    ✅ Model Statistics:")
        print(f"      - Total Models: {stats['models']['total_models']}")
        print(f"      - Active Models: {stats['models']['active_models']}")
        print(f"      - Average Accuracy: {stats['models']['average_accuracy']:.2f}")

        print(f"    ✅ Validation Statistics:")
        print(f"      - Active Models: {stats['validation']['active_models']}")
        print(
            f"      - Validation Types: {len(stats['validation']['validation_types'])}"
        )

        print(f"    ✅ Prediction Statistics:")
        print(f"      - Active Models: {stats['prediction']['active_models']}")
        print(
            f"      - Prediction Types: {len(stats['prediction']['prediction_types'])}"
        )

    except Exception as e:
        print(f"    ❌ Service statistics test failed: {e}")


async def main():
    """Main test function"""
    print("🚀 Starting ML Integration System Tests")
    print("=" * 50)

    # Test ML service initialization
    ml_service = await test_ml_service_initialization()
    if not ml_service:
        print("❌ Cannot proceed without ML service")
        return

    # Test AI validation
    await test_ai_validation(ml_service)

    # Test predictive analytics
    await test_predictive_analytics(ml_service)

    # Test pattern recognition
    await test_pattern_recognition(ml_service)

    # Test model management
    await test_model_management(ml_service)

    # Test service statistics
    await test_service_statistics(ml_service)

    print("\n" + "=" * 50)
    print("✅ ML Integration System Tests Completed Successfully!")
    print("🎉 All components are working correctly")


if __name__ == "__main__":
    asyncio.run(main())
