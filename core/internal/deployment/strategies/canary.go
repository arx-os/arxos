package strategies

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/arxos/core/internal/deployment"
)

// CanaryStrategy implements canary deployment (small percentage first)
type CanaryStrategy struct {
	config *deployment.CanaryStrategyConfig
	canaryTargets []*deployment.DeploymentTarget
	remainingTargets []*deployment.DeploymentTarget
	validationStartTime time.Time
}

// NewCanaryStrategy creates a new canary deployment strategy
func NewCanaryStrategy() *CanaryStrategy {
	return &CanaryStrategy{
		config: &deployment.CanaryStrategyConfig{
			CanaryPercentage:        10,
			ValidationPeriodMinutes: 60,
			AutoPromote:            false,
			SuccessThreshold:       0.95,
			MetricsToMonitor:       []string{"health_score", "error_rate", "response_time"},
		},
	}
}

// Name returns the strategy name
func (s *CanaryStrategy) Name() string {
	return "canary"
}

// Validate validates the deployment for this strategy
func (s *CanaryStrategy) Validate(d *deployment.Deployment) error {
	// Parse strategy config if provided
	if d.StrategyConfig != nil {
		var config deployment.CanaryStrategyConfig
		if err := json.Unmarshal(d.StrategyConfig, &config); err != nil {
			return fmt.Errorf("invalid strategy config: %w", err)
		}
		s.config = &config
	}

	// Validate config
	if s.config.CanaryPercentage <= 0 || s.config.CanaryPercentage > 50 {
		return fmt.Errorf("canary percentage must be between 1 and 50")
	}

	if s.config.ValidationPeriodMinutes <= 0 {
		s.config.ValidationPeriodMinutes = 60
	}

	if s.config.SuccessThreshold <= 0 || s.config.SuccessThreshold > 1 {
		s.config.SuccessThreshold = 0.95
	}

	// Check minimum target count
	if d.TargetCount < 2 {
		return fmt.Errorf("canary deployment requires at least 2 targets")
	}

	return nil
}

// Plan creates deployment waves for canary strategy
func (s *CanaryStrategy) Plan(d *deployment.Deployment, targets []*deployment.DeploymentTarget) ([]*deployment.DeploymentWave, error) {
	if len(targets) < 2 {
		return nil, fmt.Errorf("canary deployment requires at least 2 targets")
	}

	// Calculate canary size
	canarySize := int(math.Ceil(float64(len(targets)) * float64(s.config.CanaryPercentage) / 100))
	if canarySize == 0 {
		canarySize = 1
	}

	// Split targets into canary and remaining
	s.canaryTargets = targets[:canarySize]
	s.remainingTargets = targets[canarySize:]

	// Set deployment wave for targets
	for i, target := range s.canaryTargets {
		target.DeploymentWave = 0
		target.DeploymentOrder = i
	}

	for i, target := range s.remainingTargets {
		target.DeploymentWave = 1
		target.DeploymentOrder = i
	}

	// Create waves
	waves := []*deployment.DeploymentWave{
		{
			WaveNumber: 0,
			Targets:    s.canaryTargets,
			Config: map[string]interface{}{
				"type":                    "canary",
				"validation_period_minutes": s.config.ValidationPeriodMinutes,
				"auto_promote":            s.config.AutoPromote,
				"success_threshold":       s.config.SuccessThreshold,
			},
		},
		{
			WaveNumber: 1,
			Targets:    s.remainingTargets,
			Config: map[string]interface{}{
				"type":     "production",
				"parallel": true,
			},
		},
	}

	return waves, nil
}

// Execute executes a deployment wave
func (s *CanaryStrategy) Execute(ctx context.Context, wave *deployment.DeploymentWave) error {
	waveType, _ := wave.Config["type"].(string)

	switch waveType {
	case "canary":
		// Start validation period after canary deployment
		s.validationStartTime = time.Now()
		
		// If not auto-promote, wait for manual approval
		if !s.config.AutoPromote {
			return s.waitForApproval(ctx, wave)
		}
		
		// If auto-promote, validate canary health
		return s.validateCanary(ctx, wave)

	case "production":
		// Production deployment proceeds normally
		return nil

	default:
		return fmt.Errorf("unknown wave type: %s", waveType)
	}
}

// OnFailure handles deployment failure for a target
func (s *CanaryStrategy) OnFailure(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget, err error) error {
	// Check if this is a canary target
	isCanary := false
	for _, ct := range s.canaryTargets {
		if ct.ID == target.ID {
			isCanary = true
			break
		}
	}

	if isCanary {
		// Canary failed - abort entire deployment
		return fmt.Errorf("canary deployment failed, aborting: %w", err)
	}

	// Production target failed - check failure rate
	failureRate := float64(d.FailedCount) / float64(len(s.remainingTargets))
	maxFailureRate := 1.0 - s.config.SuccessThreshold

	if failureRate > maxFailureRate {
		// Too many failures - abort deployment
		return fmt.Errorf("failure rate %.2f%% exceeds threshold, aborting deployment", failureRate*100)
	}

	// Continue with other targets
	return nil
}

// OnSuccess handles successful deployment for a target
func (s *CanaryStrategy) OnSuccess(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget) error {
	// Check if all canary targets are complete
	canaryComplete := true
	canarySuccessful := 0
	
	for _, ct := range s.canaryTargets {
		if ct.Status == "completed" {
			canarySuccessful++
		} else if ct.Status != "failed" {
			canaryComplete = false
		}
	}

	if canaryComplete && target.DeploymentWave == 0 {
		// All canary targets complete - check success rate
		successRate := float64(canarySuccessful) / float64(len(s.canaryTargets))
		
		if successRate < s.config.SuccessThreshold {
			return fmt.Errorf("canary success rate %.2f%% below threshold %.2f%%", 
				successRate*100, s.config.SuccessThreshold*100)
		}

		// Log canary success
		fmt.Printf("Canary deployment successful (%.2f%% success rate)\n", successRate*100)
	}

	return nil
}

// Helper methods

func (s *CanaryStrategy) waitForApproval(ctx context.Context, wave *deployment.DeploymentWave) error {
	// In a real implementation, this would:
	// 1. Send notifications to approvers
	// 2. Wait for approval via API/CLI
	// 3. Monitor canary metrics during waiting period
	// 4. Timeout after validation period

	fmt.Printf("Canary deployment complete. Waiting for manual approval...\n")
	fmt.Printf("Canary targets: %d\n", len(s.canaryTargets))
	fmt.Printf("Validation period: %d minutes\n", s.config.ValidationPeriodMinutes)

	// For now, simulate waiting
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-time.After(time.Duration(s.config.ValidationPeriodMinutes) * time.Minute):
		return fmt.Errorf("validation period expired without approval")
	}
}

func (s *CanaryStrategy) validateCanary(ctx context.Context, wave *deployment.DeploymentWave) error {
	// Monitor canary health during validation period
	validationDuration := time.Duration(s.config.ValidationPeriodMinutes) * time.Minute
	checkInterval := time.Minute
	checks := int(validationDuration / checkInterval)

	fmt.Printf("Starting canary validation for %d minutes...\n", s.config.ValidationPeriodMinutes)

	for i := 0; i < checks; i++ {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(checkInterval):
			// Check canary health
			health, err := s.checkCanaryHealth(ctx)
			if err != nil {
				return fmt.Errorf("canary health check failed: %w", err)
			}

			if health < s.config.SuccessThreshold {
				return fmt.Errorf("canary health %.2f%% below threshold %.2f%%", 
					health*100, s.config.SuccessThreshold*100)
			}

			fmt.Printf("Canary health check %d/%d: %.2f%%\n", i+1, checks, health*100)
		}
	}

	fmt.Println("Canary validation successful, proceeding with full deployment")
	return nil
}

func (s *CanaryStrategy) checkCanaryHealth(ctx context.Context) (float64, error) {
	// In a real implementation, this would:
	// 1. Query metrics for canary targets
	// 2. Compare with baseline metrics
	// 3. Calculate health score based on configured metrics

	// For now, return a simulated health score
	healthyTargets := 0
	for _, target := range s.canaryTargets {
		if target.Status == "completed" && target.HealthCheckPassed != nil && *target.HealthCheckPassed {
			healthyTargets++
		}
	}

	if len(s.canaryTargets) == 0 {
		return 0, fmt.Errorf("no canary targets to check")
	}

	return float64(healthyTargets) / float64(len(s.canaryTargets)), nil
}