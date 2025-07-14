package gateway

import (
	"fmt"
	"math/rand"
	"net/http"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// LoadBalancer manages service instances and distributes requests
type LoadBalancer struct {
	config     LoadBalancerConfig
	logger     *zap.Logger
	instances  map[string][]*ServiceInstance
	strategies map[string]LoadBalancingStrategy
	mu         sync.RWMutex
	metrics    *LoadBalancerMetrics
}

// LoadBalancerConfig defines load balancer configuration
type LoadBalancerConfig struct {
	DefaultStrategy string                    `yaml:"default_strategy"`
	Strategies      map[string]StrategyConfig `yaml:"strategies"`
	HealthCheck     HealthCheckConfig         `yaml:"health_check"`
	StickySessions  StickySessionConfig       `yaml:"sticky_sessions"`
	ConnectionPool  ConnectionPoolConfig      `yaml:"connection_pool"`
}

// StrategyConfig defines load balancing strategy configuration
type StrategyConfig struct {
	Type           string            `yaml:"type"`
	Weight         int               `yaml:"weight"`
	HealthBased    bool              `yaml:"health_based"`
	StickySessions bool              `yaml:"sticky_sessions"`
	Parameters     map[string]string `yaml:"parameters"`
}

// HealthCheckConfig defines health check configuration
type HealthCheckConfig struct {
	Enabled          bool          `yaml:"enabled"`
	Interval         time.Duration `yaml:"interval"`
	Timeout          time.Duration `yaml:"timeout"`
	FailureThreshold int           `yaml:"failure_threshold"`
	SuccessThreshold int           `yaml:"success_threshold"`
	Path             string        `yaml:"path"`
}

// StickySessionConfig defines sticky session configuration
type StickySessionConfig struct {
	Enabled     bool          `yaml:"enabled"`
	Duration    time.Duration `yaml:"duration"`
	CookieName  string        `yaml:"cookie_name"`
	HeaderName  string        `yaml:"header_name"`
	MaxSessions int           `yaml:"max_sessions"`
}

// ConnectionPoolConfig defines connection pool configuration
type ConnectionPoolConfig struct {
	Enabled            bool          `yaml:"enabled"`
	MaxConnections     int           `yaml:"max_connections"`
	MaxIdleConnections int           `yaml:"max_idle_connections"`
	IdleTimeout        time.Duration `yaml:"idle_timeout"`
	MaxLifetime        time.Duration `yaml:"max_lifetime"`
}

// ServiceInstance represents a service instance
type ServiceInstance struct {
	ID                string
	URL               string
	Weight            int
	Health            ServiceStatus
	ResponseTime      time.Duration
	LastCheck         time.Time
	Failures          int
	Successes         int
	ActiveConnections int
	mu                sync.RWMutex
}

// LoadBalancingStrategy defines the interface for load balancing strategies
type LoadBalancingStrategy interface {
	Select(instances []*ServiceInstance, request *http.Request) (*ServiceInstance, error)
	GetName() string
}

// RoundRobinStrategy implements round-robin load balancing
type RoundRobinStrategy struct {
	current int
	mu      sync.Mutex
}

// WeightedStrategy implements weighted load balancing
type WeightedStrategy struct {
	weights map[string]int
	mu      sync.Mutex
}

// HealthBasedStrategy implements health-based load balancing
type HealthBasedStrategy struct {
	fallbackStrategy LoadBalancingStrategy
}

// StickySessionStrategy implements sticky session load balancing
type StickySessionStrategy struct {
	sessions map[string]*StickySession
	mu       sync.RWMutex
	config   StickySessionConfig
}

// StickySession represents a sticky session
type StickySession struct {
	InstanceID string
	CreatedAt  time.Time
	LastAccess time.Time
	Requests   int
}

// LoadBalancerMetrics holds load balancer metrics
type LoadBalancerMetrics struct {
	requestsTotal     *prometheus.CounterVec
	requestsDuration  *prometheus.HistogramVec
	instanceHealth    *prometheus.GaugeVec
	activeConnections *prometheus.GaugeVec
}

// NewLoadBalancer creates a new load balancer
func NewLoadBalancer(config LoadBalancerConfig) (*LoadBalancer, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	lb := &LoadBalancer{
		config:     config,
		logger:     logger,
		instances:  make(map[string][]*ServiceInstance),
		strategies: make(map[string]LoadBalancingStrategy),
	}

	// Initialize metrics
	lb.initializeMetrics()

	// Initialize strategies
	lb.initializeStrategies()

	// Start health checking if enabled
	if config.HealthCheck.Enabled {
		go lb.startHealthChecking()
	}

	return lb, nil
}

// initializeMetrics initializes load balancer metrics
func (lb *LoadBalancer) initializeMetrics() {
	lb.metrics = &LoadBalancerMetrics{
		requestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_loadbalancer_requests_total",
				Help: "Total requests handled by load balancer",
			},
			[]string{"service", "instance", "strategy"},
		),
		requestsDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_loadbalancer_request_duration_seconds",
				Help:    "Request duration through load balancer",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service", "instance", "strategy"},
		),
		instanceHealth: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_loadbalancer_instance_health",
				Help: "Instance health status (0=unhealthy, 1=healthy)",
			},
			[]string{"service", "instance"},
		),
		activeConnections: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_loadbalancer_active_connections",
				Help: "Number of active connections per instance",
			},
			[]string{"service", "instance"},
		),
	}
}

// initializeStrategies initializes load balancing strategies
func (lb *LoadBalancer) initializeStrategies() {
	for name, config := range lb.config.Strategies {
		var strategy LoadBalancingStrategy

		switch config.Type {
		case "round_robin":
			strategy = &RoundRobinStrategy{}
		case "weighted":
			strategy = &WeightedStrategy{
				weights: make(map[string]int),
			}
		case "health_based":
			strategy = &HealthBasedStrategy{
				fallbackStrategy: &RoundRobinStrategy{},
			}
		case "sticky_session":
			strategy = &StickySessionStrategy{
				sessions: make(map[string]*StickySession),
				config:   lb.config.StickySessions,
			}
		default:
			lb.logger.Warn("Unknown load balancing strategy",
				zap.String("strategy", config.Type),
				zap.String("name", name),
			)
			strategy = &RoundRobinStrategy{}
		}

		lb.strategies[name] = strategy
	}
}

// AddInstance adds a service instance to the load balancer
func (lb *LoadBalancer) AddInstance(serviceName string, instance *ServiceInstance) {
	lb.mu.Lock()
	defer lb.mu.Unlock()

	if lb.instances[serviceName] == nil {
		lb.instances[serviceName] = make([]*ServiceInstance, 0)
	}

	lb.instances[serviceName] = append(lb.instances[serviceName], instance)

	lb.logger.Info("Service instance added",
		zap.String("service", serviceName),
		zap.String("instance", instance.ID),
		zap.String("url", instance.URL),
	)
}

// RemoveInstance removes a service instance from the load balancer
func (lb *LoadBalancer) RemoveInstance(serviceName string, instanceID string) {
	lb.mu.Lock()
	defer lb.mu.Unlock()

	instances := lb.instances[serviceName]
	for i, instance := range instances {
		if instance.ID == instanceID {
			lb.instances[serviceName] = append(instances[:i], instances[i+1:]...)
			lb.logger.Info("Service instance removed",
				zap.String("service", serviceName),
				zap.String("instance", instanceID),
			)
			return
		}
	}
}

// GetInstance selects an instance using the configured strategy
func (lb *LoadBalancer) GetInstance(serviceName string, request *http.Request) (*ServiceInstance, error) {
	lb.mu.RLock()
	instances := lb.instances[serviceName]
	strategy := lb.getStrategy(serviceName)
	lb.mu.RUnlock()

	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available for service %s", serviceName)
	}

	// Filter healthy instances
	healthyInstances := lb.getHealthyInstances(instances)
	if len(healthyInstances) == 0 {
		return nil, fmt.Errorf("no healthy instances available for service %s", serviceName)
	}

	// Select instance using strategy
	instance, err := strategy.Select(healthyInstances, request)
	if err != nil {
		return nil, fmt.Errorf("failed to select instance: %w", err)
	}

	// Update metrics
	lb.metrics.requestsTotal.WithLabelValues(serviceName, instance.ID, strategy.GetName()).Inc()

	lb.logger.Debug("Instance selected",
		zap.String("service", serviceName),
		zap.String("instance", instance.ID),
		zap.String("strategy", strategy.GetName()),
	)

	return instance, nil
}

// getStrategy gets the load balancing strategy for a service
func (lb *LoadBalancer) getStrategy(serviceName string) LoadBalancingStrategy {
	// Check if service has specific strategy
	if strategy, exists := lb.strategies[serviceName]; exists {
		return strategy
	}

	// Use default strategy
	if strategy, exists := lb.strategies[lb.config.DefaultStrategy]; exists {
		return strategy
	}

	// Fallback to round-robin
	return &RoundRobinStrategy{}
}

// getHealthyInstances filters instances to only healthy ones
func (lb *LoadBalancer) getHealthyInstances(instances []*ServiceInstance) []*ServiceInstance {
	healthy := make([]*ServiceInstance, 0)
	for _, instance := range instances {
		instance.mu.RLock()
		if instance.Health == ServiceStatusHealthy {
			healthy = append(healthy, instance)
		}
		instance.mu.RUnlock()
	}
	return healthy
}

// startHealthChecking starts the health checking process
func (lb *LoadBalancer) startHealthChecking() {
	ticker := time.NewTicker(lb.config.HealthCheck.Interval)
	defer ticker.Stop()

	for range ticker.C {
		lb.checkAllInstances()
	}
}

// checkAllInstances checks health of all instances
func (lb *LoadBalancer) checkAllInstances() {
	lb.mu.RLock()
	services := make(map[string][]*ServiceInstance)
	for service, instances := range lb.instances {
		services[service] = instances
	}
	lb.mu.RUnlock()

	for serviceName, instances := range services {
		for _, instance := range instances {
			go lb.checkInstanceHealth(serviceName, instance)
		}
	}
}

// checkInstanceHealth checks the health of a specific instance
func (lb *LoadBalancer) checkInstanceHealth(serviceName string, instance *ServiceInstance) {
	start := time.Now()

	client := &http.Client{
		Timeout: lb.config.HealthCheck.Timeout,
	}

	healthURL := fmt.Sprintf("%s%s", instance.URL, lb.config.HealthCheck.Path)
	req, err := http.NewRequest("GET", healthURL, nil)
	if err != nil {
		lb.updateInstanceHealth(serviceName, instance, ServiceStatusUnhealthy, time.Since(start))
		return
	}

	resp, err := client.Do(req)
	duration := time.Since(start)

	if err != nil {
		lb.updateInstanceHealth(serviceName, instance, ServiceStatusUnhealthy, duration)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		lb.updateInstanceHealth(serviceName, instance, ServiceStatusHealthy, duration)
	} else {
		lb.updateInstanceHealth(serviceName, instance, ServiceStatusUnhealthy, duration)
	}
}

// updateInstanceHealth updates the health status of an instance
func (lb *LoadBalancer) updateInstanceHealth(serviceName string, instance *ServiceInstance, status ServiceStatus, responseTime time.Duration) {
	instance.mu.Lock()
	defer instance.mu.Unlock()

	oldHealth := instance.Health
	instance.Health = status
	instance.ResponseTime = responseTime
	instance.LastCheck = time.Now()

	if status == ServiceStatusHealthy {
		instance.Successes++
		instance.Failures = 0
	} else {
		instance.Failures++
		instance.Successes = 0
	}

	// Update metrics
	var healthValue float64
	if status == ServiceStatusHealthy {
		healthValue = 1.0
	}
	lb.metrics.instanceHealth.WithLabelValues(serviceName, instance.ID).Set(healthValue)

	if oldHealth != status {
		lb.logger.Info("Instance health changed",
			zap.String("service", serviceName),
			zap.String("instance", instance.ID),
			zap.String("old_health", string(oldHealth)),
			zap.String("new_health", string(status)),
			zap.Duration("response_time", responseTime),
		)
	}
}

// RoundRobinStrategy implementation
func (rr *RoundRobinStrategy) Select(instances []*ServiceInstance, request *http.Request) (*ServiceInstance, error) {
	rr.mu.Lock()
	defer rr.mu.Unlock()

	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	instance := instances[rr.current]
	rr.current = (rr.current + 1) % len(instances)

	return instance, nil
}

func (rr *RoundRobinStrategy) GetName() string {
	return "round_robin"
}

// WeightedStrategy implementation
func (ws *WeightedStrategy) Select(instances []*ServiceInstance, request *http.Request) (*ServiceInstance, error) {
	ws.mu.Lock()
	defer ws.mu.Unlock()

	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	// Calculate total weight
	totalWeight := 0
	for _, instance := range instances {
		totalWeight += instance.Weight
	}

	if totalWeight == 0 {
		// If no weights specified, use round-robin
		return instances[0], nil
	}

	// Select based on weight
	random := rand.Intn(totalWeight)
	currentWeight := 0

	for _, instance := range instances {
		currentWeight += instance.Weight
		if random < currentWeight {
			return instance, nil
		}
	}

	// Fallback to first instance
	return instances[0], nil
}

func (ws *WeightedStrategy) GetName() string {
	return "weighted"
}

// HealthBasedStrategy implementation
func (hb *HealthBasedStrategy) Select(instances []*ServiceInstance, request *http.Request) (*ServiceInstance, error) {
	// Filter instances by health status
	healthyInstances := make([]*ServiceInstance, 0)
	for _, instance := range instances {
		instance.mu.RLock()
		if instance.Health == ServiceStatusHealthy {
			healthyInstances = append(healthyInstances, instance)
		}
		instance.mu.RUnlock()
	}

	if len(healthyInstances) == 0 {
		// Fallback to all instances if no healthy ones
		return hb.fallbackStrategy.Select(instances, request)
	}

	// Use fallback strategy on healthy instances
	return hb.fallbackStrategy.Select(healthyInstances, request)
}

func (hb *HealthBasedStrategy) GetName() string {
	return "health_based"
}

// StickySessionStrategy implementation
func (ss *StickySessionStrategy) Select(instances []*ServiceInstance, request *http.Request) (*ServiceInstance, error) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	// Get session ID from cookie or header
	sessionID := ss.getSessionID(request)
	if sessionID == "" {
		// No session, use round-robin
		return ss.selectRandomInstance(instances)
	}

	// Check if session exists and is still valid
	if session, exists := ss.sessions[sessionID]; exists {
		if time.Since(session.LastAccess) < ss.config.Duration {
			// Find the instance for this session
			for _, instance := range instances {
				if instance.ID == session.InstanceID {
					session.LastAccess = time.Now()
					session.Requests++
					return instance, nil
				}
			}
			// Instance not found, remove session
			delete(ss.sessions, sessionID)
		} else {
			// Session expired, remove it
			delete(ss.sessions, sessionID)
		}
	}

	// Create new session
	instance, err := ss.selectRandomInstance(instances)
	if err != nil {
		return nil, err
	}

	ss.sessions[sessionID] = &StickySession{
		InstanceID: instance.ID,
		CreatedAt:  time.Now(),
		LastAccess: time.Now(),
		Requests:   1,
	}

	return instance, nil
}

func (ss *StickySessionStrategy) GetName() string {
	return "sticky_session"
}

// getSessionID extracts session ID from request
func (ss *StickySessionStrategy) getSessionID(request *http.Request) string {
	// Try cookie first
	if cookie, err := request.Cookie(ss.config.CookieName); err == nil {
		return cookie.Value
	}

	// Try header
	if sessionID := request.Header.Get(ss.config.HeaderName); sessionID != "" {
		return sessionID
	}

	return ""
}

// selectRandomInstance selects a random instance
func (ss *StickySessionStrategy) selectRandomInstance(instances []*ServiceInstance) (*ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	// Simple random selection
	index := rand.Intn(len(instances))
	return instances[index], nil
}

// GetStats returns load balancer statistics
func (lb *LoadBalancer) GetStats() map[string]interface{} {
	lb.mu.RLock()
	defer lb.mu.RUnlock()

	stats := make(map[string]interface{})
	for serviceName, instances := range lb.instances {
		serviceStats := make(map[string]interface{})
		healthyCount := 0
		totalWeight := 0

		for _, instance := range instances {
			instance.mu.RLock()
			instanceStats := map[string]interface{}{
				"id":                 instance.ID,
				"url":                instance.URL,
				"health":             instance.Health,
				"weight":             instance.Weight,
				"response_time":      instance.ResponseTime,
				"last_check":         instance.LastCheck,
				"failures":           instance.Failures,
				"successes":          instance.Successes,
				"active_connections": instance.ActiveConnections,
			}
			instance.mu.RUnlock()

			serviceStats[instance.ID] = instanceStats

			if instance.Health == ServiceStatusHealthy {
				healthyCount++
			}
			totalWeight += instance.Weight
		}

		serviceStats["total_instances"] = len(instances)
		serviceStats["healthy_instances"] = healthyCount
		serviceStats["total_weight"] = totalWeight

		stats[serviceName] = serviceStats
	}

	return stats
}

// UpdateConfig updates the load balancer configuration
func (lb *LoadBalancer) UpdateConfig(config LoadBalancerConfig) error {
	lb.config = config
	lb.logger.Info("Load balancer configuration updated")
	return nil
}
