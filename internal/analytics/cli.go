package analytics

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// AnalyticsCLI provides command-line interface for analytics
type AnalyticsCLI struct {
	analyticsEngine *AnalyticsEngine
}

// NewAnalyticsCLI creates a new analytics CLI
func NewAnalyticsCLI(analyticsEngine *AnalyticsEngine) *AnalyticsCLI {
	return &AnalyticsCLI{
		analyticsEngine: analyticsEngine,
	}
}

// GetCommands returns analytics CLI commands
func (cli *AnalyticsCLI) GetCommands() []*cobra.Command {
	return []*cobra.Command{
		cli.getEnergyCommand(),
		cli.getPredictiveCommand(),
		cli.getPerformanceCommand(),
		cli.getAnomalyCommand(),
		cli.getReportCommand(),
		cli.getMetricsCommand(),
	}
}

// getEnergyCommand returns energy optimization commands
func (cli *AnalyticsCLI) getEnergyCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "energy",
		Short: "Energy optimization commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "data",
		Short: "View energy consumption data",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showEnergyData()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "recommendations",
		Short: "View energy optimization recommendations",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showEnergyRecommendations()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "baseline",
		Short: "View energy baseline data",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showEnergyBaseline()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "savings",
		Short: "Calculate energy savings",
		Run: func(cmd *cobra.Command, args []string) {
			cli.calculateEnergySavings()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-rule",
		Short: "Add optimization rule",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addOptimizationRule()
		},
	})

	return cmd
}

// getPredictiveCommand returns predictive analytics commands
func (cli *AnalyticsCLI) getPredictiveCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "predictive",
		Short: "Predictive analytics commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "models",
		Short: "View predictive models",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showPredictiveModels()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "forecast",
		Short: "Generate forecast",
		Run: func(cmd *cobra.Command, args []string) {
			cli.generateForecast()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "trends",
		Short: "View trends",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showTrends()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-model",
		Short: "Add predictive model",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addPredictiveModel()
		},
	})

	return cmd
}

// getPerformanceCommand returns performance monitoring commands
func (cli *AnalyticsCLI) getPerformanceCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "performance",
		Short: "Performance monitoring commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "kpis",
		Short: "View KPIs",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showKPIs()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "alerts",
		Short: "View alerts",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showAlerts()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "thresholds",
		Short: "View thresholds",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showThresholds()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-kpi",
		Short: "Add KPI",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addKPI()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-threshold",
		Short: "Add threshold",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addThreshold()
		},
	})

	return cmd
}

// getAnomalyCommand returns anomaly detection commands
func (cli *AnalyticsCLI) getAnomalyCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "anomaly",
		Short: "Anomaly detection commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List anomalies",
		Run: func(cmd *cobra.Command, args []string) {
			cli.listAnomalies()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "rules",
		Short: "View detection rules",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showDetectionRules()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-rule",
		Short: "Add detection rule",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addDetectionRule()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "resolve",
		Short: "Resolve anomaly",
		Run: func(cmd *cobra.Command, args []string) {
			cli.resolveAnomaly()
		},
	})

	return cmd
}

// getReportCommand returns report generation commands
func (cli *AnalyticsCLI) getReportCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "report",
		Short: "Report generation commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List reports",
		Run: func(cmd *cobra.Command, args []string) {
			cli.listReports()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "generate",
		Short: "Generate report",
		Run: func(cmd *cobra.Command, args []string) {
			cli.generateReport()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "templates",
		Short: "View report templates",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showReportTemplates()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-template",
		Short: "Add report template",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addReportTemplate()
		},
	})

	return cmd
}

// getMetricsCommand returns metrics commands
func (cli *AnalyticsCLI) getMetricsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "metrics",
		Short: "View analytics metrics",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showMetrics()
		},
	}

	return cmd
}

// showEnergyData displays energy consumption data
func (cli *AnalyticsCLI) showEnergyData() {
	energyOptimizer := cli.analyticsEngine.GetEnergyOptimizer()

	fmt.Println("Energy Consumption Data")
	fmt.Println("======================")

	// Get consumption data for last 24 hours
	endTime := time.Now()
	startTime := endTime.Add(-24 * time.Hour)

	data, err := energyOptimizer.GetConsumptionData("", startTime, endTime)
	if err != nil {
		fmt.Printf("Error getting energy data: %v\n", err)
		return
	}

	if len(data) == 0 {
		fmt.Println("No energy data available")
		return
	}

	fmt.Printf("Found %d data points\n\n", len(data))

	for i, point := range data {
		if i >= 10 { // Show only first 10 points
			fmt.Printf("... and %d more data points\n", len(data)-10)
			break
		}

		fmt.Printf("Time: %s\n", point.Timestamp.Format("2006-01-02 15:04:05"))
		fmt.Printf("Building: %s\n", point.BuildingID)
		fmt.Printf("Space: %s\n", point.SpaceID)
		fmt.Printf("Asset: %s\n", point.AssetID)
		fmt.Printf("Energy Type: %s\n", point.EnergyType)
		fmt.Printf("Consumption: %.2f kWh\n", point.Consumption)
		fmt.Printf("Cost: $%.2f\n", point.Cost)
		fmt.Printf("Efficiency: %.1f%%\n", point.Efficiency)
		fmt.Println("---")
	}
}

// showEnergyRecommendations displays energy optimization recommendations
func (cli *AnalyticsCLI) showEnergyRecommendations() {
	recommendations, err := cli.analyticsEngine.GetOptimizationRecommendations("")
	if err != nil {
		fmt.Printf("Error getting recommendations: %v\n", err)
		return
	}

	fmt.Println("Energy Optimization Recommendations")
	fmt.Println("==================================")

	if len(recommendations) == 0 {
		fmt.Println("No recommendations available")
		return
	}

	for i, rec := range recommendations {
		fmt.Printf("%d. %s\n", i+1, rec.Title)
		fmt.Printf("   Type: %s\n", rec.Type)
		fmt.Printf("   Priority: %d\n", rec.Priority)
		fmt.Printf("   Potential Savings: $%.2f\n", rec.PotentialSavings)
		fmt.Printf("   Implementation Cost: $%.2f\n", rec.ImplementationCost)
		fmt.Printf("   Payback Period: %.1f months\n", float64(rec.PaybackPeriod.Hours())/24/30)
		fmt.Printf("   Confidence: %.1f%%\n", rec.Confidence*100)
		fmt.Printf("   Status: %s\n", rec.Status)
		fmt.Printf("   Description: %s\n", rec.Description)
		fmt.Println("---")
	}
}

// showEnergyBaseline displays energy baseline data
func (cli *AnalyticsCLI) showEnergyBaseline() {
	energyOptimizer := cli.analyticsEngine.GetEnergyOptimizer()

	baseline, err := energyOptimizer.GetBaselineData("")
	if err != nil {
		fmt.Printf("Error getting baseline data: %v\n", err)
		return
	}

	fmt.Println("Energy Baseline Data")
	fmt.Println("===================")

	if len(baseline) == 0 {
		fmt.Println("No baseline data available")
		return
	}

	for _, b := range baseline {
		fmt.Printf("Building: %s\n", b.BuildingID)
		fmt.Printf("Space: %s\n", b.SpaceID)
		fmt.Printf("Asset: %s\n", b.AssetID)
		fmt.Printf("Energy Type: %s\n", b.EnergyType)
		fmt.Printf("Baseline Value: %.2f\n", b.BaselineValue)
		fmt.Printf("Variance: %.2f\n", b.Variance)
		fmt.Printf("Confidence Level: %.1f%%\n", b.ConfidenceLevel*100)
		fmt.Printf("Data Points: %d\n", b.DataPoints)
		fmt.Printf("Last Updated: %s\n", b.LastUpdated.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// calculateEnergySavings calculates and displays energy savings
func (cli *AnalyticsCLI) calculateEnergySavings() {
	energyOptimizer := cli.analyticsEngine.GetEnergyOptimizer()

	buildingID := cli.promptForString("Building ID (optional): ")
	timeWindowStr := cli.promptForString("Time window (e.g., 24h, 7d): ")

	timeWindow, err := time.ParseDuration(timeWindowStr)
	if err != nil {
		timeWindow = 24 * time.Hour
	}

	savings, err := energyOptimizer.CalculateEnergySavings(buildingID, timeWindow)
	if err != nil {
		fmt.Printf("Error calculating savings: %v\n", err)
		return
	}

	fmt.Printf("Energy Savings: %.2f%%\n", savings)
	fmt.Printf("Time Window: %s\n", timeWindow.String())
	if buildingID != "" {
		fmt.Printf("Building: %s\n", buildingID)
	}
}

// addOptimizationRule adds a new optimization rule
func (cli *AnalyticsCLI) addOptimizationRule() {
	rule := OptimizationRule{
		Name:        cli.promptForString("Rule Name: "),
		Description: cli.promptForString("Description: "),
		Condition: OptimizationCondition{
			Metric:   cli.promptForString("Metric: "),
			Operator: cli.promptForString("Operator (>, <, >=, <=, ==, !=): "),
			Value:    cli.promptForFloat("Value: "),
		},
		Action: OptimizationAction{
			Type:       cli.promptForString("Action Type: "),
			Target:     cli.promptForString("Target: "),
			Parameters: make(map[string]interface{}),
		},
		Priority: cli.promptForInt("Priority: "),
		Enabled:  true,
	}

	energyOptimizer := cli.analyticsEngine.GetEnergyOptimizer()
	if err := energyOptimizer.AddOptimizationRule(rule); err != nil {
		fmt.Printf("Error adding rule: %v\n", err)
		return
	}

	fmt.Println("Optimization rule added successfully")
}

// showPredictiveModels displays predictive models
func (cli *AnalyticsCLI) showPredictiveModels() {
	predictiveEngine := cli.analyticsEngine.GetPredictiveEngine()
	models := predictiveEngine.GetModels()

	fmt.Println("Predictive Models")
	fmt.Println("================")

	if len(models) == 0 {
		fmt.Println("No models available")
		return
	}

	for _, model := range models {
		fmt.Printf("ID: %s\n", model.ID)
		fmt.Printf("Name: %s\n", model.Name)
		fmt.Printf("Type: %s\n", model.Type)
		fmt.Printf("Algorithm: %s\n", model.Algorithm)
		fmt.Printf("Target: %s\n", model.Target)
		fmt.Printf("Accuracy: %.2f%%\n", model.Accuracy*100)
		fmt.Printf("Status: %s\n", model.Status)
		fmt.Printf("Last Trained: %s\n", model.LastTrained.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// generateForecast generates a predictive forecast
func (cli *AnalyticsCLI) generateForecast() {
	metric := cli.promptForString("Metric: ")
	durationStr := cli.promptForString("Duration (e.g., 24h, 7d): ")

	duration, err := time.ParseDuration(durationStr)
	if err != nil {
		duration = 24 * time.Hour
	}

	forecast, err := cli.analyticsEngine.GetForecast(metric, duration)
	if err != nil {
		fmt.Printf("Error generating forecast: %v\n", err)
		return
	}

	fmt.Printf("Forecast for %s\n", metric)
	fmt.Printf("Duration: %s\n", duration.String())
	fmt.Printf("Confidence: %.2f%%\n", forecast.Confidence*100)
	fmt.Printf("Accuracy: %.2f%%\n", forecast.Accuracy*100)
	fmt.Println("\nForecast Values:")
	fmt.Println("Time\t\t\tValue\t\tLower\t\tUpper")
	fmt.Println("----\t\t\t-----\t\t-----\t\t-----")

	for _, value := range forecast.Values {
		fmt.Printf("%s\t%.2f\t\t%.2f\t\t%.2f\n",
			value.Timestamp.Format("2006-01-02 15:04"),
			value.Value,
			value.LowerBound,
			value.UpperBound)
	}
}

// showTrends displays data trends
func (cli *AnalyticsCLI) showTrends() {
	metric := cli.promptForString("Metric (optional): ")

	predictiveEngine := cli.analyticsEngine.GetPredictiveEngine()
	trends, err := predictiveEngine.GetTrends(metric)
	if err != nil {
		fmt.Printf("Error getting trends: %v\n", err)
		return
	}

	fmt.Println("Data Trends")
	fmt.Println("===========")

	if len(trends) == 0 {
		fmt.Println("No trends available")
		return
	}

	for _, trend := range trends {
		fmt.Printf("Metric: %s\n", trend.Metric)
		fmt.Printf("Direction: %s\n", trend.Direction)
		fmt.Printf("Slope: %.4f\n", trend.Slope)
		fmt.Printf("R²: %.4f\n", trend.R2)
		fmt.Printf("P-value: %.4f\n", trend.PValue)
		fmt.Printf("Significant: %t\n", trend.Significance)
		fmt.Printf("Data Points: %d\n", trend.DataPoints)
		fmt.Printf("Time Range: %s to %s\n",
			trend.StartTime.Format("2006-01-02 15:04"),
			trend.EndTime.Format("2006-01-02 15:04"))
		fmt.Println("---")
	}
}

// addPredictiveModel adds a new predictive model
func (cli *AnalyticsCLI) addPredictiveModel() {
	model := PredictiveModel{
		Name:      cli.promptForString("Model Name: "),
		Type:      cli.promptForString("Type: "),
		Algorithm: cli.promptForString("Algorithm: "),
		Target:    cli.promptForString("Target: "),
		Features:  []string{cli.promptForString("Features (comma-separated): ")},
	}

	predictiveEngine := cli.analyticsEngine.GetPredictiveEngine()
	if err := predictiveEngine.CreateModel(model); err != nil {
		fmt.Printf("Error creating model: %v\n", err)
		return
	}

	fmt.Println("Predictive model created successfully")
}

// showKPIs displays performance KPIs
func (cli *AnalyticsCLI) showKPIs() {
	performanceMonitor := cli.analyticsEngine.GetPerformanceMonitor()
	kpis := performanceMonitor.GetKPIs()

	fmt.Println("Performance KPIs")
	fmt.Println("================")

	if len(kpis) == 0 {
		fmt.Println("No KPIs available")
		return
	}

	for _, kpi := range kpis {
		fmt.Printf("ID: %s\n", kpi.ID)
		fmt.Printf("Name: %s\n", kpi.Name)
		fmt.Printf("Description: %s\n", kpi.Description)
		fmt.Printf("Current: %.2f %s\n", kpi.Current, kpi.Unit)
		fmt.Printf("Target: %.2f %s\n", kpi.Target, kpi.Unit)
		fmt.Printf("Status: %s\n", kpi.Status)
		fmt.Printf("Trend: %s\n", kpi.Trend)
		fmt.Printf("Last Updated: %s\n", kpi.LastUpdated.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// showAlerts displays performance alerts
func (cli *AnalyticsCLI) showAlerts() {
	status := cli.promptForString("Status (optional): ")

	alerts, err := cli.analyticsEngine.GetAlerts(status)
	if err != nil {
		fmt.Printf("Error getting alerts: %v\n", err)
		return
	}

	fmt.Println("Performance Alerts")
	fmt.Println("==================")

	if len(alerts) == 0 {
		fmt.Println("No alerts available")
		return
	}

	for _, alert := range alerts {
		fmt.Printf("ID: %s\n", alert.ID)
		fmt.Printf("KPI: %s\n", alert.KPIID)
		fmt.Printf("Type: %s\n", alert.Type)
		fmt.Printf("Severity: %s\n", alert.Severity)
		fmt.Printf("Message: %s\n", alert.Message)
		fmt.Printf("Value: %.2f\n", alert.Value)
		fmt.Printf("Threshold: %.2f\n", alert.Threshold)
		fmt.Printf("Status: %s\n", alert.Status)
		fmt.Printf("Created: %s\n", alert.CreatedAt.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// showThresholds displays performance thresholds
func (cli *AnalyticsCLI) showThresholds() {
	performanceMonitor := cli.analyticsEngine.GetPerformanceMonitor()
	thresholds := performanceMonitor.GetThresholds()

	fmt.Println("Performance Thresholds")
	fmt.Println("======================")

	if len(thresholds) == 0 {
		fmt.Println("No thresholds available")
		return
	}

	for _, threshold := range thresholds {
		fmt.Printf("ID: %s\n", threshold.ID)
		fmt.Printf("KPI: %s\n", threshold.KPIID)
		fmt.Printf("Type: %s\n", threshold.Type)
		fmt.Printf("Value: %.2f\n", threshold.Value)
		fmt.Printf("Operator: %s\n", threshold.Operator)
		fmt.Printf("Duration: %s\n", threshold.Duration.String())
		fmt.Printf("Enabled: %t\n", threshold.Enabled)
		fmt.Printf("Created: %s\n", threshold.CreatedAt.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// addKPI adds a new performance KPI
func (cli *AnalyticsCLI) addKPI() {
	kpi := KPI{
		Name:        cli.promptForString("KPI Name: "),
		Description: cli.promptForString("Description: "),
		Metric:      cli.promptForString("Metric: "),
		Target:      cli.promptForFloat("Target: "),
		Current:     0,
		Unit:        cli.promptForString("Unit: "),
		Category:    cli.promptForString("Category: "),
		Frequency:   time.Hour,
		Status:      "active",
	}

	performanceMonitor := cli.analyticsEngine.GetPerformanceMonitor()
	if err := performanceMonitor.CreateKPI(kpi); err != nil {
		fmt.Printf("Error creating KPI: %v\n", err)
		return
	}

	fmt.Println("KPI created successfully")
}

// addThreshold adds a new performance threshold
func (cli *AnalyticsCLI) addThreshold() {
	threshold := Threshold{
		KPIID:    cli.promptForString("KPI ID: "),
		Type:     cli.promptForString("Type: "),
		Value:    cli.promptForFloat("Value: "),
		Operator: cli.promptForString("Operator: "),
		Duration: time.Hour,
		Enabled:  true,
	}

	performanceMonitor := cli.analyticsEngine.GetPerformanceMonitor()
	if err := performanceMonitor.CreateThreshold(threshold); err != nil {
		fmt.Printf("Error creating threshold: %v\n", err)
		return
	}

	fmt.Println("Threshold created successfully")
}

// listAnomalies displays detected anomalies
func (cli *AnalyticsCLI) listAnomalies() {
	severity := cli.promptForString("Severity (optional): ")

	anomalies, err := cli.analyticsEngine.GetAnomalies(severity)
	if err != nil {
		fmt.Printf("Error getting anomalies: %v\n", err)
		return
	}

	fmt.Println("Detected Anomalies")
	fmt.Println("=================")

	if len(anomalies) == 0 {
		fmt.Println("No anomalies detected")
		return
	}

	for _, anomaly := range anomalies {
		fmt.Printf("ID: %s\n", anomaly.ID)
		fmt.Printf("Metric: %s\n", anomaly.Metric)
		fmt.Printf("Value: %.2f\n", anomaly.Value)
		fmt.Printf("Expected: %.2f\n", anomaly.ExpectedValue)
		fmt.Printf("Deviation: %.2f\n", anomaly.Deviation)
		fmt.Printf("Severity: %s\n", anomaly.Severity)
		fmt.Printf("Status: %s\n", anomaly.Status)
		fmt.Printf("Description: %s\n", anomaly.Description)
		fmt.Printf("Timestamp: %s\n", anomaly.Timestamp.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// showDetectionRules displays anomaly detection rules
func (cli *AnalyticsCLI) showDetectionRules() {
	anomalyDetector := cli.analyticsEngine.GetAnomalyDetector()
	rules := anomalyDetector.GetDetectionRules()

	fmt.Println("Anomaly Detection Rules")
	fmt.Println("======================")

	if len(rules) == 0 {
		fmt.Println("No detection rules available")
		return
	}

	for _, rule := range rules {
		fmt.Printf("ID: %s\n", rule.ID)
		fmt.Printf("Name: %s\n", rule.Name)
		fmt.Printf("Description: %s\n", rule.Description)
		fmt.Printf("Metric: %s\n", rule.Metric)
		fmt.Printf("Algorithm: %s\n", rule.Algorithm)
		fmt.Printf("Threshold: %.2f\n", rule.Threshold)
		fmt.Printf("Enabled: %t\n", rule.Enabled)
		fmt.Printf("Created: %s\n", rule.CreatedAt.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// addDetectionRule adds a new anomaly detection rule
func (cli *AnalyticsCLI) addDetectionRule() {
	rule := DetectionRule{
		Name:        cli.promptForString("Rule Name: "),
		Description: cli.promptForString("Description: "),
		Metric:      cli.promptForString("Metric: "),
		Algorithm:   cli.promptForString("Algorithm: "),
		Threshold:   cli.promptForFloat("Threshold: "),
		Enabled:     true,
	}

	anomalyDetector := cli.analyticsEngine.GetAnomalyDetector()
	if err := anomalyDetector.CreateDetectionRule(rule); err != nil {
		fmt.Printf("Error creating rule: %v\n", err)
		return
	}

	fmt.Println("Detection rule created successfully")
}

// resolveAnomaly resolves an anomaly
func (cli *AnalyticsCLI) resolveAnomaly() {
	anomalyID := cli.promptForString("Anomaly ID: ")

	anomalyDetector := cli.analyticsEngine.GetAnomalyDetector()
	if err := anomalyDetector.ResolveAnomaly(anomalyID); err != nil {
		fmt.Printf("Error resolving anomaly: %v\n", err)
		return
	}

	fmt.Println("Anomaly resolved successfully")
}

// listReports displays generated reports
func (cli *AnalyticsCLI) listReports() {
	reportGenerator := cli.analyticsEngine.GetReportGenerator()
	reports := reportGenerator.GetReports()

	fmt.Println("Generated Reports")
	fmt.Println("================")

	if len(reports) == 0 {
		fmt.Println("No reports available")
		return
	}

	for _, report := range reports {
		fmt.Printf("ID: %s\n", report.ID)
		fmt.Printf("Name: %s\n", report.Name)
		fmt.Printf("Type: %s\n", report.Type)
		fmt.Printf("Format: %s\n", report.Format)
		fmt.Printf("Size: %d bytes\n", report.Size)
		fmt.Printf("Status: %s\n", report.Status)
		fmt.Printf("Created: %s\n", report.CreatedAt.Format("2006-01-02 15:04:05"))
		if report.ExpiresAt != nil {
			fmt.Printf("Expires: %s\n", report.ExpiresAt.Format("2006-01-02 15:04:05"))
		}
		fmt.Println("---")
	}
}

// generateReport generates a new report
func (cli *AnalyticsCLI) generateReport() {
	reportType := cli.promptForString("Report Type: ")
	parameters := make(map[string]interface{})

	// Add basic parameters
	parameters["building_id"] = cli.promptForString("Building ID (optional): ")
	parameters["start_time"] = cli.promptForString("Start Time (optional): ")
	parameters["end_time"] = cli.promptForString("End Time (optional): ")

	report, err := cli.analyticsEngine.GenerateReport(reportType, parameters)
	if err != nil {
		fmt.Printf("Error generating report: %v\n", err)
		return
	}

	fmt.Printf("Report generated successfully: %s\n", report.ID)
	fmt.Printf("Size: %d bytes\n", report.Size)
	fmt.Printf("Format: %s\n", report.Format)
}

// showReportTemplates displays report templates
func (cli *AnalyticsCLI) showReportTemplates() {
	reportGenerator := cli.analyticsEngine.GetReportGenerator()
	templates := reportGenerator.GetReportTemplates()

	fmt.Println("Report Templates")
	fmt.Println("================")

	if len(templates) == 0 {
		fmt.Println("No templates available")
		return
	}

	for _, template := range templates {
		fmt.Printf("ID: %s\n", template.ID)
		fmt.Printf("Name: %s\n", template.Name)
		fmt.Printf("Description: %s\n", template.Description)
		fmt.Printf("Type: %s\n", template.Type)
		fmt.Printf("Format: %s\n", template.Format)
		fmt.Printf("Schedule: %s\n", template.Schedule)
		fmt.Printf("Enabled: %t\n", template.Enabled)
		fmt.Printf("Created: %s\n", template.CreatedAt.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

// addReportTemplate adds a new report template
func (cli *AnalyticsCLI) addReportTemplate() {
	template := ReportTemplate{
		Name:        cli.promptForString("Template Name: "),
		Description: cli.promptForString("Description: "),
		Type:        cli.promptForString("Type: "),
		Format:      cli.promptForString("Format: "),
		Template:    cli.promptForString("Template Content: "),
		Schedule:    cli.promptForString("Schedule: "),
		Enabled:     true,
	}

	reportGenerator := cli.analyticsEngine.GetReportGenerator()
	if err := reportGenerator.CreateReportTemplate(template); err != nil {
		fmt.Printf("Error creating template: %v\n", err)
		return
	}

	fmt.Println("Report template created successfully")
}

// showMetrics displays analytics metrics
func (cli *AnalyticsCLI) showMetrics() {
	metrics := cli.analyticsEngine.GetMetrics()

	fmt.Println("Analytics Engine Metrics")
	fmt.Println("========================")
	fmt.Printf("Total Data Points: %d\n", metrics.TotalDataPoints)
	fmt.Printf("Processed Data Points: %d\n", metrics.ProcessedDataPoints)
	fmt.Printf("Active Models: %d\n", metrics.ActiveModels)
	fmt.Printf("Generated Reports: %d\n", metrics.GeneratedReports)
	fmt.Printf("Detected Anomalies: %d\n", metrics.DetectedAnomalies)
	fmt.Printf("Active Alerts: %d\n", metrics.ActiveAlerts)
	fmt.Printf("Average Accuracy: %.2f%%\n", metrics.AverageAccuracy*100)
	fmt.Printf("Processing Time: %.2f ms\n", metrics.ProcessingTimeMs)
	fmt.Printf("Error Rate: %.2f%%\n", metrics.ErrorRate*100)

	// Show energy metrics
	energyOptimizer := cli.analyticsEngine.GetEnergyOptimizer()
	energyMetrics := energyOptimizer.GetEnergyMetrics()
	fmt.Println("\nEnergy Optimization Metrics")
	fmt.Println("===========================")
	fmt.Printf("Total Consumption: %.2f kWh\n", energyMetrics.TotalConsumption)
	fmt.Printf("Baseline Consumption: %.2f kWh\n", energyMetrics.BaselineConsumption)
	fmt.Printf("Savings: %.2f kWh\n", energyMetrics.Savings)
	fmt.Printf("Savings Percentage: %.2f%%\n", energyMetrics.SavingsPercentage)
	fmt.Printf("Optimization Rules: %d\n", energyMetrics.OptimizationRules)
	fmt.Printf("Active Recommendations: %d\n", energyMetrics.ActiveRecommendations)
	fmt.Printf("Average Efficiency: %.2f%%\n", energyMetrics.AverageEfficiency)

	// Show predictive metrics
	predictiveEngine := cli.analyticsEngine.GetPredictiveEngine()
	predictiveMetrics := predictiveEngine.GetPredictiveMetrics()
	fmt.Println("\nPredictive Analytics Metrics")
	fmt.Println("============================")
	fmt.Printf("Total Models: %d\n", predictiveMetrics.TotalModels)
	fmt.Printf("Active Models: %d\n", predictiveMetrics.ActiveModels)
	fmt.Printf("Training Models: %d\n", predictiveMetrics.TrainingModels)
	fmt.Printf("Error Models: %d\n", predictiveMetrics.ErrorModels)
	fmt.Printf("Total Forecasts: %d\n", predictiveMetrics.TotalForecasts)
	fmt.Printf("Accurate Forecasts: %d\n", predictiveMetrics.AccurateForecasts)
	fmt.Printf("Average Accuracy: %.2f%%\n", predictiveMetrics.AverageAccuracy*100)
	fmt.Printf("Average Precision: %.2f%%\n", predictiveMetrics.AveragePrecision*100)
	fmt.Printf("Average Recall: %.2f%%\n", predictiveMetrics.AverageRecall*100)
	fmt.Printf("Average F1 Score: %.2f%%\n", predictiveMetrics.AverageF1Score*100)

	// Show performance metrics
	performanceMonitor := cli.analyticsEngine.GetPerformanceMonitor()
	performanceMetrics := performanceMonitor.GetPerformanceMetrics()
	fmt.Println("\nPerformance Monitoring Metrics")
	fmt.Println("==============================")
	fmt.Printf("Total KPIs: %d\n", performanceMetrics.TotalKPIs)
	fmt.Printf("Active KPIs: %d\n", performanceMetrics.ActiveKPIs)
	fmt.Printf("Total Thresholds: %d\n", performanceMetrics.TotalThresholds)
	fmt.Printf("Active Thresholds: %d\n", performanceMetrics.ActiveThresholds)
	fmt.Printf("Total Alerts: %d\n", performanceMetrics.TotalAlerts)
	fmt.Printf("Active Alerts: %d\n", performanceMetrics.ActiveAlerts)
	fmt.Printf("Resolved Alerts: %d\n", performanceMetrics.ResolvedAlerts)
	fmt.Printf("Average Response Time: %.2f ms\n", performanceMetrics.AverageResponseTime)
	fmt.Printf("Alert Accuracy: %.2f%%\n", performanceMetrics.AlertAccuracy*100)

	// Show anomaly metrics
	anomalyDetector := cli.analyticsEngine.GetAnomalyDetector()
	anomalyMetrics := anomalyDetector.GetAnomalyMetrics()
	fmt.Println("\nAnomaly Detection Metrics")
	fmt.Println("=========================")
	fmt.Printf("Total Rules: %d\n", anomalyMetrics.TotalRules)
	fmt.Printf("Active Rules: %d\n", anomalyMetrics.ActiveRules)
	fmt.Printf("Total Anomalies: %d\n", anomalyMetrics.TotalAnomalies)
	fmt.Printf("New Anomalies: %d\n", anomalyMetrics.NewAnomalies)
	fmt.Printf("Resolved Anomalies: %d\n", anomalyMetrics.ResolvedAnomalies)
	fmt.Printf("False Positives: %d\n", anomalyMetrics.FalsePositives)
	fmt.Printf("True Positives: %d\n", anomalyMetrics.TruePositives)
	fmt.Printf("Detection Accuracy: %.2f%%\n", anomalyMetrics.DetectionAccuracy*100)
	fmt.Printf("Average Detection Time: %.2f ms\n", anomalyMetrics.AverageDetectionTime)

	// Show report metrics
	reportGenerator := cli.analyticsEngine.GetReportGenerator()
	reportMetrics := reportGenerator.GetReportMetrics()
	fmt.Println("\nReport Generation Metrics")
	fmt.Println("=========================")
	fmt.Printf("Total Templates: %d\n", reportMetrics.TotalTemplates)
	fmt.Printf("Active Templates: %d\n", reportMetrics.ActiveTemplates)
	fmt.Printf("Total Reports: %d\n", reportMetrics.TotalReports)
	fmt.Printf("Generated Reports: %d\n", reportMetrics.GeneratedReports)
	fmt.Printf("Failed Reports: %d\n", reportMetrics.FailedReports)
	fmt.Printf("Average Generation Time: %.2f ms\n", reportMetrics.AverageGenerationTime)
	fmt.Printf("Total Size: %d bytes\n", reportMetrics.TotalSize)
}

// Helper methods for user input
func (cli *AnalyticsCLI) promptForString(prompt string) string {
	fmt.Print(prompt)
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	return strings.TrimSpace(input)
}

func (cli *AnalyticsCLI) promptForInt(prompt string) int {
	for {
		input := cli.promptForString(prompt)
		if value, err := strconv.Atoi(input); err == nil {
			return value
		}
		fmt.Println("Invalid input. Please enter a number.")
	}
}

func (cli *AnalyticsCLI) promptForFloat(prompt string) float64 {
	for {
		input := cli.promptForString(prompt)
		if value, err := strconv.ParseFloat(input, 64); err == nil {
			return value
		}
		fmt.Println("Invalid input. Please enter a number.")
	}
}
