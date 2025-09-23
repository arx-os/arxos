package api

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()

	// Test CORS defaults
	if len(config.CORS.AllowedOrigins) != 1 || config.CORS.AllowedOrigins[0] != "*" {
		t.Error("Default CORS origins should be [\"*\"]")
	}

	if config.CORS.MaxAge != 3600 {
		t.Error("Default CORS max age should be 3600")
	}

	// Test rate limit defaults
	if config.RateLimit.RequestsPerMinute != 100 {
		t.Error("Default rate limit should be 100 requests per minute")
	}

	if config.RateLimit.BurstSize != 10 {
		t.Error("Default burst size should be 10")
	}
}

func TestCORSMiddleware(t *testing.T) {
	// Create a custom config with specific origins
	config := &Config{
		CORS: CORSConfig{
			AllowedOrigins: []string{"https://example.com", "https://test.com"},
			AllowedMethods: []string{"GET", "POST"},
			AllowedHeaders: []string{"Content-Type", "Authorization"},
			MaxAge:         7200,
		},
		RateLimit: DefaultConfig().RateLimit,
	}

	server := NewServerWithConfig(":8080", &Services{}, config)

	// Test allowed origin
	t.Run("allowed origin", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/test", nil)
		req.Header.Set("Origin", "https://example.com")
		w := httptest.NewRecorder()

		handler := server.corsMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		}))

		handler.ServeHTTP(w, req)

		if w.Header().Get("Access-Control-Allow-Origin") != "https://example.com" {
			t.Error("Should allow configured origin")
		}

		if w.Header().Get("Access-Control-Allow-Methods") != "GET, POST" {
			t.Error("Should set configured methods")
		}
	})

	// Test disallowed origin
	t.Run("disallowed origin", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/test", nil)
		req.Header.Set("Origin", "https://evil.com")
		w := httptest.NewRecorder()

		handler := server.corsMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		}))

		handler.ServeHTTP(w, req)

		if w.Header().Get("Access-Control-Allow-Origin") != "" {
			t.Error("Should not allow non-configured origin")
		}
	})

	// Test OPTIONS preflight
	t.Run("OPTIONS preflight", func(t *testing.T) {
		req := httptest.NewRequest("OPTIONS", "/test", nil)
		req.Header.Set("Origin", "https://example.com")
		w := httptest.NewRecorder()

		handler := server.corsMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			t.Error("Handler should not be called for OPTIONS")
		}))

		handler.ServeHTTP(w, req)

		if w.Code != http.StatusNoContent {
			t.Errorf("OPTIONS should return 204, got %d", w.Code)
		}
	})
}

func TestRateLimitMiddleware(t *testing.T) {
	config := &Config{
		CORS: DefaultConfig().CORS,
		RateLimit: RateLimitConfig{
			RequestsPerMinute: 5, // Very low for testing
			BurstSize:         2, // Small burst
			CleanupInterval:   1 * time.Second,
			ClientTTL:         5 * time.Second,
		},
	}

	server := NewServerWithConfig(":8080", &Services{}, config)

	handler := server.rateLimitMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	// Test that we can make burst requests initially
	t.Run("burst requests allowed", func(t *testing.T) {
		for i := 0; i < 2; i++ {
			req := httptest.NewRequest("GET", "/test", nil)
			req.RemoteAddr = "127.0.0.1:12345"
			w := httptest.NewRecorder()

			handler.ServeHTTP(w, req)

			if w.Code != http.StatusOK {
				t.Errorf("Request %d should be allowed, got status %d", i+1, w.Code)
			}

			// Check rate limit headers
			if w.Header().Get("X-RateLimit-Limit") != "5" {
				t.Error("Should set rate limit header")
			}
		}
	})

	// Test that additional requests are rate limited
	t.Run("rate limit exceeded", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/test", nil)
		req.RemoteAddr = "127.0.0.1:12345"
		w := httptest.NewRecorder()

		handler.ServeHTTP(w, req)

		if w.Code != http.StatusTooManyRequests {
			t.Errorf("Should be rate limited, got status %d", w.Code)
		}

		if w.Header().Get("X-RateLimit-Remaining") != "0" {
			t.Error("Should show 0 remaining requests")
		}

		if w.Header().Get("Retry-After") != "60" {
			t.Error("Should set Retry-After header")
		}
	})
}

func TestGetClientIP(t *testing.T) {
	server := NewServer(":8080", &Services{})

	tests := []struct {
		name         string
		remoteAddr   string
		forwardedFor string
		realIP       string
		expectedIP   string
	}{
		{
			name:       "direct connection",
			remoteAddr: "192.168.1.100:54321",
			expectedIP: "192.168.1.100",
		},
		{
			name:         "X-Forwarded-For single IP",
			remoteAddr:   "10.0.0.1:54321",
			forwardedFor: "203.0.113.45",
			expectedIP:   "203.0.113.45",
		},
		{
			name:         "X-Forwarded-For multiple IPs",
			remoteAddr:   "10.0.0.1:54321",
			forwardedFor: "203.0.113.45, 198.51.100.67, 10.0.0.1",
			expectedIP:   "203.0.113.45",
		},
		{
			name:       "X-Real-IP",
			remoteAddr: "10.0.0.1:54321",
			realIP:     "203.0.113.45",
			expectedIP: "203.0.113.45",
		},
		{
			name:         "X-Forwarded-For takes precedence over X-Real-IP",
			remoteAddr:   "10.0.0.1:54321",
			forwardedFor: "203.0.113.45",
			realIP:       "198.51.100.67",
			expectedIP:   "203.0.113.45",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/test", nil)
			req.RemoteAddr = tt.remoteAddr

			if tt.forwardedFor != "" {
				req.Header.Set("X-Forwarded-For", tt.forwardedFor)
			}
			if tt.realIP != "" {
				req.Header.Set("X-Real-IP", tt.realIP)
			}

			ip := server.getClientIP(req)
			if ip != tt.expectedIP {
				t.Errorf("Expected IP %s, got %s", tt.expectedIP, ip)
			}
		})
	}
}

func TestRateLimiter(t *testing.T) {
	limiter := newRateLimiter(5, 2, 1*time.Minute)

	// Should allow burst requests
	for i := 0; i < 2; i++ {
		if !limiter.allow() {
			t.Errorf("Burst request %d should be allowed", i+1)
		}
	}

	// Should reject additional requests
	if limiter.allow() {
		t.Error("Should reject request after burst exhausted")
	}

	// Check remaining count
	if remaining := limiter.remaining(); remaining != 0 {
		t.Errorf("Should have 0 remaining, got %d", remaining)
	}
}

func TestIsOriginAllowed(t *testing.T) {
	config := &Config{
		CORS: CORSConfig{
			AllowedOrigins: []string{"https://example.com", "https://test.com"},
		},
	}

	server := NewServerWithConfig(":8080", &Services{}, config)

	tests := []struct {
		origin   string
		expected bool
	}{
		{"https://example.com", true},
		{"https://test.com", true},
		{"https://evil.com", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.origin, func(t *testing.T) {
			if got := server.isOriginAllowed(tt.origin); got != tt.expected {
				t.Errorf("isOriginAllowed(%s) = %v, want %v", tt.origin, got, tt.expected)
			}
		})
	}

	// Test wildcard
	wildcardConfig := &Config{
		CORS: CORSConfig{
			AllowedOrigins: []string{"*"},
		},
	}
	wildcardServer := NewServerWithConfig(":8080", &Services{}, wildcardConfig)

	if !wildcardServer.isOriginAllowed("https://any-origin.com") {
		t.Error("Wildcard should allow any origin")
	}
}
