package handlers

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
)

// APIHandler handles general API requests following Clean Architecture principles
type APIHandler struct {
	*BaseHandler
}

// NewAPIHandler creates a new API handler with dependency injection
func NewAPIHandler(services *types.Services, logger logger.Logger) *APIHandler {
	return &APIHandler{
		BaseHandler: NewBaseHandler(services, logger),
	}
}

// HandleHealth handles GET /health - health check endpoint
func (h *APIHandler) HandleHealth(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, "health_check")
		h.logger.Info("Health check completed", "duration", time.Since(start))
	}()

	// Check database connectivity
	dbStatus := "connected"
	if err := h.services.Database.Ping(); err != nil {
		dbStatus = "disconnected"
		h.logger.Error("Database health check failed", "error", err)
	}

	// Check cache connectivity
	cacheStatus := "connected"
	if err := h.services.Cache.Ping(); err != nil {
		cacheStatus = "disconnected"
		h.logger.Error("Cache health check failed", "error", err)
	}

	response := map[string]interface{}{
		"status":    "healthy",
		"version":   "2.0.0",
		"timestamp": time.Now().UTC(),
		"checks": map[string]interface{}{
			"database": dbStatus,
			"cache":    cacheStatus,
		},
	}

	h.WriteSuccessResponse(w, response)
}

// HandleVersion handles GET /version - version information endpoint
func (h *APIHandler) HandleVersion(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "version_check")

	response := map[string]interface{}{
		"version":    "2.0.0",
		"build_time": "2024-09-29T09:00:00Z",
		"commit":     "main",
		"go_version": "1.21",
		"features": []string{
			"clean_architecture",
			"websocket_support",
			"dependency_injection",
			"postgis_spatial",
		},
	}

	h.WriteSuccessResponse(w, response)
}

// HandleMetrics handles GET /metrics - metrics endpoint for monitoring
func (h *APIHandler) HandleMetrics(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "metrics")

	// Get metrics from services
	metrics := map[string]interface{}{
		"timestamp": time.Now().UTC(),
		"services": map[string]interface{}{
			"building": map[string]interface{}{
				"total_buildings": h.getBuildingCount(),
				"status":          "active",
			},
			"equipment": map[string]interface{}{
				"total_equipment": h.getEquipmentCount(),
				"status":          "active",
			},
			"spatial": map[string]interface{}{
				"total_queries": h.getSpatialQueryCount(),
				"status":        "active",
			},
		},
	}

	h.WriteSuccessResponse(w, metrics)
}

// Helper methods for metrics
func (h *APIHandler) getBuildingCount() int {
	// This would call the domain service
	// For now, return a placeholder
	return 0
}

func (h *APIHandler) getEquipmentCount() int {
	// This would call the domain service
	// For now, return a placeholder
	return 0
}

func (h *APIHandler) getSpatialQueryCount() int {
	// This would call the domain service
	// For now, return a placeholder
	return 0
}
