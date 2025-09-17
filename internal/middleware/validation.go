package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
)

const (
	// MaxRequestSize is the maximum allowed request body size (10MB)
	MaxRequestSize = 10 * 1024 * 1024
)

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// ValidationResponse represents a validation error response
type ValidationResponse struct {
	Error   string            `json:"error"`
	Details []ValidationError `json:"details,omitempty"`
}

// Validator interface for request validation
type Validator interface {
	Validate() []ValidationError
}

// InputValidation middleware validates request input
func InputValidation(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Validate common security concerns
		if err := validateSecurityHeaders(r); err != nil {
			writeValidationError(w, []ValidationError{{Field: "headers", Message: err.Error()}})
			return
		}

		// Validate request size
		if r.ContentLength > MaxRequestSize {
			writeValidationError(w, []ValidationError{{Field: "body", Message: "request body too large"}})
			return
		}

		// Validate content type for POST/PUT/PATCH requests
		if r.Method == http.MethodPost || r.Method == http.MethodPut || r.Method == http.MethodPatch {
			contentType := r.Header.Get("Content-Type")
			if contentType == "" || !strings.Contains(contentType, "application/json") {
				writeValidationError(w, []ValidationError{{Field: "content-type", Message: "content-type must be application/json"}})
				return
			}
		}

		// Sanitize query parameters
		sanitizeQueryParams(r)

		next.ServeHTTP(w, r)
	})
}

// ValidateRequest validates a request body against a validator
func ValidateRequest(r *http.Request, v Validator) []ValidationError {
	// Decode request body
	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		return []ValidationError{{Field: "body", Message: "invalid JSON format"}}
	}

	// Validate using the validator
	return v.Validate()
}

// Common validators

// ValidateEmail validates an email address
func ValidateEmail(email string) error {
	if email == "" {
		return fmt.Errorf("email is required")
	}

	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)
	if !emailRegex.MatchString(email) {
		return fmt.Errorf("invalid email format")
	}

	if len(email) > 255 {
		return fmt.Errorf("email too long")
	}

	return nil
}

// ValidateUsername validates a username
func ValidateUsername(username string) error {
	if username == "" {
		return fmt.Errorf("username is required")
	}

	if len(username) < 3 || len(username) > 30 {
		return fmt.Errorf("username must be between 3 and 30 characters")
	}

	usernameRegex := regexp.MustCompile(`^[a-zA-Z0-9_\-]+$`)
	if !usernameRegex.MatchString(username) {
		return fmt.Errorf("username can only contain letters, numbers, underscores, and hyphens")
	}

	return nil
}

// ValidatePassword validates a password
func ValidatePassword(password string) error {
	if password == "" {
		return fmt.Errorf("password is required")
	}

	if len(password) < 8 {
		return fmt.Errorf("password must be at least 8 characters long")
	}

	if len(password) > 128 {
		return fmt.Errorf("password too long")
	}

	var hasUpper, hasLower, hasNumber bool
	for _, char := range password {
		switch {
		case 'A' <= char && char <= 'Z':
			hasUpper = true
		case 'a' <= char && char <= 'z':
			hasLower = true
		case '0' <= char && char <= '9':
			hasNumber = true
		}
	}

	if !hasUpper || !hasLower || !hasNumber {
		return fmt.Errorf("password must contain uppercase, lowercase, and numbers")
	}

	return nil
}

// ValidateArxosID validates an ArxOS ID format
func ValidateArxosID(id string) error {
	if id == "" {
		return fmt.Errorf("ArxOS ID is required")
	}

	// Format: ARXOS-NA-US-NY-NYC-0001
	arxosIDRegex := regexp.MustCompile(`^ARXOS-[A-Z]{2}-[A-Z]{2}-[A-Z]{2}-[A-Z]{3}-\d{4}$`)
	if !arxosIDRegex.MatchString(id) {
		return fmt.Errorf("invalid ArxOS ID format (expected: ARXOS-XX-XX-XX-XXX-0000)")
	}

	return nil
}

// ValidateUUID validates a UUID
func ValidateUUID(id string) error {
	if id == "" {
		return fmt.Errorf("ID is required")
	}

	uuidRegex := regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)
	if !uuidRegex.MatchString(strings.ToLower(id)) {
		return fmt.Errorf("invalid UUID format")
	}

	return nil
}

// ValidatePagination validates pagination parameters
func ValidatePagination(page, limit int) error {
	if page < 1 {
		return fmt.Errorf("page must be greater than 0")
	}

	if limit < 1 || limit > 100 {
		return fmt.Errorf("limit must be between 1 and 100")
	}

	return nil
}

// ValidateDateRange validates a date range
func ValidateDateRange(start, end string) error {
	if start == "" || end == "" {
		return fmt.Errorf("both start and end dates are required")
	}

	// Simple ISO 8601 date validation
	dateRegex := regexp.MustCompile(`^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$`)

	if !dateRegex.MatchString(start) {
		return fmt.Errorf("invalid start date format (use ISO 8601)")
	}

	if !dateRegex.MatchString(end) {
		return fmt.Errorf("invalid end date format (use ISO 8601)")
	}

	// TODO: Add actual date comparison
	return nil
}

// Helper functions

// validateSecurityHeaders checks for common security issues in headers
func validateSecurityHeaders(r *http.Request) error {
	// Check for SQL injection attempts in headers
	headers := []string{"User-Agent", "Referer", "X-Forwarded-For"}
	sqlPatterns := []string{
		"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|eval)",
		"(?i)(--|#|/\\*|\\*/)",
		"(?i)(char|nchar|varchar|nvarchar|alter|begin|cast|cursor|declare|exec|execute|fetch|kill|open|sys|table)",
	}

	for _, header := range headers {
		value := r.Header.Get(header)
		if value == "" {
			continue
		}

		for _, pattern := range sqlPatterns {
			if matched, _ := regexp.MatchString(pattern, value); matched {
				logger.Warn("Potential SQL injection in header %s: %s", header, value)
				return fmt.Errorf("invalid characters in header")
			}
		}

		// Check header length
		if len(value) > 1024 {
			return fmt.Errorf("header value too long")
		}
	}

	return nil
}

// sanitizeQueryParams sanitizes query parameters
func sanitizeQueryParams(r *http.Request) {
	query := r.URL.Query()

	// List of parameters that should be sanitized
	for key, values := range query {
		for i, value := range values {
			// Remove null bytes
			value = strings.ReplaceAll(value, "\x00", "")

			// Trim whitespace
			value = strings.TrimSpace(value)

			// Limit length
			if len(value) > 256 {
				value = value[:256]
			}

			values[i] = value
		}
		query[key] = values
	}

	r.URL.RawQuery = query.Encode()
}

// writeValidationError writes a validation error response
func writeValidationError(w http.ResponseWriter, errors []ValidationError) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)

	response := ValidationResponse{
		Error:   "Validation failed",
		Details: errors,
	}

	json.NewEncoder(w).Encode(response)
}

// Request validators for specific endpoints

// CreateBuildingRequest validates a create building request
type CreateBuildingRequest struct {
	ArxosID    string  `json:"arxos_id"`
	Name       string  `json:"name"`
	Address    string  `json:"address"`
	City       string  `json:"city"`
	State      string  `json:"state"`
	Country    string  `json:"country"`
	PostalCode string  `json:"postal_code"`
	Latitude   float64 `json:"latitude"`
	Longitude  float64 `json:"longitude"`
}

func (r CreateBuildingRequest) Validate() []ValidationError {
	var errors []ValidationError

	if err := ValidateArxosID(r.ArxosID); err != nil {
		errors = append(errors, ValidationError{Field: "arxos_id", Message: err.Error()})
	}

	if r.Name == "" {
		errors = append(errors, ValidationError{Field: "name", Message: "name is required"})
	} else if len(r.Name) > 255 {
		errors = append(errors, ValidationError{Field: "name", Message: "name too long"})
	}

	if r.Address == "" {
		errors = append(errors, ValidationError{Field: "address", Message: "address is required"})
	}

	if r.City == "" {
		errors = append(errors, ValidationError{Field: "city", Message: "city is required"})
	}

	if r.Country == "" {
		errors = append(errors, ValidationError{Field: "country", Message: "country is required"})
	}

	if r.Latitude < -90 || r.Latitude > 90 {
		errors = append(errors, ValidationError{Field: "latitude", Message: "latitude must be between -90 and 90"})
	}

	if r.Longitude < -180 || r.Longitude > 180 {
		errors = append(errors, ValidationError{Field: "longitude", Message: "longitude must be between -180 and 180"})
	}

	return errors
}

// CreateUserRequest validates a create user request
type CreateUserRequest struct {
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
	FullName string `json:"full_name"`
	Role     string `json:"role"`
}

func (r CreateUserRequest) Validate() []ValidationError {
	var errors []ValidationError

	if err := ValidateEmail(r.Email); err != nil {
		errors = append(errors, ValidationError{Field: "email", Message: err.Error()})
	}

	if err := ValidateUsername(r.Username); err != nil {
		errors = append(errors, ValidationError{Field: "username", Message: err.Error()})
	}

	if err := ValidatePassword(r.Password); err != nil {
		errors = append(errors, ValidationError{Field: "password", Message: err.Error()})
	}

	if r.FullName != "" && len(r.FullName) > 255 {
		errors = append(errors, ValidationError{Field: "full_name", Message: "full name too long"})
	}

	validRoles := map[string]bool{"admin": true, "user": true, "viewer": true}
	if r.Role != "" && !validRoles[r.Role] {
		errors = append(errors, ValidationError{Field: "role", Message: "invalid role"})
	}

	return errors
}

// LoginRequest validates a login request
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func (r LoginRequest) Validate() []ValidationError {
	var errors []ValidationError

	if r.Username == "" {
		errors = append(errors, ValidationError{Field: "username", Message: "username is required"})
	}

	if r.Password == "" {
		errors = append(errors, ValidationError{Field: "password", Message: "password is required"})
	}

	// Don't validate format for login, just presence
	return errors
}