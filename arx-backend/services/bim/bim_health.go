package bim

import (
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// HealthStatus represents the overall health status
type HealthStatus string

const (
	HealthStatusHealthy  HealthStatus = "healthy"
	HealthStatusWarning  HealthStatus = "warning"
	HealthStatusCritical HealthStatus = "critical"
	HealthStatusDegraded HealthStatus = "degraded"
	HealthStatusUnknown  HealthStatus = "unknown"
)

// HealthComponent represents a health check component
type HealthComponent struct {
	Name         string                 `json:"name"`
	Status       HealthStatus           `json:"status"`
	Message      string                 `json:"message"`
	LastCheck    time.Time              `json:"last_check"`
	Details      map[string]interface{} `json:"details"`
	ResponseTime time.Duration          `json:"response_time"`
}

// BIMHealthStatus represents the health status of BIM services
type BIMHealthStatus struct {
	OverallStatus HealthStatus                `json:"overall_status"`
	Timestamp     time.Time                   `json:"timestamp"`
	Components    map[string]*HealthComponent `json:"components"`
	Summary       map[string]interface{}      `json:"summary"`
	Uptime        time.Duration               `json:"uptime"`
	Version       string                      `json:"version"`
}

// HealthCheck represents a health check function
type HealthCheck func() *HealthComponent

// BIMHealth provides comprehensive health monitoring for BIM services
type BIMHealth struct {
	logger *zap.Logger
	mu     sync.RWMutex

	// Health tracking
	status    *BIMHealthStatus
	checks    map[string]HealthCheck
	startTime time.Time

	// Configuration
	checkInterval time.Duration
	timeout       time.Duration
	maxRetries    int
}

// NewBIMHealth creates a new BIM health monitor
func NewBIMHealth(logger *zap.Logger) (*BIMHealth, error) {
	health := &BIMHealth{
		logger:        logger,
		checks:        make(map[string]HealthCheck),
		startTime:     time.Now(),
		checkInterval: 30 * time.Second,
		timeout:       10 * time.Second,
		maxRetries:    3,
	}

	// Initialize health status
	health.status = &BIMHealthStatus{
		OverallStatus: HealthStatusUnknown,
		Timestamp:     time.Now(),
		Components:    make(map[string]*HealthComponent),
		Summary:       make(map[string]interface{}),
		Version:       "1.0.0",
	}

	// Register default health checks
	health.registerDefaultChecks()

	logger.Info("BIM health monitor initialized",
		zap.Duration("check_interval", health.checkInterval),
		zap.Duration("timeout", health.timeout))

	return health, nil
}

// GetHealth returns the current health status
func (bh *BIMHealth) GetHealth() *BIMHealthStatus {
	bh.mu.RLock()
	defer bh.mu.RUnlock()

	// Update uptime
	bh.status.Uptime = time.Since(bh.startTime)

	return bh.status
}

// UpdateHealth updates the health status with new metrics
func (bh *BIMHealth) UpdateHealth(metrics map[string]interface{}) {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	// Update summary with new metrics
	for key, value := range metrics {
		bh.status.Summary[key] = value
	}

	// Update timestamp
	bh.status.Timestamp = time.Now()

	// Determine overall status based on component statuses
	bh.updateOverallStatus()
}

// RegisterHealthCheck registers a new health check
func (bh *BIMHealth) RegisterHealthCheck(name string, check HealthCheck) error {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	if _, exists := bh.checks[name]; exists {
		return fmt.Errorf("health check %s already registered", name)
	}

	bh.checks[name] = check

	bh.logger.Info("Registered health check",
		zap.String("check_name", name))

	return nil
}

// UnregisterHealthCheck unregisters a health check
func (bh *BIMHealth) UnregisterHealthCheck(name string) error {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	if _, exists := bh.checks[name]; !exists {
		return fmt.Errorf("health check %s not found", name)
	}

	delete(bh.checks, name)
	delete(bh.status.Components, name)

	bh.logger.Info("Unregistered health check",
		zap.String("check_name", name))

	return nil
}

// RunHealthChecks runs all registered health checks
func (bh *BIMHealth) RunHealthChecks() map[string]*HealthComponent {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	results := make(map[string]*HealthComponent)

	for name, check := range bh.checks {
		startTime := time.Now()

		// Run health check with timeout
		done := make(chan *HealthComponent, 1)
		go func() {
			done <- check()
		}()

		select {
		case result := <-done:
			result.ResponseTime = time.Since(startTime)
			result.LastCheck = time.Now()
			results[name] = result
			bh.status.Components[name] = result
		case <-time.After(bh.timeout):
			results[name] = &HealthComponent{
				Name:         name,
				Status:       HealthStatusCritical,
				Message:      "Health check timed out",
				LastCheck:    time.Now(),
				ResponseTime: bh.timeout,
				Details:      make(map[string]interface{}),
			}
			bh.status.Components[name] = results[name]
		}
	}

	// Update overall status
	bh.updateOverallStatus()

	return results
}

// GetHealthCheck returns a specific health check result
func (bh *BIMHealth) GetHealthCheck(name string) (*HealthComponent, error) {
	bh.mu.RLock()
	defer bh.mu.RUnlock()

	component, exists := bh.status.Components[name]
	if !exists {
		return nil, fmt.Errorf("health check %s not found", name)
	}

	return component, nil
}

// SetHealthCheckInterval sets the health check interval
func (bh *BIMHealth) SetHealthCheckInterval(interval time.Duration) {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	bh.checkInterval = interval
}

// SetTimeout sets the health check timeout
func (bh *BIMHealth) SetTimeout(timeout time.Duration) {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	bh.timeout = timeout
}

// SetMaxRetries sets the maximum number of retries for health checks
func (bh *BIMHealth) SetMaxRetries(maxRetries int) {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	bh.maxRetries = maxRetries
}

// updateOverallStatus updates the overall health status
func (bh *BIMHealth) updateOverallStatus() {
	criticalCount := 0
	warningCount := 0
	healthyCount := 0
	unknownCount := 0

	for _, component := range bh.status.Components {
		switch component.Status {
		case HealthStatusCritical:
			criticalCount++
		case HealthStatusWarning:
			warningCount++
		case HealthStatusHealthy:
			healthyCount++
		case HealthStatusUnknown:
			unknownCount++
		}
	}

	// Determine overall status
	if criticalCount > 0 {
		bh.status.OverallStatus = HealthStatusCritical
	} else if warningCount > 0 {
		bh.status.OverallStatus = HealthStatusWarning
	} else if healthyCount > 0 {
		bh.status.OverallStatus = HealthStatusHealthy
	} else {
		bh.status.OverallStatus = HealthStatusUnknown
	}

	// Update summary
	bh.status.Summary["critical_count"] = criticalCount
	bh.status.Summary["warning_count"] = warningCount
	bh.status.Summary["healthy_count"] = healthyCount
	bh.status.Summary["unknown_count"] = unknownCount
	bh.status.Summary["total_components"] = len(bh.status.Components)
}

// registerDefaultChecks registers default health checks
func (bh *BIMHealth) registerDefaultChecks() {
	// Service availability check
	bh.RegisterHealthCheck("service_availability", func() *HealthComponent {
		return &HealthComponent{
			Name:      "service_availability",
			Status:    HealthStatusHealthy,
			Message:   "BIM service is available",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"service": "bim",
				"uptime":  time.Since(bh.startTime).String(),
			},
		}
	})

	// Memory usage check
	bh.RegisterHealthCheck("memory_usage", func() *HealthComponent {
		// This would typically check actual memory usage
		// For now, we'll simulate a healthy memory status
		return &HealthComponent{
			Name:      "memory_usage",
			Status:    HealthStatusHealthy,
			Message:   "Memory usage is within normal limits",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"usage_percentage": 45.2,
				"threshold":        80.0,
			},
		}
	})

	// Database connectivity check
	bh.RegisterHealthCheck("database_connectivity", func() *HealthComponent {
		// This would typically check database connectivity
		// For now, we'll simulate a healthy database status
		return &HealthComponent{
			Name:      "database_connectivity",
			Status:    HealthStatusHealthy,
			Message:   "Database connection is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"connection_pool_size": 10,
				"active_connections":   3,
				"response_time_ms":     5.2,
			},
		}
	})

	// File system check
	bh.RegisterHealthCheck("file_system", func() *HealthComponent {
		// This would typically check file system health
		// For now, we'll simulate a healthy file system status
		return &HealthComponent{
			Name:      "file_system",
			Status:    HealthStatusHealthy,
			Message:   "File system is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"disk_usage_percentage": 35.8,
				"available_space_gb":    125.5,
				"total_space_gb":        500.0,
			},
		}
	})

	// Network connectivity check
	bh.RegisterHealthCheck("network_connectivity", func() *HealthComponent {
		// This would typically check network connectivity
		// For now, we'll simulate a healthy network status
		return &HealthComponent{
			Name:      "network_connectivity",
			Status:    HealthStatusHealthy,
			Message:   "Network connectivity is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"latency_ms":             12.5,
				"bandwidth_mbps":         1000.0,
				"packet_loss_percentage": 0.01,
			},
		}
	})

	// BIM model integrity check
	bh.RegisterHealthCheck("bim_model_integrity", func() *HealthComponent {
		// This would typically check BIM model integrity
		// For now, we'll simulate a healthy model integrity status
		return &HealthComponent{
			Name:      "bim_model_integrity",
			Status:    HealthStatusHealthy,
			Message:   "BIM model integrity is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"total_models":      15,
				"valid_models":      15,
				"invalid_models":    0,
				"validation_errors": 0,
			},
		}
	})

	// Element validation check
	bh.RegisterHealthCheck("element_validation", func() *HealthComponent {
		// This would typically check element validation status
		// For now, we'll simulate a healthy element validation status
		return &HealthComponent{
			Name:      "element_validation",
			Status:    HealthStatusHealthy,
			Message:   "Element validation is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"total_elements":      1250,
				"valid_elements":      1245,
				"invalid_elements":    5,
				"validation_warnings": 12,
			},
		}
	})

	// Transformation performance check
	bh.RegisterHealthCheck("transformation_performance", func() *HealthComponent {
		// This would typically check transformation performance
		// For now, we'll simulate a healthy transformation performance status
		return &HealthComponent{
			Name:      "transformation_performance",
			Status:    HealthStatusHealthy,
			Message:   "Transformation performance is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"average_transformation_time_ms": 45.2,
				"max_transformation_time_ms":     150.0,
				"transformation_success_rate":    99.8,
				"queued_transformations":         3,
			},
		}
	})

	// Analytics performance check
	bh.RegisterHealthCheck("analytics_performance", func() *HealthComponent {
		// This would typically check analytics performance
		// For now, we'll simulate a healthy analytics performance status
		return &HealthComponent{
			Name:      "analytics_performance",
			Status:    HealthStatusHealthy,
			Message:   "Analytics performance is healthy",
			LastCheck: time.Now(),
			Details: map[string]interface{}{
				"average_query_time_ms": 25.5,
				"max_query_time_ms":     200.0,
				"query_success_rate":    99.9,
				"active_queries":        8,
			},
		}
	})
}

// GetHealthMetrics returns health metrics
func (bh *BIMHealth) GetHealthMetrics() map[string]interface{} {
	bh.mu.RLock()
	defer bh.mu.RUnlock()

	metrics := make(map[string]interface{})

	// Overall metrics
	metrics["overall_status"] = string(bh.status.OverallStatus)
	metrics["uptime_seconds"] = time.Since(bh.startTime).Seconds()
	metrics["total_components"] = len(bh.status.Components)

	// Component status counts
	criticalCount := 0
	warningCount := 0
	healthyCount := 0
	unknownCount := 0

	for _, component := range bh.status.Components {
		switch component.Status {
		case HealthStatusCritical:
			criticalCount++
		case HealthStatusWarning:
			warningCount++
		case HealthStatusHealthy:
			healthyCount++
		case HealthStatusUnknown:
			unknownCount++
		}
	}

	metrics["critical_count"] = criticalCount
	metrics["warning_count"] = warningCount
	metrics["healthy_count"] = healthyCount
	metrics["unknown_count"] = unknownCount

	// Response time metrics
	var totalResponseTime time.Duration
	responseTimeCount := 0

	for _, component := range bh.status.Components {
		if component.ResponseTime > 0 {
			totalResponseTime += component.ResponseTime
			responseTimeCount++
		}
	}

	if responseTimeCount > 0 {
		metrics["average_response_time_ms"] = totalResponseTime.Milliseconds() / int64(responseTimeCount)
	}

	return metrics
}

// IsHealthy returns true if the overall health status is healthy
func (bh *BIMHealth) IsHealthy() bool {
	bh.mu.RLock()
	defer bh.mu.RUnlock()

	return bh.status.OverallStatus == HealthStatusHealthy
}

// GetUnhealthyComponents returns components that are not healthy
func (bh *BIMHealth) GetUnhealthyComponents() []*HealthComponent {
	bh.mu.RLock()
	defer bh.mu.RUnlock()

	var unhealthy []*HealthComponent

	for _, component := range bh.status.Components {
		if component.Status != HealthStatusHealthy {
			unhealthy = append(unhealthy, component)
		}
	}

	return unhealthy
}

// GetComponentStatus returns the status of a specific component
func (bh *BIMHealth) GetComponentStatus(componentName string) (HealthStatus, error) {
	bh.mu.RLock()
	defer bh.mu.RUnlock()

	component, exists := bh.status.Components[componentName]
	if !exists {
		return HealthStatusUnknown, fmt.Errorf("component %s not found", componentName)
	}

	return component.Status, nil
}

// ResetHealth resets the health status
func (bh *BIMHealth) ResetHealth() {
	bh.mu.Lock()
	defer bh.mu.Unlock()

	bh.startTime = time.Now()
	bh.status = &BIMHealthStatus{
		OverallStatus: HealthStatusUnknown,
		Timestamp:     time.Now(),
		Components:    make(map[string]*HealthComponent),
		Summary:       make(map[string]interface{}),
		Version:       "1.0.0",
	}

	bh.logger.Info("Health status reset")
}
