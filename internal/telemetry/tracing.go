package telemetry

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// Tracer manages distributed tracing
type Tracer struct {
	config *ObservabilityConfig
	spans  map[string]*Span
	mu     sync.RWMutex
}

// Span represents a tracing span
type Span struct {
	TraceID    string                 `json:"trace_id"`
	SpanID     string                 `json:"span_id"`
	ParentID   string                 `json:"parent_id,omitempty"`
	name       string                 `json:"name"`
	StartTime  time.Time              `json:"start_time"`
	EndTime    *time.Time             `json:"end_time,omitempty"`
	Duration   *time.Duration         `json:"duration,omitempty"`
	Attributes map[string]interface{} `json:"attributes"`
	Events     []SpanEvent            `json:"events"`
	Status     SpanStatus             `json:"status"`
	mu         sync.RWMutex
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
		TraceID:    traceID,
		SpanID:     spanID,
		ParentID:   parentID,
		name:       name,
		StartTime:  time.Now(),
		Attributes: make(map[string]interface{}),
		Events:     make([]SpanEvent, 0),
		Status:     SpanStatus{Code: SpanStatusUnset},
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
		// TODO: Export to tracing backend
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
		"span_name": s.name,
		"trace_id":  s.TraceID,
	})

	logger.Debug("Span finished: %s (trace: %s, duration: %v)", s.name, s.TraceID, duration)
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