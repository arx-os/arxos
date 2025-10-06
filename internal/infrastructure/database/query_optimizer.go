package database

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/jmoiron/sqlx"
)

// QueryOptimizer provides query optimization and caching
type QueryOptimizer struct {
	pool               *ConnectionPool
	cache              QueryCache
	slowQueryThreshold time.Duration
	logger             domain.Logger
}

// QueryCache provides query result caching
type QueryCache interface {
	Get(ctx context.Context, key string) (any, error)
	Set(ctx context.Context, key string, value any, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
	Clear(ctx context.Context) error
}

// QueryStats tracks query performance statistics
type QueryStats struct {
	Query        string        `json:"query"`
	Duration     time.Duration `json:"duration"`
	RowsAffected int64         `json:"rows_affected"`
	CacheHit     bool          `json:"cache_hit"`
	SlowQuery    bool          `json:"slow_query"`
	Timestamp    time.Time     `json:"timestamp"`
}

// QueryPlan represents a query execution plan
type QueryPlan struct {
	Query    string         `json:"query"`
	Args     []any          `json:"args"`
	CacheKey string         `json:"cache_key"`
	CacheTTL time.Duration  `json:"cache_ttl"`
	ReadOnly bool           `json:"read_only"`
	Timeout  time.Duration  `json:"timeout"`
	Retries  int            `json:"retries"`
	Metadata map[string]any `json:"metadata"`
}

// NewQueryOptimizer creates a new query optimizer
func NewQueryOptimizer(pool *ConnectionPool, cache QueryCache, logger domain.Logger) *QueryOptimizer {
	return &QueryOptimizer{
		pool:               pool,
		cache:              cache,
		slowQueryThreshold: 100 * time.Millisecond,
		logger:             logger,
	}
}

// ExecuteQuery executes a query with optimization
func (qo *QueryOptimizer) ExecuteQuery(ctx context.Context, plan *QueryPlan) (*QueryResult, error) {
	start := time.Now()

	// Check cache first for read-only queries
	var result *QueryResult
	var cacheHit bool

	if plan.ReadOnly && plan.CacheKey != "" {
		if cached, err := qo.cache.Get(ctx, plan.CacheKey); err == nil && cached != nil {
			if cachedResult, ok := cached.(*QueryResult); ok {
				result = cachedResult
				cacheHit = true
				qo.logger.Debug("Query cache hit", "key", plan.CacheKey)
			}
		}
	}

	// Execute query if not cached
	if result == nil {
		var err error
		result, err = qo.executeQueryWithRetry(ctx, plan)
		if err != nil {
			return nil, fmt.Errorf("query execution failed: %w", err)
		}

		// Cache result for read-only queries
		if plan.ReadOnly && plan.CacheKey != "" && plan.CacheTTL > 0 {
			if err := qo.cache.Set(ctx, plan.CacheKey, result, plan.CacheTTL); err != nil {
				qo.logger.Warn("Failed to cache query result", "error", err)
			}
		}
	}

	// Track query statistics
	duration := time.Since(start)
	stats := &QueryStats{
		Query:        plan.Query,
		Duration:     duration,
		RowsAffected: result.RowsAffected,
		CacheHit:     cacheHit,
		SlowQuery:    duration > qo.slowQueryThreshold,
		Timestamp:    time.Now(),
	}

	// Log slow queries
	if stats.SlowQuery {
		qo.logger.Warn("Slow query detected",
			"query", plan.Query,
			"duration", duration,
			"rows_affected", result.RowsAffected,
		)
	}

	// Add metadata to result
	result.Stats = stats
	result.Metadata = plan.Metadata

	return result, nil
}

// executeQueryWithRetry executes a query with retry logic
func (qo *QueryOptimizer) executeQueryWithRetry(ctx context.Context, plan *QueryPlan) (*QueryResult, error) {
	var lastErr error

	for attempt := 0; attempt <= plan.Retries; attempt++ {
		// Set timeout for this attempt
		queryCtx := ctx
		if plan.Timeout > 0 {
			var cancel context.CancelFunc
			queryCtx, cancel = context.WithTimeout(ctx, plan.Timeout)
			defer cancel()
		}

		// Get appropriate connection
		conn := qo.getConnection(plan.ReadOnly)

		// Execute query
		result, err := qo.executeSingleQuery(queryCtx, conn, plan)
		if err == nil {
			return result, nil
		}

		lastErr = err

		// Check if error is retryable
		if !qo.isRetryableError(err) {
			break
		}

		// Wait before retry
		if attempt < plan.Retries {
			time.Sleep(time.Duration(attempt+1) * 100 * time.Millisecond)
		}
	}

	return nil, fmt.Errorf("query failed after %d attempts: %w", plan.Retries+1, lastErr)
}

// executeSingleQuery executes a single query
func (qo *QueryOptimizer) executeSingleQuery(ctx context.Context, conn *sqlx.DB, plan *QueryPlan) (*QueryResult, error) {
	// Determine query type
	queryType := qo.getQueryType(plan.Query)

	switch queryType {
	case "SELECT":
		return qo.executeSelectQuery(ctx, conn, plan)
	case "INSERT", "UPDATE", "DELETE":
		return qo.executeModifyQuery(ctx, conn, plan)
	default:
		return qo.executeGenericQuery(ctx, conn, plan)
	}
}

// executeSelectQuery executes a SELECT query
func (qo *QueryOptimizer) executeSelectQuery(ctx context.Context, conn *sqlx.DB, plan *QueryPlan) (*QueryResult, error) {
	rows, err := conn.QueryxContext(ctx, plan.Query, plan.Args...)
	if err != nil {
		return nil, fmt.Errorf("select query failed: %w", err)
	}
	defer rows.Close()

	var results []map[string]any
	for rows.Next() {
		row := make(map[string]any)
		if err := rows.MapScan(row); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		results = append(results, row)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("row iteration error: %w", err)
	}

	return &QueryResult{
		Data:         results,
		RowsAffected: int64(len(results)),
		QueryType:    "SELECT",
	}, nil
}

// executeModifyQuery executes INSERT/UPDATE/DELETE queries
func (qo *QueryOptimizer) executeModifyQuery(ctx context.Context, conn *sqlx.DB, plan *QueryPlan) (*QueryResult, error) {
	result, err := conn.ExecContext(ctx, plan.Query, plan.Args...)
	if err != nil {
		return nil, fmt.Errorf("modify query failed: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return nil, fmt.Errorf("failed to get rows affected: %w", err)
	}

	return &QueryResult{
		Data:         nil,
		RowsAffected: rowsAffected,
		QueryType:    qo.getQueryType(plan.Query),
	}, nil
}

// executeGenericQuery executes other query types
func (qo *QueryOptimizer) executeGenericQuery(ctx context.Context, conn *sqlx.DB, plan *QueryPlan) (*QueryResult, error) {
	result, err := conn.ExecContext(ctx, plan.Query, plan.Args...)
	if err != nil {
		return nil, fmt.Errorf("generic query failed: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		rowsAffected = 0 // Some queries don't support RowsAffected
	}

	return &QueryResult{
		Data:         nil,
		RowsAffected: rowsAffected,
		QueryType:    qo.getQueryType(plan.Query),
	}, nil
}

// getConnection returns the appropriate database connection
func (qo *QueryOptimizer) getConnection(readOnly bool) *sqlx.DB {
	if readOnly {
		return qo.pool.GetConnectionForRead()
	}
	return qo.pool.GetConnectionForWrite()
}

// getQueryType determines the type of SQL query
func (qo *QueryOptimizer) getQueryType(query string) string {
	query = strings.TrimSpace(strings.ToUpper(query))

	if strings.HasPrefix(query, "SELECT") {
		return "SELECT"
	} else if strings.HasPrefix(query, "INSERT") {
		return "INSERT"
	} else if strings.HasPrefix(query, "UPDATE") {
		return "UPDATE"
	} else if strings.HasPrefix(query, "DELETE") {
		return "DELETE"
	} else if strings.HasPrefix(query, "CREATE") {
		return "CREATE"
	} else if strings.HasPrefix(query, "DROP") {
		return "DROP"
	} else if strings.HasPrefix(query, "ALTER") {
		return "ALTER"
	}

	return "UNKNOWN"
}

// isRetryableError checks if an error is retryable
func (qo *QueryOptimizer) isRetryableError(err error) bool {
	if err == nil {
		return false
	}

	errStr := err.Error()
	retryableErrors := []string{
		"connection reset by peer",
		"broken pipe",
		"connection refused",
		"timeout",
		"temporary failure",
		"server closed connection",
	}

	for _, retryableErr := range retryableErrors {
		if strings.Contains(strings.ToLower(errStr), retryableErr) {
			return true
		}
	}

	return false
}

// GenerateCacheKey generates a cache key for a query
func (qo *QueryOptimizer) GenerateCacheKey(query string, args []any) string {
	// Simple hash-based cache key generation
	key := fmt.Sprintf("query:%s:%v", query, args)
	return fmt.Sprintf("%x", []byte(key))
}

// InvalidateCache invalidates cached queries matching a pattern
func (qo *QueryOptimizer) InvalidateCache(ctx context.Context, pattern string) error {
	// This would need to be implemented based on the cache implementation
	// For now, we'll clear all cache
	return qo.cache.Clear(ctx)
}

// QueryResult represents the result of a query execution
type QueryResult struct {
	Data         []map[string]any `json:"data"`
	RowsAffected int64            `json:"rows_affected"`
	QueryType    string           `json:"query_type"`
	Stats        *QueryStats      `json:"stats,omitempty"`
	Metadata     map[string]any   `json:"metadata,omitempty"`
}

// GetStats returns query execution statistics
func (qr *QueryResult) GetStats() *QueryStats {
	return qr.Stats
}

// IsEmpty checks if the result is empty
func (qr *QueryResult) IsEmpty() bool {
	return len(qr.Data) == 0 && qr.RowsAffected == 0
}

// GetRowCount returns the number of rows in the result
func (qr *QueryResult) GetRowCount() int {
	return len(qr.Data)
}
