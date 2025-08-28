// AQL (ArxOS Query Language) parser implementation
package query

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// AQLParser handles parsing of AQL queries
type AQLParser struct {
	// Token patterns for lexical analysis
	patterns map[string]*regexp.Regexp
}

// Token represents a lexical token in AQL
type Token struct {
	Type  string
	Value string
}

// AQLQuery represents a parsed AQL query
type AQLQuery struct {
	Type       string              // SELECT, INSERT, UPDATE, DELETE
	Fields     []string            // Fields to select/update
	From       string              // Table/collection name
	Where      *WhereClause        // WHERE conditions
	OrderBy    []OrderByClause     // ORDER BY clauses
	GroupBy    []string            // GROUP BY fields
	Having     *WhereClause        // HAVING conditions
	Limit      int                 // LIMIT value
	Offset     int                 // OFFSET value
	Values     map[string]interface{} // For INSERT/UPDATE
	Joins      []JoinClause        // JOIN clauses
}

// WhereClause represents WHERE/HAVING conditions
type WhereClause struct {
	Conditions []Condition
	Operator   string // AND, OR
}

// Condition represents a single WHERE condition
type Condition struct {
	Field    string
	Operator string // =, !=, <, >, <=, >=, LIKE, IN, BETWEEN
	Value    interface{}
	IsNested bool
	Nested   *WhereClause
}

// OrderByClause represents ORDER BY clause
type OrderByClause struct {
	Field     string
	Direction string // ASC, DESC
}

// JoinClause represents JOIN operations
type JoinClause struct {
	Type      string // INNER, LEFT, RIGHT, FULL
	Table     string
	On        *Condition
}

// NewAQLParser creates a new AQL parser
func NewAQLParser() *AQLParser {
	return &AQLParser{
		patterns: map[string]*regexp.Regexp{
			"SELECT":   regexp.MustCompile(`(?i)^SELECT\s+(.+?)\s+FROM\s+`),
			"FROM":     regexp.MustCompile(`(?i)\s+FROM\s+(\S+)`),
			"WHERE":    regexp.MustCompile(`(?i)\s+WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|\s+OFFSET|$)`),
			"ORDER_BY": regexp.MustCompile(`(?i)\s+ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s+OFFSET|$)`),
			"GROUP_BY": regexp.MustCompile(`(?i)\s+GROUP\s+BY\s+(.+?)(?:\s+HAVING|\s+ORDER\s+BY|\s+LIMIT|$)`),
			"HAVING":   regexp.MustCompile(`(?i)\s+HAVING\s+(.+?)(?:\s+ORDER\s+BY|\s+LIMIT|$)`),
			"LIMIT":    regexp.MustCompile(`(?i)\s+LIMIT\s+(\d+)`),
			"OFFSET":   regexp.MustCompile(`(?i)\s+OFFSET\s+(\d+)`),
			"JOIN":     regexp.MustCompile(`(?i)\s+(INNER|LEFT|RIGHT|FULL)?\s*JOIN\s+(\S+)\s+ON\s+(.+?)(?:\s+WHERE|\s+ORDER\s+BY|\s+GROUP\s+BY|$)`),
		},
	}
}

// Parse parses an AQL query string
func (p *AQLParser) Parse(query string) (*AQLQuery, error) {
	query = strings.TrimSpace(query)
	
	// Determine query type
	queryUpper := strings.ToUpper(query)
	var queryType string
	
	switch {
	case strings.HasPrefix(queryUpper, "SELECT"):
		queryType = "SELECT"
		return p.parseSelect(query)
	case strings.HasPrefix(queryUpper, "INSERT"):
		queryType = "INSERT"
		return p.parseInsert(query)
	case strings.HasPrefix(queryUpper, "UPDATE"):
		queryType = "UPDATE"
		return p.parseUpdate(query)
	case strings.HasPrefix(queryUpper, "DELETE"):
		queryType = "DELETE"
		return p.parseDelete(query)
	default:
		return nil, fmt.Errorf("unsupported query type: %s", strings.Split(query, " ")[0])
	}
}

// parseSelect parses a SELECT query
func (p *AQLParser) parseSelect(query string) (*AQLQuery, error) {
	result := &AQLQuery{
		Type:    "SELECT",
		Fields:  []string{},
		Joins:   []JoinClause{},
		OrderBy: []OrderByClause{},
		GroupBy: []string{},
		Limit:   -1,
		Offset:  0,
	}
	
	// Extract SELECT fields
	selectMatch := p.patterns["SELECT"].FindStringSubmatch(query)
	if len(selectMatch) < 2 {
		return nil, fmt.Errorf("invalid SELECT clause")
	}
	
	// Parse fields
	fields := strings.Split(selectMatch[1], ",")
	for _, field := range fields {
		result.Fields = append(result.Fields, strings.TrimSpace(field))
	}
	
	// Extract FROM
	fromMatch := p.patterns["FROM"].FindStringSubmatch(query)
	if len(fromMatch) < 2 {
		return nil, fmt.Errorf("missing FROM clause")
	}
	result.From = fromMatch[1]
	
	// Extract JOINs
	joinMatches := p.patterns["JOIN"].FindAllStringSubmatch(query, -1)
	for _, match := range joinMatches {
		if len(match) >= 4 {
			joinType := "INNER"
			if match[1] != "" {
				joinType = strings.ToUpper(match[1])
			}
			
			join := JoinClause{
				Type:  joinType,
				Table: match[2],
				On:    p.parseCondition(match[3]),
			}
			result.Joins = append(result.Joins, join)
		}
	}
	
	// Extract WHERE
	whereMatch := p.patterns["WHERE"].FindStringSubmatch(query)
	if len(whereMatch) >= 2 {
		result.Where = p.parseWhereClause(whereMatch[1])
	}
	
	// Extract GROUP BY
	groupMatch := p.patterns["GROUP_BY"].FindStringSubmatch(query)
	if len(groupMatch) >= 2 {
		groups := strings.Split(groupMatch[1], ",")
		for _, group := range groups {
			result.GroupBy = append(result.GroupBy, strings.TrimSpace(group))
		}
	}
	
	// Extract HAVING
	havingMatch := p.patterns["HAVING"].FindStringSubmatch(query)
	if len(havingMatch) >= 2 {
		result.Having = p.parseWhereClause(havingMatch[1])
	}
	
	// Extract ORDER BY
	orderMatch := p.patterns["ORDER_BY"].FindStringSubmatch(query)
	if len(orderMatch) >= 2 {
		result.OrderBy = p.parseOrderBy(orderMatch[1])
	}
	
	// Extract LIMIT
	limitMatch := p.patterns["LIMIT"].FindStringSubmatch(query)
	if len(limitMatch) >= 2 {
		if limit, err := strconv.Atoi(limitMatch[1]); err == nil {
			result.Limit = limit
		}
	}
	
	// Extract OFFSET
	offsetMatch := p.patterns["OFFSET"].FindStringSubmatch(query)
	if len(offsetMatch) >= 2 {
		if offset, err := strconv.Atoi(offsetMatch[1]); err == nil {
			result.Offset = offset
		}
	}
	
	return result, nil
}

// parseWhereClause parses WHERE/HAVING conditions
func (p *AQLParser) parseWhereClause(whereStr string) *WhereClause {
	clause := &WhereClause{
		Conditions: []Condition{},
		Operator:   "AND", // Default operator
	}
	
	// Check for OR operator
	if strings.Contains(strings.ToUpper(whereStr), " OR ") {
		clause.Operator = "OR"
		parts := strings.Split(whereStr, " OR ")
		for _, part := range parts {
			if cond := p.parseCondition(strings.TrimSpace(part)); cond != nil {
				clause.Conditions = append(clause.Conditions, *cond)
			}
		}
	} else {
		// Split by AND
		parts := strings.Split(whereStr, " AND ")
		for _, part := range parts {
			if cond := p.parseCondition(strings.TrimSpace(part)); cond != nil {
				clause.Conditions = append(clause.Conditions, *cond)
			}
		}
	}
	
	return clause
}

// parseCondition parses a single condition
func (p *AQLParser) parseCondition(condStr string) *Condition {
	// Pattern for parsing conditions
	condPattern := regexp.MustCompile(`(\w+)\s*(=|!=|<>|<=|>=|<|>|LIKE|IN|BETWEEN)\s*(.+)`)
	
	match := condPattern.FindStringSubmatch(condStr)
	if len(match) < 4 {
		// Try simpler pattern for basic conditions
		simplePat := regexp.MustCompile(`(\w+)\s*=\s*'?([^']+)'?`)
		simpleMatch := simplePat.FindStringSubmatch(condStr)
		if len(simpleMatch) >= 3 {
			return &Condition{
				Field:    simpleMatch[1],
				Operator: "=",
				Value:    p.parseValue(simpleMatch[2]),
			}
		}
		return nil
	}
	
	return &Condition{
		Field:    match[1],
		Operator: strings.ToUpper(match[2]),
		Value:    p.parseValue(match[3]),
	}
}

// parseValue parses a value from string
func (p *AQLParser) parseValue(valueStr string) interface{} {
	valueStr = strings.TrimSpace(valueStr)
	
	// Remove quotes if present
	if (strings.HasPrefix(valueStr, "'") && strings.HasSuffix(valueStr, "'")) ||
	   (strings.HasPrefix(valueStr, "\"") && strings.HasSuffix(valueStr, "\"")) {
		return valueStr[1:len(valueStr)-1]
	}
	
	// Try parsing as number
	if num, err := strconv.ParseFloat(valueStr, 64); err == nil {
		return num
	}
	
	// Try parsing as boolean
	if strings.ToUpper(valueStr) == "TRUE" {
		return true
	}
	if strings.ToUpper(valueStr) == "FALSE" {
		return false
	}
	
	// Handle NULL
	if strings.ToUpper(valueStr) == "NULL" {
		return nil
	}
	
	// Handle IN clause values
	if strings.HasPrefix(valueStr, "(") && strings.HasSuffix(valueStr, ")") {
		inner := valueStr[1:len(valueStr)-1]
		values := strings.Split(inner, ",")
		result := make([]interface{}, len(values))
		for i, v := range values {
			result[i] = p.parseValue(strings.TrimSpace(v))
		}
		return result
	}
	
	return valueStr
}

// parseOrderBy parses ORDER BY clause
func (p *AQLParser) parseOrderBy(orderStr string) []OrderByClause {
	clauses := []OrderByClause{}
	
	parts := strings.Split(orderStr, ",")
	for _, part := range parts {
		part = strings.TrimSpace(part)
		fields := strings.Fields(part)
		
		if len(fields) > 0 {
			clause := OrderByClause{
				Field:     fields[0],
				Direction: "ASC", // Default
			}
			
			if len(fields) > 1 {
				dir := strings.ToUpper(fields[1])
				if dir == "DESC" || dir == "ASC" {
					clause.Direction = dir
				}
			}
			
			clauses = append(clauses, clause)
		}
	}
	
	return clauses
}

// parseInsert parses an INSERT query
func (p *AQLParser) parseInsert(query string) (*AQLQuery, error) {
	// Pattern: INSERT INTO table (fields) VALUES (values)
	pattern := regexp.MustCompile(`(?i)INSERT\s+INTO\s+(\S+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)`)
	
	match := pattern.FindStringSubmatch(query)
	if len(match) < 4 {
		return nil, fmt.Errorf("invalid INSERT query")
	}
	
	result := &AQLQuery{
		Type:   "INSERT",
		From:   match[1],
		Fields: []string{},
		Values: make(map[string]interface{}),
	}
	
	// Parse fields
	fields := strings.Split(match[2], ",")
	values := strings.Split(match[3], ",")
	
	if len(fields) != len(values) {
		return nil, fmt.Errorf("field count doesn't match value count")
	}
	
	for i, field := range fields {
		field = strings.TrimSpace(field)
		result.Fields = append(result.Fields, field)
		result.Values[field] = p.parseValue(strings.TrimSpace(values[i]))
	}
	
	return result, nil
}

// parseUpdate parses an UPDATE query
func (p *AQLParser) parseUpdate(query string) (*AQLQuery, error) {
	// Pattern: UPDATE table SET field=value WHERE condition
	pattern := regexp.MustCompile(`(?i)UPDATE\s+(\S+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$`)
	
	match := pattern.FindStringSubmatch(query)
	if len(match) < 3 {
		return nil, fmt.Errorf("invalid UPDATE query")
	}
	
	result := &AQLQuery{
		Type:   "UPDATE",
		From:   match[1],
		Values: make(map[string]interface{}),
	}
	
	// Parse SET clause
	setParts := strings.Split(match[2], ",")
	for _, part := range setParts {
		eqIndex := strings.Index(part, "=")
		if eqIndex > 0 {
			field := strings.TrimSpace(part[:eqIndex])
			value := p.parseValue(strings.TrimSpace(part[eqIndex+1:]))
			result.Values[field] = value
			result.Fields = append(result.Fields, field)
		}
	}
	
	// Parse WHERE clause if present
	if len(match) > 3 && match[3] != "" {
		result.Where = p.parseWhereClause(match[3])
	}
	
	return result, nil
}

// parseDelete parses a DELETE query
func (p *AQLParser) parseDelete(query string) (*AQLQuery, error) {
	// Pattern: DELETE FROM table WHERE condition
	pattern := regexp.MustCompile(`(?i)DELETE\s+FROM\s+(\S+)(?:\s+WHERE\s+(.+))?`)
	
	match := pattern.FindStringSubmatch(query)
	if len(match) < 2 {
		return nil, fmt.Errorf("invalid DELETE query")
	}
	
	result := &AQLQuery{
		Type: "DELETE",
		From: match[1],
	}
	
	// Parse WHERE clause if present
	if len(match) > 2 && match[2] != "" {
		result.Where = p.parseWhereClause(match[2])
	}
	
	return result, nil
}