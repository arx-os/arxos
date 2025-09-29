package messaging

import (
	"context"
	"time"

	"github.com/google/uuid"
)

// Service defines the interface for messaging business logic following Clean Architecture principles
type Service interface {
	// Real-time building monitoring
	SubscribeToBuilding(ctx context.Context, userID, buildingID string) error
	UnsubscribeFromBuilding(ctx context.Context, userID, buildingID string) error
	PublishBuildingUpdate(ctx context.Context, buildingID string, update *BuildingUpdate) error

	// Equipment monitoring
	SubscribeToEquipment(ctx context.Context, userID, equipmentID string) error
	UnsubscribeFromEquipment(ctx context.Context, userID, equipmentID string) error
	PublishEquipmentUpdate(ctx context.Context, equipmentID string, update *EquipmentUpdate) error

	// Spatial queries
	SubscribeToSpatialQueries(ctx context.Context, userID, queryType string) error
	UnsubscribeFromSpatialQueries(ctx context.Context, userID, queryType string) error
	PublishSpatialUpdate(ctx context.Context, queryType string, update *SpatialUpdate) error

	// Analytics
	SubscribeToAnalytics(ctx context.Context, userID, metricType, buildingID string) error
	UnsubscribeFromAnalytics(ctx context.Context, userID, metricType, buildingID string) error
	PublishAnalyticsUpdate(ctx context.Context, metricType, buildingID string, update *AnalyticsUpdate) error

	// Workflow updates
	SubscribeToWorkflow(ctx context.Context, userID, workflowID string) error
	UnsubscribeFromWorkflow(ctx context.Context, userID, workflowID string) error
	PublishWorkflowUpdate(ctx context.Context, workflowID string, update *WorkflowUpdate) error

	// Notifications
	SendNotification(ctx context.Context, userID string, notification *Notification) error
	SendBulkNotification(ctx context.Context, userIDs []string, notification *Notification) error

	// Health and stats
	IsHealthy() bool
	GetStats() map[string]interface{}
}

// BuildingUpdate represents a building update message
type BuildingUpdate struct {
	ID         string                 `json:"id"`
	BuildingID string                 `json:"building_id"`
	Type       string                 `json:"type"` // created, updated, deleted, status_changed
	Data       map[string]interface{} `json:"data"`
	Timestamp  time.Time              `json:"timestamp"`
	Source     string                 `json:"source"`
	Priority   string                 `json:"priority"` // low, normal, high, urgent
}

// EquipmentUpdate represents an equipment update message
type EquipmentUpdate struct {
	ID          string                 `json:"id"`
	EquipmentID string                 `json:"equipment_id"`
	BuildingID  string                 `json:"building_id"`
	Type        string                 `json:"type"` // status_changed, maintenance_due, alarm, data_update
	Data        map[string]interface{} `json:"data"`
	Timestamp   time.Time              `json:"timestamp"`
	Source      string                 `json:"source"`
	Priority    string                 `json:"priority"`
}

// SpatialUpdate represents a spatial update message
type SpatialUpdate struct {
	ID        string                 `json:"id"`
	QueryType string                 `json:"query_type"` // nearby, within_bounds, floor_analysis
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	Source    string                 `json:"source"`
	Priority  string                 `json:"priority"`
}

// AnalyticsUpdate represents an analytics update message
type AnalyticsUpdate struct {
	ID         string                 `json:"id"`
	MetricType string                 `json:"metric_type"` // energy, performance, occupancy, temperature
	BuildingID string                 `json:"building_id"`
	Data       map[string]interface{} `json:"data"`
	Timestamp  time.Time              `json:"timestamp"`
	Source     string                 `json:"source"`
	Priority   string                 `json:"priority"`
}

// WorkflowUpdate represents a workflow update message
type WorkflowUpdate struct {
	ID         string                 `json:"id"`
	WorkflowID string                 `json:"workflow_id"`
	Type       string                 `json:"type"` // started, completed, failed, step_completed
	Data       map[string]interface{} `json:"data"`
	Timestamp  time.Time              `json:"timestamp"`
	Source     string                 `json:"source"`
	Priority   string                 `json:"priority"`
}

// Notification represents a notification message
type Notification struct {
	ID        string                 `json:"id"`
	UserID    string                 `json:"user_id"`
	Type      string                 `json:"type"` // alert, info, warning, error
	Title     string                 `json:"title"`
	Message   string                 `json:"message"`
	Data      map[string]interface{} `json:"data"`
	Read      bool                   `json:"read"`
	CreatedAt time.Time              `json:"created_at"`
	Priority  string                 `json:"priority"`
}

// CreateBuildingUpdate creates a new building update
func CreateBuildingUpdate(buildingID, updateType string, data map[string]interface{}, source string) *BuildingUpdate {
	return &BuildingUpdate{
		ID:         uuid.New().String(),
		BuildingID: buildingID,
		Type:       updateType,
		Data:       data,
		Timestamp:  time.Now(),
		Source:     source,
		Priority:   "normal",
	}
}

// CreateEquipmentUpdate creates a new equipment update
func CreateEquipmentUpdate(equipmentID, buildingID, updateType string, data map[string]interface{}, source string) *EquipmentUpdate {
	return &EquipmentUpdate{
		ID:          uuid.New().String(),
		EquipmentID: equipmentID,
		BuildingID:  buildingID,
		Type:        updateType,
		Data:        data,
		Timestamp:   time.Now(),
		Source:      source,
		Priority:    "normal",
	}
}

// CreateSpatialUpdate creates a new spatial update
func CreateSpatialUpdate(queryType string, data map[string]interface{}, source string) *SpatialUpdate {
	return &SpatialUpdate{
		ID:        uuid.New().String(),
		QueryType: queryType,
		Data:      data,
		Timestamp: time.Now(),
		Source:    source,
		Priority:  "normal",
	}
}

// CreateAnalyticsUpdate creates a new analytics update
func CreateAnalyticsUpdate(metricType, buildingID string, data map[string]interface{}, source string) *AnalyticsUpdate {
	return &AnalyticsUpdate{
		ID:         uuid.New().String(),
		MetricType: metricType,
		BuildingID: buildingID,
		Data:       data,
		Timestamp:  time.Now(),
		Source:     source,
		Priority:   "normal",
	}
}

// CreateWorkflowUpdate creates a new workflow update
func CreateWorkflowUpdate(workflowID, updateType string, data map[string]interface{}, source string) *WorkflowUpdate {
	return &WorkflowUpdate{
		ID:         uuid.New().String(),
		WorkflowID: workflowID,
		Type:       updateType,
		Data:       data,
		Timestamp:  time.Now(),
		Source:     source,
		Priority:   "normal",
	}
}

// CreateNotification creates a new notification
func CreateNotification(userID, notificationType, title, message string, data map[string]interface{}) *Notification {
	return &Notification{
		ID:        uuid.New().String(),
		UserID:    userID,
		Type:      notificationType,
		Title:     title,
		Message:   message,
		Data:      data,
		Read:      false,
		CreatedAt: time.Now(),
		Priority:  "normal",
	}
}
