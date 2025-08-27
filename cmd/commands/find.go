package commands

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

// FindCmd represents the find command
var FindCmd = &cobra.Command{
	Use:   "find [query]",
	Short: "Search for building objects using text and filters",
	Long: `Search for building objects using text, filters, and basic queries.

Examples:
  arx find "electrical"                    # Text search for "electrical"
  arx find type:floor                      # Find all floors
  arx find status:active                   # Find active objects
  arx find path:/systems/*                 # Find objects in systems directory
  arx find "hvac" type:system             # Combined text and type filter
  arx find type:hardware                   # Find hardware components
  arx find type:pcb                        # Find PCB designs
  arx find system:hardware                 # Find all hardware objects

Query Syntax:
  Text: "search term"                      # Search in names and descriptions
  Type: type:floor                         # Filter by object type
  Status: status:active                    # Filter by status
  Path: path:/systems/*                    # Filter by path pattern
  Properties: area>1000                   # Filter by property values
  System: system:hardware                  # Filter by system (hardware, electrical, hvac)

Flags:
  --limit: Maximum number of results (default: 50)
  --format: Output format (table, json, csv)`,
	Args: cobra.MaximumNArgs(1),
	RunE: runFind,
}

// FindOptions holds the command options
type FindOptions struct {
	Limit   int    `json:"limit"`
	Format  string `json:"format"`
	Query   string `json:"query"`
}

// runFind executes the find command
func runFind(cmd *cobra.Command, args []string) error {
	// Parse options
	options := &FindOptions{
		Limit:  50,
		Format: "table",
	}

	// Get flags
	if limit, err := cmd.Flags().GetInt("limit"); err == nil {
		options.Limit = limit
	}
	if format, err := cmd.Flags().GetString("format"); err == nil && format != "" {
		options.Format = format
	}

	// Get query from args or use default
	if len(args) > 0 {
		options.Query = args[0]
	} else {
		options.Query = "*" // Default to all objects
	}

	// Find building root
	buildingRoot, err := findBuildingRoot(".")
	if err != nil {
		return fmt.Errorf("not in a building workspace: %w", err)
	}

	// Load session to get building ID
	session, err := loadSession(buildingRoot)
	if err != nil {
		return fmt.Errorf("failed to load session: %w", err)
	}

	// Build or load index
	index, err := GetOrBuildIndex(buildingRoot, session.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to build index: %w", err)
	}

	// Execute search using index
	results, err := executeSimpleSearch(index, options)
	if err != nil {
		return fmt.Errorf("search failed: %w", err)
	}

	// Display results
	if err := displaySimpleResults(results, options); err != nil {
		return fmt.Errorf("failed to display results: %w", err)
	}

	// Show summary
	fmt.Printf("\n🔍 Search completed\n")
	fmt.Printf("📊 Found %d results\n", len(results))

	return nil
}

// executeSimpleSearch performs a basic search using the index
func executeSimpleSearch(index *Index, options *FindOptions) ([]DirectoryEntry, error) {
	var results []DirectoryEntry
	
	// Parse query
	queryType, queryValue := parseSimpleQuery(options.Query)
	
	// Search through all entries
	for _, entries := range index.PathToEntries {
		for _, entry := range entries {
			if matchesSimpleQuery(entry, queryType, queryValue) {
				results = append(results, entry)
				
				// Apply limit
				if len(results) >= options.Limit {
					break
				}
			}
		}
		if len(results) >= options.Limit {
			break
		}
	}
	
	return results, nil
}

// parseSimpleQuery parses a simple query string
func parseSimpleQuery(query string) (string, string) {
	if query == "*" || query == "" {
		return "", ""
	}
	
	if strings.Contains(query, ":") {
		parts := strings.SplitN(query, ":", 2)
		if len(parts) == 2 {
			return strings.ToLower(parts[0]), parts[1]
		}
	}
	
	// Default to text search
	return "text", query
}

// matchesSimpleQuery checks if an entry matches the query
func matchesSimpleQuery(entry DirectoryEntry, queryType, queryValue string) bool {
	if queryType == "" || queryValue == "" {
		return true
	}
	
	switch queryType {
	case "text":
		return strings.Contains(strings.ToLower(entry.Name), strings.ToLower(queryValue)) ||
			   strings.Contains(strings.ToLower(entry.Type), strings.ToLower(queryValue))
	case "type":
		return strings.EqualFold(entry.Type, queryValue)
	case "status":
		if status, exists := entry.Metadata["status"]; exists {
			return strings.EqualFold(fmt.Sprintf("%v", status), queryValue)
		}
		return false
	case "path":
		return strings.Contains(entry.Path, queryValue)
	default:
		// Check metadata
		if value, exists := entry.Metadata[queryType]; exists {
			return strings.EqualFold(fmt.Sprintf("%v", value), queryValue)
		}
		return false
	}
}

// displaySimpleResults displays search results
func displaySimpleResults(results []DirectoryEntry, options *FindOptions) error {
	if len(results) == 0 {
		fmt.Println("No results found.")
		return nil
	}

	switch options.Format {
	case "json":
		return displayJSONResults(results)
	case "csv":
		return displayCSVResults(results)
	case "table":
		fallthrough
	default:
		return displayTableResults(results)
	}
}

// displayTableResults displays results in a formatted table
func displayTableResults(results []DirectoryEntry) error {
	// Print header
	fmt.Printf("\n%-40s %-15s %-30s %s\n", "Name", "Type", "Path", "Metadata")
	fmt.Println(strings.Repeat("-", 100))

	// Print results
	for _, entry := range results {
		name := entry.Name
		if len(name) > 38 {
			name = name[:35] + "..."
		}
		
		path := entry.Path
		if len(path) > 28 {
			path = "..." + path[len(path)-25:]
		}
		
		metadata := formatMetadata(entry.Metadata)
		if len(metadata) > 47 {
			metadata = metadata[:44] + "..."
		}
		
		fmt.Printf("%-40s %-15s %-30s %s\n", name, entry.Type, path, metadata)
	}

	return nil
}

// displayJSONResults displays results in JSON format
func displayJSONResults(results []DirectoryEntry) error {
	// Simple JSON output
	fmt.Println("[")
	for i, entry := range results {
		fmt.Printf("  {\n")
		fmt.Printf("    \"name\": \"%s\",\n", entry.Name)
		fmt.Printf("    \"type\": \"%s\",\n", entry.Type)
		fmt.Printf("    \"path\": \"%s\",\n", entry.Path)
		fmt.Printf("    \"is_dir\": %t\n", entry.IsDir)
		if i < len(results)-1 {
			fmt.Printf("  },\n")
		} else {
			fmt.Printf("  }\n")
		}
	}
	fmt.Println("]")
	return nil
}

// displayCSVResults displays results in CSV format
func displayCSVResults(results []DirectoryEntry) error {
	// CSV header
	fmt.Println("Name,Type,Path,IsDir,Metadata")
	
	// CSV rows
	for _, entry := range results {
		metadata := formatMetadata(entry.Metadata)
		fmt.Printf("\"%s\",\"%s\",\"%s\",%t,\"%s\"\n",
			entry.Name, entry.Type, entry.Path, entry.IsDir, metadata)
	}
	
	return nil
}

// formatMetadata formats metadata for display
func formatMetadata(metadata map[string]interface{}) string {
	if len(metadata) == 0 {
		return ""
	}
	
	parts := make([]string, 0)
	for k, v := range metadata {
		parts = append(parts, fmt.Sprintf("%s=%v", k, v))
	}
	
	return strings.Join(parts, ";")
}

func init() {
	// Add flags
	FindCmd.Flags().IntP("limit", "l", 50, "Maximum number of results")
	FindCmd.Flags().StringP("format", "f", "table", "Output format (table, json, csv)")
}
