package middleware

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strings"
	"sync"
	"time"
)

// CSRFToken represents a CSRF token with metadata
type CSRFToken struct {
	Token     string    `json:"token"`
	ExpiresAt time.Time `json:"expires_at"`
	SessionID string    `json:"session_id"`
}

// CSRFStore manages CSRF tokens
type CSRFStore struct {
	tokens map[string]*CSRFToken
	mu     sync.RWMutex
}

// NewCSRFStore creates a new CSRF token store
func NewCSRFStore() *CSRFStore {
	store := &CSRFStore{
		tokens: make(map[string]*CSRFToken),
	}
	
	// Start cleanup goroutine
	go store.cleanup()
	
	return store
}

// cleanup removes expired tokens periodically
func (s *CSRFStore) cleanup() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()
	
	for range ticker.C {
		s.mu.Lock()
		now := time.Now()
		for key, token := range s.tokens {
			if now.After(token.ExpiresAt) {
				delete(s.tokens, key)
			}
		}
		s.mu.Unlock()
	}
}

// Generate creates a new CSRF token
func (s *CSRFStore) Generate(sessionID string) (*CSRFToken, error) {
	// Generate random token
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return nil, err
	}
	
	token := &CSRFToken{
		Token:     base64.URLEncoding.EncodeToString(b),
		ExpiresAt: time.Now().Add(4 * time.Hour), // 4 hour expiry
		SessionID: sessionID,
	}
	
	// Store token
	s.mu.Lock()
	s.tokens[token.Token] = token
	s.mu.Unlock()
	
	return token, nil
}

// Validate checks if a CSRF token is valid
func (s *CSRFStore) Validate(tokenString, sessionID string) bool {
	s.mu.RLock()
	token, exists := s.tokens[tokenString]
	s.mu.RUnlock()
	
	if !exists {
		return false
	}
	
	// Check expiration
	if time.Now().After(token.ExpiresAt) {
		// Remove expired token
		s.mu.Lock()
		delete(s.tokens, tokenString)
		s.mu.Unlock()
		return false
	}
	
	// Validate session ID matches
	return subtle.ConstantTimeCompare([]byte(token.SessionID), []byte(sessionID)) == 1
}

// Refresh generates a new token and invalidates the old one
func (s *CSRFStore) Refresh(oldToken, sessionID string) (*CSRFToken, error) {
	// Validate old token first
	if !s.Validate(oldToken, sessionID) {
		return nil, nil
	}
	
	// Remove old token
	s.mu.Lock()
	delete(s.tokens, oldToken)
	s.mu.Unlock()
	
	// Generate new token
	return s.Generate(sessionID)
}

// Global CSRF store instance
var csrfStore = NewCSRFStore()

// CSRFMiddleware provides CSRF protection for state-changing operations
func CSRFMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip CSRF for safe methods
		if r.Method == "GET" || r.Method == "HEAD" || r.Method == "OPTIONS" {
			next.ServeHTTP(w, r)
			return
		}
		
		// Skip CSRF for API endpoints that use API keys
		if r.Header.Get("X-API-Key") != "" {
			next.ServeHTTP(w, r)
			return
		}
		
		// Check if this is an HTMX request
		isHTMX := r.Header.Get("HX-Request") == "true"
		
		// Get CSRF token from appropriate source
		var csrfToken string
		if isHTMX {
			// HTMX sends token in header
			csrfToken = r.Header.Get("X-CSRF-Token")
		} else {
			// Regular forms send in body or query
			csrfToken = r.FormValue("csrf_token")
			if csrfToken == "" {
				csrfToken = r.Header.Get("X-CSRF-Token")
			}
		}
		
		// Get session ID (from cookie or context)
		sessionID := getSessionID(r)
		
		// Validate token
		if !csrfStore.Validate(csrfToken, sessionID) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusForbidden)
			json.NewEncoder(w).Encode(map[string]string{
				"error": "Invalid or missing CSRF token",
			})
			
			// Log potential CSRF attack
			logSecurityAlert(r, "CSRF token validation failed", map[string]interface{}{
				"provided_token": csrfToken != "",
				"session_id":     sessionID,
				"is_htmx":        isHTMX,
			})
			return
		}
		
		// Token is valid, proceed
		next.ServeHTTP(w, r)
	})
}

// CSRFTokenHandler handles CSRF token generation and refresh
func CSRFTokenHandler(w http.ResponseWriter, r *http.Request) {
	sessionID := getSessionID(r)
	
	switch r.Method {
	case "GET":
		// Generate new token
		token, err := csrfStore.Generate(sessionID)
		if err != nil {
			http.Error(w, "Failed to generate CSRF token", http.StatusInternalServerError)
			return
		}
		
		// Return token
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-CSRF-Token", token.Token)
		json.NewEncoder(w).Encode(map[string]string{
			"token": token.Token,
			"expires_at": token.ExpiresAt.Format(time.RFC3339),
		})
		
	case "POST":
		// Refresh token
		oldToken := r.Header.Get("X-CSRF-Token")
		if oldToken == "" {
			oldToken = r.FormValue("csrf_token")
		}
		
		token, err := csrfStore.Refresh(oldToken, sessionID)
		if err != nil || token == nil {
			http.Error(w, "Failed to refresh CSRF token", http.StatusBadRequest)
			return
		}
		
		// Return new token
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-CSRF-Token", token.Token)
		json.NewEncoder(w).Encode(map[string]string{
			"token": token.Token,
			"expires_at": token.ExpiresAt.Format(time.RFC3339),
		})
		
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// CSRFTemplateData adds CSRF token to template data
func CSRFTemplateData(r *http.Request) map[string]interface{} {
	sessionID := getSessionID(r)
	token, _ := csrfStore.Generate(sessionID)
	
	return map[string]interface{}{
		"CSRFToken": token.Token,
		"CSPNonce":  r.Context().Value("csp-nonce"),
	}
}

// getSessionID extracts session ID from request
func getSessionID(r *http.Request) string {
	// Try to get from context (set by auth middleware)
	if id := r.Context().Value("session_id"); id != nil {
		return id.(string)
	}
	
	// Try to get from cookie
	if cookie, err := r.Cookie("arxos_session"); err == nil {
		return cookie.Value
	}
	
	// Generate a temporary session ID for anonymous users
	return r.RemoteAddr
}

// HTMXSecurityMiddleware adds HTMX-specific security checks
func HTMXSecurityMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if this is an HTMX request
		if r.Header.Get("HX-Request") == "true" {
			// Verify additional security headers for HTMX
			
			// 1. Check for X-Requested-With header (defense in depth)
			if r.Header.Get("X-Requested-With") != "XMLHttpRequest" {
				w.WriteHeader(http.StatusBadRequest)
				w.Write([]byte("Invalid HTMX request"))
				return
			}
			
			// 2. Validate request timestamp to prevent replay attacks
			timestamp := r.Header.Get("X-Request-Timestamp")
			if timestamp != "" {
				reqTime, err := time.Parse(time.RFC3339, timestamp)
				if err == nil {
					// Request must be within 60 seconds
					if time.Since(reqTime).Abs() > 60*time.Second {
						w.WriteHeader(http.StatusBadRequest)
						w.Write([]byte("Request expired"))
						return
					}
				}
			}
			
			// 3. Add HTMX-specific response headers
			w.Header().Set("X-HTMX-Version", "1.9.10")
			w.Header().Set("Vary", "HX-Request")
			
			// 4. Check for HX-Trigger header for server events
			if trigger := r.Header.Get("HX-Trigger"); trigger != "" {
				// Validate trigger name to prevent injection
				if !isValidTriggerName(trigger) {
					w.WriteHeader(http.StatusBadRequest)
					w.Write([]byte("Invalid trigger name"))
					return
				}
			}
		}
		
		next.ServeHTTP(w, r)
	})
}

// isValidTriggerName validates HTMX trigger names
func isValidTriggerName(name string) bool {
	// Only allow alphanumeric, dash, underscore, and colon
	for _, char := range name {
		if !((char >= 'a' && char <= 'z') ||
			(char >= 'A' && char <= 'Z') ||
			(char >= '0' && char <= '9') ||
			char == '-' || char == '_' || char == ':') {
			return false
		}
	}
	return len(name) > 0 && len(name) < 100
}

// InputSanitizationMiddleware sanitizes user input to prevent XSS
func InputSanitizationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Parse form data if not already parsed
		if r.Form == nil {
			r.ParseForm()
		}
		
		// Sanitize all form values
		for key, values := range r.Form {
			for i, value := range values {
				// Basic HTML entity encoding for XSS prevention
				r.Form[key][i] = sanitizeInput(value)
			}
		}
		
		// Sanitize query parameters
		q := r.URL.Query()
		for key, values := range q {
			for i, value := range values {
				q[key][i] = sanitizeInput(value)
			}
		}
		r.URL.RawQuery = q.Encode()
		
		next.ServeHTTP(w, r)
	})
}

// sanitizeInput performs basic input sanitization
func sanitizeInput(input string) string {
	// This is a basic implementation. In production, use a proper HTML sanitizer
	replacements := map[string]string{
		"<":  "&lt;",
		">":  "&gt;",
		"\"": "&quot;",
		"'":  "&#39;",
		"&":  "&amp;",
	}
	
	result := input
	for old, new := range replacements {
		result = strings.ReplaceAll(result, old, new)
	}
	
	return result
}

// logSecurityAlert logs security-related events
func logSecurityAlert(r *http.Request, alertType string, details map[string]interface{}) {
	// This would log to database or security monitoring service
	// For now, just a placeholder
	go func() {
		// Log to database or monitoring service
		// Example: SecurityAlertService.Log(r, alertType, details)
	}()
}