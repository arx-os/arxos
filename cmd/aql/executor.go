package aql

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/jmoiron/sqlx"
)

// Executor executes parsed AQL queries
type Executor struct {
	db     *sqlx.DB
	parser *Parser
}

// NewExecutor creates a new AQL executor
func NewExecutor(db *sqlx.DB) *Executor {
	return &Executor{
		db:     db,
		parser: NewParser(),
	}
}

// Execute executes an AQL query string and returns results
func (e *Executor) Execute(query string) (*Result, error) {
	// Parse the query
	parsedQuery, err := e.parser.Parse(query)
	if err != nil {
		return nil, fmt.Errorf("parse error: %w", err)
	}

	// Execute based on query type
	switch parsedQuery.Type {
	case SELECT:
		return e.executeSelect(parsedQuery)
	case UPDATE:
		return e.executeUpdate(parsedQuery)
	case DELETE:
		return e.executeDelete(parsedQuery)
	case VALIDATE:
		return e.executeValidate(parsedQuery)
	case HISTORY:
		return e.executeHistory(parsedQuery)
	case DIFF:
		return e.executeDiff(parsedQuery)
	default:
		return nil, fmt.Errorf("unsupported query type: %v", parsedQuery.Type)
	}
}

// Result represents the result of an AQL query
type Result struct {
	Type         QueryType               `json:"type"`
	Columns      []string                `json:"columns,omitempty"`
	Rows         []map[string]interface{} `json:"rows,omitempty"`
	RowsAffected int64                   `json:"rows_affected,omitempty"`
	Message      string                  `json:"message,omitempty"`
	Error        string                  `json:"error,omitempty"`
}

// executeSelect executes a SELECT query
func (e *Executor) executeSelect(q *Query) (*Result, error) {
	// Build SQL query
	sqlQuery, args := e.buildSelectSQL(q)
	
	// Execute query
	rows, err := e.db.Query(sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("query execution failed: %w", err)
	}
	defer rows.Close()

	// Get column names
	columns, err := rows.Columns()
	if err != nil {
		return nil, fmt.Errorf("failed to get columns: %w", err)
	}

	// Fetch results
	results := []map[string]interface{}{}
	for rows.Next() {
		// Create a slice of interface{} to hold column values
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range values {
			valuePtrs[i] = &values[i]
		}

		// Scan row into value pointers
		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, fmt.Errorf("scan failed: %w", err)
		}

		// Create row map
		row := make(map[string]interface{})
		for i, col := range columns {
			val := values[i]
			// Handle null values
			if val == nil {
				row[col] = nil
			} else {
				// Convert bytes to string if needed
				if b, ok := val.([]byte); ok {
					row[col] = string(b)
				} else {
					row[col] = val
				}
			}
		}
		results = append(results, row)
	}

	return &Result{
		Type:    SELECT,
		Columns: columns,
		Rows:    results,
	}, nil
}

// buildSelectSQL converts AQL SELECT to SQL
func (e *Executor) buildSelectSQL(q *Query) (string, []interface{}) {
	var sqlBuilder strings.Builder
	args := []interface{}{}

	// Build SELECT clause
	sqlBuilder.WriteString("SELECT ")
	if len(q.Fields) == 0 || (len(q.Fields) == 1 && q.Fields[0] == "*") {
		sqlBuilder.WriteString("*")
	} else {
		sqlBuilder.WriteString(strings.Join(q.Fields, ", "))
	}

	// Build FROM clause
	sqlBuilder.WriteString(" FROM ")
	
	// Handle building:id format
	tableName := e.resolveTableName(q.Target)
	sqlBuilder.WriteString(tableName)

	// Build WHERE clause
	if len(q.Conditions) > 0 {
		sqlBuilder.WriteString(" WHERE ")
		conditions := []string{}
		for i, cond := range q.Conditions {
			// Use parameter placeholders
			conditions = append(conditions, fmt.Sprintf("%s %s $%d", 
				cond.Field, cond.Operator, i+1))
			args = append(args, cond.Value)
		}
		sqlBuilder.WriteString(strings.Join(conditions, " AND "))
	}

	// Add default ordering
	sqlBuilder.WriteString(" ORDER BY created_at DESC")

	// Add default limit if not specified
	if q.Options == nil || q.Options["limit"] == nil {
		sqlBuilder.WriteString(" LIMIT 100")
	}

	return sqlBuilder.String(), args
}

// resolveTableName converts AQL target to database table name
func (e *Executor) resolveTableName(target string) string {
	// Handle building:id format
	if strings.HasPrefix(target, "building:") {
		parts := strings.Split(target, ":")
		if len(parts) >= 2 {
			// For now, return arxobjects table
			// TODO: Add building-specific filtering
			return "arxobjects"
		}
	}
	
	// Direct table name
	switch target {
	case "objects", "arxobjects":
		return "arxobjects"
	case "buildings":
		return "buildings"
	case "floors":
		return "floors"
	case "systems":
		return "systems"
	default:
		return target
	}
}

// executeUpdate executes an UPDATE query
func (e *Executor) executeUpdate(q *Query) (*Result, error) {
	// Build SQL query
	sqlQuery, args := e.buildUpdateSQL(q)
	
	// Execute query
	result, err := e.db.Exec(sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("update execution failed: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	
	return &Result{
		Type:         UPDATE,
		RowsAffected: rowsAffected,
		Message:      fmt.Sprintf("Updated %d rows", rowsAffected),
	}, nil
}

// buildUpdateSQL converts AQL UPDATE to SQL
func (e *Executor) buildUpdateSQL(q *Query) (string, []interface{}) {
	var sqlBuilder strings.Builder
	args := []interface{}{}

	// Build UPDATE clause
	tableName := e.resolveTableName(q.Target)
	sqlBuilder.WriteString(fmt.Sprintf("UPDATE %s SET ", tableName))

	// Build SET clause
	setClauses := []string{}
	argIndex := 1
	for field, value := range q.Values {
		setClauses = append(setClauses, fmt.Sprintf("%s = $%d", field, argIndex))
		args = append(args, value)
		argIndex++
	}
	sqlBuilder.WriteString(strings.Join(setClauses, ", "))

	// Build WHERE clause
	if len(q.Conditions) > 0 {
		sqlBuilder.WriteString(" WHERE ")
		conditions := []string{}
		for _, cond := range q.Conditions {
			conditions = append(conditions, fmt.Sprintf("%s %s $%d", 
				cond.Field, cond.Operator, argIndex))
			args = append(args, cond.Value)
			argIndex++
		}
		sqlBuilder.WriteString(strings.Join(conditions, " AND "))
	}

	return sqlBuilder.String(), args
}

// executeDelete executes a DELETE query
func (e *Executor) executeDelete(q *Query) (*Result, error) {
	// Safety check - require WHERE clause
	if len(q.Conditions) == 0 {
		return nil, fmt.Errorf("DELETE requires WHERE clause for safety")
	}

	// Build SQL query
	sqlQuery, args := e.buildDeleteSQL(q)
	
	// Execute query
	result, err := e.db.Exec(sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("delete execution failed: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	
	return &Result{
		Type:         DELETE,
		RowsAffected: rowsAffected,
		Message:      fmt.Sprintf("Deleted %d rows", rowsAffected),
	}, nil
}

// buildDeleteSQL converts AQL DELETE to SQL
func (e *Executor) buildDeleteSQL(q *Query) (string, []interface{}) {
	var sqlBuilder strings.Builder
	args := []interface{}{}

	// Build DELETE clause
	tableName := e.resolveTableName(q.Target)
	sqlBuilder.WriteString(fmt.Sprintf("DELETE FROM %s", tableName))

	// Build WHERE clause (required)
	sqlBuilder.WriteString(" WHERE ")
	conditions := []string{}
	for i, cond := range q.Conditions {
		conditions = append(conditions, fmt.Sprintf("%s %s $%d", 
			cond.Field, cond.Operator, i+1))
		args = append(args, cond.Value)
	}
	sqlBuilder.WriteString(strings.Join(conditions, " AND "))

	return sqlBuilder.String(), args
}

// executeValidate marks an object as validated
func (e *Executor) executeValidate(q *Query) (*Result, error) {
	// For now, update confidence and validation status
	updateQuery := &Query{
		Type:   UPDATE,
		Target: q.Target,
		Values: map[string]interface{}{
			"validation_status": "validated",
			"confidence":        1.0,
			"validated_at":      "NOW()",
		},
		Conditions: q.Conditions,
	}
	
	return e.executeUpdate(updateQuery)
}

// executeHistory returns version history for an object
func (e *Executor) executeHistory(q *Query) (*Result, error) {
	// TODO: Implement history tracking
	// For now, return a placeholder result
	return &Result{
		Type:    HISTORY,
		Message: "History tracking not yet implemented",
		Rows:    []map[string]interface{}{},
	}, nil
}

// executeDiff compares two versions or states
func (e *Executor) executeDiff(q *Query) (*Result, error) {
	// TODO: Implement diff functionality
	// For now, return a placeholder result
	return &Result{
		Type:    DIFF,
		Message: "Diff functionality not yet implemented",
		Rows:    []map[string]interface{}{},
	}, nil
}

// ToJSON converts result to JSON string
func (r *Result) ToJSON() (string, error) {
	bytes, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

// ToTable converts result to table format (for display)
func (r *Result) ToTable() string {
	if len(r.Rows) == 0 {
		return "No results"
	}

	// This is a simple implementation
	// In production, use a proper table formatting library
	var output strings.Builder
	
	// Header
	output.WriteString(strings.Join(r.Columns, " | "))
	output.WriteString("\n")
	output.WriteString(strings.Repeat("-", 80))
	output.WriteString("\n")
	
	// Rows
	for _, row := range r.Rows {
		values := []string{}
		for _, col := range r.Columns {
			val := ""
			if row[col] != nil {
				val = fmt.Sprintf("%v", row[col])
			}
			values = append(values, val)
		}
		output.WriteString(strings.Join(values, " | "))
		output.WriteString("\n")
	}
	
	return output.String()
}