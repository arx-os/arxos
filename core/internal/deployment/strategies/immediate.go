package strategies

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/arxos/core/internal/deployment"
)

// ImmediateStrategy implements immediate deployment (all at once)
type ImmediateStrategy struct {
	config *deployment.ImmediateStrategyConfig
}

// NewImmediateStrategy creates a new immediate deployment strategy
func NewImmediateStrategy() *ImmediateStrategy {
	return &ImmediateStrategy{
		config: &deployment.ImmediateStrategyConfig{
			ParallelExecution: true,
			MaxParallel:       10,
			TimeoutMinutes:    30,
			StopOnFirstError:  false,
		},
	}
}

// Name returns the strategy name
func (s *ImmediateStrategy) Name() string {
	return "immediate"
}

// Validate validates the deployment for this strategy
func (s *ImmediateStrategy) Validate(d *deployment.Deployment) error {
	// Parse strategy config if provided
	if d.StrategyConfig != nil {
		var config deployment.ImmediateStrategyConfig
		if err := json.Unmarshal(d.StrategyConfig, &config); err != nil {
			return fmt.Errorf("invalid strategy config: %w", err)
		}
		s.config = &config
	}

	// Validate config
	if s.config.MaxParallel <= 0 {
		s.config.MaxParallel = 10
	}
	if s.config.TimeoutMinutes <= 0 {
		s.config.TimeoutMinutes = 30
	}

	// Check target count
	if d.TargetCount == 0 {
		return fmt.Errorf("no targets specified for deployment")
	}

	return nil
}

// Plan creates deployment waves for immediate strategy
func (s *ImmediateStrategy) Plan(d *deployment.Deployment, targets []*deployment.DeploymentTarget) ([]*deployment.DeploymentWave, error) {
	if len(targets) == 0 {
		return nil, fmt.Errorf("no targets to deploy")
	}

	// For immediate deployment, create waves based on MaxParallel setting
	waves := make([]*deployment.DeploymentWave, 0)
	
	if s.config.ParallelExecution {
		// Split targets into waves based on MaxParallel
		for i := 0; i < len(targets); i += s.config.MaxParallel {
			end := i + s.config.MaxParallel
			if end > len(targets) {
				end = len(targets)
			}
			
			wave := &deployment.DeploymentWave{
				WaveNumber: len(waves),
				Targets:    targets[i:end],
				Config: map[string]interface{}{
					"parallel":       true,
					"timeout_minutes": s.config.TimeoutMinutes,
				},
			}
			waves = append(waves, wave)
		}
	} else {
		// Single wave with all targets (sequential)
		wave := &deployment.DeploymentWave{
			WaveNumber: 0,
			Targets:    targets,
			Config: map[string]interface{}{
				"parallel":       false,
				"timeout_minutes": s.config.TimeoutMinutes,
			},
		}
		waves = append(waves, wave)
	}

	return waves, nil
}

// Execute executes a deployment wave
func (s *ImmediateStrategy) Execute(ctx context.Context, wave *deployment.DeploymentWave) error {
	// The actual execution is handled by the controller
	// This method can add strategy-specific logic if needed
	
	// Check if we should execute in parallel
	parallel, _ := wave.Config["parallel"].(bool)
	if !parallel {
		// For sequential execution, we might want to add delays or checks
		// between targets, but this is handled by the controller
	}

	return nil
}

// OnFailure handles deployment failure for a target
func (s *ImmediateStrategy) OnFailure(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget, err error) error {
	// For immediate deployment, decide whether to continue or stop
	if s.config.StopOnFirstError {
		// Cancel the entire deployment
		return fmt.Errorf("deployment stopped due to failure: %w", err)
	}

	// Continue with other targets
	// Log the error but don't stop the deployment
	if target != nil {
		// Log error for specific target
		fmt.Printf("Target %s failed: %v\n", target.BuildingID, err)
	}

	return nil // Continue deployment
}

// OnSuccess handles successful deployment for a target
func (s *ImmediateStrategy) OnSuccess(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget) error {
	// For immediate deployment, no special handling needed on success
	// Could add metrics collection or notifications here
	return nil
}