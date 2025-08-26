package query

import (
	"fmt"
	"strings"
	"time"
	"github.com/spf13/cobra"
)

var askCmd = &cobra.Command{
	Use:   "ask [question]",
	Short: "Ask questions in natural language and get AQL-powered answers",
	Long: `Ask questions about your building in natural language.
The system will automatically convert your question to AQL and execute it.

Examples:
  arx ask "show me all HVAC equipment on the 3rd floor"
  arx ask "what's the energy consumption of building A last month?"
  arx ask "find all equipment that needs maintenance this week"
  arx ask "show me the connection between electrical panel E1 and room 205"`,
	Args: cobra.MinimumNArgs(1),
	RunE: runAsk,
}

func init() {
	QueryCmd.AddCommand(askCmd)
	
	// Add flags for natural language processing
	askCmd.Flags().String("context", "", "Additional context for better query understanding")
	askCmd.Flags().String("format", "table", "Output format (table, json, csv, ascii-bim, summary)")
	askCmd.Flags().Bool("explain", false, "Show the generated AQL query")
	askCmd.Flags().Bool("interactive", false, "Enable interactive mode for query refinement")
}

func runAsk(cmd *cobra.Command, args []string) error {
	question := strings.Join(args, " ")
	context, _ := cmd.Flags().GetString("context")
	format, _ := cmd.Flags().GetString("format")
	explain, _ := cmd.Flags().GetBool("explain")
	_ = cmd.Flags().GetBool("interactive") // TODO: Implement interactive mode

	// Generate AQL query from natural language
	aqlQuery, confidence := generateAQLFromQuestion(question, context)
	
	if explain {
		fmt.Printf("Generated AQL Query (confidence: %.1f%%):\n", confidence*100)
		fmt.Printf("  %s\n\n", aqlQuery)
	}

	// Execute the generated query
	result := executeGeneratedQuery(aqlQuery, question)
	
	// Display results
	display := NewResultDisplay(format, "default")
	return display.DisplayResult(result)
}

// generateAQLFromQuestion converts natural language to AQL
func generateAQLFromQuestion(question, context string) (string, float64) {
	question = strings.ToLower(question)
	
	// Simple rule-based conversion (in production, this would use NLP/AI)
	var aqlQuery string
	confidence := 0.8

	// Equipment queries
	if strings.Contains(question, "hvac") || strings.Contains(question, "air conditioning") {
		if strings.Contains(question, "floor") {
			floor := extractFloorNumber(question)
			aqlQuery = fmt.Sprintf("SELECT * FROM equipment WHERE type IN ('hvac', 'air_conditioning') AND floor = %s", floor)
		} else {
			aqlQuery = "SELECT * FROM equipment WHERE type IN ('hvac', 'air_conditioning')"
		}
	} else if strings.Contains(question, "electrical") || strings.Contains(question, "panel") {
		if strings.Contains(question, "room") {
			room := extractRoomNumber(question)
			aqlQuery = fmt.Sprintf("SELECT * FROM equipment WHERE type = 'electrical_panel' AND room = '%s'", room)
		} else {
			aqlQuery = "SELECT * FROM equipment WHERE type = 'electrical_panel'"
		}
	} else if strings.Contains(question, "maintenance") {
		if strings.Contains(question, "week") {
			aqlQuery = "SELECT * FROM equipment WHERE maintenance_due <= NOW() + INTERVAL '7 days'"
		} else {
			aqlQuery = "SELECT * FROM equipment WHERE maintenance_due <= NOW()"
		}
	} else if strings.Contains(question, "energy") || strings.Contains(question, "consumption") {
		if strings.Contains(question, "month") {
			aqlQuery = "SELECT * FROM energy_consumption WHERE timestamp >= NOW() - INTERVAL '1 month' ORDER BY timestamp DESC"
		} else {
			aqlQuery = "SELECT * FROM energy_consumption ORDER BY timestamp DESC LIMIT 100"
		}
	} else if strings.Contains(question, "connection") || strings.Contains(question, "connected") {
		aqlQuery = "SELECT * FROM connections WHERE source_type = 'equipment' AND target_type = 'room'"
	} else if strings.Contains(question, "show me all") || strings.Contains(question, "find all") {
		if strings.Contains(question, "floor") {
			floor := extractFloorNumber(question)
			aqlQuery = fmt.Sprintf("SELECT * FROM arxobjects WHERE floor = %s", floor)
		} else {
			aqlQuery = "SELECT * FROM arxobjects LIMIT 50"
		}
	} else {
		// Default fallback
		aqlQuery = "SELECT * FROM arxobjects WHERE name ILIKE '%" + question + "%' LIMIT 20"
		confidence = 0.5
	}

	return aqlQuery, confidence
}

// executeGeneratedQuery runs the generated AQL query
func executeGeneratedQuery(aqlQuery, originalQuestion string) *AQLResult {
	// For now, generate mock results based on the query type
	// In production, this would execute the actual AQL query
	
	var objects []interface{}
	var message string
	
	if strings.Contains(aqlQuery, "hvac") || strings.Contains(aqlQuery, "air_conditioning") {
		objects = generateMockHVACResults()
		message = "Found HVAC equipment based on your question"
	} else if strings.Contains(aqlQuery, "electrical") {
		objects = generateMockElectricalResults()
		message = "Found electrical equipment based on your question"
	} else if strings.Contains(aqlQuery, "maintenance") {
		objects = generateMockMaintenanceResults()
		message = "Found equipment requiring maintenance based on your question"
	} else if strings.Contains(aqlQuery, "energy") {
		objects = generateMockEnergyResults()
		message = "Found energy consumption data based on your question"
	} else {
		objects = generateMockGenericResults(originalQuestion)
		message = "Found results based on your question"
	}

	return &AQLResult{
		Type:       "ASK",
		Objects:    objects,
		Count:      len(objects),
		Message:    message,
		Metadata: map[string]interface{}{
			"original_question": originalQuestion,
			"generated_aql":     aqlQuery,
			"confidence":        0.8,
		},
		ExecutedAt: time.Now(),
	}
}

// Helper functions for extracting information from questions
func extractFloorNumber(question string) string {
	// Simple regex-like extraction
	if strings.Contains(question, "3rd") || strings.Contains(question, "third") {
		return "3"
	} else if strings.Contains(question, "2nd") || strings.Contains(question, "second") {
		return "2"
	} else if strings.Contains(question, "1st") || strings.Contains(question, "first") {
		return "1"
	}
	return "1" // default
}

func extractRoomNumber(question string) string {
	// Extract room numbers like "205", "room 205", etc.
	words := strings.Fields(question)
	for _, word := range words {
		if len(word) >= 3 && word[0] >= '0' && word[0] <= '9' {
			return word
		}
	}
	return "101" // default
}

// Mock data generation functions
func generateMockHVACResults() []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "hvac-001", "name": "Main AHU-1", "type": "hvac", "floor": 3,
			"status": "operational", "efficiency": 85.5, "last_service": "2024-01-15",
		},
		map[string]interface{}{
			"id": "hvac-002", "name": "Zone VAV-3A", "type": "hvac", "floor": 3,
			"status": "operational", "efficiency": 92.1, "last_service": "2024-01-10",
		},
		map[string]interface{}{
			"id": "hvac-003", "name": "Chiller Unit", "type": "hvac", "floor": 1,
			"status": "maintenance", "efficiency": 78.3, "last_service": "2024-01-05",
		},
	}
}

func generateMockElectricalResults() []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "elec-001", "name": "Main Electrical Panel", "type": "electrical_panel",
			"room": "electrical_room", "status": "operational", "voltage": 480,
		},
		map[string]interface{}{
			"id": "elec-002", "name": "Sub Panel 3A", "type": "electrical_panel",
			"room": "305", "status": "operational", "voltage": 120,
		},
	}
}

func generateMockMaintenanceResults() []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "hvac-003", "name": "Chiller Unit", "type": "hvac",
			"maintenance_due": "2024-01-20", "priority": "high", "estimated_cost": 2500,
		},
		map[string]interface{}{
			"id": "elec-003", "name": "Emergency Generator", "type": "generator",
			"maintenance_due": "2024-01-22", "priority": "medium", "estimated_cost": 800,
		},
	}
}

func generateMockEnergyResults() []interface{} {
	return []interface{}{
		map[string]interface{}{
			"timestamp": "2024-01-15 10:00:00", "building": "HQ", "floor": 3,
			"consumption_kwh": 45.2, "cost_usd": 6.78,
		},
		map[string]interface{}{
			"timestamp": "2024-01-15 09:00:00", "building": "HQ", "floor": 3,
			"consumption_kwh": 42.8, "cost_usd": 6.42,
		},
	}
}

func generateMockGenericResults(question string) []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "obj-001", "name": "Generic Object", "type": "equipment",
			"description": "Found based on: " + question, "status": "active",
		},
	}
}
