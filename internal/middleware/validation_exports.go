package middleware

import (
	"encoding/json"
	"fmt"
	"html"
	"net/http"
	"regexp"
	"strings"
)

// NewValidationMiddleware creates a new validation middleware with custom options
func NewValidationMiddleware(options ...ValidationOption) func(http.Handler) http.Handler {
	config := &validationConfig{
		maxRequestSize: MaxRequestSize,
		allowedMethods: []string{"GET", "POST", "PUT", "DELETE", "PATCH"},
		requireAuth:    false,
	}

	for _, opt := range options {
		opt(config)
	}

	return func(next http.Handler) http.Handler {
		return InputValidation(next)
	}
}

// ValidationOption is a configuration option for validation middleware
type ValidationOption func(*validationConfig)

type validationConfig struct {
	maxRequestSize int64
	allowedMethods []string
	requireAuth    bool
}

// WithMaxRequestSize sets the maximum request size
func WithMaxRequestSize(size int64) ValidationOption {
	return func(c *validationConfig) {
		c.maxRequestSize = size
	}
}

// WithAllowedMethods sets the allowed HTTP methods
func WithAllowedMethods(methods []string) ValidationOption {
	return func(c *validationConfig) {
		c.allowedMethods = methods
	}
}

// ValidateID validates a generic ID string
func ValidateID(id string) error {
	if id == "" {
		return fmt.Errorf("ID cannot be empty")
	}

	// Check for common ID formats (UUID, alphanumeric with dashes)
	if len(id) < 3 || len(id) > 128 {
		return fmt.Errorf("ID must be between 3 and 128 characters")
	}

	// Allow alphanumeric, dashes, and underscores
	validID := regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)
	if !validID.MatchString(id) {
		return fmt.Errorf("ID contains invalid characters")
	}

	return nil
}

// ValidateJSON validates that a string is valid JSON
func ValidateJSON(jsonStr string) error {
	if jsonStr == "" {
		return fmt.Errorf("JSON cannot be empty")
	}

	var js interface{}
	if err := json.Unmarshal([]byte(jsonStr), &js); err != nil {
		return fmt.Errorf("invalid JSON: %w", err)
	}

	return nil
}

// SanitizeString sanitizes a string for safe storage and display
func SanitizeString(input string) string {
	// Trim whitespace
	input = strings.TrimSpace(input)

	// HTML escape to prevent XSS
	input = html.EscapeString(input)

	// Remove null bytes
	input = strings.ReplaceAll(input, "\x00", "")

	// Limit length to prevent abuse
	if len(input) > 10000 {
		input = input[:10000]
	}

	return input
}

// SanitizeID sanitizes an ID string
func SanitizeID(id string) string {
	// Remove any non-alphanumeric characters except dashes and underscores
	reg := regexp.MustCompile(`[^a-zA-Z0-9_-]`)
	return reg.ReplaceAllString(id, "")
}
