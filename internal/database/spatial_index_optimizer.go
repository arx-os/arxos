package database

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// SpatialIndexOptimizer provides advanced spatial index management
type SpatialIndexOptimizer struct {
	db           *PostGISDB
	statsCache   map[string]*IndexStats
	lastAnalyze  time.Time
	maintenance  *MaintenanceScheduler
}

// IndexStats holds statistics about index usage
type IndexStats struct {
	Name         string
	Size         int64
	Scans        int64
	TuplesRead   int64
	TuplesFetched int64
	LastUsed     time.Time
	Bloat        float64
}

// NewSpatialIndexOptimizer creates a new optimizer
func NewSpatialIndexOptimizer(db *PostGISDB) *SpatialIndexOptimizer {
	return &SpatialIndexOptimizer{
		db:          db,
		statsCache:  make(map[string]*IndexStats),
		maintenance: NewMaintenanceScheduler(db),
	}
}

// OptimizeIndices performs comprehensive index optimization
func (o *SpatialIndexOptimizer) OptimizeIndices(ctx context.Context) error {
	logger.Info("Starting spatial index optimization...")

	// Step 1: Analyze current index usage
	if err := o.analyzeIndexUsage(ctx); err != nil {
		return fmt.Errorf("failed to analyze index usage: %w", err)
	}

	// Step 2: Create optimized indices based on query patterns
	if err := o.createOptimizedIndices(ctx); err != nil {
		return fmt.Errorf("failed to create optimized indices: %w", err)
	}

	// Step 3: Create specialized indices for common query patterns
	if err := o.createSpecializedIndices(ctx); err != nil {
		return fmt.Errorf("failed to create specialized indices: %w", err)
	}

	// Step 4: Setup automatic maintenance
	if err := o.setupMaintenanceTasks(ctx); err != nil {
		return fmt.Errorf("failed to setup maintenance: %w", err)
	}

	// Step 5: Update table statistics
	if err := o.updateStatistics(ctx); err != nil {
		return fmt.Errorf("failed to update statistics: %w", err)
	}

	logger.Info("Spatial index optimization completed successfully")
	return nil
}

// analyzeIndexUsage examines current index usage patterns
func (o *SpatialIndexOptimizer) analyzeIndexUsage(ctx context.Context) error {
	query := `
		SELECT
			schemaname,
			tablename,
			indexname,
			idx_scan,
			idx_tup_read,
			idx_tup_fetch,
			pg_relation_size(indexrelid) as index_size
		FROM pg_stat_user_indexes
		WHERE schemaname = 'public'
		ORDER BY idx_scan DESC
	`

	rows, err := o.db.db.QueryContext(ctx, query)
	if err != nil {
		return err
	}
	defer rows.Close()

	for rows.Next() {
		var schema, table, index string
		var scans, tupRead, tupFetch, size int64

		if err := rows.Scan(&schema, &table, &index, &scans, &tupRead, &tupFetch, &size); err != nil {
			continue
		}

		o.statsCache[index] = &IndexStats{
			Name:          index,
			Size:          size,
			Scans:         scans,
			TuplesRead:    tupRead,
			TuplesFetched: tupFetch,
			LastUsed:      time.Now(),
		}
	}

	o.lastAnalyze = time.Now()
	return nil
}

// createOptimizedIndices creates optimized spatial indices
func (o *SpatialIndexOptimizer) createOptimizedIndices(ctx context.Context) error {
	indices := []struct {
		name  string
		query string
	}{
		// Multi-column GIST index for complex spatial queries
		{
			"idx_spatial_composite",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_composite
			 ON equipment_positions USING GIST (
				position,
				box3d(position)
			 )`,
		},
		// Optimized index for nearest neighbor queries
		{
			"idx_spatial_knn",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_knn
			 ON equipment_positions USING GIST (position)
			 WITH (fillfactor = 90)`,
		},
		// Clustered index for floor-based queries
		{
			"idx_spatial_floor_cluster",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_floor_cluster
			 ON equipment_positions USING BTREE (
				ST_Z(position)::int,
				equipment_id
			 )`,
		},
		// Spatial index with bounding box optimization
		{
			"idx_spatial_bbox",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_bbox
			 ON equipment_positions USING GIST (
				ST_Envelope(ST_Buffer(position, 0.001))
			 )`,
		},
		// Index for time-series spatial queries
		{
			"idx_spatial_temporal",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_temporal
			 ON equipment_positions USING BTREE (
				date_trunc('hour', updated_at),
				equipment_id
			 ) INCLUDE (position)`,
		},
	}

	for _, idx := range indices {
		logger.Info("Creating index: %s", idx.name)
		if _, err := o.db.db.ExecContext(ctx, idx.query); err != nil {
			logger.Warn("Failed to create index %s: %v", idx.name, err)
			// Continue with other indices
		}
	}

	return nil
}

// createSpecializedIndices creates indices for specific query patterns
func (o *SpatialIndexOptimizer) createSpecializedIndices(ctx context.Context) error {
	specializedIndices := []struct {
		name  string
		query string
	}{
		// Index for proximity searches with confidence filtering
		{
			"idx_proximity_confident",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proximity_confident
			 ON equipment_positions USING GIST (position)
			 WHERE confidence >= 0.8`,
		},
		// Index for equipment density analysis
		{
			"idx_spatial_density",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_density
			 ON equipment_positions USING GIST (
				ST_SnapToGrid(position, 5.0)
			 )`,
		},
		// Index for cross-floor connectivity queries
		{
			"idx_vertical_connections",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vertical_connections
			 ON equipment_positions USING BTREE (
				ST_X(position)::numeric(10,2),
				ST_Y(position)::numeric(10,2)
			 ) INCLUDE (ST_Z(position), equipment_id)`,
		},
		// Partial index for active equipment only
		{
			"idx_active_equipment_spatial",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_equipment_spatial
			 ON equipment_positions USING GIST (position)
			 WHERE equipment_id IN (
				SELECT id FROM equipment WHERE status = 'active'
			 )`,
		},
		// Index for building zone queries
		{
			"idx_building_zones",
			`CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_zones
			 ON equipment_positions USING GIST (
				ST_Transform(
					ST_SnapToGrid(position, 10.0),
					3857  -- Web Mercator for zone calculations
				)
			 )`,
		},
	}

	for _, idx := range specializedIndices {
		logger.Info("Creating specialized index: %s", idx.name)
		if _, err := o.db.db.ExecContext(ctx, idx.query); err != nil {
			logger.Warn("Failed to create specialized index %s: %v", idx.name, err)
		}
	}

	return nil
}

// setupMaintenanceTasks configures automatic index maintenance
func (o *SpatialIndexOptimizer) setupMaintenanceTasks(ctx context.Context) error {
	// Create maintenance function
	maintenanceFunc := `
		CREATE OR REPLACE FUNCTION maintain_spatial_indices()
		RETURNS void AS $$
		BEGIN
			-- Reindex bloated indices
			PERFORM pg_catalog.reindex_index(indexrelid::regclass)
			FROM pg_stat_user_indexes
			WHERE pg_relation_size(indexrelid) > 100000000  -- 100MB
			  AND idx_scan > 0;

			-- Update statistics on frequently used tables
			ANALYZE equipment_positions;
			ANALYZE equipment;

			-- Clean up orphaned index entries
			PERFORM pg_catalog.amcheck_verify_heapam('equipment_positions'::regclass);
		EXCEPTION
			WHEN OTHERS THEN
				RAISE WARNING 'Maintenance task failed: %', SQLERRM;
		END;
		$$ LANGUAGE plpgsql;
	`

	if _, err := o.db.db.ExecContext(ctx, maintenanceFunc); err != nil {
		return fmt.Errorf("failed to create maintenance function: %w", err)
	}

	// Schedule periodic maintenance
	scheduleQuery := `
		CREATE OR REPLACE FUNCTION schedule_spatial_maintenance()
		RETURNS void AS $$
		BEGIN
			-- Run maintenance daily at 2 AM
			INSERT INTO pg_cron.job (schedule, command)
			VALUES ('0 2 * * *', 'SELECT maintain_spatial_indices()')
			ON CONFLICT DO NOTHING;
		END;
		$$ LANGUAGE plpgsql;
	`

	// Note: This requires pg_cron extension
	if _, err := o.db.db.ExecContext(ctx, scheduleQuery); err != nil {
		logger.Warn("Could not schedule automatic maintenance (pg_cron may not be available): %v", err)
	}

	return nil
}

// updateStatistics updates table and index statistics
func (o *SpatialIndexOptimizer) updateStatistics(ctx context.Context) error {
	logger.Info("Updating spatial index statistics...")

	queries := []string{
		"VACUUM ANALYZE equipment_positions",
		"VACUUM ANALYZE equipment",
		"VACUUM ANALYZE buildings",
		"VACUUM ANALYZE floors",
	}

	for _, query := range queries {
		if _, err := o.db.db.ExecContext(ctx, query); err != nil {
			logger.Warn("Failed to update statistics: %v", err)
		}
	}

	// Update PostGIS geometry statistics
	geoStatsQuery := `
		SELECT UpdateGeometrySRID('equipment_positions', 'position', 4326);
		SELECT Populate_Geometry_Columns();
	`

	if _, err := o.db.db.ExecContext(ctx, geoStatsQuery); err != nil {
		logger.Warn("Failed to update geometry statistics: %v", err)
	}

	return nil
}

// RecommendIndexes analyzes query patterns and recommends new indexes
func (o *SpatialIndexOptimizer) RecommendIndexes(ctx context.Context) ([]string, error) {
	recommendations := []string{}

	// Analyze slow queries
	slowQueryAnalysis := `
		SELECT
			query,
			calls,
			mean_exec_time,
			total_exec_time
		FROM pg_stat_statements
		WHERE query LIKE '%equipment_positions%'
		  AND mean_exec_time > 100  -- queries slower than 100ms
		ORDER BY mean_exec_time DESC
		LIMIT 10
	`

	rows, err := o.db.db.QueryContext(ctx, slowQueryAnalysis)
	if err != nil {
		// pg_stat_statements might not be enabled
		logger.Warn("Could not analyze slow queries: %v", err)
		return recommendations, nil
	}
	defer rows.Close()

	for rows.Next() {
		var query string
		var calls int64
		var meanTime, totalTime float64

		if err := rows.Scan(&query, &calls, &meanTime, &totalTime); err != nil {
			continue
		}

		// Analyze query pattern and suggest index
		if contains(query, "ST_DWithin") && !o.hasIndex("idx_proximity") {
			recommendations = append(recommendations,
				"CREATE INDEX idx_proximity ON equipment_positions USING GIST (position)")
		}

		if contains(query, "ST_Z(position)") && !o.hasIndex("idx_floor_level") {
			recommendations = append(recommendations,
				"CREATE INDEX idx_floor_level ON equipment_positions USING BTREE (ST_Z(position))")
		}
	}

	return recommendations, nil
}

// hasIndex checks if an index exists
func (o *SpatialIndexOptimizer) hasIndex(name string) bool {
	_, exists := o.statsCache[name]
	return exists
}

// MaintenanceScheduler handles automatic maintenance tasks
type MaintenanceScheduler struct {
	db       *PostGISDB
	schedule map[string]time.Duration
}

// NewMaintenanceScheduler creates a new maintenance scheduler
func NewMaintenanceScheduler(db *PostGISDB) *MaintenanceScheduler {
	return &MaintenanceScheduler{
		db: db,
		schedule: map[string]time.Duration{
			"reindex": 24 * time.Hour,
			"analyze": 6 * time.Hour,
			"vacuum":  7 * 24 * time.Hour,
		},
	}
}

