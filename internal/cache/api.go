package cache

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// PerformanceAPI provides HTTP API for performance management
type PerformanceAPI struct {
	manager *PerformanceManager
}

// NewPerformanceAPI creates a new performance API
func NewPerformanceAPI(manager *PerformanceManager) *PerformanceAPI {
	return &PerformanceAPI{
		manager: manager,
	}
}

// RegisterRoutes registers performance API routes
func (api *PerformanceAPI) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/v1/performance/metrics", api.handleGetMetrics)
	mux.HandleFunc("/api/v1/performance/report", api.handleGetReport)
	mux.HandleFunc("/api/v1/performance/modules", api.handleGetModules)
	mux.HandleFunc("/api/v1/performance/modules/", api.handleGetModule)
	mux.HandleFunc("/api/v1/performance/alerts", api.handleGetAlerts)
	mux.HandleFunc("/api/v1/performance/alerts/", api.handleResolveAlert)
	mux.HandleFunc("/api/v1/performance/optimize", api.handleOptimize)
	mux.HandleFunc("/api/v1/performance/cache", api.handleCacheStats)
	mux.HandleFunc("/api/v1/performance/pool", api.handlePoolStats)
}

// handleGetMetrics returns performance metrics
func (api *PerformanceAPI) handleGetMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metricName := r.URL.Query().Get("metric")
	limitStr := r.URL.Query().Get("limit")

	limit := 100
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	var metrics []PerformanceMetric
	if metricName != "" {
		metrics = api.manager.GetPerformanceMonitor().GetMetrics(metricName, limit)
	} else {
		// Return system metrics
		systemMetrics := api.manager.GetPerformanceMonitor().GetSystemMetrics()
		metrics = []PerformanceMetric{
			{
				Name:      "cpu_usage",
				Value:     systemMetrics.CPUUsage,
				Unit:      "percent",
				Timestamp: time.Now(),
				Tags:      map[string]string{"type": "system"},
			},
			{
				Name:      "memory_usage",
				Value:     float64(systemMetrics.MemoryUsage),
				Unit:      "MB",
				Timestamp: time.Now(),
				Tags:      map[string]string{"type": "system"},
			},
		}
	}

	api.writeJSON(w, metrics)
}

// handleGetReport returns a comprehensive performance report
func (api *PerformanceAPI) handleGetReport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	report := api.manager.GeneratePerformanceReport()
	api.writeJSON(w, report)
}

// handleGetModules returns performance metrics for all modules
func (api *PerformanceAPI) handleGetModules(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	modules := api.manager.GetAllModulePerformance()
	api.writeJSON(w, modules)
}

// handleGetModule returns performance metrics for a specific module
func (api *PerformanceAPI) handleGetModule(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract module name from URL path
	moduleName := r.URL.Path[len("/api/v1/performance/modules/"):]
	if moduleName == "" {
		http.Error(w, "Module name required", http.StatusBadRequest)
		return
	}

	module, exists := api.manager.GetModulePerformance(moduleName)
	if !exists {
		http.Error(w, "Module not found", http.StatusNotFound)
		return
	}

	api.writeJSON(w, module)
}

// handleGetAlerts returns performance alerts
func (api *PerformanceAPI) handleGetAlerts(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	resolvedStr := r.URL.Query().Get("resolved")
	resolved := false
	if resolvedStr == "true" {
		resolved = true
	}

	alerts := api.manager.GetPerformanceMonitor().GetAlerts(resolved)
	api.writeJSON(w, alerts)
}

// handleResolveAlert resolves a performance alert
func (api *PerformanceAPI) handleResolveAlert(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract alert ID from URL path
	alertID := r.URL.Path[len("/api/v1/performance/alerts/"):]
	if alertID == "" {
		http.Error(w, "Alert ID required", http.StatusBadRequest)
		return
	}

	err := api.manager.GetPerformanceMonitor().ResolveAlert(alertID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	api.writeJSON(w, map[string]string{"status": "resolved"})
}

// handleOptimize optimizes performance for a module
func (api *PerformanceAPI) handleOptimize(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		ModuleName string `json:"module_name"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.manager.OptimizeModule(req.ModuleName)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	api.writeJSON(w, map[string]string{"status": "optimized"})
}

// handleCacheStats returns cache statistics
func (api *PerformanceAPI) handleCacheStats(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if api.manager.GetCache() == nil {
		http.Error(w, "Cache not available", http.StatusServiceUnavailable)
		return
	}

	metrics := api.manager.GetCache().GetMetrics()
	api.writeJSON(w, metrics)
}

// handlePoolStats returns resource pool statistics
func (api *PerformanceAPI) handlePoolStats(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if api.manager.GetResourcePool() == nil {
		http.Error(w, "Resource pool not available", http.StatusServiceUnavailable)
		return
	}

	metrics := api.manager.GetResourcePool().GetMetrics()
	api.writeJSON(w, metrics)
}

// writeJSON writes JSON response
func (api *PerformanceAPI) writeJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(data); err != nil {
		logger.Error("Failed to encode JSON response: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}
