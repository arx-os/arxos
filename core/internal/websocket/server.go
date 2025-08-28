// Package websocket provides layer-aware WebSocket server
package websocket

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/realtime"
)

// Server represents a layer-aware WebSocket server
type Server struct {
	upgrader      websocket.Upgrader
	clients       map[string]*Client
	layerManager  *LayerManager
	hub           *Hub
	updateEngine  *realtime.UpdateEngine
	mu            sync.RWMutex
	config        ServerConfig
}

// ServerConfig contains server configuration
type ServerConfig struct {
	Port              int
	MaxClients        int
	PingInterval      time.Duration
	WriteTimeout      time.Duration
	MaxMessageSize    int64
	EnableCompression bool
}

// Client represents a connected WebSocket client
type Client struct {
	ID         string
	conn       *websocket.Conn
	context    *LayerContext
	send       chan []byte
	hub        *Hub
	server     *Server
	mu         sync.RWMutex
}

// Hub manages client connections and message broadcasting
type Hub struct {
	clients    map[string]*Client
	broadcast  chan *BroadcastMessage
	register   chan *Client
	unregister chan *Client
	mu         sync.RWMutex
}

// BroadcastMessage represents a message to broadcast
type BroadcastMessage struct {
	Message      *Message
	TargetLayer  *Layer        // nil for all layers
	TargetClient *string       // nil for all clients
	Filter       MessageFilter // Optional filter function
}

// MessageFilter filters messages based on context
type MessageFilter func(*LayerContext, *Message) bool

// DefaultServerConfig returns default server configuration
func DefaultServerConfig() ServerConfig {
	return ServerConfig{
		Port:              8080,
		MaxClients:        1000,
		PingInterval:      30 * time.Second,
		WriteTimeout:      10 * time.Second,
		MaxMessageSize:    1024 * 1024, // 1MB
		EnableCompression: true,
	}
}

// NewServer creates a new WebSocket server
func NewServer(config ServerConfig, updateEngine *realtime.UpdateEngine) *Server {
	hub := &Hub{
		clients:    make(map[string]*Client),
		broadcast:  make(chan *BroadcastMessage, 256),
		register:   make(chan *Client, 16),
		unregister: make(chan *Client, 16),
	}
	
	server := &Server{
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				// In production, implement proper origin checking
				return true
			},
			EnableCompression: config.EnableCompression,
		},
		clients:      make(map[string]*Client),
		layerManager: NewLayerManager(),
		hub:          hub,
		updateEngine: updateEngine,
		config:       config,
	}
	
	return server
}

// Start starts the WebSocket server
func (s *Server) Start() error {
	// Start hub
	go s.hub.run()
	
	// Start update processor if available
	if s.updateEngine != nil {
		go s.processRealtimeUpdates()
	}
	
	// Setup HTTP handlers
	http.HandleFunc("/ws", s.handleWebSocket)
	http.HandleFunc("/ws/stats", s.handleStats)
	
	addr := fmt.Sprintf(":%d", s.config.Port)
	log.Printf("[WebSocket] Server starting on %s", addr)
	
	return http.ListenAndServe(addr, nil)
}

// handleWebSocket handles WebSocket connection upgrades
func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	// Parse layer context from query params
	layer := s.parseLayer(r.URL.Query().Get("layer"))
	precision := s.parsePrecision(r.URL.Query().Get("precision"))
	
	// Default viewport
	viewport := Bounds{
		MinX: -100, MaxX: 100,
		MinY: -100, MaxY: 100,
		MinZ: 0, MaxZ: 10,
	}
	
	// Upgrade connection
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("[WebSocket] Failed to upgrade: %v", err)
		return
	}
	
	// Create client
	client := &Client{
		ID:   generateClientID(),
		conn: conn,
		context: NewLayerContext(layer, precision, viewport, 1.0),
		send: make(chan []byte, 256),
		hub:  s.hub,
		server: s,
	}
	
	// Register client
	s.registerClient(client)
	
	// Start client goroutines
	go client.writePump()
	go client.readPump()
	
	// Send initial configuration
	s.sendInitialConfig(client)
}

// registerClient registers a new client
func (s *Server) registerClient(client *Client) {
	s.mu.Lock()
	s.clients[client.ID] = client
	s.mu.Unlock()
	
	s.layerManager.RegisterClient(client.context)
	s.hub.register <- client
	
	log.Printf("[WebSocket] Client %s connected (Layer: %s, Precision: %s)",
		client.ID, client.context.Layer, client.context.Precision)
}

// unregisterClient removes a client
func (s *Server) unregisterClient(client *Client) {
	s.mu.Lock()
	delete(s.clients, client.ID)
	s.mu.Unlock()
	
	s.layerManager.UnregisterClient(client.ID)
	close(client.send)
	
	log.Printf("[WebSocket] Client %s disconnected", client.ID)
}

// sendInitialConfig sends initial configuration to client
func (s *Server) sendInitialConfig(client *Client) {
	caps := GetLayerCapabilities(client.context.Layer)
	
	config := map[string]interface{}{
		"client_id":    client.ID,
		"layer":        client.context.Layer,
		"precision":    client.context.Precision,
		"capabilities": caps,
		"timestamp":    time.Now(),
	}
	
	configJSON, _ := json.Marshal(config)
	
	msg := &Message{
		ID:        generateMessageID(),
		Type:      MessageTypeSnapshot,
		Context:   *client.context,
		Payload:   configJSON,
		Priority:  PriorityHigh,
		Timestamp: time.Now(),
	}
	
	s.sendToClient(client, msg)
}

// sendToClient sends a message to a specific client
func (s *Server) sendToClient(client *Client, msg *Message) {
	// Adapt message for client's context
	adapted := s.adaptMessage(msg, client.context)
	
	data, err := json.Marshal(adapted)
	if err != nil {
		log.Printf("[WebSocket] Failed to marshal message: %v", err)
		return
	}
	
	select {
	case client.send <- data:
	default:
		// Client send channel full, drop message
		log.Printf("[WebSocket] Dropped message for client %s (buffer full)", client.ID)
	}
}

// adaptMessage adapts a message for a specific layer context
func (s *Server) adaptMessage(msg *Message, ctx *LayerContext) *Message {
	adapted := *msg
	adapted.Context = *ctx
	
	// Apply layer-specific transformations
	switch ctx.Layer {
	case LayerCLI:
		// Simplify to text only
		adapted.Payload = s.simplifyToCLI(msg.Payload)
		
	case LayerASCII:
		// Convert to ASCII representation
		adapted.Payload = s.convertToASCII(msg.Payload)
		
	case LayerWebGL:
		// Optimize for 3D rendering
		adapted.Payload = s.optimizeFor3D(msg.Payload, ctx)
		
	case LayerAR, LayerVR:
		// Apply spatial filtering based on viewport
		adapted.Payload = s.filterByViewport(msg.Payload, ctx.Viewport)
	}
	
	// Apply precision filtering
	adapted.Payload = s.applyPrecisionFilter(adapted.Payload, ctx.Precision)
	
	return &adapted
}

// Client pump methods

func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()
	
	c.conn.SetReadLimit(c.server.config.MaxMessageSize)
	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})
	
	for {
		var msg Message
		err := c.conn.ReadJSON(&msg)
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("[WebSocket] Client %s error: %v", c.ID, err)
			}
			break
		}
		
		// Handle message based on type
		c.handleMessage(&msg)
	}
}

func (c *Client) writePump() {
	ticker := time.NewTicker(c.server.config.PingInterval)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()
	
	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(c.server.config.WriteTimeout))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			
			c.conn.WriteMessage(websocket.TextMessage, message)
			
		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(c.server.config.WriteTimeout))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (c *Client) handleMessage(msg *Message) {
	switch msg.Type {
	case MessageTypeLayerChange:
		c.handleLayerChange(msg)
		
	case MessageTypeViewportChange:
		c.handleViewportChange(msg)
		
	case MessageTypePrecisionChange:
		c.handlePrecisionChange(msg)
		
	case MessageTypeSubscribe:
		c.handleSubscribe(msg)
		
	case MessageTypePing:
		c.handlePing()
		
	default:
		log.Printf("[WebSocket] Unknown message type: %s", msg.Type)
	}
}

func (c *Client) handleLayerChange(msg *Message) {
	var params struct {
		Layer Layer `json:"layer"`
	}
	
	if err := json.Unmarshal(msg.Payload, &params); err != nil {
		return
	}
	
	c.mu.Lock()
	oldLayer := c.context.Layer
	c.context.Layer = params.Layer
	c.mu.Unlock()
	
	// Update in layer manager
	c.server.layerManager.UpdateContext(c.ID, c.context)
	
	log.Printf("[WebSocket] Client %s changed layer: %s -> %s", 
		c.ID, oldLayer, params.Layer)
	
	// Send new capabilities
	c.server.sendInitialConfig(c)
}

func (c *Client) handleViewportChange(msg *Message) {
	var viewport Bounds
	if err := json.Unmarshal(msg.Payload, &viewport); err != nil {
		return
	}
	
	c.mu.Lock()
	c.context.Viewport = viewport
	c.mu.Unlock()
	
	c.server.layerManager.UpdateContext(c.ID, c.context)
}

func (c *Client) handlePrecisionChange(msg *Message) {
	var params struct {
		Precision Precision `json:"precision"`
	}
	
	if err := json.Unmarshal(msg.Payload, &params); err != nil {
		return
	}
	
	c.mu.Lock()
	c.context.Precision = params.Precision
	c.mu.Unlock()
	
	c.server.layerManager.UpdateContext(c.ID, c.context)
}

func (c *Client) handleSubscribe(msg *Message) {
	// Handle subscription requests
	// Implementation depends on what clients can subscribe to
}

func (c *Client) handlePing() {
	pong := &Message{
		ID:        generateMessageID(),
		Type:      MessageTypePong,
		Context:   *c.context,
		Timestamp: time.Now(),
	}
	
	c.server.sendToClient(c, pong)
}

// Hub run method

func (h *Hub) run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client.ID] = client
			h.mu.Unlock()
			
		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				client.server.unregisterClient(client)
			}
			h.mu.Unlock()
			
		case broadcast := <-h.broadcast:
			h.handleBroadcast(broadcast)
		}
	}
}

func (h *Hub) handleBroadcast(broadcast *BroadcastMessage) {
	h.mu.RLock()
	clients := make([]*Client, 0, len(h.clients))
	for _, client := range h.clients {
		clients = append(clients, client)
	}
	h.mu.RUnlock()
	
	for _, client := range clients {
		// Check if message should be sent to this client
		if broadcast.TargetClient != nil && client.ID != *broadcast.TargetClient {
			continue
		}
		
		if broadcast.TargetLayer != nil && client.context.Layer != *broadcast.TargetLayer {
			continue
		}
		
		if broadcast.Filter != nil && !broadcast.Filter(client.context, broadcast.Message) {
			continue
		}
		
		client.server.sendToClient(client, broadcast.Message)
	}
}

// Broadcast sends a message to all matching clients
func (s *Server) Broadcast(msg *Message, filter MessageFilter) {
	s.hub.broadcast <- &BroadcastMessage{
		Message: msg,
		Filter:  filter,
	}
}

// BroadcastToLayer sends a message to all clients in a layer
func (s *Server) BroadcastToLayer(layer Layer, msg *Message) {
	s.hub.broadcast <- &BroadcastMessage{
		Message:     msg,
		TargetLayer: &layer,
	}
}

// processRealtimeUpdates processes real-time updates
func (s *Server) processRealtimeUpdates() {
	if s.updateEngine == nil {
		return
	}
	
	// Subscribe to all updates
	subscriber, err := s.updateEngine.Subscribe(realtime.SubscriptionFilter{})
	if err != nil {
		log.Printf("[WebSocket] Failed to subscribe to updates: %v", err)
		return
	}
	
	for update := range subscriber.Channel {
		// Convert realtime update to WebSocket message
		msg := s.convertRealtimeUpdate(update)
		
		// Broadcast based on update priority
		if update.Priority >= realtime.PriorityHigh {
			// Send to all layers
			s.Broadcast(msg, nil)
		} else {
			// Send only to appropriate layers based on detail level
			s.Broadcast(msg, func(ctx *LayerContext, m *Message) bool {
				// CLI and ASCII get only high-priority updates
				if ctx.Layer <= LayerASCII && update.Priority < realtime.PriorityHigh {
					return false
				}
				return true
			})
		}
	}
}

// convertRealtimeUpdate converts a realtime update to WebSocket message
func (s *Server) convertRealtimeUpdate(update realtime.Update) *Message {
	payload, _ := json.Marshal(update)
	
	priority := PriorityNormal
	switch update.Priority {
	case realtime.PriorityEmergency, realtime.PriorityCritical:
		priority = PriorityCritical
	case realtime.PriorityHigh:
		priority = PriorityHigh
	}
	
	return &Message{
		ID:        generateMessageID(),
		Type:      MessageTypeUpdate,
		Payload:   payload,
		Priority:  priority,
		Timestamp: update.Timestamp,
	}
}

// Simplification methods

func (s *Server) simplifyToCLI(payload json.RawMessage) json.RawMessage {
	// Convert complex data to simple text representation
	var data interface{}
	if err := json.Unmarshal(payload, &data); err != nil {
		return payload
	}
	
	// Create simplified text version
	simplified := map[string]interface{}{
		"text": fmt.Sprintf("%v", data),
		"type": "cli",
	}
	
	result, _ := json.Marshal(simplified)
	return result
}

func (s *Server) convertToASCII(payload json.RawMessage) json.RawMessage {
	// Convert to ASCII art representation
	// This would integrate with the ASCII renderer
	return payload
}

func (s *Server) optimizeFor3D(payload json.RawMessage, ctx *LayerContext) json.RawMessage {
	// Optimize for 3D rendering based on zoom level
	// Apply LOD (Level of Detail) optimizations
	return payload
}

func (s *Server) filterByViewport(payload json.RawMessage, viewport Bounds) json.RawMessage {
	// Filter out objects outside viewport
	var objects []arxobject.ArxObjectUnified
	if err := json.Unmarshal(payload, &objects); err != nil {
		return payload
	}
	
	filtered := []arxobject.ArxObjectUnified{}
	for _, obj := range objects {
		// Check if object is in viewport
		pos := obj.Geometry.Position
		if float64(pos.X) >= viewport.MinX && float64(pos.X) <= viewport.MaxX &&
		   float64(pos.Y) >= viewport.MinY && float64(pos.Y) <= viewport.MaxY &&
		   float64(pos.Z) >= viewport.MinZ && float64(pos.Z) <= viewport.MaxZ {
			filtered = append(filtered, obj)
		}
	}
	
	result, _ := json.Marshal(filtered)
	return result
}

func (s *Server) applyPrecisionFilter(payload json.RawMessage, precision Precision) json.RawMessage {
	// Round values based on precision level
	precisionValue := GetPrecisionValue(precision)
	
	// This would round all numeric values in the payload
	// to the appropriate precision
	return payload
}

// Stats handling

func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
	stats := s.layerManager.GetStats()
	
	s.mu.RLock()
	totalClients := len(s.clients)
	s.mu.RUnlock()
	
	response := map[string]interface{}{
		"total_clients": totalClients,
		"layer_stats":   stats,
		"timestamp":     time.Now(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Helper functions

func (s *Server) parseLayer(layerStr string) Layer {
	switch layerStr {
	case "1", "cli":
		return LayerCLI
	case "2", "ascii":
		return LayerASCII
	case "3", "webgl":
		return LayerWebGL
	case "4", "ar":
		return LayerAR
	case "5", "vr":
		return LayerVR
	case "6", "neural":
		return LayerNeural
	default:
		return LayerASCII // Default
	}
}

func (s *Server) parsePrecision(precStr string) Precision {
	switch precStr {
	case "0", "meter":
		return PrecisionMeter
	case "1", "decimeter":
		return PrecisionDecimeter
	case "2", "centimeter":
		return PrecisionCentimeter
	case "3", "millimeter":
		return PrecisionMillimeter
	case "4", "tenthmm":
		return PrecisionTenthMM
	case "5", "hundrethmm":
		return PrecisionHundrethMM
	case "6", "micrometer":
		return PrecisionMicrometer
	case "9", "nanometer":
		return PrecisionNanometer
	default:
		return PrecisionMillimeter // Default
	}
}

func generateMessageID() string {
	return fmt.Sprintf("msg_%d", time.Now().UnixNano())
}