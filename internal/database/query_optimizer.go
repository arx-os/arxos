package database

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// QueryOptimizer provides database query optimization utilities
type QueryOptimizer struct {
	db *sql.DB
}

// NewQueryOptimizer creates a new query optimizer
func NewQueryOptimizer(db *sql.DB) *QueryOptimizer {
	return &QueryOptimizer{db: db}
}

// OptimizedQuery represents a query with optimization metadata
type OptimizedQuery struct {
	Query     string
	Params    []interface{}
	Timeout   time.Duration
	UseIndex  bool
	BatchSize int
	CacheKey  string
	CacheTTL  time.Duration
}

// QueryStats represents query performance statistics
type QueryStats struct {
	Query        string
	Duration     time.Duration
	RowsAffected int64
	CacheHit     bool
	IndexUsed    bool
	Error        error
}

// OptimizeSpatialQuery optimizes spatial queries for PostGIS
func (qo *QueryOptimizer) OptimizeSpatialQuery(query string, params []interface{}) *OptimizedQuery {
	optimized := &OptimizedQuery{
		Query:     query,
		Params:    params,
		Timeout:   30 * time.Second,
		UseIndex:  true,
		BatchSize: 1000,
		CacheTTL:  5 * time.Minute,
	}

	// Add spatial index hints for common patterns
	if strings.Contains(strings.ToUpper(query), "ST_DISTANCE") {
		optimized.Query = qo.addSpatialIndexHint(optimized.Query, "equipment_spatial_geom_idx")
	}

	if strings.Contains(strings.ToUpper(query), "ST_CONTAINS") ||
		strings.Contains(strings.ToUpper(query), "ST_INTERSECTS") {
		optimized.Query = qo.addSpatialIndexHint(optimized.Query, "equipment_spatial_geom_idx")
	}

	if strings.Contains(strings.ToUpper(query), "ST_WITHIN") {
		optimized.Query = qo.addSpatialIndexHint(optimized.Query, "equipment_spatial_geom_idx")
	}

	// Add query timeout
	optimized.Query = qo.addQueryTimeout(optimized.Query, optimized.Timeout)

	return optimized
}

// OptimizeEquipmentQuery optimizes equipment-related queries
func (qo *QueryOptimizer) OptimizeEquipmentQuery(query string, params []interface{}) *OptimizedQuery {
	optimized := &OptimizedQuery{
		Query:     query,
		Params:    params,
		Timeout:   15 * time.Second,
		UseIndex:  true,
		BatchSize: 500,
		CacheTTL:  2 * time.Minute,
	}

	// Add equipment-specific optimizations
	if strings.Contains(strings.ToUpper(query), "EQUIPMENT_SPATIAL") {
		optimized.Query = qo.addEquipmentIndexHints(optimized.Query)
	}

	// Add query timeout
	optimized.Query = qo.addQueryTimeout(optimized.Query, optimized.Timeout)

	return optimized
}

// OptimizeAnalyticsQuery optimizes analytics and reporting queries
func (qo *QueryOptimizer) OptimizeAnalyticsQuery(query string, params []interface{}) *OptimizedQuery {
	optimized := &OptimizedQuery{
		Query:     query,
		Params:    params,
		Timeout:   60 * time.Second,
		UseIndex:  true,
		BatchSize: 100,
		CacheTTL:  15 * time.Minute,
	}

	// Add analytics-specific optimizations
	if strings.Contains(strings.ToUpper(query), "COUNT") ||
		strings.Contains(strings.ToUpper(query), "SUM") ||
		strings.Contains(strings.ToUpper(query), "AVG") {
		optimized.Query = qo.addAnalyticsOptimizations(optimized.Query)
	}

	// Add query timeout
	optimized.Query = qo.addQueryTimeout(optimized.Query, optimized.Timeout)

	return optimized
}

// ExecuteOptimizedQuery executes an optimized query with monitoring
func (qo *QueryOptimizer) ExecuteOptimizedQuery(ctx context.Context, optimized *OptimizedQuery) (*QueryStats, error) {
	start := time.Now()
	stats := &QueryStats{
		Query: optimized.Query,
	}

	// Add context timeout
	queryCtx, cancel := context.WithTimeout(ctx, optimized.Timeout)
	defer cancel()

	// Execute query
	rows, err := qo.db.QueryContext(queryCtx, optimized.Query, optimized.Params...)
	if err != nil {
		stats.Error = err
		stats.Duration = time.Since(start)
		return stats, err
	}
	defer rows.Close()

	// Count rows (for SELECT queries)
	rowCount := int64(0)
	for rows.Next() {
		rowCount++
	}
	stats.RowsAffected = rowCount
	stats.Duration = time.Since(start)

	// Log slow queries
	if stats.Duration > 1*time.Second {
		logger.Warn("Slow query detected: %s (duration: %v, rows: %d)",
			optimized.Query, stats.Duration, stats.RowsAffected)
	}

	return stats, nil
}

// ExecuteOptimizedQueryRow executes an optimized single-row query
func (qo *QueryOptimizer) ExecuteOptimizedQueryRow(ctx context.Context, optimized *OptimizedQuery, dest ...interface{}) (*QueryStats, error) {
	start := time.Now()
	stats := &QueryStats{
		Query: optimized.Query,
	}

	// Add context timeout
	queryCtx, cancel := context.WithTimeout(ctx, optimized.Timeout)
	defer cancel()

	// Execute query
	err := qo.db.QueryRowContext(queryCtx, optimized.Query, optimized.Params...).Scan(dest...)
	stats.Duration = time.Since(start)

	if err != nil {
		stats.Error = err
		return stats, err
	}

	stats.RowsAffected = 1

	// Log slow queries
	if stats.Duration > 500*time.Millisecond {
		logger.Warn("Slow query detected: %s (duration: %v)",
			optimized.Query, stats.Duration)
	}

	return stats, nil
}

// addSpatialIndexHint adds spatial index hints to queries
func (qo *QueryOptimizer) addSpatialIndexHint(query, indexName string) string {
	// Add index hint for spatial queries
	// This is PostgreSQL-specific syntax
	if strings.Contains(strings.ToUpper(query), "FROM") {
		query = strings.Replace(query, "FROM equipment_spatial",
			fmt.Sprintf("FROM equipment_spatial /*+ INDEX(%s) */", indexName), 1)
	}
	return query
}

// addEquipmentIndexHints adds equipment-specific index hints
func (qo *QueryOptimizer) addEquipmentIndexHints(query string) string {
	// Add multiple index hints for equipment queries
	hints := []string{
		"equipment_spatial_equipment_id_idx",
		"equipment_spatial_building_id_idx",
		"equipment_spatial_geom_idx",
	}

	for _, hint := range hints {
		if strings.Contains(strings.ToUpper(query), "FROM") {
			query = strings.Replace(query, "FROM equipment_spatial",
				fmt.Sprintf("FROM equipment_spatial /*+ INDEX(%s) */", hint), 1)
			break
		}
	}

	return query
}

// addAnalyticsOptimizations adds analytics-specific optimizations
func (qo *QueryOptimizer) addAnalyticsOptimizations(query string) string {
	// Add materialized view hints for analytics
	if strings.Contains(strings.ToUpper(query), "COUNT") {
		query = "/*+ USE_MATERIALIZED_VIEW */ " + query
	}

	// Add parallel processing hints
	if strings.Contains(strings.ToUpper(query), "SUM") ||
		strings.Contains(strings.ToUpper(query), "AVG") {
		query = "/*+ PARALLEL(4) */ " + query
	}

	return query
}

// addQueryTimeout adds query timeout configuration
func (qo *QueryOptimizer) addQueryTimeout(query string, timeout time.Duration) string {
	// Add statement timeout
	timeoutMs := int(timeout.Milliseconds())
	return fmt.Sprintf("SET statement_timeout = %d; %s", timeoutMs, query)
}

// CreateSpatialIndexes creates optimized spatial indexes
func (qo *QueryOptimizer) CreateSpatialIndexes(ctx context.Context) error {
	indexes := []string{
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS equipment_spatial_geom_idx 
		 ON equipment_spatial USING GIST (geom)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS equipment_spatial_equipment_id_idx 
		 ON equipment_spatial (equipment_id)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS equipment_spatial_building_id_idx 
		 ON equipment_spatial (building_id)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS equipment_spatial_confidence_idx 
		 ON equipment_spatial (confidence)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS scanned_regions_geom_idx 
		 ON scanned_regions USING GIST (boundary)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS scanned_regions_building_id_idx 
		 ON scanned_regions (building_id)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS point_clouds_geom_idx 
		 ON point_clouds USING GIST (points)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS spatial_anchors_geom_idx 
		 ON spatial_anchors USING GIST (geom)`,
		`CREATE INDEX CONCURRENTLY IF NOT EXISTS spatial_anchors_building_id_idx 
		 ON spatial_anchors (building_id)`,
	}

	for _, indexSQL := range indexes {
		if _, err := qo.db.ExecContext(ctx, indexSQL); err != nil {
			logger.Warn("Failed to create index: %v", err)
			// Continue with other indexes
		}
	}

	return nil
}

// AnalyzeTables runs ANALYZE on tables for query optimization
func (qo *QueryOptimizer) AnalyzeTables(ctx context.Context) error {
	tables := []string{
		"equipment_spatial",
		"scanned_regions",
		"point_clouds",
		"spatial_anchors",
		"confidence_records",
		"building_transforms",
	}

	for _, table := range tables {
		query := fmt.Sprintf("ANALYZE %s", table)
		if _, err := qo.db.ExecContext(ctx, query); err != nil {
			logger.Warn("Failed to analyze table %s: %v", table, err)
			// Continue with other tables
		}
	}

	return nil
}

// GetQueryPlan returns the query execution plan
func (qo *QueryOptimizer) GetQueryPlan(ctx context.Context, query string, params []interface{}) (string, error) {
	explainQuery := "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query

	var plan string
	err := qo.db.QueryRowContext(ctx, explainQuery, params...).Scan(&plan)
	if err != nil {
		return "", fmt.Errorf("failed to get query plan: %w", err)
	}

	return plan, nil
}

// OptimizeConnectionPool optimizes database connection pool settings
func (qo *QueryOptimizer) OptimizeConnectionPool(maxOpen, maxIdle int, maxLifetime time.Duration) {
	qo.db.SetMaxOpenConns(maxOpen)
	qo.db.SetMaxIdleConns(maxIdle)
	qo.db.SetConnMaxLifetime(maxLifetime)

	logger.Info("Database connection pool optimized: maxOpen=%d, maxIdle=%d, maxLifetime=%v",
		maxOpen, maxIdle, maxLifetime)
}
