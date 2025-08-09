package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/lib/pq"
)

type PerformanceReport struct {
	Timestamp       time.Time        `json:"timestamp"`
	DatabaseInfo    DatabaseInfo     `json:"database_info"`
	TableStats      []TableStat      `json:"table_stats"`
	IndexStats      []IndexStat      `json:"index_stats"`
	SlowQueries     []SlowQuery      `json:"slow_queries"`
	CacheStats      []CacheStat      `json:"cache_stats"`
	Recommendations []Recommendation `json:"recommendations"`
	Summary         SummaryReport    `json:"summary"`
}

type DatabaseInfo struct {
	Name        string `json:"name"`
	Size        string `json:"size"`
	Connections int    `json:"connections"`
	Version     string `json:"version"`
}

type TableStat struct {
	TableName     string  `json:"table_name"`
	Size          string  `json:"size"`
	RowCount      int64   `json:"row_count"`
	SeqScans      int64   `json:"seq_scans"`
	IndexScans    int64   `json:"index_scans"`
	CacheHitRatio float64 `json:"cache_hit_ratio"`
	DeadTuples    int64   `json:"dead_tuples"`
	LiveTuples    int64   `json:"live_tuples"`
}

type IndexStat struct {
	TableName     string `json:"table_name"`
	IndexName     string `json:"index_name"`
	IndexScans    int64  `json:"index_scans"`
	TuplesRead    int64  `json:"tuples_read"`
	TuplesFetched int64  `json:"tuples_fetched"`
	IndexSize     string `json:"index_size"`
	UsageCategory string `json:"usage_category"`
}

type SlowQuery struct {
	Query     string  `json:"query"`
	Calls     int64   `json:"calls"`
	MeanTime  float64 `json:"mean_time"`
	TotalTime float64 `json:"total_time"`
	Rows      int64   `json:"rows"`
}

type CacheStat struct {
	TableName     string  `json:"table_name"`
	HeapBlksRead  int64   `json:"heap_blks_read"`
	HeapBlksHit   int64   `json:"heap_blks_hit"`
	CacheHitRatio float64 `json:"cache_hit_ratio"`
}

type Recommendation struct {
	Type        string `json:"type"`
	Description string `json:"description"`
	Priority    string `json:"priority"`
	SQL         string `json:"sql"`
}

type SummaryReport struct {
	TotalTables       int     `json:"total_tables"`
	TotalIndexes      int     `json:"total_indexes"`
	UnusedIndexes     int     `json:"unused_indexes"`
	HighSeqScanTables int     `json:"high_seq_scan_tables"`
	AvgCacheHitRatio  float64 `json:"avg_cache_hit_ratio"`
	SlowQueriesCount  int     `json:"slow_queries_count"`
}

func main() {
	// Database connection parameters
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbUser := getEnv("DB_USER", "postgres")
	dbPassword := getEnv("DB_PASSWORD", "")
	dbName := getEnv("DB_NAME", "arxos")

	// Connect to database
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Test connection
	if err := db.Ping(); err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}

	fmt.Println("🔍 Starting Database Performance Analysis...")
	fmt.Println("=============================================")

	// Generate performance report
	report := generatePerformanceReport(db)

	// Save report to file
	saveReport(report)

	// Print summary
	printSummary(report)
}

func generatePerformanceReport(db *sql.DB) PerformanceReport {
	report := PerformanceReport{
		Timestamp: time.Now(),
	}

	// Get database info
	report.DatabaseInfo = getDatabaseInfo(db)

	// Get table statistics
	report.TableStats = getTableStats(db)

	// Get index statistics
	report.IndexStats = getIndexStats(db)

	// Get slow queries (if pg_stat_statements is available)
	report.SlowQueries = getSlowQueries(db)

	// Get cache statistics
	report.CacheStats = getCacheStats(db)

	// Generate recommendations
	report.Recommendations = generateRecommendations(report)

	// Generate summary
	report.Summary = generateSummary(report)

	return report
}

func getDatabaseInfo(db *sql.DB) DatabaseInfo {
	var info DatabaseInfo

	// Get database name and size
	query := `
		SELECT
			current_database() as name,
			pg_size_pretty(pg_database_size(current_database())) as size,
			(SELECT count(*) FROM pg_stat_activity) as connections,
			version() as version
	`

	err := db.QueryRow(query).Scan(&info.Name, &info.Size, &info.Connections, &info.Version)
	if err != nil {
		log.Printf("Error getting database info: %v", err)
	}

	return info
}

func getTableStats(db *sql.DB) []TableStat {
	var stats []TableStat

	query := `
		SELECT
			t.tablename,
			pg_size_pretty(pg_total_relation_size(t.schemaname||'.'||t.tablename)) as size,
			COALESCE(c.reltuples, 0) as row_count,
			COALESCE(s.seq_scan, 0) as seq_scans,
			COALESCE(s.idx_scan, 0) as index_scans,
			CASE
				WHEN (st.heap_blks_hit + st.heap_blks_read) = 0 THEN 0
				ELSE ROUND(100.0 * st.heap_blks_hit / (st.heap_blks_hit + st.heap_blks_read), 2)
			END as cache_hit_ratio,
			COALESCE(s.n_dead_tup, 0) as dead_tuples,
			COALESCE(s.n_live_tup, 0) as live_tuples
		FROM pg_tables t
		LEFT JOIN pg_class c ON c.relname = t.tablename
		LEFT JOIN pg_stat_user_tables s ON s.tablename = t.tablename
		LEFT JOIN pg_statio_user_tables st ON st.tablename = t.tablename
		WHERE t.schemaname = 'public'
		ORDER BY pg_total_relation_size(t.schemaname||'.'||t.tablename) DESC
	`

	rows, err := db.Query(query)
	if err != nil {
		log.Printf("Error getting table stats: %v", err)
		return stats
	}
	defer rows.Close()

	for rows.Next() {
		var stat TableStat
		err := rows.Scan(
			&stat.TableName,
			&stat.Size,
			&stat.RowCount,
			&stat.SeqScans,
			&stat.IndexScans,
			&stat.CacheHitRatio,
			&stat.DeadTuples,
			&stat.LiveTuples,
		)
		if err != nil {
			log.Printf("Error scanning table stat: %v", err)
			continue
		}
		stats = append(stats, stat)
	}

	return stats
}

func getIndexStats(db *sql.DB) []IndexStat {
	var stats []IndexStat

	query := `
		SELECT
			schemaname,
			tablename,
			indexname,
			idx_scan as index_scans,
			idx_tup_read as tuples_read,
			idx_tup_fetch as tuples_fetched,
			pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
			CASE
				WHEN idx_scan = 0 THEN 'UNUSED'
				WHEN idx_scan < 10 THEN 'RARELY_USED'
				WHEN idx_scan < 100 THEN 'OCCASIONALLY_USED'
				ELSE 'FREQUENTLY_USED'
			END as usage_category
		FROM pg_stat_user_indexes
		ORDER BY idx_scan DESC
	`

	rows, err := db.Query(query)
	if err != nil {
		log.Printf("Error getting index stats: %v", err)
		return stats
	}
	defer rows.Close()

	for rows.Next() {
		var stat IndexStat
		var schemaName string
		err := rows.Scan(
			&schemaName,
			&stat.TableName,
			&stat.IndexName,
			&stat.IndexScans,
			&stat.TuplesRead,
			&stat.TuplesFetched,
			&stat.IndexSize,
			&stat.UsageCategory,
		)
		if err != nil {
			log.Printf("Error scanning index stat: %v", err)
			continue
		}
		stats = append(stats, stat)
	}

	return stats
}

func getSlowQueries(db *sql.DB) []SlowQuery {
	var queries []SlowQuery

	// Check if pg_stat_statements extension is available
	var extensionExists bool
	err := db.QueryRow("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements')").Scan(&extensionExists)
	if err != nil || !extensionExists {
		log.Println("⚠️  pg_stat_statements extension not available. Slow query analysis skipped.")
		return queries
	}

	query := `
		SELECT
			query,
			calls,
			mean_time,
			total_time,
			rows
		FROM pg_stat_statements
		ORDER BY mean_time DESC
		LIMIT 20
	`

	rows, err := db.Query(query)
	if err != nil {
		log.Printf("Error getting slow queries: %v", err)
		return queries
	}
	defer rows.Close()

	for rows.Next() {
		var query SlowQuery
		err := rows.Scan(
			&query.Query,
			&query.Calls,
			&query.MeanTime,
			&query.TotalTime,
			&query.Rows,
		)
		if err != nil {
			log.Printf("Error scanning slow query: %v", err)
			continue
		}
		queries = append(queries, query)
	}

	return queries
}

func getCacheStats(db *sql.DB) []CacheStat {
	var stats []CacheStat

	query := `
		SELECT
			schemaname,
			tablename,
			heap_blks_read,
			heap_blks_hit,
			CASE
				WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
				ELSE ROUND(100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read), 2)
			END as cache_hit_ratio
		FROM pg_statio_user_tables
		ORDER BY cache_hit_ratio ASC
	`

	rows, err := db.Query(query)
	if err != nil {
		log.Printf("Error getting cache stats: %v", err)
		return stats
	}
	defer rows.Close()

	for rows.Next() {
		var stat CacheStat
		var schemaName string
		err := rows.Scan(
			&schemaName,
			&stat.TableName,
			&stat.HeapBlksRead,
			&stat.HeapBlksHit,
			&stat.CacheHitRatio,
		)
		if err != nil {
			log.Printf("Error scanning cache stat: %v", err)
			continue
		}
		stats = append(stats, stat)
	}

	return stats
}

func generateRecommendations(report PerformanceReport) []Recommendation {
	var recommendations []Recommendation

	// Analyze unused indexes
	unusedIndexes := 0
	for _, index := range report.IndexStats {
		if index.UsageCategory == "UNUSED" {
			unusedIndexes++
		}
	}

	if unusedIndexes > 0 {
		recommendations = append(recommendations, Recommendation{
			Type:        "INDEX_OPTIMIZATION",
			Description: fmt.Sprintf("Found %d unused indexes that can be removed to improve write performance", unusedIndexes),
			Priority:    "MEDIUM",
			SQL:         "-- Review and drop unused indexes: SELECT indexname FROM pg_stat_user_indexes WHERE idx_scan = 0;",
		})
	}

	// Analyze cache hit ratios
	lowCacheTables := 0
	for _, cache := range report.CacheStats {
		if cache.CacheHitRatio < 80.0 {
			lowCacheTables++
		}
	}

	if lowCacheTables > 0 {
		recommendations = append(recommendations, Recommendation{
			Type:        "CACHE_OPTIMIZATION",
			Description: fmt.Sprintf("Found %d tables with low cache hit ratio (< 80%%)", lowCacheTables),
			Priority:    "HIGH",
			SQL:         "-- Consider increasing shared_buffers or optimizing queries",
		})
	}

	// Analyze sequential scans
	highSeqScanTables := 0
	for _, table := range report.TableStats {
		if table.SeqScans > table.IndexScans {
			highSeqScanTables++
		}
	}

	if highSeqScanTables > 0 {
		recommendations = append(recommendations, Recommendation{
			Type:        "QUERY_OPTIMIZATION",
			Description: fmt.Sprintf("Found %d tables with high sequential scan ratio", highSeqScanTables),
			Priority:    "HIGH",
			SQL:         "-- Add indexes on frequently queried columns",
		})
	}

	// Specific recommendations for Arxos tables
	recommendations = append(recommendations, Recommendation{
		Type:        "ARXOS_SPECIFIC",
		Description: "Ensure spatial indexes exist for PostGIS geometry columns",
		Priority:    "HIGH",
		SQL:         "CREATE INDEX IF NOT EXISTS idx_walls_geom ON walls USING GIST (geom);",
	})

	recommendations = append(recommendations, Recommendation{
		Type:        "ARXOS_SPECIFIC",
		Description: "Add composite indexes for common building asset queries",
		Priority:    "MEDIUM",
		SQL:         "CREATE INDEX IF NOT EXISTS idx_building_assets_building_system ON building_assets(building_id, system);",
	})

	return recommendations
}

func generateSummary(report PerformanceReport) SummaryReport {
	summary := SummaryReport{
		TotalTables:      len(report.TableStats),
		TotalIndexes:     len(report.IndexStats),
		SlowQueriesCount: len(report.SlowQueries),
	}

	// Count unused indexes
	for _, index := range report.IndexStats {
		if index.UsageCategory == "UNUSED" {
			summary.UnusedIndexes++
		}
	}

	// Count tables with high sequential scans
	for _, table := range report.TableStats {
		if table.SeqScans > table.IndexScans {
			summary.HighSeqScanTables++
		}
	}

	// Calculate average cache hit ratio
	totalCacheRatio := 0.0
	cacheCount := 0
	for _, cache := range report.CacheStats {
		totalCacheRatio += cache.CacheHitRatio
		cacheCount++
	}
	if cacheCount > 0 {
		summary.AvgCacheHitRatio = totalCacheRatio / float64(cacheCount)
	}

	return summary
}

func saveReport(report PerformanceReport) {
	// Save as JSON
	jsonData, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		log.Printf("Error marshaling report: %v", err)
		return
	}

	filename := fmt.Sprintf("database_performance_report_%s.json", time.Now().Format("2006-01-02_15-04-05"))
	err = os.WriteFile(filename, jsonData, 0644)
	if err != nil {
		log.Printf("Error writing report file: %v", err)
		return
	}

	fmt.Printf("📄 Performance report saved to: %s\n", filename)
}

func printSummary(report PerformanceReport) {
	fmt.Println("\n📊 PERFORMANCE ANALYSIS SUMMARY")
	fmt.Println("================================")
	fmt.Printf("Database: %s (%s)\n", report.DatabaseInfo.Name, report.DatabaseInfo.Size)
	fmt.Printf("Total Tables: %d\n", report.Summary.TotalTables)
	fmt.Printf("Total Indexes: %d\n", report.Summary.TotalIndexes)
	fmt.Printf("Unused Indexes: %d\n", report.Summary.UnusedIndexes)
	fmt.Printf("Tables with High Seq Scans: %d\n", report.Summary.HighSeqScanTables)
	fmt.Printf("Average Cache Hit Ratio: %.2f%%\n", report.Summary.AvgCacheHitRatio)
	fmt.Printf("Slow Queries Detected: %d\n", report.Summary.SlowQueriesCount)

	fmt.Println("\n🔧 RECOMMENDATIONS")
	fmt.Println("==================")
	for i, rec := range report.Recommendations {
		fmt.Printf("%d. [%s] %s\n", i+1, rec.Priority, rec.Description)
	}

	fmt.Println("\n✅ Analysis complete!")
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
