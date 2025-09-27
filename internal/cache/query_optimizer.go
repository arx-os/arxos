package cache

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// QueryType defines different types of queries
type QueryType string

const (
	QueryTypeSpatial   QueryType = "spatial"
	QueryTypeEquipment QueryType = "equipment"
	QueryTypeBuilding  QueryType = "building"
	QueryTypeAnalytics QueryType = "analytics"
	QueryTypeWorkflow  QueryType = "workflow"
	QueryTypeIT        QueryType = "it"
	QueryTypeFacility  QueryType = "facility"
)

// QueryComplexity defines query complexity levels
type QueryComplexity string

const (
	ComplexitySimple   QueryComplexity = "simple"
	ComplexityMedium   QueryComplexity = "medium"
	ComplexityComplex  QueryComplexity = "complex"
	ComplexityCritical QueryComplexity = "critical"
)

// QueryProfile represents a query execution profile
type QueryProfile struct {
	QueryID       string          `json:"query_id"`
	QueryType     QueryType       `json:"query_type"`
	Complexity    QueryComplexity `json:"complexity"`
	SQL           string          `json:"sql"`
	Parameters    []interface{}   `json:"parameters"`
	ExecutionTime time.Duration   `json:"execution_time"`
	RowsReturned  int64           `json:"rows_returned"`
	CacheHit      bool            `json:"cache_hit"`
	Optimized     bool            `json:"optimized"`
	IndexUsed     []string        `json:"index_used"`
	Cost          float64         `json:"cost"`
	CreatedAt     time.Time       `json:"created_at"`
}

// QueryOptimizer provides intelligent query optimization
type QueryOptimizer struct {
	cache             *AdvancedCache
	profiles          map[string]*QueryProfile
	indexHints        map[string][]string
	optimizationRules []OptimizationRule
	mu                sync.RWMutex
}

// OptimizationRule defines a query optimization rule
type OptimizationRule struct {
	Name        string                            `json:"name"`
	Description string                            `json:"description"`
	Condition   func(*QueryProfile) bool          `json:"-"`
	Action      func(*QueryProfile) *QueryProfile `json:"-"`
	Priority    int                               `json:"priority"`
	Enabled     bool                              `json:"enabled"`
}

// SpatialIndexHint provides hints for spatial queries
type SpatialIndexHint struct {
	TableName      string  `json:"table_name"`
	GeometryColumn string  `json:"geometry_column"`
	IndexName      string  `json:"index_name"`
	IndexType      string  `json:"index_type"` // GIST, SPGIST, etc.
	Bounds         *Bounds `json:"bounds,omitempty"`
}

// Bounds represents spatial bounds
type Bounds struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
}

// NewQueryOptimizer creates a new query optimizer
func NewQueryOptimizer(cache *AdvancedCache) *QueryOptimizer {
	optimizer := &QueryOptimizer{
		cache:             cache,
		profiles:          make(map[string]*QueryProfile),
		indexHints:        make(map[string][]string),
		optimizationRules: make([]OptimizationRule, 0),
	}

	// Initialize optimization rules
	optimizer.initializeOptimizationRules()

	return optimizer
}

// OptimizeQuery optimizes a query before execution
func (qo *QueryOptimizer) OptimizeQuery(ctx context.Context, queryType QueryType, sql string, parameters []interface{}) (*QueryProfile, error) {
	queryID := qo.generateQueryID(sql, parameters)

	// Check cache first
	if cached, found := qo.cache.Get(ctx, queryID); found {
		if profile, ok := cached.(*QueryProfile); ok {
			profile.CacheHit = true
			return profile, nil
		}
	}

	// Create initial profile
	profile := &QueryProfile{
		QueryID:    queryID,
		QueryType:  queryType,
		SQL:        sql,
		Parameters: parameters,
		CreatedAt:  time.Now(),
	}

	// Analyze query complexity
	profile.Complexity = qo.analyzeComplexity(profile)

	// Apply optimization rules
	optimizedProfile := qo.applyOptimizationRules(profile)

	// Cache the optimized query
	cacheOptions := &CacheOptions{
		TTL:  time.Hour, // Cache optimized queries for 1 hour
		Tags: []string{"query", string(queryType), "optimized"},
	}
	qo.cache.Set(ctx, queryID, optimizedProfile, cacheOptions)

	qo.mu.Lock()
	qo.profiles[queryID] = optimizedProfile
	qo.mu.Unlock()

	return optimizedProfile, nil
}

// ExecuteQuery executes a query with optimization
func (qo *QueryOptimizer) ExecuteQuery(ctx context.Context, db *sql.DB, queryType QueryType, sql string, parameters []interface{}) (*QueryProfile, error) {
	// Optimize the query
	profile, err := qo.OptimizeQuery(ctx, queryType, sql, parameters)
	if err != nil {
		return nil, fmt.Errorf("failed to optimize query: %w", err)
	}

	// Execute the optimized query
	start := time.Now()
	rows, err := db.QueryContext(ctx, profile.SQL, profile.Parameters...)
	profile.ExecutionTime = time.Since(start)

	if err != nil {
		return profile, fmt.Errorf("query execution failed: %w", err)
	}
	defer rows.Close()

	// Count rows
	var rowCount int64
	for rows.Next() {
		rowCount++
	}
	profile.RowsReturned = rowCount

	// Update profile with execution results
	qo.mu.Lock()
	qo.profiles[profile.QueryID] = profile
	qo.mu.Unlock()

	logger.Debug("Query executed: %s (time: %v, rows: %d)", profile.QueryID, profile.ExecutionTime, profile.RowsReturned)

	return profile, nil
}

// GetQueryStats returns query performance statistics
func (qo *QueryOptimizer) GetQueryStats(queryType QueryType) map[string]interface{} {
	qo.mu.RLock()
	defer qo.mu.RUnlock()

	stats := map[string]interface{}{
		"total_queries":      0,
		"avg_execution_time": 0,
		"total_rows":         0,
		"cache_hit_rate":     0,
		"optimization_rate":  0,
	}

	var totalTime time.Duration
	var totalRows int64
	var cacheHits int64
	var optimized int64
	var count int64

	for _, profile := range qo.profiles {
		if queryType == "" || profile.QueryType == queryType {
			count++
			totalTime += profile.ExecutionTime
			totalRows += profile.RowsReturned

			if profile.CacheHit {
				cacheHits++
			}
			if profile.Optimized {
				optimized++
			}
		}
	}

	if count > 0 {
		stats["total_queries"] = count
		stats["avg_execution_time"] = totalTime / time.Duration(count)
		stats["total_rows"] = totalRows
		stats["cache_hit_rate"] = float64(cacheHits) / float64(count)
		stats["optimization_rate"] = float64(optimized) / float64(count)
	}

	return stats
}

// Helper methods

func (qo *QueryOptimizer) generateQueryID(sql string, parameters []interface{}) string {
	// Create a hash of the SQL and parameters
	hash := fmt.Sprintf("%s:%v", sql, parameters)
	return fmt.Sprintf("query_%x", hash)
}

func (qo *QueryOptimizer) analyzeComplexity(profile *QueryProfile) QueryComplexity {
	sql := strings.ToLower(profile.SQL)

	// Count complexity indicators
	joins := strings.Count(sql, "join")
	subqueries := strings.Count(sql, "select") - 1
	spatialOps := strings.Count(sql, "st_")
	aggregates := strings.Count(sql, "group by") + strings.Count(sql, "order by")

	complexityScore := joins*2 + subqueries*3 + spatialOps*2 + aggregates

	switch {
	case complexityScore <= 2:
		return ComplexitySimple
	case complexityScore <= 5:
		return ComplexityMedium
	case complexityScore <= 10:
		return ComplexityComplex
	default:
		return ComplexityCritical
	}
}

func (qo *QueryOptimizer) applyOptimizationRules(profile *QueryProfile) *QueryProfile {
	optimized := *profile

	for _, rule := range qo.optimizationRules {
		if !rule.Enabled {
			continue
		}

		if rule.Condition(&optimized) {
			optimized = *rule.Action(&optimized)
			optimized.Optimized = true
			logger.Debug("Applied optimization rule: %s", rule.Name)
		}
	}

	return &optimized
}

func (qo *QueryOptimizer) initializeOptimizationRules() {
	qo.optimizationRules = []OptimizationRule{
		{
			Name:        "spatial_index_hint",
			Description: "Add spatial index hints for PostGIS queries",
			Condition: func(p *QueryProfile) bool {
				return p.QueryType == QueryTypeSpatial && strings.Contains(strings.ToLower(p.SQL), "st_")
			},
			Action: func(p *QueryProfile) *QueryProfile {
				optimized := *p
				optimized.SQL = qo.addSpatialIndexHints(optimized.SQL)
				return &optimized
			},
			Priority: 1,
			Enabled:  true,
		},
		{
			Name:        "limit_optimization",
			Description: "Add LIMIT clause for large result sets",
			Condition: func(p *QueryProfile) bool {
				return !strings.Contains(strings.ToLower(p.SQL), "limit") &&
					!strings.Contains(strings.ToLower(p.SQL), "count(")
			},
			Action: func(p *QueryProfile) *QueryProfile {
				optimized := *p
				optimized.SQL = optimized.SQL + " LIMIT 1000"
				return &optimized
			},
			Priority: 2,
			Enabled:  true,
		},
		{
			Name:        "parameter_binding",
			Description: "Optimize parameter binding for prepared statements",
			Condition: func(p *QueryProfile) bool {
				return len(p.Parameters) > 0
			},
			Action: func(p *QueryProfile) *QueryProfile {
				optimized := *p
				// In a real implementation, this would optimize parameter binding
				return &optimized
			},
			Priority: 3,
			Enabled:  true,
		},
	}
}

func (qo *QueryOptimizer) addSpatialIndexHints(sql string) string {
	// This is a simplified implementation
	// In a real system, this would analyze the SQL and add appropriate hints
	return sql
}

// AddOptimizationRule adds a custom optimization rule
func (qo *QueryOptimizer) AddOptimizationRule(rule OptimizationRule) {
	qo.mu.Lock()
	defer qo.mu.Unlock()

	qo.optimizationRules = append(qo.optimizationRules, rule)
}

// EnableOptimizationRule enables/disables an optimization rule
func (qo *QueryOptimizer) EnableOptimizationRule(name string, enabled bool) {
	qo.mu.Lock()
	defer qo.mu.Unlock()

	for i := range qo.optimizationRules {
		if qo.optimizationRules[i].Name == name {
			qo.optimizationRules[i].Enabled = enabled
			break
		}
	}
}
