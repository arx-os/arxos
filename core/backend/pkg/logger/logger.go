package logger

import (
	"context"
	"fmt"
	"io"
	"os"
	"runtime"
	"strings"
	"time"

	"encoding/json"
	"path/filepath"
	"sync"
)

// Logger interface defines the logging contract
type Logger interface {
	Debug(msg string, fields ...Field)
	Info(msg string, fields ...Field)
	Warn(msg string, fields ...Field)
	Error(msg string, fields ...Field)
	Fatal(msg string, fields ...Field)
	
	WithField(key string, value interface{}) Logger
	WithFields(fields map[string]interface{}) Logger
	WithContext(ctx context.Context) Logger
	WithError(err error) Logger
}

// Field represents a log field
type Field struct {
	Key   string
	Value interface{}
}

// Level represents the log level
type Level int

const (
	DebugLevel Level = iota
	InfoLevel
	WarnLevel
	ErrorLevel
	FatalLevel
)

// logger is the default implementation
type logger struct {
	mu       sync.RWMutex
	level    Level
	format   string // json or text
	output   io.Writer
	fields   map[string]interface{}
	context  context.Context
}

var (
	defaultLogger *logger
	once          sync.Once
)

// Initialize sets up the default logger
func Initialize(level, format string, output io.Writer) {
	once.Do(func() {
		defaultLogger = &logger{
			level:  parseLevel(level),
			format: format,
			output: output,
			fields: make(map[string]interface{}),
		}
	})
}

// GetLogger returns the default logger instance
func GetLogger() Logger {
	if defaultLogger == nil {
		// Initialize with defaults if not already done
		Initialize("info", "json", os.Stdout)
	}
	return defaultLogger
}

// New creates a new logger instance
func New(level, format string, output io.Writer) Logger {
	return &logger{
		level:  parseLevel(level),
		format: format,
		output: output,
		fields: make(map[string]interface{}),
	}
}

// Implementation of Logger interface

func (l *logger) Debug(msg string, fields ...Field) {
	l.log(DebugLevel, msg, fields...)
}

func (l *logger) Info(msg string, fields ...Field) {
	l.log(InfoLevel, msg, fields...)
}

func (l *logger) Warn(msg string, fields ...Field) {
	l.log(WarnLevel, msg, fields...)
}

func (l *logger) Error(msg string, fields ...Field) {
	l.log(ErrorLevel, msg, fields...)
}

func (l *logger) Fatal(msg string, fields ...Field) {
	l.log(FatalLevel, msg, fields...)
	os.Exit(1)
}

func (l *logger) WithField(key string, value interface{}) Logger {
	newLogger := l.clone()
	newLogger.fields[key] = value
	return newLogger
}

func (l *logger) WithFields(fields map[string]interface{}) Logger {
	newLogger := l.clone()
	for k, v := range fields {
		newLogger.fields[k] = v
	}
	return newLogger
}

func (l *logger) WithContext(ctx context.Context) Logger {
	newLogger := l.clone()
	newLogger.context = ctx
	
	// Extract common context values
	if requestID := ctx.Value("request_id"); requestID != nil {
		newLogger.fields["request_id"] = requestID
	}
	if userID := ctx.Value("user_id"); userID != nil {
		newLogger.fields["user_id"] = userID
	}
	
	return newLogger
}

func (l *logger) WithError(err error) Logger {
	if err == nil {
		return l
	}
	return l.WithField("error", err.Error())
}

// Internal methods

func (l *logger) log(level Level, msg string, fields ...Field) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if level < l.level {
		return
	}

	entry := l.createEntry(level, msg, fields...)
	
	var output []byte
	var err error
	
	if l.format == "json" {
		output, err = json.Marshal(entry)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Failed to marshal log entry: %v\n", err)
			return
		}
		output = append(output, '\n')
	} else {
		output = []byte(l.formatText(entry))
	}
	
	l.output.Write(output)
}

func (l *logger) createEntry(level Level, msg string, fields ...Field) map[string]interface{} {
	entry := make(map[string]interface{})
	
	// Add timestamp
	entry["timestamp"] = time.Now().UTC().Format(time.RFC3339Nano)
	entry["level"] = levelString(level)
	entry["message"] = msg
	
	// Add caller information
	if pc, file, line, ok := runtime.Caller(3); ok {
		entry["file"] = filepath.Base(file)
		entry["line"] = line
		
		if fn := runtime.FuncForPC(pc); fn != nil {
			entry["function"] = filepath.Base(fn.Name())
		}
	}
	
	// Add persistent fields
	for k, v := range l.fields {
		entry[k] = v
	}
	
	// Add provided fields
	for _, field := range fields {
		entry[field.Key] = field.Value
	}
	
	return entry
}

func (l *logger) formatText(entry map[string]interface{}) string {
	var sb strings.Builder
	
	// Format: [TIME] LEVEL message key=value key=value...
	timestamp := entry["timestamp"].(string)
	level := entry["level"].(string)
	message := entry["message"].(string)
	
	sb.WriteString(fmt.Sprintf("[%s] %-5s %s", timestamp, level, message))
	
	// Add fields
	for k, v := range entry {
		if k == "timestamp" || k == "level" || k == "message" {
			continue
		}
		sb.WriteString(fmt.Sprintf(" %s=%v", k, v))
	}
	
	sb.WriteString("\n")
	return sb.String()
}

func (l *logger) clone() *logger {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	newFields := make(map[string]interface{})
	for k, v := range l.fields {
		newFields[k] = v
	}
	
	return &logger{
		level:   l.level,
		format:  l.format,
		output:  l.output,
		fields:  newFields,
		context: l.context,
	}
}

// Helper functions

func parseLevel(level string) Level {
	switch strings.ToLower(level) {
	case "debug":
		return DebugLevel
	case "info":
		return InfoLevel
	case "warn", "warning":
		return WarnLevel
	case "error":
		return ErrorLevel
	case "fatal":
		return FatalLevel
	default:
		return InfoLevel
	}
}

func levelString(level Level) string {
	switch level {
	case DebugLevel:
		return "DEBUG"
	case InfoLevel:
		return "INFO"
	case WarnLevel:
		return "WARN"
	case ErrorLevel:
		return "ERROR"
	case FatalLevel:
		return "FATAL"
	default:
		return "UNKNOWN"
	}
}

// Helper constructor functions for fields

func String(key, value string) Field {
	return Field{Key: key, Value: value}
}

func Int(key string, value int) Field {
	return Field{Key: key, Value: value}
}

func Int64(key string, value int64) Field {
	return Field{Key: key, Value: value}
}

func Float64(key string, value float64) Field {
	return Field{Key: key, Value: value}
}

func Bool(key string, value bool) Field {
	return Field{Key: key, Value: value}
}

func Any(key string, value interface{}) Field {
	return Field{Key: key, Value: value}
}

func Duration(key string, value time.Duration) Field {
	return Field{Key: key, Value: value.String()}
}

func Time(key string, value time.Time) Field {
	return Field{Key: key, Value: value.Format(time.RFC3339)}
}

func Err(err error) Field {
	if err == nil {
		return Field{Key: "error", Value: nil}
	}
	return Field{Key: "error", Value: err.Error()}
}

// Package-level convenience functions

func Debug(msg string, fields ...Field) {
	GetLogger().Debug(msg, fields...)
}

func Info(msg string, fields ...Field) {
	GetLogger().Info(msg, fields...)
}

func Warn(msg string, fields ...Field) {
	GetLogger().Warn(msg, fields...)
}

func Error(msg string, fields ...Field) {
	GetLogger().Error(msg, fields...)
}

func Fatal(msg string, fields ...Field) {
	GetLogger().Fatal(msg, fields...)
}