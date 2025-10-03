package websocket

import (
	"context"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"github.com/arx-os/arxos/internal/domain"
)

// Handler handles WebSocket connections
type Handler struct {
	hub    *Hub
	config *ClientConfig
	logger domain.Logger
}

// NewHandler creates a new WebSocket handler
func NewHandler(hub *Hub, config *ClientConfig, logger domain.Logger) *Handler {
	if config == nil {
		config = DefaultClientConfig()
	}

	return &Handler{
		hub:    hub,
		config: config,
		logger: logger,
	}
}

// ServeWS handles WebSocket upgrade requests
func (h *Handler) ServeWS(w http.ResponseWriter, r *http.Request) {
	// Upgrade the connection to WebSocket
	upgrader := websocket.Upgrader{
		ReadBufferSize:  h.config.ReadBufferSize,
		WriteBufferSize: h.config.WriteBufferSize,
		CheckOrigin:     h.config.CheckOrigin,
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		h.logger.Error("Failed to upgrade WebSocket connection", "error", err)
		http.Error(w, "Failed to upgrade WebSocket connection", http.StatusBadRequest)
		return
	}

	// Generate unique client ID
	clientID := uuid.New().String()

	// Create new client
	client := NewClient(conn, h.hub, clientID, h.logger)

	// Set client metadata from request
	client.IPAddress = h.getClientIP(r)
	client.UserAgent = r.UserAgent()
	client.SessionID = h.getSessionID(r)
	client.UserID = h.getUserID(r)

	// Register client with hub
	h.hub.register <- client

	h.logger.Info("WebSocket client connected", 
		"client_id", clientID,
		"ip_address", client.IPAddress,
		"user_agent", client.UserAgent,
	)

	// Start client goroutines
	ctx := r.Context()
	go client.WritePump(ctx)
	go client.ReadPump(ctx)
}

// ServeWSWithAuth handles WebSocket upgrade requests with authentication
func (h *Handler) ServeWSWithAuth(authFunc func(*http.Request) (string, error)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Authenticate user
		userID, err := authFunc(r)
		if err != nil {
			h.logger.Error("WebSocket authentication failed", "error", err)
			http.Error(w, "Authentication required", http.StatusUnauthorized)
			return
		}

		// Upgrade the connection to WebSocket
		upgrader := websocket.Upgrader{
			ReadBufferSize:  h.config.ReadBufferSize,
			WriteBufferSize: h.config.WriteBufferSize,
			CheckOrigin:     h.config.CheckOrigin,
		}

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			h.logger.Error("Failed to upgrade WebSocket connection", "error", err)
			http.Error(w, "Failed to upgrade WebSocket connection", http.StatusBadRequest)
			return
		}

		// Generate unique client ID
		clientID := uuid.New().String()

		// Create new client
		client := NewClient(conn, h.hub, clientID, h.logger)

		// Set client metadata from request
		client.IPAddress = h.getClientIP(r)
		client.UserAgent = r.UserAgent()
		client.SessionID = h.getSessionID(r)
		client.UserID = userID

		// Register client with hub
		h.hub.register <- client

		h.logger.Info("Authenticated WebSocket client connected", 
			"client_id", clientID,
			"user_id", userID,
			"ip_address", client.IPAddress,
		)

		// Start client goroutines
		ctx := r.Context()
		go client.WritePump(ctx)
		go client.ReadPump(ctx)
	}
}

// BroadcastToRoom broadcasts a message to all clients in a room
func (h *Handler) BroadcastToRoom(roomID string, messageType string, content string, data map[string]interface{}) {
	msg := Message{
		Type:      messageType,
		Content:   content,
		RoomID:    roomID,
		Timestamp: time.Now(),
		ClientID:  "system",
		Data:      data,
	}
	h.hub.BroadcastToRoom(roomID, msg)
}

// BroadcastToTopic broadcasts a message to all clients subscribed to a topic
func (h *Handler) BroadcastToTopic(topic string, messageType string, content string, data map[string]interface{}) {
	msg := Message{
		Type:      messageType,
		Content:   content,
		Topic:     topic,
		Timestamp: time.Now(),
		ClientID:  "system",
		Data:      data,
	}
	h.hub.BroadcastToSubscribers(topic, msg)
}

// SendToUser sends a message to all clients of a specific user
func (h *Handler) SendToUser(userID string, messageType string, content string, data map[string]interface{}) {
	msg := Message{
		Type:      messageType,
		Content:   content,
		Timestamp: time.Now(),
		ClientID:  "system",
		Data:      data,
	}

	// Find all clients for this user
	h.hub.mu.RLock()
	for client := range h.hub.clients {
		if client.UserID == userID {
			client.SendMessage(msg)
		}
	}
	h.hub.mu.RUnlock()
}

// BroadcastSystemMessage broadcasts a system message to all clients
func (h *Handler) BroadcastSystemMessage(messageType string, content string) {
	h.hub.BroadcastSystemMessage(content, messageType)
}

// GetHubStats returns hub statistics
func (h *Handler) GetHubStats() map[string]interface{} {
	return h.hub.GetHubStats()
}

// GetClientStats returns client statistics
func (h *Handler) GetClientStats() map[string]interface{} {
	h.hub.mu.RLock()
	defer h.hub.mu.RUnlock()

	clientStats := make(map[string]interface{})
	for client := range h.hub.clients {
		clientStats[client.ID] = client.GetClientInfo()
	}

	return map[string]interface{}{
		"total_clients": len(h.hub.clients),
		"clients":       clientStats,
	}
}

// CleanupInactiveClients removes inactive clients
func (h *Handler) CleanupInactiveClients() {
	h.hub.CleanupInactiveClients()
}

// StartCleanupRoutine starts a routine to clean up inactive clients
func (h *Handler) StartCleanupRoutine(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			h.CleanupInactiveClients()
		}
	}
}

// getClientIP extracts the client IP address from the request
func (h *Handler) getClientIP(r *http.Request) string {
	// Check for forwarded IP
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	
	// Fallback to remote address
	return r.RemoteAddr
}

// getSessionID extracts the session ID from the request
func (h *Handler) getSessionID(r *http.Request) string {
	// Check cookies first
	if cookie, err := r.Cookie("session_id"); err == nil {
		return cookie.Value
	}
	
	// Check headers
	if sessionID := r.Header.Get("X-Session-ID"); sessionID != "" {
		return sessionID
	}
	
	return ""
}

// getUserID extracts the user ID from the request
func (h *Handler) getUserID(r *http.Request) string {
	// Check headers
	if userID := r.Header.Get("X-User-ID"); userID != "" {
		return userID
	}
	
	// Check query parameters
	if userID := r.URL.Query().Get("user_id"); userID != "" {
		return userID
	}
	
	return ""
}

// WebSocketMiddleware provides WebSocket-specific middleware
func WebSocketMiddleware(logger domain.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Add WebSocket-specific headers
			w.Header().Set("Upgrade", "websocket")
			w.Header().Set("Connection", "Upgrade")
			
			logger.Debug("WebSocket middleware applied", 
				"path", r.URL.Path,
				"method", r.Method,
			)
			
			next.ServeHTTP(w, r)
		})
	}
}

// WebSocketStats represents WebSocket statistics
type WebSocketStats struct {
	TotalConnections    int64     `json:"total_connections"`
	ActiveConnections   int       `json:"active_connections"`
	TotalRooms          int       `json:"total_rooms"`
	TotalMessages       int64     `json:"total_messages"`
	AverageConnections  float64   `json:"average_connections"`
	PeakConnections     int       `json:"peak_connections"`
	LastCleanup         time.Time `json:"last_cleanup"`
	Uptime              time.Duration `json:"uptime"`
}

// GetWebSocketStats returns comprehensive WebSocket statistics
func (h *Handler) GetWebSocketStats() *WebSocketStats {
	hubStats := h.GetHubStats()
	
	return &WebSocketStats{
		TotalConnections:   int64(hubStats["total_clients"].(int)),
		ActiveConnections:  hubStats["total_clients"].(int),
		TotalRooms:         hubStats["total_rooms"].(int),
		TotalMessages:      0, // Would need to track this
		AverageConnections: 0, // Would need to track this over time
		PeakConnections:    0, // Would need to track this
		LastCleanup:        time.Now(), // Would need to track this
		Uptime:             time.Since(time.Now()), // Would need to track hub start time
	}
}
