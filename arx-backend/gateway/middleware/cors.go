package middleware

import (
	"net/http"
	"strings"

	"go.uber.org/zap"
)

// CORSMiddleware handles Cross-Origin Resource Sharing
type CORSMiddleware struct {
	config CORSConfig
	logger *zap.Logger
}

// CORSConfig defines CORS configuration
type CORSConfig struct {
	Enabled          bool     `yaml:"enabled"`
	AllowedOrigins   []string `yaml:"allowed_origins"`
	AllowedMethods   []string `yaml:"allowed_methods"`
	AllowedHeaders   []string `yaml:"allowed_headers"`
	ExposedHeaders   []string `yaml:"exposed_headers"`
	AllowCredentials bool     `yaml:"allow_credentials"`
	MaxAge           int      `yaml:"max_age"`
	AllowWildcard    bool     `yaml:"allow_wildcard"`
}

// NewCORSMiddleware creates a new CORS middleware
func NewCORSMiddleware(config CORSConfig) (*CORSMiddleware, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, err
	}

	middleware := &CORSMiddleware{
		config: config,
		logger: logger,
	}

	return middleware, nil
}

// Middleware returns the CORS middleware function
func (cm *CORSMiddleware) Middleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Handle preflight requests
			if r.Method == "OPTIONS" {
				cm.handlePreflight(w, r)
				return
			}

			// Handle actual requests
			cm.handleCORS(w, r)
			next.ServeHTTP(w, r)
		})
	}
}

// handlePreflight handles preflight OPTIONS requests
func (cm *CORSMiddleware) handlePreflight(w http.ResponseWriter, r *http.Request) {
	origin := r.Header.Get("Origin")
	if origin == "" {
		http.Error(w, "Origin header required", http.StatusBadRequest)
		return
	}

	// Check if origin is allowed
	if !cm.isOriginAllowed(origin) {
		cm.logger.Warn("CORS preflight blocked origin",
			zap.String("origin", origin),
			zap.String("ip", cm.getClientIP(r)),
		)
		http.Error(w, "CORS policy violation", http.StatusForbidden)
		return
	}

	// Set CORS headers for preflight response
	cm.setCORSHeaders(w, origin)

	// Set preflight-specific headers
	requestMethod := r.Header.Get("Access-Control-Request-Method")
	if requestMethod != "" {
		w.Header().Set("Access-Control-Allow-Methods", strings.Join(cm.config.AllowedMethods, ", "))
	}

	requestHeaders := r.Header.Get("Access-Control-Request-Headers")
	if requestHeaders != "" {
		w.Header().Set("Access-Control-Allow-Headers", strings.Join(cm.config.AllowedHeaders, ", "))
	}

	// Set max age for preflight caching
	if cm.config.MaxAge > 0 {
		w.Header().Set("Access-Control-Max-Age", string(cm.config.MaxAge))
	}

	w.WriteHeader(http.StatusOK)
}

// handleCORS handles CORS for actual requests
func (cm *CORSMiddleware) handleCORS(w http.ResponseWriter, r *http.Request) {
	origin := r.Header.Get("Origin")
	if origin == "" {
		return
	}

	// Check if origin is allowed
	if !cm.isOriginAllowed(origin) {
		cm.logger.Warn("CORS blocked origin",
			zap.String("origin", origin),
			zap.String("ip", cm.getClientIP(r)),
		)
		http.Error(w, "CORS policy violation", http.StatusForbidden)
		return
	}

	// Set CORS headers
	cm.setCORSHeaders(w, origin)
}

// setCORSHeaders sets CORS headers on the response
func (cm *CORSMiddleware) setCORSHeaders(w http.ResponseWriter, origin string) {
	// Set Access-Control-Allow-Origin
	if cm.config.AllowWildcard && cm.isWildcardAllowed() {
		w.Header().Set("Access-Control-Allow-Origin", "*")
	} else {
		w.Header().Set("Access-Control-Allow-Origin", origin)
	}

	// Set Access-Control-Allow-Credentials
	if cm.config.AllowCredentials {
		w.Header().Set("Access-Control-Allow-Credentials", "true")
	}

	// Set Access-Control-Expose-Headers
	if len(cm.config.ExposedHeaders) > 0 {
		w.Header().Set("Access-Control-Expose-Headers", strings.Join(cm.config.ExposedHeaders, ", "))
	}
}

// isOriginAllowed checks if origin is allowed
func (cm *CORSMiddleware) isOriginAllowed(origin string) bool {
	for _, allowedOrigin := range cm.config.AllowedOrigins {
		if allowedOrigin == "*" {
			return true
		}
		if allowedOrigin == origin {
			return true
		}
		// Support for wildcard subdomains
		if strings.HasPrefix(allowedOrigin, "*.") {
			domain := strings.TrimPrefix(allowedOrigin, "*.")
			if strings.HasSuffix(origin, domain) {
				return true
			}
		}
		// Support for protocol wildcards
		if strings.HasPrefix(allowedOrigin, "https://*.") {
			domain := strings.TrimPrefix(allowedOrigin, "https://*.")
			if strings.HasPrefix(origin, "https://") && strings.HasSuffix(origin, domain) {
				return true
			}
		}
		if strings.HasPrefix(allowedOrigin, "http://*.") {
			domain := strings.TrimPrefix(allowedOrigin, "http://*.")
			if strings.HasPrefix(origin, "http://") && strings.HasSuffix(origin, domain) {
				return true
			}
		}
	}
	return false
}

// isWildcardAllowed checks if wildcard origin is allowed
func (cm *CORSMiddleware) isWildcardAllowed() bool {
	for _, allowedOrigin := range cm.config.AllowedOrigins {
		if allowedOrigin == "*" {
			return true
		}
	}
	return false
}

// getClientIP gets the real client IP address
func (cm *CORSMiddleware) getClientIP(r *http.Request) string {
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

// UpdateConfig updates the CORS configuration
func (cm *CORSMiddleware) UpdateConfig(config CORSConfig) error {
	cm.config = config
	cm.logger.Info("CORS configuration updated")
	return nil
}

// GetCORSStats returns CORS statistics
func (cm *CORSMiddleware) GetCORSStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":           cm.config.Enabled,
		"allowed_origins":   len(cm.config.AllowedOrigins),
		"allowed_methods":   len(cm.config.AllowedMethods),
		"allowed_headers":   len(cm.config.AllowedHeaders),
		"exposed_headers":   len(cm.config.ExposedHeaders),
		"allow_credentials": cm.config.AllowCredentials,
		"max_age":           cm.config.MaxAge,
		"allow_wildcard":    cm.config.AllowWildcard,
	}
}
