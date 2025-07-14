package gateway

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMonitoringMiddleware(t *testing.T) {
	config := MonitoringConfig{
		Enabled:            true,
		MetricsPort:        9090,
		MetricsPath:        "/metrics",
		HealthCheckPath:    "/health",
		LogLevel:           "info",
		LogFormat:          "json",
		RequestTracing:     true,
		PerformanceLogging: true,
		CircuitBreaker: CircuitBreakerConfig{
			Enabled:          true,
			FailureThreshold: 5,
			Timeout:          30 * time.Second,
			ResetTimeout:     60 * time.Second,
			MonitorInterval:  10 * time.Second,
		},
		HealthMonitoring: HealthMonitoringConfig{
			Enabled:          true,
			CheckInterval:    30 * time.Second,
			Timeout:          10 * time.Second,
			FailureThreshold: 3,
			SuccessThreshold: 2,
			Services:         []string{"svg-parser", "cmms-service"},
		},
		Alerting: AlertingConfig{
			Enabled:          true,
			AlertEndpoint:    "http://localhost:8080/alerts",
			AlertToken:       "test-token",
			ErrorThreshold:   0.1,
			LatencyThreshold: 5 * time.Second,
			AlertChannels:    []string{"slack", "email"},
		},
	}

	monitoring, err := NewMonitoringMiddleware(config)
	require.NoError(t, err)
	assert.NotNil(t, monitoring)
}

func TestCircuitBreaker(t *testing.T) {
	config := CircuitBreakerConfig{
		Name:             "test-service",
		FailureThreshold: 3,
		Timeout:          30 * time.Second,
		ResetTimeout:     60 * time.Second,
		MonitorInterval:  10 * time.Second,
		Enabled:          true,
	}

	cb, err := NewCircuitBreaker(config)
	require.NoError(t, err)
	assert.NotNil(t, cb)

	// Test closed state (initial)
	assert.Equal(t, CircuitStateClosed, cb.getState())

	// Test successful execution
	err = cb.Execute(context.Background(), func() error {
		return nil
	})
	assert.NoError(t, err)
	assert.Equal(t, CircuitStateClosed, cb.getState())

	// Test failure threshold
	for i := 0; i < 3; i++ {
		err = cb.Execute(context.Background(), func() error {
			return fmt.Errorf("test error")
		})
		assert.Error(t, err)
	}

	// Circuit should be open after 3 failures
	assert.Equal(t, CircuitStateOpen, cb.getState())

	// Test that circuit is open
	err = cb.Execute(context.Background(), func() error {
		return nil
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "circuit breaker is open")

	// Test force close
	cb.ForceClose()
	assert.Equal(t, CircuitStateClosed, cb.getState())

	// Test reset
	cb.Reset()
	status := cb.GetStatus()
	assert.Equal(t, CircuitStateClosed, status["state"])
	assert.Equal(t, 0, status["failures"])
}

func TestHealthMonitor(t *testing.T) {
	config := HealthConfig{
		Enabled:          true,
		CheckInterval:    1 * time.Second,
		Timeout:          5 * time.Second,
		FailureThreshold: 2,
		SuccessThreshold: 1,
		Services: []ServiceHealthConfig{
			{
				Name:             "test-service",
				URL:              "http://localhost:8080",
				HealthEndpoint:   "http://localhost:8080/health",
				Timeout:          5 * time.Second,
				Interval:         1 * time.Second,
				FailureThreshold: 2,
				SuccessThreshold: 1,
				Headers:          map[string]string{"Authorization": "Bearer test"},
				ExpectedStatus:   200,
			},
		},
		Alerting: HealthAlertingConfig{
			Enabled:           true,
			AlertEndpoint:     "http://localhost:8080/alerts",
			AlertToken:        "test-token",
			AlertChannels:     []string{"slack"},
			FailureThreshold:  2,
			RecoveryThreshold: 1,
		},
	}

	monitor, err := NewHealthMonitor(config)
	require.NoError(t, err)
	assert.NotNil(t, monitor)

	// Test service health retrieval
	health, exists := monitor.GetServiceHealth("test-service")
	assert.True(t, exists)
	assert.NotNil(t, health)
	assert.Equal(t, "test-service", health.Name)

	// Test overall health
	overallHealth := monitor.GetOverallHealth()
	assert.NotNil(t, overallHealth)
	assert.Contains(t, overallHealth, "overall_status")
	assert.Contains(t, overallHealth, "total_services")
}

func TestMetricsCollector(t *testing.T) {
	config := MetricsConfig{
		Enabled:              true,
		Port:                 9090,
		Path:                 "/metrics",
		CollectSystemMetrics: true,
		CollectCustomMetrics: true,
		HistogramBuckets:     []float64{0.1, 0.5, 1.0, 2.0, 5.0},
		EnableGoMetrics:      true,
		EnableProcessMetrics: true,
	}

	collector, err := NewMetricsCollector(config)
	require.NoError(t, err)
	assert.NotNil(t, collector)

	// Test request recording
	collector.RecordRequest("GET", "/api/test", "test-service", 200, 100*time.Millisecond, 1024)
	collector.RecordRequest("POST", "/api/test", "test-service", 500, 200*time.Millisecond, 2048)

	// Test authentication recording
	collector.RecordAuthentication("jwt", "user-123", true, 50*time.Millisecond, "")
	collector.RecordAuthentication("api_key", "user-456", false, 100*time.Millisecond, "invalid_key")

	// Test rate limiting recording
	collector.RecordRateLimit("user-123", "test-service", "per_minute", false, 50)
	collector.RecordRateLimit("user-456", "test-service", "per_hour", true, 0)

	// Test service availability
	collector.SetServiceAvailability("test-service", true)
	collector.SetServiceAvailability("other-service", false)

	// Test system metrics update
	collector.UpdateSystemMetrics()

	// Test custom metric
	customCounter := prometheus.NewCounter(prometheus.CounterOpts{
		Name: "test_custom_counter",
		Help: "Test custom counter",
	})

	err = collector.AddCustomMetric("test_counter", customCounter)
	assert.NoError(t, err)

	// Test custom metric removal
	err = collector.RemoveCustomMetric("test_counter")
	assert.NoError(t, err)
}

func TestMonitoringIntegration(t *testing.T) {
	// Test monitoring middleware with actual HTTP request
	config := MonitoringConfig{
		Enabled:            true,
		RequestTracing:     true,
		PerformanceLogging: true,
	}

	monitoring, err := NewMonitoringMiddleware(config)
	require.NoError(t, err)

	// Create test handler
	handler := monitoring.Middleware()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(10 * time.Millisecond) // Simulate processing time
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test response"))
	}))

	// Create test request
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("User-Agent", "test-agent")
	req.RemoteAddr = "127.0.0.1:12345"

	w := httptest.NewRecorder()

	// Execute request
	handler.ServeHTTP(w, req)

	// Verify response
	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "test response", w.Body.String())
}

func TestCircuitBreakerManager(t *testing.T) {
	manager, err := NewCircuitBreakerManager()
	require.NoError(t, err)
	assert.NotNil(t, manager)

	// Test circuit breaker creation
	config := CircuitBreakerConfig{
		FailureThreshold: 3,
		Timeout:          30 * time.Second,
		ResetTimeout:     60 * time.Second,
		MonitorInterval:  10 * time.Second,
		Enabled:          true,
	}

	cb1, err := manager.GetCircuitBreaker("service-1", config)
	require.NoError(t, err)
	assert.NotNil(t, cb1)

	cb2, err := manager.GetCircuitBreaker("service-2", config)
	require.NoError(t, err)
	assert.NotNil(t, cb2)

	// Test that we get the same instance for the same service
	cb1Again, err := manager.GetCircuitBreaker("service-1", config)
	require.NoError(t, err)
	assert.Equal(t, cb1, cb1Again)

	// Test status retrieval
	status := manager.GetStatus()
	assert.Contains(t, status, "service-1")
	assert.Contains(t, status, "service-2")

	// Test reset all
	manager.ResetAll()
}

func TestHealthMonitorWithMockServer(t *testing.T) {
	// Create mock health check server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"healthy"}`))
		} else {
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	config := HealthConfig{
		Enabled:          true,
		CheckInterval:    100 * time.Millisecond, // Fast for testing
		Timeout:          5 * time.Second,
		FailureThreshold: 2,
		SuccessThreshold: 1,
		Services: []ServiceHealthConfig{
			{
				Name:             "mock-service",
				URL:              server.URL,
				HealthEndpoint:   server.URL + "/health",
				Timeout:          5 * time.Second,
				Interval:         100 * time.Millisecond, // Fast for testing
				FailureThreshold: 2,
				SuccessThreshold: 1,
				ExpectedStatus:   200,
			},
		},
	}

	monitor, err := NewHealthMonitor(config)
	require.NoError(t, err)

	// Wait for health check to complete
	time.Sleep(200 * time.Millisecond)

	// Check service health
	health, exists := monitor.GetServiceHealth("mock-service")
	assert.True(t, exists)
	assert.NotNil(t, health)
	assert.Equal(t, "mock-service", health.Name)
	assert.Equal(t, HealthStatusHealthy, health.Status)
	assert.Greater(t, health.SuccessCount, 0)
}

func TestMetricsCollectorPerformance(t *testing.T) {
	config := MetricsConfig{
		Enabled:              true,
		Port:                 9091, // Different port for testing
		Path:                 "/metrics",
		CollectSystemMetrics: true,
	}

	collector, err := NewMetricsCollector(config)
	require.NoError(t, err)

	// Test performance under load
	start := time.Now()
	for i := 0; i < 1000; i++ {
		collector.RecordRequest("GET", "/api/test", "test-service", 200, 10*time.Millisecond, 1024)
	}
	duration := time.Since(start)

	// Performance should be fast (less than 1 second for 1000 requests)
	assert.Less(t, duration, time.Second)

	// Test system metrics update performance
	start = time.Now()
	for i := 0; i < 100; i++ {
		collector.UpdateSystemMetrics()
	}
	duration = time.Since(start)

	// System metrics update should be fast
	assert.Less(t, duration, 100*time.Millisecond)
}

func TestMonitoringConfiguration(t *testing.T) {
	// Test configuration updates
	config := MonitoringConfig{
		Enabled:            true,
		RequestTracing:     true,
		PerformanceLogging: true,
	}

	monitoring, err := NewMonitoringMiddleware(config)
	require.NoError(t, err)

	// Update configuration
	newConfig := MonitoringConfig{
		Enabled:            true,
		RequestTracing:     false,
		PerformanceLogging: false,
	}

	err = monitoring.UpdateConfig(newConfig)
	assert.NoError(t, err)

	// Test metrics collector configuration
	metricsConfig := MetricsConfig{
		Enabled:              true,
		Port:                 9092,
		Path:                 "/metrics",
		CollectSystemMetrics: true,
	}

	collector, err := NewMetricsCollector(metricsConfig)
	require.NoError(t, err)

	// Update metrics configuration
	newMetricsConfig := MetricsConfig{
		Enabled:              true,
		Port:                 9093,
		Path:                 "/metrics",
		CollectSystemMetrics: false,
	}

	err = collector.UpdateConfig(newMetricsConfig)
	assert.NoError(t, err)
}

func TestMonitoringStats(t *testing.T) {
	config := MonitoringConfig{
		Enabled:            true,
		RequestTracing:     true,
		PerformanceLogging: true,
	}

	monitoring, err := NewMonitoringMiddleware(config)
	require.NoError(t, err)

	stats := monitoring.GetMonitoringStats()
	assert.NotNil(t, stats)
	assert.Equal(t, true, stats["enabled"])
	assert.Equal(t, true, stats["request_tracing"])
	assert.Equal(t, true, stats["performance_logging"])

	// Test metrics collector stats
	metricsConfig := MetricsConfig{
		Enabled:              true,
		Port:                 9094,
		Path:                 "/metrics",
		CollectSystemMetrics: true,
	}

	collector, err := NewMetricsCollector(metricsConfig)
	require.NoError(t, err)

	metricsStats := collector.GetMetricsStats()
	assert.NotNil(t, metricsStats)
	assert.Equal(t, true, metricsStats["enabled"])
	assert.Equal(t, 9094, metricsStats["port"])
	assert.Equal(t, "/metrics", metricsStats["path"])
}
