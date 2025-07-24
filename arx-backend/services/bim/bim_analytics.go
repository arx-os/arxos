package bim

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// AnalyticsPeriod represents the time period for analytics
type AnalyticsPeriod string

const (
	AnalyticsPeriodHour  AnalyticsPeriod = "hour"
	AnalyticsPeriodDay   AnalyticsPeriod = "day"
	AnalyticsPeriodWeek  AnalyticsPeriod = "week"
	AnalyticsPeriodMonth AnalyticsPeriod = "month"
	AnalyticsPeriodYear  AnalyticsPeriod = "year"
)

// AnalyticsMetric represents a metric for BIM analytics
type AnalyticsMetric struct {
	Period     AnalyticsPeriod        `json:"period"`
	StartTime  time.Time              `json:"start_time"`
	EndTime    time.Time              `json:"end_time"`
	MetricName string                 `json:"metric_name"`
	Value      float64                `json:"value"`
	Count      int64                  `json:"count"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// BIMAnalyticsReport represents a comprehensive analytics report
type BIMAnalyticsReport struct {
	ReportID    string          `json:"report_id"`
	Period      AnalyticsPeriod `json:"period"`
	StartTime   time.Time       `json:"start_time"`
	EndTime     time.Time       `json:"end_time"`
	GeneratedAt time.Time       `json:"generated_at"`

	// Summary metrics
	TotalModels    int64 `json:"total_models"`
	TotalElements  int64 `json:"total_elements"`
	ActiveModels   int64 `json:"active_models"`
	ActiveElements int64 `json:"active_elements"`

	// Performance metrics
	PerformanceMetrics map[string]AnalyticsMetric `json:"performance_metrics"`

	// Element analytics
	ElementAnalytics map[string]ElementAnalytics `json:"element_analytics"`

	// System analytics
	SystemAnalytics map[string]SystemAnalytics `json:"system_analytics"`

	// User analytics
	UserAnalytics map[string]UserAnalytics `json:"user_analytics"`

	// Validation analytics
	ValidationAnalytics ValidationAnalytics `json:"validation_analytics"`

	// Transformation analytics
	TransformationAnalytics TransformationAnalytics `json:"transformation_analytics"`
}

// ElementAnalytics represents analytics for a specific element type
type ElementAnalytics struct {
	ElementType    BIMElementType    `json:"element_type"`
	TotalCount     int64             `json:"total_count"`
	ActiveCount    int64             `json:"active_count"`
	InactiveCount  int64             `json:"inactive_count"`
	AverageSize    float64           `json:"average_size"`
	PopularSystems []BIMSystemType   `json:"popular_systems"`
	CreationTrend  []TimeSeriesPoint `json:"creation_trend"`
}

// SystemAnalytics represents analytics for a specific system type
type SystemAnalytics struct {
	SystemType         BIMSystemType      `json:"system_type"`
	TotalElements      int64              `json:"total_elements"`
	ActiveElements     int64              `json:"active_elements"`
	ElementTypes       []BIMElementType   `json:"element_types"`
	PerformanceMetrics map[string]float64 `json:"performance_metrics"`
	HealthScore        float64            `json:"health_score"`
}

// UserAnalytics represents analytics for user activity
type UserAnalytics struct {
	UserID           string          `json:"user_id"`
	TotalModels      int64           `json:"total_models"`
	ActiveModels     int64           `json:"active_models"`
	TotalElements    int64           `json:"total_elements"`
	ActiveElements   int64           `json:"active_elements"`
	LastActivity     time.Time       `json:"last_activity"`
	PreferredSystems []BIMSystemType `json:"preferred_systems"`
}

// ValidationAnalytics represents analytics for validation operations
type ValidationAnalytics struct {
	TotalValidations      int64             `json:"total_validations"`
	SuccessfulValidations int64             `json:"successful_validations"`
	FailedValidations     int64             `json:"failed_validations"`
	SuccessRate           float64           `json:"success_rate"`
	AverageValidationTime float64           `json:"average_validation_time"`
	CommonErrors          map[string]int64  `json:"common_errors"`
	ValidationTrends      []TimeSeriesPoint `json:"validation_trends"`
}

// TransformationAnalytics represents analytics for transformation operations
type TransformationAnalytics struct {
	TotalTransformations      int64             `json:"total_transformations"`
	SuccessfulTransformations int64             `json:"successful_transformations"`
	FailedTransformations     int64             `json:"failed_transformations"`
	SuccessRate               float64           `json:"success_rate"`
	AverageTransformationTime float64           `json:"average_transformation_time"`
	PopularTransformations    map[string]int64  `json:"popular_transformations"`
	TransformationTrends      []TimeSeriesPoint `json:"transformation_trends"`
}

// TimeSeriesPoint represents a point in a time series
type TimeSeriesPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
	Count     int64     `json:"count"`
}

// BIMAnalyticsConfig represents configuration for BIM analytics
type BIMAnalyticsConfig struct {
	RetentionPeriod   time.Duration `json:"retention_period"`
	AggregationPeriod time.Duration `json:"aggregation_period"`
	MaxDataPoints     int           `json:"max_data_points"`
	EnableRealTime    bool          `json:"enable_real_time"`
	EnablePredictions bool          `json:"enable_predictions"`
}

// BIMAnalytics provides comprehensive BIM analytics functionality
type BIMAnalytics struct {
	logger *zap.Logger
	mu     sync.RWMutex

	// Data storage
	metrics map[string][]AnalyticsMetric
	reports map[string]*BIMAnalyticsReport

	// Configuration
	config *BIMAnalyticsConfig

	// Real-time tracking
	realTimeMetrics map[string]float64
	lastUpdate      time.Time
}

// NewBIMAnalytics creates a new BIM analytics service
func NewBIMAnalytics(logger *zap.Logger, config *BIMAnalyticsConfig) (*BIMAnalytics, error) {
	if config == nil {
		config = &BIMAnalyticsConfig{
			RetentionPeriod:   30 * 24 * time.Hour, // 30 days
			AggregationPeriod: 1 * time.Hour,
			MaxDataPoints:     1000,
			EnableRealTime:    true,
			EnablePredictions: false,
		}
	}

	ba := &BIMAnalytics{
		logger:          logger,
		metrics:         make(map[string][]AnalyticsMetric),
		reports:         make(map[string]*BIMAnalyticsReport),
		config:          config,
		realTimeMetrics: make(map[string]float64),
		lastUpdate:      time.Now(),
	}

	// Start aggregation routine
	if config.EnableRealTime {
		go ba.aggregationRoutine()
	}

	logger.Info("BIM analytics service initialized",
		zap.Duration("retention_period", config.RetentionPeriod),
		zap.Duration("aggregation_period", config.AggregationPeriod),
		zap.Int("max_data_points", config.MaxDataPoints))

	return ba, nil
}

// RecordMetric records a metric for analytics
func (ba *BIMAnalytics) RecordMetric(metricName string, value float64, metadata map[string]interface{}) error {
	ba.mu.Lock()
	defer ba.mu.Unlock()

	now := time.Now()
	metric := AnalyticsMetric{
		Period:     AnalyticsPeriodHour,
		StartTime:  now.Truncate(time.Hour),
		EndTime:    now.Truncate(time.Hour).Add(time.Hour),
		MetricName: metricName,
		Value:      value,
		Count:      1,
		Metadata:   metadata,
	}

	ba.metrics[metricName] = append(ba.metrics[metricName], metric)

	// Update real-time metrics
	ba.realTimeMetrics[metricName] = value
	ba.lastUpdate = now

	// Limit data points
	if len(ba.metrics[metricName]) > ba.config.MaxDataPoints {
		ba.metrics[metricName] = ba.metrics[metricName][len(ba.metrics[metricName])-ba.config.MaxDataPoints:]
	}

	return nil
}

// RecordModelCreated records the creation of a BIM model
func (ba *BIMAnalytics) RecordModelCreated(model *BIMModel) error {
	if err := ba.RecordMetric("model_created", 1.0, map[string]interface{}{
		"model_id":   model.ID,
		"model_name": model.Name,
		"version":    model.Version,
	}); err != nil {
		return err
	}

	// Record model size metrics
	if err := ba.RecordMetric("model_elements", float64(len(model.Elements)), map[string]interface{}{
		"model_id": model.ID,
	}); err != nil {
		return err
	}

	return nil
}

// RecordElementAdded records the addition of a BIM element
func (ba *BIMAnalytics) RecordElementAdded(element *BIMElement) error {
	// Record basic element metrics
	if err := ba.RecordMetric("element_added", 1.0, map[string]interface{}{
		"element_id":   element.ID,
		"element_type": string(element.Type),
		"system_type":  string(element.SystemType),
		"status":       string(element.Status),
	}); err != nil {
		return err
	}

	// Record element type metrics
	typeMetric := fmt.Sprintf("element_type_%s", element.Type)
	if err := ba.RecordMetric(typeMetric, 1.0, map[string]interface{}{
		"system_type": string(element.SystemType),
	}); err != nil {
		return err
	}

	// Record system type metrics
	systemMetric := fmt.Sprintf("system_type_%s", element.SystemType)
	if err := ba.RecordMetric(systemMetric, 1.0, map[string]interface{}{
		"element_type": string(element.Type),
	}); err != nil {
		return err
	}

	return nil
}

// RecordElementUpdated records the update of a BIM element
func (ba *BIMAnalytics) RecordElementUpdated(element *BIMElement) error {
	if err := ba.RecordMetric("element_updated", 1.0, map[string]interface{}{
		"element_id":   element.ID,
		"element_type": string(element.Type),
		"system_type":  string(element.SystemType),
		"status":       string(element.Status),
	}); err != nil {
		return err
	}

	return nil
}

// RecordElementDeleted records the deletion of a BIM element
func (ba *BIMAnalytics) RecordElementDeleted(element *BIMElement) error {
	if err := ba.RecordMetric("element_deleted", 1.0, map[string]interface{}{
		"element_id":   element.ID,
		"element_type": string(element.Type),
		"system_type":  string(element.SystemType),
	}); err != nil {
		return err
	}

	return nil
}

// RecordValidation records a validation operation
func (ba *BIMAnalytics) RecordValidation(elementID string, success bool, duration time.Duration, errors []string) error {
	successValue := 0.0
	if success {
		successValue = 1.0
	}

	if err := ba.RecordMetric("validation_operation", successValue, map[string]interface{}{
		"element_id":  elementID,
		"success":     success,
		"duration_ms": duration.Milliseconds(),
		"error_count": len(errors),
	}); err != nil {
		return err
	}

	// Record validation time
	if err := ba.RecordMetric("validation_time", float64(duration.Milliseconds()), map[string]interface{}{
		"element_id": elementID,
		"success":    success,
	}); err != nil {
		return err
	}

	return nil
}

// RecordTransformation records a transformation operation
func (ba *BIMAnalytics) RecordTransformation(elementID string, transformationType string, success bool, duration time.Duration) error {
	successValue := 0.0
	if success {
		successValue = 1.0
	}

	if err := ba.RecordMetric("transformation_operation", successValue, map[string]interface{}{
		"element_id":          elementID,
		"transformation_type": transformationType,
		"success":             success,
		"duration_ms":         duration.Milliseconds(),
	}); err != nil {
		return err
	}

	// Record transformation time
	if err := ba.RecordMetric("transformation_time", float64(duration.Milliseconds()), map[string]interface{}{
		"element_id":          elementID,
		"transformation_type": transformationType,
		"success":             success,
	}); err != nil {
		return err
	}

	// Record transformation type metrics
	typeMetric := fmt.Sprintf("transformation_type_%s", transformationType)
	if err := ba.RecordMetric(typeMetric, successValue, map[string]interface{}{
		"element_id": elementID,
	}); err != nil {
		return err
	}

	return nil
}

// GenerateReport generates a comprehensive analytics report
func (ba *BIMAnalytics) GenerateReport(period AnalyticsPeriod, startTime, endTime time.Time) (*BIMAnalyticsReport, error) {
	ba.mu.RLock()
	defer ba.mu.RUnlock()

	report := &BIMAnalyticsReport{
		ReportID:           fmt.Sprintf("report_%s_%d", period, time.Now().Unix()),
		Period:             period,
		StartTime:          startTime,
		EndTime:            endTime,
		GeneratedAt:        time.Now(),
		PerformanceMetrics: make(map[string]AnalyticsMetric),
		ElementAnalytics:   make(map[string]ElementAnalytics),
		SystemAnalytics:    make(map[string]SystemAnalytics),
		UserAnalytics:      make(map[string]UserAnalytics),
	}

	// Calculate summary metrics
	ba.calculateSummaryMetrics(report, startTime, endTime)

	// Calculate performance metrics
	ba.calculatePerformanceMetrics(report, startTime, endTime)

	// Calculate element analytics
	ba.calculateElementAnalytics(report, startTime, endTime)

	// Calculate system analytics
	ba.calculateSystemAnalytics(report, startTime, endTime)

	// Calculate user analytics
	ba.calculateUserAnalytics(report, startTime, endTime)

	// Calculate validation analytics
	ba.calculateValidationAnalytics(report, startTime, endTime)

	// Calculate transformation analytics
	ba.calculateTransformationAnalytics(report, startTime, endTime)

	// Store report
	ba.reports[report.ReportID] = report

	ba.logger.Info("Generated BIM analytics report",
		zap.String("report_id", report.ReportID),
		zap.String("period", string(period)),
		zap.Time("start_time", startTime),
		zap.Time("end_time", endTime),
		zap.Int64("total_models", report.TotalModels),
		zap.Int64("total_elements", report.TotalElements))

	return report, nil
}

// GetMetrics retrieves metrics for a specific period
func (ba *BIMAnalytics) GetMetrics(metricName string, period AnalyticsPeriod, startTime, endTime time.Time) ([]AnalyticsMetric, error) {
	ba.mu.RLock()
	defer ba.mu.RUnlock()

	metrics, exists := ba.metrics[metricName]
	if !exists {
		return []AnalyticsMetric{}, nil
	}

	var filteredMetrics []AnalyticsMetric
	for _, metric := range metrics {
		if metric.StartTime.After(startTime) && metric.EndTime.Before(endTime) {
			filteredMetrics = append(filteredMetrics, metric)
		}
	}

	return filteredMetrics, nil
}

// GetRealTimeMetrics returns current real-time metrics
func (ba *BIMAnalytics) GetRealTimeMetrics() map[string]float64 {
	ba.mu.RLock()
	defer ba.mu.RUnlock()

	result := make(map[string]float64)
	for key, value := range ba.realTimeMetrics {
		result[key] = value
	}

	return result
}

// GetReport retrieves a specific report
func (ba *BIMAnalytics) GetReport(reportID string) (*BIMAnalyticsReport, error) {
	ba.mu.RLock()
	defer ba.mu.RUnlock()

	report, exists := ba.reports[reportID]
	if !exists {
		return nil, fmt.Errorf("report %s not found", reportID)
	}

	return report, nil
}

// GetReports retrieves all reports
func (ba *BIMAnalytics) GetReports() map[string]*BIMAnalyticsReport {
	ba.mu.RLock()
	defer ba.mu.RUnlock()

	result := make(map[string]*BIMAnalyticsReport)
	for reportID, report := range ba.reports {
		result[reportID] = report
	}

	return result
}

// calculateSummaryMetrics calculates summary metrics for the report
func (ba *BIMAnalytics) calculateSummaryMetrics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	modelMetrics, _ := ba.GetMetrics("model_created", report.Period, startTime, endTime)
	elementMetrics, _ := ba.GetMetrics("element_added", report.Period, startTime, endTime)

	report.TotalModels = int64(len(modelMetrics))
	report.TotalElements = int64(len(elementMetrics))
	report.ActiveModels = report.TotalModels     // Simplified - would need more complex logic
	report.ActiveElements = report.TotalElements // Simplified - would need more complex logic
}

// calculatePerformanceMetrics calculates performance metrics for the report
func (ba *BIMAnalytics) calculatePerformanceMetrics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	// Calculate various performance metrics
	metrics := []string{"model_created", "element_added", "element_updated", "element_deleted"}

	for _, metricName := range metrics {
		metrics, _ := ba.GetMetrics(metricName, report.Period, startTime, endTime)
		if len(metrics) > 0 {
			// Aggregate metrics
			var totalValue float64
			var totalCount int64
			for _, metric := range metrics {
				totalValue += metric.Value
				totalCount += metric.Count
			}

			aggregatedMetric := AnalyticsMetric{
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

// calculateElementAnalytics calculates element-specific analytics
func (ba *BIMAnalytics) calculateElementAnalytics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	// Get all element type metrics
	for metricName, metrics := range ba.metrics {
		if len(metricName) > 13 && metricName[:13] == "element_type_" {
			elementType := BIMElementType(metricName[13:])

			addedMetrics, _ := ba.GetMetrics(metricName, report.Period, startTime, endTime)
			deletedMetricName := fmt.Sprintf("element_deleted_%s", elementType)
			deletedMetrics, _ := ba.GetMetrics(deletedMetricName, report.Period, startTime, endTime)

			totalCount := int64(len(addedMetrics))
			deletedCount := int64(len(deletedMetrics))
			activeCount := totalCount - deletedCount

			elementAnalytics := ElementAnalytics{
				ElementType:    elementType,
				TotalCount:     totalCount,
				ActiveCount:    activeCount,
				InactiveCount:  deletedCount,
				AverageSize:    0.0,                 // Would need geometry analysis
				PopularSystems: []BIMSystemType{},   // Would need system analysis
				CreationTrend:  []TimeSeriesPoint{}, // Would need time series analysis
			}

			report.ElementAnalytics[string(elementType)] = elementAnalytics
		}
	}
}

// calculateSystemAnalytics calculates system-specific analytics
func (ba *BIMAnalytics) calculateSystemAnalytics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	// Get all system type metrics
	for metricName, metrics := range ba.metrics {
		if len(metricName) > 12 && metricName[:12] == "system_type_" {
			systemType := BIMSystemType(metricName[12:])

			addedMetrics, _ := ba.GetMetrics(metricName, report.Period, startTime, endTime)

			totalElements := int64(len(addedMetrics))
			activeElements := totalElements // Simplified

			systemAnalytics := SystemAnalytics{
				SystemType:         systemType,
				TotalElements:      totalElements,
				ActiveElements:     activeElements,
				ElementTypes:       []BIMElementType{}, // Would need element type analysis
				PerformanceMetrics: make(map[string]float64),
				HealthScore:        1.0, // Would need health analysis
			}

			report.SystemAnalytics[string(systemType)] = systemAnalytics
		}
	}
}

// calculateUserAnalytics calculates user-specific analytics
func (ba *BIMAnalytics) calculateUserAnalytics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	// This would require user tracking data
	// For now, we'll create placeholder analytics
	userAnalytics := UserAnalytics{
		UserID:           "system",
		TotalModels:      0,
		ActiveModels:     0,
		TotalElements:    0,
		ActiveElements:   0,
		LastActivity:     time.Now(),
		PreferredSystems: []BIMSystemType{},
	}

	report.UserAnalytics["system"] = userAnalytics
}

// calculateValidationAnalytics calculates validation analytics
func (ba *BIMAnalytics) calculateValidationAnalytics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	validationMetrics, _ := ba.GetMetrics("validation_operation", report.Period, startTime, endTime)
	timeMetrics, _ := ba.GetMetrics("validation_time", report.Period, startTime, endTime)

	totalValidations := int64(len(validationMetrics))
	successfulValidations := int64(0)
	var totalTime float64

	for _, metric := range validationMetrics {
		if metric.Value > 0 {
			successfulValidations++
		}
	}

	for _, metric := range timeMetrics {
		totalTime += metric.Value
	}

	var successRate float64
	var averageTime float64

	if totalValidations > 0 {
		successRate = float64(successfulValidations) / float64(totalValidations) * 100
	}

	if len(timeMetrics) > 0 {
		averageTime = totalTime / float64(len(timeMetrics))
	}

	validationAnalytics := ValidationAnalytics{
		TotalValidations:      totalValidations,
		SuccessfulValidations: successfulValidations,
		FailedValidations:     totalValidations - successfulValidations,
		SuccessRate:           successRate,
		AverageValidationTime: averageTime,
		CommonErrors:          make(map[string]int64),
		ValidationTrends:      []TimeSeriesPoint{},
	}

	report.ValidationAnalytics = validationAnalytics
}

// calculateTransformationAnalytics calculates transformation analytics
func (ba *BIMAnalytics) calculateTransformationAnalytics(report *BIMAnalyticsReport, startTime, endTime time.Time) {
	transformationMetrics, _ := ba.GetMetrics("transformation_operation", report.Period, startTime, endTime)
	timeMetrics, _ := ba.GetMetrics("transformation_time", report.Period, startTime, endTime)

	totalTransformations := int64(len(transformationMetrics))
	successfulTransformations := int64(0)
	var totalTime float64

	for _, metric := range transformationMetrics {
		if metric.Value > 0 {
			successfulTransformations++
		}
	}

	for _, metric := range timeMetrics {
		totalTime += metric.Value
	}

	var successRate float64
	var averageTime float64

	if totalTransformations > 0 {
		successRate = float64(successfulTransformations) / float64(totalTransformations) * 100
	}

	if len(timeMetrics) > 0 {
		averageTime = totalTime / float64(len(timeMetrics))
	}

	transformationAnalytics := TransformationAnalytics{
		TotalTransformations:      totalTransformations,
		SuccessfulTransformations: successfulTransformations,
		FailedTransformations:     totalTransformations - successfulTransformations,
		SuccessRate:               successRate,
		AverageTransformationTime: averageTime,
		PopularTransformations:    make(map[string]int64),
		TransformationTrends:      []TimeSeriesPoint{},
	}

	report.TransformationAnalytics = transformationAnalytics
}

// aggregationRoutine runs the aggregation routine
func (ba *BIMAnalytics) aggregationRoutine() {
	ticker := time.NewTicker(ba.config.AggregationPeriod)
	defer ticker.Stop()

	for range ticker.C {
		ba.aggregateMetrics()
	}
}

// aggregateMetrics aggregates metrics for the current period
func (ba *BIMAnalytics) aggregateMetrics() {
	ba.mu.Lock()
	defer ba.mu.Unlock()

	now := time.Now()
	periodStart := now.Truncate(ba.config.AggregationPeriod)

	// Aggregate metrics for each metric type
	for metricName, metrics := range ba.metrics {
		var periodMetrics []AnalyticsMetric
		var totalValue float64
		var totalCount int64

		for _, metric := range metrics {
			if metric.StartTime.Equal(periodStart) {
				totalValue += metric.Value
				totalCount += metric.Count
			}
		}

		if totalCount > 0 {
			aggregatedMetric := AnalyticsMetric{
				Period:     AnalyticsPeriodHour,
				StartTime:  periodStart,
				EndTime:    periodStart.Add(ba.config.AggregationPeriod),
				MetricName: metricName,
				Value:      totalValue,
				Count:      totalCount,
			}

			periodMetrics = append(periodMetrics, aggregatedMetric)
		}

		// Update metrics with aggregated data
		if len(periodMetrics) > 0 {
			ba.metrics[metricName] = append(ba.metrics[metricName], periodMetrics...)
		}
	}
}

// ExportReportToJSON converts a report to JSON
func (ba *BIMAnalytics) ExportReportToJSON(report *BIMAnalyticsReport) ([]byte, error) {
	return json.Marshal(report)
}

// ImportReportFromJSON imports a report from JSON
func (ba *BIMAnalytics) ImportReportFromJSON(data []byte) (*BIMAnalyticsReport, error) {
	var report BIMAnalyticsReport
	if err := json.Unmarshal(data, &report); err != nil {
		return nil, err
	}
	return &report, nil
}

// ExportMetricsToJSON converts metrics to JSON
func (ba *BIMAnalytics) ExportMetricsToJSON(metrics []AnalyticsMetric) ([]byte, error) {
	return json.Marshal(metrics)
}

// ImportMetricsFromJSON imports metrics from JSON
func (ba *BIMAnalytics) ImportMetricsFromJSON(data []byte) ([]AnalyticsMetric, error) {
	var metrics []AnalyticsMetric
	if err := json.Unmarshal(data, &metrics); err != nil {
		return nil, err
	}
	return metrics, nil
}
