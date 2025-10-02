package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/models"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
	pkgmodels "github.com/arx-os/arxos/pkg/models"
)

// UserHandler handles user-related HTTP requests
type UserHandler struct {
	*BaseHandler
	userService *usecase.UserUseCase
}

// NewUserHandler creates a new user handler
func NewUserHandler(server *types.Server, userService *usecase.UserUseCase) *UserHandler {
	return &UserHandler{
		BaseHandler: NewBaseHandler(server),
		userService: userService,
	}
}

// HandleGetUsers handles GET /api/v1/users
func (h *UserHandler) HandleGetUsers(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse pagination parameters
	limit, offset := h.parsePagination(r)

	// Parse filters
	roleStr := r.URL.Query().Get("role")
	var role *string
	if roleStr != "" {
		role = &roleStr
	}

	filter := &domain.UserFilter{
		Role: role,
	}

	// Get users from service
	users, err := h.userService.ListUsers(r.Context(), filter)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Convert domain users to HTTP models
	var userModels []*pkgmodels.User
	for _, user := range users {
		userModels = append(userModels, &pkgmodels.User{
			ID:        user.ID,
			Email:     user.Email,
			FullName:  user.Name,
			Role:      user.Role,
			IsActive:  user.Active,
			CreatedAt: user.CreatedAt,
			UpdatedAt: user.UpdatedAt,
		})
	}

	// Convert to response format
	response := models.UserListResponse{
		Users:  userModels,
		Total:  len(userModels), // This should come from the service
		Limit:  limit,
		Offset: offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleGetUser handles GET /api/v1/users/{id}
func (h *UserHandler) HandleGetUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Extract user ID from URL path
	userID := h.extractIDFromPath(r.URL.Path, "/api/v1/users/")
	if userID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Get user from service
	user, err := h.userService.GetUser(r.Context(), userID)
	if err != nil {
		h.HandleError(w, r, err, http.StatusNotFound)
		return
	}

	h.RespondJSON(w, http.StatusOK, user)
}

// HandleCreateUser handles POST /api/v1/users
func (h *UserHandler) HandleCreateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Parse request body
	var req models.CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, err, http.StatusBadRequest)
		return
	}

	// Validate request
	if err := h.validateCreateUserRequest(&req); err != nil {
		h.HandleError(w, r, err, http.StatusBadRequest)
		return
	}

	// Convert HTTP model to domain model
	domainReq := &domain.CreateUserRequest{
		Email: req.Email,
		Name:  req.Name,
		Role:  req.Role,
	}

	// Create user through service
	user, err := h.userService.CreateUser(r.Context(), domainReq)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	h.RespondJSON(w, http.StatusCreated, user)
}

// HandleUpdateUser handles PUT /api/v1/users/{id}
func (h *UserHandler) HandleUpdateUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Extract user ID from URL path
	userID := h.extractIDFromPath(r.URL.Path, "/api/v1/users/")
	if userID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Parse request body
	var req models.UpdateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, err, http.StatusBadRequest)
		return
	}

	// Convert HTTP model to domain model
	domainReq := &domain.UpdateUserRequest{
		ID:   userID,
		Name: req.Name,
		Role: req.Role,
	}

	// Update user through service
	user, err := h.userService.UpdateUser(r.Context(), domainReq)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	h.RespondJSON(w, http.StatusOK, user)
}

// HandleDeleteUser handles DELETE /api/v1/users/{id}
func (h *UserHandler) HandleDeleteUser(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	// Extract user ID from URL path
	userID := h.extractIDFromPath(r.URL.Path, "/api/v1/users/")
	if userID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Delete user through service
	if err := h.userService.DeleteUser(r.Context(), userID); err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// Helper methods

func (h *UserHandler) parsePagination(r *http.Request) (int, int) {
	limitStr := r.URL.Query().Get("limit")
	offsetStr := r.URL.Query().Get("offset")

	limit := 20 // default
	offset := 0 // default

	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	return limit, offset
}

func (h *UserHandler) extractIDFromPath(path, prefix string) string {
	if len(path) <= len(prefix) {
		return ""
	}
	return path[len(prefix):]
}

func (h *UserHandler) validateCreateUserRequest(req *models.CreateUserRequest) error {
	if req.Email == "" {
		return fmt.Errorf("email is required")
	}
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	if req.Password == "" {
		return fmt.Errorf("password is required")
	}
	return nil
}
