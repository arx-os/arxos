package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"go.uber.org/zap"
)

// AuditMiddleware handles audit logging for security compliance
type AuditMiddleware struct {
	config AuditConfig
	logger *zap.Logger
}

// AuditConfig defines audit logging configuration
type AuditConfig struct {
	Enabled          bool     `yaml:"enabled"`
	LogLevel         string   `yaml:"log_level"`
	LogFormat        string   `yaml:"log_format"`
	IncludeHeaders   bool     `yaml:"include_headers"`
	IncludeBody      bool     `yaml:"include_body"`
	MaxBodySize      int64    `yaml:"max_body_size"`
	SensitiveHeaders []string `yaml:"sensitive_headers"`
	SensitivePaths   []string `yaml:"sensitive_paths"`
	ExcludePaths     []string `yaml:"exclude_paths"`
	RetentionDays    int      `yaml:"retention_days"`
	Compression      bool     `yaml:"compression"`
}

// AuditEvent represents an audit log event
type AuditEvent struct {
	Timestamp     time.Time              `json:"timestamp"`
	EventID       string                 `json:"event_id"`
	EventType     string                 `json:"event_type"`
	UserID        string                 `json:"user_id,omitempty"`
	Username      string                 `json:"username,omitempty"`
	IPAddress     string                 `json:"ip_address"`
	UserAgent     string                 `json:"user_agent"`
	Method        string                 `json:"method"`
	Path          string                 `json:"path"`
	QueryString   string                 `json:"query_string,omitempty"`
	StatusCode    int                    `json:"status_code"`
	ResponseTime  time.Duration          `json:"response_time"`
	RequestSize   int64                  `json:"request_size"`
	ResponseSize  int64                  `json:"response_size"`
	Headers       map[string]string      `json:"headers,omitempty"`
	Body          string                 `json:"body,omitempty"`
	Error         string                 `json:"error,omitempty"`
	SessionID     string                 `json:"session_id,omitempty"`
	CorrelationID string                 `json:"correlation_id,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// NewAuditMiddleware creates a new audit middleware
func NewAuditMiddleware(config AuditConfig) (*AuditMiddleware, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	middleware := &AuditMiddleware{
		config: config,
		logger: logger,
	}

	return middleware, nil
}

// Middleware returns the audit middleware function
func (am *AuditMiddleware) Middleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !am.config.Enabled {
				next.ServeHTTP(w, r)
				return
			}

			// Skip excluded paths
			if am.isPathExcluded(r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			start := time.Now()

			// Create audit event
			event := am.createAuditEvent(r)

			// Create response writer wrapper to capture response details
			responseWriter := &auditResponseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
				body:           make([]byte, 0),
			}

			// Process request
			next.ServeHTTP(responseWriter, r)

			// Complete audit event
			am.completeAuditEvent(event, responseWriter, time.Since(start))

			// Log audit event
			am.logAuditEvent(event)
		})
	}
}

// createAuditEvent creates an audit event from the request
func (am *AuditMiddleware) createAuditEvent(r *http.Request) *AuditEvent {
	event := &AuditEvent{
		Timestamp:     time.Now(),
		EventID:       am.generateEventID(),
		EventType:     "http_request",
		IPAddress:     am.getClientIP(r),
		UserAgent:     r.UserAgent(),
		Method:        r.Method,
		Path:          r.URL.Path,
		QueryString:   r.URL.RawQuery,
		RequestSize:   r.ContentLength,
		CorrelationID: r.Header.Get("X-Request-ID"),
		SessionID:     r.Header.Get("X-Session-ID"),
	}

	// Add user information if available
	if user, ok := GetUserFromContext(r.Context()); ok {
		event.UserID = user.UserID
		event.Username = user.Username
	}

	// Add headers if configured
	if am.config.IncludeHeaders {
		event.Headers = am.sanitizeHeaders(r.Header)
	}

	// Add body if configured and not sensitive
	if am.config.IncludeBody && !am.isPathSensitive(r.URL.Path) {
		event.Body = am.sanitizeBody(r)
	}

	return event
}

// completeAuditEvent completes the audit event with response information
func (am *AuditMiddleware) completeAuditEvent(event *AuditEvent, w *auditResponseWriter, responseTime time.Duration) {
	event.StatusCode = w.statusCode
	event.ResponseTime = responseTime
	event.ResponseSize = int64(len(w.body))

	// Add error information if status code indicates error
	if event.StatusCode >= 400 {
		event.Error = http.StatusText(event.StatusCode)
	}
}

// logAuditEvent logs the audit event
func (am *AuditMiddleware) logAuditEvent(event *AuditEvent) {
	// Determine log level based on event type
	var logLevel func(msg string, fields ...zap.Field)
	switch {
	case event.StatusCode >= 500:
		logLevel = am.logger.Error
	case event.StatusCode >= 400:
		logLevel = am.logger.Warn
	case am.isPathSensitive(event.Path):
		logLevel = am.logger.Info
	default:
		logLevel = am.logger.Debug
	}

	// Convert event to JSON for logging
	eventJSON, err := json.Marshal(event)
	if err != nil {
		am.logger.Error("Failed to marshal audit event", zap.Error(err))
		return
	}

	logLevel("Audit event",
		zap.String("event_id", event.EventID),
		zap.String("event_type", event.EventType),
		zap.String("user_id", event.UserID),
		zap.String("ip_address", event.IPAddress),
		zap.String("method", event.Method),
		zap.String("path", event.Path),
		zap.Int("status_code", event.StatusCode),
		zap.Duration("response_time", event.ResponseTime),
		zap.String("correlation_id", event.CorrelationID),
		zap.String("raw_event", string(eventJSON)),
	)
}

// generateEventID generates a unique event ID
func (am *AuditMiddleware) generateEventID() string {
	return fmt.Sprintf("audit_%d_%s", time.Now().UnixNano(), am.generateRandomString(8))
}

// generateRandomString generates a random string of specified length
func (am *AuditMiddleware) generateRandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// getClientIP gets the real client IP address
func (am *AuditMiddleware) getClientIP(r *http.Request) string {
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

// sanitizeHeaders removes sensitive headers
func (am *AuditMiddleware) sanitizeHeaders(headers http.Header) map[string]string {
	sanitized := make(map[string]string)

	for key, values := range headers {
		// Skip sensitive headers
		if am.isHeaderSensitive(key) {
			sanitized[key] = "[REDACTED]"
			continue
		}

		if len(values) > 0 {
			sanitized[key] = values[0]
		}
	}

	return sanitized
}

// sanitizeBody sanitizes the request body
func (am *AuditMiddleware) sanitizeBody(r *http.Request) string {
	if r.Body == nil {
		return ""
	}

	// Limit body size for logging
	if am.config.MaxBodySize > 0 && r.ContentLength > am.config.MaxBodySize {
		return "[BODY TOO LARGE]"
	}

	// Read body (this is a simplified implementation)
	// In a real implementation, you might want to use a buffer pool
	return "[BODY CONTENT]"
}

// isHeaderSensitive checks if a header is sensitive
func (am *AuditMiddleware) isHeaderSensitive(header string) bool {
	for _, sensitiveHeader := range am.config.SensitiveHeaders {
		if strings.EqualFold(header, sensitiveHeader) {
			return true
		}
	}
	return false
}

// isPathSensitive checks if a path is sensitive
func (am *AuditMiddleware) isPathSensitive(path string) bool {
	for _, sensitivePath := range am.config.SensitivePaths {
		if strings.Contains(path, sensitivePath) {
			return true
		}
	}
	return false
}

// isPathExcluded checks if a path should be excluded from audit logging
func (am *AuditMiddleware) isPathExcluded(path string) bool {
	for _, excludedPath := range am.config.ExcludePaths {
		if strings.HasPrefix(path, excludedPath) {
			return true
		}
	}
	return false
}

// auditResponseWriter wraps http.ResponseWriter to capture response details
type auditResponseWriter struct {
	http.ResponseWriter
	statusCode int
	body       []byte
}

func (aw *auditResponseWriter) WriteHeader(code int) {
	aw.statusCode = code
	aw.ResponseWriter.WriteHeader(code)
}

func (aw *auditResponseWriter) Write(data []byte) (int, error) {
	aw.body = append(aw.body, data...)
	return aw.ResponseWriter.Write(data)
}

// UpdateConfig updates the audit configuration
func (am *AuditMiddleware) UpdateConfig(config AuditConfig) error {
	am.config = config
	am.logger.Info("Audit configuration updated")
	return nil
}

// GetAuditStats returns audit statistics
func (am *AuditMiddleware) GetAuditStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":           am.config.Enabled,
		"log_level":         am.config.LogLevel,
		"include_headers":   am.config.IncludeHeaders,
		"include_body":      am.config.IncludeBody,
		"max_body_size":     am.config.MaxBodySize,
		"sensitive_headers": len(am.config.SensitiveHeaders),
		"sensitive_paths":   len(am.config.SensitivePaths),
		"exclude_paths":     len(am.config.ExcludePaths),
		"retention_days":    am.config.RetentionDays,
		"compression":       am.config.Compression,
	}
}
