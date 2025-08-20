// Package aql implements the ArxObject Query Language
// A SQL-like language for querying building infrastructure data
package aql

import (
	"fmt"
	"strings"
	"regexp"
	"strconv"
)

// Query represents a parsed AQL query
type Query struct {
	Type       QueryType
	Target     string
	Filters    []Filter
	Selections []string
	OrderBy    string
	Limit      int
	TimeTravel *TimeTravel
}

// QueryType represents the type of AQL query
type QueryType string

const (
	SELECT   QueryType = "SELECT"
	UPDATE   QueryType = "UPDATE"
	VALIDATE QueryType = "VALIDATE"
	HISTORY  QueryType = "HISTORY"
	DIFF     QueryType = "DIFF"
)

// Filter represents a query filter condition
type Filter struct {
	Field    string
	Operator string
	Value    interface{}
}

// TimeTravel allows querying historical states
type TimeTravel struct {
	AsOf     string // Specific timestamp
	Between  []string // Date range
	Version  int    // Specific version number
}

// Parser handles AQL query parsing
type Parser struct {
	query string
	pos   int
}

// NewParser creates a new AQL parser
func NewParser() *Parser {
	return &Parser{}
}

// Parse parses an AQL query string into a Query structure
func (p *Parser) Parse(query string) (*Query, error) {
	p.query = strings.TrimSpace(query)
	p.pos = 0
	
	// Determine query type
	queryType := p.parseQueryType()
	
	switch queryType {
	case SELECT:
		return p.parseSelect()
	case UPDATE:
		return p.parseUpdate()
	case VALIDATE:
		return p.parseValidate()
	case HISTORY:
		return p.parseHistory()
	case DIFF:
		return p.parseDiff()
	default:
		return nil, fmt.Errorf("unknown query type")
	}
}

// parseQueryType determines the type of query
func (p *Parser) parseQueryType() QueryType {
	upper := strings.ToUpper(p.query)
	
	if strings.HasPrefix(upper, "SELECT") {
		return SELECT
	} else if strings.HasPrefix(upper, "UPDATE") {
		return UPDATE
	} else if strings.HasPrefix(upper, "VALIDATE") {
		return VALIDATE
	} else if strings.HasPrefix(upper, "HISTORY") {
		return HISTORY
	} else if strings.HasPrefix(upper, "DIFF") {
		return DIFF
	}
	
	return ""
}

// parseSelect parses a SELECT query
func (p *Parser) parseSelect() (*Query, error) {
	q := &Query{Type: SELECT}
	
	// Parse: SELECT [fields] FROM [target] WHERE [conditions]
	selectRegex := regexp.MustCompile(`(?i)SELECT\s+(.*?)\s+FROM\s+(.*?)(?:\s+WHERE\s+(.*))?$`)
	matches := selectRegex.FindStringSubmatch(p.query)
	
	if len(matches) < 3 {
		return nil, fmt.Errorf("invalid SELECT syntax")
	}
	
	// Parse selections
	selections := strings.Split(matches[1], ",")
	for _, sel := range selections {
		q.Selections = append(q.Selections, strings.TrimSpace(sel))
	}
	
	// Parse target
	q.Target = strings.TrimSpace(matches[2])
	
	// Parse WHERE clause if present
	if len(matches) > 3 && matches[3] != "" {
		filters, err := p.parseWhereClause(matches[3])
		if err != nil {
			return nil, err
		}
		q.Filters = filters
	}
	
	return q, nil
}

// parseWhereClause parses WHERE conditions
func (p *Parser) parseWhereClause(where string) ([]Filter, error) {
	var filters []Filter
	
	// Split by AND (simplified - production would need proper parsing)
	conditions := strings.Split(where, " AND ")
	
	for _, condition := range conditions {
		filter, err := p.parseCondition(condition)
		if err != nil {
			return nil, err
		}
		filters = append(filters, filter)
	}
	
	return filters, nil
}

// parseCondition parses a single condition
func (p *Parser) parseCondition(condition string) (Filter, error) {
	// Parse operators: =, !=, >, <, >=, <=, LIKE, IN, NEAR, WITHIN, CONNECTED_TO
	operators := []string{"!=", ">=", "<=", "=", ">", "<", " LIKE ", " IN ", " NEAR ", " WITHIN ", " CONNECTED_TO "}
	
	for _, op := range operators {
		if strings.Contains(condition, op) {
			parts := strings.SplitN(condition, op, 2)
			if len(parts) != 2 {
				return Filter{}, fmt.Errorf("invalid condition: %s", condition)
			}
			
			field := strings.TrimSpace(parts[0])
			valueStr := strings.TrimSpace(parts[1])
			
			// Parse value type
			value := p.parseValue(valueStr)
			
			return Filter{
				Field:    field,
				Operator: strings.TrimSpace(op),
				Value:    value,
			}, nil
		}
	}
	
	return Filter{}, fmt.Errorf("no operator found in condition: %s", condition)
}

// parseValue parses a value string into appropriate type
func (p *Parser) parseValue(valueStr string) interface{} {
	// Remove quotes if present
	valueStr = strings.Trim(valueStr, "'\"")
	
	// Try to parse as number
	if f, err := strconv.ParseFloat(valueStr, 64); err == nil {
		return f
	}
	
	// Try to parse as boolean
	if valueStr == "true" || valueStr == "TRUE" {
		return true
	}
	if valueStr == "false" || valueStr == "FALSE" {
		return false
	}
	
	// Return as string
	return valueStr
}

// parseUpdate parses an UPDATE query
func (p *Parser) parseUpdate() (*Query, error) {
	q := &Query{Type: UPDATE}
	
	// Parse: UPDATE [target] SET [field=value] WHERE [conditions]
	updateRegex := regexp.MustCompile(`(?i)UPDATE\s+(.*?)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*))?$`)
	matches := updateRegex.FindStringSubmatch(p.query)
	
	if len(matches) < 3 {
		return nil, fmt.Errorf("invalid UPDATE syntax")
	}
	
	q.Target = strings.TrimSpace(matches[1])
	
	// Parse SET clause (simplified)
	// In production, this would handle multiple field updates
	
	// Parse WHERE clause if present
	if len(matches) > 3 && matches[3] != "" {
		filters, err := p.parseWhereClause(matches[3])
		if err != nil {
			return nil, err
		}
		q.Filters = filters
	}
	
	return q, nil
}

// parseValidate parses a VALIDATE query
func (p *Parser) parseValidate() (*Query, error) {
	q := &Query{Type: VALIDATE}
	
	// Parse: VALIDATE [target] WITH [validation_data]
	validateRegex := regexp.MustCompile(`(?i)VALIDATE\s+(.*?)(?:\s+WITH\s+(.*))?$`)
	matches := validateRegex.FindStringSubmatch(p.query)
	
	if len(matches) < 2 {
		return nil, fmt.Errorf("invalid VALIDATE syntax")
	}
	
	q.Target = strings.TrimSpace(matches[1])
	
	return q, nil
}

// parseHistory parses a HISTORY query
func (p *Parser) parseHistory() (*Query, error) {
	q := &Query{Type: HISTORY}
	
	// Parse: HISTORY OF [target] [time_range]
	historyRegex := regexp.MustCompile(`(?i)HISTORY\s+OF\s+(.*?)(?:\s+(.*))?$`)
	matches := historyRegex.FindStringSubmatch(p.query)
	
	if len(matches) < 2 {
		return nil, fmt.Errorf("invalid HISTORY syntax")
	}
	
	q.Target = strings.TrimSpace(matches[1])
	
	return q, nil
}

// parseDiff parses a DIFF query
func (p *Parser) parseDiff() (*Query, error) {
	q := &Query{Type: DIFF}
	
	// Parse: DIFF [target] BETWEEN [version1] AND [version2]
	diffRegex := regexp.MustCompile(`(?i)DIFF\s+(.*?)\s+BETWEEN\s+(.*?)\s+AND\s+(.*)$`)
	matches := diffRegex.FindStringSubmatch(p.query)
	
	if len(matches) < 4 {
		return nil, fmt.Errorf("invalid DIFF syntax")
	}
	
	q.Target = strings.TrimSpace(matches[1])
	q.TimeTravel = &TimeTravel{
		Between: []string{
			strings.TrimSpace(matches[2]),
			strings.TrimSpace(matches[3]),
		},
	}
	
	return q, nil
}