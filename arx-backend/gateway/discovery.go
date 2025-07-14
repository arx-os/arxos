package gateway

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"go.uber.org/zap"
)

// ServiceDiscovery handles service discovery and health monitoring
type ServiceDiscovery struct {
	config   *Config
	logger   *zap.Logger
	services map[string]*ServiceInfo
	health   *HealthChecker
	mu       sync.RWMutex
	stopChan chan struct{}
}

// ServiceInfo represents information about a service
type ServiceInfo struct {
	Name      string
	URL       string
	Health    string
	Status    ServiceStatus
	LastCheck time.Time
	Response  time.Duration
	Weight    int
}

// ServiceStatus represents the health status of a service
type ServiceStatus string

const (
	ServiceStatusHealthy   ServiceStatus = "healthy"
	ServiceStatusUnhealthy ServiceStatus = "unhealthy"
	ServiceStatusUnknown   ServiceStatus = "unknown"
)

// HealthChecker handles health check operations
type HealthChecker struct {
	client  *http.Client
	logger  *zap.Logger
	timeout time.Duration
}

// NewServiceDiscovery creates a new service discovery instance
func NewServiceDiscovery(config *Config) (*ServiceDiscovery, error) {
	if config == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}

	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	health := &HealthChecker{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
		logger:  logger,
		timeout: 10 * time.Second,
	}

	discovery := &ServiceDiscovery{
		config:   config,
		logger:   logger,
		services: make(map[string]*ServiceInfo),
		health:   health,
		stopChan: make(chan struct{}),
	}

	return discovery, nil
}

// Start begins the service discovery process
func (sd *ServiceDiscovery) Start() error {
	sd.logger.Info("Starting service discovery")

	// Initial service discovery
	if err := sd.discoverServices(); err != nil {
		return fmt.Errorf("failed to discover services: %w", err)
	}

	// Start health check loop
	go sd.healthCheckLoop()

	return nil
}

// Stop stops the service discovery process
func (sd *ServiceDiscovery) Stop() error {
	sd.logger.Info("Stopping service discovery")
	close(sd.stopChan)
	return nil
}

// discoverServices discovers all configured services
func (sd *ServiceDiscovery) discoverServices() error {
	sd.mu.Lock()
	defer sd.mu.Unlock()

	for serviceName, serviceConfig := range sd.config.Services {
		serviceInfo := &ServiceInfo{
			Name:   serviceName,
			URL:    serviceConfig.URL,
			Health: serviceConfig.Health,
			Status: ServiceStatusUnknown,
			Weight: serviceConfig.Weight,
		}

		sd.services[serviceName] = serviceInfo
	}

	sd.logger.Info("Services discovered",
		zap.Int("service_count", len(sd.services)),
	)

	return nil
}

// healthCheckLoop runs periodic health checks
func (sd *ServiceDiscovery) healthCheckLoop() {
	ticker := time.NewTicker(sd.config.Monitoring.HealthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			sd.performHealthChecks()
		case <-sd.stopChan:
			return
		}
	}
}

// performHealthChecks performs health checks on all services
func (sd *ServiceDiscovery) performHealthChecks() {
	sd.mu.RLock()
	services := make(map[string]*ServiceInfo)
	for name, service := range sd.services {
		services[name] = service
	}
	sd.mu.RUnlock()

	for serviceName, serviceInfo := range services {
		go sd.checkServiceHealth(serviceName, serviceInfo)
	}
}

// checkServiceHealth checks the health of a specific service
func (sd *ServiceDiscovery) checkServiceHealth(serviceName string, serviceInfo *ServiceInfo) {
	start := time.Now()

	// Perform health check
	status, err := sd.health.CheckHealth(serviceInfo.Health)
	if err != nil {
		sd.logger.Error("Health check failed",
			zap.String("service", serviceName),
			zap.String("health_url", serviceInfo.Health),
			zap.Error(err),
		)
		status = ServiceStatusUnhealthy
	}

	// Update service status
	sd.mu.Lock()
	if service, exists := sd.services[serviceName]; exists {
		service.Status = status
		service.LastCheck = time.Now()
		service.Response = time.Since(start)
	}
	sd.mu.Unlock()

	sd.logger.Debug("Health check completed",
		zap.String("service", serviceName),
		zap.String("status", string(status)),
		zap.Duration("response_time", time.Since(start)),
	)
}

// GetServiceStatus returns the status of all services
func (sd *ServiceDiscovery) GetServiceStatus() map[string]interface{} {
	sd.mu.RLock()
	defer sd.mu.RUnlock()

	status := make(map[string]interface{})
	for name, service := range sd.services {
		status[name] = map[string]interface{}{
			"name":          service.Name,
			"url":           service.URL,
			"status":        string(service.Status),
			"last_check":    service.LastCheck,
			"response_time": service.Response,
			"weight":        service.Weight,
		}
	}

	return status
}

// GetService returns a specific service by name
func (sd *ServiceDiscovery) GetService(name string) (*ServiceInfo, error) {
	sd.mu.RLock()
	defer sd.mu.RUnlock()

	service, exists := sd.services[name]
	if !exists {
		return nil, fmt.Errorf("service %s not found", name)
	}

	return service, nil
}

// UpdateConfig updates the service discovery configuration
func (sd *ServiceDiscovery) UpdateConfig(config *Config) error {
	sd.mu.Lock()
	defer sd.mu.Unlock()

	sd.config = config

	// Re-discover services with new config
	if err := sd.discoverServices(); err != nil {
		return fmt.Errorf("failed to rediscover services: %w", err)
	}

	return nil
}

// CheckHealth performs a health check on a service
func (hc *HealthChecker) CheckHealth(healthURL string) (ServiceStatus, error) {
	if healthURL == "" {
		return ServiceStatusUnknown, fmt.Errorf("health URL is empty")
	}

	ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", healthURL, nil)
	if err != nil {
		return ServiceStatusUnhealthy, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := hc.client.Do(req)
	if err != nil {
		return ServiceStatusUnhealthy, fmt.Errorf("health check request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return ServiceStatusHealthy, nil
	}

	return ServiceStatusUnhealthy, fmt.Errorf("health check returned status: %d", resp.StatusCode)
}
