package messaging

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

// WebSocketHub manages WebSocket connections following Clean Architecture principles
type WebSocketHub struct {
	// Registered clients
	clients map[*Client]bool

	// Register requests from clients
	register chan *Client

	// Unregister requests from clients
	unregister chan *Client

	// Broadcast messages to all clients
	broadcast chan []byte

	// Room-based messaging
	rooms map[string]map[*Client]bool

	// Mutex for thread-safe operations
	mutex sync.RWMutex

	// Configuration
	config *WebSocketConfig
}

// Client represents a WebSocket client connection
type Client struct {
	// WebSocket connection
	conn *websocket.Conn

	// Buffered channel of outbound messages
	send chan []byte

	// Client information
	ID       string    `json:"id"`
	UserID   string    `json:"user_id"`
	Room     string    `json:"room"`
	JoinedAt time.Time `json:"joined_at"`

	// Hub reference
	hub *WebSocketHub
}

// WebSocketConfig holds WebSocket configuration
type WebSocketConfig struct {
	ReadBufferSize  int `json:"read_buffer_size"`
	WriteBufferSize int `json:"write_buffer_size"`
	CheckOrigin     func(r *http.Request) bool
	PingPeriod      time.Duration `json:"ping_period"`
	PongWait        time.Duration `json:"pong_wait"`
	WriteWait       time.Duration `json:"write_wait"`
	MaxMessageSize  int64         `json:"max_message_size"`
}

// DefaultWebSocketConfig returns default WebSocket configuration
func DefaultWebSocketConfig() *WebSocketConfig {
	return &WebSocketConfig{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin: func(r *http.Request) bool {
			return true // Allow all origins in development
		},
		PingPeriod:     54 * time.Second,
		PongWait:       60 * time.Second,
		WriteWait:      10 * time.Second,
		MaxMessageSize: 512,
	}
}

// NewWebSocketHub creates a new WebSocket hub
func NewWebSocketHub(config *WebSocketConfig) *WebSocketHub {
	if config == nil {
		config = DefaultWebSocketConfig()
	}

	return &WebSocketHub{
		clients:    make(map[*Client]bool),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan []byte),
		rooms:      make(map[string]map[*Client]bool),
		config:     config,
	}
}

// Run starts the WebSocket hub
func (h *WebSocketHub) Run() {
	for {
		select {
		case client := <-h.register:
			h.registerClient(client)

		case client := <-h.unregister:
			h.unregisterClient(client)

		case message := <-h.broadcast:
			h.broadcastToAll(message)
		}
	}
}

// HandleWebSocket handles WebSocket connections
func (h *WebSocketHub) HandleWebSocket(w http.ResponseWriter, r *http.Request) error {
	// Upgrade HTTP connection to WebSocket
	upgrader := websocket.Upgrader{
		ReadBufferSize:  h.config.ReadBufferSize,
		WriteBufferSize: h.config.WriteBufferSize,
		CheckOrigin:     h.config.CheckOrigin,
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return fmt.Errorf("failed to upgrade connection: %w", err)
	}

	// Extract user information from request context or headers
	userID := h.extractUserID(r)
	room := h.extractRoom(r)

	// Create client
	client := &Client{
		conn:     conn,
		send:     make(chan []byte, 256),
		ID:       uuid.New().String(),
		UserID:   userID,
		Room:     room,
		JoinedAt: time.Now(),
		hub:      h,
	}

	// Register client
	h.register <- client

	// Start goroutines for reading and writing
	go client.writePump()
	go client.readPump()

	return nil
}

// BroadcastToRoom broadcasts a message to all clients in a room
func (h *WebSocketHub) BroadcastToRoom(room string, message interface{}) error {
	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	h.mutex.RLock()
	roomClients, exists := h.rooms[room]
	h.mutex.RUnlock()

	if !exists {
		return fmt.Errorf("room %s does not exist", room)
	}

	h.mutex.RLock()
	for client := range roomClients {
		select {
		case client.send <- data:
		default:
			close(client.send)
			delete(h.clients, client)
		}
	}
	h.mutex.RUnlock()

	return nil
}

// BroadcastToUser broadcasts a message to a specific user
func (h *WebSocketHub) BroadcastToUser(userID string, message interface{}) error {
	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	h.mutex.RLock()
	for client := range h.clients {
		if client.UserID == userID {
			select {
			case client.send <- data:
			default:
				close(client.send)
				delete(h.clients, client)
			}
		}
	}
	h.mutex.RUnlock()

	return nil
}

// BroadcastToAll broadcasts a message to all connected clients
func (h *WebSocketHub) BroadcastToAll(message interface{}) error {
	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	h.broadcast <- data
	return nil
}

// JoinRoom adds a client to a room
func (h *WebSocketHub) JoinRoom(userID, room string) error {
	h.mutex.Lock()
	defer h.mutex.Unlock()

	// Find client by userID
	var targetClient *Client
	for client := range h.clients {
		if client.UserID == userID {
			targetClient = client
			break
		}
	}

	if targetClient == nil {
		return fmt.Errorf("client not found for user %s", userID)
	}

	// Remove from old room if exists
	if targetClient.Room != "" {
		if roomClients, exists := h.rooms[targetClient.Room]; exists {
			delete(roomClients, targetClient)
			if len(roomClients) == 0 {
				delete(h.rooms, targetClient.Room)
			}
		}
	}

	// Add to new room
	targetClient.Room = room
	if h.rooms[room] == nil {
		h.rooms[room] = make(map[*Client]bool)
	}
	h.rooms[room][targetClient] = true

	return nil
}

// LeaveRoom removes a client from a room
func (h *WebSocketHub) LeaveRoom(userID, room string) error {
	h.mutex.Lock()
	defer h.mutex.Unlock()

	// Find client by userID
	var targetClient *Client
	for client := range h.clients {
		if client.UserID == userID {
			targetClient = client
			break
		}
	}

	if targetClient == nil {
		return fmt.Errorf("client not found for user %s", userID)
	}

	// Remove from room
	if roomClients, exists := h.rooms[room]; exists {
		delete(roomClients, targetClient)
		if len(roomClients) == 0 {
			delete(h.rooms, room)
		}
	}

	targetClient.Room = ""
	return nil
}

// GetRoomUsers returns all users in a room
func (h *WebSocketHub) GetRoomUsers(room string) ([]string, error) {
	h.mutex.RLock()
	defer h.mutex.RUnlock()

	roomClients, exists := h.rooms[room]
	if !exists {
		return nil, fmt.Errorf("room %s does not exist", room)
	}

	users := make([]string, 0, len(roomClients))
	for client := range roomClients {
		users = append(users, client.UserID)
	}

	return users, nil
}

// IsHealthy checks if the WebSocket hub is healthy
func (h *WebSocketHub) IsHealthy() bool {
	h.mutex.RLock()
	defer h.mutex.RUnlock()

	return len(h.clients) >= 0 // Always healthy if we can access the mutex
}

// GetStats returns WebSocket hub statistics
func (h *WebSocketHub) GetStats() map[string]interface{} {
	h.mutex.RLock()
	defer h.mutex.RUnlock()

	return map[string]interface{}{
		"total_clients": len(h.clients),
		"total_rooms":   len(h.rooms),
		"rooms":         h.getRoomStats(),
	}
}

// Helper methods
func (h *WebSocketHub) registerClient(client *Client) {
	h.mutex.Lock()
	defer h.mutex.Unlock()

	h.clients[client] = true

	// Add to room if specified
	if client.Room != "" {
		if h.rooms[client.Room] == nil {
			h.rooms[client.Room] = make(map[*Client]bool)
		}
		h.rooms[client.Room][client] = true
	}
}

func (h *WebSocketHub) unregisterClient(client *Client) {
	h.mutex.Lock()
	defer h.mutex.Unlock()

	if _, ok := h.clients[client]; ok {
		delete(h.clients, client)
		close(client.send)

		// Remove from room
		if client.Room != "" {
			if roomClients, exists := h.rooms[client.Room]; exists {
				delete(roomClients, client)
				if len(roomClients) == 0 {
					delete(h.rooms, client.Room)
				}
			}
		}
	}
}

func (h *WebSocketHub) broadcastToAll(message []byte) {
	h.mutex.RLock()
	for client := range h.clients {
		select {
		case client.send <- message:
		default:
			close(client.send)
			delete(h.clients, client)
		}
	}
	h.mutex.RUnlock()
}

func (h *WebSocketHub) extractUserID(r *http.Request) string {
	// Try to get from context first (set by auth middleware)
	if userID := r.Context().Value("user_id"); userID != nil {
		if id, ok := userID.(string); ok {
			return id
		}
	}

	// Fallback to header
	return r.Header.Get("X-User-ID")
}

func (h *WebSocketHub) extractRoom(r *http.Request) string {
	// Try to get from query parameter
	if room := r.URL.Query().Get("room"); room != "" {
		return room
	}

	// Fallback to header
	return r.Header.Get("X-Room")
}

func (h *WebSocketHub) getRoomStats() map[string]int {
	stats := make(map[string]int)
	for room, clients := range h.rooms {
		stats[room] = len(clients)
	}
	return stats
}

// Client methods
func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	c.conn.SetReadLimit(c.hub.config.MaxMessageSize)
	c.conn.SetReadDeadline(time.Now().Add(c.hub.config.PongWait))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(c.hub.config.PongWait))
		return nil
	})

	for {
		_, _, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				// Log unexpected close errors
			}
			break
		}
	}
}

func (c *Client) writePump() {
	ticker := time.NewTicker(c.hub.config.PingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(c.hub.config.WriteWait))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			// Add queued messages to the current websocket message
			n := len(c.send)
			for i := 0; i < n; i++ {
				w.Write([]byte{'\n'})
				w.Write(<-c.send)
			}

			if err := w.Close(); err != nil {
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
