package gateway

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLoadBalancer_NewLoadBalancer(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {
				Type: "round_robin",
			},
			"weighted": {
				Type: "weighted",
			},
		},
		HealthCheck: HealthCheckConfig{
			Enabled:  true,
			Interval: 10 * time.Second,
			Timeout:  5 * time.Second,
			Path:     "/health",
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)
	assert.NotNil(t, lb)
	assert.Equal(t, config, lb.config)
}

func TestLoadBalancer_AddInstance(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance := &ServiceInstance{
		ID:     "instance-1",
		URL:    "http://localhost:8080",
		Weight: 1,
		Health: ServiceStatusHealthy,
	}

	lb.AddInstance("test-service", instance)

	lb.mu.RLock()
	instances := lb.instances["test-service"]
	lb.mu.RUnlock()

	assert.Len(t, instances, 1)
	assert.Equal(t, instance, instances[0])
}

func TestLoadBalancer_RemoveInstance(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance := &ServiceInstance{
		ID:     "instance-1",
		URL:    "http://localhost:8080",
		Weight: 1,
		Health: ServiceStatusHealthy,
	}

	lb.AddInstance("test-service", instance)
	lb.RemoveInstance("test-service", "instance-1")

	lb.mu.RLock()
	instances := lb.instances["test-service"]
	lb.mu.RUnlock()

	assert.Len(t, instances, 0)
}

func TestLoadBalancer_GetInstance(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance1 := &ServiceInstance{
		ID:     "instance-1",
		URL:    "http://localhost:8080",
		Weight: 1,
		Health: ServiceStatusHealthy,
	}

	instance2 := &ServiceInstance{
		ID:     "instance-2",
		URL:    "http://localhost:8081",
		Weight: 1,
		Health: ServiceStatusHealthy,
	}

	lb.AddInstance("test-service", instance1)
	lb.AddInstance("test-service", instance2)

	request := httptest.NewRequest("GET", "/test", nil)

	// Test round-robin selection
	selected1, err := lb.GetInstance("test-service", request)
	require.NoError(t, err)
	assert.Equal(t, instance1, selected1)

	selected2, err := lb.GetInstance("test-service", request)
	require.NoError(t, err)
	assert.Equal(t, instance2, selected2)

	selected3, err := lb.GetInstance("test-service", request)
	require.NoError(t, err)
	assert.Equal(t, instance1, selected3)
}

func TestLoadBalancer_GetInstance_NoHealthyInstances(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance := &ServiceInstance{
		ID:     "instance-1",
		URL:    "http://localhost:8080",
		Weight: 1,
		Health: ServiceStatusUnhealthy,
	}

	lb.AddInstance("test-service", instance)

	request := httptest.NewRequest("GET", "/test", nil)

	_, err = lb.GetInstance("test-service", request)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "no healthy instances available")
}

func TestLoadBalancer_GetInstance_NoInstances(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	request := httptest.NewRequest("GET", "/test", nil)

	_, err = lb.GetInstance("test-service", request)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "no instances available")
}

func TestRoundRobinStrategy_Select(t *testing.T) {
	strategy := &RoundRobinStrategy{}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080"},
		{ID: "instance-2", URL: "http://localhost:8081"},
		{ID: "instance-3", URL: "http://localhost:8082"},
	}

	request := httptest.NewRequest("GET", "/test", nil)

	// Test round-robin selection
	selected1, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Equal(t, instances[0], selected1)

	selected2, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Equal(t, instances[1], selected2)

	selected3, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Equal(t, instances[2], selected3)

	selected4, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Equal(t, instances[0], selected4)
}

func TestRoundRobinStrategy_Select_EmptyInstances(t *testing.T) {
	strategy := &RoundRobinStrategy{}
	request := httptest.NewRequest("GET", "/test", nil)

	_, err := strategy.Select([]*ServiceInstance{}, request)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "no instances available")
}

func TestWeightedStrategy_Select(t *testing.T) {
	strategy := &WeightedStrategy{
		weights: make(map[string]int),
	}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080", Weight: 3},
		{ID: "instance-2", URL: "http://localhost:8081", Weight: 2},
		{ID: "instance-3", URL: "http://localhost:8082", Weight: 1},
	}

	request := httptest.NewRequest("GET", "/test", nil)

	// Test weighted selection (multiple times to verify distribution)
	selections := make(map[string]int)
	for i := 0; i < 1000; i++ {
		selected, err := strategy.Select(instances, request)
		require.NoError(t, err)
		selections[selected.ID]++
	}

	// Verify that instance-1 (weight 3) gets selected more often
	assert.True(t, selections["instance-1"] > selections["instance-2"])
	assert.True(t, selections["instance-2"] > selections["instance-3"])
}

func TestWeightedStrategy_Select_NoWeights(t *testing.T) {
	strategy := &WeightedStrategy{
		weights: make(map[string]int),
	}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080", Weight: 0},
		{ID: "instance-2", URL: "http://localhost:8081", Weight: 0},
	}

	request := httptest.NewRequest("GET", "/test", nil)

	selected, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Equal(t, instances[0], selected)
}

func TestHealthBasedStrategy_Select(t *testing.T) {
	fallbackStrategy := &RoundRobinStrategy{}
	strategy := &HealthBasedStrategy{
		fallbackStrategy: fallbackStrategy,
	}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080", Health: ServiceStatusHealthy},
		{ID: "instance-2", URL: "http://localhost:8081", Health: ServiceStatusUnhealthy},
		{ID: "instance-3", URL: "http://localhost:8082", Health: ServiceStatusHealthy},
	}

	request := httptest.NewRequest("GET", "/test", nil)

	selected, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Contains(t, []string{"instance-1", "instance-3"}, selected.ID)
}

func TestHealthBasedStrategy_Select_NoHealthyInstances(t *testing.T) {
	fallbackStrategy := &RoundRobinStrategy{}
	strategy := &HealthBasedStrategy{
		fallbackStrategy: fallbackStrategy,
	}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080", Health: ServiceStatusUnhealthy},
		{ID: "instance-2", URL: "http://localhost:8081", Health: ServiceStatusUnhealthy},
	}

	request := httptest.NewRequest("GET", "/test", nil)

	selected, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Contains(t, []string{"instance-1", "instance-2"}, selected.ID)
}

func TestStickySessionStrategy_Select(t *testing.T) {
	config := StickySessionConfig{
		Enabled:    true,
		Duration:   30 * time.Second,
		CookieName: "session-id",
		HeaderName: "X-Session-ID",
	}

	strategy := &StickySessionStrategy{
		sessions: make(map[string]*StickySession),
		config:   config,
	}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080"},
		{ID: "instance-2", URL: "http://localhost:8081"},
	}

	// Test first request (no session)
	request1 := httptest.NewRequest("GET", "/test", nil)
	selected1, err := strategy.Select(instances, request1)
	require.NoError(t, err)
	assert.Contains(t, []string{"instance-1", "instance-2"}, selected1.ID)

	// Test second request with session cookie
	request2 := httptest.NewRequest("GET", "/test", nil)
	request2.AddCookie(&http.Cookie{Name: "session-id", Value: "session-123"})

	selected2, err := strategy.Select(instances, request2)
	require.NoError(t, err)
	assert.Contains(t, []string{"instance-1", "instance-2"}, selected2.ID)

	// Test third request with same session (should return same instance)
	request3 := httptest.NewRequest("GET", "/test", nil)
	request3.AddCookie(&http.Cookie{Name: "session-id", Value: "session-123"})

	selected3, err := strategy.Select(instances, request3)
	require.NoError(t, err)
	assert.Equal(t, selected2.ID, selected3.ID)
}

func TestStickySessionStrategy_Select_HeaderSession(t *testing.T) {
	config := StickySessionConfig{
		Enabled:    true,
		Duration:   30 * time.Second,
		CookieName: "session-id",
		HeaderName: "X-Session-ID",
	}

	strategy := &StickySessionStrategy{
		sessions: make(map[string]*StickySession),
		config:   config,
	}

	instances := []*ServiceInstance{
		{ID: "instance-1", URL: "http://localhost:8080"},
		{ID: "instance-2", URL: "http://localhost:8081"},
	}

	// Test request with session header
	request := httptest.NewRequest("GET", "/test", nil)
	request.Header.Set("X-Session-ID", "session-456")

	selected1, err := strategy.Select(instances, request)
	require.NoError(t, err)
	assert.Contains(t, []string{"instance-1", "instance-2"}, selected1.ID)

	// Test second request with same session header
	request2 := httptest.NewRequest("GET", "/test", nil)
	request2.Header.Set("X-Session-ID", "session-456")

	selected2, err := strategy.Select(instances, request2)
	require.NoError(t, err)
	assert.Equal(t, selected1.ID, selected2.ID)
}

func TestLoadBalancer_GetStats(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance1 := &ServiceInstance{
		ID:     "instance-1",
		URL:    "http://localhost:8080",
		Weight: 2,
		Health: ServiceStatusHealthy,
	}

	instance2 := &ServiceInstance{
		ID:     "instance-2",
		URL:    "http://localhost:8081",
		Weight: 1,
		Health: ServiceStatusUnhealthy,
	}

	lb.AddInstance("test-service", instance1)
	lb.AddInstance("test-service", instance2)

	stats := lb.GetStats()

	serviceStats, exists := stats["test-service"].(map[string]interface{})
	assert.True(t, exists)
	assert.Equal(t, 2, serviceStats["total_instances"])
	assert.Equal(t, 1, serviceStats["healthy_instances"])
	assert.Equal(t, 3, serviceStats["total_weight"])
}

func TestLoadBalancer_UpdateConfig(t *testing.T) {
	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	newConfig := LoadBalancerConfig{
		DefaultStrategy: "weighted",
		Strategies: map[string]StrategyConfig{
			"weighted": {Type: "weighted"},
		},
	}

	err = lb.UpdateConfig(newConfig)
	assert.NoError(t, err)
	assert.Equal(t, newConfig, lb.config)
}

func TestLoadBalancer_HealthChecking(t *testing.T) {
	// Create test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusOK)
		} else {
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
		HealthCheck: HealthCheckConfig{
			Enabled:  true,
			Interval: 100 * time.Millisecond,
			Timeout:  5 * time.Second,
			Path:     "/health",
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance := &ServiceInstance{
		ID:     "instance-1",
		URL:    server.URL,
		Weight: 1,
		Health: ServiceStatusUnknown,
	}

	lb.AddInstance("test-service", instance)

	// Wait for health check
	time.Sleep(200 * time.Millisecond)

	// Check that instance is now healthy
	instance.mu.RLock()
	health := instance.Health
	instance.mu.RUnlock()

	assert.Equal(t, ServiceStatusHealthy, health)
}

func TestLoadBalancer_HealthChecking_Unhealthy(t *testing.T) {
	// Create test server that returns error
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	config := LoadBalancerConfig{
		DefaultStrategy: "round_robin",
		Strategies: map[string]StrategyConfig{
			"round_robin": {Type: "round_robin"},
		},
		HealthCheck: HealthCheckConfig{
			Enabled:  true,
			Interval: 100 * time.Millisecond,
			Timeout:  5 * time.Second,
			Path:     "/health",
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	instance := &ServiceInstance{
		ID:     "instance-1",
		URL:    server.URL,
		Weight: 1,
		Health: ServiceStatusUnknown,
	}

	lb.AddInstance("test-service", instance)

	// Wait for health check
	time.Sleep(200 * time.Millisecond)

	// Check that instance is now unhealthy
	instance.mu.RLock()
	health := instance.Health
	instance.mu.RUnlock()

	assert.Equal(t, ServiceStatusUnhealthy, health)
}
