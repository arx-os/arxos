package middleware

import (
	"crypto/tls"
	"fmt"
	"net/http"
	"strings"
	"time"

	"go.uber.org/zap"
)

// SecurityMiddleware handles security-related middleware
type SecurityMiddleware struct {
	config SecurityConfig
	logger *zap.Logger
	audit  *AuditLogger
}

// SecurityConfig defines security configuration
type SecurityConfig struct {
	// CORS Configuration
	CORSEnabled      bool     `yaml:"cors_enabled"`
	AllowedOrigins   []string `yaml:"allowed_origins"`
	AllowedMethods   []string `yaml:"allowed_methods"`
	AllowedHeaders   []string `yaml:"allowed_headers"`
	ExposedHeaders   []string `yaml:"exposed_headers"`
	AllowCredentials bool     `yaml:"allow_credentials"`
	MaxAge           int      `yaml:"max_age"`

	// Security Headers
	SecurityHeaders SecurityHeadersConfig `yaml:"security_headers"`

	// Request Validation
	RequestValidation RequestValidationConfig `yaml:"request_validation"`

	// DDoS Protection
	DDoSProtection DDoSProtectionConfig `yaml:"ddos_protection"`

	// Trusted Proxies
	TrustedProxies []string `yaml:"trusted_proxies"`

	// TLS Configuration
	TLSConfig TLSConfig `yaml:"tls_config"`

	// Audit Logging
	AuditLogging bool `yaml:"audit_logging"`
}

// SecurityHeadersConfig defines security headers configuration
type SecurityHeadersConfig struct {
	ContentTypeOptions      string `yaml:"content_type_options"`
	FrameOptions            string `yaml:"frame_options"`
	XSSProtection           string `yaml:"xss_protection"`
	StrictTransportSecurity string `yaml:"strict_transport_security"`
	ContentSecurityPolicy   string `yaml:"content_security_policy"`
	ReferrerPolicy          string `yaml:"referrer_policy"`
	PermissionsPolicy       string `yaml:"permissions_policy"`
}

// RequestValidationConfig defines request validation configuration
type RequestValidationConfig struct {
	MaxRequestSize      int64    `yaml:"max_request_size"`
	AllowedContentTypes []string `yaml:"allowed_content_types"`
	BlockedUserAgents   []string `yaml:"blocked_user_agents"`
	BlockedIPs          []string `yaml:"blocked_ips"`
	RateLimitByIP       bool     `yaml:"rate_limit_by_ip"`
}

// DDoSProtectionConfig defines DDoS protection configuration
type DDoSProtectionConfig struct {
	Enabled          bool          `yaml:"enabled"`
	MaxRequestsPerIP int           `yaml:"max_requests_per_ip"`
	TimeWindow       time.Duration `yaml:"time_window"`
	BlockDuration    time.Duration `yaml:"block_duration"`
	WhitelistedIPs   []string      `yaml:"whitelisted_ips"`
	BlacklistedIPs   []string      `yaml:"blacklisted_ips"`
}

// TLSConfig defines TLS configuration
type TLSConfig struct {
	MinVersion       uint16        `yaml:"min_version"`
	MaxVersion       uint16        `yaml:"max_version"`
	CipherSuites     []uint16      `yaml:"cipher_suites"`
	CurvePreferences []tls.CurveID `yaml:"curve_preferences"`
}

// NewSecurityMiddleware creates a new security middleware
func NewSecurityMiddleware(config SecurityConfig) (*SecurityMiddleware, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	audit := &AuditLogger{
		logger: logger,
	}

	middleware := &SecurityMiddleware{
		config: config,
		logger: logger,
		audit:  audit,
	}

	return middleware, nil
}

// Middleware returns the security middleware function
func (sm *SecurityMiddleware) Middleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Apply security middleware in order
			if !sm.applyCORS(w, r) {
				return
			}

			if !sm.applySecurityHeaders(w, r) {
				return
			}

			if !sm.validateRequest(r) {
				return
			}

			if !sm.applyDDoSProtection(r) {
				return
			}

			// Continue to next handler
			next.ServeHTTP(w, r)

			// Log security events
			sm.logSecurityEvent(r)
		})
	}
}

// applyCORS applies CORS policies
func (sm *SecurityMiddleware) applyCORS(w http.ResponseWriter, r *http.Request) bool {
	if !sm.config.CORSEnabled {
		return true
	}

	origin := r.Header.Get("Origin")
	if origin == "" {
		return true
	}

	// Check if origin is allowed
	if !sm.isOriginAllowed(origin) {
		sm.logger.Warn("CORS blocked origin",
			zap.String("origin", origin),
			zap.String("ip", sm.getClientIP(r)),
		)
		http.Error(w, "CORS policy violation", http.StatusForbidden)
		return false
	}

	// Set CORS headers
	w.Header().Set("Access-Control-Allow-Origin", origin)
	w.Header().Set("Access-Control-Allow-Methods", strings.Join(sm.config.AllowedMethods, ", "))
	w.Header().Set("Access-Control-Allow-Headers", strings.Join(sm.config.AllowedHeaders, ", "))
	w.Header().Set("Access-Control-Expose-Headers", strings.Join(sm.config.ExposedHeaders, ", "))
	w.Header().Set("Access-Control-Max-Age", fmt.Sprintf("%d", sm.config.MaxAge))

	if sm.config.AllowCredentials {
		w.Header().Set("Access-Control-Allow-Credentials", "true")
	}

	// Handle preflight requests
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return false
	}

	return true
}

// applySecurityHeaders applies security headers
func (sm *SecurityMiddleware) applySecurityHeaders(w http.ResponseWriter, r *http.Request) bool {
	headers := sm.config.SecurityHeaders

	// Content-Type-Options
	if headers.ContentTypeOptions != "" {
		w.Header().Set("X-Content-Type-Options", headers.ContentTypeOptions)
	}

	// Frame Options
	if headers.FrameOptions != "" {
		w.Header().Set("X-Frame-Options", headers.FrameOptions)
	}

	// XSS Protection
	if headers.XSSProtection != "" {
		w.Header().Set("X-XSS-Protection", headers.XSSProtection)
	}

	// Strict Transport Security
	if headers.StrictTransportSecurity != "" {
		w.Header().Set("Strict-Transport-Security", headers.StrictTransportSecurity)
	}

	// Content Security Policy
	if headers.ContentSecurityPolicy != "" {
		w.Header().Set("Content-Security-Policy", headers.ContentSecurityPolicy)
	}

	// Referrer Policy
	if headers.ReferrerPolicy != "" {
		w.Header().Set("Referrer-Policy", headers.ReferrerPolicy)
	}

	// Permissions Policy
	if headers.PermissionsPolicy != "" {
		w.Header().Set("Permissions-Policy", headers.PermissionsPolicy)
	}

	// Additional security headers
	w.Header().Set("X-Download-Options", "noopen")
	w.Header().Set("X-Permitted-Cross-Domain-Policies", "none")

	return true
}

// validateRequest validates incoming requests
func (sm *SecurityMiddleware) validateRequest(r *http.Request) bool {
	config := sm.config.RequestValidation

	// Check request size
	if config.MaxRequestSize > 0 && r.ContentLength > config.MaxRequestSize {
		sm.logger.Warn("Request too large",
			zap.Int64("size", r.ContentLength),
			zap.Int64("max_size", config.MaxRequestSize),
			zap.String("ip", sm.getClientIP(r)),
		)
		http.Error(w, "Request too large", http.StatusRequestEntityTooLarge)
		return false
	}

	// Check content type
	if len(config.AllowedContentTypes) > 0 {
		contentType := r.Header.Get("Content-Type")
		if !sm.isContentTypeAllowed(contentType) {
			sm.logger.Warn("Content type not allowed",
				zap.String("content_type", contentType),
				zap.String("ip", sm.getClientIP(r)),
			)
			http.Error(w, "Content type not allowed", http.StatusUnsupportedMediaType)
			return false
		}
	}

	// Check user agent
	if len(config.BlockedUserAgents) > 0 {
		userAgent := r.UserAgent()
		if sm.isUserAgentBlocked(userAgent) {
			sm.logger.Warn("Blocked user agent",
				zap.String("user_agent", userAgent),
				zap.String("ip", sm.getClientIP(r)),
			)
			http.Error(w, "Access denied", http.StatusForbidden)
			return false
		}
	}

	// Check IP address
	if len(config.BlockedIPs) > 0 {
		clientIP := sm.getClientIP(r)
		if sm.isIPBlocked(clientIP) {
			sm.logger.Warn("Blocked IP address",
				zap.String("ip", clientIP),
			)
			http.Error(w, "Access denied", http.StatusForbidden)
			return false
		}
	}

	return true
}

// applyDDoSProtection applies DDoS protection
func (sm *SecurityMiddleware) applyDDoSProtection(r *http.Request) bool {
	if !sm.config.DDoSProtection.Enabled {
		return true
	}

	clientIP := sm.getClientIP(r)

	// Check whitelist
	if sm.isIPWhitelisted(clientIP) {
		return true
	}

	// Check blacklist
	if sm.isIPBlacklisted(clientIP) {
		sm.logger.Warn("Blacklisted IP attempted access",
			zap.String("ip", clientIP),
		)
		http.Error(w, "Access denied", http.StatusForbidden)
		return false
	}

	// Rate limiting by IP (simplified implementation)
	// In a real implementation, you would use Redis or similar for distributed rate limiting
	if sm.config.DDoSProtection.MaxRequestsPerIP > 0 {
		// This is a placeholder - implement proper rate limiting
		// For now, we'll just log the request
		sm.logger.Debug("DDoS protection check",
			zap.String("ip", clientIP),
			zap.Int("max_requests", sm.config.DDoSProtection.MaxRequestsPerIP),
		)
	}

	return true
}

// isOriginAllowed checks if origin is allowed
func (sm *SecurityMiddleware) isOriginAllowed(origin string) bool {
	for _, allowedOrigin := range sm.config.AllowedOrigins {
		if allowedOrigin == "*" || allowedOrigin == origin {
			return true
		}
		// Support for wildcard subdomains
		if strings.HasPrefix(allowedOrigin, "*.") {
			domain := strings.TrimPrefix(allowedOrigin, "*.")
			if strings.HasSuffix(origin, domain) {
				return true
			}
		}
	}
	return false
}

// isContentTypeAllowed checks if content type is allowed
func (sm *SecurityMiddleware) isContentTypeAllowed(contentType string) bool {
	for _, allowedType := range sm.config.RequestValidation.AllowedContentTypes {
		if strings.HasPrefix(contentType, allowedType) {
			return true
		}
	}
	return false
}

// isUserAgentBlocked checks if user agent is blocked
func (sm *SecurityMiddleware) isUserAgentBlocked(userAgent string) bool {
	for _, blockedAgent := range sm.config.RequestValidation.BlockedUserAgents {
		if strings.Contains(userAgent, blockedAgent) {
			return true
		}
	}
	return false
}

// isIPBlocked checks if IP is blocked
func (sm *SecurityMiddleware) isIPBlocked(ip string) bool {
	for _, blockedIP := range sm.config.RequestValidation.BlockedIPs {
		if ip == blockedIP {
			return true
		}
	}
	return false
}

// isIPWhitelisted checks if IP is whitelisted
func (sm *SecurityMiddleware) isIPWhitelisted(ip string) bool {
	for _, whitelistedIP := range sm.config.DDoSProtection.WhitelistedIPs {
		if ip == whitelistedIP {
			return true
		}
	}
	return false
}

// isIPBlacklisted checks if IP is blacklisted
func (sm *SecurityMiddleware) isIPBlacklisted(ip string) bool {
	for _, blacklistedIP := range sm.config.DDoSProtection.BlacklistedIPs {
		if ip == blacklistedIP {
			return true
		}
	}
	return false
}

// getClientIP gets the real client IP address
func (sm *SecurityMiddleware) getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header
	if forwardedFor := r.Header.Get("X-Forwarded-For"); forwardedFor != "" {
		ips := strings.Split(forwardedFor, ",")
		if len(ips) > 0 {
			return strings.TrimSpace(ips[0])
		}
	}

	// Check X-Real-IP header
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}

	// Check X-Client-IP header
	if clientIP := r.Header.Get("X-Client-IP"); clientIP != "" {
		return clientIP
	}

	// Fallback to remote address
	return r.RemoteAddr
}

// logSecurityEvent logs security-related events
func (sm *SecurityMiddleware) logSecurityEvent(r *http.Request) {
	if !sm.config.AuditLogging {
		return
	}

	sm.logger.Info("Security event",
		zap.String("ip", sm.getClientIP(r)),
		zap.String("method", r.Method),
		zap.String("path", r.URL.Path),
		zap.String("user_agent", r.UserAgent()),
		zap.String("origin", r.Header.Get("Origin")),
		zap.String("referer", r.Header.Get("Referer")),
	)
}

// UpdateConfig updates the security configuration
func (sm *SecurityMiddleware) UpdateConfig(config SecurityConfig) error {
	sm.config = config
	sm.logger.Info("Security configuration updated")
	return nil
}

// GetSecurityStats returns security statistics
func (sm *SecurityMiddleware) GetSecurityStats() map[string]interface{} {
	return map[string]interface{}{
		"cors_enabled":    sm.config.CORSEnabled,
		"ddos_protection": sm.config.DDoSProtection.Enabled,
		"audit_logging":   sm.config.AuditLogging,
		"allowed_origins": len(sm.config.AllowedOrigins),
		"blocked_ips":     len(sm.config.RequestValidation.BlockedIPs),
		"whitelisted_ips": len(sm.config.DDoSProtection.WhitelistedIPs),
		"blacklisted_ips": len(sm.config.DDoSProtection.BlacklistedIPs),
	}
}
