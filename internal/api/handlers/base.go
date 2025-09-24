package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/common/logger"
	domainmodels "github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

// BaseHandler provides common functionality for all handlers
type BaseHandler struct {
	server *types.Server
}

// NewBaseHandler creates a new base handler
func NewBaseHandler(server *types.Server) *BaseHandler {
	return &BaseHandler{server: server}
}

// GetCurrentUser extracts the current user from the request context
func (h *BaseHandler) GetCurrentUser(r *http.Request) (*domainmodels.User, error) {
	// Extract user from context (set by auth middleware)
	user, ok := r.Context().Value("user").(*domainmodels.User)
	if !ok {
		return nil, fmt.Errorf("user not found in context")
	}
	return user, nil
}

// RequireAuth ensures the request is authenticated
func (h *BaseHandler) RequireAuth(w http.ResponseWriter, r *http.Request) (*domainmodels.User, bool) {
	user, err := h.GetCurrentUser(r)
	if err != nil {
		h.RespondError(w, http.StatusUnauthorized, "Authentication required")
		return nil, false
	}
	return user, true
}

// RequireRole ensures the user has the required role
func (h *BaseHandler) RequireRole(w http.ResponseWriter, r *http.Request, requiredRole string) (*domainmodels.User, bool) {
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return nil, false
	}

	if string(user.Role) != requiredRole {
		h.RespondError(w, http.StatusForbidden, "Insufficient permissions")
		return nil, false
	}

	return user, true
}

// RequireOrgAccess ensures the user has access to the organization
func (h *BaseHandler) RequireOrgAccess(w http.ResponseWriter, r *http.Request, orgID string) (*domainmodels.User, bool) {
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return nil, false
	}

	// Check if user has access to the organization
	if !h.server.HasOrgAccess(r.Context(), user, orgID) {
		h.RespondError(w, http.StatusForbidden, "Access denied to organization")
		return nil, false
	}

	return user, true
}

// ParseID extracts and validates ID from URL path
func (h *BaseHandler) ParseID(r *http.Request, param string) (string, error) {
	id := chi.URLParam(r, param)
	if id == "" {
		return "", fmt.Errorf("missing %s parameter", param)
	}

	// Validate UUID format
	if _, err := uuid.Parse(id); err != nil {
		return "", fmt.Errorf("invalid %s format", param)
	}

	return id, nil
}

// ParsePagination extracts pagination parameters from query string
func (h *BaseHandler) ParsePagination(r *http.Request) (limit, offset int) {
	limit = 20
	offset = 0

	if l := r.URL.Query().Get("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 && parsed <= 1000 {
			limit = parsed
		}
	}

	if o := r.URL.Query().Get("offset"); o != "" {
		if parsed, err := strconv.Atoi(o); err == nil && parsed >= 0 {
			offset = parsed
		}
	}

	return limit, offset
}

// ParseJSON parses JSON request body into the provided interface
func (h *BaseHandler) ParseJSON(r *http.Request, v interface{}) error {
	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		return fmt.Errorf("invalid JSON: %w", err)
	}
	return nil
}

// ValidateRequest validates the request data
func (h *BaseHandler) ValidateRequest(data interface{}) error {
	// This would use a validation library like go-playground/validator
	// For now, return nil as a placeholder
	return nil
}

// RespondJSON sends a JSON response
func (h *BaseHandler) RespondJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		logger.Error("Failed to encode JSON response: %v", err)
	}
}

// RespondError sends an error response
func (h *BaseHandler) RespondError(w http.ResponseWriter, statusCode int, message string) {
	response := models.ErrorResponse{
		Error: message,
		Code:  http.StatusText(statusCode),
	}

	h.RespondJSON(w, statusCode, response)
}

// RespondSuccess sends a success response
func (h *BaseHandler) RespondSuccess(w http.ResponseWriter, data interface{}, message string) {
	response := models.SuccessResponse{
		Success: true,
		Data:    data,
		Message: message,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// RespondPaginated sends a paginated response
func (h *BaseHandler) RespondPaginated(w http.ResponseWriter, data interface{}, limit, offset, total int) {
	pages := (total + limit - 1) / limit // Calculate total pages

	response := models.PaginatedResponse{
		Data: data,
		Pagination: models.PaginationInfo{
			Page:       (offset / limit) + 1,
			PageSize:   limit,
			Total:      int64(total),
			TotalPages: pages,
		},
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// LogRequest logs the incoming request
func (h *BaseHandler) LogRequest(r *http.Request, statusCode int, duration time.Duration) {
	logger.Info("Request: %s %s - %d - %v", r.Method, r.URL.Path, statusCode, duration)
}

// HandleError handles common errors and logs them
func (h *BaseHandler) HandleError(w http.ResponseWriter, r *http.Request, err error, message string) {
	logger.Error("Handler error: %v", err)

	// Determine appropriate status code based on error type
	statusCode := http.StatusInternalServerError
	if message == "not found" {
		statusCode = http.StatusNotFound
	} else if message == "unauthorized" {
		statusCode = http.StatusUnauthorized
	} else if message == "forbidden" {
		statusCode = http.StatusForbidden
	} else if message == "bad request" {
		statusCode = http.StatusBadRequest
	}

	h.RespondError(w, statusCode, message)
}

// GenerateID generates a new unique ID
func (h *BaseHandler) GenerateID() string {
	return uuid.New().String()
}

// GetUserIDFromContext extracts user ID from request context
func (h *BaseHandler) GetUserIDFromContext(r *http.Request) (string, error) {
	user, err := h.GetCurrentUser(r)
	if err != nil {
		return "", err
	}
	return user.ID, nil
}

// GetOrgIDFromContext extracts organization ID from request context
func (h *BaseHandler) GetOrgIDFromContext(r *http.Request) (string, error) {
	_, err := h.GetCurrentUser(r)
	if err != nil {
		return "", err
	}
	// Note: This would need to get organization ID from user's session or membership
	// For now, return empty string as placeholder
	return "", nil
}

// ValidateUserAccess validates if a user can access a resource
func (h *BaseHandler) ValidateUserAccess(w http.ResponseWriter, r *http.Request, resourceUserID string) (*domainmodels.User, bool) {
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return nil, false
	}

	// Users can access their own resources or admins can access any resource
	if user.ID != resourceUserID && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Access denied")
		return nil, false
	}

	return user, true
}

// ValidateOrgAccess validates if a user can access an organization resource
func (h *BaseHandler) ValidateOrgAccess(w http.ResponseWriter, r *http.Request, orgID string) (*domainmodels.User, bool) {
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return nil, false
	}

	// Check if user belongs to the organization
	// Note: This would need to check user's organization membership through a service
	// For now, allow access for admin users
	if string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Access denied to organization")
		return nil, false
	}

	return user, true
}
