package strategies

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/arxos/core/internal/deployment"
)

// RollingStrategy implements rolling deployment (gradual waves)
type RollingStrategy struct {
	config        *deployment.RollingStrategyConfig
	waves         []*deployment.DeploymentWave
	currentWave   int
	failureCount  int
	successCount  int
}

// NewRollingStrategy creates a new rolling deployment strategy
func NewRollingStrategy() *RollingStrategy {
	return &RollingStrategy{
		config: &deployment.RollingStrategyConfig{
			WaveSizePercentage: 25,
			WaveDelayMinutes:   15,
			StopOnFailure:      true,
			MaxFailureRate:     0.1, // 10% failure rate
		},
		currentWave: 0,
	}
}

// Name returns the strategy name
func (s *RollingStrategy) Name() string {
	return "rolling"
}

// Validate validates the deployment for this strategy
func (s *RollingStrategy) Validate(d *deployment.Deployment) error {
	// Parse strategy config if provided
	if d.StrategyConfig != nil {
		var config deployment.RollingStrategyConfig
		if err := json.Unmarshal(d.StrategyConfig, &config); err != nil {
			return fmt.Errorf("invalid strategy config: %w", err)
		}
		s.config = &config
	}

	// Validate config
	if s.config.WaveSizePercentage <= 0 && s.config.WaveSizeFixed <= 0 {
		return fmt.Errorf("either wave_size_percentage or wave_size_fixed must be specified")
	}

	if s.config.WaveSizePercentage > 100 {
		return fmt.Errorf("wave_size_percentage cannot exceed 100")
	}

	if s.config.WaveDelayMinutes < 0 {
		s.config.WaveDelayMinutes = 0
	}

	if s.config.MaxFailureRate < 0 || s.config.MaxFailureRate > 1 {
		s.config.MaxFailureRate = 0.1
	}

	return nil
}

// Plan creates deployment waves for rolling strategy
func (s *RollingStrategy) Plan(d *deployment.Deployment, targets []*deployment.DeploymentTarget) ([]*deployment.DeploymentWave, error) {
	if len(targets) == 0 {
		return nil, fmt.Errorf("no targets to deploy")
	}

	// Calculate wave size
	var waveSize int
	if s.config.WaveSizeFixed > 0 {
		waveSize = s.config.WaveSizeFixed
	} else {
		waveSize = int(math.Ceil(float64(len(targets)) * float64(s.config.WaveSizePercentage) / 100))
	}

	if waveSize == 0 {
		waveSize = 1
	}

	// Create waves
	waves := make([]*deployment.DeploymentWave, 0)
	for i := 0; i < len(targets); i += waveSize {
		end := i + waveSize
		if end > len(targets) {
			end = len(targets)
		}

		waveTargets := targets[i:end]
		
		// Set wave number for each target
		for _, target := range waveTargets {
			target.DeploymentWave = len(waves)
			target.DeploymentOrder = i
		}

		wave := &deployment.DeploymentWave{
			WaveNumber: len(waves),
			Targets:    waveTargets,
			Config: map[string]interface{}{
				"wave_delay_minutes": s.config.WaveDelayMinutes,
				"stop_on_failure":    s.config.StopOnFailure,
				"max_failure_rate":   s.config.MaxFailureRate,
				"parallel":          true, // Deploy within wave in parallel
			},
		}
		waves = append(waves, wave)
	}

	s.waves = waves
	return waves, nil
}

// Execute executes a deployment wave
func (s *RollingStrategy) Execute(ctx context.Context, wave *deployment.DeploymentWave) error {
	s.currentWave = wave.WaveNumber
	
	// If not the first wave, apply delay
	if wave.WaveNumber > 0 && s.config.WaveDelayMinutes > 0 {
		fmt.Printf("Waiting %d minutes before starting wave %d...\n", 
			s.config.WaveDelayMinutes, wave.WaveNumber+1)
		
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Duration(s.config.WaveDelayMinutes) * time.Minute):
			// Continue with deployment
		}
	}

	fmt.Printf("Starting rolling deployment wave %d/%d (%d targets)\n", 
		wave.WaveNumber+1, len(s.waves), len(wave.Targets))

	// Check previous wave health before proceeding
	if wave.WaveNumber > 0 {
		if err := s.validatePreviousWave(ctx); err != nil {
			return fmt.Errorf("previous wave validation failed: %w", err)
		}
	}

	return nil
}

// OnFailure handles deployment failure for a target
func (s *RollingStrategy) OnFailure(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget, err error) error {
	s.failureCount++
	
	// Calculate failure rate for current wave
	currentWaveTargets := 0
	currentWaveFailures := 0
	
	if s.currentWave < len(s.waves) {
		currentWaveTargets = len(s.waves[s.currentWave].Targets)
		
		for _, t := range s.waves[s.currentWave].Targets {
			if t.Status == "failed" {
				currentWaveFailures++
			}
		}
	}

	// Check if we should stop
	if s.config.StopOnFailure {
		return fmt.Errorf("rolling deployment stopped due to failure in wave %d: %w", 
			s.currentWave+1, err)
	}

	// Check failure rate
	if currentWaveTargets > 0 {
		waveFailureRate := float64(currentWaveFailures) / float64(currentWaveTargets)
		if waveFailureRate > s.config.MaxFailureRate {
			return fmt.Errorf("wave %d failure rate %.2f%% exceeds maximum %.2f%%", 
				s.currentWave+1, waveFailureRate*100, s.config.MaxFailureRate*100)
		}
	}

	// Log but continue
	fmt.Printf("Target %s failed in wave %d: %v (continuing)\n", 
		target.BuildingID, s.currentWave+1, err)
	
	return nil
}

// OnSuccess handles successful deployment for a target
func (s *RollingStrategy) OnSuccess(ctx context.Context, d *deployment.Deployment, target *deployment.DeploymentTarget) error {
	s.successCount++
	
	// Check if current wave is complete
	if s.currentWave < len(s.waves) {
		waveComplete := true
		waveSuccessful := 0
		waveFailed := 0
		
		for _, t := range s.waves[s.currentWave].Targets {
			switch t.Status {
			case "completed":
				waveSuccessful++
			case "failed":
				waveFailed++
			case "pending", "in_progress":
				waveComplete = false
			}
		}
		
		if waveComplete {
			totalWaveTargets := len(s.waves[s.currentWave].Targets)
			successRate := float64(waveSuccessful) / float64(totalWaveTargets)
			
			fmt.Printf("Wave %d complete: %d/%d successful (%.2f%% success rate)\n",
				s.currentWave+1, waveSuccessful, totalWaveTargets, successRate*100)
			
			// Check if wave met success criteria
			if successRate < (1.0 - s.config.MaxFailureRate) {
				return fmt.Errorf("wave %d success rate %.2f%% below minimum %.2f%%",
					s.currentWave+1, successRate*100, (1.0-s.config.MaxFailureRate)*100)
			}
		}
	}
	
	return nil
}

// Helper methods

func (s *RollingStrategy) validatePreviousWave(ctx context.Context) error {
	if s.currentWave == 0 || s.currentWave > len(s.waves) {
		return nil
	}
	
	previousWave := s.waves[s.currentWave-1]
	
	// Count successes and failures
	successful := 0
	failed := 0
	
	for _, target := range previousWave.Targets {
		switch target.Status {
		case "completed":
			successful++
		case "failed":
			failed++
		}
	}
	
	total := len(previousWave.Targets)
	if total == 0 {
		return nil
	}
	
	failureRate := float64(failed) / float64(total)
	
	if failureRate > s.config.MaxFailureRate {
		return fmt.Errorf("previous wave failure rate %.2f%% exceeds maximum %.2f%%",
			failureRate*100, s.config.MaxFailureRate*100)
	}
	
	fmt.Printf("Previous wave validation passed: %d/%d successful\n", successful, total)
	return nil
}

// GetWaveStatus returns the status of a specific wave
func (s *RollingStrategy) GetWaveStatus(waveNumber int) (successful, failed, pending int) {
	if waveNumber >= len(s.waves) {
		return
	}
	
	for _, target := range s.waves[waveNumber].Targets {
		switch target.Status {
		case "completed":
			successful++
		case "failed":
			failed++
		case "pending", "queued":
			pending++
		}
	}
	
	return
}

// GetProgress returns the overall deployment progress
func (s *RollingStrategy) GetProgress() (completedWaves, totalWaves int, overallProgress float64) {
	totalWaves = len(s.waves)
	totalTargets := 0
	completedTargets := 0
	
	for i, wave := range s.waves {
		waveComplete := true
		for _, target := range wave.Targets {
			totalTargets++
			if target.Status == "completed" || target.Status == "failed" {
				completedTargets++
			} else {
				waveComplete = false
			}
		}
		
		if waveComplete {
			completedWaves = i + 1
		}
	}
	
	if totalTargets > 0 {
		overallProgress = float64(completedTargets) / float64(totalTargets)
	}
	
	return
}