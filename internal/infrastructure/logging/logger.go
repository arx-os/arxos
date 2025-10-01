package logging

import (
	"log"
	"os"
)

// LogLevel represents the severity of a log message
type LogLevel int

const (
	DEBUG LogLevel = iota
	INFO
	WARN
	ERROR
)

// Logger provides structured logging following Clean Architecture
type Logger struct {
	level  LogLevel
	logger *log.Logger
}

// NewLogger creates a new logger instance
func NewLogger(level LogLevel) *Logger {
	return &Logger{
		level:  level,
		logger: log.New(os.Stdout, "[ARXOS] ", log.LstdFlags|log.Lshortfile),
	}
}

// SetLevel sets the logging level
func (l *Logger) SetLevel(level LogLevel) {
	l.level = level
}

// Debug logs a debug message
func (l *Logger) Debug(format string, args ...interface{}) {
	if l.level <= DEBUG {
		l.logger.Printf("[DEBUG] "+format, args...)
	}
}

// Info logs an info message
func (l *Logger) Info(format string, args ...interface{}) {
	if l.level <= INFO {
		l.logger.Printf("[INFO] "+format, args...)
	}
}

// Warn logs a warning message
func (l *Logger) Warn(format string, args ...interface{}) {
	if l.level <= WARN {
		l.logger.Printf("[WARN] "+format, args...)
	}
}

// Error logs an error message
func (l *Logger) Error(format string, args ...interface{}) {
	if l.level <= ERROR {
		l.logger.Printf("[ERROR] "+format, args...)
	}
}

// Fatal logs a fatal message and exits
func (l *Logger) Fatal(format string, args ...interface{}) {
	l.logger.Printf("[FATAL] "+format, args...)
	os.Exit(1)
}

// WithFields creates a logger with additional fields
func (l *Logger) WithFields(fields map[string]interface{}) *Logger {
	// Simplified implementation - in a real logger you'd store fields
	return l
}
