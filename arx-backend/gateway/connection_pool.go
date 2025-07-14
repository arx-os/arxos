package gateway

import (
	"fmt"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// ConnectionPool manages HTTP connections for performance optimization
type ConnectionPool struct {
	config  ConnectionPoolConfig
	logger  *zap.Logger
	pools   map[string]*ServiceConnectionPool
	mu      sync.RWMutex
	metrics *ConnectionPoolMetrics
}

// ConnectionPoolConfig defines connection pool configuration
type ConnectionPoolConfig struct {
	Enabled            bool            `yaml:"enabled"`
	MaxConnections     int             `yaml:"max_connections"`
	MaxIdleConnections int             `yaml:"max_idle_connections"`
	IdleTimeout        time.Duration   `yaml:"idle_timeout"`
	MaxLifetime        time.Duration   `yaml:"max_lifetime"`
	KeepAlive          time.Duration   `yaml:"keep_alive"`
	DisableCompression bool            `yaml:"disable_compression"`
	TransportConfig    TransportConfig `yaml:"transport_config"`
}

// TransportConfig defines HTTP transport configuration
type TransportConfig struct {
	DialTimeout           time.Duration `yaml:"dial_timeout"`
	ResponseHeaderTimeout time.Duration `yaml:"response_header_timeout"`
	ExpectContinueTimeout time.Duration `yaml:"expect_continue_timeout"`
	IdleConnTimeout       time.Duration `yaml:"idle_conn_timeout"`
	TLSHandshakeTimeout   time.Duration `yaml:"tls_handshake_timeout"`
	MaxIdleConnsPerHost   int           `yaml:"max_idle_conns_per_host"`
	MaxConnsPerHost       int           `yaml:"max_conns_per_host"`
}

// ServiceConnectionPool manages connections for a specific service
type ServiceConnectionPool struct {
	serviceName string
	config      ConnectionPoolConfig
	transport   *http.Transport
	client      *http.Client
	mu          sync.RWMutex
	stats       *PoolStats
}

// PoolStats holds connection pool statistics
type PoolStats struct {
	TotalConnections   int64
	ActiveConnections  int64
	IdleConnections    int64
	ConnectionErrors   int64
	ConnectionTimeouts int64
	LastConnectionTime time.Time
	mu                 sync.RWMutex
}

// ConnectionPoolMetrics holds connection pool metrics
type ConnectionPoolMetrics struct {
	totalConnections   *prometheus.GaugeVec
	activeConnections  *prometheus.GaugeVec
	idleConnections    *prometheus.GaugeVec
	connectionErrors   *prometheus.CounterVec
	connectionTimeouts *prometheus.CounterVec
	requestDuration    *prometheus.HistogramVec
}

// NewConnectionPool creates a new connection pool
func NewConnectionPool(config ConnectionPoolConfig) (*ConnectionPool, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	cp := &ConnectionPool{
		config: config,
		logger: logger,
		pools:  make(map[string]*ServiceConnectionPool),
	}

	// Initialize metrics
	cp.initializeMetrics()

	return cp, nil
}

// initializeMetrics initializes connection pool metrics
func (cp *ConnectionPool) initializeMetrics() {
	cp.metrics = &ConnectionPoolMetrics{
		totalConnections: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_connection_pool_total_connections",
				Help: "Total connections in pool",
			},
			[]string{"service"},
		),
		activeConnections: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_connection_pool_active_connections",
				Help: "Active connections in pool",
			},
			[]string{"service"},
		),
		idleConnections: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_connection_pool_idle_connections",
				Help: "Idle connections in pool",
			},
			[]string{"service"},
		),
		connectionErrors: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_connection_pool_errors_total",
				Help: "Total connection errors",
			},
			[]string{"service", "error_type"},
		),
		connectionTimeouts: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_connection_pool_timeouts_total",
				Help: "Total connection timeouts",
			},
			[]string{"service"},
		),
		requestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_connection_pool_request_duration_seconds",
				Help:    "Request duration through connection pool",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service"},
		),
	}
}

// GetPool gets or creates a connection pool for a service
func (cp *ConnectionPool) GetPool(serviceName string) (*ServiceConnectionPool, error) {
	cp.mu.RLock()
	pool, exists := cp.pools[serviceName]
	cp.mu.RUnlock()

	if exists {
		return pool, nil
	}

	cp.mu.Lock()
	defer cp.mu.Unlock()

	// Double-check after acquiring lock
	if pool, exists := cp.pools[serviceName]; exists {
		return pool, nil
	}

	// Create new pool
	pool, err := cp.createPool(serviceName)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool for %s: %w", serviceName, err)
	}

	cp.pools[serviceName] = pool
	cp.logger.Info("Connection pool created",
		zap.String("service", serviceName),
		zap.Int("max_connections", cp.config.MaxConnections),
		zap.Int("max_idle_connections", cp.config.MaxIdleConnections),
	)

	return pool, nil
}

// createPool creates a new service connection pool
func (cp *ConnectionPool) createPool(serviceName string) (*ServiceConnectionPool, error) {
	// Create custom transport
	transport := &http.Transport{
		Proxy: http.ProxyFromEnvironment,
		DialContext: (&net.Dialer{
			Timeout:   cp.config.TransportConfig.DialTimeout,
			KeepAlive: cp.config.KeepAlive,
		}).DialContext,
		MaxIdleConns:          cp.config.MaxIdleConnections,
		MaxIdleConnsPerHost:   cp.config.TransportConfig.MaxIdleConnsPerHost,
		MaxConnsPerHost:       cp.config.TransportConfig.MaxConnsPerHost,
		IdleConnTimeout:       cp.config.IdleTimeout,
		TLSHandshakeTimeout:   cp.config.TransportConfig.TLSHandshakeTimeout,
		ExpectContinueTimeout: cp.config.TransportConfig.ExpectContinueTimeout,
		ResponseHeaderTimeout: cp.config.TransportConfig.ResponseHeaderTimeout,
		DisableCompression:    cp.config.DisableCompression,
	}

	// Create HTTP client
	client := &http.Client{
		Transport: transport,
		Timeout:   30 * time.Second, // Default timeout
	}

	pool := &ServiceConnectionPool{
		serviceName: serviceName,
		config:      cp.config,
		transport:   transport,
		client:      client,
		stats:       &PoolStats{},
	}

	return pool, nil
}

// Do executes an HTTP request using the connection pool
func (cp *ConnectionPool) Do(serviceName string, request *http.Request) (*http.Response, error) {
	if !cp.config.Enabled {
		// Use default HTTP client if pooling is disabled
		client := &http.Client{Timeout: 30 * time.Second}
		return client.Do(request)
	}

	pool, err := cp.GetPool(serviceName)
	if err != nil {
		return nil, fmt.Errorf("failed to get connection pool: %w", err)
	}

	return pool.Do(request)
}

// Do executes an HTTP request using the service connection pool
func (scp *ServiceConnectionPool) Do(request *http.Request) (*http.Response, error) {
	start := time.Now()

	// Update stats
	scp.stats.mu.Lock()
	scp.stats.TotalConnections++
	scp.stats.ActiveConnections++
	scp.stats.LastConnectionTime = time.Now()
	scp.stats.mu.Unlock()

	// Execute request
	response, err := scp.client.Do(request)

	// Update stats
	scp.stats.mu.Lock()
	scp.stats.ActiveConnections--
	if err != nil {
		scp.stats.ConnectionErrors++
	} else {
		scp.stats.IdleConnections++
	}
	scp.stats.mu.Unlock()

	// Update metrics
	duration := time.Since(start)
	cp.metrics.requestDuration.WithLabelValues(scp.serviceName).Observe(duration.Seconds())

	if err != nil {
		cp.metrics.connectionErrors.WithLabelValues(scp.serviceName, "request_error").Inc()
		scp.logger.Error("Connection pool request failed",
			zap.String("service", scp.serviceName),
			zap.String("url", request.URL.String()),
			zap.Error(err),
		)
		return nil, err
	}

	// Check for timeout
	if response.StatusCode == 408 || response.StatusCode == 504 {
		cp.metrics.connectionTimeouts.WithLabelValues(scp.serviceName).Inc()
		scp.stats.mu.Lock()
		scp.stats.ConnectionTimeouts++
		scp.stats.mu.Unlock()
	}

	return response, nil
}

// Close closes all connection pools
func (cp *ConnectionPool) Close() error {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	for serviceName, pool := range cp.pools {
		if err := pool.Close(); err != nil {
			cp.logger.Error("Failed to close connection pool",
				zap.String("service", serviceName),
				zap.Error(err),
			)
		}
	}

	cp.logger.Info("All connection pools closed")
	return nil
}

// Close closes the service connection pool
func (scp *ServiceConnectionPool) Close() error {
	// Close idle connections
	scp.transport.CloseIdleConnections()

	scp.logger.Info("Connection pool closed",
		zap.String("service", scp.serviceName),
	)

	return nil
}

// GetStats returns connection pool statistics
func (cp *ConnectionPool) GetStats() map[string]interface{} {
	cp.mu.RLock()
	defer cp.mu.RUnlock()

	stats := make(map[string]interface{})
	for serviceName, pool := range cp.pools {
		poolStats := pool.GetStats()
		stats[serviceName] = poolStats
	}

	return stats
}

// GetStats returns service connection pool statistics
func (scp *ServiceConnectionPool) GetStats() map[string]interface{} {
	scp.stats.mu.RLock()
	defer scp.stats.mu.RUnlock()

	return map[string]interface{}{
		"total_connections":    scp.stats.TotalConnections,
		"active_connections":   scp.stats.ActiveConnections,
		"idle_connections":     scp.stats.IdleConnections,
		"connection_errors":    scp.stats.ConnectionErrors,
		"connection_timeouts":  scp.stats.ConnectionTimeouts,
		"last_connection":      scp.stats.LastConnectionTime,
		"max_connections":      scp.config.MaxConnections,
		"max_idle_connections": scp.config.MaxIdleConnections,
		"idle_timeout":         scp.config.IdleTimeout,
		"max_lifetime":         scp.config.MaxLifetime,
	}
}

// UpdateMetrics updates connection pool metrics
func (cp *ConnectionPool) UpdateMetrics() {
	cp.mu.RLock()
	defer cp.mu.RUnlock()

	for serviceName, pool := range cp.pools {
		stats := pool.GetStats()

		cp.metrics.totalConnections.WithLabelValues(serviceName).Set(float64(stats["total_connections"].(int64)))
		cp.metrics.activeConnections.WithLabelValues(serviceName).Set(float64(stats["active_connections"].(int64)))
		cp.metrics.idleConnections.WithLabelValues(serviceName).Set(float64(stats["idle_connections"].(int64)))
	}
}

// UpdateConfig updates the connection pool configuration
func (cp *ConnectionPool) UpdateConfig(config ConnectionPoolConfig) error {
	cp.config = config
	cp.logger.Info("Connection pool configuration updated")
	return nil
}

// GetConnectionPoolStats returns detailed connection pool statistics
func (cp *ConnectionPool) GetConnectionPoolStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":              cp.config.Enabled,
		"max_connections":      cp.config.MaxConnections,
		"max_idle_connections": cp.config.MaxIdleConnections,
		"idle_timeout":         cp.config.IdleTimeout,
		"max_lifetime":         cp.config.MaxLifetime,
		"keep_alive":           cp.config.KeepAlive,
		"disable_compression":  cp.config.DisableCompression,
		"pools_count":          len(cp.pools),
		"services":             cp.GetStats(),
	}
}
