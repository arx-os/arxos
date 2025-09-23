package middleware

import (
	"context"
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"net/http"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// CSRF token constants
const (
	CSRFTokenLength = 32
	CSRFCookieName  = "csrf_token"
	CSRFHeaderName  = "X-CSRF-Token"
	CSRFFormField   = "csrf_token"
	CSRFMaxAge      = 86400 // 24 hours
)

// CSRFStore stores and validates CSRF tokens
type CSRFStore interface {
	Generate(sessionID string) (string, error)
	Validate(sessionID, token string) bool
	Delete(sessionID string)
}

// MemoryCSRFStore is an in-memory CSRF token store
type MemoryCSRFStore struct {
	tokens map[string]tokenData
	mu     sync.RWMutex
}

type tokenData struct {
	token     string
	expiresAt time.Time
}

// NewMemoryCSRFStore creates a new in-memory CSRF store
func NewMemoryCSRFStore() *MemoryCSRFStore {
	store := &MemoryCSRFStore{
		tokens: make(map[string]tokenData),
	}

	// Start cleanup goroutine
	go store.cleanup()

	return store
}

// Generate creates a new CSRF token for a session
func (s *MemoryCSRFStore) Generate(sessionID string) (string, error) {
	// Generate random token
	tokenBytes := make([]byte, CSRFTokenLength)
	if _, err := rand.Read(tokenBytes); err != nil {
		return "", err
	}

	token := base64.URLEncoding.EncodeToString(tokenBytes)

	// Store token
	s.mu.Lock()
	s.tokens[sessionID] = tokenData{
		token:     token,
		expiresAt: time.Now().Add(24 * time.Hour),
	}
	s.mu.Unlock()

	return token, nil
}

// Validate checks if a CSRF token is valid for a session
func (s *MemoryCSRFStore) Validate(sessionID, token string) bool {
	s.mu.RLock()
	data, exists := s.tokens[sessionID]
	s.mu.RUnlock()

	if !exists {
		return false
	}

	// Check if expired
	if time.Now().After(data.expiresAt) {
		s.Delete(sessionID)
		return false
	}

	// Constant time comparison to prevent timing attacks
	return subtle.ConstantTimeCompare([]byte(data.token), []byte(token)) == 1
}

// Delete removes a CSRF token for a session
func (s *MemoryCSRFStore) Delete(sessionID string) {
	s.mu.Lock()
	delete(s.tokens, sessionID)
	s.mu.Unlock()
}

// cleanup periodically removes expired tokens
func (s *MemoryCSRFStore) cleanup() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()

	for range ticker.C {
		now := time.Now()
		s.mu.Lock()
		for sessionID, data := range s.tokens {
			if now.After(data.expiresAt) {
				delete(s.tokens, sessionID)
			}
		}
		s.mu.Unlock()
	}
}

// CSRFMiddleware provides CSRF protection
type CSRFMiddleware struct {
	store        CSRFStore
	secureCookie bool
	sameSite     http.SameSite
	excludePaths []string
}

// NewCSRFMiddleware creates a new CSRF middleware
func NewCSRFMiddleware(store CSRFStore) *CSRFMiddleware {
	return &CSRFMiddleware{
		store:        store,
		secureCookie: true,
		sameSite:     http.SameSiteStrictMode,
		excludePaths: []string{
			"/api/health",
			"/api/metrics",
			"/static/",
		},
	}
}

// WithOptions configures the CSRF middleware
func (m *CSRFMiddleware) WithOptions(secure bool, sameSite http.SameSite, excludePaths []string) *CSRFMiddleware {
	m.secureCookie = secure
	m.sameSite = sameSite
	m.excludePaths = excludePaths
	return m
}

// Handler returns the CSRF protection middleware handler
func (m *CSRFMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if path is excluded
		for _, path := range m.excludePaths {
			if r.URL.Path == path || (len(path) > 0 && path[len(path)-1] == '/' && len(r.URL.Path) > len(path) && r.URL.Path[:len(path)] == path) {
				next.ServeHTTP(w, r)
				return
			}
		}

		// Get session ID from cookie or create new one
		sessionID := m.getSessionID(r)
		if sessionID == "" {
			sessionID = m.generateSessionID()
			m.setSessionCookie(w, sessionID)
		}

		// For safe methods, just ensure token exists
		if r.Method == http.MethodGet || r.Method == http.MethodHead || r.Method == http.MethodOptions {
			token, _ := m.getOrGenerateToken(w, r, sessionID)
			// Add token to response context for templates
			ctx := context.WithValue(r.Context(), contextKey("csrf_token"), token)
			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		// For state-changing methods, validate token
		token := m.extractToken(r)
		if token == "" {
			logger.Warn("CSRF token missing for %s %s", r.Method, r.URL.Path)
			http.Error(w, "CSRF token missing", http.StatusForbidden)
			return
		}

		if !m.store.Validate(sessionID, token) {
			logger.Warn("Invalid CSRF token for %s %s", r.Method, r.URL.Path)
			http.Error(w, "Invalid CSRF token", http.StatusForbidden)
			return
		}

		// Token is valid, proceed with request
		next.ServeHTTP(w, r)
	})
}

// getSessionID retrieves the session ID from cookie
func (m *CSRFMiddleware) getSessionID(r *http.Request) string {
	cookie, err := r.Cookie("session_id")
	if err != nil {
		return ""
	}
	return cookie.Value
}

// generateSessionID creates a new session ID
func (m *CSRFMiddleware) generateSessionID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return base64.URLEncoding.EncodeToString(b)
}

// setSessionCookie sets the session ID cookie
func (m *CSRFMiddleware) setSessionCookie(w http.ResponseWriter, sessionID string) {
	http.SetCookie(w, &http.Cookie{
		Name:     "session_id",
		Value:    sessionID,
		Path:     "/",
		MaxAge:   CSRFMaxAge,
		HttpOnly: true,
		Secure:   m.secureCookie,
		SameSite: m.sameSite,
	})
}

// getOrGenerateToken gets existing token or generates new one
func (m *CSRFMiddleware) getOrGenerateToken(w http.ResponseWriter, r *http.Request, sessionID string) (string, error) {
	// Try to get existing token from cookie
	cookie, err := r.Cookie(CSRFCookieName)
	if err == nil && cookie.Value != "" {
		// Validate that this token exists in store
		if m.store.Validate(sessionID, cookie.Value) {
			return cookie.Value, nil
		}
	}

	// Generate new token
	token, err := m.store.Generate(sessionID)
	if err != nil {
		return "", err
	}

	// Set cookie
	http.SetCookie(w, &http.Cookie{
		Name:     CSRFCookieName,
		Value:    token,
		Path:     "/",
		MaxAge:   CSRFMaxAge,
		HttpOnly: false, // Must be readable by JavaScript
		Secure:   m.secureCookie,
		SameSite: m.sameSite,
	})

	return token, nil
}

// extractToken extracts CSRF token from request
func (m *CSRFMiddleware) extractToken(r *http.Request) string {
	// Try header first (for AJAX requests)
	token := r.Header.Get(CSRFHeaderName)
	if token != "" {
		return token
	}

	// Try form value
	token = r.FormValue(CSRFFormField)
	if token != "" {
		return token
	}

	// Try multipart form
	if r.MultipartForm != nil {
		values := r.MultipartForm.Value[CSRFFormField]
		if len(values) > 0 {
			return values[0]
		}
	}

	return ""
}

// GetCSRFToken retrieves the CSRF token from the request context
func GetCSRFToken(r *http.Request) string {
	if token, ok := r.Context().Value(contextKey("csrf_token")).(string); ok {
		return token
	}
	return ""
}

// CSRFTokenInput returns an HTML input field with the CSRF token
func CSRFTokenInput(r *http.Request) string {
	token := GetCSRFToken(r)
	if token == "" {
		return ""
	}
	return `<input type="hidden" name="csrf_token" value="` + token + `">`
}

// CSRFMetaTag returns an HTML meta tag with the CSRF token
func CSRFMetaTag(r *http.Request) string {
	token := GetCSRFToken(r)
	if token == "" {
		return ""
	}
	return `<meta name="csrf-token" content="` + token + `">`
}