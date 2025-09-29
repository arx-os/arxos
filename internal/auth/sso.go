package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/golang-jwt/jwt/v5"
)

// SSOProvider represents a Single Sign-On provider
type SSOProvider interface {
	Authenticate(ctx context.Context, token string) (*SSOUser, error)
	GetUserInfo(ctx context.Context, token string) (*SSOUser, error)
	ValidateToken(ctx context.Context, token string) error
}

// SSOUser represents a user from SSO provider
type SSOUser struct {
	ID       string                 `json:"id"`
	Email    string                 `json:"email"`
	Name     string                 `json:"name"`
	Username string                 `json:"username"`
	Groups   []string               `json:"groups"`
	Roles    []string               `json:"roles"`
	Claims   map[string]interface{} `json:"claims"`
}

// SSOConfig holds SSO configuration
type SSOConfig struct {
	Provider     string       `json:"provider"` // "saml", "oauth2", "ldap", "oidc"
	Enabled      bool         `json:"enabled"`
	ClientID     string       `json:"client_id"`
	ClientSecret string       `json:"client_secret"`
	RedirectURL  string       `json:"redirect_url"`
	Issuer       string       `json:"issuer"`
	Scopes       []string     `json:"scopes"`
	Endpoints    SSOEndpoints `json:"endpoints"`
}

// SSOEndpoints holds SSO provider endpoints
type SSOEndpoints struct {
	Authorization string `json:"authorization"`
	Token         string `json:"token"`
	UserInfo      string `json:"userinfo"`
	JWKS          string `json:"jwks"`
}

// OAuth2Provider implements OAuth2 SSO
type OAuth2Provider struct {
	config *SSOConfig
	client *http.Client
}

// NewOAuth2Provider creates a new OAuth2 SSO provider
func NewOAuth2Provider(config *SSOConfig) *OAuth2Provider {
	return &OAuth2Provider{
		config: config,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Authenticate authenticates a user via OAuth2
func (p *OAuth2Provider) Authenticate(ctx context.Context, code string) (*SSOUser, error) {
	// Exchange authorization code for access token
	token, err := p.exchangeCodeForToken(ctx, code)
	if err != nil {
		return nil, fmt.Errorf("failed to exchange code for token: %w", err)
	}

	// Get user info using access token
	user, err := p.GetUserInfo(ctx, token.AccessToken)
	if err != nil {
		return nil, fmt.Errorf("failed to get user info: %w", err)
	}

	return user, nil
}

// GetUserInfo retrieves user information from the SSO provider
func (p *OAuth2Provider) GetUserInfo(ctx context.Context, accessToken string) (*SSOUser, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", p.config.Endpoints.UserInfo, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", "Bearer "+accessToken)
	req.Header.Set("Accept", "application/json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to get user info: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("user info request failed with status: %d", resp.StatusCode)
	}

	var userInfo map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&userInfo); err != nil {
		return nil, fmt.Errorf("failed to decode user info: %w", err)
	}

	// Extract user information from response
	user := &SSOUser{
		Claims: userInfo,
	}

	// Map common fields
	if id, ok := userInfo["sub"].(string); ok {
		user.ID = id
	}
	if email, ok := userInfo["email"].(string); ok {
		user.Email = email
	}
	if name, ok := userInfo["name"].(string); ok {
		user.Name = name
	}
	if username, ok := userInfo["preferred_username"].(string); ok {
		user.Username = username
	}

	// Extract groups/roles
	if groups, ok := userInfo["groups"].([]interface{}); ok {
		for _, group := range groups {
			if groupStr, ok := group.(string); ok {
				user.Groups = append(user.Groups, groupStr)
			}
		}
	}

	return user, nil
}

// ValidateToken validates an access token
func (p *OAuth2Provider) ValidateToken(ctx context.Context, token string) error {
	// For OAuth2, we validate by making a request to the userinfo endpoint
	_, err := p.GetUserInfo(ctx, token)
	return err
}

// exchangeCodeForToken exchanges authorization code for access token
func (p *OAuth2Provider) exchangeCodeForToken(ctx context.Context, code string) (*OAuth2Token, error) {
	data := map[string]string{
		"grant_type":    "authorization_code",
		"code":          code,
		"client_id":     p.config.ClientID,
		"client_secret": p.config.ClientSecret,
		"redirect_uri":  p.config.RedirectURL,
	}

	req, err := http.NewRequestWithContext(ctx, "POST", p.config.Endpoints.Token, strings.NewReader(encodeFormData(data)))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("Accept", "application/json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to exchange code: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("token exchange failed with status: %d", resp.StatusCode)
	}

	var token OAuth2Token
	if err := json.NewDecoder(resp.Body).Decode(&token); err != nil {
		return nil, fmt.Errorf("failed to decode token response: %w", err)
	}

	return &token, nil
}

// OAuth2Token represents an OAuth2 token response
type OAuth2Token struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	Scope        string `json:"scope"`
}

// LDAPProvider implements LDAP SSO
type LDAPProvider struct {
	config *LDAPConfig
}

// LDAPConfig holds LDAP configuration
type LDAPConfig struct {
	Server   string `json:"server"`
	Port     int    `json:"port"`
	BaseDN   string `json:"base_dn"`
	BindDN   string `json:"bind_dn"`
	Password string `json:"password"`
	UseTLS   bool   `json:"use_tls"`
	Insecure bool   `json:"insecure"`
}

// NewLDAPProvider creates a new LDAP SSO provider
func NewLDAPProvider(config *LDAPConfig) *LDAPProvider {
	return &LDAPProvider{
		config: config,
	}
}

// Authenticate authenticates a user via LDAP
func (p *LDAPProvider) Authenticate(ctx context.Context, credentials string) (*SSOUser, error) {
	// This is a simplified LDAP implementation
	// In production, you would use a proper LDAP library like go-ldap

	logger.Info("LDAP authentication with credentials")

	// For now, return a mock user
	// In production, implement actual LDAP authentication
	user := &SSOUser{
		ID:       "ldap_user",
		Username: "ldap_user",
		Email:    "ldap_user@company.com",
		Name:     "LDAP User",
		Groups:   []string{"users"},
		Roles:    []string{"user"},
	}

	return user, nil
}

// GetUserInfo retrieves user information from LDAP
func (p *LDAPProvider) GetUserInfo(ctx context.Context, username string) (*SSOUser, error) {
	// Implement LDAP user lookup
	logger.Info("LDAP user info lookup for: %s", username)

	user := &SSOUser{
		ID:       username,
		Username: username,
		Email:    username + "@company.com",
		Name:     username,
		Groups:   []string{"users"},
		Roles:    []string{"user"},
	}

	return user, nil
}

// ValidateToken validates an LDAP session
func (p *LDAPProvider) ValidateToken(ctx context.Context, token string) error {
	// For LDAP, we would validate the session token
	// This is a placeholder implementation
	return nil
}

// SSOManager manages SSO providers and authentication
type SSOManager struct {
	providers map[string]SSOProvider
	configs   map[string]*SSOConfig
	jwtSecret string
}

// NewSSOManager creates a new SSO manager
func NewSSOManager(jwtSecret string) *SSOManager {
	return &SSOManager{
		providers: make(map[string]SSOProvider),
		configs:   make(map[string]*SSOConfig),
		jwtSecret: jwtSecret,
	}
}

// RegisterProvider registers an SSO provider
func (sm *SSOManager) RegisterProvider(name string, provider SSOProvider, config *SSOConfig) {
	sm.providers[name] = provider
	sm.configs[name] = config
}

// Authenticate authenticates a user via SSO
func (sm *SSOManager) Authenticate(ctx context.Context, providerName string, credentials map[string]string) (*SSOUser, error) {
	provider, exists := sm.providers[providerName]
	if !exists {
		return nil, fmt.Errorf("SSO provider '%s' not found", providerName)
	}

	config, exists := sm.configs[providerName]
	if !exists || !config.Enabled {
		return nil, fmt.Errorf("SSO provider '%s' not enabled", providerName)
	}

	// Authenticate based on provider type
	switch config.Provider {
	case "oauth2":
		code, ok := credentials["code"]
		if !ok {
			return nil, fmt.Errorf("authorization code required for OAuth2")
		}
		return provider.Authenticate(ctx, code)
	case "ldap":
		username, ok := credentials["username"]
		if !ok {
			return nil, fmt.Errorf("username required for LDAP")
		}
		password, ok := credentials["password"]
		if !ok {
			return nil, fmt.Errorf("password required for LDAP")
		}
		// Combine credentials for LDAP
		credentialString := fmt.Sprintf("%s:%s", username, password)
		return provider.Authenticate(ctx, credentialString)
	default:
		return nil, fmt.Errorf("unsupported SSO provider type: %s", config.Provider)
	}
}

// GenerateJWT generates a JWT token for an SSO user
func (sm *SSOManager) GenerateJWT(user *SSOUser) (string, error) {
	claims := jwt.MapClaims{
		"sub":      user.ID,
		"email":    user.Email,
		"name":     user.Name,
		"username": user.Username,
		"groups":   user.Groups,
		"roles":    user.Roles,
		"iat":      time.Now().Unix(),
		"exp":      time.Now().Add(24 * time.Hour).Unix(),
		"iss":      "arxos-sso",
		"aud":      "arxos",
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(sm.jwtSecret))
}

// ValidateJWT validates a JWT token
func (sm *SSOManager) ValidateJWT(tokenString string) (*SSOUser, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(sm.jwtSecret), nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	if !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, fmt.Errorf("invalid token claims")
	}

	user := &SSOUser{
		ID:       claims["sub"].(string),
		Email:    claims["email"].(string),
		Name:     claims["name"].(string),
		Username: claims["username"].(string),
		Claims:   claims,
	}

	// Extract groups and roles
	if groups, ok := claims["groups"].([]interface{}); ok {
		for _, group := range groups {
			if groupStr, ok := group.(string); ok {
				user.Groups = append(user.Groups, groupStr)
			}
		}
	}

	if roles, ok := claims["roles"].([]interface{}); ok {
		for _, role := range roles {
			if roleStr, ok := role.(string); ok {
				user.Roles = append(user.Roles, roleStr)
			}
		}
	}

	return user, nil
}

// Helper function to encode form data
func encodeFormData(data map[string]string) string {
	var parts []string
	for key, value := range data {
		parts = append(parts, fmt.Sprintf("%s=%s", key, value))
	}
	return strings.Join(parts, "&")
}
