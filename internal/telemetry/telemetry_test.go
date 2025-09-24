package telemetry

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/config"
)

func TestInitialize(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	// Initialize telemetry
	Initialize(cfg)
	
	// Verify global collector is set
	assert.NotNil(t, globalCollector)
	assert.Equal(t, cfg, globalCollector.config)
}

func TestTrack(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Track an event
	Track("test_event", map[string]interface{}{
		"property1": "value1",
		"property2": 42,
	})

	// Verify event was queued
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 1)
	event := globalCollector.queue[0]
	assert.Equal(t, "test_event", event.Name)
	assert.Equal(t, "value1", event.Properties["property1"])
	assert.Equal(t, 42, event.Properties["property2"])
	globalCollector.mu.Unlock()
}

func TestMetric(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Record a metric
	Metric("test_metric", 123.45, map[string]interface{}{
		"tag": "value",
	})

	// Verify metric was queued
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 1)
	event := globalCollector.queue[0]
	assert.Equal(t, "metric", event.Type)
	assert.Equal(t, "test_metric", event.Name)
	assert.Equal(t, 123.45, event.Metrics["test_metric"])
	assert.Equal(t, "value", event.Properties["tag"])
	globalCollector.mu.Unlock()
}

func TestTrackError(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Track an error
	err := assert.AnError
	TrackError("test_error", err, map[string]interface{}{
		"component": "test",
	})

	// Verify error was queued
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 1)
	event := globalCollector.queue[0]
	assert.Equal(t, "error", event.Type)
	assert.Equal(t, "test_error", event.Name)
	assert.Equal(t, "test", event.Properties["component"])
	assert.Contains(t, event.Properties, "error_message")
	globalCollector.mu.Unlock()
}

func TestCommand(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Track a command
	Command("test_command", []string{"arg1", "arg2"}, 150*time.Millisecond, true)

	// Verify command was queued (Command creates both a track event and a metric event)
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 2)
	
	// Check the track event
	trackEvent := globalCollector.queue[0]
	assert.Equal(t, "track", trackEvent.Type)
	assert.Equal(t, "command_executed", trackEvent.Name)
	assert.Equal(t, []string{"arg1", "arg2"}, trackEvent.Properties["args"])
	assert.Equal(t, true, trackEvent.Properties["success"])
	
	// Check the metric event
	metricEvent := globalCollector.queue[1]
	assert.Equal(t, "metric", metricEvent.Type)
	assert.Equal(t, "command_duration_ms", metricEvent.Name)
	assert.Equal(t, float64(150), metricEvent.Metrics["command_duration_ms"])
	globalCollector.mu.Unlock()
}

func TestCollector_Flush(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com", // Use a dummy endpoint
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Add some events to the queue
	Track("test_event_1", map[string]interface{}{"test": "value1"})
	Track("test_event_2", map[string]interface{}{"test": "value2"})

	// Verify events are in queue before flush
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 2)
	globalCollector.mu.Unlock()

	// Flush events (this will attempt to send but may fail due to dummy endpoint)
	globalCollector.flush()

	// Check that queue was cleared (flush clears queue regardless of send success)
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 0)
	globalCollector.mu.Unlock()
}

func TestCollector_FlushWithError(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://invalid-endpoint-that-will-fail.com", // Use an invalid endpoint
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Add an event to the queue
	Track("test_event", map[string]interface{}{"test": "value"})

	// Verify event is in queue before flush
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 1)
	globalCollector.mu.Unlock()

	// Flush (this will attempt to send but fail due to invalid endpoint)
	globalCollector.flush()

	// Queue should be cleared (flush clears queue regardless of send success)
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 0)
	globalCollector.mu.Unlock()
}

func TestCollector_FlushEmptyQueue(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Flush empty queue should not error
	globalCollector.flush()
}

func TestCollector_ConcurrentAccess(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Test concurrent event tracking
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			Track("concurrent_test", map[string]interface{}{
				"id": id,
			})
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Check that all events were added
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 10)
	globalCollector.mu.Unlock()
}

func TestEvent_JSONSerialization(t *testing.T) {
	event := Event{
		Type:      "test_event",
		Name:      "test",
		Timestamp: time.Now(),
		Properties: map[string]interface{}{
			"string": "value",
			"number": 42,
			"bool":   true,
		},
		Metrics: map[string]float64{
			"metric1": 1.5,
			"metric2": 2.0,
		},
		Context: &Context{
			SessionID:   "session_123",
			UserID:      "user_456",
			AnonymousID: "anon_789",
			Version:     "1.0.0",
			OS:          "linux",
			Arch:        "amd64",
			GoVersion:   "1.21.0",
		},
	}

	// Test JSON marshaling
	data, err := json.Marshal(event)
	require.NoError(t, err)
	assert.NotEmpty(t, data)

	// Test JSON unmarshaling
	var unmarshaled Event
	err = json.Unmarshal(data, &unmarshaled)
	require.NoError(t, err)
	assert.Equal(t, event.Type, unmarshaled.Type)
	assert.Equal(t, event.Name, unmarshaled.Name)
	
	// JSON unmarshaling converts int to float64, so we need to check values individually
	assert.Equal(t, "value", unmarshaled.Properties["string"])
	assert.Equal(t, float64(42), unmarshaled.Properties["number"]) // JSON converts int to float64
	assert.Equal(t, true, unmarshaled.Properties["bool"])
	
	assert.Equal(t, event.Metrics, unmarshaled.Metrics)
	assert.Equal(t, event.Context, unmarshaled.Context)
}

func TestTimer(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Start a timer
	timer := StartTimer("test_timer", map[string]interface{}{
		"component": "test",
	})
	require.NotNil(t, timer)

	// Wait a bit
	time.Sleep(10 * time.Millisecond)

	// Stop the timer
	timer.Stop()

	// Verify timing event was queued (Timer creates a metric event)
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 1)
	event := globalCollector.queue[0]
	assert.Equal(t, "metric", event.Type)
	assert.Equal(t, "test_timer_duration_ms", event.Name)
	assert.Equal(t, "test", event.Properties["component"])
	assert.Greater(t, event.Metrics["test_timer_duration_ms"], 0.0)
	globalCollector.mu.Unlock()
}

func TestCounter(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Create a counter
	counter := NewCounter("test_counter", map[string]interface{}{
		"component": "test",
	})
	require.NotNil(t, counter)

	// Increment the counter
	counter.Increment()
	counter.Add(5.0)

	// Flush the counter
	counter.Flush()

	// Verify counter event was queued (Counter.Flush() creates a single metric event)
	globalCollector.mu.Lock()
	assert.Len(t, globalCollector.queue, 1) // Flush creates one metric event
	event := globalCollector.queue[0]
	assert.Equal(t, "metric", event.Type)
	assert.Equal(t, "test_counter", event.Name)
	assert.Equal(t, float64(6), event.Metrics["test_counter"]) // 1 + 5 = 6
	globalCollector.mu.Unlock()
}

func TestHTTPMiddleware(t *testing.T) {
	cfg := &config.TelemetryConfig{
		Enabled:     true,
		Endpoint:    "https://telemetry.example.com",
		SampleRate:  1.0,
		Debug:       false,
		AnonymousID: "test-anon-id",
	}

	Initialize(cfg)
	// Clear the queue before this test
	globalCollector.mu.Lock()
	globalCollector.queue = make([]Event, 0, 100)
	globalCollector.mu.Unlock()

	// Create a test handler
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test response"))
	})

	// Wrap with telemetry middleware
	middleware := HTTPMiddleware(handler)

	// Create a test request
	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Serve the request
	middleware.ServeHTTP(w, req)

	// Verify response
	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "test response", w.Body.String())

	// HTTP middleware doesn't create events in the global collector queue
	// It only records metrics if extended instance is available
	// So we just verify the middleware executed without error
}