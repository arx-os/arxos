// Package auth provides API key authentication utilities.
package auth

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

// APIKeyConfig holds configuration for API key management
type APIKeyConfig struct {
	// Key prefix for identification
	Prefix string

	// Key length (excluding prefix)
	KeyLength int

	// Default expiration time
	DefaultExpiration time.Duration

	// Maximum keys per user
	MaxKeysPerUser int

	// Maximum keys per organization
	MaxKeysPerOrganization int

	// Default rate limit (requests per hour)
	DefaultRateLimit int
}

// DefaultAPIKeyConfig returns a default API key configuration
func DefaultAPIKeyConfig() *APIKeyConfig {
	return &APIKeyConfig{
		Prefix:                 "arx_",
		KeyLength:              32,
		DefaultExpiration:      365 * 24 * time.Hour, // 1 year
		MaxKeysPerUser:         10,
		MaxKeysPerOrganization: 50,
		DefaultRateLimit:       1000, // 1000 requests per hour
	}
}

// APIKey represents an API access key
type APIKey struct {
	ID             string         `json:"id"`
	UserID         string         `json:"user_id,omitempty"`
	OrganizationID string         `json:"organization_id,omitempty"`
	Name           string         `json:"name"`
	KeyHash        string         `json:"-"` // Never expose in JSON
	LastFour       string         `json:"last_four"`
	Permissions    map[string]any `json:"permissions,omitempty"`
	RateLimit      int            `json:"rate_limit"`
	IsActive       bool           `json:"is_active"`
	LastUsedAt     *time.Time     `json:"last_used_at,omitempty"`
	ExpiresAt      *time.Time     `json:"expires_at,omitempty"`
	CreatedAt      time.Time      `json:"created_at"`
	UpdatedAt      time.Time      `json:"updated_at"`
}

// APIKeyCreateRequest represents a request to create an API key
type APIKeyCreateRequest struct {
	Name           string         `json:"name" validate:"required,min=1,max=100"`
	UserID         string         `json:"user_id,omitempty"`
	OrganizationID string         `json:"organization_id,omitempty"`
	Permissions    map[string]any `json:"permissions,omitempty"`
	RateLimit      int            `json:"rate_limit,omitempty"`
	ExpiresAt      *time.Time     `json:"expires_at,omitempty"`
}

// APIKeyResponse represents an API key response (includes the actual key)
type APIKeyResponse struct {
	*APIKey
	Key string `json:"key"` // Only included on creation
}

// APIKeyStore defines the interface for API key storage
type APIKeyStore interface {
	// Create creates a new API key
	Create(apiKey *APIKey) error

	// Get retrieves an API key by ID
	Get(id string) (*APIKey, error)

	// GetByHash retrieves an API key by hash
	GetByHash(hash string) (*APIKey, error)

	// Update updates an existing API key
	Update(apiKey *APIKey) error

	// Delete deletes an API key
	Delete(id string) error

	// ListByUserID lists all API keys for a user
	ListByUserID(userID string) ([]*APIKey, error)

	// ListByOrganizationID lists all API keys for an organization
	ListByOrganizationID(organizationID string) ([]*APIKey, error)

	// CleanupExpired removes expired API keys
	CleanupExpired() error
}

// APIKeyManager handles API key operations
type APIKeyManager struct {
	config *APIKeyConfig
	store  APIKeyStore
}

// NewAPIKeyManager creates a new API key manager
func NewAPIKeyManager(config *APIKeyConfig, store APIKeyStore) *APIKeyManager {
	if config == nil {
		config = DefaultAPIKeyConfig()
	}
	return &APIKeyManager{
		config: config,
		store:  store,
	}
}

// CreateAPIKey creates a new API key
func (akm *APIKeyManager) CreateAPIKey(req *APIKeyCreateRequest) (*APIKeyResponse, error) {
	// Validate request
	if err := akm.validateCreateRequest(req); err != nil {
		return nil, err
	}

	// Check key limits
	if err := akm.checkKeyLimits(req.UserID, req.OrganizationID); err != nil {
		return nil, err
	}

	// Generate API key
	key, keyHash, lastFour, err := akm.generateAPIKey()
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate API key")
	}

	// Set defaults
	rateLimit := req.RateLimit
	if rateLimit <= 0 {
		rateLimit = akm.config.DefaultRateLimit
	}

	expiresAt := req.ExpiresAt
	if expiresAt == nil {
		defaultExp := time.Now().Add(akm.config.DefaultExpiration)
		expiresAt = &defaultExp
	}

	now := time.Now()
	apiKey := &APIKey{
		ID:             akm.generateID(),
		UserID:         req.UserID,
		OrganizationID: req.OrganizationID,
		Name:           req.Name,
		KeyHash:        keyHash,
		LastFour:       lastFour,
		Permissions:    req.Permissions,
		RateLimit:      rateLimit,
		IsActive:       true,
		ExpiresAt:      expiresAt,
		CreatedAt:      now,
		UpdatedAt:      now,
	}

	if err := akm.store.Create(apiKey); err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to create API key")
	}

	return &APIKeyResponse{
		APIKey: apiKey,
		Key:    key,
	}, nil
}

// ValidateAPIKey validates an API key and returns the key info
func (akm *APIKeyManager) ValidateAPIKey(key string) (*APIKey, error) {
	if key == "" {
		return nil, errors.New(errors.CodeUnauthorized, "API key is required")
	}

	// Extract key from format (remove prefix if present)
	actualKey := key
	if strings.HasPrefix(key, akm.config.Prefix) {
		actualKey = strings.TrimPrefix(key, akm.config.Prefix)
	}

	// Hash the key
	keyHash := akm.hashKey(actualKey)

	// Look up the key
	apiKey, err := akm.store.GetByHash(keyHash)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeUnauthorized, "invalid API key")
	}

	// Check if key is active
	if !apiKey.IsActive {
		return nil, errors.New(errors.CodeUnauthorized, "API key is inactive")
	}

	// Check expiration
	if apiKey.ExpiresAt != nil && apiKey.ExpiresAt.Before(time.Now()) {
		return nil, errors.New(errors.CodeUnauthorized, "API key has expired")
	}

	// Update last used time
	now := time.Now()
	apiKey.LastUsedAt = &now
	apiKey.UpdatedAt = now

	if err := akm.store.Update(apiKey); err != nil {
		// Log error but don't fail validation
		// NOTE: Logging handled by infrastructure logger when wired
	}

	return apiKey, nil
}

// RevokeAPIKey revokes an API key
func (akm *APIKeyManager) RevokeAPIKey(id string) error {
	apiKey, err := akm.store.Get(id)
	if err != nil {
		return errors.Wrap(err, errors.CodeNotFound, "API key not found")
	}

	apiKey.IsActive = false
	apiKey.UpdatedAt = time.Now()

	return akm.store.Update(apiKey)
}

// ListUserAPIKeys lists all API keys for a user
func (akm *APIKeyManager) ListUserAPIKeys(userID string) ([]*APIKey, error) {
	keys, err := akm.store.ListByUserID(userID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to list user API keys")
	}

	// Filter active keys
	var activeKeys []*APIKey
	for _, key := range keys {
		if key.IsActive && (key.ExpiresAt == nil || key.ExpiresAt.After(time.Now())) {
			activeKeys = append(activeKeys, key)
		}
	}

	return activeKeys, nil
}

// ListOrganizationAPIKeys lists all API keys for an organization
func (akm *APIKeyManager) ListOrganizationAPIKeys(organizationID string) ([]*APIKey, error) {
	keys, err := akm.store.ListByOrganizationID(organizationID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to list organization API keys")
	}

	// Filter active keys
	var activeKeys []*APIKey
	for _, key := range keys {
		if key.IsActive && (key.ExpiresAt == nil || key.ExpiresAt.After(time.Now())) {
			activeKeys = append(activeKeys, key)
		}
	}

	return activeKeys, nil
}

// UpdateAPIKey updates an API key
func (akm *APIKeyManager) UpdateAPIKey(id string, updates map[string]any) error {
	apiKey, err := akm.store.Get(id)
	if err != nil {
		return errors.Wrap(err, errors.CodeNotFound, "API key not found")
	}

	// Update allowed fields
	if name, ok := updates["name"].(string); ok && name != "" {
		apiKey.Name = name
	}

	if permissions, ok := updates["permissions"].(map[string]any); ok {
		apiKey.Permissions = permissions
	}

	if rateLimit, ok := updates["rate_limit"].(int); ok && rateLimit > 0 {
		apiKey.RateLimit = rateLimit
	}

	if expiresAt, ok := updates["expires_at"].(*time.Time); ok {
		apiKey.ExpiresAt = expiresAt
	}

	if isActive, ok := updates["is_active"].(bool); ok {
		apiKey.IsActive = isActive
	}

	apiKey.UpdatedAt = time.Now()

	return akm.store.Update(apiKey)
}

// CleanupExpiredAPIKeys removes expired API keys
func (akm *APIKeyManager) CleanupExpiredAPIKeys() error {
	return akm.store.CleanupExpired()
}

// Helper methods

func (akm *APIKeyManager) validateCreateRequest(req *APIKeyCreateRequest) error {
	if req.Name == "" {
		return errors.New(errors.CodeInvalidInput, "API key name is required")
	}

	if len(req.Name) > 100 {
		return errors.New(errors.CodeInvalidInput, "API key name is too long")
	}

	if req.UserID == "" && req.OrganizationID == "" {
		return errors.New(errors.CodeInvalidInput, "either user_id or organization_id is required")
	}

	if req.RateLimit < 0 {
		return errors.New(errors.CodeInvalidInput, "rate limit cannot be negative")
	}

	if req.ExpiresAt != nil && req.ExpiresAt.Before(time.Now()) {
		return errors.New(errors.CodeInvalidInput, "expiration time cannot be in the past")
	}

	return nil
}

func (akm *APIKeyManager) checkKeyLimits(userID, organizationID string) error {
	if userID != "" {
		userKeys, err := akm.store.ListByUserID(userID)
		if err != nil {
			return errors.Wrap(err, errors.CodeInternal, "failed to check user key limit")
		}

		activeCount := 0
		for _, key := range userKeys {
			if key.IsActive && (key.ExpiresAt == nil || key.ExpiresAt.After(time.Now())) {
				activeCount++
			}
		}

		if activeCount >= akm.config.MaxKeysPerUser {
			return errors.New(errors.CodeQuotaExceeded, "maximum API keys per user exceeded")
		}
	}

	if organizationID != "" {
		orgKeys, err := akm.store.ListByOrganizationID(organizationID)
		if err != nil {
			return errors.Wrap(err, errors.CodeInternal, "failed to check organization key limit")
		}

		activeCount := 0
		for _, key := range orgKeys {
			if key.IsActive && (key.ExpiresAt == nil || key.ExpiresAt.After(time.Now())) {
				activeCount++
			}
		}

		if activeCount >= akm.config.MaxKeysPerOrganization {
			return errors.New(errors.CodeQuotaExceeded, "maximum API keys per organization exceeded")
		}
	}

	return nil
}

func (akm *APIKeyManager) generateAPIKey() (key, keyHash, lastFour string, err error) {
	// Generate random bytes
	bytes := make([]byte, akm.config.KeyLength)
	_, err = rand.Read(bytes)
	if err != nil {
		return "", "", "", err
	}

	// Encode to base64
	key = base64.URLEncoding.EncodeToString(bytes)

	// Add prefix
	fullKey := akm.config.Prefix + key

	// Hash the key for storage
	keyHash = akm.hashKey(key)

	// Get last four characters for display
	if len(key) >= 4 {
		lastFour = key[len(key)-4:]
	} else {
		lastFour = key
	}

	return fullKey, keyHash, lastFour, nil
}

func (akm *APIKeyManager) hashKey(key string) string {
	hash := sha256.Sum256([]byte(key))
	return base64.StdEncoding.EncodeToString(hash[:])
}

func (akm *APIKeyManager) generateID() string {
	bytes := make([]byte, 16)
	rand.Read(bytes)
	return fmt.Sprintf("ak_%x", bytes)
}

// ExtractAPIKeyFromHeader extracts API key from Authorization header
func ExtractAPIKeyFromHeader(authHeader string) (string, error) {
	if authHeader == "" {
		return "", errors.New(errors.CodeUnauthorized, "missing authorization header")
	}

	// Check for API key format
	const apiKeyPrefix = "ApiKey "
	if len(authHeader) < len(apiKeyPrefix) || authHeader[:len(apiKeyPrefix)] != apiKeyPrefix {
		return "", errors.New(errors.CodeUnauthorized, "invalid authorization header format for API key")
	}

	key := authHeader[len(apiKeyPrefix):]
	if key == "" {
		return "", errors.New(errors.CodeUnauthorized, "empty API key")
	}

	return key, nil
}

// CheckPermission checks if an API key has a specific permission
func CheckPermission(apiKey *APIKey, permission string) bool {
	if apiKey.Permissions == nil {
		return false
	}

	// Check for exact permission
	if _, exists := apiKey.Permissions[permission]; exists {
		return true
	}

	// Check for wildcard permission
	if _, exists := apiKey.Permissions["*"]; exists {
		return true
	}

	// Check for namespace permission (e.g., "buildings:*")
	parts := strings.Split(permission, ":")
	if len(parts) > 1 {
		namespace := parts[0] + ":*"
		if _, exists := apiKey.Permissions[namespace]; exists {
			return true
		}
	}

	return false
}
