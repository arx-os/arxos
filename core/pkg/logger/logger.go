package logger

import (
	"log"
	"os"
)

// Logger provides basic logging functionality
type Logger struct {
	*log.Logger
}

// NewLogger creates a new logger instance
func NewLogger() *Logger {
	return &Logger{
		Logger: log.New(os.Stdout, "[ARXOS] ", log.LstdFlags|log.Lshortfile),
	}
}
