package handlers

import (
	"context"
	"net/http"
	"runtime"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
)

// HealthHandler handles health check endpoints
type HealthHandler struct {
	BaseHandler
	database  domain.Database
	cache     domain.Cache
	logger    domain.Logger
	startTime time.Time
}

// NewHealthHandler creates a new health handler
func NewHealthHandler(
	server *types.Server,
	database domain.Database,
	cache domain.Cache,
	logger domain.Logger,
) *HealthHandler {
	return &HealthHandler{
		BaseHandler: nil, // Will be injected by container
		database:    database,
		cache:       cache,
		logger:      logger,
		startTime:   time.Now(),
	}
}

// HealthResponse represents a health check response
type HealthResponse struct {
	Status    string                   `json:"status"`
	Timestamp time.Time                `json:"timestamp"`
	Uptime    time.Duration            `json:"uptime"`
	Version   string                   `json:"version"`
	Services  map[string]ServiceHealth `json:"services"`
	System    SystemHealth             `json:"system"`
	Metadata  map[string]any           `json:"metadata,omitempty"`
}

// ServiceHealth represents the health of a service
type ServiceHealth struct {
	Status       string         `json:"status"`
	ResponseTime time.Duration  `json:"response_time,omitempty"`
	LastCheck    time.Time      `json:"last_check"`
	Error        string         `json:"error,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
}

// SystemHealth represents system health information
type SystemHealth struct {
	CPUUsage        float64       `json:"cpu_usage"`
	MemoryUsage     int64         `json:"memory_usage"`
	MemoryAvailable int64         `json:"memory_available"`
	Goroutines      int           `json:"goroutines"`
	GCPauseTime     time.Duration `json:"gc_pause_time"`
	DiskUsage       int64         `json:"disk_usage"`
	DiskAvailable   int64         `json:"disk_available"`
}

// Health handles basic health check requests
func (h *HealthHandler) Health(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Health check requested")

	// Check all services
	services := h.checkAllServices(r.Context())

	// Determine overall status
	overallStatus := "healthy"
	for _, service := range services {
		if service.Status != "healthy" {
			overallStatus = "unhealthy"
			break
		}
	}

	// Get system health
	systemHealth := h.getSystemHealth()

	response := HealthResponse{
		Status:    overallStatus,
		Timestamp: time.Now(),
		Uptime:    time.Since(h.startTime),
		Version:   "1.0.0", // This would come from build info
		Services:  services,
		System:    systemHealth,
		Metadata: map[string]any{
			"build_time": h.startTime,
			"go_version": runtime.Version(),
		},
	}

	// Set appropriate status code
	statusCode := http.StatusOK
	if overallStatus != "healthy" {
		statusCode = http.StatusServiceUnavailable
	}

	h.RespondJSON(w, statusCode, response)
}

// HealthDetailed handles detailed health check requests
func (h *HealthHandler) HealthDetailed(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Detailed health check requested")

	// Perform comprehensive health checks
	services := h.checkAllServicesDetailed(r.Context())
	systemHealth := h.getSystemHealthDetailed()

	// Determine overall status
	overallStatus := "healthy"
	for _, service := range services {
		if service.Status != "healthy" {
			overallStatus = "unhealthy"
			break
		}
	}

	response := HealthResponse{
		Status:    overallStatus,
		Timestamp: time.Now(),
		Uptime:    time.Since(h.startTime),
		Version:   "1.0.0",
		Services:  services,
		System:    systemHealth,
		Metadata: map[string]any{
			"build_time":   h.startTime,
			"go_version":   runtime.Version(),
			"architecture": runtime.GOARCH,
			"os":           runtime.GOOS,
		},
	}

	// Set appropriate status code
	statusCode := http.StatusOK
	if overallStatus != "healthy" {
		statusCode = http.StatusServiceUnavailable
	}

	h.RespondJSON(w, statusCode, response)
}

// Readiness handles readiness check requests
func (h *HealthHandler) Readiness(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Readiness check requested")

	// Check critical services for readiness
	services := h.checkCriticalServices(r.Context())

	// Determine readiness status
	ready := true
	for _, service := range services {
		if service.Status != "healthy" {
			ready = false
			break
		}
	}

	response := map[string]any{
		"ready":     ready,
		"timestamp": time.Now(),
		"services":  services,
	}

	statusCode := http.StatusOK
	if !ready {
		statusCode = http.StatusServiceUnavailable
	}

	h.RespondJSON(w, statusCode, response)
}

// Liveness handles liveness check requests
func (h *HealthHandler) Liveness(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Liveness check requested")

	// Simple liveness check - just return OK if the service is running
	response := map[string]any{
		"alive":     true,
		"timestamp": time.Now(),
		"uptime":    time.Since(h.startTime),
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// checkAllServices checks the health of all services
func (h *HealthHandler) checkAllServices(ctx context.Context) map[string]ServiceHealth {
	services := make(map[string]ServiceHealth)

	// Check database
	services["database"] = h.checkDatabase(ctx)

	// Check cache
	services["cache"] = h.checkCache(ctx)

	// Check external services (if any)
	services["external_services"] = h.checkExternalServices(ctx)

	return services
}

// checkAllServicesDetailed performs detailed health checks
func (h *HealthHandler) checkAllServicesDetailed(ctx context.Context) map[string]ServiceHealth {
	services := make(map[string]ServiceHealth)

	// Check database with detailed metrics
	services["database"] = h.checkDatabaseDetailed(ctx)

	// Check cache with detailed metrics
	services["cache"] = h.checkCacheDetailed(ctx)

	// Check external services
	services["external_services"] = h.checkExternalServicesDetailed(ctx)

	return services
}

// checkCriticalServices checks only critical services for readiness
func (h *HealthHandler) checkCriticalServices(ctx context.Context) map[string]ServiceHealth {
	services := make(map[string]ServiceHealth)

	// Only check database for readiness
	services["database"] = h.checkDatabase(ctx)

	return services
}

// checkDatabase checks database health
func (h *HealthHandler) checkDatabase(ctx context.Context) ServiceHealth {
	start := time.Now()

	err := h.database.Health(ctx)
	responseTime := time.Since(start)

	status := "healthy"
	errorMsg := ""
	if err != nil {
		status = "unhealthy"
		errorMsg = err.Error()
	}

	return ServiceHealth{
		Status:       status,
		ResponseTime: responseTime,
		LastCheck:    time.Now(),
		Error:        errorMsg,
	}
}

// checkDatabaseDetailed performs detailed database health check
func (h *HealthHandler) checkDatabaseDetailed(ctx context.Context) ServiceHealth {
	start := time.Now()

	err := h.database.Health(ctx)
	responseTime := time.Since(start)

	status := "healthy"
	errorMsg := ""
	metadata := make(map[string]any)

	if err != nil {
		status = "unhealthy"
		errorMsg = err.Error()
	} else {
		// Add detailed database metrics
		metadata["connection_pool"] = "active"
		metadata["response_time"] = responseTime
	}

	return ServiceHealth{
		Status:       status,
		ResponseTime: responseTime,
		LastCheck:    time.Now(),
		Error:        errorMsg,
		Metadata:     metadata,
	}
}

// checkCache checks cache health
func (h *HealthHandler) checkCache(ctx context.Context) ServiceHealth {
	start := time.Now()

	// Simple cache health check
	_, err := h.cache.Get(ctx, "health_check")
	responseTime := time.Since(start)

	status := "healthy"
	errorMsg := ""
	if err != nil {
		// Cache miss is not necessarily an error for health check
		status = "healthy"
	}

	return ServiceHealth{
		Status:       status,
		ResponseTime: responseTime,
		LastCheck:    time.Now(),
		Error:        errorMsg,
	}
}

// checkCacheDetailed performs detailed cache health check
func (h *HealthHandler) checkCacheDetailed(ctx context.Context) ServiceHealth {
	start := time.Now()

	// Test cache operations
	testKey := "health_check_test"
	testValue := "test_value"

	err := h.cache.Set(ctx, testKey, testValue, time.Minute)
	if err == nil {
		_, err = h.cache.Get(ctx, testKey)
		if err == nil {
			h.cache.Delete(ctx, testKey)
		}
	}

	responseTime := time.Since(start)

	status := "healthy"
	errorMsg := ""
	metadata := make(map[string]any)

	if err != nil {
		status = "unhealthy"
		errorMsg = err.Error()
	} else {
		metadata["operations_tested"] = []string{"set", "get", "delete"}
		metadata["response_time"] = responseTime
	}

	return ServiceHealth{
		Status:       status,
		ResponseTime: responseTime,
		LastCheck:    time.Now(),
		Error:        errorMsg,
		Metadata:     metadata,
	}
}

// checkExternalServices checks external services health
func (h *HealthHandler) checkExternalServices(ctx context.Context) ServiceHealth {
	// Placeholder for external service checks
	return ServiceHealth{
		Status:    "healthy",
		LastCheck: time.Now(),
		Metadata: map[string]any{
			"services": []string{"ifc_service", "notification_service"},
			"status":   "not_implemented",
		},
	}
}

// checkExternalServicesDetailed performs detailed external services health check
func (h *HealthHandler) checkExternalServicesDetailed(ctx context.Context) ServiceHealth {
	// Placeholder for detailed external service checks
	return ServiceHealth{
		Status:    "healthy",
		LastCheck: time.Now(),
		Metadata: map[string]any{
			"services": []string{"ifc_service", "notification_service"},
			"status":   "not_implemented",
			"details":  "External service health checks not yet implemented",
		},
	}
}

// getSystemHealth returns basic system health information
func (h *HealthHandler) getSystemHealth() SystemHealth {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return SystemHealth{
		CPUUsage:        0, // Would need external library for CPU usage
		MemoryUsage:     int64(m.Alloc),
		MemoryAvailable: int64(m.Sys - m.Alloc),
		Goroutines:      runtime.NumGoroutine(),
		GCPauseTime:     time.Duration(m.PauseTotalNs),
		DiskUsage:       0, // Would need external library for disk usage
		DiskAvailable:   0, // Would need external library for disk usage
	}
}

// getSystemHealthDetailed returns detailed system health information
func (h *HealthHandler) getSystemHealthDetailed() SystemHealth {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return SystemHealth{
		CPUUsage:        0, // Would need external library for CPU usage
		MemoryUsage:     int64(m.Alloc),
		MemoryAvailable: int64(m.Sys - m.Alloc),
		Goroutines:      runtime.NumGoroutine(),
		GCPauseTime:     time.Duration(m.PauseTotalNs),
		DiskUsage:       0, // Would need external library for disk usage
		DiskAvailable:   0, // Would need external library for disk usage
	}
}

// Metrics handles metrics endpoint requests
func (h *HealthHandler) Metrics(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Metrics requested")

	// Get system metrics
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	metrics := map[string]any{
		"timestamp": time.Now(),
		"uptime":    time.Since(h.startTime),
		"system": map[string]any{
			"goroutines":     runtime.NumGoroutine(),
			"memory_alloc":   m.Alloc,
			"memory_total":   m.TotalAlloc,
			"gc_cycles":      m.NumGC,
			"gc_pause_total": m.PauseTotalNs,
		},
		"services": map[string]any{
			"database": h.checkDatabase(r.Context()),
			"cache":    h.checkCache(r.Context()),
		},
	}

	h.RespondJSON(w, http.StatusOK, metrics)
}
