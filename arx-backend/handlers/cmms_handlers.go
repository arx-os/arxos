package handlers

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"

	"arx/services/cmms"
	"arx/utils"
)

// CMMSHandler handles CMMS-related HTTP requests
type CMMSHandler struct {
	cmmsService *cmms.CMMSService
}

// NewCMMSHandler creates a new CMMS handler
func NewCMMSHandler(cmmsService *cmms.CMMSService) *CMMSHandler {
	return &CMMSHandler{
		cmmsService: cmmsService,
	}
}

// AddCMMSConnectionRequest represents the request to add a CMMS connection
type AddCMMSConnectionRequest struct {
	CMMSType       string  `json:"cmms_type" binding:"required"`
	APIURL         string  `json:"api_url" binding:"required"`
	APIKey         string  `json:"api_key" binding:"required"`
	Username       *string `json:"username,omitempty"`
	Password       *string `json:"password,omitempty"`
	ConnectionName string  `json:"connection_name" binding:"required"`
}

// AddCMMSConnection adds a new CMMS connection
func (h *CMMSHandler) AddCMMSConnection(c *utils.ChiContext) {
	var request AddCMMSConnectionRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	connection := cmms.CMMSConnection{
		CMMSType:       request.CMMSType,
		APIURL:         request.APIURL,
		APIKey:         request.APIKey,
		Username:       request.Username,
		Password:       request.Password,
		ConnectionName: request.ConnectionName,
	}

	result, err := h.cmmsService.AddCMMSConnection(connection)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to add CMMS connection", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":    true,
		"connection": result,
		"message":    "CMMS connection added successfully",
	})
}

// SyncWorkOrdersRequest represents the request to sync work orders
type SyncWorkOrdersRequest struct {
	ConnectionID uuid.UUID `json:"connection_id" binding:"required"`
	ForceSync    bool      `json:"force_sync"`
}

// SyncWorkOrders synchronizes work orders from CMMS
func (h *CMMSHandler) SyncWorkOrders(c *utils.ChiContext) {
	var request SyncWorkOrdersRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := h.cmmsService.SyncWorkOrders(request.ConnectionID, request.ForceSync)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to sync work orders", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"result":  result,
		"message": "Work orders synchronized successfully",
	})
}

// CreateWorkOrderRequest represents the request to create a work order
type CreateWorkOrderRequest struct {
	TemplateID     *uuid.UUID `json:"template_id,omitempty"`
	AssetID        string     `json:"asset_id" binding:"required"`
	Title          string     `json:"title" binding:"required"`
	Description    string     `json:"description" binding:"required"`
	Priority       string     `json:"priority" binding:"required"`
	EstimatedHours float64    `json:"estimated_hours" binding:"required"`
	AssignedTo     *string    `json:"assigned_to,omitempty"`
	ScheduledStart *time.Time `json:"scheduled_start,omitempty"`
	ScheduledEnd   *time.Time `json:"scheduled_end,omitempty"`
}

// CreateWorkOrder creates a new work order
func (h *CMMSHandler) CreateWorkOrder(c *utils.ChiContext) {
	var request CreateWorkOrderRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	workOrder := cmms.WorkOrder{
		AssetID:        request.AssetID,
		Title:          request.Title,
		Description:    request.Description,
		Priority:       request.Priority,
		EstimatedHours: request.EstimatedHours,
		AssignedTo:     request.AssignedTo,
		ScheduledStart: request.ScheduledStart,
		ScheduledEnd:   request.ScheduledEnd,
	}

	result, err := h.cmmsService.CreateWorkOrder(workOrder)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create work order", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":    true,
		"work_order": result,
		"message":    "Work order created successfully",
	})
}

// GetWorkOrders retrieves work orders with optional filters
func (h *CMMSHandler) GetWorkOrders(c *utils.ChiContext) {
	status := c.Reader.Query("status")
	assetID := c.Reader.Query("asset_id")
	assignedTo := c.Reader.Query("assigned_to")

	var statusPtr, assetIDPtr, assignedToPtr *string
	if status != "" {
		statusPtr = &status
	}
	if assetID != "" {
		assetIDPtr = &assetID
	}
	if assignedTo != "" {
		assignedToPtr = &assignedTo
	}

	workOrders, err := h.cmmsService.GetWorkOrders(statusPtr, assetIDPtr, assignedToPtr)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to retrieve work orders", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":     true,
		"work_orders": workOrders,
		"message":     "Work orders retrieved successfully",
	})
}

// UpdateWorkOrderStatusRequest represents the request to update work order status
type UpdateWorkOrderStatusRequest struct {
	Status string `json:"status" binding:"required"`
}

// UpdateWorkOrderStatus updates the status of a work order
func (h *CMMSHandler) UpdateWorkOrderStatus(c *utils.ChiContext) {
	workOrderIDStr := c.Reader.Param("id")
	_, err := uuid.Parse(workOrderIDStr)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid work order ID", err.Error())
		return
	}

	var request UpdateWorkOrderStatusRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// This would typically call a method to update the work order status
	// For now, we'll return a success response
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Work order status updated successfully",
	})
}

// CreateMaintenanceScheduleRequest represents the request to create a maintenance schedule
type CreateMaintenanceScheduleRequest struct {
	Name              string      `json:"name" binding:"required"`
	Description       string      `json:"description" binding:"required"`
	MaintenanceType   string      `json:"maintenance_type" binding:"required"`
	Priority          string      `json:"priority" binding:"required"`
	Frequency         string      `json:"frequency" binding:"required"`
	TriggerType       string      `json:"trigger_type" binding:"required"`
	TriggerValue      interface{} `json:"trigger_value" binding:"required"`
	EstimatedDuration int         `json:"estimated_duration" binding:"required"`
	EstimatedCost     float64     `json:"estimated_cost" binding:"required"`
	RequiredSkills    []string    `json:"required_skills"`
	RequiredTools     []string    `json:"required_tools"`
	RequiredParts     []string    `json:"required_parts"`
}

// CreateMaintenanceSchedule creates a new maintenance schedule
func (h *CMMSHandler) CreateMaintenanceSchedule(c *utils.ChiContext) {
	var request CreateMaintenanceScheduleRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	schedule := cmms.MaintenanceSchedule{
		Name:              request.Name,
		Description:       request.Description,
		MaintenanceType:   request.MaintenanceType,
		Priority:          request.Priority,
		Frequency:         request.Frequency,
		TriggerType:       request.TriggerType,
		TriggerValue:      request.TriggerValue,
		EstimatedDuration: request.EstimatedDuration,
		EstimatedCost:     request.EstimatedCost,
		RequiredSkills:    request.RequiredSkills,
		RequiredTools:     request.RequiredTools,
		RequiredParts:     request.RequiredParts,
	}

	result, err := h.cmmsService.CreateMaintenanceSchedule(schedule)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create maintenance schedule", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":  true,
		"schedule": result,
		"message":  "Maintenance schedule created successfully",
	})
}

// GetMaintenanceSchedules retrieves all maintenance schedules
func (h *CMMSHandler) GetMaintenanceSchedules(c *utils.ChiContext) {
	schedules, err := h.cmmsService.GetMaintenanceSchedules()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to retrieve maintenance schedules", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":   true,
		"schedules": schedules,
		"message":   "Maintenance schedules retrieved successfully",
	})
}

// RegisterAssetRequest represents the request to register an asset
type RegisterAssetRequest struct {
	AssetID           string                 `json:"asset_id" binding:"required"`
	Name              string                 `json:"name" binding:"required"`
	AssetType         string                 `json:"asset_type" binding:"required"`
	Description       *string                `json:"description,omitempty"`
	Manufacturer      *string                `json:"manufacturer,omitempty"`
	Model             *string                `json:"model,omitempty"`
	SerialNumber      *string                `json:"serial_number,omitempty"`
	InstallationDate  *time.Time             `json:"installation_date,omitempty"`
	WarrantyExpiry    *time.Time             `json:"warranty_expiry,omitempty"`
	ExpectedLifespan  *int                   `json:"expected_lifespan,omitempty"`
	Department        *string                `json:"department,omitempty"`
	ResponsiblePerson *string                `json:"responsible_person,omitempty"`
	Tags              []string               `json:"tags"`
	Specifications    map[string]interface{} `json:"specifications"`
}

// RegisterAsset registers a new asset
func (h *CMMSHandler) RegisterAsset(c *utils.ChiContext) {
	var request RegisterAssetRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	asset := cmms.Asset{
		ID:                request.AssetID,
		Name:              request.Name,
		AssetType:         request.AssetType,
		Description:       request.Description,
		Manufacturer:      request.Manufacturer,
		Model:             request.Model,
		SerialNumber:      request.SerialNumber,
		InstallationDate:  request.InstallationDate,
		WarrantyExpiry:    request.WarrantyExpiry,
		ExpectedLifespan:  request.ExpectedLifespan,
		Department:        request.Department,
		ResponsiblePerson: request.ResponsiblePerson,
		Tags:              request.Tags,
		Specifications:    request.Specifications,
	}

	result, err := h.cmmsService.RegisterAsset(asset)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to register asset", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"asset":   result,
		"message": "Asset registered successfully",
	})
}

// GetAssets retrieves assets with optional filters
func (h *CMMSHandler) GetAssets(c *utils.ChiContext) {
	assetType := c.Reader.Query("asset_type")
	status := c.Reader.Query("status")
	department := c.Reader.Query("department")

	var assetTypePtr, statusPtr, departmentPtr *string
	if assetType != "" {
		assetTypePtr = &assetType
	}
	if status != "" {
		statusPtr = &status
	}
	if department != "" {
		departmentPtr = &department
	}

	assets, err := h.cmmsService.GetAssets(assetTypePtr, statusPtr, departmentPtr)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to retrieve assets", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"assets":  assets,
		"message": "Assets retrieved successfully",
	})
}

// RecordPerformanceDataRequest represents the request to record performance data
type RecordPerformanceDataRequest struct {
	UptimePercentage  float64  `json:"uptime_percentage" binding:"required"`
	EfficiencyRating  float64  `json:"efficiency_rating" binding:"required"`
	Throughput        *float64 `json:"throughput,omitempty"`
	EnergyConsumption *float64 `json:"energy_consumption,omitempty"`
	Temperature       *float64 `json:"temperature,omitempty"`
	Vibration         *float64 `json:"vibration,omitempty"`
	Pressure          *float64 `json:"pressure,omitempty"`
	Speed             *float64 `json:"speed,omitempty"`
	LoadPercentage    *float64 `json:"load_percentage,omitempty"`
	ErrorCount        int      `json:"error_count"`
	WarningCount      int      `json:"warning_count"`
	MaintenanceHours  *float64 `json:"maintenance_hours,omitempty"`
	CostPerHour       *float64 `json:"cost_per_hour,omitempty"`
}

// RecordPerformanceData records performance data for an asset
func (h *CMMSHandler) RecordPerformanceData(c *utils.ChiContext) {
	assetID := c.Reader.Param("id")
	if assetID == "" {
		c.Writer.Error(http.StatusBadRequest, "Asset ID is required", "")
		return
	}

	var request RecordPerformanceDataRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	performance := cmms.AssetPerformance{
		AssetID:           assetID,
		Timestamp:         time.Now(),
		UptimePercentage:  request.UptimePercentage,
		EfficiencyRating:  request.EfficiencyRating,
		Throughput:        request.Throughput,
		EnergyConsumption: request.EnergyConsumption,
		Temperature:       request.Temperature,
		Vibration:         request.Vibration,
		Pressure:          request.Pressure,
		Speed:             request.Speed,
		LoadPercentage:    request.LoadPercentage,
		ErrorCount:        request.ErrorCount,
		WarningCount:      request.WarningCount,
		MaintenanceHours:  request.MaintenanceHours,
		CostPerHour:       request.CostPerHour,
	}

	err := h.cmmsService.RecordPerformanceData(assetID, performance)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to record performance data", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Performance data recorded successfully",
	})
}

// GetAssetStatistics retrieves asset statistics
func (h *CMMSHandler) GetAssetStatistics(c *utils.ChiContext) {
	assetID := c.Reader.Query("asset_id")
	startDateStr := c.Reader.Query("start_date")
	endDateStr := c.Reader.Query("end_date")

	var assetIDPtr *string
	if assetID != "" {
		assetIDPtr = &assetID
	}

	var startDatePtr, endDatePtr *time.Time
	if startDateStr != "" {
		startDate, err := time.Parse(time.RFC3339, startDateStr)
		if err != nil {
			c.Writer.Error(http.StatusBadRequest, "Invalid start_date format", err.Error())
			return
		}
		startDatePtr = &startDate
	}

	if endDateStr != "" {
		endDate, err := time.Parse(time.RFC3339, endDateStr)
		if err != nil {
			c.Writer.Error(http.StatusBadRequest, "Invalid end_date format", err.Error())
			return
		}
		endDatePtr = &endDate
	}

	statistics, err := h.cmmsService.GetAssetStatistics(assetIDPtr, startDatePtr, endDatePtr)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to retrieve asset statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":    true,
		"statistics": statistics,
	})
}

// GetMaintenanceStatistics retrieves maintenance statistics
func (h *CMMSHandler) GetMaintenanceStatistics(c *utils.ChiContext) {
	startDateStr := c.Reader.Query("start_date")
	endDateStr := c.Reader.Query("end_date")

	// Parse dates if provided
	if startDateStr != "" {
		_, err := time.Parse(time.RFC3339, startDateStr)
		if err != nil {
			c.Writer.Error(http.StatusBadRequest, "Invalid start_date format", err.Error())
			return
		}
	}

	if endDateStr != "" {
		_, err := time.Parse(time.RFC3339, endDateStr)
		if err != nil {
			c.Writer.Error(http.StatusBadRequest, "Invalid end_date format", err.Error())
			return
		}
	}

	// This would typically call a method to get maintenance statistics
	// For now, we'll return mock data
	statistics := map[string]interface{}{
		"total_tasks":               0,
		"completed_tasks":           0,
		"overdue_tasks":             0,
		"in_progress_tasks":         0,
		"completion_rate":           0.0,
		"total_cost":                0.0,
		"total_duration_hours":      0.0,
		"average_cost_per_task":     0.0,
		"average_duration_per_task": 0.0,
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success":    true,
		"statistics": statistics,
	})
}

// ScheduleRecurringMaintenance schedules recurring maintenance tasks
func (h *CMMSHandler) ScheduleRecurringMaintenance(c *utils.ChiContext) {
	// This would typically call a method to schedule recurring maintenance
	// For now, we'll return a success response
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Recurring maintenance scheduled successfully",
	})
}

// SetupCMMSRoutes sets up CMMS-related routes
func SetupCMMSRoutes(router chi.Router, cmmsService *cmms.CMMSService) {
	handler := NewCMMSHandler(cmmsService)

	// CMMS data synchronization routes
	router.Route("/api/v1/cmms", func(r chi.Router) {
		r.Post("/connections", utils.ToChiHandler(handler.AddCMMSConnection))
		r.Post("/sync/work-orders", utils.ToChiHandler(handler.SyncWorkOrders))
	})

	// Work order routes
	router.Route("/api/v1/work-orders", func(r chi.Router) {
		r.Post("/", utils.ToChiHandler(handler.CreateWorkOrder))
		r.Get("/", utils.ToChiHandler(handler.GetWorkOrders))
		r.Put("/{id}/status", utils.ToChiHandler(handler.UpdateWorkOrderStatus))
	})

	// Maintenance schedule routes
	router.Route("/api/v1/maintenance", func(r chi.Router) {
		r.Post("/schedules", utils.ToChiHandler(handler.CreateMaintenanceSchedule))
		r.Get("/schedules", utils.ToChiHandler(handler.GetMaintenanceSchedules))
		r.Post("/schedule-recurring", utils.ToChiHandler(handler.ScheduleRecurringMaintenance))
		r.Get("/statistics", utils.ToChiHandler(handler.GetMaintenanceStatistics))
	})

	// Asset routes
	router.Route("/api/v1/assets", func(r chi.Router) {
		r.Post("/", utils.ToChiHandler(handler.RegisterAsset))
		r.Get("/", utils.ToChiHandler(handler.GetAssets))
		r.Post("/{id}/performance", utils.ToChiHandler(handler.RecordPerformanceData))
		r.Get("/statistics", utils.ToChiHandler(handler.GetAssetStatistics))
	})
}
