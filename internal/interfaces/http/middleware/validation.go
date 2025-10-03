package middleware

import (
	"encoding/json"
	"net/http"

	"github.com/arx-os/arxos/internal/interfaces/http/validation"
)

// ValidationMiddleware provides request validation middleware
func ValidationMiddleware(validator *validation.Validator) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip validation for GET requests and health checks
			if r.Method == "GET" || isValidationHealthCheck(r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			// Validate content type for POST/PUT/PATCH requests
			if r.Method == "POST" || r.Method == "PUT" || r.Method == "PATCH" {
				contentType := r.Header.Get("Content-Type")
				if !isValidContentType(contentType) {
					http.Error(w, "Content-Type must be application/json", http.StatusBadRequest)
					return
				}
			}

			next.ServeHTTP(w, r)
		})
	}
}

// ValidateStruct validates a struct and returns validation errors
func ValidateStruct(validator *validation.Validator, target interface{}) map[string]string {
	return validator.ValidateStruct(target)
}

// ValidateQueryParams validates query parameters
func ValidateQueryParams(validator *validation.Validator, r *http.Request, rules map[string]string) map[string]string {
	return validator.ValidateQueryParams(r, rules)
}

// WriteValidationError writes a validation error response
func WriteValidationError(w http.ResponseWriter, r *http.Request, errors map[string]string) {
	errorResp := map[string]interface{}{
		"error":             "Validation Error",
		"message":           "Request validation failed",
		"code":              "VALIDATION_ERROR",
		"request_id":        r.Header.Get("X-Request-ID"),
		"validation_errors": errors,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	json.NewEncoder(w).Encode(errorResp)
}

// isValidContentType checks if the content type is valid
func isValidContentType(contentType string) bool {
	validTypes := []string{
		"application/json",
		"application/json; charset=utf-8",
		"application/json;charset=utf-8",
	}

	for _, validType := range validTypes {
		if contentType == validType {
			return true
		}
	}

	return false
}

// isValidationHealthCheck checks if the request is a health check
func isValidationHealthCheck(path string) bool {
	healthPaths := []string{
		"/health",
		"/api/v1/health",
		"/ping",
		"/status",
	}

	for _, healthPath := range healthPaths {
		if path == healthPath {
			return true
		}
	}

	return false
}

// Common validation rules for query parameters
var (
	// PaginationRules defines validation rules for pagination parameters
	PaginationRules = map[string]string{
		"limit":  "int",
		"offset": "int",
	}

	// SortRules defines validation rules for sorting parameters
	SortRules = map[string]string{
		"sort_by":    "alphanumeric",
		"sort_order": "oneof=asc desc",
	}

	// DateRangeRules defines validation rules for date range parameters
	DateRangeRules = map[string]string{
		"start_date": "date",
		"end_date":   "date",
	}

	// UUIDRules defines validation rules for UUID parameters
	UUIDRules = map[string]string{
		"id": "uuid",
	}

	// EmailRules defines validation rules for email parameters
	EmailRules = map[string]string{
		"email": "email",
	}

	// StatusRules defines validation rules for status parameters
	StatusRules = map[string]string{
		"status": "oneof=active inactive pending completed failed",
	}
)
