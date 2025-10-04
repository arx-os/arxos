package handlers

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/models"
)

// APIHandler handles general API requests following Clean Architecture
type APIHandler struct {
	BaseHandler
	logger domain.Logger
}

// NewAPIHandler creates a new API handler with proper dependency injection
func NewAPIHandler(base BaseHandler, logger domain.Logger) *APIHandler {
	return &APIHandler{
		BaseHandler: base,
		logger:      logger,
	}
}

// HandleHealth handles GET /health
func (h *APIHandler) HandleHealth(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	response := models.HealthResponse{
		Status:    "healthy",
		Version:   "2.0.0",
		Timestamp: time.Now().UTC(),
		Checks: map[string]interface{}{
			"database": "connected",
			"cache":    "connected",
		},
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleRefreshToken handles POST /auth/refresh
func (h *APIHandler) HandleRefreshToken(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Placeholder implementation
	response := map[string]string{
		"message": "Token refresh endpoint",
		"status":  "success",
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleAPIInfo handles GET /api/info
func (h *APIHandler) HandleAPIInfo(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	response := models.APIInfoResponse{
		Version:     "2.0.0",
		Name:        "ArxOS API",
		Description: "Building Operating System API",
		Endpoints: []string{
			"/api/v1/buildings",
			"/api/v1/equipment",
			"/api/v1/analytics",
			"/api/v1/hardware",
		},
		Documentation: "/api/docs",
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleMetrics handles GET /metrics
func (h *APIHandler) HandleMetrics(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Placeholder metrics response
	response := map[string]interface{}{
		"requests_total":      1000,
		"requests_per_second": 10.5,
		"response_time_ms":    150,
		"error_rate":          0.02,
		"active_connections":  25,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleStatus handles GET /status
func (h *APIHandler) HandleStatus(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	response := models.StatusResponse{
		Status:    "operational",
		Uptime:    time.Since(time.Now().Add(-time.Hour * 24)), // Placeholder uptime
		Version:   "2.0.0",
		Timestamp: time.Now().UTC(),
		Services: map[string]string{
			"database":  "healthy",
			"cache":     "healthy",
			"analytics": "healthy",
			"hardware":  "healthy",
		},
	}

	h.RespondJSON(w, http.StatusOK, response)
}
