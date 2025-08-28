package commands

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/arxos/arxos/cmd/navigation"
	"github.com/spf13/cobra"
)

// FindCmd searches for components in the building
var FindCmd = &cobra.Command{
	Use:   "find [path] [options]",
	Short: "Find building components matching criteria",
	Long: `Search for components in the building filesystem that match
specified criteria. Supports searching by type, name, and properties.

Examples:
  arxos find / -type outlet                           # Find all outlets
  arxos find /electrical -type outlet -load ">15A"    # Outlets with high load
  arxos find / -name "*panel*"                        # Find by name pattern
  arxos find /floors -type room -area ">300"          # Large rooms
  arxos find / -confidence "<0.5"                     # Low confidence items`,
	RunE: runFind,
}

func init() {
	FindCmd.Flags().StringP("type", "t", "", "Component type (outlet, panel, circuit, etc)")
	FindCmd.Flags().StringP("name", "n", "", "Name pattern (supports wildcards)")
	FindCmd.Flags().String("load", "", "Load filter (e.g., '>15A', '<10A')")
	FindCmd.Flags().String("voltage", "", "Voltage filter (e.g., '120V', '240V')")
	FindCmd.Flags().String("confidence", "", "Confidence filter (e.g., '<0.5', '>0.8')")
	FindCmd.Flags().String("status", "", "Status filter (active, inactive, fault)")
	FindCmd.Flags().String("area", "", "Area filter for rooms (e.g., '>300')")
	FindCmd.Flags().BoolP("count", "c", false, "Only show count of matches")
	FindCmd.Flags().IntP("limit", "l", 0, "Limit number of results")
}

func runFind(cmd *cobra.Command, args []string) error {
	// Get search path
	searchPath := "/"
	if len(args) > 0 {
		searchPath = args[0]
	}
	
	// Get navigation context for relative paths
	ctx := navigation.GetContext()
	if !strings.HasPrefix(searchPath, "/") {
		searchPath = ctx.GetRelativePath(searchPath)
	}
	searchPath = navigation.NormalizePath(searchPath)
	
	// Get search criteria
	criteria := buildSearchCriteria(cmd)
	
	// Perform search
	results := performSearch(searchPath, criteria)
	
	// Display results
	countOnly, _ := cmd.Flags().GetBool("count")
	limit, _ := cmd.Flags().GetInt("limit")
	
	if countOnly {
		fmt.Printf("%d matches found\n", len(results))
	} else {
		displayFindResults(results, limit)
	}
	
	return nil
}

type SearchCriteria struct {
	Type           string
	NamePattern    string
	LoadFilter     *PropertyFilter
	VoltageFilter  *PropertyFilter
	ConfidenceFilter *PropertyFilter
	StatusFilter   string
	AreaFilter     *PropertyFilter
}

type PropertyFilter struct {
	Operator string // >, <, =, >=, <=
	Value    float64
	StringValue string
}

func buildSearchCriteria(cmd *cobra.Command) *SearchCriteria {
	criteria := &SearchCriteria{}
	
	criteria.Type, _ = cmd.Flags().GetString("type")
	criteria.NamePattern, _ = cmd.Flags().GetString("name")
	criteria.StatusFilter, _ = cmd.Flags().GetString("status")
	
	// Parse property filters
	if load, _ := cmd.Flags().GetString("load"); load != "" {
		criteria.LoadFilter = parsePropertyFilter(load)
	}
	
	if voltage, _ := cmd.Flags().GetString("voltage"); voltage != "" {
		criteria.VoltageFilter = parsePropertyFilter(voltage)
	}
	
	if confidence, _ := cmd.Flags().GetString("confidence"); confidence != "" {
		criteria.ConfidenceFilter = parsePropertyFilter(confidence)
	}
	
	if area, _ := cmd.Flags().GetString("area"); area != "" {
		criteria.AreaFilter = parsePropertyFilter(area)
	}
	
	return criteria
}

func parsePropertyFilter(filter string) *PropertyFilter {
	pf := &PropertyFilter{}
	
	// Extract operator
	if strings.HasPrefix(filter, ">=") {
		pf.Operator = ">="
		filter = filter[2:]
	} else if strings.HasPrefix(filter, "<=") {
		pf.Operator = "<="
		filter = filter[2:]
	} else if strings.HasPrefix(filter, ">") {
		pf.Operator = ">"
		filter = filter[1:]
	} else if strings.HasPrefix(filter, "<") {
		pf.Operator = "<"
		filter = filter[1:]
	} else if strings.HasPrefix(filter, "=") {
		pf.Operator = "="
		filter = filter[1:]
	} else {
		pf.Operator = "="
	}
	
	// Remove quotes if present
	filter = strings.Trim(filter, "\"'")
	
	// Try to parse as number
	filter = strings.TrimSuffix(filter, "A") // Remove A from amperage
	filter = strings.TrimSuffix(filter, "V") // Remove V from voltage
	
	if val, err := strconv.ParseFloat(filter, 64); err == nil {
		pf.Value = val
	} else {
		pf.StringValue = filter
	}
	
	return pf
}

func performSearch(searchPath string, criteria *SearchCriteria) []SearchResult {
	results := []SearchResult{}
	
	// Recursively search from the given path
	searchRecursive(searchPath, criteria, &results)
	
	return results
}

func searchRecursive(path string, criteria *SearchCriteria, results *[]SearchResult) {
	// Get contents at this path
	contents := getContentsForPath(path)
	
	for _, obj := range contents {
		objectPath := navigation.NormalizePath(path + "/" + obj.Name)
		
		// Check if object matches criteria
		if matchesCriteria(obj, objectPath, criteria) {
			*results = append(*results, SearchResult{
				Path:       objectPath,
				Object:     obj,
			})
		}
		
		// Recurse into directories
		if isDirectory(obj.Type) {
			searchRecursive(objectPath, criteria, results)
		}
	}
}

func matchesCriteria(obj models.ArxObjectV2, path string, criteria *SearchCriteria) bool {
	// Check type
	if criteria.Type != "" && obj.Type != criteria.Type {
		return false
	}
	
	// Check name pattern
	if criteria.NamePattern != "" {
		pattern := strings.ReplaceAll(criteria.NamePattern, "*", "")
		if !strings.Contains(obj.Name, pattern) {
			return false
		}
	}
	
	// Check property filters
	if criteria.LoadFilter != nil {
		if !checkPropertyFilter(obj, "load", "current_load", criteria.LoadFilter) {
			return false
		}
	}
	
	if criteria.VoltageFilter != nil {
		if !checkPropertyFilter(obj, "voltage", "", criteria.VoltageFilter) {
			return false
		}
	}
	
	if criteria.ConfidenceFilter != nil {
		if !checkPropertyFilter(obj, "confidence", "", criteria.ConfidenceFilter) {
			return false
		}
	}
	
	if criteria.StatusFilter != "" {
		if status, ok := obj.Properties["status"]; ok {
			if status != criteria.StatusFilter {
				return false
			}
		} else {
			return false
		}
	}
	
	if criteria.AreaFilter != nil {
		if !checkPropertyFilter(obj, "area", "", criteria.AreaFilter) {
			return false
		}
	}
	
	return true
}

func checkPropertyFilter(obj models.ArxObjectV2, propName string, altName string, filter *PropertyFilter) bool {
	if obj.Properties == nil {
		return false
	}
	
	// Try both property names
	var value interface{}
	var ok bool
	
	value, ok = obj.Properties[propName]
	if !ok && altName != "" {
		value, ok = obj.Properties[altName]
	}
	
	if !ok {
		return false
	}
	
	// Convert value to float for comparison
	var numValue float64
	switch v := value.(type) {
	case float64:
		numValue = v
	case float32:
		numValue = float64(v)
	case int:
		numValue = float64(v)
	case string:
		// Try to extract number from string (e.g., "12.5A" -> 12.5)
		cleaned := strings.TrimSuffix(v, "A")
		cleaned = strings.TrimSuffix(cleaned, "V")
		cleaned = strings.TrimSuffix(cleaned, " sq ft")
		if val, err := strconv.ParseFloat(cleaned, 64); err == nil {
			numValue = val
		} else {
			return false
		}
	default:
		return false
	}
	
	// Apply operator
	switch filter.Operator {
	case ">":
		return numValue > filter.Value
	case "<":
		return numValue < filter.Value
	case ">=":
		return numValue >= filter.Value
	case "<=":
		return numValue <= filter.Value
	case "=":
		return numValue == filter.Value
	default:
		return false
	}
}

type SearchResult struct {
	Path   string
	Object models.ArxObjectV2
}

func displayFindResults(results []SearchResult, limit int) {
	if len(results) == 0 {
		fmt.Println("No matches found")
		return
	}
	
	// Apply limit if specified
	if limit > 0 && len(results) > limit {
		results = results[:limit]
	}
	
	// Display results
	for _, result := range results {
		fmt.Printf("%s", result.Path)
		
		// Add key properties
		if result.Object.Properties != nil {
			props := []string{}
			
			if voltage, ok := result.Object.Properties["voltage"]; ok {
				props = append(props, fmt.Sprintf("voltage=%v", voltage))
			}
			if load, ok := result.Object.Properties["load"]; ok {
				props = append(props, fmt.Sprintf("load=%v", load))
			} else if load, ok := result.Object.Properties["current_load"]; ok {
				props = append(props, fmt.Sprintf("load=%v", load))
			}
			if confidence, ok := result.Object.Properties["confidence"]; ok {
				props = append(props, fmt.Sprintf("confidence=%.2f", confidence))
			}
			if status, ok := result.Object.Properties["status"]; ok {
				props = append(props, fmt.Sprintf("status=%v", status))
			}
			
			if len(props) > 0 {
				fmt.Printf("  [%s]", strings.Join(props, ", "))
			}
		}
		
		fmt.Println()
	}
	
	fmt.Printf("\n%d matches found\n", len(results))
}

// Example output for vision.md specification
func exampleFindOutput() {
	example := `
# arxos find /electrical -type outlet -load ">15A"

/electrical/main-panel/circuit-2/outlet-4  [voltage=120V, load=16.2A, confidence=0.91]
/electrical/main-panel/circuit-5/outlet-2  [voltage=120V, load=18.5A, confidence=0.88]
/electrical/sub-panel-a/circuit-3/outlet-1  [voltage=120V, load=15.8A, confidence=0.75]

3 matches found
`
	fmt.Print(example)
}