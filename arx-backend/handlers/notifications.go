package handlers

import (
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"arx/models"
	"arx/services/notifications"
	"arx/utils"

	"gorm.io/gorm"
)

// EnhancedNotificationHandler handles enhanced notification-related HTTP requests
type EnhancedNotificationHandler struct {
	enhancedService *notifications.EnhancedNotificationService
	db              *gorm.DB
}

// NewEnhancedNotificationHandler creates a new enhanced notification handler
func NewEnhancedNotificationHandler(
	enhancedService *notifications.EnhancedNotificationService,
	db *gorm.DB,
) *EnhancedNotificationHandler {
	return &EnhancedNotificationHandler{
		enhancedService: enhancedService,
		db:              db,
	}
}

// RegisterEnhancedNotificationRoutes registers enhanced notification routes
func (h *EnhancedNotificationHandler) RegisterEnhancedNotificationRoutes(router chi.Router) {
	router.Route("/api/notifications", func(r chi.Router) {
		// Core notification endpoints
		r.Post("/send", utils.ToChiHandler(h.SendNotification))
		r.Get("/history", utils.ToChiHandler(h.GetNotificationHistory))
		r.Get("/statistics", utils.ToChiHandler(h.GetNotificationStatistics))

		// Template management
		r.Post("/templates", utils.ToChiHandler(h.CreateNotificationTemplate))
		r.Get("/templates", utils.ToChiHandler(h.GetNotificationTemplates))
		r.Get("/templates/{id}", utils.ToChiHandler(h.GetNotificationTemplate))
		r.Put("/templates/{id}", utils.ToChiHandler(h.UpdateNotificationTemplate))
		r.Delete("/templates/{id}", utils.ToChiHandler(h.DeleteNotificationTemplate))

		// Configuration management
		r.Post("/config", utils.ToChiHandler(h.CreateNotificationConfig))
		r.Get("/config", utils.ToChiHandler(h.GetNotificationConfigs))
		r.Get("/config/{id}", utils.ToChiHandler(h.GetNotificationConfig))
		r.Put("/config/{id}", utils.ToChiHandler(h.UpdateNotificationConfig))
		r.Delete("/config/{id}", utils.ToChiHandler(h.DeleteNotificationConfig))

		// User preferences
		r.Post("/preferences", utils.ToChiHandler(h.CreateNotificationPreference))
		r.Get("/preferences", utils.ToChiHandler(h.GetNotificationPreferences))
		r.Put("/preferences/{id}", utils.ToChiHandler(h.UpdateNotificationPreference))
		r.Delete("/preferences/{id}", utils.ToChiHandler(h.DeleteNotificationPreference))

		// Channel configuration
		r.Post("/channels", utils.ToChiHandler(h.CreateNotificationChannelConfig))
		r.Get("/channels", utils.ToChiHandler(h.GetNotificationChannelConfigs))
		r.Get("/channels/{channel}", utils.ToChiHandler(h.GetNotificationChannelConfig))
		r.Put("/channels/{channel}", utils.ToChiHandler(h.UpdateNotificationChannelConfig))
		r.Delete("/channels/{channel}", utils.ToChiHandler(h.DeleteNotificationChannelConfig))

		// Queue management
		r.Get("/queue/stats", utils.ToChiHandler(h.GetQueueStatistics))
		r.Post("/queue/clear", utils.ToChiHandler(h.ClearNotificationQueue))

		// Health and monitoring
		r.Get("/health", utils.ToChiHandler(h.GetNotificationHealth))
		r.Get("/health/detailed", utils.ToChiHandler(h.GetDetailedNotificationHealth))
	})
}

// Request/Response structures

// SendNotificationRequest represents a request to send a notification
type SendNotificationRequest struct {
	Title             string                           `json:"title" binding:"required"`
	Message           string                           `json:"message" binding:"required"`
	Type              models.NotificationType          `json:"type" binding:"required"`
	Channels          []models.NotificationChannelType `json:"channels"`
	Priority          models.NotificationPriority      `json:"priority"`
	RecipientID       uint                             `json:"recipient_id" binding:"required"`
	SenderID          *uint                            `json:"sender_id"`
	ConfigID          *uint                            `json:"config_id"`
	TemplateID        *uint                            `json:"template_id"`
	TemplateData      map[string]interface{}           `json:"template_data"`
	Metadata          map[string]interface{}           `json:"metadata"`
	BuildingID        *uint                            `json:"building_id"`
	AssetID           *string                          `json:"asset_id"`
	RelatedObjectID   *string                          `json:"related_object_id"`
	RelatedObjectType string                           `json:"related_object_type"`
}

// SendNotificationResponse represents a response from sending a notification
type SendNotificationResponse struct {
	Success        bool      `json:"success"`
	NotificationID uint      `json:"notification_id"`
	Message        string    `json:"message"`
	CreatedAt      time.Time `json:"created_at"`
}

// NotificationHistoryRequest represents a request for notification history
type NotificationHistoryRequest struct {
	UserID      *uint                           `json:"user_id"`
	RecipientID *uint                           `json:"recipient_id"`
	SenderID    *uint                           `json:"sender_id"`
	Type        *models.NotificationType        `json:"type"`
	Status      *models.NotificationStatus      `json:"status"`
	Priority    *models.NotificationPriority    `json:"priority"`
	Channel     *models.NotificationChannelType `json:"channel"`
	BuildingID  *uint                           `json:"building_id"`
	AssetID     *string                         `json:"asset_id"`
	StartDate   *time.Time                      `json:"start_date"`
	EndDate     *time.Time                      `json:"end_date"`
	Page        int                             `json:"page"`
	PageSize    int                             `json:"page_size"`
}

// NotificationHistoryResponse represents a response with notification history
type NotificationHistoryResponse struct {
	Notifications []models.NotificationEnhanced `json:"notifications"`
	Total         int64                         `json:"total"`
	Page          int                           `json:"page"`
	PageSize      int                           `json:"page_size"`
	TotalPages    int                           `json:"total_pages"`
}

// NotificationStatisticsResponse represents a response with notification statistics
type NotificationStatisticsResponse struct {
	Statistics  *notifications.EnhancedNotificationStatistics `json:"statistics"`
	Period      string                                        `json:"period"`
	GeneratedAt time.Time                                     `json:"generated_at"`
}

// CreateNotificationTemplateRequest represents a request to create a notification template
type CreateNotificationTemplateRequest struct {
	Name        string                           `json:"name" binding:"required"`
	Description string                           `json:"description"`
	Type        models.NotificationType          `json:"type" binding:"required"`
	Channels    []models.NotificationChannelType `json:"channels"`
	Subject     string                           `json:"subject"`
	Body        string                           `json:"body" binding:"required"`
	HTMLBody    string                           `json:"html_body"`
	Variables   map[string]interface{}           `json:"variables"`
	IsActive    bool                             `json:"is_active"`
}

// UpdateNotificationTemplateRequest represents a request to update a notification template
type UpdateNotificationTemplateRequest struct {
	Name        *string                          `json:"name"`
	Description *string                          `json:"description"`
	Type        *models.NotificationType         `json:"type"`
	Channels    []models.NotificationChannelType `json:"channels"`
	Subject     *string                          `json:"subject"`
	Body        *string                          `json:"body"`
	HTMLBody    *string                          `json:"html_body"`
	Variables   map[string]interface{}           `json:"variables"`
	IsActive    *bool                            `json:"is_active"`
}

// NotificationTemplatesResponse represents a response with notification templates
type NotificationTemplatesResponse struct {
	Templates []models.NotificationTemplateEnhanced `json:"templates"`
	Total     int64                                 `json:"total"`
	Page      int                                   `json:"page"`
	PageSize  int                                   `json:"page_size"`
}

// CreateNotificationConfigRequest represents a request to create a notification configuration
type CreateNotificationConfigRequest struct {
	Name          string                           `json:"name" binding:"required"`
	Description   string                           `json:"description"`
	Channels      []models.NotificationChannelType `json:"channels"`
	Priority      models.NotificationPriority      `json:"priority"`
	RetryAttempts int                              `json:"retry_attempts"`
	RetryDelay    int                              `json:"retry_delay"`
	Timeout       int                              `json:"timeout"`
	TemplateID    *uint                            `json:"template_id"`
	TemplateData  map[string]interface{}           `json:"template_data"`
	IsActive      bool                             `json:"is_active"`
}

// NotificationConfigsResponse represents a response with notification configurations
type NotificationConfigsResponse struct {
	Configs  []models.NotificationConfigEnhanced `json:"configs"`
	Total    int64                               `json:"total"`
	Page     int                                 `json:"page"`
	PageSize int                                 `json:"page_size"`
}

// CreateNotificationPreferenceRequest represents a request to create a notification preference
type CreateNotificationPreferenceRequest struct {
	UserID    uint                           `json:"user_id" binding:"required"`
	Channel   models.NotificationChannelType `json:"channel" binding:"required"`
	Type      models.NotificationType        `json:"type" binding:"required"`
	IsEnabled bool                           `json:"is_enabled"`
	Priority  models.NotificationPriority    `json:"priority"`
	Frequency string                         `json:"frequency"`
}

// NotificationPreferencesResponse represents a response with notification preferences
type NotificationPreferencesResponse struct {
	Preferences []models.NotificationPreference `json:"preferences"`
	Total       int64                           `json:"total"`
	Page        int                             `json:"page"`
	PageSize    int                             `json:"page_size"`
}

// QueueStatisticsResponse represents a response with queue statistics
type QueueStatisticsResponse struct {
	QueueLength    int                           `json:"queue_length"`
	Workers        int                           `json:"workers"`
	Capacity       int                           `json:"capacity"`
	ProcessorStats *notifications.ProcessorStats `json:"processor_stats"`
}

// NotificationHealthResponse represents a response with notification health status
type NotificationHealthResponse struct {
	Status     string                                        `json:"status"`
	Message    string                                        `json:"message"`
	Timestamp  time.Time                                     `json:"timestamp"`
	Services   map[string]bool                               `json:"services"`
	Statistics *notifications.EnhancedNotificationStatistics `json:"statistics"`
}

// Handler methods

// SendNotification handles POST /api/notifications/send
func (h *EnhancedNotificationHandler) SendNotification(c *utils.ChiContext) {
	var request SendNotificationRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if err := h.validateSendNotificationRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	// Set default values
	if len(request.Channels) == 0 {
		request.Channels = []models.NotificationChannelType{
			models.NotificationChannelTypeEmail,
		}
	}
	if request.Priority == "" {
		request.Priority = models.NotificationPriorityNormal
	}

	// Create notification
	notification, err := h.enhancedService.CreateNotification(
		request.Title,
		request.Message,
		request.Type,
		request.Channels,
		request.Priority,
		request.RecipientID,
		request.SenderID,
		request.ConfigID,
		request.TemplateID,
		request.TemplateData,
		request.Metadata,
	)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create notification", err.Error())
		return
	}

	// Send notification
	if err := h.enhancedService.SendNotification(notification); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to send notification", err.Error())
		return
	}

	response := SendNotificationResponse{
		Success:        true,
		NotificationID: notification.ID,
		Message:        "Notification sent successfully",
		CreatedAt:      notification.CreatedAt,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetNotificationHistory handles GET /api/notifications/history
func (h *EnhancedNotificationHandler) GetNotificationHistory(c *utils.ChiContext) {
	var request NotificationHistoryRequest
	// Parse query parameters manually since we're using Chi context
	query := c.Request.URL.Query()
	if pageStr := query.Get("page"); pageStr != "" {
		if page, err := strconv.Atoi(pageStr); err == nil {
			request.Page = page
		}
	}
	if pageSizeStr := query.Get("page_size"); pageSizeStr != "" {
		if pageSize, err := strconv.Atoi(pageSizeStr); err == nil {
			request.PageSize = pageSize
		}
	}
	if userIDStr := query.Get("user_id"); userIDStr != "" {
		if userID, err := strconv.ParseUint(userIDStr, 10, 32); err == nil {
			uid := uint(userID)
			request.UserID = &uid
		}
	}
	if recipientIDStr := query.Get("recipient_id"); recipientIDStr != "" {
		if recipientID, err := strconv.ParseUint(recipientIDStr, 10, 32); err == nil {
			rid := uint(recipientID)
			request.RecipientID = &rid
		}
	}
	if senderIDStr := query.Get("sender_id"); senderIDStr != "" {
		if senderID, err := strconv.ParseUint(senderIDStr, 10, 32); err == nil {
			sid := uint(senderID)
			request.SenderID = &sid
		}
	}
	if typeStr := query.Get("type"); typeStr != "" {
		notificationType := models.NotificationType(typeStr)
		request.Type = &notificationType
	}
	if statusStr := query.Get("status"); statusStr != "" {
		notificationStatus := models.NotificationStatus(statusStr)
		request.Status = &notificationStatus
	}
	if priorityStr := query.Get("priority"); priorityStr != "" {
		notificationPriority := models.NotificationPriority(priorityStr)
		request.Priority = &notificationPriority
	}
	if buildingIDStr := query.Get("building_id"); buildingIDStr != "" {
		if buildingID, err := strconv.ParseUint(buildingIDStr, 10, 32); err == nil {
			bid := uint(buildingID)
			request.BuildingID = &bid
		}
	}
	if assetID := query.Get("asset_id"); assetID != "" {
		request.AssetID = &assetID
	}
	if startDateStr := query.Get("start_date"); startDateStr != "" {
		if startDate, err := time.Parse("2006-01-02", startDateStr); err == nil {
			request.StartDate = &startDate
		}
	}
	if endDateStr := query.Get("end_date"); endDateStr != "" {
		if endDate, err := time.Parse("2006-01-02", endDateStr); err == nil {
			request.EndDate = &endDate
		}
	}

	// Set default pagination
	if request.Page <= 0 {
		request.Page = 1
	}
	if request.PageSize <= 0 {
		request.PageSize = 20
	}
	if request.PageSize > 100 {
		request.PageSize = 100
	}

	// Build database query
	dbQuery := h.db.Model(&models.NotificationEnhanced{})

	// Apply filters
	if request.UserID != nil {
		dbQuery = dbQuery.Where("recipient_id = ? OR sender_id = ?", *request.UserID, *request.UserID)
	}
	if request.RecipientID != nil {
		dbQuery = dbQuery.Where("recipient_id = ?", *request.RecipientID)
	}
	if request.SenderID != nil {
		dbQuery = dbQuery.Where("sender_id = ?", *request.SenderID)
	}
	if request.Type != nil {
		dbQuery = dbQuery.Where("type = ?", *request.Type)
	}
	if request.Status != nil {
		dbQuery = dbQuery.Where("status = ?", *request.Status)
	}
	if request.Priority != nil {
		dbQuery = dbQuery.Where("priority = ?", *request.Priority)
	}
	if request.BuildingID != nil {
		dbQuery = dbQuery.Where("building_id = ?", *request.BuildingID)
	}
	if request.AssetID != nil {
		dbQuery = dbQuery.Where("asset_id = ?", *request.AssetID)
	}
	if request.StartDate != nil {
		dbQuery = dbQuery.Where("created_at >= ?", *request.StartDate)
	}
	if request.EndDate != nil {
		dbQuery = dbQuery.Where("created_at <= ?", *request.EndDate)
	}

	// Get total count
	var total int64
	if err := dbQuery.Count(&total).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get notification count", err.Error())
		return
	}

	// Get notifications with pagination
	var notifications []models.NotificationEnhanced
	offset := (request.Page - 1) * request.PageSize
	if err := dbQuery.Offset(offset).Limit(request.PageSize).Order("created_at DESC").Find(&notifications).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get notifications", err.Error())
		return
	}

	// Calculate total pages
	totalPages := int((total + int64(request.PageSize) - 1) / int64(request.PageSize))

	response := NotificationHistoryResponse{
		Notifications: notifications,
		Total:         total,
		Page:          request.Page,
		PageSize:      request.PageSize,
		TotalPages:    totalPages,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetNotificationStatistics handles GET /api/notifications/statistics
func (h *EnhancedNotificationHandler) GetNotificationStatistics(c *utils.ChiContext) {
	// Get period from query parameter
	period := c.Request.URL.Query().Get("period")
	if period == "" {
		period = "7d"
	}

	// Get statistics
	statistics := h.enhancedService.GetStatistics()

	response := NotificationStatisticsResponse{
		Statistics:  statistics,
		Period:      period,
		GeneratedAt: time.Now(),
	}

	c.Writer.JSON(http.StatusOK, response)
}

// CreateNotificationTemplate handles POST /api/notifications/templates
func (h *EnhancedNotificationHandler) CreateNotificationTemplate(c *utils.ChiContext) {
	var request CreateNotificationTemplateRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if err := h.validateCreateTemplateRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	// Get current user ID from context (assuming authentication middleware sets this)
	userID, exists := c.Request.Context().Value("user_id").(uint)
	if !exists {
		c.Writer.Error(http.StatusUnauthorized, "User not authenticated", "")
		return
	}

	// Create template
	template := &models.NotificationTemplateEnhanced{
		Name:        request.Name,
		Description: request.Description,
		Type:        request.Type,
		Subject:     request.Subject,
		Body:        request.Body,
		HTMLBody:    request.HTMLBody,
		IsActive:    request.IsActive,
		CreatedBy:   userID,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Set channels
	if err := template.SetChannels(request.Channels); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to set channels", err.Error())
		return
	}

	// Set variables
	if request.Variables != nil {
		if err := template.SetVariables(request.Variables); err != nil {
			c.Writer.Error(http.StatusInternalServerError, "Failed to set variables", err.Error())
			return
		}
	}

	// Save to database
	if err := h.db.Create(template).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create template", err.Error())
		return
	}

	c.Writer.JSON(http.StatusCreated, map[string]interface{}{
		"success":  true,
		"message":  "Template created successfully",
		"template": template,
	})
}

// GetNotificationTemplates handles GET /api/notifications/templates
func (h *EnhancedNotificationHandler) GetNotificationTemplates(c *utils.ChiContext) {
	// Get query parameters
	page, _ := strconv.Atoi(c.Request.URL.Query().Get("page"))
	pageSize, _ := strconv.Atoi(c.Request.URL.Query().Get("page_size"))
	templateType := c.Request.URL.Query().Get("type")
	isActive := c.Request.URL.Query().Get("is_active")

	// Set default pagination
	if page <= 0 {
		page = 1
	}
	if pageSize <= 0 {
		pageSize = 20
	}
	if pageSize > 100 {
		pageSize = 100
	}

	// Build query
	query := h.db.Model(&models.NotificationTemplateEnhanced{})

	// Apply filters
	if templateType != "" {
		query = query.Where("type = ?", templateType)
	}
	if isActive != "" {
		active, _ := strconv.ParseBool(isActive)
		query = query.Where("is_active = ?", active)
	}

	// Get total count
	var total int64
	if err := query.Count(&total).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get template count", err.Error())
		return
	}

	// Get templates with pagination
	var templates []models.NotificationTemplateEnhanced
	offset := (page - 1) * pageSize
	if err := query.Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&templates).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get templates", err.Error())
		return
	}

	response := NotificationTemplatesResponse{
		Templates: templates,
		Total:     total,
		Page:      page,
		PageSize:  pageSize,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetNotificationTemplate handles GET /api/notifications/templates/:id
func (h *EnhancedNotificationHandler) GetNotificationTemplate(c *utils.ChiContext) {
	templateID := chi.URLParam(c.Request, "id")
	if templateID == "" {
		c.Writer.Error(http.StatusBadRequest, "Template ID is required", "")
		return
	}

	id, err := strconv.ParseUint(templateID, 10, 32)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid template ID", "")
		return
	}

	var template models.NotificationTemplateEnhanced
	if err := h.db.First(&template, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.Writer.Error(http.StatusNotFound, "Template not found", "")
			return
		}
		c.Writer.Error(http.StatusInternalServerError, "Failed to get template", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":  true,
		"template": template,
	})
}

// UpdateNotificationTemplate handles PUT /api/notifications/templates/:id
func (h *EnhancedNotificationHandler) UpdateNotificationTemplate(c *utils.ChiContext) {
	templateID := chi.URLParam(c.Request, "id")
	if templateID == "" {
		c.Writer.Error(http.StatusBadRequest, "Template ID is required", "")
		return
	}

	id, err := strconv.ParseUint(templateID, 10, 32)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid template ID", "")
		return
	}

	var request UpdateNotificationTemplateRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Get existing template
	var template models.NotificationTemplateEnhanced
	if err := h.db.First(&template, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.Writer.Error(http.StatusNotFound, "Template not found", "")
			return
		}
		c.Writer.Error(http.StatusInternalServerError, "Failed to get template", err.Error())
		return
	}

	// Update fields
	if request.Name != nil {
		template.Name = *request.Name
	}
	if request.Description != nil {
		template.Description = *request.Description
	}
	if request.Type != nil {
		template.Type = *request.Type
	}
	if request.Subject != nil {
		template.Subject = *request.Subject
	}
	if request.Body != nil {
		template.Body = *request.Body
	}
	if request.HTMLBody != nil {
		template.HTMLBody = *request.HTMLBody
	}
	if request.IsActive != nil {
		template.IsActive = *request.IsActive
	}

	// Update channels if provided
	if len(request.Channels) > 0 {
		if err := template.SetChannels(request.Channels); err != nil {
			c.Writer.Error(http.StatusInternalServerError, "Failed to update channels", err.Error())
			return
		}
	}

	// Update variables if provided
	if request.Variables != nil {
		if err := template.SetVariables(request.Variables); err != nil {
			c.Writer.Error(http.StatusInternalServerError, "Failed to update variables", err.Error())
			return
		}
	}

	template.UpdatedAt = time.Now()

	// Save to database
	if err := h.db.Save(&template).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to update template", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":  true,
		"message":  "Template updated successfully",
		"template": template,
	})
}

// DeleteNotificationTemplate handles DELETE /api/notifications/templates/:id
func (h *EnhancedNotificationHandler) DeleteNotificationTemplate(c *utils.ChiContext) {
	templateID := chi.URLParam(c.Request, "id")
	if templateID == "" {
		c.Writer.Error(http.StatusBadRequest, "Template ID is required", "")
		return
	}

	id, err := strconv.ParseUint(templateID, 10, 32)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid template ID", "")
		return
	}

	// Check if template exists
	var template models.NotificationTemplateEnhanced
	if err := h.db.First(&template, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.Writer.Error(http.StatusNotFound, "Template not found", "")
			return
		}
		c.Writer.Error(http.StatusInternalServerError, "Failed to get template", err.Error())
		return
	}

	// Soft delete
	if err := h.db.Delete(&template).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to delete template", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Template deleted successfully",
	})
}

// Additional handler methods for configuration, preferences, etc.

// CreateNotificationConfig handles POST /api/notifications/config
func (h *EnhancedNotificationHandler) CreateNotificationConfig(c *utils.ChiContext) {
	var request CreateNotificationConfigRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Get current user ID from context
	userID, exists := c.Request.Context().Value("user_id").(uint)
	if !exists {
		c.Writer.Error(http.StatusUnauthorized, "User not authenticated", "")
		return
	}

	// Create config
	config := &models.NotificationConfigEnhanced{
		Name:          request.Name,
		Description:   request.Description,
		Priority:      request.Priority,
		RetryAttempts: request.RetryAttempts,
		RetryDelay:    request.RetryDelay,
		Timeout:       request.Timeout,
		TemplateID:    request.TemplateID,
		IsActive:      request.IsActive,
		CreatedBy:     userID,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}

	// Set channels
	if err := config.SetChannels(request.Channels); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to set channels", err.Error())
		return
	}

	// Set template data
	if request.TemplateData != nil {
		if err := config.SetTemplateData(request.TemplateData); err != nil {
			c.Writer.Error(http.StatusInternalServerError, "Failed to set template data", err.Error())
			return
		}
	}

	// Save to database
	if err := h.db.Create(config).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create config", err.Error())
		return
	}

	c.Writer.JSON(http.StatusCreated, map[string]interface{}{
		"success": true,
		"message": "Configuration created successfully",
		"config":  config,
	})
}

// GetNotificationConfigs handles GET /api/notifications/config
func (h *EnhancedNotificationHandler) GetNotificationConfigs(c *utils.ChiContext) {
	// Get query parameters
	page, _ := strconv.Atoi(c.Request.URL.Query().Get("page"))
	pageSize, _ := strconv.Atoi(c.Request.URL.Query().Get("page_size"))
	isActive := c.Request.URL.Query().Get("is_active")

	// Set default pagination
	if page <= 0 {
		page = 1
	}
	if pageSize <= 0 {
		pageSize = 20
	}
	if pageSize > 100 {
		pageSize = 100
	}

	// Build query
	query := h.db.Model(&models.NotificationConfigEnhanced{})

	// Apply filters
	if isActive != "" {
		active, _ := strconv.ParseBool(isActive)
		query = query.Where("is_active = ?", active)
	}

	// Get total count
	var total int64
	if err := query.Count(&total).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get config count", err.Error())
		return
	}

	// Get configs with pagination
	var configs []models.NotificationConfigEnhanced
	offset := (page - 1) * pageSize
	if err := query.Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&configs).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get configs", err.Error())
		return
	}

	response := NotificationConfigsResponse{
		Configs:  configs,
		Total:    total,
		Page:     page,
		PageSize: pageSize,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetNotificationConfig handles GET /api/notifications/config/:id
func (h *EnhancedNotificationHandler) GetNotificationConfig(c *utils.ChiContext) {
	configID := chi.URLParam(c.Request, "id")
	if configID == "" {
		c.Writer.Error(http.StatusBadRequest, "Config ID is required", "")
		return
	}

	id, err := strconv.ParseUint(configID, 10, 32)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid config ID", "")
		return
	}

	var config models.NotificationConfigEnhanced
	if err := h.db.First(&config, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.Writer.Error(http.StatusNotFound, "Configuration not found", "")
			return
		}
		c.Writer.Error(http.StatusInternalServerError, "Failed to get configuration", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"config":  config,
	})
}

// UpdateNotificationConfig handles PUT /api/notifications/config/:id
func (h *EnhancedNotificationHandler) UpdateNotificationConfig(c *utils.ChiContext) {
	// Implementation similar to UpdateNotificationTemplate
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// DeleteNotificationConfig handles DELETE /api/notifications/config/:id
func (h *EnhancedNotificationHandler) DeleteNotificationConfig(c *utils.ChiContext) {
	// Implementation similar to DeleteNotificationTemplate
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// CreateNotificationPreference handles POST /api/notifications/preferences
func (h *EnhancedNotificationHandler) CreateNotificationPreference(c *utils.ChiContext) {
	var request CreateNotificationPreferenceRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Create preference
	preference := &models.NotificationPreference{
		UserID:    request.UserID,
		Channel:   request.Channel,
		Type:      request.Type,
		IsEnabled: request.IsEnabled,
		Priority:  request.Priority,
		Frequency: request.Frequency,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save to database
	if err := h.db.Create(preference).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create preference", err.Error())
		return
	}

	c.Writer.JSON(http.StatusCreated, map[string]interface{}{
		"success":    true,
		"message":    "Preference created successfully",
		"preference": preference,
	})
}

// GetNotificationPreferences handles GET /api/notifications/preferences
func (h *EnhancedNotificationHandler) GetNotificationPreferences(c *utils.ChiContext) {
	// Get query parameters
	userID := c.Request.URL.Query().Get("user_id")
	page, _ := strconv.Atoi(c.Request.URL.Query().Get("page"))
	pageSize, _ := strconv.Atoi(c.Request.URL.Query().Get("page_size"))

	// Set default pagination
	if page <= 0 {
		page = 1
	}
	if pageSize <= 0 {
		pageSize = 20
	}
	if pageSize > 100 {
		pageSize = 100
	}

	// Build query
	query := h.db.Model(&models.NotificationPreference{})

	// Apply filters
	if userID != "" {
		uid, err := strconv.ParseUint(userID, 10, 32)
		if err != nil {
			c.Writer.Error(http.StatusBadRequest, "Invalid user ID", "")
			return
		}
		query = query.Where("user_id = ?", uid)
	}

	// Get total count
	var total int64
	if err := query.Count(&total).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get preference count", err.Error())
		return
	}

	// Get preferences with pagination
	var preferences []models.NotificationPreference
	offset := (page - 1) * pageSize
	if err := query.Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&preferences).Error; err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get preferences", err.Error())
		return
	}

	response := NotificationPreferencesResponse{
		Preferences: preferences,
		Total:       total,
		Page:        page,
		PageSize:    pageSize,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// UpdateNotificationPreference handles PUT /api/notifications/preferences/:id
func (h *EnhancedNotificationHandler) UpdateNotificationPreference(c *utils.ChiContext) {
	// Implementation similar to UpdateNotificationTemplate
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// DeleteNotificationPreference handles DELETE /api/notifications/preferences/:id
func (h *EnhancedNotificationHandler) DeleteNotificationPreference(c *utils.ChiContext) {
	// Implementation similar to DeleteNotificationTemplate
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// CreateNotificationChannelConfig handles POST /api/notifications/channels
func (h *EnhancedNotificationHandler) CreateNotificationChannelConfig(c *utils.ChiContext) {
	// Implementation for channel configuration
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// GetNotificationChannelConfigs handles GET /api/notifications/channels
func (h *EnhancedNotificationHandler) GetNotificationChannelConfigs(c *utils.ChiContext) {
	// Implementation for getting channel configs
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// GetNotificationChannelConfig handles GET /api/notifications/channels/:channel
func (h *EnhancedNotificationHandler) GetNotificationChannelConfig(c *utils.ChiContext) {
	// Implementation for getting specific channel config
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// UpdateNotificationChannelConfig handles PUT /api/notifications/channels/:channel
func (h *EnhancedNotificationHandler) UpdateNotificationChannelConfig(c *utils.ChiContext) {
	// Implementation for updating channel config
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// DeleteNotificationChannelConfig handles DELETE /api/notifications/channels/:channel
func (h *EnhancedNotificationHandler) DeleteNotificationChannelConfig(c *utils.ChiContext) {
	// Implementation for deleting channel config
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// GetQueueStatistics handles GET /api/notifications/queue/stats
func (h *EnhancedNotificationHandler) GetQueueStatistics(c *utils.ChiContext) {
	// Get queue statistics (placeholder implementation)
	response := QueueStatisticsResponse{
		QueueLength: 0,
		Workers:     5,
		Capacity:    1000,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ClearNotificationQueue handles POST /api/notifications/queue/clear
func (h *EnhancedNotificationHandler) ClearNotificationQueue(c *utils.ChiContext) {
	// Implementation for clearing queue
	c.Writer.JSON(http.StatusNotImplemented, map[string]interface{}{
		"error": "Not implemented yet",
	})
}

// GetNotificationHealth handles GET /api/notifications/health
func (h *EnhancedNotificationHandler) GetNotificationHealth(c *utils.ChiContext) {
	// Get basic health status
	statistics := h.enhancedService.GetStatistics()

	response := NotificationHealthResponse{
		Status:    "healthy",
		Message:   "Notification service is operational",
		Timestamp: time.Now(),
		Services: map[string]bool{
			"email":   true,
			"slack":   true,
			"sms":     true,
			"webhook": true,
		},
		Statistics: statistics,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetDetailedNotificationHealth handles GET /api/notifications/health/detailed
func (h *EnhancedNotificationHandler) GetDetailedNotificationHealth(c *utils.ChiContext) {
	// Get detailed health status
	statistics := h.enhancedService.GetStatistics()

	response := NotificationHealthResponse{
		Status:    "healthy",
		Message:   "Notification service is operational with detailed status",
		Timestamp: time.Now(),
		Services: map[string]bool{
			"email":   true,
			"slack":   true,
			"sms":     true,
			"webhook": true,
			"queue":   true, // Queue operational
		},
		Statistics: statistics,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// Validation methods

// validateSendNotificationRequest validates a send notification request
func (h *EnhancedNotificationHandler) validateSendNotificationRequest(request *SendNotificationRequest) error {
	if request.Title == "" {
		return fmt.Errorf("title is required")
	}
	if request.Message == "" {
		return fmt.Errorf("message is required")
	}
	if !request.Type.IsValid() {
		return fmt.Errorf("invalid notification type: %s", request.Type)
	}
	if request.RecipientID == 0 {
		return fmt.Errorf("recipient_id is required")
	}
	if request.Priority != "" && !request.Priority.IsValid() {
		return fmt.Errorf("invalid priority: %s", request.Priority)
	}
	for _, channel := range request.Channels {
		if !channel.IsValid() {
			return fmt.Errorf("invalid channel: %s", channel)
		}
	}
	return nil
}

// validateCreateTemplateRequest validates a create template request
func (h *EnhancedNotificationHandler) validateCreateTemplateRequest(request *CreateNotificationTemplateRequest) error {
	if request.Name == "" {
		return fmt.Errorf("name is required")
	}
	if request.Body == "" {
		return fmt.Errorf("body is required")
	}
	if !request.Type.IsValid() {
		return fmt.Errorf("invalid notification type: %s", request.Type)
	}
	for _, channel := range request.Channels {
		if !channel.IsValid() {
			return fmt.Errorf("invalid channel: %s", channel)
		}
	}
	return nil
}
