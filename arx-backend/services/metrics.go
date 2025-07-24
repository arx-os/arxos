package services

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
	"gorm.io/gorm"
)

// MetricsService provides comprehensive metrics collection and aggregation
type MetricsService struct {
	db *gorm.DB

	// Custom metrics
	customMetrics map[string]*CustomMetric
	metricsMutex  sync.RWMutex

	// Aggregation
	aggregationInterval time.Duration
	aggregationData     map[string]*AggregatedMetric
	aggMutex            sync.RWMutex

	// Real-time metrics
	realTimeMetrics map[string]*RealTimeMetric
	rtMutex         sync.RWMutex

	// Performance tracking
	performanceTrackers map[string]*PerformanceTracker
	perfMutex           sync.RWMutex

	// Context for graceful shutdown
	ctx    context.Context
	cancel context.CancelFunc
}

// CustomMetric represents a custom metric
type CustomMetric struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"` // counter, gauge, histogram, summary
	Description string                 `json:"description"`
	Labels      []string               `json:"labels"`
	Value       float64                `json:"value"`
	Metadata    map[string]interface{} `json:"metadata"`
	LastUpdated time.Time              `json:"last_updated"`
}

// AggregatedMetric represents aggregated metric data
type AggregatedMetric struct {
	Name        string    `json:"name"`
	Count       int64     `json:"count"`
	Sum         float64   `json:"sum"`
	Min         float64   `json:"min"`
	Max         float64   `json:"max"`
	Avg         float64   `json:"avg"`
	P95         float64   `json:"p95"`
	P99         float64   `json:"p99"`
	LastUpdated time.Time `json:"last_updated"`
	Values      []float64 `json:"values"`
}

// RealTimeMetric represents real-time metric data
type RealTimeMetric struct {
	Name        string                 `json:"name"`
	Value       float64                `json:"value"`
	Unit        string                 `json:"unit"`
	Labels      map[string]string      `json:"labels"`
	Metadata    map[string]interface{} `json:"metadata"`
	LastUpdated time.Time              `json:"last_updated"`
}

// NewMetricsService creates a new metrics service
func NewMetricsService(db *gorm.DB) *MetricsService {
	ctx, cancel := context.WithCancel(context.Background())

	ms := &MetricsService{
		db:                  db,
		customMetrics:       make(map[string]*CustomMetric),
		aggregationData:     make(map[string]*AggregatedMetric),
		realTimeMetrics:     make(map[string]*RealTimeMetric),
		performanceTrackers: make(map[string]*PerformanceTracker),
		aggregationInterval: 60 * time.Second,
		ctx:                 ctx,
		cancel:              cancel,
	}

	// Start background aggregation
	go ms.startAggregation()

	return ms
}

// startAggregation runs background metric aggregation
func (ms *MetricsService) startAggregation() {
	ticker := time.NewTicker(ms.aggregationInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			ms.aggregateMetrics()
		case <-ms.ctx.Done():
			return
		}
	}
}

// aggregateMetrics aggregates metrics over time
func (ms *MetricsService) aggregateMetrics() {
	ms.aggMutex.Lock()
	defer ms.aggMutex.Unlock()

	// Aggregate custom metrics
	for name, metric := range ms.customMetrics {
		agg, exists := ms.aggregationData[name]
		if !exists {
			agg = &AggregatedMetric{
				Name:        name,
				Min:         metric.Value,
				Max:         metric.Value,
				LastUpdated: time.Now(),
			}
			ms.aggregationData[name] = agg
		}

		agg.Count++
		agg.Sum += metric.Value
		if metric.Value < agg.Min {
			agg.Min = metric.Value
		}
		if metric.Value > agg.Max {
			agg.Max = metric.Value
		}
		agg.Avg = agg.Sum / float64(agg.Count)
		agg.Values = append(agg.Values, metric.Value)

		// Keep only last 100 values for percentile calculation
		if len(agg.Values) > 100 {
			agg.Values = agg.Values[len(agg.Values)-100:]
		}

		// Calculate percentiles
		if len(agg.Values) > 0 {
			agg.P95 = calculatePercentile(agg.Values, 95)
			agg.P99 = calculatePercentile(agg.Values, 99)
		}

		agg.LastUpdated = time.Now()
	}
}

// calculatePercentile calculates the nth percentile of values
func calculatePercentile(values []float64, n int) float64 {
	if len(values) == 0 {
		return 0
	}

	// Sort values
	sorted := make([]float64, len(values))
	copy(sorted, values)

	// Simple percentile calculation
	index := int(float64(len(sorted)-1) * float64(n) / 100.0)
	if index >= len(sorted) {
		index = len(sorted) - 1
	}

	return sorted[index]
}

// RecordCustomMetric records a custom metric
func (ms *MetricsService) RecordCustomMetric(name, metricType, description string, value float64, labels []string, metadata map[string]interface{}) {
	ms.metricsMutex.Lock()
	defer ms.metricsMutex.Unlock()

	metric := &CustomMetric{
		Name:        name,
		Type:        metricType,
		Description: description,
		Labels:      labels,
		Value:       value,
		Metadata:    metadata,
		LastUpdated: time.Now(),
	}

	ms.customMetrics[name] = metric
}

// UpdateRealTimeMetric updates a real-time metric
func (ms *MetricsService) UpdateRealTimeMetric(name string, value float64, unit string, labels map[string]string, metadata map[string]interface{}) {
	ms.rtMutex.Lock()
	defer ms.rtMutex.Unlock()

	metric := &RealTimeMetric{
		Name:        name,
		Value:       value,
		Unit:        unit,
		Labels:      labels,
		Metadata:    metadata,
		LastUpdated: time.Now(),
	}

	ms.realTimeMetrics[name] = metric
}

// CollectSystemMetrics collects comprehensive system metrics
func (ms *MetricsService) CollectSystemMetrics() map[string]interface{} {
	metrics := make(map[string]interface{})

	// CPU metrics
	if cpuPercentages, err := cpu.Percent(0, true); err == nil {
		metrics["cpu"] = map[string]interface{}{
			"cores":          len(cpuPercentages),
			"usage_per_core": cpuPercentages,
			"total_usage":    calculateAverage(cpuPercentages),
		}
	}

	// Memory metrics
	if memory, err := mem.VirtualMemory(); err == nil {
		metrics["memory"] = map[string]interface{}{
			"total":     memory.Total,
			"used":      memory.Used,
			"available": memory.Available,
			"cached":    memory.Cached,
			"percent":   memory.UsedPercent,
		}
	}

	// Disk metrics
	if partitions, err := disk.Partitions(false); err == nil {
		diskMetrics := make(map[string]interface{})
		for _, partition := range partitions {
			if usage, err := disk.Usage(partition.Mountpoint); err == nil {
				diskMetrics[partition.Mountpoint] = map[string]interface{}{
					"total":   usage.Total,
					"used":    usage.Used,
					"free":    usage.Free,
					"percent": usage.UsedPercent,
				}
			}
		}
		metrics["disk"] = diskMetrics
	}

	// Network metrics
	if netStats, err := net.IOCounters(false); err == nil {
		if len(netStats) > 0 {
			netStat := netStats[0]
			metrics["network"] = map[string]interface{}{
				"bytes_sent":   netStat.BytesSent,
				"bytes_recv":   netStat.BytesRecv,
				"packets_sent": netStat.PacketsSent,
				"packets_recv": netStat.PacketsRecv,
				"err_in":       netStat.Errin,
				"err_out":      netStat.Errout,
				"drop_in":      netStat.Dropin,
				"drop_out":     netStat.Dropout,
			}
		}
	}

	// Database metrics
	metrics["database"] = ms.collectDatabaseMetrics()

	// Application metrics
	metrics["application"] = ms.collectApplicationMetrics()

	return metrics
}

// collectDatabaseMetrics collects database-specific metrics
func (ms *MetricsService) collectDatabaseMetrics() map[string]interface{} {
	sqlDB, _ := ms.db.DB()
	stats := sqlDB.Stats()

	return map[string]interface{}{
		"max_open_connections": stats.MaxOpenConnections,
		"open_connections":     stats.OpenConnections,
		"in_use":               stats.InUse,
		"idle":                 stats.Idle,
		"wait_count":           stats.WaitCount,
		"wait_duration":        stats.WaitDuration,
		"max_idle_closed":      stats.MaxIdleClosed,
		"max_lifetime_closed":  stats.MaxLifetimeClosed,
	}
}

// collectApplicationMetrics collects application-specific metrics
func (ms *MetricsService) collectApplicationMetrics() map[string]interface{} {
	ms.metricsMutex.RLock()
	defer ms.metricsMutex.RUnlock()

	appMetrics := make(map[string]interface{})

	// Custom metrics summary
	customMetricsCount := len(ms.customMetrics)
	appMetrics["custom_metrics_count"] = customMetricsCount

	// Real-time metrics summary
	ms.rtMutex.RLock()
	realTimeMetricsCount := len(ms.realTimeMetrics)
	appMetrics["realtime_metrics_count"] = realTimeMetricsCount
	ms.rtMutex.RUnlock()

	// Performance trackers summary
	ms.perfMutex.RLock()
	performanceTrackersCount := len(ms.performanceTrackers)
	appMetrics["performance_trackers_count"] = performanceTrackersCount
	ms.perfMutex.RUnlock()

	return appMetrics
}

// GetMetricsSummary returns a summary of all metrics
func (ms *MetricsService) GetMetricsSummary() map[string]interface{} {
	summary := make(map[string]interface{})

	// System metrics
	summary["system"] = ms.CollectSystemMetrics()

	// Custom metrics
	ms.metricsMutex.RLock()
	customMetrics := make(map[string]*CustomMetric)
	for k, v := range ms.customMetrics {
		customMetrics[k] = &CustomMetric{
			Name:        v.Name,
			Type:        v.Type,
			Description: v.Description,
			Labels:      v.Labels,
			Value:       v.Value,
			Metadata:    v.Metadata,
			LastUpdated: v.LastUpdated,
		}
	}
	summary["custom_metrics"] = customMetrics
	ms.metricsMutex.RUnlock()

	// Aggregated metrics
	ms.aggMutex.RLock()
	aggregatedMetrics := make(map[string]*AggregatedMetric)
	for k, v := range ms.aggregationData {
		aggregatedMetrics[k] = &AggregatedMetric{
			Name:        v.Name,
			Count:       v.Count,
			Sum:         v.Sum,
			Min:         v.Min,
			Max:         v.Max,
			Avg:         v.Avg,
			P95:         v.P95,
			P99:         v.P99,
			LastUpdated: v.LastUpdated,
		}
	}
	summary["aggregated_metrics"] = aggregatedMetrics
	ms.aggMutex.RUnlock()

	// Real-time metrics
	ms.rtMutex.RLock()
	realTimeMetrics := make(map[string]*RealTimeMetric)
	for k, v := range ms.realTimeMetrics {
		realTimeMetrics[k] = &RealTimeMetric{
			Name:        v.Name,
			Value:       v.Value,
			Unit:        v.Unit,
			Labels:      v.Labels,
			Metadata:    v.Metadata,
			LastUpdated: v.LastUpdated,
		}
	}
	summary["realtime_metrics"] = realTimeMetrics
	ms.rtMutex.RUnlock()

	// Performance data
	summary["performance_data"] = ms.GetPerformanceData()

	summary["timestamp"] = time.Now()
	summary["metrics_service_uptime"] = time.Since(time.Now()).String()

	return summary
}

// GetCustomMetrics returns all custom metrics
func (ms *MetricsService) GetCustomMetrics() map[string]*CustomMetric {
	ms.metricsMutex.RLock()
	defer ms.metricsMutex.RUnlock()

	metrics := make(map[string]*CustomMetric)
	for k, v := range ms.customMetrics {
		metrics[k] = &CustomMetric{
			Name:        v.Name,
			Type:        v.Type,
			Description: v.Description,
			Labels:      v.Labels,
			Value:       v.Value,
			Metadata:    v.Metadata,
			LastUpdated: v.LastUpdated,
		}
	}

	return metrics
}

// GetAggregatedMetrics returns all aggregated metrics
func (ms *MetricsService) GetAggregatedMetrics() map[string]*AggregatedMetric {
	ms.aggMutex.RLock()
	defer ms.aggMutex.RUnlock()

	metrics := make(map[string]*AggregatedMetric)
	for k, v := range ms.aggregationData {
		metrics[k] = &AggregatedMetric{
			Name:        v.Name,
			Count:       v.Count,
			Sum:         v.Sum,
			Min:         v.Min,
			Max:         v.Max,
			Avg:         v.Avg,
			P95:         v.P95,
			P99:         v.P99,
			LastUpdated: v.LastUpdated,
		}
	}

	return metrics
}

// GetRealTimeMetrics returns all real-time metrics
func (ms *MetricsService) GetRealTimeMetrics() map[string]*RealTimeMetric {
	ms.rtMutex.RLock()
	defer ms.rtMutex.RUnlock()

	metrics := make(map[string]*RealTimeMetric)
	for k, v := range ms.realTimeMetrics {
		metrics[k] = &RealTimeMetric{
			Name:        v.Name,
			Value:       v.Value,
			Unit:        v.Unit,
			Labels:      v.Labels,
			Metadata:    v.Metadata,
			LastUpdated: v.LastUpdated,
		}
	}

	return metrics
}

// GetPerformanceData returns performance tracking data
func (ms *MetricsService) GetPerformanceData() map[string]*PerformanceTracker {
	ms.perfMutex.RLock()
	defer ms.perfMutex.RUnlock()

	perfData := make(map[string]*PerformanceTracker)
	for k, v := range ms.performanceTrackers {
		perfData[k] = &PerformanceTracker{
			Count:       v.Count,
			TotalTime:   v.TotalTime,
			MinTime:     v.MinTime,
			MaxTime:     v.MaxTime,
			LastUpdated: v.LastUpdated,
		}
	}

	return perfData
}

// TrackPerformance tracks performance for an operation
func (ms *MetricsService) TrackPerformance(operation string, duration time.Duration) {
	ms.perfMutex.Lock()
	defer ms.perfMutex.Unlock()

	tracker, exists := ms.performanceTrackers[operation]
	if !exists {
		tracker = &PerformanceTracker{
			MinTime:     duration,
			MaxTime:     duration,
			LastUpdated: time.Now(),
		}
		ms.performanceTrackers[operation] = tracker
	}

	tracker.Count++
	tracker.TotalTime += duration
	if duration < tracker.MinTime {
		tracker.MinTime = duration
	}
	if duration > tracker.MaxTime {
		tracker.MaxTime = duration
	}
	tracker.LastUpdated = time.Now()
}

// ExportMetrics exports metrics to various formats
func (ms *MetricsService) ExportMetrics(format string) ([]byte, error) {
	summary := ms.GetMetricsSummary()

	switch format {
	case "json":
		return json.MarshalIndent(summary, "", "  ")
	case "prometheus":
		return ms.exportPrometheusFormat(summary)
	default:
		return json.Marshal(summary)
	}
}

// exportPrometheusFormat exports metrics in Prometheus format
func (ms *MetricsService) exportPrometheusFormat(summary map[string]interface{}) ([]byte, error) {
	var output string

	// Export custom metrics
	if customMetrics, ok := summary["custom_metrics"].(map[string]*CustomMetric); ok {
		for name, metric := range customMetrics {
			output += fmt.Sprintf("# HELP %s %s\n", name, metric.Description)
			output += fmt.Sprintf("# TYPE %s %s\n", name, metric.Type)
			output += fmt.Sprintf("%s %f\n", name, metric.Value)
		}
	}

	// Export real-time metrics
	if realTimeMetrics, ok := summary["realtime_metrics"].(map[string]*RealTimeMetric); ok {
		for name, metric := range realTimeMetrics {
			output += fmt.Sprintf("# HELP %s %s\n", name, metric.Unit)
			output += fmt.Sprintf("# TYPE %s gauge\n", name)
			output += fmt.Sprintf("%s %f\n", name, metric.Value)
		}
	}

	return []byte(output), nil
}

// calculateAverage calculates the average of a slice of float64 values
func calculateAverage(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}

	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

// Stop stops the metrics service
func (ms *MetricsService) Stop() {
	ms.cancel()
}
