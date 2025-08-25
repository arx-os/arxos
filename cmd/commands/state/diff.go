package state

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/arxos/core/internal/state"
)

var diffCmd = &cobra.Command{
	Use:   "diff [state-a] [state-b]",
	Short: "Compare two building states",
	Long: `Compare two building states and show the differences between them.
States can be specified by ID or by version number.

Examples:
  arxos state diff v1.0.0 v1.0.1
  arxos state diff abc123 def456
  arxos state diff HEAD~1 HEAD`,
	Args: cobra.ExactArgs(2),
	RunE: runDiff,
}

var (
	diffFormat   string
	diffSummary  bool
	diffDetailed bool
	diffSystems  []string
)

func init() {
	diffCmd.Flags().StringVarP(&diffFormat, "format", "f", "text", "Output format (text, json, changelog)")
	diffCmd.Flags().BoolVarP(&diffSummary, "summary", "s", false, "Show summary only")
	diffCmd.Flags().BoolVarP(&diffDetailed, "detailed", "d", false, "Show detailed changes")
	diffCmd.Flags().StringSliceVar(&diffSystems, "systems", []string{}, "Filter by system (hvac, electrical, plumbing, security, fire)")
}

func runDiff(cmd *cobra.Command, args []string) error {
	stateA := args[0]
	stateB := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create diff engine
	stateManager := state.NewManager(db)
	diffEngine := state.NewDiffEngine(db, stateManager)

	ctx := context.Background()

	// TODO: Resolve state identifiers (version -> ID)
	// For now, assume IDs are provided
	stateAID := stateA
	stateBID := stateB

	// Compare states
	fmt.Printf("Comparing states...\n")
	diff, err := diffEngine.CompareStates(ctx, stateAID, stateBID)
	if err != nil {
		return fmt.Errorf("failed to compare states: %w", err)
	}

	// Output based on format
	switch diffFormat {
	case "json":
		return outputDiffJSON(diff)
	case "changelog":
		return outputDiffChangelog(diffEngine, ctx, diff)
	default:
		return outputDiffText(diff)
	}
}

func outputDiffJSON(diff *state.StateDiff) error {
	jsonData, err := json.MarshalIndent(diff, "", "  ")
	if err != nil {
		return err
	}
	fmt.Printf("%s\n", jsonData)
	return nil
}

func outputDiffChangelog(engine *state.DiffEngine, ctx context.Context, diff *state.StateDiff) error {
	changelog := engine.GenerateChangeLog(ctx, diff)
	fmt.Print(changelog)
	return nil
}

func outputDiffText(diff *state.StateDiff) error {
	// Header
	fmt.Printf("\nState Comparison\n")
	fmt.Printf("%s\n", strings.Repeat("=", 60))
	fmt.Printf("From: v%s (%s)\n", diff.FromVersion, diff.FromStateID[:8])
	fmt.Printf("To:   v%s (%s)\n", diff.ToVersion, diff.ToStateID[:8])
	fmt.Printf("\n")

	// Summary
	fmt.Printf("Summary\n")
	fmt.Printf("%s\n", strings.Repeat("-", 40))
	fmt.Printf("Total Changes:    %d\n", diff.Summary.TotalChanges)
	fmt.Printf("Severity:         %s\n", diff.Summary.SeverityLevel)
	if len(diff.Summary.SystemsChanged) > 0 {
		fmt.Printf("Systems Changed:  %s\n", strings.Join(diff.Summary.SystemsChanged, ", "))
	}
	fmt.Printf("\n")

	if diffSummary {
		// Show only summary
		fmt.Printf("ArxObjects:\n")
		fmt.Printf("  Added:    %d\n", diff.Summary.ArxObjectsAdded)
		fmt.Printf("  Modified: %d\n", diff.Summary.ArxObjectsModified)
		fmt.Printf("  Removed:  %d\n", diff.Summary.ArxObjectsRemoved)
		return nil
	}

	// ArxObject Changes
	if diff.Summary.ArxObjectsAdded > 0 || diff.Summary.ArxObjectsModified > 0 || diff.Summary.ArxObjectsRemoved > 0 {
		fmt.Printf("ArxObject Changes\n")
		fmt.Printf("%s\n", strings.Repeat("-", 40))

		if len(diff.ArxObjectChanges.Added) > 0 {
			fmt.Printf("\n  Added (%d):\n", len(diff.ArxObjectChanges.Added))
			for _, obj := range diff.ArxObjectChanges.Added {
				fmt.Printf("    + %s (Type: %s)\n", obj.ID, obj.Type)
				if diffDetailed && len(obj.Fields) > 0 {
					for _, field := range obj.Fields {
						fmt.Printf("        %s: %v\n", field.Field, field.NewValue)
					}
				}
			}
		}

		if len(diff.ArxObjectChanges.Modified) > 0 {
			fmt.Printf("\n  Modified (%d):\n", len(diff.ArxObjectChanges.Modified))
			for _, obj := range diff.ArxObjectChanges.Modified {
				fmt.Printf("    ~ %s (Type: %s)\n", obj.ID, obj.Type)
				if diffDetailed && len(obj.Fields) > 0 {
					for _, field := range obj.Fields {
						fmt.Printf("        %s: %v → %v\n", field.Field, field.OldValue, field.NewValue)
					}
				}
			}
		}

		if len(diff.ArxObjectChanges.Removed) > 0 {
			fmt.Printf("\n  Removed (%d):\n", len(diff.ArxObjectChanges.Removed))
			for _, obj := range diff.ArxObjectChanges.Removed {
				fmt.Printf("    - %s (Type: %s)\n", obj.ID, obj.Type)
			}
		}
		fmt.Printf("\n")
	}

	// System Changes
	if hasSystemChanges(&diff.SystemChanges) {
		fmt.Printf("System Changes\n")
		fmt.Printf("%s\n", strings.Repeat("-", 40))

		outputSystemChanges("HVAC", diff.SystemChanges.HVAC)
		outputSystemChanges("Electrical", diff.SystemChanges.Electrical)
		outputSystemChanges("Plumbing", diff.SystemChanges.Plumbing)
		outputSystemChanges("Security", diff.SystemChanges.Security)
		outputSystemChanges("Fire", diff.SystemChanges.Fire)
	}

	// Metric Changes
	if hasMetricChanges(&diff.MetricChanges) {
		fmt.Printf("Performance Metrics\n")
		fmt.Printf("%s\n", strings.Repeat("-", 40))

		if diff.MetricChanges.EnergyUsage != nil {
			m := diff.MetricChanges.EnergyUsage
			fmt.Printf("  Energy Usage: %.2f → %.2f kWh (%.1f%%)\n",
				m.OldValue, m.NewValue, m.PercentChange)
		}

		if diff.MetricChanges.OccupancyRate != nil {
			m := diff.MetricChanges.OccupancyRate
			fmt.Printf("  Occupancy Rate: %.1f%% → %.1f%%\n",
				m.OldValue*100, m.NewValue*100)
		}

		if diff.MetricChanges.ResponseTime != nil {
			m := diff.MetricChanges.ResponseTime
			fmt.Printf("  Response Time: %.0fms → %.0fms\n",
				m.OldValue, m.NewValue)
		}
		fmt.Printf("\n")
	}

	// Compliance Changes
	if hasComplianceChanges(&diff.ComplianceChanges) {
		fmt.Printf("Compliance Changes\n")
		fmt.Printf("%s\n", strings.Repeat("-", 40))

		for _, change := range diff.ComplianceChanges.StatusChanges {
			fmt.Printf("  %s: %s → %s\n", change.Regulation, change.OldStatus, change.NewStatus)
		}

		if len(diff.ComplianceChanges.NewViolations) > 0 {
			fmt.Printf("  New Violations: %s\n", strings.Join(diff.ComplianceChanges.NewViolations, ", "))
		}

		if len(diff.ComplianceChanges.ResolvedViolations) > 0 {
			fmt.Printf("  Resolved: %s\n", strings.Join(diff.ComplianceChanges.ResolvedViolations, ", "))
		}
		fmt.Printf("\n")
	}

	// Footer
	fmt.Printf("Calculation Time: %dms\n", diff.CalculationTimeMs)

	return nil
}

func outputSystemChanges(system string, changes []state.SystemChange) {
	if len(changes) == 0 {
		return
	}

	fmt.Printf("\n  %s:\n", system)
	for _, change := range changes {
		impactIcon := ""
		switch change.Impact {
		case "high":
			impactIcon = "⚠"
		case "medium":
			impactIcon = "•"
		default:
			impactIcon = "·"
		}
		fmt.Printf("    %s %s: %v → %v\n",
			impactIcon, change.Parameter, change.OldValue, change.NewValue)
		if diffDetailed && change.Description != "" {
			fmt.Printf("        %s\n", change.Description)
		}
	}
}

func hasSystemChanges(s *state.SystemDiff) bool {
	return len(s.HVAC) > 0 || len(s.Electrical) > 0 || len(s.Plumbing) > 0 ||
		len(s.Security) > 0 || len(s.Fire) > 0
}

func hasMetricChanges(m *state.MetricDiff) bool {
	return m.EnergyUsage != nil || m.OccupancyRate != nil || m.ResponseTime != nil
}

func hasComplianceChanges(c *state.ComplianceDiff) bool {
	return len(c.StatusChanges) > 0 || len(c.NewViolations) > 0 || len(c.ResolvedViolations) > 0
}