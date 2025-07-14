package gateway

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSecurityMiddleware(t *testing.T) {
	config := SecurityConfig{
		CORSEnabled: true,
		AllowedOrigins: []string{
			"http://localhost:3000",
			"https://arxos.com",
			"https://*.arxos.com",
		},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           86400,
		SecurityHeaders: SecurityHeadersConfig{
			ContentTypeOptions:      "nosniff",
			FrameOptions:            "DENY",
			XSSProtection:           "1; mode=block",
			StrictTransportSecurity: "max-age=31536000; includeSubDomains",
			ContentSecurityPolicy:   "default-src 'self'",
			ReferrerPolicy:          "strict-origin-when-cross-origin",
			PermissionsPolicy:       "geolocation=(), microphone=(), camera=()",
		},
		RequestValidation: RequestValidationConfig{
			MaxRequestSize:      10485760, // 10MB
			AllowedContentTypes: []string{"application/json", "text/plain"},
			BlockedUserAgents:   []string{"curl", "wget"},
			BlockedIPs:          []string{"192.168.1.100"},
			RateLimitByIP:       true,
		},
		DDoSProtection: DDoSProtectionConfig{
			Enabled:          true,
			MaxRequestsPerIP: 1000,
			TimeWindow:       60 * time.Second,
			BlockDuration:    300 * time.Second,
			WhitelistedIPs:   []string{"127.0.0.1"},
			BlacklistedIPs:   []string{"192.168.1.200"},
		},
		AuditLogging: true,
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)
	assert.NotNil(t, security)
}

func TestCORSHandling(t *testing.T) {
	config := SecurityConfig{
		CORSEnabled: true,
		AllowedOrigins: []string{
			"http://localhost:3000",
			"https://arxos.com",
			"https://*.arxos.com",
		},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           86400,
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	// Test allowed origin
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()

	handler := security.Middleware()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	handler.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "http://localhost:3000", w.Header().Get("Access-Control-Allow-Origin"))
	assert.Equal(t, "GET, POST, PUT, DELETE", w.Header().Get("Access-Control-Allow-Methods"))
	assert.Equal(t, "Content-Type, Authorization", w.Header().Get("Access-Control-Allow-Headers"))
	assert.Equal(t, "true", w.Header().Get("Access-Control-Allow-Credentials"))

	// Test blocked origin
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.Header.Set("Origin", "http://malicious.com")
	w2 := httptest.NewRecorder()

	handler.ServeHTTP(w2, req2)

	assert.Equal(t, http.StatusForbidden, w2.Code)
}

func TestPreflightHandling(t *testing.T) {
	config := SecurityConfig{
		CORSEnabled: true,
		AllowedOrigins: []string{
			"http://localhost:3000",
		},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           86400,
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	// Test preflight request
	req := httptest.NewRequest("OPTIONS", "/api/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	req.Header.Set("Access-Control-Request-Method", "POST")
	req.Header.Set("Access-Control-Request-Headers", "Content-Type")
	w := httptest.NewRecorder()

	handler := security.Middleware()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	handler.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "http://localhost:3000", w.Header().Get("Access-Control-Allow-Origin"))
	assert.Equal(t, "GET, POST, PUT, DELETE", w.Header().Get("Access-Control-Allow-Methods"))
	assert.Equal(t, "Content-Type, Authorization", w.Header().Get("Access-Control-Allow-Headers"))
	assert.Equal(t, "86400", w.Header().Get("Access-Control-Max-Age"))
}

func TestSecurityHeaders(t *testing.T) {
	config := SecurityConfig{
		SecurityHeaders: SecurityHeadersConfig{
			ContentTypeOptions:      "nosniff",
			FrameOptions:            "DENY",
			XSSProtection:           "1; mode=block",
			StrictTransportSecurity: "max-age=31536000; includeSubDomains",
			ContentSecurityPolicy:   "default-src 'self'",
			ReferrerPolicy:          "strict-origin-when-cross-origin",
			PermissionsPolicy:       "geolocation=(), microphone=(), camera=()",
		},
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	req := httptest.NewRequest("GET", "/api/test", nil)
	w := httptest.NewRecorder()

	handler := security.Middleware()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	handler.ServeHTTP(w, req)

	// Check security headers
	assert.Equal(t, "nosniff", w.Header().Get("X-Content-Type-Options"))
	assert.Equal(t, "DENY", w.Header().Get("X-Frame-Options"))
	assert.Equal(t, "1; mode=block", w.Header().Get("X-XSS-Protection"))
	assert.Equal(t, "max-age=31536000; includeSubDomains", w.Header().Get("Strict-Transport-Security"))
	assert.Equal(t, "default-src 'self'", w.Header().Get("Content-Security-Policy"))
	assert.Equal(t, "strict-origin-when-cross-origin", w.Header().Get("Referrer-Policy"))
	assert.Equal(t, "geolocation=(), microphone=(), camera=()", w.Header().Get("Permissions-Policy"))
	assert.Equal(t, "noopen", w.Header().Get("X-Download-Options"))
	assert.Equal(t, "none", w.Header().Get("X-Permitted-Cross-Domain-Policies"))
}

func TestRequestValidation(t *testing.T) {
	config := SecurityConfig{
		RequestValidation: RequestValidationConfig{
			MaxRequestSize:      1024, // 1KB
			AllowedContentTypes: []string{"application/json", "text/plain"},
			BlockedUserAgents:   []string{"curl", "wget"},
			BlockedIPs:          []string{"192.168.1.100"},
			RateLimitByIP:       true,
		},
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	// Test blocked user agent
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("User-Agent", "curl/7.68.0")
	req.RemoteAddr = "127.0.0.1:12345"
	w := httptest.NewRecorder()

	handler := security.Middleware()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	handler.ServeHTTP(w, req)

	assert.Equal(t, http.StatusForbidden, w.Code)

	// Test blocked IP
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.Header.Set("User-Agent", "Mozilla/5.0")
	req2.RemoteAddr = "192.168.1.100:12345"
	w2 := httptest.NewRecorder()

	handler.ServeHTTP(w2, req2)

	assert.Equal(t, http.StatusForbidden, w2.Code)

	// Test valid request
	req3 := httptest.NewRequest("GET", "/api/test", nil)
	req3.Header.Set("User-Agent", "Mozilla/5.0")
	req3.RemoteAddr = "127.0.0.1:12345"
	w3 := httptest.NewRecorder()

	handler.ServeHTTP(w3, req3)

	assert.Equal(t, http.StatusOK, w3.Code)
}

func TestDDoSProtection(t *testing.T) {
	config := SecurityConfig{
		DDoSProtection: DDoSProtectionConfig{
			Enabled:          true,
			MaxRequestsPerIP: 10,
			TimeWindow:       60 * time.Second,
			BlockDuration:    300 * time.Second,
			WhitelistedIPs:   []string{"127.0.0.1"},
			BlacklistedIPs:   []string{"192.168.1.200"},
		},
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	// Test whitelisted IP
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.RemoteAddr = "127.0.0.1:12345"
	w := httptest.NewRecorder()

	handler := security.Middleware()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	handler.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	// Test blacklisted IP
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.RemoteAddr = "192.168.1.200:12345"
	w2 := httptest.NewRecorder()

	handler.ServeHTTP(w2, req2)

	assert.Equal(t, http.StatusForbidden, w2.Code)
}

func TestClientIPExtraction(t *testing.T) {
	config := SecurityConfig{}
	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	// Test X-Forwarded-For header
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("X-Forwarded-For", "192.168.1.1, 10.0.0.1")
	ip := security.getClientIP(req)
	assert.Equal(t, "192.168.1.1", ip)

	// Test X-Real-IP header
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.Header.Set("X-Real-IP", "192.168.1.2")
	ip2 := security.getClientIP(req2)
	assert.Equal(t, "192.168.1.2", ip2)

	// Test X-Client-IP header
	req3 := httptest.NewRequest("GET", "/api/test", nil)
	req3.Header.Set("X-Client-IP", "192.168.1.3")
	ip3 := security.getClientIP(req3)
	assert.Equal(t, "192.168.1.3", ip3)

	// Test fallback to RemoteAddr
	req4 := httptest.NewRequest("GET", "/api/test", nil)
	req4.RemoteAddr = "192.168.1.4:12345"
	ip4 := security.getClientIP(req4)
	assert.Equal(t, "192.168.1.4:12345", ip4)
}

func TestSecurityStats(t *testing.T) {
	config := SecurityConfig{
		CORSEnabled: true,
		DDoSProtection: DDoSProtectionConfig{
			Enabled: true,
		},
		RequestValidation: RequestValidationConfig{
			BlockedIPs: []string{"192.168.1.100"},
		},
		AuditLogging: true,
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)

	stats := security.GetSecurityStats()

	assert.Equal(t, true, stats["cors_enabled"])
	assert.Equal(t, true, stats["ddos_protection"])
	assert.Equal(t, true, stats["audit_logging"])
	assert.Equal(t, 1, stats["blocked_ips"])
}

func TestConfigurationValidation(t *testing.T) {
	// Test valid configuration
	config := SecurityConfig{
		CORSEnabled:    true,
		AllowedOrigins: []string{"http://localhost:3000"},
		SecurityHeaders: SecurityHeadersConfig{
			ContentTypeOptions: "nosniff",
		},
	}

	security, err := NewSecurityMiddleware(config)
	require.NoError(t, err)
	assert.NotNil(t, security)

	// Test configuration update
	newConfig := SecurityConfig{
		CORSEnabled: false,
		SecurityHeaders: SecurityHeadersConfig{
			ContentTypeOptions: "nosniff",
		},
	}

	err = security.UpdateConfig(newConfig)
	assert.NoError(t, err)
}
