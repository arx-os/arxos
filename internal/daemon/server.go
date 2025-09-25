package daemon

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Server handles IPC communication with the daemon
type Server struct {
	daemon     *Daemon
	socketPath string
	listener   net.Listener
	mu         sync.Mutex
	clients    map[net.Conn]bool
}

// Request represents a client request
type Request struct {
	Command string                 `json:"command"`
	Args    map[string]interface{} `json:"args,omitempty"`
}

// Response represents a server response
type Response struct {
	Success bool                   `json:"success"`
	Message string                 `json:"message,omitempty"`
	Data    map[string]interface{} `json:"data,omitempty"`
	Error   string                 `json:"error,omitempty"`
}

// NewServer creates a new IPC server
func NewServer(daemon *Daemon, socketPath string) *Server {
	return &Server{
		daemon:     daemon,
		socketPath: socketPath,
		clients:    make(map[net.Conn]bool),
	}
}

// Start starts the IPC server
func (s *Server) Start(ctx context.Context, wg *sync.WaitGroup) {
	defer wg.Done()

	// Remove existing socket file
	os.Remove(s.socketPath)

	// Create Unix domain socket
	listener, err := net.Listen("unix", s.socketPath)
	if err != nil {
		logger.Error("Failed to create Unix socket: %v", err)
		return
	}
	s.listener = listener

	// Set permissions for socket
	os.Chmod(s.socketPath, 0666)

	logger.Info("IPC server listening on %s", s.socketPath)

	// Accept connections
	go s.acceptConnections(ctx)

	// Wait for context cancellation
	<-ctx.Done()
	s.Stop()
}

// Stop stops the IPC server
func (s *Server) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Close all client connections
	for conn := range s.clients {
		conn.Close()
	}

	// Close listener
	if s.listener != nil {
		s.listener.Close()
	}

	// Remove socket file
	os.Remove(s.socketPath)
}

// acceptConnections accepts incoming connections
func (s *Server) acceptConnections(ctx context.Context) {
	for {
		conn, err := s.listener.Accept()
		if err != nil {
			select {
			case <-ctx.Done():
				return
			default:
				// Check if listener was closed
				if strings.Contains(err.Error(), "use of closed network connection") {
					return
				}
				logger.Error("Failed to accept connection: %v", err)
				continue
			}
		}

		// Register client
		s.mu.Lock()
		s.clients[conn] = true
		s.mu.Unlock()

		// Handle client in goroutine
		go s.handleClient(ctx, conn)
	}
}

// handleClient handles a client connection
func (s *Server) handleClient(ctx context.Context, conn net.Conn) {
	defer func() {
		// Unregister client
		s.mu.Lock()
		delete(s.clients, conn)
		s.mu.Unlock()
		conn.Close()
	}()

	scanner := bufio.NewScanner(conn)
	encoder := json.NewEncoder(conn)

	for scanner.Scan() {
		select {
		case <-ctx.Done():
			return
		default:
		}

		// Parse request
		var req Request
		if err := json.Unmarshal(scanner.Bytes(), &req); err != nil {
			encoder.Encode(Response{
				Success: false,
				Error:   fmt.Sprintf("Invalid request: %v", err),
			})
			continue
		}

		// Process request
		resp := s.processRequest(ctx, &req)

		// Send response
		if err := encoder.Encode(resp); err != nil {
			logger.Error("Failed to send response: %v", err)
			return
		}
	}
}

// processRequest processes a client request
func (s *Server) processRequest(ctx context.Context, req *Request) *Response {
	switch strings.ToLower(req.Command) {
	case "status":
		return s.handleStatus()

	case "stats":
		return s.handleStats()

	case "reload":
		return s.handleReload()

	case "add-watch":
		return s.handleAddWatch(req.Args)

	case "remove-watch":
		return s.handleRemoveWatch(req.Args)

	case "import":
		return s.handleImport(req.Args)

	case "sync":
		return s.handleSync()

	case "queue-status":
		return s.handleQueueStatus()

	case "ping":
		return &Response{
			Success: true,
			Message: "pong",
		}

	case "shutdown":
		go s.daemon.Stop()
		return &Response{
			Success: true,
			Message: "Daemon shutting down",
		}

	default:
		return &Response{
			Success: false,
			Error:   fmt.Sprintf("Unknown command: %s", req.Command),
		}
	}
}

// handleStatus returns daemon status
func (s *Server) handleStatus() *Response {
	status := s.daemon.GetStatus()

	return &Response{
		Success: true,
		Data:    status,
	}
}

// handleStats returns daemon statistics
func (s *Server) handleStats() *Response {
	stats := s.daemon.GetStats()

	return &Response{
		Success: true,
		Data: map[string]interface{}{
			"start_time":        stats.StartTime.Format("2006-01-02T15:04:05Z07:00"),
			"files_processed":   stats.FilesProcessed,
			"import_successes":  stats.ImportSuccesses,
			"import_failures":   stats.ImportFailures,
			"last_processed":    stats.LastProcessedFile,
			"last_processed_at": stats.LastProcessedTime.Format("2006-01-02T15:04:05Z07:00"),
		},
	}
}

// handleReload reloads daemon configuration
func (s *Server) handleReload() *Response {
	ctx := context.Background()

	if err := s.daemon.ReloadConfig(ctx); err != nil {
		return &Response{
			Success: false,
			Message: fmt.Sprintf("Failed to reload configuration: %v", err),
		}
	}

	return &Response{
		Success: true,
		Message: "Configuration reloaded successfully",
	}
}

// handleAddWatch adds a directory to watch
func (s *Server) handleAddWatch(args map[string]interface{}) *Response {
	dir, ok := args["directory"].(string)
	if !ok {
		return &Response{
			Success: false,
			Error:   "Directory not specified",
		}
	}

	if err := s.daemon.addWatchDir(dir); err != nil {
		return &Response{
			Success: false,
			Error:   err.Error(),
		}
	}

	return &Response{
		Success: true,
		Message: fmt.Sprintf("Now watching: %s", dir),
	}
}

// handleRemoveWatch removes a directory from watch
func (s *Server) handleRemoveWatch(args map[string]interface{}) *Response {
	dir, ok := args["directory"].(string)
	if !ok {
		return &Response{
			Success: false,
			Error:   "Directory not specified",
		}
	}

	if err := s.daemon.watcher.Remove(dir); err != nil {
		return &Response{
			Success: false,
			Error:   err.Error(),
		}
	}

	return &Response{
		Success: true,
		Message: fmt.Sprintf("Stopped watching: %s", dir),
	}
}

// handleImport imports a file immediately
func (s *Server) handleImport(args map[string]interface{}) *Response {
	file, ok := args["file"].(string)
	if !ok {
		return &Response{
			Success: false,
			Error:   "File not specified",
		}
	}

	// Queue import work
	item := &WorkItem{
		Type:      WorkTypeImport,
		FilePath:  file,
		Timestamp: time.Now(),
	}

	if err := s.daemon.queue.Add(item); err != nil {
		return &Response{
			Success: false,
			Error:   err.Error(),
		}
	}

	return &Response{
		Success: true,
		Message: fmt.Sprintf("Queued import for: %s", file),
	}
}

// handleSync triggers a sync operation
func (s *Server) handleSync() *Response {
	ctx := context.Background()

	if err := s.daemon.syncDatabase(ctx); err != nil {
		return &Response{
			Success: false,
			Error:   err.Error(),
		}
	}

	return &Response{
		Success: true,
		Message: "Sync completed successfully",
	}
}

// handleQueueStatus returns queue status
func (s *Server) handleQueueStatus() *Response {
	return &Response{
		Success: true,
		Data: map[string]interface{}{
			"queue_size": s.daemon.queue.Size(),
			"max_size":   s.daemon.config.QueueSize,
			"workers":    s.daemon.config.MaxWorkers,
		},
	}
}
