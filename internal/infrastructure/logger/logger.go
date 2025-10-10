package logger

import (
	"fmt"
	"log"
	"os"
	"strings"
)

// Logger implements domain.Logger interface
type Logger struct {
	level LogLevel
}

// LogLevel represents logging levels
type LogLevel int

const (
	LevelDebug LogLevel = iota
	LevelInfo
	LevelWarn
	LevelError
)

// New creates a new logger
func New(level string) *Logger {
	return &Logger{
		level: parseLogLevel(level),
	}
}

// Debug logs debug messages
func (l *Logger) Debug(msg string, keysAndValues ...interface{}) {
	if l.level <= LevelDebug {
		l.log("DEBUG", msg, keysAndValues...)
	}
}

// Info logs info messages
func (l *Logger) Info(msg string, keysAndValues ...interface{}) {
	if l.level <= LevelInfo {
		l.log("INFO", msg, keysAndValues...)
	}
}

// Warn logs warning messages
func (l *Logger) Warn(msg string, keysAndValues ...interface{}) {
	if l.level <= LevelWarn {
		l.log("WARN", msg, keysAndValues...)
	}
}

// Error logs error messages
func (l *Logger) Error(msg string, keysAndValues ...interface{}) {
	if l.level <= LevelError {
		l.log("ERROR", msg, keysAndValues...)
	}
}

// Fatal logs fatal messages and exits
func (l *Logger) Fatal(msg string, keysAndValues ...interface{}) {
	l.log("FATAL", msg, keysAndValues...)
	os.Exit(1)
}

// log formats and logs a message
func (l *Logger) log(level, msg string, keysAndValues ...interface{}) {
	// Format key-value pairs
	pairs := formatKeyValues(keysAndValues...)
	
	if pairs != "" {
		log.Printf("[%s] %s %s", level, msg, pairs)
	} else {
		log.Printf("[%s] %s", level, msg)
	}
}

// formatKeyValues formats key-value pairs for logging
func formatKeyValues(keysAndValues ...interface{}) string {
	if len(keysAndValues) == 0 {
		return ""
	}

	var parts []string
	for i := 0; i < len(keysAndValues); i += 2 {
		if i+1 < len(keysAndValues) {
			key := fmt.Sprintf("%v", keysAndValues[i])
			value := fmt.Sprintf("%v", keysAndValues[i+1])
			parts = append(parts, fmt.Sprintf("%s=%s", key, value))
		}
	}

	return strings.Join(parts, " ")
}

// parseLogLevel parses a log level string
func parseLogLevel(level string) LogLevel {
	switch strings.ToUpper(level) {
	case "DEBUG":
		return LevelDebug
	case "INFO":
		return LevelInfo
	case "WARN", "WARNING":
		return LevelWarn
	case "ERROR":
		return LevelError
	default:
		return LevelInfo
	}
}

// SetOutput sets the log output destination
func SetOutput(w *os.File) {
	log.SetOutput(w)
}

