package telemetry

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// JaegerBackend implements Backend for Jaeger
type JaegerBackend struct {
	config     Config
	httpClient *http.Client
	endpoint   string
}

// NewJaegerBackend creates a new Jaeger tracing backend
func NewJaegerBackend(config Config) (Backend, error) {
	if config.Endpoint == "" {
		config.Endpoint = "http://localhost:14268/api/traces"
	}
	if config.ServiceName == "" {
		config.ServiceName = "arxos"
	}

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	return &JaegerBackend{
		config:     config,
		httpClient: client,
		endpoint:   config.Endpoint,
	}, nil
}

// Export exports spans to Jaeger
func (b *JaegerBackend) Export(ctx context.Context, spans []*Span) error {
	if len(spans) == 0 {
		return nil
	}

	// Convert our spans to Jaeger format
	jaegerSpans := make([]JaegerSpan, 0, len(spans))
	for _, span := range spans {
		jaegerSpan := b.convertToJaegerSpan(span)
		jaegerSpans = append(jaegerSpans, jaegerSpan)
	}

	// Create Jaeger batch
	batch := JaegerBatch{
		Process: JaegerProcess{
			ServiceName: b.config.ServiceName,
			Tags: []JaegerTag{
				{Key: "service.name", Type: "string", Value: b.config.ServiceName},
				{Key: "service.version", Type: "string", Value: "1.0.0"},
			},
		},
		Spans: jaegerSpans,
	}

	// Marshal to JSON
	payload, err := json.Marshal(batch)
	if err != nil {
		return fmt.Errorf("failed to marshal Jaeger batch: %w", err)
	}

	// Send to Jaeger
	req, err := http.NewRequestWithContext(ctx, "POST", b.endpoint,
		http.NoBody)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Body = http.NoBody

	// Set the payload in the request body
	req.Body = http.NoBody
	req.GetBody = func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewReader(payload)), nil
	}
	req.ContentLength = int64(len(payload))

	resp, err := b.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send spans to Jaeger: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("Jaeger returned error status: %d", resp.StatusCode)
	}

	logger.Debug("Successfully exported %d spans to Jaeger", len(spans))
	return nil
}

// Close closes the Jaeger backend
func (b *JaegerBackend) Close() error {
	return nil
}

// convertToJaegerSpan converts our Span to Jaeger format
func (b *JaegerBackend) convertToJaegerSpan(span *Span) JaegerSpan {
	jaegerSpan := JaegerSpan{
		TraceID:       span.TraceID,
		SpanID:        span.SpanID,
		OperationName: span.Operation,
		StartTime:     span.StartTime.UnixNano() / 1000, // Convert to microseconds
		Duration:      int64(span.Duration.Microseconds()),
		Tags:          make([]JaegerTag, 0),
		Logs:          make([]JaegerLog, 0),
	}

	// Add parent span ID if exists
	if span.ParentID != "" {
		jaegerSpan.References = []JaegerReference{
			{
				RefType: "CHILD_OF",
				TraceID: span.TraceID,
				SpanID:  span.ParentID,
			},
		}
	}

	// Convert tags
	for key, value := range span.Tags {
		tag := JaegerTag{
			Key:   key,
			Type:  b.getTagType(value),
			Value: value,
		}
		jaegerSpan.Tags = append(jaegerSpan.Tags, tag)
	}

	// Convert logs
	for _, log := range span.Logs {
		jaegerLog := JaegerLog{
			Timestamp: log.Timestamp.UnixNano() / 1000, // Convert to microseconds
			Fields:    make([]JaegerTag, 0),
		}

		for key, value := range log.Fields {
			field := JaegerTag{
				Key:   key,
				Type:  b.getTagType(value),
				Value: value,
			}
			jaegerLog.Fields = append(jaegerLog.Fields, field)
		}

		jaegerSpan.Logs = append(jaegerSpan.Logs, jaegerLog)
	}

	return jaegerSpan
}

// getTagType determines the Jaeger tag type from the value
func (b *JaegerBackend) getTagType(value interface{}) string {
	switch value.(type) {
	case string:
		return "string"
	case int, int32, int64:
		return "int64"
	case float32, float64:
		return "float64"
	case bool:
		return "bool"
	default:
		return "string"
	}
}

// Jaeger data structures
type JaegerBatch struct {
	Process JaegerProcess `json:"process"`
	Spans   []JaegerSpan  `json:"spans"`
}

type JaegerProcess struct {
	ServiceName string      `json:"serviceName"`
	Tags        []JaegerTag `json:"tags"`
}

type JaegerSpan struct {
	TraceID       string            `json:"traceID"`
	SpanID        string            `json:"spanID"`
	OperationName string            `json:"operationName"`
	References    []JaegerReference `json:"references,omitempty"`
	StartTime     int64             `json:"startTime"`
	Duration      int64             `json:"duration"`
	Tags          []JaegerTag       `json:"tags"`
	Logs          []JaegerLog       `json:"logs"`
}

type JaegerReference struct {
	RefType string `json:"refType"`
	TraceID string `json:"traceID"`
	SpanID  string `json:"spanID"`
}

type JaegerTag struct {
	Key   string      `json:"key"`
	Type  string      `json:"type"`
	Value interface{} `json:"value"`
}

type JaegerLog struct {
	Timestamp int64       `json:"timestamp"`
	Fields    []JaegerTag `json:"fields"`
}
