import pytest
import asyncio
import json
import time
from datetime import datetime
from fastapi.testclient import TestClient
from svgx_engine.services.api_interface import app
from svgx_engine.services.metrics_collector import metrics_collector
from svgx_engine.services.error_handler import error_handler, ErrorSeverity, ErrorCategory
from svgx_engine.services.health_checker import health_checker
from svgx_engine.runtime.advanced_behavior_engine import AdvancedBehaviorEngine

client = TestClient(app)

class TestComprehensiveSystem:
    """Comprehensive system tests for all SVGX Engine features."""
    
    @pytest.fixture
    def base_event(self):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": "test-session",
            "user_id": "test-user",
            "canvas_id": "test-canvas"
        }
    
    @pytest.fixture
    def engine(self):
        return AdvancedBehaviorEngine()
    
    def test_metrics_collection(self):
        """Test metrics collection functionality."""
        # Reset metrics for clean test
        metrics_collector.reset_metrics()
        
        # Record some test metrics
        metrics_collector.record_counter("test_counter", 1)
        metrics_collector.record_gauge("test_gauge", 42.5)
        metrics_collector.record_histogram("test_histogram", 100.0)
        
        # Get metrics summary
        summary = metrics_collector.get_metrics_summary()
        
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert summary["counters"]["test_counter"] == 1
        assert summary["gauges"]["test_gauge"] == 42.5
        
        # Test Prometheus format export
        prometheus_format = metrics_collector.export_prometheus_format()
        assert "test_counter" in prometheus_format
        assert "test_gauge" in prometheus_format
    
    def test_ui_event_metrics(self):
        """Test UI event metrics recording."""
        metrics_collector.record_ui_event(
            event_type="selection",
            processing_time_ms=50.0,
            success=True,
            canvas_id="test-canvas",
            user_id="test-user"
        )
        
        summary = metrics_collector.get_metrics_summary()
        assert "ui_events_total" in summary["counters"]
        assert "ui_event_processing_time_ms" in summary["histograms"]
    
    def test_error_handling(self):
        """Test comprehensive error handling."""
        # Test error handling with different severities and categories
        error_result = error_handler.handle_error(
            ValueError("Test validation error"),
            context={"test": True},
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION
        )
        
        assert error_result["status"] == "error"
        assert "error_id" in error_result
        assert error_result["severity"] == "medium"
        assert error_result["category"] == "validation"
        assert "suggestions" in error_result
        
        # Test error statistics
        stats = error_handler.get_error_statistics()
        assert "error_counts" in stats
        assert stats["error_counts"]["validation"] >= 1
    
    def test_health_checking(self):
        """Test health checking functionality."""
        # Get current health
        health = health_checker.get_current_health()
        assert "overall_status" in health
        assert "checks" in health
        assert "timestamp" in health
        
        # Test health summary
        summary = health_checker.get_health_summary()
        assert "current_status" in summary
        assert "health_percentage" in summary
        assert "component_status" in summary
        
        # Test health history
        history = health_checker.get_health_history(hours=1)
        assert isinstance(history, list)
    
    def test_collaborative_editing_locks(self, engine):
        """Test collaborative editing with object locking."""
        canvas_id = "test-canvas"
        object_id = "test-object"
        session_id = "session-1"
        user_id = "user-1"
        
        # Test lock acquisition
        lock_result = engine.lock_object(canvas_id, object_id, session_id, user_id)
        assert lock_result["status"] == "lock_acquired"
        assert lock_result["canvas_id"] == canvas_id
        assert lock_result["object_id"] == object_id
        
        # Test lock conflict
        conflict_result = engine.lock_object(canvas_id, object_id, "session-2", "user-2")
        assert conflict_result["status"] == "lock_conflict"
        assert "locked_by" in conflict_result
        
        # Test lock status
        status_result = engine.get_lock_status(canvas_id, object_id)
        assert status_result["status"] == "locked"
        assert "lock_info" in status_result
        
        # Test unlock
        unlock_result = engine.unlock_object(canvas_id, object_id, session_id)
        assert unlock_result["status"] == "lock_released"
        
        # Test unlock denied (wrong session)
        denied_result = engine.unlock_object(canvas_id, object_id, "session-2")
        assert denied_result["status"] == "unlock_denied"
    
    def test_rest_api_endpoints(self, base_event):
        """Test all REST API endpoints."""
        # Test UI event endpoint
        event = {
            **base_event,
            "event_type": "selection",
            "payload": {
                "selection_mode": "single",
                "selected_ids": ["obj001"]
            }
        }
        resp = client.post("/runtime/ui-event/", json=event)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        
        # Test lock endpoint
        lock_data = {
            "canvas_id": "test-canvas",
            "object_id": "test-object",
            "session_id": "test-session",
            "user_id": "test-user"
        }
        resp = client.post("/runtime/lock/", json=lock_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "lock_acquired"
        
        # Test unlock endpoint
        unlock_data = {
            "canvas_id": "test-canvas",
            "object_id": "test-object",
            "session_id": "test-session"
        }
        resp = client.post("/runtime/unlock/", json=unlock_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "lock_released"
        
        # Test lock status endpoint
        resp = client.get("/runtime/lock-status/?canvas_id=test-canvas&object_id=test-object")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
    
    def test_metrics_endpoints(self):
        """Test metrics API endpoints."""
        # Test JSON metrics endpoint
        resp = client.get("/metrics/")
        assert resp.status_code == 200
        data = resp.json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data
        
        # Test Prometheus metrics endpoint
        resp = client.get("/metrics/prometheus")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain"
        content = resp.text
        assert "# TYPE" in content
    
    def test_error_endpoints(self):
        """Test error handling endpoints."""
        # Test error statistics endpoint
        resp = client.get("/errors/stats/")
        assert resp.status_code == 200
        data = resp.json()
        assert "error_counts" in data
        assert "total_errors" in data
    
    def test_health_endpoints(self):
        """Test health check endpoints."""
        # Test current health endpoint
        resp = client.get("/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data
        assert "checks" in data
        
        # Test health summary endpoint
        resp = client.get("/health/summary/")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_status" in data
        assert "health_percentage" in data
        
        # Test health history endpoint
        resp = client.get("/health/history/?hours=1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
    
    def test_error_scenarios(self, base_event):
        """Test various error scenarios."""
        # Test missing event_type
        event = {**base_event}
        resp = client.post("/runtime/ui-event/", json=event)
        assert resp.status_code == 400
        data = resp.json()
        assert data["status"] == "error"
        assert "error_id" in data
        
        # Test missing fields in lock request
        lock_data = {"canvas_id": "test-canvas"}
        resp = client.post("/runtime/lock/", json=lock_data)
        assert resp.status_code == 400
        data = resp.json()
        assert data["status"] == "error"
        assert "error_id" in data
        
        # Test invalid JSON
        resp = client.post("/runtime/ui-event/", data="invalid json")
        assert resp.status_code == 422
    
    def test_performance_metrics(self):
        """Test performance metrics recording."""
        # Record performance metrics
        metrics_collector.record_performance_metric(
            operation="test_operation",
            duration_ms=150.0,
            success=True,
            additional_labels={"test": "true"}
        )
        
        summary = metrics_collector.get_metrics_summary()
        assert "operations_total" in summary["counters"]
        assert "operation_duration_ms" in summary["histograms"]
    
    def test_system_health_metrics(self):
        """Test system health metrics."""
        # Record system health
        metrics_collector.record_system_health(
            component="test_component",
            status="healthy",
            details={"test": "data"}
        )
        
        summary = metrics_collector.get_metrics_summary()
        assert "system_health_status" in summary["gauges"]
        assert "system_health_details" in summary["custom_metrics"]
    
    def test_collaboration_metrics(self):
        """Test collaboration metrics."""
        # Record collaboration metrics
        metrics_collector.record_collaboration_metric(
            action="lock",
            canvas_id="test-canvas",
            user_id="test-user",
            object_id="test-object"
        )
        
        summary = metrics_collector.get_metrics_summary()
        assert "collaboration_actions_total" in summary["counters"]
        assert "collaboration_actions_by_type" in summary["counters"]
    
    def test_undo_redo_functionality(self, engine):
        """Test undo/redo functionality."""
        canvas_id = "test-canvas"
        
        # Perform some edits
        edit_event = {
            "event_type": "editing",
            "payload": {
                "target_id": "obj001",
                "edit_type": "move",
                "before": {"position": {"x": 0, "y": 0}},
                "after": {"position": {"x": 10, "y": 20}}
            }
        }
        engine.handle_ui_event(edit_event)
        
        # Test undo
        undo_result = engine.perform_undo(canvas_id)
        assert undo_result["status"] == "success"
        assert "edit_history" in undo_result
        
        # Test redo
        redo_result = engine.perform_redo(canvas_id)
        assert redo_result["status"] == "success"
    
    def test_annotation_crud(self, engine):
        """Test annotation CRUD operations."""
        canvas_id = "test-canvas"
        target_id = "obj001"
        
        # Test annotation update
        update_result = engine.update_annotation(
            canvas_id, target_id, 0, {"content": "Updated annotation"}
        )
        assert update_result["status"] == "success"
        
        # Test annotation delete
        delete_result = engine.delete_annotation(canvas_id, target_id, 0)
        assert delete_result["status"] == "success"
    
    def test_telemetry_integration(self, base_event):
        """Test telemetry integration with UI events."""
        # This would test the telemetry instrumentation decorators
        # that are applied to the behavior engine methods
        event = {
            **base_event,
            "event_type": "selection",
            "payload": {
                "selection_mode": "single",
                "selected_ids": ["obj001"]
            }
        }
        
        # The telemetry should be automatically recorded
        # when the event is processed
        resp = client.post("/runtime/ui-event/", json=event)
        assert resp.status_code == 200
        
        # Check that metrics were recorded
        summary = metrics_collector.get_metrics_summary()
        assert "ui_events_total" in summary["counters"]
    
    def test_comprehensive_error_recovery(self):
        """Test error recovery procedures."""
        # Test different error categories and their recovery
        categories = [
            ErrorCategory.VALIDATION,
            ErrorCategory.CONFLICT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.TIMEOUT,
            ErrorCategory.NETWORK
        ]
        
        for category in categories:
            error_result = error_handler.handle_error(
                Exception(f"Test {category.value} error"),
                severity=ErrorSeverity.MEDIUM,
                category=category
            )
            
            assert error_result["status"] == "error"
            assert error_result["category"] == category.value
            assert "recovery_attempted" in error_result
            assert "recovery_successful" in error_result
    
    def test_health_check_registration(self):
        """Test custom health check registration."""
        def custom_health_check():
            return {
                "status": "healthy",
                "message": "Custom health check OK",
                "details": {"custom": True},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        health_checker.register_health_check("custom_check", custom_health_check)
        
        # Run health checks
        health = health_checker.run_health_checks()
        assert "custom_check" in health["checks"]
        assert health["checks"]["custom_check"]["status"] == "healthy"
    
    def test_metrics_reset_functionality(self):
        """Test metrics reset functionality."""
        # Record some metrics
        metrics_collector.record_counter("test_reset", 1)
        
        # Verify metric exists
        summary = metrics_collector.get_metrics_summary()
        assert "test_reset" in summary["counters"]
        
        # Reset metrics
        metrics_collector.reset_metrics()
        
        # Verify metric is gone
        summary = metrics_collector.get_metrics_summary()
        assert "test_reset" not in summary["counters"]
    
    def test_error_handler_reset(self):
        """Test error handler reset functionality."""
        # Generate some errors
        error_handler.handle_error(
            ValueError("Test error"),
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION
        )
        
        # Verify errors were recorded
        stats = error_handler.get_error_statistics()
        assert stats["total_errors"] > 0
        
        # Reset error counts
        error_handler.reset_error_counts()
        
        # Verify reset
        stats = error_handler.get_error_statistics()
        assert stats["total_errors"] == 0

if __name__ == "__main__":
    pytest.main([__file__]) 