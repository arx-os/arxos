package telemetry

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// StructuredLogger provides structured logging with correlation IDs
type StructuredLogger struct {
	config *ObservabilityConfig
	mu     sync.RWMutex
}

// LogEntry represents a structured log entry
type LogEntry struct {
	Timestamp     time.Time              `json:"timestamp"`
	Level         string                 `json:"level"`
	Message       string                 `json:"message"`
	CorrelationID string                 `json:"correlation_id,omitempty"`
	TraceID       string                 `json:"trace_id,omitempty"`
	SpanID        string                 `json:"span_id,omitempty"`
	Service       string                 `json:"service"`
	Fields        map[string]interface{} `json:"fields,omitempty"`
}

// CorrelationIDKey is the context key for correlation IDs
const CorrelationIDKey ContextKey = "correlation_id"

// NewStructuredLogger creates a new structured logger
func NewStructuredLogger(config *ObservabilityConfig) *StructuredLogger {
	return &StructuredLogger{
		config: config,
	}
}

// LogWithContext logs a message with context information
func (sl *StructuredLogger) LogWithContext(ctx context.Context, level, format string, args ...interface{}) {
	entry := LogEntry{
		Timestamp: time.Now(),
		Level:     level,
		Message:   fmt.Sprintf(format, args...),
		Service:   sl.config.ServiceName,
	}

	// Extract correlation ID from context
	if correlationID := GetCorrelationID(ctx); correlationID != "" {
		entry.CorrelationID = correlationID
	}

	// Extract tracing information from context
	if traceID := TraceIDFromContext(ctx); traceID != "" {
		entry.TraceID = traceID
	}

	if span := SpanFromContext(ctx); span != nil {
		entry.SpanID = span.SpanID
	}

	sl.writeEntry(entry)
}

// LogWithFields logs a message with additional fields
func (sl *StructuredLogger) LogWithFields(ctx context.Context, level, message string, fields map[string]interface{}) {
	entry := LogEntry{
		Timestamp: time.Now(),
		Level:     level,
		Message:   message,
		Service:   sl.config.ServiceName,
		Fields:    fields,
	}

	// Extract correlation ID from context
	if correlationID := GetCorrelationID(ctx); correlationID != "" {
		entry.CorrelationID = correlationID
	}

	// Extract tracing information from context
	if traceID := TraceIDFromContext(ctx); traceID != "" {
		entry.TraceID = traceID
	}

	if span := SpanFromContext(ctx); span != nil {
		entry.SpanID = span.SpanID
	}

	sl.writeEntry(entry)
}

// writeEntry writes a log entry
func (sl *StructuredLogger) writeEntry(entry LogEntry) {
	if sl.config.Logging.Format == "json" {
		data, err := json.Marshal(entry)
		if err != nil {
			logger.Error("Failed to marshal log entry: %v", err)
			return
		}
		fmt.Fprintln(os.Stderr, string(data))
	} else {
		// Text format
		correlationPart := ""
		if entry.CorrelationID != "" {
			correlationPart = fmt.Sprintf(" [%s]", entry.CorrelationID)
		}

		tracePart := ""
		if entry.TraceID != "" {
			tracePart = fmt.Sprintf(" trace=%s", entry.TraceID)
			if entry.SpanID != "" {
				tracePart += fmt.Sprintf(" span=%s", entry.SpanID)
			}
		}

		fmt.Fprintf(os.Stderr, "%s [%s]%s %s%s\n",
			entry.Timestamp.Format(time.RFC3339),
			entry.Level,
			correlationPart,
			entry.Message,
			tracePart,
		)
	}
}

// AddCorrelationID adds a correlation ID to the context
func AddCorrelationID(ctx context.Context) context.Context {
	correlationID := generateCorrelationID()
	return context.WithValue(ctx, CorrelationIDKey, correlationID)
}

// GetCorrelationID gets the correlation ID from context
func GetCorrelationID(ctx context.Context) string {
	if correlationID, ok := ctx.Value(CorrelationIDKey).(string); ok {
		return correlationID
	}
	return ""
}

// WithCorrelationID adds a specific correlation ID to the context
func WithCorrelationID(ctx context.Context, correlationID string) context.Context {
	return context.WithValue(ctx, CorrelationIDKey, correlationID)
}

// generateCorrelationID generates a unique correlation ID
func generateCorrelationID() string {
	return fmt.Sprintf("req_%d_%d", time.Now().UnixNano(), time.Now().UnixNano()%10000)
}

// Helper functions for structured logging

// DebugWithContext logs a debug message with context
func DebugWithContext(ctx context.Context, format string, args ...interface{}) {
	if extendedInstance != nil && extendedInstance.logger != nil {
		extendedInstance.logger.LogWithContext(ctx, "debug", format, args...)
	} else {
		logger.Debug(format, args...)
	}
}

// InfoWithContext logs an info message with context
func InfoWithContext(ctx context.Context, format string, args ...interface{}) {
	if extendedInstance != nil && extendedInstance.logger != nil {
		extendedInstance.logger.LogWithContext(ctx, "info", format, args...)
	} else {
		logger.Info(format, args...)
	}
}

// WarnWithContext logs a warning message with context
func WarnWithContext(ctx context.Context, format string, args ...interface{}) {
	if extendedInstance != nil && extendedInstance.logger != nil {
		extendedInstance.logger.LogWithContext(ctx, "warn", format, args...)
	} else {
		logger.Warn(format, args...)
	}
}

// ErrorWithContext logs an error message with context
func ErrorWithContext(ctx context.Context, format string, args ...interface{}) {
	if extendedInstance != nil && extendedInstance.logger != nil {
		extendedInstance.logger.LogWithContext(ctx, "error", format, args...)
	} else {
		logger.Error(format, args...)
	}
}

// InfoWithFields logs an info message with additional fields
func InfoWithFields(ctx context.Context, message string, fields map[string]interface{}) {
	if extendedInstance != nil && extendedInstance.logger != nil {
		extendedInstance.logger.LogWithFields(ctx, "info", message, fields)
	} else {
		logger.Info("%s %+v", message, fields)
	}
}

// ErrorWithFields logs an error message with additional fields
func ErrorWithFields(ctx context.Context, message string, fields map[string]interface{}) {
	if extendedInstance != nil && extendedInstance.logger != nil {
		extendedInstance.logger.LogWithFields(ctx, "error", message, fields)
	} else {
		logger.Error("%s %+v", message, fields)
	}
}