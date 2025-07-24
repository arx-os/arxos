package handlers

import (
	"net/http"
	"time"

	"arx/services/performance"
	"arx/utils"

	"github.com/go-chi/chi/v5"
)

// PerformanceHandler handles performance optimization endpoints
type PerformanceHandler struct {
	perfService *performance.PerformanceOptimizationService
}

// NewPerformanceHandler creates a new performance handler
func NewPerformanceHandler(perfService *performance.PerformanceOptimizationService) *PerformanceHandler {
	return &PerformanceHandler{
		perfService: perfService,
	}
}

// SetupRoutes sets up the performance optimization routes
func (h *PerformanceHandler) SetupRoutes(router chi.Router) {
	router.Route("/api/v1/performance", func(r chi.Router) {
		// Cache operations
		r.Post("/cache/init", utils.ToChiHandler(h.InitializeCache))
		r.Get("/cache/stats", utils.ToChiHandler(h.GetCacheStats))
		r.Post("/cache/clear", utils.ToChiHandler(h.ClearCache))
		r.Get("/cache/{key}", utils.ToChiHandler(h.GetFromCache))
		r.Post("/cache/{key}", utils.ToChiHandler(h.SetInCache))
		r.Delete("/cache/{key}", utils.ToChiHandler(h.DeleteFromCache))

		// Database optimization
		r.Post("/database/init", utils.ToChiHandler(h.InitializeDatabase))
		r.Post("/database/optimize", utils.ToChiHandler(h.OptimizeDatabase))
		r.Get("/database/stats", utils.ToChiHandler(h.GetDatabaseStats))
		r.Post("/database/query", utils.ToChiHandler(h.ExecuteOptimizedQuery))

		// Load balancer
		r.Post("/loadbalancer/init", utils.ToChiHandler(h.InitializeLoadBalancer))
		r.Post("/loadbalancer/server", utils.ToChiHandler(h.AddServer))
		r.Get("/loadbalancer/server", utils.ToChiHandler(h.GetNextServer))
		r.Get("/loadbalancer/stats", utils.ToChiHandler(h.GetLoadBalancerStats))
		r.Put("/loadbalancer/server/{server}/health", utils.ToChiHandler(h.UpdateServerHealth))

		// Performance monitoring
		r.Get("/metrics", utils.ToChiHandler(h.GetPerformanceMetrics))
		r.Get("/metrics/history", utils.ToChiHandler(h.GetMetricsHistory))
		r.Get("/alerts", utils.ToChiHandler(h.GetAlerts))
		r.Post("/alerts/thresholds", utils.ToChiHandler(h.UpdateAlertThresholds))

		// Optimization
		r.Post("/optimize", utils.ToChiHandler(h.OptimizePerformance))
		r.Get("/optimize/results", utils.ToChiHandler(h.GetOptimizationResults))
		r.Post("/optimize/auto", utils.ToChiHandler(h.AutoOptimize))

		// Reports
		r.Get("/report", utils.ToChiHandler(h.GetPerformanceReport))
		r.Get("/report/export", utils.ToChiHandler(h.ExportPerformanceReport))

		// Health checks
		r.Get("/health", utils.ToChiHandler(h.HealthCheck))
		r.Get("/health/detailed", utils.ToChiHandler(h.DetailedHealthCheck))
	})
}

// InitializeCacheRequest represents cache initialization request
type InitializeCacheRequest struct {
	CacheType     performance.CacheType `json:"cache_type" binding:"required"`
	TTL           int                   `json:"ttl"`
	MaxSize       int                   `json:"max_size"`
	Compression   bool                  `json:"compression"`
	Serialization string                `json:"serialization"`
	RedisURL      string                `json:"redis_url"`
	CDNURL        string                `json:"cdn_url"`
}

// InitializeCacheResponse represents cache initialization response
type InitializeCacheResponse struct {
	Message string                  `json:"message"`
	Config  performance.CacheConfig `json:"config"`
}

// InitializeCache initializes caching system
func (h *PerformanceHandler) InitializeCache(c *utils.ChiContext) {
	var req InitializeCacheRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	config := performance.CacheConfig{
		CacheType:     req.CacheType,
		TTL:           req.TTL,
		MaxSize:       req.MaxSize,
		Compression:   req.Compression,
		Serialization: req.Serialization,
		RedisURL:      req.RedisURL,
		CDNURL:        req.CDNURL,
	}

	h.perfService.InitializeCache(config)

	response := InitializeCacheResponse{
		Message: "Cache initialized successfully",
		Config:  config,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetCacheStatsResponse represents cache statistics response
type GetCacheStatsResponse struct {
	Stats   performance.CacheStats `json:"stats"`
	Message string                 `json:"message"`
}

// GetCacheStats retrieves cache statistics
func (h *PerformanceHandler) GetCacheStats(c *utils.ChiContext) {
	if h.perfService == nil || h.perfService.cache == nil {
		c.Writer.Error(http.StatusBadRequest, "Cache not initialized")
		return
	}

	stats := h.perfService.cache.GetStats()

	response := GetCacheStatsResponse{
		Stats:   stats,
		Message: "Cache statistics retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ClearCacheResponse represents cache clear response
type ClearCacheResponse struct {
	Message string `json:"message"`
}

// ClearCache clears the cache
func (h *PerformanceHandler) ClearCache(c *utils.ChiContext) {
	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Cache not initialized")
		return
	}

	if err := h.perfService.ClearCache(); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to clear cache", err.Error())
		return
	}

	response := ClearCacheResponse{
		Message: "Cache cleared successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetFromCacheRequest represents get from cache request
type GetFromCacheRequest struct {
	Key string `json:"key" binding:"required"`
}

// GetFromCacheResponse represents get from cache response
type GetFromCacheResponse struct {
	Value   interface{} `json:"value"`
	Message string      `json:"message"`
}

// GetFromCache retrieves a value from cache
func (h *PerformanceHandler) GetFromCache(c *utils.ChiContext) {
	key := c.Reader.Param("key")
	if key == "" {
		c.Writer.Error(http.StatusBadRequest, "Key is required")
		return
	}

	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Cache not initialized")
		return
	}

	value, err := h.perfService.GetFromCache(key)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Key not found", err.Error())
		return
	}

	response := GetFromCacheResponse{
		Value:   value,
		Message: "Value retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// SetInCacheRequest represents set in cache request
type SetInCacheRequest struct {
	Value interface{} `json:"value" binding:"required"`
	TTL   int         `json:"ttl"`
}

// SetInCacheResponse represents set in cache response
type SetInCacheResponse struct {
	Message string `json:"message"`
}

// SetInCache sets a value in cache
func (h *PerformanceHandler) SetInCache(c *utils.ChiContext) {
	key := c.Reader.Param("key")
	if key == "" {
		c.Writer.Error(http.StatusBadRequest, "Key is required")
		return
	}

	var req SetInCacheRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Cache not initialized")
		return
	}

	if err := h.perfService.SetInCache(key, req.Value, time.Duration(req.TTL)*time.Second); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to set value in cache", err.Error())
		return
	}

	response := SetInCacheResponse{
		Message: "Value set in cache successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// DeleteFromCacheResponse represents delete from cache response
type DeleteFromCacheResponse struct {
	Message string `json:"message"`
}

// DeleteFromCache deletes a value from cache
func (h *PerformanceHandler) DeleteFromCache(c *utils.ChiContext) {
	key := c.Reader.Param("key")
	if key == "" {
		c.Writer.Error(http.StatusBadRequest, "Key is required")
		return
	}

	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Cache not initialized")
		return
	}

	if err := h.perfService.DeleteFromCache(key); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to delete from cache", err.Error())
		return
	}

	response := DeleteFromCacheResponse{
		Message: "Value deleted from cache successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// InitializeDatabaseRequest represents database initialization request
type InitializeDatabaseRequest struct {
	ConnectionPoolSize      int  `json:"connection_pool_size"`
	MaxOverflow             int  `json:"max_overflow"`
	PoolTimeout             int  `json:"pool_timeout"`
	PoolRecycle             int  `json:"pool_recycle"`
	QueryTimeout            int  `json:"query_timeout"`
	EnableQueryCache        bool `json:"enable_query_cache"`
	EnableConnectionPooling bool `json:"enable_connection_pooling"`
}

// InitializeDatabaseResponse represents database initialization response
type InitializeDatabaseResponse struct {
	Message string                     `json:"message"`
	Config  performance.DatabaseConfig `json:"config"`
}

// InitializeDatabase initializes database optimization
func (h *PerformanceHandler) InitializeDatabase(c *utils.ChiContext) {
	var req InitializeDatabaseRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	config := performance.DatabaseConfig{
		ConnectionPoolSize:      req.ConnectionPoolSize,
		MaxOverflow:             req.MaxOverflow,
		PoolTimeout:             req.PoolTimeout,
		PoolRecycle:             req.PoolRecycle,
		QueryTimeout:            req.QueryTimeout,
		EnableQueryCache:        req.EnableQueryCache,
		EnableConnectionPooling: req.EnableConnectionPooling,
	}

	if err := h.perfService.InitializeDatabase(config); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to initialize database", err.Error())
		return
	}

	response := InitializeDatabaseResponse{
		Message: "Database initialized successfully",
		Config:  config,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// OptimizeDatabaseRequest represents database optimization request
type OptimizeDatabaseRequest struct {
	Query  string                 `json:"query" binding:"required"`
	Params map[string]interface{} `json:"params"`
}

// OptimizeDatabaseResponse represents database optimization response
type OptimizeDatabaseResponse struct {
	OptimizedQuery string `json:"optimized_query"`
	Message        string `json:"message"`
}

// OptimizeDatabase optimizes database queries
func (h *PerformanceHandler) OptimizeDatabase(c *utils.ChiContext) {
	var req OptimizeDatabaseRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Database optimizer not initialized")
		return
	}

	optimizedQuery, err := h.perfService.OptimizeQuery(req.Query, req.Params)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to optimize query", err.Error())
		return
	}

	response := OptimizeDatabaseResponse{
		OptimizedQuery: optimizedQuery,
		Message:        "Query optimized successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetDatabaseStatsResponse represents database statistics response
type GetDatabaseStatsResponse struct {
	Stats   performance.DatabaseStats `json:"stats"`
	Message string                    `json:"message"`
}

// GetDatabaseStats retrieves database statistics
func (h *PerformanceHandler) GetDatabaseStats(c *utils.ChiContext) {
	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Database optimizer not initialized")
		return
	}

	stats, err := h.perfService.GetDatabaseStats()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get database stats", err.Error())
		return
	}

	response := GetDatabaseStatsResponse{
		Stats:   *stats,
		Message: "Database statistics retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExecuteOptimizedQueryRequest represents execute optimized query request
type ExecuteOptimizedQueryRequest struct {
	Query  string                 `json:"query" binding:"required"`
	Params map[string]interface{} `json:"params"`
}

// ExecuteOptimizedQueryResponse represents execute optimized query response
type ExecuteOptimizedQueryResponse struct {
	Results []map[string]interface{} `json:"results"`
	Message string                   `json:"message"`
}

// ExecuteOptimizedQuery executes an optimized query
func (h *PerformanceHandler) ExecuteOptimizedQuery(c *utils.ChiContext) {
	var req ExecuteOptimizedQueryRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	if h.perfService == nil {
		c.Writer.Error(http.StatusBadRequest, "Database optimizer not initialized")
		return
	}

	results, err := h.perfService.ExecuteOptimizedQuery(req.Query, req.Params)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to execute query", err.Error())
		return
	}

	response := ExecuteOptimizedQueryResponse{
		Results: results,
		Message: "Query executed successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// InitializeLoadBalancerRequest represents load balancer initialization request
type InitializeLoadBalancerRequest struct {
	BalancerType        performance.LoadBalancerType `json:"balancer_type" binding:"required"`
	HealthCheckInterval int                          `json:"health_check_interval"`
	HealthCheckTimeout  int                          `json:"health_check_timeout"`
	MaxRetries          int                          `json:"max_retries"`
	SessionSticky       bool                         `json:"session_sticky"`
	WeightDistribution  map[string]int               `json:"weight_distribution"`
}

// InitializeLoadBalancerResponse represents load balancer initialization response
type InitializeLoadBalancerResponse struct {
	Message string                         `json:"message"`
	Config  performance.LoadBalancerConfig `json:"config"`
}

// InitializeLoadBalancer initializes load balancer
func (h *PerformanceHandler) InitializeLoadBalancer(c *utils.ChiContext) {
	var req InitializeLoadBalancerRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	config := performance.LoadBalancerConfig{
		BalancerType:        req.BalancerType,
		HealthCheckInterval: req.HealthCheckInterval,
		HealthCheckTimeout:  req.HealthCheckTimeout,
		MaxRetries:          req.MaxRetries,
		SessionSticky:       req.SessionSticky,
		WeightDistribution:  req.WeightDistribution,
	}

	if err := h.perfService.InitializeLoadBalancer(config); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to initialize load balancer", err.Error())
		return
	}

	response := InitializeLoadBalancerResponse{
		Message: "Load balancer initialized successfully",
		Config:  config,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// AddServerRequest represents add server request
type AddServerRequest struct {
	ServerURL string `json:"server_url" binding:"required"`
	Weight    int    `json:"weight"`
}

// AddServerResponse represents add server response
type AddServerResponse struct {
	Message string `json:"message"`
}

// AddServer adds a server to the load balancer
func (h *PerformanceHandler) AddServer(c *utils.ChiContext) {
	var req AddServerRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	if err := h.perfService.AddServer(req.ServerURL, req.Weight); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add server", err.Error())
		return
	}

	response := AddServerResponse{
		Message: "Server added successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetNextServerResponse represents get next server response
type GetNextServerResponse struct {
	ServerURL string `json:"server_url"`
	Message   string `json:"message"`
}

// GetNextServer gets the next server from load balancer
func (h *PerformanceHandler) GetNextServer(c *utils.ChiContext) {
	serverURL, err := h.perfService.GetNextServer()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get next server", err.Error())
		return
	}

	response := GetNextServerResponse{
		ServerURL: serverURL,
		Message:   "Next server retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetLoadBalancerStatsResponse represents load balancer statistics response
type GetLoadBalancerStatsResponse struct {
	Stats   performance.LoadBalancerStats `json:"stats"`
	Message string                        `json:"message"`
}

// GetLoadBalancerStats retrieves load balancer statistics
func (h *PerformanceHandler) GetLoadBalancerStats(c *utils.ChiContext) {
	stats, err := h.perfService.GetLoadBalancerStats()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get load balancer stats", err.Error())
		return
	}

	response := GetLoadBalancerStatsResponse{
		Stats:   *stats,
		Message: "Load balancer statistics retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// UpdateServerHealthRequest represents update server health request
type UpdateServerHealthRequest struct {
	Healthy bool `json:"healthy"`
}

// UpdateServerHealthResponse represents update server health response
type UpdateServerHealthResponse struct {
	Message string `json:"message"`
}

// UpdateServerHealth updates server health status
func (h *PerformanceHandler) UpdateServerHealth(c *utils.ChiContext) {
	server := c.Reader.Param("server")
	if server == "" {
		c.Writer.Error(http.StatusBadRequest, "Server parameter is required")
		return
	}

	var req UpdateServerHealthRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	if err := h.perfService.UpdateServerHealth(server, req.Healthy); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to update server health", err.Error())
		return
	}

	response := UpdateServerHealthResponse{
		Message: "Server health updated successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetPerformanceMetricsResponse represents performance metrics response
type GetPerformanceMetricsResponse struct {
	Metrics performance.PerformanceMetrics `json:"metrics"`
	Message string                         `json:"message"`
}

// GetPerformanceMetrics retrieves performance metrics
func (h *PerformanceHandler) GetPerformanceMetrics(c *utils.ChiContext) {
	metrics, err := h.perfService.GetPerformanceMetrics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get performance metrics", err.Error())
		return
	}

	response := GetPerformanceMetricsResponse{
		Metrics: *metrics,
		Message: "Performance metrics retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetMetricsHistoryResponse represents metrics history response
type GetMetricsHistoryResponse struct {
	History []performance.PerformanceMetrics `json:"history"`
	Message string                           `json:"message"`
}

// GetMetricsHistory retrieves metrics history
func (h *PerformanceHandler) GetMetricsHistory(c *utils.ChiContext) {
	history, err := h.perfService.GetMetricsHistory()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get metrics history", err.Error())
		return
	}

	response := GetMetricsHistoryResponse{
		History: history,
		Message: "Metrics history retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetAlertsResponse represents alerts response
type GetAlertsResponse struct {
	Alerts  []map[string]interface{} `json:"alerts"`
	Message string                   `json:"message"`
}

// GetAlerts retrieves performance alerts
func (h *PerformanceHandler) GetAlerts(c *utils.ChiContext) {
	alerts, err := h.perfService.GetAlerts()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get alerts", err.Error())
		return
	}

	response := GetAlertsResponse{
		Alerts:  alerts,
		Message: "Alerts retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// UpdateAlertThresholdsRequest represents update alert thresholds request
type UpdateAlertThresholdsRequest struct {
	Thresholds map[string]float64 `json:"thresholds" binding:"required"`
}

// UpdateAlertThresholdsResponse represents update alert thresholds response
type UpdateAlertThresholdsResponse struct {
	Message string `json:"message"`
}

// UpdateAlertThresholds updates alert thresholds
func (h *PerformanceHandler) UpdateAlertThresholds(c *utils.ChiContext) {
	var req UpdateAlertThresholdsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	if err := h.perfService.UpdateAlertThresholds(req.Thresholds); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to update alert thresholds", err.Error())
		return
	}

	response := UpdateAlertThresholdsResponse{
		Message: "Alert thresholds updated successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// OptimizePerformanceRequest represents optimize performance request
type OptimizePerformanceRequest struct {
	OptimizationType performance.OptimizationType `json:"optimization_type" binding:"required"`
}

// OptimizePerformanceResponse represents optimize performance response
type OptimizePerformanceResponse struct {
	Result  *performance.OptimizationResult `json:"result"`
	Message string                          `json:"message"`
}

// OptimizePerformance optimizes system performance
func (h *PerformanceHandler) OptimizePerformance(c *utils.ChiContext) {
	var req OptimizePerformanceRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	result, err := h.perfService.OptimizePerformance(req.OptimizationType)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to optimize performance", err.Error())
		return
	}

	response := OptimizePerformanceResponse{
		Result:  result,
		Message: "Performance optimized successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetOptimizationResultsResponse represents optimization results response
type GetOptimizationResultsResponse struct {
	Results []performance.OptimizationResult `json:"results"`
	Message string                           `json:"message"`
}

// GetOptimizationResults retrieves optimization results
func (h *PerformanceHandler) GetOptimizationResults(c *utils.ChiContext) {
	results, err := h.perfService.GetOptimizationResults()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get optimization results", err.Error())
		return
	}

	response := GetOptimizationResultsResponse{
		Results: results,
		Message: "Optimization results retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// AutoOptimizeRequest represents auto optimize request
type AutoOptimizeRequest struct {
	OptimizationTypes []performance.OptimizationType `json:"optimization_types"`
	MaxDuration       int                            `json:"max_duration"` // seconds
}

// AutoOptimizeResponse represents auto optimize response
type AutoOptimizeResponse struct {
	Results []*performance.OptimizationResult `json:"results"`
	Message string                            `json:"message"`
}

// AutoOptimize performs automatic optimization
func (h *PerformanceHandler) AutoOptimize(c *utils.ChiContext) {
	var req AutoOptimizeRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	results, err := h.perfService.AutoOptimize(req.OptimizationTypes, time.Duration(req.MaxDuration)*time.Second)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to auto optimize", err.Error())
		return
	}

	response := AutoOptimizeResponse{
		Results: results,
		Message: "Auto optimization completed successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetPerformanceReportResponse represents performance report response
type GetPerformanceReportResponse struct {
	Report  *performance.PerformanceReport `json:"report"`
	Message string                         `json:"message"`
}

// GetPerformanceReport retrieves performance report
func (h *PerformanceHandler) GetPerformanceReport(c *utils.ChiContext) {
	report, err := h.perfService.GetPerformanceReport()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get performance report", err.Error())
		return
	}

	response := GetPerformanceReportResponse{
		Report:  report,
		Message: "Performance report retrieved successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportPerformanceReportResponse represents export performance report response
type ExportPerformanceReportResponse struct {
	ReportData string `json:"report_data"`
	Message    string `json:"message"`
}

// ExportPerformanceReport exports performance report
func (h *PerformanceHandler) ExportPerformanceReport(c *utils.ChiContext) {
	reportData, err := h.perfService.ExportPerformanceReport()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to export performance report", err.Error())
		return
	}

	response := ExportPerformanceReportResponse{
		ReportData: reportData,
		Message:    "Performance report exported successfully",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// HealthCheckResponse represents health check response
type HealthCheckResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// HealthCheck performs health check
func (h *PerformanceHandler) HealthCheck(c *utils.ChiContext) {
	status, err := h.perfService.HealthCheck()
	if err != nil {
		c.Writer.Error(http.StatusServiceUnavailable, "Health check failed", err.Error())
		return
	}

	response := HealthCheckResponse{
		Status:  status,
		Message: "Health check completed",
	}

	c.Writer.JSON(http.StatusOK, response)
}

// DetailedHealthCheckResponse represents detailed health check response
type DetailedHealthCheckResponse struct {
	Status     string                 `json:"status"`
	Message    string                 `json:"message"`
	Components map[string]interface{} `json:"components"`
}

// DetailedHealthCheck performs detailed health check
func (h *PerformanceHandler) DetailedHealthCheck(c *utils.ChiContext) {
	status, components, err := h.perfService.DetailedHealthCheck()
	if err != nil {
		c.Writer.Error(http.StatusServiceUnavailable, "Detailed health check failed", err.Error())
		return
	}

	response := DetailedHealthCheckResponse{
		Status:     status,
		Message:    "Detailed health check completed",
		Components: components,
	}

	c.Writer.JSON(http.StatusOK, response)
}
