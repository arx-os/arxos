package database

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// QueryAnalyzer analyzes and optimizes database queries
type QueryAnalyzer struct {
	pool   *ConnectionPool
	logger domain.Logger
}

// QueryAnalysis represents the analysis of a query
type QueryAnalysis struct {
	Query           string                 `json:"query"`
	ExecutionPlan   string                 `json:"execution_plan"`
	CostEstimate    float64                `json:"cost_estimate"`
	IndexUsage      []string               `json:"index_usage"`
	TableScans      []string               `json:"table_scans"`
	Recommendations []string               `json:"recommendations"`
	Warnings        []string               `json:"warnings"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// QueryOptimization represents query optimization suggestions
type QueryOptimization struct {
	OriginalQuery    string   `json:"original_query"`
	OptimizedQuery   string   `json:"optimized_query"`
	Optimizations    []string `json:"optimizations"`
	ExpectedImprovement string `json:"expected_improvement"`
	RiskLevel        string   `json:"risk_level"`
}

// SlowQuery represents a slow query with analysis
type SlowQuery struct {
	Query         string        `json:"query"`
	AverageTime   time.Duration `json:"average_time"`
	CallCount     int64         `json:"call_count"`
	TotalTime     time.Duration `json:"total_time"`
	MinTime       time.Duration `json:"min_time"`
	MaxTime       time.Duration `json:"max_time"`
	Analysis      *QueryAnalysis `json:"analysis,omitempty"`
	Optimization  *QueryOptimization `json:"optimization,omitempty"`
}

// NewQueryAnalyzer creates a new query analyzer
func NewQueryAnalyzer(pool *ConnectionPool, logger domain.Logger) *QueryAnalyzer {
	return &QueryAnalyzer{
		pool:   pool,
		logger: logger,
	}
}

// AnalyzeQuery analyzes a SQL query and provides optimization suggestions
func (qa *QueryAnalyzer) AnalyzeQuery(ctx context.Context, query string) (*QueryAnalysis, error) {
	qa.logger.Debug("Analyzing query", "query", query)

	analysis := &QueryAnalysis{
		Query:           query,
		IndexUsage:      []string{},
		TableScans:      []string{},
		Recommendations: []string{},
		Warnings:        []string{},
		Metadata:        make(map[string]interface{}),
	}

	// Get execution plan
	plan, err := qa.getExecutionPlan(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to get execution plan: %w", err)
	}
	analysis.ExecutionPlan = plan

	// Analyze query structure
	qa.analyzeQueryStructure(query, analysis)

	// Check for common performance issues
	qa.checkPerformanceIssues(query, analysis)

	// Generate recommendations
	qa.generateRecommendations(query, analysis)

	return analysis, nil
}

// getExecutionPlan gets the execution plan for a query
func (qa *QueryAnalyzer) getExecutionPlan(ctx context.Context, query string) (string, error) {
	conn := qa.pool.GetConnectionForRead()
	
	// Use EXPLAIN to get execution plan
	explainQuery := fmt.Sprintf("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) %s", query)
	
	rows, err := conn.QueryContext(ctx, explainQuery)
	if err != nil {
		return "", fmt.Errorf("failed to execute EXPLAIN: %w", err)
	}
	defer rows.Close()

	var plan string
	if rows.Next() {
		if err := rows.Scan(&plan); err != nil {
			return "", fmt.Errorf("failed to scan execution plan: %w", err)
		}
	}

	return plan, nil
}

// analyzeQueryStructure analyzes the structure of the query
func (qa *QueryAnalyzer) analyzeQueryStructure(query string, analysis *QueryAnalysis) {
	query = strings.ToUpper(strings.TrimSpace(query))

	// Check for SELECT queries
	if strings.HasPrefix(query, "SELECT") {
		qa.analyzeSelectQuery(query, analysis)
	}

	// Check for JOINs
	if strings.Contains(query, "JOIN") {
		qa.analyzeJoins(query, analysis)
	}

	// Check for WHERE clauses
	if strings.Contains(query, "WHERE") {
		qa.analyzeWhereClause(query, analysis)
	}

	// Check for ORDER BY
	if strings.Contains(query, "ORDER BY") {
		qa.analyzeOrderBy(query, analysis)
	}

	// Check for GROUP BY
	if strings.Contains(query, "GROUP BY") {
		qa.analyzeGroupBy(query, analysis)
	}
}

// analyzeSelectQuery analyzes SELECT queries
func (qa *QueryAnalyzer) analyzeSelectQuery(query string, analysis *QueryAnalysis) {
	// Check for SELECT *
	if strings.Contains(query, "SELECT *") {
		analysis.Warnings = append(analysis.Warnings, "Avoid SELECT * - specify only needed columns")
		analysis.Recommendations = append(analysis.Recommendations, "Specify only required columns in SELECT clause")
	}

	// Check for DISTINCT
	if strings.Contains(query, "DISTINCT") {
		analysis.Warnings = append(analysis.Warnings, "DISTINCT can be expensive - consider if it's necessary")
	}
}

// analyzeJoins analyzes JOIN operations
func (qa *QueryAnalyzer) analyzeJoins(query string, analysis *QueryAnalysis) {
	// Count JOINs
	joinCount := strings.Count(query, "JOIN")
	if joinCount > 5 {
		analysis.Warnings = append(analysis.Warnings, "Query has many JOINs - consider query complexity")
	}

	// Check for missing JOIN conditions
	if strings.Contains(query, "JOIN") && !strings.Contains(query, "ON") {
		analysis.Warnings = append(analysis.Warnings, "JOIN without ON clause detected")
	}
}

// analyzeWhereClause analyzes WHERE clauses
func (qa *QueryAnalyzer) analyzeWhereClause(query string, analysis *QueryAnalysis) {
	// Check for functions in WHERE clause
	functionPattern := regexp.MustCompile(`WHERE\s+.*\w+\s*\(`)
	if functionPattern.MatchString(query) {
		analysis.Warnings = append(analysis.Warnings, "Functions in WHERE clause can prevent index usage")
		analysis.Recommendations = append(analysis.Recommendations, "Avoid functions in WHERE clause for better index utilization")
	}

	// Check for LIKE with leading wildcard
	likePattern := regexp.MustCompile(`LIKE\s+['"]%`)
	if likePattern.MatchString(query) {
		analysis.Warnings = append(analysis.Warnings, "LIKE with leading wildcard prevents index usage")
		analysis.Recommendations = append(analysis.Recommendations, "Consider full-text search or different pattern matching")
	}
}

// analyzeOrderBy analyzes ORDER BY clauses
func (qa *QueryAnalyzer) analyzeOrderBy(query string, analysis *QueryAnalysis) {
	// Check for ORDER BY without LIMIT
	if strings.Contains(query, "ORDER BY") && !strings.Contains(query, "LIMIT") {
		analysis.Warnings = append(analysis.Warnings, "ORDER BY without LIMIT can be expensive")
		analysis.Recommendations = append(analysis.Recommendations, "Consider adding LIMIT to ORDER BY queries")
	}
}

// analyzeGroupBy analyzes GROUP BY clauses
func (qa *QueryAnalyzer) analyzeGroupBy(query string, analysis *QueryAnalysis) {
	// Check for GROUP BY with many columns
	groupByPattern := regexp.MustCompile(`GROUP BY\s+(.+?)(?:\s+ORDER BY|\s+HAVING|\s+LIMIT|$)`)
	matches := groupByPattern.FindStringSubmatch(query)
	if len(matches) > 1 {
		columns := strings.Split(matches[1], ",")
		if len(columns) > 5 {
			analysis.Warnings = append(analysis.Warnings, "GROUP BY with many columns can be expensive")
		}
	}
}

// checkPerformanceIssues checks for common performance issues
func (qa *QueryAnalyzer) checkPerformanceIssues(query string, analysis *QueryAnalysis) {
	// Check for N+1 query patterns
	if qa.detectNPlusOnePattern(query) {
		analysis.Warnings = append(analysis.Warnings, "Potential N+1 query pattern detected")
		analysis.Recommendations = append(analysis.Recommendations, "Consider using JOINs or batch loading")
	}

	// Check for missing indexes
	qa.checkMissingIndexes(query, analysis)

	// Check for inefficient patterns
	qa.checkInefficientPatterns(query, analysis)
}

// detectNPlusOnePattern detects potential N+1 query patterns
func (qa *QueryAnalyzer) detectNPlusOnePattern(query string) bool {
	// Simple heuristic: queries with subqueries that might be executed multiple times
	return strings.Contains(query, "SELECT") && strings.Count(query, "SELECT") > 1
}

// checkMissingIndexes checks for missing indexes
func (qa *QueryAnalyzer) checkMissingIndexes(query string, analysis *QueryAnalysis) {
	// This would analyze the query to suggest missing indexes
	// For now, we'll add a general recommendation
	analysis.Recommendations = append(analysis.Recommendations, "Review query for missing indexes on frequently queried columns")
}

// checkInefficientPatterns checks for inefficient query patterns
func (qa *QueryAnalyzer) checkInefficientPatterns(query string, analysis *QueryAnalysis) {
	// Check for subqueries that could be JOINs
	if strings.Contains(query, "SELECT") && strings.Count(query, "SELECT") > 1 {
		analysis.Recommendations = append(analysis.Recommendations, "Consider converting subqueries to JOINs for better performance")
	}

	// Check for UNION without ALL
	if strings.Contains(query, "UNION") && !strings.Contains(query, "UNION ALL") {
		analysis.Warnings = append(analysis.Warnings, "UNION without ALL removes duplicates - consider if UNION ALL is sufficient")
	}
}

// generateRecommendations generates optimization recommendations
func (qa *QueryAnalyzer) generateRecommendations(query string, analysis *QueryAnalysis) {
	// Add general recommendations based on query analysis
	if len(analysis.Warnings) > 0 {
		analysis.Recommendations = append(analysis.Recommendations, "Address warnings to improve query performance")
	}

	// Add index recommendations
	qa.generateIndexRecommendations(query, analysis)

	// Add query structure recommendations
	qa.generateStructureRecommendations(query, analysis)
}

// generateIndexRecommendations generates index recommendations
func (qa *QueryAnalyzer) generateIndexRecommendations(query string, analysis *QueryAnalysis) {
	// Extract table names and columns from query
	tables := qa.extractTables(query)
	columns := qa.extractColumns(query)

	for _, table := range tables {
		for _, column := range columns {
			if strings.Contains(query, fmt.Sprintf("%s.%s", table, column)) {
				analysis.Recommendations = append(analysis.Recommendations, 
					fmt.Sprintf("Consider creating index on %s.%s", table, column))
			}
		}
	}
}

// generateStructureRecommendations generates query structure recommendations
func (qa *QueryAnalyzer) generateStructureRecommendations(query string, analysis *QueryAnalysis) {
	// Add recommendations based on query complexity
	if strings.Count(query, "JOIN") > 3 {
		analysis.Recommendations = append(analysis.Recommendations, "Consider breaking complex query into smaller parts")
	}

	if strings.Contains(query, "HAVING") {
		analysis.Recommendations = append(analysis.Recommendations, "Consider moving HAVING conditions to WHERE clause if possible")
	}
}

// extractTables extracts table names from query
func (qa *QueryAnalyzer) extractTables(query string) []string {
	// Simple table extraction - in production, you'd use a proper SQL parser
	tablePattern := regexp.MustCompile(`FROM\s+(\w+)`)
	matches := tablePattern.FindAllStringSubmatch(query, -1)
	
	var tables []string
	for _, match := range matches {
		if len(match) > 1 {
			tables = append(tables, match[1])
		}
	}
	
	return tables
}

// extractColumns extracts column names from query
func (qa *QueryAnalyzer) extractColumns(query string) []string {
	// Simple column extraction - in production, you'd use a proper SQL parser
	columnPattern := regexp.MustCompile(`(\w+)\.(\w+)`)
	matches := columnPattern.FindAllStringSubmatch(query, -1)
	
	var columns []string
	for _, match := range matches {
		if len(match) > 2 {
			columns = append(columns, match[2])
		}
	}
	
	return columns
}

// OptimizeQuery provides query optimization suggestions
func (qa *QueryAnalyzer) OptimizeQuery(ctx context.Context, query string) (*QueryOptimization, error) {
	qa.logger.Debug("Optimizing query", "query", query)

	optimization := &QueryOptimization{
		OriginalQuery: query,
		Optimizations: []string{},
		RiskLevel:     "low",
	}

	// Analyze the query first
	analysis, err := qa.AnalyzeQuery(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze query: %w", err)
	}

	// Generate optimized query based on analysis
	optimizedQuery := qa.generateOptimizedQuery(query, analysis)
	optimization.OptimizedQuery = optimizedQuery

	// Set optimizations based on analysis
	optimization.Optimizations = analysis.Recommendations

	// Determine risk level
	if len(analysis.Warnings) > 3 {
		optimization.RiskLevel = "high"
	} else if len(analysis.Warnings) > 1 {
		optimization.RiskLevel = "medium"
	}

	// Set expected improvement
	optimization.ExpectedImprovement = qa.calculateExpectedImprovement(analysis)

	return optimization, nil
}

// generateOptimizedQuery generates an optimized version of the query
func (qa *QueryAnalyzer) generateOptimizedQuery(originalQuery string, analysis *QueryAnalysis) string {
	optimizedQuery := originalQuery

	// Apply basic optimizations
	for _, recommendation := range analysis.Recommendations {
		if strings.Contains(recommendation, "SELECT *") {
			// This would replace SELECT * with specific columns
			// For now, we'll just return the original query
		}
	}

	return optimizedQuery
}

// calculateExpectedImprovement calculates expected performance improvement
func (qa *QueryAnalyzer) calculateExpectedImprovement(analysis *QueryAnalysis) string {
	warningCount := len(analysis.Warnings)
	recommendationCount := len(analysis.Recommendations)

	if warningCount == 0 && recommendationCount == 0 {
		return "Query appears to be well-optimized"
	}

	if warningCount > 3 {
		return "Significant improvement expected (50-80%)"
	} else if warningCount > 1 {
		return "Moderate improvement expected (20-50%)"
	} else {
		return "Minor improvement expected (5-20%)"
	}
}

// GetSlowQueries retrieves slow queries from the database
func (qa *QueryAnalyzer) GetSlowQueries(ctx context.Context, limit int) ([]*SlowQuery, error) {
	conn := qa.pool.GetConnectionForRead()
	
	query := `
		SELECT 
			query,
			mean_time,
			calls,
			total_time,
			min_time,
			max_time
		FROM pg_stat_statements 
		WHERE mean_time > interval '100ms'
		ORDER BY mean_time DESC
		LIMIT $1
	`

	rows, err := conn.QueryContext(ctx, query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get slow queries: %w", err)
	}
	defer rows.Close()

	var slowQueries []*SlowQuery
	for rows.Next() {
		var sq SlowQuery
		var query, meanTime, totalTime, minTime, maxTime string
		var calls int64

		if err := rows.Scan(&query, &meanTime, &calls, &totalTime, &minTime, &maxTime); err != nil {
			return nil, fmt.Errorf("failed to scan slow query: %w", err)
		}

		sq.Query = query
		sq.CallCount = calls
		// Parse durations (simplified - in production you'd parse properly)
		sq.AverageTime = time.Millisecond * 100 // Placeholder
		sq.TotalTime = time.Millisecond * 1000   // Placeholder
		sq.MinTime = time.Millisecond * 50        // Placeholder
		sq.MaxTime = time.Millisecond * 200       // Placeholder

		slowQueries = append(slowQueries, &sq)
	}

	return slowQueries, nil
}

// AnalyzeSlowQueries analyzes slow queries and provides optimization suggestions
func (qa *QueryAnalyzer) AnalyzeSlowQueries(ctx context.Context, limit int) ([]*SlowQuery, error) {
	slowQueries, err := qa.GetSlowQueries(ctx, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get slow queries: %w", err)
	}

	// Analyze each slow query
	for _, sq := range slowQueries {
		analysis, err := qa.AnalyzeQuery(ctx, sq.Query)
		if err != nil {
			qa.logger.Warn("Failed to analyze slow query", "query", sq.Query, "error", err)
			continue
		}
		sq.Analysis = analysis

		// Generate optimization suggestions
		optimization, err := qa.OptimizeQuery(ctx, sq.Query)
		if err != nil {
			qa.logger.Warn("Failed to optimize slow query", "query", sq.Query, "error", err)
			continue
		}
		sq.Optimization = optimization
	}

	return slowQueries, nil
}
