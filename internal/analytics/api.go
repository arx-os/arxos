package analytics

import (
	"encoding/json"
	"net/http"
	"time"
)

// AnalyticsAPI provides HTTP API for analytics
type AnalyticsAPI struct {
	analyticsEngine *AnalyticsEngine
}

// NewAnalyticsAPI creates a new analytics API
func NewAnalyticsAPI(analyticsEngine *AnalyticsEngine) *AnalyticsAPI {
	return &AnalyticsAPI{
		analyticsEngine: analyticsEngine,
	}
}

// RegisterRoutes registers analytics API routes
func (api *AnalyticsAPI) RegisterRoutes(mux *http.ServeMux) {
	// Energy optimization routes
	mux.HandleFunc("/api/analytics/energy/data", api.handleEnergyData)
	mux.HandleFunc("/api/analytics/energy/recommendations", api.handleEnergyRecommendations)
	mux.HandleFunc("/api/analytics/energy/baseline", api.handleEnergyBaseline)
	mux.HandleFunc("/api/analytics/energy/savings", api.handleEnergySavings)

	// Predictive analytics routes
	mux.HandleFunc("/api/analytics/predictive/models", api.handlePredictiveModels)
	mux.HandleFunc("/api/analytics/predictive/forecasts", api.handlePredictiveForecasts)
	mux.HandleFunc("/api/analytics/predictive/trends", api.handlePredictiveTrends)

	// Performance monitoring routes
	mux.HandleFunc("/api/analytics/performance/kpis", api.handlePerformanceKPIs)
	mux.HandleFunc("/api/analytics/performance/alerts", api.handlePerformanceAlerts)
	mux.HandleFunc("/api/analytics/performance/thresholds", api.handlePerformanceThresholds)

	// Anomaly detection routes
	mux.HandleFunc("/api/analytics/anomalies", api.handleAnomalies)
	mux.HandleFunc("/api/analytics/anomalies/rules", api.handleAnomalyRules)

	// Report generation routes
	mux.HandleFunc("/api/analytics/reports", api.handleReports)
	mux.HandleFunc("/api/analytics/reports/templates", api.handleReportTemplates)

	// General analytics routes
	mux.HandleFunc("/api/analytics/metrics", api.handleMetrics)
	mux.HandleFunc("/api/analytics/process", api.handleProcessData)
}

// handleEnergyData handles energy data requests
func (api *AnalyticsAPI) handleEnergyData(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getEnergyData(w, r)
	case http.MethodPost:
		api.postEnergyData(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getEnergyData gets energy consumption data
func (api *AnalyticsAPI) getEnergyData(w http.ResponseWriter, r *http.Request) {
	buildingID := r.URL.Query().Get("building_id")
	startTimeStr := r.URL.Query().Get("start_time")
	endTimeStr := r.URL.Query().Get("end_time")

	var startTime, endTime time.Time
	var err error

	if startTimeStr != "" {
		startTime, err = time.Parse(time.RFC3339, startTimeStr)
		if err != nil {
			http.Error(w, "Invalid start_time format", http.StatusBadRequest)
			return
		}
	} else {
		startTime = time.Now().Add(-24 * time.Hour)
	}

	if endTimeStr != "" {
		endTime, err = time.Parse(time.RFC3339, endTimeStr)
		if err != nil {
			http.Error(w, "Invalid end_time format", http.StatusBadRequest)
			return
		}
	} else {
		endTime = time.Now()
	}

	energyOptimizer := api.analyticsEngine.GetEnergyOptimizer()
	data, err := energyOptimizer.GetConsumptionData(buildingID, startTime, endTime)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// postEnergyData posts new energy data
func (api *AnalyticsAPI) postEnergyData(w http.ResponseWriter, r *http.Request) {
	var dataPoint EnergyDataPoint
	if err := json.NewDecoder(r.Body).Decode(&dataPoint); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.analyticsEngine.ProcessDataPoint(dataPoint); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// handleEnergyRecommendations handles energy recommendations requests
func (api *AnalyticsAPI) handleEnergyRecommendations(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	buildingID := r.URL.Query().Get("building_id")

	recommendations, err := api.analyticsEngine.GetOptimizationRecommendations(buildingID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(recommendations)
}

// handleEnergyBaseline handles energy baseline requests
func (api *AnalyticsAPI) handleEnergyBaseline(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	buildingID := r.URL.Query().Get("building_id")

	energyOptimizer := api.analyticsEngine.GetEnergyOptimizer()
	baseline, err := energyOptimizer.GetBaselineData(buildingID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(baseline)
}

// handleEnergySavings handles energy savings requests
func (api *AnalyticsAPI) handleEnergySavings(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	buildingID := r.URL.Query().Get("building_id")
	timeWindowStr := r.URL.Query().Get("time_window")

	timeWindow, err := time.ParseDuration(timeWindowStr)
	if err != nil {
		timeWindow = 24 * time.Hour // Default to 24 hours
	}

	energyOptimizer := api.analyticsEngine.GetEnergyOptimizer()
	savings, err := energyOptimizer.CalculateEnergySavings(buildingID, timeWindow)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"savings_percentage": savings,
		"time_window":        timeWindow.String(),
		"building_id":        buildingID,
	})
}

// handlePredictiveModels handles predictive models requests
func (api *AnalyticsAPI) handlePredictiveModels(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getPredictiveModels(w, r)
	case http.MethodPost:
		api.postPredictiveModel(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getPredictiveModels gets all predictive models
func (api *AnalyticsAPI) getPredictiveModels(w http.ResponseWriter, r *http.Request) {
	predictiveEngine := api.analyticsEngine.GetPredictiveEngine()
	models := predictiveEngine.GetModels()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models)
}

// postPredictiveModel creates a new predictive model
func (api *AnalyticsAPI) postPredictiveModel(w http.ResponseWriter, r *http.Request) {
	var model PredictiveModel
	if err := json.NewDecoder(r.Body).Decode(&model); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	predictiveEngine := api.analyticsEngine.GetPredictiveEngine()
	if err := predictiveEngine.CreateModel(model); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// handlePredictiveForecasts handles predictive forecasts requests
func (api *AnalyticsAPI) handlePredictiveForecasts(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metric := r.URL.Query().Get("metric")
	durationStr := r.URL.Query().Get("duration")

	duration, err := time.ParseDuration(durationStr)
	if err != nil {
		duration = 24 * time.Hour // Default to 24 hours
	}

	forecast, err := api.analyticsEngine.GetForecast(metric, duration)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(forecast)
}

// handlePredictiveTrends handles predictive trends requests
func (api *AnalyticsAPI) handlePredictiveTrends(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metric := r.URL.Query().Get("metric")

	predictiveEngine := api.analyticsEngine.GetPredictiveEngine()
	trends, err := predictiveEngine.GetTrends(metric)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(trends)
}

// handlePerformanceKPIs handles performance KPIs requests
func (api *AnalyticsAPI) handlePerformanceKPIs(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getPerformanceKPIs(w, r)
	case http.MethodPost:
		api.postPerformanceKPI(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getPerformanceKPIs gets all performance KPIs
func (api *AnalyticsAPI) getPerformanceKPIs(w http.ResponseWriter, r *http.Request) {
	performanceMonitor := api.analyticsEngine.GetPerformanceMonitor()
	kpis := performanceMonitor.GetKPIs()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(kpis)
}

// postPerformanceKPI creates a new performance KPI
func (api *AnalyticsAPI) postPerformanceKPI(w http.ResponseWriter, r *http.Request) {
	var kpi KPI
	if err := json.NewDecoder(r.Body).Decode(&kpi); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	performanceMonitor := api.analyticsEngine.GetPerformanceMonitor()
	if err := performanceMonitor.CreateKPI(kpi); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// handlePerformanceAlerts handles performance alerts requests
func (api *AnalyticsAPI) handlePerformanceAlerts(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	status := r.URL.Query().Get("status")

	alerts, err := api.analyticsEngine.GetAlerts(status)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(alerts)
}

// handlePerformanceThresholds handles performance thresholds requests
func (api *AnalyticsAPI) handlePerformanceThresholds(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getPerformanceThresholds(w, r)
	case http.MethodPost:
		api.postPerformanceThreshold(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getPerformanceThresholds gets all performance thresholds
func (api *AnalyticsAPI) getPerformanceThresholds(w http.ResponseWriter, r *http.Request) {
	performanceMonitor := api.analyticsEngine.GetPerformanceMonitor()
	thresholds := performanceMonitor.GetThresholds()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(thresholds)
}

// postPerformanceThreshold creates a new performance threshold
func (api *AnalyticsAPI) postPerformanceThreshold(w http.ResponseWriter, r *http.Request) {
	var threshold Threshold
	if err := json.NewDecoder(r.Body).Decode(&threshold); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	performanceMonitor := api.analyticsEngine.GetPerformanceMonitor()
	if err := performanceMonitor.CreateThreshold(threshold); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// handleAnomalies handles anomalies requests
func (api *AnalyticsAPI) handleAnomalies(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	severity := r.URL.Query().Get("severity")

	anomalies, err := api.analyticsEngine.GetAnomalies(severity)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(anomalies)
}

// handleAnomalyRules handles anomaly rules requests
func (api *AnalyticsAPI) handleAnomalyRules(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getAnomalyRules(w, r)
	case http.MethodPost:
		api.postAnomalyRule(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getAnomalyRules gets all anomaly detection rules
func (api *AnalyticsAPI) getAnomalyRules(w http.ResponseWriter, r *http.Request) {
	anomalyDetector := api.analyticsEngine.GetAnomalyDetector()
	rules := anomalyDetector.GetDetectionRules()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(rules)
}

// postAnomalyRule creates a new anomaly detection rule
func (api *AnalyticsAPI) postAnomalyRule(w http.ResponseWriter, r *http.Request) {
	var rule DetectionRule
	if err := json.NewDecoder(r.Body).Decode(&rule); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	anomalyDetector := api.analyticsEngine.GetAnomalyDetector()
	if err := anomalyDetector.CreateDetectionRule(rule); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// handleReports handles reports requests
func (api *AnalyticsAPI) handleReports(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getReports(w, r)
	case http.MethodPost:
		api.postReport(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getReports gets all reports
func (api *AnalyticsAPI) getReports(w http.ResponseWriter, r *http.Request) {
	reportGenerator := api.analyticsEngine.GetReportGenerator()
	reports := reportGenerator.GetReports()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(reports)
}

// postReport generates a new report
func (api *AnalyticsAPI) postReport(w http.ResponseWriter, r *http.Request) {
	var request struct {
		Type       string                 `json:"type"`
		Parameters map[string]interface{} `json:"parameters"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	report, err := api.analyticsEngine.GenerateReport(request.Type, request.Parameters)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(report)
}

// handleReportTemplates handles report templates requests
func (api *AnalyticsAPI) handleReportTemplates(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	reportGenerator := api.analyticsEngine.GetReportGenerator()
	templates := reportGenerator.GetReportTemplates()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(templates)
}

// handleMetrics handles analytics metrics requests
func (api *AnalyticsAPI) handleMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.analyticsEngine.GetMetrics()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// handleProcessData handles data processing requests
func (api *AnalyticsAPI) handleProcessData(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var dataPoint EnergyDataPoint
	if err := json.NewDecoder(r.Body).Decode(&dataPoint); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.analyticsEngine.ProcessDataPoint(dataPoint); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}
