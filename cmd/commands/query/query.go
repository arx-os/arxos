package query

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"
)

// QueryCmd represents the query command category
var QueryCmd = &cobra.Command{
	Use:   "query",
	Short: "Execute AQL queries on ArxObjects",
	Long: `Query ArxObjects using the Arxos Query Language (AQL).
	
Supports SELECT, UPDATE, DELETE operations with spatial and relationship queries.`,
}

func init() {
	// Add subcommands
	QueryCmd.AddCommand(
		enhancedSelectCmd,  // Use enhanced version with ArxObject support
		updateCmd,
		validateCmd,
		historyCmd,
		diffCmd,
		askCmd,
		shellCmd,
		navigateCmd,
		templatesCmd,
	)
}

// SELECT command
var selectCmd = &cobra.Command{
	Use:   "select [query]",
	Short: "Query ArxObjects with SELECT",
	Example: `  arxos query select "* FROM building:hq:floor:3 WHERE type = 'wall'"
  arxos query select "id, type, confidence FROM building:* WHERE confidence < 0.7"`,
	RunE: runSelect,
}

// UPDATE command
var updateCmd = &cobra.Command{
	Use:     "update [query]",
	Short:   "Update ArxObjects properties",
	Example: `  arxos query update "wall_123 SET confidence = 0.95"`,
	RunE:    runUpdate,
}

// VALIDATE command
var validateCmd = &cobra.Command{
	Use:     "validate [object_id]",
	Short:   "Mark object as field-validated",
	Example: `  arxos query validate wall_123 --photo=wall.jpg`,
	RunE:    runValidate,
}

// HISTORY command
var historyCmd = &cobra.Command{
	Use:     "history [object_id]",
	Short:   "View object version history",
	Example: `  arxos query history wall_123`,
	RunE:    runHistory,
}

// DIFF command
var diffCmd = &cobra.Command{
	Use:     "diff [object_id]",
	Short:   "Compare object versions",
	Example: `  arxos query diff wall_123 --from=2024-01-01 --to=2024-01-15`,
	RunE:    runDiff,
}

// Enhanced implementations with result display
func runUpdate(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("update query required")
	}

	// Create mock result for demonstration
	result := &AQLResult{
		Type:    "UPDATE",
		Objects: []interface{}{},
		Count:   0,
		Message: "Update query executed successfully",
		Metadata: map[string]interface{}{
			"rows_affected": 1,
			"query_type":    "UPDATE",
		},
		ExecutedAt: time.Now(),
	}

	// Display results
	display := NewResultDisplay("table", "default")
	return display.DisplayResult(result)
}

func runValidate(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("object ID required")
	}

	objectID := args[0]

	// Create mock result for demonstration
	result := &AQLResult{
		Type:    "VALIDATE",
		Objects: []interface{}{map[string]interface{}{"id": objectID, "status": "validated", "confidence": 0.95}},
		Count:   1,
		Message: fmt.Sprintf("Object %s validated successfully", objectID),
		Metadata: map[string]interface{}{
			"rows_affected": 1,
			"query_type":    "VALIDATE",
		},
		ExecutedAt: time.Now(),
	}

	// Display results
	display := NewResultDisplay("table", "default")
	return display.DisplayResult(result)
}

func runHistory(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("object ID required")
	}

	objectID := args[0]

	// Create mock result for demonstration
	result := &AQLResult{
		Type:    "HISTORY",
		Objects: []interface{}{map[string]interface{}{"id": objectID, "version": "1.0", "change": "initial creation"}},
		Count:   1,
		Message: fmt.Sprintf("History for object %s", objectID),
		Metadata: map[string]interface{}{
			"rows_affected": 1,
			"query_type":    "HISTORY",
		},
		ExecutedAt: time.Now(),
	}

	// Display results
	display := NewResultDisplay("table", "default")
	return display.DisplayResult(result)
}

func runDiff(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("object ID required")
	}

	objectID := args[0]

	// Create mock result for demonstration
	result := &AQLResult{
		Type:    "DIFF",
		Objects: []interface{}{map[string]interface{}{"id": objectID, "change": "property updated", "old_value": "old", "new_value": "new"}},
		Count:   1,
		Message: fmt.Sprintf("Diff for object %s", objectID),
		Metadata: map[string]interface{}{
			"rows_affected": 1,
			"query_type":    "DIFF",
		},
		ExecutedAt: time.Now(),
	}

	// Display results
	display := NewResultDisplay("table", "default")
	return display.DisplayResult(result)
}
