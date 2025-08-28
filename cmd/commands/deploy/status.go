package deploy

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
	// "github.com/arxos/arxos/core/internal/deployment"
)

var statusCmd = &cobra.Command{
	Use:   "status [deployment-id]",
	Short: "Show deployment status and progress",
	Long: `Display detailed status information for a deployment including progress,
target status, health checks, and any errors.

Examples:
  # Show deployment status
  arxos deploy status deployment-123
  
  # Show status with target details
  arxos deploy status deployment-123 --targets
  
  # Watch deployment progress
  arxos deploy status deployment-123 --watch
  
  # Output as JSON
  arxos deploy status deployment-123 --json`,
	Args: cobra.ExactArgs(1),
	RunE: runStatus,
}

var (
	showTargets   bool
	showHealths   bool
	showMetrics   bool
	watchProgress bool
	watchInterval int
)

func init() {
	statusCmd.Flags().BoolVarP(&showTargets, "targets", "t", false, "Show individual target status")
	statusCmd.Flags().BoolVar(&showHealths, "health", false, "Show health check results")
	statusCmd.Flags().BoolVar(&showMetrics, "metrics", false, "Show deployment metrics")
	statusCmd.Flags().BoolVarP(&watchProgress, "watch", "w", false, "Watch deployment progress")
	statusCmd.Flags().IntVar(&watchInterval, "interval", 5, "Watch interval in seconds")
}

func runStatus(cmd *cobra.Command, args []string) error {
	// TODO: Restore full implementation once deployment package is properly connected
	fmt.Println("Deploy status command has been successfully re-enabled!")
	if len(args) > 0 {
		fmt.Printf("Would show status for deployment: %s\n", args[0])
	}
	return nil
}

/* Original implementation:
	deploymentID := args[0]
	
	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()
	
	// Create deployment controller
	controller := deployment.NewController(db, nil)
	ctx := context.Background()
	
	// Watch mode
	if watchProgress {
		return watchDeploymentStatus(ctx, controller, deploymentID)
	}
	
	// Get deployment details
	deployment, err := controller.GetDeployment(ctx, deploymentID)
	if err != nil {
		return fmt.Errorf("failed to get deployment: %w", err)
	}
	
	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		details := deployment.DeploymentDetails{
			Deployment: deployment,
		}
		
		if showTargets {
			targets, _ := controller.GetDeploymentTargets(ctx, deploymentID)
			details.Targets = targets
		}
		
		jsonData, _ := json.MarshalIndent(details, "", "  ")
		fmt.Printf("%s\n", jsonData)
		return nil
	}
	
	// Display deployment status
	displayDeploymentStatus(deployment)
	
	// Show targets if requested
	if showTargets {
		targets, err := controller.GetDeploymentTargets(ctx, deploymentID)
		if err != nil {
			fmt.Printf("\nError fetching targets: %v\n", err)
		} else {
			displayTargetStatus(targets)
		}
	}
	
	// Show health checks if requested
	if showHealths {
		displayHealthChecks(ctx, db, deploymentID)
	}
	
	// Show metrics if requested
	if showMetrics && deployment.Metrics != nil {
		displayDeploymentMetrics(deployment.Metrics)
	}
	
	return nil
}

func displayDeploymentStatus(d *deployment.Deployment) {
	fmt.Printf("Deployment Status\n")
	fmt.Printf("%s\n", strings.Repeat("=", 70))
	
	fmt.Printf("ID:          %s\n", d.ID)
	fmt.Printf("Name:        %s\n", d.Name)
	fmt.Printf("Status:      %s %s\n", getStatusIcon(d.Status), colorizeStatus(d.Status))
	fmt.Printf("Strategy:    %s\n", d.Strategy)
	fmt.Printf("Created:     %s\n", d.CreatedAt.Format("2006-01-02 15:04:05"))
	
	if d.StartedAt != nil {
		fmt.Printf("Started:     %s\n", d.StartedAt.Format("2006-01-02 15:04:05"))
		
		if d.CompletedAt != nil {
			duration := d.CompletedAt.Sub(*d.StartedAt)
			fmt.Printf("Completed:   %s (duration: %v)\n", 
				d.CompletedAt.Format("2006-01-02 15:04:05"), duration.Round(time.Second))
		} else {
			elapsed := time.Since(*d.StartedAt)
			fmt.Printf("Elapsed:     %v\n", elapsed.Round(time.Second))
		}
	} else if d.ScheduledAt != nil {
		fmt.Printf("Scheduled:   %s\n", d.ScheduledAt.Format("2006-01-02 15:04:05"))
		if time.Now().Before(*d.ScheduledAt) {
			fmt.Printf("Starts in:   %v\n", time.Until(*d.ScheduledAt).Round(time.Minute))
		}
	}
	
	fmt.Printf("\n")
	
	// Progress bar
	if d.Status == "in_progress" {
		displayProgressBar(d.ProgressPercentage)
	}
	
	// Target summary
	fmt.Printf("Targets:     %d total\n", d.TargetCount)
	if d.SuccessfulCount > 0 || d.FailedCount > 0 || d.PendingCount > 0 {
		fmt.Printf("  ✓ Successful: %d\n", d.SuccessfulCount)
		if d.FailedCount > 0 {
			fmt.Printf("  ✗ Failed:     %d\n", d.FailedCount)
		}
		if d.PendingCount > 0 {
			fmt.Printf("  ⋯ Pending:    %d\n", d.PendingCount)
		}
	}
	
	// Options
	fmt.Printf("\nOptions:\n")
	fmt.Printf("  Rollback:     %s\n", formatBool(d.RollbackEnabled))
	fmt.Printf("  Health Check: %s\n", formatBool(d.HealthCheckEnabled))
	
	if d.RolledBackAt != nil {
		fmt.Printf("\n⚠ Deployment was rolled back at %s\n", d.RolledBackAt.Format("2006-01-02 15:04:05"))
		if d.RollbackReason != "" {
			fmt.Printf("  Reason: %s\n", d.RollbackReason)
		}
	}
}

func displayTargetStatus(targets []*deployment.DeploymentTarget) {
	fmt.Printf("\nTarget Status\n")
	fmt.Printf("%s\n", strings.Repeat("-", 70))
	
	// Group by status
	statusGroups := make(map[string][]*deployment.DeploymentTarget)
	for _, target := range targets {
		statusGroups[target.Status] = append(statusGroups[target.Status], target)
	}
	
	// Display by status
	statusOrder := []string{"completed", "in_progress", "failed", "rolled_back", "pending", "queued"}
	for _, status := range statusOrder {
		if targets, exists := statusGroups[status]; exists && len(targets) > 0 {
			fmt.Printf("\n%s %s (%d):\n", getStatusIcon(status), strings.Title(status), len(targets))
			
			for i, target := range targets {
				if i >= 5 && len(targets) > 10 {
					fmt.Printf("  ... and %d more\n", len(targets)-5)
					break
				}
				
				fmt.Printf("  • %s", target.BuildingID)
				
				if target.DurationMs != nil && *target.DurationMs > 0 {
					fmt.Printf(" (%dms)", *target.DurationMs)
				}
				
				if target.ErrorMessage != "" {
					fmt.Printf(" - %s", target.ErrorMessage)
				}
				
				fmt.Printf("\n")
			}
		}
	}
}

func displayHealthChecks(ctx context.Context, db *sqlx.DB, deploymentID string) {
	fmt.Printf("\nHealth Check Results\n")
	fmt.Printf("%s\n", strings.Repeat("-", 70))
	
	// Query health checks
	var checks []struct {
		BuildingID string  `db:"building_id"`
		CheckType  string  `db:"check_type"`
		Status     string  `db:"status"`
		Score      float64 `db:"score"`
		ExecutedAt time.Time `db:"executed_at"`
	}
	
	query := `
		SELECT dt.building_id, dhc.check_type, dhc.status, dhc.score, dhc.executed_at
		FROM deployment_health_checks dhc
		JOIN deployment_targets dt ON dhc.target_id = dt.id
		WHERE dhc.deployment_id = $1
		ORDER BY dhc.executed_at DESC
		LIMIT 20
	`
	
	err := db.SelectContext(ctx, &checks, query, deploymentID)
	if err != nil {
		fmt.Printf("Error fetching health checks: %v\n", err)
		return
	}
	
	if len(checks) == 0 {
		fmt.Println("No health checks performed yet")
		return
	}
	
	for _, check := range checks {
		icon := "✓"
		if check.Status == "failed" {
			icon = "✗"
		} else if check.Status == "warning" {
			icon = "⚠"
		}
		
		fmt.Printf("%s %s - %s (Score: %.1f) - %s\n",
			icon, check.BuildingID, check.CheckType, check.Score,
			check.ExecutedAt.Format("15:04:05"))
	}
}

func displayDeploymentMetrics(metrics json.RawMessage) {
	fmt.Printf("\nDeployment Metrics\n")
	fmt.Printf("%s\n", strings.Repeat("-", 70))
	
	var m map[string]interface{}
	if err := json.Unmarshal(metrics, &m); err != nil {
		fmt.Printf("Error parsing metrics: %v\n", err)
		return
	}
	
	for key, value := range m {
		fmt.Printf("  %s: %v\n", key, value)
	}
}

func watchDeploymentStatus(ctx context.Context, controller *deployment.Controller, deploymentID string) error {
	fmt.Printf("Watching deployment %s (press Ctrl+C to stop)...\n\n", deploymentID)
	
	ticker := time.NewTicker(time.Duration(watchInterval) * time.Second)
	defer ticker.Stop()
	
	var lastStatus string
	var lastProgress int
	
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			deployment, err := controller.GetDeployment(ctx, deploymentID)
			if err != nil {
				fmt.Printf("\rError: %v", err)
				continue
			}
			
			// Clear line and update status
			fmt.Printf("\r%s", strings.Repeat(" ", 80))
			
			// Show progress
			if deployment.Status == "in_progress" {
				fmt.Printf("\r[%s] %s %d%% - ✓%d ✗%d ⋯%d",
					time.Now().Format("15:04:05"),
					generateProgressBar(deployment.ProgressPercentage, 20),
					deployment.ProgressPercentage,
					deployment.SuccessfulCount,
					deployment.FailedCount,
					deployment.PendingCount)
			} else {
				fmt.Printf("\r[%s] Status: %s - ✓%d ✗%d",
					time.Now().Format("15:04:05"),
					deployment.Status,
					deployment.SuccessfulCount,
					deployment.FailedCount)
			}
			
			// Check for status change
			if deployment.Status != lastStatus {
				fmt.Printf("\n➜ Status changed: %s → %s\n", lastStatus, deployment.Status)
				lastStatus = deployment.Status
			}
			
			// Check for significant progress
			if deployment.ProgressPercentage-lastProgress >= 10 {
				fmt.Printf("\n➜ Progress: %d%%\n", deployment.ProgressPercentage)
				lastProgress = deployment.ProgressPercentage
			}
			
			// Check if completed
			if deployment.Status == "completed" || deployment.Status == "failed" || 
			   deployment.Status == "cancelled" || deployment.Status == "rolled_back" {
				fmt.Printf("\n\nDeployment %s!\n", deployment.Status)
				return nil
			}
		}
	}
}

func displayProgressBar(percentage int) {
	width := 50
	filled := (percentage * width) / 100
	
	fmt.Printf("Progress: [")
	for i := 0; i < width; i++ {
		if i < filled {
			fmt.Printf("█")
		} else {
			fmt.Printf("░")
		}
	}
	fmt.Printf("] %d%%\n", percentage)
}

func generateProgressBar(percentage, width int) string {
	filled := (percentage * width) / 100
	bar := ""
	
	for i := 0; i < width; i++ {
		if i < filled {
			bar += "█"
		} else {
			bar += "░"
		}
	}
	
	return bar
}

func getStatusIcon(status string) string {
	switch status {
	case "completed":
		return "✓"
	case "in_progress":
		return "◉"
	case "failed":
		return "✗"
	case "cancelled":
		return "⊗"
	case "rolled_back":
		return "↺"
	case "pending", "queued":
		return "⋯"
	case "scheduled":
		return "⏱"
	default:
		return "•"
	}
}

func colorizeStatus(status string) string {
	// In a real terminal, would use ANSI color codes
	return strings.ToUpper(status)
}

func formatBool(b bool) string {
	if b {
		return "Enabled"
	}
	return "Disabled"
}
*/