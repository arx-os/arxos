package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/arx-os/arxos/internal/application/services"
	"github.com/arx-os/arxos/internal/domain/analytics"
)

// AnalyticsHandler handles HTTP requests for analytics operations
type AnalyticsHandler struct {
	analyticsService *services.AnalyticsApplicationService
}

// NewAnalyticsHandler creates a new analytics handler
func NewAnalyticsHandler(analyticsService *services.AnalyticsApplicationService) *AnalyticsHandler {
	return &AnalyticsHandler{
		analyticsService: analyticsService,
	}
}

// ProcessDataPoint handles POST /api/analytics/data-point
func (h *AnalyticsHandler) ProcessDataPoint(w http.ResponseWriter, r *http.Request) {
	var dataPoint analytics.EnergyDataPoint
	if err := json.NewDecoder(r.Body).Decode(&dataPoint); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if err := h.analyticsService.ProcessDataPoint(r.Context(), dataPoint); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// GenerateReport handles POST /api/analytics/reports
func (h *AnalyticsHandler) GenerateReport(w http.ResponseWriter, r *http.Request) {
	var req struct {
		ReportType string                 `json:"report_type"`
		Parameters map[string]interface{} `json:"parameters"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	report, err := h.analyticsService.GenerateReport(r.Context(), req.ReportType, req.Parameters)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(report)
}

// GetRecommendations handles GET /api/analytics/recommendations/{building_id}
func (h *AnalyticsHandler) GetRecommendations(w http.ResponseWriter, r *http.Request) {
	buildingID := r.URL.Path[len("/api/analytics/recommendations/"):]
	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	recommendations, err := h.analyticsService.GetOptimizationRecommendations(r.Context(), buildingID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(recommendations)
}

// GetForecast handles GET /api/analytics/forecast
func (h *AnalyticsHandler) GetForecast(w http.ResponseWriter, r *http.Request) {
	metric := r.URL.Query().Get("metric")
	if metric == "" {
		http.Error(w, "Metric parameter is required", http.StatusBadRequest)
		return
	}

	durationStr := r.URL.Query().Get("duration")
	if durationStr == "" {
		http.Error(w, "Duration parameter is required", http.StatusBadRequest)
		return
	}

	duration, err := strconv.ParseInt(durationStr, 10, 64)
	if err != nil {
		http.Error(w, "Invalid duration parameter", http.StatusBadRequest)
		return
	}

	forecast, err := h.analyticsService.GetForecast(r.Context(), metric, duration)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(forecast)
}

// GetAnomalies handles GET /api/analytics/anomalies
func (h *AnalyticsHandler) GetAnomalies(w http.ResponseWriter, r *http.Request) {
	severity := r.URL.Query().Get("severity")

	anomalies, err := h.analyticsService.GetAnomalies(r.Context(), severity)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(anomalies)
}

// GetAlerts handles GET /api/analytics/alerts
func (h *AnalyticsHandler) GetAlerts(w http.ResponseWriter, r *http.Request) {
	status := r.URL.Query().Get("status")

	alerts, err := h.analyticsService.GetAlerts(r.Context(), status)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(alerts)
}

// GetMetrics handles GET /api/analytics/metrics
func (h *AnalyticsHandler) GetMetrics(w http.ResponseWriter, r *http.Request) {
	metrics, err := h.analyticsService.GetMetrics(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// UpdateMetrics handles POST /api/analytics/metrics/update
func (h *AnalyticsHandler) UpdateMetrics(w http.ResponseWriter, r *http.Request) {
	if err := h.analyticsService.UpdateMetrics(r.Context()); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}
