package api

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// Common errors
var (
	ErrUnauthorized = errors.New("unauthorized")
	ErrForbidden    = errors.New("forbidden")
	ErrNotFound     = errors.New("not found")
	ErrBadRequest   = errors.New("bad request")
)

// getCurrentUser extracts the current user from the request context
func (s *Server) getCurrentUser(r *http.Request) (*models.User, error) {
	// Get token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return nil, ErrUnauthorized
	}

	// Extract token
	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
		return nil, ErrUnauthorized
	}
	token := parts[1]

	// Validate token and get claims
	claims, err := s.services.Auth.ValidateToken(r.Context(), token)
	if err != nil {
		return nil, ErrUnauthorized
	}

	// Get user from database
	apiUser, err := s.services.User.GetUser(r.Context(), claims.UserID)
	if err != nil {
		return nil, ErrUnauthorized
	}

	// Convert API User to models.User
	user := &models.User{
		ID:       apiUser.ID,
		Email:    apiUser.Email,
		FullName: apiUser.Name,
		Role:     apiUser.Role,
		IsActive: apiUser.Active,
	}

	if !user.IsActive {
		return nil, ErrForbidden
	}

	return user, nil
}

// getUserFromContext gets user from request context (if already authenticated)
func (s *Server) getUserFromContext(ctx context.Context) (*models.User, error) {
	userVal := ctx.Value("user")
	if userVal == nil {
		return nil, ErrUnauthorized
	}

	user, ok := userVal.(*models.User)
	if !ok {
		return nil, ErrUnauthorized
	}

	return user, nil
}

// hasPermission checks if user has a specific permission
func (s *Server) hasPermission(user *models.User, permission models.Permission) bool {
	// Check if user has the permission through their role
	role := models.Role(user.Role)
	permissions, exists := models.RolePermissions[role]
	if !exists {
		return false
	}

	for _, p := range permissions {
		if p == permission {
			return true
		}
	}
	return false
}

// hasOrgAccess checks if user has access to an organization
func (s *Server) hasOrgAccess(ctx context.Context, user *models.User, orgID string) bool {
	// Admin users have access to all organizations
	if user.Role == string(models.RoleAdmin) || user.Role == string(models.RoleOwner) {
		return true
	}

	// Check if user is member of the organization
	canAccess, err := s.services.Organization.CanUserAccessOrganization(ctx, orgID, user.ID)
	if err != nil {
		logger.Warn("Failed to check org access: %v", err)
		return false
	}

	return canAccess
}

// respondJSON sends a JSON response
func (s *Server) respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	if data != nil {
		if err := json.NewEncoder(w).Encode(data); err != nil {
			logger.Error("Failed to encode JSON response: %v", err)
		}
	}
}

// respondError sends an error response
func (s *Server) respondError(w http.ResponseWriter, status int, message string) {
	s.respondJSON(w, status, map[string]string{
		"error": message,
	})
}

// respondErrorWithDetails sends a detailed error response
func (s *Server) respondErrorWithDetails(w http.ResponseWriter, status int, message string, details interface{}) {
	s.respondJSON(w, status, map[string]interface{}{
		"error":   message,
		"details": details,
	})
}

// parseJSON parses JSON request body
func (s *Server) parseJSON(r *http.Request, v interface{}) error {
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()

	if err := decoder.Decode(v); err != nil {
		return err
	}

	return nil
}

// getPaginationParams extracts pagination parameters from request
func (s *Server) getPaginationParams(r *http.Request) (limit, offset int) {
	limit = 100  // Default limit
	offset = 0   // Default offset

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

// getQueryParam safely gets a query parameter
func (s *Server) getQueryParam(r *http.Request, key string, defaultValue string) string {
	value := r.URL.Query().Get(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// validateRequest performs basic request validation
func (s *Server) validateRequest(r *http.Request, requiredParams ...string) error {
	for _, param := range requiredParams {
		if r.URL.Query().Get(param) == "" && r.FormValue(param) == "" {
			return errors.New("missing required parameter: " + param)
		}
	}
	return nil
}