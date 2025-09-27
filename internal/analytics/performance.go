package analytics

import (
	"fmt"
	"math"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ProcessDataPoint processes a data point for performance monitoring
func (pm *PerformanceMonitor) ProcessDataPoint(dataPoint EnergyDataPoint) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	// Convert to performance data point
	perfPoint := PerformanceDataPoint{
		Timestamp: dataPoint.Timestamp,
		KPIID:     "energy_consumption",
		Value:     dataPoint.Consumption,
		Unit:      "kWh",
		Metadata: map[string]interface{}{
			"building_id": dataPoint.BuildingID,
			"space_id":    dataPoint.SpaceID,
			"asset_id":    dataPoint.AssetID,
			"efficiency":  dataPoint.Efficiency,
		},
	}

	// Store performance data
	pm.performanceData[perfPoint.KPIID] = append(pm.performanceData[perfPoint.KPIID], perfPoint)

	// Check thresholds
	if err := pm.checkThresholds(perfPoint); err != nil {
		logger.Error("Error checking thresholds: %v", err)
		return err
	}

	// Update KPIs
	if err := pm.updateKPIs(perfPoint); err != nil {
		logger.Error("Error updating KPIs: %v", err)
		return err
	}

	// Update metrics
	pm.updatePerformanceMetrics()

	logger.Debug("Performance data processed successfully")
	return nil
}

// checkThresholds checks if any thresholds have been exceeded
func (pm *PerformanceMonitor) checkThresholds(dataPoint PerformanceDataPoint) error {
	for _, threshold := range pm.thresholds {
		if !threshold.Enabled {
			continue
		}

		if threshold.KPIID != dataPoint.KPIID {
			continue
		}

		exceeded := false
		switch threshold.Operator {
		case ">":
			exceeded = dataPoint.Value > threshold.Value
		case "<":
			exceeded = dataPoint.Value < threshold.Value
		case ">=":
			exceeded = dataPoint.Value >= threshold.Value
		case "<=":
			exceeded = dataPoint.Value <= threshold.Value
		case "==":
			exceeded = math.Abs(dataPoint.Value-threshold.Value) < 0.001
		case "!=":
			exceeded = math.Abs(dataPoint.Value-threshold.Value) >= 0.001
		}

		if exceeded {
			if err := pm.createAlert(threshold, dataPoint); err != nil {
				logger.Error("Error creating alert: %v", err)
				return err
			}
		}
	}

	return nil
}

// createAlert creates a new alert
func (pm *PerformanceMonitor) createAlert(threshold Threshold, dataPoint PerformanceDataPoint) error {
	// Check if alert already exists for this threshold
	for _, existingAlert := range pm.alerts {
		if existingAlert.ThresholdID == threshold.ID && existingAlert.Status == "active" {
			return nil // Alert already exists
		}
	}

	alert := Alert{
		ID:          fmt.Sprintf("alert_%d", time.Now().UnixNano()),
		KPIID:       dataPoint.KPIID,
		ThresholdID: threshold.ID,
		Type:        threshold.Type,
		Severity:    threshold.Type,
		Message:     fmt.Sprintf("Threshold exceeded: %s %s %.2f", dataPoint.KPIID, threshold.Operator, threshold.Value),
		Value:       dataPoint.Value,
		Threshold:   threshold.Value,
		Status:      "active",
		CreatedAt:   time.Now(),
	}

	pm.alerts = append(pm.alerts, alert)
	pm.metrics.TotalAlerts++
	pm.metrics.ActiveAlerts++

	logger.Info("Alert created: %s", alert.ID)
	return nil
}

// updateKPIs updates Key Performance Indicators
func (pm *PerformanceMonitor) updateKPIs(dataPoint PerformanceDataPoint) error {
	kpi, exists := pm.kpis[dataPoint.KPIID]
	if !exists {
		// Create new KPI
		kpi = KPI{
			ID:          dataPoint.KPIID,
			Name:        dataPoint.KPIID,
			Description: fmt.Sprintf("Performance metric for %s", dataPoint.KPIID),
			Metric:      dataPoint.KPIID,
			Target:      100.0, // Default target
			Current:     dataPoint.Value,
			Unit:        dataPoint.Unit,
			Category:    "performance",
			Frequency:   time.Hour,
			LastUpdated: time.Now(),
			Trend:       "stable",
			Status:      "active",
		}
	} else {
		// Update existing KPI
		kpi.Current = dataPoint.Value
		kpi.LastUpdated = time.Now()

		// Calculate trend
		kpi.Trend = pm.calculateTrend(kpi, dataPoint)

		// Update status
		kpi.Status = pm.calculateKPIStatus(kpi)
	}

	pm.kpis[dataPoint.KPIID] = kpi
	return nil
}

// calculateTrend calculates KPI trend
func (pm *PerformanceMonitor) calculateTrend(kpi KPI, dataPoint PerformanceDataPoint) string {
	// Get recent data points for this KPI
	recentPoints := pm.performanceData[dataPoint.KPIID]
	if len(recentPoints) < 2 {
		return "stable"
	}

	// Calculate simple trend over last 10 points
	points := recentPoints
	if len(points) > 10 {
		points = points[len(points)-10:]
	}

	var sum float64
	for _, point := range points {
		sum += point.Value
	}
	average := sum / float64(len(points))

	if dataPoint.Value > average*1.05 {
		return "increasing"
	} else if dataPoint.Value < average*0.95 {
		return "decreasing"
	}

	return "stable"
}

// calculateKPIStatus calculates KPI status
func (pm *PerformanceMonitor) calculateKPIStatus(kpi KPI) string {
	if kpi.Current > kpi.Target*1.1 {
		return "critical"
	} else if kpi.Current > kpi.Target*1.05 {
		return "warning"
	} else if kpi.Current < kpi.Target*0.9 {
		return "below_target"
	}

	return "good"
}

// updatePerformanceMetrics updates performance monitoring metrics
func (pm *PerformanceMonitor) updatePerformanceMetrics() {
	pm.metrics.TotalKPIs = int64(len(pm.kpis))
	pm.metrics.TotalThresholds = int64(len(pm.thresholds))
	pm.metrics.TotalAlerts = int64(len(pm.alerts))

	// Count active KPIs
	activeKPIs := 0
	for _, kpi := range pm.kpis {
		if kpi.Status == "active" {
			activeKPIs++
		}
	}
	pm.metrics.ActiveKPIs = int64(activeKPIs)

	// Count active thresholds
	activeThresholds := 0
	for _, threshold := range pm.thresholds {
		if threshold.Enabled {
			activeThresholds++
		}
	}
	pm.metrics.ActiveThresholds = int64(activeThresholds)

	// Count active alerts
	activeAlerts := 0
	resolvedAlerts := 0
	for _, alert := range pm.alerts {
		if alert.Status == "active" {
			activeAlerts++
		} else if alert.Status == "resolved" {
			resolvedAlerts++
		}
	}
	pm.metrics.ActiveAlerts = int64(activeAlerts)
	pm.metrics.ResolvedAlerts = int64(resolvedAlerts)

	// Calculate average response time
	pm.metrics.AverageResponseTime = pm.calculateAverageResponseTime()

	// Calculate alert accuracy
	pm.metrics.AlertAccuracy = pm.calculateAlertAccuracy()
}

// calculateAverageResponseTime calculates average alert response time
func (pm *PerformanceMonitor) calculateAverageResponseTime() float64 {
	var totalResponseTime time.Duration
	var count int

	for _, alert := range pm.alerts {
		if alert.Status == "resolved" && alert.AcknowledgedAt != nil {
			responseTime := alert.AcknowledgedAt.Sub(alert.CreatedAt)
			totalResponseTime += responseTime
			count++
		}
	}

	if count == 0 {
		return 0
	}

	return float64(totalResponseTime.Milliseconds()) / float64(count)
}

// calculateAlertAccuracy calculates alert accuracy
func (pm *PerformanceMonitor) calculateAlertAccuracy() float64 {
	if pm.metrics.TotalAlerts == 0 {
		return 0
	}

	// Simplified accuracy calculation
	// In a real implementation, this would track false positives
	accuracy := float64(pm.metrics.ResolvedAlerts) / float64(pm.metrics.TotalAlerts)
	return math.Min(1.0, accuracy)
}

// CreateKPI creates a new Key Performance Indicator
func (pm *PerformanceMonitor) CreateKPI(kpi KPI) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if kpi.ID == "" {
		kpi.ID = fmt.Sprintf("kpi_%d", time.Now().UnixNano())
	}

	kpi.LastUpdated = time.Now()
	pm.kpis[kpi.ID] = kpi
	pm.metrics.TotalKPIs++

	logger.Info("KPI created: %s", kpi.ID)
	return nil
}

// UpdateKPI updates an existing KPI
func (pm *PerformanceMonitor) UpdateKPI(kpiID string, kpi KPI) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if _, exists := pm.kpis[kpiID]; !exists {
		return fmt.Errorf("KPI not found: %s", kpiID)
	}

	kpi.ID = kpiID
	kpi.LastUpdated = time.Now()
	pm.kpis[kpiID] = kpi

	logger.Info("KPI updated: %s", kpiID)
	return nil
}

// DeleteKPI deletes a KPI
func (pm *PerformanceMonitor) DeleteKPI(kpiID string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if _, exists := pm.kpis[kpiID]; !exists {
		return fmt.Errorf("KPI not found: %s", kpiID)
	}

	delete(pm.kpis, kpiID)
	pm.metrics.TotalKPIs--

	logger.Info("KPI deleted: %s", kpiID)
	return nil
}

// GetKPI returns a specific KPI
func (pm *PerformanceMonitor) GetKPI(kpiID string) (*KPI, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	kpi, exists := pm.kpis[kpiID]
	if !exists {
		return nil, fmt.Errorf("KPI not found: %s", kpiID)
	}

	return &kpi, nil
}

// GetKPIs returns all KPIs
func (pm *PerformanceMonitor) GetKPIs() []KPI {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	var kpis []KPI
	for _, kpi := range pm.kpis {
		kpis = append(kpis, kpi)
	}

	return kpis
}

// CreateThreshold creates a new performance threshold
func (pm *PerformanceMonitor) CreateThreshold(threshold Threshold) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if threshold.ID == "" {
		threshold.ID = fmt.Sprintf("threshold_%d", time.Now().UnixNano())
	}

	threshold.CreatedAt = time.Now()
	pm.thresholds[threshold.ID] = threshold
	pm.metrics.TotalThresholds++

	logger.Info("Threshold created: %s", threshold.ID)
	return nil
}

// UpdateThreshold updates an existing threshold
func (pm *PerformanceMonitor) UpdateThreshold(thresholdID string, threshold Threshold) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if _, exists := pm.thresholds[thresholdID]; !exists {
		return fmt.Errorf("threshold not found: %s", thresholdID)
	}

	threshold.ID = thresholdID
	pm.thresholds[thresholdID] = threshold

	logger.Info("Threshold updated: %s", thresholdID)
	return nil
}

// DeleteThreshold deletes a threshold
func (pm *PerformanceMonitor) DeleteThreshold(thresholdID string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if _, exists := pm.thresholds[thresholdID]; !exists {
		return fmt.Errorf("threshold not found: %s", thresholdID)
	}

	delete(pm.thresholds, thresholdID)
	pm.metrics.TotalThresholds--

	logger.Info("Threshold deleted: %s", thresholdID)
	return nil
}

// GetThreshold returns a specific threshold
func (pm *PerformanceMonitor) GetThreshold(thresholdID string) (*Threshold, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	threshold, exists := pm.thresholds[thresholdID]
	if !exists {
		return nil, fmt.Errorf("threshold not found: %s", thresholdID)
	}

	return &threshold, nil
}

// GetThresholds returns all thresholds
func (pm *PerformanceMonitor) GetThresholds() []Threshold {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	var thresholds []Threshold
	for _, threshold := range pm.thresholds {
		thresholds = append(thresholds, threshold)
	}

	return thresholds
}

// GetAlerts returns alerts based on status
func (pm *PerformanceMonitor) GetAlerts(status string) ([]Alert, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	var alerts []Alert
	for _, alert := range pm.alerts {
		if status == "" || alert.Status == status {
			alerts = append(alerts, alert)
		}
	}

	// Sort by creation time (newest first)
	sort.Slice(alerts, func(i, j int) bool {
		return alerts[i].CreatedAt.After(alerts[j].CreatedAt)
	})

	return alerts, nil
}

// GetAlert returns a specific alert
func (pm *PerformanceMonitor) GetAlert(alertID string) (*Alert, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	for _, alert := range pm.alerts {
		if alert.ID == alertID {
			return &alert, nil
		}
	}

	return nil, fmt.Errorf("alert not found: %s", alertID)
}

// AcknowledgeAlert acknowledges an alert
func (pm *PerformanceMonitor) AcknowledgeAlert(alertID string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	for i, alert := range pm.alerts {
		if alert.ID == alertID {
			now := time.Now()
			pm.alerts[i].AcknowledgedAt = &now
			pm.alerts[i].Status = "acknowledged"
			logger.Info("Alert acknowledged: %s", alertID)
			return nil
		}
	}

	return fmt.Errorf("alert not found: %s", alertID)
}

// ResolveAlert resolves an alert
func (pm *PerformanceMonitor) ResolveAlert(alertID string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	for i, alert := range pm.alerts {
		if alert.ID == alertID {
			now := time.Now()
			pm.alerts[i].ResolvedAt = &now
			pm.alerts[i].Status = "resolved"
			pm.metrics.ActiveAlerts--
			pm.metrics.ResolvedAlerts++
			logger.Info("Alert resolved: %s", alertID)
			return nil
		}
	}

	return fmt.Errorf("alert not found: %s", alertID)
}

// GetPerformanceData returns performance data for a KPI
func (pm *PerformanceMonitor) GetPerformanceData(kpiID string, startTime, endTime time.Time) ([]PerformanceDataPoint, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	var dataPoints []PerformanceDataPoint
	points, exists := pm.performanceData[kpiID]
	if !exists {
		return dataPoints, nil
	}

	for _, point := range points {
		if point.Timestamp.After(startTime) && point.Timestamp.Before(endTime) {
			dataPoints = append(dataPoints, point)
		}
	}

	// Sort by timestamp
	sort.Slice(dataPoints, func(i, j int) bool {
		return dataPoints[i].Timestamp.Before(dataPoints[j].Timestamp)
	})

	return dataPoints, nil
}

// GetPerformanceMetrics returns performance monitoring metrics
func (pm *PerformanceMonitor) GetPerformanceMetrics() *PerformanceMetrics {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	return pm.metrics
}

// GetKPITrend returns trend data for a KPI
func (pm *PerformanceMonitor) GetKPITrend(kpiID string, timeWindow time.Duration) ([]KPITrendPoint, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	endTime := time.Now()
	startTime := endTime.Add(-timeWindow)

	dataPoints, err := pm.GetPerformanceData(kpiID, startTime, endTime)
	if err != nil {
		return nil, err
	}

	var trendPoints []KPITrendPoint
	for _, point := range dataPoints {
		trendPoints = append(trendPoints, KPITrendPoint{
			Timestamp: point.Timestamp,
			Value:     point.Value,
			Unit:      point.Unit,
		})
	}

	return trendPoints, nil
}

// KPITrendPoint represents a KPI trend data point
type KPITrendPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
	Unit      string    `json:"unit"`
}
