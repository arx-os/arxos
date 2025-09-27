package analytics

import (
	"net/http"
	"testing"
	"time"
)

func TestAnalyticsEngine(t *testing.T) {
	ae := NewAnalyticsEngine()

	// Test data point processing
	dataPoint := EnergyDataPoint{
		Timestamp:   time.Now(),
		BuildingID:  "building_1",
		SpaceID:     "space_1",
		AssetID:     "asset_1",
		EnergyType:  "electricity",
		Consumption: 100.0,
		Cost:        15.0,
		Efficiency:  85.0,
		Temperature: 22.0,
		Humidity:    45.0,
		Occupancy:   10,
		WeatherData: WeatherData{
			Temperature:    22.0,
			Humidity:       45.0,
			WindSpeed:      5.0,
			SolarRadiation: 500.0,
			CloudCover:     30.0,
			Precipitation:  0.0,
		},
		Metadata: map[string]interface{}{
			"source": "sensor_1",
		},
	}

	err := ae.ProcessDataPoint(dataPoint)
	if err != nil {
		t.Fatalf("Failed to process data point: %v", err)
	}

	// Test metrics
	metrics := ae.GetMetrics()
	if metrics.ProcessedDataPoints != 1 {
		t.Errorf("Expected 1 processed data point, got %d", metrics.ProcessedDataPoints)
	}

	// Test energy optimizer
	energyOptimizer := ae.GetEnergyOptimizer()
	if energyOptimizer == nil {
		t.Fatal("Energy optimizer is nil")
	}

	// Test predictive engine
	predictiveEngine := ae.GetPredictiveEngine()
	if predictiveEngine == nil {
		t.Fatal("Predictive engine is nil")
	}

	// Test performance monitor
	performanceMonitor := ae.GetPerformanceMonitor()
	if performanceMonitor == nil {
		t.Fatal("Performance monitor is nil")
	}

	// Test anomaly detector
	anomalyDetector := ae.GetAnomalyDetector()
	if anomalyDetector == nil {
		t.Fatal("Anomaly detector is nil")
	}

	// Test report generator
	reportGenerator := ae.GetReportGenerator()
	if reportGenerator == nil {
		t.Fatal("Report generator is nil")
	}
}

func TestEnergyOptimizer(t *testing.T) {
	eo := NewEnergyOptimizer()

	// Test data point processing
	dataPoint := EnergyDataPoint{
		Timestamp:   time.Now(),
		BuildingID:  "building_1",
		SpaceID:     "space_1",
		AssetID:     "asset_1",
		EnergyType:  "electricity",
		Consumption: 100.0,
		Cost:        15.0,
		Efficiency:  85.0,
		Temperature: 22.0,
		Humidity:    45.0,
		Occupancy:   10,
	}

	err := eo.ProcessEnergyData(dataPoint)
	if err != nil {
		t.Fatalf("Failed to process energy data: %v", err)
	}

	// Test baseline data
	baseline, err := eo.GetBaselineData("building_1")
	if err != nil {
		t.Fatalf("Failed to get baseline data: %v", err)
	}

	if len(baseline) == 0 {
		t.Fatal("Expected baseline data, got empty")
	}

	// Test consumption data
	consumptionData, err := eo.GetConsumptionData("building_1", time.Now().Add(-24*time.Hour), time.Now())
	if err != nil {
		t.Fatalf("Failed to get consumption data: %v", err)
	}

	if len(consumptionData) == 0 {
		t.Fatal("Expected consumption data, got empty")
	}

	// Test optimization rule
	rule := OptimizationRule{
		Name:        "Test Rule",
		Description: "Test optimization rule",
		Condition: OptimizationCondition{
			Metric:   "consumption",
			Operator: ">",
			Value:    50.0,
		},
		Action: OptimizationAction{
			Type:   "alert",
			Target: "admin",
		},
		Priority: 1,
		Enabled:  true,
	}

	err = eo.AddOptimizationRule(rule)
	if err != nil {
		t.Fatalf("Failed to add optimization rule: %v", err)
	}

	// Test recommendations
	recommendation := EnergyRecommendation{
		BuildingID:         "building_1",
		SpaceID:            "space_1",
		AssetID:            "asset_1",
		Type:               "efficiency",
		Title:              "Test Recommendation",
		Description:        "Test energy optimization recommendation",
		Priority:           1,
		PotentialSavings:   50.0,
		ImplementationCost: 25.0,
		PaybackPeriod:      6 * 30 * 24 * time.Hour, // 6 months
		Confidence:         0.9,
		Status:             "pending",
	}

	err = eo.AddRecommendation(recommendation)
	if err != nil {
		t.Fatalf("Failed to add recommendation: %v", err)
	}

	recommendations, err := eo.GetRecommendations("building_1")
	if err != nil {
		t.Fatalf("Failed to get recommendations: %v", err)
	}

	if len(recommendations) == 0 {
		t.Fatal("Expected recommendations, got empty")
	}

	// Test energy savings calculation
	savings, err := eo.CalculateEnergySavings("building_1", 24*time.Hour)
	if err != nil {
		t.Fatalf("Failed to calculate energy savings: %v", err)
	}

	if savings < 0 {
		t.Errorf("Expected positive savings, got %f", savings)
	}

	// Test efficiency trend
	efficiencyTrend, err := eo.GetEfficiencyTrend("building_1", 24*time.Hour)
	if err != nil {
		t.Fatalf("Failed to get efficiency trend: %v", err)
	}

	if len(efficiencyTrend) == 0 {
		t.Fatal("Expected efficiency trend data, got empty")
	}
}

func TestPredictiveEngine(t *testing.T) {
	pe := NewPredictiveEngine()

	// Test data point processing
	dataPoint := EnergyDataPoint{
		Timestamp:   time.Now(),
		BuildingID:  "building_1",
		SpaceID:     "space_1",
		AssetID:     "asset_1",
		EnergyType:  "electricity",
		Consumption: 100.0,
		Cost:        15.0,
		Efficiency:  85.0,
		Temperature: 22.0,
		Humidity:    45.0,
		Occupancy:   10,
	}

	err := pe.ProcessDataPoint(dataPoint)
	if err != nil {
		t.Fatalf("Failed to process data point: %v", err)
	}

	// Test model creation
	model := PredictiveModel{
		Name:      "Test Model",
		Type:      "regression",
		Algorithm: "linear",
		Target:    "consumption",
		Features:  []string{"temperature", "humidity", "occupancy"},
		Status:    "training",
	}

	err = pe.CreateModel(model)
	if err != nil {
		t.Fatalf("Failed to create model: %v", err)
	}

	// Test model training
	err = pe.TrainModel(model.ID)
	if err != nil {
		t.Fatalf("Failed to train model: %v", err)
	}

	// Test forecast generation
	forecast, err := pe.GetForecast("consumption", 24*time.Hour)
	if err != nil {
		t.Fatalf("Failed to generate forecast: %v", err)
	}

	if forecast == nil {
		t.Fatal("Expected forecast, got nil")
	}

	// Test trends
	trends, err := pe.GetTrends("consumption")
	if err != nil {
		t.Fatalf("Failed to get trends: %v", err)
	}

	if len(trends) == 0 {
		t.Fatal("Expected trends, got empty")
	}

	// Test algorithm addition
	algorithm := Algorithm{
		Name:        "Test Algorithm",
		Type:        "regression",
		Description: "Test machine learning algorithm",
		Parameters: map[string]interface{}{
			"learning_rate": 0.01,
			"epochs":        100,
		},
		Status: "ready",
	}

	err = pe.AddAlgorithm(algorithm)
	if err != nil {
		t.Fatalf("Failed to add algorithm: %v", err)
	}
}

func TestPerformanceMonitor(t *testing.T) {
	pm := NewPerformanceMonitor()

	// Test data point processing
	dataPoint := EnergyDataPoint{
		Timestamp:   time.Now(),
		BuildingID:  "building_1",
		SpaceID:     "space_1",
		AssetID:     "asset_1",
		EnergyType:  "electricity",
		Consumption: 100.0,
		Cost:        15.0,
		Efficiency:  85.0,
		Temperature: 22.0,
		Humidity:    45.0,
		Occupancy:   10,
	}

	err := pm.ProcessDataPoint(dataPoint)
	if err != nil {
		t.Fatalf("Failed to process data point: %v", err)
	}

	// Test KPI creation
	kpi := KPI{
		Name:        "Test KPI",
		Description: "Test performance KPI",
		Metric:      "energy_consumption",
		Target:      100.0,
		Current:     100.0,
		Unit:        "kWh",
		Category:    "performance",
		Frequency:   time.Hour,
		Status:      "active",
	}

	err = pm.CreateKPI(kpi)
	if err != nil {
		t.Fatalf("Failed to create KPI: %v", err)
	}

	// Test threshold creation
	threshold := Threshold{
		KPIID:    kpi.ID,
		Type:     "warning",
		Value:    120.0,
		Operator: ">",
		Duration: time.Hour,
		Enabled:  true,
	}

	err = pm.CreateThreshold(threshold)
	if err != nil {
		t.Fatalf("Failed to create threshold: %v", err)
	}

	// Test alerts
	_, err = pm.GetAlerts("")
	if err != nil {
		t.Fatalf("Failed to get alerts: %v", err)
	}

	// Test performance data
	performanceData, err := pm.GetPerformanceData("energy_consumption", time.Now().Add(-24*time.Hour), time.Now())
	if err != nil {
		t.Fatalf("Failed to get performance data: %v", err)
	}

	if len(performanceData) == 0 {
		t.Fatal("Expected performance data, got empty")
	}

	// Test KPI trend
	trend, err := pm.GetKPITrend("energy_consumption", 24*time.Hour)
	if err != nil {
		t.Fatalf("Failed to get KPI trend: %v", err)
	}

	if len(trend) == 0 {
		t.Fatal("Expected KPI trend data, got empty")
	}
}

func TestAnomalyDetector(t *testing.T) {
	ad := NewAnomalyDetector()

	// Test data point processing
	dataPoint := EnergyDataPoint{
		Timestamp:   time.Now(),
		BuildingID:  "building_1",
		SpaceID:     "space_1",
		AssetID:     "asset_1",
		EnergyType:  "electricity",
		Consumption: 100.0,
		Cost:        15.0,
		Efficiency:  85.0,
		Temperature: 22.0,
		Humidity:    45.0,
		Occupancy:   10,
	}

	err := ad.ProcessDataPoint(dataPoint)
	if err != nil {
		t.Fatalf("Failed to process data point: %v", err)
	}

	// Test detection rule creation
	rule := DetectionRule{
		Name:        "Test Rule",
		Description: "Test anomaly detection rule",
		Metric:      "consumption",
		Algorithm:   "statistical",
		Parameters: map[string]interface{}{
			"threshold": 2.0,
			"window":    10,
		},
		Threshold: 2.0,
		Enabled:   true,
	}

	err = ad.CreateDetectionRule(rule)
	if err != nil {
		t.Fatalf("Failed to create detection rule: %v", err)
	}

	// Test baseline model creation
	baselineModel := BaselineModel{
		Metric:    "consumption",
		Algorithm: "moving_average",
		ModelData: map[string]interface{}{
			"baseline_value": 100.0,
			"data_points":    1,
		},
		Accuracy: 0.5,
		Status:   "ready",
	}

	err = ad.CreateBaselineModel(baselineModel)
	if err != nil {
		t.Fatalf("Failed to create baseline model: %v", err)
	}

	// Test anomalies
	_, err = ad.GetAnomalies("")
	if err != nil {
		t.Fatalf("Failed to get anomalies: %v", err)
	}

	// Test detection algorithms
	algorithm := DetectionAlgorithm{
		Name:        "Test Algorithm",
		Type:        "statistical",
		Description: "Test anomaly detection algorithm",
		Parameters: map[string]interface{}{
			"threshold": 2.0,
			"window":    10,
		},
		Status: "ready",
	}

	err = ad.AddDetectionAlgorithm(algorithm)
	if err != nil {
		t.Fatalf("Failed to add detection algorithm: %v", err)
	}

	// Test anomaly statistics
	stats, err := ad.GetAnomalyStatistics()
	if err != nil {
		t.Fatalf("Failed to get anomaly statistics: %v", err)
	}

	if stats == nil {
		t.Fatal("Expected anomaly statistics, got nil")
	}
}

func TestReportGenerator(t *testing.T) {
	rg := NewReportGenerator()

	// Test report template creation
	template := ReportTemplate{
		Name:        "Test Template",
		Description: "Test report template",
		Type:        "energy_summary",
		Format:      "json",
		Template:    "{{.data}}",
		Schedule:    "daily",
		Enabled:     true,
	}

	err := rg.CreateReportTemplate(template)
	if err != nil {
		t.Fatalf("Failed to create report template: %v", err)
	}

	// Test report generation
	parameters := map[string]interface{}{
		"building_id": "building_1",
		"start_time":  time.Now().Add(-24 * time.Hour),
		"end_time":    time.Now(),
	}

	report, err := rg.GenerateReport("energy_summary", parameters)
	if err != nil {
		t.Fatalf("Failed to generate report: %v", err)
	}

	if report == nil {
		t.Fatal("Expected report, got nil")
	}

	// Test report retrieval
	retrievedReport, err := rg.GetReport(report.ID)
	if err != nil {
		t.Fatalf("Failed to get report: %v", err)
	}

	if retrievedReport.ID != report.ID {
		t.Errorf("Expected report ID %s, got %s", report.ID, retrievedReport.ID)
	}

	// Test report formats
	formats := rg.GetReportFormats()
	if len(formats) == 0 {
		t.Fatal("Expected report formats, got empty")
	}

	// Test report statistics
	stats, err := rg.GetReportStatistics()
	if err != nil {
		t.Fatalf("Failed to get report statistics: %v", err)
	}

	if stats == nil {
		t.Fatal("Expected report statistics, got nil")
	}
}

func TestAnalyticsAPI(t *testing.T) {
	ae := NewAnalyticsEngine()
	api := NewAnalyticsAPI(ae)

	// Test API creation
	if api == nil {
		t.Fatal("Expected analytics API, got nil")
	}

	// Test route registration
	mux := &http.ServeMux{}
	api.RegisterRoutes(mux)

	// Verify routes are registered
	// This is a basic test - in a real implementation, you would test the actual HTTP endpoints
}

func TestAnalyticsCLI(t *testing.T) {
	ae := NewAnalyticsEngine()
	cli := NewAnalyticsCLI(ae)

	// Test CLI creation
	if cli == nil {
		t.Fatal("Expected analytics CLI, got nil")
	}

	// Test command registration
	commands := cli.GetCommands()
	if len(commands) == 0 {
		t.Fatal("Expected CLI commands, got empty")
	}

	// Verify command structure
	expectedCommands := []string{"energy", "predictive", "performance", "anomaly", "report", "metrics"}
	for _, expectedCmd := range expectedCommands {
		found := false
		for _, cmd := range commands {
			if cmd.Use == expectedCmd {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected command %s not found", expectedCmd)
		}
	}
}

func TestEnergyDataPoint(t *testing.T) {
	dataPoint := EnergyDataPoint{
		Timestamp:   time.Now(),
		BuildingID:  "building_1",
		SpaceID:     "space_1",
		AssetID:     "asset_1",
		EnergyType:  "electricity",
		Consumption: 100.0,
		Cost:        15.0,
		Efficiency:  85.0,
		Temperature: 22.0,
		Humidity:    45.0,
		Occupancy:   10,
		WeatherData: WeatherData{
			Temperature:    22.0,
			Humidity:       45.0,
			WindSpeed:      5.0,
			SolarRadiation: 500.0,
			CloudCover:     30.0,
			Precipitation:  0.0,
		},
		Metadata: map[string]interface{}{
			"source": "sensor_1",
		},
	}

	// Test data point fields
	if dataPoint.BuildingID != "building_1" {
		t.Errorf("Expected building ID 'building_1', got '%s'", dataPoint.BuildingID)
	}

	if dataPoint.Consumption != 100.0 {
		t.Errorf("Expected consumption 100.0, got %f", dataPoint.Consumption)
	}

	if dataPoint.Efficiency != 85.0 {
		t.Errorf("Expected efficiency 85.0, got %f", dataPoint.Efficiency)
	}

	if dataPoint.WeatherData.Temperature != 22.0 {
		t.Errorf("Expected weather temperature 22.0, got %f", dataPoint.WeatherData.Temperature)
	}
}

func TestOptimizationRule(t *testing.T) {
	rule := OptimizationRule{
		ID:          "rule_1",
		Name:        "Test Rule",
		Description: "Test optimization rule",
		Condition: OptimizationCondition{
			Metric:   "consumption",
			Operator: ">",
			Value:    50.0,
		},
		Action: OptimizationAction{
			Type:   "alert",
			Target: "admin",
		},
		Priority: 1,
		Enabled:  true,
	}

	// Test rule fields
	if rule.ID != "rule_1" {
		t.Errorf("Expected rule ID 'rule_1', got '%s'", rule.ID)
	}

	if rule.Condition.Metric != "consumption" {
		t.Errorf("Expected condition metric 'consumption', got '%s'", rule.Condition.Metric)
	}

	if rule.Action.Type != "alert" {
		t.Errorf("Expected action type 'alert', got '%s'", rule.Action.Type)
	}
}

func TestPredictiveModel(t *testing.T) {
	model := PredictiveModel{
		ID:        "model_1",
		Name:      "Test Model",
		Type:      "regression",
		Algorithm: "linear",
		Target:    "consumption",
		Features:  []string{"temperature", "humidity", "occupancy"},
		Accuracy:  0.85,
		Precision: 0.82,
		Recall:    0.88,
		F1Score:   0.85,
		Status:    "ready",
	}

	// Test model fields
	if model.ID != "model_1" {
		t.Errorf("Expected model ID 'model_1', got '%s'", model.ID)
	}

	if model.Type != "regression" {
		t.Errorf("Expected model type 'regression', got '%s'", model.Type)
	}

	if len(model.Features) != 3 {
		t.Errorf("Expected 3 features, got %d", len(model.Features))
	}

	if model.Accuracy != 0.85 {
		t.Errorf("Expected accuracy 0.85, got %f", model.Accuracy)
	}
}

func TestKPI(t *testing.T) {
	kpi := KPI{
		ID:          "kpi_1",
		Name:        "Test KPI",
		Description: "Test performance KPI",
		Metric:      "energy_consumption",
		Target:      100.0,
		Current:     100.0,
		Unit:        "kWh",
		Category:    "performance",
		Frequency:   time.Hour,
		Status:      "active",
	}

	// Test KPI fields
	if kpi.ID != "kpi_1" {
		t.Errorf("Expected KPI ID 'kpi_1', got '%s'", kpi.ID)
	}

	if kpi.Metric != "energy_consumption" {
		t.Errorf("Expected metric 'energy_consumption', got '%s'", kpi.Metric)
	}

	if kpi.Target != 100.0 {
		t.Errorf("Expected target 100.0, got %f", kpi.Target)
	}

	if kpi.Unit != "kWh" {
		t.Errorf("Expected unit 'kWh', got '%s'", kpi.Unit)
	}
}

func TestAnomaly(t *testing.T) {
	anomaly := Anomaly{
		ID:            "anomaly_1",
		RuleID:        "rule_1",
		Metric:        "consumption",
		Value:         150.0,
		ExpectedValue: 100.0,
		Deviation:     50.0,
		Severity:      "high",
		Timestamp:     time.Now(),
		Status:        "new",
		Description:   "Test anomaly",
		Context: map[string]interface{}{
			"building_id": "building_1",
		},
	}

	// Test anomaly fields
	if anomaly.ID != "anomaly_1" {
		t.Errorf("Expected anomaly ID 'anomaly_1', got '%s'", anomaly.ID)
	}

	if anomaly.Metric != "consumption" {
		t.Errorf("Expected metric 'consumption', got '%s'", anomaly.Metric)
	}

	if anomaly.Value != 150.0 {
		t.Errorf("Expected value 150.0, got %f", anomaly.Value)
	}

	if anomaly.Deviation != 50.0 {
		t.Errorf("Expected deviation 50.0, got %f", anomaly.Deviation)
	}

	if anomaly.Severity != "high" {
		t.Errorf("Expected severity 'high', got '%s'", anomaly.Severity)
	}
}

func TestReport(t *testing.T) {
	report := Report{
		ID:         "report_1",
		TemplateID: "template_1",
		Name:       "Test Report",
		Type:       "energy_summary",
		Format:     "json",
		Content:    []byte(`{"data": "test"}`),
		Size:       15,
		Status:     "completed",
		CreatedAt:  time.Now(),
		Metadata: map[string]interface{}{
			"building_id": "building_1",
		},
	}

	// Test report fields
	if report.ID != "report_1" {
		t.Errorf("Expected report ID 'report_1', got '%s'", report.ID)
	}

	if report.Type != "energy_summary" {
		t.Errorf("Expected type 'energy_summary', got '%s'", report.Type)
	}

	if report.Format != "json" {
		t.Errorf("Expected format 'json', got '%s'", report.Format)
	}

	if report.Size != 15 {
		t.Errorf("Expected size 15, got %d", report.Size)
	}

	if report.Status != "completed" {
		t.Errorf("Expected status 'completed', got '%s'", report.Status)
	}
}
