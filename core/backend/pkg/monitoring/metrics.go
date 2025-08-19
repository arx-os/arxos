package monitoring

import (
	"context"
	"fmt"
	"net/http"
	"runtime"
	"time"
	
	"arxos/pkg/logger"
)

// Metrics collector interface
type Metrics interface {
	RecordHTTPRequest(method, path string, statusCode int, duration time.Duration)
	RecordDatabaseQuery(operation string, duration time.Duration, err error)
	RecordTileRequest(zoom int, duration time.Duration, objectCount int)
	RecordPDFProcessing(duration time.Duration, objectCount int, err error)
	RecordWebSocketConnection(connected bool)
	RecordArxObjectCreation(objType, system string, confidence float32)
	RecordCacheHit(cacheType string, hit bool)
	GetStats() *Stats
}

// Stats represents system statistics
type Stats struct {
	Uptime           time.Duration              `json:"uptime"`
	HTTPRequests     map[string]*RequestStats   `json:"http_requests"`
	DatabaseQueries  map[string]*QueryStats     `json:"database_queries"`
	TileRequests     *TileStats                 `json:"tile_requests"`
	PDFProcessing    *ProcessingStats           `json:"pdf_processing"`
	WebSockets       *WebSocketStats            `json:"websockets"`
	ArxObjects       *ObjectStats               `json:"arx_objects"`
	Cache            map[string]*CacheStats     `json:"cache"`
	System           *SystemStats               `json:"system"`
}

// RequestStats tracks HTTP request metrics
type RequestStats struct {
	Count        int64         `json:"count"`
	TotalTime    time.Duration `json:"total_time_ms"`
	AverageTime  time.Duration `json:"average_time_ms"`
	MinTime      time.Duration `json:"min_time_ms"`
	MaxTime      time.Duration `json:"max_time_ms"`
	StatusCodes  map[int]int64 `json:"status_codes"`
}

// QueryStats tracks database query metrics
type QueryStats struct {
	Count       int64         `json:"count"`
	TotalTime   time.Duration `json:"total_time_ms"`
	AverageTime time.Duration `json:"average_time_ms"`
	Errors      int64         `json:"errors"`
}

// TileStats tracks tile service metrics
type TileStats struct {
	RequestCount    int64         `json:"request_count"`
	TotalObjects    int64         `json:"total_objects"`
	AverageObjects  float64       `json:"average_objects"`
	TotalTime       time.Duration `json:"total_time_ms"`
	AverageTime     time.Duration `json:"average_time_ms"`
	ZoomDistribution map[int]int64 `json:"zoom_distribution"`
}

// ProcessingStats tracks PDF processing metrics
type ProcessingStats struct {
	ProcessedCount  int64         `json:"processed_count"`
	TotalObjects    int64         `json:"total_objects"`
	AverageObjects  float64       `json:"average_objects"`
	TotalTime       time.Duration `json:"total_time_ms"`
	AverageTime     time.Duration `json:"average_time_ms"`
	Errors          int64         `json:"errors"`
}

// WebSocketStats tracks WebSocket metrics
type WebSocketStats struct {
	CurrentConnections int64 `json:"current_connections"`
	TotalConnections   int64 `json:"total_connections"`
	TotalMessages      int64 `json:"total_messages"`
}

// ObjectStats tracks ArxObject metrics
type ObjectStats struct {
	TotalCreated       int64            `json:"total_created"`
	TypeDistribution   map[string]int64 `json:"type_distribution"`
	SystemDistribution map[string]int64 `json:"system_distribution"`
	AverageConfidence  float64          `json:"average_confidence"`
	HighConfidence     int64            `json:"high_confidence"`
	MediumConfidence   int64            `json:"medium_confidence"`
	LowConfidence      int64            `json:"low_confidence"`
}

// CacheStats tracks cache metrics
type CacheStats struct {
	Hits       int64   `json:"hits"`
	Misses     int64   `json:"misses"`
	HitRate    float64 `json:"hit_rate"`
	Size       int64   `json:"size"`
	Evictions  int64   `json:"evictions"`
}

// SystemStats tracks system resource metrics
type SystemStats struct {
	GoRoutines     int     `json:"goroutines"`
	MemoryAlloc    uint64  `json:"memory_alloc_mb"`
	MemorySys      uint64  `json:"memory_sys_mb"`
	NumGC          uint32  `json:"num_gc"`
	CPUUsage       float64 `json:"cpu_usage_percent"`
}

// MetricsCollector implements the Metrics interface
type MetricsCollector struct {
	startTime        time.Time
	httpRequests     map[string]*RequestStats
	databaseQueries  map[string]*QueryStats
	tileStats        *TileStats
	pdfStats         *ProcessingStats
	wsStats          *WebSocketStats
	objectStats      *ObjectStats
	cacheStats       map[string]*CacheStats
	logger           logger.Logger
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector() Metrics {
	return &MetricsCollector{
		startTime:       time.Now(),
		httpRequests:    make(map[string]*RequestStats),
		databaseQueries: make(map[string]*QueryStats),
		tileStats: &TileStats{
			ZoomDistribution: make(map[int]int64),
		},
		pdfStats:    &ProcessingStats{},
		wsStats:     &WebSocketStats{},
		objectStats: &ObjectStats{
			TypeDistribution:   make(map[string]int64),
			SystemDistribution: make(map[string]int64),
		},
		cacheStats: make(map[string]*CacheStats),
		logger:     logger.GetLogger().WithField("component", "metrics"),
	}
}

// RecordHTTPRequest records an HTTP request metric
func (m *MetricsCollector) RecordHTTPRequest(method, path string, statusCode int, duration time.Duration) {
	key := fmt.Sprintf("%s %s", method, path)
	
	if _, exists := m.httpRequests[key]; !exists {
		m.httpRequests[key] = &RequestStats{
			StatusCodes: make(map[int]int64),
			MinTime:     duration,
		}
	}
	
	stats := m.httpRequests[key]
	stats.Count++
	stats.TotalTime += duration
	stats.AverageTime = stats.TotalTime / time.Duration(stats.Count)
	stats.StatusCodes[statusCode]++
	
	if duration < stats.MinTime {
		stats.MinTime = duration
	}
	if duration > stats.MaxTime {
		stats.MaxTime = duration
	}
}

// RecordDatabaseQuery records a database query metric
func (m *MetricsCollector) RecordDatabaseQuery(operation string, duration time.Duration, err error) {
	if _, exists := m.databaseQueries[operation]; !exists {
		m.databaseQueries[operation] = &QueryStats{}
	}
	
	stats := m.databaseQueries[operation]
	stats.Count++
	stats.TotalTime += duration
	stats.AverageTime = stats.TotalTime / time.Duration(stats.Count)
	
	if err != nil {
		stats.Errors++
	}
}

// RecordTileRequest records a tile request metric
func (m *MetricsCollector) RecordTileRequest(zoom int, duration time.Duration, objectCount int) {
	m.tileStats.RequestCount++
	m.tileStats.TotalObjects += int64(objectCount)
	m.tileStats.AverageObjects = float64(m.tileStats.TotalObjects) / float64(m.tileStats.RequestCount)
	m.tileStats.TotalTime += duration
	m.tileStats.AverageTime = m.tileStats.TotalTime / time.Duration(m.tileStats.RequestCount)
	m.tileStats.ZoomDistribution[zoom]++
}

// RecordPDFProcessing records PDF processing metrics
func (m *MetricsCollector) RecordPDFProcessing(duration time.Duration, objectCount int, err error) {
	m.pdfStats.ProcessedCount++
	m.pdfStats.TotalObjects += int64(objectCount)
	m.pdfStats.AverageObjects = float64(m.pdfStats.TotalObjects) / float64(m.pdfStats.ProcessedCount)
	m.pdfStats.TotalTime += duration
	m.pdfStats.AverageTime = m.pdfStats.TotalTime / time.Duration(m.pdfStats.ProcessedCount)
	
	if err != nil {
		m.pdfStats.Errors++
	}
}

// RecordWebSocketConnection records WebSocket connection changes
func (m *MetricsCollector) RecordWebSocketConnection(connected bool) {
	if connected {
		m.wsStats.CurrentConnections++
		m.wsStats.TotalConnections++
	} else {
		m.wsStats.CurrentConnections--
	}
}

// RecordArxObjectCreation records ArxObject creation
func (m *MetricsCollector) RecordArxObjectCreation(objType, system string, confidence float32) {
	m.objectStats.TotalCreated++
	m.objectStats.TypeDistribution[objType]++
	m.objectStats.SystemDistribution[system]++
	
	// Update confidence stats
	totalConf := m.objectStats.AverageConfidence * float64(m.objectStats.TotalCreated-1)
	m.objectStats.AverageConfidence = (totalConf + float64(confidence)) / float64(m.objectStats.TotalCreated)
	
	if confidence > 0.85 {
		m.objectStats.HighConfidence++
	} else if confidence >= 0.60 {
		m.objectStats.MediumConfidence++
	} else {
		m.objectStats.LowConfidence++
	}
}

// RecordCacheHit records cache hit/miss
func (m *MetricsCollector) RecordCacheHit(cacheType string, hit bool) {
	if _, exists := m.cacheStats[cacheType]; !exists {
		m.cacheStats[cacheType] = &CacheStats{}
	}
	
	stats := m.cacheStats[cacheType]
	if hit {
		stats.Hits++
	} else {
		stats.Misses++
	}
	
	total := stats.Hits + stats.Misses
	if total > 0 {
		stats.HitRate = float64(stats.Hits) / float64(total)
	}
}

// GetStats returns current statistics
func (m *MetricsCollector) GetStats() *Stats {
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	
	return &Stats{
		Uptime:          time.Since(m.startTime),
		HTTPRequests:    m.httpRequests,
		DatabaseQueries: m.databaseQueries,
		TileRequests:    m.tileStats,
		PDFProcessing:   m.pdfStats,
		WebSockets:      m.wsStats,
		ArxObjects:      m.objectStats,
		Cache:           m.cacheStats,
		System: &SystemStats{
			GoRoutines:  runtime.NumGoroutine(),
			MemoryAlloc: memStats.Alloc / 1024 / 1024,      // Convert to MB
			MemorySys:   memStats.Sys / 1024 / 1024,        // Convert to MB
			NumGC:       memStats.NumGC,
			CPUUsage:    0, // Would need more complex calculation
		},
	}
}

// HTTPMetricsMiddleware creates middleware for recording HTTP metrics
func HTTPMetricsMiddleware(metrics Metrics) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			
			// Wrap response writer to capture status code
			wrapped := &responseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
			}
			
			// Process request
			next.ServeHTTP(wrapped, r)
			
			// Record metric
			duration := time.Since(start)
			metrics.RecordHTTPRequest(r.Method, r.URL.Path, wrapped.statusCode, duration)
		})
	}
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// MetricsHandler returns an HTTP handler for metrics endpoint
func MetricsHandler(metrics Metrics) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		stats := metrics.GetStats()
		
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(stats); err != nil {
			http.Error(w, "Failed to encode metrics", http.StatusInternalServerError)
		}
	}
}

// StartMetricsServer starts a separate metrics server
func StartMetricsServer(port string, metrics Metrics) {
	mux := http.NewServeMux()
	mux.HandleFunc("/metrics", MetricsHandler(metrics))
	mux.HandleFunc("/health", HealthHandler())
	
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  120 * time.Second,
	}
	
	logger.GetLogger().Info("Starting metrics server",
		logger.String("port", port),
	)
	
	if err := server.ListenAndServe(); err != nil {
		logger.GetLogger().WithError(err).Fatal("Metrics server failed")
	}
}

// HealthHandler returns a health check handler
func HealthHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		health := map[string]interface{}{
			"status":    "healthy",
			"timestamp": time.Now().UTC(),
			"service":   "arxos",
		}
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(health)
	}
}