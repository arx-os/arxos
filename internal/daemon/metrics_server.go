package daemon

import (
	"context"
	"fmt"
	"net/http"
	"runtime"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// MetricsServer serves Prometheus metrics via HTTP
type MetricsServer struct {
	server *http.Server
	daemon *Daemon
}

// NewMetricsServer creates a new metrics server
func NewMetricsServer(daemon *Daemon, port int) *MetricsServer {
	mux := http.NewServeMux()

	// Prometheus metrics endpoint
	mux.Handle("/metrics", promhttp.Handler())

	// Health check endpoint
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// Ready check endpoint
	mux.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		if daemon.IsReady() {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("READY"))
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("NOT READY"))
		}
	})

	return &MetricsServer{
		server: &http.Server{
			Addr:    fmt.Sprintf(":%d", port),
			Handler: mux,
		},
		daemon: daemon,
	}
}

// Start begins serving metrics
func (ms *MetricsServer) Start() error {
	logger.Info("Starting metrics server on %s", ms.server.Addr)

	// Start memory usage updater
	go ms.updateMemoryMetrics()

	if err := ms.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("metrics server failed: %w", err)
	}
	return nil
}

// Stop gracefully shuts down the metrics server
func (ms *MetricsServer) Stop(ctx context.Context) error {
	logger.Info("Stopping metrics server...")
	return ms.server.Shutdown(ctx)
}

// updateMemoryMetrics periodically updates memory usage metrics
func (ms *MetricsServer) updateMemoryMetrics() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		ms.daemon.metrics.UpdateMemoryUsage(m.Alloc)
	}
}

// UpdateWorkerMetrics updates worker-related metrics
func (d *Daemon) UpdateWorkerMetrics() {
	if d.metrics == nil {
		return
	}

	d.mu.RLock()
	defer d.mu.RUnlock()

	// Update queue size
	if d.queue != nil {
		d.metrics.UpdateQueueSize(d.queue.Size())
	}

	// Update active workers count
	d.metrics.UpdateActiveWorkers(d.config.MaxWorkers)
}

// RecordFileProcessingMetrics records metrics for a processed file
func (d *Daemon) RecordFileProcessingMetrics(path string, sizeBytes int64, duration time.Duration, err error) {
	if d.metrics == nil {
		return
	}

	if err != nil {
		d.metrics.RecordError()
		return
	}

	d.metrics.RecordFileProcessed(float64(sizeBytes), duration.Seconds())
}

// RecordQueueWaitMetrics records how long an item waited in the queue
func (d *Daemon) RecordQueueWaitMetrics(waitTime time.Duration) {
	if d.metrics == nil {
		return
	}

	d.metrics.RecordQueueWaitTime(waitTime.Seconds())
}

// IsReady checks if the daemon is ready to serve requests
func (d *Daemon) IsReady() bool {
	d.mu.RLock()
	defer d.mu.RUnlock()

	// Check if database is connected
	if d.db == nil {
		return false
	}

	// Check if workers are running
	if d.queue == nil || d.queue.Size() < 0 {
		return false
	}

	return true
}