package state

import (
	"github.com/spf13/cobra"
)

// StateCmd represents the state command group
var StateCmd = &cobra.Command{
	Use:   "state",
	Short: "Manage building states and version control",
	Long: `The state command group provides Git-like version control for building configurations.
	
Capture snapshots of building state, compare versions, create branches, and restore
previous configurations. This enables Infrastructure-as-Code practices for physical buildings.

Examples:
  # Capture current state
  arxos state capture building-123 -m "After HVAC upgrade"
  
  # List state history
  arxos state list building-123
  
  # Compare two states
  arxos state diff v1.0.0 v1.0.1
  
  # Restore previous state
  arxos state restore building-123 v1.0.0
  
  # Create and manage branches
  arxos state branch create building-123 feature/new-hvac
  arxos state branch list building-123`,
}

func init() {
	// Add subcommands
	StateCmd.AddCommand(captureCmd)
	StateCmd.AddCommand(listCmd)
	StateCmd.AddCommand(diffCmd)
	StateCmd.AddCommand(restoreCmd)
	StateCmd.AddCommand(branchCmd)
	
	// Global flags for all state commands
	StateCmd.PersistentFlags().Bool("json", false, "Output in JSON format")
	StateCmd.PersistentFlags().String("config", "", "Config file path")
}