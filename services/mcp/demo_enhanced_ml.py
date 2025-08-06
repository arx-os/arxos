#!/usr/bin/env python3
"""
Enhanced ML System Demo

This demo showcases the enhanced ML integration system with real model training,
advanced validation, and production-ready ML pipelines for building code compliance.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

from ml.enhanced_ml_service import enhanced_ml_service
from ml.models import (
    AIValidationRequest,
    ValidationType,
    PredictionRequest,
    PredictionType,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_enhanced_validation():
    """Demonstrate enhanced AI validation with real ML models"""
    print("\n🤖 ENHANCED AI VALIDATION DEMO")
    print("=" * 50)

    # Test scenarios with real building data
    scenarios = [
        {
            "name": "Small Residential Building",
            "description": "Single-family home with basic requirements",
            "data": {
                "building_id": "res_001",
                "building_area": 2500,
                "building_height": 15,
                "floors": 2,
                "occupancy_type": "residential",
                "construction_type": "wood",
                "fire_rating": 1,
                "electrical_load": 800,
                "emergency_exits": 2,
            },
            "validation_type": ValidationType.STRUCTURAL,
        },
        {
            "name": "Large Commercial Building",
            "description": "Office building with complex requirements",
            "data": {
                "building_id": "com_001",
                "building_area": 25000,
                "building_height": 45,
                "floors": 8,
                "occupancy_type": "commercial",
                "construction_type": "steel",
                "fire_rating": 2,
                "electrical_load": 1500,
                "emergency_exits": 6,
            },
            "validation_type": ValidationType.FIRE_PROTECTION,
        },
        {
            "name": "Industrial Facility",
            "description": "Manufacturing facility with high electrical load",
            "data": {
                "building_id": "ind_001",
                "building_area": 50000,
                "building_height": 30,
                "floors": 3,
                "occupancy_type": "industrial",
                "construction_type": "concrete",
                "fire_rating": 3,
                "electrical_load": 3000,
                "emergency_exits": 8,
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

        start_time = time.time()
        result = await enhanced_ml_service.validate_building(request)
        processing_time = time.time() - start_time

        print(f"   ✅ Compliance: {'PASS' if result.is_compliant else 'FAIL'}")
        print(f"   🎯 Confidence: {result.confidence_score:.1%}")
        print(f"   ⚠️  Violations: {len(result.violations)}")
        print(f"   💡 Suggestions: {len(result.suggestions)}")
        print(f"   ⏱️  Processing Time: {processing_time:.3f}s")
        print(f"   🤖 Model Version: {result.model_version}")

        if result.violations:
            print("   🚨 Violations Found:")
            for violation in result.violations:
                print(f"      - {violation['rule_id']}: {violation['message']}")

        if result.suggestions:
            print("   💡 Improvement Suggestions:")
            for suggestion in result.suggestions:
                print(f"      - {suggestion['message']}")


async def demo_enhanced_prediction():
    """Demonstrate enhanced predictive analytics with real ML models"""
    print("\n🔮 ENHANCED PREDICTIVE ANALYTICS DEMO")
    print("=" * 50)

    # Test scenarios for different prediction types
    scenarios = [
        {
            "name": "Cost Estimation",
            "description": "Estimating construction costs for a residential project",
            "data": {
                "building_area": 8000,
                "construction_type": "wood",
                "complexity": 2,
                "location_factor": 1.1,
                "material_quality": 3,
                "crew_size": 12,
                "weather_factor": 1.0,
            },
            "prediction_type": PredictionType.COST_ESTIMATE,
        },
        {
            "name": "Construction Timeline",
            "description": "Predicting construction duration for a commercial project",
            "data": {
                "building_area": 15000,
                "construction_type": "steel",
                "complexity": 3,
                "location_factor": 1.2,
                "material_quality": 4,
                "crew_size": 18,
                "weather_factor": 0.9,
            },
            "prediction_type": PredictionType.CONSTRUCTION_TIME,
        },
        {
            "name": "Compliance Risk",
            "description": "Predicting compliance risk for a complex project",
            "data": {
                "building_area": 35000,
                "construction_type": "concrete",
                "complexity": 4,
                "location_factor": 1.3,
                "material_quality": 5,
                "crew_size": 25,
                "weather_factor": 1.1,
            },
            "prediction_type": PredictionType.COMPLIANCE_RISK,
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

        start_time = time.time()
        result = await enhanced_ml_service.predict(request)
        processing_time = time.time() - start_time

        print(f"   🎯 Predicted Value: {result.predicted_value:,.2f}")
        print(f"   📈 Confidence: {result.confidence_score:.1%}")
        print(f"   🔍 Factors Analyzed: {len(result.factors)}")
        print(f"   ⏱️  Processing Time: {processing_time:.3f}s")
        print(f"   🤖 Model Version: {result.model_version}")


async def demo_model_training():
    """Demonstrate model training capabilities"""
    print("\n🏋️  MODEL TRAINING DEMO")
    print("=" * 50)

    # Train validation models
    validation_types = [
        ValidationType.STRUCTURAL,
        ValidationType.FIRE_PROTECTION,
        ValidationType.ELECTRICAL,
    ]

    print("\n🔧 Training Validation Models:")
    for val_type in validation_types:
        print(f"   Training {val_type.value} validator...")
        start_time = time.time()
        model_id = await enhanced_ml_service.train_validation_model(val_type)
        training_time = time.time() - start_time

        metadata = enhanced_ml_service.metadata[model_id]
        print(f"   ✅ Model ID: {model_id}")
        print(f"   📊 Accuracy: {metadata.accuracy:.1%}")
        print(f"   ⏱️  Training Time: {training_time:.3f}s")
        print(f"   📅 Training Date: {metadata.training_date}")

    # Train prediction models
    prediction_types = [
        PredictionType.COST_ESTIMATE,
        PredictionType.CONSTRUCTION_TIME,
        PredictionType.COMPLIANCE_RISK,
    ]

    print("\n🔧 Training Prediction Models:")
    for pred_type in prediction_types:
        print(f"   Training {pred_type.value} predictor...")
        start_time = time.time()
        model_id = await enhanced_ml_service.train_prediction_model(pred_type)
        training_time = time.time() - start_time

        metadata = enhanced_ml_service.metadata[model_id]
        print(f"   ✅ Model ID: {model_id}")
        print(f"   📊 Accuracy: {metadata.accuracy:.1%}")
        print(f"   ⏱️  Training Time: {training_time:.3f}s")
        print(f"   📅 Training Date: {metadata.training_date}")


async def demo_model_statistics():
    """Demonstrate model statistics and management"""
    print("\n📈 MODEL STATISTICS DEMO")
    print("=" * 50)

    stats = enhanced_ml_service.get_model_statistics()

    print(f"📊 Model Statistics:")
    print(f"   Total Models: {stats['total_models']}")
    print(f"   Average Accuracy: {stats['average_accuracy']:.1%}")
    print(f"   Total Size: {stats['total_size'] / 1024:.2f} KB")

    print(f"\n🔍 Model Types:")
    for model_type, count in stats["model_types"].items():
        print(f"   {model_type}: {count} models")

    print(f"\n📋 Model Details:")
    for model_id, metadata in enhanced_ml_service.metadata.items():
        print(f"   {model_id}:")
        print(f"     Type: {metadata.model_type}")
        print(f"     Accuracy: {metadata.accuracy:.1%}")
        print(f"     Features: {len(metadata.features)}")
        print(f"     Size: {metadata.model_size / 1024:.2f} KB")
        print(f"     Training Date: {metadata.training_date}")


async def main():
    """Main demo function"""
    print("🚀 ENHANCED ML INTEGRATION SYSTEM DEMO")
    print("=" * 60)
    print("This demo showcases the enhanced ML integration capabilities")
    print("including real model training, advanced validation, and")
    print("production-ready ML pipelines for building code compliance.")
    print("=" * 60)

    try:
        # Demo model training
        await demo_model_training()

        # Demo enhanced validation
        await demo_enhanced_validation()

        # Demo enhanced prediction
        await demo_enhanced_prediction()

        # Demo model statistics
        await demo_model_statistics()

        print("\n" + "=" * 60)
        print("🎉 ENHANCED ML INTEGRATION SYSTEM DEMO COMPLETED!")
        print("✅ Real ML models trained and deployed")
        print("✅ Enhanced validation with actual predictions")
        print("✅ Advanced predictive analytics working")
        print("✅ Model management and statistics operational")
        print("✅ Production-ready ML pipeline established")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
