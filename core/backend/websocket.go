package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

// WebSocket upgrader with basic settings
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		// Allow all origins in development
		// TODO: Restrict in production
		return true
	},
}

// Hub maintains active client connections and broadcasts messages
type Hub struct {
	// Registered clients
	clients map[*Client]bool

	// Inbound messages from clients
	broadcast chan []byte

	// Register requests from clients
	register chan *Client

	// Unregister requests from clients
	unregister chan *Client

	// ArxObject updates to broadcast
	updates chan ArxObjectUpdate
}

// Client represents a websocket connection
type Client struct {
	hub  *Hub
	conn *websocket.Conn
	send chan []byte
}

// ArxObjectUpdate represents a change to an ArxObject
type ArxObjectUpdate struct {
	Action string    `json:"action"` // create, update, delete
	Object ArxObject `json:"object"`
}

// NewHub creates a new websocket hub
func NewHub() *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan []byte),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		updates:    make(chan ArxObjectUpdate),
	}
}

// Run starts the hub's event loop
func (h *Hub) Run() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case client := <-h.register:
			// New client connected
			h.clients[client] = true
			log.Printf("Client connected. Total clients: %d", len(h.clients))

			// Send initial connection message
			welcome := map[string]interface{}{
				"type":    "connected",
				"message": "Connected to Arxos real-time updates",
			}
			if data, err := json.Marshal(welcome); err == nil {
				client.send <- data
			}

		case client := <-h.unregister:
			// Client disconnected
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
				log.Printf("Client disconnected. Total clients: %d", len(h.clients))
			}

		case message := <-h.broadcast:
			// Broadcast message to all clients
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					// Client's send channel is full, close it
					close(client.send)
					delete(h.clients, client)
				}
			}

		case update := <-h.updates:
			// Broadcast ArxObject update to all clients
			if data, err := json.Marshal(update); err == nil {
				for client := range h.clients {
					select {
					case client.send <- data:
					default:
						close(client.send)
						delete(h.clients, client)
					}
				}
			}

		case <-ticker.C:
			// Send ping to all clients
			ping := map[string]string{"type": "ping"}
			if data, err := json.Marshal(ping); err == nil {
				for client := range h.clients {
					select {
					case client.send <- data:
					default:
						close(client.send)
						delete(h.clients, client)
					}
				}
			}
		}
	}
}

// ServeWS handles websocket requests from clients
func (h *Hub) ServeWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket upgrade error:", err)
		return
	}

	client := &Client{
		hub:  h,
		conn: conn,
		send: make(chan []byte, 256),
	}

	client.hub.register <- client

	// Start goroutines for reading and writing
	go client.writePump()
	go client.readPump()
}

// readPump handles incoming messages from the websocket connection
func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	c.conn.SetReadLimit(512000) // 512KB max message size
	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			break
		}

		// Parse incoming message
		var msg map[string]interface{}
		if err := json.Unmarshal(message, &msg); err == nil {
			// Handle different message types
			switch msg["type"] {
			case "subscribe":
				// Client wants to subscribe to specific updates
				log.Printf("Client subscribed to updates")
			case "ping":
				// Respond with pong
				pong := map[string]string{"type": "pong"}
				if data, err := json.Marshal(pong); err == nil {
					c.send <- data
				}
			default:
				// Echo the message back for now
				c.hub.broadcast <- message
			}
		}
	}
}

// writePump sends messages to the websocket connection
func (c *Client) writePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				// The hub closed the channel
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			c.conn.WriteMessage(websocket.TextMessage, message)

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// BroadcastUpdate sends an ArxObject update to all connected clients
func (h *Hub) BroadcastUpdate(action string, object ArxObject) {
	update := ArxObjectUpdate{
		Action: action,
		Object: object,
	}
	
	select {
	case h.updates <- update:
	default:
		// Channel is full, drop the update
		log.Println("Warning: Update channel full, dropping update")
	}
}

// GetClientCount returns the number of connected clients
func (h *Hub) GetClientCount() int {
	return len(h.clients)
}