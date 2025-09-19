package postgis

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

// PoolConfig contains connection pool configuration
type PoolConfig struct {
	Host               string
	Port               int
	Database           string
	User               string
	Password           string
	SSLMode            string
	MaxOpenConnections int
	MaxIdleConnections int
	ConnMaxLifetime    time.Duration
	ConnMaxIdleTime    time.Duration
	HealthCheckPeriod  time.Duration
}

// DefaultPoolConfig returns optimized default configuration
func DefaultPoolConfig() PoolConfig {
	return PoolConfig{
		Host:               "localhost",
		Port:               5432,
		Database:           "arxos",
		SSLMode:            "prefer",
		MaxOpenConnections: 25,      // Optimized for typical workload
		MaxIdleConnections: 5,       // Keep some connections warm
		ConnMaxLifetime:    time.Hour,     // Refresh connections hourly
		ConnMaxIdleTime:    10 * time.Minute, // Close idle connections after 10 min
		HealthCheckPeriod:  30 * time.Second, // Health check every 30 seconds
	}
}

// ConnectionPool manages database connections with optimized pooling
type ConnectionPool struct {
	db        *sqlx.DB
	config    PoolConfig
	stats     PoolStats
	mu        sync.RWMutex
	ctx       context.Context
	cancel    context.CancelFunc
	healthyCh chan bool
}

// PoolStats tracks connection pool statistics
type PoolStats struct {
	TotalConnections   int
	IdleConnections    int
	InUseConnections   int
	WaitCount          int64
	WaitDuration       time.Duration
	MaxIdleClosed      int64
	MaxLifetimeClosed  int64
	HealthChecksFailed int64
	LastHealthCheck    time.Time
	Healthy            bool
}

// NewConnectionPool creates an optimized connection pool
func NewConnectionPool(config PoolConfig) (*ConnectionPool, error) {
	// Build connection string
	dsn := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s "+
			"connect_timeout=10 statement_timeout=30000 idle_in_transaction_session_timeout=60000",
		config.Host, config.Port, config.User, config.Password, config.Database, config.SSLMode,
	)

	// Open database connection
	db, err := sqlx.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(config.MaxOpenConnections)
	db.SetMaxIdleConns(config.MaxIdleConnections)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(config.ConnMaxIdleTime)

	// Verify connection
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Verify PostGIS extension
	var postgisVersion string
	if err := db.Get(&postgisVersion, "SELECT PostGIS_Version()"); err != nil {
		db.Close()
		return nil, fmt.Errorf("PostGIS extension not available: %w", err)
	}

	log.Printf("Connected to PostGIS: %s", postgisVersion)

	ctx, cancel := context.WithCancel(context.Background())

	pool := &ConnectionPool{
		db:        db,
		config:    config,
		ctx:       ctx,
		cancel:    cancel,
		healthyCh: make(chan bool, 1),
		stats: PoolStats{
			Healthy: true,
		},
	}

	// Start health check routine
	go pool.healthCheckLoop()

	// Start stats collection routine
	go pool.statsCollectionLoop()

	return pool, nil
}

// GetDB returns the underlying database connection
func (p *ConnectionPool) GetDB() *sqlx.DB {
	return p.db
}

// Close closes the connection pool
func (p *ConnectionPool) Close() error {
	p.cancel()
	return p.db.Close()
}

// healthCheckLoop performs periodic health checks
func (p *ConnectionPool) healthCheckLoop() {
	ticker := time.NewTicker(p.config.HealthCheckPeriod)
	defer ticker.Stop()

	for {
		select {
		case <-p.ctx.Done():
			return
		case <-ticker.C:
			p.performHealthCheck()
		}
	}
}

// performHealthCheck checks database health
func (p *ConnectionPool) performHealthCheck() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	healthy := true

	// Check basic connectivity
	if err := p.db.PingContext(ctx); err != nil {
		healthy = false
		p.incrementHealthCheckFailed()
		log.Printf("Health check failed: ping error: %v", err)
	}

	// Check PostGIS functionality
	var result int
	err := p.db.GetContext(ctx, &result, "SELECT 1")
	if err != nil {
		healthy = false
		p.incrementHealthCheckFailed()
		log.Printf("Health check failed: query error: %v", err)
	}

	// Check connection pool health
	stats := p.db.Stats()
	if stats.OpenConnections == 0 {
		healthy = false
		log.Printf("Health check warning: no open connections")
	}

	// Update health status
	p.mu.Lock()
	p.stats.Healthy = healthy
	p.stats.LastHealthCheck = time.Now()
	p.mu.Unlock()

	// Notify health status
	select {
	case p.healthyCh <- healthy:
	default:
	}
}

// statsCollectionLoop collects connection pool statistics
func (p *ConnectionPool) statsCollectionLoop() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-p.ctx.Done():
			return
		case <-ticker.C:
			p.collectStats()
		}
	}
}

// collectStats updates pool statistics
func (p *ConnectionPool) collectStats() {
	stats := p.db.Stats()

	p.mu.Lock()
	p.stats.TotalConnections = stats.OpenConnections
	p.stats.IdleConnections = stats.Idle
	p.stats.InUseConnections = stats.InUse
	p.stats.WaitCount = stats.WaitCount
	p.stats.WaitDuration = stats.WaitDuration
	p.stats.MaxIdleClosed = stats.MaxIdleClosed
	p.stats.MaxLifetimeClosed = stats.MaxLifetimeClosed
	p.mu.Unlock()

	// Log if connection pool is under pressure
	if stats.WaitCount > 0 {
		avgWait := time.Duration(0)
		if stats.WaitCount > 0 {
			avgWait = stats.WaitDuration / time.Duration(stats.WaitCount)
		}
		log.Printf("Connection pool pressure: %d waits, avg wait time: %v", stats.WaitCount, avgWait)
	}

	// Warn if approaching connection limit
	utilizationPct := float64(stats.InUse) / float64(p.config.MaxOpenConnections) * 100
	if utilizationPct > 80 {
		log.Printf("High connection pool utilization: %.1f%% (%d/%d)",
			utilizationPct, stats.InUse, p.config.MaxOpenConnections)
	}
}

// GetStats returns current pool statistics
func (p *ConnectionPool) GetStats() PoolStats {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.stats
}

// IsHealthy returns true if the pool is healthy
func (p *ConnectionPool) IsHealthy() bool {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.stats.Healthy
}

// incrementHealthCheckFailed increments failed health check counter
func (p *ConnectionPool) incrementHealthCheckFailed() {
	p.mu.Lock()
	p.stats.HealthChecksFailed++
	p.mu.Unlock()
}

// ExecuteWithRetry executes a query with automatic retry on connection errors
func (p *ConnectionPool) ExecuteWithRetry(ctx context.Context, fn func(*sqlx.DB) error) error {
	maxRetries := 3
	backoff := 100 * time.Millisecond

	for attempt := 0; attempt < maxRetries; attempt++ {
		err := fn(p.db)
		if err == nil {
			return nil
		}

		// Check if error is retryable
		if !isRetryableError(err) {
			return err
		}

		if attempt < maxRetries-1 {
			log.Printf("Retryable error (attempt %d/%d): %v", attempt+1, maxRetries, err)
			time.Sleep(backoff)
			backoff *= 2 // Exponential backoff
		}
	}

	return fmt.Errorf("max retries exceeded")
}

// isRetryableError checks if an error is retryable
func isRetryableError(err error) bool {
	if err == nil {
		return false
	}

	errStr := err.Error()
	retryableErrors := []string{
		"connection refused",
		"connection reset",
		"broken pipe",
		"bad connection",
		"driver: bad connection",
		"sql: database is closed",
	}

	for _, retryable := range retryableErrors {
		if contains(errStr, retryable) {
			return true
		}
	}

	return false
}

// contains checks if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && (s[:len(substr)] == substr || contains(s[1:], substr)))
}

// WarmUp pre-creates connections to reduce latency
func (p *ConnectionPool) WarmUp(ctx context.Context) error {
	log.Println("Warming up connection pool...")

	numConnections := p.config.MaxIdleConnections
	var wg sync.WaitGroup
	errors := make(chan error, numConnections)

	for i := 0; i < numConnections; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			// Execute a simple query to establish connection
			var result int
			err := p.db.GetContext(ctx, &result, "SELECT 1")
			if err != nil {
				errors <- fmt.Errorf("warmup connection %d failed: %w", id, err)
			}
		}(i)
	}

	wg.Wait()
	close(errors)

	// Check for errors
	var errs []error
	for err := range errors {
		errs = append(errs, err)
	}

	if len(errs) > 0 {
		return fmt.Errorf("warmup failed with %d errors: %v", len(errs), errs[0])
	}

	log.Printf("Connection pool warmed up with %d connections", numConnections)
	return nil
}

// OptimizeForWorkload adjusts pool settings based on workload
func (p *ConnectionPool) OptimizeForWorkload(workloadType string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	switch workloadType {
	case "read_heavy":
		// More connections for read-heavy workloads
		p.config.MaxOpenConnections = 50
		p.config.MaxIdleConnections = 20
		p.db.SetMaxOpenConns(50)
		p.db.SetMaxIdleConns(20)
		log.Println("Optimized pool for read-heavy workload")

	case "write_heavy":
		// Fewer but longer-lived connections for writes
		p.config.MaxOpenConnections = 20
		p.config.MaxIdleConnections = 10
		p.config.ConnMaxLifetime = 2 * time.Hour
		p.db.SetMaxOpenConns(20)
		p.db.SetMaxIdleConns(10)
		p.db.SetConnMaxLifetime(2 * time.Hour)
		log.Println("Optimized pool for write-heavy workload")

	case "mixed":
		// Balanced configuration
		p.config.MaxOpenConnections = 30
		p.config.MaxIdleConnections = 10
		p.db.SetMaxOpenConns(30)
		p.db.SetMaxIdleConns(10)
		log.Println("Optimized pool for mixed workload")

	case "burst":
		// Handle burst traffic
		p.config.MaxOpenConnections = 100
		p.config.MaxIdleConnections = 5
		p.config.ConnMaxIdleTime = 5 * time.Minute
		p.db.SetMaxOpenConns(100)
		p.db.SetMaxIdleConns(5)
		p.db.SetConnMaxIdleTime(5 * time.Minute)
		log.Println("Optimized pool for burst traffic")
	}
}