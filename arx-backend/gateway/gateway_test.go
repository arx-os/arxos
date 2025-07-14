package gateway

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewGateway(t *testing.T) {
	config := &Config{
		Port:         8080,
		Host:         "localhost",
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
		Services: map[string]ServiceConfig{
			"test-service": {
				Name:   "test-service",
				URL:    "http://localhost:8000",
				Health: "http://localhost:8000/health",
				Routes: []Route{
					{
						Path:    "/api/test",
						Service: "test-service",
						Methods: []string{"GET", "POST"},
						Auth:    true,
					},
				},
			},
		},
		Auth: AuthConfig{
			JWTSecret:   "test-secret",
			TokenExpiry: 24 * time.Hour,
		},
		RateLimit: RateLimitConfig{
			RequestsPerSecond: 100,
			Burst:             200,
		},
		Monitoring: MonitoringConfig{
			HealthCheckInterval: 30 * time.Second,
		},
	}

	gateway, err := NewGateway(config)
	require.NoError(t, err)
	assert.NotNil(t, gateway)
	assert.NotNil(t, gateway.router)
	assert.NotNil(t, gateway.discovery)
	assert.NotNil(t, gateway.auth)
	assert.NotNil(t, gateway.rateLimit)
	assert.NotNil(t, gateway.monitoring)
}

func TestGatewayHealth(t *testing.T) {
	config := &Config{
		Port:         8080,
		Host:         "localhost",
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
		Services: map[string]ServiceConfig{
			"test-service": {
				Name:   "test-service",
				URL:    "http://localhost:8000",
				Health: "http://localhost:8000/health",
				Routes: []Route{
					{
						Path:    "/api/test",
						Service: "test-service",
						Methods: []string{"GET"},
						Auth:    false,
					},
				},
			},
		},
		Auth: AuthConfig{
			JWTSecret:   "test-secret",
			TokenExpiry: 24 * time.Hour,
		},
		RateLimit: RateLimitConfig{
			RequestsPerSecond: 100,
			Burst:             200,
		},
		Monitoring: MonitoringConfig{
			HealthCheckInterval: 30 * time.Second,
		},
	}

	gateway, err := NewGateway(config)
	require.NoError(t, err)

	health := gateway.GetHealth()
	assert.NotNil(t, health)
	assert.Equal(t, "healthy", health["status"])
	assert.NotNil(t, health["timestamp"])
	assert.NotNil(t, health["services"])
	assert.NotNil(t, health["metrics"])
}

func TestGatewayConfigValidation(t *testing.T) {
	tests := []struct {
		name        string
		config      *Config
		expectError bool
	}{
		{
			name:        "nil config",
			config:      nil,
			expectError: true,
		},
		{
			name: "invalid port",
			config: &Config{
				Port: 70000,
				Host: "localhost",
			},
			expectError: true,
		},
		{
			name: "empty host",
			config: &Config{
				Port: 8080,
				Host: "",
			},
			expectError: true,
		},
		{
			name: "no services",
			config: &Config{
				Port:     8080,
				Host:     "localhost",
				Services: map[string]ServiceConfig{},
			},
			expectError: true,
		},
		{
			name: "valid config",
			config: &Config{
				Port: 8080,
				Host: "localhost",
				Services: map[string]ServiceConfig{
					"test": {
						Name: "test",
						URL:  "http://localhost:8000",
					},
				},
			},
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateConfig(tt.config)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestRouterHealthHandler(t *testing.T) {
	config := &Config{
		Port: 8080,
		Host: "localhost",
		Services: map[string]ServiceConfig{
			"test": {
				Name: "test",
				URL:  "http://localhost:8000",
			},
		},
	}

	router, err := NewRouter(config)
	require.NoError(t, err)

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	router.healthHandler(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "application/json", w.Header().Get("Content-Type"))
	assert.Contains(t, w.Body.String(), "healthy")
}

func TestRouterNotFoundHandler(t *testing.T) {
	config := &Config{
		Port: 8080,
		Host: "localhost",
		Services: map[string]ServiceConfig{
			"test": {
				Name: "test",
				URL:  "http://localhost:8000",
			},
		},
	}

	router, err := NewRouter(config)
	require.NoError(t, err)

	req := httptest.NewRequest("GET", "/nonexistent", nil)
	w := httptest.NewRecorder()

	router.notFoundHandler(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
	assert.Equal(t, "application/json", w.Header().Get("Content-Type"))
	assert.Contains(t, w.Body.String(), "route not found")
}

func TestServiceDiscovery(t *testing.T) {
	config := &Config{
		Services: map[string]ServiceConfig{
			"test-service": {
				Name:   "test-service",
				URL:    "http://localhost:8000",
				Health: "http://localhost:8000/health",
			},
		},
		Monitoring: MonitoringConfig{
			HealthCheckInterval: 30 * time.Second,
		},
	}

	discovery, err := NewServiceDiscovery(config)
	require.NoError(t, err)

	// Test service discovery
	service, err := discovery.GetService("test-service")
	require.NoError(t, err)
	assert.Equal(t, "test-service", service.Name)
	assert.Equal(t, "http://localhost:8000", service.URL)

	// Test non-existent service
	_, err = discovery.GetService("nonexistent")
	assert.Error(t, err)

	// Test service status
	status := discovery.GetServiceStatus()
	assert.NotNil(t, status)
	assert.Contains(t, status, "test-service")
}

func TestLoadBalancer(t *testing.T) {
	config := &Config{
		Services: map[string]ServiceConfig{
			"test-service": {
				Name:   "test-service",
				URL:    "http://localhost:8000",
				Health: "http://localhost:8000/health",
				Weight: 1,
			},
		},
	}

	lb, err := NewLoadBalancer(config)
	require.NoError(t, err)

	// Test getting service instance
	instance, err := lb.GetNext("test-service")
	require.NoError(t, err)
	assert.Equal(t, "test-service", instance.Name)
	assert.Equal(t, "http://localhost:8000", instance.URL)

	// Test non-existent service
	_, err = lb.GetNext("nonexistent")
	assert.Error(t, err)

	// Test stats
	stats := lb.GetStats()
	assert.NotNil(t, stats)
}
