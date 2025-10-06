package websocket

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// Hub maintains the set of active clients and broadcasts messages to the clients
type Hub struct {
	// Registered clients
	clients map[*Client]bool

	// Inbound messages from the clients
	broadcast chan []byte

	// Register requests from the clients
	register chan *Client

	// Unregister requests from clients
	unregister chan *Client

	// Room management
	rooms map[string]map[*Client]bool

	// Client subscriptions
	subscriptions map[*Client]map[string]bool

	// Message history
	messageHistory map[string][]Message

	// Configuration
	config *HubConfig

	// Logger
	logger domain.Logger

	// Mutex for thread safety
	mu sync.RWMutex
}

// HubConfig represents WebSocket hub configuration
type HubConfig struct {
	MaxClients        int           `json:"max_clients"`
	MessageBufferSize int           `json:"message_buffer_size"`
	PingPeriod        time.Duration `json:"ping_period"`
	PongWait          time.Duration `json:"pong_wait"`
	WriteWait         time.Duration `json:"write_wait"`
	MaxMessageSize    int64         `json:"max_message_size"`
	EnableHistory     bool          `json:"enable_history"`
	HistorySize       int           `json:"history_size"`
}

// DefaultHubConfig returns default hub configuration
func DefaultHubConfig() *HubConfig {
	return &HubConfig{
		MaxClients:        1000,
		MessageBufferSize: 256,
		PingPeriod:        54 * time.Second,
		PongWait:          60 * time.Second,
		WriteWait:         10 * time.Second,
		MaxMessageSize:    512,
		EnableHistory:     true,
		HistorySize:       100,
	}
}

// NewHub creates a new WebSocket hub
func NewHub(config *HubConfig, logger domain.Logger) *Hub {
	if config == nil {
		config = DefaultHubConfig()
	}

	return &Hub{
		clients:        make(map[*Client]bool),
		broadcast:      make(chan []byte, config.MessageBufferSize),
		register:       make(chan *Client),
		unregister:     make(chan *Client),
		rooms:          make(map[string]map[*Client]bool),
		subscriptions:  make(map[*Client]map[string]bool),
		messageHistory: make(map[string][]Message),
		config:         config,
		logger:         logger,
	}
}

// Run starts the hub and handles client connections
func (h *Hub) Run(ctx context.Context) {
	h.logger.Info("WebSocket hub started")

	for {
		select {
		case <-ctx.Done():
			h.logger.Info("WebSocket hub shutting down")
			return

		case client := <-h.register:
			h.registerClient(client)

		case client := <-h.unregister:
			h.unregisterClient(client)

		case message := <-h.broadcast:
			h.broadcastMessage(message)
		}
	}
}

// registerClient registers a new client
func (h *Hub) registerClient(client *Client) {
	h.mu.Lock()
	defer h.mu.Unlock()

	// Check if we've reached max clients
	if len(h.clients) >= h.config.MaxClients {
		h.logger.Warn("Maximum clients reached, rejecting connection", "client_id", client.ID)
		client.Close()
		return
	}

	h.clients[client] = true
	h.subscriptions[client] = make(map[string]bool)

	h.logger.Info("Client registered", "client_id", client.ID, "total_clients", len(h.clients))

	// Send welcome message
	welcomeMsg := Message{
		Type:      "welcome",
		Content:   fmt.Sprintf("Welcome! You are client %s", client.ID),
		Timestamp: time.Now(),
		ClientID:  "system",
	}
	client.send <- welcomeMsg
}

// unregisterClient unregisters a client
func (h *Hub) unregisterClient(client *Client) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if _, ok := h.clients[client]; ok {
		delete(h.clients, client)
		delete(h.subscriptions, client)
		close(client.send)

		// Remove client from all rooms
		for roomID, roomClients := range h.rooms {
			if _, exists := roomClients[client]; exists {
				delete(roomClients, client)
				if len(roomClients) == 0 {
					delete(h.rooms, roomID)
				}
			}
		}

		h.logger.Info("Client unregistered", "client_id", client.ID, "total_clients", len(h.clients))
	}
}

// broadcastMessage broadcasts a message to all connected clients
func (h *Hub) broadcastMessage(message []byte) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for client := range h.clients {
		select {
		case client.send <- Message{
			Type:      "broadcast",
			Content:   string(message),
			Timestamp: time.Now(),
			ClientID:  "system",
		}:
		default:
			close(client.send)
			delete(h.clients, client)
		}
	}
}

// BroadcastToRoom broadcasts a message to all clients in a specific room
func (h *Hub) BroadcastToRoom(roomID string, message Message) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if roomClients, exists := h.rooms[roomID]; exists {
		for client := range roomClients {
			select {
			case client.send <- message:
			default:
				close(client.send)
				delete(h.clients, client)
			}
		}
	}

	// Store message in history if enabled
	if h.config.EnableHistory {
		h.storeMessage(roomID, message)
	}
}

// BroadcastToSubscribers broadcasts a message to clients subscribed to a topic
func (h *Hub) BroadcastToSubscribers(topic string, message Message) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for client, subscriptions := range h.subscriptions {
		if subscriptions[topic] {
			select {
			case client.send <- message:
			default:
				close(client.send)
				delete(h.clients, client)
			}
		}
	}
}

// JoinRoom adds a client to a room
func (h *Hub) JoinRoom(client *Client, roomID string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if h.rooms[roomID] == nil {
		h.rooms[roomID] = make(map[*Client]bool)
	}

	h.rooms[roomID][client] = true

	h.logger.Info("Client joined room", "client_id", client.ID, "room_id", roomID)

	// Send room join confirmation
	joinMsg := Message{
		Type:      "room_joined",
		Content:   fmt.Sprintf("Joined room: %s", roomID),
		RoomID:    roomID,
		Timestamp: time.Now(),
		ClientID:  "system",
	}
	client.send <- joinMsg
}

// LeaveRoom removes a client from a room
func (h *Hub) LeaveRoom(client *Client, roomID string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if roomClients, exists := h.rooms[roomID]; exists {
		delete(roomClients, client)
		if len(roomClients) == 0 {
			delete(h.rooms, roomID)
		}
	}

	h.logger.Info("Client left room", "client_id", client.ID, "room_id", roomID)

	// Send room leave confirmation
	leaveMsg := Message{
		Type:      "room_left",
		Content:   fmt.Sprintf("Left room: %s", roomID),
		RoomID:    roomID,
		Timestamp: time.Now(),
		ClientID:  "system",
	}
	client.send <- leaveMsg
}

// SubscribeToTopic subscribes a client to a topic
func (h *Hub) SubscribeToTopic(client *Client, topic string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if h.subscriptions[client] == nil {
		h.subscriptions[client] = make(map[string]bool)
	}

	h.subscriptions[client][topic] = true

	h.logger.Info("Client subscribed to topic", "client_id", client.ID, "topic", topic)

	// Send subscription confirmation
	subMsg := Message{
		Type:      "subscribed",
		Content:   fmt.Sprintf("Subscribed to topic: %s", topic),
		Topic:     topic,
		Timestamp: time.Now(),
		ClientID:  "system",
	}
	client.send <- subMsg
}

// UnsubscribeFromTopic unsubscribes a client from a topic
func (h *Hub) UnsubscribeFromTopic(client *Client, topic string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if subscriptions, exists := h.subscriptions[client]; exists {
		delete(subscriptions, topic)
	}

	h.logger.Info("Client unsubscribed from topic", "client_id", client.ID, "topic", topic)

	// Send unsubscription confirmation
	unsubMsg := Message{
		Type:      "unsubscribed",
		Content:   fmt.Sprintf("Unsubscribed from topic: %s", topic),
		Topic:     topic,
		Timestamp: time.Now(),
		ClientID:  "system",
	}
	client.send <- unsubMsg
}

// GetClientCount returns the number of connected clients
func (h *Hub) GetClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// GetRoomCount returns the number of active rooms
func (h *Hub) GetRoomCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.rooms)
}

// GetRoomClients returns the clients in a specific room
func (h *Hub) GetRoomClients(roomID string) []string {
	h.mu.RLock()
	defer h.mu.RUnlock()

	var clientIDs []string
	if roomClients, exists := h.rooms[roomID]; exists {
		for client := range roomClients {
			clientIDs = append(clientIDs, client.ID)
		}
	}
	return clientIDs
}

// GetClientSubscriptions returns the topics a client is subscribed to
func (h *Hub) GetClientSubscriptions(client *Client) []string {
	h.mu.RLock()
	defer h.mu.RUnlock()

	var topics []string
	if subscriptions, exists := h.subscriptions[client]; exists {
		for topic := range subscriptions {
			topics = append(topics, topic)
		}
	}
	return topics
}

// GetHubStats returns hub statistics
func (h *Hub) GetHubStats() map[string]any {
	h.mu.RLock()
	defer h.mu.RUnlock()

	roomStats := make(map[string]int)
	for roomID, clients := range h.rooms {
		roomStats[roomID] = len(clients)
	}

	return map[string]any{
		"total_clients":   len(h.clients),
		"total_rooms":     len(h.rooms),
		"room_stats":      roomStats,
		"config":          h.config,
		"message_history": len(h.messageHistory),
	}
}

// storeMessage stores a message in the history
func (h *Hub) storeMessage(roomID string, message Message) {
	if h.messageHistory[roomID] == nil {
		h.messageHistory[roomID] = make([]Message, 0, h.config.HistorySize)
	}

	h.messageHistory[roomID] = append(h.messageHistory[roomID], message)

	// Trim history if it exceeds the configured size
	if len(h.messageHistory[roomID]) > h.config.HistorySize {
		h.messageHistory[roomID] = h.messageHistory[roomID][1:]
	}
}

// GetMessageHistory returns the message history for a room
func (h *Hub) GetMessageHistory(roomID string) []Message {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if history, exists := h.messageHistory[roomID]; exists {
		// Return a copy to avoid race conditions
		result := make([]Message, len(history))
		copy(result, history)
		return result
	}
	return []Message{}
}

// SendDirectMessage sends a direct message to a specific client
func (h *Hub) SendDirectMessage(clientID string, message Message) bool {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for client := range h.clients {
		if client.ID == clientID {
			select {
			case client.send <- message:
				return true
			default:
				return false
			}
		}
	}
	return false
}

// BroadcastSystemMessage broadcasts a system message to all clients
func (h *Hub) BroadcastSystemMessage(content string, messageType string) {
	h.broadcastMessage([]byte(content))
}

// CleanupInactiveClients removes inactive clients
func (h *Hub) CleanupInactiveClients() {
	h.mu.Lock()
	defer h.mu.Unlock()

	for client := range h.clients {
		if time.Since(client.LastPong) > h.config.PongWait*2 {
			h.logger.Info("Removing inactive client", "client_id", client.ID)
			delete(h.clients, client)
			close(client.send)
		}
	}
}
