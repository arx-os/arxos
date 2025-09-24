package middleware

import (
	"fmt"
	"net/http"
	"runtime/debug"

	"github.com/arx-os/arxos/internal/common/logger"
)

// RecoveryMiddleware provides panic recovery
type RecoveryMiddleware struct {
	debug bool
}

// NewRecoveryMiddleware creates a new recovery middleware
func NewRecoveryMiddleware(debug bool) *RecoveryMiddleware {
	return &RecoveryMiddleware{
		debug: debug,
	}
}

// DefaultRecoveryMiddleware creates a recovery middleware with default settings
func DefaultRecoveryMiddleware() *RecoveryMiddleware {
	return NewRecoveryMiddleware(false) // Production mode by default
}

// Recovery middleware that recovers from panics
func (m *RecoveryMiddleware) Recovery(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				// Log the panic
				logger.Error("Panic recovered: %v\n%s", err, debug.Stack())

				// Get request ID from context
				requestID := r.Context().Value("request_id")
				if requestID == nil {
					requestID = "unknown"
				}

				// Log additional context
				logger.Error("Panic context - Method: %s, Path: %s, RequestID: %s, RemoteAddr: %s",
					r.Method, r.URL.Path, requestID, r.RemoteAddr)

				// Send error response
				m.respondInternalError(w, err, requestID)
			}
		}()

		next.ServeHTTP(w, r)
	})
}

// respondInternalError sends an internal server error response
func (m *RecoveryMiddleware) respondInternalError(w http.ResponseWriter, err interface{}, requestID interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)

	response := map[string]interface{}{
		"error":      "Internal server error",
		"code":       "internal_error",
		"request_id": requestID,
	}

	// Include error details in debug mode
	if m.debug {
		response["details"] = fmt.Sprintf("%v", err)
	}

	// Write JSON response
	fmt.Fprintf(w, `{"error":"%s","code":"%s","request_id":"%v"}`,
		response["error"], response["code"], response["request_id"])
}
