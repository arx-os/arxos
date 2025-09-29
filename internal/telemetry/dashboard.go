package telemetry

import (
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Dashboard provides a web interface for observability data
type Dashboard struct {
	config *ObservabilityConfig
	server *http.Server
}

// DashboardData represents data displayed on the dashboard
type DashboardData struct {
	ServiceName  string                 `json:"service_name"`
	Environment  string                 `json:"environment"`
	Timestamp    time.Time              `json:"timestamp"`
	Metrics      map[string]interface{} `json:"metrics"`
	RecentTraces []*Span                `json:"recent_traces"`
	SystemInfo   SystemInfo             `json:"system_info"`
	Alerts       []Alert                `json:"alerts"`
}

// SystemInfo contains system information
type SystemInfo struct {
	Uptime         time.Duration `json:"uptime"`
	MemoryUsage    int64         `json:"memory_usage"`
	CPUUsage       float64       `json:"cpu_usage"`
	GoroutineCount int           `json:"goroutine_count"`
}

// Alert represents a system alert
type Alert struct {
	ID        string    `json:"id"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
	Resolved  bool      `json:"resolved"`
}

var dashboardHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArxOS Observability Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { margin-bottom: 15px; }
        .metric-label { font-size: 14px; color: #666; margin-bottom: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #333; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert.warning { background: #fff3cd; border: 1px solid #ffeaa7; }
        .alert.error { background: #f8d7da; border: 1px solid #f5c6cb; }
        .alert.info { background: #d1ecf1; border: 1px solid #b8daff; }
        .trace { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }
        .trace-name { font-weight: bold; }
        .trace-duration { color: #666; font-size: 12px; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status.healthy { background: #d4edda; color: #155724; }
        .status.warning { background: #fff3cd; color: #856404; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ArxOS Observability Dashboard</h1>
            <p>Service: <strong>{{.ServiceName}}</strong> | Environment: <strong>{{.Environment}}</strong> | 
               Last Updated: {{.Timestamp.Format "2006-01-02 15:04:05"}}</p>
            <button class="refresh-btn" onclick="location.reload()">Refresh</button>
        </div>

        <div class="grid">
            <div class="card">
                <h3>System Metrics</h3>
                <div class="metric">
                    <div class="metric-label">Uptime</div>
                    <div class="metric-value">{{.SystemInfo.Uptime}}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Memory Usage</div>
                    <div class="metric-value">{{.SystemInfo.MemoryUsage}} MB</div>
                </div>
                <div class="metric">
                    <div class="metric-label">CPU Usage</div>
                    <div class="metric-value">{{printf "%.1f" .SystemInfo.CPUUsage}}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Goroutines</div>
                    <div class="metric-value">{{.SystemInfo.GoroutineCount}}</div>
                </div>
            </div>

            <div class="card">
                <h3>Application Metrics</h3>
                {{range $name, $value := .Metrics}}
                <div class="metric">
                    <div class="metric-label">{{$name}}</div>
                    <div class="metric-value">{{$value}}</div>
                </div>
                {{end}}
            </div>

            <div class="card">
                <h3>Recent Traces</h3>
                {{range .RecentTraces}}
                <div class="trace">
                    <div class="trace-name">{{.name}}</div>
                    <div class="trace-duration">Duration: {{if .Duration}}{{.Duration}}{{else}}In Progress{{end}}</div>
                    <div class="trace-duration">Trace ID: {{.TraceID}}</div>
                </div>
                {{end}}
            </div>

            <div class="card">
                <h3>Alerts</h3>
                {{if .Alerts}}
                {{range .Alerts}}
                <div class="alert {{.Level}}">
                    <strong>{{.Level | title}}:</strong> {{.Message}}
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        {{.Timestamp.Format "2006-01-02 15:04:05"}}
                    </div>
                </div>
                {{end}}
                {{else}}
                <p>No active alerts</p>
                {{end}}
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>`

// NewDashboard creates a new observability dashboard
func NewDashboard(config *ObservabilityConfig) *Dashboard {
	return &Dashboard{
		config: config,
	}
}

// Start starts the dashboard HTTP server
func (d *Dashboard) Start() error {
	mux := http.NewServeMux()
	mux.HandleFunc("/", d.handleDashboard)
	mux.HandleFunc("/api/data", d.handleAPIData)
	mux.HandleFunc("/health", d.handleHealth)

	d.server = &http.Server{
		Addr:    ":8090", // Dashboard port
		Handler: mux,
	}

	go func() {
		logger.Info("Observability dashboard starting on :8090")
		if err := d.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Dashboard server error: %v", err)
		}
	}()

	return nil
}

// Stop stops the dashboard server
func (d *Dashboard) Stop() error {
	if d.server != nil {
		return d.server.Close()
	}
	return nil
}

// handleDashboard serves the main dashboard page
func (d *Dashboard) handleDashboard(w http.ResponseWriter, r *http.Request) {
	tmpl, err := template.New("dashboard").Parse(dashboardHTML)
	if err != nil {
		http.Error(w, "Template error", http.StatusInternalServerError)
		return
	}

	data := d.gatherDashboardData()
	w.Header().Set("Content-Type", "text/html")
	tmpl.Execute(w, data)
}

// handleAPIData serves dashboard data as JSON
func (d *Dashboard) handleAPIData(w http.ResponseWriter, r *http.Request) {
	data := d.gatherDashboardData()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// handleHealth serves health check endpoint
func (d *Dashboard) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now(),
		"service":   d.config.ServiceName,
	})
}

// gatherDashboardData collects data for the dashboard
func (d *Dashboard) gatherDashboardData() *DashboardData {
	data := &DashboardData{
		ServiceName: d.config.ServiceName,
		Environment: d.config.Environment,
		Timestamp:   time.Now(),
		Metrics:     make(map[string]interface{}),
		SystemInfo:  d.getSystemInfo(),
		Alerts:      d.getActiveAlerts(),
	}

	// Gather metrics from the metrics collector
	if extendedInstance != nil && extendedInstance.metrics != nil {
		counters := extendedInstance.metrics.GetCounters()
		gauges := extendedInstance.metrics.GetGauges()
		histos := extendedInstance.metrics.GetHistograms()

		// Add some key metrics to display
		for name, counter := range counters {
			data.Metrics[name] = counter.Value
		}

		for name, gauge := range gauges {
			data.Metrics[name] = gauge.Value
		}

		for name, histo := range histos {
			data.Metrics[name+"_count"] = histo.Count
			data.Metrics[name+"_sum"] = histo.Sum
		}
	}

	// Gather recent traces
	if extendedInstance != nil && extendedInstance.tracer != nil {
		data.RecentTraces = d.getRecentTraces()
	}

	return data
}

// getSystemInfo returns current system information
func (d *Dashboard) getSystemInfo() SystemInfo {
	// This would typically use runtime metrics
	return SystemInfo{
		Uptime:         time.Since(time.Now().Add(-time.Hour)), // Placeholder
		MemoryUsage:    128,                                    // MB - placeholder
		CPUUsage:       15.5,                                   // % - placeholder
		GoroutineCount: 45,                                     // placeholder
	}
}

// getActiveAlerts returns current active alerts
func (d *Dashboard) getActiveAlerts() []Alert {
	// This would typically check various system conditions
	alerts := []Alert{}

	// Example alert logic
	if extendedInstance != nil && extendedInstance.metrics != nil {
		counters := extendedInstance.metrics.GetCounters()

		// Check for high error rates
		for name, counter := range counters {
			if name == "http_requests_total,status=500" && counter.Value > 10 {
				alerts = append(alerts, Alert{
					ID:        "high_error_rate",
					Level:     "error",
					Message:   fmt.Sprintf("High error rate detected: %.0f errors", counter.Value),
					Timestamp: time.Now(),
					Resolved:  false,
				})
			}
		}
	}

	return alerts
}

// getRecentTraces returns recent trace data
func (d *Dashboard) getRecentTraces() []*Span {
	if extendedInstance == nil || extendedInstance.tracer == nil {
		return []*Span{}
	}

	// For now, return empty traces since we don't have direct access to spans
	// In a real implementation, the tracer would provide a method to get recent spans
	return []*Span{}
}
