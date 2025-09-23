package daemon

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Metrics contains all Prometheus metrics for the daemon
type Metrics struct {
	// Counters
	filesProcessed   prometheus.Counter
	filesSkipped     prometheus.Counter
	processingErrors prometheus.Counter
	bytesProcessed   prometheus.Counter

	// Gauges
	queueSize        prometheus.Gauge
	workersActive    prometheus.Gauge
	lastProcessTime  prometheus.Gauge
	memoryUsage      prometheus.Gauge

	// Histograms
	processingDuration prometheus.Histogram
	fileSizeBytes      prometheus.Histogram
	queueWaitTime      prometheus.Histogram

	// Summary
	processingLatency prometheus.Summary
}

// NewMetrics creates and registers all daemon metrics
func NewMetrics() *Metrics {
	namespace := "arxos"
	subsystem := "daemon"

	return &Metrics{
		// Counters
		filesProcessed: promauto.NewCounter(prometheus.CounterOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "files_processed_total",
			Help:      "Total number of files processed by the daemon",
		}),

		filesSkipped: promauto.NewCounter(prometheus.CounterOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "files_skipped_total",
			Help:      "Total number of files skipped by the daemon",
		}),

		processingErrors: promauto.NewCounter(prometheus.CounterOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "processing_errors_total",
			Help:      "Total number of processing errors encountered",
		}),

		bytesProcessed: promauto.NewCounter(prometheus.CounterOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "bytes_processed_total",
			Help:      "Total number of bytes processed",
		}),

		// Gauges
		queueSize: promauto.NewGauge(prometheus.GaugeOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "queue_size",
			Help:      "Current size of the work queue",
		}),

		workersActive: promauto.NewGauge(prometheus.GaugeOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "workers_active",
			Help:      "Number of active worker threads",
		}),

		lastProcessTime: promauto.NewGauge(prometheus.GaugeOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "last_process_time_seconds",
			Help:      "Unix timestamp of the last successful processing",
		}),

		memoryUsage: promauto.NewGauge(prometheus.GaugeOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "memory_usage_bytes",
			Help:      "Current memory usage in bytes",
		}),

		// Histograms
		processingDuration: promauto.NewHistogram(prometheus.HistogramOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "processing_duration_seconds",
			Help:      "Time taken to process a file",
			Buckets:   prometheus.DefBuckets,
		}),

		fileSizeBytes: promauto.NewHistogram(prometheus.HistogramOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "file_size_bytes",
			Help:      "Size of processed files in bytes",
			Buckets:   prometheus.ExponentialBuckets(1024, 2, 20), // 1KB to 1GB
		}),

		queueWaitTime: promauto.NewHistogram(prometheus.HistogramOpts{
			Namespace: namespace,
			Subsystem: subsystem,
			Name:      "queue_wait_time_seconds",
			Help:      "Time items spend waiting in the queue",
			Buckets:   prometheus.DefBuckets,
		}),

		// Summary
		processingLatency: promauto.NewSummary(prometheus.SummaryOpts{
			Namespace:  namespace,
			Subsystem:  subsystem,
			Name:       "processing_latency_seconds",
			Help:       "Processing latency in seconds",
			Objectives: map[float64]float64{0.5: 0.05, 0.9: 0.01, 0.99: 0.001},
		}),
	}
}

// RecordFileProcessed records a successfully processed file
func (m *Metrics) RecordFileProcessed(sizeBytes float64, durationSeconds float64) {
	m.filesProcessed.Inc()
	m.bytesProcessed.Add(sizeBytes)
	m.fileSizeBytes.Observe(sizeBytes)
	m.processingDuration.Observe(durationSeconds)
	m.processingLatency.Observe(durationSeconds)
	m.lastProcessTime.SetToCurrentTime()
}

// RecordFileSkipped records a skipped file
func (m *Metrics) RecordFileSkipped() {
	m.filesSkipped.Inc()
}

// RecordError records a processing error
func (m *Metrics) RecordError() {
	m.processingErrors.Inc()
}

// UpdateQueueSize updates the current queue size
func (m *Metrics) UpdateQueueSize(size int) {
	m.queueSize.Set(float64(size))
}

// UpdateActiveWorkers updates the number of active workers
func (m *Metrics) UpdateActiveWorkers(count int) {
	m.workersActive.Set(float64(count))
}

// UpdateMemoryUsage updates the current memory usage
func (m *Metrics) UpdateMemoryUsage(bytes uint64) {
	m.memoryUsage.Set(float64(bytes))
}

// RecordQueueWaitTime records how long an item waited in the queue
func (m *Metrics) RecordQueueWaitTime(seconds float64) {
	m.queueWaitTime.Observe(seconds)
}