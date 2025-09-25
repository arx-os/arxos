package telemetry

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Tracer manages distributed tracing
type Tracer struct {
	config  *ObservabilityConfig
	backend Backend
	spans   map[string]*Span
	mu      sync.RWMutex
}

// Span represents a tracing span
type Span struct {
	TraceID       string                 `json:"trace_id"`
	SpanID        string                 `json:"span_id"`
	ParentID      string                 `json:"parent_id,omitempty"`
	Name          string                 `json:"name"`
	OperationName string                 `json:"operation_name"` // Alias for Name for backend compatibility
	StartTime     time.Time              `json:"start_time"`
	EndTime       *time.Time             `json:"end_time,omitempty"`
	Duration      *time.Duration         `json:"duration,omitempty"`
	Attributes    map[string]interface{} `json:"attributes"`
	Tags          map[string]interface{} `json:"tags"` // Alias for Attributes for backend compatibility
	Events        []SpanEvent            `json:"events"`
	Logs          []SpanLog              `json:"logs"` // Alias for Events for backend compatibility
	Status        SpanStatus             `json:"status"`
	mu            sync.RWMutex
}

// SpanLog represents a log entry within a span (alias for SpanEvent for backend compatibility)
type SpanLog struct {
	Timestamp time.Time              `json:"timestamp"`
	Fields    map[string]interface{} `json:"fields"`
}

// SpanEvent represents an event within a span
type SpanEvent struct {
	Name       string                 `json:"name"`
	Timestamp  time.Time              `json:"timestamp"`
	Attributes map[string]interface{} `json:"attributes"`
}

// SpanStatus represents the status of a span
type SpanStatus struct {
	Code    SpanStatusCode `json:"code"`
	Message string         `json:"message,omitempty"`
}

// SpanStatusCode represents span status codes
type SpanStatusCode int

const (
	SpanStatusUnset SpanStatusCode = iota
	SpanStatusOK
	SpanStatusError
)

// ContextKey is used for context keys
type ContextKey string

const (
	SpanContextKey ContextKey = "span"
	TraceIDKey     ContextKey = "trace_id"
)

// NewTracer creates a new tracer
func NewTracer(config *ObservabilityConfig) *Tracer {
	return &Tracer{
		config: config,
		spans:  make(map[string]*Span),
	}
}

// NewTracerWithBackend creates a new tracer with a specific backend
func NewTracerWithBackend(config *ObservabilityConfig, backend Backend) *Tracer {
	return &Tracer{
		config:  config,
		backend: backend,
		spans:   make(map[string]*Span),
	}
}

// SetBackend sets the tracing backend for the tracer
func (t *Tracer) SetBackend(backend Backend) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.backend = backend
}

// StartSpan starts a new span
func (t *Tracer) StartSpan(ctx context.Context, name string) (context.Context, *Span) {
	traceID := generateTraceID()
	spanID := generateSpanID()
	parentID := ""

	// Check if there's a parent span in context
	if parentSpan := SpanFromContext(ctx); parentSpan != nil {
		traceID = parentSpan.TraceID
		parentID = parentSpan.SpanID
	}

	span := &Span{
		TraceID:       traceID,
		SpanID:        spanID,
		ParentID:      parentID,
		Name:          name,
		OperationName: name, // Set alias for backend compatibility
		StartTime:     time.Now(),
		Attributes:    make(map[string]interface{}),
		Tags:          make(map[string]interface{}), // Initialize tags alias
		Events:        make([]SpanEvent, 0),
		Logs:          make([]SpanLog, 0), // Initialize logs alias
		Status:        SpanStatus{Code: SpanStatusUnset},
	}

	// Store span
	t.mu.Lock()
	t.spans[spanID] = span
	t.mu.Unlock()

	// Add span to context
	ctx = context.WithValue(ctx, SpanContextKey, span)
	ctx = context.WithValue(ctx, TraceIDKey, traceID)

	return ctx, span
}

// Stop stops the tracer
func (t *Tracer) Stop() {
	// Export remaining spans
	t.mu.RLock()
	spans := make([]*Span, 0, len(t.spans))
	for _, span := range t.spans {
		spans = append(spans, span)
	}
	t.mu.RUnlock()

	if len(spans) > 0 {
		logger.Debug("Exporting %d remaining spans", len(spans))
		// Export to tracing backend
		if err := t.exportToBackend(spans); err != nil {
			logger.Error("Failed to export spans to tracing backend: %v", err)
		}
	}
}

// SetAttribute sets an attribute on the span
func (s *Span) SetAttribute(key string, value interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Attributes[key] = value
}

// AddEvent adds an event to the span
func (s *Span) AddEvent(name string, attributes map[string]interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()

	event := SpanEvent{
		Name:       name,
		Timestamp:  time.Now(),
		Attributes: attributes,
	}
	s.Events = append(s.Events, event)

	// Also add to logs for backend compatibility
	log := SpanLog{
		Timestamp: time.Now(),
		Fields:    attributes,
	}
	s.Logs = append(s.Logs, log)
}

// SetStatus sets the status of the span
func (s *Span) SetStatus(code SpanStatusCode, message string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.Status = SpanStatus{
		Code:    code,
		Message: message,
	}
}

// RecordError records an error on the span
func (s *Span) RecordError(err error) {
	s.SetStatus(SpanStatusError, err.Error())
	s.AddEvent("exception", map[string]interface{}{
		"exception.type":    fmt.Sprintf("%T", err),
		"exception.message": err.Error(),
	})
}

// Finish finishes the span
func (s *Span) Finish() {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.EndTime != nil {
		return // Already finished
	}

	endTime := time.Now()
	s.EndTime = &endTime
	duration := endTime.Sub(s.StartTime)
	s.Duration = &duration

	// Record span duration as metric
	Metric("span_duration_seconds", duration.Seconds(), map[string]interface{}{
		"span_name": s.Name,
		"trace_id":  s.TraceID,
	})

	logger.Debug("Span finished: %s (trace: %s, duration: %v)", s.Name, s.TraceID, duration)
}

// AddAttribute adds an attribute to the span
func (s *Span) AddAttribute(key string, value interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Attributes[key] = value
	s.Tags[key] = value // Update alias for backend compatibility
}

// SpanFromContext extracts a span from context
func SpanFromContext(ctx context.Context) *Span {
	if span, ok := ctx.Value(SpanContextKey).(*Span); ok {
		return span
	}
	return nil
}

// TraceIDFromContext extracts a trace ID from context
func TraceIDFromContext(ctx context.Context) string {
	if traceID, ok := ctx.Value(TraceIDKey).(string); ok {
		return traceID
	}
	return ""
}

// generateTraceID generates a unique trace ID
func generateTraceID() string {
	return fmt.Sprintf("%016x%016x", time.Now().UnixNano(), time.Now().UnixNano()%1000000)
}

// generateSpanID generates a unique span ID
func generateSpanID() string {
	return fmt.Sprintf("%016x", time.Now().UnixNano())
}

// exportToBackend exports spans to the configured tracing backend
func (t *Tracer) exportToBackend(spans []*Span) error {
	if t.backend == nil {
		logger.Debug("No tracing backend configured, skipping export of %d spans", len(spans))
		return nil
	}

	ctx := context.Background()
	return t.backend.Export(ctx, spans)
}
