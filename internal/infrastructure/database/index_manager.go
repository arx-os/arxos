package database

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// IndexManager manages database indexes for optimal performance
type IndexManager struct {
	pool   *ConnectionPool
	logger domain.Logger
}

// IndexDefinition represents a database index
type IndexDefinition struct {
	Name       string                 `json:"name"`
	Table      string                 `json:"table"`
	Columns    []string               `json:"columns"`
	Unique     bool                   `json:"unique"`
	Partial    string                 `json:"partial,omitempty"`
	Concurrent bool                   `json:"concurrent"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// IndexStats represents index usage statistics
type IndexStats struct {
	IndexName          string    `json:"index_name"`
	TableName          string    `json:"table_name"`
	IndexSize          int64     `json:"index_size"`
	IndexScans         int64     `json:"index_scans"`
	IndexTuples        int64     `json:"index_tuples"`
	IndexTuplesRead    int64     `json:"index_tuples_read"`
	IndexTuplesFetched int64     `json:"index_tuples_fetched"`
	LastUsed           time.Time `json:"last_used"`
}

// NewIndexManager creates a new index manager
func NewIndexManager(pool *ConnectionPool, logger domain.Logger) *IndexManager {
	return &IndexManager{
		pool:   pool,
		logger: logger,
	}
}

// CreateIndex creates a database index
func (im *IndexManager) CreateIndex(ctx context.Context, index *IndexDefinition) error {
	conn := im.pool.GetConnectionForWrite()

	query := im.buildCreateIndexQuery(index)

	im.logger.Info("Creating index", "name", index.Name, "table", index.Table, "columns", index.Columns)

	if _, err := conn.ExecContext(ctx, query); err != nil {
		return fmt.Errorf("failed to create index %s: %w", index.Name, err)
	}

	im.logger.Info("Index created successfully", "name", index.Name)
	return nil
}

// DropIndex drops a database index
func (im *IndexManager) DropIndex(ctx context.Context, indexName string) error {
	conn := im.pool.GetConnectionForWrite()

	query := fmt.Sprintf("DROP INDEX IF EXISTS %s", indexName)

	im.logger.Info("Dropping index", "name", indexName)

	if _, err := conn.ExecContext(ctx, query); err != nil {
		return fmt.Errorf("failed to drop index %s: %w", indexName, err)
	}

	im.logger.Info("Index dropped successfully", "name", indexName)
	return nil
}

// GetIndexStats returns statistics for all indexes
func (im *IndexManager) GetIndexStats(ctx context.Context) ([]*IndexStats, error) {
	conn := im.pool.GetConnectionForRead()

	query := `
		SELECT 
			schemaname,
			tablename,
			indexname,
			idx_tup_read,
			idx_tup_fetch,
			idx_scan,
			pg_size_pretty(pg_relation_size(indexrelid)) as index_size
		FROM pg_stat_user_indexes 
		ORDER BY idx_scan DESC
	`

	rows, err := conn.QueryxContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to get index stats: %w", err)
	}
	defer rows.Close()

	var stats []*IndexStats
	for rows.Next() {
		var stat IndexStats
		var schemaName, tableName, indexName string
		var idxTupRead, idxTupFetch, idxScan int64
		var indexSize string

		if err := rows.Scan(&schemaName, &tableName, &indexName, &idxTupRead, &idxTupFetch, &idxScan, &indexSize); err != nil {
			return nil, fmt.Errorf("failed to scan index stats: %w", err)
		}

		stat.IndexName = indexName
		stat.TableName = fmt.Sprintf("%s.%s", schemaName, tableName)
		stat.IndexScans = idxScan
		stat.IndexTuplesRead = idxTupRead
		stat.IndexTuplesFetched = idxTupFetch
		stat.LastUsed = time.Now() // This would need to be tracked separately

		stats = append(stats, &stat)
	}

	return stats, nil
}

// AnalyzeTable performs table analysis for query optimization
func (im *IndexManager) AnalyzeTable(ctx context.Context, tableName string) error {
	conn := im.pool.GetConnectionForWrite()

	query := fmt.Sprintf("ANALYZE %s", tableName)

	im.logger.Info("Analyzing table", "table", tableName)

	if _, err := conn.ExecContext(ctx, query); err != nil {
		return fmt.Errorf("failed to analyze table %s: %w", tableName, err)
	}

	im.logger.Info("Table analysis completed", "table", tableName)
	return nil
}

// VacuumTable performs table vacuuming for maintenance
func (im *IndexManager) VacuumTable(ctx context.Context, tableName string, full bool) error {
	conn := im.pool.GetConnectionForWrite()

	var query string
	if full {
		query = fmt.Sprintf("VACUUM FULL %s", tableName)
	} else {
		query = fmt.Sprintf("VACUUM %s", tableName)
	}

	im.logger.Info("Vacuuming table", "table", tableName, "full", full)

	if _, err := conn.ExecContext(ctx, query); err != nil {
		return fmt.Errorf("failed to vacuum table %s: %w", tableName, err)
	}

	im.logger.Info("Table vacuum completed", "table", tableName)
	return nil
}

// GetUnusedIndexes returns indexes that are not being used
func (im *IndexManager) GetUnusedIndexes(ctx context.Context) ([]string, error) {
	conn := im.pool.GetConnectionForRead()

	query := `
		SELECT indexname
		FROM pg_stat_user_indexes 
		WHERE idx_scan = 0 
		AND indexname NOT LIKE '%_pkey'
		ORDER BY pg_relation_size(indexrelid) DESC
	`

	rows, err := conn.QueryxContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to get unused indexes: %w", err)
	}
	defer rows.Close()

	var unusedIndexes []string
	for rows.Next() {
		var indexName string
		if err := rows.Scan(&indexName); err != nil {
			return nil, fmt.Errorf("failed to scan unused index: %w", err)
		}
		unusedIndexes = append(unusedIndexes, indexName)
	}

	return unusedIndexes, nil
}

// GetSlowQueries returns slow queries from pg_stat_statements
func (im *IndexManager) GetSlowQueries(ctx context.Context, minDuration time.Duration) ([]map[string]interface{}, error) {
	conn := im.pool.GetConnectionForRead()

	query := `
		SELECT 
			query,
			calls,
			total_time,
			mean_time,
			rows,
			100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
		FROM pg_stat_statements 
		WHERE mean_time > $1
		ORDER BY mean_time DESC
		LIMIT 50
	`

	rows, err := conn.QueryxContext(ctx, query, minDuration.Milliseconds())
	if err != nil {
		return nil, fmt.Errorf("failed to get slow queries: %w", err)
	}
	defer rows.Close()

	var slowQueries []map[string]interface{}
	for rows.Next() {
		var query, calls, totalTime, meanTime, rowCount, hitPercent interface{}

		if err := rows.Scan(&query, &calls, &totalTime, &meanTime, &rowCount, &hitPercent); err != nil {
			return nil, fmt.Errorf("failed to scan slow query: %w", err)
		}

		slowQueries = append(slowQueries, map[string]interface{}{
			"query":       query,
			"calls":       calls,
			"total_time":  totalTime,
			"mean_time":   meanTime,
			"rows":        rowCount,
			"hit_percent": hitPercent,
		})
	}

	return slowQueries, nil
}

// CreateDefaultIndexes creates default indexes for ArxOS tables
func (im *IndexManager) CreateDefaultIndexes(ctx context.Context) error {
	defaultIndexes := []*IndexDefinition{
		// Buildings table indexes
		{
			Name:    "idx_buildings_name",
			Table:   "buildings",
			Columns: []string{"name"},
		},
		{
			Name:    "idx_buildings_created_at",
			Table:   "buildings",
			Columns: []string{"created_at"},
		},
		{
			Name:    "idx_buildings_location",
			Table:   "buildings",
			Columns: []string{"latitude", "longitude"},
		},

		// Equipment table indexes
		{
			Name:    "idx_equipment_building_id",
			Table:   "equipment",
			Columns: []string{"building_id"},
		},
		{
			Name:    "idx_equipment_type",
			Table:   "equipment",
			Columns: []string{"type"},
		},
		{
			Name:    "idx_equipment_status",
			Table:   "equipment",
			Columns: []string{"status"},
		},
		{
			Name:    "idx_equipment_building_type_status",
			Table:   "equipment",
			Columns: []string{"building_id", "type", "status"},
		},

		// Components table indexes
		{
			Name:    "idx_components_building_id",
			Table:   "components",
			Columns: []string{"building_id"},
		},
		{
			Name:    "idx_components_type",
			Table:   "components",
			Columns: []string{"type"},
		},
		{
			Name:    "idx_components_path",
			Table:   "components",
			Columns: []string{"path"},
		},
		{
			Name:    "idx_components_status",
			Table:   "components",
			Columns: []string{"status"},
		},

		// Users table indexes
		{
			Name:    "idx_users_email",
			Table:   "users",
			Columns: []string{"email"},
			Unique:  true,
		},
		{
			Name:    "idx_users_role",
			Table:   "users",
			Columns: []string{"role"},
		},
		{
			Name:    "idx_users_active",
			Table:   "users",
			Columns: []string{"active"},
		},

		// Organizations table indexes
		{
			Name:    "idx_organizations_name",
			Table:   "organizations",
			Columns: []string{"name"},
		},
		{
			Name:    "idx_organizations_plan",
			Table:   "organizations",
			Columns: []string{"plan"},
		},
	}

	for _, index := range defaultIndexes {
		if err := im.CreateIndex(ctx, index); err != nil {
			im.logger.Warn("Failed to create default index", "name", index.Name, "error", err)
			// Continue with other indexes even if one fails
		}
	}

	im.logger.Info("Default indexes creation completed")
	return nil
}

// buildCreateIndexQuery builds the CREATE INDEX SQL query
func (im *IndexManager) buildCreateIndexQuery(index *IndexDefinition) string {
	var parts []string

	parts = append(parts, "CREATE")

	if index.Unique {
		parts = append(parts, "UNIQUE")
	}

	if index.Concurrent {
		parts = append(parts, "INDEX CONCURRENTLY")
	} else {
		parts = append(parts, "INDEX")
	}

	parts = append(parts, index.Name)
	parts = append(parts, "ON")
	parts = append(parts, index.Table)

	// Add columns
	columnStr := "(" + strings.Join(index.Columns, ", ") + ")"
	parts = append(parts, columnStr)

	// Add partial index condition if specified
	if index.Partial != "" {
		parts = append(parts, "WHERE", index.Partial)
	}

	return strings.Join(parts, " ")
}

// OptimizeDatabase performs comprehensive database optimization
func (im *IndexManager) OptimizeDatabase(ctx context.Context) error {
	im.logger.Info("Starting database optimization")

	// Analyze all tables
	tables := []string{"buildings", "equipment", "components", "users", "organizations"}
	for _, table := range tables {
		if err := im.AnalyzeTable(ctx, table); err != nil {
			im.logger.Warn("Failed to analyze table", "table", table, "error", err)
		}
	}

	// Vacuum tables
	for _, table := range tables {
		if err := im.VacuumTable(ctx, table, false); err != nil {
			im.logger.Warn("Failed to vacuum table", "table", table, "error", err)
		}
	}

	im.logger.Info("Database optimization completed")
	return nil
}
