package types

import (
	"context"
	"net/http"
	"time"
)

// Server represents the HTTP server configuration
type Server struct {
	Port         string
	Host         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
	Context      context.Context
}

// NewServer creates a new server configuration
func NewServer(port, host string) *Server {
	return &Server{
		Port:         port,
		Host:         host,
		ReadTimeout:  time.Second * 30,
		WriteTimeout: time.Second * 30,
		IdleTimeout:  time.Second * 60,
		Context:      context.Background(),
	}
}

// BaseHandler provides common functionality for HTTP handlers
type BaseHandler struct {
	Server *Server
}

// NewBaseHandler creates a new base handler
func NewBaseHandler(server *Server) *BaseHandler {
	return &BaseHandler{
		Server: server,
	}
}

// RespondJSON sends a JSON response
func (h *BaseHandler) RespondJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	// JSON encoding would be implemented here
}

// LogRequest logs an HTTP request
func (h *BaseHandler) LogRequest(r *http.Request, statusCode int, duration time.Duration) {
	// Request logging would be implemented here
}
