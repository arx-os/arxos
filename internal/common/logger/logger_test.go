package logger

import (
	"bytes"
	"log"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestLogLevel_Constants(t *testing.T) {
	// Ensure log levels have correct ordering
	assert.Equal(t, 0, int(DEBUG))
	assert.Equal(t, 1, int(INFO))
	assert.Equal(t, 2, int(WARN))
	assert.Equal(t, 3, int(ERROR))
	
	// Verify ordering for filtering
	assert.True(t, DEBUG < INFO)
	assert.True(t, INFO < WARN)
	assert.True(t, WARN < ERROR)
}

func TestNew(t *testing.T) {
	tests := []struct {
		name  string
		level LogLevel
	}{
		{"debug logger", DEBUG},
		{"info logger", INFO},
		{"warn logger", WARN},
		{"error logger", ERROR},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			logger := New(tt.level)
			assert.NotNil(t, logger)
			assert.Equal(t, tt.level, logger.level)
			assert.NotNil(t, logger.logger)
		})
	}
}

func TestLogger_SetLevel(t *testing.T) {
	originalLevel := defaultLogger.level
	defer func() {
		defaultLogger.level = originalLevel
	}()

	SetLevel(DEBUG)
	assert.Equal(t, DEBUG, defaultLogger.level)

	SetLevel(ERROR)
	assert.Equal(t, ERROR, defaultLogger.level)
}

func TestLogger_LevelFiltering(t *testing.T) {
	// Capture output
	var buf bytes.Buffer
	logger := New(WARN)
	logger.logger = log.New(&buf, "", 0)

	// Test that only messages at or above the level are logged
	logger.Debug("debug message")
	logger.Info("info message") 
	logger.Warn("warn message")
	logger.Error("error message")

	output := buf.String()
	
	// Should not contain debug or info
	assert.NotContains(t, output, "debug message")
	assert.NotContains(t, output, "info message")
	
	// Should contain warn and error
	assert.Contains(t, output, "warn message")
	assert.Contains(t, output, "error message")
	assert.Contains(t, output, "[WARN]")
	assert.Contains(t, output, "[ERROR]")
}

func TestLogger_MessageFormatting(t *testing.T) {
	var buf bytes.Buffer
	logger := New(DEBUG)
	logger.logger = log.New(&buf, "", 0)

	// Test basic message
	logger.Info("test message")
	output := buf.String()
	assert.Contains(t, output, "[INFO] test message")

	// Test formatted message
	buf.Reset()
	logger.Error("error %d: %s", 404, "not found")
	output = buf.String()
	assert.Contains(t, output, "[ERROR] error 404: not found")

	// Test message with no args
	buf.Reset()
	logger.Warn("simple warning")
	output = buf.String()
	assert.Contains(t, output, "[WARN] simple warning")
}

func TestLogger_DebugLevel(t *testing.T) {
	var buf bytes.Buffer
	logger := New(DEBUG)
	logger.logger = log.New(&buf, "", 0)

	logger.Debug("debug test")
	output := buf.String()
	assert.Contains(t, output, "[DEBUG] debug test")
}

func TestLogger_InfoLevel(t *testing.T) {
	var buf bytes.Buffer
	logger := New(INFO)
	logger.logger = log.New(&buf, "", 0)

	logger.Info("info test")
	output := buf.String()
	assert.Contains(t, output, "[INFO] info test")

	// Debug should be filtered out
	buf.Reset()
	logger.Debug("debug test")
	output = buf.String()
	assert.Empty(t, output)
}

func TestLogger_WarnLevel(t *testing.T) {
	var buf bytes.Buffer
	logger := New(WARN)
	logger.logger = log.New(&buf, "", 0)

	logger.Warn("warn test")
	output := buf.String()
	assert.Contains(t, output, "[WARN] warn test")

	// Info and Debug should be filtered out
	buf.Reset()
	logger.Info("info test")
	logger.Debug("debug test")
	output = buf.String()
	assert.Empty(t, output)
}

func TestLogger_ErrorLevel(t *testing.T) {
	var buf bytes.Buffer
	logger := New(ERROR)
	logger.logger = log.New(&buf, "", 0)

	logger.Error("error test")
	output := buf.String()
	assert.Contains(t, output, "[ERROR] error test")

	// All other levels should be filtered out
	buf.Reset()
	logger.Warn("warn test")
	logger.Info("info test")
	logger.Debug("debug test")
	output = buf.String()
	assert.Empty(t, output)
}

func TestGlobalFunctions(t *testing.T) {
	// Test that global functions use the defaultLogger
	originalLevel := defaultLogger.level
	originalLogger := defaultLogger.logger
	defer func() {
		defaultLogger.level = originalLevel
		defaultLogger.logger = originalLogger
	}()

	// Replace the logger with a buffer for testing
	var buf bytes.Buffer
	defaultLogger.logger = log.New(&buf, "", 0)
	SetLevel(DEBUG)

	// Send some log messages
	Debug("debug test %d", 1)
	Info("info test %d", 2)  
	Warn("warn test %d", 3)
	Error("error test %d", 4)

	output := buf.String()

	// Verify all messages were logged
	assert.Contains(t, output, "[DEBUG] debug test 1")
	assert.Contains(t, output, "[INFO] info test 2")
	assert.Contains(t, output, "[WARN] warn test 3")
	assert.Contains(t, output, "[ERROR] error test 4")
}

func TestGlobalFunctions_WithFiltering(t *testing.T) {
	originalLevel := defaultLogger.level
	originalLogger := defaultLogger.logger
	defer func() {
		defaultLogger.level = originalLevel
		defaultLogger.logger = originalLogger
	}()

	// Replace the logger with a buffer for testing
	var buf bytes.Buffer
	defaultLogger.logger = log.New(&buf, "", 0)
	SetLevel(WARN)

	// Send messages at different levels
	Debug("debug message")
	Info("info message")
	Warn("warn message") 
	Error("error message")

	output := buf.String()

	// Only WARN and ERROR should appear
	assert.NotContains(t, output, "debug message")
	assert.NotContains(t, output, "info message")
	assert.Contains(t, output, "warn message")
	assert.Contains(t, output, "error message")
}

func TestLogger_EmptyMessage(t *testing.T) {
	var buf bytes.Buffer
	logger := New(INFO)
	logger.logger = log.New(&buf, "", 0)

	logger.Info("")
	output := buf.String()
	assert.Contains(t, output, "[INFO]")
}

func TestLogger_SpecialCharacters(t *testing.T) {
	var buf bytes.Buffer
	logger := New(INFO)
	logger.logger = log.New(&buf, "", 0)

	// Test with special characters
	logger.Info("message with\nnewline and\ttab")
	output := buf.String()
	assert.Contains(t, output, "message with\nnewline and\ttab")

	// Test with format characters  
	buf.Reset()
	logger.Info("100%% complete")
	output = buf.String()
	assert.Contains(t, output, "100% complete")
}

func TestLogger_NilArguments(t *testing.T) {
	var buf bytes.Buffer
	logger := New(INFO)
	logger.logger = log.New(&buf, "", 0)

	// Test with nil argument in format
	logger.Info("value: %v", nil)
	output := buf.String()
	assert.Contains(t, output, "value: <nil>")
}

func TestLogger_LargeMessage(t *testing.T) {
	var buf bytes.Buffer
	logger := New(INFO)
	logger.logger = log.New(&buf, "", 0)

	// Test with large message
	largeMsg := strings.Repeat("x", 10000)
	logger.Info("large: %s", largeMsg)
	output := buf.String()
	assert.Contains(t, output, "[INFO] large:")
	assert.Contains(t, output, largeMsg)
}

func TestLogger_ConcurrentAccess(t *testing.T) {
	var buf bytes.Buffer
	logger := New(INFO)
	logger.logger = log.New(&buf, "", 0)

	done := make(chan bool, 10)

	// Start multiple goroutines logging concurrently
	for i := 0; i < 10; i++ {
		go func(id int) {
			logger.Info("concurrent message %d", id)
			done <- true
		}(i)
	}

	// Wait for all to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	output := buf.String()
	// Should contain messages from all goroutines
	messageCount := strings.Count(output, "[INFO] concurrent message")
	assert.Equal(t, 10, messageCount)
}

func TestDefaultLogger_Initialization(t *testing.T) {
	// Test that default logger is properly initialized
	assert.NotNil(t, defaultLogger)
	assert.Equal(t, INFO, defaultLogger.level)
	assert.NotNil(t, defaultLogger.logger)
}

func TestLogger_OutputCallerInfo(t *testing.T) {
	// Test that the logger includes caller info (file:line)
	var buf bytes.Buffer
	logger := New(INFO)
	// Use default flags to include file info
	logger.logger = log.New(&buf, "", log.Lshortfile)

	logger.Info("test message")
	output := buf.String()
	
	// Should contain filename and line number
	assert.Contains(t, output, "logger_test.go:")
	assert.Contains(t, output, "[INFO] test message")
}

func TestLogger_FormatEdgeCases(t *testing.T) {
	var buf bytes.Buffer
	logger := New(DEBUG)
	logger.logger = log.New(&buf, "", 0)

	// Test format string with correct arguments
	logger.Debug("format %s %d", "test", 42)
	output := buf.String()
	assert.Contains(t, output, "[DEBUG] format test 42")

	// Test with percent in message
	buf.Reset()
	logger.Info("100%% complete")
	output = buf.String()
	assert.Contains(t, output, "[INFO] 100% complete")
}