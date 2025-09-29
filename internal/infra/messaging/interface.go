package messaging

import (
	"context"
	"net/http"
)

// Interface defines the messaging interface following Clean Architecture principles
type Interface interface {
	// WebSocket operations
	HandleWebSocket(w http.ResponseWriter, r *http.Request) error
	BroadcastToRoom(room string, message interface{}) error
	BroadcastToUser(userID string, message interface{}) error
	BroadcastToAll(message interface{}) error

	// Room management
	JoinRoom(userID, room string) error
	LeaveRoom(userID, room string) error
	GetRoomUsers(room string) ([]string, error)

	// Notification operations
	SendNotification(ctx context.Context, userID string, notification *Notification) error
	SendBulkNotification(ctx context.Context, userIDs []string, notification *Notification) error

	// Health check
	IsHealthy() bool
	GetStats() map[string]interface{}
}

// Notification represents a notification message
type Notification struct {
	ID       string                 `json:"id"`
	Type     string                 `json:"type"`
	Title    string                 `json:"title"`
	Message  string                 `json:"message"`
	Data     map[string]interface{} `json:"data"`
	Priority string                 `json:"priority"` // low, normal, high, urgent
}
