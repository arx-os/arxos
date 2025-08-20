// ArxOS CLI - Building Infrastructure as Code
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/arxos/arxos/core/aql"
	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/db"
	"github.com/fatih/color"
)

var (
	green  = color.New(color.FgGreen).SprintFunc()
	yellow = color.New(color.FgYellow).SprintFunc()
	red    = color.New(color.FgRed).SprintFunc()
	blue   = color.New(color.FgBlue).SprintFunc()
	cyan   = color.New(color.FgCyan).SprintFunc()
)

func main() {
	// Initialize database connection
	db.Connect()
	
	// Initialize AQL parser and executor
	parser := aql.NewParser()
	executor := aql.NewExecutor(db.DB, arxobject.NewEngine(10000))
	
	// Print welcome message
	printWelcome()
	
	// Check for command line arguments
	if len(os.Args) > 1 {
		// Execute single command
		query := strings.Join(os.Args[1:], " ")
		executeCommand(parser, executor, query)
		return
	}
	
	// Interactive mode
	scanner := bufio.NewScanner(os.Stdin)
	
	for {
		fmt.Print(cyan("arxos> "))
		
		if !scanner.Scan() {
			break
		}
		
		input := strings.TrimSpace(scanner.Text())
		
		// Handle special commands
		switch strings.ToLower(input) {
		case "exit", "quit", "q":
			fmt.Println("Goodbye!")
			return
		case "help", "?":
			printHelp()
			continue
		case "examples":
			printExamples()
			continue
		case "clear":
			fmt.Print("\033[H\033[2J")
			continue
		}
		
		// Execute AQL query
		executeCommand(parser, executor, input)
	}
}

func printWelcome() {
	fmt.Println(green("╔══════════════════════════════════════════════════════════╗"))
	fmt.Println(green("║                    ArxOS CLI v1.0.0                       ║"))
	fmt.Println(green("║         Building Infrastructure as Code                   ║"))
	fmt.Println(green("╚══════════════════════════════════════════════════════════╝"))
	fmt.Println()
	fmt.Println("Type 'help' for commands, 'examples' for query examples, 'exit' to quit")
	fmt.Println()
}

func printHelp() {
	fmt.Println(yellow("\n=== ArxOS Query Language (AQL) ==="))
	fmt.Println()
	fmt.Println("Query Commands:")
	fmt.Println("  SELECT   - Query ArxObjects")
	fmt.Println("  UPDATE   - Modify ArxObjects")
	fmt.Println("  VALIDATE - Mark objects as field-validated")
	fmt.Println("  HISTORY  - View object change history")
	fmt.Println("  DIFF     - Compare object versions")
	fmt.Println()
	fmt.Println("Special Commands:")
	fmt.Println("  help     - Show this help")
	fmt.Println("  examples - Show example queries")
	fmt.Println("  clear    - Clear screen")
	fmt.Println("  exit     - Exit ArxOS CLI")
	fmt.Println()
	fmt.Println("Operators:")
	fmt.Println("  =, !=, >, <, >=, <=     - Standard comparisons")
	fmt.Println("  LIKE                    - Pattern matching")
	fmt.Println("  IN                      - Value in list")
	fmt.Println("  NEAR                    - Spatial proximity")
	fmt.Println("  WITHIN                  - Spatial boundary")
	fmt.Println("  CONNECTED_TO            - Relationship query")
	fmt.Println()
}

func printExamples() {
	fmt.Println(yellow("\n=== Example Queries ==="))
	fmt.Println()
	
	examples := []struct {
		desc  string
		query string
	}{
		{
			"Find all HVAC units on floor 3:",
			"SELECT * FROM building:headquarters:floor:3 WHERE type = 'hvac'",
		},
		{
			"Find low-confidence walls needing validation:",
			"SELECT id, type, confidence.overall FROM building:* WHERE type = 'wall' AND confidence.overall < 0.7",
		},
		{
			"Find all outlets near position (100, 200) within 50 units:",
			"SELECT * FROM building:* WHERE type = 'outlet' AND geometry NEAR '100,200,50'",
		},
		{
			"Validate a specific wall:",
			"VALIDATE wall_123 WITH photo='wall_photo.jpg'",
		},
		{
			"View history of an object:",
			"HISTORY OF wall_123",
		},
		{
			"Compare versions:",
			"DIFF wall_123 BETWEEN '2024-01-01' AND '2024-01-15'",
		},
		{
			"Find objects connected to main panel:",
			"SELECT * FROM building:* WHERE relationships CONNECTED_TO 'panel_main_01'",
		},
		{
			"Update confidence after field validation:",
			"UPDATE wall_123 SET confidence.position = 0.95 WHERE id = 'wall_123'",
		},
	}
	
	for _, ex := range examples {
		fmt.Printf("%s\n", blue(ex.desc))
		fmt.Printf("  %s\n\n", ex.query)
	}
}

func executeCommand(parser *aql.Parser, executor *aql.Executor, input string) {
	// Parse the query
	query, err := parser.Parse(input)
	if err != nil {
		fmt.Printf("%s %s\n", red("Parse error:"), err)
		return
	}
	
	// Execute the query
	ctx := context.Background()
	result, err := executor.Execute(ctx, query)
	if err != nil {
		fmt.Printf("%s %s\n", red("Execution error:"), err)
		return
	}
	
	// Display results
	displayResults(result)
}

func displayResults(result *aql.Result) {
	switch result.Type {
	case aql.SELECT:
		displaySelectResults(result)
	case aql.UPDATE:
		fmt.Printf("%s %s\n", green("✓"), result.Message)
	case aql.VALIDATE:
		displayValidateResults(result)
	case aql.HISTORY:
		displayHistoryResults(result)
	case aql.DIFF:
		displayDiffResults(result)
	}
	
	// Show execution time
	fmt.Printf("\n%s in %v\n", 
		yellow(fmt.Sprintf("%d results", result.Count)),
		result.ExecutedAt.Sub(result.ExecutedAt).Round(time.Millisecond))
}

func displaySelectResults(result *aql.Result) {
	if len(result.Objects) == 0 {
		fmt.Println(yellow("No objects found"))
		return
	}
	
	// Create table header
	fmt.Println("\n┌────────────────────┬──────────────┬────────────┬────────────┐")
	fmt.Printf("│ %-18s │ %-12s │ %-10s │ %-10s │\n", "ID", "Type", "Confidence", "Validated")
	fmt.Println("├────────────────────┼──────────────┼────────────┼────────────┤")
	
	// Display each object
	for _, obj := range result.Objects {
		validated := "No"
		if obj.Metadata.Validated {
			validated = green("Yes")
		}
		
		confColor := getConfidenceColor(obj.Confidence.Overall)
		confidence := fmt.Sprintf("%.2f", obj.Confidence.Overall)
		
		fmt.Printf("│ %-18s │ %-12s │ %s%% │ %-10s │\n",
			truncate(obj.ID, 18),
			truncate(string(obj.Type), 12),
			confColor(fmt.Sprintf("%-9s", confidence)),
			validated)
	}
	
	fmt.Println("└────────────────────┴──────────────┴────────────┴────────────┘")
}

func displayValidateResults(result *aql.Result) {
	if len(result.Objects) > 0 {
		obj := result.Objects[0]
		fmt.Printf("\n%s Validated object %s\n", green("✓"), obj.ID)
		fmt.Printf("  New confidence: %s\n", 
			getConfidenceColor(obj.Confidence.Overall)(fmt.Sprintf("%.2f%%", obj.Confidence.Overall*100)))
		
		if propagated, ok := result.Metadata["propagated_to"].(int); ok && propagated > 0 {
			fmt.Printf("  Confidence propagated to %d related objects\n", propagated)
		}
	}
}

func displayHistoryResults(result *aql.Result) {
	fmt.Printf("\n%s Version History (%d versions)\n", blue("📜"), result.Count)
	fmt.Println("─────────────────────────────────────────")
	
	for i, obj := range result.Objects {
		fmt.Printf("Version %d: %s\n", result.Count-i, obj.Metadata.LastModified.Format("2006-01-02 15:04:05"))
		fmt.Printf("  Confidence: %.2f%% | Validated: %v\n", 
			obj.Confidence.Overall*100, obj.Metadata.Validated)
	}
}

func displayDiffResults(result *aql.Result) {
	fmt.Printf("\n%s Diff Results\n", blue("🔄"))
	fmt.Println("─────────────────────────────────────────")
	
	if changes, ok := result.Metadata["changes"].(map[string]interface{}); ok {
		for field, change := range changes {
			fmt.Printf("  %s: %v\n", field, change)
		}
	}
}

func getConfidenceColor(confidence float32) func(string) string {
	switch {
	case confidence >= 0.8:
		return green
	case confidence >= 0.5:
		return yellow
	default:
		return red
	}
}

func truncate(s string, length int) string {
	if len(s) <= length {
		return s
	}
	return s[:length-3] + "..."
}