package query

import (
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var (
	selectLimit  int
	selectOffset int
	selectFields string
)

func init() {
	selectCmd.Flags().IntVarP(&selectLimit, "limit", "l", 100, "limit number of results")
	selectCmd.Flags().IntVarP(&selectOffset, "offset", "o", 0, "offset for pagination")
	selectCmd.Flags().StringVarP(&selectFields, "fields", "", "*", "fields to select")
}

func runSelect(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("query required")
	}

	query := strings.Join(args, " ")

	// Parse the query using the AQL parser
	parser := NewAQLParser()
	aqlQuery, err := parser.Parse(query)
	if err != nil {
		return fmt.Errorf("failed to parse query: %w", err)
	}

	// Apply command-line flags to parsed query
	if selectLimit > 0 {
		aqlQuery.Limit = selectLimit
	}
	if selectOffset > 0 {
		aqlQuery.Offset = selectOffset
	}
	if selectFields != "" && selectFields != "*" {
		aqlQuery.Fields = strings.Split(selectFields, ",")
		for i := range aqlQuery.Fields {
			aqlQuery.Fields[i] = strings.TrimSpace(aqlQuery.Fields[i])
		}
	}

	// Execute the parsed query
	result, err := executeAQLQuery(aqlQuery)
	if err != nil {
		return fmt.Errorf("failed to execute query: %w", err)
	}

	// Display results using our result display system
	display := NewResultDisplay("table", "default")
	return display.DisplayResult(result)
}

// executeAQLQuery executes a parsed AQL query
func executeAQLQuery(aqlQuery *AQLQuery) (*AQLResult, error) {
	startTime := time.Now()
	
	// For now, use mock execution until database integration is complete
	// In production, this would connect to the actual database
	var objects []interface{}
	var err error
	
	switch aqlQuery.Type {
	case "SELECT":
		objects, err = executeSelectQuery(aqlQuery)
	case "INSERT":
		objects, err = executeInsertQuery(aqlQuery)
	case "UPDATE":
		objects, err = executeUpdateQuery(aqlQuery)
	case "DELETE":
		objects, err = executeDeleteQuery(aqlQuery)
	default:
		return nil, fmt.Errorf("unsupported query type: %s", aqlQuery.Type)
	}
	
	if err != nil {
		return nil, err
	}
	
	executionTime := time.Since(startTime)
	
	result := &AQLResult{
		Type:    aqlQuery.Type,
		Objects: objects,
		Count:   len(objects),
		Message: fmt.Sprintf("%s query executed successfully", aqlQuery.Type),
		Metadata: map[string]interface{}{
			"rows_affected":  len(objects),
			"query_type":     aqlQuery.Type,
			"execution_time": fmt.Sprintf("%.3fs", executionTime.Seconds()),
			"from_table":     aqlQuery.From,
		},
		ExecutedAt: time.Now(),
	}
	
	return result, nil
}

// executeSelectQuery executes a SELECT query
func executeSelectQuery(query *AQLQuery) ([]interface{}, error) {
	// Generate mock data based on the query
	// In production, this would query the actual database
	
	objects := make([]interface{}, 0)
	objectTypes := []string{"wall", "door", "window", "hvac", "electrical", "plumbing"}
	
	// Determine number of results based on limit
	count := 10
	if query.Limit > 0 && query.Limit < count {
		count = query.Limit
	}
	
	// Apply offset
	startIdx := 0
	if query.Offset > 0 {
		startIdx = query.Offset
	}
	
	for i := startIdx; i < startIdx+count; i++ {
		objType := objectTypes[i%len(objectTypes)]
		
		obj := make(map[string]interface{})
		
		// If specific fields are requested, only include those
		if len(query.Fields) > 0 && query.Fields[0] != "*" {
			for _, field := range query.Fields {
				switch field {
				case "id":
					obj["id"] = fmt.Sprintf("%s_%03d", objType, i+1)
				case "type":
					obj["type"] = objType
				case "path":
					obj["path"] = fmt.Sprintf("%s:hq/floor_%d/%s_%03d", query.From, (i/6)+1, objType, i+1)
				case "confidence":
					obj["confidence"] = 0.85 + float64(i%15)*0.01
				case "status":
					obj["status"] = "active"
				case "created_at":
					obj["created_at"] = time.Now().Add(-time.Duration(i*24) * time.Hour)
				case "updated_at":
					obj["updated_at"] = time.Now().Add(-time.Duration(i*6) * time.Hour)
				default:
					obj[field] = fmt.Sprintf("value_%s_%d", field, i)
				}
			}
		} else {
			// Include all fields
			obj = map[string]interface{}{
				"id":         fmt.Sprintf("%s_%03d", objType, i+1),
				"type":       objType,
				"path":       fmt.Sprintf("%s:hq/floor_%d/%s_%03d", query.From, (i/6)+1, objType, i+1),
				"confidence": 0.85 + float64(i%15)*0.01,
				"status":     "active",
				"created_at": time.Now().Add(-time.Duration(i*24) * time.Hour),
				"updated_at": time.Now().Add(-time.Duration(i*6) * time.Hour),
			}
		}
		
		// Apply WHERE filtering (simplified)
		if query.Where != nil && len(query.Where.Conditions) > 0 {
			// Check first condition for demonstration
			cond := query.Where.Conditions[0]
			if cond.Field == "type" && cond.Operator == "=" {
				if obj["type"] != cond.Value {
					continue
				}
			}
		}
		
		objects = append(objects, obj)
	}
	
	return objects, nil
}

// executeInsertQuery executes an INSERT query
func executeInsertQuery(query *AQLQuery) ([]interface{}, error) {
	// Mock insert execution
	insertedObj := make(map[string]interface{})
	for field, value := range query.Values {
		insertedObj[field] = value
	}
	insertedObj["id"] = fmt.Sprintf("new_%d", time.Now().Unix())
	insertedObj["created_at"] = time.Now()
	
	return []interface{}{insertedObj}, nil
}

// executeUpdateQuery executes an UPDATE query
func executeUpdateQuery(query *AQLQuery) ([]interface{}, error) {
	// Mock update execution
	updatedCount := 1
	if query.Where == nil {
		updatedCount = 5 // Simulate updating multiple rows
	}
	
	return []interface{}{
		map[string]interface{}{
			"updated_count": updatedCount,
			"fields":        query.Fields,
		},
	}, nil
}

// executeDeleteQuery executes a DELETE query
func executeDeleteQuery(query *AQLQuery) ([]interface{}, error) {
	// Mock delete execution
	deletedCount := 1
	if query.Where == nil {
		deletedCount = 3 // Simulate deleting multiple rows
	}
	
	return []interface{}{
		map[string]interface{}{
			"deleted_count": deletedCount,
			"from_table":    query.From,
		},
	}, nil
}
