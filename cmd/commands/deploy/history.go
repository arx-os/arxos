package deploy

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var historyCmd = &cobra.Command{
	Use:   "history [building-id]",
	Short: "Show deployment history for a building",
	Long: `Display the deployment history for a specific building.

Shows all deployments that have affected the building, including their status,
timing, and any rollbacks.

Examples:
  # Show deployment history for a building
  arxos deploy history bldg-123
  
  # Show detailed history with health checks
  arxos deploy history bldg-123 --detailed
  
  # Show only failed deployments
  arxos deploy history bldg-123 --failed-only`,
	Args: cobra.ExactArgs(1),
	RunE: runHistory,
}

var (
	historyDetailed  bool
	historyFailedOnly bool
	historyLimit     int
)

func init() {
	historyCmd.Flags().BoolVarP(&historyDetailed, "detailed", "d", false, "Show detailed information")
	historyCmd.Flags().BoolVar(&historyFailedOnly, "failed-only", false, "Show only failed deployments")
	historyCmd.Flags().IntVarP(&historyLimit, "limit", "l", 20, "Maximum number of results")
}

func runHistory(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	
	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()
	
	ctx := context.Background()
	
	// Query deployment history
	query := `
		SELECT 
			d.id, d.name, d.status, d.strategy,
			dt.status as target_status,
			dt.started_at, dt.completed_at, dt.duration_ms,
			dt.health_check_passed, dt.validation_passed,
			dt.error_message
		FROM deployments d
		JOIN deployment_targets dt ON d.id = dt.deployment_id
		WHERE dt.building_id = $1
	`
	
	if historyFailedOnly {
		query += " AND dt.status = 'failed'"
	}
	
	query += " ORDER BY d.created_at DESC LIMIT $2"
	
	var history []struct {
		ID                string     `db:"id"`
		Name              string     `db:"name"`
		Status            string     `db:"status"`
		Strategy          string     `db:"strategy"`
		TargetStatus      string     `db:"target_status"`
		StartedAt         *time.Time `db:"started_at"`
		CompletedAt       *time.Time `db:"completed_at"`
		DurationMs        *int       `db:"duration_ms"`
		HealthCheckPassed *bool      `db:"health_check_passed"`
		ValidationPassed  *bool      `db:"validation_passed"`
		ErrorMessage      string     `db:"error_message"`
	}
	
	err = db.SelectContext(ctx, &history, query, buildingID, historyLimit)
	if err != nil {
		return fmt.Errorf("failed to get deployment history: %w", err)
	}
	
	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(history, "", "  ")
		fmt.Printf("%s\n", jsonData)
		return nil
	}
	
	// Display history
	fmt.Printf("Deployment History for Building: %s\n", buildingID)
	fmt.Printf("%s\n", strings.Repeat("=", 80))
	
	if len(history) == 0 {
		fmt.Println("No deployment history found for this building.")
		return nil
	}
	
	for i, h := range history {
		if i > 0 {
			fmt.Printf("\n%s\n", strings.Repeat("-", 40))
		}
		
		fmt.Printf("\nDeployment: %s\n", h.Name)
		fmt.Printf("ID:         %s\n", h.ID)
		fmt.Printf("Strategy:   %s\n", h.Strategy)
		fmt.Printf("Status:     %s %s\n", getStatusIcon(h.TargetStatus), h.TargetStatus)
		
		if h.StartedAt != nil {
			fmt.Printf("Started:    %s\n", h.StartedAt.Format("2006-01-02 15:04:05"))
		}
		
		if h.CompletedAt != nil {
			fmt.Printf("Completed:  %s", h.CompletedAt.Format("2006-01-02 15:04:05"))
			if h.DurationMs != nil {
				fmt.Printf(" (duration: %dms)", *h.DurationMs)
			}
			fmt.Printf("\n")
		}
		
		if historyDetailed {
			if h.HealthCheckPassed != nil {
				fmt.Printf("Health:     %s\n", formatCheckResult(*h.HealthCheckPassed))
			}
			if h.ValidationPassed != nil {
				fmt.Printf("Validation: %s\n", formatCheckResult(*h.ValidationPassed))
			}
		}
		
		if h.ErrorMessage != "" {
			fmt.Printf("Error:      %s\n", h.ErrorMessage)
		}
	}
	
	if len(history) == historyLimit {
		fmt.Printf("\n(Showing last %d deployments. Use --limit to see more)\n", historyLimit)
	}
	
	return nil
}

func formatCheckResult(passed bool) string {
	if passed {
		return "✓ Passed"
	}
	return "✗ Failed"
}