package handlers

import (
	"net/http"

	"arx/services/ai"
	"arx/utils"

	"github.com/go-chi/chi/v5"
)

// AIHandlers handles AI integration endpoints
type AIHandlers struct {
	aiService *ai.AIService
}

// NewAIHandlers creates a new AI handlers instance
func NewAIHandlers(aiService *ai.AIService) *AIHandlers {
	return &AIHandlers{
		aiService: aiService,
	}
}

// RegisterAIRoutes registers AI routes with the router
func (h *AIHandlers) RegisterAIRoutes(router chi.Router) {
	router.Route("/api/v1/ai", func(r chi.Router) {
		// User Pattern Learning
		r.Post("/user-actions", utils.ToChiHandler(h.RecordUserAction))
		r.Post("/user-patterns", utils.ToChiHandler(h.GetUserPatterns))
		r.Post("/user-recommendations", utils.ToChiHandler(h.GetUserRecommendations))
		r.Get("/user-analytics/{userID}", utils.ToChiHandler(h.GetUserAnalytics))

		// AI Frontend Integration
		r.Post("/htmx/process", utils.ToChiHandler(h.ProcessHTMXRequest))
		r.Get("/components/{componentID}", utils.ToChiHandler(h.GetAIComponent))

		// Advanced AI Analytics
		r.Post("/analytics/datasets", utils.ToChiHandler(h.CreateAnalyticsDataset))
		r.Post("/analytics/predict", utils.ToChiHandler(h.PredictUserBehavior))
		r.Post("/analytics/trends", utils.ToChiHandler(h.AnalyzeTrends))
		r.Post("/analytics/correlations", utils.ToChiHandler(h.AnalyzeCorrelations))
		r.Post("/analytics/anomalies", utils.ToChiHandler(h.DetectAnomalies))
		r.Post("/analytics/insights", utils.ToChiHandler(h.GenerateInsights))
		r.Post("/analytics/performance", utils.ToChiHandler(h.TrackPerformanceMetrics))

		// Recommendation Management
		r.Post("/recommendations/dismiss", utils.ToChiHandler(h.DismissRecommendation))
		r.Post("/recommendations/apply", utils.ToChiHandler(h.ApplyRecommendation))
	})
}

// User Pattern Learning Handlers

// RecordUserAction handles recording user actions
func (h *AIHandlers) RecordUserAction(c *utils.ChiContext) {
	var req ai.RecordUserActionRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}
	if req.SessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "session_id is required", "")
		return
	}
	if req.ActionType == "" {
		c.Writer.Error(http.StatusBadRequest, "action_type is required", "")
		return
	}
	if req.Resource == "" {
		c.Writer.Error(http.StatusBadRequest, "resource is required", "")
		return
	}

	userAction, err := h.aiService.RecordUserAction(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to record user action", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    userAction,
		"message": "User action recorded successfully",
	})
}

// GetUserPatterns handles retrieving user patterns
func (h *AIHandlers) GetUserPatterns(c *utils.ChiContext) {
	var req ai.GetUserPatternsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}

	// Set defaults
	if req.Limit <= 0 {
		req.Limit = 50
	}
	if req.Offset < 0 {
		req.Offset = 0
	}

	patterns, err := h.aiService.GetUserPatterns(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get user patterns", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    patterns,
		"count":   len(patterns),
		"message": "User patterns retrieved successfully",
	})
}

// GetUserRecommendations handles retrieving user recommendations
func (h *AIHandlers) GetUserRecommendations(c *utils.ChiContext) {
	var req ai.GetUserRecommendationsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}

	// Set defaults
	if req.Limit <= 0 {
		req.Limit = 20
	}
	if req.Offset < 0 {
		req.Offset = 0
	}

	recommendations, err := h.aiService.GetUserRecommendations(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get user recommendations", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    recommendations,
		"count":   len(recommendations),
		"message": "User recommendations retrieved successfully",
	})
}

// GetUserAnalytics handles retrieving user analytics
func (h *AIHandlers) GetUserAnalytics(c *utils.ChiContext) {
	userID := c.Reader.Param("userID")
	if userID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	analytics, err := h.aiService.GetUserAnalytics(userID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get user analytics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    analytics,
		"message": "User analytics retrieved successfully",
	})
}

// AI Frontend Integration Handlers

// ProcessHTMXRequest handles HTMX requests
func (h *AIHandlers) ProcessHTMXRequest(c *utils.ChiContext) {
	var req ai.ProcessHTMXRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.EventType == "" {
		c.Writer.Error(http.StatusBadRequest, "event_type is required", "")
		return
	}
	if req.Target == "" {
		c.Writer.Error(http.StatusBadRequest, "target is required", "")
		return
	}
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}
	if req.SessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "session_id is required", "")
		return
	}

	response, err := h.aiService.ProcessHTMXRequest(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to process HTMX request", err.Error())
		return
	}

	// Set custom headers if provided
	if response.Headers != nil {
		for key, value := range response.Headers {
			c.Writer.Header().Set(key, value)
		}
	}

	// Return appropriate status code
	statusCode := http.StatusOK
	if response.Status > 0 {
		statusCode = response.Status
	}

	c.Writer.JSON(statusCode, map[string]interface{}{
		"success": true,
		"data":    response,
		"message": "HTMX request processed successfully",
	})
}

// GetAIComponent handles retrieving AI components
func (h *AIHandlers) GetAIComponent(c *utils.ChiContext) {
	componentID := c.Reader.Param("componentID")
	if componentID == "" {
		c.Writer.Error(http.StatusBadRequest, "Component ID is required", "")
		return
	}

	component, err := h.aiService.GetAIComponent(componentID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get AI component", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    component,
		"message": "AI component retrieved successfully",
	})
}

// Advanced AI Analytics Handlers

// CreateAnalyticsDataset handles creating analytics datasets
func (h *AIHandlers) CreateAnalyticsDataset(c *utils.ChiContext) {
	var req ai.CreateAnalyticsDatasetRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.Name == "" {
		c.Writer.Error(http.StatusBadRequest, "name is required", "")
		return
	}
	if req.Type == "" {
		c.Writer.Error(http.StatusBadRequest, "type is required", "")
		return
	}
	if len(req.Data) == 0 {
		c.Writer.Error(http.StatusBadRequest, "data is required", "")
		return
	}

	dataset, err := h.aiService.CreateAnalyticsDataset(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create analytics dataset", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    dataset,
		"message": "Analytics dataset created successfully",
	})
}

// PredictUserBehavior handles predicting user behavior
func (h *AIHandlers) PredictUserBehavior(c *utils.ChiContext) {
	var req ai.PredictUserBehaviorRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}
	if req.ModelType == "" {
		c.Writer.Error(http.StatusBadRequest, "model_type is required", "")
		return
	}
	if len(req.Input) == 0 {
		c.Writer.Error(http.StatusBadRequest, "input is required", "")
		return
	}

	// Set defaults
	if req.Horizon <= 0 {
		req.Horizon = 7
	}

	prediction, err := h.aiService.PredictUserBehavior(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to predict user behavior", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    prediction,
		"message": "User behavior prediction completed successfully",
	})
}

// AnalyzeTrends handles analyzing trends
func (h *AIHandlers) AnalyzeTrends(c *utils.ChiContext) {
	var req ai.AnalyzeTrendsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.DatasetID == "" {
		c.Writer.Error(http.StatusBadRequest, "dataset_id is required", "")
		return
	}
	if req.Metric == "" {
		c.Writer.Error(http.StatusBadRequest, "metric is required", "")
		return
	}

	// Set defaults
	if req.Period == "" {
		req.Period = "daily"
	}
	if req.Confidence <= 0 {
		req.Confidence = 0.95
	}

	trends, err := h.aiService.AnalyzeTrends(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to analyze trends", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    trends,
		"message": "Trend analysis completed successfully",
	})
}

// AnalyzeCorrelations handles analyzing correlations
func (h *AIHandlers) AnalyzeCorrelations(c *utils.ChiContext) {
	var req ai.AnalyzeCorrelationsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.DatasetID == "" {
		c.Writer.Error(http.StatusBadRequest, "dataset_id is required", "")
		return
	}
	if req.Variable1 == "" {
		c.Writer.Error(http.StatusBadRequest, "variable1 is required", "")
		return
	}
	if req.Variable2 == "" {
		c.Writer.Error(http.StatusBadRequest, "variable2 is required", "")
		return
	}

	correlations, err := h.aiService.AnalyzeCorrelations(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to analyze correlations", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    correlations,
		"message": "Correlation analysis completed successfully",
	})
}

// DetectAnomalies handles detecting anomalies
func (h *AIHandlers) DetectAnomalies(c *utils.ChiContext) {
	var req ai.DetectAnomaliesRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.DatasetID == "" {
		c.Writer.Error(http.StatusBadRequest, "dataset_id is required", "")
		return
	}
	if req.Metric == "" {
		c.Writer.Error(http.StatusBadRequest, "metric is required", "")
		return
	}

	// Set defaults
	if req.Threshold <= 0 {
		req.Threshold = 2.0
	}
	if req.WindowSize <= 0 {
		req.WindowSize = 10
	}

	anomalies, err := h.aiService.DetectAnomalies(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to detect anomalies", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    anomalies,
		"message": "Anomaly detection completed successfully",
	})
}

// GenerateInsights handles generating insights
func (h *AIHandlers) GenerateInsights(c *utils.ChiContext) {
	var req ai.GenerateInsightsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}

	// Set defaults
	if req.Limit <= 0 {
		req.Limit = 10
	}
	if req.Confidence <= 0 {
		req.Confidence = 0.8
	}

	insights, err := h.aiService.GenerateInsights(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to generate insights", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    insights,
		"count":   len(insights),
		"message": "Insights generated successfully",
	})
}

// TrackPerformanceMetrics handles tracking performance metrics
func (h *AIHandlers) TrackPerformanceMetrics(c *utils.ChiContext) {
	var req ai.TrackPerformanceMetricsRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.Category == "" {
		c.Writer.Error(http.StatusBadRequest, "category is required", "")
		return
	}
	if req.Metric == "" {
		c.Writer.Error(http.StatusBadRequest, "metric is required", "")
		return
	}

	metrics, err := h.aiService.TrackPerformanceMetrics(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to track performance metrics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    metrics,
		"message": "Performance metrics tracked successfully",
	})
}

// Recommendation Management Handlers

// DismissRecommendation handles dismissing recommendations
func (h *AIHandlers) DismissRecommendation(c *utils.ChiContext) {
	var req ai.DismissRecommendationRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.RecommendationID == "" {
		c.Writer.Error(http.StatusBadRequest, "recommendation_id is required", "")
		return
	}
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}

	err := h.aiService.DismissRecommendation(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to dismiss recommendation", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Recommendation dismissed successfully",
	})
}

// ApplyRecommendation handles applying recommendations
func (h *AIHandlers) ApplyRecommendation(c *utils.ChiContext) {
	var req ai.ApplyRecommendationRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request body", err.Error())
		return
	}

	// Validate required fields
	if req.RecommendationID == "" {
		c.Writer.Error(http.StatusBadRequest, "recommendation_id is required", "")
		return
	}
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "user_id is required", "")
		return
	}

	err := h.aiService.ApplyRecommendation(req)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to apply recommendation", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Recommendation applied successfully",
	})
}
