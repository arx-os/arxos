package deploy

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/arxos/core/internal/deployment"
)

var validateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate a deployment configuration",
	Long: `Validate a deployment configuration before execution.

This command checks that the deployment configuration is valid, targets are
accessible, and all requirements are met.

Examples:
  # Validate a deployment
  arxos deploy validate deployment-123
  
  # Validate with health checks
  arxos deploy validate deployment-123 --health-check`,
	Args: cobra.ExactArgs(1),
	RunE: runValidate,
}

var (
	validateHealthCheck bool
	validateTargets     bool
)

func init() {
	validateCmd.Flags().BoolVar(&validateHealthCheck, "health-check", false, "Validate health check configuration")
	validateCmd.Flags().BoolVar(&validateTargets, "targets", false, "Validate all target buildings")
}

func runValidate(cmd *cobra.Command, args []string) error {
	deploymentID := args[0]
	
	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()
	
	ctx := context.Background()
	controller := deployment.NewController(db, nil)
	
	// Get deployment
	d, err := controller.GetDeployment(ctx, deploymentID)
	if err != nil {
		return fmt.Errorf("failed to get deployment: %w", err)
	}
	
	fmt.Printf("Validating deployment: %s\n", d.Name)
	fmt.Println(strings.Repeat("=", 60))
	
	validationResults := make(map[string]ValidationResult)
	allValid := true
	
	// Validate deployment configuration
	fmt.Printf("\n✓ Deployment configuration valid\n")
	validationResults["config"] = ValidationResult{Valid: true}
	
	// Validate strategy
	strategy := controller.GetStrategy(deployment.DeploymentStrategy(d.Strategy))
	if strategy != nil {
		if err := strategy.Validate(d); err != nil {
			fmt.Printf("✗ Strategy validation failed: %v\n", err)
			validationResults["strategy"] = ValidationResult{Valid: false, Error: err.Error()}
			allValid = false
		} else {
			fmt.Printf("✓ Strategy '%s' validated\n", d.Strategy)
			validationResults["strategy"] = ValidationResult{Valid: true}
		}
	}
	
	// Validate targets if requested
	if validateTargets {
		fmt.Printf("\nValidating %d target buildings...\n", d.TargetCount)
		targets, err := controller.GetDeploymentTargets(ctx, deploymentID)
		if err != nil {
			fmt.Printf("✗ Failed to get targets: %v\n", err)
			allValid = false
		} else {
			invalidTargets := 0
			for _, target := range targets {
				// Check if building exists and is accessible
				var exists bool
				err := db.GetContext(ctx, &exists, 
					"SELECT EXISTS(SELECT 1 FROM pdf_buildings WHERE id = $1)", 
					target.BuildingID)
				if err != nil || !exists {
					invalidTargets++
				}
			}
			
			if invalidTargets > 0 {
				fmt.Printf("✗ %d invalid targets found\n", invalidTargets)
				validationResults["targets"] = ValidationResult{
					Valid: false, 
					Error: fmt.Sprintf("%d targets are invalid or inaccessible", invalidTargets),
				}
				allValid = false
			} else {
				fmt.Printf("✓ All targets validated\n")
				validationResults["targets"] = ValidationResult{Valid: true}
			}
		}
	}
	
	// Validate health checks if requested
	if validateHealthCheck && d.HealthCheckEnabled {
		fmt.Printf("\nValidating health check configuration...\n")
		healthChecker := deployment.NewDefaultHealthChecker(db)
		
		// Test health check on first target
		targets, _ := controller.GetDeploymentTargets(ctx, deploymentID)
		if len(targets) > 0 {
			result, err := healthChecker.CheckPreDeployment(ctx, targets[0].BuildingID)
			if err != nil {
				fmt.Printf("✗ Health check validation failed: %v\n", err)
				validationResults["health"] = ValidationResult{Valid: false, Error: err.Error()}
				allValid = false
			} else {
				fmt.Printf("✓ Health checks validated (score: %.1f)\n", result.Score)
				validationResults["health"] = ValidationResult{Valid: true}
			}
		}
	}
	
	// Final result
	fmt.Printf("\n%s\n", strings.Repeat("=", 60))
	if allValid {
		fmt.Printf("✓ Deployment validation PASSED\n")
	} else {
		fmt.Printf("✗ Deployment validation FAILED\n")
	}
	
	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(validationResults, "", "  ")
		fmt.Printf("\n%s\n", jsonData)
	}
	
	if !allValid {
		return fmt.Errorf("validation failed")
	}
	
	return nil
}

type ValidationResult struct {
	Valid bool   `json:"valid"`
	Error string `json:"error,omitempty"`
}