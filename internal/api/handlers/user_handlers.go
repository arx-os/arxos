package handlers

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// UserHandler handles user-related HTTP requests
type UserHandler struct {
	*BaseHandler
}

// NewUserHandler creates a new user handler
func NewUserHandler(server *types.Server) *UserHandler {
	return &UserHandler{
		BaseHandler: NewBaseHandler(server),
	}
}

// HandleGetUsers handles GET /api/v1/users
func (h *UserHandler) HandleGetUsers(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication and admin role
	_, ok := h.RequireRole(w, r, string(domainmodels.UserRoleAdmin))
	if !ok {
		return
	}

	// Parse pagination
	limit, offset := h.ParsePagination(r)

	// Parse filters
	filter := models.UserFilter{
		Role: r.URL.Query().Get("role"),
	}

	// Get users from service
	users, err := h.server.Services.User.ListUsers(r.Context(), filter)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve users")
		return
	}

	// Convert to response format
	userResponses := make([]*models.UserResponse, 0, len(users))
	for _, user := range users {
		if u, ok := user.(*domainmodels.User); ok {
			userResponses = append(userResponses, models.UserToResponse(u))
		}
	}

	h.RespondPaginated(w, userResponses, limit, offset, len(userResponses))
}

// HandleGetUser handles GET /api/v1/users/{id}
func (h *UserHandler) HandleGetUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Validate access
	_, ok := h.ValidateUserAccess(w, r, userID)
	if !ok {
		return
	}

	// Get user from service
	userData, err := h.server.Services.User.GetUser(r.Context(), userID)
	if err != nil {
		h.HandleError(w, r, err, "User not found")
		return
	}

	// Convert to response format
	if u, ok := userData.(*domainmodels.User); ok {
		h.RespondJSON(w, http.StatusOK, models.UserToResponse(u))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid user data")
	}
}

// HandleCreateUser handles POST /api/v1/users
func (h *UserHandler) HandleCreateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Check authentication and admin role
	_, ok := h.RequireRole(w, r, string(domainmodels.UserRoleAdmin))
	if !ok {
		return
	}

	// Parse request
	var req models.CreateUserRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Create user
	user, err := h.server.Services.User.CreateUser(r.Context(), req.Email, req.Password, req.Name)
	if err != nil {
		h.HandleError(w, r, err, "Failed to create user")
		return
	}

	// Convert to response format
	if u, ok := user.(*domainmodels.User); ok {
		h.RespondJSON(w, http.StatusCreated, models.UserToResponse(u))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid user data")
	}
}

// HandleUpdateUser handles PUT /api/v1/users/{id}
func (h *UserHandler) HandleUpdateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Validate access
	_, ok := h.ValidateUserAccess(w, r, userID)
	if !ok {
		return
	}

	// Parse request
	var req models.UpdateUserRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Convert to updates map
	updates := make(map[string]interface{})
	if req.Name != nil && *req.Name != "" {
		updates["name"] = *req.Name
	}
	if req.Email != nil && *req.Email != "" {
		updates["email"] = *req.Email
	}
	if req.Role != nil && *req.Role != "" {
		updates["role"] = *req.Role
	}
	if req.Status != nil && *req.Status != "" {
		updates["status"] = *req.Status
	}
	if req.OrgID != nil && *req.OrgID != "" {
		updates["org_id"] = *req.OrgID
	}

	// Update user
	user, err := h.server.Services.User.UpdateUser(r.Context(), userID, updates)
	if err != nil {
		h.HandleError(w, r, err, "Failed to update user")
		return
	}

	// Convert to response format
	if u, ok := user.(*domainmodels.User); ok {
		h.RespondJSON(w, http.StatusOK, models.UserToResponse(u))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid user data")
	}
}

// HandleDeleteUser handles DELETE /api/v1/users/{id}
func (h *UserHandler) HandleDeleteUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Check authentication and admin role
	_, ok := h.RequireRole(w, r, string(domainmodels.UserRoleAdmin))
	if !ok {
		return
	}

	// Delete user
	if err := h.server.Services.User.DeleteUser(r.Context(), userID); err != nil {
		h.HandleError(w, r, err, "Failed to delete user")
		return
	}

	h.RespondSuccess(w, nil, "User deleted successfully")
}

// HandleChangePassword handles POST /api/v1/users/{id}/change-password
func (h *UserHandler) HandleChangePassword(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Validate access
	_, ok := h.ValidateUserAccess(w, r, userID)
	if !ok {
		return
	}

	// Parse request
	var req models.ChangePasswordRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Change password
	if err := h.server.Services.User.ChangePassword(r.Context(), userID, req.CurrentPassword, req.NewPassword); err != nil {
		h.HandleError(w, r, err, "Failed to change password")
		return
	}

	h.RespondSuccess(w, nil, "Password changed successfully")
}

// HandleRequestPasswordReset handles POST /api/v1/users/reset-password
func (h *UserHandler) HandleRequestPasswordReset(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse request
	var req models.PasswordResetRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Request password reset
	if err := h.server.Services.User.RequestPasswordReset(r.Context(), req.Email); err != nil {
		h.HandleError(w, r, err, "Failed to request password reset")
		return
	}

	h.RespondSuccess(w, nil, "Password reset email sent")
}

// HandleConfirmPasswordReset handles POST /api/v1/users/reset-password/confirm
func (h *UserHandler) HandleConfirmPasswordReset(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse request
	var req models.PasswordResetConfirmRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Confirm password reset
	if err := h.server.Services.User.ConfirmPasswordReset(r.Context(), req.Token, req.NewPassword); err != nil {
		h.HandleError(w, r, err, "Failed to confirm password reset")
		return
	}

	h.RespondSuccess(w, nil, "Password reset successfully")
}

// HandleGetUserOrganizations handles GET /api/v1/users/{id}/organizations
func (h *UserHandler) HandleGetUserOrganizations(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Validate access
	_, ok := h.ValidateUserAccess(w, r, userID)
	if !ok {
		return
	}

	// Get user organizations
	organizations, err := h.server.Services.User.GetUserOrganizations(r.Context(), userID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve user organizations")
		return
	}

	h.RespondJSON(w, http.StatusOK, organizations)
}

// HandleGetUserSessions handles GET /api/v1/users/{id}/sessions
func (h *UserHandler) HandleGetUserSessions(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Validate access
	_, ok := h.ValidateUserAccess(w, r, userID)
	if !ok {
		return
	}

	// Get user sessions
	sessions, err := h.server.Services.User.GetUserSessions(r.Context(), userID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve user sessions")
		return
	}

	h.RespondJSON(w, http.StatusOK, sessions)
}

// HandleDeleteUserSession handles DELETE /api/v1/users/{id}/sessions/{sessionId}
func (h *UserHandler) HandleDeleteUserSession(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse user ID
	userID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Parse session ID
	sessionID, err := h.ParseID(r, "sessionId")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid session ID")
		return
	}

	// Validate access
	_, ok := h.ValidateUserAccess(w, r, userID)
	if !ok {
		return
	}

	// Delete session
	if err := h.server.Services.User.DeleteSession(r.Context(), userID, sessionID); err != nil {
		h.HandleError(w, r, err, "Failed to delete session")
		return
	}

	h.RespondSuccess(w, nil, "Session deleted successfully")
}

// HandleUpdateCurrentUser handles PUT /api/v1/users/me
func (h *UserHandler) HandleUpdateCurrentUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get current user
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.UpdateUserRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Convert to updates map
	updates := make(map[string]interface{})
	if req.Name != nil && *req.Name != "" {
		updates["name"] = *req.Name
	}
	if req.Email != nil && *req.Email != "" {
		updates["email"] = *req.Email
	}

	// Update user
	updatedUser, err := h.server.Services.User.UpdateUser(r.Context(), user.ID, updates)
	if err != nil {
		h.HandleError(w, r, err, "Failed to update user")
		return
	}

	// Convert to response format
	if u, ok := updatedUser.(*domainmodels.User); ok {
		h.RespondJSON(w, http.StatusOK, models.UserToResponse(u))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid user data")
	}
}

// HandleChangeCurrentUserPassword handles POST /api/v1/users/me/change-password
func (h *UserHandler) HandleChangeCurrentUserPassword(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get current user
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.ChangePasswordRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Change password
	if err := h.server.Services.User.ChangePassword(r.Context(), user.ID, req.CurrentPassword, req.NewPassword); err != nil {
		h.HandleError(w, r, err, "Failed to change password")
		return
	}

	h.RespondSuccess(w, nil, "Password changed successfully")
}

// Legacy handler functions for backward compatibility
func HandleGetUsers(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleGetUsers
}

func HandleGetUser(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleGetUser
}

func HandleCreateUser(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleCreateUser
}

func HandleUpdateUser(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleUpdateUser
}

func HandleDeleteUser(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleDeleteUser
}

func HandleChangePassword(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleChangePassword
}

func HandleRequestPasswordReset(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleRequestPasswordReset
}

func HandleConfirmPasswordReset(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleConfirmPasswordReset
}

func HandleGetUserOrganizations(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleGetUserOrganizations
}

func HandleGetUserSessions(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleGetUserSessions
}

func HandleDeleteUserSession(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleDeleteUserSession
}

func HandleUpdateCurrentUser(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleUpdateCurrentUser
}

func HandleChangeCurrentUserPassword(s *types.Server) http.HandlerFunc {
	handler := NewUserHandler(s)
	return handler.HandleChangeCurrentUserPassword
}
