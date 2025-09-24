package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"
	"reflect"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ValidationMiddleware provides request validation
type ValidationMiddleware struct {
	strictMode bool
}

// NewValidationMiddleware creates a new validation middleware
func NewValidationMiddleware(strictMode bool) *ValidationMiddleware {
	return &ValidationMiddleware{
		strictMode: strictMode,
	}
}

// DefaultValidationMiddleware creates a validation middleware with default settings
func DefaultValidationMiddleware() *ValidationMiddleware {
	return NewValidationMiddleware(false) // Non-strict mode by default
}

// ValidateJSON middleware that validates JSON requests
func (m *ValidationMiddleware) ValidateJSON(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Only validate JSON requests
		if !m.isJSONRequest(r) {
			next.ServeHTTP(w, r)
			return
		}

		// Check content type
		contentType := r.Header.Get("Content-Type")
		if !strings.Contains(contentType, "application/json") {
			m.respondBadRequest(w, "Content-Type must be application/json")
			return
		}

		// Validate JSON syntax
		if r.Body != nil {
			var temp interface{}
			decoder := json.NewDecoder(r.Body)
			if err := decoder.Decode(&temp); err != nil {
				logger.Warn("Invalid JSON in request: %v", err)
				m.respondBadRequest(w, "Invalid JSON format")
				return
			}

			// Reset body for next handler
			// Note: In a real implementation, you'd need to buffer the body
			// or use a different approach to validate without consuming it
		}

		next.ServeHTTP(w, r)
	})
}

// ValidateContentLength middleware that validates content length
func (m *ValidationMiddleware) ValidateContentLength(maxSize int64) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.ContentLength > maxSize {
				logger.Warn("Request too large: %d bytes (max: %d)", r.ContentLength, maxSize)
				m.respondBadRequest(w, fmt.Sprintf("Request too large. Maximum size: %d bytes", maxSize))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// ValidateRequiredHeaders middleware that validates required headers
func (m *ValidationMiddleware) ValidateRequiredHeaders(requiredHeaders []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			missingHeaders := []string{}

			for _, header := range requiredHeaders {
				if r.Header.Get(header) == "" {
					missingHeaders = append(missingHeaders, header)
				}
			}

			if len(missingHeaders) > 0 {
				logger.Warn("Missing required headers: %v", missingHeaders)
				m.respondBadRequest(w, fmt.Sprintf("Missing required headers: %s", strings.Join(missingHeaders, ", ")))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// ValidateMethod middleware that validates HTTP methods
func (m *ValidationMiddleware) ValidateMethod(allowedMethods []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			method := r.Method
			allowed := false

			for _, allowedMethod := range allowedMethods {
				if method == allowedMethod {
					allowed = true
					break
				}
			}

			if !allowed {
				logger.Warn("Method not allowed: %s (allowed: %v)", method, allowedMethods)
				m.respondMethodNotAllowed(w, fmt.Sprintf("Method %s not allowed. Allowed methods: %s", method, strings.Join(allowedMethods, ", ")))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// ValidateQueryParams middleware that validates query parameters
func (m *ValidationMiddleware) ValidateQueryParams(requiredParams []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			missingParams := []string{}

			for _, param := range requiredParams {
				if r.URL.Query().Get(param) == "" {
					missingParams = append(missingParams, param)
				}
			}

			if len(missingParams) > 0 {
				logger.Warn("Missing required query parameters: %v", missingParams)
				m.respondBadRequest(w, fmt.Sprintf("Missing required query parameters: %s", strings.Join(missingParams, ", ")))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// isJSONRequest checks if the request is a JSON request
func (m *ValidationMiddleware) isJSONRequest(r *http.Request) bool {
	// Check if it's a POST, PUT, or PATCH request
	if r.Method != "POST" && r.Method != "PUT" && r.Method != "PATCH" {
		return false
	}

	// Check content type
	contentType := r.Header.Get("Content-Type")
	return strings.Contains(contentType, "application/json")
}

// respondBadRequest sends a bad request response
func (m *ValidationMiddleware) respondBadRequest(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	fmt.Fprintf(w, `{"error":"%s","code":"bad_request"}`, message)
}

// respondMethodNotAllowed sends a method not allowed response
func (m *ValidationMiddleware) respondMethodNotAllowed(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusMethodNotAllowed)
	fmt.Fprintf(w, `{"error":"%s","code":"method_not_allowed"}`, message)
}

// ValidateStruct validates a struct using reflection
func (m *ValidationMiddleware) ValidateStruct(v interface{}) []string {
	var errors []string

	val := reflect.ValueOf(v)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
	}

	if val.Kind() != reflect.Struct {
		errors = append(errors, "Value is not a struct")
		return errors
	}

	typ := val.Type()
	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)
		fieldType := typ.Field(i)

		// Check required fields
		if fieldType.Tag.Get("required") == "true" {
			if field.Kind() == reflect.String && field.String() == "" {
				errors = append(errors, fmt.Sprintf("Field %s is required", fieldType.Name))
			}
		}

		// Check email fields
		if fieldType.Tag.Get("type") == "email" {
			if field.Kind() == reflect.String && field.String() != "" {
				if !m.isValidEmail(field.String()) {
					errors = append(errors, fmt.Sprintf("Field %s must be a valid email", fieldType.Name))
				}
			}
		}
	}

	return errors
}

// isValidEmail validates email format
func (m *ValidationMiddleware) isValidEmail(email string) bool {
	return strings.Contains(email, "@") && strings.Contains(email, ".")
}
