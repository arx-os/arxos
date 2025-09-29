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

// ZipkinBackend implements Backend for Zipkin
type ZipkinBackend struct {
	config     Config
	httpClient *http.Client
	endpoint   string
}

// NewZipkinBackend creates a new Zipkin tracing backend
func NewZipkinBackend(config Config) (Backend, error) {
	if config.Endpoint == "" {
		config.Endpoint = "http://localhost:9411/api/v2/spans"
	}
	if config.ServiceName == "" {
		config.ServiceName = "arxos"
	}

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	return &ZipkinBackend{
		config:     config,
		httpClient: client,
		endpoint:   config.Endpoint,
	}, nil
}

// Export exports spans to Zipkin
func (b *ZipkinBackend) Export(ctx context.Context, spans []*Span) error {
	if len(spans) == 0 {
		return nil
	}

	// Convert our spans to Zipkin format
	zipkinSpans := make([]ZipkinSpan, 0, len(spans))
	for _, span := range spans {
		zipkinSpan := b.convertToZipkinSpan(span)
		zipkinSpans = append(zipkinSpans, zipkinSpan)
	}

	// Marshal to JSON
	payload, err := json.Marshal(zipkinSpans)
	if err != nil {
		return fmt.Errorf("failed to marshal Zipkin spans: %w", err)
	}

	// Send to Zipkin
	req, err := http.NewRequestWithContext(ctx, "POST", b.endpoint,
		http.NoBody)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.GetBody = func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewReader(payload)), nil
	}
	req.ContentLength = int64(len(payload))

	resp, err := b.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send spans to Zipkin: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("Zipkin returned error status: %d", resp.StatusCode)
	}

	logger.Debug("Successfully exported %d spans to Zipkin", len(spans))
	return nil
}

// Close closes the Zipkin backend
func (b *ZipkinBackend) Close() error {
	return nil
}

// convertToZipkinSpan converts our Span to Zipkin format
func (b *ZipkinBackend) convertToZipkinSpan(span *Span) ZipkinSpan {
	zipkinSpan := ZipkinSpan{
		TraceID:   span.TraceID,
		ID:        span.SpanID,
		Name:      span.Operation,
		Timestamp: span.StartTime.UnixNano() / 1000, // Convert to microseconds
		Duration:  int64(span.Duration.Microseconds()),
		LocalEndpoint: ZipkinEndpoint{
			ServiceName: b.config.ServiceName,
		},
		Tags:        make(map[string]string),
		Annotations: make([]ZipkinAnnotation, 0),
	}

	// Add parent span ID if exists
	if span.ParentID != "" {
		zipkinSpan.ParentID = span.ParentID
	}

	// Convert tags (Zipkin only supports string values)
	for key, value := range span.Tags {
		if strValue, ok := value.(string); ok {
			zipkinSpan.Tags[key] = strValue
		} else {
			zipkinSpan.Tags[key] = fmt.Sprintf("%v", value)
		}
	}

	// Convert logs to annotations
	for _, log := range span.Logs {
		annotation := ZipkinAnnotation{
			Timestamp: log.Timestamp.UnixNano() / 1000, // Convert to microseconds
			Value:     fmt.Sprintf("%v", log.Fields),
		}
		zipkinSpan.Annotations = append(zipkinSpan.Annotations, annotation)
	}

	return zipkinSpan
}

// Zipkin data structures
type ZipkinSpan struct {
	TraceID       string             `json:"traceId"`
	ID            string             `json:"id"`
	ParentID      string             `json:"parentId,omitempty"`
	Name          string             `json:"name"`
	Timestamp     int64              `json:"timestamp"`
	Duration      int64              `json:"duration"`
	LocalEndpoint ZipkinEndpoint     `json:"localEndpoint"`
	Tags          map[string]string  `json:"tags"`
	Annotations   []ZipkinAnnotation `json:"annotations"`
}

type ZipkinEndpoint struct {
	ServiceName string `json:"serviceName"`
}

type ZipkinAnnotation struct {
	Timestamp int64  `json:"timestamp"`
	Value     string `json:"value"`
}
