package middleware

import (
	"fmt"
	"net/http"
	"runtime/debug"

	"github.com/arx-os/arxos/internal/common/logger"
)

// RecoveryMiddleware provides panic recovery following Clean Architecture principles
type RecoveryMiddleware struct {
	logger logger.Logger
}

// NewRecoveryMiddleware creates a new recovery middleware with dependency injection
func NewRecoveryMiddleware(logger logger.Logger) *RecoveryMiddleware {
	return &RecoveryMiddleware{
		logger: logger,
	}
}

// Handler returns the recovery middleware handler
func (r *RecoveryMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				// Log the panic
				r.logger.Error("Panic recovered",
					"error", err,
					"stack", string(debug.Stack()),
					"method", req.Method,
					"path", req.URL.Path,
					"remote_addr", req.RemoteAddr,
				)

				// Write error response
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprintf(w, `{"error":{"message":"Internal server error","code":"INTERNAL_ERROR"}}`)
			}
		}()

		next.ServeHTTP(w, req)
	})
}
