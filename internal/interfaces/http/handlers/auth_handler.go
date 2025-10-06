package handlers

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/arx-os/arxos/pkg/auth"
)

// AuthHandler handles authentication-related HTTP requests following Clean Architecture
type AuthHandler struct {
	BaseHandler
	userUC *usecase.UserUseCase
	jwtMgr *auth.JWTManager
	logger domain.Logger
}

// NewAuthHandler creates a new authentication handler with proper dependency injection
func NewAuthHandler(
	base BaseHandler,
	userUC *usecase.UserUseCase,
	jwtMgr *auth.JWTManager,
	logger domain.Logger,
) *AuthHandler {
	return &AuthHandler{
		BaseHandler: base,
		userUC:      userUC,
		jwtMgr:      jwtMgr,
		logger:      logger,
	}
}

// Mobile-specific auth request/response types
type MobileLoginRequest struct {
	Username string `json:"username" validate:"required"`
	Password string `json:"password" validate:"required"`
}

type MobileRegisterRequest struct {
	Username string `json:"username" validate:"required"`
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=8"`
	FullName string `json:"full_name,omitempty"`
	OrgID    string `json:"organization_id,omitempty"`
}

type MobileAuthTokensResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
	TokenType    string `json:"token_type"`
}

type MobileUserResponse struct {
	ID             string   `json:"id"`
	Username       string   `json:"username"`
	Email          string   `json:"email"`
	Role           string   `json:"role"`
	Permissions    []string `json:"permissions"`
	OrganizationID string   `json:"organization_id,omitempty"`
	FullName       string   `json:"full_name,omitempty"`
	Avatar         string   `json:"avatar,omitempty"`
}

type MobileAuthError struct {
	Code    string         `json:"code"`
	Message string         `json:"message"`
	Details map[string]any `json:"details,omitempty"`
}

// HandleMobileLogin handles POST /api/v1/mobile/auth/login
func (h *AuthHandler) HandleMobileLogin(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	var req MobileLoginRequest
	if err := h.ParseRequestBody(r, &req); err != nil {
		h.logger.Error("Invalid login request body", "error", err)
		h.RespondJSON(w, http.StatusBadRequest, MobileAuthError{
			Code:    "invalid_request",
			Message: "Invalid request body",
		})
		return
	}

	// Authenticate user using domain layer
	ctx := r.Context()
	user, err := h.userUC.AuthenticateUser(ctx, req.Username, req.Password)
	if err != nil {
		h.logger.Warn("Authentication failed", "username", req.Username)
		h.RespondJSON(w, http.StatusUnauthorized, MobileAuthError{
			Code:    "invalid_credentials",
			Message: "Invalid username or password",
		})
		return
	}

	// Generate JWT tokens using actual auth package
	jwtCfg := auth.DefaultJWTConfig()
	jwtMgr, err := auth.NewJWTManager(jwtCfg)
	if err != nil {
		h.logger.Error("Failed to create JWT manager", "error", err)
		h.RespondJSON(w, http.StatusInternalServerError, MobileAuthError{
			Code:    "jwt_manager_error",
			Message: "Failed to initialize JWT manager",
		})
		return
	}

	tokenPair, err := jwtMgr.GenerateTokenPair(user.ID.String(), user.Email, user.Name, user.Role, "", []string{"mobile_access"}, "", map[string]any{
		"platform": "mobile",
		"app":      "arxos_mobile",
	})
	if err != nil {
		h.logger.Error("Failed to generate tokens", "error", err)
		h.RespondJSON(w, http.StatusInternalServerError, MobileAuthError{
			Code:    "token_generation_failed",
			Message: "Failed to generate tokens",
		})
		return
	}

	// Create response using actual domain structure
	userResponse := &MobileUserResponse{
		ID:          user.ID.String(),
		Username:    user.Name, // Use Name as Username for now
		Email:       user.Email,
		Role:        user.Role,
		Permissions: []string{"mobile_access"}, // Default permissions
		FullName:    user.Name,
	}

	tokensResponse := &MobileAuthTokensResponse{
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		ExpiresIn:    int(tokenPair.ExpiresIn),
		TokenType:    tokenPair.TokenType,
	}

	response := map[string]any{
		"user":   userResponse,
		"tokens": tokensResponse,
	}

	h.logger.Info("Mobile login successful", "user_id", user.ID)
	h.RespondJSON(w, http.StatusOK, response)
}

// HandleMobileRegister handles POST /api/v1/mobile/auth/register
func (h *AuthHandler) HandleMobileRegister(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	var req MobileRegisterRequest
	if err := h.ParseRequestBody(r, &req); err != nil {
		h.logger.Error("Invalid register request body", "error", err)
		h.RespondJSON(w, http.StatusBadRequest, MobileAuthError{
			Code:    "invalid_request",
			Message: "Invalid request body",
		})
		return
	}

	// Create user using domain layer
	ctx := r.Context()
	createReq := &domain.CreateUserRequest{
		Email: req.Email,
		Name:  req.Username,  // Use Username as Name
		Role:  "mobile_user", // Default role for mobile users
	}

	user, err := h.userUC.CreateUser(ctx, createReq)
	if err != nil {
		h.logger.Error("User registration failed", "error", err, "username", req.Username)
		h.RespondJSON(w, http.StatusConflict, MobileAuthError{
			Code:    "user_already_exists",
			Message: "User already exists with this username or email",
		})
		return
	}

	// Generate tokens for new user
	jwtCfg := auth.DefaultJWTConfig()
	jwtMgr, err := auth.NewJWTManager(jwtCfg)
	if err != nil {
		h.logger.Error("Failed to create JWT manager", "error", err)
		h.RespondJSON(w, http.StatusInternalServerError, MobileAuthError{
			Code:    "jwt_manager_error",
			Message: "Failed to initialize JWT manager",
		})
		return
	}

	tokenPair, err := jwtMgr.GenerateTokenPair(user.ID.String(), user.Email, user.Name, user.Role, "", []string{"mobile_access"}, "", map[string]any{
		"platform": "mobile",
		"app":      "arxos_mobile",
	})
	if err != nil {
		h.logger.Error("Failed to generate tokens for new user", "error", err)
		h.RespondJSON(w, http.StatusInternalServerError, MobileAuthError{
			Code:    "token_generation_failed",
			Message: "Failed to generate tokens",
		})
		return
	}

	// Create response using actual domain structure
	userResponse := &MobileUserResponse{
		ID:          user.ID.String(),
		Username:    user.Name,
		Email:       user.Email,
		Role:        user.Role,
		Permissions: []string{"mobile_access"},
		FullName:    user.Name,
	}

	tokensResponse := &MobileAuthTokensResponse{
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		ExpiresIn:    int(tokenPair.ExpiresIn),
		TokenType:    tokenPair.TokenType,
	}

	response := map[string]any{
		"user":   userResponse,
		"tokens": tokensResponse,
	}

	h.logger.Info("Mobile user registered successfully", "user_id", user.ID)
	h.RespondJSON(w, http.StatusCreated, response)
}

// HandleMobileRefreshToken handles POST /api/v1/mobile/auth/refresh
func (h *AuthHandler) HandleMobileRefreshToken(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	var req struct {
		RefreshToken string `json:"refresh_token" validate:"required"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.logger.Error("Invalid refresh request body", "error", err)
		h.RespondJSON(w, http.StatusBadRequest, MobileAuthError{
			Code:    "invalid_request",
			Message: "Invalid request body",
		})
		return
	}

	// Create JWT manager for validation
	jwtCfg := auth.DefaultJWTConfig()
	jwtMgr, err := auth.NewJWTManager(jwtCfg)
	if err != nil {
		h.logger.Error("Failed to create JWT manager", "error", err)
		h.RespondJSON(w, http.StatusInternalServerError, MobileAuthError{
			Code:    "jwt_manager_error",
			Message: "Failed to initialize JWT manager",
		})
		return
	}

	// Validate refresh token and extract claims
	claims, err := jwtMgr.ValidateToken(req.RefreshToken)
	if err != nil {
		h.logger.Warn("Invalid refresh token", "error", err)
		h.RespondJSON(w, http.StatusUnauthorized, MobileAuthError{
			Code:    "invalid_refresh_token",
			Message: "Invalid or expired refresh token",
		})
		return
	}

	// Get user to validate they still exist
	ctx := r.Context()
	user, err := h.userUC.GetUser(ctx, claims.UserID)
	if err != nil {
		h.logger.Warn("User not found during refresh", "user_id", claims.UserID, "error", err)
		h.RespondJSON(w, http.StatusUnauthorized, MobileAuthError{
			Code:    "user_not_found",
			Message: "User account no longer exists",
		})
		return
	}

	// Generate new tokens
	tokenPair, err := jwtMgr.GenerateTokenPair(user.ID.String(), user.Email, user.Name, user.Role, claims.OrganizationID, claims.Permissions, "", map[string]any{
		"platform": "mobile",
		"app":      "arxos_mobile",
	})
	if err != nil {
		h.logger.Error("Failed to generate new tokens", "error", err)
		h.RespondJSON(w, http.StatusInternalServerError, MobileAuthError{
			Code:    "token_generation_failed",
			Message: "Failed to generate new tokens",
		})
		return
	}

	// Create response using actual domain structure
	userResponse := &MobileUserResponse{
		ID:             user.ID.String(),
		Username:       user.Name,
		Email:          user.Email,
		Role:           user.Role,
		Permissions:    claims.Permissions,
		OrganizationID: claims.OrganizationID,
		FullName:       user.Name,
	}

	tokensResponse := &MobileAuthTokensResponse{
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		ExpiresIn:    int(tokenPair.ExpiresIn),
		TokenType:    tokenPair.TokenType,
	}

	response := map[string]any{
		"user":   userResponse,
		"tokens": tokensResponse,
	}

	h.logger.Info("Mobile token refresh successful", "user_id", user.ID)
	h.RespondJSON(w, http.StatusOK, response)
}

// HandleMobileProfile handles GET /api/v1/mobile/auth/profile
func (h *AuthHandler) HandleMobileProfile(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get user from context (set by auth middleware)
	userID := r.Context().Value("user_id").(string)

	ctx := r.Context()
	user, err := h.userUC.GetUser(ctx, userID)
	if err != nil {
		h.logger.Error("Failed to get user profile", "user_id", userID, "error", err)
		h.RespondJSON(w, http.StatusNotFound, MobileAuthError{
			Code:    "user_not_found",
			Message: "User profile not found",
		})
		return
	}

	// Create response using actual domain structure
	userResponse := &MobileUserResponse{
		ID:          user.ID.String(),
		Username:    user.Name,
		Email:       user.Email,
		Role:        user.Role,
		Permissions: []string{"mobile_access"}, // Default permissions
		FullName:    user.Name,
	}

	h.logger.Info("Mobile profile retrieved", "user_id", user.ID)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"user": userResponse,
	})
}

// HandleMobileLogout handles POST /api/v1/mobile/auth/logout
func (h *AuthHandler) HandleMobileLogout(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get user from context
	userID := r.Context().Value("user_id").(string)

	// TODO: Implement token blacklisting/revocation if needed
	// For now, just log the logout

	h.logger.Info("Mobile user logged out", "user_id", userID)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"message": "Successfully logged out",
	})
}
