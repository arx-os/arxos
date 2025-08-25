package deploy

import (
	"github.com/spf13/cobra"
)

// DeployCmd represents the deploy command group
var DeployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "Manage configuration deployments to building portfolios",
	Long: `The deploy command group enables pushing configurations across building portfolios
using various deployment strategies (immediate, canary, rolling, blue-green).

Deploy building states, monitor progress, handle rollbacks, and ensure safe configuration
updates across your entire building infrastructure.

Examples:
  # Create a new deployment
  arxos deploy create --source-state abc123 --targets "SELECT * WHERE type='office'" --strategy canary
  
  # Check deployment status
  arxos deploy status deployment-456
  
  # Rollback a deployment
  arxos deploy rollback deployment-456 --reason "Performance degradation"
  
  # List recent deployments
  arxos deploy list --status in_progress`,
}

func init() {
	// Add subcommands
	DeployCmd.AddCommand(createCmd)
	DeployCmd.AddCommand(statusCmd)
	DeployCmd.AddCommand(listCmd)
	DeployCmd.AddCommand(rollbackCmd)
	DeployCmd.AddCommand(validateCmd)
	DeployCmd.AddCommand(historyCmd)
	
	// Global flags for all deploy commands
	DeployCmd.PersistentFlags().Bool("json", false, "Output in JSON format")
	DeployCmd.PersistentFlags().String("config", "", "Config file path")
}