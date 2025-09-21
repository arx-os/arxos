package api

import (
	"net/http"

	"github.com/arx-os/arxos/internal/metrics"
)

// HandleMetrics returns current metrics in JSON format
func (s *Server) HandleMetrics(w http.ResponseWriter, r *http.Request) {
	// Only allow GET requests
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Get metrics snapshot
	collector := metrics.GetCollector()
	snapshot := collector.GetSnapshot()

	// Respond with metrics
	s.respondJSON(w, http.StatusOK, snapshot)
}

// HandleMetricsPrometheus returns metrics in Prometheus format
func (s *Server) HandleMetricsPrometheus(w http.ResponseWriter, r *http.Request) {
	// Only allow GET requests
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Set content type for Prometheus
	w.Header().Set("Content-Type", "text/plain; version=0.0.4")

	// Get Prometheus formatted metrics
	collector := metrics.GetCollector()
	prometheusData := collector.FormatPrometheus()

	// Write metrics
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(prometheusData))
}

// MetricsResponse represents the metrics API response
type MetricsResponse struct {
	Uptime    string                 `json:"uptime"`
	Metrics   map[string]interface{} `json:"metrics"`
	System    SystemMetrics          `json:"system"`
	Timestamp int64                  `json:"timestamp"`
}

// SystemMetrics contains system-level metrics
type SystemMetrics struct {
	Goroutines       int     `json:"goroutines"`
	MemoryMB         float64 `json:"memory_mb"`
	CPUPercent       float64 `json:"cpu_percent"`
	OpenConnections  int     `json:"open_connections"`
	ActiveRequests   int     `json:"active_requests"`
}