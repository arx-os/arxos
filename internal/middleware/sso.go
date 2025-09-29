package middleware

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/auth"
	"github.com/arx-os/arxos/internal/common/logger"
)

// SSOMiddleware provides SSO authentication middleware
type SSOMiddleware struct {
	ssoManager *auth.SSOManager
	providers  map[string]bool
}

// NewSSOMiddleware creates a new SSO middleware
func NewSSOMiddleware(ssoManager *auth.SSOManager) *SSOMiddleware {
	return &SSOMiddleware{
		ssoManager: ssoManager,
		providers:  make(map[string]bool),
	}
}

// EnableProvider enables an SSO provider
func (sm *SSOMiddleware) EnableProvider(providerName string) {
	sm.providers[providerName] = true
}

// Middleware returns the HTTP middleware function for SSO
func (sm *SSOMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if SSO is required for this path
		if !sm.requiresSSO(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Extract SSO provider from query parameter or header
		providerName := r.URL.Query().Get("sso_provider")
		if providerName == "" {
			providerName = r.Header.Get("X-SSO-Provider")
		}

		if providerName == "" {
			// Default to first enabled provider
			for provider := range sm.providers {
				providerName = provider
				break
			}
		}

		if providerName == "" {
			logger.Debug("No SSO provider specified")
			http.Error(w, "SSO provider required", http.StatusBadRequest)
			return
		}

		// Check if provider is enabled
		if !sm.providers[providerName] {
			logger.Debug("SSO provider '%s' not enabled", providerName)
			http.Error(w, "SSO provider not enabled", http.StatusBadRequest)
			return
		}

		// Extract credentials based on provider type
		credentials := sm.extractCredentials(r, providerName)
		if credentials == nil {
			logger.Debug("Failed to extract credentials for provider '%s'", providerName)
			http.Error(w, "Invalid credentials", http.StatusBadRequest)
			return
		}

		// Authenticate via SSO
		user, err := sm.ssoManager.Authenticate(r.Context(), providerName, credentials)
		if err != nil {
			logger.Debug("SSO authentication failed: %v", err)
			http.Error(w, "Authentication failed", http.StatusUnauthorized)
			return
		}

		// Generate JWT token
		token, err := sm.ssoManager.GenerateJWT(user)
		if err != nil {
			logger.Error("Failed to generate JWT: %v", err)
			http.Error(w, "Authentication failed", http.StatusInternalServerError)
			return
		}

		// Add user and token to context
		ctx := context.WithValue(r.Context(), UserContextKey, &User{
			ID:    user.ID,
			Email: user.Email,
			Role:  sm.determineRole(user),
		})
		ctx = context.WithValue(ctx, "sso_user", user)
		ctx = context.WithValue(ctx, "sso_token", token)

		// Set token in response header
		w.Header().Set("Authorization", "Bearer "+token)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// requiresSSO checks if a path requires SSO authentication
func (sm *SSOMiddleware) requiresSSO(path string) bool {
	// SSO required paths
	ssoPaths := []string{
		"/api/v1/sso/",
		"/api/v1/auth/sso/",
	}

	for _, ssoPath := range ssoPaths {
		if strings.HasPrefix(path, ssoPath) {
			return true
		}
	}

	return false
}

// extractCredentials extracts credentials based on provider type
func (sm *SSOMiddleware) extractCredentials(r *http.Request, providerName string) map[string]string {
	credentials := make(map[string]string)

	// Extract based on provider type
	switch providerName {
	case "oauth2":
		// OAuth2 uses authorization code
		code := r.URL.Query().Get("code")
		if code == "" {
			code = r.Header.Get("X-Auth-Code")
		}
		if code != "" {
			credentials["code"] = code
		}

	case "ldap":
		// LDAP uses username/password
		username := r.Header.Get("X-Username")
		password := r.Header.Get("X-Password")

		// Also check form data
		if username == "" {
			username = r.FormValue("username")
		}
		if password == "" {
			password = r.FormValue("password")
		}

		if username != "" && password != "" {
			credentials["username"] = username
			credentials["password"] = password
		}

	case "saml":
		// SAML uses assertion
		assertion := r.FormValue("SAMLResponse")
		if assertion == "" {
			assertion = r.Header.Get("X-SAML-Assertion")
		}
		if assertion != "" {
			credentials["assertion"] = assertion
		}
	}

	return credentials
}

// determineRole determines user role from SSO user data
func (sm *SSOMiddleware) determineRole(user *auth.SSOUser) string {
	// Default role
	role := "user"

	// Check roles array
	for _, userRole := range user.Roles {
		switch strings.ToLower(userRole) {
		case "admin", "administrator":
			return "admin"
		case "manager", "supervisor":
			if role == "user" {
				role = "manager"
			}
		case "operator":
			if role == "user" {
				role = "operator"
			}
		}
	}

	// Check groups for role mapping
	for _, group := range user.Groups {
		switch strings.ToLower(group) {
		case "admins", "administrators":
			return "admin"
		case "managers", "supervisors":
			if role == "user" {
				role = "manager"
			}
		case "operators":
			if role == "user" {
				role = "operator"
			}
		}
	}

	return role
}

// SSOAuthHandler handles SSO authentication endpoints
type SSOAuthHandler struct {
	ssoManager *auth.SSOManager
}

// NewSSOAuthHandler creates a new SSO auth handler
func NewSSOAuthHandler(ssoManager *auth.SSOManager) *SSOAuthHandler {
	return &SSOAuthHandler{
		ssoManager: ssoManager,
	}
}

// HandleOAuth2Callback handles OAuth2 callback
func (h *SSOAuthHandler) HandleOAuth2Callback(w http.ResponseWriter, r *http.Request) {
	providerName := r.URL.Query().Get("provider")
	if providerName == "" {
		http.Error(w, "Provider parameter required", http.StatusBadRequest)
		return
	}

	code := r.URL.Query().Get("code")
	if code == "" {
		http.Error(w, "Authorization code required", http.StatusBadRequest)
		return
	}

	// Authenticate via OAuth2
	credentials := map[string]string{"code": code}
	user, err := h.ssoManager.Authenticate(r.Context(), providerName, credentials)
	if err != nil {
		logger.Error("OAuth2 authentication failed: %v", err)
		http.Error(w, "Authentication failed", http.StatusUnauthorized)
		return
	}

	// Generate JWT token
	token, err := h.ssoManager.GenerateJWT(user)
	if err != nil {
		logger.Error("Failed to generate JWT: %v", err)
		http.Error(w, "Authentication failed", http.StatusInternalServerError)
		return
	}

	// Return success response
	response := map[string]interface{}{
		"success": true,
		"token":   token,
		"user": map[string]interface{}{
			"id":       user.ID,
			"email":    user.Email,
			"name":     user.Name,
			"username": user.Username,
			"groups":   user.Groups,
			"roles":    user.Roles,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// HandleLDAPAuth handles LDAP authentication
func (h *SSOAuthHandler) HandleLDAPAuth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	username := r.FormValue("username")
	password := r.FormValue("password")

	if username == "" || password == "" {
		http.Error(w, "Username and password required", http.StatusBadRequest)
		return
	}

	// Authenticate via LDAP
	credentials := map[string]string{
		"username": username,
		"password": password,
	}
	user, err := h.ssoManager.Authenticate(r.Context(), "ldap", credentials)
	if err != nil {
		logger.Error("LDAP authentication failed: %v", err)
		http.Error(w, "Authentication failed", http.StatusUnauthorized)
		return
	}

	// Generate JWT token
	token, err := h.ssoManager.GenerateJWT(user)
	if err != nil {
		logger.Error("Failed to generate JWT: %v", err)
		http.Error(w, "Authentication failed", http.StatusInternalServerError)
		return
	}

	// Return success response
	response := map[string]interface{}{
		"success": true,
		"token":   token,
		"user": map[string]interface{}{
			"id":       user.ID,
			"email":    user.Email,
			"name":     user.Name,
			"username": user.Username,
			"groups":   user.Groups,
			"roles":    user.Roles,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// HandleSSOProviders returns available SSO providers
func (h *SSOAuthHandler) HandleSSOProviders(w http.ResponseWriter, r *http.Request) {
	providers := []map[string]interface{}{
		{
			"name":        "oauth2",
			"type":        "oauth2",
			"enabled":     true,
			"description": "OAuth2 Single Sign-On",
		},
		{
			"name":        "ldap",
			"type":        "ldap",
			"enabled":     true,
			"description": "LDAP Authentication",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"providers": providers,
	})
}
