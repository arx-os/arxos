package handlers

import (
	"net/http"
	"strconv"
	"time"

	"arxos/services"

	"github.com/go-chi/chi/v5"
)

// MonitoringHandler handles monitoring and metrics endpoints
type MonitoringHandler struct {
	monitoringService *services.MonitoringService
	loggingService    *services.LoggingService
}

// NewMonitoringHandler creates a new monitoring handler
func NewMonitoringHandler(monitoringService *services.MonitoringService, loggingService *services.LoggingService) *MonitoringHandler {
	return &MonitoringHandler{
		monitoringService: monitoringService,
		loggingService:    loggingService,
	}
}

// GetMetrics returns current system metrics
func (h *MonitoringHandler) GetMetrics(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/metrics",
		Method:    r.Method,
	}

	metrics := h.monitoringService.GetMetrics()

	// Add performance metrics
	performanceStats := h.loggingService.GetPerformanceStats()
	metrics["performance"] = performanceStats

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/metrics", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, metrics)
}

// GetHealthStatus returns system health status
func (h *MonitoringHandler) GetHealthStatus(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/health",
		Method:    r.Method,
	}

	health := h.monitoringService.GetHealthStatus()

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/health", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, health)
}

// GetAPIUsageStats returns API usage statistics
func (h *MonitoringHandler) GetAPIUsageStats(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/api-usage",
		Method:    r.Method,
	}

	period := r.URL.Query().Get("period")
	if period == "" {
		period = "24h"
	}

	stats, err := h.monitoringService.GetAPIUsageStats(period)
	if err != nil {
		h.loggingService.LogAPIError(ctx, err, http.StatusInternalServerError)
		h.monitoringService.RecordAPIError(r.Method, "/api/monitoring/api-usage", "database_error")
		respondWithError(w, http.StatusInternalServerError, "Failed to get API usage stats")
		return
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/api-usage", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, stats)
}

// GetExportJobStats returns export job statistics
func (h *MonitoringHandler) GetExportJobStats(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/export-jobs",
		Method:    r.Method,
	}

	period := r.URL.Query().Get("period")
	if period == "" {
		period = "24h"
	}

	stats, err := h.monitoringService.GetExportJobStats(period)
	if err != nil {
		h.loggingService.LogAPIError(ctx, err, http.StatusInternalServerError)
		h.monitoringService.RecordAPIError(r.Method, "/api/monitoring/export-jobs", "database_error")
		respondWithError(w, http.StatusInternalServerError, "Failed to get export job stats")
		return
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/export-jobs", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, stats)
}

// GetErrorRateStats returns error rate statistics
func (h *MonitoringHandler) GetErrorRateStats(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/error-rates",
		Method:    r.Method,
	}

	period := r.URL.Query().Get("period")
	if period == "" {
		period = "24h"
	}

	stats, err := h.monitoringService.GetErrorRateStats(period)
	if err != nil {
		h.loggingService.LogAPIError(ctx, err, http.StatusInternalServerError)
		h.monitoringService.RecordAPIError(r.Method, "/api/monitoring/error-rates", "database_error")
		respondWithError(w, http.StatusInternalServerError, "Failed to get error rate stats")
		return
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/error-rates", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, stats)
}

// GetSystemAlerts returns recent system alerts
func (h *MonitoringHandler) GetSystemAlerts(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/alerts",
		Method:    r.Method,
	}

	limitStr := r.URL.Query().Get("limit")
	limit := 50 // default limit
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	alerts, err := h.monitoringService.GetSystemAlerts(limit)
	if err != nil {
		h.loggingService.LogAPIError(ctx, err, http.StatusInternalServerError)
		h.monitoringService.RecordAPIError(r.Method, "/api/monitoring/alerts", "database_error")
		respondWithError(w, http.StatusInternalServerError, "Failed to get system alerts")
		return
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/alerts", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, alerts)
}

// GetPerformanceStats returns performance statistics
func (h *MonitoringHandler) GetPerformanceStats(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/performance",
		Method:    r.Method,
	}

	stats := h.loggingService.GetPerformanceStats()

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/performance", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, stats)
}

// GetLogs returns system logs
func (h *MonitoringHandler) GetLogs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/logs",
		Method:    r.Method,
	}

	// Parse filters
	filters := make(map[string]interface{})
	if level := r.URL.Query().Get("level"); level != "" {
		filters["level"] = level
	}
	if eventType := r.URL.Query().Get("event_type"); eventType != "" {
		filters["event_type"] = eventType
	}
	if userIDStr := r.URL.Query().Get("user_id"); userIDStr != "" {
		if userID, err := strconv.ParseUint(userIDStr, 10, 32); err == nil {
			filters["user_id"] = uint(userID)
		}
	}
	if startDateStr := r.URL.Query().Get("start_date"); startDateStr != "" {
		if startDate, err := time.Parse("2006-01-02", startDateStr); err == nil {
			filters["start_date"] = startDate
		}
	}
	if endDateStr := r.URL.Query().Get("end_date"); endDateStr != "" {
		if endDate, err := time.Parse("2006-01-02", endDateStr); err == nil {
			filters["end_date"] = endDate
		}
	}

	// Parse pagination
	limitStr := r.URL.Query().Get("limit")
	limit := 100 // default limit
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	offsetStr := r.URL.Query().Get("offset")
	offset := 0
	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	logs, err := h.loggingService.GetLogs(filters, limit, offset)
	if err != nil {
		h.loggingService.LogAPIError(ctx, err, http.StatusInternalServerError)
		h.monitoringService.RecordAPIError(r.Method, "/api/monitoring/logs", "database_error")
		respondWithError(w, http.StatusInternalServerError, "Failed to get logs")
		return
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/logs", "200", "admin", time.Since(start))

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"logs":   logs,
		"limit":  limit,
		"offset": offset,
		"total":  len(logs),
	})
}

// ExportLogs exports logs to a file
func (h *MonitoringHandler) ExportLogs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  "/api/monitoring/logs/export",
		Method:    r.Method,
	}

	// Parse filters
	filters := make(map[string]interface{})
	if level := r.URL.Query().Get("level"); level != "" {
		filters["level"] = level
	}
	if eventType := r.URL.Query().Get("event_type"); eventType != "" {
		filters["event_type"] = eventType
	}
	if userIDStr := r.URL.Query().Get("user_id"); userIDStr != "" {
		if userID, err := strconv.ParseUint(userIDStr, 10, 32); err == nil {
			filters["user_id"] = uint(userID)
		}
	}
	if startDateStr := r.URL.Query().Get("start_date"); startDateStr != "" {
		if startDate, err := time.Parse("2006-01-02", startDateStr); err == nil {
			filters["start_date"] = startDate
		}
	}
	if endDateStr := r.URL.Query().Get("end_date"); endDateStr != "" {
		if endDate, err := time.Parse("2006-01-02", endDateStr); err == nil {
			filters["end_date"] = endDate
		}
	}

	format := r.URL.Query().Get("format")
	if format == "" {
		format = "json"
	}

	// Set response headers
	filename := "logs_" + time.Now().Format("2006-01-02_15-04-05")
	switch format {
	case "json":
		w.Header().Set("Content-Type", "application/json")
		filename += ".json"
	case "csv":
		w.Header().Set("Content-Type", "text/csv")
		filename += ".csv"
	default:
		respondWithError(w, http.StatusBadRequest, "Unsupported format")
		return
	}
	w.Header().Set("Content-Disposition", "attachment; filename="+filename)

	// Export logs
	err := h.loggingService.ExportLogs(filters, format, w)
	if err != nil {
		h.loggingService.LogAPIError(ctx, err, http.StatusInternalServerError)
		h.monitoringService.RecordAPIError(r.Method, "/api/monitoring/logs/export", "export_error")
		respondWithError(w, http.StatusInternalServerError, "Failed to export logs")
		return
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, http.StatusOK, time.Since(start), 0)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, "/api/monitoring/logs/export", "200", "admin", time.Since(start))
}

// RegisterMonitoringRoutes registers monitoring routes
func (h *MonitoringHandler) RegisterMonitoringRoutes(r chi.Router) {
	r.Get("/metrics", h.GetMetrics)
	r.Get("/health", h.GetHealthStatus)
	r.Get("/api-usage", h.GetAPIUsageStats)
	r.Get("/export-jobs", h.GetExportJobStats)
	r.Get("/error-rates", h.GetErrorRateStats)
	r.Get("/alerts", h.GetSystemAlerts)
	r.Get("/performance", h.GetPerformanceStats)
	r.Get("/logs", h.GetLogs)
	r.Get("/logs/export", h.ExportLogs)
}
