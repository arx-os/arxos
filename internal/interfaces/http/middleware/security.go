package middleware

import (
	"net/http"
	"strings"
)

// SecurityMiddleware provides security headers and protections
func SecurityMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Set security headers
			w.Header().Set("X-Content-Type-Options", "nosniff")
			w.Header().Set("X-Frame-Options", "DENY")
			w.Header().Set("X-XSS-Protection", "1; mode=block")
			w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
			w.Header().Set("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

			// Set Content Security Policy
			csp := "default-src 'self'; " +
				"script-src 'self' 'unsafe-inline'; " +
				"style-src 'self' 'unsafe-inline'; " +
				"img-src 'self' data: https:; " +
				"font-src 'self'; " +
				"connect-src 'self'; " +
				"frame-ancestors 'none';"
			w.Header().Set("Content-Security-Policy", csp)

			// Set Strict-Transport-Security for HTTPS
			if r.TLS != nil {
				w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
			}

			next.ServeHTTP(w, r)
		})
	}
}

// HTTPSRedirectMiddleware redirects HTTP to HTTPS
func HTTPSRedirectMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip redirect for health checks and localhost
			if isHealthCheck(r.URL.Path) || isLocalhost(r.Host) {
				next.ServeHTTP(w, r)
				return
			}

			// Redirect HTTP to HTTPS
			if r.Header.Get("X-Forwarded-Proto") != "https" && r.TLS == nil {
				httpsURL := "https://" + r.Host + r.RequestURI
				http.Redirect(w, r, httpsURL, http.StatusMovedPermanently)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// isHealthCheck checks if the request is a health check
func isHealthCheck(path string) bool {
	healthPaths := []string{
		"/health",
		"/api/v1/health",
		"/ping",
		"/status",
	}

	for _, healthPath := range healthPaths {
		if strings.HasPrefix(path, healthPath) {
			return true
		}
	}

	return false
}

// isLocalhost checks if the host is localhost
func isLocalhost(host string) bool {
	localhostHosts := []string{
		"localhost",
		"127.0.0.1",
		"::1",
		"0.0.0.0",
	}

	for _, localhost := range localhostHosts {
		if strings.Contains(host, localhost) {
			return true
		}
	}

	return false
}

// MethodNotAllowedMiddleware returns 405 for unsupported methods
func MethodNotAllowedMiddleware(allowedMethods []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if method is allowed
			for _, method := range allowedMethods {
				if r.Method == method {
					next.ServeHTTP(w, r)
					return
				}
			}

			// Method not allowed
			w.Header().Set("Allow", strings.Join(allowedMethods, ", "))
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		})
	}
}
