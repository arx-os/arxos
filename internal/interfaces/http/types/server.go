package types

import (
	"context"
	"encoding/json"
	"fmt"
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

	if data != nil {
		json.NewEncoder(w).Encode(data)
	}
}

// LogRequest logs an HTTP request
func (h *BaseHandler) LogRequest(r *http.Request, statusCode int, duration time.Duration) {
	fmt.Printf("%s %s - %d - %v\n", r.Method, r.URL.Path, statusCode, duration)
}

// HandleError handles common HTTP errors
func (h *BaseHandler) HandleError(w http.ResponseWriter, r *http.Request, err error, statusCode int) {
	fmt.Printf("HTTP Error %d: %v\n", statusCode, err)
	http.Error(w, err.Error(), statusCode)
}

// ValidateContentType validates that the request has the expected content type
func (h *BaseHandler) ValidateContentType(r *http.Request, expectedType string) bool {
	contentType := r.Header.Get("Content-Type")
	return contentType == expectedType
}
