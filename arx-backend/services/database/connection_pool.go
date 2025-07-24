package database

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// ConnectionStatus represents the status of a database connection
type ConnectionStatus string

const (
	StatusIdle   ConnectionStatus = "idle"
	StatusActive ConnectionStatus = "active"
	StatusError  ConnectionStatus = "error"
	StatusClosed ConnectionStatus = "closed"
)

// ConnectionInfo represents information about a database connection
type ConnectionInfo struct {
	ID           string           `json:"id"`
	Status       ConnectionStatus `json:"status"`
	CreatedAt    time.Time        `json:"created_at"`
	LastUsed     time.Time        `json:"last_used"`
	UseCount     int64            `json:"use_count"`
	ErrorCount   int64            `json:"error_count"`
	LastError    string           `json:"last_error"`
	IsHealthy    bool             `json:"is_healthy"`
	ResponseTime time.Duration    `json:"response_time"`
}

// PoolConfig holds connection pool configuration
type PoolConfig struct {
	MaxConnections      int           `json:"max_connections"`
	MinConnections      int           `json:"min_connections"`
	MaxIdleConnections  int           `json:"max_idle_connections"`
	ConnectionTimeout   time.Duration `json:"connection_timeout"`
	IdleTimeout         time.Duration `json:"idle_timeout"`
	MaxLifetime         time.Duration `json:"max_lifetime"`
	HealthCheckInterval time.Duration `json:"health_check_interval"`
	RetryAttempts       int           `json:"retry_attempts"`
	RetryDelay          time.Duration `json:"retry_delay"`
}

// ConnectionPool provides database connection pooling
type ConnectionPool struct {
	config   *PoolConfig
	dbConfig *DatabaseConfig
	logger   *zap.Logger
	mu       sync.RWMutex

	// Connection management
	connections map[string]*ConnectionInfo
	available   chan *sql.DB
	active      map[string]*sql.DB

	// Statistics
	stats *PoolStats

	// Health monitoring
	healthTicker *time.Ticker
	stopChan     chan bool
}

// PoolStats holds connection pool statistics
type PoolStats struct {
	TotalConnections    int64         `json:"total_connections"`
	ActiveConnections   int64         `json:"active_connections"`
	IdleConnections     int64         `json:"idle_connections"`
	ErrorConnections    int64         `json:"error_connections"`
	TotalRequests       int64         `json:"total_requests"`
	SuccessfulRequests  int64         `json:"successful_requests"`
	FailedRequests      int64         `json:"failed_requests"`
	AverageResponseTime time.Duration `json:"average_response_time"`
	LastHealthCheck     time.Time     `json:"last_health_check"`
}

// NewConnectionPool creates a new connection pool
func NewConnectionPool(config *DatabaseConfig, logger *zap.Logger) *ConnectionPool {
	poolConfig := &PoolConfig{
		MaxConnections:      20,
		MinConnections:      5,
		MaxIdleConnections:  10,
		ConnectionTimeout:   30 * time.Second,
		IdleTimeout:         5 * time.Minute,
		MaxLifetime:         1 * time.Hour,
		HealthCheckInterval: 30 * time.Second,
		RetryAttempts:       3,
		RetryDelay:          1 * time.Second,
	}

	cp := &ConnectionPool{
		config:      poolConfig,
		dbConfig:    config,
		logger:      logger,
		connections: make(map[string]*ConnectionInfo),
		available:   make(chan *sql.DB, poolConfig.MaxConnections),
		active:      make(map[string]*sql.DB),
		stats:       &PoolStats{},
		stopChan:    make(chan bool),
	}

	// Initialize minimum connections
	go cp.initializeConnections()

	// Start health monitoring
	go cp.startHealthMonitoring()

	logger.Info("Connection pool initialized",
		zap.Int("max_connections", poolConfig.MaxConnections),
		zap.Int("min_connections", poolConfig.MinConnections),
		zap.Duration("health_check_interval", poolConfig.HealthCheckInterval),
	)

	return cp
}

// GetConnection gets a connection from the pool
func (cp *ConnectionPool) GetConnection(ctx context.Context) (*sql.DB, error) {
	start := time.Now()

	select {
	case conn := <-cp.available:
		// Update connection info
		cp.updateConnectionUsage(conn)
		cp.stats.SuccessfulRequests++
		cp.stats.AverageResponseTime = cp.calculateAverageResponseTime(time.Since(start))

		cp.logger.Debug("Connection acquired from pool",
			zap.Duration("response_time", time.Since(start)))

		return conn, nil

	case <-ctx.Done():
		cp.stats.FailedRequests++
		return nil, fmt.Errorf("timeout waiting for connection: %w", ctx.Err())

	case <-time.After(cp.config.ConnectionTimeout):
		cp.stats.FailedRequests++
		return nil, fmt.Errorf("timeout waiting for connection after %v", cp.config.ConnectionTimeout)
	}
}

// ReleaseConnection releases a connection back to the pool
func (cp *ConnectionPool) ReleaseConnection(conn *sql.DB) {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	// Check if connection is still healthy
	if cp.isConnectionHealthy(conn) {
		select {
		case cp.available <- conn:
			cp.logger.Debug("Connection released back to pool")
		default:
			cp.logger.Warn("Connection pool is full, closing connection")
			conn.Close()
		}
	} else {
		cp.logger.Warn("Unhealthy connection closed")
		conn.Close()
		cp.stats.ErrorConnections++
	}
}

// Close closes the connection pool
func (cp *ConnectionPool) Close() error {
	cp.logger.Info("Closing connection pool")

	// Stop health monitoring
	close(cp.stopChan)
	if cp.healthTicker != nil {
		cp.healthTicker.Stop()
	}

	// Close all connections
	cp.mu.Lock()
	defer cp.mu.Unlock()

	// Close available connections
	close(cp.available)
	for conn := range cp.available {
		conn.Close()
	}

	// Close active connections
	for _, conn := range cp.active {
		conn.Close()
	}

	cp.logger.Info("Connection pool closed")
	return nil
}

// GetStats returns connection pool statistics
func (cp *ConnectionPool) GetStats() *PoolStats {
	cp.mu.RLock()
	defer cp.mu.RUnlock()

	cp.stats.TotalConnections = int64(len(cp.connections))
	cp.stats.ActiveConnections = int64(len(cp.active))
	cp.stats.IdleConnections = int64(len(cp.available))

	return cp.stats
}

// HealthCheck performs a health check on the connection pool
func (cp *ConnectionPool) HealthCheck() error {
	cp.mu.RLock()
	defer cp.mu.RUnlock()

	// Check if we have any healthy connections
	healthyCount := 0
	for _, connInfo := range cp.connections {
		if connInfo.IsHealthy {
			healthyCount++
		}
	}

	if healthyCount == 0 {
		return fmt.Errorf("no healthy connections available")
	}

	// Test a connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	conn, err := cp.GetConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to get connection for health check: %w", err)
	}

	defer cp.ReleaseConnection(conn)

	// Test the connection
	if err := conn.PingContext(ctx); err != nil {
		return fmt.Errorf("connection health check failed: %w", err)
	}

	cp.stats.LastHealthCheck = time.Now()
	return nil
}

// initializeConnections initializes the minimum number of connections
func (cp *ConnectionPool) initializeConnections() {
	for i := 0; i < cp.config.MinConnections; i++ {
		if err := cp.createConnection(); err != nil {
			cp.logger.Error("Failed to create initial connection", zap.Error(err))
		}
	}
}

// createConnection creates a new database connection
func (cp *ConnectionPool) createConnection() error {
	var db *sql.DB
	var err error

	switch cp.dbConfig.Type {
	case DatabaseSQLite:
		db, err = sql.Open("sqlite3", cp.dbConfig.ConnectionString)
	case DatabasePostgreSQL:
		db, err = sql.Open("postgres", cp.dbConfig.ConnectionString)
	default:
		return fmt.Errorf("unsupported database type: %s", cp.dbConfig.Type)
	}

	if err != nil {
		return fmt.Errorf("failed to open database connection: %w", err)
	}

	// Configure connection
	db.SetMaxOpenConns(1) // Each connection in pool is separate
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(cp.config.MaxLifetime)

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), cp.config.ConnectionTimeout)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}

	// Add to pool
	connID := fmt.Sprintf("conn_%d", time.Now().UnixNano())
	connInfo := &ConnectionInfo{
		ID:        connID,
		Status:    StatusIdle,
		CreatedAt: time.Now(),
		LastUsed:  time.Now(),
		IsHealthy: true,
	}

	cp.mu.Lock()
	cp.connections[connID] = connInfo
	cp.active[connID] = db
	cp.mu.Unlock()

	// Add to available channel
	select {
	case cp.available <- db:
		cp.logger.Debug("New connection added to pool", zap.String("conn_id", connID))
	default:
		cp.logger.Warn("Connection pool is full, closing new connection")
		db.Close()
	}

	return nil
}

// updateConnectionUsage updates connection usage statistics
func (cp *ConnectionPool) updateConnectionUsage(conn *sql.DB) {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	// Find connection info
	for connID, connInfo := range cp.connections {
		if cp.active[connID] == conn {
			connInfo.LastUsed = time.Now()
			connInfo.UseCount++
			connInfo.Status = StatusActive
			break
		}
	}
}

// isConnectionHealthy checks if a connection is healthy
func (cp *ConnectionPool) isConnectionHealthy(conn *sql.DB) bool {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	return conn.PingContext(ctx) == nil
}

// startHealthMonitoring starts the health monitoring goroutine
func (cp *ConnectionPool) startHealthMonitoring() {
	cp.healthTicker = time.NewTicker(cp.config.HealthCheckInterval)
	defer cp.healthTicker.Stop()

	for {
		select {
		case <-cp.healthTicker.C:
			cp.performHealthCheck()
		case <-cp.stopChan:
			return
		}
	}
}

// performHealthCheck performs a health check on all connections
func (cp *ConnectionPool) performHealthCheck() {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	unhealthyConnections := []string{}

	for connID, conn := range cp.active {
		if !cp.isConnectionHealthy(conn) {
			unhealthyConnections = append(unhealthyConnections, connID)
			cp.connections[connID].Status = StatusError
			cp.connections[connID].IsHealthy = false
			cp.connections[connID].ErrorCount++
		} else {
			cp.connections[connID].Status = StatusIdle
			cp.connections[connID].IsHealthy = true
		}
	}

	// Remove unhealthy connections
	for _, connID := range unhealthyConnections {
		if conn, exists := cp.active[connID]; exists {
			conn.Close()
			delete(cp.active, connID)
			delete(cp.connections, connID)
		}
	}

	// Create new connections if needed
	needed := cp.config.MinConnections - len(cp.active)
	for i := 0; i < needed; i++ {
		go cp.createConnection()
	}

	if len(unhealthyConnections) > 0 {
		cp.logger.Warn("Removed unhealthy connections",
			zap.Strings("conn_ids", unhealthyConnections))
	}

	cp.stats.LastHealthCheck = time.Now()
}

// calculateAverageResponseTime calculates the average response time
func (cp *ConnectionPool) calculateAverageResponseTime(newResponseTime time.Duration) time.Duration {
	if cp.stats.SuccessfulRequests == 1 {
		return newResponseTime
	}

	// Simple moving average
	currentAvg := cp.stats.AverageResponseTime
	newAvg := (currentAvg + newResponseTime) / 2
	return newAvg
}

// GetConnectionInfo returns information about all connections
func (cp *ConnectionPool) GetConnectionInfo() map[string]*ConnectionInfo {
	cp.mu.RLock()
	defer cp.mu.RUnlock()

	result := make(map[string]*ConnectionInfo)
	for connID, connInfo := range cp.connections {
		result[connID] = connInfo
	}

	return result
}

// ResetPool resets the connection pool
func (cp *ConnectionPool) ResetPool() error {
	cp.logger.Info("Resetting connection pool")

	// Close all existing connections
	cp.Close()

	// Reinitialize
	cp.available = make(chan *sql.DB, cp.config.MaxConnections)
	cp.active = make(map[string]*sql.DB)
	cp.connections = make(map[string]*ConnectionInfo)
	cp.stats = &PoolStats{}
	cp.stopChan = make(chan bool)

	// Initialize new connections
	go cp.initializeConnections()
	go cp.startHealthMonitoring()

	return nil
}
