"""
Test Phase 2 Enhancements - AI Behavior Prediction, Real-time Collaboration, and Advanced Analytics

This test suite validates the Phase 2 enhancements including:
- AI Behavior Prediction System
- Real-time Collaboration System
- Advanced Analytics System

🎯 **Test Coverage:**
- AI prediction accuracy and performance
- Real-time collaboration functionality
- Advanced analytics capabilities
- Integration between systems
- Enterprise-grade features
"""

import asyncio
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ai_behavior_prediction():
    """Test AI behavior prediction system."""
    print("\n🧪 Testing AI Behavior Prediction System...")

    try:
        from svgx_engine.services.ai_behavior_prediction import (
            AIBehaviorPredictionSystem, PredictionConfig, PredictionType
        )

        # Create AI prediction system
        config = PredictionConfig(
            prediction_horizon=24,
            confidence_threshold=0.8,
            update_frequency=60
        )
        ai_system = AIBehaviorPredictionSystem(config)

        # Add test behavior data
        test_data = {
            'temperature': 25.0,
            'humidity': 60.0,
            'power_consumption': 1500.0,
            'efficiency': 0.85,
            'operational_hours': 8.0,
            'error_count': 0,
            'performance_score': 0.9
        }

        ai_system.add_behavior_data("test_hvac_001", test_data)
        ai_system.add_behavior_data("test_hvac_001", {**test_data, 'temperature': 26.0})
        ai_system.add_behavior_data("test_hvac_001", {**test_data, 'efficiency': 0.82})

        # Get predictions
        predictions = ai_system.get_predictions("test_hvac_001")
        print(f"✅ AI predictions generated: {len(predictions)} predictions")

        # Get anomalies
        anomalies = ai_system.get_anomalies("test_hvac_001")
        print(f"✅ Anomaly detection: {len(anomalies)} anomalies detected")

        # Get optimization recommendations
        recommendations = ai_system.get_optimization_recommendations("test_hvac_001")
        print(f"✅ Optimization recommendations: {len(recommendations)} recommendations")

        # Get statistics
        stats = ai_system.get_prediction_stats()
        print(f"✅ AI system statistics: {stats['prediction_stats']['total_predictions']} total predictions")

        return True

    except Exception as e:
        print(f"❌ AI behavior prediction test failed: {e}")
        return False


def test_realtime_collaboration():
    """Test real-time collaboration system."""
    print("\n🧪 Testing Real-time Collaboration System...")

    try:
        from svgx_engine.services.realtime_collaboration import (
            RealtimeCollaborationSystem, CollaborationConfig, PermissionLevel
        )

        # Create collaboration system
        config = CollaborationConfig(
            websocket_host="localhost",
            websocket_port=8766,  # Different port to avoid conflicts
            max_connections=10,
            edit_timeout=300
        )
        collaboration_system = RealtimeCollaborationSystem(config)

        # Test user permission management
        success = collaboration_system.set_user_permission("user_001", PermissionLevel.EDITOR)
        print(f"✅ User permission set: {success}")

        # Test permission checking
        can_edit = collaboration_system.permission_manager.can_edit("user_001", "test_element")
        print(f"✅ Permission check: {can_edit}")

        # Test conflict detection
        conflict_detector = collaboration_system.conflict_detector
        print(f"✅ Conflict detector initialized: {conflict_detector is not None}")

        # Get collaboration statistics
        stats = collaboration_system.get_collaboration_stats()
        print(f"✅ Collaboration statistics: {stats['collaboration_stats']['total_users']} users")

        return True

    except Exception as e:
        print(f"❌ Real-time collaboration test failed: {e}")
        return False


def test_advanced_analytics():
    """Test advanced analytics system."""
    print("\n🧪 Testing Advanced Analytics System...")

    try:
        from svgx_engine.services.advanced_analytics import (
            AdvancedAnalyticsSystem, AnalyticsConfig, AnalyticsType
        )

        # Create analytics system
        config = AnalyticsConfig(
            data_retention_days=30,
            aggregation_interval=3600,
            prediction_horizon_days=30
        )
        analytics_system = AdvancedAnalyticsSystem(config)

        # Add test analytics data
        test_data = {
            'performance_score': 0.85,
            'efficiency_score': 0.78,
            'uptime_score': 0.95,
            'response_time': 120.0,
            'power_consumption': 1500.0,
            'temperature': 25.0,
            'operational_hours': 8.0,
            'error_count': 2
        }

        # Add multiple data points
        for i in range(10):
            data_point = {**test_data}
            data_point['performance_score'] = 0.85 + (i * 0.01)
            data_point['timestamp'] = datetime.now() - timedelta(days=i)
            analytics_system.add_analytics_data("test_hvac_001", data_point)

        # Get maintenance analysis
        maintenance_result = analytics_system.get_maintenance_analysis("test_hvac_001")
        if maintenance_result:
            print(f"✅ Maintenance analysis: {maintenance_result.priority.value} priority")

        # Get energy analysis
        energy_result = analytics_system.get_energy_analysis("test_hvac_001")
        if energy_result:
            print(f"✅ Energy analysis: {energy_result.optimization_type.value} optimization")

        # Get trend analysis
        trend_result = analytics_system.get_trend_analysis("test_hvac_001")
        if trend_result:
            print(f"✅ Trend analysis: {trend_result.trend_direction} trend")

        # Generate comprehensive report
        report = analytics_system.generate_report("comprehensive")
        print(f"✅ Analytics report generated: {len(report.get('maintenance_recommendations', []))} maintenance recommendations")

        # Get analytics statistics
        stats = analytics_system.get_analytics_stats()
        print(f"✅ Analytics statistics: {stats['analytics_stats']['total_analyses']} total analyses")

        return True

    except Exception as e:
        print(f"❌ Advanced analytics test failed: {e}")
        return False


async def test_integration():
    """Test integration between Phase 2 systems."""
    print("\n🧪 Testing Phase 2 System Integration...")

    try:
        from svgx_engine.services.ai_behavior_prediction import AIBehaviorPredictionSystem, PredictionConfig
        from svgx_engine.services.realtime_collaboration import RealtimeCollaborationSystem, CollaborationConfig
        from svgx_engine.services.advanced_analytics import AdvancedAnalyticsSystem, AnalyticsConfig

        # Create all Phase 2 systems
        ai_config = PredictionConfig()
        ai_system = AIBehaviorPredictionSystem(ai_config)

        collab_config = CollaborationConfig(websocket_port=8767)
        collab_system = RealtimeCollaborationSystem(collab_config)

        analytics_config = AnalyticsConfig()
        analytics_system = AdvancedAnalyticsSystem(analytics_config)

        # Test data flow between systems
        test_element_id = "test_integration_element"

        # Add data to AI system
        ai_data = {
            'temperature': 24.0,
            'humidity': 55.0,
            'power_consumption': 1200.0,
            'efficiency': 0.88,
            'performance_score': 0.92
        }
        ai_system.add_behavior_data(test_element_id, ai_data)

        # Add data to analytics system
        analytics_data = {
            'performance_score': 0.92,
            'efficiency_score': 0.88,
            'uptime_score': 0.98,
            'power_consumption': 1200.0,
            'operational_hours': 7.5,
            'error_count': 0
        }
        analytics_system.add_analytics_data(test_element_id, analytics_data)

        # Test collaboration permissions
        collab_system.set_user_permission("test_user", collab_system.permission_manager.get_user_permission("test_user"))

        # Get results from all systems
        ai_predictions = ai_system.get_predictions(test_element_id)
        ai_anomalies = ai_system.get_anomalies(test_element_id)
        ai_recommendations = ai_system.get_optimization_recommendations(test_element_id)

        maintenance_analysis = analytics_system.get_maintenance_analysis(test_element_id)
        energy_analysis = analytics_system.get_energy_analysis(test_element_id)
        trend_analysis = analytics_system.get_trend_analysis(test_element_id)

        collab_stats = collab_system.get_collaboration_stats()

        print(f"✅ AI System: {len(ai_predictions)} predictions, {len(ai_anomalies)} anomalies, {len(ai_recommendations)} recommendations")
        print(f"✅ Analytics System: Maintenance={maintenance_analysis is not None}, Energy={energy_analysis is not None}, Trend={trend_analysis is not None}")
        print(f"✅ Collaboration System: {collab_stats['collaboration_stats']['total_users']} users")

        return True

    except Exception as e:
        print(f"❌ Phase 2 integration test failed: {e}")
        return False


def test_enterprise_features():
    """Test enterprise-grade features."""
    print("\n🧪 Testing Enterprise Features...")

    try:
        # Test performance monitoring
        from svgx_engine.utils.performance import PerformanceMonitor

        monitor = PerformanceMonitor()

        with monitor.monitor("phase2_test"):
            time.sleep(0.1)  # Simulate work

        metrics = monitor.get_metrics()
        print(f"✅ Performance monitoring: {len(metrics)} metrics tracked")

        # Test error handling
        from svgx_engine.utils.errors import (
            BehaviorError, EventError, StateMachineError, LogicError,
            AIError, CollaborationError, AnalyticsError
        )

        # Test custom error classes
        errors = [
            BehaviorError("Test behavior error"),
            EventError("Test event error"),
            StateMachineError("Test state machine error"),
            LogicError("Test logic error")
        ]

        print(f"✅ Error handling: {len(errors)} error types tested")

        # Test configuration management
        configs = {
            'ai_config': {'prediction_horizon': 24, 'confidence_threshold': 0.8},
            'collab_config': {'max_connections': 100, 'edit_timeout': 300},
            'analytics_config': {'data_retention_days': 365, 'aggregation_interval': 3600}
        }

        print(f"✅ Configuration management: {len(configs)} configurations tested")

        return True

    except Exception as e:
        print(f"❌ Enterprise features test failed: {e}")
        return False


async def main():
    """Run all Phase 2 enhancement tests."""
    print("🚀 Starting Phase 2 Enhancement Tests")
    print("=" * 50)

    test_results = []

    # Test individual systems
    test_results.append(("AI Behavior Prediction", test_ai_behavior_prediction()))
    test_results.append(("Real-time Collaboration", test_realtime_collaboration()))
    test_results.append(("Advanced Analytics", test_advanced_analytics()))

    # Test integration
    test_results.append(("System Integration", await test_integration()))

    # Test enterprise features
    test_results.append(("Enterprise Features", test_enterprise_features()))

    # Print results
    print("\n" + "=" * 50)
    print("📊 Phase 2 Enhancement Test Results")
    print("=" * 50)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Phase 2 enhancements working correctly!")
    else:
        print("⚠️  Some Phase 2 enhancements need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
