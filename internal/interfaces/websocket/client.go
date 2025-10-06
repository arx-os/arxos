package websocket

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/gorilla/websocket"
)

// Client represents a WebSocket client connection
type Client struct {
	// The WebSocket connection
	conn *websocket.Conn

	// Buffered channel of outbound messages
	send chan Message

	// Hub reference
	hub *Hub

	// Client ID
	ID string

	// Client metadata
	UserID      string         `json:"user_id"`
	SessionID   string         `json:"session_id"`
	IPAddress   string         `json:"ip_address"`
	UserAgent   string         `json:"user_agent"`
	ConnectedAt time.Time      `json:"connected_at"`
	LastPong    time.Time      `json:"last_pong"`
	Metadata    map[string]any `json:"metadata"`

	// Logger
	logger domain.Logger

	// Mutex for thread safety
	mu sync.RWMutex
}

// Message represents a WebSocket message
type Message struct {
	Type      string         `json:"type"`
	Content   string         `json:"content"`
	ClientID  string         `json:"client_id"`
	RoomID    string         `json:"room_id,omitempty"`
	Topic     string         `json:"topic,omitempty"`
	Timestamp time.Time      `json:"timestamp"`
	Data      map[string]any `json:"data,omitempty"`
	Error     string         `json:"error,omitempty"`
}

// ClientConfig represents client configuration
type ClientConfig struct {
	ReadBufferSize  int `json:"read_buffer_size"`
	WriteBufferSize int `json:"write_buffer_size"`
	CheckOrigin     func(r *http.Request) bool
}

// DefaultClientConfig returns default client configuration
func DefaultClientConfig() *ClientConfig {
	return &ClientConfig{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin: func(r *http.Request) bool {
			return true // Allow all origins in development
		},
	}
}

// NewClient creates a new WebSocket client
func NewClient(conn *websocket.Conn, hub *Hub, id string, logger domain.Logger) *Client {
	return &Client{
		conn:        conn,
		send:        make(chan Message, 256),
		hub:         hub,
		ID:          id,
		ConnectedAt: time.Now(),
		LastPong:    time.Now(),
		Metadata:    make(map[string]any),
		logger:      logger,
	}
}

// ReadPump pumps messages from the WebSocket connection to the hub
func (c *Client) ReadPump(ctx context.Context) {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	// Set read deadline
	c.conn.SetReadLimit(c.hub.config.MaxMessageSize)
	c.conn.SetReadDeadline(time.Now().Add(c.hub.config.PongWait))
	c.conn.SetPongHandler(func(string) error {
		c.mu.Lock()
		c.LastPong = time.Now()
		c.mu.Unlock()
		c.conn.SetReadDeadline(time.Now().Add(c.hub.config.PongWait))
		return nil
	})

	for {
		select {
		case <-ctx.Done():
			return
		default:
			var msg Message
			err := c.conn.ReadJSON(&msg)
			if err != nil {
				if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
					c.logger.Error("WebSocket error", "client_id", c.ID, "error", err)
				}
				return
			}

			// Set client ID if not set
			if msg.ClientID == "" {
				msg.ClientID = c.ID
			}

			// Process the message
			c.processMessage(msg)
		}
	}
}

// WritePump pumps messages from the hub to the WebSocket connection
func (c *Client) WritePump(ctx context.Context) {
	ticker := time.NewTicker(c.hub.config.PingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case <-ctx.Done():
			return

		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(c.hub.config.WriteWait))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.conn.WriteJSON(message); err != nil {
				c.logger.Error("Failed to write message", "client_id", c.ID, "error", err)
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(c.hub.config.WriteWait))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// processMessage processes incoming messages
func (c *Client) processMessage(msg Message) {
	c.logger.Debug("Processing message", "client_id", c.ID, "type", msg.Type)

	switch msg.Type {
	case "ping":
		c.handlePing(msg)
	case "join_room":
		c.handleJoinRoom(msg)
	case "leave_room":
		c.handleLeaveRoom(msg)
	case "subscribe":
		c.handleSubscribe(msg)
	case "unsubscribe":
		c.handleUnsubscribe(msg)
	case "broadcast":
		c.handleBroadcast(msg)
	case "direct_message":
		c.handleDirectMessage(msg)
	case "get_history":
		c.handleGetHistory(msg)
	case "get_stats":
		c.handleGetStats(msg)
	default:
		c.handleUnknownMessage(msg)
	}
}

// handlePing handles ping messages
func (c *Client) handlePing(msg Message) {
	pongMsg := Message{
		Type:      "pong",
		Content:   "pong",
		Timestamp: time.Now(),
		ClientID:  "system",
	}
	c.send <- pongMsg
}

// handleJoinRoom handles room join requests
func (c *Client) handleJoinRoom(msg Message) {
	if roomID, ok := msg.Data["room_id"].(string); ok {
		c.hub.JoinRoom(c, roomID)
	} else {
		c.sendError("Invalid room_id", msg.Type)
	}
}

// handleLeaveRoom handles room leave requests
func (c *Client) handleLeaveRoom(msg Message) {
	if roomID, ok := msg.Data["room_id"].(string); ok {
		c.hub.LeaveRoom(c, roomID)
	} else {
		c.sendError("Invalid room_id", msg.Type)
	}
}

// handleSubscribe handles topic subscription requests
func (c *Client) handleSubscribe(msg Message) {
	if topic, ok := msg.Data["topic"].(string); ok {
		c.hub.SubscribeToTopic(c, topic)
	} else {
		c.sendError("Invalid topic", msg.Type)
	}
}

// handleUnsubscribe handles topic unsubscription requests
func (c *Client) handleUnsubscribe(msg Message) {
	if topic, ok := msg.Data["topic"].(string); ok {
		c.hub.UnsubscribeFromTopic(c, topic)
	} else {
		c.sendError("Invalid topic", msg.Type)
	}
}

// handleBroadcast handles broadcast messages
func (c *Client) handleBroadcast(msg Message) {
	if content, ok := msg.Data["content"].(string); ok {
		c.hub.broadcast <- []byte(content)
	} else {
		c.sendError("Invalid content", msg.Type)
	}
}

// handleDirectMessage handles direct message requests
func (c *Client) handleDirectMessage(msg Message) {
	targetClientID, hasTarget := msg.Data["target_client_id"].(string)
	content, hasContent := msg.Data["content"].(string)

	if !hasTarget || !hasContent {
		c.sendError("Missing target_client_id or content", msg.Type)
		return
	}

	directMsg := Message{
		Type:      "direct_message",
		Content:   content,
		Timestamp: time.Now(),
		ClientID:  c.ID,
		Data: map[string]any{
			"from_client_id": c.ID,
		},
	}

	if !c.hub.SendDirectMessage(targetClientID, directMsg) {
		c.sendError("Target client not found", msg.Type)
	}
}

// handleGetHistory handles message history requests
func (c *Client) handleGetHistory(msg Message) {
	roomID, ok := msg.Data["room_id"].(string)
	if !ok {
		c.sendError("Invalid room_id", msg.Type)
		return
	}

	history := c.hub.GetMessageHistory(roomID)
	historyMsg := Message{
		Type:      "history_response",
		Timestamp: time.Now(),
		ClientID:  "system",
		Data: map[string]any{
			"room_id": roomID,
			"history": history,
		},
	}
	c.send <- historyMsg
}

// handleGetStats handles statistics requests
func (c *Client) handleGetStats(msg Message) {
	stats := c.hub.GetHubStats()
	statsMsg := Message{
		Type:      "stats_response",
		Timestamp: time.Now(),
		ClientID:  "system",
		Data: map[string]any{
			"stats": stats,
		},
	}
	c.send <- statsMsg
}

// handleUnknownMessage handles unknown message types
func (c *Client) handleUnknownMessage(msg Message) {
	c.sendError(fmt.Sprintf("Unknown message type: %s", msg.Type), msg.Type)
}

// sendError sends an error message to the client
func (c *Client) sendError(errorMsg, originalType string) {
	errorMessage := Message{
		Type:      "error",
		Error:     errorMsg,
		Timestamp: time.Now(),
		ClientID:  "system",
		Data: map[string]any{
			"original_type": originalType,
		},
	}
	c.send <- errorMessage
}

// Close closes the client connection
func (c *Client) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn != nil {
		c.conn.Close()
	}
}

// SetMetadata sets client metadata
func (c *Client) SetMetadata(key string, value any) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.Metadata[key] = value
}

// GetMetadata gets client metadata
func (c *Client) GetMetadata(key string) (any, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	value, exists := c.Metadata[key]
	return value, exists
}

// GetClientInfo returns client information
func (c *Client) GetClientInfo() map[string]any {
	c.mu.RLock()
	defer c.mu.RUnlock()

	return map[string]any{
		"id":           c.ID,
		"user_id":      c.UserID,
		"session_id":   c.SessionID,
		"ip_address":   c.IPAddress,
		"user_agent":   c.UserAgent,
		"connected_at": c.ConnectedAt,
		"last_pong":    c.LastPong,
		"metadata":     c.Metadata,
		"uptime":       time.Since(c.ConnectedAt),
	}
}

// IsAlive checks if the client connection is alive
func (c *Client) IsAlive() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return time.Since(c.LastPong) < c.hub.config.PongWait*2
}

// SendMessage sends a message to the client
func (c *Client) SendMessage(msg Message) bool {
	select {
	case c.send <- msg:
		return true
	default:
		return false
	}
}

// BroadcastToRoom broadcasts a message to a room
func (c *Client) BroadcastToRoom(roomID string, content string, messageType string) {
	msg := Message{
		Type:      messageType,
		Content:   content,
		RoomID:    roomID,
		Timestamp: time.Now(),
		ClientID:  c.ID,
	}
	c.hub.BroadcastToRoom(roomID, msg)
}

// SubscribeToTopic subscribes to a topic
func (c *Client) SubscribeToTopic(topic string) {
	c.hub.SubscribeToTopic(c, topic)
}

// UnsubscribeFromTopic unsubscribes from a topic
func (c *Client) UnsubscribeFromTopic(topic string) {
	c.hub.UnsubscribeFromTopic(c, topic)
}

// JoinRoom joins a room
func (c *Client) JoinRoom(roomID string) {
	c.hub.JoinRoom(c, roomID)
}

// LeaveRoom leaves a room
func (c *Client) LeaveRoom(roomID string) {
	c.hub.LeaveRoom(c, roomID)
}
