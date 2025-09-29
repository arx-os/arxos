package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Trace represents a distributed trace
type Trace struct {
	ID        string                 `json:"id"`
	StartTime time.Time              `json:"start_time"`
	EndTime   time.Time              `json:"end_time"`
	Duration  time.Duration          `json:"duration"`
	Tags      map[string]string      `json:"tags"`
	Spans     []*Span                `json:"spans"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// Span represents a span within a trace
type Span struct {
	ID        string                 `json:"id"`
	TraceID   string                 `json:"trace_id"`
	ParentID  string                 `json:"parent_id,omitempty"`
	Name      string                 `json:"name"`
	StartTime time.Time              `json:"start_time"`
	EndTime   time.Time              `json:"end_time"`
	Duration  time.Duration          `json:"duration"`
	Tags      map[string]string      `json:"tags"`
	Logs      []*LogEntry            `json:"logs"`
	Error     error                  `json:"error,omitempty"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// LogEntry represents a log entry within a span
type LogEntry struct {
	Timestamp time.Time              `json:"timestamp"`
	Level     string                 `json:"level"`
	Message   string                 `json:"message"`
	Fields    map[string]interface{} `json:"fields"`
}

// Tracer manages distributed tracing
type Tracer struct {
	mu     sync.RWMutex
	traces map[string]*Trace
	spans  map[string]*Span
}

// NewTracer creates a new tracer
func NewTracer() *Tracer {
	return &Tracer{
		traces: make(map[string]*Trace),
		spans:  make(map[string]*Span),
	}
}

// StartTrace starts a new trace
func (t *Tracer) StartTrace(id, name string, tags map[string]string) *Trace {
	t.mu.Lock()
	defer t.mu.Unlock()

	trace := &Trace{
		ID:        id,
		StartTime: time.Now(),
		Tags:      tags,
		Spans:     make([]*Span, 0),
		Metadata:  make(map[string]interface{}),
	}

	t.traces[id] = trace
	logger.Debug("Started trace: %s", id)
	return trace
}

// EndTrace ends a trace
func (t *Tracer) EndTrace(id string) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	trace, exists := t.traces[id]
	if !exists {
		return fmt.Errorf("trace %s not found", id)
	}

	trace.EndTime = time.Now()
	trace.Duration = trace.EndTime.Sub(trace.StartTime)

	logger.Debug("Ended trace: %s (duration: %v)", id, trace.Duration)
	return nil
}

// StartSpan starts a new span within a trace
func (t *Tracer) StartSpan(traceID, spanID, name string, parentID string, tags map[string]string) *Span {
	t.mu.Lock()
	defer t.mu.Unlock()

	span := &Span{
		ID:        spanID,
		TraceID:   traceID,
		ParentID:  parentID,
		Name:      name,
		StartTime: time.Now(),
		Tags:      tags,
		Logs:      make([]*LogEntry, 0),
		Metadata:  make(map[string]interface{}),
	}

	t.spans[spanID] = span

	// Add span to trace
	if trace, exists := t.traces[traceID]; exists {
		trace.Spans = append(trace.Spans, span)
	}

	logger.Debug("Started span: %s in trace: %s", spanID, traceID)
	return span
}

// EndSpan ends a span
func (t *Tracer) EndSpan(spanID string, err error) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	span, exists := t.spans[spanID]
	if !exists {
		return fmt.Errorf("span %s not found", spanID)
	}

	span.EndTime = time.Now()
	span.Duration = span.EndTime.Sub(span.StartTime)
	span.Error = err

	logger.Debug("Ended span: %s (duration: %v)", spanID, span.Duration)
	return nil
}

// AddLog adds a log entry to a span
func (t *Tracer) AddLog(spanID string, level, message string, fields map[string]interface{}) error {
	t.mu.RLock()
	defer t.mu.RUnlock()

	span, exists := t.spans[spanID]
	if !exists {
		return fmt.Errorf("span %s not found", spanID)
	}

	logEntry := &LogEntry{
		Timestamp: time.Now(),
		Level:     level,
		Message:   message,
		Fields:    fields,
	}

	span.Logs = append(span.Logs, logEntry)
	return nil
}

// GetTrace retrieves a trace by ID
func (t *Tracer) GetTrace(id string) (*Trace, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()

	trace, exists := t.traces[id]
	return trace, exists
}

// GetSpan retrieves a span by ID
func (t *Tracer) GetSpan(id string) (*Span, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()

	span, exists := t.spans[id]
	return span, exists
}

// GetAllTraces returns all traces
func (t *Tracer) GetAllTraces() map[string]*Trace {
	t.mu.RLock()
	defer t.mu.RUnlock()

	traces := make(map[string]*Trace)
	for id, trace := range t.traces {
		traces[id] = trace
	}
	return traces
}

// ClearTraces clears all traces older than the specified duration
func (t *Tracer) ClearTraces(olderThan time.Duration) {
	t.mu.Lock()
	defer t.mu.Unlock()

	cutoff := time.Now().Add(-olderThan)

	for id, trace := range t.traces {
		if trace.StartTime.Before(cutoff) {
			delete(t.traces, id)
		}
	}

	for id, span := range t.spans {
		if span.StartTime.Before(cutoff) {
			delete(t.spans, id)
		}
	}
}

// TraceContext provides context for tracing
type TraceContext struct {
	TraceID string
	SpanID  string
}

// ContextKey is the key for trace context
type ContextKey string

const TraceContextKey ContextKey = "trace_context"

// WithTraceContext adds trace context to a context
func WithTraceContext(ctx context.Context, traceID, spanID string) context.Context {
	return context.WithValue(ctx, TraceContextKey, &TraceContext{
		TraceID: traceID,
		SpanID:  spanID,
	})
}

// GetTraceContext retrieves trace context from a context
func GetTraceContext(ctx context.Context) (*TraceContext, bool) {
	traceCtx, ok := ctx.Value(TraceContextKey).(*TraceContext)
	return traceCtx, ok
}

// TraceFunction traces a function execution
func TraceFunction(tracer *Tracer, traceID, spanID, functionName string, fn func() error) error {
	tracer.StartSpan(traceID, spanID, functionName, "", nil)
	defer tracer.EndSpan(spanID, nil)

	err := fn()
	if err != nil {
		tracer.EndSpan(spanID, err)
		return err
	}

	return nil
}

// TraceFunctionWithContext traces a function execution with context
func TraceFunctionWithContext(ctx context.Context, tracer *Tracer, spanID, functionName string, fn func() error) error {
	traceCtx, ok := GetTraceContext(ctx)
	if !ok {
		// No trace context, execute function normally
		return fn()
	}

	tracer.StartSpan(traceCtx.TraceID, spanID, functionName, traceCtx.SpanID, nil)
	defer tracer.EndSpan(spanID, nil)

	err := fn()
	if err != nil {
		tracer.EndSpan(spanID, err)
		return err
	}

	return nil
}

// Global tracer instance
var globalTracer *Tracer
var tracerOnce sync.Once

// GetGlobalTracer returns the global tracer instance
func GetGlobalTracer() *Tracer {
	tracerOnce.Do(func() {
		globalTracer = NewTracer()
	})
	return globalTracer
}

// Convenience functions for global tracing
func StartTrace(id, name string, tags map[string]string) *Trace {
	return GetGlobalTracer().StartTrace(id, name, tags)
}

func EndTrace(id string) error {
	return GetGlobalTracer().EndTrace(id)
}

func StartSpan(traceID, spanID, name string, parentID string, tags map[string]string) *Span {
	return GetGlobalTracer().StartSpan(traceID, spanID, name, parentID, tags)
}

func EndSpan(spanID string, err error) error {
	return GetGlobalTracer().EndSpan(spanID, err)
}

func AddLog(spanID string, level, message string, fields map[string]interface{}) error {
	return GetGlobalTracer().AddLog(spanID, level, message, fields)
}
