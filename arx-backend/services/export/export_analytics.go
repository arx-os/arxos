package export

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// ExportAnalyticsPeriod represents the time period for analytics
type ExportAnalyticsPeriod string

const (
	ExportAnalyticsPeriodHour  ExportAnalyticsPeriod = "hour"
	ExportAnalyticsPeriodDay   ExportAnalyticsPeriod = "day"
	ExportAnalyticsPeriodWeek  ExportAnalyticsPeriod = "week"
	ExportAnalyticsPeriodMonth ExportAnalyticsPeriod = "month"
	ExportAnalyticsPeriodYear  ExportAnalyticsPeriod = "year"
)

// ExportAnalyticsMetric represents a metric for export analytics
type ExportAnalyticsMetric struct {
	Period     ExportAnalyticsPeriod  `json:"period"`
	StartTime  time.Time              `json:"start_time"`
	EndTime    time.Time              `json:"end_time"`
	MetricName string                 `json:"metric_name"`
	Value      float64                `json:"value"`
	Count      int64                  `json:"count"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// ExportAnalyticsReport represents a comprehensive analytics report
type ExportAnalyticsReport struct {
	ReportID    string                `json:"report_id"`
	Period      ExportAnalyticsPeriod `json:"period"`
	StartTime   time.Time             `json:"start_time"`
	EndTime     time.Time             `json:"end_time"`
	GeneratedAt time.Time             `json:"generated_at"`

	// Summary metrics
	TotalJobs       int64         `json:"total_jobs"`
	CompletedJobs   int64         `json:"completed_jobs"`
	FailedJobs      int64         `json:"failed_jobs"`
	SuccessRate     float64       `json:"success_rate"`
	AverageDuration time.Duration `json:"average_duration"`

	// Performance metrics
	PerformanceMetrics map[string]ExportAnalyticsMetric `json:"performance_metrics"`

	// Format analytics
	FormatAnalytics map[string]FormatAnalytics `json:"format_analytics"`

	// Error analytics
	ErrorAnalytics map[string]ErrorAnalytics `json:"error_analytics"`

	// User analytics
	UserAnalytics map[string]UserAnalytics `json:"user_analytics"`

	// System analytics
	SystemAnalytics SystemAnalytics `json:"system_analytics"`
}

// FormatAnalytics represents analytics for a specific export format
type FormatAnalytics struct {
	Format          ExportFormat  `json:"format"`
	TotalJobs       int64         `json:"total_jobs"`
	CompletedJobs   int64         `json:"completed_jobs"`
	FailedJobs      int64         `json:"failed_jobs"`
	SuccessRate     float64       `json:"success_rate"`
	AverageSize     int64         `json:"average_size"`
	AverageDuration time.Duration `json:"average_duration"`
	PopularFeatures []string      `json:"popular_features"`
}

// ErrorAnalytics represents analytics for errors
type ErrorAnalytics struct {
	ErrorCode       string         `json:"error_code"`
	ErrorMessage    string         `json:"error_message"`
	OccurrenceCount int64          `json:"occurrence_count"`
	Percentage      float64        `json:"percentage"`
	LastOccurrence  time.Time      `json:"last_occurrence"`
	AffectedFormats []ExportFormat `json:"affected_formats"`
}

// UserAnalytics represents analytics for user activity
type UserAnalytics struct {
	UserID           string         `json:"user_id"`
	TotalJobs        int64          `json:"total_jobs"`
	CompletedJobs    int64          `json:"completed_jobs"`
	FailedJobs       int64          `json:"failed_jobs"`
	SuccessRate      float64        `json:"success_rate"`
	AverageDuration  time.Duration  `json:"average_duration"`
	PreferredFormats []ExportFormat `json:"preferred_formats"`
	LastActivity     time.Time      `json:"last_activity"`
}

// SystemAnalytics represents system-level analytics
type SystemAnalytics struct {
	PeakConcurrency   int64              `json:"peak_concurrency"`
	AverageLoad       float64            `json:"average_load"`
	ResourceUsage     ResourceUsage      `json:"resource_usage"`
	PerformanceTrends []PerformanceTrend `json:"performance_trends"`
}

// ResourceUsage represents system resource usage
type ResourceUsage struct {
	CPUUsage    float64 `json:"cpu_usage"`
	MemoryUsage float64 `json:"memory_usage"`
	DiskUsage   float64 `json:"disk_usage"`
	NetworkIO   float64 `json:"network_io"`
}

// PerformanceTrend represents a performance trend
type PerformanceTrend struct {
	MetricName string      `json:"metric_name"`
	Values     []float64   `json:"values"`
	Timestamps []time.Time `json:"timestamps"`
	Trend      string      `json:"trend"` // improving, declining, stable
}

// ExportAnalyticsConfig represents configuration for export analytics
type ExportAnalyticsConfig struct {
	RetentionPeriod   time.Duration `json:"retention_period"`
	AggregationPeriod time.Duration `json:"aggregation_period"`
	MaxDataPoints     int           `json:"max_data_points"`
	EnableRealTime    bool          `json:"enable_real_time"`
	EnablePredictions bool          `json:"enable_predictions"`
}

// ExportAnalyticsService provides comprehensive export analytics functionality
type ExportAnalyticsService struct {
	logger *zap.Logger
	mu     sync.RWMutex

	// Data storage
	metrics map[string][]ExportAnalyticsMetric
	reports map[string]*ExportAnalyticsReport

	// Configuration
	config *ExportAnalyticsConfig

	// Real-time tracking
	realTimeMetrics map[string]float64
	lastUpdate      time.Time
}

// NewExportAnalyticsService creates a new export analytics service
func NewExportAnalyticsService(logger *zap.Logger, config *ExportAnalyticsConfig) (*ExportAnalyticsService, error) {
	if config == nil {
		config = &ExportAnalyticsConfig{
			RetentionPeriod:   30 * 24 * time.Hour, // 30 days
			AggregationPeriod: 1 * time.Hour,
			MaxDataPoints:     1000,
			EnableRealTime:    true,
			EnablePredictions: false,
		}
	}

	eas := &ExportAnalyticsService{
		logger:          logger,
		metrics:         make(map[string][]ExportAnalyticsMetric),
		reports:         make(map[string]*ExportAnalyticsReport),
		config:          config,
		realTimeMetrics: make(map[string]float64),
		lastUpdate:      time.Now(),
	}

	// Start aggregation routine
	if config.EnableRealTime {
		go eas.aggregationRoutine()
	}

	logger.Info("Export analytics service initialized",
		zap.Duration("retention_period", config.RetentionPeriod),
		zap.Duration("aggregation_period", config.AggregationPeriod),
		zap.Int("max_data_points", config.MaxDataPoints))

	return eas, nil
}

// RecordMetric records a metric for analytics
func (eas *ExportAnalyticsService) RecordMetric(metricName string, value float64, metadata map[string]interface{}) error {
	eas.mu.Lock()
	defer eas.mu.Unlock()

	now := time.Now()
	metric := ExportAnalyticsMetric{
		Period:     ExportAnalyticsPeriodHour,
		StartTime:  now.Truncate(time.Hour),
		EndTime:    now.Truncate(time.Hour).Add(time.Hour),
		MetricName: metricName,
		Value:      value,
		Count:      1,
		Metadata:   metadata,
	}

	eas.metrics[metricName] = append(eas.metrics[metricName], metric)

	// Update real-time metrics
	eas.realTimeMetrics[metricName] = value
	eas.lastUpdate = now

	// Limit data points
	if len(eas.metrics[metricName]) > eas.config.MaxDataPoints {
		eas.metrics[metricName] = eas.metrics[metricName][len(eas.metrics[metricName])-eas.config.MaxDataPoints:]
	}

	return nil
}

// RecordJobCompletion records the completion of an export job
func (eas *ExportAnalyticsService) RecordJobCompletion(job *ExportJob, result *ExportResult, duration time.Duration) error {
	// Record basic metrics
	if err := eas.RecordMetric("job_completion", 1.0, map[string]interface{}{
		"job_id":    job.ID,
		"format":    job.Format,
		"user_id":   job.UserID,
		"duration":  duration.Seconds(),
		"file_size": result.FileSize,
	}); err != nil {
		return err
	}

	// Record format-specific metrics
	formatMetric := fmt.Sprintf("format_%s_completion", job.Format)
	if err := eas.RecordMetric(formatMetric, 1.0, map[string]interface{}{
		"duration":  duration.Seconds(),
		"file_size": result.FileSize,
	}); err != nil {
		return err
	}

	// Record user-specific metrics
	userMetric := fmt.Sprintf("user_%s_completion", job.UserID)
	if err := eas.RecordMetric(userMetric, 1.0, map[string]interface{}{
		"duration": duration.Seconds(),
		"format":   job.Format,
	}); err != nil {
		return err
	}

	// Record duration metrics
	if err := eas.RecordMetric("job_duration", duration.Seconds(), map[string]interface{}{
		"format": job.Format,
	}); err != nil {
		return err
	}

	return nil
}

// RecordJobFailure records the failure of an export job
func (eas *ExportAnalyticsService) RecordJobFailure(job *ExportJob, err error, duration time.Duration) error {
	// Record basic failure metrics
	if err := eas.RecordMetric("job_failure", 1.0, map[string]interface{}{
		"job_id":   job.ID,
		"format":   job.Format,
		"user_id":  job.UserID,
		"duration": duration.Seconds(),
		"error":    err.Error(),
	}); err != nil {
		return err
	}

	// Record format-specific failure metrics
	formatMetric := fmt.Sprintf("format_%s_failure", job.Format)
	if err := eas.RecordMetric(formatMetric, 1.0, map[string]interface{}{
		"duration": duration.Seconds(),
		"error":    err.Error(),
	}); err != nil {
		return err
	}

	// Record user-specific failure metrics
	userMetric := fmt.Sprintf("user_%s_failure", job.UserID)
	if err := eas.RecordMetric(userMetric, 1.0, map[string]interface{}{
		"duration": duration.Seconds(),
		"format":   job.Format,
		"error":    err.Error(),
	}); err != nil {
		return err
	}

	return nil
}

// GenerateReport generates a comprehensive analytics report
func (eas *ExportAnalyticsService) GenerateReport(period ExportAnalyticsPeriod, startTime, endTime time.Time) (*ExportAnalyticsReport, error) {
	eas.mu.RLock()
	defer eas.mu.RUnlock()

	report := &ExportAnalyticsReport{
		ReportID:           fmt.Sprintf("report_%s_%d", period, time.Now().Unix()),
		Period:             period,
		StartTime:          startTime,
		EndTime:            endTime,
		GeneratedAt:        time.Now(),
		PerformanceMetrics: make(map[string]ExportAnalyticsMetric),
		FormatAnalytics:    make(map[string]FormatAnalytics),
		ErrorAnalytics:     make(map[string]ErrorAnalytics),
		UserAnalytics:      make(map[string]UserAnalytics),
	}

	// Calculate summary metrics
	eas.calculateSummaryMetrics(report, startTime, endTime)

	// Calculate performance metrics
	eas.calculatePerformanceMetrics(report, startTime, endTime)

	// Calculate format analytics
	eas.calculateFormatAnalytics(report, startTime, endTime)

	// Calculate error analytics
	eas.calculateErrorAnalytics(report, startTime, endTime)

	// Calculate user analytics
	eas.calculateUserAnalytics(report, startTime, endTime)

	// Calculate system analytics
	eas.calculateSystemAnalytics(report, startTime, endTime)

	// Store report
	eas.reports[report.ReportID] = report

	eas.logger.Info("Generated analytics report",
		zap.String("report_id", report.ReportID),
		zap.String("period", string(period)),
		zap.Time("start_time", startTime),
		zap.Time("end_time", endTime),
		zap.Int64("total_jobs", report.TotalJobs),
		zap.Float64("success_rate", report.SuccessRate))

	return report, nil
}

// GetMetrics retrieves metrics for a specific period
func (eas *ExportAnalyticsService) GetMetrics(metricName string, period ExportAnalyticsPeriod, startTime, endTime time.Time) ([]ExportAnalyticsMetric, error) {
	eas.mu.RLock()
	defer eas.mu.RUnlock()

	metrics, exists := eas.metrics[metricName]
	if !exists {
		return []ExportAnalyticsMetric{}, nil
	}

	var filteredMetrics []ExportAnalyticsMetric
	for _, metric := range metrics {
		if metric.StartTime.After(startTime) && metric.EndTime.Before(endTime) {
			filteredMetrics = append(filteredMetrics, metric)
		}
	}

	return filteredMetrics, nil
}

// GetRealTimeMetrics returns current real-time metrics
func (eas *ExportAnalyticsService) GetRealTimeMetrics() map[string]float64 {
	eas.mu.RLock()
	defer eas.mu.RUnlock()

	result := make(map[string]float64)
	for key, value := range eas.realTimeMetrics {
		result[key] = value
	}

	return result
}

// GetReport retrieves a specific report
func (eas *ExportAnalyticsService) GetReport(reportID string) (*ExportAnalyticsReport, error) {
	eas.mu.RLock()
	defer eas.mu.RUnlock()

	report, exists := eas.reports[reportID]
	if !exists {
		return nil, fmt.Errorf("report %s not found", reportID)
	}

	return report, nil
}

// GetReports retrieves all reports
func (eas *ExportAnalyticsService) GetReports() map[string]*ExportAnalyticsReport {
	eas.mu.RLock()
	defer eas.mu.RUnlock()

	result := make(map[string]*ExportAnalyticsReport)
	for reportID, report := range eas.reports {
		result[reportID] = report
	}

	return result
}

// calculateSummaryMetrics calculates summary metrics for the report
func (eas *ExportAnalyticsService) calculateSummaryMetrics(report *ExportAnalyticsReport, startTime, endTime time.Time) {
	completionMetrics, _ := eas.GetMetrics("job_completion", report.Period, startTime, endTime)
	failureMetrics, _ := eas.GetMetrics("job_failure", report.Period, startTime, endTime)
	durationMetrics, _ := eas.GetMetrics("job_duration", report.Period, startTime, endTime)

	report.TotalJobs = int64(len(completionMetrics) + len(failureMetrics))
	report.CompletedJobs = int64(len(completionMetrics))
	report.FailedJobs = int64(len(failureMetrics))

	if report.TotalJobs > 0 {
		report.SuccessRate = float64(report.CompletedJobs) / float64(report.TotalJobs) * 100
	}

	// Calculate average duration
	var totalDuration float64
	for _, metric := range durationMetrics {
		totalDuration += metric.Value
	}
	if len(durationMetrics) > 0 {
		report.AverageDuration = time.Duration(totalDuration/float64(len(durationMetrics))) * time.Second
	}
}

// calculatePerformanceMetrics calculates performance metrics for the report
func (eas *ExportAnalyticsService) calculatePerformanceMetrics(report *ExportAnalyticsReport, startTime, endTime time.Time) {
	// Calculate various performance metrics
	metrics := []string{"job_completion", "job_failure", "job_duration"}

	for _, metricName := range metrics {
		metrics, _ := eas.GetMetrics(metricName, report.Period, startTime, endTime)
		if len(metrics) > 0 {
			// Aggregate metrics
			var totalValue float64
			var totalCount int64
			for _, metric := range metrics {
				totalValue += metric.Value
				totalCount += metric.Count
			}

			aggregatedMetric := ExportAnalyticsMetric{
				Period:     report.Period,
				StartTime:  startTime,
				EndTime:    endTime,
				MetricName: metricName,
				Value:      totalValue,
				Count:      totalCount,
			}

			report.PerformanceMetrics[metricName] = aggregatedMetric
		}
	}
}

// calculateFormatAnalytics calculates format-specific analytics
func (eas *ExportAnalyticsService) calculateFormatAnalytics(report *ExportAnalyticsReport, startTime, endTime time.Time) {
	// Get all format completion metrics
	for metricName, metrics := range eas.metrics {
		if len(metricName) > 14 && metricName[:14] == "format_" && metricName[len(metricName)-10:] == "_completion" {
			format := ExportFormat(metricName[7 : len(metricName)-10])

			completionMetrics, _ := eas.GetMetrics(metricName, report.Period, startTime, endTime)
			failureMetricName := fmt.Sprintf("format_%s_failure", format)
			failureMetrics, _ := eas.GetMetrics(failureMetricName, report.Period, startTime, endTime)

			totalJobs := int64(len(completionMetrics) + len(failureMetrics))
			completedJobs := int64(len(completionMetrics))
			failedJobs := int64(len(failureMetrics))

			var successRate float64
			if totalJobs > 0 {
				successRate = float64(completedJobs) / float64(totalJobs) * 100
			}

			// Calculate average duration and size
			var totalDuration float64
			var totalSize int64
			for _, metric := range completionMetrics {
				if duration, ok := metric.Metadata["duration"].(float64); ok {
					totalDuration += duration
				}
				if size, ok := metric.Metadata["file_size"].(int64); ok {
					totalSize += size
				}
			}

			var averageDuration time.Duration
			var averageSize int64
			if len(completionMetrics) > 0 {
				averageDuration = time.Duration(totalDuration/float64(len(completionMetrics))) * time.Second
				averageSize = totalSize / int64(len(completionMetrics))
			}

			formatAnalytics := FormatAnalytics{
				Format:          format,
				TotalJobs:       totalJobs,
				CompletedJobs:   completedJobs,
				FailedJobs:      failedJobs,
				SuccessRate:     successRate,
				AverageSize:     averageSize,
				AverageDuration: averageDuration,
				PopularFeatures: []string{}, // TODO: Implement feature tracking
			}

			report.FormatAnalytics[string(format)] = formatAnalytics
		}
	}
}

// calculateErrorAnalytics calculates error analytics
func (eas *ExportAnalyticsService) calculateErrorAnalytics(report *ExportAnalyticsReport, startTime, endTime time.Time) {
	// Get failure metrics and analyze errors
	failureMetrics, _ := eas.GetMetrics("job_failure", report.Period, startTime, endTime)

	errorCounts := make(map[string]int64)
	errorMessages := make(map[string]string)
	errorLastOccurrence := make(map[string]time.Time)
	errorFormats := make(map[string][]ExportFormat)

	for _, metric := range failureMetrics {
		if errorMsg, ok := metric.Metadata["error"].(string); ok {
			errorCounts[errorMsg]++
			errorMessages[errorMsg] = errorMsg

			if metric.Timestamp.After(errorLastOccurrence[errorMsg]) {
				errorLastOccurrence[errorMsg] = metric.Timestamp
			}

			if format, ok := metric.Metadata["format"].(ExportFormat); ok {
				errorFormats[errorMsg] = append(errorFormats[errorMsg], format)
			}
		}
	}

	totalFailures := int64(len(failureMetrics))

	for errorMsg, count := range errorCounts {
		percentage := float64(count) / float64(totalFailures) * 100

		errorAnalytics := ErrorAnalytics{
			ErrorCode:       "CUSTOM_ERROR",
			ErrorMessage:    errorMsg,
			OccurrenceCount: count,
			Percentage:      percentage,
			LastOccurrence:  errorLastOccurrence[errorMsg],
			AffectedFormats: errorFormats[errorMsg],
		}

		report.ErrorAnalytics[errorMsg] = errorAnalytics
	}
}

// calculateUserAnalytics calculates user-specific analytics
func (eas *ExportAnalyticsService) calculateUserAnalytics(report *ExportAnalyticsReport, startTime, endTime time.Time) {
	// Get all user completion metrics
	for metricName, metrics := range eas.metrics {
		if len(metricName) > 12 && metricName[:5] == "user_" && metricName[len(metricName)-10:] == "_completion" {
			userID := metricName[5 : len(metricName)-10]

			completionMetrics, _ := eas.GetMetrics(metricName, report.Period, startTime, endTime)
			failureMetricName := fmt.Sprintf("user_%s_failure", userID)
			failureMetrics, _ := eas.GetMetrics(failureMetricName, report.Period, startTime, endTime)

			totalJobs := int64(len(completionMetrics) + len(failureMetrics))
			completedJobs := int64(len(completionMetrics))
			failedJobs := int64(len(failureMetrics))

			var successRate float64
			if totalJobs > 0 {
				successRate = float64(completedJobs) / float64(totalJobs) * 100
			}

			// Calculate average duration and preferred formats
			var totalDuration float64
			formatCounts := make(map[ExportFormat]int)
			var lastActivity time.Time

			for _, metric := range completionMetrics {
				if duration, ok := metric.Metadata["duration"].(float64); ok {
					totalDuration += duration
				}
				if format, ok := metric.Metadata["format"].(ExportFormat); ok {
					formatCounts[format]++
				}
				if metric.Timestamp.After(lastActivity) {
					lastActivity = metric.Timestamp
				}
			}

			var averageDuration time.Duration
			if len(completionMetrics) > 0 {
				averageDuration = time.Duration(totalDuration/float64(len(completionMetrics))) * time.Second
			}

			// Find preferred formats
			var preferredFormats []ExportFormat
			for format, count := range formatCounts {
				if count > 0 {
					preferredFormats = append(preferredFormats, format)
				}
			}

			userAnalytics := UserAnalytics{
				UserID:           userID,
				TotalJobs:        totalJobs,
				CompletedJobs:    completedJobs,
				FailedJobs:       failedJobs,
				SuccessRate:      successRate,
				AverageDuration:  averageDuration,
				PreferredFormats: preferredFormats,
				LastActivity:     lastActivity,
			}

			report.UserAnalytics[userID] = userAnalytics
		}
	}
}

// calculateSystemAnalytics calculates system-level analytics
func (eas *ExportAnalyticsService) calculateSystemAnalytics(report *ExportAnalyticsReport, startTime, endTime time.Time) {
	// Calculate system metrics
	concurrencyMetrics, _ := eas.GetMetrics("concurrent_jobs", report.Period, startTime, endTime)
	loadMetrics, _ := eas.GetMetrics("system_load", report.Period, startTime, endTime)

	// Find peak concurrency
	var peakConcurrency int64
	for _, metric := range concurrencyMetrics {
		if int64(metric.Value) > peakConcurrency {
			peakConcurrency = int64(metric.Value)
		}
	}

	// Calculate average load
	var totalLoad float64
	for _, metric := range loadMetrics {
		totalLoad += metric.Value
	}
	var averageLoad float64
	if len(loadMetrics) > 0 {
		averageLoad = totalLoad / float64(len(loadMetrics))
	}

	// Create performance trends
	performanceTrends := []PerformanceTrend{
		{
			MetricName: "job_completion_rate",
			Values:     []float64{report.SuccessRate},
			Timestamps: []time.Time{time.Now()},
			Trend:      "stable", // TODO: Calculate actual trend
		},
	}

	systemAnalytics := SystemAnalytics{
		PeakConcurrency:   peakConcurrency,
		AverageLoad:       averageLoad,
		ResourceUsage:     ResourceUsage{}, // TODO: Implement resource tracking
		PerformanceTrends: performanceTrends,
	}

	report.SystemAnalytics = systemAnalytics
}

// aggregationRoutine runs the aggregation routine
func (eas *ExportAnalyticsService) aggregationRoutine() {
	ticker := time.NewTicker(eas.config.AggregationPeriod)
	defer ticker.Stop()

	for range ticker.C {
		eas.aggregateMetrics()
	}
}

// aggregateMetrics aggregates metrics for the current period
func (eas *ExportAnalyticsService) aggregateMetrics() {
	eas.mu.Lock()
	defer eas.mu.Unlock()

	now := time.Now()
	periodStart := now.Truncate(eas.config.AggregationPeriod)

	// Aggregate metrics for each metric type
	for metricName, metrics := range eas.metrics {
		var periodMetrics []ExportAnalyticsMetric
		var totalValue float64
		var totalCount int64

		for _, metric := range metrics {
			if metric.StartTime.Equal(periodStart) {
				totalValue += metric.Value
				totalCount += metric.Count
			}
		}

		if totalCount > 0 {
			aggregatedMetric := ExportAnalyticsMetric{
				Period:     ExportAnalyticsPeriodHour,
				StartTime:  periodStart,
				EndTime:    periodStart.Add(eas.config.AggregationPeriod),
				MetricName: metricName,
				Value:      totalValue,
				Count:      totalCount,
			}

			periodMetrics = append(periodMetrics, aggregatedMetric)
		}

		// Update metrics with aggregated data
		if len(periodMetrics) > 0 {
			eas.metrics[metricName] = append(eas.metrics[metricName], periodMetrics...)
		}
	}
}

// ExportReportToJSON converts a report to JSON
func (eas *ExportAnalyticsService) ExportReportToJSON(report *ExportAnalyticsReport) ([]byte, error) {
	return json.Marshal(report)
}

// ImportReportFromJSON imports a report from JSON
func (eas *ExportAnalyticsService) ImportReportFromJSON(data []byte) (*ExportAnalyticsReport, error) {
	var report ExportAnalyticsReport
	if err := json.Unmarshal(data, &report); err != nil {
		return nil, err
	}
	return &report, nil
}

// ExportMetricsToJSON converts metrics to JSON
func (eas *ExportAnalyticsService) ExportMetricsToJSON(metrics []ExportAnalyticsMetric) ([]byte, error) {
	return json.Marshal(metrics)
}

// ImportMetricsFromJSON imports metrics from JSON
func (eas *ExportAnalyticsService) ImportMetricsFromJSON(data []byte) ([]ExportAnalyticsMetric, error) {
	var metrics []ExportAnalyticsMetric
	if err := json.Unmarshal(data, &metrics); err != nil {
		return nil, err
	}
	return metrics, nil
}
