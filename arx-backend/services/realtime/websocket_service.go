package realtime

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"gorm.io/gorm"
)

// MessageType represents the type of WebSocket message
type MessageType string

const (
	MessageTypeJoin       MessageType = "join"
	MessageTypeLeave      MessageType = "leave"
	MessageTypeEdit       MessageType = "edit"
	MessageTypeSync       MessageType = "sync"
	MessageTypeConflict   MessageType = "conflict"
	MessageTypeAnnotation MessageType = "annotation"
	MessageTypeComment    MessageType = "comment"
	MessageTypePresence   MessageType = "presence"
	MessageTypeLock       MessageType = "lock"
	MessageTypeUnlock     MessageType = "unlock"
	MessageTypeBroadcast  MessageType = "broadcast"
	MessageTypeError      MessageType = "error"
	MessageTypeHeartbeat  MessageType = "heartbeat"
)

// ConnectionStatus represents the status of a WebSocket connection
type ConnectionStatus string

const (
	ConnectionStatusConnected    ConnectionStatus = "connected"
	ConnectionStatusDisconnected ConnectionStatus = "disconnected"
	ConnectionStatusReconnecting ConnectionStatus = "reconnecting"
	ConnectionStatusError        ConnectionStatus = "error"
)

// WebSocketMessage represents a WebSocket message
type WebSocketMessage struct {
	Type      MessageType            `json:"type"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	SessionID string                 `json:"session_id"`
}

// WebSocketConnection represents a WebSocket connection
type WebSocketConnection struct {
	ID          string           `json:"id" gorm:"primaryKey"`
	UserID      string           `json:"user_id"`
	SessionID   string           `json:"session_id"`
	Username    string           `json:"username"`
	Status      ConnectionStatus `json:"status"`
	ConnectedAt time.Time        `json:"connected_at"`
	LastSeen    time.Time        `json:"last_seen"`
	Metadata    json.RawMessage  `json:"metadata"`
	CreatedAt   time.Time        `json:"created_at"`
	UpdatedAt   time.Time        `json:"updated_at"`
}

// WebSocketService handles WebSocket connections and real-time communication
type WebSocketService struct {
	db              *gorm.DB
	mu              sync.RWMutex
	connections     map[string]*websocket.Conn
	userConnections map[string]string          // user_id -> connection_id
	rooms           map[string]map[string]bool // room_id -> user_ids
	upgrader        websocket.Upgrader
	config          *WebSocketConfig
	messageChan     chan *WebSocketMessage
	stopChan        chan struct{}
	isRunning       bool
}

// WebSocketConfig holds configuration for the WebSocket service
type WebSocketConfig struct {
	Host              string        `json:"host"`
	Port              int           `json:"port"`
	ReadBufferSize    int           `json:"read_buffer_size"`
	WriteBufferSize   int           `json:"write_buffer_size"`
	MaxConnections    int           `json:"max_connections"`
	HeartbeatInterval time.Duration `json:"heartbeat_interval"`
	MessageTimeout    time.Duration `json:"message_timeout"`
	EnableCompression bool          `json:"enable_compression"`
	EnableOriginCheck bool          `json:"enable_origin_check"`
	AllowedOrigins    []string      `json:"allowed_origins"`
}

// NewWebSocketService creates a new WebSocket service
func NewWebSocketService(db *gorm.DB, config *WebSocketConfig) *WebSocketService {
	if config == nil {
		config = &WebSocketConfig{
			Host:              "localhost",
			Port:              8765,
			ReadBufferSize:    1024,
			WriteBufferSize:   1024,
			MaxConnections:    1000,
			HeartbeatInterval: 30 * time.Second,
			MessageTimeout:    10 * time.Second,
			EnableCompression: true,
			EnableOriginCheck: true,
			AllowedOrigins:    []string{"*"},
		}
	}

	upgrader := websocket.Upgrader{
		ReadBufferSize:  config.ReadBufferSize,
		WriteBufferSize: config.WriteBufferSize,
		CheckOrigin: func(r *http.Request) bool {
			if !config.EnableOriginCheck {
				return true
			}
			origin := r.Header.Get("Origin")
			for _, allowed := range config.AllowedOrigins {
				if allowed == "*" || allowed == origin {
					return true
				}
			}
			return false
		},
		EnableCompression: config.EnableCompression,
	}

	return &WebSocketService{
		db:              db,
		connections:     make(map[string]*websocket.Conn),
		userConnections: make(map[string]string),
		rooms:           make(map[string]map[string]bool),
		upgrader:        upgrader,
		config:          config,
		messageChan:     make(chan *WebSocketMessage, 1000),
		stopChan:        make(chan struct{}),
	}
}

// Start starts the WebSocket service
func (ws *WebSocketService) Start(ctx context.Context) error {
	ws.mu.Lock()
	defer ws.mu.Unlock()

	if ws.isRunning {
		return fmt.Errorf("WebSocket service is already running")
	}

	ws.isRunning = true

	// Start message processing loop
	go ws.messageProcessingLoop(ctx)

	// Start heartbeat loop
	go ws.heartbeatLoop(ctx)

	// Start cleanup loop
	go ws.cleanupLoop(ctx)

	return nil
}

// Stop stops the WebSocket service
func (ws *WebSocketService) Stop() {
	ws.mu.Lock()
	defer ws.mu.Unlock()

	if !ws.isRunning {
		return
	}

	ws.isRunning = false
	close(ws.stopChan)

	// Close all connections
	for connID, conn := range ws.connections {
		conn.Close()
		delete(ws.connections, connID)
	}
}

// HandleWebSocket handles a new WebSocket connection
func (ws *WebSocketService) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := ws.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Failed to upgrade connection: %v", err)
		return
	}

	// Extract user information from request
	userID := r.URL.Query().Get("user_id")
	sessionID := r.URL.Query().Get("session_id")
	username := r.URL.Query().Get("username")

	if userID == "" || sessionID == "" {
		ws.sendError(conn, "Missing user_id or session_id")
		conn.Close()
		return
	}

	// Check if user is already connected
	ws.mu.Lock()
	if existingConnID, exists := ws.userConnections[userID]; exists {
		if existingConn, ok := ws.connections[existingConnID]; ok {
			existingConn.Close()
			delete(ws.connections, existingConnID)
		}
		delete(ws.userConnections, userID)
	}
	ws.mu.Unlock()

	// Register new connection
	ws.mu.Lock()
	ws.connections[userID] = conn
	ws.userConnections[userID] = userID
	ws.mu.Unlock()

	// Save connection to database
	connection := &WebSocketConnection{
		ID:          userID,
		UserID:      userID,
		SessionID:   sessionID,
		Username:    username,
		Status:      ConnectionStatusConnected,
		ConnectedAt: time.Now(),
		LastSeen:    time.Now(),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	ws.db.Create(connection)

	// Send welcome message
	ws.sendMessage(conn, &WebSocketMessage{
		Type:      MessageTypeJoin,
		Data:      map[string]interface{}{"status": "connected"},
		Timestamp: time.Now(),
		UserID:    userID,
		SessionID: sessionID,
	})

	// Start connection handler
	go ws.handleConnection(userID, sessionID, conn)
}

// handleConnection handles a WebSocket connection
func (ws *WebSocketService) handleConnection(userID, sessionID string, conn *websocket.Conn) {
	defer func() {
		ws.disconnectUser(userID, "")
		conn.Close()
	}()

	for {
		select {
		case <-ws.stopChan:
			return
		default:
			// Set read timeout
			conn.SetReadDeadline(time.Now().Add(ws.config.MessageTimeout))

			// Read message
			_, messageBytes, err := conn.ReadMessage()
			if err != nil {
				if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
					log.Printf("WebSocket read error: %v", err)
				}
				return
			}

			// Parse message
			var message WebSocketMessage
			if err := json.Unmarshal(messageBytes, &message); err != nil {
				ws.sendError(conn, "Invalid message format")
				continue
			}

			// Update last seen
			ws.updateLastSeen(userID)

			// Process message
			ws.processMessage(&message)
		}
	}
}

// processMessage processes a WebSocket message
func (ws *WebSocketService) processMessage(message *WebSocketMessage) {
	// Send to message channel for processing
	select {
	case ws.messageChan <- message:
	default:
		log.Printf("Message channel full, dropping message from user %s", message.UserID)
	}
}

// messageProcessingLoop processes messages from the message channel
func (ws *WebSocketService) messageProcessingLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-ws.stopChan:
			return
		case message := <-ws.messageChan:
			ws.handleMessage(message)
		}
	}
}

// handleMessage handles a specific message type
func (ws *WebSocketService) handleMessage(message *WebSocketMessage) {
	switch message.Type {
	case MessageTypeJoin:
		ws.handleJoinRoom(message)
	case MessageTypeLeave:
		ws.handleLeaveRoom(message)
	case MessageTypeEdit:
		ws.handleEdit(message)
	case MessageTypeSync:
		ws.handleSync(message)
	case MessageTypeConflict:
		ws.handleConflict(message)
	case MessageTypeAnnotation:
		ws.handleAnnotation(message)
	case MessageTypeComment:
		ws.handleComment(message)
	case MessageTypePresence:
		ws.handlePresence(message)
	case MessageTypeLock:
		ws.handleLock(message)
	case MessageTypeUnlock:
		ws.handleUnlock(message)
	case MessageTypeBroadcast:
		ws.handleBroadcast(message)
	case MessageTypeHeartbeat:
		ws.handleHeartbeat(message)
	default:
		log.Printf("Unknown message type: %s", message.Type)
	}
}

// handleJoinRoom handles a join room message
func (ws *WebSocketService) handleJoinRoom(message *WebSocketMessage) {
	roomID, ok := message.Data["room_id"].(string)
	if !ok {
		return
	}

	ws.mu.Lock()
	if ws.rooms[roomID] == nil {
		ws.rooms[roomID] = make(map[string]bool)
	}
	ws.rooms[roomID][message.UserID] = true
	ws.mu.Unlock()

	// Broadcast user joined
	ws.broadcastToRoom(roomID, &WebSocketMessage{
		Type: MessageTypeJoin,
		Data: map[string]interface{}{
			"user_id":  message.UserID,
			"username": message.Data["username"],
			"room_id":  roomID,
		},
		Timestamp: time.Now(),
	})
}

// handleLeaveRoom handles a leave room message
func (ws *WebSocketService) handleLeaveRoom(message *WebSocketMessage) {
	roomID, ok := message.Data["room_id"].(string)
	if !ok {
		return
	}

	ws.mu.Lock()
	if room, exists := ws.rooms[roomID]; exists {
		delete(room, message.UserID)
		if len(room) == 0 {
			delete(ws.rooms, roomID)
		}
	}
	ws.mu.Unlock()

	// Broadcast user left
	ws.broadcastToRoom(roomID, &WebSocketMessage{
		Type: MessageTypeLeave,
		Data: map[string]interface{}{
			"user_id": message.UserID,
			"room_id": roomID,
		},
		Timestamp: time.Now(),
	})
}

// handleEdit handles an edit message
func (ws *WebSocketService) handleEdit(message *WebSocketMessage) {
	// Broadcast edit to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleSync handles a sync message
func (ws *WebSocketService) handleSync(message *WebSocketMessage) {
	// Broadcast sync to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleConflict handles a conflict message
func (ws *WebSocketService) handleConflict(message *WebSocketMessage) {
	// Broadcast conflict to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleAnnotation handles an annotation message
func (ws *WebSocketService) handleAnnotation(message *WebSocketMessage) {
	// Broadcast annotation to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleComment handles a comment message
func (ws *WebSocketService) handleComment(message *WebSocketMessage) {
	// Broadcast comment to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handlePresence handles a presence message
func (ws *WebSocketService) handlePresence(message *WebSocketMessage) {
	// Broadcast presence to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleLock handles a lock message
func (ws *WebSocketService) handleLock(message *WebSocketMessage) {
	// Broadcast lock to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleUnlock handles an unlock message
func (ws *WebSocketService) handleUnlock(message *WebSocketMessage) {
	// Broadcast unlock to room
	roomID, ok := message.Data["room_id"].(string)
	if ok {
		ws.broadcastToRoom(roomID, message)
	}
}

// handleBroadcast handles a broadcast message
func (ws *WebSocketService) handleBroadcast(message *WebSocketMessage) {
	// Broadcast to all users
	ws.broadcastToAll(message)
}

// handleHeartbeat handles a heartbeat message
func (ws *WebSocketService) handleHeartbeat(message *WebSocketMessage) {
	// Update last seen
	ws.updateLastSeen(message.UserID)
}

// broadcastToRoom broadcasts a message to all users in a room
func (ws *WebSocketService) broadcastToRoom(roomID string, message *WebSocketMessage) {
	ws.mu.RLock()
	room, exists := ws.rooms[roomID]
	if !exists {
		ws.mu.RUnlock()
		return
	}

	userIDs := make([]string, 0, len(room))
	for userID := range room {
		userIDs = append(userIDs, userID)
	}
	ws.mu.RUnlock()

	for _, userID := range userIDs {
		ws.sendToUser(userID, message)
	}
}

// broadcastToAll broadcasts a message to all connected users
func (ws *WebSocketService) broadcastToAll(message *WebSocketMessage) {
	ws.mu.RLock()
	userIDs := make([]string, 0, len(ws.userConnections))
	for userID := range ws.userConnections {
		userIDs = append(userIDs, userID)
	}
	ws.mu.RUnlock()

	for _, userID := range userIDs {
		ws.sendToUser(userID, message)
	}
}

// sendToUser sends a message to a specific user
func (ws *WebSocketService) sendToUser(userID string, message *WebSocketMessage) {
	ws.mu.RLock()
	connID, exists := ws.userConnections[userID]
	if !exists {
		ws.mu.RUnlock()
		return
	}

	conn, exists := ws.connections[connID]
	if !exists {
		ws.mu.RUnlock()
		return
	}
	ws.mu.RUnlock()

	ws.sendMessage(conn, message)
}

// sendMessage sends a message through a WebSocket connection
func (ws *WebSocketService) sendMessage(conn *websocket.Conn, message *WebSocketMessage) {
	messageBytes, err := json.Marshal(message)
	if err != nil {
		log.Printf("Failed to marshal message: %v", err)
		return
	}

	conn.SetWriteDeadline(time.Now().Add(ws.config.MessageTimeout))
	err = conn.WriteMessage(websocket.TextMessage, messageBytes)
	if err != nil {
		log.Printf("Failed to send message: %v", err)
	}
}

// sendError sends an error message through a WebSocket connection
func (ws *WebSocketService) sendError(conn *websocket.Conn, errorMessage string) {
	message := &WebSocketMessage{
		Type:      MessageTypeError,
		Data:      map[string]interface{}{"error": errorMessage},
		Timestamp: time.Now(),
	}
	ws.sendMessage(conn, message)
}

// disconnectUser disconnects a user
func (ws *WebSocketService) disconnectUser(userID, connID string) {
	ws.mu.Lock()
	delete(ws.connections, connID)
	delete(ws.userConnections, userID)

	// Remove user from all rooms
	for roomID, room := range ws.rooms {
		delete(room, userID)
		if len(room) == 0 {
			delete(ws.rooms, roomID)
		}
	}
	ws.mu.Unlock()

	// Update database
	ws.db.Model(&WebSocketConnection{}).Where("id = ?", connID).Updates(map[string]interface{}{
		"status":     ConnectionStatusDisconnected,
		"updated_at": time.Now(),
	})
}

// updateLastSeen updates the last seen timestamp for a user
func (ws *WebSocketService) updateLastSeen(userID string) {
	ws.mu.RLock()
	connID, exists := ws.userConnections[userID]
	ws.mu.RUnlock()

	if exists {
		ws.db.Model(&WebSocketConnection{}).Where("user_id = ?", userID).Updates(map[string]interface{}{
			"last_seen":  time.Now(),
			"updated_at": time.Now(),
		})
	}
}

// heartbeatLoop sends heartbeat messages to all connections
func (ws *WebSocketService) heartbeatLoop(ctx context.Context) {
	ticker := time.NewTicker(ws.config.HeartbeatInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ws.stopChan:
			return
		case <-ticker.C:
			ws.sendHeartbeats()
		}
	}
}

// sendHeartbeats sends heartbeat messages to all connections
func (ws *WebSocketService) sendHeartbeats() {
	message := &WebSocketMessage{
		Type:      MessageTypeHeartbeat,
		Data:      map[string]interface{}{"timestamp": time.Now().Unix()},
		Timestamp: time.Now(),
	}

	ws.broadcastToAll(message)
}

// cleanupLoop cleans up expired connections
func (ws *WebSocketService) cleanupLoop(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ws.stopChan:
			return
		case <-ticker.C:
			ws.cleanupExpiredConnections()
		}
	}
}

// cleanupExpiredConnections cleans up connections that haven't been seen recently
func (ws *WebSocketService) cleanupExpiredConnections() {
	expiredTime := time.Now().Add(-10 * time.Minute)

	var expiredConnections []WebSocketConnection
	ws.db.Where("last_seen < ? AND status = ?", expiredTime, ConnectionStatusConnected).Find(&expiredConnections)

	for _, conn := range expiredConnections {
		ws.mu.Lock()
		if connID, exists := ws.userConnections[conn.UserID]; exists {
			if wsConn, ok := ws.connections[connID]; ok {
				wsConn.Close()
				delete(ws.connections, connID)
			}
			delete(ws.userConnections, conn.UserID)
		}
		ws.mu.Unlock()

		ws.db.Model(&conn).Updates(map[string]interface{}{
			"status":     ConnectionStatusDisconnected,
			"updated_at": time.Now(),
		})
	}
}

// GetConnectionStats gets connection statistics
func (ws *WebSocketService) GetConnectionStats() map[string]interface{} {
	ws.mu.RLock()
	defer ws.mu.RUnlock()

	var totalConnections, activeConnections int64
	ws.db.Model(&WebSocketConnection{}).Count(&totalConnections)
	ws.db.Model(&WebSocketConnection{}).Where("status = ?", ConnectionStatusConnected).Count(&activeConnections)

	return map[string]interface{}{
		"total_connections":   totalConnections,
		"active_connections":  activeConnections,
		"current_connections": len(ws.connections),
		"total_rooms":         len(ws.rooms),
		"is_running":          ws.isRunning,
	}
}

// generateConnectionID generates a unique connection ID
func generateConnectionID() string {
	return fmt.Sprintf("conn_%d", time.Now().UnixNano())
}
