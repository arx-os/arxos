package aql

import (
	"bufio"
	"strings"
	"unicode"
)

// TokenType represents the type of token
type TokenType int

const (
	TOKEN_EOF TokenType = iota
	TOKEN_IDENTIFIER
	TOKEN_STRING
	TOKEN_NUMBER
	TOKEN_OPERATOR
	TOKEN_COMMA
	TOKEN_ASTERISK
	TOKEN_LPAREN
	TOKEN_RPAREN
)

// Token represents a lexical token
type Token struct {
	Type  TokenType
	Value string
}

// Scanner tokenizes AQL input
type Scanner struct {
	reader *bufio.Reader
	buffer []rune
	pos    int
}

// NewScanner creates a new scanner
func NewScanner(input string) *Scanner {
	return &Scanner{
		reader: bufio.NewReader(strings.NewReader(input)),
		buffer: []rune{},
		pos:    0,
	}
}

// Scan returns the next token
func (s *Scanner) Scan() Token {
	// Skip whitespace
	s.skipWhitespace()
	
	// Read next character
	ch := s.read()
	
	if ch == 0 {
		return Token{Type: TOKEN_EOF}
	}
	
	// Check token type
	switch {
	case ch == '*':
		return Token{Type: TOKEN_ASTERISK, Value: "*"}
	case ch == ',':
		return Token{Type: TOKEN_COMMA, Value: ","}
	case ch == '(':
		return Token{Type: TOKEN_LPAREN, Value: "("}
	case ch == ')':
		return Token{Type: TOKEN_RPAREN, Value: ")"}
	case ch == '\'' || ch == '"':
		return s.scanString(ch)
	case isOperatorStart(ch):
		return s.scanOperator(ch)
	case unicode.IsDigit(ch):
		return s.scanNumber(ch)
	case unicode.IsLetter(ch) || ch == '_':
		return s.scanIdentifier(ch)
	default:
		return Token{Type: TOKEN_EOF}
	}
}

// Unread pushes the last token back
func (s *Scanner) Unread() {
	if s.pos > 0 {
		s.pos--
	}
}

func (s *Scanner) read() rune {
	ch, _, err := s.reader.ReadRune()
	if err != nil {
		return 0
	}
	return ch
}

func (s *Scanner) unread() {
	s.reader.UnreadRune()
}

func (s *Scanner) skipWhitespace() {
	for {
		ch := s.read()
		if ch == 0 || !unicode.IsSpace(ch) {
			if ch != 0 {
				s.unread()
			}
			break
		}
	}
}

func (s *Scanner) scanString(quote rune) Token {
	var value strings.Builder
	value.WriteRune(quote)
	
	for {
		ch := s.read()
		if ch == 0 {
			break
		}
		value.WriteRune(ch)
		if ch == quote {
			break
		}
	}
	
	return Token{Type: TOKEN_STRING, Value: value.String()}
}

func (s *Scanner) scanNumber(first rune) Token {
	var value strings.Builder
	value.WriteRune(first)
	
	for {
		ch := s.read()
		if ch == 0 || (!unicode.IsDigit(ch) && ch != '.') {
			if ch != 0 {
				s.unread()
			}
			break
		}
		value.WriteRune(ch)
	}
	
	return Token{Type: TOKEN_NUMBER, Value: value.String()}
}

func (s *Scanner) scanIdentifier(first rune) Token {
	var value strings.Builder
	value.WriteRune(first)
	
	for {
		ch := s.read()
		if ch == 0 || (!unicode.IsLetter(ch) && !unicode.IsDigit(ch) && ch != '_' && ch != ':' && ch != '.') {
			if ch != 0 {
				s.unread()
			}
			break
		}
		value.WriteRune(ch)
	}
	
	return Token{Type: TOKEN_IDENTIFIER, Value: value.String()}
}

func (s *Scanner) scanOperator(first rune) Token {
	var value strings.Builder
	value.WriteRune(first)
	
	// Check for multi-character operators
	ch := s.read()
	if ch != 0 {
		twoChar := string(first) + string(ch)
		switch twoChar {
		case "!=", ">=", "<=", "->":
			value.WriteRune(ch)
		default:
			s.unread()
		}
	}
	
	return Token{Type: TOKEN_OPERATOR, Value: value.String()}
}

func isOperatorStart(ch rune) bool {
	return ch == '=' || ch == '!' || ch == '>' || ch == '<' || ch == '-'
}