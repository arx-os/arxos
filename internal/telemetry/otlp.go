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

// OTLPBackend implements Backend for OpenTelemetry Protocol
type OTLPBackend struct {
	config     Config
	httpClient *http.Client
	endpoint   string
}

// NewOTLPBackend creates a new OTLP tracing backend
func NewOTLPBackend(config Config) (Backend, error) {
	if config.Endpoint == "" {
		config.Endpoint = "http://localhost:4317/v1/traces"
	}
	if config.ServiceName == "" {
		config.ServiceName = "arxos"
	}

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	return &OTLPBackend{
		config:     config,
		httpClient: client,
		endpoint:   config.Endpoint,
	}, nil
}

// Export exports spans via OTLP
func (b *OTLPBackend) Export(ctx context.Context, spans []*Span) error {
	if len(spans) == 0 {
		return nil
	}

	// Convert our spans to OTLP format
	otlpSpans := make([]OTLPSpan, 0, len(spans))
	for _, span := range spans {
		otlpSpan := b.convertToOTLPSpan(span)
		otlpSpans = append(otlpSpans, otlpSpan)
	}

	// Create OTLP request
	request := OTLPRequest{
		ResourceSpans: []OTLPResourceSpan{
			{
				Resource: OTLPResource{
					Attributes: []OTLPAttribute{
						{
							Key:   "service.name",
							Value: OTLPValue{StringValue: b.config.ServiceName},
						},
						{
							Key:   "service.version",
							Value: OTLPValue{StringValue: "1.0.0"},
						},
					},
				},
				ScopeSpans: []OTLPScopeSpan{
					{
						Spans: otlpSpans,
					},
				},
			},
		},
	}

	// Marshal to JSON
	payload, err := json.Marshal(request)
	if err != nil {
		return fmt.Errorf("failed to marshal OTLP request: %w", err)
	}

	// Send to OTLP endpoint
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
		return fmt.Errorf("failed to send spans via OTLP: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("OTLP endpoint returned error status: %d", resp.StatusCode)
	}

	logger.Debug("Successfully exported %d spans via OTLP", len(spans))
	return nil
}

// Close closes the OTLP backend
func (b *OTLPBackend) Close() error {
	return nil
}

// convertToOTLPSpan converts our Span to OTLP format
func (b *OTLPBackend) convertToOTLPSpan(span *Span) OTLPSpan {
	otlpSpan := OTLPSpan{
		TraceID:           span.TraceID,
		SpanID:            span.SpanID,
		Name:              span.OperationName,
		StartTimeUnixNano: span.StartTime.UnixNano(),
		EndTimeUnixNano:   span.StartTime.Add(*span.Duration).UnixNano(),
		Attributes:        make([]OTLPAttribute, 0),
		Events:            make([]OTLPEvent, 0),
		Status: OTLPStatus{
			Code: OTLPStatusCode(span.Status.Code),
		},
	}

	// Add parent span ID if exists
	if span.ParentID != "" {
		otlpSpan.ParentSpanID = span.ParentID
	}

	// Convert tags to attributes
	for key, value := range span.Tags {
		attr := OTLPAttribute{
			Key:   key,
			Value: b.convertToOTLPValue(value),
		}
		otlpSpan.Attributes = append(otlpSpan.Attributes, attr)
	}

	// Convert logs to events
	for _, log := range span.Logs {
		event := OTLPEvent{
			TimeUnixNano: log.Timestamp.UnixNano(),
			Name:         "log",
			Attributes:   make([]OTLPAttribute, 0),
		}

		for key, value := range log.Fields {
			attr := OTLPAttribute{
				Key:   key,
				Value: b.convertToOTLPValue(value),
			}
			event.Attributes = append(event.Attributes, attr)
		}

		otlpSpan.Events = append(otlpSpan.Events, event)
	}

	return otlpSpan
}

// convertToOTLPValue converts a value to OTLP format
func (b *OTLPBackend) convertToOTLPValue(value interface{}) OTLPValue {
	switch v := value.(type) {
	case string:
		return OTLPValue{StringValue: v}
	case int, int32, int64:
		return OTLPValue{IntValue: fmt.Sprintf("%d", v)}
	case float32, float64:
		return OTLPValue{DoubleValue: fmt.Sprintf("%f", v)}
	case bool:
		return OTLPValue{BoolValue: v}
	default:
		return OTLPValue{StringValue: fmt.Sprintf("%v", v)}
	}
}

// OTLP data structures
type OTLPRequest struct {
	ResourceSpans []OTLPResourceSpan `json:"resourceSpans"`
}

type OTLPResourceSpan struct {
	Resource   OTLPResource    `json:"resource"`
	ScopeSpans []OTLPScopeSpan `json:"scopeSpans"`
}

type OTLPResource struct {
	Attributes []OTLPAttribute `json:"attributes"`
}

type OTLPScopeSpan struct {
	Spans []OTLPSpan `json:"spans"`
}

type OTLPSpan struct {
	TraceID           string          `json:"traceId"`
	SpanID            string          `json:"spanId"`
	ParentSpanID      string          `json:"parentSpanId,omitempty"`
	Name              string          `json:"name"`
	StartTimeUnixNano int64           `json:"startTimeUnixNano"`
	EndTimeUnixNano   int64           `json:"endTimeUnixNano"`
	Attributes        []OTLPAttribute `json:"attributes"`
	Events            []OTLPEvent     `json:"events"`
	Status            OTLPStatus      `json:"status"`
}

type OTLPAttribute struct {
	Key   string    `json:"key"`
	Value OTLPValue `json:"value"`
}

type OTLPValue struct {
	StringValue string `json:"stringValue,omitempty"`
	IntValue    string `json:"intValue,omitempty"`
	DoubleValue string `json:"doubleValue,omitempty"`
	BoolValue   bool   `json:"boolValue,omitempty"`
}

type OTLPEvent struct {
	TimeUnixNano int64           `json:"timeUnixNano"`
	Name         string          `json:"name"`
	Attributes   []OTLPAttribute `json:"attributes"`
}

type OTLPStatus struct {
	Code OTLPStatusCode `json:"code"`
}

type OTLPStatusCode int

const (
	OTLPStatusCodeUnset OTLPStatusCode = 0
	OTLPStatusCodeOK    OTLPStatusCode = 1
	OTLPStatusCodeError OTLPStatusCode = 2
)
