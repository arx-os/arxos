package telemetry

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Backend defines the interface for tracing backends
type Backend interface {
	Export(ctx context.Context, spans []*Span) error
	Close() error
}

// Config holds tracing backend configuration
type Config struct {
	Provider     string            `json:"provider"` // jaeger, zipkin, otlp
	Endpoint     string            `json:"endpoint"`
	ServiceName  string            `json:"service_name"`
	Environment  string            `json:"environment"`
	SampleRate   float64           `json:"sample_rate"`
	BatchSize    int               `json:"batch_size"`
	FlushTimeout time.Duration     `json:"flush_timeout"`
	Options      map[string]string `json:"options"`
}

// NewBackend creates a new tracing backend based on configuration
func NewBackend(config Config) (Backend, error) {
	switch config.Provider {
	case "jaeger":
		return NewJaegerBackend(config)
	case "zipkin":
		return NewZipkinBackend(config)
	case "otlp":
		return NewOTLPBackend(config)
	case "console":
		return NewConsoleBackend(config)
	default:
		return nil, fmt.Errorf("unsupported tracing backend: %s", config.Provider)
	}
}

// ConsoleBackend implements Backend for console output (development)
type ConsoleBackend struct {
	config Config
}

// NewConsoleBackend creates a new console tracing backend
func NewConsoleBackend(config Config) (Backend, error) {
	return &ConsoleBackend{
		config: config,
	}, nil
}

// Export exports spans to console
func (b *ConsoleBackend) Export(ctx context.Context, spans []*Span) error {
	logger.Debug("Exporting %d spans to console backend", len(spans))

	for _, span := range spans {
		logger.Debug("Span: %s [%s] - %s (duration: %v)",
			span.TraceID, span.SpanID, span.Operation, span.Duration)

		for key, value := range span.Tags {
			logger.Debug("  Tag: %s = %v", key, value)
		}

		for _, log := range span.Logs {
			logger.Debug("  Log: %s - %v", log.Timestamp.Format(time.RFC3339), log.Fields)
		}
	}

	return nil
}

// Close closes the console backend
func (b *ConsoleBackend) Close() error {
	return nil
}
