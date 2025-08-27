package support

import (
	"fmt"
	"strings"
	"time"
	
	"github.com/spf13/cobra"
	// "github.com/arxos/arxos/cmd/client"
	// "github.com/arxos/arxos/cmd/display"
)

var (
	jobStatus   string
	jobLimit    int
	fromStep    string
	memoryLimit string
	cpuLimit    string
)

func init() {
	jobsCmd.Flags().StringVar(&jobStatus, "status", "", "filter by status (running|failed|stuck|completed)")
	jobsCmd.Flags().StringVar(&timeRange, "last", "1h", "time range (1h, 24h, 7d)")
	jobsCmd.Flags().IntVar(&jobLimit, "limit", 20, "number of jobs to show")
	
	retryJobCmd.Flags().StringVar(&fromStep, "from-step", "", "retry from specific step")
	retryJobCmd.Flags().StringVar(&memoryLimit, "memory", "", "override memory limit (e.g., 8G)")
	retryJobCmd.Flags().StringVar(&cpuLimit, "cpu", "", "override CPU limit (e.g., 4)")
}

func runJobs(cmd *cobra.Command, args []string) error {
	logSupportAction("LIST_JOBS", fmt.Sprintf("status=%s, last=%s", jobStatus, timeRange))
	
	if dryRun {
		fmt.Println("[DRY RUN] Would list jobs with filters:")
		fmt.Printf("  Status: %s\n", jobStatus)
		fmt.Printf("  Time range: %s\n", timeRange)
		return nil
	}
	
	// Get jobs from backend
	c := client.GetSupportClient()
	jobs, err := c.GetJobs(jobStatus, timeRange, jobLimit)
	if err != nil {
		return fmt.Errorf("failed to get jobs: %w", err)
	}
	
	// Display jobs table
	table := display.NewTableDisplay()
	table.SetHeaders("Job ID", "User", "Type", "Status", "Duration", "Error")
	
	for _, job := range jobs {
		status := job.Status
		if job.Status == "failed" {
			status = display.Red(job.Status)
		} else if job.Status == "running" {
			status = display.Green(job.Status)
		}
		
		table.AddRow(
			job.ID,
			truncate(job.User, 20),
			job.Type,
			status,
			job.Duration,  // Already a string
			truncate(job.Error, 30),
		)
	}
	
	table.Render()
	
	// Show summary
	fmt.Printf("\nTotal: %d jobs\n", len(jobs))
	
	// Show problematic jobs
	if jobStatus == "failed" || jobStatus == "" {
		failedCount := 0
		for _, job := range jobs {
			if job.Status == "failed" {
				failedCount++
			}
		}
		if failedCount > 0 {
			fmt.Printf("\n%s %d failed jobs need attention\n", 
				display.Yellow("⚠"), failedCount)
			fmt.Println("Use 'arxos support job-inspect [job-id]' for details")
		}
	}
	
	return nil
}

func runJobInspect(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("job ID required")
	}
	
	jobID := args[0]
	logSupportAction("INSPECT_JOB", jobID)
	
	if dryRun {
		fmt.Printf("[DRY RUN] Would inspect job: %s\n", jobID)
		return nil
	}
	
	c := client.GetSupportClient()
	job, err := c.GetJobDetails(jobID)
	if err != nil {
		return fmt.Errorf("failed to get job details: %w", err)
	}
	
	// Display job details
	fmt.Printf("\n%s Job Details: %s\n", display.Blue("📋"), jobID)
	fmt.Println(strings.Repeat("─", 50))
	
	fmt.Printf("User:          %s\n", job.Job.User)
	fmt.Printf("Type:          %s\n", job.Job.Type)
	fmt.Printf("Status:        %s\n", colorizeStatus(job.Job.Status))
	fmt.Printf("Started:       N/A\n")  // TODO: Add StartTime to Job struct
	fmt.Printf("Duration:      %s\n", job.Job.Duration)
	fmt.Printf("Input File:    N/A\n")  // TODO: Add InputFile to Job struct
	
	// Show pipeline steps
	fmt.Printf("\n%s Pipeline Status:\n", display.Blue("🔄"))
	for _, step := range job.Pipeline {
		icon := "⏸"
		if step.Status == "completed" {
			icon = "✅"
		} else if step.Status == "failed" {
			icon = "❌"
		} else if step.Status == "running" {
			icon = "🔄"
		}
		
		fmt.Printf("  %s %s: %s", icon, step.Name, step.Status)
		if step.Duration != "" && step.Duration != "0" {
			fmt.Printf(" (%s)", step.Duration)
		}
		if step.Error != "" {
			fmt.Printf("\n     Error: %s", display.Red(step.Error))
		}
		fmt.Println()
	}
	
	// Show resource usage
	if verbose {
		fmt.Printf("\n%s Resource Usage:\n", display.Blue("📊"))
		// TODO: Add resource usage fields to JobDetails
		fmt.Printf("  Memory: N/A\n")
		fmt.Printf("  CPU: N/A\n")
		fmt.Printf("  Disk I/O: N/A\n")
	}
	
	// Show error details if failed
	if job.Job.Status == "failed" && job.Job.Error != "" {
		fmt.Printf("\n%s Error Details:\n", display.Red("❌"))
		fmt.Println(job.Job.Error)
		
		// Suggest fixes
		suggestions := getSuggestionsForError(job.Job.Error)
		if len(suggestions) > 0 {
			fmt.Printf("\n%s Suggested Actions:\n", display.Yellow("💡"))
			for i, suggestion := range suggestions {
				fmt.Printf("  %d. %s\n", i+1, suggestion)
			}
		}
	}
	
	return nil
}

func runRetryJob(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("job ID required")
	}
	
	jobID := args[0]
	logSupportAction("RETRY_JOB", fmt.Sprintf("%s from_step=%s", jobID, fromStep))
	
	if dryRun {
		fmt.Printf("[DRY RUN] Would retry job: %s\n", jobID)
		if fromStep != "" {
			fmt.Printf("  From step: %s\n", fromStep)
		}
		if memoryLimit != "" {
			fmt.Printf("  Memory override: %s\n", memoryLimit)
		}
		return nil
	}
	
	// Confirm action
	if !forceFlag {
		fmt.Printf("Retry job %s? This will reprocess data.\n", jobID)
		fmt.Print("Type 'yes' to continue: ")
		var confirm string
		fmt.Scanln(&confirm)
		if confirm != "yes" {
			fmt.Println("Cancelled")
			return nil
		}
	}
	
	c := client.GetSupportClient()
	
	// Build retry options
	options := client.RetryOptions{
		FromStep:    fromStep,
		MemoryLimit: memoryLimit,
		CPULimit:    cpuLimit,
	}
	
	// Start retry
	fmt.Printf("Retrying job %s...\n", jobID)
	err := c.RetryJob(jobID, options)
	if err != nil {
		return fmt.Errorf("failed to retry job: %w", err)
	}
	
	fmt.Printf("%s Job retry started successfully\n", display.Green("✅"))
	fmt.Printf("New job ID: %s\n", jobID)  // TODO: Return new job ID from RetryJob
	fmt.Printf("\nMonitor progress:\n")
	fmt.Printf("  arxos support job-inspect %s --watch\n", jobID)
	
	return nil
}

func runKillProcess(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("process ID required")
	}
	
	processID := args[0]
	logSupportAction("KILL_PROCESS", processID)
	
	if dryRun {
		fmt.Printf("[DRY RUN] Would kill process: %s\n", processID)
		return nil
	}
	
	// Extra confirmation for destructive action
	if !forceFlag {
		fmt.Printf("%s Kill process %s? This may cause data loss.\n", 
			display.Red("⚠"), processID)
		fmt.Print("Type the process ID to confirm: ")
		var confirm string
		fmt.Scanln(&confirm)
		if confirm != processID {
			fmt.Println("Cancelled")
			return nil
		}
	}
	
	c := client.GetSupportClient()
	// TODO: Parse user and process type from processID or add flags
	err := c.KillProcess("", processID)  // Empty user for now
	if err != nil {
		return fmt.Errorf("failed to kill process: %w", err)
	}
	
	fmt.Printf("%s Process %s terminated\n", display.Green("✅"), processID)
	
	return nil
}

// Helper functions

func colorizeStatus(status string) string {
	switch status {
	case "completed":
		return display.Green(status)
	case "failed":
		return display.Red(status)
	case "running":
		return display.Blue(status)
	case "stuck":
		return display.Yellow(status)
	default:
		return status
	}
}

func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%.1fs", d.Seconds())
	} else if d < time.Hour {
		return fmt.Sprintf("%.1fm", d.Minutes())
	}
	return fmt.Sprintf("%.1fh", d.Hours())
}

func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-3] + "..."
}

func getSuggestionsForError(errorDetails string) []string {
	suggestions := []string{}
	
	// Pattern match common errors
	if strings.Contains(errorDetails, "OOM") || strings.Contains(errorDetails, "memory") {
		suggestions = append(suggestions, "Increase memory limit: arxos support retry-job --memory=16G")
	}
	if strings.Contains(errorDetails, "timeout") {
		suggestions = append(suggestions, "Increase timeout or split into smaller chunks")
	}
	if strings.Contains(errorDetails, "confidence") {
		suggestions = append(suggestions, "Lower confidence threshold or validate manually")
	}
	
	return suggestions
}