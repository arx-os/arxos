package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	domaintypes "github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// UserHandler handles user-related HTTP requests
type UserHandler struct {
	BaseHandler
	userUC *usecase.UserUseCase
	logger domain.Logger
}

// NewUserHandler creates a new user handler with proper dependency injection
func NewUserHandler(base BaseHandler, userUC *usecase.UserUseCase, logger domain.Logger) *UserHandler {
	return &UserHandler{
		BaseHandler: base,
		userUC:      userUC,
		logger:      logger,
	}
}

// ListUsers handles GET /api/v1/users
func (h *UserHandler) ListUsers(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List users requested")

	// Parse query parameters
	limit := 10
	offset := 0
	organizationID := r.URL.Query().Get("organization_id")
	role := r.URL.Query().Get("role")
	active := r.URL.Query().Get("active")

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Create filter
	filter := &domain.UserFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Set optional filters
	if role != "" {
		filter.Role = &role
	}
	if active != "" {
		if active == "true" {
			activeBool := true
			filter.Active = &activeBool
		} else if active == "false" {
			activeBool := false
			filter.Active = &activeBool
		}
	}

	// Call use case
	users, err := h.userUC.ListUsers(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to list users", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	response := map[string]interface{}{
		"users":  users,
		"limit":  limit,
		"offset": offset,
		"filters": map[string]interface{}{
			"organization_id": organizationID,
			"role":            role,
			"active":          active,
		},
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// CreateUser handles POST /api/v1/users
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create user requested")

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req domain.CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Call use case
	user, err := h.userUC.CreateUser(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create user", "error", err)

		// Check for validation errors
		if err.Error() == "email is required" || err.Error() == "name is required" {
			h.RespondError(w, http.StatusBadRequest, err)
			return
		}

		// Check for duplicate email
		if err.Error() == "user with email already exists" {
			h.RespondError(w, http.StatusConflict, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusCreated, user)
}

// GetUser handles GET /api/v1/users/{id}
func (h *UserHandler) GetUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get user requested")

	userID := chi.URLParam(r, "id")
	if userID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("user ID is required"))
		return
	}

	// Call use case
	user, err := h.userUC.GetUser(r.Context(), userID)
	if err != nil {
		h.logger.Error("Failed to get user", "user_id", userID, "error", err)

		// Check for not found
		if err.Error() == "user not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, user)
}

// UpdateUser handles PUT /api/v1/users/{id}
func (h *UserHandler) UpdateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Update user requested")

	userID := chi.URLParam(r, "id")
	if userID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("user ID is required"))
		return
	}

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req domain.UpdateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Set the ID from URL parameter
	req.ID = domaintypes.FromString(userID)

	// Call use case
	user, err := h.userUC.UpdateUser(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update user", "user_id", userID, "error", err)

		// Check for validation errors
		if err.Error() == "email is required" || err.Error() == "name is required" {
			h.RespondError(w, http.StatusBadRequest, err)
			return
		}

		// Check for not found
		if err.Error() == "user not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, user)
}

// DeleteUser handles DELETE /api/v1/users/{id}
func (h *UserHandler) DeleteUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	h.logger.Info("Delete user requested")

	userID := chi.URLParam(r, "id")
	if userID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("user ID is required"))
		return
	}

	// Call use case
	err := h.userUC.DeleteUser(r.Context(), userID)
	if err != nil {
		h.logger.Error("Failed to delete user", "user_id", userID, "error", err)

		// Check for not found
		if err.Error() == "user not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusNoContent, nil)
}

// GetUserByEmail handles GET /api/v1/users/email/{email}
func (h *UserHandler) GetUserByEmail(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Get user by email requested")

	email := chi.URLParam(r, "email")
	if email == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("email is required"))
		return
	}

	// TODO: Implement GetUserByEmail in use case
	h.RespondError(w, http.StatusNotImplemented, fmt.Errorf("get user by email functionality not yet implemented"))
}

// GetUsersByOrganization handles GET /api/v1/organizations/{organization_id}/users
func (h *UserHandler) GetUsersByOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get users by organization requested")

	organizationID := chi.URLParam(r, "organization_id")
	if organizationID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("organization ID is required"))
		return
	}

	// Parse query parameters
	limit := 10
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Create filter
	filter := &domain.UserFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Call use case
	users, err := h.userUC.ListUsers(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to get users by organization", "organization_id", organizationID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	response := map[string]interface{}{
		"organization_id": organizationID,
		"users":           users,
		"limit":           limit,
		"offset":          offset,
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// ActivateUser handles POST /api/v1/users/{id}/activate
func (h *UserHandler) ActivateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Activate user requested")

	userID := chi.URLParam(r, "id")
	if userID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("user ID is required"))
		return
	}

	// TODO: Implement ActivateUser in use case
	h.RespondError(w, http.StatusNotImplemented, fmt.Errorf("activate user functionality not yet implemented"))
}

// DeactivateUser handles POST /api/v1/users/{id}/deactivate
func (h *UserHandler) DeactivateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Deactivate user requested")

	userID := chi.URLParam(r, "id")
	if userID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("user ID is required"))
		return
	}

	// TODO: Implement DeactivateUser in use case
	h.RespondError(w, http.StatusNotImplemented, fmt.Errorf("deactivate user functionality not yet implemented"))
}
