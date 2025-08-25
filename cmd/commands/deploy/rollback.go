package deploy

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/arxos/core/internal/deployment"
)

var rollbackCmd = &cobra.Command{
	Use:   "rollback [deployment-id]",
	Short: "Rollback a deployment",
	Long: `Rollback a deployment to restore previous building states.

The rollback operation will restore each affected building to its state before
the deployment. You can rollback the entire deployment or specific buildings.

Examples:
  # Rollback entire deployment
  arxos deploy rollback deployment-123 --reason "Performance issues detected"
  
  # Rollback specific buildings
  arxos deploy rollback deployment-123 --buildings bldg1,bldg2 --reason "Health check failures"
  
  # Force rollback even if deployment is in progress
  arxos deploy rollback deployment-123 --force --reason "Critical issue"`,
	Args: cobra.ExactArgs(1),
	RunE: runRollback,
}

var (
	rollbackReason    string
	rollbackScope     string
	rollbackBuildings []string
	forceRollback     bool
	skipConfirmation  bool
)

func init() {
	rollbackCmd.Flags().StringVarP(&rollbackReason, "reason", "r", "", "Reason for rollback (required)")
	rollbackCmd.Flags().StringVar(&rollbackScope, "scope", "full", "Rollback scope (full, partial, single_building)")
	rollbackCmd.Flags().StringSliceVar(&rollbackBuildings, "buildings", []string{}, "Specific buildings to rollback")
	rollbackCmd.Flags().BoolVarP(&forceRollback, "force", "f", false, "Force rollback even if deployment is in progress")
	rollbackCmd.Flags().BoolVarP(&skipConfirmation, "yes", "y", false, "Skip confirmation prompt")
	
	rollbackCmd.MarkFlagRequired("reason")
}

func runRollback(cmd *cobra.Command, args []string) error {
	deploymentID := args[0]
	
	// Validate scope
	if rollbackScope != "full" && len(rollbackBuildings) == 0 {
		return fmt.Errorf("buildings must be specified for %s rollback", rollbackScope)
	}
	
	if rollbackScope == "single_building" && len(rollbackBuildings) != 1 {
		return fmt.Errorf("exactly one building must be specified for single_building rollback")
	}
	
	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()
	
	// Create rollback manager
	controller := deployment.NewController(db, nil)
	rollbackManager := deployment.NewRollbackManager(db, controller, nil)
	
	ctx := context.Background()
	
	// Get deployment details
	deploymentDetails, err := controller.GetDeployment(ctx, deploymentID)
	if err != nil {
		return fmt.Errorf("failed to get deployment: %w", err)
	}
	
	// Display rollback details
	fmt.Printf("Rollback Details\n")
	fmt.Printf("%s\n", strings.Repeat("=", 60))
	fmt.Printf("Deployment:  %s (%s)\n", deploymentDetails.Name, deploymentDetails.ID)
	fmt.Printf("Status:      %s\n", deploymentDetails.Status)
	fmt.Printf("Scope:       %s\n", rollbackScope)
	
	if rollbackScope == "full" {
		fmt.Printf("Targets:     All %d buildings\n", deploymentDetails.TargetCount)
	} else {
		fmt.Printf("Targets:     %d buildings\n", len(rollbackBuildings))
		for _, b := range rollbackBuildings {
			fmt.Printf("  • %s\n", b)
		}
	}
	
	fmt.Printf("Reason:      %s\n", rollbackReason)
	fmt.Printf("\n")
	
	// Confirmation prompt
	if !skipConfirmation {
		fmt.Printf("⚠️  WARNING: This will restore affected buildings to their previous state.\n")
		fmt.Printf("Are you sure you want to proceed? (yes/no): ")
		
		var response string
		fmt.Scanln(&response)
		
		if strings.ToLower(response) != "yes" && strings.ToLower(response) != "y" {
			fmt.Println("Rollback cancelled.")
			return nil
		}
	}
	
	// Prepare rollback request
	req := &deployment.RollbackRequest{
		DeploymentID:    deploymentID,
		Scope:           rollbackScope,
		Buildings:       rollbackBuildings,
		Reason:          rollbackReason,
		Force:           forceRollback,
		TriggeredBy:     "cli-user",
		TriggeredByName: "CLI User",
	}
	
	// Execute rollback
	fmt.Printf("\nInitiating rollback...\n")
	result, err := rollbackManager.RollbackDeployment(ctx, req)
	if err != nil {
		return fmt.Errorf("rollback failed: %w", err)
	}
	
	// Display result
	fmt.Printf("\n✓ Rollback initiated successfully!\n\n")
	fmt.Printf("Rollback ID: %s\n", result.RollbackID)
	fmt.Printf("Status:      In Progress\n")
	
	fmt.Printf("\nUse the following command to monitor rollback progress:\n")
	fmt.Printf("  arxos deploy rollback-status %s\n", result.RollbackID)
	
	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(result, "", "  ")
		fmt.Printf("\n%s\n", jsonData)
	}
	
	return nil
}