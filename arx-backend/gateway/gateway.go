package gateway

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"go.uber.org/zap"
)

// Gateway represents the main API Gateway that routes requests to appropriate services
type Gateway struct {
	router     *Router
	discovery  *ServiceDiscovery
	auth       *AuthMiddleware
	rateLimit  *RateLimitMiddleware
	monitoring *MonitoringMiddleware
	config     *Config
	logger     *zap.Logger
	server     *http.Server
	mu         sync.RWMutex
}

// Config holds the gateway configuration
type Config struct {
	Port           int                      `yaml:"port"`
	Host           string                   `yaml:"host"`
	ReadTimeout    time.Duration            `yaml:"read_timeout"`
	WriteTimeout   time.Duration            `yaml:"write_timeout"`
	IdleTimeout    time.Duration            `yaml:"idle_timeout"`
	MaxConnections int                      `yaml:"max_connections"`
	Services       map[string]ServiceConfig `yaml:"services"`
	Auth           AuthConfig               `yaml:"auth"`
	RateLimit      RateLimitConfig          `yaml:"rate_limit"`
	Monitoring     MonitoringConfig         `yaml:"monitoring"`
}

// ServiceConfig defines configuration for a service
type ServiceConfig struct {
	Name    string  `yaml:"name"`
	URL     string  `yaml:"url"`
	Health  string  `yaml:"health"`
	Routes  []Route `yaml:"routes"`
	Timeout int     `yaml:"timeout"`
	Retries int     `yaml:"retries"`
	Weight  int     `yaml:"weight"`
}

// Route defines a routing rule
type Route struct {
	Path      string           `yaml:"path"`
	Service   string           `yaml:"service"`
	Methods   []string         `yaml:"methods"`
	Auth      bool             `yaml:"auth"`
	RateLimit *RateLimitConfig `yaml:"rate_limit"`
	Transform *TransformConfig `yaml:"transform"`
}

// AuthConfig defines authentication configuration
type AuthConfig struct {
	JWTSecret     string        `yaml:"jwt_secret"`
	TokenExpiry   time.Duration `yaml:"token_expiry"`
	RefreshExpiry time.Duration `yaml:"refresh_expiry"`
	Roles         []string      `yaml:"roles"`
}

// RateLimitConfig defines rate limiting configuration
type RateLimitConfig struct {
	RequestsPerSecond int `yaml:"requests_per_second"`
	Burst             int `yaml:"burst"`
}

// MonitoringConfig defines monitoring configuration
type MonitoringConfig struct {
	MetricsPort         int                  `yaml:"metrics_port"`
	HealthCheckInterval time.Duration        `yaml:"health_check_interval"`
	CircuitBreaker      CircuitBreakerConfig `yaml:"circuit_breaker"`
	Logging             LoggingConfig        `yaml:"logging"`
}

// CircuitBreakerConfig defines circuit breaker configuration
type CircuitBreakerConfig struct {
	FailureThreshold int           `yaml:"failure_threshold"`
	Timeout          time.Duration `yaml:"timeout"`
}

// LoggingConfig defines logging configuration
type LoggingConfig struct {
	Level  string `yaml:"level"`
	Format string `yaml:"format"`
	Output string `yaml:"output"`
}

// TransformConfig defines request/response transformation
type TransformConfig struct {
	Headers map[string]string `yaml:"headers"`
	Query   map[string]string `yaml:"query"`
	Body    map[string]string `yaml:"body"`
}

// NewGateway creates a new API Gateway instance
func NewGateway(config *Config) (*Gateway, error) {
	if config == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}

	// Initialize logger
	logger, err := initLogger(config.Monitoring.Logging)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize logger: %w", err)
	}

	// Initialize router
	router, err := NewRouter(config)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize router: %w", err)
	}

	// Initialize service discovery
	discovery, err := NewServiceDiscovery(config)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize service discovery: %w", err)
	}

	// Initialize middleware
	auth, err := NewAuthMiddleware(config.Auth)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize auth middleware: %w", err)
	}

	rateLimit, err := NewRateLimitMiddleware(config.RateLimit)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize rate limit middleware: %w", err)
	}

	monitoring, err := NewMonitoringMiddleware(config.Monitoring)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize monitoring middleware: %w", err)
	}

	gateway := &Gateway{
		router:     router,
		discovery:  discovery,
		auth:       auth,
		rateLimit:  rateLimit,
		monitoring: monitoring,
		config:     config,
		logger:     logger,
	}

	return gateway, nil
}

// Start initializes and starts the gateway server
func (g *Gateway) Start() error {
	g.mu.Lock()
	defer g.mu.Unlock()

	// Create HTTP server
	g.server = &http.Server{
		Addr:         fmt.Sprintf("%s:%d", g.config.Host, g.config.Port),
		Handler:      g.createHandler(),
		ReadTimeout:  g.config.ReadTimeout,
		WriteTimeout: g.config.WriteTimeout,
		IdleTimeout:  g.config.IdleTimeout,
	}

	// Start service discovery
	if err := g.discovery.Start(); err != nil {
		return fmt.Errorf("failed to start service discovery: %w", err)
	}

	// Start monitoring
	if err := g.monitoring.Start(); err != nil {
		return fmt.Errorf("failed to start monitoring: %w", err)
	}

	g.logger.Info("Starting API Gateway",
		zap.String("host", g.config.Host),
		zap.Int("port", g.config.Port),
		zap.Duration("read_timeout", g.config.ReadTimeout),
		zap.Duration("write_timeout", g.config.WriteTimeout),
	)

	// Start server in goroutine
	go func() {
		if err := g.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			g.logger.Error("Server failed", zap.Error(err))
		}
	}()

	return nil
}

// Stop gracefully shuts down the gateway
func (g *Gateway) Stop(ctx context.Context) error {
	g.mu.Lock()
	defer g.mu.Unlock()

	g.logger.Info("Shutting down API Gateway")

	// Stop service discovery
	if err := g.discovery.Stop(); err != nil {
		g.logger.Error("Failed to stop service discovery", zap.Error(err))
	}

	// Stop monitoring
	if err := g.monitoring.Stop(); err != nil {
		g.logger.Error("Failed to stop monitoring", zap.Error(err))
	}

	// Shutdown server
	if g.server != nil {
		if err := g.server.Shutdown(ctx); err != nil {
			return fmt.Errorf("failed to shutdown server: %w", err)
		}
	}

	g.logger.Info("API Gateway stopped successfully")
	return nil
}

// createHandler creates the main HTTP handler with all middleware
func (g *Gateway) createHandler() http.Handler {
	r := chi.NewRouter()

	// Add basic middleware
	r.Use(chimiddleware.Logger)
	r.Use(chimiddleware.Recoverer)
	r.Use(chimiddleware.RequestID)
	r.Use(chimiddleware.RealIP)
	r.Use(chimiddleware.Timeout(g.config.ReadTimeout))

	// Add custom middleware
	r.Use(g.monitoring.Middleware())
	r.Use(g.rateLimit.Middleware())
	r.Use(g.auth.Middleware())

	// Add routes
	g.router.RegisterRoutes(r)

	return r
}

// GetHealth returns the health status of the gateway
func (g *Gateway) GetHealth() map[string]interface{} {
	return map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC(),
		"services":  g.discovery.GetServiceStatus(),
		"metrics":   g.monitoring.GetMetrics(),
	}
}

// GetConfig returns the current gateway configuration
func (g *Gateway) GetConfig() *Config {
	return g.config
}

// UpdateConfig updates the gateway configuration
func (g *Gateway) UpdateConfig(config *Config) error {
	g.mu.Lock()
	defer g.mu.Unlock()

	// Validate new config
	if err := validateConfig(config); err != nil {
		return fmt.Errorf("invalid configuration: %w", err)
	}

	// Update components
	if err := g.router.UpdateConfig(config); err != nil {
		return fmt.Errorf("failed to update router config: %w", err)
	}

	if err := g.discovery.UpdateConfig(config); err != nil {
		return fmt.Errorf("failed to update service discovery config: %w", err)
	}

	if err := g.auth.UpdateConfig(config.Auth); err != nil {
		return fmt.Errorf("failed to update auth config: %w", err)
	}

	if err := g.rateLimit.UpdateConfig(config.RateLimit); err != nil {
		return fmt.Errorf("failed to update rate limit config: %w", err)
	}

	if err := g.monitoring.UpdateConfig(config.Monitoring); err != nil {
		return fmt.Errorf("failed to update monitoring config: %w", err)
	}

	g.config = config
	g.logger.Info("Gateway configuration updated successfully")

	return nil
}

// initLogger initializes the logger based on configuration
func initLogger(config LoggingConfig) (*zap.Logger, error) {
	var logger *zap.Logger
	var err error

	switch config.Level {
	case "debug":
		logger, err = zap.NewDevelopment()
	case "info":
		logger, err = zap.NewProduction()
	default:
		logger, err = zap.NewProduction()
	}

	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	return logger, nil
}

// validateConfig validates the gateway configuration
func validateConfig(config *Config) error {
	if config == nil {
		return fmt.Errorf("config cannot be nil")
	}

	if config.Port <= 0 || config.Port > 65535 {
		return fmt.Errorf("invalid port: %d", config.Port)
	}

	if config.Host == "" {
		return fmt.Errorf("host cannot be empty")
	}

	if config.ReadTimeout <= 0 {
		return fmt.Errorf("read timeout must be positive")
	}

	if config.WriteTimeout <= 0 {
		return fmt.Errorf("write timeout must be positive")
	}

	if config.IdleTimeout <= 0 {
		return fmt.Errorf("idle timeout must be positive")
	}

	if len(config.Services) == 0 {
		return fmt.Errorf("at least one service must be configured")
	}

	return nil
}
