package aql

import (
	"fmt"
	"strings"
)

// QueryType represents the type of AQL query
type QueryType int

const (
	SELECT QueryType = iota
	UPDATE
	DELETE
	VALIDATE
	HISTORY
	DIFF
)

// Query represents a parsed AQL query
type Query struct {
	Type       QueryType
	Target     string              // Object or collection
	Fields     []string           // Fields to select/update
	Conditions []Condition        // WHERE conditions
	Values     map[string]interface{} // SET values for UPDATE
	Options    map[string]interface{} // Additional options
}

// Condition represents a WHERE condition
type Condition struct {
	Field    string
	Operator string
	Value    interface{}
}

// Parser parses AQL queries
type Parser struct {
	scanner *Scanner
}

// NewParser creates a new AQL parser
func NewParser() *Parser {
	return &Parser{}
}

// Parse parses an AQL query string
func (p *Parser) Parse(input string) (*Query, error) {
	p.scanner = NewScanner(input)
	
	// Get first token to determine query type
	token := p.scanner.Scan()
	
	switch strings.ToUpper(token.Value) {
	case "SELECT":
		return p.parseSelect()
	case "UPDATE":
		return p.parseUpdate()
	case "DELETE":
		return p.parseDelete()
	case "VALIDATE":
		return p.parseValidate()
	case "HISTORY":
		return p.parseHistory()
	case "DIFF":
		return p.parseDiff()
	default:
		return nil, fmt.Errorf("unknown query type: %s", token.Value)
	}
}

func (p *Parser) parseSelect() (*Query, error) {
	query := &Query{
		Type:   SELECT,
		Fields: []string{},
		Conditions: []Condition{},
	}
	
	// Parse fields
	token := p.scanner.Scan()
	if token.Type == TOKEN_ASTERISK {
		query.Fields = append(query.Fields, "*")
		token = p.scanner.Scan() // Get next token after *
	} else {
		// Parse field list
		for {
			if token.Type != TOKEN_IDENTIFIER {
				break
			}
			query.Fields = append(query.Fields, token.Value)
			
			token = p.scanner.Scan()
			if token.Type != TOKEN_COMMA {
				break
			}
			token = p.scanner.Scan()
		}
	}
	
	// Parse FROM
	if strings.ToUpper(token.Value) != "FROM" {
		return nil, fmt.Errorf("expected FROM, got %s", token.Value)
	}
	
	token = p.scanner.Scan()
	query.Target = token.Value
	
	// Check if target ends with : and next token is * (for patterns like building:*)
	token = p.scanner.Scan()
	if strings.HasSuffix(query.Target, ":") && token.Type == TOKEN_ASTERISK {
		query.Target += "*"
		token = p.scanner.Scan() // Get token after asterisk
	}
	
	// Parse WHERE (optional)
	if token.Type != TOKEN_EOF && strings.ToUpper(token.Value) == "WHERE" {
		conditions, err := p.parseConditions()
		if err != nil {
			return nil, err
		}
		query.Conditions = conditions
	}
	
	return query, nil
}

func (p *Parser) parseConditions() ([]Condition, error) {
	conditions := []Condition{}
	
	for {
		// Parse field
		token := p.scanner.Scan()
		if token.Type != TOKEN_IDENTIFIER {
			break
		}
		field := token.Value
		
		// Parse operator
		token = p.scanner.Scan()
		operator := token.Value
		
		// Parse value
		token = p.scanner.Scan()
		value := p.parseValue(token)
		
		conditions = append(conditions, Condition{
			Field:    field,
			Operator: operator,
			Value:    value,
		})
		
		// Check for AND/OR
		token = p.scanner.Scan()
		if token.Type == TOKEN_EOF {
			break
		}
		if strings.ToUpper(token.Value) != "AND" && strings.ToUpper(token.Value) != "OR" {
			p.scanner.Unread()
			break
		}
	}
	
	return conditions, nil
}

func (p *Parser) parseValue(token Token) interface{} {
	switch token.Type {
	case TOKEN_STRING:
		return strings.Trim(token.Value, "'\"")
	case TOKEN_NUMBER:
		// Parse as float or int
		return token.Value
	case TOKEN_IDENTIFIER:
		// Could be boolean or identifier
		if token.Value == "true" {
			return true
		} else if token.Value == "false" {
			return false
		}
		return token.Value
	default:
		return token.Value
	}
}

func (p *Parser) parseUpdate() (*Query, error) {
	// TODO: Implement UPDATE parsing
	return &Query{Type: UPDATE}, nil
}

func (p *Parser) parseDelete() (*Query, error) {
	// TODO: Implement DELETE parsing
	return &Query{Type: DELETE}, nil
}

func (p *Parser) parseValidate() (*Query, error) {
	// TODO: Implement VALIDATE parsing
	return &Query{Type: VALIDATE}, nil
}

func (p *Parser) parseHistory() (*Query, error) {
	// TODO: Implement HISTORY parsing
	return &Query{Type: HISTORY}, nil
}

func (p *Parser) parseDiff() (*Query, error) {
	// TODO: Implement DIFF parsing
	return &Query{Type: DIFF}, nil
}