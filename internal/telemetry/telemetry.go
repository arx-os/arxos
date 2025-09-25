package telemetry

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"runtime"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
)

// Collector collects and sends telemetry data
type Collector struct {
	config   *config.TelemetryConfig
	client   *http.Client
	queue    []Event
	mu       sync.Mutex
	shutdown chan struct{}
	wg       sync.WaitGroup
}

// Event represents a telemetry event
type Event struct {
	Type       string                 `json:"type"`
	Name       string                 `json:"name"`
	Timestamp  time.Time              `json:"timestamp"`
	Properties map[string]interface{} `json:"properties"`
	Metrics    map[string]float64     `json:"metrics"`
	Context    *Context               `json:"context"`
}

// Context contains contextual information for events
type Context struct {
	SessionID   string `json:"session_id"`
	UserID      string `json:"user_id,omitempty"`
	AnonymousID string `json:"anonymous_id"`
	Version     string `json:"version"`
	OS          string `json:"os"`
	Arch        string `json:"arch"`
	GoVersion   string `json:"go_version"`
}

var (
	// Global collector instance
	globalCollector *Collector
	once            sync.Once
)

// ObservabilityConfig extends the base telemetry config
type ObservabilityConfig struct {
	*config.TelemetryConfig
	ServiceName string
	Environment string
	Metrics     struct {
		Enabled  bool
		Endpoint string
		Port     int
	}
	Tracing struct {
		Enabled    bool
		Endpoint   string
		SampleRate float64
	}
	Logging struct {
		Level          string
		Format         string
		CorrelationIDs bool
	}
}

// ExtendedTelemetry provides enhanced telemetry services
type ExtendedTelemetry struct {
	config  *ObservabilityConfig
	metrics *MetricsCollector
	tracer  *Tracer
	logger  *StructuredLogger
	mu      sync.RWMutex
}

var (
	extendedInstance *ExtendedTelemetry
	extendedOnce     sync.Once
)

// InitializeExtended sets up enhanced telemetry services
func InitializeExtended(cfg *config.TelemetryConfig) error {
	var err error
	extendedOnce.Do(func() {
		obsConfig := &ObservabilityConfig{
			TelemetryConfig: cfg,
			ServiceName:     "arxos",
			Environment:     "development",
		}

		// Set defaults
		obsConfig.Metrics.Enabled = true
		obsConfig.Metrics.Endpoint = "/metrics"
		obsConfig.Metrics.Port = 9090

		obsConfig.Tracing.Enabled = true
		obsConfig.Tracing.SampleRate = 0.1

		obsConfig.Logging.Level = "info"
		obsConfig.Logging.Format = "json"
		obsConfig.Logging.CorrelationIDs = true

		extendedInstance = &ExtendedTelemetry{
			config: obsConfig,
		}

		if cfg != nil && cfg.Enabled {
			// Initialize metrics collector
			if obsConfig.Metrics.Enabled {
				extendedInstance.metrics = NewMetricsCollector(obsConfig)
			}

			// Initialize tracer
			if obsConfig.Tracing.Enabled {
				extendedInstance.tracer = NewTracer(obsConfig)
			}

			// Initialize structured logger
			extendedInstance.logger = NewStructuredLogger(obsConfig)

			logger.Info("Enhanced telemetry initialized - metrics: %v, tracing: %v",
				obsConfig.Metrics.Enabled, obsConfig.Tracing.Enabled)
		} else {
			logger.Info("Enhanced telemetry disabled")
		}
	})

	return err
}

// Initialize sets up the global telemetry collector
func Initialize(cfg *config.TelemetryConfig) {
	once.Do(func() {
		if cfg == nil || !cfg.Enabled {
			logger.Debug("Telemetry disabled")
			return
		}

		globalCollector = &Collector{
			config: cfg,
			client: &http.Client{
				Timeout: 5 * time.Second,
			},
			queue:    make([]Event, 0, 100),
			shutdown: make(chan struct{}),
		}

		// Start background sender
		globalCollector.wg.Add(1)
		go globalCollector.backgroundSender()

		logger.Debug("Telemetry initialized")
	})
}

// Shutdown stops the telemetry collector
func Shutdown() {
	if globalCollector != nil {
		close(globalCollector.shutdown)
		globalCollector.wg.Wait()
		globalCollector.flush()
	}
}

// Track records a telemetry event
func Track(eventName string, properties map[string]interface{}) {
	if globalCollector == nil {
		return
	}

	event := Event{
		Type:       "track",
		Name:       eventName,
		Timestamp:  time.Now(),
		Properties: properties,
		Context:    getContext(),
	}

	globalCollector.enqueue(event)
}

// Metric records a metric event
func Metric(metricName string, value float64, properties map[string]interface{}) {
	if globalCollector == nil {
		return
	}

	event := Event{
		Type:       "metric",
		Name:       metricName,
		Timestamp:  time.Now(),
		Properties: properties,
		Metrics: map[string]float64{
			metricName: value,
		},
		Context: getContext(),
	}

	globalCollector.enqueue(event)
}

// TrackError records an error event
func TrackError(errName string, err error, properties map[string]interface{}) {
	if globalCollector == nil {
		return
	}

	if properties == nil {
		properties = make(map[string]interface{})
	}
	properties["error_message"] = err.Error()

	event := Event{
		Type:       "error",
		Name:       errName,
		Timestamp:  time.Now(),
		Properties: properties,
		Context:    getContext(),
	}

	globalCollector.enqueue(event)
}

// Command records a command execution
func Command(cmdName string, args []string, duration time.Duration, success bool) {
	if globalCollector == nil {
		return
	}

	properties := map[string]interface{}{
		"command":  cmdName,
		"args":     args,
		"duration": duration.Milliseconds(),
		"success":  success,
	}

	Track("command_executed", properties)
	Metric("command_duration_ms", float64(duration.Milliseconds()), properties)
}

// enqueue adds an event to the queue
func (c *Collector) enqueue(event Event) {
	// Apply sampling rate
	if c.config.SampleRate < 1.0 {
		// Simple random sampling
		if time.Now().UnixNano()%100 > int64(c.config.SampleRate*100) {
			return
		}
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	c.queue = append(c.queue, event)

	// Send immediately if queue is full
	if len(c.queue) >= 100 {
		go c.flush()
	}
}

// backgroundSender periodically sends queued events
func (c *Collector) backgroundSender() {
	defer c.wg.Done()

	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.flush()
		case <-c.shutdown:
			return
		}
	}
}

// flush sends all queued events
func (c *Collector) flush() {
	c.mu.Lock()
	if len(c.queue) == 0 {
		c.mu.Unlock()
		return
	}

	events := c.queue
	c.queue = make([]Event, 0, 100)
	c.mu.Unlock()

	// Send events in batches
	for i := 0; i < len(events); i += 50 {
		end := i + 50
		if end > len(events) {
			end = len(events)
		}
		batch := events[i:end]

		if err := c.sendBatch(batch); err != nil {
			if c.config.Debug {
				logger.Error("Failed to send telemetry batch: %v", err)
			}
		}
	}
}

// sendBatch sends a batch of events to the telemetry endpoint
func (c *Collector) sendBatch(events []Event) error {
	payload := map[string]interface{}{
		"events":    events,
		"timestamp": time.Now().Unix(),
	}

	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal events: %w", err)
	}

	req, err := http.NewRequest("POST", c.config.Endpoint+"/events", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "ArxOS-Telemetry/1.0")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	req = req.WithContext(ctx)

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("telemetry endpoint returned status %d", resp.StatusCode)
	}

	return nil
}

// getContext returns the current context
func getContext() *Context {
	if globalCollector == nil {
		return nil
	}

	return &Context{
		SessionID:   getSessionID(),
		AnonymousID: globalCollector.config.AnonymousID,
		Version:     getVersionFromBuildInfo(),
		OS:          runtime.GOOS,
		Arch:        runtime.GOARCH,
		GoVersion:   runtime.Version(),
	}
}

var sessionID string

// getSessionID returns a consistent session ID
func getSessionID() string {
	if sessionID == "" {
		sessionID = fmt.Sprintf("%d", time.Now().UnixNano())
	}
	return sessionID
}

// Timer tracks the duration of an operation
type Timer struct {
	name       string
	properties map[string]interface{}
	startTime  time.Time
}

// StartTimer starts a new timer
func StartTimer(name string, properties map[string]interface{}) *Timer {
	return &Timer{
		name:       name,
		properties: properties,
		startTime:  time.Now(),
	}
}

// Stop stops the timer and records the duration
func (t *Timer) Stop() {
	duration := time.Since(t.startTime)
	Metric(t.name+"_duration_ms", float64(duration.Milliseconds()), t.properties)
}

// Counter tracks a count metric
type Counter struct {
	name       string
	value      float64
	properties map[string]interface{}
	mu         sync.Mutex
}

// NewCounter creates a new counter
func NewCounter(name string, properties map[string]interface{}) *Counter {
	return &Counter{
		name:       name,
		properties: properties,
	}
}

// Increment increments the counter
func (c *Counter) Increment() {
	c.mu.Lock()
	c.value++
	c.mu.Unlock()
}

// Add adds to the counter
func (c *Counter) Add(delta float64) {
	c.mu.Lock()
	c.value += delta
	c.mu.Unlock()
}

// Flush sends the counter value
func (c *Counter) Flush() {
	c.mu.Lock()
	value := c.value
	c.value = 0
	c.mu.Unlock()

	if value > 0 {
		Metric(c.name, value, c.properties)
	}
}

// GetExtendedInstance returns the extended telemetry instance
func GetExtendedInstance() *ExtendedTelemetry {
	return extendedInstance
}

// StartDashboard starts the observability dashboard
func StartDashboard() error {
	if extendedInstance == nil || extendedInstance.config == nil {
		return fmt.Errorf("telemetry not initialized")
	}

	dashboard := NewDashboard(extendedInstance.config)
	return dashboard.Start()
}

// GetMetricsCollector returns the metrics collector instance
func GetMetricsCollector() *MetricsCollector {
	if extendedInstance != nil {
		return extendedInstance.metrics
	}
	return nil
}

// GetTracer returns the tracer instance
func GetTracer() *Tracer {
	if extendedInstance != nil {
		return extendedInstance.tracer
	}
	return nil
}

// GetStructuredLogger returns the structured logger instance
func GetStructuredLogger() *StructuredLogger {
	if extendedInstance != nil {
		return extendedInstance.logger
	}
	return nil
}

// HTTPMiddleware provides observability for HTTP requests
func HTTPMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Add correlation ID to context
		ctx := AddCorrelationID(r.Context())
		r = r.WithContext(ctx)

		// Start span if tracing is enabled
		if extendedInstance != nil && extendedInstance.tracer != nil {
			ctx, span := extendedInstance.tracer.StartSpan(ctx, fmt.Sprintf("HTTP %s %s", r.Method, r.URL.Path))
			defer span.Finish()

			// Add request attributes to span
			span.SetAttribute("http.method", r.Method)
			span.SetAttribute("http.url", r.URL.String())
			span.SetAttribute("http.user_agent", r.Header.Get("User-Agent"))

			r = r.WithContext(ctx)
		}

		// Wrap response writer to capture status code
		wrapped := &responseWriter{ResponseWriter: w}

		// Process request
		next.ServeHTTP(wrapped, r)

		// Record metrics if metrics collector is available
		if extendedInstance != nil && extendedInstance.metrics != nil {
			duration := time.Since(start).Seconds()
			tags := map[string]string{
				"method": r.Method,
				"path":   r.URL.Path,
				"status": fmt.Sprintf("%d", wrapped.statusCode),
			}

			extendedInstance.metrics.IncrementCounter("http_requests_total", tags)
			extendedInstance.metrics.RecordHistogram("http_request_duration_seconds", duration, tags)
		}

		// Log request with context
		InfoWithContext(ctx, "HTTP %s %s %d %v",
			r.Method, r.URL.Path, wrapped.statusCode, time.Since(start))
	})
}

// responseWriter wraps http.ResponseWriter to capture metrics
type responseWriter struct {
	http.ResponseWriter
	statusCode   int
	bytesWritten int64
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	if rw.statusCode == 0 {
		rw.statusCode = 200
	}
	n, err := rw.ResponseWriter.Write(b)
	rw.bytesWritten += int64(n)
	return n, err
}

// getVersionFromBuildInfo gets the version from build info or environment
func getVersionFromBuildInfo() string {
	// Try to get from environment variable first
	if version := os.Getenv("ARXOS_VERSION"); version != "" {
		return version
	}

	// Try to get from build info
	// In a real implementation, this would read from build info
	// For now, return a default version
	return "0.1.0"
}
