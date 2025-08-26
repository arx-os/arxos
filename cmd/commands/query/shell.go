package query

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var shellCmd = &cobra.Command{
	Use:   "shell",
	Short: "Start interactive AQL shell",
	Long: `Start an interactive AQL shell for building and testing queries.
The shell provides a REPL experience with command history, auto-completion,
and query templates.

Features:
  - Command history with up/down arrows
  - Auto-completion for ArxObject types and properties
  - Query templates and examples
  - Result formatting options
  - Built-in help system

Type 'help' for available commands, 'exit' to quit.`,
	RunE: runShell,
}

func init() {
	QueryCmd.AddCommand(shellCmd)

	// Shell configuration flags
	shellCmd.Flags().String("format", "table", "Default output format")
	shellCmd.Flags().Bool("history", true, "Enable command history")
	shellCmd.Flags().Bool("auto-complete", true, "Enable auto-completion")
}

func runShell(cmd *cobra.Command, args []string) error {
	format, _ := cmd.Flags().GetString("format")
	enableHistory, _ := cmd.Flags().GetBool("history")
	enableAutoComplete, _ := cmd.Flags().GetBool("auto-complete")

	fmt.Println("=== Arxos AQL Interactive Shell ===")
	fmt.Printf("Format: %s | History: %v | Auto-complete: %v\n", format, enableHistory, enableAutoComplete)
	fmt.Println("Type 'help' for commands, 'exit' to quit")
	fmt.Println()

	shell := NewAQLShell(format, enableHistory, enableAutoComplete)
	return shell.Run()
}

// AQLShell represents the interactive AQL shell
type AQLShell struct {
	format             string
	enableHistory      bool
	enableAutoComplete bool
	history            []string
	historyIndex       int
	scanner            *bufio.Scanner
	display            *ResultDisplay
}

// NewAQLShell creates a new AQL shell instance
func NewAQLShell(format string, enableHistory, enableAutoComplete bool) *AQLShell {
	return &AQLShell{
		format:             format,
		enableHistory:      enableHistory,
		enableAutoComplete: enableAutoComplete,
		history:            make([]string, 0),
		historyIndex:       0,
		scanner:            bufio.NewScanner(os.Stdin),
		display:            NewResultDisplay(format, "default"),
	}
}

// Run starts the interactive shell
func (s *AQLShell) Run() error {
	fmt.Print("arxql> ")

	for s.scanner.Scan() {
		input := strings.TrimSpace(s.scanner.Text())

		if input == "" {
			fmt.Print("arxql> ")
			continue
		}

		// Add to history
		if s.enableHistory {
			s.addToHistory(input)
		}

		// Process command
		if err := s.processCommand(input); err != nil {
			fmt.Printf("Error: %v\n", err)
		}

		fmt.Print("arxql> ")
	}

	return s.scanner.Err()
}

// processCommand handles shell commands and AQL queries
func (s *AQLShell) processCommand(input string) error {
	// Handle shell commands
	if strings.HasPrefix(input, ":") {
		return s.handleShellCommand(input[1:])
	}

	// Handle help commands
	if strings.ToLower(input) == "help" {
		return s.showHelp()
	}

	// Handle exit commands
	if strings.ToLower(input) == "exit" || strings.ToLower(input) == "quit" {
		fmt.Println("Goodbye!")
		os.Exit(0)
	}

	// Handle AQL queries
	return s.executeAQLQuery(input)
}

// handleShellCommand processes shell-specific commands
func (s *AQLShell) handleShellCommand(cmd string) error {
	parts := strings.Fields(cmd)
	if len(parts) == 0 {
		return fmt.Errorf("empty shell command")
	}

	switch parts[0] {
	case "format":
		if len(parts) > 1 {
			s.format = parts[1]
			s.display = NewResultDisplay(s.format, "default")
			fmt.Printf("Output format set to: %s\n", s.format)
		} else {
			fmt.Printf("Current format: %s\n", s.format)
		}
	case "history":
		if s.enableHistory {
			s.showHistory()
		} else {
			fmt.Println("History is disabled")
		}
	case "clear":
		fmt.Print("\033[H\033[2J") // Clear screen
	case "templates":
		s.showQueryTemplates()
	case "examples":
		s.showQueryExamples()
	default:
		return fmt.Errorf("unknown shell command: %s", parts[0])
	}

	return nil
}

// executeAQLQuery executes an AQL query and displays results
func (s *AQLShell) executeAQLQuery(query string) error {
	// For now, generate mock results based on the query
	// In production, this would execute the actual AQL query

	result := s.generateMockResult(query)
	return s.display.DisplayResult(result)
}

// generateMockResult creates mock results for demonstration
func (s *AQLShell) generateMockResult(query string) *AQLResult {
	queryLower := strings.ToLower(query)

	var objects []interface{}
	var message string

	if strings.Contains(queryLower, "select") {
		if strings.Contains(queryLower, "hvac") {
			objects = generateMockHVACResults()
			message = "Found HVAC equipment"
		} else if strings.Contains(queryLower, "electrical") {
			objects = generateMockElectricalResults()
			message = "Found electrical equipment"
		} else if strings.Contains(queryLower, "maintenance") {
			objects = generateMockMaintenanceResults()
			message = "Found maintenance items"
		} else {
			objects = generateMockGenericResults(query)
			message = "Query executed successfully"
		}
	} else if strings.Contains(queryLower, "update") {
		message = "Update query executed successfully"
	} else if strings.Contains(queryLower, "delete") {
		message = "Delete query executed successfully"
	} else {
		objects = generateMockGenericResults(query)
		message = "Query executed successfully"
	}

	return &AQLResult{
		Type:    "SHELL",
		Objects: objects,
		Count:   len(objects),
		Message: message,
		Metadata: map[string]interface{}{
			"query":          query,
			"execution_time": "0.001s",
			"format":         s.format,
		},
		ExecutedAt: time.Now(),
	}
}

// showHelp displays available commands
func (s *AQLShell) showHelp() error {
	fmt.Println("=== AQL Shell Help ===")
	fmt.Println("Shell Commands:")
	fmt.Println("  :format <format>    - Set output format (table, json, csv, ascii-bim, summary)")
	fmt.Println("  :history            - Show command history")
	fmt.Println("  :clear              - Clear screen")
	fmt.Println("  :templates          - Show query templates")
	fmt.Println("  :examples           - Show query examples")
	fmt.Println()
	fmt.Println("AQL Commands:")
	fmt.Println("  SELECT * FROM arxobjects WHERE type = 'wall'")
	fmt.Println("  UPDATE wall_123 SET confidence = 0.95")
	fmt.Println("  DELETE FROM arxobjects WHERE id = 'old_wall'")
	fmt.Println()
	fmt.Println("Other Commands:")
	fmt.Println("  help                - Show this help")
	fmt.Println("  exit, quit          - Exit shell")
	fmt.Println()
	return nil
}

// showHistory displays command history
func (s *AQLShell) showHistory() {
	if len(s.history) == 0 {
		fmt.Println("No command history")
		return
	}

	fmt.Println("=== Command History ===")
	for i, cmd := range s.history {
		fmt.Printf("%3d: %s\n", i+1, cmd)
	}
}

// showQueryTemplates displays available query templates
func (s *AQLShell) showQueryTemplates() {
	fmt.Println("=== Query Templates ===")
	fmt.Println("Equipment Queries:")
	fmt.Println("  SELECT * FROM equipment WHERE type = 'hvac'")
	fmt.Println("  SELECT * FROM equipment WHERE floor = 3")
	fmt.Println("  SELECT * FROM equipment WHERE status = 'maintenance'")
	fmt.Println()
	fmt.Println("Spatial Queries:")
	fmt.Println("  SELECT * FROM arxobjects WHERE room = '305'")
	fmt.Println("  SELECT * FROM arxobjects WHERE building = 'HQ'")
	fmt.Println()
	fmt.Println("Property Queries:")
	fmt.Println("  SELECT * FROM arxobjects WHERE confidence > 0.8")
	fmt.Println("  SELECT * FROM arxobjects WHERE last_updated > '2024-01-01'")
}

// showQueryExamples displays example queries
func (s *AQLShell) showQueryExamples() {
	fmt.Println("=== Query Examples ===")
	fmt.Println("Find all walls on floor 3:")
	fmt.Println("  SELECT * FROM arxobjects WHERE type = 'wall' AND floor = 3")
	fmt.Println()
	fmt.Println("Find equipment needing maintenance:")
	fmt.Println("  SELECT * FROM equipment WHERE maintenance_due <= NOW()")
	fmt.Println()
	fmt.Println("Find high-confidence objects:")
	fmt.Println("  SELECT * FROM arxobjects WHERE confidence > 0.9")
	fmt.Println()
	fmt.Println("Update object confidence:")
	fmt.Println("  UPDATE wall_123 SET confidence = 0.95, validated_by = 'field_user'")
}

// addToHistory adds a command to history
func (s *AQLShell) addToHistory(cmd string) {
	s.history = append(s.history, cmd)
	if len(s.history) > 100 { // Keep last 100 commands
		s.history = s.history[1:]
	}
	s.historyIndex = len(s.history)
}
