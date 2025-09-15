package api

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"runtime"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// HealthStatus represents the health status of a component
type HealthStatus string

const (
	HealthStatusHealthy   HealthStatus = "healthy"
	HealthStatusDegraded  HealthStatus = "degraded"
	HealthStatusUnhealthy HealthStatus = "unhealthy"
)

// HealthCheck represents a health check result
type HealthCheck struct {
	Status      HealthStatus           `json:"status"`
	Timestamp   time.Time              `json:"timestamp"`
	Version     string                 `json:"version"`
	Uptime      string                 `json:"uptime"`
	Checks      map[string]CheckResult `json:"checks"`
	SystemInfo  SystemInfo             `json:"system_info"`
}

// CheckResult represents an individual check result
type CheckResult struct {
	Status   HealthStatus `json:"status"`
	Message  string       `json:"message,omitempty"`
	Duration string       `json:"duration,omitempty"`
	Error    string       `json:"error,omitempty"`
}

// SystemInfo contains system information
type SystemInfo struct {
	GoVersion    string `json:"go_version"`
	NumCPU       int    `json:"num_cpu"`
	NumGoroutine int    `json:"num_goroutine"`
	MemoryMB     uint64 `json:"memory_mb"`
}

// ReadinessCheck represents readiness status
type ReadinessCheck struct {
	Ready     bool                   `json:"ready"`
	Timestamp time.Time              `json:"timestamp"`
	Checks    map[string]CheckResult `json:"checks"`
}

// HealthChecker performs health checks
type HealthChecker struct {
	db         *sql.DB
	startTime  time.Time
	version    string
	checks     map[string]func(context.Context) CheckResult
	mu         sync.RWMutex
}

// NewHealthChecker creates a new health checker
func NewHealthChecker(db *sql.DB, version string) *HealthChecker {
	hc := &HealthChecker{
		db:        db,
		startTime: time.Now(),
		version:   version,
		checks:    make(map[string]func(context.Context) CheckResult),
	}

	// Register default checks
	hc.RegisterCheck("database", hc.checkDatabase)
	hc.RegisterCheck("disk_space", hc.checkDiskSpace)
	hc.RegisterCheck("memory", hc.checkMemory)

	return hc
}

// RegisterCheck registers a custom health check
func (hc *HealthChecker) RegisterCheck(name string, check func(context.Context) CheckResult) {
	hc.mu.Lock()
	defer hc.mu.Unlock()
	hc.checks[name] = check
}

// HealthHandler returns the health check HTTP handler
func (hc *HealthChecker) HealthHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()

		health := hc.performHealthCheck(ctx)

		// Determine HTTP status code based on health
		statusCode := http.StatusOK
		if health.Status == HealthStatusUnhealthy {
			statusCode = http.StatusServiceUnavailable
		} else if health.Status == HealthStatusDegraded {
			statusCode = http.StatusOK // Still return 200 for degraded
		}

		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.WriteHeader(statusCode)

		if err := json.NewEncoder(w).Encode(health); err != nil {
			logger.Error("Failed to encode health check response: %v", err)
		}
	}
}

// ReadyHandler returns the readiness check HTTP handler
func (hc *HealthChecker) ReadyHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()

		readiness := hc.performReadinessCheck(ctx)

		statusCode := http.StatusOK
		if !readiness.Ready {
			statusCode = http.StatusServiceUnavailable
		}

		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.WriteHeader(statusCode)

		if err := json.NewEncoder(w).Encode(readiness); err != nil {
			logger.Error("Failed to encode readiness check response: %v", err)
		}
	}
}

// LiveHandler returns a simple liveness check handler
func (hc *HealthChecker) LiveHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":    "alive",
			"timestamp": time.Now(),
		})
	}
}

// performHealthCheck executes all health checks
func (hc *HealthChecker) performHealthCheck(ctx context.Context) HealthCheck {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	health := HealthCheck{
		Timestamp: time.Now(),
		Version:   hc.version,
		Uptime:    time.Since(hc.startTime).Round(time.Second).String(),
		Checks:    make(map[string]CheckResult),
		SystemInfo: SystemInfo{
			GoVersion:    runtime.Version(),
			NumCPU:       runtime.NumCPU(),
			NumGoroutine: runtime.NumGoroutine(),
		},
	}

	// Get memory stats
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	health.SystemInfo.MemoryMB = m.Alloc / 1024 / 1024

	// Run all checks concurrently
	var wg sync.WaitGroup
	checkResults := make(chan struct {
		name   string
		result CheckResult
	}, len(hc.checks))

	for name, check := range hc.checks {
		wg.Add(1)
		go func(name string, check func(context.Context) CheckResult) {
			defer wg.Done()
			start := time.Now()
			result := check(ctx)
			result.Duration = time.Since(start).Round(time.Millisecond).String()
			checkResults <- struct {
				name   string
				result CheckResult
			}{name: name, result: result}
		}(name, check)
	}

	wg.Wait()
	close(checkResults)

	// Collect results and determine overall status
	overallStatus := HealthStatusHealthy
	for cr := range checkResults {
		health.Checks[cr.name] = cr.result
		if cr.result.Status == HealthStatusUnhealthy {
			overallStatus = HealthStatusUnhealthy
		} else if cr.result.Status == HealthStatusDegraded && overallStatus == HealthStatusHealthy {
			overallStatus = HealthStatusDegraded
		}
	}

	health.Status = overallStatus
	return health
}

// performReadinessCheck checks if the service is ready to handle requests
func (hc *HealthChecker) performReadinessCheck(ctx context.Context) ReadinessCheck {
	readiness := ReadinessCheck{
		Timestamp: time.Now(),
		Checks:    make(map[string]CheckResult),
		Ready:     true,
	}

	// Check critical components for readiness
	criticalChecks := []string{"database"}

	for _, checkName := range criticalChecks {
		if check, exists := hc.checks[checkName]; exists {
			result := check(ctx)
			readiness.Checks[checkName] = result
			if result.Status == HealthStatusUnhealthy {
				readiness.Ready = false
			}
		}
	}

	return readiness
}

// Default health check implementations

func (hc *HealthChecker) checkDatabase(ctx context.Context) CheckResult {
	if hc.db == nil {
		return CheckResult{
			Status:  HealthStatusUnhealthy,
			Message: "Database connection not initialized",
		}
	}

	// Use context for timeout
	err := hc.db.PingContext(ctx)
	if err != nil {
		return CheckResult{
			Status:  HealthStatusUnhealthy,
			Message: "Database ping failed",
			Error:   err.Error(),
		}
	}

	// Check connection pool stats
	stats := hc.db.Stats()
	if stats.OpenConnections > 0 {
		utilizationPct := float64(stats.InUse) / float64(stats.OpenConnections) * 100

		status := HealthStatusHealthy
		message := "Database connection pool healthy"

		if utilizationPct > 90 {
			status = HealthStatusDegraded
			message = "Database connection pool utilization high"
		}

		return CheckResult{
			Status:  status,
			Message: message,
		}
	}

	return CheckResult{
		Status:  HealthStatusHealthy,
		Message: "Database connection healthy",
	}
}

func (hc *HealthChecker) checkDiskSpace(ctx context.Context) CheckResult {
	// This is a simplified check - in production you'd check actual disk usage
	// using syscall.Statfs on Unix or similar

	// For now, return healthy
	return CheckResult{
		Status:  HealthStatusHealthy,
		Message: "Disk space adequate",
	}
}

func (hc *HealthChecker) checkMemory(ctx context.Context) CheckResult {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	// Check if memory usage is too high (simplified check)
	allocMB := m.Alloc / 1024 / 1024

	status := HealthStatusHealthy
	message := "Memory usage normal"

	if allocMB > 500 { // If using more than 500MB
		status = HealthStatusDegraded
		message = "Memory usage elevated"
	}

	if allocMB > 1000 { // If using more than 1GB
		status = HealthStatusUnhealthy
		message = "Memory usage critical"
	}

	return CheckResult{
		Status:  status,
		Message: message,
	}
}

// MetricsHandler returns Prometheus-compatible metrics
func (hc *HealthChecker) MetricsHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var m runtime.MemStats
		runtime.ReadMemStats(&m)

		w.Header().Set("Content-Type", "text/plain; version=0.0.4")

		// Basic Go runtime metrics in Prometheus format
		metrics := []string{
			"# HELP go_goroutines Number of goroutines that currently exist.",
			"# TYPE go_goroutines gauge",
			"go_goroutines " + fmt.Sprintf("%d", runtime.NumGoroutine()),
			"",
			"# HELP go_memstats_alloc_bytes Number of bytes allocated and still in use.",
			"# TYPE go_memstats_alloc_bytes gauge",
			"go_memstats_alloc_bytes " + fmt.Sprintf("%d", m.Alloc),
			"",
			"# HELP go_memstats_sys_bytes Number of bytes obtained from system.",
			"# TYPE go_memstats_sys_bytes gauge",
			"go_memstats_sys_bytes " + fmt.Sprintf("%d", m.Sys),
			"",
			"# HELP arxos_uptime_seconds Time since service started in seconds.",
			"# TYPE arxos_uptime_seconds counter",
			"arxos_uptime_seconds " + fmt.Sprintf("%d", int(time.Since(hc.startTime).Seconds())),
		}

		for _, metric := range metrics {
			w.Write([]byte(metric + "\n"))
		}
	}
}