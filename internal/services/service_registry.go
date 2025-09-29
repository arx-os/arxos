package services

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ServiceRegistry manages service discovery and registration
type ServiceRegistry struct {
	services map[string]*ServiceInfo
	mu       sync.RWMutex
	ttl      time.Duration
}

// ServiceInfo represents information about a registered service
type ServiceInfo struct {
	Name         string            `json:"name"`
	Version      string            `json:"version"`
	Address      string            `json:"address"`
	Port         int               `json:"port"`
	Health       ServiceHealth     `json:"health"`
	Metadata     map[string]string `json:"metadata"`
	Tags         []string          `json:"tags"`
	LastSeen     time.Time         `json:"last_seen"`
	RegisteredAt time.Time         `json:"registered_at"`
}

// ServiceHealth represents the health status of a service
type ServiceHealth struct {
	Status    HealthStatus  `json:"status"`
	Message   string        `json:"message"`
	Timestamp time.Time     `json:"timestamp"`
	Checks    []HealthCheck `json:"checks"`
}

// HealthStatus represents the health status
type HealthStatus string

const (
	HealthStatusHealthy   HealthStatus = "healthy"
	HealthStatusUnhealthy HealthStatus = "unhealthy"
	HealthStatusUnknown   HealthStatus = "unknown"
)

// HealthCheck represents a health check
type HealthCheck struct {
	Name      string       `json:"name"`
	Status    HealthStatus `json:"status"`
	Message   string       `json:"message"`
	Timestamp time.Time    `json:"timestamp"`
}

// NewServiceRegistry creates a new service registry
func NewServiceRegistry(ttl time.Duration) *ServiceRegistry {
	sr := &ServiceRegistry{
		services: make(map[string]*ServiceInfo),
		ttl:      ttl,
	}

	// Start cleanup goroutine
	go sr.cleanup()

	return sr
}

// Register registers a service
func (sr *ServiceRegistry) Register(ctx context.Context, service *ServiceInfo) error {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	service.LastSeen = time.Now()
	if service.RegisteredAt.IsZero() {
		service.RegisteredAt = time.Now()
	}

	sr.services[service.Name] = service
	logger.Info("Service registered: %s at %s:%d", service.Name, service.Address, service.Port)

	return nil
}

// Deregister deregisters a service
func (sr *ServiceRegistry) Deregister(ctx context.Context, serviceName string) error {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	if _, exists := sr.services[serviceName]; exists {
		delete(sr.services, serviceName)
		logger.Info("Service deregistered: %s", serviceName)
	}

	return nil
}

// GetService retrieves a service by name
func (sr *ServiceRegistry) GetService(ctx context.Context, serviceName string) (*ServiceInfo, error) {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	service, exists := sr.services[serviceName]
	if !exists {
		return nil, fmt.Errorf("service '%s' not found", serviceName)
	}

	// Check if service is still alive
	if time.Since(service.LastSeen) > sr.ttl {
		return nil, fmt.Errorf("service '%s' is stale", serviceName)
	}

	return service, nil
}

// ListServices lists all registered services
func (sr *ServiceRegistry) ListServices(ctx context.Context) ([]*ServiceInfo, error) {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	services := make([]*ServiceInfo, 0, len(sr.services))
	for _, service := range sr.services {
		// Only return alive services
		if time.Since(service.LastSeen) <= sr.ttl {
			services = append(services, service)
		}
	}

	return services, nil
}

// UpdateHealth updates the health status of a service
func (sr *ServiceRegistry) UpdateHealth(ctx context.Context, serviceName string, health *ServiceHealth) error {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	service, exists := sr.services[serviceName]
	if !exists {
		return fmt.Errorf("service '%s' not found", serviceName)
	}

	service.Health = *health
	service.LastSeen = time.Now()

	logger.Debug("Health updated for service %s: %s", serviceName, health.Status)

	return nil
}

// cleanup removes stale services
func (sr *ServiceRegistry) cleanup() {
	ticker := time.NewTicker(sr.ttl / 2)
	defer ticker.Stop()

	for range ticker.C {
		sr.mu.Lock()
		for name, service := range sr.services {
			if time.Since(service.LastSeen) > sr.ttl {
				delete(sr.services, name)
				logger.Info("Removed stale service: %s", name)
			}
		}
		sr.mu.Unlock()
	}
}

// ServiceClient provides client capabilities for service communication
type ServiceClient struct {
	registry *ServiceRegistry
	timeout  time.Duration
}

// NewServiceClient creates a new service client
func NewServiceClient(registry *ServiceRegistry, timeout time.Duration) *ServiceClient {
	return &ServiceClient{
		registry: registry,
		timeout:  timeout,
	}
}

// CallService calls a service method
func (sc *ServiceClient) CallService(ctx context.Context, serviceName, method string, request interface{}) (interface{}, error) {
	// Get service information
	service, err := sc.registry.GetService(ctx, serviceName)
	if err != nil {
		return nil, fmt.Errorf("failed to get service: %w", err)
	}

	// Check service health
	if service.Health.Status != HealthStatusHealthy {
		return nil, fmt.Errorf("service '%s' is unhealthy: %s", serviceName, service.Health.Message)
	}

	// Make service call (placeholder implementation)
	logger.Debug("Calling service %s method %s", serviceName, method)

	// In a real implementation, this would make an HTTP/gRPC call
	// For now, return a mock response
	response := map[string]interface{}{
		"service":   serviceName,
		"method":    method,
		"status":    "success",
		"timestamp": time.Now(),
	}

	return response, nil
}

// ServiceGateway provides gateway capabilities for service routing
type ServiceGateway struct {
	registry *ServiceRegistry
	routes   map[string]*Route
	mu       sync.RWMutex
}

// Route represents a service route
type Route struct {
	Path        string              `json:"path"`
	Service     string              `json:"service"`
	Method      string              `json:"method"`
	Timeout     time.Duration       `json:"timeout"`
	Retries     int                 `json:"retries"`
	LoadBalance LoadBalanceStrategy `json:"load_balance"`
	Metadata    map[string]string   `json:"metadata"`
}

// LoadBalanceStrategy represents load balancing strategy
type LoadBalanceStrategy string

const (
	LoadBalanceRoundRobin LoadBalanceStrategy = "round_robin"
	LoadBalanceRandom     LoadBalanceStrategy = "random"
	LoadBalanceLeastConn  LoadBalanceStrategy = "least_conn"
)

// NewServiceGateway creates a new service gateway
func NewServiceGateway(registry *ServiceRegistry) *ServiceGateway {
	return &ServiceGateway{
		registry: registry,
		routes:   make(map[string]*Route),
	}
}

// AddRoute adds a route to the gateway
func (sg *ServiceGateway) AddRoute(path string, route *Route) {
	sg.mu.Lock()
	defer sg.mu.Unlock()

	sg.routes[path] = route
	logger.Info("Route added: %s -> %s", path, route.Service)
}

// RemoveRoute removes a route from the gateway
func (sg *ServiceGateway) RemoveRoute(path string) {
	sg.mu.Lock()
	defer sg.mu.Unlock()

	delete(sg.routes, path)
	logger.Info("Route removed: %s", path)
}

// GetRoute retrieves a route by path
func (sg *ServiceGateway) GetRoute(path string) (*Route, error) {
	sg.mu.RLock()
	defer sg.mu.RUnlock()

	route, exists := sg.routes[path]
	if !exists {
		return nil, fmt.Errorf("route not found: %s", path)
	}

	return route, nil
}

// RouteRequest routes a request to the appropriate service
func (sg *ServiceGateway) RouteRequest(ctx context.Context, path string, request interface{}) (interface{}, error) {
	route, err := sg.GetRoute(path)
	if err != nil {
		return nil, err
	}

	// Get service instances
	_, err = sg.registry.GetService(ctx, route.Service)
	if err != nil {
		return nil, fmt.Errorf("failed to get service '%s': %w", route.Service, err)
	}

	// Create service client
	client := NewServiceClient(sg.registry, route.Timeout)

	// Make service call
	response, err := client.CallService(ctx, route.Service, route.Method, request)
	if err != nil {
		return nil, fmt.Errorf("service call failed: %w", err)
	}

	return response, nil
}

// ServiceHealthChecker provides health checking capabilities
type ServiceHealthChecker struct {
	registry *ServiceRegistry
	interval time.Duration
	checks   map[string]HealthCheckFunc
}

// HealthCheckFunc represents a health check function
type HealthCheckFunc func(ctx context.Context, service *ServiceInfo) *ServiceHealth

// NewServiceHealthChecker creates a new service health checker
func NewServiceHealthChecker(registry *ServiceRegistry, interval time.Duration) *ServiceHealthChecker {
	shc := &ServiceHealthChecker{
		registry: registry,
		interval: interval,
		checks:   make(map[string]HealthCheckFunc),
	}

	// Start health checking
	go shc.startHealthChecking()

	return shc
}

// RegisterHealthCheck registers a health check function
func (shc *ServiceHealthChecker) RegisterHealthCheck(serviceName string, checkFunc HealthCheckFunc) {
	shc.checks[serviceName] = checkFunc
	logger.Info("Health check registered for service: %s", serviceName)
}

// startHealthChecking starts the health checking process
func (shc *ServiceHealthChecker) startHealthChecking() {
	ticker := time.NewTicker(shc.interval)
	defer ticker.Stop()

	for range ticker.C {
		services, err := shc.registry.ListServices(context.Background())
		if err != nil {
			logger.Error("Failed to list services for health checking: %v", err)
			continue
		}

		for _, service := range services {
			if checkFunc, exists := shc.checks[service.Name]; exists {
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				health := checkFunc(ctx, service)
				cancel()

				if health != nil {
					shc.registry.UpdateHealth(context.Background(), service.Name, health)
				}
			}
		}
	}
}

// DefaultHealthCheck provides a default health check implementation
func DefaultHealthCheck(ctx context.Context, service *ServiceInfo) *ServiceHealth {
	// Simple HTTP health check
	health := &ServiceHealth{
		Status:    HealthStatusHealthy,
		Message:   "Service is healthy",
		Timestamp: time.Now(),
		Checks: []HealthCheck{
			{
				Name:      "basic",
				Status:    HealthStatusHealthy,
				Message:   "Basic health check passed",
				Timestamp: time.Now(),
			},
		},
	}

	// In a real implementation, this would make an HTTP call to the service's health endpoint
	// For now, we'll assume the service is healthy if it's registered

	return health
}
