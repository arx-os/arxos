package monitoring

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestNewMetricsCollector(t *testing.T) {
	collector := NewMetricsCollector()

	assert.NotNil(t, collector)
	assert.NotNil(t, collector.metrics)
	assert.NotNil(t, collector.counters)
	assert.NotNil(t, collector.gauges)
	assert.NotNil(t, collector.timers)
	assert.NotNil(t, collector.histograms)
}

func TestMetricsCollector_IncrementCounter(t *testing.T) {
	collector := NewMetricsCollector()

	// Test incrementing counter
	collector.IncrementCounter("test_counter", map[string]string{"label1": "value1"})

	counter := collector.GetCounter("test_counter", map[string]string{"label1": "value1"})
	assert.NotNil(t, counter)
	assert.Equal(t, int64(1), counter.Value)
	assert.Equal(t, "test_counter", counter.Name)

	// Test incrementing same counter again
	collector.IncrementCounter("test_counter", map[string]string{"label1": "value1"})

	counter = collector.GetCounter("test_counter", map[string]string{"label1": "value1"})
	assert.Equal(t, int64(2), counter.Value)
}

func TestMetricsCollector_SetGauge(t *testing.T) {
	collector := NewMetricsCollector()

	// Test setting gauge
	collector.SetGauge("test_gauge", 42.5, map[string]string{"label1": "value1"})

	gauge := collector.GetGauge("test_gauge", map[string]string{"label1": "value1"})
	assert.NotNil(t, gauge)
	assert.Equal(t, 42.5, gauge.Value)
	assert.Equal(t, "test_gauge", gauge.Name)

	// Test updating gauge
	collector.SetGauge("test_gauge", 100.0, map[string]string{"label1": "value1"})

	gauge = collector.GetGauge("test_gauge", map[string]string{"label1": "value1"})
	assert.Equal(t, 100.0, gauge.Value)
}

func TestMetricsCollector_RecordTimer(t *testing.T) {
	collector := NewMetricsCollector()

	duration := 150 * time.Millisecond
	collector.RecordTimer("test_timer", duration, map[string]string{"label1": "value1"})

	timer := collector.GetTimer("test_timer", map[string]string{"label1": "value1"})
	assert.NotNil(t, timer)
	assert.Equal(t, duration, timer.Duration)
	assert.Equal(t, "test_timer", timer.Name)
}

func TestMetricsCollector_RecordHistogram(t *testing.T) {
	collector := NewMetricsCollector()

	// Test recording histogram values
	collector.RecordHistogram("test_histogram", 1.5, map[string]string{"label1": "value1"})
	collector.RecordHistogram("test_histogram", 2.5, map[string]string{"label1": "value1"})
	collector.RecordHistogram("test_histogram", 3.5, map[string]string{"label1": "value1"})

	histogram := collector.GetHistogram("test_histogram", map[string]string{"label1": "value1"})
	assert.NotNil(t, histogram)
	assert.Equal(t, int64(3), histogram.Count)
	assert.Equal(t, 7.5, histogram.Sum) // 1.5 + 2.5 + 3.5
	assert.Equal(t, "test_histogram", histogram.Name)
	assert.NotNil(t, histogram.Buckets)
}

func TestMetricsCollector_GetAllMetrics(t *testing.T) {
	collector := NewMetricsCollector()

	// Add some metrics
	collector.IncrementCounter("counter1", nil)
	collector.SetGauge("gauge1", 10.0, nil)
	collector.RecordTimer("timer1", 100*time.Millisecond, nil)
	collector.RecordHistogram("histogram1", 5.0, nil)

	allMetrics := collector.GetAllMetrics()

	assert.Contains(t, allMetrics, "counters")
	assert.Contains(t, allMetrics, "gauges")
	assert.Contains(t, allMetrics, "timers")
	assert.Contains(t, allMetrics, "histograms")
	assert.Contains(t, allMetrics, "timestamp")
}

func TestMetricsCollector_GetMetricsSummary(t *testing.T) {
	collector := NewMetricsCollector()

	// Add some metrics
	collector.IncrementCounter("counter1", nil)
	collector.SetGauge("gauge1", 10.0, nil)
	collector.RecordTimer("timer1", 100*time.Millisecond, nil)
	collector.RecordHistogram("histogram1", 5.0, nil)

	summary := collector.GetMetricsSummary()

	assert.Equal(t, 1, summary["total_counters"])
	assert.Equal(t, 1, summary["total_gauges"])
	assert.Equal(t, 1, summary["total_timers"])
	assert.Equal(t, 1, summary["total_histograms"])
	assert.Contains(t, summary, "timestamp")
}

func TestMetricsCollector_Reset(t *testing.T) {
	collector := NewMetricsCollector()

	// Add some metrics
	collector.IncrementCounter("counter1", nil)
	collector.SetGauge("gauge1", 10.0, nil)
	collector.RecordTimer("timer1", 100*time.Millisecond, nil)
	collector.RecordHistogram("histogram1", 5.0, nil)

	// Verify metrics exist
	summary := collector.GetMetricsSummary()
	assert.Equal(t, 1, summary["total_counters"])
	assert.Equal(t, 1, summary["total_gauges"])
	assert.Equal(t, 1, summary["total_timers"])
	assert.Equal(t, 1, summary["total_histograms"])

	// Reset metrics
	collector.Reset()

	// Verify metrics are cleared
	summary = collector.GetMetricsSummary()
	assert.Equal(t, 0, summary["total_counters"])
	assert.Equal(t, 0, summary["total_gauges"])
	assert.Equal(t, 0, summary["total_timers"])
	assert.Equal(t, 0, summary["total_histograms"])
}

func TestMetricsCollector_ExportMetrics(t *testing.T) {
	collector := NewMetricsCollector()

	// Add some metrics
	collector.IncrementCounter("test_counter", map[string]string{"label1": "value1"})
	collector.SetGauge("test_gauge", 42.5, map[string]string{"label1": "value1"})
	collector.RecordHistogram("test_histogram", 1.5, map[string]string{"label1": "value1"})

	// Export metrics
	exported := collector.ExportMetrics()

	// Verify Prometheus format
	assert.Contains(t, exported, "# HELP test_counter")
	assert.Contains(t, exported, "# TYPE test_counter counter")
	assert.Contains(t, exported, "test_counter{label1=\"value1\"} 1")

	assert.Contains(t, exported, "# HELP test_gauge")
	assert.Contains(t, exported, "# TYPE test_gauge gauge")
	assert.Contains(t, exported, "test_gauge{label1=\"value1\"} 42.50")

	assert.Contains(t, exported, "# HELP test_histogram")
	assert.Contains(t, exported, "# TYPE test_histogram histogram")
	assert.Contains(t, exported, "test_histogram_sum{label1=\"value1\"} 1.50")
	assert.Contains(t, exported, "test_histogram_count{label1=\"value1\"} 1")
}

func TestMetricsCollector_ConcurrentAccess(t *testing.T) {
	collector := NewMetricsCollector()

	// Test concurrent access
	done := make(chan bool, 10)

	for i := 0; i < 10; i++ {
		go func() {
			defer func() { done <- true }()

			collector.IncrementCounter("concurrent_counter", nil)
			collector.SetGauge("concurrent_gauge", 1.0, nil)
			collector.RecordTimer("concurrent_timer", 1*time.Millisecond, nil)
			collector.RecordHistogram("concurrent_histogram", 1.0, nil)
		}()
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify final values
	counter := collector.GetCounter("concurrent_counter", nil)
	assert.Equal(t, int64(10), counter.Value)

	gauge := collector.GetGauge("concurrent_gauge", nil)
	assert.Equal(t, 1.0, gauge.Value) // Last value set

	histogram := collector.GetHistogram("concurrent_histogram", nil)
	assert.Equal(t, int64(10), histogram.Count)
	assert.Equal(t, 10.0, histogram.Sum)
}

func TestGlobalMetricsCollector(t *testing.T) {
	// Test global metrics collector
	collector1 := GetGlobalMetricsCollector()
	collector2 := GetGlobalMetricsCollector()

	// Should return the same instance
	assert.Equal(t, collector1, collector2)

	// Test global convenience functions
	IncrementCounter("global_counter", nil)
	SetGauge("global_gauge", 42.0, nil)
	RecordTimer("global_timer", 100*time.Millisecond, nil)
	RecordHistogram("global_histogram", 5.0, nil)

	// Verify metrics were recorded
	counter := collector1.GetCounter("global_counter", nil)
	assert.NotNil(t, counter)
	assert.Equal(t, int64(1), counter.Value)

	gauge := collector1.GetGauge("global_gauge", nil)
	assert.NotNil(t, gauge)
	assert.Equal(t, 42.0, gauge.Value)

	timer := collector1.GetTimer("global_timer", nil)
	assert.NotNil(t, timer)
	assert.Equal(t, 100*time.Millisecond, timer.Duration)

	histogram := collector1.GetHistogram("global_histogram", nil)
	assert.NotNil(t, histogram)
	assert.Equal(t, int64(1), histogram.Count)
	assert.Equal(t, 5.0, histogram.Sum)
}

func TestMetricsCollector_StartMetricsCollection(t *testing.T) {
	collector := NewMetricsCollector()
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Start metrics collection
	go collector.StartMetricsCollection(ctx, 10*time.Millisecond)

	// Wait for context to be done
	<-ctx.Done()

	// Verify system metrics were collected
	allMetrics := collector.GetAllMetrics()
	gauges := allMetrics["gauges"].(map[string]*Gauge)

	// Should have system metrics
	assert.Contains(t, gauges, "system_memory_usage")
	assert.Contains(t, gauges, "system_cpu_usage")
	assert.Contains(t, gauges, "system_goroutines")
}

func BenchmarkMetricsCollector_IncrementCounter(b *testing.B) {
	collector := NewMetricsCollector()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		collector.IncrementCounter("benchmark_counter", nil)
	}
}

func BenchmarkMetricsCollector_SetGauge(b *testing.B) {
	collector := NewMetricsCollector()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		collector.SetGauge("benchmark_gauge", float64(i), nil)
	}
}

func BenchmarkMetricsCollector_RecordTimer(b *testing.B) {
	collector := NewMetricsCollector()
	duration := 100 * time.Millisecond

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		collector.RecordTimer("benchmark_timer", duration, nil)
	}
}

func BenchmarkMetricsCollector_RecordHistogram(b *testing.B) {
	collector := NewMetricsCollector()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		collector.RecordHistogram("benchmark_histogram", float64(i), nil)
	}
}
