package examples

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/domain/messaging"
	inframessaging "github.com/arx-os/arxos/internal/infra/messaging"
)

// WebSocketIntegrationExample demonstrates how to use WebSocket functionality
// following Clean Architecture principles
type WebSocketIntegrationExample struct {
	messagingService messaging.Service
	hub              *inframessaging.WebSocketHub
}

// NewWebSocketIntegrationExample creates a new WebSocket integration example
func NewWebSocketIntegrationExample(messagingService messaging.Service, hub *inframessaging.WebSocketHub) *WebSocketIntegrationExample {
	return &WebSocketIntegrationExample{
		messagingService: messagingService,
		hub:              hub,
	}
}

// DemonstrateBuildingMonitoring shows how to implement real-time building monitoring
func (w *WebSocketIntegrationExample) DemonstrateBuildingMonitoring(ctx context.Context) error {
	buildingID := "building-001"
	userID := "user-123"

	// Subscribe user to building updates
	if err := w.messagingService.SubscribeToBuilding(ctx, userID, buildingID); err != nil {
		return err
	}

	// Simulate building updates
	updates := []*messaging.BuildingUpdate{
		messaging.CreateBuildingUpdate(buildingID, "status_changed", map[string]interface{}{
			"status":      "active",
			"occupancy":   75,
			"temperature": 22.5,
		}, "sensor_system"),

		messaging.CreateBuildingUpdate(buildingID, "energy_update", map[string]interface{}{
			"consumption": 1250.5,
			"efficiency":  85.2,
			"peak_hours":  []string{"09:00", "10:00", "11:00"},
		}, "energy_monitor"),

		messaging.CreateBuildingUpdate(buildingID, "maintenance_alert", map[string]interface{}{
			"equipment_id": "hvac-001",
			"alert_type":   "filter_replacement_due",
			"priority":     "medium",
		}, "maintenance_system"),
	}

	// Publish updates
	for _, update := range updates {
		if err := w.messagingService.PublishBuildingUpdate(ctx, buildingID, update); err != nil {
			return err
		}
		time.Sleep(100 * time.Millisecond) // Simulate real-time updates
	}

	return nil
}

// DemonstrateEquipmentMonitoring shows how to implement real-time equipment monitoring
func (w *WebSocketIntegrationExample) DemonstrateEquipmentMonitoring(ctx context.Context) error {
	equipmentID := "hvac-001"
	buildingID := "building-001"
	userID := "user-123"

	// Subscribe user to equipment updates
	if err := w.messagingService.SubscribeToEquipment(ctx, userID, equipmentID); err != nil {
		return err
	}

	// Simulate equipment updates
	updates := []*messaging.EquipmentUpdate{
		messaging.CreateEquipmentUpdate(equipmentID, buildingID, "status_changed", map[string]interface{}{
			"status":      "running",
			"temperature": 22.5,
			"humidity":    45.0,
			"fan_speed":   75,
		}, "hvac_controller"),

		messaging.CreateEquipmentUpdate(equipmentID, buildingID, "maintenance_due", map[string]interface{}{
			"maintenance_type": "filter_replacement",
			"due_date":         "2024-01-15",
			"priority":         "medium",
		}, "maintenance_scheduler"),

		messaging.CreateEquipmentUpdate(equipmentID, buildingID, "alarm", map[string]interface{}{
			"alarm_type":    "temperature_high",
			"threshold":     25.0,
			"current_value": 26.5,
			"severity":      "high",
		}, "alarm_system"),
	}

	// Publish updates
	for _, update := range updates {
		if err := w.messagingService.PublishEquipmentUpdate(ctx, equipmentID, update); err != nil {
			return err
		}
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

// DemonstrateSpatialQueries shows how to implement real-time spatial queries
func (w *WebSocketIntegrationExample) DemonstrateSpatialQueries(ctx context.Context) error {
	queryType := "nearby_equipment"
	userID := "user-123"

	// Subscribe user to spatial queries
	if err := w.messagingService.SubscribeToSpatialQueries(ctx, userID, queryType); err != nil {
		return err
	}

	// Simulate spatial updates
	updates := []*messaging.SpatialUpdate{
		messaging.CreateSpatialUpdate(queryType, map[string]interface{}{
			"center": map[string]float64{"x": 10.5, "y": 20.3, "z": 0.0},
			"radius": 5.0,
			"equipment": []map[string]interface{}{
				{"id": "outlet-001", "distance": 2.1, "type": "electrical"},
				{"id": "sensor-002", "distance": 3.5, "type": "environmental"},
			},
		}, "spatial_engine"),

		messaging.CreateSpatialUpdate(queryType, map[string]interface{}{
			"center": map[string]float64{"x": 15.2, "y": 25.8, "z": 0.0},
			"radius": 3.0,
			"equipment": []map[string]interface{}{
				{"id": "light-003", "distance": 1.8, "type": "lighting"},
			},
		}, "spatial_engine"),
	}

	// Publish updates
	for _, update := range updates {
		if err := w.messagingService.PublishSpatialUpdate(ctx, queryType, update); err != nil {
			return err
		}
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

// DemonstrateAnalytics shows how to implement real-time analytics
func (w *WebSocketIntegrationExample) DemonstrateAnalytics(ctx context.Context) error {
	metricType := "energy"
	buildingID := "building-001"
	userID := "user-123"

	// Subscribe user to analytics
	if err := w.messagingService.SubscribeToAnalytics(ctx, userID, metricType, buildingID); err != nil {
		return err
	}

	// Simulate analytics updates
	updates := []*messaging.AnalyticsUpdate{
		messaging.CreateAnalyticsUpdate(metricType, buildingID, map[string]interface{}{
			"consumption": 1250.5,
			"efficiency":  85.2,
			"trend":       "decreasing",
			"prediction": map[string]interface{}{
				"next_hour":  1200.0,
				"confidence": 0.85,
			},
		}, "analytics_engine"),

		messaging.CreateAnalyticsUpdate(metricType, buildingID, map[string]interface{}{
			"consumption": 1180.3,
			"efficiency":  87.1,
			"trend":       "decreasing",
			"anomalies": []map[string]interface{}{
				{"time": "14:30", "value": 1350.0, "severity": "medium"},
			},
		}, "analytics_engine"),
	}

	// Publish updates
	for _, update := range updates {
		if err := w.messagingService.PublishAnalyticsUpdate(ctx, metricType, buildingID, update); err != nil {
			return err
		}
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

// DemonstrateWorkflowUpdates shows how to implement real-time workflow updates
func (w *WebSocketIntegrationExample) DemonstrateWorkflowUpdates(ctx context.Context) error {
	workflowID := "maintenance-workflow-001"
	userID := "user-123"

	// Subscribe user to workflow updates
	if err := w.messagingService.SubscribeToWorkflow(ctx, userID, workflowID); err != nil {
		return err
	}

	// Simulate workflow updates
	updates := []*messaging.WorkflowUpdate{
		messaging.CreateWorkflowUpdate(workflowID, "started", map[string]interface{}{
			"workflow_name":      "HVAC Maintenance",
			"assigned_to":        "technician-001",
			"estimated_duration": "2 hours",
		}, "workflow_engine"),

		messaging.CreateWorkflowUpdate(workflowID, "step_completed", map[string]interface{}{
			"step_name": "Filter Inspection",
			"status":    "completed",
			"duration":  "15 minutes",
			"next_step": "Filter Replacement",
		}, "workflow_engine"),

		messaging.CreateWorkflowUpdate(workflowID, "completed", map[string]interface{}{
			"total_duration": "1.5 hours",
			"status":         "success",
			"notes":          "All maintenance tasks completed successfully",
		}, "workflow_engine"),
	}

	// Publish updates
	for _, update := range updates {
		if err := w.messagingService.PublishWorkflowUpdate(ctx, workflowID, update); err != nil {
			return err
		}
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

// DemonstrateNotifications shows how to implement notifications
func (w *WebSocketIntegrationExample) DemonstrateNotifications(ctx context.Context) error {
	userID := "user-123"

	// Send individual notification
	notification := messaging.CreateNotification(
		userID,
		"alert",
		"High Energy Consumption",
		"Building 001 is consuming 15% more energy than usual",
		map[string]interface{}{
			"building_id": "building-001",
			"consumption": 1350.0,
			"threshold":   1200.0,
		},
	)

	if err := w.messagingService.SendNotification(ctx, userID, notification); err != nil {
		return err
	}

	// Send bulk notification
	userIDs := []string{"user-123", "user-456", "user-789"}
	bulkNotification := messaging.CreateNotification(
		"", // Will be set for each user
		"info",
		"System Maintenance",
		"Scheduled maintenance will begin at 2:00 AM",
		map[string]interface{}{
			"maintenance_type":   "database_optimization",
			"scheduled_time":     "2024-01-15T02:00:00Z",
			"estimated_duration": "30 minutes",
		},
	)

	if err := w.messagingService.SendBulkNotification(ctx, userIDs, bulkNotification); err != nil {
		return err
	}

	return nil
}

// GetWebSocketStats returns current WebSocket statistics
func (w *WebSocketIntegrationExample) GetWebSocketStats() map[string]interface{} {
	return w.hub.GetStats()
}
