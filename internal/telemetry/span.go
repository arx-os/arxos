package telemetry

import (
	"context"
	"fmt"
	"time"
)

// Span represents a distributed tracing span
type Span struct {
	TraceID   string                 `json:"trace_id"`
	SpanID    string                 `json:"span_id"`
	ParentID  string                 `json:"parent_id,omitempty"`
	Operation string                 `json:"operation"`
	Service   string                 `json:"service"`
	StartTime time.Time              `json:"start_time"`
	EndTime   time.Time              `json:"end_time,omitempty"`
	Duration  time.Duration          `json:"duration,omitempty"`
	Tags      map[string]interface{} `json:"tags"`
	Logs      []SpanLog              `json:"logs,omitempty"`
	Status    SpanStatus             `json:"status"`
	Context   context.Context        `json:"-"`
}

// SpanLog represents a log entry within a span
type SpanLog struct {
	Timestamp time.Time              `json:"timestamp"`
	Level     string                 `json:"level"`
	Message   string                 `json:"message"`
	Fields    map[string]interface{} `json:"fields,omitempty"`
}

// SpanStatus represents the status of a span
type SpanStatus int

const (
	SpanStatusUnknown SpanStatus = iota
	SpanStatusOK
	SpanStatusError
	SpanStatusCancelled
)

// Finish finishes the span
func (s *Span) Finish() {
	s.EndTime = time.Now()
	s.Duration = s.EndTime.Sub(s.StartTime)
}

// SetAttribute sets an attribute on the span
func (s *Span) SetAttribute(key string, value interface{}) {
	if s.Tags == nil {
		s.Tags = make(map[string]interface{})
	}
	s.Tags[key] = value
}

// AddLog adds a log entry to the span
func (s *Span) AddLog(level, message string, fields map[string]interface{}) {
	log := SpanLog{
		Timestamp: time.Now(),
		Level:     level,
		Message:   message,
		Fields:    fields,
	}
	s.Logs = append(s.Logs, log)
}

// SetStatus sets the status of the span
func (s *Span) SetStatus(status SpanStatus) {
	s.Status = status
}

// SetError sets the span status to error and adds error information
func (s *Span) SetError(err error) {
	s.Status = SpanStatusError
	s.SetAttribute("error", true)
	s.SetAttribute("error.message", err.Error())
}

// GetTraceID returns the trace ID
func (s *Span) GetTraceID() string {
	return s.TraceID
}

// GetSpanID returns the span ID
func (s *Span) GetSpanID() string {
	return s.SpanID
}

// GetParentID returns the parent span ID
func (s *Span) GetParentID() string {
	return s.ParentID
}

// GetOperation returns the operation name
func (s *Span) GetOperation() string {
	return s.Operation
}

// GetService returns the service name
func (s *Span) GetService() string {
	return s.Service
}

// GetStartTime returns the start time
func (s *Span) GetStartTime() time.Time {
	return s.StartTime
}

// GetEndTime returns the end time
func (s *Span) GetEndTime() time.Time {
	return s.EndTime
}

// GetDuration returns the duration
func (s *Span) GetDuration() time.Duration {
	return s.Duration
}

// GetTags returns the tags
func (s *Span) GetTags() map[string]interface{} {
	return s.Tags
}

// GetLogs returns the logs
func (s *Span) GetLogs() []SpanLog {
	return s.Logs
}

// GetStatus returns the status
func (s *Span) GetStatus() SpanStatus {
	return s.Status
}

// GetContext returns the context
func (s *Span) GetContext() context.Context {
	return s.Context
}

// NewSpan creates a new span
func NewSpan(traceID, spanID, operation, service string) *Span {
	return &Span{
		TraceID:   traceID,
		SpanID:    spanID,
		Operation: operation,
		Service:   service,
		StartTime: time.Now(),
		Tags:      make(map[string]interface{}),
		Logs:      make([]SpanLog, 0),
		Status:    SpanStatusOK,
	}
}

// NewChildSpan creates a new child span
func NewChildSpan(parent *Span, operation string) *Span {
	span := NewSpan(parent.TraceID, generateSpanID(), operation, parent.Service)
	span.ParentID = parent.SpanID
	return span
}

// generateSpanID generates a unique span ID
func generateSpanID() string {
	return fmt.Sprintf("%x", time.Now().UnixNano())
}

// generateTraceID generates a unique trace ID
func generateTraceID() string {
	return fmt.Sprintf("%x", time.Now().UnixNano())
}
