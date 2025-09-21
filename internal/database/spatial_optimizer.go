package database

import (
	"context"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/dgraph-io/ristretto"
	"github.com/lib/pq"
)

// SpatialOptimizer provides optimized spatial query operations
type SpatialOptimizer struct {
	db              *PostGISDB
	cache           *QueryCache
	bulkOps         *BulkSpatialOps
	streamManager   *SpatialStreamManager
	indexManager    *SpatialIndexManager
	prefetcher      *PredictivePrefetcher
	metricsCollector *MetricsCollector
	mu              sync.RWMutex
}

// NewSpatialOptimizer creates a new spatial optimizer
func NewSpatialOptimizer(db *PostGISDB) (*SpatialOptimizer, error) {
	cache, err := NewQueryCache(100*1024*1024, 5*time.Minute) // 100MB cache, 5 min TTL
	if err != nil {
		return nil, fmt.Errorf("failed to create query cache: %w", err)
	}

	return &SpatialOptimizer{
		db:               db,
		cache:            cache,
		bulkOps:          NewBulkSpatialOps(db),
		streamManager:    NewSpatialStreamManager(db),
		indexManager:     NewSpatialIndexManager(db),
		prefetcher:       NewPredictivePrefetcher(cache),
		metricsCollector: NewMetricsCollector(),
	}, nil
}

// QueryCache implements an efficient query result cache
type QueryCache struct {
	cache       *ristretto.Cache
	ttl         time.Duration
	mu          sync.RWMutex
	hits        int64
	misses      int64
	evictions   int64
}

// NewQueryCache creates a new query cache
func NewQueryCache(maxSize int64, ttl time.Duration) (*QueryCache, error) {
	cache, err := ristretto.NewCache(&ristretto.Config{
		NumCounters: maxSize / 10,
		MaxCost:     maxSize,
		BufferItems: 64,
		OnEvict: func(item *ristretto.Item) {
			// Track evictions for metrics
		},
	})
	if err != nil {
		return nil, err
	}

	return &QueryCache{
		cache: cache,
		ttl:   ttl,
	}, nil
}

// Get retrieves a cached query result
func (qc *QueryCache) Get(query string, args ...interface{}) (interface{}, bool) {
	key := qc.generateKey(query, args...)

	qc.mu.Lock()
	defer qc.mu.Unlock()

	if value, found := qc.cache.Get(key); found {
		qc.hits++
		logger.Debug("Cache hit for query: %s", key[:16])
		return value, true
	}

	qc.misses++
	return nil, false
}

// Set stores a query result in cache
func (qc *QueryCache) Set(query string, result interface{}, cost int64, args ...interface{}) {
	key := qc.generateKey(query, args...)

	qc.cache.SetWithTTL(key, result, cost, qc.ttl)
	qc.cache.Wait() // Ensure the value is processed

	logger.Debug("Cached query result: %s (cost: %d)", key[:16], cost)
}

// generateKey creates a cache key from query and arguments
func (qc *QueryCache) generateKey(query string, args ...interface{}) string {
	h := md5.New()
	h.Write([]byte(query))
	for _, arg := range args {
		h.Write([]byte(fmt.Sprintf("%v", arg)))
	}
	return hex.EncodeToString(h.Sum(nil))
}

// GetMetrics returns cache metrics
func (qc *QueryCache) GetMetrics() CacheMetrics {
	qc.mu.RLock()
	defer qc.mu.RUnlock()

	hitRate := float64(0)
	if total := qc.hits + qc.misses; total > 0 {
		hitRate = float64(qc.hits) / float64(total) * 100
	}

	return CacheMetrics{
		Hits:      qc.hits,
		Misses:    qc.misses,
		Evictions: qc.evictions,
		HitRate:   hitRate,
	}
}

// CacheMetrics contains cache performance metrics
type CacheMetrics struct {
	Hits      int64
	Misses    int64
	Evictions int64
	HitRate   float64
}

// BulkSpatialOps handles bulk spatial operations
type BulkSpatialOps struct {
	db        *PostGISDB
	batchSize int
}

// NewBulkSpatialOps creates a new bulk operations handler
func NewBulkSpatialOps(db *PostGISDB) *BulkSpatialOps {
	return &BulkSpatialOps{
		db:        db,
		batchSize: 1000,
	}
}

// BulkProximitySearch performs proximity searches for multiple centers
func (b *BulkSpatialOps) BulkProximitySearch(ctx context.Context, centers []spatial.Point3D, radius float64) (map[string][]string, error) {
	if len(centers) == 0 {
		return nil, nil
	}

	// Build single query for multiple centers
	query := `
		WITH centers AS (
			SELECT
				row_number() OVER () as center_id,
				ST_SetSRID(ST_MakePoint($1, $2, $3), 4326) as point
			FROM (VALUES ` + b.buildCenterValues(centers) + `) as t(x, y, z)
		)
		SELECT
			c.center_id,
			e.equipment_id
		FROM centers c
		CROSS JOIN LATERAL (
			SELECT equipment_id
			FROM equipment_positions ep
			WHERE ST_DWithin(
				ep.position,
				c.point,
				$4
			)
			ORDER BY ST_Distance(ep.position, c.point)
			LIMIT 100
		) e
	`

	// Execute bulk query
	args := make([]interface{}, 0, len(centers)*3+1)
	for _, center := range centers {
		args = append(args, center.X, center.Y, center.Z)
	}
	args = append(args, radius)

	rows, err := b.db.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("bulk proximity search failed: %w", err)
	}
	defer rows.Close()

	// Organize results by center
	results := make(map[string][]string)
	for rows.Next() {
		var centerID int
		var equipmentID string
		if err := rows.Scan(&centerID, &equipmentID); err != nil {
			continue
		}

		key := fmt.Sprintf("center_%d", centerID)
		results[key] = append(results[key], equipmentID)
	}

	return results, nil
}

// buildCenterValues builds VALUES clause for centers
func (b *BulkSpatialOps) buildCenterValues(centers []spatial.Point3D) string {
	values := make([]string, len(centers))
	for i := range centers {
		values[i] = fmt.Sprintf("($%d, $%d, $%d)", i*3+1, i*3+2, i*3+3)
	}
	return strings.Join(values, ", ")
}

// BulkUpdatePositions updates multiple equipment positions in a single transaction
func (b *BulkSpatialOps) BulkUpdatePositions(ctx context.Context, updates []PositionUpdate) error {
	if len(updates) == 0 {
		return nil
	}

	tx, err := b.db.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Prepare statement for bulk updates
	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO equipment_positions (equipment_id, position, confidence, source, updated_at)
		VALUES ($1, ST_SetSRID(ST_MakePoint($2, $3, $4), 4326), $5, $6, $7)
		ON CONFLICT (equipment_id) DO UPDATE
		SET position = EXCLUDED.position,
		    confidence = EXCLUDED.confidence,
		    source = EXCLUDED.source,
		    updated_at = EXCLUDED.updated_at
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	// Execute updates in batches
	for i := 0; i < len(updates); i += b.batchSize {
		end := i + b.batchSize
		if end > len(updates) {
			end = len(updates)
		}

		for _, update := range updates[i:end] {
			_, err := stmt.ExecContext(ctx,
				update.EquipmentID,
				update.Position.X,
				update.Position.Y,
				update.Position.Z,
				update.Confidence,
				update.Source,
				time.Now(),
			)
			if err != nil {
				return fmt.Errorf("failed to update position for %s: %w", update.EquipmentID, err)
			}
		}
	}

	return tx.Commit()
}

// PositionUpdate represents a position update
type PositionUpdate struct {
	EquipmentID string
	Position    spatial.Point3D
	Confidence  spatial.ConfidenceLevel
	Source      string
}

// SpatialStreamManager manages real-time spatial data streams
type SpatialStreamManager struct {
	db         *PostGISDB
	listeners  map[string]*SpatialListener
	mu         sync.RWMutex
}

// NewSpatialStreamManager creates a new stream manager
func NewSpatialStreamManager(db *PostGISDB) *SpatialStreamManager {
	return &SpatialStreamManager{
		db:        db,
		listeners: make(map[string]*SpatialListener),
	}
}

// SpatialListener represents a spatial change listener
type SpatialListener struct {
	ID       string
	Channel  string
	Events   chan SpatialEvent
	Filters  []SpatialFilter
	listener *pq.Listener
	done     chan bool
}

// SpatialEvent represents a spatial change event
type SpatialEvent struct {
	Type      string          `json:"type"`
	Equipment string          `json:"equipment_id"`
	Position  spatial.Point3D `json:"position"`
	Timestamp time.Time       `json:"timestamp"`
	Source    string          `json:"source"`
}

// SpatialFilter defines filtering criteria for spatial events
type SpatialFilter struct {
	Type   string
	Center *spatial.Point3D
	Radius float64
	BBox   *spatial.BoundingBox
}

// StreamProximityChanges creates a stream for proximity-based changes
func (s *SpatialStreamManager) StreamProximityChanges(center spatial.Point3D, radius float64) (<-chan SpatialEvent, func(), error) {
	listenerID := fmt.Sprintf("proximity_%s", generateID())
	events := make(chan SpatialEvent, 100)
	done := make(chan bool)

	// Create PostgreSQL LISTEN connection
	connStr := s.db.GetConnectionString()
	listener := pq.NewListener(connStr, 10*time.Second, time.Minute, func(ev pq.ListenerEventType, err error) {
		if err != nil {
			logger.Error("Listener error: %v", err)
		}
	})

	// Start listening
	if err := listener.Listen("spatial_changes"); err != nil {
		return nil, nil, fmt.Errorf("failed to start listener: %w", err)
	}

	spatialListener := &SpatialListener{
		ID:       listenerID,
		Channel:  "spatial_changes",
		Events:   events,
		listener: listener,
		done:     done,
		Filters: []SpatialFilter{
			{
				Type:   "proximity",
				Center: &center,
				Radius: radius,
			},
		},
	}

	s.mu.Lock()
	s.listeners[listenerID] = spatialListener
	s.mu.Unlock()

	// Start event processor
	go s.processEvents(spatialListener)

	// Return cleanup function
	cleanup := func() {
		close(done)
		listener.Close()
		s.mu.Lock()
		delete(s.listeners, listenerID)
		s.mu.Unlock()
		close(events)
	}

	return events, cleanup, nil
}

// processEvents processes incoming spatial events
func (s *SpatialStreamManager) processEvents(listener *SpatialListener) {
	for {
		select {
		case <-listener.done:
			return
		case notification := <-listener.listener.Notify:
			if notification == nil {
				continue
			}

			var event SpatialEvent
			if err := json.Unmarshal([]byte(notification.Extra), &event); err != nil {
				logger.Warn("Failed to unmarshal spatial event: %v", err)
				continue
			}

			// Apply filters
			if s.matchesFilters(event, listener.Filters) {
				select {
				case listener.Events <- event:
				default:
					logger.Warn("Event channel full, dropping event")
				}
			}
		case <-time.After(time.Minute):
			// Ping to keep connection alive
			if err := listener.listener.Ping(); err != nil {
				logger.Error("Failed to ping listener: %v", err)
				return
			}
		}
	}
}

// matchesFilters checks if event matches any filter
func (s *SpatialStreamManager) matchesFilters(event SpatialEvent, filters []SpatialFilter) bool {
	if len(filters) == 0 {
		return true
	}

	for _, filter := range filters {
		switch filter.Type {
		case "proximity":
			if filter.Center != nil {
				distance := spatial.Distance(*filter.Center, event.Position)
				if distance <= filter.Radius {
					return true
				}
			}
		case "bbox":
			if filter.BBox != nil {
				if filter.BBox.Contains(event.Position) {
					return true
				}
			}
		default:
			return true
		}
	}

	return false
}

// SpatialIndexManager manages spatial indices
type SpatialIndexManager struct {
	db *PostGISDB
}

// NewSpatialIndexManager creates a new index manager
func NewSpatialIndexManager(db *PostGISDB) *SpatialIndexManager {
	return &SpatialIndexManager{db: db}
}

// CreateOptimizedIndices creates optimized spatial indices
func (m *SpatialIndexManager) CreateOptimizedIndices(ctx context.Context) error {
	indices := []string{
		// Multi-resolution spatial indices
		`CREATE INDEX IF NOT EXISTS idx_equipment_position_coarse
		 ON equipment_positions USING GIST (ST_SnapToGrid(position, 10.0))`,

		`CREATE INDEX IF NOT EXISTS idx_equipment_position_medium
		 ON equipment_positions USING GIST (ST_SnapToGrid(position, 1.0))`,

		`CREATE INDEX IF NOT EXISTS idx_equipment_position_fine
		 ON equipment_positions USING GIST (ST_SnapToGrid(position, 0.1))`,

		// Partial indices for equipment types
		`CREATE INDEX IF NOT EXISTS idx_hvac_equipment
		 ON equipment_positions USING GIST (position)
		 WHERE equipment_id IN (SELECT id FROM equipment WHERE type = 'hvac')`,

		`CREATE INDEX IF NOT EXISTS idx_electrical_equipment
		 ON equipment_positions USING GIST (position)
		 WHERE equipment_id IN (SELECT id FROM equipment WHERE type = 'electrical')`,

		// Covering index for common queries
		`CREATE INDEX IF NOT EXISTS idx_equipment_covering
		 ON equipment_positions USING GIST (position)
		 INCLUDE (confidence, source, updated_at)`,

		// 3D index for Z-axis queries
		`CREATE INDEX IF NOT EXISTS idx_equipment_position_3d
		 ON equipment_positions USING GIST (position gist_geometry_ops_nd)`,

		// Time-based partial index for recent data
		`CREATE INDEX IF NOT EXISTS idx_recent_positions
		 ON equipment_positions USING GIST (position)
		 WHERE updated_at > NOW() - INTERVAL '7 days'`,
	}

	for _, index := range indices {
		if _, err := m.db.db.ExecContext(ctx, index); err != nil {
			logger.Warn("Failed to create index: %v", err)
			// Continue with other indices
		}
	}

	// Cluster table for better performance
	if _, err := m.db.db.ExecContext(ctx,
		`CLUSTER equipment_positions USING idx_equipment_position_medium`); err != nil {
		logger.Warn("Failed to cluster table: %v", err)
	}

	// Update statistics
	if _, err := m.db.db.ExecContext(ctx, `ANALYZE equipment_positions`); err != nil {
		logger.Warn("Failed to analyze table: %v", err)
	}

	return nil
}

// PredictivePrefetcher implements predictive query prefetching
type PredictivePrefetcher struct {
	cache         *QueryCache
	patterns      map[string]*QueryPattern
	mu            sync.RWMutex
}

// QueryPattern represents a query access pattern
type QueryPattern struct {
	Query     string
	Frequency int
	LastSeen  time.Time
	Related   []string
}

// NewPredictivePrefetcher creates a new prefetcher
func NewPredictivePrefetcher(cache *QueryCache) *PredictivePrefetcher {
	return &PredictivePrefetcher{
		cache:    cache,
		patterns: make(map[string]*QueryPattern),
	}
}

// RecordAccess records a query access for pattern learning
func (p *PredictivePrefetcher) RecordAccess(query string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	pattern, exists := p.patterns[query]
	if !exists {
		pattern = &QueryPattern{
			Query:    query,
			Related:  make([]string, 0),
		}
		p.patterns[query] = pattern
	}

	pattern.Frequency++
	pattern.LastSeen = time.Now()
}

// PrefetchRelated prefetches related queries based on patterns
func (p *PredictivePrefetcher) PrefetchRelated(ctx context.Context, query string, executor QueryExecutor) {
	p.mu.RLock()
	pattern, exists := p.patterns[query]
	p.mu.RUnlock()

	if !exists || len(pattern.Related) == 0 {
		return
	}

	// Prefetch related queries in background
	go func() {
		for _, relatedQuery := range pattern.Related {
			if _, cached := p.cache.Get(relatedQuery); !cached {
				// Execute and cache the query
				if result, err := executor.Execute(ctx, relatedQuery); err == nil {
					p.cache.Set(relatedQuery, result, 1000)
				}
			}
		}
	}()
}

// QueryExecutor interface for executing queries
type QueryExecutor interface {
	Execute(ctx context.Context, query string, args ...interface{}) (interface{}, error)
}

// MetricsCollector collects performance metrics
type MetricsCollector struct {
	metrics map[string]*QueryMetrics
	mu      sync.RWMutex
}

// QueryMetrics contains query performance metrics
type QueryMetrics struct {
	Count        int64
	TotalTime    time.Duration
	MinTime      time.Duration
	MaxTime      time.Duration
	AvgTime      time.Duration
	LastExecuted time.Time
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		metrics: make(map[string]*QueryMetrics),
	}
}

// RecordQuery records query execution metrics
func (m *MetricsCollector) RecordQuery(query string, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	metric, exists := m.metrics[query]
	if !exists {
		metric = &QueryMetrics{
			MinTime: duration,
			MaxTime: duration,
		}
		m.metrics[query] = metric
	}

	metric.Count++
	metric.TotalTime += duration
	metric.AvgTime = metric.TotalTime / time.Duration(metric.Count)
	metric.LastExecuted = time.Now()

	if duration < metric.MinTime {
		metric.MinTime = duration
	}
	if duration > metric.MaxTime {
		metric.MaxTime = duration
	}
}

// GetMetrics returns collected metrics
func (m *MetricsCollector) GetMetrics() map[string]*QueryMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// Return a copy to avoid race conditions
	copy := make(map[string]*QueryMetrics)
	for k, v := range m.metrics {
		metricCopy := *v
		copy[k] = &metricCopy
	}

	return copy
}

// Helper functions

func generateID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}

func (p *PostGISDB) GetConnectionString() string {
	if p.connStr != "" {
		return p.connStr
	}
	return fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		p.config.Host, p.config.Port, p.config.User,
		p.config.Password, p.config.Database, p.config.SSLMode,
	)
}