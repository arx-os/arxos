package infrastructure

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
)

// Logger implements the logger interface following Clean Architecture
type Logger struct {
	config *config.Config
	logger *log.Logger
}

// NewLogger creates a new logger instance
func NewLogger(cfg *config.Config) domain.Logger {
	return &Logger{
		config: cfg,
		logger: log.New(os.Stdout, "[ARXOS] ", log.LstdFlags|log.Lshortfile),
	}
}

// Debug logs a debug message
func (l Logger) Debug(msg string, fields ...any) {
	if l.config.Mode == "development" {
		l.log("DEBUG", msg, fields...)
	}
}

// Info logs an info message
func (l *Logger) Info(msg string, fields ...any) {
	l.log("INFO", msg, fields...)
}

// Warn logs a warning message
func (l *Logger) Warn(msg string, fields ...any) {
	l.log("WARN", msg, fields...)
}

// Error logs an error message
func (l *Logger) Error(msg string, fields ...any) {
	l.log("ERROR", msg, fields...)
}

// Fatal logs a fatal message and exits
func (l *Logger) Fatal(msg string, fields ...any) {
	l.log("FATAL", msg, fields...)
	os.Exit(1)
}

// log formats and logs a message with fields
func (l *Logger) log(level, msg string, fields ...any) {
	// Format fields as key-value pairs
	formattedMsg := msg
	if len(fields) > 0 {
		formattedMsg += " | "
		for i := 0; i < len(fields); i += 2 {
			if i+1 < len(fields) {
				formattedMsg += fmt.Sprintf("%v=%v ", fields[i], fields[i+1])
			}
		}
	}

	l.logger.Printf("[%s] %s", level, formattedMsg)
}

// WithFields returns a logger with additional fields
// Implements domain.Logger interface
func (l *Logger) WithFields(fields map[string]any) domain.Logger {
	// For simplicity, return the same logger
	// In a production logger, you'd store fields and include them in all logs
	return l
}

// StructuredLogger provides structured logging capabilities
type StructuredLogger struct {
	*Logger
}

// NewStructuredLogger creates a new structured logger
func NewStructuredLogger(cfg *config.Config) domain.Logger {
	return &StructuredLogger{
		Logger: NewLogger(cfg).(*Logger),
	}
}

// LogWithFields logs a message with structured fields
func (sl *StructuredLogger) LogWithFields(level, msg string, fields map[string]any) {
	// Convert map to key-value pairs
	var fieldPairs []any
	for k, v := range fields {
		fieldPairs = append(fieldPairs, k, v)
	}

	// Use the base logger's log method
	sl.Logger.log(level, msg, fieldPairs...)
}

// DebugWithFields logs a debug message with structured fields
func (sl *StructuredLogger) DebugWithFields(msg string, fields map[string]any) {
	sl.LogWithFields("DEBUG", msg, fields)
}

// InfoWithFields logs an info message with structured fields
func (sl *StructuredLogger) InfoWithFields(msg string, fields map[string]any) {
	sl.LogWithFields("INFO", msg, fields)
}

// WarnWithFields logs a warning message with structured fields
func (sl *StructuredLogger) WarnWithFields(msg string, fields map[string]any) {
	sl.LogWithFields("WARN", msg, fields)
}

// ErrorWithFields logs an error message with structured fields
func (sl *StructuredLogger) ErrorWithFields(msg string, fields map[string]any) {
	sl.LogWithFields("ERROR", msg, fields)
}

// JSONLogger provides JSON-formatted logging
type JSONLogger struct {
	*Logger
}

// NewJSONLogger creates a new JSON logger
func NewJSONLogger(cfg *config.Config) domain.Logger {
	return &JSONLogger{
		Logger: NewLogger(cfg).(*Logger),
	}
}

// LogJSON logs a message in JSON format
func (jl *JSONLogger) LogJSON(level, msg string, fields map[string]any) {
	// Create JSON log entry
	logEntry := map[string]any{
		"level":   level,
		"message": msg,
		"time":    time.Now().Format(time.RFC3339),
	}

	// Add fields to log entry
	for k, v := range fields {
		logEntry[k] = v
	}

	// Marshal to JSON
	jsonBytes, err := json.Marshal(logEntry)
	if err != nil {
		// Fallback to base logger if JSON marshaling fails
		jl.Logger.log(level, msg)
		return
	}

	// Log the JSON string
	jl.Logger.log(level, string(jsonBytes))
}
