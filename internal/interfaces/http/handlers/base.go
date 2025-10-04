package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/pkg/auth"
)

// BaseHandler defines the common HTTP handler interface following Clean Architecture
type BaseHandler interface {
	// HTTP Response Helpers
	RespondJSON(w http.ResponseWriter, statusCode int, data interface{})
	RespondError(w http.ResponseWriter, statusCode int, err error)

	// Request Validation
	ValidateContentType(r *http.Request, expectedType string) error
	ValidateRequest(r *http.Request) error

	// Authentication & Authorization
	GetUserFromContext(ctx context.Context) (*domain.User, error)
	RequireAuth(next http.Handler) http.Handler

	// Logging & Monitoring
	LogRequest(r *http.Request, statusCode int, duration time.Duration)
	LogError(r *http.Request, err error, statusCode int)

	// Request Helpers
	ParseRequestBody(r *http.Request, v interface{}) error
	ParseURLParams(r *http.Request) map[string]string
}

// BaseHandlerImpl provides concrete implementation of BaseHandler
type BaseHandlerImpl struct {
	logger     domain.Logger
	jwtManager *auth.JWTManager
}

// NewBaseHandler creates a new BaseHandler implementation
func NewBaseHandler(logger domain.Logger, jwtManager *auth.JWTManager) BaseHandler {
	return &BaseHandlerImpl{
		logger:     logger,
		jwtManager: jwtManager,
	}
}

// RespondJSON sends a JSON response with proper headers
func (h *BaseHandlerImpl) RespondJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.WriteHeader(statusCode)

	if data != nil {
		if err := json.NewEncoder(w).Encode(data); err != nil {
			h.logger.Error("Failed to encode JSON response", "error", err)
			http.Error(w, "Failed to encode response", http.StatusInternalServerError)
			return
		}
	}
}

// RespondError sends a consistent error response
func (h *BaseHandlerImpl) RespondError(w http.ResponseWriter, statusCode int, err error) {
	h.logger.Error("HTTP error response", "status", statusCode, "error", err)

	errorResponse := map[string]interface{}{
		"error":     http.StatusText(statusCode),
		"message":   err.Error(),
		"status":    statusCode,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}

	h.RespondJSON(w, statusCode, errorResponse)
}

// ValidateContentType validates that the request has the expected content type
func (h *BaseHandlerImpl) ValidateContentType(r *http.Request, expectedType string) error {
	contentType := r.Header.Get("Content-Type")
	if !strings.Contains(contentType, expectedType) {
		return fmt.Errorf("content type must be %s, got %s", expectedType, contentType)
	}
	return nil
}

// ValidateRequest validates common request parameters
func (h *BaseHandlerImpl) ValidateRequest(r *http.Request) error {
	// Validate HTTP method
	if r.Method == "" {
		return fmt.Errorf("missing HTTP method")
	}

	// Validate URL path
	if r.URL.Path == "" {
		return fmt.Errorf("missing URL path")
	}

	// Add more validation as needed
	return nil
}

// GetUserFromContext extracts user information from request context
func (h *BaseHandlerImpl) GetUserFromContext(ctx context.Context) (*domain.User, error) {
	user, ok := ctx.Value("user").(*domain.User)
	if !ok || user == nil {
		return nil, fmt.Errorf("user not found in context")
	}
	return user, nil
}

// RequireAuth creates middleware to require authentication
func (h *BaseHandlerImpl) RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract token from Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			h.RespondError(w, http.StatusUnauthorized, fmt.Errorf("missing authorization header"))
			return
		}

		// Validate Bearer token format
		tokenParts := strings.Split(authHeader, " ")
		if len(tokenParts) != 2 || tokenParts[0] != "Bearer" {
			h.RespondError(w, http.StatusUnauthorized, fmt.Errorf("invalid authorization header format"))
			return
		}

		// Validate JWT token
		claims, err := h.jwtManager.ValidateToken(tokenParts[1])
		if err != nil {
			h.RespondError(w, http.StatusUnauthorized, fmt.Errorf("invalid token: %w", err))
			return
		}

		// Extract user from claims and add to context
		user := &domain.User{
			ID:    claims.UserID,
			Email: claims.Email,
			Role:  claims.Role,
		}

		ctx := context.WithValue(r.Context(), "user", user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// LogRequest logs an HTTP request with structured logging
func (h *BaseHandlerImpl) LogRequest(r *http.Request, statusCode int, duration time.Duration) {
	h.logger.Info("HTTP request completed",
		"method", r.Method,
		"path", r.URL.Path,
		"status", statusCode,
		"duration_ms", duration.Milliseconds(),
		"user_agent", r.Header.Get("User-Agent"),
		"remote_addr", r.RemoteAddr,
	)
}

// LogError logs an HTTP error with structured logging
func (h *BaseHandlerImpl) LogError(r *http.Request, err error, statusCode int) {
	h.logger.Error("HTTP error occurred",
		"method", r.Method,
		"path", r.URL.Path,
		"status", statusCode,
		"error", err.Error(),
		"remote_addr", r.RemoteAddr,
	)
}

// ParseRequestBody parses JSON request body into a Go struct
func (h *BaseHandlerImpl) ParseRequestBody(r *http.Request, v interface{}) error {
	if r.Body == nil {
		return fmt.Errorf("request body is nil")
	}

	defer r.Body.Close()

	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		return fmt.Errorf("failed to parse request body: %w", err)
	}

	// Note: Struct validation would be implemented here if needed
	// For now, we rely on struct tags and manual validation in handlers

	return nil
}

// ParseURLParams extracts URL parameters from the request path
func (h *BaseHandlerImpl) ParseURLParams(r *http.Request) map[string]string {
	params := make(map[string]string)

	// This would typically be implemented with chi.URLParam
	// For now, return empty map - handlers will override this
	return params
}
