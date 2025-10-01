// Package metrics provides Prometheus metrics collection for the API layer
package metrics

import (
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Collector holds all Prometheus metrics for the ArxOS API
type Collector struct {
	// HTTP Request Metrics
	requestsTotal   *prometheus.CounterVec
	requestDuration *prometheus.HistogramVec
	requestSize     *prometheus.HistogramVec
	responseSize    *prometheus.HistogramVec
	activeRequests  prometheus.Gauge

	// API Operation Metrics
	buildingOps     *prometheus.CounterVec
	equipmentOps    *prometheus.CounterVec
	spatialQueries  *prometheus.CounterVec
	userOps         *prometheus.CounterVec
	organizationOps *prometheus.CounterVec

	// Database Metrics
	dbQueriesTotal      *prometheus.CounterVec
	dbQueryDuration     *prometheus.HistogramVec
	dbConnectionsActive prometheus.Gauge
	dbConnectionsIdle   prometheus.Gauge
	dbErrors            *prometheus.CounterVec

	// Cache Metrics
	cacheHits              *prometheus.CounterVec
	cacheMisses            *prometheus.CounterVec
	cacheOperationDuration *prometheus.HistogramVec
	cacheSize              prometheus.Gauge

	// Authentication Metrics
	authAttempts   *prometheus.CounterVec
	tokenRefreshes prometheus.Counter
	activeSessions prometheus.Gauge
	failedLogins   prometheus.Counter

	// Error Metrics
	errorsTotal *prometheus.CounterVec

	// Business Metrics
	activeUsers         prometheus.Gauge
	activeOrganizations prometheus.Gauge
	totalBuildings      prometheus.Gauge
	totalEquipment      prometheus.Gauge

	// Sync Metrics
	syncOperations *prometheus.CounterVec
	syncDuration   *prometheus.HistogramVec
	syncQueueSize  prometheus.Gauge

	// Workflow Metrics
	workflowExecutions *prometheus.CounterVec
	workflowDuration   *prometheus.HistogramVec
	activeWorkflows    prometheus.Gauge
}

// NewCollector creates a new Prometheus metrics collector
func NewCollector() *Collector {
	return &Collector{
		// HTTP Request Metrics
		requestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "requests_total",
				Help:      "Total number of API requests by method, path, and status",
			},
			[]string{"method", "path", "status"},
		),
		requestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "request_duration_seconds",
				Help:      "API request duration in seconds",
				Buckets:   []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
			},
			[]string{"method", "path"},
		),
		requestSize: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "request_size_bytes",
				Help:      "API request body size in bytes",
				Buckets:   prometheus.ExponentialBuckets(100, 10, 7),
			},
			[]string{"method", "path"},
		),
		responseSize: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "response_size_bytes",
				Help:      "API response body size in bytes",
				Buckets:   prometheus.ExponentialBuckets(100, 10, 7),
			},
			[]string{"method", "path", "status"},
		),
		activeRequests: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "active_requests",
				Help:      "Number of currently active requests",
			},
		),

		// API Operation Metrics
		buildingOps: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "building_operations_total",
				Help:      "Total number of building operations",
			},
			[]string{"operation", "result"},
		),
		equipmentOps: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "equipment_operations_total",
				Help:      "Total number of equipment operations",
			},
			[]string{"operation", "result"},
		),
		spatialQueries: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "spatial_queries_total",
				Help:      "Total number of spatial queries",
			},
			[]string{"query_type", "result"},
		),
		userOps: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "user_operations_total",
				Help:      "Total number of user operations",
			},
			[]string{"operation", "result"},
		),
		organizationOps: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "organization_operations_total",
				Help:      "Total number of organization operations",
			},
			[]string{"operation", "result"},
		),

		// Database Metrics
		dbQueriesTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "db",
				Name:      "queries_total",
				Help:      "Total number of database queries",
			},
			[]string{"operation", "table", "result"},
		),
		dbQueryDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "db",
				Name:      "query_duration_seconds",
				Help:      "Database query duration in seconds",
				Buckets:   []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5},
			},
			[]string{"operation", "table"},
		),
		dbConnectionsActive: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "db",
				Name:      "connections_active",
				Help:      "Number of active database connections",
			},
		),
		dbConnectionsIdle: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "db",
				Name:      "connections_idle",
				Help:      "Number of idle database connections",
			},
		),
		dbErrors: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "db",
				Name:      "errors_total",
				Help:      "Total number of database errors",
			},
			[]string{"operation", "error_type"},
		),

		// Cache Metrics
		cacheHits: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "cache",
				Name:      "hits_total",
				Help:      "Total number of cache hits",
			},
			[]string{"cache_type"},
		),
		cacheMisses: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "cache",
				Name:      "misses_total",
				Help:      "Total number of cache misses",
			},
			[]string{"cache_type"},
		),
		cacheOperationDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "cache",
				Name:      "operation_duration_seconds",
				Help:      "Cache operation duration in seconds",
				Buckets:   []float64{.0001, .0005, .001, .005, .01, .025, .05},
			},
			[]string{"operation"},
		),
		cacheSize: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "cache",
				Name:      "size_bytes",
				Help:      "Current cache size in bytes",
			},
		),

		// Authentication Metrics
		authAttempts: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "auth",
				Name:      "attempts_total",
				Help:      "Total number of authentication attempts",
			},
			[]string{"method", "result"},
		),
		tokenRefreshes: promauto.NewCounter(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "auth",
				Name:      "token_refreshes_total",
				Help:      "Total number of token refreshes",
			},
		),
		activeSessions: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "auth",
				Name:      "active_sessions",
				Help:      "Number of active user sessions",
			},
		),
		failedLogins: promauto.NewCounter(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "auth",
				Name:      "failed_logins_total",
				Help:      "Total number of failed login attempts",
			},
		),

		// Error Metrics
		errorsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "api",
				Name:      "errors_total",
				Help:      "Total number of errors by type and component",
			},
			[]string{"error_type", "component", "severity"},
		),

		// Business Metrics
		activeUsers: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "business",
				Name:      "active_users",
				Help:      "Number of active users in the last 24 hours",
			},
		),
		activeOrganizations: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "business",
				Name:      "active_organizations",
				Help:      "Number of active organizations",
			},
		),
		totalBuildings: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "business",
				Name:      "total_buildings",
				Help:      "Total number of buildings in the system",
			},
		),
		totalEquipment: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "business",
				Name:      "total_equipment",
				Help:      "Total number of equipment items in the system",
			},
		),

		// Sync Metrics
		syncOperations: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "sync",
				Name:      "operations_total",
				Help:      "Total number of sync operations",
			},
			[]string{"operation", "result"},
		),
		syncDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "sync",
				Name:      "duration_seconds",
				Help:      "Sync operation duration in seconds",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"operation"},
		),
		syncQueueSize: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "sync",
				Name:      "queue_size",
				Help:      "Number of items in sync queue",
			},
		),

		// Workflow Metrics
		workflowExecutions: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: "arxos",
				Subsystem: "workflow",
				Name:      "executions_total",
				Help:      "Total number of workflow executions",
			},
			[]string{"workflow_id", "result"},
		),
		workflowDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: "arxos",
				Subsystem: "workflow",
				Name:      "duration_seconds",
				Help:      "Workflow execution duration in seconds",
				Buckets:   []float64{.1, .5, 1, 5, 10, 30, 60, 120, 300, 600},
			},
			[]string{"workflow_id"},
		),
		activeWorkflows: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: "arxos",
				Subsystem: "workflow",
				Name:      "active_executions",
				Help:      "Number of currently executing workflows",
			},
		),
	}
}

// HTTP Metrics Recording

// RecordRequest records an HTTP request with all relevant metrics
func (c *Collector) RecordRequest(method, path string, statusCode int, duration time.Duration, requestSize, responseSize int64) {
	status := strconv.Itoa(statusCode)

	c.requestsTotal.WithLabelValues(method, path, status).Inc()
	c.requestDuration.WithLabelValues(method, path).Observe(duration.Seconds())

	if requestSize > 0 {
		c.requestSize.WithLabelValues(method, path).Observe(float64(requestSize))
	}
	if responseSize > 0 {
		c.responseSize.WithLabelValues(method, path, status).Observe(float64(responseSize))
	}
}

// IncrementActiveRequests increments active request counter
func (c *Collector) IncrementActiveRequests() {
	c.activeRequests.Inc()
}

// DecrementActiveRequests decrements active request counter
func (c *Collector) DecrementActiveRequests() {
	c.activeRequests.Dec()
}

// API Operation Metrics

// RecordBuildingOp records a building operation
func (c *Collector) RecordBuildingOp(operation string, success bool) {
	result := resultLabel(success)
	c.buildingOps.WithLabelValues(operation, result).Inc()
}

// RecordEquipmentOp records an equipment operation
func (c *Collector) RecordEquipmentOp(operation string, success bool) {
	result := resultLabel(success)
	c.equipmentOps.WithLabelValues(operation, result).Inc()
}

// RecordSpatialQuery records a spatial query
func (c *Collector) RecordSpatialQuery(queryType string, success bool) {
	result := resultLabel(success)
	c.spatialQueries.WithLabelValues(queryType, result).Inc()
}

// RecordUserOp records a user operation
func (c *Collector) RecordUserOp(operation string, success bool) {
	result := resultLabel(success)
	c.userOps.WithLabelValues(operation, result).Inc()
}

// RecordOrganizationOp records an organization operation
func (c *Collector) RecordOrganizationOp(operation string, success bool) {
	result := resultLabel(success)
	c.organizationOps.WithLabelValues(operation, result).Inc()
}

// Database Metrics

// RecordDBQuery records a database query
func (c *Collector) RecordDBQuery(operation, table string, duration time.Duration, success bool) {
	result := resultLabel(success)
	c.dbQueriesTotal.WithLabelValues(operation, table, result).Inc()
	c.dbQueryDuration.WithLabelValues(operation, table).Observe(duration.Seconds())
}

// RecordDBError records a database error
func (c *Collector) RecordDBError(operation, errorType string) {
	c.dbErrors.WithLabelValues(operation, errorType).Inc()
}

// UpdateDBConnections updates database connection metrics
func (c *Collector) UpdateDBConnections(active, idle int) {
	c.dbConnectionsActive.Set(float64(active))
	c.dbConnectionsIdle.Set(float64(idle))
}

// Cache Metrics

// RecordCacheHit records a cache hit
func (c *Collector) RecordCacheHit(cacheType string) {
	c.cacheHits.WithLabelValues(cacheType).Inc()
}

// RecordCacheMiss records a cache miss
func (c *Collector) RecordCacheMiss(cacheType string) {
	c.cacheMisses.WithLabelValues(cacheType).Inc()
}

// RecordCacheOp records a cache operation
func (c *Collector) RecordCacheOp(operation string, duration time.Duration) {
	c.cacheOperationDuration.WithLabelValues(operation).Observe(duration.Seconds())
}

// UpdateCacheSize updates cache size metric
func (c *Collector) UpdateCacheSize(sizeBytes int64) {
	c.cacheSize.Set(float64(sizeBytes))
}

// Authentication Metrics

// RecordAuthAttempt records an authentication attempt
func (c *Collector) RecordAuthAttempt(method string, success bool) {
	result := resultLabel(success)
	c.authAttempts.WithLabelValues(method, result).Inc()

	if !success {
		c.failedLogins.Inc()
	}
}

// RecordTokenRefresh records a token refresh
func (c *Collector) RecordTokenRefresh() {
	c.tokenRefreshes.Inc()
}

// UpdateActiveSessions updates active session count
func (c *Collector) UpdateActiveSessions(count int) {
	c.activeSessions.Set(float64(count))
}

// Error Metrics

// RecordError records an error
func (c *Collector) RecordError(errorType, component, severity string) {
	c.errorsTotal.WithLabelValues(errorType, component, severity).Inc()
}

// Business Metrics

// UpdateBusinessMetrics updates business-level metrics
func (c *Collector) UpdateBusinessMetrics(activeUsers, activeOrgs, totalBuildings, totalEquipment int) {
	c.activeUsers.Set(float64(activeUsers))
	c.activeOrganizations.Set(float64(activeOrgs))
	c.totalBuildings.Set(float64(totalBuildings))
	c.totalEquipment.Set(float64(totalEquipment))
}

// Sync Metrics

// RecordSyncOp records a sync operation
func (c *Collector) RecordSyncOp(operation string, duration time.Duration, success bool) {
	result := resultLabel(success)
	c.syncOperations.WithLabelValues(operation, result).Inc()
	c.syncDuration.WithLabelValues(operation).Observe(duration.Seconds())
}

// UpdateSyncQueueSize updates sync queue size
func (c *Collector) UpdateSyncQueueSize(size int) {
	c.syncQueueSize.Set(float64(size))
}

// Workflow Metrics

// RecordWorkflowExecution records a workflow execution
func (c *Collector) RecordWorkflowExecution(workflowID string, duration time.Duration, success bool) {
	result := resultLabel(success)
	c.workflowExecutions.WithLabelValues(workflowID, result).Inc()
	c.workflowDuration.WithLabelValues(workflowID).Observe(duration.Seconds())
}

// UpdateActiveWorkflows updates active workflow count
func (c *Collector) UpdateActiveWorkflows(count int) {
	c.activeWorkflows.Set(float64(count))
}

// Helper function to convert boolean success to label
func resultLabel(success bool) string {
	if success {
		return "success"
	}
	return "error"
}

// Global collector instance
var globalCollector *Collector

// Initialize initializes the global metrics collector
func Initialize() *Collector {
	if globalCollector == nil {
		globalCollector = NewCollector()
	}
	return globalCollector
}

// Get returns the global metrics collector
func Get() *Collector {
	if globalCollector == nil {
		globalCollector = Initialize()
	}
	return globalCollector
}
