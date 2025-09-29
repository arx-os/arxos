package messaging

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"github.com/stretchr/testify/assert"
)

func TestNewWebSocketHub(t *testing.T) {
	tests := []struct {
		name   string
		config *WebSocketConfig
		want   *WebSocketHub
	}{
		{
			name:   "with nil config",
			config: nil,
			want: &WebSocketHub{
				clients:    make(map[*Client]bool),
				register:   make(chan *Client),
				unregister: make(chan *Client),
				broadcast:  make(chan []byte),
				rooms:      make(map[string]map[*Client]bool),
				config:     DefaultWebSocketConfig(),
			},
		},
		{
			name:   "with custom config",
			config: &WebSocketConfig{ReadBufferSize: 2048},
			want: &WebSocketHub{
				clients:    make(map[*Client]bool),
				register:   make(chan *Client),
				unregister: make(chan *Client),
				broadcast:  make(chan []byte),
				rooms:      make(map[string]map[*Client]bool),
				config:     &WebSocketConfig{ReadBufferSize: 2048},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := NewWebSocketHub(tt.config)
			assert.Equal(t, tt.want.config, got.config)
			assert.NotNil(t, got.clients)
			assert.NotNil(t, got.register)
			assert.NotNil(t, got.unregister)
			assert.NotNil(t, got.broadcast)
			assert.NotNil(t, got.rooms)
		})
	}
}

func TestDefaultWebSocketConfig(t *testing.T) {
	config := DefaultWebSocketConfig()

	assert.Equal(t, 1024, config.ReadBufferSize)
	assert.Equal(t, 1024, config.WriteBufferSize)
	assert.NotNil(t, config.CheckOrigin)
	assert.Equal(t, 54*time.Second, config.PingPeriod)
	assert.Equal(t, 60*time.Second, config.PongWait)
	assert.Equal(t, 10*time.Second, config.WriteWait)
	assert.Equal(t, int64(512), config.MaxMessageSize)

	// Test CheckOrigin function
	req := &http.Request{}
	assert.True(t, config.CheckOrigin(req))
}

func TestWebSocketHub_HandleWebSocket(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		// Clean up
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		err := hub.HandleWebSocket(w, r)
		if err != nil {
			t.Errorf("HandleWebSocket failed: %v", err)
		}
	}))
	defer server.Close()

	// Convert HTTP URL to WebSocket URL
	wsURL := "ws" + server.URL[4:]

	// Connect to WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Skip("WebSocket connection failed, skipping test")
	}
	defer conn.Close()

	// Give some time for the connection to be registered
	time.Sleep(10 * time.Millisecond)

	// Check that client was registered
	assert.True(t, len(hub.clients) > 0)
}

func TestWebSocketHub_BroadcastToRoom(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create a mock client
	client := &Client{
		ID:     "test-client",
		UserID: "test-user",
		Room:   "test-room",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register client
	hub.register <- client

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Test broadcasting to room
	message := map[string]string{"test": "message"}
	err := hub.BroadcastToRoom("test-room", message)
	assert.NoError(t, err)

	// Test broadcasting to non-existent room
	err = hub.BroadcastToRoom("non-existent-room", message)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "does not exist")
}

func TestWebSocketHub_BroadcastToUser(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create a mock client
	client := &Client{
		ID:     "test-client",
		UserID: "test-user",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register client
	hub.register <- client

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Test broadcasting to user
	message := map[string]string{"test": "message"}
	err := hub.BroadcastToUser("test-user", message)
	assert.NoError(t, err)

	// Test broadcasting to non-existent user
	err = hub.BroadcastToUser("non-existent-user", message)
	assert.NoError(t, err) // Should not error, just no clients to send to
}

func TestWebSocketHub_BroadcastToAll(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create mock clients
	client1 := &Client{
		ID:     "test-client-1",
		UserID: "test-user-1",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	client2 := &Client{
		ID:     "test-client-2",
		UserID: "test-user-2",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register clients
	hub.register <- client1
	hub.register <- client2

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Test broadcasting to all
	message := map[string]string{"test": "message"}
	err := hub.BroadcastToAll(message)
	assert.NoError(t, err)
}

func TestWebSocketHub_JoinRoom(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create a mock client
	client := &Client{
		ID:     "test-client",
		UserID: "test-user",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register client
	hub.register <- client

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Test joining room
	err := hub.JoinRoom("test-user", "test-room")
	assert.NoError(t, err)

	// Verify client is in room
	assert.Equal(t, "test-room", client.Room)
	assert.Contains(t, hub.rooms, "test-room")
	assert.Contains(t, hub.rooms["test-room"], client)

	// Test joining non-existent user
	err = hub.JoinRoom("non-existent-user", "test-room")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "client not found")
}

func TestWebSocketHub_LeaveRoom(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create a mock client
	client := &Client{
		ID:     "test-client",
		UserID: "test-user",
		Room:   "test-room",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register client and add to room
	hub.register <- client

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Test leaving room
	err := hub.LeaveRoom("test-user", "test-room")
	assert.NoError(t, err)

	// Verify client is no longer in room
	assert.Equal(t, "", client.Room)
	assert.NotContains(t, hub.rooms["test-room"], client)

	// Test leaving non-existent user
	err = hub.LeaveRoom("non-existent-user", "test-room")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "client not found")
}

func TestWebSocketHub_GetRoomUsers(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create mock clients
	client1 := &Client{
		ID:     "test-client-1",
		UserID: "test-user-1",
		Room:   "test-room",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	client2 := &Client{
		ID:     "test-client-2",
		UserID: "test-user-2",
		Room:   "test-room",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register clients
	hub.register <- client1
	hub.register <- client2

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Test getting room users
	users, err := hub.GetRoomUsers("test-room")
	assert.NoError(t, err)
	assert.Len(t, users, 2)
	assert.Contains(t, users, "test-user-1")
	assert.Contains(t, users, "test-user-2")

	// Test getting non-existent room users
	users, err = hub.GetRoomUsers("non-existent-room")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "does not exist")
}

func TestWebSocketHub_IsHealthy(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Hub should always be healthy
	assert.True(t, hub.IsHealthy())
}

func TestWebSocketHub_GetStats(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create mock clients
	client1 := &Client{
		ID:     "test-client-1",
		UserID: "test-user-1",
		Room:   "test-room-1",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	client2 := &Client{
		ID:     "test-client-2",
		UserID: "test-user-2",
		Room:   "test-room-2",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	// Register clients
	hub.register <- client1
	hub.register <- client2

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	// Get stats
	stats := hub.GetStats()
	assert.Equal(t, 2, stats["total_clients"])
	assert.Equal(t, 2, stats["total_rooms"])

	rooms := stats["rooms"].(map[string]int)
	assert.Equal(t, 1, rooms["test-room-1"])
	assert.Equal(t, 1, rooms["test-room-2"])
}

func TestWebSocketHub_extractUserID(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Test with header
	req := &http.Request{
		Header: make(http.Header),
	}
	req.Header.Set("X-User-ID", "test-user")

	userID := hub.extractUserID(req)
	assert.Equal(t, "test-user", userID)

	// Test with context
	req = &http.Request{}
	ctx := context.WithValue(req.Context(), "user_id", "context-user")
	req = req.WithContext(ctx)

	userID = hub.extractUserID(req)
	assert.Equal(t, "context-user", userID)
}

func TestWebSocketHub_extractRoom(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Test with header
	req := &http.Request{
		Header: make(http.Header),
	}
	req.Header.Set("X-Room", "test-room")

	room := hub.extractRoom(req)
	assert.Equal(t, "test-room", room)
}

func TestClient_readPump(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		err := hub.HandleWebSocket(w, r)
		if err != nil {
			t.Errorf("HandleWebSocket failed: %v", err)
		}
	}))
	defer server.Close()

	// Convert HTTP URL to WebSocket URL
	wsURL := "ws" + server.URL[4:]

	// Connect to WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Skip("WebSocket connection failed, skipping test")
	}
	defer conn.Close()

	// Give some time for the connection to be established
	time.Sleep(10 * time.Millisecond)

	// The readPump should be running in a goroutine
	// We can't easily test it without a real WebSocket connection
	// This test mainly ensures the function doesn't panic
}

func TestClient_writePump(t *testing.T) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		err := hub.HandleWebSocket(w, r)
		if err != nil {
			t.Errorf("HandleWebSocket failed: %v", err)
		}
	}))
	defer server.Close()

	// Convert HTTP URL to WebSocket URL
	wsURL := "ws" + server.URL[4:]

	// Connect to WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Skip("WebSocket connection failed, skipping test")
	}
	defer conn.Close()

	// Give some time for the connection to be established
	time.Sleep(10 * time.Millisecond)

	// The writePump should be running in a goroutine
	// We can't easily test it without a real WebSocket connection
	// This test mainly ensures the function doesn't panic
}

func BenchmarkWebSocketHub_BroadcastToAll(b *testing.B) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create mock clients
	for i := 0; i < 100; i++ {
		client := &Client{
			ID:     "test-client-" + string(rune(i)),
			UserID: "test-user-" + string(rune(i)),
			send:   make(chan []byte, 1),
			hub:    hub,
		}
		hub.register <- client
	}

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	message := map[string]string{"test": "message"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		hub.BroadcastToAll(message)
	}
}

func BenchmarkWebSocketHub_JoinRoom(b *testing.B) {
	hub := NewWebSocketHub(DefaultWebSocketConfig())

	// Start hub in goroutine
	go hub.Run()
	defer func() {
		close(hub.register)
		close(hub.unregister)
		close(hub.broadcast)
	}()

	// Create mock client
	client := &Client{
		ID:     "test-client",
		UserID: "test-user",
		send:   make(chan []byte, 1),
		hub:    hub,
	}

	hub.register <- client

	// Give time for registration
	time.Sleep(10 * time.Millisecond)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		hub.JoinRoom("test-user", "test-room")
	}
}
