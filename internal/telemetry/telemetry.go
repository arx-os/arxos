package telemetry

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"runtime"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/config"
	"github.com/joelpate/arxos/internal/common/logger"
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

// Error records an error event
func Error(errName string, err error, properties map[string]interface{}) {
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
		Version:     "0.1.0", // TODO: Get from build info
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