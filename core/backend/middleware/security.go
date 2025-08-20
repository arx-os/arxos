package middleware

import (
	"arxos/db"
	"arxos/models"
	"context"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

// RateLimiter stores rate limit information for different clients
type RateLimiter struct {
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
	rate     rate.Limit
	burst    int
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(rps float64, burst int) *RateLimiter {
	return &RateLimiter{
		limiters: make(map[string]*rate.Limiter),
		rate:     rate.Limit(rps),
		burst:    burst,
	}
}

// GetLimiter returns a rate limiter for the given key
func (rl *RateLimiter) GetLimiter(key string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.limiters[key]
	if !exists {
		limiter = rate.NewLimiter(rl.rate, rl.burst)
		rl.limiters[key] = limiter
	}

	return limiter
}

// Cleanup removes old limiters to prevent memory leaks
func (rl *RateLimiter) Cleanup() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Remove limiters older than 1 hour
	for key, limiter := range rl.limiters {
		// Check if limiter has been inactive for more than 1 hour
		// Since rate.Limiter doesn't expose LastEvent, we'll use a simpler cleanup approach
		// Remove limiters that haven't been used recently
		if limiter.TokensAt(time.Now()) >= float64(rl.burst) {
			delete(rl.limiters, key)
		}
	}
}

// RateLimitMiddleware applies rate limiting based on client identifier
func RateLimitMiddleware(rps float64, burst int) func(http.Handler) http.Handler {
	limiter := NewRateLimiter(rps, burst)

	// Start cleanup goroutine
	go func() {
		ticker := time.NewTicker(time.Hour)
		defer ticker.Stop()
		for range ticker.C {
			limiter.Cleanup()
		}
	}()

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get client identifier (IP address or API key)
			clientID := getClientIdentifier(r)

			// Get rate limiter for this client
			clientLimiter := limiter.GetLimiter(clientID)

			// Check if request is allowed
			if !clientLimiter.Allow() {
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set("X-RateLimit-Limit", strconv.Itoa(burst))
				w.Header().Set("X-RateLimit-Remaining", "0")
				w.Header().Set("X-RateLimit-Reset", time.Now().Add(time.Second).Format(time.RFC3339))
				w.WriteHeader(http.StatusTooManyRequests)
				json.NewEncoder(w).Encode(map[string]interface{}{
					"error":       "Rate limit exceeded",
					"retry_after": time.Second,
				})
				return
			}

			// Add rate limit headers
			w.Header().Set("X-RateLimit-Limit", strconv.Itoa(burst))
			w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(clientLimiter.Burst()))
			w.Header().Set("X-RateLimit-Reset", time.Now().Add(time.Second).Format(time.RFC3339))

			next.ServeHTTP(w, r)
		})
	}
}

// getClientIdentifier returns a unique identifier for the client
func getClientIdentifier(r *http.Request) string {
	// Check for API key first
	if apiKey := r.Header.Get("X-API-Key"); apiKey != "" {
		return "api:" + apiKey
	}

	// Fall back to IP address
	ip := r.Header.Get("X-Forwarded-For")
	if ip == "" {
		ip = r.Header.Get("X-Real-IP")
	}
	if ip == "" {
		ip = r.RemoteAddr
	}

	// Extract first IP if multiple are present
	if strings.Contains(ip, ",") {
		ip = strings.TrimSpace(strings.Split(ip, ",")[0])
	}

	return "ip:" + ip
}

// APIKeyMiddleware validates API keys for data vendor access
func APIKeyMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		apiKey := r.Header.Get("X-API-Key")
		if apiKey == "" {
			http.Error(w, "Missing API key", http.StatusUnauthorized)
			return
		}

		// Validate API key
		var apiKeyRecord models.DataVendorAPIKey
		if err := db.DB.Where("key = ? AND is_active = ?", apiKey, true).First(&apiKeyRecord).Error; err != nil {
			http.Error(w, "Invalid API key", http.StatusUnauthorized)
			return
		}

		// Check if API key is expired
		if !apiKeyRecord.ExpiresAt.IsZero() && time.Now().After(apiKeyRecord.ExpiresAt) {
			http.Error(w, "API key expired", http.StatusUnauthorized)
			return
		}

		// Check rate limit for API key
		if !checkAPIKeyRateLimit(apiKeyRecord) {
			http.Error(w, "API key rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		// Add API key info to request context
		ctx := r.Context()
		ctx = context.WithValue(ctx, "api_key", apiKeyRecord)
		r = r.WithContext(ctx)

		next.ServeHTTP(w, r)
	})
}

// checkAPIKeyRateLimit checks if the API key has exceeded its rate limit
func checkAPIKeyRateLimit(apiKey models.DataVendorAPIKey) bool {
	// Count requests in the last hour
	var count int64
	oneHourAgo := time.Now().Add(-time.Hour)

	db.DB.Model(&models.DataVendorRequest{}).
		Where("api_key_id = ? AND created_at >= ?", apiKey.ID, oneHourAgo).
		Count(&count)

	return int(count) < apiKey.RateLimit
}

// DataObfuscationMiddleware applies data obfuscation for sensitive exports
func DataObfuscationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if obfuscation is requested
		obfuscate := r.URL.Query().Get("obfuscate") == "true"
		anonymize := r.URL.Query().Get("anonymize") == "true"

		if obfuscate || anonymize {
			// Wrap the response writer to intercept and obfuscate data
			obfuscatedWriter := &ObfuscatedResponseWriter{
				ResponseWriter: w,
				obfuscate:      obfuscate,
				anonymize:      anonymize,
			}
			next.ServeHTTP(obfuscatedWriter, r)
		} else {
			next.ServeHTTP(w, r)
		}
	})
}

// ObfuscatedResponseWriter wraps http.ResponseWriter to obfuscate sensitive data
type ObfuscatedResponseWriter struct {
	http.ResponseWriter
	obfuscate bool
	anonymize bool
	written   bool
}

func (w *ObfuscatedResponseWriter) Write(data []byte) (int, error) {
	if (w.obfuscate || w.anonymize) && !w.written {
		// Obfuscate the data before writing
		obfuscatedData := obfuscateData(data, w.obfuscate, w.anonymize)
		w.written = true
		return w.ResponseWriter.Write(obfuscatedData)
	}
	return w.ResponseWriter.Write(data)
}

// obfuscateData applies data obfuscation to sensitive fields
func obfuscateData(data []byte, obfuscate, anonymize bool) []byte {
	var jsonData interface{}
	if err := json.Unmarshal(data, &jsonData); err != nil {
		// If not JSON, return as-is
		return data
	}

	// Apply obfuscation recursively
	obfuscated := obfuscateJSON(jsonData, obfuscate, anonymize)

	// Convert back to JSON
	obfuscatedData, err := json.Marshal(obfuscated)
	if err != nil {
		return data
	}

	return obfuscatedData
}

// obfuscateJSON recursively obfuscates sensitive fields in JSON data
func obfuscateJSON(data interface{}, obfuscate, anonymize bool) interface{} {
	switch v := data.(type) {
	case map[string]interface{}:
		obfuscated := make(map[string]interface{})
		for key, value := range v {
			if isSensitiveField(key) && obfuscate {
				obfuscated[key] = obfuscateValue(value)
			} else if isAddressField(key) && anonymize {
				obfuscated[key] = anonymizeAddress(value)
			} else if isLocationField(key) && anonymize {
				obfuscated[key] = anonymizeLocation(value)
			} else {
				obfuscated[key] = obfuscateJSON(value, obfuscate, anonymize)
			}
		}
		return obfuscated
	case []interface{}:
		obfuscated := make([]interface{}, len(v))
		for i, value := range v {
			obfuscated[i] = obfuscateJSON(value, obfuscate, anonymize)
		}
		return obfuscated
	default:
		return data
	}
}

// isSensitiveField checks if a field name indicates sensitive data
func isSensitiveField(fieldName string) bool {
	sensitiveFields := []string{
		"email", "phone", "address", "ssn", "social_security",
		"credit_card", "account_number", "password", "secret",
		"private_key", "api_key", "token", "session_id",
		"ip_address", "user_agent", "personal_id", "license_number",
		"estimated_value", "replacement_cost", "cost", "price",
		"revenue", "salary", "income", "financial", "bank",
		"account", "routing", "tax_id", "ein", "ssn",
	}

	fieldNameLower := strings.ToLower(fieldName)
	for _, sensitive := range sensitiveFields {
		if strings.Contains(fieldNameLower, sensitive) {
			return true
		}
	}
	return false
}

// isAddressField checks if a field contains address information
func isAddressField(fieldName string) bool {
	addressFields := []string{
		"address", "street", "city", "state", "zip", "postal",
		"location", "building_address", "site_address",
		"street_address", "mailing_address", "physical_address",
	}

	fieldNameLower := strings.ToLower(fieldName)
	for _, address := range addressFields {
		if strings.Contains(fieldNameLower, address) {
			return true
		}
	}
	return false
}

// isLocationField checks if a field contains location coordinates
func isLocationField(fieldName string) bool {
	locationFields := []string{
		"latitude", "longitude", "lat", "lng", "coord",
		"x_coordinate", "y_coordinate", "position", "location",
		"gps", "geo", "coordinates",
	}

	fieldNameLower := strings.ToLower(fieldName)
	for _, location := range locationFields {
		if strings.Contains(fieldNameLower, location) {
			return true
		}
	}
	return false
}

// obfuscateValue applies obfuscation to a sensitive value
func obfuscateValue(value interface{}) interface{} {
	if str, ok := value.(string); ok {
		if len(str) > 4 {
			return str[:2] + "***" + str[len(str)-2:]
		}
		return "***"
	}
	if _, ok := value.(float64); ok {
		// Obfuscate financial values
		return "***"
	}
	if _, ok := value.(int); ok {
		// Obfuscate numeric sensitive data
		return "***"
	}
	return "***"
}

// anonymizeAddress anonymizes address information
func anonymizeAddress(value interface{}) interface{} {
	if str, ok := value.(string); ok {
		// Simple address anonymization - keep city and state, mask street
		parts := strings.Split(str, ",")
		if len(parts) >= 2 {
			// Keep city and state, mask street address
			return "***, " + strings.TrimSpace(parts[len(parts)-2]) + ", " + strings.TrimSpace(parts[len(parts)-1])
		}
		return "***"
	}
	return "***"
}

// anonymizeLocation anonymizes location coordinates
func anonymizeLocation(value interface{}) interface{} {
	if num, ok := value.(float64); ok {
		// Round to nearest 0.1 degree (roughly 11km precision)
		return math.Round(num*10) / 10
	}
	if str, ok := value.(string); ok {
		// Try to parse as float and anonymize
		if num, err := strconv.ParseFloat(str, 64); err == nil {
			return fmt.Sprintf("%.1f", math.Round(num*10)/10)
		}
	}
	return "***"
}

// Encryption utilities for secure data storage
type Encryption struct {
	key []byte
}

// NewEncryption creates a new encryption instance
func NewEncryption(key []byte) *Encryption {
	return &Encryption{key: key}
}

// Encrypt encrypts data using AES-256-GCM
func (e *Encryption) Encrypt(data []byte) (string, error) {
	block, err := aes.NewCipher(e.key)
	if err != nil {
		return "", err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := rand.Read(nonce); err != nil {
		return "", err
	}

	ciphertext := gcm.Seal(nonce, nonce, data, nil)
	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// Decrypt decrypts data using AES-256-GCM
func (e *Encryption) Decrypt(encryptedData string) ([]byte, error) {
	data, err := base64.StdEncoding.DecodeString(encryptedData)
	if err != nil {
		return nil, err
	}

	block, err := aes.NewCipher(e.key)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonceSize := gcm.NonceSize()
	if len(data) < nonceSize {
		return nil, fmt.Errorf("ciphertext too short")
	}

	nonce, ciphertext := data[:nonceSize], data[nonceSize:]
	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}

	return plaintext, nil
}

// SecurityHeadersMiddleware adds security headers to responses
func SecurityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Security headers
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
		w.Header().Set("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

		next.ServeHTTP(w, r)
	})
}

// AuditLoggingMiddleware logs security-relevant events
func AuditLoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a custom response writer to capture status code
		responseWriter := &ResponseWriter{ResponseWriter: w}

		next.ServeHTTP(responseWriter, r)

		// Log security events
		logSecurityEvent(r, responseWriter.statusCode, time.Since(start))
	})
}

// ResponseWriter wraps http.ResponseWriter to capture status code
type ResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *ResponseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// logSecurityEvent logs security-relevant events
func logSecurityEvent(r *http.Request, statusCode int, duration time.Duration) {
	// Log failed authentication attempts
	if statusCode == http.StatusUnauthorized || statusCode == http.StatusForbidden {
		logSecurityAlert(r, "Authentication failure", map[string]interface{}{
			"status_code": statusCode,
			"ip_address":  getClientIP(r),
			"user_agent":  r.UserAgent(),
			"path":        r.URL.Path,
		})
	}

	// Log rate limit violations
	if statusCode == http.StatusTooManyRequests {
		logSecurityAlert(r, "Rate limit exceeded", map[string]interface{}{
			"client_id":  getClientIdentifier(r),
			"ip_address": getClientIP(r),
			"user_agent": r.UserAgent(),
			"path":       r.URL.Path,
		})
	}

	// Log suspicious activity
	if duration > 10*time.Second {
		logSecurityAlert(r, "Slow request detected", map[string]interface{}{
			"duration":   duration,
			"ip_address": getClientIP(r),
			"path":       r.URL.Path,
		})
	}
}

// logSecurityAlert logs a security alert
func logSecurityAlert(r *http.Request, alertType string, details map[string]interface{}) {
	// In a production environment, this would send to a security monitoring system
	// For now, we'll log to the database
	detailsJSON, _ := json.Marshal(details)

	alert := models.SecurityAlert{
		AlertType: alertType,
		IPAddress: getClientIP(r),
		UserAgent: r.UserAgent(),
		Path:      r.URL.Path,
		Method:    r.Method,
		Details:   detailsJSON,
		CreatedAt: time.Now(),
	}

	db.DB.Create(&alert)
}

// getClientIP extracts the real client IP address
func getClientIP(r *http.Request) string {
	// Check for forwarded headers
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return strings.Split(ip, ",")[0]
	}
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Client-IP"); ip != "" {
		return ip
	}

	return r.RemoteAddr
}
