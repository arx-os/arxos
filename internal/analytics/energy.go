package analytics

import (
	"fmt"
	"math"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ProcessEnergyData processes energy consumption data
func (eo *EnergyOptimizer) ProcessEnergyData(dataPoint EnergyDataPoint) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	// Store data point
	key := fmt.Sprintf("%s_%s_%s_%s", dataPoint.BuildingID, dataPoint.SpaceID, dataPoint.AssetID, dataPoint.EnergyType)
	eo.consumptionData[key] = append(eo.consumptionData[key], dataPoint)

	// Update baseline if needed
	if err := eo.updateBaseline(dataPoint); err != nil {
		logger.Error("Error updating baseline: %v", err)
		return err
	}

	// Check optimization rules
	if err := eo.checkOptimizationRules(dataPoint); err != nil {
		logger.Error("Error checking optimization rules: %v", err)
		return err
	}

	// Update metrics
	eo.updateEnergyMetrics(dataPoint)

	logger.Debug("Energy data processed successfully")
	return nil
}

// updateBaseline updates baseline energy consumption data
func (eo *EnergyOptimizer) updateBaseline(dataPoint EnergyDataPoint) error {
	key := fmt.Sprintf("%s_%s_%s_%s", dataPoint.BuildingID, dataPoint.SpaceID, dataPoint.AssetID, dataPoint.EnergyType)

	baseline, exists := eo.baselineData[key]
	if !exists {
		baseline = BaselineData{
			BuildingID:      dataPoint.BuildingID,
			SpaceID:         dataPoint.SpaceID,
			AssetID:         dataPoint.AssetID,
			EnergyType:      dataPoint.EnergyType,
			BaselineValue:   dataPoint.Consumption,
			Variance:        0,
			ConfidenceLevel: 0.5,
			LastUpdated:     time.Now(),
			DataPoints:      1,
		}
	} else {
		// Update baseline using exponential moving average
		alpha := 0.1 // Smoothing factor
		baseline.BaselineValue = alpha*dataPoint.Consumption + (1-alpha)*baseline.BaselineValue

		// Update variance
		deviation := dataPoint.Consumption - baseline.BaselineValue
		baseline.Variance = alpha*deviation*deviation + (1-alpha)*baseline.Variance

		// Update confidence level
		baseline.ConfidenceLevel = math.Min(1.0, baseline.ConfidenceLevel+0.01)
		baseline.DataPoints++
		baseline.LastUpdated = time.Now()
	}

	eo.baselineData[key] = baseline
	return nil
}

// checkOptimizationRules checks if any optimization rules should trigger
func (eo *EnergyOptimizer) checkOptimizationRules(dataPoint EnergyDataPoint) error {
	for _, rule := range eo.optimizationRules {
		if !rule.Enabled {
			continue
		}

		if eo.evaluateCondition(rule.Condition, dataPoint) {
			if err := eo.executeAction(rule.Action, dataPoint); err != nil {
				logger.Error("Error executing optimization action: %v", err)
				return err
			}
		}
	}

	return nil
}

// evaluateCondition evaluates an optimization condition
func (eo *EnergyOptimizer) evaluateCondition(condition OptimizationCondition, dataPoint EnergyDataPoint) bool {
	value := eo.getMetricValue(condition.Metric, dataPoint)

	switch condition.Operator {
	case ">":
		return value > condition.Value
	case "<":
		return value < condition.Value
	case ">=":
		return value >= condition.Value
	case "<=":
		return value <= condition.Value
	case "==":
		return math.Abs(value-condition.Value) < 0.001
	case "!=":
		return math.Abs(value-condition.Value) >= 0.001
	default:
		return false
	}
}

// getMetricValue gets the value of a specific metric from a data point
func (eo *EnergyOptimizer) getMetricValue(metric string, dataPoint EnergyDataPoint) float64 {
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

// executeAction executes an optimization action
func (eo *EnergyOptimizer) executeAction(action OptimizationAction, dataPoint EnergyDataPoint) error {
	switch action.Type {
	case "adjust_setpoint":
		return eo.adjustSetpoint(action, dataPoint)
	case "schedule_change":
		return eo.changeSchedule(action, dataPoint)
	case "alert":
		return eo.sendAlert(action, dataPoint)
	case "report":
		return eo.generateReport(action, dataPoint)
	default:
		return fmt.Errorf("unknown action type: %s", action.Type)
	}
}

// adjustSetpoint adjusts a setpoint based on the action
func (eo *EnergyOptimizer) adjustSetpoint(action OptimizationAction, dataPoint EnergyDataPoint) error {
	logger.Info("Adjusting setpoint for %s: %v", action.Target, action.Parameters)
	// Implementation would depend on the specific building automation system
	return nil
}

// changeSchedule changes a schedule based on the action
func (eo *EnergyOptimizer) changeSchedule(action OptimizationAction, dataPoint EnergyDataPoint) error {
	logger.Info("Changing schedule for %s: %v", action.Target, action.Parameters)
	// Implementation would depend on the specific building automation system
	return nil
}

// sendAlert sends an alert based on the action
func (eo *EnergyOptimizer) sendAlert(action OptimizationAction, dataPoint EnergyDataPoint) error {
	logger.Info("Sending alert for %s: %v", action.Target, action.Parameters)
	// Implementation would depend on the specific alerting system
	return nil
}

// generateReport generates a report based on the action
func (eo *EnergyOptimizer) generateReport(action OptimizationAction, dataPoint EnergyDataPoint) error {
	logger.Info("Generating report for %s: %v", action.Target, action.Parameters)
	// Implementation would depend on the specific reporting system
	return nil
}

// updateEnergyMetrics updates energy optimization metrics
func (eo *EnergyOptimizer) updateEnergyMetrics(dataPoint EnergyDataPoint) {
	eo.metrics.TotalConsumption += dataPoint.Consumption

	// Calculate baseline consumption
	key := fmt.Sprintf("%s_%s_%s_%s", dataPoint.BuildingID, dataPoint.SpaceID, dataPoint.AssetID, dataPoint.EnergyType)
	if baseline, exists := eo.baselineData[key]; exists {
		eo.metrics.BaselineConsumption += baseline.BaselineValue
	}

	// Calculate savings
	if eo.metrics.BaselineConsumption > 0 {
		eo.metrics.Savings = eo.metrics.BaselineConsumption - eo.metrics.TotalConsumption
		eo.metrics.SavingsPercentage = (eo.metrics.Savings / eo.metrics.BaselineConsumption) * 100
	}

	// Update efficiency
	if len(eo.consumptionData[key]) > 0 {
		totalEfficiency := 0.0
		count := 0
		for _, dp := range eo.consumptionData[key] {
			if dp.Efficiency > 0 {
				totalEfficiency += dp.Efficiency
				count++
			}
		}
		if count > 0 {
			eo.metrics.AverageEfficiency = totalEfficiency / float64(count)
		}
	}
}

// AddOptimizationRule adds a new optimization rule
func (eo *EnergyOptimizer) AddOptimizationRule(rule OptimizationRule) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	if rule.ID == "" {
		rule.ID = fmt.Sprintf("rule_%d", time.Now().UnixNano())
	}

	rule.CreatedAt = time.Now()
	rule.UpdatedAt = time.Now()
	eo.optimizationRules = append(eo.optimizationRules, rule)
	eo.metrics.OptimizationRules++

	logger.Info("Optimization rule added: %s", rule.ID)
	return nil
}

// UpdateOptimizationRule updates an existing optimization rule
func (eo *EnergyOptimizer) UpdateOptimizationRule(ruleID string, rule OptimizationRule) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	for i, existingRule := range eo.optimizationRules {
		if existingRule.ID == ruleID {
			rule.ID = ruleID
			rule.CreatedAt = existingRule.CreatedAt
			rule.UpdatedAt = time.Now()
			eo.optimizationRules[i] = rule
			logger.Info("Optimization rule updated: %s", ruleID)
			return nil
		}
	}

	return fmt.Errorf("optimization rule not found: %s", ruleID)
}

// DeleteOptimizationRule deletes an optimization rule
func (eo *EnergyOptimizer) DeleteOptimizationRule(ruleID string) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	for i, rule := range eo.optimizationRules {
		if rule.ID == ruleID {
			eo.optimizationRules = append(eo.optimizationRules[:i], eo.optimizationRules[i+1:]...)
			eo.metrics.OptimizationRules--
			logger.Info("Optimization rule deleted: %s", ruleID)
			return nil
		}
	}

	return fmt.Errorf("optimization rule not found: %s", ruleID)
}

// GetOptimizationRules returns all optimization rules
func (eo *EnergyOptimizer) GetOptimizationRules() []OptimizationRule {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	return eo.optimizationRules
}

// GetOptimizationRule returns a specific optimization rule
func (eo *EnergyOptimizer) GetOptimizationRule(ruleID string) (*OptimizationRule, error) {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	for _, rule := range eo.optimizationRules {
		if rule.ID == ruleID {
			return &rule, nil
		}
	}

	return nil, fmt.Errorf("optimization rule not found: %s", ruleID)
}

// GetRecommendations returns energy optimization recommendations
func (eo *EnergyOptimizer) GetRecommendations(buildingID string) ([]EnergyRecommendation, error) {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	var recommendations []EnergyRecommendation
	for _, rec := range eo.recommendations {
		if buildingID == "" || rec.BuildingID == buildingID {
			recommendations = append(recommendations, rec)
		}
	}

	// Sort by priority (higher priority first)
	sort.Slice(recommendations, func(i, j int) bool {
		return recommendations[i].Priority > recommendations[j].Priority
	})

	return recommendations, nil
}

// AddRecommendation adds a new energy optimization recommendation
func (eo *EnergyOptimizer) AddRecommendation(recommendation EnergyRecommendation) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	if recommendation.ID == "" {
		recommendation.ID = fmt.Sprintf("rec_%d", time.Now().UnixNano())
	}

	recommendation.CreatedAt = time.Now()
	recommendation.UpdatedAt = time.Now()
	eo.recommendations = append(eo.recommendations, recommendation)
	eo.metrics.ActiveRecommendations++

	logger.Info("Energy recommendation added: %s", recommendation.ID)
	return nil
}

// UpdateRecommendation updates an existing recommendation
func (eo *EnergyOptimizer) UpdateRecommendation(recID string, recommendation EnergyRecommendation) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	for i, existingRec := range eo.recommendations {
		if existingRec.ID == recID {
			recommendation.ID = recID
			recommendation.CreatedAt = existingRec.CreatedAt
			recommendation.UpdatedAt = time.Now()
			eo.recommendations[i] = recommendation
			logger.Info("Energy recommendation updated: %s", recID)
			return nil
		}
	}

	return fmt.Errorf("recommendation not found: %s", recID)
}

// DeleteRecommendation deletes a recommendation
func (eo *EnergyOptimizer) DeleteRecommendation(recID string) error {
	eo.mu.Lock()
	defer eo.mu.Unlock()

	for i, rec := range eo.recommendations {
		if rec.ID == recID {
			eo.recommendations = append(eo.recommendations[:i], eo.recommendations[i+1:]...)
			eo.metrics.ActiveRecommendations--
			logger.Info("Energy recommendation deleted: %s", recID)
			return nil
		}
	}

	return fmt.Errorf("recommendation not found: %s", recID)
}

// GetBaselineData returns baseline energy consumption data
func (eo *EnergyOptimizer) GetBaselineData(buildingID string) ([]BaselineData, error) {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	var baselines []BaselineData
	for _, baseline := range eo.baselineData {
		if buildingID == "" || baseline.BuildingID == buildingID {
			baselines = append(baselines, baseline)
		}
	}

	return baselines, nil
}

// GetConsumptionData returns energy consumption data
func (eo *EnergyOptimizer) GetConsumptionData(buildingID string, startTime, endTime time.Time) ([]EnergyDataPoint, error) {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	var dataPoints []EnergyDataPoint
	for _, points := range eo.consumptionData {
		for _, point := range points {
			if buildingID == "" || point.BuildingID == buildingID {
				if point.Timestamp.After(startTime) && point.Timestamp.Before(endTime) {
					dataPoints = append(dataPoints, point)
				}
			}
		}
	}

	// Sort by timestamp
	sort.Slice(dataPoints, func(i, j int) bool {
		return dataPoints[i].Timestamp.Before(dataPoints[j].Timestamp)
	})

	return dataPoints, nil
}

// GetEnergyMetrics returns energy optimization metrics
func (eo *EnergyOptimizer) GetEnergyMetrics() *EnergyMetrics {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	return eo.metrics
}

// CalculateEnergySavings calculates potential energy savings
func (eo *EnergyOptimizer) CalculateEnergySavings(buildingID string, timeWindow time.Duration) (float64, error) {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	endTime := time.Now()
	startTime := endTime.Add(-timeWindow)

	var totalConsumption float64
	var totalBaseline float64

	for key, points := range eo.consumptionData {
		if buildingID != "" && !contains(key, buildingID) {
			continue
		}

		for _, point := range points {
			if point.Timestamp.After(startTime) && point.Timestamp.Before(endTime) {
				totalConsumption += point.Consumption
			}
		}

		// Get baseline for this key
		if baseline, exists := eo.baselineData[key]; exists {
			totalBaseline += baseline.BaselineValue
		}
	}

	if totalBaseline == 0 {
		return 0, fmt.Errorf("no baseline data available")
	}

	savings := totalBaseline - totalConsumption
	savingsPercentage := (savings / totalBaseline) * 100

	return savingsPercentage, nil
}

// contains checks if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[:len(substr)] == substr
}

// GetEfficiencyTrend returns efficiency trend over time
func (eo *EnergyOptimizer) GetEfficiencyTrend(buildingID string, timeWindow time.Duration) ([]EfficiencyDataPoint, error) {
	eo.mu.RLock()
	defer eo.mu.RUnlock()

	endTime := time.Now()
	startTime := endTime.Add(-timeWindow)

	var efficiencyPoints []EfficiencyDataPoint
	for _, points := range eo.consumptionData {
		for _, point := range points {
			if buildingID == "" || point.BuildingID == buildingID {
				if point.Timestamp.After(startTime) && point.Timestamp.Before(endTime) {
					efficiencyPoints = append(efficiencyPoints, EfficiencyDataPoint{
						Timestamp:  point.Timestamp,
						Efficiency: point.Efficiency,
						BuildingID: point.BuildingID,
						SpaceID:    point.SpaceID,
						AssetID:    point.AssetID,
					})
				}
			}
		}
	}

	// Sort by timestamp
	sort.Slice(efficiencyPoints, func(i, j int) bool {
		return efficiencyPoints[i].Timestamp.Before(efficiencyPoints[j].Timestamp)
	})

	return efficiencyPoints, nil
}

// EfficiencyDataPoint represents an efficiency data point
type EfficiencyDataPoint struct {
	Timestamp  time.Time `json:"timestamp"`
	Efficiency float64   `json:"efficiency"`
	BuildingID string    `json:"building_id"`
	SpaceID    string    `json:"space_id"`
	AssetID    string    `json:"asset_id"`
}
