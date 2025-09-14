// Package maintenance implements predictive maintenance analysis for building equipment
package maintenance

import (
	"context"
	"fmt"
	"math"
	"sort"
	"time"

	"github.com/joelpate/arxos/internal/connections"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// Predictor analyzes equipment health and predicts maintenance needs
type Predictor struct {
	db          database.DB
	connManager *connections.Manager
	history     *MetricsHistory
}

// NewPredictor creates a new predictive maintenance analyzer
func NewPredictor(db database.DB, connManager *connections.Manager) *Predictor {
	return &Predictor{
		db:          db,
		connManager: connManager,
		history:     NewMetricsHistory(),
	}
}

// MaintenanceAlert represents a predicted maintenance requirement
type MaintenanceAlert struct {
	EquipmentID     string                `json:"equipment_id"`
	EquipmentName   string                `json:"equipment_name"`
	AlertType       MaintenanceAlertType  `json:"alert_type"`
	Severity        AlertSeverity         `json:"severity"`
	PredictedDate   time.Time             `json:"predicted_date"`
	Confidence      float64               `json:"confidence"`
	Description     string                `json:"description"`
	Recommendations []string              `json:"recommendations"`
	Indicators      []MaintenanceIndicator `json:"indicators"`
	EstimatedCost   float64               `json:"estimated_cost"`
}

// MaintenanceAlertType represents the type of maintenance needed
type MaintenanceAlertType string

const (
	AlertTypePreventive MaintenanceAlertType = "preventive"
	AlertTypePredictive MaintenanceAlertType = "predictive"
	AlertTypeEmergency  MaintenanceAlertType = "emergency"
	AlertTypeScheduled  MaintenanceAlertType = "scheduled"
)

// AlertSeverity represents the urgency of the maintenance alert
type AlertSeverity string

const (
	SeverityLow      AlertSeverity = "low"
	SeverityMedium   AlertSeverity = "medium"
	SeverityHigh     AlertSeverity = "high"
	SeverityCritical AlertSeverity = "critical"
)

// MaintenanceIndicator represents a specific health indicator
type MaintenanceIndicator struct {
	Name        string    `json:"name"`
	Value       float64   `json:"value"`
	Threshold   float64   `json:"threshold"`
	Unit        string    `json:"unit"`
	Trend       string    `json:"trend"` // improving, stable, degrading
	LastUpdated time.Time `json:"last_updated"`
}

// EquipmentHealth represents the current health status of equipment
type EquipmentHealth struct {
	EquipmentID          string                  `json:"equipment_id"`
	OverallScore         float64                 `json:"overall_score"` // 0-100
	HealthStatus         HealthStatus            `json:"health_status"`
	LastMaintenanceDate  *time.Time              `json:"last_maintenance_date"`
	NextScheduledDate    *time.Time              `json:"next_scheduled_date"`
	OperationalHours     float64                 `json:"operational_hours"`
	EfficiencyRating     float64                 `json:"efficiency_rating"`
	FailureProbability   float64                 `json:"failure_probability"`
	Indicators           []MaintenanceIndicator  `json:"indicators"`
	MaintenanceHistory   []MaintenanceRecord     `json:"maintenance_history"`
}

// HealthStatus represents the overall health of equipment
type HealthStatus string

const (
	HealthExcellent HealthStatus = "excellent"
	HealthGood      HealthStatus = "good"
	HealthFair      HealthStatus = "fair"
	HealthPoor      HealthStatus = "poor"
	HealthCritical  HealthStatus = "critical"
)

// MaintenanceRecord represents a historical maintenance event
type MaintenanceRecord struct {
	Date        time.Time `json:"date"`
	Type        string    `json:"type"`
	Description string    `json:"description"`
	Cost        float64   `json:"cost"`
	Technician  string    `json:"technician"`
	Duration    int       `json:"duration_minutes"`
}

// AnalyzeEquipmentHealth performs comprehensive health analysis for equipment
func (p *Predictor) AnalyzeEquipmentHealth(ctx context.Context, equipmentID string) (*EquipmentHealth, error) {
	equipment, err := p.db.GetEquipment(ctx, equipmentID)
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	health := &EquipmentHealth{
		EquipmentID:        equipmentID,
		MaintenanceHistory: p.getMaintenanceHistory(equipmentID),
		Indicators:         []MaintenanceIndicator{},
	}

	// Analyze different health aspects
	p.analyzeElectricalHealth(health, equipment)
	p.analyzeUsagePatterns(health, equipment)
	p.analyzeEnvironmentalFactors(health, equipment)
	p.analyzeConnectionHealth(health, equipment)

	// Calculate overall health score
	health.OverallScore = p.calculateOverallScore(health)
	health.HealthStatus = p.determineHealthStatus(health.OverallScore)
	health.FailureProbability = p.calculateFailureProbability(health)

	// Estimate next maintenance dates
	p.estimateMaintenanceDates(health, equipment)

	return health, nil
}

// PredictMaintenanceNeeds generates maintenance alerts for equipment
func (p *Predictor) PredictMaintenanceNeeds(ctx context.Context, equipmentIDs []string) ([]MaintenanceAlert, error) {
	var alerts []MaintenanceAlert

	for _, equipmentID := range equipmentIDs {
		equipment, err := p.db.GetEquipment(ctx, equipmentID)
		if err != nil {
			logger.Warn("Failed to analyze equipment %s: %v", equipmentID, err)
			continue
		}

		health, err := p.AnalyzeEquipmentHealth(ctx, equipmentID)
		if err != nil {
			logger.Warn("Failed to analyze health for %s: %v", equipmentID, err)
			continue
		}

		// Generate alerts based on health analysis
		equipmentAlerts := p.generateAlertsFromHealth(equipment, health)
		alerts = append(alerts, equipmentAlerts...)
	}

	// Sort alerts by severity and predicted date
	sort.Slice(alerts, func(i, j int) bool {
		if alerts[i].Severity != alerts[j].Severity {
			return getSeverityWeight(alerts[i].Severity) > getSeverityWeight(alerts[j].Severity)
		}
		return alerts[i].PredictedDate.Before(alerts[j].PredictedDate)
	})

	return alerts, nil
}

// AnalyzeSystemWidePatterns looks for patterns across the entire building
func (p *Predictor) AnalyzeSystemWidePatterns(ctx context.Context) (*SystemAnalysis, error) {
	// Get all equipment
	plans, err := p.db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get floor plans: %w", err)
	}

	analysis := &SystemAnalysis{
		TotalEquipment:    0,
		HealthDistribution: make(map[HealthStatus]int),
		SystemInsights:    []SystemInsight{},
		Recommendations:   []string{},
	}

	var allEquipment []*models.Equipment
	for _, plan := range plans {
		allEquipment = append(allEquipment, plan.Equipment...)
	}

	analysis.TotalEquipment = len(allEquipment)

	// Analyze each piece of equipment
	var healthScores []float64
	for _, equipment := range allEquipment {
		health, err := p.AnalyzeEquipmentHealth(ctx, equipment.ID)
		if err != nil {
			continue
		}

		analysis.HealthDistribution[health.HealthStatus]++
		healthScores = append(healthScores, health.OverallScore)
	}

	// Calculate system-wide metrics
	if len(healthScores) > 0 {
		analysis.AverageHealthScore = average(healthScores)
		analysis.HealthVariance = variance(healthScores)
	}

	// Generate system insights
	p.generateSystemInsights(analysis, allEquipment)

	return analysis, nil
}

// SystemAnalysis represents system-wide maintenance patterns
type SystemAnalysis struct {
	TotalEquipment       int                    `json:"total_equipment"`
	AverageHealthScore   float64                `json:"average_health_score"`
	HealthVariance       float64                `json:"health_variance"`
	HealthDistribution   map[HealthStatus]int   `json:"health_distribution"`
	SystemInsights       []SystemInsight        `json:"system_insights"`
	Recommendations      []string               `json:"recommendations"`
	PredictedDowntime    time.Duration          `json:"predicted_downtime"`
	EstimatedMaintenanceCost float64           `json:"estimated_maintenance_cost"`
}

// SystemInsight represents a system-wide pattern or insight
type SystemInsight struct {
	Category    string    `json:"category"`
	Description string    `json:"description"`
	Impact      string    `json:"impact"`
	Confidence  float64   `json:"confidence"`
	Equipment   []string  `json:"affected_equipment"`
}

// Private methods for health analysis

func (p *Predictor) analyzeElectricalHealth(health *EquipmentHealth, equipment *models.Equipment) {
	// Analyze electrical patterns based on equipment type
	switch equipment.Type {
	case "panel", "breaker", "transformer":
		// High-power equipment analysis
		health.Indicators = append(health.Indicators, MaintenanceIndicator{
			Name:        "Load Balance",
			Value:       85.0, // Simulated - would come from energy analysis
			Threshold:   90.0,
			Unit:        "%",
			Trend:       "stable",
			LastUpdated: time.Now(),
		})

	case "outlet", "switch":
		// Low-power equipment analysis
		health.Indicators = append(health.Indicators, MaintenanceIndicator{
			Name:        "Contact Resistance",
			Value:       0.05, // Simulated
			Threshold:   0.1,
			Unit:        "Ω",
			Trend:       "stable",
			LastUpdated: time.Now(),
		})
	}
}

func (p *Predictor) analyzeUsagePatterns(health *EquipmentHealth, equipment *models.Equipment) {
	// Simulate usage pattern analysis
	baseHours := 8760.0 // Hours in a year
	
	switch equipment.Type {
	case "hvac":
		health.OperationalHours = baseHours * 0.6 // HVAC runs ~60% of time
		health.EfficiencyRating = 82.0
	case "server", "computer":
		health.OperationalHours = baseHours * 0.9 // IT equipment runs ~90% of time
		health.EfficiencyRating = 95.0
	default:
		health.OperationalHours = baseHours * 0.3
		health.EfficiencyRating = 88.0
	}

	health.Indicators = append(health.Indicators, MaintenanceIndicator{
		Name:        "Usage Hours",
		Value:       health.OperationalHours,
		Threshold:   baseHours * 0.8,
		Unit:        "hours",
		Trend:       "increasing",
		LastUpdated: time.Now(),
	})
}

func (p *Predictor) analyzeEnvironmentalFactors(health *EquipmentHealth, equipment *models.Equipment) {
	// Simulate environmental analysis
	health.Indicators = append(health.Indicators, MaintenanceIndicator{
		Name:        "Operating Temperature",
		Value:       72.0, // Simulated
		Threshold:   85.0,
		Unit:        "°F",
		Trend:       "stable",
		LastUpdated: time.Now(),
	})

	if equipment.Type == "server" || equipment.Type == "computer" {
		health.Indicators = append(health.Indicators, MaintenanceIndicator{
			Name:        "Dust Accumulation",
			Value:       25.0, // Simulated percentage
			Threshold:   40.0,
			Unit:        "%",
			Trend:       "increasing",
			LastUpdated: time.Now(),
		})
	}
}

func (p *Predictor) analyzeConnectionHealth(health *EquipmentHealth, equipment *models.Equipment) {
	// Analyze connection quality and patterns
	downstream := p.connManager.GetDownstream(equipment.ID)
	upstream := p.connManager.GetUpstream(equipment.ID)
	
	connectionLoad := float64(len(downstream) + len(upstream))
	health.Indicators = append(health.Indicators, MaintenanceIndicator{
		Name:        "Connection Load",
		Value:       connectionLoad,
		Threshold:   10.0, // Arbitrary threshold
		Unit:        "connections",
		Trend:       "stable",
		LastUpdated: time.Now(),
	})
}

func (p *Predictor) calculateOverallScore(health *EquipmentHealth) float64 {
	if len(health.Indicators) == 0 {
		return 50.0 // Default middle score
	}

	var totalScore float64
	var weights float64

	for _, indicator := range health.Indicators {
		// Calculate indicator health (0-100)
		indicatorHealth := 100.0
		if indicator.Value > indicator.Threshold {
			// Above threshold is bad
			overage := indicator.Value - indicator.Threshold
			indicatorHealth = math.Max(0, 100.0-overage*2)
		}

		// Weight different indicators
		weight := 1.0
		if indicator.Name == "Usage Hours" {
			weight = 2.0 // Usage is more important
		}

		totalScore += indicatorHealth * weight
		weights += weight
	}

	score := totalScore / weights
	
	// Factor in efficiency rating
	if health.EfficiencyRating > 0 {
		score = (score + health.EfficiencyRating) / 2
	}

	return math.Min(100.0, math.Max(0.0, score))
}

func (p *Predictor) determineHealthStatus(score float64) HealthStatus {
	switch {
	case score >= 90:
		return HealthExcellent
	case score >= 75:
		return HealthGood
	case score >= 60:
		return HealthFair
	case score >= 40:
		return HealthPoor
	default:
		return HealthCritical
	}
}

func (p *Predictor) calculateFailureProbability(health *EquipmentHealth) float64 {
	// Simple failure probability based on health score
	baseFailureRate := (100.0 - health.OverallScore) / 100.0
	
	// Adjust based on operational hours
	if health.OperationalHours > 8000 { // More than typical year
		baseFailureRate *= 1.2
	}

	return math.Min(1.0, baseFailureRate)
}

func (p *Predictor) estimateMaintenanceDates(health *EquipmentHealth, equipment *models.Equipment) {
	now := time.Now()
	
	// Estimate next scheduled maintenance based on equipment type
	var maintenanceInterval time.Duration
	switch equipment.Type {
	case "hvac":
		maintenanceInterval = 90 * 24 * time.Hour // Quarterly
	case "server", "computer":
		maintenanceInterval = 180 * 24 * time.Hour // Semi-annually
	case "panel", "transformer":
		maintenanceInterval = 365 * 24 * time.Hour // Annually
	default:
		maintenanceInterval = 180 * 24 * time.Hour // Default semi-annual
	}

	// Adjust based on health score
	if health.OverallScore < 60 {
		maintenanceInterval = time.Duration(float64(maintenanceInterval) * 0.5) // More frequent
	}

	nextDate := now.Add(maintenanceInterval)
	health.NextScheduledDate = &nextDate
}

func (p *Predictor) generateAlertsFromHealth(equipment *models.Equipment, health *EquipmentHealth) []MaintenanceAlert {
	var alerts []MaintenanceAlert

	// Critical health alert
	if health.HealthStatus == HealthCritical {
		alerts = append(alerts, MaintenanceAlert{
			EquipmentID:   equipment.ID,
			EquipmentName: equipment.Name,
			AlertType:     AlertTypeEmergency,
			Severity:      SeverityCritical,
			PredictedDate: time.Now().Add(24 * time.Hour),
			Confidence:    0.95,
			Description:   "Equipment health is critical and requires immediate attention",
			Recommendations: []string{
				"Schedule emergency maintenance",
				"Consider equipment replacement",
				"Monitor closely for failure signs",
			},
			EstimatedCost: p.estimateMaintenanceCost(equipment, AlertTypeEmergency),
		})
	}

	// Predictive maintenance alerts
	if health.FailureProbability > 0.3 {
		daysUntilMaintenance := int((1.0 - health.FailureProbability) * 30)
		alerts = append(alerts, MaintenanceAlert{
			EquipmentID:   equipment.ID,
			EquipmentName: equipment.Name,
			AlertType:     AlertTypePredictive,
			Severity:      p.getSeverityFromProbability(health.FailureProbability),
			PredictedDate: time.Now().Add(time.Duration(daysUntilMaintenance) * 24 * time.Hour),
			Confidence:    health.FailureProbability,
			Description:   fmt.Sprintf("Equipment showing signs of degradation (%.1f%% failure probability)", health.FailureProbability*100),
			Recommendations: p.getRecommendationsForEquipment(equipment),
			EstimatedCost: p.estimateMaintenanceCost(equipment, AlertTypePredictive),
		})
	}

	// Add indicator-specific alerts
	for _, indicator := range health.Indicators {
		if indicator.Value > indicator.Threshold {
			alerts = append(alerts, p.createIndicatorAlert(equipment, indicator))
		}
	}

	return alerts
}

func (p *Predictor) getSeverityFromProbability(probability float64) AlertSeverity {
	switch {
	case probability > 0.7:
		return SeverityCritical
	case probability > 0.5:
		return SeverityHigh
	case probability > 0.3:
		return SeverityMedium
	default:
		return SeverityLow
	}
}

func (p *Predictor) getRecommendationsForEquipment(equipment *models.Equipment) []string {
	switch equipment.Type {
	case "hvac":
		return []string{
			"Replace air filters",
			"Clean coils and fins",
			"Check refrigerant levels",
			"Inspect electrical connections",
		}
	case "server", "computer":
		return []string{
			"Clean dust from components",
			"Check thermal paste application",
			"Update firmware and software",
			"Test backup systems",
		}
	case "panel", "breaker":
		return []string{
			"Inspect electrical connections",
			"Test circuit breaker operation",
			"Check for signs of overheating",
			"Verify load balancing",
		}
	default:
		return []string{
			"Perform routine inspection",
			"Clean and lubricate as needed",
			"Check connections and fasteners",
			"Update documentation",
		}
	}
}

func (p *Predictor) createIndicatorAlert(equipment *models.Equipment, indicator MaintenanceIndicator) MaintenanceAlert {
	return MaintenanceAlert{
		EquipmentID:   equipment.ID,
		EquipmentName: equipment.Name,
		AlertType:     AlertTypePreventive,
		Severity:      SeverityMedium,
		PredictedDate: time.Now().Add(7 * 24 * time.Hour), // Next week
		Confidence:    0.8,
		Description:   fmt.Sprintf("%s exceeds threshold: %.2f %s (limit: %.2f %s)", 
			indicator.Name, indicator.Value, indicator.Unit, indicator.Threshold, indicator.Unit),
		Recommendations: []string{
			fmt.Sprintf("Address %s issue", indicator.Name),
			"Schedule inspection",
		},
		Indicators:    []MaintenanceIndicator{indicator},
		EstimatedCost: p.estimateMaintenanceCost(equipment, AlertTypePreventive),
	}
}

func (p *Predictor) estimateMaintenanceCost(equipment *models.Equipment, alertType MaintenanceAlertType) float64 {
	baseCost := 100.0 // Base cost in dollars

	// Equipment type multiplier
	switch equipment.Type {
	case "hvac":
		baseCost *= 5.0
	case "server", "computer":
		baseCost *= 2.0
	case "panel", "transformer":
		baseCost *= 8.0
	default:
		baseCost *= 1.5
	}

	// Alert type multiplier
	switch alertType {
	case AlertTypeEmergency:
		baseCost *= 3.0
	case AlertTypePredictive:
		baseCost *= 1.5
	case AlertTypePreventive:
		baseCost *= 1.0
	case AlertTypeScheduled:
		baseCost *= 0.8
	}

	return baseCost
}

func (p *Predictor) generateSystemInsights(analysis *SystemAnalysis, equipment []*models.Equipment) {
	// Analyze equipment age patterns
	if analysis.AverageHealthScore < 70 {
		analysis.SystemInsights = append(analysis.SystemInsights, SystemInsight{
			Category:    "System Health",
			Description: "Overall system health is below optimal levels",
			Impact:      "Increased risk of failures and higher maintenance costs",
			Confidence:  0.85,
		})
	}

	// Analyze equipment distribution
	criticalCount := analysis.HealthDistribution[HealthCritical]
	if criticalCount > len(equipment)/10 { // More than 10% critical
		analysis.SystemInsights = append(analysis.SystemInsights, SystemInsight{
			Category:    "Critical Equipment",
			Description: fmt.Sprintf("%d pieces of equipment are in critical condition", criticalCount),
			Impact:      "High risk of system failures and downtime",
			Confidence:  0.95,
		})
		
		analysis.Recommendations = append(analysis.Recommendations,
			"Prioritize maintenance for critical equipment",
			"Consider emergency maintenance budget allocation",
		)
	}

	// Calculate estimated costs
	totalCost := 0.0
	for _, eq := range equipment {
		totalCost += p.estimateMaintenanceCost(eq, AlertTypePreventive)
	}
	analysis.EstimatedMaintenanceCost = totalCost
}

func (p *Predictor) getMaintenanceHistory(equipmentID string) []MaintenanceRecord {
	// Simulate maintenance history - in production this would query the database
	return []MaintenanceRecord{
		{
			Date:        time.Now().AddDate(0, -3, 0),
			Type:        "Preventive",
			Description: "Routine maintenance check",
			Cost:        150.0,
			Technician:  "John Smith",
			Duration:    60,
		},
	}
}

// Utility functions

func getSeverityWeight(severity AlertSeverity) int {
	switch severity {
	case SeverityCritical:
		return 4
	case SeverityHigh:
		return 3
	case SeverityMedium:
		return 2
	case SeverityLow:
		return 1
	default:
		return 0
	}
}

func average(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func variance(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	avg := average(values)
	sumSquares := 0.0
	for _, v := range values {
		diff := v - avg
		sumSquares += diff * diff
	}
	return sumSquares / float64(len(values))
}

// GetScheduledMaintenanceCount returns the number of scheduled maintenance tasks
func (p *Predictor) GetScheduledMaintenanceCount(ctx context.Context) (int, error) {
	// Query database for scheduled maintenance tasks
	// This is a simplified implementation - get equipment from all floor plans
	plans, err := p.db.GetAllFloorPlans(ctx)
	if err != nil {
		return 0, fmt.Errorf("failed to get floor plans: %w", err)
	}
	
	var equipment []*models.Equipment
	for _, plan := range plans {
		planEquipment, err := p.db.GetEquipmentByFloorPlan(ctx, plan.Name)
		if err != nil {
			continue // Skip if we can't get equipment for this plan
		}
		equipment = append(equipment, planEquipment...)
	}
	
	scheduledCount := 0
	currentTime := time.Now()
	
	// Count equipment that needs maintenance within next 30 days
	for _, eq := range equipment {
		health, err := p.AnalyzeEquipmentHealth(ctx, eq.ID)
		if err != nil {
			continue
		}
		
		// Equipment with low health scores or high failure probability needs maintenance
		if health.OverallScore < 60 || health.FailureProbability > 0.3 {
			scheduledCount++
		}
		
		// Also count equipment that hasn't been maintained in a long time
		if eq.MarkedAt != nil {
			daysSinceCreation := currentTime.Sub(*eq.MarkedAt).Hours() / 24
			if daysSinceCreation > 90 { // 90 days without maintenance
				scheduledCount++
			}
		}
	}
	
	return scheduledCount, nil
}

// GetOverdueMaintenanceCount returns the number of overdue maintenance tasks
func (p *Predictor) GetOverdueMaintenanceCount(ctx context.Context) (int, error) {
	// Query database for overdue maintenance tasks
	// Get equipment from all floor plans
	plans, err := p.db.GetAllFloorPlans(ctx)
	if err != nil {
		return 0, fmt.Errorf("failed to get floor plans: %w", err)
	}
	
	var equipment []*models.Equipment
	for _, plan := range plans {
		planEquipment, err := p.db.GetEquipmentByFloorPlan(ctx, plan.Name)
		if err != nil {
			continue // Skip if we can't get equipment for this plan
		}
		equipment = append(equipment, planEquipment...)
	}
	
	overdueCount := 0
	currentTime := time.Now()
	
	for _, eq := range equipment {
		health, err := p.AnalyzeEquipmentHealth(ctx, eq.ID)
		if err != nil {
			continue
		}
		
		// Equipment with critical health scores is overdue for maintenance
		if health.OverallScore < 30 || health.FailureProbability > 0.7 {
			overdueCount++
		}
		
		// Also count equipment that hasn't been maintained in a very long time
		if eq.MarkedAt != nil {
			daysSinceCreation := currentTime.Sub(*eq.MarkedAt).Hours() / 24
			if daysSinceCreation > 180 { // 180 days is definitely overdue
				overdueCount++
			}
		}
	}
	
	return overdueCount, nil
}