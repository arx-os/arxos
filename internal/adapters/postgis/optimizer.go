package postgis

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/jmoiron/sqlx"
)

// QueryOptimizer handles database query optimization
type QueryOptimizer struct {
	db      *sqlx.DB
	metrics QueryMetrics
}

// QueryMetrics tracks query performance
type QueryMetrics struct {
	SlowQueries      []SlowQuery
	QueryStats       map[string]*QueryStat
	IndexSuggestions []IndexSuggestion
}

// SlowQuery represents a slow-running query
type SlowQuery struct {
	Query      string
	Duration   time.Duration
	Rows       int64
	Timestamp  time.Time
	ExplainPlan string
}

// QueryStat tracks statistics for a query pattern
type QueryStat struct {
	Pattern      string
	Count        int64
	TotalTime    time.Duration
	AvgTime      time.Duration
	MinTime      time.Duration
	MaxTime      time.Duration
	LastExecuted time.Time
}

// IndexSuggestion recommends a new index
type IndexSuggestion struct {
	Table      string
	Columns    []string
	Reason     string
	ImpactScore int // 1-10 scale
	Query      string
}

// NewQueryOptimizer creates a new optimizer
func NewQueryOptimizer(db *sqlx.DB) *QueryOptimizer {
	return &QueryOptimizer{
		db: db,
		metrics: QueryMetrics{
			QueryStats: make(map[string]*QueryStat),
		},
	}
}

// OptimizeSpatialQueries creates optimized spatial queries
func (o *QueryOptimizer) OptimizeSpatialQueries(ctx context.Context) error {
	log.Println("Optimizing spatial queries...")

	// Ensure spatial indexes exist
	spatialIndexes := []struct {
		Table  string
		Column string
		Index  string
	}{
		{"buildings", "origin", "idx_buildings_origin_gist"},
		{"equipment", "position", "idx_equipment_position_gist"},
	}

	for _, idx := range spatialIndexes {
		query := fmt.Sprintf(`
			CREATE INDEX IF NOT EXISTS %s
			ON %s USING GIST(%s)
		`, idx.Index, idx.Table, idx.Column)

		if _, err := o.db.ExecContext(ctx, query); err != nil {
			log.Printf("Warning: Failed to create spatial index %s: %v", idx.Index, err)
		} else {
			log.Printf("Ensured spatial index %s exists", idx.Index)
		}
	}

	// Create compound indexes for common query patterns
	compoundIndexes := []struct {
		Table   string
		Columns []string
		Index   string
	}{
		{"equipment", []string{"building_id", "status"}, "idx_equipment_building_status"},
		{"equipment", []string{"type", "status"}, "idx_equipment_type_status"},
		{"equipment", []string{"building_id", "path"}, "idx_equipment_building_path"},
		{"users", []string{"email", "status"}, "idx_users_email_status"},
		{"sessions", []string{"user_id", "expires_at"}, "idx_sessions_user_expires"},
	}

	for _, idx := range compoundIndexes {
		columns := strings.Join(idx.Columns, ", ")
		query := fmt.Sprintf(`
			CREATE INDEX IF NOT EXISTS %s
			ON %s (%s)
		`, idx.Index, idx.Table, columns)

		if _, err := o.db.ExecContext(ctx, query); err != nil {
			log.Printf("Warning: Failed to create compound index %s: %v", idx.Index, err)
		} else {
			log.Printf("Ensured compound index %s exists", idx.Index)
		}
	}

	// Update table statistics for better query planning
	tables := []string{"buildings", "equipment", "users", "sessions"}
	for _, table := range tables {
		query := fmt.Sprintf("ANALYZE %s", table)
		if _, err := o.db.ExecContext(ctx, query); err != nil {
			log.Printf("Warning: Failed to analyze table %s: %v", table, err)
		} else {
			log.Printf("Updated statistics for table %s", table)
		}
	}

	return nil
}

// FindNearbyOptimized is an optimized version of FindNearby
func (o *QueryOptimizer) FindNearbyOptimized(ctx context.Context, lon, lat, alt float64, radiusMeters float64) ([]Equipment, error) {
	// Use bounding box pre-filter for better performance
	// Convert radius to approximate degrees (1 degree ≈ 111,111 meters at equator)
	degreeRadius := radiusMeters / 111111.0

	query := `
		WITH center AS (
			SELECT ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)::geography as point
		),
		bbox AS (
			SELECT
				$1 - $4 as min_lon,
				$1 + $4 as max_lon,
				$2 - $4 as min_lat,
				$2 + $4 as max_lat
		)
		SELECT
			e.id,
			e.building_id,
			e.path,
			e.name,
			e.type,
			e.status,
			e.confidence,
			ST_AsGeoJSON(e.position) as position_json,
			ST_Distance(e.position::geography, center.point) as distance_meters
		FROM equipment e, center, bbox
		WHERE
			-- Bounding box filter (uses spatial index)
			ST_Within(
				e.position,
				ST_MakeEnvelope(bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat, 4326)
			)
			-- Precise distance filter
			AND ST_DWithin(e.position::geography, center.point, $5)
		ORDER BY distance_meters ASC
		LIMIT 1000
	`

	rows, err := o.db.QueryContext(ctx, query, lon, lat, alt, degreeRadius, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("optimized spatial query failed: %w", err)
	}
	defer rows.Close()

	var equipment []Equipment
	for rows.Next() {
		var eq Equipment
		var positionJSON string
		var distance float64

		err := rows.Scan(
			&eq.ID,
			&eq.BuildingID,
			&eq.Path,
			&eq.Name,
			&eq.Type,
			&eq.Status,
			&eq.Confidence,
			&positionJSON,
			&distance,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		// Parse position from GeoJSON
		// This would need proper GeoJSON parsing in production
		eq.Metadata = map[string]interface{}{
			"distance_meters": distance,
			"position_json":   positionJSON,
		}

		equipment = append(equipment, eq)
	}

	return equipment, nil
}

// OptimizeEquipmentByFloor creates an optimized query for equipment on a floor
func (o *QueryOptimizer) OptimizeEquipmentByFloor(ctx context.Context, buildingID string, floor int) ([]Equipment, error) {
	// Use prepared statement for better performance
	query := `
		SELECT
			e.id,
			e.building_id,
			e.path,
			e.name,
			e.type,
			e.status,
			e.confidence,
			ST_X(e.position) as lon,
			ST_Y(e.position) as lat,
			ST_Z(e.position) as alt
		FROM equipment e
		WHERE e.building_id = $1
		AND e.path LIKE $2
		ORDER BY e.path, e.name
	`

	floorPattern := fmt.Sprintf("Floor %d/%%", floor)

	rows, err := o.db.QueryContext(ctx, query, buildingID, floorPattern)
	if err != nil {
		return nil, fmt.Errorf("floor equipment query failed: %w", err)
	}
	defer rows.Close()

	var equipment []Equipment
	for rows.Next() {
		var eq Equipment
		var lon, lat, alt sql.NullFloat64

		err := rows.Scan(
			&eq.ID,
			&eq.BuildingID,
			&eq.Path,
			&eq.Name,
			&eq.Type,
			&eq.Status,
			&eq.Confidence,
			&lon, &lat, &alt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		if lon.Valid && lat.Valid {
			eq.Location = Position{
				Lon: lon.Float64,
				Lat: lat.Float64,
				Alt: alt.Float64,
			}
		}

		equipment = append(equipment, eq)
	}

	return equipment, nil
}

// AnalyzeSlowQueries finds and analyzes slow queries
func (o *QueryOptimizer) AnalyzeSlowQueries(ctx context.Context, thresholdMs int) error {
	// Query PostgreSQL statistics for slow queries
	query := `
		SELECT
			query,
			calls,
			total_time,
			mean_time,
			min_time,
			max_time,
			stddev_time,
			rows
		FROM pg_stat_statements
		WHERE mean_time > $1
		ORDER BY mean_time DESC
		LIMIT 20
	`

	// Note: pg_stat_statements extension must be enabled
	rows, err := o.db.QueryContext(ctx, query, thresholdMs)
	if err != nil {
		// Extension might not be installed
		if strings.Contains(err.Error(), "pg_stat_statements") {
			log.Println("pg_stat_statements extension not available, skipping slow query analysis")
			return nil
		}
		return fmt.Errorf("failed to query slow queries: %w", err)
	}
	defer rows.Close()

	o.metrics.SlowQueries = nil
	for rows.Next() {
		var queryText string
		var calls int64
		var totalTime, meanTime, minTime, maxTime, stddevTime float64
		var rowCount int64

		err := rows.Scan(
			&queryText,
			&calls,
			&totalTime,
			&meanTime,
			&minTime,
			&maxTime,
			&stddevTime,
			&rowCount,
		)
		if err != nil {
			continue
		}

		slowQuery := SlowQuery{
			Query:     queryText,
			Duration:  time.Duration(meanTime * float64(time.Millisecond)),
			Rows:      rowCount / calls, // Average rows per call
			Timestamp: time.Now(),
		}

		// Get EXPLAIN plan for the query if possible
		if explainPlan, err := o.getExplainPlan(ctx, queryText); err == nil {
			slowQuery.ExplainPlan = explainPlan
		}

		o.metrics.SlowQueries = append(o.metrics.SlowQueries, slowQuery)

		// Suggest indexes based on the slow query
		o.suggestIndexes(queryText, meanTime)
	}

	return nil
}

// getExplainPlan gets the execution plan for a query
func (o *QueryOptimizer) getExplainPlan(ctx context.Context, query string) (string, error) {
	// Only explain SELECT queries for safety
	if !strings.HasPrefix(strings.ToUpper(strings.TrimSpace(query)), "SELECT") {
		return "", fmt.Errorf("can only explain SELECT queries")
	}

	explainQuery := fmt.Sprintf("EXPLAIN ANALYZE %s", query)

	rows, err := o.db.QueryContext(ctx, explainQuery)
	if err != nil {
		return "", err
	}
	defer rows.Close()

	var plan strings.Builder
	for rows.Next() {
		var line string
		if err := rows.Scan(&line); err != nil {
			return "", err
		}
		plan.WriteString(line)
		plan.WriteString("\n")
	}

	return plan.String(), nil
}

// suggestIndexes analyzes a query and suggests potential indexes
func (o *QueryOptimizer) suggestIndexes(query string, avgTime float64) {
	queryLower := strings.ToLower(query)

	// Simple heuristic-based index suggestions
	suggestions := []struct {
		pattern    string
		table      string
		columns    []string
		reason     string
	}{
		{
			pattern: "where building_id",
			table:   "equipment",
			columns: []string{"building_id"},
			reason:  "Frequent filtering by building_id",
		},
		{
			pattern: "where status",
			table:   "equipment",
			columns: []string{"status"},
			reason:  "Frequent filtering by status",
		},
		{
			pattern: "where type",
			table:   "equipment",
			columns: []string{"type"},
			reason:  "Frequent filtering by equipment type",
		},
		{
			pattern: "st_dwithin",
			table:   "equipment",
			columns: []string{"position"},
			reason:  "Spatial proximity queries",
		},
		{
			pattern: "order by created_at",
			table:   "equipment",
			columns: []string{"created_at"},
			reason:  "Frequent ordering by creation time",
		},
	}

	for _, s := range suggestions {
		if strings.Contains(queryLower, s.pattern) {
			impactScore := 1
			if avgTime > 100 {
				impactScore = 5
			}
			if avgTime > 1000 {
				impactScore = 8
			}
			if avgTime > 5000 {
				impactScore = 10
			}

			o.metrics.IndexSuggestions = append(o.metrics.IndexSuggestions, IndexSuggestion{
				Table:       s.table,
				Columns:     s.columns,
				Reason:      s.reason,
				ImpactScore: impactScore,
				Query:       query,
			})
		}
	}
}

// GetMetrics returns current optimization metrics
func (o *QueryOptimizer) GetMetrics() QueryMetrics {
	return o.metrics
}

// CreateMaterializedView creates a materialized view for complex queries
func (o *QueryOptimizer) CreateMaterializedView(ctx context.Context, name, query string) error {
	dropQuery := fmt.Sprintf("DROP MATERIALIZED VIEW IF EXISTS %s", name)
	createQuery := fmt.Sprintf("CREATE MATERIALIZED VIEW %s AS %s", name, query)
	indexQuery := fmt.Sprintf("CREATE UNIQUE INDEX ON %s (id)", name)

	// Drop existing view
	if _, err := o.db.ExecContext(ctx, dropQuery); err != nil {
		return fmt.Errorf("failed to drop materialized view: %w", err)
	}

	// Create new view
	if _, err := o.db.ExecContext(ctx, createQuery); err != nil {
		return fmt.Errorf("failed to create materialized view: %w", err)
	}

	// Create index
	if _, err := o.db.ExecContext(ctx, indexQuery); err != nil {
		log.Printf("Warning: Failed to create index on materialized view: %v", err)
	}

	log.Printf("Created materialized view: %s", name)
	return nil
}

// RefreshMaterializedView refreshes a materialized view
func (o *QueryOptimizer) RefreshMaterializedView(ctx context.Context, name string) error {
	query := fmt.Sprintf("REFRESH MATERIALIZED VIEW CONCURRENTLY %s", name)
	if _, err := o.db.ExecContext(ctx, query); err != nil {
		return fmt.Errorf("failed to refresh materialized view: %w", err)
	}
	return nil
}