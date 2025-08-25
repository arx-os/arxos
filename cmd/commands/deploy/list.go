package deploy

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"github.com/jmoiron/sqlx"
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List deployments",
	Long: `List deployments with filtering and sorting options.

Examples:
  # List all recent deployments
  arxos deploy list
  
  # List in-progress deployments
  arxos deploy list --status in_progress
  
  # List deployments for a specific building
  arxos deploy list --building bldg-123
  
  # List failed deployments from the last week
  arxos deploy list --status failed --since 7d`,
	Aliases: []string{"ls"},
	RunE:    runList,
}

var (
	listStatus   []string
	listStrategy []string
	listBuilding string
	listSince    string
	listLimit    int
	listOffset   int
	listSortBy   string
	listSortOrder string
	showSummary  bool
)

func init() {
	listCmd.Flags().StringSliceVar(&listStatus, "status", []string{}, 
		"Filter by status (draft, in_progress, completed, failed, rolled_back)")
	listCmd.Flags().StringSliceVar(&listStrategy, "strategy", []string{}, 
		"Filter by strategy (immediate, canary, rolling, blue_green)")
	listCmd.Flags().StringVar(&listBuilding, "building", "", "Filter by building ID")
	listCmd.Flags().StringVar(&listSince, "since", "", "Show deployments since (e.g., 24h, 7d, 30d)")
	listCmd.Flags().IntVarP(&listLimit, "limit", "l", 20, "Maximum number of results")
	listCmd.Flags().IntVar(&listOffset, "offset", 0, "Offset for pagination")
	listCmd.Flags().StringVar(&listSortBy, "sort", "created_at", 
		"Sort by field (created_at, updated_at, name, status)")
	listCmd.Flags().StringVar(&listSortOrder, "order", "desc", "Sort order (asc, desc)")
	listCmd.Flags().BoolVar(&showSummary, "summary", false, "Show summary statistics")
}

func runList(cmd *cobra.Command, args []string) error {
	// Parse since duration
	var sinceTime *time.Time
	if listSince != "" {
		duration, err := parseDuration(listSince)
		if err != nil {
			return fmt.Errorf("invalid since duration: %w", err)
		}
		t := time.Now().Add(-duration)
		sinceTime = &t
	}
	
	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()
	
	ctx := context.Background()
	
	// Build query
	query, args := buildListQuery(listStatus, listStrategy, listBuilding, sinceTime, 
		listSortBy, listSortOrder, listLimit, listOffset)
	
	// Execute query
	var deployments []deploymentSummary
	err = db.SelectContext(ctx, &deployments, query, args...)
	if err != nil {
		return fmt.Errorf("failed to list deployments: %w", err)
	}
	
	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(deployments, "", "  ")
		fmt.Printf("%s\n", jsonData)
		return nil
	}
	
	// Show summary if requested
	if showSummary {
		displayListSummary(ctx, db, sinceTime)
		fmt.Println()
	}
	
	// Display deployments
	if len(deployments) == 0 {
		fmt.Println("No deployments found matching the criteria.")
		return nil
	}
	
	fmt.Printf("Deployments (%d results)\n", len(deployments))
	fmt.Printf("%s\n", strings.Repeat("=", 100))
	fmt.Printf("%-36s %-25s %-12s %-10s %-8s %s\n", 
		"ID", "Name", "Status", "Strategy", "Targets", "Created")
	fmt.Printf("%s\n", strings.Repeat("-", 100))
	
	for _, d := range deployments {
		// Truncate name if too long
		name := d.Name
		if len(name) > 24 {
			name = name[:21] + "..."
		}
		
		// Format status with icon
		status := fmt.Sprintf("%s %-11s", getStatusIcon(d.Status), d.Status)
		
		// Format progress for in-progress deployments
		targets := fmt.Sprintf("%d", d.TargetCount)
		if d.Status == "in_progress" {
			targets = fmt.Sprintf("%d/%d", d.SuccessfulCount+d.FailedCount, d.TargetCount)
		}
		
		fmt.Printf("%-36s %-25s %-12s %-10s %-8s %s\n",
			d.ID,
			name,
			status,
			d.Strategy,
			targets,
			d.CreatedAt.Format("2006-01-02 15:04"))
	}
	
	// Show pagination info
	if listOffset > 0 || len(deployments) == listLimit {
		fmt.Printf("\n")
		if listOffset > 0 {
			fmt.Printf("Showing results %d-%d", listOffset+1, listOffset+len(deployments))
		}
		if len(deployments) == listLimit {
			fmt.Printf(" (use --offset %d for next page)", listOffset+listLimit)
		}
		fmt.Printf("\n")
	}
	
	return nil
}

type deploymentSummary struct {
	ID              string    `db:"id"`
	Name            string    `db:"name"`
	Status          string    `db:"status"`
	Strategy        string    `db:"strategy"`
	TargetCount     int       `db:"target_count"`
	SuccessfulCount int       `db:"successful_count"`
	FailedCount     int       `db:"failed_count"`
	Progress        int       `db:"progress_percentage"`
	CreatedAt       time.Time `db:"created_at"`
	StartedAt       *time.Time `db:"started_at"`
	CompletedAt     *time.Time `db:"completed_at"`
}

func buildListQuery(statuses, strategies []string, buildingID string, since *time.Time,
	sortBy, sortOrder string, limit, offset int) (string, []interface{}) {
	
	query := `
		SELECT 
			d.id, d.name, d.status, d.strategy, d.target_count,
			d.successful_count, d.failed_count, d.progress_percentage,
			d.created_at, d.started_at, d.completed_at
		FROM deployments d
		WHERE 1=1
	`
	
	args := []interface{}{}
	argNum := 1
	
	// Add filters
	if len(statuses) > 0 {
		query += fmt.Sprintf(" AND d.status = ANY($%d)", argNum)
		args = append(args, statuses)
		argNum++
	}
	
	if len(strategies) > 0 {
		query += fmt.Sprintf(" AND d.strategy = ANY($%d)", argNum)
		args = append(args, strategies)
		argNum++
	}
	
	if buildingID != "" {
		query += fmt.Sprintf(" AND $%d = ANY(d.target_buildings)", argNum)
		args = append(args, buildingID)
		argNum++
	}
	
	if since != nil {
		query += fmt.Sprintf(" AND d.created_at >= $%d", argNum)
		args = append(args, *since)
		argNum++
	}
	
	// Add sorting
	validSortFields := map[string]bool{
		"created_at": true,
		"updated_at": true,
		"name":       true,
		"status":     true,
	}
	
	if !validSortFields[sortBy] {
		sortBy = "created_at"
	}
	
	if sortOrder != "asc" && sortOrder != "desc" {
		sortOrder = "desc"
	}
	
	query += fmt.Sprintf(" ORDER BY d.%s %s", sortBy, strings.ToUpper(sortOrder))
	
	// Add pagination
	query += fmt.Sprintf(" LIMIT $%d OFFSET $%d", argNum, argNum+1)
	args = append(args, limit, offset)
	
	return query, args
}

func displayListSummary(ctx context.Context, db *sqlx.DB, since *time.Time) {
	var summary struct {
		Total       int `db:"total"`
		InProgress  int `db:"in_progress"`
		Completed   int `db:"completed"`
		Failed      int `db:"failed"`
		RolledBack  int `db:"rolled_back"`
	}
	
	query := `
		SELECT 
			COUNT(*) as total,
			COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
			COUNT(*) FILTER (WHERE status = 'completed') as completed,
			COUNT(*) FILTER (WHERE status = 'failed') as failed,
			COUNT(*) FILTER (WHERE status = 'rolled_back') as rolled_back
		FROM deployments
		WHERE 1=1
	`
	
	args := []interface{}{}
	if since != nil {
		query += " AND created_at >= $1"
		args = append(args, *since)
	}
	
	err := db.GetContext(ctx, &summary, query, args...)
	if err != nil {
		fmt.Printf("Error fetching summary: %v\n", err)
		return
	}
	
	fmt.Printf("Deployment Summary")
	if since != nil {
		fmt.Printf(" (since %s)", since.Format("2006-01-02"))
	}
	fmt.Printf("\n")
	fmt.Printf("%s\n", strings.Repeat("-", 60))
	fmt.Printf("Total:        %d\n", summary.Total)
	if summary.InProgress > 0 {
		fmt.Printf("In Progress:  %d\n", summary.InProgress)
	}
	fmt.Printf("Completed:    %d\n", summary.Completed)
	if summary.Failed > 0 {
		fmt.Printf("Failed:       %d\n", summary.Failed)
	}
	if summary.RolledBack > 0 {
		fmt.Printf("Rolled Back:  %d\n", summary.RolledBack)
	}
}

func parseDuration(s string) (time.Duration, error) {
	// Support formats like "24h", "7d", "30d"
	if strings.HasSuffix(s, "d") {
		days := strings.TrimSuffix(s, "d")
		var d int
		_, err := fmt.Sscanf(days, "%d", &d)
		if err != nil {
			return 0, err
		}
		return time.Duration(d) * 24 * time.Hour, nil
	}
	
	return time.ParseDuration(s)
}