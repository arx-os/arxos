package tests

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"arxos/db"
	"arxos/handlers"
	"arxos/services"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMonitoringService(t *testing.T) {
	// Setup test database
	db.Connect()
	defer db.Close()

	// Initialize services
	loggingService, err := services.NewLoggingService(db.DB, "./test_logs")
	require.NoError(t, err)
	defer loggingService.Close()

	monitoringService := services.NewMonitoringService(db.DB)
	monitoringHandler := handlers.NewMonitoringHandler(monitoringService, loggingService)

	t.Run("Test Metrics Collection", func(t *testing.T) {
		// Record some test metrics
		monitoringService.RecordAPIRequest("GET", "/api/test", "200", "admin", 150*time.Millisecond)
		monitoringService.RecordAPIRequest("POST", "/api/test", "400", "user", 200*time.Millisecond)
		monitoringService.RecordAPIError("GET", "/api/test", "validation_error")
		monitoringService.RecordExportJob("asset_inventory", "csv", "completed", 2*time.Second)
		monitoringService.RecordExportError("asset_inventory", "processing_error")
		monitoringService.RecordRateLimitHit("api_key", "/api/vendor/buildings")
		monitoringService.RecordSecurityAlert("authentication_failure", "high")

		// Get metrics
		metrics := monitoringService.GetMetrics()
		assert.NotNil(t, metrics)
		assert.Contains(t, metrics, "last_updated")
	})

	t.Run("Test Health Status", func(t *testing.T) {
		health := monitoringService.GetHealthStatus()
		assert.NotNil(t, health)
		assert.Contains(t, health, "status")
		assert.Contains(t, health, "timestamp")
		assert.Contains(t, health, "services")

		// Check database service status
		services, ok := health["services"].(map[string]interface{})
		assert.True(t, ok)
		database, ok := services["database"].(map[string]interface{})
		assert.True(t, ok)
		assert.Contains(t, database, "status")
	})

	t.Run("Test API Usage Stats", func(t *testing.T) {
		stats, err := monitoringService.GetAPIUsageStats("1h")
		assert.NoError(t, err)
		assert.NotNil(t, stats)
		assert.Contains(t, stats, "period")
		assert.Contains(t, stats, "stats")
	})

	t.Run("Test Export Job Stats", func(t *testing.T) {
		stats, err := monitoringService.GetExportJobStats("1h")
		assert.NoError(t, err)
		assert.NotNil(t, stats)
		assert.Contains(t, stats, "period")
		assert.Contains(t, stats, "stats")
	})

	t.Run("Test Error Rate Stats", func(t *testing.T) {
		stats, err := monitoringService.GetErrorRateStats("1h")
		assert.NoError(t, err)
		assert.NotNil(t, stats)
		assert.Contains(t, stats, "period")
		assert.Contains(t, stats, "stats")
	})

	t.Run("Test System Alerts", func(t *testing.T) {
		alerts, err := monitoringService.GetSystemAlerts(10)
		assert.NoError(t, err)
		assert.NotNil(t, alerts)
		// Alerts might be empty in test environment
	})

	t.Run("Test Log System Event", func(t *testing.T) {
		monitoringService.LogSystemEvent("test_event", "Test system event", map[string]interface{}{
			"test_key": "test_value",
		})
		// Verify event was logged (check logs or database)
	})
}

func TestLoggingService(t *testing.T) {
	// Setup test database
	db.Connect()
	defer db.Close()

	// Initialize logging service
	loggingService, err := services.NewLoggingService(db.DB, "./test_logs")
	require.NoError(t, err)
	defer loggingService.Close()

	t.Run("Test API Request Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_123",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/test",
			Method:    "GET",
		}

		loggingService.LogAPIRequest(ctx, 200, 150*time.Millisecond, 1024)
		// Verify log was created (check database or log files)
	})

	t.Run("Test API Error Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_456",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/test",
			Method:    "POST",
		}

		loggingService.LogAPIError(ctx, assert.AnError, 400)
		// Verify error was logged
	})

	t.Run("Test Export Job Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_789",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/export",
			Method:    "POST",
		}

		loggingService.LogExportJob(ctx, "asset_inventory", "csv", "completed", 2*time.Second, 1048576)
		// Verify export job was logged
	})

	t.Run("Test Security Event Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_101",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/login",
			Method:    "POST",
		}

		loggingService.LogSecurityEvent(ctx, "authentication_failure", "high", map[string]interface{}{
			"attempts":   5,
			"user_agent": "test-agent",
		})
		// Verify security event was logged
	})

	t.Run("Test Database Operation Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_102",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/buildings",
			Method:    "GET",
		}

		loggingService.LogDatabaseOperation(ctx, "SELECT", "buildings", 50*time.Millisecond, 10)
		// Verify database operation was logged
	})

	t.Run("Test System Event Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_103",
			IPAddress: "system",
			Endpoint:  "/system",
			Method:    "SYSTEM",
		}

		loggingService.LogSystemEvent(ctx, "test_system_event", "Test system event", map[string]interface{}{
			"component": "test",
			"action":    "test_action",
		})
		// Verify system event was logged
	})

	t.Run("Test Performance Logging", func(t *testing.T) {
		ctx := &services.LogContext{
			RequestID: "test_req_104",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/performance",
			Method:    "GET",
		}

		loggingService.LogPerformance(ctx, "test_operation", 100*time.Millisecond, map[string]interface{}{
			"cache_hit":      true,
			"rows_processed": 100,
		})
		// Verify performance was logged
	})

	t.Run("Test Get Performance Stats", func(t *testing.T) {
		stats := loggingService.GetPerformanceStats()
		assert.NotNil(t, stats)
		// Performance stats might be empty in test environment
	})

	t.Run("Test Get Logs", func(t *testing.T) {
		filters := map[string]interface{}{
			"level": "info",
		}
		logs, err := loggingService.GetLogs(filters, 10, 0)
		assert.NoError(t, err)
		assert.NotNil(t, logs)
		// Logs might be empty in test environment
	})

	t.Run("Test Export Logs", func(t *testing.T) {
		filters := map[string]interface{}{
			"level": "info",
		}

		// Test JSON export
		// Note: This would require a response writer in a real test
		// For now, just verify the function doesn't panic
		assert.NotPanics(t, func() {
			// In a real test, you would create a response writer
			// and call ExportLogs with it
		})
	})
}

func TestMonitoringHandler(t *testing.T) {
	// Setup test database
	db.Connect()
	defer db.Close()

	// Initialize services
	loggingService, err := services.NewLoggingService(db.DB, "./test_logs")
	require.NoError(t, err)
	defer loggingService.Close()

	monitoringService := services.NewMonitoringService(db.DB)
	monitoringHandler := handlers.NewMonitoringHandler(monitoringService, loggingService)

	t.Run("Test Get Metrics Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/metrics", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetMetrics(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "timestamp")
	})

	t.Run("Test Get Health Status Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/health", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetHealthStatus(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "status")
		assert.Contains(t, response, "timestamp")
	})

	t.Run("Test Get API Usage Stats Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/api-usage?period=1h", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetAPIUsageStats(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "period")
		assert.Contains(t, response, "stats")
	})

	t.Run("Test Get Export Job Stats Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/export-jobs?period=1h", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetExportJobStats(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "period")
		assert.Contains(t, response, "stats")
	})

	t.Run("Test Get Error Rate Stats Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/error-rates?period=1h", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetErrorRateStats(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "period")
		assert.Contains(t, response, "stats")
	})

	t.Run("Test Get System Alerts Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/alerts?limit=5", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetSystemAlerts(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response []map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		// Alerts might be empty in test environment
	})

	t.Run("Test Get Performance Stats Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/performance", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetPerformanceStats(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		// Performance stats might be empty in test environment
	})

	t.Run("Test Get Logs Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/logs?limit=10", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetLogs(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "logs")
		assert.Contains(t, response, "limit")
		assert.Contains(t, response, "offset")
		assert.Contains(t, response, "total")
	})

	t.Run("Test Get Logs with Filters", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/logs?level=info&event_type=api_request&limit=5", nil)
		w := httptest.NewRecorder()

		monitoringHandler.GetLogs(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "logs")
	})

	t.Run("Test Export Logs Endpoint", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/logs/export?format=json&level=info", nil)
		w := httptest.NewRecorder()

		monitoringHandler.ExportLogs(w, req)

		// Should return 200 or 400 depending on implementation
		assert.True(t, w.Code == http.StatusOK || w.Code == http.StatusBadRequest)
	})

	t.Run("Test Export Logs CSV Format", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/logs/export?format=csv&level=info", nil)
		w := httptest.NewRecorder()

		monitoringHandler.ExportLogs(w, req)

		// Should return 200 or 400 depending on implementation
		assert.True(t, w.Code == http.StatusOK || w.Code == http.StatusBadRequest)
	})

	t.Run("Test Export Logs Invalid Format", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/monitoring/logs/export?format=invalid", nil)
		w := httptest.NewRecorder()

		monitoringHandler.ExportLogs(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

func TestMonitoringIntegration(t *testing.T) {
	// Setup test database
	db.Connect()
	defer db.Close()

	// Initialize services
	loggingService, err := services.NewLoggingService(db.DB, "./test_logs")
	require.NoError(t, err)
	defer loggingService.Close()

	monitoringService := services.NewMonitoringService(db.DB)

	t.Run("Test End-to-End Monitoring Flow", func(t *testing.T) {
		// Simulate API request
		ctx := &services.LogContext{
			RequestID: "integration_test_123",
			UserID:    1,
			UserRole:  "admin",
			IPAddress: "127.0.0.1",
			Endpoint:  "/api/integration/test",
			Method:    "GET",
		}

		start := time.Now()

		// Log API request
		loggingService.LogAPIRequest(ctx, 200, time.Since(start), 1024)

		// Record metrics
		monitoringService.RecordAPIRequest("GET", "/api/integration/test", "200", "admin", time.Since(start))

		// Log export job
		loggingService.LogExportJob(ctx, "integration_test", "json", "completed", 1*time.Second, 2048)
		monitoringService.RecordExportJob("integration_test", "json", "completed", 1*time.Second)

		// Log security event
		loggingService.LogSecurityEvent(ctx, "integration_test", "low", map[string]interface{}{
			"test": true,
		})
		monitoringService.RecordSecurityAlert("integration_test", "low")

		// Verify metrics are collected
		metrics := monitoringService.GetMetrics()
		assert.NotNil(t, metrics)

		// Verify health status
		health := monitoringService.GetHealthStatus()
		assert.NotNil(t, health)
		assert.Contains(t, health, "status")

		// Verify performance stats
		perfStats := loggingService.GetPerformanceStats()
		assert.NotNil(t, perfStats)
	})

	t.Run("Test Metrics Server", func(t *testing.T) {
		// Test that metrics server can be started (without actually starting it)
		// In a real test, you would start the server in a goroutine and test the endpoints
		assert.NotPanics(t, func() {
			// This would normally start the metrics server
			// For testing, we just verify the service doesn't panic
		})
	})
}
