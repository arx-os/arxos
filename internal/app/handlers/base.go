package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	domainmodels "github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

// BaseHandler provides common functionality for all handlers following Clean Architecture principles
type BaseHandler struct {
	services *types.Services
	logger   logger.Logger
}

// NewBaseHandler creates a new base handler with dependency injection
func NewBaseHandler(services *types.Services, logger logger.Logger) *BaseHandler {
	return &BaseHandler{
		services: services,
		logger:   logger,
	}
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

// GetOrganizationID extracts the organization ID from the request context
func (h *BaseHandler) GetOrganizationID(r *http.Request) (string, error) {
	orgID, ok := r.Context().Value("organization_id").(string)
	if !ok {
		return "", fmt.Errorf("organization_id not found in context")
	}
	return orgID, nil
}

// GetPathParam extracts a path parameter from the request
func (h *BaseHandler) GetPathParam(r *http.Request, key string) (string, error) {
	param := chi.URLParam(r, key)
	if param == "" {
		return "", fmt.Errorf("path parameter %s is required", key)
	}
	return param, nil
}

// GetQueryParam extracts a query parameter from the request
func (h *BaseHandler) GetQueryParam(r *http.Request, key string) string {
	return r.URL.Query().Get(key)
}

// GetQueryParamAsInt extracts a query parameter as integer from the request
func (h *BaseHandler) GetQueryParamAsInt(r *http.Request, key string, defaultValue int) (int, error) {
	param := r.URL.Query().Get(key)
	if param == "" {
		return defaultValue, nil
	}
	return strconv.Atoi(param)
}

// GetQueryParamAsUUID extracts a query parameter as UUID from the request
func (h *BaseHandler) GetQueryParamAsUUID(r *http.Request, key string) (uuid.UUID, error) {
	param := r.URL.Query().Get(key)
	if param == "" {
		return uuid.Nil, fmt.Errorf("query parameter %s is required", key)
	}
	return uuid.Parse(param)
}

// WriteJSONResponse writes a JSON response with proper headers
func (h *BaseHandler) WriteJSONResponse(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		h.logger.Error("Failed to encode JSON response", "error", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

// WriteErrorResponse writes an error response in JSON format
func (h *BaseHandler) WriteErrorResponse(w http.ResponseWriter, statusCode int, message string, details interface{}) {
	errorResponse := map[string]interface{}{
		"error": map[string]interface{}{
			"message": message,
			"code":    http.StatusText(statusCode),
			"time":    time.Now().UTC().Format(time.RFC3339),
		},
	}

	if details != nil {
		errorResponse["error"].(map[string]interface{})["details"] = details
	}

	h.WriteJSONResponse(w, statusCode, errorResponse)
}

// WriteSuccessResponse writes a success response in JSON format
func (h *BaseHandler) WriteSuccessResponse(w http.ResponseWriter, data interface{}) {
	response := map[string]interface{}{
		"data": data,
		"meta": map[string]interface{}{
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		},
	}

	h.WriteJSONResponse(w, http.StatusOK, response)
}

// LogRequest logs the incoming request for debugging
func (h *BaseHandler) LogRequest(r *http.Request, operation string) {
	h.logger.Info("Request received",
		"method", r.Method,
		"path", r.URL.Path,
		"operation", operation,
		"user_agent", r.UserAgent(),
		"remote_addr", r.RemoteAddr,
	)
}

// LogError logs an error with context
func (h *BaseHandler) LogError(r *http.Request, operation string, err error) {
	h.logger.Error("Request failed",
		"method", r.Method,
		"path", r.URL.Path,
		"operation", operation,
		"error", err.Error(),
		"remote_addr", r.RemoteAddr,
	)
}
