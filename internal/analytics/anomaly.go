package analytics

import (
	"fmt"
	"math"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ProcessDataPoint processes a data point for anomaly detection
func (ad *AnomalyDetector) ProcessDataPoint(dataPoint EnergyDataPoint) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	// Check each detection rule
	for _, rule := range ad.detectionRules {
		if !rule.Enabled {
			continue
		}

		if ad.isAnomaly(rule, dataPoint) {
			anomaly := ad.createAnomaly(rule, dataPoint)
			ad.anomalies = append(ad.anomalies, anomaly)
			ad.metrics.TotalAnomalies++
			ad.metrics.NewAnomalies++

			logger.Info("Anomaly detected: %s", anomaly.ID)
		}
	}

	// Update baseline models
	if err := ad.updateBaselineModels(dataPoint); err != nil {
		logger.Error("Error updating baseline models: %v", err)
		return err
	}

	// Update metrics
	ad.updateAnomalyMetrics()

	logger.Debug("Anomaly detection data processed successfully")
	return nil
}

// isAnomaly checks if a data point is an anomaly based on a rule
func (ad *AnomalyDetector) isAnomaly(rule DetectionRule, dataPoint EnergyDataPoint) bool {
	value := ad.getMetricValue(rule.Metric, dataPoint)

	// Get baseline for this metric
	baselineKey := fmt.Sprintf("%s_%s", rule.Metric, dataPoint.BuildingID)
	baseline, exists := ad.baselineModels[baselineKey]
	if !exists {
		return false
	}

	// Calculate deviation from baseline
	deviation := math.Abs(value - ad.getBaselineValue(baseline))
	threshold := rule.Threshold

	// Check if deviation exceeds threshold
	return deviation > threshold
}

// getMetricValue gets the value of a specific metric from a data point
func (ad *AnomalyDetector) getMetricValue(metric string, dataPoint EnergyDataPoint) float64 {
	switch metric {
	case "consumption":
		return dataPoint.Consumption
	case "cost":
		return dataPoint.Cost
	case "efficiency":
		return dataPoint.Efficiency
	case "temperature":
		return dataPoint.Temperature
	case "humidity":
		return dataPoint.Humidity
	case "occupancy":
		return float64(dataPoint.Occupancy)
	default:
		return 0
	}
}

// getBaselineValue gets the baseline value from a baseline model
func (ad *AnomalyDetector) getBaselineValue(baseline BaselineModel) float64 {
	// Simplified baseline value extraction
	// In a real implementation, this would use the actual model
	if value, ok := baseline.ModelData["baseline_value"].(float64); ok {
		return value
	}
	return 0
}

// createAnomaly creates a new anomaly
func (ad *AnomalyDetector) createAnomaly(rule DetectionRule, dataPoint EnergyDataPoint) Anomaly {
	value := ad.getMetricValue(rule.Metric, dataPoint)
	baselineKey := fmt.Sprintf("%s_%s", rule.Metric, dataPoint.BuildingID)
	baseline, _ := ad.baselineModels[baselineKey]
	expectedValue := ad.getBaselineValue(baseline)
	deviation := math.Abs(value - expectedValue)

	// Calculate severity based on deviation
	severity := "low"
	if deviation > rule.Threshold*2 {
		severity = "high"
	} else if deviation > rule.Threshold*1.5 {
		severity = "medium"
	}

	return Anomaly{
		ID:            fmt.Sprintf("anomaly_%d", time.Now().UnixNano()),
		RuleID:        rule.ID,
		Metric:        rule.Metric,
		Value:         value,
		ExpectedValue: expectedValue,
		Deviation:     deviation,
		Severity:      severity,
		Timestamp:     dataPoint.Timestamp,
		Status:        "new",
		Description:   fmt.Sprintf("Anomaly detected in %s: %.2f (expected: %.2f)", rule.Metric, value, expectedValue),
		Context: map[string]interface{}{
			"building_id": dataPoint.BuildingID,
			"space_id":    dataPoint.SpaceID,
			"asset_id":    dataPoint.AssetID,
			"rule_id":     rule.ID,
		},
	}
}

// updateBaselineModels updates baseline models with new data
func (ad *AnomalyDetector) updateBaselineModels(dataPoint EnergyDataPoint) error {
	// Update baseline for consumption metric
	consumptionKey := fmt.Sprintf("consumption_%s", dataPoint.BuildingID)
	baseline, exists := ad.baselineModels[consumptionKey]
	if !exists {
		baseline = BaselineModel{
			ID:        consumptionKey,
			Metric:    "consumption",
			Algorithm: "moving_average",
			ModelData: map[string]interface{}{
				"baseline_value": dataPoint.Consumption,
				"data_points":    1,
			},
			Accuracy:    0.5,
			LastTrained: time.Now(),
			Status:      "ready",
		}
	} else {
		// Update baseline using exponential moving average
		currentBaseline := ad.getBaselineValue(baseline)
		alpha := 0.1 // Smoothing factor
		newBaseline := alpha*dataPoint.Consumption + (1-alpha)*currentBaseline

		baseline.ModelData["baseline_value"] = newBaseline
		baseline.LastTrained = time.Now()
		baseline.Accuracy = math.Min(1.0, baseline.Accuracy+0.01)
	}

	ad.baselineModels[consumptionKey] = baseline
	return nil
}

// updateAnomalyMetrics updates anomaly detection metrics
func (ad *AnomalyDetector) updateAnomalyMetrics() {
	ad.metrics.TotalRules = int64(len(ad.detectionRules))
	ad.metrics.TotalAnomalies = int64(len(ad.anomalies))

	// Count active rules
	activeRules := 0
	for _, rule := range ad.detectionRules {
		if rule.Enabled {
			activeRules++
		}
	}
	ad.metrics.ActiveRules = int64(activeRules)

	// Count anomalies by status
	newAnomalies := 0
	resolvedAnomalies := 0
	for _, anomaly := range ad.anomalies {
		switch anomaly.Status {
		case "new":
			newAnomalies++
		case "resolved":
			resolvedAnomalies++
		}
	}
	ad.metrics.NewAnomalies = int64(newAnomalies)
	ad.metrics.ResolvedAnomalies = int64(resolvedAnomalies)

	// Calculate detection accuracy
	ad.metrics.DetectionAccuracy = ad.calculateDetectionAccuracy()
}

// calculateDetectionAccuracy calculates anomaly detection accuracy
func (ad *AnomalyDetector) calculateDetectionAccuracy() float64 {
	if ad.metrics.TotalAnomalies == 0 {
		return 0
	}

	// Simplified accuracy calculation
	// In a real implementation, this would track true/false positives
	accuracy := float64(ad.metrics.ResolvedAnomalies) / float64(ad.metrics.TotalAnomalies)
	return math.Min(1.0, accuracy)
}

// CreateDetectionRule creates a new anomaly detection rule
func (ad *AnomalyDetector) CreateDetectionRule(rule DetectionRule) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	if rule.ID == "" {
		rule.ID = fmt.Sprintf("rule_%d", time.Now().UnixNano())
	}

	rule.CreatedAt = time.Now()
	ad.detectionRules = append(ad.detectionRules, rule)
	ad.metrics.TotalRules++

	logger.Info("Detection rule created: %s", rule.ID)
	return nil
}

// UpdateDetectionRule updates an existing detection rule
func (ad *AnomalyDetector) UpdateDetectionRule(ruleID string, rule DetectionRule) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	for i, existingRule := range ad.detectionRules {
		if existingRule.ID == ruleID {
			rule.ID = ruleID
			rule.CreatedAt = existingRule.CreatedAt
			ad.detectionRules[i] = rule
			logger.Info("Detection rule updated: %s", ruleID)
			return nil
		}
	}

	return fmt.Errorf("detection rule not found: %s", ruleID)
}

// DeleteDetectionRule deletes a detection rule
func (ad *AnomalyDetector) DeleteDetectionRule(ruleID string) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	for i, rule := range ad.detectionRules {
		if rule.ID == ruleID {
			ad.detectionRules = append(ad.detectionRules[:i], ad.detectionRules[i+1:]...)
			ad.metrics.TotalRules--
			logger.Info("Detection rule deleted: %s", ruleID)
			return nil
		}
	}

	return fmt.Errorf("detection rule not found: %s", ruleID)
}

// GetDetectionRule returns a specific detection rule
func (ad *AnomalyDetector) GetDetectionRule(ruleID string) (*DetectionRule, error) {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	for _, rule := range ad.detectionRules {
		if rule.ID == ruleID {
			return &rule, nil
		}
	}

	return nil, fmt.Errorf("detection rule not found: %s", ruleID)
}

// GetDetectionRules returns all detection rules
func (ad *AnomalyDetector) GetDetectionRules() []DetectionRule {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	return ad.detectionRules
}

// GetAnomalies returns anomalies based on severity
func (ad *AnomalyDetector) GetAnomalies(severity string) ([]Anomaly, error) {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	var anomalies []Anomaly
	for _, anomaly := range ad.anomalies {
		if severity == "" || anomaly.Severity == severity {
			anomalies = append(anomalies, anomaly)
		}
	}

	// Sort by timestamp (newest first)
	sort.Slice(anomalies, func(i, j int) bool {
		return anomalies[i].Timestamp.After(anomalies[j].Timestamp)
	})

	return anomalies, nil
}

// GetAnomaly returns a specific anomaly
func (ad *AnomalyDetector) GetAnomaly(anomalyID string) (*Anomaly, error) {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	for _, anomaly := range ad.anomalies {
		if anomaly.ID == anomalyID {
			return &anomaly, nil
		}
	}

	return nil, fmt.Errorf("anomaly not found: %s", anomalyID)
}

// UpdateAnomaly updates an anomaly
func (ad *AnomalyDetector) UpdateAnomaly(anomalyID string, anomaly Anomaly) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	for i, existingAnomaly := range ad.anomalies {
		if existingAnomaly.ID == anomalyID {
			anomaly.ID = anomalyID
			anomaly.Timestamp = existingAnomaly.Timestamp
			ad.anomalies[i] = anomaly
			logger.Info("Anomaly updated: %s", anomalyID)
			return nil
		}
	}

	return fmt.Errorf("anomaly not found: %s", anomalyID)
}

// ResolveAnomaly resolves an anomaly
func (ad *AnomalyDetector) ResolveAnomaly(anomalyID string) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	for i, anomaly := range ad.anomalies {
		if anomaly.ID == anomalyID {
			ad.anomalies[i].Status = "resolved"
			ad.metrics.ResolvedAnomalies++
			logger.Info("Anomaly resolved: %s", anomalyID)
			return nil
		}
	}

	return fmt.Errorf("anomaly not found: %s", anomalyID)
}

// MarkAnomalyAsFalsePositive marks an anomaly as a false positive
func (ad *AnomalyDetector) MarkAnomalyAsFalsePositive(anomalyID string) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	for i, anomaly := range ad.anomalies {
		if anomaly.ID == anomalyID {
			ad.anomalies[i].Status = "false_positive"
			ad.metrics.FalsePositives++
			logger.Info("Anomaly marked as false positive: %s", anomalyID)
			return nil
		}
	}

	return fmt.Errorf("anomaly not found: %s", anomalyID)
}

// GetBaselineModel returns a specific baseline model
func (ad *AnomalyDetector) GetBaselineModel(modelID string) (*BaselineModel, error) {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	model, exists := ad.baselineModels[modelID]
	if !exists {
		return nil, fmt.Errorf("baseline model not found: %s", modelID)
	}

	return &model, nil
}

// GetBaselineModels returns all baseline models
func (ad *AnomalyDetector) GetBaselineModels() []BaselineModel {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	var models []BaselineModel
	for _, model := range ad.baselineModels {
		models = append(models, model)
	}

	return models
}

// CreateBaselineModel creates a new baseline model
func (ad *AnomalyDetector) CreateBaselineModel(model BaselineModel) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	if model.ID == "" {
		model.ID = fmt.Sprintf("baseline_%d", time.Now().UnixNano())
	}

	model.LastTrained = time.Now()
	ad.baselineModels[model.ID] = model

	logger.Info("Baseline model created: %s", model.ID)
	return nil
}

// UpdateBaselineModel updates an existing baseline model
func (ad *AnomalyDetector) UpdateBaselineModel(modelID string, model BaselineModel) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	if _, exists := ad.baselineModels[modelID]; !exists {
		return fmt.Errorf("baseline model not found: %s", modelID)
	}

	model.ID = modelID
	model.LastTrained = time.Now()
	ad.baselineModels[modelID] = model

	logger.Info("Baseline model updated: %s", modelID)
	return nil
}

// DeleteBaselineModel deletes a baseline model
func (ad *AnomalyDetector) DeleteBaselineModel(modelID string) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	if _, exists := ad.baselineModels[modelID]; !exists {
		return fmt.Errorf("baseline model not found: %s", modelID)
	}

	delete(ad.baselineModels, modelID)
	logger.Info("Baseline model deleted: %s", modelID)
	return nil
}

// AddDetectionAlgorithm adds a new detection algorithm
func (ad *AnomalyDetector) AddDetectionAlgorithm(algorithm DetectionAlgorithm) error {
	ad.mu.Lock()
	defer ad.mu.Unlock()

	if algorithm.ID == "" {
		algorithm.ID = fmt.Sprintf("algo_%d", time.Now().UnixNano())
	}

	algorithm.Status = "ready"
	ad.algorithms[algorithm.ID] = algorithm

	logger.Info("Detection algorithm added: %s", algorithm.ID)
	return nil
}

// GetDetectionAlgorithm returns a specific detection algorithm
func (ad *AnomalyDetector) GetDetectionAlgorithm(algorithmID string) (*DetectionAlgorithm, error) {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	algorithm, exists := ad.algorithms[algorithmID]
	if !exists {
		return nil, fmt.Errorf("detection algorithm not found: %s", algorithmID)
	}

	return &algorithm, nil
}

// GetDetectionAlgorithms returns all detection algorithms
func (ad *AnomalyDetector) GetDetectionAlgorithms() []DetectionAlgorithm {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	var algorithms []DetectionAlgorithm
	for _, algorithm := range ad.algorithms {
		algorithms = append(algorithms, algorithm)
	}

	return algorithms
}

// GetAnomalyMetrics returns anomaly detection metrics
func (ad *AnomalyDetector) GetAnomalyMetrics() *AnomalyMetrics {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	return ad.metrics
}

// GetAnomalyStatistics returns anomaly statistics
func (ad *AnomalyDetector) GetAnomalyStatistics() (*AnomalyStatistics, error) {
	ad.mu.RLock()
	defer ad.mu.RUnlock()

	stats := &AnomalyStatistics{
		TotalAnomalies:       ad.metrics.TotalAnomalies,
		NewAnomalies:         ad.metrics.NewAnomalies,
		ResolvedAnomalies:    ad.metrics.ResolvedAnomalies,
		FalsePositives:       ad.metrics.FalsePositives,
		TruePositives:        ad.metrics.TruePositives,
		DetectionAccuracy:    ad.metrics.DetectionAccuracy,
		AverageDetectionTime: ad.metrics.AverageDetectionTime,
	}

	// Calculate severity distribution
	severityCounts := make(map[string]int64)
	for _, anomaly := range ad.anomalies {
		severityCounts[anomaly.Severity]++
	}
	stats.SeverityDistribution = severityCounts

	// Calculate status distribution
	statusCounts := make(map[string]int64)
	for _, anomaly := range ad.anomalies {
		statusCounts[anomaly.Status]++
	}
	stats.StatusDistribution = statusCounts

	// Calculate metric distribution
	metricCounts := make(map[string]int64)
	for _, anomaly := range ad.anomalies {
		metricCounts[anomaly.Metric]++
	}
	stats.MetricDistribution = metricCounts

	return stats, nil
}

// AnomalyStatistics represents anomaly detection statistics
type AnomalyStatistics struct {
	TotalAnomalies       int64            `json:"total_anomalies"`
	NewAnomalies         int64            `json:"new_anomalies"`
	ResolvedAnomalies    int64            `json:"resolved_anomalies"`
	FalsePositives       int64            `json:"false_positives"`
	TruePositives        int64            `json:"true_positives"`
	DetectionAccuracy    float64          `json:"detection_accuracy"`
	AverageDetectionTime float64          `json:"average_detection_time"`
	SeverityDistribution map[string]int64 `json:"severity_distribution"`
	StatusDistribution   map[string]int64 `json:"status_distribution"`
	MetricDistribution   map[string]int64 `json:"metric_distribution"`
}
