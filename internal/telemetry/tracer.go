package telemetry

import (
	"context"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Tracer provides distributed tracing capabilities
type Tracer interface {
	StartSpan(ctx context.Context, operation string) (context.Context, *Span)
	FinishSpan(span *Span, err error)
	AddTag(span *Span, key string, value interface{})
	AddLog(span *Span, level, message string, fields map[string]interface{})
}

// TracerConfig holds tracing configuration
type TracerConfig struct {
	ServiceName string  `json:"service_name"`
	Endpoint    string  `json:"endpoint"`
	Enabled     bool    `json:"enabled"`
	SampleRate  float64 `json:"sample_rate"`
}

// DefaultTracer implements the Tracer interface
type DefaultTracer struct {
	config     *TracerConfig
	spans      map[string]*Span
	activeSpan string
	mu         sync.RWMutex
	backend    Backend
}

// NewTracer creates a new tracer
func NewTracer(config *ObservabilityConfig) Tracer {
	tracerConfig := &TracerConfig{
		ServiceName: config.ServiceName,
		Endpoint:    config.Tracing.Endpoint,
		Enabled:     config.Tracing.Enabled,
		SampleRate:  config.Tracing.SampleRate,
	}

	// Create backend
	backendConfig := Config{
		Provider:     "console", // Default to console for now
		Endpoint:     config.Tracing.Endpoint,
		ServiceName:  config.ServiceName,
		Environment:  config.Environment,
		SampleRate:   config.Tracing.SampleRate,
		BatchSize:    100,
		FlushTimeout: 5 * time.Second,
		Options:      make(map[string]string),
	}

	backend, err := NewBackend(backendConfig)
	if err != nil {
		logger.Error("Failed to create tracing backend: %v", err)
		backend = &ConsoleBackend{config: backendConfig}
	}

	return &DefaultTracer{
		config:  tracerConfig,
		spans:   make(map[string]*Span),
		backend: backend,
	}
}

// StartSpan starts a new span
func (t *DefaultTracer) StartSpan(ctx context.Context, operation string) (context.Context, *Span) {
	if !t.config.Enabled {
		return ctx, nil
	}

	// Generate trace and span IDs
	traceID := generateTraceID()
	spanID := generateSpanID()

	// Check if we're in an existing trace
	if existingTraceID := ctx.Value("trace_id"); existingTraceID != nil {
		traceID = existingTraceID.(string)
	}

	span := &Span{
		TraceID:   traceID,
		SpanID:    spanID,
		Operation: operation,
		Service:   t.config.ServiceName,
		StartTime: time.Now(),
		Tags:      make(map[string]interface{}),
		Logs:      make([]SpanLog, 0),
		Status:    SpanStatusOK,
		Context:   ctx,
	}

	// Set parent span if exists
	if parentSpanID := ctx.Value("span_id"); parentSpanID != nil {
		span.ParentID = parentSpanID.(string)
	}

	// Store span
	t.mu.Lock()
	t.spans[span.SpanID] = span
	t.activeSpan = span.SpanID
	t.mu.Unlock()

	// Add span to context
	ctx = context.WithValue(ctx, "trace_id", span.TraceID)
	ctx = context.WithValue(ctx, "span_id", span.SpanID)
	ctx = context.WithValue(ctx, "span", span)

	return ctx, span
}

// FinishSpan finishes a span
func (t *DefaultTracer) FinishSpan(span *Span, err error) {
	if span == nil || !t.config.Enabled {
		return
	}

	span.Finish()

	if err != nil {
		span.SetError(err)
	}

	// Send span to backend
	go func() {
		if err := t.backend.Export(context.Background(), []*Span{span}); err != nil {
			logger.Error("Failed to export span: %v", err)
		}
	}()

	// Remove from active spans
	t.mu.Lock()
	delete(t.spans, span.SpanID)
	if t.activeSpan == span.SpanID {
		t.activeSpan = ""
	}
	t.mu.Unlock()
}

// AddTag adds a tag to a span
func (t *DefaultTracer) AddTag(span *Span, key string, value interface{}) {
	if span != nil {
		span.SetAttribute(key, value)
	}
}

// AddLog adds a log entry to a span
func (t *DefaultTracer) AddLog(span *Span, level, message string, fields map[string]interface{}) {
	if span != nil {
		span.AddLog(level, message, fields)
	}
}

// GetSpanFromContext retrieves a span from context
func GetSpanFromContext(ctx context.Context) *Span {
	if span := ctx.Value("span"); span != nil {
		return span.(*Span)
	}
	return nil
}

// GetTraceIDFromContext retrieves a trace ID from context
func GetTraceIDFromContext(ctx context.Context) string {
	if traceID := ctx.Value("trace_id"); traceID != nil {
		return traceID.(string)
	}
	return ""
}

// ContextKey is a type for context keys
type ContextKey string

const (
	TraceIDKey ContextKey = "trace_id"
	SpanIDKey  ContextKey = "span_id"
	SpanKey    ContextKey = "span"
)
