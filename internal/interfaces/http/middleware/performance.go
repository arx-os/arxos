package middleware

import (
	"context"
	"net/http"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// PerformanceMiddleware provides performance monitoring for HTTP requests
func PerformanceMiddleware(metricsCollector any, logger domain.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Create a response writer wrapper to capture status code
			pw := &performanceResponseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
			}

			// Process request
			next.ServeHTTP(pw, r)

			// Calculate metrics
			duration := time.Since(start)

			// Record metrics
			recordHTTPMetrics(metricsCollector, r, pw.statusCode, duration, logger)
		})
	}
}

// performanceResponseWriter wraps http.ResponseWriter to capture status code
type performanceResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

// WriteHeader captures the status code
func (pw *performanceResponseWriter) WriteHeader(code int) {
	pw.statusCode = code
	pw.ResponseWriter.WriteHeader(code)
}

// recordHTTPMetrics records HTTP performance metrics
func recordHTTPMetrics(metricsCollector any, r *http.Request, statusCode int, duration time.Duration, logger domain.Logger) {
	// This is a simplified implementation
	// In a real implementation, you would use the metricsCollector to record metrics

	logger.Debug("HTTP request completed",
		"method", r.Method,
		"path", r.URL.Path,
		"status", statusCode,
		"duration", duration,
	)
}

// DatabasePerformanceMiddleware provides performance monitoring for database operations
func DatabasePerformanceMiddleware(logger domain.Logger) func(func(context.Context, string, ...any) error) func(context.Context, string, ...any) error {
	return func(dbFunc func(context.Context, string, ...any) error) func(context.Context, string, ...any) error {
		return func(ctx context.Context, query string, args ...any) error {
			start := time.Now()

			err := dbFunc(ctx, query, args...)

			duration := time.Since(start)

			// Record database metrics
			recordDatabaseMetrics(query, duration, err, logger)

			return err
		}
	}
}

// recordDatabaseMetrics records database performance metrics
func recordDatabaseMetrics(query string, duration time.Duration, err error, logger domain.Logger) {
	// This is a simplified implementation
	// In a real implementation, you would record detailed database metrics

	logger.Debug("Database query completed",
		"query", query,
		"duration", duration,
		"error", err != nil,
	)
}

// CachePerformanceMiddleware provides performance monitoring for cache operations
func CachePerformanceMiddleware(logger domain.Logger) func(func(context.Context, string) (any, error)) func(context.Context, string) (any, error) {
	return func(cacheFunc func(context.Context, string) (any, error)) func(context.Context, string) (any, error) {
		return func(ctx context.Context, key string) (any, error) {
			start := time.Now()

			result, err := cacheFunc(ctx, key)

			duration := time.Since(start)

			// Record cache metrics
			recordCacheMetrics(key, duration, err == nil, logger)

			return result, err
		}
	}
}

// recordCacheMetrics records cache performance metrics
func recordCacheMetrics(key string, duration time.Duration, hit bool, logger domain.Logger) {
	// This is a simplified implementation
	// In a real implementation, you would record detailed cache metrics

	logger.Debug("Cache operation completed",
		"key", key,
		"duration", duration,
		"hit", hit,
	)
}

// PerformanceStats tracks performance statistics
type PerformanceStats struct {
	mu           sync.RWMutex
	requestCount int64
	successCount int64
	errorCount   int64
	totalLatency time.Duration
	maxLatency   time.Duration
	minLatency   time.Duration
	statusCodes  map[int]int64
	lastReset    time.Time
}

// NewPerformanceStats creates a new performance stats tracker
func NewPerformanceStats() *PerformanceStats {
	return &PerformanceStats{
		statusCodes: make(map[int]int64),
		lastReset:   time.Now(),
	}
}

// RecordRequest records a request
func (ps *PerformanceStats) RecordRequest(statusCode int, latency time.Duration) {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	ps.requestCount++

	if statusCode >= 200 && statusCode < 400 {
		ps.successCount++
	} else {
		ps.errorCount++
	}

	ps.totalLatency += latency

	if latency > ps.maxLatency {
		ps.maxLatency = latency
	}

	if ps.minLatency == 0 || latency < ps.minLatency {
		ps.minLatency = latency
	}

	ps.statusCodes[statusCode]++
}

// GetStats returns current performance statistics
func (ps *PerformanceStats) GetStats() map[string]any {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	avgLatency := time.Duration(0)
	if ps.requestCount > 0 {
		avgLatency = ps.totalLatency / time.Duration(ps.requestCount)
	}

	return map[string]any{
		"request_count":   ps.requestCount,
		"success_count":   ps.successCount,
		"error_count":     ps.errorCount,
		"average_latency": avgLatency,
		"max_latency":     ps.maxLatency,
		"min_latency":     ps.minLatency,
		"status_codes":    ps.statusCodes,
		"last_reset":      ps.lastReset,
	}
}

// Reset resets all statistics
func (ps *PerformanceStats) Reset() {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	ps.requestCount = 0
	ps.successCount = 0
	ps.errorCount = 0
	ps.totalLatency = 0
	ps.maxLatency = 0
	ps.minLatency = 0
	ps.statusCodes = make(map[int]int64)
	ps.lastReset = time.Now()
}

// PerformanceConfig represents performance monitoring configuration
type PerformanceConfig struct {
	EnableHTTPMonitoring     bool          `json:"enable_http_monitoring"`
	EnableDatabaseMonitoring bool          `json:"enable_database_monitoring"`
	EnableCacheMonitoring    bool          `json:"enable_cache_monitoring"`
	SlowQueryThreshold       time.Duration `json:"slow_query_threshold"`
	SlowRequestThreshold     time.Duration `json:"slow_request_threshold"`
	MetricsInterval          time.Duration `json:"metrics_interval"`
	EnableDetailedLogging    bool          `json:"enable_detailed_logging"`
}

// DefaultPerformanceConfig returns default performance configuration
func DefaultPerformanceConfig() *PerformanceConfig {
	return &PerformanceConfig{
		EnableHTTPMonitoring:     true,
		EnableDatabaseMonitoring: true,
		EnableCacheMonitoring:    true,
		SlowQueryThreshold:       100 * time.Millisecond,
		SlowRequestThreshold:     500 * time.Millisecond,
		MetricsInterval:          30 * time.Second,
		EnableDetailedLogging:    false,
	}
}

// PerformanceMonitor manages performance monitoring
type PerformanceMonitor struct {
	config *PerformanceConfig
	stats  *PerformanceStats
	logger domain.Logger
}

// NewPerformanceMonitor creates a new performance monitor
func NewPerformanceMonitor(config *PerformanceConfig, logger domain.Logger) *PerformanceMonitor {
	return &PerformanceMonitor{
		config: config,
		stats:  NewPerformanceStats(),
		logger: logger,
	}
}

// GetPerformanceReport returns a comprehensive performance report
func (pm *PerformanceMonitor) GetPerformanceReport() map[string]any {
	stats := pm.stats.GetStats()

	report := map[string]any{
		"timestamp": time.Now(),
		"config":    pm.config,
		"stats":     stats,
		"health":    pm.getHealthStatus(),
	}

	return report
}

// getHealthStatus returns the health status based on performance metrics
func (pm *PerformanceMonitor) getHealthStatus() map[string]any {
	stats := pm.stats.GetStats()

	requestCount := stats["request_count"].(int64)
	errorCount := stats["error_count"].(int64)
	avgLatency := stats["average_latency"].(time.Duration)

	errorRate := float64(0)
	if requestCount > 0 {
		errorRate = float64(errorCount) / float64(requestCount) * 100
	}

	status := "healthy"
	if errorRate > 10 || avgLatency > pm.config.SlowRequestThreshold {
		status = "degraded"
	}
	if errorRate > 25 || avgLatency > pm.config.SlowRequestThreshold*2 {
		status = "unhealthy"
	}

	return map[string]any{
		"status":      status,
		"error_rate":  errorRate,
		"avg_latency": avgLatency,
		"thresholds": map[string]any{
			"slow_request": pm.config.SlowRequestThreshold,
			"error_rate":   10.0,
		},
	}
}

// StartMonitoring starts background performance monitoring
func (pm *PerformanceMonitor) StartMonitoring(ctx context.Context) {
	ticker := time.NewTicker(pm.config.MetricsInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			pm.logPerformanceMetrics()
		}
	}
}

// logPerformanceMetrics logs current performance metrics
func (pm *PerformanceMonitor) logPerformanceMetrics() {
	stats := pm.stats.GetStats()
	health := pm.getHealthStatus()

	pm.logger.Info("Performance metrics",
		"request_count", stats["request_count"],
		"error_count", stats["error_count"],
		"average_latency", stats["average_latency"],
		"health_status", health["status"],
		"error_rate", health["error_rate"],
	)
}
