package strategies

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arxos/core/internal/deployment"
)

// BlueGreenStrategy implements blue-green deployment
type BlueGreenStrategy struct {
	config *deployment.BlueGreenStrategyConfig
	blueTargets []*deployment.DeploymentTarget
	greenTargets []*deployment.DeploymentTarget
	currentEnvironment string // "blue" or "green"
	trafficShiftStage int
	switchTime time.Time
}

// NewBlueGreenStrategy creates a new blue-green deployment strategy
func NewBlueGreenStrategy() *BlueGreenStrategy {
	return &BlueGreenStrategy{
		config: &deployment.BlueGreenStrategyConfig{
			ValidationPeriodMinutes:  120,
			TrafficShiftPercentage:   []int{0, 50, 100},
			TrafficShiftDelayMinutes: 30,
			RollbackWindowHours:      24,
			AutoSwitch:               false,
		},
		currentEnvironment: "blue",
		trafficShiftStage:  0,
	}
}

// Name returns the strategy name
func (s *BlueGreenStrategy) Name() string {
	return "blue_green"
}

// Validate validates the deployment for this strategy
func (s *BlueGreenStrategy) Validate(d *deployment.Deployment) error {
	// Parse strategy config if provided
	if d.StrategyConfig != nil {
		var config deployment.BlueGreenStrategyConfig
		if err := json.Unmarshal(d.StrategyConfig, &config); err != nil {
			return fmt.Errorf("invalid strategy config: %w", err)
		}
		s.config = &config
	}

	// Validate config
	if s.config.ValidationPeriodMinutes <= 0 {
		s.config.ValidationPeriodMinutes = 120
	}

	if len(s.config.TrafficShiftPercentage) == 0 {
		s.config.TrafficShiftPercentage = []int{0, 50, 100}
	}

	// Validate traffic shift percentages
	for i, pct := range s.config.TrafficShiftPercentage {
		if pct < 0 || pct > 100 {
			return fmt.Errorf("invalid traffic shift percentage at stage %d: %d", i, pct)
		}
		if i > 0 && pct <= s.config.TrafficShiftPercentage[i-1] {
			return fmt.Errorf("traffic shift percentages must be increasing")
		}
	}

	if s.config.RollbackWindowHours <= 0 {
		s.config.RollbackWindowHours = 24
	}

	// Blue-green requires even number of targets for proper splitting
	// Or we need to handle asymmetric deployments
	if d.TargetCount < 2 {
		return fmt.Errorf("blue-green deployment requires at least 2 targets")
	}

	return nil
}

// Plan creates deployment waves for blue-green strategy
func (s *BlueGreenStrategy) Plan(d *deployment.Deployment, targets []*deployment.DeploymentTarget) ([]*deployment.DeploymentWave, error) {
	if len(targets) < 2 {
		return nil, fmt.Errorf("blue-green deployment requires at least 2 targets")
	}

	// Split targets into blue and green environments
	// In a real scenario, this would be based on existing infrastructure
	// For simulation, we split evenly
	mid := len(targets) / 2
	s.blueTargets = targets[:mid]
	s.greenTargets = targets[mid:]

	// Determine which environment to deploy to
	// In production, this would check current active environment
	deployEnvironment := "green" // Deploy to inactive environment
	if s.currentEnvironment == "green" {
		deployEnvironment = "blue"
	}

	var deployTargets []*deployment.DeploymentTarget
	if deployEnvironment == "blue" {
		deployTargets = s.blueTargets
	} else {
		deployTargets = s.greenTargets
	}

	// Set deployment wave for targets
	for i, target := range deployTargets {
		target.DeploymentWave = 0
		target.DeploymentOrder = i
	}

	// Create waves
	waves := []*deployment.DeploymentWave{
		{
			WaveNumber: 0,
			Targets:    deployTargets,
			Config: map[string]interface{}{
				"environment":              deployEnvironment,
				"type":                     "deployment",
				"parallel":                 true,
				"validation_period_minutes": s.config.ValidationPeriodMinutes,
			},
		},
	}

	// Add traffic shift waves
	for i, shiftPct := range s.config.TrafficShiftPercentage {
		wave := &deployment.DeploymentWave{
			WaveNumber: i + 1,
			Targets:    []*deployment.DeploymentTarget{}, // No actual deployment, just traffic shift
			Config: map[string]interface{}{
				"type":                 "traffic_shift",
				"shift_percentage":     shiftPct,
				"shift_delay_minutes":  s.config.TrafficShiftDelayMinutes,
				"environment":          deployEnvironment,
			},
		}
		waves = append(waves, wave)
	}

	return waves, nil
}

// Execute executes a deployment wave
func (s *BlueGreenStrategy) Execute(ctx context.Context, wave *deployment.DeploymentWave) error {
	waveType, _ := wave.Config["type"].(string)

	switch waveType {
	case "deployment":
		// Deploy to inactive environment
		environment, _ := wave.Config["environment"].(string)
		fmt.Printf("Deploying to %s environment (%d targets)\n", environment, len(wave.Targets))
		
		// After deployment, validate the new environment
		return s.validateEnvironment(ctx, environment)

	case "traffic_shift":
		// Shift traffic to new environment
		shiftPct, _ := wave.Config["shift_percentage"].(int)
		environment, _ := wave.Config["environment"].(string)
		
		return s.shiftTraffic(ctx, environment, shiftPct)

	default:
		return fmt.Errorf("unknown wave type: %s", waveType)
	}
}

// OnFailure handles deployment failure for a target
func (s *BlueGreenStrategy) OnFailure(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget, err error) error {
	// In blue-green, failure in the inactive environment doesn't affect production
	// But we should stop the deployment
	
	if target != nil {
		environment := s.getTargetEnvironment(target)
		
		// If this is the inactive environment, we can safely fail
		if environment != s.currentEnvironment {
			fmt.Printf("Deployment to %s environment failed: %v\n", environment, err)
			fmt.Println("Production environment remains unaffected")
			return fmt.Errorf("blue-green deployment failed in %s environment: %w", environment, err)
		}
		
		// If somehow the active environment is affected, this is critical
		return fmt.Errorf("CRITICAL: active environment affected: %w", err)
	}
	
	return err
}

// OnSuccess handles successful deployment for a target
func (s *BlueGreenStrategy) OnSuccess(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget) error {
	// Check if all targets in the deployment wave are complete
	environment := s.getTargetEnvironment(target)
	envTargets := s.getEnvironmentTargets(environment)
	
	complete := true
	successful := 0
	
	for _, t := range envTargets {
		if t.Status == "completed" {
			successful++
		} else if t.Status != "failed" {
			complete = false
		}
	}
	
	if complete {
		successRate := float64(successful) / float64(len(envTargets))
		fmt.Printf("%s environment deployment complete: %.2f%% success rate\n", 
			environment, successRate*100)
		
		if successRate < 0.95 {
			return fmt.Errorf("%s environment success rate too low: %.2f%%", 
				environment, successRate*100)
		}
		
		// Mark switch time for rollback window
		if environment != s.currentEnvironment {
			s.switchTime = time.Now()
			fmt.Printf("Ready to switch from %s to %s\n", s.currentEnvironment, environment)
		}
	}
	
	return nil
}

// Helper methods

func (s *BlueGreenStrategy) validateEnvironment(ctx context.Context, environment string) error {
	fmt.Printf("Validating %s environment for %d minutes...\n", 
		environment, s.config.ValidationPeriodMinutes)
	
	// In production, this would:
	// 1. Run smoke tests against the new environment
	// 2. Check health endpoints
	// 3. Validate critical functionality
	// 4. Compare metrics with baseline
	
	validationEnd := time.Now().Add(time.Duration(s.config.ValidationPeriodMinutes) * time.Minute)
	checkInterval := 5 * time.Minute
	
	for time.Now().Before(validationEnd) {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(checkInterval):
			// Perform validation checks
			health := s.checkEnvironmentHealth(environment)
			if health < 0.95 {
				return fmt.Errorf("%s environment health check failed: %.2f%%", 
					environment, health*100)
			}
			
			remaining := time.Until(validationEnd)
			fmt.Printf("%s environment healthy, %v remaining in validation\n", 
				environment, remaining.Round(time.Minute))
		}
	}
	
	fmt.Printf("%s environment validation successful\n", environment)
	return nil
}

func (s *BlueGreenStrategy) shiftTraffic(ctx context.Context, environment string, percentage int) error {
	// Wait before shifting traffic
	if s.config.TrafficShiftDelayMinutes > 0 && s.trafficShiftStage > 0 {
		fmt.Printf("Waiting %d minutes before traffic shift...\n", s.config.TrafficShiftDelayMinutes)
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Duration(s.config.TrafficShiftDelayMinutes) * time.Minute):
			// Continue
		}
	}
	
	fmt.Printf("Shifting %d%% traffic to %s environment\n", percentage, environment)
	
	// In production, this would:
	// 1. Update load balancer configuration
	// 2. Modify DNS weights
	// 3. Update service mesh routing rules
	// 4. Monitor for errors during shift
	
	// Simulate traffic shift
	time.Sleep(5 * time.Second)
	
	// Check health after shift
	health := s.checkEnvironmentHealth(environment)
	if health < 0.95 {
		// Rollback traffic shift
		fmt.Printf("Health check failed after traffic shift, rolling back\n")
		return fmt.Errorf("traffic shift to %s failed health check", environment)
	}
	
	s.trafficShiftStage++
	
	if percentage == 100 {
		// Full switch complete
		oldEnvironment := s.currentEnvironment
		s.currentEnvironment = environment
		fmt.Printf("Successfully switched from %s to %s environment\n", 
			oldEnvironment, s.currentEnvironment)
		
		// Start rollback window timer
		go s.monitorRollbackWindow(ctx)
	}
	
	return nil
}

func (s *BlueGreenStrategy) getTargetEnvironment(target *deployment.DeploymentTarget) string {
	for _, t := range s.blueTargets {
		if t.ID == target.ID {
			return "blue"
		}
	}
	return "green"
}

func (s *BlueGreenStrategy) getEnvironmentTargets(environment string) []*deployment.DeploymentTarget {
	if environment == "blue" {
		return s.blueTargets
	}
	return s.greenTargets
}

func (s *BlueGreenStrategy) checkEnvironmentHealth(environment string) float64 {
	// In production, this would check actual health metrics
	// For simulation, return a high health score
	targets := s.getEnvironmentTargets(environment)
	healthy := 0
	
	for _, target := range targets {
		if target.Status == "completed" {
			healthy++
		}
	}
	
	if len(targets) == 0 {
		return 0
	}
	
	return float64(healthy) / float64(len(targets))
}

func (s *BlueGreenStrategy) monitorRollbackWindow(ctx context.Context) {
	rollbackDeadline := s.switchTime.Add(time.Duration(s.config.RollbackWindowHours) * time.Hour)
	
	fmt.Printf("Rollback window open until %s\n", rollbackDeadline.Format(time.RFC3339))
	
	// Monitor for issues during rollback window
	checkInterval := 15 * time.Minute
	
	for time.Now().Before(rollbackDeadline) {
		select {
		case <-ctx.Done():
			return
		case <-time.After(checkInterval):
			// Check health
			health := s.checkEnvironmentHealth(s.currentEnvironment)
			if health < 0.90 {
				fmt.Printf("WARNING: %s environment health degraded: %.2f%%\n", 
					s.currentEnvironment, health*100)
				// In production, would trigger alerts
			}
		}
	}
	
	fmt.Println("Rollback window closed")
}

// Rollback performs a blue-green rollback by switching traffic back
func (s *BlueGreenStrategy) Rollback(ctx context.Context) error {
	if time.Since(s.switchTime) > time.Duration(s.config.RollbackWindowHours)*time.Hour {
		return fmt.Errorf("rollback window has expired")
	}
	
	// Determine previous environment
	previousEnv := "blue"
	if s.currentEnvironment == "blue" {
		previousEnv = "green"
	}
	
	fmt.Printf("Rolling back from %s to %s environment\n", s.currentEnvironment, previousEnv)
	
	// Shift traffic back immediately
	if err := s.shiftTraffic(ctx, previousEnv, 100); err != nil {
		return fmt.Errorf("rollback failed: %w", err)
	}
	
	s.currentEnvironment = previousEnv
	fmt.Println("Rollback completed successfully")
	
	return nil
}