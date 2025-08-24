package middleware

import (
	"bytes"
	"encoding/json"
	"html"
	"io"
	"io/ioutil"
	"net/http"
	"reflect"
	"regexp"
	"strings"
)

var (
	// Dangerous patterns that could indicate XSS attempts
	scriptPattern     = regexp.MustCompile(`(?i)<script[^>]*>.*?</script>`)
	onEventPattern    = regexp.MustCompile(`(?i)\bon\w+\s*=`)
	javascriptPattern = regexp.MustCompile(`(?i)javascript:`)
	iframePattern     = regexp.MustCompile(`(?i)<iframe[^>]*>.*?</iframe>`)
	objectPattern     = regexp.MustCompile(`(?i)<object[^>]*>.*?</object>`)
	embedPattern      = regexp.MustCompile(`(?i)<embed[^>]*>`)
	dataURIPattern    = regexp.MustCompile(`(?i)data:[^,]*script`)
)

// SanitizationMiddleware provides input sanitization to prevent XSS attacks
func SanitizationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip sanitization for binary uploads
		if strings.Contains(r.Header.Get("Content-Type"), "multipart/form-data") {
			next.ServeHTTP(w, r)
			return
		}

		// For JSON requests, sanitize the body
		if strings.Contains(r.Header.Get("Content-Type"), "application/json") {
			body, err := ioutil.ReadAll(r.Body)
			if err != nil {
				http.Error(w, "Failed to read request body", http.StatusBadRequest)
				return
			}
			r.Body.Close()

			// Parse JSON
			var data interface{}
			if err := json.Unmarshal(body, &data); err != nil {
				http.Error(w, "Invalid JSON", http.StatusBadRequest)
				return
			}

			// Sanitize the data
			sanitized := sanitizeValue(data)

			// Re-encode the sanitized data
			sanitizedBody, err := json.Marshal(sanitized)
			if err != nil {
				http.Error(w, "Failed to process request", http.StatusInternalServerError)
				return
			}

			// Replace the request body with sanitized version
			r.Body = ioutil.NopCloser(bytes.NewBuffer(sanitizedBody))
			r.ContentLength = int64(len(sanitizedBody))
		}

		// Sanitize query parameters
		query := r.URL.Query()
		for key, values := range query {
			for i, value := range values {
				query[key][i] = sanitizeString(value)
			}
		}
		r.URL.RawQuery = query.Encode()

		// Sanitize form data
		if r.Method == "POST" || r.Method == "PUT" || r.Method == "PATCH" {
			if err := r.ParseForm(); err == nil {
				for key, values := range r.PostForm {
					for i, value := range values {
						r.PostForm[key][i] = sanitizeString(value)
					}
				}
			}
		}

		next.ServeHTTP(w, r)
	})
}

// sanitizeValue recursively sanitizes any value
func sanitizeValue(v interface{}) interface{} {
	if v == nil {
		return nil
	}

	switch val := v.(type) {
	case string:
		return sanitizeString(val)
	case []interface{}:
		sanitized := make([]interface{}, len(val))
		for i, item := range val {
			sanitized[i] = sanitizeValue(item)
		}
		return sanitized
	case map[string]interface{}:
		sanitized := make(map[string]interface{})
		for key, value := range val {
			// Sanitize both key and value
			sanitizedKey := sanitizeString(key)
			sanitized[sanitizedKey] = sanitizeValue(value)
		}
		return sanitized
	default:
		// For other types (numbers, booleans, etc.), return as-is
		return v
	}
}

// sanitizeString removes potentially dangerous content from strings
func sanitizeString(input string) string {
	// First, HTML escape the string
	sanitized := html.EscapeString(input)

	// Additional sanitization for common XSS patterns
	sanitized = scriptPattern.ReplaceAllString(sanitized, "")
	sanitized = onEventPattern.ReplaceAllString(sanitized, "")
	sanitized = javascriptPattern.ReplaceAllString(sanitized, "")
	sanitized = iframePattern.ReplaceAllString(sanitized, "")
	sanitized = objectPattern.ReplaceAllString(sanitized, "")
	sanitized = embedPattern.ReplaceAllString(sanitized, "")
	sanitized = dataURIPattern.ReplaceAllString(sanitized, "")

	// Remove null bytes
	sanitized = strings.ReplaceAll(sanitized, "\x00", "")

	// Trim excessive whitespace
	sanitized = strings.TrimSpace(sanitized)

	return sanitized
}

// ValidateInput provides strict input validation for specific field types
func ValidateInput(fieldType string, value string) bool {
	switch fieldType {
	case "email":
		emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
		return emailRegex.MatchString(value)
	case "username":
		// Allow alphanumeric, underscore, dash, 3-20 characters
		usernameRegex := regexp.MustCompile(`^[a-zA-Z0-9_-]{3,20}$`)
		return usernameRegex.MatchString(value)
	case "uuid":
		uuidRegex := regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)
		return uuidRegex.MatchString(value)
	case "alphanumeric":
		alphaRegex := regexp.MustCompile(`^[a-zA-Z0-9]+$`)
		return alphaRegex.MatchString(value)
	case "numeric":
		numRegex := regexp.MustCompile(`^[0-9]+$`)
		return numRegex.MatchString(value)
	case "arxobject_id":
		// ArxObject ID pattern from models
		idPattern := regexp.MustCompile(`^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$`)
		return idPattern.MatchString(value)
	default:
		return true
	}
}

// SanitizeJSON sanitizes a JSON string
func SanitizeJSON(jsonStr string) (string, error) {
	var data interface{}
	if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
		return "", err
	}

	sanitized := sanitizeValue(data)
	result, err := json.Marshal(sanitized)
	if err != nil {
		return "", err
	}

	return string(result), nil
}

// SanitizeHTML provides basic HTML sanitization
func SanitizeHTML(html string) string {
	// Remove script tags
	html = scriptPattern.ReplaceAllString(html, "")
	
	// Remove event handlers
	html = onEventPattern.ReplaceAllString(html, "")
	
	// Remove javascript: protocol
	html = javascriptPattern.ReplaceAllString(html, "")
	
	// Remove dangerous tags
	html = iframePattern.ReplaceAllString(html, "")
	html = objectPattern.ReplaceAllString(html, "")
	html = embedPattern.ReplaceAllString(html, "")
	
	return html
}

// ContentTypeValidationMiddleware ensures proper content-type headers
func ContentTypeValidationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// For POST/PUT/PATCH requests, validate content-type
		if r.Method == "POST" || r.Method == "PUT" || r.Method == "PATCH" {
			contentType := r.Header.Get("Content-Type")
			
			// Check if content-type is set
			if contentType == "" {
				http.Error(w, "Content-Type header is required", http.StatusBadRequest)
				return
			}
			
			// Validate content-type for JSON endpoints
			if strings.HasPrefix(r.URL.Path, "/api/") {
				if !strings.Contains(contentType, "application/json") && 
				   !strings.Contains(contentType, "multipart/form-data") {
					http.Error(w, "Invalid Content-Type. Expected application/json or multipart/form-data", http.StatusBadRequest)
					return
				}
			}
		}
		
		next.ServeHTTP(w, r)
	})
}

// ResponseSanitizationWriter wraps http.ResponseWriter to sanitize output
type ResponseSanitizationWriter struct {
	http.ResponseWriter
	sanitize bool
}

func (w *ResponseSanitizationWriter) Write(data []byte) (int, error) {
	if w.sanitize && strings.Contains(w.Header().Get("Content-Type"), "application/json") {
		// Try to sanitize JSON response
		if sanitized, err := SanitizeJSON(string(data)); err == nil {
			return w.ResponseWriter.Write([]byte(sanitized))
		}
	}
	return w.ResponseWriter.Write(data)
}

// OutputSanitizationMiddleware sanitizes response data
func OutputSanitizationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Wrap response writer to sanitize output
		sanitizedWriter := &ResponseSanitizationWriter{
			ResponseWriter: w,
			sanitize:       true,
		}
		
		next.ServeHTTP(sanitizedWriter, r)
	})
}