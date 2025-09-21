package security

import (
	"encoding/base64"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSanitizerString(t *testing.T) {
	s := NewSanitizer()

	tests := []struct {
		name     string
		input    string
		maxLen   int
		expected string
	}{
		{
			name:     "normal string",
			input:    "hello world",
			maxLen:   100,
			expected: "hello world",
		},
		{
			name:     "string with spaces",
			input:    "  hello world  ",
			maxLen:   100,
			expected: "hello world",
		},
		{
			name:     "string with null bytes",
			input:    "hello\x00world",
			maxLen:   100,
			expected: "helloworld",
		},
		{
			name:     "string too long",
			input:    "this is a very long string",
			maxLen:   10,
			expected: "this is a ",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := s.SanitizeString(tt.input, tt.maxLen)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSanitizeHTML(t *testing.T) {
	s := NewSanitizer()

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "plain text",
			input:    "hello world",
			expected: "hello world",
		},
		{
			name:     "HTML tags",
			input:    "<script>alert('xss')</script>",
			expected: "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;",
		},
		{
			name:     "HTML entities",
			input:    "test & test",
			expected: "test &amp; test",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := s.SanitizeHTML(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSanitizeSQL(t *testing.T) {
	s := NewSanitizer()

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "normal string",
			input:    "hello world",
			expected: "hello world",
		},
		{
			name:     "single quotes",
			input:    "it's a test",
			expected: "it''s a test",
		},
		{
			name:     "SQL injection attempt",
			input:    "'; DROP TABLE users; --",
			expected: "''; DROP TABLE users; --",
		},
		{
			name:     "null bytes",
			input:    "test\x00value",
			expected: "testvalue",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := s.SanitizeSQL(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSanitizePath(t *testing.T) {
	s := NewSanitizer()

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "normal path",
			input:    "folder/file.txt",
			expected: "folder/file.txt",
		},
		{
			name:     "path traversal attempt",
			input:    "../../../etc/passwd",
			expected: "etc/passwd",
		},
		{
			name:     "absolute path",
			input:    "/etc/passwd",
			expected: "etc/passwd",
		},
		{
			name:     "null bytes",
			input:    "file\x00.txt",
			expected: "file.txt",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := s.SanitizePath(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestValidateEmail(t *testing.T) {
	s := NewSanitizer()

	tests := []struct {
		name  string
		email string
		valid bool
	}{
		{"valid email", "test@example.com", true},
		{"valid with subdomain", "user@mail.example.com", true},
		{"valid with plus", "user+tag@example.com", true},
		{"invalid no @", "test.example.com", false},
		{"invalid no domain", "test@", false},
		{"invalid no user", "@example.com", false},
		{"invalid spaces", "test @example.com", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := s.ValidateEmail(tt.email)
			assert.Equal(t, tt.valid, result)
		})
	}
}

func TestValidateArxOSID(t *testing.T) {
	s := NewSanitizer()

	tests := []struct {
		name  string
		id    string
		valid bool
	}{
		{
			name:  "valid ArxOS ID",
			id:    "ARXOS-US-CA-SF-BLD-0001",
			valid: true,
		},
		{
			name:  "valid with path",
			id:    "ARXOS-US-CA-SF-BLD-0001/floor-01/room-101",
			valid: true,
		},
		{
			name:  "invalid format",
			id:    "INVALID-ID",
			valid: false,
		},
		{
			name:  "empty",
			id:    "",
			valid: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := s.ValidateArxOSID(tt.id)
			assert.Equal(t, tt.valid, result)
		})
	}
}

func TestCSRFProtector(t *testing.T) {
	protector := NewCSRFProtector()

	t.Run("GenerateToken", func(t *testing.T) {
		// Generate multiple tokens and ensure they're different
		token1, err := protector.GenerateToken()
		require.NoError(t, err)
		assert.NotEmpty(t, token1)

		token2, err := protector.GenerateToken()
		require.NoError(t, err)
		assert.NotEmpty(t, token2)

		// Tokens should be different
		assert.NotEqual(t, token1, token2)

		// Token should be base64 encoded
		decoded, err := base64.URLEncoding.DecodeString(token1)
		require.NoError(t, err)
		assert.Equal(t, 32, len(decoded)) // 32 bytes as configured
	})

	t.Run("ValidateToken", func(t *testing.T) {
		token, _ := protector.GenerateToken()

		// Valid token
		assert.True(t, protector.ValidateToken(token, token))

		// Different tokens
		otherToken, _ := protector.GenerateToken()
		assert.False(t, protector.ValidateToken(token, otherToken))

		// Empty tokens
		assert.False(t, protector.ValidateToken("", token))
		assert.False(t, protector.ValidateToken(token, ""))
		assert.False(t, protector.ValidateToken("", ""))
	})

	t.Run("MustGenerateToken", func(t *testing.T) {
		// Should not panic under normal conditions
		assert.NotPanics(t, func() {
			token := protector.MustGenerateToken()
			assert.NotEmpty(t, token)
		})
	})

	t.Run("TokenRandomness", func(t *testing.T) {
		// Generate many tokens and ensure uniqueness
		tokens := make(map[string]bool)
		for i := 0; i < 100; i++ {
			token, err := protector.GenerateToken()
			require.NoError(t, err)

			// Check for duplicates
			if tokens[token] {
				t.Errorf("Duplicate token generated: %s", token)
			}
			tokens[token] = true
		}

		// Should have 100 unique tokens
		assert.Equal(t, 100, len(tokens))
	})
}

func TestInputValidator(t *testing.T) {
	validator := NewInputValidator()

	t.Run("ValidateBuildingName", func(t *testing.T) {
		tests := []struct {
			name      string
			input     string
			expectErr bool
		}{
			{"valid name", "Building 123", false},
			{"empty name", "", true},
			{"special chars", "Building@#$", true},
			{"too long", strings.Repeat("a", 300), true},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				err := validator.Validate("building_name", tt.input)
				if tt.expectErr {
					assert.Error(t, err)
				} else {
					assert.NoError(t, err)
				}
			})
		}
	})

	t.Run("ValidateStatus", func(t *testing.T) {
		tests := []struct {
			name      string
			input     string
			expectErr bool
		}{
			{"valid OPERATIONAL", "OPERATIONAL", false},
			{"valid DEGRADED", "DEGRADED", false},
			{"valid FAILED", "FAILED", false},
			{"invalid status", "BROKEN", true},
			{"empty", "", true},
			{"lowercase", "operational", true},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				err := validator.Validate("status", tt.input)
				if tt.expectErr {
					assert.Error(t, err)
				} else {
					assert.NoError(t, err)
				}
			})
		}
	})
}

func TestXSSProtector(t *testing.T) {
	protector := NewXSSProtector()

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "plain text",
			input:    "Hello World",
			expected: "Hello World",
		},
		{
			name:     "script tag",
			input:    "<script>alert('XSS')</script>",
			expected: "&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;",
		},
		{
			name:     "img tag with onerror",
			input:    `<img src="x" onerror="alert('XSS')">`,
			expected: "&lt;img src=&#34;x&#34; onerror=&#34;alert(&#39;XSS&#39;)&#34;&gt;",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := protector.Clean(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestRemoveControlCharacters(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "normal text",
			input:    "hello world",
			expected: "hello world",
		},
		{
			name:     "with newlines",
			input:    "hello\nworld",
			expected: "hello\nworld",
		},
		{
			name:     "with tabs",
			input:    "hello\tworld",
			expected: "hello\tworld",
		},
		{
			name:     "with control chars",
			input:    "hello\x00\x01\x02world",
			expected: "helloworld",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := RemoveControlCharacters(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// Benchmarks
func BenchmarkCSRFGenerate(b *testing.B) {
	protector := NewCSRFProtector()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		protector.GenerateToken()
	}
}

func BenchmarkCSRFValidate(b *testing.B) {
	protector := NewCSRFProtector()
	token, _ := protector.GenerateToken()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		protector.ValidateToken(token, token)
	}
}

func BenchmarkSanitizeHTML(b *testing.B) {
	s := NewSanitizer()
	input := "<script>alert('xss')</script>"
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		s.SanitizeHTML(input)
	}
}