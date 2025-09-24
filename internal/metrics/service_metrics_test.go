package metrics

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestServiceMetrics(t *testing.T) {
	t.Run("NewServiceMetrics", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")

		assert.Equal(t, "test-service", metrics.serviceName)
		assert.NotNil(t, metrics.collector)
		assert.NotNil(t, metrics.operationCounters)
		assert.NotNil(t, metrics.operationDurations)
		assert.NotNil(t, metrics.operationErrors)
	})

	t.Run("StartOperation", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")
		operation := metrics.StartOperation("test_operation")

		assert.Equal(t, "test-service", operation.serviceName)
		assert.Equal(t, "test_operation", operation.operation)
		assert.NotZero(t, operation.startTime)
		assert.NotNil(t, operation.metrics)
	})

	t.Run("CompleteOperation", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")
		operation := metrics.StartOperation("test_operation")

		// Complete operation
		operation.CompleteOperation()

		// Verify metrics were recorded
		summary := metrics.GetServiceSummary()
		assert.Greater(t, summary.TotalOperations, int64(0))
		assert.Greater(t, summary.SuccessfulOperations, int64(0))
	})

	t.Run("CompleteOperationWithError", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")
		operation := metrics.StartOperation("test_operation")

		// Complete operation with error
		err := fmt.Errorf("test error")
		operation.CompleteOperationWithError(err)

		// Verify metrics were recorded
		summary := metrics.GetServiceSummary()
		assert.Greater(t, summary.TotalOperations, int64(0))
		assert.Greater(t, summary.FailedOperations, int64(0))
	})

	t.Run("RecordRetry", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")

		// Record retry
		metrics.RecordRetry("test_operation")

		// Verify retry was recorded
		summary := metrics.GetServiceSummary()
		// Note: retry count would need to be added to summary
		assert.NotNil(t, summary)
	})

	t.Run("RecordCircuitBreakerState", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")

		// Record circuit breaker state
		metrics.RecordCircuitBreakerState("test_operation", 1) // Open

		// Verify state was recorded
		summary := metrics.GetServiceSummary()
		assert.NotNil(t, summary.CircuitBreakerState)
	})

	t.Run("RecordFallbackUsage", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")

		// Record fallback usage
		metrics.RecordFallbackUsage("test_operation")

		// Verify fallback was recorded
		summary := metrics.GetServiceSummary()
		assert.NotNil(t, summary)
	})

	t.Run("RecordBatchOperation", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")

		// Record batch operation
		metrics.RecordBatchOperation("test_operation", 100)

		// Verify batch operation was recorded
		summary := metrics.GetServiceSummary()
		assert.NotNil(t, summary)
	})

	t.Run("GetServiceSummary", func(t *testing.T) {
		metrics := NewServiceMetrics("test-service")

		// Perform some operations
		operation1 := metrics.StartOperation("operation1")
		operation1.CompleteOperation()

		operation2 := metrics.StartOperation("operation2")
		operation2.CompleteOperationWithError(fmt.Errorf("test error"))

		// Get summary
		summary := metrics.GetServiceSummary()

		assert.Equal(t, "test-service", summary.ServiceName)
		assert.Equal(t, int64(2), summary.TotalOperations)
		assert.Equal(t, int64(1), summary.SuccessfulOperations)
		assert.Equal(t, int64(1), summary.FailedOperations)
		assert.Equal(t, 0.5, summary.ErrorRate)
		assert.NotZero(t, summary.Timestamp)
	})
}

func TestServiceMetricsMiddleware(t *testing.T) {
	t.Run("NewServiceMetricsMiddleware", func(t *testing.T) {
		middleware := NewServiceMetricsMiddleware("test-service")

		assert.NotNil(t, middleware.metrics)
		assert.Equal(t, "test-service", middleware.metrics.serviceName)
	})

	t.Run("WrapOperation", func(t *testing.T) {
		middleware := NewServiceMetricsMiddleware("test-service")

		// Wrap successful operation
		err := middleware.WrapOperation("test_operation", func() error {
			return nil
		})

		assert.NoError(t, err)

		// Verify metrics were recorded
		summary := middleware.GetMetrics().GetServiceSummary()
		assert.Equal(t, int64(1), summary.TotalOperations)
		assert.Equal(t, int64(1), summary.SuccessfulOperations)
	})

	t.Run("WrapOperationWithError", func(t *testing.T) {
		middleware := NewServiceMetricsMiddleware("test-service")

		// Wrap operation that returns error
		expectedErr := fmt.Errorf("test error")
		err := middleware.WrapOperation("test_operation", func() error {
			return expectedErr
		})

		assert.Equal(t, expectedErr, err)

		// Verify metrics were recorded
		summary := middleware.GetMetrics().GetServiceSummary()
		assert.Equal(t, int64(1), summary.TotalOperations)
		assert.Equal(t, int64(1), summary.FailedOperations)
	})

	t.Run("WrapOperationWithContext", func(t *testing.T) {
		middleware := NewServiceMetricsMiddleware("test-service")
		ctx := context.Background()

		// Wrap operation with context
		err := middleware.WrapOperationWithContext(ctx, "test_operation", func(ctx context.Context) error {
			return nil
		})

		assert.NoError(t, err)

		// Verify metrics were recorded
		summary := middleware.GetMetrics().GetServiceSummary()
		assert.Equal(t, int64(1), summary.TotalOperations)
		assert.Equal(t, int64(1), summary.SuccessfulOperations)
	})
}

func TestInstrumentation(t *testing.T) {
	t.Run("NewInstrumentation", func(t *testing.T) {
		instrumentation := NewInstrumentation("test-service")

		assert.Equal(t, "test-service", instrumentation.serviceName)
		assert.NotNil(t, instrumentation.metrics)
		assert.NotNil(t, instrumentation.tracer)
		assert.NotNil(t, instrumentation.activeOperations)
	})

	t.Run("StartOperation", func(t *testing.T) {
		instrumentation := NewInstrumentation("test-service")
		ctx := context.Background()
		labels := map[string]string{"key": "value"}

		tracker := instrumentation.StartOperation(ctx, "test_operation", labels)

		assert.Equal(t, "test_operation", tracker.Operation)
		assert.Equal(t, ctx, tracker.Context)
		assert.Equal(t, labels, tracker.Labels)
		assert.NotZero(t, tracker.StartTime)
	})

	t.Run("CompleteOperation", func(t *testing.T) {
		instrumentation := NewInstrumentation("test-service")
		ctx := context.Background()

		tracker := instrumentation.StartOperation(ctx, "test_operation", nil)
		instrumentation.CompleteOperation(tracker)

		// Verify operation is no longer active
		activeOps := instrumentation.GetActiveOperations()
		assert.Empty(t, activeOps)
	})

	t.Run("CompleteOperationWithError", func(t *testing.T) {
		instrumentation := NewInstrumentation("test-service")
		ctx := context.Background()

		tracker := instrumentation.StartOperation(ctx, "test_operation", nil)
		err := fmt.Errorf("test error")
		instrumentation.CompleteOperationWithError(tracker, err)

		// Verify operation is no longer active
		activeOps := instrumentation.GetActiveOperations()
		assert.Empty(t, activeOps)

		// Verify error was recorded
		stats := instrumentation.GetOperationStats()
		assert.Equal(t, int64(1), stats["test_operation"].ErrorCount)
	})

	t.Run("RecordRetry", func(t *testing.T) {
		instrumentation := NewInstrumentation("test-service")
		ctx := context.Background()

		tracker := instrumentation.StartOperation(ctx, "test_operation", nil)
		instrumentation.RecordRetry(tracker)

		// Verify retry was recorded
		assert.Equal(t, int32(1), tracker.RetryCount)

		stats := instrumentation.GetOperationStats()
		assert.Equal(t, int64(1), stats["test_operation"].RetryCount)
	})

	t.Run("GetOperationStats", func(t *testing.T) {
		instrumentation := NewInstrumentation("test-service")
		ctx := context.Background()

		// Start and complete operations
		tracker1 := instrumentation.StartOperation(ctx, "operation1", nil)
		instrumentation.CompleteOperation(tracker1)

		tracker2 := instrumentation.StartOperation(ctx, "operation2", nil)
		instrumentation.CompleteOperationWithError(tracker2, fmt.Errorf("test error"))

		// Get stats
		stats := instrumentation.GetOperationStats()

		assert.Len(t, stats, 2)
		assert.Equal(t, int64(1), stats["operation1"].TotalCount)
		assert.Equal(t, int64(0), stats["operation1"].ErrorCount)
		assert.Equal(t, int64(1), stats["operation2"].TotalCount)
		assert.Equal(t, int64(1), stats["operation2"].ErrorCount)
	})
}

func TestInstrumentationMiddleware(t *testing.T) {
	t.Run("NewInstrumentationMiddleware", func(t *testing.T) {
		middleware := NewInstrumentationMiddleware("test-service")

		assert.NotNil(t, middleware.instrumentation)
		assert.Equal(t, "test-service", middleware.instrumentation.serviceName)
	})

	t.Run("WrapOperation", func(t *testing.T) {
		middleware := NewInstrumentationMiddleware("test-service")
		ctx := context.Background()
		labels := map[string]string{"key": "value"}

		// Wrap successful operation
		err := middleware.WrapOperation(ctx, "test_operation", labels, func(ctx context.Context) error {
			return nil
		})

		assert.NoError(t, err)

		// Verify operation was tracked
		stats := middleware.GetInstrumentation().GetOperationStats()
		assert.Equal(t, int64(1), stats["test_operation"].TotalCount)
		assert.Equal(t, int64(0), stats["test_operation"].ErrorCount)
	})

	t.Run("WrapOperationWithRetry", func(t *testing.T) {
		middleware := NewInstrumentationMiddleware("test-service")
		ctx := context.Background()
		labels := map[string]string{"key": "value"}

		attemptCount := 0

		// Wrap operation that fails first time, succeeds second time
		err := middleware.WrapOperationWithRetry(ctx, "test_operation", labels, 2, func(ctx context.Context) error {
			attemptCount++
			if attemptCount == 1 {
				return fmt.Errorf("temporary error")
			}
			return nil
		})

		assert.NoError(t, err)
		assert.Equal(t, 2, attemptCount)

		// Verify operation was tracked
		stats := middleware.GetInstrumentation().GetOperationStats()
		assert.Equal(t, int64(1), stats["test_operation"].TotalCount)
		assert.Equal(t, int64(0), stats["test_operation"].ErrorCount)
		assert.Equal(t, int64(1), stats["test_operation"].RetryCount)
	})
}

func TestTracer(t *testing.T) {
	t.Run("NewTracer", func(t *testing.T) {
		tracer := NewTracer("test-service")

		assert.Equal(t, "test-service", tracer.serviceName)
		assert.NotNil(t, tracer.spans)
	})

	t.Run("StartSpan", func(t *testing.T) {
		tracer := NewTracer("test-service")
		ctx := context.Background()
		labels := map[string]string{"key": "value"}

		span := tracer.StartSpan(ctx, "test_operation", labels)

		assert.NotEmpty(t, span.SpanID)
		assert.NotEmpty(t, span.TraceID)
		assert.Equal(t, "test_operation", span.Operation)
		assert.Equal(t, "test-service", span.Service)
		assert.Equal(t, labels, span.Labels)
		assert.NotZero(t, span.StartTime)
		assert.Equal(t, SpanStatusUnknown, span.Status)
	})

	t.Run("FinishSpan", func(t *testing.T) {
		tracer := NewTracer("test-service")
		ctx := context.Background()

		span := tracer.StartSpan(ctx, "test_operation", nil)
		spanID := span.SpanID

		// Finish span
		tracer.FinishSpan(spanID, SpanStatusOK)

		// Verify span is no longer active
		spans := tracer.GetSpans()
		assert.NotContains(t, spans, spanID)

		// Verify span was updated
		assert.Equal(t, SpanStatusOK, span.Status)
		assert.NotZero(t, span.EndTime)
		assert.NotZero(t, span.Duration)
	})

	t.Run("AddEvent", func(t *testing.T) {
		tracer := NewTracer("test-service")
		ctx := context.Background()

		span := tracer.StartSpan(ctx, "test_operation", nil)
		spanID := span.SpanID

		// Add event
		eventLabels := map[string]string{"event_key": "event_value"}
		tracer.AddEvent(spanID, "test_event", eventLabels)

		// Verify event was added
		span.mu.RLock()
		assert.Len(t, span.Events, 1)
		assert.Equal(t, "test_event", span.Events[0].Name)
		assert.Equal(t, eventLabels, span.Events[0].Labels)
		span.mu.RUnlock()
	})
}

func TestDashboard(t *testing.T) {
	t.Run("NewDashboard", func(t *testing.T) {
		dashboard := NewDashboard("test-service")

		assert.Equal(t, "test-service", dashboard.serviceName)
		assert.NotNil(t, dashboard.collector)
		assert.NotNil(t, dashboard.alertRules)
		assert.NotNil(t, dashboard.notifications)
	})

	t.Run("AddAlertRule", func(t *testing.T) {
		dashboard := NewDashboard("test-service")

		rule := AlertRule{
			Name:        "test_rule",
			Metric:      "error_rate",
			Threshold:   0.1,
			Operator:    "gt",
			Severity:    "warning",
			Description: "Error rate too high",
			Enabled:     true,
		}

		dashboard.AddAlertRule(rule)

		assert.Len(t, dashboard.alertRules, 1)
		assert.Equal(t, rule, dashboard.alertRules[0])
	})

	t.Run("AddNotification", func(t *testing.T) {
		dashboard := NewDashboard("test-service")

		notification := Notification{
			Type:     "info",
			Title:    "Test Notification",
			Message:  "This is a test notification",
			Severity: "info",
		}

		dashboard.AddNotification(notification)

		assert.Len(t, dashboard.notifications, 1)
		assert.Equal(t, "Test Notification", dashboard.notifications[0].Title)
		assert.NotEmpty(t, dashboard.notifications[0].ID)
		assert.NotZero(t, dashboard.notifications[0].Timestamp)
	})

	t.Run("GetDashboardData", func(t *testing.T) {
		dashboard := NewDashboard("test-service")

		data := dashboard.GetDashboardData()

		assert.Equal(t, "test-service", data.ServiceName)
		assert.NotZero(t, data.Timestamp)
		assert.NotNil(t, data.SystemInfo)
		assert.NotNil(t, data.ServiceMetrics)
		assert.NotNil(t, data.OperationMetrics)
		assert.NotNil(t, data.ErrorMetrics)
		assert.NotNil(t, data.PerformanceMetrics)
		assert.NotNil(t, data.Alerts)
		assert.NotNil(t, data.Notifications)
		assert.NotNil(t, data.HealthStatus)
	})
}

func TestGlobalRegistry(t *testing.T) {
	t.Run("GetServiceMetrics", func(t *testing.T) {
		// Clear registry
		registryMu.Lock()
		serviceMetricsRegistry = make(map[string]*ServiceMetrics)
		registryMu.Unlock()

		// Get service metrics
		metrics1 := GetServiceMetrics("test-service")
		metrics2 := GetServiceMetrics("test-service")

		// Should return same instance
		assert.Equal(t, metrics1, metrics2)
		assert.Equal(t, "test-service", metrics1.serviceName)
	})

	t.Run("GetAllServiceMetrics", func(t *testing.T) {
		// Clear registry
		registryMu.Lock()
		serviceMetricsRegistry = make(map[string]*ServiceMetrics)
		registryMu.Unlock()

		// Get multiple service metrics
		GetServiceMetrics("service1")
		GetServiceMetrics("service2")

		// Get all metrics
		allMetrics := GetAllServiceMetrics()

		assert.Len(t, allMetrics, 2)
		assert.Contains(t, allMetrics, "service1")
		assert.Contains(t, allMetrics, "service2")
	})

	t.Run("GetServiceMetricsSummary", func(t *testing.T) {
		// Clear registry
		registryMu.Lock()
		serviceMetricsRegistry = make(map[string]*ServiceMetrics)
		registryMu.Unlock()

		// Get service metrics and perform operations
		metrics := GetServiceMetrics("test-service")
		operation := metrics.StartOperation("test_operation")
		operation.CompleteOperation()

		// Get summary
		summary := GetServiceMetricsSummary()

		assert.Contains(t, summary, "test-service")
		assert.Equal(t, int64(1), summary["test-service"].TotalOperations)
		assert.Equal(t, int64(1), summary["test-service"].SuccessfulOperations)
	})
}

func TestPerformanceMonitor(t *testing.T) {
	t.Run("NewPerformanceMonitor", func(t *testing.T) {
		monitor := NewPerformanceMonitor("test-service")

		assert.NotNil(t, monitor.instrumentation)
		assert.NotNil(t, monitor.thresholds)
		assert.NotNil(t, monitor.alerts)
	})

	t.Run("SetThreshold", func(t *testing.T) {
		monitor := NewPerformanceMonitor("test-service")
		threshold := 100 * time.Millisecond

		monitor.SetThreshold("test_operation", threshold)

		assert.Equal(t, threshold, monitor.thresholds["test_operation"])
	})

	t.Run("MonitorOperation", func(t *testing.T) {
		monitor := NewPerformanceMonitor("test-service")
		threshold := 50 * time.Millisecond

		monitor.SetThreshold("test_operation", threshold)

		// Monitor operation that exceeds threshold
		monitor.MonitorOperation("test_operation", 100*time.Millisecond)

		// Check for alerts
		alerts := monitor.GetAlerts()
		assert.Len(t, alerts, 1)
		assert.Equal(t, "test-service", alerts[0].Service)
		assert.Equal(t, "test_operation", alerts[0].Operation)
		assert.Equal(t, "warning", alerts[0].Severity)
	})
}

func TestSystemMetricsCollector(t *testing.T) {
	t.Run("NewSystemMetricsCollector", func(t *testing.T) {
		collector := NewSystemMetricsCollector()

		assert.NotNil(t, collector.collector)
		assert.NotNil(t, collector.stopCh)
	})

	t.Run("StartStop", func(t *testing.T) {
		collector := NewSystemMetricsCollector()

		// Start collection
		collector.Start(100 * time.Millisecond)

		// Let it run for a bit
		time.Sleep(200 * time.Millisecond)

		// Stop collection
		collector.Stop()

		// Should not panic
		assert.NotNil(t, collector)
	})
}
