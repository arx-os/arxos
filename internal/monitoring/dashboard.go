// Package monitoring implements real-time building system monitoring
package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/ascii/abim"
	"github.com/joelpate/arxos/internal/ascii/layers"
	"github.com/joelpate/arxos/internal/connections"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/energy"
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/maintenance"
	"github.com/joelpate/arxos/pkg/models"
)

// Dashboard provides real-time monitoring of building systems
type Dashboard struct {
	db            database.DB
	connManager   *connections.Manager
	predictor     *maintenance.Predictor
	energySystems map[string]*energy.FlowSystem
	renderer      *abim.Renderer
	metrics       *SystemMetrics
	alerts        *AlertManager
	mu            sync.RWMutex
	updateTicker  *time.Ticker
	stopCh        chan struct{}
	running       bool
}

// SystemMetrics holds comprehensive system performance data
type SystemMetrics struct {
	Timestamp           time.Time                    `json:"timestamp"`
	SystemHealth        OverallHealth                `json:"system_health"`
	EnergyMetrics       map[string]EnergyMetrics     `json:"energy_metrics"`
	ConnectionMetrics   ConnectionMetrics            `json:"connection_metrics"`
	EquipmentMetrics    map[string]EquipmentMetrics  `json:"equipment_metrics"`
	MaintenanceMetrics  MaintenanceMetrics           `json:"maintenance_metrics"`
	PerformanceMetrics  PerformanceMetrics           `json:"performance_metrics"`
	ActiveAlerts        []Alert                      `json:"active_alerts"`
	TrendData          map[string][]TrendPoint      `json:"trend_data"`
}

// OverallHealth represents the aggregate system health
type OverallHealth struct {
	Status       HealthStatus `json:"status"`
	Score        float64      `json:"score"`         // 0-100
	Uptime       time.Duration `json:"uptime"`
	LastIssue    *time.Time   `json:"last_issue,omitempty"`
	CriticalSystems int       `json:"critical_systems"`
	HealthySystems  int       `json:"healthy_systems"`
}

// EnergyMetrics tracks energy system performance
type EnergyMetrics struct {
	FlowType     string    `json:"flow_type"`
	TotalFlow    float64   `json:"total_flow"`
	Efficiency   float64   `json:"efficiency"`
	TotalLoss    float64   `json:"total_loss"`
	PeakDemand   float64   `json:"peak_demand"`
	LoadFactor   float64   `json:"load_factor"`
	LastUpdated  time.Time `json:"last_updated"`
}

// ConnectionMetrics tracks connection system health
type ConnectionMetrics struct {
	TotalConnections    int       `json:"total_connections"`
	ActiveConnections   int       `json:"active_connections"`
	FailedConnections   int       `json:"failed_connections"`
	AverageLatency      float64   `json:"average_latency_ms"`
	ThroughputMbps     float64   `json:"throughput_mbps"`
	ErrorRate          float64   `json:"error_rate"`
	LastUpdated        time.Time `json:"last_updated"`
}

// EquipmentMetrics tracks individual equipment performance
type EquipmentMetrics struct {
	EquipmentID      string                 `json:"equipment_id"`
	HealthScore      float64               `json:"health_score"`
	Status           models.EquipmentStatus `json:"status"`
	FailureProbability float64             `json:"failure_probability"`
	MaintenanceDue   *time.Time            `json:"maintenance_due,omitempty"`
	LastMaintenance  *time.Time            `json:"last_maintenance,omitempty"`
	OperatingHours   float64               `json:"operating_hours"`
	EfficiencyRating float64               `json:"efficiency_rating"`
}

// MaintenanceMetrics tracks maintenance system performance
type MaintenanceMetrics struct {
	ScheduledTasks     int       `json:"scheduled_tasks"`
	OverdueTasks       int       `json:"overdue_tasks"`
	CompletedThisWeek  int       `json:"completed_this_week"`
	AverageRepairTime  float64   `json:"average_repair_time_hours"`
	PreventiveRatio    float64   `json:"preventive_ratio"`
	CostSavings        float64   `json:"cost_savings"`
	LastUpdated        time.Time `json:"last_updated"`
}

// PerformanceMetrics tracks system performance
type PerformanceMetrics struct {
	RenderTimeMs       float64   `json:"render_time_ms"`
	FrameRate          float64   `json:"frame_rate"`
	MemoryUsageMB      float64   `json:"memory_usage_mb"`
	CPUUsagePercent    float64   `json:"cpu_usage_percent"`
	ActiveLayers       int       `json:"active_layers"`
	DatabaseQueries    int       `json:"database_queries"`
	LastUpdated        time.Time `json:"last_updated"`
}

// TrendPoint represents a single data point in trend analysis
type TrendPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
}

// HealthStatus represents overall system health
type HealthStatus string

const (
	HealthExcellent HealthStatus = "excellent"
	HealthGood      HealthStatus = "good"
	HealthFair      HealthStatus = "fair"
	HealthPoor      HealthStatus = "poor"
	HealthCritical  HealthStatus = "critical"
)

// NewDashboard creates a new monitoring dashboard
func NewDashboard(db database.DB, plan *models.FloorPlan, width, height int) *Dashboard {
	connManager := connections.NewManager(db)
	predictor := maintenance.NewPredictor(db, connManager)
	renderer := abim.NewRenderer(width, height)
	
	// Initialize energy systems for different flow types
	energySystems := map[string]*energy.FlowSystem{
		"electrical": energy.NewFlowSystem(energy.FlowElectrical, connManager),
		"thermal":    energy.NewFlowSystem(energy.FlowThermal, connManager),
		"fluid":      energy.NewFlowSystem(energy.FlowFluid, connManager),
	}
	
	// Add all ABIM layers
	renderer.AddLayer("structure", layers.NewStructureLayer(plan))
	renderer.AddLayer("equipment", layers.NewEquipmentLayer(plan.Equipment))
	renderer.AddLayer("connections", layers.NewConnectionLayer(connManager))
	renderer.AddLayer("energy", layers.NewEnergyLayer(energySystems["electrical"]))
	
	failureLayer := layers.NewFailureLayer(connManager, predictor)
	renderer.AddLayer("failure", failureLayer)
	
	dashboard := &Dashboard{
		db:            db,
		connManager:   connManager,
		predictor:     predictor,
		energySystems: energySystems,
		renderer:      renderer,
		metrics:       &SystemMetrics{},
		alerts:        NewAlertManager(),
		stopCh:        make(chan struct{}),
	}
	
	logger.Info("Dashboard initialized with %d energy systems", len(energySystems))
	return dashboard
}

// Start begins real-time monitoring
func (d *Dashboard) Start(ctx context.Context) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	if d.running {
		return fmt.Errorf("dashboard already running")
	}
	
	d.running = true
	d.updateTicker = time.NewTicker(5 * time.Second) // Update every 5 seconds
	
	go d.monitoringLoop(ctx)
	logger.Info("Dashboard monitoring started")
	return nil
}

// Stop halts monitoring
func (d *Dashboard) Stop() {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	if !d.running {
		return
	}
	
	d.running = false
	if d.updateTicker != nil {
		d.updateTicker.Stop()
	}
	close(d.stopCh)
	logger.Info("Dashboard monitoring stopped")
}

// GetMetrics returns current system metrics
func (d *Dashboard) GetMetrics() *SystemMetrics {
	d.mu.RLock()
	defer d.mu.RUnlock()
	
	// Return a copy to avoid race conditions
	metricsCopy := *d.metrics
	return &metricsCopy
}

// GetVisualization returns the current ABIM visualization
func (d *Dashboard) GetVisualization() [][]rune {
	return d.renderer.Render()
}

// GetAlerts returns current active alerts
func (d *Dashboard) GetAlerts() []Alert {
	return d.alerts.GetActiveAlerts()
}

// SetLayerVisible controls ABIM layer visibility
func (d *Dashboard) SetLayerVisible(layerName string, visible bool) error {
	return d.renderer.SetLayerVisible(layerName, visible)
}

// SimulateFailure injects a failure for testing
func (d *Dashboard) SimulateFailure(equipmentID string, position models.Point, 
	failureType layers.FailureType, severity layers.FailureSeverity) error {
	
	// Get failure layer and simulate
	layerNames := d.renderer.GetLayerNames()
	for _, name := range layerNames {
		if name == "failure" {
			// This is a simplified approach - in production we'd need layer access
			logger.Info("Simulating failure: %s at (%f,%f) - %s/%s", 
				equipmentID, position.X, position.Y, failureType, severity)
			
			// Create alert for the failure
			alert := Alert{
				ID:          fmt.Sprintf("failure_%s_%d", equipmentID, time.Now().Unix()),
				Type:        AlertFailure,
				Severity:    AlertSeverity(severity),
				Message:     fmt.Sprintf("Equipment %s failed (%s)", equipmentID, failureType),
				EquipmentID: &equipmentID,
				Timestamp:   time.Now(),
			}
			d.alerts.AddAlert(alert)
			return nil
		}
	}
	
	return fmt.Errorf("failure layer not found")
}

// monitoringLoop is the main monitoring routine
func (d *Dashboard) monitoringLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			logger.Info("Monitoring loop stopped by context")
			return
		case <-d.stopCh:
			logger.Info("Monitoring loop stopped by stop channel")
			return
		case <-d.updateTicker.C:
			d.updateMetrics(ctx)
		}
	}
}

// updateMetrics collects and updates all system metrics
func (d *Dashboard) updateMetrics(ctx context.Context) {
	start := time.Now()
	
	d.mu.Lock()
	defer d.mu.Unlock()
	
	// Update timestamp
	d.metrics.Timestamp = time.Now()
	
	// Update energy metrics
	d.updateEnergyMetrics(ctx)
	
	// Update connection metrics
	d.updateConnectionMetrics(ctx)
	
	// Update equipment metrics
	d.updateEquipmentMetrics(ctx)
	
	// Update maintenance metrics
	d.updateMaintenanceMetrics(ctx)
	
	// Update performance metrics
	d.updatePerformanceMetrics(start)
	
	// Update overall health
	d.updateOverallHealth()
	
	// Update visualization
	d.renderer.Update(5.0) // 5 second delta
	
	// Process alerts
	d.processAlerts(ctx)
	
	updateDuration := time.Since(start)
	logger.Debug("Metrics update completed in %v", updateDuration)
}

// updateEnergyMetrics collects energy system data
func (d *Dashboard) updateEnergyMetrics(ctx context.Context) {
	if d.metrics.EnergyMetrics == nil {
		d.metrics.EnergyMetrics = make(map[string]EnergyMetrics)
	}
	
	for flowType, system := range d.energySystems {
		result, err := system.Simulate()
		if err != nil {
			logger.Warn("Energy simulation failed for %s: %v", flowType, err)
			continue
		}
		
		d.metrics.EnergyMetrics[flowType] = EnergyMetrics{
			FlowType:    flowType,
			TotalFlow:   result.TotalFlow,
			Efficiency:  result.Efficiency,
			TotalLoss:   result.TotalLoss,
			PeakDemand:  result.TotalFlow * 1.2, // Mock peak demand
			LoadFactor:  0.75,                   // Mock load factor
			LastUpdated: time.Now(),
		}
	}
}

// updateConnectionMetrics collects connection system data
func (d *Dashboard) updateConnectionMetrics(ctx context.Context) {
	// Get connection statistics from manager
	stats := d.connManager.GetStatistics()
	
	d.metrics.ConnectionMetrics = ConnectionMetrics{
		TotalConnections:  stats.TotalConnections,
		ActiveConnections: stats.ActiveConnections,
		FailedConnections: stats.FailedConnections,
		AverageLatency:    stats.AverageLatency,
		ThroughputMbps:   stats.ThroughputMbps,
		ErrorRate:        stats.ErrorRate,
		LastUpdated:      time.Now(),
	}
}

// updateEquipmentMetrics collects equipment health data
func (d *Dashboard) updateEquipmentMetrics(ctx context.Context) {
	if d.metrics.EquipmentMetrics == nil {
		d.metrics.EquipmentMetrics = make(map[string]EquipmentMetrics)
	}
	
	// Get all equipment from all floor plans
	plans, err := d.db.GetAllFloorPlans(ctx)
	if err != nil {
		logger.Warn("Failed to get floor plans for metrics: %v", err)
		return
	}
	
	var equipment []*models.Equipment
	for _, plan := range plans {
		planEquipment, err := d.db.GetEquipmentByFloorPlan(ctx, plan.Name)
		if err != nil {
			continue // Skip if we can't get equipment for this plan
		}
		equipment = append(equipment, planEquipment...)
	}
	
	for _, eq := range equipment {
		health, err := d.predictor.AnalyzeEquipmentHealth(ctx, eq.ID)
		if err != nil {
			logger.Debug("Failed to analyze health for %s: %v", eq.ID, err)
			continue
		}
		
		d.metrics.EquipmentMetrics[eq.ID] = EquipmentMetrics{
			EquipmentID:        eq.ID,
			HealthScore:        health.OverallScore,
			Status:             eq.Status,
			FailureProbability: health.FailureProbability,
			OperatingHours:     calculateOperatingHours(eq),
			EfficiencyRating:   calculateEfficiency(eq, health),
		}
	}
}

// updateMaintenanceMetrics collects maintenance system data
func (d *Dashboard) updateMaintenanceMetrics(ctx context.Context) {
	// Get maintenance statistics
	scheduled, err := d.predictor.GetScheduledMaintenanceCount(ctx)
	if err != nil {
		logger.Warn("Failed to get scheduled maintenance count: %v", err)
		scheduled = 0
	}
	
	overdue, err := d.predictor.GetOverdueMaintenanceCount(ctx)
	if err != nil {
		logger.Warn("Failed to get overdue maintenance count: %v", err)
		overdue = 0
	}
	
	d.metrics.MaintenanceMetrics = MaintenanceMetrics{
		ScheduledTasks:    scheduled,
		OverdueTasks:      overdue,
		CompletedThisWeek: 0, // Would be calculated from maintenance history
		AverageRepairTime: 4.5, // Hours - would be calculated from historical data
		PreventiveRatio:   0.75, // Percentage of preventive vs reactive maintenance
		CostSavings:       15000.0, // Dollar savings from predictive maintenance
		LastUpdated:       time.Now(),
	}
}

// updatePerformanceMetrics collects system performance data
func (d *Dashboard) updatePerformanceMetrics(start time.Time) {
	renderStart := time.Now()
	_ = d.renderer.Render() // Render to measure performance
	renderTime := time.Since(renderStart)
	
	d.metrics.PerformanceMetrics = PerformanceMetrics{
		RenderTimeMs:    float64(renderTime.Nanoseconds()) / 1e6,
		FrameRate:       1000.0 / (float64(renderTime.Nanoseconds()) / 1e6),
		MemoryUsageMB:   getCurrentMemoryUsage(),
		CPUUsagePercent: getCurrentCPUUsage(),
		ActiveLayers:    len(d.renderer.GetLayerNames()),
		DatabaseQueries: 0, // Would be tracked by database layer
		LastUpdated:     time.Now(),
	}
}

// updateOverallHealth calculates aggregate system health
func (d *Dashboard) updateOverallHealth() {
	totalScore := 0.0
	systemCount := 0
	criticalSystems := 0
	healthySystems := 0
	
	// Aggregate equipment health
	for _, eq := range d.metrics.EquipmentMetrics {
		totalScore += eq.HealthScore
		systemCount++
		
		if eq.HealthScore < 30 {
			criticalSystems++
		} else if eq.HealthScore > 80 {
			healthySystems++
		}
	}
	
	// Factor in energy efficiency
	for _, energy := range d.metrics.EnergyMetrics {
		totalScore += energy.Efficiency
		systemCount++
		
		if energy.Efficiency < 30 {
			criticalSystems++
		} else if energy.Efficiency > 80 {
			healthySystems++
		}
	}
	
	averageScore := 75.0 // Default if no systems
	if systemCount > 0 {
		averageScore = totalScore / float64(systemCount)
	}
	
	// Determine status
	var status HealthStatus
	switch {
	case averageScore >= 90:
		status = HealthExcellent
	case averageScore >= 75:
		status = HealthGood
	case averageScore >= 60:
		status = HealthFair
	case averageScore >= 40:
		status = HealthPoor
	default:
		status = HealthCritical
	}
	
	d.metrics.SystemHealth = OverallHealth{
		Status:          status,
		Score:           averageScore,
		Uptime:          time.Since(time.Now().Add(-24 * time.Hour)), // Mock uptime
		CriticalSystems: criticalSystems,
		HealthySystems:  healthySystems,
	}
}

// processAlerts handles alert generation and management
func (d *Dashboard) processAlerts(ctx context.Context) {
	// Check for critical equipment
	for equipmentID, metrics := range d.metrics.EquipmentMetrics {
		if metrics.HealthScore < 20 {
			alert := Alert{
				ID:          fmt.Sprintf("critical_equipment_%s", equipmentID),
				Type:        AlertEquipmentCritical,
				Severity:    AlertCritical,
				Message:     fmt.Sprintf("Equipment %s health critical (%.1f%%)", equipmentID, metrics.HealthScore),
				EquipmentID: &equipmentID,
				Timestamp:   time.Now(),
			}
			d.alerts.AddAlert(alert)
		}
	}
	
	// Check for low energy efficiency
	for flowType, metrics := range d.metrics.EnergyMetrics {
		if metrics.Efficiency < 50 {
			alert := Alert{
				ID:        fmt.Sprintf("low_efficiency_%s", flowType),
				Type:      AlertEnergyEfficiency,
				Severity:  AlertWarning,
				Message:   fmt.Sprintf("%s system efficiency low (%.1f%%)", flowType, metrics.Efficiency),
				Timestamp: time.Now(),
			}
			d.alerts.AddAlert(alert)
		}
	}
	
	// Auto-resolve old alerts
	d.alerts.CleanupExpiredAlerts(24 * time.Hour)
}

// Helper functions

func calculateOperatingHours(eq *models.Equipment) float64 {
	// Mock calculation - would use actual runtime data
	return float64(time.Since(eq.MarkedAt).Hours())
}

func calculateEfficiency(eq *models.Equipment, health *maintenance.EquipmentHealth) float64 {
	// Mock efficiency calculation based on health score
	return health.OverallScore * 0.9 // Efficiency typically correlates with health
}

func getCurrentMemoryUsage() float64 {
	// Mock memory usage - would use runtime.ReadMemStats in production
	return 128.5 // MB
}

func getCurrentCPUUsage() float64 {
	// Mock CPU usage - would use system monitoring in production
	return 15.2 // Percent
}