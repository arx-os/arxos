package database

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
	"github.com/lib/pq"
)

// OptimizedSpatialQueries provides optimized spatial query implementations
type OptimizedSpatialQueries struct {
	db        *PostGISDB
	optimizer *SpatialOptimizer
}

// NewOptimizedSpatialQueries creates optimized spatial queries handler
func NewOptimizedSpatialQueries(db *PostGISDB) (*OptimizedSpatialQueries, error) {
	optimizer, err := NewSpatialOptimizer(db)
	if err != nil {
		return nil, fmt.Errorf("failed to create spatial optimizer: %w", err)
	}

	return &OptimizedSpatialQueries{
		db:        db,
		optimizer: optimizer,
	}, nil
}

// FindEquipmentNearOptimized performs optimized proximity search with caching
func (q *OptimizedSpatialQueries) FindEquipmentNearOptimized(ctx context.Context, center spatial.Point3D, radius float64) ([]string, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("proximity_search", time.Since(startTime))
	}()

	// Check cache first
	cacheKey := fmt.Sprintf("proximity:%.2f:%.2f:%.2f:%.2f", center.X, center.Y, center.Z, radius)
	if cached, found := q.optimizer.cache.Get(cacheKey); found {
		return cached.([]string), nil
	}

	// Choose index based on radius
	var query string
	if radius < 10 {
		// Use fine-grained index for small radius
		query = q.buildProximityQuery("idx_equipment_position_fine")
	} else if radius < 100 {
		// Use medium index
		query = q.buildProximityQuery("idx_equipment_position_medium")
	} else {
		// Use coarse index for large radius
		query = q.buildProximityQuery("idx_equipment_position_coarse")
	}

	// Execute query
	rows, err := q.db.db.QueryContext(ctx, query, center.X, center.Y, center.Z, radius)
	if err != nil {
		return nil, fmt.Errorf("proximity search failed: %w", err)
	}
	defer rows.Close()

	var results []string
	for rows.Next() {
		var equipmentID string
		var distance float64
		if err := rows.Scan(&equipmentID, &distance); err != nil {
			continue
		}
		results = append(results, equipmentID)
	}

	// Cache results
	q.optimizer.cache.Set(cacheKey, results, int64(len(results)*64))

	// Prefetch related queries
	q.optimizer.prefetcher.RecordAccess(cacheKey)
	q.prefetchNearbyRegions(ctx, center, radius)

	return results, nil
}

// buildProximityQuery builds optimized proximity query
func (q *OptimizedSpatialQueries) buildProximityQuery(indexHint string) string {
	return fmt.Sprintf(`
		SELECT
			equipment_id,
			ST_Distance(position, ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)) as distance
		FROM equipment_positions /*+ INDEX(%s) */
		WHERE ST_DWithin(
			position,
			ST_SetSRID(ST_MakePoint($1, $2, $3), 4326),
			$4
		)
		ORDER BY distance
		LIMIT 1000
	`, indexHint)
}

// FindEquipmentInBoundingBoxOptimized performs optimized bounding box search
func (q *OptimizedSpatialQueries) FindEquipmentInBoundingBoxOptimized(ctx context.Context, bbox spatial.BoundingBox) ([]string, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("bbox_search", time.Since(startTime))
	}()

	// Check cache
	cacheKey := fmt.Sprintf("bbox:%.2f:%.2f:%.2f:%.2f:%.2f:%.2f",
		bbox.Min.X, bbox.Min.Y, bbox.Min.Z,
		bbox.Max.X, bbox.Max.Y, bbox.Max.Z)

	if cached, found := q.optimizer.cache.Get(cacheKey); found {
		return cached.([]string), nil
	}

	// Build optimized query with 3D index
	query := `
		SELECT equipment_id
		FROM equipment_positions
		WHERE position &&& ST_MakeBox3D(
			ST_SetSRID(ST_MakePoint($1, $2, $3), 4326),
			ST_SetSRID(ST_MakePoint($4, $5, $6), 4326)
		)
		AND ST_3DIntersects(
			position,
			ST_MakeBox3D(
				ST_SetSRID(ST_MakePoint($1, $2, $3), 4326),
				ST_SetSRID(ST_MakePoint($4, $5, $6), 4326)
			)
		)
	`

	rows, err := q.db.db.QueryContext(ctx, query,
		bbox.Min.X, bbox.Min.Y, bbox.Min.Z,
		bbox.Max.X, bbox.Max.Y, bbox.Max.Z)
	if err != nil {
		return nil, fmt.Errorf("bounding box search failed: %w", err)
	}
	defer rows.Close()

	var results []string
	for rows.Next() {
		var equipmentID string
		if err := rows.Scan(&equipmentID); err != nil {
			continue
		}
		results = append(results, equipmentID)
	}

	// Cache results
	q.optimizer.cache.Set(cacheKey, results, int64(len(results)*64))

	return results, nil
}

// FindEquipmentOnFloorOptimized performs optimized floor containment search
func (q *OptimizedSpatialQueries) FindEquipmentOnFloorOptimized(ctx context.Context, floorID string) ([]string, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("floor_search", time.Since(startTime))
	}()

	// Check cache
	cacheKey := fmt.Sprintf("floor:%s", floorID)
	if cached, found := q.optimizer.cache.Get(cacheKey); found {
		return cached.([]string), nil
	}

	// Use materialized view if available
	query := `
		SELECT equipment_id
		FROM equipment_positions ep
		WHERE EXISTS (
			SELECT 1
			FROM floor_boundaries fb
			WHERE fb.floor_id = $1
			AND ST_Contains(fb.boundary, ep.position)
		)
	`

	rows, err := q.db.db.QueryContext(ctx, query, floorID)
	if err != nil {
		return nil, fmt.Errorf("floor search failed: %w", err)
	}
	defer rows.Close()

	var results []string
	for rows.Next() {
		var equipmentID string
		if err := rows.Scan(&equipmentID); err != nil {
			continue
		}
		results = append(results, equipmentID)
	}

	// Cache results with longer TTL for floor data (changes less frequently)
	q.optimizer.cache.Set(cacheKey, results, int64(len(results)*64))

	return results, nil
}

// BulkProximitySearch performs proximity searches for multiple centers
func (q *OptimizedSpatialQueries) BulkProximitySearch(ctx context.Context, centers []spatial.Point3D, radius float64) (map[string][]string, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("bulk_proximity", time.Since(startTime))
	}()

	return q.optimizer.bulkOps.BulkProximitySearch(ctx, centers, radius)
}

// StreamProximityChanges creates a real-time stream of proximity changes
func (q *OptimizedSpatialQueries) StreamProximityChanges(center spatial.Point3D, radius float64) (<-chan SpatialEvent, func(), error) {
	return q.optimizer.streamManager.StreamProximityChanges(center, radius)
}

// FindKNearestNeighbors finds K nearest neighbors efficiently
func (q *OptimizedSpatialQueries) FindKNearestNeighbors(ctx context.Context, center spatial.Point3D, k int) ([]EquipmentDistance, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("knn_search", time.Since(startTime))
	}()

	// Check cache
	cacheKey := fmt.Sprintf("knn:%.2f:%.2f:%.2f:%d", center.X, center.Y, center.Z, k)
	if cached, found := q.optimizer.cache.Get(cacheKey); found {
		return cached.([]EquipmentDistance), nil
	}

	// Use KNN operator for efficient search
	query := `
		SELECT
			equipment_id,
			position <-> ST_SetSRID(ST_MakePoint($1, $2, $3), 4326) as distance
		FROM equipment_positions
		ORDER BY position <-> ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)
		LIMIT $4
	`

	rows, err := q.db.db.QueryContext(ctx, query, center.X, center.Y, center.Z, k)
	if err != nil {
		return nil, fmt.Errorf("KNN search failed: %w", err)
	}
	defer rows.Close()

	var results []EquipmentDistance
	for rows.Next() {
		var ed EquipmentDistance
		if err := rows.Scan(&ed.EquipmentID, &ed.Distance); err != nil {
			continue
		}
		results = append(results, ed)
	}

	// Cache results
	q.optimizer.cache.Set(cacheKey, results, int64(len(results)*100))

	return results, nil
}

// EquipmentDistance represents equipment with distance
type EquipmentDistance struct {
	EquipmentID string
	Distance    float64
}

// FindEquipmentAlongPath finds equipment along a path
func (q *OptimizedSpatialQueries) FindEquipmentAlongPath(ctx context.Context, path []spatial.Point3D, bufferDistance float64) ([]string, error) {
	if len(path) < 2 {
		return nil, fmt.Errorf("path must have at least 2 points")
	}

	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("path_search", time.Since(startTime))
	}()

	// Build LineString from path
	points := make([]string, len(path))
	for i, p := range path {
		points[i] = fmt.Sprintf("%f %f %f", p.X, p.Y, p.Z)
	}
	lineString := fmt.Sprintf("LINESTRING Z(%s)", strings.Join(points, ","))

	// Query with buffer around path
	query := `
		SELECT DISTINCT equipment_id
		FROM equipment_positions
		WHERE ST_DWithin(
			position,
			ST_Buffer(ST_GeomFromText($1, 4326), $2),
			0
		)
		ORDER BY equipment_id
	`

	rows, err := q.db.db.QueryContext(ctx, query, lineString, bufferDistance)
	if err != nil {
		return nil, fmt.Errorf("path search failed: %w", err)
	}
	defer rows.Close()

	var results []string
	for rows.Next() {
		var equipmentID string
		if err := rows.Scan(&equipmentID); err != nil {
			continue
		}
		results = append(results, equipmentID)
	}

	return results, nil
}

// ClusterEquipment performs spatial clustering using DBSCAN
func (q *OptimizedSpatialQueries) ClusterEquipment(ctx context.Context, eps float64, minPoints int) ([]EquipmentCluster, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("clustering", time.Since(startTime))
	}()

	// Use PostGIS clustering function
	query := `
		WITH clusters AS (
			SELECT
				equipment_id,
				ST_ClusterDBSCAN(position, eps := $1, minpoints := $2)
					OVER () as cluster_id,
				position
			FROM equipment_positions
		)
		SELECT
			cluster_id,
			array_agg(equipment_id) as equipment_ids,
			ST_AsText(ST_Centroid(ST_Collect(position))) as centroid
		FROM clusters
		WHERE cluster_id IS NOT NULL
		GROUP BY cluster_id
		ORDER BY cluster_id
	`

	rows, err := q.db.db.QueryContext(ctx, query, eps, minPoints)
	if err != nil {
		return nil, fmt.Errorf("clustering failed: %w", err)
	}
	defer rows.Close()

	var clusters []EquipmentCluster
	for rows.Next() {
		var cluster EquipmentCluster
		var centroidWKT string
		if err := rows.Scan(&cluster.ID, pq.Array(&cluster.EquipmentIDs), &centroidWKT); err != nil {
			continue
		}

		// Parse centroid
		cluster.Centroid = parseWKTPoint(centroidWKT)
		clusters = append(clusters, cluster)
	}

	return clusters, nil
}

// EquipmentCluster represents a spatial cluster of equipment
type EquipmentCluster struct {
	ID           int
	EquipmentIDs []string
	Centroid     spatial.Point3D
}

// GetSpatialStatistics calculates spatial statistics for equipment
func (q *OptimizedSpatialQueries) GetSpatialStatistics(ctx context.Context) (*SpatialStatistics, error) {
	startTime := time.Now()
	defer func() {
		q.optimizer.metricsCollector.RecordQuery("spatial_stats", time.Since(startTime))
	}()

	query := `
		SELECT
			COUNT(*) as total_equipment,
			ST_AsText(ST_Centroid(ST_Collect(position))) as centroid,
			ST_AsText(ST_Extent(position)) as extent,
			AVG(ST_Z(position)) as avg_height,
			STDDEV(ST_Z(position)) as height_stddev,
			ST_Area(ST_ConvexHull(ST_Collect(position))) as convex_hull_area
		FROM equipment_positions
	`

	var stats SpatialStatistics
	var centroidWKT, extentWKT sql.NullString
	var avgHeight, heightStdDev, convexHullArea sql.NullFloat64

	err := q.db.db.QueryRowContext(ctx, query).Scan(
		&stats.TotalEquipment,
		&centroidWKT,
		&extentWKT,
		&avgHeight,
		&heightStdDev,
		&convexHullArea,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate spatial statistics: %w", err)
	}

	if centroidWKT.Valid {
		stats.Centroid = parseWKTPoint(centroidWKT.String)
	}
	if extentWKT.Valid {
		stats.BoundingBox = parseWKTBox(extentWKT.String)
	}
	if avgHeight.Valid {
		stats.AverageHeight = avgHeight.Float64
	}
	if heightStdDev.Valid {
		stats.HeightStdDev = heightStdDev.Float64
	}
	if convexHullArea.Valid {
		stats.ConvexHullArea = convexHullArea.Float64
	}

	return &stats, nil
}

// SpatialStatistics contains spatial statistics
type SpatialStatistics struct {
	TotalEquipment int
	Centroid       spatial.Point3D
	BoundingBox    spatial.BoundingBox
	AverageHeight  float64
	HeightStdDev   float64
	ConvexHullArea float64
}

// CreateSpatialIndices creates optimized spatial indices
func (q *OptimizedSpatialQueries) CreateSpatialIndices(ctx context.Context) error {
	return q.optimizer.indexManager.CreateOptimizedIndices(ctx)
}

// GetCacheMetrics returns cache performance metrics
func (q *OptimizedSpatialQueries) GetCacheMetrics() CacheMetrics {
	return q.optimizer.cache.GetMetrics()
}

// GetQueryMetrics returns query performance metrics
func (q *OptimizedSpatialQueries) GetQueryMetrics() map[string]*QueryMetrics {
	return q.optimizer.metricsCollector.GetMetrics()
}

// prefetchNearbyRegions prefetches data for nearby regions
func (q *OptimizedSpatialQueries) prefetchNearbyRegions(ctx context.Context, center spatial.Point3D, radius float64) {
	// Prefetch adjacent regions in background
	go func() {
		offsets := []struct{ dx, dy float64 }{
			{radius, 0}, {-radius, 0},
			{0, radius}, {0, -radius},
		}

		for _, offset := range offsets {
			adjacentCenter := spatial.Point3D{
				X: center.X + offset.dx,
				Y: center.Y + offset.dy,
				Z: center.Z,
			}

			cacheKey := fmt.Sprintf("proximity:%.2f:%.2f:%.2f:%.2f",
				adjacentCenter.X, adjacentCenter.Y, adjacentCenter.Z, radius)

			if _, found := q.optimizer.cache.Get(cacheKey); !found {
				// Perform the query and cache it
				q.FindEquipmentNearOptimized(ctx, adjacentCenter, radius)
			}
		}
	}()
}

// Helper functions

func parseWKTPoint(wkt string) spatial.Point3D {
	// Simple WKT point parser
	// Format: POINT(x y) or POINT Z(x y z)
	var x, y, z float64

	if strings.Contains(wkt, "POINT Z") {
		fmt.Sscanf(wkt, "POINT Z(%f %f %f)", &x, &y, &z)
	} else {
		fmt.Sscanf(wkt, "POINT(%f %f)", &x, &y)
	}

	return spatial.Point3D{X: x, Y: y, Z: z}
}

func parseWKTBox(wkt string) spatial.BoundingBox {
	// Simple WKT box parser
	// Format: BOX(x1 y1, x2 y2)
	var minX, minY, maxX, maxY float64
	fmt.Sscanf(wkt, "BOX(%f %f, %f %f)", &minX, &minY, &maxX, &maxY)

	return spatial.BoundingBox{
		Min: spatial.Point3D{X: minX, Y: minY, Z: 0},
		Max: spatial.Point3D{X: maxX, Y: maxY, Z: 0},
	}
}