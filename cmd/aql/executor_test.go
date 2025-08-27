package aql

import (
	"testing"
)

func TestParser(t *testing.T) {
	tests := []struct {
		name    string
		query   string
		wantErr bool
	}{
		{
			name:    "Simple SELECT",
			query:   "SELECT * FROM building:main",
			wantErr: false,
		},
		{
			name:    "SELECT with fields",
			query:   "SELECT id, name, type FROM arxobjects",
			wantErr: false,
		},
		{
			name:    "SELECT with WHERE",
			query:   "SELECT * FROM building:main WHERE type = 'wall'",
			wantErr: false,
		},
		{
			name:    "SELECT with complex WHERE",
			query:   "SELECT * FROM building:main WHERE type = 'wall' AND confidence > 0.8",
			wantErr: false,
		},
		{
			name:    "Invalid query",
			query:   "INVALID QUERY",
			wantErr: true,
		},
	}

	parser := NewParser()
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			query, err := parser.Parse(tt.query)
			if (err != nil) != tt.wantErr {
				t.Errorf("Parse() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && query == nil {
				t.Error("Parse() returned nil query without error")
			}
		})
	}
}

func TestScanner(t *testing.T) {
	tests := []struct {
		input    string
		expected []Token
	}{
		{
			input: "SELECT * FROM building",
			expected: []Token{
				{Type: TOKEN_IDENTIFIER, Value: "SELECT"},
				{Type: TOKEN_ASTERISK, Value: "*"},
				{Type: TOKEN_IDENTIFIER, Value: "FROM"},
				{Type: TOKEN_IDENTIFIER, Value: "building"},
				{Type: TOKEN_EOF},
			},
		},
		{
			input: "WHERE confidence >= 0.8",
			expected: []Token{
				{Type: TOKEN_IDENTIFIER, Value: "WHERE"},
				{Type: TOKEN_IDENTIFIER, Value: "confidence"},
				{Type: TOKEN_OPERATOR, Value: ">="},
				{Type: TOKEN_NUMBER, Value: "0.8"},
				{Type: TOKEN_EOF},
			},
		},
		{
			input: "type = 'wall'",
			expected: []Token{
				{Type: TOKEN_IDENTIFIER, Value: "type"},
				{Type: TOKEN_OPERATOR, Value: "="},
				{Type: TOKEN_STRING, Value: "'wall'"},
				{Type: TOKEN_EOF},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			scanner := NewScanner(tt.input)
			for i, expected := range tt.expected {
				token := scanner.Scan()
				if token.Type != expected.Type || token.Value != expected.Value {
					t.Errorf("Token %d: got %v, expected %v", i, token, expected)
				}
			}
		})
	}
}

func TestBuildSelectSQL(t *testing.T) {
	executor := &Executor{}
	
	tests := []struct {
		name     string
		query    *Query
		wantSQL  string
		wantArgs int
	}{
		{
			name: "Simple SELECT",
			query: &Query{
				Type:   SELECT,
				Fields: []string{"*"},
				Target: "building:main",
			},
			wantSQL:  "SELECT * FROM arxobjects ORDER BY created_at DESC LIMIT 100",
			wantArgs: 0,
		},
		{
			name: "SELECT with WHERE",
			query: &Query{
				Type:   SELECT,
				Fields: []string{"id", "name"},
				Target: "arxobjects",
				Conditions: []Condition{
					{Field: "type", Operator: "=", Value: "wall"},
				},
			},
			wantSQL:  "SELECT id, name FROM arxobjects WHERE type = $1 ORDER BY created_at DESC LIMIT 100",
			wantArgs: 1,
		},
		{
			name: "SELECT with multiple conditions",
			query: &Query{
				Type:   SELECT,
				Fields: []string{"*"},
				Target: "arxobjects",
				Conditions: []Condition{
					{Field: "type", Operator: "=", Value: "wall"},
					{Field: "confidence", Operator: ">", Value: 0.8},
				},
			},
			wantSQL:  "SELECT * FROM arxobjects WHERE type = $1 AND confidence > $2 ORDER BY created_at DESC LIMIT 100",
			wantArgs: 2,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			sql, args := executor.buildSelectSQL(tt.query)
			if sql != tt.wantSQL {
				t.Errorf("buildSelectSQL() sql = %v, want %v", sql, tt.wantSQL)
			}
			if len(args) != tt.wantArgs {
				t.Errorf("buildSelectSQL() args count = %v, want %v", len(args), tt.wantArgs)
			}
		})
	}
}