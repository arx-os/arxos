package gateway

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// HealthMonitor monitors the health of services
type HealthMonitor struct {
	config   HealthConfig
	logger   *zap.Logger
	services map[string]*ServiceHealth
	mu       sync.RWMutex
	metrics  *HealthMetrics
	alerting *HealthAlerting
}

// HealthConfig defines health monitoring configuration
type HealthConfig struct {
	Enabled          bool                  `yaml:"enabled"`
	CheckInterval    time.Duration         `yaml:"check_interval"`
	Timeout          time.Duration         `yaml:"timeout"`
	FailureThreshold int                   `yaml:"failure_threshold"`
	SuccessThreshold int                   `yaml:"success_threshold"`
	Services         []ServiceHealthConfig `yaml:"services"`
	Alerting         HealthAlertingConfig  `yaml:"alerting"`
}

// ServiceHealthConfig defines health check configuration for a service
type ServiceHealthConfig struct {
	Name             string            `yaml:"name"`
	URL              string            `yaml:"url"`
	HealthEndpoint   string            `yaml:"health_endpoint"`
	Timeout          time.Duration     `yaml:"timeout"`
	Interval         time.Duration     `yaml:"interval"`
	FailureThreshold int               `yaml:"failure_threshold"`
	SuccessThreshold int               `yaml:"success_threshold"`
	Headers          map[string]string `yaml:"headers"`
	ExpectedStatus   int               `yaml:"expected_status"`
}

// ServiceHealth represents the health status of a service
type ServiceHealth struct {
	Name                 string
	URL                  string
	Status               HealthStatus
	LastCheck            time.Time
	LastSuccess          time.Time
	LastFailure          time.Time
	ResponseTime         time.Duration
	FailureCount         int
	SuccessCount         int
	ConsecutiveFailures  int
	ConsecutiveSuccesses int
	Error                string
	Details              map[string]interface{}
	mu                   sync.RWMutex
}

// HealthStatus represents the health status
type HealthStatus string

const (
	HealthStatusHealthy   HealthStatus = "healthy"
	HealthStatusUnhealthy HealthStatus = "unhealthy"
	HealthStatusUnknown   HealthStatus = "unknown"
	HealthStatusDegraded  HealthStatus = "degraded"
)

// HealthMetrics holds health monitoring metrics
type HealthMetrics struct {
	statusGauge            *prometheus.GaugeVec
	responseTimeHistogram  *prometheus.HistogramVec
	failureCounter         *prometheus.CounterVec
	successCounter         *prometheus.CounterVec
	checkDurationHistogram *prometheus.HistogramVec
}

// HealthAlerting handles health alerts
type HealthAlerting struct {
	config HealthAlertingConfig
	logger *zap.Logger
}

// HealthAlertingConfig defines alerting configuration
type HealthAlertingConfig struct {
	Enabled           bool     `yaml:"enabled"`
	AlertEndpoint     string   `yaml:"alert_endpoint"`
	AlertToken        string   `yaml:"alert_token"`
	AlertChannels     []string `yaml:"alert_channels"`
	FailureThreshold  int      `yaml:"failure_threshold"`
	RecoveryThreshold int      `yaml:"recovery_threshold"`
}

// NewHealthMonitor creates a new health monitor
func NewHealthMonitor(config HealthConfig) (*HealthMonitor, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	monitor := &HealthMonitor{
		config:   config,
		logger:   logger,
		services: make(map[string]*ServiceHealth),
		alerting: &HealthAlerting{
			config: config.Alerting,
			logger: logger,
		},
	}

	// Initialize metrics
	monitor.initializeMetrics()

	// Initialize services
	for _, serviceConfig := range config.Services {
		monitor.addService(serviceConfig)
	}

	// Start monitoring if enabled
	if config.Enabled {
		go monitor.startMonitoring()
	}

	return monitor, nil
}

// initializeMetrics initializes health monitoring metrics
func (hm *HealthMonitor) initializeMetrics() {
	hm.metrics = &HealthMetrics{
		statusGauge: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_service_health_status",
				Help: "Service health status (0=unknown, 1=healthy, 2=degraded, 3=unhealthy)",
			},
			[]string{"service"},
		),
		responseTimeHistogram: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_service_health_response_time_seconds",
				Help:    "Service health check response time in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service"},
		),
		failureCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_service_health_failures_total",
				Help: "Total service health check failures",
			},
			[]string{"service"},
		),
		successCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_service_health_successes_total",
				Help: "Total service health check successes",
			},
			[]string{"service"},
		),
		checkDurationHistogram: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_service_health_check_duration_seconds",
				Help:    "Service health check duration in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service"},
		),
	}
}

// addService adds a service to the health monitor
func (hm *HealthMonitor) addService(config ServiceHealthConfig) {
	service := &ServiceHealth{
		Name:    config.Name,
		URL:     config.URL,
		Status:  HealthStatusUnknown,
		Details: make(map[string]interface{}),
	}

	hm.mu.Lock()
	hm.services[config.Name] = service
	hm.mu.Unlock()

	// Start monitoring for this service
	go hm.monitorService(config)
}

// monitorService monitors a specific service
func (hm *HealthMonitor) monitorService(config ServiceHealthConfig) {
	ticker := time.NewTicker(config.Interval)
	defer ticker.Stop()

	for range ticker.C {
		hm.checkServiceHealth(config)
	}
}

// checkServiceHealth performs a health check for a service
func (hm *HealthMonitor) checkServiceHealth(config ServiceHealthConfig) {
	start := time.Now()

	// Create HTTP client with timeout
	client := &http.Client{
		Timeout: config.Timeout,
	}

	// Create request
	req, err := http.NewRequest("GET", config.HealthEndpoint, nil)
	if err != nil {
		hm.recordFailure(config.Name, fmt.Sprintf("Failed to create request: %v", err), time.Since(start))
		return
	}

	// Add headers
	for key, value := range config.Headers {
		req.Header.Set(key, value)
	}

	// Perform request
	resp, err := client.Do(req)
	duration := time.Since(start)

	if err != nil {
		hm.recordFailure(config.Name, fmt.Sprintf("Request failed: %v", err), duration)
		return
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode == config.ExpectedStatus {
		hm.recordSuccess(config.Name, duration)
	} else {
		hm.recordFailure(config.Name, fmt.Sprintf("Unexpected status code: %d", resp.StatusCode), duration)
	}
}

// recordSuccess records a successful health check
func (hm *HealthMonitor) recordSuccess(serviceName string, duration time.Duration) {
	hm.mu.Lock()
	service, exists := hm.services[serviceName]
	hm.mu.Unlock()

	if !exists {
		return
	}

	service.mu.Lock()
	defer service.mu.Unlock()

	service.LastCheck = time.Now()
	service.LastSuccess = time.Now()
	service.ResponseTime = duration
	service.SuccessCount++
	service.ConsecutiveSuccesses++
	service.ConsecutiveFailures = 0
	service.Error = ""

	// Update status based on consecutive successes
	if service.ConsecutiveSuccesses >= hm.config.SuccessThreshold {
		service.Status = HealthStatusHealthy
	}

	// Update metrics
	hm.metrics.successCounter.WithLabelValues(serviceName).Inc()
	hm.metrics.responseTimeHistogram.WithLabelValues(serviceName).Observe(duration.Seconds())
	hm.metrics.checkDurationHistogram.WithLabelValues(serviceName).Observe(duration.Seconds())

	// Update status gauge
	hm.updateStatusGauge(serviceName, service.Status)

	hm.logger.Debug("Service health check success",
		zap.String("service", serviceName),
		zap.Duration("duration", duration),
		zap.Int("consecutive_successes", service.ConsecutiveSuccesses),
	)
}

// recordFailure records a failed health check
func (hm *HealthMonitor) recordFailure(serviceName string, error string, duration time.Duration) {
	hm.mu.Lock()
	service, exists := hm.services[serviceName]
	hm.mu.Unlock()

	if !exists {
		return
	}

	service.mu.Lock()
	defer service.mu.Unlock()

	service.LastCheck = time.Now()
	service.LastFailure = time.Now()
	service.ResponseTime = duration
	service.FailureCount++
	service.ConsecutiveFailures++
	service.ConsecutiveSuccesses = 0
	service.Error = error

	// Update status based on consecutive failures
	if service.ConsecutiveFailures >= hm.config.FailureThreshold {
		service.Status = HealthStatusUnhealthy
		hm.alerting.sendAlert(serviceName, "Service unhealthy", error)
	} else if service.ConsecutiveFailures > 0 {
		service.Status = HealthStatusDegraded
	}

	// Update metrics
	hm.metrics.failureCounter.WithLabelValues(serviceName).Inc()
	hm.metrics.responseTimeHistogram.WithLabelValues(serviceName).Observe(duration.Seconds())
	hm.metrics.checkDurationHistogram.WithLabelValues(serviceName).Observe(duration.Seconds())

	// Update status gauge
	hm.updateStatusGauge(serviceName, service.Status)

	hm.logger.Warn("Service health check failure",
		zap.String("service", serviceName),
		zap.String("error", error),
		zap.Duration("duration", duration),
		zap.Int("consecutive_failures", service.ConsecutiveFailures),
	)
}

// updateStatusGauge updates the status gauge metric
func (hm *HealthMonitor) updateStatusGauge(serviceName string, status HealthStatus) {
	var value float64
	switch status {
	case HealthStatusUnknown:
		value = 0
	case HealthStatusHealthy:
		value = 1
	case HealthStatusDegraded:
		value = 2
	case HealthStatusUnhealthy:
		value = 3
	}

	hm.metrics.statusGauge.WithLabelValues(serviceName).Set(value)
}

// startMonitoring starts the health monitoring
func (hm *HealthMonitor) startMonitoring() {
	hm.logger.Info("Health monitoring started",
		zap.Int("services", len(hm.services)),
		zap.Duration("check_interval", hm.config.CheckInterval),
	)
}

// GetServiceHealth gets the health status of a service
func (hm *HealthMonitor) GetServiceHealth(serviceName string) (*ServiceHealth, bool) {
	hm.mu.RLock()
	defer hm.mu.RUnlock()

	service, exists := hm.services[serviceName]
	if !exists {
		return nil, false
	}

	service.mu.RLock()
	defer service.mu.RUnlock()

	// Create a copy to avoid race conditions
	health := &ServiceHealth{
		Name:                 service.Name,
		URL:                  service.URL,
		Status:               service.Status,
		LastCheck:            service.LastCheck,
		LastSuccess:          service.LastSuccess,
		LastFailure:          service.LastFailure,
		ResponseTime:         service.ResponseTime,
		FailureCount:         service.FailureCount,
		SuccessCount:         service.SuccessCount,
		ConsecutiveFailures:  service.ConsecutiveFailures,
		ConsecutiveSuccesses: service.ConsecutiveSuccesses,
		Error:                service.Error,
		Details:              make(map[string]interface{}),
	}

	// Copy details
	for key, value := range service.Details {
		health.Details[key] = value
	}

	return health, true
}

// GetAllHealthStatus gets the health status of all services
func (hm *HealthMonitor) GetAllHealthStatus() map[string]*ServiceHealth {
	hm.mu.RLock()
	defer hm.mu.RUnlock()

	status := make(map[string]*ServiceHealth)
	for name, service := range hm.services {
		if health, exists := hm.GetServiceHealth(name); exists {
			status[name] = health
		}
	}

	return status
}

// GetOverallHealth gets the overall health status
func (hm *HealthMonitor) GetOverallHealth() map[string]interface{} {
	allStatus := hm.GetAllHealthStatus()

	healthy := 0
	unhealthy := 0
	degraded := 0
	unknown := 0

	for _, status := range allStatus {
		switch status.Status {
		case HealthStatusHealthy:
			healthy++
		case HealthStatusUnhealthy:
			unhealthy++
		case HealthStatusDegraded:
			degraded++
		case HealthStatusUnknown:
			unknown++
		}
	}

	total := len(allStatus)
	overallStatus := HealthStatusHealthy
	if unhealthy > 0 {
		overallStatus = HealthStatusUnhealthy
	} else if degraded > 0 {
		overallStatus = HealthStatusDegraded
	}

	return map[string]interface{}{
		"overall_status": overallStatus,
		"total_services": total,
		"healthy":        healthy,
		"unhealthy":      unhealthy,
		"degraded":       degraded,
		"unknown":        unknown,
		"services":       allStatus,
	}
}

// sendAlert sends a health alert
func (ha *HealthAlerting) sendAlert(serviceName, title, message string) {
	if !ha.config.Enabled {
		return
	}

	ha.logger.Warn("Health alert",
		zap.String("service", serviceName),
		zap.String("title", title),
		zap.String("message", message),
	)

	// In a real implementation, you would send this to your alerting system
	// For now, we'll just log it
}

// UpdateConfig updates the health monitoring configuration
func (hm *HealthMonitor) UpdateConfig(config HealthConfig) error {
	hm.config = config
	hm.logger.Info("Health monitoring configuration updated")
	return nil
}

// GetHealthStats returns health monitoring statistics
func (hm *HealthMonitor) GetHealthStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":           hm.config.Enabled,
		"check_interval":    hm.config.CheckInterval,
		"timeout":           hm.config.Timeout,
		"failure_threshold": hm.config.FailureThreshold,
		"success_threshold": hm.config.SuccessThreshold,
		"services_count":    len(hm.services),
		"alerting_enabled":  hm.config.Alerting.Enabled,
	}
}
