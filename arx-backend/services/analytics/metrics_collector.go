package analytics

import (
	"fmt"
	"math"
	"sort"
	"sync"
	"time"

	"gorm.io/gorm"
)

// MetricType represents the type of metric
type MetricType string

const (
	MetricTypeCounter   MetricType = "counter"
	MetricTypeGauge     MetricType = "gauge"
	MetricTypeHistogram MetricType = "histogram"
	MetricTypeSummary   MetricType = "summary"
)

// MetricCategory represents the category of metric
type MetricCategory string

const (
	CategorySystem      MetricCategory = "system"
	CategoryApplication MetricCategory = "application"
	CategoryBusiness    MetricCategory = "business"
	CategoryUser        MetricCategory = "user"
	CategoryCustom      MetricCategory = "custom"
)

// CollectedMetric represents a collected metric
type CollectedMetric struct {
	ID        string                 `json:"id" gorm:"primaryKey"`
	Name      string                 `json:"name"`
	Type      MetricType             `json:"type"`
	Category  MetricCategory         `json:"category"`
	Value     float64                `json:"value"`
	Unit      string                 `json:"unit"`
	Labels    map[string]string      `json:"labels" gorm:"type:json"`
	Metadata  map[string]interface{} `json:"metadata" gorm:"type:json"`
	Timestamp time.Time              `json:"timestamp"`
	Source    string                 `json:"source"`
	Tags      []string               `json:"tags" gorm:"type:json"`
}

// MetricAggregation represents aggregated metrics
type MetricAggregation struct {
	ID              string                 `json:"id" gorm:"primaryKey"`
	MetricName      string                 `json:"metric_name"`
	Category        MetricCategory         `json:"category"`
	AggregationType string                 `json:"aggregation_type"` // sum, avg, min, max, count
	Value           float64                `json:"value"`
	Count           int                    `json:"count"`
	Min             float64                `json:"min"`
	Max             float64                `json:"max"`
	Sum             float64                `json:"sum"`
	Average         float64                `json:"average"`
	StdDev          float64                `json:"std_dev"`
	Percentiles     map[string]float64     `json:"percentiles" gorm:"type:json"`
	TimeRange       map[string]interface{} `json:"time_range" gorm:"type:json"`
	Labels          map[string]string      `json:"labels" gorm:"type:json"`
	CreatedAt       time.Time              `json:"created_at"`
}

// MetricsCollector provides metrics collection and aggregation
type MetricsCollector struct {
	service      *AnalyticsService
	db           *gorm.DB
	metrics      map[string]*CollectedMetric
	aggregations map[string]*MetricAggregation
	collectors   map[string]MetricCollector
	lock         sync.RWMutex
	collecting   bool
}

// MetricCollector interface for different metric collection strategies
type MetricCollector interface {
	Collect() ([]*CollectedMetric, error)
	GetName() string
	GetCategory() MetricCategory
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector(service *AnalyticsService) *MetricsCollector {
	collector := &MetricsCollector{
		service:      service,
		db:           service.db,
		metrics:      make(map[string]*CollectedMetric),
		aggregations: make(map[string]*MetricAggregation),
		collectors:   make(map[string]MetricCollector),
	}

	// Register default collectors
	collector.registerDefaultCollectors()

	// Load existing data
	collector.loadMetrics()
	collector.loadAggregations()

	return collector
}

// StartCollection starts metrics collection
func (c *MetricsCollector) StartCollection() {
	c.lock.Lock()
	c.collecting = true
	c.lock.Unlock()

	go c.collectionLoop()
}

// StopCollection stops metrics collection
func (c *MetricsCollector) StopCollection() {
	c.lock.Lock()
	c.collecting = false
	c.lock.Unlock()
}

// RegisterCollector registers a new metric collector
func (c *MetricsCollector) RegisterCollector(collector MetricCollector) {
	c.lock.Lock()
	c.collectors[collector.GetName()] = collector
	c.lock.Unlock()
}

// CollectMetrics collects metrics from all registered collectors
func (c *MetricsCollector) CollectMetrics() ([]*CollectedMetric, error) {
	var allMetrics []*CollectedMetric

	c.lock.RLock()
	collectors := make([]MetricCollector, 0, len(c.collectors))
	for _, collector := range c.collectors {
		collectors = append(collectors, collector)
	}
	c.lock.RUnlock()

	for _, collector := range collectors {
		metrics, err := collector.Collect()
		if err != nil {
			continue // Skip failed collectors
		}

		// Save metrics
		for _, metric := range metrics {
			metric.ID = c.generateID("metric")
			metric.Timestamp = time.Now()

			c.lock.Lock()
			c.metrics[metric.ID] = metric
			c.lock.Unlock()

			// Save to database
			c.db.Create(metric)
		}

		allMetrics = append(allMetrics, metrics...)
	}

	return allMetrics, nil
}

// AggregateMetrics aggregates metrics over a time period
func (c *MetricsCollector) AggregateMetrics(metricName string, aggregationType string, startTime, endTime time.Time, labels map[string]string) (*MetricAggregation, error) {
	// Query metrics from database
	var metrics []CollectedMetric
	query := c.db.Where("name = ? AND timestamp BETWEEN ? AND ?", metricName, startTime, endTime)

	// Apply label filters
	for key, value := range labels {
		query = query.Where("JSON_EXTRACT(labels, ?) = ?", "$."+key, value)
	}

	if err := query.Find(&metrics).Error; err != nil {
		return nil, fmt.Errorf("failed to query metrics: %w", err)
	}

	if len(metrics) == 0 {
		return nil, fmt.Errorf("no metrics found for aggregation")
	}

	// Calculate aggregation
	aggregation := c.calculateAggregation(metrics, aggregationType, startTime, endTime)

	c.lock.Lock()
	c.aggregations[aggregation.ID] = aggregation
	c.lock.Unlock()

	// Save to database
	if err := c.db.Create(aggregation).Error; err != nil {
		return nil, fmt.Errorf("failed to save aggregation: %w", err)
	}

	return aggregation, nil
}

// GetMetrics gets metrics with optional filtering
func (c *MetricsCollector) GetMetrics(metricName string, category MetricCategory, startTime, endTime *time.Time, limit int) ([]map[string]interface{}, error) {
	query := c.db.Model(&CollectedMetric{})

	if metricName != "" {
		query = query.Where("name = ?", metricName)
	}

	if category != "" {
		query = query.Where("category = ?", category)
	}

	if startTime != nil && endTime != nil {
		query = query.Where("timestamp BETWEEN ? AND ?", startTime, endTime)
	}

	if limit > 0 {
		query = query.Limit(limit)
	}

	query = query.Order("timestamp DESC")

	var metrics []CollectedMetric
	if err := query.Find(&metrics).Error; err != nil {
		return nil, fmt.Errorf("failed to get metrics: %w", err)
	}

	var results []map[string]interface{}
	for _, metric := range metrics {
		results = append(results, map[string]interface{}{
			"id":        metric.ID,
			"name":      metric.Name,
			"type":      metric.Type,
			"category":  metric.Category,
			"value":     metric.Value,
			"unit":      metric.Unit,
			"labels":    metric.Labels,
			"timestamp": metric.Timestamp,
			"source":    metric.Source,
			"tags":      metric.Tags,
		})
	}

	return results, nil
}

// GetAggregations gets metric aggregations
func (c *MetricsCollector) GetAggregations(metricName string, aggregationType string, limit int) ([]map[string]interface{}, error) {
	query := c.db.Model(&MetricAggregation{})

	if metricName != "" {
		query = query.Where("metric_name = ?", metricName)
	}

	if aggregationType != "" {
		query = query.Where("aggregation_type = ?", aggregationType)
	}

	if limit > 0 {
		query = query.Limit(limit)
	}

	query = query.Order("created_at DESC")

	var aggregations []MetricAggregation
	if err := query.Find(&aggregations).Error; err != nil {
		return nil, fmt.Errorf("failed to get aggregations: %w", err)
	}

	var results []map[string]interface{}
	for _, agg := range aggregations {
		results = append(results, map[string]interface{}{
			"id":               agg.ID,
			"metric_name":      agg.MetricName,
			"category":         agg.Category,
			"aggregation_type": agg.AggregationType,
			"value":            agg.Value,
			"count":            agg.Count,
			"min":              agg.Min,
			"max":              agg.Max,
			"sum":              agg.Sum,
			"average":          agg.Average,
			"std_dev":          agg.StdDev,
			"percentiles":      agg.Percentiles,
			"time_range":       agg.TimeRange,
			"labels":           agg.Labels,
			"created_at":       agg.CreatedAt,
		})
	}

	return results, nil
}

// CreateCustomMetric creates a custom metric
func (c *MetricsCollector) CreateCustomMetric(name string, metricType MetricType, category MetricCategory, value float64, unit string, labels map[string]string, metadata map[string]interface{}, tags []string) (*CollectedMetric, error) {
	metric := &CollectedMetric{
		ID:        c.generateID("metric"),
		Name:      name,
		Type:      metricType,
		Category:  category,
		Value:     value,
		Unit:      unit,
		Labels:    labels,
		Metadata:  metadata,
		Timestamp: time.Now(),
		Source:    "custom",
		Tags:      tags,
	}

	c.lock.Lock()
	c.metrics[metric.ID] = metric
	c.lock.Unlock()

	// Save to database
	if err := c.db.Create(metric).Error; err != nil {
		return nil, fmt.Errorf("failed to save metric: %w", err)
	}

	return metric, nil
}

// GetMetricSummary gets a summary of metrics
func (c *MetricsCollector) GetMetricSummary(metricName string, hours int) (map[string]interface{}, error) {
	endTime := time.Now()
	startTime := endTime.Add(-time.Duration(hours) * time.Hour)

	// Get metrics for the time period
	metrics, err := c.GetMetrics(metricName, "", &startTime, &endTime, 0)
	if err != nil {
		return nil, fmt.Errorf("failed to get metrics: %w", err)
	}

	if len(metrics) == 0 {
		return nil, fmt.Errorf("no metrics found for summary")
	}

	// Calculate summary statistics
	summary := c.calculateMetricSummary(metrics)

	summary["period"] = map[string]interface{}{
		"start_time": startTime,
		"end_time":   endTime,
		"hours":      hours,
	}

	summary["metric_name"] = metricName
	summary["total_metrics"] = len(metrics)
	summary["generated_at"] = time.Now()

	return summary, nil
}

// Helper methods

func (c *MetricsCollector) collectionLoop() {
	ticker := time.NewTicker(60 * time.Second) // Collect every minute
	defer ticker.Stop()

	for c.isCollecting() {
		select {
		case <-ticker.C:
			_, err := c.CollectMetrics()
			if err != nil {
				// Log error but continue collection
				continue
			}
		}
	}
}

func (c *MetricsCollector) isCollecting() bool {
	c.lock.RLock()
	defer c.lock.RUnlock()
	return c.collecting
}

func (c *MetricsCollector) generateID(prefix string) string {
	return fmt.Sprintf("%s_%d", prefix, time.Now().UnixNano())
}

func (c *MetricsCollector) registerDefaultCollectors() {
	// Register system metrics collector
	c.RegisterCollector(NewSystemMetricsCollector())

	// Register application metrics collector
	c.RegisterCollector(NewApplicationMetricsCollector())

	// Register business metrics collector
	c.RegisterCollector(NewBusinessMetricsCollector())
}

func (c *MetricsCollector) calculateAggregation(metrics []CollectedMetric, aggregationType string, startTime, endTime time.Time) *MetricAggregation {
	if len(metrics) == 0 {
		return nil
	}

	// Extract values
	values := make([]float64, len(metrics))
	for i, metric := range metrics {
		values[i] = metric.Value
	}

	// Calculate statistics
	sum := 0.0
	min := values[0]
	max := values[0]

	for _, value := range values {
		sum += value
		if value < min {
			min = value
		}
		if value > max {
			max = value
		}
	}

	average := sum / float64(len(values))
	stdDev := c.calculateStandardDeviation(values, average)

	// Calculate percentiles
	percentiles := c.calculatePercentiles(values)

	// Calculate aggregated value based on type
	var aggregatedValue float64
	switch aggregationType {
	case "sum":
		aggregatedValue = sum
	case "avg":
		aggregatedValue = average
	case "min":
		aggregatedValue = min
	case "max":
		aggregatedValue = max
	case "count":
		aggregatedValue = float64(len(values))
	default:
		aggregatedValue = average
	}

	aggregation := &MetricAggregation{
		ID:              c.generateID("aggregation"),
		MetricName:      metrics[0].Name,
		Category:        metrics[0].Category,
		AggregationType: aggregationType,
		Value:           aggregatedValue,
		Count:           len(values),
		Min:             min,
		Max:             max,
		Sum:             sum,
		Average:         average,
		StdDev:          stdDev,
		Percentiles:     percentiles,
		TimeRange: map[string]interface{}{
			"start_time": startTime,
			"end_time":   endTime,
		},
		Labels:    metrics[0].Labels,
		CreatedAt: time.Now(),
	}

	return aggregation
}

func (c *MetricsCollector) calculateStandardDeviation(values []float64, mean float64) float64 {
	if len(values) == 0 {
		return 0.0
	}

	sum := 0.0
	for _, value := range values {
		diff := value - mean
		sum += diff * diff
	}

	return math.Sqrt(sum / float64(len(values)))
}

func (c *MetricsCollector) calculatePercentiles(values []float64) map[string]float64 {
	if len(values) == 0 {
		return map[string]float64{}
	}

	// Sort values
	sortedValues := make([]float64, len(values))
	copy(sortedValues, values)
	sort.Float64s(sortedValues)

	percentiles := map[string]float64{
		"p50": c.getPercentile(sortedValues, 50),
		"p90": c.getPercentile(sortedValues, 90),
		"p95": c.getPercentile(sortedValues, 95),
		"p99": c.getPercentile(sortedValues, 99),
	}

	return percentiles
}

func (c *MetricsCollector) getPercentile(values []float64, percentile int) float64 {
	if len(values) == 0 {
		return 0.0
	}

	index := int(float64(percentile) / 100.0 * float64(len(values)-1))
	if index >= len(values) {
		index = len(values) - 1
	}

	return values[index]
}

func (c *MetricsCollector) calculateMetricSummary(metrics []map[string]interface{}) map[string]interface{} {
	if len(metrics) == 0 {
		return map[string]interface{}{}
	}

	// Extract values
	values := make([]float64, len(metrics))
	for i, metric := range metrics {
		if value, ok := metric["value"].(float64); ok {
			values[i] = value
		}
	}

	// Calculate statistics
	sum := 0.0
	min := values[0]
	max := values[0]

	for _, value := range values {
		sum += value
		if value < min {
			min = value
		}
		if value > max {
			max = value
		}
	}

	average := sum / float64(len(values))
	stdDev := c.calculateStandardDeviation(values, average)

	// Calculate percentiles
	percentiles := c.calculatePercentiles(values)

	summary := map[string]interface{}{
		"count":       len(values),
		"sum":         sum,
		"average":     average,
		"min":         min,
		"max":         max,
		"std_dev":     stdDev,
		"percentiles": percentiles,
	}

	return summary
}

func (c *MetricsCollector) loadMetrics() {
	var metrics []CollectedMetric
	if err := c.db.Find(&metrics).Error; err != nil {
		return
	}

	for i := range metrics {
		c.metrics[metrics[i].ID] = &metrics[i]
	}
}

func (c *MetricsCollector) loadAggregations() {
	var aggregations []MetricAggregation
	if err := c.db.Find(&aggregations).Error; err != nil {
		return
	}

	for i := range aggregations {
		c.aggregations[aggregations[i].ID] = &aggregations[i]
	}
}

// SystemMetricsCollector collects system-level metrics
type SystemMetricsCollector struct{}

func NewSystemMetricsCollector() *SystemMetricsCollector {
	return &SystemMetricsCollector{}
}

func (c *SystemMetricsCollector) GetName() string {
	return "system"
}

func (c *SystemMetricsCollector) GetCategory() MetricCategory {
	return CategorySystem
}

func (c *SystemMetricsCollector) Collect() ([]*CollectedMetric, error) {
	var metrics []*CollectedMetric

	// Mock system metrics collection
	// In real implementation, this would collect actual system metrics

	// CPU usage
	metrics = append(metrics, &CollectedMetric{
		Name:      "cpu_usage",
		Type:      MetricTypeGauge,
		Category:  CategorySystem,
		Value:     45.2,
		Unit:      "percent",
		Labels:    map[string]string{"host": "localhost"},
		Timestamp: time.Now(),
		Source:    "system",
		Tags:      []string{"cpu", "system"},
	})

	// Memory usage
	metrics = append(metrics, &CollectedMetric{
		Name:      "memory_usage",
		Type:      MetricTypeGauge,
		Category:  CategorySystem,
		Value:     62.8,
		Unit:      "percent",
		Labels:    map[string]string{"host": "localhost"},
		Timestamp: time.Now(),
		Source:    "system",
		Tags:      []string{"memory", "system"},
	})

	// Disk usage
	metrics = append(metrics, &CollectedMetric{
		Name:      "disk_usage",
		Type:      MetricTypeGauge,
		Category:  CategorySystem,
		Value:     34.5,
		Unit:      "percent",
		Labels:    map[string]string{"host": "localhost"},
		Timestamp: time.Now(),
		Source:    "system",
		Tags:      []string{"disk", "system"},
	})

	return metrics, nil
}

// ApplicationMetricsCollector collects application-level metrics
type ApplicationMetricsCollector struct{}

func NewApplicationMetricsCollector() *ApplicationMetricsCollector {
	return &ApplicationMetricsCollector{}
}

func (c *ApplicationMetricsCollector) GetName() string {
	return "application"
}

func (c *ApplicationMetricsCollector) GetCategory() MetricCategory {
	return CategoryApplication
}

func (c *ApplicationMetricsCollector) Collect() ([]*CollectedMetric, error) {
	var metrics []*CollectedMetric

	// Mock application metrics collection

	// Response time
	metrics = append(metrics, &CollectedMetric{
		Name:      "response_time",
		Type:      MetricTypeHistogram,
		Category:  CategoryApplication,
		Value:     245.0,
		Unit:      "milliseconds",
		Labels:    map[string]string{"endpoint": "/api/workflows"},
		Timestamp: time.Now(),
		Source:    "application",
		Tags:      []string{"performance", "api"},
	})

	// Error rate
	metrics = append(metrics, &CollectedMetric{
		Name:      "error_rate",
		Type:      MetricTypeGauge,
		Category:  CategoryApplication,
		Value:     2.1,
		Unit:      "percent",
		Labels:    map[string]string{"endpoint": "/api/workflows"},
		Timestamp: time.Now(),
		Source:    "application",
		Tags:      []string{"errors", "api"},
	})

	// Throughput
	metrics = append(metrics, &CollectedMetric{
		Name:      "throughput",
		Type:      MetricTypeCounter,
		Category:  CategoryApplication,
		Value:     125.5,
		Unit:      "requests_per_second",
		Labels:    map[string]string{"endpoint": "/api/workflows"},
		Timestamp: time.Now(),
		Source:    "application",
		Tags:      []string{"performance", "api"},
	})

	return metrics, nil
}

// BusinessMetricsCollector collects business-level metrics
type BusinessMetricsCollector struct{}

func NewBusinessMetricsCollector() *BusinessMetricsCollector {
	return &BusinessMetricsCollector{}
}

func (c *BusinessMetricsCollector) GetName() string {
	return "business"
}

func (c *BusinessMetricsCollector) GetCategory() MetricCategory {
	return CategoryBusiness
}

func (c *BusinessMetricsCollector) Collect() ([]*CollectedMetric, error) {
	var metrics []*CollectedMetric

	// Mock business metrics collection

	// Active users
	metrics = append(metrics, &CollectedMetric{
		Name:      "active_users",
		Type:      MetricTypeGauge,
		Category:  CategoryBusiness,
		Value:     150.0,
		Unit:      "users",
		Labels:    map[string]string{"period": "hourly"},
		Timestamp: time.Now(),
		Source:    "business",
		Tags:      []string{"users", "engagement"},
	})

	// Workflow executions
	metrics = append(metrics, &CollectedMetric{
		Name:      "workflow_executions",
		Type:      MetricTypeCounter,
		Category:  CategoryBusiness,
		Value:     1250.0,
		Unit:      "executions",
		Labels:    map[string]string{"period": "daily"},
		Timestamp: time.Now(),
		Source:    "business",
		Tags:      []string{"workflows", "automation"},
	})

	// Success rate
	metrics = append(metrics, &CollectedMetric{
		Name:      "success_rate",
		Type:      MetricTypeGauge,
		Category:  CategoryBusiness,
		Value:     97.5,
		Unit:      "percent",
		Labels:    map[string]string{"period": "daily"},
		Timestamp: time.Now(),
		Source:    "business",
		Tags:      []string{"quality", "reliability"},
	})

	return metrics, nil
}
