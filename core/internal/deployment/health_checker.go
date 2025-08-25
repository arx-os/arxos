package deployment

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/pkg/errors"
)

// DefaultHealthChecker implements the HealthChecker interface
type DefaultHealthChecker struct {
	db        *sqlx.DB
	checks    map[string]HealthCheckFunc
	thresholds HealthCheckThresholds
}

// HealthCheckFunc is a function that performs a health check
type HealthCheckFunc func(ctx context.Context, buildingID string) (*CheckResult, error)

// NewDefaultHealthChecker creates a new default health checker
func NewDefaultHealthChecker(db *sqlx.DB) *DefaultHealthChecker {
	hc := &DefaultHealthChecker{
		db:     db,
		checks: make(map[string]HealthCheckFunc),
		thresholds: HealthCheckThresholds{
			MinScore:        80.0,
			MaxResponseTime: 5000,
			MaxErrorRate:    0.05,
		},
	}

	// Register default health checks
	hc.RegisterCheck("system_status", hc.checkSystemStatus)
	hc.RegisterCheck("arxobject_integrity", hc.checkArxObjectIntegrity)
	hc.RegisterCheck("performance_metrics", hc.checkPerformanceMetrics)
	hc.RegisterCheck("compliance_status", hc.checkComplianceStatus)
	hc.RegisterCheck("connectivity", hc.checkConnectivity)

	return hc
}

// RegisterCheck registers a new health check function
func (hc *DefaultHealthChecker) RegisterCheck(name string, checkFunc HealthCheckFunc) {
	hc.checks[name] = checkFunc
}

// CheckPreDeployment performs pre-deployment health checks
func (hc *DefaultHealthChecker) CheckPreDeployment(ctx context.Context, buildingID string) (*HealthCheckResult, error) {
	result := &HealthCheckResult{
		Passed:  true,
		Score:   100.0,
		Checks:  make(map[string]CheckResult),
		Issues:  []string{},
		Metrics: make(map[string]float64),
	}

	// Run pre-deployment specific checks
	preChecks := []string{
		"system_status",
		"connectivity",
		"arxobject_integrity",
	}

	for _, checkName := range preChecks {
		if checkFunc, exists := hc.checks[checkName]; exists {
			checkResult, err := checkFunc(ctx, buildingID)
			if err != nil {
				checkResult = &CheckResult{
					Name:    checkName,
					Passed:  false,
					Score:   0,
					Details: fmt.Sprintf("Check failed: %v", err),
				}
			}

			result.Checks[checkName] = *checkResult

			// Update overall result
			if !checkResult.Passed {
				result.Passed = false
				result.Issues = append(result.Issues, fmt.Sprintf("%s: %s", checkName, checkResult.Details))
			}

			// Update overall score (weighted average)
			result.Score = (result.Score + checkResult.Score) / 2
		}
	}

	// Check if score meets minimum threshold
	if result.Score < hc.thresholds.MinScore {
		result.Passed = false
		result.Issues = append(result.Issues, fmt.Sprintf("Overall score %.2f below threshold %.2f", 
			result.Score, hc.thresholds.MinScore))
	}

	// Record health check in database
	hc.recordHealthCheck(ctx, buildingID, "pre_deployment", result)

	return result, nil
}

// CheckPostDeployment performs post-deployment health checks
func (hc *DefaultHealthChecker) CheckPostDeployment(ctx context.Context, buildingID string) (*HealthCheckResult, error) {
	result := &HealthCheckResult{
		Passed:  true,
		Score:   100.0,
		Checks:  make(map[string]CheckResult),
		Issues:  []string{},
		Metrics: make(map[string]float64),
	}

	// Run all health checks
	for checkName, checkFunc := range hc.checks {
		checkResult, err := checkFunc(ctx, buildingID)
		if err != nil {
			checkResult = &CheckResult{
				Name:    checkName,
				Passed:  false,
				Score:   0,
				Details: fmt.Sprintf("Check failed: %v", err),
			}
		}

		result.Checks[checkName] = *checkResult

		// Update overall result
		if !checkResult.Passed {
			result.Passed = false
			result.Issues = append(result.Issues, fmt.Sprintf("%s: %s", checkName, checkResult.Details))
		}

		// Update overall score
		result.Score = math.Min(result.Score, checkResult.Score)
	}

	// Additional post-deployment specific checks
	if responseTime, exists := result.Metrics["response_time_ms"]; exists {
		if responseTime > float64(hc.thresholds.MaxResponseTime) {
			result.Passed = false
			result.Issues = append(result.Issues, fmt.Sprintf("Response time %.0fms exceeds threshold %dms",
				responseTime, hc.thresholds.MaxResponseTime))
		}
	}

	if errorRate, exists := result.Metrics["error_rate"]; exists {
		if errorRate > hc.thresholds.MaxErrorRate {
			result.Passed = false
			result.Issues = append(result.Issues, fmt.Sprintf("Error rate %.2f%% exceeds threshold %.2f%%",
				errorRate*100, hc.thresholds.MaxErrorRate*100))
		}
	}

	// Record health check
	hc.recordHealthCheck(ctx, buildingID, "post_deployment", result)

	return result, nil
}

// ValidateDeployment validates a deployment against building requirements
func (hc *DefaultHealthChecker) ValidateDeployment(ctx context.Context, buildingID string, stateID string) (*ValidationResult, error) {
	result := &ValidationResult{
		Valid:    true,
		Errors:   []string{},
		Warnings: []string{},
		Details:  make(map[string]interface{}),
	}

	// Check if state exists
	var stateExists bool
	err := hc.db.GetContext(ctx, &stateExists, `
		SELECT EXISTS(SELECT 1 FROM building_states WHERE id = $1 AND building_id = $2)
	`, stateID, buildingID)
	if err != nil || !stateExists {
		result.Valid = false
		result.Errors = append(result.Errors, "State does not exist or does not belong to building")
		return result, nil
	}

	// Validate ArxObject integrity
	arxObjectCount := 0
	err = hc.db.GetContext(ctx, &arxObjectCount, `
		SELECT arxobject_count FROM building_states WHERE id = $1
	`, stateID)
	if err != nil {
		result.Warnings = append(result.Warnings, "Could not verify ArxObject count")
	} else {
		result.Details["arxobject_count"] = arxObjectCount
		if arxObjectCount == 0 {
			result.Warnings = append(result.Warnings, "State contains no ArxObjects")
		}
	}

	// Check for required systems
	var systemsState json.RawMessage
	err = hc.db.GetContext(ctx, &systemsState, `
		SELECT systems_state FROM building_states WHERE id = $1
	`, stateID)
	if err == nil && systemsState != nil {
		var systems map[string]interface{}
		if err := json.Unmarshal(systemsState, &systems); err == nil {
			requiredSystems := []string{"hvac", "electrical", "fire", "security"}
			for _, sys := range requiredSystems {
				if _, exists := systems[sys]; !exists {
					result.Warnings = append(result.Warnings, fmt.Sprintf("Required system '%s' not configured", sys))
				}
			}
		}
	}

	// Check compliance requirements
	var complianceStatus json.RawMessage
	err = hc.db.GetContext(ctx, &complianceStatus, `
		SELECT compliance_status FROM building_states WHERE id = $1
	`, stateID)
	if err == nil && complianceStatus != nil {
		var compliance map[string]interface{}
		if err := json.Unmarshal(complianceStatus, &compliance); err == nil {
			for regulation, status := range compliance {
				if statusStr, ok := status.(string); ok && statusStr != "compliant" {
					result.Warnings = append(result.Warnings, 
						fmt.Sprintf("Compliance issue: %s is %s", regulation, statusStr))
				}
			}
		}
	}

	// Final validation
	if len(result.Errors) > 0 {
		result.Valid = false
	}

	return result, nil
}

// Individual health check implementations

func (hc *DefaultHealthChecker) checkSystemStatus(ctx context.Context, buildingID string) (*CheckResult, error) {
	result := &CheckResult{
		Name:   "system_status",
		Passed: true,
		Score:  100.0,
	}

	// Check if building exists and is active
	var status string
	err := hc.db.GetContext(ctx, &status, `
		SELECT COALESCE(metadata->>'status', 'active') 
		FROM pdf_buildings WHERE id = $1
	`, buildingID)
	
	if err != nil {
		result.Passed = false
		result.Score = 0
		result.Details = fmt.Sprintf("Failed to check building status: %v", err)
		return result, nil
	}

	if status != "active" {
		result.Score = 50.0
		result.Details = fmt.Sprintf("Building status is %s", status)
		if status == "maintenance" || status == "offline" {
			result.Passed = false
		}
	}

	return result, nil
}

func (hc *DefaultHealthChecker) checkArxObjectIntegrity(ctx context.Context, buildingID string) (*CheckResult, error) {
	result := &CheckResult{
		Name:   "arxobject_integrity",
		Passed: true,
		Score:  100.0,
	}

	// Check for ArxObject anomalies
	var stats struct {
		Total      int     `db:"total"`
		Invalid    int     `db:"invalid"`
		Duplicates int     `db:"duplicates"`
	}

	err := hc.db.GetContext(ctx, &stats, `
		WITH object_stats AS (
			SELECT 
				COUNT(*) as total,
				COUNT(*) FILTER (WHERE x_nano = 0 AND y_nano = 0 AND z_nano = 0) as invalid,
				COUNT(*) - COUNT(DISTINCT id) as duplicates
			FROM arx_objects
			WHERE building_id = $1
		)
		SELECT * FROM object_stats
	`, buildingID)

	if err != nil {
		result.Passed = false
		result.Score = 0
		result.Details = fmt.Sprintf("Failed to check ArxObject integrity: %v", err)
		return result, nil
	}

	// Calculate score based on integrity issues
	if stats.Total == 0 {
		result.Score = 50.0
		result.Details = "No ArxObjects found"
	} else {
		invalidRate := float64(stats.Invalid) / float64(stats.Total)
		duplicateRate := float64(stats.Duplicates) / float64(stats.Total)
		
		result.Score = 100.0 * (1.0 - invalidRate - duplicateRate)
		
		if invalidRate > 0.01 || duplicateRate > 0 {
			result.Passed = false
			result.Details = fmt.Sprintf("Found %d invalid and %d duplicate objects out of %d total",
				stats.Invalid, stats.Duplicates, stats.Total)
		}
	}

	return result, nil
}

func (hc *DefaultHealthChecker) checkPerformanceMetrics(ctx context.Context, buildingID string) (*CheckResult, error) {
	result := &CheckResult{
		Name:   "performance_metrics",
		Passed: true,
		Score:  100.0,
	}

	// Simulate performance check
	// In production, would query actual metrics
	responseTime := 100 + (uuid.New().ID() % 200) // Random 100-300ms
	errorRate := float64(uuid.New().ID()%10) / 1000.0 // 0-0.01
	
	// Score based on response time
	if responseTime < 200 {
		result.Score = 100.0
	} else if responseTime < 500 {
		result.Score = 80.0
	} else if responseTime < 1000 {
		result.Score = 60.0
	} else {
		result.Score = 40.0
		result.Passed = false
	}

	// Adjust for error rate
	if errorRate > 0.01 {
		result.Score *= 0.8
		result.Passed = false
		result.Details = fmt.Sprintf("High error rate: %.2f%%", errorRate*100)
	}

	return result, nil
}

func (hc *DefaultHealthChecker) checkComplianceStatus(ctx context.Context, buildingID string) (*CheckResult, error) {
	result := &CheckResult{
		Name:   "compliance_status",
		Passed: true,
		Score:  100.0,
	}

	// Check latest compliance status from building states
	var complianceJSON json.RawMessage
	err := hc.db.GetContext(ctx, &complianceJSON, `
		SELECT compliance_status 
		FROM building_states 
		WHERE building_id = $1 
		ORDER BY created_at DESC 
		LIMIT 1
	`, buildingID)

	if err != nil || complianceJSON == nil {
		result.Score = 75.0 // Unknown compliance is not a failure but reduces score
		result.Details = "No compliance data available"
		return result, nil
	}

	var compliance map[string]string
	if err := json.Unmarshal(complianceJSON, &compliance); err != nil {
		result.Score = 75.0
		result.Details = "Could not parse compliance data"
		return result, nil
	}

	// Check compliance status
	nonCompliant := []string{}
	for regulation, status := range compliance {
		if status != "compliant" {
			nonCompliant = append(nonCompliant, regulation)
		}
	}

	if len(nonCompliant) > 0 {
		result.Score = 100.0 - (float64(len(nonCompliant)) * 20.0)
		result.Score = math.Max(result.Score, 0)
		
		if result.Score < 60 {
			result.Passed = false
		}
		
		result.Details = fmt.Sprintf("Non-compliant with: %v", nonCompliant)
	}

	return result, nil
}

func (hc *DefaultHealthChecker) checkConnectivity(ctx context.Context, buildingID string) (*CheckResult, error) {
	result := &CheckResult{
		Name:   "connectivity",
		Passed: true,
		Score:  100.0,
	}

	// Check last sync time (if applicable)
	var lastSync time.Time
	err := hc.db.GetContext(ctx, &lastSync, `
		SELECT COALESCE(MAX(created_at), NOW()) 
		FROM building_states 
		WHERE building_id = $1
	`, buildingID)

	if err != nil {
		result.Score = 90.0
		result.Details = "Could not verify connectivity"
		return result, nil
	}

	timeSinceSync := time.Since(lastSync)
	if timeSinceSync > 24*time.Hour {
		result.Score = 50.0
		result.Passed = false
		result.Details = fmt.Sprintf("No updates for %.0f hours", timeSinceSync.Hours())
	} else if timeSinceSync > 1*time.Hour {
		result.Score = 80.0
		result.Details = fmt.Sprintf("Last update %.0f minutes ago", timeSinceSync.Minutes())
	}

	return result, nil
}

// Helper methods

func (hc *DefaultHealthChecker) recordHealthCheck(ctx context.Context, buildingID, checkType string, result *HealthCheckResult) {
	// Record health check in database
	resultJSON, _ := json.Marshal(result)
	
	_, err := hc.db.ExecContext(ctx, `
		INSERT INTO deployment_health_checks (
			id, check_name, check_type, check_config, executed_at,
			status, score, metrics, issues
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9
		)
	`, uuid.New().String(), checkType, "system", resultJSON, time.Now(),
		map[bool]string{true: "passed", false: "failed"}[result.Passed],
		result.Score, result.Metrics, result.Issues)
	
	if err != nil {
		// Log error but don't fail the health check
		fmt.Printf("Failed to record health check: %v\n", err)
	}
}

// ContinuousMonitor performs continuous health monitoring during deployment
type ContinuousMonitor struct {
	checker   *DefaultHealthChecker
	interval  time.Duration
	threshold float64
	stopChan  chan bool
	results   chan *HealthCheckResult
}

// NewContinuousMonitor creates a new continuous health monitor
func NewContinuousMonitor(checker *DefaultHealthChecker, interval time.Duration) *ContinuousMonitor {
	return &ContinuousMonitor{
		checker:   checker,
		interval:  interval,
		threshold: 80.0,
		stopChan:  make(chan bool),
		results:   make(chan *HealthCheckResult, 100),
	}
}

// Start begins continuous monitoring
func (cm *ContinuousMonitor) Start(ctx context.Context, buildingID string) {
	go func() {
		ticker := time.NewTicker(cm.interval)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-cm.stopChan:
				return
			case <-ticker.C:
				result, err := cm.checker.CheckPostDeployment(ctx, buildingID)
				if err != nil {
					fmt.Printf("Continuous health check error: %v\n", err)
					continue
				}
				
				// Send result
				select {
				case cm.results <- result:
				default:
					// Channel full, skip
				}
				
				// Check if health is critically low
				if result.Score < cm.threshold {
					fmt.Printf("WARNING: Building %s health score %.2f below threshold %.2f\n",
						buildingID, result.Score, cm.threshold)
				}
			}
		}
	}()
}

// Stop stops continuous monitoring
func (cm *ContinuousMonitor) Stop() {
	close(cm.stopChan)
}

// GetResults returns the results channel
func (cm *ContinuousMonitor) GetResults() <-chan *HealthCheckResult {
	return cm.results
}