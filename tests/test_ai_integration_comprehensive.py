#!/usr/bin/env python3
"""
Comprehensive test suite for AI Integration Features
Tests user pattern learning, AI frontend integration, and advanced AI analytics
"""

import unittest
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Import AI services
from svgx_engine.services.ai.user_pattern_learning import (
    UserPatternLearningService,
    UserAction,
    UserSession,
    UserPattern,
    UserPreference,
    UserRecommendation,
    UserAnalytics,
)
from svgx_engine.services.ai.ai_frontend_integration import (
    AIFrontendIntegrationService,
    HTMXRequest,
    HTMXResponse,
    AIComponent,
    SmartFormField,
    IntelligentSearch,
    AIAssistant,
)
from svgx_engine.services.ai.advanced_ai_analytics import (
    AdvancedAIAnalyticsService,
    AnalyticsDataset,
    PredictionResult,
    TrendAnalysis,
    CorrelationAnalysis,
    AnomalyDetection,
    Insight,
    PerformanceMetrics,
)


class TestUserPatternLearning(unittest.TestCase):
    """Test user pattern learning functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = UserPatternLearningService()
        self.user_id = "test_user_123"
        self.session_id = "session_456"

    def test_record_user_action(self):
        """Test recording user actions"""
        # Test basic action recording
        action = self.service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="view",
            resource="/dashboard",
            context={
                "page_url": "https://example.com/dashboard",
                "user_agent": "Mozilla/5.0",
                "screen_size": "1920x1080",
            },
        )

        self.assertIsNotNone(action)
        self.assertEqual(action.user_id, self.user_id)
        self.assertEqual(action.session_id, self.session_id)
        self.assertEqual(action.action_type, "view")
        self.assertEqual(action.resource, "/dashboard")

        # Test action with metadata
        action_with_meta = self.service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="create",
            resource="/projects",
            context={"page_url": "https://example.com/projects"},
            duration=5000,
            metadata={"project_type": "cad", "complexity": "high"},
        )

        self.assertIsNotNone(action_with_meta)
        self.assertEqual(action_with_meta.duration, 5000)
        self.assertEqual(action_with_meta.metadata["project_type"], "cad")

    def test_manage_user_session(self):
        """Test user session management"""
        # Start session
        session = self.service.start_user_session(
            user_id=self.user_id, device_info="Desktop Chrome", location="New York"
        )

        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, self.user_id)
        self.assertIsNone(session.end_time)

        # End session
        ended_session = self.service.end_user_session(session.id)
        self.assertIsNotNone(ended_session.end_time)
        self.assertGreater(ended_session.duration, 0)

    def test_analyze_frequency_patterns(self):
        """Test frequency pattern analysis"""
        # Record multiple actions
        for i in range(10):
            self.service.record_user_action(
                user_id=self.user_id,
                session_id=self.session_id,
                action_type="view",
                resource="/dashboard",
            )

        for i in range(5):
            self.service.record_user_action(
                user_id=self.user_id,
                session_id=self.session_id,
                action_type="edit",
                resource="/projects",
            )

        patterns = self.service.analyze_frequency_patterns(self.user_id)
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)

        # Check dashboard pattern
        dashboard_pattern = next(
            (p for p in patterns if "dashboard" in p.pattern), None
        )
        self.assertIsNotNone(dashboard_pattern)
        self.assertEqual(dashboard_pattern.frequency, 10)

    def test_analyze_sequence_patterns(self):
        """Test sequence pattern analysis"""
        # Record sequential actions
        actions = [
            ("view", "/dashboard"),
            ("click", "/projects"),
            ("view", "/projects"),
            ("create", "/projects/new"),
            ("view", "/dashboard"),
            ("click", "/projects"),
            ("view", "/projects"),
        ]

        for action_type, resource in actions:
            self.service.record_user_action(
                user_id=self.user_id,
                session_id=self.session_id,
                action_type=action_type,
                resource=resource,
            )

        patterns = self.service.analyze_sequence_patterns(self.user_id)
        self.assertIsInstance(patterns, list)

    def test_analyze_timing_patterns(self):
        """Test timing pattern analysis"""
        # Record actions with timing
        self.service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="view",
            resource="/dashboard",
        )

        time.sleep(0.1)  # Simulate time gap

        self.service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="edit",
            resource="/projects",
        )

        patterns = self.service.analyze_timing_patterns(self.user_id)
        self.assertIsInstance(patterns, list)

    def test_analyze_preference_patterns(self):
        """Test preference pattern analysis"""
        # Record actions with different contexts
        contexts = [
            {"theme": "dark", "language": "en"},
            {"theme": "dark", "language": "en"},
            {"theme": "light", "language": "es"},
            {"theme": "dark", "language": "en"},
        ]

        for context in contexts:
            self.service.record_user_action(
                user_id=self.user_id,
                session_id=self.session_id,
                action_type="view",
                resource="/dashboard",
                context=context,
            )

        patterns = self.service.analyze_preference_patterns(self.user_id)
        self.assertIsInstance(patterns, list)

    def test_generate_recommendations(self):
        """Test recommendation generation"""
        # Record some actions first
        self.service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="view",
            resource="/dashboard",
        )

        recommendations = self.service.generate_recommendations(self.user_id)
        self.assertIsInstance(recommendations, list)

    def test_update_user_analytics(self):
        """Test user analytics updates"""
        # Record actions to generate analytics
        for i in range(5):
            self.service.record_user_action(
                user_id=self.user_id,
                session_id=self.session_id,
                action_type="view",
                resource=f"/page_{i}",
            )

        analytics = self.service.update_user_analytics(self.user_id)
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.user_id, self.user_id)
        self.assertGreater(analytics.total_actions, 0)


class TestAIFrontendIntegration(unittest.TestCase):
    """Test AI frontend integration functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = AIFrontendIntegrationService()
        self.user_id = "test_user_123"
        self.session_id = "session_456"

    def test_process_htmx_request(self):
        """Test HTMX request processing"""
        request = HTMXRequest(
            event_type="click",
            target="#submit-btn",
            trigger="click",
            user_id=self.user_id,
            session_id=self.session_id,
            data={"form_data": "test"},
            context={
                "page_url": "https://example.com/form",
                "user_agent": "Mozilla/5.0",
            },
        )

        response = self.service.process_htmx_request(request)
        self.assertIsInstance(response, HTMXResponse)
        self.assertIsNotNone(response.html)
        self.assertIsNotNone(response.javascript)

    def test_handle_smart_form(self):
        """Test smart form handling"""
        form_data = {
            "fields": [
                {"name": "project_name", "type": "text", "value": "Test Project"},
                {
                    "name": "description",
                    "type": "textarea",
                    "value": "Test description",
                },
            ]
        }

        response = self.service.handle_smart_form(
            user_id=self.user_id,
            form_data=form_data,
            context={"page_url": "https://example.com/form"},
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("form", response.html.lower())

    def test_handle_intelligent_search(self):
        """Test intelligent search handling"""
        search_data = {
            "query": "cad project",
            "filters": {"category": "design"},
            "sort_by": "relevance",
        }

        response = self.service.handle_intelligent_search(
            user_id=self.user_id,
            search_data=search_data,
            context={"page_url": "https://example.com/search"},
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("search", response.html.lower())

    def test_handle_context_suggestions(self):
        """Test context suggestions handling"""
        context = {
            "current_page": "/projects",
            "recent_actions": ["view", "edit"],
            "user_preferences": {"theme": "dark"},
        }

        response = self.service.handle_context_suggestions(
            user_id=self.user_id, context=context
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIsNotNone(response.html)

    def test_handle_adaptive_navigation(self):
        """Test adaptive navigation handling"""
        navigation_context = {
            "current_page": "/dashboard",
            "user_patterns": ["frequent_dashboard", "project_creation"],
            "recent_pages": ["/projects", "/settings"],
        }

        response = self.service.handle_adaptive_navigation(
            user_id=self.user_id, navigation_context=navigation_context
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("nav", response.html.lower())

    def test_handle_personalized_dashboard(self):
        """Test personalized dashboard handling"""
        dashboard_data = {
            "user_id": self.user_id,
            "preferences": {"widgets": ["recent_projects", "activity_feed"]},
            "recent_activity": ["project_created", "file_edited"],
        }

        response = self.service.handle_personalized_dashboard(
            user_id=self.user_id, dashboard_data=dashboard_data
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("dashboard", response.html.lower())

    def test_handle_ai_assistant(self):
        """Test AI assistant handling"""
        assistant_data = {
            "message": "Help me create a new CAD project",
            "context": "user is on project creation page",
            "user_history": ["frequent_project_creation"],
        }

        response = self.service.handle_ai_assistant(
            user_id=self.user_id, assistant_data=assistant_data
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIsNotNone(response.html)

    def test_handle_recommendation_widget(self):
        """Test recommendation widget handling"""
        recommendations = [
            {"type": "feature", "title": "Try 3D modeling", "confidence": 0.85},
            {"type": "project", "title": "Create assembly", "confidence": 0.72},
        ]

        response = self.service.handle_recommendation_widget(
            user_id=self.user_id, recommendations=recommendations
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("recommendation", response.html.lower())

    def test_handle_predictive_input(self):
        """Test predictive input handling"""
        input_data = {
            "field_name": "project_name",
            "current_value": "Test",
            "user_history": ["Test Project 1", "Test Project 2"],
            "context": "project creation form",
        }

        response = self.service.handle_predictive_input(
            user_id=self.user_id, input_data=input_data
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIsNotNone(response.html)

    def test_handle_smart_table(self):
        """Test smart table handling"""
        table_data = {
            "data": [
                {"id": 1, "name": "Project A", "status": "active"},
                {"id": 2, "name": "Project B", "status": "completed"},
            ],
            "columns": ["id", "name", "status"],
            "user_preferences": {"sort_by": "name", "filter": "active"},
        }

        response = self.service.handle_smart_table(
            user_id=self.user_id, table_data=table_data
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("table", response.html.lower())

    def test_handle_intelligent_chart(self):
        """Test intelligent chart handling"""
        chart_data = {
            "chart_type": "line",
            "data": [
                {"date": "2024-01-01", "value": 10},
                {"date": "2024-01-02", "value": 15},
            ],
            "user_preferences": {"theme": "dark", "show_trends": True},
        }

        response = self.service.handle_intelligent_chart(
            user_id=self.user_id, chart_data=chart_data
        )

        self.assertIsInstance(response, HTMXResponse)
        self.assertIn("chart", response.html.lower())


class TestAdvancedAIAnalytics(unittest.TestCase):
    """Test advanced AI analytics functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = AdvancedAIAnalyticsService()
        self.user_id = "test_user_123"

    def test_create_analytics_dataset(self):
        """Test creating analytics datasets"""
        data = [
            {"user_id": "user1", "action": "view", "timestamp": "2024-01-01T10:00:00"},
            {"user_id": "user2", "action": "edit", "timestamp": "2024-01-01T11:00:00"},
        ]

        dataset = self.service.create_analytics_dataset(
            name="User Actions",
            dataset_type="user_behavior",
            description="User action patterns",
            data=data,
            schema={"user_id": "string", "action": "string", "timestamp": "datetime"},
        )

        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.name, "User Actions")
        self.assertEqual(dataset.type, "user_behavior")
        self.assertEqual(len(dataset.data), 2)

    def test_predict_user_behavior(self):
        """Test user behavior prediction"""
        input_data = {
            "user_id": self.user_id,
            "recent_actions": ["view", "edit", "create"],
            "session_duration": 1800,
            "page_views": 15,
        }

        result = self.service.predict_user_behavior(
            user_id=self.user_id,
            model_type="linear_regression",
            input_data=input_data,
            horizon=7,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.model_id, "linear_regression")
        self.assertIsNotNone(result.output)
        self.assertGreater(result.confidence, 0)

    def test_analyze_trends(self):
        """Test trend analysis"""
        # Create dataset first
        data = [
            {"date": "2024-01-01", "value": 10},
            {"date": "2024-01-02", "value": 12},
            {"date": "2024-01-03", "value": 15},
        ]

        dataset = self.service.create_analytics_dataset(
            name="Trend Data",
            dataset_type="trend_analysis",
            description="Test trend data",
            data=data,
        )

        analysis = self.service.analyze_trends(
            dataset_id=dataset.id, metric="value", period="daily", confidence=0.95
        )

        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.dataset_id, dataset.id)
        self.assertEqual(analysis.metric, "value")
        self.assertIsNotNone(analysis.trend)

    def test_analyze_correlations(self):
        """Test correlation analysis"""
        # Create dataset with multiple variables
        data = [
            {"user_id": "user1", "session_duration": 1800, "page_views": 15},
            {"user_id": "user2", "session_duration": 3600, "page_views": 30},
            {"user_id": "user3", "session_duration": 900, "page_views": 8},
        ]

        dataset = self.service.create_analytics_dataset(
            name="Correlation Data",
            dataset_type="correlation_analysis",
            description="Test correlation data",
            data=data,
        )

        analysis = self.service.analyze_correlations(
            dataset_id=dataset.id, variable1="session_duration", variable2="page_views"
        )

        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.dataset_id, dataset.id)
        self.assertEqual(analysis.variable1, "session_duration")
        self.assertEqual(analysis.variable2, "page_views")
        self.assertIsNotNone(analysis.correlation)

    def test_detect_anomalies(self):
        """Test anomaly detection"""
        # Create dataset with potential anomalies
        data = [
            {"timestamp": "2024-01-01T10:00:00", "value": 10},
            {"timestamp": "2024-01-01T11:00:00", "value": 12},
            {"timestamp": "2024-01-01T12:00:00", "value": 100},  # Anomaly
            {"timestamp": "2024-01-01T13:00:00", "value": 11},
        ]

        dataset = self.service.create_analytics_dataset(
            name="Anomaly Data",
            dataset_type="anomaly_detection",
            description="Test anomaly data",
            data=data,
        )

        detection = self.service.detect_anomalies(
            dataset_id=dataset.id, metric="value", threshold=2.0, window_size=5
        )

        self.assertIsNotNone(detection)
        self.assertEqual(detection.dataset_id, dataset.id)
        self.assertEqual(detection.metric, "value")

    def test_generate_ai_insights(self):
        """Test AI insights generation"""
        insights = self.service.generate_ai_insights(
            user_id=self.user_id,
            categories=["usage_pattern", "performance_optimization"],
            limit=5,
            confidence=0.8,
        )

        self.assertIsInstance(insights, list)
        self.assertLessEqual(len(insights), 5)

        for insight in insights:
            self.assertIsInstance(insight, Insight)
            self.assertGreater(insight.confidence, 0.8)

    def test_track_performance_metrics(self):
        """Test performance metrics tracking"""
        metrics = self.service.track_performance_metrics(
            category="system_performance",
            metric="response_time",
            value=150.5,
            unit="ms",
            threshold=200.0,
            metadata={"endpoint": "/api/projects", "method": "GET"},
        )

        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.category, "system_performance")
        self.assertEqual(metrics.metric, "response_time")
        self.assertEqual(metrics.value, 150.5)
        self.assertEqual(metrics.unit, "ms")

    def test_get_analytics_summary(self):
        """Test analytics summary generation"""
        # Create some test data first
        self.service.create_analytics_dataset(
            name="Test Dataset",
            dataset_type="user_behavior",
            description="Test data",
            data=[{"test": "data"}],
        )

        summary = self.service.get_analytics_summary()
        self.assertIsNotNone(summary)
        self.assertIn("datasets_count", summary)
        self.assertIn("predictions_count", summary)
        self.assertIn("insights_count", summary)


class TestAIIntegration(unittest.TestCase):
    """Test AI integration end-to-end functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.pattern_service = UserPatternLearningService()
        self.frontend_service = AIFrontendIntegrationService()
        self.analytics_service = AdvancedAIAnalyticsService()
        self.user_id = "integration_test_user"
        self.session_id = "integration_session"

    def test_end_to_end_ai_workflow(self):
        """Test complete AI integration workflow"""
        # 1. Record user actions
        self.pattern_service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="view",
            resource="/dashboard",
        )

        self.pattern_service.record_user_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="click",
            resource="/projects",
        )

        # 2. Generate recommendations
        recommendations = self.pattern_service.generate_recommendations(self.user_id)
        self.assertIsInstance(recommendations, list)

        # 3. Process HTMX request with AI
        htmx_request = HTMXRequest(
            event_type="click",
            target="#recommendation-btn",
            trigger="click",
            user_id=self.user_id,
            session_id=self.session_id,
            data={
                "recommendation_id": (
                    recommendations[0].id if recommendations else "test"
                )
            },
            context={"page_url": "https://example.com/dashboard"},
        )

        htmx_response = self.frontend_service.process_htmx_request(htmx_request)
        self.assertIsInstance(htmx_response, HTMXResponse)

        # 4. Create analytics dataset
        analytics_data = [
            {
                "user_id": self.user_id,
                "action": "view",
                "timestamp": "2024-01-01T10:00:00",
            },
            {
                "user_id": self.user_id,
                "action": "click",
                "timestamp": "2024-01-01T10:05:00",
            },
        ]

        dataset = self.analytics_service.create_analytics_dataset(
            name="Integration Test",
            dataset_type="user_behavior",
            description="End-to-end test data",
            data=analytics_data,
        )

        # 5. Generate insights
        insights = self.analytics_service.generate_ai_insights(
            user_id=self.user_id, categories=["usage_pattern"], limit=3
        )

        self.assertIsInstance(insights, list)

        # 6. Track performance
        metrics = self.analytics_service.track_performance_metrics(
            category="ai_integration",
            metric="workflow_completion_time",
            value=2.5,
            unit="seconds",
        )

        self.assertIsNotNone(metrics)

        # Verify integration worked
        self.assertGreater(len(recommendations), 0)
        self.assertIsNotNone(htmx_response.html)
        self.assertIsNotNone(dataset.id)
        self.assertGreater(len(insights), 0)
        self.assertIsNotNone(metrics.id)


if __name__ == "__main__":
    # Run comprehensive tests
    unittest.main(verbosity=2)
