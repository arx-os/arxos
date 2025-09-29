package messaging

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/messaging"
)

// Service implements the messaging domain service interface using WebSocket infrastructure
type Service struct {
	hub *WebSocketHub
}

// NewService creates a new messaging service with dependency injection
func NewService(hub *WebSocketHub) messaging.Service {
	return &Service{hub: hub}
}

// Building monitoring methods
func (s *Service) SubscribeToBuilding(ctx context.Context, userID, buildingID string) error {
	room := "building:" + buildingID
	return s.hub.JoinRoom(userID, room)
}

func (s *Service) UnsubscribeFromBuilding(ctx context.Context, userID, buildingID string) error {
	room := "building:" + buildingID
	return s.hub.LeaveRoom(userID, room)
}

func (s *Service) PublishBuildingUpdate(ctx context.Context, buildingID string, update *messaging.BuildingUpdate) error {
	room := "building:" + buildingID
	return s.hub.BroadcastToRoom(room, update)
}

// Equipment monitoring methods
func (s *Service) SubscribeToEquipment(ctx context.Context, userID, equipmentID string) error {
	room := "equipment:" + equipmentID
	return s.hub.JoinRoom(userID, room)
}

func (s *Service) UnsubscribeFromEquipment(ctx context.Context, userID, equipmentID string) error {
	room := "equipment:" + equipmentID
	return s.hub.LeaveRoom(userID, room)
}

func (s *Service) PublishEquipmentUpdate(ctx context.Context, equipmentID string, update *messaging.EquipmentUpdate) error {
	room := "equipment:" + equipmentID
	return s.hub.BroadcastToRoom(room, update)
}

// Spatial queries methods
func (s *Service) SubscribeToSpatialQueries(ctx context.Context, userID, queryType string) error {
	room := "spatial_queries:" + queryType
	return s.hub.JoinRoom(userID, room)
}

func (s *Service) UnsubscribeFromSpatialQueries(ctx context.Context, userID, queryType string) error {
	room := "spatial_queries:" + queryType
	return s.hub.LeaveRoom(userID, room)
}

func (s *Service) PublishSpatialUpdate(ctx context.Context, queryType string, update *messaging.SpatialUpdate) error {
	room := "spatial_queries:" + queryType
	return s.hub.BroadcastToRoom(room, update)
}

// Analytics methods
func (s *Service) SubscribeToAnalytics(ctx context.Context, userID, metricType, buildingID string) error {
	room := "analytics:" + metricType
	if buildingID != "" {
		room += ":building:" + buildingID
	}
	return s.hub.JoinRoom(userID, room)
}

func (s *Service) UnsubscribeFromAnalytics(ctx context.Context, userID, metricType, buildingID string) error {
	room := "analytics:" + metricType
	if buildingID != "" {
		room += ":building:" + buildingID
	}
	return s.hub.LeaveRoom(userID, room)
}

func (s *Service) PublishAnalyticsUpdate(ctx context.Context, metricType, buildingID string, update *messaging.AnalyticsUpdate) error {
	room := "analytics:" + metricType
	if buildingID != "" {
		room += ":building:" + buildingID
	}
	return s.hub.BroadcastToRoom(room, update)
}

// Workflow methods
func (s *Service) SubscribeToWorkflow(ctx context.Context, userID, workflowID string) error {
	room := "workflow:" + workflowID
	return s.hub.JoinRoom(userID, room)
}

func (s *Service) UnsubscribeFromWorkflow(ctx context.Context, userID, workflowID string) error {
	room := "workflow:" + workflowID
	return s.hub.LeaveRoom(userID, room)
}

func (s *Service) PublishWorkflowUpdate(ctx context.Context, workflowID string, update *messaging.WorkflowUpdate) error {
	room := "workflow:" + workflowID
	return s.hub.BroadcastToRoom(room, update)
}

// Notification methods
func (s *Service) SendNotification(ctx context.Context, userID string, notification *messaging.Notification) error {
	return s.hub.BroadcastToUser(userID, notification)
}

func (s *Service) SendBulkNotification(ctx context.Context, userIDs []string, notification *messaging.Notification) error {
	var lastErr error
	for _, userID := range userIDs {
		if err := s.hub.BroadcastToUser(userID, notification); err != nil {
			lastErr = fmt.Errorf("failed to send notification to user %s: %w", userID, err)
		}
	}
	return lastErr
}

// Health and stats methods
func (s *Service) IsHealthy() bool {
	return s.hub.IsHealthy()
}

func (s *Service) GetStats() map[string]interface{} {
	return s.hub.GetStats()
}
