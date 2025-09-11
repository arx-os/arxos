package maintenance

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

// MetricsHistory manages time-series data for equipment metrics
type MetricsHistory struct {
	metrics map[string]*EquipmentMetrics
	mu      sync.RWMutex
}

// EquipmentMetrics stores historical performance data for a piece of equipment
type EquipmentMetrics struct {
	EquipmentID string                    `json:"equipment_id"`
	DataPoints  []MetricDataPoint         `json:"data_points"`
	Trends      map[string]*TrendAnalysis `json:"trends"`
	LastUpdate  time.Time                 `json:"last_update"`
}

// MetricDataPoint represents a single measurement at a point in time
type MetricDataPoint struct {
	Timestamp   time.Time         `json:"timestamp"`
	MetricName  string            `json:"metric_name"`
	Value       float64           `json:"value"`
	Unit        string            `json:"unit"`
	Source      string            `json:"source"` // energy, connection, sensor, etc.
	Metadata    map[string]string `json:"metadata,omitempty"`
}

// TrendAnalysis contains statistical analysis of a metric over time
type TrendAnalysis struct {
	MetricName       string        `json:"metric_name"`
	Direction        TrendDirection `json:"direction"`
	Slope            float64       `json:"slope"`           // Rate of change
	Confidence       float64       `json:"confidence"`      // 0-1
	RSquared         float64       `json:"r_squared"`       // Correlation coefficient
	StandardDev      float64       `json:"standard_dev"`    // Variability
	Mean             float64       `json:"mean"`
	RecentChange     float64       `json:"recent_change"`   // % change in last period
	PredictedValue   float64       `json:"predicted_value"` // Next expected value
	AnalysisWindow   time.Duration `json:"analysis_window"`
	LastAnalyzed     time.Time     `json:"last_analyzed"`
}

// TrendDirection indicates the direction of change over time
type TrendDirection string

const (
	TrendIncreasing TrendDirection = "increasing"
	TrendDecreasing TrendDirection = "decreasing"
	TrendStable     TrendDirection = "stable"
	TrendVolatile   TrendDirection = "volatile"
	TrendUnknown    TrendDirection = "unknown"
)

// NewMetricsHistory creates a new metrics history manager
func NewMetricsHistory() *MetricsHistory {
	return &MetricsHistory{
		metrics: make(map[string]*EquipmentMetrics),
	}
}

// RecordMetric adds a new data point for equipment
func (mh *MetricsHistory) RecordMetric(equipmentID, metricName string, value float64, unit, source string) {
	mh.mu.Lock()
	defer mh.mu.Unlock()

	if mh.metrics[equipmentID] == nil {
		mh.metrics[equipmentID] = &EquipmentMetrics{
			EquipmentID: equipmentID,
			DataPoints:  []MetricDataPoint{},
			Trends:      make(map[string]*TrendAnalysis),
		}
	}

	dataPoint := MetricDataPoint{
		Timestamp:  time.Now(),
		MetricName: metricName,
		Value:      value,
		Unit:       unit,
		Source:     source,
	}

	metrics := mh.metrics[equipmentID]
	metrics.DataPoints = append(metrics.DataPoints, dataPoint)
	metrics.LastUpdate = time.Now()

	// Keep only recent data (last 30 days by default)
	cutoff := time.Now().AddDate(0, 0, -30)
	mh.pruneOldData(metrics, cutoff)

	// Update trend analysis if we have enough data
	mh.updateTrendAnalysis(metrics, metricName)
}

// GetMetrics returns all metrics for an equipment
func (mh *MetricsHistory) GetMetrics(equipmentID string) *EquipmentMetrics {
	mh.mu.RLock()
	defer mh.mu.RUnlock()

	if metrics, exists := mh.metrics[equipmentID]; exists {
		// Return a copy to avoid race conditions
		return mh.copyMetrics(metrics)
	}
	return nil
}

// GetMetricHistory returns historical data for a specific metric
func (mh *MetricsHistory) GetMetricHistory(equipmentID, metricName string, since time.Time) []MetricDataPoint {
	mh.mu.RLock()
	defer mh.mu.RUnlock()

	metrics := mh.metrics[equipmentID]
	if metrics == nil {
		return []MetricDataPoint{}
	}

	var result []MetricDataPoint
	for _, dp := range metrics.DataPoints {
		if dp.MetricName == metricName && dp.Timestamp.After(since) {
			result = append(result, dp)
		}
	}

	// Sort by timestamp
	sort.Slice(result, func(i, j int) bool {
		return result[i].Timestamp.Before(result[j].Timestamp)
	})

	return result
}

// GetTrendAnalysis returns trend analysis for a specific metric
func (mh *MetricsHistory) GetTrendAnalysis(equipmentID, metricName string) *TrendAnalysis {
	mh.mu.RLock()
	defer mh.mu.RUnlock()

	metrics := mh.metrics[equipmentID]
	if metrics == nil {
		return nil
	}

	if trend, exists := metrics.Trends[metricName]; exists {
		// Return a copy
		copied := *trend
		return &copied
	}
	return nil
}

// AnalyzePatterns performs pattern analysis on equipment metrics
func (mh *MetricsHistory) AnalyzePatterns(equipmentID string) *PatternAnalysis {
	mh.mu.RLock()
	defer mh.mu.RUnlock()

	metrics := mh.metrics[equipmentID]
	if metrics == nil {
		return &PatternAnalysis{
			EquipmentID: equipmentID,
			Patterns:    []Pattern{},
		}
	}

	analysis := &PatternAnalysis{
		EquipmentID: equipmentID,
		Patterns:    []Pattern{},
		AnalyzedAt:  time.Now(),
	}

	// Detect various patterns
	mh.detectCyclicalPatterns(analysis, metrics)
	mh.detectAnomalies(analysis, metrics)
	mh.detectDegradationPatterns(analysis, metrics)
	mh.detectUsagePatterns(analysis, metrics)

	return analysis
}

// PatternAnalysis contains detected patterns in equipment behavior
type PatternAnalysis struct {
	EquipmentID string    `json:"equipment_id"`
	Patterns    []Pattern `json:"patterns"`
	AnalyzedAt  time.Time `json:"analyzed_at"`
}

// Pattern represents a detected behavioral pattern
type Pattern struct {
	Type        PatternType `json:"type"`
	Description string      `json:"description"`
	Confidence  float64     `json:"confidence"`
	MetricName  string      `json:"metric_name"`
	StartTime   time.Time   `json:"start_time"`
	EndTime     time.Time   `json:"end_time"`
	Severity    string      `json:"severity"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// PatternType represents different types of patterns
type PatternType string

const (
	PatternCyclical    PatternType = "cyclical"
	PatternAnomaly     PatternType = "anomaly"
	PatternDegradation PatternType = "degradation"
	PatternUsage       PatternType = "usage"
	PatternSeasonal    PatternType = "seasonal"
)

// Private methods for trend analysis and pattern detection

func (mh *MetricsHistory) pruneOldData(metrics *EquipmentMetrics, cutoff time.Time) {
	var kept []MetricDataPoint
	for _, dp := range metrics.DataPoints {
		if dp.Timestamp.After(cutoff) {
			kept = append(kept, dp)
		}
	}
	metrics.DataPoints = kept
}

func (mh *MetricsHistory) updateTrendAnalysis(metrics *EquipmentMetrics, metricName string) {
	// Get data points for this metric
	var values []float64
	var timestamps []time.Time

	for _, dp := range metrics.DataPoints {
		if dp.MetricName == metricName {
			values = append(values, dp.Value)
			timestamps = append(timestamps, dp.Timestamp)
		}
	}

	// Need at least 5 points for meaningful analysis
	if len(values) < 5 {
		return
	}

	// Sort by timestamp
	sort.Slice(values, func(i, j int) bool {
		return timestamps[i].Before(timestamps[j])
	})

	trend := &TrendAnalysis{
		MetricName:     metricName,
		AnalysisWindow: time.Hour * 24 * 7, // 7 days
		LastAnalyzed:   time.Now(),
	}

	// Calculate basic statistics
	trend.Mean = mh.calculateMean(values)
	trend.StandardDev = mh.calculateStandardDev(values, trend.Mean)

	// Perform linear regression to determine trend
	trend.Slope, trend.RSquared = mh.linearRegression(values, timestamps)
	trend.Confidence = trend.RSquared // Simple confidence based on correlation

	// Determine trend direction
	trend.Direction = mh.determineTrendDirection(trend.Slope, trend.StandardDev, trend.Confidence)

	// Calculate recent change (last 20% of data)
	recentStart := len(values) * 4 / 5
	if recentStart < len(values)-1 {
		recentValues := values[recentStart:]
		recentMean := mh.calculateMean(recentValues)
		if trend.Mean != 0 {
			trend.RecentChange = ((recentMean - trend.Mean) / trend.Mean) * 100
		}
	}

	// Predict next value based on trend
	if len(timestamps) > 1 {
		timeDelta := timestamps[len(timestamps)-1].Sub(timestamps[len(timestamps)-2]).Seconds()
		trend.PredictedValue = values[len(values)-1] + (trend.Slope * timeDelta)
	}

	metrics.Trends[metricName] = trend
}

func (mh *MetricsHistory) calculateMean(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func (mh *MetricsHistory) calculateStandardDev(values []float64, mean float64) float64 {
	if len(values) <= 1 {
		return 0
	}
	
	sumSquares := 0.0
	for _, v := range values {
		diff := v - mean
		sumSquares += diff * diff
	}
	
	variance := sumSquares / float64(len(values)-1)
	return variance // Return variance for simplicity, square root would be std dev
}

func (mh *MetricsHistory) linearRegression(values []float64, timestamps []time.Time) (slope, rSquared float64) {
	n := len(values)
	if n < 2 {
		return 0, 0
	}

	// Convert timestamps to numeric values (seconds since first timestamp)
	var x []float64
	baseTime := timestamps[0]
	for _, ts := range timestamps {
		x = append(x, ts.Sub(baseTime).Seconds())
	}

	// Calculate means
	xMean := mh.calculateMean(x)
	yMean := mh.calculateMean(values)

	// Calculate slope and correlation
	var numerator, xDenominator, yDenominator float64
	for i := 0; i < n; i++ {
		xDiff := x[i] - xMean
		yDiff := values[i] - yMean
		
		numerator += xDiff * yDiff
		xDenominator += xDiff * xDiff
		yDenominator += yDiff * yDiff
	}

	if xDenominator == 0 {
		return 0, 0
	}

	slope = numerator / xDenominator
	
	// Calculate R-squared
	if yDenominator > 0 {
		correlation := numerator / (xDenominator * yDenominator)
		rSquared = correlation * correlation
	}

	return slope, rSquared
}

func (mh *MetricsHistory) determineTrendDirection(slope, standardDev, confidence float64) TrendDirection {
	if confidence < 0.3 {
		return TrendUnknown
	}

	// Consider volatility
	if standardDev > abs(slope)*10 {
		return TrendVolatile
	}

	threshold := standardDev * 0.1 // Adjust threshold based on variability
	
	if slope > threshold {
		return TrendIncreasing
	} else if slope < -threshold {
		return TrendDecreasing
	} else {
		return TrendStable
	}
}

func (mh *MetricsHistory) detectCyclicalPatterns(analysis *PatternAnalysis, metrics *EquipmentMetrics) {
	// Group data by metric name
	metricData := make(map[string][]MetricDataPoint)
	for _, dp := range metrics.DataPoints {
		metricData[dp.MetricName] = append(metricData[dp.MetricName], dp)
	}

	for metricName, dataPoints := range metricData {
		if len(dataPoints) < 24 { // Need at least 24 hours of data
			continue
		}

		// Simple cyclical detection - look for daily patterns
		if mh.detectDailyCycle(dataPoints) {
			analysis.Patterns = append(analysis.Patterns, Pattern{
				Type:        PatternCyclical,
				Description: fmt.Sprintf("%s shows daily cyclical pattern", metricName),
				Confidence:  0.75,
				MetricName:  metricName,
				StartTime:   dataPoints[0].Timestamp,
				EndTime:     dataPoints[len(dataPoints)-1].Timestamp,
				Severity:    "info",
			})
		}
	}
}

func (mh *MetricsHistory) detectAnomalies(analysis *PatternAnalysis, metrics *EquipmentMetrics) {
	// Group data by metric name
	metricData := make(map[string][]MetricDataPoint)
	for _, dp := range metrics.DataPoints {
		metricData[dp.MetricName] = append(metricData[dp.MetricName], dp)
	}

	for metricName, dataPoints := range metricData {
		if len(dataPoints) < 10 {
			continue
		}

		// Calculate values array
		var values []float64
		for _, dp := range dataPoints {
			values = append(values, dp.Value)
		}

		mean := mh.calculateMean(values)
		stdDev := mh.calculateStandardDev(values, mean)

		// Detect outliers (values beyond 2 standard deviations)
		for _, dp := range dataPoints {
			if abs(dp.Value-mean) > 2*stdDev {
				analysis.Patterns = append(analysis.Patterns, Pattern{
					Type:        PatternAnomaly,
					Description: fmt.Sprintf("Anomalous %s value: %.2f (expected: %.2f ± %.2f)", metricName, dp.Value, mean, stdDev),
					Confidence:  0.8,
					MetricName:  metricName,
					StartTime:   dp.Timestamp,
					EndTime:     dp.Timestamp,
					Severity:    "warning",
					Metadata: map[string]interface{}{
						"value":    dp.Value,
						"expected": mean,
						"stddev":   stdDev,
					},
				})
			}
		}
	}
}

func (mh *MetricsHistory) detectDegradationPatterns(analysis *PatternAnalysis, metrics *EquipmentMetrics) {
	for metricName, trend := range metrics.Trends {
		// Look for sustained degradation
		if trend.Direction == TrendDecreasing && trend.Confidence > 0.6 {
			severity := "info"
			if trend.RecentChange < -20 { // More than 20% decline
				severity = "warning"
			}
			if trend.RecentChange < -50 { // More than 50% decline
				severity = "critical"
			}

			analysis.Patterns = append(analysis.Patterns, Pattern{
				Type:        PatternDegradation,
				Description: fmt.Sprintf("%s showing degradation trend (%.1f%% decline)", metricName, abs(trend.RecentChange)),
				Confidence:  trend.Confidence,
				MetricName:  metricName,
				StartTime:   time.Now().Add(-trend.AnalysisWindow),
				EndTime:     time.Now(),
				Severity:    severity,
				Metadata: map[string]interface{}{
					"slope":         trend.Slope,
					"recent_change": trend.RecentChange,
				},
			})
		}
	}
}

func (mh *MetricsHistory) detectUsagePatterns(analysis *PatternAnalysis, metrics *EquipmentMetrics) {
	// Look for usage-related metrics
	usageMetrics := []string{"usage_hours", "operational_hours", "load_factor"}
	
	for _, metricName := range usageMetrics {
		if trend, exists := metrics.Trends[metricName]; exists {
			if trend.Direction == TrendIncreasing && trend.RecentChange > 30 {
				analysis.Patterns = append(analysis.Patterns, Pattern{
					Type:        PatternUsage,
					Description: fmt.Sprintf("High usage pattern detected for %s (%.1f%% increase)", metricName, trend.RecentChange),
					Confidence:  trend.Confidence,
					MetricName:  metricName,
					StartTime:   time.Now().Add(-trend.AnalysisWindow),
					EndTime:     time.Now(),
					Severity:    "info",
				})
			}
		}
	}
}

func (mh *MetricsHistory) detectDailyCycle(dataPoints []MetricDataPoint) bool {
	// Simple daily cycle detection
	// Group by hour of day and check for consistent patterns
	hourlyAverages := make(map[int][]float64)
	
	for _, dp := range dataPoints {
		hour := dp.Timestamp.Hour()
		hourlyAverages[hour] = append(hourlyAverages[hour], dp.Value)
	}

	// Calculate average for each hour
	hourlyMeans := make(map[int]float64)
	for hour, values := range hourlyAverages {
		if len(values) > 0 {
			hourlyMeans[hour] = mh.calculateMean(values)
		}
	}

	// Look for variation between hours (simplified cycle detection)
	if len(hourlyMeans) < 12 { // Need data for at least half the day
		return false
	}

	var allMeans []float64
	for _, mean := range hourlyMeans {
		allMeans = append(allMeans, mean)
	}

	overallMean := mh.calculateMean(allMeans)
	variation := mh.calculateStandardDev(allMeans, overallMean)

	// If there's significant variation between hours, consider it cyclical
	return variation > overallMean*0.1 // 10% variation threshold
}

func (mh *MetricsHistory) copyMetrics(original *EquipmentMetrics) *EquipmentMetrics {
	copy := &EquipmentMetrics{
		EquipmentID: original.EquipmentID,
		DataPoints:  make([]MetricDataPoint, len(original.DataPoints)),
		Trends:      make(map[string]*TrendAnalysis),
		LastUpdate:  original.LastUpdate,
	}

	// Copy data points
	for i, dp := range original.DataPoints {
		copy.DataPoints[i] = dp
	}

	// Copy trends
	for name, trend := range original.Trends {
		trendCopy := *trend
		copy.Trends[name] = &trendCopy
	}

	return copy
}

// Utility function
func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}