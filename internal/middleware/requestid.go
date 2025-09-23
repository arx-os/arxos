package middleware

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

const (
	// ContextKeyRequestID stores the request ID in the context
	ContextKeyRequestID contextKey = "request_id"
)

// RequestID is a chi-compatible middleware that ensures each request has an ID.
// It reads X-Request-ID if provided by client/proxy, otherwise generates one.
// The ID is set in the request context and echoed back in the X-Request-ID header.
func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = generateRequestID()
		}

		// Set on context and response header
		ctx := context.WithValue(r.Context(), ContextKeyRequestID, requestID)
		w.Header().Set("X-Request-ID", requestID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// GetRequestID returns the request ID from context if present.
func GetRequestID(ctx context.Context) string {
	if v := ctx.Value(ContextKeyRequestID); v != nil {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

func generateRequestID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}
