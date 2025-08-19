package main

import (
	"encoding/json"
	"log"
	"time"

	"github.com/gorilla/websocket"
)

// Hub maintains active client connections and broadcasts messages
type Hub struct {
	clients    map[*Client]bool
	broadcast  chan []byte
	register   chan *Client
	unregister chan *Client
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

			// Send welcome message
			welcome := map[string]interface{}{
				"type":    "connected",
				"message": "Connected to Arxos real-time updates",
				"time":    time.Now(),
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
					delete(h.clients, client)
					close(client.send)
				}
			}

		case <-ticker.C:
			// Send ping to keep connections alive
			ping := map[string]string{"type": "ping"}
			if data, err := json.Marshal(ping); err == nil {
				for client := range h.clients {
					select {
					case client.send <- data:
					default:
					}
				}
			}
		}
	}
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
				// Client wants to subscribe to updates
				log.Printf("Client subscribed to updates")
				
			case "ping":
				// Respond with pong
				pong := map[string]string{"type": "pong"}
				if data, err := json.Marshal(pong); err == nil {
					c.send <- data
				}
				
			case "update":
				// Client sending an update - broadcast to others
				c.hub.broadcast <- message
				
			default:
				// Echo unknown messages for debugging
				log.Printf("Unknown message type: %v", msg["type"])
			}
		}
	}
}

// writePump handles sending messages to the websocket connection
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
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}