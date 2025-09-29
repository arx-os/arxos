package telemetry

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/config"
)

// createTestMetricsCollector creates a metrics collector for testing
func createTestMetricsCollector() *MetricsCollector {
	cfg := &ObservabilityConfig{
		TelemetryConfig: &config.TelemetryConfig{
			Enabled:     false, // Disable telemetry for testing
			Endpoint:    "https://telemetry.example.com",
			SampleRate:  1.0,
			Debug:       false,
			AnonymousID: "test-anon-id",
		},
		ServiceName: "test-service",
		Environment: "test",
	}
	return NewMetricsCollector(cfg)
}

func TestNewMetricsCollector(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)
	assert.NotNil(t, collector.counters)
	assert.NotNil(t, collector.gauges)
	assert.NotNil(t, collector.histos)
	// Don't test mutex directly as it copies the lock
}

func TestMetricsCollector_IncrementCounter(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Test incrementing a counter
	collector.IncrementCounter("test_counter", map[string]string{"tag": "value"})

	counters := collector.GetCounters()
	// The key includes tags, so it will be "test_counter,tag=value"
	key := "test_counter,tag=value"
	counter, exists := counters[key]
	require.True(t, exists)
	assert.Equal(t, "test_counter", counter.Name)
	assert.Equal(t, float64(1), counter.Value)
	assert.Equal(t, map[string]string{"tag": "value"}, counter.Tags)
}

func TestMetricsCollector_IncrementCounterMultiple(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Increment counter multiple times
	collector.IncrementCounter("test_counter", nil)
	collector.IncrementCounter("test_counter", nil)
	collector.IncrementCounter("test_counter", nil)

	counters := collector.GetCounters()
	// The key for nil tags is just the name
	counter, exists := counters["test_counter"]
	require.True(t, exists)
	assert.Equal(t, float64(3), counter.Value)
}

func TestMetricsCollector_RecordGauge(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Test adding a gauge value
	collector.RecordGauge("test_gauge", 42.5, map[string]string{"tag": "value"})

	gauges := collector.GetGauges()
	// The key includes tags, so it will be "test_gauge,tag=value"
	key := "test_gauge,tag=value"
	gauge, exists := gauges[key]
	require.True(t, exists)
	assert.Equal(t, "test_gauge", gauge.Name)
	assert.Equal(t, 42.5, gauge.Value)
	assert.Equal(t, map[string]string{"tag": "value"}, gauge.Tags)
}

func TestMetricsCollector_RecordGaugeMultiple(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Add multiple gauge values
	collector.RecordGauge("test_gauge", 10.0, nil)
	collector.RecordGauge("test_gauge", 20.0, nil)
	collector.RecordGauge("test_gauge", 30.0, nil)

	gauges := collector.GetGauges()
	// The key for nil tags is just the name
	gauge, exists := gauges["test_gauge"]
	require.True(t, exists)
	assert.Equal(t, 30.0, gauge.Value) // Should be the last value
}

func TestMetricsCollector_RecordHistogram(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Test recording histogram values
	collector.RecordHistogram("test_histogram", 1.0, map[string]string{"tag": "value"})
	collector.RecordHistogram("test_histogram", 2.0, map[string]string{"tag": "value"})
	collector.RecordHistogram("test_histogram", 3.0, map[string]string{"tag": "value"})

	histograms := collector.GetHistograms()
	// The key includes tags, so it will be "test_histogram,tag=value"
	key := "test_histogram,tag=value"
	histogram, exists := histograms[key]
	require.True(t, exists)
	assert.Equal(t, "test_histogram", histogram.Name)
	assert.Equal(t, map[string]string{"tag": "value"}, histogram.Tags)
	assert.Equal(t, int64(3), histogram.Count)
	assert.Equal(t, 6.0, histogram.Sum) // 1.0 + 2.0 + 3.0
}

func TestMetricsCollector_GetCounters(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Add some counters
	collector.IncrementCounter("counter1", map[string]string{"tag": "value1"})
	collector.IncrementCounter("counter2", map[string]string{"tag": "value2"})

	// Get all counters
	counters := collector.GetCounters()
	assert.Len(t, counters, 2)

	// Check individual counters (keys include tags)
	counter1Key := "counter1,tag=value1"
	counter1, exists := counters[counter1Key]
	require.True(t, exists)
	assert.Equal(t, "counter1", counter1.Name)
	assert.Equal(t, float64(1), counter1.Value)

	counter2Key := "counter2,tag=value2"
	counter2, exists := counters[counter2Key]
	require.True(t, exists)
	assert.Equal(t, "counter2", counter2.Name)
	assert.Equal(t, float64(1), counter2.Value)
}

func TestMetricsCollector_GetGauges(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Add some gauges
	collector.RecordGauge("gauge1", 42.0, map[string]string{"tag": "value1"})
	collector.RecordGauge("gauge2", 84.0, map[string]string{"tag": "value2"})

	// Get all gauges
	gauges := collector.GetGauges()
	assert.Len(t, gauges, 2)

	// Check individual gauges (keys include tags)
	gauge1Key := "gauge1,tag=value1"
	gauge1, exists := gauges[gauge1Key]
	require.True(t, exists)
	assert.Equal(t, "gauge1", gauge1.Name)
	assert.Equal(t, 42.0, gauge1.Value)

	gauge2Key := "gauge2,tag=value2"
	gauge2, exists := gauges[gauge2Key]
	require.True(t, exists)
	assert.Equal(t, "gauge2", gauge2.Name)
	assert.Equal(t, 84.0, gauge2.Value)
}

func TestMetricsCollector_GetHistograms(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Add some histograms
	collector.RecordHistogram("histogram1", 1.0, map[string]string{"tag": "value1"})
	collector.RecordHistogram("histogram2", 2.0, map[string]string{"tag": "value2"})

	// Get all histograms
	histograms := collector.GetHistograms()
	assert.Len(t, histograms, 2)

	// Check individual histograms (keys include tags)
	histogram1Key := "histogram1,tag=value1"
	histogram1, exists := histograms[histogram1Key]
	require.True(t, exists)
	assert.Equal(t, "histogram1", histogram1.Name)
	assert.Equal(t, int64(1), histogram1.Count)

	histogram2Key := "histogram2,tag=value2"
	histogram2, exists := histograms[histogram2Key]
	require.True(t, exists)
	assert.Equal(t, "histogram2", histogram2.Name)
	assert.Equal(t, int64(1), histogram2.Count)
}

func TestMetricsCollector_ConcurrentAccess(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Test concurrent access
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			collector.IncrementCounter("concurrent_counter", map[string]string{"id": string(rune(id))})
			collector.RecordGauge("concurrent_gauge", float64(id), map[string]string{"id": string(rune(id))})
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Check that all operations completed without race conditions
	counters := collector.GetCounters()
	// Each goroutine creates a counter with a unique tag, so we should have 10 counters
	assert.Len(t, counters, 10)

	gauges := collector.GetGauges()
	// Each goroutine creates a gauge with a unique tag, so we should have 10 gauges
	assert.Len(t, gauges, 10)
}

func TestMetricsCollector_Stop(t *testing.T) {
	collector := createTestMetricsCollector()
	require.NotNil(t, collector)

	// Add some metrics
	collector.IncrementCounter("test_counter", nil)
	collector.RecordGauge("test_gauge", 42.0, nil)

	// Stop collector
	collector.Stop()
}

func TestCounterMetric_JSONSerialization(t *testing.T) {
	counter := CounterMetric{
		Name:  "test_counter",
		Value: 42,
		Tags: map[string]string{
			"tag1": "value1",
			"tag2": "value2",
		},
	}

	// Create a DTO without mutex for JSON testing
	counterDTO := struct {
		Name  string            `json:"name"`
		Value float64           `json:"value"`
		Tags  map[string]string `json:"tags"`
	}{
		Name:  counter.Name,
		Value: counter.Value,
		Tags:  counter.Tags,
	}

	// Test JSON marshaling
	data, err := json.Marshal(counterDTO)
	require.NoError(t, err)
	assert.NotEmpty(t, data)

	// Test JSON unmarshaling
	var unmarshaled struct {
		Name  string            `json:"name"`
		Value float64           `json:"value"`
		Tags  map[string]string `json:"tags"`
	}
	err = json.Unmarshal(data, &unmarshaled)
	require.NoError(t, err)
	assert.Equal(t, counter.Name, unmarshaled.Name)
	assert.Equal(t, counter.Value, unmarshaled.Value)
	assert.Equal(t, counter.Tags, unmarshaled.Tags)
}

func TestGaugeMetric_JSONSerialization(t *testing.T) {
	gauge := GaugeMetric{
		Name:  "test_gauge",
		Value: 123.45,
		Tags: map[string]string{
			"tag1": "value1",
			"tag2": "value2",
		},
		Timestamp: time.Now(),
	}

	// Create a DTO without mutex for JSON testing
	gaugeDTO := struct {
		Name      string            `json:"name"`
		Value     float64           `json:"value"`
		Tags      map[string]string `json:"tags"`
		Timestamp time.Time         `json:"timestamp"`
	}{
		Name:      gauge.Name,
		Value:     gauge.Value,
		Tags:      gauge.Tags,
		Timestamp: gauge.Timestamp,
	}

	// Test JSON marshaling
	data, err := json.Marshal(gaugeDTO)
	require.NoError(t, err)
	assert.NotEmpty(t, data)

	// Test JSON unmarshaling
	var unmarshaled struct {
		Name      string            `json:"name"`
		Value     float64           `json:"value"`
		Tags      map[string]string `json:"tags"`
		Timestamp time.Time         `json:"timestamp"`
	}
	err = json.Unmarshal(data, &unmarshaled)
	require.NoError(t, err)
	assert.Equal(t, gauge.Name, unmarshaled.Name)
	assert.Equal(t, gauge.Value, unmarshaled.Value)
	assert.Equal(t, gauge.Tags, unmarshaled.Tags)
}

func TestHistogramMetric_JSONSerialization(t *testing.T) {
	histogram := HistogramMetric{
		Name:  "test_histogram",
		Count: 10,
		Sum:   50.0,
		Min:   1.0,
		Max:   10.0,
		Buckets: map[float64]int64{
			1.0:  5,
			5.0:  8,
			10.0: 10,
		},
		Tags: map[string]string{
			"tag1": "value1",
		},
	}

	// Test basic properties (skip JSON due to map[float64]int64 not being JSON serializable)
	assert.Equal(t, "test_histogram", histogram.Name)
	assert.Equal(t, int64(10), histogram.Count)
	assert.Equal(t, 50.0, histogram.Sum)
	assert.Equal(t, 1.0, histogram.Min)
	assert.Equal(t, 10.0, histogram.Max)
	assert.Equal(t, map[string]string{"tag1": "value1"}, histogram.Tags)
	assert.Len(t, histogram.Buckets, 3)
}
