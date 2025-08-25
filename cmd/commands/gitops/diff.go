package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/arxos/arxos/core/internal/gitops"
	"github.com/arxos/arxos/core/internal/state"
	"github.com/spf13/cobra"
)

var diffCmd = &cobra.Command{
	Use:   "diff [building-id] [ref1] [ref2]",
	Short: "Show differences between states or branches",
	Long: `Display differences between two building states or branches.
	
References can be:
  - Branch names (e.g., main, feature-xyz)
  - State IDs (e.g., abc123...)
  - Special refs: HEAD, HEAD~1, etc.`,
	Args: cobra.MinimumNArgs(1),
	RunE: runDiff,
}

var (
	diffFormat   string
	diffSummary  bool
	diffDetailed bool
	diffHTML     bool
)

func init() {
	diffCmd.Flags().StringVarP(&diffFormat, "format", "f", "text", "Output format (text/json/html)")
	diffCmd.Flags().BoolVar(&diffSummary, "summary", false, "Show summary only")
	diffCmd.Flags().BoolVar(&diffDetailed, "detailed", false, "Show detailed changes")
	diffCmd.Flags().BoolVar(&diffHTML, "html", false, "Generate HTML diff view")
}

func runDiff(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	
	var ref1, ref2 string
	if len(args) == 1 {
		// Diff current branch against main
		ref1 = "main"
		ref2 = "HEAD"
	} else if len(args) == 2 {
		// Diff ref1 against current
		ref1 = args[1]
		ref2 = "HEAD"
	} else {
		ref1 = args[1]
		ref2 = args[2]
	}

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create managers
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	diffViewer := gitops.NewDiffViewer(stateManager)

	ctx := context.Background()

	// Resolve references to state IDs
	state1ID, err := resolveRef(ctx, branchManager, buildingID, ref1)
	if err != nil {
		return fmt.Errorf("failed to resolve %s: %w", ref1, err)
	}

	state2ID, err := resolveRef(ctx, branchManager, buildingID, ref2)
	if err != nil {
		return fmt.Errorf("failed to resolve %s: %w", ref2, err)
	}

	// Generate diff
	diff, err := diffViewer.GenerateDiff(ctx, state1ID, state2ID)
	if err != nil {
		return fmt.Errorf("failed to generate diff: %w", err)
	}

	// Output based on format
	switch diffFormat {
	case "json":
		jsonData, _ := json.MarshalIndent(diff, "", "  ")
		fmt.Printf("%s\n", jsonData)
		
	case "html":
		fmt.Println(diff.HTML)
		
	default: // text
		if diffSummary {
			printDiffSummary(diff)
		} else {
			printDiffText(diff, diffDetailed)
		}
	}

	return nil
}

func resolveRef(ctx context.Context, branchMgr *gitops.BranchManager, buildingID, ref string) (string, error) {
	// Special refs
	if ref == "HEAD" {
		branch, err := branchMgr.GetCurrentBranch(ctx, buildingID)
		if err != nil {
			return "", err
		}
		return branch.HeadStateID, nil
	}
	
	if strings.HasPrefix(ref, "HEAD~") {
		// Would implement parent navigation
		return "", fmt.Errorf("parent navigation not yet implemented")
	}

	// Try as branch name
	branch, err := branchMgr.GetBranch(ctx, buildingID, ref)
	if err == nil {
		return branch.HeadStateID, nil
	}

	// Assume it's a state ID
	return ref, nil
}

func printDiffSummary(diff *gitops.DiffResult) {
	fmt.Println("Changes Summary")
	fmt.Println(strings.Repeat("=", 40))
	
	if diff.Summary.ObjectsAdded > 0 {
		fmt.Printf("  Objects added:    +%d\n", diff.Summary.ObjectsAdded)
	}
	if diff.Summary.ObjectsModified > 0 {
		fmt.Printf("  Objects modified: ~%d\n", diff.Summary.ObjectsModified)
	}
	if diff.Summary.ObjectsRemoved > 0 {
		fmt.Printf("  Objects removed:  -%d\n", diff.Summary.ObjectsRemoved)
	}
	if diff.Summary.SystemsChanged > 0 {
		fmt.Printf("  Systems changed:  %d\n", diff.Summary.SystemsChanged)
	}
	if diff.Summary.PropertiesChanged > 0 {
		fmt.Printf("  Properties:       %d\n", diff.Summary.PropertiesChanged)
	}
	
	fmt.Printf("\nTotal changes: %d\n", diff.Summary.TotalChanges)
}

func printDiffText(diff *gitops.DiffResult, detailed bool) {
	// Print summary first
	printDiffSummary(diff)
	
	// Print object changes
	if len(diff.Objects) > 0 {
		fmt.Printf("\n%s\n", strings.Repeat("=", 40))
		fmt.Println("Object Changes:")
		
		for _, obj := range diff.Objects {
			icon := getDiffIcon(obj.Type)
			fmt.Printf("%s %s (%s)\n", icon, obj.ID, obj.ObjectType)
			
			if detailed && len(obj.Changes) > 0 {
				for _, change := range obj.Changes {
					fmt.Printf("    %s: %v → %v\n",
						change.Field,
						formatDiffValue(change.OldValue),
						formatDiffValue(change.NewValue))
				}
			}
		}
	}
	
	// Print system changes
	if len(diff.Systems) > 0 {
		fmt.Printf("\n%s\n", strings.Repeat("=", 40))
		fmt.Println("System Changes:")
		
		for _, sys := range diff.Systems {
			icon := getDiffIcon(sys.Type)
			fmt.Printf("%s %s\n", icon, sys.SystemID)
			
			if detailed && len(sys.Changes) > 0 {
				for _, change := range sys.Changes {
					fmt.Printf("    %s: %v → %v\n",
						change.Field,
						formatDiffValue(change.OldValue),
						formatDiffValue(change.NewValue))
				}
			}
		}
	}
	
	// Print property changes
	if len(diff.Properties) > 0 {
		fmt.Printf("\n%s\n", strings.Repeat("=", 40))
		fmt.Println("Property Changes:")
		
		for _, prop := range diff.Properties {
			icon := getDiffIcon(prop.Type)
			
			switch prop.Type {
			case "added":
				fmt.Printf("%s %s: %v\n", icon, prop.Key, formatDiffValue(prop.NewValue))
			case "removed":
				fmt.Printf("%s %s: %v\n", icon, prop.Key, formatDiffValue(prop.OldValue))
			case "modified":
				fmt.Printf("%s %s: %v → %v\n", icon, prop.Key,
					formatDiffValue(prop.OldValue),
					formatDiffValue(prop.NewValue))
			}
		}
	}
}

func getDiffIcon(diffType string) string {
	switch diffType {
	case "added":
		return "+"
	case "modified":
		return "~"
	case "removed":
		return "-"
	default:
		return " "
	}
}

func formatDiffValue(v interface{}) string {
	if v == nil {
		return "<null>"
	}
	
	str := fmt.Sprintf("%v", v)
	if len(str) > 50 {
		return str[:47] + "..."
	}
	return str
}