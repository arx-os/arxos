package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/interfaces/http/types"
)

// BaseHandler provides common functionality for HTTP handlers
type BaseHandler struct {
	Server *types.Server
}

// NewBaseHandler creates a new base handler
func NewBaseHandler(server *types.Server) *BaseHandler {
	return &BaseHandler{
		Server: server,
	}
}

// RespondJSON sends a JSON response
func (h *BaseHandler) RespondJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		fmt.Printf("Failed to encode JSON response: %v\n", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
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

// GetUserFromContext extracts user information from request context
func (h *BaseHandler) GetUserFromContext(r *http.Request) (string, bool) {
	// This would extract user information from JWT token or session
	// For now, return a placeholder
	return "user123", true
}

// ValidateRequest validates common request parameters
func (h *BaseHandler) ValidateRequest(r *http.Request) error {
	// Add common validation logic here
	return nil
}

// SetCORSHeaders sets CORS headers for cross-origin requests
func (h *BaseHandler) SetCORSHeaders(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}

// HandleOptions handles CORS preflight requests
func (h *BaseHandler) HandleOptions(w http.ResponseWriter, r *http.Request) {
	h.SetCORSHeaders(w)
	w.WriteHeader(http.StatusOK)
}
