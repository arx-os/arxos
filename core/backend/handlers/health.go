package handlers

import (
	"encoding/json"
	"net/http"
	"runtime"
	"time"
)

// HealthResponse represents the health check response structure
type HealthResponse struct {
	Status    string                 `json:"status"`
	Timestamp time.Time              `json:"timestamp"`
	Services  map[string]string     `json:"services"`
	Metrics   map[string]interface{} `json:"metrics"`
	Version   string                 `json:"version"`
	Uptime    string                 `json:"uptime"`
}

// SystemMetrics contains system performance metrics
type SystemMetrics struct {
	MemoryUsage    map[string]interface{} `json:"memory_usage"`
	CPUUsage       float64                `json:"cpu_usage"`
	Goroutines     int                    `json:"goroutines"`
	HeapAlloc      uint64                 `json:"heap_alloc"`
	HeapSys        uint64                 `json:"heap_sys"`
	HeapIdle       uint64                 `json:"heap_idle"`
	HeapInuse      uint64                 `json:"heap_inuse"`
	HeapReleased   uint64                 `json:"heap_released"`
	HeapObjects    uint64                 `json:"heap_objects"`
	StackInuse     uint64                 `json:"stack_inuse"`
	StackSys       uint64                 `json:"stack_sys"`
	MSpanInuse     uint64                 `json:"mspan_inuse"`
	MSpanSys       uint64                 `json:"mspan_sys"`
	MCacheInuse    uint64                 `json:"mcache_inuse"`
	MCacheSys      uint64                 `json:"mcache_sys"`
	BuckHashSys    uint64                 `json:"buck_hash_sys"`
	GCSys          uint64                 `json:"gc_sys"`
	OtherSys       uint64                 `json:"other_sys"`
	NextGC         uint64                 `json:"next_gc"`
	LastGC         uint64                 `json:"last_gc"`
	PauseTotalNs   uint64                 `json:"pause_total_ns"`
	PauseNs        [256]uint64           `json:"pause_ns"`
	PauseEnd       [256]uint64           `json:"pause_end"`
	NumGC          uint32                 `json:"num_gc"`
	GCCPUFraction  float64                `json:"gc_cpu_fraction"`
	EnableGC       bool                   `json:"enable_gc"`
	DebugGC        bool                   `json:"debug_gc"`
}

var (
	startTime = time.Now()
	appVersion = "1.0.0" // This should be set at build time
)

// HealthCheck provides a comprehensive health check endpoint
func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Pragma", "no-cache")
	w.Header().Set("Expires", "0")

	// Check service health
	services := checkServices()

	// Get system metrics
	metrics := getSystemMetrics()

	// Determine overall status
	status := "healthy"
	for _, serviceStatus := range services {
		if serviceStatus != "healthy" {
			status = "degraded"
			break
		}
	}

	// Calculate uptime
	uptime := time.Since(startTime)

	health := HealthResponse{
		Status:    status,
		Timestamp: time.Now(),
		Services:  services,
		Metrics:   metrics,
		Version:   appVersion,
		Uptime:    uptime.String(),
	}

	// Set appropriate status code
	if status == "healthy" {
		w.WriteHeader(http.StatusOK)
	} else {
		w.WriteHeader(http.StatusServiceUnavailable)
	}

	json.NewEncoder(w).Encode(health)
}

// checkServices performs health checks on all services
func checkServices() map[string]string {
	services := make(map[string]string)

	// Database health check
	services["database"] = checkDatabaseHealth()

	// Redis health check (if configured)
	services["redis"] = checkRedisHealth()

	// Cache health check
	services["cache"] = checkCacheHealth()

	// API health check
	services["api"] = checkAPIHealth()

	// File system health check
	services["filesystem"] = checkFilesystemHealth()

	return services
}

// checkDatabaseHealth checks database connectivity and performance
func checkDatabaseHealth() string {
	return checkDatabaseHealthImpl()
}

// checkRedisHealth checks Redis connectivity and performance
func checkRedisHealth() string {
	return checkRedisHealthImpl()
}

// checkCacheHealth checks cache system health
func checkCacheHealth() string {
	return checkCacheHealthImpl()
}

// checkAPIHealth checks API endpoint health
func checkAPIHealth() string {
	return checkAPIHealthImpl()
}

// checkFilesystemHealth checks file system health
func checkFilesystemHealth() string {
	return checkFilesystemHealthImpl()
}

// getSystemMetrics collects comprehensive system metrics
func getSystemMetrics() map[string]interface{} {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	metrics := map[string]interface{}{
		"memory_usage": map[string]interface{}{
			"alloc":        m.Alloc,
			"total_alloc":  m.TotalAlloc,
			"sys":          m.Sys,
			"num_gc":       m.NumGC,
			"heap_alloc":   m.HeapAlloc,
			"heap_sys":     m.HeapSys,
			"heap_idle":    m.HeapIdle,
			"heap_inuse":   m.HeapInuse,
			"heap_released": m.HeapReleased,
			"heap_objects": m.HeapObjects,
		},
		"goroutines": runtime.NumGoroutine(),
		"cpu_count":  runtime.NumCPU(),
		"gc_stats": map[string]interface{}{
			"next_gc":        m.NextGC,
			"last_gc":        m.LastGC,
			"pause_total_ns": m.PauseTotalNs,
			"num_gc":         m.NumGC,
			"gc_cpu_fraction": m.GCCPUFraction,
		},
		"stack_stats": map[string]interface{}{
			"stack_inuse": m.StackInuse,
			"stack_sys":   m.StackSys,
		},
		"mspan_stats": map[string]interface{}{
			"mspan_inuse": m.MSpanInuse,
			"mspan_sys":   m.MSpanSys,
		},
		"mcache_stats": map[string]interface{}{
			"mcache_inuse": m.MCacheInuse,
			"mcache_sys":   m.MCacheSys,
		},
		"other_stats": map[string]interface{}{
			"buck_hash_sys": m.BuckHashSys,
			"gc_sys":        m.GCSys,
			"other_sys":     m.OtherSys,
		},
	}

	return metrics
}

// DetailedHealthCheck provides detailed health information for debugging
func DetailedHealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// Perform detailed health checks
	detailedHealth := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now(),
		"services":  checkServices(),
		"metrics":   getSystemMetrics(),
		"version":   appVersion,
		"uptime":    time.Since(startTime).String(),
		"environment": map[string]interface{}{
			"go_version": runtime.Version(),
			"os":         runtime.GOOS,
			"arch":       runtime.GOARCH,
			"cpu_count":  runtime.NumCPU(),
		},
		"detailed_checks": map[string]interface{}{
			"database": checkDetailedDatabaseHealth(),
			"redis":    checkDetailedRedisHealth(),
			"cache":    checkDetailedCacheHealth(),
			"api":      checkDetailedAPIHealth(),
		},
	}

	json.NewEncoder(w).Encode(detailedHealth)
}

// checkDetailedDatabaseHealth provides detailed database health information
func checkDetailedDatabaseHealth() map[string]interface{} {
	return checkDetailedDatabaseHealthImpl()
}

// checkDetailedRedisHealth provides detailed Redis health information
func checkDetailedRedisHealth() map[string]interface{} {
	return checkDetailedRedisHealthImpl()
}

// checkDetailedCacheHealth provides detailed cache health information
func checkDetailedCacheHealth() map[string]interface{} {
	return checkDetailedCacheHealthImpl()
}

// checkDetailedAPIHealth provides detailed API health information
func checkDetailedAPIHealth() map[string]interface{} {
	return checkDetailedAPIHealthImpl()
}
