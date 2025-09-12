package middleware

import (
	"encoding/json"
	"net/http"
	"regexp"
	"strings"
	"unicode/utf8"
)

// ValidationMiddleware provides input validation and sanitization
type ValidationMiddleware struct {
	maxBodySize    int64
	maxHeaderSize  int
	allowedMethods []string
}

// NewValidationMiddleware creates a new validation middleware
func NewValidationMiddleware() *ValidationMiddleware {
	return &ValidationMiddleware{
		maxBodySize:   10 * 1024 * 1024, // 10MB default
		maxHeaderSize: 8192,              // 8KB headers
		allowedMethods: []string{
			http.MethodGet, http.MethodPost, http.MethodPut,
			http.MethodPatch, http.MethodDelete, http.MethodOptions,
		},
	}
}

// Middleware returns the validation middleware handler
func (v *ValidationMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Validate HTTP method
		if !v.isMethodAllowed(r.Method) {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		// Validate request size
		if r.ContentLength > v.maxBodySize {
			http.Error(w, "Request body too large", http.StatusRequestEntityTooLarge)
			return
		}

		// Limit request body size
		r.Body = http.MaxBytesReader(w, r.Body, v.maxBodySize)

		// Validate headers
		if !v.validateHeaders(r) {
			http.Error(w, "Invalid headers", http.StatusBadRequest)
			return
		}

		// Validate URL path
		if !v.validatePath(r.URL.Path) {
			http.Error(w, "Invalid path", http.StatusBadRequest)
			return
		}

		// Validate query parameters
		if !v.validateQueryParams(r) {
			http.Error(w, "Invalid query parameters", http.StatusBadRequest)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// isMethodAllowed checks if the HTTP method is allowed
func (v *ValidationMiddleware) isMethodAllowed(method string) bool {
	for _, allowed := range v.allowedMethods {
		if method == allowed {
			return true
		}
	}
	return false
}

// validateHeaders validates request headers
func (v *ValidationMiddleware) validateHeaders(r *http.Request) bool {
	totalSize := 0
	for name, values := range r.Header {
		// Check header name
		if !isValidHeaderName(name) {
			return false
		}

		// Check header values
		for _, value := range values {
			if !utf8.ValidString(value) {
				return false
			}
			totalSize += len(name) + len(value)
			if totalSize > v.maxHeaderSize {
				return false
			}

			// Check for null bytes
			if strings.Contains(value, "\x00") {
				return false
			}
		}
	}
	return true
}

// validatePath validates the URL path
func (v *ValidationMiddleware) validatePath(path string) bool {
	// Check for null bytes
	if strings.Contains(path, "\x00") {
		return false
	}

	// Check for path traversal attempts
	if strings.Contains(path, "..") {
		return false
	}

	// Validate UTF-8
	if !utf8.ValidString(path) {
		return false
	}

	return true
}

// validateQueryParams validates query parameters
func (v *ValidationMiddleware) validateQueryParams(r *http.Request) bool {
	for key, values := range r.URL.Query() {
		// Validate parameter name
		if !isValidParamName(key) {
			return false
		}

		// Validate parameter values
		for _, value := range values {
			if !utf8.ValidString(value) {
				return false
			}
			// Check for null bytes
			if strings.Contains(value, "\x00") {
				return false
			}
			// Limit individual parameter value length
			if len(value) > 2048 {
				return false
			}
		}
	}
	return true
}

// isValidHeaderName checks if a header name is valid
func isValidHeaderName(name string) bool {
	// RFC 7230: field-name = token
	// token = 1*tchar
	// tchar = "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "." /
	//         "0-9" / "A-Z" / "^" / "_" / "`" / "a-z" / "|" / "~"
	validHeader := regexp.MustCompile(`^[!#$%&'*+\-.0-9A-Z^_` + "`" + `a-z|~]+$`)
	return validHeader.MatchString(name)
}

// isValidParamName checks if a parameter name is valid
func isValidParamName(name string) bool {
	// Allow alphanumeric, underscore, hyphen
	validParam := regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)
	return validParam.MatchString(name) && len(name) <= 100
}

// ValidateJSON validates and sanitizes JSON input
func ValidateJSON(data []byte, v interface{}) error {
	// Check for valid UTF-8
	if !utf8.Valid(data) {
		return &ValidationError{Message: "Invalid UTF-8 in JSON"}
	}

	// Decode JSON with strict validation
	decoder := json.NewDecoder(strings.NewReader(string(data)))
	decoder.DisallowUnknownFields()
	
	if err := decoder.Decode(v); err != nil {
		return &ValidationError{Message: "Invalid JSON", Err: err}
	}

	return nil
}

// ValidationError represents a validation error
type ValidationError struct {
	Message string
	Field   string
	Err     error
}

func (e *ValidationError) Error() string {
	if e.Field != "" {
		return e.Message + ": " + e.Field
	}
	if e.Err != nil {
		return e.Message + ": " + e.Err.Error()
	}
	return e.Message
}

// Email validation regex
var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)

// ValidateEmail validates an email address
func ValidateEmail(email string) bool {
	if len(email) > 254 { // RFC 5321
		return false
	}
	return emailRegex.MatchString(email)
}

// ValidatePassword validates password strength
func ValidatePassword(password string) error {
	if len(password) < 8 {
		return &ValidationError{Message: "Password must be at least 8 characters"}
	}
	if len(password) > 128 {
		return &ValidationError{Message: "Password too long"}
	}
	
	var (
		hasUpper  bool
		hasLower  bool
		hasNumber bool
	)
	
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
		return &ValidationError{Message: "Password must contain uppercase, lowercase, and numbers"}
	}
	
	return nil
}

// SanitizeString removes potentially dangerous characters
func SanitizeString(input string) string {
	// Remove null bytes
	input = strings.ReplaceAll(input, "\x00", "")
	
	// Trim whitespace
	input = strings.TrimSpace(input)
	
	// Ensure valid UTF-8
	if !utf8.ValidString(input) {
		return ""
	}
	
	return input
}

// ValidateID validates an ID (UUID or similar)
func ValidateID(id string) bool {
	// Allow UUIDs and alphanumeric IDs
	validID := regexp.MustCompile(`^[a-zA-Z0-9-_]{1,128}$`)
	return validID.MatchString(id)
}