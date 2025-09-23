package middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestCSRFMiddleware(t *testing.T) {
	// Create CSRF middleware
	store := NewMemoryCSRFStore()
	csrfMiddleware := NewCSRFMiddleware(store)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Success"))
	})

	// Wrap with CSRF middleware
	handler := csrfMiddleware.Handler(testHandler)

	// Test GET request (should generate token)
	t.Run("GET request generates token", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		// Check that cookies were set
		cookies := rec.Result().Cookies()
		hasSessionCookie := false
		hasCSRFCookie := false

		for _, cookie := range cookies {
			if cookie.Name == "session_id" {
				hasSessionCookie = true
			}
			if cookie.Name == CSRFCookieName {
				hasCSRFCookie = true
			}
		}

		if !hasSessionCookie {
			t.Error("Session cookie not set")
		}
		if !hasCSRFCookie {
			t.Error("CSRF cookie not set")
		}

		if rec.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", rec.Code)
		}
	})

	// Test POST without token (should fail)
	t.Run("POST without token fails", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/test", nil)
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		if rec.Code != http.StatusForbidden {
			t.Errorf("Expected status 403, got %d", rec.Code)
		}
	})

	// Test POST with valid token
	t.Run("POST with valid token succeeds", func(t *testing.T) {
		// First, make a GET request to get a token
		getReq := httptest.NewRequest(http.MethodGet, "/test", nil)
		getRec := httptest.NewRecorder()
		handler.ServeHTTP(getRec, getReq)

		// Extract cookies
		cookies := getRec.Result().Cookies()
		var sessionID, csrfToken string
		for _, cookie := range cookies {
			if cookie.Name == "session_id" {
				sessionID = cookie.Value
			}
			if cookie.Name == CSRFCookieName {
				csrfToken = cookie.Value
			}
		}

		// Make POST request with token
		postReq := httptest.NewRequest(http.MethodPost, "/test", strings.NewReader("data=test"))
		postReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		postReq.Header.Set(CSRFHeaderName, csrfToken)
		postReq.AddCookie(&http.Cookie{Name: "session_id", Value: sessionID})

		postRec := httptest.NewRecorder()
		handler.ServeHTTP(postRec, postReq)

		if postRec.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", postRec.Code)
		}
	})

	// Test POST with invalid token
	t.Run("POST with invalid token fails", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/test", nil)
		req.Header.Set(CSRFHeaderName, "invalid-token")
		req.AddCookie(&http.Cookie{Name: "session_id", Value: "test-session"})

		rec := httptest.NewRecorder()
		handler.ServeHTTP(rec, req)

		if rec.Code != http.StatusForbidden {
			t.Errorf("Expected status 403, got %d", rec.Code)
		}
	})

	// Test excluded paths
	t.Run("Excluded paths bypass CSRF", func(t *testing.T) {
		// Configure middleware with excluded path
		csrfMiddleware := NewCSRFMiddleware(store).WithOptions(true, http.SameSiteStrictMode, []string{"/api/health"})
		handler := csrfMiddleware.Handler(testHandler)

		req := httptest.NewRequest(http.MethodPost, "/api/health", nil)
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("Expected status 200 for excluded path, got %d", rec.Code)
		}
	})
}

func TestCSRFStore(t *testing.T) {
	store := NewMemoryCSRFStore()

	t.Run("Generate and validate token", func(t *testing.T) {
		sessionID := "test-session-1"

		// Generate token
		token, err := store.Generate(sessionID)
		if err != nil {
			t.Fatalf("Failed to generate token: %v", err)
		}

		if token == "" {
			t.Error("Generated token is empty")
		}

		// Validate correct token
		if !store.Validate(sessionID, token) {
			t.Error("Valid token failed validation")
		}

		// Validate incorrect token
		if store.Validate(sessionID, "wrong-token") {
			t.Error("Invalid token passed validation")
		}

		// Validate token for wrong session
		if store.Validate("wrong-session", token) {
			t.Error("Token validated for wrong session")
		}
	})

	t.Run("Token expiration", func(t *testing.T) {
		sessionID := "test-session-2"

		// Generate token with short expiry
		store.mu.Lock()
		store.tokens[sessionID] = tokenData{
			token:     "test-token",
			expiresAt: time.Now().Add(-1 * time.Hour), // Already expired
		}
		store.mu.Unlock()

		// Should not validate expired token
		if store.Validate(sessionID, "test-token") {
			t.Error("Expired token passed validation")
		}

		// Token should be deleted after validation attempt
		store.mu.RLock()
		_, exists := store.tokens[sessionID]
		store.mu.RUnlock()

		if exists {
			t.Error("Expired token not deleted")
		}
	})

	t.Run("Delete token", func(t *testing.T) {
		sessionID := "test-session-3"

		// Generate token
		token, _ := store.Generate(sessionID)

		// Delete token
		store.Delete(sessionID)

		// Should not validate deleted token
		if store.Validate(sessionID, token) {
			t.Error("Deleted token passed validation")
		}
	})
}

func TestCSRFHelpers(t *testing.T) {
	t.Run("GetCSRFToken from context", func(t *testing.T) {
		token := "test-token-123"
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		ctx := context.WithValue(req.Context(), contextKey("csrf_token"), token)
		req = req.WithContext(ctx)

		retrieved := GetCSRFToken(req)
		if retrieved != token {
			t.Errorf("Expected token %s, got %s", token, retrieved)
		}
	})

	t.Run("CSRFTokenInput generates HTML", func(t *testing.T) {
		token := "test-token-456"
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		ctx := context.WithValue(req.Context(), contextKey("csrf_token"), token)
		req = req.WithContext(ctx)

		html := CSRFTokenInput(req)
		expected := `<input type="hidden" name="csrf_token" value="test-token-456">`

		if html != expected {
			t.Errorf("Expected HTML %s, got %s", expected, html)
		}
	})

	t.Run("CSRFMetaTag generates HTML", func(t *testing.T) {
		token := "test-token-789"
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		ctx := context.WithValue(req.Context(), contextKey("csrf_token"), token)
		req = req.WithContext(ctx)

		html := CSRFMetaTag(req)
		expected := `<meta name="csrf-token" content="test-token-789">`

		if html != expected {
			t.Errorf("Expected HTML %s, got %s", expected, html)
		}
	})
}

func BenchmarkCSRFValidation(b *testing.B) {
	store := NewMemoryCSRFStore()
	sessionID := "bench-session"
	token, _ := store.Generate(sessionID)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		store.Validate(sessionID, token)
	}
}

func BenchmarkCSRFGeneration(b *testing.B) {
	store := NewMemoryCSRFStore()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		store.Generate("session-" + string(rune(i)))
	}
}